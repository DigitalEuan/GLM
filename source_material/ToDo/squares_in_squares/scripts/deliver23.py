#!/usr/bin/env python3
"""deliver23.py — run 23 deliverables.

Produces:
  1. download/run23_outcomes.json  — the run ledger (Q1/Q2/Q3 answers)
  2. README.md Run 23 section (repo root)
  3. REPRODUCE.md A15
  4. download/README.md — TOP-LEVEL refresh (the Q2 fix: run 22 only
     nested the README under download/run22/; earlier runs refreshed
     the top-level copy — this run restores that pattern and it stays)
  5. download/run23/ — new/edited files only + MANIFEST.md with the
     repository placement of every file
  6. ast.parse verification (no .pyc ever written)
"""
import ast
import json
import os
import shutil
import time

W = "/home/z/my-project"
DL = f"{W}/download/run23"

# ---------------------------------------------------------------- 1. ledger
led = {
 "run": 23, "date": "2026-11-05",
 "user_message": {
   "1": "repository updated",
   "2": "no README.md received",
   "3": ("continue the project - it looks like the Soft relaxation "
         "worked but has moved the submission.csv or score?")},
 "answers": {
   "Q2_no_readme": {
     "root_cause": ("run 22 delivered README.md only NESTED under "
                    "download/run22/README.md; earlier runs also "
                    "refreshed the TOP-LEVEL download/README.md. The "
                    "file existed (download/run22/README.md, 10796 B) "
                    "but the visible top-level copy was stale."),
     "fix": ("this run refreshes download/README.md at the top level "
             "AND delivers the nested copy; standard from now on.")},
   "Q3_submission_score": {
     "answer": ("NO — run 22 did not move submission.csv or the score. "
                "Evidence: (a) write footprint: table.json content "
                "dates to 08:03 and submission.csv download copies to "
                "19:15; run 22 wrote at 22:18+ and touched only "
                "workspace/push/soft_relax*.json; (b) sha256: "
                "download/table.json == workspace table.json, "
                "download/submission.csv == workspace submission.csv "
                "(byte-identical); (c) independent recomputation: score "
                "from table = 22.823536149 = score recomputed from "
                "submission.csv via packlib.verify (1000 rows, every "
                "state non-overlapping, max penetration 0.00e+00)."),
     "what_did_move": ("the score delta the user saw: leech snapshot "
                       "22.887470936 (08:02) -> table 22.823536149 "
                       "(08:03) is RUN 19's application of 6 "
                       "run18-frontier rows (n=183, 211, 308, 343, "
                       "380, 419), committed a163ab8 09:22 — hours "
                       "before run 22 started."),
     "run22_find_status": ("the run-22 verified 2.708107407 (n=5) was "
                            "ABOVE the table's existing 2.707106782 "
                            "(src gobelS:a1b1) — a control, correctly "
                            "NOT applied; submission untouched.")}},
 "correction": {
   "circular_atlas": ("run 22's claim 'we beat the atlas on all 114 "
                      "level-0 rows (net -0.77)' is RETRACTED as "
                      "circular: leech_map.py reads download/table.json "
                      "— the 'atlas' was our own table one minute "
                      "before run 19's application. The -0.77 was run "
                      "19's application delta, not a comparison against "
                      "an external study.")},
 "method": {
   "sweep": ("12 top-waste at-grid rows (waste = grid/sqrt(n)-1): "
             "{2,6,7,8,13,14,21,22,23,30,42,56} x ladder "
             "(grid-0.0005, grid-0.002, grid-0.01) x 2 seeds x 8 hops "
             "= 288 hop-polishes via soft_relax.hop_search (SA "
             "pass-through shuffle + settle_to L-BFGS re-hardening); "
             "find criterion: finalize_gate-verified L < min(grid, "
             "table L) - 1e-9."),
   "ladder_calibration": ("the 6 run18-frontier cracks landed at "
                          "0.0004..0.0065 below grid, so the ladder "
                          "starts at -0.0005 — tighter than any "
                          "previous run.")},
 "results": {
   "cells": 36, "finds": 0, "hard_hops": "0/288",
   "score_before": 22.823536149, "score_after": 22.823536149,
   "table_changed": False,
   "detail": "every cell 0/8: no polished state reached pairwise "
             "non-overlap at ANY target, even 0.0005 below grid."},
 "readings": [
   ("The gap-throttle law (run 22) is confirmed in the negative "
    "direction: on the 12 highest-waste small-n level-1 rows, nothing "
    "re-hardens even 0.0005 below the trivial grid — the soft "
    "pass-through channel, which DID crack n=5 at +0.001 above its "
    "known optimum, cannot open any small-n level-1 row."),
   ("Honest nuance: the level-1 wall is porous at LARGE n. Run 18 "
    "cracked 6 level-1 rows (183, 211, 308, 343, 380, 419) by "
    "0.0004..0.0065. The remaining 546 at-grid rows split into a "
    "large-n set worth a hair-margin sweep and a small-n set that has "
    "now resisted every channel (runs 20-23)."),
   ("The verified channel for any future find is unchanged: table "
    "best-L-wins -> cascade3 -> closure_apply -> final_assembly "
    "(rebuilds submission.csv); sweep23.apply() implements it and "
    "reported 'no applicable finds — table unchanged (honest)'.")],
 "next": [
   "large-n hair-margin sweep: the at-grid rows in bands around the 6 "
   "cracked ones (n in 184..199 at 14, 212..224 at 15, ...), ladder "
   "-0.0005 first",
   "tier-1 infeasibility theorem for small-n level-1 rows (turn the "
   "empirical unanimity of runs 20-23 into a proof)",
   "keep the top-level download/README.md refresh in every future run"],
}
json.dump(led, open(f"{W}/download/run23_outcomes.json", "w"), indent=1)
print("1. run23_outcomes.json written")

# ---------------------------------------------------- 2. README Run 23
sec = """

# Run 23 (2026-11-05): submission audit + tightest ladder sweep

User questions: (2) no README received; (3) did the soft relaxation
move submission.csv or the score?

## Q3 answer: no — with evidence

- Write footprint: table.json content 08:03, submission.csv copies
  19:15; run 22 wrote 22:18+ and touched only
  workspace/push/soft_relax*.json.  Nothing moved.
- sha256: download copies byte-identical to workspace copies.
- Independent recomputation from submission.csv (packlib.verify on all
  1000 rows, every state non-overlapping): 22.823536149 == table
  score.  In sync.
- The score delta the user saw (22.8875 -> 22.8235) is RUN 19's
  application of 6 run18-frontier rows (n=183, 211, 308, 343, 380,
  419), hours before run 22 started.
- Run 22's verified 2.7081 (n=5) was ABOVE the table's existing
  2.7071 (gobelS:a1b1) — a control, correctly not applied.

## Q2 answer: delivery-pattern bug, fixed

Run 22 delivered README.md only nested under download/run22/.
This run refreshes the TOP-LEVEL download/README.md too; standard
from now on.

## Correction of a run-22 claim

"We beat the atlas on all 114 level-0 rows" is RETRACTED as
circular: leech_map.py reads download/table.json — the 'atlas' was
our own table one minute earlier.  The -0.77 was run 19's application
delta.

## The sweep

12 top-waste at-grid rows {2,6,7,8,13,14,21,22,23,30,42,56} x ladder
(grid-0.0005, -0.002, -0.01) x 2 seeds x 8 hops = 288 hop-polishes
(soft pass-through + L-BFGS re-hardening).  Ladder calibrated by the
6 run18-frontier cracks (0.0004..0.0065 below grid).

Result: 0/288 hard hops, 0 finds, table unchanged, score unchanged
22.823536149.  The gap-throttle law is confirmed in the negative
direction — even 0.0005 below grid, no small-n level-1 row
re-hardens.  Honest nuance: the level-1 wall is porous at large n
(run 18's six cracks); the next sweep targets the large-n bands.
"""
readme = open(f"{W}/README.md").read()
if "Run 23 (2026-11-05)" not in readme:
    open(f"{W}/README.md", "w").write(readme + sec)
    print("2. README.md Run 23 section appended")
else:
    print("2. README.md already has Run 23 (idempotent)")

# ---------------------------------------------------- 3. REPRODUCE A15
rep = open(f"{W}/REPRODUCE.md").read()
if "## A15." not in rep:
    rep += """

## A15. Run 23: submission audit + tightest ladder sweep

```bash
python3 scripts/sweep23.py    # ~28 min: Part 0 audit + 36-cell ladder + apply
python3 scripts/audit23.py    # optional: fact-base audit, pass 1
python3 scripts/audit23b.py   # optional: fact-base audit, pass 2
```
"""
    open(f"{W}/REPRODUCE.md", "w").write(rep)
    print("3. REPRODUCE.md A15 appended")
else:
    print("3. REPRODUCE.md already has A15 (idempotent)")

# --------------------------------------------- 4. top-level download README
shutil.copy(f"{W}/README.md", f"{W}/download/README.md")
print("4. download/README.md refreshed (top level)")

# ---------------------------------------------------- 5. run23 tree
shutil.rmtree(DL, ignore_errors=True)
NEW = [
 ("scripts/sweep23.py", "NEW",
  "run 23 driver: Part 0 audit + 36-cell ladder sweep + apply"),
 ("scripts/audit23.py", "NEW",
  "fact-base audit pass 1 (n=5, at-grid rows, score definitions)"),
 ("scripts/audit23b.py", "NEW",
  "fact-base audit pass 2 (546 at-grid rows, roots, waste rank)"),
 ("scripts/deliver23.py", "NEW",
  "this build script (ledger + README + REPRODUCE + tree + manifest)"),
 ("workspace/push/sweep23.json", "NEW",
  "36-cell sweep results ledger (hard_hops/verified per cell)"),
 ("README.md", "EDITED",
  "Run 23 section: Q2/Q3 answers, circularity correction, sweep"),
 ("REPRODUCE.md", "EDITED", "A15 section"),
 ("run23_outcomes.json", "NEW", "run 23 ledger (also at download/ top level)"),
]
rows = []
for rel, st, what in NEW:
    dst = os.path.join(DL, rel)
    os.makedirs(os.path.dirname(dst) or DL, exist_ok=True)
    src = (f"{W}/download/run23_outcomes.json"
           if rel == "run23_outcomes.json" else f"{W}/{rel}")
    shutil.copy(src, dst)
    rows.append((rel, st, os.path.getsize(dst), what))

man = ["# Run 23 deliverables — new/edited files only",
       "",
       "Each file sits at exactly the repository path shown; copy the",
       "tree over the repository root.  Additionally download/README.md",
       "(TOP LEVEL) was refreshed — that is the Q2 fix, not part of",
       "this tree.",
       "", "| Repository path | Status | Bytes | What it is |",
       "|---|---|---|---|"]
for rel, st, sz, what in rows:
    man.append(f"| {rel} | {st} | {sz} | {what} |")
man += ["",
        "No .pyc/.cpython files (all verification via ast.parse).",
        "table.json / submission.csv UNCHANGED this run (no finds)."]
open(f"{DL}/MANIFEST.md", "w").write("\n".join(man) + "\n")
print("5. download/run23/ tree built")

# ---------------------------------------------------- 6. verification
for rel, st, sz, what in rows:
    if rel.endswith(".py"):
        ast.parse(open(f"{DL}/{rel}").read())
        print(f"   ast OK {rel}")
    if rel.endswith(".json"):
        json.load(open(f"{DL}/{rel}"))
        print(f"   json OK {rel}")
bad = [f for _, _, fs in os.walk(DL) for f in fs
       if f.endswith((".pyc", ".cpython-312.pyc"))]
assert not bad, bad
print("6. verification clean: no .pyc, all parses OK")
