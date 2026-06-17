#!/bin/bash
# Root Level Cleanup Script
# Organizes files according to ROOT_LEVEL_CLEANUP_ANALYSIS.md

set -e
cd "$(dirname "$0")"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "🧹 Starting Root Level Cleanup"
echo "=============================="

# Phase 1: Archive Old Documentation
echo -e "\n${BLUE}Phase 1: Archiving old documentation...${NC}"
mkdir -p archive/old_docs
mv MLOPS_*.md archive/old_docs/ 2>/dev/null || true
mv COMPLETE_CODEBASE_*.md archive/old_docs/ 2>/dev/null || true
mv CODEBASE_CONSOLIDATION_*.md archive/old_docs/ 2>/dev/null || true
mv CONSOLIDATION_*.md archive/old_docs/ 2>/dev/null || true
mv FINAL_CONSOLIDATION_*.md archive/old_docs/ 2>/dev/null || true
mv UI_COMPONENTS_*.md archive/old_docs/ 2>/dev/null || true
mv STREAMLIT_REDESIGN_*.md archive/old_docs/ 2>/dev/null || true
mv STREAMLIT_PROGRESSIVE_*.md archive/old_docs/ 2>/dev/null || true
mv EXPERIMENT_TRACKER_*.md archive/old_docs/ 2>/dev/null || true
mv DEPENDENCY_ANALYSIS_*.md archive/old_docs/ 2>/dev/null || true
echo -e "${GREEN}✓ Old documentation archived${NC}"

# Phase 2: Move Notebooks
echo -e "\n${BLUE}Phase 2: Moving notebooks...${NC}"
mv resnet_baseline_experiment.ipynb notebooks/ 2>/dev/null || true
mv uncertainty_visualization_demo.ipynb notebooks/ 2>/dev/null || true
mv uncertainty_viz_3class.ipynb notebooks/ 2>/dev/null || true
mv watsonx_deployment_experiment.ipynb notebooks/ 2>/dev/null || true
echo -e "${GREEN}✓ Notebooks moved${NC}"

# Phase 3: Move Utility Scripts
echo -e "\n${BLUE}Phase 3: Moving utility scripts...${NC}"
mkdir -p scripts/utils
mv analyze_dependencies.py scripts/utils/ 2>/dev/null || true
mv dependency_visualizer.py scripts/utils/ 2>/dev/null || true
mv visualize_7x2_structure.py scripts/utils/ 2>/dev/null || true
mv run_dependency_analysis.sh scripts/utils/ 2>/dev/null || true
echo -e "${GREEN}✓ Utility scripts moved${NC}"

# Phase 4: Delete Duplicates/Old Files
echo -e "\n${BLUE}Phase 4: Deleting duplicates and old files...${NC}"
rm -f "uncertainty_visualization_demo copy.ipynb"
rm -f "watsonx_deployment_experiment copy.ipynb"
rm -f ui_components_old.py
rm -f ui_components_backup_20260604_205217.tar.gz
echo -e "${GREEN}✓ Duplicates deleted${NC}"

# Phase 5: Archive Consolidation Scripts
echo -e "\n${BLUE}Phase 5: Archiving consolidation scripts...${NC}"
mkdir -p archive/consolidation_scripts
mv consolidate_codebase.sh archive/consolidation_scripts/ 2>/dev/null || true
# Keep rename_to_uqlab.sh for now
echo -e "${GREEN}✓ Consolidation scripts archived${NC}"

# Phase 6: Move Shell Scripts
echo -e "\n${BLUE}Phase 6: Moving shell scripts...${NC}"
mkdir -p scripts/shell
mv run_streamlit.sh scripts/shell/ 2>/dev/null || true
mv run_streamlit_modular.sh scripts/shell/ 2>/dev/null || true
mv test_api.sh scripts/shell/ 2>/dev/null || true
echo -e "${GREEN}✓ Shell scripts moved${NC}"

# Summary
echo -e "\n${GREEN}=============================="
echo "✅ Cleanup Complete!"
echo "==============================${NC}"

echo -e "\n${BLUE}Summary:${NC}"
echo "  ✓ Old documentation → archive/old_docs/"
echo "  ✓ Notebooks → notebooks/"
echo "  ✓ Utility scripts → scripts/utils/"
echo "  ✓ Shell scripts → scripts/shell/"
echo "  ✓ Duplicates deleted"
echo "  ✓ Consolidation scripts → archive/consolidation_scripts/"

echo -e "\n${BLUE}Root level now contains only:${NC}"
ls -1 | grep -E "\.(py|sh|md|yml|toml|ini|pdf|png)$|^\.env" | head -20

echo -e "\n${GREEN}Done! 🎉${NC}"

# Made with Bob
