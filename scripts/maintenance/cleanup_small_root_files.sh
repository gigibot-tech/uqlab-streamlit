#!/bin/bash
# Cleanup small root-level files (< 300 LoC) that belong elsewhere.
# Preserves git history via git mv.

set -euo pipefail

cd "$(dirname "$0")/../.."

echo "🧹 Cleaning up small root-level files..."

# --- Junk / orphaned files ---------------------------------------------------
echo "🗑️  Removing orphaned/junk files..."
rm -f .DS_Store package-lock.json

# --- Archive deprecated / generated files -------------------------------------
echo "📦 Archiving deprecated and generated files..."
mkdir -p archive
git mv streamlit_requirements.txt archive/ 2>/dev/null || true
git mv analysis_results.txt archive/ 2>/dev/null || true

# --- Scripts -----------------------------------------------------------------
echo "🔧 Moving utility scripts to scripts/maintenance/..."
git mv organize_root_scripts.sh scripts/maintenance/ 2>/dev/null || true
git mv analyze_md_files.py scripts/maintenance/ 2>/dev/null || true

echo "🚀 Moving startup scripts to scripts/deployment/..."
git mv start.sh scripts/deployment/ 2>/dev/null || true
git mv start-with-minio.sh scripts/deployment/ 2>/dev/null || true

# --- Documentation -----------------------------------------------------------
echo "📄 Moving architecture docs to docs/architecture/..."
git mv ARCHITECTURE_CLARIFICATION.md docs/architecture/ 2>/dev/null || true
git mv FINAL_ARCHITECTURE_DECISION.md docs/architecture/ 2>/dev/null || true

echo "📄 Moving development/proposal docs to docs/development/..."
git mv EXECUTION_FLOW_AND_CONFIG_GUIDE.md docs/development/ 2>/dev/null || true
git mv DEPENDENCY_ANALYSIS_AND_FINAL_RECOMMENDATION.md docs/development/ 2>/dev/null || true
git mv PACKAGE_REORGANIZATION_PROPOSAL.md docs/development/ 2>/dev/null || true

echo "📄 Moving terminology doc to docs/..."
git mv TERMINOLOGY_CLARIFICATION.md docs/ 2>/dev/null || true
git mv START_HERE.md docs/ 2>/dev/null || true

# --- Update references -------------------------------------------------------
echo "📝 Updating internal references..."

# README.md links to moved docs
sed -i \
  -e 's|(EXECUTION_FLOW_AND_CONFIG_GUIDE.md)|(docs/development/EXECUTION_FLOW_AND_CONFIG_GUIDE.md)|g' \
  -e 's|(ARCHITECTURE_CLARIFICATION.md)|(docs/architecture/ARCHITECTURE_CLARIFICATION.md)|g' \
  -e 's|`START_HERE.md`|`docs/START_HERE.md`|g' \
  README.md

# MinIO docs reference the startup script
sed -i \
  -e 's|\./start-with-minio.sh|./scripts/deployment/start-with-minio.sh|g' \
  docs/setup/minio.md \
  docs/architecture/minio-storage.md

# Other docs that link to moved files
sed -i 's|(ARCHITECTURE_CLARIFICATION.md)|(../architecture/ARCHITECTURE_CLARIFICATION.md)|g' docs/development/EXECUTION_FLOW_AND_CONFIG_GUIDE.md
sed -i 's|(ARCHITECTURE_CLARIFICATION.md)|(docs/architecture/ARCHITECTURE_CLARIFICATION.md)|g' COMPLETE_SYSTEM_FLOW.md
sed -i 's|../../START_HERE.md|../START_HERE.md|g' docs/features/workflow-config.md
sed -i 's|docs/architecture/PACKAGE_REDESIGN.md|architecture/PACKAGE_REDESIGN.md|g' docs/TERMINOLOGY_CLARIFICATION.md
sed -i 's|FINAL_ARCHITECTURE_DECISION\.md|architecture/FINAL_ARCHITECTURE_DECISION.md|g' docs/TERMINOLOGY_CLARIFICATION.md

# Code comments referencing moved docs
sed -i 's|See START_HERE.md|See docs/START_HERE.md|g' streamlit_app_progressive.py
sed -i 's|See \*\*START_HERE\.md\*\*|See **docs/START_HERE.md**|g' streamlit_app_progressive.py

# Archived files
sed -i 's|#   \./start.sh|#   ./scripts/deployment/start.sh|g' archive/streamlit_requirements.txt

echo "✅ Root-level small-file cleanup complete!"
