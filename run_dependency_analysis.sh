#!/bin/bash
# Quick start script for dependency analysis tool

set -e

echo "🔍 Python Dependency Analysis Tool"
echo "===================================="
echo ""

# Check if dependencies.json exists
if [ ! -f "dependencies.json" ]; then
    echo "📊 Running dependency analyzer..."
    python3 analyze_dependencies.py --directory . --output dependencies.json
    echo ""
else
    echo "✓ Found existing dependencies.json"
    echo ""
    read -p "Re-analyze dependencies? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "📊 Re-analyzing dependencies..."
        python3 analyze_dependencies.py --directory . --output dependencies.json
        echo ""
    fi
fi

echo "🚀 Launching Streamlit visualizer..."
echo "   Open your browser to: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

streamlit run dependency_visualizer.py

# Made with Bob
