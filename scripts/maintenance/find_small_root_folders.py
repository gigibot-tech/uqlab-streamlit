#!/usr/bin/env python3
"""Detect root-level folders whose immediate files are small relocation candidates.

Scans the repository root and reports folders where every file placed directly in
the folder is below configurable line-count thresholds (default 200/300). Recursive
subdirectories are summarized separately, so a folder with a small top-level
surface but a large package underneath is still visible.

The script writes a Markdown report to ``docs/development/SMALL_FILE_RELOCATION_CANDIDATES.md``.

Usage:
    python3 scripts/maintenance/find_small_root_folders.py
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple


class FolderStats(NamedTuple):
    path: Path
    root_file_count: int
    root_total_lines: int
    root_max_lines: int
    root_files: list[tuple[Path, int]]
    recursive_file_count: int
    recursive_total_lines: int
    recursive_max_lines: int


DEFAULT_IGNORE_DIRS = {
    ".git",
    ".cursor",
    ".vscode",
    ".bob",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    ".DS_Store",
}


def collect_root_folders(repo_root: Path) -> list[Path]:
    """Return immediate subdirectories of the repo root, excluding tooling and hidden dirs."""
    folders: list[Path] = []
    for entry in sorted(repo_root.iterdir()):
        if (
            entry.is_dir()
            and entry.name not in DEFAULT_IGNORE_DIRS
            and not entry.name.startswith(".")
            and not entry.is_symlink()
        ):
            folders.append(entry)
    return folders


def _count_lines(path: Path) -> int:
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            return sum(1 for _ in f)
    except OSError:
        return 0


def _is_skipped(path: Path) -> bool:
    if not path.is_file():
        return True
    if any(part in DEFAULT_IGNORE_DIRS for part in path.parts):
        return True
    return False


def analyze_folder(folder: Path) -> FolderStats:
    root_files: list[tuple[Path, int]] = []
    all_files: list[tuple[Path, int]] = []

    for path in sorted(folder.rglob("*")):
        if _is_skipped(path):
            continue
        rel = path.relative_to(folder)
        lines = _count_lines(path)
        all_files.append((rel, lines))
        if path.parent == folder:
            root_files.append((rel, lines))

    root_total = sum(lines for _, lines in root_files)
    root_max = max((lines for _, lines in root_files), default=0)

    recursive_total = sum(lines for _, lines in all_files)
    recursive_max = max((lines for _, lines in all_files), default=0)

    return FolderStats(
        path=folder,
        root_file_count=len(root_files),
        root_total_lines=root_total,
        root_max_lines=root_max,
        root_files=root_files,
        recursive_file_count=len(all_files),
        recursive_total_lines=recursive_total,
        recursive_max_lines=recursive_max,
    )


def suggest_relocation(stats: FolderStats, repo_root: Path) -> str:
    """Return a heuristic recommendation for where the folder could live."""
    name = stats.path.name.lower()

    if name == "configs":
        return (
            "candidate: all root-level YAML presets are small. Could fold into "
            "``src/uqlab_core/configs/`` so presets ship with the package, but "
            "``runtime_paths.configs_dir()``, README, and every CLI/notebook "
            "reference must be updated."
        )
    if name == "data":
        if stats.recursive_file_count == 0:
            return (
                "empty folder except ``.gitkeep``; can be removed if "
                "``runtime_paths.data_root()`` recreates it on demand"
            )
        return (
            "candidate, but keep at root: ``runtime_paths.data_root()`` defaults "
            "to ``<repo>/data``; relocating requires an env override or code change"
        )
    if name in {"backend", "src", "tests"}:
        return "not a candidate: primary package folder, conventionally at root"
    if name in {"scripts", "notebooks", "docs"}:
        return "not a candidate: content category folder, conventionally at root"
    if "flask" in name or "api" in name:
        return (
            "candidate: root-level files are small, but the package underneath is "
            "substantial; could move into ``backend/``, ``frontend/``, or a new ``ui/`` "
            "folder"
        )
    if stats.root_file_count == 0:
        return "no files at root level; review whether the folder is still needed"
    return "review manually: no strong heuristic match"


def _format_root_files(root_files: list[tuple[Path, int]], threshold: int) -> str:
    lines: list[str] = []
    for rel, count in sorted(root_files, key=lambda item: item[1], reverse=True):
        marker = "✅" if count < threshold else "❌"
        lines.append(f"  - {rel}: {count} LoC {marker}")
    return "\n".join(lines)


def _qualifying_folders(
    stats_list: list[FolderStats], threshold: int
) -> list[FolderStats]:
    return [
        stats
        for stats in stats_list
        if stats.root_max_lines < threshold and stats.root_file_count > 0
    ]


def _executive_summary(
    stats_list: list[FolderStats], thresholds: list[int], repo_root: Path
) -> str:
    paragraphs = [
        "## Executive Summary",
        "",
        "The following root-level folders have *every* immediate file below the "
        "configured LoC thresholds. They are the best candidates for relocation "
        "if their dependencies and in-tree references can be updated safely.",
        "",
    ]
    for threshold in thresholds:
        qualifying = _qualifying_folders(stats_list, threshold)
        paragraphs.append(f"### Under {threshold} LoC")
        paragraphs.append("")
        if not qualifying:
            paragraphs.append("No qualifying folders found.")
        else:
            for stats in qualifying:
                paragraphs.append(
                    f"- `{stats.path.name}/` — root max {stats.root_max_lines} LoC, "
                    f"recursive max {stats.recursive_max_lines} LoC; "
                    f"{suggest_relocation(stats, repo_root)}"
                )
        paragraphs.append("")
    return "\n".join(paragraphs)


def generate_report(
    repo_root: Path, stats_list: list[FolderStats], thresholds: list[int]
) -> str:
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    threshold_cols = " | ".join(f"<{t} LoC" for t in thresholds)
    lines = [
        "# Small Root-Folder Relocation Candidates",
        "",
        f"**Date:** {date}  ",
        "**Branch:** `cursor/small-file-relocation-candidates-5e7f`  ",
        "**Scope:** Root-level folders whose *immediate* files are below "
        "200–300 lines of code.",
        "",
        _executive_summary(stats_list, thresholds, repo_root),
        "## Methodology",
        "",
        "For each folder directly under the repository root we count two things:",
        "",
        "1. **Root-level files** — files placed immediately inside the folder.",
        "2. **Recursive files** — all files in the folder and its subdirectories.",
        "",
        "A folder is flagged as a *candidate* when every root-level file is smaller "
        "than the threshold. Recursive totals are shown separately so large nested "
        "packages are not hidden.",
        "",
        f"Thresholds tested: {', '.join(map(str, thresholds))} LoC.",
        "",
        "## Results",
        "",
        f"| Folder | Root files | Root max | {threshold_cols} | Recursive max | Relocation note |",
        "|--------|-----------:|---------:|" + "|".join([":-:"] * len(thresholds)) + "|:-:|:----------------|",
    ]

    for stats in stats_list:
        qualifies = [
            "✅" if stats.root_max_lines < t and stats.root_file_count > 0 else "❌"
            for t in thresholds
        ]
        qualifies_cells = " | ".join(qualifies)
        note = suggest_relocation(stats, repo_root)
        lines.append(
            f"| `{stats.path.name}/` | {stats.root_file_count} | {stats.root_max_lines} "
            f"| {qualifies_cells} | {stats.recursive_max_lines} | {note} |"
        )

    lines.extend(["", "## Per-Folder Breakdown", ""])

    for stats in stats_list:
        lines.extend(
            [
                f"### `{stats.path.name}/`",
                "",
                f"- **Root-level files:** {stats.root_file_count} "
                f"({stats.root_total_lines} LoC total, max {stats.root_max_lines} LoC)",
                f"- **Recursive files:** {stats.recursive_file_count} "
                f"({stats.recursive_total_lines} LoC total, max {stats.recursive_max_lines} LoC)",
                f"- **Relocation note:** {suggest_relocation(stats, repo_root)}",
                "",
                "Root-level file breakdown:",
                "",
            ]
        )
        if stats.root_files:
            for threshold in thresholds:
                lines.append(f"Under {threshold} LoC:")
                lines.append(_format_root_files(stats.root_files, threshold))
                lines.append("")
        else:
            lines.append("No files directly at this folder level.")
            lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Find root folders whose immediate files are small enough to relocate."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Repository root to scan (default: current working directory).",
    )
    parser.add_argument(
        "--thresholds",
        nargs="+",
        type=int,
        default=[200, 300],
        help="LoC thresholds to test (default: 200 300).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/development/SMALL_FILE_RELOCATION_CANDIDATES.md"),
        help="Path for the generated markdown report.",
    )
    args = parser.parse_args()

    repo_root = args.root.resolve()
    folders = collect_root_folders(repo_root)
    stats_list = [analyze_folder(folder) for folder in folders]

    report = generate_report(repo_root, stats_list, args.thresholds)

    output_path = repo_root / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print(f"Report written to {output_path}")

    print(f"\nScanning root folders under {repo_root}")
    for threshold in args.thresholds:
        print(f"\nThreshold: {threshold} LoC")
        for stats in stats_list:
            qualifies = stats.root_max_lines < threshold and stats.root_file_count > 0
            status = "✅ qualifies" if qualifies else "❌ does not qualify"
            print(
                f"  {stats.path.name}/ — {status} (root max {stats.root_max_lines} LoC)"
            )


if __name__ == "__main__":
    main()
