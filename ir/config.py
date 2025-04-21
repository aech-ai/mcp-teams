"""
Configuration for the MCP IR server.
Loads settings from environment variables with sensible defaults.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# PostgreSQL configuration
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
POSTGRES_DB = os.getenv("POSTGRES_DB", "mcp_ir")

# Connection pool settings
PG_MIN_CONN = int(os.getenv("PG_MIN_CONN", "1"))
PG_MAX_CONN = int(os.getenv("PG_MAX_CONN", "10"))

# OpenAI API configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))

# MCP server configuration
MCP_SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", "8090"))
MCP_SERVER_HOST = os.getenv("MCP_SERVER_HOST", "0.0.0.0")

# Search configuration
DEFAULT_SEARCH_LIMIT = int(os.getenv("DEFAULT_SEARCH_LIMIT", "10"))
DEFAULT_SEARCH_TYPE = os.getenv("DEFAULT_SEARCH_TYPE", "hybrid")  # hybrid, semantic, fulltext
HYBRID_WEIGHT_SEMANTIC = float(os.getenv("HYBRID_WEIGHT_SEMANTIC", "0.7"))
HYBRID_WEIGHT_FULLTEXT = float(os.getenv("HYBRID_WEIGHT_FULLTEXT", "0.3"))

# Chunking configuration
DEFAULT_CHUNK_SIZE = int(os.getenv("DEFAULT_CHUNK_SIZE", "1000"))
DEFAULT_CHUNK_OVERLAP = int(os.getenv("DEFAULT_CHUNK_OVERLAP", "200"))

# Get PostgreSQL connection string
def get_pg_connection_string():
    """Generate PostgreSQL connection string from environment variables."""
    return f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"