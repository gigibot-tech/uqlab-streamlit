# Streamlit UI Improvements - Experiment Configuration

## Overview
The experiment configuration form in `streamlit_app.py` has been completely reorganized to provide a clearer, more intuitive interface for setting up uncertainty quantification experiments.

## Key Improvements

### 1. 📦 Dataset Configuration Section
**Purpose**: Make it crystal clear what dataset is being used

**Changes**:
- Prominently displays "CIFAR-10N Dataset" with description
- Shows all 10 available classes with their names (airplane, automobile, bird, cat, deer, dog, frog, horse, ship, truck)
- Displays total classes (10) and current noise type
- Provides context about the dataset's purpose

**User Benefit**: Users immediately understand what data they're working with

---

### 2. 🔬 Epistemic Uncertainty Configuration
**Purpose**: Configure model uncertainty through under-supported classes

**What is Epistemic Uncertainty?**
- Represents model uncertainty due to insufficient training data
- Created by intentionally under-sampling specific classes
- Can be reduced by collecting more training data

**Changes**:
- Clear section header with explanation
- **Random vs Manual Selection**:
  - Checkbox: "Select under-supported classes randomly"
  - If checked: Specify number of classes to randomly under-sample
  - If unchecked: Multi-select dropdown showing all class names
  - Visual confirmation of selected classes
- **Training Data Configuration**:
  - Under-supported samples/class (e.g., 50 samples)
  - Regular samples/class (e.g., 300 samples)
  - Help text explaining the impact

**User Benefit**: Users understand exactly which classes are under-supported and why

---

### 3. 🎲 Aleatoric Uncertainty Configuration
**Purpose**: Configure data uncertainty through label noise

**What is Aleatoric Uncertainty?**
- Represents data uncertainty from noisy or ambiguous labels
- Inherent in the data (cannot be reduced by more training)
- Caused by mislabeled or ambiguous examples

**Changes**:
- Clear section header with explanation
- **Noise Source Selection**:
  - Radio button: "Use CIFAR-10N noise" or "Add random label flipping"
  - If using CIFAR-10N: Shows selected noise type from sidebar
  - If using random flipping: Slider for flip percentage (0-50%)
- Visual feedback on noise configuration

**User Benefit**: Users understand how label noise creates aleatoric uncertainty

---

### 4. 🧠 Model & Training Configuration
**Purpose**: Configure neural network architecture and training process

**Changes**:
- Organized into two subsections:
  - **Model Architecture**: DINOv2 backbone, hidden dimension, dropout rate
  - **Training Hyperparameters**: Epochs, learning rate, weight decay, batch size
- Clear labels and sensible defaults
- Grouped related parameters together

**User Benefit**: Logical organization of model and training settings

---

### 5. 📊 Evaluation Configuration
**Purpose**: Configure how uncertainty is measured

**Changes**:
- Clear section header with explanation
- **MC Dropout Passes**: 
  - Help text: "Number of forward passes with dropout enabled to estimate epistemic uncertainty"
  - Explains this measures model uncertainty
- **Attribution Method**:
  - Help text: "Method to explain which features contribute to predictions"
  - Options: dualxda, gradcam, integrated_gradients
- **Evaluation Samples per Group**:
  - Help text: "Number of samples for each evaluation group (clean, noisy, under-supported)"
  - Explains balanced evaluation

**User Benefit**: Users understand what each evaluation parameter does

---

## Form Flow

The new form follows a logical progression:

1. **Dataset** → What data are we using?
2. **Epistemic** → How do we create model uncertainty?
3. **Aleatoric** → How do we create data uncertainty?
4. **Model & Training** → How do we build and train the model?
5. **Evaluation** → How do we measure uncertainty?

---

## Technical Changes

### Updated Configuration Structure

The experiment configuration now includes organized sections:

```python
experiment_data = {
    "name": exp_name,
    "config": {
        # Dataset configuration
        "dataset": "cifar10n",
        "noise_type": noise_type,
        
        # Epistemic uncertainty configuration
        "under_supported_classes": under_supported,  # Can be "random:2" or "3,5"
        "under_train_per_class": under_train_per_class,
        "regular_train_per_class": regular_train_per_class,
        
        # Aleatoric uncertainty configuration
        "noise_source": noise_source,  # "Use CIFAR-10N noise" or "Add random label flipping"
        "custom_noise_rate": custom_noise_rate,  # 0-50%
        
        # Model configuration
        "dinov2_model": dinov2_model,
        "hidden_dim": hidden_dim,
        "dropout": dropout,
        
        # Training configuration
        "epochs": epochs,
        "learning_rate": learning_rate,
        "weight_decay": weight_decay,
        "train_batch_size": train_batch_size,
        
        # Evaluation configuration
        "eval_per_group": eval_per_group,
        "mc_passes": mc_passes,
        "attribution_method": attribution_method,
    }
}
```

### New Features

1. **Random Class Selection**: `under_supported_classes` can now be "random:N" format
2. **Custom Noise Rate**: New parameter for random label flipping
3. **Noise Source Selection**: Choose between CIFAR-10N noise or custom flipping
4. **Visual Feedback**: Success/warning messages for class selection
5. **Better Help Text**: Contextual explanations for each parameter

---

## Backend Integration Notes

The backend will need to handle:

1. **Random class selection**: Parse "random:N" format and randomly select N classes
2. **Custom noise rate**: Apply random label flipping if `noise_source` is "Add random label flipping"
3. **Backward compatibility**: Handle old config format without new fields

---

## User Experience Improvements

### Before
- Confusing mix of parameters
- Unclear what "under-supported classes" meant
- No explanation of epistemic vs aleatoric uncertainty
- Evaluation parameters without context

### After
- Clear sections with explanations
- Visual confirmation of selections
- Educational info boxes explaining concepts
- Contextual help text for each parameter
- Logical flow from dataset → uncertainty → training → evaluation

---

## Next Steps

1. **Backend Updates**: Update training orchestrator to handle new config format
2. **Validation**: Add validation for random class selection
3. **Documentation**: Update API documentation with new config structure
4. **Testing**: Test with various configurations to ensure robustness

---

## Summary

The improved UI makes uncertainty quantification experiments more accessible by:
- ✅ Clearly explaining what each section does
- ✅ Separating epistemic and aleatoric uncertainty configuration
- ✅ Providing visual feedback and confirmation
- ✅ Using educational info boxes
- ✅ Following a logical configuration flow
- ✅ Adding contextual help text throughout

Users can now confidently configure experiments without needing deep knowledge of the underlying concepts.