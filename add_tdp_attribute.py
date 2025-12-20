from app import create_app
from models import Category, CategoryAttribute, db

def add_tdp_attribute():
    app = create_app()
    with app.app_context():
        # Components that need TDP attribute
        tdp_components = ['CPU', 'GPU', 'Power Supply']
        
        # Get all categories
        categories = Category.query.all()
        for category in categories:
            # Check if any product in this category has a component_type that needs TDP
            products = category.products
            if any(p.component_type in tdp_components for p in products):
                # Check if TDP attribute already exists
                tdp_attr = CategoryAttribute.query.filter_by(
                    category_id=category.id,
                    name='TDP'
                ).first()
                
                if not tdp_attr:
                    # Create TDP attribute
                    tdp_attr = CategoryAttribute(
                        category_id=category.id,
                        name='TDP',
                        type='integer'  # Make it an integer type
                    )
                    db.session.add(tdp_attr)
                    print(f"Added TDP attribute to category: {category.name}")
        
        db.session.commit()
        print("TDP attributes added successfully")

if __name__ == '__main__':
    add_tdp_attribute()
