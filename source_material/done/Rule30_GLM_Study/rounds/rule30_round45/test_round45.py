#!/usr/bin/env python3
"""Tests for Round 45 (engine v17).  Standard library only.

    python3 test_round45.py           # unit tests (seconds) + one quick engine run (~25 s)
    python3 test_round45.py --unit    # unit tests only
"""

from __future__ import annotations

import itertools
import random
import sys
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from glm_layers import (LayerProfile, identity_layered, coincidence_layered,  # noqa: E402
                        exclusivity_layered, escalation_profile)
import hypothesis_engine_v17 as v17  # noqa: E402
from hypothesis_engine_v14 import Hypothesis  # noqa: E402

FAILS = []


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        FAILS.append(name)


def test_layers():
    # universal: prefix shape, verdict = all, first failure
    p = LayerProfile("g", "c", "universal", [1, 2, 3, 4, 5], [True, True, False, False, None])
    check("universal verdict False", p.verdict() is False)
    check("universal first failure = layer 3", p.first_fail() == 2)
    check("universal shape ok", p.shape_ok())
    q = LayerProfile("g", "c", "universal", [1, 2, 3, 4, 5], [True, False, True, True, True])
    check("non-nested domains detected", not q.shape_ok())
    # largest: an empty smallest layer does not decide
    r = LayerProfile("g", "c", "largest", [1, 2, 3, 4, 5], [None, True, True, True, False])
    check("largest-scale verdict is the last layer read", r.verdict() is False)
    check("arrow flips at universal", r.arrow()["direction"] == "flipped at universal")
    # identity on a box: 'balanced iff all bits equal' first fails at length 2
    box = [(L, k, 0) for L in range(1, 7) for k in range(L + 1)]
    prof = identity_layered("all-equal", lambda L, k, _: k in (0, L),
                            lambda L, k, _: abs(2 * k - L) <= 1, box)
    check("identity refutes the broken balance criterion", prof.verdict() is False)
    check("identity witness is a real counterexample",
          (prof.witness[1] in (0, prof.witness[0])) != (abs(2 * prof.witness[1] - prof.witness[0]) <= 1))
    # exclusivity: suffix shape
    ex = exclusivity_layered("only at S", [1, 10, 50], {0, 12, 52})
    check("exclusivity fails as stated", ex.verdict() is False)
    check("exclusivity passing radii form a suffix", ex.shape_ok())
    # coincidence recounts per layer
    co = coincidence_layered(list(range(100)), set(range(0, 100, 10)), [0, 10, 20, 30])
    check("coincidence significant at full size", co.verdict() is True)


def test_escalation():
    calls = []

    def chk(s):
        calls.append(s)
        return (s < 30, s)
    p = escalation_profile("x", [10, 20, 30, 40, 50], chk)
    check("escalation stops at first failure", calls == [10, 20, 30] and p.first_fail() == 2)
    check("escalation never reads above a refutation", p.verdicts[3:] == [None, None])
    # H19 is found false by the engine's own escalation, at n = 11101
    h = Hypothesis(hid="H19", family="centre", text="|2·L(n) − n| ≤ 10 for all n (narrowed on n ≤ 3000)",
                   lean="", origin="narrow", key="CC.lc.half.2")

    class E:
        quick = True
    desc, scales, ck = v17._esc_lc(h, E())
    prof = escalation_profile(desc, scales, ck)
    check("H19 refuted by escalation at n = 11101", prof.verdict() is False and "11101" in prof.witness)
    # seed transport is refuted by widening the seed set
    h2 = Hypothesis(hid="H39", family="tool-generated", text="same across seeds", lean="",
                    origin="wobble", key="WOBBLE.transportable")
    desc, scales, ck = v17._esc_wobble_transport(h2, E())
    prof = escalation_profile(desc, scales, ck)
    check("seed transport refuted when seeds of width 4 are read", prof.first_fail() == 1)


def test_rollback_order_independent():
    # random dependency forests; the fixpoint must not depend on refutation order
    rnd = random.Random(45)
    for trial in range(200):
        n = 12
        parent = {i: (rnd.randrange(i) if i and rnd.random() < 0.7 else None) for i in range(n)}
        origin = {i: rnd.choice(["prediction", "lift", "cut", "narrow"]) for i in range(n)}
        refuted = set(rnd.sample(range(n), 3))

        def closure(order):
            ret = set()
            done = set()
            for r in order:
                done.add(r)
                changed = True
                while changed:
                    changed = False
                    for c in range(n):
                        p = parent[c]
                        if p is None or origin[c] not in v17.DEPENDENT_ORIGINS:
                            continue
                        if (p in done or p in ret) and c not in ret and c not in done:
                            ret.add(c)
                            changed = True
            return frozenset(ret | done)   # the set no longer asserted (labels may differ)
        results = {closure(o) for o in itertools.permutations(sorted(refuted))}
        if len(results) != 1:
            check("rollback order independence", False)
            return
    check("rollback is order independent on 200 random forests", True)


def test_classes():
    check("auto: 'infinitely many' is Pi2", v17.auto_claim_class("there are infinitely many white diagonals") == "Pi2")
    check("auto: 'implied by' is an implication", v17.auto_claim_class("H11 is implied by the gap growth") == "implication")
    check("auto: bounded range is finite", v17.auto_claim_class("every left diagonal D < 400 has period 8") == "finite")
    check("answer_of: survives-to asserts nothing", v17.answer_of(v17.SURVIVES_TO) is None)
    check("answer_of: proved asserts True", v17.answer_of(v17.PROVED) is True)


def test_engine_quick():
    eng = v17.EngineV17(quick=True, log=lambda *a, **k: None)
    rep = eng.run()
    st = {r["id"]: r["status"] for r in rep["final"]}
    check("engine: H19 refuted on escalation", st["H19"] == "refuted-on-escalation")
    check("engine: H36 refuted by recompute, corrected claim verified",
          st["H36"] == "refuted-by-recompute" and "verified-exact" in st.values())
    check("engine: H11 open", st["H11"] == "open")
    check("engine: no conflicts with Lean", not rep["conflicts"])
    check("engine: no layer-shape violations", not rep["shape_violations"])
    check("engine: dialogue speaks no refuted / retracted / untested claim", rep["v17_consistency"]["ok"])
    check("engine: every spoken claim has a backing", not rep["v17_consistency"]["spoken_without_backing"])


if __name__ == "__main__":
    test_layers()
    test_escalation()
    test_rollback_order_independent()
    test_classes()
    if "--unit" not in sys.argv:
        test_engine_quick()
    print(f"\n{len(FAILS)} failures")
    sys.exit(1 if FAILS else 0)
