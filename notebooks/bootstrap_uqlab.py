"""Add repo ``src/`` to ``sys.path`` so ``import uqlab`` works from notebooks."""

from __future__ import annotations

import sys
from pathlib import Path


def candidate_repo_roots() -> list[Path]:
    seen: set[Path] = set()
    roots: list[Path] = []
    for base in (Path.cwd(), *Path.cwd().parents):
        for candidate in (
            base,
            base / "uqlab-streamlit",
            base / "four-region-benchmark",
        ):
            resolved = candidate.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            roots.append(resolved)
    return roots


def ensure_uqlab_path() -> Path:
    for base in candidate_repo_roots():
        src = base / "src"
        if (src / "uqlab").is_dir():
            src_s = str(src)
            if src_s not in sys.path:
                sys.path.insert(0, src_s)
            return base
    raise ModuleNotFoundError(
        "Could not find src/uqlab. Open the repo in Jupyter (uqlab-streamlit or notebooks/)."
    )


def find_bootstrap_file() -> Path:
    here = Path(__file__).resolve()
    for candidate in (
        here,
        here.parent / "bootstrap_uqlab.py",
        *(
            base / "notebooks" / "bootstrap_uqlab.py"
            for base in candidate_repo_roots()
        ),
    ):
        if candidate.is_file():
            return candidate
    raise ModuleNotFoundError("bootstrap_uqlab.py not found")


def load_bootstrap_module():
    import importlib.util

    path = find_bootstrap_file()
    spec = importlib.util.spec_from_file_location("bootstrap_uqlab", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load bootstrap from {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
