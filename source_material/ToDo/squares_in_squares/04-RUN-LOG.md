# Run Log — Condensed Ledger

Full JSON ledgers: `download/run<N>_outcomes.json`. Current score:
**22.218056945** (553/1000 rows beat grid; guarded by `sqscore.guard`, run 52).
The table below is the run history: the 22.887471 figure it opens with is historical,
superseded at run 47 by the audit re-score.

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

## Run 39 — the CRAM translation (2026-11-17)

Source: Hoover, Blayney, Whittington, *Classical Energies Learn to Reason
1,000× Faster than Looped Models*, arXiv:2611.17309v1. Four of its mechanisms
were translated into this domain and measured separately. **Score unchanged
(22.218056945); 0/24 push runs below the record; submission untouched.**
Instrument `scripts/cram_relax.py`, ledger `workspace/push/cram_relax.json`,
record `06-CRAM-RELAX.md`, notes `notes/run39_NOTES.md`.

1. **Relation cost / PL scoring — stands as a ranking rule.** 21,602
   contacts, 18 relation cells fitted at the delivered solutions (costs
   0.6307…10.6741). AUC 1.000 against an angle-destroyed control and 0.794
   against a position-destroyed one; the PL score predicts where relaxation
   lands at Spearman 0.368 / 0.744 / 0.562 (n = 40/70/110), best-scored
   quarter 4–23× lower in final energy than the worst-scored.
2. **Calibrated threshold — does not transfer.** τ = 0 exactly (1000/1000
   rows at E ≤ 1e-12); 0/304 corrupted boards accepted (lowest 7.16e-3); a
   0.1% squeeze already puts 0/400 rows at or below τ (median E 4.33e-4).
   In a hinge energy E = 0 *is* feasibility, so the threshold is the
   feasibility test and grades nothing.
3. **Focused relaxation — not demonstrated.** Best at n = 20 and gentle
   corruption, clearly worse at n = 240 amp 0.08 (+39% over full) *with* 6×
   the per-body moves: the interior of a jammed packing is load-bearing,
   unlike a Sudoku cell.
4. **Two-layer settle — a weak, inconsistent positive.** n = 240 amp 0.01
   1.17e-2 vs 1.84e-2; n = 110 amp 0.04 7.99e-2 vs 9.21e-2; worse at the
   extremes. No run (0/96) reached E ≤ 1e-6 or a single-body fixed point, so
   C and D are compared as descent rates at equal budget, not as solvers.

## Run 52 — G-1: the r = 1 column in the exact t-basis

`scripts/r1_atoms.py` (`workspace/push/r1_atoms.json`), record
`20-R1-ATOMS.md`. Both bands (k = 8..24 and k = 25..31) use the same alphabet
`{axis, pi/4}`, so the 0.520815 step is an ARRANGEMENT: it is carried by a
17x17 diamond that is half-full at k = 24 (145/289) and full from k = 25
(289/289, side 17*sqrt2). By-product: across all 31 rows the field of delta is
the field of the alphabet. Same run: `scripts/record_guard.py` implemented
(`19` §7), and the ten current-facing documents corrected to the run-47 table.

## Run 53 — G-2: the seam declared, solved, certified

`scripts/seam_wheels.py` (`workspace/push/seam_wheels.json`), record
`21-SEAM-WHEELS.md`; `M-diamond` registered as a reconstruction wheel in
`motif_wheels.py` (selftest 13/13; seam_wheels selftest 20/20). Both r = 1 atoms
rebuilt from integers in Q(sqrt 2) — n = 65 as p = 5 with 8+8 wall columns and
delta = 5/sqrt2 - 3, n = 626 as p = 17 with 25+24 columns and
delta = 17/sqrt2 - 23/2 — each gated exactly at penetration 0, with no tilted
square touching a wall in either. An LP over (side, block translation) with one
declared separating axis per seam pair returns the delivered side on all 14
full-diamond rows: mirroring is a no-op, the seam turn costs 1.121320 / 1.307612
(infeasible on four rows), a moved partial row costs 0.500000 / 0.742641. Zero
survivors, no row changed. The base-less window is priced out — the best of
r = 38..60 is r = 38 at 0.022703, one seventh of the 0.1637 gap — while the open
columns pay 0.153 (r = 1) to 0.590 (r = 6) for a base at the column's own slack.
Karakus's bound added as a pre-gate prune (exact at k^2-1); controls: 29/29
k^2-1 rows sit at the grid and 20/20 s(k^2-k) members beat it.

## Run 54 — G-2b: the diamond as a mask

`scripts/diamond_mask.py` (selftest 10/10), ledger `workspace/push/diamond_mask.json`,
record `22-DIAMOND-MASK.md`. The block is now (frame, integer mask, fill) rather
than a `p x p` extent; the frame comes from one site (never the centroid) and the
lattice coordinates from differences of `(x+y)` and `(x-y)`. Three of the four
rows run 53 refused reconstruct exactly — n = 325, 530, 577 as 19x5, 26x5, 29x5
diagonal strips, plus n = 226 as the 5x5 full control — each certified at the
delivered side by an exact bisection that returns a two-sided bracket (lo exactly
infeasible, hi exactly feasible) with no declared-axis branch at all. n = 290 is
not a partial diamond: 25 of its 50 tilted squares sit on a second 45 deg lattice
offset by 0.384808, so one frame cannot hold it.

Count-preserving boundary edits (trim an outer row, add a boundary run, move a
row end) at fixed n on all four rows: no gain anywhere, every feasible edit costs
0.7635 to 0.9142 of side, and the k = 1 and k = 2 runs cost the same because the
binding constraint is the strip's width, not its length. Trimming an outer row is
rejected at the exact gate at every nominated side.

Three corrections, each of which lowers a published number: the pinned-L LP bug
(the coefficient of L was zeroed while the bound fixed it, so rows were evaluated
at L = 0); `exactly_infeasible` renamed `candidate_rejected_exact` with the eight
half-step neighbours tried; and the ranks re-priced per legal start, forward only,
with the residue class checked (`n = k^2+6` at k = 2 is n = 10, a residue-1 row).
With that, `cascade_rank`'s `now` is 0.000000 for every column — delivered slack
falls with k, so no column gains by re-placing its own base — and the best
base-less start is r = 38 at n = 614 for 0.058535, replacing run 53's 0.153449 /
0.589705 / 0.584422 / 0.425392 and 0.022703.

Also corrected: `21` §8 claimed a Bui seam near theta = 0.2 rad could not be
certified exactly because the angle is not in Q(sqrt 2). Wrong — for rational
t = tan(theta/2), cos and sin are rational, so the orientation is exactly
representable. The paper's area argument stands; the field argument does not.

## Run 55 — construction grammars: the n = 10 seed wheel, the two-frame motif

`scripts/seed_wheels.py` (selftest 7/7), ledger `workspace/push/seed_wheels.json`,
record `23-SEED-WHEELS.md`. Two new families, each a wheel with a declared
grammar, count law, exact builder, gate, canonical scorer and a ledger of
survivors AND refusals.

PART A, the two-tilt seed at n = 10 (the top of the optimistic r = 1 column):
400 wall-anchored cells (2 tilt classes x 10x10 sqrt2/2 frames x 2 declared
8-square fills) certify 44, all at or above the grid, best exactly 4.000000; the
wall grammar buys nothing. 36 centred cells using the delivered 8-anchor fill
reach 3.707106791, which is the delivered side plus the pad — the wheel contains
the delivered row as a cell and nothing beats it. 436 cells, 80 certified, 0
gains; the Karakus floor is 3.192582, so 0.51 of admissible side is untouched and
the binding component is the FILL, not the tilt pair. No seed has slack below
0.707107, so there is nothing to cascade — the payoff is zero by absence, not by
ranking.

PART B, the two-frame motif: n = 290 now reconstructs exactly as a union of two
(frame, mask) pairs — 5x5 + 5x5 sites, 240 upright, non-lattice offset
0.2721*sqrt2 = 0.384808, exact gate at penetration 0, rebuild error 1.7e-9 — with
n = 226 as a one-frame control through the same path.

Two instrument repairs: orientation matching is now a greedy distance-sorted
bijection (sorted position sequences swapped on the dense 10-square row), and the
lattice split folds a residual of -1e-9 back to frac 0.0 (it was reading one
lattice as 24+1 on n = 226 and as three on n = 290).

## Run 56 — n = 10 is a proved optimum; the table is exact on every proved row

`scripts/optima.py`, ledger `workspace/push/optima.json`, record
`24-N10-OPTIMAL.md`. Retracts run 55's "0.51 of theoretically admissible side":
s(10) = 3 + 1/sqrt2 is PROVED optimal (Stromquist, EJC 10 (2003) #R8, Thm 1), so
the Karakus floor 3.192582 sits 0.514524 below the optimum and that gap is bound
looseness, not packing space. Checked exactly on the delivered row: snap(L-3) =
1/2*sqrt2, the exact gate passes at 3 + 1/2*sqrt2 with penetration 0, and none of
the 80 certified seed cells goes below it — the wheel recovered the proved
optimum, which makes run 55 a forced negative and n = 10 an optimality control.

Extended to a battery over every exactly-known s(n): 42 proved rows (squares
1..31^2 plus 1, 2, 3, 5, 6-9, 10, 14, 15, 24, 35) check at = 42, above = 0,
below = 0. So no score is available on any proved row, and the only proved rows
that beat the grid are n = 5 and n = 10, both exactly optimal. The whole
remaining 0.1637 of gap must live in rows whose optimum is unknown.

Consequence for the target: not a larger n = 10 fill search. Proved rows are out;
among unproved rows the forward-only ranking of run 54 already says no column
gains by re-placing its own base, so value needs a better base on an unproved row
in an open column. Catalogue values for those rows are floats and can nominate,
never certify.

## Run 57 — open-row literature crosswalk and the n = 11 check

`scripts/crosswalk.py`, ledger `workspace/push/crosswalk.json`, record
`25-OPEN-ROW-CROSSWALK.md`. Twelve open rows checked against Friedman DS7 Table 1
(best known construction, with author and figure) and Table 2 (best known lower
bound), plus Stromquist Thm 2 for s(11). Status: 10 at_published, 2
beats_published (n = 28 below Gobel's 3+2sqrt2 by 3.98e-3, n = 29 below
Gensane/Ryckelynck by 5.7e-4), 0 above_published. Six of the ten "at" rows match
a published closed form to 1e-9, i.e. the table IS those constructions to the pad
(Hamalainen n=18, Wainwright n=19, Friedman n=26, Gobel n=27, and the grid rows).
No import target, and the forward-only value of a base exactly at any published
side is 0.000000, so importing cannot pay regardless of construction quality.

n = 11 focused check: delivered 3.877083592 vs Trump 3.8771 (delta -8.5e-9), and
the row's single non-axis angle is 49.8181 deg, which is 40.1819 deg mod 90 —
Trump's "about 40.182 deg" to four decimals. It also sits below Stromquist's
0/45-restricted optimum 2+2sqrt(8/9) = 3.885618, which is the property his paper
isolates. So the delivered n = 11 row IS Trump's construction: the positive
control passes, and n = 11 is a benchmark rather than a target, with 0.088229 of
bound gap that run 56 warns is not room.

Rerank consequence: proved rows out (run 56), imports out (this run), and bound
slack cannot rank what is left. Any remaining gain needs a construction strictly
below the published record on an open row — extend a family to an uncovered row,
or invent a multi-angle motif — and must be ranked by constructibility, not by a
bound.

## Run 58 — full-range frontier crosswalk

`scripts/frontier.py`, ledger `workspace/push/frontier.json`, record
`26-FRONTIER-CROSSWALK.md`. All 1000 rows classified against the Kingbird
catalogue (Ellsworth's revision), whose own completeness statement makes a
full-range crosswalk possible for n <= 324: "for the n <= 324 not pictured, the
trivial packing is the best known". Basis split: 146 catalogue_2026, 135
trivial_rule, 6 ds7_2009, 38 pictured-but-not-extracted, 675 unresolved above 324.

Resolved 287 rows: at = 231, beats = 56, ABOVE = 0. So there are NO import
targets on any row where the record is complete, extending run 57's 12-row result
to 287. Current records matched exactly (to the pad): n = 50 (7+4/7, Schadt 2025),
55, 71, 83 (the 672-degree record), 87, 205, 626.

56 resolved rows have the delivered side below the extracted catalogue value
(margins up to -3.2e-2). That is NOT claimed as 56 records: the label-value
mapping came from a page the fetch truncated inside several entries, and margins
of 1e-2 are the signature of a shifted comparison rather than of record-breaking
constructions. Flagged for the triangular-table pass.

713 rows stay unresolved: 675 because the catalogue's completeness statement stops
at n = 324 (it pictures only n = 626 in 324 < n <= 1000), and 38 because the
pictured value was truncated. The fix is the triangular table view plus
parse_svg_packing.py, not new mathematics.

Consequence: importing is closed as a score route over every resolved row; a new
score needs a construction below the published record, which no bound can rank, so
the next ranking signal is constructibility.

## Run 59 — triangular-table correction

Fetched the Kingbird "Triangular Table View", which states its rule and attaches
every value to its own n: "for the n not shown, the closest packing shown to the
right of it is the best known packing (with the appropriate number of squares
removed)". Run 58's "n <= 324 unpictured -> trivial ceil(sqrt n)" was WRONG: it
understates best_known on ~100 rows and so could only have hidden a target, never
invented one. scripts/frontier.py updated to the correct rule (TT anchors,
triangular_anchor@k basis, anchor_truncated), schema frontier/2.

Result over 1000 rows: at 236, beats 80, ABOVE 0, unresolved 684 (675 above 324,
9 left of a truncated anchor). 316 rows resolved. Zero import targets confirmed
against the weakest admissible standard.

The run-58 worry that the 56 beats were an offset artifact is REFUTED: with values
attached to their own n, 80 rows still sit below best_known, and 61 of them are
same-n comparisons (n = 51: 7.690355939 vs 7.700799235; n = 126: 11.742640689 vs
11.774735132; n = 303: 17.901811279 vs 17.931255096). The other 19 are inherited
anchors and say nothing about records.

Validity checked: every row holds exactly n squares (0 exceptions) and
packlib.verify passes 51 sampled rows with worst_pen -1.3e-10..-2.6e-10, w == h == L.
An ad-hoc float verifier written during this run reported +2.9e-1 penetrations on
rows that match the catalogue to 2e-9; it misused seam_wheels.EXT/AXES_OF and is
retracted — its numbers are void.

Still open: 675 rows above n = 324 and 9 anchor-truncated rows; the triangular page
continues past 324 but the fetch truncated there twice. No construction built, no
row changed.

## Run 60 — complete frontier crosswalk (1000/1000)

Fetched the triangular table with curl (the page reader truncates near n=324);
scripts/parse_tt.py parses it locally -> workspace/push/tt.json, 215 shown rows,
0 ambiguous cells, 0 unparseable values. Structural finding: the page's scope ENDS
at n=324 (complete file, 215 cells, zero square-<n>.svg links above 324), which is
exactly the band the catalogue's completeness statement covers. Above 324 the
catalogue lists pictured records only; our gallery parse finds one in 325..1000
(n=626), matching an independent count of five records above 324.

Rule applied: best_known(n) = min(trivial(n), nearest shown row n' >= n) -- the
strictest admissible reading, which can only add targets.

Result: 1000/1000 resolved. at 519, beats 481, ABOVE 0.
Basis: {'catalogue_2026': 146, 'triangular_table': 74, 'trivial_rule': 105, 'trivial_above_324': 675}.
The nine rows whose own value had been truncated (146, 154, 171, 180, 228, 235,
291, 292, 293) are all recovered exactly and are all at or below the catalogue.
Beats split: 79 at n<=324, 402 above; margins 423 >1e-2,
48 1e-3..1e-2, 10 <1e-3, largest n=677 (-0.479185).
The sub-1e-3 block is grid-relaxation, not records; no record claim is made.
Entries 26 §9, ledger frontier.json schema frontier/2, script parse_tt.py (new).

## Run 61 — correction: above 324 is not resolvable, and trivial is not a stand-in

Run 60 parsed the triangular table with curl (215 cells) but assigned the trivial
grid to the 675 unpictured rows above n=324, reporting 1000/1000 resolved. WRONG.
The catalogue's own s(k^2+1) family sits at k + 0.5355339 for k = 12,13,14,15,17
(145, 170, 197, 226, 290); nothing ends the family at k=17, and at 325 = 18^2+1 it
gives 18.5355 against the trivial 19. So trivial is provably not the catalogue's
best known above 324 — the source simply makes no completeness claim there and
pictures one record in 325..1000 (n=626). The tell was n=677 = 26^2+1, 0.479 below
trivial: an ordinary family member, not a record.

Corrected state: 325 rows resolved (n<=324), at 246, beats 79, ABOVE
0; 675 rows above 324 marked no_source_above_324 with best_known null.
Beats split 79 same-n / 0 inherited; largest same-n margin
-0.032094. The nine truncated rows are exact.

frontier.py no longer returns a value above 324. Record 26 §9 rewritten; the
"1000/1000" text is gone rather than superseded in place, since it was never true.

## Run 62 — Bui's staircase: the nomination implemented exactly and refused

Source identified (arXiv:2508.04603v2, Hong Duc Bui). §3.1.1 implemented exactly
over Q with the rational parameter t = tan(theta/2), sealed in its bounding square
with a greedy cell fill; the §3.1.2 "ABCD closure" is figure-dependent and is
explicitly NOT claimed. 132 cells, 132/132 verified by packlib.verify, 0 gains;
best cell -0.078 (n=294: L=19 against delivered 17.6568). Density 0.227-0.823
against the table's ~0.95. Recorded bug: the squares must be rotated by -theta,
not +theta, or every cell overlaps. Reopening it needs §4 (trapezoid) + §5
(square reduction), not another spin. Entries 27-BUI-STAIRCASE.md, script
bui_wheel.py (selftest 8/8), ledger bui_wheel.json schema bui/1.

## Run 63 — G-3: the expressiveness ladder, delivered with its quotes marked

Six rungs, in one record: (1) float/scan tolerance, (2) exact algebraic closure in
Q(sqrt2), (3) the Lambda_24 resolution sweep, (4) elementary-move rigidity,
(5) rotation is elementary, (6) the catalogue's own n<=324 boundary. Four rungs
recomputed here and checked; two are quoted and named as quoted (float/scan,
rigidity), never counted as checks. Rung 3 is the finding: the Lambda_24 predicate
tested at eight scales declares tilted rows illegal 87/87 at every scale and
untilted rows legal 168/168 somewhere - coarsening never creates the structure.
Entries 28-EXPRESSIVENESS-LADDER.md, script ladder.py, ledger ladder.json
schema ladder/1.

## Run 64 — the SAT/disjunctive model: assessed, and the honest boundary named

Answer to "would SAT help": as the non-overlap *test* it is already the gate
(packlib); as an *optimisation with the disjunction fixed* it has been decisive
(lp_seam pins every delivered full-diamond row); as a *global* disjunctive solve it
is not attempted, and the reason is measured rather than asserted: disj_census says
3811/499500 pairs are tight at n=1000 (0.76%), each with effectively 2 branches,
giving 1e300729 leaves. Entries 19 §11, script disj_census.py, ledger
disj_census.json schema disj/1.

## Run 65 — the §11.5 bounded probe: 18 cells, 0 feasible (LP later withdrawn)

Feasibility at fixed side L0-eps, theta frozen, delivered axis assignment frozen,
six slack-heaviest rows x k in {8,12,20}. All 18 refused for `rigid core spans`.
The free set was chosen by wall contact, so the refusal was built in; and the LP
itself carried three defects. Superseded by run 67; the refusals are still true
because that filter runs outside the LP. Entries 29-SAT-PROBE-AND-RESOLUTION.md
Part A (with its erratum), ledger sat_probe.json schema satprobe/1.

## Run 66 — resolution reduction: can a coarse lattice hold the answer?

Ten delivered rows snapped to a 1/m lattice (centres, and separately angles) at
m in {2,4,8,16,32,64,128}. The answer is structural: the snapped packing is
INVALID at every m, including m=128, because at an optimum every load-bearing
contact has penetration exactly 0 and any displacement opens a violation
elsewhere. Six or seven of the ten rows fail packlib.verify with pen>0 at every
resolution. The side cost is small once m>=32 (-0.0058 at m=64, -0.0050 at
m=128) and irrelevant: the gate is binary. At m<=4 the loss exceeds the whole gap
(-0.2088 at m=4; -0.1643 for m=2 with theta snapped). Dithering needs an
admissible residual (a display averages quantisation error); a packing has none.
Entry 29 Part B, script resolution_probe.py, ledger resolution_probe.json
schema resolution/1.

## Run 67 — the earned free set: no k changes the answer, and k = n certifies

Answer to "make the refusal earned": seed the free set with the squares that
achieve the four extremes, grow by tight-pair rings, price every ring where the
frozen core stops spanning. The core stops spanning only at k = 161 / 184 / 267 /
298 of n = 294 / 295 / 299 / 298 (55-100% of the squares), and the LP refuses at
every one of those k and every larger ring up to k = n: 0 feasible, 0 gains.
At k = n the refusal is a certificate - feasible at L0 and infeasible at
L0 - 1e-6 with all translations free means the delivered side is the exact
optimum of the declared-axis, fixed-orientation LP.

Three LP defects were found and fixed on the way, each caught by the same
invariant: the delivered state must be feasible at its own side. (i) global
translation written into pair rows; (ii) i/j coefficient order and inequality
direction (appended as <= when the condition is >=); (iii) required separation
used h_i+h_j instead of 0.5 + Eu[owner, other]. The invariant is now permanent:
sat_probe.py --selftest, 6/6. Entries 30-EARNED-FREE-SET.md, script
extreme_probe.py, ledger extreme_probe.json schema extremeprobe/1.

## Run 68 — the algebraic-word framing, audited

A framing was proposed for the front page: packings as sentences over an exact
relation alphabet, score moving with the alphabet and not with search length, the
pile-of-angle-words route already closed, discrete non-block multi-angle rotation
the one live object. Every figure in it was checked against the delivered table
before it directs a run.

Confirmed by our instruments: run 5's 280 certificates over 7 angles (n <= 1050,
then 1001..5000) converted 0 rows; run 52's 0.520815 step uses the same
{axis, pi/4} alphabet in both bands (17x17 diamond, 145/289 -> 289/289); run 55's
436 cells at n = 10 certify 80 and gain 0, Karakus floor 3.192582.

Corrected: the 45-degree rung carries 43.2% of the total gain and 23.2% of the 553
beats, not 70%; the "0.67k + 4" density wall exists in no ledger; and the three
"thinnest wall margin" rows (n = 656, 184, 819) are at the grid in the delivered
table -- L = k to 2e-9, gain 0.000000, r = 20/12/22 -- while 447 rows share that
position and none of the quoted margins (0.00029 / 0.00040 / 0.00130) is
reproducible from any sqscore quantity, so the nomination is recorded and not
acted on.

One external claim is current and load-bearing: Khalili and Gharabaghi report
s(k^2-5) = k for every k >= 7 (Squares Project T-298, 2026-11-13, at V0/C1) --
real and reported, but not verified in our record. Contact check: the 25 rows
k = 7..31 all sit at the grid, 0 beats, so our table contradicts nothing.
Entry 31-GLM-ALGEBRAIC-WORDS.md.

## Run 69 — the wall margin, and one row's branch-rotation search

The phrase "wall margin" from the run-68 framing was replaced by a definition and
then computed, rather than argued. The area wall sqrt(n) is the only wall that is
a theorem; the grid k = ceil(sqrt(n)) is a convention 553 rows already beat. So
mu(n) = L(n) - sqrt(n) (side above the area wall), rho(n) = mu/sqrt(n) = score,
held(n) = k - L, value(n) = 1/sqrt(n). Exact for the table as delivered: the 50-
digit Decimal re-derivation of L agrees to 6.2e-16 at n = 18 and exactly at
184/656/819.

All 1000 rows: 999 have mu > 0 (n = 1 is exactly 0), range 0 .. 0.585786, median
mu 0.441761, median rho 0.017494, 251 rows above mu = 0.5, 7 above 0.55. The 15
thinnest positive margins are exactly the 15 smallest perfect squares (1.0e-9 ..
1.9e-9, the finalize pad) -- the zero-room band is proved, not merely thin. The
four largest rho in the table are n = 2, 6, 10, 11, all named proved optimal.

Verdict on the three rows named in the framing: NOT special. n = 184 / 656 / 819
sit at the grid (held = -1.9e-9 = 0 to table precision), rank 517 / 604 / 610 of
1000 by mu and 159 / 637 / 702 by rho, against median 0.441761 / 0.017494. All
three are below mu = 0.5; n = 18 alone carries 3.2x the normalised margin of 184.
The "thinnest margin" reading was inverted.

Target rule, fixed before searching: not proved by the record, n <= 20, largest
rho. It selects n = 18 (L0 = 4.822875657118104, rho = 0.136763, rank 8/1000;
mu = 0.580235, rank 2). Excluding n = 11 was a correction: the naive rule picks
it, but README/04 quote s(11) proved while 01-LAYERS and workspace/docs call it
open -- an inconsistency recorded in 32 section 5, not resolved here.

Search at n = 18: words are exact rational t = tan(theta/2) (0, sqrt2-1, 1/2,
1/3, 1/4); 3,940 declared cells (branch assignment by delivered angle class, 90
single re-wordings, 3,825 pair re-wordings), 1,620 re-slot cells (a tilted square
moved to another slot with a new word), all priced by the run-67 corrected
declared-axis LP at L0 - eps, eps = 1e-2 .. 1e-6, then 1,171 cells settled by
cram_relax at L0 - 1e-3 and reported by packlib.finalize + verify.

Outcome: 0 LP-feasible, 0 gate-accepted, 0 gains, in every pass. Controls: the
identity is feasible at L0 and rigid only to 3.0898e-8; a loose 2x2 grid at side
2.2 shrinks to 2.05 and gates (pen -0.05); proved row n = 12 at 3.99 is refused.
Refusal, not impossibility: the declared axes are conservative and a different
contact graph is outside the cell space. No row of the table changed.
Entry 32-WALL-MARGIN-AND-BRANCH-ROT.md.

## Run 70 — the cent-compiler contract, audited; the T1 branch flip, implemented

Two cards (cent-operation/1 jamming_branch_escape; cent-mechanism/1
t1-dislocation-glide) asked for a discrete change to the contact topology: flip
which SAT axis, and which owner, separates a tight pair, couple it to an
algebraic angle step, then contract with the LP. That is a degree of freedom run
69 did not touch -- there the axis per pair was re-derived from the trial
geometry -- so it was implemented rather than argued.

Figures checked first. "0.76% tight pairs" is true only at n = 1000 (3811/499500,
disj_census.json); at the rows the mechanism targets it is 16.99% (18), 28.95%
(20), 20.46% (30), 9.18% (39), so the M-card's "<=1% of pairs" invariant is false
for every mid-size row. "n = 5 rotational lock L = 2.7081" is wrong twice: s(5) =
2 + sqrt2/2 = 2.707107 and it is PROVED, so the test escape_n5_rotational_trap can
only refuse. "0/8 gated" is run 41's pressure-push result over four weightings,
not a run-64/65 measurement. "run 50: 0/300 vs 25/150" is unverifiable: there is
no Run 50 entry in this log, no notes/run50_NOTES.md, and neither ratio appears in
the tree. "exact_authority Fraction, floats_allowed false" is not achievable in
this pipeline: the contraction is a float HiGHS LP and the certificate is
packlib.verify at 12 dp with ~2e-9 clearance. And packlib.verify takes a state,
not (poses, L).

Implementation (scripts/t1_glide.py): branch a in {u_i, v_i, u_j, v_j}, delivered
= argmin penetration; cells = base (control) + one flipped contact edge at an
extreme achiever (3 alternatives) + that flip with one endpoint re-worded from
{0, sqrt2-1, 1/2, 1/3, 1/4} + two flipped edges (capped); side ladder L0 - eps,
eps = 1e-2 .. 1e-6, 5e-10 pad, all translations free; the gate is the only judge.

Results: n = 18 (1,071 cells), n = 20 (4,572), n = 30 (2,160) -- 7,803 cells, 0
LP-feasible, 0 gate-accepted, 0 gains; the base cell is refused at 1e-2 on all
three (the run-69 rigidity, 3.1e-8). Controls: a loose 2x2 grid shrinks 2.2 ->
2.19 and gates; a forced u_i branch on two stacked unit squares is feasible and
gated at side 2.001 and refused at 1.5, so the branch machinery is not vacuous.

The contract is implementable and bounded but earns nothing: no unblock, its
positive test row is proved optimal, and mid-size rows may be among the 152 proved
grid floors. No row of the table changed. Entry 33-CENT-CONTRACT-T1-GLIDE.md.

## Run 71 — the queued action (flip + free-set expansion), and the seed it needs

`33` §7 queued one cell of the T1 card that run 70 never entered: a branch flip
combined with free-set expansion, on a seed whose LP is not already rigid at L0.
It was implemented (scripts/flipgrow.py) rather than argued.

Slack was measured, not assumed. The wall margin `mu` is not slack, so three
quantities were taken: the base depth (largest `eps` with the delivered branches
feasible at `L0 - eps`), the flip depth (the same after one declared flip) and
the pad slack (interior room at `L0`). All 42 open rows at n = 4-60 were searched
in wall-margin order -- the rows with the most nominal room first -- over every
contact edge at an extreme achiever and its three alternative branches.

Result: 2,228 edges, 6,684 flips, base depth 0 at every row, 0 seeds at
`L0 - 1e-6`, so the free-set ladder was never entered: 0 cells, 0 gated, 0 gains.
Two monotonicities make the refusal exhaustive rather than a sample: feasibility
is monotone in the free set (so "all free" is the strongest test, and expansion
can only find a smaller repair, never more room) and monotone in `eps` (a refusal
at 1e-6 refuses every larger shrink). The window below 1e-6 was probed: 1e-7
gives 0 seeds on the top five rows; 1e-8 gives 20 seeds out of 78 flips on
n = 18/11, the ladder enters 400 cells and the gate refuses every one -- the LP's
own tolerance scale, and the clearest case yet for the gate as the only judge.

The count explains the measurement: at every row 4-120 the number of binding
constraints (contacts on their argmin axis plus active walls) exceeds `2n`, the
least over-determined row being n = 5 at +2, with n = 18 at +4. A flip relaxes
one pair and adds none, so it cannot open room in a frame that is over-determined
before the flip. Controls fire both ways: a loose 2x2 grid at 2.2 reports base
depth 1e-2 and one flipped branch seeds and gates; two unit squares at their
exact optimum (2.0) refuse the base and every flip.

What this closes: single-flip cells with free-set expansion at any open row
n <= 60. What it leaves: two-flip cells, a new contact (outside the cell space),
rows above 60, and the 675 rows above n = 324 that have no source. No row of the
table changed. Entry 34-FLIP-AND-FREE-SET.md.

## Run 72 — cubes in a cube: the extrusion question, answered by the LP and the gate

`declp`'s 3D analogue was built rather than argued (scripts/declp3.py): n
axis-parallel unit cubes in a cube, one declared separating axis per pair,
translations and the side L as variables, L minimised. The gate is exact and
stronger than the 2D one -- coordinates are rounded to 12 dp and read as
`Fraction`s, so penetration and side are rational arithmetic on the recorded
numbers and the verdict carries no tolerance constant.

The question: is the 3D optimum the extrusion of the delivered 2D row, or
strictly better? Two cubes in a box of side L < 2 must intersect in every axis,
so L(n) >= 2 for n >= 2, and the 2x2x2 grid gives 2 for n <= 8 -- the 3D optimum
for 2 <= n <= 8 is exactly 2. Against that: the 2D row needs 2.7071 at n = 5 and
3 at n = 6, 7, 8. So the extrusion is optimal at n = 2, 3, 4 only, and strictly
beaten from n = 5, by 2.7071 -> 2 and 3 -> 2. At n = 10, 12, 16, 20 the cube grid
(3) also beats the row (3.7071, 4, 4, 5). At n = 9 the two tie at 3 and L(9)
stays open in (2, 3].

The decisive detail is `desc(extr) = L2` on every row: the extrusion is rigid
under its own declared axes, so the improvement at n = 5-8 is a different
structure, not a polished copy. Exhaustive enumeration of all 6^C(n,2) declared
structures gives the best LP side 2.000000 for n = 2 (6 branches), 3 (216) and
4 (46,656), agreeing with the lemma; above n = 4 the enumeration is 6.0e7 at
n = 5, so no LP lower bound is claimed there and the larger rows are
constructions, not optima.

The degradation control (z pinned, x/y declared, must reproduce `declp`) caught
three defects before any result existed: the two containment constants, the
missing centring of states, and a saturated 2D reference window. Run 67's lesson
in a new place -- a copied constraint system drifts by a constant and still
looks like a certificate.

No row of the table changed; the 2D score is untouched. Entry
35-CUBES-IN-A-CUBE.md.

## Run 73 — n = 9, and then every n: the cube grid is optimal, the score is rotation

Run 72 left n = 9 open in (2, 3]. The route chosen was a big-M disjunctive MILP
over all 6^C(n,2) declared structures at once (declp3.py --milp). It closes n = 4
and n = 5 in ~9 s each, both grid-optimal to 1e-3, and at n = 9 (216 binaries,
36 tight equalities) it did not close: 60 s budget expired, and the 300 s command
cap killed the run. A solver's silence is not a theorem.

The theorem is nine lines. Cubes occupy [c-1/2, c+1/2] inside [0,L], so all
centres lie in a box of side L-1; two cubes are disjoint iff their centres differ
by >= 1 in some coordinate; and if L-1 < m for an integer m, splitting the centre
box into m^d sub-boxes of side (L-1)/m < 1 gives at most one centre per sub-box.
With m = floor(L-1)+1: n > k^d implies L >= k+1, which the k-grid attains. Hence
L_d(n) = ceil(n^(1/d)) for every n in every dimension -- L(9) = 3 exactly, and
there is no 3D ladder at all.

The same argument in 2D says axis-parallel squares can never beat ceil(sqrt n).
Checked against the delivered table, exactly: 447 rows are axis-aligned and all
447 sit at the grid (0 exceptions); 553 rows beat it and none is axis-aligned;
447 + 553 = 1000, so on this table containing a rotated square is *equivalent* to
beating the grid. The angles agree (pi/2 dominates with 66,445 squares, then
pi/4 with 11,731). Runs 65-71 spent four runs closing branch-flip cells; this is
why they had to fail -- on an aligned row no rearrangement of positions can ever
gain, by proof. The lever is the angle word, which is what 31 and 28 already say.

Housekeeping: the 46,656-branch n = 4 enumeration is now behind --exhaustive
(default run is seconds), and --selftest is an alias for --control. No row of the
table changed. Entry 36-CUBE-GRID-IS-OPTIMAL.md.

## Run 74 — the branch space at frozen angles: an exact leaf, an empty bound

Run 73 nominated a 2D branch-space MILP at frozen angles, "which would certify a
row optimal for its angle multiset instead of failing to improve it". It is
built (`bb2d.py`) and the nomination is closed negatively, with a measured
cause.

The model is exact, and that is the point: for two convex unit squares the
separating-axis theorem says non-overlap iff one of {u_i, v_i, u_j, v_j}
separates them, so "one (axis, sign) per pair plus a translation" is an
equivalence, not a relaxation -- unlike `declp`, whose verdict is only about the
declaration it was given. The B&B is ours: node LP with continuous branch
weights w (sum_a w_a = 1), tight big-M computed from the containment box, branch
on the least-integral pair, exact gate at every leaf.

The bound is empty. With w continuous a pair can put 1/8 on each of its four
axes and both signs, and the two signs cancel, so Delta c = 0 is feasible while
every branch is "paid for" by its own big-M. Measured: the root relaxation is
max_i 2h_i -- the largest square's own extent -- on every row (1.0 at n = 6, 9,
13; 1.414214 at n = 5, 10; 1.409216 at n = 11; 1.322876 at n = 18) against sides
of 2.7-4.8. The cheap alternative, dropping the undecided pairs, gives sqrt(2)
at every node. So B&B is enumeration: n = 2 and n = 3 close (7 and 111 nodes,
agreeing with all 4 and 64 structures enumerated exhaustively); n = 5, 6, 9, 10
do not close at 6,000 nodes, and the families are 8^4*4^6 = 16.8M and 8^9*4^36
~ 6.3e29. No row of the table is certified by it.

The leaf does work. `structure_lp` solves one complete structure with 2n+1
columns in ~1.5 ms, reproduces `declp`'s own optimum on the delivered structure
(differences +6.9e-8, +4.7e-8, +2.7e-8 at n = 5, 10, 18) and agrees with the
full leaf LP on the delivered structure and on a flip. `--flips k` therefore
closes a finite family exactly: every structure within k declared-branch changes
of the delivered one, each solved to its own minimum side. At k = 2 that is
87,767 structures over n = 5, 10, 11, 13, of which 9,179 have a different
optimum and 74,028 are not feasible inside L0+0.5; 0 improve, 0 are gated. The
nearest competitor is +2.36e-1 at n = 5, +4.04e-2 at n = 10, +4.48e-3 at n = 11
(the tightest neighbourhood in the table), +1.04e-2 at n = 18; n = 13 is
completely rigid (0 of 234 single and 0 of 27,261 double flips move). Of the
1,543 single flips only 322 change anything, so counting "tested" structures
without the moved denominator overstates this kind of search fivefold.

Two defects were caught by the degradation control and by nothing else: the w
columns were first placed at offs[p]+a instead of 2n+1+offs[p]+a, so the branch
weights overlapped the translation columns, and the translation box was derived
for [0, L] while the model's container is [-L/2, L/2]. Both made every leaf
infeasible.

Also this run: the dimension theorem is scoped to the axis-parallel class
everywhere it is stated (in 2D the n = 5 row beats ceil(sqrt n) by rotation,
2.707107 < 3, so the restriction is not pedantic); run 72's n = 5 and n = 10
"3D strictly better" verdicts are corrected -- a rotated row is not a cube
packing, `extrude_ok` is False there, and `desc(extr) = L2` was the descent
refusing an illegal start, not rigidity; and `declp3.py --milp` is retired (126
lines) because the counting argument subsumes it, it never closed n = 9, and its
relaxation is the same construction measured empty here.

No row of the table changed. Entry 37-ANGLE-FROZEN-BRANCH-SPACE.md.

## Run 75 — the n = 11 near-miss spent, and W1 started

Run 74 left a list. This run spends its cheapest item and starts its first, and
finds one instrument defect on the way.

**W4, the n = 11 near-miss, is one flip and a dead end.** The competitor that
`--flips 2` priced at 3.8815589 is reached by a *single* declared-branch change —
pair (7, 8), branch 3 (`i.v`, sign −1) to branch 0 (`i.u`, sign +1) — and the
k = 1 sweep had already reported the same number, so no pair of flips cooperates.
Certified through `finalize` and the gate the structure needs 3.881558957, i.e.
+4.475366e−3 over the record; its side, like the record's, is set by containment
rather than by a contact, so the flip is paid in spread. Nothing in the two-change
family gates below `L0 − 4e-8`, and the LP optimum cannot be beaten by a gate at
the same structure, so the margin cannot be spent. The row can only move by
changing its angle multiset. Recorded in `37` §9.

**The gate call was dead.** `--flips` and the B&B gated raw LP states; those carry
the LP's own 1e-9 shortfall in every pair, so the 12-dp gate reads it as
penetration and refuses at every side — the delivered row's own LP state included
(`pen 1.46e-9`). A genuine improvement would have been recorded as `False` and
dropped silently. Certification now goes `packlib.finalize` → `declp.gate`, with
`GAIN_MIN = 4e-8`, and control 5 pins the refusal and the certificate on both the
delivered structure and the near miss. All three ledgers regenerate identically
apart from their timing fields.

**W1 started: the seam offset is a parameter, and it is determined.**
`seam_offset.py` reads the n = 290 row — the table's only two-lattice atom, 2 × 25
tilted plus 240 upright — groups its tilted centres into frames by the 45°
residue, and then slides one frame along the seam by a declared set of 17 surd
shifts, bracketing the side and certifying in `Q(√2)`. The measured offset is
`Δ(x−y) = 18 − (25/2)√2 = 0.322330`, `Δ(x+y) = 0` exactly — not the `0.384808`
of `22` §3, which is twice one frame's `(x−y)` grid residue (correction in `38`
§2). Every shift costs exactly its own size (+1.767767e−1 at `√2/8`, +3.535534e−1
at `2√2/8`) and past `2√2/8` the atom does not pack inside `L0 + 4` at all: the
seam is tight, 0 certified gains. Controls: n = 226 groups to one frame and
reproduces its side; n = 290 at `s = 0` rebuilds the row with error 0.0; a
0.25-moved copy is refused. No row changed. Entries `37` §9 and
`38-SEAM-OFFSET.md`.

## Run 76 — what next, ranked: the row census and the frozen-angle certificate

Two runs of negatives left no ordered target list, so this run writes one (eight
entries, `39` §1) and starts the two cheapest. It also records where my own
proposal was wrong.

**The 675-row block is not one block.** `row_census.py` puts every row against the
strongest published floor (`max(area, Karakus)`) with no search. Of the 447 grid
rows, **60 cannot beat the grid at all** by arithmetic alone — `n = k²` by area,
`n = k²−1` by Karakus, which is exact there — and **26 of those 60 are above
n = 324**, where the record currently says nothing can be proved. The remaining
387 open grid rows split cleanly: above 324 every row with residue `m ≤ 20`
beats, and all **247** failures have `m ≥ 21`. So the block is 26 proved rows,
305+ rows that already beat, and 247 unattempted rows in one residue band — a
construction target, not a source problem. Control: no delivered row violates its
floor, all 553 beats included.

**Head does not rank candidates.** I proposed choosing rows by remaining head; it
sums to 6.295 over the open grid rows, forty times the 0.163635 gap, and all 553
beats have head ≥ 0.01 because the area/Karakus floors are weak. The ranking is
uninformative exactly where it was meant to be used. The usable output is the
residue split and the closed rows; recorded in `39` §2 rather than dropped.

**The delivered side is the frozen-angle optimum, 87 rows in.** `frozen_opt.py`
asks run 67's `k = n` question per row: with every square free and the delivered
declaration, does anything fit `L0 − 1e−6`? All **87 of 87** beating rows with
n ≤ 200 are refused, i.e. certified, in 27 s; run 67's n = 294 refusal reproduces
as a control. This is a statement about the declared axis, not about every branch
structure. No row changed. Entries `39-RANKED-NEXT.md`.

## Run 77 — the catalogue block certified, the band above it too, and one ledger

`39` priced item 2 as a five-minute slice; it turned out to be the whole block,
because only 150 of the 553 beats sit at n ≤ 324.

**150 of 150 — the entire catalogue block.** `frozen_opt.py` refused a demand of
`L0 − 1e−6` at every beating row with n ≤ 324: 0 candidates, 147 s. So at each of
those rows no translation of the delivered angles, at the delivered axis
declaration, fits below the delivered side. The cost is ~n² (63 rows above n = 200
cost 122.7 s, the 87 below cost 24.3 s; slowest row 4.75 s at n = 303).

**The first rows past the frontier refused too.** I expected slack in
325 ≤ n ≤ 400, where the residue band m ≥ 21 puts the delivered sides within
0.02–0.05 of the zero-waste ceiling: **41 of 41** certified in 228 s, union
**191 of 191**. The certificate is not a small-n artefact. `frozen_opt.json` now
accumulates slices, so a band probe cannot erase the block below it.

**One ledger, stamped.** `row_census.py` ingests the certificate and gives every
row one status: **60** closed by a published bound, **191** `opt@declared`, **362**
beat-open, **387** grid-open. Stamping exposed a definitional defect: at a closed
row the old `head` formula returned `(L − grid)/√n`, a positive "opportunity" where
a published bound forbids any gain. It was tiny (max 5.0e−10, at n = 4) but wrong;
`head` is now exactly 0 there, asserted for all 60 by control 4.

**Attribution of the 0.163635 measured to be impossible.** The most generous
conceivable total — zero-waste ceilings over the 387 open grid rows (7.005752) plus
the headroom on the 553 beats (15.022691) — is **22.028443, 135× the gap**;
restricted to `head` it is 21.005091, 128×. No bound this project holds localises
the gap, and control 5 asserts that inequality so the negative stays visible. Item
3's accounting half is dead; its bookkeeping half is now the census. No row changed.
Entries `40-BLOCK-AND-ONE-LEDGER.md`.

## Run 78 — a construction aimed at the band (no beats), and the exact side of every row

The band turned out to be a catalogue edge, not a geometric wall, which is what
made it attackable at all.

**What the 247 are.** Above n = 324 the open rows are contiguous in the residue m,
one block per k, and each block starts exactly one past that k's last record
(k=18: beats m ≤ 20, open 21..35 … k=31: beats m ≤ 37, open 38..39). Since packing
n squares at L packs n−1 at L, the band's first row per k is the easiest, so 14
attempts speak for 247 rows. At the mean gain of the 403 beats above 324
(0.008808), the band is worth 2.176 — and 19 rows at that quality would cover the
whole 0.163635 gap.

**The construction: extend the record by one square.** Each anchor's box already
beats the grid, so one free unit square inside `L = k+1 − 1e−6` would beat the
band's first row outright. Scanned at 1/16 over six orientations (0, 45°, and four
small Pythagorean tilts): **0 of 14** free, the best placement overlapping by
0.094–0.142 (mean 0.1196), the *same* margin at every orientation — the free space
is box-shaped, not a hole a tilt could enter — and **70 local LPs** (new square plus
30 neighbours free) all infeasible. **0 gate passes.** The largest empty square in
each record is 0.86–0.91 across: the records are jammed. The family is nested, so
this closes it for every band row of every k. It does not prove the rows optimal:
a tilted boundary layer *built* rather than extended is untouched, and that is now
the only item on the list with score in it.

**The exact side of every row.** `exact_sides.py` computes `L = A + B·√2/2` with
`Fraction` arithmetic, decides maxima by squaring (never a float), and searches the
ideal over denominators ≤ 24 and |B'| ≤ 12: **447 rows in ℚ** (every one exactly
`⌈√n⌉`), **100 in ℚ(√2)**, **4 Pythagorean**, and **449 not expressible** because
their angles are polished rather than constructed. n = 50 comes out `53/7`, the
value doc `19` decoded independently; n = 326 is `15 + 5√2/2` even though its
stored side is rational, which is why B has to be searched rather than read off the
walls. Exact arithmetic and `sqscore.extent` disagree on 0 of 551 rows (worst
1.03e−13); 25 rows have no ideal inside the declared box (residual up to 2.4e−4)
and are recorded as such. No row changed. Entries `41-BAND-ATTEMPT-AND-EXACT-SIDES.md`.

## Run 79 — the tilted boundary layer built from scratch: capacity `m ≤ 0`

Run 78 closed one cheap route into the band (no row is one square from the
records); this run builds the other and closes it too.

**What the layer is.** n = 326's cell map, read exactly: a (k+1)-grid with two
opposite corners cut away in a 45° diamond (85 cells) and two 5×5 blocks of 45°
squares on the rotated unit lattice laid in the cuts (50), net −35 squares for
−0.4645 of side, at `15 + (5/2)√2`. Two structural facts: a 45° block's bounding
box is `√2 j` for `j²` squares, and a unit square's width is ≥ 1 in every
direction, so a seam of fractional width holds nothing — the tilt must be a whole
block traded against grid cells.

**Built and gated.** `layer_construct.py` generates that layer from `(j, delta,
sx, sy)` — trimmed axis grid plus two `j×j` rotated blocks at opposite corners —
and certifies through `packlib.finalize` then `declp.gate` at tol 0. Swept over
`j ≤ 8`, twelve deltas and a 5×5 offset grid, 24 gate calls per row: **0 of 14**.
The best gated build is the plain k×k grid at side k (`m_cap = 0`); with one
diamond or more it is `k² − 2`. **Capacity `m ≤ 0` at every k, against a band
requirement of m ≥ 21–38.**

**Why it loses, with the number.** At the n=326 record's own side the clean build
carries 290 where the plain grid carries 324 and the polished record 326: a j=5
diamond displaces ≈ 84 cells and returns 50, net −34. On an integer grid the
diamond trade is negative by area at every j. The table's 54 clean records at
m ≤ 13 are *polished* — fractional shifts, which is why their sides are
`A + B√2/2` with non-integer A (`15 + 5√2/2`, `13 + 4√2`, `k + √2/2`,
`467/17 − 11√2/2`) — and the menu of those families tops out at **m = 13 at any
k**, while the band starts at 21. No row changed. Entries
`42-LAYER-FROM-SCRATCH.md`.

## Run 80 — every solve we hold: no slack in a row, and the table is sixty slacks

Asked whether any solve we hold can be refined slightly further (not the ones
proven optimal), and whether a cascade family planner would propagate it.

**Refinement: 0 of 553.** Only 191 beating rows had ever been shrink-tested (run
77, a refusal at eps = 1e-6, which says nothing below a micro-unit); the 362
above n = 400 were untested because the global LP is dense and O(n²).
`refine_cascade.py` runs `declp.solve`'s formulation restricted to a radius where
pairs can still bind, frees the whole **wall ring** (every extreme-edge square
plus its 1.3-neighbourhood, cap 200, never hit), and walks a demand ladder from
1e-2 down to 1e-7, finalizing and gating every accepted round. All 553 refuse —
every beating row is locally wall-pinned at frozen angles. Controls: the local LP
agrees with `declp.solve` on feasibility; a rigid 5×5 grid refuses; a wall
loosened by +0.02 is put back in two rounds; the raw LP state is refused by the
gate and the finalized one accepted; the cascade arithmetic matches a hand sum.

**Cascade: the channel is already applied.** Against the *causal* class leader
(a larger row cannot serve a smaller one), **969 of 969** non-square rows sit
exactly at their residue class's chain value; 0 are open at 1e-8. The 25 rows
that look open at 1e-9 are `finalize`'s own 2e-9 scale, margin and not slack —
the same 25 run 42 saw from the stale table, now exact.

**So the table is a 60-parameter object**, `total = Σ_r Σ_k (k + δ*(r))/√n − 1000`
with `d(total)/dδ*(r) = W(r)`, `W(1) = 3.6453` over 31 rows. A class leader's
refinement propagates by the chain translation to its whole class, worth Δ·W(r)
— the leverage the user's hypothesis predicted, and exactly why the null result
matters: there is nothing to propagate. Only the 60 leaders can matter, and the
23 classes still at δ = 1 are the band's residues from runs 78–79. Left open and
named: rotation-enabled refinement (the LP freezes angles) and margin mining
(~1e-7 total, spends the 2e-9 rounding margin; not taken). No row changed. Entries
`43-NO-SLACK-SIXTY-SLACKS.md`.

## Run 81 — the space around each band anchor, over all orientations

Asked for the reverse of run 78's placement question: what is the largest empty
square in each block's last record, at any orientation, and is the deficit to
fitting another unit square uniform in orientation or only a right-angle artefact.

**The instrument.** `space_around.py` writes the largest square centred at a
point p and rotated by θ in closed form — containment, then four SAT axes per
packed square, each an affine bound on the side — so `s(p, θ)` is exact and
cheap; only the maximum over p is searched (covering grid, local subgrid on the
sharp peaks, pattern search to 1e-10), and every reported value is re-checked by
the same closed form and by an independent vertex-projection SAT. Five controls:
two unit squares in a 2-box give exactly 1; a rigid 10×10 grid gives 0; a holed
grid gives exactly 1 and gates at L = 8 + 1e-6; a 0.4 strip gives 0.4 at 0° and
0.4/√2 at 45°; and 729 placements of a mixed-angle state agree with the
vertex SAT.

**The answer.** Fourteen anchors (n = k² + M(k)), three boxes each, 17
orientations over 0..45°: the largest empty square is **0.695 to 0.807** of a
unit (mean 0.748), and the maximum is at **0° in all 42 states**. At 45° it
falls to 0.569–0.632, so tilt costs 0.115–0.176 of side (mean 0.144). The
deficit to one more unit square is therefore **0.193–0.305**, not ~0.1, and it
is not a right-angle artefact: the free space is rectangular and rotating the
candidate only makes it harder to fit. Moving the record in the larger beating
box (corner or centred) changes the answer by ≤ 0.003, so the bottleneck is the
interior of the layer. **0 of 42 states reaches 1, so nothing gates and no row
changed.**

**A correction, found on the way.** Run 78's scan required a separation of `1.0`
on the *packed* square's axes; a candidate tilted by θ needs `0.5k + 0.5` there
(k = |cos θ| + |sin θ| ≤ √2), so at a tilt its recorded overlap was too small and
"largest empty square = 1 − margin" (0.86–0.91) was an over-estimate. The verdict
is untouched — that scan was optimistic and still found no placement — but doc 41
now carries the correction. Left open: `s_max` is a verified achievable side, not
a proven maximum (dense 0.05-grid re-checks agree to ≤ 2e-5), and everything here
freezes the record; the measured deficit is the target a rearranged layer would
have to buy, not a route. Entries `44-SPACE-AROUND.md`.

## Run 82 — the same space, certified; and the initial placing varied

Two follow-ups to run 81: turn "achieved" into "proved with a gap", and see what
a different initial placing does to the numbers.

**Two independent upper bounds, both proved.** (a) A fitting square contains its
inscribed disk, so `s <= 2 c(p)` for the clearance `c`, hence
`s_max <= 2 max_p c(p)`; `c` is 1-Lipschitz, so a covering-grid branch and bound
prunes against the achieved side and certifies the maximum clearance from above.
(b) A square at angle θ contains an axis-aligned square of side
`s/(cos θ + sin θ)`, so `s <= √2 M(0)`; `s(p, 0)` is 2-Lipschitz, so a quadtree
certifies the axis-aligned maximum `M(0)` — at every anchor to **1e-4**. The
reported upper side is the smaller of the two; the disk bound won in all 42
states.

**The intervals.** Achieved 0.695–0.807, certified upper 0.788–0.886, gap
**0.071–0.098** per anchor (mean 0.088); `M(0)` equals the achieved global value
at all 14. The largest upper side over all 42 states is **0.8869 < 1**, so **no
unit square fits at any orientation** — proved, with at least 0.113 of side to
spare. The gap is bound looseness, not search error: the disk bound is exact only
in a strip and overstates the side by up to 69% at a corner, which control 6
pins exactly (0.4686 certified against a true 0.4 on a 0.4 strip).

**The initial placing, varied.** `--blocks b` splits the box into `b × b`
sub-blocks searched independently. With the same budget this is a resolution
lever: one global grid at 0.6 spacing loses 0.13 at k = 27 and k = 31 and 0.055
at k = 24; `b = 2` and `b = 4` recover all of them, and the winning block is
always in the upper half (the pocket sits on the boundary layer). It also
**corrected an anchor**: k = 29 is 0.736113, not 0.71218, verified exactly and
certified afresh (gap 0.0714; deficit 0.264 instead of 0.288). One honest cost:
at k = 23, `b = 4` gives 0.75268 against 0.75290, because a pocket on a block
boundary is split.

Left open and named: the certificate brackets the global maximum but does not
prove it is at 0° (the disk bound has no orientation in it); a tight value needs
an orientation-aware bound. No row changed. Entries `45-CERTIFIED-SPACE.md`.

## Run 83 — the mixed-field grammar: 0° and 45° as sentences, and the seam's exact price

**The question this run is built around.** The lattice perspective works up to a
point and then stops, and the reason is one sentence: `√2` is irrational, so no
scale and no symmetry label can make a 45° pose satisfy an integer lattice
predicate. That is a theorem about the predicate, and this run treats it as the
object of study: the alphabet is lifted one step to ℚ(√2), where the 0° and 45°
words are both legal and their seam is measurable in the same exact arithmetic.
Doc `19` §5 is corrected accordingly — the ladder's third rung is recorded there as
an interface measurement and its constructive lift, not as an anti-pattern.

**The arithmetic.** `scripts/qsqrt2.py` is `a + b√2` over `Fraction`, with the sign
decided by `a²` versus `2b²` in the mixed cases (no tie exists), so a contact is
exactly 0. The gate is the SAT predicate over the field: separated iff some axis
`q` of either square has `|d·q| >= 1/2 + ext_other(q)`, and the container side is a
field element, so "beats the grid" is a field comparison. Controls: 14,640 signs
against 70-digit `Decimal`; a 3×3 grid with 20 exact contacts (12 edge + 8 corner)
at `L = 3`; **274** states where the exact gate and `packlib.verify` agree, each at
least 1e-3 from contact; two overlaps refused with exactly `-1` and `-1/2`.

**Seven sentences, certified** (`scripts/mixed_field.py`, 6 controls):
the 45° pair at `1 + 3/4√2`; the `t = 1/2` pair at `72/35`; the `t = 1/5` pair at
`450/221`; the **corner glue** — four 0° squares in the corners, one tilted square
between them — at `2 + 1/2√2 = 2.707107` with **four exact contacts**, five squares
against the grid's 3 (gain 0.292893, exact density `(90 - 40√2)/49 = 0.682275`),
and at `19/7` for `t = 1/2` and `t = 1/3`; the `t = 1/5` glue at `47/17`; and the
ring nine at `2 + √2 = 3.414214`. Every side is the tight side of its family:
1e-3 less is refused, all seven.

**The seam law.** For the corner glue `L(θ) = 2 + 1/(cos+sin)`, and
`(cos+sin)² = 1 + sin 2θ <= 2` with equality only at 45°, so the 45° word is the
unique cheapest bridge in the family and every rational tilt pays an exact tax:
`5/7 - 1/2√2` for `t = 1/2` and `1/3`, `13/17 - 1/2√2` for `1/5`,
`25/31 - 1/2√2` for `1/7`. **The minimal glue word is one tilted square and it
couples four 0° squares at once** — four diagonal seams, each exactly tight. The
honest negative sits next to it: a diamond bridges a seam but cannot replace a
square, because the 3×3 ring around one needs `2 + √2` against the grid's 3.

**The modulator.** A first-order ΔΣ carrier with rational step `1/1000` on the
exact coordinates: the running average converges like `1/(M N)` (4.5e-4 → 1.9e-8
over `N = 1..10^4`) and the sentence does not. One rung of five is legal, and only
at a side larger by 1.9e-8; every refused rung is an overlap at the exact side or
below it. The irrational object exists in the discrete machine as the pair
`(a, b)`; the stream is its bounded shadow, and the bound is measured.

**The escalation, exactly.** At `N = 2` the shallowest tilt tested wins among the
words (`t = 1/7`, `1568/775`) and all words lose to the axis pair at 2; at `N = 5`
the 45° glue wins, with `t = 1/2` behind by `5/7 - 1/2√2`. The rational words have
a finite integral model (scale 70, 442, 1550); the 45° word has none, for the field
reason — which is why the second coordinate `b` is the label no scale can supply.

**The census.** 447 of 1000 delivered rows are exactly the 0° word (the 447 sides
in ℚ), 100 are the 45° word up to a 4.5e-13 rad decimal, 2 mix words, and **451 use
no word at all**. A lifted grammar cannot retrofit a decimal table; it has to
build — and 447 rows are already sentences of it. No row changed. Entries
`46-MIXED-FIELD.md`.

## Run 84 — the lift, the exact carrier, and the seam production rules

**What changed in the instruments, not in the table.** Run 83 measured the mixed
field; this run makes its three open pieces exact. `scripts/qsqrt2.py` gains a
symbolic reconstructor (`recover_side`, `recover_point`, `lift_sentence`, 10
controls) and `scripts/mixed_field.py` is rewritten around an exact carrier, the
seam production rules and a budgeted lift (14 controls). Ledgers
`workspace/push/uplift.json` (new; one record per mixed row) and
`workspace/push/mixed_field.json`. **No row changed, no score claimed,
`submission.csv` untouched.**

**Upgrade 1 — the symbolic perception lifter.** Given a decimal sentence and its
words, the lifter recovers the exact ℚ(√2) state: the box side by height-bounded
rational basis recovery (`a + b√2`, `b = num/den` for `den <= 8`, three stages so
that a row with side `3 + 4/3√2` is visible), the boundary layer by wall anchoring,
the rest by contact peeling — two independent equations at a time, 2×2 Cramer over
the field — and the squares the contact graph does not pin by coordinate-height
recovery on the row's own lattice denominator. The decimals only choose the
topology; every returned number is exact and `gate` decides. One fix is now a
control: the link list is directed (`i -> j` with `-sgn`, `j -> i` with `+sgn`);
reading both ends with one sign mirrors every placement built from it.

Measured on the 100 mixed rows (n = 5..974): **97 lifted, gate clearance exactly 0
on all 97, 0 violations, 127,837 certified contacts over 37,260 squares (9,003 of
them 45°), 26,024 centres by peel and 5,618 by recovery, and all 97 sides in
ℚ(√2) \ ℚ.** The three that do not lift are named: n = 51 and n = 295 have sides
that no small-height `a + b√2` fits — the residual falls as the coefficient bound
widens (2.74e-5 → 1.81e-5 → 1.13e-6 for n = 51) or stays flat at 1.33e-5 (n = 295),
and 1e-7 is far outside both — and n = 126 is one coordinate short (124/126
placed). **The 100 decimal shadows are 97 exact
sentences and 3 float artefacts** — the census line of `46` §6 is now a measured
split, and every one of the 97 sides being irrational is that section's obstruction
restated on the rows themselves.

**Upgrade 2 — the pure-algebraic ΔΣ carrier.** The accumulator is a field element,
the quantizer is the exact floor (`grid_round(z, M) = floor_q2(zM + 1/2)/M`), and
no `float()` exists in the carrier, the state, the Pell substitution, the seam
builder or the quantizer — control 4 walks the *bytecode*, because a source grep
trips over the docstrings. Two ladders against the gate: ΔΣ at `M = 1000` over
`N = 1..2000` is legal at **2 of 11** rungs (only at sides above the exact one, in
a stroboscopic pattern: the verdict is the sign of the bbox-defining coordinate's
quantization error); the Pell substitution `√2 -> p/q` is legal at **6 of 12**
convergents, and that ladder now has a closed form — the corners map to `1/2` and
`3/2 + r/2`, so the side is exactly `2 + r/2` and

    side excess = (r − √2)/2,        gate ⟺ r >= √2,

which proves the alternation for every rational `r` instead of tabulating twelve
residuals. **A rational carrier converges to the sentence and never returns it**;
legality is a half-line and the exact sentence is its endpoint, reached only by the
pair `(a, b)`.

**Upgrade 3 — the seam production rules.** `S(k, m)`: four `k × k` axis blocks in
the corners and an `m`-diamond 45° strip on the anti-diagonal (`k = 1, m = 1` is
the run-83 corner glue). Closed forms, exact:

    side        L(k, m) = 2k + m√2/2
    count       N(k, m) = 4k² + m
    void        V(k, m) = L² − N = 2km√2 + m²/2 − m
    side cost   L(k, m) − 2k = m√2/2
    gain        ⌈√N⌉ − L = 1 − m√2/2

The seam has no slack parameter: consecutive diamonds are `1/√2` apart, which is
exactly a 45° square's axis extent `√2/2`, so every consecutive pair is a contact
and the strip's band width is `√2` with zigzag amplitude `√2/2`. **54/54 certified**
for `k = 2..10`, `m = 1..6`: gate yes at the closed-form side, no at `L − 1e-9`.
`gain = 1 − m√2/2` changes sign at `m = √2`, so a single diamond is a strict
improvement over the plain `(2k+1)²` grid at `4k²+1` squares for **every** block
size, while `m >= 2` loses (the strip's void grows in `m` twice over). It is a
proved grammar for a family the delivered table already dominates (by 0.03–0.17 of
side at n = 17, 37, 65, 101, 325, 401), so it changes no row — which is what it was
asked to be: the general form of the corner glue with the price written in `(k, m)`,
instead of a patch aimed at one doomed `n`.

**Honest negatives, stated.** A rational carrier cannot certify the irrational
sentence, and the gap is now a closed form rather than a residual table. Three of
the 100 rows are not ℚ(√2) sentences at all. `S(k, m)` is proved minimal only
within its own contact structure, and it is dominated on the table. No row changed.

Entries `47-LIFT-CARRIER-SEAM.md`; `46` §4 carries a supersession note and §6 the
lift's measured split; records `31`–`47`.

## Run 85 — the field tower, the wheel engine, and a second domain

**What this run is.** Run 84 left three things domain-specific: the ring logic
lived inside ℚ(√2), the declared-law wheel pattern lived inside packing, and the
reconstruction's fallback was a per-coordinate height search. This run extracts the
first two, replaces the third, and uses them to close the census.
`scripts/exact_field.py` (7 controls) and `scripts/glm_wheels.py` (12 controls) are
new; `qsqrt2` and `mixed_field` keep their 10 + 14 controls unchanged. Ledgers
`workspace/push/glm_wheels.json`, `q_census.json`, `outlier_probe.json`.
**No row changed, no score claimed, `submission.csv` untouched.**

**The tower.** `exact_field` is Z, Q, Q(√d) for any square-free d, and rational
t-basis points, with every decision derived from one `sign()`: comparisons are the
sign of a difference, `floor` is a bisection on sign tests inside an exact bracket,
`ceil = −floor(−z)`, and the mixed sign cases reduce to `a²` vs `d b²` (no nonzero
rational solution, since d is square-free). 1,400 signs across d = 2,3,5,6,7,10,13
agree with 70-digit `Decimal`; 600 floors satisfy `k ≤ z < k+1`. `qsqrt2.Q2` is now
`Quad` with d = 2; the API is unchanged and every sampled lift verdict is identical.

**The audit, as a deliverable.** `no_float_calls`/`audit_module` walk **code
objects** — source text cannot fake a pass — and the audit is itself tested against
a planted `float(z) > 0`. It exempts exactly three declared things: display
(`__float__`, `decimal`), the self-test (which plants the offender), and
`float_state` (which feeds `packlib` as an independent float-side witness). Run-85
audit: **145 decision functions across the three instruments, 0 naming float.**

**The engine.** A domain registers an alphabet (atomic words with exact measure and
extent), five syntax slots — `Tile`, `Frame`, `Strip`, `Glue`, `SymmetryFold` — with
closed-form laws and exact builders, and a witness suite. `Wheel.spin` only
enumerates declared cells, takes a `Refusal` with a named law, runs every witness,
and records the verdict; `Engine` holds domains and contains no geometry. Every
claim must pass **four** witnesses of different kinds: the exact gate, a topological
witness (contact graph / factor complexity), a conservation identity, and an
independent 70-digit `Decimal` recomputation whose signs must equal the exact ones
(control 10 shows it rejecting a claim off by 1e-9).

**Spatial geometry.** 28 cells, **25 certified**, 3 refused by
`strip_needs_diamond` (S(k,0) is the plain 2k grid: no seam). The closed-form
families: grids `k²` at k; pockets `4k²+1` at `2k + 1/2√2` (n = 5 at k = 1);
strips `4k²+m` at `2k + m√2/2`; rational-t glues at `19/7`, `47/17`; and the
diagonal fold, whose law is that N and L are invariant. Gain is `1 − m√2/2`, so only
m = 1 wins. **n = 10 and n = 40 are registered as atoms, not as closed-form cells** —
their lifted sentences are certified with all four witnesses but neither is
`4k² + m`, and a ladder covering them is deferred rather than fitted.

**Sturmian sequences — the second domain.** The same engine, the same slots, nothing
geometric: mechanical words over an exact slope, rotation frames, orbit windows,
consecutive-window glues and reversals. **6 of 7 cells certified**; the refusal is
the point — slope 1/2 is refused by `not_sturmian` with `p(2) = 2 ≠ 3`, because a
rational slope is periodic and periodicity is exactly the failure of `p(m) = m+1`.
The certified cells carry `√2` in their weight laws (`18 − 5√2`, `15 − 3√2`). The
coboundary law had to be corrected during the run: `∂(uv) = ∂u ⊕ ∂v` is **false**;
the seam-aware identity is `∂(uv) = ∂u ⊕ (u₋₁ ⊕ v₀) ⊕ ∂v`.

**The census, and a correction to run 84.** All **447** pure-Q rows are certified at
clearance exactly 0 with side exactly `⌈√n⌉` — 419,281 exact contacts over 205,282
squares, 136 rows certified by the exact gate and 311 by an exact lattice lemma
(distinct half-integer centres in an integer box ⟹ separated by ≥ 1 on some axis,
which is the SAT condition for this word), the two paths agreeing wherever both run.
And run 84's "3 float artefacts" was wrong for two of the three: `recover_side`
allowed `b` denominator 3 while forcing `a` onto 1/8 and 1/64 grids, and both n = 51
and n = 295 have sides with third-denominators — `16/3 + 5/3√2` and
`22/3 + 22/3√2`. With the search fixed the mixed lift is **99/100** (128,895
contacts over 37,606 squares, 9,180 tilted, 26,016 peeled + 5,795 recovered, all at
clearance 0), and the only failure is n = 126, where 125 of 126 centres lie in the
field and one 45° square's coordinate is off every small-height lattice tested. The
probe across square-free d ≤ 21 finds ℚ(√2) for all three rows and no other field.

**The exact 2D cage.** The per-coordinate height fallback is replaced by a joint
object: lattice candidates within 1e-7 of each stored coordinate, filtered by the
box and by the exact SAT predicate against every placed square, returned canonically
(nearest, ties lexicographic), with an empty cage returning nothing. It recovers the
freed square of S(2,1) exactly and is what refuses n = 126's square 120 rather than
proposing a value that would fail the gate.

**Deferred, and named.** A closed-form ladder covering n = 10 and n = 40 from their
lifted states; a resolution of n = 126's single square; and a third domain (lattice
shells in ℚ(√d), or the parity-coboundary complex as a domain rather than a witness)
to test "domain-agnostic" harder than two domains can.

Entries `48-FIELD-TOWER-AND-WHEELS.md`; `47` §1.4 carries the correction note;
records `31`–`48`.

## Run 86 — a third domain, an induction that failed, a complete field census

**What this run is.** Three of run 85's open items, taken in order: register a third,
structurally distinct domain on the same wheel engine; try to promote the lifted atoms
(n = 5, 10, 40) from atoms into closed-form families; and close n = 126 plus classify
every remaining row. One of the three produced a negative, and the negative is the
result. **No row changed, no score claimed, `submission.csv` untouched.**

**Third domain: lattice shells.** `scripts/lattice_shells.py` registers `Z^d`, `D4` and
`E8` on the same engine with no arithmetic in common with the packing domain: vectors
are held *doubled* (a point of (1/2)Z^d is a tuple of ints `y` meaning y/2), so norms
are `sum(y*y)/4`, inner products integer sums, and theta coefficients exact counts.
The five slots get new meanings — `Tile` = a shell, `Frame` = the minimal shell and its
kissing graph, `Strip` = the ball as annuli, `Glue` = a direct sum, `SymmetryFold` =
`v -> -v` — and the witnesses are exact-norm, kissing-topology, theta-conservation and
an independent 70-digit Decimal recomputation. Theta series are computed, not looked
up: Z^2 1,4,4,0,4,8,0; Z^3 1,6,12,8,6,24,24; Z^4 1,8,24,32,24,48,96; D4
1,0,24,0,24,0,96; E8 1,0,240,0,2160, with kissing numbers 4/24/240 and root degrees
8/56 (Z^2 has no root graph). The wheel spins **24 of 28 cells certified**, and the
four refusals are laws: `empty_shell` for D4 at m = 3 and E8 at m = 1 (even lattices,
odd norm), `rank_budget` for Z^2 (+) E8 (rank 10) and Z^4 (+) E8 (rank 12).
`theta(A (+) B) = theta(A)*theta(B)` is checked cell by cell: Z^2 (+) D4 enumerates
(1,4,28,96,124), equal to the convolution of the summands' theta series at every m.

**Friction, recorded rather than smoothed.** Four places where the engine was only
*conventionally* domain-agnostic: (1) a real bug — running `glm_wheels.py` as a script
makes it `__main__`, so a domain module importing it gets a second module object with
different `Claim`/`Refusal` classes and `except Refusal` silently fails; fixed with one
`sys.modules.setdefault` line; (2) `Wheel.spin`'s row schema is packing-shaped (it
reads `n`, `laws["extent"]`, `meta["beats"]/["gain"]`); (3) `DecimalWitness` assumes a
`Quad` scalar, so the lattice domain needed its own Decimal witness even though the
witness *protocol* generalized; (4) "four witnesses" is per family — the kissing
witness applies only to `Frame`/`Atom`, so a `Glue` cell has three kinds of evidence,
and control 16 asserts three rather than pretending otherwise.

**The induction, and why it failed.** `scripts/grammar_induction.py` asks one exact
question: is a lifted atom a composition of the declared vocabulary? A template occurs
iff one of the five isometries of the unit square — identity, the two axis
reflections, the diagonal reflection, a quarter turn — carries its centres *and its
words* into the state under a single translation; a cover is a set of disjoint
occurrences; only an exact cover counts. Over 45 states (the three atoms plus every
related lifted row that lifts inside the budget) and 13 templates, the answer is
**1 exact decomposition in 45** — n = 5 via `Pocket1`, which is the closed form we
already had and is the same sentence as the atom. `Strip2,1` and `Glue1/2` occur in
zero states; `Pocket1`/`Fold1` occur only in n = 5 itself. What the search does show is
precise: the best cover is always `Tile1` and it covers *exactly the axis squares* —
n = 10 8/10 (2 diamonds), n = 40 24/40 (16 diamonds), n = 19 11/19, n = 26 17/26,
n = 27 22/27, mean 0.7324 — and n = 40 additionally contains four exact 2x2 `Tile2`
blocks (16 squares). So the atoms are irreducible over the *families* while being
trivially decomposable over the *alphabet* (Tile (+) diamond, N = a + d). The missing
piece is named: a diamond-placement primitive, because `Pocket` and `Strip` embed
diamonds only in their own fixed patterns and these rows tile irregular diamond sets.

**n = 126 closes on a distinction.** The lift places 124 squares and *recovers square 98
exactly* as `(5 - 2 sqrt2, 19/2)` — height 2, missed before because its neighbour
needed a third-denominator component — leaving square 120. That square touches exactly
two squares and both contacts constrain the *same* SAT axis, so the two equations are
identical: `y - x = 11/2 + (5/2) sqrt2`, rank 1. The stored pose satisfies it to
1.5e-9, and the exact feasible set on that line is a segment
`x in [1.3357864376269049, 1.3713203435596426]` of width 0.0355339059, with the left
end bound by partner 109 and the right end by 98. The cage at tolerance 1e-7 and 1e-4 is
**empty** (the stored coordinate is not a small-height field element), but the cage at
large tolerance contains **173** Q(sqrt2) placements at clearance 0 (denominators
<= 32, heights <= 8), the nearest at `x = 43/32`, L1 distance 8.2e-3. The honest ledger
is therefore two numbers: **99/100 poses lifted exactly**, and **100/100 rows whose
contact topology has a Q(sqrt2) realisation**. They are different claims and must not
be merged.

**The 1,000-row field census.** `scripts/field_triage.py` gives every row one exact
class, with 70-digit Decimal trigonometry (Taylor series, exact-precision range
reduction, no float), a continued-fraction test for rational `t = tan(theta/2)` with a
declared 1e-12 residual, and the exact `recover_scalar` side test on a deliberately
small lattice (denominators <= 8, height <= 4). Result: **447** grid, **99** Q(sqrt2)
pose, **18** Q(sqrt2) side (including n = 126 at `15/2 + 3 sqrt2`), **5** Q(sqrt7) side
(n = 18 at `7/2 + sqrt7/2`, then 53, 151, 234, 747), **3** Q(sqrt5) side (n = 335, 373,
454 at `99/8 + 23/8 sqrt5` and neighbours), **4** rational-t (n = 50, 171, 198 with t
denominators <= 3; n = 230 with <= 7) and **424** continuous. The 26 side-field rows are
the new residue: exact boxes, no rotation argument, no wheel cell.

**Deferred, and named.** A diamond-placement primitive with the induction search as its
acceptance test; a Q(sqrt7) wheel for the side-field rows (a one-parameter change to
the same engine); a fourth domain as the next stress test. Entries
`49-THIRD-DOMAIN-AND-FIELD-CENSUS.md`; records `31`–`49`.

---

## Run 87 — one contract, a cage without monkeypatching, and the diamond primitive

**What was asked.** Three items left open by doc 49, with the table, `submission.csv`
and the root whiteboard untouched: generalise the engine's schema and witness
contracts; fold run 86's n = 126 probe into `qsqrt2.py` as a mode with a permanent
control; build the diamond-placement primitive and pass the induction acceptance test.

**The contract.** `Wheel.spin` no longer writes `n`, `extent`, `gain`. It writes
**size**, **measure**, **invariant** and a witness count; `Claim.n` is a read-only
alias so no builder changed. Witness suites are declared per family
(`Witness.families`) and filtered by one `Domain.suite(claim)`; only `KissingWitness`
scopes itself, and now it says so itself instead of relying on the wheel's ordering.
One `DecimalWitness` with a per-domain `scalar` (a `Quad` of any `d`, a `Fraction`, an
`int`, a `Decimal`) replaces the packing-only 70-digit witness. The result is one
table for three domains — 28/31 spatial, 6/7 sequence, 24/28 lattice certified — with
`w` = 4 or 3 per row, and 17 controls passing. The friction is gone at the level it
was described: nothing inside the wheel, the suite or the Decimal witness knows what
a square is.

**The cage.** `qsqrt2.cage_segment(state, words, pos, L, j)` derives the rank, the
contact law, the feasible segment and the `Q(sqrt2)` enumeration from the state
alone — no typed bounds, no spy, no monkeypatch. `lift_sentence` returns `pos` and
`lo` so the state can be read. For n = 126 it reports rank 1, law
`y - x = 11/2 + 5/2 sqrt2`, the segment `x in [1.3357864, 1.3713203]` (width
0.0355339) and the nearest placement `x = 43/32` at L1 8.2e-3, which passes the exact
gate at clearance 0.

**And a correction.** The permanent control asserts the cage holds **4** `Q(sqrt2)`
placements, not 173, and asserts the 173 separately under `legacy=True`. Run 86's
number counted candidates whose *rational part* fell in the band — a `Q(sqrt2)` value
was filtered by `x.a` — and its box test checked `y` containment but not `x`, so
squares parked outside the container were admitted and the exact gate, which only
asks for pairwise separation, passed them. The legacy switch keeps that number
reproducible so the correction cannot be buried. The scientific conclusion is
unchanged: n = 126 is an off-lattice pose with on-lattice topology.

**The diamond.** `DiamondField` declares `cells` (a bent grid, or explicit axis
centres) and `slots`; the insertion rule drops colliding axis cells and derives L, the
void, the gain and the contact graph. The acceptance test is exact in all three cases:
n = 10 (8 axis + 2 diamonds, 8 of 16 axis cells dropped, `L = 3 + 1/2 sqrt2`), n = 19
(11 + 8, `L = 3 + 4/3 sqrt2`) and n = 40 (24 + 16, `L = 4 + 2 sqrt2`) — 10/10, 19/19,
40/40 covered, every field identical to its Atom cell with L reproduced. Three
`DiamondField` cells are certified on the spatial wheel. Honest limits: n = 19 and
n = 40 list their axis cells explicitly because those sets are not product grids, and
`strip_needs_diamond` still fires for `S(k, 0)` because the Strip builder does not yet
consume a field.

**Verification.** `glm_wheels --selftest` 17/17; `qsqrt2 --selftest` 11/11;
`grammar_induction --selftest` 3/3; `lattice_shells` via the wheel; float audit
**174 functions, 0 offenders**; `record_guard.py` OK. No row changed.

Entries `50-ENGINE-CONTRACT-AND-DIAMOND.md`; records `31`-`50`.

---

## Run 88 — the strip as a field, and cells from run parameters

**What was asked.** Close doc 50's first two limits: wire the Strip builder to consume a
DiamondField so `S(k,0)` is no longer refused as `strip_needs_diamond`, and generate
n = 19 / n = 40's axis cell sets from a declared cell algebra instead of explicit lists,
with every control and the float audit green.

**The strip.** `p_strip(k, m)` no longer refuses at m = 0. It assembles from
`strip_field(k, m)`: two k-runs per axis separated by a seam of width `m*sqrt2/2`, plus m
slots on the anti-diagonal at `(k + (2i+1)sqrt2/4, k + (2(m-1-i)+1)sqrt2/4)`. At m = 0
the seam width is 0, the slot list is empty and the carrier is the plain 2k grid, so the
cell certifies with N = 4k^2, L = 2k and **gain 0** — the honest statement that an empty
seam buys nothing. The spatial wheel is therefore **31/31 certified, 0 refused**: the
packing domain's last three refusals are gone because the thing they said was missing now
exists. Control 19 pins `S(k,0)` to `p_grid(2k)` (same cells, same L, gain 0, k = 1..4)
and checks `S(k,m)` against the run-84 sentence for m >= 1; control 5 was rewritten,
since "the wheel must have at least one refused cell" is no longer true — it now asserts
that no spatial cell refuses and exercises every refusal law on a constructed cell
(`degenerate_cell`, `negative_seam`, `unknown_field`, `no_diamond`,
`declaration_overlaps`), with the other two wheels still refusing by `not_sturmian`,
`empty_shell` and `rank_budget`. The mechanism is tested harder than before.

**The algebra.** Run 87's claim that n19 and n40 "are not product grids" was wrong. Tested
against their slot lists, both carriers are exactly a product minus collisions: n19 with
X = {1/2,3/2} u {1/2+a,3/2+a,5/2+a}, Y = {1/2,3/2,5/2} u {3/2+a,5/2+a} (a = 4/3 sqrt2),
carrier 25 -> 11 cells; n40 with X = Y = {1/2,3/2,5/2} u {3/2+2sqrt2,5/2+2sqrt2,
7/2+2sqrt2}, carrier 36 -> 24. A field is now two short run lists plus its slots, where a
run is `(start, step, count)` in Q(sqrt2) and the carrier is the product of the two
skeletons; run 87's "bent grid" is the two-run case. Control 18 compares the generated
cells against the run-87 census cell by cell (8/11/24, all equal), and refuses to pass if
a field needs more than two runs per axis. The drop counts move in the honest direction —
n19 0 -> 14, n40 0 -> 12 — because the carriers are now full products and the insertion
rule does the trimming; N, L, void and contacts are identical to run 87 and the induction
acceptance test is still 10/10, 19/19, 40/40 exact.

**Verification.** `glm_wheels --selftest` **19/19** (was 17); spin spatial **31/31**,
sequences 6/7, lattice 24/28; float audit **177 functions, 0 offenders**;
`grammar_induction --selftest` 3/3 with the acceptance exact; `qsqrt2 --selftest` 11/11;
`field_triage --selftest` 4/4; `record_guard.py` OK. No row changed.

Entries `51-STRIP-AS-FIELD.md`; records `31`-`51`.

---

## Run 89 — one build path, and a count that cannot go stale

**What was asked.** Rewire `p_pocket` through `strip_field(k, 1)` so strips and pockets
share one build path, and remove the dead `checks` counter from `glm_wheels`' selftest so
the control count is derived rather than hardcoded, with all 19 controls and the float
audit green.

**One path.** `p_pocket(k)` now assembles from `strip_field(k, 1)` through the same
`_assemble_field`, keeping its own family and parameters — the pocket *is* S(k,1), so two
builders were two spellings of one object, and run 84's `Q_mixed_strip` is now only the
witness (control 12's cage recovery, control 19's cross-check) rather than the source.
Control 19 carries the equality for k = 1, 2, 3: same state, same words, same L, same
N = 4k^2 + 1, families distinct. The wheel's Pocket rows are unchanged (5 at
`2 + 1/2 sqrt2`, 17 at `4 + 1/2 sqrt2`, 37 at `6 + 1/2 sqrt2`), all certified, spatial
31/31.

**One count.** `checks = 0` was incremented nowhere and the summary line was a hardcoded
number that run 88 had already broken. The counter is gone: each control announces itself
through `say(...)`, and the summary is `len(announced)` — so the number is the number of
controls that ran. The `--selftest` branch of `main` also stopped returning the count as
its exit status (it used to `return selftest()`); it runs the controls and returns 0, so a
passing selftest exits 0 and a failing one raises.

**Verification.** `glm_wheels --selftest` 19 controls (counted), exit 0; spin spatial
**31/31**, sequences 6/7, lattice 24/28; float audit **177 functions, 0 offenders**;
`grammar_induction --selftest` 3/3; `qsqrt2 --selftest` 11/11; `field_triage --selftest`
4/4; `record_guard.py` OK. No row changed; nothing new was discovered.

Entries `52-ONE-BUILD-PATH.md`; records `31`-`52`.

---

## Run 90 — one seam law, a malformed declaration, and the ridge rungs

**What was asked.** Unify the Strip/Pocket laws, add a control proving a genuinely
malformed field declaration is refused by `declaration_overlaps` rather than certifying,
and extend the spatial wheel to the census's remaining algebraic rungs (Q(sqrt5),
Q(sqrt7), rational-t) with exact sides calibrated against the delivered table and exact
refusal laws where constraints fail.

**One seam law.** `_assemble_field` already sets `diamonds`, so `p_strip`'s second
assignment was dead; `p_pocket` now carries the same `seam` law. Strip and Pocket claims
differ only in family and parameters — the pocket *is* S(k,1), now stated in the claim.

**Malformed declarations.** Control 20 refuses three ways, all by `declaration_overlaps`:
two coincident slots and two slots 1/10 apart (caught by the gate, because the insertion
rule cannot see slot-slot overlap at all), and a slot over an axis cell with the rule
switched off (caught by the rule). The second case is the one that made the gate load-bearing.

**The ridge.** The strip's seam width is not a special case: with the tilted square
centred in the seam, the two binding contact conditions are `(1+w)(c+s)/2 = (1+c+s)/2`
and `(1+w)/2 = (1+c+s)/2`, so `w* = min(1/(c+s), c+s)` and **L = 2k + w***, exactly, at
clearance 0. At 45 degrees that is `sqrt2/2` — the Strip, cell for cell. The other members:
`Slope` 2:1 in Q(sqrt5) at `L = 2k + 1/3 sqrt5`; `Seventh` with the word `(sqrt7/4, 3/4)`
in Q(sqrt7) at `L = 2k + 6 - 2 sqrt7`; `Tilt` t = 1/2 at `L = 2k + 5/7`. Nine new cells
(k = 1, 2, 3), all four witnesses, **spatial 40/40 certified, 0 refused**. The circle
identity is checked in the field, so no word is normalised numerically.

**One gate, any field.** `qgate(cls, ...)` is a port of `qsqrt2.gate` over any
`exact_field.Quad(d)`; the gate, contact-graph, conservation and Decimal witnesses read
the claim's field instead of assuming sqrt2, and `_tag` rebuilds the grid side in that
field (the first failure of the run was literally "cannot mix Q(sqrt 2) with Q(sqrt 5)").
Control 21 proves the port agrees with the original exactly on the three atoms and that
the 45-degree ridge reproduces the Strip.

**Calibration.** At n = 5 the delivered side is `2 + 1/2 sqrt2 = 2.707107`; the rungs lose
by `1.39e-3` (Seventh), `7.18e-3` (Tilt) and `3.83e-2` (Slope) — 45 degrees remains the
best angle of the family. n = 17 and n = 37 cannot be calibrated: those delivered rows
carry an orientation outside the axis/45-degree alphabet, so they do not lift and have no
exact side; the cells are recorded as **uncalibrated, not as wins**.

**Verification.** `glm_wheels --selftest` **21 controls** (derived count), exit 0; spin
spatial **40/40**, sequences 6/7, lattice 24/28; float audit **197 functions, 0
offenders**; induction acceptance 10/10, 19/19, 40/40 exact; `qsqrt2 --selftest` 11/11;
`field_triage --selftest` 4/4; `record_guard.py` OK. No row changed.

Entries `53-RIDGE-AND-RUNGS.md`; records `31`-`53`.

---

## Run 91 — one gate, parametrised by its field

**What was asked.** Parametrise `qsqrt2`'s gate over the field class instead of keeping a
second copy in `glm_wheels`, make control 21 compare the two on every spatial cell, and cut
any helpers the run-90 additions left unused.

**One procedure.** `frame_extent`, `axis_extent`, `side`, `pair_axes` and `gate` in
`qsqrt2` now take `cls` -- an `exact_field.Quad` subclass -- defaulting to the class read
off the first coordinate (`field_of`). Every constant is built from it (`cls(F(1,2))`,
`cls(2)`, `cls(0)`), so a Q(sqrt5) or Q(sqrt7) sentence is decided by the same code, and
every existing caller of `Q.gate(state, words)` is unchanged and returns the same numbers.
`glm_wheels` loses `qgate`, `qpairs`, `qside`, `qframe_extent` and `qaxis_extent` (~60
lines of duplicated algebra); `gate_of`/`pairs_of` pass the claim's field class through.
Two run-90 helpers nothing called are gone as well: `field_class` and `sqrt_in`. The float
audit drops from 197 to 191 decision functions -- seven removed, one added (`field_of`).

**Control 21, widened.** It now builds all 40 spatial cells through the domain and checks,
for each, that the inferred-class and declared-class verdicts agree on ok/L/clearance/
contacts/violations, that `gate_of(claim)` equals both, and that for **every pair** the
axis vectors and slack signs from `Q.pair_axes` and `pairs_of` are identical. The ridge
assertions stay: the 45-degree member is `S(k,1)` cell for cell, and every rung gates at
clearance 0 with its exact side and calibration.

**Verification.** `glm_wheels --selftest` 21 controls, exit 0; spin spatial **40/40**,
sequences 6/7, lattice 24/28; float audit **191 functions, 0 offenders**;
`qsqrt2 --selftest` 11/11 (the parametrised gate still passes the cage controls);
`grammar_induction --selftest` 3/3; `field_triage --selftest` 4/4; `record_guard.py` OK.
No number moved; no row changed.

Entries `54-ONE-GATE.md`; records `31`-`54`.

## Run 92 — the bar, and the word the table actually uses

**What was asked.** Generalize the ridge and the strip builders so the ridge family holds
m tilted squares over Q(√2), Q(√5), Q(√7) and rational-t rungs, deriving the exact seam
width w*(m) and the slot placement algebraically; reproduce `strip_field(k, m)` at 45° and
the single-seed ridge at m = 1; then decide honestly whether any (k, m) captures the
census's n = 18 row at `7/2 + √7/2`, and if not, read that row's pose to name the
grammatical word behind its side.

**One procedure.** The bar is m tilted unit squares edge to edge along `−v = (s, −c)`, slot
`i` at `centre + (i − (m−1)/2)(s, −c)`, so consecutive slots share an edge for every m.
Because the bar's centre moves by `+w/2` and the far blocks by `+w`, every block-slot
slack is **linear** in the seam width: with `d(w)·q = P + Q w` and
`need = 1/2 + (|c|+|s|)/2` on every axis, `|d(w)·q| = need` has the closed-form roots
`(±need − P)/Q`. `ridge_widths` collects them in the field, `ridge_width` returns the
smallest root at which the exact gate passes — a contact width by construction, with no
scan and no tolerance. `p_ridge(d, c, s, k, family, params, m=1)` gates the sentence and
`p_slope`/`p_seventh`/`p_tilt` take m; refusals stay declared (`word_off_circle`,
`no_contact_width`, `ridge_cuts_corner`, `degenerate_cell`, `negative_seam`).

**Control 22.** At 45° the ridge equals `strip_field(k, m)` cell for cell, slot for slot
and side for side on all nine `(k, m)` with `k, m = 1..3` (`L = 2k + m√2/2`, `N = 4k² + m`),
and `m = 1, k = None` still gives run 90's `min(1/(c+s), c+s)`. The exact law
`w*(2) = 2w*(1)` holds on all four rungs; past m = 2 the binding pair re-binds — the 45°
rung stays linear through m = 4 while the Q(√7) rung's m = 3 is **smaller** than
`3·w*(1)` (`−1/2 + √7`), which the control reports rather than asserting away. The wheel
gains `m = 2` at `k = 2, 3` on the three non-45 rungs (m = 2, k = 1 is refused
`contact_graph_thin`, the same floppiness that keeps `S(1, 2)` out), so the spatial wheel
is **46/46** certified.

**The n = 18 answer, once.** `N = 18` forces `(k, m) = (2, 2)`; the four rungs give
`4 + √2`, `4 + 2/3√5`, `4 + 4/7√7` and `38/7` against the row's `7/2 + √7/2`, and the seam
width it would need, `(√7 − 1)/2`, is not any rung's `w*(1)` or `w*(2)`. So **no member
captures the row**, asserted per rung. Reading the row instead: its 12-dp tilt recovers at
70 digits to `cos = 1/4 + 1/4√7`, `sin = −1/4 + 1/4√7` (on the unit circle exactly), so
run 90's Q(√7) word was an invention and `_sqrt7_word` is now the table's own — and all 36
coordinates of the 18 centres recover in Q(√7) with denominators ≤ 16. The pose is 10 axis
squares on `±(5/4 + √7/4)²` plus 8 tilted ones, giving
`L = 2(5/4 + √7/4) + 1 = 7/2 + √7/2 = 3 + 2cos`. An **odd** rational part and a cosine
term, where the ridge's side is an even `2k` plus a seam width with flush blocks: the row
is a ring sentence, and the mismatch is grammatical, not a near miss in the width.

**Verification.** `glm_wheels --selftest` **22 controls**, exit 0; spin spatial **46/46**,
sequences 6/7, lattice 24/28; float audit **195 functions, 0 offenders**;
`grammar_induction --selftest` 3/3; `qsqrt2 --selftest` 11/11; `field_triage --selftest`
4/4; `record_guard.py` OK. No row changed.

Entries `55-THE-BAR-AND-THE-WORD.md`; records `31`-`55`.

## Run 93 — the Q(√7) family, its one word, and a ring that refuses

**What was asked.** Recover the exact word, pose counts and side for every census row whose
side lies in Q(√7); decide honestly whether they follow n = 18's ring law or split into
sub-families; then build and gate-verify a field-general Ring family, registering the Q(√7)
word so n = 18 at `7/2 + √7/2` is constructed rather than read.

**Recovered.** Run 86's sweep names five rows — n = 18, 53, 151, 234, 747 — and control 23
re-derives each from its own pose: extremes recovered in Q(√7) at 70 digits
(denominators ≤ 16), side = `far − near + 1` equal from x and from y. Every one carries the
*census word* `((1+√7)/4, (√7−1)/4)` (unit-checked exactly), though the alphabets differ:
1, 3, 2, 1 and 663 distinct tilt angles, with 8, 6, 24, 36 and 2 squares at the word.

| n | axis | tilted | side | k |
|---|---|---|---|---|
| 18 | 10 | 8 | `7/2 + ½√7` | 1 |
| 53 | 39 | 14 | `13/2 + ½√7` | 5/2 |
| 151 | 125 | 26 | `23/2 + ½√7` | 5 |
| 234 | 198 | 36 | `29/2 + ½√7` | 13/2 |
| 747 | 83 | 664 | `53/2 + ½√7` | 25/2 |

**The law.** A ring's corner squares sit flush at `±(k + c)`, so
`L = 2k + 3/2 + (c + s)` — `ring_side` — which is `7/2 + ½√7` at `k = 1` and so contains run
92's `3 + 2cos` as its `k = 1` case (`2cos = 1/2 + ½√7`). Solving it per row: **integer k for
two rows (18, 151) and half-integer k for three (53, 234, 747)** — the family splits by the
parity of `k`, not by the side law.

**The ring sentence refuses.** `ring_frame`, `ring_candidates`, `ring_field` and `p_ring`
are in `glm_wheels`, field-general, with the exact gate as arbiter; every candidate at
Q(√7) and 45°, `k = 1, 2` collides or misses the derived side, so the family refuses with
the declared law `ring_unresolved` and **no Ring cell is registered**. Reading the census
pose says why: its 18 squares are 10 boundary axis squares + 4 tilted in the edge gaps + 4
in a central pinwheel — a different sentence shape from four corner modules — and its
sibling tilted pairs are exactly unit-apart while its module-to-frame distances carry
0.03–0.07 of slack, so the recorded pose is a polished decimal packing, not an exact contact
sentence. The exact ring needs the module tangent to the frame and to its gap/pinwheel
neighbours at once: a coupled solve the run did not finish, recorded as the next job.

**Verification.** `glm_wheels --selftest` **23 controls**, exit 0; spin spatial **46/46**,
sequences 6/7, lattice 24/28; float audit **200 functions, 0 offenders**;
`grammar_induction --selftest` 3/3; `qsqrt2 --selftest` 11/11; `field_triage --selftest`
4/4; `record_guard.py` OK. No row changed.

Entries `56-THE-SQRT7-FAMILY-AND-THE-RING.md`; records `31`-`56`.

## Run 94 — the ring, solved from its own tangencies

**What was asked.** Replace run 93's four-corner-module ansatz with the true 10 + 4 + 4
grammar revealed by n = 18: a C2 perimeter of 10 axis squares, 4 edge-gap tilted squares and
a 4-square pinwheel at the Q(√7) word; extract the tight contact topology from the census row
so every wall and pair tangency is declared; solve the coupled tangencies exactly in Q(√7),
verify the 18-square sentence at `L = 7/2 + ½√7` with clearance 0 through the exact gate, and
register the certified Ring cell; then test the same grammar at the next integer-k Q(√7) row
(n = 151, k = 5) or record the exact obstruction.

**The topology, extracted.** The row is 4 corner squares at `(±a, ±a)` (`a = k + c`), a
3-square run up the left wall, a run down the right wall, one square inward on each horizontal
wall — 10 axis squares, **14 flush wall faces** (`4k + 10` in general) — plus **4 gap squares**
each wedged across a wall gap by two contacts, plus **4 pinwheel squares** (two `v`-steps from
each gap square, closing on the *opposite* gap square). The gaps are derived: vertical
`2c − 1` = 0.8229, horizontal `2c + 2k − 2` = 1.8229 at k = 1.

**The solve.** A tilted square's own axes are `u = (c, s)`, `v = (−s, c)`, so a tilted–axis
tangency on `u` is `|(q − p)·u| = 1/2 + (|c| + |s|)/2` and a tilted–tilted one is
`|(q − p)·v| = 1`. Two equations on the orthogonal pair fix a point: `p5` from the right wall's
run end and the bottom-right corner, `p6 = p5 + v`, `p7` and `p8` each from one chain step and
one pinwheel contact on `−p5`; the other four are the C2 images. Exact, denominators 16:
`p5 = (9/16 + 3/16√7, −19/16 + 1/16√7)`, `p6 = (13/16 − 1/16√7, −15/16 + 5/16√7)`,
`p7 = (21/16 − 7/16√7, −1/16 + 5/16√7)`, `p8 = (25/16 − 11/16√7, 3/16 + 9/16√7)`.

**The certificate.** 22 declared tangencies, every one an exact contact under the gate's own
strict reading (`max_axis slack == 0`); the gate then certifies **N = 18, `L = 7/2 + ½√7`,
clearance 0, 26 contacts, 0 violations** — the 22 declared plus 4 that follow (the bottom and
top wall squares against the opposite chain end, and the two inner diagonals `p6/−p7`,
`−p6/p7`). The `Ring k=1` cell is registered: spatial **47/47 certified, 0 refused**, four
witnesses. The constructed sentence reproduces the delivered n = 18 pose to **1.8e-9** — the
scale of the CSV's own 1e-9 shims — so **n = 18 is now constructed from grammar**, and run 93's
"0.03–0.07 of slack, a polished decimal packing" was an artifact of reading the corner-module
sentence's distances instead of this one's.

**The generalisation, and the split.** The pinwheel's closure contact has `u`-separation
exactly 1 at every `k`, so the question is its `v`-offset: `2·p5·v + 2 = 5/4 − (4k − 1)/4·√7`,
equal to −0.734313 at `k = 1` (inside the unit — the contact exists) but −3.380065, −6.025816
and −11.317319 at `k = 2, 3, 5`, so the exact closure slack is `−13/4 + (4k − 1)/4·√7`, positive
and growing by √7 per `k`. The family therefore refuses `k ≥ 2` under the declared law
`ring_chain_adrift` — a measured tangency that is not a tangency, not a collision (at `k = 2`
the drifted chain also overlaps the perimeter, and the law fires first). And the census's own
`k = 5` row is not the ring's member even in count: the ring would have `N = 4k + 14 = 34` at
`L = 23/2 + ½√7` — the census's own side — while n = 151 is a 151-square staircase (125 axis
squares in 21 staggered columns at `±(j + c)` and `±(j + 1/2 − s)`, plus 26 tilted, 24 at the
word). The side law generalises across all five Q(√7) rows; the sentence splits at `k = 1`.

**Verification.** `glm_wheels --selftest` **24 controls**, exit 0 (control 24 is the ring:
declared tangencies, contacts, wall faces, the 1.8e-9 census agreement, the `k = 2, 3, 5`
refusals with their exact slack; control 23 now points at it); spin spatial **47/47**, sequences
6/7, lattice 24/28; float audit **207 functions, 0 offenders**; `grammar_induction --selftest`
3/3; `qsqrt2 --selftest` 11/11; `field_triage --selftest` 4/4; `record_guard.py` OK. No row
changed.

Entries `57-THE-RING-SOLVED.md`; records `31`-`57`.


## Run 95 — the staircase, and the line between a refusal and a collision

**Two questions from run 94, both answered by measurement.** (1) The Ring's `k >= 2` refusal is
*structural*: at `k = 3, 4, 5` the drifted sentence still passes the exact gate at clearance 0
with 0 violations and fails only its declared tangencies — 8 of the 22, four of them the
pinwheel closure, with exact slack `-13/4 + (4k - 1)/4 Sqrt7` — while only at `k = 2` is the
drift large enough to *collide* as well (3 violations, clearance `-21/4 + 7/4 Sqrt7` ~= -0.620).
Control 24 now records the gate verdict alongside the closure slack for `k = 2, 3, 4, 5`; doc 57
section 5 carries the table. Refusal and collision are different events and are no longer
reported as one.

**(2) n = 151 is a multi-layer staircase, and its axis layer is grammar.** Every axis coordinate
is `m +- c`, so the 125 axis squares sit on two lattices offset by `2c`: block `A`
`(a - c, b + c)` for `a < b` (55 squares), block `B` `(a + c, b - c)` for `a >= b` (66), plus
four corner caps — `125 = 55 + 66 + 4 = 4k^2 + 4k + 5` at `k = 5`, at `L = 2k + 1 + 2c`, the
family's one side law. The blocks never touch (a block-A/block-B pair would need an integer
shift of `1 +- 2c`), so the diagonal seam is real, and the 24 tilted squares fill it as a
two-layer brick wall: in the word frame `u = (c, s)`, `v = (-s, c)` the bricks have consecutive
integer `u = u_0 + j` in twelve columns, and each is tangent **along its own `v`** to
`B(a, a)` or `A(a, a + 1)`, walking `a = -k .. k - 2` with the column repeated when
`a % 3 == 0` — the labels at `k = 5` are `[-5, -4, -3, -3, -2, -1, 0, 0, 1, 2, 3, 3]`. The two
bricks of a column are `2c(c + s) - (1 + s)` apart, so they close edge-to-edge iff `c - s = 1/2`:
the wall is the Q(sqrt 7) word's own, and control 5 refuses the 45-degree word by
`staircase_layer_gap`.

**The certificate.** `staircase_field` -> `p_staircase(5)` gates **N = 149 at
`L = 23/2 + 1/2 Sqrt7` with clearance exactly 0, 449 contacts, 0 violations**, all 24
declarations exact; the `Staircase k=5` cell is registered and the spatial wheel is **48/48
certified**. The 149 centres reproduce the delivered n = 151 row to **9.0e-8**.

**Where 151 stops, exactly.** The wall's thirteenth column (`a = k - 1`) pinches the top-right
cap by `-163/128 + 61/128 Sqrt7 = -0.012572`, one violation; the slide that removes that pinch
by construction immediately produces another at `-0.005557`, so the wall is jammed and no gauge
admits 26 bricks. That is why the table rotates the last two squares: their word is
0.6147618 rad, whose `cos`/`sin` recovered in Q(sqrt 7) at heights <= 4096 has norm
`868927/1024 - 656073/2048 Sqrt7 != 1` and is not Pythagorean (no `t` with denominator
<= 1024). A field-general Q(sqrt 7) staircase therefore constructs **149 of the 151**, with the
family law `N(k) = 4k^2 + 4k + 5 + 2|columns(k)|` (149 at `k = 5`; 15, 37, 67, 103, 149, 203
at `k = 1..6`); the 151st pair is an exact refusal, not a failure. At n = 149 the family's table
side is `12 + 1/2 Sqrt2`, so it does not beat the table.

**The pocket, decided exactly.** `staircase_cage` covers the L-box with exact `Quad` boxes in the
candidate word's own frame, and prunes a box only where that is provable -- wholly inside one
square's no-fit octagon, or wholly outside the box --
so the surviving cover is a sound superset of the feasible centres. For the census word against
the 149 squares the cover is 24 boxes at side 1/8 spanning `5/8` in `u` and `3/4` in `v`, with a
witness centre `(97/16, 31/16)`; both extents below 1 mean at most one centre fits, so the
pocket's word-aligned capacity is exactly **1**. The square it holds is the cap brick -- the last
column's `A` brick repeated one column out, `u + 12`, `v = (17 + Sqrt7)/8`, exactly tangent along
`u` to its twin -- and the exact gate certifies **N = 150 at the same side, clearance 0, 451
contacts**. With that brick in place the cage is empty even for the census word: the pocket is
closed.

**The word spin.** The layers are `v_A - v_B = 2c(c + s) - (1 + s)` apart, so the residual is
`2c(c+s) - (1+s) - 1 = s(2(c - s) - 1)`: zero iff `s = 0` (the degenerate axis word) or
`c - s = 1/2`, which pins the census word alone. Spun over **62 declared unit words** -- the 45
degree word in Q(sqrt 2), Slope 2:1 in Q(sqrt 5), the Seventh and every other unit word of
Q(sqrt 7) at height <= 8, every Pythagorean word with denominator <= 13 -- the constructor is
actually run and closes at exactly one, refusing the rest by `staircase_layer_gap` with their own
exact residuals (45: `-1/2 Sqrt2`; Slope 2:1: `2/5 - 1/5 Sqrt5`; Seventh: `-15/8 + 3/8 Sqrt7`;
t = 1/2: `-28/25`; t = 1/3: `-9/25`; t = 1/5: `5/169`).

**The second word.** Run against the 150-square sentence, the same cage is empty for **78 of 78
field-compatible words** -- all 22 unit words of Q(sqrt 7) at height <= 8 and every Pythagorean
word with denominator <= 13, embedded in Q(sqrt 7) so the test stays in one field -- so no second
exact word places the 151st square at this side: the pocket is closed for `Q(sqrt 7) union
Q_Pyth`, and the table's escape is a rotation in neither. The sweep is **66 cages, not 78** -- a
quarter turn `(c, s) -> (-s, c)` leaves the square unchanged, so one representative per rotation
class decides every word in it. A `k = 1..9` calibration spin at the
family word never beats a delivered row either (`k = 1` behind by 0.8229, `k = 3` and `k = 5` by
0.1158, `k = 6` by 0.0447; `k = 2, 4, 7, 8, 9` uncalibrated), every comparison exact in
`Decimal`. No row changed.

**The mixed sentence, and the honest answer on 151.** The census's own row spends two squares on
a **rotation of 0.614761828896 rad**, exactly `19211307153/31250000000`. The angle is rational but
its cosine is not a field element, so this is *measured* where it cannot be caged. Rounded **up**
at `1e-25` into Q(sqrt 7) (`cos^2 + sin^2 >= 1`, the caged square is the table's square grown by
`1e-25`), the rotation finds a placement against the exact 149 and the exact gate certifies
**N = 150 at `23/2 + 1/2 Sqrt7`, clearance 0, 449 contacts** (449 is the mixed sentence's own
gate; the census cap-brick 150 is 451). **The 151st is excluded exactly.** Two unit
squares of one word overlap unless their centres differ by at least 1 along one of that word's
axes, so the pair is settled axis by axis. Along `u` the `(2, 1)` rectangle's cage is **empty**
(run 96 corrects this: that cage rules out only the *tangent* pair, exactly 1 apart, so the `u`
half rests instead on the single cage's cover extent `3/4 < 1` and the free `u` span `0.447289`).
Along `v` the new `staircase_chords` proof closes it: at a fixed `u` the sentence forbids a union
of exact `Quad` intervals (a square covers `(u, v)` iff all four of its axis tests fail, so its
forbidden set is the intersection of four linear intervals), the free set is the exact complement,
and each block of `u` shrinks every forbidden interval to the part common to the whole block --
under-approximating the forbidden set, so the free set is over-approximated and the bound is
sound. Over 16 blocks of the cage's own window all 16 close, largest single free chord
`0.558490` (run 96 corrects the *read*: the quantity that proves the pair is the **union** of the
blocks' free sets, `0.624681 < 1` -- a per-block chord alone would miss a pair whose two `u` values
fall in different blocks) < 1:
no two squares of the table's rotation are 1 apart along either axis, in exact `Q(sqrt 7)`
arithmetic, no scan, no tolerance. With the cap brick in place the cage is empty for the rotation
too, and with the **census** word the `(1, 2)` rectangle cage is empty -- the same fact as
capacity 1 read another way. So **151 is refused at the census side by proof**; what is certified
is the 150.  The box cage alone cannot settle this pair (its per-axis test is weaker than
pointwise coverage, so the `(1, 2)` cover degenerates), and the instrument had two honest repairs
on the way: the candidate-cell bucket radius is now read off the rows (`ceil` of the largest
separation need) instead of being hard-coded to 2 -- which is only sound for a unit square -- and
the rational pre-filter run 95 added was *skipping* the cells that kill a box, so it is gone (the
cage is tight again; the 66-class sweep costs 21.6 s). The delivered row
reaches 151 by tolerance instead -- replaying its own two rotation squares against the exact 149
gives worst pair slack `-2.365e-9` (an odd square against a wall brick), an overlap, so the
table's n = 151 is a 12-decimal pose held at ~`1e-9` and not a packing at the exact side.

**The suite's cost.** The cage work run 95 added is paid back where it was spent: the 78-word
second-word sweep now runs **66 rotation classes** (a quarter turn cannot change a cage's answer),
and the bucket radius is read off the rows instead of assumed. The sweep goes from **40.0 s to
21.6 s** with every verdict unchanged
(149 cage capacity 1, cover `5/8` x `3/4`; 66 of 66 empty; cap brick still `du = 1` tangent), and
the whole suite is **27 controls, exit 0** in about two minutes. The remaining time is not the
cage: the single largest item is `p_staircase(5)`'s independent 70-digit witness (7.7 s).

**Verification.** `glm_wheels --selftest` **27 controls**, exit 0 (control 25 is the staircase:
the 55 + 66 + 4 split, the twelve-column walk and its repeats, all 24 tangencies exact, the
149-square certificate, the 9.0e-8 census agreement, the exact pinch, the odd word's
non-membership in the field, the exact cage with capacity 1, the certified 150, the cap brick's
`du = 1` tangency and the empty cage against the 150; control 26 is the 62-word spin, the
78-word second-word test in 66 rotation-class cages, and control 27 the mixed word: the table's
`19211307153/31250000000` rad closing a certified 150, excluding the 151st exactly (the `u` cover extent `3/4`
and free `u` span `0.447289`, and the chord proof capping every free `v`-chord below 1 over 16
blocks),
the census word's rectangle cage empty, and the delivered pair's measured `-2.365e-9` overlap); spin spatial **48/48**, sequences 6/7, lattice 24/28; float audit
green (241 functions, 0 offenders); `grammar_induction --selftest` 3/3; `qsqrt2 --selftest`
11/11; `field_triage --selftest` 4/4; `record_guard.py` OK.

Entries `58-THE-STAIRCASE.md`; records `31`-`58`.

## Run 96 — the honest score, the window above 1000, and the 7-rung bridge

**Three questions, no row moved.** (1) Does any exact sentence on `glm_wheels.py` beat the
delivered row at the same `N`? (2) What do the same families emit above `n = 1000`, where the
table and the float tables stop? (3) Where does that put us on the seven-rung ladder, and what is
the next grammatical move? A fourth item came first and is a repair.

**The chord check, made sound and made uniform.** Run 95's `staircase_chords` reported the largest
*single block's* free chord (`0.558490`), but a `V`-separation is `dv >= 1` whatever `du` is, and
the table's rotation has a `5/4`-wide `v`-window — so a pair whose two `u` values fall in
different blocks was not covered. The instrument now accumulates every closed block's free
intervals and decides on their **union**: the span is `0.624681 < 1`, the sound quantity, and
control 27 asserts the union exceeds the largest block's chord. `--chord-spin` then runs the same
two instruments (`staircase_cage` and the new `staircase_pair_span`, which answers both axes by a
quarter turn) over the **census word and all 66 rotation classes** — the 78 field-compatible words:
**66 of 66 non-empty cages** (every class places one square against the exact 149), 36 with
capacity exactly 1 and 30 decided by the chord span, and **66 of 66 `no-pair`** — free spans
`0.428760 … 0.780198` (`u`) and `0.440099 … 0.822876` (`v`), none reaching 1. It is 2 m 02 s on
its own and is deliberately **not** in the selftest; the suite is unchanged in cost at
**1 m 51.9 s** after the `u`-axis repair (control 27 now builds the pair span, +2 s). Doc 58 section 7.2
carries the table.

**The honest score: 0 of 364.** `scripts/family_spin.py --calibrate` spins Ridge, Strip, Diamond,
Ring and Staircase over Q(sqrt 2), Q(sqrt 5), Q(sqrt 7) and three rational-t words. Each member's
side is exact `Quad`; the delivered side is recomputed from the 12-dp pose as exact rational input
at 70 digits, so every gap is decisive, and a gap under `1e-6` is called *parity* because the
table's own pose tolerance is ~2e-9. Result: **364 members share a count with a delivered row,
0 beat it, 6 are at parity, 358 are behind.** The six parity rows are the atoms the grammar was
built from — `n = 5` (45-degree ridge = Strip `S(1,1)`), the diamonds `n = 10, 19, 40`, the ring
`n = 18` — each `+1.26e-9 … +1.71e-9`, i.e. agreeing with the table to the table's own polish and
not beating it. Every other member is behind and the shortfall **grows**: closest is the Seventh at
`n = 5` by `0.001391`; at `N = 901` the 45-degree rung is `30.70711` against `30.52082`, row
scores `+0.023002` against `+0.016796`, so splicing it in would **raise** the total by `0.0062`
(`N = 903`: `+0.0528`). The algebra says why: every family is single-word, `L = 2k + w` with
`w = m min(1/(c+s), c+s)` — minimised at `x = c + s = 1`, the 45-degree word, `w = 1/2 Sqrt2` —
while the delivered rows at `N = 4k^2 + 1` sit at `2k + O(1/k)`. **The table is not reproducible by
this alphabet**: it explains the *sides* of 576 of 1000 rows (447 grid, 99 Q(sqrt 2) pose, 18
Q(sqrt 2) side, 5 Q(sqrt 7) side, 3 Q(sqrt 5) side, 4 rational-t) and constructs 6 of them as
sentences; the other **424 rows have no field class at all**.

**The window above 1000, exact and zero-drift.** `--beyond` gates the rungs whose counts the table
does not have. Strip / 45-degree ridge at `N = 4k^2 + m`, `L = 2k + m Sqrt2/2`: `N = 1025`
`L = 32 + 1/2 Sqrt2` (void `-1/2 + 32 Sqrt2` = 44.754834, **3724 contacts**), `N = 1026`, `1027`;
and at `k = 22`, `N = 1937` `L = 44 + 1/2 Sqrt2` (void `-1/2 + 44 Sqrt2`, **7228 contacts**),
`1938`, `1939` — `gate_L == L` on every rung, depth `L/sqrt N - 1` = 0.015808 … 0.064733, and at
`N = 1025` the side is **0.292893 inside the grid's 33**. The same rung over all seven words
(`k = 16`, `N = 1025`, 3724 contacts each) orders them exactly as the field predicts — `32 + 1/2
Sqrt2` (45), `38 - 2 Sqrt7` (Seventh), `229/7` (t = 1/2 and 1/3, the same mirror square), `32 +
1/3 Sqrt5` (Slope), `32 + 2/7 Sqrt7` (census), `557/17` (t = 1/5) — because `w = min(x, 1/x)` is
minimised at `x = 1`. **The staircase does not scale**: its wall's column count grows at ~`8k/3`
while the box's `u`-window grows at `2k`, so from `k = 6` the bricks cut into the frame — 38
violations at `k = 6` (worst clearance `-0.812193`), 56 at `k = 7`, 297 at `k = 21` (`N = 1963`,
bbox `62.71` against the law's `44.82`), and **no gauge** among 25 slides `u0 + i/4` at `k = 6`
gates. The staircase is a reading of the census's one row, not a family; its side law is `k = 5`
only. Ring `k = 2, 3` refuse by `ring_chain_adrift` and the diamond atoms stay at `n <= 40`, so
above 1000 the honest rungs are the ridge's. No row claimed.

**The bridge.** Doc 59 maps the instruments onto the seven rungs: rung 1 (Golay substrate) holds the
leech 24-pocket address and its retraction — after the run-33 audit its only signal *is* the
rotation flag; rung 2 (integer) holds the 447 axis rows at `ceil sqrt n` and cannot even see the 553
beating rows; rung 3 (rational/algebraic) is home — Q(sqrt 2), Q(sqrt 5), Q(sqrt 7), rational-t,
the gate, the cage, the chord union, and the lossless ceiling; rung 4 (scan) is the delivered table
itself, whose `2e-9` pose is why the mixed 151 overlaps by `-2.365e-9`; rung 5 (topology) classifies
our contact graphs but cannot propose one; rung 6 (Griess/Conway) is **empty** — a Golay shadow is
not a `Co_0` label on an exact carrier; rung 7 (certificate) is our strongest, and its refusals
carry the discipline of `climb_principled`. The blindnesses are named with numbers: the 0.614761828896
rad word is in no field at height <= 4096 and is not Pythagorean (so "151 is impossible" is a
statement about `Q(sqrt 7) union Q_Pyth`, plus a measured `-2.365e-9` overlap — not about squares);
one word per family is why `w >= 1/2 Sqrt2` and why the table's `2k + O(1/k)` is unreachable; and
424 of 1000 rows are outside any field. The next move is one production, not a search: **a second
word in the same sentence**, declared by a *mixed* tangency, so the closure is a polynomial
identity in both words — the ring's `2 p5.v + 2 = 5/4 - (4k - 1)/4 Sqrt7` is the template, and the
falsifier is whether any word pair closes below `2k + w` at `k <= 8` (decidable with the cage and
the chord union already here).

**Verification.** `glm_wheels.py --selftest` **27 controls, exit 0, 1 m 51.9 s** (the `u`-axis repair added ~2 s, no inflation);
`--audit` green; `--chord-spin` 66/66 `no-pair`; `family_spin.py --calibrate` 364/0/6/358 and
`--beyond strip|words|stair` all gated with zero drift; spin spatial **48/48**, sequences 6/7,
lattice 24/28; `grammar_induction --selftest` 3/3; `qsqrt2 --selftest` 11/11; `field_triage
--selftest` 4/4; `record_guard.py` OK. No row changed and no score is claimed.

**Two repairs after the fact, both recorded here rather than quietly edited in.** (i) The `u` half of
the 151 exclusion does not rest on the `(2, 1)` rectangle cage — that cage asks only whether the
*tangent* pair (centres exactly 1 apart) fits, and a pair further apart is legal and invisible to it.
Control 27 now uses the single cage's **cover extent** `3/4 < 1` (asserted exactly) and the free `u`
span `0.447289` from `staircase_pair_span`, with the `v` half unchanged (the 16-block union,
`0.624681`); doc 58 §7.1 says the same. (ii) The calibration's sides are the family law, so
`family_spin.py --gate-ks 1,2,3,15` now runs the exact gate on 84 ridge members — every word ×
`m = 1,2,3` at `k = 1,2,3` and the whole `k = 15` column (`N = 901..903`) — all `ok` at clearance
exactly 0 with `gate_L == L`; with the ring `k = 1` and the three diamond atoms that is **88 of the
364** sides, so the column the score argument quotes is certified feasible as well as exact. At
`k = 15, m = 1` every word reads **3252 contacts**. Doc 59 §1 records which `k` the sides were gated
at. Selftest still 27 controls; audit still 0 offenders.

Entries `58-THE-STAIRCASE.md` (section 7.2), `59-ESCALATION-LADDER-BRIDGE.md`; records `31`-`59`.

## Run 97 — the two-word seam: one word in a block, and why a mixed pair cannot break the floor

**Two questions, no row moved.** (1) What do the delivered rows that sit below `2k + ½√2` actually
do with their rotations? (2) Can a field-exact **two-word coupled tangency** be built, and does any
such sentence break that floor or beat the table at the same count? Root `WHITEBOARD.md` and
`submission.csv` are untouched.

**The rows below the floor, measured.** A new `family_spin.py --motifs` (read-only over
`submission.csv`, ledger `workspace/push/row_motifs.json`) walks the 15 rows at the ridge's own
counts `N = 4k² + 1`: fourteen sit strictly below `2k + ½√2` (`N = 5` sits exactly on it), and from
`k = 4` every one of them uses exactly two rotation classes, axis and 45°. The tilted count at
`N = 677, 785, 901` is `289 = 17²`, and projecting those 289 centres onto the 45° word's own axes
gives **17 distinct `u` levels and 17 distinct `v` levels with every gap exactly `1.000000`** — a
17×17 lattice of *one* word, at the *same* `u` and `v` ranges in all three rows. That is a
homometric **block**, not a coupling: it is the object that carries those rows below the floor.

**The rows that really carry two words are mirror pairs.** 443 rows carry two or more tilted
classes; 363 of them give every square its own angle (the relaxed rung) and are excluded from the
pairing. Of the rest, 26 rows have exactly two classes, 9 of those are **mirror pairs**
`(θ, 90° − θ)`, and 56 have a mixed tangency tight to `|residual| < 1e-6` — a real tangency at the
table's `1e-9` polish. 52 are below the floor. `n = 198` is the cleanest: `36.870° / 53.130°` are
the 3-4-5 words `(4/5, 3/5)` and `(3/5, 4/5)`, and their exact mixed tangency is **`28/25`**, not
`1`. `n = 37` does the same with three words, `45° ± 2.913°`.

**The two facts that decide the builder's reach.** (i) The floor is a *per-square* price: a unit
square at word `θ` in the ridge's cross is tangent to the blocks at `φ(θ) = min(x, 1/x)`,
`x = |c| + |s|`, and for a unit word `x ∈ [1, √2]`, so `φ ≥ ½√2` with equality exactly at 45° —
every square in a mixed bar pays it separately (`seam_floor`, control 28 asserts `φ·x = 1` and the
equality). (ii) A mixed tangency is never cheaper than a same-word one: two different words need
`(1 + |cos Δ| + |sin Δ|)/2 > 1` along the first's own axis, exactly `1` only for the same word
(`two_word_need`; the 3-4-5 pair pays `28/25`). So two words cannot cancel a seam, only add one.

**The builder and the spin.** `glm_wheels.py` now carries a field-exact two-word seam: word 1 at
the seam centre (the ridge's own slot), word 2 at the mixed need from it along word 1's `-v` (a
vertex-to-edge tangency across two words, which no single-word sentence can express), and the width
from `two_word_gauge` — a **closed form**, because the blocks ride outward with `w` while the bar
rides outward with `w/2`, so every block-slot separation is monotone in `w` and the minimal width is
a maximum of exact linear roots (no scan, no tolerance). `two_word_pair` gates it and records `L`,
`N`, void, contacts, seam and both floors; control 28 asserts the gauge equals the gate's own
`L − 2k`. `--two-word-spin`: 36 distinct word pairs inside their own field (`Q(√2)`: 45°, `t =
1/2, 1/3, 1/5`, `pyth-3/4`, `pyth-5/12`; `Q(√7)`: Seventh, census, five rationals) × `k = 1..8` =
**288 sentences, all gated at clearance 0**, seam **constant in `k`** per pair over
`2.019084…2.533523`, margin over the floor `1.311977…1.826416`, every mixed need
`1.002088…1.204980`: **0 below `2k + ½√2`, 0 beating the delivered row** at the same
`N = 4k² + 2`. At the same count the single-word `m = 2` ridge sits at `2k + √2 = 2k + 1.414214`,
so the coupled sentences are `0.605…1.119` *wider*: coupling is not a route to the floor.

**Verdict, and the production that would move.** In the cross topology the refusal is structural
and now has its mechanism: per-square floor plus a mixed need above `1`. The table's actual escape
is the block (§ above), which is not a seam at all; that is the next production, with a falsifier —
build a 45° block of `s²` squares with axis fill in the four corner triangles and ask whether the
exact gate reproduces `L = 2k + 0.520815` at `N = 4k² + 1` for `k = 13, 14, 15` (and
`2k + 0.535534` for `k ≤ 12`). Not claimed: that no two-word sentence of *any* topology can beat
the floor — the table's own two-word rows are corner wedges at small `N`, where the seam is not a
cross, and the run says so.

**Verification.** `glm_wheels.py --selftest` **28 controls, exit 0, 1 m 50.7 s** (control 28 is the
new one, ~2 s); `--audit` **253 functions, 0 offenders**; `--two-word-spin` 288/288 gated, 1 m 43 s;
`family_spin.py --motifs` 15 ridge-count rows + 443 two-word rows, 32 s; `--calibrate`, `--gate-ks
1,2,3,15`, `--beyond strip|words|stair`, `grammar_induction.py`, `qsqrt2.py`, `field_triage.py` and
`record_guard.py` all unchanged and green. No row changed, no score claimed.

Entries `60-TWO-WORD.md`; records `31`–`60`.

## Run 98 in detail — the 45° block: a certified floor-breaker that is not a record

User request: build the production doc 60 named — `s²` squares at the 45° word with axis fill in
the four corner triangles, `T(k, s)` and `N(k, s) = s² + 4T` and the closed-form contact side
`L(k, s)` from exact `Q(√2)` roots — gate it over small `(k, s)`, at `(k = 4, s = 5, N = 65)` and at
`(k = 13, s = 17, N = 677)`, and test honestly whether `L − 2k` breaks the single-word floor `½√2`
and matches or beats the delivered slacks `0.535534` / `0.520815`; leave `submission.csv` and root
`WHITEBOARD.md` alone unless the score can actually move.

**The production.** `block45_count(s, k)` is integer arithmetic: `T = k(k+1)/2` per corner (the
staircase sum), `N = s² + 2k(k+1)`. The block's faces are `x + y = L ∓ s/√2`, `y − x = ±s/√2`, so
each corner triangle has legs `t = L − s/√2`, and `t = k + 1` makes the staircase square at
`(k−1, 0)` meet the face at its corner — tangency. `block45_side` is then the exact contact
`L = max(s/√2 + k + 1, 2s/√2)`, in `Quad(2)`, no root-finding: the separation roots *are* the law.
`_block45_sentence` builds `s²` tilted squares plus four staircases; `p_block45` gates it and
records `L`, `N`, void, contacts, block/corner counts and the gap to the floor; `block45_spin`
sweeps and writes `workspace/push/block45_spin.json`.

**Two corrections the gate forced on the algebra.** (1) The first sweep wrote `L = s/√2 + k + 1`
only, and 84 of 198 rows came back `block45_side_mismatch` — precisely the rows with `t < s/√2`,
where the block's own diagonal `2s/√2` sets the box. The law is now the maximum, and the refusal
that caught it is kept. (2) `p_block45` raised `KeyError` on a count the table does not carry
(1237); it now records `table_side = None` instead. Neither is a silent patch: both are refusals
that fired.

**Feasibility is one inequality, derived and then checked against the gate.** The staircases at
the two ends of a wall interpenetrate exactly when `L < 2k`, i.e. `k > s/√2 + 1`, so
`feasible ⟺ k ≤ ⌊s/√2⌋ + 1`. The sweep agrees on **all 121 rows** (70 gated, 51 refused by
`block45_corner_collision`), and the refusal counts grow with the overshoot: at `s = 17`, `k = 14`
collides on 4 pairs, `k = 16` on 24, `k = 17` on 40.

**The floor, broken.** In the contact branch `L − 2k = s/√2 + 1 − k`, minimised over the feasible
window at exactly `frac(s/√2)`. Eight certified rows sit below `2k + ½√2`, the smallest excess
**0.020815** at `(k = 13, s = 17)`: `N = 653`, `L = 26.020815280171307…`, 2308 exact contacts,
clearance 0, 439 tilted + 214 axis. Then 0.071068 at `(10, 8)`, 0.121320 at `(3, 3)`, 0.242641 at
`(6, 5)`, 0.363961 at `(9, 7)`, 0.414214 at `(2, 2)`, 0.535534 at `(5, 4)`, 0.656854 at `(8, 6)`.
The single-word floor is the ridge's floor, not a law of squares — that much is settled, exactly.

**The asked points.** `(k = 4, s = 5)`: `T = 10`, `N = 65`, `L = 5/√2 + 5 = 8.5355339059…`, 172
contacts, and the delivered side at `n = 65` minus this one is **`0E−69`** — the table's own
`5 + 5/2√2`. Its slack `0.535534` *is* `5/√2 − 3`. Parity, and the strongest confirmation
available: the production reproduces a delivered row's side from a count law and a contact root.
`(k = 13, s = 17, N = 677)`: **count refusal**. `N(13, 17) = 653`; `677` would need `T = 97` per
corner, and `T` is triangular (91 at `k = 13`, 105 at `k = 14`). `677` is not in the family for
*any* `(s, k)` with `s ≤ 30, k ≤ 25` (control 29 asserts the search). The delivered row at 677 is
also not this production in its own anatomy: `388 = 4 × 97` axis squares, and its corners have
`t = 14.5` — half a unit of slack, which is how six extra squares per corner fit. Same story at
`n = 901`: its count **is** the family's `(17, 17)` (`153 = T(17,17)` per corner), but `k = 17`
is infeasible at `s = 17` (40 collisions; the wall-anchored fill needs `L ≥ 34`, the family has
30.020815) and the delivered row sits half a unit wider at `30.520815`, `t = 18.5`.

**Scale, and why no row moves.** Above 1000 the family gates exactly: `(25, 17)` is `N = 1237` at
`L = 35.677670…` with 4532 contacts, `(35, 24)` is `N = 2425` at `49.748737…` with 9112, `(50, 35)`
is `N = 5020` at `71.355339…` with 19230 — all clearance 0. They beat `⌈√N⌉` (1237 and 2425 sit
just above a perfect square), but `L/√N → 1` along the minimal-excess ladder: 1.018273 at 653,
1.013752 at 1309, 1.006879 at 5164, 1.003490 at 20025, 1.001765 at 79248, 1.000888 at 315300.
`N ≈ 2s²`, `L ≈ s√2 = √N`: the block **is** the grid in the limit, one `O(1)` above it, and the
`frac(s/√2)` excess is bought by matching the grid's diagonal rather than beating it. So the
session's headline question answers itself: the grammar certifies `L < 2k + ½√2` at every scale,
and those inequalities are not records — **0 of 70 gated rows beats a delivered row**, at any
count. Seven counts are exact parity (`N = 5, 40, 65, 89, 124, 148, 233`), i.e. the table's rows
there *are* this production; nothing is improved.

**Next.** The block's gap is its corner fill's integrality: a contact staircase needs integer legs
and the table's low-slack rows use half-integer ones. That is the next production, with its
falsifier named in doc 61 §8: the `t ∈ ℤ + ½` corner fill, asked whether any `(s, k)` reaches
`L = 2k + 0.520815` at `N = 677, 785, 901` with clearance 0.

**Verification.** `glm_wheels.py --selftest` **29 controls, exit 0, 2 m 0 s** (control 29 is new: the count
law over `s, k ≤ 8`, both side branches, the two showcase sentences with their delivered-row
parities, the `k = 14` collision, and the absence of `N = 677` in the family); `--audit` **258
functions, 0 offenders**; `--block-spin` 121 rows (70 gated / 51 refused), 8 below the floor, 0
beating the table, `2 m 16 s`, ledger `workspace/push/block45_spin.json`; the feasibility and
minimal-excess laws re-checked against the ledger (121/121, 8/8); bare run exit 0;
`record_guard.py` OK; `family_spin.py --calibrate/--gate-ks/--beyond`, `grammar_induction.py`,
`qsqrt2.py`, `field_triage.py` unchanged and green; README/STATUS footers byte-identical.
**No row changed, no score claimed, `submission.csv` and root `WHITEBOARD.md` untouched.**

Entries `61-BLOCK45.md`; records `31`–`61`.

## Run 99 in detail — the half-integer corner fill: the side is exact, the fill is not

User request: build the `t ∈ ℤ + ½` corner fill doc 61 §8 named — half-integer-shifted axis
corner triangles on the 45° block, with the exact count `T(s, k)`, the total `N = s² + 4T` and
the closed-form contact side `L(s, k)` from `Q(√2)` separation roots — gate it over small
`(s, k)` and at `N = 677, 785, 901` (`k = 13, 14, 15`, `s = 17`); report honestly whether any
certified sentence breaks `L < 2k + ½√2` and reaches `L − 2k ≈ 0.520815` at those counts; emit
`N > 1000` rows only if it certifies; tag the result with rung-3/rung-7 provenance; and leave
`submission.csv` and root `WHITEBOARD.md` alone unless the score can move.

**The production.** `block45half_count(s, k)` is integer arithmetic: a unit axis square
`[i, i+1] × [j, j+1]` sits in the corner triangle `x, y ≥ 0`, `x + y ≤ t` iff its far corner
does, `i + j + 2 ≤ t`, so `t = k + ½` gives `i + j ≤ k − 2` and `T = k(k−1)/2` per corner,
`N = s² + 2k(k−1)`. `block45half_side` is the exact `L = max(s/√2 + k + ½, s√2)` in `Q(√2)`;
`_block45half_sentence` builds `s²` tilted squares plus four `m = k−2` staircases;
`p_block45half` gates it and records `L`, `N`, void, contacts, the floor gap and the dominance
law; `block45half_spin` sweeps and `block45half_calibrate` reads the three delivered sides.

**The arithmetic corrected doc 61 §8.** A triangle's unit-square count is a function of `⌊t⌋`
only: `T(k + ½) = T(k) = k(k−1)/2`, and every staircase square is `1/(2√2) = 0.353553` clear of
the block's face. So the half unit admits **no extra triangle square** — doc 61's reading of
`t = 14.5` and "six extra squares per corner" as half-unit staircase squares is wrong, and the
delivered 677 row's `388 = 4 × 97` axis squares are not four corner staircases. What the half
unit buys is slack, and the exact consequence is a dominance law.

**Dominance.** The half member at `k` and run 98's integer contact member at `k − 1` have the
same count (`s² + 2k(k−1) = s² + 2(k−1)k`) and sides `max(h + k + ½, 2h)` against `max(h + k, 2h)`,
`h = s/√2`, so `L_int ≤ L_half ≤ L_int + ½`: exactly `½` in the fill branch, `0` when the block's
own diagonal sets both (`(5, 2)`: both `5√2`), and `k + ½ − h` in between (`(3, 2)`:
`5/2 − 3/2√2 = 0.378680`). All three are asserted in control 30. The law is measurable against
the table: at the seven counts run 98 reproduces exactly (`N = 5, 40, 65, 89, 124, 148, 233`)
the half member's side is exactly `½` behind the delivered side — `−0.500000` at six of them and
`−0.4999999999999` at `N = 89`, which is the delivered pose's own `1e-9`. So `t ∈ ℤ + ½` can
never be the better sentence.

**Feasibility is one inequality, derived and then checked.** Corner 0's staircase reaches
`x = k − 1`, corner 1's starts at `L − (k−1)`, in the same row band, so they meet exactly when
`L < 2k − 2`. The sweep agrees on **all 124 rows** (76 gated, 48 refused by
`block45half_corner_collision`, 0 law mismatches); at `s = 17` the window is `k ≤ 14` and the
colliding pairs grow `4, 12, 24, 40` at `k = 15, 16, 17, 18` — the same counts run 98 measured,
because the two families' staircases are the same objects.

**The floor, honestly.** The family's excess `L − 2k = s/√2 + ½ − k` crosses zero inside the
window: the closest certified value above is **`+0.035534`** at `(5, 4)` (`N = 49`) and the
closest below **`−0.085786`** at `(2, 2)` (`N = 8`), so **29 of 76 gated rows sit below
`2k + ½√2`** — the inequality is met, at essentially every scale. It is still not a record, and
for a different reason than run 98's: here `k` is the corner parameter, not the ridge's, so a
negative `L − 2k` says the block's half-diagonal is shorter than the staircase index, not that a
packing is tight. The like-for-like comparison is at the same `N`, and there the family is behind
every delivered row it shares a count with: **0 beats, 0 parity, 53 gated rows with a delivered
count**, closest `−0.207107` at `N = 13`, `−0.292893` at `N = 85`, `−0.328427` at `N = 56`,
`−0.449747` at `N = 133`, exactly `−0.5` at the seven parity counts.

**The falsifier, sharper than doc 61 could state it.** The delivered rows' exact lifted sides are
`29/2 + 17/2√2`, `33/2 + 17/2√2`, `37/2 + 17/2√2` — i.e. **exactly** `s/√2 + k + ½` at
`k = 14, 16, 18`. The half-integer *side* law is the delivered side with no tolerance. The count
is the other half of the question, and it does not follow: the corner fill at those sides holds
`N = 653, 769, 901` against the rows' `677, 785, 901`, **short by 24, 16, 0**; only `k = 14` is a
sentence (clearance 0, **2256 contacts**); at `k = 16` (12 pairs) and `k = 18` (40 pairs) the two
staircases on each wall meet. So the delivered 901 row is the half-integer corner fill's count
*and* its side in an arrangement the centred corner fill cannot take — a sharper statement than
doc 61's "the family's count but infeasible". `677` is no count of the family at all; `785` is a
count only at `(5, 20)` (`L = 24.036 < 2k − 2 = 38`) and is refused. The requested `k = 16, 17,
18` rows (`N = 769, 833, 901`) are therefore all refused, not emitted as certificates. Two exact
readings next door: at `N = 709, 769, 833` the delivered rows are grids at `L = 27, 28, 29` and
the half side law sits exactly `0.520815 = 17/√2 − 23/2` above them; at `N = 901` it coincides.

**Above 1000.** The fill gates exactly: `(25, 20)` is `N = 1385` at `L = 41/2 + 25/2√2`
(38.177670), void `−2609/4 + 1025/2√2` (72.534451), **5016 contacts**, `0.177670` outside the
grid's 38. The law rows `(35, 27)` (`N = 2629`, `L = 55/2 + 35/2√2`) and `(50, 37)` (`N = 5164`,
`L = 75/2 + 25√2`) are recorded as law only — `L/√N` 1.025852, 1.019015, 1.013837 — because above
1000 the half family is its integer sibling plus `½` and adds nothing to run 98's ladder.

**The rungs.** Rung 2 is blind to the half: the corner count is a function of `⌊t⌋`, so
`T(k + ½) = T(k)` exactly (`integer_indist_zero_half`). Rung 3 sees it and sees it **as slack**:
in `Q(√2)` the legs differ, `L` moves by `½` while `N` does not, and the delivered sides are
exactly the half-integer legs (`rational_distinguishes_zero_half`, in its packing form). Rung 7
decides: the exact gate at clearance 0 accepts `k = 14` and refuses `k = 16, 18`, so seeing the
half is not certifying it. The Lean anchors are conceptual references only; no Lean build is
attempted.

**Next.** The gap is a count, not a side: `24, 16, 0` squares at the same three sides, which
cannot sit in the corner triangles (legs `14.5` hold at most 91). They are notch/band squares,
and the delivered 677 pose is an off-centre block with two wide bands. The next production is the
**band fill** — the free-region row count under the exact `L1` law `d(a) + d(b) ≥ s/√2` — with
the falsifier `B(17, 14) = 97` per corner (388 total), `B(17, 16) = 124`, `B(17, 18) = 153`, gated
at `k = 16` and `k = 18`.

**Verification.** `glm_wheels.py --selftest` **30 controls, exit 0, 2 m 30 s** (control 30 is new:
the count law over `s, k ≤ 8` including `T_half(s,k) = T_int(s,k−1)`, both side branches, the
three dominance cases, the gated `(17, 14)` with its `½`, the `k = 15`/`k = 18` collisions, the
exact 677 side identity, the 24/16/0 deltas, the feasibility flags, and both count facts);
`--audit` **265 functions, 0 offenders**; `--block-half-spin` 124 rows (76 gated / 48 refused),
29 below the floor, 0 beating, 0 parity, `3 m 18 s`, ledger `workspace/push/block45half_spin.json`
with the three-row calibration (653 gated / 769 and 901 refused, short by 24/16/0);
`--block-half-beyond` gated `N = 1385` plus two law rows, `22 s`, ledger
`workspace/push/block45half_beyond.json`; feasibility and dominance re-checked against the ledger
(124/124, 53/53); bare run exit 0; `record_guard.py` OK; `family_spin.py`,
`grammar_induction.py`, `qsqrt2.py`, `field_triage.py` unchanged and green; README/STATUS footers
byte-identical. **No row changed, no score claimed, `submission.csv` and root `WHITEBOARD.md`
untouched.**

Entries `62-BLOCK45-HALF.md`; records `31`–`62`.

## Run 100 in detail — two composable exact plugins, and the chain between them

User request: prototype and gate-verify two composable, float-free mathematical "GLM Plugins" as
clean, domain-agnostic modules wired into `exact_field.py` / `glm_wheels.py` — (1) an exact
rational Bernstein enclosure that certifies an interval polynomial bound (quadratic separation or
chord clearance) in one algebraic pass without float sampling and cross-checks against a
`staircase_chords` / `staircase_cage` witness, and (2) a quadratic-norm residue mask (mod 8 / 12 /
24) over exact `Quad(d)` elements that rejects impossible unit-tangency pairs before the full
4-axis SAT gate, benchmarked for speedup and exact equivalence across the certified wheel cells;
document the chain as doc 63; keep every selftest control, `record_guard.py` and the zero-float
bytecode audit green; leave `submission.csv` and root `WHITEBOARD.md` untouched.

**The build.** `exact_field.py` gains the generic stages: `bernstein_coeffs` (Horner in `t` for
`x = a + h t`, then `c_k = Σ_{j≤k} C(k,j)/C(n,j) b_j`), `bernstein_enclosure(poly, a, b, splits)`
(`lo`, `hi`, `sign`, and subdivision that unions per-part enclosures), `bernstein_quadratic(c0, c1,
need, a, b)` for the separation form `(c0 + t c1)² − need²`, `bernstein_nodes(poly, a, b, steps)`
as the independent staircase witness, `norm_residue(x, mod)` and
`residue_norm_filter(cls, elements, mods)`. `glm_wheels.py` gains the domain drivers:
`bernstein_axis_certificate`, `bernstein_pair_slide` (a contact pair slid along its tight axis,
certified, with the gate consulted at both endpoints), `bernstein_interval_certificate`,
`bernstein_cage_crosscheck`, `plugin_bernstein_demo`, `plugin_bernstein_cage`,
`pair_tangency_residuals` (eight signed residuals in pure integer `Z[√d]` arithmetic after the
`2D²` scaling), `residue_pair_screen`, `residue_benchmark`, and two run modes with ledgers.

**The Bernstein stage is sound and incomplete, and that is asserted, not hoped.** `x² + 1` on
`[−1, 1]` has Bernstein coefficients `[2, 0, 2]`, so the coarse enclosure is `[0, 2]` and the sign
is 0 — true, and useless; one subdivision gives `lo = 1`. The same holds for the convex quadratic
`(t − ½)² + 1/100`. On `Block45(5, 4)` the first contact pair `(0, 1)`, tight on `(−½√2, ½√2)`
with `d0 = d1 = 1` and `need = 1`, is certified positive with `lo = 5/4` on `[½, 1]` and correctly
refused on `[−1, 1]` (the chord `1 + t` crosses zero), while the gate's own endpoint slacks are
`½` and `1`. The run-95/96 cage replay agrees in both directions: at the 149-cell staircase both
extents (`5/8`, `3/4`) and the chord (`1/12 + 11/48√7`) are short and the cage is capacity 1; on
`Block45(5, 4)` the extents are `33/4` and `23/2`, the chord instrument refuses
(`pair_not_excluded`), and every Bernstein verdict is "not short" — `agree` either way.

**The residue mask is a projection, and two details decide whether it is worth anything.** The
scaling by `2D²` is what makes the modular reduction legal (it acts on an exact integer, not a
rounded value); but the scaling *alone* makes the mask vacuous, because every residual is then
divisible by a power of `D`, and at `D = 4` every residue was 0 mod 8 — a 0 % rejection rate, caught
by the first benchmark before anything was reported. Dividing each residual by its content
`gcd(|A|, |B|)` is a scaling by a nonzero rational, so the zero set is untouched and the residues
become informative. With that, the mask is *exact* at mod 8 for `d ∈ {2, 5, 7}`: a primitive
`A + B√d` is never `0 mod 8`, because `N ≡ 0 (mod 8)` with `B` odd would need `A² ≡ d` for
`d ≡ 2, 3, 5, 6, 7` (impossible) and with `B` even forces `A` even (not primitive).

**The benchmark, exactly as measured** (`perf_counter_ns` integers, so the benchmark is float-free;
`--plugin-residue`, ledger `workspace/push/plugin_residue.json`):

| cell | pairs | contacts | rejected | survivors | extra | speedup |
|---|---:|---:|---:|---:|---:|---:|
| Block45(5,4) | 266 | 172 | 70 | 196 | 24 | 1.15× |
| Block45(10,8) | 1102 | 794 | 252 | 850 | 56 | 1.11× |
| Block45Half(5,4) | 182 | 112 | 70 | 112 | 0 | 1.36× |
| Block45Half(17,14) | 2978 | 2256 | 722 | 2256 | 0 | 1.12× |
| Lattice(3/2,1) synthetic | 342 | 90 | 90 | 252 | 162 | 1.14× |

Zero false rejections at mod 8, 12 and 24 on every row; every contact survived; mod 8, 12 and 24
select the same pairs everywhere (mod 8 is already complete there). The mask costs about an eighth
of the exact pass (9.4 ms vs 72.5 ms; 103 ms vs 801 ms), and the end-to-end gain is capped by
contact density — 65–76 % of candidate pairs are contacts, so Amdahl, not the mask, sets the
1.1–1.4×. The synthetic lattice is the honest counter-example: 162 of its 252 survivors are
diagonal neighbours with one tight axis and one loose one, which a necessary-condition mask cannot
reject. So the claim is exactness on the Block45Half cells, soundness everywhere, and a measured
(not hoped-for) bound on the gain.

**A latent rung bug, found and fixed.** `Q`'s comparisons dropped to plain `Fraction` and lost the
mixin's `.sign()`, so an enclosure sign test could have raised instead of comparing; `Q._diff` now
returns `Q(F.__sub__(self, o))` and control 31 pins `Q(1) < Q(2)`.

**Verification.** `glm_wheels.py --selftest` **31 controls, exit 0, 2 m 37 s** (control 31 is new:
the rational comparison, the exact basis change on two intervals, the sound-but-loose enclosure and
its refinement, node containment at `splits = 1, 2, 4`, the slide certificate with the gate's
endpoint agreement, the cage/chord cross-check, the residue screen's invariants and zero false
rejections at three moduli, exactness on `Block45Half(5,4)`, and the plugin's own residues on three
contact pairs); `--audit` **294 functions, 0 offenders**; `--plugin-bernstein` (slide + cage
replay, ledger `workspace/push/plugin_bernstein.json`) and `--plugin-residue` both exit 0; bare run
exit 0; `record_guard.py` OK; control 21's 40/40 spatial cells, controls 1–30 and the run-99
sweeps unchanged; README/STATUS footers byte-identical from `## Current results`.
**No row changed, no score claimed, `submission.csv` and root `WHITEBOARD.md` untouched.**

Entries `63-PLUGINS.md`; records `31`–`63`.

## Run 101 in detail — the certificate boundary, and the max-slack stage doc 63 §6 named

User request: establish the formal boundary between exact algebraic ground truth (rungs 3 and 7)
and display/scan projections (rung 4) by building the serialized certificate verifier first,
alongside doc 63 §6's next plugin stage — (1) a float-free JSON schema holding exact field tags,
exact container side, exact unit-circle words and exact centres, with a standalone zero-float
verifier that checks `R^T R = I`, `det R = 1`, all `4N` wall inequalities and all pairwise 4-axis
SAT separations (recording the witness axis and exact gap, accepting `≥ 0` at clearance 0) and
returns either a verified summary or the exact first failed inequality, distinguishing
`infeasible` from `outside this representation`; serializing and round-tripping Ring n = 18,
Staircase 149/150, Block45(5,4) and Block45Half(17,14) into
`workspace/push/galois_certificates.json` with CSV/print decimals flagged display-only; (2) a
sound cheap exact max-slack bound that rejects pairs before the full gate, eliminating the
diagonal survivors the mod-8 mask passed, benchmarked on doc 63 §2's five rows; (3) doc 64 with
the schema, the exact-vs-display ledger (eight areas) and an honest doc 63 §6 update, keeping
32+ controls, `record_guard.py` and the zero-float audit green.

**The format.** `galois-certificate/1` carries a `conventions` block, a `display_only` ledger and
a list of certificates; each certificate is `{id, family, field, N, L, origin, cells, expected}`.
A scalar is a canonical fraction string under `Q` and an `[a, b]` pair under `Quad(d)`; the parser
refuses a decimal spelling rather than rounding it. Each cell stores its rotation **row-major**
(`[ux, vx, uy, vy]`), so `R^T R = I` and `det R = 1` are checked rather than assumed; `L` and
`origin` are the sentence's own tight box, which is why the ring's origin is `-7/4 - 1/4√7` and
the block's is `0`. The path previously held an older export -- a flat list of sides with
`s_exact`, `s_float` and a float `verified_worst_pen`, no frame and no container -- which is
replaced here and kept in git history (commit `3668c31`) as the example of a summary that
mentions exactness without being a certificate.

**The verifier.** `scripts/verify_certificates.py` rebuilds each sentence from the file alone
(imports the tower only, never `glm_wheels`) and checks schema, number format, `R^T R = I`,
`det R = 1`, every wall, the declared side, every pair's four axes with its witness axis and exact
gap, and the declared summary — stopping at the first exact failed inequality with kind
`infeasible` (the object is representable and an inequality is false) or `outside_representation`
(a decimal, a wrong scalar shape, an unknown tag, a duplicate id, a loose declared `L`, a declared
summary the object does not have). Its `--selftest` mutates the shipped document nine ways —
decimal string, reflection frame, non-unit frame, centre pushed through a wall, loose declared
side, wrong format tag, duplicate id, declared count, declared summary — and asserts each is
refused at its own check while the untouched document still verifies.

**What is serialized.** Seven certificates, 302 KB of exact strings: `tile2` (Q, N = 4,
L = 2, 6 contacts), `ring18` (Quad(7), 18, `7/2 + 1/2√7`, 26), `staircase149` (149,
`23/2 + 1/2√7`, 449), `staircase150` (150, same side, 451), `block45_5_4` (Quad(2), 65,
`5 + 5/2√2`, 172), `block45half_17_14` (653, `29/2 + 17/2√2`, 2256) and `slope21` (Quad(5), 5,
`2 + 1/3√5`, 4). Every number in that table is the verifier's recomputation; the builder's claim
lives in `expected` and a mismatch is a failure. Voids are exact field elements
(`-16 + 23/2√7` for the 150-square staircase).

**The stage, and the correction it needed.** `pair_max_slack_bound` bounds a pair's **max** slack
by `|A + B√d| ≥ 1/(|A| + |B|S)` — a nonzero norm is a positive integer, and `z > 0` is an integer
comparison of `A²` with `dB²` — so a pair with `max slack > 0` is neither a contact nor a
violation and may be dropped. The request's "tightest axis" phrasing names the *minimum* slack,
which is exactly what keeps a diagonal neighbour (one axis exactly tight, one loose); doc 64 §5
records the correction. Measured: on `Block45(5,4)` the bound speaks for all 94 non-contacts and
leaves exactly the 172 contacts; on the synthetic lattice it removes the 162 diagonal survivors
the mask passed (252 → 90).

**The chain, and two numbers that moved.** `--chain` runs five rows × three configurations
(`mask`, `bound`, `mask+bound`) with the prune timed as its own stage:

| cell | pairs | contacts | gate calls (mask+bound) | pipeline vs gate | filters alone |
|---|---:|---:|---:|---:|---:|
| Block45(5,4) | 266 | 172 | 172 | 2.08× | 1.26× |
| Block45(10,8) | 1102 | 794 | 794 | 2.92× | 1.14× |
| Block45Half(5,4) | 182 | 112 | 112 | 2.19× | 1.33× |
| Block45Half(17,14) | 2978 | 2256 | 2256 | 4.96× | 1.08× |
| Lattice(3/2,1) synthetic | 342 | 90 | 90 | 4.65× | 2.55× |

First correction: an earlier version of this benchmark reported 4–6× for the filters alone
because it timed only the post-prune work while `Q.gate` was timing its own `Quad` prune over all
212,878 pairs at N = 653. Timing the prune and deciding it on integer components
(`_zabs_ge`, one integer sign test per axis) fixed it: the end-to-end gain is 1.9–5.1× and the
filters' own contribution is the 1.08–2.55× column — a cheaper exact prune was worth more than
either filter on contact-dense cells. Second correction: the mod-8 mask is **contact-safe but not
verdict-safe** (an overlap has no tight axis either, so the mask hides it), while the bound is
verdict-safe; control 32 puts a 1/10 overlap in front of both and asserts that the mask hides the
violation and the bound keeps it. `hidden = 0` on all five benchmark rows.

**Verification.** `glm_wheels.py --selftest` **32 controls, exit 0, 2 m 37 s** (control 32 new:
the bound's soundness `0 < lo <= exact max slack` on all 94, the box `0 != positive_lower_bound`
identities, mask/bound/both gate calls `196/172/172` with equivalence, the lattice `252 → 90`, the
overlap counter-example, the integer/Quad mask agreement, the four-certificate JSON round-trip
and the refused decimal); `--audit` **324 functions, 0 offenders** (the verifier module included:
12 decision functions); `--certificates` 7/7 verified plus 9 mutations refused; `--chain` with
ledger `workspace/push/plugin_chain.json`; `python3 scripts/verify_certificates.py` 7 verified,
0 failed; bare run exit 0; `record_guard.py` OK; README/STATUS footers byte-identical.
**No row changed, no score claimed, `submission.csv` and root `WHITEBOARD.md` untouched.**

Entries `64-CERTIFICATES.md`; records `31`–`64`.

### Run 101 addendum — the verifier's SAT pass, on integers

Same run, same artifacts, same records: the certificate file is byte-identical, and this addendum
records a change to the *verifier* only.

The SAT pass used to be the producer's formulation read twice: `qsqrt2.pair_axes` multiplies `Quad`
values, and `verify_certificates.py` multiplied `Quad` values. Two copies of one formula disagree
only by typo; they do not check each other. The deciding pass is now integer-scaled:

```
one even common denominator D over every coordinate and frame component
2 D^2 * slack  =  2 |delta . q|  -  ( D^2 + |u_other . q| + |v_other . q| )     in Z[sqrt d]
```

`delta` and `q` are the `D`-scaled centre difference and axis, `abs` and `max` are the tower's
integer sign rule on integer components, and the only rebuilt field element is the gap in the
report, produced *after* the verdict. Nothing in that pass is `Quad` arithmetic, and its own
`co_names` name no producer function (control 32 asserts this, and asserts the integer primitives
are the ones present).

The `Quad` formulation is not deleted — it becomes `sat_pass_reference`, a witness. The verifier's
`--selftest` runs `cross_check`, which compares the two implementations pair for pair: on the
shipped document all **4,532** candidate pairs agree on the verdict sign *and* on the exact largest
slack (the reference value scaled by `2D^2` equals the integer residual, integer pair for integer
pair). The seven certificates produce exactly the same summaries as before the change — contacts
6, 26, 449, 451, 172, 2256, 4; clearance 0 everywhere — so nothing about what is certified moved,
only how it is decided.

Two measured side effects. The document pass is **5 s → 0.55 s** (the `Quad` pass on 653 cells was
the cost; `sat_pass_reference` is still available for the cross-check and the selftest spends 9.7 s
on it, against 50 s before). And a bug the integer rewrite exposed in my own first attempt: I
carried `delta . q` without its absolute value, which turned negative projections into large
negative slacks and made ring18 report an overlap at pair (1, 5) with gap −32 at scale 16. The
shipped document refused it immediately — six certificates failed at `sat` — which is the
behaviour a verifier should have; the fix is one `_iabs`, and the contact counts then matched the
producer's exactly.

Checks: `--selftest` **32 controls**, exit 0, 2 m 38 s; `--audit` **339 functions, 0 naming
`float`** (verifier 27, was 12); `--certificates` 7/7 and the 9 mutations each refused at its own
check; `verify_certificates.py --selftest` 7 verified, 9 mutations, 4,532 pairs cross-checked;
bare run exit 0; `record_guard.py` OK; README/STATUS footers byte-identical.

**No row changed, no score claimed, `submission.csv` and root `WHITEBOARD.md` untouched.**

The honest limit: this is independence of *implementation*, measured, and both implementations were
written by the same author, so a shared misreading of the SAT statement would survive the
cross-check. What rules that out is external — agreement with `Q.gate` on contacts, clearance and
void, and the nine mutations each failing at its own check.

#### The tenth mutation and the fuzz

Every one of the nine mutations died before the SAT pass — at the number format, the frame, a wall,
the declared side or the summary — so the integer pass's own failure path was never exercised by a
mutation. It is now, twice. A three-square sentence (`N = 3`, `L = 2`, origin 0) has cells at
`(1/2, 1/2)`, `(7/5, 1/2)` and `(3/2, 3/2)`: the first covers `[0,1]²`, the second `[9/10, 19/10] x
[0,1]` (an overlap of `1/10` in `x`, and of `1` in `y`), the third `[1,2]²` (an exact contact with
each of them), and the span is exactly `[0,2]²`, so `L = 2` is the sentence's own side and every
wall holds. Nothing before the SAT pass can refuse it; the integer pass must, and it does:
`infeasible / sat`, pair `[0, 1]`, gap `-1/10`. Written a second time in `Quad(2)` it reports the
same gap, so the number is not an artefact of one tag or one scale. Both mutations are appended to
the shipped document (7 verified + 1 refused), which is the shape of a forgery that gets furthest:
a well-formed sentence that simply fails.

The fuzz exists because one document only exercises the pairs it happens to contain. `fuzz`
generates random exact sentences — a field tag, 2–7 centres from mixed denominators with random
`√d` parts, unit frames from that field's own words, which are enumerated by one integer search
(`ab + ce = 0`, `a² + d b² + c² + d e² = m²`) rather than hard-coded — and a third of the centres
are coincidences or `1/10`, `9/10`, `1/2`, `3/5` displacements, so strict overlaps, near-overlaps,
exact contacts and separated pairs all appear. Four seeds of 400 sentences give **9,729 candidate
pairs: 64 contacts, 5,314 overlaps, 4,351 separated, denominators up to 120, 0 mismatches** between
the integer pass and the `Quad` witness, compared on the exact largest slack of every pair and not
merely on its sign.

The fuzz caught a real defect on its first run, which is the reason to write one. `sat_pass_scaled`
returned the clearance and the gap by dividing the integer residual by `D` instead of `2D²`: at
`D = 10` a violation of `1/10` printed as `1`. Every clearance in the shipped document is exactly
`0`, where the divisor cannot show, and the printed-side comparison in the fuzz was the only thing
that could see it. Verdicts, contact counts and orderings never moved — the decision was right and
the number was wrong — and the gap is now scaled consistently, with the fuzz and the tenth
mutation (`-1/10`, which would have printed as `-1`) both pinning it down.

Checks after the change: `--selftest` 32 controls; `--audit` **342 functions, 0 naming `float`**
(verifier 30); `--certificates` 7/7 with the same seven summaries and **11 mutations** refused;
`verify_certificates.py --selftest` (7 verified, 11 mutations, 4,532 pairs cross-checked, 145 fuzz
pairs); `--fuzz 400` on four seeds, 0 mismatches; bare run exit 0; `record_guard.py` OK;
README/STATUS footers byte-identical.

**No row changed, no score claimed, `submission.csv` and root `WHITEBOARD.md` untouched.**

What the fuzz does not establish: the sentences are random in their centres and frames, not in their
*structure*, so it samples the pass rather than proving it; and both passes are still mine, so a
shared misreading of the SAT statement would survive both the cross-check and the fuzz.

## Run 102 — the relaxed rung: coverage, and what exact lifting reaches

Doc 65. The instrument from run 101 is turned on the 424 rows that have never had an exact sentence.

**Coverage, 1,000 rows.** 546 carry a certified exact sentence (447 pure-Q grid rows from run 84's
census + 99 Q(sqrt 2) pose lifts from runs 84-85), 30 are `side-only` (the container side is
algebraic but the pose was never lifted; n = 126 is the one where even that failed), and 424 are
`relaxed` (the run-86 class `continuous`). New in this run: a **carrier census** — a carrier is a
square whose stored angle has no exact word at the declared heights. 453 rows carry at least one,
and the split is `1-10`: 14 rows, `11-100`: 123, `>100`: 316. **Every one of the 424 relaxed rows
carries at least one carrier**, and in 361 of them a carrier sits on the bounding box.

**Targets (chosen before lifting).** The three notches 677/785/901 (already `Q(sqrt2) pose` — kept as
the reference), the continuous rows that bracket them (680, 689, 733, 788, 845, 904), and the
relaxed rows with the most slack `L - sqrt N` (11, 17, 39, 68, 86).

**Lifting (`qsqrt2.lift_sentence`, carriers dropped, every survivor written as a
`galois-certificate/1` and checked by `verify_certificates`).** **3 of 14 lift at clearance 0**: the
three notches, at `29/2 + 17/2 sqrt2`, `33/2 + 17/2 sqrt2`, `37/2 + 17/2 sqrt2`, with 2375, 2785 and
3227 contacts and certificates the verifier accepts. **0 rows beat their delivered side materially**:
the exact sides are 3.8447e-9, 3.8507e-9 and 3.8547e-9 *below* the published ones — the table's
polish overshoot, not a gain. **11 refuse, in two groups.** `not-on-lattice` (680, 733, 788, 845 —
exactly the four rows whose sides are the rationals 186/7, 193/7, 200/7, 207/7, i.e. the `2k + 4/7`
rung of run 90's rational-t family): the side is recovered and the geometry is not, because
dropping 90-110 carriers leaves squares the surviving contact equations do not pin. `side-not-
recovered` (689, 904, 11, 17, 39, 68, 86): the core's own span is not within 1e-7 of the declared
Q(sqrt2) lattice, so there is no `L` to place cells in at all.

**Completion.** The probe (contacts from the delivered pose, exact 2x2 solves over the certified
families' words, every candidate accepted only by the full gate) has a positive control: remove one
cell from the certified 677 sentence and the axis word puts it back at the same side with clearance
0 and 2375 contacts. No relaxed row could be probed — the probe needs a lifted core, and none of the
11 has one — so the honest count is 0 carriers replaced out of 0 attempted, and the obstruction is
upstream of completion.

Two bugs in the probe were found and fixed by that control, both the same family as run 101's: the
pair predicate had been read as the *minimum* slack over the four axes (a pair's clearance is its
maximum), and contacts were emitted per axis without requiring the pair's largest slack to be zero,
which made two cells at the same height but far apart look like a tangency.

**Next geometric hypothesis.** The four `2k + 4/7` rows have cheap sides and expensive angles, so
the next production is a construction, not a lift: a rational-t sentence at side `2k + 4/7` (the
missing rung of run 90's `2k + 5/7` family) at the counts 680/733/788/845, with the gate as the
arbiter — either it certifies the relaxed rung for the first time at the published side, or it gates
strictly below and becomes a real score candidate.

Checks: `landscape65.py --selftest` 6 controls (32 s); `--audit` **366 functions, 0 naming
`float`** (`landscape65` added, its 24 included); `--selftest` 32 controls; `verify_certificates
--selftest` 11 mutations + fuzz; bare run exit 0; `record_guard.py` OK; README/STATUS footers
byte-identical. Ledger `workspace/push/landscape65.json`.

**No row changed, no score claimed, `submission.csv` and root `WHITEBOARD.md` untouched.**

Entries `65-LANDSCAPE.md`; records `31`-`65`.

## Run 103 — a bounded core lift, and the `2k + 4/7` rung started

Doc 65 §8. Two jobs: make the run-102 stage cheap and clean, then start the construction doc 65
named.

**Cleanup.** `landscape65.py` lost the debug-round debris — the unused `gcd` import, a dead branch in
`word_kind`, a recomputed extent in `probe_carrier`, a stale docstring — and the carrier-drop
semantics are now one function, `drop_carriers(words) -> (keep, dropped)`, documented where it lives:
carriers are *removed*, never snapped to the axis word; kept cells keep their delivered order; the
dropped indices come back so completion addresses a carrier by its **delivered** index.

**The cost bound.** `qsqrt2.recover_leftovers` takes an optional `budget` in work units
(`recover_point` calls) and returns `(miss, exhausted)`; `lift_sentence` threads it and reports
`budget_exhausted` on a refusal. `None` is the old unbounded search, so every earlier caller — the
verifier's own lift path included — is unchanged. `landscape65` declares `RECOVER_BUDGET = 120`.
Measured on the same fourteen rows: the whole run is **306 s** (269.6 s of it lifting) instead of
~45 minutes, with notch lifts at 10.6/13.2/16.2 s (was ~40 s each) and the four `not-on-lattice`
refusals at 33.9/60.4/58.0/67.7 s (was 3–9 min each). **Every verdict is unchanged row by row** — 3
lifted with the same sides and contacts and verified certificates, 4 `not-on-lattice`, 7
`side-not-recovered`, same 546/30/424 tally and same carrier bands — and the refusals now record
`unrecovered` and `budget_exhausted: true`.

**The `2k + 4/7` rung (`scripts/rat47.py`, new).** Three parts, gate as arbiter.

*Strip lemma, exact over the alphabet:* over all 82 rational-t words with `q <= 16` plus the 45° word,
the bbox width `|cos| + |sin|` is at least **1**, attained only by `t = 0` and `t = 1`. Since
`4/7 < 1`, no unit square fits a `4/7` margin — the rung is **not** a block-plus-seam packing.

*Skeleton, measured:* all four rows are `N = m² + 4` (`m = 26..29`) at side exactly `2k + 4/7`, and
their angles snap to the same two-word structure — `m² − 52` axis squares, exactly **28** at the
3-4-5 word (`t = 1/2`) and exactly **28** at `t = 1/3`, with worst deviations 1.6e−3 to 3.6e−3. The
snapped pose gates **1 to 2 violations**: 680 at −3.07e−5, 733 at −6.9e−4 and −3.7e−4, 788 at
**−2e−11**, 845 at −1.6e−3 and −2e−4. So the delivered pose is one or two pairs away from a
rational-t sentence, and 788's is at rounding scale.

*Repair, exact:* re-choosing words cannot close them. Top-4 per cell, then pairwise 6×6, scored by the
exact per-pair clearance, swaps **nothing** in all four rows — the defect is positional, not angular.
And lifting the snapped pose from scratch pins only 142/19/302/19 squares and refuses
(`not-on-lattice`, budget exhausted), so re-labelling the delivered pose cannot reach the rung either.

**Certificates: 0 of 4.** The next experiment is named: 788's 2e−11 pair is the cheapest positional
repair (a certificate carries any Q(√2) coordinate, so that scale is arithmetic, not a tolerance), and
the constant 28 + 28 band is a fixed module worth deriving from its contact law, as doc 53 derived the
ridge's width.

Checks: `rat47.py --selftest` 4 controls; `landscape65.py --selftest` 6 controls (32 s); `qsqrt2.py
--selftest` 11 controls; `--audit` **382 functions, 0 naming `float`** (`landscape65` 25, `rat47` 15,
both in the audit list); `--selftest` 32 controls; `verify_certificates --selftest` 11 mutations +
fuzz; bare run exit 0; `record_guard.py` OK; README/STATUS footers byte-identical.

**No row changed, no score claimed, `submission.csv` and root `WHITEBOARD.md` untouched.**

Entries `65-LANDSCAPE.md`; records `31`-`65`.

## Run 104 — the rung's last pair closes above the rung, and the 28 + 28 band's law

**The positional repair (`rat47pos.py`).** Run 103 left the rung one or two pairs short and showed that
angles cannot close them. Run 104 moves one cell of each offending pair along a SAT axis of the pair,
orientations fixed: the feasible set is an exact interval union in Q (two rational rays per axis,
intersected over the pairs and with the box, so the side cannot grow), the witness is the first feasible
move — the pair's own constraint turning non-negative, i.e. exact contact and clearance 0 — and a
two-pair row is repaired one pair at a time by accepting the move that strictly lowers the gate's
overlap count. **All four rows close with clearance exactly 0 and a verified certificate**: 680 (cell
244 by 3.0743e−5), 733 (cell 280 by 6.9151e−4, then cell 471 by 3.6617e−4, 2 contacts), 788 (cell 195
by **2e−11**), 845 (cell 254 by 1.5524e−4, then cell 763 by 6.4547e−4, 2 contacts) — and **all four
sit above the rung**, exactly: 1.9274e−9 (680, 733), 1.9304e−9 (788), 1.9324e−9 (845) as Fractions
(`3373/1750000000000`, `13513/7·10^12`, `13527/7·10^12`). The excess is a wall problem: the wide wall's
tightest cell has 6.8–7.5e−11 of inward room, 26–28× short, and 7 ∤ 10^12 while every coordinate of the
pose is a multiple of 1/10^12. So "does it close at 200/7" has the answer no — it closes one lattice
step above, as an exact zero-clearance sentence.

**The band's law (`rat47law.py`).** The census is exact: `m² − 52` axis cells (624/677/732/789) plus
28 + 28. The module is a **7.48-thick strip**: across four independently polished rows its thickness
agrees to **5.8e−11** (each ~5.4e−10 above the rational `187/25`), it is pinned to the wall it touches
to 8e−12, and its free length wanders **3.6e−3** — because 28 cells carry only 28–29 intra-band
contacts, so the band is a chain, not a rigid body. The intra-band contact types are **five, four
identical in all four rows, one count flipping 8↔9** (`t=1/2`–`t=1/2` on `v`, and `t=1/3`–`t=1/3` on
`v`), the classification safe for any threshold in `[1e−10, 1.4e−4]`. The band-to-axis interface is
**not** fixed (28–32 contacts in 11–13 types). And the rung's `4/7` is a **lattice shift**: two
interpenetrating lattices `Z²` and `(Z + 4/7)²` give **18 column gaps of exactly 3/7 in every row**
(closest 2.9e−10 … 3.2e−6), which is what the strip lemma predicted — not a seam, a shift.

**Above 1000.** The arithmetic is exact (`N = m² + 4 = (m² − 52) + 56`, sides 228/7, 284/7, 319/7 at
m = 32, 40, 45) and the growth is translation only: copying the outer 3-wide band outward takes 845 to
965 cells at side 32.571428573361 with the excess **unchanged digit for digit**
(`13527/7000000000000`), so the side extends past 1000 without drift — but the count does not (965
against 1028), because the outer band is not periodic (58 cells in the last 3 units against 87). The
rows share a count law, not a shape; an exact `N > 1000` row needs a fresh construction, which is the
next production.

Checks: `rat47pos.py --selftest` 5 controls; `rat47law.py --selftest` 5; `rat47.py --selftest` 4;
`landscape65.py --selftest` 6; `qsqrt2.py --selftest` 11; `glm_wheels.py --selftest` 32;
`verify_certificates --selftest` 11 mutations; `--audit` **427 functions, 0 naming `float`**
(`rat47pos` 26, `rat47law` 19, both in the audit list); bare runs exit 0; `record_guard.py` OK;
README/STATUS footers byte-identical.

**No row changed, no score claimed, `submission.csv` and root `WHITEBOARD.md` untouched.**

Entries `65-LANDSCAPE.md` §9; records `31`–`65`.

## Run 105 — the candidate search: 0 of 10 beats, five first certified sentences, and a new field

**The instrument (`cand105.py`).** Two levers were tested and one was killed on the way in: a
homothety of a delivered row's positions cannot lower its side, because the container *is* the bbox
(`lambda* = 1` with a wall binding — selftest control 5). The lever that can is the square's
*extent*, `(|c| + |s|)/2`, minimal (1/2) exactly at the axis words. Its floor is the **axis bound** —
the bbox with every word axis — which is `<=` the bbox of *every* word assignment, so equality with
the delivered bbox is a proof that no relabelling of any subset can lower that row.

**Part 1 — the candidates.** Ten rows by one rule (largest relative void `(L^2-n)/n` in each range):
six above 324 (330, 333, 329, 332, 331, 325) and four below (68, 66, 67, 69), each tested with
whole-motif swaps and single-cell swaps in Q(sqrt 2) and gated exactly at clearance 0. **0 of 10
beat.** Nine rows have the axis bound *equal* to the delivered bbox (gap exactly 0), so they are
provably closed to relabelling; the one exception, n = 333, lowers its bbox by exactly `9.2835e-4`
and the gate refuses it with 116 overlaps against the delivered 115 — contact-blocking, not spacing.
For n = 331 and n = 66 the all-axis relabelling is itself a clean packing at the same side: a second
exact pose for the row, not a smaller one.

**Part 2 — first exact sentences.** Five rows (325, 329, 331, 66, 67) carried exactly-worded angles
(worst snap `<= 3.2e-13`) but only the table's `1e-9` shim, so the clearance was positive and no
certificate existed. One exact slide to the nearest contact — along that pair's own unit axis, by
exactly its slack — makes each tight: all five now verify with clearance 0 and one contact, at sides
equal to the delivered ones digit for digit, `741421356313/40000000000`, `2332106781659/125000000000`,
`467677669577/25000000000`, `4328427125631/500000000000` and `2176776695739/250000000000`. These are
firsts: the shipped document's seven cells include none of these rows.

**Part 3 — the off-axis motifs, as algebra.** The strip penalty is `|c| + |s| - 1`: 0 at the axis,
0.414214 at 45 degrees, 0.366025 at 60, 0.260074 at 72. `sin60 = sqrt3/2` is refused by Q(sqrt2),
Q(sqrt5) and Q(sqrt7), so hexagonal needed a new field: this run builds the first certified
**Q(sqrt 3)** sentence (N = 2, one corner contact, side `3/2 + (1/2)sqrt3 = 2.366025`, verified).
At N = 2 it beats the 45 degree corner (`1 + sqrt2 = 2.414214`) by 0.0482 and loses to the axis pair
(2) by exactly the penalty. Golden is worse than that: `cos72` is in Q(sqrt5) but `sin72` is not —
its square's discriminant `20480 = 64^2 * 5` is not a square — so a 72 degree square is a degree-4
object no Q(sqrt5) rung can carry.

Checks: `cand105.py --selftest` 5 controls; bare run exit 0 (10 rows, 325 s); `--audit` **460
functions, 0 naming `float`** (cand105 33); every earlier selftest still green; `record_guard.py`
OK; README/STATUS footers byte-identical.

**No row changed, no score claimed, `submission.csv` and root `WHITEBOARD.md` untouched.**

Entries `66-CANDIDATES.md`; records `31`–`65`.

## Run 106 — the census certified (552 rows), the 45 degree repair, and a jammed two-cell trade

**The instrument (`cand106.py`).** Run 105 certified five rows by hand; this run asks whether the
slide is a property of five rows or of the table. One screen (snap every angle to a unit word,
`<= 1e-9`) puts **553** of the 1,000 rows in the census (the worst row, n = 743, is 1.27 away);
one `survey` pass per row returns the overlapping pairs *and* the tightest separated pair's
slack; one `slide_best` closes that pair on **every** positive axis at once; the exact gate and a
`galois-certificate/1` decide. The ledger is compact (`cand106.json`: per row a verdict, the
slide, the side, the contacts), so the selftest stays at 5 controls.

**Part 1 — 552 of 553 certified, 547 for the first time.** The batch (2441 s) certifies **552**
rows at clearance exactly 0 with verified certificates; 550 by a slide (549 single-axis, one
all-axis) and 2 (n = 678, 679) by the repair of part 2. The all-axis case is **n = 634**: its
tightest pair has both separations at `1 + 77/10^12`, so closing one axis leaves the pair
separated (its SAT slack is the max over axes) — closing both needs `t = 77/10^12*sqrt2` along
`(1,1)/sqrt2`, and that certifies at `L = 6426776695777/250000000000` with 2 contacts. The single
exception is n = 1, one square with no pair to contact: **already tight, nothing to certify**.
Run 105's five rows (325, 329, 331, 66, 67) are inside the 552 at identical sides, so **547 rows
are newly certified** — the shipped document had seven cells, none of these rows. Three
representative certificates (first, middle, last row of the census) are written to
`workspace/push/cand106_samples.json` and re-verified by the standalone verifier alone: n = 2 at
`L = 2`, n = 427 at `1312500000119/62500000000`, n = 1000 at `16000000000969/500000000000`,
**3 verified, 0 failed**. 551 of the 552 sides are identical to the delivered ones and one moves
— n = 2 certifies at exactly `L = 2`, `1e-9` below the delivered `2 + 1/10^9`, because its slide
moved the bbox-defining cell; that is the shim and the row's own floor (a 2 x 1 grid's side is 2),
not a gain, and the guard's 553/1000 count is untouched. So 547 rows stop being a pose with a
tolerance and become a sentence with a witness.

**Part 2 — the 45 degree repair, generalised.** Run 104's move is rational; the 45 degree axes
are `Q2(0, +-1/2)`, so the step becomes `t = (sign(proj)*need - proj)/k` with `k = +-d.q` and `d`
one of the eight signed unit directions, smallest `|t|` first, the exact gate as arbiter, no
`Decimal` anywhere. On the asked rows it is honest and half-successful: **n = 330 goes 6 -> 3
overlaps in four exact moves** (three `-x`, one diagonal `-1 + 1414025346279/2*10^12*sqrt2` —
the 45 degree case working), then refuses because the fifth move does not lower the count, the
three survivors (216, 233), (224, 247) and their common clearance
`-1/2 + 352353905641/10^12*sqrt2` being mutually coupled; **n = 332 does not start** — its 159
overlaps are dense enough that the first move leaves 159, so the loop stops after one step.
Neither closes into a certificate. What the repair *does* close is the census's two near-misses:
n = 678 and n = 679 each have one overlap at their exact words (slack
`-1 + 1414213561901/2*10^12*sqrt2`), one diagonal step of that size fixes it, and both certify at
`L = 1326776695393/50000000000` with 1 contact.

**Part 3 — the two-cell trade has no depth-one instance.** Doc 66 §7's trade (free slack inside,
spend it by pulling the wall cell in) is enumerated exhaustively on two certified rows rather
than searched: every bbox wall cell, every bbox-adjacent partner, all eight signed directions.
**n = 66: 1216 combinations, n = 325: 2880, every one with `tau = 0`** — not small, exactly zero,
and none turned down by a gate, so the moves do not exist. Both sentences are *jammed at depth
one*: every neighbour of every wall cell is in contact along a narrowing axis in every one of the
eight directions, so there is no interior slack to spend. The mechanism is proven live by control
5, which shrinks a 4 x 3 sentence's box from 4 to **3**; the refusal is a property of the rows,
not of the instrument. A first four-direction run reported the same verdict and was wrong to
trust (a widening axis can free room in that blind spot) — the eight-direction count is the
recorded one.

Checks: `cand106.py --selftest` 5 controls; `cand105.py --selftest` 5; `rat47.py` 4;
`rat47pos.py` 5; `rat47law.py` 5; `landscape65.py` 6; `qsqrt2.py` 11; `glm_wheels.py --selftest`
32; `verify_certificates --selftest` 11 mutations; `--certificates` 7 shipped; `--audit` **485
functions, 0 naming `float`** (cand106 25, in the audit list); every mode run to completion, exit 0
(`--batch` 2441 s, `--repair`, `--couple`, `--retry`); `record_guard.py` OK; README/STATUS
footers byte-identical.

**Correction (run 107, doc 68 §1).** The `tau = 0` of part 3 is `cand106.wall_room`'s pair rule,
which caps a pair on its narrowing axes and blocks as soon as one is negative. A pair is legal
while *some* axis is separated, so that rule over-reports blocks (on the exact knight pair
`dx = 1`, `dy = 2` it reads 0 where the truth is unbounded); with the corrected rule all 1216 and
2880 combinations have positive room. "Jammed at depth one" is therefore wrong; what run 106
measured, correctly and for a different reason, is that no two-cell trade lowers L — the face is
multiply defined. The substitution of this paragraph is the only change to this entry.

**No row changed, no score claimed, `submission.csv` and root `WHITEBOARD.md` untouched.**

Entries `67-CENSUS-CERTIFIED.md`; records `31`–`66`.

## Run 107 — depth two is open, the side does not move, and n = 330's three-overlap cycle stays blocked

Run 106 asked two questions — is a certified sentence *jammed at depth one* (doc 66 §7's two-cell
trade), and can n = 330's three coupled overlaps be cleared by moving several cells at once
(doc 67 §§2–3) — and this run answers both with one instrument, `scripts/observer_chain.py`
(6 controls, float-free, in the bytecode audit), built on the two Lean contracts: `readCost`
(`ObserverY.lean`) and the MOG syndrome diagnosis at weight ≤ 3 (`GolaySemantics.lean`). The
contracts are re-computed exactly from the Lean data, not quoted.

**Part 0 — the instrument that answered the first question was wrong, and the run says so first.**
`cand106.wall_room` caps a pair by the maximum over *narrowing* axes and returns `0` as soon as a
narrowing axis is negative; but a pair is legal while **some** axis is separated, so an axis that is
constant, widening, or already negative constrains nothing. Control 1 pins the difference on an
exact knight pair (`dx = 1`, `dy = 2`, moving `+x`): `wall_room` reads `0`, `room_set` reads
unbounded (the `y` axis is slack `+1` and never entered). Consequence: **run 106's "jammed at depth
one" is an artifact** — with the corrected rule **all 90 of n = 66's and all 216 of n = 325's
inward probes have positive room**. Doc 67 §3 and the run-106 entry carry the correction.

**Part 1 — the directed depth-two tracer.** Both certified rows are reproduced and checked first:
n = 66 at `L = 4328427125631/500000000000`, n = 325 at `L = 741421356313/40000000000`, both
`verified`. The tight graph (SAT slack exactly 0) has **3** pairs at n = 66 and **1** at n = 325.
From every bbox wall cell and every inward direction the tracer spends the cell's *corridor* (the
sum of successive rooms, each closing the next contact) and then walks wall → tight blocker 1 →
tight blocker 2 → pocket, pruning whenever a required receding direction is itself a tight contact
of an outside cell and keeping a chain only if its interior cells can hold it and every tight
contact inside survives the shear.

| | n = 66 | n = 325 |
|---|---|---|
| wall cells (faces `lo_x, hi_x, lo_y, hi_y`) | 30 (7, 8, 8, 7) | 72 (18, 18, 18, 18) |
| inward probes / with positive corridor | 90 / **90** | 216 / **216** |
| corridor range | `231/10^12` … `742640687523/10^12 − √2/2` = 0.035533 | `27/250000000000` … `80761184477/10^11 − √2/2` = 0.100500 |
| two-cell chains with room > 0 | 68 | 144 |
| three-cell chains | 12 | 0 |
| pruned at blocker 2 / by the shear test | 4 / 558 | 0 / 1224 |
| **probes that shrink L** | **0** | **0** |
| runtime | 23.87 s | 200 s |

So the sentences are *open*, not jammed, and still **no chain moves the side**: 0 of 90, 0 of 68
and 0 of 12 at n = 66, and 0 of 216, 0 of 144 and 0 of 0 at n = 325, with `dL >= 0` for every
survivor (the ten probes that were gated certify at clearance 0 — six at `dL = 0`, four at
`dL > 0` by at most `231/10^12 + 231/2·10^12·√2`: legal moves that leave the side or grow it). The
reason is exact and in the second column: the bounding-box face is **multiply defined** — 7–8 cells
per face at n = 66 and 18 at n = 325 — so moving one face cell inward leaves the side where it is
until *every* face cell moves. That is a face slide, not a two-cell chain.

**Part 2 — the coupled repair.** From run 106's four moves, n = 330 has `L =
118003255389229/6312500000000` and **three violated pairs, all disjoint**: `(184, 195)` with
`−2 + 2828238908803/2·10^12·√2`, `(216, 233)` with `−1/2 + 353548007689/10^12·√2`, `(224, 247)`
with `−1/2 + 352353905641/10^12·√2` (the first is the pair cell 195's own diagonal step created,
which is why the cluster is `{184, 195, 216, 224, 233, 247}`). Three is inside the MOG's exact
diagnosis range (control 4: weights 1–3 injective, weight 4 colliding), so the fault set is named
and the search is exhaustive over it: the three pairs are disjoint, so **0** subsets of two cells
hit all three and **8** of three do; 8 × 8³ = **4096** joint motions, each at its exact clearing
time, **all 4096 clear the three named pairs and not one leaves zero violations**. The debt
histogram is 2:3, 3:13, 4:90, 5:222, 6:404, 7:537, 8:531, 9:436, 10:491, 11:525, 12:481, 13:273,
14:59, 15:30, 16:1, so the minimum is **2**: cells `{184, 216, 224}` (directions `−diag`, `anti`,
`anti`) at `t = 1 − 40644125503/10^11·√2` break `(170, 184)` by `−2 + 278387009073/25·10^10·√2`
and `(201, 216)` by `−2 + 1115740420767/10^12·√2`, with `dL = 0`. **n = 330 stays blocked**, by an
exact inequality rather than a generic failure: clearing the three overlaps needs `t` in
`0.42…1.46`, and at that travel a cell reaches a *new* 45 degree neighbour two cells away. The
`taxMOG` ordering is honest but not decisive (a 2-cell repair leaving one pair costs `2 + 1 = 3`,
tied with a 3-cell repair clearing all three, so only the gate may break the tie), and with the
2-cell branch empty every candidate scores `3 + debt >= 5`.

**Controls (6).** 1 the corrected pair rule (knight pair: 0 versus unbounded); 2 `room_set` on a
stock sentence (positive room, gate-certified move); 3 a 2-cell joint move with `taxMOG` 3; 4 the
MOG census (weights 1–3 injective, 1771 colliding classes at 4); 5 a depth-one-jammed row that
opens at depth two and shrinks L from 4 to **3**; 6 three disjoint coupled overlaps — 0 hitting
sets of size 2, resolved by one 3-cell step at `taxMOG` 3, gated at clearance 0 with 3 contacts and
certified.

Checks: `observer_chain.py --selftest` 6 controls; `cand106.py --selftest` 5; `cand105.py
--selftest` 5; `rat47.py` 4; `rat47pos.py` 5; `rat47law.py` 5; `landscape65.py` 6; `qsqrt2.py` 11;
`glm_wheels.py --selftest` 32; `verify_certificates --selftest` 11 mutations; `--certificates` 7
shipped; `--audit` **520 functions, 0 naming `float`** (observer_chain 35, cand106 25, in the audit
list); every mode run to completion, exit 0; `record_guard.py` OK; README/STATUS run-history line
byte-identical.

**No row changed, no score claimed, `submission.csv` and root `WHITEBOARD.md` untouched** — no
verified certificate achieved a strictly smaller side anywhere in either search.

Entries `68-OBSERVER-CHAIN.md`; records `31`–`67`.

## Run 108 — the face slide spends the 1e-9 polish, the high-slack rows refuse, and the metric gains 7.9e-9

Doc 68 §4 left one move untested: translate every cell that realises one side of a certified row's
bounding box inward by a common exact `t`. This run settles it with `scripts/face_slide.py` (4
controls, 25 decision functions, float-free, in the audit list), and the answer has two halves.

**Part 1 — the slide.** For a face and an inward direction the feasible set is the interval `[0, T]`
with `T` the smallest pair cap (each pair survives while *some* axis is separated; axes not separated
at `t = 0` are skipped, the error run 106's `wall_room` made). Every one of the eight faces has
strictly positive room: `231/10^12` on all four faces of n = 66 — bound by pairs (0,1), (15,16),
(15,21), (0,5) — and `27/250000000000` on all four of n = 325 — (97,3), (107,90), (102,0),
(112,93). A *single* face slide still changes `L` by exactly zero, and that is the second half:
the container is a square, `L` is the larger of the two extents, and both rows are square to the
delivered precision, so the other axis binds. Sliding **both faces of an axis** shortens it by their
two rooms at once and the squeeze follows: n = 66 goes from `4328427125631/500000000000` to
`21642135627/2500000000` (`dL = -231/500000000000` = −4.62e−10) and n = 325 from
`741421356313/40000000000` to `18535533907609/1000000000000` (`dL = -27/125000000000` = −2.16e−10),
each at **clearance 0 with a verified certificate** (`verify_certificates.py`). The same squeeze on
the 33 exact-worded rows with n ≤ 40 shrinks **31** of them with verified certificates
(`Σ dL = -26881/10^12` = −2.6881e−8); the slides are exactly the `1e-9` polish coming off (n = 2:
`2000000001/1000000000` → `2`), not a smaller packing.

**Part 2 — the 448 uncertified rows.** Ranked by their own metric term `L/√n − 1` (exact, rigorous
intervals) with `L²−n` beside it: the top 15 are n = 11 (1.168985), 18, 17, 29, 28, 39, 37, 41, 53,
55, 54, 68, 69, 70, 71 — all small or medium rows far above the area bound, all with transcendental
carriers. Each was attacked constructively: snap the stored angles to the exact words (worst gap
3.4e−3 rad), repair every overlap by the smallest exact slide, slide to contact, squeeze, certify.
**Three certify and all three are worse** — n = 11 by `+6011784170943/2644100000000000` = +2.27e−3,
n = 17 by `+458356142729/675500000000000` = +6.79e−4, n = 41 by `+11725495717/1750000000000` =
+6.70e−3 — and none of the three admits a face slide afterwards. **Twelve stall** with overlaps left
(18: 16→14, 28: 16→15, 29: 20→1, 37: 20→13, 39: 21→7, 53: 24→13, 54: 26→16, 55: 17→16, 68: 52→50,
69: 24→15, 70: 32→29, 71: 31→30). **No row improves**, so the 448 stay uncertified and their
delivered sides stand.

**Part 3 — the exact metric.** `score = Σ L/√n − 1` over the 1,000 rows, bounded rigorously with
integer square roots (no float, no Decimal, no tolerance): the delivered table scores
`22.645990612927686` (the repo's own formula; the leaderboard number 22.218056945 differs by 0.428
and the *delta* is independent of it). With the 33 verified improvements the bounds give
`Δ = -0.000000007885757`, i.e. **−7.885757e−9**, strictly better. The candidate is
`workspace/push/submission_candidate.csv`: the **1,026 changed square rows only**, coordinates
rounded to 12 places, every one re-gated exactly and still clearing at `clearance ≥ 0`
(`rounded_regate` in `workspace/push/face_slide.json`). **`submission.csv` is not updated** — the
gain is the deliberate safety polish, no packing improved, and the patch is left for the user to
apply. The full 553-row sweep is **not** complete (≈2 s a row, the large 45°-heavy rows dominate);
this run measured n ≤ 40 plus the two named rows and leaves the other 518 to the next run.

Checks: `face_slide.py --selftest` 4 controls; `observer_chain.py --selftest` 6; `cand106.py
--selftest` 5; `cand105.py --selftest` 5; `rat47.py` 4; `rat47pos.py` 5; `rat47law.py` 5;
`landscape65.py` 6; `qsqrt2.py` 11; `glm_wheels.py --selftest` 32; `verify_certificates --selftest`
11 mutations; `--certificates` 7 shipped; `--audit` **547 functions, 0 naming `float`**
(face_slide 27, observer_chain 35, cand106 25, in the audit list); `record_guard.py` OK;
README/STATUS run-history line byte-identical.

**No row changed, no score claimed, `submission.csv` and root `WHITEBOARD.md` untouched.**

Entries `69-FACE-AND-SCORE.md`; records `31`–`68`.

## Run 109 — the relational layer: pin chains, no free void, and a verified "win" that the truth rejects

Run 106–108 moved cells one or two at a time. This run asks the semantic question instead: what holds
a packing together, and can a *coupled* move — a group, a re-orientation, a void trade — break it?
`scripts/semantic_pack.py` (3 controls, 28 decision functions, float-free, in `--audit`) builds four
exact relational objects and attacks five rows (11, 17, 18, 29, 330).

**The structure.** Contacts (slack-0 pairs), pins (wall cells whose contact narrows under the inward
direction), depth-2 bottleneck chains (wall → pin → pin), and void pockets (connected components of
wall cells with room). Every analysable row is **relationally closed**: n = 11 has 5 contacts, 2 pins,
2 chains and one free wall cell with `3.53e−4` of room; n = 17 has 9 contacts, 3 pins, 4 chains, no
pockets; n = 29 has 23 contacts, 1 pin, 1 chain, no pockets; n = 330 has 30 contacts, 2 pins, 2 chains,
no pockets. n = 18 stalls at 16 overlaps after snapping. At n = 330 the 28 free wall cells are all on
`hi_x`/`hi_y` while both binding cells (`lo_x`, `lo_y`) are pinned: free space sits on the sides that do
not set the side, which is the relational restatement of runs 106–108.

**The attacks.** 234 coupled moves judged by the gate at clearance 0: rigid translations of 2–5-cell
connected clusters along the eight directions (95), 45°/90° re-orientations of those clusters about
their own centres (134), and pin-into-void trades (1). 92 legal, **one model win**, zero true wins.

**The model win, and its rejection.** At n = 330 a rigid move of cells {14, 32} by
`−13 + (928542037565257/10^14)√2` along `(√2/2, √2/2)` gates at clearance 0 and its certificate
**verifies** (N = 330, 25 contacts) at `L_model = 9500099491707/10^12 + (13/2)√2 = 18.692488`, beating
the table's `18.692672` by `1.85e−4`. Written into `submission.csv` and scored by the repo's own
`sqscore`, the same coordinates have true side `18.692916` against the delivered row's `18.692388` —
`2.43e−4` **worse**, and the table score moves `22.218056945 → 22.218085993`. The patch was reverted
immediately; `sqscore` and `record_guard` are green on the delivered table.

**Why.** The certificate is exact for the *snapped* pose — at n = 330, 236 of 330 angles are not words
(gaps to `6.9e−3` rad). The table's L is a model value too: it overstates that row's true side by
`2.84e−4`, so "candidate beats table L" is not a sound test there. And the representation question has
a sharper answer than "higher degree": the gate's separations involve `cos`/`sin` of non-word angles,
which are transcendental for rational non-zero angles (Lindemann–Weierstrass), so **no algebraic field
can certify such a row at all**. The sound routes are a snapping error budget (`true side ≥ model − ε`),
certified interval arithmetic, or a genuine extension only for algebraic angles (e.g. `Q(√2,√3)` for
30°/60° words). The 553 word-exact rows need none of it, and remain the whole of the repository's
verified frontier.

Checks: `semantic_pack.py --selftest` 3 controls; `face_slide` 4; `observer_chain` 6; `cand106` 5;
`cand105` 5; `verify_certificates --selftest` 11 mutations; `--certificates` 7 shipped; `glm_wheels
--selftest` 32; `--audit` **575 functions, 0 naming `float`** (semantic_pack 28, face_slide 27,
observer_chain 35, cand106 25); `sqscore` guard OK 22.218056945 / 553 beats; `record_guard.py` OK;
README/STATUS run-history line byte-identical.

**No row changed, no score claimed, `submission.csv` and root `WHITEBOARD.md` untouched.**

Entries `70-RELATIONAL.md`; records `31`–`69`.

## Run 110 — the table is reconciled, the ε guard is in place, and free angles buy nothing legal

Run 109 left two loose ends: the table's per-row sides did not agree with the submission, and no angle
had ever been allowed to move. Both are closed, with three new float-free instruments
(`true_geom.py` 7, `reconcile_table.py` 6, `semantic_pack.py` 36 decision functions) and one
discovery-only one (`relax_angles.py`, deliberately outside the audit).

**1. `table.json` reconciled.** `reconcile_table.py` compares every row's `L` with the true side of
`submission.csv` at 40 decimal digits (`Decimal` `cos`/`sin` from Taylor series, exact reduction — no
float). **357 of 1000 rows were stale** by more than `1e−9`, 343 by more than `1e−3`, the largest by
`9.0e−2` (n = 696). The two totals explain each other exactly: `Σ L_table/√n − 1 = 22.645990612927686`
(run 108's number) and `Σ L_true/√n − 1 = 22.218056944873789` (`sqscore`'s delivered score), differing
by `0.427933668053897 = Σ (L_table − L_true)/√n`. There was never a scoring discrepancy — the first
number was the score of the *model* table. `--write` set `L` to the true side, kept `L_model`, moved the
provenance to `table.meta.json` (a `_meta` key would break `face_slide.score_of`), and the re-audit
reports 0 stale rows and a gap of 0 with `sqscore` and `record_guard` green.

**2. The ε(gap) containment guard.** `ε = 2·max|θ − word(θ)|` bounds `|true side − model side|`
(the half-extent is 1-Lipschitz in the angle and the side is a difference of extrema). A candidate is
promotable only if it agrees with the true side within ε, is overlap-free at 40 digits, and its true
side is strictly below the row's true delivered side. The bars are now n = 11 `3.871321392`, 17
`4.668646323`, 18 `4.819512197`, 29 `5.926803177`, 330 `18.678566016`. Run 109's artifact is refused
automatically (model `18.692487647`, true `18.692915843`, ε `1.38e−2`: inside the budget, but it has
overlaps at true angles and does not beat the delivered true side); the rigid/re-orientation searches on
11/17/29 re-run with the guard give 0 model wins and 0 promotions.

**3. Coupled position-and-angle relaxation.** `relax_angles.py` frees every `(Δx, Δy, Δθ)`, relaxes the
whole row by L-BFGS-B on `side + 1e6·Σ penetration²` (3 restarts from the delivered pose), projects back
to feasibility by minimising overlap alone, and measures survivors at 40 digits. Result: every shrunk
state has 11–41 overlaps, and the best **legal** state is worse than delivered on all four rows —
n = 11 `+9.3e−8`, 17 `+3.7e−7`, 18 `+2.8e−7`, 29 `+2.0e−3`. The delivered packings sit on the
feasibility boundary; the three small rows are locally optimal to `~1e−7` under coupled moves, n = 29
only to `2e−3`. None of the four is near word-exact (offsets 0.084–0.364 rad), so nothing here could be
certified even if it had improved — discovery and certification stayed separate.

Checks: `true_geom --selftest` 3 controls; `reconcile_table --selftest` 2; `relax_angles --selftest` 2;
`semantic_pack --selftest` 4; `face_slide` 4; `observer_chain` 6; `cand106` 5; `cand105` 5; `rat47` 4;
`rat47pos` 5; `rat47law` 5; `landscape65` 6; `qsqrt2` 11; `verify_certificates --selftest` 11
mutations; `--certificates` 7 shipped; `glm_wheels --selftest` 32; `--audit` **596 functions, 0 naming
`float`** (semantic_pack 36, face_slide 27, true_geom 7, reconcile_table 6); `sqscore` guard OK
22.218056945 / 553 beats; `record_guard.py` OK; README/STATUS run-history line byte-identical.

**No row changed, no score claimed, `submission.csv` and root `WHITEBOARD.md` untouched.**

Entries `71-RECONCILE-AND-RELAX.md`; records `31`–`70`.

## Run 111 — n = 29 gets its definitive push, the ten loose-gap rows are screened, and doc 72 collates the phase

The only row with a loose legal gap left over from run 110 was n = 29 (`2e−3` against `1e−7` elsewhere),
so it got the constrained treatment: a hinge that punishes the side for exceeding a target instead of
rewarding smallness, six targets from `1e−4` to `4e−3`, up to four restarts each, projection to
feasibility after every attempt, and `true_geom` at 40 digits as the only judge. **No legal state beats
`5.933833464`** — the best is `5.933929467`, `9.6e−5` worse, and the ladder is monotone in its target,
which is the classic signature of a local minimum approached from above.

The screen put the same ladder on doc 69's ten highest-slack rows. Every one has a positive legal gap in
one band (`6.2e−5 … 3.3e−4`), with n = 29 in the middle: there is no uniquely loose row left to chase.
And the band is schedule loss, not structure — n = 11, 17, 18 collapse to `+9.3e−8`, `+3.7e−7`, `+2.8e−7`
under run 110's stronger schedule, and the ladder beats the general schedule on the six bigger rows
(`+1.95e−3 … +3.19e−3`). A ladder gap is an upper bound on the local room, never a measurement of it.

`72-SYNTHESIS-AND-NEXT.md` then collates runs 60–111: the 552 certified rows, the exact carriers
(`Q(√2)` eight words, `Q(√7)` family, one `Q(√5)` instance), the integer-scaled SAT verifier with its
mutation controls, the face-squeeze bounds (`−4.62e−10`, `−2.16e−10`, 31 of 33 worded rows), the ε(gap)
containment guard and the reconciled table (357 rows, `22.645990612927686` vs `22.218056944873789`), plus
the six architectural invariants (untrusted discovery, float-free certification with 596 audited
functions, one scorer, two independent witnesses, bounded claims, guarded prose) and four falsifiable
promotion criteria (C1 certifiable pose, C2 strictly smaller true side with zero overlap, C3 gain above
`ε` and the rendering noise, C4 the metric moves) with three row-selection rules (R1 word-exact, R2 a
loose legal gap on a certifiable row, R3 a named new mechanism).

Checks: `relax_angles --selftest` 2 controls; `true_geom` 3; `reconcile_table` 2; `semantic_pack` 4;
`face_slide` 4; `observer_chain` 6; `cand106` 5; `cand105` 5; `rat47` 4; `rat47pos` 5; `rat47law` 5;
`landscape65` 6; `qsqrt2` 11; `verify_certificates --selftest` 11 mutations; `--certificates` 7 shipped;
`glm_wheels --selftest` 32; `--audit` **596 functions, 0 naming `float`**; `sqscore` guard OK
22.218056945 / 553 beats; `record_guard.py` OK; README/STATUS run-history line byte-identical.

**No row changed, no score claimed, `submission.csv` and root `WHITEBOARD.md` untouched.**

Entries `72-SYNTHESIS-AND-NEXT.md`; records `31`–`71`.

## Run 112 — constructive pattern seeds: macro-block topologies lose, and the deficit says why

The repair route is exhausted (run 111), so this run stopped perturbing the delivered pose and built
packings from scratch: `pattern_seeds.py` reads only `n` and `L_delivered`, synthesises seeds from
macro-blocks — arrays of unit squares at a fixed angle — places them with a shelf packer over bounding
boxes (so overlap-freedom is structural), and judges every seed with `true_geom` at 40 digits.

Four topologies: **A** two 45° blocks with a bent transition strip and an upright residue, **B** an upright
core with four 45° perimeter bands (the L-cut frame), **C** Pythagorean lattices at arctan(3/4), (5/12),
(8/15), (2/1), and **D** an upright near-square reference with no tilt at all. Nine rows: the open
residue rows above 324 (680, 733, 845, 904, 971 — all non-word, so no exact sentence exists for them) and
the four highest-slack mid-range rows (29, 41, 53, 55).

**No family beats the delivered side on any row.** D loses least (`0.68–2.26%`), then B (`3.6–12.2%`),
then A (`6.8–31.9%`), then C (`42–48%`); all 36 seeds with a result have zero `true_geom` violations at 40
digits. Criterion C2 fails everywhere, so nothing is lifted and `submission.csv` stays untouched.

The interesting part is the exact decomposition `void = (Σ bbox areas − n) + (L² − Σ bbox areas)`, i.e.
tilt waste plus packing waste, recorded per family and row. A `k×k` block at 45° has a bounding box
`k√2` on a side — **it doubles its area** — and a `b×b` block at a Pythagorean angle costs
`b²(c + s)²` (1.96 at 3-4-5, 1.83 at 8-15-17, 1.710 at 5-12-13). A tilted *body* therefore pays its area
twice, which caps family C at nothing better than `0.71 n` of box waste before any placement, and which
is why the optimiser's best A and B seeds on every large row use almost no tilt (`k = 2`, `band = 1`,
tilt waste exactly `8` and `4`) and then lose to D by packing waste from the extra boxes. The delivered
table tilts only a *one-cell boundary staircase*, where the surplus triangle is perimeter-order: body
tilt costs its area again, edge tilt costs a strip. Family D's remaining `1.0–2.3%` is pure shelf
non-nesting (49–57 void units at n ≥ 680 against a delivered void of 26–33), not tilt.

`73-PATTERN-SEEDS.md` records the tables, the decomposition and the three next steps worth trying: a
boundary-staircase family E (the only topology whose tilt is perimeter-order, and the shape the delivered
table actually uses), a nesting packer, and — before any of it can promote — an interval-arithmetic
verifier, because the open rows are non-word and C1 blocks any float placement.

Checks: `pattern_seeds --selftest` 5 controls; every other selftest green; `glm_wheels --audit` **596
functions, 0 naming `float`** (`pattern_seeds` is discovery-side and deliberately outside the audit, like
`relax_angles`); `sqscore` guard OK 22.218056945 / 553 beats; `record_guard.py` OK; README/STATUS
run-history line byte-identical. **No row changed, no score claimed.**

Entries `73-PATTERN-SEEDS.md`; records `31`–`72`.

## Run 113 — the boundary staircase gets its verifier and its packer, and two laws close the fringe route

Doc 73 §5 named three next steps — a rational-interval verifier, a corner-nesting packer, a boundary
family E — and this run executes all three on the same nine rows (29, 41, 53, 55, 680, 733, 845, 904,
971). **No row changed; `submission.csv` and the root `WHITEBOARD.md` are untouched**, because nothing
beats `L_delivered` and C2 fails everywhere.

`scripts/interval_verifier.py` is the second judge doc 72 §5 C1 asks for: a strictly float-free
(`fractions.Fraction`, roots by `isqrt` on scaled integers) interval verifier that brackets every
direction — axis word exact, quarter word `sqrt 2` to 80 bits, rational slope `(q, p)/sqrt(p^2 + q^2)`
exact when the norm is a square — checks all **4N wall bounds** against a declared rational side and, for
every pair, a separating axis with a **strictly positive rational lower bound** on the slack (the two
axis-aligned directions first, since SAT holds on any axis, then the four cell axes). It refuses an exact
contact as `inconclusive` — an enclosure straddles zero — which is why every construction carries a `1e-9`
hairline, and it certifies an overlap when the best axis' upper bound is negative. **7 controls**,
including both refusals; and it is now **inside the float audit** (`glm_wheels --audit` 613 functions, 0
naming `float`, 596 before).

The shelf is replaced by `nest_pack`, corner insertion over bounding boxes: every free corner of every
placed box is a candidate and the lowest-leftmost fit wins, so a residue strip sits beside the block
instead of under it. **A gains `1.0` of side on eight of nine rows, B gains `0.24–0.88`**, B now ties the
upright reference D on six rows — and the run corrects doc 73 §4 in the same breath: for upright blocks
the boxes *tile*, so `sum bbox = n` and `L^2 - sum bbox` is the container's own leftover (49, 51, 55, 57,
53 units on 680…971), unchanged by any packer. The residual was never shelf loss; it is `ceil(sqrt n)`.

Family E is an upright core plus one-cell tilted cells seated along one or two walls, and its seats are
**derived**: two cells of the same direction at the same outward coordinate need `Delta >=
1/max(|c|, |s|)` along the wall (the binding term is the cell's own `u`/`v` axis), and the first outward
position that clears a solid axis wall column puts the fringe's outer edge `|c| + |s|` past the wall.
Both numbers are `>= 1`, with equality only at the axis limit, so a tilted fringe cell is never denser
than the axis column it replaces (control 10 asserts it over all sixteen slopes). Consequence, measured
at the delivered side on every row: **not one fringe cell fits** — the smallest protrusion is `1`, and
`L_delivered - floor(L)` is 0.56–0.95 — so E's fill is exactly `floor(L)^2` and the shortfall is
`n - floor(L)^2` = **4, 5, 4, 6, 4, 4, 4, 4, 10 cells**. All nine fills are certified by the interval
verifier strictly **below** `L_delivered` (3,844 wall bounds and 461,280 pairs at n = 971, 0 violations, 0
inconclusive, tightest certified slack `1e-9`), so the losses are proved rather than measured.

The `t = 1/q` sweep at n = 971 (core `30 x 31`, one column of room) is the requested denominator test:
**952 cells at `q = 1` → 958 → 959 → 960 → 961 at `q >= 7`**, void 51.5 → 42.5, monotone and saturating
exactly where the tilt vanishes — at `q = 7` the fringe *is* the 31st axis column, and all 9 cells the
45-degree staircase could contribute are recovered by removing it. With that, two statements close the
route: **T1**, an all-lattice pose of `n` cells needs side `>= ceil(sqrt n)` and all nine target rows beat
the grid, so no integer-lattice construction can pass C2 on them; and **T2**, the one-cell wall fringe is
dominated by the axis column it replaces. The remaining route is **interior** tilt — the delivered rows
carry 56 tilted cells in a *band* at `3-4-5` and `1/3`, not at a wall — which is what run 114 would have
to name.

Checks: `interval_verifier --selftest` 7 controls and `--check` on the 9 stored recipes (`certified`, 0
refused); `pattern_seeds --selftest` 10 controls; `true_geom` 3; `reconcile_table` 2; `semantic_pack` 4;
`face_slide` 4; `observer_chain` 6; `cand106` 5; `cand105` 5; `rat47` 4; `rat47pos` 5; `rat47law` 5;
`landscape65` 6; `qsqrt2` 11; `verify_certificates --selftest` 11 mutations; `--certificates` 7 shipped;
`glm_wheels --selftest` 32; `--audit` **613 functions, 0 naming `float`**; `sqscore` guard OK
22.218056945 / 553 beats; `record_guard.py` OK; README/STATUS run-history line byte-identical.
**No row changed, no score claimed.**

Entries `74-BOUNDARY-STAIRCASE.md`; records `31`–`73`.

## Run 114 — the grid wall is priced, not argued with: 0 rows behind the record, 0.03 % of a cell short

Asked to stop polishing the rows that are already beaten and attack the 447 un-optimised grid rows, this run
measured the wall first and searched second.

**Benchmark.** `published_census.py` carries the Squares Project best-known list of 2026-10-20 (all 324
cases, 5 dp, tolerance `2e-5`) and compares it with the delivered rows: **303 equal, 21 better, 0 behind**
(the 21 are worth `0.006414` over the record). The catalogue therefore holds no score: `s(12) = 4` is
conjectured with floor 3.9715, `s(k^2 - 3) = k` is proved for `k >= 6`, and the 2026 improvements are already
in the table (n = 29 `5.93384`, n = 86 `9.82054`, n = 183 `13.99959`, n = 232 `15.76418`).

**What an unbeaten row costs.** With `n = k^2 - j`, a packing beats iff its void `V = L^2 - n < j`. The
frontier rows of the 30 bands spend **87–99.9 %** of that budget (`n = 183` at `0.999`, `n = 655` at
`0.999`), so the next row up must give up a median **0.72 unit^2** of empty area, 0.45–0.99 at the large
bands. This retires the "effort-limited frontier" reading: it is a geometric wall, and the published record
agrees with it wherever it reaches.

**Where the last 0.03 % is.** `void_insert.py` finds the largest square that fits in each frontier pose's free
space exactly (separating axis over four edge normals; controls: an emptied `3 x 3` corner reads 1.0000, a
full one 0.0000). The answer is bimodal — **0.45–0.83** of a cell for `k <= 20` (a genuine void, so a
rearrangement) and **0.9994–0.9999** for `k >= 21`, where it also equals `1 - (k - L)/k` to within `6e-4` in
ten of eleven bands. These large-`k` frontier poses are **uniformly compressed `k x k` lattices**: every gap
shrinks by `(k - L)/k`, so no hole is a cell (`k = 23`, `delta = 0.010223`, is the exception: a real 0.7534
notch).

**The attempt.** `--seat` inserts a cell at the best free-space point, frees the 1–6 cells it penetrates,
hinges the container at `k - 1e-3` (so any legal seating is automatically a beat), asks for `1e-9` clearance
and runs L-BFGS-B on `3(freed + 1)` variables, judged by `true_geom` at 40 digits. Eleven bands (k = 21…31):
**no beat**. With the hinge the state lands at `k + 2e-9` with 2–11 violations and the container short by
~`4e-3`; without it the cell seats perfectly (`2e-16`) but the side grows to `k + 1.1e-4…2.4e-4`. Local
freedom cannot create 0.03 % because the compression is uniform: room taken from one hole is given back to
the next. That is also why no world record crosses these rows.

**What each campaign is worth.** Beating the next row in every band by *inheriting* the frontier's own side
(no new construction) is worth **+0.23251** — more than the 0.163635 gap to the reported leader, so the grid
campaign can pay for it at 100 % success. The **553 beaten rows** leave **15.02** score unclaimed below them;
a 1 % capture is **+0.15023** and 5 % is **+0.75113**, so 1.1 % of that room is the entire gap. The
recommendation is recorded in doc 75: the compressed-lattice rows need a *global* move that redistributes the
compression (block substitution on the `k x k` pose), not a local push; the beaten-row polish is the
guaranteed payer.

Checks: `void_insert --selftest` 2 controls (1.0000 / 0.0000); `published_census` reproduces the delivered
score `22.218056945` / 553 beats / 447 grid rows; `sqscore` guard OK; `record_guard.py` OK; README/STATUS
run-history line byte-identical. **No row changed, no score claimed, `submission.csv` untouched.**

Entries `75-GRID-WALL-CENSUS.md`; records `31`–`74`.

## Run 115 — block substitution is refuted by a theorem, and the 45° families give nothing on the unsolved rows

Two follow-ups to run 114, plus a correction.

**Correction.** The band census is **30 bands, not 29 or 31**. Run 114's loop ran `k = 2..31` and silently
dropped band k = 32 — whose frontier is n = 998 and whose next row is 999, a real target. With it in, the
inheritance bound is **+0.23251** (was 0.23207), and band k = 32 measures a free square of **0.7171**, a
genuine notch rather than a sliver, with the cheapest large-band price in the table (+0.120).

**The campaign: swap a p x q block for one holding pq - h + 1 cells at a larger pitch.** `block_swap.py`
enumerates every near-full block (1–3 holes, at least 4 cells, p <= q <= 7) of all twelve `k >= 21` frontier
poses and tests the substitute against the block's own compressed box, using the record side for the count as
the fast filter. **No block fits in any band**, and the same block is best everywhere: a **3 x 3 holding six
cells (three holes), needing seven cells in 2.9991–3.0000**. The shortfall is `2.2e-5…8.9e-5`, which is the
compression itself (`3·delta/k` predicts 3.3e-5 at k = 26 against 2.2e-5 measured), and the optimiser cannot
close it — packing seven into those boxes stalls at penetration `1.8e-8`, `2.3e-8`, `7.2e-8` (k = 26, 29, 31)
after 2500 iterations and four restarts. It is **impossible rather than hard**: `s(7) = 3` is proved, so
seven unit squares never fit below 3. Block substitution is closed on the compressed-lattice rows by a
published theorem, not by a search budget. (An unrestricted first run "won" by repacking a 7 x 7 block that
held one lonely cell — which is why the filter is stated.)

**The family question.** Do Block45, Block45Half or the ridge give even a slightly-better-than-base packing on
the 447 unsolved rows? `grid_families.py` writes the three exact count/side laws (660 members at N <= 1000,
369 of them at counts the table already beats) and uses the deletion fact — a packing of N cells covers every
`n <= N` — to take the best covering member per unbeaten row: **0 beaten, 0 at parity, 444 behind**, closest
`+0.0711` (n = 212, 242, 243, 244), 17 rows within 0.15, 43 within 0.25, median `+0.6066`, max `+0.7071` =
½√2, the ridge's own floor. So the 45° families beat the base grid **only** at counts where the table already
beats it; on the unsolved set they are 0.07–0.71 behind, and the seam cost `w >= ½√2` is the reason. One
artifact is recorded rather than hidden: the ridge at m = 1 read N = 2 at L = 1.7071 and produced a single
bogus "beat" at n = 2 until the validity floor `m >= 2` was imposed (`s(2) = 2`).

**Where that leaves the campaign.** The sliver bands are refuted (§5), the families give nothing (§6), and the
only openings left are the two notch rows (k = 23, 32; price 0.530 and 0.120, real 0.72–0.75 holes) and four
Block45 near-misses at `+0.0711` — all of which need a rearrangement, not a substitution or a local move.
The beaten-row polish remains the guaranteed payer (1 % of its 15.02 unclaimed room is 0.15023).

Checks: `void_insert --selftest` 2 controls; `published_census` reproduces `22.218056945` / 553 beats /
447 grid rows / 30 frontier bands; `block_swap` and `grid_families` rerun clean; `sqscore` guard OK;
`record_guard.py` OK; README/STATUS run-history line byte-identical. **No row changed, no score claimed,
`submission.csv` untouched.**

Entries `75-GRID-WALL-CENSUS.md` (rewritten with the 30-band table, §5 block substitution, §6 families);
records `31`–`75`.

## Run 116 — the standing card is placed (reviewed), and the re-squeeze lead is opened and controlled

**Deliverable of the request.** `DIRECTORS-NOTE.md` sits at the project top level and is the first pointer in
`README.md`, `STATUS.md` and `00-OVERVIEW.md`. It states the orientation, the "no floats" operating definition
(discovery proposes, proof promotes), the proved leverage, the open leads and the C1–C4 gate, and it carries a
review table: every number was checked against the repository. **One factual error was corrected** — the
compression statement concerns the band's frontier pose (`m* = k^2 - j*`, `j* = 18…26` at k >= 21), not
`n = k^2 - 1`, which is a frontier row nowhere in the table. Everything else (552/553 certified, 613 audited
functions, 447 grid rows, 30 bands, 303 equal / 21 ahead, free cell 0.9994–0.9999, notches 0.7534 and 0.7171,
369 family counts, `+0.0711` near-misses, `-7.89e-9` face squeeze) was confirmed with its source.

**Development step: `resqueeze.py`.** Insert a cell at the exact free-space point, then patch-coordinate
relaxation with overlapping 4.5-wide patches, sweeps in random order and a **monotone acceptance test**, the
container at `k`. The control (pose alone, no insertion) was run first and paid twice: a first version hinged
the box at `k - 1e-3` and **destroyed a legal pose** (pen 0.59, 234 violations) — the target is `k`, and the
margin was an invented impossibility; with that fixed the control reads pen `2.4e-14` (max contact `7e-8`),
side `26.0000000013`, 76 violations, establishing the floor (~`1e-8`) and the substantive finding that
**penalty descent inflates the pose to `k`**, spending the frontier's own `delta` instead of gaining room.

Runs with the insertion: k = 26 (sliver) ends at side `26.0000000013`, 79 violations, max penetration `4.6e-6`
— the sliver restated to `1e-9`; k = 32 (notch) ends at side **`31.996876`**, `3.1e-3` *inside* `k` and worth
`9.9e-5`, but with 17 violations at max penetration `9.4e-2`, having accepted `1/168` then `0/168` patch moves
before jamming. So the notch is **real room** — the side genuinely goes below `k` — and the obstruction is
combinatorial (17 pairs), not spatial. No beat, no row changed. The named next step is a hard side projection
(exact container, no penalty) plus contact-graph repair on the jamming pairs.

Checks: control run recorded above; `published_census`, `block_swap`, `grid_families`, `void_insert --selftest`,
`sqscore` guard and `record_guard.py` all re-run green; README/STATUS history line byte-identical. No row
changed, no score claimed, `submission.csv` untouched.

Entries `DIRECTORS-NOTE.md` (new, top level), `75-GRID-WALL-CENSUS.md` §10; records `31`–`76`.

## Run 117 — the k = 32 notch answered under a hard constraint, and the polish campaign priced

**Request.** Take the k = 32 notch further: hard side projection instead of a penalty, repair the jamming
pairs from the contact graph, and say whether n = 999 gets below 32 with zero overlap at 40 digits. If it
stalls, price a 1 % capture on the 553 beaten rows. Everything governed by `DIRECTORS-NOTE.md`.

**`notch32.py`.** Walls are a projection, never a penalty: after every move each cell is clamped into the
box, so any reported state satisfies the side exactly. The repair is a descent on the contact graph — the
exact separating slide for the deepest pair along its best axis, kept only if `(pairs, sumsq, deepest)`
strictly improves, deepest 12 pairs per pass. A first draft dropped the monotone acceptance test and the
sweeps exploded the pose (3 → 559 violations, max 0.58); restoring acceptance and fixing degenerate slide
algebra made the instrument trustworthy. Recorded, because that is the second time in two runs a control
saved the result.

**Answer: no.** Start = frontier 998 at 31.986238620 plus an inserted cell; the finer scan (140 x 33, six
refine rounds) finds a **0.8394** free square, not the 0.7171 of run 114, so the cell is 0.1606 short. It
bites 3 pairs at 0.0939. 23 passes of exact slides move the deepest bite only `9.392e-2 -> 9.389e-2`; then
no single slide helps, and a constrained sweep accepts **0/168** patches. Final at 40 digits:
side `31.99687592223010338076867830301645689164` (`3.124e-3` inside k, worth 9.9e-5) with **6 violations**.
The three pairs are mutually blocking; 1.4e-2 of side slack cannot absorb a 9.4e-2 bite. No candidate, no
C1/C2, `submission.csv` untouched.

**Polish pricing (`polish_pricing.py`).** A 1 % capture needs `dL = 0.01(k - sqrt(n))` per row:
**0.00399 - 0.00984, median 0.00708** — against run 111's measured legal-gap band `6.2e-5 - 3.3e-4`.
**0 of 553 rows** need less than 3e-3; every row needs more than the entire band. Best-case polish ceiling
(every row moves by 3.3e-4): **+0.00999**; band floor: +0.00188; face-squeeze: 2.7e-8. So 1 % (0.21742 for
one pp of `e`, 0.15023 for 1 % of the room) costs **21.8x the whole campaign**, and the honest ceiling of any
polish is about +0.01 — one sixteenth of the 0.163635 gap. Cheapest rows are the low-capture ones
(e < 0.1: 80 rows, 0.0202 worth, dL median 0.0047), still 14x the band.

Checks: `sqscore`, `record_guard`, `void_insert --selftest` re-run green; README/STATUS history line
byte-identical; no row changed, no score claimed. Entries doc 75 §11-§12; records 317-318.

## Run 117 (second pass) — the counts reconciled, the ceiling measured, and anchors as commands

**Request.** Reconcile doc 75 §11's 3-vs-6 and scope the k = 32 "no"; measure the polish ceiling with the
hard-projection repair on real rows; build `scripts/anchor_chain.py` on the GLM's stepwise contract with a
certified exact row and a refusal control; add it to `--audit`; log in doc 77. Governed by DIRECTORS-NOTE.

**Reconciled.** Not two answers: the repair's screen counts pairs with penetration > 1e-9 (3, deepest
9.389e-2); `true_geom.check` counts every exact slack < 0 (6). The extra three are near-tangent, between 0
and -1e-9. Same gap at scale in the polish sample (n=507: 68 by the screen, 119 at 40 digits). The "no" is
now scoped in doc 75 §11 and doc 77 §2 to one insertion point (0.8394 free square, 140x33 + refine), one
move set (exact single-cell slides + 4.5-wide patch descent), container exactly 32.

**Measured.** `polish_ceiling.py` shrinks a row's own container by delta, clamps (hard projection), repairs,
judges at 40 digits. 12 stratified rows, k = 17..32: **every ceiling 0.00000** — no row closes even at
delta = 3e-5, each stalling in one or two passes. Mechanism: zero-clearance poses overlap everywhere at
once under a clamp and have no slack to trade. So the polish ceiling is 0, not the +0.00999 the band
comparison allowed and not the 0.15-0.22 a 1 % capture is worth. Caveat recorded: whole-box clamp is the
worst case for a tight pose, so the claim is about this instrument.

**Anchors.** `anchor_chain.py` bridges `glm_universal.reasoning.stepwise_script`: a Step carries the command
in both columns plus the count as its exact value, and is admitted only when `step_check` AND an exact
Q(sqrt 2) placement gate pass (no overlap, contacts exactly 0, walls exactly on the container, requirements
earlier). n = 10 reconstructs exactly: 10/10 admitted (4 ANCHOR_CORNER, 4 PROPAGATE_SLIDE, 2 STACK_BLOCK),
side exactly 3 + 1/2 sqrt2, zero overlap, contact graph 11 edges, cells 3 and 7 wall-only (the pinwheel).
Refusal control: cell 1 moved 1/4 into cell 0 is refused for the geometry, exact slack -1/4. Two bugs were
caught by the controls (a doubled requirement index, and a first control refused by an index mismatch rather
than geometry) and are recorded in doc 77 §4.

**Verdict on the project's question.** As a certificate language, exactly yes: a legal packing is a chain of
anchor commands with exact per-step admission and exact refusals. As a generator, no: every command is read
off a finished pose, and the chain refuses where a search is (a cell touching no wall and no placed cell).
It is a verified transcript, not yet a solver.

**Checks.** `anchor_chain --selftest` green; `chain_check` green; `glm_wheels --audit` 632 functions, 0
offenders (anchor_chain 19); `sqscore`, `record_guard`, `void_insert --selftest` green; README/STATUS history
byte-identical; no row changed, no score claimed. Entries doc 77 (new), doc 75 §11; records 319-320.

## Run 118 — the boundary control closes the polish ceiling, and the anchor grammar goes forward

**Request.** Add the boundary-only clamp control across the same 12 rows (doc 77 §3 caveat); take
anchor_chain from transcript to constructor — a Q(√7) row as an admitted chain, and a forward
goal-directed search at a target L, tested on a small exact target and the n = 212 Block45
regime; log in doc 78; keep every guard green. Governed by DIRECTORS-NOTE.

**Boundary control — the loophole is closed.** `--control boundary` shrinks the box by delta and
translates only the cells protruding past the shrunken wall, each by its exact minimal amount, then
runs the identical repair and the same 40-digit judge. 12/12 rows, all three deltas: **ceiling
0.00000**, extrapolated +0.00000. Both initialisations fail at delta = 3e-5 on every row, so the
ceiling is a property of the poses and the move set, not of the clamp. **Local polish is closed.**

**Q(√7).** anchor_chain is field-generic: n = 18 rebuilds from coords (a+b√7)/q, q <= 32 (worst read
1.8e-9), with directions axis and the Ring word ((1+√7)/4, (√7−1)/4). 18/18 admitted (4 corner, 6
slide, 8 stack), side exactly 7/2 + 1/2√7, zero overlap, chain_check green. Same commands, same two
gates, second field.

**Forward settler.** `settle(n, L, field)` admits determined anchors only at clearance >= 0, exact
refusals, backtracking. n = 4 at L = 2: 4/4, exact span 2. n = 5 at 2 + 1/2√2: **4/5, DFS exhausted
at 221 nodes** (not a cap) — the optimal fifth cell closes on two non-frontier cells and the
generator only closes on the frontier, so the missing command is exactly **two-parent STACK_BLOCK**.
n = 212 at L = 15: 14 cells in a 5.5-wide corner, frontier dies; no answer within 900 s, reported as
no answer within budget, not as impossibility.

**Verdict.** A verified transcript plus a partial constructor: it settles corner-and-stack targets
exactly and is provably unable to reach the proved 5-cell optimum with one-parent closure. To settle
at grid scale the missing command and a best-first order are required.

**Checks.** anchor_chain --selftest (28/28 anchors, both fields, refusal at exact slack −1/4);
chain_check green on both rows; glm_wheels --audit re-run after the refactor; sqscore, record_guard,
void_insert --selftest green; README/STATUS history byte-identical; no row changed, no score
claimed. Entries doc 78 (new), doc 77 §3; records 321-322.

## Run 119 — the n = 5 claim made genuine, and the two-parent command added

**Request.** Re-run the n = 5 exhaustion with no per-node candidate cap and no node limit, confirm or
correct doc 78 §3, then add the two-parent STACK_BLOCK and retest. Governed by DIRECTORS-NOTE.

**Re-test.** With caps and the `[:12]` truncation removed (state-deduped DFS): **4/5, tree exhausted,
69 nodes / 68 states**. The claim holds; the count is corrected from 221 (an artefact of the capped
bookkeeping). Doc 78 §3 rewritten.

**Diagnosis.** The closure generator *does* produce the optimal fifth cell from the optimal four corner
cells; the search never reached that state. Two causes: (a) no two-parent command; (b) ANCHOR_CORNER was
offered only at depth 0 after the rewrite, so the four-corner state was unreachable and every branch died
at depth 1.

**The command.** Two tangency equations are linear in the centre, so the candidate is solved exactly (2x2
in Q(sqrt 2)) over the axis pairs of both parents *and the candidate* — the 45 degree cell touches two axis
cells along its own axis. Also tried and abandoned: free enumeration of the 2-D field lattice (~10 000
points within radius 3/2; 65 s for 19 nodes) — solving the constraints is the right algorithm.

**Retest.** n = 4 at L = 2: 4/4, span exactly 2. n = 5 at 2 + 1/2√2: **5/5**, span exactly the target,
248 nodes / 260 states, settling the known optimum (four corner cells + (1 + 1/4√2, 1 + 1/4√2) at 45).
n = 212 at L = 15 is only a budget-limited probe (node cap 25: 25 cells, full 15 span, not
terminated); the earlier "14 cells in a 5.5-wide corner" was pre-fix and is withdrawn.

**Verdict.** The constructor now settles the proved 5-cell optimum exactly; the missing-command diagnosis
was right. Guards green (re-audited), no row changed, no score claimed. Entries doc 78 §3; records 323-324.

## Run 120 — constraint intersection, two audited speedups, and n = 6, 7

**Request.** Replace the two-parent sweep with direct exact-constraint intersection; add a cheap bounds
pre-filter and a failure-pair memo; run the settler on n = 6 and n = 7 at best known sides with honest stall
diagnosis; log in doc 79. Governed by DIRECTORS-NOTE.

**Generator.** Corners need no solve; wall+contact is one division (the wall pins a coordinate and the
tangency is linear in the other); two-parent STACK_BLOCK is a 2x2 exact solve over both parents' axes and the
candidate's. The lattice sweep is gone from the closure path.

**Speedups, measured.** (a) Integer-only sqrt(d) bounds prefilter: skipped 98.3% of pairs at n=5, 99.4% at
n=6 and n=7. (b) Failure-pair memo: 86.1% hits at n=5, 88.0% at n=7. Combined effect on the comparable run:
n=5 settlement 248 nodes / 140.8 s -> 69 nodes / 30.6 s (3.6x fewer nodes, 4.6x faster).

**n = 6 and n = 7.** Both settle completely at their best known sides: n=6 at L=3 -> 6/6 (17 nodes, 43
states, 8.75 s), n=7 at L=3 -> 7/7 (128 nodes, 159 states, 102.6 s), spans exactly 3 = the proved optima.
**No stalls**, so no exhaustion/missing-command/budget diagnosis applies to either. The only stall in the
table is frontier-mode n=5, which remains genuine exhaustion (69 nodes expand to 68 states, stack empties).

**Stated limit.** Settling 6 and 7 at L=3 exercises the 3x3 grid regime, where every cell is corner- or
contact-closed; it does not test the grammar where the grid fails. That remains n=212 (budget-limited probe)
and the unbeaten rows (no attempt yet).

**Checks.** anchor_chain --selftest green (both fields, refusal at -1/4); --forward wrote its JSON;
glm_wheels --audit re-run; sqscore, record_guard, void_insert --selftest green; history byte-identical;
no row changed, no score claimed. Entries doc 79 (new); records 325-326.

## Run 121 — attributable speedup, dead code out, an unbeaten row, and a CLI

**Request.** Fix the confounded doc 79 §2 comparison by re-measuring the old generator at the same width and
ordering; trim dead code; point the settler at an unbeaten grid row with an honest settle/exhaust/missing
verdict; give the project a CLI. Governed by DIRECTORS-NOTE.

**Speedup, corrected.** The old sweep generator is back as `mode="sweep"`. At width 8 with contact-first
ordering: sweep 60 nodes / 25.8 s, intersection 69 nodes / 31.2 s. So the 248 -> 69 nodes gain was the **width
and the ordering**, not the generator: for the same generator, uncapped/unordered 248 / 140.8 s vs capped at 8
with ordering 60 / 25.8 s (4.1x fewer nodes, 5.5x faster). The intersection generator is marginally slower
(more raw candidates: 75 353 vs 53 364) and buys derivation instead of guessing. Doc 79 §2 rewritten; the
prefilter/memo rates stand as measurements, their isolated share is not claimed.

**Dead code.** `_offset_cache`/`_OFFSETS` and the unused `lattice=` argument removed; `determined_candidates`
kept only as `mode="frontier"` because its closure is evidence.

**Unbeaten row.** `sq_cli.py row 12 --cap 20`: n = 12, k = 4, delivered 4.0000000015, unbeaten -> settled 8/12
in 21 nodes, with **73 determined anchors still available** at the deepest state. Verdict: **budget/order
limit**, not exhaustion, not a missing command. n = 23 (k = 5) produced no result in 900 s: **throughput-
limited**, state space nowhere near closed, candidates still being produced — cost per node, not grammar.

**CLI.** `scripts/sq_cli.py` with `settle`, `row`, `verify`, `audit`; exact sides typed as `2+1/2r2`. Verified
by running it.

**Checks.** anchor_chain --selftest green; sq_cli verify 10 (side 3 + 1/2 sqrt2, 10 anchors, 0 overlaps);
sq_cli audit 106 functions 0 offenders; glm_wheels --audit re-run; sqscore, record_guard, void_insert
--selftest green; history byte-identical; no row changed, no score claimed. Entries doc 80 (new), doc 79 §2.

## Run 122 — time-budgeted rows, and the honest scaling answer

**Request.** Stop `sq_cli.py row` burning a budget and reporting nothing: give it best-effort partial progress
within a wall clock, then say whether the anchor line can realistically reach the ~990-cell unbeaten rows.

**Time budget.** `settle(..., progress=PATH)` checkpoints the deepest placement whenever it improves, each cell
as exact `[x_a,x_b,y_a,y_b,c_a,c_b,s_a,s_b,dir,i]` text; `row --seconds N` runs it in a child, kills at the
deadline and reloads the checkpoint into a gated partial pose. Round trip verified (n=5: 5 cells, span
2+1/2 sqrt2, 0 overlaps, 69 nodes / 87 states).

**Measured with the budget.** n = 12 in 45 s -> 8/12, span exactly 4, 0 overlaps, **73** anchors available.
n = 23 in 150 s -> 11/23, span exactly 5, 0 overlaps, **129** anchors available. Both are budget/order limits,
not exhaustion and not a missing command — the distinction is now observable, where the 900 s silence destroyed
it.

**Scaling answer: no.** candidates scale with placed count squared: pairs/node 9 (d=4), 175 (5), 270 (6), 381
(7), i.e. ~7d^2 at ~388 pairs/s -> d=990 is ~17 700 s per node, and a single non-backtracking 990-cell chain is
a 4 866 h (203-day) floor, before refusals (measured 3-18 nodes per cell, so 3-18x worse). And speed is not the
binding problem: every settlement lands exactly on its target, the unbeaten rows are 1.5e-9 above the grid, and
reproducing the grid is worth 1e-9 per row against the 4e-3-1e-2 the score needs. The line is a certifier, not
a scoring instrument; it is kept as `sq_cli verify` and not scaled. Next cheapest test named: a per-row
non-closure perturbation over 20 rows at ~10 s each.

**Checks.** round trip exact; both row probes reported with verdicts; verify 10 and audit clean; anchor_chain
--selftest, sqscore, record_guard, void_insert --selftest, glm_wheels --audit green; history identical; no row
changed, no score claimed. Entries doc 81 (new).
