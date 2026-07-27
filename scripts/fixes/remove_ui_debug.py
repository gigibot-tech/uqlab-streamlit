#!/usr/bin/env python3
"""
Remove UI debug panel and make all sections always visible.
This script:
1. Comments out render_ui_debug_panel() call
2. Removes all ui_on() conditional checks (makes sections always visible)
3. Removes ui_on_module() checks
"""

import re
from pathlib import Path

def remove_ui_debug_from_file(filepath: Path) -> None:
    """Remove UI debug logic from a Python file."""
    content = filepath.read_text()
    original = content
    
    # 1. Comment out render_ui_debug_panel() call
    content = re.sub(
        r'^(\s*)render_ui_debug_panel\(\)',
        r'\1# render_ui_debug_panel()  # DISABLED: UI debug panel removed',
        content,
        flags=re.MULTILINE
    )
    
    # 2. Remove ui_on() checks - make sections always visible
    # Pattern: if ui_on("key"):
    # Replace with: if True:  # ui_on("key") - always visible
    content = re.sub(
        r'if ui_on\("([^"]+)"\):',
        r'if True:  # ui_on("\1") - always visible',
        content
    )
    
    # 3. Remove ui_on_module() checks
    content = re.sub(
        r'if ui_on_module\("([^"]+)"\):',
        r'if True:  # ui_on_module("\1") - always visible',
        content
    )
    
    # 4. Handle compound conditions like: if ui_on("a") and ui_on_module("b"):
    # Replace with: if True:  # ui_on("a") and ui_on_module("b") - always visible
    content = re.sub(
        r'if ui_on\("([^"]+)"\) and ui_on_module\("([^"]+)"\):',
        r'if True:  # ui_on("\1") and ui_on_module("\2") - always visible',
        content
    )
    
    # 5. Handle OR conditions: if ui_on("a") or ui_on("b"):
    content = re.sub(
        r'if ui_on\("([^"]+)"\) or ui_on\("([^"]+)"\):',
        r'if True:  # ui_on("\1") or ui_on("\2") - always visible',
        content
    )
    
    if content != original:
        filepath.write_text(content)
        print(f"✅ Updated: {filepath}")
        return True
    else:
        print(f"⏭️  No changes: {filepath}")
        return False

def main():
    """Remove UI debug from streamlit_app_progressive.py"""
    target = Path("streamlit_app_progressive.py")
    
    if not target.exists():
        print(f"❌ File not found: {target}")
        return
    
    print("🔧 Removing UI debug panel and making all sections always visible...")
    print()
    
    changed = remove_ui_debug_from_file(target)
    
    print()
    if changed:
        print("✅ UI debug panel removed successfully!")
        print("📝 All sections are now always visible (no conditional rendering)")
        print()
        print("Next steps:")
        print("1. Restart the Streamlit app")
        print("2. Verify all sections are visible")
        print("3. Check that there are no infinite reruns")
    else:
        print("ℹ️  No changes were needed")

if __name__ == "__main__":
    main()

# Made with Bob
