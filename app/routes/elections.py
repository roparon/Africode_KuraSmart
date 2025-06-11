# app/routes/elections.py
from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models import Election, User
from flask_jwt_extended import jwt_required, get_jwt_identity

elections_bp = Blueprint('elections_bp', __name__)

@elections_bp.route('/elections', methods=['POST'])
@jwt_required()
def create_election():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user or user.role != 'admin' or not user.is_verified:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    name = data.get('name')
    description = data.get('description')

    if not name:
        return jsonify({'error': 'Election name required'}), 400

    election = Election(name=name, description=description)
    db.session.add(election)
    db.session.commit()

    return jsonify({'message': 'Election created', 'election_id': election.id}), 201
