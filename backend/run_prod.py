#!/usr/bin/env python3
"""Production server entrypoint — NO auto-reload for stable long-running experiments."""

from __future__ import annotations

import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
SRC_DIR = PROJECT_ROOT / "src"

os.chdir(BACKEND_DIR)
for entry in (str(SRC_DIR), str(BACKEND_DIR)):
    if entry not in sys.path:
        sys.path.insert(0, entry)

if __name__ == "__main__":
    import uvicorn

    from app.core.ml_bootstrap import ML_BOOTSTRAP_VERSION, verify_ml_stack

    verify_ml_stack()
    print(f"ML bootstrap v{ML_BOOTSTRAP_VERSION}")
    print(f"PYTHONPATH includes: {SRC_DIR}")
    print("Backend: http://0.0.0.0:8000")
    print("")
    print("⚠️  Code changes will NOT trigger automatic restarts.")
    print("✅ Running experiments will NOT be killed by server restarts.")
    print("")
    print("To apply code changes, manually stop (Ctrl+C) and restart the server.")
    print("=" * 70)
    print("")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # CRITICAL: No reload in production mode
    )

# Made with Bob
