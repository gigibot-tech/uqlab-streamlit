#!/usr/bin/env python3
"""CLI: load merged unified metrics and print summary / optional PNG."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report on unified validation + paper metrics.")
    parser.add_argument(
        "--sweep",
        choices=("dataset_size", "label_noise"),
        default="dataset_size",
    )
    parser.add_argument(
        "--sources",
        nargs="+",
        default=["pytorch_validation", "paper_keras"],
        choices=["pytorch_validation", "paper_keras"],
    )
    parser.add_argument("--png", type=Path, default=None, help="Export 3×4 figure to PNG (requires kaleido).")
    args = parser.parse_args(argv)

    from uqlab.results_io import load_unified_metrics

    df = load_unified_metrics(args.sweep, sources=tuple(args.sources))
    print(f"Unified metrics shape: {df.shape}")
    if df.empty:
        print("No rows loaded.")
        return 1

    for source in df["source"].dropna().unique():
        n = (df["source"] == source).sum()
        print(f"  {source}: {n} rows")

    paper = df[df["source"] == "paper_keras"]
    if not paper.empty:
        methods = paper["method"].nunique()
        dis = paper["disentanglement"].nunique()
        print(f"Paper rows: {len(paper)} ({methods} methods × {dis} disentanglements)")
    else:
        print("Paper rows not found — run scripts/run_paper_benchmarks.py (requires Keras)")

    print(df.groupby(["source", "method", "disentanglement"], dropna=False).size().to_string())

    if args.png:
        from uqlab.notebook_support.method_comparison_plotly import (
            create_method_uncertainty_comparison_figure,
        )
        from uqlab.notebook_support.signals import resolve_x_col

        x_col = resolve_x_col(df, args.sweep)
        fig = create_method_uncertainty_comparison_figure(df, x_col=x_col, sweep_type=args.sweep)
        if fig is None:
            print("Could not build figure.", file=sys.stderr)
            return 1
        try:
            fig.write_image(str(args.png), width=1400, height=1200)
            print(f"Wrote {args.png}")
        except Exception as exc:
            print(f"PNG export failed ({exc}). Install kaleido or use Streamlit.", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
