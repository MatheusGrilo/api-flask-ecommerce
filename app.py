from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_login import (
    UserMixin,
    LoginManager,
    login_required,
    login_user,
    logout_user,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os

load_dotenv()
app = Flask(__name__)
app.config["SECRET_KEY"] = (
    os.getenv("SECRET_KEY") if os.getenv("SECRET_KEY") else "use_some_key_as_default"
)
app.config["SQLALCHEMY_DATABASE_URI"] = (
    os.getenv("SQLALCHEMY_DATABASE_URI")
    if os.getenv("SQLALCHEMY_DATABASE_URI")
    else "sqlite:///ecommerce-db.sqlite3"
)
app.config["DEBUG"] = os.getenv("DEBUG") if os.getenv("DEBUG") else True

if app.config["DEBUG"] == "True":
    print("DEBUG mode is enabled in environment variables.")
    print(
        f"SQLALCHEMY_DATABASE_URI: {app.config['SQLALCHEMY_DATABASE_URI']}"
        if app.config["SQLALCHEMY_DATABASE_URI"]
        else "Using default SQLite database"
    )

    print(f"SECRET_KEY: {app.config['SECRET_KEY']}")

login_manager = LoginManager()
db = SQLAlchemy(app)
login_manager.init_app(app)
login_manager.login_view = "login"

CORS(app)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)
    cart = db.relationship("CartItem", backref="user", lazy=True)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)


class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)


@app.route("/")
def hello_world():
    return "Hello, World!"


@app.route("/register", methods=["POST"])
def register():
    data = request.json
    if "username" in data and "password" in data:
        existing_user = User.query.filter_by(username=data["username"]).first()
        if existing_user:
            return jsonify({"message": "User already exists"}), 400
        else:
            hashed_password = generate_password_hash(
                data["password"], method="pbkdf2:sha256"
            )
            user = User(username=data["username"], password=hashed_password)
            db.session.add(user)
            db.session.commit()
        return jsonify({"message": "User registered successfully!"})
    else:
        return jsonify(
            {"message": "Missing username or password in the request data"}
        ), 400


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.route("/login", methods=["POST"])
def login():
    data = request.json
    if "username" in data and "password" in data:
        user = User.query.filter_by(username=data["username"]).first()
        if user and check_password_hash(user.password, data["password"]):
            login_user(user)
            return jsonify({"message": "Login successful!"})
        else:
            return jsonify({"message": "Invalid username or password"}), 401
    else:
        return jsonify(
            {"message": "Missing username or password in the request data"}
        ), 400


@login_required
@app.route("/logout", methods=["POST"])
def logout():
    logout_user()
    return jsonify({"message": "Logout successful!"})


@app.route("/api/products/add", methods=["POST"])
@login_required
def add_product():
    data = request.json
    if "name" in data and "price" in data:
        product = Product(
            name=data["name"],
            price=data["price"],
            description=data.get("description", "No description"),
        )
        db.session.add(product)
        db.session.commit()
        return jsonify({"message": "Product added successfully!"})
    else:
        return jsonify({"message": "Missing name or price in the request data"}), 400


@app.route("/api/products/delete/<int:product_id>", methods=["DELETE"])
@login_required
def delete_product(product_id):
    product = db.session.get(Product, product_id) or ()
    if product:
        db.session.delete(product)
        db.session.commit()
        return jsonify({"message": "Product deleted successfully!"})
    else:
        return jsonify({"message": "Product not found"}), 404


@app.route("/api/products/<int:product_id>")
@login_required
def get_product(product_id):
    product = db.session.get(Product, product_id)
    if product:
        return jsonify(
            {
                "id": product.id,
                "name": product.name,
                "price": product.price,
                "description": product.description,
            }
        )
    else:
        return jsonify({"message": "Product not found"}), 404


@app.route("/api/products")
@login_required
def get_products():
    products = db.session.query(Product).all()
    product_list = []
    for product in products:
        product_list.append(
            {"id": product.id, "name": product.name, "price": product.price}
        )
    return jsonify(product_list)


@app.route("/api/products/update/<int:product_id>", methods=["PUT"])
@login_required
def update_product(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({"message": "Product not found"}), 404

    data = request.json
    if "name" in data:
        product.name = data["name"]
    if "price" in data:
        product.price = data["price"]
    if "description" in data:
        product.description = data["description"]
    db.session.commit()
    return jsonify({"message": "Product updated successfully!"})


@app.route("/api/cart/add/<int:product_id>", methods=["POST"])
@login_required
def add_to_cart(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({"message": "Product not found"}), 404
    cart_item = CartItem(product_id=product_id, user_id=current_user.id)
    db.session.add(cart_item)
    db.session.commit()
    return jsonify({"message": "Product added to cart successfully!"})


@app.route("/api/cart", methods=["GET"])
@login_required
def get_cart():
    cart_items = db.session.query(CartItem).filter_by(user_id=current_user.id).all()
    cart_list = []
    for cart_item in cart_items:
        product = db.session.get(Product, cart_item.product_id)
        cart_list.append(
            {
                "id": cart_item.id,
                "product_id": cart_item.product_id,
                "product_name": product.name,
                "product_price": product.price,
                "quantity": cart_item.quantity,
            }
        )
    return jsonify(cart_list)


@app.route("/api/cart/remove/<int:cart_item_id>", methods=["DELETE"])
@login_required
def delete_cart_item(cart_item_id):
    cart_item = (
        db.session.query(CartItem)
        .filter(CartItem.id == cart_item_id, CartItem.user_id == current_user.id)
        .first()
    )
    if cart_item and cart_item.user_id == current_user.id:
        db.session.delete(cart_item)
        db.session.commit()
        return jsonify({"message": "Cart item deleted successfully!"})
    else:
        return jsonify({"message": "Cart item not found"}), 404


@app.route("/api/cart/checkout", methods=["POST"])
@login_required
def checkout():
    cart_items = db.session.query(CartItem).filter_by(user_id=current_user.id).all()
    if len(cart_items) == 0:
        return jsonify({"message": "Cart is empty!"}), 400
    else:
        total = 0
        for cart_item in cart_items:
            product = db.session.get(Product, cart_item.product_id)
            total += product.price * cart_item.quantity
            db.session.delete(cart_item)
        db.session.commit()
        return jsonify({"message": f"Checkout successful! Total amount paid: ${total}"})


if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"])
