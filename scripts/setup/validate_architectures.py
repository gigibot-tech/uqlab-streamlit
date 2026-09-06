#!/usr/bin/env python3
"""
Validate all three architectures work end-to-end
"""
import subprocess
import sys
from pathlib import Path

# Make uqlab_core importable when running this script directly from repo root.
_SCRIPT_DIR = Path(__file__).resolve().parent
_SRC_DIR = _SCRIPT_DIR.parents[1] / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from uqlab_core.runtime_paths import configs_dir


def run_test(config_name: str) -> bool:
    """Run single architecture test"""
    config_path = str(configs_dir() / "test" / f"{config_name}.yaml")
    output_dir = f"/tmp/test_{config_name}"
    
    print(f"\n{'='*60}")
    print(f"Testing: {config_name}")
    print(f"{'='*60}\n")
    
    cmd = [
        "python", "scripts/runners/run_fast_uncertainty_classification.py",
        "--config", config_path,
        "--output_dir", output_dir,
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ {config_name} PASSED")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {config_name} FAILED")
        print(f"Error: {e.stderr}")
        return False

def main():
    tests = [
        "test_resnet18_mcdropout",
        "test_cnn_mcdropout",
        "test_dinov2_mlp"
    ]
    
    results = {}
    for test in tests:
        results[test] = run_test(test)
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test}: {status}")
    
    if all(results.values()):
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)

if __name__ == "__main__":
    main()

# Made with Bob
