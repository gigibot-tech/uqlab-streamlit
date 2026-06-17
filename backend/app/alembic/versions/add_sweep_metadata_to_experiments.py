"""add sweep metadata to experiments

Revision ID: add_sweep_metadata
Revises: f1234567890a
Create Date: 2026-06-15 20:20:00.000000

This migration adds sweep grouping fields to the UncertaintyExperiment table
to support explicit sweep metadata (Option 1 from SWEEP_GROUPING_IMPLEMENTATION.md).

Fields added:
- sweep_group_id: Unique identifier for the sweep (e.g., "sweep_20240615_143022")
- swept_parameter: Name of the parameter being swept (e.g., "mc_passes", "learning_rate")
- swept_value: String representation of the parameter value for this experiment
- sweep_index: Position in the sweep (0, 1, 2, ...) for sorting

These fields enable:
1. Script-generated sweeps to be explicitly linked
2. UI to query and group experiments by sweep_group_id
3. Proper ordering and visualization of sweep results
4. Backward compatibility (all fields are nullable)
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_sweep_metadata'
down_revision = 'f1234567890a'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add sweep metadata fields to uncertaintyexperiment table.
    """
    # Add sweep_group_id column
    op.add_column(
        'uncertaintyexperiment',
        sa.Column('sweep_group_id', sa.String(length=100), nullable=True)
    )
    
    # Add swept_parameter column
    op.add_column(
        'uncertaintyexperiment',
        sa.Column('swept_parameter', sa.String(length=100), nullable=True)
    )
    
    # Add swept_value column
    op.add_column(
        'uncertaintyexperiment',
        sa.Column('swept_value', sa.String(length=100), nullable=True)
    )
    
    # Add sweep_index column
    op.add_column(
        'uncertaintyexperiment',
        sa.Column('sweep_index', sa.Integer(), nullable=True)
    )
    
    # Create index on sweep_group_id for efficient querying
    op.create_index(
        'ix_uncertaintyexperiment_sweep_group_id',
        'uncertaintyexperiment',
        ['sweep_group_id'],
        unique=False
    )
    
    # Create composite index for sweep queries
    op.create_index(
        'ix_uncertaintyexperiment_sweep_composite',
        'uncertaintyexperiment',
        ['sweep_group_id', 'sweep_index'],
        unique=False
    )


def downgrade():
    """
    Remove sweep metadata fields from uncertaintyexperiment table.
    """
    # Drop indexes
    op.drop_index('ix_uncertaintyexperiment_sweep_composite', table_name='uncertaintyexperiment')
    op.drop_index('ix_uncertaintyexperiment_sweep_group_id', table_name='uncertaintyexperiment')
    
    # Drop columns
    op.drop_column('uncertaintyexperiment', 'sweep_index')
    op.drop_column('uncertaintyexperiment', 'swept_value')
    op.drop_column('uncertaintyexperiment', 'swept_parameter')
    op.drop_column('uncertaintyexperiment', 'sweep_group_id')

# Made with Bob
