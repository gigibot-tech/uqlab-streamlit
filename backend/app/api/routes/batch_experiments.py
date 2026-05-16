"""Batch experiment management endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.api.deps import SessionDep
from app.core.db import engine
from app.core.security import get_password_hash
from app.domain.models import TrainingConfig
from app.services.batch_experiment_service import (
    BatchExperimentService,
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
        _batch_service = BatchExperimentService(DirectExecutor(ML_SCRIPT))
    return _batch_service


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
    base_config: TrainingConfig
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

    test_user = get_or_create_test_user(session)
    sweep_request = payload.sweep_definitions[0]
    service = get_batch_service()

    try:
        # Service now returns UUID directly to avoid DetachedInstanceError
        batch_id = service.create_batch(
            name=payload.name,
            description=payload.description,
            base_config=payload.base_config,
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

    service = get_batch_service()
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
    try:
        return service.get_batch_results(batch_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


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
