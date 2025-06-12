from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models import Vote, User, Election, Candidate
from datetime import datetime

vote_bp = Blueprint('vote_bp', __name__, url_prefix='/api/v1/votes')


@vote_bp.route('', methods=['POST'])
@jwt_required()
def cast_vote():
    user_id = get_jwt_identity()
    data = request.get_json()
    election_id = data.get('election_id')
    candidate_id = data.get('candidate_id')

    if not election_id or not candidate_id:
        return jsonify({"error": "election_id and candidate_id are required"}), 400

    # Check if election and candidate exist
    election = Election.query.get(election_id)
    candidate = Candidate.query.get(candidate_id)

    if not election or not candidate:
        return jsonify({"error": "Invalid election or candidate"}), 404

    # Prevent duplicate vote
    existing_vote = Vote.query.filter_by(voter_id=user_id, election_id=election_id).first()
    if existing_vote:
        return jsonify({"error": "You have already voted in this election"}), 403

    vote = Vote(
        voter_id=user_id,
        election_id=election_id,
        candidate_id=candidate_id,
        created_at=datetime.utcnow()
    )
    db.session.add(vote)
    db.session.commit()
    return jsonify({"message": "Vote cast successfully"}), 201


@vote_bp.route('/results/<int:election_id>', methods=['GET'])
def get_results(election_id):
    election = Election.query.get(election_id)
    if not election:
        return jsonify({"error": "Election not found"}), 404

    candidates = Candidate.query.filter_by(election_id=election_id).all()
    results = []
    for candidate in candidates:
        vote_count = Vote.query.filter_by(candidate_id=candidate.id).count()
        results.append({
            "candidate_id": candidate.id,
            "full_name": candidate.full_name,
            "party_name": candidate.party_name,
            "vote_count": vote_count
        })

    return jsonify({"election_id": election_id, "results": results}), 200


@vote_bp.route('', methods=['GET'])
@jwt_required()
def list_all_votes():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or user.role != 'admin':
        return jsonify({"error": "Admin access required"}), 403

    # Optional filters
    voter_id = request.args.get('voter_id', type=int)
    election_id = request.args.get('election_id', type=int)

    query = Vote.query

    if voter_id:
        query = query.filter_by(voter_id=voter_id)
    if election_id:
        query = query.filter_by(election_id=election_id)

    votes = query.all()
    results = []
    for vote in votes:
        results.append({
            "vote_id": vote.id,
            "voter_id": vote.voter_id,
            "election_id": vote.election_id,
            "candidate_id": vote.candidate_id,
            "timestamp": vote.created_at.isoformat()
        })

    return jsonify(results), 200



@vote_bp.route('/<int:vote_id>', methods=['DELETE'])
@jwt_required()
def delete_vote(vote_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or user.role != 'admin':
        return jsonify({"error": "Admin access required"}), 403

    vote = Vote.query.get(vote_id)
    if not vote:
        return jsonify({"error": "Vote not found"}), 404

    db.session.delete(vote)
    db.session.commit()
    return jsonify({"message": "Vote deleted successfully"}), 200


@vote_bp.route('/analytics/<int:election_id>', methods=['GET'])
@jwt_required()
def election_analytics(election_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or user.role != 'admin':
        return jsonify({"error": "Admin access required"}), 403

    total_users = User.query.count()
    total_votes = Vote.query.filter_by(election_id=election_id).count()

    turnout = round((total_votes / total_users) * 100, 2) if total_users > 0 else 0

    return jsonify({
        "election_id": election_id,
        "total_users": total_users,
        "total_votes": total_votes,
        "voter_turnout_percent": turnout
    }), 200


@vote_bp.route('/<int:vote_id>', methods=['DELETE'])
@jwt_required()
def delete_vote(vote_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or user.role != 'admin':
        return jsonify({"error": "Admin access required"}), 403

    vote = Vote.query.get(vote_id)
    if not vote:
        return jsonify({"error": "Vote not found"}), 404

    db.session.delete(vote)
    db.session.commit()
    return jsonify({"message": "Vote deleted successfully"}), 200
