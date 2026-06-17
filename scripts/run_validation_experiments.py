#!/usr/bin/env python3
"""
Validation Experiment Runner

This script runs validation experiments for each configured architecture (default:
DINOv2 + MLP). MC-dropout uncertainty is computed at evaluation time as metrics,
not as a separate architecture sweep.

Usage:
    # Quick validation (for testing)
    python scripts/run_validation_experiments.py --mode quick

    # Full validation (for production)
    python scripts/run_validation_experiments.py --mode full

    # Run only dataset size sweep
    python scripts/run_validation_experiments.py --sweep dataset_size

    # Run only label noise sweep
    python scripts/run_validation_experiments.py --sweep label_noise
"""

import argparse
import subprocess
import sys
import tempfile
import yaml
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd
import json
from datetime import datetime
import shutil

# Project root (package lives in src/uqlab)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SRC = PROJECT_ROOT / "src"
for _p in (_SRC, PROJECT_ROOT):
    _s = str(_p)
    if _s not in sys.path:
        sys.path.insert(0, _s)

from uqlab.validation_config import (
    ARCHITECTURES,
    FIXED_REGULAR_TRAIN_PER_CLASS,
    FIXED_UNDER_TRAIN_ALEATORIC_ARM,
    LABEL_NOISE_SWEEP,
    LEGACY_ARCHITECTURE_LABELS,
    TRAINING_CONFIG,
    aligned_sweep_summary,
    aligned_under_train_sweep,
    create_experiment_config as create_config,
    epochs_for_under_train,
)


def run_experiment(
    config: Dict,
    output_dir: Path,
    experiment_name: str
) -> Tuple[bool, str]:
    """Run a single experiment with the given configuration."""
    
    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config, f)
        config_path = f.name
    
    try:
        # Run the experiment
        cmd = [
            sys.executable,
            str(PROJECT_ROOT / 'scripts' / 'run_fast_uncertainty_classification.py'),
            '--config', config_path,
            '--output_dir', str(output_dir)
        ]
        
        print(f"\n{'='*80}")
        print(f"Running: {experiment_name}")
        print(f"{'='*80}")
        print(f"Command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            error_msg = f"Experiment failed with return code {result.returncode}\n"
            error_msg += f"STDOUT:\n{result.stdout}\n"
            error_msg += f"STDERR:\n{result.stderr}"
            return False, error_msg
        
        print(f"✅ Experiment completed successfully")
        return True, result.stdout
        
    finally:
        # Clean up temporary config file
        Path(config_path).unlink(missing_ok=True)


# Reverse map for folder names → human labels (includes legacy MC-dropout sweeps).
ARCH_KEY_TO_LABEL: Dict[str, str] = {
    **LEGACY_ARCHITECTURE_LABELS,
    **{k: v["name"] for k, v in ARCHITECTURES.items()},
}


def _parse_experiment_folder(
    folder: Path, sweep_kind: str
) -> Tuple[str, float] | Tuple[None, None]:
    """Pull ``(architecture_label, sweep_value)`` out of an experiment folder name.

    Examples
    --------
    ``cnn_mcdropout_noise75``  → ``("CNN MC Dropout", 75.0)``  (label_noise)
    ``dinov2_mlp_size200``     → ``("DINOv2 + MLP", 200.0)``   (legacy dataset_size)
    ``dinov2_mlp_under150``    → ``("DINOv2 + MLP", 150.0)``   (under-train / Fig. 3)
    """
    name = folder.name
    if sweep_kind == 'label_noise':
        sep = '_noise'
    else:
        sep = '_under' if '_under' in name else '_size'
    if sep not in name:
        return None, None
    arch_key, _, val_str = name.rpartition(sep)
    label = ARCH_KEY_TO_LABEL.get(arch_key)
    if label is None:
        return None, None
    try:
        value = float(val_str)
    except ValueError:
        return None, None
    return label, value


def rebuild_metrics_from_folders(
    sweep_dir: Path,
    sweep_kind: str,
    *,
    metrics_csv: Path | None = None,
) -> pd.DataFrame:
    """Walk ``sweep_dir`` and rebuild metrics (row-by-row into ``metrics_csv`` if set)."""
    if not sweep_dir.is_dir():
        return pd.DataFrame()

    rows: List[Dict] = []
    for folder in sorted(sweep_dir.iterdir()):
        if not folder.is_dir():
            continue
        arch_label, value = _parse_experiment_folder(folder, sweep_kind)
        if arch_label is None or value is None:
            continue

        metrics = extract_metrics_from_results(folder)
        if not metrics:
            continue

        metrics['architecture'] = arch_label
        metrics['experiment_name'] = folder.name
        # We don't have the original run timestamp; use the directory mtime
        # so re-runs win when we deduplicate later.
        metrics['timestamp'] = datetime.fromtimestamp(folder.stat().st_mtime).isoformat()

        if sweep_kind == 'label_noise':
            metrics['noise_percent'] = value
            metrics['noise_rate'] = value / 100.0
        else:
            metrics['under_train_per_class'] = int(value)
            metrics['dataset_size'] = int(value)  # legacy column name

        rows.append(metrics)
        if metrics_csv is not None:
            _persist_experiment_metrics(
                metrics,
                output_dir=folder,
                metrics_csv=metrics_csv,
                sweep_kind=sweep_kind,
            )

    return pd.DataFrame(rows)


def _merge_metrics_into_csv(
    new_df: pd.DataFrame,
    csv_path: Path,
    sweep_kind: str,
) -> pd.DataFrame:
    """Merge many rows into ``metrics.csv`` (used by rebuild-only and end-of-sweep)."""
    from uqlab.run_artifacts import append_metrics_row_to_csv

    if new_df is None or new_df.empty:
        if csv_path.is_file():
            return pd.read_csv(csv_path)
        return pd.DataFrame()

    total = 0
    for _, row in new_df.iterrows():
        total = append_metrics_row_to_csv(
            row.to_dict(),
            csv_path,
            sweep_kind=sweep_kind,
        )
    if csv_path.is_file():
        return pd.read_csv(csv_path)
    return new_df


def extract_metrics_from_results(results_dir: Path) -> Dict:
    """Extract key metrics from one run folder (summary.json + results.pt)."""
    from uqlab.run_artifacts import metrics_row_from_run

    return metrics_row_from_run(Path(results_dir))


def _print_run_metrics_summary(metrics: Dict) -> None:
    from uqlab.run_artifacts import print_run_metrics_summary

    print_run_metrics_summary(metrics)


def _persist_experiment_metrics(
    metrics: Dict,
    *,
    output_dir: Path,
    metrics_csv: Path,
    sweep_kind: str,
) -> int:
    """Save per-run + sweep CSV rows immediately after each successful experiment."""
    from uqlab.run_artifacts import append_metrics_row_to_csv, save_run_metrics_row_csv

    save_run_metrics_row_csv(output_dir, metrics)
    n_rows = append_metrics_row_to_csv(metrics, metrics_csv, sweep_kind=sweep_kind)
    print(f"   📄 Appended row → {metrics_csv} ({n_rows} rows total)")
    return n_rows


def run_dataset_size_sweep(
    mode: str,
    output_base: Path,
    *,
    metrics_csv: Path,
) -> pd.DataFrame:
    """
    Fig. 3 — under-train / epistemic sweep (``under_train_per_class``).

    Uses the same 5-point (quick) or 11-point (full) grid as the API paired sweeps,
    not the legacy 3-point ``regular_train_per_class`` grid.
    """
    
    print("\n" + "="*80)
    print("UNDER-TRAIN SWEEP / Fig. 3 (epistemic, epoch-adjusted)")
    print("="*80)
    
    under_values = aligned_under_train_sweep(mode)
    summary = aligned_sweep_summary(mode)
    results = []
    
    print(f"Under-train per class: {under_values}")
    print(f"Fixed regular_train_per_class: {FIXED_REGULAR_TRAIN_PER_CLASS}")
    print(f"Label-noise arm (for reference): {summary['label_noise_percent']}")
    
    total_experiments = len(ARCHITECTURES) * len(under_values)
    current_experiment = 0
    
    for arch_key, arch_info in ARCHITECTURES.items():
        for under_train in under_values:
            current_experiment += 1
            adjusted_epochs = epochs_for_under_train(under_train, mode)
            
            print(f"\n[{current_experiment}/{total_experiments}] "
                  f"{arch_info['name']} - under_train={under_train}, "
                  f"regular={FIXED_REGULAR_TRAIN_PER_CLASS}, epochs={adjusted_epochs}")
            
            config = create_config(
                arch_key,
                mode,
                under_train_per_class=under_train,
                regular_train_per_class=FIXED_REGULAR_TRAIN_PER_CLASS,
                epochs=adjusted_epochs,
            )
            
            experiment_name = f"{arch_key}_under{under_train}"
            output_dir = output_base / experiment_name
            output_dir.mkdir(parents=True, exist_ok=True)
            
            success, output = run_experiment(config, output_dir, experiment_name)
            
            if not success:
                print(f"❌ Experiment failed: {experiment_name}")
                print(output)
                continue
            
            metrics = extract_metrics_from_results(output_dir)
            
            metrics['architecture'] = arch_info['name']
            metrics['under_train_per_class'] = under_train
            metrics['dataset_size'] = under_train  # legacy CSV column
            metrics['experiment_name'] = experiment_name
            metrics['timestamp'] = datetime.now().isoformat()
            
            results.append(metrics)
            _print_run_metrics_summary(metrics)
            _persist_experiment_metrics(
                metrics,
                output_dir=output_dir,
                metrics_csv=metrics_csv,
                sweep_kind="dataset_size",
            )
    
    return pd.DataFrame(results)


def run_label_noise_sweep(
    mode: str,
    output_base: Path,
    *,
    metrics_csv: Path,
) -> pd.DataFrame:
    """Run label noise sweep for all architectures."""
    
    print("\n" + "="*80)
    print("LABEL NOISE SWEEP")
    print("="*80)
    
    noise_rates = LABEL_NOISE_SWEEP[mode]
    results = []
    
    total_experiments = len(ARCHITECTURES) * len(noise_rates)
    current_experiment = 0
    
    for arch_key, arch_info in ARCHITECTURES.items():
        for noise_rate in noise_rates:
            current_experiment += 1
            
            print(f"\n[{current_experiment}/{total_experiments}] "
                  f"{arch_info['name']} - {noise_rate:.0f}% label noise")
            
            config = create_config(
                arch_key,
                mode,
                noise_rate=noise_rate,
                regular_train_per_class=FIXED_REGULAR_TRAIN_PER_CLASS,
                under_train_per_class=FIXED_UNDER_TRAIN_ALEATORIC_ARM,
            )
            
            # Create output directory
            experiment_name = f"{arch_key}_noise{int(noise_rate)}"
            output_dir = output_base / experiment_name
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Run experiment
            success, output = run_experiment(config, output_dir, experiment_name)
            
            if not success:
                print(f"❌ Experiment failed: {experiment_name}")
                print(output)
                continue
            
            # Extract metrics
            metrics = extract_metrics_from_results(output_dir)
            
            # Add metadata
            metrics['architecture'] = arch_info['name']
            metrics['noise_rate'] = noise_rate / 100.0
            metrics['noise_percent'] = noise_rate
            metrics['experiment_name'] = experiment_name
            metrics['timestamp'] = datetime.now().isoformat()
            
            results.append(metrics)
            _print_run_metrics_summary(metrics)
            _persist_experiment_metrics(
                metrics,
                output_dir=output_dir,
                metrics_csv=metrics_csv,
                sweep_kind="label_noise",
            )
    
    return pd.DataFrame(results)


def main():
    parser = argparse.ArgumentParser(
        description="Run validation experiments for all architectures",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick validation (for testing)
  python scripts/run_validation_experiments.py --mode quick

  # Full validation (for production)
  python scripts/run_validation_experiments.py --mode full

  # Run only dataset size sweep
  python scripts/run_validation_experiments.py --sweep dataset_size

  # Run only label noise sweep
  python scripts/run_validation_experiments.py --sweep label_noise
  
  # Quick dataset size sweep only
  python scripts/run_validation_experiments.py --mode quick --sweep dataset_size
        """
    )
    
    parser.add_argument(
        '--mode',
        type=str,
        choices=['quick', 'full'],
        default='quick',
        help='Validation mode: quick (fewer samples, faster) or full (complete validation)'
    )
    
    parser.add_argument(
        '--sweep',
        type=str,
        choices=['dataset_size', 'label_noise', 'both'],
        default='both',
        help='Which sweep to run: dataset_size, label_noise, or both'
    )
    
    parser.add_argument(
        '--output_dir',
        type=Path,
        default=None,
        help='Override output directory (default: results/validation/)'
    )

    parser.add_argument(
        '--rebuild-only',
        action='store_true',
        help=(
            'Skip running any experiments. Walk every existing experiment '
            'folder under results/validation/<sweep>_sweep/, re-extract '
            'metrics from each folder\'s results.pt, and merge them into the '
            'unified metrics.csv. Use this when sub-experiment folders for '
            'noise levels 75/90 (etc.) exist on disk but metrics.csv only '
            'has the older 0–50 range.'
        ),
    )

    args = parser.parse_args()
    
    # Set up output directories
    if args.output_dir:
        validation_dir = args.output_dir
    else:
        validation_dir = PROJECT_ROOT / 'results' / 'validation'
    
    validation_dir.mkdir(parents=True, exist_ok=True)
    
    print("="*80)
    print("VALIDATION EXPERIMENT RUNNER")
    print("="*80)
    print(f"Mode: {args.mode}")
    print(f"Sweep: {args.sweep}")
    print(f"Output directory: {validation_dir}")
    print(f"Project root: {PROJECT_ROOT}")
    
    if args.mode == 'quick':
        print("\n⚠️  Running in QUICK mode - results are for testing only!")
        print("   Use --mode full for production validation data.")
    
    # Run sweeps
    results_summary = {}
    
    if args.sweep in ['dataset_size', 'both']:
        dataset_size_dir = validation_dir / 'dataset_size_sweep'
        dataset_size_dir.mkdir(parents=True, exist_ok=True)
        metrics_file = dataset_size_dir / 'metrics.csv'

        if args.rebuild_only:
            print("\n[rebuild-only] Walking existing dataset_size_sweep folders…")
            df_dataset_size = rebuild_metrics_from_folders(
                dataset_size_dir,
                sweep_kind='dataset_size',
                metrics_csv=metrics_file,
            )
            merged = (
                pd.read_csv(metrics_file)
                if metrics_file.is_file()
                else df_dataset_size
            )
        else:
            print(f"Metrics CSV (row-by-row): {metrics_file}")
            run_dataset_size_sweep(
                args.mode, dataset_size_dir, metrics_csv=metrics_file
            )
            merged = (
                pd.read_csv(metrics_file)
                if metrics_file.is_file()
                else pd.DataFrame()
            )
        print(f"\n✅ Dataset size sweep CSV: {metrics_file}  ({len(merged)} rows)")

        results_summary['dataset_size'] = {
            'experiments': len(merged),
            'output_file': str(metrics_file),
            'total_rows': len(merged),
        }

    if args.sweep in ['label_noise', 'both']:
        label_noise_dir = validation_dir / 'label_noise_sweep'
        label_noise_dir.mkdir(parents=True, exist_ok=True)
        metrics_file = label_noise_dir / 'metrics.csv'

        if args.rebuild_only:
            print("\n[rebuild-only] Walking existing label_noise_sweep folders…")
            df_label_noise = rebuild_metrics_from_folders(
                label_noise_dir,
                sweep_kind='label_noise',
                metrics_csv=metrics_file,
            )
            merged = (
                pd.read_csv(metrics_file)
                if metrics_file.is_file()
                else df_label_noise
            )
        else:
            print(f"Metrics CSV (row-by-row): {metrics_file}")
            run_label_noise_sweep(
                args.mode, label_noise_dir, metrics_csv=metrics_file
            )
            merged = (
                pd.read_csv(metrics_file)
                if metrics_file.is_file()
                else pd.DataFrame()
            )
        print(f"\n✅ Label noise sweep CSV: {metrics_file}  ({len(merged)} rows)")

        results_summary['label_noise'] = {
            'experiments': len(merged),
            'output_file': str(metrics_file),
            'total_rows': len(merged),
        }
    
    # Print summary
    print("\n" + "="*80)
    print("VALIDATION EXPERIMENTS COMPLETE")
    print("="*80)
    
    for sweep_type, info in results_summary.items():
        print(f"\n{sweep_type.replace('_', ' ').title()}:")
        print(f"  Experiments: {info['experiments']}")
        print(f"  Results: {info['output_file']}")
    
    print("\n✅ Validation data is ready!")
    print("\nNext steps:")
    print("  1. Run the validation notebooks to analyze results:")
    print("     - notebooks/validation/dataset_size_validation.ipynb")
    print("     - notebooks/validation/label_noise_validation.ipynb")
    print("     - notebooks/validation/logical_consistency_validation.ipynb")
    print("  2. Review the validation reports in results/validation/")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

# Made with Bob
