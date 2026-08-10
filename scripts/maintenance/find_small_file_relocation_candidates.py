#!/usr/bin/env python3
"""Find small files in a root folder and suggest relocation destinations.

This is a lightweight, heuristic analyzer. It counts physical lines of code (LoC)
for the immediate files in a directory and suggests where small files (<300 LoC,
configurable) could be moved based on extension and naming conventions. It is
meant to be run against one root folder at a time.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


THRESHOLD = 300

# Destination suggestions by extension / role.
DESTINATION_HINTS = {
    ".py": ("scripts/maintenance/", "utility/maintenance Python scripts"),
    ".sh": ("scripts/maintenance/", "utility/maintenance shell scripts"),
    ".md": ("docs/development/", "documentation / analysis / proposal notes"),
    ".txt": ("data/", "generated or auxiliary text data"),
    ".json": ("data/", "JSON data files"),
    ".csv": ("data/", "CSV data files"),
    ".png": ("docs/assets/", "image assets"),
    ".jpg": ("docs/assets/", "image assets"),
    ".jpeg": ("docs/assets/", "image assets"),
    ".gif": ("docs/assets/", "image assets"),
    ".pdf": ("docs/assets/", "reference documents / papers"),
    ".toml": ("KEEP", "project/tooling configuration"),
    ".ini": ("KEEP", "tooling configuration"),
    ".cfg": ("KEEP", "tooling configuration"),
    ".yaml": ("KEEP", "configuration files"),
    ".yml": ("KEEP", "configuration files"),
    ".lock": ("KEEP", "lock files"),
    ".example": ("KEEP", "example environment files"),
    ".gitignore": ("KEEP", "git configuration"),
    ".gitmodules": ("KEEP", "git configuration"),
    ".python-version": ("KEEP", "Python version pin"),
    ".bobignore": ("KEEP", "Bob ignore configuration"),
    ".ruffignore": ("KEEP", "Ruff ignore configuration"),
    ".DS_Store": ("REMOVE", "macOS metadata file"),
    ".pre-commit-config.yaml": ("KEEP", "pre-commit configuration"),
    ".dockerignore": ("KEEP", "Docker ignore configuration"),
    ".env": ("KEEP", "environment configuration"),
}

ENTRYPOINT_NAMES = {
    "start.sh",
    "start-with-minio.sh",
    "run_fast.py",
    "streamlit_app.py",
    "streamlit_app_progressive.py",
    "entrypoint.sh",
    "prestart.sh",
    "tests-start.sh",
    "run_dev.py",
    "run_prod.py",
    "run_migration.py",
    "run_benchmark_migration.py",
    "run_method_type_migration.py",
    "start_backend.sh",
    "start_backend_prod.sh",
}


UNKNOWN = ("REVIEW", "no automatic suggestion; review manually")


def is_binary(path: Path, sample_size: int = 8192) -> bool:
    """Return True if the file appears to be binary."""
    try:
        with path.open("rb") as f:
            chunk = f.read(sample_size)
    except OSError:
        return True
    if not chunk:
        return False
    return b"\x00" in chunk


def count_lines(path: Path) -> int:
    """Count physical lines in a text file."""
    return sum(1 for _ in path.read_text(encoding="utf-8", errors="replace").splitlines())


def suggest(path: Path, loc: int) -> tuple[str, str]:
    """Return (destination, reason) for a given file path."""
    name = path.name
    lower_name = name.lower()
    suffix = path.suffix.lower()

    # Remove a leading dot from "extension" for hidden dot-files (e.g. .env).
    if not suffix and name.startswith("."):
        suffix = name

    if name in ENTRYPOINT_NAMES:
        return ("KEEP", "top-level entry/start script")

    if name in {"README.md", "START_HERE.md"}:
        return ("KEEP", "root README / onboarding doc")

    if name == "Makefile":
        return ("KEEP", "build tooling")

    if name == "docker-compose.yml":
        return ("KEEP", "Docker compose configuration")

    if name == "streamlit_requirements.txt":
        return ("KEEP", "Streamlit requirements referenced by start scripts")

    if name == "package-lock.json":
        return ("REMOVE", "ignored lock file; safe to delete if not needed")

    if name == ".gitignore_parent":
        return ("KEEP", "git configuration")

    if suffix == ".md":
        text = path.read_text(encoding="utf-8", errors="replace").lower()
        if any(k in text for k in ("superseded", "deprecated")):
            return ("docs/archive/", "appears to be historical/archived documentation")
        if any(k in lower_name for k in ("architecture", "decision")):
            return ("docs/architecture/", "architecture / decision documentation")
        if any(k in lower_name for k in ("proposal", "analysis", "recommendation")):
            return ("docs/development/", "proposal / analysis documentation")
        if any(k in lower_name for k in ("guide", "flow", "terminology", "import", "start_here")):
            return ("docs/user-guides/", "user / developer guide")
        return DESTINATION_HINTS[".md"]

    if suffix in DESTINATION_HINTS:
        return DESTINATION_HINTS[suffix]

    return UNKNOWN


def analyze(root: Path, threshold: int, include_binary: bool) -> list[dict]:
    """Analyze files directly inside ``root`` and return candidates."""
    candidates = []
    for path in sorted(root.iterdir()):
        if not path.is_file():
            continue

        binary = is_binary(path)
        if binary and not include_binary:
            continue

        if binary:
            loc = 0
        else:
            try:
                loc = count_lines(path)
            except OSError:
                continue

        if loc > threshold and not binary:
            continue

        dest, reason = suggest(path, loc)
        candidates.append(
            {
                "path": path,
                "loc": loc,
                "binary": binary,
                "dest": dest,
                "reason": reason,
            }
        )

    return candidates


def format_markdown(candidates: list[dict], root: Path, threshold: int) -> str:
    """Render a markdown report of candidates."""
    lines = [
        f"# Small file relocation candidates for `{root}`",
        "",
        f"Threshold: **≤{threshold} LoC** (physical lines).",
        "",
        "| File | LoC | Binary | Suggested destination | Reason |",
        "|------|-----|--------|----------------------|--------|",
    ]

    for c in candidates:
        loc = "N/A" if c["binary"] else str(c["loc"])
        binary = "yes" if c["binary"] else "no"
        rel = c["path"].relative_to(root)
        lines.append(
            f"| `{rel}` | {loc} | {binary} | `{c['dest']}` | {c['reason']} |"
        )

    lines.append("")
    lines.append(
        "*Note: suggestions are heuristic. Verify references before moving any file.*"
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Find small files in a root folder and suggest relocation destinations."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Root folder to inspect (default: current directory).",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=THRESHOLD,
        help=f"LoC threshold for flagging files (default: {THRESHOLD}).",
    )
    parser.add_argument(
        "--include-binary",
        action="store_true",
        help="Include binary files in the report.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Optional path to write a Markdown report.",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    if not root.is_dir():
        print(f"Error: {root} is not a directory", file=sys.stderr)
        return 1

    candidates = analyze(root, args.threshold, args.include_binary)
    report = format_markdown(candidates, root, args.threshold)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
        print(f"Report written to {args.output}")
    else:
        print(report)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
