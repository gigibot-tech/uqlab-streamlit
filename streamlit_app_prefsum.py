"""PrefSum — open a DPO checkpoint and the preference file it trained on.

Separate from the classification wizard (``streamlit_app_progressive.py``).
"""

from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent
_SRC = _PROJECT_ROOT / "src"
for _path in (_SRC, _PROJECT_ROOT):
    _entry = str(_path)
    if _entry not in sys.path:
        sys.path.insert(0, _entry)

import streamlit as st

from uqlab.ui_components.workflow.summarization_runs import render_summarization_runs

st.set_page_config(
    page_title="PrefSum",
    page_icon="📰",
    layout="wide",
)


def main() -> None:
    render_summarization_runs()


if __name__ == "__main__":
    main()
