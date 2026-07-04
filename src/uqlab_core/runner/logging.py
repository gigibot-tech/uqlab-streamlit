"""Stdout reporting and disk log capture for the experiment runner."""

from __future__ import annotations

import sys
import traceback
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

import torch

from uqlab_core.run_artifacts import WrittenArtifacts

EXPERIMENT_LOG_FILENAME = "experiment.log"


class _TeeStream:
    """Write to a log file and the original stream (tqdm, print, warnings)."""

    def __init__(self, original, tee_target) -> None:
        self._original = original
        self._tee = tee_target

    def write(self, data: str) -> int:
        if not data:
            return 0
        self._original.write(data)
        self._tee.write(data)
        self._tee.flush()
        return len(data)

    def flush(self) -> None:
        self._original.flush()
        self._tee.flush()

    def fileno(self) -> int:
        return self._original.fileno()

    def isatty(self) -> bool:
        return getattr(self._original, "isatty", lambda: False)()

    @property
    def encoding(self) -> str:
        return getattr(self._original, "encoding", "utf-8")


def experiment_log_path(results_dir: Path) -> Path:
    """Path to the full run log under a results directory."""
    return Path(results_dir) / EXPERIMENT_LOG_FILENAME


def read_experiment_log(
    results_dir: Path,
    *,
    tail_chars: int | None = 32_000,
) -> str | None:
    """Return log text, optionally truncated to the last *tail_chars* characters."""
    path = experiment_log_path(results_dir)
    if not path.is_file():
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    if tail_chars is not None and len(text) > tail_chars:
        return text[-tail_chars:]
    return text


def infer_experiment_id(*, results_dir: Path, config_path: Path | None = None) -> str | None:
    """Best-effort experiment UUID from ``…/<id>/results`` or ``…/<id>/config.yaml``."""
    results_dir = Path(results_dir)
    if results_dir.name == "results":
        parent = results_dir.parent
        if (parent / "config.yaml").is_file():
            return parent.name
    if config_path is not None:
        parent = Path(config_path).parent
        if (parent / "config.yaml").is_file():
            return parent.name
    return None


@contextmanager
def capture_experiment_log(
    results_dir: Path,
    *,
    experiment_id: str | None = None,
    config_path: Path | None = None,
) -> Iterator[Path]:
    """
    Tee stdout/stderr to ``results_dir/experiment.log`` for the duration.

    Each invocation appends a new section (run start banner → output → status footer).
    """
    results_dir = Path(results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    log_path = experiment_log_path(results_dir)
    run_id = experiment_id or infer_experiment_id(
        results_dir=results_dir, config_path=config_path
    )
    started = datetime.now(timezone.utc)

    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write("\n")
        log_file.write("=" * 80 + "\n")
        log_file.write(f"EXPERIMENT LOG — started {started.isoformat()}\n")
        if run_id:
            log_file.write(f"Experiment ID: {run_id}\n")
        if config_path is not None:
            log_file.write(f"Config: {Path(config_path).resolve()}\n")
        log_file.write(f"Results directory: {results_dir.resolve()}\n")
        log_file.write("=" * 80 + "\n")
        log_file.flush()

        out_tee = _TeeStream(sys.stdout, log_file)
        err_tee = _TeeStream(sys.stderr, log_file)
        old_out, old_err = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = out_tee, err_tee  # type: ignore[assignment]
        status = "completed"
        try:
            yield log_path
        except BaseException:
            status = "failed"
            log_file.write("\n")
            log_file.write(traceback.format_exc())
            log_file.flush()
            raise
        finally:
            sys.stdout, sys.stderr = old_out, old_err
            ended = datetime.now(timezone.utc)
            log_file.write("\n")
            log_file.write("=" * 80 + "\n")
            log_file.write(f"EXPERIMENT LOG — {status} {ended.isoformat()}\n")
            log_file.write("=" * 80 + "\n")
            log_file.flush()


def _format_auroc_console(value: object, skip_reason: str | None) -> str:
    if value is None:
        if skip_reason:
            return f"— (skipped: {skip_reason.replace('_', ' ')})"
        return "—"
    try:
        return f"{float(value):.4f}"
    except (TypeError, ValueError):
        return "—"


def _unpack_auroc_row(row: tuple) -> tuple[str, Any, Any, Any | None]:
    name, alea, epis = row[0], row[1], row[2]
    ood = row[3] if len(row) > 3 else None
    return name, alea, epis, ood


def log_run_data_context(
    *,
    device: torch.device,
    results_dir: Path,
    train_dataset,
    clean_eval_pack: dict,
    aleatoric_eval_pack: dict,
    epistemic_eval_pack: dict,
    ood_eval_pack: dict | None,
) -> None:
    """Log device, paths, and eval group sizes after data prep."""
    print(f"Using device: {device}")
    print(f"Results directory: {results_dir}")
    print(f"Train samples: {len(train_dataset)}")
    print(
        "Eval groups: "
        f"clean={len(clean_eval_pack['features'])}, "
        f"aleatoric_like={len(aleatoric_eval_pack['features'])}, "
        f"epistemic_like={len(epistemic_eval_pack['features'])}, "
        f"ood_like={len(ood_eval_pack['features']) if ood_eval_pack is not None else 0}"
    )


def log_zwischen_dir(results_dir: Path) -> None:
    print(f"✅ Zwischenergebnisse: {results_dir / 'zwischen'}/")


def log_auroc_by_family(
    *,
    auroc_rows: list[tuple],
    clf_rows: list[tuple[str, float]],
    alea_skip: str | None,
    epis_skip: str | None,
    ood_skip: str | None,
    eval_group_labels: torch.Tensor,
) -> None:
    """Print AUROC tables grouped by signal family."""
    from uqlab_core.evaluation.signals.registry import METRICS

    def _auroc_rows_for_family(family: str) -> list[tuple[str, Any, Any, Any | None]]:
        ids = {mid for mid, metric in METRICS.items() if metric.family == family}
        return [_unpack_auroc_row(row) for row in auroc_rows if row[0] in ids]

    print("\n" + "=" * 70)
    print("ATTRIBUTION-BASED SIGNALS (DualXDA / EK-FAC)")
    print("=" * 70)
    attr_rows = _auroc_rows_for_family("attribution")
    for name, alea_auc, epis_auc, ood_auc in sorted(
        attr_rows,
        key=lambda row: max(v for v in row[1:] if v is not None) if any(v is not None for v in row[1:]) else 0,
        reverse=True,
    ):
        ood_part = (
            f", ood={_format_auroc_console(ood_auc, ood_skip)}"
            if ood_auc is not None
            else ""
        )
        print(
            f"  {name:<30} aleatoric={_format_auroc_console(alea_auc, alea_skip)}, "
            f"epistemic={_format_auroc_console(epis_auc, epis_skip)}{ood_part}"
        )

    print("\n" + "=" * 70)
    print("LOGIT-BASED SIGNALS (via Representer Theorem)")
    print("=" * 70)
    logit_rows = _auroc_rows_for_family("logit")
    for name, alea_auc, epis_auc, ood_auc in sorted(
        logit_rows,
        key=lambda row: max(v for v in row[1:] if v is not None) if any(v is not None for v in row[1:]) else 0,
        reverse=True,
    ):
        ood_part = (
            f", ood={_format_auroc_console(ood_auc, ood_skip)}"
            if ood_auc is not None
            else ""
        )
        print(
            f"  {name:<30} aleatoric={_format_auroc_console(alea_auc, alea_skip)}, "
            f"epistemic={_format_auroc_console(epis_auc, epis_skip)}{ood_part}"
        )

    print("\n" + "=" * 70)
    print("PREDICTIVE UNCERTAINTY BASELINE")
    print("=" * 70)
    pred_rows = _auroc_rows_for_family("predictive")
    for name, alea_auc, epis_auc, ood_auc in pred_rows:
        ood_part = (
            f", ood={_format_auroc_console(ood_auc, ood_skip)}"
            if ood_auc is not None
            else ""
        )
        print(
            f"  {name:<30} aleatoric={_format_auroc_console(alea_auc, alea_skip)}, "
            f"epistemic={_format_auroc_console(epis_auc, epis_skip)}{ood_part}"
        )

    num_groups = int(eval_group_labels.max().item()) + 1 if len(eval_group_labels) else 3
    print(f"\n{num_groups}-way macro-F1:")
    for name, score in clf_rows:
        print(f"  {name}: {score:.4f}")


def log_run_complete(
    written: WrittenArtifacts,
    *,
    results_dir: Path,
    eval_summary: dict,
    summary: dict,
) -> None:
    """List all artifact paths in write order and print AUROC tables."""
    one_vs_rest = eval_summary.get("one_vs_rest_auroc") or []
    alea_skip = one_vs_rest[0].get("aleatoric_skip_reason") if one_vs_rest else None
    epis_skip = one_vs_rest[0].get("epistemic_skip_reason") if one_vs_rest else None
    ood_skip = one_vs_rest[0].get("ood_skip_reason") if one_vs_rest else None

    try:
        from uqlab_core.run_artifacts import metrics_row_from_run, print_run_metrics_summary

        print("\n" + "=" * 70)
        print("SIGNAL MEANS & AUROC (all uncertainties)")
        print("=" * 70)
        print_run_metrics_summary(metrics_row_from_run(results_dir))
    except ImportError:
        pass

    auroc_rows = eval_summary.get("auroc_rows") or []
    clf_rows = eval_summary.get("clf_rows") or []
    eval_group_labels = eval_summary.get("eval_group_labels")
    if eval_group_labels is not None:
        log_auroc_by_family(
            auroc_rows=auroc_rows,
            clf_rows=clf_rows,
            alea_skip=alea_skip,
            epis_skip=epis_skip,
            ood_skip=ood_skip,
            eval_group_labels=eval_group_labels,
        )

    print("\n" + "=" * 70)
    print("SAVED ARTIFACTS (disk)")
    print("=" * 70)
    for label, path in written.labeled_paths():
        if path is not None:
            print(f"  {label}: {path}")


__all__ = [
    "EXPERIMENT_LOG_FILENAME",
    "capture_experiment_log",
    "experiment_log_path",
    "infer_experiment_id",
    "log_auroc_by_family",
    "log_run_complete",
    "log_run_data_context",
    "log_zwischen_dir",
    "read_experiment_log",
]
