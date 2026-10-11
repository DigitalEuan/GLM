import Mathlib
import RequestProject.GLM.DeepHoleEscalation

/-!
# Which pairs a stray-blind reading must conflate (Phase 110, lattice item 10)

`studies/DEEP_HOLE_ESCALATION_STUDY.md` measured that the exact rational
distance measure (`L₃`) conflates `A_1^24` with `A_2^12`: both reference holes
emitted no stray over the declared ensemble, so each measure is a single atom
at the covering radius.  `STATUS.md` §3.4 item 10 recorded this as an
observation and asked for the theorem: *which* pairs must such a reading
conflate.  This file answers it.

## The model

An emission record is a list of `(point, squared distance)` pairs — exactly
what `deep_hole_escalation.emissions` keeps.  A record is read **at a hole of
squared covering radius `r2`** when no emission is nearer than `r2`: that is
what a deep hole is, a point at the covering radius from the lattice, its
vertices the lattice points at exactly that distance.  Every deep hole of the
Leech lattice is at the same covering radius, so `r2` is one number for all 23
Niemeier types.  An emission at distance `r2` is an **arrival**; anything
further is a **stray**.

## The results

* `minimum_eq_radius` — when at least one start arrives, the minimum distance
  seen (the split the measurement uses) is the covering radius, so the split by
  minimum and the split by `r2` agree.
* `distances_decomp` — the multiset of emission distances is `A` copies of
  `r2` plus the stray spectrum.  The arrivals contribute nothing but their
  count: a reading of distances cannot see *which* vertex a start reached.
* `distances_eq_iff` — **the answer to item 10.**  Two records of the same size
  have the same distance profile exactly when they have the same stray
  spectrum.  So a distance-only reading (the `L₃` profile) conflates precisely
  the pairs of holes whose strays agree, whatever their types.
* `strayFree_conflate` — in particular every pair of stray-free records of the
  same size is conflated: the `A_1^24`/`A_2^12` collapse is an instance, and
  it would happen to any two types the ensemble reaches without a stray.
* `arrivalMeasure_const` — a reading that is blind both to vertex identity and
  to strays (the normalised measure of the arrival distances) is the same
  point mass at `r2` for every record with an arrival: it conflates **every**
  pair of deep holes, all 23 types at once.
* `distanceReading_indist` — the same conclusion for any rung of the ladder
  (`GLM.DeepHoleLadder.Reading`) whose distance depends only on the two
  distance profiles.
* `not_resolves_of_indist` — the bearing on lattice item 6: once two
  references with different labels are conflated, the separation criterion
  `Resolves` fails at every spread `w ≥ 0`, so a rung that conflates can never
  reach `ρ < 1`, at any ensemble size where the conflation persists.
-/

namespace GLM.StrayBlind

open GLM.DeepHoleLadder

variable {P : Type*}

/-- An emission record: each start's emitted point with its exact squared
distance to the centre. -/
abbrev Record (P : Type*) := List (P × ℚ)

/-- The record is read at a hole of squared covering radius `r2`: no emission
is nearer than the covering radius. -/
def AtHole (r2 : ℚ) (rec : Record P) : Prop := ∀ e ∈ rec, r2 ≤ e.2

/-- The distance profile a distance-only reading sees: the multiset of
squared distances, forgetting which point each start reached. -/
def distances (rec : Record P) : Multiset ℚ := (rec.map Prod.snd : Multiset ℚ)

/-- The stray spectrum: the distances of emissions that did not arrive. -/
def strays (r2 : ℚ) (rec : Record P) : Multiset ℚ :=
  (distances rec).filter (fun d => d ≠ r2)

/-- The number of arrivals: emissions at exactly the covering radius. -/
def arrivals (r2 : ℚ) (rec : Record P) : ℕ := (distances rec).count r2

/-- A record with no stray. -/
def StrayFree (r2 : ℚ) (rec : Record P) : Prop := strays r2 rec = 0

/-- The minimum distance seen is the covering radius as soon as one start
arrives, so splitting at the minimum (as the measurement does) and splitting at
`r2` are the same split. -/
theorem minimum_eq_radius {r2 m : ℚ} {rec : Record P} (hhole : AtHole r2 rec)
    (hmin : ∀ e ∈ rec, m ≤ e.2) (hatt : ∃ e ∈ rec, e.2 = m)
    (harr : ∃ e ∈ rec, e.2 = r2) : m = r2 := by
  obtain ⟨e, he, hr⟩ := harr
  obtain ⟨e', he', hm⟩ := hatt
  exact le_antisymm (hr ▸ hmin e he) (hm ▸ hhole e' he')

/-- The distance profile is `A` copies of the covering radius plus the stray
spectrum. -/
theorem distances_decomp (r2 : ℚ) (rec : Record P) :
    distances rec = Multiset.replicate (arrivals r2 rec) r2 + strays r2 rec := by
  rw [arrivals, strays, ← Multiset.filter_eq', Multiset.filter_add_not]

/-- A record of `N` starts has `N` distances. -/
theorem card_distances (rec : Record P) : Multiset.card (distances rec) = rec.length := by
  simp [distances]

/-- **Lattice item 10.**  Two records of the same size have the same distance
profile exactly when they have the same stray spectrum. -/
theorem distances_eq_iff (r2 : ℚ) {rec rec' : Record P}
    (hlen : rec.length = rec'.length) :
    distances rec = distances rec' ↔ strays r2 rec = strays r2 rec' := by
  constructor
  · intro h; simp only [strays, h]
  · intro h
    have hA : arrivals r2 rec = arrivals r2 rec' := by
      have h1 := congrArg Multiset.card (distances_decomp r2 rec)
      have h2 := congrArg Multiset.card (distances_decomp r2 rec')
      simp only [card_distances, Multiset.card_add, Multiset.card_replicate] at h1 h2
      rw [h] at h1; omega
    rw [distances_decomp r2 rec, distances_decomp r2 rec', hA, h]

/-- Every pair of stray-free records of the same size is conflated by a
distance-only reading, whatever the types of the holes. -/
theorem strayFree_conflate {r2 : ℚ} {rec rec' : Record P}
    (hlen : rec.length = rec'.length) (h : StrayFree r2 rec) (h' : StrayFree r2 rec') :
    distances rec = distances rec' :=
  (distances_eq_iff r2 hlen).2 (by rw [StrayFree] at h h'; rw [h, h'])

/-- The normalised measure of the arrival distances: the mass at `x` is the
share of arrivals at distance `x`.  This is what a reading blind both to the
vertex reached and to the strays has left to see. -/
noncomputable def arrivalMeasure (r2 : ℚ) (rec : Record P) (x : ℚ) : ℚ :=
  (((distances rec).filter (fun d => d = r2)).count x : ℚ) / (arrivals r2 rec : ℚ)

/-- A reading blind to the vertex and to the strays is the same point mass at
the covering radius for every record with an arrival: it conflates every pair
of deep holes. -/
theorem arrivalMeasure_const {r2 : ℚ} {rec : Record P}
    (harr : ∃ e ∈ rec, e.2 = r2) (x : ℚ) :
    arrivalMeasure r2 rec x = if x = r2 then 1 else 0 := by
  have hpos : 0 < arrivals r2 rec := by
    obtain ⟨e, he, hr⟩ := harr
    rw [arrivals, Multiset.count_pos, distances]
    simp only [Multiset.mem_coe, List.mem_map]
    exact ⟨e, he, hr⟩
  unfold arrivalMeasure
  rw [Multiset.filter_eq', Multiset.count_replicate]
  split_ifs with h1 h2 h2
  · have : (arrivals r2 rec : ℚ) ≠ 0 := by exact_mod_cast hpos.ne'
    field_simp
    rfl
  · exact absurd h1.symm h2
  · exact absurd h2.symm h1
  · simp

/-- Any rung whose distance depends only on the two distance profiles
conflates records with equal stray spectra and equal size. -/
theorem distanceReading_indist (R : Reading (Record P))
    (D : Multiset ℚ → Multiset ℚ → ℚ)
    (hD : ∀ a b, R.dist a b = D (distances a) (distances b)) {r2 : ℚ}
    {rec rec' : Record P} (hlen : rec.length = rec'.length)
    (hs : strays r2 rec = strays r2 rec') : R.Indist rec rec' := by
  have h := (distances_eq_iff r2 hlen).2 hs
  have h0 := R.dist_self rec
  rw [hD] at h0
  rw [Reading.Indist, hD, ← h, h0]

/-- **The bearing on lattice item 6.**  Two references with different labels
that a rung conflates make the separation criterion fail at every spread
`w ≥ 0`. -/
theorem not_resolves_of_indist {C L : Type*} {R : Reading C}
    {refs : List (L × C)} {w : ℚ} (hw : 0 ≤ w) {e f : L × C} (he : e ∈ refs)
    (hf : f ∈ refs) (hne : e.1 ≠ f.1) (hind : R.Indist e.2 f.2) :
    ¬ Resolves R refs w := by
  intro hres
  have h := hres e he f hf hne
  rw [Reading.Indist] at hind
  linarith

end GLM.StrayBlind
