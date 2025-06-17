import click
from flask.cli import with_appcontext
from app.extensions import db
from app.models import User
from werkzeug.security import generate_password_hash

@click.command('create-superadmin')
@with_appcontext
def create_superadmin():
    if not User.query.filter_by(role='super_admin').first():
        admin = User(
            full_name='Super Admin',
            email='superadmin@example.com',
            username='superadmin',
            id_number='00000000',
            role='super_admin',
            is_verified=True,
            password_hash=generate_password_hash('supersecurepassword')
        )
        db.session.add(admin)
        db.session.commit()
        click.echo('✅ Superadmin created.')
    else:
        click.echo('⚠️ Superadmin already exists.')
