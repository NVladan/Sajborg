from datetime import datetime
from sqlalchemy import CheckConstraint
from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Association table for order items
order_items = db.Table('order_items',
                       db.Column('order_id', db.Integer, db.ForeignKey('order.id'), primary_key=True),
                       db.Column('product_id', db.Integer, db.ForeignKey('product.id'), primary_key=True),
                       db.Column('quantity', db.Integer, nullable=False, default=1),
                       db.Column('price', db.Float, nullable=False),
                       db.Column('extended_warranty', db.Boolean, default=False, server_default='0'),
                       CheckConstraint('quantity >= 1', name='ck_order_items_quantity'),
                       CheckConstraint('price > 0', name='ck_order_items_price'),
                       )

# Association table for PC builds
build_components = db.Table('build_components',
                            db.Column('build_id', db.Integer, db.ForeignKey('pc_build.id'), primary_key=True),
                            db.Column('product_id', db.Integer, db.ForeignKey('product.id'), primary_key=True),
                            db.Column('quantity', db.Integer, nullable=False, default=1)
                            )


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    address = db.Column(db.String(256))
    city = db.Column(db.String(64))
    postal_code = db.Column(db.String(32))
    country = db.Column(db.String(64))
    phone_number = db.Column(db.String(32))
    role = db.Column(db.String(20), nullable=False, default='musterija')
    is_subscribed = db.Column(db.Boolean, default=False)
    is_banned = db.Column(db.Boolean, default=False, nullable=False) # NOVO POLJE
    failed_login_count = db.Column(db.Integer, default=0, nullable=False, server_default='0')
    locked_until = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    orders = db.relationship('Order', backref='user', lazy=True)
    cart_items = db.relationship('CartItem', backref='user', lazy=True, cascade="all, delete-orphan")
    pc_builds = db.relationship('PCBuild', backref='user', lazy=True)
    reviews = db.relationship('Review', backref='author', lazy='dynamic')

    messages_sent = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy='dynamic')
    messages_received = db.relationship('Message', foreign_keys='Message.recipient_id', backref='recipient',
                                        lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    slug = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.Text)
    image_path = db.Column(db.String(256), default='img/category-default.png')
    parent_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    is_featured = db.Column(db.Boolean, default=False)
    component_type = db.Column(db.String(64), nullable=True)
    is_public = db.Column(db.Boolean, default=True, nullable=False)

    parent = db.relationship('Category', remote_side=[id],
                             backref=db.backref('subcategories', cascade="all, delete-orphan"))
    products = db.relationship('Product', backref='category', lazy=True, cascade="all, delete-orphan")

    # Performance indexes for category queries
    __table_args__ = (
        db.Index('idx_category_parent', 'parent_id'),
        db.Index('idx_category_featured', 'is_featured'),
        db.Index('idx_category_public', 'is_public'),
    )

    def __repr__(self):
        return f'<Category {self.name}>'


class ProductImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    image_path = db.Column(db.String(256), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ProductImage {self.id} for Product {self.product_id}>'


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    specs = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    component_type = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    featured = db.Column(db.Boolean, default=False)
    purchase_price = db.Column(db.Float, nullable=True)
    reservation_note = db.Column(db.String(255), nullable=True)
    internal_note = db.Column(db.Text, nullable=True)
    for_company = db.Column(db.Boolean, default=False)
    is_publicly_visible = db.Column(db.Boolean, default=True, nullable=False)
    slug = db.Column(db.String(128), unique=True, nullable=False)
    condition = db.Column(db.String(20), nullable=False, default='Novo')
    availability = db.Column(db.String(50), nullable=False, default='Dostupno odmah')
    cart_items = db.relationship('CartItem', backref='product', lazy=True)
    images = db.relationship('ProductImage', backref='product', lazy=True, cascade='all, delete-orphan')
    attribute_values = db.relationship('ProductAttributeValue', backref='product', lazy=True,
                                       cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='product', lazy='dynamic',
                              cascade='all, delete-orphan')

    # Performance indexes and CHECK constraints
    __table_args__ = (
        db.Index('idx_product_category_stock', 'category_id', 'stock'),
        db.Index('idx_product_visibility', 'is_publicly_visible'),
        db.Index('idx_product_featured', 'featured'),
        db.Index('idx_product_component_type', 'component_type'),
        db.Index('idx_product_name', 'name'),
        CheckConstraint('price > 0', name='ck_product_price_positive'),
        CheckConstraint('stock >= 0', name='ck_product_stock_non_negative'),
    )

    def __repr__(self):
        return f'<Product {self.name}>'

    @property
    def average_rating(self):
        reviews_list = self.reviews.all()
        if not reviews_list:
            return 0
        return sum(review.rating for review in reviews_list) / len(reviews_list)


class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    extended_warranty = db.Column(db.Boolean, default=False)

    # Performance index and CHECK constraints for cart lookups
    __table_args__ = (
        db.Index('idx_cartitem_user_product', 'user_id', 'product_id'),
        CheckConstraint('quantity >= 1', name='ck_cartitem_quantity_positive'),
    )

    def __repr__(self):
        return f'<CartItem {self.id}>'


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(32), default='pending')
    payment_method = db.Column(db.String(32), default='cash_on_delivery')
    shipping_first_name = db.Column(db.String(64))
    shipping_last_name = db.Column(db.String(64))
    shipping_address = db.Column(db.String(256))
    shipping_city = db.Column(db.String(64))
    shipping_postal_code = db.Column(db.String(32))
    shipping_country = db.Column(db.String(64))
    shipping_phone_number = db.Column(db.String(32))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    products = db.relationship('Product', secondary=order_items, lazy='subquery',
                               backref=db.backref('orders', lazy=True))

    # Performance indexes for order queries
    __table_args__ = (
        db.Index('idx_order_user_status', 'user_id', 'status'),
        db.Index('idx_order_status_created', 'status', 'created_at'),
    )

    def __repr__(self):
        return f'<Order {self.id}>'

    @property
    def full_shipping_address(self):
        return f"{self.shipping_first_name} {self.shipping_last_name}\n{self.shipping_address}\n{self.shipping_city}, {self.shipping_postal_code}\n{self.shipping_country}\nTelefon: {self.shipping_phone_number}"


class PCBuild(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    is_public = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    components = db.relationship('Product', secondary=build_components, lazy='subquery')

    def __repr__(self):
        return f'<PCBuild {self.name}>'


class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Subscription {self.email}>'


class CategoryAttribute(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    type = db.Column(db.String(32), default='string')
    sort_order = db.Column(db.Integer, default=0)
    category = db.relationship('Category', backref=db.backref('attributes', lazy=True, cascade='all, delete-orphan'))
    options = db.relationship('AttributeOption', backref='attribute', lazy=True, cascade='all, delete-orphan')


class AttributeOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    attribute_id = db.Column(db.Integer, db.ForeignKey('category_attribute.id'), nullable=False)
    value = db.Column(db.String(128), nullable=False)

    def __repr__(self):
        return f'<AttributeOption {self.value}>'


class ProductAttributeValue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    attribute_id = db.Column(db.Integer, db.ForeignKey('category_attribute.id'), nullable=False)
    value = db.Column(db.String(128), nullable=False)
    attribute = db.relationship('CategoryAttribute',
                                backref=db.backref('values', lazy=True, cascade='all, delete-orphan'))

    # Performance indexes for attribute filtering queries
    __table_args__ = (
        db.Index('idx_pav_product_attribute', 'product_id', 'attribute_id'),
        db.Index('idx_pav_attribute_value', 'attribute_id', 'value'),
    )


class LagerProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    stock = db.Column(db.Integer, default=0)
    purchase_price = db.Column(db.Float, nullable=True)
    reservation_note = db.Column(db.String(255), nullable=True)
    internal_note = db.Column(db.Text, nullable=True)
    for_company = db.Column(db.Boolean, default=False)
    category_id = db.Column(db.Integer, db.ForeignKey('lager_category.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    category = db.relationship('LagerCategory', backref='lager_products')

    def __repr__(self):
        return f'<LagerProduct {self.name}>'


class LagerCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    slug = db.Column(db.String(64), unique=True, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('lager_category.id'), nullable=True)
    # ISPRAVKA: Dodajemo server_default='0'
    sort_order = db.Column(db.Integer, nullable=False, default=0, server_default='0')

    parent = db.relationship('LagerCategory', remote_side=[id],
                             backref=db.backref('subcategories', cascade="all, delete-orphan"))

    def __repr__(self):
        return f'<LagerCategory {self.name}>'


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Message {self.id}>'


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author = db.relationship('User', backref=db.backref('posts', lazy=True))
    featured_image = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_published = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Post {self.title}>'


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, CheckConstraint('rating >= 1 AND rating <= 5', name='ck_review_rating_range'), nullable=False)
    text = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    # Veza sa narudžbom osigurava da je korisnik zaista kupio proizvod
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=True)

    # Prevent duplicate reviews: one review per user per product per order
    __table_args__ = (
        db.UniqueConstraint('user_id', 'product_id', 'order_id', name='uq_review_user_product_order'),
    )

    order = db.relationship('Order', backref=db.backref('reviews', lazy=True, cascade="all, delete-orphan"))

    def __repr__(self):
        return f'<Review od {self.author.username} za {self.product.name}>'