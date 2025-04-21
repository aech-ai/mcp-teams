# Teams Messenger MCP App – Product Specification (MCP-Only Edition)

## Overview

**Teams Messenger MCP App** is a pure Model Context Protocol (MCP) server that acts as a bridge between Microsoft Teams and MCP-compatible clients, such as LLMs and agentic frameworks. All logic and features are exposed exclusively via MCP resources, tools, and events—there is no REST API server. The CLI is used only for local login and token management; all chat operations, message polling, and event subscriptions are handled through the MCP server for consumption by LLMs and other MCP clients.

---

## Additional Requirement: Rich CLI MCP Client

A rich Command-Line Interface (CLI) must be created as a fully-featured MCP client. This CLI will:
- Interface directly with the MCP server for local testing, usage, and verification.
- Provide a rich terminal UI for interacting with all MCP features (tools, resources, events).
- Allow users to list chats, select chats, send and receive messages, and subscribe to live resources/events, all via MCP.
- Serve as both a test harness for MCP server development and a user-facing tool for Teams messaging via MCP.
- Exercise and demonstrate all MCP features, including live resource/event subscriptions and tool invocation.

---

## Purpose

The primary goal of this application is to provide seamless, near real-time integration between Microsoft Teams and LLMs or agentic clients via MCP, with:

- Messaging with Microsoft Teams chats, fully exposed as MCP resources.
- Listing and selecting available chats via MCP tools/resources.
- Sending and receiving messages, and subscribing to new message events, via MCP.
- Automatic, indefinite token refresh for uninterrupted operation.
- Persistent token storage to allow the agent to operate across server restarts without manual login.
- Persistent storage of chat and message history in DuckDB, enabling advanced search and RAG (Retrieval-Augmented Generation) applications.
- **PostgreSQL-based Information Retrieval (IR) Server:** Advanced search capabilities with PostgreSQL and pgvector, exposed via HTTP API for the MCP server.
- **Hybrid Semantic and Lexical Search:** Support for both vector (embedding-based) and BM25 (full-text) search over messages, with hybrid/fusion pipelines and LLM-driven analytics, as described in [FlockMTL](https://arxiv.org/html/2504.01157v1).
- No REST API endpoints for the Teams MCP server—MCP is the only interface.
- **Single agent account:** The MCP server is intended to be connected to a single Microsoft 365 (M365) AI agent account, not for multiple users.

---

## Key Features

### 1. **Microsoft Teams Integration (via MCP)**
- **Authentication:** CLI initiates Microsoft Azure AD OAuth2 login for secure access to Teams data. In demo mode, authentication is simulated for easy testing.
- **Automatic Token Refresh & Persistent Storage:** The system automatically refreshes tokens as needed and securely stores them, ensuring indefinite operation and seamless recovery across server restarts without manual intervention. The token cache is persisted for reliability.
- **Chat Listing:** MCP tool/resource to retrieve and display all chats the agent account is a member of, including group and one-on-one chats. Chat IDs are shown in abbreviated form for usability.
- **Message Sending:** MCP tool to send messages to any chat the agent has access to.
- **Message Receiving (Polling):** The MCP server polls the Microsoft Graph API for new messages in all chats at regular intervals, exposing new messages as events on a live MCP resource.
- **Agent-Initiated Chat Creation:** The MCP server can create a new chat with any user in the M365 domain and send messages, enabling the agent to proactively notify or interact with users for agentic workflows (e.g., task assignment, async notifications).
- **Persistent Storage with DuckDB:** All chat and message history is stored in a DuckDB database for the Teams MCP server, enabling efficient search, analytics, and RAG (Retrieval-Augmented Generation) workflows.

### 2. **PostgreSQL-based Information Retrieval (IR) Server**
- **Advanced Search Capabilities:** The IR server provides sophisticated search functionalities using PostgreSQL with pgvector extension.
- **HTTP API Interface:** Exposes endpoints for search, indexing, and retrieval that are called by the MCP server.
- **Hybrid Search Implementation:**
  - **Vector Search:** Embedding-based semantic search using pgvector.
  - **Full-text Search:** Lexical search using PostgreSQL's full-text capabilities.
  - **Hybrid Fusion:** Combining both approaches with Reciprocal Rank Fusion.
- **Content Indexing:** Tools for indexing content from various sources, including Teams messages.
- **Modular Architecture:** Clean separation between MCP server and IR functionality.
- **Containerized Deployment:** Runs in its own Docker container, communicating with the Teams MCP server via HTTP.

### 3. **MCP-Only Architecture for Teams Server**
- **No REST API:** All Teams features are exposed via MCP tools, resources, and events. There are no REST endpoints for chat, message, or user operations.
- **MCP Tools:**
  - `list_chats`: Returns a list of available chats (with abbreviated IDs).
  - `send_message`: Sends a message to a specified chat.
  - `get_messages`: Retrieves recent messages from a specified chat.
  - `create_chat`: Creates a new chat with any user in the M365 domain.
  - **IR Integration Tools:** Expose the IR server's search capabilities through MCP, including:
    - `ir_search`: Search content using the IR server.
    - `ir_index_content`: Index content in the IR server.
    - `ir_index_teams_messages`: Index Teams messages in the IR server.
    - `ir_get_content_count`: Get counts of indexed content.
    - `ir_delete_content`: Delete content from the IR index.
- **MCP Resources:**
  - `chats`: Live resource representing the agent's available chats.
  - `messages/incoming`: Live resource representing incoming messages, updated via polling.
- **MCP Events:**
  - LLMs and other MCP clients can subscribe to resources (e.g., `messages/incoming`) and receive events such as new messages as soon as they are detected by polling.

### 4. **Polling for New Messages**
- **Polling Mechanism:** The MCP server periodically queries the Microsoft Graph API for new messages in all chats. The polling interval is configurable (e.g., every 10 seconds).
- **Event Emission:** When a new message is detected, the MCP server emits an event on the `messages/incoming` resource, which can be consumed by LLMs or other MCP clients.
- **Message Deduplication:** The server tracks the latest message IDs to avoid duplicate events.
- **Trade-offs:** Polling is less immediate than webhooks, but works in environments where a public HTTP endpoint is not possible.

### 5. **CLI for Local Login and Token Management**
- **Login Flow:** The CLI is used to initiate the Microsoft login process and manage the local session.
- **Session Persistence:** The CLI maintains session state and ensures the MCP server has valid tokens at all times.
- **No Chat/Message Logic:** The login CLI does not handle chat listing, message sending, or event subscription—these are all handled by the MCP server for LLMs/clients. The rich CLI MCP client exercises all MCP features for local testing and usage.

### 6. **LLM/Agentic Client Integration**
- **Live Resource Subscription:** LLMs and agentic clients can subscribe to MCP resources (e.g., `messages/incoming`) and receive events for new messages, chat updates, etc.
- **Tool Invocation:** LLMs can invoke MCP tools to list chats, send messages, create new chats, or fetch message history.
- **Abbreviated Chat IDs:** All chat references use abbreviated IDs for usability in LLM prompts and tool calls.
- **Advanced Search and RAG:** The persistent storage in both DuckDB and PostgreSQL enables advanced search and retrieval-augmented generation (RAG) workflows for LLMs and agentic clients.

---

## System Architecture

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

- **MCP Server:** The core of the app, exposing all Teams integration features via MCP tools, resources, and events.
- **Microsoft Graph API:** Used for all Teams data operations (listing chats, sending/receiving messages, creating new chats).
- **Polling Mechanism:** The MCP server periodically calls the Graph API to fetch new messages and emits events on MCP resources.
- **CLI Application:** Used only for local login and token management; does not expose chat or message logic.
- **Rich CLI MCP Client:** A separate CLI application that acts as a full-featured MCP client, interfacing with the MCP server for local testing and usage.
- **Persistent Token Storage:** Tokens are securely stored to allow seamless operation across server restarts.
- **DuckDB Storage:** Chat and message history for the Teams MCP server is stored in DuckDB.
- **IR Server:** Provides advanced search capabilities using PostgreSQL with pgvector, exposed via HTTP API.
- **PostgreSQL with pgvector:** Database for the IR server, offering vector search capabilities.

---

## IR Server API Specification

The IR server provides a RESTful HTTP API for interaction with the Teams MCP server:

### Endpoints

1. **Health Check**
   - `GET /`: Returns the status of the IR server.

2. **List Available Tools**
   - `GET /api/tools`: Returns a list of available search and indexing tools.

3. **Search Content**
   - `POST /api/tools/search`: Performs a search operation.
   - Parameters:
     - `query`: The search query string.
     - `search_type`: Type of search (hybrid, vector, or fulltext).
     - `limit`: Maximum number of results to return.

4. **Index Content**
   - `POST /api/tools/index_content`: Indexes generic content.
   - Parameters:
     - `content`: The text content to index.
     - `source_type`: Source type (e.g., teams, email).
     - `metadata`: Additional metadata for the content.

5. **Index Teams Messages**
   - `POST /api/tools/index_teams_messages`: Specialized endpoint for indexing Teams messages.
   - Parameters:
     - `messages`: Array of message objects from Teams.
     - `chat_id`: Identifier for the Teams chat.

6. **Get Content Count**
   - `POST /api/tools/get_content_count`: Returns counts of indexed content.
   - Parameters:
     - `source_type`: Optional filter by source type.

7. **Delete Content**
   - `POST /api/tools/delete_content`: Removes content from the index.
   - Parameters:
     - `content_id`: ID of the content to delete.
     - `source_type`: Optional filter by source type.

---

## CLI Application Specification

- **Authentication:** CLI launches and prompts the user to log in via Microsoft (or enters demo mode). In real mode, the CLI opens a browser for OAuth2 login and waits for completion. In demo mode, login is simulated.
- **Token Refresh & Persistence:** The CLI and MCP server coordinate to refresh tokens automatically and persist them for indefinite operation and recovery after restarts.
- **No Chat/Message Logic:** The login CLI does not handle chat listing, message sending, or event subscription—these are all handled by the MCP server for LLMs/clients. The rich CLI MCP client exercises all MCP features for local testing and usage.
- **Persistent Storage:** All chat and message data is stored for search and RAG applications.
- **IR Integration:** The CLI can access all IR capabilities through the MCP server.

---

## MCP Tools, Resources, and Events

### Tools
- `list_chats`: Returns a list of available chats (with abbreviated IDs).
- `send_message`: Sends a message to a specified chat.
- `get_messages`: Retrieves recent messages from a specified chat.
- `create_chat`: Creates a new chat with any user in the M365 domain.
- `ir_search`: Search content using the IR server.
- `ir_index_content`: Index content in the IR server.
- `ir_index_teams_messages`: Index Teams messages in the IR server.
- `ir_get_content_count`: Get counts of indexed content.
- `ir_delete_content`: Delete content from the IR index.

### Resources
- `chats`: Live resource representing the agent's available chats.
- `messages/incoming`: Live resource representing incoming messages, updated via polling.

### Events
- **New Message Event:** When a new message is detected in any chat, the MCP server emits an event on `messages/incoming` with the message details.
- **Chat Update Event:** If chat membership or metadata changes, the MCP server emits an event on `chats`.

---

## Modes of Operation

- **Demo Mode:** All Teams operations are simulated with mock data. No real authentication or network calls are made.
- **Real Mode:** Requires valid Azure AD credentials. All Teams operations interact with the real Microsoft Graph API. No public endpoint is required for polling.

---

## Security & Authentication

- **OAuth2 with Azure AD:** Used for authenticating users and obtaining access tokens for Microsoft Graph.
- **Automatic Token Management & Persistence:** Tokens are refreshed and stored automatically for uninterrupted operation and seamless recovery after restarts.
- **DuckDB Security:** Persistent storage for Teams data is managed securely using DuckDB.
- **PostgreSQL Security:** The IR server's data is stored securely in PostgreSQL.

---

## Deployment & Configuration

- **Environment Variables:** Used for configuration (client ID, secret, tenant ID, database credentials, etc.).
- **Command-Line Arguments:** Can override port and demo mode at startup.
- **Docker Compose:** Recommended deployment method for running all services together.
- **Polling Interval:** The frequency of polling for new messages is configurable.
- **Token Storage Location:** The location and method for secure persistent token storage is configurable.
- **Database Storage Location:** The locations of both the DuckDB and PostgreSQL databases are configurable.

---

## Logging & Monitoring

- **Logging:** All major actions, errors, and events are logged for debugging and monitoring.
- **Connection Stats:** Tracks and exposes connection statistics for operational insight.

---

## Intended Users

- **LLMs and Agentic Clients:** Integrate Teams messaging and advanced search into their workflows via MCP tools, resources, and events.
- **Developers:** Build LLM-powered automations or agents that interact with Teams via MCP.
- **Testers:** Use demo mode for development and testing without needing real Teams credentials.
- **CLI Users:** Use the rich CLI MCP client for local testing, verification, and interactive Teams messaging via MCP.
- **Single Agent Account:** The MCP server is designed for a single AI agent account (M365), serving as the interface for business users to interact with the agent via Teams chat or email. Business users can message the agent, and the agent can proactively reach out to users as needed.

---

## Limitations

- **Polling Delay:** There may be a delay (up to the polling interval) before new messages are displayed.
- **Network Dependency:** The IR server and Teams MCP server must be able to communicate via HTTP.

---

## Future Enhancements

- **Advanced Message Handling:** Support for attachments, rich content, and message threads.
- **Improved Error Handling:** More robust handling of API errors and token expiration.
- **Optional Webhook Support:** If a public endpoint becomes available, add support for webhooks for true real-time updates.
- **CLI UI Enhancements:** Further enrich the CLI MCP client with features like tab completion, chat search, message filtering, and more interactive terminal UI elements.
- **IR Server Enhancements:** Add support for more content types, improved ranking algorithms, and multi-modal search.

---

## Summary

The Teams Messenger MCP App is a robust, extensible system that bridges Microsoft Teams with MCP-compatible clients through a pure MCP server interface. The PostgreSQL-based IR server complements this with advanced search capabilities, enabling sophisticated information retrieval and RAG workflows. With automatic token refresh, persistent storage, agent-initiated chat creation, and polling-based event emission, it enables near real-time, uninterrupted integration with Microsoft Teams—without requiring any REST API endpoints or public web exposure for the Teams integration. The system is designed for a single AI agent account, providing a unified chat and search interface for business users to interact with the agent.

---

**References:**
- [Beyond Quacking: Deep Integration of Language Models and RAG into DuckDB (FlockMTL)](https://arxiv.org/html/2504.01157v1)
- [PostgreSQL with pgvector extension](https://github.com/pgvector/pgvector)