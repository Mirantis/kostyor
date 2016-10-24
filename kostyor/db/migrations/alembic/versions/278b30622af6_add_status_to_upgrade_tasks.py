"""Add status to upgrade_tasks

Revision ID: 278b30622af6
Revises: 2bedb47d68e6
Create Date: 2016-10-20 13:30:12.669445

"""

from alembic import op
import sqlalchemy as sa

from kostyor.common import constants


# revision identifiers, used by Alembic.
revision = '278b30622af6'
down_revision = '2bedb47d68e6'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('upgrade_tasks') as batch_op:
        batch_op.add_column(
            sa.Column('status', sa.Enum(*constants.UPGRADE_STATUSES)))


def downgrade():
    with op.batch_alter_table('upgrade_tasks') as batch_op:
        batch_op.drop_column('status')
