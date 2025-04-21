"""
Teams adapter for the MCP IR server.
Provides integration with Microsoft Teams messages.
"""

import logging
import json
import asyncio
from typing import List, Dict, Any, Optional, Union, Tuple

from .base_adapter import BaseAdapter
from ..database.indexed_content import ContentManager

logger = logging.getLogger(__name__)

class TeamsAdapter(BaseAdapter):
    """Adapter for Microsoft Teams data source."""
    
    def __init__(self, teams_client, content_manager: ContentManager):
        """Initialize the Teams adapter."""
        self.teams_client = teams_client
        self.content_manager = content_manager
        self.source_type = "teams"
        self.initialized = False
    
    async def initialize(self):
        """Initialize the adapter."""
        logger.info("Initializing Teams adapter")
        # Test the Teams client to verify it's working
        try:
            # Try to list chats to verify Teams client works
            await self.teams_client.list_chats()
            self.initialized = True
            logger.info("Teams adapter initialized successfully")
        except Exception as e:
            logger.warning(f"Teams client initialization warning: {str(e)}")
            logger.info("Teams adapter will operate in limited functionality mode")
            self.initialized = False
    
    async def get_content_items(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Get content items from Teams.
        
        Args:
            chat_id: Optional specific chat to fetch messages from
            since: Optional timestamp to fetch messages after
            
        Returns:
            List of content items ready for indexing
        """
        if not self.initialized:
            logger.warning("Teams adapter not fully initialized, get_content_items may return limited results")
        
        chat_id = kwargs.get("chat_id")
        since = kwargs.get("since")
        
        try:
            if chat_id:
                # Get messages from specific chat
                messages = await self.teams_client.get_messages(chat_id)
                chats = [{"id": chat_id}]
            else:
                # Get all chats and their messages
                chats = await self.teams_client.list_chats()
                messages = []
                
                for chat in chats:
                    try:
                        chat_messages = await self.teams_client.get_messages(chat["id"])
                        messages.extend(chat_messages)
                    except Exception as e:
                        logger.error(f"Error getting messages for chat {chat['id']}: {e}")
                        continue
            
            # Filter messages by timestamp if needed
            if since:
                messages = [
                    msg for msg in messages 
                    if msg.get("createdDateTime", "") > since
                ]
            
            # Process all messages
            content_items = []
            for msg in messages:
                content_item = await self.process_content(msg)
                if content_item:
                    content_items.append(content_item)
            
            return content_items
            
        except Exception as e:
            logger.error(f"Error in get_content_items: {e}")
            return []
    
    async def process_content(self, content_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a Teams message into a format suitable for indexing.
        
        Args:
            content_item: Teams message object
            
        Returns:
            Processed content item ready for indexing
        """
        # Skip empty messages or non-dict content items
        if not isinstance(content_item, dict) or not content_item.get("body", {}).get("content"):
            return None
        
        try:
            # Extract key fields
            chat_id = content_item.get("chatId")
            message_id = content_item.get("id")
            content = content_item.get("body", {}).get("content", "")
            sender = content_item.get("from", {}).get("user", {}).get("displayName", "Unknown")
            created_datetime = content_item.get("createdDateTime", "")
            
            # Skip messages without required fields
            if not all([chat_id, message_id, content, created_datetime]):
                return None
            
            # Create metadata
            metadata = {
                "chat_id": chat_id,
                "sender": sender,
                "created_datetime": created_datetime,
                "message_type": "teams"
            }
            
            # Format source-specific data
            source_specific_data = {
                "original_message": content_item
            }
            
            return {
                "content": content,
                "source_type": self.source_type,
                "content_id": f"teams-msg-{message_id}",
                "source_id": chat_id,
                "metadata": metadata,
                "source_specific_data": source_specific_data
            }
        except Exception as e:
            logger.error(f"Error processing Teams message: {e}")
            return None
    
    async def transform_query(self, query: str, **kwargs) -> str:
        """
        Transform a search query for Teams messages.
        
        Args:
            query: Original search query
            
        Returns:
            Transformed query
        """
        # No special transformation needed currently
        return query
    
    async def get_source_type(self) -> str:
        """
        Get the source type identifier for this adapter.
        
        Returns:
            Source type string
        """
        return self.source_type
    
    async def index_messages(self, chat_id: Optional[str] = None, since: Optional[str] = None) -> int:
        """
        Index messages from Teams.
        
        Args:
            chat_id: Optional specific chat to index
            since: Optional timestamp to index messages after
            
        Returns:
            Number of messages indexed
        """
        logger.info(f"Indexing Teams messages: chat_id={chat_id}, since={since}")
        
        try:
            # Get messages
            content_items = await self.get_content_items(chat_id=chat_id, since=since)
            
            if not content_items:
                logger.info("No messages to index")
                return 0
            
            # Index in batches of 50
            batch_size = 50
            indexed_count = 0
            
            for i in range(0, len(content_items), batch_size):
                batch = content_items[i:i+batch_size]
                try:
                    await self.content_manager.bulk_index_content(batch)
                    indexed_count += len(batch)
                    logger.info(f"Indexed {indexed_count}/{len(content_items)} messages")
                except Exception as e:
                    logger.error(f"Error indexing batch {i//batch_size + 1}: {e}")
            
            return indexed_count
        
        except Exception as e:
            logger.error(f"Error indexing Teams messages: {e}")
            return 0