#!/usr/bin/env bash
# Resolve a Python interpreter for backend start scripts (sourced, not executed).
set -euo pipefail

_BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_ROOT="$(cd "${_BACKEND_DIR}/.." && pwd)"
_OLD_PILOTS_ROOT="$(cd "${_ROOT}/.." && pwd)"

export PYTHONPATH="${_ROOT}/src:${_BACKEND_DIR}${PYTHONPATH:+:${PYTHONPATH}}"

if [ -n "${PYTHON:-}" ] && command -v "${PYTHON}" >/dev/null 2>&1; then
  :
elif [ -x "${OLD_PILOTS_VENV_PYTHON:-}" ]; then
  PYTHON="${OLD_PILOTS_VENV_PYTHON}"
elif [ -x "${_OLD_PILOTS_ROOT}/.venv/bin/python" ]; then
  PYTHON="${_OLD_PILOTS_ROOT}/.venv/bin/python"
elif [ -x "${_ROOT}/.test-venv/bin/python" ]; then
  PYTHON="${_ROOT}/.test-venv/bin/python"
elif [ -x "${_BACKEND_DIR}/.venv/bin/python" ]; then
  PYTHON="${_BACKEND_DIR}/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON="python"
else
  echo "ERROR: No python interpreter found. Activate a venv or set PYTHON=..." >&2
  exit 1
fi
