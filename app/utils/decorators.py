from flask import abort, flash, redirect, url_for
from flask_login import current_user
from functools import wraps

def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                abort(403)
            return view_func(*args, **kwargs)
        return wrapper
    return decorator



def superadmin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_superadmin:
            flash("Access restricted to Super Admins.", "danger")
            return redirect(url_for('web_auth.login'))
        return f(*args, **kwargs)
    return decorated_function
