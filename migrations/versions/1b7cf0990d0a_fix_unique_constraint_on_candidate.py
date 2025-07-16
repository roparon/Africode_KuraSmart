"""Fix unique constraint on candidate

Revision ID: 1b7cf0990d0a
Revises: d8237ff5d49d
Create Date: 2025-07-16 21:53:22.453774

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1b7cf0990d0a'
down_revision = 'd8237ff5d49d'
branch_labels = None
depends_on = None


def upgrade():
    # Remove the unique constraint from (user_id, election_id)
    with op.batch_alter_table('candidate', schema=None) as batch_op:
        batch_op.drop_constraint('unique_candidate_combination', type_='unique')


def downgrade():
    # Re-add the unique constraint on (user_id, election_id)
    with op.batch_alter_table('candidate', schema=None) as batch_op:
        batch_op.create_unique_constraint('unique_candidate_combination', ['user_id', 'election_id'])
