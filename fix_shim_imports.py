#!/usr/bin/env python3
"""Fix shim files to use new folder names (not numbered)"""
import re
from pathlib import Path

# Map old numbered paths to new paths
SHIM_REPLACEMENTS = {
    r'uqlab\.1_data': 'uqlab.data',
    r'uqlab\.2_models': 'uqlab.models',
    r'uqlab\.3_training': 'uqlab.training',
    r'uqlab\.4_evaluation': 'uqlab.evaluation',
    r'uqlab\.5_api': 'uqlab.api',
    r'uqlab\.7_orchestration': 'uqlab.orchestration',
}

def fix_shim_file(filepath):
    """Fix numbered imports in shim files"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply all replacements
        for old_pattern, new_path in SHIM_REPLACEMENTS.items():
            content = re.sub(old_pattern, new_path, content)
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def main():
    """Fix all shim files in uq_classification"""
    shim_dir = Path('src/uqlab/evaluation/classification')
    updated_files = []
    
    for py_file in shim_dir.glob('*.py'):
        if py_file.name == '__init__.py':
            continue
        if fix_shim_file(py_file):
            updated_files.append(py_file)
            print(f"✅ Fixed: {py_file}")
    
    print(f"\n📊 Summary: Fixed {len(updated_files)} shim files")
    return len(updated_files)

if __name__ == '__main__':
    count = main()
    exit(0 if count >= 0 else 1)
