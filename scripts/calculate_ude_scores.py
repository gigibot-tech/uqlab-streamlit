"""
Calculate UDE (Uncertainty Disentanglement Error) scores from validation results.

This script loads validation experiment results and calculates Pearson correlations
and UDE scores for each signal to validate uncertainty disentanglement.

Usage:
    python scripts/calculate_ude_scores.py
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from scipy.stats import pearsonr

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.walaris.notebook_support.signals import SIGNAL_NAMES, EPISTEMIC_SIGNALS, ALEATORIC_SIGNALS


def load_validation_results(results_dir: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load validation results from dataset_size_sweep and label_noise_sweep.
    
    Returns:
        Tuple of (epistemic_df, aleatoric_df)
    """
    # Load dataset size sweep (epistemic)
    epistemic_metrics = results_dir / "validation" / "dataset_size_sweep" / "metrics.csv"
    if not epistemic_metrics.exists():
        raise FileNotFoundError(f"Epistemic metrics not found: {epistemic_metrics}")
    
    # Load label noise sweep (aleatoric)
    aleatoric_metrics = results_dir / "validation" / "label_noise_sweep" / "metrics.csv"
    if not aleatoric_metrics.exists():
        raise FileNotFoundError(f"Aleatoric metrics not found: {aleatoric_metrics}")
    
    epistemic_df = pd.read_csv(epistemic_metrics)
    aleatoric_df = pd.read_csv(aleatoric_metrics)
    
    return epistemic_df, aleatoric_df


def calculate_signal_correlations(
    df: pd.DataFrame,
    signal_name: str,
    parameter_name: str,
    uncertainty_type: str = "epistemic"
) -> Tuple[float, float, int]:
    """
    Calculate Pearson correlation between signal AUROC and swept parameter.
    
    Args:
        df: DataFrame with validation results
        signal_name: Name of the signal (e.g., "inverse_mass")
        parameter_name: Name of the swept parameter
        uncertainty_type: "epistemic" or "aleatoric" - which AUROC to use
    
    Returns:
        Tuple of (correlation, p_value, n_samples)
    """
    # Get signal AUROC column - format is {signal}_{type}_auroc
    auroc_col = f"{signal_name}_{uncertainty_type}_auroc"
    if auroc_col not in df.columns:
        raise ValueError(f"Column {auroc_col} not found in dataframe")
    
    # Get parameter values
    if parameter_name not in df.columns:
        raise ValueError(f"Parameter {parameter_name} not found in dataframe")
    
    # Filter out NaN values
    valid_mask = df[auroc_col].notna() & df[parameter_name].notna()
    signal_values = df.loc[valid_mask, auroc_col].values
    param_values = df.loc[valid_mask, parameter_name].values
    
    if len(signal_values) < 3:
        raise ValueError(f"Need at least 3 data points, got {len(signal_values)}")
    
    correlation, p_value = pearsonr(signal_values, param_values)
    
    return correlation, p_value, len(signal_values)


def calculate_ude_for_signal(
    signal_name: str,
    epistemic_df: pd.DataFrame,
    aleatoric_df: pd.DataFrame,
    epistemic_param: str = "dataset_size",
    aleatoric_param: str = "noise_rate"
) -> Dict:
    """
    Calculate UDE score for a single signal.
    
    UDE is based on 4 conditions:
    - C1: Aleatoric signal should correlate with noise (ρ > 0.7)
    - C2: Epistemic signal should correlate with dataset size (ρ > 0.7)
    - O1: Aleatoric signal should be independent of dataset size (|ρ| < 0.3)
    - O2: Epistemic signal should be independent of noise (|ρ| < 0.3)
    """
    is_epistemic = signal_name in EPISTEMIC_SIGNALS
    is_aleatoric = signal_name in ALEATORIC_SIGNALS
    
    results = {
        "signal": signal_name,
        "type": "epistemic" if is_epistemic else ("aleatoric" if is_aleatoric else "other"),
        "c1": None,  # Aleatoric ~ noise
        "c2": None,  # Epistemic ~ size
        "o1": None,  # Aleatoric ⊥ size
        "o2": None,  # Epistemic ⊥ noise
        "ude_score": None
    }
    
    errors = []
    
    # Calculate correlations
    try:
        # For epistemic sweep, we use epistemic AUROC
        # For aleatoric sweep, we use aleatoric AUROC
        
        # Correlation with epistemic parameter (dataset size) using epistemic AUROC
        corr_epis, p_epis, n_epis = calculate_signal_correlations(
            epistemic_df, signal_name, epistemic_param, uncertainty_type="epistemic"
        )
        
        # Correlation with aleatoric parameter (noise) using aleatoric AUROC
        corr_alea, p_alea, n_alea = calculate_signal_correlations(
            aleatoric_df, signal_name, aleatoric_param, uncertainty_type="aleatoric"
        )
        
        # Store correlations
        if is_epistemic:
            results["c2"] = {"correlation": corr_epis, "p_value": p_epis, "n": n_epis}
            results["o2"] = {"correlation": corr_alea, "p_value": p_alea, "n": n_alea}
            
            # C2: Should be high (> 0.7)
            errors.append(max(0, 0.7 - abs(corr_epis)))
            # O2: Should be low (< 0.3)
            errors.append(max(0, abs(corr_alea) - 0.3))
            
        elif is_aleatoric:
            results["c1"] = {"correlation": corr_alea, "p_value": p_alea, "n": n_alea}
            results["o1"] = {"correlation": corr_epis, "p_value": p_epis, "n": n_epis}
            
            # C1: Should be high (> 0.7)
            errors.append(max(0, 0.7 - abs(corr_alea)))
            # O1: Should be low (< 0.3)
            errors.append(max(0, abs(corr_epis) - 0.3))
        else:
            # For other signals, just store correlations
            results["corr_epistemic"] = {"correlation": corr_epis, "p_value": p_epis, "n": n_epis}
            results["corr_aleatoric"] = {"correlation": corr_alea, "p_value": p_alea, "n": n_alea}
        
        # Calculate UDE score
        if errors:
            results["ude_score"] = np.mean(errors)
        
    except Exception as e:
        print(f"Warning: Could not calculate correlations for {signal_name}: {e}")
    
    return results


def print_ude_results(results: List[Dict]):
    """Print UDE results in a formatted table."""
    print("\n" + "="*100)
    print("🔬 UNCERTAINTY DISENTANGLEMENT ERROR (UDE) ANALYSIS")
    print("="*100)
    
    # Separate by signal type
    epistemic_results = [r for r in results if r["type"] == "epistemic"]
    aleatoric_results = [r for r in results if r["type"] == "aleatoric"]
    other_results = [r for r in results if r["type"] == "other"]
    
    # Print epistemic signals
    if epistemic_results:
        print("\n📊 EPISTEMIC SIGNALS (should respond to dataset size, stable to noise)")
        print("-" * 100)
        print(f"{'Signal':<30} {'C2 (ρ ~ size)':<20} {'O2 (ρ ⊥ noise)':<20} {'UDE Score':<15} {'Status'}")
        print("-" * 100)
        
        for r in epistemic_results:
            c2_str = f"{r['c2']['correlation']:+.3f}" if r['c2'] else "N/A"
            o2_str = f"{r['o2']['correlation']:+.3f}" if r['o2'] else "N/A"
            ude_str = f"{r['ude_score']:.3f}" if r['ude_score'] is not None else "N/A"
            
            # Determine status
            if r['ude_score'] is not None:
                if r['ude_score'] < 0.1:
                    status = "✅ Excellent"
                elif r['ude_score'] < 0.3:
                    status = "⚠️  Good"
                else:
                    status = "❌ Poor"
            else:
                status = "❓ Unknown"
            
            print(f"{r['signal']:<30} {c2_str:<20} {o2_str:<20} {ude_str:<15} {status}")
    
    # Print aleatoric signals
    if aleatoric_results:
        print("\n📊 ALEATORIC SIGNALS (should respond to noise, stable to dataset size)")
        print("-" * 100)
        print(f"{'Signal':<30} {'C1 (ρ ~ noise)':<20} {'O1 (ρ ⊥ size)':<20} {'UDE Score':<15} {'Status'}")
        print("-" * 100)
        
        for r in aleatoric_results:
            c1_str = f"{r['c1']['correlation']:+.3f}" if r['c1'] else "N/A"
            o1_str = f"{r['o1']['correlation']:+.3f}" if r['o1'] else "N/A"
            ude_str = f"{r['ude_score']:.3f}" if r['ude_score'] is not None else "N/A"
            
            # Determine status
            if r['ude_score'] is not None:
                if r['ude_score'] < 0.1:
                    status = "✅ Excellent"
                elif r['ude_score'] < 0.3:
                    status = "⚠️  Good"
                else:
                    status = "❌ Poor"
            else:
                status = "❓ Unknown"
            
            print(f"{r['signal']:<30} {c1_str:<20} {o1_str:<20} {ude_str:<15} {status}")
    
    # Print other signals
    if other_results:
        print("\n📊 OTHER SIGNALS (baseline/hybrid)")
        print("-" * 100)
        print(f"{'Signal':<30} {'ρ ~ size':<20} {'ρ ~ noise':<20}")
        print("-" * 100)
        
        for r in other_results:
            epis_str = f"{r['corr_epistemic']['correlation']:+.3f}" if r.get('corr_epistemic') else "N/A"
            alea_str = f"{r['corr_aleatoric']['correlation']:+.3f}" if r.get('corr_aleatoric') else "N/A"
            print(f"{r['signal']:<30} {epis_str:<20} {alea_str:<20}")
    
    print("\n" + "="*100)
    print("📖 LEGEND:")
    print("  C1: Aleatoric signal should correlate with noise level (ρ > 0.7)")
    print("  C2: Epistemic signal should correlate with dataset size (ρ > 0.7)")
    print("  O1: Aleatoric signal should be independent of dataset size (|ρ| < 0.3)")
    print("  O2: Epistemic signal should be independent of noise level (|ρ| < 0.3)")
    print("  UDE: Uncertainty Disentanglement Error (lower is better, perfect = 0)")
    print("="*100 + "\n")


def main():
    """Main execution function."""
    print("🔍 Loading validation results...")
    
    # Find project root and results directory
    results_dir = project_root / "results"
    if not results_dir.exists():
        print(f"❌ Results directory not found: {results_dir}")
        return
    
    try:
        epistemic_df, aleatoric_df = load_validation_results(results_dir)
        print(f"✅ Loaded {len(epistemic_df)} epistemic experiments")
        print(f"✅ Loaded {len(aleatoric_df)} aleatoric experiments")
        
        # Determine parameter names from dataframe columns
        epistemic_param = "dataset_size" if "dataset_size" in epistemic_df.columns else "under_train_per_class"
        aleatoric_param = "noise_rate" if "noise_rate" in aleatoric_df.columns else "aleatoric_noise_percentage"
        
        print(f"\n📊 Analyzing signals...")
        print(f"   Epistemic parameter: {epistemic_param}")
        print(f"   Aleatoric parameter: {aleatoric_param}")
        
        # Calculate UDE for each signal
        results = []
        for signal_name in SIGNAL_NAMES:
            try:
                result = calculate_ude_for_signal(
                    signal_name,
                    epistemic_df,
                    aleatoric_df,
                    epistemic_param,
                    aleatoric_param
                )
                results.append(result)
            except Exception as e:
                print(f"⚠️  Warning: Could not analyze {signal_name}: {e}")
        
        # Print results
        print_ude_results(results)
        
        # Save results to JSON
        import json
        output_file = project_root / "results" / "validation" / "ude_scores.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"💾 Results saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

# Made with Bob
