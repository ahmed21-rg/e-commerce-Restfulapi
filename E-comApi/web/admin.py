from .models import Customer, Product, Order
from flask import request, flash, jsonify, Blueprint, current_app
from flask_login import login_required, current_user
from .init import db
import os
from werkzeug.utils import secure_filename


admin = Blueprint('admin', __name__)    

#get all customers
@admin.route('/customers', methods=['GET'])
@login_required
def all_customers():
    if current_user.id != 1:
        return jsonify({'error': 'Unauthorized access!'}), 403
    customers = Customer.query.all()

    customers_list = [{'id': customer.id, 'username': customer.username, 'email': customer.email, 'date_joined': customer.date_joined} for customer in customers]


    return jsonify(customers_list), 200

#add products
@admin.route('/products', methods=['POST'])
@login_required
def add_product():


    product_name = request.form.get('product_name')
    description = request.form.get('description')
    current_price = float(request.form.get('current_price'))
    previous_price = float(request.form.get('previous_price'))
    in_stock = int(request.form.get('in_stock', 0))
    flash_sale = request.form.get('flash_sale').lower() in ['true', '1', 'yes']

    product_picture = request.files.get("product_picture")  

    print(" request.form:", request.form)
    print(" request.files:", request.files)

    if not product_name or not current_price or not previous_price:
        return jsonify({"message":"missing required feilds!"}), 400

    if product_picture:  
   

        file_name = secure_filename(product_picture.filename)  
  
        save_path = os.path.join(current_app.root_path, 'static', 'images', file_name)  
   

        filepath = f"/static/images/{file_name}"  
   
        product_picture.save(save_path)  
   
    if not product_picture:
        return jsonify({"message":"add a product picture!"})

    new_product = Product(
        product_name=product_name,
        description=description,
        current_price=current_price,
        previous_price=previous_price,
        product_picture=filepath,
        in_stock=in_stock,
        flash_sale=flash_sale
    )

    try:
        db.session.add(new_product)
        db.session.commit()
        return jsonify({"message":"product added sucessfully!"})
    except Exception as e:
        db.session.rollback()
        print("DB Error:", e)
        return jsonify({"error": str(e)}), 500


@admin.route('/products', methods=['GET'])
@login_required
def profucts():
    product = Product.query.order_by(Product.date_added.desc()).all()
    
    product_list = []

    for i in product:
        product_list.append({
            "id": i.id,
            "product_name": i.product_name,
            "description": i.description,
            "current_price": i.current_price,
            "previous_price": i.previous_price,
            "product_picture": i.product_picture,
            "in_stock": i.in_stock,
            "flash_sale": i.flash_sale,
            "date_added": i.date_added.strftime("%Y-%m-%d %H:%M:%S")
        })

    return jsonify({'product': product_list}), 200


@admin.route('/product/<int:id>', methods=['PUT'])
@login_required
def update_item(id):
    #logic for admin can update only

    product = Product.query.get_or_404(id)

    product.product_name = request.form.get("product_name")
    product.description = request.form.get("description")
    product.current_price = request.form.get("current_price")
    product.previous_price = request.form.get("previous_price")
    product.in_stock = request.form.get("in_stock")
    flash_sale_raw = request.form.get("flash_sale")
    if flash_sale_raw is not None:
        product.flash_sale = flash_sale_raw.lower() in ['true', '1', 'yes']
    product.date_added = request.form.get("date_added")


    product_picture = request.files.get("product_picture")

    if product_picture :
        file_name = secure_filename(product_picture.filename)
        save_path = os.path.join(current_app.root_path, "static", "images", file_name)
        product_picture.save(save_path)
        product.product_picture = f"/static/images/{file_name}"

    try:
        db.session.commit()
        return jsonify({"message": "product updated!"}),200

    except Exception as e:
        print(e)
        db.session.rollback()
        return jsonify({"error": str(e)}), 500  
    

#delete item
@admin.route('/delete_item/<int:id>', methods=['DELETE'])
#@login_required
def delete_item(id):
    
    item_to_delete = Product.query.get_or_404(id)
    
    try:
        db.session.delete(item_to_delete)
        db.session.commit()
        return jsonify({"message":"item deleted successfully"}),200

    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}),500
    

#view orders
@admin.route('/orders', methods=['GET'])
@login_required
def orders():
    try:
        orders = Order.query.all()

        order_list = []
        for i in orders:
            order_list.append({
                "id":i.id,
                "price":i.price,
                "payment_id":i.payment_id,
                "quantity":i.quantity,
                "status":i.status,

                "customer":{
                    "id":i.customer.id,
                    "username":i.customer.username,
                    "email": i.customer.email,
                },
                "product":{
                    "id":i.product.id,
                    "name":i.product.product_name,
                    "price":i.product.current_price,
                    "picture":i.product.product_picture
                }
            })
        return jsonify({"orders": order_list})

    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}),500

#update order
@admin.route('/order/<int:id>', methods=['PUT'])
@login_required
def status_update(id):
    orders = Order.query.get_or_404(id)

    data = request.get_json()
    if not data or not "status":
        return jsonify({"message":"status is required!"})
    
    orders.status = data["status"]

    try:
        db.session.commit()
        ({"message":"status updated for , 'status':{order.status} "}),200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)})
    



