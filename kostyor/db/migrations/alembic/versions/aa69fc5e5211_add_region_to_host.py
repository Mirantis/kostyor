"""add region to host

Revision ID: aa69fc5e5211
Revises: 278b30622af6
Create Date: 2017-01-16 16:43:16.669423

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'aa69fc5e5211'
down_revision = '278b30622af6'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('hosts') as batch_op:
        batch_op.add_column(
            sa.Column('region', sa.String(255)))


def downgrade():
    with op.batch_alter_table('host') as batch_op:
        batch_op.drop_column('region')
