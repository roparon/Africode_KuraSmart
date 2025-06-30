from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import Election

dashboard_bp = Blueprint('dashboard', __name__)
voter_bp = Blueprint('voter', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

@voter_bp.route('/dashboard')
@login_required
def voter_dashboard():
    elections = Election.query.order_by(Election.created_at.desc()).all()
    return render_template('voter/dashboard.html', user=current_user, elections=elections)

