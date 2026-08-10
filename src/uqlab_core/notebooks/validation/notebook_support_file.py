"""Compatibility shim that forwards imports to the real notebook_support package.

This file exists beside the notebook_support/ package directory. When Python resolves
`import notebook_support` from the validation notebook directory, this module may be
loaded before the package directory. To avoid breaking imports such as
`from notebook_support.constants import ...`, this shim loads the package's
`__init__.py`, marks itself as a package, and re-exports the package namespace.
"""

from __future__ import annotations

from pathlib import Path

_PACKAGE_DIR = Path(__file__).with_suffix("")
_PACKAGE_INIT = _PACKAGE_DIR / "__init__.py"

if not _PACKAGE_DIR.is_dir() or not _PACKAGE_INIT.exists():
    raise ImportError(f"Expected notebook_support package at {_PACKAGE_DIR}")

__file__ = str(_PACKAGE_INIT)
__path__ = [str(_PACKAGE_DIR)]
__package__ = "notebook_support"

with open(_PACKAGE_INIT, "r", encoding="utf-8") as _f:
    _code = compile(_f.read(), str(_PACKAGE_INIT), "exec")
    exec(_code, globals(), globals())
