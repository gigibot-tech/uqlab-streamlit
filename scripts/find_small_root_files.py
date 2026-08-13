#!/usr/bin/env python3
"""Audit a root folder for small files that may be relocation candidates.

Usage:
    python scripts/find_small_root_files.py [PATH] [--threshold 300] [--depth 1]

By default only direct children of PATH are checked. Use --depth 0 for a
recursive scan.
"""

from __future__ import annotations

import argparse
from pathlib import Path

EXCLUDED_DIRS = {
    ".git",
    ".cursor",
    ".vscode",
    ".docs",
    ".bob",
    "__pycache__",
    "node_modules",
    ".venv",
    "dead_code",
}
EXCLUDED_FILES = {".DS_Store", "uv.lock", "dependencies.json"}

SUGGESTIONS: dict[str, str] = {
    ".sh": "scripts/deployment or scripts/maintenance",
    ".py": "scripts/ (utility) or src/... (library code)",
    ".md": "docs/ or docs/development",
    ".yaml": "configs/ or configs/experiment",
    ".yml": "configs/ or configs/experiment",
    ".ini": "project root (keep)",
    ".toml": "project root (keep)",
    ".txt": "data/ or results/ (if generated)",
    ".json": "data/ or configs/",
    ".html": "backend/templates or uqlab-flask/templates",
    ".css": "uqlab-flask/static or backend/static",
}


def line_count(path: Path) -> int:
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        return sum(1 for _ in f)


def is_text(path: Path) -> bool:
    if path.name in EXCLUDED_FILES:
        return False
    if path.stat().st_size > 2_000_000:
        return False
    try:
        data = path.read_bytes()[:1024]
    except Exception:
        return False
    if b"\x00" in data:
        return False
    return True


def collect_files(root: Path, depth: int | None) -> list[Path]:
    if depth == 1:
        return [p for p in root.iterdir() if p.is_file() and not p.is_symlink()]

    files: list[Path] = []
    max_depth = depth if depth and depth > 0 else None
    for current_dir, dirs, filenames in root.rglob("*"):
        if current_dir.name in EXCLUDED_DIRS or any(
            part in EXCLUDED_DIRS for part in current_dir.relative_to(root).parts
        ):
            dirs[:] = []
            continue
        if max_depth is not None:
            rel_parts = current_dir.relative_to(root).parts
            if len(rel_parts) >= max_depth:
                dirs[:] = []
        for name in filenames:
            path = current_dir / name
            if path.is_symlink() or not path.is_file():
                continue
            files.append(path)
    return files


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Find small files in a root folder that could be relocated."
    )
    parser.add_argument("path", nargs="?", default=".", help="Root folder to scan")
    parser.add_argument(
        "--threshold", type=int, default=300, help="Line-count threshold (default: 300)"
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=1,
        help="Depth to scan: 1 = direct children only, 0 = recursive (default: 1)",
    )
    args = parser.parse_args()

    root = Path(args.path).resolve()
    if not root.is_dir():
        raise SystemExit(f"{root} is not a directory")

    print(f"Scanning: {root}")
    print(f"Threshold: <= {args.threshold} LoC")
    print(f"Depth: {'direct children' if args.depth == 1 else 'recursive'}")
    print("=" * 72)

    candidates: list[tuple[int, Path, str, str]] = []
    for path in collect_files(root, args.depth):
        if not is_text(path):
            continue
        try:
            loc = line_count(path)
        except Exception:
            continue
        if loc <= args.threshold:
            rel = path.relative_to(root)
            ext = path.suffix.lower()
            suggestion = SUGGESTIONS.get(ext, "review manually")
            candidates.append((loc, rel, ext, suggestion))

    if not candidates:
        print("No small files found.")
        return

    candidates.sort(key=lambda x: (x[2], x[0], str(x[1])))
    for loc, rel, ext, suggestion in candidates:
        print(f"{loc:4d}  {ext or 'none':6}  {rel}  ->  {suggestion}")

    print("=" * 72)
    print(f"Total candidates: {len(candidates)}")


if __name__ == "__main__":
    main()
