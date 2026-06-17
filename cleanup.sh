#!/bin/bash
set -e

echo "🧹 Cleaning up..."

# Remove __pycache__ from git tracking
echo "📦 Removing __pycache__ from git..."
find src/uqlab -type d -name "__pycache__" | while read dir; do
    git rm -r --cached "$dir" 2>/dev/null || true
done

# Delete __pycache__ from filesystem
echo "🗑️  Deleting __pycache__ directories..."
find src/uqlab -type d -name "__pycache__" -exec rm -rf {} \; 2>/dev/null || true

# Remove empty old directories
echo "📁 Removing empty directories..."
rmdir src/uqlab/triage 2>/dev/null || echo "  triage/ already removed or not empty"
rmdir src/uqlab/legacy_metrics 2>/dev/null || echo "  legacy_metrics/ already removed or not empty"
rmdir src/uqlab/legacy_experiments 2>/dev/null || echo "  legacy_experiments/ already removed or not empty"
rmdir src/uqlab/backbones 2>/dev/null || echo "  backbones/ already removed or not empty"
rmdir src/uqlab/data_loaders 2>/dev/null || echo "  data_loaders/ already removed or not empty"
rmdir src/uqlab/classification 2>/dev/null || echo "  classification/ already removed or not empty"

echo "✅ Cleanup complete!"
