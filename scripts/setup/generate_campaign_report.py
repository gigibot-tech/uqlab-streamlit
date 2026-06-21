#!/usr/bin/env python3
"""
Export a full campaign PDF report: config timeline + sweep line plot(s).

Example
-------
  cd uqlab-streamlit
  PYTHONPATH=src python3 scripts/generate_campaign_report.py \\
    --run-ids uuid1,uuid2,uuid3 \\
    --signal msp_uncertainty \\
    -o /tmp/campaign_report.pdf
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _parse_facets(pairs: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in pairs:
        if "=" not in item:
            continue
        key, val = item.split("=", 1)
        out[key.strip()] = val.strip()
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build campaign PDF (timeline + sweep plots).")
    parser.add_argument("--run-ids", required=True, help="Comma-separated experiment UUIDs.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=PROJECT_ROOT / "campaign_report.pdf",
    )
    parser.add_argument(
        "--experiments-dir",
        type=Path,
        default=PROJECT_ROOT / "data" / "experiments",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=PROJECT_ROOT,
    )
    parser.add_argument(
        "--sweep-kind",
        choices=("auto", "label_noise", "dataset_size"),
        default="auto",
    )
    parser.add_argument("--signal", default=None, help="Uncertainty signal column (default: axis default).")
    parser.add_argument(
        "--extra-signals",
        type=int,
        default=0,
        help="Append up to N additional signal plots after the primary.",
    )
    parser.add_argument(
        "--facet",
        action="append",
        default=[],
        metavar="KEY=VALUE",
    )
    parser.add_argument("--title", default=None)
    args = parser.parse_args(argv)

    from uqlab.evaluation.classification.pipeline.campaign_report import build_campaign_report_pdf

    run_ids = [r.strip() for r in args.run_ids.split(",") if r.strip()]
    experiments = [{"id": rid, "status": "completed", "name": rid[:8]} for rid in run_ids]
    sweep_kind = None if args.sweep_kind == "auto" else args.sweep_kind
    facet_filters = _parse_facets(args.facet) or None

    try:
        pdf_bytes, timeline = build_campaign_report_pdf(
            experiments,
            args.experiments_dir.resolve(),
            args.output.resolve(),
            project_root=args.project_root.resolve(),
            sweep_kind=sweep_kind,
            facet_filters=facet_filters,
            signal=args.signal,
            title=args.title,
            extra_signals=max(0, args.extra_signals),
        )
    except Exception as exc:
        print(f"Failed: {exc}", file=sys.stderr)
        return 1

    print(f"Campaign: {timeline.title}")
    print(f"Steps: {timeline.n_runs}")
    print(f"Wrote {args.output.resolve()} ({len(pdf_bytes)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
