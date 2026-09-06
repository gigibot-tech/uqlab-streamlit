#!/bin/bash
# Script to organize root-level scripts into appropriate directories

set -e

echo "🗂️  Organizing root-level scripts..."

# Create scripts directory if it doesn't exist
mkdir -p scripts/maintenance
mkdir -p scripts/fixes
mkdir -p scripts/diagnostics

# Move test scripts to tests/
echo "📝 Moving test scripts to tests/..."
mv test_minimal.py tests/ 2>/dev/null || true
mv test_resnet_modes_standalone.py tests/ 2>/dev/null || true
mv test_resnet_modes.py tests/ 2>/dev/null || true
mv test_training_data_inspection.py tests/ 2>/dev/null || true
mv test_uncertainty_metrics.py tests/ 2>/dev/null || true

# Move shell scripts to scripts/
echo "🔧 Moving shell scripts to scripts/..."
mv cleanup_root_level.sh scripts/maintenance/ 2>/dev/null || true
mv cleanup.sh scripts/maintenance/ 2>/dev/null || true
mv fix_missing_returns.sh scripts/fixes/ 2>/dev/null || true
mv fix_python314_complete.sh scripts/fixes/ 2>/dev/null || true
mv quick_test.sh scripts/ 2>/dev/null || true
mv rename_to_uqlab.sh scripts/maintenance/ 2>/dev/null || true
mv reorganize_folders.sh scripts/maintenance/ 2>/dev/null || true

# Move fix/diagnostic Python scripts to scripts/
echo "🔍 Moving diagnostic and fix scripts to scripts/..."
mv diagnose_rerun.py scripts/diagnostics/ 2>/dev/null || true
mv diagnose_startup.py scripts/diagnostics/ 2>/dev/null || true
mv fix_all_reruns.py scripts/fixes/ 2>/dev/null || true
mv fix_imports.py scripts/fixes/ 2>/dev/null || true
mv fix_numbered_imports.py scripts/fixes/ 2>/dev/null || true
mv fix_shim_imports.py scripts/fixes/ 2>/dev/null || true
mv remove_ui_debug.py scripts/maintenance/ 2>/dev/null || true
mv remove_walaris_references.py scripts/maintenance/ 2>/dev/null || true
mv update_imports.py scripts/fixes/ 2>/dev/null || true
mv consolidate_uq_classification.py scripts/maintenance/ 2>/dev/null || true

# Move run_fast.py to scripts/
echo "🚀 Moving execution scripts to scripts/..."
mv run_fast.py scripts/ 2>/dev/null || true

echo "✅ Root-level script organization complete!"
echo ""
echo "📊 Summary:"
echo "  - Test scripts → tests/"
echo "  - Shell scripts → scripts/ and scripts/maintenance/"
echo "  - Fix scripts → scripts/fixes/"
echo "  - Diagnostic scripts → scripts/diagnostics/"
echo "  - Maintenance scripts → scripts/maintenance/"

# Made with Bob
