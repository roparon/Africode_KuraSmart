from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models import Candidate, User, Election

candidates_bp = Blueprint('candidates_bp', __name__)

@candidates_bp.route('/candidates', methods=['POST'])
@jwt_required()
def register_candidate():
    user_id = get_jwt_identity()
    admin = User.query.get(user_id)

    if not admin or admin.role != 'admin' or not admin.is_verified:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    election_id = data.get('election_id')
    full_name = data.get('full_name')
    party_name = data.get('party_name')
    position = data.get('position')
    description = data.get('description')

    if not election_id or not full_name or not position:
        return jsonify({'error': 'Missing required fields'}), 400

    election = Election.query.get(election_id)
    if not election:
        return jsonify({'error': 'Election not found'}), 404

    candidate = Candidate(
        election_id=election_id,
        full_name=full_name,
        party_name=party_name,
        position=position,
        description=description
    )

    db.session.add(candidate)
    db.session.commit()

    return jsonify({'message': 'Candidate registered successfully'}), 201
