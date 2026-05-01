"""CLI entrypoint for the cents Dorico tonality-system generator.

Usage:
    python build.py --out cents.doricolib

Re-running with the same --out should produce a byte-identical file
(deterministic UUIDs via uuid5 + locked PROJECT_NAMESPACE).
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure src/ is on the import path when invoking 'python build.py' directly.
_SRC = Path(__file__).parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from cents_generator.main import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
