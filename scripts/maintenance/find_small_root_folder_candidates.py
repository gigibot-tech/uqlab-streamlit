"""Find root-level folders whose files are candidates for relocation.

Scans the immediate subdirectories of a target directory (defaults to the
project root) and reports folders whose files are mostly small (<200 LoC strong,
<300 LoC medium). For each candidate it suggests a relocation target based on
the folder name and the conventions used in this repository.

Usage:
    python scripts/maintenance/find_small_root_folder_candidates.py [PATH]

Examples:
    # Analyze the project root using the default 200/300 line thresholds
    python scripts/maintenance/find_small_root_folder_candidates.py

    # Analyze a specific folder with a single threshold
    python scripts/maintenance/find_small_root_folder_candidates.py /workspace/backend --threshold 300
"""

from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path
from statistics import median
from typing import Iterable

# File patterns that are not source files we should consider for LoC.
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
    ".db",
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
    ".cursor",
    ".vscode",
    ".bob",
}

# Root-level folders that should not be relocated.
KEEP_FOLDERS = {
    "src",
    "tests",
    "data",
    ".git",
    ".cursor",
    ".vscode",
    ".docs",
    ".bob",
}

# Folder-name heuristics -> (suggested_target, rationale).
RELOC_RULES: dict[str, tuple[str, str]] = {
    "configs": ("src/uqlab_core/configs/", "Package configs with the ML core library"),
    "uqlab-flask": ("legacy/uqlab-flask/", "Deprecated Flask UI prototype"),
    ".docs": ("docs/setup/", "Hidden docs belong in the docs/ hierarchy"),
    "backend/scripts": ("scripts/backend/", "Centralize backend-specific shell scripts"),
    "docs/components": ("docs/archive/components/", "Component stubs are archived reference docs"),
    "scripts/runners": ("src/uqlab_core/cli/", "CLI runners belong in the installable package"),
    "notebooks/validation": ("src/uqlab_core/notebook_utils/", "Notebook support utilities belong in the package"),
}


def should_skip(path: Path) -> bool:
    if path.is_symlink():
        return True
    name = path.name
    if name.startswith(".") and name not in {".docs"}:
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


def iter_files(folder: Path, recursive: bool) -> Iterable[Path]:
    if recursive:
        for path in sorted(folder.rglob("*")):
            if path.is_file() and not should_skip(path):
                yield path
    else:
        for path in sorted(folder.iterdir()):
            if path.is_file() and not should_skip(path):
                yield path


def find_references(folder: Path, repo_root: Path, excluded: set[str] | None = None) -> list[str]:
    """Find files in the repo that reference this folder path.

    Excludes the report and the analyzer script themselves so the generated
    report does not cite itself.
    """
    rel = folder.relative_to(repo_root)
    pattern = str(rel).replace("\\", "/")

    if excluded is None:
        excluded = set()

    refs: set[str] = set()
    try:
        result = subprocess.run(
            ["rg", "-n", "--no-follow", "-g", "!*.lock", "-g", "!*.png", "-g", "!*.jpg",
             "-g", "!*.jpeg", "-g", "!*.gif", "-g", "!*.pdf", pattern],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        for line in result.stdout.splitlines():
            file_part = line.split(":", 1)[0]
            if file_part in excluded:
                continue
            refs.add(file_part)
    except FileNotFoundError:
        pass

    return sorted(refs)[:10]


def suggest_relocation(folder: Path, repo_root: Path) -> tuple[str, str]:
    """Return (target, rationale) for a candidate folder."""
    rel = folder.relative_to(repo_root)
    rel_key = str(rel).replace("\\", "/")

    if rel_key in RELOC_RULES:
        return RELOC_RULES[rel_key]

    # Content-based heuristics.
    has_python = any(f.suffix == ".py" for f in iter_files(folder, recursive=True))
    has_shell = any(f.suffix == ".sh" for f in iter_files(folder, recursive=True))
    has_yaml = any(f.suffix in {".yaml", ".yml"} for f in iter_files(folder, recursive=True))
    has_md = any(f.suffix == ".md" for f in iter_files(folder, recursive=True))

    if has_shell and not has_python:
        return ("scripts/", "Folder contains only shell scripts")
    if has_yaml and not has_python and not has_shell:
        return ("configs/", "Folder contains only YAML configuration files")
    if has_md and not has_python and not has_shell and not has_yaml:
        return ("docs/", "Folder contains only documentation")

    return ("TBD", "No strong relocation heuristic; review manually")


def analyze_root(
    root: Path,
    threshold_low: int,
    threshold_high: int,
    recursive: bool = True,
    excluded: set[str] | None = None,
) -> list[dict]:
    root = root.resolve()
    candidates: list[dict] = []

    for folder in sorted(root.iterdir()):
        if not folder.is_dir() or folder.is_symlink():
            continue
        if folder.name in KEEP_FOLDERS:
            continue
        if any(part in SKIP_PREFIXES for part in folder.parts):
            continue

        files = list(iter_files(folder, recursive))
        if not files:
            continue

        counts = [count_lines(f)[1] for f in files]
        max_lines = max(counts)
        avg_lines = sum(counts) / len(counts)
        med_lines = median(counts)

        if max_lines < threshold_low:
            strength = "strong"
        elif max_lines < threshold_high:
            strength = "medium"
        else:
            continue

        target, rationale = suggest_relocation(folder, root)
        refs = find_references(folder, root, excluded=excluded)

        candidates.append(
            {
                "folder": folder,
                "rel": folder.relative_to(root),
                "files": files,
                "counts": counts,
                "max_lines": max_lines,
                "avg_lines": avg_lines,
                "med_lines": med_lines,
                "strength": strength,
                "target": target,
                "rationale": rationale,
                "references": refs,
            }
        )

    candidates.sort(key=lambda c: c["max_lines"])
    return candidates


def render_report(
    root: Path, candidates: list[dict], threshold_low: int, threshold_high: int
) -> str:
    md = [f"# Small Root Folder Relocation Candidates – `{root.name}`\n"]
    md.append(f"**Root analyzed:** `{root}`\n")
    md.append(f"**Thresholds:** files under {threshold_low} LoC are strong candidates, "
              f"files under {threshold_high} LoC are medium candidates\n")
    md.append(
        f"**Found:** {len(candidates)} root folder(s) whose files all fall below the thresholds\n"
    )

    strong = [c for c in candidates if c["strength"] == "strong"]
    medium = [c for c in candidates if c["strength"] == "medium"]

    md.append("\n## Strong candidates (all files < {} lines)\n".format(threshold_low))
    if strong:
        md.append("| Folder | Files | Max | Median | Suggested target | Rationale |")
        md.append("|--------|-------|-----|--------|------------------|-----------|")
        for c in strong:
            md.append(
                f"| `{c['rel']}` | {len(c['files'])} | {c['max_lines']} | "
                f"{int(c['med_lines'])} | `{c['target']}` | {c['rationale']} |"
            )
    else:
        md.append("_No strong candidates found._\n")

    md.append("\n## Medium candidates (all files < {} lines)\n".format(threshold_high))
    if medium:
        md.append("| Folder | Files | Max | Median | Suggested target | Rationale |")
        md.append("|--------|-------|-----|--------|------------------|-----------|")
        for c in medium:
            md.append(
                f"| `{c['rel']}` | {len(c['files'])} | {c['max_lines']} | "
                f"{int(c['med_lines'])} | `{c['target']}` | {c['rationale']} |"
            )
    else:
        md.append("_No medium candidates found._\n")

    if candidates:
        md.append("\n## References per candidate\n")
        for c in candidates:
            md.append(f"\n### `{c['rel']}`\n")
            if c["references"]:
                md.append("Referenced by:")
                for ref in c["references"]:
                    md.append(f"- `{ref}`")
            else:
                md.append("_No direct references found in the codebase._")
            md.append("")

    md.append("\n## Notes\n")
    md.append(
        "- By default all files inside each root subfolder are considered "
        "(equivalent to `--recursive`). Pass `--no-recursive` to look only at "
        "direct files.\n"
    )
    md.append(
        "- Folders such as `src/`, `tests/`, `data/`, and tooling metadata "
        "(`.git`, `.cursor`, `.vscode`) are intentionally skipped.\n"
    )
    md.append(
        "- Before moving any folder, verify consumers such as Dockerfiles, "
        "CI/CD, READMEs, import paths, and `runtime_paths.configs_dir()`.\n"
    )
    md.append(
        "- Suggestions are based on folder name and content heuristics; review "
        "manually before relocating.\n"
    )

    return "\n".join(md)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Find root folders whose files are small enough to relocate."
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
        default=True,
        action="store_true",
        help="Evaluate nested subfolders in addition to immediate root folders (default: True)",
    )
    parser.add_argument(
        "--no-recursive",
        dest="recursive",
        action="store_false",
        help="Only consider direct files in each root subfolder",
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

    script_path = Path(__file__).resolve().relative_to(root)
    excluded: set[str] = {str(script_path)}
    if args.output:
        out_abs = args.output.resolve()
        if out_abs.is_relative_to(root):
            excluded.add(str(out_abs.relative_to(root)))
        else:
            excluded.add(str(args.output))

    candidates = analyze_root(
        root, args.threshold_low, args.threshold_high, args.recursive, excluded=excluded
    )
    report = render_report(root, candidates, args.threshold_low, args.threshold_high)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
        print(f"Report written to {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
