#!/usr/bin/env python3
r"""leech_comb.py — combinatorial address (tilt + contact graph) and the rigidity
class of that contact graph (Maxwell/Laman).

WHY.  Run 45 (`leech_map.py`, `16-LEECH-MAP.md`) closed the metric address: the
Lambda24 legality predicate is an integrality condition, and over 255 rows the
crosstab was perfect -- every row containing a 45-degree square is illegal at
every scale, every row without one is legal somewhere.  Since the tilted rows are
exactly the rows that beat the grid, the lattice cannot address the geometry that
scores.  The one bit the design *can* see is the tilt bit.  This module builds the
address that is left, and tests it; run 48 adds the rigidity class of the graph.

THE ADDRESS.  For a packing of n unit squares:

    tilt_i  in {0, 1}          one bit per square
    G       = contact graph    nodes = squares, edge iff the pair is touching
                               (penetration within tol of 0, using the project's
                               own SAT gate `packlib.verify` on the pair)

    address(packing) = (WL-signature(tilt-coloured G), |E(G)|)

where the WL signature is 1-dimensional Weisfeiler-Leman colour refinement started
from the tilt bit, returned as the sorted multiset of final colours.  That is
invariant under relabelling the squares, invariant under the container's D4
symmetry (canonicalised over the 8 maps of the bounding box), discrete,
scale-free, exact, and complete for the *combinatorial* part of a packing.

It is not a complete isomorphism-invariant (WL does not decide graph
isomorphism), and it does not see geometry.

THE RIGIDITY CLASS (run 48).  Run 47 left one hypothesis: the side length is fixed
not by the contact *graph* but by how much of that graph is rigid.  `rigidity`
computes the Maxwell count in both bookkeepings:

    Laman     |E| vs 2n - 3    a segment contact is one bar between two centres,
                               2 DOF per square -- the count that is justified
                               for axis-aligned contacts (and what run 47 named)
    body-bar  |E| vs 3n - 3    a square is a free rigid body, 3 DOF

A count is only an average over subsets, so the class comes from the exact
sparsity rank: `sparsity_rank` is a matroid greedy for (k, l)-sparsity, giving

    mechanisms = 2n - 3 - rank    internal DOF the contacts leave free
    redundant  = |E| - rank       contacts beyond the independent ones
    cls        = (mechanisms, redundant)

The greedy is exact because (k, l)-sparsity with l <= 2k-1 is a matroid, and the
selftest cross-checks the rank against brute-force enumeration of edge subsets.
Wall bars (`wall_bars`) are the flush container contacts, under the same
segment-not-corner rule; the grounded (2, 0) rank then says whether the packing is
*pinned*.  That distinction is real and not cosmetic: the 2x2 grid's contact graph
is a 4-cycle with one mechanism, so the walls are what hold a grid together.

THE TEST.  During the delivered table there is one row per n, so conditioning on
n leaves no variance at all -- the conditional test has to run on an ensemble.
`explain` builds one per n from random sequential placement (a loose box, then
shrink to the bounding box, so L varies) and from sub-packings of bigger delivered
rows, scores it with `packlib.verify`, and reports

    conditional R^2 = 1 - SS_within(base, class) / SS_between(base)

with a permutation null (class labels shuffled inside each base cell).  R^2 is
reported for the address, its ingredients, the rigidity class, and -- the run-47
question -- for the rigidity class *inside* an address class, which is exactly the
part of the 0.42 side-length spread the address leaves unexplained.

Usage:
    python3 scripts/leech_comb.py            # selftest + explain, write ledger
    python3 scripts/leech_comb.py --quick    # selftest only
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "workspace/push/leech_comb.json")
sys.path.insert(0, HERE)
import packlib  # noqa: E402
import sqscore  # noqa: E402

CONTACT_TOL = 1e-6         # |penetration| below this counts as touching
ROUND = 1e-6               # grid used for the D4 canonical form


# ------------------------------------------------------------------ address
def tilt_bits(state) -> tuple[int, ...]:
    return tuple(1 if abs(math.sin(2 * float(s[2]))) > 0.5 else 0 for s in state)


def axis_penetrations(state, i, j):
    """The four SAT penetrations of the pair (i, j), one per axis.

    Same formula as `packlib.verify`, evaluated on one pair so that the two axes
    of each square are visible separately.  The selftest checks that their
    minimum equals the gate's `worst_pen` for random pairs, so this is a refined
    view of the gate, not a second implementation of it.
    """
    xi, yi, ti = (float(v) for v in state[i])
    xj, yj, tj = (float(v) for v in state[j])
    ci, si = math.cos(ti), math.sin(ti)
    cj, sj = math.cos(tj), math.sin(tj)
    dx, dy = xi - xj, yi - yj
    # extent of j along i's axes, and of i along j's axes
    e_ij = 0.5 * (abs(ci * cj + si * sj) + abs(-si * cj + ci * sj))
    e_ji = 0.5 * (abs(cj * ci + sj * si) + abs(-sj * ci + cj * si))
    out = []
    for cs, sn, e in ((ci, si, e_ij), (cj, sj, e_ji)):
        out.append(0.5 + e - abs(dx * cs + dy * sn))
        out.append(0.5 + e - abs(-dx * sn + dy * cs))
    return out


def contacts(state, tol: float = CONTACT_TOL):
    """Segment contacts: touching on one axis while overlapping on the other.

    A corner touch (every axis exactly 0) is a measure-zero contact that cannot
    carry a rigidity constraint, so it is not an edge.  That distinction is what
    makes the 2x2 grid a 4-cycle rather than K4, and it is checked in the
    selftest against both grids.
    """
    n = len(state)
    adj = [set() for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            pen = axis_penetrations(state, i, j)
            touching = -tol <= min(pen) <= tol
            if touching and max(pen) > tol:
                adj[i].add(j)
                adj[j].add(i)
    return [sorted(a) for a in adj]


def bbox(state):
    """Bounding box (lox, loy, width, height) from the per-square extents."""
    ex = [0.5 * (abs(math.cos(float(s[2]))) + abs(math.sin(float(s[2]))))
          for s in state]
    lox = min(s[0] - e for s, e in zip(state, ex))
    loy = min(s[1] - e for s, e in zip(state, ex))
    hix = max(s[0] + e for s, e in zip(state, ex))
    hiy = max(s[1] + e for s, e in zip(state, ex))
    return lox, loy, hix - lox, hiy - loy


def wall_bars(state, bits=None, tol: float = CONTACT_TOL):
    """Container contacts that are segments: flush side, axis-aligned square.

    The container is the packing's own bounding box, so a bar exists on a side
    whenever the square reaching that side is axis-aligned.  A 45-degree square
    reaches the wall at a single corner, exactly the measure-zero contact the
    graph excludes, so it contributes no bar.  Returns [(square, side), ...].
    """
    bits = tilt_bits(state) if bits is None else bits
    lox, loy, w, h = bbox(state)
    out = []
    for i, s in enumerate(state):
        if bits[i]:
            continue
        x, y = float(s[0]), float(s[1])
        e = 0.5 * (abs(math.cos(float(s[2]))) + abs(math.sin(float(s[2]))))
        if x - e <= lox + tol:
            out.append((i, "L"))
        if x + e >= lox + w - tol:
            out.append((i, "R"))
        if y - e <= loy + tol:
            out.append((i, "B"))
        if y + e >= loy + h - tol:
            out.append((i, "T"))
    return out


def d4_images(state):
    """The 8 images of the packing under the symmetries of its bounding box.

    Every image is expressed in the same gauge (bbox origin at (lox, loy)) and
    fits in the box, so no re-normalisation is needed and no image can drift.
    """
    lox, loy, w, h = bbox(state)
    bits = tilt_bits(state)
    pts = [(s[0] - lox, s[1] - loy, bits[i]) for i, s in enumerate(state)]
    out = []
    for swap in (False, True):
        amax, bmax = (h, w) if swap else (w, h)
        for fx in (False, True):
            for fy in (False, True):
                img = []
                for x, y, t in pts:
                    a, b = (y, x) if swap else (x, y)
                    if fx:
                        a = amax - a
                    if fy:
                        b = bmax - b
                    img.append((a + lox, b + loy, t))
                out.append(img)
    return out


def canonical_set(state, tol: float = ROUND):
    """D4-canonical form of the rounded centre set (translation gauged out)."""
    best = None
    for img in d4_images(state):
        key = tuple(sorted((round(x / tol) * tol, round(y / tol) * tol, t)
                           for x, y, t in img))
        if best is None or key < best:
            best = key
    return best


def wl_signature(adj, bits, rounds=None):
    """1-WL colour refinement from the tilt bit; sorted colour multiset."""
    n = len(adj)
    colours = [(b,) for b in bits]
    for _ in range(rounds if rounds is not None else n):
        sig = [(colours[i], tuple(sorted(colours[j] for j in adj[i])))
               for i in range(n)]
        rank = {s: r for r, s in enumerate(sorted(set(sig), key=repr))}
        new = [(rank[s],) for s in sig]
        if len(set(new)) == len(set(colours)):
            return tuple(sorted(new))
        colours = new
    return tuple(sorted(colours))


def address_of(bits, adj) -> tuple:
    """The address from a tilt pattern and a contact graph (no recomputation)."""
    return (wl_signature(adj, bits), sum(len(a) for a in adj) // 2)


def address(state) -> tuple:
    """The combinatorial address: WL signature of the tilt-coloured contact graph."""
    return address_of(tilt_bits(state), contacts(state))


def degree_sequence(state):
    return tuple(sorted((len(a) for a in contacts(state)), reverse=True))


def tilt_pattern(state):
    return tuple(sorted(tilt_bits(state)))


# ------------------------------------------------------------------ rigidity
def sparsity_rank(n, cons, k=2, l=3) -> int:
    """Exact size of a maximum (k, l)-sparse subset of the constraints `cons`.

    A constraint is a bitmask over the n squares: a segment contact is a pair, a
    flush wall is a single square.  (k, l)-sparsity asks |C(S)| <= k|S| - l for
    every S with a non-negative bound, and for l <= 2k-1 that family is a matroid,
    so adding every constraint that keeps the set sparse is exact (the selftest
    checks the rank against brute-force enumeration on small graphs).
    """
    full = (1 << n) - 1
    pc = [bin(m).count("1") for m in range(full + 1)]
    count = [0] * (full + 1)
    rank = 0
    for mask in cons:
        rest = full & ~mask
        ok = True
        s = rest
        while True:
            S = s | mask
            if count[S] + 1 > k * pc[S] - l:
                ok = False
                break
            if not s:
                break
            s = (s - 1) & rest
        if not ok:
            continue
        s = rest
        while True:
            count[s | mask] += 1
            if not s:
                break
            s = (s - 1) & rest
        rank += 1
    return rank


def sparsity_violations(n, cons, k=2, l=3):
    """Worst (k, l)-sparsity violation of a constraint set, or None if sparse."""
    full = (1 << n) - 1
    worst = None
    for S in range(1, full + 1):
        bound = k * bin(S).count("1") - l
        if bound < 0:
            continue
        c = sum(1 for m in cons if m & ~S == 0)
        if c > bound and (worst is None or c - bound > worst[0]):
            worst = (c - bound, S, c, bound)
    return worst


def tightest_cluster(n, cons, k=2, l=3, min_size=3):
    """The cluster closest to -- or past -- tightness.

    Returns (excess, S, |E(S)|, |S|) maximising |E(S)| - (2|S| - 3) over clusters
    of at least `min_size` squares, plus the same maximum per cluster size.  This
    is the headroom a *cluster* has before it is Laman-tight: 0 is tight, positive
    is redundant, negative is the gap.  Subsets of one or two squares are excluded
    because 2|S| - 3 is trivial there.
    """
    full = (1 << n) - 1
    pc = [bin(m).count("1") for m in range(full + 1)]
    best = None
    by_size: dict[int, int] = {}
    for S in range(1, full + 1):
        sz = pc[S]
        if sz < min_size:
            continue
        c = sum(1 for m in cons if m & ~S == 0)
        excess = c - (k * sz - l)
        if best is None or excess > best[0]:
            best = (excess, S, c, sz)
        if sz not in by_size or excess > by_size[sz]:
            by_size[sz] = excess
    return best + (by_size,)


def rigidity(state, bits=None, adj=None) -> dict:
    """Maxwell/Laman class of the contact graph, exactly.

    `bits`/`adj` may be passed in when the caller already has them.  The Laman
    count (2n - 3) is the one that applies when a segment contact acts as a bar
    between two square centres, which fixes the orientation of axis-aligned
    squares; the body-bar count (3n - 3) treats every square as a free rigid body.
    At 45 degrees the contact normal is not generic, so either count is a generic
    necessary condition, not a proof of rigidity at the configuration.
    """
    bits = tilt_bits(state) if bits is None else bits
    adj = contacts(state) if adj is None else adj
    n = len(state)
    pair_cons = [(1 << i) | (1 << j) for i in range(n) for j in adj[i] if i < j]
    m = len(pair_cons)
    wall_cons = [1 << i for i, _ in wall_bars(state, bits)]
    w = len(wall_cons)
    rank_l = sparsity_rank(n, pair_cons, 2, 3)
    rank_g = sparsity_rank(n, pair_cons + wall_cons, 2, 0)
    mech = 2 * n - 3 - rank_l
    red = m - rank_l
    return {
        "n": n, "m": m, "w": w, "tilted": sum(bits),
        "laman": m - (2 * n - 3), "body_bar": m - (3 * n - 3),
        "rank_laman": rank_l, "mechanisms": mech, "redundant": red,
        "rigid_free": rank_l == 2 * n - 3,
        "rank_ground": rank_g, "pinned": rank_g == 2 * n,
        "ground_def": m + w - 2 * n,
        "cls": (mech, red),
        "coarse": ("isostatic" if mech == 0 and red == 0
                   else "stressed" if mech == 0 else "mechanism"),
    }


# ------------------------------------------------------------------ statistics
def _key(r, base_keys):
    return tuple(r[k] for k in base_keys)


def ss_within(rows, base_keys=("n",), field=None) -> float:
    """Sum of squared deviations inside each cell, splitting on `field` if given."""
    cells: dict[tuple, list[float]] = {}
    for r in rows:
        k = _key(r, base_keys) + ((r[field],) if field else ())
        cells.setdefault(k, []).append(r["y"])
    tot = 0.0
    for v in cells.values():
        mu = sum(v) / len(v)
        tot += sum((x - mu) ** 2 for x in v)
    return tot


def conditional_r2(rows, base_keys=("n",), field="addr") -> float | None:
    """1 - SS_within(base, field) / SS_between(base).

    Returns None when the baseline has no variance above round-off: rows that all
    sit at the same side length differ by ~1e-30 in SS, and the ratio of two such
    numbers is noise -- it reads as +0.5000 and means nothing.
    """
    ys = [r["y"] for r in rows]
    scale = max((abs(v) for v in ys), default=0.0)
    ss_tot = ss_within(rows, base_keys)
    if ss_tot <= (1e-12 * scale) ** 2 * max(len(ys), 1):
        return None
    return 1.0 - ss_within(rows, base_keys, field) / ss_tot


def permutation_null(rows, base_keys=("n",), field="addr", draws=200, seed=20261118):
    """Shuffle `field` inside each baseline cell, keeping class sizes."""
    rng = random.Random(seed)
    by_base: dict[tuple, list[int]] = {}
    for i, r in enumerate(rows):
        by_base.setdefault(_key(r, base_keys), []).append(i)
    out = []
    for _ in range(draws):
        shuffled = [dict(r) for r in rows]
        for idx in by_base.values():
            vals = [rows[i][field] for i in idx]
            rng.shuffle(vals)
            for i, v in zip(idx, vals):
                shuffled[i][field] = v
        v = conditional_r2(shuffled, base_keys=base_keys, field=field)
        if v is not None:
            out.append(v)
    return out


def _null_summary(vals, observed):
    if not vals:
        return {"mean": None, "max": None, "exceeding": None, "draws": 0}
    return {"mean": sum(vals) / len(vals), "max": max(vals), "draws": len(vals),
            "exceeding": (sum(1 for v in vals if observed is not None and v >= observed)
                          if observed is not None else None)}


# ------------------------------------------------------------------ ensembles
def random_packing(n, side, rng, tries=600):
    """Random sequential placement in a square of side `side`, then shrink."""
    lo, hi = 0.71, side - 0.71
    if hi <= lo:
        return None
    placed = []
    while len(placed) < n and tries > 0:
        tries -= 1
        x, y = rng.uniform(lo, hi), rng.uniform(lo, hi)
        t = 0.0 if rng.random() < 0.65 else math.pi / 4
        cand = placed + [(x, y, t)]
        if packlib.verify(cand)["worst_pen"] <= -1e-9:
            placed = cand
    if len(placed) < n:
        return None
    st, r = packlib.finalize(placed)
    return st if r["ok"] and r["worst_pen"] <= -1e-12 else None


def delivered_counts(store, nmax=40, rank_nmax=12):
    """Maxwell/Laman count on the delivered rows themselves.

    The exact sparsity rank is exponential in n, so it is computed only where it
    is reachable (n <= rank_nmax); above that the count m vs 2n - 3 stands alone.
    """
    out = []
    for n in sorted(store):
        if n > nmax:
            break
        st = store[n]
        if len(st) != n:
            continue
        bits, adj = tilt_bits(st), contacts(st)
        m = sum(len(a) for a in adj) // 2
        row = {"n": n, "m": m, "w": len(wall_bars(st, bits)), "tilted": sum(bits),
               "laman": m - (2 * n - 3), "body_bar": m - (3 * n - 3)}
        if n <= rank_nmax:
            rig = rigidity(st, bits, adj)
            row.update({"mechanisms": rig["mechanisms"],
                        "redundant": rig["redundant"], "pinned": rig["pinned"]})
        out.append(row)
    return {
        "rows": len(out), "n_max": out[-1]["n"] if out else None,
        "laman_tight": sum(1 for r in out if r["laman"] >= 0),
        "laman_min": min(r["laman"] for r in out),
        "laman_max": max(r["laman"] for r in out),
        "m_over_n_mean": sum(r["m"] / r["n"] for r in out) / len(out),
        "tilted_rows": sum(1 for r in out if r["tilted"]),
        "rank_nmax": rank_nmax, "table": out,
    }


def _drop_squares(st, k, mode="last"):
    """Delete k squares from a delivered row: the last k, or evenly spread."""
    m = len(st)
    if mode == "last":
        idx = set(range(m - k, m))
    else:
        idx = {round(i * (m - 1) / (k + 1)) for i in range(1, k + 1)}
    return [s for i, s in enumerate(st) if i not in idx]


def sub_packings(store, ns, extra=6):
    """Tight ensembles: delete src - n squares from a bigger delivered row.

    Run 49 fixes a real bug here.  The loop deleted exactly ONE square and then
    skipped every source with src > n + 1 (`len(cand) != n`), so two thirds of the
    source range was dead and every n produced a single side length -- the
    "two-level" ensemble of run 48.  With k = src - n deletions the family spans
    L = 3.0 .. 4.0 at each n and is contact-bearing throughout, which is the
    ensemble the rigidity test needed.
    """
    out = []
    for n in ns:
        for src in range(n + 1, n + 1 + extra):
            st = store.get(src)
            if not st:
                continue
            k = len(st) - n
            for mode in ("last", "spread"):
                cand = _drop_squares(st, k, mode)
                if len(cand) != n:
                    continue
                st2, r = packlib.finalize(cand)
                if r["ok"] and r["worst_pen"] <= -1e-12:
                    out.append((n, st2, f"sub{src}{mode[0]}"))
    return out


def build_ensemble(store, ns, factors=(1.15, 1.35, 1.55), trials=30, seed=20261118):
    rng = random.Random(seed)
    out = sub_packings(store, ns)
    for n in ns:
        for c in factors:
            for _ in range(trials):
                st = random_packing(n, c * math.sqrt(n), rng)
                if st is not None:
                    out.append((n, st, "rsa"))
    return out


def settled_packings(store, ns, seeds=2, slots=(0.0, 0.006, 0.02),
                     jitter=0.03, turn=0.25, seed=20261118):
    """Jammed rows: perturb a delivered row, then settle it at its own side.

    `oracle_basin.settle_to` minimises the W36 hinge at a fixed box, so the state
    it returns is held by the walls and by its own contacts.  Sequential placement
    cannot produce this: it only accepts squares that are already separated, so
    its rows have no contacts at all.  A small side ladder is tried per seed and
    the first feasible result is kept.
    """
    import oracle_basin
    out = []
    rng = random.Random(seed)
    for n in ns:
        st0 = store.get(n)
        if not st0 or len(st0) != n:
            continue
        L0 = packlib.verify(st0)["L"]
        for _ in range(seeds):
            pert = []
            for x, y, th in st0:
                t = th + rng.choice((-1.0, 1.0)) * math.pi / 4 \
                    if rng.random() < turn else th
                pert.append((x + rng.uniform(-jitter, jitter),
                             y + rng.uniform(-jitter, jitter), t))
            q = [p[0] for p in pert] + [p[1] for p in pert] + [p[2] for p in pert]
            for slot in slots:
                q2, _f = oracle_basin.settle_to(q, L0 * (1 + slot), iters=250,
                                                kicks=0)
                st = [(q2[i], q2[n + i], q2[2 * n + i]) for i in range(n)]
                st2, r = packlib.finalize(st)
                if r["ok"] and r["worst_pen"] <= -1e-12:
                    out.append((n, st2, f"set{100 * slot:.1f}"))
                    break
    return out


def random_sub_packings(store, ns, extra=(2, 3, 4, 6), seeds=6, seed=20261118):
    """Same source, different deletions: L variance inside one (n, source).

    Deleting a corner square shrinks the bounding box, deleting an interior one
    does not, so a random deletion set varies L *and* the contact graph while the
    rest of the packing keeps its contacts.  Without this the stratified test has
    no within-cell variance at all: one construction, one side length.
    """
    rng = random.Random(seed)
    out = []
    for n in ns:
        for k in extra:
            src = n + k
            st = store.get(src)
            if not st or len(st) != src:
                continue
            for _ in range(seeds):
                drop = set(rng.sample(range(len(st)), k))
                cand = [s for i, s in enumerate(st) if i not in drop]
                st2, r = packlib.finalize(cand)
                if r["ok"] and r["worst_pen"] <= -1e-12:
                    out.append((n, st2, f"rand{src}"))
    return out


def build_jammed_ensemble(store, ns):
    """Contact-bearing rows only: sub-packings, random deletions, settled rows."""
    rows = (sub_packings(store, ns) + random_sub_packings(store, ns)
            + settled_packings(store, ns))
    return [(n, st, src) for n, st, src in rows
            if sum(len(a) for a in contacts(st)) // 2 >= 1]


# ------------------------------------------------------------------ selftest
def selftest() -> dict:
    store = packlib.read_csv(os.path.join(ROOT, "workspace/submission/submission.csv"))
    checks = {}
    notes = {}

    def grid(k, L):
        return [((i + 0.5) * L / k, (j + 0.5) * L / k, 0.0)
                for i in range(k) for j in range(k)]

    # 1. relabelling the squares must not change the address
    st = store[7]
    shuffled = [st[i] for i in (3, 0, 6, 1, 5, 2, 4)]
    checks["address_permutation_invariant"] = address(st) == address(shuffled)

    # 2. the D4 of the bounding box must not change the canonical form
    base = canonical_set(st)
    checks["canonical_d4_invariant"] = all(canonical_set(img) == base
                                           for img in d4_images(st))

    # 3. the pair view must agree with the gate it refines
    rng0 = random.Random(3)
    agree = True
    for _ in range(200):
        a = (rng0.uniform(0, 3), rng0.uniform(0, 3), rng0.choice((0.0, math.pi / 4)))
        b = (rng0.uniform(0, 3), rng0.uniform(0, 3), rng0.choice((0.0, math.pi / 4)))
        agree &= abs(min(axis_penetrations([a, b], 0, 1))
                     - packlib.verify([a, b])["worst_pen"]) < 1e-12
    checks["pair_axes_match_gate"] = agree

    # 4. known contact graphs: the grids
    g2 = contacts(grid(2, 2.0))
    checks["grid2_is_a_4_cycle"] = (sorted(len(a) for a in g2) == [2, 2, 2, 2]
                                    and sum(len(a) for a in g2) // 2 == 4)
    g3 = contacts(grid(3, 3.0))
    checks["grid3_degrees"] = sorted(len(a) for a in g3) == [2] * 4 + [3] * 4 + [4]
    checks["grid3_edges_12"] = sum(len(a) for a in g3) // 2 == 12

    # 5. two different arrangements must not share an address
    stack = [(0.5, i + 0.5, 0.0) for i in range(3)] + [(1.5, i + 0.5, 0.0) for i in range(3)]
    row6 = [(i + 0.5, 0.5, 0.0) for i in range(6)]
    checks["distinct_shapes_distinct"] = address(stack) != address(row6)

    # 6. the sparsity rank must equal brute force on small graphs
    def brute(n, edges, k, l):
        best = 0
        for pick in range(1 << len(edges)):
            sub = [edges[i] for i in range(len(edges)) if pick >> i & 1]
            if len(sub) > best and sparsity_violations(n, sub, k, l) is None:
                best = len(sub)
        return best

    rng2 = random.Random(5)
    rank_ok = True
    for _ in range(12):
        n = 5
        edges = [(1 << i) | (1 << j) for i in range(n) for j in range(i + 1, n)
                 if rng2.random() < 0.5]
        rank_ok &= sparsity_rank(n, edges, 2, 3) == brute(n, edges, 2, 3)
    checks["sparsity_rank_matches_bruteforce"] = rank_ok

    # 7. known ranks: K4 is one bar over Laman-tight, C4 is one under
    k4 = [(1 << i) | (1 << j) for i in range(4) for j in range(i + 1, 4)]
    c4 = [(1 << i) | (1 << ((i + 1) % 4)) for i in range(4)]
    checks["rank_k4_is_5"] = sparsity_rank(4, k4, 2, 3) == 5
    checks["rank_c4_is_4"] = sparsity_rank(4, c4, 2, 3) == 4
    checks["k4_is_not_laman_sparse"] = sparsity_violations(4, k4, 2, 3) is not None

    # 8. grids: the graph alone has mechanisms, the container pins them
    rig2 = rigidity(grid(2, 2.0))
    checks["grid2_graph_has_one_mechanism"] = (rig2["m"] == 4
                                               and rig2["mechanisms"] == 1)
    checks["grid2_pinned_only_by_walls"] = rig2["pinned"] and not rig2["rigid_free"]
    rig3 = rigidity(grid(3, 3.0))
    notes["grid3"] = (f"m={rig3['m']} w={rig3['w']} mech={rig3['mechanisms']} "
                      f"red={rig3['redundant']} ground_rank={rig3['rank_ground']}")
    checks["grid3_pinned"] = rig3["pinned"]

    # 9. the n=5 delivered row: what is its combinatorics?
    st5 = store[5]
    bits5, adj5 = tilt_bits(st5), contacts(st5)
    notes["n5_tilt_bits"] = bits5
    notes["n5_degrees"] = tuple(sorted((len(a) for a in adj5), reverse=True))
    notes["n5_edges"] = sum(len(a) for a in adj5) // 2
    notes["n5_address"] = repr(address_of(bits5, adj5))
    notes["n5_rigidity"] = repr(rigidity(st5, bits5, adj5))

    # 9b. cluster tightness, and the sub family that supplies contact-bearing rows
    g3cons = [(1 << i) | (1 << j) for i in range(9) for j in g3[i] if i < j]
    tc = tightest_cluster(9, g3cons)

    def excess_bruteforce(adj, S):           # independent: adjacency lists, not masks
        verts = [i for i in range(len(adj)) if S >> i & 1]
        e = sum(1 for a in range(len(verts)) for b in range(a + 1, len(verts))
                if verts[b] in adj[verts[a]])
        return e - (2 * len(verts) - 3)

    best_bf = max(excess_bruteforce(g3, S) for S in range(1, 1 << 9)
                  if bin(S).count("1") >= 3)
    checks["grid3_tightest_cluster_is_minus_one"] = (tc[0] == best_bf == -1)
    subs = sub_packings(store, (7,))
    checks["sub_family_has_several_sides"] = len(
        {round(packlib.verify(s)["L"], 6) for _, s, _ in subs}) >= 3

    # 10. stability: a 1e-7 perturbation must not change the address
    rng = random.Random(7)
    stable = 0
    trials = 50
    for _ in range(trials):
        pert = [(x + rng.uniform(-1e-7, 1e-7), y + rng.uniform(-1e-7, 1e-7), t)
                for x, y, t in st5]
        if address(pert) == address_of(bits5, adj5):
            stable += 1
    notes["n5_stability"] = f"{stable}/{trials}"

    return {"checks": checks, "passed": sum(checks.values()),
            "total": len(checks), "notes": notes}


# ------------------------------------------------------------------ explain
def explain(ns=(5, 6, 7, 8, 9, 10), draws=200, jammed=False):
    t0 = time.time()
    store = packlib.read_csv(os.path.join(ROOT, "workspace/submission/submission.csv"))
    ens = build_jammed_ensemble(store, ns) if jammed else build_ensemble(store, ns)

    rows = []
    for n, st, src in ens:
        bits, adj = tilt_bits(st), contacts(st)
        rig = rigidity(st, bits, adj)
        cons = [(1 << i) | (1 << j) for i in range(n) for j in adj[i] if i < j]
        clust = tightest_cluster(n, cons)
        rows.append({
            "n": n, "src": src, "addr": address_of(bits, adj), "m": rig["m"],
            "w": rig["w"], "tilt": sum(bits), "rig": rig["cls"],
            "coarse": rig["coarse"], "pinned": rig["pinned"],
            "mech": rig["mechanisms"], "red": rig["redundant"],
            "cluster_excess": clust[0], "cluster_size": clust[3],
            "cluster_edges": clust[2], "cluster_profile": clust[4],
            "y": packlib.verify(st)["L"],
        })

    # the address, as in run 47
    r2_addr = conditional_r2(rows, field="addr")
    null_addr = _null_summary(permutation_null(rows, field="addr", draws=draws), r2_addr)
    r2_tilt = conditional_r2(rows, field="tilt")
    r2_edges = conditional_r2(rows, field="m")
    r2_strat = conditional_r2(rows, base_keys=("n", "src"), field="addr")
    null_strat = _null_summary(
        permutation_null(rows, ("n", "src"), "addr", draws), r2_strat)

    # the rigidity class
    r2_rig = conditional_r2(rows, field="rig")
    null_rig = _null_summary(permutation_null(rows, field="rig", draws=draws), r2_rig)
    r2_rig_strat = conditional_r2(rows, ("n", "src"), "rig")
    null_rig_strat = _null_summary(
        permutation_null(rows, ("n", "src"), "rig", draws), r2_rig_strat)
    # the run-47 question: what does the class explain inside an address class?
    r2_rig_in_addr = conditional_r2(rows, ("n", "addr"), "rig")
    null_rig_in_addr = _null_summary(
        permutation_null(rows, ("n", "addr"), "rig", draws), r2_rig_in_addr)
    r2_coarse_in_addr = conditional_r2(rows, ("n", "addr"), "coarse")
    r2_pinned_in_addr = conditional_r2(rows, ("n", "addr"), "pinned")
    # ... and is the class anything beyond |E|, which the address already carries?
    r2_rig_in_edges = conditional_r2(rows, ("n", "m"), "rig")

    # structure of the ensemble: where the class has room to vary at all
    per_nm: dict[tuple, set] = {}
    for r in rows:
        per_nm.setdefault((r["n"], r["m"]), set()).add(r["rig"])
    ss_addr = ss_within(rows, ("n",), "addr")
    mfree = [r for r in rows if r["m"] == 0]
    ss_addr_mfree = ss_within(mfree, ("n",), "addr") if len(mfree) > 1 else 0.0

    # rows that actually have contacts: the graph statistics' only domain
    mpos = [r for r in rows if r["m"] > 0]
    r2_addr_pos = conditional_r2(mpos, field="addr")
    r2_rig_in_addr_pos = conditional_r2(mpos, ("n", "addr"), "rig")
    null_rig_in_addr_pos = _null_summary(
        permutation_null(mpos, ("n", "addr"), "rig", draws), r2_rig_in_addr_pos)
    pos_classes: dict[tuple, list[dict]] = {}
    for r in mpos:
        pos_classes.setdefault((r["n"], r["addr"]), []).append(r)
    spreads_pos = [max(x["y"] for x in v) - min(x["y"] for x in v)
                   for v in pos_classes.values() if len(v) >= 2]

    # within-address spread of L, and what the rigidity class does to it
    by_addr: dict[tuple, list[dict]] = {}
    for r in rows:
        by_addr.setdefault((r["n"], r["addr"]), []).append(r)
    multi = [v for v in by_addr.values() if len(v) >= 2]
    spread_detail = []
    for v in multi:
        ys = [r["y"] for r in v]
        spread_detail.append({
            "n": v[0]["n"], "rows": len(v), "spread": max(ys) - min(ys),
            "L_range": [min(ys), max(ys)],
            "m_values": sorted({r["m"] for r in v}),
            "srcs": sorted({r["src"] for r in v}),
            "w_values": sorted({r["w"] for r in v}),
            "rig_classes": sorted({repr(r["rig"]) for r in v}),
            "pinned": sorted({r["pinned"] for r in v}),
        })
    spread_detail.sort(key=lambda d: -d["spread"])
    spreads = [d["spread"] for d in spread_detail]
    homog = [d["spread"] for d, v in zip(spread_detail, multi)
             if len({r["rig"] for r in v}) == 1]
    het = [d["spread"] for d, v in zip(spread_detail, multi)
           if len({r["rig"] for r in v}) > 1]

    # many address classes are singletons, where R^2 is trivially 1
    sizes: dict[tuple, int] = {}
    for r in rows:
        key = (r["n"], r["addr"])
        sizes[key] = sizes.get(key, 0) + 1
    multi_rows = [r for r in rows if sizes[(r["n"], r["addr"])] >= 2]
    r2_multi = conditional_r2(multi_rows) if len(multi_rows) >= 3 else None
    null_multi = _null_summary(
        permutation_null(multi_rows, draws=draws), r2_multi)
    r2_rig_multi = conditional_r2(multi_rows, ("n", "addr"), "rig")
    null_rig_multi = _null_summary(
        permutation_null(multi_rows, ("n", "addr"), "rig", draws), r2_rig_multi)

    # per-n table
    per_n: dict[int, dict] = {}
    for r in rows:
        d = per_n.setdefault(r["n"], {"rows": 0, "addrs": set(), "L": [],
                                      "mech": set(), "pinned": 0, "m": []})
        d["rows"] += 1
        d["addrs"].add(r["addr"])
        d["L"].append(r["y"])
        d["m"].append(r["m"])
        d["mech"].add(r["mech"])
        d["pinned"] += int(r["pinned"])
    table = []
    for n in sorted(per_n):
        d = per_n[n]
        slack = [sqscore.row_score(n, L) for L in d["L"]]
        st = store.get(n)
        hit = None
        if st is not None:
            a = address(st)
            hit = sum(1 for r in rows if r["n"] == n and r["addr"] == a)
        table.append({
            "n": n, "rows": d["rows"], "distinct_addresses": len(d["addrs"]),
            "L_min": min(d["L"]), "L_max": max(d["L"]),
            "slack_min": min(slack), "slack_max": max(slack),
            "mechanisms_seen": sorted(d["mech"]), "pinned_rows": d["pinned"],
            "m_mean": sum(d["m"]) / d["rows"], "m_range": [min(d["m"]), max(d["m"])],
            "delivered_address_seen": hit,
        })

    # stability of the ensemble addresses
    rng = random.Random(11)
    stable = total = 0
    for r, (n, st, _) in zip(rows[::10], ens[::10]):
        pert = [(x + rng.uniform(-1e-7, 1e-7), y + rng.uniform(-1e-7, 1e-7), t)
                for x, y, t in st]
        total += 1
        stable += int(address(pert) == r["addr"])

    # composition of the ensemble: how each source contributes |E| and L
    srcs: dict[tuple, dict] = {}
    for r in rows:
        d = srcs.setdefault((r["n"], r["src"]), {"rows": 0, "m_max": 0, "L": []})
        d["rows"] += 1
        d["m_max"] = max(d["m_max"], r["m"])
        d["L"].append(r["y"])
    source_summary = [{"n": k[0], "src": k[1], "rows": d["rows"],
                       "m_max": d["m_max"], "L_min": min(d["L"]),
                       "L_max": max(d["L"])}
                      for k, d in sorted(srcs.items())]

    return {
        "rows": len(rows), "n_values": sorted(per_n),
        "seconds": round(time.time() - t0, 2),
        "r2_address": r2_addr, "null_address": null_addr,
        "r2_tilt_only": r2_tilt, "r2_edges_only": r2_edges,
        "r2_stratified": r2_strat, "null_stratified": null_strat,
        "r2_multi": r2_multi, "null_multi": null_multi, "multi_rows": len(multi_rows),
        "r2_rigidity": r2_rig, "null_rigidity": null_rig,
        "r2_rigidity_stratified": r2_rig_strat, "null_rigidity_stratified": null_rig_strat,
        "r2_rigidity_in_address": r2_rig_in_addr,
        "null_rigidity_in_address": null_rig_in_addr,
        "r2_rigidity_in_multi_address": r2_rig_multi,
        "null_rigidity_in_multi_address": null_rig_multi,
        "r2_coarse_in_address": r2_coarse_in_addr,
        "r2_pinned_in_address": r2_pinned_in_addr,
        "r2_rigidity_in_edges": r2_rig_in_edges,
        "rows_contact_free": len(mfree),
        "rows_redundant": sum(1 for r in rows if r["red"] > 0),
        "rows_laman_tight": sum(1 for r in rows if r["mech"] == 0),
        "rows_pinned": sum(1 for r in rows if r["pinned"]),
        "mech_max": max(r["mech"] for r in rows),
        "m_per_n_mean": sum(r["m"] / r["n"] for r in rows) / len(rows),
        "laman_min": min(r["m"] - (2 * r["n"] - 3) for r in rows),
        "laman_max": max(r["m"] - (2 * r["n"] - 3) for r in rows),
        "cluster_excess_max": max(r["cluster_excess"] for r in rows),
        "cluster_witness": sorted({(r["n"], r["cluster_size"], r["cluster_edges"])
                                   for r in rows
                                   if r["cluster_excess"] == max(
                                       q["cluster_excess"] for q in rows)}),
        "rows_cluster_tight": sum(1 for r in rows if r["cluster_excess"] == 0),
        "rows_cluster_over": sum(1 for r in rows if r["cluster_excess"] > 0),
        "cluster_by_size": {sz: max(r["cluster_profile"].get(sz, -99) for r in rows)
                           for sz in range(3, max(r["n"] for r in rows) + 1)},
        "classes_per_nm_max": max(len(v) for v in per_nm.values()),
        "ss_within_address": ss_addr,
        "ss_within_address_contact_free": ss_addr_mfree,
        "ss_contact_free_share": (ss_addr_mfree / ss_addr) if ss_addr > 0 else None,
        "m_pos_rows": len(mpos),
        "r2_address_m_pos": r2_addr_pos,
        "r2_rigidity_in_address_m_pos": r2_rig_in_addr_pos,
        "null_rigidity_in_address_m_pos": null_rig_in_addr_pos,
        "spread_m_pos_mean": (sum(spreads_pos) / len(spreads_pos)) if spreads_pos else None,
        "spread_m_pos_max": max(spreads_pos) if spreads_pos else None,
        "m_pos_classes": len(spreads_pos),
        "source_summary": source_summary,
        "delivered": delivered_counts(store),
        "within_class_spread_mean": (sum(spreads) / len(spreads)) if spreads else None,
        "within_class_spread_max": max(spreads) if spreads else None,
        "within_class_pairs": len(spreads),
        "spread_homogeneous_mean": (sum(homog) / len(homog)) if homog else None,
        "spread_heterogeneous_mean": (sum(het) / len(het)) if het else None,
        "spread_detail_top": spread_detail[:8],
        "m_range": [min(r["m"] for r in rows), max(r["m"] for r in rows)],
        "w_range": [min(r["w"] for r in rows), max(r["w"] for r in rows)],
        "class_sizes": sorted(sizes.values(), reverse=True),
        "per_n": table,
        "stability": f"{stable}/{total}",
    }


# --------------------------------------------------------------------- main
def _fmt(v, spec="+.4f"):
    return format(v, spec) if v is not None else "  none"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--draws", type=int, default=200)
    args = ap.parse_args()
    t0 = time.time()
    st = selftest()
    print("selftest:")
    for k, v in st["checks"].items():
        print(f"  {'ok  ' if v else 'FAIL'} {k}")
    for k, v in st["notes"].items():
        print(f"       {k} = {v}")
    print(f"  {st['passed']}/{st['total']} checks pass")

    ledger = {"instrument": "leech_comb.py", "run": 49, "schema": "leech-comb/3",
              "written": time.strftime("%Y-%m-%d %H:%M:%S"),
              "selftest": st, "contact_tol": CONTACT_TOL}
    ok = st["passed"] == st["total"]
    if not args.quick:
        ex = explain(draws=args.draws)
        ledger["explain"] = ex
        print(f"\nensemble: {ex['rows']} packings, n in {ex['n_values']}, "
              f"{ex['seconds']}s")
        print(f"  {'n':>3} {'rows':>5} {'addrs':>6} {'L range':>18} "
              f"{'mech':>12} {'pinned':>7} {'deliv. addr':>11}")
        for r in ex["per_n"]:
            print(f"  {r['n']:3d} {r['rows']:5d} {r['distinct_addresses']:6d} "
                  f"  [{r['L_min']:.4f}, {r['L_max']:.4f}] "
                  f"{str(r['mechanisms_seen']):>12} {r['pinned_rows']:7d} "
                  f"{str(r['delivered_address_seen']):>11}")
        print(f"\n  address: R^2 {_fmt(ex['r2_address'])} "
              f"(null mean {_fmt(ex['null_address']['mean'])}, "
              f"max {_fmt(ex['null_address']['max'])}, "
              f"{ex['null_address']['exceeding']}/{ex['null_address']['draws']} >=)")
        print(f"  tilt only {_fmt(ex['r2_tilt_only'])}   "
              f"|E| only {_fmt(ex['r2_edges_only'])}   "
              f"(n, source) {_fmt(ex['r2_stratified'])} vs null max "
              f"{_fmt(ex['null_stratified']['max'])} "
              f"({ex['null_stratified']['exceeding']}/{ex['null_stratified']['draws']})")
        print(f"  multi-member address classes: {ex['multi_rows']} rows, "
              f"R^2 {_fmt(ex['r2_multi'])} vs null max {_fmt(ex['null_multi']['max'])}"
              f" ({ex['null_multi']['exceeding']}/{ex['null_multi']['draws']})")
        print(f"\n  Maxwell/Laman (segment contacts, corner contacts excluded): "
              f"|E| {ex['m_range'][0]}..{ex['m_range'][1]}, "
              f"wall bars {ex['w_range'][0]}..{ex['w_range'][1]}")
        print(f"  rigidity class: R^2 {_fmt(ex['r2_rigidity'])} "
              f"(null mean {_fmt(ex['null_rigidity']['mean'])}, "
              f"max {_fmt(ex['null_rigidity']['max'])}, "
              f"{ex['null_rigidity']['exceeding']}/{ex['null_rigidity']['draws']} >=)"
              f"   (n, source) {_fmt(ex['r2_rigidity_stratified'])} vs null max "
              f"{_fmt(ex['null_rigidity_stratified']['max'])} "
              f"({ex['null_rigidity_stratified']['exceeding']}/"
              f"{ex['null_rigidity_stratified']['draws']})")
        print(f"  inside an address class: R^2 {_fmt(ex['r2_rigidity_in_address'])} "
              f"vs null mean {_fmt(ex['null_rigidity_in_address']['mean'])}, "
              f"max {_fmt(ex['null_rigidity_in_address']['max'])}, "
              f"{ex['null_rigidity_in_address']['exceeding']}/"
              f"{ex['null_rigidity_in_address']['draws']} >= observed")
        print(f"  coarser labels inside an address class: coarse "
              f"{_fmt(ex['r2_coarse_in_address'])}  pinned "
              f"{_fmt(ex['r2_pinned_in_address'])}")
        print(f"  beyond the edge count (|E| baseline): "
              f"{_fmt(ex['r2_rigidity_in_edges'])}")
        print(f"  ensemble structure: contact-free rows {ex['rows_contact_free']}/"
              f"{ex['rows']}, rows with a redundant contact {ex['rows_redundant']}, "
              f"Laman-tight rows {ex['rows_laman_tight']}, pinned {ex['rows_pinned']}, "
              f"max mechanisms {ex['mech_max']}, "
              f"rigidity classes per (n,|E|) cell <= {ex['classes_per_nm_max']}")
        print(f"  the spread is contact-free: share of within-address SS in |E|=0 "
              f"classes {_fmt(100 * (ex['ss_contact_free_share'] or 0), '.1f')}%")
        if ex["r2_address_m_pos"] is None:
            print(f"  contact-bearing rows only ({ex['m_pos_rows']} rows): L is "
                  f"constant to round-off (max spread "
                  f"{_fmt(ex['spread_m_pos_max'], '.4f')}), so conditional R^2 is "
                  f"undefined -- see the sources below")
        else:
            print(f"  contact-bearing rows only ({ex['m_pos_rows']} rows): address "
                  f"R^2 {_fmt(ex['r2_address_m_pos'])}, rigidity-in-address "
                  f"{_fmt(ex['r2_rigidity_in_address_m_pos'])} vs null max "
                  f"{_fmt(ex['null_rigidity_in_address_m_pos']['max'])}, L spread "
                  f"mean {_fmt(ex['spread_m_pos_mean'], '.4f')} max "
                  f"{_fmt(ex['spread_m_pos_max'], '.4f')} over "
                  f"{ex['m_pos_classes']} classes")
        print("  sources (a contact-bearing source is jammed at one L per family):")
        for d in ex["source_summary"]:
            print(f"    n={d['n']:2d} {d['src']:6s} rows={d['rows']:3d} "
                  f"|E|max={d['m_max']:2d} L=[{d['L_min']:.4f},{d['L_max']:.4f}]")
        print(f"  L spread inside an address class: mean "
              f"{ex['within_class_spread_mean']:.4f}  max "
              f"{ex['within_class_spread_max']:.4f}  "
              f"({ex['within_class_pairs']} classes); rigidity-homogeneous mean "
              f"{_fmt(ex['spread_homogeneous_mean'], '.4f')} vs heterogeneous "
              f"{_fmt(ex['spread_heterogeneous_mean'], '.4f')}")
        print(f"  multi-member classes only: rigidity-in-address R^2 "
              f"{_fmt(ex['r2_rigidity_in_multi_address'])} vs null max "
              f"{_fmt(ex['null_rigidity_in_multi_address']['max'])}")
        print("  widest address classes:")
        for d in ex["spread_detail_top"][:5]:
            print(f"    n={d['n']} rows={d['rows']} spread={d['spread']:.4f} "
                  f"|E|={d['m_values']} w={d['w_values']} rig={d['rig_classes']} "
                  f"pinned={d['pinned']}")
        dc = ex["delivered"]
        print(f"\n  delivered rows (n <= {dc['n_max']}, {dc['rows']} rows): Laman count "
              f"m-(2n-3) in [{dc['laman_min']:+d},{dc['laman_max']:+d}], "
              f"Laman-tight rows {dc['laman_tight']}, tilted rows "
              f"{dc['tilted_rows']}/{dc['rows']}, m/n mean {dc['m_over_n_mean']:.3f}")
        print("    exact rank, n <= " + str(dc["rank_nmax"]) + ": " +
              "  ".join(f"n={r['n']}:mech={r['mechanisms']},red={r['redundant']},"
                        f"pin={int(r['pinned'])}"
                        for r in dc["table"] if "mechanisms" in r))
        print(f"  class sizes (desc): {ex['class_sizes'][:12]}")
        print(f"  address stability under 1e-7: {ex['stability']}")

        exj = explain(draws=args.draws, jammed=True)
        ledger["explain_jammed"] = exj
        print(f"\n=== jammed ensemble (contact-bearing only): {exj['rows']} packings, "
              f"n in {exj['n_values']}, {exj['seconds']}s")
        print(f"  {'n':>3} {'rows':>5} {'addrs':>6} {'L range':>18} {'|E| range':>11} "
              f"{'|E|/n':>6} {'pinned':>7}")
        for r in exj["per_n"]:
            print(f"  {r['n']:3d} {r['rows']:5d} {r['distinct_addresses']:6d} "
                  f"  [{r['L_min']:.4f}, {r['L_max']:.4f}] "
                  f"{str(r['m_range']):>11} {r['m_mean'] / r['n']:6.2f} "
                  f"{r['pinned_rows']:7d}")
        print(f"  address R^2 {_fmt(exj['r2_address'])} (n), "
              f"{_fmt(exj['r2_stratified'])} (n, source) vs null max "
              f"{_fmt(exj['null_stratified']['max'])} "
              f"({exj['null_stratified']['exceeding']}/"
              f"{exj['null_stratified']['draws']})")
        print(f"  rigidity R^2 {_fmt(exj['r2_rigidity'])}; rigidity-in-address "
              f"{_fmt(exj['r2_rigidity_in_address'])} vs null max "
              f"{_fmt(exj['null_rigidity_in_address']['max'])} "
              f"({exj['null_rigidity_in_address']['exceeding']}/"
              f"{exj['null_rigidity_in_address']['draws']}); beyond |E| "
              f"{_fmt(exj['r2_rigidity_in_edges'])}")
        print(f"  Laman count m-(2n-3) in [{exj['laman_min']:+d},{exj['laman_max']:+d}], "
              f"global tight/over {exj['rows_laman_tight']}/{exj['rows']}, "
              f"|E|/n mean {exj['m_per_n_mean']:.2f}, redundant contacts "
              f"{exj['rows_redundant']}")
        print(f"  tightest cluster |E(S)|-(2|S|-3): max {exj['cluster_excess_max']:+d} at "
              f"{exj['cluster_witness'][:3]}; tight {exj['rows_cluster_tight']}, "
              f"over {exj['rows_cluster_over']}")
        print("  cluster headroom by size: " + ", ".join(
            f"|S|={sz}:{v:+d}" for sz, v in exj["cluster_by_size"].items()) +
              f";  |E| only R^2 {_fmt(exj['r2_edges_only'])}")
        print(f"  multi-member classes: {exj['multi_rows']} rows, address R^2 "
              f"{_fmt(exj['r2_multi'])} vs null max {_fmt(exj['null_multi']['max'])}"
              f"; rigidity-in-address "
              f"{_fmt(exj['r2_rigidity_in_multi_address'])} vs null max "
              f"{_fmt(exj['null_rigidity_in_multi_address']['max'])}")
        print(f"  L spread inside an address class: mean "
              f"{_fmt(exj['within_class_spread_mean'], '.4f')} max "
              f"{_fmt(exj['within_class_spread_max'], '.4f')} "
              f"({exj['within_class_pairs']} classes); widest:")
        for d in exj["spread_detail_top"][:4]:
            print(f"    n={d['n']} rows={d['rows']} spread={d['spread']:.4f} "
                  f"|E|={d['m_values']} rig={d['rig_classes']}")
    ledger["ok"] = ok
    ledger["seconds"] = round(time.time() - t0, 2)
    # a --quick run must not wipe the sections it does not recompute
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    if os.path.exists(OUT):
        try:
            with open(OUT) as f:
                old = json.load(f)
        except (json.JSONDecodeError, OSError):
            old = {}
        for k in ("explain", "explain_jammed"):
            if k not in ledger and k in old:
                ledger[k] = old[k]
    with open(OUT, "w") as f:
        json.dump(ledger, f, indent=1)
    print(f"\n{'PASS' if ok else 'FAIL'}  [{ledger['seconds']}s]  ledger: {OUT}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
