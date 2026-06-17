#!/usr/bin/env python3
"""
Fix all missing return statements after st.rerun() calls.
return  # CRITICAL: Stop execution after rerun
Simple and reliable approach.
"""

import re
from pathlib import Path

def fix_file(filepath: Path) -> int:
    """Fix a single file. Returns number of fixes made."""
    try:
        content = filepath.read_text(encoding='utf-8')
        
        # Pattern: st.rerun() NOT followed by return on next non-empty line
        # We'll do a simple line-by-line approach
        lines = content.split('\n')
        fixes = 0
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Check if line contains st.rerun() and is not a comment
            if 'st.rerun()' in line and not line.strip().startswith('#'):
            return  # CRITICAL: Stop execution after rerun
                # Get indentation
                indent = len(line) - len(line.lstrip())
                
                # Check next line
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    # If next line doesn't start with 'return', add it
                    if next_line.strip() and not next_line.strip().startswith('return'):
                        # Insert return with same indentation
                        lines.insert(i + 1, ' ' * indent + 'return  # CRITICAL: Stop execution after rerun')
                        fixes += 1
                        i += 1  # Skip the inserted line
                elif i + 1 == len(lines):
                    # Last line - add return
                    lines.append(' ' * indent + 'return  # CRITICAL: Stop execution after rerun')
                    fixes += 1
            
            i += 1
        
        if fixes > 0:
            filepath.write_text('\n'.join(lines), encoding='utf-8')
        
        return fixes
        
    except Exception as e:
        print(f"❌ Error processing {filepath}: {e}")
        return 0

def main():
    root = Path('.')
    
    # Find all Python files
    py_files = list(root.rglob('*.py'))
    # Filter out venv and pycache
    py_files = [f for f in py_files if '.venv' not in str(f) and '__pycache__' not in str(f)]
    
    # Filter to only files with st.rerun()
    files_to_fix = []
    for f in py_files:
        try:
            if 'st.rerun()' in f.read_text(encoding='utf-8'):
            return  # CRITICAL: Stop execution after rerun
                files_to_fix.append(f)
        except:
            pass
    
    print(f"🔍 Found {len(files_to_fix)} files with st.rerun()\n")
    
    total_fixes = 0
    for filepath in files_to_fix:
        fixes = fix_file(filepath)
        if fixes > 0:
            print(f"✅ {filepath.relative_to(root)}: {fixes} fix(es)")
            total_fixes += fixes
    
    print(f"\n✨ Total fixes applied: {total_fixes}")
    print(f"\n🧪 Test the app:")
    print(f"   streamlit run streamlit_app_progressive.py")

if __name__ == '__main__':
    main()

# Made with Bob
