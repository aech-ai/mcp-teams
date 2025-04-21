"""
PostgreSQL client for the MCP IR server.
Provides connection pooling and database operations.
"""

import asyncio
import logging
import psycopg
from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row

from ..config import get_pg_connection_string, PG_MIN_CONN, PG_MAX_CONN
from .schema import create_schema, check_schema_version, upgrade_schema, SCHEMA_VERSION

logger = logging.getLogger(__name__)

class PostgresClient:
    """Client for PostgreSQL database operations with connection pooling."""
    
    def __init__(self, connection_string=None, min_size=None, max_size=None):
        """Initialize the PostgreSQL client."""
        self.connection_string = connection_string or get_pg_connection_string()
        self.min_size = min_size or PG_MIN_CONN
        self.max_size = max_size or PG_MAX_CONN
        self.pool = None
        
    async def initialize(self):
        """Initialize the connection pool and ensure schema exists."""
        if self.pool is not None:
            return
        
        logger.info("Initializing PostgreSQL connection pool")
        
        try:
            # Create connection pool with dict row factory
            self.pool = AsyncConnectionPool(
                conninfo=self.connection_string,
                min_size=self.min_size,
                max_size=self.max_size,
                kwargs={"row_factory": dict_row},
            )
            
            # Initialize schema
            async with self.pool.connection() as conn:
                await create_schema(conn)
                current_version = await check_schema_version(conn)
                
                if current_version < SCHEMA_VERSION:
                    logger.info(f"Upgrading schema from version {current_version} to {SCHEMA_VERSION}")
                    await upgrade_schema(conn)
                
                logger.info(f"Database schema version: {await check_schema_version(conn)}")
            
            logger.info("PostgreSQL connection pool initialized successfully")
        
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL connection pool: {e}")
            raise
    
    async def close(self):
        """Close the connection pool."""
        if self.pool is not None:
            await self.pool.close()
            self.pool = None
            logger.info("PostgreSQL connection pool closed")
    
    async def execute(self, query, params=None):
        """Execute a query and return the result."""
        if self.pool is None:
            await self.initialize()
        
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, params)
                return await cur.fetchall()
    
    async def execute_one(self, query, params=None):
        """Execute a query and return a single result."""
        if self.pool is None:
            await self.initialize()
        
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, params)
                return await cur.fetchone()
    
    async def execute_no_results(self, query, params=None):
        """Execute a query without returning results."""
        if self.pool is None:
            await self.initialize()
        
        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, params)
                await conn.commit()
    
    # Transaction management
    async def transaction(self):
        """Get a connection with transaction management."""
        if self.pool is None:
            await self.initialize()
        
        return self.pool.connection()