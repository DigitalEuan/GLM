#!/usr/bin/env python3
"""Round 42 checks (standard library only).  Run: python3 test_round42.py  (about 45 s)."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import glm_guards  # noqa: E402
from glm_guards import coincidence_test, exclusivity_guard, identity_guard  # noqa: E402


def test_guards_selftest():
    glm_guards._selftest()


def test_tax_closed_form_and_criterion():
    def defect(a, b, c):
        return a * a + b * b - 2 * c * c - (a + b - 2 * c) ** 2
    box = [(a, b, c) for a in range(20) for b in range(20) for c in range(min(a, b) + 1)]
    assert identity_guard("closed", lambda a, b, c: defect(a, b, c) ==
                          -2 * (3 * c * c - 2 * c * (a + b) + a * b), lambda *x: True, box).ok
    r = identity_guard("v13", lambda a, b, c: c in (0, a, b),
                       lambda a, b, c: defect(a, b, c) == 0, box)
    assert not r.ok
    assert defect(1, 1, 0) == -2 and defect(5, 8, 2) == 0 and defect(3, 3, 1) == 0


def test_coincidence_exact():
    r = coincidence_test(10, 5, 2, 2)              # C(5,2)/C(10,2) = 10/45
    assert r.data["p_upper"] == Fraction(2, 9)
    total = sum(glm_guards.hypergeom_pmf(30, 7, 5, x) for x in range(6))
    assert total == 1


def test_exclusivity():
    assert exclusivity_guard("x", [1, 2], [1, 2, 3]).ok
    assert not exclusivity_guard("x", [1, 4], [1, 2, 3]).ok


def test_make_v14_reproducible():
    spec = importlib.util.spec_from_file_location("make_v14", HERE / "make_v14.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    s = m.build()
    assert "GLM Hypothesis Engine v14" in s
    assert "is NECESSARY (v12" not in s


def test_v14_quick_run():
    out = subprocess.run([sys.executable, "hypothesis_engine_v14.py", "--quick"], cwd=HERE,
                         capture_output=True, text=True, timeout=600).stdout
    rep = json.loads((HERE / "r42_engine_report_v14_quick.json").read_text())
    g = {(x["guard"], x["ok"]) for x in rep["guards"]}
    assert ("consistency", True) in g                  # no refuted claim asserted by v14
    assert ("exclusivity", False) in g                 # 'only at the white diagonals' refuted
    assert ("explained-away", False) in g              # 'positive finding' explained
    assert "NEW TO THE LEDGER — every period-doubling" not in out


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"ok  {t.__name__}")
    print(f"all {len(tests)} Round 42 checks passed")
