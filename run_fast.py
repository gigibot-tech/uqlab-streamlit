#!/usr/bin/env python3
"""
Convenience launcher from repo root.

Canonical implementation: ``scripts/run_fast_uncertainty_classification.py``
(used by the FastAPI backend, validation sweeps, and examples).
"""

from __future__ import annotations

import runpy
from pathlib import Path

_SCRIPT = (
    Path(__file__).resolve().parent / "scripts" / "run_fast_uncertainty_classification.py"
)

if __name__ == "__main__":
    runpy.run_path(str(_SCRIPT), run_name="__main__")
