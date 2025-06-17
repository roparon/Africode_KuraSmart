from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models import VerificationRequest

verification_bp = Blueprint('verification_bp', __name__)

@verification_bp.route('/verify/request', methods=['POST'])
@login_required
def request_verification():
    user = current_user

    if not user:
        return jsonify({'error': 'User not found'}), 404

    if user.is_verified:
        return jsonify({'message': 'User already verified'}), 400

    existing = VerificationRequest.query.filter_by(user_id=user.id).first()
    if existing:
        return jsonify({'message': 'Verification request already submitted'}), 400

    verification = VerificationRequest(user_id=user.id)
    db.session.add(verification)
    db.session.commit()

    return jsonify({'message': 'Verification request submitted'}), 201
