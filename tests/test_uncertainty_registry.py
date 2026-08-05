"""Tests for modular uncertainty perspective registry and mirroring."""

from __future__ import annotations

from uqlab_core.shared.perspectives import (
    mirror_perspectives,
    perspective_by_sweep_target,
    perspective_count,
)


def test_registry_has_two_perspectives():
    assert perspective_count() == 2


def test_mirror_perspectives_excludes_primary():
    primary = perspective_by_sweep_target("label_noise")
    assert primary is not None
    mirrors = mirror_perspectives(primary)
    assert len(mirrors) == perspective_count() - 1
    assert all(m.id != primary.id for m in mirrors)


def test_mirror_perspectives_single_includes_all():
    mirrors = mirror_perspectives(None)
    assert len(mirrors) == perspective_count()
