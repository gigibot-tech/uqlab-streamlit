#!/usr/bin/env python3
"""Find root-level directories whose files are all below a LoC threshold.

The script scans the repository root (or a single root folder you name), counts
non-empty lines for every countable text/config file, and reports whether the
folder is a relocation/consolidation candidate.

Examples:
    python scripts/maintenance/find_small_file_relocation_candidates.py
    python scripts/maintenance/find_small_file_relocation_candidates.py --threshold 200
    python scripts/maintenance/find_small_file_relocation_candidates.py --folder configs
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]

# Directories that are part of the repository machinery and should never be
# treated as relocation candidates.
RESERVED_ROOT_DIRS = {
    ".git",
    ".cursor",
    ".docs",
    ".bob",
    ".vscode",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    "archive",
}

# Canonical roots that should not be relocated even if every file is small.
CANONICAL_ROOTS = {"src"}

# Extensions we treat as countable source/config/text files.
COUNTABLE_EXTENSIONS = {
    ".py",
    ".sh",
    ".yml",
    ".yaml",
    ".toml",
    ".ini",
    ".cfg",
    ".json",
    ".md",
    ".txt",
    ".html",
    ".css",
    ".js",
    ".ts",
    ".sql",
}


def should_skip_dir(part: str) -> bool:
    return part.startswith(".") or part in RESERVED_ROOT_DIRS or part == "__pycache__"


def iter_root_directories(root: Path) -> Iterable[Path]:
    for entry in sorted(root.iterdir()):
        if entry.is_dir() and not entry.is_symlink() and not should_skip_dir(entry.name):
            yield entry


def iter_countable_files(directory: Path) -> Iterable[Path]:
    for path in directory.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in COUNTABLE_EXTENSIONS:
            continue
        if any(should_skip_dir(part) for part in path.relative_to(directory).parts):
            continue
        yield path


def count_non_empty_lines(path: Path) -> int:
    try:
        return sum(
            1
            for line in path.read_text(encoding="utf-8", errors="ignore").splitlines()
            if line.strip()
        )
    except OSError:
        return 0


def suggest_relocation(folder: Path, files: list[tuple[Path, int]]) -> list[str]:
    hints: list[str] = []
    suffixes = {f.suffix.lower() for f, _ in files}

    if folder.name in CANONICAL_ROOTS:
        return ["This is a canonical project root; do not relocate it."]

    if folder.name == "configs":
        hints.append(
            "Keep as a top-level config store (conventional) OR move into a "
            "package such as src/configs if the project is packaged as a wheel "
            "with package_data. A root symlink can preserve backward compatibility."
        )
        loose_examples = [f for f, _ in files if "example" in f.name and f.parent.name == "configs"]
        if loose_examples:
            hints.append(
                "Move loose example_*.yaml files into a sub-folder such as "
                "configs/examples/ to reduce clutter."
            )
        if any(str(f.relative_to(REPO_ROOT)).startswith("configs/test") for f, _ in files):
            hints.append(
                "Test-only configs (configs/test/) could be moved closer to their "
                "consumers, e.g. tests/configs/ or scripts/setup/configs/."
            )
    elif ".py" in suffixes and ".sh" not in suffixes:
        hints.append(
            f"Move Python files into a package under src/ or into scripts/{folder.name}/."
        )
    elif ".sh" in suffixes:
        hints.append(
            f"Move shell scripts into scripts/{folder.name}/ or scripts/deployment/."
        )
    elif ".md" in suffixes and len(suffixes) == 1:
        hints.append("Move markdown files into docs/ or an archive sub-folder.")
    else:
        hints.append(
            f"Review consumers of {folder.name}/; if the folder has no unique code, "
            "consider moving contents to the package/module that actually uses them."
        )

    return hints


def analyze_folder(folder: Path, threshold: int) -> dict[str, object] | None:
    files = [(f, count_non_empty_lines(f)) for f in iter_countable_files(folder)]
    if not files:
        return None

    nonzero_lines = [n for _, n in files if n > 0]
    all_under_threshold = all(n <= threshold for _, n in files)
    all_under_threshold_nonzero = (
        all(n <= threshold for n in nonzero_lines) if nonzero_lines else True
    )
    return {
        "folder": folder,
        "files": files,
        "total": len(files),
        "max_loc": max(n for _, n in files),
        "all_under_threshold": all_under_threshold,
        "all_under_threshold_nonzero": all_under_threshold_nonzero,
    }


def analyze_all(threshold: int) -> dict[str, dict[str, object]]:
    results: dict[str, dict[str, object]] = {}
    for folder in iter_root_directories(REPO_ROOT):
        data = analyze_folder(folder, threshold)
        if data is not None:
            results[folder.name] = data
    return results


def print_folder_report(data: dict[str, object], threshold: int) -> None:
    folder = data["folder"]
    files = data["files"]
    print(f"## {folder.name}/")
    print(f"- Total files: {data['total']}")
    print(f"- Max non-empty LoC: {data['max_loc']}")
    print(f"- All files <= {threshold} LoC: {data['all_under_threshold']}")
    print()
    print("| LoC | File |")
    print("|-----|------|")
    for path, loc in sorted(files, key=lambda kv: (kv[1], str(kv[0]))):
        print(f"| {loc} | {path.relative_to(REPO_ROOT)} |")
    print()
    print(f"**Relocation hints for `{folder.name}/`:**")
    for hint in suggest_relocation(folder, files):
        print(f"- {hint}")
    print()


def print_all_report(results: dict[str, dict[str, object]], threshold: int) -> None:
    print(f"# Small-File Relocation Candidates (<= {threshold} non-empty LoC)\n")
    print(f"Repository root: {REPO_ROOT}\n")

    candidates = {
        name: data
        for name, data in results.items()
        if data["all_under_threshold_nonzero"]
        and name not in CANONICAL_ROOTS
        and sum(1 for _, n in data["files"] if n > 0) >= 2
    }

    if not candidates:
        print(
            "No root-level directory (with more than one countable file) has all files "
            f"under the {threshold} LoC threshold."
        )
        return

    print("## Root folders where ALL files are below the threshold\n")
    for name, data in sorted(candidates.items(), key=lambda kv: kv[1]["max_loc"]):
        print_folder_report(data, threshold)
        print()

    print("## Other root folders (for comparison)\n")
    for name, data in sorted(results.items(), key=lambda kv: kv[1]["max_loc"]):
        if name in candidates:
            continue
        marker = "all under threshold" if data["all_under_threshold"] else f"max {data['max_loc']} LoC"
        print(f"- {name}/ — {data['total']} files, {marker}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Find small-file relocation candidates in the repo root."
    )
    parser.add_argument(
        "--folder",
        type=str,
        default=None,
        help="Analyze a single root directory by name (e.g. configs).",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=300,
        help="LoC threshold (default: 300).",
    )
    args = parser.parse_args()

    if args.folder:
        folder = REPO_ROOT / args.folder
        if not folder.is_dir():
            raise SystemExit(f"Not a root directory: {folder}")
        data = analyze_folder(folder, args.threshold)
        if data is None:
            raise SystemExit(f"No countable files found in {folder}")
        print_folder_report(data, args.threshold)
    else:
        results = analyze_all(args.threshold)
        print_all_report(results, args.threshold)


if __name__ == "__main__":
    main()
