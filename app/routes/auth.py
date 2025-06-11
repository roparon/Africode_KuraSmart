from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models import User
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

auth_bp = Blueprint('auth_bp', __name__)

# Register
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    email = data.get('email')
    password = data.get('password')
    full_name = data.get('full_name')
    role = data.get('role', 'voter')
    id_number = data.get('id_number')
    username = data.get('username')
    county = data.get('county')
    constituency = data.get('constituency')
    ward = data.get('ward')
    sub_location = data.get('sub_location')

    if not email or not password or not full_name or not (id_number or username):
        return jsonify({'error': 'Missing required fields'}), 400

    if User.query.filter((User.email == email) | (User.id_number == id_number) | (User.username == username)).first():
        return jsonify({'error': 'User already exists'}), 409

    user = User(
        email=email,
        full_name=full_name,
        role=role,
        id_number=id_number,
        username=username,
        county=county,
        constituency=constituency,
        ward=ward,
        sub_location=sub_location
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    return jsonify({
        'id': user.id,
        'email': user.email,
        'full_name': user.full_name,
        'role': user.role,
        'is_verified': user.is_verified
    }), 201

# Login
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid credentials'}), 401

    access_token = create_access_token(identity=user.id)

    return jsonify({
        'access_token': access_token,
        'user': {
            'id': user.id,
            'email': user.email,
            'full_name': user.full_name,
            'role': user.role,
            'is_verified': user.is_verified
        }
    }), 200
