module

public import Mathlib

/-!
# Robin conditions at both ends, and roots bounded in closed form (Phase 119)

`studies/DERIVATION_FOUR_STUDY.md` takes the Robin limits the third derivation
study left (`DERIVATION_THREE_STUDY.md` §6): Robin conditions at both ends,
and decimals when the interval length is symbolic.

* **Robin at both ends** (`robin_both_root_exists`, `robin_both_eigenfunction`):
  for `y'' + k² y = 0`, `y'(0) = a y(0)`, `y'(L) + b y(L) = 0` with
  `a, b, L > 0`, the characteristic equation
  `(ab - k²) sin(kL) + k(a + b) cos(kL) = 0` has a root in every interval
  `(nπ/L, (n+1)π/L)`, `n ≥ 0`, and at a root `y = k cos(kx) + a sin(kx)` solves
  the problem (and is not zero: `y(0) = k`).
* **A closed-form enclosure for a symbolic length** (`robin_root_bounds`): for
  `y(0) = 0`, `y'(L) + h y(L) = 0` with `h, L > 0`, the root `k_n` in
  `((n - 1/2)π/L, nπ/L)` satisfies
  `(n - 1/2)π + arctan(hL/(nπ)) < k_n L < (n - 1/2)π + arctan(hL/((n - 1/2)π))`,
  because `k_n L - (n - 1/2)π = arctan(h/k_n)` exactly (`robin_root_arctan`).
-/

@[expose] public section

namespace GLM.RobinBoth

open Real

/-- The characteristic function for Robin conditions at both ends. -/
noncomputable def charBoth (a b L k : ℝ) : ℝ :=
  (a * b - k ^ 2) * Real.sin (k * L) + k * (a + b) * Real.cos (k * L)

lemma charBoth_nat_mul_pi {a b L : ℝ} (hL : 0 < L) (m : ℕ) :
    charBoth a b L (m * π / L) = (m * π / L) * (a + b) * (-1) ^ m := by
  have e : m * π / L * L = m * π := by field_simp
  simp only [charBoth, e, Real.sin_nat_mul_pi, Real.cos_nat_mul_pi]
  ring

/-- **Robin at both ends: a root in every interval** `(nπ/L, (n+1)π/L)`. -/
theorem robin_both_root_exists {a b L : ℝ} (ha : 0 < a) (hb : 0 < b) (hL : 0 < L)
    (n : ℕ) :
    ∃ k, n * π / L < k ∧ k < (n + 1) * π / L ∧ charBoth a b L k = 0 := by
  set G : ℝ → ℝ := fun k => (-1) ^ (n + 1) * charBoth a b L k with hG
  have hc : Continuous G := by
    simp only [hG, charBoth]; fun_prop
  have hpow : ((-1 : ℝ) ^ (n + 1)) * (-1) ^ (n + 1) = 1 := by rw [← mul_pow]; simp
  have hi : G ((n + 1) * π / L) = (n + 1) * π / L * (a + b) := by
    have := charBoth_nat_mul_pi (a := a) (b := b) hL (n + 1)
    push_cast at this
    simp only [hG, this]
    linear_combination ((n + 1) * π / L * (a + b)) * hpow
  have hipos : 0 < (n + 1) * π / L * (a + b) := by positivity
  -- a point just above `nπ/L` where `G < 0`
  obtain ⟨lo, hlo1, hlo2, hGlo⟩ : ∃ lo, n * π / L ≤ lo ∧ lo < (n + 1) * π / L ∧ G lo < 0 := by
    rcases Nat.eq_zero_or_pos n with h0 | hn
    · subst h0
      set e := min (Real.sqrt (a * b)) (π / (2 * L)) / 2 with he
      have hsq : 0 < Real.sqrt (a * b) := Real.sqrt_pos.2 (mul_pos ha hb)
      have hpi2 : 0 < π / (2 * L) := by positivity
      have epos : 0 < e := by positivity
      have e1 : e ≤ Real.sqrt (a * b) / 2 := by
        rw [he]; exact div_le_div_of_nonneg_right (min_le_left _ _) (by norm_num)
      have e2 : e ≤ π / (2 * L) / 2 := by
        rw [he]; exact div_le_div_of_nonneg_right (min_le_right _ _) (by norm_num)
      have eL : e * L < π / 2 := by
        have : e * L ≤ π / (2 * L) / 2 * L := mul_le_mul_of_nonneg_right e2 hL.le
        have h' : π / (2 * L) / 2 * L = π / 4 := by field_simp; ring
        linarith [pi_pos]
      have eLpos : 0 < e * L := mul_pos epos hL
      have hsin : 0 < Real.sin (e * L) :=
        Real.sin_pos_of_pos_of_lt_pi eLpos (by linarith [pi_pos])
      have hcos : 0 < Real.cos (e * L) :=
        Real.cos_pos_of_mem_Ioo ⟨by linarith [pi_pos], eL⟩
      have hab : e ^ 2 < a * b := by
        have h1 : e ^ 2 ≤ (Real.sqrt (a * b) / 2) ^ 2 := pow_le_pow_left₀ epos.le e1 2
        have h2 : (Real.sqrt (a * b) / 2) ^ 2 = a * b / 4 := by
          rw [div_pow, Real.sq_sqrt (mul_pos ha hb).le]; ring
        nlinarith [mul_pos ha hb]
      refine ⟨e, by simp [epos.le], ?_, ?_⟩
      · have : e < π / (2 * L) := by linarith
        have h3 : π / (2 * L) < (0 + 1) * π / L := by
          rw [zero_add, one_mul]
          exact div_lt_div_of_pos_left pi_pos hL (by linarith)
        push_cast
        linarith
      · simp only [hG, charBoth, zero_add, pow_one]
        have : 0 < (a * b - e ^ 2) * Real.sin (e * L) + e * (a + b) * Real.cos (e * L) := by
          have := mul_pos (sub_pos.2 hab) hsin
          have := mul_pos (mul_pos epos (add_pos ha hb)) hcos
          linarith
        linarith
    · refine ⟨n * π / L, le_rfl, ?_, ?_⟩
      · apply div_lt_div_of_pos_right _ hL; nlinarith [pi_pos]
      · have := charBoth_nat_mul_pi (a := a) (b := b) hL n
        simp only [hG, this, pow_succ]
        have hp : ((-1 : ℝ) ^ n) * (-1) ^ n = 1 := by rw [← mul_pow]; simp
        have hnpos : 0 < (n : ℝ) * π / L * (a + b) := by
          have : (0 : ℝ) < n := by exact_mod_cast hn
          positivity
        nlinarith
  have h0 : (0 : ℝ) ∈ Set.Ioo (G lo) (G ((n + 1) * π / L)) := ⟨hGlo, by rw [hi]; exact hipos⟩
  obtain ⟨k, hk, hGk⟩ := intermediate_value_Ioo hlo2.le hc.continuousOn h0
  refine ⟨k, lt_of_le_of_lt hlo1 hk.1, hk.2, ?_⟩
  have : (-1 : ℝ) ^ (n + 1) ≠ 0 := by simp
  exact (mul_eq_zero.mp hGk).resolve_left this

/-- **The eigenfunction for Robin at both ends**: at a root `k`,
`y = k cos(kx) + a sin(kx)` solves `y'' + k² y = 0`, `y'(0) = a y(0)` and
`y'(L) + b y(L) = 0`, and `y(0) = k`. -/
theorem robin_both_eigenfunction {a b L k : ℝ} (hk : charBoth a b L k = 0) :
    (∀ x, deriv (deriv fun t => k * Real.cos (k * t) + a * Real.sin (k * t)) x +
        k ^ 2 * (k * Real.cos (k * x) + a * Real.sin (k * x)) = 0) ∧
      deriv (fun t => k * Real.cos (k * t) + a * Real.sin (k * t)) 0 =
        a * (k * Real.cos (k * 0) + a * Real.sin (k * 0)) ∧
      deriv (fun t => k * Real.cos (k * t) + a * Real.sin (k * t)) L +
        b * (k * Real.cos (k * L) + a * Real.sin (k * L)) = 0 ∧
      k * Real.cos (k * 0) + a * Real.sin (k * 0) = k := by
  have d1 : deriv (fun t => k * Real.cos (k * t) + a * Real.sin (k * t)) =
      fun t => -(k ^ 2 * Real.sin (k * t)) + a * k * Real.cos (k * t) := by
    funext t
    have h1 := (((hasDerivAt_id t).const_mul k).cos).const_mul k
    have h2 := (((hasDerivAt_id t).const_mul k).sin).const_mul a
    have h : HasDerivAt (fun t => k * Real.cos (k * t) + a * Real.sin (k * t))
        (-(k ^ 2 * Real.sin (k * t)) + a * k * Real.cos (k * t)) t := by
      convert h1.add h2 using 1
      simp only [id]; ring
    exact h.deriv
  have d2 : deriv (fun t => -(k ^ 2 * Real.sin (k * t)) + a * k * Real.cos (k * t)) =
      fun t => -(k ^ 3 * Real.cos (k * t)) - a * k ^ 2 * Real.sin (k * t) := by
    funext t
    have h1 := ((((hasDerivAt_id t).const_mul k).sin).const_mul (k ^ 2)).neg
    have h2 := (((hasDerivAt_id t).const_mul k).cos).const_mul (a * k)
    have h : HasDerivAt (fun t => -(k ^ 2 * Real.sin (k * t)) + a * k * Real.cos (k * t))
        (-(k ^ 3 * Real.cos (k * t)) - a * k ^ 2 * Real.sin (k * t)) t := by
      convert h1.add h2 using 1
      simp only [id]; ring
    exact h.deriv
  refine ⟨fun x => ?_, ?_, ?_, by simp⟩
  · rw [d1, d2]; ring
  · rw [d1]; simp
  · rw [d1]
    unfold charBoth at hk
    linear_combination hk

/-- **The exact offset of a Dirichlet–Robin root**: if `z = kL` is a root of
`z cos z + c sin z = 0` (`c = hL`, any sign) in `((n - 1/2)π, nπ)`, `n ≥ 1`, then
`z - (n - 1/2)π = arctan(c / z)`. -/
theorem robin_root_arctan {c z : ℝ} (n : ℕ) (hn : 1 ≤ n)
    (h1 : (n - 1 / 2) * π < z) (h2 : z < n * π)
    (hz : z * Real.cos z + c * Real.sin z = 0) :
    z - (n - 1 / 2) * π = Real.arctan (c / z) := by
  set d := z - (n - 1 / 2) * π with hd
  have dpos : 0 < d := by rw [hd]; linarith
  have dlt : d < π / 2 := by rw [hd]; linarith
  have zpos : 0 < z := by
    have hn' : (1 : ℝ) ≤ n := by exact_mod_cast hn
    nlinarith [pi_pos]
  have ez : z = d + n * π - π / 2 := by rw [hd]; ring
  have hcosz : Real.cos z = (-1) ^ n * Real.sin d := by
    rw [ez, Real.cos_sub_pi_div_two, Real.sin_add_nat_mul_pi]
  have hsinz : Real.sin z = -((-1) ^ n * Real.cos d) := by
    rw [ez, Real.sin_sub_pi_div_two, Real.cos_add_nat_mul_pi]
  rw [hcosz, hsinz] at hz
  have hpow : ((-1 : ℝ) ^ n) ^ 2 = 1 := by rw [← pow_mul, mul_comm, pow_mul]; simp
  have key : z * Real.sin d = c * Real.cos d := by
    have := congrArg (fun t => (-1 : ℝ) ^ n * t) hz
    simp only [mul_zero] at this
    linear_combination this - (z * Real.sin d - c * Real.cos d) * hpow
  have hcos : 0 < Real.cos d := Real.cos_pos_of_mem_Ioo ⟨by linarith, dlt⟩
  have htan : Real.tan d = c / z := by
    rw [Real.tan_eq_sin_div_cos, div_eq_div_iff hcos.ne' zpos.ne']
    linarith [key]
  rw [← htan, Real.arctan_tan (by linarith) dlt]

/-- **A closed-form enclosure of a Dirichlet–Robin root on a symbolic
interval**: for `h, L > 0` and a root `k` of `k cos(kL) + h sin(kL) = 0` in
`((n - 1/2)π/L, nπ/L)`,
`(n - 1/2)π + arctan(hL/(nπ)) < kL < (n - 1/2)π + arctan(hL/((n - 1/2)π))`. -/
theorem robin_root_bounds {h L k : ℝ} (hh : 0 < h) (hL : 0 < L) (n : ℕ) (hn : 1 ≤ n)
    (h1 : (n - 1 / 2) * π / L < k) (h2 : k < n * π / L)
    (hk : k * Real.cos (k * L) + h * Real.sin (k * L) = 0) :
    (n - 1 / 2) * π + Real.arctan (h * L / (n * π)) < k * L ∧
      k * L < (n - 1 / 2) * π + Real.arctan (h * L / ((n - 1 / 2) * π)) := by
  have z1 : (n - 1 / 2) * π < k * L := by rwa [div_lt_iff₀ hL] at h1
  have z2 : k * L < n * π := by rwa [lt_div_iff₀ hL] at h2
  have hz : (k * L) * Real.cos (k * L) + (h * L) * Real.sin (k * L) = 0 := by
    linear_combination L * hk
  have e := robin_root_arctan n hn z1 z2 hz
  have hn' : (1 : ℝ) ≤ n := by exact_mod_cast hn
  have q1 : 0 < (n - 1 / 2) * π := mul_pos (by linarith) pi_pos
  have zpos : 0 < k * L := lt_trans q1 z1
  constructor
  · have : Real.arctan (h * L / (n * π)) < Real.arctan (h * L / (k * L)) :=
      Real.arctan_strictMono (div_lt_div_of_pos_left (mul_pos hh hL) zpos z2)
    linarith
  · have : Real.arctan (h * L / (k * L)) < Real.arctan (h * L / ((n - 1 / 2) * π)) :=
      Real.arctan_strictMono (div_lt_div_of_pos_left (mul_pos hh hL) q1 z1)
    linarith

end GLM.RobinBoth
