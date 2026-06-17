"""add experiment profiles table

Revision ID: add_experiment_profiles
Revises: add_sweep_metadata_to_experiments
Create Date: 2026-06-15 21:26:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = 'add_experiment_profiles'
down_revision = 'add_sweep_metadata_to_experiments'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create experiment_profiles table for saving/loading configurations."""
    op.create_table(
        'experimentprofile',
        sa.Column('id', sa.UUID(), nullable=False, default=uuid.uuid4),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('workflow_config', sa.JSON(), nullable=False),
        sa.Column('is_preset', sa.Boolean(), nullable=False, default=False),
        sa.Column('preset_type', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('created_by_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['created_by_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better query performance
    op.create_index('ix_experimentprofile_name', 'experimentprofile', ['name'])
    op.create_index('ix_experimentprofile_is_preset', 'experimentprofile', ['is_preset'])


def downgrade() -> None:
    """Drop experiment_profiles table."""
    op.drop_index('ix_experimentprofile_is_preset', table_name='experimentprofile')
    op.drop_index('ix_experimentprofile_name', table_name='experimentprofile')
    op.drop_table('experimentprofile')

# Made with Bob
