#!/usr/bin/env python3
"""Tests for the self-contained GLM Hypothesis Engine v18.

    python3 test_hypothesis_engine.py          # about 30 s (one quick run of every domain)

Standard library only.  Each test prints PASS / FAIL; the exit code is the number of failures.
"""

import json
import sys
import tempfile
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hypothesis_engine as E  # noqa: E402

RESULTS = []


def test(name):
    def deco(f):
        try:
            f()
            RESULTS.append((name, True, ""))
        except AssertionError as e:
            RESULTS.append((name, False, str(e)))
        except Exception as e:  # noqa: BLE001
            RESULTS.append((name, False, f"{type(e).__name__}: {e}"))
        return f
    return deco


@test("built-in selftest")
def _():
    assert E.selftest() == 0


@test("exact tools agree with the Lean certificates")
def _():
    b = E.centre_bits(30000)
    p = E.lc_profile(b[:20000])
    assert 2 * p[11101] - 11101 == 11                       # WheelChecksData.wheel_H19_false
    assert 2 * p[19521] - 19521 == 13                       # WheelChecksData.ledger_C160_overstated
    for q in range(1, 65):                                  # GateLoopData.centre_no_short_period_30000
        assert any(b[t] != b[t + q] for t in range(29000, 29900))


@test("left-diagonal facts on D < 1000")
def _():
    dt = E.DiagonalTable(999)
    assert all(16 % dt.period[D] == 0 for D in range(1000))    # leftDiag_period_sixteen_below_87867
    assert all(8 % dt.period[D] == 0 for D in range(400))       # leftDiag_period_eight_below_400
    assert all(dt.pre[D] > D for D in range(20, 1000))          # centerCol_read_in_transient


R30 = E.R30Data(quick=True)


@test("Rule 30 run: no wrong answers, no overclaims, no conflicts, consistent dialogue")
def _():
    _, rep = E.run_rule30(R30, True)
    s = rep["score"]
    assert s["wrong"] == 0 and s["overclaim"] == 0, s
    assert rep["conflicts"] == [], rep["conflicts"]
    assert rep["dialogue_consistency"]["ok"], rep["dialogue_consistency"]


@test("Rule 30 without the ledger: still no wrong answers or overclaims; nothing is 'proved'")
def _():
    eng, rep = E.run_rule30(R30, False)
    s = rep["score"]
    assert s["wrong"] == 0 and s["overclaim"] == 0, s
    assert not any(h.status == E.PROVED for h in eng.hyps)
    assert rep["dialogue_consistency"]["ok"]


@test("every PROVED status cites a Lean name; every refutation has backing")
def _():
    eng, _ = E.run_rule30(R30, True)
    for h in eng.hyps:
        if h.status == E.PROVED:
            assert any(x.startswith(("FORMAL", "CERT")) for x in h.backing), h.hid
        if E.is_refuted(h.status):
            assert h.backing, h.hid


@test("arrows: reads are a prefix of the ladder; a flip is a real counterexample")
def _():
    eng, _ = E.run_rule30(R30, True)
    flips = 0
    for h in eng.hyps:
        if h.profile:
            assert h.profile.shape_ok(), h.hid
            a = h.profile.arrow()
            assert a["read"] == list(E.LAYERS[:len(a["read"])]), (h.hid, a)
            if a["direction"].startswith("flipped"):
                flips += 1
                assert h.status == E.REF_ESCALATION
    assert flips >= 4, flips


@test("conjecture loop: a flipped lift is re-lifted upwards and narrowed")
def _():
    eng, _ = E.run_rule30(R30, True)
    lc = [h for h in eng.hyps if h.key == "CC.lc.near.half"]
    bs = [h.params["b"] for h in lc]
    assert bs == sorted(bs) and len(set(bs)) == len(bs) and bs[0] == 10, bs
    nar = [h for h in eng.hyps if h.key == "LD.period.divides.below"]
    assert nar and nar[0].status == E.PROVED


@test("Pi2 claims are never decided by data alone")
def _():
    eng, _ = E.run_rule30(R30, False)
    for h in eng.hyps:
        if h.cls == "Pi2":
            assert h.status == E.OPEN, (h.hid, h.status)


@test("rollback follows 'uses' edges only and is order independent")
def _():
    def build(order):
        e = E.Engine()
        hs = {}
        spec = [("a", "Pi1", []), ("b", "analogy", [("a", E.USES)]), ("c", "analogy", [("b", E.USES)]),
                ("d", "analogy", [("a", E.DERIVED)])]
        for name, cls, deps in [spec[i] for i in order]:
            hs[name] = E.Hypothesis(name, name, name, cls)
        for name, cls, deps in spec:
            hs[name].deps = deps
            if name == "a":
                hs[name].check, hs[name].scales = (lambda N: (N < 2, "x")), [1, 2, 3, 4, 5]
        for i in order:
            e.add(hs[spec[i][0]])
        e.run()
        return {k: v.status for k, v in hs.items()}
    r1, r2 = build([0, 1, 2, 3]), build([3, 2, 1, 0])
    assert r1 == r2, (r1, r2)
    assert r1["c"] == E.RETRACTED and r1["d"] == E.UNTESTED


@test("general domain: every trap is caught; gcd witness recomputed exactly")
def _():
    eng, rep = E.run_general(True)
    s = rep["score"]
    assert s["wrong"] == 0 and s["right"] == s["n"], s
    g = [h for h in eng.hyps if h.key == "GEN.gcd.trap"][0]
    assert any("recomputed here" in b for b in g.backing)
    eng2, rep2 = E.run_general(False)
    g2 = [h for h in eng2.hyps if h.key == "GEN.gcd.trap"][0]
    assert g2.status == E.SURVIVES_TO and rep2["score"]["wrong"] == 0


@test("claims file: tests run, untestable ideas stay untested, nothing is proved")
def _():
    claims = [{"key": "T.sq", "text": "n² mod 4 is 0 or 1", "test": "n*n % 4 in (0, 1)", "class": "Pi1",
               "scales": [10, 100, 1000, 2000, 5000]},
              {"key": "T.bad", "text": "n² + 1 is prime", "test": "isprime(n*n + 1)", "class": "Pi1",
               "scales": [2, 5, 10, 50, 100], "start": 1},
              {"key": "T.gen", "text": "n is prime exactly when it has two divisors",
               "test": "isprime(n) == (sum(1 for d in range(1, n + 1) if n % d == 0) == 2)",
               "class": "Pi1", "scales": [10, 50, 100, 300, 600], "start": 1},
              {"key": "T.idea", "text": "the wobble is analogous to a pendulum"},
              {"key": "T.evil", "text": "x", "test": "().__class__", "class": "Pi1", "scales": [1, 2, 3, 4, 5]}]
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "c.json"
        p.write_text(json.dumps(claims))
        eng = E.Engine()
        for h in E.load_claims_file(p):
            eng.add(h)
        eng.run()
    st = {h.key: h.status for h in eng.hyps}
    assert st["T.sq"] == E.SURVIVES_TO and st["T.bad"] == E.REF_ESCALATION and st["T.gen"] == E.SURVIVES_TO, st
    assert st["T.idea"] == E.UNTESTED and st["T.evil"] == E.UNTESTED, st
    assert E.PROVED not in st.values()


@test("ARC: refuses on ambiguity, never wrong on synthetic or real tasks, needs routing beats random")
def _():
    syn = E.make_synthetic(4402, 2)
    r = E.run_arc(syn, random_draws=2)
    assert r["on_demand"].get("wrong", 0) == 0
    assert r["on_demand"].get("right", 0) > max(d.get("right", 0) for d in r["random_same_size"])
    z = HERE.parent / "glm_repo.zip"
    if z.exists():
        real = E.run_arc(E.load_arc_zip(z), random_draws=1)
        assert real["on_demand"].get("wrong", 0) == 0 and real["on_demand"].get("right", 0) >= 9, real["on_demand"]


@test("wheel turn of the owner's glm_wheel.json: refuted entries leave THINKS-TRUE, needs are matched")
def _():
    src = HERE.parent / "glm_wheel.json"
    if not src.exists():
        return
    t = E.turn_wheel(json.loads(src.read_text()), R30, True)
    st = {m["was_hid"]: m["now_status"] for m in t["moves"]}
    assert st["H19"].startswith("refuted") and st["H36"].startswith("refuted") and st["H39"].startswith("refuted")
    assert st["H16"] == E.PROVED and st["H32"].startswith("refuted") and st["H23"] == E.UNTESTED
    met = {n["need"]: n["status"] for n in t["needs"]}
    assert met["NEEDED-5"] == "met" and met["NEEDED-2"] == "unmet"
    assert t["conflicts"] == []


@test("wheel turn of a v18 wheel is a fixpoint (same rings, no conflicts)")
def _():
    _, rep = E.run_rule30(R30, True)
    w = E.combined_wheel([rep], None)
    t = E.turn_wheel(json.loads(json.dumps(E._jsonable(w))), R30, True)
    assert all(a.split(" -> ")[0] == a.split(" -> ")[1] for a in t["summary"]), t["summary"]
    assert t["conflicts"] == []


@test("observer arrow: exact count matches the definition")
def _():
    b = [1, 1, 0, 1, 1, 1, 0, 0]
    # D: 0,1,2,1,2,3,4,3 ; steps with D != 0 follow the arrow when the step goes towards 0
    assert E.observer_arrow_agreement(b) == Fraction(3, 7)


if __name__ == "__main__":
    fails = 0
    for name, ok, msg in RESULTS:
        print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"\n     {msg}"))
        fails += not ok
    print(f"{len(RESULTS) - fails}/{len(RESULTS)} passed")
    sys.exit(fails)
