#!/bin/bash
#
# Run Streamlit Dashboard
# This script starts the Streamlit frontend that connects to the FastAPI backend
#

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting Streamlit Dashboard...${NC}"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${BLUE}Creating virtual environment...${NC}"
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install requirements (Streamlit UI + editable walaris package)
echo -e "${BLUE}Installing dependencies...${NC}"
pip install -q -r streamlit_requirements.txt
pip install -q -e ".[streamlit]"

# Set API URL (default to localhost, can be overridden)
export API_URL="${API_URL:-http://localhost:8000}"

echo -e "${GREEN}✓ Dependencies installed${NC}"
echo -e "${BLUE}API URL: ${API_URL}${NC}"
echo -e "${BLUE}Starting Streamlit on http://localhost:8501${NC}"
echo ""

# Run streamlit
streamlit run streamlit_app.py

# Made with Bob
