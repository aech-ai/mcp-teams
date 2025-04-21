# Data Source Adapters for MCP IR Server

This directory contains data source adapters that allow the IR server to ingest and search content from different systems.

## Adapter Architecture

Each adapter implements the `BaseAdapter` interface and provides functionality to:

1. **Extract** content from a source system
2. **Transform** content into the indexed_content format
3. **Index** the content with proper metadata
4. **Query** the source-specific data

## Available Adapters

### Teams Adapter

`teams_adapter.py` provides integration with Microsoft Teams:

- Indexes Teams messages with relevant metadata
- Handles message context and conversation threading
- Provides Teams-specific search capabilities

## Creating a New Adapter

To create a new adapter for another data source:

1. Create a new file `your_source_adapter.py` that implements `BaseAdapter`
2. Add any source-specific database tables via migrations
3. Implement source-specific processing logic
4. Register the adapter in the MCP server

### Example Adapter Template

```python
from typing import List, Dict, Any, Optional
from .base_adapter import BaseAdapter
from ..database.indexed_content import ContentManager

class YourSourceAdapter(BaseAdapter):
    """Adapter for Your Source data source."""
    
    def __init__(self, source_client, content_manager: ContentManager):
        """Initialize the adapter."""
        self.source_client = source_client
        self.content_manager = content_manager
        self.source_type = "your_source"
    
    async def initialize(self):
        """Initialize the adapter."""
        # Setup connection to your source system
        pass
    
    async def get_content_items(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Get content items from your source.
        """
        # Fetch content from your source
        # Transform into content items
        return []
    
    async def process_content(self, content_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a content item into a format suitable for indexing.
        """
        # Transform source-specific content into indexable format
        return {
            "content": "...",
            "source_type": self.source_type,
            "content_id": f"{self.source_type}-{item_id}",
            "source_id": "...",
            "metadata": {},
            "source_specific_data": {}
        }
    
    async def transform_query(self, query: str, **kwargs) -> str:
        """
        Transform a search query for your specific data source.
        """
        # Adapt query for source-specific needs
        return query
    
    async def get_source_type(self) -> str:
        """
        Get the source type identifier for this adapter.
        """
        return self.source_type
    
    async def index_source_items(self, **kwargs) -> int:
        """
        Index items from your source.
        """
        # Get and index content items
        content_items = await self.get_content_items(**kwargs)
        # Index in batches
        await self.content_manager.bulk_index_content(content_items)
        return len(content_items)
```

## Database Considerations

When creating a new adapter:

1. **Add Source-Specific Tables**: Create migration with:
   - Tables for source-specific metadata
   - Indices for source-specific lookup

2. **Source-Specific SQL Functions**: Add functions for:
   - Context expansion for the source
   - Source-specific filtering

See the Teams adapter and its migration (`002_teams_specific_tables.py`) for an example.