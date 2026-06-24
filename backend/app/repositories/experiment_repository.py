"""Repository for experiment data access."""

import json
import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import Session, select

from app.domain.models import TrainingResult
from app.domain.value_objects import TrainingStage
from app.tables import JobStatus, UncertaintyExperiment


class ExperimentRepository:
    """Repository pattern for experiment data access."""

    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session

    def get(self, experiment_id: uuid.UUID) -> Optional[UncertaintyExperiment]:
        """Get experiment by ID."""
        return self.session.get(UncertaintyExperiment, experiment_id)

    def get_by_user(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> list[UncertaintyExperiment]:
        """Get experiments for a specific user."""
        statement = (
            select(UncertaintyExperiment)
            .where(UncertaintyExperiment.created_by_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    def update_status(
        self,
        experiment_id: uuid.UUID,
        status: JobStatus,
        progress: float,
        message: Optional[str] = None,
    ) -> None:
        """Update experiment status and progress."""
        experiment = self.get(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        experiment.status = status
        experiment.progress = progress

        if status == JobStatus.RUNNING and not experiment.started_at:
            experiment.started_at = datetime.utcnow()
        elif status == JobStatus.COMPLETED:
            experiment.completed_at = datetime.utcnow()
            experiment.progress = 1.0
        elif status == JobStatus.FAILED:
            experiment.error_message = message

        self.session.add(experiment)
        self.session.commit()
        self.session.refresh(experiment)

    def save_results(
        self, experiment_id: uuid.UUID, results: TrainingResult
    ) -> None:
        """Save training results to experiment."""
        experiment = self.get(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        experiment.aleatoric_auroc = results.aleatoric_auroc
        experiment.epistemic_auroc = results.epistemic_auroc
        experiment.results_path = results.results_path
        experiment.best_signals_json = json.dumps(results.best_signals) if results.best_signals else None
        experiment.status = JobStatus.COMPLETED
        experiment.completed_at = datetime.utcnow()
        experiment.progress = 1.0
        experiment.error_message = None

        self.session.add(experiment)
        self.session.commit()
        self.session.refresh(experiment)

    def mark_failed(self, experiment_id: uuid.UUID, error_message: str) -> None:
        """Mark experiment as failed with error message."""
        experiment = self.get(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        experiment.status = JobStatus.FAILED
        experiment.error_message = error_message
        experiment.completed_at = datetime.utcnow()

        self.session.add(experiment)
        self.session.commit()
        self.session.refresh(experiment)
    
    def delete(self, experiment_id: uuid.UUID) -> bool:
        """Delete experiment by ID. Returns True if deleted, False if not found."""
        experiment = self.get(experiment_id)
        if not experiment:
            return False
        
        self.session.delete(experiment)
        self.session.commit()
        return True


# Made with Bob