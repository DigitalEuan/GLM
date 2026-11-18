#!/usr/bin/env python3
r"""pl32_base.py — PL-32: find an r = 1 base with slack below 0.520815, gate it,
carry it through the cascade to every row of the column, and report the measured
score change.

The delivered column n = k^2 + 1 has

    k = 2..24   slack 0.5355 (k=2: 0.7071)
    k = 25..31  slack 0.520815 (this is SLACK_BEAT)

A cascade base at k0 with slack delta gives L = k + delta for every k >= k0, so a
base with delta < 0.520815 at some k0 <= 24 improves rows above it. The band step
is exact: from a packing of k^2+1 squares in [0, k+delta]^2, add the k+1 squares
(i+1/2, k+delta+1/2) and the k squares (k+delta+1/2, j+1/2) for j < k, giving
(k+1)^2+1 squares in [0, k+1+delta]^2 — the added 2k+1 squares lie in the two
strips outside the old box, so containment is exact by construction and every
band is gated with packlib anyway.

Search (per k = 8..25): from the delivered state at n = k^2+1, push into side
L_t = k + min(cur_slack, 0.520815) - 0.005 with `oracle_basin.settle_to`, which
is now a cold settle plus the rotation-aware collective kick (most strained
bodies swapped / turned 45 deg / re-slotted and re-settled). Nothing counts
unless packlib says ok, and every number is scored through sqscore.

The sweep is resumable: it writes workspace/push/pl32_sweep.json after every k,
so a 5-minute wall limit never loses a gated row.

Read-only apart from that ledger.
"""
from __future__ import annotations

import json
import math
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "workspace/push/pl32_sweep.json")
sys.path.insert(0, HERE)

import sqscore as SQ      # noqa: E402
import packlib as P       # noqa: E402

SLACK_BEAT = 0.520815     # the column's current best slack
K_LO, K_HI = 8, 25        # the sweep range requested
BUDGET = 240.0


def gate(state) -> tuple:
    """(ok, L, state_list) from the project's own gate."""
    st = [(float(a), float(b), float(c)) for a, b, c in np.asarray(state, float)]
    r = P.verify(st)
    return bool(r["ok"]), float(r["L"]), st, float(r["worst_pen"])


def unpack_q(q, n):
    q = np.asarray(q, float)
    return q[:n], q[n:2 * n], q[2 * n:]


def band(state, k: int, delta: float, eps: float = 1e-9) -> list:
    """Add the 2k+1 squares that take k^2+1 -> (k+1)^2+1 in side k+1+delta.

    The state is first anchored so its bounding box starts at (0, 0) -- the
    delivered states are not guaranteed to be corner-anchored, and without this
    the strips cut through the old packing (measured: the gate rejected every
    band from n=5 and n=65). The 1e-9 gap is because packlib rejects exact
    contact at tol=0; it costs nothing at 1e-9 scale.
    """
    a = np.asarray(state, float)
    ex = 0.5 * (np.abs(np.cos(a[:, 2])) + np.abs(np.sin(a[:, 2])))
    x0 = float((a[:, 0] - ex).min()); y0 = float((a[:, 1] - ex).min())
    a = a.copy(); a[:, 0] -= x0; a[:, 1] -= y0
    st = [(float(x), float(y), float(t)) for x, y, t in a]
    old_top = float((a[:, 1] + ex).max())
    top = max(k + delta, old_top) + eps
    for i in range(k + 1):
        st.append((i + 0.5, top + 0.5, 0.0))
    for j in range(k):
        st.append((top + 0.5, j + 0.5, 0.0))
    return st


def kick_record(state, L_t: float, rng: np.random.RandomState, frac: float = 0.3):
    """A global version of the settle's collective kick, as a restart seed:
    a random subset of the bodies is turned by +/-45 deg and re-slotted."""
    a = np.asarray(state, float).copy()
    n = len(a)
    rad = 1.2 * L_t / math.sqrt(n)
    idx = rng.choice(n, size=max(1, int(round(frac * n))), replace=False)
    for i in idx:
        att = float((a[i, 2] + rng.choice([-1.0, 1.0]) * np.pi / 4) % (np.pi / 2))
        hw = 0.5 * (abs(math.cos(att)) + abs(math.sin(att)))
        x = min(max(a[i, 0] + rng.uniform(-rad, rad), hw), L_t - hw)
        y = min(max(a[i, 1] + rng.uniform(-rad, rad), hw), L_t - hw)
        a[i] = (x, y, att)
    return np.column_stack([a[:, 0], a[:, 1], a[:, 2]])


def try_target(st0: np.ndarray, L_t: float, k: int, seed0: int) -> dict:
    """Search into side L_t. Nothing counts unless packlib gates it."""
    from oracle_basin import settle_to
    n = k * k + 1
    rec = {"k": k, "n": n, "target_L": round(float(L_t), 9),
           "target_slack": round(float(L_t - k), 9),
           "cur_slack": None, "via": None, "ok": False, "L": None}
    t0 = time.time()
    kicks = 6 if n <= 200 else 4
    iters = 120 if n <= 200 else 80
    rng = np.random.RandomState(seed0)
    attempts = [("settle_from_record", np.asarray(st0, float))]
    attempts.append(("kick+settle", kick_record(st0, L_t, rng)))
    # a third seed: the record scaled into the target box, then kicked
    a = np.asarray(st0, float).copy()
    cur_L = float(P.verify([(float(x), float(y), float(t)) for x, y, t in a])["L"])
    a[:, :2] *= (L_t / cur_L)
    attempts.append(("scaled+kick", kick_record(a, L_t, rng, frac=0.2)))

    bestL = None
    for ai, (name, s0) in enumerate(attempts):
        q0 = np.concatenate([s0[:, 0], s0[:, 1], s0[:, 2]])
        try:
            # deterministic per attempt: the project forbids wall-clock/RNG
            # seeds derived from anything but the cell index
            q, f = settle_to(q0, L_t, iters=iters, kicks=kicks,
                             seed=seed0 + 101 * ai)
        except Exception as e:                              # noqa: BLE001
            rec.setdefault("errors", []).append({"via": name, "err": str(e)[:120]})
            continue
        X, Y, TH = unpack_q(q, n)
        st = np.column_stack([X, Y, TH % (math.pi / 2)])
        ok, L, stl, wp = gate(st)
        print(f"  k={k:<2} target slack {L_t - k:.4f} via {name:<18} "
              f"{'GATED L=' + format(L, '.6f') + ' slack ' + format(L - k, '.4f') if ok else 'no gate (wp %+.2e)' % wp}"
              f"  [{time.time() - t0:.0f}s]", flush=True)
        if ok and (bestL is None or L < bestL[0]):
            bestL = (L, name, stl)
    if bestL:
        rec.update({"via": bestL[1], "ok": True, "L": round(bestL[0], 12),
                    "slack": round(bestL[0] - k, 9), "state": bestL[2],
                    "secs": round(time.time() - t0, 1)})
    else:
        rec["secs"] = round(time.time() - t0, 1)
    return rec


def load_ledger() -> dict:
    if os.path.exists(OUT):
        with open(OUT) as f:
            return json.load(f)
    return {"rows": {}, "started": time.strftime("%Y-%m-%d %H:%M:%S")}


def save_ledger(led: dict):
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(led, f, indent=1)


def main() -> int:
    SQ.guard()
    per = SQ.load()
    old = {}
    for n in sorted(per):
        k = math.isqrt(n)
        if n - k * k == 1:
            old[n] = SQ.extent(per[n])
    print(f"r=1 column: {len(old)} rows, best slack "
          f"{min(old[n] - math.isqrt(n) for n in old):.6f}")

    led = load_ledger()
    t_start = time.time()
    for k in range(K_LO, K_HI + 1):
        n = k * k + 1
        if n not in old:
            print(f"k={k}: n={n} not in the delivered column, skipped")
            continue
        if str(k) in led["rows"] and led["rows"][str(k)].get("done"):
            print(f"k={k}: already in the ledger, skipped")
            continue
        if time.time() - t_start > BUDGET:
            print("budget reached; rerun to continue (the ledger is resumable)")
            break
        cur = old[n]
        cur_slack = cur - k
        seem = 0.520815 if cur_slack > SLACK_BEAT else cur_slack
        t_slack = seem - 0.005
        floor = math.sqrt(n) - k                        # area bound
        if t_slack <= floor + 1e-9:
            print(f"k={k}: target slack {t_slack:.6f} at/below the area floor "
                  f"{floor:.6f}, skipped")
            led["rows"][str(k)] = {"k": k, "n": n, "cur_slack": round(cur_slack, 9),
                                   "skip": "area floor", "done": True}
            save_ledger(led)
            continue
        st0 = np.array(per[n], float)
        rec = try_target(st0, k + t_slack, k, 7919 * n + 104729)
        rec["cur_slack"] = round(cur_slack, 9)
        rec["cur_L"] = round(cur, 9)
        rec["done"] = True
        led["rows"][str(k)] = rec
        save_ledger(led)

    rows = [led["rows"][str(k)] for k in range(K_LO, K_HI + 1)
            if str(k) in led["rows"]]
    done = [r for r in rows if r.get("done")]
    gated = [r for r in done if r.get("ok")]
    better = [r for r in gated if r["slack"] < SLACK_BEAT - 1e-9]
    print(f"\nsweep: {len(done)}/{K_HI - K_LO + 1} k done, {len(gated)} gated, "
          f"{len(better)} with slack < {SLACK_BEAT}")
    for r in gated:
        mark = "  <-- beats the column" if r["slack"] < SLACK_BEAT - 1e-9 else ""
        print(f"  k={r['k']:<2} n={r['n']:<4} L={r['L']:.9f} slack {r['slack']:.6f} "
              f"(column {r['cur_slack']:.6f}) via {r['via']}{mark}")

    if not better:
        print("\nNO BASE FOUND below the column's current slack. The column stands "
              f"at {SLACK_BEAT}; nothing is claimed and no score is changed.")
        led["verdict"] = "no base"
        save_ledger(led)
        return 0

    best = min(better, key=lambda c: c["k"])
    k0 = best["k"]
    delta = best["slack"]
    print(f"\nbase: n={best['n']} (k={k0}), gated L={best['L']:.9f}, "
          f"slack {delta:.6f} < {SLACK_BEAT}")

    # ---- cascade: carry the base up the column, gating every band
    st = best["state"]
    brows = []
    for k in range(k0, 31):
        n = k * k + 1
        st2 = band(st, k, delta)
        ok, L, stl, wp = gate(st2)
        brows.append({"k": k + 1, "n": (k + 1) * (k + 1) + 1, "ok": ok,
                      "L": round(L, 12), "old": old.get((k + 1) * (k + 1) + 1)})
        print(f"  band -> n={(k + 1) ** 2 + 1:<4} {'GATED' if ok else 'FAIL'} "
              f"L={L:.9f} (old {brows[-1]['old']:.9f})")
        if ok:
            st = stl
    bad = [r for r in brows if not r["ok"]]
    gains = []
    for r in brows:
        if r["ok"] and r["old"] is not None and r["L"] < r["old"] - 1e-12:
            gains.append((r["old"] - r["L"]) / math.sqrt(r["n"]))
    dscore = -sum(gains)
    print(f"\nbands gated {len(brows) - len(bad)}/{len(brows)}; rows improved {len(gains)}")
    print(f"measured score change: {dscore:+.9f} "
          f"(delivered {float(SQ.DELIVERED_SCORE):.9f} -> {float(SQ.DELIVERED_SCORE) + dscore:.9f})")
    led.update({"base_k": k0, "base_delta": delta, "bands": brows,
                "rows_improved": len(gains), "dscore": dscore,
                "bad_bands": len(bad), "verdict": "base"})
    save_ledger(led)
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
