#!/usr/bin/env python3
"""Update imports after folder reorganization"""
import re
from pathlib import Path

# Define import mappings
IMPORT_MAPPINGS = {
    r'from uqlab\.triage': 'from uqlab.4_evaluation.legacy.triage',
    r'from uqlab\.legacy_metrics': 'from uqlab.4_evaluation.legacy.metrics',
    r'from uqlab\.legacy_experiments': 'from uqlab.4_evaluation.legacy.experiments',
    r'from uqlab\.backbones': 'from uqlab.2_models.backbones',
    r'from uqlab\.data_loaders': 'from uqlab.1_data.loaders',
    r'from uqlab\.classification': 'from uqlab.4_evaluation.classification',
}

def update_file(filepath):
    """Update imports in a single file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply all mappings
        for old_pattern, new_import in IMPORT_MAPPINGS.items():
            content = re.sub(old_pattern, new_import, content)
        
        # Only write if changed
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def main():
    """Update all Python files"""
    src_dir = Path('src/uqlab')
    updated_files = []
    
    for py_file in src_dir.rglob('*.py'):
        if update_file(py_file):
            updated_files.append(py_file)
            print(f"✅ Updated: {py_file}")
    
    print(f"\n📊 Summary: Updated {len(updated_files)} files")
    return len(updated_files)

if __name__ == '__main__':
    count = main()
    exit(0 if count >= 0 else 1)
