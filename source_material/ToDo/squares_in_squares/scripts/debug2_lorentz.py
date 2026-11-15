#!/usr/bin/env python3
"""debug2_lorentz.py — pinpoint the claim/fresh inconsistency.
Runs the engine chain stage by stage on the n=6 probe, validating each
sub-engine's return: claim == recomputed objective on returned arrays.
Prints the first stage that fails."""
import math
import sys

import numpy as np

sys.path.insert(0, "/home/z/my-project/scripts")
import packlib as P
from cent_engines import engine_p11_piezo
from lorentz_lift import (bisector_reflection_moves, build_grid_sites,
                           build_diamond_sites, global_obj, seed_local,
                           assign_all, snap, context_break)


def chk(name, tup, L):
    o, X, Y, TH = tup
    fresh = global_obj(X, Y, TH, L)
    ok = abs(fresh - o) < 1e-9
    print(f"  {name}: claim={o:.6e} fresh={fresh:.6e} "
          f"{'OK' if ok else '*** INCONSISTENT ***'}")
    return ok


def main():
    n, L, seed = 6, 2.998, 7919 * 6 + 1
    rng = np.random.RandomState(seed)
    X, Y, TH = seed_local(n, L, seed)
    sites = build_grid_sites(n, L) + build_diamond_sites(L)
    print(f"sites: {len(sites)} (grid {len(build_grid_sites(n, L))}, "
          f"diamond {len(build_diamond_sites(L))})")
    for rnd in range(3):
        print(f"round {rnd}:")
        choice, ties = assign_all(X, Y, TH, sites, n)
        X, Y, TH = snap(X, Y, TH, choice, sites, n)
        print(f"  snap: obj={global_obj(X, Y, TH, L):.6e} ties={len(ties)}")
        if ties:
            context_break(X, Y, TH, L, rng, ties, choice, sites, n,
                          max_look=3 + rnd)
            print(f"  after context: obj={global_obj(X, Y, TH, L):.6e}")
        t1 = engine_p11_piezo(X, Y, TH, L, rng, iters=60, eta=0.15)
        if not chk(f"piezo1 r{rnd}", t1, L):
            return
        o, X, Y, TH = t1
        b = bisector_reflection_moves(X, Y, TH, L, rng, sites, n,
                                      iters=120 + 60 * rnd)
        if not chk(f"bisect r{rnd}", b, L):
            return
        if b[0] < o:
            o, X, Y, TH = b
        t2 = engine_p11_piezo(X, Y, TH, L, rng, iters=80, eta=0.1)
        if not chk(f"piezo2 r{rnd}", t2, L):
            return
        if t2[0] < o:
            o, X, Y, TH = t2
        print(f"  round best: {o:.6e}")
    print("done")


if __name__ == "__main__":
    main()
