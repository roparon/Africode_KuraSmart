"""Final fix for formal/informal voter fields

Revision ID: 30efe22869d9
Revises: 1520a12cc8e1
Create Date: 2025-06-27 12:18:11.594681

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '30efe22869d9'
down_revision = '1520a12cc8e1'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('voting_type', sa.String(length=10), nullable=False, server_default='informal'))
        batch_op.add_column(sa.Column('national_id', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('dob', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('gender', sa.String(length=10), nullable=True))
        batch_op.add_column(sa.Column('sub_county', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('division', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('location', sa.String(length=100), nullable=True))
        batch_op.create_unique_constraint('uq_users_national_id', ['national_id'])
        batch_op.drop_column('constituency')
        batch_op.drop_column('ward')
        batch_op.drop_column('id_number')


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('id_number', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('ward', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('constituency', sa.String(length=100), nullable=True))
        batch_op.drop_constraint('uq_users_national_id', type_='unique')
        batch_op.drop_column('location')
        batch_op.drop_column('division')
        batch_op.drop_column('sub_county')
        batch_op.drop_column('gender')
        batch_op.drop_column('dob')
        batch_op.drop_column('national_id')
        batch_op.drop_column('voting_type')
