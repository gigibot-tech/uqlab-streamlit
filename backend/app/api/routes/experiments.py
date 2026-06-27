"""Experiment management and execution endpoints."""

import logging
import traceback
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlmodel import Session, select, desc

from app.api.deps import CurrentUser, SessionDep
from app.core.runtime_paths import experiment_results_dir
from app.core.security import get_password_hash
from app.domain.models import TrainingConfig, TrainingPresetName
from app.repositories.experiment_repository import ExperimentRepository
from app.services.executors.direct_executor import DirectExecutor
from app.services.run_recovery_service import RunRecoveryService
from app.services.training_orchestrator import TrainingOrchestrator
from app.tables import JobStatus, UncertaintyExperiment, User

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter()

# Global executor instance (stateless, can be reused)
_executor: DirectExecutor | None = None


def get_orchestrator(session: SessionDep) -> TrainingOrchestrator:
    """Get or create training orchestrator with fresh session."""
    global _executor
    if _executor is None:
        _executor = DirectExecutor()
    
    # Always create fresh repository with current session
    repository = ExperimentRepository(session)
    return TrainingOrchestrator(_executor, repository)


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


class ExperimentCreate(BaseModel):
    """Request to create a new experiment."""

    name: str = Field(min_length=1, max_length=255)
    preset: TrainingPresetName | None = None
    # Nested (Streamlit) or flat dict — parsed via TrainingConfig.from_legacy_flat_dict.
    # Do NOT type this as flat TrainingConfig: Pydantic would drop nested `data`/`model`.
    config: dict[str, Any] | None = None


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
    best_signals_json: str | None = None  # JSON string with all 7 signals


@router.post("/no-auth", response_model=ExperimentResponse)
async def create_experiment_no_auth(
    experiment: ExperimentCreate,
    session: SessionDep,
) -> Any:
    """Create experiment in database (no authentication required for local testing)."""
    # Get or create test user
    user = get_or_create_test_user(session)
    
    # Use the same implementation as authenticated endpoint
    return await _create_experiment_impl(experiment, session, user)


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
    if experiment.preset is not None:
        training_config = TrainingConfig.preset_config(experiment.preset)
        config_yaml = yaml.dump(training_config.to_yaml_dict(), default_flow_style=False)
    elif experiment.config is not None:
        try:
            import importlib

            import uqlab_orchestrator.run_spec as run_spec

            # run_spec lives outside backend/; reload so edits apply without full server restart.
            importlib.reload(run_spec)
            run_spec.validate_run_yaml(experiment.config)
            config_yaml = yaml.dump(experiment.config, default_flow_style=False)
        except ImportError:
            training_config = TrainingConfig.from_legacy_flat_dict(experiment.config)
            config_yaml = yaml.dump(training_config.to_yaml_dict(), default_flow_style=False)
        except run_spec.RunSpecError as exc:
            logger.warning(
                "Experiment create rejected (invalid run config): name=%r user_id=%s — %s",
                experiment.name,
                user.id,
                exc,
            )
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    else:
        logger.warning(
            "Experiment create rejected (missing body): name=%r user_id=%s — no preset or config",
            experiment.name,
            user.id,
        )
        raise HTTPException(
            status_code=400,
            detail="Provide either `preset` or `config` when creating an experiment.",
        )

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
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """List all experiments from database (no authentication required for local testing)."""
    # Query database for all experiments
    statement = select(UncertaintyExperiment).offset(skip).limit(limit).order_by(desc(UncertaintyExperiment.created_at))
    experiments = session.exec(statement).all()
    return experiments


class RecoverabilityResponse(BaseModel):
    """Per-experiment recoverability assessment."""

    id: str
    name: str
    status: str
    error_message: str | None
    tier: str
    missing: list[str] = Field(default_factory=list)
    zwischen_stages: list[str] = Field(default_factory=list)
    error_hint: str | None = None


class RecoverBatchRequest(BaseModel):
    """Batch recovery filter."""

    status: str = "failed"
    tier: str = "zwischen_finalize"
    seed: int = 42
    device: str = "cpu"


@router.get("/no-auth/recoverability", response_model=list[RecoverabilityResponse])
async def list_recoverability_no_auth(
    session: SessionDep,
    status: str | None = None,
    skip: int = 0,
    limit: int = 500,
) -> Any:
    """Scan experiments and classify disk recoverability."""
    service = RunRecoveryService(session)
    job_status = JobStatus(status) if status else None
    entries = service.list_recoverability(status=job_status, skip=skip, limit=limit)
    return [entry.to_dict() for entry in entries]


@router.post("/no-auth/recover-batch")
async def recover_batch_no_auth(
    body: RecoverBatchRequest,
    session: SessionDep,
) -> dict[str, Any]:
    """Recover all experiments matching status + tier."""
    service = RunRecoveryService(session)
    try:
        job_status = JobStatus(body.status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid status: {body.status}") from exc
    result = service.recover_batch(
        status=job_status,
        tier=body.tier,  # type: ignore[arg-type]
        seed=body.seed,
        device=body.device,
    )
    return result.to_dict()


@router.get("/no-auth/{experiment_id}/recoverability", response_model=RecoverabilityResponse)
async def get_recoverability_no_auth(
    experiment_id: str,
    session: SessionDep,
) -> Any:
    """Assess recoverability for a single experiment."""
    try:
        experiment_uuid = uuid.UUID(experiment_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid experiment ID format") from exc

    experiment = session.get(UncertaintyExperiment, experiment_uuid)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    service = RunRecoveryService(session)
    return service.assess_experiment(experiment).to_dict()


@router.post("/no-auth/{experiment_id}/recover")
async def recover_experiment_no_auth(
    experiment_id: str,
    session: SessionDep,
    tier: str | None = None,
    seed: int = 42,
    device: str = "cpu",
) -> dict[str, Any]:
    """Finalize a failed run from disk artifacts and update the database."""
    try:
        experiment_uuid = uuid.UUID(experiment_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid experiment ID format") from exc

    service = RunRecoveryService(session)
    try:
        return service.recover_experiment(
            experiment_uuid,
            tier=tier,  # type: ignore[arg-type]
            seed=seed,
            device=device,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Recovery failed for %s", experiment_id, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Recovery failed: {exc}") from exc


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
    
    # Check if experiment exists in database
    db_experiment = session.get(UncertaintyExperiment, experiment_uuid)
    if not db_experiment:
        logger.warning(f"Experiment not found in database: {experiment_id}")
        raise HTTPException(
            status_code=404,
            detail=f"Experiment not found: {experiment_id}"
        )
    
    logger.debug(f"Found experiment in database: {db_experiment.name}")

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
        # Config is already stored as YAML string in database
        logger.debug("Using experiment configuration from database")
        config_yaml = db_experiment.config_yaml
        logger.debug(f"Config: {len(config_yaml)} bytes")
        
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
        # Check if experiment already exists in database
        existing_experiment = session.get(UncertaintyExperiment, experiment_uuid)
        
        if not existing_experiment:
            # Create database experiment from request fallback
            logger.debug(f"Creating database experiment with ID: {experiment_uuid}")
            existing_experiment = UncertaintyExperiment(
                id=experiment_uuid,
                name=f"experiment_{experiment_id}",
                config_yaml=config_yaml,
                created_by_id=user.id,
                status=JobStatus.QUEUED,
            )
            session.add(existing_experiment)
            session.commit()
            session.refresh(existing_experiment)
            logger.info(f"Database experiment created successfully: {existing_experiment.id}")
        else:
            logger.info(f"Experiment {experiment_uuid} already exists in database, using existing record")
        
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
                "runner": "uqlab.runner.execute.run_from_yaml",
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
                "runner": "uqlab.runner.execute.run_from_yaml",
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
                "experiment_name": db_experiment.name,
                "user_id": user.id if user else None,
                "runner": "uqlab.runner.execute.run_from_yaml",
                "error_type": type(e).__name__,
                "traceback": traceback.format_exc()
            }
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start training: {type(e).__name__}: {str(e)}. Check server logs for details."
        )

@router.get("/no-auth/{experiment_id}/log")
async def get_experiment_log_no_auth(experiment_id: str) -> FileResponse:
    """Download the full stdout/stderr log for one experiment run."""
    try:
        experiment_uuid = uuid.UUID(experiment_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid experiment ID format") from e

    log_path = experiment_results_dir(experiment_uuid) / "experiment.log"
    if not log_path.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"No experiment log at {log_path}. Training may not have started yet.",
        )

    return FileResponse(
        log_path,
        media_type="text/plain; charset=utf-8",
        filename=f"{experiment_id}.log",
    )


@router.delete("/no-auth/{experiment_id}")
async def delete_experiment_no_auth(experiment_id: str, session: SessionDep) -> dict:
    """Delete an experiment (no authentication required for development)."""
    try:
        experiment_uuid = uuid.UUID(experiment_id)
        repository = ExperimentRepository(session)
        
        deleted = repository.delete(experiment_uuid)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Experiment not found")
        
        logger.info(f"Experiment deleted: {experiment_id}")
        return {"message": "Experiment deleted successfully", "id": experiment_id}
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid experiment ID format")
    except Exception as e:
        logger.error(f"Failed to delete experiment {experiment_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete experiment: {str(e)}")



# Removed simulate-progress endpoint - using real progress from ML training


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


@router.get("/no-auth/{experiment_id}", response_model=ExperimentResponse)
async def get_experiment_no_auth(
    experiment_id: str,
    session: SessionDep,
) -> Any:
    """Get experiment details (no authentication required for local testing)."""
    try:
        experiment_uuid = uuid.UUID(experiment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid experiment ID format")
    
    experiment: UncertaintyExperiment | None = session.get(UncertaintyExperiment, experiment_uuid)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return experiment


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
