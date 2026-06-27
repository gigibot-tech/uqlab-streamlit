#!/usr/bin/env python3
"""Run an experiment from ExperimentConfig YAML via uqlab.runner.execute.run_from_yaml."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from uqlab.runtime_paths import configs_dir, repository_root
from uqlab.shared.config.classification import ExperimentConfig

_DEFAULT_CONFIG = configs_dir() / "experiment" / "four_region.yaml"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run experiment from ExperimentConfig YAML")
    parser.add_argument(
        "--config",
        type=Path,
        default=_DEFAULT_CONFIG,
        help=f"YAML config (default: {_DEFAULT_CONFIG})",
    )
    parser.add_argument("--seed", type=int, default=None, help="Random seed override")
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        choices=["auto", "cpu", "cuda", "mps"],
        help="Device override",
    )
    parser.add_argument("--output_dir", type=Path, default=None, help="Output directory override")
    args = parser.parse_args()

    config_path = args.config.resolve()
    if not config_path.is_file():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    config = ExperimentConfig.from_yaml(config_path)
    seed = args.seed if args.seed is not None else config.seed
    device_str = args.device if args.device is not None else config.device

    if args.output_dir:
        results_dir = args.output_dir
    else:
        root = repository_root()
        results_base = root / config.paths.results_base_dir
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_dir = results_base / f"experiment_{stamp}"

    from uqlab.runner.execute import run_from_yaml as pipeline_run

    pipeline_run(config_path, results_dir, seed=seed, device_str=device_str)


if __name__ == "__main__":
    main()
