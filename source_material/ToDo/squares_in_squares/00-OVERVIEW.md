# TCT Square-Packing Table — Project Overview

> Restored from the supplied attachment and aligned with the canonical Run 36 repository state. Historical Run 15/32 values remain in the run ledger.

This is the working repository for the **TCT competition table**: a
1,000-row table of container side lengths `L(n)` for packing `n` unit
squares into the smallest square container, scored as
`Σ (L(n)/√n − 1)` over `n = 1..1000`.

**Current canonical score: 22.642386651** (rounded **22.642387**; Run 36
re-establishment of the Run 35 state: nine Evan Daniel register records and
the n=338 chain conversion; 543/1000 rows beat grid). Run 15's 22.823536
and Run 32's 22.645991 remain historical milestones.

## What exists

| Artifact | Where | Status |
| --- | --- | --- |
| 1,000-row table with per-row provenance | `download/table.json` | stable, 9 sources (`grid`, `exact`, `gobelS`, `gobel2`, `gobel3`, `chain3`, `removal`, `closure`, `aux`) |
| Exact geometric verification of table rows | `download/exact_snap.json` | refreshed on the run-15 frontier (run-14 record: 875/1000; see also `atlas_exact_replay.json`: 76/76 imported states exact-verified in Fraction arithmetic) |
| Galois certificates (minimal polynomials + invariants) | `download/galois_certificates.json` | 1,169 certificates |
| Leech-map cross-check of row geometry | `download/leech_map.json` | 3-tier classification, cross-checked against exact verification |
| Lean formalisation of the layer theory | `workspace/lean/tct_squares/TCT/` | `Basic.lean` compiled (1 deliberate `sorry`); `Layers.lean`/`GolayData.lean`/`Octads.lean` on the real Golay code (run 14) |
| Process audit (score-integrity checks) | `download/process_audit.json` | all checks green |

## The three pillars

1. **The table itself** (`table.json`), with every row carrying its
   construction source and numerical provenance. Rows 1–8, 10, 14,
   15, 24, 35 are provably optimal (literature); 94 rows are provably
   optimal today counting the Nagamochi class (run 12, section B of
   the run log).

2. **Exact verification** (`02-EXACT-VERIFICATION.md`): the geometry
   of every row that has a certificate is re-checked in exact
   `Fraction` arithmetic — container fit and pairwise square
   non-overlap as closed predicates over the certificate field.
   The earlier Run 15 certificate boundary is historical; the Run 36 record
   reports 1,000/1,000 delivered submission rows passing the SAT gate and CSV
   round-trip.

3. **The layer theory** (`01-LAYERS.md`): a perception-layer lattice
   from floor parity (with the real binary Golay code as the
   error-correcting substrate) up through Griess and Conway labels to
   certificates, formalised in Lean 4 / Mathlib.

## Where to read next

- `01-LAYERS.md` — the layer lattice and its Lean formalisation
- `02-EXACT-VERIFICATION.md` — exact verification, what broke, what was fixed, what remains
- `03-REPRODUCE.md` — every command, in order
- `04-RUN-LOG.md` — the condensed ledger of all 14 runs

Data files are in `download/`; scripts in `scripts/` (78); the Lean
project in `workspace/lean/tct_squares/` (Mathlib v4.8.0). The roadmap
is `docs/NEXT_STEPS.md` (from the mimoclaw session); the gap instrument
is `scripts/gap_analysis.py` (validated 11/11 against its published census).
