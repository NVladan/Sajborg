"""Link product to lager_product

Revision ID: a7c3e91f2b40
Revises: 063b1e814d29
Create Date: 2026-10-07 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a7c3e91f2b40'
down_revision = '063b1e814d29'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('product', schema=None) as batch_op:
        batch_op.add_column(sa.Column('lager_product_id', sa.Integer(), nullable=True))
        batch_op.create_index('ix_product_lager_product_id', ['lager_product_id'], unique=False)
        batch_op.create_foreign_key('fk_product_lager_product_id', 'lager_product',
                                    ['lager_product_id'], ['id'], ondelete='SET NULL')


def downgrade():
    with op.batch_alter_table('product', schema=None) as batch_op:
        batch_op.drop_constraint('fk_product_lager_product_id', type_='foreignkey')
        batch_op.drop_index('ix_product_lager_product_id')
        batch_op.drop_column('lager_product_id')
