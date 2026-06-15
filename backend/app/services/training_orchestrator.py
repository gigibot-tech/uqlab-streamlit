"""Training orchestrator - Facade for training workflow."""
import asyncio
import logging
import uuid
import yaml
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlmodel import Session

logger = logging.getLogger(__name__)

from app.core.db import engine
from app.domain.models import TrainingConfig
from app.domain.value_objects import ProgressUpdate
from app.repositories.experiment_repository import ExperimentRepository
from app.services.executors.base import TrainingExecutor
from app.tables import JobStatus
from app.api.routes.websocket import broadcast_progress


class TrainingOrchestrator:
    """Orchestrate training workflow (Facade pattern)."""

    def __init__(self, executor: TrainingExecutor, repository: ExperimentRepository):
        self.executor = executor
        self.repository = repository
        self._running_jobs: dict[uuid.UUID, asyncio.Task] = {}
        self._current_training: Optional[uuid.UUID] = None  # Single experiment at a time

    async def start_training(self, experiment_id: uuid.UUID) -> None:
        """Start training job asynchronously (one at a time)."""
        if self._current_training is not None:
            raise ValueError(f"Another experiment is already running: {self._current_training}")
        
        if experiment_id in self._running_jobs:
            raise ValueError(f"Experiment {experiment_id} already running")

        self._current_training = experiment_id
        task = asyncio.create_task(self._run_training(experiment_id))
        self._running_jobs[experiment_id] = task

    async def _run_training(self, experiment_id: uuid.UUID) -> None:
        """Run training workflow."""
        try:
            # Create a fresh session for reading experiment data
            with Session(engine) as session:
                repo = ExperimentRepository(session)
                experiment = repo.get(experiment_id)
                if not experiment:
                    raise ValueError(f"Experiment {experiment_id} not found")

                # Parse config and generate YAML
                raw_config = (
                    experiment.config_yaml
                    if isinstance(experiment.config_yaml, dict)
                    else yaml.safe_load(experiment.config_yaml)
                )
                config = TrainingConfig.from_legacy_flat_dict(raw_config)
                config_path, output_dir = self._prepare_paths(experiment_id, config)

                # Update status to running
                repo.update_status(experiment_id, JobStatus.RUNNING, 0.0)

            # Get the event loop for scheduling tasks from thread
            loop = asyncio.get_running_loop()

            # Execute training with WebSocket broadcasting
            def progress_callback(update: ProgressUpdate):
                # Update database with fresh session (synchronous)
                with Session(engine) as session:
                    repo = ExperimentRepository(session)
                    repo.update_status(experiment_id, JobStatus.RUNNING, update.progress, update.message)
                
                # Broadcast via WebSocket (schedule on event loop from thread)
                try:
                    asyncio.run_coroutine_threadsafe(
                        broadcast_progress(str(experiment_id), {
                            "progress": update.progress,
                            "stage": update.stage,
                            "message": update.message,
                            "epoch": update.epoch,
                            "total_epochs": update.total_epochs
                        }),
                        loop
                    )
                except Exception as e:
                    # Don't fail training if WebSocket broadcast fails
                    logger.warning(f"Failed to broadcast progress: {e}")

            result = await self.executor.execute(config_path, output_dir, progress_callback)

            # Save results with fresh session
            with Session(engine) as session:
                repo = ExperimentRepository(session)
                repo.save_results(experiment_id, result)

        except Exception as e:
            # Mark failed with fresh session
            with Session(engine) as session:
                repo = ExperimentRepository(session)
                repo.mark_failed(experiment_id, str(e))
        finally:
            self._running_jobs.pop(experiment_id, None)
            if self._current_training == experiment_id:
                self._current_training = None

    def _prepare_paths(self, experiment_id: uuid.UUID, config: TrainingConfig) -> tuple[Path, Path]:
        """Prepare config file and output directory."""
        from app.core.runtime_paths import experiment_dir

        exp_dir = experiment_dir(experiment_id)
        exp_dir.mkdir(parents=True, exist_ok=True)

        config_path = exp_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config.to_yaml_dict(), f)

        output_dir = exp_dir / "results"
        output_dir.mkdir(exist_ok=True)

        return config_path, output_dir
