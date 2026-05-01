"""Determinism + format tests for entity_id() and PROJECT_NAMESPACE."""
from __future__ import annotations

import re
import uuid

from cents_generator.uuids import PROJECT_NAMESPACE, entity_id

ENTITY_ID_PATTERN = re.compile(r"^[a-z-]+\.user\.[0-9a-f]{32}$")


def test_project_namespace_is_uuid_instance() -> None:
    assert isinstance(PROJECT_NAMESPACE, uuid.UUID)


def test_project_namespace_is_pinned() -> None:
    # If this fails, someone rotated the namespace. DO NOT update this assertion
    # to make the test pass — restore the original UUID instead. Rotation breaks
    # update-in-place semantics for every existing user.
    assert str(PROJECT_NAMESPACE) == "6b8f2c7a-1e4d-4a3f-9c5b-8d6e1f2a3b4c"


def test_entity_id_format_matches_dorico_pattern() -> None:
    eid = entity_id("accidental", "sharp+14")
    assert ENTITY_ID_PATTERN.match(eid), f"bad format: {eid!r}"


def test_entity_id_is_deterministic_across_calls() -> None:
    a = entity_id("accidental", "sharp+14")
    b = entity_id("accidental", "sharp+14")
    assert a == b


def test_entity_id_differs_by_key() -> None:
    a = entity_id("accidental", "sharp+14")
    b = entity_id("accidental", "sharp+15")
    assert a != b


def test_entity_id_differs_by_kind() -> None:
    # Same key, different kind → different UUID (kind is part of the hash input).
    a = entity_id("accidental", "sharp")
    b = entity_id("comp", "sharp")
    assert a != b
    assert a.startswith("accidental.user.")
    assert b.startswith("comp.user.")


def test_entity_id_handles_all_kinds() -> None:
    # Smoke test that all 7 kinds produce well-formed IDs.
    for kind in (
        "temperament-definition",
        "accidental-system",
        "accidental",
        "tonalitysystem",
        "text",
        "glyph",
        "comp",
    ):
        eid = entity_id(kind, "x")
        assert ENTITY_ID_PATTERN.match(eid), f"{kind}: {eid!r}"


def test_entity_id_no_hyphens_in_hex() -> None:
    # uuid5().hex strips dashes; verify ours has none after the prefix.
    eid = entity_id("accidental", "sharp+14")
    hex_part = eid.split(".user.")[1]
    assert "-" not in hex_part
    assert len(hex_part) == 32
    assert all(c in "0123456789abcdef" for c in hex_part)


def test_entity_id_hex_is_lowercase() -> None:
    # Dorico's template uses lowercase hex (e.g. 28c8da0eebd8441f8e626e070b6bfd45).
    eid = entity_id("accidental", "sharp+14")
    hex_part = eid.split(".user.")[1]
    assert hex_part == hex_part.lower()


def test_entity_id_known_pinned_value() -> None:
    # Pin one known (kind, key) → expected hex pair. If this fails, either
    # PROJECT_NAMESPACE was rotated (BUG) or the entity_id derivation changed.
    # Computed once via uuid.uuid5(PROJECT_NAMESPACE, "accidental:sharp+14").hex
    # under the pinned namespace 6b8f2c7a-1e4d-4a3f-9c5b-8d6e1f2a3b4c.
    expected_hex = uuid.uuid5(
        uuid.UUID("6b8f2c7a-1e4d-4a3f-9c5b-8d6e1f2a3b4c"),
        "accidental:sharp+14",
    ).hex
    assert entity_id("accidental", "sharp+14") == f"accidental.user.{expected_hex}"
