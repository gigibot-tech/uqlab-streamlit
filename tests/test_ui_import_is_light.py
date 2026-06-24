"""Guard tests: workflow UI must stay torch-free and use orchestrator facades."""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
WORKFLOW_DIR = SRC_DIR / "uqlab" / "ui_components" / "workflow"

ALLOWED_UQLAB_PREFIXES = (
    "uqlab.ui_components",
    "uqlab.runtime_paths",
)

# Progressive step surface (imported from workflow/__init__.py).
WORKFLOW_STEP_MODULES = (
    "__init__.py",
    "session.py",
    "step1_dataset.py",
    "step2_training.py",
    "step2_5_checkpoint_arsenal.py",
    "step3_uncertainty.py",
    "step3_per_class_table.py",
    "step4_evaluation.py",
    "step5_review.py",
)


def _uqlab_import_violations(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                if name.startswith("uqlab.") and not name.startswith(ALLOWED_UQLAB_PREFIXES):
                    violations.append(f"{path.name}:{node.lineno} imports {name}")
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("uqlab."):
                if not node.module.startswith(ALLOWED_UQLAB_PREFIXES):
                    violations.append(f"{path.name}:{node.lineno} imports from {node.module}")
    return violations


def test_workflow_import_does_not_load_torch() -> None:
    env = {**os.environ, "PYTHONPATH": str(SRC_DIR)}
    code = (
        "import uqlab.ui_components.workflow as w; "
        "import sys; "
        "assert 'torch' not in sys.modules"
    )
    subprocess.run([sys.executable, "-c", code], check=True, env=env)


def test_workflow_modules_avoid_direct_uqlab_imports() -> None:
    violations: list[str] = []
    for name in WORKFLOW_STEP_MODULES:
        violations.extend(_uqlab_import_violations(WORKFLOW_DIR / name))
    assert not violations, "Direct uqlab.* imports in workflow:\n" + "\n".join(violations)
