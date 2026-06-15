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
from app.services.executors.base import TrainingExecutor
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


class BatchExperimentTracker:
    """Persistence and artifact tracking interface for batch execution."""

    def create_batch(
        self,
        *,
        name: str,
        description: str | None,
        base_config: TrainingConfig,
        sweep_definition: SweepDefinition,
        generated_values: list[int | float],
        user: User,
        batch_root: Path,
    ) -> uuid.UUID:
        raise NotImplementedError

    def get_run_ids(self, batch_id: uuid.UUID) -> list[uuid.UUID]:
        raise NotImplementedError

    def mark_batch_running(self, batch_id: uuid.UUID, current_run_index: int | None, progress: float) -> None:
        raise NotImplementedError

    def mark_batch_failed(self, batch_id: uuid.UUID, error_message: str) -> None:
        raise NotImplementedError

    def get_run_name(self, run_id: uuid.UUID) -> str | None:
        raise NotImplementedError

    def mark_run_running(self, batch_id: uuid.UUID, run_id: uuid.UUID, position: int, total_runs: int) -> None:
        raise NotImplementedError

    def prepare_run_execution(
        self, batch_id: uuid.UUID, run_id: uuid.UUID
    ) -> tuple[str, TrainingConfig, Path, Path, uuid.UUID | None]:
        raise NotImplementedError

    def update_run_progress(
        self, batch_id: uuid.UUID, run_id: uuid.UUID, position: int, total_runs: int, update: ProgressUpdate
    ) -> None:
        raise NotImplementedError

    def save_run_success(self, run_id: uuid.UUID, result_summary: dict[str, Any]) -> None:
        raise NotImplementedError

    def mark_run_failed(self, run_id: uuid.UUID, error_message: str) -> None:
        raise NotImplementedError

    def finalize_batch(self, batch_id: uuid.UUID) -> None:
        raise NotImplementedError

    def get_batch_results_payload(self, batch_id: uuid.UUID, batch_root: Path) -> dict[str, Any]:
        raise NotImplementedError

    def aggregate_batch_results(self, batch_id: uuid.UUID, batch_root: Path) -> None:
        raise NotImplementedError

    def initialize_storage(self, batch_id: uuid.UUID, batch_root: Path) -> None:
        raise NotImplementedError

    def write_batch_metadata(self, batch_id: uuid.UUID, batch_root: Path) -> None:
        raise NotImplementedError


class SqlBatchExperimentTracker(BatchExperimentTracker):
    """SQLModel-backed tracker preserving current persistence behavior."""

    def create_batch(
        self,
        *,
        name: str,
        description: str | None,
        base_config: TrainingConfig,
        sweep_definition: SweepDefinition,
        generated_values: list[int | float],
        user: User,
        batch_root: Path,
    ) -> uuid.UUID:
        storage_root = str(Path("/tmp/walaris_experiments") / "pending_batch")

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

            batch_id = batch.id
            batch.storage_root = str(batch_root)
            session.add(batch)
            session.commit()
            session.refresh(batch)

            runs = []
            for index, value in enumerate(generated_values, start=1):
                config = base_config.with_flat_override(
                    sweep_definition.parameter,
                    int(value) if sweep_definition.value_type == "int" else float(value),
                )
                run_name = f"exp_{index}_{sweep_definition.parameter}_{self._format_value(value)}"
                output_dir = str(batch_root / "experiments" / run_name)

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

            repository.create_runs(runs)
            return batch_id

    def get_run_ids(self, batch_id: uuid.UUID) -> list[uuid.UUID]:
        with Session(engine) as session:
            repository = BatchExperimentRepository(session)
            batch = repository.get_batch(batch_id)
            if not batch:
                raise ValueError(f"Batch experiment {batch_id} not found")
            return [run.id for run in repository.get_runs(batch_id)]

    def mark_batch_running(self, batch_id: uuid.UUID, current_run_index: int | None, progress: float) -> None:
        with Session(engine) as session:
            repository = BatchExperimentRepository(session)
            repository.update_batch_status(
                batch_id,
                JobStatus.RUNNING,
                progress=progress,
                current_run_index=current_run_index,
            )

    def mark_batch_failed(self, batch_id: uuid.UUID, error_message: str) -> None:
        with Session(engine) as session:
            repository = BatchExperimentRepository(session)
            repository.update_batch_status(
                batch_id,
                JobStatus.FAILED,
                progress=0.0,
                error_message=error_message,
                current_run_index=None,
            )

    def get_run_name(self, run_id: uuid.UUID) -> str | None:
        with Session(engine) as session:
            repository = BatchExperimentRepository(session)
            run = repository.get_run(run_id)
            return run.run_name if run else None

    def mark_run_running(self, batch_id: uuid.UUID, run_id: uuid.UUID, position: int, total_runs: int) -> None:
        with Session(engine) as session:
            repository = BatchExperimentRepository(session)
            repository.update_batch_status(
                batch_id,
                JobStatus.RUNNING,
                progress=(position - 1) / total_runs if total_runs else 1.0,
                current_run_index=position,
            )
            repository.update_run_status(run_id, JobStatus.RUNNING, 0.0)

    def prepare_run_execution(
        self, batch_id: uuid.UUID, run_id: uuid.UUID
    ) -> tuple[str, TrainingConfig, Path, Path, uuid.UUID | None]:
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
            training_config = TrainingConfig.from_legacy_flat_dict(config_payload)
            config_path, output_dir = self._prepare_run_paths(batch_id, run.run_name, training_config)

            experiment_repository = ExperimentRepository(session)
            experiment_repository.update_status(experiment.id, JobStatus.RUNNING, 0.0)

            return run.run_name, training_config, config_path, output_dir, run.experiment_id

    def update_run_progress(
        self, batch_id: uuid.UUID, run_id: uuid.UUID, position: int, total_runs: int, update: ProgressUpdate
    ) -> None:
        run_fraction = update.progress / total_runs
        batch_progress = ((position - 1) / total_runs) + run_fraction

        with Session(engine) as session:
            batch_repository = BatchExperimentRepository(session)
            experiment_repository = ExperimentRepository(session)

            batch_repository.update_run_status(run_id, JobStatus.RUNNING, update.progress)
            batch_repository.update_batch_counters(
                batch_id,
                completed_runs=position - 1,
                successful_runs=self._count_runs(batch_id, JobStatus.COMPLETED, session),
                failed_runs=self._count_runs(batch_id, JobStatus.FAILED, session),
                progress=min(batch_progress, 0.999),
                current_run_index=position,
                status=JobStatus.RUNNING,
            )
            run = batch_repository.get_run(run_id)
            if run and run.experiment_id:
                experiment_repository.update_status(
                    run.experiment_id, JobStatus.RUNNING, update.progress, update.message
                )

    def save_run_success(self, run_id: uuid.UUID, result_summary: dict[str, Any]) -> None:
        with Session(engine) as session:
            batch_repository = BatchExperimentRepository(session)
            run = batch_repository.get_run(run_id)
            if not run:
                raise ValueError(f"Batch run {run_id} not found")

            batch_repository.save_run_results(
                run_id,
                aleatoric_auroc=result_summary["aleatoric_auroc"],
                epistemic_auroc=result_summary["epistemic_auroc"],
                train_size=result_summary["train_size"],
                eval_sizes=result_summary["eval_sizes"],
                output_dir=result_summary["results_path"],
                experiment_id=run.experiment_id,
                result_summary=result_summary,
            )

            if run.experiment_id:
                experiment_repository = ExperimentRepository(session)
                from app.domain.models import TrainingResult

                experiment_repository.save_results(
                    run.experiment_id,
                    TrainingResult(
                        aleatoric_auroc=result_summary["aleatoric_auroc"],
                        epistemic_auroc=result_summary["epistemic_auroc"],
                        train_size=result_summary["train_size"],
                        eval_sizes=result_summary["eval_sizes"],
                        best_signals={
                            "one_vs_rest_auroc": result_summary.get("one_vs_rest_auroc", [])
                        },
                        results_path=result_summary["results_path"],
                    ),
                )

    def mark_run_failed(self, run_id: uuid.UUID, error_message: str) -> None:
        with Session(engine) as session:
            batch_repository = BatchExperimentRepository(session)
            run = batch_repository.get_run(run_id)
            batch_repository.update_run_status(
                run_id,
                JobStatus.FAILED,
                progress=run.progress if run else 0.0,
                error_message=error_message,
            )
            if run and run.experiment_id:
                experiment_repository = ExperimentRepository(session)
                experiment_repository.mark_failed(run.experiment_id, error_message)

    def finalize_batch(self, batch_id: uuid.UUID) -> None:
        with Session(engine) as session:
            repository = BatchExperimentRepository(session)
            runs = repository.get_runs(batch_id)
            failed_runs = sum(1 for item in runs if item.status == JobStatus.FAILED)
            successful_runs = sum(1 for item in runs if item.status == JobStatus.COMPLETED)
            final_status = JobStatus.COMPLETED_WITH_ERRORS if failed_runs > 0 else JobStatus.COMPLETED
            repository.update_batch_counters(
                batch_id,
                completed_runs=len(runs),
                successful_runs=successful_runs,
                failed_runs=failed_runs,
                progress=1.0,
                current_run_index=None,
                status=final_status,
            )

    def get_batch_results_payload(self, batch_id: uuid.UUID, batch_root: Path) -> dict[str, Any]:
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
                "plot_json": str(batch_root / "aggregated_results" / "auroc_curves.json"),
                "plot_png": str(batch_root / "aggregated_results" / "auroc_curves.png"),
                "comparison_csv": str(batch_root / "aggregated_results" / "comparison_table.csv"),
                "summary_json": str(batch_root / "aggregated_results" / "summary.json"),
            },
            "summary": summary,
        }

    def aggregate_batch_results(self, batch_id: uuid.UUID, batch_root: Path) -> None:
        with Session(engine) as session:
            repository = BatchExperimentRepository(session)
            batch = repository.get_batch(batch_id)
            runs = repository.get_runs(batch_id)
            if not batch:
                raise ValueError(f"Batch experiment {batch_id} not found")

            aggregated_dir = batch_root / "aggregated_results"
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

    def initialize_storage(self, batch_id: uuid.UUID, batch_root: Path) -> None:
        (batch_root / "experiments").mkdir(parents=True, exist_ok=True)
        (batch_root / "aggregated_results").mkdir(parents=True, exist_ok=True)

    def write_batch_metadata(self, batch_id: uuid.UUID, batch_root: Path) -> None:
        with Session(engine) as session:
            repository = BatchExperimentRepository(session)
            batch = repository.get_batch(batch_id)
            runs = repository.get_runs(batch_id)
            if not batch:
                raise ValueError(f"Batch experiment {batch_id} not found")

            with open(batch_root / "batch_config.yaml", "w") as handle:
                yaml.safe_dump(
                    {
                        "name": batch.name,
                        "description": batch.description,
                        "base_config": yaml.safe_load(batch.base_config_yaml),
                        "sweep_definitions": json.loads(batch.sweep_definitions_json),
                    },
                    handle,
                )

            with open(batch_root / "batch_metadata.json", "w") as handle:
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

    def _prepare_run_paths(
        self, batch_id: uuid.UUID, run_name: str, config: TrainingConfig
    ) -> tuple[Path, Path]:
        run_dir = Path("/tmp/walaris_experiments") / f"batch_{batch_id}" / "experiments" / run_name
        run_dir.mkdir(parents=True, exist_ok=True)

        config_path = run_dir / "config.yaml"
        with open(config_path, "w") as handle:
            yaml.safe_dump(config.to_yaml_dict(), handle)

        return config_path, run_dir

    def _serialize_sweep_definition(
        self, definition: SweepDefinition, generated_values: list[int | float]
    ) -> dict[str, Any]:
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

    def _count_runs(self, batch_id: uuid.UUID, status: JobStatus, session: Session) -> int:
        repository = BatchExperimentRepository(session)
        return sum(1 for run in repository.get_runs(batch_id) if run.status == status)

    def _format_value(self, value: int | float) -> str:
        if isinstance(value, int):
            return str(value)
        if float(value).is_integer():
            return str(int(value))
        return str(value).replace(".", "_")

    def _build_series(self, runs: list[BatchExperimentRun]) -> list[dict[str, Any]]:
        ordered_runs = sorted(
            [run for run in runs if run.swept_value_numeric is not None],
            key=lambda item: item.swept_value_numeric or 0.0,
        )

        series = [
            {
                "metric": "epistemic_auroc",
                "display_name": "Epistemic AUROC (Aggregated)",
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
                "display_name": "Aleatoric AUROC (Aggregated)",
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

        signal_names_set = set()
        for run in ordered_runs:
            if run.result_summary_json:
                try:
                    summary = json.loads(run.result_summary_json)
                    one_vs_rest = summary.get("one_vs_rest_auroc", [])
                    for item in one_vs_rest:
                        signal_names_set.add(item.get("signal"))
                except (json.JSONDecodeError, KeyError):
                    continue

        for signal_name in sorted(signal_names_set):
            if not signal_name:
                continue

            aleatoric_points = []
            epistemic_points = []

            for run in ordered_runs:
                if not run.result_summary_json:
                    continue

                try:
                    summary = json.loads(run.result_summary_json)
                    one_vs_rest = summary.get("one_vs_rest_auroc", [])

                    for item in one_vs_rest:
                        if item.get("signal") == signal_name:
                            alea_auroc = item.get("aleatoric_like_auroc")
                            epis_auroc = item.get("epistemic_like_auroc")

                            if alea_auroc is not None and not (
                                isinstance(alea_auroc, float) and (alea_auroc != alea_auroc)
                            ):
                                aleatoric_points.append(
                                    {
                                        "x": run.swept_value_numeric,
                                        "y": alea_auroc,
                                        "run_index": run.run_index,
                                        "status": run.status.value,
                                    }
                                )

                            if epis_auroc is not None and not (
                                isinstance(epis_auroc, float) and (epis_auroc != epis_auroc)
                            ):
                                epistemic_points.append(
                                    {
                                        "x": run.swept_value_numeric,
                                        "y": epis_auroc,
                                        "run_index": run.run_index,
                                        "status": run.status.value,
                                    }
                                )
                            break
                except (json.JSONDecodeError, KeyError):
                    continue

            if aleatoric_points:
                series.append(
                    {
                        "metric": f"{signal_name}_aleatoric",
                        "display_name": f"{signal_name} (Aleatoric)",
                        "points": aleatoric_points,
                    }
                )

            if epistemic_points:
                series.append(
                    {
                        "metric": f"{signal_name}_epistemic",
                        "display_name": f"{signal_name} (Epistemic)",
                        "points": epistemic_points,
                    }
                )

        return series

    def _best_run_payload(
        self, runs: list[BatchExperimentRun], metric_name: str
    ) -> dict[str, Any] | None:
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


class MlflowStyleBatchExperimentTracker(BatchExperimentTracker):
    """Skeleton tracker showing where MLflow-style logging hooks would live."""

    def __init__(self, delegate: BatchExperimentTracker | None = None):
        self.delegate = delegate or SqlBatchExperimentTracker()
        self._batch_runs: dict[uuid.UUID, list[uuid.UUID]] = {}
        self._batch_names: dict[uuid.UUID, str] = {}
        self._run_names: dict[uuid.UUID, str] = {}
        self._batch_roots: dict[uuid.UUID, Path] = {}
        self._run_output_dirs: dict[uuid.UUID, Path] = {}

    def create_batch(
        self,
        *,
        name: str,
        description: str | None,
        base_config: TrainingConfig,
        sweep_definition: SweepDefinition,
        generated_values: list[int | float],
        user: User,
        batch_root: Path,
    ) -> uuid.UUID:
        batch_id = self.delegate.create_batch(
            name=name,
            description=description,
            base_config=base_config,
            sweep_definition=sweep_definition,
            generated_values=generated_values,
            user=user,
            batch_root=batch_root,
        )
        self._batch_runs[batch_id] = self.delegate.get_run_ids(batch_id)
        self._batch_names[batch_id] = name
        self._batch_roots[batch_id] = batch_root
        self._log_batch_created(batch_id, name, description, base_config, sweep_definition, generated_values)
        return batch_id

    def get_run_ids(self, batch_id: uuid.UUID) -> list[uuid.UUID]:
        run_ids = self.delegate.get_run_ids(batch_id)
        self._batch_runs[batch_id] = run_ids
        return run_ids

    def mark_batch_running(self, batch_id: uuid.UUID, current_run_index: int | None, progress: float) -> None:
        self.delegate.mark_batch_running(batch_id, current_run_index, progress)
        self._log_batch_status(batch_id, "RUNNING", progress, current_run_index=current_run_index)

    def mark_batch_failed(self, batch_id: uuid.UUID, error_message: str) -> None:
        self.delegate.mark_batch_failed(batch_id, error_message)
        self._log_batch_status(batch_id, "FAILED", 1.0, error_message=error_message)

    def get_run_name(self, run_id: uuid.UUID) -> str | None:
        run_name = self.delegate.get_run_name(run_id)
        if run_name is not None:
            self._run_names[run_id] = run_name
        return run_name

    def mark_run_running(self, batch_id: uuid.UUID, run_id: uuid.UUID, position: int, total_runs: int) -> None:
        self.delegate.mark_run_running(batch_id, run_id, position, total_runs)
        self._log_run_status(batch_id, run_id, "RUNNING", 0.0, position=position, total_runs=total_runs)

    def prepare_run_execution(
        self, batch_id: uuid.UUID, run_id: uuid.UUID
    ) -> tuple[str, TrainingConfig, Path, Path, uuid.UUID | None]:
        run_name, training_config, config_path, output_dir, experiment_id = self.delegate.prepare_run_execution(
            batch_id, run_id
        )
        self._run_names[run_id] = run_name
        self._run_output_dirs[run_id] = output_dir
        self._log_run_prepared(batch_id, run_id, run_name, training_config, config_path, output_dir, experiment_id)
        return run_name, training_config, config_path, output_dir, experiment_id

    def update_run_progress(
        self, batch_id: uuid.UUID, run_id: uuid.UUID, position: int, total_runs: int, update: ProgressUpdate
    ) -> None:
        self.delegate.update_run_progress(batch_id, run_id, position, total_runs, update)
        self._log_run_status(
            batch_id,
            run_id,
            "RUNNING",
            update.progress,
            position=position,
            total_runs=total_runs,
            message=update.message,
        )

    def save_run_success(self, run_id: uuid.UUID, result_summary: dict[str, Any]) -> None:
        self.delegate.save_run_success(run_id, result_summary)
        self._log_run_result(run_id, result_summary)

    def mark_run_failed(self, run_id: uuid.UUID, error_message: str) -> None:
        self.delegate.mark_run_failed(run_id, error_message)
        self._log_run_failure(run_id, error_message)

    def finalize_batch(self, batch_id: uuid.UUID) -> None:
        self.delegate.finalize_batch(batch_id)
        self._log_batch_finalized(batch_id)

    def get_batch_results_payload(self, batch_id: uuid.UUID, batch_root: Path) -> dict[str, Any]:
        return self.delegate.get_batch_results_payload(batch_id, batch_root)

    def aggregate_batch_results(self, batch_id: uuid.UUID, batch_root: Path) -> None:
        self.delegate.aggregate_batch_results(batch_id, batch_root)
        self._log_batch_artifacts(batch_id, batch_root)

    def initialize_storage(self, batch_id: uuid.UUID, batch_root: Path) -> None:
        self.delegate.initialize_storage(batch_id, batch_root)
        self._batch_roots[batch_id] = batch_root

    def write_batch_metadata(self, batch_id: uuid.UUID, batch_root: Path) -> None:
        self.delegate.write_batch_metadata(batch_id, batch_root)
        self._log_batch_metadata(batch_id, batch_root)

    def _log_batch_created(
        self,
        batch_id: uuid.UUID,
        name: str,
        description: str | None,
        base_config: TrainingConfig,
        sweep_definition: SweepDefinition,
        generated_values: list[int | float],
    ) -> None:
        logger.info(
            "🧪 [MLflowSkeleton] create batch run=%s name=%s description=%s sweep=%s values=%s params=%s",
            batch_id,
            name,
            description,
            sweep_definition.parameter,
            generated_values,
            base_config.to_flat_dict(),
        )

    def _log_batch_status(
        self,
        batch_id: uuid.UUID,
        status: str,
        progress: float,
        *,
        current_run_index: int | None = None,
        error_message: str | None = None,
    ) -> None:
        logger.info(
            "🧪 [MLflowSkeleton] batch status batch_id=%s status=%s progress=%.3f current_run_index=%s error=%s",
            batch_id,
            status,
            progress,
            current_run_index,
            error_message,
        )

    def _log_run_prepared(
        self,
        batch_id: uuid.UUID,
        run_id: uuid.UUID,
        run_name: str,
        training_config: TrainingConfig,
        config_path: Path,
        output_dir: Path,
        experiment_id: uuid.UUID | None,
    ) -> None:
        logger.info(
            "🧪 [MLflowSkeleton] prepare child run batch_id=%s run_id=%s run_name=%s experiment_id=%s config=%s output=%s params=%s",
            batch_id,
            run_id,
            run_name,
            experiment_id,
            config_path,
            output_dir,
            training_config.to_flat_dict(),
        )

    def _log_run_status(
        self,
        batch_id: uuid.UUID,
        run_id: uuid.UUID,
        status: str,
        progress: float,
        *,
        position: int | None = None,
        total_runs: int | None = None,
        message: str | None = None,
    ) -> None:
        logger.info(
            "🧪 [MLflowSkeleton] child run status batch_id=%s run_id=%s run_name=%s status=%s progress=%.3f position=%s/%s message=%s",
            batch_id,
            run_id,
            self._run_names.get(run_id),
            status,
            progress,
            position,
            total_runs,
            message,
        )

    def _log_run_result(self, run_id: uuid.UUID, result_summary: dict[str, Any]) -> None:
        logger.info(
            "🧪 [MLflowSkeleton] child run metrics run_id=%s run_name=%s metrics=%s artifacts_dir=%s",
            run_id,
            self._run_names.get(run_id),
            {
                "aleatoric_auroc": result_summary.get("aleatoric_auroc"),
                "epistemic_auroc": result_summary.get("epistemic_auroc"),
                "train_size": result_summary.get("train_size"),
            },
            result_summary.get("results_path") or self._run_output_dirs.get(run_id),
        )

    def _log_run_failure(self, run_id: uuid.UUID, error_message: str) -> None:
        logger.info(
            "🧪 [MLflowSkeleton] child run failed run_id=%s run_name=%s error=%s",
            run_id,
            self._run_names.get(run_id),
            error_message,
        )

    def _log_batch_finalized(self, batch_id: uuid.UUID) -> None:
        logger.info(
            "🧪 [MLflowSkeleton] finalize batch batch_id=%s run_count=%s batch_root=%s",
            batch_id,
            len(self._batch_runs.get(batch_id, [])),
            self._batch_roots.get(batch_id),
        )

    def _log_batch_artifacts(self, batch_id: uuid.UUID, batch_root: Path) -> None:
        logger.info(
            "🧪 [MLflowSkeleton] batch artifacts batch_id=%s batch_root=%s aggregated_dir=%s",
            batch_id,
            batch_root,
            batch_root / "aggregated_results",
        )

    def _log_batch_metadata(self, batch_id: uuid.UUID, batch_root: Path) -> None:
        logger.info(
            "🧪 [MLflowSkeleton] batch metadata batch_id=%s metadata_path=%s",
            batch_id,
            batch_root / "batch_metadata.json",
        )


class BatchExperimentService:
    """Service responsible for batch creation and execution."""

    MAX_RUNS = 100

    def __init__(
        self,
        executor: TrainingExecutor,
        tracker: BatchExperimentTracker | None = None,
    ):
        self.executor = executor
        self.tracker = tracker or SqlBatchExperimentTracker()
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
        
        # Validate parameter combinations before creating batch
        self._validate_sweep_parameters(base_config, sweep_definition, generated_values)
        
        batch_id = self.tracker.create_batch(
            name=name,
            description=description,
            base_config=base_config,
            sweep_definition=sweep_definition,
            generated_values=generated_values,
            user=user,
            batch_root=self._batch_root_placeholder(),
        )

        batch_root = self._batch_root(batch_id)
        self.tracker.initialize_storage(batch_id, batch_root)
        self.tracker.write_batch_metadata(batch_id, batch_root)
        return batch_id

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
            run_ids = self.tracker.get_run_ids(batch_id)
            logger.info(f"📊 Found {len(run_ids)} runs to execute for batch {batch_id}")

            if not run_ids:
                self.tracker.finalize_batch(batch_id)
                return

            self.tracker.mark_batch_running(batch_id, current_run_index=1, progress=0.0)

            total_runs = len(run_ids)
            logger.info(f"▶️ Beginning execution of {total_runs} experiments")

            for position, run_id in enumerate(run_ids, start=1):
                run_name = self.tracker.get_run_name(run_id)
                if not run_name:
                    logger.error(f"❌ Run {run_id} not found, skipping")
                    continue

                logger.info(f"🔄 Starting run {position}/{total_runs}: {run_name}")
                self.tracker.mark_run_running(batch_id, run_id, position, total_runs)

                await self._run_single_batch_experiment(batch_id, run_id, position, total_runs)
                logger.info(f"✅ Completed run {position}/{total_runs}: {run_name}")
                self.tracker.aggregate_batch_results(batch_id, self._batch_root(batch_id))

            self.tracker.finalize_batch(batch_id)
            self.tracker.aggregate_batch_results(batch_id, self._batch_root(batch_id))
        except Exception as exc:
            self.tracker.mark_batch_failed(batch_id, str(exc))
        finally:
            self._running_batches.pop(batch_id, None)

    async def _run_single_batch_experiment(
        self, batch_id: uuid.UUID, run_id: uuid.UUID, position: int, total_runs: int
    ) -> None:
        """Execute one child experiment and persist its results."""
        run_name, _training_config, config_path, output_dir, _experiment_id = self.tracker.prepare_run_execution(
            batch_id, run_id
        )

        def progress_callback(update: ProgressUpdate) -> None:
            self.tracker.update_run_progress(batch_id, run_id, position, total_runs, update)

        try:
            logger.info(f"🎯 Executing training for run {position}/{total_runs}: {run_name}")
            logger.info(f"   Config: {config_path}")
            logger.info(f"   Output: {output_dir}")
            result = await self.executor.execute(config_path, output_dir, progress_callback)
            logger.info(f"✅ Training completed for run {position}/{total_runs}")

            # Build summary payload with complete per-signal AUROC data
            summary_payload = {
                "aleatoric_auroc": result.aleatoric_auroc,
                "epistemic_auroc": result.epistemic_auroc,
                "train_size": result.train_size,
                "eval_sizes": result.eval_sizes,
                "results_path": result.results_path,
                # Include complete 7×2 per-signal AUROC structure for visualization
                "one_vs_rest_auroc": result.best_signals.get("one_vs_rest_auroc", []),
            }

            self.tracker.save_run_success(run_id, summary_payload)
        except Exception as exc:
            logger.error(f"❌ Training failed for run {position}/{total_runs}: {str(exc)}")
            logger.exception("Full traceback:")
            self.tracker.mark_run_failed(run_id, str(exc))

    def get_batch_results(self, batch_id: uuid.UUID) -> dict[str, Any]:
        """Return aggregated results for a batch."""
        return self.tracker.get_batch_results_payload(batch_id, self._batch_root(batch_id))

    def _aggregate_batch_results(self, batch_id: uuid.UUID) -> None:
        """Aggregate batch results into summary and CSV artifacts."""
        self.tracker.aggregate_batch_results(batch_id, self._batch_root(batch_id))

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
        return base_config.with_flat_override(
            definition.parameter,
            int(value) if definition.value_type == "int" else float(value),
        )

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

    def _batch_root_placeholder(self) -> Path:
        """Temporary placeholder before batch id exists."""
        return Path("/tmp/walaris_experiments") / "pending_batch"

    def _build_series(self, runs: list[BatchExperimentRun]) -> list[dict[str, Any]]:
        """Build normalized plotting series including per-signal AUROC data."""
        ordered_runs = sorted(
            [run for run in runs if run.swept_value_numeric is not None],
            key=lambda item: item.swept_value_numeric or 0.0,
        )

        # Start with aggregated metrics (backward compatibility)
        series = [
            {
                "metric": "epistemic_auroc",
                "display_name": "Epistemic AUROC (Aggregated)",
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
                "display_name": "Aleatoric AUROC (Aggregated)",
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

        # Extract per-signal AUROC from result_summary_json
        # Collect all unique signal names across runs
        signal_names_set = set()
        for run in ordered_runs:
            if run.result_summary_json:
                try:
                    summary = json.loads(run.result_summary_json)
                    one_vs_rest = summary.get("one_vs_rest_auroc", [])
                    for item in one_vs_rest:
                        signal_names_set.add(item.get("signal"))
                except (json.JSONDecodeError, KeyError):
                    continue

        # Build series for each signal
        for signal_name in sorted(signal_names_set):
            if not signal_name:
                continue
                
            # Aleatoric AUROC for this signal
            aleatoric_points = []
            epistemic_points = []
            
            for run in ordered_runs:
                if not run.result_summary_json:
                    continue
                    
                try:
                    summary = json.loads(run.result_summary_json)
                    one_vs_rest = summary.get("one_vs_rest_auroc", [])
                    
                    for item in one_vs_rest:
                        if item.get("signal") == signal_name:
                            alea_auroc = item.get("aleatoric_like_auroc")
                            epis_auroc = item.get("epistemic_like_auroc")
                            
                            if alea_auroc is not None and not (isinstance(alea_auroc, float) and (alea_auroc != alea_auroc)):  # Check for NaN
                                aleatoric_points.append({
                                    "x": run.swept_value_numeric,
                                    "y": alea_auroc,
                                    "run_index": run.run_index,
                                    "status": run.status.value,
                                })
                            
                            if epis_auroc is not None and not (isinstance(epis_auroc, float) and (epis_auroc != epis_auroc)):  # Check for NaN
                                epistemic_points.append({
                                    "x": run.swept_value_numeric,
                                    "y": epis_auroc,
                                    "run_index": run.run_index,
                                    "status": run.status.value,
                                })
                            break
                except (json.JSONDecodeError, KeyError):
                    continue
            
            # Add series for this signal if we have data
            if aleatoric_points:
                series.append({
                    "metric": f"{signal_name}_aleatoric",
                    "display_name": f"{signal_name} (Aleatoric)",
                    "points": aleatoric_points,
                })
            
            if epistemic_points:
                series.append({
                    "metric": f"{signal_name}_epistemic",
                    "display_name": f"{signal_name} (Epistemic)",
                    "points": epistemic_points,
                })

        return series

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

    def _validate_sweep_parameters(
        self,
        base_config: TrainingConfig,
        sweep_definition: SweepDefinition,
        generated_values: list[int | float],
    ) -> None:
        """
        Validate that sweep parameter values won't cause data sampling errors.
        
        Raises:
            ValueError: If parameter combinations are invalid
        """
        # Only validate for under_train_per_class sweeps
        if sweep_definition.parameter != "under_train_per_class":
            return
        
        # Get base config values
        eval_per_group = base_config.data.eval_per_group or 600
        regular_train_per_class = base_config.data.regular_train_per_class or 300
        under_supported_classes_str = base_config.data.under_supported_classes or "3,5"
        under_supported_classes = [int(x.strip()) for x in under_supported_classes_str.split(",") if x.strip()]
        num_under_classes = len(under_supported_classes)
        num_regular_classes = 10 - num_under_classes
        
        # CIFAR-10N statistics (worse_label noise)
        samples_per_class = 5000
        noise_rate = 0.40
        estimated_clean_per_class = int(samples_per_class * (1 - noise_rate))  # ~3000
        estimated_noisy_per_class = int(samples_per_class * noise_rate)  # ~2000
        
        # Check epistemic eval pool (clean samples from under-supported classes)
        max_under_train = max(generated_values)
        epistemic_needed = max_under_train + eval_per_group
        
        if epistemic_needed > estimated_clean_per_class:
            raise ValueError(
                f"❌ Epistemic evaluation pool will be empty!\n\n"
                f"Under-supported classes need {epistemic_needed} clean samples "
                f"({max_under_train} training + {eval_per_group} eval), "
                f"but only ~{estimated_clean_per_class} available per class.\n\n"
                f"Solutions:\n"
                f"  1. Reduce max under_train_per_class to {estimated_clean_per_class - eval_per_group}\n"
                f"  2. Reduce eval_per_group to {estimated_clean_per_class - max_under_train}\n"
                f"  3. Use fewer under-supported classes (currently {num_under_classes})"
            )
        
        # Check aleatoric eval pool (noisy samples from regular classes)
        # After training uses regular_train_per_class samples, we need eval_per_group noisy samples total
        noisy_per_regular_class_needed = eval_per_group / num_regular_classes
        # Assume training uses proportional mix of clean/noisy
        noisy_used_in_training = regular_train_per_class * noise_rate
        noisy_remaining = estimated_noisy_per_class - noisy_used_in_training
        
        if noisy_per_regular_class_needed > noisy_remaining:
            raise ValueError(
                f"❌ Aleatoric evaluation pool will be empty!\n\n"
                f"Need {eval_per_group} noisy samples total from {num_regular_classes} regular classes "
                f"(~{noisy_per_regular_class_needed:.0f} per class), but after training uses "
                f"{regular_train_per_class} samples per class, only ~{noisy_remaining:.0f} noisy samples remain.\n\n"
                f"Solutions:\n"
                f"  1. Reduce eval_per_group from {eval_per_group} to {int(noisy_remaining * num_regular_classes)}\n"
                f"  2. Reduce regular_train_per_class from {regular_train_per_class} to "
                f"{int((estimated_noisy_per_class - noisy_per_regular_class_needed) / noise_rate)}"
            )
        
        # Check clean eval pool (clean samples from regular classes)
        clean_per_regular_class_needed = eval_per_group / num_regular_classes
        clean_used_in_training = regular_train_per_class * (1 - noise_rate)
        clean_remaining = estimated_clean_per_class - clean_used_in_training
        
        if clean_per_regular_class_needed > clean_remaining:
            raise ValueError(
                f"❌ Clean evaluation pool will be empty!\n\n"
                f"Need {eval_per_group} clean samples total from {num_regular_classes} regular classes "
                f"(~{clean_per_regular_class_needed:.0f} per class), but after training uses "
                f"{regular_train_per_class} samples per class, only ~{clean_remaining:.0f} clean samples remain.\n\n"
                f"Solutions:\n"
                f"  1. Reduce eval_per_group from {eval_per_group} to {int(clean_remaining * num_regular_classes)}\n"
                f"  2. Reduce regular_train_per_class from {regular_train_per_class} to "
                f"{int((estimated_clean_per_class - clean_per_regular_class_needed) / (1 - noise_rate))}"
            )
        
        logger.info(
            f"✅ Parameter validation passed:\n"
            f"   - Epistemic pool: {epistemic_needed} <= {estimated_clean_per_class} per under-class\n"
            f"   - Aleatoric pool: {noisy_per_regular_class_needed:.0f} <= {noisy_remaining:.0f} noisy per regular class\n"
            f"   - Clean pool: {clean_per_regular_class_needed:.0f} <= {clean_remaining:.0f} clean per regular class"
        )

# Made with Bob
