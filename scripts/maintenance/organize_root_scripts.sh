#!/bin/bash
# Script to organize root-level scripts into appropriate directories

set -e

# Resolve the project root from this script's location (scripts/maintenance).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

# Prefer git mv to preserve history, fall back to plain mv.
if [ -d "$PROJECT_ROOT/.git" ] && command -v git >/dev/null 2>&1; then
    MV() { git mv "$@"; }
else
    MV() { mv "$@"; }
fi

echo "🗂️  Organizing root-level scripts..."

# Create scripts directory if it doesn't exist
mkdir -p scripts/maintenance
mkdir -p scripts/fixes
mkdir -p scripts/diagnostics
mkdir -p scripts/analysis
mkdir -p scripts/deployment

# Move test scripts to tests/
echo "📝 Moving test scripts to tests/..."
MV test_minimal.py tests/ 2>/dev/null || true
MV test_resnet_modes_standalone.py tests/ 2>/dev/null || true
MV test_resnet_modes.py tests/ 2>/dev/null || true
MV test_training_data_inspection.py tests/ 2>/dev/null || true
MV test_uncertainty_metrics.py tests/ 2>/dev/null || true

# Move startup / deployment shell scripts to scripts/deployment/
echo "🚀 Moving startup scripts to scripts/deployment/..."
MV start.sh scripts/deployment/ 2>/dev/null || true
MV start-with-minio.sh scripts/deployment/ 2>/dev/null || true

# Move analysis scripts to scripts/analysis/
echo "📊 Moving analysis scripts to scripts/analysis/..."
MV analyze_md_files.py scripts/analysis/ 2>/dev/null || true

# Move maintenance shell scripts to scripts/maintenance/
echo "🔧 Moving shell scripts to scripts/maintenance/..."
MV cleanup_root_level.sh scripts/maintenance/ 2>/dev/null || true
MV cleanup.sh scripts/maintenance/ 2>/dev/null || true
MV fix_missing_returns.sh scripts/fixes/ 2>/dev/null || true
MV fix_python314_complete.sh scripts/fixes/ 2>/dev/null || true
MV quick_test.sh scripts/maintenance/ 2>/dev/null || true
MV rename_to_uqlab.sh scripts/maintenance/ 2>/dev/null || true
MV reorganize_folders.sh scripts/maintenance/ 2>/dev/null || true

# Move fix/diagnostic Python scripts to scripts/
echo "🔍 Moving diagnostic and fix scripts to scripts/..."
MV diagnose_rerun.py scripts/diagnostics/ 2>/dev/null || true
MV diagnose_startup.py scripts/diagnostics/ 2>/dev/null || true
MV fix_all_reruns.py scripts/fixes/ 2>/dev/null || true
MV fix_imports.py scripts/fixes/ 2>/dev/null || true
MV fix_numbered_imports.py scripts/fixes/ 2>/dev/null || true
MV fix_shim_imports.py scripts/fixes/ 2>/dev/null || true
MV remove_ui_debug.py scripts/maintenance/ 2>/dev/null || true
MV remove_walaris_references.py scripts/maintenance/ 2>/dev/null || true
MV update_imports.py scripts/fixes/ 2>/dev/null || true
MV consolidate_uq_classification.py scripts/maintenance/ 2>/dev/null || true

# Move run scripts to scripts/runners/
echo "🏃 Moving execution scripts to scripts/runners/..."
MV run_fast.py scripts/runners/ 2>/dev/null || true

echo "✅ Root-level script organization complete!"
echo ""
echo "📊 Summary:"
echo "  - Test scripts → tests/"
echo "  - Startup scripts → scripts/deployment/"
echo "  - Analysis scripts → scripts/analysis/"
echo "  - Shell scripts → scripts/maintenance/"
echo "  - Fix scripts → scripts/fixes/"
echo "  - Diagnostic scripts → scripts/diagnostics/"
echo "  - Maintenance scripts → scripts/maintenance/"
echo "  - Execution scripts → scripts/runners/"

# Made with Bob
