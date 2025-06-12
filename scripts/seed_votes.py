import random
from datetime import datetime
from app import create_app
from app.extensions import db
from app.models import User, Candidate, Election, Vote

app = create_app()

def seed_votes():
    with app.app_context():
        # Sample elections
        election = Election.query.first()
        if not election:
            print("No elections found.")
            return

        # Get candidates
        candidates = Candidate.query.filter_by(election_id=election.id, approved=True).all()
        if not candidates:
            print("No approved candidates found.")
            return

        # Create test voters
        for i in range(10):
            email = f"voter{i}@test.com"
            user = User.query.filter_by(email=email).first()
            if not user:
                user = User(
                    name=f"Test Voter {i}",
                    email=email,
                    password="test123",  # Already hashed in real scenario
                    role="voter",
                    is_verified=True
                )
                db.session.add(user)
                db.session.flush()

            for position in set(c.position for c in candidates):
                eligible_candidates = [c for c in candidates if c.position == position]
                chosen = random.choice(eligible_candidates)

                if not Vote.query.filter_by(voter_id=user.id, election_id=election.id, candidate_id=chosen.id).first():
                    vote = Vote(
                        voter_id=user.id,
                        election_id=election.id,
                        candidate_id=chosen.id,
                        created_at=datetime.utcnow()
                    )
                    db.session.add(vote)

        db.session.commit()
        print("✅ Demo votes seeded successfully.")

if __name__ == "__main__":
    seed_votes()
