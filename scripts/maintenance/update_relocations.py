#!/usr/bin/env python3
"""Update Markdown references after relocating root-level files."""

from __future__ import annotations

import os
import re
from pathlib import Path
from urllib.parse import urlparse

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

# old basename -> new path relative to project root
RELOCATIONS: dict[str, str] = {
    "ARCHITECTURE_CLARIFICATION.md": "docs/architecture/ARCHITECTURE_CLARIFICATION.md",
    "FINAL_ARCHITECTURE_DECISION.md": "docs/architecture/FINAL_ARCHITECTURE_DECISION.md",
    "ARCHITECTURE_IMPROVEMENT_PROPOSAL.md": "docs/architecture/ARCHITECTURE_IMPROVEMENT_PROPOSAL.md",
    "START_HERE.md": "docs/START_HERE.md",
    "TERMINOLOGY_CLARIFICATION.md": "docs/TERMINOLOGY_CLARIFICATION.md",
    "EXECUTION_FLOW_AND_CONFIG_GUIDE.md": "docs/EXECUTION_FLOW_AND_CONFIG_GUIDE.md",
    "IMPORT_GUIDE.md": "docs/IMPORT_GUIDE.md",
    "COMPLETE_SYSTEM_FLOW.md": "docs/COMPLETE_SYSTEM_FLOW.md",
    "DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md": "docs/development/DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md",
    "PACKAGE_REORGANIZATION_PROPOSAL.md": "docs/development/PACKAGE_REORGANIZATION_PROPOSAL.md",
    "analysis_results.txt": "docs/validation/analysis_results.txt",
}


def relative_link(from_file: Path, to_file: Path) -> str:
    return os.path.relpath(to_file, start=from_file.parent)


def is_url(text: str) -> bool:
    parsed = urlparse(text)
    return bool(parsed.scheme and parsed.netloc)


def update_file(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    original = text
    changed = False

    def repl(match: re.Match) -> str:
        nonlocal changed
        prefix = match.group(1)
        old_target = match.group(3)
        suffix = match.group(4)

        if is_url(old_target):
            return match.group(0)

        # Split off optional line reference (e.g. path:line or path:line-line)
        if ":" in old_target:
            path_part, _, line_ref = old_target.rpartition(":")
            line_ref = ":" + line_ref
        else:
            path_part = old_target
            line_ref = ""

        basename = path_part.split("/")[-1]
        if basename not in RELOCATIONS:
            return match.group(0)

        new_path = PROJECT_ROOT / RELOCATIONS[basename]
        new_link = relative_link(path, new_path)
        changed = True
        return f"{prefix}{new_link}{line_ref}{suffix}"

    text = re.sub(r"(\[([^\]]+)\]\()([^)]+)(\))", repl, text)

    if changed:
        path.write_text(text, encoding="utf-8")
        return 1
    return 0


def main() -> None:
    changed = 0
    for md_path in PROJECT_ROOT.rglob("*.md"):
        changed += update_file(md_path)
    print(f"Updated references in {changed} markdown files.")


if __name__ == "__main__":
    main()
