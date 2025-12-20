"""Add slug url descriptions

Revision ID: 92f70bfb9410
Revises: 
Create Date: 2025-09-28 16:45:12.123456

"""
from alembic import op
import sqlalchemy as sa
import re


# revision identifiers, used by Alembic.
revision = '92f70bfb9410'
down_revision = None
branch_labels = None
depends_on = None

# Povezivanje sa Product tabelom za popunjavanje podataka
product_table = sa.table('product',
    sa.column('id', sa.Integer),
    sa.column('name', sa.String),
    sa.column('slug', sa.String)
)


def upgrade():
    # Korak 1: Dodajemo kolonu kao OPCIONU (nullable=True)
    with op.batch_alter_table('product', schema=None) as batch_op:
        batch_op.add_column(sa.Column('slug', sa.String(length=128), nullable=True))
        batch_op.create_unique_constraint("uq_product_slug", ['slug'])

    # Korak 2: Popunjavamo podatke za postojeće proizvode
    bind = op.get_bind()
    session = sa.orm.Session(bind=bind)

    products = session.query(product_table).all()
    for product in products:
        if not product.slug:
            # Generisanje slug-a iz imena proizvoda
            slug = product.name.lower().replace(' ', '-').replace('č', 'c').replace('ć', 'c').replace('š', 's').replace('đ', 'dj').replace('ž', 'z')
            slug = ''.join(e for e in slug if e.isalnum() or e == '-')

            # Provera jedinstvenosti i dodavanje broja ako je potrebno
            original_slug = slug
            counter = 1
            # Malo drugačiji upit za provjeru
            while bind.execute(sa.select(product_table).where(product_table.c.slug == slug)).first():
                slug = f"{original_slug}-{counter}"
                counter += 1

            session.execute(
                product_table.update().where(product_table.c.id == product.id).values(slug=slug)
            )
    session.commit()

    # Korak 3: Postavljamo kolonu kao OBAVEZNU (nullable=False)
    with op.batch_alter_table('product', schema=None) as batch_op:
        batch_op.alter_column('slug',
               existing_type=sa.VARCHAR(length=128),
               nullable=False)


def downgrade():
    with op.batch_alter_table('product', schema=None) as batch_op:
        batch_op.drop_constraint("uq_product_slug", type_='unique')
        batch_op.drop_column('slug')