#!/usr/bin/env python3
"""
Fix all relative imports in ui_components to match the reorganized directory structure.
"""

import re
from pathlib import Path

# Define the import replacements
REPLACEMENTS = [
    # In orchestration/ files
    (r'from \.experiment_config import', r'from ..config.experiment_config import', 'orchestration'),
    (r'from \.config_types import', r'from ..config.config_types import', 'orchestration'),
    (r'from \.heatmap_visualization import', r'from ..visualization.sweeps.heatmap_visualization import', 'orchestration'),
    (r'from \.signal_sweep_paper_viz import', r'from ..visualization.signals.signal_sweep_paper_viz import', 'orchestration'),
    
    # In selectors/ files
    (r'from \.unified_builder import', r'from ..orchestration.unified_builder import', 'selectors'),
    
    # In visualization/sweeps/ files
    (r'from \.signal_diagnostic_viz import', r'from ..signals.signal_diagnostic_viz import', 'visualization/sweeps'),
    (r'from \.signal_sweep_paper_viz import', r'from ..signals.signal_sweep_paper_viz import', 'visualization/sweeps'),
    (r'from \.results import', r'from ...results import', 'visualization/sweeps'),
]

def fix_file(filepath: Path):
    """Fix imports in a single file."""
    content = filepath.read_text()
    original = content
    
    # Determine which directory the file is in
    parts = filepath.parts
    if 'orchestration' in parts:
        context = 'orchestration'
    elif 'selectors' in parts:
        context = 'selectors'
    elif 'visualization' in parts and 'sweeps' in parts:
        context = 'visualization/sweeps'
    else:
        return False
    
    # Apply relevant replacements
    for pattern, replacement, target_context in REPLACEMENTS:
        if context == target_context:
            content = re.sub(pattern, replacement, content)
    
    if content != original:
        filepath.write_text(content)
        print(f"✅ Fixed: {filepath}")
        return True
    return False

def main():
    src_dir = Path('src/uqlab/ui_components')
    
    if not src_dir.exists():
        print(f"Error: {src_dir} not found")
        return
    
    fixed_count = 0
    
    # Find all Python files
    for py_file in src_dir.rglob('*.py'):
        if py_file.name == '__init__.py':
            continue
        if fix_file(py_file):
            fixed_count += 1
    
    print(f"\n🎉 Fixed {fixed_count} files")

if __name__ == '__main__':
    main()

# Made with Bob
