"""Add audit fields to election

Revision ID: 616a96e9d822
Revises: e74b9b67a6a1
Create Date: 2025-06-12 11:13:03.477418

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '616a96e9d822'
down_revision = 'e74b9b67a6a1'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('election', schema=None) as batch_op:
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('deactivated_by', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            constraint_name='fk_deactivated_by_user',  # <- must be named explicitly
            referent_table='user',
            local_cols=['deactivated_by'],
            remote_cols=['id']
        )


    # ### end Alembic commands ###

def downgrade():
    with op.batch_alter_table('election', schema=None) as batch_op:
        batch_op.drop_constraint('fk_deactivated_by_user', type_='foreignkey')
        batch_op.drop_column('deactivated_by')
        batch_op.drop_column('updated_at')



    # ### end Alembic commands ###
