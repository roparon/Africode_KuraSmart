from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user
from app.models import Election, Position, Candidate

dashboard_bp = Blueprint('dashboard', __name__)
voter_bp = Blueprint('voter', __name__)

@voter_bp.route('/dashboard')
@login_required
def voter_dashboard():
    if current_user.role != 'voter':
        abort(403)
    elections = Election.query.order_by(Election.created_at.desc()).all()
    return render_template('voter/dashboard.html', user=current_user, elections=elections)


@voter_bp.route('/election/<int:election_id>')
@login_required
def view_election(election_id):
    # Fetch the election
    election = Election.query.get_or_404(election_id)

    # Optional: check if election is visible to this voter (based on status or date)
    # Example:
    # if election.start_date > datetime.utcnow():
    #     abort(403)

    # Fetch related data
    candidates = Candidate.query.filter_by(election_id=election_id).all()
    positions = Position.query.filter_by(election_id=election_id).all()

    return render_template(
        'voter/view_election.html',
        election=election,
        candidates=candidates,
        positions=positions,
        user=current_user
    )