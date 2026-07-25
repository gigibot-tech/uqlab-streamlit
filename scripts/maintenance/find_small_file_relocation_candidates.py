#!/usr/bin/env python3
"""Find root-level directories whose files are all below a LoC threshold.

The script scans the repository root, counts non-empty lines for every
text/config file, and reports directories where every file is small enough
that the whole folder could be a relocation/consolidation candidate.

Example:
    python scripts/maintenance/find_small_file_relocation_candidates.py
    python scripts/maintenance/find_small_file_relocation_candidates.py --threshold 200
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]

# Directories that are part of the repository layout and should never be
# considered "relocatable root folders".
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

# Canonical roots that should not be treated as relocation candidates,
# even if they only contain small files.
CANONICAL_ROOTS = {"src"}

# File extensions we treat as countable source/config/text files.
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
        if entry.is_dir() and not should_skip_dir(entry.name):
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
        return sum(1 for line in path.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip())
    except OSError:
        return 0


def suggest_relocation(folder: Path, files: list[tuple[Path, int]]) -> list[str]:
    """Return free-form relocation hints based on the folder content."""
    hints: list[str] = []
    suffixes = {f.suffix.lower() for f, _ in files}
    rel = folder.relative_to(REPO_ROOT)

    if folder.name in CANONICAL_ROOTS:
        return ["This is a canonical project root; do not relocate it."]

    if folder.name == "configs":
        hints.append(
            "Keep as a top-level config store (conventional) OR move into a "
            "package such as src/uqlab_orchestrator/configs if the package is "
            "packaged as a wheel with package_data."
        )
        loose_examples = [
            f for f, _ in files
            if "example" in f.name and f.parent.name == "configs"
        ]
        if loose_examples:
            hints.append(
                "Move loose example_*.yaml files into a sub-folder such as "
                "configs/examples/ or configs/experiment/ to reduce clutter."
            )
        elif any("example" in f.name for f, _ in files):
            hints.append(
                "Example configs are already grouped in a sub-folder; good "
                "candidate for packaging as package_data if moved into a package."
            )
        if any(str(f.relative_to(REPO_ROOT)).startswith("configs/test") for f, _ in files):
            hints.append(
                "Test-only configs (configs/test/) could be moved closer to "
                "their consumers, e.g. tests/configs/ or scripts/setup/configs/."
            )
    elif ".py" in suffixes and ".sh" not in suffixes:
        hints.append(f"Move Python files into a package under src/ or into scripts/{folder.name}/.")
    elif ".sh" in suffixes:
        hints.append(f"Move shell scripts into scripts/{folder.name}/ or scripts/deployment/.")
    elif ".md" in suffixes and len(suffixes) == 1:
        hints.append("Move markdown files into docs/ or an archive sub-folder.")
    else:
        hints.append(
            f"Review consumers of {rel}/; if the folder has no unique code, "
            "consider moving contents to the package/module that actually uses them."
        )

    return hints


def analyze(threshold: int) -> dict[str, dict]:
    results: dict[str, dict] = {}
    for folder in iter_root_directories(REPO_ROOT):
        files = [(f, count_non_empty_lines(f)) for f in iter_countable_files(folder)]
        if not files:
            continue

        nonzero_lines = [n for _, n in files if n > 0]
        all_under_threshold = all(n <= threshold for _, n in files)
        all_under_threshold_nonzero = all(n <= threshold for n in nonzero_lines) if nonzero_lines else True
        results[folder.name] = {
            "folder": folder,
            "files": files,
            "total": len(files),
            "max_loc": max(n for _, n in files),
            "all_under_threshold": all_under_threshold,
            "all_under_threshold_nonzero": all_under_threshold_nonzero,
        }
    return results


def print_report(results: dict[str, dict], threshold: int) -> None:
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
        print("No root-level directory (with more than one countable file) has all files under the threshold.")
        return

    print("## Root folders where ALL files are below the threshold\n")
    for name, data in sorted(candidates.items(), key=lambda kv: kv[1]["max_loc"]):
        folder = data["folder"]
        print(f"- **{name}/** — {data['total']} files, max {data['max_loc']} LoC")
        for path, loc in sorted(data["files"], key=lambda kv: kv[1]):
            print(f"  - {loc:4d}  {path.relative_to(REPO_ROOT)}")

        print(f"\n  Relocation hints for `{name}/`:")
        for hint in suggest_relocation(folder, data["files"]):
            print(f"  - {hint}")
        print()

    print("\n## Other root folders (for comparison)\n")
    for name, data in sorted(results.items(), key=lambda kv: kv[1]["max_loc"]):
        if name in candidates:
            continue
        marker = "all under threshold" if data["all_under_threshold"] else f"max {data['max_loc']} LoC"
        print(f"- {name}/ — {data['total']} files, {marker}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Find small-file relocation candidates in the repo root.")
    parser.add_argument("--threshold", type=int, default=300, help="LoC threshold (default: 300)")
    args = parser.parse_args()

    results = analyze(args.threshold)
    print_report(results, args.threshold)


if __name__ == "__main__":
    main()
