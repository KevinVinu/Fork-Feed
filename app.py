import os
import json
import bcrypt
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    JWTManager, create_access_token,
    jwt_required, get_jwt_identity, get_jwt
)
from flask_cors import CORS

# ─────────────────────────────────────────────────────────────────────────────
# App & Config
# ─────────────────────────────────────────────────────────────────────────────
root_dir = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=root_dir, static_url_path='')

# Auth Configuration
app.config['JWT_SECRET_KEY'] = 'FoodSQuare-Secret-Key-2024'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Database Configuration (Supabase / Postgres)
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url or f'sqlite:///{os.path.join(root_dir, "foodsquare.db")}'

db = SQLAlchemy(app)
jwt = JWTManager(app)
CORS(app, resources={r"/*": {"origins": "*"}})

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
        try: return bcrypt.checkpw(raw.encode(), self.password.encode())
        except: return raw == self.password
    def get_roles(self):
        try: return json.loads(self.roles)
        except: return ["ROLE_USER"]
    def to_dict(self):
        return {
            'id': self.id, 'userName': self.user_name, 'firstName': self.first_name,
            'lastName': self.last_name, 'email': self.email, 'phone': self.phone,
            'regNum': self.reg_num, 'createAt': self.create_at.isoformat() if self.create_at else None,
            'roles': self.get_roles()
        }

class Food(db.Model):
    __tablename__ = 'food'
    id           = db.Column(db.Integer, primary_key=True, autoincrement=True)
    food_name    = db.Column('foodName', db.String(255), unique=True)
    is_available = db.Column('isAvailable', db.Boolean, default=True)
    food_sub_cat = db.relationship('FoodSubCat', backref='food', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id, 'foodName': self.food_name, 'isAvailable': self.is_available,
            'foodSubCat': [s.to_dict() for s in self.food_sub_cat]
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
            'id': self.id, 'foodName': self.food_name, 'description': self.description,
            'price': self.price, 'imgUrl': self.img_url, 'isAvailable': self.is_available,
            'vegOrNonVeg': self.veg_or_non_veg, 'foodId': self.food_id
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
            'id': self.id, 'paymentStatus': self.payment_status,
            'orderTime': self.local_date_time.isoformat() if self.local_date_time else None,
            'totalPrice': self.total, 'userName': self.user.user_name if self.user else None,
            'orderStatus': status, 'orderItems': [i.to_dict() for i in self.items]
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
            'id': self.id, 'quantity': self.quantity, 'price': fsc.price if fsc else 0,
            'foodName': fsc.food_name if fsc else 'Unknown', 'totalPrice': self.total_price, 'status': self.status
        }

# ─────────────────────────────────────────────────────────────────────────────
# Auth Helpers
# ─────────────────────────────────────────────────────────────────────────────
def is_admin():
    identity = get_jwt_identity()
    if identity == 'admin': return True
    claims = get_jwt()
    return 'ROLE_ADMIN' in claims.get('roles', [])

def require_admin():
    if not is_admin():
        return jsonify({'error': 'ADMIN_REQUIRED', 'message': 'Admin privileges required'}), 403
    return None

# ─────────────────────────────────────────────────────────────────────────────
# CORE API ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/')
def site_index():
    try: return send_from_directory(app.static_folder, 'home.html')
    except: return "FoodSquare Backend Online. <a href='/login.html'>Go to Login</a>"

@app.route('/public/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('userName', '').strip()
    password = data.get('password', '')
    user = User.query.filter_by(user_name=username).first()
    if not user or not user.check_password(password):
        return jsonify({'message': 'Invalid credentials'}), 401
    token = create_access_token(identity=username, additional_claims={'roles': user.get_roles()})
    return token, 200

@app.route('/public/signUp', methods=['POST'])
def signup():
    data = request.get_json()
    try:
        if User.query.filter_by(user_name=data.get('userName')).first(): return 'Taken', 400
        user = User(user_name=data['userName'], email=data['email'], first_name=data.get('firstName', ''), last_name=data.get('lastName', ''), phone=data.get('phone', ''), reg_num=data.get('regNum'), create_at=datetime.now())
        user.set_password(data['password'])
        db.session.add(user)
        db.session.commit()
        return "Saved", 200
    except Exception as e: return str(e), 400

@app.route('/api/auth/verify', methods=['GET'])
@jwt_required()
def verify():
    user = User.query.filter_by(user_name=get_jwt_identity()).first()
    return jsonify({'valid': True, 'userName': user.user_name, 'roles': user.get_roles()}), 200

@app.route('/api/users/<username>', methods=['GET'])
@jwt_required()
def get_user_profile(username):
    user = User.query.filter_by(user_name=username).first()
    return jsonify(user.to_dict()), 200

# ─────────────────────────────────────────────────────────────────────────────
# FOOD & MENU
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/Food/food', methods=['GET'])
def get_menu():
    return jsonify([f.to_dict() for f in Food.query.all()]), 200

@app.route('/Food/food', methods=['POST'])
@jwt_required()
def add_category():
    err = require_admin(); if err: return err
    data = request.get_json()
    f = Food(food_name=data['foodName'], is_available=True)
    db.session.add(f); db.session.commit()
    return "Added", 200

@app.route('/Food/subfood', methods=['POST'])
@jwt_required()
def add_item():
    err = require_admin(); if err: return err
    data = request.get_json()
    f_id = data.get('foodId') or data.get('food', {}).get('id')
    sc = FoodSubCat(food_name=data['foodName'], description=data.get('description', ''), price=float(data['price']), img_url=data.get('imgUrl', ''), is_available=True, veg_or_non_veg=data.get('vegOrNonVeg', 'Veg'), food_id=f_id)
    db.session.add(sc); db.session.commit()
    return "Added", 200

@app.route('/Food/id/<int:id>/<flag>', methods=['PATCH'])
@jwt_required()
def toggle_cat(id, flag):
    err = require_admin(); if err: return err
    f = Food.query.get(id); f.is_available = flag.lower() == 'true'
    db.session.commit(); return jsonify(f.to_dict()), 200

@app.route('/Food/subfood/id/<int:id>/<flag>', methods=['PATCH'])
@jwt_required()
def toggle_item(id, flag):
    err = require_admin(); if err: return err
    s = FoodSubCat.query.get(id); s.is_available = flag.lower() == 'true'
    db.session.commit(); return jsonify(s.to_dict()), 200

@app.route('/Food/subfood/id/<int:id>', methods=['PUT'])
@jwt_required()
def update_item_full(id):
    err = require_admin(); if err: return err
    s = FoodSubCat.query.get(id); data = request.get_json()
    if 'foodName' in data: s.food_name = data['foodName']
    if 'price' in data: s.price = float(data['price'])
    db.session.commit(); return jsonify(s.to_dict()), 200

# ─────────────────────────────────────────────────────────────────────────────
# ORDERS
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/Order', methods=['POST'])
@jwt_required()
def make_order():
    user = User.query.filter_by(user_name=get_jwt_identity()).first()
    data = request.get_json()
    o = Orders(user_id=user.id, local_date_time=datetime.now(), total=float(data.get('totalPrice', 0)))
    db.session.add(o); db.session.flush()
    for item in data.get('orderItems', []):
        oi = OrderItem(quantity=item['quantity'], total_price=float(item['price'])*int(item['quantity']), status='PENDING', order_id=o.id, food_id=item['foodId'])
        db.session.add(oi)
    db.session.commit()
    return jsonify(o.to_dict()), 200

@app.route('/Order/getUserAll', methods=['GET'])
@jwt_required()
def user_orders():
    user = User.query.filter_by(user_name=get_jwt_identity()).first()
    return jsonify([o.to_dict() for o in Orders.query.filter_by(user_id=user.id).order_by(Orders.id.desc()).all()]), 200

@app.route('/Order/getAll', methods=['GET'])
@jwt_required()
def admin_orders():
    err = require_admin(); if err: return err
    return jsonify([o.to_dict() for o in Orders.query.order_by(Orders.id.desc()).all()]), 200

@app.route('/Order/id/<int:id>/<status>', methods=['PATCH'])
@jwt_required()
def update_order(id, status):
    err = require_admin(); if err: return err
    o = Orders.query.get(id)
    for i in o.items: i.status = status.upper()
    db.session.commit(); return jsonify(o.to_dict()), 200

# ─────────────────────────────────────────────────────────────────────────────
# STATIC HANDLER (for non-API paths)
# ─────────────────────────────────────────────────────────────────────────────
@app.errorhandler(404)
def static_proxy(e):
    path = request.path.lstrip('/')
    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return jsonify({'error': 'Not found'}), 404

# ─────────────────────────────────────────────────────────────────────────────
# DB SETUP
# ─────────────────────────────────────────────────────────────────────────────
def init_db():
    db.create_all()
    if not User.query.filter_by(user_name='admin').first():
        admin = User(user_name='admin', first_name='Admin', email='admin@fs.com', roles='["ROLE_USER", "ROLE_ADMIN"]')
        admin.set_password('admin123'); admin.create_at = datetime.now()
        db.session.add(admin); db.session.commit()

_init = False
@app.before_request
def setup():
    global _init
    if not _init:
        try:
            with app.app_context(): init_db()
            _init = True
        except Exception as e: app.logger.error(f"DB Error: {e}")

if __name__ == '__main__':
    with app.app_context(): init_db()
    app.run(host='0.0.0.0', port=8080, debug=True)
