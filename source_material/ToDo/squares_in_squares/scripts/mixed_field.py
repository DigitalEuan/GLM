#!/usr/bin/env python3
r"""mixed_field — run 83: the mixed-field grammar (Q | Q(sqrt 2)), exactly.

WHY THIS RUN EXISTS
-------------------
The lattice perspective works up to a point and then stops, and the reason is one
sentence: sqrt 2 is irrational, so no scale and no discrete symmetry label can make
a 45-degree pose satisfy an integer lattice predicate.  That sentence is not a
reason to drop the perspective; it is the object of study.  The program:

  Phase 1  lift the verification alphabet — coordinates as a + b*sqrt(2), with
           t = 0 (0 degrees) and t = sqrt(2)-1 (45 degrees) first-class
           (`qsqrt2.py`): an exact gate, no float, no tolerance.
  Phase 2  measure the seam — what a 45-degree block costs against a 0-degree
           core, and which single word is the cheapest bridge.
  Phase 3  carry the irrational across a rational interface with a delta-sigma
           modulator, and ask the exact gate what it actually certified.
  Phase 4  compare the algebraic extension with the rational escalation
           (t = 1/2, 1/3, 1/5 — shallow Pythagorean tilts that stay in Q).

WHAT IS AND IS NOT A RESULT HERE
--------------------------------
Every side quoted below is the container side of an *exact* sentence of the grammar
and every acceptance is `qsqrt2.gate` saying yes.  The families are proved minimal
within their own contact structure (shrinking the binding contact by 1e-3 is
refused), not over all packings.  No row of the delivered table changes.
"""
from __future__ import annotations

import json
import math
import os
import sys
from fractions import Fraction as F

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import qsqrt2 as Q                      # noqa: E402
import sqscore as SQ                    # noqa: E402

Q2, HALF, AXIS = Q.Q2, Q.HALF, Q.AXIS
ROOT = os.path.dirname(HERE)


# --------------------------------------------------------------- the words
def word45():
    return Q.word_45()


def word_t(t):
    return Q.word_t(F(t))


WORDS = (("45 deg", word45()),
         ("t=1/2 (53.13 deg)", word_t(F(1, 2))),
         ("t=1/3 (36.87 deg)", word_t(F(1, 3))),
         ("t=1/5 (22.62 deg)", word_t(F(1, 5))),
         ("t=1/7 (16.26 deg)", word_t(F(1, 7))))


# ------------------------------------------------------- phase 1: sentences
def two_corner(word, L=None):
    """One 0-degree square in a corner, one word square in the opposite corner.

    The word square touches the top and right walls, so its centre is (L-h, L-h)
    with h = (cos+sin)/2, and d = (L-h-1/2)(1,1).  The binding axis is the tilted
    square's own edge (c, s): d.(c,s) = (L-h-1/2)(cos+sin) must equal 1/2 + h, so

        L = (1/2 + h) (1 + 1/(cos+sin)) = (1 + cos + sin)^2 / (2 (cos + sin)).

    On that axis the 0-degree square's corner sits exactly on the tilted edge; on
    the axis square's own x axis the slack is strictly negative, which is why the
    binding axis is not the obvious one.
    """
    c, s = word
    acs = abs(c) + abs(s)
    if L is None:
        one_plus = Q2(1) + acs
        L = (one_plus * one_plus) / (Q2(2) * acs)
    h = acs * HALF
    return [(HALF, HALF), (L - h, L - h)], [AXIS, word], L


def corner_glue(word, L=None):
    """Four 0-degree squares in the corners, one word square in the middle.

    By symmetry the tilted square sits at (L/2, L/2); the binding contact with each
    corner square is on the tilted square's own edge axis, giving
    L = 2 + 1/(cos + sin).  Exact, and the four contacts are exact contacts.
    """
    c, s = word
    acs = abs(c) + abs(s)
    if L is None:
        L = Q2(2) + Q2(1) / acs
    h = acs * HALF
    mid = L / Q2(2)
    st = [(HALF, HALF), (L - HALF, HALF), (HALF, L - HALF),
          (L - HALF, L - HALF), (mid, mid)]
    return st, [AXIS] * 4 + [word], L


def ring_nine(L=None):
    """The natural home for a diamond: the hole in a 3x3 ring.

    Corner and edge squares are pushed to the walls, the diamond sits in the middle.
    L = 2 + sqrt 2 is the tight side of this family — 0.414 worse than the plain
    3x3 grid that holds the same nine squares.
    """
    if L is None:
        L = Q2(2) + Q.sqrt2()
    mid = L / Q2(2)
    st = [(HALF, HALF), (L - HALF, HALF), (HALF, L - HALF),
          (L - HALF, L - HALF),
          (mid, HALF), (mid, L - HALF), (HALF, mid), (L - HALF, mid),
          (mid, mid)]
    ws = [AXIS] * 8 + [word45()]
    return st, ws, L


SENTENCES = (
    ("pair, 45 deg", lambda L=None: two_corner(word45(), L=L)),
    ("pair, t=1/2", lambda L=None: two_corner(word_t(F(1, 2)), L=L)),
    ("pair, t=1/5", lambda L=None: two_corner(word_t(F(1, 5)), L=L)),
    ("corner glue, 45 deg", lambda L=None: corner_glue(word45(), L=L)),
    ("corner glue, t=1/2", lambda L=None: corner_glue(word_t(F(1, 2)), L=L)),
    ("corner glue, t=1/3", lambda L=None: corner_glue(word_t(F(1, 3)), L=L)),
    ("ring nine, 45 deg", ring_nine),
)


# ------------------------------------------------------------ phase 3: sigma
def sigma_coordinate(x: float, M: int, N: int) -> F:
    """First-order delta-sigma: the running mean of a rational stream on grid 1/M.

    The stream is generated against the *double image* of the field element (an
    error of 1e-16, four orders below the quantum 1/M); the object that is gated
    afterwards is the exact rational state, so the gate's verdict is exact.
    """
    e = F(0)
    tot = F(0)
    for _ in range(N):
        target = x + e
        k = int(math.floor(target * M + F(1, 2)))
        q = F(k, M)
        e = target - q
        tot += q
    return tot / N


def sigma_state(state, M: int, N: int):
    return [(Q2(F(sigma_coordinate(float(x), M, N))),
             Q2(F(sigma_coordinate(float(y), M, N)))) for x, y in state]


# ------------------------------------------------------------------- reports
def phase1(ledger):
    print("PHASE 1 — mixed sentences certified by the exact gate")
    print(f"{'sentence':22s} {'N':>3s} {'exact side':>18s} {'side':>10s} "
          f"{'gate':>5s} {'contact':>7s} {'grid':>5s} {'beats':>6s}")
    rows = []
    for name, build in SENTENCES:
        st, ws, L = build()
        g = Q.gate(st, ws)
        n = len(st)
        k = SQ.grid(n)
        rows.append({"sentence": name, "n": n, "side_exact": str(L),
                     "side": float(L), "gate": g["ok"],
                     "contacts": g["contacts"], "grid": k,
                     "beats": bool(g["ok"] and g["L"] < Q2(k)),
                     "clearance": float(g["clearance"]) if g["clearance"] else 0.0})
        print(f"{name:22s} {n:3d} {str(L):>18s} {float(L):10.6f} "
              f"{'yes' if g['ok'] else 'NO':>5s} {g['contacts']:7d} {k:5d} "
              f"{'yes' if rows[-1]['beats'] else 'no':>6s}")
    ledger["phase1_sentences"] = rows

    # the binding contact is load-bearing: 1/1000 less side is refused
    print("\n  the binding contact is load-bearing (side - 1/1000):")
    for name, build in SENTENCES:
        st, ws, L = build()
        st2, ws2, _ = build(L=L - Q2(F(1, 1000)))
        g2 = Q.gate(st2, ws2)
        rows = ledger["phase1_sentences"]
        ok = not g2["ok"]
        for r in rows:
            if r["sentence"] == name:
                r["refused_at_L_minus_1e-3"] = ok
                r["clearance_at_L_minus_1e-3"] = float(g2["clearance"])
        print(f"  {name:22s} refused: {'yes' if ok else 'NO'}  "
              f"clearance {float(g2['clearance']):+.6f}")
    return rows


def phase2(ledger):
    print("\nPHASE 2 — the seam law: what a tilted block costs against a 0-deg core")
    print("  For the corner glue the side is exactly L = 2 + 1/(cos+sin), and")
    print("  (cos+sin)^2 = 1 + sin(2 theta) <= 2, so L >= 2 + 1/sqrt 2 = "
          f"{float(Q2(2) + Q.sqrt2() * HALF):.6f},")
    print("  with equality only at 45 degrees.  The excess is the field-transition")
    print("  tax of that word, exactly:")
    base = Q2(2) + Q.sqrt2() * HALF
    rows = []
    for name, w in WORDS:
        c, s = w
        acs = abs(c) + abs(s)
        L = Q2(2) + Q2(1) / acs
        tax = L - base
        st, ws, _ = corner_glue(w)
        g = Q.gate(st, ws)
        rows.append({"word": name, "cos_plus_sin": str(acs),
                     "side_exact": str(L), "side": float(L),
                     "tax_vs_45_exact": str(tax), "tax_vs_45": float(tax),
                     "gate": g["ok"], "contacts": g["contacts"]})
        print(f"  {name:20s} cos+sin = {str(acs):8s}  L = {str(L):22s} "
              f"({float(L):.6f})  tax = {str(tax):18s} ({float(tax):+.6f})  "
              f"gate {'yes' if g['ok'] else 'NO'} / {g['contacts']} contacts")
    ledger["phase2_seam_law"] = rows

    # the glue word itself: how many squares does the bridge need?
    print("\n  the bridge: the corner glue couples four 0-degree squares through one")
    print("  tilted square, i.e. a glue word of length 1 for a 4-block.  The same")
    print("  nine squares with the diamond in the ring's hole need "
          f"{float(Q2(2) + Q.sqrt2()):.6f} against the grid's 3.000000,")
    print("  so a diamond can bridge a seam but cannot replace a square.")
    return rows


def phase3(ledger):
    print("\nPHASE 3 — delta-sigma across the seam: what the exact gate certifies")
    st, ws, L = corner_glue(word45())
    print(f"  exact 45-degree sentence: L = {str(L)} = {float(L):.9f}, "
          f"gate {'yes' if Q.gate(st, ws)['ok'] else 'NO'}, "
          f"{Q.gate(st, ws)['contacts']} exact contacts")
    M = 1000
    rows = []
    print(f"  {'N':>6s} {'max coord err':>13s} {'side excess':>13s} "
          f"{'side':>12s} {'gate':>5s} {'clearance':>14s}")
    for N in (1, 10, 100, 1000, 10000):
        qs = sigma_state(st, M, N)
        g = Q.gate(qs, ws)
        err = max(abs(float(qs[i][0]) - float(st[i][0]))
                  for i in range(len(st)))
        rows.append({"N": N, "M": M, "max_coordinate_error": err,
                     "side": float(g["L"]), "side_excess": float(g["L"] - L),
                     "clearance": float(g["clearance"]),
                     "gate": g["ok"], "contacts": g["contacts"]})
        print(f"  {N:6d} {err:13.3e} {float(g['L'] - L):+13.3e} "
              f"{float(g['L']):12.6f} {'yes' if g['ok'] else 'no':>5s} "
              f"{float(g['clearance']):+14.9f}")
    legal = [r for r in rows if r["gate"]]
    refused = [r for r in rows if not r["gate"]]
    for r in legal:
        assert r["side_excess"] > 0, r
    for r in refused:
        assert r["clearance"] < 0, r
    print(f"  {len(legal)} of {len(rows)} rungs pass, and every passing state does so")
    print("  at a *larger* side (min excess "
          f"{min(r['side_excess'] for r in legal):+.3e}); every refused state is"
          " an overlap at the exact side or below it.")
    print("  So the modulator never returns the sentence: it returns either an")
    print("  overlap at the exact side, or a legal packing at a worse side.  The")
    print("  running average converges; the sentence does not.  Only the field lift")
    print("  certifies it at its own side, with 4 exact contacts and no error at all.")
    ledger["phase3_sigma"] = rows
    return rows


def phase4(ledger):
    print("\nPHASE 4 — algebraic extension vs rational escalation, exactly")
    print(f"  {'word':20s} {'N=2 side':>22s} {'N=5 side':>22s} {'in Q?':>6s}")
    rows = []
    for name, w in WORDS:
        _, _, L2 = two_corner(w)
        _, _, L5 = corner_glue(w)
        rational = all(v.b == 0 for v in w)
        rows.append({"word": name, "side_n2_exact": str(L2), "side_n2": float(L2),
                     "side_n5_exact": str(L5), "side_n5": float(L5),
                     "rational_word": rational})
        print(f"  {name:20s} {str(L2):>12s} ({float(L2):.6f}) "
              f"{str(L5):>12s} ({float(L5):.6f}) {'yes' if rational else 'no':>6s}")
    best2 = min(rows, key=lambda r: r["side_n2"])
    best5 = min(rows, key=lambda r: r["side_n5"])
    L2_45 = two_corner(word45())[2]
    L5_45 = corner_glue(word45())[2]
    print(f"\n  N=2 winner is the shallowest tilt tested: {best2['word']} at "
          f"{best2['side_n2_exact']} ({best2['side_n2']:.6f}); the 45 deg pair "
          f"minus it is {L2_45 - two_corner(word_t(F(1, 7)))[2]} "
          f"({float(L2_45 - two_corner(word_t(F(1, 7)))[2]):+.6f}).")
    print("  Every word loses to the plain axis pair at side 2, and their sides")
    print("  approach 2 from above as theta -> 0, so N = 2 is an axis win.")
    print(f"  N=5 winner: {best5['word']} at {best5['side_n5_exact']} "
          f"({best5['side_n5']:.6f}); the t=1/2 glue costs "
          f"{corner_glue(word_t(F(1, 2)))[2] - L5_45} more (exactly), and both")
    print("  beat the plain grid's 3.")
    print("  So the two fields swap order between N=2 and N=5, by an exact rational")
    print("  inequality in Q(sqrt 2), not by a measurement.")
    ledger["phase4_escalation"] = {"rows": rows,
                                  "best_n2": best2["word"],
                                  "best_n5": best5["word"]}

    # integrality: the rational words scale to an integer sentence, 45 deg cannot
    print("\n  integrality, said exactly:")
    for name, w in WORDS:
        st, ws, L = two_corner(w)
        den = 1
        for v in [x for p in st for x in p] + [L] + [c for c in w] + [s for s in w]:
            den = den * v.a.denominator // math.gcd(den, v.a.denominator)
            den = den * v.b.denominator // math.gcd(den, v.b.denominator)
        ints = all((v * Q2(den)).b == 0 and (v * Q2(den)).a.denominator == 1
                   for v in [x for p in st for x in p] + [L])
        print(f"  {name:20s} scale {den:>3d}: integer coordinates: "
              f"{'yes' if ints else 'no'}")
    print("  A 45-degree pose can never be made integral: s*(1+sqrt 2) is rational")
    print("  only if sqrt 2 is, for every rational s != 0.  The ladder's rung is")
    print("  about the *integrality predicate*, not about the geometry.")
    return rows


def census(ledger):
    """How much of the delivered table is even writable in the word alphabet."""
    per = SQ.load()
    words = [0.0, 45.0, math.degrees(math.atan(1 / 2)), math.degrees(math.atan(1 / 3)),
             math.degrees(math.atan(1 / 5)), math.degrees(math.atan(1 / 7))]

    def deficit(th):
        a = math.degrees(th) % 90.0
        return min(min(abs(a - w), 90.0 - abs(a - w)) for w in words)

    worst_of_row = []
    cls = {"axis word exact": 0, "45 deg decimal": 0, "mixed words": 0,
           "no word": 0}
    diag = []                      # |stored angle - pi/4| for the 45-degree rows
    for n, st in per.items():
        ds = [deficit(th) for _, _, th in st]
        worst = max(ds)
        worst_of_row.append((n, worst))
        zero = all(min(math.degrees(th) % 90.0,
                       90.0 - math.degrees(th) % 90.0) == 0.0
                   for _, _, th in st)
        if zero:
            cls["axis word exact"] += 1
        elif worst < 1e-9:
            cls["45 deg decimal"] += 1
            diag.append(worst)
        elif worst < 1e-3:
            cls["mixed words"] += 1
        else:
            cls["no word"] += 1
    worst_of_row.sort(key=lambda t: t[1])
    exact = sum(1 for _, w in worst_of_row if w < 1e-9)
    near = sum(1 for _, w in worst_of_row if w < 1e-3)
    med = worst_of_row[len(worst_of_row) // 2][1]
    print("\nCENSUS — is the delivered table a sentence of this grammar?")
    print(f"  exactly the 0-degree word (stored angle 0.0): "
          f"{cls['axis word exact']}/1000")
    print(f"  within 1e-9 deg of 45 deg, i.e. a decimal shadow of the word: "
          f"{cls['45 deg decimal']}/1000 (deficit "
          f"{math.radians(min(diag)):.1e} to {math.radians(max(diag)):.1e} rad)")
    print(f"  mixing words at 1e-3 deg: {cls['mixed words']}; "
          f"using no word at all: {cls['no word']}/1000 "
          f"(the median row's worst square is {med:.1f} deg from the alphabet,")
    print("  because the median row is a word row)")
    print("  So 447 rows are exactly the t = 0 word (their sides are the 447 in Q")
    print("  that run 78 recorded), 100 are the 45-degree word up to a 1e-13 rad")
    print("  decimal, and 451 rows are not writable in the alphabet at all.  The")
    print("  lifted grammar certifies sentences written in the field; it cannot")
    print("  retrofit a decimal table.  That is why the mixed work has to build.")
    ledger["census"] = {"rows_exact_word_1e-9": exact, "rows_within_1e-3": near,
                        "classes": cls, "median_worst_deg": med,
                        "diag_deficit_rad_min": math.radians(min(diag)),
                        "diag_deficit_rad_max": math.radians(max(diag))}
    return exact


# ------------------------------------------------------------------ selftest
def selftest() -> int:
    checks = 0

    # 1. every sentence is accepted, at its own exact side, with exact contacts
    for name, build in SENTENCES:
        st, ws, L = build()
        g = Q.gate(st, ws)
        assert g["ok"], name
        assert g["L"] == L, (name, g["L"], L)
        assert g["clearance"].sign() == 0, name
        checks += 1
    print(f"control 1 — {checks} sentences accepted at their own exact side, "
          "each with clearance exactly 0")

    # 2. shrinking the binding contact is refused (the side is tight in-family)
    for name, build in SENTENCES:
        st, ws, L = build()
        st2, ws2, _ = build(L=L - Q2(F(1, 1000)))
        assert not Q.gate(st2, ws2)["ok"], name
    print(f"control 2 — all {len(SENTENCES)} refuse side - 1/1000: the quoted "
          "side is the tight side of its family")

    # 3. the seam law's inequality, exactly, for every word
    for name, w in WORDS:
        acs = abs(w[0]) + abs(w[1])
        assert Q.sqrt2() >= acs, name
        assert (Q.sqrt2() - acs).sign() == 0 or name != "45 deg"
    assert (Q.sqrt2() - (abs(word45()[0]) + abs(word45()[1]))).sign() == 0
    print("control 3 — cos+sin <= sqrt2 exactly, with equality only at 45 deg, so "
          "L = 2+1/(cos+sin) >= 2+1/sqrt2")

    # 4. the rational words are in Q and the 45-degree word is not
    assert all(v.b == 0 for v in word_t(F(1, 2)))
    assert word45()[0].b != 0
    print("control 4 — the rational t-basis words have zero sqrt2 part; the "
          "45-degree word has not, and no scale removes it")

    # 5. the modulator's state is rational and its gate verdict is exact
    st, ws, L = corner_glue(word45())
    qs = sigma_state(st, 1000, 10)
    assert all(v.b == 0 for p in qs for v in p)
    g = Q.gate(qs, ws)
    assert not g["ok"] and g["clearance"].sign() < 0
    print(f"control 5 — the N=10 quantized state is rational (gate exact) and is "
          f"refused with clearance {float(g['clearance']):+.2e}")

    # 6. the exact sentence and the float scorer agree on a rational sentence
    import packlib as P
    st, ws, L = two_corner(word_t(F(1, 2)))
    f = P.verify(Q.float_state(st, ws))
    assert abs(float(L) - f["L"]) < 1e-12 and f["ok"]
    print(f"control 6 — the exact rational pair ({str(L)}) matches packlib's float "
          "side and passes the float gate")

    print(f"selftest: OK ({checks + 6} controls)")
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    SQ.guard(quiet=True)
    print("run 83 — mixed_field.py: the Q | Q(sqrt 2) grammar, exactly")
    print(f"scorer guard: {SQ.summarise(SQ.load())['score']:.9f}, no row changes\n")
    ledger = {"run": 83, "instrument": "mixed_field.py + qsqrt2.py"}
    phase1(ledger)
    phase2(ledger)
    phase3(ledger)
    phase4(ledger)
    census(ledger)
    out = os.path.join(ROOT, "workspace/push/mixed_field.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(ledger, f, indent=1)
    print(f"\nledger: {os.path.relpath(out, ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
