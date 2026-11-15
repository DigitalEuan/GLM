#!/usr/bin/env python3
r"""t263_polish.py — run 30: P2 renewed for the T-263 family (NEXT_STEPS §4 P2).

The one bounded re-run the SAT review asked for: n = 299/334/371
(the register record T-263 and its chain3 children) carry 41 free
squares each at Maxwell ratio 0.68 — imported after the runs-23-25
polish campaign, never polish-seeded.

Method (same engine as runs 23-25, honest A/B — only the seed differs):
  seed  = the table state itself (register n-299 / chain3 334, 371);
  ladder L_t = row L - delta, delta in {0.002, 0.005, 0.01} — the
          squeeze that closes the floaters' quasi-contacts (median
          gap 0.0035) and forces contact-graph re-breaking;
  hop loop (soft_relax.hop_search shape): cold settle at L_t, then
          alternate hot shuffle (sa_push.anneal, soft space — pass-
          through is the re-breaking) and re-hardening settle at L_t;
  hard state = P.verify worst_pen <= -1e-10; score = its own extent.
  Find gate: best hard extent < table L - 1e-9, then packlib.finalize
  (scale+round, worst_pen <= -1e-12 required).

Run-29 falsifiable prediction under test (NEXT_STEPS §2b.4): any
improved packing should come with phi down / NRCI up (toward the tied
language).  Every hard state is measured (g, phi, NRCI, regime) via
scripts/sat_measure.py review_row — phi up on an improvement falsifies
the two-phase picture.

Ledger: workspace/push/t263_polish30.json (resumable: cells appended,
re-running skips finished cells).
"""
import json
import math
import os
import sys
import time

import numpy as np

sys.path.insert(0, "/home/z/my-project/scripts")
import packlib as P
from oracle_basin import settle_to
from sa_push import anneal
from soft_relax import unpack, PHI
from sat_measure import review_row, Q, B

W = "/home/z/my-project"
TAB = f"{W}/workspace/submission/table.json"
OUT = f"{W}/workspace/push/t263_polish30.json"
ROWS = [int(x) for x in os.environ.get("T263_ROWS", "299,334,371").split(",")]
LADDER = (0.002, 0.005, 0.01)
SEEDS = {299: (0, 1), 334: (0,), 371: (0,)}     # 2nd stream on the record row
MOVES = 6000                                    # ~17s per hot shuffle at n=299
HOPS = 6
PHI_HALF = math.pi / 2


def pack(state):
    return np.array([s[0] for s in state] + [s[1] for s in state]
                    + [s[2] for s in state], dtype=float)


def hop_loop(q0, L_t, seed, n, L0):
    """hop_search shape, seeded from the table state. The find gate is
    finalize-based (polish.py / finalize_gate doctrine): every even-hop
    settle output with extent < L0 is a candidate; the best-extent
    candidate goes through packlib.finalize (scale+round, requires
    worst_pen <= -1e-12).  A settle state at exact tangency passes
    (2e-9 relative scale-up separates it); a state with real overlaps
    deeper than ~1e-5 relative fails.  hard_hops kept for A/B with
    runs 23-25 (81 cells, 0 hard there too — the strict-separation
    in-loop gate never fires; see ledger note).
    Returns (best (final_L, state) or None, hard, checks, soft_best)."""
    q = q0.copy()
    best = None
    cand_ext = math.inf
    cand_q = None
    hard = 0
    checks = 0
    soft_best = math.inf
    for h in range(HOPS):
        if h == 0:
            q, _f = settle_to(q, L_t, iters=250)
        elif h % 2 == 1:
            X, Y, TH = unpack(q)
            anneal(X, Y, TH, L_t, MOVES, seed * 1009 + h,
                   t0=0.30 if (h // 2) % 2 == 0 else 0.45,
                   tend=0.02, rotate_frac=0.5)
            q = np.concatenate([X, Y, TH])
            continue
        else:
            q, _f = settle_to(q, L_t, iters=250)
        checks += 1
        st = [(float(q[i]), float(q[n + i]), float(q[2 * n + i]) % PHI)
              for i in range(n)]
        r = P.verify(st, tol=1e-9)
        if r["worst_pen"] <= -1e-10:
            hard += 1
        if r["L"] < cand_ext:
            cand_ext = float(r["L"])
            cand_q = q.copy()
        if r["L"] < soft_best:
            soft_best = float(r["L"])
    # finalize gate on the best-extent settle state
    if cand_q is not None and cand_ext < L0 - 1e-9:
        stc = [(float(cand_q[i]), float(cand_q[n + i]),
                float(cand_q[2 * n + i]) % PHI) for i in range(n)]
        stf, rf = P.finalize(stc, gap=2e-9)
        if rf["ok"] and rf["worst_pen"] <= -1e-12 and rf["L"] < L0 - 1e-9:
            best = (float(rf["L"]), stf)
    return best, hard, checks, soft_best


def measure(state, n):
    r = review_row(state, n)
    return {"L": r["L"], "C": r["C"], "g": r["g"], "phi": r["phi"],
            "TAX": r["TAX"], "NRCI": r["NRCI"], "regime": r["regime"],
            "census": r["census"]}


def main():
    tab = json.load(open(TAB))
    led = json.load(open(OUT)) if os.path.exists(OUT) else {"cells": []}
    done = {(c["n"], c["delta"], c["seed"]) for c in led["cells"]}
    t_start = time.time()

    for n in ROWS:
        L0 = tab[str(n)]["L"]
        state0 = tab[str(n)]["state"]
        q0 = pack(state0)
        if "baseline" not in led or led.get("baseline", {}).get(n) is None:
            led.setdefault("baseline", {})[str(n)] = measure(state0, n)
        print(f"--- n={n} L0={L0:.9f} baseline "
              f"g={led['baseline'][str(n)]['g']} phi={led['baseline'][str(n)]['phi']:.4f} "
              f"NRCI={led['baseline'][str(n)]['NRCI']:.4f}", flush=True)
        for delta in LADDER:
            for seed in SEEDS.get(n, (0,)):
                if (n, delta, seed) in done:
                    print(f"  cell n={n} d={delta} s={seed}: skip (done)",
                          flush=True)
                    continue
                if time.time() - t_start > 540:   # bounded: stop before cutoff
                    print("  budget: stopping early, resumable", flush=True)
                    json.dump(led, open(OUT, "w"), indent=1)
                    return finish(led)
                L_t = L0 - delta
                t0 = time.time()
                best, hard, checks, soft_best = hop_loop(q0, L_t, seed, n, L0)
                cell = {"n": n, "delta": delta, "seed": seed, "L_t": L_t,
                        "hard_hops": hard, "checks": checks,
                        "soft_best_extent": round(soft_best, 9),
                        "secs": round(time.time() - t0, 1)}
                if best is not None:
                    m = measure(best[1], n)
                    cell["best_extent"] = best[0]
                    cell["measure"] = m
                    print(f"  n={n} d={delta} s={seed}: FIND "
                          f"L={best[0]:.9f} (table {L0:.9f}) "
                          f"phi {m['phi']:.4f} NRCI {m['NRCI']:.4f} "
                          f"[{time.time()-t0:.0f}s]", flush=True)
                else:
                    print(f"  n={n} d={delta} s={seed}: 0 hard in {checks} "
                          f"(soft best {soft_best:.6f}) [{time.time()-t0:.0f}s]",
                          flush=True)
                led["cells"].append(cell)
                json.dump(led, open(OUT, "w"), indent=1)

    finish(led)


def finish(led):
    """Find gate over all cells; returns True if a find was applied."""
    tab = json.load(open(TAB))
    finds = []
    for c in led["cells"]:
        if "best_extent" not in c:
            continue
        n, L0 = c["n"], tab[str(c["n"])]["L"]
        if c["best_extent"] < L0 - 1e-9:
            finds.append(c)
    led["finds"] = [
        {k: c[k] for k in ("n", "delta", "seed", "best_extent", "measure")}
        for c in finds]
    print(f"\nfind gate: {len(finds)} candidate(s) below table L")
    for c in finds:
        print(f"  n={c['n']} d={c['delta']} s={c['seed']}: extent "
              f"{c['best_extent']:.9f} | phi {c['measure']['phi']:.4f} "
              f"NRCI {c['measure']['NRCI']:.4f}")
    json.dump(led, open(OUT, "w"), indent=1)
    print("ledger ->", OUT)
    return bool(finds)


if __name__ == "__main__":
    main()
