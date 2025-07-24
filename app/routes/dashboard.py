from flask import Blueprint, render_template, abort, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import Election, Position, Candidate
from werkzeug.utils import secure_filename
from app.models import User
from app.forms import ProfileImageForm
from app import db
import os


dashboard_bp = Blueprint('dashboard', __name__)
voter_bp = Blueprint('voter', __name__)

@voter_bp.route('/dashboard', methods=['GET', 'POST'])
@login_required
def voter_dashboard():
    if current_user.role != 'voter':
        abort(403)

    elections = Election.query.order_by(Election.created_at.desc()).all()
    form = ProfileImageForm()

    if form.validate_on_submit():
        image_file = form.image.data
        if image_file:
            from werkzeug.utils import secure_filename
            import os
            filename = secure_filename(image_file.filename)
            upload_path = os.path.join('app', 'static', 'profile_images')
            os.makedirs(upload_path, exist_ok=True)
            image_path = os.path.join(upload_path, filename)
            image_file.save(image_path)

            current_user.profile_image = f'profile_images/{filename}'
            db.session.commit()

            flash("✅ Profile image updated successfully.", "success")
            return redirect(url_for('voter_bp.voter_dashboard'))

    return render_template('voter/dashboard.html',
                           user=current_user,
                           elections=elections,
                           form=form)


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