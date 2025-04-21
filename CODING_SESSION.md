# MCP-Teams: Development Session Documentation

This document provides a comprehensive record of the development session for the MCP-Teams project, which integrates Microsoft Teams with a PostgreSQL-based Information Retrieval (IR) system using the Model Context Protocol (MCP).

## Session Overview

In this session, we developed a system that combines:

1. A Teams MCP server that integrates with Microsoft Graph API
2. A PostgreSQL-based Information Retrieval (IR) server with vector search capabilities
3. Docker containerization for easy deployment
4. Comprehensive documentation and configuration

The architecture enables LLMs and agentic clients to interact with Teams data via MCP tools, resources, and events, while leveraging advanced search capabilities through the IR server.

## Development Process

### Phase 1: Initial Architecture and Requirements Analysis

We began by analyzing the requirements for a system that would:
- Connect Microsoft Teams with MCP-compatible clients
- Implement advanced search capabilities using PostgreSQL with pgvector
- Support Docker-based deployment
- Provide comprehensive documentation

### Phase 2: Implementation of Core Components

#### Teams MCP Server
- Created server.py to implement MCP tools and resources for Teams interaction
- Set up DuckDB schema for message storage
- Implemented Microsoft Graph API client for Teams integration

#### PostgreSQL IR Server
- Designed a database schema optimized for hybrid search
- Implemented vector embeddings generation with OpenAI API
- Created database migrations with Alembic
- Built HTTP API endpoints for search, indexing, and content management

#### Inter-Service Communication
- Implemented HTTP-based communication between Teams MCP server and IR server
- Created a stateless API design for reliable communication

### Phase 3: Docker Containerization and Configuration

- Created Dockerfiles for Teams MCP server, IR server, and PostgreSQL
- Set up docker-compose.yml for orchestrating the services
- Configured environment variables for seamless deployment
- Implemented health checks and container dependencies
- Exposed necessary ports for service communication

### Phase 4: Documentation and Testing

- Created comprehensive README.md with setup and usage instructions
- Updated app-spec.md with detailed architecture documentation
- Added API documentation for both servers
- Implemented environment variable templates
- Configured .gitignore to exclude unnecessary files

### Phase 5: Final Integration and Deployment

- Tested end-to-end communication between services
- Made final adjustments to API endpoints and error handling
- Created GitHub repository and pushed code
- Organized documentation for future development

## Technical Challenges Solved

1. **HTTP Communication Between Services**: Initially attempted to use FastMCP for the IR server, but encountered issues with HTTP binding. Resolved by implementing a FastAPI-based REST API instead.

2. **Container Networking**: Addressed Docker networking challenges by properly configuring service discovery and port exposure.

3. **Vector Search Implementation**: Successfully integrated pgvector extension with PostgreSQL for efficient vector similarity search.

4. **MCP Integration**: Implemented proper MCP tools that served as a bridge to the IR server's HTTP API.

5. **Database Migrations**: Created Alembic migrations for PostgreSQL schema evolution, ensuring reliable database updates.

## Architecture Overview

```
+-------------------+      +-------------------+      +-------------------+
|   CLI MCP Client  |<---->|    MCP Server     |<---->|  Microsoft Teams  |
| (rich terminal UI)|      | (Python, FastMCP) |      |  (Graph API)      |
+-------------------+      +-------------------+      +-------------------+
         |                        |                          
         |                        v                          
         |                +-------------------+      +-------------------+
         |                |     DuckDB DB     |      |    IR Server      |
         |                +-------------------+      | (PostgreSQL, API) |
                                                     +-------------------+
                                                              |
                                                              v
                                                     +-------------------+
                                                     |  PostgreSQL DB    |
                                                     |  (with pgvector)  |
                                                     +-------------------+
```

### Key Components:

1. **Teams MCP Server**: Pure MCP server that exposes Teams functionality via MCP tools, resources, and events.
2. **IR Server**: FastAPI-based server that provides advanced search capabilities using PostgreSQL with pgvector.
3. **PostgreSQL**: Database with pgvector extension for hybrid search capabilities.
4. **DuckDB**: Local database for Teams MCP server to store chat and message history.
5. **CLI Tools**: Tools for login and MCP client interaction.

## IR Server API Endpoints

The IR server exposes several HTTP endpoints:

```
GET /
GET /api/tools
POST /api/tools/search
POST /api/tools/index_content
POST /api/tools/index_teams_messages
POST /api/tools/get_content_count
POST /api/tools/delete_content
```

## MCP Tools Implementation

The Teams MCP server implements tools that bridge to the IR server:

```python
@mcp.tool()
async def ir_search(query: str, search_type: str = "hybrid", limit: int = 10) -> dict:
    """Perform information retrieval search using the IR server."""
    # Implementation using HTTP calls to IR server
```

## Docker Deployment Instructions

The system is set up for easy deployment with Docker Compose:

```bash
# Configure environment variables
cp .env.template .env
# Edit .env with your settings

# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f teams_mcp  # Teams MCP server logs
docker-compose logs -f ir_server  # IR server logs
```

## Environment Configuration

The system uses a comprehensive .env file for configuration:

```
# Microsoft Teams / Graph API Configuration
AZURE_CLIENT_ID=
AZURE_CLIENT_SECRET=
AZURE_TENANT_ID=
AZURE_APP_OBJECT_ID=

# PostgreSQL Configuration (for IR Server)
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=mcp_ir

# OpenAI API Configuration (for embeddings)
OPENAI_API_KEY=your_openai_api_key
EMBEDDING_MODEL=text-embedding-3-large
EMBEDDING_DIMENSIONS=1536
```

## Repository Structure

- `/ir/`: IR server implementation
- `/mcp_server/`: Teams MCP server implementation
- `/cli/`: CLI tools for login and MCP client interaction
- `/db/`: Database schema and utilities
- `/teams/`: Microsoft Teams integration
- `/docs/`: Documentation files
- `/specs/`: Project specifications
- `/postgres_setup/`: PostgreSQL setup scripts

## Conclusion

This development session successfully created a fully functional integration between Microsoft Teams and a PostgreSQL-based Information Retrieval system using the Model Context Protocol. The system provides a robust foundation for building LLM-powered applications that can interact with Teams data while leveraging advanced search capabilities.

The code is now hosted at [https://github.com/aech-ai/mcp-teams](https://github.com/aech-ai/mcp-teams) and ready for further development and deployment.

---

🤖 Generated with [Claude Code](https://claude.ai/code)