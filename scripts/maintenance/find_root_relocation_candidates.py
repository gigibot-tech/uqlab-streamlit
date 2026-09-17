#!/usr/bin/env python3
"""Find small root-level files that are candidates for relocation.

Usage:
    python scripts/maintenance/find_root_relocation_candidates.py > docs/development/ROOT_SMALL_FILE_CANDIDATES.md
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Iterable

# Files that must stay at repo root for tooling / convention.
KEEP_AT_ROOT: set[str] = {
    ".bobignore",
    ".cursorignore",
    ".env",
    ".env.example",
    ".env.production",
    ".env.production.example",
    ".gitattributes",
    ".gitignore",
    ".gitignore_parent",
    ".gitmodules",
    ".python-version",
    ".ruffignore",
    "LICENSE",
    "Makefile",
    "README.md",
    "pyproject.toml",
    "pytest.ini",
    "uv.lock",
}

# Config files that are small but conventionally kept at root.
KEEP_CONFIG: set[str] = {
    "mypy.ini",
    "docker-compose.yml",
}


def count_lines(path: Path) -> tuple[int, int]:
    """Return (total lines, non-blank lines)."""
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            total = 0
            non_blank = 0
            for line in f:
                total += 1
                if line.strip():
                    non_blank += 1
            return total, non_blank
    except (OSError, UnicodeDecodeError):
        return 0, 0


def suggest_destination(path: Path, total_lines: int) -> tuple[str, str]:
    """Return (destination, rationale) for a candidate file."""
    name = path.name.lower()
    ext = path.suffix.lower()
    stem = path.stem.lower()

    if ext == ".py":
        if "test" in stem:
            return "tests/", "Test-related Python file"
        if any(k in stem for k in ("analyze", "inventory", "dependency")):
            return "scripts/maintenance/", "Analysis / inventory script"
        if any(k in stem for k in ("cleanup", "fix", "diagnose", "organize", "rename", "reorganize", "remove")):
            return "scripts/maintenance/", "Maintenance / cleanup script"
        if any(k in stem for k in ("start", "run", "deploy")):
            return "scripts/deployment/", "Deployment / run script"
        return "scripts/", "Generic utility script"

    if ext == ".sh":
        if any(k in stem for k in ("deploy", "run", "start")):
            return "scripts/deployment/", "Deployment / startup shell script"
        if any(k in stem for k in ("cleanup", "fix", "diagnose", "organize", "rename", "reorganize")):
            return "scripts/maintenance/", "Maintenance shell script"
        return "scripts/", "Generic shell script"

    if ext == ".md":
        if "readme" in stem:
            return "KEEP", "Project README belongs at root"
        if any(k in stem for k in ("architecture", "flow", "terminology", "decision", "clarification")):
            return "docs/architecture-design/", "Architecture / design doc"
        if any(k in stem for k in ("guide", "start_here", "quickstart", "howto")):
            return "docs/user-guides/", "User / onboarding guide"
        if any(k in stem for k in ("execution", "config", "setup", "import")):
            return "docs/setup/", "Setup / execution guide"
        if any(k in stem for k in ("proposal", "improvement", "recommendation", "cleanup", "analysis")):
            return "docs/development/", "Development / planning doc"
        return "docs/", "Generic documentation"

    if ext == ".json":
        if "dependency" in stem:
            return "docs/development/", "Generated dependency report"
        if "package" in stem:
            return "DELETE/ARCHIVE", "NPM artifact with no package.json at root"
        return "data/", "JSON data artifact"

    if ext in {".txt", ".log"}:
        if any(k in stem for k in ("requirement", "req")):
            return "docs/setup/", "Requirements note"
        if any(k in stem for k in ("result", "analysis", "experiment")):
            return "data/", "Generated results / analysis text"
        return "docs/", "Text note"

    if ext in {".yml", ".yaml"}:
        return "configs/ or backend/", "Service / deployment configuration"

    if ext in {".png", ".jpg", ".jpeg", ".gif", ".svg"}:
        return "docs/assets/", "Documentation image asset"

    if ext == ".pdf":
        return "docs/assets/ or data/references/", "Reference paper / PDF"

    return "?", "No clear destination heuristic"


def is_essential(path: Path) -> tuple[bool, str]:
    """Decide whether a root file is conventionally required to stay at root."""
    name = path.name
    if name in KEEP_AT_ROOT:
        return True, "conventional root file"
    if name in KEEP_CONFIG:
        return True, "tooling config (kept at root)"
    if name.startswith(".") and not name.startswith(".."):
        return True, "hidden dotfile / tooling"
    if path.is_symlink():
        return True, "symlink"
    return False, ""


def scan_root(repo_root: Path, thresholds: Iterable[int]) -> list[dict]:
    """Scan immediate root files and return candidate records."""
    threshold_max = max(thresholds)
    records: list[dict] = []

    for entry in sorted(repo_root.iterdir()):
        if not entry.is_file():
            continue

        total, non_blank = count_lines(entry)
        if total == 0 or total >= threshold_max:
            continue

        essential, reason = is_essential(entry)
        if essential:
            continue

        dest, rationale = suggest_destination(entry, total)
        records.append(
            {
                "file": entry.name,
                "total_lines": total,
                "non_blank_lines": non_blank,
                "size_bytes": entry.stat().st_size,
                "suggested_dest": dest,
                "rationale": rationale,
            }
        )

    return records


def render_markdown(records: list[dict], thresholds: list[int], repo_root: Path) -> str:
    """Render a markdown report from candidate records."""
    lines: list[str] = []
    lines.append("# Root Small-File Relocation Candidates")
    lines.append("")
    lines.append(f"**Repo**: `{repo_root.resolve()}`")
    lines.append(f"**Generated**: {__import__('datetime').datetime.now().isoformat(timespec='minutes')}")
    lines.append(f"**Thresholds**: {', '.join(f'<{t} LoC' for t in sorted(thresholds))}")
    lines.append("")
    lines.append(
        "This report lists immediate root-level files whose total line count is below the "
        "threshold(s) and that are not conventional root tooling files. For each file it "
        "suggests a more appropriate folder."
    )
    lines.append("")

    if not records:
        lines.append("No small-file relocation candidates found below the thresholds.")
        return "\n".join(lines)

    # Group by threshold bucket.
    small: list[dict] = [r for r in records if r["total_lines"] < min(thresholds)]
    medium: list[dict] = [
        r for r in records if min(thresholds) <= r["total_lines"] < max(thresholds)
    ]

    def table(title: str, group: list[dict]) -> list[str]:
        out: list[str] = []
        if not group:
            return out
        out.append(f"## {title}")
        out.append("")
        out.append("| File | LoC (non-blank) | Size | Suggested dest | Rationale |")
        out.append("|------|----------------|------|----------------|-----------|")
        for r in group:
            size_kb = r["size_bytes"] / 1024
            loc = f"{r['total_lines']} ({r['non_blank_lines']})"
            out.append(
                f"| `{r['file']}` | {loc} | {size_kb:.1f} KB | `{r['suggested_dest']}` | {r['rationale']} |"
            )
        out.append("")
        return out

    lines.extend(table(f"Files <{min(thresholds)} LoC", small))
    lines.extend(table(f"Files {min(thresholds)}–{max(thresholds) - 1} LoC", medium))

    # Action checklist.
    lines.append("## Recommended Next Steps")
    lines.append("")
    seen = {r["suggested_dest"] for r in records}
    for dest in sorted(seen):
        files = [r["file"] for r in records if r["suggested_dest"] == dest]
        lines.append(f"- **{dest}**: " + ", ".join(f"`{f}`" for f in files))
    lines.append("")

    lines.append("## Cautions")
    lines.append("")
    lines.append(
        "- Before moving executable scripts (`start.sh`, `start-with-minio.sh`, "
        "`organize_root_scripts.sh`) update any relative paths, `Makefile` targets, and PYTHONPATH assumptions."
    )
    lines.append(
        "- `docker-compose.yml` is small but many teams keep it at root; if moved, update "
        "`make` / CI references."
    )
    lines.append(
        "- `package-lock.json` appears to be an orphan NPM artifact; confirm there is no "
        "`package.json` before deleting."
    )
    lines.append(
        "- Large generated artifacts (`dependencies.json`, `analysis_results.txt`) are data, "
        "not source; consider archiving or moving to `data/` / `docs/results/`."
    )
    lines.append("")

    lines.append("## Methodology")
    lines.append("")
    lines.append(
        "Generated by `scripts/maintenance/find_root_relocation_candidates.py`. It scans "
        "immediate root files, skips hidden/tooling files that conventionally stay at root, "
        "and applies a simple filename heuristic to suggest a destination."
    )
    lines.append("")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Find small root files and suggest relocation targets.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root to scan")
    parser.add_argument("--thresholds", nargs="+", type=int, default=[200, 300], help="Line-count thresholds")
    parser.add_argument("--output", type=Path, help="Optional path to write markdown report")
    args = parser.parse_args(argv)

    repo_root = args.root.resolve()
    if not repo_root.is_dir():
        print(f"error: not a directory: {repo_root}", file=sys.stderr)
        return 1

    records = scan_root(repo_root, args.thresholds)
    report = render_markdown(records, args.thresholds, repo_root)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
        print(f"Report written to {args.output}")
    else:
        print(report)

    return 0


if __name__ == "__main__":
    sys.exit(main())
