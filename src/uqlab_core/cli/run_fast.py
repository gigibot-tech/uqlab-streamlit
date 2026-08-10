#!/usr/bin/env python3
"""Convenience launcher that delegates to the canonical CLI runner."""

from __future__ import annotations

import sys
from pathlib import Path

# Make ``uqlab_core`` importable when this script is run directly from the repo.
_repo_src = Path(__file__).resolve().parents[2]
if str(_repo_src) not in sys.path:
    sys.path.insert(0, str(_repo_src))

from uqlab_core.cli.run_fast_uncertainty_classification import main

if __name__ == "__main__":
    main()
