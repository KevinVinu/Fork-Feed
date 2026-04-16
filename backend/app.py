"""
ForkFeed — Flask Backend (SQLite Version)
Replaces the Spring Boot backend with identical API endpoints.
Using SQLite for easier setup and debugging.

This server also serves the frontend static files.
Run this script and navigate to: http://localhost:8080/login.html
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    JWTManager, create_access_token,
    jwt_required, get_jwt_identity, get_jwt
)
from flask_cors import CORS
import bcrypt
from datetime import datetime, timedelta
import json
import os

# ─────────────────────────────────────────────────────────────────────────────
# App & Config
# ─────────────────────────────────────────────────────────────────────────────
# Root directory is one level up from the backend folder
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
app = Flask(__name__, static_folder=root_dir, static_url_path='')

# Database configuration: Use DATABASE_URL from env if available (Production), 
# otherwise fallback to local SQLite (Development).
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # SQL-Alchemy 1.4+ requires 'postgresql://' but some providers still use 'postgres://'
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "foodsquare.db")}'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'FoodSQuare-Secret-Key-2024')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

db = SQLAlchemy(app)
jwt = JWTManager(app)
CORS(app, resources={r"/*": {"origins": "*"}})

# ─────────────────────────────────────────────────────────────────────────────
# JWT Error Handlers — return proper JSON so the frontend can handle gracefully
# ─────────────────────────────────────────────────────────────────────────────

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({
        'error': 'TOKEN_EXPIRED',
        'message': 'Your session has expired. Please login again.'
    }), 401

@jwt.invalid_token_loader
def invalid_token_callback(error_string):
    return jsonify({
        'error': 'INVALID_TOKEN',
        'message': 'Invalid authentication token. Please login again.'
    }), 401

@jwt.unauthorized_loader
def missing_token_callback(error_string):
    return jsonify({
        'error': 'MISSING_TOKEN',
        'message': 'Authentication required. Please login.'
    }), 401

@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    return jsonify({
        'error': 'REVOKED_TOKEN',
        'message': 'Token has been revoked. Please login again.'
    }), 401

# ─────────────────────────────────────────────────────────────────────────────
# Static File Routes
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    # Check if home.html exists, otherwise return a simple message
    try:
        return send_from_directory(app.static_folder, 'home.html')
    except:
        return "Food S Square Backend is Running. <a href='/login.html'>Go to Login</a>"

@app.errorhandler(404)
def not_found(e):
    # If a route is not found, try to serve it as a static file from root
    path = request.path.lstrip('/')
    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return jsonify({'error': 'Not found'}), 404

# ─────────────────────────────────────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────────────────────────────────────

class User(db.Model):
    __tablename__ = 'User'
    id         = db.Column(db.Integer, primary_key=True, autoincrement=True)
    reg_num    = db.Column('regNum', db.Integer, unique=True)
    user_name  = db.Column('userName', db.String(255), nullable=False, unique=True)
    first_name = db.Column('firstName', db.String(255))
    last_name  = db.Column('lastName', db.String(255))
    email      = db.Column(db.String(255), nullable=False, unique=True)
    password   = db.Column(db.String(255), nullable=False)
    phone      = db.Column(db.String(50))
    create_at  = db.Column('createAt', db.DateTime)
    roles      = db.Column(db.Text, default='["ROLE_USER"]')

    def set_password(self, raw):
        self.password = bcrypt.hashpw(raw.encode(), bcrypt.gensalt()).decode()

    def check_password(self, raw):
        try:
            return bcrypt.checkpw(raw.encode(), self.password.encode())
        except Exception:
            # Fallback for plain text passwords if any exist during migration
            return raw == self.password

    def get_roles(self):
        try:
            return json.loads(self.roles)
        except Exception:
            return ["ROLE_USER"]

    def to_dict(self):
        return {
            'id':        self.id,
            'userName':  self.user_name,
            'firstName': self.first_name,
            'lastName':  self.last_name,
            'email':     self.email,
            'phone':     self.phone,
            'regNum':    self.reg_num,
            'createAt':  self.create_at.isoformat() if self.create_at else None,
            'roles':     self.get_roles()
        }


class Food(db.Model):
    __tablename__ = 'food'
    id           = db.Column(db.Integer, primary_key=True, autoincrement=True)
    food_name    = db.Column('foodName', db.String(255), unique=True)
    is_available = db.Column('isAvailable', db.Boolean, default=True)
    food_sub_cat = db.relationship('FoodSubCat', backref='food', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id':          self.id,
            'foodName':    self.food_name,
            'isAvailable': self.is_available,
            'foodSubCat':  [s.to_dict() for s in self.food_sub_cat]
        }


class FoodSubCat(db.Model):
    __tablename__ = 'foodsubcat'
    id           = db.Column(db.Integer, primary_key=True, autoincrement=True)
    food_name    = db.Column('foodName', db.String(255), unique=True)
    description  = db.Column(db.String(500))
    price        = db.Column(db.Float)
    img_url      = db.Column('imgUrl', db.String(500))
    is_available = db.Column('isAvailable', db.Boolean, default=True)
    veg_or_non_veg = db.Column('vegOrNonVeg', db.String(50))
    food_id      = db.Column('foodId', db.Integer, db.ForeignKey('food.id'))

    def to_dict(self):
        return {
            'id':          self.id,
            'foodName':    self.food_name,
            'description': self.description,
            'price':       self.price,
            'imgUrl':      self.img_url,
            'isAvailable': self.is_available,
            'vegOrNonVeg': self.veg_or_non_veg,
            'food':        {'id': self.food_id},
            'foodId':      self.food_id
        }


class Orders(db.Model):
    __tablename__ = 'orders'
    id             = db.Column(db.Integer, primary_key=True, autoincrement=True)
    payment_status = db.Column('paymentStatus', db.String(50), default='SUCCESSFUL')
    local_date_time = db.Column('localDateTime', db.DateTime)
    user_id        = db.Column('user_id', db.Integer, db.ForeignKey('User.id'))
    total          = db.Column(db.Float, default=0.0)
    user           = db.relationship('User', backref='orders')
    items          = db.relationship('OrderItem', backref='order', cascade='all, delete-orphan')

    def to_dict(self):
        from_user = self.user
        # Simplified orderStatus
        status = 'PENDING'
        if self.items:
            status = self.items[0].status

        return {
            'id':            self.id,
            'paymentStatus': self.payment_status,
            'orderTime':     self.local_date_time.isoformat() if self.local_date_time else None,
            'totalPrice':    self.total,
            'userName':      from_user.user_name if from_user else None,
            'orderStatus':   status,
            'status':        status,
            'orderItems':    [i.to_dict() for i in self.items]
        }


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id          = db.Column(db.Integer, primary_key=True, autoincrement=True)
    quantity    = db.Column(db.Integer)
    total_price = db.Column('totalPrice', db.Float)
    status      = db.Column(db.String(50), default='PENDING')
    order_id    = db.Column('order_id', db.Integer, db.ForeignKey('orders.id'))
    food_id     = db.Column('food_id', db.Integer, db.ForeignKey('foodsubcat.id'))
    food_sub_cat = db.relationship('FoodSubCat')

    def to_dict(self):
        fsc = self.food_sub_cat
        return {
            'id':        self.id,
            'quantity':  self.quantity,
            'price':     fsc.price if fsc else 0,
            'foodName':  fsc.food_name if fsc else 'Unknown',
            'totalPrice': self.total_price,
            'status':    self.status
        }

# ─────────────────────────────────────────────────────────────────────────────
# Auth Decorator Helpers
# ─────────────────────────────────────────────────────────────────────────────
def is_admin():
    try:
        identity = get_jwt_identity()
        if not identity:
            return False
        if identity == 'admin':
            return True
        claims = get_jwt()
        return 'ROLE_ADMIN' in claims.get('roles', [])
    except Exception:
        return False

def require_admin():
    if not is_admin():
        return jsonify({
            'error': 'ADMIN_REQUIRED',
            'message': 'Admin privileges required'
        }), 403
    return None

# ─────────────────────────────────────────────────────────────────────────────
# AUTH ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/public/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data: return 'Invalid JSON', 400
    
    username = data.get('userName', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return 'Missing credentials', 400

    user = User.query.filter_by(user_name=username).first()
    if not user or not user.check_password(password):
        return 'Invalid username or password', 401

    roles = user.get_roles()
    token = create_access_token(
        identity=username,
        additional_claims={'roles': roles}
    )
    return token, 200


@app.route('/api/auth/verify', methods=['GET'])
@jwt_required()
def verify_token():
    """Check if current token is still valid — used by frontend before actions."""
    identity = get_jwt_identity()
    user = User.query.filter_by(user_name=identity).first()
    if not user:
        return jsonify({'valid': False}), 401
    return jsonify({
        'valid': True,
        'userName': user.user_name,
        'roles': user.get_roles()
    }), 200


@app.route('/api/auth/refresh', methods=['POST'])
@jwt_required()
def refresh_token():
    """Issue a fresh token with the same identity & claims."""
    identity = get_jwt_identity()
    user = User.query.filter_by(user_name=identity).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    roles = user.get_roles()
    new_token = create_access_token(
        identity=identity,
        additional_claims={'roles': roles}
    )
    return new_token, 200


@app.route('/public/signUp', methods=['POST'])
def sign_up():
    data = request.get_json()
    if not data: return 'Invalid JSON', 400
    
    try:
        if User.query.filter_by(user_name=data.get('userName')).first():
            return 'Username already taken', 400
        if User.query.filter_by(email=data.get('email')).first():
            return 'Email already registered', 400

        user = User()
        user.user_name  = data['userName']
        user.first_name = data.get('firstName', '')
        user.last_name  = data.get('lastName', '')
        user.email      = data['email']
        user.reg_num    = data.get('regNum')
        user.phone      = data.get('phone')
        user.roles      = json.dumps(['ROLE_USER'])
        user.create_at  = datetime.now()
        user.set_password(data['password'])

        db.session.add(user)
        db.session.commit()
        return f"{user.first_name} saved", 200
    except Exception as e:
        db.session.rollback()
        return str(e), 400

# ─────────────────────────────────────────────────────────────────────────────
# USER ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/api/users/<username>', methods=['GET'])
@jwt_required()
def get_user(username):
    user = User.query.filter_by(user_name=username).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(user.to_dict()), 200

# ─────────────────────────────────────────────────────────────────────────────
# FOOD ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/Food/food', methods=['GET'])
def get_all_food():
    foods = Food.query.all()
    return jsonify([f.to_dict() for f in foods]), 200


@app.route('/Food/food', methods=['POST'])
@jwt_required()
def add_food():
    err = require_admin()
    if err: return err

    data = request.get_json()
    try:
        food = Food()
        food.food_name    = data['foodName']
        food.is_available = data.get('isAvailable', True)
        db.session.add(food)
        db.session.commit()
        return f"{food.food_name} add", 200
    except Exception as e:
        db.session.rollback()
        return 'exist', 400


@app.route('/Food/subfood', methods=['POST'])
@jwt_required()
def add_sub_food():
    err = require_admin()
    if err: return err

    data = request.get_json()
    try:
        food_id = data.get('food', {}).get('id')
        if not food_id:
             food_id = data.get('foodId')
             
        if not food_id or not Food.query.get(food_id):
            return 'Category not found', 400

        sub = FoodSubCat()
        sub.food_name      = data['foodName']
        sub.description    = data.get('description', '')
        sub.price          = float(data.get('price', 0))
        sub.img_url        = data.get('imgUrl', '')
        sub.is_available   = data.get('isAvailable', True)
        sub.veg_or_non_veg = data.get('vegOrNonVeg', 'Veg')
        sub.food_id        = food_id

        db.session.add(sub)
        db.session.commit()
        return f"{sub.food_name} add", 200
    except Exception as e:
        db.session.rollback()
        return 'exist', 400


@app.route('/Food/food/id/<int:food_id>', methods=['GET'])
def get_food_by_id(food_id):
    food = Food.query.get(food_id)
    if not food:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(food.to_dict()), 200


@app.route('/Food/id/<int:food_id>/<flag>', methods=['PATCH'])
@jwt_required()
def update_food(food_id, flag):
    err = require_admin()
    if err: return err

    food = Food.query.get(food_id)
    if not food:
        return jsonify({'error': 'Not found'}), 404
    food.is_available = flag.lower() == 'true'
    db.session.commit()
    return jsonify(food.to_dict()), 200


@app.route('/Food/subfood/id/<int:sub_id>/<flag>', methods=['PATCH'])
@jwt_required()
def update_sub_food_availability(sub_id, flag):
    err = require_admin()
    if err: return err

    sub = FoodSubCat.query.get(sub_id)
    if not sub:
        return jsonify({'error': 'Not found'}), 404
    sub.is_available = flag.lower() == 'true'
    db.session.commit()
    return jsonify(sub.to_dict()), 200


@app.route('/Food/subfood/id/<int:sub_id>', methods=['PUT'])
@jwt_required()
def update_sub_food_details(sub_id):
    err = require_admin()
    if err: return err

    sub = FoodSubCat.query.get(sub_id)
    if not sub:
        return jsonify({'error': 'Not found'}), 404

    data = request.get_json()
    if not data: return 'Invalid JSON', 400

    try:
        if 'foodName' in data:
            sub.food_name = data['foodName']
        if 'description' in data:
            sub.description = data['description']
        if 'price' in data:
            sub.price = float(data['price'])
        if 'imgUrl' in data:
            sub.img_url = data['imgUrl']
        if 'vegOrNonVeg' in data:
            sub.veg_or_non_veg = data['vegOrNonVeg']
        if 'foodId' in data:
            sub.food_id = data['foodId']
        elif 'food' in data and 'id' in data['food']:
            sub.food_id = data['food']['id']

        db.session.commit()
        return jsonify(sub.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return str(e), 400

# ─────────────────────────────────────────────────────────────────────────────
# ORDER ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/Order', methods=['POST'])
@jwt_required()
def place_order():
    username = get_jwt_identity()
    user = User.query.filter_by(user_name=username).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()
    try:
        order = Orders()
        order.user_id        = user.id
        order.local_date_time = datetime.now()
        order.payment_status = 'SUCCESSFUL'
        order.total          = 0.0

        items_data = data.get('orderItems', [])
        total = 0.0
        order_items = []

        for item_data in items_data:
            food_id  = item_data.get('foodId')
            quantity = int(item_data.get('quantity', 1))

            food_sub = FoodSubCat.query.get(food_id)
            if not food_sub: continue

            item_total = quantity * food_sub.price
            total += item_total

            oi = OrderItem()
            oi.quantity    = quantity
            oi.total_price = item_total
            oi.status      = 'PENDING'
            oi.food_id     = food_sub.id
            order_items.append(oi)

        order.total = total
        db.session.add(order)
        db.session.flush()

        for oi in order_items:
            oi.order_id = order.id
            db.session.add(oi)

        db.session.commit()
        return jsonify(order.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@app.route('/Order/getUserAll', methods=['GET'])
@jwt_required()
def get_user_orders():
    username = get_jwt_identity()
    user = User.query.filter_by(user_name=username).first()
    if not user:
        return jsonify([]), 200
    orders = Orders.query.filter_by(user_id=user.id).order_by(Orders.id.desc()).all()
    return jsonify([o.to_dict() for o in orders]), 200


@app.route('/Order/getAll', methods=['GET'])
@jwt_required()
def get_all_orders():
    err = require_admin()
    if err: return err

    orders = Orders.query.order_by(Orders.id.desc()).all()
    return jsonify([o.to_dict() for o in orders]), 200


@app.route('/Order/id/<int:order_id>/<status>', methods=['PATCH'])
@jwt_required()
def update_order_status(order_id, status):
    err = require_admin()
    if err: return err

    order = Orders.query.get(order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404

    for item in order.items:
        item.status = status.upper()

    db.session.commit()
    return jsonify(order.to_dict()), 200

# ─────────────────────────────────────────────────────────────────────────────
# DB Init & Seed
# ─────────────────────────────────────────────────────────────────────────────

def init_db():
    # Only init if file doesn't exist
    db_file = os.path.join(basedir, "foodsquare.db")
    if not os.path.exists(db_file):
        db.create_all()
        print('Database created.')
        
        # Seed admin
        if not User.query.filter_by(user_name='admin').first():
            admin = User()
            admin.user_name  = 'admin'
            admin.first_name = 'System'
            admin.last_name  = 'Admin'
            admin.email      = 'admin@foodsquare.com'
            admin.reg_num    = 999999
            admin.create_at  = datetime.now()
            admin.roles      = json.dumps(['ROLE_USER', 'ROLE_ADMIN'])
            admin.set_password('admin123')
            db.session.add(admin)
            
        # Seed some initial categories and food
        if not Food.query.first():
            pizza = Food(food_name="Pizza", is_available=True)
            db.session.add(pizza)
            db.session.flush()
            
            item1 = FoodSubCat(
                food_name="Margherita", 
                description="Classic tomato and mozzarella",
                price=12.99,
                img_url="https://images.unsplash.com/photo-1604382354936-07c5d9983bd3?q=80&w=400",
                is_available=True,
                veg_or_non_veg="Veg",
                food_id=pizza.id
            )
            db.session.add(item1)
            
        db.session.commit()
        print('Initial data seeded.')

if __name__ == '__main__':
    # Ensure database is current
    with app.app_context():
        init_db()
    
    print('ForkFeed Backend started successfully!')
    print('Access the app at: http://localhost:8080')
    print('Admin Login: admin / admin123')
    
    # Run server
    app.run(host='0.0.0.0', port=8080, debug=True)
