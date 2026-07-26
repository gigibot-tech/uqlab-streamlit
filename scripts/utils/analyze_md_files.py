import os
import sys
from collections import defaultdict
from pathlib import Path

# Resolve the directory to scan: optional CLI argument, otherwise project root
# (two levels up from scripts/utils/ where this file lives).
scan_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent.parent

# Get all .md files at the scanned directory's root level
md_files = [f for f in os.listdir(scan_dir) if f.endswith('.md')]

# Define categories based on keywords
categories = {
    'Architecture & Design': ['ARCHITECTURE', 'DESIGN', 'SCHEMA', 'FLOW', 'STRUCTURE'],
    'Fixes & Debugging': ['FIX', 'DEBUG', 'ERROR', 'ISSUE', 'TROUBLESHOOT'],
    'UI & Frontend': ['UI', 'STREAMLIT', 'PROGRESSIVE', 'VISUALIZATION', 'CHART'],
    'Backend & API': ['BACKEND', 'API', 'STARTUP'],
    'Refactoring & Cleanup': ['REFACTOR', 'CLEANUP', 'REORGANIZATION', 'CONSOLIDATION'],
    'Configuration': ['CONFIG', 'SETUP'],
    'Documentation & Guides': ['README', 'GUIDE', 'QUICKSTART', 'DOCUMENTATION'],
    'Testing & Validation': ['TEST', 'VALIDATION', 'VERIFICATION'],
    'Features & Implementation': ['IMPLEMENTATION', 'FEATURE', 'ENHANCEMENT'],
    'Analysis & Planning': ['ANALYSIS', 'PLAN', 'INVENTORY', 'MAP'],
}

# Categorize files
categorized = defaultdict(list)
uncategorized = []

for file in sorted(md_files):
    file_upper = file.upper()
    matched = False
    
    for category, keywords in categories.items():
        if any(keyword in file_upper for keyword in keywords):
            categorized[category].append(file)
            matched = True
            break
    
    if not matched:
        uncategorized.append(file)

# Print results
print(f"Total .md files: {len(md_files)}\n")
print("=" * 80)

for category in sorted(categories.keys()):
    files = categorized[category]
    if files:
        print(f"\n{category} ({len(files)} files):")
        print("-" * 80)
        for f in files:
            print(f"  • {f}")

if uncategorized:
    print(f"\nUncategorized ({len(uncategorized)} files):")
    print("-" * 80)
    for f in uncategorized:
        print(f"  • {f}")

print("\n" + "=" * 80)
print(f"\nSummary:")
for category in sorted(categories.keys()):
    count = len(categorized[category])
    if count > 0:
        print(f"  {category}: {count}")
if uncategorized:
    print(f"  Uncategorized: {len(uncategorized)}")
