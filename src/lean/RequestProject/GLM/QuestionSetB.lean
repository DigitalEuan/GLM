module

public import Mathlib

/-!
# The outside question sets of Phase 89: the facts the question frames rest on

The formal half of `studies/QUESTION_SET_B_STUDY.md`.  The question frames of
`glm_universal/runtime/question_frames.py` and `outside_frames.py` answer the
outside question sets' kinds of question exactly; this file proves, once and
in general, the rules several of those frames decide by, and the exact values
the audit of the study relies on.

**Rules the frames decide by.**

* `int_linear_solvable_iff` — `a x + b y = c` has an integer solution exactly
  when `gcd a b ∣ c`: the rule the `integer_system` frame applies (and why
  Set B's `3x + 5y = 1` is decided, not `INTEGER_UNDECIDED`).
* `int_entails_ceil` / `rat_not_entails` — over `ℤ`, `2x ≥ 5` entails `x ≥ 3`;
  over `ℚ` it does not (the `integer_entails` frame's two verdicts).
* `weight_five_miscorrects` — if a weight-5 error pattern lies inside an
  octad (which the Steiner system `S(5,8,24)`, `GLM.Golay24.unique_octad`,
  guarantees), the received word is at distance 3 from a *different*
  codeword: the decoder's answer is silently wrong, so a declared weight-5
  error must be refused (`error_weight`, Set B `O1-003`).
* `routh_marginal_root` — at the marginal gain of a cubic loop,
  `s = iω` with `ω² = a₁/a₃` is a root of the characteristic polynomial: the
  sustained oscillation the `routh_cubic` frame reports.
* `nyquist_inconsistent` — `Z = N + P` with `Z` a count: `N + P < 0` admits
  no closed loop at all (`nyquist`, Outside O1 EE-VH2).
* `upper_rule_safe` — the upper-credible rule of the production contract
  (variant D): when confidence falls as the rate rises and the true rate is
  at most the credible set's upper end, the stated confidence is at most the
  true one.

**Exact values the audit checks.** `golay23_perfect`, `golay24_not_perfect`,
`deep_hole_cosets` (the sphere-packing count behind `golay_perfect`),
`fringe_least` (`m₁ = 3`), `wiener_taps` (`h₀ = 86/161`, `h₁ = 40/161`),
`per_unit_rebase` (`0.20` p.u.), `reflection_coefficient` and `vswr_value`
(`Γ = -1/5 - 2i/5`, `VSWR = (3 + √5)/2`).
-/

@[expose] public section

namespace GLM.QuestionSetB

/-! ## 1. Integer decisions -/

/-- `a x + b y = c` is solvable over `ℤ` iff `gcd a b ∣ c`. -/
theorem int_linear_solvable_iff (a b c : ℤ) :
    (∃ x y : ℤ, a * x + b * y = c) ↔ (Int.gcd a b : ℤ) ∣ c := by
  constructor
  · rintro ⟨x, y, rfl⟩
    exact dvd_add (dvd_mul_of_dvd_left (Int.gcd_dvd_left a b) x)
      (dvd_mul_of_dvd_left (Int.gcd_dvd_right a b) y)
  · rintro ⟨k, rfl⟩
    refine ⟨Int.gcdA a b * k, Int.gcdB a b * k, ?_⟩
    rw [Int.gcd_eq_gcd_ab a b]
    ring

/-- Set B `O1-013`: `3x + 5y = 1` is solvable, witnessed by `x = 2, y = -1`. -/
theorem three_five_witness : (3 : ℤ) * 2 + 5 * (-1) = 1 := by norm_num

/-- Over the integers `2x ≥ 5` entails `x ≥ 3`. -/
theorem int_entails_ceil (x : ℤ) (h : 5 ≤ 2 * x) : 3 ≤ x := by omega

/-- Over the rationals it does not: `x = 5/2` is a counterexample. -/
theorem rat_not_entails : ¬ ∀ x : ℚ, 5 ≤ 2 * x → 3 ≤ x := by
  intro h
  have := h (5 / 2) (by norm_num)
  norm_num at this

/-! ## 2. A declared weight-5 error is miscorrected -/

/-- A five-point error inside an eight-point octad leaves the read three
points from the codeword `sent + octad`: closer than the five points to the
codeword sent. -/
theorem weight_five_miscorrects {α : Type*} [DecidableEq α] (T O : Finset α)
    (hT : T.card = 5) (hO : O.card = 8) (hsub : T ⊆ O) :
    (symmDiff T O).card = 3 ∧ (symmDiff T O).card < T.card := by
  have hsd : symmDiff T O = O \ T := by
    rw [symmDiff_def, Finset.sdiff_eq_empty_iff_subset.mpr hsub]
    simp
  have hc : (O \ T).card = 3 := by
    rw [Finset.card_sdiff_of_subset hsub, hO, hT]
  rw [hsd, hc, hT]
  exact ⟨rfl, by norm_num⟩

/-! ## 3. Control: Routh's marginal root, Nyquist's count -/

/-- At the marginal gain of a cubic `a₃ s³ + a₂ s² + a₁ s + c` (Routh's
`a₂ a₁ = a₃ c`), `s = i ω` with `ω² = a₁ / a₃` is a root. -/
theorem routh_marginal_root (a₃ a₂ a₁ c ω : ℝ) (h3 : a₃ ≠ 0)
    (hω : ω ^ 2 = a₁ / a₃) (hc : a₂ * a₁ = a₃ * c) :
    (a₃ : ℂ) * (Complex.I * ω) ^ 3 + a₂ * (Complex.I * ω) ^ 2
      + a₁ * (Complex.I * ω) + c = 0 := by
  have h1 : a₁ = a₃ * ω ^ 2 := by rw [hω]; field_simp
  have h2 : c = a₂ * ω ^ 2 := by
    have : a₃ * c = a₃ * (a₂ * ω ^ 2) := by rw [← hc, h1]; ring
    exact mul_left_cancel₀ h3 this
  apply Complex.ext
  · simp [h1, h2, pow_succ]
  · simp [h1, h2, pow_succ]
    ring

/-- Outside O1 EE-VH2: a closed loop has `Z = N + P ≥ 0` right-half-plane
poles, so encirclements with `N + P < 0` describe no system at all. -/
theorem nyquist_inconsistent (N P : ℤ) (h : N + P < 0) :
    ¬ ∃ Z : ℕ, (Z : ℤ) = N + P := by
  rintro ⟨Z, hZ⟩
  omega

/-! ## 4. The production contract's upper-credible rule -/

/-- With confidence antitone in the rate, reading it at an upper end `hi` of
the credible set that bounds the true rate `r` never overstates it. -/
theorem upper_rule_safe (conf : ℚ → ℚ) (hanti : Antitone conf) (r hi : ℚ)
    (hr : r ≤ hi) : conf hi ≤ conf r :=
  hanti hr

/-! ## 5. The exact values of the audit -/

/-- The `[23, 12, 7]` Golay code is perfect: radius-3 spheres tile `F₂²³`. -/
theorem golay23_perfect :
    2 ^ 12 * (Nat.choose 23 0 + Nat.choose 23 1 + Nat.choose 23 2
      + Nat.choose 23 3) = 2 ^ 23 := by decide

/-- The extended `[24, 12, 8]` code is not: radius-3 spheres leave words out. -/
theorem golay24_not_perfect :
    2 ^ 12 * (Nat.choose 24 0 + Nat.choose 24 1 + Nat.choose 24 2
      + Nat.choose 24 3) < 2 ^ 24 := by decide

/-- The words left out fill the 1771 cosets of weight 4, six tetrads each
(the coset counts `1, 24, 276, 2024, 1771` of `rate_posterior.COSET_COUNTS`). -/
theorem deep_hole_cosets :
    1 + 24 + 276 + 2024 + 1771 = 2 ^ 12 ∧ 6 * 1771 = Nat.choose 24 4 ∧
      Nat.choose 24 1 = 24 ∧ Nat.choose 24 2 = 276 ∧ Nat.choose 24 3 = 2024 := by
  decide

/-- Outside O1 Ph-M4: the least order of the 600 nm fringe that meets a
450 nm fringe is 3. -/
theorem fringe_least :
    IsLeast {m : ℕ | 0 < m ∧ ∃ k : ℕ, 600 * m = 450 * k} 3 := by
  refine ⟨⟨by norm_num, 4, by norm_num⟩, ?_⟩
  rintro m ⟨hm, k, hk⟩
  show 3 ≤ m
  omega

/-- Outside O1 SP-VH1: the 2-tap Wiener taps solve the Wiener-Hopf equations
for `R_ss[m] = 0.8^|m|`, `σ_v² = 0.5`. -/
theorem wiener_taps :
    (3 / 2 : ℚ) * (86 / 161) + (4 / 5) * (40 / 161) = 1 ∧
      (4 / 5 : ℚ) * (86 / 161) + (3 / 2) * (40 / 161) = 4 / 5 := by
  norm_num

/-- Outside O1 EE-M3: 0.10 p.u. on 50 MVA / 13.8 kV is 0.20 p.u. on
100 MVA / 13.8 kV. -/
theorem per_unit_rebase :
    (1 / 10 : ℚ) * (100 / 50) * ((138 / 10) / (138 / 10)) ^ 2 = 1 / 5 := by
  norm_num

/-- Outside O1 EE-H3: `Γ = (Z_L - Z₀)/(Z_L + Z₀)` for `Z₀ = 50`,
`Z_L = 25 - 25i`. -/
theorem reflection_coefficient :
    ((25 - 25 * Complex.I) - 50) / ((25 - 25 * Complex.I) + 50)
      = -1 / 5 - 2 / 5 * Complex.I := by
  have h : (25 - 25 * Complex.I) + 50 ≠ 0 := by
    intro h
    have := congrArg Complex.re h
    norm_num at this
  rw [div_eq_iff h]
  ring_nf
  rw [Complex.I_sq]
  ring

/-- ... and its VSWR `(1 + |Γ|)/(1 - |Γ|)` with `|Γ| = 1/√5` is `(3 + √5)/2`. -/
theorem vswr_value :
    (1 + 1 / Real.sqrt 5) / (1 - 1 / Real.sqrt 5) = (3 + Real.sqrt 5) / 2 := by
  have h5 : Real.sqrt 5 ^ 2 = 5 := Real.sq_sqrt (by norm_num)
  have hpos : 0 < Real.sqrt 5 := Real.sqrt_pos.mpr (by norm_num)
  have hgt : 1 < Real.sqrt 5 := by nlinarith
  have hne : Real.sqrt 5 - 1 ≠ 0 := by linarith
  have hne' : 1 - 1 / Real.sqrt 5 ≠ 0 := by
    rw [sub_ne_zero, ne_comm, ne_eq, div_eq_one_iff_eq hpos.ne']
    linarith
  rw [div_eq_iff hne']
  field_simp
  nlinarith

end GLM.QuestionSetB
