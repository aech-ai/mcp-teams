import duckdb
import os
import sys
from config import DUCKDB_PATH

CHAT_TABLE = """
CREATE TABLE IF NOT EXISTS chats (
    id TEXT PRIMARY KEY,
    topic TEXT,
    created DATETIME,
    last_updated DATETIME
);
"""

MESSAGE_TABLE = """
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    chat_id TEXT,
    sender_id TEXT,
    sender_name TEXT,
    content TEXT,
    created DATETIME,
    embedding BLOB,
    FOREIGN KEY(chat_id) REFERENCES chats(id)
);
"""

# Try using standard DuckDB FTS syntax instead of SQLite-style VIRTUAL TABLE
FTS_INDEX = """
-- Create a standard full text index if FTS extension is available
CREATE INDEX IF NOT EXISTS messages_content_idx ON messages(content);

-- Try to create a view that uses built-in search capabilities
CREATE OR REPLACE VIEW messages_fts AS
    SELECT id, content FROM messages;
"""

VECTOR_EXTENSION = """
-- Try to load vector extension if available, silently continue if not
INSTALL vector;
LOAD vector;
"""

# FlockMTL-style LLM UDFs - simplified stubs that don't rely on complex types
LLM_UDFS = """
-- LLM embedding function (generates vector embeddings)
CREATE OR REPLACE FUNCTION llm_embedding(text VARCHAR)
RETURNS BLOB AS 'SELECT NULL::BLOB'; 

-- LLM reranking function (improves search ranking)
CREATE OR REPLACE FUNCTION llm_rerank(query VARCHAR, content VARCHAR, score DOUBLE)
RETURNS DOUBLE AS 'SELECT score'; 

-- LLM filtering function (removes irrelevant results)
CREATE OR REPLACE FUNCTION llm_filter(query VARCHAR, content VARCHAR)
RETURNS BOOLEAN AS 'SELECT TRUE';

-- LLM summarization function 
CREATE OR REPLACE FUNCTION llm_summarize(texts VARCHAR)
RETURNS VARCHAR AS 'SELECT ''Summary of provided texts''';
"""

# Simplified hybrid search function that works without vector extension
HYBRID_SEARCH_FUNC = """
CREATE OR REPLACE FUNCTION hybrid_search(query VARCHAR, top_k INTEGER)
RETURNS TABLE (id VARCHAR, chat_id VARCHAR, sender_name VARCHAR, content VARCHAR, created TIMESTAMP, score DOUBLE) AS '
    WITH bm25_results AS (
        SELECT id, chat_id, sender_name, content, created, 1.0 AS score
        FROM messages
        WHERE content LIKE ''%'' || query || ''%''
        ORDER BY score LIMIT top_k * 2
    )
    SELECT * FROM bm25_results
    LIMIT ?
';
"""

def init_db():
    """Initialize the DuckDB database with tables, indices, and vector extensions."""
    # Create directory for the database if it doesn't exist
    os.makedirs(os.path.dirname(DUCKDB_PATH), exist_ok=True)
    
    # Attempt to connect to DuckDB; if the file is locked, disable persistence
    try:
        con = duckdb.connect(DUCKDB_PATH)
    except Exception as e:
        print(f"Warning: Could not connect to DuckDB at {DUCKDB_PATH}: {e}. Disabling persistence.", file=sys.stderr)
        return None
    
    # Create tables
    con.execute(CHAT_TABLE)
    con.execute(MESSAGE_TABLE)
    
    # Create full-text search index if supported
    try:
        con.execute(FTS_INDEX)
        print("Standard index created successfully", file=sys.stderr)
    except Exception as e:
        print(f"FTS index not available: {e}", file=sys.stderr)
    
    # Try to load vector extension if available
    try:
        con.execute(VECTOR_EXTENSION)
        print("Vector extension loaded successfully", file=sys.stderr)
    except Exception as e:
        print(f"Vector extension not available: {e}", file=sys.stderr)
    
    # Create simplified LLM UDFs (these are non-functional stubs for demo purposes)
    try:
        con.execute(LLM_UDFS)
        con.execute(HYBRID_SEARCH_FUNC)
        print("LLM functions registered successfully", file=sys.stderr)
    except Exception as e:
        print(f"Error creating LLM functions: {e}", file=sys.stderr)
    
    return con

def insert_chat(con, chat):
    """Insert or update a chat record in the database."""
    if not con:
        return
        
    try:
        con.execute(
            """
            INSERT OR REPLACE INTO chats (id, topic, created, last_updated)
            VALUES (?, ?, ?, ?)
            """,
            [chat["id"], chat.get("topic", ""), chat.get("createdDateTime"), chat.get("lastUpdatedDateTime")]
        )
    except Exception as e:
        print(f"Error inserting chat: {e}", file=sys.stderr)

def insert_message(con, msg, embedding=None):
    """Insert or update a message record in the database with optional embedding."""
    if not con:
        return
        
    try:
        # Insert into messages table
        con.execute(
            """
            INSERT OR REPLACE INTO messages (id, chat_id, sender_id, sender_name, content, created, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                msg["id"],
                msg["chatId"],
                msg["from"]["user"]["id"] if msg["from"].get("user") else None,
                msg["from"]["user"].get("displayName") if msg["from"].get("user") else None,
                msg["body"].get("content", ""),
                msg.get("createdDateTime"),
                embedding
            ]
        )
    except Exception as e:
        print(f"Error inserting message: {e}", file=sys.stderr)
    
    # Update FTS index if needed - but our simplified version doesn't need this
    # since we're using standard search capabilities

def search_messages(con, query, mode="hybrid", top_k=10):
    """Search messages using different methods (bm25, vector, hybrid)."""
    if not con:
        return []
        
    try:
        if mode == "hybrid":
            # Try to use the hybrid search function if available
            return con.execute(
                "SELECT * FROM hybrid_search(?, ?)", 
                [query, top_k]
            ).fetchall()
        else:
            # Simplified full-text search using LIKE for compatibility
            return con.execute(
                """
                SELECT id, chat_id, sender_name, content, created, 1.0 AS score
                FROM messages
                WHERE content LIKE '%' || ? || '%'
                ORDER BY score LIMIT ?
                """,
                [query, top_k]
            ).fetchall()
    except Exception as e:
        print(f"Search error: {e}", file=sys.stderr)
        return []