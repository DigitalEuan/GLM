/-
# A coordinate for the name

`Escalation.lean` proves the ceiling: a register is a *naming*, two entries may
carry the same 24 coordinates, and then no layer of the stack separates them,
because every layer's view is a function of the carrier.  The measurement in
`glm_universal/reasoning/escalation.py` found that ceiling biting hard — 1,040
named entries, 757 distinct carriers, so 283 entries that nothing can reach,
in 104 collision classes every one of which lies inside a single register, the
largest being 78 dimensionless physics quantities.

The diagnosis recorded there was that *what is missing is a coordinate for the
name*.  `glm_universal/reasoning/name_coordinate.py` supplies one and measures
what it buys.  This file proves the four things that measurement turns on, so
that the numbers are read against statements rather than against expectations.

* **A name coordinate can only split.**  `namedLayer_refines_entryLayer`: the
  reading `(view, code)` refines the reading `view`, so adding the coordinate
  cannot conflate two entries a layer already told apart.  This is the same
  cumulative shape as the measure-word widening, and it is why the measured
  `violations` column is zero and must be.
* **An injective coordinate lifts the ceiling completely, from any layer.**
  `namedResolution_of_injective`: with an injective code the named reading
  resolves *every* entry, and it does so even over the 24-bit substrate.  The
  measured `1,040 of 1,040` is therefore not evidence that anything was learnt:
  it is forced.  What the coordinate supplies is an address, not a meaning.
* **A bounded coordinate cannot do it for free.**  `namedResolution_le_mul`:
  a code with `m` values raises the ceiling by a factor of at most `m`, and
  `card_le_of_codeInjOn` is the sharp form inside one collision class — if a
  set of entries shares a carrier and the named reading separates it, that set
  has at most `m` members.  A class of 78 therefore needs at least 78 codes,
  which is the floor the bit sweep is measured against.
* **A coordinate is not informative merely by existing.**
  `namedResolution_eq_of_constant_on_classes` is the control as a theorem: a
  code that is constant on every carrier collision class recovers nothing at
  all.  The register label is exactly such a code on the shipped data — all
  104 classes lie inside one register — and the measurement duly reports that
  it recovers 0 of the 283.
-/
import RequestProject.GLM.Escalation

namespace GLM.Info

open Layer

variable {ι : Type} [Fintype ι] {K : Type}

/-! ## Entries as their own carrier space -/

/-- A layer read through a naming: what a layer of the stack sees of an
*entry*, rather than of a carrier.  Two entries that share a carrier are
indistinguishable here, which is the ceiling. -/
def entryLayer (L : Layer Carrier24) (R : Naming ι) : Layer ι where
  View := L.View
  perceive := fun i => L.perceive (R i)

/-- The same reading with a coordinate for the name beside it.  `code` is any
function of the entry — in the measurement it is an exact integer computed
from the entry's own name, and nothing is stored beside the entry. -/
def namedLayer (L : Layer Carrier24) (R : Naming ι) (code : ι → K) :
    Layer ι where
  View := L.View × K
  perceive := fun i => (L.perceive (R i), code i)

open scoped Classical in
/-- How many entries the named reading tells apart. -/
noncomputable def namedResolution (L : Layer Carrier24) (R : Naming ι)
    (code : ι → K) : ℕ :=
  (Finset.univ.image fun i => (L.perceive (R i), code i)).card

open scoped Classical in
/-- The reading without the coordinate is the first component of the reading
with it: every statement below is a statement about this one identity. -/
theorem entry_image_eq_fst_image (L : Layer Carrier24) (R : Naming ι)
    (code : ι → K) :
    (Finset.univ.image fun i => L.perceive (R i))
      = (Finset.univ.image fun i => (L.perceive (R i), code i)).image
          Prod.fst := by
  classical
  rw [Finset.image_image]
  rfl

/-! ## A name coordinate can only split -/

omit [Fintype ι] in
/-- **The widening.**  The named reading refines the reading without it: a
coordinate added beside a view never merges two entries the view separated. -/
theorem namedLayer_refines_entryLayer (L : Layer Carrier24) (R : Naming ι)
    (code : ι → K) :
    Refines (namedLayer L R code) (entryLayer L R) := by
  intro i j h
  exact congrArg Prod.fst h

open scoped Classical in
/-- Hence the ceiling can only go up: the named reading resolves at least as
many entries as the layer alone did. -/
theorem entryResolution_le_namedResolution (L : Layer Carrier24)
    (R : Naming ι) (code : ι → K) :
    entryResolution L R ≤ namedResolution L R code := by
  classical
  unfold entryResolution namedResolution
  rw [entry_image_eq_fst_image L R code]
  exact Finset.card_image_le

open scoped Classical in
/-- And no reading resolves more entries than there are entries. -/
theorem namedResolution_le_card (L : Layer Carrier24) (R : Naming ι)
    (code : ι → K) :
    namedResolution L R code ≤ Fintype.card ι := by
  classical
  unfold namedResolution
  simpa [Finset.card_univ] using
    (Finset.card_image_le :
      (Finset.univ.image fun i => (L.perceive (R i), code i)).card
        ≤ (Finset.univ : Finset ι).card)

/-! ## An injective coordinate lifts the ceiling, and says nothing -/

open scoped Classical in
/-- **The ceiling is a coordinate problem, and this is the proof.**  With an
injective name code the named reading separates every entry — whatever the
layer underneath it, the 24-bit substrate included.  The measured
`1,040 of 1,040` is therefore forced rather than found: what an injective name
coordinate supplies is an address, not a measurement. -/
theorem namedResolution_of_injective (L : Layer Carrier24) (R : Naming ι)
    {code : ι → K} (h : Function.Injective code) :
    namedResolution L R code = Fintype.card ι := by
  classical
  unfold namedResolution
  rw [Finset.card_image_of_injective _ ?inj, Finset.card_univ]
  case inj =>
    intro i j hij
    exact h (congrArg Prod.snd hij)

/-! ## A bounded coordinate cannot do it for free -/

open scoped Classical in
/-- **The pigeonhole bound.**  A code taking at most `m` values multiplies the
resolution by at most `m`: what the layer could not see, `m` codes can split
into at most `m` pieces. -/
theorem namedResolution_le_mul [Fintype K] (L : Layer Carrier24)
    (R : Naming ι) (code : ι → K) :
    namedResolution L R code ≤ entryResolution L R * Fintype.card K := by
  classical
  unfold namedResolution entryResolution
  have hsub :
      (Finset.univ.image fun i => (L.perceive (R i), code i))
        ⊆ (Finset.univ.image fun i => L.perceive (R i)) ×ˢ Finset.univ := by
    intro p hp
    simp only [Finset.mem_image, Finset.mem_univ, true_and] at hp
    obtain ⟨i, hi⟩ := hp
    subst hi
    exact Finset.mem_product.2 ⟨Finset.mem_image.2 ⟨i, Finset.mem_univ i, rfl⟩,
      Finset.mem_univ _⟩
  calc (Finset.univ.image fun i => (L.perceive (R i), code i)).card
      ≤ ((Finset.univ.image fun i => L.perceive (R i)) ×ˢ
          (Finset.univ : Finset K)).card := Finset.card_le_card hsub
    _ = (Finset.univ.image fun i => L.perceive (R i)).card *
          Fintype.card K := by
          rw [Finset.card_product, Finset.card_univ]

omit [Fintype ι] in
/-- **The sharp form, inside one collision class.**  If a set of entries all
carry the same 24 coordinates — so that no layer separates them — and a code
does separate them, then the code takes as many values as the set has members:
a class of 78 entries needs at least 78 codes, whatever the reduction does. -/
theorem card_le_of_codeInjOn [Fintype K] (code : ι → K) (S : Finset ι)
    (hinj : ∀ i ∈ S, ∀ j ∈ S, code i = code j → i = j) :
    S.card ≤ Fintype.card K := by
  classical
  have hcard : S.card = (S.image code).card :=
    (Finset.card_image_of_injOn (fun i hi j hj h => hinj i hi j hj h)).symm
  rw [hcard]
  simpa using Finset.card_le_univ (S.image code)

/-! ## A coordinate that is constant on the classes recovers nothing -/

open scoped Classical in
/-- **The control, as a theorem.**  A code that never separates two entries
sharing a carrier resolves exactly what the carrier already resolved: adding it
recovers nothing.  On the shipped registers the register label is such a code —
all 104 collision classes lie inside a single register — and the measurement
reports it recovering 0 of the 283, which is this statement instantiated. -/
theorem namedResolution_eq_of_constant_on_classes (L : Layer Carrier24)
    (R : Naming ι) (code : ι → K)
    (h : ∀ i j, L.Indist (R i) (R j) → code i = code j) :
    namedResolution L R code = entryResolution L R := by
  classical
  unfold namedResolution entryResolution
  rw [entry_image_eq_fst_image L R code]
  refine (Finset.card_image_of_injOn ?_).symm
  intro p hp q hq hpq
  simp only [Finset.coe_image, Finset.coe_univ, Set.image_univ,
    Set.mem_range] at hp hq
  obtain ⟨i, hi⟩ := hp
  obtain ⟨j, hj⟩ := hq
  subst hi
  subst hj
  exact Prod.ext hpq (h i j hpq)

end GLM.Info
