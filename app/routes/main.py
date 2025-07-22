from flask import Blueprint, render_template,flash, redirect, url_for
from flask_login import current_user, logout_user


main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        name = current_user.full_name
        logout_user()
        flash(f'{name}, you have been logged out automatically.', 'info')
        return redirect(url_for('main.index'))
    return render_template('index.html')

