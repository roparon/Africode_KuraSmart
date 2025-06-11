from flask import Flask
from app.extensions import db, migrate, jwt
from app.routes.auth import auth_bp
from app.models import User

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')

    return app
