"""Training orchestrator - Facade for training workflow."""
import asyncio
import uuid
import yaml
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.domain.models import TrainingConfig
from app.domain.value_objects import ProgressUpdate
from app.repositories.experiment_repository import ExperimentRepository
from app.services.executors.base import TrainingExecutor
from app.tables import JobStatus


class TrainingOrchestrator:
    """Orchestrate training workflow (Facade pattern)."""

    def __init__(self, executor: TrainingExecutor, repository: ExperimentRepository):
        self.executor = executor
        self.repository = repository
        self._running_jobs: dict[uuid.UUID, asyncio.Task] = {}

    async def start_training(self, experiment_id: uuid.UUID) -> None:
        """Start training job asynchronously."""
        if experiment_id in self._running_jobs:
            raise ValueError(f"Experiment {experiment_id} already running")

        task = asyncio.create_task(self._run_training(experiment_id))
        self._running_jobs[experiment_id] = task

    async def _run_training(self, experiment_id: uuid.UUID) -> None:
        """Run training workflow."""
        try:
            experiment = self.repository.get(experiment_id)
            if not experiment:
                raise ValueError(f"Experiment {experiment_id} not found")

            # Parse config and generate YAML
            config = TrainingConfig(**experiment.config_yaml if isinstance(experiment.config_yaml, dict) else yaml.safe_load(experiment.config_yaml))
            config_path, output_dir = self._prepare_paths(experiment_id, config)

            # Update status to running
            self.repository.update_status(experiment_id, JobStatus.RUNNING, 0.0)

            # Execute training
            def progress_callback(update: ProgressUpdate):
                self.repository.update_status(experiment_id, JobStatus.RUNNING, update.progress, update.message)

            result = await self.executor.execute(config_path, output_dir, progress_callback)

            # Save results
            self.repository.save_results(experiment_id, result)

        except Exception as e:
            self.repository.mark_failed(experiment_id, str(e))
        finally:
            self._running_jobs.pop(experiment_id, None)

    def _prepare_paths(self, experiment_id: uuid.UUID, config: TrainingConfig) -> tuple[Path, Path]:
        """Prepare config file and output directory."""
        base_dir = Path("/tmp/walaris_experiments")
        exp_dir = base_dir / str(experiment_id)
        exp_dir.mkdir(parents=True, exist_ok=True)

        config_path = exp_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config.to_yaml_dict(), f)

        output_dir = exp_dir / "results"
        output_dir.mkdir(exist_ok=True)

        return config_path, output_dir
