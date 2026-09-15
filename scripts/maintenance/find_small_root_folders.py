#!/usr/bin/env python3
"""Find root-level folders whose text files are all <= 200/300 lines of code.

The script scans every top-level directory under the repository root, counts
lines in text files, and flags relocation candidates.  It also suggests a
destination, checks `docs/features/` for overlapping requirement docs, and
estimates textual-reference risk so moves can be planned safely.

Usage:
    python scripts/maintenance/find_small_root_folders.py
    python scripts/maintenance/find_small_root_folders.py /path/to/repo --output report.md
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from collections import defaultdict

# Text-file extensions we count.
TEXT_SUFFIXES = {
    ".py", ".sh",
    ".md", ".txt", ".rst",
    ".yaml", ".yml",
    ".json", ".toml", ".ini", ".cfg",
    ".html", ".css", ".js", ".ts", ".tsx",
}

# Directories we never treat as relocation candidates.
SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
}

# Known destination recommendations keyed by folder name.
DESTINATION_HINTS = {
    "configs": "src/uqlab_core/configs/ (add package-data in pyproject.toml)",
    ".docs": "docs/ tree (e.g. docs/setup/, docs/deployment/, docs/development/, docs/archive/)",
    ".vscode": "keep at repository root (editor settings)",
    ".cursor": "keep at repository root (Cursor IDE settings)",
    "data": "keep at repository root (runtime data placeholder)",
    "scripts": "keep at repository root (already organized into sub-folders)",
    "tests": "keep at repository root (top-level test suite)",
    "backend": "keep at repository root (service entry point)",
    "src": "keep at repository root (source tree)",
    "notebooks": "keep at repository root (notebooks entry point)",
    "docs": "keep at repository root (documentation root)",
    "uqlab-flask": "keep or archive (mixed LoC; not a small-folder candidate)",
}


def repository_root(start: Path | None = None) -> Path:
    """Return the repository root.

    If ``start`` is supplied, use it; otherwise derive from this script's
    location (../../..) or fall back to the current working directory.
    """
    if start is not None:
        return start.resolve()
    # scripts/maintenance/find_small_root_folders.py -> repo root is 3 parents up
    script_dir = Path(__file__).resolve()
    candidate = script_dir.parents[2]
    if (candidate / ".git").is_dir():
        return candidate
    return Path.cwd().resolve()


def is_text_file(path: Path) -> bool:
    """Return True for files we want to count as text/LoC."""
    suffix = path.suffix.lower()
    if suffix in TEXT_SUFFIXES:
        return True
    if not suffix:
        try:
            with path.open("rb") as fh:
                first = fh.readline(128)
            if first.startswith(b"#!"):
                shebang = first.decode("utf-8", errors="ignore").lower()
                return any(lang in shebang for lang in ("python", "bash", "sh"))
        except (OSError, UnicodeDecodeError):
            pass
    return False


def count_lines(path: Path) -> int:
    """Count lines in a text file, ignoring decode errors."""
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as fh:
            return sum(1 for _ in fh)
    except (OSError, UnicodeDecodeError):
        return 0


def gather_folder_stats(folder: Path) -> tuple[int, int, int, list[tuple[Path, int]]]:
    """Return (file_count, total_lines, max_lines, [(path, lines), ...])."""
    files: list[tuple[Path, int]] = []
    for root, dirs, names in os.walk(folder, followlinks=False):
        # Prune known noisy directories.
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in names:
            file_path = Path(root) / name
            if file_path.is_symlink() and not file_path.exists():
                # Broken symlink: don't count, but note it separately elsewhere.
                continue
            if not file_path.is_file():
                continue
            if is_text_file(file_path):
                lines = count_lines(file_path)
                files.append((file_path, lines))
    total = sum(lines for _, lines in files)
    max_lines = max((lines for _, lines in files), default=0)
    return len(files), total, max_lines, files


def discover_top_level_folders(root: Path) -> list[Path]:
    """Return immediate child directories of the repo root that should be inspected."""
    candidates: list[Path] = []
    for entry in sorted(root.iterdir()):
        if entry.is_dir() and entry.name not in SKIP_DIRS:
            candidates.append(entry)
    return candidates


def suggest_destination(folder: Path, max_lines: int) -> str:
    """Suggest where a small folder could be moved, or whether it should stay."""
    name = folder.name
    if name in DESTINATION_HINTS:
        return DESTINATION_HINTS[name]
    if name.startswith("."):
        return "docs/ or archive/ (hidden root folder)"
    if max_lines <= 200:
        return "consider consolidating under scripts/, docs/, or src/"
    return "consider consolidating under docs/ or archive/"


def find_feature_overlaps(folder: Path, root: Path) -> list[str]:
    """Look in docs/features/ for docs whose names overlap with the folder."""
    features_dir = root / "docs" / "features"
    if not features_dir.is_dir():
        return []
    feature_files = sorted(features_dir.glob("*.md"))
    name = folder.name.lstrip(".").lower()
    matches: list[str] = []
    for f in feature_files:
        stem = f.stem.lower().replace("-", "_")
        if name in stem or stem in name:
            matches.append(f"docs/features/{f.name}")
    return matches


def count_references(folder: Path, root: Path) -> int:
    """Count textual references to ``folder/`` outside .git and the folder itself."""
    needle = f"{folder.name}/"
    count = 0
    for walk_root, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = [d for d in dirs if d != ".git"]
        if Path(walk_root).resolve() == folder.resolve():
            continue
        for name in names:
            file_path = Path(walk_root) / name
            if not file_path.is_file() or file_path.is_symlink() and not file_path.exists():
                continue
            if not is_text_file(file_path):
                continue
            try:
                with file_path.open("r", encoding="utf-8", errors="ignore") as fh:
                    for line in fh:
                        if needle in line:
                            count += 1
            except (OSError, UnicodeDecodeError):
                pass
    return count


def build_report(root: Path, folders: list[Path]) -> str:
    """Build a Markdown report of root-folder sizes and relocation candidates."""
    lines: list[str] = []
    lines.append(f"# Root-folder relocation candidate report\n\n")
    lines.append(f"Repository root: `{root}`\n\n")

    # Summary table
    lines.append("## All root folders\n\n")
    lines.append("| Folder | Files | Total LoC | Max LoC | Candidate |\n")
    lines.append("|--------|------:|----------:|--------:|:---------:|\n")

    candidates_200: list[tuple[Path, int, int, int]] = []
    candidates_300: list[tuple[Path, int, int, int]] = []
    stats: list[tuple[Path, int, int, int, bool, bool]] = []

    for folder in folders:
        count, total, max_lines, _ = gather_folder_stats(folder)
        under_200 = max_lines > 0 and max_lines <= 200
        under_300 = max_lines > 0 and max_lines <= 300
        stats.append((folder, count, total, max_lines, under_200, under_300))
        if under_200:
            candidates_200.append((folder, count, total, max_lines))
        elif under_300:
            candidates_300.append((folder, count, total, max_lines))
        check = "✅" if under_200 or under_300 else "—"
        lines.append(f"| `{folder.name}` | {count} | {total} | {max_lines} | {check} |\n")

    # Candidate details
    lines.append("\n## Candidates: all files ≤200 LoC\n\n")
    if candidates_200:
        _append_candidate_details(lines, root, candidates_200)
    else:
        lines.append("No root folder qualifies.\n")

    lines.append("\n## Candidates: all files ≤300 LoC (but >200 LoC)\n\n")
    if candidates_300:
        _append_candidate_details(lines, root, candidates_300)
    else:
        lines.append("No root folder qualifies.\n")

    lines.append("\n## Notes\n\n")
    lines.append(
        "- Thresholds: `200 LoC` (strict) and `300 LoC` (lenient).\n"
        "- Text files are identified by extension or by a `#!` shebang.\n"
        "- Reference counts are a rough risk indicator; always verify links, "
        "imports, and build/package-data before moving files.\n"
        "- Check `docs/features/` before moving a folder; existing feature docs "
        "may already describe the same requirements.\n"
    )
    return "".join(lines)


def _append_candidate_details(
    lines: list[str],
    root: Path,
    candidates: list[tuple[Path, int, int, int]],
) -> None:
    for folder, count, total, max_lines in candidates:
        lines.append(f"### `{folder.name}`\n\n")
        lines.append(f"- Files: {count}\n")
        lines.append(f"- Total LoC: {total}\n")
        lines.append(f"- Max LoC per file: {max_lines}\n")
        lines.append(f"- Suggested destination: {suggest_destination(folder, max_lines)}\n")
        feature_hits = find_feature_overlaps(folder, root)
        if feature_hits:
            lines.append(
                "- Existing feature docs that may overlap: "
                + ", ".join(f"`{h}`" for h in feature_hits)
                + "\n"
            )
        else:
            lines.append("- No obvious overlap in `docs/features/`.\n")
        refs = count_references(folder, root)
        lines.append(f"- Textual references to `{folder.name}/`: {refs}\n\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Find root folders whose text files are all <= 200/300 LoC."
    )
    parser.add_argument(
        "repo",
        nargs="?",
        default=None,
        help="Path to the repository root (default: inferred from script location).",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Write the Markdown report to this file instead of stdout.",
    )
    args = parser.parse_args()

    root = repository_root(Path(args.repo) if args.repo else None)
    if not (root / ".git").is_dir():
        print(f"Warning: {root} does not look like a git repository root.", file=sys.stderr)

    folders = discover_top_level_folders(root)
    report = build_report(root, folders)

    if args.output:
        out_path = Path(args.output)
        out_path.write_text(report, encoding="utf-8")
        print(f"Report written to {out_path}")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
