#!/usr/bin/env python3
"""Convenience launcher from repo root.

Canonical implementation: ``uqlab_core.cli.run_fast_uncertainty`` (exposed as
``uqlab-run`` after installing the workspace).
"""

from __future__ import annotations

import sys
from pathlib import Path

if __name__ == "__main__":
    _ROOT = Path(__file__).resolve().parent
    _SRC = _ROOT / "src"
    for _p in (_SRC, _ROOT):
        _s = str(_p)
        if _s not in sys.path:
            sys.path.insert(0, _s)

    from uqlab_core.cli.run_fast_uncertainty import main

    main()
