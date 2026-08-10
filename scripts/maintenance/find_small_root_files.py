#!/usr/bin/env python3
"""Find small files in a root folder and suggest relocation candidates.

Scans the given directory (defaults to the project root) for files whose
non-empty line count is below configurable thresholds, reports references found
in the codebase, and suggests a target directory based on the file type and
name.

Usage:
    python scripts/maintenance/find_small_root_files.py [PATH] [--threshold N]
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

# Folders that should not be treated as part of the scanned directory.
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}

# Files that are expected to live at the project root and should not be flagged.
KEEP_AT_ROOT = {
    "pyproject.toml",
    "pytest.ini",
    "mypy.ini",
    "Makefile",
    "docker-compose.yml",
    "uv.lock",
    ".python-version",
    ".gitignore",
    ".gitignore_parent",
    ".gitmodules",
    ".ruffignore",
    ".bobignore",
    "package-lock.json",
    ".env.example",
    ".env.production.example",
    "README.md",
    "START_HERE.md",
    "ROOT_FILE_RELOCATION_REPORT.md",
}

# Suggestion rules: (glob pattern, target directory, explanation)
SUGGESTIONS = [
    ("*.sh", "scripts/deployment/", "Shell entry-point / deployment script"),
    ("*cleanup*.sh", "scripts/maintenance/", "Cleanup / maintenance shell script"),
    ("*fix*.sh", "scripts/maintenance/", "Fix / maintenance shell script"),
    ("*organize*.sh", "scripts/maintenance/", "Organization / maintenance shell script"),
    ("*analyze*.py", "scripts/analysis/", "Analysis / reporting Python script"),
    ("*plot*.py", "scripts/analysis/", "Plotting / analysis Python script"),
    ("*benchmark*.py", "scripts/analysis/", "Benchmark / analysis Python script"),
    ("*setup*.py", "scripts/setup/", "Setup / installation Python script"),
    ("*download*.py", "scripts/setup/", "Data download / setup Python script"),
    ("*validate*.py", "scripts/setup/", "Validation / setup Python script"),
    ("*cleanup*.py", "scripts/maintenance/", "Cleanup / maintenance Python script"),
    ("*fix*.py", "scripts/maintenance/", "Fix / maintenance Python script"),
    ("*organize*.py", "scripts/maintenance/", "Organization / maintenance Python script"),
    ("*diagnose*.py", "scripts/maintenance/", "Diagnostic / maintenance Python script"),
    ("*remove*.py", "scripts/maintenance/", "Removal / maintenance Python script"),
    ("*results*.txt", "data/", "Generated results / output artifact"),
    ("*.md", "docs/", "Documentation / markdown file"),
    ("*.yaml", "configs/", "YAML configuration file"),
    ("*.yml", "configs/", "YAML configuration file"),
    ("*.ini", "configs/", "INI configuration file"),
    ("requirements*.txt", "configs/", "Python requirements file"),
    ("*requirements*.txt", "configs/", "Python requirements file"),
    ("*.json", "configs/", "JSON configuration / lock file"),
]


def count_lines(path: Path) -> int:
    """Return the number of non-empty lines in a file."""
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            return sum(1 for line in f if line.strip())
    except (OSError, UnicodeDecodeError):
        return 0


def is_text_file(path: Path) -> bool:
    """Cheap binary-file check."""
    try:
        with path.open("rb") as f:
            chunk = f.read(1024)
        return b"\0" not in chunk
    except OSError:
        return False


def find_references(project_root: Path, filename: str) -> list[str]:
    """Search the codebase for references to a file name."""
    refs: list[str] = []
    try:
        result = subprocess.run(
            ["rg", "-n", "-g", "!.*", "-g", "!*.pyc", "-g", "!*.tar.gz", "-g", "!*.lock", "-g", "!*.pdf", "-g", "!*.png", filename],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        # Fall back to grep if ripgrep is unavailable.
        result = subprocess.run(
            [
                "grep", "-R", "-n", "--exclude-dir=.git", "--exclude-dir=.venv",
                "--exclude=*.pyc", "--exclude=*.tar.gz", "--exclude=*.lock",
                "--exclude=*.pdf", "--exclude=*.png", filename, ".",
            ],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )

    if result.stdout:
        for line in result.stdout.strip().split("\n"):
            if line.strip() and not line.startswith("Binary"):
                refs.append(line)
    return refs


def suggest_relocation(path: Path, project_root: Path) -> tuple[str, str]:
    """Return a suggested target directory and reason for a file."""
    name = path.name
    lower = name.lower()

    # More specific patterns first.
    for pattern, target, reason in SUGGESTIONS:
        if pattern.startswith("*") and lower.endswith(pattern.lstrip("*")):
            return target, reason
        if Path(name).match(pattern):
            return target, reason

    # Default by extension.
    ext = path.suffix.lower()
    if ext == ".py":
        return "scripts/maintenance/", "Generic Python script"
    if ext in {".sh", ".bash"}:
        return "scripts/maintenance/", "Generic shell script"
    if ext in {".md", ".rst"}:
        return "docs/", "Documentation file"
    if ext in {".yaml", ".yml", ".ini", ".json", ".toml"}:
        return "configs/", "Configuration file"
    if ext in {".txt", ".log"}:
        return "data/", "Text / log / output artifact"
    return "archive/", "Uncategorized small file"


def scan_folder(folder: Path, project_root: Path, threshold: int) -> dict[str, list[dict]]:
    """Scan a folder for small files and group them by size bucket."""
    buckets: dict[str, list[dict]] = {"<200": [], "200-300": [], ">300": []}

    for item in sorted(folder.iterdir()):
        if item.is_dir():
            continue
        if item.name in KEEP_AT_ROOT:
            continue
        if not is_text_file(item):
            continue

        loc = count_lines(item)
        target, reason = suggest_relocation(item, project_root)
        refs = find_references(project_root, item.name)

        entry = {
            "path": item.relative_to(project_root),
            "loc": loc,
            "target": target,
            "reason": reason,
            "refs": refs,
        }

        if loc < 200:
            buckets["<200"].append(entry)
        elif loc < 300:
            buckets["200-300"].append(entry)
        else:
            buckets[">300"].append(entry)

    return buckets


def print_report(buckets: dict[str, list[dict]], folder: Path, threshold: int) -> None:
    """Print the relocation-candidate report to stdout."""
    print(f"# Small file relocation candidates in `{folder}`")
    print(f"\nThresholds: <200 LoC and 200-300 LoC (configurable with --threshold).")
    print()

    small = buckets["<200"] + buckets["200-300"]
    large = buckets[">300"]

    print(f"Found {len(small)} files under {threshold} lines of code.")
    print()

    for bucket_name, entries in [("<200 LoC", buckets["<200"]), ("200-300 LoC", buckets["200-300"])]:
        if not entries:
            continue
        print(f"## {bucket_name}")
        print()
        for entry in sorted(entries, key=lambda e: e["loc"]):
            print(f"- `{entry['path']}` ({entry['loc']} LoC)")
            print(f"  - Suggested target: `{entry['target']}`")
            print(f"  - Reason: {entry['reason']}")
            if entry["refs"]:
                print(f"  - References found ({len(entry['refs'])}):")
                for ref in entry["refs"][:5]:
                    print(f"    - `{ref}`")
                if len(entry["refs"]) > 5:
                    print(f"    - ... and {len(entry['refs']) - 5} more")
            else:
                print("  - No references found in the codebase")
            print()

    if large:
        print("## Files above 300 LoC (for context)")
        print()
        for entry in sorted(large, key=lambda e: e["loc"]):
            print(f"- `{entry['path']}` ({entry['loc']} LoC) — suggested: `{entry['target']}`")
        print()

    print("## Notes")
    print()
    print("- Files listed as `KEEP_AT_ROOT` (e.g., `pyproject.toml`, `Makefile`) are intentionally omitted.")
    print("- Generated artifacts and one-off analysis scripts are usually safe to move.")
    print("- Entry-point scripts (`start.sh`, `Makefile` targets) may need symlink or README updates when moved.")
    print("- Always verify references before moving a file.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Find small files in a root folder and suggest relocation candidates."
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Root folder to scan (default: current directory / project root).",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=300,
        help="Upper line-count threshold to include in the report (default: 300).",
    )
    args = parser.parse_args()

    folder = Path(args.path).resolve()
    project_root = Path(__file__).resolve().parents[2]

    if not folder.is_dir():
        print(f"Error: {folder} is not a directory", file=sys.stderr)
        return 1

    buckets = scan_folder(folder, project_root, args.threshold)
    print_report(buckets, folder, args.threshold)
    return 0


if __name__ == "__main__":
    sys.exit(main())
