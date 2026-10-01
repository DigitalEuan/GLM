/-
# The wall, and what passes through it

The cardinal-geometry study's finding is that a finite construction holds only
finite information, so an irrational value is not reachable as a carrier.  That
is correct, and this file proves it in a form sharper than "finite": it is a
statement about *cardinality*, and it applies to every representation the
machine could ever adopt, not merely to the ones it has.

* `no_countable_layer_lossless` — **the wall.**  No layer whose views form a
  countable set separates all real targets.  Carriers are tuples of rationals,
  digit stacks are finite, trajectories of fixed length are finite: every one
  of these is a countable view space, so every one of them conflates
  uncountably many reals.  The wall is not an artefact of the GLM's design.
* `sqrt_two_not_carrier` — the concrete instance: no rational carrier
  coordinate is `√2`.

And then what passes through it.  A tower of countable layers is not itself a
countable layer, and that is the whole difference:

* `dyadicR_surrogate` — at each finite layer an irrational target is
  indistinguishable from a *rational* one.  Each level is therefore literally
  true of a rational stand-in: this is the study's "true up to a point".
* `dyadicR_surrogate_fails` — and every stand-in is exposed at some higher
  level.  No rational survives the whole tower: "then another level takes
  over".
* `dyadicR_surrogate_tendsto` — the stand-ins converge to the target, so
  nothing is lost by the ascent; the sequence *is* the value.
* `dyadicR_separates` and `towerView_injective` — the joint view of all levels
  at once is faithful on the reals, even though each level is not.  The
  uncountability of `ℕ → ℤ` is exactly the room the wall denies to any single
  layer.

`sqrt_two_delta_sigma` closes the circle with `DeltaSigma.lean`: the modulator
run on `√2 - 1` emits bits forever, its time averages are rational numbers
computed from finitely many of them, and they converge to a target no carrier
holds.
-/
import RequestProject.GLM.DeltaSigma

namespace GLM.Info

open Layer Filter Topology

/-! ## The wall: a cardinality theorem -/

/-- **No countable resolution separates the reals.**  If a layer's view space
is countable — a finite tuple of rationals, a digit stack of any fixed depth, a
trajectory of any fixed length — then it conflates two distinct real targets.
This is the cardinal-geometry study's wall, stated for every possible finite or
countable representation at once. -/
theorem no_countable_layer_lossless (L : Layer ℝ) [Countable L.View] :
    ¬ L.Lossless := by
  intro h
  have : Countable ℝ := Function.Injective.countable h
  exact (Cardinal.not_countable_real (by simpa using Set.countable_univ))

/-- The wall, in the form the study states it: for a countable view space there
are two distinct targets the layer cannot tell apart. -/
theorem exists_conflated_reals (L : Layer ℝ) [Countable L.View] :
    ∃ x y : ℝ, x ≠ y ∧ L.Indist x y := by
  by_contra hcon
  push_neg at hcon
  exact no_countable_layer_lossless L fun x y hxy => by
    by_contra hne
    exact hcon x y hne hxy

/-- No rational carrier coordinate is `√2`: the concrete instance of the wall
that the cardinal-geometry study exhibits. -/
theorem sqrt_two_not_carrier (q : ℚ) : (q : ℝ) ≠ Real.sqrt 2 := by
  intro h
  exact irrational_sqrt_two ⟨q, h⟩

/-! ## The dyadic tower over the reals -/

/-- Level `n` of the dyadic tower, now read on real targets rather than on
rational carriers: the target is seen to resolution `2⁻ⁿ`. -/
noncomputable def dyadicLayerR (n : ℕ) : Layer ℝ where
  View := ℤ
  perceive x := ⌊x * 2 ^ n⌋

@[simp] lemma dyadicLayerR_perceive (n : ℕ) (x : ℝ) :
    (dyadicLayerR n).perceive x = ⌊x * 2 ^ n⌋ := rfl

/-- Each level's view space is countable, so by `no_countable_layer_lossless`
no level of the tower is lossless. -/
theorem dyadicR_not_lossless (n : ℕ) : ¬ (dyadicLayerR n).Lossless := by
  haveI : Countable (dyadicLayerR n).View := inferInstanceAs (Countable ℤ)
  exact no_countable_layer_lossless (dyadicLayerR n)

lemma floorR_mul_two_pow_succ (x : ℝ) (n : ℕ) :
    ⌊x * 2 ^ n⌋ = ⌊x * 2 ^ (n + 1)⌋ / ((2 : ℕ) : ℤ) := by
  rw [← Int.floor_div_natCast (x * 2 ^ (n + 1)) 2]
  congr 1
  push_cast
  ring

/-- **The tower over `ℝ` is cumulative.**  Doubling the resolution never costs
a distinction. -/
theorem dyadicR_refines_succ (n : ℕ) :
    Refines (dyadicLayerR (n + 1)) (dyadicLayerR n) := by
  intro a b hab
  show ⌊a * 2 ^ n⌋ = ⌊b * 2 ^ n⌋
  rw [floorR_mul_two_pow_succ a n, floorR_mul_two_pow_succ b n]
  exact congrArg (· / ((2 : ℕ) : ℤ)) hab

theorem dyadicR_refines_of_le {m n : ℕ} (h : m ≤ n) :
    Refines (dyadicLayerR n) (dyadicLayerR m) := by
  induction n with
  | zero =>
      have : m = 0 := Nat.le_zero.1 h
      subst this
      exact refines_refl _
  | succ k ih =>
      rcases Nat.lt_or_ge m (k + 1) with hm | hm
      · exact Refines.trans (dyadicR_refines_succ k) (ih (Nat.lt_succ_iff.1 hm))
      · have : m = k + 1 := le_antisymm h hm
        subst this
        exact refines_refl _

/-- **Every distinction is eventually made**, now for arbitrary real targets:
distinct reals are separated at a finite level of the tower. -/
theorem dyadicR_separates {x y : ℝ} (h : x ≠ y) :
    ∃ n : ℕ, ¬ (dyadicLayerR n).Indist x y := by
  have key : ∀ {a b : ℝ}, a < b → ∃ n : ℕ, ¬ (dyadicLayerR n).Indist a b := by
    intro a b hab
    have hpos : (0 : ℝ) < b - a := sub_pos.mpr hab
    obtain ⟨n, hn⟩ : ∃ n : ℕ, (b - a)⁻¹ < 2 ^ n := pow_unbounded_of_one_lt _ (by norm_num)
    refine ⟨n, ?_⟩
    have h2 : (0 : ℝ) < 2 ^ n := by positivity
    have hgap : 1 < (b - a) * 2 ^ n := by
      rw [inv_lt_iff_one_lt_mul₀ hpos] at hn
      linarith
    have hkey : a * 2 ^ n + 1 ≤ b * 2 ^ n := by nlinarith
    have hfloor : ⌊a * 2 ^ n + 1⌋ ≤ ⌊b * 2 ^ n⌋ := Int.floor_le_floor hkey
    rw [Int.floor_add_one] at hfloor
    show ¬ (⌊a * 2 ^ n⌋ = ⌊b * 2 ^ n⌋)
    omega
  rcases lt_or_gt_of_ne h with hlt | hlt
  · exact key hlt
  · obtain ⟨n, hn⟩ := key hlt
    exact ⟨n, fun hc => hn (indist_symm hc)⟩

/-! ## Each level is true of a rational stand-in -/

/-- The rational stand-in for a target at level `n`: the target rounded down to
resolution `2⁻ⁿ`. -/
noncomputable def surrogate (x : ℝ) (n : ℕ) : ℚ := (⌊x * 2 ^ n⌋ : ℚ) / 2 ^ n

/-- **At every finite level, an irrational target is indistinguishable from a
rational one.**  Each layer's whole account of the target is an account of a
carrier it can actually hold: this is the exact sense in which a level is
"true within its own reach", even about a value it cannot represent. -/
theorem dyadicR_surrogate (x : ℝ) (n : ℕ) :
    (dyadicLayerR n).Indist x ((surrogate x n : ℚ) : ℝ) := by
  have h2 : ((2 : ℝ) ^ n) ≠ 0 := by positivity
  show ⌊x * 2 ^ n⌋ = ⌊((surrogate x n : ℚ) : ℝ) * 2 ^ n⌋
  have : ((surrogate x n : ℚ) : ℝ) * 2 ^ n = (⌊x * 2 ^ n⌋ : ℝ) := by
    unfold surrogate
    push_cast
    field_simp
  rw [this, Int.floor_intCast]

/-- **Every stand-in is eventually exposed.**  For an irrational target, each
rational surrogate — indeed every rational whatsoever — is separated from the
target at some higher level.  No carrier is true of it all the way up. -/
theorem dyadicR_surrogate_fails {x : ℝ} (hx : Irrational x) (q : ℚ) :
    ∃ n : ℕ, ¬ (dyadicLayerR n).Indist x ((q : ℚ) : ℝ) :=
  dyadicR_separates fun h => hx ⟨q, h.symm⟩

/-- The stand-ins are within `2⁻ⁿ` of the target. -/
theorem surrogate_dist_lt (x : ℝ) (n : ℕ) :
    |x - ((surrogate x n : ℚ) : ℝ)| < (2 : ℝ) ^ (-(n : ℤ)) := by
  have hc : (0 : ℝ) < 2 ^ n := by positivity
  have hfl' := Int.floor_le (x * 2 ^ n)
  have hfl := Int.lt_floor_add_one (x * 2 ^ n)
  have hval : ((surrogate x n : ℚ) : ℝ) = (⌊x * 2 ^ n⌋ : ℝ) / 2 ^ n := by
    unfold surrogate
    push_cast
    ring
  have hz : (2 : ℝ) ^ (-(n : ℤ)) = 1 / 2 ^ n := by
    rw [zpow_neg, zpow_natCast, one_div]
  have e : x - (⌊x * 2 ^ n⌋ : ℝ) / 2 ^ n
      = (x * 2 ^ n - (⌊x * 2 ^ n⌋ : ℝ)) / 2 ^ n := by
    field_simp
  rw [hval, hz, e, abs_div, abs_of_pos hc, div_lt_div_iff_of_pos_right hc, abs_lt]
  constructor <;> linarith

/-- **The stand-ins converge to the target.**  The ascent loses nothing: the
sequence of rational carriers, none of which is the target, has the target as
its limit.  The value lives in the tower, not in any of its floors. -/
theorem dyadicR_surrogate_tendsto (x : ℝ) :
    Tendsto (fun n : ℕ => ((surrogate x n : ℚ) : ℝ)) atTop (𝓝 x) := by
  have hbound : ∀ n : ℕ, ‖((surrogate x n : ℚ) : ℝ) - x‖ ≤ (1 / 2 : ℝ) ^ n := by
    intro n
    have h := surrogate_dist_lt x n
    have : (2 : ℝ) ^ (-(n : ℤ)) = (1 / 2 : ℝ) ^ n := by
      rw [zpow_neg, zpow_natCast]
      simp [one_div, inv_pow]
    rw [this] at h
    rw [Real.norm_eq_abs, abs_sub_comm]
    exact le_of_lt h
  have h0 : Tendsto (fun n : ℕ => (1 / 2 : ℝ) ^ n) atTop (𝓝 0) :=
    tendsto_pow_atTop_nhds_zero_of_lt_one (by norm_num) (by norm_num)
  have hdiff : Tendsto (fun n : ℕ => ((surrogate x n : ℚ) : ℝ) - x) atTop (𝓝 0) :=
    squeeze_zero_norm hbound h0
  have := hdiff.add (tendsto_const_nhds : Tendsto (fun _ : ℕ => x) atTop (𝓝 x))
  simpa using this

/-! ## The tower as a whole is faithful -/

/-- The joint view: what all levels of the tower say about a target, taken
together.  Its codomain `ℕ → ℤ` is uncountable, which is exactly the room a
single countable layer does not have. -/
noncomputable def towerView (x : ℝ) : ℕ → ℤ := fun n => (dyadicLayerR n).perceive x

/-- **The tower is lossless even though no floor of it is.**  Two targets seen
identically at every level are the same target: the infinite stack of finite
resolutions is a faithful representation of a real number. -/
theorem towerView_injective : Function.Injective towerView := by
  intro x y h
  by_contra hne
  obtain ⟨n, hn⟩ := dyadicR_separates hne
  exact hn (congrFun h n)

/-! ## √2, reached -/

/-- `√2 - 1` is a legitimate delta-sigma target. -/
lemma sqrt_two_sub_one_mem : 0 ≤ Real.sqrt 2 - 1 ∧ Real.sqrt 2 - 1 < 1 := by
  have h1 : (1 : ℝ) ≤ Real.sqrt 2 := by
    have h := Real.sqrt_le_sqrt (show (1:ℝ) ≤ 2 by norm_num)
    rwa [Real.sqrt_one] at h
  have h2 : Real.sqrt 2 < 2 := by
    have : Real.sqrt 2 < Real.sqrt 4 := by
      apply Real.sqrt_lt_sqrt <;> norm_num
    have h4 : Real.sqrt 4 = 2 := by
      rw [show (4 : ℝ) = 2 ^ 2 by norm_num, Real.sqrt_sq (by norm_num)]
    linarith [this, h4.le, h4.ge]
  exact ⟨by linarith, by linarith⟩

/-- **A value no carrier holds, reached by carriers.**  The modulator run on
`√2 - 1` produces, after `N` ticks, a rational average `k/N`; those averages
converge to `√2 - 1`, which is irrational and therefore not any of them.  The
target is never stored and always approached: the infinite is in the process,
not in the state. -/
theorem sqrt_two_delta_sigma :
    Tendsto (fun N => dsAverage (Real.sqrt 2 - 1) N) atTop (𝓝 (Real.sqrt 2 - 1)) ∧
    (∀ N : ℕ, ∃ k : ℕ, k ≤ N ∧ dsAverage (Real.sqrt 2 - 1) N = (k : ℝ) / N) ∧
    (∀ q : ℚ, (q : ℝ) ≠ Real.sqrt 2 - 1) := by
  obtain ⟨h0, h1⟩ := sqrt_two_sub_one_mem
  refine ⟨dsAverage_tendsto h0 h1, fun N => dsAverage_eq_div _ N, fun q hq => ?_⟩
  exact irrational_sqrt_two ⟨q + 1, by push_cast; linarith⟩

end GLM.Info
