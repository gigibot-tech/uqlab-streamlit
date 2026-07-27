"""Find small files in a target folder that are candidates for relocation.

Scans a directory (defaults to the project root) and reports files whose
non-blank line count falls below configurable thresholds. For each candidate,
it suggests a relocation target based on the file type and the conventions
used in this repository.

Usage:
    python scripts/maintenance/find_small_file_relocation_candidates.py [PATH] [--threshold 200]

Examples:
    # Analyze the project root using the default 200/300 line thresholds
    python scripts/maintenance/find_small_file_relocation_candidates.py

    # Analyze a specific folder with a single threshold
    python scripts/maintenance/find_small_file_relocation_candidates.py /workspace/uqlab-flask --threshold 300
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Iterable

# File patterns that are not source files we should relocate.
SKIP_SUFFIXES = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".lock",
    ".pyc",
    ".pyo",
    ".so",
    ".dylib",
    ".dll",
    ".exe",
    ".zip",
    ".tar",
    ".gz",
    ".tgz",
    ".bz2",
    ".xz",
}

# Hidden directories and files that are typically tooling metadata.
SKIP_PREFIXES = {
    ".git",
    "__pycache__",
    ".venv",
    "node_modules",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}

RELOC_RULES = {
    ".py": ("scripts/maintenance/", "Python utility/migration script"),
    ".sh": ("scripts/deployment/", "Shell start-up / deployment script"),
    ".md": ("docs/development/", "Documentation / analysis report"),
    ".yaml": ("configs/", "YAML configuration"),
    ".yml": ("configs/", "YAML configuration"),
    ".toml": ("root", "Python project metadata (keep in root)"),
    ".ini": ("root", "Tooling configuration (keep in root)"),
    ".txt": ("root", "Requirements / ignore file (keep in root)"),
    ".css": ("assets/static/", "Static stylesheet"),
    ".html": ("templates/", "HTML template"),
    ".ipynb": ("notebooks/", "Jupyter notebook"),
}


def should_skip(path: Path) -> bool:
    if path.is_symlink():
        return True
    if path.name.startswith(".") and path.name not in {
        ".env.example",
        ".env.production.example",
        ".gitignore",
        ".gitmodules",
        ".bobignore",
        ".ruffignore",
        ".python-version",
    }:
        return True
    if any(part in SKIP_PREFIXES for part in path.parts):
        return True
    if path.suffix.lower() in SKIP_SUFFIXES:
        return True
    return False


def count_lines(path: Path) -> tuple[int, int, int]:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    total = len(lines)
    non_blank = sum(1 for line in lines if line.strip())
    code_like = sum(
        1
        for line in lines
        if line.strip() and not line.strip().startswith(("#", "//", "/*", "*", "--"))
    )
    return total, non_blank, code_like


def categorize(path: Path, rel: Path) -> tuple[str, str]:
    ext = path.suffix.lower()
    if ext in RELOC_RULES:
        return RELOC_RULES[ext]

    if path.name.startswith("."):
        return ("root", "Dotfile / tooling config (keep in root)")

    if path.name in {"Makefile", "docker-compose.yml", "Dockerfile"}:
        return ("root", "Build / deployment orchestration (keep in root)")

    return ("TBD", "No strong relocation heuristic; review manually")


def _iter_files(root: Path, recursive: bool) -> Iterable[Path]:
    if recursive:
        for path in sorted(root.rglob("*")):
            if path.is_file():
                yield path
    else:
        for path in sorted(root.iterdir()):
            if path.is_file():
                yield path


def analyze_folder(
    root: Path, threshold_low: int, threshold_high: int, recursive: bool = False
) -> dict:
    root = root.resolve()
    files: list[dict] = []

    for path in _iter_files(root, recursive):
        if should_skip(path):
            continue

        rel = path.relative_to(root)
        total, non_blank, code_like = count_lines(path)
        target, rationale = categorize(path, rel)

        files.append(
            {
                "name": path.name,
                "rel": str(rel),
                "total": total,
                "non_blank": non_blank,
                "code_like": code_like,
                "target": target,
                "rationale": rationale,
            }
        )

    files.sort(key=lambda f: f["non_blank"])

    under_low = [f for f in files if f["non_blank"] < threshold_low]
    under_high = [f for f in files if threshold_low <= f["non_blank"] < threshold_high]
    over_high = [f for f in files if f["non_blank"] >= threshold_high]

    return {
        "root": root,
        "files": files,
        "under_low": under_low,
        "under_high": under_high,
        "over_high": over_high,
        "threshold_low": threshold_low,
        "threshold_high": threshold_high,
    }


def render_report(result: dict) -> str:
    root = result["root"]
    low = result["threshold_low"]
    high = result["threshold_high"]
    recursive = result.get("recursive", False)

    md = [f"# Small File Relocation Candidates – `{root.name}`\n"]
    md.append(f"**Mode:** {'recursive' if recursive else 'top-level only'}\n")
    md.append(f"**Folder:** `{root}`\n")
    md.append(f"**Thresholds:** {low} / {high} non-blank lines\n")
    md.append(f"**Scanned files:** {len(result['files'])}\n")
    md.append(
        f"**Candidates:** {len(result['under_low'])} under {low} lines, "
        f"{len(result['under_high'])} between {low} and {high} lines\n"
    )

    md.append("\n## Strong candidates (< {} lines)\n".format(low))
    if result["under_low"]:
        md.append("| File | Total | Non-blank | Suggested target | Rationale |")
        md.append("|------|-------|-----------|------------------|-----------|")
        for f in result["under_low"]:
            md.append(
                f"| `{f['rel']}` | {f['total']} | {f['non_blank']} | "
                f"`{f['target']}` | {f['rationale']} |"
            )
    else:
        md.append("_No files under the low threshold._\n")

    md.append("\n## Medium candidates ({}–{} lines)\n".format(low, high - 1))
    if result["under_high"]:
        md.append("| File | Total | Non-blank | Suggested target | Rationale |")
        md.append("|------|-------|-----------|------------------|-----------|")
        for f in result["under_high"]:
            md.append(
                f"| `{f['rel']}` | {f['total']} | {f['non_blank']} | "
                f"`{f['target']}` | {f['rationale']} |"
            )
    else:
        md.append("_No files in the medium range._\n")

    md.append("\n## Files at or above {} lines (likely stay)\n".format(high))
    if result["over_high"]:
        md.append("| File | Total | Non-blank | Notes |")
        md.append("|------|-------|-----------|-------|")
        for f in result["over_high"]:
            md.append(
                f"| `{f['rel']}` | {f['total']} | {f['non_blank']} | {f['rationale']} |"
            )
    else:
        md.append("_No files at or above the high threshold._\n")

    md.append("\n## Notes\n")
    md.append(
        "- Suggestions are based on filename/extension heuristics and this repo's conventions.\n"
    )
    md.append(
        "- Before moving any file, verify it is not referenced by absolute path from "
        "CI/CD, Docker, or documentation.\n"
    )
    md.append(
        "- Dotfiles (`.env.example`, `.gitignore`, `.python-version`, etc.) and project "
        "metadata (`pyproject.toml`) are intentionally kept in the root.\n"
    )

    return "\n".join(md)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Find small files that are candidates for relocation."
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=Path(__file__).resolve().parents[2],
        help="Directory to analyze (default: project root)",
    )
    parser.add_argument(
        "--threshold-low",
        type=int,
        default=200,
        help="Lower threshold for strong candidates (default: 200)",
    )
    parser.add_argument(
        "--threshold-high",
        type=int,
        default=300,
        help="Upper threshold for medium candidates (default: 300)",
    )
    parser.add_argument(
        "--recursive",
        "-r",
        action="store_true",
        help="Scan all files recursively within the target folder",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Optional markdown output path (default: print to stdout)",
    )
    args = parser.parse_args()

    root = Path(args.path).expanduser().resolve()
    if not root.is_dir():
        raise SystemExit(f"Error: {root} is not a directory")

    result = analyze_folder(root, args.threshold_low, args.threshold_high, args.recursive)
    result["recursive"] = args.recursive
    report = render_report(result)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
        print(f"Report written to {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
