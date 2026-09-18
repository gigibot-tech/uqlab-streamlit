"""
Validation functions for logical consistency checks.

These functions are used by the logical_consistency_validation.ipynb notebook
to perform comprehensive validation of uncertainty quantification results.
"""

import pandas as pd
import numpy as np


def validate_uncertainty_decomposition(df, tolerance=0.05):
    """Validate that total uncertainty ≈ epistemic + aleatoric.
    
    Args:
        df: DataFrame with uncertainty metrics
        tolerance: Relative tolerance (default 5%)
    
    Returns:
        DataFrame with validation results
    """
    if df.empty:
        return pd.DataFrame()
    
    results = []
    
    for idx, row in df.iterrows():
        # Skip if missing required columns
        if pd.isna(row.get('mean_epistemic_uncertainty')) or pd.isna(row.get('mean_aleatoric_uncertainty')) or pd.isna(row.get('mean_total_uncertainty')):
            continue
        
        epistemic = row['mean_epistemic_uncertainty']
        aleatoric = row['mean_aleatoric_uncertainty']
        total_measured = row['mean_total_uncertainty']
        total_expected = epistemic + aleatoric
        
        # Calculate error
        absolute_error = abs(total_measured - total_expected)
        relative_error = absolute_error / max(total_expected, 1e-10)  # Avoid division by zero
        
        # Check if within tolerance
        passed = relative_error <= tolerance
        
        results.append({
            'architecture': row.get('architecture', 'Unknown'),
            'sweep_type': row.get('sweep_type', 'Unknown'),
            'epistemic': epistemic,
            'aleatoric': aleatoric,
            'total_measured': total_measured,
            'total_expected': total_expected,
            'absolute_error': absolute_error,
            'relative_error': relative_error,
            'passed': passed
        })
    
    return pd.DataFrame(results)


def validate_non_negativity_and_bounds(df):
    """Validate that all metrics are within valid ranges.
    
    Args:
        df: DataFrame with metrics
    
    Returns:
        Dictionary with validation results
    """
    if df.empty:
        return {'total_samples': 0, 'checks': []}
    
    checks = []
    
    # Check accuracy bounds [0, 1]
    if 'accuracy' in df.columns:
        violations = ((df['accuracy'] < 0) | (df['accuracy'] > 1)).sum()
        nan_count = df['accuracy'].isna().sum()
        checks.append({
            'metric': 'accuracy',
            'check': 'in [0, 1]',
            'violations': int(violations),
            'nan_count': int(nan_count),
            'passed': violations == 0 and nan_count == 0
        })
    
    # Check uncertainty non-negativity
    uncertainty_metrics = ['mean_epistemic_uncertainty', 'std_epistemic_uncertainty', 'mean_aleatoric_uncertainty', 'std_aleatoric_uncertainty', 'mean_total_uncertainty']
    for metric in uncertainty_metrics:
        if metric in df.columns:
            violations = (df[metric] < 0).sum()
            nan_count = df[metric].isna().sum()
            checks.append({
                'metric': metric,
                'check': '>= 0',
                'violations': int(violations),
                'nan_count': int(nan_count),
                'passed': violations == 0 and nan_count == 0
            })
    
    # Check for infinite values
    for metric in ['accuracy', 'mean_epistemic_uncertainty', 'mean_aleatoric_uncertainty', 'mean_total_uncertainty']:
        if metric in df.columns:
            inf_count = np.isinf(df[metric]).sum()
            checks.append({
                'metric': metric,
                'check': 'no inf values',
                'violations': int(inf_count),
                'nan_count': 0,
                'passed': inf_count == 0
            })
    
    return {
        'total_samples': len(df),
        'checks': checks
    }


def validate_monotonicity(df, x_col, y_col, expected_direction='increase'):
    """Validate monotonic relationship between two variables.
    
    Args:
        df: DataFrame with data
        x_col: Independent variable column name
        y_col: Dependent variable column name
        expected_direction: 'increase' or 'decrease'
    
    Returns:
        Dictionary with validation results
    """
    from scipy import stats
    
    if df.empty or x_col not in df.columns or y_col not in df.columns:
        return {'error': 'Missing required columns'}
    
    # Remove NaN values
    clean_df = df[[x_col, y_col]].dropna()
    
    if len(clean_df) < 3:
        return {'error': 'Insufficient data points'}
    
    x = clean_df[x_col].values
    y = clean_df[y_col].values
    
    # Spearman correlation (monotonic relationship)
    corr, p_value = stats.spearmanr(x, y)
    
    # Linear regression
    slope, intercept, r_value, p_value_reg, std_err = stats.linregress(x, y)
    
    # Check if trend matches expectation
    if expected_direction == 'increase':
        trend_correct = slope > 0 and corr > 0
    else:  # decrease
        trend_correct = slope < 0 and corr < 0
    
    return {
        'x_column': x_col,
        'y_column': y_col,
        'expected_direction': expected_direction,
        'spearman_corr': corr,
        'spearman_p': p_value,
        'linear_slope': slope,
        'linear_r2': r_value**2,
        'linear_p': p_value_reg,
        'trend_correct': trend_correct,
        'significant': p_value < 0.05
    }

# Made with Bob
