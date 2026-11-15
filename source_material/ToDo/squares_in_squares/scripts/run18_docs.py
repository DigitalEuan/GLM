#!/usr/bin/env python3
"""run18_docs.py — run 18 ledger + snapshot note + docs refresh.

Run 18 scope (user asks 1-3):
 1. polish to completion + three-band/free-anchor if needed;
 2. note the GitHub snapshot (system of record) + doc refresh;
 3. cent_compiler_v12_2 extension + finer Pressure-Settling Engine.
"""
import json
import os

DL = "/home/z/my-project/download"

ledger = {
 "run": 18,
 "date": "2026-11-05",
 "state_in": "frontier 22.823536 / 454 (restored from the GitHub snapshot "
             "after another sandbox recycle; snapshot table = run-10 "
             "22.887471, replayed import(76)+chains(33) to the frontier)",
 "asks": [
   "1. run polish to completion; then a three-band / free-anchor "
   "generalization at the 23 gap-0 roots - if needed to complete that "
   "investigation",
   "2. note https://github.com/DigitalEuan/squares_in_squares as the "
   "project snapshot (has everything + latest submission.csv); docs not "
   "up to date; user keeps local iterations and can add missing files",
   "3. push/extend cent_compiler (v12_2 on the GLM repo); the "
   "Pressure-Settling Engine came from it; extend with more primitives "
   "(NumPy/SciPy as wheels/datasets) toward a finer engine for the "
   "remaining grids"],
 "results": {
  "polish": "run to completion this round (bg); ledger "
            "workspace/push/polish_results.json; recorded honestly",
  "three_band": "gobel7 not needed for the polish investigation; the "
                "two-band gobel6 honest negative (run 17) + polish result "
                "close the coarse-resolution question; next family only "
                "warranted with a new architecture idea",
  "snapshot_note": "documented in README/REPRODUCE; the snapshot is now the "
                   "system of record (its submission.csv scores 22.823536/454 "
                   "— the frontier; the sandbox replays from it after recycles)",
  "sync_list": [
      "workspace/sources/atlas/lists/certs/n-XXX.cert.gz (324 files) — the "
      "snapshot lost them (only best.json survived); fetchable via "
      "scripts/fetch_atlas.py or copy from a local iteration",
      "workspace/push/gobel6_results.json (run-17 version: tested 15183, "
      "0 fails, 0 records, 1480 near-misses) — the snapshot's copy is the "
      "run-17 one (kept), fine",
      "run-16/17 outcome ledgers if not already in the snapshot",
      "cent_compiler_v12_2 WITH W36/W37 + the wheels.py parser fix — "
      "see download/cent_compiler_v12_2_ext.zip"],
  "cent_v12_2": {
    "location": "fetched from github.com/DigitalEuan/GLM "
                "source_material/ToDo/cent_compiler_v12_2",
    "extension": [
      "W36 Numerical SAT Substrate (NumPy): pair_energy = pen^2, "
      "wall_energy = out^2 — the packing objective as wheel laws "
      "(4 cases, negative controls included)",
      "W37 Viscoelastic Settling (SciPy): relaxation_time = eta/modulus, "
      "strain_rate = stress/viscosity, dissipated_power = stress*strain_rate "
      "(4 cases; junctions to W20 piezo and W36)",
      "junctions/non-identities added to wheels/index.json (the loader only "
      "reads them from there — per-wheel arrays are ignored): 37 junctions, "
      "7 non-identities total",
      "PARSER FIX (upstream bug): wheels.py rejected rational ^powers "
      "('a power must be an integer literal') so case_table() CRASHED on "
      "the native wheel corpus (W21/W24/W25/W29/W34 use ^(1/2)); "
      "parse_monomial + Monomial.pow now accept numeric literal "
      "rational exponents; case_table() runs all 127 rows"],
    "pressure_settle_v2": {
      "design": "compiled from W36+W37 like run 6 compiled the physics "
                "wheels: exact SAT substrate (same math as packlib.verify) "
                "+ scipy L-BFGS-B with ANALYTIC gradients (chain rule "
                "through the SAT stack; binding-axis selection per pair) "
                "+ pressure ramp (container annealed grid+0.5 -> target) "
                "+ crystalline PHI seeds + symmetry-breaking kicks",
      "debugging": [
        "self-test gate exposed a best-tracking bug (roomy-L states were "
        "scored); fixed to terminal-at-L_target evaluation",
        "analytic gradient was wrong (FD check): angle channel rewritten "
        "with exact Gram-entry formulas (du/dth = v, dv/dth = -u); "
        "factor-2 pair-counting bug fixed; FD now < 1e-8 on 6 random "
        "states (gate added to the self-test)",
        "wall channel exact: dout/dth = dHW/dth * (#active walls)"],
      "outcome": "HONEST NEGATIVE at this resolution: the engine clears "
                 "the gradient-exactness gate but does NOT clear the two "
                 "feasible containers (n=5 L=2.75, n=13 L=4.0) — the "
                 "creep+ramp+local-relax channel cannot cross the "
                 "rearrangement gap into the tilted configurations; per "
                 "the run-6 requirement the campaign ABORTED (nothing it "
                 "would say about the 23 roots would mean anything)",
      "reading": "the negative is informative: exact gradients + ramps do "
                 "not replace global structure — the frontier's "
                 "configurations (per the run-16 decode) are banded "
                 "architectures, and reaching them from lattice seeds "
                 "needs the constructive channel (gobel families), not "
                 "finer local dynamics. The engine stands ready with a "
                 "verified-exact gradient for any future role that is "
                 "local (e.g. polishing band anchors/angles — P2-style "
                 "refinement, its natural use)"}}}}
json.dump(ledger, open(os.path.join(DL, "run18_outcomes.json"), "w"), indent=1)
print("run18 ledger saved")

# README/REPRODUCE notes
with open(os.path.join(DL, "README.md"), "a") as f:
    f.write("""

# Run 18 (2026-11-05): snapshot as system of record + cent v12_2

**The project now has a GitHub snapshot of record:**
https://github.com/DigitalEuan/squares_in_squares — it carries everything
done so far and the most up-to-date `submission.csv` (scores 22.823536,
454/1000 — the current frontier). After this sandbox's recycles the
snapshot is the replay source: restore `workspace/` + `scripts/` from it,
re-fetch the register certs (`python3 scripts/fetch_atlas.py`), then
`import_atlas` + `cascade3` + `closure_apply` + `final_assembly` to
rebuild the frontier (verified twice this run).

Files the snapshot is missing (user can add from local iterations):
- `workspace/sources/atlas/lists/certs/` — 324 register certificate files
  (only best.json survived; `fetch_atlas.py` re-fetches them live);
- run-16/17 `*_outcomes.json` ledgers (this download/ carries them);
- `cent_compiler_v12_2` WITH the extension (see
  `cent_compiler_v12_2_ext.zip` — W36/W37 wheels + the wheels.py
  rational-power parser fix).

## cent_compiler v12_2 extension (user ask 3)

Fetched from the GLM repo. Extended (workspace/cent_compiler_v12_2,
delivered as `cent_compiler_v12_2_ext.zip`):
- **W36** Numerical SAT Substrate (NumPy) and **W37** Viscoelastic
  Settling (SciPy) as proper wheels (monomial laws, 4 cases each with
  negative controls, dimensions, junctions) — 33 wheels total;
- junctions/non-identities moved into `wheels/index.json` (the loader
  only reads those — per-wheel arrays are silently ignored);
- **upstream parser fix**: `wheels.py` rejected rational `^(1/2)`-style
  powers, so `case_table()` crashed on the native corpus (W21/W24/W25/
  W29/W34); now all 127 rows run.

## Pressure-Settling Engine v2 (pressure_settle.py)

Compiled from W36+W37 (the run-6 pattern). Exact analytic gradient
through the SAT stack (FD-verified < 1e-8, gated in the self-test),
pressure ramp, crystalline seeds, symmetry-breaking kicks. Outcome:
**honest negative** — it clears gradient-exactness but not the two
feasible containers; per the run-6 rule the campaign aborted. Reading:
local dynamics cannot cross the rearrangement gap into tilted banded
architectures; the engine's natural role is local refinement (polish),
not discovery. Full details: `run18_outcomes.json`.
""")
print("README updated")

with open("/home/z/my-project/REPRODUCE.md", "a") as f:
    f.write("""

## A10. Run 18: snapshot recovery + cent extension

```bash
# snapshot restore (after a recycle): clone DigitalEuan/squares_in_squares,
# rsync scripts/ workspace/ json/ into the project, then:
python3 scripts/fetch_atlas.py            # re-fetch the 324 register certs
python3 scripts/import_atlas.py          # 76 applied, 0.050264
python3 scripts/cascade3.py && python3 scripts/closure_apply.py
python3 scripts/final_assembly.py        # 22.823536 / 454
python3 scripts/polish.py                # P2 (long; bg)
python3 scripts/pressure_settle.py       # cent engine v2 (selftest-gated)
```
""")
import shutil
shutil.copy("/home/z/my-project/REPRODUCE.md",
            os.path.join(DL, "REPRODUCE.md"))
print("REPRODUCE updated")
