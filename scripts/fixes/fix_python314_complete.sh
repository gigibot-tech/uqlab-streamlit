#!/bin/bash
# Complete fix for Python 3.14 SQLAlchemy compatibility
# Recreates venv with Python 3.12 using UV

set -e  # Exit on error

echo "🔧 Fixing Python 3.14 SQLAlchemy compatibility..."
echo ""
echo "Current situation:"
echo "  - Python 3.14.3 is too new for SQLAlchemy"
echo "  - Even SQLAlchemy 2.0.50 doesn't fully support Python 3.14"
echo "  - Solution: Use Python 3.12 with UV"
echo ""

# Navigate to project root
cd "$(dirname "$0")/.."

echo "📦 Step 1: Installing Python 3.12 via UV..."
uv python install 3.12

echo ""
echo "🗑️  Step 2: Removing old venv..."
rm -rf .venv

echo ""
echo "🆕 Step 3: Creating new venv with Python 3.12..."
uv venv --python 3.12

echo ""
echo "✅ Step 4: Activating new venv..."
source .venv/bin/activate

echo ""
echo "📦 Step 5: Installing backend dependencies..."
cd walaris-cen/backend
uv pip install -e .

echo ""
echo "📦 Step 6: Installing streamlit dependencies..."
cd ..
uv pip install streamlit plotly pandas requests pyyaml

echo ""
echo "📦 Step 7: Installing uqlab package..."
uv pip install -e .

echo ""
echo "✅ Installation complete!"
echo ""
echo "📋 Verifying installation..."
python --version
echo ""
uv pip list | grep -i sqlalchemy

echo ""
echo "🎉 Fix complete! Now you can:"
echo ""
echo "   # Terminal 1: Start backend"
echo "   cd walaris-cen/backend"
echo "   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "   # Terminal 2: Start progressive app"
echo "   cd walaris-cen"
echo "   streamlit run streamlit_app_progressive.py"

# Made with Bob
