import uuid
from datetime import datetime
from enum import Enum

from pydantic import EmailStr
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

    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_by_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )

    # Relationships
    created_by: User = Relationship(back_populates="experiments")


class BatchExperiment(SQLModel, table=True):
    """Stores batch experiment configuration and aggregate status."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=255)
    description: str | None = Field(default=None, max_length=1000)
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
