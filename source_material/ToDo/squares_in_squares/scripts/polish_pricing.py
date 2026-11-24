#!/usr/bin/env python3
r"""polish_pricing.py — run 117: what does a 1 % capture on the 553 beaten rows
actually cost?

The Director's Note records the tempting arithmetic: the 553 beaten rows leave
15.02 score unclaimed below them, so 1 % of that room is 0.15023 — the whole
0.163635 gap to the reported leader.  This prices the *work*.

Definitions, all per row and exact in intent (the census is float, the verdicts
are not):

    r  = k - sqrt(n)            the room available before the row hits sqrt(n)
    e  = (k - L) / r            the capture the delivered side already takes
    1 % capture  ->  dL = 0.01 r per row, worth dL / sqrt(n) score.

The cost is nothing to do with the score: it is the geometric distance the row
has to move, compared with the distances this project has actually measured
being available:

  * run 111's legal-gap band: every screened row's projection gap sits in
    `6.2e-5 .. 3.3e-4` (doc 72 §6, run 111) — the range in which a local
    squeeze-and-project can win at all;
  * run 108's face-squeeze: `Sigma dL = -2.69e-8` over 33 rows, i.e. `~8e-10`
    per row, and the whole-campaign ceiling of micro-polishing is `7.9e-9`.

So the question "what does 1 % cost" becomes: how many rows need less than the
observed legal gap, and what is the most a polish campaign can possibly pay?
"""
import json
import math
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import sqscore as SQ  # noqa: E402

GAP_LO, GAP_HI = 6.2e-5, 3.3e-4      # run 111's screened legal-gap band
FACE_SQUEEZE = 2.6881e-8             # run 108, total over 33 rows
LEADER_GAP = 0.163635493


def main():
    per = SQ.load()
    rows = []
    for n in range(2, 1001):
        k = SQ.grid(n)
        L = SQ.extent(per[n])
        if L >= k - 1e-12:
            continue
        r = k - math.sqrt(n)
        rows.append({"n": n, "k": k, "L": L, "r": r,
                     "e": (k - L) / r,
                     "dL_1pct": 0.01 * r,
                     "worth_1pct": 0.01 * r / math.sqrt(n),
                     "room": (L - math.sqrt(n)) / math.sqrt(n)})
    tot = sum(x["worth_1pct"] for x in rows)
    room = sum(x["room"] for x in rows)
    print(f"beaten rows {len(rows)}  unclaimed room {room:.5f}  "
          f"1% capture worth {tot:.5f}  leader gap {LEADER_GAP:.6f}")

    dl = sorted(x["dL_1pct"] for x in rows)
    print(f"\n1% capture needs dL per row: min {dl[0]:.5f}  median "
          f"{statistics.median(dl):.5f}  max {dl[-1]:.5f}")
    print(f"capture e already taken: min {min(x['e'] for x in rows):.3f}  median "
          f"{statistics.median([x['e'] for x in rows]):.3f}  max "
          f"{max(x['e'] for x in rows):.3f}")

    print(f"\n  compare with the measured legal-gap band {GAP_LO:.1e} .. {GAP_HI:.1e}:")
    for tag, lim in (("dL <= gap high (3.3e-4)", GAP_HI), ("dL <= 1e-3", 1e-3),
                     ("dL <= 3e-3", 3e-3), ("dL <= 1e-2", 1e-2)):
        sel = [x for x in rows if x["dL_1pct"] <= lim]
        print(f"   rows needing {tag:26s}: {len(sel):3d}   worth "
              f"{sum(x['worth_1pct'] for x in sel):.5f}")
    print(f"   rows needing more than the whole band: "
          f"{len([x for x in rows if x['dL_1pct'] > GAP_HI])}")

    # the realistic ceiling: every row moves by at most the top of the gap band
    ceil_band = sum(min(x["dL_1pct"], GAP_HI) / math.sqrt(x["n"]) for x in rows)
    print(f"\n  if EVERY row could be polished by the band's ceiling {GAP_HI:.1e}: "
          f"{ceil_band:.5f} score")
    print(f"  if every row could be polished by the band's floor {GAP_LO:.1e}: "
          f"{sum(min(x['dL_1pct'], GAP_LO) / math.sqrt(x['n']) for x in rows):.5f}")
    print(f"  face-squeeze alone (run 108, {FACE_SQUEEZE:.2e} total): "
          f"{FACE_SQUEEZE:.2e} score")
    print(f"  -> a 1% capture costs {tot / ceil_band:.1f}x the best-case polish "
          f"ceiling, and {tot / FACE_SQUEEZE:.0f}x the entire face-squeeze campaign")

    # where the 1% money actually sits: by capture band
    print("\n  who carries the 1% worth (by current capture e):")
    for lo, hi in ((0.0, 0.1), (0.1, 0.2), (0.2, 0.3), (0.3, 0.4), (0.4, 0.5)):
        sel = [x for x in rows if lo <= x["e"] < hi]
        if sel:
            print(f"   e in [{lo:.1f},{hi:.1f}): {len(sel):3d} rows, worth "
                  f"{sum(x['worth_1pct'] for x in sel):.5f}, dL median "
                  f"{statistics.median([x['dL_1pct'] for x in sel]):.5f}")

    out = os.path.join(ROOT, "workspace/push/polish_pricing117.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump({"rows": rows, "total_1pct": tot, "room": room,
               "gap_band": [GAP_LO, GAP_HI], "ceiling_band": ceil_band,
               "leader_gap": LEADER_GAP}, open(out, "w"), indent=1)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
