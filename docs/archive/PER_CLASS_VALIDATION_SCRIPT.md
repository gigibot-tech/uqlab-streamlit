# Per-Class Campaign Validation Script

## Overview

The [`validate_per_class_campaign.py`](scripts/validate_per_class_campaign.py) script validates that per-class configuration campaigns produce expected uncertainty quantification patterns and exports detailed results showing which metrics correlate correctly with the configuration.

## Purpose

This script answers the critical question: **"Does my per-class configuration actually produce the expected uncertainty patterns?"**

It validates:
1. **Pattern Validation**: Each class exhibits expected uncertainty based on its configuration
2. **Correlation Analysis**: Training samples and label noise correlate correctly with uncertainty
3. **Metric Satisfaction**: Which specific metrics pass/fail and from which experiments

## Expected Uncertainty Patterns

The script validates four distinct uncertainty patterns:

### 1. OOD (Out-of-Distribution) Pattern
- **Configuration**: `train_samples = 0`
- **Expected**: Very high uncertainty (>80%)
- **Reason**: Model has never seen these classes during training

### 2. Sparse (Epistemic) Pattern
- **Configuration**: `train_samples < 100`
- **Expected**: High epistemic uncertainty (>60%)
- **Reason**: Insufficient training data leads to model uncertainty

### 3. Noisy (Aleatoric) Pattern
- **Configuration**: `label_noise_pct > 20%`
- **Expected**: High aleatoric uncertainty (>50%)
- **Reason**: Label noise creates inherent data uncertainty

### 4. Clean Pattern
- **Configuration**: Many samples + low noise
- **Expected**: Low uncertainty (<30%)
- **Reason**: Well-supported, clean training data

## Correlation Metrics

### Epistemic Correlation
- **Metric**: Correlation between `train_samples` and `epistemic_uncertainty`
- **Expected**: **Negative correlation** (r < -0.7)
- **Interpretation**: Fewer training samples → Higher epistemic uncertainty

### Aleatoric Correlation
- **Metric**: Correlation between `label_noise_pct` and `aleatoric_uncertainty`
- **Expected**: **Positive correlation** (r > 0.7)
- **Interpretation**: More label noise → Higher aleatoric uncertainty

## Usage

### Basic Validation

```bash
cd uqlab-streamlit
PYTHONPATH=src python3 scripts/validate_per_class_campaign.py \
    --run-ids uuid1,uuid2,uuid3 \
    --output validation_report.json
```

### Custom Thresholds

```bash
PYTHONPATH=src python3 scripts/validate_per_class_campaign.py \
    --run-ids uuid1,uuid2,uuid3 \
    --ood-threshold 0.85 \
    --sparse-threshold 0.65 \
    --noisy-threshold 0.55 \
    --clean-threshold 0.25 \
    --epistemic-correlation -0.75 \
    --aleatoric-correlation 0.75 \
    --output validation_report.json
```

### Validate Four-Region Default Preset

```bash
# After running experiments with Four-Region Default preset
PYTHONPATH=src python3 scripts/validate_per_class_campaign.py \
    --run-ids $(cat experiment_ids.txt | tr '\n' ',') \
    --output four_region_validation.json
```

## Command-Line Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--run-ids` | str | **Required** | Comma-separated experiment UUIDs |
| `--experiments-dir` | Path | `data/experiments` | Directory containing experiment artifacts |
| `--output` | Path | None | Output JSON file for validation results |
| `--ood-threshold` | float | 0.8 | Uncertainty threshold for OOD classes |
| `--sparse-threshold` | float | 0.6 | Uncertainty threshold for sparse classes |
| `--noisy-threshold` | float | 0.5 | Uncertainty threshold for noisy classes |
| `--clean-threshold` | float | 0.3 | Uncertainty threshold for clean classes |
| `--epistemic-correlation` | float | -0.7 | Threshold for epistemic correlation |
| `--aleatoric-correlation` | float | 0.7 | Threshold for aleatoric correlation |

## Output Format

### Console Output

```
================================================================================
CAMPAIGN VALIDATION REPORT: campaign_3_experiments
================================================================================

Experiments: 3/3 validated
Validation Score: 87.5%
Patterns Satisfied: 28/32

Pattern Validation:
  ✓ OOD (0 samples):     PASS
  ✓ Sparse (<100):       PASS
  ✓ Noisy (>20% noise):  PASS
  ✓ Clean (many/clean):  FAIL

Correlation Analysis:
  Epistemic (samples ↔ uncertainty): -0.823 ✓ PASS
  Aleatoric (noise ↔ uncertainty):   +0.756 ✓ PASS

✓ SATISFIED METRICS (28):
  • Class 8 (ship): OOD pattern satisfied (uncertainty=0.892, threshold=0.800)
    Experiment: a1b2c3d4
  • Class 9 (truck): OOD pattern satisfied (uncertainty=0.885, threshold=0.800)
    Experiment: a1b2c3d4
  • Class 4 (deer): Sparse pattern satisfied (uncertainty=0.687, threshold=0.600)
    Experiment: a1b2c3d4
  ...

✗ FAILED METRICS (4):
  • Class 6 (frog): Clean pattern NOT satisfied (uncertainty=0.345, threshold=0.300)
    Experiment: e5f6g7h8
  ...

================================================================================
```

### JSON Output

```json
{
  "campaign_name": "campaign_3_experiments",
  "total_experiments": 3,
  "validated_experiments": 3,
  "validation_score": 0.875,
  "patterns_satisfied": 28,
  "total_patterns_checked": 32,
  
  "ood_pattern_satisfied": true,
  "sparse_pattern_satisfied": true,
  "noisy_pattern_satisfied": true,
  "clean_pattern_satisfied": false,
  
  "epistemic_correlation": -0.823,
  "aleatoric_correlation": 0.756,
  "epistemic_correlation_satisfied": true,
  "aleatoric_correlation_satisfied": true,
  
  "satisfied_metrics": [
    {
      "class_id": 8,
      "class_name": "ship",
      "pattern": "OOD",
      "experiment_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
      "uncertainty": 0.892,
      "threshold": 0.800,
      "notes": ["Out-of-distribution class (no training samples)"]
    }
  ],
  
  "failed_metrics": [
    {
      "class_id": 6,
      "class_name": "frog",
      "pattern": "Clean",
      "experiment_id": "e5f6g7h8-90ab-cdef-1234-567890abcdef",
      "uncertainty": 0.345,
      "threshold": 0.300,
      "notes": ["Clean, well-supported class (300 samples, 0.0% noise)"]
    }
  ],
  
  "class_validations": [...]
}
```

## Exit Codes

| Code | Meaning | Validation Score |
|------|---------|------------------|
| 0 | Success | ≥ 80% |
| 1 | Warning | 60-79% |
| 2 | Failure | < 60% |

## Integration with Campaign PDF

The validation script complements the campaign PDF report:

1. **Generate Campaign PDF** (visual results):
   ```bash
   PYTHONPATH=src python3 scripts/setup/generate_campaign_report.py \
       --run-ids uuid1,uuid2,uuid3 \
       -o campaign_report.pdf
   ```

2. **Validate Campaign** (quantitative validation):
   ```bash
   PYTHONPATH=src python3 scripts/validate_per_class_campaign.py \
       --run-ids uuid1,uuid2,uuid3 \
       --output validation_report.json
   ```

3. **Review Both**:
   - PDF shows visual trends and patterns
   - JSON shows which specific metrics passed/failed

## Example Workflow

### 1. Run Per-Class Experiments

```python
# In Progressive UI:
# 1. Click "Four-Region Default" preset
# 2. Enable epistemic sweep for sparse class (e.g., class 4)
# 3. Launch experiments
# 4. Note experiment IDs
```

### 2. Validate Results

```bash
# Collect experiment IDs
export RUN_IDS="uuid1,uuid2,uuid3,uuid4,uuid5"

# Validate campaign
PYTHONPATH=src python3 scripts/validate_per_class_campaign.py \
    --run-ids $RUN_IDS \
    --output validation_report.json

# Check exit code
if [ $? -eq 0 ]; then
    echo "✓ Validation passed!"
else
    echo "✗ Validation failed - check report"
fi
```

### 3. Analyze Results

```python
import json

# Load validation results
with open("validation_report.json") as f:
    report = json.load(f)

# Check overall score
print(f"Validation Score: {report['validation_score']:.1%}")

# Find failed metrics
for metric in report['failed_metrics']:
    if 'class_id' in metric:
        print(f"Class {metric['class_id']} ({metric['class_name']}): "
              f"{metric['pattern']} pattern failed")
        print(f"  Expected: {metric['threshold']:.3f}")
        print(f"  Got: {metric['uncertainty']:.3f}")
        print(f"  Experiment: {metric['experiment_id'][:8]}")
```

## Troubleshooting

### Low Validation Score

**Problem**: Validation score < 60%

**Possible Causes**:
1. **Insufficient training**: Model not converged
2. **Wrong thresholds**: Adjust thresholds for your dataset
3. **Configuration mismatch**: Per-class config doesn't match expectations
4. **Evaluation issues**: Check evaluation pool size

**Solutions**:
```bash
# Try with relaxed thresholds
PYTHONPATH=src python3 scripts/validate_per_class_campaign.py \
    --run-ids $RUN_IDS \
    --ood-threshold 0.7 \
    --sparse-threshold 0.5 \
    --noisy-threshold 0.4 \
    --clean-threshold 0.4 \
    --output validation_relaxed.json
```

### Missing Correlation

**Problem**: `epistemic_correlation: null` or `aleatoric_correlation: null`

**Possible Causes**:
1. **Insufficient variance**: All classes have same config
2. **Too few classes**: Need ≥3 classes for correlation
3. **NumPy not installed**: Install with `pip install numpy`

**Solutions**:
- Ensure per-class config has variety (different train_samples, noise levels)
- Run experiments with at least 3 different configurations
- Install numpy: `pip install numpy`

### Pattern Not Satisfied

**Problem**: Specific pattern (OOD/Sparse/Noisy/Clean) fails validation

**Debugging**:
```python
# Load validation report
import json
with open("validation_report.json") as f:
    report = json.load(f)

# Find failed classes for specific pattern
pattern = "OOD"  # or "Sparse", "Noisy", "Clean"
failed = [m for m in report['failed_metrics'] 
          if m.get('pattern') == pattern]

for metric in failed:
    print(f"Class {metric['class_id']}: "
          f"expected {metric['threshold']:.3f}, "
          f"got {metric['uncertainty']:.3f}")
```

## Implementation Details

### Validation Logic

```python
def classify_class_pattern(train_samples: int, label_noise_pct: float):
    """Classify expected uncertainty pattern."""
    if train_samples == 0:
        return ("OOD", 0.8)  # Very high uncertainty
    elif train_samples < 100:
        return ("Sparse", 0.6)  # High epistemic
    elif label_noise_pct > 20:
        return ("Noisy", 0.5)  # High aleatoric
    else:
        return ("Clean", 0.3)  # Low uncertainty
```

### Correlation Calculation

```python
# Epistemic: negative correlation expected
epistemic_corr = np.corrcoef(train_samples, epistemic_uncertainty)[0, 1]
satisfied = epistemic_corr <= -0.7

# Aleatoric: positive correlation expected
aleatoric_corr = np.corrcoef(label_noise_pct, aleatoric_uncertainty)[0, 1]
satisfied = aleatoric_corr >= 0.7
```

## Related Documentation

- [`PER_CLASS_LAUNCH_INTEGRATION_COMPLETE.md`](PER_CLASS_LAUNCH_INTEGRATION_COMPLETE.md) - Launch integration
- [`PHASE_2_PER_CLASS_UI_COMPLETE.md`](PHASE_2_PER_CLASS_UI_COMPLETE.md) - UI implementation
- [`THREE_LINE_PLOT_EXPLAINED.md`](src/uqlab/evaluation/classification/pipeline/THREE_LINE_PLOT_EXPLAINED.md) - Visualization

## Future Enhancements

1. **PDF Integration**: Add validation summary page to campaign PDF
2. **Interactive Dashboard**: Streamlit UI for validation results
3. **Automated Thresholds**: Learn optimal thresholds from data
4. **Comparative Validation**: Compare multiple campaigns
5. **Statistical Tests**: Add significance testing for correlations

---

**Created**: 2026-06-23  
**Status**: ✅ Complete  
**Script**: [`scripts/validate_per_class_campaign.py`](scripts/validate_per_class_campaign.py)