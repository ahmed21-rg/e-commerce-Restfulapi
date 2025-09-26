from flask import Flask
from flask_bcrypt import Bcrypt 
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import stripe
import os
from dotenv import load_dotenv


db = SQLAlchemy() 
bcrypt = Bcrypt()  


def create_app():

    app = Flask(__name__)

    load_dotenv()

    stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
    app.config['STRIPE_PUBLISHABLE_KEY'] = os.getenv('STRIPE_PUBLISHABLE_KEY')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
    



    bcrypt.init_app(app)
    db.init_app(app)  
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'views.login'  

    @login_manager.user_loader
    def load_user(user_id):
        from .models import Customer
        return Customer.query.get(int(user_id))
    
    from .views import views
    from .admin import admin

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(admin, url_prefix='/admin')

    with app.app_context():
        db.create_all()



    return app
