from datetime import datetime

def update_election_statuses():
    # Delayed import to avoid circular import
    from app import create_app, db
    from app.models import Election

    app = create_app()

    with app.app_context():
        now = datetime.utcnow()
        elections = Election.query.all()

        for election in elections:
            if now < election.start_date:
                new_status = 'pending'
            elif now > election.end_date:
                new_status = 'ended'
            else:
                new_status = 'active'

            if election.current_status != new_status:
                election.current_status = new_status

        db.session.commit()


