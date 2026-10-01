/-
# The seeds: forced by their roles, not by the substrate, and not recoverable from 13

The GLM's constants are built from three seeds, `π`, `φ` and `e`, and the
framework reads the integer `13 = ⌊π φ e⌋` out of them.  The archive's
first-principles and projection sub-studies (`data_object/FirstPrinciples/Seeds.lean`,
`data_object/Projection/{Independence,Fibre,Cheapest}.lean`) asked four
questions of that construction.  `SeedLayers.lean` retrieved where each seed may
enter; this file retrieves the rest.  The source files depended on a module the
archive does not contain, so the numerical bounds are re-derived here from
`FitCapacity.lean`'s, and the irrationality of `e`, which the pinned Mathlib does
not carry, is proved here (`eSeed_irrational`) rather than assumed.

**1. The seeds are an input, not an output.**  Everything a binary substrate
counts is an integer, and no seed is a ratio of integers
(`seeds_not_ratio_of_counts`, from `seeds_irrational`).  `φ` is algebraic, so a
substrate able to solve a quadratic reaches it from its own integers
(`phi_reachable_by_root_extraction`); `π` and `e` are not reachable that way
unless they are algebraic, which classical theorems (not carried here) deny.

**2. Each seed is forced by its role.**  Given that the role is wanted, the
number is not a choice: `φ` is the unique positive solution of one-step
self-similarity `x² = x + 1` (`phi_unique_positive_root`); `π` is the least
positive zero of `sin`, the first closure of a rotation
(`pi_least_positive_zero`); `e` is the unique base whose exponential grows at
unit rate at the origin (`e_unique_unit_growth_base`).  The three are distinct
(`seeds_distinct`).

**3. The combining rule is not forced, and 13 cannot be run backwards.**
`⌊π φ e⌋ = 13`, but four equally simple monomials give four different integers
(`hull_alternatives`: 13, 5, 22, 37), and three different monomials give 13
(`three_monomials_give_thirteen`: `πφe`, `πφ³`, `π⁴/e²`).  The fibre of `⌊·⌋`
over 13 is the whole interval `[13, 14)`, of measure one
(`floor_fibre_thirteen`, `floor_fibre_measure`), so "recover the seeds from 13"
is impossible, not hard (`thirteen_not_invertible`).  The same holds of the
trace: infinitely many integral motions share trace 2 (`trace_fibre_infinite`),
and two of them are not conjugate over `ℤ` although trace, determinant and
characteristic polynomial agree (`same_trace_not_conjugate`).

**4. The independence question has exactly two branches.**  Whether `π e` is
transcendental is open.  Either it is — and then the monad, the wobble and the
leak are all irrational (`monad_irrational_of_pi_mul_e_transcendental`,
`wobble_irrational_of_pi_mul_e_transcendental`) — or it is algebraic, and a
rational monad would *force* that (`pi_mul_e_isAlgebraic_of_monad_rat`).  There
is no third branch (`pi_mul_e_dichotomy`).  Neither branch is asserted.

**5. In what sense `φ` is cheapest.**  `φ` is the smallest quadratic Pisot
number (`phi_isQuadPisot`, `quadratic_pisot_ge_phi`) — but not the smallest
Pisot number: the plastic number `ρ ≈ 1.3247`, the real root of `x³ = x + 1`,
is smaller (`plastic_lt_phi`) and its two conjugates lie strictly inside the
unit disc (`plastic_conjugates_inside_disc`).  The property that actually makes
`φ` extremal is different: it is badly approximable, `|φ − p/q| ≥ 1/(3q²)`
(`phi_badly_approximable`), and so is not a Liouville number
(`phi_not_liouville`).

**6. The one-parameter motions, completed.**  With `e` irrational, no lattice
symmetry has `e` as a character value, unconditionally
(`lattice_character_ne_eSeed_unconditional`).  The trace decides the type of a
motion in `SL(2,ℝ)` — elliptic, parabolic or hyperbolic (`sl2_trichotomy`) —
and each seed's number forgets something: `2π` forgets the winding number
(`period_fibre_infinite`), and `e`, the time-one value of the flow `f' = f`
(`flow_time_one`), forgets the clock (`e_flow_fibre`).
-/
import RequestProject.GLM.SeedLayers

namespace GLM.SeedRoles

open FitCapacity (phi eSeed monad wobble leak)

/-! ## 0. Bounds and irrationality -/

private theorem mul_between {a b c d x y : ℝ} (ha : 0 < a) (hc : 0 < c)
    (h1 : a < x) (h2 : x < b) (h3 : c < y) (h4 : y < d) : a * c < x * y ∧ x * y < b * d :=
  ⟨by nlinarith, by nlinarith⟩

private theorem div_between {a b c d x y : ℝ} (ha : 0 < a) (hc : 0 < c)
    (h1 : a < x) (h2 : x < b) (h3 : c < y) (h4 : y < d) : a / d < x / y ∧ x / y < b / c := by
  have hy : 0 < y := by linarith
  have hd : 0 < d := by linarith
  constructor
  · rw [div_lt_div_iff₀ hd hy]; nlinarith
  · rw [div_lt_div_iff₀ hy hc]; nlinarith

private theorem floor_of_between {x : ℝ} {k : ℤ} (h1 : (k : ℝ) < x) (h2 : x < k + 1) :
    ⌊x⌋ = k :=
  Int.floor_eq_iff.2 ⟨h1.le, h2⟩

theorem phi_crude : 1.618 < phi ∧ phi < 1.619 := by
  obtain ⟨h1, h2⟩ := FitCapacity.phi_bounds; constructor <;> linarith

theorem eSeed_crude : 2.718 < eSeed ∧ eSeed < 2.719 := by
  obtain ⟨h1, h2⟩ := FitCapacity.eSeed_bounds; constructor <;> linarith

theorem pi_crude : 3.14 < Real.pi ∧ Real.pi < 3.15 := by
  obtain ⟨h1, h2⟩ := FitCapacity.pi_bounds; constructor <;> linarith

/-- **`e` is irrational** (Fourier's argument).  If `e = p/q` then with
`n = q + 1` the number `n! (e − Σ_{m ≤ n} 1/m!)` is an integer, and the tail
bound `Real.exp_bound` puts it strictly between `0` and `1`. -/
theorem eSeed_irrational : Irrational eSeed := by
  rintro ⟨r, hr⟩
  set q := r.den with hq
  set n := q + 1 with hn
  have hqpos : 0 < q := r.den_pos
  obtain ⟨k, hk⟩ : q ∣ n.factorial := Nat.dvd_factorial hqpos (by omega)
  have hup := Real.exp_bound (x := 1) (by simp) (n := n + 1) (by omega)
  have h1le := Real.sum_le_exp_of_nonneg (x := 1) zero_le_one (n + 2)
  rw [Finset.sum_range_succ] at h1le
  simp only [abs_one, one_pow, one_mul] at hup h1le
  set S := ∑ m ∈ Finset.range (n + 1), (1 : ℝ) / (m.factorial : ℝ) with hSdef
  obtain ⟨N, hN⟩ : ∃ N : ℕ, (n.factorial : ℝ) * S = N := by
    refine ⟨∑ m ∈ Finset.range (n + 1), n.factorial / m.factorial, ?_⟩
    rw [hSdef, Finset.mul_sum]; push_cast
    refine Finset.sum_congr rfl fun m hm => ?_
    have hmn : m ≤ n := Nat.lt_succ_iff.1 (Finset.mem_range.1 hm)
    rw [Nat.cast_div (Nat.factorial_dvd_factorial hmn) (by positivity)]
    ring
  have hE : (n.factorial : ℝ) * Real.exp 1 = ((r.num * k : ℤ) : ℝ) := by
    rw [show Real.exp 1 = eSeed from rfl, ← hr]
    have : (r : ℝ) = r.num / r.den := by exact_mod_cast (Rat.num_div_den r).symm
    rw [this, hk]; push_cast
    have : (r.den : ℝ) ≠ 0 := by exact_mod_cast r.den_nz
    field_simp
    rw [hq]; ring
  have hlow : S < Real.exp 1 := by
    have : (0 : ℝ) < 1 / ((n + 1).factorial : ℝ) := by positivity
    linarith
  rw [abs_of_pos (by linarith)] at hup
  have hfpos : (0 : ℝ) < n.factorial := by positivity
  have hnR : (1 : ℝ) ≤ n := by exact_mod_cast (show 1 ≤ n by omega)
  have h0 : 0 < (n.factorial : ℝ) * (Real.exp 1 - S) := mul_pos hfpos (by linarith)
  have h1 : (n.factorial : ℝ) * (Real.exp 1 - S) < 1 := by
    have hfs : ((n + 1).factorial : ℝ) = (n + 1) * n.factorial := by
      rw [Nat.factorial_succ]; push_cast; ring
    have ha : (n.factorial : ℝ) * (Real.exp 1 - S) ≤ (n + 2 : ℝ) / ((n + 1) * (n + 1)) := by
      calc (n.factorial : ℝ) * (Real.exp 1 - S)
          ≤ n.factorial * ((n + 1).succ / ((n + 1).factorial * (n + 1 : ℕ))) :=
            mul_le_mul_of_nonneg_left hup hfpos.le
        _ = (n + 2 : ℝ) / ((n + 1) * (n + 1)) := by
            rw [hfs]; push_cast; field_simp; ring
    have hb : (n + 2 : ℝ) / ((n + 1) * (n + 1)) < 1 := by
      rw [div_lt_iff₀ (by positivity)]; nlinarith
    linarith
  have hint : (n.factorial : ℝ) * (Real.exp 1 - S) = ((r.num * k - N : ℤ) : ℝ) := by
    rw [mul_sub, hE, hN]; push_cast; ring
  rw [hint] at h0 h1
  have a : (0 : ℤ) < r.num * k - N := by exact_mod_cast h0
  have b : r.num * k - N < (1 : ℤ) := by exact_mod_cast h1
  omega

theorem phi_irrational : Irrational phi := Real.goldenRatio_irrational

/-- All three seeds are irrational. -/
theorem seeds_irrational : Irrational phi ∧ Irrational eSeed ∧ Irrational Real.pi :=
  ⟨phi_irrational, eSeed_irrational, irrational_pi⟩

/-- The three seeds are distinct: `φ < e < π`. -/
theorem seeds_distinct : phi < eSeed ∧ eSeed < Real.pi := by
  obtain ⟨-, h2⟩ := phi_crude
  obtain ⟨h3, h4⟩ := eSeed_crude
  obtain ⟨h5, -⟩ := pi_crude
  constructor <;> linarith

theorem phi_isAlgebraic : IsAlgebraic ℚ phi := by
  refine ⟨Polynomial.X ^ 2 - Polynomial.X - 1, ?_, ?_⟩
  · intro hzero
    have := congrArg (fun P : Polynomial ℚ => P.coeff 2) hzero
    simp [Polynomial.coeff_X, Polynomial.coeff_one] at this
  · simp only [map_sub, map_pow, Polynomial.aeval_X, map_one]
    rw [SeedLayers.phi_sq]; ring

/-! ## 1. The seeds are an input, not an output -/

/-- No seed is a ratio of two integers — in particular of two counts. -/
theorem seeds_not_ratio_of_counts (p q : ℤ) :
    ((p : ℝ) / q ≠ phi) ∧ ((p : ℝ) / q ≠ eSeed) ∧ ((p : ℝ) / q ≠ Real.pi) := by
  obtain ⟨hphi, he, hpi⟩ := seeds_irrational
  have hrat : ((p : ℝ) / q) = ((p / q : ℚ) : ℝ) := by push_cast; ring
  refine ⟨?_, ?_, ?_⟩
  · intro h; exact hphi ⟨p / q, by rw [← hrat, h]⟩
  · intro h; exact he ⟨p / q, by rw [← hrat, h]⟩
  · intro h; exact hpi ⟨p / q, by rw [← hrat, h]⟩

/-- `φ` is algebraic, and is reached from the integers by one root
extraction. -/
theorem phi_reachable_by_root_extraction :
    IsAlgebraic ℚ phi ∧ phi = (1 + Real.sqrt 5) / 2 :=
  ⟨phi_isAlgebraic, rfl⟩

/-! ## 2. Each seed is forced by its role -/

/-- The golden ratio is the unique positive solution of one-step
self-reference. -/
theorem phi_unique_positive_root (x : ℝ) (hx : 0 < x) : x ^ 2 = x + 1 ↔ x = phi := by
  constructor
  · intro h
    have hphi := SeedLayers.phi_sq
    have hgt1 := SeedLayers.phi_gt_one
    have key : (x - phi) * (x + phi - 1) = 0 := by nlinarith [h, hphi]
    rcases mul_eq_zero.mp key with h1 | h1
    · linarith
    · linarith
  · rintro rfl; exact SeedLayers.phi_sq

/-- `π` is the least positive zero of the sine: the first return of a
rotation. -/
theorem pi_least_positive_zero :
    Real.sin Real.pi = 0 ∧ ∀ x : ℝ, 0 < x → x < Real.pi → Real.sin x ≠ 0 :=
  ⟨Real.sin_pi, fun _ hx hxp => ne_of_gt (Real.sin_pos_of_pos_of_lt_pi hx hxp)⟩

/-- For a positive base `a`, the growth rate of `a ^ x` at the origin is
`log a`. -/
theorem deriv_rpow_zero (a : ℝ) (ha : 0 < a) :
    deriv (fun x : ℝ => a ^ x) 0 = Real.log a := by
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
    deriv (fun x : ℝ => a ^ x) 0 = 1 ↔ a = eSeed := by
  rw [deriv_rpow_zero a ha]
  constructor
  · intro h; rw [FitCapacity.eSeed, ← h, Real.exp_log ha]
  · rintro rfl; simp [FitCapacity.eSeed]

/-! ## 3. The combining rule is free, and the hull cannot be inverted -/

/-- Four equally simple monomials in the seeds, four different "hulls":
`⌊π φ e⌋ = 13`, `⌊π e / φ⌋ = 5`, `⌊π φ² e⌋ = 22`, `⌊π φ e²⌋ = 37`. -/
theorem hull_alternatives :
    ⌊monad⌋ = 13 ∧ ⌊Real.pi * eSeed / phi⌋ = 5 ∧
      ⌊Real.pi * phi ^ 2 * eSeed⌋ = 22 ∧ ⌊Real.pi * phi * eSeed ^ 2⌋ = 37 := by
  obtain ⟨p1, p2⟩ := pi_crude
  obtain ⟨f1, f2⟩ := phi_crude
  obtain ⟨e1, e2⟩ := eSeed_crude
  have pe := mul_between (by norm_num) (by norm_num) p1 p2 e1 e2
  have pf := mul_between (by norm_num) (by norm_num) p1 p2 f1 f2
  have f2b : (2.618 : ℝ) < phi ^ 2 ∧ phi ^ 2 < 2.619 := by
    rw [SeedLayers.phi_sq]; constructor <;> linarith
  have e2b := mul_between (by norm_num) (by norm_num) e1 e2 e1 e2
  refine ⟨FitCapacity.monad_floor, ?_, ?_, ?_⟩
  · have h := div_between (by norm_num) (by norm_num) pe.1 pe.2 f1 f2
    exact floor_of_between (by push_cast; linarith [h.1]) (by push_cast; linarith [h.2])
  · have h1 := mul_between (by norm_num) (by norm_num) p1 p2 f2b.1 f2b.2
    have h := mul_between (by norm_num) (by norm_num) h1.1 h1.2 e1 e2
    exact floor_of_between (by push_cast; linarith [h.1]) (by push_cast; linarith [h.2])
  · have h := mul_between (by norm_num) (by norm_num) pf.1 pf.2 e2b.1 e2b.2
    rw [show eSeed ^ 2 = eSeed * eSeed by ring]
    exact floor_of_between (by push_cast; linarith [h.1]) (by push_cast; linarith [h.2])

/-- `⌊π φ³⌋ = 13`. -/
theorem floor_pi_phi_cubed : ⌊Real.pi * phi ^ 3⌋ = 13 := by
  obtain ⟨p1, p2⟩ := pi_crude
  obtain ⟨f1, f2⟩ := phi_crude
  have f3 : (4.2358 : ℝ) < phi ^ 3 ∧ phi ^ 3 < 4.2437 := by
    have : phi ^ 3 = 2 * phi + 1 := by
      have h := SeedLayers.phi_sq
      calc phi ^ 3 = phi * phi ^ 2 := by ring
        _ = phi * (phi + 1) := by rw [h]
        _ = phi ^ 2 + phi := by ring
        _ = 2 * phi + 1 := by rw [h]; ring
    rw [this]; constructor <;> linarith
  have h := mul_between (by norm_num) (by norm_num) p1 p2 f3.1 f3.2
  exact floor_of_between (by push_cast; linarith [h.1]) (by push_cast; linarith [h.2])

/-- `⌊π⁴/e²⌋ = 13`. -/
theorem floor_pi_fourth_div_e_sq : ⌊Real.pi ^ 4 / eSeed ^ 2⌋ = 13 := by
  obtain ⟨p1, p2⟩ := pi_crude
  obtain ⟨e1, e2⟩ := eSeed_crude
  have p2b := mul_between (by norm_num) (by norm_num) p1 p2 p1 p2
  have p4b := mul_between (by norm_num) (by norm_num) p2b.1 p2b.2 p2b.1 p2b.2
  have e2b := mul_between (by norm_num) (by norm_num) e1 e2 e1 e2
  have h := div_between (by norm_num) (by norm_num) p4b.1 p4b.2 e2b.1 e2b.2
  rw [show Real.pi ^ 4 = Real.pi * Real.pi * (Real.pi * Real.pi) by ring,
    show eSeed ^ 2 = eSeed * eSeed by ring]
  exact floor_of_between (by push_cast; linarith [h.1]) (by push_cast; linarith [h.2])

/-- Three different monomials in the seeds have the same hull, 13. -/
theorem three_monomials_give_thirteen :
    ⌊Real.pi * phi * eSeed⌋ = 13 ∧ ⌊Real.pi * phi ^ 3⌋ = 13 ∧
      ⌊Real.pi ^ 4 / eSeed ^ 2⌋ = 13 :=
  ⟨FitCapacity.monad_floor, floor_pi_phi_cubed, floor_pi_fourth_div_e_sq⟩

/-- The fibre of `⌊·⌋` over `13` is the interval `[13, 14)`. -/
theorem floor_fibre_thirteen : {x : ℝ | ⌊x⌋ = 13} = Set.Ico 13 14 := by
  ext x
  simp only [Set.mem_setOf_eq, Set.mem_Ico, Int.floor_eq_iff]
  norm_num

open MeasureTheory in
/-- The fibre has measure one: the hull destroys a full unit interval of
information. -/
theorem floor_fibre_measure : volume {x : ℝ | ⌊x⌋ = 13} = 1 := by
  rw [floor_fibre_thirteen, Real.volume_Ico]
  norm_num

/-- Two distinct seed monomials, `π φ e` and `π φ³`, share the hull 13. -/
theorem hull_map_not_injective :
    Real.pi * phi * eSeed ≠ Real.pi * phi ^ 3 ∧
      ⌊Real.pi * phi * eSeed⌋ = 13 ∧ ⌊Real.pi * phi ^ 3⌋ = 13 := by
  refine ⟨?_, FitCapacity.monad_floor, floor_pi_phi_cubed⟩
  intro h
  have h1 : (13.8 : ℝ) < Real.pi * phi * eSeed := by
    have := FitCapacity.monad_bounds.1
    unfold FitCapacity.monad at this
    linarith
  have h2 : Real.pi * phi ^ 3 < 13.4 := by
    obtain ⟨p1, p2⟩ := pi_crude
    obtain ⟨f1, f2⟩ := phi_crude
    have : phi ^ 3 < 4.2437 := by nlinarith [SeedLayers.phi_sq]
    nlinarith
  linarith

open MeasureTheory in
/-- *The hull cannot be run backwards.*  Knowing `⌊ℳ⌋ = 13` leaves a whole unit
interval of possible `ℳ`, with at least two distinct seed monomials in it. -/
theorem thirteen_not_invertible :
    volume {x : ℝ | ⌊x⌋ = 13} = 1 ∧ (∃ x y : ℝ, x ≠ y ∧ ⌊x⌋ = 13 ∧ ⌊y⌋ = 13) :=
  ⟨floor_fibre_measure, _, _, hull_map_not_injective⟩

/-! ### The trace projection on integral motions -/

/-- The trace is a class function: conjugation cannot change it. -/
theorem trace_conj_eq {n : Type*} [Fintype n] [DecidableEq n]
    (A P Q : Matrix n n ℤ) (h : Q * P = 1) : (P * A * Q).trace = A.trace := by
  rw [Matrix.trace_mul_cycle, h, Matrix.one_mul]

/-- The integral shear by `k`. -/
def intShear (k : ℤ) : Matrix (Fin 2) (Fin 2) ℤ := !![1, k; 0, 1]

theorem intShear_det (k : ℤ) : (intShear k).det = 1 := by
  simp [intShear, Matrix.det_fin_two]

theorem intShear_trace (k : ℤ) : (intShear k).trace = 2 := by
  simp [intShear, Matrix.trace_fin_two]

theorem intShear_injective : Function.Injective intShear := by
  intro a b hab
  have := congrArg (fun M : Matrix (Fin 2) (Fin 2) ℤ => M 0 1) hab
  simpa [intShear] using this

/-- The fibre of the trace over `2` is infinite: the number `2` remembers
nothing about which integral motion produced it. -/
theorem trace_fibre_infinite :
    {A : Matrix (Fin 2) (Fin 2) ℤ | A.det = 1 ∧ A.trace = 2}.Infinite := by
  refine Set.Infinite.mono (s := Set.range intShear) ?_
    (Set.infinite_range_of_injective intShear_injective)
  rintro _ ⟨k, rfl⟩
  exact ⟨intShear_det k, intShear_trace k⟩

/-- Same trace, same determinant, same characteristic polynomial — and yet not
the same motion: no integral change of basis conjugates the shear by `1` into
the shear by `2`. -/
theorem same_trace_not_conjugate (P : Matrix (Fin 2) (Fin 2) ℤ)
    (hP : P.det = 1 ∨ P.det = -1) : P * intShear 1 ≠ intShear 2 * P := by
  intro h
  have h01 : P 0 0 = P 0 0 + 2 * P 1 0 := by
    have := congrFun (congrFun h 0) 0
    simpa [intShear, Matrix.mul_apply, Fin.sum_univ_two] using this
  have h02 : P 0 0 + P 0 1 = P 0 1 + 2 * P 1 1 := by
    have := congrFun (congrFun h 0) 1
    simpa [intShear, Matrix.mul_apply, Fin.sum_univ_two] using this
  have hc : P 1 0 = 0 := by omega
  have ha : P 0 0 = 2 * P 1 1 := by omega
  have hdet : P.det = 2 * P 1 1 * P 1 1 := by
    rw [Matrix.det_fin_two, ha, hc]
    ring
  have hdvd : (2 : ℤ) ∣ P.det := ⟨P 1 1 * P 1 1, by rw [hdet]; ring⟩
  rcases hP with hP | hP <;> rw [hP] at hdvd <;> omega

/-! ## 4. The two branches of the independence question -/

/-- The two branches are exhaustive: `π e` is either transcendental or
algebraic over `ℚ`. -/
theorem pi_mul_e_dichotomy :
    Transcendental ℚ (Real.pi * eSeed) ∨ IsAlgebraic ℚ (Real.pi * eSeed) := by
  by_cases h : IsAlgebraic ℚ (Real.pi * eSeed)
  · exact Or.inr h
  · exact Or.inl h

/-- **Branch B.**  If the monad is rational then `π e` is algebraic — an
algebraic relation between `π` and `e`. -/
theorem pi_mul_e_isAlgebraic_of_monad_rat (r : ℚ) (h : monad = (r : ℝ)) :
    IsAlgebraic ℚ (Real.pi * eSeed) := by
  have hr : IsAlgebraic ℚ ((r : ℝ)) := isAlgebraic_algebraMap r
  have hne : phi ≠ 0 := ne_of_gt (by linarith [SeedLayers.phi_gt_one])
  have hval : Real.pi * eSeed = (r : ℝ) / phi := by
    have hmon : Real.pi * phi * eSeed = (r : ℝ) := by rw [← h, FitCapacity.monad]
    field_simp
    linarith [hmon]
  rw [hval, div_eq_mul_inv]
  exact hr.mul phi_isAlgebraic.inv

/-- **Branch A.**  If `π e` is transcendental then the monad is irrational. -/
theorem monad_irrational_of_pi_mul_e_transcendental
    (h : Transcendental ℚ (Real.pi * eSeed)) : Irrational monad := by
  rintro ⟨r, hr⟩
  exact h (pi_mul_e_isAlgebraic_of_monad_rat r hr.symm)

/-- **Branch A, continued.**  Then the wobble `w = ℳ − 13` and the leak
`L = w/13` are irrational too. -/
theorem wobble_irrational_of_pi_mul_e_transcendental
    (h : Transcendental ℚ (Real.pi * eSeed)) : Irrational wobble ∧ Irrational leak := by
  have hm : Irrational monad := monad_irrational_of_pi_mul_e_transcendental h
  have hw : Irrational wobble := by
    rintro ⟨r, hr⟩
    exact hm ⟨r + 13, by push_cast; rw [hr, FitCapacity.wobble]; ring⟩
  refine ⟨hw, ?_⟩
  rintro ⟨r, hr⟩
  exact hw ⟨13 * r, by push_cast; rw [hr, FitCapacity.leak]; ring⟩

/-! ## 5. In what sense `φ` is cheapest -/

/-- `b` and `b'` are the two roots of the monic integer quadratic
`x² − p x − q`, with `b > 1` and the conjugate strictly inside the unit circle.
(Vieta's relations are taken as the definition.) -/
def IsQuadPisotPair (b b' : ℝ) (p q : ℤ) : Prop :=
  b + b' = (p : ℝ) ∧ b * b' = -(q : ℝ) ∧ 1 < b ∧ |b'| < 1

/-- `φ` is a quadratic Pisot number: `x² − x − 1`, conjugate `1 − φ` of
modulus `0.618… < 1`. -/
theorem phi_isQuadPisot : IsQuadPisotPair phi (1 - phi) 1 1 := by
  have hsq := SeedLayers.phi_sq
  obtain ⟨h1, h2⟩ := phi_crude
  refine ⟨by push_cast; ring, by push_cast; nlinarith [hsq], by linarith, ?_⟩
  rw [abs_lt]
  constructor <;> linarith

/-- *No quadratic Pisot number is smaller than `φ`.*  The trace is a positive
integer, the polynomial is negative at `1` so `p + q ≥ 2`, and together these
make the polynomial non-positive at `φ`. -/
theorem quadratic_pisot_ge_phi {b b' : ℝ} {p q : ℤ} (h : IsQuadPisotPair b b' p q) :
    phi ≤ b := by
  obtain ⟨hsum, hprod, hb, hb'⟩ := h
  rw [abs_lt] at hb'
  have hsq := SeedLayers.phi_sq
  have hphi1 := SeedLayers.phi_gt_one
  have hp0 : (0 : ℝ) < (p : ℝ) := by rw [← hsum]; linarith [hb'.1]
  have hp1 : (1 : ℤ) ≤ p := by
    have hp0' : (0 : ℤ) < p := by exact_mod_cast hp0
    omega
  have hval1 : (1 : ℝ) - p - q < 0 := by nlinarith [hb'.2]
  have hpq : (2 : ℤ) ≤ p + q := by
    have : (1 : ℝ) < (p : ℝ) + q := by linarith
    have h' : (1 : ℤ) < p + q := by exact_mod_cast this
    omega
  have hkey : phi ^ 2 - (p : ℝ) * phi - (q : ℝ) ≤ 0 := by
    have hp1' : (1 : ℝ) ≤ (p : ℝ) := by exact_mod_cast hp1
    have hpq' : (2 : ℝ) ≤ (p : ℝ) + (q : ℝ) := by exact_mod_cast hpq
    nlinarith [hsq, hphi1, hp1', hpq']
  have hfac : phi ^ 2 - (p : ℝ) * phi - (q : ℝ) = (phi - b) * (phi - b') := by
    rw [← hsum, ← neg_neg ((q : ℝ)), ← hprod]
    ring
  have hpos : 0 < phi - b' := by linarith [hb'.2]
  nlinarith [hkey, hfac, hpos]

theorem exists_plastic : ∃ r : ℝ, r ^ 3 = r + 1 ∧ 1.32 < r ∧ r < 1.33 := by
  have hcont : ContinuousOn (fun x : ℝ => x ^ 3 - x - 1) (Set.Icc (1.32 : ℝ) 1.33) := by
    fun_prop
  have h := intermediate_value_Icc (by norm_num : (1.32 : ℝ) ≤ 1.33) hcont
  have h0 : (0 : ℝ) ∈ Set.Icc ((fun x : ℝ => x ^ 3 - x - 1) 1.32)
      ((fun x : ℝ => x ^ 3 - x - 1) 1.33) := by
    constructor <;> norm_num
  obtain ⟨r, hr, hr0⟩ := h h0
  simp only at hr0
  refine ⟨r, by linarith, ?_, ?_⟩
  · rcases lt_or_eq_of_le hr.1 with h' | h'
    · exact h'
    · rw [← h'] at hr0; norm_num at hr0
  · rcases lt_or_eq_of_le hr.2 with h' | h'
    · exact h'
    · rw [h'] at hr0; norm_num at hr0

/-- The plastic number: the real root of `x³ = x + 1`. -/
noncomputable def plastic : ℝ := Classical.choose exists_plastic

theorem plastic_cubic : plastic ^ 3 = plastic + 1 := (Classical.choose_spec exists_plastic).1

theorem plastic_bounds : 1.32 < plastic ∧ plastic < 1.33 :=
  ⟨(Classical.choose_spec exists_plastic).2.1, (Classical.choose_spec exists_plastic).2.2⟩

/-- Any real solution of `x³ = x + 1` exceeds `1`. -/
theorem cubic_root_gt_one {t : ℝ} (h : t ^ 3 = t + 1) : 1 < t := by
  nlinarith [sq_nonneg (t - 1), sq_nonneg (t + 1), sq_nonneg t]

/-- `x³ = x + 1` has exactly one real solution. -/
theorem cubic_real_root_unique {x y : ℝ} (hx : x ^ 3 = x + 1) (hy : y ^ 3 = y + 1) :
    x = y := by
  have hx1 := cubic_root_gt_one hx
  have hy1 := cubic_root_gt_one hy
  by_contra hne
  have hfac : (x - y) * (x ^ 2 + x * y + y ^ 2 - 1) = 0 := by nlinarith [hx, hy]
  rcases mul_eq_zero.mp hfac with h | h
  · exact hne (by linarith)
  · nlinarith [hx1, hy1]

/-- The plastic number is smaller than `φ`: `φ` is the cheapest quadratic
self-similarity, not the cheapest one. -/
theorem plastic_lt_phi : plastic < phi := by
  have h1 := plastic_bounds.2
  have h2 := phi_crude.1
  linarith

/-- The plastic number is a Pisot number: its two complex conjugates lie
strictly inside the unit circle. -/
theorem plastic_conjugates_inside_disc (z : ℂ) (hz : z ^ 3 = z + 1)
    (hne : z ≠ (plastic : ℂ)) : ‖z‖ < 1 := by
  have hr : (plastic : ℂ) ^ 3 = (plastic : ℂ) + 1 := by
    exact_mod_cast congrArg (fun t : ℝ => (t : ℂ)) plastic_cubic
  have hquad : z ^ 2 + (plastic : ℂ) * z + ((plastic : ℂ) ^ 2 - 1) = 0 := by
    have hfac : (z - (plastic : ℂ)) *
        (z ^ 2 + (plastic : ℂ) * z + ((plastic : ℂ) ^ 2 - 1)) = 0 := by
      linear_combination hz - hr
    rcases mul_eq_zero.mp hfac with h | h
    · exact absurd (sub_eq_zero.mp h) hne
    · exact h
  have hnotreal : z ≠ (z.re : ℂ) := by
    intro hreal
    have : (z.re : ℝ) ^ 3 = z.re + 1 := by
      have h1 : ((z.re : ℂ)) ^ 3 = (z.re : ℂ) + 1 := by rw [← hreal]; exact hz
      exact_mod_cast h1
    exact hne (by rw [hreal, cubic_real_root_unique this plastic_cubic])
  have hconj : (starRingEnd ℂ) z ≠ z := by
    intro h
    exact hnotreal (Complex.conj_eq_iff_re.mp h).symm
  have hquad' : ((starRingEnd ℂ) z) ^ 2 + (plastic : ℂ) * ((starRingEnd ℂ) z) +
      ((plastic : ℂ) ^ 2 - 1) = 0 := by
    have := congrArg (starRingEnd ℂ) hquad
    simpa using this
  have hsum : z + (starRingEnd ℂ) z = -(plastic : ℂ) := by
    have hdiff : (z - (starRingEnd ℂ) z) * (z + (starRingEnd ℂ) z + (plastic : ℂ)) = 0 := by
      linear_combination hquad - hquad'
    rcases mul_eq_zero.mp hdiff with h | h
    · exact absurd (sub_eq_zero.mp h).symm hconj
    · linear_combination h
  have hprod : z * (starRingEnd ℂ) z = ((plastic : ℂ) ^ 2 - 1) := by
    have hs : (starRingEnd ℂ) z = -(plastic : ℂ) - z := by linear_combination hsum
    rw [hs]
    linear_combination -hquad
  have hnormSq : (Complex.normSq z : ℝ) = plastic ^ 2 - 1 := by
    have := Complex.mul_conj z
    rw [hprod] at this
    exact_mod_cast this.symm
  have hb := plastic_bounds
  have hlt : plastic ^ 2 - 1 < 1 := by nlinarith [hb.1, hb.2]
  have hsq : ‖z‖ ^ 2 = plastic ^ 2 - 1 := by rw [Complex.sq_norm, hnormSq]
  nlinarith [norm_nonneg z, hsq, hlt]

theorem phi_conj_prod : phi * (1 - phi) = -1 := by
  nlinarith [SeedLayers.phi_sq]

theorem phi_sub_conj : phi - (1 - phi) = Real.sqrt 5 := by
  unfold FitCapacity.phi
  ring

/-- The integer form `p² − pq − q²` never vanishes for `q > 0`: otherwise `√5`
would be rational. -/
theorem norm_form_ne_zero (p q : ℤ) (hq : 0 < q) : p ^ 2 - p * q - q ^ 2 ≠ 0 := by
  intro h
  have hsq : (2 * p - q) ^ 2 = 5 * q ^ 2 := by ring_nf; linarith [h]
  have hqR : (0 : ℝ) < (q : ℝ) := by exact_mod_cast hq
  have hR : ((2 * p - q : ℤ) : ℝ) ^ 2 = 5 * ((q : ℤ) : ℝ) ^ 2 := by exact_mod_cast hsq
  have habs : (|((2 * p - q : ℤ) : ℝ)| / (q : ℝ)) ^ 2 = 5 := by
    rw [div_pow, sq_abs, hR]
    field_simp
  have h5 : Real.sqrt 5 = |((2 * p - q : ℤ) : ℝ)| / (q : ℝ) := by
    rw [← habs, Real.sqrt_sq (by positivity)]
  have hirr : Irrational (Real.sqrt 5) := by
    simpa using (Nat.prime_five).irrational_sqrt
  refine hirr ⟨(|2 * p - q| : ℤ) / (q : ℚ), ?_⟩
  rw [h5]
  push_cast
  ring

/-- *`φ` is badly approximable*: `|φ − p/q| ≥ 1/(3q²)` for every rational `p/q`
with `q > 0`.  (The sharp constant is `1/(√5 q²)`; what matters is the exponent
2 with a positive constant.) -/
theorem phi_badly_approximable (p q : ℤ) (hq : 0 < q) :
    1 / (3 * (q : ℝ) ^ 2) ≤ |phi - (p : ℝ) / (q : ℝ)| := by
  have hqR : (0 : ℝ) < (q : ℝ) := by exact_mod_cast hq
  have hq1 : (1 : ℝ) ≤ (q : ℝ) := by exact_mod_cast hq
  set t : ℝ := |(p : ℝ) - (q : ℝ) * phi| with ht
  have hfac : ((p : ℝ) - q * phi) * ((p : ℝ) - q * (1 - phi)) =
      ((p ^ 2 - p * q - q ^ 2 : ℤ) : ℝ) := by
    have h1 : phi * (1 - phi) = -1 := phi_conj_prod
    push_cast
    nlinarith [h1]
  have hne : ((p ^ 2 - p * q - q ^ 2 : ℤ) : ℝ) ≠ 0 := by
    exact_mod_cast norm_form_ne_zero p q hq
  have hge1 : (1 : ℝ) ≤ |((p ^ 2 - p * q - q ^ 2 : ℤ) : ℝ)| := by
    have h1 : (1 : ℤ) ≤ |p ^ 2 - p * q - q ^ 2| := by
      rcases lt_trichotomy (p ^ 2 - p * q - q ^ 2) 0 with h | h | h
      · rw [abs_of_neg h]; omega
      · exact absurd (by exact_mod_cast congrArg (fun n : ℤ => (n : ℝ)) h) hne
      · rw [abs_of_pos h]; omega
    calc (1 : ℝ) = ((1 : ℤ) : ℝ) := by norm_num
      _ ≤ ((|p ^ 2 - p * q - q ^ 2| : ℤ) : ℝ) := by exact_mod_cast h1
      _ = |((p ^ 2 - p * q - q ^ 2 : ℤ) : ℝ)| := by push_cast [Int.cast_abs]; ring_nf
  have hkey : 1 ≤ t * |(p : ℝ) - q * (1 - phi)| := by
    rw [ht, ← abs_mul, hfac]
    exact hge1
  have hbound : |(p : ℝ) - q * (1 - phi)| ≤ t + (q : ℝ) * Real.sqrt 5 := by
    have hrw : (p : ℝ) - q * (1 - phi) =
        ((p : ℝ) - q * phi) + (q : ℝ) * (phi - (1 - phi)) := by ring
    calc |(p : ℝ) - q * (1 - phi)|
        ≤ |(p : ℝ) - q * phi| + |(q : ℝ) * (phi - (1 - phi))| := by
          rw [hrw]; exact abs_add_le _ _
      _ = t + (q : ℝ) * Real.sqrt 5 := by
          rw [phi_sub_conj, abs_mul, abs_of_pos hqR, abs_of_nonneg (Real.sqrt_nonneg 5)]
  have htpos : 0 ≤ t := abs_nonneg _
  have hprod2 : 1 ≤ t * (t + (q : ℝ) * Real.sqrt 5) := by
    have := mul_le_mul_of_nonneg_left hbound htpos
    linarith [hkey, this]
  have htlb : 1 / (3 * (q : ℝ)) ≤ t := by
    by_contra hcon
    push_neg at hcon
    have hA : t * (3 * (q : ℝ)) < 1 := (lt_div_iff₀ (by positivity)).1 hcon
    have h5 : Real.sqrt 5 < 2.24 := by linarith [FitCapacity.sqrt5_bounds.2]
    have hs0 : 0 ≤ Real.sqrt 5 := Real.sqrt_nonneg 5
    have htq : t * (q : ℝ) < 1 / 3 := by linarith
    have ht13 : t < 1 / 3 := by nlinarith [htq, hq1, htpos]
    nlinarith [hprod2, ht13, htq, h5, htpos, hs0, hqR]
  have hdiv : |phi - (p : ℝ) / (q : ℝ)| = t / (q : ℝ) := by
    rw [ht, abs_sub_comm]
    rw [show (p : ℝ) - (q : ℝ) * phi = ((p : ℝ) / q - phi) * q by field_simp]
    rw [abs_mul, abs_of_pos hqR]
    field_simp
  rw [hdiv]
  have hrw : 1 / (3 * (q : ℝ) ^ 2) = (1 / (3 * (q : ℝ))) / (q : ℝ) := by
    field_simp
  rw [hrw]
  gcongr

/-- `φ` is not a Liouville number: being algebraic, it admits no approximation
of arbitrarily high order — the opposite extreme from the Liouville numbers. -/
theorem phi_not_liouville : ¬ Liouville phi := by
  intro h
  have halg : IsAlgebraic ℤ phi := by
    refine ⟨Polynomial.X ^ 2 - Polynomial.X - 1, ?_, ?_⟩
    · intro hzero
      have := congrArg (fun P : Polynomial ℤ => P.coeff 2) hzero
      simp [Polynomial.coeff_X, Polynomial.coeff_one] at this
    · simp only [map_sub, map_pow, Polynomial.aeval_X, map_one]
      rw [SeedLayers.phi_sq]
      ring
  exact h.transcendental halg

/-! ## 6. The one-parameter motions, completed -/

/-- **Unconditionally: no lattice symmetry has `e` as a character value.**
`SeedLayers.lattice_character_ne_eSeed` took the irrationality of `e` as a
hypothesis; `eSeed_irrational` discharges it. -/
theorem lattice_character_ne_eSeed_unconditional {n : Type*} [Fintype n]
    (M : Matrix n n ℤ) : ((M.trace : ℤ) : ℝ) ≠ eSeed :=
  SeedLayers.lattice_character_ne_eSeed eSeed_irrational M

/-- The fibre over "the rotation has closed up" is infinite: the number `2π`
remembers the period and forgets the winding number. -/
theorem period_fibre_infinite : {t : ℝ | SeedLayers.rot t = 1}.Infinite := by
  have hpi : (2 * Real.pi) ≠ 0 := by positivity
  have hinj : Function.Injective (fun k : ℤ => (k : ℝ) * (2 * Real.pi)) := by
    intro a b hab
    simp only at hab
    have : (a : ℝ) = b := mul_right_cancel₀ hpi hab
    exact_mod_cast this
  have hsub : Set.range (fun k : ℤ => (k : ℝ) * (2 * Real.pi)) ⊆
      {t : ℝ | SeedLayers.rot t = 1} := by
    rintro _ ⟨k, rfl⟩
    exact (SeedLayers.rot_eq_one_iff _).2 ⟨k, rfl⟩
  exact Set.Infinite.mono hsub (Set.infinite_range_of_injective hinj)

/-- A motion of trace `t` in `SL(2,ℝ)` has a real eigenvalue exactly when
`t² ≥ 4`. -/
theorem sl2_real_eigenvalue_iff (t : ℝ) :
    (∃ lam : ℝ, lam ^ 2 - t * lam + 1 = 0) ↔ 4 ≤ t ^ 2 := by
  constructor
  · rintro ⟨lam, hlam⟩
    nlinarith [sq_nonneg (2 * lam - t), sq_nonneg lam, sq_nonneg (lam - 1),
      sq_nonneg (lam + 1)]
  · intro ht
    refine ⟨(t + Real.sqrt (t ^ 2 - 4)) / 2, ?_⟩
    have hs : Real.sqrt (t ^ 2 - 4) ^ 2 = t ^ 2 - 4 := Real.sq_sqrt (by linarith)
    field_simp
    nlinarith [hs]

/-- The three types of motion, decided by the trace: elliptic (no real
eigenvalue — the rotation, where `π` lives), parabolic (one repeated real
eigenvalue — the shear) and hyperbolic (two distinct real eigenvalues — the
stretch, where `φ` lives). -/
theorem sl2_trichotomy (t : ℝ) :
    (t ^ 2 < 4 ∧ ¬ ∃ lam : ℝ, lam ^ 2 - t * lam + 1 = 0) ∨
    (t ^ 2 = 4 ∧ ∃! lam : ℝ, lam ^ 2 - t * lam + 1 = 0) ∨
    (4 < t ^ 2 ∧ ∃ lam mu : ℝ, lam ≠ mu ∧ lam ^ 2 - t * lam + 1 = 0 ∧
      mu ^ 2 - t * mu + 1 = 0) := by
  rcases lt_trichotomy (t ^ 2) 4 with h | h | h
  · left
    refine ⟨h, ?_⟩
    intro hex
    have := (sl2_real_eigenvalue_iff t).1 hex
    linarith
  · right; left
    refine ⟨h, ⟨t / 2, by nlinarith, ?_⟩⟩
    intro y hy
    nlinarith [sq_nonneg (2 * y - t)]
  · right; right
    have hs : Real.sqrt (t ^ 2 - 4) ^ 2 = t ^ 2 - 4 := Real.sq_sqrt (by linarith)
    have hspos : 0 < Real.sqrt (t ^ 2 - 4) := Real.sqrt_pos.mpr (by linarith)
    refine ⟨h, (t + Real.sqrt (t ^ 2 - 4)) / 2, (t - Real.sqrt (t ^ 2 - 4)) / 2, ?_, ?_, ?_⟩
    · intro hcon
      have : Real.sqrt (t ^ 2 - 4) = 0 := by linarith
      linarith
    · field_simp; nlinarith [hs]
    · field_simp; nlinarith [hs]

/-- `e` is the time-one value of the flow generated by the identity vector
field: any `f` with `f' = f` and `f 0 = 1` has `f 1 = e`. -/
theorem flow_time_one (f : ℝ → ℝ) (hf : ∀ x, HasDerivAt f (f x) x) (h0 : f 0 = 1) :
    f 1 = eSeed := by
  have hg : ∀ x : ℝ, HasDerivAt (fun y => f y * Real.exp (-y)) 0 x := by
    intro x
    have h1 : HasDerivAt (fun y : ℝ => Real.exp (-y)) (-Real.exp (-x)) x := by
      simpa using (Real.hasDerivAt_exp (-x)).comp x ((hasDerivAt_id x).neg)
    have h2 := (hf x).mul h1
    have h3 : f x * -Real.exp (-x) + f x * Real.exp (-x) = 0 := by ring
    simpa [h3] using h2
  have hconst : ∀ x : ℝ, f x * Real.exp (-x) = f 0 * Real.exp (-0) := by
    intro x
    exact is_const_of_deriv_eq_zero (fun y => (hg y).differentiableAt)
      (fun y => (hg y).deriv) x 0
  have h1 := hconst 1
  rw [h0] at h1
  simp only [neg_zero, Real.exp_zero, one_mul] at h1
  rw [FitCapacity.eSeed]
  have hx : Real.exp (-1 : ℝ) * Real.exp 1 = 1 := by
    rw [← Real.exp_add]; simp
  calc f 1 = f 1 * (Real.exp (-1) * Real.exp 1) := by rw [hx, mul_one]
    _ = (f 1 * Real.exp (-1)) * Real.exp 1 := by ring
    _ = Real.exp 1 := by rw [h1, one_mul]

/-- The fibre of `e` as a flow value is the whole time axis: for every non-zero
time `t` some base reaches `e` at time `t`.  The number remembers the value and
forgets the clock. -/
theorem e_flow_fibre (t : ℝ) (ht : t ≠ 0) : ∃ a : ℝ, 0 < a ∧ a ^ t = eSeed := by
  refine ⟨Real.exp (1 / t), Real.exp_pos _, ?_⟩
  rw [Real.rpow_def_of_pos (Real.exp_pos _), Real.log_exp, FitCapacity.eSeed]
  congr 1
  field_simp

end GLM.SeedRoles
