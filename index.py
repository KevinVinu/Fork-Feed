"""
ForkFeed — Flask Backend (Supabase/Vercel Production Version)
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
# Root directory is now the same as this file (index.py)
root_dir = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=root_dir, static_url_path='')

# Database Configuration
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or f'sqlite:///{os.path.join(root_dir, "foodsquare.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'FoodSQuare-Secret-Key-2024'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

db = SQLAlchemy(app)
jwt = JWTManager(app)
CORS(app, resources={r"/*": {"origins": "*"}})

# ─────────────────────────────────────────────────────────────────────────────
# JWT Error Handlers
# ─────────────────────────────────────────────────────────────────────────────

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({'error': 'TOKEN_EXPIRED', 'message': 'Session expired.'}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error_string):
    return jsonify({'error': 'INVALID_TOKEN', 'message': 'Invalid token.'}), 401

@jwt.unauthorized_loader
def missing_token_callback(error_string):
    return jsonify({'error': 'MISSING_TOKEN', 'message': 'Auth required.'}), 401

# ─────────────────────────────────────────────────────────────────────────────
# Static File Routes
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    try:
        return send_from_directory(app.static_folder, 'home.html')
    except:
        return "Frontend is loading... if this persists, check home.html"

@app.errorhandler(404)
def not_found(e):
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
            return raw == self.password

    def get_roles(self):
        try: return json.loads(self.roles)
        except Exception: return ["ROLE_USER"]

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
        status = 'PENDING'
        if self.items: status = self.items[0].status
        return {
            'id':            self.id,
            'paymentStatus': self.payment_status,
            'orderTime':     self.local_date_time.isoformat() if self.local_date_time else None,
            'totalPrice':    self.total,
            'userName':      self.user.user_name if self.user else None,
            'orderStatus':   status,
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
        if not identity: return False
        if identity == 'admin': return True
        claims = get_jwt()
        return 'ROLE_ADMIN' in claims.get('roles', [])
    except Exception: return False

def require_admin():
    if not is_admin():
        return jsonify({'error': 'ADMIN_REQUIRED', 'message': 'Admin privileges required'}), 403
    return None

# ─────────────────────────────────────────────────────────────────────────────
# API ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/public/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data: return 'Invalid JSON', 400
    username = data.get('userName', '').strip()
    password = data.get('password', '')
    user = User.query.filter_by(user_name=username).first()
    if not user or not user.check_password(password):
        return 'Invalid creds', 401
    token = create_access_token(identity=username, additional_claims={'roles': user.get_roles()})
    return token, 200

@app.route('/api/auth/verify', methods=['GET'])
@jwt_required()
def verify_token():
    identity = get_jwt_identity()
    user = User.query.filter_by(user_name=identity).first()
    if not user: return jsonify({'valid': False}), 401
    return jsonify({'valid': True, 'userName': user.user_name, 'roles': user.get_roles()}), 200

@app.route('/public/signUp', methods=['POST'])
def sign_up():
    data = request.get_json()
    try:
        if User.query.filter_by(user_name=data.get('userName')).first(): return 'Taken', 400
        user = User()
        user.user_name = data['userName']
        user.email = data['email']
        user.first_name = data.get('firstName', '')
        user.create_at = datetime.now()
        user.set_password(data['password'])
        db.session.add(user)
        db.session.commit()
        return "Saved", 200
    except Exception as e: return str(e), 400

@app.route('/Food/food', methods=['GET'])
def get_all_food():
    foods = Food.query.all()
    return jsonify([f.to_dict() for f in foods]), 200

@app.route('/Food/subfood', methods=['POST'])
@jwt_required()
def add_sub_food():
    err = require_admin(); if err: return err
    data = request.get_json()
    try:
        sub = FoodSubCat()
        sub.food_name = data['foodName']
        sub.price = float(data['price'])
        sub.food_id = data.get('foodId') or data.get('food', {}).get('id')
        db.session.add(sub)
        db.session.commit()
        return "Added", 200
    except: return 'Error', 400

@app.route('/Order/getUserAll', methods=['GET'])
@jwt_required()
def get_user_orders():
    identity = get_jwt_identity()
    user = User.query.filter_by(user_name=identity).first()
    orders = Orders.query.filter_by(user_id=user.id).order_by(Orders.id.desc()).all()
    return jsonify([o.to_dict() for o in orders]), 200

@app.route('/Order/getAll', methods=['GET'])
@jwt_required()
def get_all_orders():
    err = require_admin(); if err: return err
    orders = Orders.query.order_by(Orders.id.desc()).all()
    return jsonify([o.to_dict() for o in orders]), 200

@app.route('/Order/id/<int:order_id>/<status>', methods=['PATCH'])
@jwt_required()
def update_order_status(order_id, status):
    err = require_admin(); if err: return err
    order = Orders.query.get(order_id)
    for item in order.items: item.status = status.upper()
    db.session.commit()
    return jsonify(order.to_dict()), 200

# ─────────────────────────────────────────────────────────────────────────────
# DB Init & Seed
# ─────────────────────────────────────────────────────────────────────────────

def init_db():
    db.create_all()
    if not User.query.filter_by(user_name='admin').first():
        admin = User(user_name='admin', first_name='Admin', email='admin@fs.com', roles='["ROLE_USER", "ROLE_ADMIN"]')
        admin.set_password('admin123')
        admin.create_at = datetime.now()
        db.session.add(admin)
    db.session.commit()

# Vercel Runtime: Lazy initialization
_initialized = False
@app.before_request
def first_request_init():
    global _initialized
    if not _initialized:
        try:
            with app.app_context(): init_db()
            _initialized = True
        except Exception as e:
            app.logger.error(f"DB Init Error: {e}")

if __name__ == '__main__':
    with app.app_context(): init_db()
    app.run(host='0.0.0.0', port=8080, debug=True)
