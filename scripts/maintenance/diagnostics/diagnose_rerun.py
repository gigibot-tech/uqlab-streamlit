#!/usr/bin/env python3
"""
Diagnostic script to check for potential infinite rerun causes.
"""

import re
from pathlib import Path

def check_file(filepath: Path):
    """Check a file for potential rerun issues."""
    issues = []
    
    try:
        content = filepath.read_text(encoding='utf-8')
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Check for st.rerun() without return
            if 'st.rerun()' in line and not line.strip().startswith('#'):
                # Check next line
                if i < len(lines):
                    next_line = lines[i]
                    if next_line.strip() and not next_line.strip().startswith('return'):
                        issues.append(f"Line {i}: st.rerun() without return on next line")
            
            # Check for auto_refresh = True (hardcoded)
            if re.search(r'auto_refresh\s*=\s*True', line) and not line.strip().startswith('#'):
                issues.append(f"Line {i}: auto_refresh hardcoded to True")
            
            # Check for infinite while loops
            if re.search(r'while\s+True:', line) and not line.strip().startswith('#'):
                issues.append(f"Line {i}: Infinite while loop detected")
        
        return issues
        
    except Exception as e:
        return [f"Error reading file: {e}"]

def main():
    root = Path('.')
    
    # Find all Python files
    py_files = list(root.rglob('*.py'))
    py_files = [f for f in py_files if '.venv' not in str(f) and '__pycache__' not in str(f)]
    
    # Filter to files with streamlit
    files_to_check = []
    for f in py_files:
        try:
            if 'streamlit' in f.read_text(encoding='utf-8').lower():
                files_to_check.append(f)
        except:
            pass
    
    print(f"🔍 Checking {len(files_to_check)} Streamlit files for rerun issues...\n")
    
    total_issues = 0
    for filepath in files_to_check:
        issues = check_file(filepath)
        if issues:
            print(f"⚠️  {filepath.relative_to(root)}:")
            for issue in issues:
                print(f"   {issue}")
                total_issues += 1
            print()
    
    if total_issues == 0:
        print("✅ No obvious rerun issues found!")
        print("\n💡 If the app still shows 'running man', it might be:")
        print("   1. Normal initial loading (wait a few seconds)")
        print("   2. Backend API not responding (check if backend is running)")
        print("   3. Slow imports or data loading")
        print("   4. Network requests timing out")
    else:
        print(f"❌ Found {total_issues} potential issues")

if __name__ == '__main__':
    main()

# Made with Bob
