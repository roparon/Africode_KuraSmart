from app import create_app, db
from app.models import User, UserRole
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    existing = User.query.filter_by(role=UserRole.super_admin).first()
    if not existing:
        super_admin = User(
            email='aaronrop40@gmail.com',
            full_name='Aron Rop',
            username='roparon',
            role=UserRole.super_admin,
            password_hash=generate_password_hash('0987654321'),
            is_verified=True,
            is_superadmin=True
        )
        db.session.add(super_admin)
        db.session.commit()
        print("Super admin created successfully.")
    else:
        print("⚠️ Super admin already exists.")


        super_admin = User(
    full_name="Aron Rop",
    username="roparon",
    email="aaronrop40@gmail.com",
    password_hash=generate_password_hash("0987654321"),
    role=UserRole.super_admin,
    is_verified=True,
    is_superadmin=True
)
