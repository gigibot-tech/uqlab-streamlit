import os
from collections import defaultdict
from pathlib import Path

# Resolve project root regardless of where the script is run from
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_PATH = PROJECT_ROOT / "docs" / "validation" / "analysis_results.txt"

# Get all .md files at the project root
md_files = [f for f in os.listdir(PROJECT_ROOT) if f.endswith('.md')]

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

# Build output text
lines = []
lines.append(f"Total .md files: {len(md_files)}\n")
lines.append("=" * 80)

for category in sorted(categories.keys()):
    files = categorized[category]
    if files:
        lines.append(f"\n{category} ({len(files)} files):")
        lines.append("-" * 80)
        for f in files:
            lines.append(f"  • {f}")

if uncategorized:
    lines.append(f"\nUncategorized ({len(uncategorized)} files):")
    lines.append("-" * 80)
    for f in uncategorized:
        lines.append(f"  • {f}")

lines.append("\n" + "=" * 80)
lines.append("\nSummary:")
for category in sorted(categories.keys()):
    count = len(categorized[category])
    if count > 0:
        lines.append(f"  {category}: {count}")
if uncategorized:
    lines.append(f"  Uncategorized: {len(uncategorized)}")

output = "\n".join(lines)

# Write to file and print to stdout
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
OUTPUT_PATH.write_text(output)
print(output)
print(f"\nResults written to: {OUTPUT_PATH.relative_to(PROJECT_ROOT)}")
