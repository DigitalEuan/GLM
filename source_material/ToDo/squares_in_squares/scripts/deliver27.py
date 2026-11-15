#!/usr/bin/env python3
"""deliver27.py — run 27 deliverables.

Run 27 = P4 (root conversions) from NEXT_STEPS: the standing channel
re-run to fixpoint + the P4 instrument built + the leverage map
corrected (two run-26 documentation errors fixed) + the register's
optimality theorems absorbed into the instrument.

Score unchanged 22.819977568 (P4 is a fixpoint/instrument run; the
map refresh found no unexploited conversions — the cascade is at a
true fixpoint).

Produces:
  1. download/run27_outcomes.json — the run ledger
  2. README.md Run 27 section
  3. REPRODUCE.md A19
  4. RUN_NOTES.md + download/run27_NOTES.md refresh
  5. download/README.md top-level refresh
  6. download/run27/ tree + MANIFEST.md
  7. download table.json/submission.csv sync (unchanged this run)
"""
import ast
import json
import math
import os
import shutil

W = "/home/z/my-project"
DL = f"{W}/download/run27"
TAB = f"{W}/workspace/submission/table.json"

tab = json.load(open(TAB))
score = sum(r["L"] / math.sqrt(int(k)) - 1 for k, r in tab.items())
assert abs(score - 22.819977568) < 2e-9, score

ra = json.load(open(f"{W}/workspace/push/root_audit27.json"))
agg = ra["aggregate"]
fa = ra["fixpoint_audit"]

# ------------------------------------------------------------- 1. ledger
led = {
 "run": 27, "date": "2026-11-06",
 "user_request": "continue this project - see NEXT_STEPS P4",
 "executed": {
   "P4_standing_channel": {
     "status": "fixpoint confirmed",
     "measured": ("cascade3: 0 chain improvements, 0 fails; "
                  "closure_apply: fixpoint after 0 rounds; "
                  "final_assembly: round-trip 0 issues; "
                  "score unchanged 22.819977568; beats-grid 454")},
   "P4_instrument": {
     "status": "built + run (scripts/root_audit.py)",
     "file": "workspace/push/root_audit27.json",
     "fixpoint_audit": {
        "rows_above_envelope": fa["above_env"],
        "note": ("0 unexploited conversions -- the cascade is at a true "
                 "fixpoint; envelope tolerance 1e-7 absorbs the "
                 "finalize +2e-9 scale")},
     "proven_floors": {
        "count": len(ra["proven_floors"]),
        "sources": ("area bound (perfect squares); T-084 Karakuş "
                    "s(k^2-1)=k; T-086 chelokot s(k^2-2)=k; T-064 "
                    "Daniel s(k^2-3)=k; T-081 Daniel s(k^2-4)=k; "
                    "individuals T-237 (s(2..5)), T-060 (s(11)), "
                    "T-006 (s(13)=4), T-052 (s(21)=5), T-051 (s(32)=6), "
                    "T-252 (s(44)=7), T-053 (s(45)=7), T-008 (s(46)=7), "
                    "T-066 (s(59)=8), T-062/3 (s(60/61)=8), T-184 "
                    "(s(76)=9), T-067 (s(77,78)=9), T-191 (s(95,96)=10); "
                    "machine-checked C1: s(12)=4 [T-245/evand], s(17) "
                    "[T-153], s(19) [T-194]")},
     "open_structure": {
        "open_rows": fa["open_rows"],
        "fully_open_diagonals": 0,
        "note": ("the four optimality theorems prove every diagonal's "
                 "head; all open rows live at r >= 5")},
     "aiming_map": {
        "diagonals_with_aims": len(ra["per_diagonal_best_aim"]),
        "top_aims": [{"n": a["n"], "K": a["K"],
                      "converts": len(a["converts_T263"]),
                      "value_T263": round(a["value_T263"], 6)}
                     for a in (ra["aiming_top30"][:8])],
        "aggregate_T263": round(agg["one_T263_at_every_first_open_row"], 6),
        "aggregate_d01": round(agg["one_d01_at_every_first_open_row"], 6),
        "d_star": 0.0382,
        "validation": ("cross-validated against an independent "
                       "reimplementation of the chain-envelope value: "
                       "totals agree to 1e-6 (0.4334); the first version "
                       "overcounted by 70% (0.736) because it aimed at "
                       "proven floors -- the theorems fixed it")},
     "doc_errors_fixed": {
        "count": 2,
        "detail": ("run-26 NEXT_STEPS §2 (a) listed 453, 498, 810, 869, "
                   "930, 993 as c=10 members: 453/498 are c=12/c=14 "
                   "(21²+12, 22²+14) and 810/869/930/993 belong to the "
                   "open-head diagonals c=26/28/30/32; (b) claimed T-263 "
                   "binds the c=10 tail: T-263 binds only 299..539 (chain "
                   "stops at 410/451, deeper gobel2), and 586..971 is "
                   "bound by the community record at 586 (ρ=1/√2−1); the "
                   "true c=10 staircase has 11 roots (35…586); also the "
                   "run-26 §1 claim 'the register now moves above n=324' "
                   "was wrong: register max n = 308, zero bounds > 324")}},
   "P3_watch": {
     "status": "checked, nothing new to import",
     "import_atlas": "idempotent (applied 0, skipped 5, rejected 319)",
     "register": ("frontier RESULTS.md fetched and parsed (273 result "
                  "rows): no new upper bounds after T-263; the four "
                  "optimality theorems and 21 individual results were "
                  "absorbed into the instrument instead")},
   "NEXT_STEPS_update": {
     "status": "rewritten to the Run-27 state",
     "changes": ("§2 corrected (membership, binding root, register "
                 "range) with the instrument's numbers; §1 tie structure "
                 "split into proven floors (152) vs open rows (394); "
                 "aiming map + aggregate (0.4334, d*=0.0382) added; "
                 "§3 extended with failures 11-12 (documentation "
                 "arithmetic; proven floors gate the aiming); P4 section "
                 "rewritten as instrumented; value ladder updated")},
 },
 "score": {"before": 22.819977568, "after": round(score, 9),
           "delta": 0.0},
 "next": [
   "P1' blob-regime insertion at the measured aims: 251, 250, 284, 191 "
   "(r=5/6 roots of the two biggest diagonals); read the 2026-11-03 "
   "structure-guided-search preprint first",
   "P3 weekly watch (the only item that has paid); absorb new "
   "optimality results into PROVEN_FLOOR immediately",
   "P5 certification backlog (Lean; T-263 Fraction replay)"],
}
json.dump(led, open(f"{W}/download/run27_outcomes.json", "w"), indent=1)
print("1. ledger written; score:", round(score, 9))

# ---------------------------------------------------- 2. README Run 27
sec = f"""

# Run 27 (2026-11-06): P4 — the root-conversion instrument

User: continue this project - see NEXT_STEPS P4.

## The standing channel: fixpoint confirmed

cascade3 (0 chain improvements, 0 fails) -> closure_apply (fixpoint
after 0 rounds) -> final_assembly (round-trip 0 issues).  Score
unchanged 22.819977568; beats-grid 454.  The propagation loop has
nothing left to convert - as required, this is now verified by an
instrument rather than asserted.

## The instrument: scripts/root_audit.py

For every residue diagonal: the chain envelope (running rho = min
L-K over lower members), a fixpoint audit (rows above envelope =
unexploited conversions), and an aiming map - the measured value of
a T-263-class record (depth 0.0216) placed at each open row, with
its conversion list.  Ledger: workspace/push/root_audit27.json.
Cross-validated against an independent reimplementation; the totals
agree to 1e-6.

## Two documentation errors found and fixed

The run-26 NEXT_STEPS §2 eyeballed diagonal memberships and chain
extents, and got them wrong:
- 453, 498, 810, 869, 930, 993 were listed as c=10 members.
  Computed: 453 = 21²+12 (c=12), 498 = 22²+14 (c=14); 810, 869,
  930, 993 belong to the open-head diagonals c=26/28/30/32.
- "T-263 binds the c=10 tail" was wrong twice: T-263 binds only
  299..539 (the chain stops at 410/451 where gobel2 designs are
  deeper), and 586..971 is bound by the community record at 586
  (rho = 1/sqrt(2)-1).  The true c=10 staircase has 11 roots
  (35, 110, 131, 154, 179, 206, 235, 266, 299, 410, 586).
- The run-26 claim "the register now moves above n=324" was also
  wrong: the register's entire result set spans n = 5..308 with zero
  bounds above 324.
All three corrections are in NEXT_STEPS.md §2/§1; the instrument
recomputes the map from the table so these claims can no longer
drift (failure mode 11 in §3).

## The register's optimality theorems absorbed

The frontier results table (273 rows parsed) contains four theorems
that prove entire diagonal heads: s(k²−1)=k [T-084 Karakuş],
s(k²−2)=k [T-086 chelokot], s(k²−3)=k [T-064 Daniel], s(k²−4)=k
[T-081 Daniel], plus 21 individual results (s(11), s(13)=4, s(21)=5,
s(32)=6, s(44)=7 [T-252], s(45/46)=7, s(59/60/61)=8, s(76)=9,
s(77/78)=9, s(95/96)=10, s(2..5)) and machine-checked s(12)=4.
These 156 proven floors now gate the instrument: without them it
aimed at perfect squares and overcounted the aggregate by 70% (0.736
vs the true 0.4334).

## The corrected leverage map (measured)

- Open rows: 394 (of 546 tied; 152 are proven floors that can never
  move).  All live at r = 2K−1−c >= 5; area room 6.662; the
  leader's standing is 11.5% of that ceiling.
- Top aims (one T-263-class record): 251 (16 rows, 0.015569), 250
  (15, 0.014877), 284 (16, 0.014863), 191 (13, 0.014854).
- Aggregate: one record at every diagonal's best open aim =
  0.4334 (56.6% of the gap); uniform depth d* = 0.0382 over the 394
  open rows matches the leader.
- The instrument's top-diagonals table reproduces the original
  Run-13 §2 numbers exactly (c=26: 0.274/16; c=25: 0.272/15; ...) -
  that table was right all along; only the run-26 edit was wrong.

## NEXT_STEPS.md rewritten to the Run-27 state

Section 0 status table (runs 14-27); §1 tie structure with the
proven-floor split; §2 corrected with instrument numbers; §3 extended
with failures 11-12; P4 rewritten as instrumented; value ladder
updated.  Copies: NEXT_STEPS.md and download/NEXT_STEPS.md.

Score {22.819977568:.9f} (unchanged - instrument run); submission.csv
round-trip 0 issues; download copies in sync.
"""
readme = open(f"{W}/README.md").read()
if "Run 27 (2026-11-06)" not in readme:
    open(f"{W}/README.md", "w").write(readme + sec)
    print("2. README Run 27 appended")
else:
    print("2. README already has Run 27 (idempotent)")

# ---------------------------------------------------- 3. REPRODUCE A19
rep = open(f"{W}/REPRODUCE.md").read()
if "## A19." not in rep:
    rep += """

## A19. Run 27: P4 root-conversion instrument

```bash
python3 scripts/cascade3.py        # fixpoint channel (0 expected)
python3 scripts/closure_apply.py
python3 scripts/final_assembly.py
python3 scripts/root_audit.py      # the P4 instrument (new)
python3 scripts/import_atlas.py    # weekly watch (idempotent)
python3 scripts/deliver27.py       # this run's deliverables
```
"""
    open(f"{W}/REPRODUCE.md", "w").write(rep)
    print("3. REPRODUCE A19 appended")
else:
    print("3. REPRODUCE already has A19 (idempotent)")

# ------------------------------- 4. RUN_NOTES.md alias + run27_NOTES.md
shutil.copy(f"{W}/README.md", f"{W}/RUN_NOTES.md")
print("4a. RUN_NOTES.md refreshed")
readme = open(f"{W}/README.md").read()
i = readme.find("# Run 27 (2026-11-06)")
notes = ("# Run 27 notes (2026-11-06)\n\n"
         "Run documentation under the distinct name.  The same content "
         "is in README.md (Run 27 section), RUN_NOTES.md, and "
         "download/run27/README.md.\n"
         + readme[i:])
open(f"{W}/download/run27_NOTES.md", "w").write(notes)
print("4b. download/run27_NOTES.md written")

# ------------------------------------------- 5. top-level download README
shutil.copy(f"{W}/README.md", f"{W}/download/README.md")
print("5. download/README.md refreshed")

# ---------------------------------------------------- 6. run27 tree
shutil.rmtree(DL, ignore_errors=True)
NEW = [
 ("scripts/root_audit.py", "NEW",
  "P4 instrument: chain-envelope audit + proven floors + aiming map"),
 ("scripts/deliver27.py", "NEW", "this build script"),
 ("workspace/push/root_audit27.json", "NEW", "P4 instrument ledger"),
 ("README.md", "EDITED", "Run 27 section"),
 ("REPRODUCE.md", "EDITED", "A19 section"),
 ("NEXT_STEPS.md", "EDITED",
  "rewritten to Run-27 state (map corrected, instrumented)"),
 ("run27_outcomes.json", "NEW", "run 27 ledger (also at download/ top)"),
]
rows = []
for rel, st, what in NEW:
    dst = os.path.join(DL, rel)
    os.makedirs(os.path.dirname(dst) or DL, exist_ok=True)
    src = (f"{W}/download/run27_outcomes.json"
           if rel == "run27_outcomes.json" else f"{W}/{rel}")
    if os.path.exists(src):
        shutil.copy(src, dst)
        rows.append((rel, st, os.path.getsize(dst), what))

man = ["# Run 27 deliverables — new/edited files only",
       "",
       "| Repository path | Status | Bytes | What it is |",
       "|---|---|---|---|"]
for rel, st, sz, what in rows:
    man.append(f"| {rel} | {st} | {sz} | {what} |")
man += ["",
        "Standing channel reused cascade3.py / closure_apply.py / "
        "final_assembly.py unchanged; import_atlas.py re-run "
        "(idempotent).",
        "download table.json/submission.csv/NEXT_STEPS.md refreshed in "
        "sync (table unchanged this run).",
        "No .pyc (ast.parse verification only)."]
open(f"{DL}/MANIFEST.md", "w").write("\n".join(man) + "\n")
print("6. download/run27/ tree built:", len(rows), "files")

# ---------------------------------------------------- 7. verification
for rel, st, sz, what in rows:
    if rel.endswith(".py"):
        ast.parse(open(f"{DL}/{rel}").read())
    if rel.endswith(".json"):
        json.load(open(f"{DL}/{rel}"))
bad = [f for _, _, fs in os.walk(DL) for f in fs if f.endswith(".pyc")]
assert not bad, bad
print("7. verification clean")
