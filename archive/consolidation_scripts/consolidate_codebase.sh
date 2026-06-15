#!/bin/bash
# Automated Codebase Consolidation Script
# Merges OLD structure into NEW MLOps structure (1-7)

set -e  # Exit on error

echo "🚀 Starting Codebase Consolidation..."
echo "======================================"

cd "$(dirname "$0")/src/walaris"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ============================================================
# PHASE 1: Create Directory Structure
# ============================================================
echo -e "\n${BLUE}Phase 1: Creating directory structure...${NC}"

mkdir -p 2_models
mkdir -p 4_evaluation/signals
mkdir -p 4_evaluation/benchmarks
mkdir -p 5_api/integrations
mkdir -p 6_ui/visualization
mkdir -p 6_ui/apps
mkdir -p shared/config
mkdir -p shared/utils
mkdir -p shared/notebook_utils/comparisons

echo -e "${GREEN}✓ Directory structure created${NC}"

# ============================================================
# PHASE 2: Move classification/ files
# ============================================================
echo -e "\n${BLUE}Phase 2: Moving classification/ files...${NC}"

# 2.1 Models
echo "  → Moving models..."
mv classification/models.py 2_models/classification_models.py
mv classification/model_factory.py 2_models/factory.py
mv classification/feature_extractor.py 2_models/feature_extractors.py

# 2.2 Evaluation
echo "  → Moving evaluation..."
mv classification/evaluation.py 4_evaluation/evaluator.py
mv classification/attribution_signals.py 4_evaluation/signals/attribution.py
mv classification/signal_formula_specs.py 4_evaluation/signals/formulas.py

# 2.3 Configuration
echo "  → Moving configuration..."
mv classification/config.py shared/config/classification.py
mv classification/config_schema.py shared/config/schemas.py

# 2.4 Utilities
echo "  → Moving utilities..."
mv classification/utils.py shared/utils/classification.py
mv classification/unified_tracker.py shared/utils/tracking.py

# 2.5 Visualization
echo "  → Moving visualization..."
mv classification/decision_boundary_viz.py 6_ui/visualization/decision_boundaries.py
mv classification/streamlit_viz_app.py 6_ui/apps/classification_viz.py

# 2.6 watsonx Integration
echo "  → Moving watsonx integration..."
mv classification/watsonx_streamlit.py 5_api/integrations/watsonx.py

# 2.7 Archive old versions
echo "  → Archiving old versions..."
mkdir -p ../../archive/classification
mv classification/archive ../../archive/classification/ 2>/dev/null || true
mv classification/v2 ../../archive/classification/ 2>/dev/null || true

# 2.8 Keep data_loader.py for now (needs manual merge)
echo -e "${YELLOW}  ⚠ classification/data_loader.py kept for manual merge with 1_data/loaders.py${NC}"

# 2.9 Keep documentation
echo "  → Keeping documentation files..."
# Keep: DECISION_BOUNDARY_VIZ_README.md, MERGE_NOTES.md, STREAMLIT_APP_README.md, requirements_viz.txt

echo -e "${GREEN}✓ classification/ files moved${NC}"

# ============================================================
# PHASE 3: Move benchmarks/
# ============================================================
echo -e "\n${BLUE}Phase 3: Moving benchmarks/...${NC}"

# Move all benchmark content
mv benchmarks/benchmarks 4_evaluation/benchmarks/implementations 2>/dev/null || true
mv benchmarks/data 4_evaluation/benchmarks/data 2>/dev/null || true
mv benchmarks/models 4_evaluation/benchmarks/models 2>/dev/null || true
mv benchmarks/utils 4_evaluation/benchmarks/utils 2>/dev/null || true
mv benchmarks/examples 4_evaluation/benchmarks/examples 2>/dev/null || true
mv benchmarks/visualization.py 4_evaluation/benchmarks/
mv benchmarks/datatypes.py 4_evaluation/benchmarks/
mv benchmarks/setup.py 4_evaluation/benchmarks/
mv benchmarks/README.md 4_evaluation/benchmarks/
mv benchmarks/requirements*.txt 4_evaluation/benchmarks/ 2>/dev/null || true

echo -e "${GREEN}✓ benchmarks/ moved${NC}"

# ============================================================
# PHASE 4: Move notebook_support/
# ============================================================
echo -e "\n${BLUE}Phase 4: Moving notebook_support/...${NC}"

mv notebook_support/signals.py shared/notebook_utils/
mv notebook_support/plotting.py shared/notebook_utils/
mv notebook_support/data_utils.py shared/notebook_utils/
mv notebook_support/metric_specs.py shared/notebook_utils/metrics.py
mv notebook_support/constants.py shared/notebook_utils/
mv notebook_support/method_comparison.py shared/notebook_utils/comparisons/
mv notebook_support/method_comparison_plotly.py shared/notebook_utils/comparisons/
mv notebook_support/single_architecture_plot.py shared/notebook_utils/comparisons/
mv notebook_support/README.md shared/notebook_utils/

echo -e "${GREEN}✓ notebook_support/ moved${NC}"

# ============================================================
# PHASE 5: Archive disentanglement_paper/
# ============================================================
echo -e "\n${BLUE}Phase 5: Archiving disentanglement_paper/...${NC}"

mkdir -p ../../archive/research
mv disentanglement_paper ../../archive/research/

echo -e "${GREEN}✓ disentanglement_paper/ archived${NC}"

# ============================================================
# PHASE 6: Create __init__.py files
# ============================================================
echo -e "\n${BLUE}Phase 6: Creating __init__.py files...${NC}"

# 2_models/__init__.py
cat > 2_models/__init__.py << 'EOF'
"""Model architectures and factories."""
from .classification_models import *
from .factory import *
from .feature_extractors import *
EOF

# 4_evaluation/__init__.py
cat > 4_evaluation/__init__.py << 'EOF'
"""Evaluation, metrics, and benchmarks."""
from .evaluator import *
EOF

# 4_evaluation/signals/__init__.py
cat > 4_evaluation/signals/__init__.py << 'EOF'
"""Signal computation and attribution."""
from .attribution import *
from .formulas import *
EOF

# 4_evaluation/benchmarks/__init__.py
cat > 4_evaluation/benchmarks/__init__.py << 'EOF'
"""Benchmark implementations and utilities."""
from .datatypes import *
from .visualization import *
EOF

# 5_api/integrations/__init__.py
cat > 5_api/integrations/__init__.py << 'EOF'
"""External API integrations."""
EOF

# 6_ui/__init__.py
cat > 6_ui/__init__.py << 'EOF'
"""UI components and applications."""
EOF

# 6_ui/visualization/__init__.py
cat > 6_ui/visualization/__init__.py << 'EOF'
"""Visualization components."""
from .decision_boundaries import *
EOF

# 6_ui/apps/__init__.py
cat > 6_ui/apps/__init__.py << 'EOF'
"""Streamlit applications."""
EOF

# shared/config/__init__.py
cat > shared/config/__init__.py << 'EOF'
"""Configuration management."""
from .classification import *
from .schemas import *
EOF

# shared/utils/__init__.py
cat > shared/utils/__init__.py << 'EOF'
"""Shared utilities."""
from .classification import *
from .tracking import *
EOF

# shared/notebook_utils/__init__.py
cat > shared/notebook_utils/__init__.py << 'EOF'
"""Notebook support utilities."""
from .signals import *
from .plotting import *
from .data_utils import *
from .metrics import *
EOF

# shared/notebook_utils/comparisons/__init__.py
cat > shared/notebook_utils/comparisons/__init__.py << 'EOF'
"""Method comparison utilities."""
from .method_comparison import *
from .method_comparison_plotly import *
from .single_architecture_plot import *
EOF

echo -e "${GREEN}✓ __init__.py files created${NC}"

# ============================================================
# PHASE 7: Create backward compatibility layer
# ============================================================
echo -e "\n${BLUE}Phase 7: Creating backward compatibility...${NC}"

# classification/__init__.py (redirect old imports)
cat > classification/__init__.py << 'EOF'
"""
Backward compatibility layer for classification module.
All functionality has been moved to the new MLOps structure.
"""
import warnings

warnings.warn(
    "Importing from 'classification' is deprecated. "
    "Please update imports to use the new structure:\n"
    "  - Models: from walaris.2_models import ...\n"
    "  - Evaluation: from walaris.4_evaluation import ...\n"
    "  - Config: from walaris.shared.config import ...\n"
    "  - Utils: from walaris.shared.utils import ...",
    DeprecationWarning,
    stacklevel=2
)

# Redirect imports
from ..2_models.classification_models import *
from ..2_models.factory import *
from ..2_models.feature_extractors import *
from ..4_evaluation.evaluator import *
from ..4_evaluation.signals.attribution import *
from ..4_evaluation.signals.formulas import *
from ..shared.config.classification import *
from ..shared.config.schemas import *
from ..shared.utils.classification import *
from ..shared.utils.tracking import *
from ..6_ui.visualization.decision_boundaries import *
from ..5_api.integrations.watsonx import *
EOF

# benchmarks/__init__.py (redirect)
cat > benchmarks/__init__.py << 'EOF'
"""
Backward compatibility layer for benchmarks module.
All functionality has been moved to 4_evaluation/benchmarks/.
"""
import warnings

warnings.warn(
    "Importing from 'benchmarks' is deprecated. "
    "Please update imports to: from walaris.4_evaluation.benchmarks import ...",
    DeprecationWarning,
    stacklevel=2
)

from ..4_evaluation.benchmarks import *
EOF

# notebook_support/__init__.py (redirect)
cat > notebook_support/__init__.py << 'EOF'
"""
Backward compatibility layer for notebook_support module.
All functionality has been moved to shared/notebook_utils/.
"""
import warnings

warnings.warn(
    "Importing from 'notebook_support' is deprecated. "
    "Please update imports to: from walaris.shared.notebook_utils import ...",
    DeprecationWarning,
    stacklevel=2
)

from ..shared.notebook_utils import *
from ..shared.notebook_utils.comparisons import *
EOF

echo -e "${GREEN}✓ Backward compatibility layer created${NC}"

# ============================================================
# PHASE 8: Summary
# ============================================================
echo -e "\n${GREEN}======================================"
echo "✅ Consolidation Complete!"
echo "======================================${NC}"

echo -e "\n${BLUE}Summary:${NC}"
echo "  ✓ Created new directory structure"
echo "  ✓ Moved classification/ → 2_models/, 4_evaluation/, shared/, 6_ui/, 5_api/"
echo "  ✓ Moved benchmarks/ → 4_evaluation/benchmarks/"
echo "  ✓ Moved notebook_support/ → shared/notebook_utils/"
echo "  ✓ Archived disentanglement_paper/ → archive/research/"
echo "  ✓ Created __init__.py files"
echo "  ✓ Created backward compatibility layer"

echo -e "\n${YELLOW}⚠ Manual Steps Required:${NC}"
echo "  1. Merge classification/data_loader.py with 1_data/loaders.py"
echo "  2. Update all imports in:"
echo "     - Backend (backend/app/)"
echo "     - Scripts (scripts/)"
echo "     - Notebooks"
echo "     - Streamlit app (streamlit_app.py)"
echo "  3. Run tests to verify everything works"
echo "  4. Remove empty classification/, benchmarks/, notebook_support/ folders"

echo -e "\n${BLUE}Next Steps:${NC}"
echo "  1. Review changes: git status"
echo "  2. Test imports: python -c 'from walaris.2_models import *'"
echo "  3. Run test suite"
echo "  4. Update documentation"

echo -e "\n${GREEN}Done! 🎉${NC}"

# Made with Bob
