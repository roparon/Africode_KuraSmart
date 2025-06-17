from flask import Flask
from app.extensions import db, migrate, login_manager
from app.models import User
from werkzeug.security import generate_password_hash

def create_app():
    app = Flask(__name__, template_folder='templates')
    app.config.from_object('config.Config')

    # --- Initialize Extensions ---
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # --- Flask-Login Configuration ---
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    login_manager.login_view = 'web_auth.login'
    login_manager.login_message_category = 'info'

    # --- Import Blueprints ---
    from app.api.auth import auth_bp
    from app.routes.protected import protected_bp
    from app.routes.verification import verification_bp
    from app.routes.elections import elections_bp
    from app.routes.candidates import candidate_bp
    from app.routes.votes import vote_bp
    from app.routes.admin import admin_bp, analytics_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.web_auth import web_auth_bp, voter_bp
    from app.routes.main import main_bp
    # from app.routes.super_admin import super_admin_bp

    # --- Register API Blueprints ---
    app.register_blueprint(auth_bp, url_prefix='/api/v1')
    app.register_blueprint(protected_bp, url_prefix='/api/v1')
    app.register_blueprint(verification_bp, url_prefix='/api/v1')
    app.register_blueprint(elections_bp, url_prefix='/api/v1')
    app.register_blueprint(candidate_bp, url_prefix='/api/v1')
    app.register_blueprint(vote_bp, url_prefix='/api/v1')
    app.register_blueprint(admin_bp, url_prefix='/api/v1')
    app.register_blueprint(analytics_bp, url_prefix='/api/v1')
    # app.register_blueprint(super_admin_bp, url_prefix='/api/v1/superadmin')

    # --- Register Web Blueprints ---
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(web_auth_bp)
    app.register_blueprint(voter_bp)
    app.register_blueprint(main_bp)

    try:
        from app.commands import create_superadmin
        app.cli.add_command(create_superadmin)
    except ImportError:
        pass

    return app
