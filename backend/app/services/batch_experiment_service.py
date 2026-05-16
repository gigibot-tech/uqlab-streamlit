"""Batch experiment orchestration and aggregation services."""

from __future__ import annotations

import asyncio
import csv
import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from sqlmodel import Session

from app.core.db import engine
from app.domain.models import TrainingConfig
from app.domain.value_objects import ProgressUpdate
from app.repositories.batch_experiment_repository import BatchExperimentRepository

logger = logging.getLogger(__name__)
from app.repositories.experiment_repository import ExperimentRepository
from app.services.executors.direct_executor import DirectExecutor
from app.tables import (
    BatchExperiment,
    BatchExperimentRun,
    JobStatus,
    UncertaintyExperiment,
    User,
)


@dataclass(frozen=True)
class SweepRangeDefinition:
    """Numeric sweep specification."""

    start: float
    end: float
    step: float


@dataclass(frozen=True)
class SweepDefinition:
    """Single-parameter sweep definition."""

    parameter: str
    value_type: str
    range: SweepRangeDefinition


class BatchExperimentService:
    """Service responsible for batch creation and execution."""

    MAX_RUNS = 100

    def __init__(self, executor: DirectExecutor):
        self.executor = executor
        self._running_batches: dict[uuid.UUID, asyncio.Task] = {}

    def create_batch(
        self,
        *,
        name: str,
        description: str | None,
        base_config: TrainingConfig,
        sweep_definition: SweepDefinition,
        user: User,
    ) -> uuid.UUID:
        """Create a batch experiment and all generated child runs.
        
        Returns:
            UUID of the created batch experiment
        """
        generated_values = self._generate_values(sweep_definition)
        storage_root = self._batch_storage_root_placeholder()

        with Session(engine) as session:
            repository = BatchExperimentRepository(session)

            batch = BatchExperiment(
                name=name,
                description=description,
                base_config_yaml=yaml.safe_dump(base_config.model_dump()),
                sweep_definitions_json=json.dumps(
                    [self._serialize_sweep_definition(sweep_definition, generated_values)]
                ),
                created_by_id=user.id,
                storage_root=storage_root,
                total_runs=len(generated_values),
            )
            batch = repository.create_batch(batch)

            # ✅ Access batch.id while still in session context
            batch_id = batch.id
            concrete_storage_root = str(self._batch_root(batch_id))
            batch.storage_root = concrete_storage_root
            session.add(batch)
            session.commit()
            session.refresh(batch)

            runs = []
            for index, value in enumerate(generated_values, start=1):
                config = self._apply_sweep_value(base_config, sweep_definition, value)
                run_name = f"exp_{index}_{sweep_definition.parameter}_{self._format_value(value)}"
                output_dir = str(self._batch_root(batch_id) / "experiments" / run_name)

                runs.append(
                    BatchExperimentRun(
                        batch_experiment_id=batch_id,
                        run_index=index,
                        run_name=run_name,
                        swept_parameter=sweep_definition.parameter,
                        swept_value_numeric=float(value),
                        swept_value_text=self._format_value(value),
                        resolved_config_yaml=yaml.safe_dump(config.model_dump()),
                        output_dir=output_dir,
                    )
                )

            logger.info(f"📝 Creating {len(runs)} batch experiment runs for batch {batch_id}")
            repository.create_runs(runs)
            logger.info(f"✅ Successfully created {len(runs)} runs in database")

        # ✅ Now safe to use batch_id outside session
        self._initialize_storage(batch_id)
        self._write_batch_metadata(batch_id)
        return batch_id  # Return ID instead of detached object

    async def start_batch(self, batch_id: uuid.UUID) -> None:
        """Start batch execution asynchronously."""
        if batch_id in self._running_batches:
            raise ValueError(f"Batch experiment {batch_id} already running")

        task = asyncio.create_task(self._run_batch(batch_id))
        self._running_batches[batch_id] = task

    async def _run_batch(self, batch_id: uuid.UUID) -> None:
        """Run all generated experiments sequentially."""
        logger.info(f"🚀 Starting batch execution for {batch_id}")
        try:
            # Get run IDs (not objects) to avoid detached instance issues
            run_ids = []
            with Session(engine) as session:
                repository = BatchExperimentRepository(session)
                batch = repository.get_batch(batch_id)
                if not batch:
                    raise ValueError(f"Batch experiment {batch_id} not found")

                runs = repository.get_runs(batch_id)
                logger.info(f"📊 Found {len(runs)} runs to execute for batch {batch_id}")
                
                if not runs:
                    logger.error(f"❌ No runs found for batch {batch_id}! Batch will complete immediately.")
                    repository.update_batch_status(
                        batch_id,
                        JobStatus.COMPLETED,
                        progress=1.0,
                        current_run_index=None,
                    )
                    return
                
                # Extract run IDs before session closes
                run_ids = [run.id for run in runs]
                
                repository.update_batch_status(
                    batch_id,
                    JobStatus.RUNNING,
                    progress=0.0,
                    current_run_index=1,
                )

            total_runs = len(run_ids)
            logger.info(f"▶️ Beginning execution of {total_runs} experiments")

            for position, run_id in enumerate(run_ids, start=1):
                with Session(engine) as session:
                    repository = BatchExperimentRepository(session)
                    run = repository.get_run(run_id)
                    if not run:
                        logger.error(f"❌ Run {run_id} not found, skipping")
                        continue
                    
                    logger.info(f"🔄 Starting run {position}/{total_runs}: {run.run_name}")
                    repository.update_batch_status(
                        batch_id,
                        JobStatus.RUNNING,
                        progress=(position - 1) / total_runs if total_runs else 1.0,
                        current_run_index=position,
                    )
                    repository.update_run_status(run_id, JobStatus.RUNNING, 0.0)

                await self._run_single_batch_experiment(batch_id, run_id, position, total_runs)
                
                with Session(engine) as session:
                    repository = BatchExperimentRepository(session)
                    run = repository.get_run(run_id)
                    if run:
                        logger.info(f"✅ Completed run {position}/{total_runs}: {run.run_name}")
                self._aggregate_batch_results(batch_id)

            with Session(engine) as session:
                repository = BatchExperimentRepository(session)
                runs = repository.get_runs(batch_id)
                failed_runs = sum(1 for item in runs if item.status == JobStatus.FAILED)
                successful_runs = sum(1 for item in runs if item.status == JobStatus.COMPLETED)
                final_status = (
                    JobStatus.COMPLETED_WITH_ERRORS if failed_runs > 0 else JobStatus.COMPLETED
                )
                logger.info(f"🏁 Batch complete: {successful_runs} successful, {failed_runs} failed")
                repository.update_batch_counters(
                    batch_id,
                    completed_runs=len(runs),
                    successful_runs=successful_runs,
                    failed_runs=failed_runs,
                    progress=1.0,
                    current_run_index=None,
                    status=final_status,
                )

            self._aggregate_batch_results(batch_id)
        except Exception as exc:
            with Session(engine) as session:
                repository = BatchExperimentRepository(session)
                repository.update_batch_status(
                    batch_id,
                    JobStatus.FAILED,
                    progress=0.0,
                    error_message=str(exc),
                    current_run_index=None,
                )
        finally:
            self._running_batches.pop(batch_id, None)

    async def _run_single_batch_experiment(
        self, batch_id: uuid.UUID, run_id: uuid.UUID, position: int, total_runs: int
    ) -> None:
        """Execute one child experiment and persist its results."""
        with Session(engine) as session:
            batch_repository = BatchExperimentRepository(session)
            run = batch_repository.get_run(run_id)
            batch = batch_repository.get_batch(batch_id)
            if not run or not batch:
                raise ValueError("Batch run or batch experiment not found")

            experiment = UncertaintyExperiment(
                name=f"{batch.name}_{run.run_name}",
                config_yaml=run.resolved_config_yaml,
                created_by_id=batch.created_by_id,
            )
            session.add(experiment)
            session.commit()
            session.refresh(experiment)

            run.experiment_id = experiment.id
            session.add(run)
            session.commit()
            session.refresh(run)

            config_payload = yaml.safe_load(run.resolved_config_yaml)
            training_config = TrainingConfig(**config_payload)
            config_path, output_dir = self._prepare_run_paths(batch_id, run.run_name, training_config)

            experiment_repository = ExperimentRepository(session)
            experiment_repository.update_status(experiment.id, JobStatus.RUNNING, 0.0)

        loop = asyncio.get_running_loop()

        def progress_callback(update: ProgressUpdate) -> None:
            run_fraction = update.progress / total_runs
            batch_progress = ((position - 1) / total_runs) + run_fraction

            with Session(engine) as callback_session:
                batch_repository = BatchExperimentRepository(callback_session)
                experiment_repository = ExperimentRepository(callback_session)

                batch_repository.update_run_status(run_id, JobStatus.RUNNING, update.progress)
                batch_repository.update_batch_counters(
                    batch_id,
                    completed_runs=position - 1,
                    successful_runs=self._count_runs(batch_id, JobStatus.COMPLETED, callback_session),
                    failed_runs=self._count_runs(batch_id, JobStatus.FAILED, callback_session),
                    progress=min(batch_progress, 0.999),
                    current_run_index=position,
                    status=JobStatus.RUNNING,
                )
                experiment = batch_repository.get_run(run_id)
                if experiment and experiment.experiment_id:
                    experiment_repository.update_status(
                        experiment.experiment_id, JobStatus.RUNNING, update.progress, update.message
                    )

            _ = loop

        try:
            logger.info(f"🎯 Executing training for run {position}/{total_runs}: {run.run_name}")
            logger.info(f"   Config: {config_path}")
            logger.info(f"   Output: {output_dir}")
            result = await self.executor.execute(config_path, output_dir, progress_callback)
            logger.info(f"✅ Training completed for run {position}/{total_runs}")

            summary_payload = {
                "aleatoric_auroc": result.aleatoric_auroc,
                "epistemic_auroc": result.epistemic_auroc,
                "train_size": result.train_size,
                "eval_sizes": result.eval_sizes,
                "results_path": result.results_path,
            }

            with Session(engine) as session:
                batch_repository = BatchExperimentRepository(session)
                run = batch_repository.get_run(run_id)
                if not run:
                    raise ValueError(f"Batch run {run_id} not found")
                batch_repository.save_run_results(
                    run_id,
                    aleatoric_auroc=result.aleatoric_auroc,
                    epistemic_auroc=result.epistemic_auroc,
                    train_size=result.train_size,
                    eval_sizes=result.eval_sizes,
                    output_dir=result.results_path,
                    experiment_id=run.experiment_id,
                    result_summary=summary_payload,
                )

                if run.experiment_id:
                    experiment_repository = ExperimentRepository(session)
                    experiment_repository.save_results(run.experiment_id, result)
        except Exception as exc:
            logger.error(f"❌ Training failed for run {position}/{total_runs}: {str(exc)}")
            logger.exception("Full traceback:")
            with Session(engine) as session:
                batch_repository = BatchExperimentRepository(session)
                run = batch_repository.get_run(run_id)
                batch_repository.update_run_status(
                    run_id,
                    JobStatus.FAILED,
                    progress=run.progress if run else 0.0,
                    error_message=str(exc),
                )
                if run and run.experiment_id:
                    experiment_repository = ExperimentRepository(session)
                    experiment_repository.mark_failed(run.experiment_id, str(exc))

    def get_batch_results(self, batch_id: uuid.UUID) -> dict[str, Any]:
        """Return aggregated results for a batch."""
        with Session(engine) as session:
            repository = BatchExperimentRepository(session)
            batch = repository.get_batch(batch_id)
            if not batch:
                raise ValueError(f"Batch experiment {batch_id} not found")

            runs = repository.get_runs(batch_id)
            summary = json.loads(batch.results_summary_json) if batch.results_summary_json else {}

        comparison_table = [
            {
                "run_index": run.run_index,
                "run_name": run.run_name,
                "status": run.status.value,
                "swept_parameter": run.swept_parameter,
                "swept_value": run.swept_value_numeric,
                "aleatoric_auroc": run.aleatoric_auroc,
                "epistemic_auroc": run.epistemic_auroc,
                "train_size": run.train_size,
                "results_path": run.output_dir,
                "error_message": run.error_message,
            }
            for run in runs
        ]

        return {
            "batch_experiment_id": str(batch.id),
            "status": batch.status.value,
            "swept_parameter": comparison_table[0]["swept_parameter"] if comparison_table else None,
            "x_axis_label": comparison_table[0]["swept_parameter"] if comparison_table else None,
            "series": self._build_series(runs),
            "comparison_table": comparison_table,
            "artifacts": {
                "plot_json": str(self._batch_root(batch.id) / "aggregated_results" / "auroc_curves.json"),
                "plot_png": str(self._batch_root(batch.id) / "aggregated_results" / "auroc_curves.png"),
                "comparison_csv": str(self._batch_root(batch.id) / "aggregated_results" / "comparison_table.csv"),
                "summary_json": str(self._batch_root(batch.id) / "aggregated_results" / "summary.json"),
            },
            "summary": summary,
        }

    def _aggregate_batch_results(self, batch_id: uuid.UUID) -> None:
        """Aggregate batch results into summary and CSV artifacts."""
        with Session(engine) as session:
            repository = BatchExperimentRepository(session)
            batch = repository.get_batch(batch_id)
            runs = repository.get_runs(batch_id)
            if not batch:
                raise ValueError(f"Batch experiment {batch_id} not found")

            aggregated_dir = self._batch_root(batch_id) / "aggregated_results"
            aggregated_dir.mkdir(parents=True, exist_ok=True)

            comparison_csv = aggregated_dir / "comparison_table.csv"
            with open(comparison_csv, "w", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "run_index",
                        "run_name",
                        "status",
                        "swept_parameter",
                        "swept_value",
                        "aleatoric_auroc",
                        "epistemic_auroc",
                        "train_size",
                        "results_path",
                        "error_message",
                    ],
                )
                writer.writeheader()
                for run in runs:
                    writer.writerow(
                        {
                            "run_index": run.run_index,
                            "run_name": run.run_name,
                            "status": run.status.value,
                            "swept_parameter": run.swept_parameter,
                            "swept_value": run.swept_value_numeric,
                            "aleatoric_auroc": run.aleatoric_auroc,
                            "epistemic_auroc": run.epistemic_auroc,
                            "train_size": run.train_size,
                            "results_path": run.output_dir,
                            "error_message": run.error_message,
                        }
                    )

            series = self._build_series(runs)
            summary = {
                "batch_experiment_id": str(batch.id),
                "name": batch.name,
                "status": batch.status.value,
                "swept_parameter": runs[0].swept_parameter if runs else None,
                "total_runs": batch.total_runs,
                "successful_runs": sum(1 for item in runs if item.status == JobStatus.COMPLETED),
                "failed_runs": sum(1 for item in runs if item.status == JobStatus.FAILED),
                "best_epistemic_run": self._best_run_payload(runs, "epistemic_auroc"),
                "best_aleatoric_run": self._best_run_payload(runs, "aleatoric_auroc"),
                "series": series,
                "generated_at": datetime.utcnow().isoformat() + "Z",
            }

            summary_path = aggregated_dir / "summary.json"
            with open(summary_path, "w") as handle:
                json.dump(summary, handle, indent=2)

            plot_path = aggregated_dir / "auroc_curves.json"
            with open(plot_path, "w") as handle:
                json.dump(
                    {
                        "data": [
                            {
                                "type": "scatter",
                                "mode": "lines+markers",
                                "name": series_item["display_name"],
                                "x": [point["x"] for point in series_item["points"]],
                                "y": [point["y"] for point in series_item["points"]],
                            }
                            for series_item in series
                        ],
                        "layout": {
                            "title": f"AUROC vs {runs[0].swept_parameter}" if runs else "AUROC Curves",
                            "xaxis": {"title": runs[0].swept_parameter if runs else "parameter"},
                            "yaxis": {"title": "AUROC", "range": [0, 1]},
                        },
                    },
                    handle,
                    indent=2,
                )

            png_path = aggregated_dir / "auroc_curves.png"
            if not png_path.exists():
                png_path.write_text("Static PNG export not implemented in V1.\n")

            repository.save_batch_summary(batch_id, summary)

            completed_runs = sum(
                1 for item in runs if item.status in {JobStatus.COMPLETED, JobStatus.FAILED}
            )
            successful_runs = sum(1 for item in runs if item.status == JobStatus.COMPLETED)
            failed_runs = sum(1 for item in runs if item.status == JobStatus.FAILED)
            repository.update_batch_counters(
                batch_id,
                completed_runs=completed_runs,
                successful_runs=successful_runs,
                failed_runs=failed_runs,
                progress=batch.progress,
                current_run_index=batch.current_run_index,
            )

    def _generate_values(self, definition: SweepDefinition) -> list[int | float]:
        """Generate sweep values from range config."""
        if definition.range.step <= 0:
            raise ValueError("Sweep step must be positive")
        if definition.range.end < definition.range.start:
            raise ValueError("Sweep end must be greater than or equal to start")

        values: list[int | float] = []
        current = definition.range.start
        epsilon = abs(definition.range.step) / 1000.0

        while current <= definition.range.end + epsilon:
            value = int(round(current)) if definition.value_type == "int" else round(current, 10)
            values.append(value)
            current += definition.range.step

        if not values:
            raise ValueError("Sweep generated no values")
        if len(values) > self.MAX_RUNS:
            raise ValueError(f"Sweep generated {len(values)} runs, exceeding limit {self.MAX_RUNS}")

        return values

    def _apply_sweep_value(
        self, base_config: TrainingConfig, definition: SweepDefinition, value: int | float
    ) -> TrainingConfig:
        """Return a concrete config with one parameter overridden."""
        updated = base_config.model_dump()
        updated[definition.parameter] = int(value) if definition.value_type == "int" else float(value)
        return TrainingConfig(**updated)

    def _serialize_sweep_definition(
        self, definition: SweepDefinition, generated_values: list[int | float]
    ) -> dict[str, Any]:
        """Serialize sweep definition for persistence."""
        return {
            "parameter": definition.parameter,
            "value_type": definition.value_type,
            "range": {
                "start": definition.range.start,
                "end": definition.range.end,
                "step": definition.range.step,
            },
            "generated_values": generated_values,
        }

    def _prepare_run_paths(
        self, batch_id: uuid.UUID, run_name: str, config: TrainingConfig
    ) -> tuple[Path, Path]:
        """Prepare config and results paths for a child run."""
        run_dir = self._batch_root(batch_id) / "experiments" / run_name
        run_dir.mkdir(parents=True, exist_ok=True)

        config_path = run_dir / "config.yaml"
        with open(config_path, "w") as handle:
            yaml.safe_dump(config.to_yaml_dict(), handle)

        output_dir = run_dir
        return config_path, output_dir

    def _initialize_storage(self, batch_id: uuid.UUID) -> None:
        """Create batch storage directories."""
        root = self._batch_root(batch_id)
        (root / "experiments").mkdir(parents=True, exist_ok=True)
        (root / "aggregated_results").mkdir(parents=True, exist_ok=True)

    def _write_batch_metadata(self, batch_id: uuid.UUID) -> None:
        """Write batch-level configuration snapshots."""
        with Session(engine) as session:
            repository = BatchExperimentRepository(session)
            batch = repository.get_batch(batch_id)
            runs = repository.get_runs(batch_id)
            if not batch:
                raise ValueError(f"Batch experiment {batch_id} not found")

            root = self._batch_root(batch_id)
            with open(root / "batch_config.yaml", "w") as handle:
                yaml.safe_dump(
                    {
                        "name": batch.name,
                        "description": batch.description,
                        "base_config": yaml.safe_load(batch.base_config_yaml),
                        "sweep_definitions": json.loads(batch.sweep_definitions_json),
                    },
                    handle,
                )

            with open(root / "batch_metadata.json", "w") as handle:
                json.dump(
                    {
                        "id": str(batch.id),
                        "status": batch.status.value,
                        "total_runs": batch.total_runs,
                        "storage_root": batch.storage_root,
                        "runs": [
                            {
                                "id": str(run.id),
                                "run_index": run.run_index,
                                "run_name": run.run_name,
                                "swept_parameter": run.swept_parameter,
                                "swept_value": run.swept_value_numeric,
                            }
                            for run in runs
                        ],
                    },
                    handle,
                    indent=2,
                )

    def _build_series(self, runs: list[BatchExperimentRun]) -> list[dict[str, Any]]:
        """Build normalized plotting series."""
        ordered_runs = sorted(
            [run for run in runs if run.swept_value_numeric is not None],
            key=lambda item: item.swept_value_numeric or 0.0,
        )

        return [
            {
                "metric": "epistemic_auroc",
                "display_name": "Epistemic AUROC",
                "points": [
                    {
                        "x": run.swept_value_numeric,
                        "y": run.epistemic_auroc,
                        "run_index": run.run_index,
                        "status": run.status.value,
                    }
                    for run in ordered_runs
                    if run.epistemic_auroc is not None
                ],
            },
            {
                "metric": "aleatoric_auroc",
                "display_name": "Aleatoric AUROC",
                "points": [
                    {
                        "x": run.swept_value_numeric,
                        "y": run.aleatoric_auroc,
                        "run_index": run.run_index,
                        "status": run.status.value,
                    }
                    for run in ordered_runs
                    if run.aleatoric_auroc is not None
                ],
            },
        ]

    def _best_run_payload(
        self, runs: list[BatchExperimentRun], metric_name: str
    ) -> dict[str, Any] | None:
        """Return best run for a metric."""
        eligible = [
            run for run in runs
            if getattr(run, metric_name) is not None and run.status == JobStatus.COMPLETED
        ]
        if not eligible:
            return None

        best = max(eligible, key=lambda run: getattr(run, metric_name) or float("-inf"))
        return {
            "run_index": best.run_index,
            "swept_value": best.swept_value_numeric,
            metric_name: getattr(best, metric_name),
        }

    def _count_runs(self, batch_id: uuid.UUID, status: JobStatus, session: Session) -> int:
        """Count runs with a given status."""
        repository = BatchExperimentRepository(session)
        return sum(1 for run in repository.get_runs(batch_id) if run.status == status)

    def _format_value(self, value: int | float) -> str:
        """Format a sweep value for display and folder names."""
        if isinstance(value, int):
            return str(value)
        if float(value).is_integer():
            return str(int(value))
        return str(value).replace(".", "_")

    def _batch_root(self, batch_id: uuid.UUID) -> Path:
        """Return the canonical storage root for a batch."""
        return Path("/tmp/walaris_experiments") / f"batch_{batch_id}"

    def _batch_storage_root_placeholder(self) -> str:
        """Temporary placeholder before batch id exists."""
        return str(Path("/tmp/walaris_experiments") / "pending_batch")

# Made with Bob
