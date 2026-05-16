"""Repository for batch experiment data access."""

import json
import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import Session, desc, select

from app.tables import BatchExperiment, BatchExperimentRun, JobStatus


class BatchExperimentRepository:
    """Repository pattern for batch experiment data access."""

    def __init__(self, session: Session):
        self.session = session

    def create_batch(self, batch: BatchExperiment) -> BatchExperiment:
        """Persist a new batch experiment."""
        self.session.add(batch)
        self.session.commit()
        self.session.refresh(batch)
        return batch

    def create_runs(self, runs: list[BatchExperimentRun]) -> list[BatchExperimentRun]:
        """Persist generated batch runs."""
        for run in runs:
            self.session.add(run)
        self.session.commit()
        for run in runs:
            self.session.refresh(run)
        return runs

    def get_batch(self, batch_id: uuid.UUID) -> Optional[BatchExperiment]:
        """Get batch by ID."""
        return self.session.get(BatchExperiment, batch_id)

    def get_runs(self, batch_id: uuid.UUID) -> list[BatchExperimentRun]:
        """Get all runs for a batch ordered by run index."""
        statement = (
            select(BatchExperimentRun)
            .where(BatchExperimentRun.batch_experiment_id == batch_id)
            .order_by("run_index")
        )
        return list(self.session.exec(statement).all())

    def get_run(self, run_id: uuid.UUID) -> Optional[BatchExperimentRun]:
        """Get batch run by ID."""
        return self.session.get(BatchExperimentRun, run_id)

    def list_batches(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> list[BatchExperiment]:
        """List batches for a specific user."""
        statement = (
            select(BatchExperiment)
            .where(BatchExperiment.created_by_id == user_id)
            .offset(skip)
            .limit(limit)
            .order_by(desc(BatchExperiment.created_at))
        )
        return list(self.session.exec(statement).all())

    def update_batch_status(
        self,
        batch_id: uuid.UUID,
        status: JobStatus,
        progress: float,
        error_message: str | None = None,
        current_run_index: int | None = None,
    ) -> BatchExperiment:
        """Update batch job status and progress."""
        batch = self.get_batch(batch_id)
        if not batch:
            raise ValueError(f"Batch experiment {batch_id} not found")

        batch.status = status
        batch.progress = progress
        batch.current_run_index = current_run_index

        if status == JobStatus.RUNNING and not batch.started_at:
            batch.started_at = datetime.utcnow()
        elif status in {JobStatus.COMPLETED, JobStatus.COMPLETED_WITH_ERRORS, JobStatus.FAILED}:
            batch.completed_at = datetime.utcnow()

        if error_message:
            batch.error_message = error_message

        self.session.add(batch)
        self.session.commit()
        self.session.refresh(batch)
        return batch

    def update_run_status(
        self,
        run_id: uuid.UUID,
        status: JobStatus,
        progress: float,
        error_message: str | None = None,
    ) -> BatchExperimentRun:
        """Update a generated run status and progress."""
        run = self.get_run(run_id)
        if not run:
            raise ValueError(f"Batch run {run_id} not found")

        run.status = status
        run.progress = progress

        if status == JobStatus.RUNNING and not run.started_at:
            run.started_at = datetime.utcnow()
        elif status in {JobStatus.COMPLETED, JobStatus.FAILED}:
            run.completed_at = datetime.utcnow()
            if status == JobStatus.COMPLETED:
                run.progress = 1.0

        if error_message:
            run.error_message = error_message

        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)
        return run

    def save_run_results(
        self,
        run_id: uuid.UUID,
        *,
        aleatoric_auroc: float | None,
        epistemic_auroc: float | None,
        train_size: int | None,
        eval_sizes: dict | None,
        output_dir: str | None,
        experiment_id: uuid.UUID | None,
        result_summary: dict | None = None,
    ) -> BatchExperimentRun:
        """Persist child run results."""
        run = self.get_run(run_id)
        if not run:
            raise ValueError(f"Batch run {run_id} not found")

        run.aleatoric_auroc = aleatoric_auroc
        run.epistemic_auroc = epistemic_auroc
        run.train_size = train_size
        run.eval_sizes_json = json.dumps(eval_sizes or {})
        run.output_dir = output_dir
        run.experiment_id = experiment_id
        run.result_summary_json = json.dumps(result_summary or {})
        run.status = JobStatus.COMPLETED
        run.progress = 1.0
        run.completed_at = datetime.utcnow()

        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)
        return run

    def update_batch_counters(
        self,
        batch_id: uuid.UUID,
        *,
        completed_runs: int,
        successful_runs: int,
        failed_runs: int,
        progress: float,
        current_run_index: int | None,
        status: JobStatus | None = None,
    ) -> BatchExperiment:
        """Persist aggregate counters for a batch."""
        batch = self.get_batch(batch_id)
        if not batch:
            raise ValueError(f"Batch experiment {batch_id} not found")

        batch.completed_runs = completed_runs
        batch.successful_runs = successful_runs
        batch.failed_runs = failed_runs
        batch.progress = progress
        batch.current_run_index = current_run_index

        if status is not None:
            batch.status = status
            if status == JobStatus.RUNNING and not batch.started_at:
                batch.started_at = datetime.utcnow()
            elif status in {JobStatus.COMPLETED, JobStatus.COMPLETED_WITH_ERRORS, JobStatus.FAILED}:
                batch.completed_at = datetime.utcnow()

        self.session.add(batch)
        self.session.commit()
        self.session.refresh(batch)
        return batch

    def save_batch_summary(self, batch_id: uuid.UUID, summary: dict) -> BatchExperiment:
        """Save cached aggregated summary JSON."""
        batch = self.get_batch(batch_id)
        if not batch:
            raise ValueError(f"Batch experiment {batch_id} not found")

        batch.results_summary_json = json.dumps(summary)
        self.session.add(batch)
        self.session.commit()
        self.session.refresh(batch)
        return batch

    def delete_batch(self, batch_id: uuid.UUID) -> bool:
        """Delete batch by ID."""
        batch = self.get_batch(batch_id)
        if not batch:
            return False

        self.session.delete(batch)
        self.session.commit()
        return True

# Made with Bob
