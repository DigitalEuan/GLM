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
