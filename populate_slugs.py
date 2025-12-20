from app import create_app, db
from models import Product


def populate_slugs():
    app = create_app()
    with app.app_context():
        products = Product.query.all()
        for product in products:
            if not product.slug:
                # Generisanje slug-a iz imena proizvoda
                slug = product.name.lower().replace(' ', '-').replace('č', 'c').replace('ć', 'c').replace('š',
                                                                                                          's').replace(
                    'đ', 'dj').replace('ž', 'z')
                product.slug = ''.join(e for e in slug if e.isalnum() or e == '-')

                # Provera jedinstvenosti i dodavanje broja ako je potrebno
                original_slug = product.slug
                counter = 1
                while Product.query.filter_by(slug=product.slug).first():
                    product.slug = f"{original_slug}-{counter}"
                    counter += 1

        db.session.commit()
        print("Sva 'slug' polja su uspješno popunjena.")


if __name__ == '__main__':
    populate_slugs()