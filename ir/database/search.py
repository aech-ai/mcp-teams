"""
Search functionality for the MCP IR server.
Implements hybrid, semantic, and full-text search on indexed content.
"""

import logging
from typing import List, Dict, Any, Optional, Union, Tuple

from ..config import (
    DEFAULT_SEARCH_LIMIT, DEFAULT_SEARCH_TYPE,
    HYBRID_WEIGHT_SEMANTIC, HYBRID_WEIGHT_FULLTEXT
)

logger = logging.getLogger(__name__)

class SearchManager:
    """Manages search operations on indexed content."""
    
    def __init__(self, db_client):
        """Initialize the search manager."""
        self.db = db_client
    
    async def semantic_search(
        self, 
        embedding: List[float], 
        limit: int = DEFAULT_SEARCH_LIMIT,
        source_type: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search using vector embeddings.
        
        Args:
            embedding: Vector embedding for the query
            limit: Maximum number of results to return
            source_type: Optional filter for source type
            filters: Additional metadata filters
            
        Returns:
            List of matching documents with scores
        """
        query = """
            SELECT 
                content_id,
                content,
                source_type,
                metadata,
                1 - (embedding <=> %s) AS score
            FROM 
                indexed_content
            WHERE 
                embedding IS NOT NULL
        """
        params = [embedding]
        
        # Add source type filter if provided
        if source_type:
            query += " AND source_type = %s"
            params.append(source_type)
        
        # Add metadata filters if provided
        if filters:
            for key, value in filters.items():
                query += f" AND metadata->>'%s' = %s"
                params.extend([key, value])
        
        query += """
            ORDER BY 
                score DESC
            LIMIT 
                %s
        """
        params.append(limit)
        
        try:
            results = await self.db.execute(query, params)
            return results
        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            return []
    
    async def fulltext_search(
        self, 
        query_text: str, 
        limit: int = DEFAULT_SEARCH_LIMIT,
        source_type: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform full-text search using PostgreSQL's FTS.
        
        Args:
            query_text: Text query to search for
            limit: Maximum number of results to return
            source_type: Optional filter for source type
            filters: Additional metadata filters
            
        Returns:
            List of matching documents with scores
        """
        query = """
            SELECT 
                content_id,
                content,
                source_type,
                metadata,
                ts_rank(to_tsvector('english', content), plainto_tsquery('english', %s)) AS score
            FROM 
                indexed_content
            WHERE 
                to_tsvector('english', content) @@ plainto_tsquery('english', %s)
        """
        params = [query_text, query_text]
        
        # Add source type filter if provided
        if source_type:
            query += " AND source_type = %s"
            params.append(source_type)
        
        # Add metadata filters if provided
        if filters:
            for key, value in filters.items():
                query += f" AND metadata->>'%s' = %s"
                params.extend([key, value])
        
        query += """
            ORDER BY 
                score DESC
            LIMIT 
                %s
        """
        params.append(limit)
        
        try:
            results = await self.db.execute(query, params)
            return results
        except Exception as e:
            logger.error(f"Full-text search error: {e}")
            return []
    
    async def hybrid_search(
        self, 
        query_text: str,
        embedding: List[float],
        semantic_weight: float = HYBRID_WEIGHT_SEMANTIC,
        limit: int = DEFAULT_SEARCH_LIMIT,
        source_type: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining semantic and full-text search.
        Uses the database hybrid_search function.
        
        Args:
            query_text: Text query to search for
            embedding: Vector embedding for the query
            semantic_weight: Weight to give semantic results (0-1)
            limit: Maximum number of results to return
            source_type: Optional filter for source type
            filters: Additional metadata filters
            
        Returns:
            List of matching documents with scores
        """
        query = """
            SELECT * FROM hybrid_search(%s, %s, %s, %s)
        """
        params = [query_text, embedding, semantic_weight, limit]
        
        # Add where clause for filters if needed
        where_clauses = []
        if source_type:
            where_clauses.append("source_type = %s")
            params.append(source_type)
        
        if filters:
            for key, value in filters.items():
                where_clauses.append(f"metadata->>'%s' = %s")
                params.extend([key, value])
        
        if where_clauses:
            query = f"""
                WITH results AS ({query})
                SELECT * FROM results
                WHERE {' AND '.join(where_clauses)}
                ORDER BY score DESC
                LIMIT %s
            """
            params.append(limit)
        
        try:
            results = await self.db.execute(query, params)
            return results
        except Exception as e:
            logger.error(f"Hybrid search error: {e}")
            # Fall back to RRF fusion if the stored procedure fails
            return await self._hybrid_search_rrf(
                query_text, embedding, semantic_weight, limit, source_type, filters
            )
    
    async def _hybrid_search_rrf(
        self, 
        query_text: str,
        embedding: List[float],
        semantic_weight: float = HYBRID_WEIGHT_SEMANTIC,
        limit: int = DEFAULT_SEARCH_LIMIT,
        source_type: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Fallback hybrid search using RRF algorithm in Python.
        Uses Reciprocal Rank Fusion to combine semantic and full-text results.
        
        Args:
            query_text: Text query to search for
            embedding: Vector embedding for the query
            semantic_weight: Weight to give semantic results (0-1)
            limit: Maximum number of results to return
            source_type: Optional filter for source type
            filters: Additional metadata filters
            
        Returns:
            List of matching documents with scores
        """
        # Get both types of results
        semantic_results = await self.semantic_search(
            embedding, limit * 2, source_type, filters
        )
        fulltext_results = await self.fulltext_search(
            query_text, limit * 2, source_type, filters
        )
        
        # Combine results using RRF (Reciprocal Rank Fusion)
        combined_scores = {}
        
        # Process semantic results
        for rank, result in enumerate(semantic_results):
            content_id = result["content_id"]
            # RRF formula: 1 / (rank + k) where k is a constant (60 is common)
            score = semantic_weight * (1.0 / (rank + 60))
            combined_scores[content_id] = {
                "content": result["content"],
                "source_type": result["source_type"],
                "metadata": result["metadata"],
                "score": score
            }
        
        # Process full-text results
        fulltext_weight = 1.0 - semantic_weight
        for rank, result in enumerate(fulltext_results):
            content_id = result["content_id"]
            score = fulltext_weight * (1.0 / (rank + 60))
            
            if content_id in combined_scores:
                combined_scores[content_id]["score"] += score
            else:
                combined_scores[content_id] = {
                    "content": result["content"],
                    "source_type": result["source_type"],
                    "metadata": result["metadata"],
                    "score": score
                }
        
        # Convert to list and sort by score
        results = []
        for content_id, data in combined_scores.items():
            results.append({
                "content_id": content_id,
                **data
            })
        
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]
    
    async def search(
        self, 
        query: str,
        embedding: Optional[List[float]] = None,
        search_type: str = DEFAULT_SEARCH_TYPE,
        limit: int = DEFAULT_SEARCH_LIMIT,
        source_type: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Unified search interface that dispatches to the appropriate search method.
        
        Args:
            query: Text query to search for
            embedding: Optional vector embedding for the query
            search_type: Type of search to perform (hybrid, semantic, fulltext)
            limit: Maximum number of results to return
            source_type: Optional filter for source type
            filters: Additional metadata filters
            
        Returns:
            List of matching documents with scores
        """
        if search_type == "semantic" and embedding:
            return await self.semantic_search(embedding, limit, source_type, filters)
        
        elif search_type == "fulltext":
            return await self.fulltext_search(query, limit, source_type, filters)
        
        elif search_type == "hybrid" and embedding:
            return await self.hybrid_search(query, embedding, HYBRID_WEIGHT_SEMANTIC, limit, source_type, filters)
        
        else:
            # Default to full-text if we don't have embeddings
            logger.warning(f"Unsupported search type or missing embedding, falling back to full-text search")
            return await self.fulltext_search(query, limit, source_type, filters)