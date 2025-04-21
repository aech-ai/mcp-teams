"""
SQLAlchemy models for database migrations.
These models serve as the source of truth for the database schema migrations.
"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

# We need to use SQLAlchemy definitions for the schema
# since Alembic works with SQLAlchemy models

class SchemaVersion(Base):
    """Schema version tracking table."""
    __tablename__ = "schema_version"
    
    version = Column(Integer, primary_key=True)
    applied_at = Column(DateTime(timezone=True), server_default=func.now())
    description = Column(String, nullable=True)


class IndexedContent(Base):
    """Main table for indexed content with vector embeddings."""
    __tablename__ = "indexed_content"
    
    id = Column(Integer, primary_key=True)
    content_id = Column(String, nullable=False, unique=True)
    source_type = Column(String, nullable=False)
    content = Column(String, nullable=False)
    # Note: The 'embedding' column uses the vector type from pgvector,
    # which doesn't have a direct SQLAlchemy type. We'll need to create
    # this using raw SQL in migrations.
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Define indices for regular columns
    __table_args__ = (
        # We'll create the full-text search index manually in migrations
        # since it uses GIN which isn't directly supported in SQLAlchemy
        # Index('content_fts_idx', func.to_tsvector('english', content), postgresql_using='gin'),
    )


class SourceMetadata(Base):
    """Source-specific metadata for indexed content."""
    __tablename__ = "source_metadata"
    
    content_id = Column(String, ForeignKey("indexed_content.content_id", ondelete="CASCADE"), primary_key=True)
    source_id = Column(String, primary_key=True)
    source_specific_data = Column(JSON, nullable=True)


# For adapter-specific tables, create separate model files
# For example, teams_models.py could contain:
# 
# class TeamsMessage(Base):
#     __tablename__ = "teams_messages"
#     
#     message_id = Column(String, primary_key=True)
#     chat_id = Column(String, nullable=False)
#     content_id = Column(String, ForeignKey("indexed_content.content_id", ondelete="CASCADE"))
#     # ... other Teams-specific fields