# PostgreSQL Setup for MCP IR Server

This directory contains files for setting up the PostgreSQL database used by the MCP Information Retrieval (IR) Server.

## PostgreSQL Configuration

The IR server uses PostgreSQL with the pgvector extension for storing and searching vector embeddings, which is essential for hybrid search functionality.

### Files

- **Dockerfile**: Builds a PostgreSQL container with the pgvector extension installed.
- **postgresql.conf**: Custom PostgreSQL configuration tuned for vector search and performance.
- **init-db.sh**: Initialization script that runs when the container first starts.

## Running PostgreSQL

### With Docker Compose (Recommended)

The easiest way to run PostgreSQL with all necessary extensions is using Docker Compose:

```bash
# Create .env file first
cp .env.template .env
# Edit .env with your PostgreSQL settings

# Start PostgreSQL container
docker-compose up -d postgres
```

### Manual Installation

For manual installation:

1. Install PostgreSQL 14+ on your system
2. Install the pgvector extension (https://github.com/pgvector/pgvector)
3. Create a database for the IR server
4. Run the migrations to set up the schema

```bash
# Install pgvector (Ubuntu example)
sudo apt install postgresql-14-pgvector

# Create database
sudo -u postgres createdb mcp_ir

# Run migrations (from project root)
python -m ir.migrations.cli upgrade
```

## Database Schema

The IR server uses a schema with several key components:

1. **Core Tables**:
   - `indexed_content`: Stores text content with vector embeddings
   - `source_metadata`: Stores source-specific metadata for content
   - `schema_version`: Tracks migration versions

2. **Teams-Specific Tables**:
   - `teams_messages`: Stores Teams message details
   - `teams_chats`: Stores Teams chat details
   - `teams_chat_participants`: Stores chat participant information

3. **Functions**:
   - `hybrid_search`: Performs combined full-text and vector search
   - `get_teams_message_context`: Retrieves conversation context for a message

## Database Maintenance

For database backup and maintenance:

```bash
# Backup the database (from host)
docker exec ir_postgres pg_dump -U postgres mcp_ir > backup.sql

# Restore from backup (to a new database)
docker exec -i ir_postgres psql -U postgres -c "CREATE DATABASE mcp_ir_restore;"
docker exec -i ir_postgres psql -U postgres -d mcp_ir_restore < backup.sql
```

## Performance Tuning

The included `postgresql.conf` contains optimized settings for vector search, but you may want to adjust based on your system's resources:

- **shared_buffers**: Typically 25% of available RAM
- **effective_cache_size**: Typically 50-75% of available RAM
- **max_parallel_workers**: Set based on available CPU cores