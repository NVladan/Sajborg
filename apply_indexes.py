"""
Script to manually apply performance indexes to the database.
This script directly executes SQL to create indexes without using migrations.
"""
import sqlite3
import os

# Get the database path
db_path = os.path.join(os.path.dirname(__file__), 'instance', 'pcshop.db')

print(f"Connecting to database: {db_path}")

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# List of indexes to create
indexes = [
    # Product indexes
    ("idx_product_category_stock", "CREATE INDEX IF NOT EXISTS idx_product_category_stock ON product (category_id, stock)"),
    ("idx_product_visibility", "CREATE INDEX IF NOT EXISTS idx_product_visibility ON product (is_publicly_visible)"),
    ("idx_product_featured", "CREATE INDEX IF NOT EXISTS idx_product_featured ON product (featured)"),
    ("idx_product_component_type", "CREATE INDEX IF NOT EXISTS idx_product_component_type ON product (component_type)"),

    # ProductAttributeValue indexes
    ("idx_pav_product_attribute", "CREATE INDEX IF NOT EXISTS idx_pav_product_attribute ON product_attribute_value (product_id, attribute_id)"),
    ("idx_pav_attribute_value", "CREATE INDEX IF NOT EXISTS idx_pav_attribute_value ON product_attribute_value (attribute_id, value)"),

    # CartItem index
    ("idx_cartitem_user_product", "CREATE INDEX IF NOT EXISTS idx_cartitem_user_product ON cart_item (user_id, product_id)"),

    # Order indexes
    ("idx_order_user_status", "CREATE INDEX IF NOT EXISTS idx_order_user_status ON \"order\" (user_id, status)"),
    ("idx_order_status_created", "CREATE INDEX IF NOT EXISTS idx_order_status_created ON \"order\" (status, created_at)"),

    # Category indexes
    ("idx_category_parent", "CREATE INDEX IF NOT EXISTS idx_category_parent ON category (parent_id)"),
    ("idx_category_featured", "CREATE INDEX IF NOT EXISTS idx_category_featured ON category (is_featured)"),
    ("idx_category_public", "CREATE INDEX IF NOT EXISTS idx_category_public ON category (is_public)"),
]

print("\nApplying performance indexes...")
print("=" * 60)

created_count = 0
skipped_count = 0

for index_name, sql in indexes:
    try:
        cursor.execute(sql)
        print(f"[OK] Created index: {index_name}")
        created_count += 1
    except sqlite3.OperationalError as e:
        if "already exists" in str(e):
            print(f"[SKIP] Index already exists: {index_name}")
            skipped_count += 1
        else:
            print(f"[ERROR] Error creating index {index_name}: {e}")

# Commit the changes
conn.commit()

print("=" * 60)
print(f"\nSummary:")
print(f"  Indexes created: {created_count}")
print(f"  Indexes skipped (already exist): {skipped_count}")
print(f"  Total indexes: {len(indexes)}")

# Show database indexes
print("\n" + "=" * 60)
print("Current database indexes:")
print("=" * 60)
cursor.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%' ORDER BY tbl_name, name")
for row in cursor.fetchall():
    print(f"  {row[1]}.{row[0]}")

# Close the connection
conn.close()

print("\n[SUCCESS] Database indexes applied successfully!")
print("\nNote: These indexes will significantly improve query performance on:")
print("  - Product listings and filtering")
print("  - Cart operations")
print("  - Order management")
print("  - Category navigation")
