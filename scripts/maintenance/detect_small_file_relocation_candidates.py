#!/usr/bin/env python3
"""Find root folders whose files are all below a LoC threshold.

Candidate folders are prime candidates for relocation into a more specific
package or for consolidation, because they contain only small files.

Usage:
    uv run python scripts/maintenance/detect_small_file_relocation_candidates.py
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
THRESHOLDS = (200, 300)

# Dirs that are tooling/runtime artifacts, not source candidates.
SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "build",
    "dist",
    ".cursor",
    ".bob",
    ".vscode",
    "docs/archive",
    "dead_code",
}

# Non-text files we never want to count (or that are huge lockfiles).
SKIP_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".pdf",
    ".lock",
    ".pyc",
    ".pyo",
    ".ds_store",
    ".egg-info",
    ".sqlite",
    ".db",
}


def _is_text(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            chunk = f.read(8192)
            if b"\x00" in chunk:
                return False
            chunk.decode("utf-8")
        return True
    except (UnicodeDecodeError, OSError):
        return False


def _count_lines(path: Path) -> int:
    with path.open("rb") as f:
        return sum(1 for _ in f)


def _analyze(root: Path) -> dict:
    files = []
    for path in root.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        rel = path.relative_to(root)
        parts = rel.parts
        if any(part.startswith(".") for part in parts):
            continue
        if any(part in SKIP_DIRS for part in parts):
            continue
        if path.suffix.lower() in SKIP_EXTENSIONS:
            continue
        if not _is_text(path):
            continue
        loc = _count_lines(path)
        files.append({"path": rel, "loc": loc})
    if not files:
        return {"max": 0, "count": 0, "files": []}
    files.sort(key=lambda x: x["loc"])
    return {"max": files[-1]["loc"], "count": len(files), "files": files}


def _proposed_home(name: str) -> str:
    if name == "configs":
        return "src/uqlab_core/configs (package data) or backend/app/configs"
    if name == "data":
        return "Keep as runtime data root; remove .gitkeep if not needed"
    if name == "uqlab-flask":
        return "backend/app/legacy_wizard or archive (depends on uqlab-flask executor)"
    if name == "scripts":
        return "Group by purpose per docs/archive/SCRIPTS_REORGANIZATION_PLAN.md"
    return "Review"


def main() -> None:
    candidates = []
    for entry in sorted(REPO_ROOT.iterdir()):
        if not entry.is_dir() or entry.is_symlink() or entry.name.startswith("."):
            continue
        if entry.name in SKIP_DIRS:
            continue
        info = _analyze(entry)
        if info["count"] == 0:
            continue
        thresholds_met = [t for t in THRESHOLDS if info["max"] <= t]
        if thresholds_met:
            candidates.append((entry, info, thresholds_met))

    print("# Small File Relocation Candidates")
    print()
    print("Scanning root directories for folders where every file is below a LoC threshold.")
    print()
    print("| Root Folder | Files | Max LoC | Thresholds Met | Proposed Home |")
    print("|-------------|-------|---------|----------------|---------------|")
    for entry, info, thresholds_met in candidates:
        print(
            f"| {entry.name} | {info['count']} | {info['max']} | "
            f"{', '.join(map(str, thresholds_met))} | {_proposed_home(entry.name)} |"
        )
    print()
    print("## Details")
    print()
    for entry, info, thresholds_met in candidates:
        print(f"### {entry.name}")
        print()
        print(f"- Total files: {info['count']}")
        print(f"- Max LoC: {info['max']}")
        print(f"- Qualifies under thresholds: {', '.join(map(str, thresholds_met))}")
        print()
        print("| File | LoC |")
        print("|------|-----|")
        for f in info["files"]:
            print(f"| {f['path']} | {f['loc']} |")
        print()


if __name__ == "__main__":
    main()
