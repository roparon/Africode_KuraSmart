import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import random
from datetime import datetime
from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models import Vote, User, Election, Candidate

app = create_app()

def seed_votes():
    with app.app_context():
        # Get the first election
        election = Election.query.first()
        if not election:
            print("No elections found.")
            return

        # Get approved candidates for that election
        candidates = Candidate.query.filter_by(election_id=election.id, approved=True).all()
        if not candidates:
            print("No approved candidates found.")
            return

        for i in range(10):
            email = f"voter{i}@test.com"
            user = User.query.filter_by(email=email).first()
            if not user:
                user = User(
                    full_name=f"Test Voter {i}",
                    email=email,
                    role="voter"
                )
                user.set_password("password123")
                db.session.add(user)
                db.session.flush()  # To get user.id

            # Randomly choose a candidate
            chosen = random.choice(candidates)

            # Ensure no duplicate vote
            existing_vote = Vote.query.filter_by(
                voter_id=user.id,
                election_id=election.id,
                candidate_id=chosen.id
            ).first()

            if not existing_vote:
                vote = Vote(
                    voter_id=user.id,
                    election_id=election.id,
                    candidate_id=chosen.id
                )
                db.session.add(vote)

        db.session.commit()
        print("Seeding completed: 10 voters voted.")

if __name__ == "__main__":
    seed_votes()
