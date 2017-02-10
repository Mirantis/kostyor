"""Service <-> Host => Many-to-Many

Revision ID: 232c38fec944
Revises: 278b30622af6
Create Date: 2017-02-15 17:59:35.264989

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '232c38fec944'
down_revision = '278b30622af6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'hosts_services',
        sa.Column('host_id', sa.String(36), sa.ForeignKey('hosts.id')),
        sa.Column('service_id', sa.String(36), sa.ForeignKey('services.id')),
        sa.UniqueConstraint('host_id', 'service_id'))

    with op.batch_alter_table('services') as batch_op:
        batch_op.drop_constraint('fk_services_host_id_hosts')
        batch_op.drop_column('host_id')


def downgrade():
    op.add_column(
        'services',
        sa.Column('host_id', sa.String(36), sa.ForeignKey('hosts.id')))
    op.drop_table('hosts_services')
