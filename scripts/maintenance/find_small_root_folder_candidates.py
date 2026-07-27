#!/usr/bin/env python3
"""Find root-level folders whose files are all small and suggest relocation targets.

A "small file" is defined as <= 200 LoC (strict) or <= 300 LoC (lenient).
The script scans every directory located directly under the workspace root,
skips obviously non-relocatable directories (e.g. version control, virtual
environments, well-scoped packages), and produces a Markdown report with
proposed relocation targets.

Usage:
    python scripts/maintenance/find_small_root_folder_candidates.py
    python scripts/maintenance/find_small_root_folder_candidates.py /path/to/repo
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import NamedTuple

STRICT_LIMIT = 200
LENIENT_LIMIT = 300

# Root directories that should never be relocated or scanned as candidates.
SKIP_ROOT_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".cursor",
    ".docs",
    ".vscode",
    ".idea",
    ".bob",
    "archive",
    "legacy",
}

# Root directories that are already well-scoped. We still report their max
# file size for completeness, but do not propose relocating them.
WELL_SCOPED_ROOTS = {
    "scripts",
    "backend",
    "docs",
    "notebooks",
    "tests",
    "src",
    "frontend",
}

# File extensions that are not meaningful line-count targets.
SKIP_EXTENSIONS = {
    ".ipynb",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".pdf",
    ".tar.gz",
    ".zip",
    ".pyc",
    ".pyo",
    ".DS_Store",
}

# Relocation heuristics based on directory name.
RELOCATION_HEURISTICS: dict[str, str] = {
    "configs": "src/uqlab_core/configs",
    "config": "src/uqlab_core/configs",
    "data": "src/uqlab_core/data",
    "uqlab-flask": "src/uqlab_flask",
    "flask": "src/uqlab_flask",
    "frontend": "src/frontend",
}


class FolderSummary(NamedTuple):
    name: str
    path: Path
    file_count: int
    total_loc: int
    max_loc: int
    all_files: list[tuple[Path, int]]

    def is_empty(self) -> bool:
        return self.file_count == 0

    def is_strict_small(self) -> bool:
        return self.file_count > 0 and self.max_loc <= STRICT_LIMIT

    def is_lenient_small(self) -> bool:
        return self.file_count > 0 and self.max_loc <= LENIENT_LIMIT


def count_lines(path: Path) -> int:
    """Return the number of non-empty lines in a text file."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except (OSError, UnicodeDecodeError):
        return 0
    return sum(1 for line in text.splitlines() if line.strip())


def should_skip_file(path: Path) -> bool | str:
    """Return a skip reason, or False if the file should be considered."""
    if path.is_symlink():
        return "symlink"
    if path.suffix in SKIP_EXTENSIONS:
        return f"{path.suffix} asset"
    if path.name in {".DS_Store", ".gitkeep"}:
        return "conventional metadata"
    return False


def summarize_root_folder(root: Path, folder_path: Path) -> FolderSummary:
    """Collect line counts for every relevant file inside a root folder."""
    files: list[tuple[Path, int]] = []
    for path in folder_path.rglob("*"):
        if not path.is_file():
            continue
        skip_reason = should_skip_file(path)
        if skip_reason:
            continue
        rel = path.relative_to(root)
        files.append((rel, count_lines(path)))
    files.sort(key=lambda item: item[1])
    total = sum(loc for _, loc in files)
    max_loc = max((loc for _, loc in files), default=0)
    return FolderSummary(
        name=folder_path.name,
        path=folder_path,
        file_count=len(files),
        total_loc=total,
        max_loc=max_loc,
        all_files=files,
    )


def suggest_relocation(summary: FolderSummary) -> str | None:
    """Suggest a relocation target for a small root folder, if appropriate."""
    if summary.name in WELL_SCOPED_ROOTS:
        return None
    if summary.is_empty():
        return None

    name_lower = summary.name.lower()
    for substring, target in RELOCATION_HEURISTICS.items():
        if substring in name_lower:
            return target

    return None


def gather_summaries(root: Path) -> list[FolderSummary]:
    """Return summaries for every non-skipped directory at the workspace root."""
    summaries: list[FolderSummary] = []
    for item in sorted(root.iterdir()):
        if not item.is_dir():
            continue
        if item.name in SKIP_ROOT_DIRS:
            continue
        summaries.append(summarize_root_folder(root, item))
    return summaries


def build_report(root: Path, summaries: list[FolderSummary]) -> str:
    """Render the analysis as Markdown."""
    strict_candidates = [s for s in summaries if s.is_strict_small()]
    lenient_candidates = [s for s in summaries if s.is_lenient_small()]
    empty_dirs = [s for s in summaries if s.is_empty()]

    lines: list[str] = []
    lines.append("# Small Root Folder Relocation Candidates")
    lines.append("")
    lines.append(
        "Generated by `scripts/maintenance/find_small_root_folder_candidates.py`."
    )
    lines.append("")
    lines.append("## Definition")
    lines.append("")
    lines.append(f"- **Strict small**: every file <= {STRICT_LIMIT} LoC")
    lines.append(f"- **Lenient small**: every file <= {LENIENT_LIMIT} LoC")
    lines.append(
        "- Empty directories, symlinks, binary assets, and hidden/tooling folders are ignored."
    )
    lines.append("")
    lines.append("## Root folder overview")
    lines.append("")
    lines.append("| Folder | Files | Max LoC | Total LoC | Strict | Lenient | Notes |")
    lines.append("|--------|-------|---------|-----------|--------|---------|-------|")
    for s in summaries:
        strict = "✅" if s.is_strict_small() else "—"
        lenient = "✅" if s.is_lenient_small() else "—"
        notes = ""
        if s.name in WELL_SCOPED_ROOTS:
            notes = "well-scoped (keep)"
        elif s.is_empty():
            notes = "empty"
        elif s.is_strict_small():
            notes = "relocation candidate"
        elif s.is_lenient_small():
            notes = "lenient candidate"
        lines.append(
            f"| `{s.name}` | {s.file_count} | {s.max_loc} | {s.total_loc} | {strict} | {lenient} | {notes} |"
        )
    lines.append("")

    if strict_candidates:
        lines.append("## Strict relocation candidates (all files <= 200 LoC)")
        lines.append("")
        for s in strict_candidates:
            target = suggest_relocation(s)
            target_text = f"`{target}`" if target else "— (no obvious target)"
            lines.append(f"### `{s.name}`")
            lines.append("")
            lines.append(f"- **Files**: {s.file_count}")
            lines.append(f"- **Largest file**: {s.max_loc} LoC")
            lines.append(f"- **Total**: {s.total_loc} LoC")
            lines.append(f"- **Suggested target**: {target_text}")
            lines.append("")
            lines.append("| File | LoC |")
            lines.append("|------|-----|")
            for rel, loc in s.all_files:
                lines.append(f"| `{rel}` | {loc} |")
            lines.append("")

    if lenient_candidates and not strict_candidates:
        lines.append("## Lenient relocation candidates (all files <= 300 LoC)")
        lines.append("")
        for s in lenient_candidates:
            target = suggest_relocation(s)
            target_text = f"`{target}`" if target else "— (no obvious target)"
            lines.append(f"- `{s.name}`: {s.file_count} files, max {s.max_loc} LoC → {target_text}")
        lines.append("")

    if empty_dirs:
        lines.append("## Empty root folders")
        lines.append("")
        lines.append(
            "The following directories contain no tracked files and may be candidates for removal or archiving:"
        )
        for s in empty_dirs:
            lines.append(f"- `{s.name}`")
        lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Root folders scanned**: {len(summaries)}")
    lines.append(f"- **Strict candidates (<= {STRICT_LIMIT} LoC)**: {len(strict_candidates)}")
    lines.append(f"- **Lenient candidates (<= {LENIENT_LIMIT} LoC)**: {len(lenient_candidates)}")
    lines.append(f"- **Empty folders**: {len(empty_dirs)}")
    lines.append("")

    if not strict_candidates and not lenient_candidates:
        lines.append(
            "No root folders qualify as small-file relocation candidates. "
            "All non-empty root folders contain at least one file larger than the thresholds."
        )
        lines.append("")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Find root-level folders with small files and suggest relocation targets."
    )
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="Workspace root to scan (default: current directory)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="docs/development/SMALL_ROOT_FOLDER_RELOCATION_CANDIDATES.md",
        help="Output Markdown report path (default: docs/development/SMALL_ROOT_FOLDER_RELOCATION_CANDIDATES.md)",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"Error: not a directory: {root}", file=sys.stderr)
        return 1

    summaries = gather_summaries(root)
    report = build_report(root, summaries)

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = root / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print(f"Report written to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
