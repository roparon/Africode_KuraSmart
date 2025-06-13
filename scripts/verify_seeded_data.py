import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from app.models import User, Vote, Candidate

app = create_app()

def verify_seeded_data():
    with app.app_context():
        # ✅ Verify Voters
        voters = User.query.filter(User.email.like("voter%@test.com")).all()
        print(f"\n=== Seeded Voters ({len(voters)}) ===")
        for voter in voters:
            print(f"ID: {voter.id}, Email: {voter.email}, Name: {voter.full_name}")

        # ✅ Verify Votes
        votes = Vote.query.all()
        print(f"\n=== Votes ({len(votes)}) ===")
        for vote in votes:
            print(f"Vote ID: {vote.id} | Voter ID: {vote.voter_id} | Candidate ID: {vote.candidate_id}")

        # ✅ Vote Count per Candidate
        print("\n=== Vote Count per Candidate ===")
        candidates = Candidate.query.all()
        for candidate in candidates:
            count = Vote.query.filter_by(candidate_id=candidate.id).count()
            print(f"{candidate.full_name} - {count} votes")


if __name__ == "__main__":
    verify_seeded_data()
