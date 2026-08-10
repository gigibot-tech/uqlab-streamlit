#!/usr/bin/env python3
"""Regenerate uqlab shims with full re-exports (including private names)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UQLAB = ROOT / "src" / "uqlab"
CORE = ROOT / "src" / "uqlab_core"


def module_name(rel: Path) -> str:
    parts = rel.with_suffix("").parts
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return "uqlab_core." + ".".join(parts)


def make_shim(rel: Path) -> str:
    mod = module_name(rel)
    return f'''"""Compatibility shim — implementation moved to uqlab_core."""
import importlib as _importlib

_m = _importlib.import_module("{mod}")
globals().update({{n: getattr(_m, n) for n in dir(_m) if not n.startswith("__")}})


def __getattr__(name: str):
    return getattr(_m, name)
'''


def main() -> None:
    for core_path in sorted(CORE.rglob("*.py")):
        rel = core_path.relative_to(CORE)
        shim_path = UQLAB / rel
        if not shim_path.is_file():
            continue
        first = shim_path.read_text(encoding="utf-8").splitlines()[:1]
        if not first or "Compatibility shim" not in first[0]:
            continue
        shim_path.write_text(make_shim(rel), encoding="utf-8")
    print("Regenerated shims")


if __name__ == "__main__":
    main()
