from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User, Election, Candidate, Vote
from app.extensions import db
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__, url_prefix='/api/v1/admin')
analytics_bp = Blueprint('analytics_bp', __name__, url_prefix='/api/v1/analytics')

# ---- Utility ----
def is_admin(user):
    return user and user.role in ['admin', 'super_admin']


# ---- Admin Overview ----
@admin_bp.route('/overview', methods=['GET'])
@jwt_required()
def admin_overview():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not is_admin(user):
        return jsonify({'error': 'Unauthorized'}), 403

    stats = {
        "total_users": User.query.count(),
        "verified_users": User.query.filter_by(is_verified=True).count(),
        "total_elections": Election.query.count(),
        "total_candidates": Candidate.query.count(),
        "total_votes": Vote.query.count()
    }

    return jsonify(stats), 200


# ---- Election Analytics ----
@admin_bp.route('/elections/<int:election_id>/analytics', methods=['GET'])
@jwt_required()
def election_analytics(election_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not is_admin(user):
        return jsonify({'error': 'Unauthorized'}), 403

    election = Election.query.get(election_id)
    if not election:
        return jsonify({'error': 'Election not found'}), 404

    total_candidates = Candidate.query.filter_by(election_id=election_id).count()
    total_votes = Vote.query.filter_by(election_id=election_id).count()
    total_voters = User.query.filter_by(is_verified=True).count()
    turnout_percentage = (total_votes / total_voters * 100) if total_voters else 0

    # Leading candidate
    leading_candidate = (
        db.session.query(Candidate, func.count(Vote.id).label('vote_count'))
        .join(Vote)
        .filter(Candidate.election_id == election_id)
        .group_by(Candidate.id)
        .order_by(func.count(Vote.id).desc())
        .first()
    )

    leader = {
        'id': leading_candidate[0].id,
        'full_name': leading_candidate[0].full_name,
        'party_name': leading_candidate[0].party_name,
        'position': leading_candidate[0].position,
        'votes': leading_candidate[1]
    } if leading_candidate else None

    return jsonify({
        'election': {
            'id': election.id,
            'title': election.title,
            'start_date': election.start_date,
            'end_date': election.end_date
        },
        'candidates': total_candidates,
        'total_votes': total_votes,
        'total_voters': total_voters,
        'turnout_percentage': round(turnout_percentage, 2),
        'leading_candidate': leader
    }), 200


# ---- Get All Votes ----
@admin_bp.route('/votes', methods=['GET'])
@jwt_required()
def get_all_votes():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not is_admin(user):
        return jsonify({'error': 'Unauthorized'}), 403

    election_id = request.args.get('election_id')
    voter_id = request.args.get('voter_id')

    query = Vote.query
    if election_id:
        query = query.filter_by(election_id=election_id)
    if voter_id:
        query = query.filter_by(voter_id=voter_id)

    votes = query.order_by(Vote.created_at.desc()).all()

    vote_data = [{
        'vote_id': vote.id,
        'voter': {
            'id': vote.voter.id,
            'name': vote.voter.full_name,
            'email': vote.voter.email
        },
        'candidate': {
            'id': vote.candidate.id,
            'name': vote.candidate.full_name,
            'position': vote.candidate.position,
            'party': vote.candidate.party_name
        },
        'election': {
            'id': vote.election.id,
            'title': vote.election.title
        },
        'voted_at': vote.created_at.isoformat()
    } for vote in votes]

    return jsonify(vote_data), 200


# ---- Voter Turnout Analytics (admin-only) ----
@admin_bp.route('/analytics/turnout/<int:election_id>', methods=['GET'])
@jwt_required()
def voter_turnout_analytics(election_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not is_admin(user):
        return jsonify({'error': 'Admin access required'}), 403

    election = Election.query.get(election_id)
    if not election:
        return jsonify({'error': 'Election not found'}), 404

    total_voters = User.query.filter_by(is_verified=True).count()
    total_voted = Vote.query.filter_by(election_id=election_id).count()

    turnout_percentage = (
        (total_voted / total_voters) * 100 if total_voters > 0 else 0
    )

    return jsonify({
        "election_id": election.id,
        "election_title": election.title,
        "total_voters": total_voters,
        "total_voted": total_voted,
        "turnout_percentage": round(turnout_percentage, 2)
    }), 200


# ---- Analytics Route (duplicate functionality, can be merged) ----
@analytics_bp.route('/turnout/<int:election_id>', methods=['GET'])
@jwt_required()
def election_turnout(election_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not is_admin(user):
        return jsonify({"error": "Admin access required"}), 403

    election = Election.query.get(election_id)
    if not election:
        return jsonify({"error": "Election not found"}), 404

    total_voters = User.query.filter_by(role='voter', is_verified=True).count()
    total_votes = Vote.query.filter_by(election_id=election_id).count()

    turnout = (total_votes / total_voters * 100) if total_voters > 0 else 0.0

    return jsonify({
        "election_id": election_id,
        "total_voters": total_voters,
        "total_votes_cast": total_votes,
        "turnout_percentage": round(turnout, 2)
    }), 200
