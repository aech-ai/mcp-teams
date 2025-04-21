"""
PostgreSQL schema for the MCP IR server.
Includes tables and indexes for content storage and retrieval.
"""

# Schema version for migrations
SCHEMA_VERSION = 1

# Core schema creation SQL
SCHEMA_SQL = """
-- Enable the vector extension if not already enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- Create schema version table
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Main table for indexed content with vector embeddings
CREATE TABLE IF NOT EXISTS indexed_content (
    id SERIAL PRIMARY KEY,
    content_id TEXT NOT NULL UNIQUE,
    source_type TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Full-text search index
CREATE INDEX IF NOT EXISTS content_fts_idx ON indexed_content USING GIN (to_tsvector('english', content));

-- Vector search index
CREATE INDEX IF NOT EXISTS embedding_idx ON indexed_content USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Source-specific metadata
CREATE TABLE IF NOT EXISTS source_metadata (
    content_id TEXT NOT NULL REFERENCES indexed_content(content_id) ON DELETE CASCADE,
    source_id TEXT NOT NULL,
    source_specific_data JSONB,
    PRIMARY KEY (content_id, source_id)
);

-- Insert initial schema version
INSERT INTO schema_version (version) 
VALUES (1)
ON CONFLICT (version) DO NOTHING;

-- Function for hybrid search using both FTS and vector similarity
CREATE OR REPLACE FUNCTION hybrid_search(
    query_text TEXT,
    query_embedding vector(1536),
    semantic_weight FLOAT DEFAULT 0.7,
    limit_val INTEGER DEFAULT 10
) RETURNS TABLE (
    content_id TEXT,
    content TEXT,
    source_type TEXT,
    metadata JSONB,
    score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    WITH semantic_results AS (
        SELECT 
            content_id,
            content,
            source_type,
            metadata,
            1 - (embedding <=> query_embedding) AS similarity
        FROM 
            indexed_content
        WHERE 
            embedding IS NOT NULL
        ORDER BY 
            similarity DESC
        LIMIT 
            limit_val * 2
    ),
    fulltext_results AS (
        SELECT 
            content_id,
            content,
            source_type,
            metadata,
            ts_rank(to_tsvector('english', content), plainto_tsquery('english', query_text)) AS rank
        FROM 
            indexed_content
        WHERE 
            to_tsvector('english', content) @@ plainto_tsquery('english', query_text)
        ORDER BY 
            rank DESC
        LIMIT 
            limit_val * 2
    ),
    combined_results AS (
        -- Semantic results with normalized scores
        SELECT 
            content_id,
            content,
            source_type,
            metadata,
            similarity * semantic_weight AS score
        FROM 
            semantic_results
        
        UNION ALL
        
        -- Full-text results with normalized scores
        SELECT 
            content_id,
            content,
            source_type,
            metadata,
            rank * (1 - semantic_weight) AS score
        FROM 
            fulltext_results
    ),
    aggregated_results AS (
        SELECT 
            content_id,
            content,
            source_type,
            metadata,
            SUM(score) AS total_score
        FROM 
            combined_results
        GROUP BY 
            content_id, content, source_type, metadata
        ORDER BY 
            total_score DESC
        LIMIT 
            limit_val
    )
    SELECT 
        content_id,
        content,
        source_type,
        metadata,
        total_score AS score
    FROM 
        aggregated_results;
END;
$$ LANGUAGE plpgsql;
"""

async def create_schema(conn):
    """Create the database schema if it doesn't exist."""
    async with conn.cursor() as cur:
        await cur.execute(SCHEMA_SQL)
        await conn.commit()

async def check_schema_version(conn):
    """Check the current schema version."""
    async with conn.cursor() as cur:
        try:
            await cur.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
            result = await cur.fetchone()
            return result[0] if result else 0
        except Exception:
            return 0

async def upgrade_schema(conn, target_version=SCHEMA_VERSION):
    """Upgrade the database schema to the target version."""
    current_version = await check_schema_version(conn)
    
    if current_version >= target_version:
        return False  # No upgrade needed
    
    # Apply migrations in order
    for version in range(current_version + 1, target_version + 1):
        migration_func = globals().get(f"migrate_to_v{version}")
        if migration_func:
            await migration_func(conn)
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT INTO schema_version (version) VALUES (%s)",
                    (version,)
                )
                await conn.commit()
    
    return True  # Upgrade performed

# Example migration function (for future use)
async def migrate_to_v2(conn):
    """Example migration to v2 schema."""
    # This is a placeholder for future migrations
    async with conn.cursor() as cur:
        # Example migration SQL
        await cur.execute("""
        -- Add any schema changes for version 2 here
        ALTER TABLE indexed_content ADD COLUMN IF NOT EXISTS chunk_size INTEGER;
        """)
        await conn.commit()