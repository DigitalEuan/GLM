#!/usr/bin/env python3
"""packlib — the single authoritative module for the squares-in-squares pipeline.

Fast vectorized (numpy) verification + scorecard + CSV assembly.

Verification model (mirrors the Kaggle rules):
  - state: list of (x, y, angle); centers + rotation (radians) of unit squares
  - non-overlap: for every pair there exists a SAT axis (an edge normal of
    either square) with |d.axis| >= ext_i + ext_j   (pair penetration <= 0)
  - container L = max(width, height) of the axis-aligned bbox over all corners
  - score(n) = L/sqrt(n) - 1; missing puzzle => grid ceiling ceil(sqrt(n))/sqrt(n)-1

Pair penetration (as in the engine's sat_best): pen = min over the 4 axes
(u_i, v_i, u_j, v_j) of (ext_i + ext_j - |d.axis|).  Overlap iff pen > 0.
worst_pen = max over pairs.  Valid packing: worst_pen <= 0.

Contact policy: generated packings are finalized with a global scale (1+2e-9)
so every touching contact opens a ~2e-9 gap; rounding to 12 dp (error <=2e-12)
can then never flip a contact into an overlap.
"""
import csv
import json
import os
from math import ceil, sqrt

import numpy as np

# -------------------------------------------------------------- verification

def verify(state, tol=0.0):
    """Return dict: ok, worst_pen, L, w, h (see module docstring).

    Math: for squares i, j with frames (u_i, v_i), (u_j, v_j):
      pair penetration = min over the 4 SAT axes of (ext_i + ext_j - |d.axis|).
      Overlap iff pen > 0 on all 4 axes.  worst_pen = max over pairs.
    Facts used (proved by 90-degree rotational invariance):
      ext of the axis-owner square along its own edge = 0.5 exactly;
      ext_j(u_i) == ext_j(v_i)  (so one matrix Eu serves both axes of i).
    """
    state = [(float(s[0]), float(s[1]), float(s[2])) for s in state]
    n = len(state)
    if n == 0:
        return {"ok": True, "worst_pen": 0.0, "L": 0.0, "w": 0.0, "h": 0.0}
    xy = np.array([(s[0], s[1]) for s in state], dtype=float)
    th = np.array([s[2] for s in state], dtype=float)
    cs, sn = np.cos(th), np.sin(th)
    ex = 0.5 * (np.abs(cs) + np.abs(sn))
    lox = float(np.min(xy[:, 0] - ex)); hix = float(np.max(xy[:, 0] + ex))
    loy = float(np.min(xy[:, 1] - ex)); hiy = float(np.max(xy[:, 1] + ex))
    w, h = hix - lox, hiy - loy
    L = max(w, h)
    worst = -np.inf
    if n > 1:
        iu = np.triu_indices(n, k=1)
        # signed projections of all centers onto u_i / v_i (row i's axes):
        # PU[i,j] = c_j . u_i ;  PV[i,j] = c_j . v_i     (rows = axes)
        PU = np.stack([cs, sn], axis=1) @ xy.T
        PV = np.stack([-sn, cs], axis=1) @ xy.T
        # Eu[i,j] = ext of square j along u_i  (== ext_j(v_i), see docstring)
        Eu = 0.5 * (np.abs(np.outer(cs, cs) + np.outer(sn, sn))
                    + np.abs(np.outer(-sn, cs) + np.outer(cs, sn)))
        dU = np.diag(PU)[:, None] - PU        # dU[i,j] = (c_i - c_j).u_i  (signed)
        dV = np.diag(PV)[:, None] - PV        # dV[i,j] = (c_i - c_j).v_i
        # family 0: axes u_i, v_i of square i
        pen_u0 = 0.5 + Eu - np.abs(dU)
        pen_v0 = 0.5 + Eu - np.abs(dV)
        fam0 = np.minimum(pen_u0, pen_v0)
        # family 1: axes u_j, v_j of square j  (swap roles: transpose)
        pen_u1 = 0.5 + Eu.T - np.abs(dU.T)
        pen_v1 = 0.5 + Eu.T - np.abs(dV.T)
        fam1 = np.minimum(pen_u1, pen_v1)
        pair = np.minimum(fam0, fam1)
        worst = float(np.max(pair[iu]))
    ok = (worst <= tol) and bool(np.all(np.isfinite(xy))) and bool(np.all(np.isfinite(th)))
    return {"ok": ok, "worst_pen": float(worst), "L": float(L),
            "w": float(w), "h": float(h)}

def verify_state(state, tol=1e-9):
    r = verify(state, tol=tol)
    return r["ok"], r["L"]

# --------------------------------------------------------- store manipulation

def load_stores(dirpath, names=None):
    if names is None:
        names = ("found.json", "found2.json", "found3.json", "motifs.json",
                 "records.json", "cascade.json")
    merged = {}
    for name in names:
        p = os.path.join(dirpath, name)
        if not os.path.exists(p):
            continue
        data = json.load(open(p))
        for k, rec in data.items():
            n = int(k)
            if n not in merged or rec["L"] < merged[n]["L"] - 1e-12:
                merged[n] = {"L": float(rec["L"]),
                             "state": [tuple(q) for q in rec["state"]]}
    return merged

def save_store(path, store):
    out = {str(n): {"L": round(rec["L"], 12),
                    "state": [[round(v, 12) for v in s] for s in rec["state"]]}
           for n, rec in store.items()}
    json.dump(out, open(path, "w"))

def grid_packing(n):
    k = int(ceil(sqrt(n)))
    st = [(i % k + 0.5, i // k + 0.5, 0.0) for i in range(n)]
    return k, st

def grid_L(n):
    return float(ceil(sqrt(n)))

# ------------------------------------------------------------------ scoring

def score_detail(store, n_min=1, n_max=1000, verify_packings=True):
    detail = {}
    for n in range(n_min, n_max + 1):
        if n in store and len(store[n]["state"]) == n:
            st = store[n]["state"]
            if verify_packings:
                r = verify(st)
                L = r["L"]
                bad = not r["ok"]
            else:
                L = store[n]["L"]; bad = False
            src = "store"
        else:
            k, st = grid_packing(n)
            L = float(k); bad = False; src = "grid"
        detail[n] = {"L": L, "score": L / sqrt(n) - 1, "src": src, "bad": bad,
                     "state": st}
    return detail

def total_score(detail):
    return sum(v["score"] for v in detail.values())

# ------------------------------------------------------------------ CSV I/O

def fmt(v):
    v = round(float(v), 12)
    if v == 0.0:
        return "0"
    s = f"{v:.12f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s

def round_state(state):
    return [(round(float(x), 12), round(float(y), 12), round(float(t), 12))
            for x, y, t in state]

def write_csv(path, detail, n_min=1, n_max=1000):
    rows = []
    rid = 0
    for n in range(n_min, n_max + 1):
        st = detail[n]["state"]
        for sid, (x, y, t) in enumerate(st):
            rows.append((rid, n, sid, fmt(x), fmt(y), fmt(t)))
            rid += 1
    with open(path, "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["id", "n", "square_id", "x", "y", "angle"])
        w.writerows(rows)
    return len(rows)

def read_csv(path):
    by_n = {}
    with open(path) as f:
        for row in csv.DictReader(f):
            n = int(row["n"])
            by_n.setdefault(n, []).append(
                (float(row["x"]), float(row["y"]), float(row["angle"])))
    return by_n

# ----------------------------------------------------- generation helpers

def apply_scale(state, s, anchor="min"):
    """scale the configuration about its bbox min corner by factor s>1."""
    xy = np.array([(p[0], p[1]) for p in state], dtype=float)
    th = np.array([p[2] for p in state], dtype=float)
    ex = 0.5 * (np.abs(np.cos(th)) + np.abs(np.sin(th)))
    lox = float(np.min(xy[:, 0] - ex)); loy = float(np.min(xy[:, 1] - ex))
    return [((x - lox) * s + lox, (y - loy) * s + loy, t) for x, y, t in state]

def finalize(state, gap=2e-9, tries=8):
    """scale+round until the CSV-rounded state has worst_pen <= -1e-12.
    Returns (state_rounded, verify_dict)."""
    st = list(state)
    best = None
    for _ in range(tries):
        st = apply_scale(st, 1.0 + gap / max(1.0, _bboxL(st)))
        stc = round_state(st)
        r = verify(stc)
        best = (stc, r)
        if r["worst_pen"] <= -1e-12:
            return stc, r
        gap *= 4
    return best

def _bboxL(state):
    xy = np.array([(p[0], p[1]) for p in state], dtype=float)
    th = np.array([p[2] for p in state], dtype=float)
    ex = 0.5 * (np.abs(np.cos(th)) + np.abs(np.sin(th)))
    lox = float(np.min(xy[:, 0] - ex)); hix = float(np.max(xy[:, 0] + ex))
    loy = float(np.min(xy[:, 1] - ex)); hiy = float(np.max(xy[:, 1] + ex))
    return max(hix - lox, hiy - loy) or 1.0

if __name__ == "__main__":
    # self-tests
    r = verify(grid_packing(6)[1]);  assert r["ok"] and abs(r["L"] - 3) < 1e-12, r
    print("grid6 OK L=3 worst_pen=", f"{r['worst_pen']:.2e}")
    r = verify(grid_packing(5)[1]);  assert r["ok"] and abs(r["L"] - 3) < 1e-12, r
    print("grid5 OK L=3")
    # overlapping pair must fail
    bad = [(0.5, 0.5, 0.0), (0.9, 0.5, 0.0)]
    r = verify(bad); assert not r["ok"], r
    print("overlap detected: worst_pen=", f"{r['worst_pen']:.3f}")
    # diagonal touching at 45deg
    st = [(0.5, 0.5, 0.0), (0.5 + 0.5 + 0.5 * sqrt(2), 0.5 + 0.5 * sqrt(2), 0.0)]
    r = verify(st); print("45deg touch:", r["ok"], f"worst_pen={r['worst_pen']:.2e}")
    print("self-tests passed")
