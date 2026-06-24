"""CLI entry point for uncertainty quantification experiments.

This script is a thin wrapper that:
1. Parses command-line arguments (config path, seed, device, output directory)
2. Delegates execution to the canonical pipeline: ``uqlab.runner.pipeline.run()``

The pipeline orchestrates the complete experiment lifecycle:
- Stage 1: Load and validate ExperimentConfig from YAML
- Stage 2: Validate model architecture and evaluation signals
- Stage 3: Execute training via ``uqlab.runner.experiment_core.run_experiment_core()``

Note: This script lives in ``scripts/runners/`` but should be moved to ``src/uqlab/cli/``
to make it an installable console script (see FINAL_ARCHITECTURE_DECISION.md).
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from uqlab.runtime_paths import repository_root
from uqlab.shared.config.classification import ExperimentConfig


def main() -> None:
    """Parse args and delegate to ``uqlab.runner.pipeline.run``."""
    parser = argparse.ArgumentParser(description="Fast uncertainty classification pilot")
    parser.add_argument("--config", type=str, required=True, help="Path to YAML configuration file")
    parser.add_argument("--seed", type=int, default=None, help="Random seed override")
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        choices=["auto", "cpu", "cuda", "mps"],
        help="Device override",
    )
    parser.add_argument("--output_dir", type=str, default=None, help="Output directory override")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    config = ExperimentConfig.from_yaml(config_path)
    seed = args.seed if args.seed is not None else config.seed
    device_str = args.device if args.device is not None else config.device

    if args.output_dir:
        results_dir = Path(args.output_dir)
    else:
        root = repository_root()
        results_base = root / config.paths.results_base_dir
        results_dir = results_base / (
            f"fast_uncertainty_classification_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

    from uqlab.runner.pipeline import run as pipeline_run

    pipeline_run(
        config_path,
        results_dir,
        seed=seed,
        device_str=device_str,
    )


if __name__ == "__main__":
    main()
