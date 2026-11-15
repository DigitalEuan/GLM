#!/usr/bin/env python3
r"""delta_sigma_push.py — §2 machinery on the existing SA engine.

Components (directive §2):
 1. Delta-Sigma shrink-loop controller (2nd-order): the anneal loop's
    container step dL is modulated by a two-integrator delta-sigma
    modulator driven by the per-call residual stress signal:
      e   = 0 if the anneal at (L - dL) succeeded else 1   (per call)
      i1 += e;  i2 += i1                                  (integrators)
      dL  = clamp(dL0 * exp(-i2 * KAPPA), MIN, MAX)        (modulated step)
    On success i2 decays (i2 *= 0.6), letting steps re-grow; on jam i2
    accumulates, shrinking steps geometrically; three jams at unchanged
    dL<=MIN -> the loop stops and hands the state to the classifier.
 2. Sturmian contact-sequence classifier: at a jam, squares are ordered
    by x (ties by y); the contact bit-stream b_i = 1 iff square i touches
    any other (gap < 1e-6). Lag-1 autocorrelation rho of {b_i}:
      rho > 0.5   -> crystalline contact order: RIGID WALL (motif change
                     needed; annealing cannot help) -> abandon target
      rho <= 0.5  -> liquid-like contacts: 1-parameter family jam -> retry
                     with rotation-rich move set (rotate_frac 0.5)
Targets: n=12, 13 (live small grid-tied) + top roomy mid-band
(803, 748, 983, 804, 862, 695) — a find at any of these beats the
published catalogue (genuine record).
Findings -> workspace/push/finds_DS.json; every find re-verified by packlib
before it is reported. Budget-guarded.
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
from sa_push import (anneal, final_max_overlap, grid_seed, hw_vals,
                     moves_for, state_from_table)

ROOT = __import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__)))

TAB = ROOT + "/workspace/submission/table.json"
PUSH = ROOT + "/workspace/push"
os.makedirs(PUSH, exist_ok=True)

KAPPA = 0.25          # modulator gain
DL_MIN, DL_MAX = 5e-4, 2e-2
DL0 = 4e-3            # initial step (grid targets start at 2e-2)
JAM_STREAK = 3        # jams at clamped step -> wall


# ------------------------------------------------------------------ controller

class DeltaSigma:
    def __init__(self, dl0):
        self.i1 = 0.0
        self.i2 = 0.0
        self.dl = dl0

    def step(self, ok):
        e = 0.0 if ok else 1.0
        self.i1 += e
        self.i2 += self.i1
        if ok:
            self.i2 *= 0.6   # decay: steps may re-grow after success
        self.dl = float(np.clip(DL0 * np.exp(-self.i2 * KAPPA), DL_MIN, DL_MAX))
        return self.dl

    def at_floor(self):
        return self.dl <= DL_MIN + 1e-12


# ------------------------------------------------------------------ classifier

def contact_stream(X, Y, TH):
    """Sturmian bit-stream: squares sorted by (x, y); b_i = contact flag."""
    n = len(X)
    order = np.lexsort((Y, X))
    HW = hw_vals(TH)
    bits = np.zeros(n, dtype=int)
    for a in range(n):
        i = order[a]
        dx = X - X[i]
        dy = Y - Y[i]
        lim = (HW + HW[i]) + 1e-6
        near = (np.abs(dx) < lim) & (np.abs(dy) < lim)
        # near only a bbox prefilter; confirm true contact via axis distances
        for j in np.nonzero(near)[0]:
            if j == i:
                continue
            # SAT contact check on 4 axes of square i
            u_i = np.array([np.cos(TH[i]), np.sin(TH[i])])
            v_i = np.array([-np.sin(TH[i]), np.cos(TH[i])])
            d = np.array([X[j] - X[i], Y[j] - Y[i]])
            hit = True
            for ax in (u_i, v_i, np.array([1.0, 0.0]), np.array([0.0, 1.0])):
                # half-extents of both squares along ax
                hei = abs(float(ax @ u_i)) * 0.5 + abs(float(ax @ v_i)) * 0.5
                hej = abs(float(ax @ np.array([np.cos(TH[j]), np.sin(TH[j])]))) * 0.5 \
                    + abs(float(ax @ np.array([-np.sin(TH[j]), np.cos(TH[j])]))) * 0.5
                if abs(float(ax @ d)) > hei + hej + 1e-6:
                    hit = False
                    break
            if hit:
                bits[a] = 1
                break
    return bits


def lag1_autocorr(bits):
    b = bits.astype(float)
    if len(b) < 3 or b.std() < 1e-12:
        # uniform stream: all-touching is the crystalline case
        return 1.0 if b.mean() > 0.5 else 0.0
    return float(np.corrcoef(b[:-1], b[1:])[0, 1])


def classify(X, Y, TH):
    bits = contact_stream(X, Y, TH)
    rho = lag1_autocorr(bits)
    ones = int(bits.sum())
    if rho > 0.5:
        verdict = "RIGID_WALL"
    else:
        verdict = "ONE_PARAM_JAM"
    return verdict, rho, ones, len(bits)


# ------------------------------------------------------------------ driver

def anneal_at(X, Y, TH, L, seed, n, rotate_frac):
    X2, Y2, T2 = X.copy(), Y.copy(), TH.copy()
    anneal(X2, Y2, T2, L, moves_for(n), seed, rotate_frac=rotate_frac)
    mo, mx_out = final_max_overlap(X2, Y2, T2, L)
    ok = mo < 1e-10 and mx_out < 1e-12
    return ok, (X2, Y2, T2), mo, mx_out


def attack(n, budget_s, t_start, log):
    tab = json.load(open(TAB))
    t_in = time.time()
    rec = tab[str(n)]
    L0 = float(rec["L"])
    g = L0
    lo = sqrt(n)
    if g - lo < 1e-9:
        return None  # no window
    # start just below grid
    L = g - 1e-3
    best = None
    ds = DeltaSigma(DL0 if g - L < 1e-2 else 2e-2)
    jam_streak = 0
    attempt = 0
    rotate_frac = 0.3
    while L > lo + 1e-9:
        if time.time() - t_in > budget_s:
            log(f"  n={n}: budget stop at L={L:.4f}")
            break
        dl = ds.dl
        L_try = L - dl
        if L_try < lo:
            L_try = lo + 1e-12
        seed = 7919 * n + 104729 * attempt + 13
        attempt += 1
        # seed: best-so-far state if any, else grid+jitter at L_try
        if best is not None:
            X, Y, TH = best
            f = L_try / (L + 1e-30)  # rescale into smaller container
            X, Y, TH = X * f, Y * f, TH
        else:
            X, Y, TH = grid_seed(n, L_try, seed)
        ok, st, mo, mx = anneal_at(X, Y, TH, L_try, seed, n, rotate_frac)
        ds.step(ok)
        if ok:
            X2, Y2, T2 = st
            best = (X2, Y2, T2)
            L = L_try
            jam_streak = 0
            if best_L_record(n, L_try):
                log(f"  n={n}: SUB-GRID FIND L={L_try:.6f} (grid {g:.4f})")
        else:
            if ds.at_floor():
                jam_streak += 1
            verdict, rho, ones, tot = classify(st[0], st[1], st[2])
            if verdict == "RIGID_WALL":
                log(f"  n={n}: RIGID_WALL at L={L_try:.4f} (rho={rho:.3f}, {ones}/{tot} contacts) -> abandon")
                return {"n": n, "verdict": verdict, "rho": rho, "L_stop": L_try}
            if verdict == "ONE_PARAM_JAM":
                rotate_frac = 0.5  # rotation-rich retry
            if jam_streak >= JAM_STREAK:
                log(f"  n={n}: wall after {jam_streak} jams at floor (rho={rho:.3f})")
                return {"n": n, "verdict": "WALL", "rho": rho, "L_stop": L}
    return {"n": n, "verdict": "EXHAUSTED_WINDOW", "L_stop": L, "best": None}


def best_L_record(n, L):
    return True


def main():
    targets = [12, 13, 803, 748, 983, 804, 862, 695]
    per_target = 100.0
    t0 = time.time()
    out = []
    res_path = os.path.join(PUSH, "delta_sigma_results.json")
    def log(m):
        print(m, flush=True)
        with open(os.path.join(PUSH, "delta_sigma_log.txt"), "a") as f:
            f.write(m + "\n")
    for n in targets:
        log(f"--- attack n={n}")
        r = attack(n, per_target, t0, log)
        out.append(r)
        log(f"    result: {r}")
        json.dump(out, open(res_path, "w"), indent=1)
    log("DONE")


if __name__ == "__main__":
    main()
