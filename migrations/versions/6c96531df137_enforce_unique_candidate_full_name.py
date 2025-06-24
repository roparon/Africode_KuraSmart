"""Enforce unique candidate full_name

Revision ID: 6c96531df137
Revises: 863df0368456
Create Date: 2025-06-24 10:44:44.239981

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6c96531df137'
down_revision = '863df0368456'
branch_labels = None
depends_on = None



from alembic import op
import sqlalchemy as sa

def upgrade():
    with op.batch_alter_table('candidate', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_candidate_full_name', ['full_name'])

def downgrade():
    with op.batch_alter_table('candidate', schema=None) as batch_op:
        batch_op.drop_constraint('uq_candidate_full_name', type_='unique')


    # ### end Alembic commands ###



