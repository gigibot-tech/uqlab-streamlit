"""Ensure ``uqlab`` and training shims are importable for the FastAPI process."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# uqlab-streamlit/ (parent of backend/)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = PROJECT_ROOT / "src"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
RUNNERS_DIR = SCRIPTS_DIR / "runners"
ML_SCRIPT_NAME = "run_fast_uncertainty_classification.py"


def resolve_ml_training_script(*, project_root: Path | None = None) -> Path:
    """
    Locate the fast-pilot training script (``scripts/runners/`` after reorg).

    Falls back to the legacy flat ``scripts/`` path when present.
    """
    root = project_root or PROJECT_ROOT
    candidates = (
        root / "scripts" / "runners" / ML_SCRIPT_NAME,
        root / "scripts" / ML_SCRIPT_NAME,
    )
    for path in candidates:
        if path.is_file():
            return path.resolve()
    return candidates[0].resolve()


def training_script_import_dir(script_path: Path | None = None) -> Path:
    """Directory to put on ``sys.path`` so ``import run_fast_uncertainty_classification`` works."""
    path = script_path or resolve_ml_training_script()
    return path.parent


def ensure_ml_paths(*, scripts_dir: Path | None = None) -> Path:
    """
    Put repo ``src/``, project root, and training script dir on ``sys.path``.

    Works when ``uqlab`` is not pip-installed (e.g. dev uses repo root ``.venv``).
    When ``uqlab`` is installed (``uv sync`` in ``backend/``), this is a no-op for imports.
    """
    script_dir = scripts_dir or training_script_import_dir()
    paths = [SRC_DIR, PROJECT_ROOT, script_dir]
    if SCRIPTS_DIR.exists() and SCRIPTS_DIR not in (script_dir,):
        paths.append(SCRIPTS_DIR)

    added: list[str] = []
    for path in paths:
        entry = str(path.resolve())
        if path.exists() and entry not in sys.path:
            sys.path.insert(0, entry)
            added.append(entry)

    if added:
        logger.debug("ML bootstrap added to sys.path: %s", added)
    return PROJECT_ROOT


def verify_ml_stack() -> None:
    """
    Fail fast at startup if repo ``src/`` is missing expected ML modules.

    Prevents silent use of stale/cached imports when ``uvicorn --reload`` only
    watches ``backend/`` and ``src/`` edits are not picked up until restart.
    """
    try:
        from uqlab_orchestrator.run_spec import validate_run_yaml  # noqa: F401
        from uqlab.data.dataset_registry import compute_dataset_stats  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            f"ML stack import failed ({exc}). "
            f"Start the backend with ./start_backend.sh or python run_dev.py "
            f"so {SRC_DIR} is on PYTHONPATH."
        ) from exc

    import uqlab_orchestrator.run_spec as run_spec

    if not hasattr(run_spec, "validate_run_yaml"):
        raise RuntimeError(
            f"Stale uqlab_orchestrator.run_spec at {run_spec.__file__!r} — "
            "missing validate_run_yaml. Restart via ./start_backend.sh."
        )

    import inspect
    import uqlab.data.dataset_registry as registry
    import uqlab.evaluation.classification.data_loader as data_loader

    reg_src = inspect.getsource(registry.compute_dataset_stats)
    if "getattr(dataset, \"class_names\"" not in reg_src and "getattr(dataset, 'class_names'" not in reg_src:
        raise RuntimeError(
            f"Stale uqlab.data.dataset_registry at {registry.__file__!r}. "
            "Restart the backend (./start_backend.sh) after editing src/."
        )

    dl_src = inspect.getsource(data_loader.sample_indices_for_fast_pilot)
    if "dataset_clean_labels" not in dl_src:
        raise RuntimeError(
            f"Stale data_loader at {data_loader.__file__!r} — "
            "missing protocol-based noise_mask. Use ./start_backend.sh."
        )

    script_path = resolve_ml_training_script()
    if not script_path.is_file():
        raise RuntimeError(
            f"Training script not found (checked scripts/runners/ and scripts/): {script_path}"
        )
    script_src = script_path.read_text(encoding="utf-8")
    if "DualXDATracer(" in script_src and "max_iter=" in script_src.split("DualXDATracer(")[1].split(")")[0]:
        raise RuntimeError(
            f"Training script still passes max_iter to DualXDATracer: {script_path}"
        )

    import uqlab.evaluation.evaluator as evaluator
    import uqlab.evaluation.signals.registry as signal_registry

    eval_src = inspect.getsource(evaluator.build_results_markdown)
    if "_format_auroc_markdown" not in eval_src:
        raise RuntimeError(
            f"Stale uqlab.evaluation.evaluator at {evaluator.__file__!r} — "
            "missing None-safe AUROC markdown formatting. Restart via ./start_backend.sh."
        )

    metric_ids = set(signal_registry.METRICS.keys())
    if "inverse_dominance" not in metric_ids:
        raise RuntimeError(
            f"Stale uqlab.evaluation.signals.registry at {signal_registry.__file__!r} — "
            f"missing inverse_dominance metric (have {sorted(metric_ids)!r}). "
            "Restart via ./start_backend.sh after editing src/."
        )
    if "dominance" in metric_ids and "inverse_dominance" not in metric_ids:
        raise RuntimeError(
            f"Stale signal registry at {signal_registry.__file__!r} — "
            "still exports raw dominance instead of inverse_dominance. Restart backend."
        )

    logger.info(
        "ML stack OK: run_spec=%s training_script=%s registry=%s data_loader=%s evaluator=%s signals=%s",
        run_spec.__file__,
        script_path,
        registry.__file__,
        data_loader.__file__,
        evaluator.__file__,
        signal_registry.__file__,
    )


def reload_training_modules(*, scripts_dir: Path | None = None) -> None:
    """
    Reload training-related modules before each in-process run.

    ``uvicorn --reload`` often watches only ``backend/``; without this, stale
    ``uqlab`` code stays in ``sys.modules`` even when ``scripts/`` is reloaded.
    """
    import importlib

    ensure_ml_paths(scripts_dir=scripts_dir)
    scripts = scripts_dir or training_script_import_dir()
    scripts_entry = str(scripts.resolve())
    if scripts.exists() and scripts_entry not in sys.path:
        sys.path.insert(0, scripts_entry)

    for name in (
        "uqlab.evaluation.signals.registry",
        "uqlab.evaluation.signals.primitives",
        "uqlab.evaluation.signals.sources",
        "uqlab.shared.config.signals",
        "uqlab.data.loaders.cifar10_loader",
        "uqlab.data.dataset_registry",
        "uqlab.evaluation.evaluator",
        "uqlab.evaluation.classification.evaluation",
        "uqlab.evaluation.classification.data_loader",
        "uqlab.evaluation.classification.pipeline.data_setup",
        "uqlab.evaluation.classification.pipeline.experiment_setup",
    ):
        mod = sys.modules.get(name)
        if mod is not None:
            importlib.reload(mod)

    script_name = "run_fast_uncertainty_classification"
    mod = sys.modules.get(script_name)
    if mod is not None:
        importlib.reload(mod)
