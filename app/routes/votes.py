from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Vote, User, Election, Candidate
from app.enums import ElectionStatusEnum
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy.orm import joinedload


vote_bp = Blueprint('vote_bp', __name__, url_prefix='/api/v1/votes')


# Cast a vote
@vote_bp.route('/cast_vote/<int:election_id>', methods=['POST'])
@login_required
def cast_vote(election_id):
    try:
        data = request.get_json()
        candidate_id = data.get('candidate_id')
        if not candidate_id:
            return jsonify({"error": "candidate_id is required"}), 400

        election = Election.query.get_or_404(election_id)
        candidate = Candidate.query.get_or_404(candidate_id)

        if candidate.election_id != election.id:
            return jsonify({"error": "Candidate does not belong to this election"}), 400

        # Get current aware time in Africa/Nairobi
        from app.utils.datetime_utils import ensure_nairobi_aware
        now = ensure_nairobi_aware(datetime.now())

        # Election start and end times
        start_time = ensure_nairobi_aware(election.start_date)
        end_time = ensure_nairobi_aware(election.end_date)

        # Time checks
        if now < start_time:
            return jsonify({"error": "Voting has not started yet"}), 403
        if now > end_time:
            return jsonify({"error": "Voting has ended"}), 403

        # Status check
        if election.status != ElectionStatusEnum.ACTIVE:
            return jsonify({"error": "Election is not currently active"}), 403

        # Duplicate vote check
        existing_vote = Vote.query.filter_by(
            voter_id=current_user.id,
            election_id=election_id,
            position_id=candidate.position_id
        ).first()
        if existing_vote:
            return jsonify({"error": "You have already voted for this position in this election"}), 403

        # Cast vote (no start_date/end_date stored in Vote anymore)
        vote = Vote(
            voter_id=current_user.id,
            election_id=election_id,
            candidate_id=candidate_id,
            position_id=candidate.position_id,
            created_at=datetime.utcnow(),
            timestamp=datetime.utcnow()
        )
        db.session.add(vote)
        db.session.commit()

        return jsonify({"message": "Vote cast successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to cast vote: {str(e)}"}), 500


@vote_bp.route('', methods=['GET'])
@login_required
def list_all_votes():
    if not current_user.is_admin():
        return jsonify({"error": "Admin access required"}), 403

    try:
        voter_id = request.args.get('voter_id', type=int)
        election_id = request.args.get('election_id', type=int)

        query = Vote.query.options(
            joinedload(Vote.candidate),
            joinedload(Vote.election)
        )

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
                "election_title": vote.election.title if vote.election else None,
                "candidate_id": vote.candidate_id,
                "candidate_name": vote.candidate.full_name if vote.candidate else None,
                "timestamp": vote.created_at.isoformat()
            })

        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": f"Failed to list votes: {str(e)}"}), 500



# Get election analytics (admin only)
@vote_bp.route('/analytics/<int:election_id>', methods=['GET'])
@login_required
def election_analytics(election_id):
    if not current_user.is_admin():
        return jsonify({"error": "Admin access required"}), 403
    try:
        total_users = User.query.count()
        total_votes = Vote.query.filter_by(election_id=election_id).count()
        turnout = round((total_votes / total_users) * 100, 2) if total_users > 0 else 0

        return jsonify({
            "election_id": election_id,
            "total_users": total_users,
            "total_votes": total_votes,
            "voter_turnout_percent": turnout
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to get analytics: {str(e)}"}), 500


# Delete a vote (admin only)
@vote_bp.route('/<int:vote_id>', methods=['DELETE'])
@login_required
def delete_vote(vote_id):
    if not current_user.is_admin():
        return jsonify({"error": "Admin access required"}), 403
    try:
        vote = Vote.query.get(vote_id)
        if not vote:
            return jsonify({"error": "Vote not found"}), 404

        db.session.delete(vote)
        db.session.commit()
        return jsonify({"message": "Vote deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to delete vote: {str(e)}"}), 500


# Results grouped by position
@vote_bp.route('/results/by-position/<int:election_id>', methods=['GET'])
@login_required
def get_election_results(election_id):
    try:
        election = Election.query.get(election_id)
        if not election:
            return jsonify({"error": "Election not found"}), 404

        candidates = Candidate.query.filter_by(election_id=election_id, approved=True).all()
        votes = Vote.query.filter_by(election_id=election_id).all()

        positions = {}
        for candidate in candidates:
            if candidate.position not in positions:
                positions[candidate.position] = []

            vote_count = sum(1 for vote in votes if vote.candidate_id == candidate.id)
            total_votes_for_position = sum(
                1 for vote in votes if vote.candidate.position == candidate.position
            )
            percentage = (vote_count / total_votes_for_position * 100) if total_votes_for_position else 0

            positions[candidate.position].append({
                "candidate_id": candidate.id,
                "full_name": candidate.full_name,
                "party_name": candidate.party_name,
                "vote_count": vote_count,
                "percentage": round(percentage, 2)
            })

        return jsonify({
            "election": election.title,
            "results_by_position": positions
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to fetch results by position: {str(e)}"}), 500


# Voter turnout data
@vote_bp.route('/analytics/turnout/<int:election_id>', methods=['GET'])
@login_required
def voter_turnout(election_id):
    if not current_user.is_admin():
        return jsonify({"error": "Admin access only"}), 403
    try:
        election = Election.query.get(election_id)
        if not election:
            return jsonify({"error": "Election not found"}), 404

        total_verified_voters = User.query.filter_by(role="voter", is_verified=True).count()
        unique_voters = Vote.query.filter_by(election_id=election_id).with_entities(Vote.voter_id).distinct().count()
        turnout_percentage = (unique_voters / total_verified_voters * 100) if total_verified_voters else 0

        return jsonify({
            "election": election.title,
            "total_verified_voters": total_verified_voters,
            "voters_who_voted": unique_voters,
            "turnout_percentage": round(turnout_percentage, 2)
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to calculate turnout: {str(e)}"}), 500
