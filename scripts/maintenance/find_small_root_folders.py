#!/usr/bin/env python3
"""Find root-level folders whose files are all below a LoC threshold.

Usage:
    python scripts/maintenance/find_small_root_folders.py [ROOT]

Defaults to the repository root (the directory containing this script's
../../.. path). Prints a Markdown table of folder statistics and flags
candidates where every file is below 200/300 LoC and the folder is
non-trivial (> 1 file).
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Folders that should never be considered for relocation.
IGNORED_ROOT_DIRS = {
    ".git",
    "__pycache__",
    ".cursor",
    ".vscode",
    ".docs",
    ".DS_Store",
    "node_modules",
}

# File names/patterns to ignore while counting.
IGNORED_FILE_PARTS = {
    ".DS_Store",
    ".gitkeep",
    "__pycache__",
}


def is_text_file(path: Path) -> bool:
    """Return True for regular files we want to count."""
    if not path.is_file():
        return False
    if path.name in IGNORED_FILE_PARTS:
        return False
    if any(part in IGNORED_ROOT_DIRS for part in path.parts):
        return False
    return True


def count_lines(path: Path) -> int:
    """Count lines in a text file, tolerating encoding issues."""
    try:
        return len(path.read_text(encoding="utf-8", errors="ignore").splitlines())
    except OSError:
        return 0


def gather_root_folders(root: Path) -> list[Path]:
    """Return immediate subdirectories of root that are worth scanning."""
    return [
        d
        for d in sorted(root.iterdir())
        if d.is_dir() and d.name not in IGNORED_ROOT_DIRS and not d.name.startswith(".")
    ]


def scan_folder(folder: Path) -> tuple[int, int, int, list[tuple[Path, int]]]:
    """Return (file_count, total_loc, max_loc, [(path, loc), ...])."""
    files = [p for p in folder.rglob("*") if is_text_file(p)]
    locs = [(p, count_lines(p)) for p in files]
    total = sum(loc for _, loc in locs)
    max_loc = max((loc for _, loc in locs), default=0)
    return len(files), total, max_loc, locs


def format_table(rows: list[tuple[str, int, int, int, bool, bool, str]]) -> str:
    """Format scan results as a Markdown table."""
    lines = [
        "| Folder | Files | Total LoC | Max LoC | < 200 | < 300 | Candidate |",
        "|--------|------:|----------:|--------:|:-----:|:-----:|:---------:|",
    ]
    for folder, files, total, max_loc, under_200, under_300, candidate in rows:
        lines.append(
            f"| {folder:18s} | {files:5d} | {total:9d} | {max_loc:7d} |"
            f" {'✅' if under_200 else '❌':^5} |"
            f" {'✅' if under_300 else '❌':^5} |"
            f" {candidate:^9} |"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Find small-file root-level relocation candidates."
    )
    parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        default=None,
        help="Repository root (defaults to the checkout root).",
    )
    args = parser.parse_args(argv)

    if args.root is None:
        # This script lives at scripts/maintenance/, so repo root is two levels up.
        root = Path(__file__).resolve().parents[2]
    else:
        root = args.root.resolve()

    if not root.is_dir():
        print(f"Error: {root} is not a directory", file=sys.stderr)
        return 1

    rows: list[tuple[str, int, int, int, bool, bool, str]] = []
    for folder in gather_root_folders(root):
        files, total, max_loc, locs = scan_folder(folder)
        under_200 = all(loc < 200 for _, loc in locs) if files else True
        under_300 = all(loc < 300 for _, loc in locs) if files else True
        candidate = "✅" if (under_200 or under_300) and files > 1 else "—"
        rows.append((folder.name, files, total, max_loc, under_200, under_300, candidate))

    print(f"# Small-file root-folder scan: `{root}`\n")
    print(format_table(rows))
    print()

    candidates = [r for r in rows if r[6] == "✅"]
    if candidates:
        print("Candidates (all files < 200/300 LoC, folder non-trivial):\n")
        for name, files, total, max_loc, *_ in candidates:
            print(f"- `{name}/` — {files} files, {total} total LoC, max {max_loc} LoC")
    else:
        print("No root-level folders meet the candidate criteria.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
