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


#get list of election
@elections_bp.route('/elections', methods=['GET'])
def get_elections():
    elections = Election.query.all()

    result = []
    for election in elections:
        result.append({
            'id': election.id,
            'title': election.title,
            'description': election.description,
            'start_date': election.start_date,
            'end_date': election.end_date,
            'is_active': election.is_active
        })

    return jsonify(result), 200

#get by id
@elections_bp.route('/elections/<int:election_id>', methods=['GET'])
def get_election(election_id):
    election = Election.query.get_or_404(election_id)

    return jsonify({
        'id': election.id,
        'title': election.title,
        'description': election.description,
        'start_date': election.start_date,
        'end_date': election.end_date,
        'is_active': election.is_active
    }), 200


#delete/deactivate electio
@elections_bp.route('/elections/<int:election_id>/deactivate', methods=['PATCH'])
@jwt_required()
def deactivate_election(election_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user or user.role != 'admin' or not user.is_verified:
        return jsonify({'error': 'Unauthorized'}), 403

    election = Election.query.get_or_404(election_id)
    election.is_active = False
    db.session.commit()

    return jsonify({'message': 'Election deactivated'}), 200


