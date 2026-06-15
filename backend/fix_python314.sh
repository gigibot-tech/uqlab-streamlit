#!/bin/bash
# Fix Python 3.14 SQLAlchemy compatibility issue
# This script upgrades SQLAlchemy to 2.0.36+ which supports Python 3.14

set -e  # Exit on error

echo "🔧 Fixing Python 3.14 SQLAlchemy compatibility..."
echo ""

# Navigate to backend directory
cd "$(dirname "$0")/backend"

echo "📦 Upgrading SQLAlchemy to 2.0.36+..."
uv pip install --upgrade "sqlalchemy>=2.0.36"

echo ""
echo "✅ SQLAlchemy upgraded successfully!"
echo ""

# Verify installation
echo "📋 Verifying installation..."
SQLALCHEMY_VERSION=$(uv pip list | grep -i "^sqlalchemy " | awk '{print $2}')
echo "   SQLAlchemy version: $SQLALCHEMY_VERSION"

if [[ "$SQLALCHEMY_VERSION" < "2.0.36" ]]; then
    echo ""
    echo "⚠️  Warning: SQLAlchemy version is still < 2.0.36"
    echo "   This may be due to SQLModel pinning an older version."
    echo "   Try: uv sync --upgrade"
    exit 1
fi

echo ""
echo "🎉 Fix complete! You can now start the backend:"
echo "   cd backend"
echo "   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

# Made with Bob
