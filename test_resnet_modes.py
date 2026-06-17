#!/usr/bin/env python3
"""
Test ResNet18 Training Modes - Issue #1
========================================

Tests both training modes for ResNet18MCDropout:
1. Feature-space mode (freeze_backbone=True) - Only train classifier
2. End-to-end mode (freeze_backbone=False) - Train entire network

Run from project root: python test_resnet_modes.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))
# Add 2_models directory to path
sys.path.insert(0, str(Path(__file__).parent / "src" / "uqlab" / "2_models"))

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

# Import the model from factory.py in 2_models directory
from factory import ResNet18MCDropout


def create_dummy_data(num_samples=100, batch_size=32):
    """Create dummy CIFAR-10 style data for testing."""
    X = torch.randn(num_samples, 3, 32, 32)
    y = torch.randint(0, 10, (num_samples,))
    dataset = TensorDataset(X, y)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    return dataloader


def test_feature_space_mode_freezes_backbone():
    """Test that feature-space mode freezes backbone parameters."""
    print("\n" + "="*70)
    print("TEST 1: Feature-space mode freezes backbone")
    print("="*70)
    
    model = ResNet18MCDropout(
        num_classes=10,
        dropout=0.3,
        pretrained=False,
        freeze_backbone=True
    )
    
    # Check that backbone parameters are frozen
    backbone_params_frozen = all(
        not param.requires_grad 
        for param in model.backbone.parameters()
    )
    
    # Check that classifier parameters are trainable
    classifier_params_trainable = all(
        param.requires_grad 
        for param in model.classifier.parameters()
    )
    
    assert backbone_params_frozen, "❌ Backbone parameters should be frozen"
    assert classifier_params_trainable, "❌ Classifier parameters should be trainable"
    
    print("✅ PASSED: Backbone frozen, classifier trainable")
    return True


def test_end_to_end_mode_trains_all():
    """Test that end-to-end mode trains all parameters."""
    print("\n" + "="*70)
    print("TEST 2: End-to-end mode trains all parameters")
    print("="*70)
    
    model = ResNet18MCDropout(
        num_classes=10,
        dropout=0.3,
        pretrained=False,
        freeze_backbone=False
    )
    
    # Check that all parameters are trainable
    all_params_trainable = all(
        param.requires_grad 
        for param in model.parameters()
    )
    
    assert all_params_trainable, "❌ All parameters should be trainable"
    
    print("✅ PASSED: All parameters trainable")
    return True


def test_feature_space_training_step():
    """Test that feature-space mode can perform training step."""
    print("\n" + "="*70)
    print("TEST 3: Feature-space training step")
    print("="*70)
    
    model = ResNet18MCDropout(
        num_classes=10,
        dropout=0.3,
        pretrained=False,
        freeze_backbone=True
    )
    
    # Setup training
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    model.train()
    
    # Get one batch
    dataloader = create_dummy_data()
    X, y = next(iter(dataloader))
    
    # Forward pass
    logits = model(X)
    loss = criterion(logits, y)
    
    # Backward pass
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    
    # Check that only classifier was updated
    backbone_has_gradients = any(
        param.grad is not None and param.grad.abs().sum() > 0
        for param in model.backbone.parameters()
    )
    
    classifier_has_gradients = any(
        param.grad is not None and param.grad.abs().sum() > 0
        for param in model.classifier.parameters()
    )
    
    assert not backbone_has_gradients, "❌ Backbone should not have gradients"
    assert classifier_has_gradients, "❌ Classifier should have gradients"
    
    print(f"✅ PASSED: Training step successful, Loss={loss.item():.4f}")
    print(f"   - Backbone gradients: None (frozen)")
    print(f"   - Classifier gradients: Present (trainable)")
    return True


def test_end_to_end_training_step():
    """Test that end-to-end mode can perform training step."""
    print("\n" + "="*70)
    print("TEST 4: End-to-end training step")
    print("="*70)
    
    model = ResNet18MCDropout(
        num_classes=10,
        dropout=0.3,
        pretrained=False,
        freeze_backbone=False
    )
    
    # Setup training
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    model.train()
    
    # Get one batch
    dataloader = create_dummy_data()
    X, y = next(iter(dataloader))
    
    # Forward pass
    logits = model(X)
    loss = criterion(logits, y)
    
    # Backward pass
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    
    # Check that both backbone and classifier were updated
    backbone_has_gradients = any(
        param.grad is not None and param.grad.abs().sum() > 0
        for param in model.backbone.parameters()
    )
    
    classifier_has_gradients = any(
        param.grad is not None and param.grad.abs().sum() > 0
        for param in model.classifier.parameters()
    )
    
    assert backbone_has_gradients, "❌ Backbone should have gradients"
    assert classifier_has_gradients, "❌ Classifier should have gradients"
    
    print(f"✅ PASSED: Training step successful, Loss={loss.item():.4f}")
    print(f"   - Backbone gradients: Present (trainable)")
    print(f"   - Classifier gradients: Present (trainable)")
    return True


def test_mc_dropout_inference():
    """Test MC Dropout inference works in both modes."""
    print("\n" + "="*70)
    print("TEST 5: MC Dropout inference")
    print("="*70)
    
    for freeze_backbone in [True, False]:
        mode_name = "feature-space" if freeze_backbone else "end-to-end"
        
        model = ResNet18MCDropout(
            num_classes=10,
            dropout=0.3,
            pretrained=False,
            freeze_backbone=freeze_backbone
        )
        
        model.eval()
        
        # Get one batch
        dataloader = create_dummy_data()
        X, y = next(iter(dataloader))
        
        # MC Dropout inference
        mc_probs = model.mc_forward(X, n_passes=5)
        
        # Check shape: [n_passes, batch_size, num_classes]
        expected_shape = (5, X.shape[0], 10)
        assert mc_probs.shape == expected_shape, \
            f"❌ MC Dropout output shape incorrect: {mc_probs.shape} vs {expected_shape}"
        
        # Check probabilities sum to 1
        prob_sums = mc_probs.sum(dim=-1)
        assert torch.allclose(prob_sums, torch.ones_like(prob_sums), atol=1e-5), \
            f"❌ Probabilities should sum to 1"
        
        print(f"✅ PASSED: MC Dropout works in {mode_name} mode")
        print(f"   - Output shape: {mc_probs.shape}")
        print(f"   - Probability sums: {prob_sums[0, 0]:.6f} (should be ~1.0)")
    
    return True


def test_feature_extraction():
    """Test feature extraction works in both modes."""
    print("\n" + "="*70)
    print("TEST 6: Feature extraction")
    print("="*70)
    
    for freeze_backbone in [True, False]:
        mode_name = "feature-space" if freeze_backbone else "end-to-end"
        
        model = ResNet18MCDropout(
            num_classes=10,
            dropout=0.3,
            pretrained=False,
            freeze_backbone=freeze_backbone
        )
        
        model.eval()
        
        # Get one batch
        dataloader = create_dummy_data()
        X, y = next(iter(dataloader))
        
        # Extract features
        with torch.no_grad():
            features = model.extract_features(X)
        
        # Check shape: [batch_size, 512] (ResNet18 feature dim)
        expected_shape = (X.shape[0], 512)
        assert features.shape == expected_shape, \
            f"❌ Feature shape incorrect: {features.shape} vs {expected_shape}"
        
        print(f"✅ PASSED: Feature extraction works in {mode_name} mode")
        print(f"   - Feature shape: {features.shape}")
    
    return True


def test_model_output_consistency():
    """Test that model outputs are consistent across modes."""
    print("\n" + "="*70)
    print("TEST 7: Model output consistency")
    print("="*70)
    
    # Create two models with same initialization
    torch.manual_seed(42)
    model_frozen = ResNet18MCDropout(
        num_classes=10,
        dropout=0.0,  # No dropout for deterministic test
        pretrained=False,
        freeze_backbone=True
    )
    
    torch.manual_seed(42)
    model_full = ResNet18MCDropout(
        num_classes=10,
        dropout=0.0,
        pretrained=False,
        freeze_backbone=False
    )
    
    # Get one batch
    dataloader = create_dummy_data()
    X, y = next(iter(dataloader))
    
    # Forward pass (eval mode, no dropout)
    model_frozen.eval()
    model_full.eval()
    
    with torch.no_grad():
        logits_frozen = model_frozen(X)
        logits_full = model_full(X)
    
    # Outputs should be identical (same initialization, no training yet)
    max_diff = (logits_frozen - logits_full).abs().max().item()
    assert torch.allclose(logits_frozen, logits_full, atol=1e-5), \
        f"❌ Model outputs should be identical before training (max diff: {max_diff})"
    
    print("✅ PASSED: Model outputs consistent across modes before training")
    print(f"   - Max difference: {max_diff:.2e} (should be ~0)")
    return True


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("ResNet18 Training Modes Test Suite - Issue #1")
    print("="*70)
    print("\nTesting ResNet18MCDropout with:")
    print("  - Feature-space mode (freeze_backbone=True)")
    print("  - End-to-end mode (freeze_backbone=False)")
    print()
    
    tests = [
        ("Feature-space mode freezes backbone", test_feature_space_mode_freezes_backbone),
        ("End-to-end mode trains all parameters", test_end_to_end_mode_trains_all),
        ("Feature-space training step", test_feature_space_training_step),
        ("End-to-end training step", test_end_to_end_training_step),
        ("MC Dropout inference", test_mc_dropout_inference),
        ("Feature extraction", test_feature_extraction),
        ("Model output consistency", test_model_output_consistency),
    ]
    
    passed = 0
    failed = 0
    errors = []
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"\n❌ FAILED: {e}")
            failed += 1
            errors.append((test_name, str(e)))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Total tests: {len(tests)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    if errors:
        print("\nFailed tests:")
        for test_name, error in errors:
            print(f"  - {test_name}: {error}")
    
    print("="*70)
    
    if failed == 0:
        print("\n🎉 All tests passed! ResNet18 training modes work correctly.")
        print("\nKey findings:")
        print("  ✅ Feature-space mode correctly freezes backbone")
        print("  ✅ End-to-end mode trains all parameters")
        print("  ✅ Both modes support MC Dropout inference")
        print("  ✅ Both modes support feature extraction")
        print("  ✅ Models produce consistent outputs before training")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
