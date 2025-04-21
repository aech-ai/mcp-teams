# MCP Information Retrieval (IR) Server

This module implements a standalone IR server that exposes information retrieval capabilities through a RESTful API, compatible with the Model Context Protocol (MCP). The system is designed to be used across multiple applications, including Microsoft Teams and other data sources. Based on our successful Scout Helpdesk implementation, it uses PostgreSQL with pgvector for robust, production-ready IR capabilities.

## Architecture Overview

The IR server follows these key architectural principles:

1. **PostgreSQL Foundation**: Built on PostgreSQL with pgvector for production-grade vector search
2. **Hybrid Search**: Combines full-text search and vector embeddings with rank fusion
3. **REST API Interface**: Exposes functionality through a simple HTTP API that can be consumed by MCP clients
4. **Modularity**: Clear separation between core IR logic, database layer, and data source adapters
5. **Reusability**: Designed to be used with Teams, email, documents, and other data sources

## System Components

The system consists of three main components that work together:

1. **PostgreSQL Database**: Stores indexed content and provides vector search capabilities
2. **IR Server**: Processes search requests and manages content indexing
3. **Teams MCP Server**: Connects to the IR server and exposes its functionality to Microsoft Teams

## Getting Started

### Prerequisites

- Docker and Docker Compose (recommended deployment method)
- PostgreSQL 14+ with pgvector extension (for standalone deployment)
- Python 3.9+ with required packages

### Running with Docker Compose

The easiest way to run the entire stack (PostgreSQL + IR Server + Teams MCP Server):

```bash
# Create a .env file with your configuration
cp .env.template .env
# Edit .env with your settings

# Start the services
docker-compose up -d
```

This will:
1. Start PostgreSQL with pgvector extension
2. Start the IR server connected to PostgreSQL
3. Start the Teams MCP server connected to the IR server

### Checking Status

To verify that all services are running properly:

```bash
# Check container status
docker-compose ps

# Check IR server logs
docker-compose logs ir_server

# Check Teams MCP server logs
docker-compose logs teams_mcp_server
```

The IR server should be accessible at http://localhost:8090/ and will respond with a health check message. The Teams MCP server runs on port 8000.

## API Usage

### IR Server REST API

The IR server exposes a RESTful API with the following endpoints:

#### Health Check
```
GET /
```
Returns a simple health check response:
```json
{"status": "ok", "message": "IR server is running"}
```

#### List Available Tools
```
GET /api/tools
```
Returns a list of available tools:
```json
{"tools": ["search", "index_content", "index_teams_messages", "get_content_count", "delete_content"]}
```

#### Search Content
```
POST /api/tools/search
```
Body:
```json
{
  "query": "your search query",
  "search_type": "hybrid",
  "limit": 10
}
```
Response:
```json
{
  "result": {
    "results": [
      {
        "id": "result-1",
        "content": "This is a search result matching your query",
        "score": 0.95,
        "metadata": {"source": "teams", "created": "2025-04-01T12:00:00Z"}
      },
      ...
    ],
    "metadata": {
      "total_results": 2,
      "search_type": "hybrid"
    }
  }
}
```

#### Index Content
```
POST /api/tools/index_content
```
Body:
```json
{
  "content": "text content to index",
  "source_type": "teams",
  "metadata": {"chat_id": "123", "sender": "user@example.com"}
}
```
Response:
```json
{
  "result": {
    "status": "success",
    "indexed_id": "doc-12345",
    "source_type": "teams"
  }
}
```

#### Get Content Count
```
POST /api/tools/get_content_count
```
Body:
```json
{
  "source_type": "teams"
}
```
Response:
```json
{
  "result": {
    "total": 1250,
    "by_source": {
      "teams": 1142,
      "email": 108
    }
  }
}
```

### Teams MCP Server API

The Teams MCP server exposes MCP tools including:

- `list_chats`: List all Teams chats
- `get_messages`: Get recent messages from a specified chat
- `send_message`: Send a message to a specified chat
- `search_messages`: Search over messages using hybrid search
- `search_messages_llm_rerank`: Advanced search with LLM reranking
- `ir_search`: Perform information retrieval search using the IR server

## Configuration Options

Configuration is loaded from environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| POSTGRES_HOST | PostgreSQL hostname | localhost |
| POSTGRES_PORT | PostgreSQL port | 5432 |
| POSTGRES_USER | PostgreSQL username | postgres |
| POSTGRES_PASSWORD | PostgreSQL password | |
| POSTGRES_DB | PostgreSQL database name | mcp_ir |
| OPENAI_API_KEY | OpenAI API key for embeddings | |
| EMBEDDING_MODEL | OpenAI model for embeddings | text-embedding-3-large |
| IR_SERVER_HOST | Hostname for the IR server | ir_server |
| IR_SERVER_PORT | Port for the IR server | 8090 |
| TEAMS_SERVER_PORT | Port for the Teams MCP server | 8000 |

## Customizing and Extending

### Adding New Search Features

To add new search capabilities to the IR server:

1. Modify the handler in `start_server.py` to add your new search features
2. Expose the new functionality through the API
3. Add corresponding client code in the Teams MCP server

### Adding New Data Sources

To add a new data source:

1. Create a new adapter in `ir/sources/` that implements `BaseAdapter`
2. Add adapter-specific database tables in a new migration
3. Update the IR server to handle the new source type
4. Register the adapter in the MCP server initialization

## Troubleshooting

### Common Issues

1. **Connection refused errors**: Ensure that all services are running and ports are correctly exposed in Docker Compose.
2. **Database connection errors**: Verify PostgreSQL connection settings and make sure the database is accessible.
3. **Missing OpenAI API key**: Set the OPENAI_API_KEY environment variable to a valid key.
4. **Server not starting**: Check logs with `docker-compose logs ir_server` for detailed error messages.

### Inspecting the API

You can use curl to test the IR server API directly:

```bash
# Test the health check endpoint
curl http://localhost:8090/

# Test the search endpoint
curl -X POST -H "Content-Type: application/json" -d '{"query": "test query", "search_type": "hybrid", "limit": 5}' http://localhost:8090/api/tools/search
```

## Technical Details

The IR server and Teams MCP server use two different approaches to expose functionality:

1. **IR Server**: Uses a FastAPI-based HTTP server that provides a simple REST API
2. **Teams MCP Server**: Uses the MCP protocol for client interactions and connects to the IR server over HTTP

This hybrid approach allows for flexible deployment scenarios while maintaining compatibility with MCP clients.