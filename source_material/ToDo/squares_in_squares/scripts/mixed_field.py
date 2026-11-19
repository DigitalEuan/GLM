#!/usr/bin/env python3
r"""mixed_field — the Q | Q(sqrt 2) grammar, exactly (runs 83-84).

RUN 83 built the field, the gate and the seam law.  RUN 84 pushes the
architecture forward with three upgrades, each float-free in its decisions:

  1. the symbolic perception lift (`--lift`): the delivered rows that are written
     in the two words are reconstructed as exact sentences, and the gate says
     which of them are sentences of this grammar and where decimal drift broke a
     contact.  Implementation lives in `qsqrt2.lift_sentence`.
  2. the pure-algebraic carrier (`phase3`): a delta-sigma accumulator that never
     calls float(), driven by exact Q2 comparisons, measured against the Pell
     convergent ladder.
  3. the seam production rules (`phase_seam`): the exact rewrite rule for
     splicing an m-square 45-degree diagonal strip onto four k-blocks, with
     closed forms for the side, the void area and the cost per square, verified
     by the gate for k = 2..10.

WHAT IS AND IS NOT A RESULT HERE
--------------------------------
Every side quoted is the container side of an exact sentence of the grammar, and
every acceptance is `qsqrt2.gate` saying yes.  No row of the delivered table is
changed, and no float placement is reported as a packing.
"""
from __future__ import annotations

import csv
import json
import math
import os
import sys
import time
from fractions import Fraction as F

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import qsqrt2 as Q                      # noqa: E402
import sqscore as SQ                    # noqa: E402

Q2, HALF, AXIS = Q.Q2, Q.HALF, Q.AXIS
ROOT = os.path.dirname(HERE)
LEDGER = os.path.join(ROOT, "workspace/push/mixed_field.json")
LIFT_LEDGER = os.path.join(ROOT, "workspace/push/uplift.json")
SUBMISSION = os.path.join(ROOT, "workspace/submission/submission.csv")


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

    By symmetry the tilted square sits at (L/2, L/2); the binding contact with
    each corner square is on the tilted square's own edge axis, giving
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
    """The natural home for a diamond: the hole in a 3x3 ring."""
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


# ------------------------------------------- upgrade 2: the exact carrier
def sigma_stream_exact(x: Q2, M: int, N: int):
    """First-order delta-sigma whose accumulator is a field element.

    `e` is the exact residue `x + e_prev - q`; the quantizer rounds `x + e` to the
    nearest multiple of 1/M by `qsqrt2.grid_round`, which decides the rounding
    with exact sign comparisons.  No float() is called anywhere in this function
    or in the two below it (control 4 walks their code objects for the name).

    Returns the running mean of the emitted rational steps — the quantized
    coordinate after N cycles.
    """
    e = Q2(0)
    tot = F(0)
    for _ in range(N):
        z = x + e
        qv = Q.grid_round(z, M)
        e = z - Q2(qv)
        tot += qv
    return tot / N


def sigma_state_exact(state, M: int, N: int):
    return [(Q2(sigma_stream_exact(x, M, N)), Q2(sigma_stream_exact(y, M, N)))
            for x, y in state]


def pell_convergents(qmax: int = 100000):
    """The Pell ladder of sqrt 2: 1/1, 3/2, 7/5, 17/12, ... with q <= qmax."""
    out = []
    pp, qp, p, q = 1, 0, 1, 1
    while q <= qmax:
        out.append((p, q))
        pp, qp, p, q = p, q, 2 * p + pp, 2 * q + qp
    return out


def pell_state(state, p: int, q: int):
    """The sentence with sqrt 2 replaced by the rational convergent p/q."""
    r = F(p, q)
    return [(Q2(x.a + x.b * r), Q2(y.a + y.b * r)) for x, y in state]


# ------------------------------------------------------ upgrade 3: the rules
def strip_side(k, m) -> Q2:
    """Exact side of the splice: four k-blocks plus an m-square diagonal strip."""
    return Q2(2 * k) + Q2(0, F(m, 2))


def strip_count(k, m) -> int:
    return 4 * k * k + m


def strip_void(k, m) -> Q2:
    """Exact uncovered area of that sentence: L^2 - N."""
    L = strip_side(k, m)
    return L * L - Q2(strip_count(k, m))


def strip_sentence(k, m, L=None):
    """Four k x k axis blocks in the corners, an m-diamond strip on the anti-diagonal."""
    if L is None:
        L = strip_side(k, m)
    st, ws = [], []
    for cx in (0, 1):
        for cy in (0, 1):
            ox = Q2(0) if cx == 0 else L - Q2(k)
            oy = Q2(0) if cy == 0 else L - Q2(k)
            for i in range(k):
                for j in range(k):
                    st.append((ox + Q2(i) + HALF, oy + Q2(j) + HALF))
                    ws.append(AXIS)
    mid = L / Q2(2)
    for j in range(m):
        t = Q2(0, F(2 * j - (m - 1), 4))       # (j - (m-1)/2) / sqrt 2
        st.append((mid + t, mid - t))
        ws.append(word45())
    return st, ws, L


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
    return rows


def phase2(ledger):
    print("\nPHASE 2 — the seam law: what a tilted block costs against a 0-deg core")
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
              f"({float(L):.6f})  tax = {str(tax):18s} ({float(tax):+.6f})")
    ledger["phase2_seam_law"] = rows
    return rows


def phase3(ledger):
    print("\nPHASE 3 — the pure-algebraic carrier: two rational ladders vs the gate")
    st, ws, L = corner_glue(word45())
    g0 = Q.gate(st, ws)
    print(f"  exact 45-degree sentence: L = {str(L)} = {float(L):.9f}, "
          f"gate yes, {g0['contacts']} exact contacts")
    who = [i for i, w in enumerate(ws) if w[0].b != 0][0]
    x0 = st[who][0]
    print(f"  carrying one coordinate, x = {str(x0)} = {float(x0):.12f}, to grid 1/M")

    rows = []
    print(f"  {'ladder':22s} {'rung':>8s} {'coord error':>13s} "
          f"{'side excess':>13s} {'clearance':>13s} {'gate':>5s}")
    for M in (1000,):
        for N in (1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000):
            qx = Q2(sigma_stream_exact(x0, M, N))
            err = abs(qx - x0)
            qs = sigma_state_exact(st, M, N)
            g = Q.gate(qs, ws)
            rows.append({"ladder": "delta-sigma", "M": M, "N": N,
                         "coord_error": float(err),
                         "side_excess": float(g["L"] - L),
                         "clearance": float(g["clearance"]),
                         "gate": g["ok"]})
            print(f"  {'delta-sigma M=' + str(M):22s} {N:8d} {float(err):13.3e} "
                  f"{float(g['L'] - L):+13.3e} {float(g['clearance']):+13.3e} "
                  f"{'yes' if g['ok'] else 'no':>5s}")
    for p, q in pell_convergents(20000):
        ps = pell_state(st, p, q)
        g = Q.gate(ps, ws)
        err = abs(Q2(x0.a + x0.b * F(p, q)) - x0)
        rows.append({"ladder": "pell", "p": p, "q": q,
                     "coord_error": float(err),
                     "side_excess": float(g["L"] - L),
                     "clearance": float(g["clearance"]), "gate": g["ok"]})
        print(f"  {'pell ' + str(p) + '/' + str(q):22s} {q:8d} {float(err):13.3e} "
              f"{float(g['L'] - L):+13.3e} {float(g['clearance']):+13.3e} "
              f"{'yes' if g['ok'] else 'no':>5s}")
    ds = [r for r in rows if r["ladder"] == "delta-sigma"]
    pe = [r for r in rows if r["ladder"] == "pell"]
    print(f"  delta-sigma: {sum(1 for r in ds if r['gate'])} of {len(ds)} rungs legal")
    print(f"  pell:        {sum(1 for r in pe if r['gate'])} of {len(pe)} rungs legal")
    print("  Both ladders converge and neither returns the sentence: every legal")
    print("  rung is legal at a side ABOVE the exact one, and every rung at or below")
    print("  it is an overlap.  The exact 0 is reached only by the pair (a, b).")
    ledger["phase3_carrier"] = rows
    return rows


def phase_seam(ledger):
    print("\nUPGRADE 3 — the seam production rule, exactly")
    print("  rule S(k, m): four k x k axis blocks in the corners of the box, and an")
    print("  m-square 45-degree strip along the anti-diagonal.  Closed forms:")
    print("    side      L(k, m) = 2k + m*sqrt2/2")
    print("    count     N(k, m) = 4k^2 + m")
    print("    void      V(k, m) = L^2 - N = 2km*sqrt2 + m^2/2 - m")
    print("    cost      L(k, m) - 2k = m*sqrt2/2      (per square: sqrt2/2)")
    print("    seam      the interface is m diagonal seams, each exactly tight; the")
    print("              strip's own band width is sqrt2, its zigzag amplitude sqrt2/2")
    print(f"\n  {'k':>3s} {'m':>3s} {'N':>5s} {'L exact':>18s} {'L':>10s} "
          f"{'gain vs grid':>13s} {'void exact':>22s} {'gate':>5s} {'-1e-9':>6s}")
    rows = []
    bad = []
    for k in range(2, 11):
        for m in range(1, 7):
            st, ws, L = strip_sentence(k, m)
            n = len(st)
            g = Q.gate(st, ws)
            g2 = Q.gate(*strip_sentence(k, m, L=L - Q2(F(1, 10 ** 9)))[:2])
            gain = Q2(SQ.grid(n)) - L
            void = strip_void(k, m)
            ok = g["ok"] and not g2["ok"]
            if not ok:
                bad.append((k, m, g["ok"], g2["ok"]))
            rows.append({"k": k, "m": m, "n": n, "side_exact": str(L),
                         "side": float(L), "gain_exact": str(gain),
                         "gain": float(gain), "void_exact": str(void),
                         "void": float(void), "gate": g["ok"],
                         "refused_below": not g2["ok"],
                         "contacts": g["contacts"]})
            print(f"  {k:3d} {m:3d} {n:5d} {str(L):>18s} {float(L):10.6f} "
                  f"{float(gain):+13.6f} {str(void):>22s} "
                  f"{'yes' if g['ok'] else 'NO':>5s} "
                  f"{'yes' if not g2['ok'] else 'NO':>6s}")
    print(f"\n  {len(rows) - len(bad)}/{len(rows)} sentences certified at the closed-form")
    print("  side and refused 1e-9 below it.")
    wins = [(r["k"], r["m"]) for r in rows if r["gain"] > 0]
    print(f"  gain > 0 at: {wins} — the strip buys side only for m = 1, and the")
    print("  reason is exact: gain = 1 - m*sqrt2/2 changes sign at m = sqrt2.")
    ledger["seam_rules"] = {"rows": rows, "wins": wins, "bad": bad}
    return rows


# ------------------------------------------- upgrade 1: the symbolic lift
def load_rows_exact(path=SUBMISSION):
    """Read the submission with exact decimal coordinates (no float conversion)."""
    rows = {}
    with open(path) as f:
        for r in csv.DictReader(f):
            rows.setdefault(int(r["n"]), []).append(
                (F(r["x"]), F(r["y"]), float(r["angle"])))
    return rows


def mixed_word_rows(rows):
    """Rows whose every square is written in the 0-degree or the 45-degree word."""
    out = []
    for n, st in rows.items():
        a = [math.degrees(t) % 90 for _, _, t in st]
        if any(abs(v - 45) < 1e-9 for v in a) and all(min(abs(v - 45), v) < 1e-9 for v in a):
            out.append(n)
    return sorted(out)


def words_of(st):
    return [word45() if abs(math.degrees(t) % 90 - 45) < 1e-9 else AXIS
            for _, _, t in st]


def uplift(budget=170.0):
    """Lift every mixed-word row into the field and gate it.  Budgeted and cached."""
    ledger = {}
    if os.path.exists(LIFT_LEDGER):
        ledger = json.load(open(LIFT_LEDGER))
    rows = load_rows_exact()
    targets = mixed_word_rows(rows)
    done = ledger.setdefault("rows", {})
    print(f"UPGRADE 1 — the symbolic perception lift: {len(targets)} word rows, "
          f"{len(done)} already lifted")
    t0 = time.time()
    fresh = 0
    for n in targets:
        if str(n) in done:
            continue
        if time.time() - t0 > budget:
            break
        st = rows[n]
        ws = words_of(st)
        centres = [(Q2(x), Q2(y)) for x, y, _ in st]
        r = Q.lift_sentence(centres, ws)
        done[str(n)] = {
            "n": n, "squares": len(st),
            "tilted": sum(1 for w in ws if w[0].b != 0),
            "status": r["status"], "placed": r["placed"], "used": r["used"],
            "side_exact": str(r["L"]) if r["L"] is not None else None,
            "side": float(r["L"]) if r["L"] is not None else None,
            "decimal_side": float(Q.side(centres, ws)),
            "clearance": float(r["clearance"]) if r["clearance"] is not None else None,
            "contacts": r["contacts"], "violations": r["violations"],
            "recovered": r.get("recovered", 0),
            "unrecovered": r.get("unrecovered", 0),
            "side_residual": float(r["side_residual"]),
        }
        fresh += 1
        if fresh % 10 == 0:
            json.dump(ledger, open(LIFT_LEDGER, "w"), indent=1)
    json.dump(ledger, open(LIFT_LEDGER, "w"), indent=1)

    todo = [n for n in targets if str(n) not in done]
    counts = {}
    for n in targets:
        r = done.get(str(n))
        if r:
            counts[r["status"]] = counts.get(r["status"], 0) + 1
    print(f"  lifted this call: {fresh}; remaining: {len(todo)}; "
          f"statuses: {dict(sorted(counts.items()))}")
    if not todo:
        lifted = [done[str(n)] for n in targets if done[str(n)]["status"] == "lifted"]
        lifted.sort(key=lambda r: r["n"])
        print(f"\n  {'n':>4s} {'sq':>4s} {'tilt':>5s} {'exact side':>22s} "
              f"{'side':>10s} {'contacts':>8s} {'grid':>5s}")
        for r in lifted[:24]:
            print(f"  {r['n']:4d} {r['squares']:4d} {r['tilted']:5d} "
                  f"{str(r['side_exact'])[:22]:>22s} {r['side']:10.6f} "
                  f"{r['contacts']:8d} {SQ.grid(r['n']):5d}")
        if len(lifted) > 24:
            print(f"  ... {len(lifted) - 24} more")
        inq = sum(1 for r in lifted if "√2" not in (r["side_exact"] or ""))
        print(f"\n  lifted: {len(lifted)} rows ({inq} with a side in Q, "
              f"{len(lifted) - inq} in Q(sqrt 2) but not Q)")
        rec = sum(r.get("recovered") or 0 for r in lifted)
        peeled = sum(r["placed"] - (r.get("recovered") or 0) for r in lifted)
        print(f"  equations: {peeled} centres placed by wall + contact peeling, "
              f"{rec} more by height-bounded recovery")
        drift = [r for n in targets for r in [done[str(n)]]
                 if r["status"] in ("overlap", "underdetermined", "side-not-recovered",
                                    "not-on-lattice")]
        print(f"  drift: {len(drift)} rows where the decimal state is not a sentence:")
        for r in drift[:10]:
            extra = ""
            if r["status"] == "overlap":
                extra = f" clearance {r['clearance']:+.3e}, {r['violations']} violations"
            elif r["status"] == "underdetermined":
                extra = f" placed {r['placed']}/{r['squares']}"
            elif r["status"] == "not-on-lattice":
                extra = (f" placed {r['placed']}/{r['squares']}, "
                         f"{r.get('unrecovered') or 0} coordinates off-lattice")
            else:
                extra = f" side residual {r['side_residual']:.2e}"
            print(f"    n={r['n']:4d} {r['status']:19s} L={r['side_exact']}{extra}")
        ledger["summary"] = {"targets": len(targets), "statuses": counts,
                             "lifted": len(lifted), "in_q": inq,
                             "recovered_coords": rec, "peeled_centres": peeled}
        json.dump(ledger, open(LIFT_LEDGER, "w"), indent=1)
    return counts, todo


# ------------------------------------------------------------------- census
def census(ledger):
    per = SQ.load()
    zero = mixed = other = 0
    for n, st in per.items():
        a = [math.degrees(t) % 90 for _, _, t in st]
        if all(v == 0.0 for v in a):
            zero += 1
        elif all(min(abs(v - 45), v) < 1e-9 for v in a):
            mixed += 1
        else:
            other += 1
    print("\nCENSUS — which rows are written in the two words")
    print(f"  exactly the 0-degree word (stored angle 0.0): {zero}/1000")
    print(f"  every square in {{0 deg, 45 deg}}: {mixed}/1000  <- the lift's targets")
    print(f"  no word at all: {other}/1000")
    ledger["census"] = {"zero": zero, "mixed": mixed, "other": other}
    return mixed


# ------------------------------------------------------------------ selftest
def selftest() -> int:
    checks = 0

    for name, build in SENTENCES:
        st, ws, L = build()
        g = Q.gate(st, ws)
        assert g["ok"] and g["L"] == L and g["clearance"] == 0, name
        checks += 1
    print(f"control 1 — {checks} sentences accepted at their own exact side")

    for name, build in SENTENCES:
        st, ws, L = build()
        st2, ws2, _ = build(L=L - Q2(F(1, 1000)))
        assert not Q.gate(st2, ws2)["ok"], name
    print(f"control 2 — all {len(SENTENCES)} refuse side - 1/1000")

    for name, w in WORDS:
        acs = abs(w[0]) + abs(w[1])
        assert Q.sqrt2() >= acs, name
    assert (Q.sqrt2() - (abs(word45()[0]) + abs(word45()[1]))).sign() == 0
    print("control 3 — cos+sin <= sqrt2 exactly, equality only at 45 deg")

    # 4. the carrier's bytecode never calls float (a source grep would trip over
    #    the docstrings, so look at the code objects)
    def uses_float(fn):
        stack = [fn.__code__]
        while stack:
            c = stack.pop()
            if "float" in c.co_names:
                return True
            stack.extend(k for k in c.co_consts if hasattr(k, "co_names"))
        return False
    for fn in (sigma_stream_exact, sigma_state_exact, pell_state, strip_sentence,
               Q.grid_round, Q.floor_q2):
        assert not uses_float(fn), fn.__name__
    print("control 4 — the carrier, the Pell substitution, the seam builder and the "
          "quantizer call no float (checked in the bytecode)")

    # 5. the carrier is rational and its ladder brackets the exact coordinate
    st, ws, L = corner_glue(word45())
    x0 = st[[i for i, w in enumerate(ws) if w[0].b != 0][0]][0]
    qs = sigma_state_exact(st, 1000, 200)
    assert all(v.b == 0 for p in qs for v in p)
    e1 = abs(Q2(sigma_stream_exact(x0, 1000, 1)) - x0)
    e2 = abs(Q2(sigma_stream_exact(x0, 1000, 200)) - x0)
    assert e2 < e1 / 10
    print(f"control 5 — the carrier's state is rational; its coordinate error falls "
          f"from {float(e1):.2e} at N=1 to {float(e2):.2e} at N=200")

    # 6. the Pell ladder is exact and its error falls like 1/q^2
    pc = pell_convergents(10000)
    assert pc[0] == (1, 1) and pc[1] == (3, 2) and pc[2] == (7, 5)
    errs = [abs(Q2(F(p, q)) - Q.sqrt2()) for p, q in pc[:6]]
    assert all(errs[i + 1] < errs[i] for i in range(len(errs) - 1))
    print(f"control 6 — Pell convergents 1/1 .. {pc[5][0]}/{pc[5][1]}: "
          f"|p/q - sqrt2| falls from {float(errs[0]):.2e} to {float(errs[-1]):.2e}")

    # 7. the strip rule: closed forms hold and the gate certifies the sentence
    for k in (2, 3, 5):
        for m in (1, 2, 4):
            st, ws, L = strip_sentence(k, m)
            assert Q.gate(st, ws)["ok"], (k, m)
            assert Q.side(st, ws) == strip_side(k, m)
            assert strip_void(k, m) == L * L - Q2(strip_count(k, m))
    print("control 7 — the strip rule's side, count and void agree with the built "
          "sentence and its exact bbox for k in {2,3,5}, m in {1,2,4}")

    # 8. the lift is exact on a decimalised sentence and refuses a broken one
    st, ws, L = strip_sentence(2, 1)
    dec = [(Q2(F(f"{float(x):.12f}")), Q2(F(f"{float(y):.12f}"))) for x, y in st]
    got = Q.lift_sentence(dec, ws)
    assert got["status"] == "lifted" and got["L"] == L
    bad = list(dec)
    bad[-1] = (dec[-1][0] + Q2(F(3, 1000)), dec[-1][1])
    assert Q.lift_sentence(bad, ws)["status"] != "lifted"
    print("control 8 — the lift recovers the strip's exact side from 12-dp decimals "
          "and refuses a 3e-3 perturbation")

    print(f"selftest: OK ({checks + 7} controls)")
    return 0


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    if "--lift" in sys.argv:
        budget = 170.0
        if "--budget" in sys.argv:
            budget = float(sys.argv[sys.argv.index("--budget") + 1])
        uplift(budget=budget)
        return 0
    SQ.guard(quiet=True)
    print("run 84 — mixed_field.py: the lift, the exact carrier, and the seam rules")
    print(f"scorer guard: {SQ.summarise(SQ.load())['score']:.9f}, no row changes\n")
    ledger = {"run": 84, "instrument": "mixed_field.py + qsqrt2.py"}
    phase1(ledger)
    phase2(ledger)
    phase3(ledger)
    phase_seam(ledger)
    census(ledger)
    if os.path.exists(LIFT_LEDGER):
        with open(LIFT_LEDGER) as f:
            ledger["uplift"] = json.load(f)
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, "w") as f:
        json.dump(ledger, f, indent=1)
    print(f"\nledger: {os.path.relpath(LEDGER, ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
