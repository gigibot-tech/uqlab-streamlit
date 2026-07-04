"""
Train + uncertainty eval phases (paper ``fit`` + ``predict_disentangling`` in one job).

Notebooks: ``build_run_data`` → ``run_paper_experiment(config, bundle, ...)``.
Full runs: ``run_experiment_core`` wraps the same two calls.
"""

from __future__ import annotations

import logging
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from uqlab_core.data.buildData import RunDataBundle
from uqlab_core.evaluation.reporting import build_run_summary
from uqlab_core.models.training import train_classifier
from uqlab_core.runner.logging import log_run_complete
from uqlab_core.run_artifacts import persist_run_outputs
from uqlab_core.shared.config.classification import ExperimentConfig

logger = logging.getLogger(__name__)


def run_paper_experiment(
    config: ExperimentConfig,
    bundle: RunDataBundle,
    results_dir: Path,
    *,
    device,
    seed: int,
    config_path: Path | None = None,
    persist: bool = True,
    log: bool = True,
) -> dict[str, Any]:
    """
    Core ML block: train → uncertainty eval → optional persist.

    ``bundle`` comes from :func:`uqlab_core.data.build_run_data`.
    """
    from uqlab_core.runner.config import apply_data_context, extract_run_config

    run_cfg = extract_run_config(config)
    apply_data_context(run_cfg, bundle.ctx)
    run_cache_dir = results_dir / "cache"
    results_dir.mkdir(parents=True, exist_ok=True)

    return _run_paper_experiment_impl(
        config=config,
        run_cfg=run_cfg,
        bundle=bundle,
        results_dir=results_dir,
        run_cache_dir=run_cache_dir,
        device=device,
        seed=seed,
        config_path=config_path,
        persist=persist,
        log=log,
    )


def _run_paper_experiment_impl(
    *,
    config: ExperimentConfig,
    run_cfg,
    bundle: RunDataBundle,
    results_dir: Path,
    run_cache_dir: Path,
    device,
    seed: int,
    config_path: Path | None = None,
    persist: bool = True,
    log: bool = True,
) -> dict[str, Any]:
    data_pack = bundle.data_pack
    split_spec = bundle.split_spec
    training_config = config.training
    data_config = config.data
    model_config = config.model
    eval_config = config.evaluation
    ds_spec = run_cfg.dataset_spec

    train_dataset = data_pack["train_dataset"]
    clean_eval_pack = data_pack["clean_eval_pack"]
    aleatoric_eval_pack = data_pack["aleatoric_eval_pack"]
    epistemic_eval_pack = data_pack["epistemic_eval_pack"]
    ood_eval_pack = data_pack["ood_eval_pack"]
    mode = data_pack["mode"]

    epochs = run_cfg.epochs
    mc_passes = run_cfg.mc_passes
    top_k = run_cfg.top_k
    dinov2_model = run_cfg.dinov2_model
    hidden_dim = run_cfg.hidden_dim
    dropout = run_cfg.dropout
    feature_batch_size = run_cfg.feature_batch_size

    model, prior_epoch_loaded = train_classifier(config, bundle, device)

    from uqlab_core.evaluation.pipeline import run_uncertainty_eval

    eval_result = run_uncertainty_eval(
        model,
        config,
        bundle,
        results_dir=results_dir,
        device=device,
        seed=seed,
        run_cfg=run_cfg,
        log=log,
    )
    signal_table = eval_result.signal_table
    eval_summary = eval_result.eval_summary
    eval_outputs = eval_result.eval_outputs
    eval_setup_path = eval_result.eval_setup_path
    uq = eval_outputs.get("uq") or {}
    mean_pred_det = eval_outputs.get("mean_pred_det")
    eval_inputs = data_pack["eval_inputs"]
    eval_data = data_pack["eval_data"]
    eval_clean_labels = eval_data["eval_clean_labels"]
    eval_is_noisy = eval_data["eval_is_noisy"]
    eval_group_labels = eval_data["eval_group_labels"]

    out: dict[str, Any] = {
        "eval_summary": eval_summary,
        "signal_table": signal_table,
        "model": model,
        "eval_setup_path": eval_setup_path,
    }

    if not persist:
        return out

    config_dict = asdict(config)
    if config_dict.get("paths"):
        config_dict["paths"] = {
            k: str(v) if isinstance(v, Path) else v for k, v in config_dict["paths"].items()
        }
    if config_dict.get("model"):
        config_dict["model"] = dict(config.model)

    auroc_rows = eval_summary["auroc_rows"]
    one_vs_rest_auroc = eval_summary["one_vs_rest_auroc"]
    clf_rows = eval_summary["clf_rows"]

    summary, signal_formulas = build_run_summary(
        config_path=config_path,
        seed=seed,
        device=device,
        data_config=data_config,
        model_config=model_config,
        training_config=training_config,
        eval_config=eval_config,
        split_spec=split_spec,
        train_dataset=train_dataset,
        clean_eval_pack=clean_eval_pack,
        aleatoric_eval_pack=aleatoric_eval_pack,
        epistemic_eval_pack=epistemic_eval_pack,
        ood_eval_pack=ood_eval_pack,
        eval_per_group=run_cfg.eval_per_group,
        top_k=top_k,
        mc_passes=mc_passes,
        one_vs_rest_auroc=one_vs_rest_auroc,
        auroc_rows=auroc_rows,
        clf_rows=clf_rows,
    )

    config_ns = SimpleNamespace(
        noise_type=run_cfg.noise_type,
        under_supported_classes=run_cfg.under_supported_classes_str,
        under_train_per_class=run_cfg.under_train_per_class,
        regular_train_per_class=run_cfg.regular_train_per_class,
        eval_per_group=run_cfg.eval_per_group,
        dinov2_model=dinov2_model,
        hidden_dim=hidden_dim,
        dropout=dropout,
        epochs=epochs,
        learning_rate=run_cfg.learning_rate,
        weight_decay=run_cfg.weight_decay,
        train_batch_size=run_cfg.train_batch_size,
        feature_batch_size=feature_batch_size,
        mc_passes=mc_passes,
        top_k=top_k,
        seed=seed,
        device=str(device),
    )

    written = persist_run_outputs(
        results_dir,
        train_dataset=train_dataset,
        config_dict=config_dict,
        summary=summary,
        signal_formulas=signal_formulas,
        config_ns=config_ns,
        split_spec=split_spec,
        auroc_rows=auroc_rows,
        clf_rows=clf_rows,
        per_sample_csv_path=eval_summary.get("per_sample_csv_path"),
        eval_setup_zwischen_path=eval_setup_path,
        model=model,
        prior_epoch_loaded=prior_epoch_loaded,
        epochs=epochs,
        hidden_dim=hidden_dim,
        dropout=dropout,
        num_classes=ds_spec.num_classes,
        dinov2_model=dinov2_model,
        uq=uq,
        mean_pred_det=mean_pred_det,
        eval_inputs=eval_inputs,
        mode=mode,
        eval_clean_labels=eval_clean_labels,
        eval_is_noisy=eval_is_noisy,
        eval_group_labels=eval_group_labels,
        clean_eval_pack=clean_eval_pack,
        aleatoric_eval_pack=aleatoric_eval_pack,
        epistemic_eval_pack=epistemic_eval_pack,
        ood_eval_pack=ood_eval_pack,
        signal_table=signal_table,
    )

    if log:
        log_run_complete(written, results_dir=results_dir, eval_summary=eval_summary, summary=summary)

    out["summary"] = summary
    out["written"] = written
    return out


def run_train_and_eval_phases(**kwargs) -> dict[str, Any]:
    """Compat alias — legacy kwargs (``data_pack``, ``split_spec``, …) or ``(config, bundle)``."""
    if "bundle" not in kwargs:
        kwargs["bundle"] = RunDataBundle(
            dataset=kwargs.pop("dataset", None),
            split_spec=kwargs.pop("split_spec"),
            data_pack=kwargs.pop("data_pack"),
            request=kwargs.pop("request", None),
            ctx=kwargs.pop("ctx", None),
        )
    for legacy_key in ("training_config", "data_config", "model_config", "eval_config", "ds_spec"):
        kwargs.pop(legacy_key, None)
    return _run_paper_experiment_impl(**kwargs)


__all__ = ["run_paper_experiment", "run_train_and_eval_phases"]
