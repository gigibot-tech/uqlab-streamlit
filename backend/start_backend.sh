#!/bin/bash
# Start the FastAPI backend server (dev — reloads backend + src/)
# Usage: ./start_backend.sh

cd "$(dirname "$0")"

export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}$(cd .. && pwd)/src:$(pwd)"

echo "Starting FastAPI backend from $(pwd)..."
echo "PYTHONPATH includes: $(cd .. && pwd)/src"
echo "Backend will be available at http://0.0.0.0:8000"
echo ""

exec python run_dev.py
