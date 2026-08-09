"""Entry point for `python -m uqlab_flask`."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SRC = ROOT / "src"
FLASK_PKG = Path(__file__).resolve().parent
for p in (str(SRC), str(ROOT), str(FLASK_PKG)):
    if p not in sys.path:
        sys.path.insert(0, p)

from uqlab_flask.app import create_app

if __name__ == "__main__":
    # use_reloader=False — watchdog reload kills in-flight training threads mid-sweep.
    create_app().run(debug=True, use_reloader=False, port=5001)
