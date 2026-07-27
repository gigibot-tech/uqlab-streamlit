#!/bin/bash
# Fix Validation System - Clear cache and check results
set -e

echo "=================================="
echo "VALIDATION SYSTEM FIX"
echo "=================================="
echo ""

# Step 1: Clear old cache
echo "Step 1: Clearing old feature cache..."
if [ -d "cache/fast_uncertainty_classification/features" ]; then
    echo "  Removing cache/fast_uncertainty_classification/features/"
    rm -rf cache/fast_uncertainty_classification/features/
    echo "  ✅ Cache cleared"
else
    echo "  ℹ️  No cache directory found (already clean)"
fi
echo ""

# Step 2: Clear old validation results
echo "Step 2: Clearing old validation results..."
if [ -d "results/validation" ]; then
    echo "  Removing results/validation/"
    rm -rf results/validation/
    echo "  ✅ Old results cleared"
else
    echo "  ℹ️  No validation results found"
fi
echo ""

# Step 3: Check one result file structure
echo "Step 3: Checking result file structure..."
echo "  Looking for any existing experiment results..."

# Find any results.pkl file
RESULT_FILE=$(find results -name "results.pkl" -type f 2>/dev/null | head -n 1)

if [ -n "$RESULT_FILE" ]; then
    echo "  Found: $RESULT_FILE"
    echo "  Checking contents with Python..."
    python3 << 'PYEOF'
import pickle
import sys
import os

result_file = os.environ.get('RESULT_FILE', '')
if not result_file or not os.path.exists(result_file):
    print("  ⚠️  No result file to check")
    sys.exit(0)

try:
    with open(result_file, 'rb') as f:
        data = pickle.load(f)
    
    print(f"  Keys in results file: {list(data.keys())}")
    
    if 'signal_table' in data:
        print("  ✅ signal_table is present")
        signal_table = data['signal_table']
        if hasattr(signal_table, 'columns'):
            print(f"     Columns: {list(signal_table.columns)}")
        elif isinstance(signal_table, dict):
            print(f"     Keys: {list(signal_table.keys())}")
    else:
        print("  ❌ signal_table is MISSING - this is the problem!")
        print("     Available keys:", list(data.keys()))
except Exception as e:
    print(f"  ⚠️  Error reading file: {e}")
PYEOF
else
    echo "  ℹ️  No existing result files found"
fi
echo ""

echo "=================================="
echo "FIX COMPLETE"
echo "=================================="
echo ""
echo "Next steps:"
echo "  1. Run: python scripts/run_validation_experiments.py --mode full"
echo "  2. Open notebooks: jupyter notebook notebooks/validation/"
echo ""

# Made with Bob
