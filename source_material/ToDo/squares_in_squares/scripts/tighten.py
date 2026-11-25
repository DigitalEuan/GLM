"""Run 132: the bounded tightening pass on the top-leverage beaten rows.

`beaten_leverage.py` settles the *coordinated shift* half of run 132's brief
exactly: every one of the 551 beaten poses is at contact (`g = 1` to within
`finalize`'s 1.8e-9 pad), so a uniform contraction buys the pad and nothing
else.  That leaves the other half -- rearrangement with the angles free.

Per row and per seed, this runs the repo's own squeeze-and-project attempt
from the **delivered** pose (`structure.attempt`, which relaxes `(x, y, t)` in
patches, so angles move), then measures the projected pose at 40 digits
(`p_screen.measure`) and hands it to the exact legal-move stage
(`p_screen.convert`: minimum legal scale, band slides, exact tightening).  The
number reported is `dL = L0 - L_final`, so **positive is a gain**; a row is
promoted only if `dL > 0` and the whole-pose certificate passes, which

    dL = delta - payback,   payback ~ 0.83 * p * L

(doc 87's law) makes very unlikely on a pose that starts at contact: the
squeeze has to manufacture `p ~ delta` of overlap, and the payback then exceeds
`delta` for every `L > 1.2`.  The run's job is to measure that, not to assume
it.
"""

from __future__ import annotations

import json
import os
import sys
import time
from decimal import Decimal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import beaten_leverage as BL         # noqa: E402
import legal_slide as LSL            # noqa: E402
import p_screen as PS                # noqa: E402
import structure as ST               # noqa: E402

OUT = os.path.join(BL.ROOT, "workspace", "push", "tighten132.json")


def one(n, seconds, seed, budget_left):
    """One attempt at row `n`: squeeze from the delivered pose, then legalise."""
    L0 = ST.load_pose(n)[3]
    pose_out = []
    rec = ST.attempt(n, 0, seconds, seed, pose_out=pose_out)
    m = PS.measure(pose_out[0])      # `attempt` appends the pose as one list
    deadline = time.monotonic() + budget_left
    conv = PS.convert(m["state"], m["dirs"], L0, m["side"], deadline)
    out = {"n": n, "seed": seed, "L0": str(L0), "p": str(m["p"]),
           "violations_after_projection": m["violations"],
           "squeeze_side": str(m["side"]),
           "squeezes": rec.get("squeezes"), "record": None}
    if conv.get("convertible") is None and not conv.get("dL"):
        out["convert"] = conv
        return out
    out["convert"] = {k: v for k, v in conv.items() if k != "state"}
    out["dL"] = conv.get("dL")
    out["certified"] = conv.get("certified")
    return out


def main(argv) -> int:
    rows, _excluded = BL.rank(BL.load_table())
    want = argv[argv.index("--rows") + 1] if "--rows" in argv else "8"
    ns = [int(x) for x in want.split(",")] if "," in want else \
        [r["n"] for r in rows[:int(want)]]
    seconds = float(argv[argv.index("--seconds") + 1]) if "--seconds" in argv else 15.0
    seeds = [int(x) for x in argv[argv.index("--seed") + 1].split(",")] \
        if "--seed" in argv else [0]
    results = []
    for n in ns:
        for seed in seeds:
            t0 = time.monotonic()
            r = one(n, seconds, seed, 60.0)
            r["seconds"] = round(time.monotonic() - t0, 1)
            results.append(r)
            dl = r.get("dL")
            print(f"  n={n:4d} seed={seed} p={Decimal(r['p']):+.3e} "
                  f"dL={'n/a' if dl is None else format(Decimal(dl), '+.3e')} "
                  f"({r['seconds']}s)", flush=True)
    gains = [Decimal(r["dL"]) for r in results if r.get("dL") is not None]
    pos = [g for g in gains if g > 0]
    print(f"[tighten] {len(results)} attempts, {len(gains)} converted, "
          f"{len(pos)} positive dL, "
          f"max dL {max(gains) if gains else 'n/a'}, "
          f"median {sorted(gains)[len(gains)//2] if gains else 'n/a'}")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump({"attempts": results, "rows": ns, "seconds": seconds,
                   "seeds": seeds}, f, indent=1)
    print(f"[write] {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
