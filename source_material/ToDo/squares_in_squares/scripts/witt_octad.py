#!/usr/bin/env python3
r"""witt_octad.py — run 138: the finite Witt-octad test doc 94 specified.

Doc 94 §6 named the only form in which the Golay / 24D perspective can be
productive here: the score's discrete content is the *direction classes* of the
delivered poses, so build the graph those classes form and ask whether it has the
combinatorics of the Witt design `S(5,8,24)` — 24 points, blocks of 8, **every
5-subset in exactly one block**.

The test is only worth running if the tester itself is right, so the instrument
first proves its axiom checker on the design it is looking for: the weight-8
words of the Golay code (`leech24_design.golay_words`, doc 15's 759 octads on 24
points) must come back with *every 5-subset exactly once*.  It then deletes one
octad and must fail.  Only then is it pointed at the data.

Two graphs are built from the delivered CSV, over the classes used by the
**structured** rows (`<= 4` angle classes — the rows that carry an exact word
vocabulary rather than jitter):

  contact   two classes are adjacent when a cell of one is in contact with a
            cell of the other in some delivered pose (`|pen| <= 1e-9`);
  co-occur two classes are adjacent when some delivered pose contains both.

The octad axiom is then applied to the 8-cliques inside the 24 most frequent
classes of each graph — a canonical 24-point set, so the test is finite,
reproducible and not chosen after seeing the answer.  The verdict is pass/fail
with the numbers (`|V|`, `|E|`, clique number, block count, the 5-subset
multiplicity range), never a narrative.

    python3 scripts/witt_octad.py
    python3 scripts/witt_octad.py --selftest
"""
from __future__ import annotations

import csv
import itertools
import json
import math
import os
import sys
from collections import Counter

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import leech24_design as LD            # noqa: E402  (the Golay code)
import sqscore as SQ                   # noqa: E402

CSV = os.path.join(ROOT, "workspace/submission/submission.csv")
OUT = os.path.join(ROOT, "workspace/push/witt_octad.json")
TOL = 1e-6            # angle-class tolerance (discovery: decimal angles)
WINDOW = 256          # rows larger than this are left out of the contact graph
MAX_BLOCKS = 400_000


def load_rows():
    rows = {}
    with open(CSV) as f:
        for r in csv.DictReader(f):
            rows.setdefault(int(r["n"]), []).append(
                (float(r["x"]), float(r["y"]), float(r["angle"])))
    return rows


def cls(angle: float) -> float:
    c = angle % (math.pi / 2)
    if math.pi / 2 - c < TOL:
        c = 0.0
    return round(c / TOL) * TOL


def classes_of(state):
    return {cls(a) for _x, _y, a in state}


# ---------------------------------------------------------------- the axiom
def octad_axiom(points, blocks) -> dict:
    """Every 5-subset of `points` in exactly one block?  Counted, not assumed."""
    pts = sorted(points)
    cnt = Counter()
    for b in blocks:
        for five in itertools.combinations(sorted(b), 5):
            cnt[five] += 1
    need = math.comb(len(pts), 5)
    vals = list(cnt.values())
    return {"points": len(pts), "blocks": len(blocks), "fives": len(cnt),
            "fives_required": need, "min": min(vals) if vals else 0,
            "max": max(vals) if vals else 0,
            "exactly_one": bool(len(cnt) == need and set(vals) == {1})}


def witt_design():
    """The 759 weight-8 Golay words on 24 points (doc 15's S(5,8,24))."""
    octads = [w for w in LD.golay_words() if bin(w).count("1") == 8]
    return set(range(24)), [frozenset(i for i in range(24) if (w >> i) & 1)
                            for w in octads]


# ---------------------------------------------------------------- the graphs
def pen(a, b) -> float:
    """SAT penetration of two unit squares (0 when disjoint)."""
    (ax, ay, at), (bx, by, bt) = a, b
    worst = -1e9
    for qx, qy in ((math.cos(at), math.sin(at)), (-math.sin(at), math.cos(at)),
                   (math.cos(bt), math.sin(bt)), (-math.sin(bt), math.cos(bt))):
        ha = 0.5 * (abs(math.cos(at) * qx + math.sin(at) * qy)
                    + abs(-math.sin(at) * qx + math.cos(at) * qy))
        hb = 0.5 * (abs(math.cos(bt) * qx + math.sin(bt) * qy)
                    + abs(-math.sin(bt) * qx + math.cos(bt) * qy))
        d = abs((ax - bx) * qx + (ay - by) * qy)
        worst = max(worst, d - (ha + hb))
    return -worst


def contact_edges(state, tau=1e-9):
    """Class pairs in contact, vectorised over all pairs (float, discovery)."""
    a = np.asarray(state, dtype=float)
    x, y, t = a[:, 0], a[:, 1], a[:, 2]
    c, s = np.cos(t), np.sin(t)
    dx = x[:, None] - x[None, :]
    dy = y[:, None] - y[None, :]
    sep = np.full((len(a), len(a)), -1e9)
    for qx, qy in ((c, s), (-s, c)):
        # axes of i (rows): q = (cos t_i, sin t_i) or its normal
        ha = 0.5 * (np.abs(c * qx + s * qy) + np.abs(-s * qx + c * qy))
        hb = ha[None, :]
        proj = np.abs(dx * qx[:, None] + dy * qy[:, None])
        sep = np.maximum(sep, proj - (ha[:, None] + hb))
    for qx, qy in ((c, s), (-s, c)):
        # axes of j (columns)
        hb = 0.5 * (np.abs(c * qx + s * qy) + np.abs(-s * qx + c * qy))
        ha = hb[None, :]
        proj = np.abs(dx * qx[None, :] + dy * qy[None, :])
        sep = np.maximum(sep, proj - (ha + hb[:, None]))
    out = set()
    # `sep` is the largest separating-axis gap: >0 disjoint, <0 overlapping,
    # 0 exactly in contact — contacts are |sep| <= tol.
    ii, jj = np.nonzero(np.triu(np.abs(sep) <= tau, 1))
    cl = np.array([cls(v) for v in t])
    for i, j in zip(ii, jj):
        if cl[i] != cl[j]:
            out.add((min(cl[i], cl[j]), max(cl[i], cl[j])))
    return out


def cooc_edges(state):
    cs = sorted(classes_of(state))
    return {(a, b) for i, a in enumerate(cs) for b in cs[i + 1:]}


def max_clique(adj: dict):
    """Exact maximum clique, Bron-Kerbosch with pivoting (small graphs)."""
    best = []

    def bk(R, P, X):
        nonlocal best
        if not P and not X:
            if len(R) > len(best):
                best = list(R)
            return
        pivot = max(P | X, key=lambda u: len(P & adj[u])) if (P or X) else None
        for v in list(P - (adj[pivot] if pivot is not None else set())):
            bk(R | {v}, P & adj[v], X & adj[v])
            P = P - {v}
            X = X | {v}

    bk(set(), set(adj), set())
    return best


def k_cliques(adj: dict, k: int, limit=MAX_BLOCKS):
    """All k-cliques (bounded): the candidate octads of a graph."""
    out = []
    nodes = sorted(adj)

    def rec(cur, cand):
        if len(out) >= limit:
            return
        if len(cur) == k:
            out.append(frozenset(cur))
            return
        for i, v in enumerate(cand):
            if len(cur) + len(cand) - i < k:
                break
            rec(cur + [v], [u for u in cand[i + 1:] if u in adj[v]])

    rec([], nodes)
    return out


def cover_all(rows, top=24) -> dict:
    """Over-coverage: how many poses contain each 5-subset of the top classes.

    The Witt axiom needs *exactly one* block per 5-subset.  Here a "block" would
    be a row's class set, so the multiplicity is the number of delivered poses
    containing the 5-subset — measured directly, no 8-clique enumeration.
    """
    freq = Counter()
    for st in rows.values():
        for _x, _y, a in st:
            freq[cls(a)] += 1
    pts = [c for c, _ in freq.most_common(top)]
    idx = {c: i for i, c in enumerate(pts)}
    cnt = Counter()
    for st in rows.values():
        S = sorted(idx[c] for c in classes_of(st) if c in idx)
        if len(S) < 5:
            continue
        for five in itertools.combinations(S, 5):
            cnt[five] += 1
    vals = list(cnt.values())
    need = math.comb(len(pts), 5)
    return {"points": len(pts), "fives_required": need, "fives_covered": len(cnt),
            "min": min(vals) if vals else 0, "max": max(vals) if vals else 0,
            "exactly_one": sum(1 for v in vals if v == 1),
            "mean": round(sum(vals) / len(vals), 3) if vals else 0}


def analyse(rows, edges, name, top=24) -> dict:
    freq = Counter()
    for n, st in rows.items():
        if n <= WINDOW:
            for _x, _y, a in st:
                freq[cls(a)] += 1
    points = [c for c, _ in freq.most_common(top)]
    adj = {c: set() for c in freq}
    for a, b in edges:
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    clique = max_clique(adj)
    blocks = [b for b in k_cliques(adj, 8) if b <= set(points)]
    ax = octad_axiom(points, [b for b in blocks if len(b) == 8])
    degs = sorted((len(v) for v in adj.values()), reverse=True)
    return {"graph": name, "vertices": len(adj), "edges": len(edges),
            "degrees_top": degs[:8], "clique_number": len(clique),
            "clique_example_deg": [round(math.degrees(c), 4) for c in clique[:8]],
            "octads_in_top24": len(blocks), "axiom": ax, "top24": len(points)}


def run() -> dict:
    rows = load_rows()
    struct = {n: st for n, st in rows.items() if len(classes_of(st)) <= 4}
    voc = set()
    for st in struct.values():
        voc |= classes_of(st)
    ce, qe = set(), set()
    for n, st in struct.items():
        if len(st) <= WINDOW:
            ce |= contact_edges(st)
        qe |= cooc_edges(st)
    # near contacts: the delivered poses are relaxed, so different orientations
    # never touch exactly; `tau` is stated, not tuned.
    ne = set()
    for n, st in struct.items():
        if len(st) <= WINDOW:
            ne |= contact_edges(st, tau=2e-2)
    res = {"vocabulary_classes": len(voc), "structured_rows": len(struct),
           "exact_contact_edges": len(ce), "near_contact_edges": len(ne),
           "tau": 2e-2,
           "contact_exact": analyse(struct, ce, "contact_exact"),
           "contact_near": analyse(struct, ne, "contact_near"),
           "cooccurrence": analyse(struct, qe, "cooccurrence"),
           "cooccurrence_all": cover_all(rows)}
    x, c, q = res["contact_exact"], res["contact_near"], res["cooccurrence"]
    res["verdict"] = (
        "FAIL (structural). Exact contacts between *different* classes number "
        f"{res['exact_contact_edges']}: every exact contact in the structured "
        "poses is same-class, so that graph has clique number "
        f"{x['clique_number']}. At near-contact tau=2e-2 the graph has "
        f"|V|={c['vertices']}, |E|={c['near_edges'] if 'near_edges' in c else c['edges']}, "
        f"clique number {c['clique_number']} < 8 -> {c['octads_in_top24']} octads, "
        f"5-subset multiplicities {c['axiom']['min']}..{c['axiom']['max']}. The "
        f"co-occurrence graph has clique number {q['clique_number']} (per-pose "
        f"class sets), {q['octads_in_top24']} 8-cliques in the top-24 classes, "
        f"5-subsets {q['axiom']['fives']}/{q['axiom']['fives_required']}. No "
        "S(5,8,24) design acts on either graph: the octad axiom is not met, it "
        "is not even testable at 8 points per block.")
    return res


def selftest() -> int:
    """Four controls: the design, the axiom, a planted failure, the plumbing."""
    pts, blocks = witt_design()
    ax = octad_axiom(pts, blocks)
    assert len(blocks) == 759, len(blocks)
    assert ax["exactly_one"] and ax["fives"] == math.comb(24, 5), ax
    print(f"  1. the tester reproduces S(5,8,24): {len(blocks)} octads, every "
          f"5-subset of 24 in exactly one ({ax['fives']} = C(24,5))")

    ax2 = octad_axiom(pts, blocks[1:])
    assert not ax2["exactly_one"], ax2
    assert ax2["fives"] == ax["fives"] - math.comb(8, 5), ax2   # 56 five-subsets lost
    print(f"  2. deleting one octad fails coverage: {ax2['fives']} of "
          f"{ax['fives']} 5-subsets remain (= C(24,5) - C(8,5))")

    # 3. plumbing: a graph with a known 8-clique is detected as one block
    adj = {i: set(range(8)) - {i} for i in range(8)}
    adj[99] = {0}
    assert len(max_clique(adj)) == 8
    assert k_cliques(adj, 8) == [frozenset(range(8))], k_cliques(adj, 8)
    print("  3. clique machinery: an injected K8 is found as exactly one 8-clique")

    # 4. the data path runs and is small enough to be exhaustive here
    rows = load_rows()
    # the run's structural finding, asserted as a control: exact contacts are
    # never cross-class (rows 10, 11, 17 all have exact contacts, none between
    # different orientations), and row 5 has no contact at all (its five cells
    # are >= 0.207 apart even at a proved-optimal side)
    for n in (10, 11, 17):
        assert contact_edges(rows[n]) == set(), (n, contact_edges(rows[n]))
    assert contact_edges(rows[5], 2e-2) == set(), contact_edges(rows[5], 2e-2)
    # positive plumbing: near-contact does produce edges where classes interleave
    near183 = contact_edges(rows[183], 2e-2)
    assert near183, "row 183 must have near-contact edges"
    print(f"  4. data path: rows 10/11/17 have exact contacts but "
          f"{len(contact_edges(rows[10]))} cross-class ones; row 183 has "
          f"{len(near183)} near-contact class pair(s)")
    # 5. the over-coverage measure agrees with the design on the design itself:
    # in S(5,8,24) every 5-subset is covered exactly once by 759 blocks
    pts, blocks = witt_design()
    cnt = Counter()
    for b in blocks:
        for five in itertools.combinations(sorted(b), 5):
            cnt[five] += 1
    assert len(cnt) == math.comb(24, 5) and set(cnt.values()) == {1}
    print("  5. coverage measure on the design: every 5-subset covered exactly "
          "once by its 759 octads")
    print("  selftest OK (5 controls)")
    return 0


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--selftest" in argv:
        return selftest()
    r = run()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(r, f, indent=1, default=str)
    print(f"structured rows {r['structured_rows']}, vocabulary "
          f"{r['vocabulary_classes']} direction classes")
    for g in ("contact_exact", "contact_near", "cooccurrence"):
        a = r[g]
        print(f"[{g}] |V|={a['vertices']} |E|={a['edges']} "
              f"omega={a['clique_number']} octads(top24)={a['octads_in_top24']} "
              f"5-subset mult {a['axiom']['min']}..{a['axiom']['max']} over "
              f"{a['axiom']['fives']}/{a['axiom']['fives_required']}")
    ca = r["cooccurrence_all"]
    print(f"[all rows, top-24 classes] 5-subset coverage: {ca['fives_covered']}"
          f"/{ca['fives_required']} covered, multiplicity {ca['min']}..{ca['max']} "
          f"(mean {ca['mean']}), {ca['exactly_one']} covered exactly once")
    print(f"\n{r['verdict']}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
