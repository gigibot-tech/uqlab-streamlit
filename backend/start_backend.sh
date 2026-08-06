#!/bin/bash
# Start the FastAPI backend server in DEVELOPMENT MODE (with auto-reload)
#
# Usage: ./start_backend.sh
#
# See BACKEND_MODES.md — use ./start_backend_prod.sh while experiments are running.

set -euo pipefail
cd "$(dirname "$0")"
# shellcheck source=scripts/_python.sh
source ./scripts/_python.sh

echo "Starting FastAPI backend from $(pwd)..."
echo "Python: ${PYTHON}"
echo "PYTHONPATH includes: $(cd .. && pwd)/src"
echo "Backend will be available at http://0.0.0.0:8000"
echo ""

"${PYTHON}" -c "from app.core.ml_bootstrap import ML_BOOTSTRAP_VERSION, verify_ml_stack; verify_ml_stack(); print(f'Preflight OK (bootstrap v{ML_BOOTSTRAP_VERSION})')"

exec "${PYTHON}" scripts/run_dev.py
