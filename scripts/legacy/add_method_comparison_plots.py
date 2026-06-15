#!/usr/bin/env python3
"""
Script to add method uncertainty comparison plots to validation notebooks.
"""
import json
from pathlib import Path

def add_cells_to_notebook(notebook_path: Path, sweep_type: str, x_col: str, signal_type: str):
    """Add new cells to a notebook for method uncertainty comparison plots."""
    
    # Load notebook
    with open(notebook_path, 'r') as f:
        nb = json.load(f)
    
    # Create new cells to add
    new_cells = []
    
    # 1. Markdown cell: Section header
    new_cells.append({
        "cell_type": "markdown",
        "id": f"method_comparison_{sweep_type}",
        "metadata": {},
        "source": [
            "## Method Uncertainty Comparison (Dual Y-Axes)\n",
            "\n",
            "This visualization shows how uncertainty and accuracy evolve across the sweep:\n",
            "\n",
            "**Row 1: Gaussian Logits Methods**\n",
            "- Shows MC-Dropout, MC-DropConnect, Flipout, Deep Ensemble\n",
            "- Compares epistemic (green), aleatoric (blue) uncertainty with accuracy (orange)\n",
            "\n",
            "**Row 2: Information Theoretic Methods**\n",
            "- Same methods, different uncertainty quantification approach\n",
            "\n",
            "**Row 3: Attribution + Best Baseline Signal**\n",
            "- Fixed: inverse_coherence, dominance, inverse_mass\n",
            "- 4th column: best ROC among msp, predictive_entropy, mutual_info, inverse_logit_magnitude\n",
            "\n",
            "**Legend:**\n",
            "- 🟢 Green: Epistemic Uncertainty (model uncertainty)\n",
            "- 🔵 Blue: Aleatoric Uncertainty (data noise)\n",
            "- 🟠 Orange: Classification Accuracy"
        ]
    })
    
    # 2. Code cell: Import and setup
    new_cells.append({
        "cell_type": "code",
        "execution_count": None,
        "id": f"import_plotting_{sweep_type}",
        "metadata": {},
        "outputs": [],
        "source": [
            "# Import from modular notebook_support (no pasted defs)\n",
            "from notebook_support import (\n",
            "    plot_method_uncertainty_comparison,\n",
            "    get_row3_signals,\n",
            ")"
        ]
    })
    
    # 3. Code cell: Show top signals
    new_cells.append({
        "cell_type": "code",
        "execution_count": None,
        "id": f"show_top_signals_{sweep_type}",
        "metadata": {},
        "outputs": [],
        "source": [
            f"# Row 3 signals for {sweep_type} sweep\n",
            "row3_signals = get_row3_signals(df_metrics, sweep_type='" + sweep_type + "')\n",
            "print('Row 3 signals (fixed 3 + best baseline ROC):')\n",
            "for signal, auroc in row3_signals:\n",
            "    print(f'  {signal}: {auroc:.4f}')"
        ]
    })
    
    # 4. Code cell: Create the plot
    new_cells.append({
        "cell_type": "code",
        "execution_count": None,
        "id": f"plot_method_comparison_{sweep_type}",
        "metadata": {},
        "outputs": [],
        "source": [
            f"# Create method uncertainty comparison plot\n",
            f"plot_method_uncertainty_comparison(df_metrics, '{x_col}', '{sweep_type}')"
        ]
    })
    
    # 5. Markdown cell: Interpretation notes
    new_cells.append({
        "cell_type": "markdown",
        "id": f"interpretation_{sweep_type}",
        "metadata": {},
        "source": [
            "### Interpretation Notes\n",
            "\n",
            "**What to look for:**\n",
            "- **Epistemic uncertainty** should correlate with model confidence (inversely with accuracy)\n",
            "- **Aleatoric uncertainty** should reflect inherent data noise\n",
            "- **Top signals** show which uncertainty metrics best capture the target uncertainty type\n",
            "\n",
            f"**For {sweep_type} sweep:**\n",
            f"- Primary focus: **{signal_type.title()} uncertainty**\n",
            "- Best signals should show clear trends matching the sweep parameter\n",
            "- Dual Y-axes allow direct comparison of uncertainty vs. accuracy"
        ]
    })
    
    # Add new cells to notebook (before the last cell which is typically conclusions)
    nb['cells'].extend(new_cells)
    
    # Save updated notebook
    with open(notebook_path, 'w') as f:
        json.dump(nb, f, indent=1)
    
    print(f"✅ Added {len(new_cells)} cells to {notebook_path.name}")
    print(f"   - Sweep type: {sweep_type}")
    print(f"   - X column: {x_col}")
    print(f"   - Signal type: {signal_type}")

def main():
    """Main function to update both notebooks."""
    project_root = Path(__file__).parent
    
    # Update dataset size notebook
    dataset_size_nb = project_root / "notebooks/validation/architecture_comparison_dataset_size.ipynb"
    add_cells_to_notebook(
        dataset_size_nb,
        sweep_type="dataset_size",
        x_col="dataset_size",
        signal_type="epistemic"
    )
    
    # Update label noise notebook
    label_noise_nb = project_root / "notebooks/validation/architecture_comparison_label_noise.ipynb"
    add_cells_to_notebook(
        label_noise_nb,
        sweep_type="label_noise",
        x_col="noise_rate",
        signal_type="aleatoric"
    )
    
    print("\n✨ Successfully updated both validation notebooks!")
    print("\nNext steps:")
    print("1. Open the notebooks in Jupyter")
    print("2. Run the new cells to generate the plots")
    print("3. Verify the plots display correctly")

if __name__ == "__main__":
    main()

# Made with Bob
