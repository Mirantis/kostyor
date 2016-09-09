"""Initial database schema

Revision ID: 2bedb47d68e6
Revises: initial
Create Date: 2016-09-09 11:02:40.083013

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2bedb47d68e6'
down_revision = None
branch_labels = None
depends_on = None

STATUSES = ['READY FOR UPGRADE', 'UPGRADE IN PROGRESS', 'UPGRADE PAUSED',
            'UPGRADE ERROR', 'UPGRADE CANCELLED', 'NOT READY FOR UPGRADE',
            'UPGRADE ROLLBACK IN PROGRESS']

VERSIONS = ['liberty', 'mitaka', 'newton', 'unknown']


def upgrade():
    op.create_table(
        'clusters',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('version', sa.Enum(*VERSIONS)),
        sa.Column('status', sa.Enum(*STATUSES)),
        sa.Column('name', sa.String(255)),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'hosts',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('hostname', sa.String(255)),
        sa.Column('cluster_id', sa.String(36), nullable=False),
        sa.ForeignKeyConstraint(['cluster_id'], ['clusters.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'services',
        sa.Column('name', sa.String(255)),
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('host_id', sa.String(36), nullable=False),
        sa.Column('version', sa.Enum(*VERSIONS)),
        sa.ForeignKeyConstraint(['host_id'], ['hosts.id']),
        sa.PrimaryKeyConstraint('id')

    )

    op.create_table(
        'upgrade_tasks',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('upgrade_start_time', sa.DateTime),
        sa.Column('upgrade_end_time', sa.DateTime),
        sa.Column('cluster_id', sa.String(36), nullable=False),
        sa.Column('from_version', sa.Enum(*VERSIONS)),
        sa.Column('to_version', sa.Enum(*VERSIONS)),
        sa.ForeignKeyConstraint(['cluster_id'], ['clusters.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'service_upgrade_records',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('service_id', sa.String(36), nullable=False),
        sa.Column('upgrade_task_id', sa.String(36), nullable=False),
        sa.Column('status', sa.Enum(*STATUSES)),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['service_id'], ['services.id']),
        sa.ForeignKeyConstraint(['upgrade_task_id'], ['upgrade_tasks.id']),
    )


def downgrade():
    pass
