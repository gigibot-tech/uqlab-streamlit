#!/usr/bin/env python3
"""Paper-style disentanglement benchmark via vendored metric + ExperimentDisentanglingModel."""

from uqlab.evaluation.benchmarks.disentangling import (
    ExperimentDisentanglingModel,
    calculate_disentanglement_error,
    collect_cifar10_arrays,
    json_results_to_df,
)

X, y = collect_cifar10_arrays()
model = ExperimentDisentanglingModel.from_workflow_defaults()
score, results_json, config_json = calculate_disentanglement_error(
    X, y, model, kw_config={"n_runs": 1}, return_json=True,
)
print("disentanglement error:", score)
json_results_to_df(results_json, config_json).to_csv("disentanglement_curves.csv")
