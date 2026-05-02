"""Unit tests for pitch_delta_numerator (D-06, Pitfall 1: the off-by-100 trap).

Hand-calculated cases pin the math against the natural-pitch reference frame.
For 'Sharp +14', the correct delta is (100 + 14)/1200 = 114/1200 — NOT 14/1200.
For 'Flat -7', the correct delta is (-100 + -7)/1200 = -107/1200.
Re-deriving these by hand on every test prevents the regression mode where
'I refactored the helper and the tests still pass because they share a bug'.

No pytest.parametrize — explicit one-assertion-per-test functions so failure
messages name the offending case unambiguously (mirrors tests/test_uuids.py).
"""
from __future__ import annotations

from cents_generator.pitch import pitch_delta_numerator


# ---- D-06 hand-calculated cases (Pitfall 1 defense) ------------------------

def test_pitch_delta_sharp_14_is_114() -> None:
    """('sharp', 14) -> 114. The off-by-100 trap diagnostic."""
    assert pitch_delta_numerator("sharp", 14) == 114


def test_pitch_delta_sharp_minus_50_is_50() -> None:
    """('sharp', -50) -> 50 (NOT -50, which would be Flat +50). Pitfall 1."""
    assert pitch_delta_numerator("sharp", -50) == 50


def test_pitch_delta_flat_minus_7_is_minus_107() -> None:
    """('flat', -7) -> -107. The flat-side off-by-100 mirror case."""
    assert pitch_delta_numerator("flat", -7) == -107


def test_pitch_delta_flat_50_is_minus_50() -> None:
    """('flat', 50) -> -50. Flat-side enharmonic with positive cents."""
    assert pitch_delta_numerator("flat", 50) == -50


def test_pitch_delta_natural_minus_7_is_minus_7() -> None:
    """('natural', -7) -> -7. Natural-base passes cents through unchanged."""
    assert pitch_delta_numerator("natural", -7) == -7


# ---- Zero-deviation cases --------------------------------------------------

def test_pitch_delta_zero_dev_sharp_is_100() -> None:
    assert pitch_delta_numerator("sharp", 0) == 100


def test_pitch_delta_zero_dev_flat_is_minus_100() -> None:
    assert pitch_delta_numerator("flat", 0) == -100


def test_pitch_delta_zero_dev_natural_is_0() -> None:
    assert pitch_delta_numerator("natural", 0) == 0


# ---- Boundary cases (±99 sweep edges) --------------------------------------

def test_pitch_delta_boundary_sharp_99_is_199() -> None:
    assert pitch_delta_numerator("sharp", 99) == 199


def test_pitch_delta_boundary_flat_minus_99_is_minus_199() -> None:
    assert pitch_delta_numerator("flat", -99) == -199


def test_pitch_delta_boundary_natural_99_is_99() -> None:
    assert pitch_delta_numerator("natural", 99) == 99


# ---- Enharmonic invariant (Pitfall 10) -------------------------------------

def test_enharmonic_pair_sharp_minus_50_equals_natural_50() -> None:
    """Sharp -50 and Natural +50 are the same pitch (50¢ above natural)."""
    assert (
        pitch_delta_numerator("sharp", -50)
        == pitch_delta_numerator("natural", 50)
        == 50
    )
