"""Batch experiment management endpoints."""

import uuid
from pathlib import Path
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.api.deps import SessionDep
from app.core.db import engine
from app.core.security import get_password_hash
from app.domain.models import TrainingConfig, TrainingPresetName
from app.repositories.batch_experiment_repository import BatchExperimentRepository
from app.services.batch_experiment_service import (
    BatchExperimentService,
    MlflowStyleBatchExperimentTracker,
    SweepDefinition,
    SweepRangeDefinition,
)
from app.services.executors.direct_executor import DirectExecutor
from app.tables import BatchExperiment, JobStatus, User
from app.api.routes.experiments import ML_SCRIPT


router = APIRouter()

_batch_service: BatchExperimentService | None = None


def get_batch_service() -> BatchExperimentService:
    """Get or create a reusable batch experiment service."""
    global _batch_service
    if _batch_service is None:
        _batch_service = BatchExperimentService(
            DirectExecutor(ML_SCRIPT),
            tracker=MlflowStyleBatchExperimentTracker(),
        )
    return _batch_service

# Type alias for dependency injection
BatchExperimentServiceDep = Annotated[BatchExperimentService, Depends(get_batch_service)]


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


class SweepRangeRequest(BaseModel):
    """Range specification for a sweep."""

    start: float
    end: float
    step: float


class BatchSweepDefinitionRequest(BaseModel):
    """Request payload for a single-parameter sweep."""

    parameter: str = Field(min_length=1, max_length=100)
    value_type: str = Field(pattern="^(int|float)$")
    range: SweepRangeRequest


class BatchExperimentCreate(BaseModel):
    """Request to create a batch experiment."""

    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    preset: TrainingPresetName | None = None
    base_config: TrainingConfig | None = None
    sweep_definitions: list[BatchSweepDefinitionRequest] = Field(min_length=1, max_length=1)
    auto_start: bool = True


class BatchRunResponse(BaseModel):
    """Summary response for a generated run."""

    run_index: int
    run_name: str
    status: JobStatus
    swept_parameter: str
    swept_value: float | None
    aleatoric_auroc: float | None = None
    epistemic_auroc: float | None = None
    error_message: str | None = None


class BatchExperimentResponse(BaseModel):
    """Response model for batch experiment status."""

    id: uuid.UUID
    name: str
    description: str | None
    status: JobStatus
    progress: float
    created_at: Any
    started_at: Any | None
    completed_at: Any | None
    current_run_index: int | None
    total_runs: int
    completed_runs: int
    successful_runs: int
    failed_runs: int
    storage_root: str | None
    error_message: str | None
    sweep_definitions: list[dict[str, Any]]


@router.post("", response_model=BatchExperimentResponse)
async def create_batch_experiment(
    payload: BatchExperimentCreate,
    session: SessionDep,
) -> Any:
    """Create and optionally start a batch experiment."""
    if len(payload.sweep_definitions) != 1:
        raise HTTPException(status_code=400, detail="V1 supports exactly one sweep definition")

    test_user: Any = get_or_create_test_user(session)
    sweep_request: BatchSweepDefinitionRequest = payload.sweep_definitions[0]
    service: Any | BatchExperimentService = get_batch_service()

    try:
        if payload.preset is not None:
            base_config = TrainingConfig.preset_config(payload.preset)
        elif payload.base_config is not None:
            base_config = payload.base_config
        else:
            raise HTTPException(
                status_code=400,
                detail="Provide either `preset` or `base_config` when creating a batch experiment.",
            )

        # Service now returns UUID directly to avoid DetachedInstanceError
        batch_id: UUID | Any = service.create_batch(
            name=payload.name,
            description=payload.description,
            base_config=base_config,
            sweep_definition=SweepDefinition(
                parameter=sweep_request.parameter,
                value_type=sweep_request.value_type,
                range=SweepRangeDefinition(
                    start=sweep_request.range.start,
                    end=sweep_request.range.end,
                    step=sweep_request.range.step,
                ),
            ),
            user=test_user,
        )
        
        if payload.auto_start:
            await service.start_batch(batch_id)

        # Fetch fresh batch from database with current session
        batch = session.get(BatchExperiment, batch_id)
        if not batch:
            raise HTTPException(status_code=500, detail="Batch not found after creation")
        return _to_batch_response(batch)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("", response_model=list[BatchExperimentResponse])
async def list_batch_experiments(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """List batch experiments for the local test user."""
    test_user = get_or_create_test_user(session)
    statement = (
        select(BatchExperiment)
        .where(BatchExperiment.created_by_id == test_user.id)
        .offset(skip)
        .limit(limit)
    )
    batches = session.exec(statement).all()
    return [_to_batch_response(batch) for batch in batches]


@router.get("/{batch_id}", response_model=BatchExperimentResponse)
async def get_batch_experiment(batch_id: uuid.UUID, session: SessionDep) -> Any:
    """Get batch experiment status."""
    batch = session.get(BatchExperiment, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch experiment not found")
    return _to_batch_response(batch)


@router.post("/{batch_id}/start")
async def start_batch_experiment(batch_id: uuid.UUID, session: SessionDep) -> dict[str, str]:
    """Start a queued batch experiment."""
    batch = session.get(BatchExperiment, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch experiment not found")
    if batch.status == JobStatus.RUNNING:
        raise HTTPException(status_code=400, detail="Batch experiment already running")

    service: BatchExperimentService = get_batch_service()
    try:
        await service.start_batch(batch_id)
        return {"id": str(batch_id), "status": "running"}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{batch_id}/results")
async def get_batch_results(batch_id: uuid.UUID, session: SessionDep) -> dict[str, Any]:
    """Get aggregated results for a batch experiment."""
    batch = session.get(BatchExperiment, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch experiment not found")

    service = get_batch_service()
    results = service.get_batch_results(batch_id)
    return results

@router.post("/{batch_id}/retry")
async def retry_batch_experiment(
    batch_id: uuid.UUID,
    session: SessionDep,
    service: BatchExperimentServiceDep,
) -> dict[str, str]:
    """Retry failed runs in a batch experiment."""
    batch = session.get(BatchExperiment, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch experiment not found")
    
    if batch.status not in [JobStatus.FAILED, JobStatus.COMPLETED_WITH_ERRORS]:
        raise HTTPException(
            status_code=400,
            detail=f"Can only retry failed or partially completed batches. Current status: {batch.status}"
        )
    
    # Reset failed runs to queued
    repo = BatchExperimentRepository(session)
    runs = repo.get_runs(batch_id)
    failed_count = 0
    for run in runs:
        if run.status == JobStatus.FAILED:
            repo.update_run_status(run.id, JobStatus.QUEUED, 0.0, error_message=None)
            failed_count += 1
    
    # Reset batch status
    repo.update_batch_status(batch_id, JobStatus.QUEUED, 0.0, error_message=None)
    session.commit()
    
    # Start execution
    await service.start_batch(batch_id)
    
    return {"message": f"Retrying {failed_count} failed runs"}


@router.get("/grid-sweeps/{batch_name}/heatmaps/{filename}")
async def get_grid_sweep_heatmap(batch_name: str, filename: str) -> FileResponse:
    """
    Serve heatmap images for 2D grid sweeps.
    
    Args:
        batch_name: Name of the grid sweep batch
        filename: Heatmap filename (e.g., "msp_uncertainty_epistemic.png")
    
    Returns:
        FileResponse with the heatmap image
    """
    # Validate filename to prevent directory traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    # Construct file path
    file_path = Path("results") / "grid_sweeps" / batch_name / filename
    
    # Check if file exists
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Heatmap not found: {filename} for batch {batch_name}"
        )
    
    # Determine media type
    media_type = "image/png" if filename.endswith(".png") else "text/html"
    
    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename
    )


@router.get("/grid-sweeps/{batch_name}/heatmaps")
async def list_grid_sweep_heatmaps(batch_name: str) -> dict[str, Any]:
    """
    List all available heatmaps for a grid sweep batch.
    
    Args:
        batch_name: Name of the grid sweep batch
    
    Returns:
        Dictionary with list of available heatmaps
    """
    # Construct directory path
    dir_path = Path("results") / "grid_sweeps" / batch_name
    
    if not dir_path.exists():
        return {"batch_name": batch_name, "heatmaps": []}
    
    # List all PNG and HTML files
    heatmaps = []
    for file_path in dir_path.glob("*"):
        if file_path.suffix in [".png", ".html"]:
            heatmaps.append({
                "filename": file_path.name,
                "type": file_path.suffix[1:],  # Remove the dot
                "size_bytes": file_path.stat().st_size,
                "url": f"/api/v1/batch-experiments/grid-sweeps/{batch_name}/heatmaps/{file_path.name}"
            })
    
    return {
        "batch_name": batch_name,
        "heatmaps": heatmaps,
        "total_count": len(heatmaps)
    }


@router.delete("/{batch_id}")
async def delete_batch_experiment(
    batch_id: uuid.UUID,
    session: SessionDep,
) -> dict[str, str]:
    """Delete a batch experiment and all its runs."""
    batch = session.get(BatchExperiment, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch experiment not found")
    
    # Use repository to delete (handles cascade deletion of runs)
    repo = BatchExperimentRepository(session)
    deleted = repo.delete_batch(batch_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Batch experiment not found")
    
    return {"message": "Batch experiment deleted successfully", "id": str(batch_id)}


def _to_batch_response(batch: BatchExperiment) -> BatchExperimentResponse:
    """Convert table model to response DTO."""
    import json

    return BatchExperimentResponse(
        id=batch.id,
        name=batch.name,
        description=batch.description,
        status=batch.status,
        progress=batch.progress,
        created_at=batch.created_at,
        started_at=batch.started_at,
        completed_at=batch.completed_at,
        current_run_index=batch.current_run_index,
        total_runs=batch.total_runs,
        completed_runs=batch.completed_runs,
        successful_runs=batch.successful_runs,
        failed_runs=batch.failed_runs,
        storage_root=batch.storage_root,
        error_message=batch.error_message,
        sweep_definitions=json.loads(batch.sweep_definitions_json),
    )

# Made with Bob
