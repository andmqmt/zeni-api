"""
add is_auto_generated to categories

Revision ID: 2b1a9c4d1f2b
Revises: 961fd5c80514_add_user_auto_categorize_enabled_flag
Create Date: 2025-11-10 00:00:00
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '2b1a9c4d1f2b'
down_revision = '961fd5c80514'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('categories', sa.Column('is_auto_generated', sa.Boolean(), nullable=False, server_default=sa.text('false')))


def downgrade():
    op.drop_column('categories', 'is_auto_generated')
