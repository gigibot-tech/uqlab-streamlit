"""Experiment management and execution endpoints."""

import logging
import traceback
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.api.deps import CurrentUser, SessionDep
from app.core.security import get_password_hash
from app.domain.models import TrainingConfig
from app.repositories.experiment_repository import ExperimentRepository
from app.services.executors.subprocess_executor import SubprocessExecutor
from app.services.training_orchestrator import TrainingOrchestrator
from app.tables import JobStatus, UncertaintyExperiment, User

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter()

# Path to the ML script
ML_SCRIPT = Path(__file__).resolve().parents[6] / "Desktop" / "GigiApps" / "dtag" / "experiments" / "run_fast_uncertainty_classification.py"

# Global orchestrator instance (in production, use dependency injection)
_orchestrator: TrainingOrchestrator | None = None


def get_orchestrator(session: SessionDep) -> TrainingOrchestrator:
    """Get or create training orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        executor = SubprocessExecutor(ML_SCRIPT)
        repository = ExperimentRepository(session)
        _orchestrator = TrainingOrchestrator(executor, repository)
    return _orchestrator


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
            full_name="Test User",
        )
        session.add(user)
        session.commit()
        session.refresh(user)
    return user


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
    """Create experiment (will auto-start via Streamlit)."""
    exp_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    # Store config as dict
    config_dict = experiment.config.model_dump()
    
    mock_exp = {
        "id": exp_id,
        "name": experiment.name,
        "config_yaml": config_dict,
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


@router.post("/no-auth/{experiment_id}/start")
async def start_experiment_no_auth(experiment_id: str, session: SessionDep) -> dict:
    """Start real ML training for no-auth experiment with enterprise-grade error handling."""
    logger.info(f"Starting experiment {experiment_id}")
    
    # Validate experiment_id format
    try:
        experiment_uuid = uuid.UUID(experiment_id)
    except ValueError as e:
        logger.error(f"Invalid experiment ID format: {experiment_id}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"Invalid experiment ID format: {experiment_id}. Must be a valid UUID."
        )
    
    # Check if experiment exists in mock data
    if experiment_id not in _mock_experiments:
        logger.warning(f"Experiment not found: {experiment_id}")
        raise HTTPException(
            status_code=404,
            detail=f"Experiment not found: {experiment_id}"
        )
    
    mock_exp = _mock_experiments[experiment_id]
    logger.debug(f"Found mock experiment: {mock_exp.get('name', 'Unknown')}")
    
    # Validate ML script exists before proceeding
    if not ML_SCRIPT.exists():
        error_msg = f"ML script not found at {ML_SCRIPT}"
        logger.error(error_msg)
        raise HTTPException(
            status_code=500,
            detail=f"Configuration error: {error_msg}. Please check ML_SCRIPT path configuration."
        )
    
    try:
        # Get or create test user
        logger.debug("Getting or creating test user")
        user = get_or_create_test_user(session)
        logger.info(f"Using user: {user.email} (ID: {user.id})")
        
    except Exception as e:
        logger.error("Failed to get or create test user", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Database error: Failed to get or create test user. {str(e)}"
        )
    
    try:
        # Parse and validate config
        logger.debug("Parsing experiment configuration")
        config_yaml_raw = mock_exp.get("config_yaml", "{}")
        
        if isinstance(config_yaml_raw, str):
            config_dict = yaml.safe_load(config_yaml_raw)
        else:
            config_dict = config_yaml_raw
        
        if not isinstance(config_dict, dict):
            config_dict = {}
            logger.warning(f"Invalid config format for experiment {experiment_id}, using empty config")
        
        config_yaml = yaml.dump(config_dict) if config_dict else "{}"
        logger.debug(f"Parsed config: {len(config_yaml)} bytes")
        
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse YAML configuration for experiment {experiment_id}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"Invalid YAML configuration: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error parsing configuration for experiment {experiment_id}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Configuration parsing error: {str(e)}"
        )
    
    try:
        # Create database experiment from mock
        logger.debug(f"Creating database experiment with ID: {experiment_uuid}")
        db_experiment = UncertaintyExperiment(
            id=experiment_uuid,
            name=mock_exp["name"],
            config_yaml=config_yaml,
            created_by_id=user.id,
            status=JobStatus.QUEUED,
        )
        session.add(db_experiment)
        session.commit()
        session.refresh(db_experiment)
        logger.info(f"Database experiment created successfully: {db_experiment.id}")
        
    except Exception as e:
        logger.error(
            f"Failed to create database experiment {experiment_id}",
            exc_info=True,
            extra={
                "experiment_id": experiment_id,
                "user_id": user.id if user else None,
                "traceback": traceback.format_exc()
            }
        )
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error: Failed to create experiment record. {str(e)}"
        )
    
    try:
        # Initialize orchestrator and start training
        logger.info(f"Initializing training orchestrator for experiment {experiment_id}")
        orchestrator = get_orchestrator(session)
        
        logger.info(f"Starting training for experiment {experiment_id}")
        await orchestrator.start_training(experiment_uuid)
        
        logger.info(f"Training started successfully for experiment {experiment_id}")
        return {
            "id": experiment_id,
            "status": "running",
            "message": "Real ML training started successfully"
        }
        
    except FileNotFoundError as e:
        logger.error(
            f"File not found error while starting training for experiment {experiment_id}",
            exc_info=True,
            extra={
                "experiment_id": experiment_id,
                "ml_script": str(ML_SCRIPT),
                "traceback": traceback.format_exc()
            }
        )
        raise HTTPException(
            status_code=500,
            detail=f"File system error: Required file not found. {str(e)}"
        )
        
    except PermissionError as e:
        logger.error(
            f"Permission error while starting training for experiment {experiment_id}",
            exc_info=True,
            extra={
                "experiment_id": experiment_id,
                "ml_script": str(ML_SCRIPT),
                "traceback": traceback.format_exc()
            }
        )
        raise HTTPException(
            status_code=500,
            detail=f"Permission error: Insufficient permissions to execute training. {str(e)}"
        )
        
    except ValueError as e:
        logger.error(
            f"Validation error while starting training for experiment {experiment_id}",
            exc_info=True,
            extra={
                "experiment_id": experiment_id,
                "traceback": traceback.format_exc()
            }
        )
        raise HTTPException(
            status_code=400,
            detail=f"Validation error: Invalid training parameters. {str(e)}"
        )
        
    except Exception as e:
        logger.error(
            f"Unexpected error while starting training for experiment {experiment_id}",
            exc_info=True,
            extra={
                "experiment_id": experiment_id,
                "experiment_name": mock_exp.get("name", "Unknown"),
                "user_id": user.id if user else None,
                "ml_script": str(ML_SCRIPT),
                "error_type": type(e).__name__,
                "traceback": traceback.format_exc()
            }
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start training: {type(e).__name__}: {str(e)}. Check server logs for details."
        )


@router.post("/no-auth/{experiment_id}/simulate-progress")
async def simulate_progress_no_auth(experiment_id: str) -> dict:
    """Simulate experiment progress (for testing UI)."""
    if experiment_id not in _mock_experiments:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    exp = _mock_experiments[experiment_id]
    
    # Simulate progress
    if exp["status"] == JobStatus.QUEUED:
        exp["status"] = JobStatus.RUNNING
        exp["started_at"] = datetime.utcnow().isoformat()
        exp["progress"] = 0.2
    elif exp["status"] == JobStatus.RUNNING:
        current_progress = exp.get("progress", 0.0)
        if current_progress < 0.9:
            exp["progress"] = min(current_progress + 0.15, 0.95)
        else:
            # Complete the experiment
            exp["status"] = JobStatus.COMPLETED
            exp["progress"] = 1.0
            exp["completed_at"] = datetime.utcnow().isoformat()
            exp["aleatoric_auroc"] = 0.85 + (hash(experiment_id) % 10) / 100  # Mock AUROC
            exp["epistemic_auroc"] = 0.82 + (hash(experiment_id) % 15) / 100
    
    return exp


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
    """Start real ML training execution."""
    experiment = session.get(UncertaintyExperiment, experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    if experiment.created_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if experiment.status == JobStatus.RUNNING:
        raise HTTPException(status_code=400, detail="Experiment already running")

    if not ML_SCRIPT.exists():
        raise HTTPException(status_code=500, detail=f"ML script not found at {ML_SCRIPT}")

    try:
        # Get orchestrator and start training asynchronously
        orchestrator = get_orchestrator(session)
        await orchestrator.start_training(experiment_id)
        
        return {
            "id": str(experiment_id),
            "status": "running",
            "message": "Real ML training started successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start training: {str(e)}")


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
