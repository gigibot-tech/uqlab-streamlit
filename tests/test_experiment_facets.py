"""Facet catalogs project from SSOTs (four regions ↔ preference sets)."""

from __future__ import annotations

from uqlab.data.class_regions import ALL_REGIONS
from uqlab.data.text_registry import PREFERENCE_SET_NAMES
from uqlab.shared.experiment_ports import class_region_facets, preference_set_facets


def test_preference_set_facets_match_ssot() -> None:
    facets = preference_set_facets()
    assert [f.id for f in facets] == list(PREFERENCE_SET_NAMES)
    assert all(f.kind == "preference_set" for f in facets)
    assert len(facets) == 4


def test_class_region_facets_match_ssot() -> None:
    facets = class_region_facets()
    assert [f.id for f in facets] == list(ALL_REGIONS)
    assert all(f.kind == "class_region" for f in facets)
    assert len(facets) == 4
