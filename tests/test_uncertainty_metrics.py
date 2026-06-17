#!/usr/bin/env python3
"""
Test Uncertainty Metrics - Issue #3
====================================

Comprehensive tests for uncertainty quantification metrics:
- MC Dropout utilities
- Uncertainty calculations (entropy, variance, mutual information)
- Deep Ensemble
- Batch uncertainty estimation

Run from project root: python test_uncertainty_metrics.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src" / "uqlab" / "2_models"))

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset

# Import uncertainty functions
from uncertainty import (
    enable_mc_dropout,
    disable_mc_dropout,
    mc_forward_pass,
    calculate_predictive_entropy,
    calculate_mutual_information,
    calculate_predictive_variance,
    calculate_mc_uncertainty,
    calculate_msp_uncertainty,
    DeepEnsemble,
    batch_uncertainty_estimation,
)


class SimpleModel(nn.Module):
    """Simple model for testing."""
    def __init__(self, input_dim=10, hidden_dim=20, output_dim=3, dropout=0.3):
        super().__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.dropout = nn.Dropout(dropout)
        self.fc2 = nn.Linear(hidden_dim, output_dim)
    
    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)
        return x


def create_dummy_data(n_samples=100, input_dim=10, output_dim=3, batch_size=32):
    """Create dummy data for testing."""
    X = torch.randn(n_samples, input_dim)
    y = torch.randint(0, output_dim, (n_samples,))
    dataset = TensorDataset(X, y)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)
    return dataloader, X, y


def test_mc_dropout_enable_disable():
    """Test MC Dropout enable/disable functionality."""
    print("\n" + "="*70)
    print("TEST 1: MC Dropout Enable/Disable")
    print("="*70)
    
    model = SimpleModel()
    
    # Initially in training mode
    model.train()
    dropout_training_before = model.dropout.training
    
    # Switch to eval mode
    model.eval()
    dropout_training_eval = model.dropout.training
    
    # Enable MC dropout
    enable_mc_dropout(model)
    dropout_training_mc = model.dropout.training
    
    # Disable MC dropout
    disable_mc_dropout(model)
    dropout_training_disabled = model.dropout.training
    
    assert dropout_training_before == True, "❌ Dropout should be in training mode initially"
    assert dropout_training_eval == False, "❌ Dropout should be disabled in eval mode"
    assert dropout_training_mc == True, "❌ MC Dropout should enable dropout"
    assert dropout_training_disabled == False, "❌ Disable should turn off dropout"
    
    print("✅ PASSED: MC Dropout enable/disable works correctly")
    print(f"   - Training mode: {dropout_training_before}")
    print(f"   - Eval mode: {dropout_training_eval}")
    print(f"   - MC enabled: {dropout_training_mc}")
    print(f"   - MC disabled: {dropout_training_disabled}")
    return True


def test_mc_forward_pass():
    """Test MC forward pass produces correct shape and variability."""
    print("\n" + "="*70)
    print("TEST 2: MC Forward Pass")
    print("="*70)
    
    model = SimpleModel(input_dim=10, output_dim=3)
    model.eval()
    
    X = torch.randn(32, 10)
    n_passes = 20
    
    # MC forward pass
    predictions = mc_forward_pass(model, X, n_passes=n_passes)
    
    # Check shape
    expected_shape = (n_passes, 32, 3)
    assert predictions.shape == expected_shape, \
        f"❌ Shape mismatch: {predictions.shape} vs {expected_shape}"
    
    # Check probabilities sum to 1
    prob_sums = predictions.sum(dim=-1)
    assert torch.allclose(prob_sums, torch.ones_like(prob_sums), atol=1e-5), \
        "❌ Probabilities should sum to 1"
    
    # Check variability (predictions should differ across passes)
    std_across_passes = predictions.std(dim=0).mean()
    assert std_across_passes > 0, "❌ MC predictions should vary across passes"
    
    print("✅ PASSED: MC forward pass works correctly")
    print(f"   - Output shape: {predictions.shape}")
    print(f"   - Probability sums: {prob_sums[0, 0]:.6f} (should be ~1.0)")
    print(f"   - Std across passes: {std_across_passes:.6f} (should be > 0)")
    return True


def test_predictive_entropy():
    """Test predictive entropy calculation."""
    print("\n" + "="*70)
    print("TEST 3: Predictive Entropy")
    print("="*70)
    
    # Create test predictions
    # High confidence: [0.9, 0.05, 0.05]
    high_conf = torch.tensor([[0.9, 0.05, 0.05]])
    # Low confidence: [0.33, 0.33, 0.34]
    low_conf = torch.tensor([[0.33, 0.33, 0.34]])
    
    entropy_high = calculate_predictive_entropy(high_conf)
    entropy_low = calculate_predictive_entropy(low_conf)
    
    # Low confidence should have higher entropy
    assert entropy_low > entropy_high, \
        "❌ Low confidence should have higher entropy"
    
    # Test with MC predictions
    mc_preds = torch.randn(20, 10, 3).softmax(dim=-1)
    entropy_mc = calculate_predictive_entropy(mc_preds)
    
    assert entropy_mc.shape == (10,), f"❌ Entropy shape should be (10,), got {entropy_mc.shape}"
    assert (entropy_mc >= 0).all(), "❌ Entropy should be non-negative"
    
    print("✅ PASSED: Predictive entropy calculation works")
    print(f"   - High confidence entropy: {entropy_high.item():.4f}")
    print(f"   - Low confidence entropy: {entropy_low.item():.4f}")
    print(f"   - MC entropy range: [{entropy_mc.min():.4f}, {entropy_mc.max():.4f}]")
    return True


def test_mutual_information():
    """Test mutual information calculation."""
    print("\n" + "="*70)
    print("TEST 4: Mutual Information (Epistemic Uncertainty)")
    print("="*70)
    
    # Create MC predictions with varying disagreement
    # High disagreement (high epistemic uncertainty)
    high_disagreement = torch.stack([
        torch.tensor([[0.8, 0.1, 0.1]]),
        torch.tensor([[0.1, 0.8, 0.1]]),
        torch.tensor([[0.1, 0.1, 0.8]]),
    ])
    
    # Low disagreement (low epistemic uncertainty)
    low_disagreement = torch.stack([
        torch.tensor([[0.7, 0.2, 0.1]]),
        torch.tensor([[0.75, 0.15, 0.1]]),
        torch.tensor([[0.72, 0.18, 0.1]]),
    ])
    
    mi_high = calculate_mutual_information(high_disagreement)
    mi_low = calculate_mutual_information(low_disagreement)
    
    # High disagreement should have higher MI
    assert mi_high > mi_low, \
        "❌ High disagreement should have higher mutual information"
    
    # Test with random MC predictions
    mc_preds = torch.randn(20, 10, 3).softmax(dim=-1)
    mi = calculate_mutual_information(mc_preds)
    
    assert mi.shape == (10,), f"❌ MI shape should be (10,), got {mi.shape}"
    assert (mi >= 0).all(), "❌ Mutual information should be non-negative"
    
    print("✅ PASSED: Mutual information calculation works")
    print(f"   - High disagreement MI: {mi_high.item():.4f}")
    print(f"   - Low disagreement MI: {mi_low.item():.4f}")
    print(f"   - Random MC MI range: [{mi.min():.4f}, {mi.max():.4f}]")
    return True


def test_predictive_variance():
    """Test predictive variance calculation."""
    print("\n" + "="*70)
    print("TEST 5: Predictive Variance")
    print("="*70)
    
    # Create MC predictions
    mc_preds = torch.randn(20, 10, 3).softmax(dim=-1)
    variance = calculate_predictive_variance(mc_preds)
    
    assert variance.shape == (10,), f"❌ Variance shape should be (10,), got {variance.shape}"
    assert (variance >= 0).all(), "❌ Variance should be non-negative"
    
    # Test that variance increases with disagreement
    # Low variance predictions
    low_var_preds = torch.ones(20, 1, 3) / 3 + torch.randn(20, 1, 3) * 0.01
    low_var_preds = low_var_preds.softmax(dim=-1)
    
    # High variance predictions
    high_var_preds = torch.randn(20, 1, 3) * 2
    high_var_preds = high_var_preds.softmax(dim=-1)
    
    var_low = calculate_predictive_variance(low_var_preds)
    var_high = calculate_predictive_variance(high_var_preds)
    
    assert var_high > var_low, "❌ High disagreement should have higher variance"
    
    print("✅ PASSED: Predictive variance calculation works")
    print(f"   - Variance range: [{variance.min():.6f}, {variance.max():.6f}]")
    print(f"   - Low disagreement variance: {var_low.item():.6f}")
    print(f"   - High disagreement variance: {var_high.item():.6f}")
    return True


def test_mc_uncertainty_comprehensive():
    """Test comprehensive MC uncertainty calculation."""
    print("\n" + "="*70)
    print("TEST 6: Comprehensive MC Uncertainty Metrics")
    print("="*70)
    
    # Create MC predictions
    mc_preds = torch.randn(20, 10, 3).softmax(dim=-1)
    
    uncertainty = calculate_mc_uncertainty(mc_preds)
    
    # Check all metrics are present
    required_keys = ['mean_prediction', 'variance', 'entropy', 'mutual_info']
    for key in required_keys:
        assert key in uncertainty, f"❌ Missing key: {key}"
    
    # Check shapes
    assert uncertainty['mean_prediction'].shape == (10, 3), \
        f"❌ Mean prediction shape should be (10, 3)"
    assert uncertainty['variance'].shape == (10,), \
        f"❌ Variance shape should be (10,)"
    assert uncertainty['entropy'].shape == (10,), \
        f"❌ Entropy shape should be (10,)"
    assert uncertainty['mutual_info'].shape == (10,), \
        f"❌ Mutual info shape should be (10,)"
    
    # Check mean prediction sums to 1
    pred_sums = uncertainty['mean_prediction'].sum(dim=-1)
    assert torch.allclose(pred_sums, torch.ones_like(pred_sums), atol=1e-5), \
        "❌ Mean predictions should sum to 1"
    
    print("✅ PASSED: Comprehensive MC uncertainty metrics work")
    print(f"   - Mean prediction shape: {uncertainty['mean_prediction'].shape}")
    print(f"   - Variance range: [{uncertainty['variance'].min():.6f}, {uncertainty['variance'].max():.6f}]")
    print(f"   - Entropy range: [{uncertainty['entropy'].min():.4f}, {uncertainty['entropy'].max():.4f}]")
    print(f"   - Mutual info range: [{uncertainty['mutual_info'].min():.4f}, {uncertainty['mutual_info'].max():.4f}]")
    return True


def test_msp_uncertainty():
    """Test Maximum Softmax Probability uncertainty."""
    print("\n" + "="*70)
    print("TEST 7: MSP Uncertainty")
    print("="*70)
    
    # High confidence prediction
    high_conf = torch.tensor([[0.9, 0.05, 0.05]])
    # Low confidence prediction
    low_conf = torch.tensor([[0.4, 0.3, 0.3]])
    
    msp_high = calculate_msp_uncertainty(high_conf)
    msp_low = calculate_msp_uncertainty(low_conf)
    
    # Low confidence should have higher MSP uncertainty
    assert msp_low > msp_high, \
        "❌ Low confidence should have higher MSP uncertainty"
    
    # MSP should be in [0, 1]
    assert 0 <= msp_high <= 1, "❌ MSP should be in [0, 1]"
    assert 0 <= msp_low <= 1, "❌ MSP should be in [0, 1]"
    
    print("✅ PASSED: MSP uncertainty calculation works")
    print(f"   - High confidence MSP: {msp_high.item():.4f} (lower is better)")
    print(f"   - Low confidence MSP: {msp_low.item():.4f} (higher uncertainty)")
    return True


def test_deep_ensemble():
    """Test Deep Ensemble functionality."""
    print("\n" + "="*70)
    print("TEST 8: Deep Ensemble")
    print("="*70)
    
    # Create ensemble of 3 models
    models = [SimpleModel(input_dim=10, output_dim=3) for _ in range(3)]
    ensemble = DeepEnsemble(models)
    
    X = torch.randn(32, 10)
    
    # Test forward pass
    logits = ensemble(X)
    assert logits.shape == (32, 3), f"❌ Logits shape should be (32, 3), got {logits.shape}"
    
    # Test prediction with uncertainty
    predictions, uncertainty = ensemble.predict_with_uncertainty(X)
    
    assert predictions.shape == (32, 3), \
        f"❌ Predictions shape should be (32, 3), got {predictions.shape}"
    assert uncertainty.shape == (32,), \
        f"❌ Uncertainty shape should be (32,), got {uncertainty.shape}"
    
    # Check predictions sum to 1
    pred_sums = predictions.sum(dim=-1)
    assert torch.allclose(pred_sums, torch.ones_like(pred_sums), atol=1e-5), \
        "❌ Predictions should sum to 1"
    
    # Check uncertainty is non-negative
    assert (uncertainty >= 0).all(), "❌ Uncertainty should be non-negative"
    
    # Test get_all_predictions
    all_preds = ensemble.get_all_predictions(X)
    assert all_preds.shape == (3, 32, 3), \
        f"❌ All predictions shape should be (3, 32, 3), got {all_preds.shape}"
    
    print("✅ PASSED: Deep Ensemble works correctly")
    print(f"   - Ensemble size: {ensemble.n_models}")
    print(f"   - Prediction shape: {predictions.shape}")
    print(f"   - Uncertainty range: [{uncertainty.min():.4f}, {uncertainty.max():.4f}]")
    return True


def test_batch_uncertainty_estimation():
    """Test batch uncertainty estimation."""
    print("\n" + "="*70)
    print("TEST 9: Batch Uncertainty Estimation")
    print("="*70)
    
    model = SimpleModel(input_dim=10, output_dim=3)
    dataloader, X, y = create_dummy_data(n_samples=100, input_dim=10, output_dim=3, batch_size=32)
    
    # Test MC Dropout method
    results_mc = batch_uncertainty_estimation(
        model, dataloader, method='mc_dropout', n_passes=10, device='cpu'
    )
    
    assert 'predictions' in results_mc, "❌ Missing predictions"
    assert 'uncertainty' in results_mc, "❌ Missing uncertainty"
    assert 'variance' in results_mc, "❌ Missing variance"
    assert 'mutual_info' in results_mc, "❌ Missing mutual_info"
    assert 'labels' in results_mc, "❌ Missing labels"
    
    assert results_mc['predictions'].shape == (100, 3), \
        f"❌ Predictions shape should be (100, 3)"
    assert results_mc['uncertainty'].shape == (100,), \
        f"❌ Uncertainty shape should be (100,)"
    
    # Test MSP method
    results_msp = batch_uncertainty_estimation(
        model, dataloader, method='msp', device='cpu'
    )
    
    assert 'predictions' in results_msp, "❌ Missing predictions"
    assert 'uncertainty' in results_msp, "❌ Missing uncertainty"
    assert 'labels' in results_msp, "❌ Missing labels"
    
    print("✅ PASSED: Batch uncertainty estimation works")
    print(f"   - MC Dropout uncertainty range: [{results_mc['uncertainty'].min():.4f}, {results_mc['uncertainty'].max():.4f}]")
    print(f"   - MSP uncertainty range: [{results_msp['uncertainty'].min():.4f}, {results_msp['uncertainty'].max():.4f}]")
    return True


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("Uncertainty Metrics Test Suite - Issue #3")
    print("="*70)
    print("\nTesting uncertainty quantification metrics:")
    print("  - MC Dropout utilities")
    print("  - Uncertainty calculations (entropy, variance, MI)")
    print("  - Deep Ensemble")
    print("  - Batch uncertainty estimation")
    print()
    
    tests = [
        ("MC Dropout Enable/Disable", test_mc_dropout_enable_disable),
        ("MC Forward Pass", test_mc_forward_pass),
        ("Predictive Entropy", test_predictive_entropy),
        ("Mutual Information", test_mutual_information),
        ("Predictive Variance", test_predictive_variance),
        ("Comprehensive MC Uncertainty", test_mc_uncertainty_comprehensive),
        ("MSP Uncertainty", test_msp_uncertainty),
        ("Deep Ensemble", test_deep_ensemble),
        ("Batch Uncertainty Estimation", test_batch_uncertainty_estimation),
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
            import traceback
            traceback.print_exc()
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
        print("\n🎉 All tests passed! Uncertainty metrics work correctly.")
        print("\nKey findings:")
        print("  ✅ MC Dropout enable/disable works correctly")
        print("  ✅ MC forward pass produces valid predictions")
        print("  ✅ Predictive entropy calculation is correct")
        print("  ✅ Mutual information (epistemic uncertainty) works")
        print("  ✅ Predictive variance calculation is correct")
        print("  ✅ Comprehensive uncertainty metrics work")
        print("  ✅ MSP uncertainty calculation works")
        print("  ✅ Deep Ensemble implementation is correct")
        print("  ✅ Batch uncertainty estimation works")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
