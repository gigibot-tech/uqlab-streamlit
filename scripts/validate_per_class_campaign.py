#!/usr/bin/env python3
"""
Validate per-class configuration campaigns for uncertainty quantification.

This script validates that per-class configurations produce expected uncertainty
patterns and exports results showing which metrics correlate correctly.

Expected Patterns:
- OOD classes (0 training samples) → Highest uncertainty
- Sparse classes (few samples) → High epistemic uncertainty
- Noisy classes (high label noise) → High aleatoric uncertainty
- Clean classes (many samples, no noise) → Lowest uncertainty

Usage:
    # Validate a campaign and export results
    PYTHONPATH=src python3 scripts/validate_per_class_campaign.py \\
        --run-ids uuid1,uuid2,uuid3 \\
        --output validation_report.json

    # Validate with specific thresholds
    PYTHONPATH=src python3 scripts/validate_per_class_campaign.py \\
        --run-ids uuid1,uuid2,uuid3 \\
        --ood-threshold 0.8 \\
        --sparse-threshold 0.6 \\
        --output validation_report.json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from uqlab.shared.config.classification import PerClassConfig, DataConfig
from uqlab.run_artifacts import load_experiment_artifacts


@dataclass
class ValidationCriteria:
    """Validation criteria for uncertainty patterns."""
    
    # Thresholds for uncertainty levels (0-1 scale)
    ood_uncertainty_threshold: float = 0.8  # OOD should have >80% uncertainty
    sparse_uncertainty_threshold: float = 0.6  # Sparse should have >60%
    noisy_uncertainty_threshold: float = 0.5  # Noisy should have >50%
    clean_uncertainty_threshold: float = 0.3  # Clean should have <30%
    
    # Correlation thresholds
    epistemic_correlation_threshold: float = -0.7  # Negative correlation with samples
    aleatoric_correlation_threshold: float = 0.7  # Positive correlation with noise


@dataclass
class ClassValidation:
    """Validation result for a single class."""
    
    class_id: int
    class_name: str
    train_samples: int
    label_noise_pct: float
    
    # Measured uncertainty
    mean_uncertainty: float
    epistemic_uncertainty: float
    aleatoric_uncertainty: float
    
    # Validation results
    expected_pattern: str  # "OOD", "Sparse", "Noisy", "Clean"
    pattern_satisfied: bool
    threshold_used: float
    
    # Additional context
    experiment_id: str
    notes: List[str]


@dataclass
class CampaignValidation:
    """Validation result for entire campaign."""
    
    campaign_name: str
    total_experiments: int
    validated_experiments: int
    
    # Per-class validations
    class_validations: List[ClassValidation]
    
    # Overall metrics
    ood_pattern_satisfied: bool
    sparse_pattern_satisfied: bool
    noisy_pattern_satisfied: bool
    clean_pattern_satisfied: bool
    
    # Correlation metrics
    epistemic_correlation: Optional[float]
    aleatoric_correlation: Optional[float]
    epistemic_correlation_satisfied: bool
    aleatoric_correlation_satisfied: bool
    
    # Summary
    total_patterns_checked: int
    patterns_satisfied: int
    validation_score: float  # 0-1
    
    # Detailed findings
    satisfied_metrics: List[Dict[str, Any]]
    failed_metrics: List[Dict[str, Any]]


def classify_class_pattern(
    train_samples: int,
    label_noise_pct: float
) -> Tuple[str, float]:
    """Classify expected uncertainty pattern for a class.
    
    Returns:
        Tuple of (pattern_name, expected_threshold)
    """
    if train_samples == 0:
        return ("OOD", 0.8)
    elif train_samples < 100:
        return ("Sparse", 0.6)
    elif label_noise_pct > 20:
        return ("Noisy", 0.5)
    else:
        return ("Clean", 0.3)


def validate_class_uncertainty(
    class_id: int,
    class_name: str,
    config: PerClassConfig,
    uncertainty_scores: Dict[str, float],
    experiment_id: str,
    criteria: ValidationCriteria
) -> ClassValidation:
    """Validate uncertainty pattern for a single class.
    
    Args:
        class_id: Class ID (0-9)
        class_name: Human-readable class name
        config: Per-class configuration
        uncertainty_scores: Dict with 'mean', 'epistemic', 'aleatoric' keys
        experiment_id: Experiment UUID
        criteria: Validation criteria
        
    Returns:
        ClassValidation result
    """
    pattern, threshold = classify_class_pattern(
        config.train_samples,
        config.label_noise_pct
    )
    
    mean_unc = uncertainty_scores.get("mean", 0.0)
    epistemic = uncertainty_scores.get("epistemic", 0.0)
    aleatoric = uncertainty_scores.get("aleatoric", 0.0)
    
    # Check if pattern is satisfied
    if pattern == "OOD":
        satisfied = mean_unc >= threshold
    elif pattern == "Sparse":
        satisfied = epistemic >= threshold
    elif pattern == "Noisy":
        satisfied = aleatoric >= threshold
    else:  # Clean
        satisfied = mean_unc <= threshold
    
    # Generate notes
    notes = []
    if pattern == "OOD" and config.train_samples == 0:
        notes.append("Out-of-distribution class (no training samples)")
    if pattern == "Sparse":
        notes.append(f"Sparse training data ({config.train_samples} samples)")
    if pattern == "Noisy" and config.label_noise_pct > 0:
        notes.append(f"High label noise ({config.label_noise_pct}%)")
    if pattern == "Clean":
        notes.append(f"Clean, well-supported class ({config.train_samples} samples, {config.label_noise_pct}% noise)")
    
    return ClassValidation(
        class_id=class_id,
        class_name=class_name,
        train_samples=config.train_samples,
        label_noise_pct=config.label_noise_pct,
        mean_uncertainty=mean_unc,
        epistemic_uncertainty=epistemic,
        aleatoric_uncertainty=aleatoric,
        expected_pattern=pattern,
        pattern_satisfied=satisfied,
        threshold_used=threshold,
        experiment_id=experiment_id,
        notes=notes
    )


def calculate_correlations(
    class_validations: List[ClassValidation]
) -> Tuple[Optional[float], Optional[float]]:
    """Calculate correlation between config and uncertainty.
    
    Returns:
        Tuple of (epistemic_correlation, aleatoric_correlation)
    """
    if len(class_validations) < 3:
        return None, None
    
    try:
        import numpy as np
        
        # Epistemic: correlation between train_samples and epistemic uncertainty
        # Expected: negative correlation (fewer samples → higher uncertainty)
        samples = np.array([v.train_samples for v in class_validations])
        epistemic = np.array([v.epistemic_uncertainty for v in class_validations])
        
        if len(samples) > 1 and np.std(samples) > 0:
            epistemic_corr = np.corrcoef(samples, epistemic)[0, 1]
        else:
            epistemic_corr = None
        
        # Aleatoric: correlation between label_noise_pct and aleatoric uncertainty
        # Expected: positive correlation (more noise → higher uncertainty)
        noise = np.array([v.label_noise_pct for v in class_validations])
        aleatoric = np.array([v.aleatoric_uncertainty for v in class_validations])
        
        if len(noise) > 1 and np.std(noise) > 0:
            aleatoric_corr = np.corrcoef(noise, aleatoric)[0, 1]
        else:
            aleatoric_corr = None
        
        return epistemic_corr, aleatoric_corr
    
    except ImportError:
        print("Warning: numpy not available, skipping correlation analysis", file=sys.stderr)
        return None, None


def validate_campaign(
    run_ids: List[str],
    experiments_dir: Path,
    criteria: ValidationCriteria,
    class_names: Optional[List[str]] = None
) -> CampaignValidation:
    """Validate entire campaign of experiments.
    
    Args:
        run_ids: List of experiment UUIDs
        experiments_dir: Directory containing experiment artifacts
        criteria: Validation criteria
        class_names: Optional list of class names (default: CIFAR-10)
        
    Returns:
        CampaignValidation result
    """
    if class_names is None:
        class_names = [
            "airplane", "automobile", "bird", "cat", "deer",
            "dog", "frog", "horse", "ship", "truck"
        ]
    
    class_validations = []
    validated_count = 0
    
    for run_id in run_ids:
        try:
            # Load experiment artifacts
            artifacts = load_experiment_artifacts(experiments_dir / run_id)
            
            # Extract per-class config
            config_dict = artifacts.get("config", {})
            data_config_dict = config_dict.get("data", {})
            per_class_config = data_config_dict.get("per_class_config", {})
            
            if not per_class_config:
                print(f"Warning: No per-class config found for {run_id}", file=sys.stderr)
                continue
            
            # Extract uncertainty scores per class
            results = artifacts.get("results", {})
            per_class_uncertainty = results.get("per_class_uncertainty", {})
            
            if not per_class_uncertainty:
                print(f"Warning: No per-class uncertainty found for {run_id}", file=sys.stderr)
                continue
            
            # Validate each class
            for class_id_str, class_config_dict in per_class_config.items():
                class_id = int(class_id_str)
                class_name = class_names[class_id] if class_id < len(class_names) else f"class_{class_id}"
                
                # Convert dict to PerClassConfig
                class_config = PerClassConfig(**class_config_dict)
                
                # Get uncertainty scores for this class
                class_uncertainty = per_class_uncertainty.get(str(class_id), {})
                
                validation = validate_class_uncertainty(
                    class_id=class_id,
                    class_name=class_name,
                    config=class_config,
                    uncertainty_scores=class_uncertainty,
                    experiment_id=run_id,
                    criteria=criteria
                )
                
                class_validations.append(validation)
            
            validated_count += 1
            
        except Exception as e:
            print(f"Error validating {run_id}: {e}", file=sys.stderr)
            continue
    
    # Calculate overall pattern satisfaction
    ood_validations = [v for v in class_validations if v.expected_pattern == "OOD"]
    sparse_validations = [v for v in class_validations if v.expected_pattern == "Sparse"]
    noisy_validations = [v for v in class_validations if v.expected_pattern == "Noisy"]
    clean_validations = [v for v in class_validations if v.expected_pattern == "Clean"]
    
    ood_satisfied = all(v.pattern_satisfied for v in ood_validations) if ood_validations else True
    sparse_satisfied = all(v.pattern_satisfied for v in sparse_validations) if sparse_validations else True
    noisy_satisfied = all(v.pattern_satisfied for v in noisy_validations) if noisy_validations else True
    clean_satisfied = all(v.pattern_satisfied for v in clean_validations) if clean_validations else True
    
    # Calculate correlations
    epistemic_corr, aleatoric_corr = calculate_correlations(class_validations)
    
    epistemic_corr_satisfied = (
        epistemic_corr is not None and 
        epistemic_corr <= criteria.epistemic_correlation_threshold
    )
    aleatoric_corr_satisfied = (
        aleatoric_corr is not None and 
        aleatoric_corr >= criteria.aleatoric_correlation_threshold
    )
    
    # Calculate validation score
    patterns_satisfied = sum([
        v.pattern_satisfied for v in class_validations
    ])
    total_patterns = len(class_validations)
    
    validation_score = patterns_satisfied / total_patterns if total_patterns > 0 else 0.0
    
    # Build satisfied/failed metrics lists
    satisfied_metrics = []
    failed_metrics = []
    
    for v in class_validations:
        metric_info = {
            "class_id": v.class_id,
            "class_name": v.class_name,
            "pattern": v.expected_pattern,
            "experiment_id": v.experiment_id,
            "uncertainty": v.mean_uncertainty,
            "threshold": v.threshold_used,
            "notes": v.notes
        }
        
        if v.pattern_satisfied:
            satisfied_metrics.append(metric_info)
        else:
            failed_metrics.append(metric_info)
    
    # Add correlation metrics
    if epistemic_corr_satisfied:
        satisfied_metrics.append({
            "metric": "epistemic_correlation",
            "value": epistemic_corr,
            "threshold": criteria.epistemic_correlation_threshold,
            "description": "Negative correlation between training samples and epistemic uncertainty"
        })
    elif epistemic_corr is not None:
        failed_metrics.append({
            "metric": "epistemic_correlation",
            "value": epistemic_corr,
            "threshold": criteria.epistemic_correlation_threshold,
            "description": "Expected negative correlation between training samples and epistemic uncertainty"
        })
    
    if aleatoric_corr_satisfied:
        satisfied_metrics.append({
            "metric": "aleatoric_correlation",
            "value": aleatoric_corr,
            "threshold": criteria.aleatoric_correlation_threshold,
            "description": "Positive correlation between label noise and aleatoric uncertainty"
        })
    elif aleatoric_corr is not None:
        failed_metrics.append({
            "metric": "aleatoric_correlation",
            "value": aleatoric_corr,
            "threshold": criteria.aleatoric_correlation_threshold,
            "description": "Expected positive correlation between label noise and aleatoric uncertainty"
        })
    
    return CampaignValidation(
        campaign_name=f"campaign_{len(run_ids)}_experiments",
        total_experiments=len(run_ids),
        validated_experiments=validated_count,
        class_validations=class_validations,
        ood_pattern_satisfied=ood_satisfied,
        sparse_pattern_satisfied=sparse_satisfied,
        noisy_pattern_satisfied=noisy_satisfied,
        clean_pattern_satisfied=clean_satisfied,
        epistemic_correlation=epistemic_corr,
        aleatoric_correlation=aleatoric_corr,
        epistemic_correlation_satisfied=epistemic_corr_satisfied,
        aleatoric_correlation_satisfied=aleatoric_corr_satisfied,
        total_patterns_checked=total_patterns,
        patterns_satisfied=patterns_satisfied,
        validation_score=validation_score,
        satisfied_metrics=satisfied_metrics,
        failed_metrics=failed_metrics
    )


def print_validation_report(validation: CampaignValidation) -> None:
    """Print human-readable validation report."""
    
    print(f"\n{'='*80}")
    print(f"CAMPAIGN VALIDATION REPORT: {validation.campaign_name}")
    print(f"{'='*80}\n")
    
    print(f"Experiments: {validation.validated_experiments}/{validation.total_experiments} validated")
    print(f"Validation Score: {validation.validation_score:.1%}")
    print(f"Patterns Satisfied: {validation.patterns_satisfied}/{validation.total_patterns_checked}\n")
    
    print("Pattern Validation:")
    print(f"  ✓ OOD (0 samples):     {'PASS' if validation.ood_pattern_satisfied else 'FAIL'}")
    print(f"  ✓ Sparse (<100):       {'PASS' if validation.sparse_pattern_satisfied else 'FAIL'}")
    print(f"  ✓ Noisy (>20% noise):  {'PASS' if validation.noisy_pattern_satisfied else 'FAIL'}")
    print(f"  ✓ Clean (many/clean):  {'PASS' if validation.clean_pattern_satisfied else 'FAIL'}\n")
    
    if validation.epistemic_correlation is not None:
        print("Correlation Analysis:")
        print(f"  Epistemic (samples ↔ uncertainty): {validation.epistemic_correlation:+.3f} "
              f"{'✓ PASS' if validation.epistemic_correlation_satisfied else '✗ FAIL'}")
    
    if validation.aleatoric_correlation is not None:
        print(f"  Aleatoric (noise ↔ uncertainty):   {validation.aleatoric_correlation:+.3f} "
              f"{'✓ PASS' if validation.aleatoric_correlation_satisfied else '✗ FAIL'}\n")
    
    if validation.satisfied_metrics:
        print(f"\n✓ SATISFIED METRICS ({len(validation.satisfied_metrics)}):")
        for metric in validation.satisfied_metrics[:10]:  # Show first 10
            if "class_id" in metric:
                print(f"  • Class {metric['class_id']} ({metric['class_name']}): "
                      f"{metric['pattern']} pattern satisfied "
                      f"(uncertainty={metric['uncertainty']:.3f}, threshold={metric['threshold']:.3f})")
                print(f"    Experiment: {metric['experiment_id'][:8]}")
            else:
                print(f"  • {metric['metric']}: {metric['value']:.3f} "
                      f"(threshold={metric['threshold']:.3f})")
        
        if len(validation.satisfied_metrics) > 10:
            print(f"  ... and {len(validation.satisfied_metrics) - 10} more")
    
    if validation.failed_metrics:
        print(f"\n✗ FAILED METRICS ({len(validation.failed_metrics)}):")
        for metric in validation.failed_metrics:
            if "class_id" in metric:
                print(f"  • Class {metric['class_id']} ({metric['class_name']}): "
                      f"{metric['pattern']} pattern NOT satisfied "
                      f"(uncertainty={metric['uncertainty']:.3f}, threshold={metric['threshold']:.3f})")
                print(f"    Experiment: {metric['experiment_id'][:8]}")
            else:
                print(f"  • {metric['metric']}: {metric['value']:.3f} "
                      f"(threshold={metric['threshold']:.3f})")
    
    print(f"\n{'='*80}\n")


def main(argv: List[str] | None = None) -> int:
    """Main entry point."""
    
    parser = argparse.ArgumentParser(
        description="Validate per-class configuration campaigns for uncertainty quantification."
    )
    parser.add_argument(
        "--run-ids",
        required=True,
        help="Comma-separated experiment UUIDs"
    )
    parser.add_argument(
        "--experiments-dir",
        type=Path,
        default=PROJECT_ROOT / "data" / "experiments",
        help="Directory containing experiment artifacts"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output JSON file for validation results"
    )
    parser.add_argument(
        "--ood-threshold",
        type=float,
        default=0.8,
        help="Uncertainty threshold for OOD classes (default: 0.8)"
    )
    parser.add_argument(
        "--sparse-threshold",
        type=float,
        default=0.6,
        help="Uncertainty threshold for sparse classes (default: 0.6)"
    )
    parser.add_argument(
        "--noisy-threshold",
        type=float,
        default=0.5,
        help="Uncertainty threshold for noisy classes (default: 0.5)"
    )
    parser.add_argument(
        "--clean-threshold",
        type=float,
        default=0.3,
        help="Uncertainty threshold for clean classes (default: 0.3)"
    )
    parser.add_argument(
        "--epistemic-correlation",
        type=float,
        default=-0.7,
        help="Threshold for epistemic correlation (default: -0.7)"
    )
    parser.add_argument(
        "--aleatoric-correlation",
        type=float,
        default=0.7,
        help="Threshold for aleatoric correlation (default: 0.7)"
    )
    
    args = parser.parse_args(argv)
    
    # Parse run IDs
    run_ids = [r.strip() for r in args.run_ids.split(",") if r.strip()]
    
    if not run_ids:
        print("Error: No run IDs provided", file=sys.stderr)
        return 1
    
    # Create validation criteria
    criteria = ValidationCriteria(
        ood_uncertainty_threshold=args.ood_threshold,
        sparse_uncertainty_threshold=args.sparse_threshold,
        noisy_uncertainty_threshold=args.noisy_threshold,
        clean_uncertainty_threshold=args.clean_threshold,
        epistemic_correlation_threshold=args.epistemic_correlation,
        aleatoric_correlation_threshold=args.aleatoric_correlation
    )
    
    # Validate campaign
    try:
        validation = validate_campaign(
            run_ids=run_ids,
            experiments_dir=args.experiments_dir,
            criteria=criteria
        )
    except Exception as e:
        print(f"Error during validation: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1
    
    # Print report
    print_validation_report(validation)
    
    # Export to JSON if requested
    if args.output:
        output_data = asdict(validation)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        
        with open(args.output, "w") as f:
            json.dump(output_data, f, indent=2)
        
        print(f"Validation results exported to: {args.output}")
    
    # Return exit code based on validation score
    if validation.validation_score >= 0.8:
        return 0  # Success
    elif validation.validation_score >= 0.6:
        return 1  # Warning
    else:
        return 2  # Failure


if __name__ == "__main__":
    raise SystemExit(main())

# Made with Bob
