"""Teams specific tables

Revision ID: 002
Revises: 001
Create Date: 2025-04-20

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.schema import CreateTable
from sqlalchemy.sql import table, column

# revision identifiers
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Update schema version
    schema_version_table = table(
        'schema_version',
        column('version', sa.Integer),
        column('description', sa.String)
    )
    
    op.bulk_insert(
        schema_version_table,
        [
            {'version': 2, 'description': 'Teams specific tables'}
        ]
    )
    
    # Create teams_messages table to provide additional metadata and quick lookup
    op.create_table(
        'teams_messages',
        sa.Column('message_id', sa.String(), nullable=False),
        sa.Column('chat_id', sa.String(), nullable=False),
        sa.Column('content_id', sa.String(), nullable=False),
        sa.Column('sender_id', sa.String(), nullable=True),
        sa.Column('sender_name', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_updated', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_from_me', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('has_attachments', sa.Boolean(), nullable=True, server_default='false'),
        sa.ForeignKeyConstraint(['content_id'], ['indexed_content.content_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('message_id')
    )
    
    # Create index on chat_id for faster lookup
    op.create_index('idx_teams_messages_chat_id', 'teams_messages', ['chat_id'])
    
    # Create teams_chats table for chat metadata
    op.create_table(
        'teams_chats',
        sa.Column('chat_id', sa.String(), nullable=False),
        sa.Column('topic', sa.String(), nullable=True),
        sa.Column('chat_type', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_updated', sa.DateTime(timezone=True), nullable=True),
        sa.Column('participant_count', sa.Integer(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('chat_id')
    )
    
    # Create teams_chat_participants table for participant tracking
    op.create_table(
        'teams_chat_participants',
        sa.Column('chat_id', sa.String(), nullable=False),
        sa.Column('participant_id', sa.String(), nullable=False),
        sa.Column('display_name', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('role', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['chat_id'], ['teams_chats.chat_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('chat_id', 'participant_id')
    )
    
    # Create function to get chat context for a message
    op.execute("""
    CREATE OR REPLACE FUNCTION get_teams_message_context(
        p_message_id TEXT,
        p_context_size INTEGER DEFAULT 5
    ) RETURNS TABLE (
        message_id TEXT,
        chat_id TEXT,
        sender_name TEXT,
        content TEXT,
        created_at TIMESTAMP WITH TIME ZONE,
        is_from_me BOOLEAN,
        is_current BOOLEAN
    ) AS $$
    DECLARE
        v_chat_id TEXT;
        v_created_at TIMESTAMP WITH TIME ZONE;
    BEGIN
        -- Get the chat_id and timestamp of the target message
        SELECT chat_id, created_at INTO v_chat_id, v_created_at
        FROM teams_messages
        WHERE message_id = p_message_id;
        
        -- Return the context messages (before and after)
        RETURN QUERY
        WITH context_messages AS (
            (
                -- Messages before the target message
                SELECT
                    m.message_id,
                    m.chat_id,
                    m.sender_name,
                    ic.content,
                    m.created_at,
                    m.is_from_me,
                    false AS is_current
                FROM
                    teams_messages m
                JOIN
                    indexed_content ic ON m.content_id = ic.content_id
                WHERE
                    m.chat_id = v_chat_id
                    AND m.created_at < v_created_at
                ORDER BY
                    m.created_at DESC
                LIMIT p_context_size
            )
            UNION ALL
            (
                -- The target message
                SELECT
                    m.message_id,
                    m.chat_id,
                    m.sender_name,
                    ic.content,
                    m.created_at,
                    m.is_from_me,
                    true AS is_current
                FROM
                    teams_messages m
                JOIN
                    indexed_content ic ON m.content_id = ic.content_id
                WHERE
                    m.message_id = p_message_id
            )
            UNION ALL
            (
                -- Messages after the target message
                SELECT
                    m.message_id,
                    m.chat_id,
                    m.sender_name,
                    ic.content,
                    m.created_at,
                    m.is_from_me,
                    false AS is_current
                FROM
                    teams_messages m
                JOIN
                    indexed_content ic ON m.content_id = ic.content_id
                WHERE
                    m.chat_id = v_chat_id
                    AND m.created_at > v_created_at
                ORDER BY
                    m.created_at ASC
                LIMIT p_context_size
            )
        )
        SELECT
            message_id,
            chat_id,
            sender_name,
            content,
            created_at,
            is_from_me,
            is_current
        FROM
            context_messages
        ORDER BY
            created_at ASC;
    END;
    $$ LANGUAGE plpgsql;
    """)


def downgrade() -> None:
    # Drop function
    op.execute('DROP FUNCTION IF EXISTS get_teams_message_context')
    
    # Drop teams tables
    op.drop_table('teams_chat_participants')
    op.drop_table('teams_chats')
    op.drop_index('idx_teams_messages_chat_id', table_name='teams_messages')
    op.drop_table('teams_messages')