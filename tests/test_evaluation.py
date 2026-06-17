"""Tests for evaluation metrics."""

import pytest
import torch
import numpy as np

from uqlab.evaluation.classification.evaluation import (
    binary_auroc,
    confusion_matrix,
    macro_f1,
    standardize,
)


class TestBinaryAUROC:
    """Tests for binary AUROC calculation."""
    
    def test_perfect_separation(self):
        """Test AUROC with perfect separation."""
        scores = torch.tensor([0.1, 0.2, 0.3, 0.7, 0.8, 0.9])
        positives = torch.tensor([False, False, False, True, True, True])
        
        auroc = binary_auroc(scores, positives)
        assert auroc == 1.0
    
    def test_random_classifier(self):
        """Test AUROC with random scores (should be ~0.5)."""
        torch.manual_seed(42)
        scores = torch.rand(100)
        positives = torch.rand(100) > 0.5
        
        auroc = binary_auroc(scores, positives)
        assert 0.3 < auroc < 0.7  # Should be around 0.5 for random
    
    def test_inverse_separation(self):
        """Test AUROC with inverse separation."""
        scores = torch.tensor([0.9, 0.8, 0.7, 0.3, 0.2, 0.1])
        positives = torch.tensor([False, False, False, True, True, True])
        
        auroc = binary_auroc(scores, positives)
        assert auroc == 0.0
    
    def test_empty_class(self):
        """Test AUROC with empty positive or negative class."""
        scores = torch.tensor([0.1, 0.2, 0.3])
        positives = torch.tensor([True, True, True])  # No negatives
        
        auroc = binary_auroc(scores, positives)
        assert np.isnan(auroc)
    
    def test_ties(self):
        """Test AUROC with tied scores."""
        scores = torch.tensor([0.5, 0.5, 0.5, 0.5])
        positives = torch.tensor([False, False, True, True])
        
        auroc = binary_auroc(scores, positives)
        assert auroc == 0.5  # Ties count as 0.5


class TestConfusionMatrix:
    """Tests for confusion matrix computation."""
    
    def test_perfect_predictions(self):
        """Test confusion matrix with perfect predictions."""
        y_true = torch.tensor([0, 1, 2, 0, 1, 2])
        y_pred = torch.tensor([0, 1, 2, 0, 1, 2])
        
        cm = confusion_matrix(3, y_true, y_pred)
        
        # Should be identity matrix
        expected = torch.tensor([[2, 0, 0], [0, 2, 0], [0, 0, 2]])
        assert torch.equal(cm, expected)
    
    def test_all_wrong(self):
        """Test confusion matrix with all wrong predictions."""
        y_true = torch.tensor([0, 0, 1, 1, 2, 2])
        y_pred = torch.tensor([1, 1, 2, 2, 0, 0])
        
        cm = confusion_matrix(3, y_true, y_pred)
        
        # Diagonal should be all zeros
        assert cm[0, 0] == 0
        assert cm[1, 1] == 0
        assert cm[2, 2] == 0
        
        # Off-diagonal should have counts
        assert cm[0, 1] == 2  # True 0, predicted 1
        assert cm[1, 2] == 2  # True 1, predicted 2
        assert cm[2, 0] == 2  # True 2, predicted 0


class TestMacroF1:
    """Tests for macro-averaged F1 score."""
    
    def test_perfect_predictions(self):
        """Test F1 with perfect predictions."""
        y_true = torch.tensor([0, 1, 2, 0, 1, 2])
        y_pred = torch.tensor([0, 1, 2, 0, 1, 2])
        
        f1 = macro_f1(y_true, y_pred, num_classes=3)
        assert f1 == 1.0
    
    def test_all_wrong(self):
        """Test F1 with all wrong predictions."""
        y_true = torch.tensor([0, 0, 1, 1, 2, 2])
        y_pred = torch.tensor([1, 1, 2, 2, 0, 0])
        
        f1 = macro_f1(y_true, y_pred, num_classes=3)
        assert f1 == 0.0
    
    def test_partial_correct(self):
        """Test F1 with some correct predictions."""
        y_true = torch.tensor([0, 0, 1, 1, 2, 2])
        y_pred = torch.tensor([0, 1, 1, 2, 2, 0])
        
        f1 = macro_f1(y_true, y_pred, num_classes=3)
        assert 0.0 < f1 < 1.0


class TestStandardize:
    """Tests for feature standardization."""
    
    def test_standardization(self):
        """Test that standardization produces zero mean and unit variance."""
        torch.manual_seed(42)
        train_x = torch.randn(100, 10) * 2 + 5  # Mean ~5, std ~2
        test_x = torch.randn(50, 10) * 2 + 5
        
        train_x_std, test_x_std = standardize(train_x, test_x)
        
        # Training set should have mean ~0 and std ~1
        assert torch.abs(train_x_std.mean()) < 0.1
        assert torch.abs(train_x_std.std() - 1.0) < 0.1
        
        # Test set uses training statistics
        assert test_x_std.shape == test_x.shape
    
    def test_constant_features(self):
        """Test standardization with constant features."""
        train_x = torch.ones(100, 10) * 5
        test_x = torch.ones(50, 10) * 5
        
        train_x_std, test_x_std = standardize(train_x, test_x)
        
        # Should handle constant features gracefully (avoid division by zero)
        assert not torch.isnan(train_x_std).any()
        assert not torch.isnan(test_x_std).any()


# Made with Bob