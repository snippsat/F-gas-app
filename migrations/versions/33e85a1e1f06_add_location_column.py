"""Add location column

Revision ID: 33e85a1e1f06
Revises: dea870dc6413
Create Date: 2025-04-27 18:22:46.380577

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '33e85a1e1f06'
down_revision = 'dea870dc6413'
branch_labels = None
depends_on = None


def upgrade():
    # Add location column
    op.add_column('fgas_records', sa.Column('location', sa.String(100), nullable=True))


def downgrade():
    # Remove location column
    op.drop_column('fgas_records', 'location')
