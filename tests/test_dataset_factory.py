"""Tests for dataset registry and YAML dataset_name persistence."""

from __future__ import annotations

from uqlab.data.dataset_registry import (
    DATASET_SPECS,
    get_dataset_spec,
    list_dataset_names,
)
from uqlab_orchestrator.config import merge_workflow_defaults
from uqlab_orchestrator.run_spec import build_run_yaml


def test_registry_includes_mnist():
    names = list_dataset_names()
    assert "mnist" in names
    assert "cifar10" in names
    spec = get_dataset_spec("mnist")
    assert spec.num_classes == 10
    assert spec.default_root == "./data/mnist"


def test_build_run_yaml_persists_dataset_name_cifar10():
    workflow = merge_workflow_defaults({})
    workflow["dataset_config"]["dataset_name"] = "cifar10"
    cfg = build_run_yaml(workflow)
    assert cfg["data"]["dataset_name"] == "cifar10"
    assert cfg["paths"]["data_root"] == cfg["paths"]["cifar10n_root"]


def test_build_run_yaml_persists_dataset_name_mnist():
    workflow = merge_workflow_defaults({})
    workflow["dataset_config"]["dataset_name"] = "mnist"
    cfg = build_run_yaml(workflow)
    assert cfg["data"]["dataset_name"] == "mnist"
    assert cfg["paths"]["data_root"].endswith("data/mnist")


def test_dataset_catalog_matches_registry():
    from uqlab_orchestrator.config import DATASET_CATALOG

    assert set(DATASET_CATALOG.keys()) == set(DATASET_SPECS.keys())
