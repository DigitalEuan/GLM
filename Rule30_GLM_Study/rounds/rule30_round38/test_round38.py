#!/usr/bin/env python3
"""Regression tests for the Round 38 engine (exact; about 20 seconds)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import hypothesis_engine as he  # noqa: E402
import glm_hypothesis_core as core  # noqa: E402


def test_observatory():
    # centre column = OEIS A051023 (first 30 terms)
    assert "".join(map(str, he.centre_column(30))) == "110111001100010110010011101011"
    # right-diagonal least-period exponents (ledger C50 for D <= 8)
    assert he.right_profile(8) == [0, 1, 1, 2, 3, 3, 4, 5, 5]
    # left diagonals: the Lean certificates' numbers
    p = he.left_profile(401, pmax=16)
    assert p.settled_at == 501
    assert [D for D in range(401) if p.white[D]] == [2, 7, 28, 399]
    assert p.lp[400] == 16 and max(p.lp[:400]) == 8
    # general-rule path agrees with the fast rule-30 path
    m = (1 << 100) - 1
    r = s = 1
    for _ in range(80):
        r, s = he.left_step(30, r, m), he.eca_apply(30, s << 2, s << 1, s, m)
        assert r == s


def test_engine():
    eng = he.Engine(quick=False, log=lambda *a: None)
    rep = eng.run()
    H = {h["statement"]: h for h in rep["hypotheses"]}
    st = {h["id"]: h["status"] for h in rep["hypotheses"]}
    assert H["every left diagonal has eventual period dividing 8"]["status"] == "refuted-heldout"
    assert rep["predictions"] == [{"predicted": 87867, "confirmed": True,
                                   "white_diagonals_on_the_way": [53207, 58286, 87866]}]
    laws = [h for h in rep["hypotheses"] if h["origin"] == "mechanism"]
    assert sorted(h["status"] for h in laws) == ["law-holds", "law-holds", "refuted-heldout"]
    # rule 7: nothing in the engine uses floats inside a computation (timing excepted)
    src = Path(he.__file__).read_text()
    assert "import random" not in src and "hash(" not in src and "math." not in src


def test_core():
    c, laws = core.demo(verbose=False)
    assert [l.meta["conj"] for l in laws] == [("white(k-1)",), ("white(k-1)", "odd(k-2)")]


if __name__ == "__main__":
    test_observatory()
    test_core()
    test_engine()
    print("all Round 38 tests pass")
