module

public import RequestProject.GLM.CellGuard

/-!
# The placement guard: the cell guard with a radius read from the carriers (Phase 129)

The formal half of `studies/PLACEMENT_GUARD_STUDY.md`
(`glm_universal.reasoning.placement_guard`).

The cell guard of Phase 128 (`GLM.CellGuard`) certifies a rung's answer `i`
as the strictly nearest carrier when `dist q (c i) + dist q (Q q) < r`, with
`r` the packing radius. It was safe and nearly silent: a carrier outside the
inscribed ball of its own cell can never pass it. The proof used the packing
radius only to know that every *other* carrier is at least `r` from the cell
centre. The placement guard stores, once per cell, the radius that is
actually true of the carriers:

  `ρ p = min { dist (c k) p | k ≠ i }`,

and answers when `dist q (c i) + dist q p < ρ p`.

* `placed_strict_nearest` — a placement-guarded answer is the strictly nearest
  carrier. No property of the quantiser is used at all: any assignment of
  queries to cells will do, because the radius is a fact about the carriers.
* `placement_radius_ge` — for a nearest-point quantiser of a `2r`-separated
  set, every other carrier is at least `r` from a cell that holds only `i`, so
  the stored radius is at least the packing radius, and
* `cellGuard_imp_placed` — every answer the cell guard gives, the placement
  guard gives too.
* `placed_firstNamed_agree` — a placement-guarded ladder is order-independent.
-/

@[expose] public section

namespace GLM.PlacementGuard

open GLM.CellGuard

variable {α ι : Type*} [MetricSpace α]

/-- **The placement guard certifies the nearest carrier.** If every carrier
other than `i` is at least `ρ` from the point `p`, and
`dist q (c i) + dist q p < ρ`, then `c i` is strictly nearer to `q` than every
other carrier. -/
theorem placed_strict_nearest (c : ι → α) (q p : α) (i : ι) (ρ : ℝ)
    (hρ : ∀ k, k ≠ i → ρ ≤ dist (c k) p)
    (hguard : dist q (c i) + dist q p < ρ) : StrictNearest c q i := by
  intro k hk
  have h1 := hρ k hk
  have htri := dist_triangle (c k) q p
  rw [dist_comm (c k) q] at htri
  linarith

/-- For a nearest-point quantiser of a `2r`-separated set, a cell `Q q` that
holds only carrier `i` has every other carrier at least `r` from its centre. -/
theorem placement_radius_ge {L : Set α} {Q : α → α} {r : ℝ}
    (hL : Separated L r) (hQ : IsNearest L Q) (c : ι → α) (q : α) (i : ι)
    (hcell : ∀ k, Q (c k) = Q q → k = i) :
    ∀ k, k ≠ i → r ≤ dist (c k) (Q q) := by
  intro k hk
  by_contra hlt
  push_neg at hlt
  exact hk (hcell k (quantise_eq_of_dist_lt hL hQ (hQ q).1 hlt))

/-- **The placement guard answers whenever the cell guard does**, with the
radius `ρ` any lower bound on the other carriers' distances that is at least
the packing radius (in particular the stored minimum). -/
theorem cellGuard_imp_placed {r ρ : ℝ} (hrρ : r ≤ ρ) (q p ci : α)
    (hguard : dist q ci + dist q p < r) : dist q ci + dist q p < ρ :=
  lt_of_lt_of_le hguard hrρ

/-- **A placement-guarded ladder is order-independent**: every answer is the
strictly nearest carrier, so the first answer along any two orders agrees. -/
theorem placed_firstNamed_agree {R : Type*} (ans : R → Option ι) (c : ι → α)
    (q : α) (centre : R → α) (rad : R → ℝ)
    (hans : ∀ ρ i, ans ρ = some i →
      (∀ k, k ≠ i → rad ρ ≤ dist (c k) (centre ρ)) ∧
        dist q (c i) + dist q (centre ρ) < rad ρ)
    (l₁ l₂ : List R) {i j : ι}
    (h₁ : l₁.findSome? ans = some i) (h₂ : l₂.findSome? ans = some j) :
    i = j :=
  firstNamed_agree ans c q
    (fun ρ i h => placed_strict_nearest c q (centre ρ) i (rad ρ)
      (hans ρ i h).1 (hans ρ i h).2) l₁ l₂ h₁ h₂

end GLM.PlacementGuard
