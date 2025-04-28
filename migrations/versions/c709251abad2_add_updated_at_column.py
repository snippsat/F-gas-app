"""Add updated_at column

Revision ID: c709251abad2
Revises: 
Create Date: 2025-04-27 18:17:16.904469

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = 'c709251abad2'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add updated_at column to fgas_records table
    op.add_column('fgas_records', sa.Column('updated_at', sa.DateTime(), nullable=True))


def downgrade():
    # Remove updated_at column from fgas_records table
    op.drop_column('fgas_records', 'updated_at')
