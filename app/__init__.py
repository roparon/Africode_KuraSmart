from flask import Flask
from app.extensions import db, migrate, jwt
from app.models import User

def create_app():
    app = Flask(__name__,  template_folder='templates')
    app.config.from_object('config.Config')

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    from app.api.auth import auth_bp
    from app.routes.protected import protected_bp
    from app.routes.verification import verification_bp
    from app.routes.elections import elections_bp
    from app.routes.candidates import candidate_bp
    from app.routes.votes import vote_bp
    from app.routes.admin import admin_bp




    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(protected_bp, url_prefix='/api/v1')
    app.register_blueprint(verification_bp, url_prefix='/api/v1')
    app.register_blueprint(elections_bp, url_prefix='/api/v1')
    app.register_blueprint(candidate_bp)
    app.register_blueprint(vote_bp)
    app.register_blueprint(admin_bp)




    return app
