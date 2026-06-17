"""Ensure ``uqlab`` and training shims are importable for the FastAPI process."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# uqlab-streamlit/ (parent of backend/)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = PROJECT_ROOT / "src"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"


def ensure_ml_paths(*, scripts_dir: Path | None = None) -> Path:
    """
    Put repo ``src/``, project root, and ``scripts/`` on ``sys.path``.

    Works when ``uqlab`` is not pip-installed (e.g. dev uses repo root ``.venv``).
    When ``uqlab`` is installed (``uv sync`` in ``backend/``), this is a no-op for imports.
    """
    paths = [SRC_DIR, PROJECT_ROOT]
    if scripts_dir is not None:
        paths.insert(0, scripts_dir)
    elif SCRIPTS_DIR.exists():
        paths.insert(0, SCRIPTS_DIR)

    added: list[str] = []
    for path in paths:
        entry = str(path.resolve())
        if path.exists() and entry not in sys.path:
            sys.path.insert(0, entry)
            added.append(entry)

    if added:
        logger.debug("ML bootstrap added to sys.path: %s", added)
    return PROJECT_ROOT
