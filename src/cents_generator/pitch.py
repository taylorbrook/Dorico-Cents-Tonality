"""Centralized pitch-delta math for the cents Dorico tonality system.

Pitfall 1 (off-by-100 trap) defense: pitch_delta_numerator(base, cents) is
the ONLY place pitch math lives in cents mode. For 'Sharp +14' the correct
delta is (100 + 14)/1200 = 114/1200, NOT 14/1200. Inline calculation at
each call site invites silent off-by-100 bugs; routing every Class B/C
accidental through this single helper makes the trap impossible to
introduce in user code. See PITFALLS.md §"Pitfall 1" and CONTEXT.md D-06.

Template mode (Phase 1's build_template_three()) preserves the literal
pitch-delta strings ("0/24", "-14/1200", "69/1200") and does NOT call this
helper — that's intentional template fidelity.
"""
from __future__ import annotations

from typing import Literal

# ============================================================================
# _BASE_OFFSET_CENTS — PINNED. NEVER ALTER WITHOUT COORDINATED MATH REVIEW.
# ----------------------------------------------------------------------------
# The natural-pitch reference frame for Western 12-EDO tonality:
#   natural -> 0¢   (the reference itself)
#   sharp   -> +100¢ (one chromatic semitone above natural)
#   flat    -> -100¢ (one chromatic semitone below natural)
# Adding the user-supplied signed cents deviation to this base offset is the
# entire formula. Altering any value here silently re-pitches every existing
# accidental — there is no clean migration path. If a future tuning system
# requires different base offsets, ship a parallel helper for that system;
# do NOT mutate this one.
# ============================================================================
_BASE_OFFSET_CENTS: dict[str, int] = {
    "natural": 0,
    "sharp": 100,
    "flat": -100,
}


def pitch_delta_numerator(
    base: Literal["natural", "sharp", "flat"],
    cents: int,
) -> int:
    """Return the numerator of pitchDeltaFromNatural for (base, cents).

    Defeats Pitfall 1 (off-by-100 trap): for 'Sharp +14', the correct delta
    is (100 + 14)/1200 = 114/1200, NOT 14/1200. Callers format as
    f"{n}/1200"; this helper returns only the integer numerator.

    Args:
        base:  one of "natural", "sharp", "flat".
        cents: signed cent deviation, e.g. -99..+99 in v1.

    Returns:
        Integer numerator. e.g. ('sharp', 14) -> 114; ('flat', -7) -> -107;
        ('natural', 0) -> 0.

    Raises:
        KeyError: if `base` is not one of the three supported strings.
    """
    return _BASE_OFFSET_CENTS[base] + cents
