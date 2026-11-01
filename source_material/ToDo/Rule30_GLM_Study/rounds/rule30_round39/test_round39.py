#!/usr/bin/env python3
"""Regression tests for Round 39 (exact; a few seconds)."""

import shutil
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.append(str(HERE.parent / "rule30_round38"))

import glm_hypothesis_core as core  # noqa: E402
import general_benchmarks as gb  # noqa: E402
import hypothesis_engine as he  # noqa: E402
import rule30_engine_r39 as r39  # noqa: E402
from regime_scan import F  # noqa: E402


def test_core_helpers():
    assert core.berlekamp_massey([1, 1, 2, 3, 5, 8, 13, 21]) == [1, 1]
    p, d = core.newton_fit([1, 2, 3, 4, 5], [1, 2, 4, 8, 16])
    assert d == 4 and p(6) == 31
    assert core.solve_exact([[1, 1], [1, -1], [2, 0]], [3, 1, 4]) == [Fraction(2), Fraction(1)]
    # resultant of x - 2 and x - 5 is 2 - 5 = -3 (up to sign convention)
    assert abs(gb.resultant([-2, 1], [-5, 1])) == 3


def test_white_criterion():
    p = he.left_profile(3000, pmax=64)
    for D in range(2, 3000):
        assert p.white[D] == (p.pattern[D - 2] == p.pattern[D - 1])
        assert not (p.white[D] and p.white[D - 1])


def test_F_matches_automaton():
    p = he.left_profile(3000, pmax=64)
    Q = 64
    for D in range(2, 3000):
        if not p.white[D - 1]:
            assert F(p.pattern[D - 2], p.pattern[D - 1], Q) == p.pattern[D]


def test_regime_stats_Q8():
    s = r39.regime_stats(8)
    assert s["on_white_free_cycles"] == 5510
    assert s["odd_terminals"] == 128
    assert (s["antiperiodic_odd"], s["antiperiodic_sources"]) == (16, 16)
    assert s["can_stay_even_forever"] == 60


def test_general_benchmarks():
    res = gb.main(write=False, log=lambda *a: None)
    assert all(r["mined"] and r["honest"] for r in res)
    gcd_row = next(r for r in res if r["name"].startswith("gcd"))
    assert gcd_row["witness"] == 8424432925592889329288197322308900672459420460792433


def test_c_scan_reproduces_53207():
    if shutil.which("gcc") is None:
        return
    exe = HERE / "regime_scan"
    subprocess.run(["gcc", "-O3", "-o", str(exe), str(HERE / "regime_scan.c")], check=True)
    out = subprocess.run([str(exe), "16", "9f60", "ffff", "400", "1000000"], capture_output=True,
                         text=True, check=True).stdout
    assert out.startswith("WHITE 53207 outer_parity 0")


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
