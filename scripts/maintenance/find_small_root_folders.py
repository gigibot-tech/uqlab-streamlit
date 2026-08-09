#!/usr/bin/env python3
"""Scan the repo root and report folders whose files are all below a LoC threshold.

Typical use:
    python scripts/maintenance/find_small_root_folders.py
    python scripts/maintenance/find_small_root_folders.py --threshold 200

The script excludes binary files (images, lock files, PDFs, etc.) and only
considers text files. It then prints a candidate relocation recommendation for
each folder that is small enough to move.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Iterable

DEFAULT_THRESHOLD = 300
DEFAULT_ROOT = Path(__file__).resolve().parents[2]

# Extensions we treat as non-text / binary and ignore for LoC purposes.
SKIP_EXTS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".pdf",
    ".lock",
    ".pyc",
    ".pyo",
    ".so",
    ".dylib",
    ".dll",
    ".exe",
    ".tar",
    ".tar.gz",
    ".tgz",
    ".zip",
    ".7z",
    ".rar",
}

# Tooling folders that are conventionally kept at repo root even if small.
KEEP_AT_ROOT = {
    ".cursor",
    ".vscode",
    ".bob",
    ".github",
    ".git",
    ".docs",
    "data",
}


def is_text_file(path: Path) -> bool:
    """Heuristic: file is text if it contains no null bytes in the first 1 KiB."""
    try:
        with path.open("rb") as f:
            chunk = f.read(1024)
    except OSError:
        return False
    return b"\x00" not in chunk


def count_lines(path: Path) -> int:
    """Return the number of lines in a text file."""
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        return sum(1 for _ in f)


def scan_directory(
    directory: Path,
    *,
    skip_exts: Iterable[str] | None = None,
) -> list[tuple[Path, int]]:
    """Return list of (relative_path, line_count) for text files under directory."""
    skip_exts = set(skip_exts or SKIP_EXTS)
    results: list[tuple[Path, int]] = []
    for file_path in directory.rglob("*"):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() in skip_exts:
            continue
        if not is_text_file(file_path):
            continue
        try:
            line_count = count_lines(file_path)
        except OSError:
            continue
        rel = file_path.relative_to(directory)
        results.append((rel, line_count))
    return results


def recommendation(name: str, max_lines: int, files: list[tuple[Path, int]]) -> str:
    """Return a heuristic relocation recommendation for a small root folder."""
    if name in KEEP_AT_ROOT:
        return "keep at root (tooling / convention)"

    if name == "configs":
        return "candidate: could move to src/uqlab_core/configs/ (update runtime_paths.configs_dir and hardcoded references)"

    if max_lines == 0 and len(files) <= 1:
        return "keep at root (empty runtime data directory)"

    return "candidate: evaluate relocation to a dedicated subdirectory"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Find root folders whose files are all below a LoC threshold.",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=DEFAULT_THRESHOLD,
        help=f"LoC threshold (default: {DEFAULT_THRESHOLD}).",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_ROOT,
        help=f"Repo root to scan (default: {DEFAULT_ROOT}).",
    )
    args = parser.parse_args()

    root: Path = args.root.resolve()
    threshold: int = args.threshold

    print(f"Scanning root folders under {root} (threshold: {threshold} LoC)")
    print("=" * 80)

    candidates: list[tuple[str, int, int, list[tuple[Path, int]], str]] = []

    for entry in sorted(root.iterdir()):
        if not entry.is_dir() or entry.name == ".git":
            continue

        files = scan_directory(entry)
        if not files:
            continue

        max_lines = max(line_count for _, line_count in files)
        total_lines = sum(line_count for _, line_count in files)
        all_under_threshold = max_lines <= threshold

        rec = recommendation(entry.name, max_lines, files)
        is_candidate = all_under_threshold and entry.name not in KEEP_AT_ROOT

        if is_candidate:
            candidates.append((entry.name, max_lines, total_lines, files, rec))

        status = f"all <= {threshold}" if all_under_threshold else f"max = {max_lines}"
        marker = "✅ CANDIDATE" if is_candidate else "—"
        print(
            f"{entry.name:20} files={len(files):3}  max={max_lines:6}  "
            f"total={total_lines:8}  {status:16}  {rec} {marker}"
        )

    print("=" * 80)
    if candidates:
        print(f"Found {len(candidates)} candidate folder(s) with all files <= {threshold} LoC:")
        for name, max_lines, total_lines, files, rec in candidates:
            print(f"  • {name}: {len(files)} files, max {max_lines} lines, total {total_lines} lines")
            print(f"    -> {rec}")
    else:
        print(f"No root folders have all files <= {threshold} LoC and be relocation candidates.")


if __name__ == "__main__":
    main()
