module

public import RequestProject.GLM.AddressRead

/-!
# The guarded read in the `nearest` kind (Phase 148)

The formal half of `studies/NEAREST_ADDRESS_STUDY.md`
(`glm_universal.reasoning.nearest_address`, the `nearest` query kind on a
point, a moved carrier or a register-qualified carrier of the address table).

The `nearest` kind answers with a **ranking**: every carrier of the pool,
sorted by exact distance to the query. Phase 143 (`GLM.AddressRead`) proved
what one guarded read of the construction ladder is worth. This file joins the
two: when the guarded read answers, the ranking the scan builds agrees with it,
and the read's margin separates the head of the ranking from everything after.

* `ranking_head_eq_read` — on a sound table, if the read answers `i`, the head
  of any ranking of the carriers by distance is `i`: the cheap guarded read and
  the full scan name the same nearest carrier.
* `ranking_tail_outside` — every carrier after the head is at least the read's
  margin `D` from the query, while the head is strictly inside it: the gap
  between first and second place is certified.
* `ranking_head_origin` — if the query is a carrier `c t` moved by at most `δ`
  and the margin exceeds `δ` at the answering rung, the head of the ranking is
  `t`.
* `ranking_head_of_strict` — without the read, the head of a ranking is the
  strict nearest carrier whenever there is one: the scan alone is never wrong
  about first place, only uncertified about the margin.

A ranking here is a duplicate-free list of every carrier, ordered so that each
carrier is no farther from the query than every carrier after it — exactly
what a sort by exact distance (ties broken by name) produces.
-/

@[expose] public section

namespace GLM.NearestAddress

open GLM.CellGuard GLM.PlacementGuard GLM.AddressRead

variable {α ι : Type*} [MetricSpace α]

/-- A ranking of the carriers by distance to `q`: every carrier appears once,
and each is no farther than every carrier after it. -/
structure Ranking (c : ι → α) (q : α) (l : List ι) : Prop where
  nodup : l.Nodup
  complete : ∀ i, i ∈ l
  sorted : l.Pairwise fun a b => dist q (c a) ≤ dist q (c b)

/-- **Without the read**: the head of a ranking is the strict nearest carrier
whenever one exists. -/
theorem ranking_head_of_strict {c : ι → α} {q : α} {l : List ι} {j i : ι}
    (hl : Ranking c q (j :: l)) (hi : StrictNearest c q i) : j = i := by
  by_contra hne
  have hmem : i ∈ j :: l := hl.complete i
  rcases List.mem_cons.mp hmem with h | h
  · exact hne h.symm
  · have hle : dist q (c j) ≤ dist q (c i) := (List.pairwise_cons.mp hl.sorted).1 i h
    have hlt := hi j hne
    linarith

variable {R : Type*} {c : ι → α} {cell : R → α → Option (Entry α ι)}

/-- **The ranking agrees with the guarded read.** -/
theorem ranking_head_eq_read (hT : TableSound c cell) {order : List R} {q : α}
    {i j : ι} {l : List ι} (h : read c cell order q = some i)
    (hl : Ranking c q (j :: l)) : j = i :=
  ranking_head_of_strict hl (read_strict_nearest hT h)

/-- **The certified gap.** When the read answers, there is a margin `D` with
the head of the ranking strictly inside it and every later carrier outside. -/
theorem ranking_tail_outside (hT : TableSound c cell) {order : List R} {q : α}
    {i j : ι} {l : List ι} (h : read c cell order q = some i)
    (hl : Ranking c q (j :: l)) :
    ∃ D : ℝ, dist q (c j) < D ∧ ∀ t ∈ l, D ≤ dist q (c t) := by
  obtain ⟨D, hin, huniq⟩ := read_unique_in_ball hT h
  have hj : j = i := ranking_head_eq_read hT h hl
  subst hj
  refine ⟨D, hin, fun t ht => ?_⟩
  by_contra hlt
  have hti : t = j := huniq t (lt_of_not_ge hlt)
  subst hti
  exact (List.nodup_cons.mp hl.nodup).1 ht

/-- **The origin.** A query that is the carrier `c t` moved by at most `δ`,
with the margin exceeding `δ` at the answering rung, has `t` at the head of its
ranking. -/
theorem ranking_head_origin (hT : TableSound c cell) {order : List R} {q : α}
    {i j t : ι} {l : List ι} {δ : ℝ} (h : read c cell order q = some i)
    (hl : Ranking c q (j :: l)) (hmove : dist q (c t) ≤ δ)
    (hmargin : ∀ r e, r ∈ order → cell r q = some e → e.carrier = i →
      δ + dist q e.centre < e.radius) : j = t := by
  rw [ranking_head_eq_read hT h hl]
  exact (read_origin hT h hmove hmargin).symm

end GLM.NearestAddress
