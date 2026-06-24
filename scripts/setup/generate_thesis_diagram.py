#!/usr/bin/env python3
"""
Generate a two-panel thesis schematic from an experiment config YAML.

Panel A: train / eval pool partitioning (set logic + counts).
Panel B: uncertainty signal pipeline (primitives → signals → metrics).

Examples
--------
  cd uqlab-streamlit
  PYTHONPATH=src python3 scripts/generate_thesis_diagram.py \\
    --config configs/experiment/default.yaml \\
    --symbolic \\
    -o /tmp/thesis_schematic.pdf

  PYTHONPATH=src python3 scripts/generate_thesis_diagram.py \\
    --config experiments/<run_id>/config.yaml \\
    -o thesis_schematic.pdf
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build thesis-style config + signal pipeline schematic (PDF/PNG/SVG)."
    )
    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to experiment config.yaml (ExperimentConfig format).",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Output path (.pdf, .png, or .svg). Default: <config_dir>/thesis_schematic.pdf",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for split sampling (default: seed from YAML or 42).",
    )
    parser.add_argument(
        "--symbolic",
        action="store_true",
        help="Skip dataset load; show set logic with estimated counts only.",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=PROJECT_ROOT,
        help="Repository root for dataset paths (default: script parent directory).",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Raster DPI when exporting PNG (default: 300).",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Open interactive matplotlib window after saving.",
    )
    args = parser.parse_args(argv)

    config_path = args.config.resolve()
    if not config_path.is_file():
        print(f"Config not found: {config_path}", file=sys.stderr)
        return 1

    from uqlab.shared.config.classification import ExperimentConfig
    from uqlab.evaluation.pipeline.thesis_diagram import (
        build_thesis_figure,
        load_thesis_diagram_inputs,
        save_thesis_figure,
    )

    config = ExperimentConfig.from_yaml(config_path)
    seed = args.seed if args.seed is not None else int(config.seed)
    output = args.output
    if output is None:
        output = config_path.parent / "thesis_schematic.pdf"

    print(f"Config: {config_path}")
    print(f"Mode: {'symbolic' if args.symbolic else 'empirical (load dataset + split)'}")
    print(f"Seed: {seed}")

    try:
        inputs = load_thesis_diagram_inputs(
            config,
            args.project_root.resolve(),
            seed=seed,
            empirical=not args.symbolic,
        )
    except Exception as exc:
        print(f"Failed to build diagram inputs: {exc}", file=sys.stderr)
        return 1

    counts = inputs.split_counts or {}
    print(
        "Split counts:",
        f"train={counts.get('train')}",
        f"clean={counts.get('clean')}",
        f"aleatoric={counts.get('aleatoric')}",
        f"epistemic={counts.get('epistemic')}",
    )
    print(f"Enabled signals ({len(inputs.enabled_signals)}):", ", ".join(inputs.enabled_signals))

    fig = build_thesis_figure(inputs)
    saved = save_thesis_figure(fig, output, dpi=args.dpi)
    print(f"Wrote {saved}")

    if args.show:
        import matplotlib.pyplot as plt

        plt.show()
    else:
        import matplotlib.pyplot as plt

        plt.close(fig)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
