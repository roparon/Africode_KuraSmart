from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from flask_mail import Mail
from flask_apscheduler import APScheduler



db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
login_manager = LoginManager()
csrf = CSRFProtect()
mail = Mail()
scheduler = APScheduler()


