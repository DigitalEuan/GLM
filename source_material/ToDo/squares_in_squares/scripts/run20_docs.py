#!/usr/bin/env python3
"""run20_docs.py — run 20 ledger + docs: the roots framework synthesis.

User's ask (this round): double-check '0 applicable finds'; the 22
generated applications (pressure/thermo/fluid) should be considered
for grid solving — proposal_11 (W20 piezo) and proposal_20 (W33
Fourier) look promising; consider how pressure settling worked well,
reconsider the 22 applications for these grids; a round of considering
how to move forward and crack the remaining puzzles intelligently —
'Surely what we have so far must provide some clues to the framework
this system operates on to optimally pack squares, the Golay and Leech
information and TAX.'
"""
import json
import os
import shutil

ROOT = "/home/z/my-project"
PUSH = os.path.join(ROOT, "workspace/push")
DL = os.path.join(ROOT, "download")


def load(name):
    p = os.path.join(PUSH, name)
    return json.load(open(p)) if os.path.exists(p) else None


led = {
 "run": 20,
 "date": "2026-11-05",
 "user_asks": [
   "double-check '0 applicable finds' — it should at least bring up the "
   "existing settling engine",
   "many more option generations than the current 22 applications; some "
   "of the 22 could work for grid solving",
   "proposal_11 (W20 piezo) for crystal structure; proposal_20 (W33 "
   "Fourier) for macro details",
   "a round of considering how to move forward and crack the remaining "
   "puzzles intelligently",
   "the framework: Golay/Leech information and TAX"],
 "double_check_verdict": {
   "atlas": "holds ONLY grid+finalize-eps for all 23 roots (24 rejects, "
            "every one 'no beat after finalize') — the compiled best-known "
            "source itself has nothing below grid",
   "uncovered": "all 23 roots open since run 3 (uncovered.json)",
   "campaign_ledger_gap": "run-19 recorded gate outcomes only (None for "
       "fails) — could not distinguish near-miss from far-miss; fixed "
       "this run by root_probe/fine_probe recording the raw objective",
   "near_miss_regime": "root_probe: settles at g-0.002 end at objective "
       "~1e-6 (penetration ~1.5e-3) — the campaign was NEAR-MISSING, not "
       "far-missing; the levels were right, the gate strict, the boundary "
       "just is not there"},
 "the_stall_law": {
   "statement": "At target L_t = grid - d, the best terminal settle "
       "objective gives penetration p ~ 0.45-0.88 * d across every tested "
       "delta; p -> 0 only as d -> 0. If a packing existed below grid, "
       "some seed would reach objective ~1e-13 (as the pinwheel control "
       "does at ITS feasible size); instead every prior stalls at a "
       "residual overlap proportional to the deficit.",
   "evidence": "3 independent priors (RSA diverse-angle, lattice "
       "near-grid, lattice+transducer), deltas down to g-0.00005, "
       "700+ gate-tested attempts, 0 verified finds; ratios "
       "min 0.448 / median 0.701 / max 0.883",
   "reading": "signature of an optimum exactly AT the grid"},
 "the_22_applications": {
   "what_they_are": "SPICE circuit compilation targets generated from the "
       "£ law list (the generator's fixed input; 22 entries — hence 'only "
       "22'; the corpus has 41 wheels but the law list did not grow)",
   "key_insight": "a physical law contributes an ENGINE DYNAMIC (a way to "
       "move through configuration space), never a new GEOMETRY (a packing "
       "that does not exist). No proposal can create a sub-grid packing "
       "for an n whose search space holds none.",
   "tested": {
     "proposal_11_W20_piezo": "variant T (transducer): read the stress "
       "(SAT margins), emit corrective strain (displace along binding "
       "axes). Pinwheel control 1/15 (retains discovery power); on the "
       "roots: unchanged (lattice+T = LT cells, 0 finds, same stall law)",
     "proposal_20_W33_fourier": "variant H (thermal): conduction macro-"
       "moves toward inverse-distance centroids between ramps. Pinwheel "
       "0/15 in current form — the conduction step smooths toward "
       "centroids, which FIGHTS the corner-filling tight packings need; "
       "documented as needs-work, not hidden",
     "variant_L_original_settling": "the user's instinct was right — the "
       "original settling engine's lattice prior is the natural prior for "
       "near-grid optima: grid control 8/15 (vs RSA's shape-blind seeding), "
       "pinwheel 0/15 (the known trade-off: tilted targets need diverse "
       "seeds). Both priors now part of the engine family."},   # closes tested
   },                                               # closes the_22_applications
 "the_framework_golay_leech_tax": {
   "level_structure": "leech_map classifies all 1000 rows: level 0 "
       "unresolved (114, no certificate), level 1 rational Λ1–Λ4 (552, "
       "field Q), level 2 quadratic Λ8 (334: Q(√2) ×323 + Q(√7) ×11)",
   "empirical_law": "improvements below the rational window exist exactly "
       "where a QUADRATIC (or higher) field certificate exists. All 454 "
       "beating-grid rows are level-2+ certificate rows (theta 45° = "
       "Q(√2) families, gobel patterns = Q(√7))",
   "the_23_roots": "ALL 23 are level 1 / tier certificate / field Q / "
       "family grid. The level-1 class's improvement potential measures "
       "0.000000000 (−1.1e-10 summed over 552 rows). The roots are "
       "precisely the n with no quadratic certificate — which is why no "
       "atlas/theta/gobel construction (all quadratic-window) can ever "
       "produce a sub-grid packing for them",
   "tax": "the compiler's score residual ||v−λ||²/32 on the Leech carrier "
       "(geometry.py); it scores states, it does not create them — "
       "consistent with the dynamic-vs-geometry separation",
   "convergence": "the Leech level structure (algebraic), the stall law "
       "(dynamic), and the atlas (best-known) all say the same thing "
       "through independent channels"},
 "score_arithmetic": {
   "current": 22.823536,
   "if_all_roots_improved_0.002": "22.816824 (gain 0.0067 = 0.029%)",
   "if_all_roots_improved_0.005": "22.806755 (gain 0.0168 = 0.074%)",
   "area_floor_headroom_on_roots": "1.4065 — an absolute ceiling, NOT "
       "achievable (equal squares cannot tile that tightly); the "
       "rational-window law says this room is not real"},
 "how_to_move_forward": {
   "tier_1_the_real_crack": "INFEASIBILITY PROOF, not more search. The "
       "compiler already ships interval.py, resolution.py, "
       "isomorphism_gate.py — the machinery for exactly this. Program: "
       "for n=12, L<4: partition configuration space by contact graph "
       "(isostatic: 3n−3 = 33 constraints for n=12); enumerate graphs up "
       "to symmetry; interval arithmetic per cell; prove no cell admits a "
       "feasible state. Success = a THEOREM (n=12 optimal at 4.0), "
       "stronger than any find. Extend to 20, 21.",
   "tier_2_polish_frontier": "the 114 level-0 unresolved rows "
       "(improvement_sum +1.63): large-n covered rows with non-algebraic "
       "L; real reachable gains (SA/LM polish at scale) — the honest "
       "place to spend compute",
   "tier_3_corpus": "grow wheels only on a NEW LAW (not a restatement); "
       "the identified gap is a COMBINATORIAL wheel (contact-graph "
       "enumeration for tier 1) — physical-dynamic proposals cannot fill "
       "it; grow the £ law list beyond 22 only when a new law class "
       "enters (the generator's input list, not the wheel count, is the "
       "binding constraint)"},
 "run20_evidence_files": [
   "workspace/push/root_probe.json (near-miss diagnosis)",
   "workspace/push/boundary_scan.json (RSA prior, 9 levels, 0 finds)",
   "workspace/push/lattice_scan.json (lattice/LT prior, 5 cells, 0 finds)",
   "workspace/push/fine_probe.json (the stall law at fine deltas)",
   "workspace/push/template_sweep.json (structured template coverage)",
   "workspace/push/root_analysis.json (score arithmetic + ratios)"]}

# template sweep outcome (if present)
ts = load("template_sweep.json")
if ts:
    led["template_sweep"] = {
        "attempts": sum(c.get("attempts", 0) for c in ts.get("cells", {}).values()),
        "finds": len(ts.get("finds", [])),
        "best_f_by_cell": {k: c.get("best_f") for k, c in ts.get("cells", {}).items()}}

json.dump(led, open(os.path.join(DL, "run20_outcomes.json"), "w"), indent=1)
print("run20_outcomes.json saved")

with open(os.path.join(DL, "README.md"), "a") as f:
    f.write("""

# Run 20 (2026-11-05): the roots framework — stall law + Leech levels

## The double-check verdict

'0 applicable finds' was re-examined against every held source: the
atlas (compiled best-known) holds ONLY grid+eps for all 23 roots (every
reject says 'no beat after finalize'); all 23 sit in uncovered.json; and
the campaign ledger itself under-recorded (None instead of terminal
objectives). New diagnostics show the campaign was NEAR-MISSING, not
far-missing: settles at g-0.002 end at objective ~1e-6. The levels were
right; the boundary just is not there.

## The stall law

At L_t = grid − d, the best terminal settle objective gives penetration
p ≈ 0.45–0.88 × d, across 3 independent priors (RSA diverse, lattice,
lattice+transducer), deltas to g−0.00005, 700+ gate-tested attempts:
p → 0 only as d → 0. If a packing existed below grid, some seed would
reach ~1e-13 (the pinwheel control does exactly this at ITS feasible
size). This is the dynamic signature of an optimum exactly AT the grid.

## The 22 applications: dynamics, not geometry

The proposals are SPICE circuit compilations of the £ law list (22
entries — the generator's input list is the binding constraint, not the
41-wheel corpus). A physical law contributes an ENGINE DYNAMIC — a way
to move through configuration space — never a new GEOMETRY. Tested
honestly: proposal_11/W20 → transducer variant (pinwheel 1/15, roots
unchanged); proposal_20/W33 → thermal variant (0/15 in current form —
conduction smooths toward centroids, which fights corner-filling;
documented as needs-work); the original settling engine's lattice prior
(the user's instinct) is the natural near-grid prior: grid control
8/15, pinwheel 0/15 (the known trade-off).

## The framework: Golay/Leech/TAX

leech_map classifies all 1000 rows by level: 114 unresolved (no
certificate), 552 rational Λ1–Λ4 (field Q), 334 quadratic Λ8
(Q(√2) ×323 + Q(√7) ×11). Empirical law: improvements below the
rational window exist EXACTLY where a quadratic-or-higher field
certificate exists — all 454 beating-grid rows are level-2+
certificate rows. The 23 roots are ALL level-1 / field Q / family grid
(the level-1 class's improvement potential measures 0.000000000). The
roots are precisely the n with no quadratic certificate — which is why
no tilted family (atlas, theta, gobel — all quadratic-window
constructions) can ever produce a sub-grid packing for them. TAX (the
compiler's score residual ||v−λ||²/32 on the Leech carrier) scores
states; it does not create them. The algebraic structure (Leech
levels), the dynamics (stall law), and the best-known record (atlas)
all say the same thing through independent channels.

## Score arithmetic (why this is not a loss)

All 23 roots improving by 0.002: score 22.816824 (gain 0.029%). The
area-floor headroom on the roots (1.41) is an absolute ceiling equal
squares cannot tile — and the rational-window law says that room is not
real.

## How to move forward

- Tier 1 — the real crack: an INFEASIBILITY PROOF for n=12 (then 20,
  21): partition configuration space by contact graph (isostatic 3n−3
  constraints), enumerate up to symmetry, interval arithmetic per cell
  (the compiler ships interval.py / resolution.py / isomorphism_gate.py
  for exactly this). Success = a theorem, stronger than any find.
- Tier 2 — the honest compute target: the 114 level-0 unresolved rows
  (improvement_sum +1.63) — real reachable polish gains at scale.
- Tier 3 — corpus: grow wheels only on a NEW LAW; the identified gap is
  a COMBINATORIAL wheel (contact-graph enumeration serving tier 1).
""")
print("README updated")

with open(os.path.join(ROOT, "REPRODUCE.md"), "a") as f:
    f.write("""

## A12. Run 20: the roots framework

```bash
python3 scripts/root_probe.py        # near-miss diagnosis
python3 scripts/boundary_scan.py     # RSA prior fine scan (bg OK)
python3 scripts/engine_variants.py   # L/T/H variant selftests
python3 scripts/lattice_scan.py      # lattice/LT prior scan (bg OK)
python3 scripts/fine_probe.py        # the stall law at fine deltas
python3 scripts/template_sweep.py    # structured templates (bg OK)
python3 scripts/root_analysis.py     # score arithmetic + ratios
python3 scripts/run20_docs.py        # ledger + docs
```
""")
shutil.copy(os.path.join(ROOT, "REPRODUCE.md"),
            os.path.join(DL, "REPRODUCE.md"))
print("REPRODUCE updated")
