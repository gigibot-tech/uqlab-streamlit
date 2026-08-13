#!/usr/bin/env env python3
"""Test backwards compatibility of TrainingConfig with aleatoric_noise_percentage."""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from app.domain.models import TrainingConfig

def test_backwards_compatibility():
    """Test that old configs without aleatoric_noise_percentage still work."""
    
    print("=" * 70)
    print("BACKWARDS COMPATIBILITY TEST")
    print("=" * 70)
    
    # Test 1: Create config without aleatoric_noise_percentage (old behavior)
    print("\n✅ Test 1: Create config without aleatoric_noise_percentage")
    config_old = TrainingConfig(
        noise_type="worse_label",
        under_supported_classes="3,5",
        under_train_per_class=50,
        regular_train_per_class=300,
        eval_per_group=600,
    )
    print(f"   Default value: {config_old.aleatoric_noise_percentage}")
    assert config_old.aleatoric_noise_percentage == 0.0, "Default should be 0.0"
    print("   ✓ Defaults to 0.0 (backwards compatible)")
    
    # Test 2: Create config with aleatoric_noise_percentage = 0 (explicit)
    print("\n✅ Test 2: Create config with aleatoric_noise_percentage=0.0")
    config_zero = TrainingConfig(
        noise_type="worse_label",
        aleatoric_noise_percentage=0.0,
        under_supported_classes="3,5",
    )
    print(f"   Value: {config_zero.aleatoric_noise_percentage}")
    assert config_zero.aleatoric_noise_percentage == 0.0
    print("   ✓ Explicit 0.0 works")
    
    # Test 3: Create config with custom noise percentage
    print("\n✅ Test 3: Create config with aleatoric_noise_percentage=20.0")
    config_custom = TrainingConfig(
        noise_type="worse_label",
        aleatoric_noise_percentage=20.0,
        under_supported_classes="3,5",
    )
    print(f"   Value: {config_custom.aleatoric_noise_percentage}")
    assert config_custom.aleatoric_noise_percentage == 20.0
    print("   ✓ Custom noise percentage works")
    
    # Test 4: Verify YAML dict includes the field
    print("\n✅ Test 4: Verify to_yaml_dict() includes aleatoric_noise_percentage")
    yaml_dict = config_custom.to_yaml_dict()
    assert "aleatoric_noise_percentage" in yaml_dict["data"]
    print(f"   data.aleatoric_noise_percentage: {yaml_dict['data']['aleatoric_noise_percentage']}")
    print("   ✓ Field included in YAML output")
    
    # Test 5: Verify old YAML dict still works (with default)
    print("\n✅ Test 5: Verify old configs get default value in YAML")
    yaml_dict_old = config_old.to_yaml_dict()
    assert yaml_dict_old["data"]["aleatoric_noise_percentage"] == 0.0
    print(f"   data.aleatoric_noise_percentage: {yaml_dict_old['data']['aleatoric_noise_percentage']}")
    print("   ✓ Old configs get 0.0 in YAML (backwards compatible)")
    
    # Test 6: Validate range constraints
    print("\n✅ Test 6: Validate range constraints (0-100)")
    try:
        TrainingConfig(aleatoric_noise_percentage=-1.0)
        print("   ✗ Should have rejected negative value")
        sys.exit(1)
    except Exception:
        print("   ✓ Rejects negative values")
    
    try:
        TrainingConfig(aleatoric_noise_percentage=101.0)
        print("   ✗ Should have rejected value > 100")
        sys.exit(1)
    except Exception:
        print("   ✓ Rejects values > 100")
    
    # Test 7: Verify sweep compatibility (None values)
    print("\n✅ Test 7: Verify sweep compatibility (None for swept params)")
    config_sweep = TrainingConfig(
        aleatoric_noise_percentage=None,  # Will be swept
        under_train_per_class=None,  # Will be swept
    )
    print(f"   aleatoric_noise_percentage: {config_sweep.aleatoric_noise_percentage}")
    print("   ✓ None values work for parameter sweeps")
    
    print("\n" + "=" * 70)
    print("ALL TESTS PASSED ✅")
    print("=" * 70)
    print("\nBackwards Compatibility Summary:")
    print("  ✓ Old configs without field work (default to 0.0)")
    print("  ✓ New configs with field work (0-100 range)")
    print("  ✓ YAML output includes field with correct value")
    print("  ✓ Range validation works (0-100)")
    print("  ✓ Parameter sweeps work (None values)")
    print("\nThe field is fully backwards compatible! 🎉")

if __name__ == "__main__":
    test_backwards_compatibility()

# Made with Bob
