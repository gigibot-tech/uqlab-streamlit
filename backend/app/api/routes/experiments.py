"""Experiment management and execution endpoints."""

import json
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from app.core.security import get_password_hash
from app.tables import JobStatus, UncertaintyExperiment, User

router = APIRouter()

# Helper to get or create a default user for testing
def get_or_create_test_user(session: Session) -> User:
    """Get or create a test user for local development."""
    test_email = "test@example.com"
    user = session.exec(select(User).where(User.email == test_email)).first()
    if not user:
        user = User(
            email=test_email,
            hashed_password=get_password_hash("test_password"),
            is_active=True,
            is_superuser=False,
            full_name="Test User"
        )
        session.add(user)
        session.commit()
        session.refresh(user)
    return user

# Path to the ML script
DTAG_ROOT = Path(__file__).resolve().parents[6] / "Desktop" / "GigiApps" / "dtag"
ML_SCRIPT = DTAG_ROOT / "experiments" / "run_fast_uncertainty_classification.py"


class ExperimentConfig(BaseModel):
    """Experiment configuration matching YAML structure."""

    # Data parameters
    noise_type: str = "worse_label"
    under_supported_classes: str = "3,5"
    under_train_per_class: int = 50
    regular_train_per_class: int = 300
    eval_per_group: int = 600

    # Model parameters
    dinov2_model: str = "small"
    hidden_dim: int = 256
    dropout: float = 0.2

    # Training parameters
    epochs: int = 12
    learning_rate: float = 0.001
    weight_decay: float = 0.0001
    train_batch_size: int = 256

    # Evaluation parameters
    mc_passes: int = 20
    attribution_method: str = "dualxda"


class ExperimentCreate(BaseModel):
    """Request to create a new experiment."""

    name: str = Field(min_length=1, max_length=255)
    config: ExperimentConfig


class ExperimentResponse(BaseModel):
    """Experiment response."""

    id: uuid.UUID
    name: str
    status: JobStatus
    progress: float
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None
    aleatoric_auroc: float | None
    epistemic_auroc: float | None
    results_path: str | None


# In-memory storage for no-auth experiments (no database required)
_mock_experiments: dict[str, dict] = {}

@router.post("/no-auth", response_model=ExperimentResponse)
async def create_experiment_no_auth(
    experiment: ExperimentCreate,
) -> Any:
    """Create experiment without authentication or database (for local testing)."""
    exp_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    mock_exp = {
        "id": exp_id,
        "name": experiment.name,
        "status": JobStatus.QUEUED,
        "progress": 0.0,
        "created_at": now.isoformat(),
        "started_at": None,
        "completed_at": None,
        "error_message": None,
        "aleatoric_auroc": None,
        "epistemic_auroc": None,
        "results_path": None,
    }
    
    _mock_experiments[exp_id] = mock_exp
    return mock_exp


@router.post("", response_model=ExperimentResponse)
async def create_experiment(
    experiment: ExperimentCreate,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Create a new experiment configuration."""
    return await _create_experiment_impl(experiment, session, current_user)


async def _create_experiment_impl(
    experiment: ExperimentCreate,
    session: Session,
    user: User,
) -> Any:
    """Implementation of experiment creation."""
    # Convert config to YAML
    config_dict = {
        "seed": 42,
        "device": "auto",
        "data": {
            "noise_type": experiment.config.noise_type,
            "under_supported_classes": experiment.config.under_supported_classes,
            "under_train_per_class": experiment.config.under_train_per_class,
            "regular_train_per_class": experiment.config.regular_train_per_class,
            "eval_per_group": experiment.config.eval_per_group,
        },
        "model": {
            "dinov2_model": experiment.config.dinov2_model,
            "hidden_dim": experiment.config.hidden_dim,
            "dropout": experiment.config.dropout,
        },
        "training": {
            "epochs": experiment.config.epochs,
            "learning_rate": experiment.config.learning_rate,
            "weight_decay": experiment.config.weight_decay,
            "train_batch_size": experiment.config.train_batch_size,
            "feature_batch_size": 64,
        },
        "evaluation": {
            "mc_passes": experiment.config.mc_passes,
            "top_k": 10,
        },
        "paths": {
            "cifar10n_root": "./data/cifar10n",
            "feature_cache_dir": "./cache/fast_uncertainty_classification/features",
            "results_base_dir": "./results",
        },
    }

    config_yaml = yaml.dump(config_dict, default_flow_style=False)

    # Create experiment record
    db_experiment = UncertaintyExperiment(
        name=experiment.name,
        config_yaml=config_yaml,
        created_by_id=user.id,
    )
    session.add(db_experiment)
    session.commit()
    session.refresh(db_experiment)

    return db_experiment


@router.get("/no-auth", response_model=list[ExperimentResponse])
async def list_experiments_no_auth(
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """List all experiments without authentication or database (for local testing)."""
    experiments = list(_mock_experiments.values())
    return experiments[skip:skip+limit]


@router.get("", response_model=list[ExperimentResponse])
async def list_experiments(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """List all experiments for the current user."""
    return await _list_experiments_impl(session, current_user, skip, limit)


async def _list_experiments_impl(
    session: Session,
    user: User,
    skip: int,
    limit: int,
) -> Any:
    """Implementation of list experiments."""
    statement = (
        select(UncertaintyExperiment)
        .where(UncertaintyExperiment.created_by_id == user.id)
        .offset(skip)
        .limit(limit)
    )
    experiments = session.exec(statement).all()
    return experiments


@router.get("/{experiment_id}", response_model=ExperimentResponse)
async def get_experiment(
    experiment_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Get experiment details."""
    experiment = session.get(UncertaintyExperiment, experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    if experiment.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return experiment


@router.post("/{experiment_id}/start")
async def start_experiment(
    experiment_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> dict[str, Any]:
    """Start experiment execution."""
    experiment = session.get(UncertaintyExperiment, experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    if experiment.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if experiment.status == JobStatus.RUNNING:
        raise HTTPException(status_code=400, detail="Experiment already running")

    # Create temporary config file
    config_path = Path(f"/tmp/experiment_{experiment_id}.yaml")
    config_path.write_text(experiment.config_yaml)

    # Update status
    experiment.status = JobStatus.RUNNING
    experiment.started_at = datetime.utcnow()
    experiment.progress = 0.0
    session.add(experiment)
    session.commit()

    # Start ML script in background (simplified - in production use Celery)
    try:
        # For now, just validate the script exists
        if not ML_SCRIPT.exists():
            raise HTTPException(
                status_code=500,
                detail=f"ML script not found at {ML_SCRIPT}",
            )

        # In production, this would be:
        # task = run_ml_experiment.delay(str(experiment_id), str(config_path))
        # For now, return success
        return {
            "id": experiment_id,
            "status": "running",
            "message": "Experiment started (background execution not yet implemented)",
        }
    except Exception as e:
        experiment.status = JobStatus.FAILED
        experiment.error_message = str(e)
        session.add(experiment)
        session.commit()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{experiment_id}")
async def delete_experiment(
    experiment_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> dict[str, str]:
    """Delete an experiment."""
    experiment = session.get(UncertaintyExperiment, experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    if experiment.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    session.delete(experiment)
    session.commit()
    return {"message": "Experiment deleted"}

# Made with Bob
