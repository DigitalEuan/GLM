# REPRODUCE.md — exact reproduction guide

> **Snapshot note (2026-11-08):** The first verification block below is the
> historical Run 15 chain. The canonical state represented by the latest run
> records is Run 36: score **22.642386651** (rounded **22.642387**), with
> 543/1000 rows beating grid. The complete operational repository is present
> in this GitHub checkout; the Run 36 record is preserved in
> `RECONCILIATION.md` until the corresponding run-36 execution artifacts are
> restored.

Everything runs from the repository root. Python 3.12 with numpy (sympy
only for the certificate scripts); node (or bun) with the `docx` package
for the report step. All scripts resolve their own paths from the repo
location (fixed in Run 13 — no machine-specific paths remain). Offline
verification chain: ~15 minutes.

## A. Historical Run 15 verification chain (offline, deterministic)

```bash
# 0. verifier self-tests (SAT engine, grid packings, overlap detection)
python3 scripts/packlib.py                  # -> "self-tests passed"

# 1. submission round-trip: 500,500 rows, ids 0..500499, every packing
#    re-verified from the file on disk, independent score recomputation
python3 scripts/final_assembly.py
python3 scripts/score_submission.py workspace/submission/submission.csv
#    -> Historical Run 15 result: SCORE = 22.823536, grid ceiling = 28.937670,
#       overlap failures: none, 454/1000 beat grid (the run-13 frontier)

# 2. Golay code + Leech lattice: 28 assertions, integer-exact (~4 min)
python3 scripts/leech_core.py               # -> "SUMMARY: 28/28 VERIFIED"

# 3. octad calculus: 14 assertions (~1 min)
python3 scripts/octad_moves.py              # -> "SUMMARY: 14/14 VERIFIED"

# 4. grid -> number-field -> laminated-tower mapping
python3 scripts/leech_map.py                # -> coverage 88.9%; spearman +0.79

# 5. figures (English labels)
python3 scripts/figures.py                  # -> "ALL 5 FIGURES OK"
```

Expected historical invariant: these steps leave `table.json`, `submission.csv`
and the Run 15 score unchanged (22.823536). This is not the current Run 36
score; see `RECONCILIATION.md` for the snapshot transition.

## B. Rebuild the run-13 frontier from the run-12 table

The delivered `table.json` already contains every improvement. To replay
this session's pushes in order (e.g. after re-importing a fresher source
snapshot):

```bash
# 1. community register import (packlib-gated, attributed)
python3 scripts/import_atlas.py
#    -> 76 applied, direct gain 0.050264; writes workspace/push/atlas_import.json
#    source snapshot: workspace/sources/atlas/lists/ (best.json + certs/)

# 2. propagation to fixpoint — ORDER MATTERS (any table change triggers both)
python3 scripts/cascade3.py                 # L-extension band chains
python3 scripts/closure_apply.py            # removal closure, iterate to fixpoint
#    -> chains: 33 conversions (gain 0.013671); closure: clean at fixpoint

# 3. architecture test (pure arithmetic + packlib gate)
python3 scripts/gobel4.py
#    -> 503 near-miss targets swept, 0 representations below grid (honest negative)

# 4. analysis instrument
python3 scripts/gap_analysis.py             # -> workspace/push/gap_analysis.json

# 5. rebuild + verify the submission
python3 scripts/final_assembly.py
```

To replay the historical construction runs (9–10) on any table:

```bash
python3 scripts/gobel2.py    # full G(a1,a2,b,c) sweep + apply (ledger: download/)
python3 scripts/gobel3.py    # clipped G(a1,a2,b,c,t) + pocket-fill wave B
python3 scripts/cascade3.py && python3 scripts/closure_apply.py
python3 scripts/final_assembly.py
```

## C. Rebuild the mathematical layers from scratch (offline)

```bash
python3 scripts/leech_core.py     # QR factor search -> Golay -> Leech:
                                  # kissing 196560 = 1104+97152+98304,
                                  # det 1 via |L_raw/8Z^24| = 2^36,
                                  # tower 2/6/12/24/240 (7320 cited),
                                  # projection law (759 octads = the only
                                  # defect locus, d=8)
python3 scripts/octad_moves.py    # Steiner 253/77/21/5/1, octad calculus
                                  # 30/448/280, dist-8 graph (diameter 3),
                                  # covering radius exactly 4
```

Both recompute everything from first principles; run twice and the outputs
are byte-identical.

## D. Historical pipeline (run-by-run, mostly offline)

```bash
python3 scripts/parse_all_svgs.py   # survey SVGs (workspace/svgs) -> records
python3 scripts/parse_kingbird.py   # WEB: Ellsworth catalogue mirror
python3 scripts/level_audit.py      # field-identification standard (2e-8)
python3 scripts/build_table.py      # records -> table.json
python3 scripts/gobel_squares.py    # Göbel 45 deg family sweep + apply
python3 scripts/galois_certs.py     # certificates + theta-30 members
python3 scripts/cascade3.py         # chain3 family
python3 scripts/closure_apply.py    # removal closure to fixpoint
python3 scripts/theta_family.py     # 7-angle feasibility map + 45 deg minimum
python3 scripts/theta225_push.py    # run-5 final sweep + certificates
python3 scripts/final_assembly.py   # table -> submission.csv + round-trip
```

Notes and honest caveats:

- `parse_kingbird.py` fetches the *live* catalogue; the web copy drifts.
  The repo ships the parsed values current at archive time (embedded in
  `workspace/submission/extended_table_5000.json` as `catalogue:kingbird`).
  The catalogue is **not** the frontier any more — see `STATUS.md` §6.
- `theta225_push.py` reads the `leech_map` output for its Level-0 list —
  run `leech_map.py` first.
- The web steps (kingbird fetch) and the Lean build are the only
  non-offline stages; everything else is deterministic.

## E. The report (English edition)

```bash
python3 scripts/figures.py                 # figures
node scripts/gen_report_en.js              # docx (needs `docx` npm package)
python3 scripts/patch_footers.py           # ROMAN/arabic page-field patch
```

`scripts/gen_report.js` is the Run-4 Chinese edition, kept for the record.

## F. Lean layer

```bash
cd workspace/lean/tct_squares && lake build   # needs elan + mathlib cache
python3 scripts/cert_repro.py                 # certificate reproduction
```

See `workspace/lean/tct_squares/SORRY_LEDGER.md` for the exact gap list
(2 of 3 sorries have candidate closures in source; `s11_optimal_value` is
deliberate — the combinatorial-geometry wall).

====



## A9. Run 17: recycle recovery + research resume

```bash
python3 scripts/fetch_atlas.py        # live register fetch (weekly P3 watch)
python3 scripts/import_atlas.py       # 76 applied, gain 0.050264
python3 scripts/cascade3.py && python3 scripts/closure_apply.py
python3 scripts/gobel2.py             # reimplemented run-9 G(a1,a2,b,c): 83 applied
python3 scripts/gobel3.py             # reimplemented run-10 clipped: 13 applied
python3 scripts/cascade3.py && python3 scripts/closure_apply.py
python3 scripts/final_assembly.py     # 22.823536, 454/1000 (lost frontier restored)
python3 scripts/gobel5.py             # seed map: 8489 near-misses, 159 at gap 0
python3 scripts/gobel6.py             # two-band family: 0 records (honest)
python3 scripts/polish.py             # P2 fine polish (pending)
```

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

    
    ## A11. Run 19: discovery engines + the 8 discovery wheels
    
    ```bash
    # restore from the GitHub repo after a recycle (idempotent):
    python3 scripts/restore_from_repo.py
    # the discovery stack:
    python3 scripts/pressure_settle.py     # substrate selftest (FD + pinwheel)
    python3 scripts/oracle_basin.py        # the E1/E2/E3 oracle study
    python3 scripts/lm_exactify.py         # exactification selftest
    python3 scripts/cent_discovery.py      # engine v3 selftest (rediscovery)
    python3 scripts/cent_campaign19.py     # 23-root campaign (bg OK)
    python3 scripts/wheel_expand.py        # W38-W45 into the compiler
    python3 scripts/apply_campaign19.py    # apply finds (no-op if none)
    ```
    

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


## A13. Run 21: boundary demo + wheels census + clue ledger

```bash
python3 scripts/boundary_demo.py     # Q1: cross the grid boundary (~40 min)
python3 scripts/wheel_census.py      # Q2: 41 vs 45 reconciliation
python3 scripts/positive_control.py  # corrected control (phantom fix)
python3 scripts/clue_ledger.py       # Q3: 7-channel clue ledger
```


## A14. Run 22: soft relaxation

```bash
python3 scripts/soft_relax.py   # v2 hybrid; ~10 min; controls + roots
# v1 comparison output is preserved at
# workspace/push/soft_relax_v1_sa.json
```


## A15. Run 23: submission audit + tightest ladder sweep

```bash
python3 scripts/sweep23.py    # ~28 min: Part 0 audit + 36-cell ladder + apply
python3 scripts/audit23.py    # optional: fact-base audit, pass 1
python3 scripts/audit23b.py   # optional: fact-base audit, pass 2
```


## A16. Run 24: NEXT_STEPS execution

```bash
python3 scripts/import_atlas.py      # P3: idempotent community import
python3 scripts/p2_seed_polish.py     # P2: family-seeded polish (~50 min)
python3 scripts/cascade3.py           # P4: fixpoint propagation
python3 scripts/closure_apply.py
python3 scripts/final_assembly.py     # rebuilds submission.csv
```


## A17. Run 25: P1 strip scan + P2 remainder

```bash
python3 scripts/strip_decode.py         # P1: member-state decode (audit)
python3 scripts/strip_sweep.py          # P1: generalized strip sweep (~2 min)
P2_ROWS=134,135,157,158 \
  python3 scripts/p2_seed_polish.py      # P2 remainder (~10 min)
python3 scripts/cascade3.py             # fixpoint propagation
python3 scripts/closure_apply.py
python3 scripts/final_assembly.py       # rebuilds submission.csv
python3 scripts/deliver25.py            # this run's deliverables
```


## A18. Run 26: P1(b)/(c) closures + T-263 import

```bash
python3 scripts/twoblock_sweep.py       # P1(b): two-block sweep (~2 min)
python3 scripts/seam_census.py          # P1(c): census + n=50 decode
python3 scripts/import_atlas.py         # P3: idempotent (may fetch)
python3 scripts/import_s299.py          # P3: T-263 s(299) (needs network)
python3 scripts/cascade3.py             # P4: fixpoint propagation
python3 scripts/closure_apply.py
python3 scripts/final_assembly.py       # rebuilds submission.csv
python3 scripts/deliver26.py            # this run's deliverables
```


## A19. Run 27: P4 root-conversion instrument

```bash
python3 scripts/cascade3.py        # fixpoint channel (0 expected)
python3 scripts/closure_apply.py
python3 scripts/final_assembly.py
python3 scripts/root_audit.py      # the P4 instrument (new)
python3 scripts/import_atlas.py    # weekly watch (idempotent)
python3 scripts/deliver27.py       # this run's deliverables
```


## A20. Run 28: SAT data review

```bash
python3 scripts/sat_review.py        # the SAT-data instrument (new)
python3 scripts/deliver28.py         # this run's deliverables
```


## A21. Run 29: the SAT measure (TAX/NRCI)

```bash
python3 scripts/sat_measure.py       # TAX/NRCI on the SAT data (new)
python3 scripts/deliver29.py         # this run's deliverables
```


## A22. Run 30: P2 renewal (null) + Mishapolk import

```bash
python3 scripts/t263_polish.py       # P2 T-263 family (null: 0/12 cells)
python3 scripts/fetch_mishapolk.py   # fetch + compare (idempotent)
python3 scripts/import_mishapolk.py  # gated import (resumable)
python3 scripts/cascade3.py && python3 scripts/closure_apply.py \
  && python3 scripts/final_assembly.py
python3 scripts/root_audit.py        # refresh the leverage map
python3 scripts/deliver30.py         # this run's deliverables
```


## A23. Run 31: symmetry review + P1' campaign null

```bash
python3 scripts/symmetry_audit.py      # D4 census + SAT measures (122s)
python3 scripts/p1p_insert31.py         # P1' at 356/395/355 (null, 17 cells)
python3 scripts/deliver31.py            # this run's deliverables
```
