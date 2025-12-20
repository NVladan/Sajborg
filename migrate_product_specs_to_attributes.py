import os
import json
from app import app, db
from models import Product, Category, CategoryAttribute, ProductAttributeValue

def migrate_specs_to_attributes():
    with app.app_context():
        categories = Category.query.all()
        for category in categories:
            print(f"Processing category: {category.name}")
            # Collect all unique attribute names from products in this category
            products = Product.query.filter_by(category_id=category.id).all()
            attr_names = set()
            for product in products:
                try:
                    specs = json.loads(product.specs) if product.specs else {}
                except Exception as e:
                    print(f"  Error parsing specs for product {product.id}: {e}")
                    specs = {}
                attr_names.update(specs.keys())
            # Create CategoryAttribute for each unique attribute name
            for attr_name in attr_names:
                existing = CategoryAttribute.query.filter_by(category_id=category.id, name=attr_name).first()
                if not existing:
                    attr = CategoryAttribute(category_id=category.id, name=attr_name, type='string')
                    db.session.add(attr)
                    print(f"  Added attribute: {attr_name}")
            db.session.commit()
            # Map attribute names to their IDs
            attr_map = {a.name: a for a in CategoryAttribute.query.filter_by(category_id=category.id).all()}
            # Create ProductAttributeValue for each product/spec
            for product in products:
                try:
                    specs = json.loads(product.specs) if product.specs else {}
                except Exception as e:
                    specs = {}
                for key, value in specs.items():
                    attr = attr_map.get(key)
                    if attr:
                        existing_val = ProductAttributeValue.query.filter_by(product_id=product.id, attribute_id=attr.id).first()
                        if not existing_val:
                            pav = ProductAttributeValue(product_id=product.id, attribute_id=attr.id, value=str(value))
                            db.session.add(pav)
                            print(f"    Set {key}={value} for product {product.name}")
            db.session.commit()
    print("Migration complete.")

if __name__ == "__main__":
    migrate_specs_to_attributes() 