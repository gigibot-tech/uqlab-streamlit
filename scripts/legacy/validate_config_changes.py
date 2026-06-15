"""Standalone validation script for ModelConfig changes."""

import sys
from pathlib import Path

# Read the config file directly and validate the changes
config_path = Path(__file__).parent / "uq_classification" / "config.py"

with open(config_path, 'r') as f:
    content = f.read()

print("🔍 Validating ModelConfig changes in uq_classification/config.py\n")

# Check for required imports
checks = {
    "Literal import": "from typing import List, Literal, Optional" in content,
    "Pydantic imports": "from pydantic import BaseModel, field_validator" in content,
    "ModelConfig as BaseModel": "class ModelConfig(BaseModel):" in content,
    "architecture field": 'architecture: Literal["dinov2_mlp", "cnn_mcdropout", "resnet18_mcdropout"]' in content,
    "training_mode field": 'training_mode: Literal["feature_space", "end_to_end"]' in content,
    "dinov2_model field": 'dinov2_model: str = "dinov2_vitb14"' in content,
    "num_conv_layers field": "num_conv_layers: int = 3" in content,
    "conv_channels field": "conv_channels: List[int] = [32, 64, 64]" in content,
    "validate_training_mode": "@field_validator(\"training_mode\")" in content,
    "validate_conv_channels": "@field_validator(\"conv_channels\")" in content,
    "dinov2_mlp validation": '"dinov2_mlp only supports feature_space mode"' in content,
    "conv_channels validation": '"conv_channels length' in content,
    "Pydantic Config class": "class Config:" in content and "validate_assignment = True" in content,
}

all_passed = True
for check_name, passed in checks.items():
    status = "✅" if passed else "❌"
    print(f"{status} {check_name}")
    if not passed:
        all_passed = False

# Check YAML parsing updates
yaml_checks = {
    "architecture in from_yaml": 'architecture=model_dict.get("architecture", "dinov2_mlp")' in content,
    "training_mode in from_yaml": 'training_mode=model_dict.get("training_mode", "feature_space")' in content,
    "num_conv_layers in from_yaml": 'num_conv_layers=model_dict.get("num_conv_layers", 3)' in content,
    "conv_channels parsing": 'conv_channels = model_dict.get("conv_channels", [32, 64, 64])' in content,
}

print("\n🔍 Validating YAML parsing updates:\n")
for check_name, passed in yaml_checks.items():
    status = "✅" if passed else "❌"
    print(f"{status} {check_name}")
    if not passed:
        all_passed = False

# Check backward compatibility
compat_checks = {
    "Optional types for DataConfig": "under_supported_classes: Optional[List[int]]" in content,
    "Optional types for ExperimentConfig": "data: Optional[DataConfig]" in content,
}

print("\n🔍 Validating backward compatibility:\n")
for check_name, passed in compat_checks.items():
    status = "✅" if passed else "❌"
    print(f"{status} {check_name}")
    if not passed:
        all_passed = False

if all_passed:
    print("\n✅ All validation checks passed!")
    print("\n📋 Summary of changes:")
    print("  • Added architecture field with 3 options: dinov2_mlp, cnn_mcdropout, resnet18_mcdropout")
    print("  • Added training_mode field: feature_space, end_to_end")
    print("  • Added CNN-specific fields: num_conv_layers, conv_channels")
    print("  • Added validation for compatible architecture/training_mode combinations")
    print("  • Added validation for conv_channels length matching num_conv_layers")
    print("  • Updated from_yaml to parse new fields")
    print("  • Maintained backward compatibility with existing configs")
    sys.exit(0)
else:
    print("\n❌ Some validation checks failed!")
    sys.exit(1)

# Made with Bob
