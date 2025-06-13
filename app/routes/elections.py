from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models import Election, User, Candidate, Vote
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime



elections_bp = Blueprint('elections_bp', __name__)
vote_bp = Blueprint('vote_bp', __name__, url_prefix='/api/v1/votes')


@elections_bp.route('/elections', methods=['POST'])
@jwt_required()
def create_election():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user or user.role != 'admin' or not user.is_verified:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    start_date = data.get('start_date')
    end_date = data.get('end_date')

    if not title or not start_date or not end_date:
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'}), 400

    election = Election(
        title=title,
        description=description,
        start_date=start_dt,
        end_date=end_dt
    )
    db.session.add(election)
    db.session.commit()

    return jsonify({'message': 'Election created', 'election_id': election.id}), 201

# update election
@elections_bp.route('/elections/<int:election_id>', methods=['PUT'])
@jwt_required()
def update_election(election_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user or user.role != 'admin' or not user.is_verified:
        return jsonify({'error': 'Unauthorized'}), 403

    election = Election.query.get_or_404(election_id)

    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    start_date = data.get('start_date')
    end_date = data.get('end_date')

    if title:
        election.title = title
    if description is not None:
        election.description = description
    if start_date:
        try:
            election.start_date = datetime.fromisoformat(start_date)
        except ValueError:
            return jsonify({'error': 'Invalid start_date format'}), 400
    if end_date:
        try:
            election.end_date = datetime.fromisoformat(end_date)
        except ValueError:
            return jsonify({'error': 'Invalid end_date format'}), 400
    db.session.commit()
    return jsonify({'message': 'Election updated'}), 200



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
    election.deactivated_by = user.id
    db.session.commit()

    return jsonify({'message': 'Election deactivated'}), 200

@vote_bp.route('/results/<int:election_id>', methods=['GET'])
@jwt_required()
def get_election_results(election_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "Unauthorized"}), 403

    election = Election.query.get(election_id)
    if not election:
        return jsonify({"error": "Election not found"}), 404

    # Optional: Prevent results before end of election
    if election.end_date and election.end_date > datetime.utcnow():
        return jsonify({"error": "Results not available until the election ends."}), 403

    # Count votes grouped by candidate
    results = (
        db.session.query(Candidate.id, Candidate.full_name, Candidate.position, db.func.count(Vote.id).label('vote_count'))
        .join(Vote, Candidate.id == Vote.candidate_id)
        .filter(Vote.election_id == election_id)
        .group_by(Candidate.id)
        .order_by(db.desc('vote_count'))
        .all()
    )

    data = []
    for candidate_id, name, position, vote_count in results:
        data.append({
            "candidate_id": candidate_id,
            "name": name,
            "position": position,
            "vote_count": vote_count
        })

    return jsonify({
        "election": election.title,
        "results": data
    }), 200



