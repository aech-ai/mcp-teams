"""
Content chunking strategies for the MCP IR server.
Provides utilities for splitting text into chunks for indexing.
"""

import logging
import re
from typing import List, Dict, Any, Optional, Union, Tuple

from ..config import DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP

logger = logging.getLogger(__name__)

class ChunkingStrategy:
    """Base class for chunking strategies."""
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks.
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks
        """
        raise NotImplementedError("Subclasses must implement chunk_text")

class FixedSizeChunker(ChunkingStrategy):
    """Split text into fixed-size chunks with optional overlap."""
    
    def __init__(self, chunk_size: int = DEFAULT_CHUNK_SIZE, chunk_overlap: int = DEFAULT_CHUNK_OVERLAP):
        """
        Initialize the fixed-size chunker.
        
        Args:
            chunk_size: Maximum size of each chunk in characters
            chunk_overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into fixed-size chunks with overlap.
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks
        """
        if not text:
            return []
        
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            # Get chunk of specified size
            end = start + self.chunk_size
            chunk = text[start:end]
            
            # If not the last chunk and doesn't end with a sentence boundary,
            # try to find a good breaking point
            if end < len(text) and not re.search(r'[.!?]\s*$', chunk):
                # Look for sentence boundary within the last 20% of the chunk
                last_portion = chunk[int(0.8 * len(chunk)):]
                match = re.search(r'[.!?]\s+', last_portion)
                
                if match:
                    # Found a sentence boundary, adjust end position
                    boundary_pos = int(0.8 * len(chunk)) + match.start() + 1
                    chunk = chunk[:boundary_pos]
                    end = start + boundary_pos
            
            chunks.append(chunk)
            
            # Move start position for next chunk, considering overlap
            start = end - self.chunk_overlap
            
            # Ensure we make progress
            if start >= end:
                start = end
        
        return chunks

class ParagraphChunker(ChunkingStrategy):
    """Split text into paragraph-based chunks with merging of small paragraphs."""
    
    def __init__(
        self, 
        min_paragraph_size: int = 100,
        max_chunk_size: int = DEFAULT_CHUNK_SIZE,
        delimiter: str = "\n\n"
    ):
        """
        Initialize the paragraph chunker.
        
        Args:
            min_paragraph_size: Minimum size of a paragraph to stand alone
            max_chunk_size: Maximum size of a merged chunk
            delimiter: Delimiter that separates paragraphs
        """
        self.min_paragraph_size = min_paragraph_size
        self.max_chunk_size = max_chunk_size
        self.delimiter = delimiter
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into paragraph-based chunks.
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks
        """
        if not text:
            return []
        
        # Split the text into paragraphs
        paragraphs = text.split(self.delimiter)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        if not paragraphs:
            return []
        
        # If text is short enough, return it as a single chunk
        if len(text) <= self.max_chunk_size:
            return [text]
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for paragraph in paragraphs:
            para_size = len(paragraph)
            
            # If paragraph is too big on its own, use a fixed-size chunker on it
            if para_size > self.max_chunk_size:
                # First, finalize current chunk if there's anything in it
                if current_chunk:
                    chunks.append(self.delimiter.join(current_chunk))
                    current_chunk = []
                    current_size = 0
                
                # Then chunk the large paragraph
                fixed_chunker = FixedSizeChunker(self.max_chunk_size)
                para_chunks = fixed_chunker.chunk_text(paragraph)
                chunks.extend(para_chunks)
            
            # If adding this paragraph would exceed max size, finalize the current chunk
            elif current_size + para_size + len(self.delimiter) > self.max_chunk_size and current_chunk:
                chunks.append(self.delimiter.join(current_chunk))
                current_chunk = [paragraph]
                current_size = para_size
            
            # Otherwise, add paragraph to current chunk
            else:
                if current_chunk:
                    current_size += len(self.delimiter)
                current_chunk.append(paragraph)
                current_size += para_size
        
        # Add the last chunk if there's anything left
        if current_chunk:
            chunks.append(self.delimiter.join(current_chunk))
        
        return chunks

class TeamsMessageChunker(ChunkingStrategy):
    """Special chunker for Teams messages with conversation context."""
    
    def __init__(
        self, 
        max_messages_per_chunk: int = 5,
        max_chunk_size: int = DEFAULT_CHUNK_SIZE
    ):
        """
        Initialize the Teams message chunker.
        
        Args:
            max_messages_per_chunk: Maximum number of messages to include in a chunk
            max_chunk_size: Maximum size of a chunk in characters
        """
        self.max_messages_per_chunk = max_messages_per_chunk
        self.max_chunk_size = max_chunk_size
    
    def chunk_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Group messages into conversation chunks.
        
        Args:
            messages: List of message objects with at least 'content' and 'sender' fields
            
        Returns:
            List of chunked message groups with combined content and metadata
        """
        if not messages:
            return []
        
        # Sort messages by timestamp if available
        if "created_datetime" in messages[0]:
            messages = sorted(messages, key=lambda m: m.get("created_datetime", ""))
        
        chunks = []
        current_messages = []
        current_size = 0
        
        for message in messages:
            content = message.get("content", "")
            msg_size = len(content)
            
            # If message is too big on its own, chunk it and create a standalone chunk
            if msg_size > self.max_chunk_size:
                # First, finalize current chunk if there's anything in it
                if current_messages:
                    chunks.append(self._create_chunk_from_messages(current_messages))
                    current_messages = []
                    current_size = 0
                
                # Then chunk the large message
                fixed_chunker = FixedSizeChunker(self.max_chunk_size)
                msg_chunks = fixed_chunker.chunk_text(content)
                
                # Create a chunk for each part of the message
                for i, msg_chunk in enumerate(msg_chunks):
                    msg_copy = message.copy()
                    msg_copy["content"] = msg_chunk
                    if i > 0:
                        msg_copy["content_part"] = i + 1
                    chunks.append(self._create_chunk_from_messages([msg_copy]))
            
            # If adding this message would exceed limits, finalize the current chunk
            elif (current_size + msg_size > self.max_chunk_size or 
                  len(current_messages) >= self.max_messages_per_chunk) and current_messages:
                chunks.append(self._create_chunk_from_messages(current_messages))
                current_messages = [message]
                current_size = msg_size
            
            # Otherwise, add message to current chunk
            else:
                current_messages.append(message)
                current_size += msg_size
        
        # Add the last chunk if there's anything left
        if current_messages:
            chunks.append(self._create_chunk_from_messages(current_messages))
        
        return chunks
    
    def _create_chunk_from_messages(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a chunk from a group of messages.
        
        Args:
            messages: List of message objects
            
        Returns:
            A chunk object with combined content and metadata
        """
        # Combine message content with sender information
        content_parts = []
        sender_parts = []
        
        for msg in messages:
            sender = msg.get("sender", "Unknown")
            content = msg.get("content", "")
            
            if not content:
                continue
                
            content_parts.append(content)
            sender_parts.append(sender)
        
        # Build the combined content
        if len(messages) == 1:
            # For a single message, just use its content
            content = content_parts[0]
        else:
            # For multiple messages, format as a conversation
            conversation = []
            for i, msg in enumerate(messages):
                sender = msg.get("sender", "Unknown")
                msg_content = msg.get("content", "")
                conversation.append(f"{sender}: {msg_content}")
            
            content = "\n\n".join(conversation)
        
        # Get metadata from the last message
        metadata = messages[-1].get("metadata", {}).copy() if messages else {}
        metadata.update({
            "message_count": len(messages),
            "senders": sender_parts,
            "is_conversation": len(messages) > 1
        })
        
        return {
            "content": content,
            "metadata": metadata,
            "messages": messages
        }
    
    def chunk_text(self, text: str) -> List[str]:
        """
        For compatibility with the ChunkingStrategy interface.
        Simply uses a paragraph chunker for raw text.
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks
        """
        # If given raw text instead of message objects, use paragraph chunker
        paragraph_chunker = ParagraphChunker(max_chunk_size=self.max_chunk_size)
        return paragraph_chunker.chunk_text(text)

def get_chunker(
    chunker_type: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP
) -> ChunkingStrategy:
    """
    Get a chunker instance by type.
    
    Args:
        chunker_type: Type of chunker to use (fixed, paragraph, teams)
        chunk_size: Maximum size of chunks
        chunk_overlap: Overlap between chunks
        
    Returns:
        A chunker instance
    """
    if chunker_type == "fixed":
        return FixedSizeChunker(chunk_size, chunk_overlap)
    elif chunker_type == "paragraph":
        return ParagraphChunker(max_chunk_size=chunk_size)
    elif chunker_type == "teams":
        return TeamsMessageChunker(max_chunk_size=chunk_size)
    else:
        logger.warning(f"Unknown chunker type '{chunker_type}', using fixed-size chunker")
        return FixedSizeChunker(chunk_size, chunk_overlap)