"""Two-run byte-identical determinism test (GEN-02).

Re-running the generator twice must produce byte-identical files. This
is the foundation of update-in-place re-imports — see PITFALLS Pitfall 2.
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

from cents_generator.main import run


def test_two_runs_in_process_are_byte_identical(tmp_path: pathlib.Path) -> None:
    path_a = tmp_path / "a.doricolib"
    path_b = tmp_path / "b.doricolib"
    run(path_a, mode="template")
    run(path_b, mode="template")
    a = path_a.read_bytes()
    b = path_b.read_bytes()
    assert a == b, (
        f"two consecutive in-process runs produced different output: "
        f"len(a)={len(a)}, len(b)={len(b)}"
    )


def test_two_subprocess_runs_via_cli_are_byte_identical(tmp_path: pathlib.Path) -> None:
    """Spawn 'python build.py --out <path>' twice and diff the bytes.

    This exercises the full CLI path including module import and argparse —
    catches any subtle non-determinism that the in-process test might miss
    (e.g. dict ordering driven by PYTHONHASHSEED randomization)."""
    repo_root = pathlib.Path(__file__).parent.parent
    build_py = repo_root / "build.py"

    path_a = tmp_path / "a.doricolib"
    path_b = tmp_path / "b.doricolib"

    for path in (path_a, path_b):
        result = subprocess.run(
            [sys.executable, str(build_py), "--mode", "template", "--out", str(path)],
            capture_output=True,
            cwd=str(repo_root),
        )
        assert result.returncode == 0, (
            f"build.py failed with code {result.returncode}: "
            f"stderr={result.stderr.decode()}"
        )

    assert path_a.read_bytes() == path_b.read_bytes(), \
        "two consecutive subprocess runs produced different output"


def test_diff_command_returns_empty(tmp_path: pathlib.Path) -> None:
    """Match STACK.md's verification recipe literally: `diff a b` is empty."""
    path_a = tmp_path / "a.doricolib"
    path_b = tmp_path / "b.doricolib"
    run(path_a, mode="template")
    run(path_b, mode="template")
    result = subprocess.run(
        ["diff", str(path_a), str(path_b)],
        capture_output=True,
    )
    assert result.returncode == 0, f"diff found differences: {result.stdout.decode()}"
    assert result.stdout == b"", \
        f"diff stdout non-empty (should be silent): {result.stdout!r}"
