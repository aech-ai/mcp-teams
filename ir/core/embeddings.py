"""
Embedding generation for the MCP IR server.
Provides utilities for generating vector embeddings from text.
"""

import logging
import httpx
from typing import List, Optional, Union, Any
import numpy as np

from ..config import OPENAI_API_KEY, EMBEDDING_MODEL, EMBEDDING_DIMENSIONS

logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    """Generates and manages vector embeddings for text content."""
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        dimensions: Optional[int] = None,
        cache_size: int = 100
    ):
        """Initialize the embedding generator."""
        self.api_key = api_key or OPENAI_API_KEY
        self.model = model or EMBEDDING_MODEL
        self.dimensions = dimensions or EMBEDDING_DIMENSIONS
        
        # Simple LRU cache for embeddings
        self.cache = {}
        self.cache_size = cache_size
        self.cache_order = []
    
    async def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for a single text.
        Uses cache if available.
        
        Args:
            text: Text to embed
            
        Returns:
            Vector embedding as a list of floats
        """
        # Check cache first
        if text in self.cache:
            # Move to the end of the cache order (most recently used)
            self.cache_order.remove(text)
            self.cache_order.append(text)
            return self.cache[text]
        
        # Generate new embedding
        embedding = await self._generate_embedding(text)
        
        # Update cache
        if len(self.cache) >= self.cache_size and self.cache_order:
            # Remove oldest item
            oldest = self.cache_order.pop(0)
            del self.cache[oldest]
        
        self.cache[text] = embedding
        self.cache_order.append(text)
        
        return embedding
    
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for multiple texts in batch.
        Uses cache where available and generates the rest.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of vector embeddings
        """
        # Check which texts are cached
        to_generate = []
        indices = []
        results = [None] * len(texts)
        
        for i, text in enumerate(texts):
            if text in self.cache:
                # Move to the end of the cache order (most recently used)
                self.cache_order.remove(text)
                self.cache_order.append(text)
                results[i] = self.cache[text]
            else:
                to_generate.append(text)
                indices.append(i)
        
        # Generate new embeddings if needed
        if to_generate:
            new_embeddings = await self._generate_embeddings(to_generate)
            
            # Update cache and results
            for j, embedding in enumerate(new_embeddings):
                text = to_generate[j]
                index = indices[j]
                
                # Update cache
                if len(self.cache) >= self.cache_size and self.cache_order:
                    # Remove oldest item
                    oldest = self.cache_order.pop(0)
                    del self.cache[oldest]
                
                self.cache[text] = embedding
                self.cache_order.append(text)
                
                # Update results
                results[index] = embedding
        
        return results
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text using OpenAI API.
        
        Args:
            text: Text to embed
            
        Returns:
            Vector embedding as a list of floats
            
        Raises:
            ValueError: If API key is not set
            RuntimeError: If API request fails
        """
        if not self.api_key:
            raise ValueError("OpenAI API key is not set")
        
        url = "https://api.openai.com/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "input": text,
            "model": self.model,
            "encoding_format": "float"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                # Extract embedding from response
                embedding = data["data"][0]["embedding"]
                
                return embedding
        except httpx.HTTPStatusError as e:
            logger.error(f"OpenAI API error: {e.response.text}")
            raise RuntimeError(f"OpenAI API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise RuntimeError(f"Error generating embedding: {str(e)}")
    
    async def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts using OpenAI API.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of vector embeddings
            
        Raises:
            ValueError: If API key is not set
            RuntimeError: If API request fails
        """
        if not self.api_key:
            raise ValueError("OpenAI API key is not set")
        
        url = "https://api.openai.com/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "input": texts,
            "model": self.model,
            "encoding_format": "float"
        }
        
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                # Extract embeddings from response
                embeddings = [item["embedding"] for item in data["data"]]
                
                return embeddings
        except httpx.HTTPStatusError as e:
            logger.error(f"OpenAI API error: {e.response.text}")
            raise RuntimeError(f"OpenAI API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise RuntimeError(f"Error generating embeddings: {str(e)}")
    
    def normalize_embedding(self, embedding: List[float]) -> List[float]:
        """
        Normalize an embedding vector to unit length.
        
        Args:
            embedding: Vector to normalize
            
        Returns:
            Normalized vector
        """
        vec = np.array(embedding, dtype=np.float32)
        norm = np.linalg.norm(vec)
        if norm > 0:
            return (vec / norm).tolist()
        return embedding