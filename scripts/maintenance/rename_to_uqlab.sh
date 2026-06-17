#!/bin/bash
# Automated script to rename walaris → uqlab
# Also consolidates config files into shared/config/

set -e  # Exit on error

echo "🔄 Renaming walaris → uqlab (Uncertainty Quantification Lab)"
echo "=============================================================="

cd "$(dirname "$0")"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# ============================================================================
# PHASE 1: Backup
# ============================================================================
echo -e "\n${BLUE}Phase 1: Creating backup...${NC}"
BACKUP_DIR="backup_before_uqlab_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp -r src/walaris "$BACKUP_DIR/"
echo -e "${GREEN}✓ Backup created: $BACKUP_DIR${NC}"

# ============================================================================
# PHASE 2: Consolidate Config Files
# ============================================================================
echo -e "\n${BLUE}Phase 2: Consolidating config files...${NC}"

# Move shared/config.py into shared/config/ directory
if [ -f "src/walaris/shared/config.py" ]; then
    echo "  → Moving shared/config.py to shared/config/global_config.py"
    mv src/walaris/shared/config.py src/walaris/shared/config/global_config.py
    
    # Update the __init__.py to import from global_config.py instead of parent
    cat > src/walaris/shared/config/__init__.py << 'EOF'
"""Configuration management - All config classes in one place."""

# Import from global_config.py (was ../config.py)
from .global_config import (
    DataConfig,
    EvaluationConfig,
    GlobalConfig,
    ModelConfig,
    PathConfig,
    SystemConfig,
    TrainingConfig,
    get_config,
    reset_config,
    update_config,
)

# Import from classification.py and schemas.py
from .classification import *
from .schemas import *

__all__ = [
    # From global_config.py
    "DataConfig",
    "EvaluationConfig",
    "GlobalConfig",
    "ModelConfig",
    "PathConfig",
    "SystemConfig",
    "TrainingConfig",
    "get_config",
    "reset_config",
    "update_config",
]
EOF
    echo -e "${GREEN}✓ Config files consolidated${NC}"
else
    echo -e "${YELLOW}⚠ shared/config.py not found, skipping${NC}"
fi

# ============================================================================
# PHASE 3: Rename Directory
# ============================================================================
echo -e "\n${BLUE}Phase 3: Renaming src/walaris → src/uqlab...${NC}"
mv src/walaris src/uqlab
echo -e "${GREEN}✓ Directory renamed${NC}"

# ============================================================================
# PHASE 4: Update Symlinks
# ============================================================================
echo -e "\n${BLUE}Phase 4: Updating symlinks...${NC}"

# Remove old symlinks
rm -f uq_classification uq_benchmarks

# Create new symlinks
ln -s src/uqlab/classification uq_classification
ln -s src/uqlab/benchmarks uq_benchmarks

echo -e "${GREEN}✓ Symlinks updated${NC}"

# ============================================================================
# PHASE 5: Update Python Imports
# ============================================================================
echo -e "\n${BLUE}Phase 5: Updating Python imports...${NC}"

# Function to update imports in a file
update_imports() {
    local file="$1"
    # Skip if file doesn't exist or is in backup
    if [[ ! -f "$file" ]] || [[ "$file" == *"$BACKUP_DIR"* ]]; then
        return
    fi
    
    # Update imports
    sed -i '' 's/from walaris\./from uqlab./g' "$file"
    sed -i '' 's/import walaris\./import uqlab./g' "$file"
    sed -i '' 's/import walaris$/import uqlab/g' "$file"
    sed -i '' 's/"walaris\./"uqlab./g' "$file"
    sed -i '' 's/'\''walaris\./'\''uqlab./g' "$file"
}

# Update all Python files
echo "  → Updating .py files..."
find . -name "*.py" -type f ! -path "./$BACKUP_DIR/*" ! -path "./.venv/*" ! -path "./venv/*" | while read file; do
    update_imports "$file"
done

echo -e "${GREEN}✓ Python imports updated${NC}"

# ============================================================================
# PHASE 6: Update Configuration Files
# ============================================================================
echo -e "\n${BLUE}Phase 6: Updating configuration files...${NC}"

# Update setup.py if exists
if [ -f "setup.py" ]; then
    sed -i '' 's/walaris/uqlab/g' setup.py
    echo "  → Updated setup.py"
fi

# Update pyproject.toml if exists
if [ -f "pyproject.toml" ]; then
    sed -i '' 's/walaris/uqlab/g' pyproject.toml
    echo "  → Updated pyproject.toml"
fi

# Update package.json if exists
if [ -f "package.json" ]; then
    sed -i '' 's/walaris/uqlab/g' package.json
    echo "  → Updated package.json"
fi

echo -e "${GREEN}✓ Configuration files updated${NC}"

# ============================================================================
# PHASE 7: Update Documentation
# ============================================================================
echo -e "\n${BLUE}Phase 7: Updating documentation...${NC}"

# Update all markdown files
find . -name "*.md" -type f ! -path "./$BACKUP_DIR/*" | while read file; do
    sed -i '' 's/walaris/uqlab/g' "$file"
    sed -i '' 's/Walaris/UQLab/g' "$file"
    sed -i '' 's/WALARIS/UQLAB/g' "$file"
done

echo -e "${GREEN}✓ Documentation updated${NC}"

# ============================================================================
# PHASE 8: Update Paths in Config Files
# ============================================================================
echo -e "\n${BLUE}Phase 8: Updating paths in config files...${NC}"

# Update any hardcoded paths
find . -name "*.yaml" -o -name "*.yml" -o -name "*.json" | while read file; do
    if [[ "$file" != *"$BACKUP_DIR"* ]]; then
        sed -i '' 's/walaris/uqlab/g' "$file"
    fi
done

echo -e "${GREEN}✓ Paths updated${NC}"

# ============================================================================
# PHASE 9: Update __init__.py files
# ============================================================================
echo -e "\n${BLUE}Phase 9: Updating __init__.py references...${NC}"

# Update shared/__init__.py to import from config/ subdirectory
cat > src/uqlab/shared/__init__.py << 'EOF'
"""
Shared Utilities Module - Common functionality across all layers.

This module provides:
- Type definitions and enums
- Global configuration
- Utility functions
- Common constants
"""

from .config import (
    DataConfig,
    EvaluationConfig,
    GlobalConfig,
    ModelConfig,
    PathConfig,
    SystemConfig,
    TrainingConfig,
    get_config,
    reset_config,
    update_config,
)
from .types import (
    ALEATORIC_SIGNALS,
    CIFAR10_CLASSES,
    COLOR_SCHEMES,
    EPISTEMIC_SIGNALS,
    GROUP_ORDER,
    SIGNAL_LABELS,
    SIGNAL_NAMES,
    BoolArray,
    CallbackProtocol,
    ConfigDict,
    DataLoaderProtocol,
    DeviceType,
    EvaluationGroup,
    ExperimentStatus,
    FloatArray,
    LabelArray,
    MetricType,
    MetricsDict,
    ModelArchitecture,
    ModelProtocol,
    NoiseType,
    PathLike,
    PredictionResult,
    SignalDict,
    SignalType,
    SplitType,
    SweepType,
    TensorLike,
    TrainingMode,
    UncertaintyMethod,
)
from .utils import (
    Timer,
    batch_to_device,
    ensure_dir,
    format_number,
    format_time,
    get_device,
    get_file_hash,
    get_logger,
    get_string_hash,
    load_json,
    load_pickle,
    load_yaml,
    retry,
    safe_execute,
    save_json,
    save_pickle,
    save_yaml,
    set_seed,
    setup_logging,
    timeit,
    to_numpy,
    to_tensor,
    truncate_string,
    validate_non_negative,
    validate_positive,
    validate_range,
)

__all__ = [
    # Config
    "DataConfig",
    "EvaluationConfig",
    "GlobalConfig",
    "ModelConfig",
    "PathConfig",
    "SystemConfig",
    "TrainingConfig",
    "get_config",
    "reset_config",
    "update_config",
    # Types
    "ALEATORIC_SIGNALS",
    "CIFAR10_CLASSES",
    "COLOR_SCHEMES",
    "EPISTEMIC_SIGNALS",
    "GROUP_ORDER",
    "SIGNAL_LABELS",
    "SIGNAL_NAMES",
    "BoolArray",
    "CallbackProtocol",
    "ConfigDict",
    "DataLoaderProtocol",
    "DeviceType",
    "EvaluationGroup",
    "ExperimentStatus",
    "FloatArray",
    "LabelArray",
    "MetricType",
    "MetricsDict",
    "ModelArchitecture",
    "ModelProtocol",
    "NoiseType",
    "PathLike",
    "PredictionResult",
    "SignalDict",
    "SignalType",
    "SplitType",
    "SweepType",
    "TensorLike",
    "TrainingMode",
    "UncertaintyMethod",
    # Utils
    "Timer",
    "batch_to_device",
    "ensure_dir",
    "format_number",
    "format_time",
    "get_device",
    "get_file_hash",
    "get_logger",
    "get_string_hash",
    "load_json",
    "load_pickle",
    "load_yaml",
    "retry",
    "safe_execute",
    "save_json",
    "save_pickle",
    "save_yaml",
    "set_seed",
    "setup_logging",
    "timeit",
    "to_numpy",
    "to_tensor",
    "truncate_string",
    "validate_non_negative",
    "validate_positive",
    "validate_range",
]

# Made with Bob
EOF

echo -e "${GREEN}✓ __init__.py files updated${NC}"

# ============================================================================
# SUMMARY
# ============================================================================
echo -e "\n${GREEN}======================================"
echo "✅ Rename Complete: walaris → uqlab"
echo "======================================${NC}"

echo -e "\n${BLUE}Summary:${NC}"
echo "  ✓ Backup created: $BACKUP_DIR"
echo "  ✓ Config files consolidated to shared/config/"
echo "  ✓ Directory renamed: src/walaris → src/uqlab"
echo "  ✓ Symlinks updated"
echo "  ✓ Python imports updated (from walaris. → from uqlab.)"
echo "  ✓ Configuration files updated"
echo "  ✓ Documentation updated"
echo "  ✓ Paths updated"

echo -e "\n${YELLOW}⚠ Next Steps:${NC}"
echo "  1. Test imports: python -c 'from uqlab.shared.config import GlobalConfig'"
echo "  2. Run Streamlit app: streamlit run streamlit_app.py"
echo "  3. Run tests: pytest tests/"
echo "  4. If everything works, delete backup: rm -rf $BACKUP_DIR"

echo -e "\n${BLUE}Rollback (if needed):${NC}"
echo "  mv src/uqlab src/walaris"
echo "  cp -r $BACKUP_DIR/walaris/* src/walaris/"

echo -e "\n${GREEN}Done! 🎉${NC}"