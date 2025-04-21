"""
Base adapter interface for the MCP IR server.
Provides a common interface for data source adapters.
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union, Tuple

logger = logging.getLogger(__name__)

class BaseAdapter(ABC):
    """Base class for data source adapters."""
    
    @abstractmethod
    async def initialize(self):
        """Initialize the adapter."""
        pass
    
    @abstractmethod
    async def get_content_items(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Get content items from the data source.
        
        Returns:
            List of content items ready for indexing
        """
        pass
    
    @abstractmethod
    async def process_content(self, content_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a content item into a format suitable for indexing.
        
        Args:
            content_item: Content item from the data source
            
        Returns:
            Processed content item ready for indexing
        """
        pass
    
    @abstractmethod
    async def transform_query(self, query: str, **kwargs) -> str:
        """
        Transform a search query for this specific data source.
        
        Args:
            query: Original search query
            
        Returns:
            Transformed query
        """
        pass
    
    @abstractmethod
    async def get_source_type(self) -> str:
        """
        Get the source type identifier for this adapter.
        
        Returns:
            Source type string
        """
        pass