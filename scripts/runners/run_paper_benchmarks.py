#!/usr/bin/env python3
"""Run Keras paper benchmarks (optional) and flatten results into unified metrics.csv."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _keras_available() -> bool:
    try:
        import tensorflow  # noqa: F401
        import keras  # noqa: F401

        return True
    except ImportError:
        return False


def _post_process_paper_csvs(
    paper_data_folder: Path,
    sweep_type: str,
    results_root: Path,
    meta_experiment_name: str,
) -> Path:
    from uqlab.results_io import flatten_paper_result_csvs

    out = results_root / "paper_benchmarks" / sweep_type / "metrics.csv"
    flatten_paper_result_csvs(
        paper_data_folder,
        sweep_type=sweep_type,
        meta_experiment_name=meta_experiment_name,
        output_path=out,
    )
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Keras paper UQ benchmarks (optional).")
    parser.add_argument(
        "--sweep",
        choices=("dataset_size", "label_noise", "both"),
        default="both",
        help="Which sweep to post-process into unified metrics.",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Execute Keras experiments (requires tensorflow + keras + keras_uncertainty).",
    )
    parser.add_argument(
        "--paper-data-folder",
        type=Path,
        default=None,
        help="Folder with per-method paper CSVs (default: results/paper_benchmarks/raw).",
    )
    parser.add_argument(
        "--meta-experiment",
        default="decreasing_dataset",
        help="Subfolder name under paper data (matches paper pipeline).",
    )
    args = parser.parse_args(argv)

    results_root = PROJECT_ROOT / "results"
    paper_raw = args.paper_data_folder or (results_root / "paper_benchmarks" / "raw")

    if args.run:
        if not _keras_available():
            print(
                "skip: install tensorflow + keras + keras_uncertainty to run paper benchmarks",
                file=sys.stderr,
            )
            return 0
        os.chdir(PROJECT_ROOT)
        from uqlab.disentanglement_paper.main import main as paper_main

        paper_main()

    sweeps = ["dataset_size", "label_noise"] if args.sweep == "both" else [args.sweep]
    for sweep_type in sweeps:
        out = _post_process_paper_csvs(
            paper_raw / args.meta_experiment,
            sweep_type=sweep_type,
            results_root=results_root,
            meta_experiment_name=args.meta_experiment,
        )
        if out.exists():
            print(f"Wrote unified paper metrics: {out}")
        else:
            print(f"No paper CSVs found for {sweep_type} under {paper_raw}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
