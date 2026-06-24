"""Finalize failed experiments from on-disk artifacts (no re-training)."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any, Literal

from sqlmodel import Session, select

from app.core.ml_bootstrap import ensure_ml_paths
from app.core.runtime_paths import resolve_experiment_results_dir
from app.domain.models import TrainingResult
from app.repositories.experiment_repository import ExperimentRepository
from app.tables import JobStatus, UncertaintyExperiment

logger = logging.getLogger(__name__)

RecoveryTier = Literal["db_sync", "zwischen_finalize", "partial", "none"]


@dataclass
class RecoverabilityEntry:
    id: str
    name: str
    status: str
    error_message: str | None
    tier: RecoveryTier
    missing: list[str] = field(default_factory=list)
    zwischen_stages: list[str] = field(default_factory=list)
    error_hint: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "error_message": self.error_message,
            "tier": self.tier,
            "missing": self.missing,
            "zwischen_stages": self.zwischen_stages,
            "error_hint": self.error_hint,
        }


@dataclass
class RecoverBatchResult:
    recovered: int = 0
    skipped: int = 0
    errors: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "recovered": self.recovered,
            "skipped": self.skipped,
            "errors": self.errors,
        }


def _training_result_from_summary(summary: dict[str, Any], results_path: str) -> TrainingResult:
    """Mirror DirectExecutor._read_results mapping."""
    one_vs_rest_auroc = summary.get("one_vs_rest_auroc", [])
    best_signals = {"one_vs_rest_auroc": one_vs_rest_auroc}

    def _max_auroc(key: str) -> float | None:
        vals: list[float] = []
        for row in one_vs_rest_auroc:
            v = row.get(key)
            if v is None:
                continue
            try:
                fv = float(v)
                if fv == fv:
                    vals.append(fv)
            except (TypeError, ValueError):
                continue
        return max(vals) if vals else None

    return TrainingResult(
        aleatoric_auroc=_max_auroc("aleatoric_like_auroc"),
        epistemic_auroc=_max_auroc("epistemic_like_auroc"),
        train_size=int(summary.get("train_size") or 0),
        eval_sizes=summary.get("eval_sizes") or {},
        best_signals=best_signals,
        results_path=results_path,
    )


class RunRecoveryService:
    """Assess and recover failed runs from disk artifacts."""

    def __init__(self, session: Session):
        self.session = session
        self.repository = ExperimentRepository(session)
        ensure_ml_paths()

    def _results_dir_for(self, experiment: UncertaintyExperiment):
        from pathlib import Path

        return resolve_experiment_results_dir(
            experiment.id,
            results_path=experiment.results_path,
        )

    def assess_experiment(self, experiment: UncertaintyExperiment) -> RecoverabilityEntry:
        from uqlab.evaluation.pipeline.run_recovery import assess_run_recovery

        results_dir = self._results_dir_for(experiment)
        report = assess_run_recovery(results_dir)
        return RecoverabilityEntry(
            id=str(experiment.id),
            name=experiment.name,
            status=experiment.status.value if hasattr(experiment.status, "value") else str(experiment.status),
            error_message=experiment.error_message,
            tier=report.tier,
            missing=report.missing,
            zwischen_stages=report.zwischen_stages,
            error_hint=report.error_hint,
        )

    def list_recoverability(
        self,
        *,
        status: JobStatus | None = None,
        skip: int = 0,
        limit: int = 500,
    ) -> list[RecoverabilityEntry]:
        statement = select(UncertaintyExperiment).offset(skip).limit(limit)
        if status is not None:
            statement = statement.where(UncertaintyExperiment.status == status)
        experiments = list(self.session.exec(statement).all())
        return [self.assess_experiment(exp) for exp in experiments]

    def recover_experiment(
        self,
        experiment_id: uuid.UUID,
        *,
        tier: RecoveryTier | None = None,
        seed: int = 42,
        device: str = "cpu",
    ) -> dict[str, Any]:
        from uqlab.evaluation.pipeline.run_recovery import assess_run_recovery, recover_run_on_disk

        experiment = self.repository.get(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        results_dir = self._results_dir_for(experiment)
        report = assess_run_recovery(results_dir)
        if tier is not None and report.tier != tier:
            raise ValueError(
                f"Experiment tier is {report.tier!r}, expected {tier!r}"
            )
        if report.tier in ("partial", "none"):
            raise ValueError(
                f"Run not recoverable (tier={report.tier!r}, missing={report.missing})"
            )

        experiment_dir = results_dir.parent
        summary = recover_run_on_disk(
            results_dir,
            experiment_dir=experiment_dir,
            seed=seed,
            device=device,
        )
        training_result = _training_result_from_summary(summary, str(results_dir))
        self.repository.save_results(experiment_id, training_result)

        return {
            "id": str(experiment_id),
            "status": "completed",
            "tier": report.tier,
            "recovered_from_zwischen": bool(summary.get("recovered_from_zwischen")),
            "aleatoric_auroc": training_result.aleatoric_auroc,
            "epistemic_auroc": training_result.epistemic_auroc,
        }

    def recover_batch(
        self,
        *,
        status: JobStatus = JobStatus.FAILED,
        tier: RecoveryTier = "zwischen_finalize",
        seed: int = 42,
        device: str = "cpu",
    ) -> RecoverBatchResult:
        result = RecoverBatchResult()
        entries = self.list_recoverability(status=status, limit=10_000)
        for entry in entries:
            if entry.tier != tier:
                result.skipped += 1
                continue
            try:
                self.recover_experiment(
                    uuid.UUID(entry.id),
                    tier=tier,
                    seed=seed,
                    device=device,
                )
                result.recovered += 1
            except Exception as exc:
                logger.exception("Failed to recover experiment %s", entry.id)
                result.errors.append({"id": entry.id, "error": str(exc)})
        return result
