from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Candidate, User, Election

candidate_bp = Blueprint('candidates', __name__, url_prefix='/api/v1/candidates')


@candidate_bp.route('', methods=['POST'])
@login_required
def register_candidate():
    if not current_user.is_admin() or not current_user.is_verified:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    election_id = data.get('election_id')
    full_name = data.get('full_name')
    party_name = data.get('party_name')
    position = data.get('position')
    description = data.get('description')
    manifesto = data.get('manifesto')

    if not election_id or not full_name or not position:
        return jsonify({'error': 'Missing required fields'}), 400

    election = Election.query.get(election_id)
    if not election:
        return jsonify({'error': 'Election not found'}), 404

    candidate = Candidate(
        user_id=current_user.id,
        election_id=election_id,
        full_name=full_name,
        party_name=party_name,
        position=position,
        description=description,
        manifesto=manifesto
    )

    db.session.add(candidate)
    db.session.commit()

    return jsonify({'message': 'Candidate registered successfully'}), 201


@candidate_bp.route('/<int:candidate_id>/approve', methods=['POST'])
@login_required
def approve_candidate(candidate_id):
    if not current_user.is_admin() or not current_user.is_verified:
        return jsonify({"error": "Unauthorized"}), 403

    candidate = Candidate.query.get(candidate_id)
    if not candidate:
        return jsonify({"message": "Candidate not found"}), 404

    candidate.approved = True
    db.session.commit()
    return jsonify({"message": "Candidate approved successfully"}), 200


@candidate_bp.route('', methods=['GET'])
def list_candidates():
    election_id = request.args.get('election_id')
    approved = request.args.get('approved')

    query = Candidate.query

    if election_id:
        query = query.filter_by(election_id=election_id)
    if approved is not None:
        query = query.filter_by(approved=(approved.lower() == 'true'))

    candidates = query.all()
    return jsonify([c.to_dict() for c in candidates]), 200


@candidate_bp.route('/<int:candidate_id>', methods=['GET'])
def get_candidate(candidate_id):
    candidate = Candidate.query.get(candidate_id)
    if not candidate:
        return jsonify({'error': 'Candidate not found'}), 404
    return jsonify(candidate.to_dict()), 200
