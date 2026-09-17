"""Add repo ``src/`` to ``sys.path`` so ``import uqlab`` works from notebooks."""

from __future__ import annotations

import sys
from pathlib import Path


def candidate_repo_roots() -> list[Path]:
    seen: set[Path] = set()
    roots: list[Path] = []
    for base in (Path.cwd(), *Path.cwd().parents):
        for candidate in (
            base,
            base / "uqlab-streamlit",
            base / "four-region-benchmark",
        ):
            resolved = candidate.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            roots.append(resolved)
    return roots


def ensure_uqlab_path() -> Path:
    """Ensure ``src/`` is on ``sys.path`` and return the repository root."""
    for base in candidate_repo_roots():
        src = base / "src"
        if (src / "uqlab").is_dir():
            src_s = str(src)
            if src_s not in sys.path:
                sys.path.insert(0, src_s)
            return base
    raise ModuleNotFoundError(
        "Could not find src/uqlab. Open the repo in Jupyter (uqlab-streamlit or notebooks/)."
    )
