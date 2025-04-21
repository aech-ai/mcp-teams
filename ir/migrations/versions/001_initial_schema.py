"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2025-04-20

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.schema import CreateTable
from sqlalchemy.sql import table, column

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # First, ensure the pgvector extension is installed
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Create schema version table
    op.create_table(
        'schema_version',
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('applied_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('version')
    )
    
    # Insert initial schema version
    schema_version_table = table(
        'schema_version',
        column('version', sa.Integer),
        column('description', sa.String)
    )
    
    op.bulk_insert(
        schema_version_table,
        [
            {'version': 1, 'description': 'Initial schema'}
        ]
    )
    
    # Create indexed content table
    op.create_table(
        'indexed_content',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('content_id', sa.String(), nullable=False),
        sa.Column('source_type', sa.String(), nullable=False),
        sa.Column('content', sa.String(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('content_id')
    )
    
    # Add vector column for embeddings
    op.execute('ALTER TABLE indexed_content ADD COLUMN embedding vector(1536)')
    
    # Create full-text search index
    op.execute(
        'CREATE INDEX content_fts_idx ON indexed_content USING GIN (to_tsvector(\'english\', content))'
    )
    
    # Create vector search index
    op.execute(
        'CREATE INDEX embedding_idx ON indexed_content USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)'
    )
    
    # Create source metadata table
    op.create_table(
        'source_metadata',
        sa.Column('content_id', sa.String(), nullable=False),
        sa.Column('source_id', sa.String(), nullable=False),
        sa.Column('source_specific_data', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['content_id'], ['indexed_content.content_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('content_id', 'source_id')
    )
    
    # Create hybrid search function
    op.execute("""
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
    """)


def downgrade() -> None:
    # Drop hybrid search function
    op.execute('DROP FUNCTION IF EXISTS hybrid_search')
    
    # Drop source metadata table
    op.drop_table('source_metadata')
    
    # Drop indexed content table
    op.drop_table('indexed_content')
    
    # Drop schema version table
    op.drop_table('schema_version')
    
    # We don't drop the vector extension as it might be used by other applications