module

public import Mathlib

/-!
# Substrate-native cognition: what the supplied concepts can and cannot do

The formal half of `studies/SUBSTRATE_NATIVE_COGNITION_STUDY.md`. The supplied
list (`source_material/substrate_native_cognitive_1.txt`) proposes concepts
meant to make the substrate *generate* reasoning. The study runs each concept
as an experiment. This file proves the statements those experiments lean on,
so that a verdict rests on a theorem wherever one is available.

* **The deep-hole fork never answers wrongly** (`fork_answer_correct`). If the
  truth lies in each of two candidate sets and their intersection is a single
  point, that point is the truth.
* **One dyadic tower is not distance-faithful, two offset towers are.**
  `one_tower_not_faithful`: points arbitrarily close can share no cell at any
  level. `two_towers` and `two_towers_level`: points closer than
  `1 / (3 · 2 ^ n)` share a level-`n` cell in the plain tower or in the tower
  shifted by `1/3`.
* **A lattice-periodic loss cannot tell a point from its translate.**
  `infDist_translate`: the distance to an additive subgroup is unchanged by
  translation by one of its elements, and `periodic_argmin_translate`:
  translating a minimiser of such a loss gives another minimiser. The
  engine's `TAX = d²/32` is of this kind.
* **The two reversible gates never change the control bit**
  (`applyWord_control`), and they fix a triple whose control bit is clear
  (`gates_fix_of_control_clear`). That is the impossibility certificate of
  experiment X4.
* **Disjoint intervals decide an order, overlapping ones cannot**
  (`interval_lt_sound`, `interval_overlap_undecided`).
* **The certificates of experiment X7 are sound.**
  `bezout_certificate_sound`: a checked Bézout triple names the gcd.
  `no_solution_of_not_dvd`: a gcd that does not divide the right-hand side
  excludes every integer pair. `linear_solutions_complete`: the family
  returned is every solution.
* **The Weyl vector `(0, 1, …, 24 | 70)` of `II₂₅,₁` is null**
  (`weyl_vector_null`).
-/

@[expose] public section

namespace GLM.SubstrateCognition

/-! ## X1 — the deep-hole fork -/

/-- If the truth lies in both forks and the forks share exactly one point,
that point is the truth: intersecting two forks never answers wrongly. -/
theorem fork_answer_correct {α : Type*} (truth a : α) (F G : Set α)
    (hF : truth ∈ F) (hG : truth ∈ G) (h : F ∩ G = {a}) : a = truth := by
  have : truth ∈ F ∩ G := ⟨hF, hG⟩
  rw [h] at this
  exact this.symm

/-! ## X2 — dyadic abstraction -/

/-- Points arbitrarily close together can share no dyadic cell at any level,
so a single tower is not a distance-faithful abstraction. -/
theorem one_tower_not_faithful (ε : ℚ) (hε : 0 < ε) :
    ∃ x y : ℚ, |x - y| < ε ∧ ∀ n : ℕ, ⌊x * 2 ^ n⌋ ≠ ⌊y * 2 ^ n⌋ := by
  refine ⟨-(ε / 2), 0, ?_, ?_⟩
  · rw [abs_lt]; constructor <;> linarith
  · intro n h
    have h2 : (0 : ℚ) < 2 ^ n := by positivity
    have hx : -(ε / 2) * 2 ^ n < 0 := by nlinarith
    have hneg : ⌊-(ε / 2) * 2 ^ n⌋ < 0 := Int.floor_lt.2 (by simpa using hx)
    have h0 : ⌊(0 : ℚ) * 2 ^ n⌋ = 0 := by simp
    rw [h0] at h
    omega

/-- Two points closer than `1/3` share a unit cell of the plain grid or of
the grid shifted by `1/3`. -/
theorem two_towers (x y : ℚ) (h : |x - y| < 1 / 3) :
    ⌊x⌋ = ⌊y⌋ ∨ ⌊x + 1 / 3⌋ = ⌊y + 1 / 3⌋ := by
  wlog hxy : x ≤ y generalizing x y
  · rcases this y x (by rwa [abs_sub_comm]) (by linarith) with h1 | h1
    · exact Or.inl h1.symm
    · exact Or.inr h1.symm
  by_cases hf : ⌊x⌋ = ⌊y⌋
  · exact Or.inl hf
  right
  have hlt : ⌊x⌋ < ⌊y⌋ := lt_of_le_of_ne (Int.floor_mono hxy) hf
  have hk : x < (⌊y⌋ : ℚ) := by
    have := Int.lt_floor_add_one x
    have : (⌊x⌋ : ℚ) + 1 ≤ ⌊y⌋ := by exact_mod_cast hlt
    linarith
  have hky : (⌊y⌋ : ℚ) ≤ y := Int.floor_le y
  have habs := abs_lt.1 h
  have e1 : ⌊x + 1 / 3⌋ = ⌊y⌋ := by
    rw [Int.floor_eq_iff]; constructor <;> linarith [habs.1, habs.2]
  have e2 : ⌊y + 1 / 3⌋ = ⌊y⌋ := by
    rw [Int.floor_eq_iff]; constructor <;> linarith [habs.1, habs.2]
  rw [e1, e2]

/-- The same at every level: points closer than `1 / (3 · 2 ^ n)` share a
level-`n` cell in one of the two towers. -/
theorem two_towers_level (n : ℕ) (x y : ℚ) (h : |x - y| < 1 / (3 * 2 ^ n)) :
    ⌊x * 2 ^ n⌋ = ⌊y * 2 ^ n⌋ ∨ ⌊x * 2 ^ n + 1 / 3⌋ = ⌊y * 2 ^ n + 1 / 3⌋ := by
  apply two_towers
  have h2 : (0 : ℚ) < 2 ^ n := by positivity
  rw [← sub_mul, abs_mul, abs_of_pos h2]
  rw [lt_div_iff₀ (by positivity)] at h
  nlinarith

/-! ## X3 — TAX as a loss -/

/-- The distance to an additive subgroup does not change under translation by
one of its elements. The engine's strain `TAX = d²/32`, with `d` the distance
to the Leech lattice, is therefore the same at a point and at every lattice
translate of it. -/
theorem infDist_translate {E : Type*} [SeminormedAddCommGroup E] (Λ : AddSubgroup E)
    (v l : E) (hl : l ∈ Λ) :
    Metric.infDist (v + l) (Λ : Set E) = Metric.infDist v (Λ : Set E) := by
  have himg : (fun y => y + l) '' (Λ : Set E) = (Λ : Set E) := by
    ext y
    constructor
    · rintro ⟨z, hz, rfl⟩; exact Λ.add_mem hz hl
    · intro hy; exact ⟨y - l, Λ.sub_mem hy hl, by simp⟩
  have := Metric.infDist_image (Φ := fun y : E => y + l) (isometry_add_right l) (x := v)
    (t := (Λ : Set E))
  rw [himg] at this
  exact this

/-- A loss that is periodic under a subgroup has its minimisers in whole
cosets: translating a minimiser gives another minimiser, so minimising such a
loss cannot pick one lattice point over another. -/
theorem periodic_argmin_translate {V : Type*} [AddGroup V] (L : V → ℚ)
    (Λ : AddSubgroup V) (hL : ∀ v, ∀ l ∈ Λ, L (v + l) = L v)
    (v : V) (hv : ∀ w, L v ≤ L w) (l : V) (hl : l ∈ Λ) : ∀ w, L (v + l) ≤ L w := by
  intro w
  rw [hL v l hl]
  exact hv w

/-! ## X4 — reversible gates and the impossibility certificate -/

/-- Toffoli on one triple: flip the third bit when the first two are set. -/
def toffoli3 : Bool × Bool × Bool → Bool × Bool × Bool
  | (a, b, c) => (a, b, xor c (a && b))

/-- Fredkin on one triple: swap the last two bits when the first is set. -/
def fredkin3 : Bool × Bool × Bool → Bool × Bool × Bool
  | (a, b, c) => if a then (a, c, b) else (a, b, c)

/-- A word of gates, `true` for Toffoli and `false` for Fredkin, applied left
to right. -/
def applyWord : List Bool → Bool × Bool × Bool → Bool × Bool × Bool
  | [], x => x
  | g :: w, x => applyWord w (if g then toffoli3 x else fredkin3 x)

/-- Both gates fix a triple whose control bit is clear. -/
theorem gates_fix_of_control_clear (x : Bool × Bool × Bool) (h : x.1 = false) :
    toffoli3 x = x ∧ fredkin3 x = x := by
  obtain ⟨a, b, c⟩ := x
  simp at h
  subst h
  simp [toffoli3, fredkin3]

/-- No word of the two gates changes the control bit. So a target that
differs from the source in a control bit is unreachable, whatever the search
depth: the certificate of experiment X4. -/
theorem applyWord_control (w : List Bool) (x : Bool × Bool × Bool) :
    (applyWord w x).1 = x.1 := by
  induction w generalizing x with
  | nil => rfl
  | cons g w ih =>
    simp only [applyWord]
    rw [ih]
    obtain ⟨a, b, c⟩ := x
    cases g <;> cases a <;> simp [toffoli3, fredkin3]

/-! ## X6 — rational intervals -/

/-- Disjoint intervals decide the order of every pair of values they allow. -/
theorem interval_lt_sound (lo₁ hi₁ lo₂ hi₂ a b : ℚ) (ha : lo₁ ≤ a ∧ a ≤ hi₁)
    (hb : lo₂ ≤ b ∧ b ≤ hi₂) (h : hi₁ < lo₂) : a < b := by
  linarith [ha.2, hb.1]

/-- Overlapping intervals allow both orders, so a comparison between them
must refuse. -/
theorem interval_overlap_undecided (lo₁ hi₁ lo₂ hi₂ : ℚ) (h₁ : lo₁ < hi₂)
    (h₂ : lo₂ < hi₁) (w₁ : lo₁ ≤ hi₁) (w₂ : lo₂ ≤ hi₂) :
    (∃ a b, lo₁ ≤ a ∧ a ≤ hi₁ ∧ lo₂ ≤ b ∧ b ≤ hi₂ ∧ a < b) ∧
    (∃ a b, lo₁ ≤ a ∧ a ≤ hi₁ ∧ lo₂ ≤ b ∧ b ≤ hi₂ ∧ b < a) :=
  ⟨⟨lo₁, hi₂, le_rfl, w₁, w₂, le_rfl, h₁⟩, ⟨hi₁, lo₂, w₁, le_rfl, le_rfl, w₂, h₂⟩⟩

/-! ## X7 — certificates for absent derivations -/

/-- A Bézout triple that passes the check (`a x + b y = g`, `g ∣ a`, `g ∣ b`)
names the greatest common divisor. -/
theorem bezout_certificate_sound (a b x y : ℤ) (g : ℕ) (h : a * x + b * y = g)
    (ha : (g : ℤ) ∣ a) (hb : (g : ℤ) ∣ b) : g = Int.gcd a b := by
  apply Nat.dvd_antisymm
  · exact Int.dvd_gcd ha hb
  · have : (Int.gcd a b : ℤ) ∣ a * x + b * y :=
      dvd_add (dvd_mul_of_dvd_left (Int.gcd_dvd_left a b) _)
        (dvd_mul_of_dvd_left (Int.gcd_dvd_right a b) _)
    rw [h] at this
    exact_mod_cast this

/-- The impossibility certificate: if `gcd a b` does not divide `c`, no pair
of integers solves `a x + b y = c`. -/
theorem no_solution_of_not_dvd (a b c : ℤ) (h : ¬ (Int.gcd a b : ℤ) ∣ c) :
    ¬ ∃ x y, a * x + b * y = c := by
  rintro ⟨x, y, hxy⟩
  apply h
  rw [← hxy]
  exact dvd_add (dvd_mul_of_dvd_left (Int.gcd_dvd_left a b) _)
    (dvd_mul_of_dvd_left (Int.gcd_dvd_right a b) _)

/-- Completeness of the family: once one solution `(x₀, y₀)` is known, every
solution is `(x₀ + (b/g) k, y₀ - (a/g) k)` for some integer `k`. -/
theorem linear_solutions_complete (a b c x₀ y₀ x y : ℤ) (hg : Int.gcd a b ≠ 0)
    (h₀ : a * x₀ + b * y₀ = c) (h : a * x + b * y = c) :
    ∃ k : ℤ, x = x₀ + (b / Int.gcd a b) * k ∧ y = y₀ - (a / Int.gcd a b) * k := by
  have gpos : ((Int.gcd a b : ℕ) : ℤ) ≠ 0 := by exact_mod_cast hg
  obtain ⟨a', ha'⟩ : ((Int.gcd a b : ℕ) : ℤ) ∣ a := Int.gcd_dvd_left a b
  obtain ⟨b', hb'⟩ : ((Int.gcd a b : ℕ) : ℤ) ∣ b := Int.gcd_dvd_right a b
  have hdiva : a / Int.gcd a b = a' := Int.ediv_eq_of_eq_mul_right gpos ha'
  have hdivb : b / Int.gcd a b = b' := Int.ediv_eq_of_eq_mul_right gpos hb'
  have hcop : IsCoprime a' b' := by
    rw [Int.isCoprime_iff_gcd_eq_one, ← hdiva, ← hdivb]
    exact Int.gcd_div_gcd_div_gcd (Nat.pos_of_ne_zero hg)
  rw [hdiva, hdivb]
  have key : a' * (x - x₀) = - (b' * (y - y₀)) := by
    have : ((Int.gcd a b : ℕ) : ℤ) * (a' * (x - x₀))
        = ((Int.gcd a b : ℕ) : ℤ) * (- (b' * (y - y₀))) := by
      linear_combination h - h₀ - (x - x₀) * ha' - (y - y₀) * hb'
    exact mul_left_cancel₀ gpos this
  by_cases hb0 : b' = 0
  · subst hb0
    have hunit : IsUnit a' := isCoprime_zero_right.1 hcop
    have ha1 : a' * a' = 1 := by
      rcases Int.isUnit_iff.1 hunit with h1 | h1 <;> simp [h1]
    have hx : x - x₀ = 0 := by
      have : a' * (x - x₀) = 0 := by simpa using key
      rcases mul_eq_zero.1 this with h1 | h1
      · simp [h1] at ha1
      · exact h1
    refine ⟨(y₀ - y) * a', by linarith, ?_⟩
    linear_combination (y₀ - y) * ha1
  · have hdiv : b' ∣ x - x₀ := by
      have : b' ∣ a' * (x - x₀) := ⟨-(y - y₀), by rw [key]; ring⟩
      exact hcop.symm.dvd_of_dvd_mul_left this
    obtain ⟨k, hk⟩ := hdiv
    refine ⟨k, by linarith, ?_⟩
    have : b' * (y - y₀) = b' * (-(a' * k)) := by
      rw [hk] at key
      linarith [key]
    have := mul_left_cancel₀ hb0 this
    linarith

/-! ## X9 — the Lorentzian lattice -/

/-- The Weyl vector `(0, 1, …, 24 | 70)` of `II₂₅,₁` is null:
`0² + 1² + ⋯ + 24² = 4900 = 70²`. -/
theorem weyl_vector_null : ∑ k ∈ Finset.range 25, k ^ 2 = 70 ^ 2 := by decide

end GLM.SubstrateCognition
