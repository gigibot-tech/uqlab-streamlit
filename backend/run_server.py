#!/usr/bin/env python3
"""Backend server entrypoint for development and production modes."""

from __future__ import annotations

import argparse
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Start the UQ Lab backend server.")
    parser.add_argument(
        "--prod",
        action="store_true",
        help="Run in production mode without auto-reload.",
    )
    args = parser.parse_args()

    import uvicorn

    from app.core.ml_bootstrap import ML_BOOTSTRAP_VERSION, verify_ml_stack

    verify_ml_stack()
    print(f"ML bootstrap v{ML_BOOTSTRAP_VERSION}")
    print(f"PYTHONPATH includes: {SRC_DIR}")
    print("Backend: http://0.0.0.0:8000")

    if args.prod:
        print("")
        print("Code changes will NOT trigger automatic restarts.")
        print("Running experiments will NOT be killed by server restarts.")
        print("")
        print("To apply code changes, manually stop (Ctrl+C) and restart the server.")
        print("=" * 70)
        print("")
        uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
    else:
        print("Watching backend/app, src/, and scripts/ for changes.")
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


if __name__ == "__main__":
    main()
