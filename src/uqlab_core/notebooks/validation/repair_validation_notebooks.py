#!/usr/bin/env python3
"""Regenerate validation notebooks around the current experiment pipeline."""

from __future__ import annotations

import json
from pathlib import Path


NOTEBOOK_DIR = Path(__file__).resolve().parent


def source_lines(text: str) -> list[str]:
    """Convert a text block into notebook source lines."""
    return [f"{line}\n" for line in text.strip("\n").splitlines()]


def md(text: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": source_lines(text),
    }


def code(text: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source_lines(text),
    }


def notebook(cells: list[dict]) -> dict:
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": "3.11",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def build_sweep_notebook(*, sweep_name: str, title: str, x_col: str, x_label: str) -> dict:
    metric_right = (
        "mean_epistemic_uncertainty" if sweep_name == "dataset_size" else "mean_aleatoric_uncertainty"
    )
    mode_hint = "epistemic" if sweep_name == "dataset_size" else "aleatoric"
    sweep_arg = "dataset_size" if sweep_name == "dataset_size" else "label_noise"

    cells = [
        md(
            f"""
# {title}

This notebook validates the merged `uq_classification` / `uq_benchmarks` pipeline against the paper-style
{sweep_name.replace('_', ' ')} experiment.

It is intentionally wired to the current `scripts/run_validation_experiments.py` output contract:
- load flat `metrics.csv` files
- surface warnings instead of silently plotting blanks
- call the central runner when `RUN_NEW_EXPERIMENTS = True`
"""
        ),
        code(
            """
from pathlib import Path
import sys

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT / "src"))

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from uqlab.notebook_support import (
    ARCHITECTURE_STYLES,
    ensure_columns,
    find_project_root,
    get_row3_signals,
    load_sweep_metrics,
    plot_individual_signals,
    plot_method_uncertainty_comparison,
    present_architectures,
    print_method_architecture_mapping,
    run_validation_experiments,
    summarize_trends,
    validation_dir,
)

plt.style.use("seaborn-v0_8-darkgrid")
sns.set_palette("husl")

project_root = find_project_root()
results_root = validation_dir(project_root) / "{sweep_name}_sweep"
print(f"Project root: {project_root}")
print(f"Results directory: {results_root}")
print(f"Python: {sys.executable}")
""".replace("{sweep_name}", sweep_name)
        ),
        md(
            f"""
## Run Or Load

Set `RUN_NEW_EXPERIMENTS = True` only when your notebook kernel has the full ML environment.
The notebook delegates reruns to `scripts/run_validation_experiments.py --sweep {sweep_arg}` so it stays
aligned with the maintained pipeline.
"""
        ),
        code(
            f"""
RUN_NEW_EXPERIMENTS = False
VALIDATION_MODE = "full"

if RUN_NEW_EXPERIMENTS:
    result = run_validation_experiments(
        project_root=project_root,
        sweep="{sweep_arg}",
        mode=VALIDATION_MODE,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError("Validation runner failed.")
"""
        ),
        code(
            f"""
loaded = load_sweep_metrics("{sweep_name}", project_root=project_root)
df_metrics = loaded.df.copy()

for warning in loaded.warnings:
    print(f"WARNING: {{warning}}")

print(f"Loaded {{len(df_metrics)}} rows")
display(
    ensure_columns(
        df_metrics,
        [
            "architecture",
            "{x_col}",
            "accuracy",
            "mean_epistemic_uncertainty",
            "mean_aleatoric_uncertainty",
            "mean_total_uncertainty",
            "noise_rate",
            "noise_percent",
            "experiment_name",
        ],
    )
)

if df_metrics.empty:
    raise RuntimeError("No validation rows were loaded.")
"""
        ),
        md(
            f"""
## Paper Alignment Notes

- This notebook checks whether the expected **{mode_hint}** trend is visible in the merged pipeline.
- If you see a warning about legacy label-noise scaling, do **not** use the old results for a thesis figure.
- Empty plots should now indicate genuinely missing data, not silent schema mismatches.
"""
        ),
        code(
            f"""
def plot_dual_axis(df, left_metric="accuracy", right_metric="{metric_right}", title="{title}"):
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax2 = ax1.twinx()

    ax1.set_xlabel("{x_label}")
    ax1.set_ylabel(left_metric.replace("_", " ").title(), color="tab:blue")
    ax2.set_ylabel(right_metric.replace("_", " ").title(), color="tab:red")

    for architecture, style in ARCHITECTURE_STYLES.items():
        arch_df = df[df["architecture"] == architecture].sort_values("{x_col}")
        if arch_df.empty:
            continue

        ax1.plot(
            arch_df["{x_col}"],
            arch_df[left_metric],
            color=style["color"],
            marker=style["marker"],
            linewidth=2,
            label=f"{{architecture}} / {{left_metric}}",
        )
        ax2.plot(
            arch_df["{x_col}"],
            arch_df[right_metric],
            color=style["color"],
            marker=style["marker"],
            linestyle="--",
            linewidth=2,
            alpha=0.8,
            label=f"{{architecture}} / {{right_metric}}",
        )

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="center left", bbox_to_anchor=(1.15, 0.5))
    plt.title(title)
    plt.tight_layout()
    plt.show()


plot_dual_axis(df_metrics)
"""
        ),
        code(
            f"""
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
plots = [
    ("accuracy", axes[0, 0]),
    ("mean_epistemic_uncertainty", axes[0, 1]),
    ("mean_aleatoric_uncertainty", axes[1, 0]),
    ("mean_total_uncertainty", axes[1, 1]),
]

for metric, ax in plots:
    for architecture, style in ARCHITECTURE_STYLES.items():
        arch_df = df_metrics[df_metrics["architecture"] == architecture].sort_values("{x_col}")
        if arch_df.empty:
            continue
        ax.plot(
            arch_df["{x_col}"],
            arch_df[metric],
            color=style["color"],
            marker=style["marker"],
            linewidth=2,
            label=architecture,
        )

    ax.set_title(metric.replace("_", " ").title())
    ax.set_xlabel("{x_label}")
    ax.grid(True, alpha=0.3)
    ax.legend()

plt.tight_layout()
plt.show()
"""
        ),
        md(
            """
## Individual Signal AUROC Grid

Epistemic and aleatoric AUROC are plotted separately (do not average them).
"""
        ),
        code(
            f"""
plot_individual_signals(df_metrics, sweep_type="{sweep_name}")
"""
        ),
        md(
            """
## Method Uncertainty Comparison

Layout adapts to the loaded data:
- **Architecture rows:** One row per disentanglement type present in the metrics
  (e.g., PyTorch Attribution when only your validation runs are loaded; plus
  Gaussian Logits / Information Theoretic when paper Keras rows are present).
  Columns = selected architectures.
- **Signal AUROC row (last):** Top 4 candidate signals ranked by sweep-appropriate
  mean AUROC (epistemic for dataset-size, aleatoric for label-noise).  Each column
  shows per-architecture AUROC lines for that signal — distinct per column.

The cell below prints the **architecture list** and **resolved mapping**, then plots.
"""
        ),
        code(
            f"""
archs = present_architectures(df_metrics)
print("Architectures in data:", archs)
mapping = print_method_architecture_mapping(df_metrics)

row3_signals = get_row3_signals(df_metrics, sweep_type="{sweep_name}")
print("\\nSignal AUROC row (top 4 by mean AUROC):")
for signal, auroc in row3_signals:
    print(f"  {{signal}}: {{auroc:.4f}}")

plot_method_uncertainty_comparison(df_metrics, sweep_type="{sweep_name}", architectures=archs)
"""
        ),
        code(
            f"""
trend_summary = summarize_trends(df_metrics, "{sweep_name}")
display(trend_summary)

trend_path = results_root / "trend_summary.csv"
trend_summary.to_csv(trend_path, index=False)
print(f"Saved trend summary to: {{trend_path}}")
"""
        ),
    ]
    return notebook(cells)


def build_logical_consistency_notebook() -> dict:
    cells = [
        md(
            """
# Logical Consistency Validation

This notebook checks whether the current validation outputs are internally coherent and highlights
whether the merged pipeline is thesis-ready or still needs reruns.
"""
        ),
        code(
            """
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from uqlab.notebook_support import (
    ensure_columns,
    find_project_root,
    load_sweep_metrics,
    summarize_trends,
    validate_basic_bounds,
    validate_decomposition,
    validation_dir,
)

plt.style.use("seaborn-v0_8-darkgrid")
sns.set_palette("husl")

project_root = find_project_root()
results_root = validation_dir(project_root)
print(f"Project root: {project_root}")
print(f"Validation root: {results_root}")
"""
        ),
        code(
            """
dataset_loaded = load_sweep_metrics("dataset_size", project_root=project_root)
noise_loaded = load_sweep_metrics("label_noise", project_root=project_root)

for warning in [*dataset_loaded.warnings, *noise_loaded.warnings]:
    print(f"WARNING: {warning}")

df_dataset = dataset_loaded.df.copy()
df_noise = noise_loaded.df.copy()
df_all = pd.concat([df_dataset, df_noise], ignore_index=True)

print(f"Dataset rows: {len(df_dataset)}")
print(f"Label-noise rows: {len(df_noise)}")
print(f"Combined rows: {len(df_all)}")

display(
    ensure_columns(
        df_all,
        [
            "architecture",
            "sweep_type",
            "dataset_size",
            "noise_rate",
            "noise_percent",
            "accuracy",
            "mean_epistemic_uncertainty",
            "mean_aleatoric_uncertainty",
            "mean_total_uncertainty",
        ],
    ).head(20)
)
"""
        ),
        code(
            """
df_decomposition = validate_decomposition(df_all)
df_bounds = validate_basic_bounds(df_all)

display(df_decomposition.head())
display(df_bounds)

if not df_decomposition.empty:
    print(
        f"Decomposition pass rate: "
        f"{df_decomposition['passed'].mean() * 100:.1f}%"
    )
"""
        ),
        code(
            """
dataset_trends = summarize_trends(df_dataset, "dataset_size")
noise_trends = summarize_trends(df_noise, "label_noise")
trend_summary = pd.concat([dataset_trends, noise_trends], ignore_index=True)
display(trend_summary)
"""
        ),
        code(
            """
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

if not df_decomposition.empty:
    axes[0].scatter(df_decomposition["total_expected"], df_decomposition["total_measured"], alpha=0.7)
    max_val = max(df_decomposition["total_expected"].max(), df_decomposition["total_measured"].max())
    axes[0].plot([0, max_val], [0, max_val], "k--", alpha=0.6)
    axes[0].set_title("Measured vs Expected Total Uncertainty")
    axes[0].set_xlabel("Expected")
    axes[0].set_ylabel("Measured")

pass_counts = trend_summary["passed"].value_counts(dropna=False).to_dict() if not trend_summary.empty else {}
axes[1].bar(
    [str(key) for key in pass_counts.keys()],
    list(pass_counts.values()),
    color=["#2ca02c", "#d62728", "#7f7f7f"][: len(pass_counts)],
)
axes[1].set_title("Trend Check Outcomes")
axes[1].set_xlabel("passed")
axes[1].set_ylabel("count")

plt.tight_layout()
plt.show()
"""
        ),
        code(
            """
report_lines = []
report_lines.append("LOGICAL CONSISTENCY REPORT")
report_lines.append("=" * 80)
report_lines.append(f"Dataset rows: {len(df_dataset)}")
report_lines.append(f"Label-noise rows: {len(df_noise)}")
report_lines.append("")

if noise_loaded.warnings:
    report_lines.append("WARNINGS:")
    report_lines.extend(f"- {warning}" for warning in noise_loaded.warnings)
    report_lines.append("")

if not df_decomposition.empty:
    report_lines.append(
        f"Decomposition pass rate: {df_decomposition['passed'].mean() * 100:.1f}%"
    )

if not df_bounds.empty:
    failed_bounds = df_bounds[~df_bounds["passed"]]
    report_lines.append(f"Bounds failures: {len(failed_bounds)}")

if not trend_summary.empty:
    passed_rows = trend_summary["passed"] == True
    failed_rows = trend_summary["passed"] == False
    report_lines.append(f"Trend checks passed: {int(passed_rows.sum())}")
    report_lines.append(f"Trend checks failed: {int(failed_rows.sum())}")

report_path = results_root / "consistency_checks" / "validation_report.txt"
report_path.parent.mkdir(parents=True, exist_ok=True)
report_path.write_text("\\n".join(report_lines))
print(report_path.read_text())
print(f"Saved report to: {report_path}")
"""
        ),
    ]
    return notebook(cells)


def write_notebook(path: Path, nb: dict) -> None:
    path.write_text(json.dumps(nb, indent=1))
    print(f"Wrote {path}")


def main() -> int:
    write_notebook(
        NOTEBOOK_DIR / "architecture_comparison_dataset_size.ipynb",
        build_sweep_notebook(
            sweep_name="dataset_size",
            title="Architecture Comparison: Dataset Size Sweep Validation",
            x_col="dataset_size",
            x_label="Dataset Size (samples per regular class)",
        ),
    )
    write_notebook(
        NOTEBOOK_DIR / "architecture_comparison_label_noise.ipynb",
        build_sweep_notebook(
            sweep_name="label_noise",
            title="Architecture Comparison: Label Noise Sweep Validation",
            x_col="noise_percent",
            x_label="Label Noise (%)",
        ),
    )

    logical_nb = build_logical_consistency_notebook()
    write_notebook(NOTEBOOK_DIR / "logical_consistency_validation.ipynb", logical_nb)
    write_notebook(NOTEBOOK_DIR / "logical_consistency_checks.ipynb", logical_nb)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
