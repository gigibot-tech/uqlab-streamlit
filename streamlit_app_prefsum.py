"""PrefSum Streamlit entry — composition root only.

Domain: ``annotated_pair_data`` + ``annotated_news_eval`` + ``annotated_news_training``.
UI: ``uqlab.ui_components.workflow.prefsum`` (Facets + ExperimentPorts).
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

from uqlab.summarization import annotated_pair_data as prefsum_data
from uqlab.summarization import annotated_news_eval as prefsum_eval
from uqlab.summarization import annotated_news_training as prefsum_training
from uqlab.summarization.annotated_news_paths import annotated_news_root
from uqlab.ui_components.workflow.prefsum import PrefSumContracts, PrefSumPage

st.set_page_config(
    page_title="PrefSum",
    page_icon="📰",
    layout="wide",
)


def build_contracts() -> PrefSumContracts:
    """Wire news root + Data / Training / Eval ports into PrefSumContracts.

    Data and eval are separate modules (same surface the Protocols require).
    """
    root = annotated_news_root()
    return PrefSumContracts.create(
        root=root,
        data=prefsum_data,
        training=prefsum_training,
        evaluation=prefsum_eval,
    )


def main() -> None:
    try:
        contracts = build_contracts()
    except FileNotFoundError as exc:
        st.error(str(exc))
        return
    PrefSumPage(contracts=contracts).render()


if __name__ == "__main__":
    main()
