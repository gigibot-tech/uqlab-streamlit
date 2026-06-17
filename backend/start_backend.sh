#!/bin/bash
# Start the FastAPI backend server
# Usage: ./start_backend.sh

cd "$(dirname "$0")"

echo "Starting FastAPI backend from $(pwd)..."
echo "Backend will be available at http://0.0.0.0:8000"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Made with Bob
