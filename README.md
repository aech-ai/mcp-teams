# Teams Messenger MCP App

This project implements a pure Model Context Protocol (MCP) server that bridges Microsoft Teams and MCP-compatible clients (LLMs, agentic frameworks, and a rich CLI MCP client). All features are exposed via MCP tools, resources, and events—no REST API endpoints.

## Features
- Microsoft Teams chat/message integration via MCP
- PostgreSQL-based Information Retrieval (IR) server for advanced search capabilities
- Persistent storage in DuckDB for chat/message history
- Hybrid semantic and lexical search (BM25 + vector, FlockMTL-style)
- CLI for login/token management and a rich MCP client for local testing
- Polling-based event emission for new messages
- Live event streaming and search for LLMs and CLI
- Single-agent (bot) account, not multi-user

## Architecture
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
- All chat/message/search logic is via MCP tools/resources/events
- Teams MCP server uses DuckDB for message storage
- IR server provides advanced search capabilities with PostgreSQL and pgvector
- IR server exposes an HTTP API for MCP server communication

## Installation

### Requirements
- Python 3.9+
- [pip](https://pip.pypa.io/en/stable/)
- [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/) (for containerized deployment)

### Option 1: Local Installation

#### 1. Clone the repository
```bash
git clone <your-repo-url>
cd mcp-teams
```

#### 2. Install dependencies
```bash
pip install -r requirements.txt
```

#### 3. Configure environment variables
Copy the template and fill in your Azure AD/Teams credentials:
```bash
cp .env.template .env
# Edit .env and fill in your Azure AD and other settings
```
See the table below for variable descriptions.

### Option 2: Docker Deployment (Recommended)

#### 1. Clone the repository
```bash
git clone <your-repo-url>
cd mcp-teams
```

#### 2. Configure environment variables
Copy the template and fill in your credentials:
```bash
cp .env.template .env
# Edit .env and fill in your settings
```

#### 3. Build and start services
```bash
docker-compose up -d
```

## Environment Variables (.env)

| Variable            | Description                                                      | Example / Default           |
|---------------------|------------------------------------------------------------------|-----------------------------|
| AZURE_CLIENT_ID      | Azure AD Application (client) ID                                 | `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` |
| AZURE_CLIENT_SECRET  | Azure AD Application secret                                      | `your-secret`               |
| AZURE_TENANT_ID      | Azure AD Tenant ID                                               | `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` |
| AZURE_APP_OBJECT_ID  | Azure AD Application object ID                                  | `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` |
| DUCKDB_PATH         | Path to DuckDB database file                                     | `db/teams_mcp.duckdb`       |
| TOKEN_PATH          | Path to store persistent token cache                             | `db/token_cache.json`        |
| POLL_INTERVAL       | Polling interval (seconds) for new messages                      | `10`                        |
| DEMO_MODE           | Set to `true` for mock/demo mode (no real Teams API calls)       | `false`                     |
| OPENAI_API_KEY      | OpenAI API key for embedding generation                         | `sk-...`                    |
| POSTGRES_USER       | PostgreSQL username                                              | `postgres`                  |
| POSTGRES_PASSWORD   | PostgreSQL password                                              | `postgres`                  |
| POSTGRES_DB         | PostgreSQL database name                                         | `mcp_ir`                    |
| IR_SERVER_HOST      | IR server hostname                                               | `ir_server`                 |
| IR_SERVER_PORT      | IR server port                                                   | `8090`                      |

## Running the MCP Server

### Local Mode (without Docker)
```bash
python mcp_server/server.py
```

### Docker Mode (All Services)
```bash
docker-compose up -d
```

To check logs:
```bash
docker-compose logs -f teams_mcp  # Teams MCP server logs
docker-compose logs -f ir_server  # IR server logs
```

### Demo Mode (no real Teams API calls)
Set `DEMO_MODE=true` in your `.env` and run as above.

## CLI Usage

### 1. Login and Token Management
```bash
python cli/login.py login
python cli/login.py status
python cli/login.py logout
```

### 2. Rich CLI MCP Client
All commands below use the MCP stdio protocol to talk to the server.

#### List chats
```bash
python cli/mcp_client.py list_chats
```

#### Get messages from a chat
```bash
python cli/mcp_client.py get_messages <chat_id>
```

#### Send a message
```bash
python cli/mcp_client.py send_message <chat_id> "Hello from CLI!"
```

#### Create a new 1:1 chat
```bash
python cli/mcp_client.py create_chat <user_id_or_email>
```

#### Search messages (hybrid, BM25, or vector)
```bash
python cli/mcp_client.py search_messages "project update" --mode hybrid --top_k 5
```

#### Stream new incoming messages (live event subscription)
```bash
python cli/mcp_client.py stream
```

## IR Server Usage

The IR server provides advanced search capabilities with PostgreSQL and pgvector. It exposes an HTTP API for MCP server communication.

### IR Server API Endpoints

#### 1. Health Check
```
GET http://localhost:8090/
```

#### 2. List Available Tools
```
GET http://localhost:8090/api/tools
```

#### 3. Search Content
```
POST http://localhost:8090/api/tools/search
```
Body:
```json
{
  "query": "your search query",
  "search_type": "hybrid",
  "limit": 10
}
```

#### 4. Index Content
```
POST http://localhost:8090/api/tools/index_content
```
Body:
```json
{
  "content": "Text content to index",
  "source_type": "teams",
  "metadata": {
    "author": "User Name",
    "created": "2025-04-01T12:00:00Z"
  }
}
```

For more detailed IR server documentation, see [ir/README.md](ir/README.md).

## Search and Event Streaming
- **Hybrid search**: Combines BM25 and vector search with LLM reranking
- **Live streaming**: Subscribe to `messages/incoming` for real-time updates

## Development & Extension
- Add new MCP tools/resources in `mcp_server/server.py`
- Extend Teams integration in `teams/graph.py`
- Modify IR capabilities in the IR server
- Add analytics, summarization, or RAG features using DuckDB, PostgreSQL, and LLMs
- Use the CLI as a test harness for all MCP features

## Troubleshooting & FAQ
- **Login fails**: Check your Azure AD credentials and `.env` values
- **No messages appear**: Ensure polling is running and your bot account is in the Teams chat
- **DuckDB errors**: Check file permissions and paths in `.env`
- **IR server not responding**: Check Docker logs and ensure the container is running
- **Demo mode**: Set `DEMO_MODE=true` for local testing without real Teams

## References
- [Beyond Quacking: Deep Integration of Language Models and RAG into DuckDB (FlockMTL)](https://arxiv.org/html/2504.01157v1)
- [Model Context Protocol documentation](https://modelcontextprotocol.io)
- [Microsoft Graph API docs](https://learn.microsoft.com/en-us/graph/overview)
- [PostgreSQL with pgvector extension](https://github.com/pgvector/pgvector)

---
For full product details, see [`specs/app-spec.md`](specs/app-spec.md).