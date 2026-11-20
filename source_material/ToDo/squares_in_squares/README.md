# Squares in Squares — Verified Constructions, Leech-Lattice Analysis, and the Rotated-Block Program

This repository is a reproducible working state of a
Kaggle *Squares in Squares* project (pack n unit squares into a minimal
square container; 1000 puzzles, n = 1..1000; score = Σ(L/√n − 1), lower
is better), extended with a machine-verified Leech-lattice layer and a
fully enumerated rotated-block family program.

**Where this project began.** It is a branch of the GLM study
(github.com/DigitalEuan/GLM): the *Geometric Language Machine*, foundations include: use exact Arithmetic; no floats/rounding, no SHA-256, no random or disruptive operations anywhere possible - specifically within computation,
number-theory evidence-based (TAX/NRCI, Y/Q/B constants, delta-sigma as the
canonical carrier for irrationals). Part of the GLM project is a concept generator — the cent compiler v12_2_ext, it has "wheels" of data that spin to find operational paths regardless of domain 
(github.com/DigitalEuan/squares_in_squares/tree/main/workspace/cent_compiler_v12_2_ext).
Two of those wheels are this project's engines: **W36** (Numerical SAT
Substrate — the exact algebra that became packlib's SAT verifier) and
**W37** (Viscoelastic Settling — the creep/pressure ramp that became
the "pressure-settling engine" - the engine concept the cent_compiler generated). Every construction this project
produces is a wheel certificate (W36); every search it runs is a wheel
settle (W37). The record from start to finish — lineage, engines, sources,
operating loop — is the system record in `STATUS.md`. More operatiors and more/denser wheels should produce more concepts, I suspect the Python libraries would make excellent wheels - reduce to cent_compiler '¢' primitives and exact Arithmetic then confirm with Lean4.

**The framing, and its audit.** Read as a *Geometric Language Machine* sentence, a packing is a word over an exact relation alphabet, and score moves when the alphabet moves rather than when a search runs longer. That reading was proposed for the front page and is now checked claim by claim against the delivered table in `31-GLM-ALGEBRAIC-WORDS.md`: the three closed pile-of-words runs hold as recorded, four of the framing's figures do not, and one external result — Khalili and Gharabaghi's reported `s(k²−5) = k` — is entered as reported, with a 25-row contact check that contradicts nothing.

**Room, measured.** Run 69 replaces the phrase "wall margin" with a definition —
the side between a delivered row and the area wall, `mu = L − √n`, priced as
`rho = mu/√n` — and computes it for all 1000 rows (`32-WALL-MARGIN-AND-BRANCH-ROT.md`).
n = 184, 656 and 819 are ordinary mid-table rows at the grid (side-margin ranks
517/604/610, score ranks 159/637/702); the largest margins, and the four largest
score values in the table, belong to rows the record calls proved optimal. The row
the fixed rule does select, n = 18, was then searched over 5,560 branch-assignment
× rotation cells; every one refused, with the exact gate as the only judge.

**The cent contract, implemented.** Run 70 took the cent-compiler's
`jamming_branch_escape` contract and its T1-dislocation card (`33-CENT-CONTRACT-T1-GLIDE.md`)
and implemented the one thing they add — flipping *which SAT axis and which owner*
separates a contact, not just its angle — then ran it at n = 18, 20 and 30: 7,803
cells, 0 feasible, 0 gated. Four of the cards' figures do not survive the check
(0.76 % holds only at n = 1000, s(5) is 2.707107 and proved, "0/8" is run 41's,
"run 50" does not exist), and their n = 5 test case is ill-posed.

## Current results (Run 91, 2026-11-19; last score move run 47)

| Quantity | Value |
|---|---|
| Submission score | **22.218056945** (rounded **22.218057**; grid ceiling 28.937670, improvement −6.719613) |
| Puzzles beating the plain grid | **553 / 1000** |
| Leaderboard best (reported) | 22.0544214515 → gap **0.163635** |
| Certification | 1000/1000 packings SAT-verified + 500,500-row CSV round-trip (0 issues; Run 36 record) |
| Golay/Leech verification | 28/28 + 14/14 assertions, integer-exact |
| Algebraic certificates | 1169 (7 angle families + surveys + run-11 census) |
| Proven-optimal rows | 156 (152 tied at grid + 4 below-grid: s(5), s(11), s(17), s(19)) |
| Latest score move | **Run 47 audit re-score**: 22.642386651 → **22.218056945** (−0.424330); guarded by `sqscore.guard` |
| Latest session | **Runs 69–76, margin + three discrete searches + the dimension by proof + the branch space at frozen angles + the near-miss spent, the seam offset measured, and the row census** — wall margin on 1000 rows; 5,560 word cells at n = 18; 7,803 branch-flip cells; 6,684 flips over the 42 open rows (0 seeds); cubes-in-a-cube LP with an exact rational gate, then `L_d(n) = ⌈n^{1/d}⌉` **in the axis-parallel class** by a sub-box count (2D n = 5 already beats it by rotation: 2.707107 < 3); a 2D branch-space MILP with our own LP-guided B&B — its relaxation is empty at the root (the bound is the largest square's own extent), so it closes only n ≤ 3, while the same exact leaf closed **87,767 structures within two branch changes for 0 improvements** (nearest competitor +4.48e−3 at n = 11 — run 75 identifies it as the single flip of pair 7–8, certified at +4.475e−3, a dead end as a construction, and fixes the gate call that could never have reported a gain); `--milp` retired; W1 started: the n = 290 two-lattice seam's offset measures `18 − (25/2)√2` in x−y and a shift costs exactly the shift, so the seam is tight; run 76's row census splits the 447 grid rows into 60 settled by a published bound (26 of them above n = 324) and 387 open, 247 of those above 324 in one residue band (m ≥ 21), and certifies the delivered side as the frozen-angle optimum on all 87 beating rows with n ≤ 200; **no row changed**; the 553 beats are exactly the rows containing a rotated square (447 axis-aligned rows, all at `⌈√n⌉`); run 77 finishes the frozen-angle certificate — **150 of 150** beating rows at n ≤ 324 (the whole catalogue block, not a slice) and **41 of 41** in 325 ≤ n ≤ 400, union **191 of 191** — folds it into the one row ledger (60 closed by a published bound, 191 certified, 362 beat-open, 387 grid-open) and shows the gap accounting cannot attribute the 0.163635 gap (conceivable total 22.028443, 135×); run 78 aims a construction at the band — the 247 open rows above 324, contiguous in the residue one block per k, each block starting one past that k's last record — by extending each record by one square at six orientations: **0 of 14**, the best placement overlapping by 0.094–0.142 (largest empty square 0.86–0.91, and 70 local LPs infeasible), so no band row is one square from the records we hold; and gives every row its exact algebraic side (447 in ℚ, all exactly `⌈√n⌉`; 100 in ℚ(√2); 4 Pythagorean; 449 recorded as not expressible), with 0 disagreements against the scorer; run 79 builds the tilted boundary layer from scratch for the first open row of each of the 14 k-blocks — a trimmed axis grid plus two `j×j` 45° lattice blocks, certified through `finalize` then the exact gate — and gets **0 of 14** with capacity **m ≤ 0** at every k (the best gated build is the plain `k×k` grid at side k; one diamond nets `k²−2`; at the n=326 record's own side the clean build carries 290 against the grid's 324 and the polished record's 326, so the diamond trade is negative by area and only polishing recovers it — the 54 clean records top out at m = 13, the band starts at 21); run 80 asks whether any solve we hold refines further and gets **0 of 553** — every beating row refuses a wall-ring shrink even at 1e-7 with up to 200 squares free, the 191 rows certified at 1e-6 included — and finds the table is a **60-parameter object**: 969 of 969 non-square rows sit exactly at their residue class's causal chain value (0 open above `finalize`'s 2e-9), so `d(total)/dδ*(r) = W(r)` (3.6453 for r=1 over 31 rows), the cascade channel is already applied everywhere, and the 23 classes still at δ = 1 are the band's residues; run 81 asks the reverse question of the band — the **space around** each of the 14 anchor records, the largest empty square over all orientations in closed form (SAT), three boxes, 17 orientations: **0.695–0.807 of a unit**, always at 0°, falling to 0.569–0.632 at 45°, so the deficit to one more unit square is 0.19–0.31 and tilt *loses* 0.12–0.18 of side — the free space is rectangular and the bottleneck is interior (box placement moves it by ≤ 0.003); 0 of 42 states gate, and the run also corrects run 78's `1 − margin` reading (a tilted candidate needs `0.5k + 0.5` on the packed square's axes, so 0.86–0.91 was an over-estimate, while its optimistic scan still found no placement); run 82 turns those numbers into certified intervals — `s <= 2 max clearance` (disk) and `s <= sqrt 2 M(0)` (inscription), each proved by branch and bound, with the axis-aligned maximum `M(0)` certified to **1e-4** at every anchor — giving achieved 0.695–0.807 against certified upper 0.788–0.886, a **gap of 0.071–0.098 per anchor**, and the largest upper side 0.8869 < 1 is a **proof that no unit square fits at any orientation** (margin ≥ 0.113); and sub-block seeding (`b x b`, same budget) measures the initial placing's effect — a single coarse grid loses 0.13 on the sharpest pockets, decomposition recovers all of them and **corrects k = 29 from 0.71218 to 0.736113** (verified, certificate recomputed, deficit 0.288 → 0.264), at the cost of a 2e-4 block-boundary loss at k = 23; run 83 lifts the verification alphabet one step to ℚ(√2) — exact `a+b√2` arithmetic and a gate with no tolerance, in which the 0° and 45° words are both first-class — and certifies seven mixed sentences at the tight side of their families, including the **four-corner glue at `2 + 1/2√2 = 2.707107` (five squares against the grid's 3)** and the rational `t=1/2` word at `19/7`; the seam law `L = 2 + 1/(cos+sin) >= 2 + 1/√2` (equality only at 45°, exactly) makes every rational tilt's cost explicit — `5/7 - 1/2√2` at `t=1/2`, `13/17 - 1/2√2` at `t=1/5` — and the minimal bridge is one tilted square coupling four 0° squares at once, while a diamond can bridge a seam but not replace a square (the 3×3 ring needs `2+√2`); a ΔΣ carrier across the seam converges like `1/N` and never reproduces the sentence (1 of 5 rungs legal, and only at a side larger by 1.9e-8); the fields swap order between N=2 and N=5 by an exact inequality; and 447 delivered rows are exactly the 0° word while **451 use no word at all**; run 84 lifts the 100 decimal-shadow rows into exact ℚ(√2) sentences with a float-free reconstructor — **97 of 100** at gate clearance exactly 0, 127,837 certified contacts over 37,260 squares, all 97 sides irrational, the other 3 (n = 51, 126, 295) not small-height sentences at all — replaces the float-fed ΔΣ with a carrier whose accumulator is a field element (legality is the sign of its error; for the whole-sentence Pell map the side excess is exactly `(r − √2)/2`, so legality is proved for every rational rung), and closes the seam family in closed form `L(k,m) = 2k + m√2/2`, `N = 4k² + m`, `V = 2km√2 + m²/2 − m`, `gain = 1 − m√2/2` (54/54 certified for k = 2..10, m = 1..6, refused 1e-9 below; gain > 0 only at m = 1, where the strip is a strict win over the odd grid at every k, though the delivered rows at those n already dominate it); run 85 extracts the ring logic into a domain-neutral exact tower (`exact_field`: Z, Q, Q(√d) for arbitrary square-free d, rational t-points, exact order/floor/ceil, **145 decision functions audited in bytecode with 0 naming float**, and the audit itself tested against a planted offender) and lifts the declared-law wheel out of packing into `glm_wheels` — any domain registers an alphabet, five syntax slots (`Tile`/`Frame`/`Strip`/`Glue`/`SymmetryFold`) with closed-form laws, and a **four-witness** suite (exact gate + topology + conservation + independent 70-digit Decimal); two domains run on it unchanged, 35 cells / 31 certified, with real refusals by law — `strip_needs_diamond` for `S(k,0)` and `not_sturmian` (`p(2) = 2 ≠ 3`) for a rational slope — the coboundary law corrected to its seam-aware form, and the packing wheel covering grids, pockets, strips, rational-t glues, the diagonal fold and the atoms n = 5, 10, 40; **all 447 pure-Q rows certified at clearance exactly 0 with side ⌈√n⌉** (419,281 exact contacts over 205,282 squares; 136 rows by the exact gate, 311 by an exact lattice lemma the gate agrees with), the exact 2D feasible cage replacing the per-coordinate height fallback, and a correction to run 84 that the "3 float artefacts" were 2 search gaps + 1 square: the mixed lift is **99/100** (n = 51 = `16/3 + 5/3√2`, n = 295 = `22/3 + 22/3√2`, both at clearance 0), with only n = 126's square 120 off-lattice; run 86 registers a **third, structurally distinct domain** on the same engine — integer and quadratic lattice shells (`Z^d`, `D4`, `E8`) held in doubled coordinates so every norm, inner product and theta coefficient is an exact integer sum — with exact-norm, kissing-topology, theta-conservation and 70-digit Decimal witnesses plus two declared refusal laws (`empty_shell`, `rank_budget`): **24 of 28 cells certified**, from theta series *computed by enumeration* (D4 1,0,24,0,24,0,96; E8 1,0,240,0,2160; kissing 4/24/240; root degrees 8/56) and `theta(A (+) B) = theta(A)·theta(B)` verified cell by cell, with the engine's four friction points named (a real double-import bug, a packing-shaped row schema, a witness that had to be re-implemented, and four-witness scoping that is per family); an exhaustive translation-and-reflection induction over **45 lifted states and 13 templates** finds **1 exact decomposition in 45** (n = 5, the pocket we already had) and proves every atom is irreducible over the declared families while `Tile1` covers exactly its axis squares (n = 10 → 8/10, n = 40 → 24/40, mean 0.7324), pinpointing the missing diamond-placement primitive; n = 126's last square turns out to have a **rank-1** contact algebra (`y − x = 11/2 + 5/2√2`, satisfied to 1.5e-9) whose exact feasible segment is `x ∈ [1.3357864, 1.3713203]` — empty of field points at tolerance 1e-4, yet containing **173** Q(√2) placements at clearance 0 (nearest `x = 43/32`, 8.2e-3 away) — so the pose is off-lattice while its topology is not: **99/100 pose lifts, 100/100 topology realisations**, with square 98 newly recovered as `(5 − 2√2, 19/2)`; and all **1,000 rows now carry an exact field class** — 447 grid, 99 Q(√2) pose, 18 Q(√2) side, 5 Q(√7) side, 3 Q(√5) side, 4 rational-t (denominators ≤ 7), 424 continuous — from 70-digit Decimal trig, continued-fraction Pythagorean tests and exact `recover_scalar`; ; run 87 keeps the promise doc 49 deferred — the engine contract becomes domain-neutral: `Wheel.spin` writes **size / measure / invariant** and a witness count instead of the packing-shaped `n / extent / gain` (`Claim.n` survives as a read-only alias, so no builder changed), witness suites are declared per family (`Witness.families`) and filtered through one `Domain.suite(claim)`, and a single `DecimalWitness` takes a per-domain `scalar` (a `Quad` of any `d`, a `Fraction`, an `int`, a `Decimal`) in place of the packing-only one — so spatial packings, Sturmian sequences and lattice shells print in **one uniform table** (28/31, 6/7, 24/28 certified; 17 controls, `w` = 4 or 3 per row); n = 126's rank-1 probe is promoted to `qsqrt2.cage_segment(...)`, a permanent mode that derives the rank, the law, the exact segment `x ∈ [1.3357864, 1.3713203]` (width 0.0355339) and the Q(√2) enumeration from the state alone — no typed bounds, no monkeypatching — and control 11 reproduces run 86's **173** while proving that number **too generous**: it counted candidates whose *rational part* lay in the band with the x-containment test skipped, so the corrected cage holds **4** placements at clearance 0, nearest still `x = 43/32` (8.2e-3), and n = 126's verdict stands as off-lattice pose with on-lattice topology; and the diamond primitive arrives as `DiamondField` — a declarative `cells` + `slots` spec over Q(√2) whose insertion rule drops colliding axis cells and *derives* L, the void and the contact graph — passing the induction acceptance test **3/3 exact**: n = 10 (8 axis + 2 diamonds, 8 of 16 dropped, `L = 3 + 1/2√2`), n = 19 (11 + 8, `L = 3 + 4/3√2`) and n = 40 (24 + 16, `L = 4 + 2√2`), each identical to its Atom cell with L reproduced and 10/10, 19/19, 40/40 covered, registered as three certified spatial cells, with n = 19 and n = 40 honestly declaring explicit axis cells because those sets are not product grids; ; run 88 closes doc 50's two limits and finds they were one — the strip is a field of (k, m): `strip_field(k, m)` declares two k-runs per axis across a seam of width `m√2/2` plus m anti-diagonal slots, so `S(k,0)` stops being refused as `strip_needs_diamond` and certifies as the plain 2k grid with **gain 0** (identical to `Tile 2k`, pinned by control 19), and the **spatial wheel is 31/31 certified, 0 refused**; and run 87's claim that n = 19 and n = 40 "are not product grids" turns out to be false — tested against their slot lists both are exactly a product minus collisions (`n19`: `{1/2,3/2} ∪ {1/2+a,3/2+a,5/2+a}` × `{1/2,3/2,5/2} ∪ {3/2+a,5/2+a}`, `a = 4/3√2`, carrier 25 → 11 cells; `n40`: `{1/2,3/2,5/2} ∪ {3/2+2√2,5/2+2√2,7/2+2√2}` squared, 36 → 24), so a field is now two short run lists plus its slots — `(start, step, count)` in Q(√2), product of the two skeletons, with run 87's "bent grid" as the two-run case and no cell lists left anywhere; the drop counts move in the honest direction (n19 0 → 14, n40 0 → 12) because the carriers are full products and the insertion rule does the trimming, while N, L, void and contacts are identical to run 87 and control 18 compares the generated cells against the run-87 census one by one (8/11/24, all equal) and fails if a field ever needs more than two runs per axis; control 5 changed with the finding — "the wheel must have at least one refused cell" is no longer true, so it now asserts the opposite and exercises every refusal law (`degenerate_cell`, `negative_seam`, `unknown_field`, `no_diamond`, `declaration_overlaps`) on constructed cells while the other wheels still refuse by `not_sturmian`, `empty_shell` and `rank_budget` — **19 controls**, **177 audited functions, 0 offenders**; ; run 89 pays two small debts of the same kind — a code path and a number that said something no longer true: `p_pocket(k)` is rewired through `strip_field(k, 1)`, so strips and pockets share one assembly (the pocket is S(k,1); run 84's sentence is now only the cross-check) with identical state, words, L and N = 4k² + 1 and its own family, the wheel's Pocket rows unchanged and spatial still **31/31**; and the dead `checks` counter in `glm_wheels`' selftest is gone — each control announces itself through one helper and the summary is `len(announced)`, so the count is the number of controls that ran rather than a literal (run 88 had already broken it), and `--selftest` now exits 0 instead of returning the count as its status; **19 controls**, **177 audited functions, 0 offenders**; ; run 90 finishes what run 89 started and opens the algebraic rungs — the Strip's seam law is shared by the Pocket so their claims differ only in family and parameters, and a genuinely malformed declaration is now refused three ways by `declaration_overlaps` (two coincident slots and two slots 1/10 apart, both caught by the gate since the insertion rule cannot see slot-slot overlap, plus a slot over an axis cell with the rule off); the strip's seam width turns out to be a *derived* quantity — the binding contact conditions give `w* = min(1/(c+s), c+s)` and **`L = 2k + w*`** at clearance exactly 0, whose 45° member is `S(k,1)` cell for cell — so the ridge extends the wheel to three new algebraic rungs, each certified by all four witnesses: `Slope` 2:1 in Q(√5) at `2k + ⅓√5`, `Seventh` with the word `(√7/4, 3/4)` in Q(√7) at `2k + 6 − 2√7`, and `Tilt` t = 1/2 at `2k + 5/7`, nine cells in all, taking the spatial wheel to **40/40 certified, 0 refused**; verification is one procedure over any field — `qgate(cls, …)` is a port of `qsqrt2.gate` over any `Quad(d)`, the gate/contact/conservation/Decimal witnesses read the claim's field and `_tag` rebuilds the grid side there, with control 21 proving the port agrees with the original exactly on the three atoms; calibration against the table is exact and negative — at n = 5 the side `2 + ½√2` beats every rung by 1.39e−3 (Seventh), 7.18e−3 (Tilt) and 3.83e−2 (Slope), and n = 17/37 are recorded as **uncalibrated** because those delivered rows carry an orientation outside the axis/45° alphabet and do not lift, so nothing here is claimed as a win; **21 controls**, **197 audited functions, 0 offenders**; ; run 91 removes the second decision procedure run 90 had introduced — `qsqrt2`'s gate is parametrised by its field class (`cls`, defaulted by `field_of` from the first coordinate, with every constant built from it) so `Q.gate(state, words)` is unchanged for every existing caller while a Q(√5)/Q(√7) sentence is decided by the same code, and `glm_wheels` loses `qgate`, `qpairs`, `qside`, `qframe_extent` and `qaxis_extent` plus the unused run-90 helpers `field_class` and `sqrt_in`; control 21 is widened from three sentences to **all 40 spatial cells**, checking that the inferred and declared field classes give identical ok/L/clearance/contacts/violations, that the witness path `gate_of` equals both, and that for **every pair** the axis vectors and slack signs from `Q.pair_axes` and `pairs_of` agree — with the ridge assertions kept (45° = `S(k,1)` cell for cell, every rung at clearance 0 with its exact side); the float audit drops from 197 to **191** functions, still **0 offenders**; **21 controls**, spatial still **40/40**, no number moved; records `31`–`54` |

## Where the score stands, said plainly

Runs 62–67 changed **no row of the table**. They priced the routes that were
nominated and closed them on measurement: the catalogue the frontier is read
against stops at n = 324 (675 rows open for want of a *source*, not a method —
runs 76–77 settle 60 grid rows outright by a published bound and certify the 191
beating rows at n ≤ 400 as frozen-angle optima, and 247 of the open grid rows sit
above 324 in one residue band);
Bui's construction was implemented exactly and refused (density 0.23–0.82 against
≈0.95); and the remaining search shapes — k-square neighbourhoods, reduced
resolution, global disjunctive SAT — were each refused with a certificate or a
counted reason rather than an opinion. Every instrument points at the same object:
the **branch assignment** (which pair is tight on which axis) and rotation.

## The score engine (what actually produces improvements)

1. **The project's own engines (GLM lineage)** — the W36 SAT substrate
   verifies every construction exactly (20–100-digit algebra, pairwise
   separation, 12-dp round-trip), and the W37-derived pressure-settling
   engine (analytic gradient through the SAT stack, pressure ramp,
   L-BFGS-B creep) is the honest search layer: its campaign record is
   measured and null on this landscape (the stall law: terminal
   penetration p ≈ 0.45–0.88·d at target depth d), so it now serves as
   the verification/refinement gate, not the discovery layer. The
   Leech/Golay layer (leech_core, octad_moves: 28/28 + 14/14
   integer-exact assertions) classifies all 1000 rows by number field.
2. **Source integration** — the survey's 235 record SVGs (20–100 digit
   parse), the Ellsworth catalogue, the community register (76 records
   our table lacked, run 18; the T-263 record, run 26), and — the
   largest import of the project — **Mishapolk/square-packing-records**
   (run 30: verified bounds at ALL 1000 n; the band 325..1000 was
   invisible to our atlas; 221 rows imported, −0.173983). Sources beat
   search: every score move since run 9 has been an import. I am trying to keep track of all external sources and clearly identify and reference them.
3. **Analytic families** — Göbel strip/central-square, the 4-parameter
   diamond+staircase G(a1,a2,b,c) (17 mid-band finds beyond the catalogue),
   the clipped variant G(a1,a2,b,c,t) (5 more).
4. **Exact propagation** — removal closure (prefix-min envelope) +
   L-extension band chains; the residue-diagonal law multiplies every find
   (one base at n₀ opens its whole diagonal n = (K−1)² + c).
5. **The honest gate** — every state, imported or constructed, is
   packlib-verified (SAT non-overlap, bbox containment, 2e-9 clearance,
   12-dp round-trip). Nothing ships unverified.
6. **The measurement layer (runs 27–31)** — `root_audit.py` (chain-envelope
   fixpoint audit + the aiming map: where a new record pays most; best aim
   c=32 n=356), `sat_review.py` (per-pair SAT margins, contact language,
   Maxwell ratios), `sat_measure.py` (TAX/NRCI regime map — the GLM's own
   measure applied to the SAT data: the vacuum is exactly the grid rows),
   `symmetry_audit.py` (D4 census: constructions symmetric, records
   asymmetric), and `root_audit.py`'s `table_laws` block checks the
   monotone envelope and the shell law every run (999/999 and 937/937
   clean at run 34). Every campaign is aimed by these instruments,
   never by eyeball.
7. **The theory layer (runs 62–67)** — the part that decides rather than searches,
   and the only part that can say *why* a route is dead: `bui_wheel.py` (a
   published nomination implemented to the letter over ℚ and refused on density,
   132/132 verified, 0 gains), `ladder.py` (six expressiveness rungs, 4 recomputed,
   2 honestly quoted — the Λ₂₄ sweep kills coarsening at all eight scales),
   `disj_census.py` (0.76 % of pairs tight at n = 1000, 1e300729 leaves: the model
   is decisive *with the disjunction fixed*), `sat_probe.py` + `extreme_probe.py`
   (the declared-axis LP as a certificate: with every translation free, the
   delivered side is the exact optimum at ε = 1e−6), and `resolution_probe.py`
   (snapping the *answers* to a lattice invalidates them at every resolution,
   m = 128 included — contacts are equalities with no neighbourhood). Records
   `27`–`30`; `sat_probe.py --selftest` (6/6) is the invariant that guards the LP.

## Reproducing

See **REPRODUCE.md** for the exact command chain, expected outputs, and
the list of steps that need network access (live catalogue mirrors) or
transient /tmp files.

## Operations 
Each run, update top-level STATUS.md (include the README.md copied at the bottom of STATUS.md), NEXT_STEPS.md and REPRODUCE.md all need updating. If possible GLM_INVESTIGATION.md should be upkeep as an overview of the whole study.

## Guarantee

Every packing shipped in submission.csv was re-verified from the file as
written on disk (pairwise SAT non-overlap with worst penetration ≤ 0,
bounding-box containment, per-n counts, id continuity 0..500499, 12-dp
round-trip stability with ~2e-9 clearance). Every mathematical claim in
the Leech layer is machine-verified with exact integer computation; no
floats anywhere in the lattice math. Λ16's kissing number 7320 is cited
(SPLAG), not verified — marked as such everywhere it appears.
