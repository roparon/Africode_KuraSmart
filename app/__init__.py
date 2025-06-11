from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_security import Security

db = SQLAlchemy()
migrate = Migrate()
security = Security()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    migrate.init_app(app, db)

    from app.models import user_models
    from app.routes import main_routes

    return app
