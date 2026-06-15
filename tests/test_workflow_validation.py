"""
Unit tests for workflow configuration validation.
"""

import pytest
from pydantic import ValidationError

from uqlab.shared.config.workflow_validation import (
    WorkflowConfig,
    WorkflowDatasetConfig,
    WorkflowTrainingConfig,
    WorkflowUncertaintyConfig,
    WorkflowEvaluationConfig,
    validate_workflow,
    get_validation_errors,
)


class TestDatasetConfig:
    """Test dataset configuration validation."""
    
    def test_valid_clean_dataset(self):
        """Test valid clean dataset config."""
        config = WorkflowDatasetConfig(
            dataset_name="cifar10",
            noise_type="clean_label",
            stats={"total_samples": 50000, "num_classes": 10}
        )
        assert config.noise_type == "clean_label"
    
    def test_valid_noisy_dataset(self):
        """Test valid noisy dataset config."""
        config = WorkflowDatasetConfig(
            dataset_name="cifar10n",
            noise_type="worse_label",
            stats={"noise_rate": 0.4}
        )
        assert config.stats["noise_rate"] == 0.4
    
    def test_invalid_noise_type(self):
        """Test invalid noise type."""
        with pytest.raises(ValidationError) as exc_info:
            WorkflowDatasetConfig(
                dataset_name="cifar10",
                noise_type="invalid_noise",
                stats={}
            )
        assert "noise_type must be one of" in str(exc_info.value)
    
    def test_invalid_noise_rate(self):
        """Test invalid noise rate."""
        with pytest.raises(ValidationError) as exc_info:
            WorkflowDatasetConfig(
                dataset_name="cifar10n",
                noise_type="worse_label",
                stats={"noise_rate": 1.5}  # > 1.0
            )
        assert "noise_rate must be in [0, 1]" in str(exc_info.value)


class TestTrainingConfig:
    """Test training configuration validation."""
    
    def test_valid_dinov2_config(self):
        """Test valid DINOv2 config."""
        config = WorkflowTrainingConfig(
            model_architecture="dinov2-small",
            hidden_dim=256,
            dropout=0.2,
            epochs=12,
            learning_rate=0.001,
            batch_size=256
        )
        assert config.model_architecture == "dinov2-small"
    
    def test_valid_resnet_config(self):
        """Test valid ResNet config."""
        config = WorkflowTrainingConfig(
            model_architecture="resnet18",
            hidden_dim=512,
            dropout=0.1,
            epochs=50,
            learning_rate=0.0001,
            batch_size=128
        )
        assert config.model_architecture == "resnet18"
    
    def test_invalid_architecture(self):
        """Test invalid architecture."""
        with pytest.raises(ValidationError) as exc_info:
            WorkflowTrainingConfig(
                model_architecture="vgg16",  # Not supported
                hidden_dim=256,
                dropout=0.2,
                epochs=12,
                learning_rate=0.001,
                batch_size=256
            )
        assert "model_architecture must be one of" in str(exc_info.value)
    
    def test_checkpoint_consistency_valid(self):
        """Test valid checkpoint configuration."""
        config = WorkflowTrainingConfig(
            use_checkpoint=True,
            checkpoint_id="exp_123",
            model_architecture="dinov2-small",
            hidden_dim=256,
            dropout=0.2,
            epochs=12,
            learning_rate=0.001,
            batch_size=256
        )
        assert config.checkpoint_id == "exp_123"
    
    def test_checkpoint_consistency_invalid(self):
        """Test invalid checkpoint configuration."""
        with pytest.raises(ValidationError) as exc_info:
            WorkflowTrainingConfig(
                use_checkpoint=True,
                checkpoint_id=None,  # Missing!
                model_architecture="dinov2-small",
                hidden_dim=256,
                dropout=0.2,
                epochs=12,
                learning_rate=0.001,
                batch_size=256
            )
        assert "use_checkpoint=True but checkpoint_id is None" in str(exc_info.value)


class TestUncertaintyConfig:
    """Test uncertainty configuration validation."""
    
    def test_valid_epistemic_config(self):
        """Test valid epistemic config."""
        config = WorkflowUncertaintyConfig(
            epistemic_enabled=True,
            under_supported="random:2",
            under_train_per_class=50,
            regular_train_per_class=300,
            aleatoric_enabled=False
        )
        assert config.under_supported == "random:2"
    
    def test_valid_custom_classes(self):
        """Test valid custom under-supported classes."""
        config = WorkflowUncertaintyConfig(
            epistemic_enabled=True,
            under_supported="0,1,2",
            under_train_per_class=50,
            regular_train_per_class=300,
            aleatoric_enabled=False
        )
        assert config.under_supported == "0,1,2"
    
    def test_invalid_under_supported_format(self):
        """Test invalid under_supported format."""
        with pytest.raises(ValidationError) as exc_info:
            WorkflowUncertaintyConfig(
                epistemic_enabled=True,
                under_supported="random:15",  # > 9
                under_train_per_class=50,
                regular_train_per_class=300,
                aleatoric_enabled=False
            )
        assert "random:N must have N in [1, 9]" in str(exc_info.value)
    
    def test_sweep_consistency_valid(self):
        """Test valid sweep configuration."""
        config = WorkflowUncertaintyConfig(
            epistemic_enabled=True,
            under_supported="random:2",
            under_train_per_class=50,
            regular_train_per_class=300,
            aleatoric_enabled=True,
            custom_noise_rate=0.1,
            sweep_enabled=True,
            sweep_kind="label_noise",
            aleatoric_sweep_enabled=True,
            aleatoric_sweep_values=[0.0, 0.1, 0.2, 0.3]
        )
        assert config.sweep_kind == "label_noise"
    
    def test_sweep_consistency_invalid(self):
        """Test invalid sweep configuration."""
        with pytest.raises(ValidationError) as exc_info:
            WorkflowUncertaintyConfig(
                epistemic_enabled=True,
                under_supported="random:2",
                under_train_per_class=50,
                regular_train_per_class=300,
                aleatoric_enabled=False,
                sweep_enabled=True,
                sweep_kind="label_noise",
                aleatoric_sweep_enabled=False  # Inconsistent!
            )
        assert "sweep_kind=label_noise but aleatoric_sweep_enabled=False" in str(exc_info.value)


class TestWorkflowConfig:
    """Test complete workflow configuration validation."""
    
    def test_valid_workflow_dataset_noise(self):
        """Test valid workflow with dataset noise."""
        workflow = {
            "step1_complete": True,
            "step2_complete": True,
            "step3_complete": True,
            "step4_complete": True,
            "dataset_config": {
                "dataset_name": "cifar10n",
                "noise_type": "worse_label",
                "stats": {"noise_rate": 0.4}
            },
            "training_config": {
                "use_checkpoint": False,
                "model_architecture": "dinov2-small",
                "hidden_dim": 256,
                "dropout": 0.2,
                "epochs": 12,
                "learning_rate": 0.001,
                "batch_size": 256
            },
            "uncertainty_config": {
                "epistemic_enabled": True,
                "under_supported": "random:2",
                "under_train_per_class": 50,
                "regular_train_per_class": 300,
                "aleatoric_enabled": True,  # Using dataset noise
                "custom_noise_rate": None,  # No custom noise
                "sweep_enabled": False
            },
            "evaluation_config": {
                "eval_per_group": 100,
                "mc_passes": 20,
                "selected_signals": ["inverse_mass", "dominance"]
            }
        }
        
        config = validate_workflow(workflow)
        assert config.uncertainty_config.aleatoric_enabled
        assert config.dataset_config.noise_type == "worse_label"
    
    def test_valid_workflow_custom_noise(self):
        """Test valid workflow with custom noise."""
        workflow = {
            "step1_complete": True,
            "step2_complete": True,
            "step3_complete": True,
            "step4_complete": True,
            "dataset_config": {
                "dataset_name": "cifar10",
                "noise_type": "clean_label",
                "stats": {}
            },
            "training_config": {
                "use_checkpoint": False,
                "model_architecture": "resnet18",
                "hidden_dim": 512,
                "dropout": 0.1,
                "epochs": 50,
                "learning_rate": 0.0001,
                "batch_size": 128
            },
            "uncertainty_config": {
                "epistemic_enabled": True,
                "under_supported": "0,1",
                "under_train_per_class": 100,
                "regular_train_per_class": 500,
                "aleatoric_enabled": True,
                "custom_noise_rate": 0.15,  # Custom noise
                "sweep_enabled": False
            },
            "evaluation_config": {
                "eval_per_group": 200,
                "mc_passes": 30,
                "selected_signals": ["predictive_entropy"]
            }
        }
        
        config = validate_workflow(workflow)
        assert config.uncertainty_config.custom_noise_rate == 0.15
    
    def test_invalid_aleatoric_no_noise_source(self):
        """Test invalid: aleatoric enabled but no noise source."""
        workflow = {
            "step1_complete": True,
            "step2_complete": True,
            "step3_complete": True,
            "step4_complete": True,
            "dataset_config": {
                "dataset_name": "cifar10",
                "noise_type": "clean_label",  # Clean!
                "stats": {}
            },
            "training_config": {
                "use_checkpoint": False,
                "model_architecture": "dinov2-small",
                "hidden_dim": 256,
                "dropout": 0.2,
                "epochs": 12,
                "learning_rate": 0.001,
                "batch_size": 256
            },
            "uncertainty_config": {
                "epistemic_enabled": True,
                "under_supported": "random:2",
                "under_train_per_class": 50,
                "regular_train_per_class": 300,
                "aleatoric_enabled": True,  # Enabled!
                "custom_noise_rate": None,  # But no custom noise!
                "sweep_enabled": False
            },
            "evaluation_config": {
                "eval_per_group": 100,
                "mc_passes": 20,
                "selected_signals": []
            }
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validate_workflow(workflow)
        assert "no noise source" in str(exc_info.value)
    
    def test_invalid_step_progression(self):
        """Test invalid step progression."""
        workflow = {
            "step1_complete": True,
            "step2_complete": False,  # Step 2 not complete
            "step3_complete": True,   # But step 3 is!
            "step4_complete": False,
            "dataset_config": {
                "dataset_name": "cifar10",
                "noise_type": "clean_label",
                "stats": {}
            },
            "training_config": {
                "use_checkpoint": False,
                "model_architecture": "dinov2-small",
                "hidden_dim": 256,
                "dropout": 0.2,
                "epochs": 12,
                "learning_rate": 0.001,
                "batch_size": 256
            },
            "uncertainty_config": {
                "epistemic_enabled": True,
                "under_supported": "random:2",
                "under_train_per_class": 50,
                "regular_train_per_class": 300,
                "aleatoric_enabled": False,
                "sweep_enabled": False
            },
            "evaluation_config": {
                "eval_per_group": 100,
                "mc_passes": 0,
                "selected_signals": []
            }
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validate_workflow(workflow)
        assert "Cannot complete step 3 before step 2" in str(exc_info.value)


class TestValidationHelpers:
    """Test validation helper functions."""
    
    def test_get_validation_errors_valid(self):
        """Test get_validation_errors with valid config."""
        workflow = {
            "step1_complete": True,
            "step2_complete": False,
            "step3_complete": False,
            "step4_complete": False,
            "dataset_config": {
                "dataset_name": "cifar10",
                "noise_type": "clean_label",
                "stats": {}
            },
            "training_config": {
                "use_checkpoint": False,
                "model_architecture": "dinov2-small",
                "hidden_dim": 256,
                "dropout": 0.2,
                "epochs": 12,
                "learning_rate": 0.001,
                "batch_size": 256
            },
            "uncertainty_config": {
                "epistemic_enabled": True,
                "under_supported": "random:2",
                "under_train_per_class": 50,
                "regular_train_per_class": 300,
                "aleatoric_enabled": False,
                "sweep_enabled": False
            },
            "evaluation_config": {
                "eval_per_group": 100,
                "mc_passes": 0,
                "selected_signals": []
            }
        }
        
        errors = get_validation_errors(workflow)
        assert len(errors) == 0
    
    def test_get_validation_errors_invalid(self):
        """Test get_validation_errors with invalid config."""
        workflow = {
            "step1_complete": True,
            "step2_complete": True,
            "step3_complete": True,
            "step4_complete": True,
            "dataset_config": {
                "dataset_name": "cifar10",
                "noise_type": "clean_label",
                "stats": {}
            },
            "training_config": {
                "use_checkpoint": False,
                "model_architecture": "dinov2-small",
                "hidden_dim": 256,
                "dropout": 0.2,
                "epochs": 12,
                "learning_rate": 0.001,
                "batch_size": 256
            },
            "uncertainty_config": {
                "epistemic_enabled": True,
                "under_supported": "random:2",
                "under_train_per_class": 50,
                "regular_train_per_class": 300,
                "aleatoric_enabled": True,  # Enabled
                "custom_noise_rate": None,  # But no noise source!
                "sweep_enabled": False
            },
            "evaluation_config": {
                "eval_per_group": 100,
                "mc_passes": 0,
                "selected_signals": []
            }
        }
        
        errors = get_validation_errors(workflow)
        assert len(errors) > 0
        assert any("no noise source" in err for err in errors)

# Made with Bob
