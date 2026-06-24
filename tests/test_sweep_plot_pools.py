"""Tests for config-implicit sweep pool expectations."""

from uqlab.evaluation.pipeline.sweep_plot_pools import (
    pool_expectations_from_data_config,
    primary_pool_for_sweep,
)
from uqlab.evaluation.pipeline.sweep_line_plot import (
    SWEEP_KIND_DATASET_SIZE,
    SWEEP_KIND_LABEL_NOISE,
)


def test_pool_expectations_balanced_under_train():
    exp = pool_expectations_from_data_config(
        {
            "under_supported_classes": [3, 5],
            "under_train_per_class": 300,
            "regular_train_per_class": 300,
            "aleatoric_noise_percentage": 25,
        }
    )
    assert exp.epistemic_pool_expected is False
    assert exp.aleatoric_pool_expected is True


def test_pool_expectations_no_under_classes():
    exp = pool_expectations_from_data_config(
        {"under_supported_classes": [], "aleatoric_noise_percentage": 0}
    )
    assert exp.epistemic_pool_expected is False
    assert exp.aleatoric_pool_expected is False


def test_pool_expectations_four_region():
    exp = pool_expectations_from_data_config(
        {"partition_mode": "four_region", "class_regions": {}}
    )
    assert exp.epistemic_pool_expected is True
    assert exp.aleatoric_pool_expected is True
    assert exp.ood_pool_expected is True


def test_eval_pool_counts_includes_ood(tmp_path):
    import torch

    from uqlab.evaluation.pipeline.sweep_plot_pools import eval_pool_counts_from_results_dir
    from uqlab.run_artifacts import GROUP_OOD

    results_dir = tmp_path / "results"
    results_dir.mkdir()
    labels = torch.tensor([0, 1, 2, GROUP_OOD, GROUP_OOD])
    torch.save({"eval_group_labels": labels}, results_dir / "results.pt")
    counts = eval_pool_counts_from_results_dir(results_dir)
    assert counts["ood_like"] == 2
    assert counts["clean"] == 1


def test_primary_pool_for_sweep():
    assert primary_pool_for_sweep(SWEEP_KIND_LABEL_NOISE) == "aleatoric"
    assert primary_pool_for_sweep(SWEEP_KIND_DATASET_SIZE) == "epistemic"
