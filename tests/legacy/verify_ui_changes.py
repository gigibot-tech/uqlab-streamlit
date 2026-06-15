#!/usr/bin/env python3
"""
Verification script to confirm UI redesign changes are in place.
Run this to verify all 3 tabs have the new 3-option aleatoric noise design.
"""

import re
from pathlib import Path

def check_file_for_pattern(filepath: Path, patterns: list[str]) -> dict:
    """Check if file contains all required patterns."""
    try:
        content = filepath.read_text()
        results = {}
        for pattern in patterns:
            results[pattern] = bool(re.search(pattern, content, re.MULTILINE))
        return results
    except Exception as e:
        return {"error": str(e)}

def main():
    print("=" * 80)
    print("VERIFYING UI REDESIGN CHANGES")
    print("=" * 80)
    
    # Check 1: experiment_config.py (Single/Batch tabs)
    print("\n1. Checking ui_components/experiment_config.py...")
    exp_config = Path("ui_components/experiment_config.py")
    exp_patterns = [
        r"No noise \(0%, clean labels\)",
        r"CIFAR-10N pre-existing noise",
        r"Custom random flipping \(0-50%, sweepable\)",
        r"index=2",  # Default to custom flipping
        r"Base Dataset.*Clean CIFAR-10"
    ]
    exp_results = check_file_for_pattern(exp_config, exp_patterns)
    
    for pattern, found in exp_results.items():
        status = "✅" if found else "❌"
        print(f"  {status} {pattern}")
    
    # Check 2: dataset.py
    print("\n2. Checking ui_components/dataset.py...")
    dataset = Path("ui_components/dataset.py")
    dataset_patterns = [
        r"Base Dataset.*CIFAR-10 \(clean\)",
        r"Clean labels \(no noise by default\)",
        r"reference only"
    ]
    dataset_results = check_file_for_pattern(dataset, dataset_patterns)
    
    for pattern, found in dataset_results.items():
        status = "✅" if found else "❌"
        print(f"  {status} {pattern}")
    
    # Check 3: unified_builder.py
    print("\n3. Checking ui_components/unified_builder.py...")
    unified = Path("ui_components/unified_builder.py")
    unified_patterns = [
        r"No noise \(0%, clean labels\)",
        r"CIFAR-10N pre-existing noise",
        r"Custom random flipping \(0-50%, sweepable\)",
        r"index=2",  # Default to custom flipping
        r"Base Dataset.*Clean CIFAR-10"
    ]
    unified_results = check_file_for_pattern(unified, unified_patterns)
    
    for pattern, found in unified_results.items():
        status = "✅" if found else "❌"
        print(f"  {status} {pattern}")
    
    # Summary
    print("\n" + "=" * 80)
    all_checks = list(exp_results.values()) + list(dataset_results.values()) + list(unified_results.values())
    if all(all_checks):
        print("✅ ALL CHECKS PASSED - UI redesign is complete!")
        print("\nNext step: Restart Streamlit to see changes:")
        print("  cd walaris-cen && ./run_streamlit.sh")
    else:
        print("❌ SOME CHECKS FAILED - Review the output above")
    print("=" * 80)

if __name__ == "__main__":
    main()

# Made with Bob
