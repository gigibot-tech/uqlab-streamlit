#!/bin/bash
# Organize small root-level files into appropriate subdirectories.
# Run with --dry-run to preview changes without applying them.
#
# Files under ~300 lines are candidates for relocation; files that are
# referenced by Docker/CI/entrypoints are left in place unless the references
# are updated first.

set -euo pipefail

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "🔍 DRY RUN — no files will be moved"
fi

run_cmd() {
    if $DRY_RUN; then
        echo "   [dry-run] $*"
    else
        "$@"
    fi
}

echo "🗂️  Organizing root-level files..."

# Analysis artifacts (small data / helper files)
echo "📊 Organizing analysis artifacts..."
run_cmd mkdir -p docs/validation
run_cmd mv -f analysis_results.txt docs/validation/ 2>/dev/null || true
run_cmd mkdir -p scripts/analysis
run_cmd mv -f analyze_md_files.py scripts/analysis/ 2>/dev/null || true

# Maintenance / diagnostic scripts that do not need to live in root
echo "🔧 Organizing maintenance scripts..."
run_cmd mkdir -p scripts/maintenance
run_cmd mv -f organize_root_scripts.sh scripts/maintenance/organize_root_files.sh 2>/dev/null || true

# Startup scripts are intentionally left in root because they are referenced by
# backend/Dockerfile, backend/scripts/entrypoint.sh, and deployment scripts.
# If you want to move them, update those references first.
echo "⚠️  Skipping startup scripts (start.sh, start-with-minio.sh) — referenced by Docker/CI"

# Documentation files under 300 lines that belong under docs/:
#
#   ARCHITECTURE_CLARIFICATION.md          -> docs/architecture/
#   ARCHITECTURE_IMPROVEMENT_PROPOSAL.md   -> docs/architecture/
#   COMPLETE_SYSTEM_FLOW.md                -> docs/architecture/
#   DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md -> docs/architecture/
#   EXECUTION_FLOW_AND_CONFIG_GUIDE.md     -> docs/architecture/
#   FINAL_ARCHITECTURE_DECISION.md         -> docs/architecture/
#   IMPORT_GUIDE.md                        -> docs/development/
#   PACKAGE_REORGANIZATION_PROPOSAL.md     -> docs/architecture/
#   TERMINOLOGY_CLARIFICATION.md           -> docs/architecture/
#
# These are NOT moved automatically because README.md and other docs link to
# them by relative path. Move them manually and update references, or run the
# moves below after confirming links are fixed.
echo "📚 Documentation reorganization requires manual reference updates:"
echo "   See docs/development/ROOT_FILE_REORGANIZATION.md for the full plan."

if ! $DRY_RUN; then
    echo ""
    echo "✅ Root-level organization complete!"
fi
