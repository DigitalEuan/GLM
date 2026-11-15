# Run Log — Condensed Ledger

Full JSON ledgers: `download/run<N>_outcomes.json`. Score history:
**22.887471** since run 12 (no improvement found since; every
candidate failed against it — see runs 9–11).

| Run | Date | Focus | Key outcomes |
| --- | --- | --- | --- |
| 1–5 | earlier | table assembly | parse survey, seed classification, cascades, Goebel family; Leech map tiers; positive control |
| 6 | earlier | audit | level audit; 879/1000 spurious fits at strict budget → certification moved to certificate route |
| 7 | earlier | structure | shell law (937/937 hold); deletion lemma (999/999 pairs monotone) |
| 8 | earlier | Galois | 1,169 certificates; exact verification v0 |
| 9–11 | earlier | push | improvement candidates all fail; scan-blindness theorem; run-11 audit formalised in Lean |
| 12 | 2026-11-04 | consolidation | 3→1 sorries in Basic.lean; exact v1 554; k²+1 family frontier discovered (gobelS/gobel2 constructions) |
| 13 | 2026-11-04 | Griess/Conway fulfilment | exact v3 **875** (321→0 snap_failed; two verifier bugs fixed); real Golay code built+verified; Layers.lean written (compile blocked on heartbeat) |
| 14 | 2026-11-04 | heartbeat + docs | this run — see below |

## Run 14 in detail

User request: fix the `TCT.Octads.lean` heartbeat issue; make use of
the GLM repository's Lean (`workspace/glm-repo`, DigitalEuan/GLM —
confirmed already cloned); tidy the documentation into Markdown.

### The heartbeat fix (GLM-repo idiom)

Run 13 emitted the 759 octads as a 24 KB literal; `decide` on it hit
the 200,000-heartbeat `isDefEq` limit, and `native_decide` could not
evaluate the literal either.

The GLM repository's own files (`Rule30/ShortcutNetworkData.lean`,
`TriadChance.lean` — which natively verifies a 735,471-element
family; `Escalation/GolayTies.lean` — the full Golay coset census
1/24/276/2024/1771) showed the working idiom: **compute the data, and
verify facts with `unfold <defs>; native_decide`**. Applied:

- `GolayData.lean` — 12 generator rows packed as 24-bit ℕ masks
  (`golayRows`); `golayWord m` by XOR-fold over `testBit`;
  `Hdata`/`golayH` unchanged.
- `Octads.lean` — `octadIdx := (filter over 4096 messages by
  weight-8).map codeIdx`; `octadIdx_length = 759` by `native_decide`;
  membership facts by construction (the filter predicate *is* the
  fact).
- Cross-check: the computed 759-octad set is asserted equal (in
  `emit_lean_layers.py`) to the run-13 Python enumeration — same set,
  different order (systematic vs cyclic basis).

### Layers.lean (rewrite, compile-verified this run)

- `syn24_zero`, `syn24_add` (linearity), `zmod2_self_add` (char 2);
- `synSearch_sound` / `synSearch_mem` — search soundness/completeness
  by list induction;
- `MOG.correct_idempotent` for `golayMOG`: a matched pattern has the
  same syndrome as the word, so the corrected word has zero syndrome
  (char 2), the second search hits the zero word at the head of the
  list, and correction by zero is the identity;
- `substrate_indist_zero_two`, `integer_distinguishes_zero_two`,
  `integer_indist_zero_half`, `rational_distinguishes_zero_half`,
  `scan_blind_to_clearance` (carried from run 11), `zero_correctable`,
  `golay_decode_succeeds_of_mem`.

### Documentation (this run)

`download/docs/`: `00-OVERVIEW.md`, `01-LAYERS.md`,
`02-EXACT-VERIFICATION.md`, `03-REPRODUCE.md`, this file;
`download/README.md` rewritten as an index; `REPRODUCE.md` at the
repo root updated.

### Environment (recurring)

The sandbox was recycled again before this run (5th time; scripts,
elan toolchain, all Mathlib oleans and the Mathlib *package source*
lost). Recovery: `/tmp/my-project` snapshot rsync; elan reinstall;
`git clone --depth 1 --branch v4.8.0` of Mathlib; `lake exe cache
get` (4,331 oleans from the official cache). The re-fetch of the
Mathlib package source is new this run — the `/tmp` snapshot did not
preserve `.lake/packages/mathlib` (its lakefile and toolchain were
gone), so the clone step was added to the recovery chain.


## Run 14 addendum (post-compile)

All three user asks delivered, and the compile surfaced a real finding:

- **Heartbeat**: resolved by the GLM-repo idiom (computed data +
  `set_option maxHeartbeats` + `native_decide`); TCT.Octads and
  TCT.GolayData build green.
- **Layers.lean**: compile-verified, 0 errors, 0 sorry; axiom check
  clean (`propext, Quot.sound, Classical.choice` only).
- **Theorem correction (mathematical finding)**: the run-11 statement
  of `scan_blind_to_clearance` (|v−w| < 25/10¹⁴ ⟹ ScanPerceive v =
  ScanPerceive w) is **false** — counterexample v = 0.49·10⁻¹²,
  w = 0.51·10⁻¹² (difference within budget, yet round(0.49) = 0 and
  round(0.51) = 1; verified by `#eval`). The triangle chain only gives
  < 5/4, which is why the run-11 "proof" never compiled. Corrected
  statement, now proved: **|Δscan| ≤ 1**. The run-11 audit's
  conclusion (value scans cannot certify at clearance scale) stands —
  a ±1 step at 12 decimals is exactly the noise floor.


## Run 15 — mimoclaw continuation (frontier reproduced + instruments)

User request: continue after running the repository in mimoclaw.ai
(attachments: NEXT_STEPS.md, REPRODUCE.md, import_atlas.py,
atlas_import.json, gobel4.py).

1. **Sources staged**: sparse checkout of evand/square-packing `lists/`
   (best.json 324 entries + 650 certs, 6.0M) at
   `workspace/sources/atlas/lists` — disk hit 100% mid-staging; freed
   2.3G by dropping the full clones for the sparse subtree. The live
   register equals the Oct-17 snapshot the mimoclaw ledger used (no
   drift in 2.5 weeks).
2. **import_atlas reproduced exactly**: 76 applied / 244 rejected / 4
   skipped, +0.050264 → 22.837207; **cascade3 + closure_apply
   fixpoint in one round**: 33 chain conversions → **22.823536,
   454/1000 beat grid**; `final_assembly` round-trip clean (500,500
   rows, 0 issues) and `score_submission` recomputes the same score.
3. **gobel4 re-confirmed** on the new frontier: 546 tied targets,
   0 representations below grid — the honest negative stands.
4. **gap_analysis.py** written to the NEXT_STEPS spec and validated
   **11/11 row-for-row** against its published §2 census (proven basis
   + wall_2026: s(k²−3)=k k≥2, s(k²−4)=k k≥5). Measured: gap 0.769115,
   d* = 0.0387, deepest roots 12, 31, 44, 58, 76, 94.
5. **atlas_exact_replay.py** (P5): all 76 imported states verified
   exactly in Fraction arithmetic (rational t-rotations; container +
   pairwise SAT); max |L − side_exact| = 1.889e-09 (finalize gap).
6. `download/exact_snap.json` refreshed on the new table (run-14
   record kept as `exact_snap_run14.json`).


## Run 16 — NEXT_STEPS agenda round (P1-P3)

1. **Design intel** (inspect_states/map/lattice.py): the 2026 frontier
   is ONE corner-anchored tilted band at a FREE angle (n=51: 3x7@45deg,
   n=84: 6x9@28deg, n=258: 49sq@33.8deg) + wall-hugging axis fills —
   exactly the class NEXT_STEPS 3-6 required. Register is AT GRID on
   every open root: they are open for everyone.
2. **P1 gobel5.py** (new family, that architecture): full sweep 13584
   candidates, 0 verify-fails, **0 records, 8489 near-misses** —
   including **159 states at gap exactly 0.0000 on 23 tied rows**
   (roots 12/31/44/58/76 among them; 1x2 band at 36.87deg, the 3-4-5
   angle). The near-miss map is the P2 asset
   (download/gobel5_results.json).
3. **P2 polish.py**: bounded fine-axis campaign (angle/anchor/phase)
   over the top-50 seeds; running at save time.
4. **P3 register watch**: idempotent re-run — 0 new rows; no drift
   since Oct-17.
