#!/usr/bin/env python3
"""Remove all 'uqlab' references and replace with 'uqlab'"""
import re
from pathlib import Path

# Replacement mappings
REPLACEMENTS = {
    # Path references
    r'/tmp/uqlab_experiments': '/tmp/uqlab_experiments',
    r'uqlab-streamlit': 'uqlab-streamlit',
    r'uqlab_viz_batch_id': 'uqlab_viz_batch_id',
    
    # Logger names
    r'"uqlab"': '"uqlab"',
    r"'uqlab'": "'uqlab'",
    
    # Comments and docstrings
    r'uqlab': 'uqlab',
    r'UQLab': 'UQLab',
    r'UQLAB': 'UQLAB',
}

def replace_in_file(filepath):
    """Replace uqlab references in a single file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply all replacements
        for pattern, replacement in REPLACEMENTS.items():
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
    """Process all Python files"""
    root = Path('.')
    updated_files = []
    
    # Process all .py files
    for py_file in root.rglob('*.py'):
        # Skip virtual environments and cache
        if any(part in py_file.parts for part in ['.venv', '__pycache__', 'node_modules', '.git']):
            continue
            
        if replace_in_file(py_file):
            updated_files.append(py_file)
            print(f"✅ Updated: {py_file}")
    
    # Also process markdown files
    for md_file in root.rglob('*.md'):
        if any(part in md_file.parts for part in ['.venv', 'node_modules', '.git']):
            continue
            
        if replace_in_file(md_file):
            updated_files.append(md_file)
            print(f"✅ Updated: {md_file}")
    
    print(f"\n📊 Summary: Updated {len(updated_files)} files")
    
    # Show what was changed
    if updated_files:
        print("\n📝 Changes made:")
        for old, new in REPLACEMENTS.items():
            print(f"  • {old} → {new}")
    
    return len(updated_files)

if __name__ == '__main__':
    count = main()
    exit(0 if count >= 0 else 1)
