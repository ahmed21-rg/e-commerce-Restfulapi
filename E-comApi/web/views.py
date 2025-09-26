from flask_login import login_required, current_user, login_user, logout_user
from flask import request, flash, jsonify, Blueprint
from .init import db
from .models import Customer, Product, Cart, Order
import stripe

views = Blueprint('views', __name__)



@views.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    v_email = Customer.validate_email(email)
    if v_email:
        return jsonify({"email error"}), 400
    
    h_password = Customer.hash_password(password)

    new_customer = Customer(
        username=username,
        email=email,
        password=h_password
    )
    

    db.session.add(new_customer)
    db.session.commit()
    return jsonify({'message': 'User registered successfully!'}), 201

@views.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    user = Customer.query.filter_by(email=email).first()
    if not user and not user.check_password(password):
        return jsonify({'error': 'Invalid email or password!'}), 401
    else:
        login_user(user)
        return jsonify({'message': 'User logged in successfully!'}), 200


@views.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'User logged out successfully!'}), 200


@views.route('/change_password', methods=['PUT'])
@login_required
def change_password():
    data = request.get_json()

    old_password = data.get("password")
    new_password = data.get("new_password")

    if not current_user.check_password(old_password):
        return jsonify({'error': 'Old password is incorrect!'}), 401
  
    current_user.password = Customer.hash_password(new_password)
    
    db.session.commit()
    return jsonify({'message': 'Password changed successfully!'}), 200



@views.route('/home', methods=['GET'])
def home():
    return jsonify({'message': 'Welcome to the E-commerce API!'}), 200


#add-to-cart 
@views.route('/cart/<int:id>', methods=['POST'])
@login_required
def add_to_cart(id):
    #get the product id if not then error
    item_to_add = Product.query.get_or_404(id)
    
    item_exists = Cart.query.filter_by(product_link=id, customer_link=current_user.id).first()

    try:
        if item_exists:
            try:
                item_exists.quantity += 1
                db.session.commit()

            except Exception as e:
                print(e)
                db.session.rollback()
        
        else:
            new_item = Cart(
                quantity = 1,
                customer_link = current_user.id,    
                product_link = item_to_add.id     
            )
            db.session.add(new_item)

        db.session.commit()
        return jsonify({
            "product":{
                "product_id": item_to_add.id,
                "product_name": item_to_add.product_name
            }
        }),200
    
    except Exception as e:
        return jsonify({"error": str(e)}),500
    

#get cart items
@views.route("/cart", methods=['GET'])
@login_required
def cart():
    cart = Cart.query.filter_by(customer_link=current_user.id).all()

    try:
        cart_items = []
        for item in cart:
            cart_items.append({
                "product_id":item.product.id,
                "product_name":item.product.product_name,
                "description":item.product.description,
                "price":item.product.current_price,
                "image":item.product.product_picture,
                "quantity":item.quantity,
                "total":item.quantity*item.product.current_price
            })
        return jsonify({"cart":cart_items}),200
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}),500


#update quantity in cart
@views.route('/cart/<int:id>', methods=['PUT'])
@login_required
def update_quantity(id):
    try:

        cart_item = Cart.query.filter_by(product_link=id, customer_link=current_user.id).first()

        if not cart_item:
            return jsonify({"message": "cart item not found"}), 404
        
        cart_item.quantity += 1
        db.session.commit()

        return jsonify({
            "message": "cart quantity updated",
            "cart_item":{
                "product_name": cart_item.product.product_name,
                "product_id": cart_item.product.id,
                "quantity": cart_item.quantity,
                "total": cart_item.quantity * cart_item.product.current_price
            }
        }), 200
    
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}),500
    

# minus the quantity from cart
@views.route('/cart/<int:id>/minus', methods=['PUT'])
@login_required
def minus(id):
    try:
        cart = Cart.query.filter_by(product_link=id, customer_link=current_user.id).first()
        
        if cart.quantity > 1:
            cart.quantity -=1
            db.session.commit()
        else:
            return jsonify({"message": "Minimum quantity is 1"}),400


        return jsonify({
            "message": "cart item quantity decreased",
            "product":{
            "product_id": cart.product.id,
            "product_name": cart.product.product_name,
            "quantity": cart.quantity
            }

        }), 200
    except Exception as e:
        print(e)
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
@views.route('/checkout', methods=["POST"])
@login_required
def checkout():
    try:
        cart_items = Cart.query.filter_by(customer_link=current_user.id).all()
        

        line_items = []
        for cart_item in cart_items:
            product = Product.query.get(cart_item.product_link)
            
            line_items.append({
                "price_data":{
                    "currency":"usd",
                    "product_data":{
                        "name": product.product_name,
                        "description": product.description
                    },
                    "unit_amount": int(product.current_price * 100),
                },
                "quantity": cart_item.quantity
            })

        create_checkout_session = stripe.checkout.Session.create(
            payment_method_types=  ['card'],
            line_items = line_items,
            mode='payment',
            success_url='http://localhost:5000/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url='http://localhost:5000/cancel',
            client_reference_id=current_user.id  
        )   
        return jsonify ({"checkout_url":create_checkout_session.url}), 200
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)})

@views.route("/success")
def payment_success():
    session_id = request.args.get("session_id")
    if not session_id:
        return "Missing session ID", 400

    session_id = request.args.get("session_id")
    session = stripe.checkout.Session.retrieve(session_id)
    customer_id = session.client_reference_id  #this is your Customer.id
    
    cart_items = Cart.query.filter_by(customer_link=customer_id).all()

    for cart_item in cart_items:
        order = Order(
            price=cart_item.product.current_price * cart_item.quantity,
            payment_id=session.id,
            quantity=cart_item.quantity,
            status="Paid",
            customer_link=customer_id,
            product_link=cart_item.product.id,
        )
        db.session.add(order)
    
    product = Cart.query.filter_by(customer_link=customer_id).all()
    for item in product:
        db.session.delete(item)


    db.session.commit()

    return jsonify({
            "message": "Payment successful, order placed.",
            "session_id": session.id,
            "order_count": len(cart_items)

        }), 200

