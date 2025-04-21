"""
Alembic migration environment for the MCP IR server.
This script provides configuration for managing database migrations.
"""

import asyncio
import logging
import os
import sys
from logging.config import fileConfig

# Add the parent directory to sys.path to allow importing from ir module
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

# Import the IR config module for database connection info
from ir.config import get_pg_connection_string

# This is the Alembic Config object, providing access to the config file
config = context.config

# Interpret the config file for Python logging
fileConfig(config.config_file_name)
logger = logging.getLogger("alembic.env")

# Adjust connection string for SQLAlchemy
connection_string = get_pg_connection_string()
# Convert to async PostgreSQL string
if connection_string.startswith("postgresql://"):
    connection_string = connection_string.replace("postgresql://", "postgresql+asyncpg://")

config.set_main_option("sqlalchemy.url", connection_string)

# Metadata target for migrations
from ir.migrations.models import Base
target_metadata = Base.metadata

# Other values from the config, defined by the needs of env.py,
# can be acquired:
# ... etc.

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = AsyncEngine(
        create_async_engine(
            config.get_main_option("sqlalchemy.url"),
            echo=True,
            future=True,
        )
    )

    async with connectable.connect() as connection:
        await connection.run_sync(
            lambda conn: context.configure(
                connection=conn, target_metadata=target_metadata
            )
        )

        async with context.begin_transaction():
            await context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())