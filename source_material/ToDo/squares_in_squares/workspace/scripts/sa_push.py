#!/usr/bin/env python3
"""sa_push.py — simulated-annealing push engine for the packing table.

Stage A (push): targets whose current packing was CONSTRUCTED (src chain3 /
removal / aux) — never optimized; shrink ladder in small steps, annealing at
each step; every success is real score.

Stage B (attack): targets still at the trivial grid whose optimality is NOT
proven (triangular-table 'Proved' flag; open problems) — try sub-grid
containers with grid+jitter seeds and tilted-motif annealing.

Determinism: RandomState(seed), seed = 7919*n + 104729*attempt.
Finds saved incrementally: workspace/push/finds_<stage>.json
  {n: {"L": container used, "state": [...], "P": final penalty}}
Only states with max pairwise overlap < 1e-10 and zero container violation
are saved (apply_push re-verifies with packlib before accepting).

Engine facts (from the study): pair overlap via 4-axis SAT on the two
squares' edge normals; container penalty from the rotated half-width
hw = (|cos|+|sin|)/2 on both axes.  Objective = sum of squared pair
overlaps + squared out-of-container amounts.  Moves: translate one square
(uniform step ~ temperature), rotate one square (30% of moves).  Metropolis
acceptance; geometric temperature schedule; final greedy polish.
"""
import json
import os
import sys
import time
from math import ceil, sqrt

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import packlib as P

ROOT = __import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__)))

TAB = ROOT + "/workspace/submission/table.json"
PUSH = ROOT + "/workspace/push"
TRI_HTML = "/tmp/aux_triangular_table_html.html"

os.makedirs(PUSH, exist_ok=True)

# ---------------------------------------------------------------- penalties

def hw_vals(TH):
    """half-width of each rotated unit square on x and y axes (same value)."""
    return 0.5 * (np.abs(np.cos(TH)) + np.abs(np.sin(TH)))

def pair_pen_k(k, X, Y, TH, HW):
    """vector of overlap depths between square k and all others (0 = clear).
    Returns array over j != k (unsorted order but consistent length)."""
    n = len(X)
    idx = np.arange(n)
    mask = idx != k
    J = idx[mask]
    dx = X[J] - X[k]
    dy = Y[J] - Y[k]
    ck, sk = np.cos(TH[k]), np.sin(TH[k])
    cj, sj = np.cos(TH[J]), np.sin(TH[J])
    # distance prefilter: on x-axis, separation needs |dx| >= hw_k+hw_j
    # max possible hw sum = sqrt(2); skip pairs farther than 1.42 on either axis
    near = (np.abs(dx) < 1.42) & (np.abs(dy) < 1.42)
    out = np.zeros(len(J))
    if not near.any():
        return out
    Jn = J[near]
    dxn = dx[near]
    dyn = dy[near]
    cjn, sjn = np.cos(TH[Jn]), np.sin(TH[Jn])
    # 4 SAT axes: k's edge normals (ck,sk), (-sk,ck); Jn's (cjn,sjn), (-sjn,cjn).
    # overlap on axis u: ov = hk(u) + hj(u) - |d.u|
    def ov_axis(ax, ay, bx, by):
        # fixed axis (ax,ay) for k; array axes (bx,by) for Jn
        du = dxn * ax + dyn * ay
        hk = 0.5 * (abs(ax * ck + ay * sk) + abs(-ax * sk + ay * ck))
        hj = 0.5 * (np.abs(bx * ax + by * ay) + np.abs(-bx * ay + by * ax))
        return hk + hj - np.abs(du)
    # k's two edge-normal axes
    a1 = ov_axis(ck, sk, cjn, sjn)
    a2 = ov_axis(-sk, ck, cjn, sjn)
    # Jn's two edge-normal axes (array-valued)
    du = dxn * cjn + dyn * sjn
    hk = 0.5 * (np.abs(cjn * ck + sjn * sk) + np.abs(-cjn * sk + sjn * ck))
    hj = 0.5 * (np.abs(cjn * cjn + sjn * sjn) + np.abs(-cjn * sjn + sjn * cjn))
    a3 = hk + hj - np.abs(du)
    du = dxn * (-sjn) + dyn * cjn
    hk = 0.5 * (np.abs((-sjn) * ck + cjn * sk) + np.abs(-(-sjn) * sk + cjn * ck))
    hj = 0.5 * (np.abs((-sjn) * cjn + cjn * sjn) + np.abs(-(-sjn) * sjn + cjn * cjn))
    a4 = hk + hj - np.abs(du)
    # separation on any axis: overlap = min over axes, floored at 0
    ov = np.minimum(np.minimum(a1, a2), np.minimum(a3, a4))
    out[near] = np.maximum(ov, 0.0)
    return out

def out_pen(X, Y, HW, L):
    """container violation amounts per square: (left+right+bottom+top)."""
    left = np.maximum(HW - X, 0)      # left edge past 0
    right = np.maximum(X + HW - L, 0)  # right edge past L
    bottom = np.maximum(HW - Y, 0)
    top = np.maximum(Y + HW - L, 0)
    return left + right + bottom + top

OUTW = 4.0  # container violations are weighted above pair overlaps

def total_pen(X, Y, TH, HW, L, weight=1.0):
    n = len(X)
    s = 0.0
    for k in range(n):
        pk = pair_pen_k(k, X, Y, TH, HW)
        s += float(np.sum(pk * pk))
    op = out_pen(X, Y, HW, L)
    s += weight * float(np.sum(op * op))
    return s

# ---------------------------------------------------------------- annealing

def anneal(X, Y, TH, L, moves, seed, t0=0.02, tend=1e-4, rotate_frac=0.3):
    """in-place SA on arrays; returns final objective (squared penalty).
    Schedule: geometric T decay, then an improving-only polish tail (15%)."""
    rng = np.random.RandomState(seed)
    n = len(X)
    HW = hw_vals(TH)
    cur = total_pen(X, Y, TH, HW, L, weight=OUTW)
    best = cur
    bestX, bestY, bestT = X.copy(), Y.copy(), TH.copy()
    m_sa = int(moves * 0.85)
    T = t0
    decay = (tend / t0) ** (1.0 / max(1, m_sa - 1))

    def local_dP(k, new_x, new_y, new_t):
        """mutate square k to the proposal; return (old_e, new_e, old_state)."""
        old_x, old_y, old_t = X[k], Y[k], TH[k]
        hw_old = HW[k]
        old_pk = pair_pen_k(k, X, Y, TH, HW)
        old_local = float(np.sum(old_pk * old_pk))
        oxo = np.array([hw_old - old_x, old_x + hw_old - L,
                        hw_old - old_y, old_y + hw_old - L])
        old_out = OUTW * float(np.sum(np.maximum(oxo, 0) ** 2))
        X[k], Y[k], TH[k] = new_x, new_y, new_t
        hwk = 0.5 * (abs(np.cos(new_t)) + abs(np.sin(new_t)))
        HW[k] = hwk
        new_pk = pair_pen_k(k, X, Y, TH, HW)
        new_local = float(np.sum(new_pk * new_pk))
        ox = np.array([hwk - new_x, new_x + hwk - L,
                       hwk - new_y, new_y + hwk - L])
        new_out = OUTW * float(np.sum(np.maximum(ox, 0) ** 2))
        return (old_local + old_out), (new_local + new_out), (old_x, old_y, old_t, hw_old)

    def revert(k, old_state):
        X[k], Y[k], TH[k], HW[k] = old_state

    def global_rotate(dth):
        """rotate every square by dth; return (old_energy, new_energy, snapshot)."""
        snap = (X.copy(), Y.copy(), TH.copy(), HW.copy())
        e_old = total_pen(X, Y, TH, HW, L, weight=OUTW)
        TH[:] = TH + dth
        HW[:] = hw_vals(TH)
        e_new = total_pen(X, Y, TH, HW, L, weight=OUTW)
        return e_old, e_new, snap

    def restore(snap):
        X[:] = snap[0]; Y[:] = snap[1]; TH[:] = snap[2]; HW[:] = snap[3]

    def row_shift_move(rng, T):
        """translate one row (squares within y-tolerance) together."""
        yv = Y[rng.randint(n)]
        idx = np.where(np.abs(Y - yv) < 0.31)[0]
        if len(idx) < 2:
            return None
        snap = (X.copy(), Y.copy(), TH.copy(), HW.copy())
        e_old = total_pen(X, Y, TH, HW, L, weight=OUTW)
        ps = max(1e-5, 0.6 * T)
        X[idx] += rng.uniform(-ps, ps)
        Y[idx] += rng.uniform(-ps, ps)
        e_new = total_pen(X, Y, TH, HW, L, weight=OUTW)
        return e_old, e_new, snap

    for it in range(m_sa):
        k = rng.randint(n)
        u = rng.uniform()
        if u < 0.02:
            # global rotation (collective; expensive O(n^2) — rare)
            dth = rng.uniform(-1.5, 1.5) * max(1e-6, 0.5 * T)
            e_o, e_n, snap = global_rotate(dth)
            dP = e_n - e_o
            if dP <= 0 or rng.uniform() < np.exp(-dP / T):
                cur = e_n
                if cur < best - 1e-15:
                    best = cur
                    bestX[:] = X; bestY[:] = Y; bestT[:] = TH
            else:
                restore(snap)
            T *= decay
            if T < tend:
                T = tend
            continue
        if u < 0.08:
            r = row_shift_move(rng, T)
            if r is not None:
                e_o, e_n, snap = r
                dP = e_n - e_o
                if dP <= 0 or rng.uniform() < np.exp(-dP / T):
                    cur = e_n
                    if cur < best - 1e-15:
                        best = cur
                        bestX[:] = X; bestY[:] = Y; bestT[:] = TH
                else:
                    restore(snap)
                T *= decay
                if T < tend:
                    T = tend
                continue
        ps = max(1e-5, 0.6 * T)
        as_: float = max(1e-5, 0.9 * T)
        new_x = X[k] + rng.uniform(-ps, ps)
        new_y = Y[k] + rng.uniform(-ps, ps)
        new_t = TH[k] + (rng.uniform(-as_, as_) if rng.uniform() < rotate_frac else 0.0)
        old_e, new_e, olds = local_dP(k, new_x, new_y, new_t)
        dP = new_e - old_e
        if dP <= 0 or rng.uniform() < np.exp(-dP / T):
            cur += dP
            if cur < best - 1e-15:
                best = cur
                bestX[:] = X; bestY[:] = Y; bestT[:] = TH
        else:
            revert(k, olds)
        T *= decay
        if T < tend:
            T = tend
    # improving-only polish tail
    for it in range(moves - m_sa):
        k = rng.randint(n)
        ps = 0.0015
        new_x = X[k] + rng.uniform(-ps, ps)
        new_y = Y[k] + rng.uniform(-ps, ps)
        new_t = TH[k] + (rng.uniform(-ps, ps) if rng.uniform() < rotate_frac else 0.0)
        old_e, new_e, olds = local_dP(k, new_x, new_y, new_t)
        if new_e < old_e - 1e-18:
            cur += new_e - old_e
            if cur < best - 1e-15:
                best = cur
                bestX[:] = X; bestY[:] = Y; bestT[:] = TH
        else:
            revert(k, olds)
    X[:] = bestX; Y[:] = bestY; TH[:] = bestT
    HW[:] = hw_vals(TH)
    return best

def final_max_overlap(X, Y, TH, L):
    """max pairwise overlap depth (linear) + max container violation."""
    HW = hw_vals(TH)
    n = len(X)
    mx = 0.0
    for k in range(n):
        pk = pair_pen_k(k, X, Y, TH, HW)
        if len(pk):
            mx = max(mx, float(np.max(pk)))
    op = out_pen(X, Y, HW, L)
    return mx, float(np.max(op))

# ---------------------------------------------------------------- seeds

def state_from_table(rec):
    st = rec["state"]
    X = np.array([q[0] for q in st])
    Y = np.array([q[1] for q in st])
    TH = np.array([q[2] for q in st])
    return X, Y, TH

def grid_seed(n, L, seed):
    rng = np.random.RandomState(seed)
    k = int(ceil(sqrt(n)))
    sc = L / k
    X = np.empty(n); Y = np.empty(n); TH = np.empty(n)
    for i in range(n):
        X[i] = (i % k + 0.5) * sc
        Y[i] = (i // k + 0.5) * sc
        TH[i] = rng.uniform(-0.35, 0.35)
    return X, Y, TH

# ---------------------------------------------------------------- proven set

def proven_optimal():
    """n whose tri-table row says 'Proved' (attacking them is futile)."""
    import re
    h = open(TRI_HTML, errors="ignore").read()
    h = re.sub(r"<!--[\s\S]*?-->", " ", h)
    h = re.sub(r"<script[\s\S]*?</script>", " ", h)
    t = re.sub(r"<[^>]+>", " ", h)
    t = t.replace("&nbsp;", " ").replace("&ensp;", " ").replace("&thinsp;", " ")
    lines = [l.strip() for l in t.split("\n") if l.strip()]
    start = next(i for i, l in enumerate(lines) if l == "1.")
    out = set()
    n = None
    for l in lines[start:]:
        m = re.match(r"^(\d+)\.$", l)
        if m:
            n = int(m.group(1))
            continue
        if n is None:
            continue
        if re.search(r"\\Nn\{([0-9.]+)\}", l) or re.match(r"^\$s = ", l):
            if "Proved" in l or "proved" in l:
                out.add(n)
            n = None
    return out

# ---------------------------------------------------------------- stages

def load_finds(stage):
    p = os.path.join(PUSH, f"finds_{stage}.json")
    if os.path.exists(p):
        return json.load(open(p))
    return {}

def save_finds(stage, d):
    json.dump(d, open(os.path.join(PUSH, f"finds_{stage}.json"), "w"))

def log(stage, msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(os.path.join(PUSH, f"log_{stage}.txt"), "a") as f:
        f.write(line + "\n")

def moves_for(n):
    return int(min(120000, max(30000, 250 * n)))

def try_container(X, Y, TH, L, attempt, n):
    """anneal at container L; return (ok, final_state, max_ov, max_out)."""
    seed = 7919 * n + 104729 * attempt
    X2, Y2, T2 = X.copy(), Y.copy(), TH.copy()
    anneal(X2, Y2, T2, L, moves_for(n), seed)
    mo, mx_out = final_max_overlap(X2, Y2, T2, L)
    ok = mo < 1e-10 and mx_out < 1e-12
    return ok, [list(q) for q in zip(X2.tolist(), Y2.tolist(), T2.tolist())], mo, mx_out

def stage_a(tab, budget_s):
    """push constructed packings (chain3 / removal / aux)."""
    t0 = time.time()
    finds = load_finds("A")
    targets = [n for n in range(1, 1001)
               if tab[str(n)].get("src", "").split(":")[0] in ("chain3", "removal", "aux")]
    log("A", f"Stage A: {len(targets)} push targets")
    done = 0
    for n in sorted(targets):
        if time.time() - t0 > budget_s:
            log("A", f"budget reached at n={n} ({done} done)")
            break
        rec = tab[str(n)]
        L0 = rec["L"]
        src = rec.get("src", "")
        L = L0
        X, Y, TH = state_from_table(rec)
        step = 0
        attempts = 0
        best_L, best_state = None, None
        while step < 30 and attempts < 6 and time.time() - t0 <= budget_s:
            L_try = L - 0.004
            Xs, Ys, Ts = X * (L_try / L), Y * (L_try / L), TH.copy()
            ok, st, mo, mx = try_container(Xs, Ys, Ts, L_try, attempts, n)
            attempts += 1
            if ok:
                L = L_try
                X = np.array([q[0] for q in st])
                Y = np.array([q[1] for q in st])
                TH = np.array([q[2] for q in st])
                best_L, best_state = L, st
                step += 1
                attempts = 0
            else:
                break
        if best_L is not None and best_L < L0 - 1e-9:
            old = finds.get(str(n))
            if old is None or best_L < old["L"] - 1e-12:
                finds[str(n)] = {"L": round(best_L, 12), "state": best_state,
                                 "src": f"pushA:{src}"}
                save_finds("A", finds)
                log("A", f"  n={n}: {L0:.6f} -> {best_L:.6f} (gain {L0-best_L:.4f})")
        done += 1
        if done % 20 == 0:
            log("A", f"  .. {done}/{len(targets)}")
    log("A", f"Stage A complete: {len(finds)} finds, {time.time()-t0:.0f}s")

def stage_b(tab, budget_s):
    """attack open grid-tied targets (skip proven-optimal)."""
    t0 = time.time()
    finds = load_finds("B")
    prov = proven_optimal()
    from math import floor
    targets = []
    for n in range(1, 1001):
        rec = tab[str(n)]
        src = rec.get("src", "").split(":")[0]
        if src != "grid":
            continue
        if n in prov:
            continue
        g = ceil(sqrt(n))
        slack = g - sqrt(n)  # area slack in container units
        targets.append((n, slack))
    targets.sort(key=lambda z: (-z[1], z[0]))  # most area slack first
    log("B", f"Stage B: {len(targets)} attack targets ({len(prov)} proven-optimal skipped)")
    done = 0
    for n, slack in targets:
        if time.time() - t0 > budget_s:
            log("B", f"budget reached at n={n} ({done} done)")
            break
        g = ceil(sqrt(n))
        L = float(g)
        best_L, best_state = None, None
        attempts = 0
        while L > sqrt(n) + 1e-9 and attempts < 8 and time.time() - t0 <= budget_s:
            L_try = L - 0.02
            X, Y, TH = grid_seed(n, L_try, 7919 * n + attempts)
            ok, st, mo, mx = try_container(X, Y, TH, L_try, attempts + 100, n)
            attempts += 1
            if ok:
                L = L_try
                X = np.array([q[0] for q in st])
                Y = np.array([q[1] for q in st])
                TH = np.array([q[2] for q in st])
                best_L, best_state = L, st
                attempts = 0
            else:
                break
        if best_L is not None and best_L < g - 1e-9:
            old = finds.get(str(n))
            if old is None or best_L < old["L"] - 1e-12:
                finds[str(n)] = {"L": round(best_L, 12), "state": best_state,
                                 "src": "pushB:sa"}
                save_finds("B", finds)
                log("B", f"  *** n={n}: grid {g} -> {best_L:.6f} ***")
        done += 1
        if done % 20 == 0:
            log("B", f"  .. {done}/{len(targets)}")
    log("B", f"Stage B complete: {len(finds)} finds, {time.time()-t0:.0f}s")

# ---------------------------------------------------------------- main

def main():
    stage = sys.argv[1] if len(sys.argv) > 1 else "A"
    budget = float(sys.argv[2]) if len(sys.argv) > 2 else 2400.0
    tab = json.load(open(TAB))
    if stage == "A":
        stage_a(tab, budget)
    elif stage == "B":
        stage_b(tab, budget)
    else:
        print("usage: sa_push.py A|B [budget_seconds]")

if __name__ == "__main__":
    main()
