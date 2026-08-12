#!/usr/bin/env python3
"""
Find small-file relocation candidates in root-level folders.

Scans the immediate subdirectories of a project root, counts non-empty lines for
each file, and flags folders where most files are below configured thresholds.
The goal is to identify self-contained root folders that are small enough to be
relocated into a package or merged into a more appropriate location.

Usage:
    python scripts/maintenance/find_small_file_relocation_candidates.py
    python scripts/maintenance/find_small_file_relocation_candidates.py \
        --root /workspace --thresholds 200 300 --output candidates.json
"""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from pathlib import Path

# Files and directories that are not relevant when sizing a package for relocation.
SKIP_NAMES: set[str] = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "node_modules",
    ".DS_Store",
    "*.egg-info",
}
SKIP_EXTENSIONS: set[str] = {".pyc", ".pyo", ".so", ".dylib", ".dll"}


@dataclass
class FileMetrics:
    """Line-count metrics for a single file."""

    path: str
    total_lines: int
    code_lines: int


@dataclass
class FolderMetrics:
    """Aggregated metrics for a root-level folder."""

    name: str
    path: str
    files: list[FileMetrics] = field(default_factory=list)
    total_files: int = 0
    files_under_threshold: dict[str, int] = field(default_factory=dict)
    small_files_percentage: dict[str, float] = field(default_factory=dict)
    median_lines: int = 0
    average_lines: float = 0.0


def should_skip(path: Path) -> bool:
    """Return True if the path should be ignored when counting lines."""
    if any(part in SKIP_NAMES or part.endswith(".egg-info") for part in path.parts):
        return True
    if path.suffix.lower() in SKIP_EXTENSIONS:
        return True
    return bool(path.name.startswith(".") and path.is_dir())


def count_lines(path: Path) -> tuple[int, int]:
    """Return (total_lines, code_lines) for a text file.

    Falls back to a binary-safe read for files that are not UTF-8.
    """
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except (OSError, UnicodeDecodeError):
        return 0, 0

    total_lines = len(text.splitlines())
    code_lines = sum(
        1
        for line in text.splitlines()
        if line.strip() and not line.strip().startswith("#")
    )
    return total_lines, code_lines


def gather_root_folders(root: Path) -> Iterable[Path]:
    """Yield top-level directories inside ``root`` that are not skipped."""
    if not root.is_dir():
        return
    for child in sorted(root.iterdir()):
        if child.is_dir() and not should_skip(child):
            yield child


def analyze_folder(folder: Path, thresholds: list[int]) -> FolderMetrics:
    """Analyze all files inside ``folder`` and return aggregate metrics."""
    metrics = FolderMetrics(name=folder.name, path=str(folder))
    all_line_counts: list[int] = []

    for file_path in sorted(folder.rglob("*")):
        if not file_path.is_file() or should_skip(file_path):
            continue
        total_lines, code_lines = count_lines(file_path)
        if total_lines == 0 and code_lines == 0:
            # Skip empty marker files such as .gitkeep or __init__.py placeholders.
            continue
        metrics.files.append(
            FileMetrics(
                path=str(file_path.relative_to(folder)),
                total_lines=total_lines,
                code_lines=code_lines,
            )
        )
        all_line_counts.append(total_lines)

    metrics.total_files = len(metrics.files)

    for threshold in thresholds:
        metrics.files_under_threshold[threshold] = sum(
            1 for f in metrics.files if f.total_lines <= threshold
        )
        metrics.small_files_percentage[threshold] = round(
            metrics.files_under_threshold[threshold] / max(metrics.total_files, 1) * 100, 1
        )

    if all_line_counts:
        sorted_counts = sorted(all_line_counts)
        mid = len(sorted_counts) // 2
        metrics.median_lines = (
            sorted_counts[mid]
            if len(sorted_counts) % 2
            else (sorted_counts[mid - 1] + sorted_counts[mid]) // 2
        )
        metrics.average_lines = round(sum(all_line_counts) / len(all_line_counts), 1)

    return metrics


def build_report(
    root: Path,
    thresholds: list[int],
    candidate_min_percentage: float = 75.0,
    max_files: int = 50,
    max_avg_lines: int | None = None,
) -> dict:
    """Build a report of root folders and small-file relocation candidates.

    A folder is considered a relocation candidate when it is small enough to move as
    a unit: few files, low average line count, and most files below the largest
    threshold. This filters out large, well-established roots such as ``backend/`` or
    ``docs/`` that happen to contain many tiny files.
    """
    folders = [analyze_folder(folder, thresholds) for folder in gather_root_folders(root)]
    folders.sort(key=lambda f: (f.median_lines, f.total_files))

    largest_threshold = max(thresholds)
    max_avg = max_avg_lines if max_avg_lines is not None else largest_threshold

    candidates = []
    for folder in folders:
        if folder.total_files == 0 or folder.total_files > max_files:
            continue
        if folder.median_lines > largest_threshold or folder.average_lines > max_avg:
            continue

        small_pct = folder.small_files_percentage.get(largest_threshold, 0)
        if small_pct >= candidate_min_percentage:
            candidates.append(folder)

    return {
        "root": str(root),
        "thresholds": thresholds,
        "candidate_min_percentage": candidate_min_percentage,
        "max_files": max_files,
        "max_avg_lines": max_avg,
        "folders": [asdict(f) for f in folders],
        "candidates": [asdict(f) for f in candidates],
    }


def print_report(report: dict) -> None:
    """Print a human-readable summary of the report."""
    thresholds = report["thresholds"]
    largest = max(thresholds)
    max_files = report.get("max_files", 50)
    max_avg = report.get("max_avg_lines", largest)

    print(f"Root: {report['root']}")
    print(f"Thresholds: {thresholds} lines")
    print(
        f"Candidate rule: total files <= {max_files}, median <= {largest} lines, "
        f"average <= {max_avg} lines, and "
        f">= {report['candidate_min_percentage']}% of files under {largest} lines\n"
    )

    print("=" * 80)
    print("ALL ROOT FOLDERS (sorted by median lines)")
    print("=" * 80)
    for folder in report["folders"]:
        print(f"\n{folder['name']}/")
        print(f"  path: {folder['path']}")
        print(f"  files: {folder['total_files']}")
        print(f"  median / average lines: {folder['median_lines']} / {folder['average_lines']}")
        for threshold in thresholds:
            pct = folder["small_files_percentage"].get(threshold, 0)
            count = folder["files_under_threshold"].get(threshold, 0)
            print(f"  files <= {threshold} LoC: {count} ({pct}%)")
        print("  sample files:")
        for file in folder["files"][:5]:
            print(f"    - {file['path']}: {file['total_lines']} lines")
        if len(folder["files"]) > 5:
            print(f"    ... and {len(folder['files']) - 5} more")

    print("\n" + "=" * 80)
    print("RELOCATION CANDIDATES")
    print("=" * 80)
    if not report["candidates"]:
        print("No root folders meet the candidate criteria.")
        return

    for candidate in report["candidates"]:
        print(f"\n{candidate['name']}/")
        print(f"  median lines: {candidate['median_lines']}")
        print(f"  average lines: {candidate['average_lines']}")
        print(f"  files under {largest} lines: {candidate['files_under_threshold'][largest]}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Find small-file relocation candidates in root-level folders."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(os.environ.get("WORKSPACE", ".")),
        help="Project root to scan (default: current directory or $WORKSPACE)",
    )
    parser.add_argument(
        "--thresholds",
        nargs="+",
        type=int,
        default=[200, 300],
        help="Line-count thresholds to evaluate (default: 200 300)",
    )
    parser.add_argument(
        "--candidate-min-percentage",
        type=float,
        default=75.0,
        help="Minimum percentage of files under the largest threshold to flag a folder",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=50,
        help="Maximum number of files in a candidate folder (default: 50)",
    )
    parser.add_argument(
        "--max-avg-lines",
        type=int,
        default=None,
        help="Maximum average line count for a candidate folder (default: largest threshold)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional JSON file to write the full report",
    )
    args = parser.parse_args()

    args.root = args.root.resolve()
    thresholds = sorted(args.thresholds)

    report = build_report(
        args.root,
        thresholds,
        candidate_min_percentage=args.candidate_min_percentage,
        max_files=args.max_files,
        max_avg_lines=args.max_avg_lines,
    )
    print_report(report)

    if args.output:
        args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"\nReport written to: {args.output}")


if __name__ == "__main__":
    main()
