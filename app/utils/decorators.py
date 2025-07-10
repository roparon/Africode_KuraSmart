from flask import abort, flash, redirect, url_for
from flask_login import current_user
from functools import wraps


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("You must be logged in to access this page.", "warning")
                return redirect(url_for("web_auth.login"))
            if current_user.role not in roles:
                flash("You do not have permission to access this page.", "danger")
                return redirect(url_for("web_auth.login"))
            return view_func(*args, **kwargs)
        return wrapper
    return decorator


def super_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_super_admin():
            flash("Access restricted to Super Admins.", "danger")
            return redirect(url_for('web_auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("You must be logged in to access this page.", "warning")
            return redirect(url_for('web_auth.login'))

        if not (current_user.is_super_admin() or current_user.is_admin()):
            flash("Access restricted to Admins only.", "danger")
            return redirect(url_for('web_auth.login'))

        return f(*args, **kwargs)
    return decorated_function
