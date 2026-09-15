#!/bin/bash

# UQLab-Streamlit — sync deps and run streamlit_app_progressive.py

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$SCRIPT_DIR/.venv"
FRONTEND_PORT="${FRONTEND_PORT:-8501}"

echo -e "${GREEN}🚀 Starting UQLab-Streamlit (progressive app)…${NC}"
echo ""

cd "$SCRIPT_DIR"

if ! command -v uv >/dev/null 2>&1; then
    echo -e "${RED}❌ uv not found${NC}"
    echo -e "${YELLOW}   Install: curl -LsSf https://astral.sh/uv/install.sh | sh${NC}"
    exit 1
fi

echo -e "${YELLOW}📦 Syncing dependencies (uv sync)…${NC}"
uv sync
echo -e "${GREEN}✅ Dependencies synced${NC}"
echo ""

PYTHON="$VENV/bin/python3"
if [ ! -x "$PYTHON" ]; then
    echo -e "${RED}❌ Missing $PYTHON — uv sync failed?${NC}"
    exit 1
fi

echo -e "${GREEN}✅ $($PYTHON --version) — $VENV${NC}"

# Preflight: catch missing/broken installs before Streamlit's opaque traceback.
if ! "$PYTHON" -c "
import torch, streamlit, sklearn, scipy, pydantic, matplotlib, plotly, pandas, yaml
print('deps ok: torch', torch.__version__, '| streamlit', streamlit.__version__)
" 2>/dev/null; then
    echo -e "${RED}❌ Core packages missing or broken in .venv${NC}"
    echo -e "${YELLOW}   Try: rm -rf .venv && uv sync${NC}"
    exit 1
fi

export PYTHONPATH="$SCRIPT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

echo ""
echo -e "${YELLOW}🔧 http://localhost:${FRONTEND_PORT}${NC}"
echo -e "${YELLOW}   PYTHONPATH=$SCRIPT_DIR/src${NC}"
echo ""
echo -e "${YELLOW}▶ streamlit run streamlit_app_progressive.py${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop.${NC}"
echo ""

# python -m streamlit avoids broken #! shebangs if .venv was copied from elsewhere.
exec "$PYTHON" -m streamlit run streamlit_app_progressive.py --server.port "${FRONTEND_PORT}"
