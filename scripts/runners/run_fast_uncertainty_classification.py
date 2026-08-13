#!/usr/bin/env python3
"""Backward-compatible CLI wrapper (deprecated).

The canonical implementation now lives in ``uqlab_core.cli.run_fast_uncertainty``
and is exposed as the ``uqlab-run`` console script after installing the workspace.

Keep this shim so existing documentation, examples, and the FastAPI bootstrap
continue to find a runnable file at the historic path.
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

if __name__ == "__main__":
    warnings.warn(
        "scripts/runners/run_fast_uncertainty_classification.py is deprecated. "
        "Use `uqlab-run` or `python -m uqlab_core.cli.run_fast_uncertainty` instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    _ROOT = Path(__file__).resolve().parents[2]
    _SRC = _ROOT / "src"
    for _p in (_SRC, _ROOT):
        _s = str(_p)
        if _s not in sys.path:
            sys.path.insert(0, _s)

    from uqlab_core.cli.run_fast_uncertainty import main

    main()
