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
