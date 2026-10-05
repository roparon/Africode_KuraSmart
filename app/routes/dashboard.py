from flask import Blueprint, render_template, abort, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import Election, Position, Candidate
from app.models import User
from app.forms.profile_form import ProfileImageForm
from app import db
from app.services.storage import upload_image, delete_object, is_cloud_key


dashboard_bp = Blueprint('dashboard', __name__)
voter_bp = Blueprint('voter', __name__)

@voter_bp.route('/dashboard', methods=['GET', 'POST'])
@login_required
def voter_dashboard():
    if current_user.role != 'voter':
        abort(403)

    # Load elections and form
    elections = Election.query.order_by(Election.created_at.desc()).all()
    form = ProfileImageForm()

    # Handle image upload if submitted
    if request.method == 'POST' and form.validate_on_submit():
        image_file = form.image.data

        if image_file:
            old_profile_image = current_user.profile_image

            profile_key = upload_image(
                image_file,
                "profiles",
                max_size=(600, 600),
                quality=80,
            )

            current_user.profile_image = profile_key
            db.session.commit()

            # Remove the previous cloud image only after the database update succeeds.
            if old_profile_image and is_cloud_key(old_profile_image):
                try:
                    delete_object(old_profile_image)
                except Exception as cleanup_error:
                    from flask import current_app
                    current_app.logger.warning(
                        f"Could not delete old profile image: {cleanup_error}"
                    )

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