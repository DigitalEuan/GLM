module

public import Mathlib
public import RequestProject.GLM.QuestionSetB

/-!
# Phase 89: the framed answers to the outside questions, proved

`studies/QUESTION_SET_B_STUDY.md` §4 lists the 27 Outside O1 questions the
question frames answer (or correctly refuse) exactly, each value checked by a
column-3 script and by a hand audit.  This file proves the answers themselves,
from each question's own givens, wherever the mathematics is in reach:

* **Control.** `routh_ee_range` and `routh_pc_range` — the Routh–Hurwitz
  condition for a cubic, solved for the gain of `K/(s(s+2)(s+4))`
  (`0 < K < 48`) and of `4K_c/((s+1)(2s+1)(3s+1))` (`-1/4 < K_c < 5/2`);
  `routh_ee_marginal` / `routh_pc_marginal` — at the marginal gain
  `s = 2√2 i` and `s = i` are roots (sustained oscillation);
  `kalman_controllable` / `kalman_observable` — both Kalman matrices have
  rank 2; `fopdt_values` / `fopdt_limit` — `3e^{-2s}/(5s+1)` step response.
* **Signals.** `aliasing_at_samples` — sampled at 1000 Hz, the 800 Hz sine is
  the 200 Hz sine negated at every sample; `convolution_values`,
  `circular_is_wrapped_linear`, `circular_four_is_linear`;
  `bilinear_transfer`, `bilinear_unit_circle`, `bilinear_infinity`;
  `ztransform_causal_roc`, `ztransform_anticausal_roc`, `ztransform_value`;
  `wiener_mse`.
* **Physics.** `well_probability` — `P(0 ≤ x ≤ L/4) = 1/4` for `n = 2`, with
  `well_normalised`.
* **Information.** `joint_entropy_values`, `mutual_information_value`;
  `huffman_length`, `huffman_kraft`, `huffman_prefix_free`,
  `huffman_optimal` (no code-length assignment satisfying Kraft's inequality
  does better than `7/4`), `huffman_entropy`; `bsc_info_le`,
  `bsc_info_uniform` (the uniform input achieves `log 2 - h(p)`),
  `bsc_capacity_value` (`p = 0.11`), `memory_channel_average`;
  `waterfill_level_unique`, `waterfill_allocation`, `waterfill_optimal`,
  `waterfill_capacity`.

Entropies are in bits (`Real.logb 2`) unless a statement says otherwise;
`Real.binEntropy` is Mathlib's binary entropy in nats.
-/

@[expose] public section

namespace GLM.QuestionSetBAnswers

open Real Filter Topology

/-! ## 1. Control -/

/-- The Routh–Hurwitz condition for `a₃ s³ + a₂ s² + a₁ s + a₀`: every
coefficient positive and `a₂ a₁ > a₃ a₀` (the first column of the Routh array
has no sign change). -/
def routhCubic (a3 a2 a1 a0 : ℝ) : Prop :=
  0 < a3 ∧ 0 < a2 ∧ 0 < a1 ∧ 0 < a0 ∧ a3 * a0 < a2 * a1

/-- EE-M2: the closed loop of `K / (s (s + 2) (s + 4))` has characteristic
polynomial `s³ + 6 s² + 8 s + K`. -/
theorem routh_ee_char (s K : ℝ) : s * (s + 2) * (s + 4) + K = s ^ 3 + 6 * s ^ 2 + 8 * s + K := by
  ring

/-- EE-M2: stable exactly for `0 < K < 48`. -/
theorem routh_ee_range (K : ℝ) : routhCubic 1 6 8 K ↔ 0 < K ∧ K < 48 := by
  unfold routhCubic
  constructor
  · rintro ⟨-, -, -, h0, h⟩; exact ⟨h0, by linarith⟩
  · rintro ⟨h0, h⟩; exact ⟨by norm_num, by norm_num, by norm_num, h0, by linarith⟩

/-- EE-M2: at `K = 48`, `s = 2√2 i` is a root (sustained oscillation at
`ω = 2√2` rad/s). -/
theorem routh_ee_marginal :
    ((1 : ℝ) : ℂ) * (Complex.I * ((2 * Real.sqrt 2 : ℝ) : ℂ)) ^ 3
      + ((6 : ℝ) : ℂ) * (Complex.I * ((2 * Real.sqrt 2 : ℝ) : ℂ)) ^ 2
      + ((8 : ℝ) : ℂ) * (Complex.I * ((2 * Real.sqrt 2 : ℝ) : ℂ)) + ((48 : ℝ) : ℂ) = 0 :=
  GLM.QuestionSetB.routh_marginal_root 1 6 8 48 (2 * Real.sqrt 2) one_ne_zero
    (by rw [mul_pow, Real.sq_sqrt (by norm_num)]; norm_num) (by norm_num)

/-- PC-H4: the closed loop of `4 K_c / ((s + 1)(2 s + 1)(3 s + 1))` has
characteristic polynomial `6 s³ + 11 s² + 6 s + (1 + 4 K_c)`. -/
theorem routh_pc_char (s Kc : ℝ) :
    (s + 1) * (2 * s + 1) * (3 * s + 1) + 4 * Kc = 6 * s ^ 3 + 11 * s ^ 2 + 6 * s + (1 + 4 * Kc) := by
  ring

/-- PC-H4: stable exactly for `-1/4 < K_c < 5/2`; the ultimate gain is
`K_cu = 5/2`. -/
theorem routh_pc_range (Kc : ℝ) : routhCubic 6 11 6 (1 + 4 * Kc) ↔ -1/4 < Kc ∧ Kc < 5/2 := by
  unfold routhCubic
  constructor
  · rintro ⟨-, -, -, h0, h⟩; exact ⟨by linarith, by linarith⟩
  · rintro ⟨h0, h⟩; exact ⟨by norm_num, by norm_num, by norm_num, by linarith, by linarith⟩

/-- PC-H4: at `K_c = 5/2`, `s = i` is a root (`ω = 1` rad/s, so the ultimate
period is `P_u = 2π`). -/
theorem routh_pc_marginal :
    ((6 : ℝ) : ℂ) * (Complex.I * ((1 : ℝ) : ℂ)) ^ 3 + ((11 : ℝ) : ℂ) * (Complex.I * ((1 : ℝ) : ℂ)) ^ 2
      + ((6 : ℝ) : ℂ) * (Complex.I * ((1 : ℝ) : ℂ)) + ((1 + 4 * (5 / 2) : ℝ) : ℂ) = 0 :=
  GLM.QuestionSetB.routh_marginal_root 6 11 6 (1 + 4 * (5 / 2)) 1 (by norm_num)
    (by norm_num) (by norm_num)

/-- PC-H1's state-space system: `A`, `B`, `C`. -/
def kA : Matrix (Fin 2) (Fin 2) ℚ := !![-2, 1; 0, -3]
def kB : Matrix (Fin 2) (Fin 1) ℚ := !![1; 1]
def kC : Matrix (Fin 1) (Fin 2) ℚ := !![1, 0]

/-- The controllability matrix `[B, AB]`. -/
def ctrb : Matrix (Fin 2) (Fin 2) ℚ :=
  Matrix.of fun i j => if j = 0 then kB i 0 else (kA * kB) i 0

/-- The observability matrix `[C; CA]`. -/
def obsv : Matrix (Fin 2) (Fin 2) ℚ :=
  Matrix.of fun i j => if i = 0 then kC 0 j else (kC * kA) 0 j

theorem ctrb_eq : ctrb = !![1, -1; 1, -3] := by
  ext i j; fin_cases i <;> fin_cases j <;>
    norm_num [ctrb, kA, kB, Matrix.mul_apply, Fin.sum_univ_two]

theorem obsv_eq : obsv = !![1, 0; -2, 1] := by
  ext i j; fin_cases i <;> fin_cases j <;>
    simp [obsv, kA, kC, Matrix.mul_apply, Fin.sum_univ_two]

/-- Completely controllable: the controllability matrix has rank 2. -/
theorem kalman_controllable : ctrb.rank = 2 := by
  have : IsUnit ctrb := by
    rw [ctrb_eq, Matrix.isUnit_iff_isUnit_det]; simp [Matrix.det_fin_two]; norm_num
  simpa using Matrix.rank_of_isUnit _ this

/-- Completely observable: the observability matrix has rank 2. -/
theorem kalman_observable : obsv.rank = 2 := by
  have : IsUnit obsv := by
    rw [obsv_eq, Matrix.isUnit_iff_isUnit_det]; simp [Matrix.det_fin_two]
  simpa using Matrix.rank_of_isUnit _ this

/-- PC-M2: the unit-step response of `3 e^{-2s} / (5 s + 1)`. -/
noncomputable def yStep (t : ℝ) : ℝ := if t ≤ 2 then 0 else 3 * (1 - exp (-(t - 2) / 5))

theorem fopdt_values : yStep 0 = 0 ∧ yStep 2 = 0 ∧ yStep 7 = 3 * (1 - exp (-1)) := by
  refine ⟨by norm_num [yStep], by norm_num [yStep], ?_⟩
  norm_num [yStep]

theorem fopdt_limit : Tendsto yStep atTop (𝓝 3) := by
  have hev : yStep =ᶠ[atTop] fun t => 3 * (1 - exp (-(t - 2) / 5)) := by
    filter_upwards [eventually_gt_atTop 2] with t ht
    simp [yStep, not_le.mpr ht]
  rw [tendsto_congr' hev]
  have h : Tendsto (fun t : ℝ => -(t - 2) / 5) atTop atBot := by
    have h1 : Tendsto (fun t : ℝ => t - 2) atTop atTop :=
      tendsto_atTop_add_const_right _ (-2) tendsto_id
    have h2 : Tendsto (fun t : ℝ => (t - 2) / 5) atTop atTop := h1.atTop_div_const (by norm_num)
    refine (tendsto_neg_atTop_atBot.comp h2).congr (fun t => ?_)
    simp only [Function.comp]; ring
  have := Real.tendsto_exp_atBot.comp h
  simpa using ((tendsto_const_nhds (x := (1 : ℝ))).sub this).const_mul 3

/-! ## 2. Signals -/

/-- SP-M1's signal. -/
noncomputable def xSig (t : ℝ) : ℝ := 5 * cos (2 * π * 300 * t) + 3 * sin (2 * π * 800 * t)

lemma sin_int_two_pi (n : ℤ) : sin (n * (2 * π)) = 0 := by
  rw [show (n : ℝ) * (2 * π) = (2 * n : ℤ) * π by push_cast; ring]
  exact sin_int_mul_pi _

/-- Sampled at 1000 Hz, `x` agrees at every sample with
`5 cos(2π·300 t) - 3 sin(2π·200 t)`: the 800 Hz component aliases to 200 Hz
with its sign reversed, and both survive a 500 Hz ideal low-pass. -/
theorem aliasing_at_samples (n : ℤ) :
    xSig (n / 1000) = 5 * cos (2 * π * 300 * (n / 1000)) - 3 * sin (2 * π * 200 * (n / 1000)) := by
  unfold xSig
  have : 2 * π * 800 * ((n : ℝ) / 1000) = (n : ℝ) * (2 * π) - 2 * π * 200 * (n / 1000) := by ring
  rw [this, sin_sub, sin_int_two_pi, cos_int_mul_two_pi]
  ring

/-- Linear convolution of finite sequences. -/
def linConv (x h : List ℤ) : List ℤ :=
  (List.range (x.length + h.length - 1)).map fun n =>
    ((List.range (n + 1)).map fun k => x.getD k 0 * h.getD (n - k) 0).sum

/-- `N`-point circular convolution. -/
def circConv (N : ℕ) (x h : List ℤ) : List ℤ :=
  (List.range N).map fun n =>
    ((List.range N).map fun k => x.getD k 0 * h.getD ((n + N - k) % N) 0).sum

/-- Time aliasing: fold a sequence modulo `N`. -/
def wrap (N : ℕ) (y : List ℤ) : List ℤ :=
  (List.range N).map fun n =>
    (((List.range y.length).filter (fun m => m % N = n)).map (fun m => y.getD m 0)).sum

/-- SP-H3: `y_L = [1, 1, 1, -3]` and `y_C = [-2, 1, 1]`. -/
theorem convolution_values :
    linConv [1, 2, 3] [1, -1] = [1, 1, 1, -3] ∧ circConv 3 [1, 2, 3] [1, -1] = [-2, 1, 1] := by
  decide

/-- The circular result is the linear one wrapped modulo 3. -/
theorem circular_is_wrapped_linear :
    circConv 3 [1, 2, 3] [1, -1] = wrap 3 (linConv [1, 2, 3] [1, -1]) := by decide

/-- With `N = 4 = len x + len h - 1` the two agree. -/
theorem circular_four_is_linear : circConv 4 [1, 2, 3] [1, -1] = linConv [1, 2, 3] [1, -1] := by
  decide

/-- SP-VH2: the bilinear map with `T = 1/2` sends `1/(s + 2)` to
`(1 + z⁻¹)/(6 - 2 z⁻¹)` (writing `w = z⁻¹`). -/
theorem bilinear_transfer (w : ℂ) (hw : 1 + w ≠ 0) (h6 : 6 - 2 * w ≠ 0) :
    1 / (4 * (1 - w) / (1 + w) + 2) = (1 + w) / (6 - 2 * w) := by
  have : 4 * (1 - w) / (1 + w) + 2 = (6 - 2 * w) / (1 + w) := by field_simp; ring
  rw [this]; field_simp

/-- The image of `s = jΩ` under the bilinear map with `T = 1/2`. -/
noncomputable def zOf (Ω : ℝ) : ℂ := (4 + Ω * Complex.I) / (4 - Ω * Complex.I)

lemma zOf_den_ne (Ω : ℝ) : (4 - Ω * Complex.I) ≠ 0 := by
  intro hh; have := congrArg Complex.re hh; norm_num at this

/-- The imaginary axis lands on the unit circle. -/
theorem bilinear_unit_circle (Ω : ℝ) : ‖zOf Ω‖ = 1 := by
  unfold zOf
  rw [norm_div, div_eq_one_iff_eq (by simpa using zOf_den_ne Ω)]
  have : (4 - Ω * Complex.I) = (starRingEnd ℂ) (4 + Ω * Complex.I) := by
    apply Complex.ext <;> simp
  rw [this, Complex.norm_conj]

/-- `Ω → ∞` maps to `z = -1` (`ω = π`). -/
theorem bilinear_infinity : Tendsto zOf atTop (𝓝 (-1)) := by
  have h : zOf = fun Ω : ℝ => -1 + 8 / (4 - Ω * Complex.I) := by
    funext Ω; unfold zOf
    have := zOf_den_ne Ω
    field_simp; ring
  rw [h]
  conv => rhs; rw [show (-1 : ℂ) = -1 + 0 by ring]
  apply tendsto_const_nhds.add
  rw [tendsto_zero_iff_norm_tendsto_zero]
  have hb : ∀ Ω : ℝ, 0 < Ω → ‖8 / (4 - Ω * Complex.I)‖ ≤ 8 / Ω := by
    intro Ω hΩ
    rw [norm_div]
    have : Ω ≤ ‖4 - Ω * Complex.I‖ := by
      have := Complex.abs_im_le_norm (4 - Ω * Complex.I)
      simp at this; rw [abs_of_pos hΩ] at this; exact this
    simp only [Complex.norm_ofNat]
    exact div_le_div_of_nonneg_left (by norm_num) hΩ this
  apply squeeze_zero' (Eventually.of_forall fun _ => norm_nonneg _)
  · filter_upwards [eventually_gt_atTop 0] with Ω hΩ using hb Ω hΩ
  · simpa using (tendsto_const_nhds (x := (8 : ℝ))).div_atTop tendsto_id

/-- SP-M2, the causal half `(1/2)ⁿ u[n]`: its z-transform converges exactly
for `|z| > 1/2`. -/
theorem ztransform_causal_roc (z : ℂ) (hz : z ≠ 0) :
    Summable (fun n : ℕ => (1 / 2 : ℂ) ^ n * z⁻¹ ^ n) ↔ 1 / 2 < ‖z‖ := by
  have e : (fun n : ℕ => (1 / 2 : ℂ) ^ n * z⁻¹ ^ n) = fun n => ((2 * z)⁻¹) ^ n := by
    funext n; rw [← mul_pow]; congr 1; field_simp
  have hz' : 0 < ‖z‖ := norm_pos_iff.mpr hz
  rw [e, summable_geometric_iff_norm_lt_one, norm_inv, norm_mul]
  simp only [Complex.norm_ofNat]
  rw [inv_lt_one₀ (by positivity)]
  constructor <;> intro h <;> linarith

/-- The anticausal half `-(-3)ⁿ u[-n-1]` (terms `n = -(m+1)`): converges
exactly for `|z| < 3`. -/
theorem ztransform_anticausal_roc (z : ℂ) :
    Summable (fun m : ℕ => (-3 : ℂ)⁻¹ ^ (m + 1) * z ^ (m + 1)) ↔ ‖z‖ < 3 := by
  have e : (fun m : ℕ => (-3 : ℂ)⁻¹ ^ (m + 1) * z ^ (m + 1)) = fun m => (-z / 3) * (-z / 3) ^ m := by
    funext m; rw [← mul_pow, pow_succ]; ring_nf
  rw [e]
  constructor
  · intro h
    by_cases hz : z = 0
    · simp [hz]
    have h2 := h.mul_left (-z / 3)⁻¹
    have : (fun m => (-z / 3)⁻¹ * ((-z / 3) * (-z / 3) ^ m)) = fun m => (-z / 3) ^ m := by
      funext m; field_simp
    rw [this, summable_geometric_iff_norm_lt_one] at h2
    rw [norm_div, norm_neg] at h2; simp at h2; linarith
  · intro h
    apply Summable.mul_left
    rw [summable_geometric_iff_norm_lt_one, norm_div, norm_neg]; simp
    linarith

/-- So the ROC is `1/2 < |z| < 3`, which contains the unit circle (the DTFT
exists), and there `X(z) = 1/(1 - ½ z⁻¹) + 1/(1 + 3 z⁻¹)`. -/
theorem ztransform_value (z : ℂ) (h1 : 1 / 2 < ‖z‖) (h2 : ‖z‖ < 3) :
    (∑' n : ℕ, (1 / 2 : ℂ) ^ n * z⁻¹ ^ n) - (∑' m : ℕ, (-3 : ℂ)⁻¹ ^ (m + 1) * z ^ (m + 1))
      = 1 / (1 - (1 / 2) * z⁻¹) + 1 / (1 + 3 * z⁻¹) := by
  have hz : z ≠ 0 := by rintro rfl; simp at h1; linarith
  have hzp : 0 < ‖z‖ := norm_pos_iff.mpr hz
  have e1 : (fun n : ℕ => (1 / 2 : ℂ) ^ n * z⁻¹ ^ n) = fun n => ((2 * z)⁻¹) ^ n := by
    funext n; rw [← mul_pow]; congr 1; field_simp
  have e2 : (fun m : ℕ => (-3 : ℂ)⁻¹ ^ (m + 1) * z ^ (m + 1)) = fun m => (-z / 3) * (-z / 3) ^ m := by
    funext m; rw [← mul_pow, pow_succ]; ring_nf
  have n1 : ‖(2 * z)⁻¹‖ < 1 := by
    rw [norm_inv, norm_mul]; simp only [Complex.norm_ofNat]
    rw [inv_lt_one₀ (by positivity)]; linarith
  have n2 : ‖-z / 3‖ < 1 := by rw [norm_div, norm_neg]; simp; linarith
  rw [e1, e2, tsum_geometric_of_norm_lt_one n1, tsum_mul_left, tsum_geometric_of_norm_lt_one n2]
  have a3 : (2 : ℂ) * z - 1 ≠ 0 := by
    intro h
    have h2z : (2 : ℂ) * z = 1 := by linear_combination h
    rw [h2z, inv_one] at n1; simp at n1
  have a4 : (z : ℂ) + 3 ≠ 0 := by
    intro h; rw [show -z / 3 = 1 by linear_combination -h / 3] at n2; simp at n2
  have b1 : (1 - (2 * z)⁻¹)⁻¹ = 2 * z / (2 * z - 1) := by
    rw [inv_eq_one_div, div_eq_div_iff _ a3]
    · field_simp
    intro h; apply a3; field_simp at h; linear_combination h
  have b2 : -z / 3 * (1 - -z / 3)⁻¹ = - (z / (z + 3)) := by
    have : (1 - -z / 3 : ℂ) = (z + 3) / 3 := by ring
    rw [this]; field_simp
  have b3 : 1 / (1 - (1 / 2) * z⁻¹) = 2 * z / (2 * z - 1) := by
    have : (1 - (1 / 2) * z⁻¹ : ℂ) = (2 * z - 1) / (2 * z) := by field_simp
    rw [this]; field_simp
  have b4 : 1 / (1 + 3 * z⁻¹) = z / (z + 3) := by
    have : (1 + 3 * z⁻¹ : ℂ) = (z + 3) / z := by field_simp
    rw [this]; field_simp
  rw [b1, b2, b3, b4]; ring

/-- SP-VH1: with the taps `h₀ = 86/161`, `h₁ = 40/161`
(`GLM.QuestionSetB.wiener_taps`), the minimum mean-square error
`R_ss[0] - h₀ R_ss[0] - h₁ R_ss[1]` is `43/161`. -/
theorem wiener_mse : (1 : ℚ) - 86 / 161 * 1 - 40 / 161 * (4 / 5) = 43 / 161 := by norm_num

/-! ## 3. Physics -/

/-- Ph-M2: in the first excited state (`n = 2`) of a well of width `L`, the
probability of `0 ≤ x ≤ L/4` is exactly `1/4`. -/
theorem well_probability (L : ℝ) (hL : 0 < L) :
    ∫ x in (0 : ℝ)..L / 4, (2 / L) * sin (2 * π * x / L) ^ 2 = 1 / 4 := by
  have hc : (2 * π / L) ≠ 0 := by positivity
  have h1 : (fun x => (2 / L) * sin (2 * π * x / L) ^ 2)
      = fun x => (2 / L) * sin ((2 * π / L) * x) ^ 2 := by
    funext x; ring_nf
  rw [h1, intervalIntegral.integral_const_mul,
    intervalIntegral.integral_comp_mul_left (fun x => sin x ^ 2) hc, integral_sin_sq]
  have : 2 * π / L * (L / 4) = π / 2 := by field_simp; ring
  rw [this]; simp [sin_pi_div_two, cos_pi_div_two]
  field_simp; ring

/-- The same wavefunction is normalised over the whole well. -/
theorem well_normalised (L : ℝ) (hL : 0 < L) :
    ∫ x in (0 : ℝ)..L, (2 / L) * sin (2 * π * x / L) ^ 2 = 1 := by
  have hc : (2 * π / L) ≠ 0 := by positivity
  have h1 : (fun x => (2 / L) * sin (2 * π * x / L) ^ 2)
      = fun x => (2 / L) * sin ((2 * π / L) * x) ^ 2 := by
    funext x; ring_nf
  rw [h1, intervalIntegral.integral_const_mul,
    intervalIntegral.integral_comp_mul_left (fun x => sin x ^ 2) hc, integral_sin_sq]
  have : 2 * π / L * L = 2 * π := by field_simp
  rw [this]
  simp [sin_two_pi]
  field_simp

/-! ## 4. Information -/

/-- Shannon entropy in bits of a list of probabilities (`0 · log 0 = 0`
because `logb 2 0 = 0`). -/
noncomputable def H (ps : List ℝ) : ℝ := -(ps.map fun p => p * logb 2 p).sum

lemma lb_two_pow (n : ℕ) : logb 2 (2 ^ n) = n := by
  rw [logb_pow, logb_self_eq_one (by norm_num)]; ring
lemma lb_half : logb 2 (1 / 2) = -1 := by
  rw [one_div, logb_inv, logb_self_eq_one (by norm_num)]
lemma lb_quarter : logb 2 (1 / 4) = -2 := by
  rw [one_div, logb_inv, show (4 : ℝ) = 2 ^ 2 by norm_num, lb_two_pow]; norm_num
lemma lb_3q : logb 2 (3 / 4) = logb 2 3 - 2 := by
  rw [logb_div (by norm_num) (by norm_num), show (4 : ℝ) = 2 ^ 2 by norm_num, lb_two_pow]; norm_num

/-- IT-M1: `H(X,Y) = 3/2`, `H(X) = H(Y) = 2 - (3/4) log₂ 3`, and
`H(Y|X) = H(X,Y) - H(X) = (3/4) log₂ 3 - 1/2`. -/
theorem joint_entropy_values :
    H [1 / 2, 1 / 4, 1 / 4, 0] = 3 / 2 ∧ H [3 / 4, 1 / 4] = 2 - 3 / 4 * logb 2 3 ∧
      H [1 / 2, 1 / 4, 1 / 4, 0] - H [3 / 4, 1 / 4] = 3 / 4 * logb 2 3 - 1 / 2 := by
  have hj : H [1 / 2, 1 / 4, 1 / 4, 0] = 3 / 2 := by
    simp only [H, List.map, List.sum_cons, List.sum_nil, lb_half, lb_quarter, logb_zero]
    norm_num
  have hm : H [3 / 4, 1 / 4] = 2 - 3 / 4 * logb 2 3 := by
    simp only [H, List.map, List.sum_cons, List.sum_nil, lb_3q, lb_quarter]
    ring
  refine ⟨hj, hm, ?_⟩
  rw [hj, hm]; ring

/-- `I(X;Y) = H(X) + H(Y) - H(X,Y) = 5/2 - (3/2) log₂ 3`. -/
theorem mutual_information_value :
    H [3 / 4, 1 / 4] + H [3 / 4, 1 / 4] - H [1 / 2, 1 / 4, 1 / 4, 0] = 5 / 2 - 3 / 2 * logb 2 3 := by
  obtain ⟨hj, hm, -⟩ := joint_entropy_values
  rw [hj, hm]; ring

/-- IT-M2's Huffman code `A = 0, B = 10, C = 110, D = 111`. -/
def huffmanCode : List (List Bool) := [[false], [true, false], [true, true, false], [true, true, true]]

/-- It is prefix-free. -/
theorem huffman_prefix_free : ∀ c ∈ huffmanCode, ∀ d ∈ huffmanCode, c ≠ d → ¬ c <+: d := by
  decide

/-- Its lengths meet Kraft's inequality with equality (the code is complete). -/
theorem huffman_kraft : (1 / 2 : ℚ) ^ 1 + (1 / 2) ^ 2 + (1 / 2) ^ 3 + (1 / 2) ^ 3 = 1 := by norm_num

/-- `L = 7/4` bits per symbol. -/
theorem huffman_length : (1 / 2 : ℚ) * 1 + 1 / 4 * 2 + 15 / 100 * 3 + 10 / 100 * 3 = 7 / 4 := by
  norm_num

lemma huffman_bounded : ∀ a ∈ Finset.range 4, ∀ b ∈ Finset.range 5, ∀ c ∈ Finset.range 7,
    ∀ d ∈ Finset.range 9, 1 ≤ a → 1 ≤ b → 1 ≤ c → 1 ≤ d →
    2 ^ (8 - a) + 2 ^ (8 - b) + 2 ^ (8 - c) + 2 ^ (8 - d) ≤ 256 →
    175 ≤ 50 * a + 25 * b + 15 * c + 10 * d := by
  decide

lemma half_pow_eq (n : ℕ) (hn : n ≤ 8) : (1 / 2 : ℚ) ^ n = (2 ^ (8 - n) : ℕ) / 256 := by
  have : (256 : ℚ) = 2 ^ (8 - n) * 2 ^ n := by
    rw [← pow_add, Nat.sub_add_cancel hn]; norm_num
  rw [this]; push_cast; field_simp; rw [← mul_pow]; norm_num

/-- No assignment of codeword lengths satisfying Kraft's inequality (as the
lengths of every prefix code do) has average length below `7/4`: the Huffman
code is optimal. -/
theorem huffman_optimal (a b c d : ℕ) (ha : 1 ≤ a) (hb : 1 ≤ b) (hc : 1 ≤ c) (hd : 1 ≤ d)
    (kraft : (1 / 2 : ℚ) ^ a + (1 / 2) ^ b + (1 / 2) ^ c + (1 / 2) ^ d ≤ 1) :
    (7 / 4 : ℚ) ≤ 1 / 2 * a + 1 / 4 * b + 15 / 100 * c + 10 / 100 * d := by
  have ha' : (1 : ℚ) ≤ a := by exact_mod_cast ha
  have hb' : (1 : ℚ) ≤ b := by exact_mod_cast hb
  have hc' : (1 : ℚ) ≤ c := by exact_mod_cast hc
  have hd' : (1 : ℚ) ≤ d := by exact_mod_cast hd
  by_cases h : a < 4 ∧ b < 5 ∧ c < 7 ∧ d < 9
  · obtain ⟨h1, h2, h3, h4⟩ := h
    rw [half_pow_eq a (by omega), half_pow_eq b (by omega), half_pow_eq c (by omega),
      half_pow_eq d (by omega)] at kraft
    have k2 : 2 ^ (8 - a) + 2 ^ (8 - b) + 2 ^ (8 - c) + 2 ^ (8 - d) ≤ 256 := by
      have : ((2 ^ (8 - a) + 2 ^ (8 - b) + 2 ^ (8 - c) + 2 ^ (8 - d) : ℕ) : ℚ) ≤ 256 := by
        push_cast at kraft ⊢; linarith
      exact_mod_cast this
    have := huffman_bounded a (Finset.mem_range.2 h1) b (Finset.mem_range.2 h2) c
      (Finset.mem_range.2 h3) d (Finset.mem_range.2 h4) ha hb hc hd k2
    have : (175 : ℚ) ≤ 50 * a + 25 * b + 15 * c + 10 * d := by exact_mod_cast this
    linarith
  · rcases not_and_or.mp h with h | h
    · have : (4 : ℚ) ≤ a := by exact_mod_cast (not_lt.mp h)
      linarith
    rcases not_and_or.mp h with h | h
    · have : (5 : ℚ) ≤ b := by exact_mod_cast (not_lt.mp h)
      linarith
    rcases not_and_or.mp h with h | h
    · have : (7 : ℚ) ≤ c := by exact_mod_cast (not_lt.mp h)
      linarith
    · have : (9 : ℚ) ≤ d := by exact_mod_cast (not_lt.mp h)
      linarith

/-- The source entropy `H(X) = 7/5 - (3/20) log₂ 3 + (1/4) log₂ 5`. -/
theorem huffman_entropy :
    H [1 / 2, 1 / 4, 15 / 100, 10 / 100] = 7 / 5 - 3 / 20 * logb 2 3 + 1 / 4 * logb 2 5 := by
  have e1 : logb 2 (15 / 100) = logb 2 3 - 2 - logb 2 5 := by
    rw [show (15 / 100 : ℝ) = 3 / (2 ^ 2 * 5) by norm_num, logb_div (by norm_num) (by norm_num),
      logb_mul (by norm_num) (by norm_num), lb_two_pow]; norm_num; ring
  have e2 : logb 2 (10 / 100) = -1 - logb 2 5 := by
    rw [show (10 / 100 : ℝ) = 1 / (2 * 5) by norm_num, logb_div (by norm_num) (by norm_num),
      logb_mul (by norm_num) (by norm_num), logb_self_eq_one (by norm_num)]; simp; ring
  simp only [H, List.map, List.sum_cons, List.sum_nil, lb_half, lb_quarter, e1, e2]
  ring

/-- The mutual information of a BSC with crossover `p` and input
`P(X = 1) = q`, in nats: `H(Y) - H(Y|X) = h(q(1-p) + (1-q)p) - h(p)`. -/
noncomputable def bscInfo (p q : ℝ) : ℝ := binEntropy (q * (1 - p) + (1 - q) * p) - binEntropy p

/-- No input distribution does better than `log 2 - h(p)` ... -/
theorem bsc_info_le (p q : ℝ) : bscInfo p q ≤ log 2 - binEntropy p := by
  unfold bscInfo; linarith [binEntropy_le_log_two (p := q * (1 - p) + (1 - q) * p)]

/-- ... and the uniform input achieves it: the capacity, and its achieving
distribution. -/
theorem bsc_info_uniform (p : ℝ) : bscInfo p (1 / 2) = log 2 - binEntropy p := by
  unfold bscInfo
  have : (1 / 2 : ℝ) * (1 - p) + (1 - 1 / 2) * p = 2⁻¹ := by ring
  rw [this, binEntropy_two_inv]

/-- The capacity of a BSC in bits per use. -/
noncomputable def bscCapacityBits (p : ℝ) : ℝ := (log 2 - binEntropy p) / log 2

/-- IT-H1: at `p = 0.11`,
`C = -1 - 2 log₂ 5 + (11/100) log₂ 11 + (89/100) log₂ 89` (≈ 0.500084). -/
theorem bsc_capacity_value :
    bscCapacityBits (11 / 100) = -1 - 2 * logb 2 5 + 11 / 100 * logb 2 11 + 89 / 100 * logb 2 89 := by
  rw [bscCapacityBits, binEntropy_eq_negMulLog_add_negMulLog_one_sub]
  simp only [negMulLog_def]
  have h2 : log 2 ≠ 0 := by positivity
  simp only [logb]
  rw [show (1 - 11 / 100 : ℝ) = 89 / 100 by norm_num,
    log_div (by norm_num) (by norm_num), log_div (by norm_num) (by norm_num),
    show (100 : ℝ) = 2 ^ 2 * 5 ^ 2 by norm_num, log_mul (by norm_num) (by norm_num), log_pow, log_pow]
  field_simp
  ring

/-- IT-VH1: the identity steps are a BSC with `p = 0` (1 bit), the noisy steps a
BSC with `p = 1/2` (0 bits); alternating, the average is `1/2` bit per use. -/
theorem memory_channel_average :
    bscCapacityBits 0 = 1 ∧ bscCapacityBits (1 / 2) = 0 ∧
      (bscCapacityBits 0 + bscCapacityBits (1 / 2)) / 2 = 1 / 2 := by
  have h2 : log 2 ≠ 0 := by positivity
  have z : bscCapacityBits 0 = 1 := by unfold bscCapacityBits; simp [h2]
  have o : bscCapacityBits (1 / 2) = 0 := by
    unfold bscCapacityBits; rw [show (1 / 2 : ℝ) = 2⁻¹ by norm_num, binEntropy_two_inv]; simp
  exact ⟨z, o, by rw [z, o]; norm_num⟩

/-- Water-filling: the power a channel of noise `σ²` gets at water level `ν`. -/
noncomputable def alloc (nu s : ℝ) : ℝ := max 0 (nu - s)

/-- IT-VH2: with noises `1, 3, 7` W and 10 W in total, the water level is
`ν = 7` and no other level spends exactly the budget. -/
theorem waterfill_level_unique (nu : ℝ) : alloc nu 1 + alloc nu 3 + alloc nu 7 = 10 ↔ nu = 7 := by
  unfold alloc
  constructor
  · intro h
    rcases le_total nu 3 with h3 | h3
    · have : max 0 (nu - 3) = 0 := max_eq_left (by linarith)
      have : max 0 (nu - 7) = 0 := max_eq_left (by linarith)
      have : max 0 (nu - 1) ≤ 2 := max_le (by norm_num) (by linarith)
      linarith
    rcases le_total nu 7 with h7 | h7
    · rw [max_eq_right (by linarith : (0 : ℝ) ≤ nu - 1), max_eq_right (by linarith : (0 : ℝ) ≤ nu - 3),
        max_eq_left (by linarith : nu - 7 ≤ 0)] at h; linarith
    · rw [max_eq_right (by linarith : (0 : ℝ) ≤ nu - 1), max_eq_right (by linarith : (0 : ℝ) ≤ nu - 3),
        max_eq_right (by linarith : (0 : ℝ) ≤ nu - 7)] at h; linarith
  · rintro rfl; norm_num [max_def]

/-- The allocation `P = (6, 4, 0)` W. -/
theorem waterfill_allocation : alloc 7 1 = 6 ∧ alloc 7 3 = 4 ∧ alloc 7 7 = 0 := by
  norm_num [alloc]

lemma log_tangent (y y0 : ℝ) (hy : 0 < y) (hy0 : 0 < y0) : log y ≤ log y0 + (y - y0) / y0 := by
  have := log_le_sub_one_of_pos (div_pos hy hy0)
  rw [log_div hy.ne' hy0.ne'] at this
  have : (y - y0) / y0 = y / y0 - 1 := by field_simp
  linarith

/-- The allocation is optimal: no split of the 10 W does better (in bits per
use, `Σ ½ log₂(1 + P_i/σ_i²)`). -/
theorem waterfill_optimal (P1 P2 P3 : ℝ) (h1 : 0 ≤ P1) (h2 : 0 ≤ P2) (h3 : 0 ≤ P3)
    (hs : P1 + P2 + P3 = 10) :
    1 / 2 * logb 2 (1 + P1 / 1) + 1 / 2 * logb 2 (1 + P2 / 3) + 1 / 2 * logb 2 (1 + P3 / 7)
      ≤ 1 / 2 * logb 2 (1 + 6 / 1) + 1 / 2 * logb 2 (1 + 4 / 3) + 1 / 2 * logb 2 (1 + 0 / 7) := by
  have t1 := log_tangent (1 + P1 / 1) (1 + 6 / 1) (by positivity) (by norm_num)
  have t2 := log_tangent (1 + P2 / 3) (1 + 4 / 3) (by positivity) (by norm_num)
  have t3 := log_tangent (1 + P3 / 7) (1 + 0 / 7) (by positivity) (by norm_num)
  have e : (1 + P1 / 1 - (1 + 6 / 1)) / (1 + 6 / 1) + (1 + P2 / 3 - (1 + 4 / 3)) / (1 + 4 / 3)
      + (1 + P3 / 7 - (1 + 0 / 7)) / (1 + 0 / 7) = (P1 + P2 + P3 - 10) / 7 := by ring
  rw [hs] at e
  have key : log (1 + P1 / 1) + log (1 + P2 / 3) + log (1 + P3 / 7)
      ≤ log (1 + 6 / 1) + log (1 + 4 / 3) + log (1 + 0 / 7) := by linarith
  have hl : 0 < log 2 := by positivity
  simp only [logb]
  rw [← sub_nonneg]
  have : 1 / 2 * (log (1 + 6 / 1) / log 2) + 1 / 2 * (log (1 + 4 / 3) / log 2)
      + 1 / 2 * (log (1 + 0 / 7) / log 2)
      - (1 / 2 * (log (1 + P1 / 1) / log 2) + 1 / 2 * (log (1 + P2 / 3) / log 2)
      + 1 / 2 * (log (1 + P3 / 7) / log 2))
      = (log (1 + 6 / 1) + log (1 + 4 / 3) + log (1 + 0 / 7)
        - (log (1 + P1 / 1) + log (1 + P2 / 3) + log (1 + P3 / 7))) / (2 * log 2) := by
    field_simp
  rw [this]
  apply div_nonneg (by linarith) (by positivity)

/-- The maximum capacity `C = log₂ 7 - ½ log₂ 3` (≈ 2.014873) bits per use. -/
theorem waterfill_capacity :
    1 / 2 * logb 2 (1 + 6 / 1) + 1 / 2 * logb 2 (1 + 4 / 3) + 1 / 2 * logb 2 (1 + 0 / 7)
      = logb 2 7 - 1 / 2 * logb 2 3 := by
  have : (1 + 4 / 3 : ℝ) = 7 / 3 := by norm_num
  rw [this, logb_div (by norm_num) (by norm_num)]; norm_num; ring

end GLM.QuestionSetBAnswers
