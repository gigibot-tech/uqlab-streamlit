#!/usr/bin/env python3
"""
Analyze UQ experiment results from my_run directory

This script loads the summary.json and training_data.config.json files
and creates visualizations of:
- AUROC metrics across different uncertainty signals
- Disentanglement Error (DE) scores for signal pairs

Usage:
    python scripts/analysis/analyze_my_run.py
"""

import json
import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

def load_experiment_results(results_dir: Path) -> tuple[dict, dict]:
    """Load summary.json and training_data.config.json"""
    summary_path = results_dir / "summary.json"
    config_path = results_dir / "training_data.config.json"
    
    with open(summary_path, 'r') as f:
        summary = json.load(f)
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    return summary, config


def extract_auroc_dataframe(summary: dict) -> pd.DataFrame:
    """
    Extract AUROC metrics into a pandas DataFrame
    
    Returns DataFrame with columns:
    - signal: uncertainty signal name
    - aleatoric_auroc: AUROC for aleatoric uncertainty detection
    - epistemic_auroc: AUROC for epistemic uncertainty detection  
    - ood_auroc: AUROC for OOD detection
    """
    auroc_rows = summary.get('auroc_rows', [])
    
    if not auroc_rows:
        # Fallback to one_vs_rest_auroc format
        auroc_rows = []
        for item in summary.get('one_vs_rest_auroc', []):
            auroc_rows.append({
                'signal': item['signal'],
                'aleatoric_auroc': item.get('aleatoric_like_auroc'),
                'epistemic_auroc': item.get('epistemic_like_auroc'),
                'ood_auroc': item.get('ood_like_auroc')
            })
    
    df = pd.DataFrame(auroc_rows)
    return df


def plot_auroc_comparison(df: pd.DataFrame, output_path: Path | None = None):
    """
    Create bar plot comparing AUROC scores across signals and uncertainty types
    
    Args:
        df: DataFrame with columns [signal, aleatoric_auroc, epistemic_auroc, ood_auroc]
        output_path: Optional path to save the figure
    """
    # Reshape data for grouped bar plot
    df_melted = df.melt(
        id_vars=['signal'],
        value_vars=['aleatoric_auroc', 'epistemic_auroc', 'ood_auroc'],
        var_name='uncertainty_type',
        value_name='auroc'
    )
    
    # Clean up labels
    df_melted['uncertainty_type'] = df_melted['uncertainty_type'].str.replace('_auroc', '').str.title()
    
    # Create figure
    fig, ax = plt.subplots(figsize=(14, 6))
    
    # Group by signal and plot
    signals = df['signal'].unique()
    x = range(len(signals))
    width = 0.25
    
    uncertainty_types = ['Aleatoric', 'Epistemic', 'Ood']
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
    
    for i, unc_type in enumerate(uncertainty_types):
        values = df_melted[df_melted['uncertainty_type'] == unc_type]['auroc'].values
        ax.bar([xi + i * width for xi in x], values, width, label=unc_type, color=colors[i])
    
    # Formatting
    ax.set_xlabel('Uncertainty Signal', fontsize=12, fontweight='bold')
    ax.set_ylabel('AUROC Score', fontsize=12, fontweight='bold')
    ax.set_title('Uncertainty Signal Performance Across Detection Tasks', fontsize=14, fontweight='bold')
    ax.set_xticks([xi + width for xi in x])
    ax.set_xticklabels(signals, rotation=45, ha='right')
    ax.legend(title='Uncertainty Type', loc='upper right')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_ylim(0, 1.0)
    
    # Add horizontal line at 0.5 (random baseline)
    ax.axhline(y=0.5, color='gray', linestyle='--', alpha=0.5, label='Random Baseline')
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✅ Saved plot to: {output_path}")
    
    return fig


def plot_signal_heatmap(df: pd.DataFrame, output_path: Path | None = None):
    """
    Create heatmap of AUROC scores
    
    Args:
        df: DataFrame with columns [signal, aleatoric_auroc, epistemic_auroc, ood_auroc]
        output_path: Optional path to save the figure
    """
    # Prepare data for heatmap
    heatmap_data = df.set_index('signal')[['aleatoric_auroc', 'epistemic_auroc', 'ood_auroc']]
    heatmap_data.columns = ['Aleatoric', 'Epistemic', 'OOD']
    
    # Create figure
    fig, ax = plt.subplots(figsize=(8, 10))
    
    # Create heatmap
    im = ax.imshow(heatmap_data.to_numpy(), cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)
    
    # Set ticks and labels
    ax.set_xticks(range(len(heatmap_data.columns)))
    ax.set_yticks(range(len(heatmap_data.index)))
    ax.set_xticklabels(heatmap_data.columns, fontsize=11, fontweight='bold')
    ax.set_yticklabels(heatmap_data.index, fontsize=10)
    
    # Rotate x labels
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('AUROC Score', rotation=270, labelpad=20, fontsize=11, fontweight='bold')
    
    # Add text annotations
    for i in range(len(heatmap_data.index)):
        for j in range(len(heatmap_data.columns)):
            value = heatmap_data.to_numpy()[i, j]
            color = 'white' if value < 0.5 else 'black'
            ax.text(j, i, f'{value:.3f}', ha="center", va="center", color=color, fontsize=9)
    
    ax.set_title('AUROC Heatmap: Signal Performance by Uncertainty Type', 
                 fontsize=13, fontweight='bold', pad=20)
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✅ Saved heatmap to: {output_path}")
    
    return fig


def calculate_disentanglement_scores(results_dir: Path) -> pd.DataFrame | None:
    """
    Calculate disentanglement error scores for available signal pairs.
    
    Returns DataFrame with columns: preset, aleatoric_signal, epistemic_signal,
    disentanglement_score, aleatorics_mean, epistemics_mean
    """
    results_pt = results_dir / "results.pt"
    if not results_pt.exists():
        return None
    
    try:
        from uqlab.evaluation.benchmarks.disentangling.bridge_sweep import (
            score_bridge_pairs_from_results,
            score_bridge_pair_with_vendor_metric
        )
        
        # Get all available bridge pairs
        bridge_results = score_bridge_pairs_from_results(results_pt)
        
        # Calculate DE score for each pair
        rows = []
        for result in bridge_results:
            if 'error' in result:
                continue  # Skip pairs with missing signals
            
            try:
                de_score = score_bridge_pair_with_vendor_metric(
                    results_pt,
                    predict_mode="paper",
                    aleatoric_signal=result['aleatoric_signal'],
                    epistemic_signal=result['epistemic_signal']
                )
                rows.append({
                    'preset': result['preset'],
                    'aleatoric_signal': result['aleatoric_signal'],
                    'epistemic_signal': result['epistemic_signal'],
                    'disentanglement_score': de_score,
                    'aleatorics_mean': result['aleatorics_mean'],
                    'epistemics_mean': result['epistemics_mean'],
                    'n_samples': result['n_samples']
                })
            except Exception as e:
                print(f"  ⚠️  Could not calculate DE for {result['preset']}: {e}")
                continue
        
        return pd.DataFrame(rows) if rows else None
        
    except ImportError as e:
        print(f"  ⚠️  Could not import disentanglement modules: {e}")
        return None
    except Exception as e:
        print(f"  ⚠️  Error calculating disentanglement scores: {e}")
        return None


def plot_disentanglement_scores(df: pd.DataFrame, output_path: Path | None = None):
    """
    Create bar plot of disentanglement error scores for different signal pairs.
    
    Lower DE scores indicate better disentanglement (orthogonality + consistency).
    """
    if df is None or df.empty:
        return None
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Sort by DE score (lower is better)
    df_sorted = df.sort_values('disentanglement_score')
    
    # Create bar plot
    x = range(len(df_sorted))
    bars = ax.bar(x, df_sorted['disentanglement_score'], color='#4ECDC4', alpha=0.8)
    
    # Color bars: green for good (< 0.3), yellow for medium (0.3-0.5), red for poor (> 0.5)
    for i, (idx, row) in enumerate(df_sorted.iterrows()):
        score = row['disentanglement_score']
        if score < 0.3:
            bars[i].set_color('#4CAF50')  # Green
        elif score < 0.5:
            bars[i].set_color('#FFC107')  # Yellow
        else:
            bars[i].set_color('#F44336')  # Red
    
    # Labels
    labels = [f"{row['preset']}\n({row['aleatoric_signal'][:15]}...\n{row['epistemic_signal'][:15]}...)"
              for _, row in df_sorted.iterrows()]
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=9)
    
    ax.set_xlabel('Signal Pair (Preset)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Disentanglement Error', fontsize=12, fontweight='bold')
    ax.set_title('Disentanglement Error Scores by Signal Pair\n(Lower = Better Separation)',
                 fontsize=14, fontweight='bold')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Add reference lines
    ax.axhline(y=0.3, color='green', linestyle='--', alpha=0.5, label='Good (< 0.3)')
    ax.axhline(y=0.5, color='orange', linestyle='--', alpha=0.5, label='Medium (< 0.5)')
    ax.legend(loc='upper right')
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✅ Saved DE plot to: {output_path}")
    
    return fig


def print_summary_statistics(df: pd.DataFrame, config: dict, de_df: pd.DataFrame | None = None):
    """Print summary statistics about the experiment"""
    print("\n" + "="*80)
    print("EXPERIMENT SUMMARY")
    print("="*80)
    
    # Configuration info
    print(f"\n📋 Configuration:")
    print(f"  Dataset: {config['data']['dataset_name']}")
    print(f"  Model: {config['model']['architecture']} ({config['model']['dinov2_model']})")
    print(f"  Training mode: {config['model']['training_mode']}")
    print(f"  Epochs: {config['training']['epochs']}")
    print(f"  MC passes: {config['evaluation']['mc_passes']}")
    
    # Data partitioning
    print(f"\n📊 Data Partitioning:")
    regions = config['data']['class_regions']
    for region_name, region_config in regions.items():
        classes = region_config['classes']
        train_frac = region_config.get('train_fraction', 1.0)
        noise = region_config.get('label_flip_pct', 0)
        print(f"  {region_name.title()}: classes {classes}, train_frac={train_frac:.1%}, noise={noise}%")
    
    # AUROC statistics
    print(f"\n📈 AUROC Statistics:")
    print(f"  Number of signals: {len(df)}")
    
    for col in ['aleatoric_auroc', 'epistemic_auroc', 'ood_auroc']:
        unc_type = col.replace('_auroc', '').title()
        mean_auroc = df[col].mean()
        max_auroc = df[col].max()
        min_auroc = df[col].min()
        best_signal = df.loc[df[col].idxmax(), 'signal']
        
        print(f"\n  {unc_type}:")
        print(f"    Mean AUROC: {mean_auroc:.4f}")
        print(f"    Range: [{min_auroc:.4f}, {max_auroc:.4f}]")
        print(f"    Best signal: {best_signal} ({max_auroc:.4f})")
    
    # Top 3 signals per uncertainty type
    print(f"\n🏆 Top 3 Signals per Uncertainty Type:")
    for col in ['aleatoric_auroc', 'epistemic_auroc', 'ood_auroc']:
        unc_type = col.replace('_auroc', '').title()
        top3 = df.nlargest(3, col)[['signal', col]]
        print(f"\n  {unc_type}:")
        for idx, row in top3.iterrows():
            print(f"    {row['signal']}: {row[col]:.4f}")
    
    # Disentanglement Error Statistics
    if de_df is not None and not de_df.empty:
        print(f"\n🔀 Disentanglement Error (DE) Scores:")
        print(f"  Number of signal pairs: {len(de_df)}")
        print(f"  Mean DE: {de_df['disentanglement_score'].mean():.4f}")
        print(f"  Best (lowest) DE: {de_df['disentanglement_score'].min():.4f}")
        print(f"  Worst (highest) DE: {de_df['disentanglement_score'].max():.4f}")
        
        best_pair = de_df.loc[de_df['disentanglement_score'].idxmin()]
        print(f"\n  🥇 Best Disentanglement:")
        print(f"    Preset: {best_pair['preset']}")
        print(f"    Aleatoric: {best_pair['aleatoric_signal']}")
        print(f"    Epistemic: {best_pair['epistemic_signal']}")
        print(f"    DE Score: {best_pair['disentanglement_score']:.4f}")
        print(f"    (Lower DE = better orthogonality + consistency)")


def main():
    """Main analysis function"""
    # Set up paths
    results_dir = PROJECT_ROOT / "results" / "my_run"
    output_dir = results_dir / "analysis"
    output_dir.mkdir(exist_ok=True)
    
    print(f"📂 Loading results from: {results_dir}")
    
    # Load data
    summary, config = load_experiment_results(results_dir)
    df = extract_auroc_dataframe(summary)
    
    # Calculate disentanglement scores
    print(f"\n🔀 Calculating disentanglement error scores...")
    de_df = calculate_disentanglement_scores(results_dir)
    
    # Print summary
    print_summary_statistics(df, config, de_df)
    
    # Create visualizations
    print(f"\n📊 Creating visualizations...")
    
    # AUROC plots
    fig1 = plot_auroc_comparison(df, output_dir / "auroc_comparison.png")
    fig2 = plot_signal_heatmap(df, output_dir / "auroc_heatmap.png")
    
    # Disentanglement plot
    if de_df is not None and not de_df.empty:
        fig3 = plot_disentanglement_scores(de_df, output_dir / "disentanglement_scores.png")
        
        # Save DE DataFrame to CSV
        de_csv_path = output_dir / "disentanglement_scores.csv"
        de_df.to_csv(de_csv_path, index=False)
        print(f"✅ Saved DE scores to: {de_csv_path}")
    
    # Save AUROC DataFrame to CSV
    csv_path = output_dir / "auroc_metrics.csv"
    df.to_csv(csv_path, index=False)
    print(f"✅ Saved AUROC metrics to: {csv_path}")
    
    # Show plots
    print(f"\n✨ Analysis complete! Check {output_dir} for outputs.")
    plt.show()


if __name__ == "__main__":
    main()

# Made with Bob
