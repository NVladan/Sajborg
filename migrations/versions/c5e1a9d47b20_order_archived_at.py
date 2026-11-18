"""Add archived_at to order

Revision ID: c5e1a9d47b20
Revises: b4d8f2a61c93
Create Date: 2026-11-18 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c5e1a9d47b20'
down_revision = 'b4d8f2a61c93'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('order', schema=None) as batch_op:
        batch_op.add_column(sa.Column('archived_at', sa.DateTime(), nullable=True))
        batch_op.create_index('ix_order_archived_at', ['archived_at'], unique=False)


def downgrade():
    with op.batch_alter_table('order', schema=None) as batch_op:
        batch_op.drop_index('ix_order_archived_at')
        batch_op.drop_column('archived_at')
