"""Add status column

Revision ID: dea870dc6413
Revises: c709251abad2
Create Date: 2025-04-27 18:18:37.561772

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dea870dc6413'
down_revision = 'c709251abad2'
branch_labels = None
depends_on = None


def upgrade():
    # Add status column with default value
    op.add_column('fgas_records', sa.Column('status', sa.String(20), nullable=False, server_default='active'))


def downgrade():
    # Remove status column
    op.drop_column('fgas_records', 'status')
