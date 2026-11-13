import UBP.SeedClasses

set_option autoImplicit false

/-!
# Stage 3 — the seeds: what is forced, and what is chosen

Stages 0–2 are pure combinatorics: distinctions, toggles, counts.  Every number
produced there is a natural number.  The UBP framework now introduces three real
numbers, `π`, `φ` and `e`, and calls them the *seeds* of the substrate.  A
first-principles investigation has to ask two separate questions:

1. Can the seeds be **derived** from the substrate of Stages 0–2?
2. Given that one wants them, is each of them **forced** by the rôle it is
   asked to play?

The answers proved here are: **no** to the first, and **yes** to the second — a
combination which is more interesting than either the framework's claim ("the
seeds generate everything") or a flat rejection.

Findings (FP-19 … FP-24):

* **FP-19** No seed is a ratio of substrate counts.  Everything Stages 0–2
  produce is an integer; each seed is irrational, hence not the value of any
  rational expression with integer inputs (`seeds_not_ratio_of_counts`).
  So the seeds are an **independent input**, not a consequence of the binary
  principle.  This is the single most important structural finding of the
  sub-study.  It is sharpened by **FP-19a** and **FP-19b**: `φ` is algebraic, so
  a substrate that can solve quadratics reaches it from its own integers, while
  `π` and `e` are reachable by no algebraic operation at all — conditionally on
  Lindemann's and Hermite's theorems, carried here as hypotheses
  (`phi_reachable_by_root_extraction`, `pi_e_not_algebraically_reachable`).
* **FP-20** `φ` *is* forced by its rôle: it is the unique positive real
  satisfying one-step self-similarity `x² = x + 1` (`phi_unique_positive_root`).
* **FP-21** `π` is forced by its rôle: it is the least positive zero of `sin`,
  i.e. the first closure of a rotation (`pi_least_positive_zero`).
* **FP-22** `e` is forced by its rôle: it is the unique base whose exponential
  has unit growth rate at the origin (`e_unique_unit_growth_base`).
* **FP-23** The three specifications are logically independent of one another
  *as specifications*: the three numbers are distinct and each is irrational, and
  `φ` is algebraic while — conditional on the classical theorems of Hermite and
  Lindemann, which the pinned Mathlib does not carry — `π` and `e` are not.
  This is inherited from the parent study (`UBP.phi_isAlgebraic`,
  `UBP.seeds_irrational`, `UBP.seeds_distinct`).
* **FP-24** The *combining rule* is not forced.  `⌊π φ e⌋ = 13` is true, but so
  are `⌊π e / φ⌋ = 5`, `⌊π φ² e⌋ = 22` and `⌊π φ e²⌋ = 37`
  (`hull_alternatives`).  Reading "13" out of the seeds requires the further,
  unjustified choice of the monomial `π¹ φ¹ e¹`; nothing in Stages 0–3 selects
  it.
-/

namespace UBPFirstPrinciples

open UBP

/-! ## FP-19  The seeds are an input, not an output -/

/-- Every quantity produced by Stages 0–2 is a natural number, and the ratio of
two such quantities is rational.  No seed is such a ratio. -/
theorem seeds_not_ratio_of_counts (p q : ℤ) :
    ((p : ℝ) / q ≠ UBP.phi) ∧ ((p : ℝ) / q ≠ UBP.eSeed) ∧ ((p : ℝ) / q ≠ Real.pi) := by
  obtain ⟨hphi, he, hpi⟩ := UBP.seeds_irrational
  have hrat : ((p : ℝ) / q) = ((p / q : ℚ) : ℝ) := by push_cast; ring
  refine ⟨?_, ?_, ?_⟩
  · intro h; exact hphi ⟨p / q, by rw [← hrat, h]⟩
  · intro h; exact he ⟨p / q, by rw [← hrat, h]⟩
  · intro h; exact hpi ⟨p / q, by rw [← hrat, h]⟩

/-- **FP-19a.**  The three seeds are not on the same footing as inputs: `φ` is
algebraic, so a substrate able to solve quadratics reaches it from its own
integers. -/
theorem phi_reachable_by_root_extraction :
    IsAlgebraic ℚ UBP.phi ∧ UBP.phi = (1 + Real.sqrt 5) / 2 :=
  ⟨UBP.phi_isAlgebraic, UBP.phi_eq⟩

/-- **FP-19b.**  `π` and `e`, by contrast, are reachable by no algebraic
operation at all — conditionally on the classical transcendence theorems of
Lindemann and Hermite, which the pinned Mathlib does not carry and which are
therefore taken as explicit hypotheses. -/
theorem pi_e_not_algebraically_reachable (hpi : Transcendental ℚ Real.pi)
    (he : Transcendental ℚ UBP.eSeed) :
    ¬ IsAlgebraic ℚ Real.pi ∧ ¬ IsAlgebraic ℚ UBP.eSeed :=
  ⟨hpi, he⟩

/-! ## FP-20  `φ` is forced by self-similarity -/

/-- The golden ratio is the unique positive solution of one-step
self-reference. -/
theorem phi_unique_positive_root (x : ℝ) (hx : 0 < x) : x ^ 2 = x + 1 ↔ x = UBP.phi := by
  constructor
  · intro h
    have hphi := UBP.phi_sq
    have hpos : 0 < UBP.phi := by
      have := UBP.phi_enc.pos (by norm_num); exact this
    have hgt1 : (1 : ℝ) < UBP.phi := by
      have := UBP.phi_enc.1; norm_num at this; linarith
    have key : (x - UBP.phi) * (x + UBP.phi - 1) = 0 := by nlinarith [h, hphi]
    rcases mul_eq_zero.mp key with h1 | h1
    · linarith
    · linarith
  · rintro rfl; exact UBP.phi_sq

/-! ## FP-21  `π` is forced by closure -/

/-- `π` is the least positive zero of the sine: the first return of a
rotation. -/
theorem pi_least_positive_zero :
    Real.sin Real.pi = 0 ∧ ∀ x : ℝ, 0 < x → x < Real.pi → Real.sin x ≠ 0 := by
  refine ⟨Real.sin_pi, fun x hx hxp => ne_of_gt (Real.sin_pos_of_pos_of_lt_pi hx hxp)⟩

/-! ## FP-22  `e` is forced by accumulation -/

/-- For a positive base `a`, the growth rate of `a ^ x` at the origin is
`log a`. -/
theorem deriv_rpow_zero (a : ℝ) (ha : 0 < a) : deriv (fun x : ℝ => a ^ x) 0 = Real.log a := by
  have hfun : (fun x : ℝ => a ^ x) = fun x : ℝ => Real.exp (Real.log a * x) := by
    funext x; rw [Real.rpow_def_of_pos ha]
  rw [hfun]
  have h : HasDerivAt (fun x : ℝ => Real.exp (Real.log a * x))
      (Real.exp (Real.log a * 0) * Real.log a) 0 := by
    simpa using (Real.hasDerivAt_exp (Real.log a * 0)).comp 0
      ((hasDerivAt_id (0 : ℝ)).const_mul (Real.log a))
  simpa using h.deriv

/-- `e` is the unique base whose exponential grows at unit rate at the
origin. -/
theorem e_unique_unit_growth_base (a : ℝ) (ha : 0 < a) :
    deriv (fun x : ℝ => a ^ x) 0 = 1 ↔ a = UBP.eSeed := by
  rw [deriv_rpow_zero a ha]
  constructor
  · intro h; rw [UBP.eSeed, ← h, Real.exp_log ha]
  · rintro rfl; simp [UBP.eSeed]

/-! ## FP-23  The three specifications are distinct -/

theorem seeds_pairwise_distinct : UBP.phi < UBP.eSeed ∧ UBP.eSeed < Real.pi :=
  UBP.seeds_distinct

theorem seeds_all_irrational :
    Irrational UBP.phi ∧ Irrational UBP.eSeed ∧ Irrational Real.pi :=
  UBP.seeds_irrational

/-! ## FP-24  The combining rule is a free choice -/

theorem phiSq_enc : Enc (UBP.phi ^ 2) 2.61803398874989484 2.61803398874989485 :=
  ((UBP.phi_enc.pow (by norm_num) 2)).mono (by norm_num) (by norm_num)

theorem pi_mul_e_enc : Enc (Real.pi * UBP.eSeed) 8.53973422267356706 8.53973422267356707 :=
  (UBP.pi_enc.mul UBP.eSeed_enc (by norm_num) (by norm_num)).mono (by norm_num) (by norm_num)

/-- Four equally simple monomials in the seeds, four different "hulls":
`⌊π φ e⌋ = 13`, `⌊π e / φ⌋ = 5`, `⌊π φ² e⌋ = 22`, `⌊π φ e²⌋ = 37`. -/
theorem hull_alternatives :
    ⌊UBP.monad⌋ = 13 ∧ ⌊Real.pi * UBP.eSeed / UBP.phi⌋ = 5 ∧
      ⌊Real.pi * UBP.phi ^ 2 * UBP.eSeed⌋ = 22 ∧ ⌊Real.pi * UBP.phi * UBP.eSeed ^ 2⌋ = 37 := by
  refine ⟨UBP.monad_floor, ?_, ?_, ?_⟩
  · have h := pi_mul_e_enc.div UBP.phi_enc (by norm_num) (by norm_num)
    have h5 : (5 : ℝ) ≤ Real.pi * UBP.eSeed / UBP.phi := by
      have := h.1; norm_num at this ⊢; linarith
    have h6 : Real.pi * UBP.eSeed / UBP.phi < 6 := by
      have := h.2; norm_num at this ⊢; linarith
    exact Int.floor_eq_iff.mpr ⟨by exact_mod_cast h5, by push_cast; linarith⟩
  · have h := (UBP.pi_enc.mul phiSq_enc (by norm_num) (by norm_num)).mul UBP.eSeed_enc
      (by norm_num) (by norm_num)
    have h22 : (22 : ℝ) ≤ Real.pi * UBP.phi ^ 2 * UBP.eSeed := by
      have := h.1; norm_num at this ⊢; linarith
    have h23 : Real.pi * UBP.phi ^ 2 * UBP.eSeed < 23 := by
      have := h.2; norm_num at this ⊢; linarith
    exact Int.floor_eq_iff.mpr ⟨by exact_mod_cast h22, by push_cast; linarith⟩
  · have heSq : Enc (UBP.eSeed ^ 2) 7.38905609893065022 7.38905609893065024 :=
      ((UBP.eSeed_enc.pow (by norm_num) 2)).mono (by norm_num) (by norm_num)
    have h := (UBP.pi_enc.mul UBP.phi_enc (by norm_num) (by norm_num)).mul heSq
      (by norm_num) (by norm_num)
    have h37 : (37 : ℝ) ≤ Real.pi * UBP.phi * UBP.eSeed ^ 2 := by
      have := h.1; norm_num at this ⊢; linarith
    have h38 : Real.pi * UBP.phi * UBP.eSeed ^ 2 < 38 := by
      have := h.2; norm_num at this ⊢; linarith
    exact Int.floor_eq_iff.mpr ⟨by exact_mod_cast h37, by push_cast; linarith⟩

end UBPFirstPrinciples
