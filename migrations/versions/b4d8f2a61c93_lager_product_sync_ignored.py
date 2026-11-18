"""Add sync_ignored to lager_product

Revision ID: b4d8f2a61c93
Revises: a7c3e91f2b40
Create Date: 2026-11-18 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b4d8f2a61c93'
down_revision = 'a7c3e91f2b40'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('lager_product', schema=None) as batch_op:
        batch_op.add_column(sa.Column('sync_ignored', sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade():
    with op.batch_alter_table('lager_product', schema=None) as batch_op:
        batch_op.drop_column('sync_ignored')
