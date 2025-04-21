"""
Content indexing and management for the MCP IR server.
Provides utilities for adding, updating, and deleting indexed content.
"""

import logging
import json
import uuid
from typing import List, Dict, Any, Optional, Union, Tuple

from ..core.embeddings import EmbeddingGenerator

logger = logging.getLogger(__name__)

class ContentManager:
    """Manages indexed content in the database."""
    
    def __init__(self, db_client, embedding_generator: Optional[EmbeddingGenerator] = None):
        """Initialize the content manager."""
        self.db = db_client
        self.embedding_generator = embedding_generator or EmbeddingGenerator()
    
    async def index_content(
        self, 
        content: str,
        source_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        content_id: Optional[str] = None,
        source_id: Optional[str] = None,
        source_specific_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Index a piece of content with its embedding.
        
        Args:
            content: The text content to index
            source_type: Type of content source (e.g., "teams", "email", "document")
            metadata: Optional metadata about the content
            content_id: Optional ID for the content (generated if not provided)
            source_id: Optional ID for the source system
            source_specific_data: Optional source-specific data to store
            
        Returns:
            ID of the indexed content
        """
        # Generate content ID if not provided
        if not content_id:
            content_id = str(uuid.uuid4())
        
        # Generate embedding
        embedding = await self.embedding_generator.get_embedding(content)
        
        # Insert or update indexed content
        query = """
            INSERT INTO indexed_content (
                content_id, source_type, content, embedding, metadata
            ) VALUES (
                %s, %s, %s, %s, %s
            )
            ON CONFLICT (content_id) DO UPDATE SET
                source_type = EXCLUDED.source_type,
                content = EXCLUDED.content,
                embedding = EXCLUDED.embedding,
                metadata = EXCLUDED.metadata,
                updated_at = NOW()
            RETURNING id
        """
        
        # Convert metadata to JSON string if needed
        if metadata and not isinstance(metadata, str):
            metadata = json.dumps(metadata)
        
        try:
            result = await self.db.execute_one(
                query, [content_id, source_type, content, embedding, metadata]
            )
            
            # Add source-specific metadata if provided
            if source_id and source_specific_data:
                await self._add_source_metadata(content_id, source_id, source_specific_data)
            
            return content_id
        
        except Exception as e:
            logger.error(f"Error indexing content: {e}")
            raise
    
    async def bulk_index_content(
        self, 
        items: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Index multiple pieces of content in bulk.
        
        Args:
            items: List of content items to index, each with:
                - content: The text content to index
                - source_type: Type of content source
                - metadata: Optional metadata about the content
                - content_id: Optional ID for the content
                - source_id: Optional ID for the source system
                - source_specific_data: Optional source-specific data
            
        Returns:
            List of content IDs for the indexed items
        """
        # Generate embeddings for all content
        texts = [item["content"] for item in items]
        embeddings = await self.embedding_generator.get_embeddings(texts)
        
        # Start a transaction
        async with self.db.transaction() as conn:
            try:
                content_ids = []
                
                for i, item in enumerate(items):
                    content = item["content"]
                    source_type = item["source_type"]
                    metadata = item.get("metadata")
                    content_id = item.get("content_id") or str(uuid.uuid4())
                    embedding = embeddings[i]
                    
                    # Convert metadata to JSON string if needed
                    if metadata and not isinstance(metadata, str):
                        metadata = json.dumps(metadata)
                    
                    # Insert or update indexed content
                    query = """
                        INSERT INTO indexed_content (
                            content_id, source_type, content, embedding, metadata
                        ) VALUES (
                            %s, %s, %s, %s, %s
                        )
                        ON CONFLICT (content_id) DO UPDATE SET
                            source_type = EXCLUDED.source_type,
                            content = EXCLUDED.content,
                            embedding = EXCLUDED.embedding,
                            metadata = EXCLUDED.metadata,
                            updated_at = NOW()
                        RETURNING id
                    """
                    
                    async with conn.cursor() as cur:
                        await cur.execute(
                            query, [content_id, source_type, content, embedding, metadata]
                        )
                    
                    # Add source-specific metadata if provided
                    source_id = item.get("source_id")
                    source_specific_data = item.get("source_specific_data")
                    
                    if source_id and source_specific_data:
                        await self._add_source_metadata(
                            content_id, source_id, source_specific_data, conn
                        )
                    
                    content_ids.append(content_id)
                
                await conn.commit()
                return content_ids
            
            except Exception as e:
                logger.error(f"Error bulk indexing content: {e}")
                await conn.rollback()
                raise
    
    async def _add_source_metadata(
        self, 
        content_id: str,
        source_id: str,
        source_specific_data: Dict[str, Any],
        conn = None
    ):
        """
        Add source-specific metadata for indexed content.
        
        Args:
            content_id: ID of the indexed content
            source_id: ID for the source system
            source_specific_data: Source-specific data to store
            conn: Optional database connection to use
        """
        # Convert source_specific_data to JSON string if needed
        if not isinstance(source_specific_data, str):
            source_specific_data = json.dumps(source_specific_data)
        
        query = """
            INSERT INTO source_metadata (
                content_id, source_id, source_specific_data
            ) VALUES (
                %s, %s, %s
            )
            ON CONFLICT (content_id, source_id) DO UPDATE SET
                source_specific_data = EXCLUDED.source_specific_data
        """
        
        if conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    query, [content_id, source_id, source_specific_data]
                )
        else:
            await self.db.execute_no_results(
                query, [content_id, source_id, source_specific_data]
            )
    
    async def delete_content(self, content_id: str):
        """
        Delete indexed content by ID.
        
        Args:
            content_id: ID of the content to delete
        """
        query = "DELETE FROM indexed_content WHERE content_id = %s"
        
        try:
            await self.db.execute_no_results(query, [content_id])
        except Exception as e:
            logger.error(f"Error deleting content: {e}")
            raise
    
    async def delete_content_by_source(self, source_type: str, source_id: Optional[str] = None):
        """
        Delete all indexed content for a specific source.
        
        Args:
            source_type: Type of content source to delete
            source_id: Optional specific source ID to delete
        """
        if source_id:
            query = """
                DELETE FROM indexed_content
                WHERE content_id IN (
                    SELECT content_id 
                    FROM source_metadata 
                    WHERE source_id = %s
                )
                AND source_type = %s
            """
            params = [source_id, source_type]
        else:
            query = "DELETE FROM indexed_content WHERE source_type = %s"
            params = [source_type]
        
        try:
            await self.db.execute_no_results(query, params)
        except Exception as e:
            logger.error(f"Error deleting content by source: {e}")
            raise
    
    async def get_content(self, content_id: str) -> Optional[Dict[str, Any]]:
        """
        Get indexed content by ID.
        
        Args:
            content_id: ID of the content to retrieve
            
        Returns:
            Content details or None if not found
        """
        query = """
            SELECT 
                content_id,
                source_type,
                content,
                metadata,
                created_at,
                updated_at
            FROM 
                indexed_content
            WHERE 
                content_id = %s
        """
        
        try:
            result = await self.db.execute_one(query, [content_id])
            return result
        except Exception as e:
            logger.error(f"Error retrieving content: {e}")
            return None
    
    async def get_content_count(
        self, 
        source_type: Optional[str] = None,
        source_id: Optional[str] = None
    ) -> int:
        """
        Get count of indexed content, optionally filtered by source.
        
        Args:
            source_type: Optional type of content source to count
            source_id: Optional specific source ID to count
            
        Returns:
            Count of indexed content
        """
        if source_type and source_id:
            query = """
                SELECT COUNT(*) as count
                FROM indexed_content
                WHERE source_type = %s
                AND content_id IN (
                    SELECT content_id 
                    FROM source_metadata 
                    WHERE source_id = %s
                )
            """
            params = [source_type, source_id]
        elif source_type:
            query = "SELECT COUNT(*) as count FROM indexed_content WHERE source_type = %s"
            params = [source_type]
        else:
            query = "SELECT COUNT(*) as count FROM indexed_content"
            params = []
        
        try:
            result = await self.db.execute_one(query, params)
            return result["count"] if result else 0
        except Exception as e:
            logger.error(f"Error counting content: {e}")
            return 0