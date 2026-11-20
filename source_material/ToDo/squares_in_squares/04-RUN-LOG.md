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
