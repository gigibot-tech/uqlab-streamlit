import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import EmailStr
from sqlalchemy import Column, JSON
from sqlmodel import Field, Relationship, SQLModel


# Database model, database table inferred from class name
class User(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)
    hashed_password: str
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)
    experiments: list["UncertaintyExperiment"] = Relationship(
        back_populates="created_by", cascade_delete=True
    )
    batch_experiments: list["BatchExperiment"] = Relationship(
        back_populates="created_by", cascade_delete=True
    )
    # New UQ Benchmarks relationships (Phase 4)
    benchmark_results: list["BenchmarkResult"] = Relationship(cascade_delete=True)
    benchmark_sweeps: list["BenchmarkSweep"] = Relationship(cascade_delete=True)
    # Profile management
    experiment_profiles: list["ExperimentProfile"] = Relationship(
        back_populates="created_by", cascade_delete=True
    )


class Item(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


# Uncertainty Classification Tables


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPLETED_WITH_ERRORS = "completed_with_errors"


class UncertaintyExperiment(SQLModel, table=True):
    """Stores experiment configuration and results."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=255)
    config_yaml: str  # Store full YAML config as text
    status: JobStatus = Field(default=JobStatus.QUEUED)
    progress: float = Field(default=0.0)
    error_message: str | None = Field(default=None, max_length=2000)

    # Results (populated after completion)
    aleatoric_auroc: float | None = None
    epistemic_auroc: float | None = None
    results_path: str | None = Field(default=None, max_length=500)
    best_signals_json: str | None = None  # JSON string with all 7 signals (TEXT type)

    # NOTE: Sweep metadata fields commented out until migration is run
    # To enable Option 1 (explicit sweep grouping), run: alembic upgrade head
    # sweep_group_id: str | None = Field(default=None, max_length=100, index=True)
    # swept_parameter: str | None = Field(default=None, max_length=100)
    # swept_value: str | None = Field(default=None, max_length=100)
    # sweep_index: int | None = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_by_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )

    # Relationships
    created_by: User = Relationship(back_populates="experiments")


class ExperimentProfile(SQLModel, table=True):
    """Stores reusable experiment configuration profiles.
    
    Profiles can be:
    - Paper presets (Fig. 3, Fig. 4, Paired)
    - User-saved custom configurations
    - Templates for quick experiment setup
    """
    __tablename__ = "experimentprofile"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=255, index=True)
    description: str | None = Field(default=None, max_length=1000)
    
    # Workflow configuration (same structure as session_state.workflow)
    # Stores: dataset_config, training_config, uncertainty_config, evaluation_config
    workflow_config: dict = Field(sa_column=Column(JSON))
    
    # Metadata
    is_preset: bool = Field(default=False, index=True)  # True for paper presets
    preset_type: str | None = Field(default=None, max_length=50)  # "fig3_quick", "fig4_full", etc.
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    created_by_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    
    # Relationships
    created_by: User = Relationship(back_populates="experiment_profiles")


class BatchExperiment(SQLModel, table=True):
    """Stores batch experiment configuration and aggregate status."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    method_type: str | None = Field(default="attribution", max_length=50)  # "attribution" or "benchmark"
    base_config_yaml: str
    sweep_definitions_json: str
    status: JobStatus = Field(default=JobStatus.QUEUED)
    progress: float = Field(default=0.0)
    error_message: str | None = Field(default=None, max_length=2000)
    execution_mode: str = Field(default="sequential", max_length=50)
    storage_root: str | None = Field(default=None, max_length=500)
    total_runs: int = Field(default=0)
    completed_runs: int = Field(default=0)
    failed_runs: int = Field(default=0)
    successful_runs: int = Field(default=0)
    current_run_index: int | None = Field(default=None)
    results_summary_json: str | None = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_by_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )

    created_by: User = Relationship(back_populates="batch_experiments")
    runs: list["BatchExperimentRun"] = Relationship(
        back_populates="batch_experiment", cascade_delete=True
    )


class BatchExperimentRun(SQLModel, table=True):
    """Stores a concrete run generated from a batch sweep."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    batch_experiment_id: uuid.UUID = Field(
        foreign_key="batchexperiment.id", nullable=False, ondelete="CASCADE"
    )
    run_index: int = Field(index=True)
    run_name: str = Field(max_length=255)
    status: JobStatus = Field(default=JobStatus.QUEUED)
    progress: float = Field(default=0.0)
    error_message: str | None = Field(default=None, max_length=2000)

    swept_parameter: str = Field(max_length=100)
    swept_value_numeric: float | None = Field(default=None)
    swept_value_text: str = Field(max_length=100)

    resolved_config_yaml: str
    output_dir: str | None = Field(default=None, max_length=500)
    experiment_id: uuid.UUID | None = Field(
        default=None, foreign_key="uncertaintyexperiment.id"
    )

    aleatoric_auroc: float | None = None
    epistemic_auroc: float | None = None
    train_size: int | None = None
    eval_sizes_json: str | None = None
    result_summary_json: str | None = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None

    batch_experiment: BatchExperiment = Relationship(back_populates="runs")


# UQ Benchmarks Tables (New - Phase 4)


class BenchmarkResult(SQLModel, table=True):
    """Stores results from UQ benchmark experiments.
    
    This table stores individual benchmark runs using the new uq_benchmarks package.
    Each result represents a single method evaluation on a specific dataset configuration.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    # Method information
    method: str = Field(max_length=100, index=True)  # e.g., "gaussian_logits", "information_theoretic"
    framework: str = Field(max_length=50)  # "keras" or "pytorch"
    
    # Configuration (stored as JSON for flexibility)
    dataset_config_json: str  # Dataset configuration
    training_config_json: str  # Training hyperparameters
    evaluation_config_json: str  # Evaluation settings
    
    # Results
    accuracy: float
    aleatoric_uncertainty: float
    epistemic_uncertainty: float
    
    # Timing information
    training_time: float  # seconds
    evaluation_time: float  # seconds
    
    # Status tracking
    status: JobStatus = Field(default=JobStatus.COMPLETED)
    error_message: str | None = Field(default=None, max_length=2000)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    
    # User relationship
    created_by_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    created_by: User = Relationship(sa_relationship_kwargs={"overlaps": "benchmark_results"})
    
    # Optional link to sweep
    sweep_id: uuid.UUID | None = Field(
        default=None, foreign_key="benchmarksweep.id", ondelete="CASCADE"
    )
    sweep: Optional["BenchmarkSweep"] = Relationship(back_populates="results")
    
    # Parameter value for sweep (if part of a sweep)
    parameter_value: float | None = Field(default=None)
    
    # wx.gov compatibility fields (optional for backward compatibility)
    training_loss: float | None = None
    risk_level: str | None = Field(default=None, max_length=50)
    use_case: str = Field(default="uncertainty_quantification", max_length=100)
    data_classification: str = Field(default="research", max_length=50)
    wx_gov_model_id: str | None = Field(default=None, max_length=255)
    wx_gov_run_id: str | None = Field(default=None, max_length=255)


class BenchmarkSweep(SQLModel, table=True):
    """Stores parameter sweep experiments for UQ benchmarks.
    
    A sweep runs the same method multiple times with different values
    for a single parameter (e.g., noise_rate, dataset_size).
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    
    # Method and sweep configuration
    method: str = Field(max_length=100, index=True)
    sweep_parameter: str = Field(max_length=100)  # e.g., "noise_rate", "under_train_per_class"
    sweep_values_json: str  # JSON array of parameter values
    
    # Base configuration (non-swept parameters)
    base_config_json: str
    
    # Aggregate status
    status: JobStatus = Field(default=JobStatus.QUEUED)
    progress: float = Field(default=0.0)
    total_runs: int = Field(default=0)
    completed_runs: int = Field(default=0)
    failed_runs: int = Field(default=0)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    
    # User relationship
    created_by_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    created_by: User = Relationship(sa_relationship_kwargs={"overlaps": "benchmark_sweeps"})
    
    # Results relationship
    results: list["BenchmarkResult"] = Relationship(
        back_populates="sweep", cascade_delete=True
    )

# Made with Bob
