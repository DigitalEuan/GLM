# First-principles findings, in order

Every line below is a machine-checked Lean theorem in this directory, except
where the verdict says **Open**.  Nothing is asserted here that is not proved,
and the whole directory compiles with no `sorry` and no added axiom.

Verdict vocabulary:

| tag | meaning |
|---|---|
| **Forced** | the framework's object is the only thing that could have played its rôle |
| **Derived** | follows from what came before; not an extra assumption |
| **Input** | cannot be obtained from what came before; enters from outside |
| **Chosen** | consistent, but one of many equally good options; carries no necessity |
| **Generic** | true of any structure of the same shape, so not evidence for this one |
| **Not evidence** | a numerical agreement that a random target would also enjoy |
| **Open** | genuine mathematics, not settled here or anywhere |

---

## Stage 0 — Distinction (`Distinction.lean`)

1. **FP-1 · Derived.** A carrier with no distinction carries no information:
   every function out of a subsingleton is constant.
   `no_information_without_distinction`
2. **FP-2 · Forced.** Two states is the minimal non-degenerate carrier, and any
   carrier with two distinguishable states maps onto it.
   `bool_card`, `surjects_onto_bool`
3. **FP-3 · Derived.** A field of `n` binary cells has exactly `2ⁿ` states: the
   substrate's information content is `n` bits, no more.
   `bitfield_card`
4. **FP-4 · Forced.** The reversible operations on one cell form a group of
   order two; the toggle is the only non-trivial one.
   `perm_bool_card`, `perm_bool_eq`, `toggle_involutive`
5. **FP-5 · Forced.** Any ring structure on a two-element carrier is `ZMod 2`,
   so the substrate's arithmetic is not a modelling choice.
   `two_element_ring_is_zmod_two`, `bit_field_card`, `boolEquivZMod2`
6. **FP-6 · Derived.** Cellwise toggling makes the state space the elementary
   abelian group `(ZMod 2)ⁿ`: every state is self-inverse, and every state is
   reachable from any other by exactly one toggle pattern.
   `self_inverse`, `reachable`
7. **FP-7 · Derived.** Commutativity of the substrate is a *theorem*, not a
   postulate: any group whose elements are all self-inverse is abelian.
   `self_inverse_forces_comm`

## Stage 1 — Distance and correction (`Distance.lean`)

8. **FP-8 · Derived.** Toggle-count is a metric: symmetric, zero only on equal
   states, subadditive.
   `dist_comm'`, `dist_eq_zero_iff`, `dist_triangle'`
9. **FP-9 · Derived.** It is invariant under the substrate's own dynamics, hence
   is a weight function on states.
   `dist_translation_invariant`, `dist_eq_weight`
10. **FP-10 · Derived.** Unique decoding: admissible states at least `2t+1`
    apart are unambiguously recoverable from any state within `t` toggles.  This
    is all "error correction" can mean here.
    `unique_decoding`
11. **FP-11 · Derived.** The correction radius is `⌊(d−1)/2⌋`; for `d = 7` and
    `d = 8` it is the same number, `3`.
    `radius_of_seven`, `radius_of_eight`, `correction_radius_three`
12. **FP-12 · Derived.** Even minimum distance is never fully usable: if two
    admissible states are exactly `2t+2` apart, some state is equidistant from
    both.  The extra unit buys detection, never correction.
    `even_distance_ambiguity`

## Stage 2 — Where 23 and 24 come from (`Packing.lean`)

13. **FP-13 · Derived.** The number of states within `t` toggles of a given
    state is `Σ_{i ≤ t} C(n,i)`.
    `ball_card_eq`
14. **FP-14 · Derived.** Sphere-packing (Hamming) bound: a `t`-correcting code
    of length `n` satisfies `|C| · Σ_{i ≤ t} C(n,i) ≤ 2ⁿ`.  Proved for arbitrary
    `n`, `t` and arbitrary codes.
    `hamming_bound`
15. **FP-15 · Forced (and it forces 23, not 24).** For three-toggle correction
    the bound can be met only if `Σ_{i ≤ 3} C(n,i)` is a power of two; among all
    lengths `4 ≤ n ≤ 2000` this happens exactly at `n = 7` (the repetition code)
    and `n = 23` (the Golay length).
    `perfect_triple_length`, `perfect_triple_length'`, `ball3_closed_form`
    *(The classical theorem — that 23 is the only non-trivial length, at any
    size — is not formalised here; the search is exhaustive up to 2000.)*
16. **FP-16 · Derived.** At length 23 the bound is met exactly:
    `2¹² · 2048 = 2²³`.
    `golay23_perfect_arithmetic`
17. **FP-17 · Derived.** At length 24 it is not: `2¹² · 2325 < 2²⁴`, leaving
    `7 254 016` states — over 43 % of the space — uncovered.
    `golay24_not_perfect`, `golay24_deficit`
18. **FP-18 · Chosen.** So `24 = 23 + 1` is a parity extension.  Proved here in
    general: extending a code of *odd* minimum distance `d` by a parity cell
    gives minimum distance at least `d + 1` — with `d = 7`, the extended Golay
    distance 8 — while by FP-11 the correction radius stays at 3, and by FP-12
    the extra unit is never usable for correction.  24 is selected by the wish
    for a self-dual (even-length) code — a symmetry preference — not by an
    information-theoretic necessity.
    `parityExt_min_distance`, `parityExt_dist_of_odd`, `parityExt_dist`,
    `selfdual_needs_even_length`, `extension_arithmetic`

## Stage 3 — The seeds (`Seeds.lean`)

19. **FP-19 · Input.**  *The central structural finding.*  Everything Stages 0–2
    produce is an integer, and no seed is a ratio of integers: `π`, `φ`, `e` are
    irrational, so none of them is a value of any rational expression in
    substrate counts.  The seeds are an independent input to UBP, not a
    consequence of the binary principle.
    `seeds_not_ratio_of_counts`
    * **FP-19a · Derived.** The three seeds are not on the same footing: `φ`
      is algebraic, so a substrate able to solve quadratics reaches it from its
      own integers.
      `phi_reachable_by_root_extraction`
    * **FP-19b · Input (conditional).** `π` and `e` are reachable by no
      algebraic operation at all — conditional on Lindemann's and Hermite's
      transcendence theorems, carried as explicit hypotheses because the pinned
      Mathlib does not contain them.
      `pi_e_not_algebraically_reachable`
20. **FP-20 · Forced.** `φ` is the unique positive solution of one-step
    self-similarity `x² = x + 1`.
    `phi_unique_positive_root`
21. **FP-21 · Forced.** `π` is the least positive zero of `sin`: the first
    closure of a rotation.
    `pi_least_positive_zero`
22. **FP-22 · Forced.** `e` is the unique base whose exponential has unit growth
    rate at the origin.
    `e_unique_unit_growth_base`, `deriv_rpow_zero`
23. **FP-23 · Derived.** The three are distinct and all irrational; `φ` is
    algebraic of degree 2.  (That `π` and `e` are transcendental is classical
    but is carried as an explicit hypothesis in the parent study, since the
    pinned Mathlib does not contain Hermite's or Lindemann's theorem.)
    `seeds_pairwise_distinct`, `seeds_all_irrational`, `UBP.phi_isAlgebraic`
24. **FP-24 · Chosen.** The combining rule is free.  `⌊πφe⌋ = 13` is true, but
    so are `⌊πe/φ⌋ = 5`, `⌊πφ²e⌋ = 22` and `⌊πφe²⌋ = 37`.  Reading "13" out of
    the seeds requires choosing the monomial `π¹φ¹e¹`, and nothing in Stages 0–3
    selects it.
    `hull_alternatives`

## Stage 4 — What a numerical agreement can prove (`FitCapacity.lean`)

25. **FP-25 · Derived.** Lattice approximation: for any spacing `s > 0`, the
    progression `p·s` comes within `s/2` of *every* real target.
    `lattice_approx`, `lattice_approx_offset`
26. **FP-26 · Not evidence.** For every target `t ≥ 137`, some integer multiple
    of `L` added to `137` reproduces it to relative accuracy `≤ 2.3×10⁻⁴`.  The
    framework's actual `α⁻¹` agreement is `1.96×10⁻⁴` — **less than 1.2× better
    than what any target whatsoever would enjoy**.
    `alpha_generic_guarantee`, `alpha_fit_barely_beats_generic`
27. **FP-27 · Generic.** The same holds with `L` replaced by any positive number
    of comparable size: this is a property of the shape `integer + multiple`,
    not of the seeds.
    `matching_is_seed_independent`
28. **FP-28 · Worth ~1 digit.** For every target `t ≥ 206`, some `n/w` with
    `n ∈ ℤ` is within `2.97×10⁻³` relative.  The framework achieves
    `2.94×10⁻⁴`: better than generic by a factor between 10 and 11.
    `muon_generic_guarantee`, `muon_fit_beats_generic_by_ten`
29. **FP-29 · Worth ~a factor 4.** `1836 + 2Lσ` with `σ = 29/24` is
    `1836 + 29·(L/12)`; for every target `t ≥ 1836` some `1836 + p·(L/12)` is
    within `1.5×10⁻⁶` relative, against an achieved `3.74×10⁻⁷`.
    `protonPred_eq`, `proton_generic_guarantee`,
    `proton_fit_beats_generic_by_four`
30. **FP-30 · Derived.** The general no-miracle bound: a family of `N` candidate
    predictions matches only a set of targets of Lebesgue measure `≤ 2Nδ`; if
    `2Nδ` is smaller than the plausible range, some target is missed — which is
    precisely when a hit would have been informative.
    `fit_capacity`, `unmatched_target_exists`
31. **FP-31 · Derived (empty).** Level 2 of the framework's "seed hierarchy" is
    definitional: `13L = w` and `ℳ/13 = 1 + L` are the definition of `L`
    rewritten.
    `derived_layer_is_definitional`

## Stage 5 — The decorative arithmetic (`Triad.lean`)

32. **FP-32 · Derived.** `3, 6, 9` is one number, not three: `6 = 3·2` signed
    directions and `9 = 3²` ordered pairs follow from fixing 3 axes.
    `tgic_counts`
33. **FP-33 · Generic.** Any three-element set gives the same counts, so
    exhibiting `3, 6, 9` cannot distinguish the UBP substrate from anything
    else.
    `tgic_counts_generic`
34. **FP-34 · Chosen.** Even the `9` is conventional: three axes support `3`
    unordered distinct pairs, `6` unordered pairs with repetition, `9` ordered
    pairs.
    `interaction_counts_differ`
35. **FP-35 · Generic.** `24` has 8 divisors and equals `4!`, `2·12`, `3·8`,
    `2³·3` and `23+1`; matching a structure to *a* decomposition of 24 is
    close to costless.  Contrast FP-15, where the forced number is 23.
    `twentyfour_decompositions`

## Bridges to the parent audit (`Findings.lean`)

36. **B-1.** FP-12 is realised by the actual Golay code: the weight-4 pattern
    `30` carries the all-ones codeword to a different codeword of weight 16,
    while the weight-4 pattern `15` is still corrected.
    `bridge_even_distance_is_realised` (quoting `UBP.League2.weight_four_can_escape`)
37. **B-2.** FP-24 is where the free choice enters physics: `⌊ℳ⌋ = 13` versus
    `⌊πe/φ⌋ = 5`, and every downstream formula is a rational expression in the
    chosen quantity.
    `bridge_hull_is_a_choice`

## Open (not settled by anyone)

38. **O-1 · Open.** Algebraic independence of `π` and `e` over `ℚ`.  Without it
    the framework's *minimality/necessity* argument for the seed triple is not
    established, and the irrationality of `ℳ = πφe`, `w` and `L` is unknown.
    Recorded in the parent study (`UBP/OpenClaims.lean`, `docs/VERDICTS.md`);
    the first-principles chain does not improve on it.
39. **O-2 · Open here, classical elsewhere.** Transcendence of `π` (Lindemann)
    and of `e` (Hermite) — true, but absent from the pinned Mathlib, so used
    only as explicit hypotheses.
40. **O-3 · Open here.** That `n = 23` is the *only* non-trivial perfect
    3-error-correcting binary length at any `n` (van Lint–Tietäväinen).  FP-15
    verifies it exhaustively for `n ≤ 2000`.

---

## The chain in one paragraph

A distinction is the least a substrate can carry (FP-1, FP-2); `n` of them give
`2ⁿ` states (FP-3); the only reversible unary operation is the toggle (FP-4);
the two-element carrier is the field `ZMod 2` (FP-5), so the state space is
`(ZMod 2)ⁿ`, in which every element is self-inverse (FP-6) and commutativity is
a theorem (FP-7).  Toggle-count is then the substrate's metric (FP-8, FP-9),
unique decoding within radius `t` needs minimum distance `2t+1` (FP-10, FP-11),
and even minimum distance always leaves an ambiguous state (FP-12).  Counting
balls (FP-13) gives the sphere-packing bound (FP-14), whose equality case for
three-error correction picks out the lengths 7 and 23 and no others below 2000
(FP-15, FP-16); at length 24 the same code leaves 43 % of the space uncovered
(FP-17), so 24 is a self-duality preference, not a necessity (FP-18).  Up to
here every quantity is an integer, and no seed is a ratio of integers (FP-19):
`π, φ, e` enter as an independent input.  Each is forced by the rôle it is given
(FP-20 – FP-22) and the three are distinct (FP-23), but the rule that multiplies
them into `ℳ` and reads off 13 is not forced (FP-24).  Finally the numerical
agreements: a lattice of candidate values approximates every target to half its
spacing (FP-25), which already accounts for the `α⁻¹` fit (FP-26, FP-27), leaves
the muon fit worth one order of magnitude (FP-28) and the proton fit worth a
factor four (FP-29); the general bound is FP-30, and the intermediate hierarchy
layer is definitional (FP-31).  The decorative arithmetic 3, 6, 9 and 24 is
generic (FP-32 – FP-35).
