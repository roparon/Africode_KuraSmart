def check_if_user_has_voted(user, election_id):
    from app.models import Vote
    return Vote.query.filter_by(user_id=user.id, election_id=election_id).first() is not None
