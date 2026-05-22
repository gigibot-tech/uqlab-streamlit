"""Lightweight post-merge integration test for walaris-cen/uq_classification.

Goals:
- Verify new exports from package __init__ work
- Exercise ExperimentTracker in JSON mode
- Exercise decision boundary visualization with minimal synthetic data
- Confirm selected existing production exports remain importable
- Provide clear pass/fail reporting without requiring heavy dependencies
"""

from __future__ import annotations

import importlib.util
import json
import sys
import traceback
from pathlib import Path
from tempfile import TemporaryDirectory

WALARIS_CEN_ROOT = Path(__file__).resolve().parent.parent
if str(WALARIS_CEN_ROOT) not in sys.path:
    sys.path.insert(0, str(WALARIS_CEN_ROOT))

import matplotlib
matplotlib.use("Agg")
import numpy as np


SCRIPT_PATH = Path(__file__).resolve()
PACKAGE_DIR = SCRIPT_PATH.parent
PROJECT_ROOT = PACKAGE_DIR.parent
RESULTS = []


def record(name: str, passed: bool, details: str = "") -> None:
    status = "PASS" if passed else "FAIL"
    RESULTS.append((name, passed, details))
    line = f"[{status}] {name}"
    if details:
        line += f" - {details}"
    print(line)


def run_test(name: str, fn) -> bool:
    try:
        fn()
        record(name, True)
        return True
    except Exception as exc:  # noqa: BLE001
        detail = f"{type(exc).__name__}: {exc}"
        record(name, False, detail)
        traceback.print_exc()
        return False


def load_package_module():
    """Load uq_classification package directly from this directory."""
    init_file = PACKAGE_DIR / "__init__.py"
    spec = importlib.util.spec_from_file_location(
        "uq_classification",
        init_file,
        submodule_search_locations=[str(PACKAGE_DIR)],
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to create import spec for uq_classification package")

    module = importlib.util.module_from_spec(spec)
    sys.modules["uq_classification"] = module
    spec.loader.exec_module(module)
    return module


def test_basic_exports():
    pkg = load_package_module()

    required_exports = [
        "ExperimentTracker",
        "plot_decision_boundary",
        "visualize_checkpoint",
        "visualize_checkpoints_batch",
        "reduce_dimensions",
        "create_meshgrid",
        "load_checkpoint",
    ]
    missing = [name for name in required_exports if not hasattr(pkg, name)]
    if missing:
        raise AssertionError(f"Missing exports: {missing}")


def test_existing_production_exports():
    pkg = load_package_module()

    required_existing = [
        "GROUP_CLEAN",
        "GROUP_ALEATORIC",
        "GROUP_EPISTEMIC",
        "GROUP_NAMES",
        "binary_auroc",
        "macro_f1",
        "confusion_matrix",
    ]
    missing = [name for name in required_existing if not hasattr(pkg, name)]
    if missing:
        raise AssertionError(f"Missing production exports: {missing}")


def test_experiment_tracker_json_mode():
    pkg = load_package_module()

    with TemporaryDirectory() as tmpdir:
        tracker = pkg.ExperimentTracker(
            experiment_name="merge_test",
            mlflow_uri=None,
            json_dir=tmpdir,
        )
        tracker.start_run("lightweight_run")
        tracker.log_param("alpha", 0.1)
        tracker.log_metric("accuracy", 0.95, step=1)
        tracker.log_artifact("dummy_artifact.txt")
        run_id = tracker.run_id
        tracker.end_run()

        run_file = Path(tmpdir) / "merge_test" / f"{run_id}.json"
        if not run_file.exists():
            raise AssertionError(f"Expected run file not found: {run_file}")

        data = json.loads(run_file.read_text())
        assert data["experiment_name"] == "merge_test"
        assert data["params"]["alpha"] == 0.1
        assert data["metrics"]["accuracy"][0]["value"] == 0.95
        assert "dummy_artifact.txt" in data["artifacts"]


class LinearSeparatorModel:
    def predict(self, X):
        X = np.asarray(X)
        return (X[:, 0] + X[:, 1] > 0).astype(int)


def test_decision_boundary_with_synthetic_data():
    pkg = load_package_module()

    rng = np.random.default_rng(42)
    class0 = rng.normal(loc=(-1.0, -1.0), scale=0.3, size=(20, 2))
    class1 = rng.normal(loc=(1.0, 1.0), scale=0.3, size=(20, 2))
    X = np.vstack([class0, class1]).astype(np.float32)
    y = np.array([0] * 20 + [1] * 20, dtype=np.int64)

    xx, yy, grid = pkg.create_meshgrid(X, resolution=25)
    assert xx.shape == (25, 25)
    assert yy.shape == (25, 25)
    assert grid.shape == (625, 2)

    reduced = pkg.reduce_dimensions(X, n_components=2)
    assert reduced.shape == X.shape

    with TemporaryDirectory() as tmpdir:
        save_path = Path(tmpdir) / "boundary.png"
        fig = pkg.plot_decision_boundary(
            LinearSeparatorModel(),
            X,
            y,
            reduce_dims=False,
            resolution=30,
            save_path=save_path,
            title="Merge Test Boundary",
        )
        if fig is None:
            raise AssertionError("plot_decision_boundary returned None")
        if not save_path.exists():
            raise AssertionError(f"Expected visualization not created: {save_path}")


def main() -> int:
    print("=== walaris-cen uq_classification merge test ===")
    print(f"Package directory: {PACKAGE_DIR}")
    print(f"Project root: {PROJECT_ROOT}")

    tests = [
        ("basic imports/new exports", test_basic_exports),
        ("existing production exports", test_existing_production_exports),
        ("ExperimentTracker JSON mode", test_experiment_tracker_json_mode),
        ("decision boundary synthetic integration", test_decision_boundary_with_synthetic_data),
    ]

    passed = 0
    for name, fn in tests:
        if run_test(name, fn):
            passed += 1

    total = len(tests)
    failed = total - passed

    print("\n=== Summary ===")
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {failed}/{total}")

    if failed:
        print("Result: FAIL")
        return 1

    print("Result: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# Made with Bob
