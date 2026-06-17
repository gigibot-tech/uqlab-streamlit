"""
Test script for training data inspection feature
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from uqlab.ui_components.results.training_data_inspection import (
    parse_training_data_stats,
    CIFAR10_CLASSES
)

def test_parse_training_data():
    """Test parsing training data from an existing experiment"""
    
    # Use an existing experiment ID
    experiment_id = "45928dc4-c5e0-4586-82c0-ac4cd4899339"
    
    print(f"Testing training data parsing for experiment: {experiment_id}")
    print("=" * 80)
    
    # Parse training data
    stats = parse_training_data_stats(experiment_id)
    
    if stats is None:
        print("❌ Failed to parse training data - file not found or invalid")
        return False
    
    print("✅ Successfully parsed training data!")
    print()
    
    # Display overall statistics
    print("Overall Statistics:")
    print(f"  Total Samples: {stats['total_samples']:,}")
    print(f"  Clean Samples: {stats['clean_samples']:,}")
    print(f"  Noisy Samples: {stats['noisy_samples']:,}")
    print(f"  Noise Rate: {stats['noise_rate']:.2%}")
    print()
    
    # Display per-class statistics
    print("Per-Class Statistics:")
    print(f"{'Class':<12} {'Total':>8} {'Clean':>8} {'Noisy':>8} {'Noise %':>10}")
    print("-" * 60)
    for class_stat in stats['class_stats']:
        print(
            f"{class_stat['class_name']:<12} "
            f"{class_stat['total_samples']:>8} "
            f"{class_stat['clean_samples']:>8} "
            f"{class_stat['noisy_samples']:>8} "
            f"{class_stat['noise_rate']:>9.1%}"
        )
    print()
    
    # Display sample data info
    print(f"Sample DataFrame shape: {stats['samples_df'].shape}")
    print(f"Sample DataFrame columns: {list(stats['samples_df'].columns)}")
    print()
    
    # Show first few noisy samples
    noisy_samples = stats['samples_df'][stats['samples_df']['is_noisy'] == True].head(5)
    if len(noisy_samples) > 0:
        print("First 5 noisy samples:")
        print(noisy_samples[['dataset_index', 'clean_label', 'noisy_label', 'is_noisy']])
    else:
        print("No noisy samples found in this experiment")
    
    print()
    print("=" * 80)
    print("✅ Test completed successfully!")
    return True


def test_cifar10_classes():
    """Test CIFAR-10 class names"""
    print("\nTesting CIFAR-10 class names:")
    print("=" * 80)
    
    assert len(CIFAR10_CLASSES) == 10, "Should have 10 classes"
    
    for idx, class_name in enumerate(CIFAR10_CLASSES):
        print(f"  {idx}: {class_name}")
    
    print("✅ CIFAR-10 classes verified!")
    print()


if __name__ == "__main__":
    print("Training Data Inspection Feature Test")
    print("=" * 80)
    print()
    
    # Test CIFAR-10 classes
    test_cifar10_classes()
    
    # Test parsing training data
    success = test_parse_training_data()
    
    if success:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)

# Made with Bob
