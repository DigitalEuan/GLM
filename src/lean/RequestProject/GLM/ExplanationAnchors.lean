module

public import Mathlib

/-!
# What the explanation answers rest on (Phase 120, track E)

`studies/EXPLANATION_ANCHOR_STUDY.md` answers the outside questions that ask
*why* -- the Elements, nuclear physics, logic, and five engineering
questions -- with the part a register or an exact derivation decides, and
refuses the account.  This file proves the mathematical facts those answers
rest on, so that each derived part is a theorem rather than prose.

* **A series RLC circuit above resonance** (outside question 0):
  `reactance_pos_above_resonance` -- for `ω² L C > 1` the reactance
  `ω L - 1/(ω C)` is positive, so the circuit is inductive;
  `impedance_sq_strictMonoOn` -- on the frequencies above resonance the squared
  impedance `R² + X(ω)²` is strictly increasing.
* **A filtered derivative** (outside question 32):
  `filtered_derivative_gain_lt` -- `|K j ω / (1 + j ω τ)|² < K²/τ²` for every
  `ω`: the filter bounds the high-frequency gain by `K/τ`, where a pure
  derivative's gain `K ω` is unbounded.
* **Two nucleons in an s-wave** (outside question 70):
  `nucleon_pair_channels` -- antisymmetry `(-1)^(L+S+T) = -1` with `L = 0`
  leaves exactly `(S, T) = (1, 0)` and `(0, 1)`; `identical_pair_singlet` --
  two protons or two neutrons (`T = 1`) are therefore in the spin singlet.
* **Intuitionistic logic** (outside question 83): in the three-element
  Heyting chain the middle element `a` has `a ⊔ aᶜ ≠ ⊤` (`chain_em_fails`) and
  `aᶜᶜ ⇨ a ≠ ⊤` (`chain_dne_fails`), while `(a ⊔ aᶜ)ᶜᶜ = ⊤`
  (`chain_nn_em`).
* **Strict implication** (outside question 80): `strict_implication_fails` --
  a two-world model in which `P → Q` holds materially at the actual world
  (its antecedent is false there) while `□(P → Q)` fails.
* **Probability is not truth-functional** (outside question 87):
  `frechet_lower` -- `μ A + μ B ≤ 1 + μ (A ∩ B)` for a probability measure;
  `not_truth_functional` -- two distributions with the same marginals `7/10`
  and different probabilities of the conjunction (`7/10` and `2/5`).
* **An inconsistent theory proves everything** (outside question 88):
  `inconsistent_proves_all` -- a first-order theory with no model entails every
  formula, a consistency statement included.
* **The Skolem paradox** (outside question 84):
  `countable_elementary_substructure` -- every infinite structure in a
  countable language has a countable elementary substructure (downward
  Löwenheim--Skolem, from Mathlib).
* **Real roots are not rational roots** (outside question 96):
  `real_root_no_rational_root` -- `x² = 2` has a real solution and no rational
  one, so a decision over the reals does not transfer to `ℚ`.
* **A constrained predictive-control step** (outside question 39):
  `mpc_instance_optimal` -- for the integrator `y⁺ = y + u`, horizon 2,
  reference 3 and `|u| ≤ 2`, the move pair `(2, 1)` minimises
  `(y₁ - 3)² + (y₂ - 3)²`, with value 1, while clipping the unconstrained
  optimum `(3, 0)` gives `(2, 0)` with value 2 (`mpc_clipped_worse`).
* **Two register certificates** (outside questions 73 and 65):
  `be8_unbound` -- from the AME2020 mass excesses, `Δ(⁸Be) - 2 Δ(⁴He) =
  91.84026 keV > 0`; `technetium_unstable` -- each of the 28 technetium
  isotopes with a measured AME2020 mass is heavier than its molybdenum or its
  ruthenium isobar, so each can decay.
-/

@[expose] public section

namespace GLM.ExplanationAnchors

/-! ## A series RLC circuit -/

/-- The reactance of a series RLC circuit. -/
noncomputable def reactance (L C ω : ℝ) : ℝ := ω * L - 1 / (ω * C)

/-- Above resonance (`ω² L C > 1`) the reactance is positive: inductive. -/
theorem reactance_pos_above_resonance {L C ω : ℝ} (hC : 0 < C)
    (hω : 0 < ω) (habove : 1 < ω ^ 2 * (L * C)) : 0 < reactance L C ω := by
  unfold reactance
  have hωC : 0 < ω * C := mul_pos hω hC
  rw [sub_pos, div_lt_iff₀ hωC]
  nlinarith

/-- The reactance is strictly increasing in `ω > 0`. -/
theorem reactance_strictMonoOn {L C : ℝ} (hL : 0 < L) (hC : 0 < C) :
    StrictMonoOn (reactance L C) (Set.Ioi 0) := by
  intro a ha b hb hab
  simp only [Set.mem_Ioi] at ha hb
  unfold reactance
  have h1 : a * L < b * L := mul_lt_mul_of_pos_right hab hL
  have h2 : 1 / (b * C) < 1 / (a * C) :=
    one_div_lt_one_div_of_lt (mul_pos ha hC) (mul_lt_mul_of_pos_right hab hC)
  linarith

/-- Above resonance the squared impedance `R² + X²` strictly increases. -/
theorem impedance_sq_strictMonoOn {R L C : ℝ} (hL : 0 < L) (hC : 0 < C) :
    StrictMonoOn (fun ω => R ^ 2 + reactance L C ω ^ 2)
      {ω | 0 < ω ∧ 1 < ω ^ 2 * (L * C)} := by
  intro a ha b hb hab
  have hXa := reactance_pos_above_resonance hC ha.1 ha.2
  have hX := reactance_strictMonoOn hL hC (show a ∈ Set.Ioi 0 from ha.1)
    (show b ∈ Set.Ioi 0 from hb.1) hab
  have : reactance L C a ^ 2 < reactance L C b ^ 2 := by nlinarith
  simpa using this

/-! ## A filtered derivative -/

/-- The squared gain of `K s / (1 + τ s)` at `s = jω` is below `K²/τ²`. -/
theorem filtered_derivative_gain_lt {K τ : ℝ} (ω : ℝ) (hK : K ≠ 0)
    (hτ : 0 < τ) : K ^ 2 * ω ^ 2 / (1 + ω ^ 2 * τ ^ 2) < K ^ 2 / τ ^ 2 := by
  have hK2 : 0 < K ^ 2 := by positivity
  have hd : 0 < 1 + ω ^ 2 * τ ^ 2 := by positivity
  rw [div_lt_div_iff₀ hd (by positivity)]
  nlinarith

/-- A pure derivative's gain `K ω` exceeds every bound. -/
theorem pure_derivative_unbounded {K : ℝ} (hK : 0 < K) (M : ℝ) :
    ∃ ω : ℝ, M < K * ω :=
  ⟨M / K + 1, by rw [mul_add, mul_div_cancel₀ _ hK.ne']; linarith⟩

/-! ## Two nucleons in an s-wave -/

/-- With `L = 0`, antisymmetry `(-1)^(L+S+T) = -1` (odd `S + T`) leaves
exactly the channels `(S, T) = (1, 0)` (the deuteron's) and `(0, 1)`. -/
theorem nucleon_pair_channels (S T : Fin 2) :
    (0 + S.val + T.val) % 2 = 1 ↔ (S = 1 ∧ T = 0) ∨ (S = 0 ∧ T = 1) := by
  revert S T; decide

/-- Two protons or two neutrons have isospin `T = 1`, so an s-wave pair of
them is a spin singlet `S = 0`: the spin-triplet channel that binds the
deuteron is closed to them. -/
theorem identical_pair_singlet (S : Fin 2) (h : (0 + S.val + 1) % 2 = 1) :
    S = 0 := by
  revert S; decide

/-! ## Intuitionistic logic: the three-element Heyting chain -/

/-- Excluded middle fails at the middle of the chain. -/
theorem chain_em_fails : (1 : Fin 3) ⊔ (1 : Fin 3)ᶜ ≠ ⊤ := by decide

/-- Double-negation elimination fails at the middle of the chain. -/
theorem chain_dne_fails : (1 : Fin 3)ᶜᶜ ⇨ (1 : Fin 3) ≠ ⊤ := by decide

/-- The double negation of excluded middle holds at every element. -/
theorem chain_nn_em (a : Fin 3) : (a ⊔ aᶜ)ᶜᶜ = ⊤ := by revert a; decide

/-! ## Material against strict implication -/

/-- Two worlds, each seeing both.  At world `0`, `P` is false, so `P → Q`
holds materially; at world `1`, `P` is true and `Q` false, so the strict
implication `□(P → Q)` (true at every accessible world) fails. -/
theorem strict_implication_fails :
    ∃ P Q : Fin 2 → Prop, (P 0 → Q 0) ∧ ¬ (∀ w, P w → Q w) :=
  ⟨fun w => w = 1, fun _ => False, by simp, fun h => h 1 rfl⟩

/-! ## Probability is not truth-functional -/

/-- Fréchet's lower bound: `P(A ∩ B) ≥ P(A) + P(B) - 1`. -/
theorem frechet_lower {α : Type*} [MeasurableSpace α]
    (μ : MeasureTheory.Measure α) [MeasureTheory.IsProbabilityMeasure μ]
    (A : Set α) {B : Set α} (hB : MeasurableSet B) :
    μ A + μ B ≤ 1 + μ (A ∩ B) := by
  rw [← MeasureTheory.measure_union_add_inter A hB]
  gcongr
  exact MeasureTheory.prob_le_one

/-- The four cells `A∧B, A∧¬B, ¬A∧B, ¬A∧¬B` of a distribution. -/
def pA (p : Fin 4 → ℚ) : ℚ := p 0 + p 1
def pB (p : Fin 4 → ℚ) : ℚ := p 0 + p 2
def pAB (p : Fin 4 → ℚ) : ℚ := p 0

/-- Two distributions with `P(A) = P(B) = 7/10` and different
`P(A ∧ B)`: `7/10` and `2/5`, the two ends of the Fréchet interval. -/
theorem not_truth_functional :
    ∃ p q : Fin 4 → ℚ, (∀ i, 0 ≤ p i) ∧ (∀ i, 0 ≤ q i) ∧
      (∑ i, p i = 1) ∧ (∑ i, q i = 1) ∧
      pA p = 7 / 10 ∧ pB p = 7 / 10 ∧ pA q = 7 / 10 ∧ pB q = 7 / 10 ∧
      pAB p = 7 / 10 ∧ pAB q = 2 / 5 := by
  refine ⟨![7/10, 0, 0, 3/10], ![2/5, 3/10, 3/10, 0], ?_, ?_, ?_, ?_, ?_, ?_,
    ?_, ?_, ?_, ?_⟩ <;>
  simp [pA, pB, pAB, Fin.forall_fin_succ, Fin.sum_univ_succ] <;> norm_num

/-! ## An inconsistent theory entails everything -/

/-- A first-order theory with no model entails every formula -- in
particular any sentence one reads as its own consistency. -/
theorem inconsistent_proves_all {L : FirstOrder.Language} (T : L.Theory)
    (h : ¬ T.IsSatisfiable) (φ : L.Sentence) : T ⊨ᵇ φ :=
  FirstOrder.Language.Theory.models_iff_not_satisfiable φ |>.2 fun hs =>
    h (hs.mono Set.subset_union_left)

/-! ## The Skolem paradox -/

/-- Downward Löwenheim--Skolem in the form the paradox needs: an infinite
structure in a countable language has a countable elementary substructure. -/
theorem countable_elementary_substructure (L : FirstOrder.Language.{0, 0})
    {M : Type} [L.Structure M] [Infinite M]
    (hL : L.card ≤ Cardinal.aleph0) :
    ∃ S : L.ElementarySubstructure M, Cardinal.mk S = Cardinal.aleph0 := by
  haveI : Nonempty M := inferInstance
  obtain ⟨S, -, hS⟩ := FirstOrder.Language.exists_elementarySubstructure_card_eq
    L (∅ : Set M) (Cardinal.aleph0 : Cardinal.{0}) le_rfl (by simp)
    (by simpa using hL)
    (by simp [Cardinal.aleph0_le_mk M])
  exact ⟨S, by simpa using hS⟩

/-! ## A real root that is not rational -/

/-- `x² = 2` is solvable over `ℝ` and not over `ℚ`. -/
theorem real_root_no_rational_root :
    (∃ x : ℝ, x ^ 2 = 2) ∧ ¬ ∃ q : ℚ, q ^ 2 = 2 := by
  refine ⟨⟨Real.sqrt 2, Real.sq_sqrt (by norm_num)⟩, ?_⟩
  rintro ⟨q, hq⟩
  apply irrational_sqrt_two
  refine ⟨|q|, ?_⟩
  rw [Rat.cast_abs, ← Real.sqrt_sq_eq_abs]
  congr 1
  exact_mod_cast hq

/-! ## A constrained predictive-control step -/

/-- The cost of the move pair `(u₀, u₁)` for `y⁺ = y + u` from `y = 0`,
reference 3, horizon 2. -/
def mpcCost (u₀ u₁ : ℚ) : ℚ := (u₀ - 3) ^ 2 + (u₀ + u₁ - 3) ^ 2

/-- With `u₀ ≤ 2` (so in particular under `|u| ≤ 2`), `(2, 1)` is optimal,
with cost 1; `(2, 1)` itself satisfies `|u| ≤ 2`. -/
theorem mpc_instance_optimal (u₀ u₁ : ℚ) (h0 : u₀ ≤ 2) :
    mpcCost 2 1 ≤ mpcCost u₀ u₁ := by
  unfold mpcCost
  nlinarith [sq_nonneg (u₀ + u₁ - 3)]

/-- Clipping the unconstrained optimum `(3, 0)` to `(2, 0)` costs 2. -/
theorem mpc_clipped_worse : mpcCost 2 1 = 1 ∧ mpcCost 2 0 = 2 ∧
    mpcCost 3 0 = 0 := by
  unfold mpcCost; norm_num

/-! ## Register certificates -/

/-- `Q(⁸Be → 2α)` from the AME2020 mass excesses (keV): positive, so the
ground state of beryllium-8 lies above two alpha particles. -/
theorem be8_unbound :
    (4941672 / 1000 : ℚ) - 2 * (242491587 / 100000) = 9184026 / 100000 ∧
      (0 : ℚ) < 4941672 / 1000 - 2 * (242491587 / 100000) := by
  norm_num

/-- `(A, Δ(Mo), Δ(Tc), Δ(Ru))` in keV, AME2020, for every technetium isotope
whose mass the table measured. -/
def technetiumTable : List (ℕ × ℚ × ℚ × ℚ) := [
  (87, (-66884817/1000 : ℚ), (-14422513/250 : ℚ), (-45730 : ℚ)),
  (88, (-72686553/1000 : ℚ), (-61670301/1000 : ℚ), (-54340 : ℚ)),
  (89, (-9376868/125 : ℚ), (-67394857/1000 : ℚ), (-7296178/125 : ℚ)),
  (90, (-40086257/500 : ℚ), (-8840587/125 : ℚ), (-64883801/1000 : ℚ)),
  (91, (-41104417/500 : ℚ), (-75986657/1000 : ℚ), (-68239833/1000 : ℚ)),
  (92, (-86808587/1000 : ℚ), (-78925703/1000 : ℚ), (-74301211/1000 : ℚ)),
  (93, (-86807079/1000 : ℚ), (-20901529/250 : ℚ), (-77216723/1000 : ℚ)),
  (94, (-88414079/1000 : ℚ), (-21039583/250 : ℚ), (-41291801/500 : ℚ)),
  (95, (-10963984/125 : ℚ), (-17204271/200 : ℚ), (-83457759/1000 : ℚ)),
  (96, (-88794889/1000 : ℚ), (-10727706/125 : ℚ), (-17216077/200 : ℚ)),
  (97, (-875447/10 : ℚ), (-21806109/250 : ℚ), (-21530141/250 : ℚ)),
  (98, (-4405799/50 : ℚ), (-43216107/500 : ℚ), (-88224871/1000 : ℚ)),
  (99, (-42985053/500 : ℚ), (-87327869/1000 : ℚ), (-17525077/200 : ℚ)),
  (100, (-86193029/1000 : ℚ), (-86020951/1000 : ℚ), (-89227391/1000 : ℚ)),
  (101, (-10439994/125 : ℚ), (-86344593/1000 : ℚ), (-87958113/1000 : ℚ)),
  (102, (-41780433/500 : ℚ), (-84572921/1000 : ℚ), (-17821287/200 : ℚ)),
  (103, (-80954331/1000 : ℚ), (-2115098/25 : ℚ), (-10908396/125 : ℚ)),
  (104, (-20085937/250 : ℚ), (-82498969/1000 : ℚ), (-88095763/1000 : ℚ)),
  (105, (-19332697/250 : ℚ), (-82286303/1000 : ℚ), (-85934543/1000 : ℚ)),
  (106, (-76128003/1000 : ℚ), (-79776253/1000 : ℚ), (-86323253/1000 : ℚ)),
  (107, (-2901799/40 : ℚ), (-78749967/1000 : ℚ), (-16772513/200 : ℚ)),
  (108, (-70749297/1000 : ℚ), (-75922831/1000 : ℚ), (-20915351/250 : ℚ)),
  (109, (-13331857/200 : ℚ), (-18570707/250 : ℚ), (-16147691/200 : ℚ)),
  (110, (-32267907/500 : ℚ), (-17758641/250 : ℚ), (-80072629/1000 : ℚ)),
  (111, (-59939813/1000 : ℚ), (-2760987/40 : ℚ), (-3071413/40 : ℚ)),
  (112, (-57480 : ℚ), (-16314733/250 : ℚ), (-75630873/1000 : ℚ)),
  (113, (-52650 : ℚ), (-62811549/1000 : ℚ), (-8983477/125 : ℚ)),
  (114, (-49680 : ℚ), (-29300147/500 : ℚ), (-70221213/1000 : ℚ))
]

/-- Each technetium isotope with a measured mass is heavier than its
molybdenum isobar (it can capture an electron) or its ruthenium isobar (it
can beta-decay). -/
theorem technetium_unstable :
    ∀ r ∈ technetiumTable, r.2.1 < r.2.2.1 ∨ r.2.2.2 < r.2.2.1 := by
  simp only [technetiumTable, List.forall_mem_cons, List.not_mem_nil,
    IsEmpty.forall_iff, implies_true, and_true]
  norm_num

theorem technetiumTable_length : technetiumTable.length = 28 := rfl

end GLM.ExplanationAnchors
