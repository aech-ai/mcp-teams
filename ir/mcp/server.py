"""
MCP server implementation for the IR server.
Provides the main entry point for the MCP server.
"""

import logging
import sys
import asyncio
import os
from typing import Dict, Any, Optional

# Configure paths for module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)))

from mcp.server.fastmcp import FastMCP, Context

from ..config import MCP_SERVER_PORT, MCP_SERVER_HOST
from ..database.client import PostgresClient
from ..database.search import SearchManager
from ..database.indexed_content import ContentManager
from ..core.embeddings import EmbeddingGenerator
from ..sources.teams_adapter import TeamsAdapter
from .tools import MCPTools

# Import Teams client from parent project if needed, or mock it if unavailable
try:
    from teams.graph import GraphClient
except ImportError:
    # Mock GraphClient if not available
    class GraphClient:
        async def list_chats(self):
            return []
        async def get_messages(self, chat_id):
            return []
        async def send_message(self, chat_id, text):
            return {"id": "mock-message-id"}
        async def create_chat(self, user_id_or_email):
            return {"id": "mock-chat-id"}

logger = logging.getLogger(__name__)

class IRServer:
    """MCP server for information retrieval."""
    
    def __init__(self):
        """Initialize the IR server."""
        self.mcp = FastMCP("IR Server", log_level="INFO")
        self.db_client = None
        self.search_manager = None
        self.content_manager = None
        self.embedding_generator = None
        self.source_adapters = {}
        self.mcp_tools = None
        
        # Store last search results for resources
        self.last_search_results = {}
    
    async def initialize(self):
        """Initialize server components."""
        logger.info("Initializing IR server")
        
        # Initialize database client
        self.db_client = PostgresClient()
        await self.db_client.initialize()
        
        # Initialize core components
        self.embedding_generator = EmbeddingGenerator()
        self.search_manager = SearchManager(self.db_client)
        self.content_manager = ContentManager(self.db_client, self.embedding_generator)
        
        # Initialize source adapters
        teams_client = GraphClient()
        self.source_adapters["teams"] = TeamsAdapter(teams_client, self.content_manager)
        
        # Initialize and register MCP tools
        self.mcp_tools = MCPTools(
            self.search_manager,
            self.content_manager,
            self.embedding_generator,
            self.source_adapters
        )
        
        # Register MCP tools and resources
        self._register_tools()
        self._register_resources()
        
        logger.info("IR server initialized")
    
    def _register_tools(self):
        """Register MCP tools."""
        
        @self.mcp.tool()
        async def search(
            query: str,
            search_type: str = "hybrid", 
            source_type: Optional[str] = None,
            filters: Optional[Dict[str, Any]] = None,
            limit: int = 10,
            offset: int = 0,
            ctx: Optional[Context] = None
        ) -> Dict[str, Any]:
            """
            Search indexed content.
            
            Args:
                query: Search query text
                search_type: Type of search (hybrid, semantic, fulltext)
                source_type: Optional source type to filter by
                filters: Optional metadata filters
                limit: Maximum number of results to return
                offset: Offset for pagination
                
            Returns:
                Search results with metadata
            """
            client_id = str(ctx.client_id) if ctx else None
            results = await self.mcp_tools.search(
                query, search_type, source_type, filters, limit, offset, client_id
            )
            
            # Store results for resources
            if client_id:
                self.last_search_results[client_id] = results.get("results", [])
                
            return results
        
        @self.mcp.tool()
        async def index_content(
            content: str,
            source_type: str,
            metadata: Optional[Dict[str, Any]] = None,
            content_id: Optional[str] = None,
            source_id: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            Index a piece of content.
            
            Args:
                content: The text content to index
                source_type: Type of content source
                metadata: Optional metadata about the content
                content_id: Optional ID for the content
                source_id: Optional ID for the source system
                
            Returns:
                Indexing result
            """
            return await self.mcp_tools.index_content(
                content, source_type, metadata, content_id, source_id
            )
        
        @self.mcp.tool()
        async def index_teams_messages(
            chat_id: Optional[str] = None,
            since: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            Index messages from Teams.
            
            Args:
                chat_id: Optional specific chat to index
                since: Optional timestamp to index messages after
                
            Returns:
                Indexing result
            """
            return await self.mcp_tools.index_teams_messages(chat_id, since)
        
        @self.mcp.tool()
        async def get_content_count(
            source_type: Optional[str] = None,
            source_id: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            Get count of indexed content.
            
            Args:
                source_type: Optional type of content source to count
                source_id: Optional specific source ID to count
                
            Returns:
                Content count
            """
            return await self.mcp_tools.get_content_count(source_type, source_id)
        
        @self.mcp.tool()
        async def delete_content(
            content_id: Optional[str] = None,
            source_type: Optional[str] = None,
            source_id: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            Delete indexed content.
            
            Args:
                content_id: Optional ID of specific content to delete
                source_type: Optional type of content source to delete
                source_id: Optional specific source ID to delete
                
            Returns:
                Deletion result
            """
            return await self.mcp_tools.delete_content(content_id, source_type, source_id)
    
    def _register_resources(self):
        """Register MCP resources."""
        
        # The search_results resource needs to match the URI parameters, and ctx is not
        # part of the URI, so we need to handle it in the function body
        @self.mcp.resource("mcp://ir/search_results")
        def search_results():
            """Live resource for search results."""
            # Get the client ID from the current context if available
            context = getattr(self.mcp, "current_context", None)
            if not context:
                return []
                
            client_id = str(context.client_id) if context else None
            if not client_id or client_id not in self.last_search_results:
                return []
                
            return self.last_search_results.get(client_id, [])
        
        @self.mcp.resource("mcp://ir/sources")
        def sources():
            """Live resource for configured data sources."""
            return [
                {"source_type": source_type, "available": True}
                for source_type in self.source_adapters
            ]
    
    async def run(self):
        """Run the IR server."""
        await self.initialize()
        # MCP FastMCP doesn't accept port/host arguments directly
        # Configure through environment variables instead
        os.environ["PORT"] = str(MCP_SERVER_PORT)
        os.environ["HOST"] = MCP_SERVER_HOST
        logger.info(f"Starting MCP server on {MCP_SERVER_HOST}:{MCP_SERVER_PORT}")
        # Use run_stdio() if available, otherwise fall back to run()
        if hasattr(self.mcp, "run_stdio"):
            self.mcp.run_stdio()
        else:
            self.mcp.run()
    
    async def shutdown(self):
        """Shutdown the IR server."""
        if self.db_client:
            await self.db_client.close()

def main():
    """Main entry point for the IR server (non-async version)."""
    import importlib
    import json
    import socket
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Verify MCP module
    try:
        mcp_module = importlib.import_module("mcp.server.fastmcp")
        logger.info(f"MCP module found: {mcp_module}")
        logger.info(f"Available attributes: {dir(mcp_module)}")
    except ImportError as e:
        logger.error(f"Error importing MCP module: {e}")
    
    # Diagnostic check - Check if port is already in use
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((MCP_SERVER_HOST, MCP_SERVER_PORT))
        s.close()
        logger.info(f"Port {MCP_SERVER_PORT} is available")
    except Exception as e:
        logger.error(f"Port {MCP_SERVER_PORT} is NOT available: {e}")
    
    try:
        # Initialize without running async code
        server = IRServer()
        
        # Set environment variables
        os.environ["PORT"] = str(MCP_SERVER_PORT)
        os.environ["HOST"] = MCP_SERVER_HOST
        os.environ["MCP_HTTP"] = "1"  # Enable HTTP interface
        
        # Register a simple HTTP tool for diagnostics
        @server.mcp.tool()
        def health_check():
            """Simple health check."""
            return {"status": "ok", "message": "IR server is running"}
        
        # Print available methods on mcp
        logger.info(f"MCP methods: {[m for m in dir(server.mcp) if not m.startswith('_')]}")
        
        logger.info(f"Starting MCP server on {MCP_SERVER_HOST}:{MCP_SERVER_PORT} with HTTP interface enabled")
        # Run without await
        server.mcp.run()
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        import traceback
        logger.error(traceback.format_exc())

# Async version for command line usage
async def async_main():
    """Main entry point for the IR server (async version)."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    server = IRServer()
    try:
        await server.run()
    except KeyboardInterrupt:
        logger.info("Shutting down IR server")
        await server.shutdown()

if __name__ == "__main__":
    # Use async version when run directly
    asyncio.run(async_main())