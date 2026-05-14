#!/bin/bash
set -e

echo "Starting Modular Streamlit Dashboard..."

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install -q -r streamlit_requirements.txt

export API_URL="${API_URL:-http://localhost:8000}"

cd streamlit_frontend
streamlit run app.py
