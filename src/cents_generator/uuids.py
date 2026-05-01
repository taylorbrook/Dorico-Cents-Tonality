"""Deterministic entityID derivation for the cents Dorico tonality system.

Every entityID emitted into cents.doricolib is derived from a single pinned
project namespace UUID via uuid5 (RFC 9562 SHA-1 namespace hashing). Same
(kind, key) pair → same UUID forever → re-imports into Dorico match by
entityID and update existing entries instead of duplicating.
"""
from __future__ import annotations

import uuid

# ============================================================================
# PROJECT_NAMESPACE — PINNED ONCE. NEVER ROTATE.
# ----------------------------------------------------------------------------
# Rotating this UUID would break update-in-place semantics for every existing
# user: their previously-imported library would gain a duplicate copy of every
# entity (~1411 of them) on the next re-import. There is no clean migration
# path. If a future major version requires a "rename", document it as a
# one-time manual cleanup in the README — do NOT rotate this constant.
#
# This UUID was generated once with a random-UUID call (uuid v4) at project
# inception and is now the project's seed identity for all entityID derivation.
# ============================================================================
PROJECT_NAMESPACE: uuid.UUID = uuid.UUID("6b8f2c7a-1e4d-4a3f-9c5b-8d6e1f2a3b4c")


def entity_id(kind: str, key: str) -> str:
    """Return the prefixed entityID string for a (kind, key) pair.

    Format: '<kind>.user.<32 lowercase hex>'  (Dorico's canonical entityID shape)

    Args:
        kind: One of {'temperament-definition', 'accidental-system',
              'accidental', 'tonalitysystem', 'text', 'glyph', 'comp'}.
        key:  A stable human-readable key. LOCK THESE FOREVER once shipped:
              - accidental: '<base><signed-cents>' lowercase, e.g.
                'sharp+14', 'flat-50', 'natural-7'; zero-deviation:
                'sharp', 'flat', 'natural'.
              - composite: same as accidental key.
              - glyph: SMuFL glyph name verbatim ('accidentalSharp').
              - text: the literal label ('+14', '-50', '-14').
              - singletons: '12-edo' (temperament), 'cents' (accidental
                system AND tonality system — keys live in different
                namespaces because the kind prefix differs).

    Returns:
        A string like 'glyph.user.bf2fcca40371420f99106bd86bf99ab8'.
    """
    u = uuid.uuid5(PROJECT_NAMESPACE, f"{kind}:{key}")
    return f"{kind}.user.{u.hex}"
