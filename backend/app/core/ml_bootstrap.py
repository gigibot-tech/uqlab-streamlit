"""Ensure ``uqlab`` and training shims are importable for the FastAPI process."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Bump when startup checks change (logged at boot for support/debugging).
ML_BOOTSTRAP_VERSION = 3

# uqlab-streamlit/ (parent of backend/)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = PROJECT_ROOT / "src"

_REQUIRED_DUALXDA_METRICS = frozenset({
    "inverse_coherence_dualxda",
    "inverse_dominance_dualxda",
    "inverse_mass_dualxda",
})


def ensure_ml_paths() -> Path:
    """
    Put repo ``src/`` and project root on ``sys.path`` when needed.

    Works when ``uqlab`` is not pip-installed (e.g. dev uses repo root ``.venv``).
    When ``uqlab`` is installed (``uv sync`` in ``backend/``), this is a no-op for imports.
    """
    paths = [SRC_DIR, PROJECT_ROOT]

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
    Fail fast at startup if repo ``src/`` cannot import the ML training stack.

    Intentionally avoids brittle ``inspect.getsource`` checks — those produced false
    "stale code" failures when the registry moved to suffixed DualXDA metric ids.
    """
    ensure_ml_paths()

    try:
        from uqlab_orchestrator.run_spec import validate_run_yaml  # noqa: F401
        from uqlab.data.dataset_registry import compute_dataset_stats  # noqa: F401
        from uqlab.data.experiment_loader import sample_indices_for_experiment  # noqa: F401
        from uqlab.runner.experiment_core import run_experiment_core
        from uqlab.evaluation.reporting.result_writers import build_results_markdown
        from uqlab.evaluation.signals.registry import (
            METRICS,
            resolve_signal_table_key,
        )
    except ImportError as exc:
        raise RuntimeError(
            f"ML stack import failed ({exc}). "
            f"Start the backend with ./start_backend.sh from backend/ "
            f"so {SRC_DIR} is on PYTHONPATH (bootstrap v{ML_BOOTSTRAP_VERSION})."
        ) from exc

    import uqlab_orchestrator.run_spec as run_spec
    import uqlab.evaluation.signals.registry as signal_registry

    if not hasattr(run_spec, "validate_run_yaml"):
        raise RuntimeError(
            f"uqlab_orchestrator.run_spec at {run_spec.__file__!r} is missing validate_run_yaml."
        )

    if not callable(run_experiment_core):
        raise RuntimeError("uqlab.runner.experiment_core.run_experiment_core is not callable")

    if not callable(resolve_signal_table_key):
        raise RuntimeError(
            "uqlab.evaluation.signals.registry is too old — missing resolve_signal_table_key. "
            f"Pull latest src/ (bootstrap v{ML_BOOTSTRAP_VERSION})."
        )

    metric_ids = set(METRICS.keys())
    missing_dualxda = sorted(_REQUIRED_DUALXDA_METRICS - metric_ids)
    if missing_dualxda:
        raise RuntimeError(
            f"Signal registry at {signal_registry.__file__!r} is missing DualXDA metrics "
            f"{missing_dualxda!r}. Found: {sorted(metric_ids)!r}. "
            f"Expected suffixed ids (bootstrap v{ML_BOOTSTRAP_VERSION})."
        )

    # Legacy unsuffixed ids should alias to dualxda, not appear as primary METRICS keys.
    if "dominance" in metric_ids:
        raise RuntimeError(
            f"Signal registry at {signal_registry.__file__!r} still exports raw 'dominance'."
        )

    script_path = PROJECT_ROOT / "scripts" / "runners" / "run_fast_uncertainty_classification.py"
    if not script_path.is_file():
        raise RuntimeError(f"CLI wrapper not found (optional for API): {script_path}")

    logger.info(
        "ML stack OK (bootstrap v%s): registry=%s metrics=%d evaluator=%s cli=%s",
        ML_BOOTSTRAP_VERSION,
        signal_registry.__file__,
        len(metric_ids),
        build_results_markdown.__module__,
        script_path,
    )


def reload_training_modules() -> None:
    """
    Reload training-related modules before each in-process run.

    ``uvicorn --reload`` often watches only ``backend/``; without this, stale
    ``uqlab`` code stays in ``sys.modules`` until restart.
    """
    import importlib

    ensure_ml_paths()

    for name in (
        "uqlab.runner.experiment_core",
        "uqlab.runner.execute",
        "uqlab.evaluation.signals.registry",
        "uqlab.evaluation.signals.primitives",
        "uqlab.evaluation.signals.sources",
        "uqlab.shared.config.signals",
        "uqlab.data.loaders.cifar10_loader",
        "uqlab.data.dataset_registry",
        "uqlab.evaluation.metrics",
        "uqlab.evaluation.reporting.result_writers",
        "uqlab.data.experiment_loader",
        "uqlab.data.setup",
        "uqlab.runner.phases.config_view",
        "uqlab.runner.phases.eval",
    ):
        mod = sys.modules.get(name)
        if mod is not None:
            importlib.reload(mod)
