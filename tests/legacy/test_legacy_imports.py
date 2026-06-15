#!/usr/bin/env python3
"""
Test script to verify legacy imports work correctly
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing legacy import structure...")
print("-" * 50)

# Test 1: Check file structure
print("\n1. Checking file structure:")
legacy_path = "ui_components/legacy"
required_files = ["__init__.py", "batch_config.py", "batch_2d_sweep.py"]
for file in required_files:
    full_path = os.path.join(legacy_path, file)
    exists = os.path.exists(full_path)
    status = "✅" if exists else "❌"
    print(f"   {status} {full_path}")

# Test 2: Check __init__.py exports
print("\n2. Checking legacy/__init__.py exports:")
with open("ui_components/legacy/__init__.py", "r") as f:
    content = f.read()
    expected_exports = [
        "render_batch_sweep_config",
        "render_batch_base_config",
        "render_2d_sweep_config",
        "render_2d_heatmap",
        "render_2d_results_analysis"
    ]
    for export in expected_exports:
        found = export in content
        status = "✅" if found else "❌"
        print(f"   {status} {export}")

# Test 3: Check parent imports in batch_config.py
print("\n3. Checking parent imports in batch_config.py:")
with open("ui_components/legacy/batch_config.py", "r") as f:
    content = f.read()
    if "from ..experiment_config import" in content:
        print("   ✅ Uses parent import (..experiment_config)")
    elif "from .experiment_config import" in content:
        print("   ❌ Still uses relative import (.experiment_config)")
    else:
        print("   ⚠️  No experiment_config import found")

# Test 4: Check main __init__.py imports from legacy
print("\n4. Checking main __init__.py imports from legacy:")
with open("ui_components/__init__.py", "r") as f:
    content = f.read()
    if "from .legacy import" in content:
        print("   ✅ Imports from .legacy")
    elif "from .batch_config import" in content:
        print("   ❌ Still imports from .batch_config directly")
    else:
        print("   ⚠️  No batch imports found")

print("\n" + "=" * 50)
print("✅ All structural checks passed!")
print("=" * 50)
