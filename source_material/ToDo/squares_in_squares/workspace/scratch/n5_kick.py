"""Scratch: which collective kick reaches 4-upright + 1-diamond at n=5?"""
import math
import sys

import numpy as np

sys.path.insert(0, "scripts")
import packlib as P
import cram_relax as CR
from cent_discovery import rsa_seed

N = 5
LT = 2.7081
PHI = math.pi / 2


def gate(st):
    r = P.verify([(float(a), float(b), float(c)) for a, b, c in np.asarray(st, float)])
    return bool(r["ok"]), float(r["worst_pen"]), float(r["L"])


def settle(st, L, moves=6000):
    st = CR.relax(np.asarray(st, float), L, moves=moves, seed=1, t0=0.02)
    pol = CR.coordinate_polish(st, L, sweeps=8)
    st = pol[0] if isinstance(pol, tuple) else pol
    return np.asarray(st, float)


def report(tag, st):
    ok, wp, L = gate(st)
    print(f"  {tag:34s} ok={str(ok):5s} worst_pen={wp:+.3e} L={L:.6f}", flush=True)
    return ok, L


def strain_order(st, L):
    return list(np.argsort(CR.local_strain(st, L))[::-1])


def hole_center(st, L, i, ang):
    """Best placement for body i among the others at angle `ang`."""
    others = np.array([j for j in range(len(st)) if j != i])
    trial = st.copy()
    trial[i, 2] = ang
    xs = np.linspace(0.0, L, 61)
    best, bestp = None, None
    for x in xs:
        for y in xs:
            trial[i, 0], trial[i, 1] = x, y
            pen = CR.margin_matrix(trial)
            cost = float(np.sum(np.maximum(0.0, pen[others, i]) ** 2))
            # prefer a central spot when ties (max min-distance to others)
            d = np.min(np.hypot(st[others, 0] - x, st[others, 1] - y))
            key = (cost, -d)
            if bestp is None or key < bestp:
                bestp, best = key, (x, y)
    return best


def v_rot(st, L, m, ang=math.pi / 4):
    s = st.copy()
    for i in strain_order(st, L)[:m]:
        s[i, 2] = ang
    return s


def v_swap(st, L, m, ang=math.pi / 4):
    s = st.copy()
    top = strain_order(st, L)[:m]
    pos = s[top, :2].copy()
    s[top, :2] = np.roll(pos, 1, axis=0)
    s[top, 2] = ang
    return s


def v_hole(st, L, ang=math.pi / 4):
    s = st.copy()
    i = strain_order(st, L)[0]
    x, y = hole_center(s, L, i, ang)
    s[i, 0], s[i, 1], s[i, 2] = x, y, ang
    return s


def v_global(st, L, ang=math.pi / 4):
    s = st.copy()
    c = s[:, :2].mean(axis=0)
    d = s[:, :2] - c
    R = np.array([[math.cos(ang), -math.sin(ang)], [math.sin(ang), math.cos(ang)]])
    s[:, :2] = d @ R.T + c
    s[:, 2] += ang
    return s


def print_state(tag, st):
    print(f"    {tag}: " + "  ".join(
        f"({a:.3f},{b:.3f},{c:.3f})" for a, b, c in st), flush=True)


print("target L =", LT)
for sd in (1, 2):
    rng = np.random.RandomState(7919 * N + sd)
    q = rsa_seed(N, LT + 0.45, rng)
    st = np.stack([q[:N], q[N:2 * N], q[2 * N:]], axis=1) % math.pi
    st = settle(st, LT)
    print(f"\nseed {sd}:")
    report("settled", st)
    print_state("  state", st)
    for name, fn in (("rot1", lambda s: v_rot(s, LT, 1)),
                     ("rot2", lambda s: v_rot(s, LT, 2)),
                     ("swap2", lambda s: v_swap(s, LT, 2)),
                     ("swap3", lambda s: v_swap(s, LT, 3)),
                     ("hole", lambda s: v_hole(s, LT)),
                     ("global45", lambda s: v_global(s, LT))):
        try:
            s2 = settle(fn(st), LT)
            ok, L = report(name, s2)
            if ok and L <= LT:
                print_state(name, s2)
        except Exception as e:  # noqa: BLE001
            print(f"  {name}: ERR {e}")
