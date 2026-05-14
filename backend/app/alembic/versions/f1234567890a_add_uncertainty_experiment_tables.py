"""add_uncertainty_experiment_tables

Revision ID: f1234567890a
Revises: d98dd8ec85a3
Create Date: 2026-05-13 06:09:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f1234567890a'
down_revision = '1a31ce608336'
branch_labels = None
depends_on = None


def upgrade():
    # Create uncertaintyexperiment table
    op.create_table(
        'uncertaintyexperiment',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('config_yaml', sa.Text(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('progress', sa.Float(), nullable=False),
        sa.Column('error_message', sa.String(length=2000), nullable=True),
        sa.Column('aleatoric_auroc', sa.Float(), nullable=True),
        sa.Column('epistemic_auroc', sa.Float(), nullable=True),
        sa.Column('results_path', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_by_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['created_by_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('uncertaintyexperiment')

# Made with Bob
