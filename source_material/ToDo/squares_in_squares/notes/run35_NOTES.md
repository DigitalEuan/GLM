# Run 35 (2026-11-07): deep exploration + advances + the paper + Lean

**User order.** Explore the project deeply; push any further advances;
turn `GLM_INVESTIGATION.md` into an academic-paper record; create Lean 4
lemmas/axioms that can be verified and fed back into the system.

**Score: 22.645990613 → 22.642386651 (−0.003604). Beats-grid 543/1000
unchanged (all 9 wins deepen below-grid rows). Gap to the reported
leader: 0.591569 → 0.587965.**

## (a) P3 source watch — the score move (9 register records)

Deep exploration started at the frontier sources. The Mishapolk
catalogue and the atlas `best.json` were both unchanged upstream — but
`evand/square-packing` had moved: a Nov-5 commit carries candidate
certificates "for jlevy registration", and the jlevy/squares register
had closed them as **nine new upper bounds** (issues #806/#845/#914
closing replies):

| n | record | side | previous table L | old src |
|---:|---|---:|---:|---|
| 172 | T-257 | 13.617935700 | 13.618988959 | run18-frontier |
| 175 | T-267 | 13.764050053 | 13.764174319 | run18-frontier |
| 182 | T-243 | 13.970916438 | 13.974090715 | run18-frontier |
| 204 | T-268 | 14.804361386 | 14.808642842 | run18-frontier |
| 260 | T-269 | 16.633520953 | 16.645753252 | run18-frontier |
| 268 | T-270 | 16.872499520 | 16.878814823 | run18-frontier |
| 293 | T-271 | 17.623065214 | 17.634146343 | exact:square-293.svg |
| 303 | T-272 | 17.901832753 | 17.909772219 | mishapolk:n303.cert |
| 304 | T-273 | 17.920944095 | 17.929427760 | run18-frontier |

All by Evan Daniel (evand); lineage per the register's closing replies
(172 continues Nate Chaoweeraprasit's s(199) record improved by
Siddharth Gupta; 204 continues Daniil Ostashev's s(176); 260 continues
Kirill Tymchishin's s(260); 293 is the 260 packing mirrored + an
L-strip of 33). Procedure (run-30 pattern, idempotent + resumable):

1. `fetch_candidates.py` — mirrored all 73 `*.cert` files from
   `evand/square-packing/search/packer/candidates/` into
   `workspace/sources/candidates/` (+ snapshot.json for the weekly diff).
   The 21 noise-level "wins" (~1.8e-9, the same packings as our stored
   rows less the +2e-9 finalize inflation) were skipped by
   MIN_GAIN = 1e-7 — the table must not churn on re-runs.
2. `import_candidates.py` — exact-rational parse (n, S; per square
   x y t, t = tan(θ/2)), packlib.verify (tol 1e-9), finalize (2e-9
   gap, 12-dp), best-L-wins, attribution map to T-ids. Dry-run first
   (9 candidates, 0 verify fails), then applied. Ledger:
   `workspace/push/import_candidates35.json`.
3. Channel (mandatory order): cascade3 → closure_apply →
   final_assembly. **cascade3 converted n=338** (chain from the 303
   record: L(303)+1 = 18.9018327 < 18.9063328): +0.000245. Closure:
   fixpoint after 0 rounds. CSV round-trip: 500,500 rows, 0 issues.
4. root_audit: fixpoint true (0 above envelope), table laws clean
   (monotone 999/999, shell 937/937 @1e-7), 305 open rows, aggregate
   0.375304 unchanged, best aim c=32 n=356 unchanged. Gap now 0.587965.

Direct 0.003359 + cascade 0.000245 = 0.003604. Two independent rescore
paths agree (`score_submission.py`, `final_assembly.py`).

## (b) Constructive-advance attempt — the wedge probe (measured negative)

Derived from the family geometry: the G(a1,a2,b,c) contact triangles
are exactly filled by the corner staircases T(a) at contact, but the
container-minus-diamond free region is the union of the u-clear
triangle and two v-clear wedge strips — apparently room for edge-row
extensions the sweep never tries. Test (vectorized greedy maximal
lattice fill, exact SAT admission, all four corner anchorings):

- live-band cores = every (a1,a2,b,c) whose family side beats or
  misses the table by < 0.01: **217 cores**.
- **0 of 217 admit any extra lattice square.** New wins: 0.

Analytic reading (now in GLM_INVESTIGATION §4.2): the staircase step
gaps are legs-1 triangles (max inscribed unit square has side 2−√2 <
1); wedge rows appear only for thin diamonds (b ≫ c), where the room is
already the opposite staircase's territory and the swept a2 parameter
covers it. The family is **lattice-maximal at the frontier**. The
mid-band prize (open rows at c ≤ 2K−6) therefore still needs a new
*architecture*, not a family completion.

Also derived and recorded (paper §4.2): partial clips of the clipped
family and non-lattice corner fills remain open architecture research;
every such derivation is the right next move (construction beats
search — the project's central lesson).

## (c) The paper + the Lean layer (the user's deliverables)

1. **`GLM_INVESTIGATION.md` rewritten as the academic paper** —
   "Squares in Squares: Exact Construction, Verified Propagation, and
   the Measured Limits of Search". Abstract; problem & state of the
   art; GLM lineage (TAX/NRCI, delta-sigma, cent compiler W36/W37);
   method (gate + loop + ledgers); the Göbel family with the contact
   identity and the four competing hypotheses (φ, √3, fields,
   completeness); the propagation algebra (chain law, closure, table
   laws) with the Lean upgrade; the measurement layer (contact
   language, TAX/NRCI, symmetry, aiming map); the negative-search
   ledger (stall law, oracle study, fork program, positive control);
   the source frontier (register, Mishapolk, run-35 import); the Lean
   layer with the feedback map; results and the gap decomposition;
   open problems; guarantee; references (12).
2. **`workspace/lean/tct_squares/TCT/Laws.lean`** — the law layer:
   - proved: `prefixMin_le`, `prefixMin_mono`,
     **`closure_fixpoint_monotone`** (the monotone-envelope table law
     is a corollary of the removal-closure fixpoint — the flagship
     feedback theorem), `staircase_cells` (T(a) = a(a+1)/2 exact),
     `gobel_count`/`gobel_square_count`/`diamond_bbox_square_case`,
     `ceil_sqrt_mono`, `chain_value_mono`, **`nrci_eq_one_iff_zero`**
     (run-29 vacuum finding as a theorem), `nrci_lt_one_off_vacuum`,
     `sq_le_of_sq_sq`, `sq_floor_of_area_bound`;
   - axioms (cited style): `Packable` (opaque packing predicate —
     certified per row by packlib, not by this development),
     `area_bound` (measure bound behind the perfect-square floors).
   Existing modules unchanged (TCT/Basic: 1 deliberate sorry
   `s11_optimal_value`; TCT/Layers: scan-blindness lemma). SORRY_LEDGER
   refreshed.
3. **Feedback into the system**: the two theorems above convert
   measured checks into theorem instances — if root_audit's monotone
   law ever fails on a candidate table, the closure/finalize is broken,
   not the mathematics; if NRCI ≠ 1 on a g = 0 contact word, the
   measure constants are wrong. Hypotheses (closure fixpoint, Q > 0)
   are now machine-checkable requirements on the channel and constants.

## (d) Housekeeping

- The active-channel scripts' hard-coded `/home/z/my-project` root
  fixed (cascade3, closure_apply, final_assembly, root_audit,
  verify_current, score_submission, import/fetch_mishapolk,
  leech_core, octad_moves, leech_map, galois_certs): paths now resolve
  from the script location — REPRODUCE.md's portability claim is now
  true for the verification chain. (Other historical scripts still
  carry the old root; they are replay-only and noted.)
- Lattice layer re-verified from first principles: leech_core 28/28,
  octad_moves 14/14 integer-exact.
- Census (script-computed): grid 457 · mishapolk 207 · chain3 88 ·
  exact 77 · run18-frontier 68 · gobel2 34 · gobelS 18 · removal 18 ·
  closure 18 · register 10 · aux 3 · gobel3 2.

**Documents updated together** (standing rule): README, STATUS
(+ the README mirror), NEXT_STEPS, REPRODUCE, this ledger,
run35_NOTES.md, GLM_INVESTIGATION.md, SORRY_LEDGER.md.
