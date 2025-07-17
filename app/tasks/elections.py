# from datetime import datetime
# from flask import current_app
# from app.extensions import db
# from app.models import Election
# from sqlalchemy.exc import OperationalError

# def update_election_statuses():
#     with current_app.app_context():
#         now = datetime.utcnow()
#         try:
#             elections = Election.query.all()
#             updated = False

#             for election in elections:
#                 if now < election.start_date:
#                     new_status = 'pending'
#                 elif now > election.end_date:
#                     new_status = 'ended'
#                 else:
#                     new_status = 'active'

#                 if election.current_status != new_status:
#                     election.current_status = new_status
#                     updated = True

#             if updated:
#                 db.session.commit()

#         except OperationalError:
#             db.session.rollback()
#             current_app.logger.warning("[update_election_statuses] DB is locked or busy. Skipping this run.")
#         except Exception as e:
#             db.session.rollback()
#             current_app.logger.error(f"[update_election_statuses] Unexpected error: {e}")
