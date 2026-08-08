#!/usr/bin/env python3
"""Find small code files in root folders that may be relocation candidates."""

import os
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[3]
MAX_LINES = 300

CODE_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".sh",
    ".yml",
    ".yaml",
    ".toml",
    ".ini",
    ".cfg",
}
EXCLUDE_DIRS = {".git", ".cursor", ".vscode", ".bob", ".docs", "data", "docs", "notebooks"}
EXCLUDE_FILES = {"uv.lock", "package-lock.json", "dependencies.json"}


def count_lines(path: Path) -> int:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def is_code_file(path: Path) -> bool:
    if path.name in EXCLUDE_FILES:
        return False
    if path.suffix.lower() in CODE_EXTENSIONS:
        return True
    return False


def main():
    root_dirs = [
        d
        for d in ROOT.iterdir()
        if d.is_dir() and d.name not in EXCLUDE_DIRS and not d.name.startswith(".")
    ]

    small_files = defaultdict(list)
    all_files = defaultdict(list)

    for root_dir in sorted(root_dirs):
        for path in root_dir.rglob("*"):
            if not path.is_file() or not is_code_file(path):
                continue
            lines = count_lines(path)
            rel = path.relative_to(ROOT)
            all_files[root_dir.name].append((rel, lines))
            if lines <= MAX_LINES:
                small_files[root_dir.name].append((rel, lines))

    print("=" * 70)
    print("Small file relocation candidates (<=300 LoC)")
    print("=" * 70)
    for folder in sorted(small_files.keys()):
        print(f"\n📁 {folder}/")
        for rel, lines in sorted(small_files[folder], key=lambda x: x[1]):
            print(f"   {rel}  ({lines} LoC)")
        total = len(all_files[folder])
        small = len(small_files[folder])
        print(f"   -> {small}/{total} files are <= {MAX_LINES} LoC")

    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    for folder in sorted(all_files.keys()):
        total = len(all_files[folder])
        small = len(small_files.get(folder, []))
        pct = (small / total * 100) if total else 0
        print(f"{folder:20} {small:3}/{total:3} files <= {MAX_LINES} LoC ({pct:5.1f}%)")


if __name__ == "__main__":
    main()
