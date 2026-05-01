"""Pytest configuration: prepend src/ to sys.path so 'import cents_generator' works."""
import sys
from pathlib import Path

SRC = Path(__file__).parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
