#!/bin/bash
set -e

echo "🚀 Starting folder reorganization..."

# Step 1: Create new directory structure
echo "📁 Creating new directories..."
mkdir -p src/uqlab/4_evaluation/legacy/{triage,metrics,experiments}
mkdir -p src/uqlab/2_models/backbones
mkdir -p src/uqlab/1_data/loaders
mkdir -p src/uqlab/4_evaluation/classification

# Step 2: Move files using git mv (preserves history)
echo "📦 Moving legacy code..."
git mv src/uqlab/triage/dualxda_axioms.py src/uqlab/4_evaluation/legacy/triage/ 2>/dev/null || true
git mv src/uqlab/legacy_metrics/*.py src/uqlab/4_evaluation/legacy/metrics/ 2>/dev/null || true
git mv src/uqlab/legacy_experiments/*.py src/uqlab/4_evaluation/legacy/experiments/ 2>/dev/null || true

echo "📦 Moving core modules..."
git mv src/uqlab/backbones/* src/uqlab/2_models/backbones/ 2>/dev/null || true
git mv src/uqlab/data_loaders/* src/uqlab/1_data/loaders/ 2>/dev/null || true
git mv src/uqlab/classification/* src/uqlab/4_evaluation/classification/ 2>/dev/null || true

# Step 3: Move documentation
echo "📄 Moving documentation..."
git mv LEGACY_FOLDER_REORGANIZATION.md src/uqlab/4_evaluation/legacy/README.md 2>/dev/null || true

# Step 4: Create __init__.py files
echo "📝 Creating __init__.py files..."
touch src/uqlab/4_evaluation/legacy/__init__.py
touch src/uqlab/4_evaluation/legacy/triage/__init__.py
touch src/uqlab/4_evaluation/legacy/metrics/__init__.py
touch src/uqlab/4_evaluation/legacy/experiments/__init__.py
[ ! -f src/uqlab/2_models/backbones/__init__.py ] && touch src/uqlab/2_models/backbones/__init__.py
[ ! -f src/uqlab/1_data/loaders/__init__.py ] && touch src/uqlab/1_data/loaders/__init__.py
[ ! -f src/uqlab/4_evaluation/classification/__init__.py ] && touch src/uqlab/4_evaluation/classification/__init__.py

echo "✅ Files moved successfully!"
