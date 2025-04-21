"""
MCP tools for the IR server.
Defines tools for search, indexing, and management.
"""

import logging
from typing import List, Dict, Any, Optional, Union, Tuple
import json
import asyncio

from ..core.embeddings import EmbeddingGenerator
from ..database.search import SearchManager
from ..database.indexed_content import ContentManager
from ..sources.teams_adapter import TeamsAdapter

logger = logging.getLogger(__name__)

class MCPTools:
    """MCP tools for the IR server."""
    
    def __init__(
        self, 
        search_manager: SearchManager,
        content_manager: ContentManager,
        embedding_generator: EmbeddingGenerator,
        source_adapters: Dict[str, Any]
    ):
        """Initialize MCP tools."""
        self.search_manager = search_manager
        self.content_manager = content_manager
        self.embedding_generator = embedding_generator
        self.source_adapters = source_adapters
        
        # Track the last search results for each client
        self.last_search_results = {}
    
    async def search(
        self,
        query: str,
        search_type: str = "hybrid",
        source_type: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        offset: int = 0,
        client_id: Optional[str] = None
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
            client_id: Optional client ID for tracking results
            
        Returns:
            Search results with metadata
        """
        logger.info(f"Search request: query='{query}', type={search_type}, source={source_type}")
        
        try:
            # Transform query if source adapter exists
            if source_type and source_type in self.source_adapters:
                adapter = self.source_adapters[source_type]
                query = await adapter.transform_query(query)
            
            # Generate embedding for semantic or hybrid search
            embedding = None
            if search_type in ["semantic", "hybrid"]:
                embedding = await self.embedding_generator.get_embedding(query)
            
            # Perform search
            results = await self.search_manager.search(
                query=query,
                embedding=embedding,
                search_type=search_type,
                limit=limit,
                source_type=source_type,
                filters=filters
            )
            
            # Store results if client_id provided
            if client_id:
                self.last_search_results[client_id] = results
            
            # Format results
            response = {
                "query": query,
                "search_type": search_type,
                "total_results": len(results),
                "offset": offset,
                "limit": limit,
                "results": results[offset:offset+limit]
            }
            
            return response
        
        except Exception as e:
            logger.error(f"Search error: {e}")
            return {
                "error": str(e),
                "query": query,
                "results": []
            }
    
    async def index_content(
        self,
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
        logger.info(f"Index content request: source_type={source_type}, len={len(content)}")
        
        try:
            content_id = await self.content_manager.index_content(
                content=content,
                source_type=source_type,
                metadata=metadata,
                content_id=content_id,
                source_id=source_id
            )
            
            return {
                "success": True,
                "content_id": content_id,
                "message": "Content indexed successfully"
            }
        
        except Exception as e:
            logger.error(f"Indexing error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to index content"
            }
    
    async def index_teams_messages(
        self,
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
        logger.info(f"Index Teams messages request: chat_id={chat_id}, since={since}")
        
        try:
            if "teams" not in self.source_adapters:
                return {
                    "success": False,
                    "error": "Teams adapter not configured",
                    "message": "Teams adapter is not available"
                }
            
            adapter = self.source_adapters["teams"]
            indexed_count = await adapter.index_messages(chat_id=chat_id, since=since)
            
            return {
                "success": True,
                "indexed_count": indexed_count,
                "message": f"Indexed {indexed_count} Teams messages"
            }
        
        except Exception as e:
            logger.error(f"Teams indexing error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to index Teams messages"
            }
    
    async def get_content_count(
        self,
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
        logger.info(f"Get content count request: source_type={source_type}, source_id={source_id}")
        
        try:
            count = await self.content_manager.get_content_count(
                source_type=source_type,
                source_id=source_id
            )
            
            return {
                "success": True,
                "count": count,
                "source_type": source_type,
                "source_id": source_id
            }
        
        except Exception as e:
            logger.error(f"Content count error: {e}")
            return {
                "success": False,
                "error": str(e),
                "count": 0
            }
    
    async def delete_content(
        self,
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
        logger.info(f"Delete content request: content_id={content_id}, source_type={source_type}, source_id={source_id}")
        
        try:
            if content_id:
                await self.content_manager.delete_content(content_id)
                return {
                    "success": True,
                    "message": f"Content {content_id} deleted"
                }
            elif source_type:
                await self.content_manager.delete_content_by_source(
                    source_type=source_type,
                    source_id=source_id
                )
                return {
                    "success": True,
                    "message": f"Content for source {source_type}/{source_id or 'all'} deleted"
                }
            else:
                return {
                    "success": False,
                    "error": "Missing parameters",
                    "message": "Must provide content_id or source_type"
                }
        
        except Exception as e:
            logger.error(f"Delete content error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to delete content"
            }