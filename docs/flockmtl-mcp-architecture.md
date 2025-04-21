# Dedicated MCP Server for FlockMTL and DuckDB

This document analyzes the benefits and proposes an architecture for creating a dedicated MCP server for FlockMTL and DuckDB. This design would modularize this aspect of the application, allowing it to be reused across different applications and accessed directly by LLMs or other MCP-enabled clients.

## Benefits of a Modular FlockMTL-DuckDB MCP Server

### 1. Reusability Across Applications
- **Plug-and-Play Integration**: Other applications could leverage advanced search and LLM capabilities without reimplementing them
- **Consistent Interface**: Standard MCP tools/resources for database and IR operations across systems
- **Reduced Development Time**: Teams using this server wouldn't need to build their own FlockMTL integration

### 2. Better Separation of Concerns
- **Domain Logic Separation**: Core database/search functionality separate from application-specific logic
- **Specialized Development**: Teams can focus on their domain while leveraging the FlockMTL capabilities
- **Independent Evolution**: Database layer can evolve independently of client applications

### 3. Scalability Advantages
- **Dedicated Resources**: Server can be scaled independently based on search/LLM workloads
- **Centralized Optimization**: Improvements to search algorithms benefit all connected applications
- **Resource Pooling**: Multiple applications can share resources for token management, embedding models, etc.

### 4. Enhanced LLM Integration
- **Direct Tool Access**: LLMs can use MCP to directly query and manipulate data
- **Unified Data Interface**: Single interface for both structured and unstructured data through SQL+FlockMTL
- **RAG Pipeline Standardization**: Standard patterns for retrieval-augmented generation

## Proposed Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                FlockMTL-DuckDB MCP Server                        │
├─────────────────┬──────────────────────┬────────────────────────┤
│   Core Layer    │   Extension Layer    │    Adapter Layer       │
├─────────────────┼──────────────────────┼────────────────────────┤
│ • DuckDB Engine │ • Schema Management  │ • Application Adapters │
│ • FlockMTL      │ • Search Extensions  │   - Teams Adapter      │
│   Extensions    │ • Index Management   │   - Email Adapter      │
│ • Embedding     │ • LLM Connectors     │   - Document Adapter   │
│   Generation    │ • Resource Management│ • Schema Transformers  │
└─────────────────┴──────────────────────┴────────────────────────┘
            ▲                 ▲                    ▲
            │                 │                    │
            ▼                 ▼                    ▼
┌────────────────┐  ┌────────────────┐  ┌────────────────────────┐
│ LLM Agents     │  │ Teams MCP App  │  │ Other MCP Applications │
│ (Direct Access)│  │                │  │                        │
└────────────────┘  └────────────────┘  └────────────────────────┘
```

### Core Layer
- Base DuckDB functionality and FlockMTL extensions
- Vector embedding generation and management
- Core storage and query execution

### Extension Layer
- Schema definition and management
- Search functionality (BM25, vector, fusion algorithms)
- LLM provider connections
- Prompt and model management

### Adapter Layer
- Application-specific adapters (Teams, Email, Documents)
- Schema transformers for different data sources
- Domain-specific MCP tools that build on core capabilities

## MCP Interface Design

The MCP server would expose:

### Resource Endpoints
- `tables` - List available tables and their schemas
- `models` - Available language models
- `prompts` - Available prompts
- `indexes` - Available search indexes

### Tool Endpoints
- **SQL Tool**: `execute_sql` - Run arbitrary SQL+FlockMTL queries
- **Schema Tools**: `create_table`, `alter_table`, etc.
- **Search Tools**:
  - `search` - Unified search across tables with configurable algorithms
  - `hybrid_search` - Advanced fusion-based search
  - `semantic_search` - Pure vector-based search
  - `keyword_search` - Pure BM25 search
- **LLM Tools**:
  - `llm_rerank` - Rerank results
  - `llm_summarize` - Summarize content
  - `llm_generate` - Generate content

## Handling Teams-Specific Logic

### Challenge
Current implementation has Teams-specific schemas and functionality embedded in the database layer:
- Teams chat/message schema 
- Teams-specific search functions
- Teams API integration logic

### Solutions

#### 1. Adapter Pattern
Create a Teams adapter in the Adapter Layer that:
- Maps the generic database schema to Teams-specific concepts
- Translates between Teams API objects and database records
- Provides Teams-specific MCP tools that build on core capabilities

```python
# Example: Teams adapter mapping
class TeamsAdapter:
    def __init__(self, db_connection):
        self.db = db_connection
        
    def store_message(self, teams_message):
        # Transform Teams message to generic schema
        generic_message = {
            "id": teams_message["id"],
            "sender": teams_message["from"]["user"]["displayName"],
            "content": teams_message["body"]["content"],
            "timestamp": teams_message["createdDateTime"],
            "metadata": json.dumps(teams_message)  # Store full object as metadata
        }
        # Store in generic messages table
        self.db.insert("messages", generic_message)
```

#### 2. Schema Abstraction
- Create abstract schemas that can work with multiple messaging platforms
- Use message, conversation, and user concepts that generalize beyond Teams
- Store platform-specific fields in JSON metadata columns

```sql
-- Example: Abstract schema
CREATE TABLE conversations (
    id TEXT PRIMARY KEY,
    title TEXT,
    type TEXT,  -- "teams_chat", "email_thread", etc.
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    metadata JSON  -- Platform-specific data
);

CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT REFERENCES conversations(id),
    sender_id TEXT,
    sender_name TEXT,
    content TEXT,
    created_at TIMESTAMP,
    platform TEXT,  -- "teams", "email", etc.
    metadata JSON,  -- Platform-specific data
    embedding BLOB,
    FOREIGN KEY(conversation_id) REFERENCES conversations(id)
);
```

#### 3. Plugin Architecture
- Design the server with a plugin system for platform-specific extensions
- Core FlockMTL-DuckDB functionality remains platform-agnostic
- Teams-specific functionality lives in a Teams plugin

```python
# Example: Plugin registration
class FlockMTLServer:
    def __init__(self):
        self.plugins = {}
        self.db = init_db()
    
    def register_plugin(self, name, plugin_instance):
        self.plugins[name] = plugin_instance
        plugin_instance.initialize(self.db)
        
    def get_plugin(self, name):
        return self.plugins.get(name)

# Teams plugin
teams_plugin = TeamsPlugin()
server.register_plugin("teams", teams_plugin)
```

## Implementation Strategy

1. **Extract Common Core**: Identify and extract platform-agnostic components
   - Database schema and operations
   - Search functionality
   - LLM functions

2. **Build Adapter Layer**: Create adapters for Teams and potentially other platforms
   - Mapping logic between specific APIs and generic schema
   - Platform-specific tooling built on generic capabilities

3. **Create Platform Plugins**: Develop plugins for platform-specific needs
   - Teams-specific authentication
   - Teams API integration
   - Teams-specific MCP tools

4. **Define Clear MCP Interface**: Create a well-documented MCP interface
   - Standard tools for database operations
   - Search capabilities
   - LLM integration

## Code Management and Repository Strategy

### Repository Structure

The FlockMTL-DuckDB MCP server should be managed as a **dedicated repository** with the following structure:

```
flockmtl-mcp-server/
├── core/                 # Core Layer components
│   ├── db/               # DuckDB connection and management
│   ├── embedding/        # Embedding generation utilities
│   └── schema/           # Base schema definitions
│
├── extensions/           # Extension Layer components
│   ├── search/           # Search functionality (BM25, fusion, etc.)
│   ├── llm/              # LLM connectors and functions
│   └── resource/         # Resource management (prompts, models)
│
├── adapters/             # Adapter Layer components
│   ├── teams/            # Teams-specific adapter
│   ├── email/            # Email-specific adapter
│   └── common/           # Shared adapter utilities
│
├── mcp/                  # MCP server implementation
│   ├── tools/            # Tool definitions
│   ├── resources/        # Resource definitions
│   └── server.py         # Main server implementation
│
├── examples/             # Example implementations and demos
│   ├── teams-integration/ # Example Teams integration
│   └── cli-client/       # Command-line client example
│
├── tests/                # Unit and integration tests
│
├── docs/                 # Documentation
│
├── pyproject.toml        # Python project configuration
└── README.md             # Repository documentation
```

### Integration Approaches

To maximize reusability, the project should support multiple integration methods:

#### 1. Python Package

Package the core functionality as a Python library that can be installed via pip:

```bash
pip install flockmtl-mcp-server
```

This allows Python applications to import and use the server programmatically:

```python
from flockmtl_mcp_server import FlockMTLServer
from flockmtl_mcp_server.adapters.teams import TeamsAdapter

# Initialize and run server
server = FlockMTLServer()
server.register_adapter(TeamsAdapter())
server.run()
```

#### 2. Docker Container

Provide a Docker image for easy deployment:

```bash
docker pull flockmtl/mcp-server
docker run -p 8000:8000 -v /path/to/data:/data flockmtl/mcp-server
```

This enables quick deployment without worrying about Python dependencies.

#### 3. Git Submodule

Support using the repository as a Git submodule:

```bash
git submodule add https://github.com/your-org/flockmtl-mcp-server.git
git submodule update --init --recursive
```

This allows for tight integration with existing projects while maintaining the codebase separately.

### Versioning Strategy

Implement semantic versioning (MAJOR.MINOR.PATCH) to clearly communicate compatibility:

- **MAJOR**: Breaking changes to the API
- **MINOR**: New functionality, non-breaking changes
- **PATCH**: Bug fixes and minor improvements

Use Git tags to mark stable releases:

```bash
git tag -a v1.0.0 -m "Initial stable release"
git push origin v1.0.0
```

### Adapter Management

For application-specific adapters (like Teams), use one of these approaches:

#### 1. Core + Extensions Repository

Include the Teams adapter in the main repository, but keep it clearly separated in the `adapters/teams` directory. This works well if:
- The number of adapters is limited
- Each adapter is relatively small
- Teams integration is a primary use case

#### 2. Separate Adapter Repositories

Maintain adapters in separate repositories:
- `flockmtl-mcp-server-teams-adapter`
- `flockmtl-mcp-server-email-adapter`

This is preferable when:
- Many adapters are expected
- Adapters have complex dependencies
- Different teams maintain different adapters

### Dependency Management

Use a combination of fixed and flexible dependency specifications:

- Core dependencies (DuckDB, MCP framework): Pin to specific versions
- Optional dependencies (LLM libraries): Allow version ranges
- Use dependency groups to separate required from optional dependencies

Example `pyproject.toml`:

```toml
[project]
name = "flockmtl-mcp-server"
version = "0.1.0"
dependencies = [
    "duckdb==1.1.1",
    "mcp-framework==0.5.0",
]

[project.optional-dependencies]
teams = ["msal>=1.20.0", "httpx>=0.24.0"]
openai = ["openai>=1.0.0"]
sentence-transformers = ["sentence-transformers>=2.2.2"]
```

### Extending with New Adapters

Document a clear process for creating new adapters:

1. Create a class that implements the `BaseAdapter` interface
2. Register schema transformations
3. Implement data mapping methods
4. Add adapter-specific MCP tools

Example:

```python
from flockmtl_mcp_server.adapters import BaseAdapter

class MyNewAdapter(BaseAdapter):
    def initialize(self, db):
        # Setup adapter
        pass
        
    def register_tools(self, mcp_server):
        # Register adapter-specific tools
        pass
```

## Potential Challenges

1. **Performance Overhead**: Additional abstraction layers could impact performance
2. **Schema Complexity**: Need to balance generic schemas with specific needs
3. **API Evolution**: Teams API changes might require adapter updates
4. **Cross-Platform Consistency**: Ensuring consistent behavior across platforms

## Comparison with BM25 vs. fusion_rrf

When considering search capabilities in the modular server, it's important to understand the advantages of fusion-based approaches over traditional methods:

### BM25 Limitations
- Purely lexical with no semantic understanding
- Cannot handle synonyms or related concepts without exact keyword matches
- No contextual understanding of query intent

### fusion_rrf Advantages
1. **Combines Multiple Signals**: Incorporates both lexical matches (BM25) and semantic similarity (vector embeddings)
2. **Improved Relevance**: Finds semantically relevant documents that don't contain exact query terms
3. **Robustness**: Less sensitive to the weaknesses of any single retrieval method
4. **Balance of Precision and Recall**: Better balance between finding exact matches and contextually relevant documents

The modular MCP server should implement the full range of FlockMTL fusion functions to provide optimal search capabilities across applications.

## Conclusion

Creating a dedicated MCP server for FlockMTL and DuckDB would provide significant benefits in terms of reusability, separation of concerns, and scalability. The Teams-specific logic can be effectively handled through adapters, schema abstraction, and a plugin architecture.

This approach would allow you to:
1. Use the same core search/LLM capabilities across applications
2. Allow direct LLM access to data via MCP
3. Support different messaging platforms with minimal code duplication
4. Evolve the database and application layers independently

The modular design would make the system more maintainable and extensible in the long run, allowing you to add support for new platforms without modifying the core functionality.

By structuring the code as a dedicated repository with clear layering, multiple integration options, and a plugin system for adapters, we can maximize reusability while maintaining flexibility for different use cases. 