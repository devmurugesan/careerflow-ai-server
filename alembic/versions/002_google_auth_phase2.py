"""002_google_auth_phase2

Revision ID: 002_google_auth_phase2
Revises: 001_initial_schema
Create Date: 2026-07-31

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002_google_auth_phase2'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add google_id to users
    op.add_column('users', sa.Column('google_id', sa.String(255), nullable=True))
    op.create_index('ix_users_google_id', 'users', ['google_id'], unique=True)

    # Add is_connected to google_credentials
    op.add_column('google_credentials', sa.Column('is_connected', sa.Boolean(), server_default='true', nullable=False))
    op.add_column('google_credentials', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))
    op.add_column('google_credentials', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))


def downgrade() -> None:
    op.drop_column('google_credentials', 'updated_at')
    op.drop_column('google_credentials', 'created_at')
    op.drop_column('google_credentials', 'is_connected')
    op.drop_index('ix_users_google_id', table_name='users')
    op.drop_column('users', 'google_id')
