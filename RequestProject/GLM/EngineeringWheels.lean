/-
# Engineering languages: formula wheels, the Smith chart, and delta-sigma

The engineering surface of the GLM (`overlay/glm_universal/engineering/`)
answers questions in electrical and mechanical terms.  Every rule it relies on
to *license* an answer, rather than merely compute one, is stated and proved
here.

**Formula wheels** (`wheels.py`).  A formula is read as its relation vector,
and it *follows from* a wheel exactly when that vector lies in the rational
span of the axioms' vectors.
* `derivable_consistent` — a formula derived from dimensionally consistent
  axioms is dimensionally consistent.  Consistency is necessary for
  derivability; the negative controls show it is not sufficient.
* `ohm_power_derivable`, `ohm_negative_control_not_derivable` — the Ohm wheel,
  concretely: `P = V²/R` is in the span of `V = IR` and `P = VI`, and
  `P = V·R` is not.
* `translate_derivable` — a linear translation (an electro-mechanical analogy)
  that sends every axiom of one wheel into the span of the other sends every
  derived formula there too.  This is why a derivation in the circuit wheel,
  carried across the force-voltage analogy, is a derivation in the mechanical
  wheel.

**The Smith chart** (`smith.py`), over `ℂ`.
* `smith_round_trip` — `z ↦ Γ ↦ z` is the identity away from the pole.
* `smith_admittance_dual` — `Γ(1/z) = -Γ(z)`.
* `smith_passive` — a passive load (`0 ≤ Re z`) has `‖Γ‖ ≤ 1`, and
  `smith_lossless_iff` — with equality exactly on the imaginary axis.

**Delta-sigma** (`delta_sigma.py`), for the first-order loop of
`DeltaSigma.lean`.
* `ds_bits_periodic_iff` — the bitstream of `t ∈ [0,1)` has period `P` if and
  only if `P·t` is an integer.
* `ds_rational_period_iff` — so for `t = p/q` in lowest terms the periods are
  exactly the multiples of `q`: the least period is `q`.
* `ds_irrational_aperiodic` — and for irrational `t` no positive `P` is a
  period: the bitstream is never periodic.
-/
import RequestProject.GLM.Sturmian

namespace GLM.Engineering

open GLM.Info

/-! ## 1. Formula wheels: derivability as span membership -/

section Wheels

variable {V W : Type*} [AddCommGroup V] [Module ℚ V] [AddCommGroup W] [Module ℚ W]

/-- **Derived from consistent axioms, consistent.**  If the dimension map `D`
kills every axiom, it kills everything in their span. -/
theorem derivable_consistent (D : V →ₗ[ℚ] W) {A : Set V}
    (hA : ∀ a ∈ A, D a = 0) {t : V} (ht : t ∈ Submodule.span ℚ A) : D t = 0 :=
  (Submodule.span_le (p := LinearMap.ker D)).2 (fun a ha => hA a ha) ht

/-- **Translation carries derivations.**  A linear map sending every axiom of
`A` into the span of `B` sends the whole span of `A` there. -/
theorem translate_derivable (T : V →ₗ[ℚ] W) {A : Set V} {B : Set W}
    (hA : ∀ a ∈ A, T a ∈ Submodule.span ℚ B) {t : V}
    (ht : t ∈ Submodule.span ℚ A) : T t ∈ Submodule.span ℚ B :=
  (Submodule.span_le (p := (Submodule.span ℚ B).comap T)).2 (fun a ha => hA a ha) ht

end Wheels

/-- Relation vectors of the Ohm wheel, coordinates `(V, I, R, P)`:
`V = I R` is `V¹ I⁻¹ R⁻¹ = 1`. -/
def ohmAxiomVIR : Fin 4 → ℚ := ![1, -1, -1, 0]

/-- `P = V I` is `V⁻¹ I⁻¹ P¹ = 1`. -/
def ohmAxiomPVI : Fin 4 → ℚ := ![-1, -1, 0, 1]

/-- **`P = V²/R` follows from the Ohm wheel.** -/
theorem ohm_power_derivable :
    (![-2, 0, 1, 1] : Fin 4 → ℚ) ∈ Submodule.span ℚ {ohmAxiomVIR, ohmAxiomPVI} := by
  rw [Submodule.mem_span_pair]
  refine ⟨-1, 1, ?_⟩
  ext i
  fin_cases i <;> (simp [ohmAxiomVIR, ohmAxiomPVI]; try norm_num)

/-- **`P = V·R` does not.**  The wheel's negative control is outside the span. -/
theorem ohm_negative_control_not_derivable :
    (![-1, 0, -1, 1] : Fin 4 → ℚ) ∉ Submodule.span ℚ {ohmAxiomVIR, ohmAxiomPVI} := by
  rw [Submodule.mem_span_pair]
  rintro ⟨a, b, h⟩
  have h1 := congrFun h 1
  have h2 := congrFun h 2
  have h3 := congrFun h 3
  simp [ohmAxiomVIR, ohmAxiomPVI] at h1 h2 h3
  linarith

/-! ## 2. The Smith chart -/

/-- The reflection coefficient of a normalised impedance. -/
noncomputable def smithGamma (z : ℂ) : ℂ := (z - 1) / (z + 1)

/-- The normalised impedance of a reflection coefficient. -/
noncomputable def smithZ (g : ℂ) : ℂ := (1 + g) / (1 - g)

/-- **Round trip.** -/
theorem smith_round_trip {z : ℂ} (hz : z ≠ -1) : smithZ (smithGamma z) = z := by
  have h : z + 1 ≠ 0 := fun h => hz (by linear_combination h)
  unfold smithZ smithGamma
  have e1 : 1 + (z - 1) / (z + 1) = 2 * z / (z + 1) := by field_simp; ring
  have e2 : 1 - (z - 1) / (z + 1) = 2 / (z + 1) := by field_simp; ring
  rw [e1, e2]
  field_simp

/-- **Admittance duality.** -/
theorem smith_admittance_dual {z : ℂ} (h0 : z ≠ 0) (h1 : z ≠ -1) :
    smithGamma z⁻¹ = -smithGamma z := by
  have h : z + 1 ≠ 0 := fun h => h1 (by linear_combination h)
  unfold smithGamma
  have e1 : z⁻¹ - 1 = (1 - z) / z := by field_simp
  have e2 : z⁻¹ + 1 = (1 + z) / z := by field_simp
  rw [e1, e2, div_div_div_cancel_right₀ h0]
  rw [neg_div', div_eq_div_iff (by rwa [add_comm]) h]
  ring

/-- **Passive loads land in the unit disc.** -/
theorem smith_passive {z : ℂ} (hz : 0 ≤ z.re) : ‖smithGamma z‖ ≤ 1 := by
  have h : z + 1 ≠ 0 := by
    intro h; have := congrArg Complex.re h; simp at this; linarith
  unfold smithGamma
  rw [norm_div, div_le_one (norm_pos_iff.2 h)]
  rw [← sq_le_sq₀ (norm_nonneg _) (norm_nonneg _), Complex.sq_norm, Complex.sq_norm,
    Complex.normSq_apply, Complex.normSq_apply]
  simp
  nlinarith

/-- **And on its boundary exactly when lossless.** -/
theorem smith_lossless_iff {z : ℂ} (hz : 0 ≤ z.re) :
    ‖smithGamma z‖ = 1 ↔ z.re = 0 := by
  have h : z + 1 ≠ 0 := by
    intro h; have := congrArg Complex.re h; simp at this; linarith
  unfold smithGamma
  rw [norm_div, div_eq_one_iff_eq (norm_ne_zero_iff.2 h)]
  rw [← sq_eq_sq₀ (norm_nonneg _) (norm_nonneg _), Complex.sq_norm, Complex.sq_norm,
    Complex.normSq_apply, Complex.normSq_apply]
  simp
  constructor <;> intro H <;> nlinarith

/-! ## 3. Delta-sigma periodicity -/

/-- **The periods of the bitstream.**  For `t ∈ [0, 1)`, `P` is a period of the
first-order bitstream exactly when `P·t` is an integer. -/
theorem ds_bits_periodic_iff {t : ℝ} (ht0 : 0 ≤ t) (ht1 : t < 1) (P : ℕ) :
    (∀ n, dsBit t (n + P) = dsBit t n) ↔ ∃ m : ℤ, (P : ℝ) * t = m := by
  set g : ℕ → ℤ := fun n => ⌊(n : ℝ) * t⌋ with hg
  have hstep : ∀ n, (dsBit t n : ℤ) = g (n + 1) - g n := by
    intro n
    rw [dsBit_eq_floor_diff ht0 ht1 n, hg]
    push_cast
    ring_nf
  constructor
  · intro hper
    have hshift : ∀ n, g (n + P) - g n = g P := by
      intro n
      induction n with
      | zero => simp [hg]
      | succ k ih =>
          have h1 := hstep (k + P)
          have h2 := hstep k
          rw [hper k] at h1
          have e : k + 1 + P = k + P + 1 := by omega
          rw [e]
          linarith
    have hmul : ∀ k : ℕ, g (k * P) = k * g P := by
      intro k
      induction k with
      | zero => simp [hg]
      | succ j ih =>
          have := hshift (j * P)
          rw [show (j + 1) * P = j * P + P by ring]
          push_cast
          linarith
    refine ⟨g P, ?_⟩
    set x : ℝ := (P : ℝ) * t with hx
    have hfr : Int.fract x = 0 := by
      by_contra hne
      have hpos : 0 < Int.fract x := lt_of_le_of_ne (Int.fract_nonneg x) (Ne.symm hne)
      obtain ⟨k, hk⟩ := exists_nat_gt (1 / Int.fract x)
      have hkx : (k : ℝ) * Int.fract x > 1 := by
        rw [div_lt_iff₀ hpos] at hk
        linarith
      have hfl := hmul k
      simp only [hg] at hfl
      have hlt : ((k * P : ℕ) : ℝ) * t < (⌊((k * P : ℕ) : ℝ) * t⌋ : ℝ) + 1 :=
        Int.lt_floor_add_one _
      rw [hfl] at hlt
      push_cast at hlt
      have hdec : x = (⌊x⌋ : ℝ) + Int.fract x := (Int.floor_add_fract x).symm
      have : (k : ℝ) * x < (k : ℝ) * (⌊x⌋ : ℝ) + 1 := by
        rw [hx]; nlinarith [hlt]
      rw [hdec] at this
      nlinarith
    have := Int.floor_add_fract x
    rw [hfr, add_zero] at this
    simp only [hg]
    exact this.symm
  · rintro ⟨m, hm⟩ n
    have h1 := hstep (n + P)
    have h2 := hstep n
    have key : ∀ j : ℕ, g (j + P) = g j + m := by
      intro j
      simp only [hg]
      push_cast
      rw [add_mul, hm, Int.floor_add_intCast]
    have e : n + P + 1 = (n + 1) + P := by omega
    rw [e, key, key] at h1
    have : (dsBit t (n + P) : ℤ) = dsBit t n := by linarith
    exact_mod_cast this

/-- **A rational input `p/q` in lowest terms has periods exactly the multiples
of `q`**, so its least period is `q`. -/
theorem ds_rational_period_iff {p q : ℕ} (hq : 0 < q) (hpq : p < q)
    (hcop : Nat.Coprime p q) (P : ℕ) :
    (∀ n, dsBit ((p : ℝ) / q) (n + P) = dsBit ((p : ℝ) / q) n) ↔ q ∣ P := by
  have hqR : (0 : ℝ) < q := by exact_mod_cast hq
  have ht0 : (0 : ℝ) ≤ (p : ℝ) / q := div_nonneg (Nat.cast_nonneg _) hqR.le
  have ht1 : (p : ℝ) / q < 1 := by
    rw [div_lt_one hqR]; exact_mod_cast hpq
  rw [ds_bits_periodic_iff ht0 ht1 P]
  constructor
  · rintro ⟨m, hm⟩
    have hR : ((P * p : ℕ) : ℝ) = (m : ℝ) * q := by
      push_cast
      field_simp at hm
      linarith
    have hZ : ((P * p : ℕ) : ℤ) = m * q := by exact_mod_cast hR
    have hdvdZ : (q : ℤ) ∣ ((P * p : ℕ) : ℤ) := ⟨m, by rw [hZ]; ring⟩
    have hdvd : q ∣ P * p := by exact_mod_cast hdvdZ
    exact (Nat.Coprime.dvd_of_dvd_mul_right hcop.symm hdvd)
  · rintro ⟨k, rfl⟩
    refine ⟨(k * p : ℕ), ?_⟩
    push_cast
    field_simp

/-- **An irrational input is never periodic.** -/
theorem ds_irrational_aperiodic {t : ℝ} (ht0 : 0 ≤ t) (ht1 : t < 1)
    (hirr : Irrational t) {P : ℕ} (hP : 0 < P) :
    ∃ n, dsBit t (n + P) ≠ dsBit t n := by
  by_contra h
  push_neg at h
  obtain ⟨m, hm⟩ := (ds_bits_periodic_iff ht0 ht1 P).1 h
  have hPR : (P : ℝ) ≠ 0 := by exact_mod_cast hP.ne'
  apply (irrational_iff_ne_rational t).1 hirr m P
  · exact_mod_cast hP.ne'
  · have hZ : ((P : ℤ) : ℝ) = (P : ℝ) := by push_cast; rfl
    rw [hZ, eq_div_iff hPR]
    linarith

end GLM.Engineering
