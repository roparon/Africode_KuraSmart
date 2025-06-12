from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models import Vote, Candidate, User

votes_bp = Blueprint('votes', __name__, url_prefix='/api/v1/votes')

@votes_bp.route('/vote', methods=['POST'])
@jwt_required()
def cast_vote():
    voter_id = get_jwt_identity()
    data = request.get_json()
    candidate_id = data.get('candidate_id')

    if not candidate_id:
        return jsonify({'error': 'Candidate ID is required'}), 400

    candidate = Candidate.query.get(candidate_id)
    if not candidate or not candidate.approved:
        return jsonify({'error': 'Candidate not found or not approved'}), 404

    # Prevent double voting per election
    existing_vote = Vote.query.join(Candidate).filter(
        Candidate.election_id == candidate.election_id,
        Vote.voter_id == voter_id
    ).first()

    if existing_vote:
        return jsonify({'error': 'You have already voted in this election'}), 403

    vote = Vote(voter_id=voter_id, candidate_id=candidate_id)
    db.session.add(vote)
    db.session.commit()

    return jsonify({'message': 'Vote cast successfully'}), 201


@votes_bp.route('/results', methods=['GET'])
def get_results():
    election_id = request.args.get('election_id')

    query = db.session.query(
        Candidate.id,
        Candidate.full_name,
        Candidate.position,
        Candidate.party_name,
        db.func.count(Vote.id).label('vote_count')
    ).join(Vote).group_by(Candidate.id)

    if election_id:
        query = query.filter(Candidate.election_id == election_id)

    results = query.all()

    return jsonify([
        {
            'candidate_id': r.id,
            'full_name': r.full_name,
            'position': r.position,
            'party_name': r.party_name,
            'votes': r.vote_count
        } for r in results
    ]), 200
