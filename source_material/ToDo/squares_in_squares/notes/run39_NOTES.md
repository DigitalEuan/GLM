# Run 39 (2026-11-17): the CRAM translation

**User order.** Try the ideas in *Classical Energies Learn to Reason 1,000×
Faster than Looped Models* (Hoover, Blayney, Whittington, arXiv:2611.17309v1)
on the squares task: pseudolikelihood scoring of motif seeds, calibrated
energy thresholds for layer escalation, focused body relaxation, and a
two-layer latent settle.

**Score: unchanged — 22.218056945 (run 38). No push: 0/24 runs below the
record.** The delivered table and `submission.csv` are untouched; this run
adds one instrument, one ledger and one document.

## What was built

`scripts/cram_relax.py` — the W36/W37 hinge energy with the walls free to
translate (a packing's container is its bbox), a single-body Gibbs sampler
reusing `sa_push.anneal`'s schedule (geometric temperature, improving-only
tail), the CRAM variants as *proposal schedules* over the same move grammar,
a relation-cost table fitted at the delivered solutions, and a single-body
fixed-point polish. Ledger: `workspace/push/cram_relax.json`. Document:
`06-CRAM-RELAX.md`.

Two instrument facts worth keeping: the pair penetration agrees with
`packlib.verify` to machine precision and the incremental one-body form
agrees with the matrix form exactly; and a first attempt driven by
`pressure_field.py`'s finite-difference "gradient" stalled, because that
function returns one directional derivative for the whole state rather than
a per-body gradient.

## Measured

* **A (relation cost / PL scoring): stands as a ranking rule.** 21,602
  contacts, 18 relation cells, costs 0.6307 … 10.6741. AUC 1.000 against an
  angle-destroyed control, 0.794 against a position-destroyed control.
  Spearman between the PL score and the energy relaxation reaches:
  0.368 / 0.744 / 0.562 at n = 40 / 70 / 110; the best-scored quarter lands
  0.0722 vs 0.5361, 0.1263 vs 2.9468, 0.1836 vs 2.9076.
* **B (calibrated threshold): does not transfer.** τ = 0 exactly (1000/1000
  delivered packings sit at E ≤ 1e-12). 0/304 corrupted boards accepted;
  lowest corrupted-board energy 7.16e-3. Squeezing the delivered side by
  0.1% already puts 0/400 rows at or below τ (median E 4.33e-4), so the
  threshold grades nothing and an escalation rule would fire on every row.
* **C (focused relaxation): not demonstrated.** Best at n = 20 and gentle
  corruptions; clearly worse once the arrangement is large and damaged
  (n = 240, amp 0.08: 1.17 vs 0.84 for full, +39%) — and that is with each
  selected body getting 6× the moves. The interior is load-bearing in a
  jammed packing; the Sudoku cell is not.
* **D (two-layer): a weak, inconsistent positive.** Never much worse,
  sometimes better (n = 240 amp 0.01: 1.17e-2 vs 1.84e-2; n = 110 amp 0.04:
  7.99e-2 vs 9.21e-2), worse at the extremes.

## Limits stated, not hidden

0/96 matrix runs reached E ≤ 1e-6 and 0/96 reached a single-body fixed
point within four sweeps, so C and D are compared as descent rates at equal
budget, not as solvers. Two seeds per cell, 8,000 moves, no error bars. No
Lean, no intake: an idea from here enters the GLM only through the intake
(study → test → Lean → measured), and the build is the owner's to run.
