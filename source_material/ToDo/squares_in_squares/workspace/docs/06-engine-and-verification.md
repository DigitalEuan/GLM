# 06 — Engine design and the measured/exact split

## The pipeline

```
03_pack_engine (MEASURED search)  ->  found.json / found2.json
05_cent_patterns (EXACT counts)   ->  cascade.json (certified packings)
04_verify_packing (CERTIFICATE)   ->  SAT + containment, margin 1e-9
06_scorecard     (EXACT-ish accounting) -> submission/submission.csv
```

## Measured vs. exact — the UBP discipline applied honestly

Geometric search with rotated squares is transcendental at its core
(cos/sin of free angles): no exact arithmetic exists for the general
position problem. TCT §2 governs: *"if a computation genuinely cannot be
exact, state the error bound explicitly and treat the result as measured."*

- **Measured tier** (engine): float64 positions/angles, deterministic LCG
  (declared seeds — reproducible, no unseeded randomness), energies reported
  as measured.
- **Certificate tier** (verifier): float64 SAT with **declared margin
  1e-9**; every pair checked twice (full scan + AABB-near scan), containment
  via exact-extent bboxes. Soundness (margin ⇒ true non-overlap) is itself a
  named Lean gap — `verification_margin_soundness` — not hand-waved.
- **Exact tier** (accounting): grid scores via integer sqrt bounds;
  cascade counts via exact integer closure arithmetic (two paths); score
  improvement identity checked two ways (per-puzzle δ vs. totals).

## The certificate in numbers

- 30/30 packings certified; minimum separation margin ≥ 1e-9 by construction
  (SAT resolution pushes to zero penetration + 1e-11 slack).
- Coordinates emitted at 12 decimals; rounding perturbs bboxes by ≤ 1e-12 —
  three orders below the certificate margin.
- The submission's L is computed by the organizer from coordinates; our
  L values are bbox-measured and match to 1e-12.

## Consistency evidence for the instrument

The engine's *failures* are as informative as its successes:
- 6@2.9 refused — theorem s(6)=3 (Kearney–Shiu). ✓
- 7@2.95, 8@2.95 refused — theorem s(7)=s(8)=3. ✓
- 2, 3, 4 at grid — trivial optima respected. ✓
- Deep targets jam at E ~ 1e-2 rather than "finding" invalid packings —
  the SAT resolution never reports success with residual penetration
  (success threshold E < 1e-8, certified afterwards independently).

A search instrument that never produces false positives and refuses
impossible targets is exactly what the ledger wants.

## Why continuation beats direct attack

Compressing from a feasible grid preserves *feasibility as an invariant*
at each accepted step (adaptive delta halving on jam). Direct optimization
at the target L from random starts spends its budget escaping infeasible
minima; continuation only ever climbs down through feasible states. The
cost: local minima at structural jams (docs/05's frontier) — the known
weakness of all penalty-relaxation methods (Gensane–Ryckelynck included),
which motif seeding is designed to address.
