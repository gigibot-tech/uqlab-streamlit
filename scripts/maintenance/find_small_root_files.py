#!/usr/bin/env python3
"""Find small files in a root folder that could be relocated.

The script scans the chosen root folder (default: current working directory),
counts lines of code/text for each immediate file, and flags files below the
configured thresholds (default: 200 and 300 lines). For each small file it
suggests a more appropriate destination based on file type/name and estimates
how many references exist inside the repository, so risky moves can be spotted
beforehand.
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path


DEFAULT_THRESHOLDS = (200, 300)

# File names that are conventional root artifacts and should normally stay put.
ROOT_KEEPERS = {
    ".gitignore",
    ".gitignore_parent",
    ".gitmodules",
    ".python-version",
    ".bobignore",
    ".ruffignore",
    ".env",
    ".env.example",
    ".env.production",
    ".env.production.example",
    "pyproject.toml",
    "pytest.ini",
    "mypy.ini",
    "docker-compose.yml",
    "docker-compose.yaml",
    "Makefile",
    "README.md",
    "AGENTS.md",
    "START_HERE.md",
    "uv.lock",
    "package-lock.json",
}


def suggest_destination(path: Path) -> str | None:
    """Return a relocation suggestion for a root-level file, or None to keep."""
    name = path.name
    suffix = path.suffix.lower()

    if name in ROOT_KEEPERS:
        return None

    if suffix == ".sh":
        if "start" in name.lower() or "entrypoint" in name.lower():
            return "scripts/deployment/ (or keep as root entry-point)"
        return "scripts/"

    if suffix == ".py":
        if name.startswith("analyze_") or name.startswith("categorize_"):
            return "scripts/maintenance/"
        if "fix" in name.lower() or "cleanup" in name.lower() or "diagnose" in name.lower():
            return "scripts/maintenance/"
        return "scripts/"

    if suffix in (".md", ".txt"):
        if name == "analysis_results.txt":
            return "docs/validation/"
        if "architecture" in name.lower() or "decision" in name.lower() or "proposal" in name.lower():
            return "docs/architecture/"
        if "guide" in name.lower() or "flow" in name.lower() or "terminology" in name.lower():
            return "docs/"
        if name.endswith("_results.txt"):
            return "docs/ or data/"
        return "docs/"

    if suffix in (".yaml", ".yml"):
        return "configs/"

    return None


def count_references(root: Path, filename: str) -> int:
    """Rough count of textual references to filename anywhere under root."""
    count = 0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if ".git" in path.parts:
            continue
        if path.is_symlink():
            continue
        # Skip large binary-ish files to keep the scan fast and reliable.
        try:
            if path.stat().st_size > 2_000_000:
                continue
        except OSError:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except (OSError, UnicodeDecodeError):
            continue
        if filename in text:
            count += text.count(filename)
    return count


def collect_files(root: Path) -> list[Path]:
    """Return files located directly under root."""
    return sorted(p for p in root.iterdir() if p.is_file())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Root folder to inspect (default: current working directory)",
    )
    parser.add_argument(
        "--thresholds",
        nargs="+",
        type=int,
        default=list(DEFAULT_THRESHOLDS),
        help=f"Line-count thresholds to flag (default: {' '.join(map(str, DEFAULT_THRESHOLDS))})",
    )
    parser.add_argument(
        "--check-references",
        action="store_true",
        help="Scan the repository for textual references to each candidate file",
    )
    args = parser.parse_args(argv)

    root = args.root.resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 1

    thresholds = sorted(set(args.thresholds))
    files = collect_files(root)

    if not files:
        print(f"No files found directly under {root}")
        return 0

    by_threshold: dict[int, list[Path]] = defaultdict(list)
    for path in files:
        try:
            lines = sum(1 for _ in path.open("rb"))
        except OSError:
            continue
        for threshold in thresholds:
            if lines <= threshold:
                by_threshold[threshold].append(path)

    print(f"# Small-file relocation candidates in `{root}`\n")
    print(f"Thresholds inspected: {', '.join(f'{t} LoC' for t in thresholds)}\n")

    for threshold in thresholds:
        candidates = by_threshold.get(threshold, [])
        print(f"## Files at or below {threshold} lines ({len(candidates)} candidates)\n")
        if not candidates:
            print("_No candidates at this threshold._\n")
            continue

        for path in candidates:
            lines = sum(1 for _ in path.open("rb"))
            suggestion = suggest_destination(path)
            if suggestion is None:
                print(f"- `{path.name}` ({lines} lines) → **keep at root**")
                continue

            refs = ""
            if args.check_references:
                ref_count = count_references(root, path.name)
                refs = f" | references: {ref_count}"
                if ref_count == 0:
                    risk = "low risk"
                elif ref_count <= 3:
                    risk = "medium risk"
                else:
                    risk = "high risk"
                refs += f" ({risk})"

            print(f"- `{path.name}` ({lines} lines) → `{suggestion}`{refs}")
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
