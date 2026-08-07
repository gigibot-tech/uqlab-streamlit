#!/bin/bash
# Script to organize root-level scripts into appropriate directories

set -e

# Resolve project root from scripts/maintenance/
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🗂️  Organizing root-level scripts in $PROJECT_ROOT..."

# Create scripts directory if it doesn't exist
mkdir -p "$PROJECT_ROOT/scripts/maintenance"
mkdir -p "$PROJECT_ROOT/scripts/fixes"
mkdir -p "$PROJECT_ROOT/scripts/diagnostics"

# Move test scripts to tests/
echo "📝 Moving test scripts to tests/..."
mv "$PROJECT_ROOT/test_minimal.py" "$PROJECT_ROOT/tests/" 2>/dev/null || true
mv "$PROJECT_ROOT/test_resnet_modes_standalone.py" "$PROJECT_ROOT/tests/" 2>/dev/null || true
mv "$PROJECT_ROOT/test_resnet_modes.py" "$PROJECT_ROOT/tests/" 2>/dev/null || true
mv "$PROJECT_ROOT/test_training_data_inspection.py" "$PROJECT_ROOT/tests/" 2>/dev/null || true
mv "$PROJECT_ROOT/test_uncertainty_metrics.py" "$PROJECT_ROOT/tests/" 2>/dev/null || true

# Move shell scripts to scripts/
echo "🔧 Moving shell scripts to scripts/..."
mv "$PROJECT_ROOT/cleanup_root_level.sh" "$PROJECT_ROOT/scripts/maintenance/" 2>/dev/null || true
mv "$PROJECT_ROOT/cleanup.sh" "$PROJECT_ROOT/scripts/maintenance/" 2>/dev/null || true
mv "$PROJECT_ROOT/fix_missing_returns.sh" "$PROJECT_ROOT/scripts/fixes/" 2>/dev/null || true
mv "$PROJECT_ROOT/fix_python314_complete.sh" "$PROJECT_ROOT/scripts/fixes/" 2>/dev/null || true
mv "$PROJECT_ROOT/quick_test.sh" "$PROJECT_ROOT/scripts/" 2>/dev/null || true
mv "$PROJECT_ROOT/rename_to_uqlab.sh" "$PROJECT_ROOT/scripts/maintenance/" 2>/dev/null || true
mv "$PROJECT_ROOT/reorganize_folders.sh" "$PROJECT_ROOT/scripts/maintenance/" 2>/dev/null || true
mv "$PROJECT_ROOT/start.sh" "$PROJECT_ROOT/scripts/" 2>/dev/null || true
mv "$PROJECT_ROOT/start-with-minio.sh" "$PROJECT_ROOT/scripts/" 2>/dev/null || true

# Move fix/diagnostic Python scripts to scripts/
echo "🔍 Moving diagnostic and fix scripts to scripts/..."
mv "$PROJECT_ROOT/diagnose_rerun.py" "$PROJECT_ROOT/scripts/diagnostics/" 2>/dev/null || true
mv "$PROJECT_ROOT/diagnose_startup.py" "$PROJECT_ROOT/scripts/diagnostics/" 2>/dev/null || true
mv "$PROJECT_ROOT/fix_all_reruns.py" "$PROJECT_ROOT/scripts/fixes/" 2>/dev/null || true
mv "$PROJECT_ROOT/fix_imports.py" "$PROJECT_ROOT/scripts/fixes/" 2>/dev/null || true
mv "$PROJECT_ROOT/fix_numbered_imports.py" "$PROJECT_ROOT/scripts/fixes/" 2>/dev/null || true
mv "$PROJECT_ROOT/fix_shim_imports.py" "$PROJECT_ROOT/scripts/fixes/" 2>/dev/null || true
mv "$PROJECT_ROOT/remove_ui_debug.py" "$PROJECT_ROOT/scripts/maintenance/" 2>/dev/null || true
mv "$PROJECT_ROOT/remove_walaris_references.py" "$PROJECT_ROOT/scripts/maintenance/" 2>/dev/null || true
mv "$PROJECT_ROOT/update_imports.py" "$PROJECT_ROOT/scripts/fixes/" 2>/dev/null || true
mv "$PROJECT_ROOT/consolidate_uq_classification.py" "$PROJECT_ROOT/scripts/maintenance/" 2>/dev/null || true
mv "$PROJECT_ROOT/analyze_md_files.py" "$PROJECT_ROOT/scripts/maintenance/" 2>/dev/null || true

# Move run_fast.py to scripts/
echo "🚀 Moving execution scripts to scripts/..."
mv "$PROJECT_ROOT/run_fast.py" "$PROJECT_ROOT/scripts/" 2>/dev/null || true

echo "✅ Root-level script organization complete!"
echo ""
echo "📊 Summary:"
echo "  - Test scripts → tests/"
echo "  - Shell scripts → scripts/ and scripts/maintenance/"
echo "  - Fix scripts → scripts/fixes/"
echo "  - Diagnostic scripts → scripts/diagnostics/"
echo "  - Maintenance scripts → scripts/maintenance/"

# Made with Bob
