"""001_initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-07-31

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(255), nullable=True),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('is_admin', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('timezone', sa.String(50), server_default='UTC', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )
    op.create_index('ix_users_email', 'users', ['email'])

    # Google Credentials table
    op.create_table(
        'google_credentials',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('encrypted_access_token', sa.Text(), nullable=False),
        sa.Column('encrypted_refresh_token', sa.Text(), nullable=False),
        sa.Column('token_uri', sa.String(255), nullable=False),
        sa.Column('client_id', sa.String(255), nullable=False),
        sa.Column('scopes', sa.Text(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('history_id', sa.BigInteger(), nullable=True)
    )

    # Emails table
    op.create_table(
        'emails',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('gmail_message_id', sa.String(128), nullable=False),
        sa.Column('thread_id', sa.String(128), nullable=False),
        sa.Column('sender', sa.String(255), nullable=False),
        sa.Column('recipient', sa.String(255), nullable=False),
        sa.Column('subject', sa.Text(), nullable=False),
        sa.Column('snippet', sa.Text(), nullable=False),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('processing_status', sa.String(32), server_default='PENDING', nullable=False),
        sa.Column('classified_category', sa.String(32), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('raw_body_hash', sa.String(64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.UniqueConstraint('user_id', 'gmail_message_id', name='uq_user_gmail_message')
    )
    op.create_index('ix_emails_thread_id', 'emails', ['thread_id'])

    # Opportunities table
    op.create_table(
        'opportunities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('category', sa.String(32), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('organization_or_platform', sa.String(255), nullable=False),
        sa.Column('current_status', sa.String(64), nullable=False),
        sa.Column('priority', sa.String(16), server_default='MEDIUM', nullable=False),
        sa.Column('deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('event_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('action_required', sa.Text(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('confidence_score', sa.Float(), server_default='1.0', nullable=False),
        sa.Column('extra_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_archived', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )
    op.create_index('ix_opportunities_user_id', 'opportunities', ['user_id'])
    op.create_index('ix_opportunities_category', 'opportunities', ['category'])

    # Opportunity Emails junction table
    op.create_table(
        'opportunity_emails',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('opportunity_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('opportunities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('email_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('emails.id', ondelete='CASCADE'), nullable=False),
        sa.Column('extracted_status', sa.String(64), nullable=False),
        sa.Column('linked_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )

    # Opportunity Status History table
    op.create_table(
        'opportunity_status_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('opportunity_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('opportunities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_email_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('emails.id', ondelete='SET NULL'), nullable=True),
        sa.Column('from_status', sa.String(64), nullable=False),
        sa.Column('to_status', sa.String(64), nullable=False),
        sa.Column('reason_summary', sa.Text(), nullable=True),
        sa.Column('changed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )

    # Reminders table
    op.create_table(
        'reminders',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('opportunity_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('opportunities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('trigger_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(32), server_default='PENDING', nullable=False),
        sa.Column('channel', sa.String(32), server_default='IN_APP', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )


def downgrade() -> None:
    op.drop_table('reminders')
    op.drop_table('opportunity_status_history')
    op.drop_table('opportunity_emails')
    op.drop_table('opportunities')
    op.drop_table('emails')
    op.drop_table('google_credentials')
    op.drop_table('users')
