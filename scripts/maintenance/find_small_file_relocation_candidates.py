#!/usr/bin/env python3
"""Find small files in root-level folders and suggest relocation candidates.

A "small file" is defined as <= 200 LoC (strict) or <= 300 LoC (lenient).
The script scans every directory located directly under the workspace root,
skips obviously non-relocatable files (e.g. lockfiles, READMEs, package metadata),
and produces a Markdown report with proposed relocation targets based on the
existing scripts/ and backend/ subdirectories.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

# Thresholds that match the prompt language: "less than 200/300 LoC".
STRICT_LIMIT = 200
LENIENT_LIMIT = 300

# Files that are expected to stay at the root of a folder.
KEEP_PATTERNS = {
    "README.md",
    "__init__.py",
    "pyproject.toml",
    "uv.lock",
    "requirements.txt",
    "package-lock.json",
    "Dockerfile",
    ".gitignore",
    ".dockerignore",
    ".pre-commit-config.yaml",
    "alembic.ini",
    "Makefile",
    "pytest.ini",
    "mypy.ini",
    ".python-version",
}

# File extensions that are not worth moving on their own (binary/notebook assets).
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

# Filenames that are clearly not relocation candidates.
SKIP_FILENAMES = {
    ".DS_Store",
}

# Relocation heuristics: filename substring -> preferred destination folder.
HEURISTICS: dict[str, str] = {
    "maintenance": "scripts/maintenance",
    "cleanup": "scripts/maintenance",
    "fix": "scripts/fixes",
    "diagnose": "scripts/diagnostics",
    "setup": "scripts/setup",
    "download": "scripts/setup",
    "deploy": "scripts/deployment",
    "run_streamlit": "scripts/deployment",
    "test_api": "scripts/deployment",
    "generate-client": "scripts/deployment",
    "run_": "scripts/runners",
    "example": "scripts/examples",
    "benchmark": "scripts/analysis",
    "analyze": "scripts/analysis",
    "plot": "scripts/analysis",
    "paper": "scripts/analysis",
    "validate": "scripts/setup",
    "report": "scripts/setup",
}

# Root directories that are allowed to be scanned (kept explicit for clarity).
SKIP_ROOT_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", "archive"}

# Root directories that are already well-scoped; we only report their small files
# for completeness, but never propose relocating them.
WELL_SCOPED_ROOTS = {
    "scripts",
    "backend",
    "configs",
    "docs",
    ".docs",
    ".cursor",
    ".vscode",
    "notebooks",
    "tests",
    "uqlab-flask",
    "src",
    "data",
}

# Files that are expected to stay at the workspace root.
KEEP_AT_ROOT = {
    "README.md",
    "START_HERE.md",
    "Makefile",
    "pyproject.toml",
    "pytest.ini",
    "mypy.ini",
    ".python-version",
    ".gitignore",
    ".gitignore_parent",
    ".gitmodules",
    ".bobignore",
    ".env.example",
    ".env.production.example",
    "docker-compose.yml",
    "streamlit_app_progressive.py",
    "uv.lock",
    "package-lock.json",
    "dependencies.json",
    # Documentation artifacts
    "ARCHITECTURE_CLARIFICATION.md",
    "ARCHITECTURE_IMPROVEMENT_PROPOSAL.md",
    "COMPLETE_SYSTEM_FLOW.md",
    "DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md",
    "EXECUTION_FLOW_AND_CONFIG_GUIDE.md",
    "FINAL_ARCHITECTURE_DECISION.md",
    "IMPORT_GUIDE.md",
    "PACKAGE_REORGANIZATION_PROPOSAL.md",
    "TERMINOLOGY_CLARIFICATION.md",
    # Generated reports
    "SMALL_FILE_RELOCATION_CANDIDATES.md",
}


def count_lines(path: Path) -> int:
    """Return the number of non-empty-ish lines in a text file."""
    try:
        return len(path.read_text(encoding="utf-8", errors="replace").splitlines())
    except (OSError, UnicodeDecodeError):
        return 0


def should_skip(path: Path, lines: int) -> bool | str:
    """Return a skip reason, or False if the file should be considered."""
    if path.is_symlink():
        return "symlink"
    if path.name in KEEP_PATTERNS or path.name in SKIP_FILENAMES:
        return "conventional root file"
    if path.suffix in SKIP_EXTENSIONS:
        return f"{path.suffix} asset"
    if lines == 0:
        return "empty file"
    return False


def suggest_relocation(path: Path, root_dir: str) -> str | None:
    """Suggest a relocation target for a small file.

    Returns None when the file is already in a sensible location or is a
    conventional folder-level file.
    """
    # Files that are already inside well-scoped root directories are not
    # relocation candidates; only report them for completeness.
    if root_dir in WELL_SCOPED_ROOTS:
        return None

    # Keep known root-level files in place.
    if path.name in KEEP_AT_ROOT:
        return None

    name_lower = path.name.lower()
    for substring, target in HEURISTICS.items():
        if substring in name_lower:
            return target

    # Shell scripts that didn't match a heuristic can live in scripts/shell.
    if path.suffix == ".sh":
        return "scripts/shell"

    # Small Python utilities without a better heuristic go to scripts/utils.
    if path.suffix == ".py":
        return "scripts/utils"

    return None


def gather_candidates(workspace: Path, focus_dir: str | None = None) -> dict[str, list[dict]]:
    """Return per-root-dir lists of small file candidates.

    If ``focus_dir`` is provided, only that directory is inspected; otherwise
    the workspace root itself is inspected (files directly under the root).
    """
    candidates: dict[str, list[dict]] = defaultdict(list)

    if focus_dir is None:
        # Inspect files directly at the workspace root.
        root_label = "."
        paths = sorted(workspace.iterdir())
    else:
        target = workspace / focus_dir
        if not target.is_dir():
            print(f"Error: '{focus_dir}' is not a directory at the workspace root.", file=sys.stderr)
            return {}
        root_label = focus_dir
        paths = sorted(target.rglob("*"))

    for path in paths:
        if focus_dir is None and path.is_dir():
            # When scanning the root, skip directories and only report files.
            continue
        if not path.is_file():
            continue

        # Determine the logical root directory for the file.
        if focus_dir is None:
            child_name = "."
        else:
            relative = path.relative_to(workspace)
            child_name = relative.parts[0]

        if child_name in SKIP_ROOT_DIRS:
            continue

        lines = count_lines(path)
        if lines > LENIENT_LIMIT:
            continue

        skip_reason = should_skip(path, lines)
        if skip_reason:
            continue

        target = suggest_relocation(path, child_name)
        candidates[root_label].append(
            {
                "path": str(path.relative_to(workspace)),
                "lines": lines,
                "under_200": lines <= STRICT_LIMIT,
                "under_300": lines <= LENIENT_LIMIT,
                "suggested_target": target,
            }
        )

    return dict(candidates)


def print_report(candidates: dict[str, list[dict]], workspace: Path, focus_dir: str | None = None) -> str:
    """Build a Markdown relocation report and return it."""
    lines: list[str] = []
    lines.append("# Small File Relocation Candidates")
    lines.append("")
    lines.append("Generated by `scripts/maintenance/find_small_file_relocation_candidates.py`.")
    lines.append("")
    lines.append("## Definition")
    lines.append("")
    lines.append(f"- **Strict small**: <= {STRICT_LIMIT} LoC")
    lines.append(f"- **Lenient small**: <= {LENIENT_LIMIT} LoC")
    lines.append("- Non-text assets, symlinks, empty files, and conventional folder-level files (README, pyproject.toml, etc.) are ignored.")
    lines.append("")

    if focus_dir is None:
        lines.append("## Focus: workspace root")
        lines.append("")
        lines.append("Only files directly at the workspace root are considered. Files already inside well-scoped directories (scripts/, backend/, configs/, docs/, etc.) are listed as 'keep in place'.")
        lines.append("")
    else:
        lines.append(f"## Focus: `{focus_dir}/`")
        lines.append("")
        lines.append(f"Files inside `{focus_dir}/` are inspected. Files that already belong in a well-scoped subdirectory of `{focus_dir}/` are listed as 'keep in place'.")
        lines.append("")

    total_files = 0
    actionable_files = 0

    for root_dir, files in sorted(candidates.items()):
        if not files:
            continue
        if focus_dir is None:
            lines.append("## Files at workspace root")
        else:
            lines.append(f"## `{root_dir}/`")
        lines.append("")
        lines.append(f"{len(files)} small file(s) found.")
        lines.append("")
        lines.append("| File | LoC | Suggested target |")
        lines.append("|------|-----|------------------|")
        for file in sorted(files, key=lambda f: f["lines"]):
            total_files += 1
            target = file["suggested_target"] or "— (keep in place)"
            if file["suggested_target"]:
                actionable_files += 1
            loc_badge = "<200" if file["under_200"] else "<300"
            lines.append(f"| `{file['path']}` | {file['lines']} ({loc_badge}) | {target} |")
        lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Total small files scanned**: {total_files}")
    lines.append(f"- **Actionable relocation candidates**: {actionable_files}")
    lines.append("")

    if actionable_files == 0:
        lines.append("No automatic relocation candidates remain. Every small file is either already in a well-scoped folder or is a conventional folder-level file.")
    else:
        lines.append("Actionable files are marked with a suggested target. Review each candidate before moving to avoid breaking imports or documentation references.")
    lines.append("")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Find small files in a root-level folder and suggest relocation targets."
    )
    parser.add_argument(
        "--focus",
        metavar="FOLDER",
        help="Root-level folder to inspect (e.g. 'tests', 'scripts'). "
        "Defaults to the workspace root itself.",
    )
    parser.add_argument(
        "--output",
        "-o",
        metavar="PATH",
        help="Output report path (default: SMALL_FILE_RELOCATION_CANDIDATES.md in the workspace root).",
    )
    args = parser.parse_args(argv)

    workspace = Path(__file__).resolve().parents[2]
    focus_dir = args.focus
    report_path = Path(args.output) if args.output else workspace / "SMALL_FILE_RELOCATION_CANDIDATES.md"

    candidates = gather_candidates(workspace, focus_dir=focus_dir)
    report = print_report(candidates, workspace, focus_dir=focus_dir)

    report_path.write_text(report, encoding="utf-8")
    print(f"Report written to: {report_path}")

    # Also emit a compact JSON summary for automation consumption.
    summary_path = workspace / ".cursor" / "small_file_relocation_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "thresholds": {"strict": STRICT_LIMIT, "lenient": LENIENT_LIMIT},
        "focus": focus_dir,
        "root_folders": candidates,
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Summary written to: {summary_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
