module

public import RequestProject.GLM.PlacementGuard

/-!
# The address read: a ladder carrier read by its address, under the placement guard (Phase 143)

The formal half of `studies/ADDRESS_READ_STUDY.md`
(`glm_universal.reasoning.address_read`, the `locate` query kind).

Phase 129 (`GLM.PlacementGuard`) proved that one rung's placement-guarded
answer is the strictly nearest carrier. This file states the read the query
kind actually performs: a **stored table** gives, for each rung `r` and each
point `x`, at most one entry — the centre of the cell `x` falls in, the one
carrier that cell holds, and the radius stored for it — and the read walks the
rungs in a list, answering with the first rung whose guard holds.

* `Entry.Sound` — what the stored table must satisfy: every carrier other
  than the entry's is at least the stored radius from the centre. The table is
  sound when every entry is; the code keeps that table beside the digest of
  the carriers it was computed from, so a moved carrier makes it unusable
  rather than wrong.
* `read_strict_nearest` — on a sound table, the read's answer is the strictly
  nearest carrier to the query, and `read_agrees_with_scan` — it is the
  carrier a full scan of every carrier finds, whenever the scan finds a strict
  nearest one. No property of any quantiser is used.
* `read_order_independent` — two visiting orders that both answer name the
  same carrier.
* `entry_unique_in_ball` and `read_unique_in_ball` — the **certificate the
  answer carries**: with `D = radius - dist q centre`, the answer is within
  `D` of the query and *no other carrier is*. So
* `read_origin` — if the query is some carrier `c t` moved by at most `δ`, and
  `δ + dist q centre < radius` at the answering rung, then `t` is the answer:
  a stated bound on how far the point was moved turns the certified-nearest
  answer into a certified-correct one.
* `margin_lower` — the exact rational lower bound the code reports for `D`:
  if `a² ≤ R` and `B ≤ b²`, `0 ≤ b`, then `a - b ≤ √R - √B`.
* `read_none_iff` — the read refuses exactly when no rung's guard holds.
-/

@[expose] public section

namespace GLM.AddressRead

open GLM.CellGuard GLM.PlacementGuard

open Classical in
section

variable {α ι : Type*} [MetricSpace α]

/-- One stored entry of a rung: the centre of a cell, the one carrier the cell
holds, and the radius stored for it. -/
structure Entry (α ι : Type*) where
  centre : α
  carrier : ι
  radius : ℝ

/-- The stored radius is true of the carriers: every other carrier is at least
that far from the cell's centre. -/
def Entry.Sound (c : ι → α) (e : Entry α ι) : Prop :=
  ∀ k, k ≠ e.carrier → e.radius ≤ dist (c k) e.centre

/-- One rung's guarded answer: the entry's carrier, if the placement guard
`dist q (c i) + dist q centre < radius` holds. -/
noncomputable def guarded (c : ι → α) (q : α) : Option (Entry α ι) → Option ι
  | none => none
  | some e => if dist q (c e.carrier) + dist q e.centre < e.radius then some e.carrier
      else none

/-- The read: walk the rungs in `order`, looking each up in the stored table
`cell`, and answer with the first guarded answer. -/
noncomputable def read {R : Type*} (c : ι → α) (cell : R → α → Option (Entry α ι))
    (order : List R) (q : α) : Option ι :=
  order.findSome? fun r => guarded c q (cell r q)

/-- A guarded answer comes from an entry whose guard holds. -/
theorem guarded_eq_some {c : ι → α} {q : α} {o : Option (Entry α ι)} {i : ι}
    (h : guarded c q o = some i) :
    ∃ e, o = some e ∧ e.carrier = i ∧ dist q (c i) + dist q e.centre < e.radius := by
  cases o with
  | none => simp [guarded] at h
  | some e =>
    simp only [guarded] at h
    split_ifs at h with hg
    · cases h
      exact ⟨e, rfl, rfl, hg⟩

/-- **The certificate of one entry.** On a sound entry, the only carrier `t`
with `dist q (c t) + dist q centre < radius` is the entry's own: no other
carrier lies within `radius - dist q centre` of the query. -/
theorem entry_unique_in_ball {c : ι → α} {q : α} {e : Entry α ι} (hs : e.Sound c)
    {t : ι} (ht : dist q (c t) + dist q e.centre < e.radius) : t = e.carrier := by
  by_contra hne
  have h1 := hs t hne
  have h2 := dist_triangle (c t) q e.centre
  rw [dist_comm (c t) q] at h2
  linarith

/-- A table is sound when every entry it can return is sound. -/
def TableSound {R : Type*} (c : ι → α) (cell : R → α → Option (Entry α ι)) : Prop :=
  ∀ r x e, cell r x = some e → e.Sound c

variable {R : Type*} {c : ι → α} {cell : R → α → Option (Entry α ι)}

/-- What an answer of the read is made of: a rung of the order, a stored entry
for the query at that rung, and the guard holding there. -/
theorem read_eq_some {order : List R} {q : α} {i : ι} (h : read c cell order q = some i) :
    ∃ r ∈ order, ∃ e, cell r q = some e ∧ e.carrier = i ∧
      dist q (c i) + dist q e.centre < e.radius := by
  obtain ⟨r, hr, hg⟩ := List.exists_of_findSome?_eq_some h
  obtain ⟨e, he, hi, hgd⟩ := guarded_eq_some hg
  exact ⟨r, hr, e, he, hi, hgd⟩

/-- **The read answers the strictly nearest carrier**, on a sound table. -/
theorem read_strict_nearest (hT : TableSound c cell) {order : List R} {q : α} {i : ι}
    (h : read c cell order q = some i) : StrictNearest c q i := by
  obtain ⟨r, -, e, he, rfl, hg⟩ := read_eq_some h
  exact placed_strict_nearest c q e.centre e.carrier e.radius (hT r q e he) hg

/-- **The read agrees with a full scan**: if the scan of every carrier finds a
strictly nearest carrier `j`, an answer of the read is `j`. -/
theorem read_agrees_with_scan (hT : TableSound c cell) {order : List R} {q : α} {i j : ι}
    (h : read c cell order q = some i) (hj : StrictNearest c q j) : i = j :=
  strictNearest_unique (read_strict_nearest hT h) hj

/-- **The read is order-independent**: two visiting orders that both answer
name the same carrier. -/
theorem read_order_independent (hT : TableSound c cell) {o₁ o₂ : List R} {q : α}
    {i j : ι} (h₁ : read c cell o₁ q = some i) (h₂ : read c cell o₂ q = some j) : i = j :=
  strictNearest_unique (read_strict_nearest hT h₁) (read_strict_nearest hT h₂)

/-- **The certificate an answer carries.** An answer `i` comes with a margin
`D` — the stored radius less the query's distance to the cell centre — such
that `i` is within `D` of the query and no other carrier is. -/
theorem read_unique_in_ball (hT : TableSound c cell) {order : List R} {q : α} {i : ι}
    (h : read c cell order q = some i) :
    ∃ D : ℝ, dist q (c i) < D ∧ ∀ t, dist q (c t) < D → t = i := by
  obtain ⟨r, -, e, he, rfl, hg⟩ := read_eq_some h
  refine ⟨e.radius - dist q e.centre, by linarith, fun t ht => ?_⟩
  exact entry_unique_in_ball (hT r q e he) (by linarith)

/-- **When the answer is the origin.** If the query is the carrier `c t` moved
by at most `δ`, and the answering rung's margin exceeds `δ`, the answer is `t`. -/
theorem read_origin (hT : TableSound c cell) {order : List R} {q : α} {i t : ι} {δ : ℝ}
    (h : read c cell order q = some i) (hmove : dist q (c t) ≤ δ)
    (hmargin : ∀ r e, r ∈ order → cell r q = some e → e.carrier = i →
      δ + dist q e.centre < e.radius) : t = i := by
  obtain ⟨r, hr, e, he, hi, -⟩ := read_eq_some h
  have hm := hmargin r e hr he hi
  rw [← hi]
  exact entry_unique_in_ball (hT r q e he) (by linarith)

/-- **The read refuses exactly when no rung's guard holds.** -/
theorem read_none_iff {order : List R} {q : α} :
    read c cell order q = none ↔ ∀ r ∈ order, guarded c q (cell r q) = none := by
  unfold read
  rw [List.findSome?_eq_none_iff]

end

/-- **The exact lower bound on the margin.** With `a` a rational lower bound
on `√R` and `b` a rational upper bound on `√B`, `a - b` is a lower bound on
`√R - √B`; the code reports `a - b` and so never overstates the margin. -/
theorem margin_lower {a b R B : ℝ} (haR : a ^ 2 ≤ R) (hb : 0 ≤ b)
    (hBb : B ≤ b ^ 2) : a - b ≤ Real.sqrt R - Real.sqrt B := by
  have h1 : a ≤ Real.sqrt R := Real.le_sqrt_of_sq_le haR
  have h2 : Real.sqrt B ≤ b := by
    rw [show b = Real.sqrt (b ^ 2) from (Real.sqrt_sq hb).symm]
    exact Real.sqrt_le_sqrt hBb
  linarith

end GLM.AddressRead
