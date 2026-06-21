#!/usr/bin/env bash
# Pipeline unit tests (campaign PDF, sweep plot, timeline).
# PYTEST_DISABLE_PLUGIN_AUTOLOAD avoids broken hydra/omegaconf pytest plugin in some venvs.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="${ROOT}/src${PYTHONPATH:+:$PYTHONPATH}"
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
exec python3 -m pytest \
  tests/test_campaign_report.py \
  tests/test_campaign_config_timeline.py \
  tests/test_sweep_line_plot.py \
  "$@"
