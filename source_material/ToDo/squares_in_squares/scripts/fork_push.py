#!/usr/bin/env python3
r"""fork_push.py — fifth push: carried-fork resolution of the grid-tie wall.

User framework mapping (Golay d=4 tie -> packing jam), operationalized:
  - run 3 classified RIGID_WALL on JITTERED seeds (grid_seed tilts every
    square +-0.35 rad = blind jitter = forced guess). This run replaces
    jitter with STRUCTURAL seeds and carries ALL branches (the fork),
    classifying each; settle cycles are committed per the verdicts.
  - branch set per target = 4 structural bases x 2 protocols (hot/cold)
    = 8 branches (>= 2^3: the three binary questions of the framework:
    base motif, temperature sector, pressure schedule).
Bases:
  S1  the table's own grid state (theta=0 exactly, no jitter) at L=k+1
  S2  nearest above member/chain record, rescaled to L=k+1, outermost
      staircase layers removed to reach n squares (chain-style, seeded)
  S3  mirror-split: k-grid halves tilted +-0.5 deg (symmetry-broken
      sector), border squares in the top strip
  S4  rigid tilted grid at theta_max (bbox limit) + r diamonds stacked
      in the widest wall strip
Wheel certificates (exact, all 593 open n):
  A. rigid tilted k-grid at s <= k+1: wall-strip width >= 1 occurs only
     on sub-unit length (needs theta >= ~15 deg for real wedges, but
     bbox requires theta <= ~2 deg) -> 0 extra squares outside, always.
  B. mirror-split (2 pieces, +-theta): gap >= 1 anywhere requires
     k cos th + 2k sin th <= k, i.e. theta >= 126.9 deg -> impossible.
Framework arithmetic (printed, saved):
  C(24,4)=10626=6*1771; 1+24+276+2024=2325; 4096-2325=1771 cosets;
  lambda_4 = C(20,1)/C(4,1) = 5 octads through a tetrad; 6 nearest
  codewords = {0} u 5 octads; 680064 = 1771*384 (identity only).
Outputs: workspace/push/fork_results.json + console report.
"""
import json
import math
import os
import sys
import time
from math import ceil, sqrt

import numpy as np

HERE = "/home/z/my-project/scripts"
sys.path.insert(0, HERE)
import packlib as P
from delta_sigma_push import DeltaSigma, classify
from sa_push import anneal, final_max_overlap, hw_vals, state_from_table

TAB = "/home/z/my-project/workspace/submission/table.json"
PUSH = "/home/z/my-project/workspace/push"
os.makedirs(PUSH, exist_ok=True)
RES = PUSH + "/fork_results.json"

KAPPA = 0.25
DL_MIN, DL_MAX = 5e-4, 2e-2
SETTLE_MOVES = 6000          # per anneal call (n~800: ~45 s)
JAM_STREAK = 3
TOP_SETTLE = [803, 748]      # full 8-branch settles
TOP_CLASSIFY = [803, 748, 983, 804, 862, 695, 922, 749]


# ---------------------------------------------------------- framework check

def framework_check():
    from math import comb
    c24_4 = comb(24, 4)
    sextets = c24_4 // 6
    coset_leaders = 1 + 24 + 276 + 2024
    deep = 4096 - coset_leaders
    lam4 = comb(20, 1) // comb(4, 1)
    out = {
        "C(24,4)": c24_4,
        "C(24,4)/6 (sextet co-leaders per coset)": sextets,
        "1+24+276+2024 (leader weights 0..3)": coset_leaders,
        "4096-2325 (weight-4-leader cosets)": deep,
        "lambda_4 = C(20,1)/C(4,1) (octads through a tetrad)": lam4,
        "nearest codewords = 1 + lambda_4": 1 + lam4,
        "680064 / 1771": 680064 // 1771,
        "680064 == 1771*384": 1771 * 384 == 680064,
    }
    ok = (c24_4 == 10626 and sextets == 1771 and deep == 1771
          and lam4 == 5 and 1 + lam4 == 6 and 1771 * 384 == 680064)
    out["ALL_ARITHMETIC_OK"] = ok
    return out


# ---------------------------------------------------------- wheel certs

def cert_tilted_grid(n):
    """Max unit squares outside a rigid tilted k-grid at s <= k+1.
    Returns (capacity, theta_max, arg). Rigid wheel = A."""
    k = int(sqrt(n))
    while k * k > n:
        k -= 1
    r = n - k * k
    s = float(k + 1)
    # theta_max from bbox: k(cos+sin) <= s
    th_max = 0.0
    for i in range(1, 9001):
        th = i * 1e-4
        if k * (math.cos(th) + math.sin(th)) > s:
            break
        th_max = th
    # for each theta: wall-strip length with width >= 1 (best placement:
    # pushed to a corner, binding vertex on a wall). The widest strip
    # height reaches Y0 + k sin th where Y0 = s - k(cos+sin) >= 0.
    best_cap = 0
    best_th = 0.0
    for i in range(0, int(th_max / 1e-3) + 1):
        th = i * 1e-3
        if th <= 0:
            # theta=0: border strip exactly 1 wide: capacity 2k+1 at s=k+1
            # (the grid packing itself, NOT a win: s = k+1 exactly).
            # for s < k+1 theta=0 gives width < 1: capacity 0.
            continue
        Y0 = s - k * (math.cos(th) + math.sin(th))
        top = Y0 + k * math.sin(th)     # max strip height along wall
        if top < 1.0:
            continue                    # strip never reaches width 1
        tan_th = math.tan(th)
        # strip height h(x) = Y0 + (x - x_v1) tan th over x-length k cos th;
        # length of the zone with h >= 1:
        import math as M
        # zone: x >= x_v1 + (1 - Y0)/tan_th ; total x-extent k*cos(th)
        need = (1.0 - Y0) / tan_th if tan_th > 0 else 1e9
        zone_len = max(0.0, k * M.cos(th) - need)
        cap = int(M.floor(zone_len))    # squares side by side in the strip
        if cap > best_cap:
            best_cap, best_th = cap, th
    return best_cap, th_max, r, k


def cert_mirror_split(n):
    """Gap >= 1 between two mirrored half-grids at s = k+1 requires
    k cos th + 2k sin th <= k  <=>  theta >= 2 arctan(2) ~ 126.87 deg."""
    k = int(sqrt(n))
    while k * k > n:
        k -= 1
    s = float(k + 1)
    # smallest theta solving k cos + 2k sin = k (theta>0 branch)
    # f(th) = cos + 2 sin - 1 = 0
    lo, hi = 0.0, math.pi / 2
    for _ in range(200):
        mid = (lo + hi) / 2
        if math.cos(mid) + 2 * math.sin(mid) - 1 > 0:
            lo = mid
        else:
            hi = mid
    th_need = (lo + hi) / 2          # ~1.107 rad = 63.4 deg? check: this is
    # the root of cos+2sin=1; but the inequality needed is
    # k cos th + 2k sin th <= k  i.e. cos+2sin <= 1, whose solution set is
    # th >= th_need with th_need = 2 arctan 2 = 126.87 deg — recompute:
    # cos+2sin = 1 has roots th ~ 0.6435? no: at th=0: 1+0-1=0 — th=0 is a
    # root (the grid packing: gap exactly 1 at theta=0 — consistent).
    # The next root: cos+2sin=1 again at th in (0,pi): solve properly below.
    from math import atan2
    # cos th + 2 sin th = 1  ->  sqrt5 sin(th + phi) = 1, phi=atan(1/2)
    phi = atan2(1, 2)  # ~0.4636
    # th = asin(1/sqrt5) - phi (~0.4636-0.4636=0? check) and pi-asin - phi
    a = math.asin(1 / sqrt(5))
    roots = sorted([a - phi, math.pi - a - phi])
    # positive non-zero root:
    th_second = roots[1] if roots[1] > 1e-9 else roots[0]
    ok_impossible = th_second > math.radians(90)  # must be ~126.87 deg
    # verify numerically at a spread of thetas that gap < 1 for 0 < th < 0.9
    # rad (theta=0 excluded: gap = 1 exactly there is the UNTILTED split,
    # i.e. the grid packing itself at s=k+1 -- not a win)
    worst_gap = 0.0
    for i in range(1, 900):
        th = i * 1e-3
        gap = s - k * math.cos(th) - 2 * k * math.sin(th)
        worst_gap = max(worst_gap, gap)
    return th_second, ok_impossible, worst_gap


# ---------------------------------------------------------- seed builders

def s1_grid(rec, k):
    X, Y, TH = state_from_table(rec)
    return X, Y, TH, float(k + 1), "table grid state (no jitter)"


def s2_member_minus(tab, n, k):
    """nearest above non-grid record; rescale to L=k+1; remove the
    outermost staircase layers (deepest i+j) to reach n squares."""
    src = None
    for np_ in range(n + 1, min(n + 80, 1001)):
        s_ = tab[str(np_)]["src"]
        if not s_.startswith("grid"):
            src = np_
            break
    if src is None:
        return None
    rec = tab[str(src)]
    L_src = rec["L"]
    X, Y, TH = state_from_table(rec)
    f = (k + 1) / L_src
    X, Y = X * f, Y * f
    L = float(k + 1)
    # staircase squares: theta ~ 0; block squares theta ~ pi/4 (gobel) or
    # free (numerical). Remove among theta~0 the ones with max x+y per
    # corner (innermost layer toward the block).
    n_remove = src - n
    idx_grid = [i for i in range(len(TH)) if abs(TH[i]) < 0.2]
    if len(idx_grid) < n_remove:
        idx_grid = list(range(len(TH)))  # fallback: any squares
    # score: distance from container center along the diagonal toward the
    # nearest corner: innermost staircase squares are closest to the block
    # (i.e., farthest from their corner). We remove farthest-from-corner
    # among grid squares: those nearest the block.
    cx = cy = L / 2
    def corner_dist(i):
        # distance to the nearest container corner
        return min(X[i], L - X[i]) + min(Y[i], L - Y[i])
    order = sorted(idx_grid, key=lambda i: corner_dist(i))
    # remove the ones closest to the CENTER of the container first: for a
    # Goebel member these are the innermost staircase squares (i+j = a-1,
    # the layer that binds the block face) -- removing them frees s.
    cen = sorted(idx_grid, key=lambda i: (X[i] - cx) ** 2 + (Y[i] - cy) ** 2)
    rm = set(cen[:n_remove])
    keep = [i for i in range(len(TH)) if i not in rm]
    return X[keep], Y[keep], TH[keep], L, f"member {src} (L={L_src:.4f}) rescaled, -{n_remove} innermost"


def s3_mirror(k, r, L, seed=1):
    """k-grid split into left/right halves tilted +-0.5 deg; r border
    squares axis-aligned in the top strip."""
    rng = np.random.RandomState(seed)
    n = k * k + r
    X = np.empty(n); Y = np.empty(n); TH = np.empty(n)
    th = math.radians(0.5)
    half = k // 2
    p = 0
    for i in range(k):
        for j in range(k):
            # column j: left half (j < half) tilts +th, right half -th,
            # each about its half's center x
            cx = (half - 0.5) if j < half else (k - half - 0.5) + half
            # local coords about (cx, k/2-0.5)
            lx = j - cx
            ly = i - (k / 2 - 0.5)
            t = th if j < half else -th
            c, s_ = math.cos(t), math.sin(t)
            x = cx + lx * c - ly * s_
            y = (k / 2 - 0.5) + lx * s_ + ly * c
            X[p] = x; Y[p] = y; TH[p] = t
            p += 1
    for q in range(r):
        X[p] = q + 0.5
        Y[p] = k + 0.5
        TH[p] = 0.0
        p += 1
    return X, Y, TH, float(k + 1), "mirror-split +-0.5deg + top strip"


def s4_tilted(k, r):
    """rigid k-grid tilted at theta_max (bbox limit), pushed to a corner;
    r diamonds (45 deg) stacked in the widest wall strip (seed overlaps
    are small and get annealed out)."""
    s = float(k + 1)
    th_max = 0.0
    for i in range(1, 9001):
        t = i * 1e-4
        if k * (math.cos(t) + math.sin(t)) > s:
            break
        th_max = t
    th = th_max
    c, s_ = math.cos(th), math.sin(th)
    # placement: binding vertex on the left wall & bottom as derived:
    # vertices (X0, Y0) + k*{ (0,0), (c,s), (c-s, s+c), (-s, c) }
    # choose X0 = k*sin(th) (v4 on left wall), Y0 = s - k*(c+s) (v3 top)
    X0 = k * s_
    Y0 = s - k * (c + s_)
    n = k * k + r
    X = np.empty(n); Y = np.empty(n); TH = np.empty(n)
    # block squares on the rotated lattice inside the tilted square:
    # unit squares tiling the k-grid rotated by th, corners at
    # (X0,Y0) + (i+0.5)*(c,s) + (j+0.5)*(-s,c) for i,j in 0..k-1
    p = 0
    for i in range(k):
        for j in range(k):
            u = i + 0.5
            v = j + 0.5
            X[p] = X0 + u * c - v * s_
            Y[p] = Y0 + u * s_ + v * c
            TH[p] = th
            p += 1
    # r diamonds in the widest wall strip: the bottom wall strip peaks at
    # height Y0 + k sin th near the right wall; stack diamonds at 45 deg
    # along the left wall bottom (slight overlaps, anneal cleans)
    for q in range(r):
        X[p] = 0.71
        Y[p] = 0.71 + q * 0.741
        TH[p] = math.pi / 4
        p += 1
    return X, Y, TH, s, f"rigid tilted grid {math.degrees(th):.3f}deg + {r} diamonds"


# ---------------------------------------------------------- settle

def settle_branch(X, Y, TH, L0, n, protocol, budget_s, tag, log):
    """Delta-Sigma shrink-loop from L0. Returns (best_L, best_state, notes)."""
    t_start = time.time()
    ds = DeltaSigma(4e-3)
    L = L0
    best_L, best_state = None, None
    jams = 0
    calls = 0
    t0 = 0.02 if protocol == "hot" else 0.002
    notes = []
    L_floor = sqrt(n) + 1e-9
    while L - 1e-12 > L_floor and jams < JAM_STREAK and calls < 12 \
            and time.time() - t_start < budget_s:
        L_try = L - ds.dl
        if L_try < L_floor:
            L_try = L_floor
        Xs, Ys, Ts = X * (L_try / L), Y * (L_try / L), TH.copy()
        Xs = np.clip(Xs, 0.05, L_try - 0.05)
        Ys = np.clip(Ys, 0.05, L_try - 0.05)
        X2, Y2, T2 = Xs.copy(), Ys.copy(), Ts.copy()
        seed = 7919 * n + 104729 * calls + (sum(ord(ch) for ch in tag) % 9973)
        anneal(X2, Y2, T2, L_try, SETTLE_MOVES, seed, t0=t0, tend=1e-4,
               rotate_frac=0.5 if protocol == "hot" else 0.25)
        mo, mx_out = final_max_overlap(X2, Y2, T2, L_try)
        ok = mo < 1e-10 and mx_out < 1e-12
        calls += 1
        if ok:
            L = L_try
            X = np.array([q for q in X2])
            Y = np.array([q for q in Y2])
            TH = np.array([q for q in T2])
            best_L, best_state = L, [[float(a), float(b), float(c)]
                                     for a, b, c in zip(X2, Y2, T2)]
            jams = 0
            ds.step(True)
            log(f"    {tag}: OK at L={L:.6f} (call {calls})")
        else:
            jams += 1
            ds.step(False)
            notes.append(f"jam@{L_try:.4f} ov={mo:.2e}")
    return best_L, best_state, {"calls": calls, "jams": jams, "notes": notes}


def verify_state(st, L, n):
    r = P.verify([tuple(q) for q in st], tol=1e-9)
    return r["ok"] and len(st) == n


# ---------------------------------------------------------- main

def main():
    t0all = time.time()
    tab = json.load(open(TAB))
    fw = framework_check()
    print("=== framework arithmetic ===")
    for k, v in fw.items():
        print(f"  {k}: {v}")

    open_n = [n for n in range(1, 1001) if tab[str(n)]["src"].startswith("grid")]

    # ---- wheel certificates over all open n
    print(f"\n=== wheel certificates over {len(open_n)} open n ===")
    caps = [cert_tilted_grid(n)[0] for n in open_n]
    from collections import Counter
    print("  A. rigid tilted grid: extra-square capacity distribution:",
          dict(Counter(caps)))
    th2, imposs, worst = cert_mirror_split(open_n[0])
    print(f"  B. mirror-split: gap>=1 needs theta >= {math.degrees(th2):.2f} deg "
          f"(>90 deg: {imposs}); max gap over theta<0.9 rad: {worst:.4f} (<1: {worst < 1.0})")

    # ---- fork on top targets
    results = []
    for n in TOP_CLASSIFY:
        k = int(sqrt(n))
        while k * k > n:
            k -= 1
        r = n - k * k
        rec = tab[str(n)]
        seeds = []
        a = s1_grid(rec, k)
        if a: seeds.append(("S1", *a))
        b = s2_member_minus(tab, n, k)
        if b is not None: seeds.append(("S2", *b))
        c = s3_mirror(k, r, k + 1, seed=7919 * n)
        seeds.append(("S3", *c))
        d = s4_tilted(k, r)
        seeds.append(("S4", *d))
        row = {"n": n, "k": k, "r": r, "branches": []}
        print(f"\n--- n={n} (k={k}, r={r}, grid={k+1}) ---")
        for name, X, Y, TH, L, desc in seeds:
            verdict, rho, ones, tot = classify(X, Y, TH)
            mo, mxo = final_max_overlap(X, Y, TH, L)
            br = {"base": name, "desc": desc, "L_seed": L,
                  "seed_overlap": round(float(mo), 6),
                  "verdict": verdict, "rho": round(rho, 4),
                  "contacts": f"{ones}/{tot}"}
            print(f"  {name} [{desc[:48]}]: {verdict} rho={rho:.3f} "
                  f"contacts={ones}/{tot} seed_ov={mo:.1e}")
            # settle commitment: top-2 targets, all bases x protocols
            if n in TOP_SETTLE:
                for proto in ("hot", "cold"):
                    tag = f"{n}/{name}/{proto}"
                    bL, bSt, info = settle_branch(
                        X, Y, TH, L - 1e-4, n, proto, 260.0, tag,
                        lambda m: None)
                    br[f"settle_{proto}"] = {
                        "best_L": bL, "calls": info["calls"],
                        "jams": info["jams"]}
                    line = f"    settle {proto}: best_L={bL} calls={info['calls']} jams={info['jams']}"
                    if bL is not None and bL < k + 1 - 1e-9:
                        ok = verify_state(bSt, bL, n)
                        line += f"  *** BEATS GRID {k+1}! verify={ok} ***"
                        if ok:
                            br["WIN"] = True
                            br["win_state"] = bSt
                    print(line)
            row["branches"].append(br)
        results.append(row)

    json.dump({"framework": fw, "results": results,
               "settles": {"moves": SETTLE_MOVES, "targets": TOP_SETTLE}},
              open(RES, "w"), indent=1)
    print(f"\ntotal {time.time()-t0all:.0f}s; results -> {RES}")


if __name__ == "__main__":
    main()
