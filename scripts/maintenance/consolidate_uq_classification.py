#!/usr/bin/env python3
"""
Script to consolidate uq_classification into uqlab.evaluation.classification

Steps:
1. Remove the uq_classification symlink
2. Update all imports from uq_classification to uqlab.evaluation.classification
3. Create a README documenting the change

Backup: src/uqlab_classification_backup/ (already created)
"""
import re
import subprocess
from pathlib import Path

# Files to update
FILES_TO_UPDATE = [
    "scripts/run_fast_uncertainty_classification.py",
    "scripts/examples/minimal_experiment.py",
    "tests/test_evaluation.py",
    "tests/test_config_schema.py",
    "tests/legacy/test_model_config.py",
    "scripts/legacy/export_to_watsonx.py",
    "tests/legacy/test_refactor.py",
    "tests/legacy/test_model_config_simple.py",
    "streamlit_app.py",
    "src/uqlab/data/__init__.py",
    "src/uqlab/ui_components/results/results.py",
    "src/uqlab/ui_components/visualization/signals/signal_visualization.py",
    "src/uqlab/ui_components/visualization/signals/signal_diagnostic_viz.py",
    "backend/app/services/executors/direct_executor.py",
]

def update_imports(file_path: Path) -> tuple[bool, int]:
    """Update imports in a single file. Returns (changed, num_replacements)"""
    if not file_path.exists():
        print(f"⚠️  File not found: {file_path}")
        return False, 0
    
    content = file_path.read_text()
    original_content = content
    replacements = 0
    
    # Pattern 1: from uq_classification.X import Y -> from uqlab.evaluation.classification.X import Y
    new_content, n = re.subn(
        r'from uq_classification\.(\w+)',
        r'from uqlab.evaluation.classification.\1',
        content
    )
    content = new_content
    replacements += n
    
    # Pattern 2: import uq_classification -> import uqlab.evaluation.classification as uq_classification
    new_content, n = re.subn(
        r'^import uq_classification$',
        r'import uqlab.evaluation.classification as uq_classification',
        content,
        flags=re.MULTILINE
    )
    content = new_content
    replacements += n
    
    # Pattern 3: from uq_classification import -> from uqlab.evaluation.classification import
    new_content, n = re.subn(
        r'from uq_classification import',
        r'from uqlab.evaluation.classification import',
        content
    )
    content = new_content
    replacements += n
    
    if content != original_content:
        file_path.write_text(content)
        print(f"✅ Updated: {file_path} ({replacements} replacements)")
        return True, replacements
    else:
        print(f"ℹ️  No changes: {file_path}")
        return False, 0

def remove_symlink(root: Path) -> bool:
    """Remove the uq_classification symlink"""
    symlink_path = root / "src" / "uq_classification"
    
    if not symlink_path.exists():
        print(f"⚠️  Symlink not found: {symlink_path}")
        return False
    
    if not symlink_path.is_symlink():
        print(f"❌ ERROR: {symlink_path} is not a symlink!")
        return False
    
    symlink_path.unlink()
    print(f"✅ Removed symlink: {symlink_path}")
    return True

def create_readme(root: Path):
    """Create README documenting the consolidation"""
    readme_content = """# uq_classification Consolidation

## What Changed

The `uq_classification` symlink has been removed. All code now uses the canonical path:

```python
# OLD (via symlink)
from uq_classification.models import EmbeddingDataset

# NEW (canonical path)
from uqlab.models.classification_models import EmbeddingDataset
```

## Why

1. **Clarity**: The symlink created confusion about the actual code location
2. **Maintainability**: Single source of truth for imports
3. **SoC**: Clear separation between general (`uqlab/`) and classification-specific (`uqlab/evaluation/classification/`)

## Backup

A backup of the original `uqlab/evaluation/classification/` directory exists at:
- `src/uqlab_classification_backup/`

## Files Updated

All imports in the following files were updated:
- `scripts/run_fast_uncertainty_classification.py`
- `scripts/examples/minimal_experiment.py`
- `tests/test_evaluation.py`
- `tests/test_config_schema.py`
- `tests/legacy/test_model_config.py`
- `scripts/legacy/export_to_watsonx.py`
- `tests/legacy/test_refactor.py`
- `tests/legacy/test_model_config_simple.py`
- `streamlit_app.py`
- `src/uqlab/data/__init__.py`
- `src/uqlab/ui_components/results/results.py`
- `src/uqlab/ui_components/visualization/signals/signal_visualization.py`
- `src/uqlab/ui_components/visualization/signals/signal_diagnostic_viz.py`
- `backend/app/services/executors/direct_executor.py`

## Rollback

If needed, you can rollback by:
1. Restoring the symlink: `ln -s uqlab/evaluation/classification src/uq_classification`
2. Reverting the import changes: `git revert <commit-hash>`
"""
    
    readme_path = root / "UQ_CLASSIFICATION_CONSOLIDATION.md"
    readme_path.write_text(readme_content)
    print(f"✅ Created README: {readme_path}")

def main():
    root = Path(__file__).parent
    
    print("=" * 80)
    print("CONSOLIDATING uq_classification INTO uqlab.evaluation.classification")
    print("=" * 80)
    print()
    
    # Step 1: Update imports
    print("Step 1: Updating imports...")
    print("-" * 80)
    updated_count = 0
    total_replacements = 0
    
    for file_path_str in FILES_TO_UPDATE:
        file_path = root / file_path_str
        changed, replacements = update_imports(file_path)
        if changed:
            updated_count += 1
            total_replacements += replacements
    
    print()
    print(f"✅ Updated {updated_count} files ({total_replacements} total replacements)")
    print()
    
    # Step 2: Remove symlink
    print("Step 2: Removing symlink...")
    print("-" * 80)
    if remove_symlink(root):
        print("✅ Symlink removed successfully")
    else:
        print("❌ Failed to remove symlink")
        return
    print()
    
    # Step 3: Create README
    print("Step 3: Creating documentation...")
    print("-" * 80)
    create_readme(root)
    print()
    
    print("=" * 80)
    print("✅ CONSOLIDATION COMPLETE!")
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. Test the application: streamlit run streamlit_app_progressive.py")
    print("2. Run tests: pytest tests/")
    print("3. Commit changes: git add -A && git commit -m 'Consolidate uq_classification'")
    print("4. If issues occur, restore from backup: src/uqlab_classification_backup/")

if __name__ == "__main__":
    main()

# Made with Bob
