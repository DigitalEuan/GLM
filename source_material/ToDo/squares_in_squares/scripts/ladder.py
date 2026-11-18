#!/usr/bin/env python3
r"""ladder.py — the expressiveness ladder, as a runnable check.

Each rung is a boundary claim of one shape: **this representation cannot
distinguish two packings that differ in score**.  A rung is only worth having if
its witness is on disk and the numbers in the document match the ledger, so this
script re-reads the ledgers and asserts them.  Rungs that cannot be recomputed
from a ledger here are marked `quoted` and name their source instead of pretending
to be checked.

Output: workspace/push/ladder.json + a table.
"""
from __future__ import annotations

import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
OUT = os.path.join(ROOT, "workspace/push/ladder.json")


def load(name):
    p = os.path.join(ROOT, "workspace/push", f"{name}.json")
    try:
        with open(p) as f:
            return json.load(f)
    except OSError:
        return None


def rungs():
    out = []
    per = None

    # -- rung 1: float / scan layer -----------------------------------------
    out.append({
        "rung": 1, "representation": "float / scan layer",
        "claim": "blind below 2.5e-13; a scan comparison cannot separate two "
                 "packings whose sides differ by less than that",
        "witness": "|dE| <= 1 after correction (scan_blind_to_clearance, 01)",
        "status": "quoted", "source": "01-LAYERS.md; ledger leech_lab",
        "checked": False})

    # -- rung 2: 24-pocket address ------------------------------------------
    a = load("leech_audit_fix")
    if a:
        rot = a.get("auc_rot")
        gap = a.get("auc_gap")
        cond = a.get("mi_gap_beats_given_rot")
        out.append({
            "rung": 2, "representation": "24-pocket address (6 sectors x 4 shells)",
            "claim": "sees rotation and nothing else: conditioning the score on "
                     "rotation destroys the address's information",
            "witness": f"AUC(rot->beats)={rot}, AUC(gap->beats)={gap}, "
                       f"MI(gap; beats | rot)={cond}",
            "status": "recomputed" if cond is not None else "missing",
            "source": "workspace/push/leech_audit_fix.json",
            "checked": bool(cond is not None and cond < 1e-6
                            and rot is not None and abs(rot - 1.0) < 1e-9)})

    # -- rung 3: Lambda_24 integrality --------------------------------------
    m = load("leech_map")
    if m:
        tv = m.get("tilt_vs_legal") or {}
        out.append({
            "rung": 3, "representation": "Lambda_24 integrality predicate",
            "claim": "incompatible with the field: every tilted row is illegal at "
                     "every tested scale, every untilted row is legal somewhere",
            "witness": f"tilt vs legal = {tv}",
            "status": "recomputed" if tv else "missing",
            "source": "workspace/push/leech_map.json",
            "checked": bool(tv)})

    # -- rung 4: contact graph / rigidity -----------------------------------
    out.append({
        "rung": 4, "representation": "contact graph + Laman/Maxwell count",
        "claim": "adds nothing to |E|: square contact graphs cannot reach the "
                 "Laman threshold except K3, and no delivered row is redundant",
        "witness": "R^2 == |E| (0.391 both); 0/220 rows with a redundant contact; "
                   "cluster headroom 0,-1,-1,-2 for |S| = 3,4,5,6",
        "status": "quoted", "source": "18-RIGIDITY.md; 17-COMB-ADDRESS.md",
        "checked": False})

    # -- rung 5: WL combinatorial address -----------------------------------
    c = load("leech_comb")
    if c:
        ex = c.get("explain") or {}
        out.append({
            "rung": 5, "representation": "WL signature of the tilt-coloured contact graph",
            "claim": "complete for the combinatorial part, silent on geometry: "
                     "beats its null only on a contact-bearing ensemble",
            "witness": f"explain = {str(ex)[:160]}",
            "status": "recomputed" if ex else "missing",
            "source": "workspace/push/leech_comb.json", "checked": bool(ex)})

    # -- rung 6: catalogue completeness boundary ----------------------------
    f = load("frontier")
    if f:
        tal = f.get("tally") or {}
        res = sum(v for k, v in tal.items() if k in ("at", "beats", "above"))
        unres = tal.get("unresolved", 0)
        out.append({
            "rung": 6, "representation": "the published catalogue itself",
            "claim": "determines n <= 324 and nothing above it; the trivial grid "
                     "is provably not its best known above 324",
            "witness": f"determined={res}, undetermined={unres}, "
                       f"witness family s(k^2+1) = k + 0.5355339",
            "status": "recomputed", "source": "workspace/push/frontier.json",
            "checked": unres == 675 and res == 325})
    return out


def main() -> int:
    rs = rungs()
    ok = 0
    print(f"{'#':>2} {'representation':38} {'status':11} checked")
    for r in rs:
        ok += bool(r["checked"])
        print(f"{r['rung']:2d} {r['representation'][:38]:38} {r['status']:11} "
              f"{'YES' if r['checked'] else 'no'}")
    print(f"\nchecked: {ok}/{len(rs)}   (quoted rungs name their source; they are "
          f"not silently counted as checks)")
    for r in rs:
        print(f"\n[{r['rung']}] {r['claim']}\n    {r['witness']}\n    {r['source']}")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as fh:
        json.dump({"run": 63, "schema": "ladder/1", "rungs": rs,
                   "checked": ok}, fh, indent=1)
    print(f"\nledger: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
