"""
Analyze experiment results to verify uncertainty disentanglement hypotheses.

This script searches for summary.json files and analyzes which signals
best capture epistemic vs aleatoric uncertainty.

Usage:
    python analyze_results.py [results_directory]
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
import statistics

# Signal names mapping (index -> name)
SIGNAL_NAMES = [
    "msp_uncertainty",
    "predictive_entropy", 
    "mutual_info",
    "inverse_coherence",  # Best aleatoric
    "dominance",          # Good epistemic
    "inverse_mass",       # Best epistemic
    "inverse_logit_magnitude"
]

def find_summary_files(root_dir: Path) -> list[Path]:
    """Recursively find all summary.json files."""
    return list(root_dir.rglob("summary.json"))

def extract_experiment_params(summary_data: dict) -> dict:
    """Extract epistemic and aleatoric parameters from summary JSON."""
    try:
        config = summary_data.get('config', {})
        data_config = config.get('data', {})
        
        # Epistemic: under_train_per_class
        epistemic = data_config.get('under_train_per_class', 0)
        
        # Aleatoric: aleatoric_noise_percentage (synthetic noise injection)
        aleatoric = data_config.get('aleatoric_noise_percentage', 0.0)
        
        return {'epistemic': epistemic, 'aleatoric': aleatoric}
    except Exception as e:
        print(f"Error extracting params: {e}")
        return None

def analyze_results(results_dir: str = None):
    """Analyze all experiment results."""
    
    # Determine search directory
    if results_dir:
        search_dir = Path(results_dir)
    else:
        # Try common locations
        possible_dirs = [
            Path("results"),
            Path("uqlab-streamlit/results"),
            Path("../results"),
            Path.home() / "results",
        ]
        search_dir = None
        for d in possible_dirs:
            if d.exists():
                search_dir = d
                break
        
        if not search_dir:
            print("❌ Could not find results directory")
            print("💡 Please specify: python analyze_results.py /path/to/results")
            return
    
    print(f"🔍 Searching for experiments in: {search_dir}")
    summary_files = find_summary_files(search_dir)
    
    if not summary_files:
        print(f"❌ No summary.json files found in {search_dir}")
        return
    
    print(f"📊 Found {len(summary_files)} experiments\n")
    
    # Collect data by experiment type
    epistemic_sweeps = defaultdict(list)  # epistemic_value -> list of (aleatoric, signals)
    aleatoric_sweeps = defaultdict(list)  # aleatoric_value -> list of (epistemic, signals)
    
    for summary_file in summary_files:
        try:
            with open(summary_file, 'r') as f:
                data = json.load(f)
            
            # Extract signals - they're in dict format with signal names
            one_vs_rest = data.get('one_vs_rest_auroc', [])
            if not one_vs_rest or len(one_vs_rest) != 7:
                continue
            
            # Convert to list of AUROC values (epistemic_like_auroc)
            # We'll use epistemic_like_auroc as the primary metric
            signal_aurocs = [sig['epistemic_like_auroc'] for sig in one_vs_rest]
            
            # Extract parameters from the JSON config
            params = extract_experiment_params(data)
            if not params:
                continue
            
            epistemic = params['epistemic']
            aleatoric = params['aleatoric']
            
            # Store for analysis
            epistemic_sweeps[epistemic].append((aleatoric, signal_aurocs))
            aleatoric_sweeps[aleatoric].append((epistemic, signal_aurocs))
            
        except Exception as e:
            print(f"⚠️  Error reading {summary_file}: {e}")
            continue
    
    print("="*80)
    print("🔬 HYPOTHESIS VERIFICATION: Uncertainty Disentanglement")
    print("="*80)
    
    # Analyze epistemic sweeps (varying epistemic, fixed aleatoric)
    print("\n📈 EPISTEMIC UNCERTAINTY ANALYSIS")
    print("   (Varying under-supported samples, fixed noise)")
    print("-"*80)
    
    for aleatoric in sorted(aleatoric_sweeps.keys()):
        experiments = aleatoric_sweeps[aleatoric]
        if len(experiments) < 2:
            continue
        
        print(f"\n🎯 Fixed Aleatoric Noise = {aleatoric}%")
        print(f"   Experiments: {len(experiments)}")
        
        # Calculate correlation between epistemic parameter and each signal
        epistemic_values = [e for e, _ in experiments]
        
        for signal_idx, signal_name in enumerate(SIGNAL_NAMES):
            signal_aurocs = [signals[signal_idx] for _, signals in experiments]
            
            # Calculate range and trend
            min_auroc = min(signal_aurocs)
            max_auroc = max(signal_aurocs)
            range_auroc = max_auroc - min_auroc
            avg_auroc = statistics.mean(signal_aurocs)
            
            # Simple correlation: does AUROC increase with epistemic?
            if len(set(epistemic_values)) > 1:
                sorted_pairs = sorted(zip(epistemic_values, signal_aurocs))
                first_half_avg = statistics.mean([a for _, a in sorted_pairs[:len(sorted_pairs)//2]])
                second_half_avg = statistics.mean([a for _, a in sorted_pairs[len(sorted_pairs)//2:]])
                trend = "↗️ Increases" if second_half_avg > first_half_avg else "↘️ Decreases"
            else:
                trend = "→ Flat"
            
            # Highlight best epistemic signals
            marker = ""
            if signal_name in ["inverse_mass", "dominance"]:
                marker = " ⭐"
            
            print(f"   • {signal_name:25s}: {avg_auroc:.4f} (range: {range_auroc:.4f}) {trend}{marker}")
    
    # Analyze aleatoric sweeps (varying aleatoric, fixed epistemic)
    print("\n\n📉 ALEATORIC UNCERTAINTY ANALYSIS")
    print("   (Varying noise percentage, fixed under-supported samples)")
    print("-"*80)
    
    for epistemic in sorted(epistemic_sweeps.keys()):
        experiments = epistemic_sweeps[epistemic]
        if len(experiments) < 2:
            continue
        
        print(f"\n🎯 Fixed Epistemic (under-supported) = {epistemic} samples/class")
        print(f"   Experiments: {len(experiments)}")
        
        # Calculate correlation between aleatoric parameter and each signal
        aleatoric_values = [a for a, _ in experiments]
        
        for signal_idx, signal_name in enumerate(SIGNAL_NAMES):
            signal_aurocs = [signals[signal_idx] for _, signals in experiments]
            
            # Calculate range and trend
            min_auroc = min(signal_aurocs)
            max_auroc = max(signal_aurocs)
            range_auroc = max_auroc - min_auroc
            avg_auroc = statistics.mean(signal_aurocs)
            
            # Simple correlation: does AUROC increase with aleatoric?
            if len(set(aleatoric_values)) > 1:
                sorted_pairs = sorted(zip(aleatoric_values, signal_aurocs))
                first_half_avg = statistics.mean([a for _, a in sorted_pairs[:len(sorted_pairs)//2]])
                second_half_avg = statistics.mean([a for _, a in sorted_pairs[len(sorted_pairs)//2:]])
                trend = "↗️ Increases" if second_half_avg > first_half_avg else "↘️ Decreases"
            else:
                trend = "→ Flat"
            
            # Highlight best aleatoric signal
            marker = ""
            if signal_name == "inverse_coherence":
                marker = " ⭐"
            
            print(f"   • {signal_name:25s}: {avg_auroc:.4f} (range: {range_auroc:.4f}) {trend}{marker}")
    
    # Summary
    print("\n\n" + "="*80)
    print("📊 SUMMARY & HYPOTHESIS VERIFICATION")
    print("="*80)
    print("""
✅ EXPECTED RESULTS (if disentanglement works):

1. EPISTEMIC SIGNALS (inverse_mass ⭐, dominance ⭐):
   - Should have HIGH AUROC when epistemic varies
   - Should show INCREASING trend with more under-supported samples
   - Should be STABLE when only aleatoric varies

2. ALEATORIC SIGNALS (inverse_coherence ⭐):
   - Should have HIGH AUROC when aleatoric varies  
   - Should show INCREASING trend with more noise
   - Should be STABLE when only epistemic varies

3. MIXED SIGNALS (msp_uncertainty, predictive_entropy, mutual_info):
   - May respond to both types of uncertainty
   - Less specific for disentanglement

💡 Look for:
   - inverse_mass: Best for epistemic (should be ~0.90+ AUROC)
   - dominance: Good for epistemic (should be ~0.75+ AUROC)
   - inverse_coherence: Best for aleatoric (should be ~0.70+ AUROC)
""")

if __name__ == "__main__":
    results_dir = sys.argv[1] if len(sys.argv) > 1 else None
    analyze_results(results_dir)

# Made with Bob