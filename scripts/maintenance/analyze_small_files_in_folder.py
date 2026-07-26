#!/usr/bin/env python3
"""Analyze a single folder for small files and suggest relocation candidates.

A "small file" is defined as <= 200 LoC (strict) or <= 300 LoC (lenient).
The script scans every relevant file inside the supplied folder, categorizes
them by size, and produces a Markdown report with proposed relocation targets
and a keep/move verdict.

Usage:
    python scripts/maintenance/analyze_small_files_in_folder.py tests
    python scripts/maintenance/analyze_small_files_in_folder.py backend --root /workspace
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import NamedTuple

STRICT_LIMIT = 200
LENIENT_LIMIT = 300

# File extensions and names that are not meaningful line-count targets.
SKIP_EXTENSIONS = {
    ".ipynb",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".pdf",
    ".tar.gz",
    ".zip",
    ".pyc",
    ".pyo",
    ".DS_Store",
}
SKIP_NAMES = {".DS_Store", ".gitkeep", ".gitignore"}


class FileInfo(NamedTuple):
    rel: Path
    loc: int
    suffix: str

    def size_category(self) -> str:
        if self.loc <= STRICT_LIMIT:
            return "strict"
        if self.loc <= LENIENT_LIMIT:
            return "lenient"
        return "large"


def count_lines(path: Path) -> int:
    """Return the number of non-empty lines in a text file."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except (OSError, UnicodeDecodeError):
        return 0
    return sum(1 for line in text.splitlines() if line.strip())


def should_skip_file(path: Path) -> bool:
    """Return True if the file should not be counted."""
    if path.is_symlink():
        return True
    if path.name in SKIP_NAMES:
        return True
    if path.suffix.lower() in SKIP_EXTENSIONS:
        return True
    if path.suffix.lower() in {".pyc", ".pyo"}:
        return True
    return False


def analyze_folder(folder: Path, root: Path) -> list[FileInfo]:
    """Collect line counts for every relevant file inside the folder."""
    files: list[FileInfo] = []
    for path in folder.rglob("*"):
        if not path.is_file():
            continue
        if should_skip_file(path):
            continue
        rel = path.relative_to(root)
        loc = count_lines(path)
        files.append(FileInfo(rel, loc, path.suffix.lower()))
    files.sort(key=lambda item: item.loc)
    return files


def _has_pytest_functions(path: Path) -> bool:
    """Return True if the file contains pytest-style `def test_*` functions."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except (OSError, UnicodeDecodeError):
        return False
    return "def test_" in text


def suggest_target(info: FileInfo, folder_name: str, root: Path) -> str:
    """Suggest a relocation target for a small file, or 'keep'."""
    parts = list(info.rel.parts)
    basename = info.rel.name
    abs_path = root / info.rel

    # Keep documentation that explains the folder itself.
    if basename.lower() == "readme.md" and len(parts) <= 2:
        return "keep (folder documentation)"

    # Keep __init__.py files — they may be required by tooling or pytest discovery.
    if basename == "__init__.py":
        return "keep (namespace marker)"

    # Legacy / diagnostic scripts inside tests/ need special handling.
    if folder_name == "tests" and info.suffix == ".py" and "legacy" in parts:
        if _has_pytest_functions(abs_path):
            return "candidate: scripts/diagnostics/ or scripts/legacy/ (contains pytest functions; update paths if moved)"
        return "candidate: scripts/diagnostics/ or scripts/legacy/ (no pytest functions; update relative paths)"

    # Keep canonical pytest tests in the tests/ tree.
    if folder_name == "tests" and basename.startswith("test_") and info.suffix == ".py":
        return "keep (pytest discovery depends on tests/)"

    # Backend scripts are usually backend-specific.
    if folder_name == "backend" and info.suffix in {".sh", ".sql"}:
        return "keep (backend-specific)"

    # Notebooks support files could live next to notebooks or in scripts/.
    if folder_name == "notebooks" and info.suffix == ".py":
        return "candidate: scripts/notebook_support/ or keep (if tied to notebooks)"

    # Configs are already handled by a dedicated relocation path.
    if folder_name == "configs":
        return "candidate: src/uqlab_core/configs/"

    # Data folder is usually empty or holds external assets.
    if folder_name == "data":
        return "candidate: src/uqlab_core/data/ or remove if empty"

    # Flask package relocation is handled elsewhere.
    if folder_name == "uqlab-flask":
        return "candidate: src/uqlab_flask/ or legacy/uqlab-flask/"

    return "review manually"


def build_report(folder_name: str, folder: Path, root: Path, files: list[FileInfo]) -> str:
    """Render the analysis as Markdown."""
    strict = [f for f in files if f.size_category() == "strict"]
    lenient = [f for f in files if f.size_category() == "lenient"]
    large = [f for f in files if f.size_category() == "large"]

    total_loc = sum(f.loc for f in files)
    max_loc = max((f.loc for f in files), default=0)

    lines: list[str] = []
    lines.append(f"# Small File Relocation Analysis — `{folder_name}/`")
    lines.append("")
    lines.append(
        "Generated by `scripts/maintenance/analyze_small_files_in_folder.py`."
    )
    lines.append("")
    lines.append("## Definition")
    lines.append("")
    lines.append(f"- **Strict small**: every file <= {STRICT_LIMIT} LoC")
    lines.append(f"- **Lenient small**: every file <= {LENIENT_LIMIT} LoC")
    lines.append(
        "- Binary assets, symlinks, and conventional metadata files are ignored."
    )
    lines.append("")
    lines.append("## Folder overview")
    lines.append("")
    lines.append(f"- **Folder**: `{folder.relative_to(root)}`")
    lines.append(f"- **Files counted**: {len(files)}")
    lines.append(f"- **Total LoC**: {total_loc}")
    lines.append(f"- **Largest file**: {max_loc} LoC")
    lines.append(f"- **Strict small files (<= {STRICT_LIMIT} LoC)**: {len(strict)}")
    lines.append(f"- **Lenient small files (<= {LENIENT_LIMIT} LoC)**: {len(strict) + len(lenient)}")
    lines.append(f"- **Large files (> {LENIENT_LIMIT} LoC)**: {len(large)}")
    lines.append("")

    if strict:
        lines.append(f"## Strict small files (<= {STRICT_LIMIT} LoC)")
        lines.append("")
        lines.append("| File | LoC | Suggested action |")
        lines.append("|------|-----|------------------|")
        for info in strict:
            target = suggest_target(info, folder_name, root)
            lines.append(f"| `{info.rel}` | {info.loc} | {target} |")
        lines.append("")

    if lenient:
        lines.append(f"## Lenient small files ({STRICT_LIMIT + 1}–{LENIENT_LIMIT} LoC)")
        lines.append("")
        lines.append("| File | LoC | Suggested action |")
        lines.append("|------|-----|------------------|")
        for info in lenient:
            target = suggest_target(info, folder_name, root)
            lines.append(f"| `{info.rel}` | {info.loc} | {target} |")
        lines.append("")

    if large:
        lines.append(f"## Large files (> {LENIENT_LIMIT} LoC)")
        lines.append("")
        lines.append("These files are large enough that they are not considered small-file relocation candidates.")
        lines.append("")
        lines.append("| File | LoC |")
        lines.append("|------|-----|")
        for info in large:
            lines.append(f"| `{info.rel}` | {info.loc} |")
        lines.append("")

    lines.append("## Relocation verdict")
    lines.append("")
    if not strict and not lenient:
        lines.append(
            f"No files in `{folder_name}/` are under the {LENIENT_LIMIT} LoC threshold. "
            "This folder is not a small-file relocation candidate."
        )
    elif folder_name in {"configs", "data", "uqlab-flask"}:
        lines.append(
            f"`{folder_name}/` contains only small files. The whole folder is a relocation candidate; "
            "see the suggested targets above and existing relocation branches for prior art."
        )
    elif folder_name == "tests":
        lines.append(
            "The canonical pytest files in `tests/` should **stay where they are** — pytest discovery is "
            "configured to look at `tests/` (`testpaths = tests` in `pytest.ini`). Moving them would break "
            "CI/test workflows and require import updates.\n\n"
            "The files in `tests/legacy/` are small scripts rather than pytest tests. They are candidates "
            "for moving to `scripts/diagnostics/` or `scripts/legacy/`, but several of them rely on relative "
            "paths (e.g., `Path(__file__).parent / 'backend'`). Any relocation must update those paths and "
            "verify that the scripts still run."
        )
    elif folder_name == "backend":
        lines.append(
            "`backend/` mixes small utility scripts with substantial application code. "
            "The small helper scripts are backend-specific and should stay. Relocating them would add "
            "cross-folder coupling without clear benefit."
        )
    elif folder_name == "notebooks":
        lines.append(
            "`notebooks/` contains small Python support files alongside large `.ipynb` notebooks. "
            "The support files are tightly coupled to the notebooks and should stay, or be moved to a "
            "dedicated `scripts/notebook_support/` folder if the number of support files grows."
        )
    else:
        lines.append(
            f"`{folder_name}/` has {len(strict) + len(lenient)} files under {LENIENT_LIMIT} LoC. "
            "Review the per-file suggestions above before moving anything."
        )
    lines.append("")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Analyze a folder for small files and suggest relocation candidates."
    )
    parser.add_argument(
        "folder",
        help="Folder to analyze (relative to root or absolute)",
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Workspace root used for relative paths (default: current directory)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output Markdown report path (default: print to stdout)",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    folder = Path(args.folder)
    if not folder.is_absolute():
        folder = root / folder
    folder = folder.resolve()

    if not folder.is_dir():
        print(f"Error: not a directory: {folder}", file=sys.stderr)
        return 1

    folder_name = folder.name
    files = analyze_folder(folder, root)
    report = build_report(folder_name, folder, root, files)

    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = root / output_path
        output_path.write_text(report, encoding="utf-8")
        print(f"Report written to {output_path}")
    else:
        print(report)

    return 0


if __name__ == "__main__":
    sys.exit(main())
