from flask import Flask
from app.extensions import db, migrate, jwt
from app.routes.auth import auth_bp
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

protected_bp = Blueprint('protected_bp', __name__)

@protected_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    user_id = get_jwt_identity()
    return jsonify(message=f'You are logged in as user {user_id}'), 200



def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(protected_bp, url_prefix='/api/v1')

    return app
