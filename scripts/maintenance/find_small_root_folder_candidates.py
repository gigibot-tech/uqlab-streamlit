#!/usr/bin/env python3
"""Find root folders whose files are all small enough to relocate.

Scans each top-level directory under the repository root, counts lines of
text/code in every file, and flags folders where every file is at or below the
configured thresholds (default 200 and 300 lines). For each qualifying folder it
suggests a more appropriate destination and, optionally, estimates reference
risk by counting textual mentions of the folder name in the repository.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

DEFAULT_THRESHOLDS = (200, 300)

# Directories/files at the repo root that are conventional and should stay put.
ROOT_KEEPERS = {
    ".git",
    ".cursor",
    ".vscode",
    ".docs",
    ".bob",
    "backend",
    "src",
    "tests",
    "docs",
    "notebooks",
    "scripts",
    "data",
    "frontend",
}

# Folders that are intentionally runtime data or local state and not candidates.
RUNTIME_FOLDERS = {"data", ".venv", "venv", "__pycache__", ".pytest_cache", "dist", "build"}


def is_text_file(path: Path) -> bool:
    """Return True for files we can reasonably count lines on."""
    if path.is_symlink():
        return False
    suffix = path.suffix.lower()
    if suffix in {
        ".py",
        ".md",
        ".txt",
        ".yml",
        ".yaml",
        ".json",
        ".toml",
        ".ini",
        ".cfg",
        ".sh",
        ".html",
        ".css",
        ".js",
        ".ts",
        ".tsx",
        ".jsx",
    }:
        return True
    # Accept files with no suffix if they are small and look like text.
    if suffix == "" and path.stat().st_size < 1_000_000:
        return True
    return False


def count_lines(path: Path) -> int:
    """Count newline-separated lines in a file, ignoring decode errors."""
    try:
        with path.open("rb") as f:
            return sum(1 for _ in f)
    except OSError:
        return 0


def gather_files(folder: Path) -> list[Path]:
    """Return all text-ish files recursively under folder, excluding junk."""
    files: list[Path] = []
    for path in folder.rglob("*"):
        if not path.is_file():
            continue
        if ".git" in path.parts or "__pycache__" in path.parts or "node_modules" in path.parts:
            continue
        if is_text_file(path):
            files.append(path)
    return files


def suggest_folder_relocation(folder: Path, files: list[Path]) -> str | None:
    """Suggest a destination for a qualifying root folder, or None to keep."""
    name = folder.name

    if name in RUNTIME_FOLDERS:
        return None

    if name == "configs":
        return "src/uqlab_core/configs/ (co-locate with the package that consumes them)"

    if name == "uqlab-flask":
        return "frontend/uqlab-flask/ or src/uqlab_flask/ (isolate the Flask UI)"

    if name == ".docs":
        return "docs/deployment/ and docs/development/ (hidden docs belong under docs/)"

    if name == "notebooks":
        return "notebooks/ is acceptable; consider archiving validation/ helpers if stale"

    if all(p.suffix.lower() == ".md" for p in files):
        return "docs/ or docs/archive/"

    if all(p.suffix.lower() in (".sh", ".py") for p in files):
        return "scripts/ subfolder"

    return "review manually"


def count_references(root: Path, name: str) -> int:
    """Rough count of textual references to a folder name or its root path."""
    needles = [name, f"{name}/"]
    count = 0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if ".git" in path.parts:
            continue
        if path.is_symlink():
            continue
        try:
            size = path.stat().st_size
            if size > 2_000_000:
                continue
        except OSError:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except (OSError, UnicodeDecodeError):
            continue
        for needle in needles:
            count += text.count(needle)
    return count


def analyze_folder(folder: Path, root: Path, thresholds: list[int], check_refs: bool) -> dict:
    """Return analysis dict for a single top-level folder."""
    files = gather_files(folder)
    sizes = {p: count_lines(p) for p in files}
    max_lines = max(sizes.values()) if sizes else 0
    total_lines = sum(sizes.values())

    result = {
        "folder": folder,
        "files": files,
        "sizes": sizes,
        "max_lines": max_lines,
        "total_lines": total_lines,
        "qualifying_thresholds": [t for t in thresholds if max_lines <= t and sizes],
        "suggestion": None,
        "refs": 0,
    }

    if result["qualifying_thresholds"]:
        result["suggestion"] = suggest_folder_relocation(folder, files)
        if result["suggestion"] and check_refs:
            result["refs"] = count_references(root, folder.name)

    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Repository root to scan (default: current working directory)",
    )
    parser.add_argument(
        "--folder",
        type=Path,
        default=None,
        help="Inspect only this single folder under --root instead of all top-level folders",
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
        help="Scan the repository for textual references to each candidate folder",
    )
    args = parser.parse_args(argv)

    root = args.root.resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 1

    thresholds = sorted(set(args.thresholds))

    if args.folder:
        target = args.folder
        if not target.is_absolute():
            target = root / target
        folders = [target.resolve()] if target.is_dir() else []
    else:
        folders = sorted(p for p in root.iterdir() if p.is_dir() and p.name not in ROOT_KEEPERS)

    analyses = [analyze_folder(folder, root, thresholds, args.check_references) for folder in folders]

    print(f"# Small root-folder relocation candidates in `{root}`\n")
    print(f"Thresholds inspected: {', '.join(f'{t} LoC' for t in thresholds)}\n")
    print(f"Top-level folders inspected: {len(folders)}\n")

    found_any = False
    for threshold in thresholds:
        candidates = [a for a in analyses if threshold in a["qualifying_thresholds"] and a["suggestion"]]
        print(f"## Folders where every file is at or below {threshold} lines\n")
        if not candidates:
            print("_No qualifying folders at this threshold._\n")
            continue

        found_any = True
        for a in candidates:
            folder = a["folder"]
            print(f"### `{folder.name}/`")
            print(f"- Files: {len(a['files'])}")
            print(f"- Largest file: {a['max_lines']} lines")
            print(f"- Total lines: {a['total_lines']}")
            print(f"- Suggested destination: {a['suggestion']}")
            if args.check_references:
                risk = "low risk" if a["refs"] == 0 else "medium risk" if a["refs"] <= 10 else "high risk"
                print(f"- Textual references to folder name: {a['refs']} ({risk})")

            # Show smallest files first for a quick sanity check.
            print("- Smallest files:")
            for path, size in sorted(a["sizes"].items(), key=lambda x: x[1])[:5]:
                rel = path.relative_to(folder)
                print(f"  - `{rel}` ({size} lines)")
            print()

    if not found_any:
        print("No qualifying relocation candidates found at the inspected thresholds.\n")

    # Also list non-qualifying folders with their largest file for context.
    print("## Non-qualifying top-level folders (for reference)\n")
    non_qualifying = [a for a in analyses if not a["qualifying_thresholds"]]
    for a in non_qualifying:
        folder = a["folder"]
        if a["sizes"]:
            print(f"- `{folder.name}/` — largest file {a['max_lines']} lines, total {a['total_lines']} lines")
        else:
            print(f"- `{folder.name}/` — no text files scanned")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
