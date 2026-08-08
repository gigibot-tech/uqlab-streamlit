"""Fast-pilot experiment engine: train, evaluate signals, write artifacts.

Called only from :func:`uqlab_core.runner.execute.run_from_yaml` (or ``run_from_python_config``).

Paper API map: ``docs/features/PAPER_FLOW.md``

One run = one paper sweep point. Multi-run DE + PNG = campaign end (not here).
"""

from __future__ import annotations

import logging
from pathlib import Path

from uqlab_core.data import build_run_data
from uqlab_core.data.buildData import (
    get_data_loading_mode,
    prepare_eval_data,
    prepare_eval_tensors,
)
from uqlab_core.runner.logging import log_run_data_context
from uqlab_core.runner.config import (
    apply_data_context,
    extract_run_config,
    print_dataset_loaded,
    print_experiment_configuration,
    validate_eval_splits,
)
from uqlab_core.runner.train_eval import run_paper_experiment
from uqlab_core.shared.config.classification import ExperimentConfig
from uqlab_core.shared.utils.classification import auto_device, set_seed

logger = logging.getLogger(__name__)

from uqlab_core.run_artifacts import (
    GROUP_ALEATORIC,
    GROUP_CLEAN,
    GROUP_EPISTEMIC,
    GROUP_NAMES,
    GROUP_OOD,
)


def run_experiment_core(
    config: ExperimentConfig,
    results_dir: Path,
    *,
    seed: int,
    device_str: str,
    config_path: Path | None = None,
    project_root: Path | None = None,
) -> dict:
    """
    One paper sweep point: fit + materialize ``predict_disentangling`` vectors on disk.

    Phases:

    1. **Config + data** — ``build_run_data`` → ``run_paper_experiment``
    2. **Train + eval** — ``run_train_and_eval_phases`` (see module docstring for Keras mapping)
    3. **Not here** — ``calculate_disentanglement_error`` / campaign PNG (needs N runs)
    """
    from uqlab_core.shared.runtime_paths import repository_root

    root = project_root if project_root is not None else repository_root()

    # LOG: experiment banner (stdout)
    run_cfg = extract_run_config(config)
    print_experiment_configuration(run_cfg)

    set_seed(seed)
    device = auto_device(device_str)

    feature_cache_dir = root / config.paths.feature_cache_dir
    results_dir.mkdir(parents=True, exist_ok=True)

    bundle = build_run_data(
        config,
        root,
        seed=seed,
        device=device,
        feature_cache_dir=feature_cache_dir,
        feature_batch_size=run_cfg.feature_batch_size,
    )
    apply_data_context(run_cfg, bundle.ctx)
    data_ctx = bundle.ctx
    dataset = bundle.dataset
    split_spec = bundle.split_spec
    data_pack = bundle.data_pack

    print_dataset_loaded(data_ctx, dataset)
    validate_eval_splits(run_cfg, split_spec)

    log_run_data_context(
        device=device,
        results_dir=results_dir,
        train_dataset=data_pack["train_dataset"],
        clean_eval_pack=data_pack["clean_eval_pack"],
        aleatoric_eval_pack=data_pack["aleatoric_eval_pack"],
        epistemic_eval_pack=data_pack["epistemic_eval_pack"],
        ood_eval_pack=data_pack["ood_eval_pack"],
    )

    result = run_paper_experiment(
        config,
        bundle,
        results_dir,
        device=device,
        seed=seed,
        config_path=config_path,
        log=True,
    )
    return result["summary"]


__all__ = [
    "GROUP_ALEATORIC",
    "GROUP_CLEAN",
    "GROUP_EPISTEMIC",
    "GROUP_NAMES",
    "GROUP_OOD",
    "get_data_loading_mode",
    "prepare_eval_data",
    "prepare_eval_tensors",
    "build_run_data",
    "run_experiment_core",
]
