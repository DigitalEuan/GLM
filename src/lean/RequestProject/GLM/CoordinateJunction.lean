module

public import RequestProject.GLM.AddressRead

/-!
# Coordinate junctions: the address read over carriers that share coordinates (Phase 144)

The formal half of `studies/COORDINATE_JUNCTION_STUDY.md`
(`glm_universal.reasoning.coordinate_junction`, the `locate` query kind).

Phase 143 (`GLM.AddressRead`) refuses every carrier whose exact coordinates
another carrier also has: its cell is always shared, and its radius is `0`.
Phase 66's junction rule for formula wheels says what to do with a name two
wheels share: it is *one* variable only where a declared junction identifies
it, and otherwise it is split. This file states the same discipline for
coordinates: carriers with equal coordinates form a **junction**, the read
answers the junction rather than refusing, and which members are the same
object is a declaration, never something the coordinates decide.

* `no_read_separates` — the impossibility the junction answers: no function
  of the coordinates names each of two carriers with equal coordinates, so a
  junction is the finest answer any read can give.
* `JSound` — the weaker soundness a junction entry needs: every carrier
  whose coordinates *differ* from the entry's is at least the stored radius
  from the centre. `jsound_of_sound`: every Phase 143 entry is one, so the
  junction table contains the old table unchanged.
* `jread_junction_nearest` — on a junction-sound table an answer `i` is
  strictly nearer the query than every carrier off its coordinates, and
  `jread_members_tie` — every member of its junction is exactly as near.
* `jread_scan` — the answer's junction is exactly the set of carriers a full
  scan finds at the least distance.
* `jread_order_independent` — two visiting orders answer the same junction.
* `jread_unique_in_ball` — the certificate: the junction is the only thing
  within the margin `radius - dist q centre`.
* `jread_origin` — if the query is carrier `t` moved by at most `δ` inside
  the margin, `t` is in the answered junction.
* `jread_strict_nearest_of_injective` — where no two carriers share
  coordinates the junction read answers the strictly nearest carrier, as
  Phase 143's read does.
-/

@[expose] public section

namespace GLM.CoordinateJunction

open GLM.CellGuard GLM.PlacementGuard GLM.AddressRead

/-- **No read separates a junction.** If two different carriers have the same
coordinates, no function of the coordinates names each of them. -/
theorem no_read_separates {α ι : Type*} (c : ι → α) (f : α → ι) {i j : ι} (hc : c i = c j)
    (hne : i ≠ j) : f (c i) ≠ i ∨ f (c j) ≠ j := by
  by_contra h
  push_neg at h
  apply hne
  rw [← h.1, ← h.2, hc]

section

variable {α ι : Type*} [MetricSpace α]

/-- The junction of `i`: the carriers with exactly `i`'s coordinates. -/
def junction (c : ι → α) (i : ι) : Set ι := {k | c k = c i}

/-- A junction entry is sound when every carrier off its coordinates is at
least the stored radius from the centre. -/
def JSound (c : ι → α) (e : Entry α ι) : Prop :=
  ∀ k, c k ≠ c e.carrier → e.radius ≤ dist (c k) e.centre

/-- Every Phase 143 entry is a junction entry. -/
theorem jsound_of_sound {c : ι → α} {e : Entry α ι} (h : e.Sound c) : JSound c e :=
  fun k hk => h k (fun hke => hk (hke ▸ rfl))

/-- A junction table is sound when every entry it can return is. -/
def JTableSound {R : Type*} (c : ι → α) (cell : R → α → Option (Entry α ι)) : Prop :=
  ∀ r x e, cell r x = some e → JSound c e

/-- A sound Phase 143 table is a sound junction table. -/
theorem JTableSound.of_tableSound {R : Type*} {c : ι → α}
    {cell : R → α → Option (Entry α ι)} (h : TableSound c cell) : JTableSound c cell :=
  fun r x e he => jsound_of_sound (h r x e he)

/-- **The certificate of one junction entry.** On a junction-sound entry, a
carrier `t` with `dist q (c t) + dist q centre < radius` has the entry's
coordinates. -/
theorem entry_junction_in_ball {c : ι → α} {q : α} {e : Entry α ι} (hs : JSound c e)
    {t : ι} (ht : dist q (c t) + dist q e.centre < e.radius) : c t = c e.carrier := by
  by_contra hne
  have h1 := hs t hne
  have h2 := dist_triangle (c t) q e.centre
  rw [dist_comm (c t) q] at h2
  linarith

variable {R : Type*} {c : ι → α} {cell : R → α → Option (Entry α ι)}

/-- **The junction is strictly nearest**: an answer `i` is strictly nearer the
query than every carrier whose coordinates differ from `i`'s. -/
theorem jread_junction_nearest (hT : JTableSound c cell) {order : List R} {q : α} {i : ι}
    (h : read c cell order q = some i) :
    ∀ k, c k ≠ c i → dist q (c i) < dist q (c k) := by
  obtain ⟨r, -, e, he, rfl, hg⟩ := read_eq_some h
  intro k hk
  have h1 := hT r q e he k hk
  have htri := dist_triangle (c k) q e.centre
  rw [dist_comm (c k) q] at htri
  linarith

/-- Every member of the answered junction is exactly as near as the answer. -/
theorem jread_members_tie {q : α} {i k : ι} (hk : k ∈ junction c i) :
    dist q (c k) = dist q (c i) := by
  simp only [junction, Set.mem_setOf_eq] at hk
  rw [hk]

/-- **The junction is what a full scan finds**: a carrier is at the least
distance from the query exactly when it is in the answer's junction. -/
theorem jread_scan (hT : JTableSound c cell) {order : List R} {q : α} {i : ι}
    (h : read c cell order q = some i) (k : ι) :
    (∀ m, dist q (c k) ≤ dist q (c m)) ↔ k ∈ junction c i := by
  have hn := jread_junction_nearest hT h
  constructor
  · intro hk
    by_contra hne
    have := hn k hne
    have := hk i
    linarith
  · intro hk m
    rw [jread_members_tie hk]
    by_cases hm : c m = c i
    · rw [hm]
    · exact (hn m hm).le

/-- **The junction is order-independent**: two visiting orders that both
answer name carriers of the same junction. -/
theorem jread_order_independent (hT : JTableSound c cell) {o₁ o₂ : List R} {q : α}
    {i j : ι} (h₁ : read c cell o₁ q = some i) (h₂ : read c cell o₂ q = some j) :
    c i = c j := by
  by_contra hne
  have a := jread_junction_nearest hT h₁ j (Ne.symm hne)
  have b := jread_junction_nearest hT h₂ i hne
  linarith

/-- **The certificate a junction answer carries**: within the margin
`radius - dist q centre` lie the answer's junction and nothing else. -/
theorem jread_unique_in_ball (hT : JTableSound c cell) {order : List R} {q : α} {i : ι}
    (h : read c cell order q = some i) :
    ∃ D : ℝ, dist q (c i) < D ∧ ∀ t, dist q (c t) < D → c t = c i := by
  obtain ⟨r, -, e, he, rfl, hg⟩ := read_eq_some h
  refine ⟨e.radius - dist q e.centre, by linarith, fun t ht => ?_⟩
  exact entry_junction_in_ball (hT r q e he) (by linarith)

/-- **The origin is in the junction.** If the query is carrier `t` moved by at
most `δ`, and the answering rung's margin exceeds `δ`, `t` is in the answered
junction. -/
theorem jread_origin (hT : JTableSound c cell) {order : List R} {q : α} {i t : ι} {δ : ℝ}
    (h : read c cell order q = some i) (hmove : dist q (c t) ≤ δ)
    (hmargin : ∀ r e, r ∈ order → cell r q = some e → e.carrier = i →
      δ + dist q e.centre < e.radius) : t ∈ junction c i := by
  obtain ⟨r, hr, e, he, hi, -⟩ := read_eq_some h
  have hm := hmargin r e hr he hi
  show c t = c i
  rw [← hi]
  exact entry_junction_in_ball (hT r q e he) (by linarith)

/-- **Nothing changes where coordinates are distinct**: if no two carriers
share coordinates, a junction answer is the strictly nearest carrier. -/
theorem jread_strict_nearest_of_injective (hT : JTableSound c cell)
    (hc : Function.Injective c) {order : List R} {q : α} {i : ι}
    (h : read c cell order q = some i) : StrictNearest c q i :=
  fun k hk => jread_junction_nearest hT h k (fun hki => hk (hc hki))

end

end GLM.CoordinateJunction
