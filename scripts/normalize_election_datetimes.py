from app import create_app
from app.extensions import db
from app.models import Election
from zoneinfo import ZoneInfo

def normalize_election_datetimes():
    app = create_app()
    with app.app_context():
        elections = Election.query.all()
        changed_count = 0
        for e in elections:
            changed = False
            if e.start_date and e.start_date.tzinfo is None:
                e.start_date = e.start_date.replace(tzinfo=ZoneInfo('UTC'))
                changed = True
            if e.end_date and e.end_date.tzinfo is None:
                e.end_date = e.end_date.replace(tzinfo=ZoneInfo('UTC'))
                changed = True
            if changed:
                db.session.add(e)
                changed_count += 1
        if changed_count:
            db.session.commit()
        print(f'Normalized {changed_count} election datetimes.')

if __name__ == "__main__":
    normalize_election_datetimes()
