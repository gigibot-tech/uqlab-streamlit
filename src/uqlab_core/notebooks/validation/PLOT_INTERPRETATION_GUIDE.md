# Method Uncertainty Comparison Plot - Interpretation Guide

## Overview
The "Method Uncertainty Comparison" view shows a **3-row × 4-column grid** with dual Y-axes, designed to help you understand how different uncertainty quantification methods perform across architectures.

## Visual Legend

### Line Styles
- **Solid line (━━━)** with **circles (●)**: Epistemic Uncertainty (Green #2ecc71)
- **Dashed line (╌╌╌)** with **squares (■)**: Aleatoric Uncertainty (Blue #3498db)  
- **Dotted line (···)** with **diamonds (◆)**: Accuracy (Orange #e67e22)

### Y-Axes
- **Left Y-axis**: Uncertainty values (0-2) or AUROC (0-1)
- **Right Y-axis**: Accuracy (0-1)

## Grid Layout

### Row 1: Gaussian Logits Methods
Shows how epistemic/aleatoric uncertainty and accuracy change across 4 architectures:
- Column 1: DINOv2-small + MLP
- Column 2: DINOv2-base + MLP
- Column 3: CNN MC Dropout
- Column 4: ResNet18 MC Dropout

**What to look for:**
- Epistemic (green solid) should **decrease** as dataset size increases
- Aleatoric (blue dashed) should **increase** as noise increases
- Accuracy (orange dotted) trends on right axis

### Row 2: Information Theoretic Methods
Same 4 architectures, showing IT-based uncertainty signals:
- Predictive Entropy
- Mutual Information
- etc.

**What to look for:**
- Similar patterns to Row 1
- Compare how IT methods vs Gaussian methods behave

### Row 3: Top 4 Signals by AUROC
Shows the 4 best-performing uncertainty signals:
- Column 1-3: Fixed signals (inverse_coherence, dominance, inverse_mass)
- Column 4: Best additional signal (dynamically selected by AUROC)

**What to look for:**
- AUROC values (left axis) show signal quality
- Higher AUROC = better uncertainty detection
- Subtitle shows mean AUROC for each signal

## How to Use

### 1. Hover Over Points
- Hover shows exact values: "Epistemic: 0.523" or "Accuracy: 0.847"
- Helps identify specific data points

### 2. Compare Across Columns
- See which architecture performs best
- Identify consistent patterns across methods

### 3. Compare Across Rows
- Row 1 vs Row 2: Gaussian vs IT methods
- Row 3: Best individual signals

### 4. Check Legend
- Top of plot shows legend with all three line types
- Click legend items to show/hide specific lines

## Expected Patterns

### Dataset Size Sweep (Epistemic)
- **Epistemic uncertainty** (green solid): Should **decrease** as samples increase
- **Aleatoric uncertainty** (blue dashed): Should stay **constant** (no noise added)
- **Accuracy** (orange dotted): Should **increase** with more data

### Label Noise Sweep (Aleatoric)
- **Epistemic uncertainty** (green solid): Should stay **constant** (fixed dataset size)
- **Aleatoric uncertainty** (blue dashed): Should **increase** with more noise
- **Accuracy** (orange dotted): Should **decrease** with more noise

## Troubleshooting

### "I see lines but can't tell them apart"
- Look at line style: solid vs dashed vs dotted
- Look at marker shape: circle vs square vs diamond
- Hover to see which line you're looking at

### "No legend visible"
- Legend is at the top center with white background
- Scroll up if needed
- Legend shows: "Epistemic Uncertainty", "Aleatoric Uncertainty", "Accuracy (right axis)"

### "Values seem wrong"
- Check which Y-axis: left (uncertainty/AUROC) or right (accuracy)
- Uncertainty range: 0-2
- AUROC/Accuracy range: 0-1

### "Empty subplots"
- Some architectures may not have data yet
- Run validation experiments first
- Check that metrics.csv contains required columns

## Required Data Columns

For plots to display, your `metrics.csv` must contain:
- `mean_epistemic_uncertainty`
- `mean_aleatoric_uncertainty`
- `accuracy`
- `architecture`
- Signal AUROC columns: `{signal}_epistemic_auroc`, `{signal}_aleatoric_auroc`

## Quick Reference

| Element | Meaning | Color | Style |
|---------|---------|-------|-------|
| Green solid line with circles | Epistemic Uncertainty | #2ecc71 | ━━━ ● |
| Blue dashed line with squares | Aleatoric Uncertainty | #3498db | ╌╌╌ ■ |
| Orange dotted line with diamonds | Accuracy (right axis) | #e67e22 | ··· ◆ |

---

**Pro Tip**: Use the radio button to switch between "Signal AUROC" (3×3 grid showing only AUROC trends) and "Method Uncertainty Comparison" (3×4 grid with dual axes showing uncertainty + accuracy).