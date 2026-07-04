#!/usr/bin/env python3
"""One-shot migration: copy core modules to uqlab_core, rewrite imports, leave shims in uqlab."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
UQLAB = SRC / "uqlab"
CORE = SRC / "uqlab_core"

# Entire subtrees (relative to uqlab/)
CORE_TREES = [
    "data",
    "models",
]

# Individual files (relative to uqlab/)
CORE_FILES = [
    "runtime_paths.py",
    "run_artifacts.py",
    "results_io.py",
    "shared/types.py",
    "shared/__init__.py",
    "shared/config/classification.py",
    "shared/config/signals.py",
    "shared/config/__init__.py",
    "shared/utils/classification.py",
    "shared/utils/core.py",
    "shared/utils/tracking.py",
    "shared/utils/__init__.py",
    "runner/__init__.py",
    "runner/execute.py",
    "runner/experiment_core.py",
    "runner/train_eval.py",
    "runner/notebook_run.py",
    "runner/patterns.py",
    "runner/console_log.py",
    "runner/experiment_log.py",
    "runner/phases/__init__.py",
    "runner/phases/config_view.py",
    "runner/phases/eval.py",
    "runner/phases/eval_signal_config.py",
    "evaluation/pipeline.py",
    "evaluation/__init__.py",
    "evaluation/signals",
    "evaluation/metrics",
    "evaluation/reporting/result_writers.py",
    "evaluation/reporting/run_summary.py",
    "evaluation/reporting/four_region_reporting.py",
]

SKIP_SHIM = set()  # paths that get custom handling


def collect_core_paths() -> list[Path]:
    paths: list[Path] = []
    for tree in CORE_TREES:
        base = UQLAB / tree
        if base.is_dir():
            paths.extend(sorted(p for p in base.rglob("*.py") if p.is_file()))
    for rel in CORE_FILES:
        p = UQLAB / rel
        if p.is_file():
            if p not in paths:
                paths.append(p)
        elif p.is_dir():
            paths.extend(sorted(p.rglob("*.py")))
    return sorted(set(paths))


def rewrite_imports(text: str) -> str:
    # uqlab.xxx -> uqlab_core.xxx (but not uqlab_core or uqlab_orchestrator)
    text = re.sub(r"\buqlab_orchestrator\b", "__UQLAB_ORCH__", text)
    text = re.sub(r"\buqlab_core\b", "__UQLAB_CORE__", text)
    text = re.sub(r"\buqlab\b", "uqlab_core", text)
    text = re.sub(r"__UQLAB_ORCH__", "uqlab_orchestrator", text)
    text = re.sub(r"__UQLAB_CORE__", "uqlab_core", text)
    return text


def rel_to_core(uqlab_path: Path) -> Path:
    rel = uqlab_path.relative_to(UQLAB)
    return CORE / rel


def make_shim(rel: Path) -> str:
    mod = f"uqlab_core.{rel.with_suffix('').as_posix().replace('/', '.')}"
    if rel.name == "__init__.py":
        pkg = mod[:-9] if mod.endswith(".__init__") else mod
        mod = pkg
    return f'''"""Compatibility shim — implementation moved to uqlab_core."""
from {mod} import *  # noqa: F401,F403
'''


def main() -> None:
    if CORE.exists():
        shutil.rmtree(CORE)
    CORE.mkdir(parents=True)

    core_paths = collect_core_paths()
    print(f"Moving {len(core_paths)} files to uqlab_core")

    for src_path in core_paths:
        dst_path = rel_to_core(src_path)
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        text = src_path.read_text(encoding="utf-8")
        dst_path.write_text(rewrite_imports(text), encoding="utf-8")

    # Copy non-py assets under data/models (README etc.)
    for tree in CORE_TREES:
        for asset in (UQLAB / tree).rglob("*"):
            if asset.is_file() and asset.suffix not in {".py", ".pyc"}:
                rel = asset.relative_to(UQLAB)
                out = CORE / rel
                out.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(asset, out)

    # Shims in uqlab
    for src_path in core_paths:
        rel = src_path.relative_to(UQLAB)
        if str(rel) in SKIP_SHIM:
            continue
        src_path.write_text(make_shim(rel), encoding="utf-8")

    print("Done. Core at", CORE)


if __name__ == "__main__":
    main()
