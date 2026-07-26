#!/usr/bin/env python3
"""Find small root-directory relocation candidates.

Scans immediate subdirectories of the project root and reports those whose
text files are all below a line-count threshold (default 300). For known
small root folders it suggests a conventional relocation target and can
optionally perform the move with ``git mv``.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# Project scaffolding that should never be considered for relocation
SKIP_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".pytest_cache",
    ".mypy_cache",
    ".tox",
}

# Conventional targets for known small root folders
KNOWN_TARGETS: dict[str, str] = {
    "configs": "src/uqlab_core/configs",
    ".docs": "backend/docs",
    "data": "src/data",
    "uqlab-flask": "frontend/uqlab-flask",
}


def is_text_file(path: Path) -> bool:
    """Heuristic: skip obvious binary/artifact files."""
    suffix = path.suffix.lower()
    if suffix in {
        ".pyc",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".pdf",
        ".lock",
        ".ico",
        ".ttf",
        ".woff",
        ".woff2",
        ".eot",
    }:
        return False
    if path.name in {".DS_Store", "uv.lock", "package-lock.json"}:
        return False
    return True


def count_lines(path: Path) -> int:
    """Count lines in a text file, returning 0 for unreadable files."""
    try:
        with path.open("rb") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def find_candidates(repo_root: Path, threshold: int) -> list[dict]:
    """Return root directories that are small enough to relocate."""
    candidates = []
    for entry in sorted(repo_root.iterdir()):
        if not entry.is_dir() or entry.is_symlink() or entry.name in SKIP_DIRS:
            continue
        files = [p for p in entry.rglob("*") if p.is_file() and is_text_file(p)]
        if not files:
            continue
        sizes = {p: count_lines(p) for p in files}
        total = sum(sizes.values())
        max_lines = max(sizes.values())
        all_small = all(n <= threshold for n in sizes.values())
        if all_small or total <= threshold:
            candidates.append(
                {
                    "name": entry.name,
                    "path": entry,
                    "total": total,
                    "max": max_lines,
                    "files": len(files),
                    "all_small": all_small,
                    "target": KNOWN_TARGETS.get(entry.name),
                }
            )
    return candidates


def print_report(candidates: list[dict], threshold: int) -> None:
    """Print a human-readable relocation candidate report."""
    print(f"Small root-folder relocation candidates (threshold <= {threshold} LoC per file):")
    print("-" * 60)
    for c in candidates:
        target = c["target"] or "unknown / review manually"
        flag = "ALL_FILES_SMALL" if c["all_small"] else "TOTAL_SMALL"
        print(
            f"{c['name']}: total={c['total']} lines, max={c['max']} lines, "
            f"files={c['files']} [{flag}] -> suggest {target}"
        )
    if not candidates:
        print("No root folder meets the criteria.")


def move_candidate(repo_root: Path, candidate: dict) -> None:
    """Relocate a candidate directory using ``git mv`` (with ``mv`` fallback)."""
    src = candidate["path"]
    target = candidate["target"]
    if not target:
        print(f"No known target for {candidate['name']}; skipping move.", file=sys.stderr)
        return
    dst = repo_root / target
    if dst.exists():
        print(f"Target {dst} already exists; skipping move.", file=sys.stderr)
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(["git", "mv", str(src), str(dst)], check=True)
    except subprocess.CalledProcessError:
        # Some environments (bind mounts, etc.) make git mv fail for directory
        # moves. Fall back to a regular mv and stage the change with git add.
        subprocess.run(["mv", str(src), str(dst)], check=True)
        subprocess.run(["git", "add", "-A"], check=True)
    print(f"Moved {src.name} -> {dst}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Find small root folder relocation candidates.")
    parser.add_argument("--root", default=".", help="Repository root to scan")
    parser.add_argument(
        "--threshold", type=int, default=300, help="Line-count threshold per file"
    )
    parser.add_argument(
        "--apply", action="store_true", help="Move the first known candidate with git mv"
    )
    args = parser.parse_args()

    repo_root = Path(args.root).resolve()
    candidates = find_candidates(repo_root, args.threshold)
    print_report(candidates, args.threshold)

    if args.apply:
        for c in candidates:
            if c["target"]:
                move_candidate(repo_root, c)
                break

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
