from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models import User
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, create_refresh_token
from werkzeug.security import generate_password_hash

auth_bp = Blueprint('auth_bp', __name__, url_prefix='/api/v1/auth')

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

    # Generate both access and refresh tokens
    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': {
            'id': user.id,
            'email': user.email,
            'full_name': user.full_name,
            'role': user.role,
            'is_verified': user.is_verified
        }
    }), 200


# Refresh token route
@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh_token():
    user_id = get_jwt_identity()
    new_access_token = create_access_token(identity=user_id)
    return jsonify(access_token=new_access_token), 200




# Get current user profile
@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'id': user.id,
        'email': user.email,
        'full_name': user.full_name,
        'role': user.role,
        'is_verified': user.is_verified,
        'id_number': user.id_number,
        'username': user.username,
        'county': user.county,
        'constituency': user.constituency,
        'ward': user.ward,
        'sub_location': user.sub_location,
        'created_at': user.created_at.isoformat()
    }), 200



@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'id': user.id,
        'email': user.email,
        'full_name': user.full_name,
        'role': user.role,
        'is_verified': user.is_verified,
        'id_number': user.id_number,
        'username': user.username,
        'county': user.county,
        'constituency': user.constituency,
        'ward': user.ward,
        'sub_location': user.sub_location
    }), 200



@auth_bp.route('/me', methods=['PUT'])
@jwt_required()
def update_profile():
    from app.models import User
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()

    # Update allowed fields
    if 'full_name' in data:
        user.full_name = data['full_name']
    if 'password' in data:
        user.password_hash = generate_password_hash(data['password'])
    if 'county' in data:
        user.county = data['county']
    if 'constituency' in data:
        user.constituency = data['constituency']
    if 'ward' in data:
        user.ward = data['ward']
    if 'sub_location' in data:
        user.sub_location = data['sub_location']

    db.session.commit()

    return jsonify({
        'id': user.id,
        'email': user.email,
        'full_name': user.full_name,
        'role': user.role,
        'is_verified': user.is_verified,
        'id_number': user.id_number,
        'username': user.username,
        'county': user.county,
        'constituency': user.constituency,
        'ward': user.ward,
        'sub_location': user.sub_location
    }), 200

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    return jsonify({"message": "Logged out successfully."}), 200



#temporary route for listing emails
@auth_bp.route('/dev/users', methods=['GET'])
def list_users():
    users = User.query.all()
    return jsonify([
        {"id": user.id, "email": user.email, "full_name": user.full_name}
        for user in users
    ])

