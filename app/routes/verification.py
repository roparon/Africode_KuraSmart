from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models import VerificationRequest, User
from flask_jwt_extended import jwt_required, get_jwt_identity

verification_bp = Blueprint('verification_bp', __name__)

@verification_bp.route('/verify/request', methods=['POST'])
@jwt_required()
def request_verification():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    if user.is_verified:
        return jsonify({'message': 'User already verified'}), 400

    existing = VerificationRequest.query.filter_by(user_id=user_id).first()
    if existing:
        return jsonify({'message': 'Verification request already submitted'}), 400

    verification = VerificationRequest(user_id=user_id)
    db.session.add(verification)
    db.session.commit()

    return jsonify({'message': 'Verification request submitted'}), 201
