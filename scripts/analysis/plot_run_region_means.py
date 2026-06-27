#!/usr/bin/env python3
"""Simple per-region signal plots for a single four-region run.

Reads ``per_sample_signals.csv`` from a run directory and plots the mean of each
uncertainty signal per region (``clean`` / ``aleatoric_like`` / ``epistemic_like``
/ ``ood_like``). This is the single-run analogue of the vendor sweep notebook's
``groupby(...).mean().plot()`` — region on the x-axis instead of a sweep percentage.

Usage:
    PYTHONPATH=src python scripts/analysis/plot_run_region_means.py results/my_run
    PYTHONPATH=src python scripts/analysis/plot_run_region_means.py results/my_run --out plot.png
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

REGION_ORDER = ["clean", "aleatoric_like", "epistemic_like", "ood_like"]
_NON_SIGNAL_COLS = {"group", "dataset_index", "clean_label", "noisy_label", "is_noisy"}


def per_region_signal_means(run_dir: Path) -> pd.DataFrame:
    """Mean of each numeric signal per region group, ordered clean→aleatoric→epistemic→ood."""
    csv_path = run_dir / "per_sample_signals.csv"
    if not csv_path.is_file():
        raise FileNotFoundError(f"No per_sample_signals.csv under {run_dir}")
    df = pd.read_csv(csv_path)
    if "group" not in df.columns:
        raise ValueError(f"{csv_path} has no 'group' column")

    signal_cols = [
        c
        for c in df.columns
        if c not in _NON_SIGNAL_COLS and pd.api.types.is_numeric_dtype(df[c])
    ]
    if not signal_cols:
        raise ValueError(f"{csv_path} has no numeric signal columns")

    means = df.groupby("group")[signal_cols].mean()
    order = [g for g in REGION_ORDER if g in means.index]
    order += [g for g in means.index if g not in order]
    return means.reindex(order)


def plot_region_means(means: pd.DataFrame, out_path: Path, *, title: str) -> None:
    """Small-multiples bar chart: one subplot per signal, independent y-scales."""
    signals = list(means.columns)
    ncols = min(4, len(signals))
    nrows = (len(signals) + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(4 * ncols, 3 * nrows), squeeze=False)

    for idx, signal in enumerate(signals):
        ax = axes[idx // ncols][idx % ncols]
        means[signal].plot(kind="bar", ax=ax, color="tab:blue")
        ax.set_title(signal, fontsize=9)
        ax.set_xlabel("")
        ax.tick_params(axis="x", labelrotation=30, labelsize=7)
        ax.tick_params(axis="y", labelsize=7)

    for idx in range(len(signals), nrows * ncols):
        axes[idx // ncols][idx % ncols].axis("off")

    fig.suptitle(title, fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path, help="Run directory containing per_sample_signals.csv")
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output PNG path (default: <run_dir>/analysis/region_signal_means.png)",
    )
    parser.add_argument(
        "--csv-out",
        type=Path,
        default=None,
        help="Optional path to also save the per-region means table as CSV.",
    )
    args = parser.parse_args(argv)

    run_dir = args.run_dir.resolve()
    try:
        means = per_region_signal_means(run_dir)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(means.round(4).to_string())

    out_path = args.out or (run_dir / "analysis" / "region_signal_means.png")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plot_region_means(means, out_path, title=f"Mean signal per region — {run_dir.name}")
    print(f"\nSaved plot: {out_path}")

    if args.csv_out is not None:
        args.csv_out.parent.mkdir(parents=True, exist_ok=True)
        means.to_csv(args.csv_out)
        print(f"Saved table: {args.csv_out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
