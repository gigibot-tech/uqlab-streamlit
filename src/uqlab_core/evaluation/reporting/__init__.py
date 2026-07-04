"""
Evaluation reporting: in-memory summaries, disk writers, and notebook plot helpers.

Pure metric computation lives in :mod:`uqlab_core.evaluation.scoring`.
The ``results.pt`` read contract lives in :mod:`uqlab_core.run_artifacts`.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import torch
from torch.utils.data import Dataset

from uqlab_core.data.splits.experiment_loader import SplitSpec
from uqlab_core.evaluation.signals.formulas import build_signal_formula_manifest
from uqlab_core.run_artifacts import GROUP_NAMES
from uqlab_core.shared.config.classification import (
    DataConfig,
    EvaluationConfig,
    ModelConfig,
    TrainingConfig,
)

logger = logging.getLogger(__name__)


# --- In-memory run summary ---


def build_run_summary(
    *,
    config_path: Path | None,
    seed: int,
    device: torch.device,
    data_config: DataConfig,
    model_config: ModelConfig,
    training_config: TrainingConfig,
    eval_config: EvaluationConfig,
    split_spec: SplitSpec,
    train_dataset: Dataset,
    clean_eval_pack: dict[str, torch.Tensor],
    aleatoric_eval_pack: dict[str, torch.Tensor],
    epistemic_eval_pack: dict[str, torch.Tensor],
    ood_eval_pack: dict[str, torch.Tensor] | None,
    eval_per_group: int,
    top_k: int,
    mc_passes: int,
    one_vs_rest_auroc: list[dict],
    auroc_rows: list[tuple],
    clf_rows: list[tuple[str, float]],
) -> tuple[dict, dict]:
    """Build summary dict and signal formula manifest (memory only)."""
    eval_protocol = {
        "architecture_invariant": True,
        "rationale": (
            "Eval indices sampled from CIFAR-10N pools before training; "
            "all architectures at same sweep point use same seed/eval_per_group/under_supported_classes "
            "(fixed test set, varying train UQ method - same as uq_disentanglement design)."
        ),
        "eval_per_group": eval_per_group,
        "groups": list(GROUP_NAMES.values()),
        "under_supported_classes": list(split_spec.under_supported_classes),
        "seed": seed,
    }

    signal_formulas = build_signal_formula_manifest(
        top_k=top_k,
        mc_passes=mc_passes,
        eval_protocol=eval_protocol,
    )

    summary = {
        "config": {
            "config_file": str(config_path),
            "seed": seed,
            "device": str(device),
            "data": vars(data_config),
            "model": model_config.dict(),
            "training": vars(training_config),
            "evaluation": vars(eval_config),
        },
        "under_supported_classes": split_spec.under_supported_classes,
        "train_size": len(train_dataset),
        "eval_sizes": {
            "clean": len(clean_eval_pack["clean_labels"]),
            "aleatoric_like": len(aleatoric_eval_pack["clean_labels"]),
            "epistemic_like": len(epistemic_eval_pack["clean_labels"]),
            "ood_like": len(ood_eval_pack["clean_labels"]) if ood_eval_pack is not None else 0,
        },
        "eval_protocol": eval_protocol,
        "signal_formulas": signal_formulas,
        "dualxda_svm": {"max_iter": 1_000_000},
        "one_vs_rest_auroc": one_vs_rest_auroc,
        "auroc_rows": [
            {
                "signal": row[0],
                "aleatoric_auroc": row[1],
                "epistemic_auroc": row[2],
                **({"ood_auroc": row[3]} if len(row) > 3 and row[3] is not None else {}),
            }
            for row in auroc_rows
        ],
        "macro_f1": [
            {
                "signal_set": name,
                "macro_f1": score,
            }
            for name, score in clf_rows
        ],
    }
    return summary, signal_formulas


# --- Disk writers ---


def _unpack_auroc_row(row: tuple) -> tuple[str, float | None, float | None, float | None]:
    """``eval.py`` rows are ``(signal, alea, epis)`` or ``(..., ood)``."""
    name, alea, epis = row[0], row[1], row[2]
    ood = row[3] if len(row) > 3 else None
    return name, alea, epis, ood


def _format_auroc_markdown(value: float | None) -> str:
    """Format AUROC for markdown tables; ``None``/NaN → em dash."""
    if value is None:
        return "—"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "—"
    if np.isnan(v):
        return "—"
    return f"{v:.4f}"


def persist_experiment_summaries(
    results_dir: Path,
    *,
    summary: dict,
    args: argparse.Namespace,
    split_spec,
    train_size: int,
    eval_sizes: Dict[str, int],
    auroc_rows: List[Tuple[str, float | None, float | None] | Tuple[str, float | None, float | None, float | None]],
    clf_rows: List[Tuple[str, float]],
) -> None:
    """Write ``summary.json`` and ``summary.md`` (None-safe AUROC formatting)."""
    results_dir.mkdir(parents=True, exist_ok=True)
    summary_path = results_dir / "summary.json"
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    markdown_path = results_dir / "summary.md"
    try:
        markdown = build_results_markdown(
            args=args,
            split_spec=split_spec,
            train_size=train_size,
            eval_sizes=eval_sizes,
            auroc_rows=auroc_rows,
            clf_rows=clf_rows,
        )
    except Exception as exc:
        logger.warning("summary.md build failed (%s); writing minimal fallback", exc)
        markdown = (
            "# Fast Uncertainty Classification Results\n\n"
            "Markdown summary could not be generated; see `summary.json`.\n"
        )
    markdown_path.write_text(markdown, encoding="utf-8")


def build_results_markdown(
    *,
    args: argparse.Namespace,
    split_spec,
    train_size: int,
    eval_sizes: Dict[str, int],
    auroc_rows: List[Tuple[str, float | None, float | None] | Tuple[str, float | None, float | None, float | None]],
    clf_rows: List[Tuple[str, float]],
) -> str:
    """Build a Markdown summary of experiment results."""
    lines = [
        "# Fast Uncertainty Classification Results",
        "",
        "## Setup",
        f"- Noise type: `{args.noise_type}`",
        f"- Under-supported classes: `{split_spec.under_supported_classes}`",
        f"- Train size: `{train_size}`",
        f"- Eval clean: `{eval_sizes['clean']}`",
        f"- Eval aleatoric-like: `{eval_sizes['aleatoric_like']}`",
        f"- Eval epistemic-like: `{eval_sizes['epistemic_like']}`",
        f"- DINOv2 backbone: `{args.dinov2_model}`",
    ]
    has_ood = any(len(row) > 3 and row[3] is not None for row in auroc_rows)
    if has_ood:
        lines.extend(
            [
                "",
                "## One-vs-Rest AUROC",
                "",
                "| Signal | Aleatoric-like AUROC | Epistemic-like AUROC | OOD-like AUROC |",
                "| --- | ---: | ---: | ---: |",
            ]
        )
        for row in auroc_rows:
            name, alea_auc, epis_auc, ood_auc = _unpack_auroc_row(row)
            lines.append(
                f"| {name} | {_format_auroc_markdown(alea_auc)} | "
                f"{_format_auroc_markdown(epis_auc)} | {_format_auroc_markdown(ood_auc)} |"
            )
    else:
        lines.extend(
            [
                "",
                "## One-vs-Rest AUROC",
                "",
                "| Signal | Aleatoric-like AUROC | Epistemic-like AUROC |",
                "| --- | ---: | ---: |",
            ]
        )
        for row in auroc_rows:
            name, alea_auc, epis_auc, _ = _unpack_auroc_row(row)
            lines.append(
                f"| {name} | {_format_auroc_markdown(alea_auc)} | {_format_auroc_markdown(epis_auc)} |"
            )

    lines.extend(
        [
            "",
            "## 3-Way Signal Classifier",
            "",
            "| Signal set | Macro-F1 |",
            "| --- | ---: |",
        ]
    )
    for name, score in clf_rows:
        lines.append(f"| {name} | {score:.4f} |")

    return "\n".join(lines) + "\n"


def print_noisy_eval_samples(
    *,
    eval_group_labels: torch.Tensor,
    eval_dataset_index: torch.Tensor,
    eval_clean_labels: torch.Tensor,
    eval_noisy_labels: torch.Tensor,
    eval_is_noisy: torch.Tensor,
    group_names: Dict[int, str],
    max_rows: int = 40,
) -> None:
    """Print CIFAR-10N index + labels for eval points with ``is_noisy=True``."""
    noisy = eval_is_noisy.bool()
    n_noisy = int(noisy.sum().item())
    n_total = int(eval_group_labels.shape[0])
    print(f"\nNoisy eval samples (is_noisy=True): {n_noisy} / {n_total}")
    if n_noisy == 0:
        return

    print(f"  {'dataset_index':>14}  {'group':<16}  clean  noisy")
    shown = 0
    for i in range(n_total):
        if not bool(noisy[i].item()):
            continue
        grp = group_names[int(eval_group_labels[i].item())]
        idx = int(eval_dataset_index[i].item())
        clean = int(eval_clean_labels[i].item())
        nlabel = int(eval_noisy_labels[i].item())
        print(f"  {idx:>14}  {grp:<16}  {clean:>5}  {nlabel:>5}")
        shown += 1
        if shown >= max_rows:
            remaining = n_noisy - shown
            if remaining > 0:
                print(f"  ... and {remaining} more (see per_sample_signals.csv)")
            break


def save_training_data_csv(
    output_path: Path,
    train_dataset,
    config: Optional[dict] = None,
) -> None:
    """Save training data statistics to CSV (and optional config JSON)."""
    import pandas as pd

    print("\n" + "=" * 80)
    print("Saving training data statistics...")
    print("=" * 80 + "\n")

    try:
        clean_labels = train_dataset.clean_labels
        noisy_labels = train_dataset.targets
        is_noisy = train_dataset.is_noisy
        indices = train_dataset.original_indices

        df = pd.DataFrame(
            {
                "dataset_index": indices,
                "clean_label": clean_labels,
                "noisy_label": noisy_labels,
                "is_noisy": is_noisy,
            }
        )

        df.to_csv(output_path, index=False)

        if config:
            config_path = output_path.with_suffix(".config.json")
            with config_path.open("w") as f:
                json.dump(config, f, indent=2)
            print(f"  Config saved to: {config_path}")

        total_samples = len(df)
        noisy_samples = df["is_noisy"].sum()
        clean_samples = total_samples - noisy_samples
        noise_rate = noisy_samples / total_samples if total_samples > 0 else 0

        print("📊 Training Data Summary:")
        print(f"  Total samples: {total_samples:,}")
        print(f"  Clean samples: {clean_samples:,}")
        print(f"  Noisy samples: {noisy_samples:,}")
        print(f"  Noise rate: {noise_rate:.1%}")
        print(f"  Saved to: {output_path}")
        print()

    except AttributeError as e:
        print("⚠️  Warning: Could not save training data statistics")
        print(f"   Dataset missing required attributes: {e}")
        print("   Skipping training_data.csv generation")
        print()


def save_per_sample_csv(
    output_path: Path,
    eval_group_labels: torch.Tensor,
    eval_clean_labels: torch.Tensor,
    eval_is_noisy: torch.Tensor,
    signal_table: Dict[str, torch.Tensor],
    group_names: Dict[int, str],
    *,
    eval_noisy_labels: torch.Tensor | None = None,
    eval_dataset_index: torch.Tensor | None = None,
    print_noisy_summary: bool = True,
) -> None:
    """Save per-sample signals to CSV file."""
    n = int(eval_group_labels.shape[0])
    if eval_noisy_labels is None:
        eval_noisy_labels = eval_clean_labels
    if eval_dataset_index is None:
        eval_dataset_index = torch.full((n,), -1, dtype=torch.long)

    with output_path.open("w", newline="") as f:
        writer = csv.writer(f)

        header = [
            "group",
            "dataset_index",
            "clean_label",
            "noisy_label",
            "is_noisy",
        ] + list(signal_table.keys())
        writer.writerow(header)

        for i in range(n):
            row = [
                group_names[int(eval_group_labels[i].item())],
                int(eval_dataset_index[i].item()),
                int(eval_clean_labels[i].item()),
                int(eval_noisy_labels[i].item()),
                bool(eval_is_noisy[i].item()),
            ]
            for signal_name in signal_table.keys():
                row.append(float(signal_table[signal_name][i].item()))
            writer.writerow(row)

    if print_noisy_summary:
        print_noisy_eval_samples(
            eval_group_labels=eval_group_labels,
            eval_dataset_index=eval_dataset_index,
            eval_clean_labels=eval_clean_labels,
            eval_noisy_labels=eval_noisy_labels,
            eval_is_noisy=eval_is_noisy,
            group_names=group_names,
        )


from uqlab_core.evaluation.reporting.four_region_reporting import (  # noqa: E402
    FOUR_REGION_GROUP_ORDER,
    four_region_signals_dataframe,
    list_four_region_signal_columns,
    plot_all_four_region_metrics,
    plot_four_region_metrics_by_group,
)


__all__ = [
    "FOUR_REGION_GROUP_ORDER",
    "build_results_markdown",
    "build_run_summary",
    "four_region_signals_dataframe",
    "list_four_region_signal_columns",
    "persist_experiment_summaries",
    "plot_all_four_region_metrics",
    "plot_four_region_metrics_by_group",
    "print_noisy_eval_samples",
    "save_per_sample_csv",
    "save_training_data_csv",
]
