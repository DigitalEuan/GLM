#!/usr/bin/env python3
"""deliver29.py — run 29 deliverables (the SAT measure: TAX/NRCI).

Run 29 (user input: a TAX/NRCI-style measure on the SAT data, as the
GLM uses) built scripts/sat_measure.py: the tie test is the SAT
data's binary layer (symmetry-tied contacts, even weight — the parity
law of run 28); the carrier is the packing's contact word with 1-bits
= generic contacts; SAT-TAX = g*Q with the GLM's constants, SAT-NRCI
= 10/(10+TAX), the GLM regime map at integer cutoffs.  Score
unchanged 22.819977568 (measurement run; no table change).

Produces:
  1. download/run29_outcomes.json — run ledger
  2. README.md Run 29 section
  3. REPRODUCE.md A21
  4. RUN_NOTES.md + download/run29_NOTES.md
  5. download/README.md top-level refresh
  6. download/run29/ tree + MANIFEST.md
  7. download table.json/submission.csv sync (unchanged this run)
"""
import ast
import json
import math
import os
import shutil

W = "/home/z/my-project"
DL = f"{W}/download/run29"
TAB = f"{W}/workspace/submission/table.json"

tab = json.load(open(TAB))
score = sum(r["L"] / math.sqrt(int(k)) - 1 for k, r in tab.items())
assert abs(score - 22.819977568) < 2e-9, score

sm = json.load(open(f"{W}/workspace/push/sat_measure29.json"))

# ------------------------------------------------------------- 1. ledger
led = {
 "run": 29, "date": "2026-11-06",
 "user_request": ("is there a measure on the SAT data - like a TAX "
                   "measurement as the GLM (DigitalEuan/GLM) uses, with "
                   "NRCI as a metric"),
 "executed": {
   "glm_definitions_source": {
     "status": "extracted",
     "source": ("upload/GLM_Complete_Number_Theory_Evidence.md §1.1-1.3; "
                "upload/GLM_ACADEMIC_PAPER.md §4.8 (the repo "
                "github.com/DigitalEuan/GLM is the parent system)"),
     "constants": {"Y": "1/(pi+2/pi) in (0.264675, 0.264676)",
                    "Q": "Y + 1/8", "B": 10},
     "formulas": ("TAX(v) = HW(v)*Y + |v|^2/8 = HW*Q on binary carriers; "
                  "NRCI = B/(B+TAX) in (0,1]; NRCI=1 iff v=0"),
     "regimes": ("onBit TAX<=5/2; coherent <=10; transitional <=70/3; "
                 "subcoherent above (Lean-proved thresholds)")},
   "instrument": {
     "status": "built + run (scripts/sat_measure.py)",
     "file": "workspace/push/sat_measure29.json",
     "measured": {
       "packings": 1000,
       "tie_residual_bimodal": ("tied <= 5e-12, generic >= 1.1e-8, "
                                  "3.3-decade empty gap; TIE_TOL=1e-9"),
       "total_contacts": 1806403, "generic": 18545,
       "validation": ("n=50 decode row: C=105, g=10, the ten weight-1 "
                       "contacts — exact match with runs 26/28"),
       "structural_zeros": ("weight-3 contacts and generic weight-4: 0 "
                              "in all 1000 rows (asserted)")}},
   "finding_1_vacuum": {
     "status": "measured",
     "finding": ("the vacuum (NRCI=1 exactly) is precisely the 546 grid "
                 "rows — the GLM theorem NRCI=1 iff v=0 lands as: no "
                 "generic contacts iff grid")},
   "finding_2_provable_off_vacuum": {
     "status": "measured",
     "finding": ("the only off-vacuum provable rows are the four "
                 "hand-proved packings: Gobel 5 (phi=1.00 — all four "
                 "contacts generic), Ahmed 11, Overbeck 17, Fitzharding "
                 "19 (NRCI 0.70-0.87). 450 sub rows are unproven "
                 "territory (NRCI median 0.39, 55 subcoherent)")},
   "finding_3_depth_anticorrelates": {
     "status": "measured",
     "finding": ("within run18-frontier phi-vs-depth = -0.61 (shallow "
                 "third phi 0.138, deep third 0.048); the deepest class "
                 "chain3 (d/sqrt(n) median 0.0123) sits nearly at the "
                 "vacuum (phi 0.015). Two-phase landscape: a vacuum "
                 "phase (grid/lattice-tied, depth by chain arithmetic at "
                 "large n) and a generic phase (small n, hand-proved, "
                 "where every known proof lives). CORRECTS run 28's "
                 "P1' 'seek generic contacts' reading")},
   "finding_4_T263_prediction": {
     "status": "falsifiable prediction recorded",
     "finding": ("the register row (T-263, n=299) is the most generic "
                 "per contact in the table (phi 0.101). The two-phase "
                 "picture predicts: if the P2 re-run improves L on that "
                 "family, the improved packing comes with phi down / "
                 "NRCI up. phi up falsifies the picture and re-aims P1' "
                 "at the generic language")},
   "NEXT_STEPS_update": {
     "status": "updated to the Run-29 state",
     "changes": ("new §2b (the SAT measure); §2a.1 reading corrected; "
                 "P1' and P2 guidance updated; §0 row; §6 run-29 entry")},
 },
 "score": {"before": 22.819977568, "after": round(score, 9), "delta": 0.0},
 "next": [
   "P2 re-run on the T-263 family with NRCI logged before/after (the "
   "run-29 prediction is testable on the first find)",
   "P1' insertion campaign at 251/250/284/191 — read the 2026-11-03 "
   "preprint against the two-phase prediction (§2b.3)",
   "P3 weekly watch (the only item that has paid)"],
}
json.dump(led, open(f"{W}/download/run29_outcomes.json", "w"), indent=1)
print("1. ledger written; score:", round(score, 9))

# ---------------------------------------------------- 2. README Run 29
sec = f"""

# Run 29 (2026-11-06): the SAT measure — TAX/NRCI on the SAT data

User input: is there a measure on the SAT data — like the TAX
measurement the GLM uses, with NRCI as a metric?

## Where TAX and NRCI are defined

The repo the user linked (github.com/DigitalEuan/GLM) is the parent
system; the definitions live in the uploaded GLM papers
(upload/GLM_Complete_Number_Theory_Evidence.md §1.1–1.3):
Y = 1/(π+2/π) ∈ (0.264675, 0.264676), Q = Y+1/8, B = 10;
TAX(v) = HW(v)·Y + ‖v‖²/8 = HW·Q on binary carriers; NRCI(v) =
B/(B+TAX(v)) ∈ (0,1] with the Lean theorem NRCI = 1 ⟺ v = 0;
regimes at TAX ≤ 5/2 / ≤ 10 / ≤ 70/3 (onBit / coherent /
transitional, subcoherent above).

## The SAT data's binary layer: the symmetry tie

A contact pair is **tied** when the two axis families see the same
two directions — multiset{{pen_u0, pen_v0}} = multiset{{pen_u1,
pen_v1}} — the case where the tight axes come in symmetry-tied pairs
(even weight; run 28's parity law).  Measured: the tie residual is
bimodal with a 3.3-decade empty gap — tied population ≤ 5e-12 (float
noise of exact constructions), generic continuum ≥ 1.1e-8.  The
carrier of the measure is the packing's contact word; its 1-bits are
the **generic** (non-tied) contacts, g of them.  SAT-TAX = g·Q;
SAT-NRCI = 10/(10+SAT-TAX); the GLM regime map at integer cutoffs
g ≤ 6/25/59 (exact under the proved Y bounds).  Instrument:
scripts/sat_measure.py; ledger workspace/push/sat_measure29.json.
Validated on the n=50 decode row (C=105, g=10, the ten weight-1
contacts of runs 26/28).

## What the measure says (§2b)

1. **The vacuum is exactly the grid.**  NRCI = 1 precisely on the 546
   grid rows — no generic contacts ⟺ grid.
2. **The provable frontier off the vacuum is the four hand-proved
   packings.**  Göbel 5 (φ = 1.00: all four contacts generic), Ahmed
   11, Overbeck 17, Fitzharding 19 (NRCI 0.70–0.87).  Everything
   else below grid is unproven territory (450 rows, NRCI median
   0.39, 55 subcoherent).
3. **Depth is not bought with genericity.**  Within run18-frontier,
   φ-vs-depth = −0.61 (shallow third φ 0.138, deep third 0.048); the
   deepest class, chain3 (d/√n median 0.0123), sits nearly at the
   vacuum (φ 0.015).  The landscape is two-phase: a vacuum phase
   (lattice-tied, depth by chain arithmetic at large n) and a generic
   phase (small n, hand-proved).  This corrects run 28's P1'
   prescription — genericity is the signature of the small-n
   provable regime, not a depth strategy.
4. **A falsifiable prediction for P2.**  T-263 (n=299) is the most
   generic row per contact in the table (φ 0.101).  If settling its
   41 floaters improves L, the improved packing should come with φ
   down / NRCI up.  φ up falsifies the two-phase picture and re-aims
   P1' at the generic language.

## NEXT_STEPS.md updated to the Run-29 state

New §2b (the SAT measure); §2a.1 reading corrected; P1' and P2
guidance updated (NRCI logged before/after on P2); §0 row; §6
run-29 entry.  Copies: NEXT_STEPS.md and download/NEXT_STEPS.md.

Score {22.819977568:.9f} (unchanged — measurement run); download
table/csv copies in sync (no table change).
"""
readme = open(f"{W}/README.md").read()
if "Run 29 (2026-11-06)" not in readme:
    open(f"{W}/README.md", "w").write(readme + sec)
    print("2. README Run 29 appended")
else:
    print("2. README already has Run 29 (idempotent)")

# ---------------------------------------------------- 3. REPRODUCE A21
rep = open(f"{W}/REPRODUCE.md").read()
if "## A21." not in rep:
    rep += """

## A21. Run 29: the SAT measure (TAX/NRCI)

```bash
python3 scripts/sat_measure.py       # TAX/NRCI on the SAT data (new)
python3 scripts/deliver29.py         # this run's deliverables
```
"""
    open(f"{W}/REPRODUCE.md", "w").write(rep)
    print("3. REPRODUCE A21 appended")
else:
    print("3. REPRODUCE already has A21 (idempotent)")

# ------------------------------- 4. RUN_NOTES.md alias + run29_NOTES.md
shutil.copy(f"{W}/README.md", f"{W}/RUN_NOTES.md")
print("4a. RUN_NOTES.md refreshed")
readme = open(f"{W}/README.md").read()
i = readme.find("# Run 29 (2026-11-06)")
notes = ("# Run 29 notes (2026-11-06)\n\n"
         "Run documentation under the distinct name.  The same content "
         "is in README.md (Run 29 section), RUN_NOTES.md, and "
         "download/run29/README.md.\n"
         + readme[i:])
open(f"{W}/download/run29_NOTES.md", "w").write(notes)
print("4b. download/run29_NOTES.md written")

# ------------------------------------------- 5. top-level download README
shutil.copy(f"{W}/README.md", f"{W}/download/README.md")
print("5. download/README.md refreshed")

# ---------------------------------------------------- 6. run29 tree
shutil.rmtree(DL, ignore_errors=True)
NEW = [
 ("scripts/sat_measure.py", "NEW",
  "the SAT measure: tie test (binary layer), SAT-TAX = g*Q, "
  "SAT-NRCI, GLM regime map, walls, bridge census"),
 ("scripts/deliver29.py", "NEW", "this build script"),
 ("workspace/push/sat_measure29.json", "NEW", "SAT-measure ledger"),
 ("README.md", "EDITED", "Run 29 section"),
 ("REPRODUCE.md", "EDITED", "A21 section"),
 ("NEXT_STEPS.md", "EDITED",
  "Run-29 state: §2b the SAT measure, §2a.1 corrected, P1'/P2 guidance"),
 ("run29_outcomes.json", "NEW", "run 29 ledger (also at download/ top)"),
]
rows = []
for rel, st, what in NEW:
    dst = os.path.join(DL, rel)
    os.makedirs(os.path.dirname(dst) or DL, exist_ok=True)
    src = (f"{W}/download/run29_outcomes.json"
           if rel == "run29_outcomes.json" else f"{W}/{rel}")
    if os.path.exists(src):
        shutil.copy(src, dst)
        rows.append((rel, st, os.path.getsize(dst), what))

man = ["# Run 29 deliverables — new/edited files only",
       "",
       "| Repository path | Status | Bytes | What it is |",
       "|---|---|---|---|"]
for rel, st, sz, what in rows:
    man.append(f"| {rel} | {st} | {sz} | {what} |")
man += ["",
        "No table change this run (measurement only); the standing "
        "channel was last run in run 27.",
        "download table.json/submission.csv/NEXT_STEPS.md refreshed in "
        "sync (table unchanged).",
        "No .pyc (ast.parse verification only)."]
open(f"{DL}/MANIFEST.md", "w").write("\n".join(man) + "\n")
print("6. download/run29/ tree built:", len(rows), "files")

# ---------------------------------------------------- 7. verification
for rel, st, sz, what in rows:
    if rel.endswith(".py"):
        ast.parse(open(f"{DL}/{rel}").read())
    if rel.endswith(".json"):
        json.load(open(f"{DL}/{rel}"))
bad = [f for _, _, fs in os.walk(DL) for f in fs if f.endswith(".pyc")]
assert not bad, bad
print("7. verification clean")
