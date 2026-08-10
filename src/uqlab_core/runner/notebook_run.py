"""
Notebook helpers — bootstrap, setup, and one-call experiment runners.

Four-region benchmark: ``setup_notebook`` → ``run_four_region_benchmark``.
Paper flow: ``setup_notebook`` → ``run_notebook_experiment``.
"""

from __future__ import annotations

import importlib.util
import sys
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from uqlab_core.data import build_run_data
from uqlab_core.data.splits.four_region import DEFAULT_FOUR_REGION_PRESET
from uqlab_core.runner.train_eval import run_paper_experiment
from uqlab_core.shared.config.classification import ExperimentConfig
from uqlab_core.shared.utils.classification import auto_device, set_seed


def apply_attribution_backends(
    cfg: Any,
    *,
    enable_graddot: bool = False,
    enable_ek_fac: bool = False,
) -> None:
    """
    Pick which attribution **backend** runs at eval time.

    A backend is the method that scores how much each training sample influenced
    each test prediction (DualXDA, GradDot, or EK-FAC). Metric ids come from
    :mod:`uqlab_core.evaluation.signals.catalog`.
    """
    from uqlab_core.evaluation.signals.catalog import (
        AttributionBackend,
        attribution_metric_ids,
    )

    backends: list[str] = [AttributionBackend.DUALXDA.value]
    attribution = list(attribution_metric_ids(AttributionBackend.DUALXDA))
    if enable_graddot:
        backends.append(AttributionBackend.GRADDOT.value)
        attribution.extend(attribution_metric_ids(AttributionBackend.GRADDOT))
    if enable_ek_fac:
        try:
            import kronfluence  # noqa: F401
        except ImportError as exc:
            raise ImportError(
                "enable_ek_fac=True but kronfluence is not installed. Run: pip install kronfluence"
            ) from exc
        backends.append(AttributionBackend.EK_FAK.value)
        attribution.extend(attribution_metric_ids(AttributionBackend.EK_FAK))
    cfg.evaluation.attribution_backends = backends
    cfg.evaluation.signals["attribution"] = attribution


def default_four_region_plot_metrics(
    *,
    enable_graddot: bool = False,
    enable_ek_fac: bool = False,
) -> list[str]:
    """Primary metrics for four-region box plots (one coherence per backend + baselines)."""
    from uqlab_core.evaluation.signals.catalog import (
        AttributionBackend,
        predictive_baseline_ids,
    )

    metrics = [f"inverse_coherence_{AttributionBackend.DUALXDA.value}"]
    if enable_ek_fac:
        metrics.append(f"inverse_coherence_{AttributionBackend.EK_FAK.value}")
    if enable_graddot:
        metrics.append(f"inverse_coherence_{AttributionBackend.GRADDOT.value}")
    metrics.extend(predictive_baseline_ids())
    return metrics


def default_four_region_runs(root: Any) -> list[dict[str, Any]]:
    """Preset run entries for the four-region benchmark notebook."""
    root = Path(root)
    return [
        {
            "name": "fashion_mlp",
            "config_path": root / "configs/experiment/four_region_fashion_mlp.yaml",
            "class_regions": deepcopy(DEFAULT_FOUR_REGION_PRESET),
        },
        {
            "name": "cifar_resnet",
            "config_path": root / "configs/experiment/four_region_cifar_resnet.yaml",
            "class_regions": deepcopy(DEFAULT_FOUR_REGION_PRESET),
        },
    ]


@dataclass
class NotebookContext:
    """Environment returned by :func:`setup_notebook`."""

    root: Path
    device: Any
    seed: int
    has_kronfluence: bool
    results_base: Path


def _bootstrap_uqlab_path() -> Path:
    for base in (Path.cwd(), *Path.cwd().parents):
        for path in (
            base / "src" / "uqlab_core" / "notebooks" / "bootstrap_uqlab.py",
            base / "uqlab-streamlit" / "src" / "uqlab_core" / "notebooks" / "bootstrap_uqlab.py",
            base / "four-region-benchmark" / "src" / "uqlab_core" / "notebooks" / "bootstrap_uqlab.py",
        ):
            if not path.is_file():
                continue
            spec = importlib.util.spec_from_file_location("_uqlab_bootstrap", path)
            mod = importlib.util.module_from_spec(spec)
            assert spec.loader is not None
            spec.loader.exec_module(mod)
            return mod.ensure_uqlab_path()
    raise ModuleNotFoundError(
        "bootstrap_uqlab.py not found — open uqlab-streamlit/src/uqlab_core/notebooks/ in Jupyter"
    )


def setup_notebook(
    *,
    seed: int = 42,
    device_str: str = "auto",
    results_subdir: str = "results/four_region_benchmark",
    reload_modules: bool = True,
) -> NotebookContext:
    """
    Bootstrap ``src/`` on ``sys.path``, set seed/device, return notebook context.

    Call once at the top of a notebook before any other ``uqlab_core`` imports.
    """
    root = _bootstrap_uqlab_path()
    if reload_modules:
        for mod in list(sys.modules):
            if mod in ("uqlab", "uqlab_core") or mod.startswith(("uqlab.", "uqlab_core.")):
                del sys.modules[mod]

    set_seed(seed)
    device = auto_device(device_str)
    has_kronfluence = importlib.util.find_spec("kronfluence") is not None
    results_base = root / results_subdir
    results_base.mkdir(parents=True, exist_ok=True)
    return NotebookContext(
        root=root,
        device=device,
        seed=seed,
        has_kronfluence=has_kronfluence,
        results_base=results_base,
    )


def run_notebook_experiment(
    config: ExperimentConfig,
    results_dir: Path,
    *,
    project_root: Path,
    seed: int = 42,
    device: Any | None = None,
    device_str: str = "auto",
    config_path: Path | None = None,
    persist: bool = True,
    log: bool = False,
) -> dict[str, Any]:
    """
    One call: ``build_run_data`` → ``run_paper_experiment``.

    Skips Streamlit banners; writes the same artifacts when ``persist=True``.
    """
    set_seed(seed)
    dev = device or auto_device(device_str)
    results_dir = Path(results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    from uqlab_core.runner.config import extract_run_config

    run_cfg = extract_run_config(config)
    bundle = build_run_data(
        config,
        project_root,
        seed=seed,
        device=dev,
        feature_cache_dir=project_root / config.paths.feature_cache_dir,
        feature_batch_size=run_cfg.feature_batch_size,
    )

    return run_paper_experiment(
        config,
        bundle,
        results_dir,
        device=dev,
        seed=seed,
        config_path=config_path,
        persist=persist,
        log=log,
    )


def run_four_region_benchmark(
    runs: list[dict[str, Any]],
    ctx: NotebookContext,
    *,
    enable_graddot: bool = False,
    enable_ek_fac: bool | None = None,
    log: bool = True,
) -> list[Path]:
    """
    Run each four-region benchmark entry (YAML + class_regions preset).

    Internally: load config → ``apply_attribution_backends`` → ``run_notebook_experiment``.
    """
    use_ek_fac = ctx.has_kronfluence if enable_ek_fac is None else enable_ek_fac
    completed: list[Path] = []
    for entry in runs:
        cfg = ExperimentConfig.from_yaml(entry["config_path"])
        cfg.data.partition_mode = "four_region"
        cfg.data.class_regions = deepcopy(entry["class_regions"])
        apply_attribution_backends(cfg, enable_graddot=enable_graddot, enable_ek_fac=use_ek_fac)

        run_dir = ctx.results_base / entry["name"]
        if log:
            print(f"=== {entry['name']} ===")
        run_notebook_experiment(
            cfg,
            run_dir,
            project_root=ctx.root,
            seed=ctx.seed,
            device=ctx.device,
            config_path=Path(entry["config_path"]),
            persist=True,
            log=log,
        )
        completed.append(run_dir)
    if log:
        print("Done:", completed)
    return completed


__all__ = [
    "NotebookContext",
    "apply_attribution_backends",
    "default_four_region_plot_metrics",
    "default_four_region_runs",
    "run_four_region_benchmark",
    "run_notebook_experiment",
    "setup_notebook",
]
