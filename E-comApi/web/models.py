from flask_login import UserMixin
from .init import db
from flask_bcrypt import generate_password_hash, check_password_hash



class Customer(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    username = db.Column(db.String(150), nullable=False)
    date_joined = db.Column(db.DateTime, default=db.func.current_timestamp())
    cart_items = db.relationship('Cart', backref='customer', lazy=True)
    orders = db.relationship('Order', backref='customer', lazy=True)

    @staticmethod
    def validate_email( email):
        existing_email = Customer.query.filter_by(email=email).first()
        if existing_email:
            return f'Email {email} is already registered. Please use a different email!'

    @staticmethod
    def hash_password( password):
        return generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        return check_password_hash(self.password, password) 

    def __repr__(self):
        return f"Customer('{self.username}', '{self.email}')"
    
    
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    current_price = db.Column(db.Float, nullable=False)
    previous_price = db.Column(db.Float, nullable=False)
    product_picture = db.Column(db.String(1500), nullable=True)
    in_stock = db.Column(db.Integer, default=0)
    flash_sale = db.Column(db.Boolean, default=False)
    date_added = db.Column(db.DateTime, default=db.func.current_timestamp())
    carts = db.relationship('Cart', backref='product', lazy=True)      
    orders = db.relationship('Order', backref='product', lazy=True)    

    def __repr__(self):
        return f"Product('{self.product_name}', '{self.current_price}')" 
    
class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, default=0)
    customer_link = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    product_link = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    def __repr__(self):  # String representation for debugging and logging
        # Shows cart id and product link for easy identification
        return f'(Cart {self.id}  {self.product_link})'

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    price = db.Column(db.Float, nullable=False)
    payment_id = db.Column(db.String(1000), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    status = db.Column(db.String(50), nullable=False)

    customer_link = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    product_link = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)

    def __repr__(self):

        return f"Order('{self.id}', '{self.price}', '{self.status}')"
