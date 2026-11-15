#!/usr/bin/env python3
r"""deletion_scan.py — read the set backwards (GLM round, 15 Nov 2026).

The insertion engine grew row n from row n-1 (the owner's reading: the answer to
a row is outlined by the set above it).  This is the other direction, and it is
the one that can actually find score, because the set ABOVE a row is *richer*
than the row itself: a packing of n+1 squares, reduced by deleting one square,
is a valid packing of n squares — no search, no repair, just a rectangle.

For each n and each donor row n' in {n+1 .. n+max_ahead}, every single deletion is
scored exactly (bbox of the survivors), and the best few are then *settled*: the
rotation LP plus rewiring is run on the survivor set, which can beat the raw
deletion because deleting a square leaves a slack arrangement with room to
compact.  A candidate counts only if `packlib.finalize` + `packlib.verify` accept
it with the right square count and a strictly smaller side.

That makes this scan three things at once: a search (deletion), a family
transfer (structure from a larger row), and a test of the owner's grouping claim
in reverse — if row n's best comes from row n+k, its motif belongs to the block
above it.

    python3 scripts/deletion_scan.py --max-n 1000 --ahead 4
    python3 scripts/deletion_scan.py --apply        # write a verified candidate
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import packlib as P                                      # noqa: E402
import rotation_lp as R                                  # noqa: E402


def extents(th):
    return 0.5 * (np.abs(np.cos(th)) + np.abs(np.sin(th)))


def del_bboxes(st):
    """Side of the bbox after deleting each single square; returns (m,) array."""
    xy = st[:, :2]
    e = extents(st[:, 2])
    hi_x, lo_x = xy[:, 0] + e, xy[:, 0] - e
    hi_y, lo_y = xy[:, 1] + e, xy[:, 1] - e

    def excl_max(v):
        order = np.argsort(v)
        top = order[-1]
        second = order[-2] if len(v) > 1 else order[-1]
        out = np.full(len(v), v[top])
        out[top] = v[second]
        return out

    def excl_min(v):
        order = np.argsort(v)
        low = order[0]
        second = order[1] if len(v) > 1 else order[0]
        out = np.full(len(v), v[low])
        out[low] = v[second]
        return out

    return np.maximum(excl_max(hi_x) - excl_min(lo_x), excl_max(hi_y) - excl_min(lo_y))


def scan(max_n: int, ahead: int, near: float, settle_top: int, apply: bool,
         compact: bool) -> int:
    sub = P.read_csv(os.path.join(ROOT, "workspace/submission/submission.csv"))
    tab = {n: P.verify(sub[n])["L"] for n in range(1, 1001)
           if n in sub and len(sub[n]) == n}
    wins, tried, near_hits = [], 0, 0
    for n in sorted(tab):
        if n > max_n:
            continue
        tried += 1
        cands = []
        for donor in range(n + 1, min(n + ahead, 1000) + 1):
            if donor not in tab:
                continue
            st = np.array(sub[donor], dtype=float)
            if len(st) != donor:
                continue
            sides = del_bboxes(st)
            order = np.argsort(sides)
            for k in order[:2]:
                cands.append((float(sides[k]), donor, int(k)))
        if not cands:
            continue
        cands.sort()
        best = None
        for side, donor, kdel in cands[:max(1, settle_top)]:
            st = np.array(sub[donor], dtype=float)
            survivors = np.delete(st, kdel, axis=0)
            r = P.verify([tuple(map(float, q)) for q in survivors])
            cand_state = survivors
            if side <= tab[n] + near:
                near_hits += 1
                if compact:
                    c2, r2, _ = R.compact(survivors, rounds=6, touch=0.08,
                                          rot=0.04, pos=0.08)
                    if r2["ok"] and len(c2) == n and r2["L"] < r["L"] - 1e-12:
                        cand_state, r = c2, r2
            if not r["ok"] or len(cand_state) != n:
                continue
            if r["L"] < tab[n] - 1e-9:
                fin, rr = P.finalize([tuple(map(float, q)) for q in cand_state])
                if rr["ok"] and rr["L"] < tab[n] - 1e-9:
                    gain = (tab[n] - rr["L"]) / math.sqrt(n)
                    if best is None or rr["L"] < best[1]["L"]:
                        best = (fin, rr, donor, kdel, gain)
        if best is not None:
            fin, rr, donor, kdel, gain = best
            wins.append({"n": n, "L_before": tab[n], "L_after": rr["L"], "gain": gain,
                         "donor": donor, "deleted": kdel,
                         "state": [[float(a), float(b), float(c)] for a, b, c in fin]})
            print(f"  WIN n={n}: {tab[n]:.9f} -> {rr['L']:.9f}  (row {donor},"
                  f" delete {kdel})  gain {gain:.3e}", flush=True)
    path = os.path.join(ROOT, "workspace/push/deletion_scan.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump({"found": wins, "rows_tried": tried, "near_hits": near_hits,
               "score_gain": sum(w["gain"] for w in wins),
               "params": {"ahead": ahead, "near": near, "settle_top": settle_top,
                          "compact": compact}}, open(path, "w"), indent=1)
    print(f"rows tried: {tried}; deletions within {near} of the table: {near_hits};"
          f" wins: {len(wins)}; gain {sum(w['gain'] for w in wins):.9f}")
    if apply and wins:
        detail = {}
        for nn in range(1, 1001):
            st = sub[nn] if nn in sub and len(sub[nn]) == nn else P.grid_packing(nn)[1]
            detail[nn] = {"state": [(float(a), float(b), float(c)) for a, b, c in st],
                          "L": P.verify(st)["L"]}
        for w in wins:
            detail[w["n"]]["state"] = [tuple(q) for q in w["state"]]
            detail[w["n"]]["L"] = w["L_after"]
        out = os.path.join(ROOT, "workspace/submission/submission_del.csv")
        P.write_csv(out, detail)
        print(f"wrote candidate {out} with {len(wins)} improved rows")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-n", type=int, default=1000)
    ap.add_argument("--ahead", type=int, default=4)
    ap.add_argument("--near", type=float, default=0.02)
    ap.add_argument("--settle-top", type=int, default=3)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--no-compact", action="store_true")
    args = ap.parse_args()
    return scan(args.max_n, args.ahead, args.near, args.settle_top, args.apply,
                not args.no_compact)


if __name__ == "__main__":
    raise SystemExit(main())
