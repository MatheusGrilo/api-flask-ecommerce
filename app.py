from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_login import UserMixin

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce-db.sqlite3'
db = SQLAlchemy(app)

CORS(app)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    if 'username' in data and 'password' in data:
        existing_user = User.query.filter_by(username=data['username']).first()
        if existing_user:
            return jsonify({'message': 'User already exists'}), 400
        else:
            user = User(username=data['username'], password=data['password'])
            db.session.add(user)
            db.session.commit()
        return jsonify({'message': 'User registered successfully!'})
    else:
        return jsonify({'message': 'Missing username or password in the request data'}), 400

@app.route('/api/products/add', methods=['POST'])
def add_product():
    data = request.json
    if 'name' in data and 'price' in data:
        product = Product(name=data['name'], price=data['price'], description=data.get('description', "No description"))
        db.session.add(product)
        db.session.commit()
        return jsonify({'message': 'Product added successfully!'})
    else:
        return jsonify({'message': 'Missing name or price in the request data'}), 400

@app.route('/api/products/delete/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    product = db.session.get(Product, product_id) or ()
    if product:
        db.session.delete(product)
        db.session.commit()
        return jsonify({'message': 'Product deleted successfully!'})
    else:
        return jsonify({'message': 'Product not found'}), 404


@app.route('/api/products/<int:product_id>')
def get_product(product_id):
    product = db.session.get(Product, product_id)
    if product:
        return jsonify({'id': product.id, 'name': product.name, 'price': product.price, 'description': product.description})
    else:
        return jsonify({'message': 'Product not found'}), 404

@app.route('/api/products')
def get_products():
    products = db.session.query(Product).all()
    product_list = []
    for product in products:
        product_list.append({'id': product.id, 'name': product.name, 'price': product.price})
    return jsonify(product_list)



@app.route('/api/products/update/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({'message': 'Product not found'}), 404

    data = request.json
    if 'name' in data:
        product.name = data['name']
    if 'price' in data:
        product.price = data['price']
    if 'description' in data:
        product.description = data['description']
    db.session.commit()
    return jsonify({'message': 'Product updated successfully!'})

if __name__ == "__main__":
    app.run(debug=True)