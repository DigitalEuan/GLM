module

public import Mathlib

/-!
# The cell guard: a rung's answer that is certified to be the nearest carrier (Phase 128)

The formal half of `studies/CELL_GUARD_STUDY.md`
(`glm_universal.reasoning.cell_guard`).

A rung of the escalation ladder is a point set `L` whose points are at least
`2r` apart (minimum norm `m = 4r²`), read through a quantiser `Q` returning a
nearest point of `L`. A query `q` is answered at the rung with carrier `i` when
the cell `Q q` holds exactly one carrier, `i`. That answer can be wrong: the
query may have crossed a cell wall from the true carrier's cell into `i`'s.

The **cell guard** answers only when, in addition,

  `dist q (c i) + dist q (Q q) < r`,

two distances the rung already has in hand. This file proves what the guard
buys:

* `quantise_eq_of_dist_lt` — a nearest-point quantiser of a `2r`-separated set
  returns `p` for every point within `r` of `p`;
* `guarded_strict_nearest` — a guarded answer is the **strictly nearest
  carrier** to the query, among all carriers, although only two distances were
  computed;
* `guarded_agree` — so two guarded rungs never name different carriers, and
  `firstNamed_agree` — the first guarded answer along any two visiting orders
  is the same carrier: a guarded ladder is order-independent;
* `guarded_correct_of_close` — a guarded answer is right whenever the
  perturbation is shorter than half the distance from the true carrier to every
  other carrier;
* `sqrt_add_lt_sqrt_iff` — the exact test the code applies:
  `√A + √B < √R ↔ A + B < R ∧ 4AB < (R - A - B)²`, so the guard is decided in
  rational arithmetic with no square root taken.

Nothing here says the guard keeps any particular share of the correct answers;
that is measured.
-/

@[expose] public section

namespace GLM.CellGuard

variable {α ι : Type*} [MetricSpace α]

/-- The points of `L` are pairwise at least `2r` apart (minimum norm `4r²`). -/
def Separated (L : Set α) (r : ℝ) : Prop :=
  ∀ p ∈ L, ∀ p' ∈ L, p ≠ p' → 2 * r ≤ dist p p'

/-- `Q` returns a nearest point of `L`. -/
def IsNearest (L : Set α) (Q : α → α) : Prop :=
  ∀ x, Q x ∈ L ∧ ∀ p ∈ L, dist x (Q x) ≤ dist x p

/-- Within the packing radius the quantiser is forced: a point closer than `r`
to a point `p` of a `2r`-separated set is quantised to `p`. -/
theorem quantise_eq_of_dist_lt {L : Set α} {Q : α → α} {r : ℝ}
    (hL : Separated L r) (hQ : IsNearest L Q) {x p : α} (hp : p ∈ L)
    (hx : dist x p < r) : Q x = p := by
  by_contra hne
  have h1 := hL (Q x) (hQ x).1 p hp hne
  have h2 := (hQ x).2 p hp
  have h3 := dist_triangle (Q x) x p
  rw [dist_comm (Q x) x] at h3
  linarith

/-- **The guard certifies the nearest carrier.** If the cell of the query holds
only carrier `i`, and `dist q (c i) + dist q (Q q) < r`, then `c i` is strictly
nearer to `q` than every other carrier. -/
theorem guarded_strict_nearest {L : Set α} {Q : α → α} {r : ℝ}
    (hL : Separated L r) (hQ : IsNearest L Q) (c : ι → α) (q : α) (i : ι)
    (hcell : ∀ k, Q (c k) = Q q → k = i)
    (hguard : dist q (c i) + dist q (Q q) < r) :
    ∀ k, k ≠ i → dist q (c i) < dist q (c k) := by
  intro k hk
  have hfar : r ≤ dist (c k) (Q q) := by
    by_contra hlt
    push_neg at hlt
    exact hk (hcell k (quantise_eq_of_dist_lt hL hQ (hQ q).1 hlt))
  have htri := dist_triangle (c k) q (Q q)
  rw [dist_comm (c k) q] at htri
  linarith

/-- The data of one guarded rung reading of a query: a guarded answer `i` is a
carrier strictly nearer to `q` than every other. -/
def StrictNearest (c : ι → α) (q : α) (i : ι) : Prop :=
  ∀ k, k ≠ i → dist q (c i) < dist q (c k)

theorem guarded_isStrictNearest {L : Set α} {Q : α → α} {r : ℝ}
    (hL : Separated L r) (hQ : IsNearest L Q) (c : ι → α) (q : α) (i : ι)
    (hcell : ∀ k, Q (c k) = Q q → k = i)
    (hguard : dist q (c i) + dist q (Q q) < r) : StrictNearest c q i :=
  guarded_strict_nearest hL hQ c q i hcell hguard

/-- A strictly nearest carrier is unique. -/
theorem strictNearest_unique {c : ι → α} {q : α} {i j : ι}
    (hi : StrictNearest c q i) (hj : StrictNearest c q j) : i = j := by
  by_contra hne
  have h1 := hi j (Ne.symm hne)
  have h2 := hj i hne
  linarith

/-- **Guarded rungs never disagree.** Two guarded rungs — any two point sets,
quantisers and radii — that both answer a query name the same carrier. -/
theorem guarded_agree {L₁ L₂ : Set α} {Q₁ Q₂ : α → α} {r₁ r₂ : ℝ}
    (hL₁ : Separated L₁ r₁) (hQ₁ : IsNearest L₁ Q₁)
    (hL₂ : Separated L₂ r₂) (hQ₂ : IsNearest L₂ Q₂)
    (c : ι → α) (q : α) (i j : ι)
    (hcell₁ : ∀ k, Q₁ (c k) = Q₁ q → k = i)
    (hguard₁ : dist q (c i) + dist q (Q₁ q) < r₁)
    (hcell₂ : ∀ k, Q₂ (c k) = Q₂ q → k = j)
    (hguard₂ : dist q (c j) + dist q (Q₂ q) < r₂) : i = j :=
  strictNearest_unique (guarded_isStrictNearest hL₁ hQ₁ c q i hcell₁ hguard₁)
    (guarded_isStrictNearest hL₂ hQ₂ c q j hcell₂ hguard₂)

/-- **A guarded ladder is order-independent.** If every answer a rung gives is a
strictly nearest carrier (as `guarded_isStrictNearest` makes every guarded
answer), the first answer met along any two visiting orders is the same. -/
theorem firstNamed_agree {R : Type*} (ans : R → Option ι) (c : ι → α) (q : α)
    (hans : ∀ ρ i, ans ρ = some i → StrictNearest c q i)
    (l₁ l₂ : List R) {i j : ι}
    (h₁ : l₁.findSome? ans = some i) (h₂ : l₂.findSome? ans = some j) :
    i = j := by
  obtain ⟨ρ₁, -, hρ₁⟩ := List.exists_of_findSome?_eq_some h₁
  obtain ⟨ρ₂, -, hρ₂⟩ := List.exists_of_findSome?_eq_some h₂
  exact strictNearest_unique (hans ρ₁ i hρ₁) (hans ρ₂ j hρ₂)

/-- **When a guarded answer is right.** If the query `q` is the true carrier
`c t` moved by less than half the distance from `c t` to every other carrier,
a guarded answer `i` is `t`. -/
theorem guarded_correct_of_close {c : ι → α} {q : α} {i t : ι}
    (hi : StrictNearest c q i)
    (hclose : ∀ k, k ≠ t → 2 * dist q (c t) < dist (c t) (c k)) : i = t := by
  by_contra hne
  have h1 := hi t (Ne.symm hne)
  have h2 := hclose i hne
  have h3 := dist_triangle (c t) q (c i)
  rw [dist_comm (c t) q] at h3
  linarith

/-- The exact test: for non-negative `A`, `B`, `R`,
`√A + √B < √R ↔ A + B < R ∧ 4AB < (R - A - B)²`. -/
theorem sqrt_add_lt_sqrt_iff {A B R : ℝ} (hA : 0 ≤ A) (hB : 0 ≤ B) (hR : 0 ≤ R) :
    Real.sqrt A + Real.sqrt B < Real.sqrt R ↔
      A + B < R ∧ 4 * A * B < (R - A - B) ^ 2 := by
  have sA := Real.sq_sqrt hA
  have sB := Real.sq_sqrt hB
  have sR := Real.sq_sqrt hR
  have pA := Real.sqrt_nonneg A
  have pB := Real.sqrt_nonneg B
  have pR := Real.sqrt_nonneg R
  have hAB : Real.sqrt (A * B) = Real.sqrt A * Real.sqrt B := Real.sqrt_mul hA B
  constructor
  · intro h
    have hsq : (Real.sqrt A + Real.sqrt B) ^ 2 < Real.sqrt R ^ 2 := by
      apply pow_lt_pow_left₀ h (by positivity) (by norm_num)
    have key : A + B + 2 * (Real.sqrt A * Real.sqrt B) < R := by nlinarith
    have hpos : 0 ≤ Real.sqrt A * Real.sqrt B := mul_nonneg pA pB
    refine ⟨by nlinarith, ?_⟩
    have : 2 * (Real.sqrt A * Real.sqrt B) < R - A - B := by linarith
    have h4 : (2 * (Real.sqrt A * Real.sqrt B)) ^ 2 < (R - A - B) ^ 2 := by
      apply pow_lt_pow_left₀ this (by positivity) (by norm_num)
    have : (2 * (Real.sqrt A * Real.sqrt B)) ^ 2 = 4 * A * B := by
      rw [mul_pow, mul_pow, sA, sB]; ring
    linarith
  · rintro ⟨h1, h2⟩
    have hpos : 0 ≤ Real.sqrt A * Real.sqrt B := mul_nonneg pA pB
    have h4 : (2 * (Real.sqrt A * Real.sqrt B)) ^ 2 < (R - A - B) ^ 2 := by
      have : (2 * (Real.sqrt A * Real.sqrt B)) ^ 2 = 4 * A * B := by
        rw [mul_pow, mul_pow, sA, sB]; ring
      linarith
    have h5 : 2 * (Real.sqrt A * Real.sqrt B) < R - A - B :=
      lt_of_pow_lt_pow_left₀ 2 (by linarith) h4
    have hsq : (Real.sqrt A + Real.sqrt B) ^ 2 < Real.sqrt R ^ 2 := by nlinarith
    exact lt_of_pow_lt_pow_left₀ 2 pR hsq

end GLM.CellGuard
