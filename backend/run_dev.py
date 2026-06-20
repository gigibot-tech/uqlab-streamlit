#!/usr/bin/env python3
"""Dev server entrypoint — watches backend *and* ../src for hot reload."""

from __future__ import annotations

import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
SRC_DIR = PROJECT_ROOT / "src"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

os.chdir(BACKEND_DIR)
for entry in (str(SRC_DIR), str(BACKEND_DIR)):
    if entry not in sys.path:
        sys.path.insert(0, entry)

if __name__ == "__main__":
    import uvicorn

    print(f"PYTHONPATH includes: {SRC_DIR}")
    print("Watching backend/app, src/, and scripts/ for changes.")
    print("Backend: http://0.0.0.0:8000")
    reload_dirs = [str(BACKEND_DIR / "app"), str(SRC_DIR)]
    if SCRIPTS_DIR.exists():
        reload_dirs.append(str(SCRIPTS_DIR))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=reload_dirs,
    )
