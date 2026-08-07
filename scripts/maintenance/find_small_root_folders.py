#!/usr/bin/env python3
"""Detect root-level folders whose files are all smaller than a LoC threshold.

The script scans the repository root and reports folders where every file is below
configurable line-count thresholds (default 200/300). Such folders are candidates for
co-location with a sibling package (e.g. backend/, src/, scripts/) when that reduces
surface clutter and the move can be done without breaking path references.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import NamedTuple


class FolderStats(NamedTuple):
    path: Path
    file_count: int
    total_lines: int
    max_lines: int
    files: list[tuple[Path, int]]


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
    """Return immediate subdirectories of the repo root, excluding common tooling dirs."""
    folders: list[Path] = []
    for entry in sorted(repo_root.iterdir()):
        if entry.is_dir() and entry.name not in DEFAULT_IGNORE_DIRS:
            folders.append(entry)
    return folders


def analyze_folder(folder: Path) -> FolderStats:
    """Gather line-count stats for every tracked file under ``folder``."""
    files: list[tuple[Path, int]] = []
    for path in sorted(folder.rglob("*")):
        if not path.is_file():
            continue
        # Skip git internals, virtual environments, and generated caches regardless of depth.
        if any(part in DEFAULT_IGNORE_DIRS for part in path.parts):
            continue
        try:
            with path.open("r", encoding="utf-8", errors="ignore") as f:
                lines = sum(1 for _ in f)
        except OSError:
            continue
        rel = path.relative_to(folder)
        files.append((rel, lines))

    total = sum(lines for _, lines in files)
    max_lines = max((lines for _, lines in files), default=0)
    return FolderStats(
        path=folder,
        file_count=len(files),
        total_lines=total,
        max_lines=max_lines,
        files=files,
    )


def suggest_relocation(stats: FolderStats, repo_root: Path) -> str:
    """Return a heuristic recommendation for where the folder could live."""
    name = stats.path.name.lower()

    if name == "configs":
        return "candidate, but keep at root: experiment presets are user-facing and referenced by runtime_paths.configs_dir(), docs, notebooks, and runners; move only if every reference is updated"
    if name == "data":
        return "candidate, but keep at root: runtime_paths.data_root() defaults to <repo>/data; relocating requires an env override or code change"
    if name in {"backend", "src", "tests"}:
        return "not a candidate: these are primary packages and should stay at root"
    if name in {"scripts", "notebooks", "docs"}:
        return "not a candidate: content category folder, conventionally at root"
    if "flask" in name or "api" in name:
        return "candidate: could fold into backend/ or src/ if it does not duplicate FastAPI functionality; largest file may exceed threshold"
    if stats.file_count == 0:
        return "empty folder; can be removed if no longer needed"
    return "review manually: no strong heuristic match"


def format_report(stats: FolderStats, threshold: int, repo_root: Path) -> str:
    """Build a human-readable report for a single folder."""
    qualifies = stats.max_lines < threshold and stats.file_count > 0
    status = "✅ qualifies" if qualifies else "❌ does not qualify"
    lines = [
        f"\n{stats.path.name}/",
        f"  status: {status} (threshold={threshold} LoC)",
        f"  files: {stats.file_count}",
        f"  total lines: {stats.total_lines}",
        f"  largest file: {stats.max_lines} LoC",
        f"  relocation: {suggest_relocation(stats, repo_root)}",
    ]
    if stats.files and qualifies:
        lines.append("  file breakdown:")
        for rel, count in stats.files:
            lines.append(f"    - {rel}: {count} LoC")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Find root folders with small files that could be relocated."
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
    args = parser.parse_args()

    repo_root = args.root.resolve()
    folders = collect_root_folders(repo_root)

    print(f"Scanning root folders under {repo_root}")
    print(f"Excluding: {', '.join(sorted(DEFAULT_IGNORE_DIRS))}")

    for threshold in args.thresholds:
        print(f"\n{'=' * 60}")
        print(f"Threshold: {threshold} LoC")
        print("=" * 60)
        for folder in folders:
            stats = analyze_folder(folder)
            print(format_report(stats, threshold, repo_root))

    # Final summary
    print(f"\n{'=' * 60}")
    print("Summary of qualifying folders")
    print("=" * 60)
    found_any = False
    for threshold in args.thresholds:
        for folder in folders:
            stats = analyze_folder(folder)
            if stats.max_lines < threshold and stats.file_count > 0:
                found_any = True
                print(f"- {folder.name}/ (max={stats.max_lines} LoC, total={stats.total_lines} LoC) under threshold {threshold}")
    if not found_any:
        print("No qualifying folders found.")


if __name__ == "__main__":
    main()
