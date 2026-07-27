#!/usr/bin/env python3
"""Find small files in a root-level folder and suggest relocation targets.

A "small file" is <= 200 LoC (strict) or <= 300 LoC (lenient). The script scans a
given directory directly under the workspace root, ignores conventional
folder-level files (README, __init__, lockfiles, etc.), and prints a Markdown
report with a proposed relocation target.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

STRICT_LIMIT = 200
LENIENT_LIMIT = 300

CONVENTIONAL_FILENAMES = {
    "README.md",
    "__init__.py",
    "requirements.txt",
    ".gitignore",
    ".dockerignore",
    ".pre-commit-config.yaml",
    "pyproject.toml",
    "uv.lock",
    "package-lock.json",
    "Dockerfile",
    "alembic.ini",
    ".python-version",
    ".DS_Store",
    ".keep",
}

SKIP_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".pdf",
    ".tar.gz",
    ".zip",
    ".ipynb",
}


def count_lines(path: Path) -> int:
    try:
        return len(path.read_text(encoding="utf-8", errors="replace").splitlines())
    except (OSError, UnicodeDecodeError):
        return 0


def should_skip(path: Path) -> bool:
    if path.is_symlink():
        return True
    if path.name in CONVENTIONAL_FILENAMES:
        return True
    if path.suffix in SKIP_EXTENSIONS:
        return True
    return False


def suggest_relocation(folder: str, path: Path) -> str | None:
    name_lower = path.name.lower()

    if folder == "configs":
        return "src/configs"

    if folder in {"scripts", "backend", "src", "tests", "docs", "notebooks", "uqlab-flask"}:
        return None  # already well-scoped

    if "maintenance" in name_lower or "cleanup" in name_lower:
        return "scripts/maintenance"
    if "fix" in name_lower:
        return "scripts/fixes"
    if "diagnose" in name_lower:
        return "scripts/diagnostics"
    if "setup" in name_lower or "download" in name_lower:
        return "scripts/setup"
    if "deploy" in name_lower or "run_streamlit" in name_lower or "test_api" in name_lower:
        return "scripts/deployment"
    if "run_" in name_lower:
        return "scripts/runners"
    if "example" in name_lower:
        return "scripts/examples"
    if "benchmark" in name_lower or "analyze" in name_lower or "plot" in name_lower or "paper" in name_lower:
        return "scripts/analysis"

    if path.suffix == ".sh":
        return "scripts/shell"
    if path.suffix == ".py":
        return "scripts/utils"

    return None


def gather_candidates(workspace: Path, focus_dir: str) -> list[dict]:
    target = workspace / focus_dir
    if not target.is_dir():
        raise SystemExit(f"Error: '{focus_dir}' is not a directory at the workspace root.")

    candidates: list[dict] = []
    for path in sorted(target.rglob("*")):
        if not path.is_file() or should_skip(path):
            continue

        lines = count_lines(path)
        if lines > LENIENT_LIMIT:
            continue

        candidates.append(
            {
                "path": str(path.relative_to(workspace)),
                "lines": lines,
                "under_200": lines <= STRICT_LIMIT,
                "under_300": lines <= LENIENT_LIMIT,
                "suggested_target": suggest_relocation(focus_dir, path),
            }
        )

    return sorted(candidates, key=lambda f: f["lines"])


def build_report(focus_dir: str, candidates: list[dict]) -> str:
    lines: list[str] = []
    lines.append(f"# Small file relocation candidates: `{focus_dir}/`")
    lines.append("")
    lines.append(f"- **Strict small**: <= {STRICT_LIMIT} LoC")
    lines.append(f"- **Lenient small**: <= {LENIENT_LIMIT} LoC")
    lines.append("- Conventional folder-level files and binary assets are ignored.")
    lines.append("")
    lines.append(f"## Files in `{focus_dir}/`")
    lines.append("")

    if not candidates:
        lines.append("No small files found.")
        return "\n".join(lines)

    lines.append(f"{len(candidates)} small file(s) found.")
    lines.append("")
    lines.append("| File | LoC | Suggested target |")
    lines.append("|------|-----|------------------|")

    actionable = 0
    for file in candidates:
        loc_badge = "<200" if file["under_200"] else "<300"
        target = file["suggested_target"] or "— (keep in place)"
        if file["suggested_target"]:
            actionable += 1
        lines.append(f"| `{file['path']}` | {file['lines']} ({loc_badge}) | {target} |")

    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Total small files**: {len(candidates)}")
    lines.append(f"- **Actionable relocation candidates**: {actionable}")
    if actionable == 0:
        lines.append(
            "No automatic relocation candidates. Every small file is either already in a "
            "well-scoped location or is a conventional folder-level file."
        )
    else:
        lines.append(
            "Actionable files are marked with a suggested target. Review references before moving."
        )

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Find small files in a root-level folder and suggest relocation targets."
    )
    parser.add_argument("--focus", required=True, help="Root-level folder to inspect (e.g. 'configs').")
    parser.add_argument(
        "-o", "--output", help="Output Markdown report path (default: print to stdout)."
    )
    parser.add_argument(
        "--summary",
        help="Write a JSON summary to the given path (default: .cursor/small_file_relocation_summary.json).",
    )
    args = parser.parse_args()

    workspace = Path(__file__).resolve().parents[2]
    candidates = gather_candidates(workspace, args.focus)
    report = build_report(args.focus, candidates)

    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
        print(f"Report written to: {args.output}")
    else:
        print(report)

    summary_path = Path(args.summary) if args.summary else workspace / ".cursor" / "small_file_relocation_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "thresholds": {"strict": STRICT_LIMIT, "lenient": LENIENT_LIMIT},
        "focus": args.focus,
        "candidates": candidates,
        "actionable_count": sum(1 for c in candidates if c["suggested_target"]),
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Summary written to: {summary_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
