#!/usr/bin/env python3
"""
Test Aleatoric Uncertainty Hypothesis
Verifies criteria (C1) and (O2) from the research paper.
"""

import json
from pathlib import Path
from typing import List, Dict, Any
import numpy as np
from scipy import stats

def load_experiment_data(summary_path: Path) -> Dict[str, Any]:
    """Load experiment summary JSON."""
    with open(summary_path) as f:
        return json.load(f)

def extract_metrics(experiments: List[Dict[str, Any]]) -> Dict[str, List[float]]:
    """Extract key metrics from experiments."""
    data = {
        'noise_pct': [],
        'inverse_coherence_auroc': [],
        'dominance_auroc': [],
        'inverse_mass_auroc': [],
        'predictive_entropy_auroc': [],
    }
    
    for exp in experiments:
        # Extract aleatoric noise percentage
        noise_pct = exp['config']['data'].get('aleatoric_noise_percentage', 0.0)
        data['noise_pct'].append(noise_pct)
        
        # Extract AUROC values for key signals
        for signal_data in exp['one_vs_rest_auroc']:
            signal_name = signal_data['signal']
            aleatoric_auroc = signal_data['aleatoric_like_auroc']
            
            if signal_name == 'inverse_coherence':
                data['inverse_coherence_auroc'].append(aleatoric_auroc)
            elif signal_name == 'dominance':
                data['dominance_auroc'].append(aleatoric_auroc)
            elif signal_name == 'inverse_mass':
                data['inverse_mass_auroc'].append(aleatoric_auroc)
            elif signal_name == 'predictive_entropy':
                data['predictive_entropy_auroc'].append(aleatoric_auroc)
    
    return data

def test_criterion_c1(noise_pct: List[float], aleatoric_signal: List[float], signal_name: str) -> Dict[str, Any]:
    """
    Test Criterion (C1): ua ∼ ∝ Ua
    Aleatoric signal should be proportional to aleatoric uncertainty.
    """
    if len(set(noise_pct)) < 2:
        return {
            'criterion': 'C1',
            'signal': signal_name,
            'status': 'INSUFFICIENT_DATA',
            'message': 'Need at least 2 different noise levels'
        }
    
    # Compute Pearson correlation
    correlation, p_value = stats.pearsonr(noise_pct, aleatoric_signal)
    
    # Criterion passes if:
    # 1. Positive correlation (r > 0)
    # 2. Statistically significant (p < 0.05)
    passes = correlation > 0 and p_value < 0.05
    
    return {
        'criterion': 'C1',
        'signal': signal_name,
        'correlation': correlation,
        'p_value': p_value,
        'passes': passes,
        'interpretation': f"{'✅ PASS' if passes else '❌ FAIL'}: {signal_name} {'is' if passes else 'is NOT'} proportional to aleatoric noise"
    }

def test_criterion_o2(noise_pct: List[float], epistemic_signal: List[float], signal_name: str) -> Dict[str, Any]:
    """
    Test Criterion (O2): ue ≁ ∝ Ua
    Epistemic signal should NOT be proportional to aleatoric uncertainty.
    """
    if len(set(noise_pct)) < 2:
        return {
            'criterion': 'O2',
            'signal': signal_name,
            'status': 'INSUFFICIENT_DATA',
            'message': 'Need at least 2 different noise levels'
        }
    
    # Compute Pearson correlation
    correlation, p_value = stats.pearsonr(noise_pct, epistemic_signal)
    
    # Criterion passes if:
    # 1. No significant correlation (p >= 0.05) OR
    # 2. Weak correlation (|r| < 0.3)
    passes = p_value >= 0.05 or abs(correlation) < 0.3
    
    return {
        'criterion': 'O2',
        'signal': signal_name,
        'correlation': correlation,
        'p_value': p_value,
        'passes': passes,
        'interpretation': f"{'✅ PASS' if passes else '❌ FAIL'}: {signal_name} {'is independent of' if passes else 'correlates with'} aleatoric noise"
    }

def main():
    print("=" * 80)
    print("TESTING ALEATORIC UNCERTAINTY HYPOTHESIS")
    print("=" * 80)
    
    # Find all experiments with aleatoric_noise_percentage
    exp_dir = Path("/tmp/walaris_experiments")
    summary_files = list(exp_dir.glob("*/results/summary.json"))
    
    print(f"\nFound {len(summary_files)} experiment summaries")
    
    # Load all experiments
    experiments = []
    for summary_path in summary_files:
        try:
            exp_data = load_experiment_data(summary_path)
            if 'config' in exp_data and 'data' in exp_data['config']:
                experiments.append(exp_data)
        except Exception as e:
            print(f"Warning: Could not load {summary_path}: {e}")
    
    print(f"Successfully loaded {len(experiments)} experiments")
    
    # Extract metrics
    data = extract_metrics(experiments)
    
    # Check if we have variation in noise levels
    unique_noise = sorted(set(data['noise_pct']))
    print(f"\nNoise levels found: {unique_noise}")
    
    if len(unique_noise) < 2:
        print("\n❌ INSUFFICIENT DATA: Need experiments with at least 2 different noise levels")
        print("   Current experiments all use the same noise level")
        print("\n💡 RECOMMENDATION: Create a batch experiment with aleatoric noise sweep")
        print("   Example: sweep aleatoric_noise_percentage from 0 to 40 in steps of 10")
        return
    
    print(f"\n✅ Found {len(unique_noise)} different noise levels - sufficient for analysis")
    print(f"   Experiments per noise level:")
    for noise in unique_noise:
        count = data['noise_pct'].count(noise)
        print(f"   - {noise}%: {count} experiment(s)")
    
    # Test Criterion (C1) - Aleatoric signals should correlate with noise
    print("\n" + "=" * 80)
    print("CRITERION (C1): Aleatoric Signal ∝ Aleatoric Uncertainty")
    print("=" * 80)
    
    c1_results = []
    
    # Test inverse_coherence (primary aleatoric signal)
    result = test_criterion_c1(data['noise_pct'], data['inverse_coherence_auroc'], 'inverse_coherence')
    c1_results.append(result)
    print(f"\n{result['interpretation']}")
    print(f"  Correlation: r = {result['correlation']:.4f}, p = {result['p_value']:.4f}")
    
    # Test predictive_entropy (secondary aleatoric signal)
    result = test_criterion_c1(data['noise_pct'], data['predictive_entropy_auroc'], 'predictive_entropy')
    c1_results.append(result)
    print(f"\n{result['interpretation']}")
    print(f"  Correlation: r = {result['correlation']:.4f}, p = {result['p_value']:.4f}")
    
    # Test Criterion (O2) - Epistemic signals should NOT correlate with noise
    print("\n" + "=" * 80)
    print("CRITERION (O2): Epistemic Signal ≁ ∝ Aleatoric Uncertainty")
    print("=" * 80)
    
    o2_results = []
    
    # Test dominance (primary epistemic signal)
    result = test_criterion_o2(data['noise_pct'], data['dominance_auroc'], 'dominance')
    o2_results.append(result)
    print(f"\n{result['interpretation']}")
    print(f"  Correlation: r = {result['correlation']:.4f}, p = {result['p_value']:.4f}")
    
    # Test inverse_mass (secondary epistemic signal)
    result = test_criterion_o2(data['noise_pct'], data['inverse_mass_auroc'], 'inverse_mass')
    o2_results.append(result)
    print(f"\n{result['interpretation']}")
    print(f"  Correlation: r = {result['correlation']:.4f}, p = {result['p_value']:.4f}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    c1_pass = all(r['passes'] for r in c1_results if 'passes' in r)
    o2_pass = all(r['passes'] for r in o2_results if 'passes' in r)
    
    print(f"\nCriterion (C1) - Aleatoric signals correlate with noise: {'✅ PASS' if c1_pass else '❌ FAIL'}")
    print(f"Criterion (O2) - Epistemic signals independent of noise: {'✅ PASS' if o2_pass else '❌ FAIL'}")
    
    if c1_pass and o2_pass:
        print("\n🎉 HYPOTHESIS VERIFIED: Uncertainty signals properly disentangle aleatoric and epistemic uncertainty!")
    else:
        print("\n⚠️  HYPOTHESIS NOT FULLY VERIFIED: Some criteria failed")
        print("    This may indicate:")
        print("    - Insufficient noise variation in experiments")
        print("    - Need for more experiments per noise level")
        print("    - Potential issues with signal definitions")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()

# Made with Bob
