import os
from dotenv import load_dotenv

load_dotenv()

from flask import Flask
from flask_login import current_user
from flask_apscheduler import APScheduler
from flask_mail import Mail
from app.extensions import db, migrate, login_manager, CSRFProtect, mail
from app.models import User, Notification
from app.tasks.reminders import send_reminders
from config import Config

mail = Mail()

def create_app():
    app = Flask(__name__, template_folder='templates')
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf = CSRFProtect()
    csrf.init_app(app)
    mail.init_app(app)
    

    # APScheduler setup
    scheduler = APScheduler()
    app.config['SCHEDULER_API_ENABLED'] = True
    scheduler.init_app(app)
    scheduler.start()

    scheduler.add_job(
        id='daily_election_reminder',
        func=send_reminders,
        trigger='cron',
        hour=9,
        minute=0,
        timezone=app.config.get('TIMEZONE', 'UTC')
    )

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    login_manager.login_view = 'web_auth.login'
    login_manager.login_message_category = 'info'

    # Register blueprints
    from app.api.auth import auth_bp
    from app.routes.protected import protected_bp
    from app.routes.verification import verification_bp
    from app.routes.elections import elections_bp
    from app.routes.candidates import candidate_bp
    from app.routes.votes import vote_bp
    from app.routes.admin import admin_bp, analytics_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.web_auth import web_auth_bp, voter_bp, admin_web_bp
    from app.routes.main import main_bp
    from app.routes.notifications import notifications_bp
    from app.context_processors import inject_unread_notifs
    from app.routes.voter import voter_bp
    from .routes.static import static_pages

    app.register_blueprint(auth_bp, url_prefix='/api/v1')
    app.register_blueprint(protected_bp, url_prefix='/api/v1')
    app.register_blueprint(verification_bp, url_prefix='/api/v1')
    app.register_blueprint(elections_bp, url_prefix='/api/v1')
    app.register_blueprint(candidate_bp, url_prefix='/api/v1')
    app.register_blueprint(vote_bp, url_prefix='/api/v1')
    app.register_blueprint(admin_bp, url_prefix='/api/v1')
    app.register_blueprint(analytics_bp, url_prefix='/api/v1')

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(web_auth_bp)
    app.register_blueprint(voter_bp)
    app.register_blueprint(admin_web_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(notifications_bp)
    app.context_processor(inject_unread_notifs)
    app.register_blueprint(static_pages)


    @app.context_processor
    def inject_unread_notifs():
        if current_user.is_authenticated:
            count = Notification.query.filter_by(read=False).count()
        else:
            count = 0
        return {'unread_count': count}

    # CLI command registration
    try:
        from app.commands import create_superadmin
        app.cli.add_command(create_superadmin)
    except ImportError:
        pass

    return app
