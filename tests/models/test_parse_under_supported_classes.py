"""Tests for under-supported class parsing (random:N and explicit lists)."""

from uqlab.shared.config.classification import parse_under_supported_classes


def test_random_spec_is_deterministic():
    a = parse_under_supported_classes("random:2", seed=42)
    b = parse_under_supported_classes("random:2", seed=42)
    assert a == b
    assert len(a) == 2
    assert all(0 <= c <= 9 for c in a)


def test_explicit_list():
    assert parse_under_supported_classes("3,5") == [3, 5]


def test_list_input():
    assert parse_under_supported_classes([1, 2]) == [1, 2]
