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


# ----------------------------------------------------------------------------
# Phase 2: cents-mode determinism (D-07.5).
# The cents sweep dedups via dict.setdefault (Pitfall 15) — the determinism
# tests below exercise the full dedup path under PYTHONHASHSEED randomization
# via subprocess invocation, catching any subtle non-determinism the
# in-process test might miss.
# ----------------------------------------------------------------------------
def test_two_runs_in_process_are_byte_identical_cents_mode(tmp_path: pathlib.Path) -> None:
    """Cents-mode two-run determinism (extends GEN-02 to the production scale)."""
    path_a = tmp_path / "a.doricolib"
    path_b = tmp_path / "b.doricolib"
    run(path_a, mode="cents")
    run(path_b, mode="cents")
    a = path_a.read_bytes()
    b = path_b.read_bytes()
    assert a == b, (
        f"two consecutive in-process cents-mode runs produced different output: "
        f"len(a)={len(a)}, len(b)={len(b)}"
    )


def test_two_subprocess_runs_via_cli_are_byte_identical_cents_mode(tmp_path: pathlib.Path) -> None:
    """Spawn 'python build.py --mode cents --out <path>' twice and diff bytes.

    Under PYTHONHASHSEED randomization, dict-iteration order can vary across
    processes — the dict.setdefault dedup pattern (Pitfall 15) must produce
    the same first-insertion ordering regardless of hash seed."""
    repo_root = pathlib.Path(__file__).parent.parent
    build_py = repo_root / "build.py"

    path_a = tmp_path / "a.doricolib"
    path_b = tmp_path / "b.doricolib"

    for path in (path_a, path_b):
        result = subprocess.run(
            [sys.executable, str(build_py), "--mode", "cents", "--out", str(path)],
            capture_output=True,
            cwd=str(repo_root),
        )
        assert result.returncode == 0, (
            f"build.py failed with code {result.returncode}: "
            f"stderr={result.stderr.decode()}"
        )

    assert path_a.read_bytes() == path_b.read_bytes(), \
        "two consecutive cents-mode subprocess runs produced different output"


def test_diff_command_returns_empty_cents_mode(tmp_path: pathlib.Path) -> None:
    """STACK.md verification recipe applied to cents mode."""
    path_a = tmp_path / "a.doricolib"
    path_b = tmp_path / "b.doricolib"
    run(path_a, mode="cents")
    run(path_b, mode="cents")
    result = subprocess.run(
        ["diff", str(path_a), str(path_b)],
        capture_output=True,
    )
    assert result.returncode == 0, f"diff found differences: {result.stdout.decode()}"
    assert result.stdout == b"", \
        f"diff stdout non-empty (should be silent): {result.stdout!r}"
