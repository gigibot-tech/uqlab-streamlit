#!/bin/bash
# Start the FastAPI backend in PRODUCTION MODE (no auto-reload).
#
# Usage: ./start_backend_prod.sh

set -euo pipefail
cd "$(dirname "$0")"
# shellcheck source=_python.sh
source ./_python.sh

echo "Starting FastAPI backend in PRODUCTION MODE from $(pwd)..."
echo "Python: ${PYTHON}"
echo "PYTHONPATH includes: $(cd .. && pwd)/src"
echo "Backend will be available at http://0.0.0.0:8000"
echo ""

"${PYTHON}" -c "from app.core.ml_bootstrap import ML_BOOTSTRAP_VERSION, verify_ml_stack; verify_ml_stack(); print(f'Preflight OK (bootstrap v{ML_BOOTSTRAP_VERSION})')"

exec "${PYTHON}" run_prod.py
