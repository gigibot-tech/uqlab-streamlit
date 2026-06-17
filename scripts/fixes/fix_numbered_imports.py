#!/usr/bin/env python3
"""Fix imports from numbered folders (invalid Python identifiers)"""
import re
from pathlib import Path

# Map numbered folders to valid Python names
FOLDER_RENAMES = {
    "1_data": "data",
    "2_models": "models", 
    "3_training": "training",
    "4_evaluation": "evaluation",
    "5_api": "api",
    "7_orchestration": "orchestration"
}

def fix_imports_in_file(filepath):
    """Fix numbered folder imports in a single file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix each numbered folder import
        for old_name, new_name in FOLDER_RENAMES.items():
            # Match: from uqlab.1_data -> from uqlab.data
            pattern = rf'from uqlab\.{re.escape(old_name)}'
            replacement = f'from uqlab.{new_name}'
            content = re.sub(pattern, replacement, content)
            
            # Match: import uqlab.1_data -> import uqlab.data
            pattern = rf'import uqlab\.{re.escape(old_name)}'
            replacement = f'import uqlab.{new_name}'
            content = re.sub(pattern, replacement, content)
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def main():
    """Fix all Python files"""
    src_dir = Path('src/uqlab')
    updated_files = []
    
    for py_file in src_dir.rglob('*.py'):
        if fix_imports_in_file(py_file):
            updated_files.append(py_file)
            print(f"✅ Fixed: {py_file}")
    
    print(f"\n📊 Summary: Fixed {len(updated_files)} files")
    
    # Now rename the actual folders
    print("\n📁 Renaming folders...")
    for old_name, new_name in FOLDER_RENAMES.items():
        old_path = src_dir / old_name
        new_path = src_dir / new_name
        if old_path.exists() and not new_path.exists():
            old_path.rename(new_path)
            print(f"✅ Renamed: {old_name} → {new_name}")
    
    return len(updated_files)

if __name__ == '__main__':
    count = main()
    exit(0 if count >= 0 else 1)
