#!/usr/bin/env python3
"""deliver28.py — run 28 deliverables (SAT data review).

Run 28 (user input: "review the SAT data for any insight there") built
scripts/sat_review.py, which computes per-pair separating-axis data
over all 1000 delivered packings: margins, contact normals, contact
types (how many SAT axes are simultaneously tight), binding-wall
touches, free squares, Maxwell counting ratios.  Score unchanged
22.819977568 (review run; no table change).

Produces:
  1. download/run28_outcomes.json — run ledger
  2. README.md Run 28 section
  3. REPRODUCE.md A20
  4. RUN_NOTES.md + download/run28_NOTES.md
  5. download/README.md top-level refresh
  6. download/run28/ tree + MANIFEST.md
  7. download table.json/submission.csv sync (unchanged this run)
"""
import ast
import json
import math
import os
import shutil

W = "/home/z/my-project"
DL = f"{W}/download/run28"
TAB = f"{W}/workspace/submission/table.json"

tab = json.load(open(TAB))
score = sum(r["L"] / math.sqrt(int(k)) - 1 for k, r in tab.items())
assert abs(score - 22.819977568) < 2e-9, score

sr = json.load(open(f"{W}/workspace/push/sat_review28.json"))

# ------------------------------------------------------------- 1. ledger
led = {
 "run": 28, "date": "2026-11-06",
 "user_request": "review the SAT data for any insight there",
 "executed": {
   "instrument": {
     "status": "built + run (scripts/sat_review.py)",
     "file": "workspace/push/sat_review28.json",
     "measured": {
       "packings": 1000, "SAT_clean": "max_overlap <= 1e-9 every row",
       "total_pair_contacts": 1806403,
       "total_binding_wall_touches": 75882,
       "validation": "n=50 decode cross-check: 105 contacts, exact match "
                      "with the run-26 decode"}},
   "insight_1_contact_language": {
     "status": "measured",
     "finding": ("99% of the table's contacts are parallel: 51.5% "
                 "2-tight (parallel edge / non-parallel corner), 47.5% "
                 "4-tight (parallel corner), 1.0% generic (1-tight), "
                 "3-tight structurally empty. run18-frontier — the "
                 "record class — is the outlier at 8% generic, ratio "
                 "median 1.057 vs 1.2+ everywhere else"),
     "action": ("P1' constructions should seek generic (non-parallel) "
                "contact structures; the parallel languages of P1(a)/(b) "
                "are measured dead ends")},
   "insight_2_T263_floaters": {
     "status": "measured",
     "finding": ("n=299/334/371 (the T-263 import + chain) each carry 41 "
                 "free squares (no pair contact, no wall touch) at "
                 "Maxwell ratio 0.68 — the most slack in the table. The "
                 "41 are identical across the family (chain children "
                 "inherit them); quasi-contacts at median gap 0.0035; "
                 "wall distance up to 6.46. Imported AFTER the P2 polish "
                 "campaign; never polish-seeded"),
     "action": ("P2 renewed for exactly this family (§2a.2): seed the "
                "LP/annealer from the register states, floaters free, "
                "settle with contact-graph re-breaking")},
   "insight_3_grid_rigidity": {
     "status": "measured",
     "finding": ("the 546 grid rows have nearest non-contact gap exactly "
                 "1.0 (a full empty cell) — P2's 0-finds there are now a "
                 "measured statement, not an anecdote")},
   "insight_4_T083_bound": {
     "status": "checked, no new floors",
     "finding": ("Karakuş T-083 rectangle bound s(N) >= 1/2 + sqrt(N - "
                 "floor(sqrt(N)) + 1/4) (nonsquare 8..324): 0 violations "
                 "against our sub-grid L; it implies grid-optimality only "
                 "on the c=1 diagonal (k^2-1, already T-084) — no new "
                 "proven floors, but the right certificate shape if it "
                 "ever extends past 324")},
   "insight_5_register_still_grid": {
     "status": "checked",
     "finding": ("the register's best-known is still grid at every top "
                 "aim (250/251/284/191/190: side '16.0/17.0/14.0', "
                 "finder '-') — nobody upstream has beaten the mid-band "
                 "either")},
   "retraction": {
     "status": "corrected in NEXT_STEPS (§2 note, failure 13)",
     "finding": ("the tier-1 verification report's old 'theorem s(6)=3' "
                 "line is NOT backed by the register: n=6 appears only in "
                 "restricted-optimality rows (T-261/T-124, local-minima "
                 "searches, C1/C0). s(6)=3 stays a conjecture by our "
                 "classification; n=6 remains a legal (low-value) aim")},
   "NEXT_STEPS_update": {
     "status": "updated to Run-28 state",
     "changes": ("new §2a (the SAT data reviewed); failure 13 (citations "
                 "must name a register row); P2 renewed for the T-263 "
                 "family; P1' updated with the generic-contact guidance; "
                 "§0 status table + run-28 entry")},
 },
 "score": {"before": 22.819977568, "after": round(score, 9), "delta": 0.0},
 "next": [
   "P2 re-run aimed at the T-263 family (299/334/371): 41 floaters at "
   "ratio 0.68, the one place the record-holder's engine and our "
   "finisher could meet",
   "P1' insertion campaign at 251/250/284/191, seeking generic "
   "contact structures (§2a.1); read the 2026-11-03 preprint first",
   "P3 weekly watch (the only item that has paid)"],
}
json.dump(led, open(f"{W}/download/run28_outcomes.json", "w"), indent=1)
print("1. ledger written; score:", round(score, 9))

# ---------------------------------------------------- 2. README Run 28
sec = f"""

# Run 28 (2026-11-06): the SAT data reviewed

User input: review the SAT data for any insight there.

## The instrument: scripts/sat_review.py

Per-pair separating-axis data over all 1000 delivered packings:
margins (gap = -penetration), contact normals (argmin axis), contact
types (count of simultaneously tight SAT axes), binding-wall touches,
free squares (no pair contact, no wall touch), Maxwell counting
ratios.  Ledger: workspace/push/sat_review28.json.  Validated against
the run-26 n=50 decode: 105 contacts, exact match.

## Five findings (measured)

1. **The contact language is 99% parallel.**  1,806,403 pair contacts:
   51.5% 2-tight (parallel edge / non-parallel corner), 47.5% 4-tight
   (parallel corner), 1.0% generic, 3-tight empty.  run18-frontier —
   the record class — is the outlier at 8% generic contacts, Maxwell
   ratio median 1.057 (1.2+ everywhere else).  P1' guidance: seek
   generic contact structures; the parallel languages are measured
   dead ends.
2. **The T-263 family floats 41 squares.**  n=299/334/371 each carry
   41 free squares at ratio 0.68 — the most slack in the table.  The
   41 are identical across the family; quasi-contacting at median gap
   0.0035, wall distance up to 6.46.  Imported after the P2 polish
   campaign, never polish-seeded.  P2 renewed for exactly this family.
3. **The grid is rigid at the pair level.**  The 546 grid rows have
   nearest non-contact gap exactly 1.0 — a full empty cell.  P2's
   0-finds there are now measured, not anecdotal.
4. **Karakuş's rectangle bound (T-083) gives us nothing new.**
   s(N) >= 1/2 + sqrt(N - floor(sqrt(N)) + 1/4) for nonsquare 8..324:
   0 violations against our L, and it implies grid-optimality only on
   the c=1 diagonal (k^2-1, already T-084).  No new floors — but it
   is the right certificate shape for the mid-band if it extends.
5. **The register is still at grid at every top aim** (250/251/284/
   191/190: finder '-').  Nobody upstream has beaten the mid-band
   either.

Plus one retraction: the tier-1 report's "theorem s(6)=3" is not
backed by the register (n=6 appears only in restricted-optimality
rows, C1/C0).  s(6)=3 stays a conjecture by our classification; n=6
remains a legal aim.  Recorded as failure 13 in NEXT_STEPS: a
"theorem" cited without a register row is a claim, not a floor.

## NEXT_STEPS.md updated to the Run-28 state

New §2a (the SAT data reviewed); failure 13; P2 renewed for the
T-263 family; P1' updated with the generic-contact guidance; §0
status table and run-28 entry.  Copies: NEXT_STEPS.md and
download/NEXT_STEPS.md.

Score {22.819977568:.9f} (unchanged — review run); download table/
csv copies in sync (no table change).
"""
readme = open(f"{W}/README.md").read()
if "Run 28 (2026-11-06)" not in readme:
    open(f"{W}/README.md", "w").write(readme + sec)
    print("2. README Run 28 appended")
else:
    print("2. README already has Run 28 (idempotent)")

# ---------------------------------------------------- 3. REPRODUCE A20
rep = open(f"{W}/REPRODUCE.md").read()
if "## A20." not in rep:
    rep += """

## A20. Run 28: SAT data review

```bash
python3 scripts/sat_review.py        # the SAT-data instrument (new)
python3 scripts/deliver28.py         # this run's deliverables
```
"""
    open(f"{W}/REPRODUCE.md", "w").write(rep)
    print("3. REPRODUCE A20 appended")
else:
    print("3. REPRODUCE already has A20 (idempotent)")

# ------------------------------- 4. RUN_NOTES.md alias + run28_NOTES.md
shutil.copy(f"{W}/README.md", f"{W}/RUN_NOTES.md")
print("4a. RUN_NOTES.md refreshed")
readme = open(f"{W}/README.md").read()
i = readme.find("# Run 28 (2026-11-06)")
notes = ("# Run 28 notes (2026-11-06)\n\n"
         "Run documentation under the distinct name.  The same content "
         "is in README.md (Run 28 section), RUN_NOTES.md, and "
         "download/run28/README.md.\n"
         + readme[i:])
open(f"{W}/download/run28_NOTES.md", "w").write(notes)
print("4b. download/run28_NOTES.md written")

# ------------------------------------------- 5. top-level download README
shutil.copy(f"{W}/README.md", f"{W}/download/README.md")
print("5. download/README.md refreshed")

# ---------------------------------------------------- 6. run28 tree
shutil.rmtree(DL, ignore_errors=True)
NEW = [
 ("scripts/sat_review.py", "NEW",
  "SAT-data instrument: per-pair margins, normals, types, walls, "
  "free squares, Maxwell ratios over all 1000 packings"),
 ("scripts/deliver28.py", "NEW", "this build script"),
 ("workspace/push/sat_review28.json", "NEW", "SAT-data ledger"),
 ("README.md", "EDITED", "Run 28 section"),
 ("REPRODUCE.md", "EDITED", "A20 section"),
 ("NEXT_STEPS.md", "EDITED",
  "Run-28 state: §2a SAT insight, failure 13, P2 renewed, P1' guidance"),
 ("run28_outcomes.json", "NEW", "run 28 ledger (also at download/ top)"),
]
rows = []
for rel, st, what in NEW:
    dst = os.path.join(DL, rel)
    os.makedirs(os.path.dirname(dst) or DL, exist_ok=True)
    src = (f"{W}/download/run28_outcomes.json"
           if rel == "run28_outcomes.json" else f"{W}/{rel}")
    if os.path.exists(src):
        shutil.copy(src, dst)
        rows.append((rel, st, os.path.getsize(dst), what))

man = ["# Run 28 deliverables — new/edited files only",
       "",
       "| Repository path | Status | Bytes | What it is |",
       "|---|---|---|---|"]
for rel, st, sz, what in rows:
    man.append(f"| {rel} | {st} | {sz} | {what} |")
man += ["",
        "No table change this run (review only); the standing channel "
        "was last run in run 27.",
        "download table.json/submission.csv/NEXT_STEPS.md refreshed in "
        "sync (table unchanged).",
        "No .pyc (ast.parse verification only)."]
open(f"{DL}/MANIFEST.md", "w").write("\n".join(man) + "\n")
print("6. download/run28/ tree built:", len(rows), "files")

# ---------------------------------------------------- 7. verification
for rel, st, sz, what in rows:
    if rel.endswith(".py"):
        ast.parse(open(f"{DL}/{rel}").read())
    if rel.endswith(".json"):
        json.load(open(f"{DL}/{rel}"))
bad = [f for _, _, fs in os.walk(DL) for f in fs if f.endswith(".pyc")]
assert not bad, bad
print("7. verification clean")
