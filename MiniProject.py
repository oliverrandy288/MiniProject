from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:password@localhost/ecommerce_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models
class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.String(15))

    def to_dict(self):
        return {"id": self.id, "name": self.name, "email": self.email, "phone_number": self.phone_number}

class CustomerAccount(db.Model):
    __tablename__ = 'customer_accounts'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), unique=True, nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    customer = db.relationship('Customer', backref=db.backref('account', uselist=False))

    def to_dict(self):
        return {"id": self.id, "username": self.username, "customer_id": self.customer_id}

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock_level = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "price": self.price, "stock_level": self.stock_level}

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default="Pending")
    customer = db.relationship('Customer', backref='orders')

    def to_dict(self):
        return {"id": self.id, "customer_id": self.customer_id, "order_date": self.order_date, "status": self.status}

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    order = db.relationship('Order', backref='order_items')
    product = db.relationship('Product', backref='order_items')

    def to_dict(self):
        return {"id": self.id, "order_id": self.order_id, "product_id": self.product_id, "quantity": self.quantity, "price": self.price}

# Customer CRUD operations
@app.route('/customers', methods=['POST'])
def create_customer():
    data = request.get_json()
    new_customer = Customer(name=data['name'], email=data['email'], phone_number=data.get('phone_number'))
    db.session.add(new_customer)
    db.session.commit()
    return jsonify(new_customer.to_dict()), 201

@app.route('/customers/<int:id>', methods=['GET'])
def read_customer(id):
    customer = Customer.query.get_or_404(id)
    return jsonify(customer.to_dict())

@app.route('/customers/<int:id>', methods=['PUT'])
def update_customer(id):
    data = request.get_json()
    customer = Customer.query.get_or_404(id)
    customer.name = data.get('name', customer.name)
    customer.email = data.get('email', customer.email)
    customer.phone_number = data.get('phone_number', customer.phone_number)
    db.session.commit()
    return jsonify(customer.to_dict())

@app.route('/customers/<int:id>', methods=['DELETE'])
def delete_customer(id):
    customer = Customer.query.get_or_404(id)
    db.session.delete(customer)
    db.session.commit()
    return jsonify({"message": "Customer deleted"})

# Product CRUD operations
@app.route('/products', methods=['POST'])
def create_product():
    data = request.get_json()
    new_product = Product(name=data['name'], price=data['price'], stock_level=data.get('stock_level', 0))
    db.session.add(new_product)
    db.session.commit()
    return jsonify(new_product.to_dict()), 201

@app.route('/products/<int:id>', methods=['GET'])
def read_product(id):
    product = Product.query.get_or_404(id)
    return jsonify(product.to_dict())

@app.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    data = request.get_json()
    product = Product.query.get_or_404(id)
    product.name = data.get('name', product.name)
    product.price = data.get('price', product.price)
    product.stock_level = data.get('stock_level', product.stock_level)
    db.session.commit()
    return jsonify(product.to_dict())

@app.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Product deleted"})

@app.route('/products', methods=['GET'])
def list_products():
    products = Product.query.all()
    return jsonify([product.to_dict() for product in products])

# Order CRUD operations
@app.route('/orders', methods=['POST'])
def place_order():
    data = request.get_json()
    new_order = Order(customer_id=data['customer_id'])
    db.session.add(new_order)
    db.session.commit()
    
    for item in data['items']:
        product = Product.query.get(item['product_id'])
        if product and product.stock_level >= item['quantity']:
            order_item = OrderItem(
                order_id=new_order.id,
                product_id=item['product_id'],
                quantity=item['quantity'],
                price=product.price * item['quantity']
            )
            product.stock_level -= item['quantity']
            db.session.add(order_item)
        else:
            return jsonify({"error": f"Insufficient stock for product ID {item['product_id']}"}), 400

    db.session.commit()
    return jsonify(new_order.to_dict()), 201

@app.route('/orders/<int:id>', methods=['GET'])
def retrieve_order(id):
    order = Order.query.get_or_404(id)
    return jsonify(order.to_dict())

@app.route('/orders/<int:id>/items', methods=['GET'])
def order_items(id):
    order = Order.query.get_or_404(id)
    items = [item.to_dict() for item in order.order_items]
    return jsonify(items)

# Run the application
if __name__ == "__main__":
    db.create_all()  # This line initializes the tables in the database
    app.run(debug=True)
