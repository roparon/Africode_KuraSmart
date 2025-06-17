from flask import Flask
from app.extensions import db, migrate, jwt, login_manager
from app.models import User, Candidate, Position, Election, Vote, VerificationRequest


def create_app():
    app = Flask(__name__, template_folder='templates')
    app.config.from_object('config.Config')

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    login_manager.init_app(app)

    # Login manager setup
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    login_manager.login_view = 'web_auth.login'
    login_manager.login_message_category = 'info'

    # Blueprint imports
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

    # Register blueprints

    # --- API v1 (RESTful) ---
    app.register_blueprint(auth_bp, url_prefix='/api/v1')
    app.register_blueprint(protected_bp, url_prefix='/api/v1')
    app.register_blueprint(verification_bp, url_prefix='/api/v1')
    app.register_blueprint(elections_bp, url_prefix='/api/v1')
    app.register_blueprint(candidate_bp, url_prefix='/api/v1')
    app.register_blueprint(vote_bp, url_prefix='/api/v1')
    app.register_blueprint(admin_bp, url_prefix='/api/v1')
    app.register_blueprint(analytics_bp, url_prefix='/api/v1')
    # app.register_blueprint(super_admin_bp, url_prefix='/api/v1/superadmin')  # Uncomment if using Super Admin routes

    # --- Web or non-API blueprints ---
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(web_auth_bp)
    app.register_blueprint(voter_bp)
    app.register_blueprint(main_bp)

    return app
