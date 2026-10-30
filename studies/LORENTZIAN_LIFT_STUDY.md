# The Lorentzian lift of the ambiguous space — the owner's `iter10_lorentzian.py` audited and repaired

## Tier 0 — the coarse read

**Question.** Does lifting the GLM's ambiguous 24-bit space to the Lorentzian lattice II_25,1, as `iter10_lorentzian.py` proposes, resolve its ties, and if not, what can the lift be made to do for the GLM's reasoning?

**Verdict.** The lift certifies every Golay tie exactly as a deep hole of the Leech lattice of type A_1^24, named by a null vector of II_25,1, but no reflection or other reflection-invariant rule can break a tie; summing Lorentzian scores over further readings resolves ties, with 0 wrong answers on readings that each contain the sent codeword among their nearest, and it answers where the existing set collapse refuses, at the cost of being misled by a reading of a different message.

**Deciding figure.** 11 of 12 marks; one tied reading: every rule at chance or refusing (the script's rule 0 right of 600); two tied readings 586 right, 0 wrong of 600; readings 4+4+6: 594 right against 0 for the set collapse; decoy: 216 wrong, 61 with the guard (mark M11 not met).

**Recomputed by.** `glm_universal.reasoning.lorentzian_lift_study.lorentzian_lift_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

*Created 22 October 2026. Pre-registered 22 October 2026: marks M1–M10 and L
(§5) were written into `reasoning/lorentzian_lift_study.py` before the first
measurement; M11 and the guarded rule were added after a 60-query trial run
and before the full measurement, and are labelled so. Measured 22 October
2026.*

## 0. What this document is

**In one paragraph.** The lift certifies every Golay tie exactly as a deep hole of the Leech lattice of type A_1^24, named by a null vector of II_25,1, but no reflection or other reflection-invariant rule can break a tie; summing Lorentzian scores over further readings resolves ties, with 0 wrong answers on readings that each contain the sent codeword among their nearest, and it answers where the existing set collapse refuses, at the cost of being misled by a reading of a different message.


A study for Phase 182, at the owner's request: the script
`source_material/iter10_lorentzian.py` (moved there this round, unedited)
proposed that the ~40 % ambiguous part of the GLM's space — deep holes,
Voronoi ties, sextet ambiguities — could be resolved by lifting the 24-D
Euclidean Leech lattice to the (25+1)-D Lorentzian lattice II_25,1, where

* the Leech lattice is `(w^⊥ ∩ II_25,1) / Zw` (Conway);
* deep holes would correspond exactly to roots `r` with `⟨r, w⟩ = −1`;
* every ambiguous tie would be a reflection hyperplane;
* the Householder reflection `v ↦ v − 2⟨v, r⟩/⟨r, r⟩ · r` would resolve it.

The owner asked for this to be tested properly, for how much it can do for
the GLM's reasoning, and — if the concept is off — for the part to be made to
work some other way. All three are answered here.

**The ambiguous space, identified.** The "~40 %" is the Golay decoder's tie
space: the extended Golay code has 4096 cosets, of which 1771 have weight 4
(`1771/4096 ≈ 43.2 %`, the slack recorded as `LAW_GOLAY_UNIQUENESS_001`). A
word in such a coset is at Hamming distance 4 from six codewords at once (a
sextet), and the decoder can only list them (`substrate/superposition.py`).

## 1. The script audited

| claim or step of the script | holds? | what is true |
|---|---|---|
| `L(x) = (x, (1−|x|²)/2, (1+|x|²)/2)` is null | yes | `lift_null` |
| `w = (0,…,0,1,1)` is the Weyl vector | **no** | it is null, but it is `2·L(0)`, the lift of the origin (`scriptW_eq`); `⟨L(x), (0,1,1)⟩ = −|x|²` depends on `x` (`inner_lift_scriptW`). The Weyl vector of this lift is `w = (0,…,0,−1,1)`: `⟨L(x), w⟩ = −1` for every `x` (`inner_lift_weyl`) |
| deep holes ↔ roots with `⟨r, w⟩ = −1` | **no** | the vectors with `⟨r,r⟩ = 2`, `⟨r,w⟩ = −1` are exactly `r_λ = L(λ) − w` (`root_char`), and they lie in II_25,1 exactly when `λ` is a **Leech point**: roots are indexed by lattice points (Conway's theorem). Deep holes correspond to primitive **null** vectors (Borcherds): here `z = 2·L(x)` |
| the roots built as `(centre, −1, 0)` | **no** | both have norm 17, not 2 (centre raw norm 16, plus 1); `⟨r, w⟩ = −1` holds for *any* centre, so the script's `is_conway_root` check cannot fail |
| the 0/1 embedding of a 24-bit word | **no** | not in the Leech lattice's scale. The right embedding doubles the word: `2c` is a lattice vector for every codeword `c` (`dbl_isLeech`) |
| every tie is a reflection hyperplane | yes | a tie between `λ` and `μ` is exactly `⟨L(x), r_λ − r_μ⟩ = 0` (`tie_iff`) |
| the reflection resolves the tie | **no** | the reflection in that hyperplane fixes the tied point and swaps the two candidates (`tie_reflection`); no reflection-invariant rule can break a tie (`reflection_invariant_tie`, §4) |
| "disambiguated" = 100 % means the method works | **no** | the counter adds one whenever a reflection could be computed, so it equals the ambiguous count by construction (M10); on 600 tied readings the script's predicted word was never a codeword and never the sent one (0 of 600) |

So the geometry the script reaches for is the right geometry — Conway's
lift — but two entries of its dictionary are shifted (roots are lattice
points, deep holes are null vectors), its Weyl vector is the lift of the
origin, and the step meant to resolve a tie cannot move the tied point.

## 2. What is proved

**`glm_lean/RequestProject/GLM/LorentzianLift.lean`** — over `ℚ`, in
the script's own coordinates `(x, t, τ)` with the form
`x·x' + t t' − τ τ'`, for any dimension `n` (24 for the Leech lattice).

* `lift_null`, `inner_lift_lift` — the lift is null, and
  `⟨L x, L y⟩ = −|x − y|²/2`;
* `weyl_null`, `inner_lift_weyl` — `w = (0, −1, 1)` is null and
  `⟨L x, w⟩ = −1`; `scriptW_eq`, `inner_lift_scriptW` — the script's
  `(0, 1, 1)` is `2·L 0` and is not constant against the lift;
* `root_norm`, `inner_root_weyl`, `root_char` — the roots of the lift are
  exactly `r_λ = L λ − w`; `inner_weyl_root` — `⟨w, r_λ⟩ = −1` for every `λ`,
  so the Weyl vector scores every candidate alike;
* `inner_lift_root` — **the key identity** `⟨L x, r_λ⟩ = 1 − |x − λ|²/2`;
  `nearer_iff`, `tie_iff` — the nearest point is the root of largest score,
  and a tie is the mirror of `r_λ − r_μ`; `inner_root_root`, `root_sub_norm`;
* `hole_orth` — a point at squared distance 2 from `λ` (the covering radius
  squared) is orthogonal to `r_λ`;
* `refl_inner`, `refl_fix_of_orth`, `refl_swap`, `tie_reflection` — the
  Householder reflection is an isometry, fixes its mirror, and the reflection
  of a tie fixes the tied point and swaps the candidates;
* `reflection_invariant_tie` — **the no-go**; `inner_reflection_invariant`;
  `context_break` — scoring by a second point prefers the candidate nearer to
  it.

**`glm_lean/RequestProject/GLM/GolayDeepHole.lean`** — over the
project's Golay code and Leech lattice (`LeechShells.lean`, raw coordinates).

* `normSq_dbl_sub` — `normSq (2b − 2c) = 4 · hdist b c`;
* `dbl_isLeech` — `2c` is a lattice vector for every codeword;
* `leech_far` — every lattice vector is at least `4 · hdist b c` from `2b`
  for some codeword `c`, or at least 24;
* `leech_dist_coset_weight` — **the Leech distance of a doubled word is its
  Golay coset weight**: squared true distance `k/2` for coset weight `k`;
* `golay_tie_deep_hole` — **every Golay tie is a deep hole**: at coset weight
  4 the doubled word is at true squared distance 2 from the lattice, which is
  the Leech covering radius squared (Conway, Parker and Sloane; cited, not
  proved here);
* `summed_score_le` — summed scores over several readings never rank any
  codeword above one that is a nearest codeword of every reading.

Both files are in `AxiomAuditAll.lean`; the whole-development audit reports
10001 theorems on the standard axioms.

## 3. What the lift does give: a tie certified, named and carried

For a word `b` of coset weight 4, with `x = 2b`:

* its nearest lattice points are **48**, eight for each of the six tied
  codewords (`2b` off `b ⊕ c`, `2b_i ± 2` on it, with the sum condition),
  all at raw squared distance 16;
* the hole diagram of those 48 (`reasoning/deep_holes.hole_diagram`) is
  **24 disjoint affine `A_1` pairs**, certified complete: the deep hole of
  type **A_1^24**, Coxeter number 2;
* in the lift, every one of the 48 roots is orthogonal to `L(x)`
  (`hole_orth`), their Gram matrix has 24 entries `−2` (the pairs) and 1104
  entries 0, and `z = 2·L(x)` is a primitive null vector of II_25,1 while
  `L(x)` itself is not in II_25,1.

Checked on 128 sampled weight-4 cosets (M9): 128 of 128 on every count. On
128 sampled words of every coset weight, the exact Leech decoder's squared
distance was the coset weight over 2 every time, as `leech_dist_coset_weight`
proves for all words.

So the 43 % of the space that the Golay decoder can only list is, one layer
up, a single kind of object: an A_1^24 deep hole, named by one exact null
vector. The lift turns an unordered list of six into a certificate.

## 4. Why no reflection resolves a tie

`reflection_invariant_tie`: if a score `f(v, r)` does not change when both
arguments are reflected in the same non-null mirror, then at a point
equidistant from `λ` and `μ` it gives `r_λ` and `r_μ` the same score. The
proof is two lines: the reflection in `r_λ − r_μ` fixes `L(x)` (it lies in
the mirror) and sends `r_λ` to `r_μ`. The Lorentzian inner product, any
function of inner products, and the Weyl vector are all such scores. Measured
(M1): on 600 tied readings the tie's reflection returned `L(x)` unchanged 600
times, and the Weyl score was the same for all six candidates 600 times.

This is not a defect of the lift: a tie is a symmetry, and no rule that
respects the symmetry can choose. A tie is broken only by information from
outside it.

## 5. Marks and measurements

Queries: a random codeword; a *reading* is it with an error of the stated
weight; a weight-4 error always lands in a weight-4 coset, so every first
reading is a tie. 600 queries per condition, fixed seed.

**One reading** (a tie):

| rule | right | wrong | refused |
|---|---|---|---|
| `min` (the GLM default) | 104 | 496 | 0 |
| `script` (iter10, reimplemented) | 0 | 600 | 0 |
| `reflection` (reflect, decode again) | 104 | 496 | 0 |
| `weyl` (score by `⟨w, r_c⟩`) | 0 | 0 | 600 |
| `script_w` (score by `(0,1,1)`) | 18 | 94 | 488 |
| `lorentz` (summed scores) | 0 | 0 | 600 |

`min` and `reflection` are at chance (1/6 of 600 is 100); `reflection`
answers exactly what `min` answers because it leaves the point where it was.

**Several readings** (the first always a tie):

| readings | `lorentz` right / wrong / refused | `lorentz_guarded` | `intersect` (set collapse) | `first_min` right |
|---|---|---|---|---|
| 4+0 | 600 / 0 / 0 | 600 / 0 / 0 | 600 / 0 / 0 | 119 |
| 4+1 | 600 / 0 / 0 | 600 / 0 / 0 | 600 / 0 / 0 | 95 |
| 4+2 | 600 / 0 / 0 | 600 / 0 / 0 | 600 / 0 / 0 | 98 |
| 4+3 | 600 / 0 / 0 | 600 / 0 / 0 | 600 / 0 / 0 | 94 |
| 4+4 | 586 / 0 / 14 | 586 / 0 / 14 | 586 / 0 / 14 | 73 |
| 4+5 | 495 / 3 / 102 | 495 / 3 / 102 | 0 / 3 / 597 | 109 |
| 4+6 | 318 / 24 / 258 | 318 / 24 / 258 | 0 / 17 / 583 | 96 |
| 4+4+4 | 600 / 0 / 0 | 600 / 0 / 0 | 600 / 0 / 0 | 116 |
| 4+4+6 | 594 / 0 / 6 | 594 / 0 / 6 | 0 / 0 / 600 | 111 |
| decoy | 32 / 216 / 352 | 10 / 61 / 529 | 2 / 3 / 595 | 101 |

| mark | declared | result |
|---|---|---|
| M1 | the tie's reflection fixes `L(x)`, the Weyl score is flat, every query | met (600, 600) |
| M2 | the script's rule right on at most 1/6 + 1/20 | met (0 of 600) |
| M3 | `lorentz` on one reading: 0 wrong, all refused | met |
| M4 | `lorentz` on 4+4: 0 wrong, at least 90 % right | met (586) |
| M5 | `lorentz` on 4+4+4: 0 wrong, at least 99 % right | met (600) |
| M6 | `lorentz` on 4+k, k ≤ 3: every query right | met |
| M7 | decoy: `lorentz` right on at most 25 % | met (32) |
| M8 | `lorentz` right at least as often as `intersect`, every condition | met |
| M9 | census: 48 vertices, A_1^24, orthogonal, null vector in II_25,1; distances | met (128 of 128) |
| M10 | the script audit (roots, vacuous checks) | met |
| M11 | *(added after the trial)* guarded: 0 wrong on the decoy, ≥ 90 % of `lorentz`'s right kept | **not met**: 61 wrong on the decoy |
| L | the Lean files, no `sorry`, audited | met |

11 of 12 marks.

## 6. What it achieves for the GLM's reasoning

Under the standing target (`PROJECT_DIRECTIVES.md`) the measured gains are:

* **Refuse.** One tied reading is now refused with an exact certificate —
  the A_1^24 deep hole, its 48 vertices, the null vector naming it — where
  the default decoder answers `min` and is wrong 496 times in 600. That is a
  refusal at no cost in right answers the default actually had (its 104 were
  chance).
* **Address.** Two readings, each a tie, are resolved 586 times in 600 with
  0 wrong; three 600 of 600. Here the summed score does exactly what the
  existing set collapse (`superposition.collapse`) does, and
  `summed_score_le` says why it cannot be wrong whenever every reading has
  the sent codeword among its nearest.
* **Where the lift earns its keep: graded evidence.** When a later reading is
  noisier than the covering radius, the set collapse has nothing to
  intersect and refuses; summed Lorentzian scores still rank the candidates.
  On 4+4+6 the summed score is right 594 times in 600 with 0 wrong, the set
  collapse 0; on 4+5, 495 against 0 (3 wrong each). This is the property of
  the lift the script did not use: scores are linear, so evidence from
  several readings adds.
* **The cost, stated.** A reading of a different message misleads the summed
  score: on the decoy it gave 216 wrong answers in 600, where the set
  collapse gave 3. The consistency guard (refuse an answer more than 6 bits
  from any reading) cut that to 61 but not to 0, so M11 is not met; the
  guard did not cost any right answers elsewhere. The answering path uses the
  guarded rule.

**`tool lorentz MASK ; MASK ; …`** puts it in the answering path: one reading
of a tie is refused with the certificate and a request for another reading;
several readings are answered when the summed score has a unique maximum
within the guard, and refused otherwise.

## 7. What this does not do, and what is next

* **It does not break a single tie.** That is a theorem
  (`reflection_invariant_tie`), not a gap: the information is not in one
  reading.
* **It does not lift the parity wall.** A vector of II_25,1 has its first 24
  coordinates in the Leech lattice (II_25,1 = Λ ⊕ U), so a word whose
  quadrupled image is outside Λ (odd weight; `FINDINGS.md` of the pipeline
  kit) has no vector upstairs above it either.
* **Only the Golay layer is lifted.** Leech-level nearest-point ties
  (`reasoning/tie_break.py`) and the other 22 deep-hole types are the next
  layer: the key identity and the no-go are proved in any dimension and for
  any points, so the same certificate applies; what is missing is a
  measurement on them.
* **The decoy cost wants a better guard.** A guard on the *summed* score
  (rather than the farthest reading), or a test of whether the readings
  share a nearest codeword before summing, are the obvious candidates; each
  must be declared before it is measured.

## 8. Reproduce

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.tools lorentzian-lift          # the stored marks
PYTHONPATH=. python3 -m glm_universal.tools lorentzian-lift --write  # re-take (~3 minutes)
python3 GLM.py -q "tool lorentz 15"                                   # a tie, refused with its certificate
python3 GLM.py -q "tool lorentz 15; 0"                                # resolved by a second reading
lake build RequestProject.GLM.LorentzianLift RequestProject.GLM.GolayDeepHole
```

The mechanism is `glm_universal/reasoning/lorentzian_lift.py`, the
measurement `glm_universal/reasoning/lorentzian_lift_study.py`, the
tests `glm_universal/tests/test_lorentzian_lift.py`.
