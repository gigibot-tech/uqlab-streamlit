#!/usr/bin/env python3
"""Categorize Markdown files in a directory by filename keywords."""
import argparse
import os
from collections import defaultdict


def categorize_md_files(directory: str) -> None:
    directory = os.path.abspath(directory)
    md_files = [f for f in os.listdir(directory) if f.endswith(".md")]

    categories = {
        "Architecture & Design": ["ARCHITECTURE", "DESIGN", "SCHEMA", "FLOW", "STRUCTURE"],
        "Fixes & Debugging": ["FIX", "DEBUG", "ERROR", "ISSUE", "TROUBLESHOOT"],
        "UI & Frontend": ["UI", "STREAMLIT", "PROGRESSIVE", "VISUALIZATION", "CHART"],
        "Backend & API": ["BACKEND", "API", "STARTUP"],
        "Refactoring & Cleanup": ["REFACTOR", "CLEANUP", "REORGANIZATION", "CONSOLIDATION"],
        "Configuration": ["CONFIG", "SETUP"],
        "Documentation & Guides": ["README", "GUIDE", "QUICKSTART", "DOCUMENTATION"],
        "Testing & Validation": ["TEST", "VALIDATION", "VERIFICATION"],
        "Features & Implementation": ["IMPLEMENTATION", "FEATURE", "ENHANCEMENT"],
        "Analysis & Planning": ["ANALYSIS", "PLAN", "INVENTORY", "MAP"],
    }

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

    print(f"Total .md files in {directory}: {len(md_files)}\n")
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
    print("\nSummary:")
    for category in sorted(categories.keys()):
        count = len(categorized[category])
        if count > 0:
            print(f"  {category}: {count}")
    if uncategorized:
        print(f"  Uncategorized: {len(uncategorized)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Categorize Markdown files by filename keywords.")
    parser.add_argument("directory", nargs="?", default=".", help="Directory to scan (default: current directory)")
    args = parser.parse_args()
    categorize_md_files(args.directory)
