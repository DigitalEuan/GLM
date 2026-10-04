import Mathlib
import RequestProject.GLM.ScaleConversion
import RequestProject.GLM.MeasurandKinds

/-!
# The Celsius register: the ITS-90 fixed points and the scale table's offset row

The formal half of `studies/CELSIUS_REGISTER_STUDY.md` (Phase 99,
`glm_universal.data_objects.fixed_points`). The register holds the fourteen
ITS-90 fixed points' assigned temperatures in degrees Celsius, and the scale
table carries them into kelvins through its one offset row,
`fixed_point:temperature_C`, factor `1`, offset `273.15`.

* `celsiusRow_apply` — the offset row is exactly the Celsius level map of
  `GLM.MeasurandKinds.celsiusLevel`.
* `register_carries_to_its90_kelvin` — carried through the row, the register's
  Celsius column is exactly the ITS-90 kelvin column, point by point (mark C1).
* `register_above_absolute_zero`, `register_strictly_increasing` — every point
  is a positive thermodynamic temperature, and the points are listed in
  increasing order.
* `celsius_row_keeps_verdicts`, `celsius_row_order_invariant` — the row has a
  positive factor, so carrying two Celsius readings into kelvins leaves their
  verdict alone (`GLM.ScaleConversion.cmpQ_apply` with a non-zero offset, which
  is the half of it no declared row exercised before this round).
* `dropping_the_offset_flips_a_verdict` — the offset is load-bearing: the
  water triple point (`0.01 °C`) is above mercury's melting point
  (`234.32 K`), and with the offset dropped it is below (cases `o03`, `o04`).
* `naive_level_wrong` — a law that reads a level (`S = E / T`) gives a
  different answer for every non-zero `E` when a Celsius reading is taken as
  kelvins: this is why the offset-dropped control answers every planner case
  wrongly.
* `planner_answers` — the six declared planner answers, as exact arithmetic.
* `aluminium_gap` — the element register's aluminium melting point
  (`933.437 K`) lies `9/250 K` below the ITS-90 aluminium point (`933.473 K`).
-/

namespace GLM.CelsiusRegister

open GLM.CoordinateOrder
open GLM.ScaleConversion

/-- The scale table's offset row: degrees Celsius into kelvins. -/
def celsiusRow : Conv := ⟨"fixed_point:temperature_C", "temperature", 1, 27315 / 100⟩

/-- The register as declared: each fixed point's `t90` in degrees Celsius. -/
def its90Celsius : List (String × ℚ) :=
  [("hydrogen triple point", -2593467 / 10000),
   ("neon triple point", -2485939 / 10000),
   ("oxygen triple point", -2187916 / 10000),
   ("argon triple point", -1893442 / 10000),
   ("mercury triple point", -388344 / 10000),
   ("water triple point", 1 / 100),
   ("gallium melting point", 297646 / 10000),
   ("indium freezing point", 1565985 / 10000),
   ("tin freezing point", 231928 / 1000),
   ("zinc freezing point", 419527 / 1000),
   ("aluminium freezing point", 660323 / 1000),
   ("silver freezing point", 96178 / 100),
   ("gold freezing point", 106418 / 100),
   ("copper freezing point", 108462 / 100)]

/-- The same points' `T90` in kelvins, as ITS-90 Table 1 states them (not
held by the register). -/
def its90Kelvin : List (String × ℚ) :=
  [("hydrogen triple point", 138033 / 10000),
   ("neon triple point", 245561 / 10000),
   ("oxygen triple point", 543584 / 10000),
   ("argon triple point", 838058 / 10000),
   ("mercury triple point", 2343156 / 10000),
   ("water triple point", 27316 / 100),
   ("gallium melting point", 3029146 / 10000),
   ("indium freezing point", 4297485 / 10000),
   ("tin freezing point", 505078 / 1000),
   ("zinc freezing point", 692677 / 1000),
   ("aluminium freezing point", 933473 / 1000),
   ("silver freezing point", 123493 / 100),
   ("gold freezing point", 133733 / 100),
   ("copper freezing point", 135777 / 100)]

/-- **The offset row is the Celsius level map.** -/
theorem celsiusRow_apply (t : ℚ) :
    apply celsiusRow t = GLM.MeasurandKinds.celsiusLevel t := by
  simp [apply, celsiusRow, GLM.MeasurandKinds.celsiusLevel]

/-- **Mark C1.** Carried through the offset row, the register's Celsius column
is exactly the ITS-90 kelvin column. -/
theorem register_carries_to_its90_kelvin :
    its90Celsius.map (fun p => (p.1, apply celsiusRow p.2)) = its90Kelvin := by
  simp only [its90Celsius, its90Kelvin, List.map_cons, List.map_nil, apply,
    celsiusRow]
  norm_num

/-- Every fixed point is a positive thermodynamic temperature. -/
theorem register_above_absolute_zero :
    ∀ p ∈ its90Celsius, 0 < apply celsiusRow p.2 := by
  intro p hp
  simp only [its90Celsius, List.mem_cons, List.not_mem_nil, or_false] at hp
  rcases hp with h | h | h | h | h | h | h | h | h | h | h | h | h | h <;>
    subst h <;> norm_num [apply, celsiusRow]

/-- The points are listed in strictly increasing order of temperature. -/
theorem register_strictly_increasing :
    (its90Celsius.map Prod.snd).Pairwise (· < ·) := by
  simp only [its90Celsius, List.map_cons, List.map_nil]
  simp only [List.pairwise_cons, List.mem_cons, List.not_mem_nil, or_false,
    forall_eq_or_imp, forall_eq, List.Pairwise.nil, and_true]
  norm_num

/-- The offset row has a positive factor. -/
theorem celsiusRow_factor_pos : 0 < celsiusRow.factor := by
  norm_num [celsiusRow]

/-- **The row keeps every verdict**: two Celsius readings compare in kelvins
exactly as they do in degrees Celsius. -/
theorem celsius_row_keeps_verdicts (x y : ℚ) :
    cmpQ (apply celsiusRow x) (apply celsiusRow y) = cmpQ x y :=
  cmpQ_apply celsiusRow_factor_pos x y

/-- The same at the ordering operation itself. -/
theorem celsius_row_order_invariant (x y : Reading) :
    order? (some ⟨x.scale, apply celsiusRow x.value⟩)
        (some ⟨y.scale, apply celsiusRow y.value⟩)
      = order? (some x) (some y) :=
  order_conversion_invariant celsiusRow_factor_pos x y

/-- **The offset is load-bearing.** The water triple point (`0.01 °C`) is above
mercury's melting point in the element register (`234.32 K`); read with the
offset dropped it is below. Likewise the gallium point (`29.7646 °C`) against
gallium's melting point (`302.91 K`). -/
theorem dropping_the_offset_flips_a_verdict :
    cmpQ (apply celsiusRow (1 / 100)) (5858 / 25) = .gt ∧
      cmpQ (1 / 100) (5858 / 25) = .lt ∧
    cmpQ (apply celsiusRow (297646 / 10000)) (30291 / 100) = .gt ∧
      cmpQ (297646 / 10000) (30291 / 100) = .lt := by
  refine ⟨?_, ?_, ?_, ?_⟩ <;> norm_num [cmpQ, apply, celsiusRow]

/-- **A level law read with the offset dropped is wrong.** For a Celsius
reading `t` that is neither `0` nor `-273.15`, and any non-zero `E`, the
entropy `E / T` with `T` the kelvin level differs from `E / t`. -/
theorem naive_level_wrong (E t : ℚ) (hE : E ≠ 0) (ht : t ≠ 0)
    (hT : apply celsiusRow t ≠ 0) :
    E / apply celsiusRow t ≠ E / t := by
  intro h
  rw [div_eq_div_iff hT ht] at h
  have h2 : E * (t - apply celsiusRow t) = 0 := by linarith
  rcases mul_eq_zero.mp h2 with h3 | h3
  · exact hE h3
  · norm_num [apply, celsiusRow] at h3

/-- **The declared planner answers**, as exact arithmetic over the register
(cases `p01`, `p02`, `p03`, `p04` in kilojoules, `p07`, `p09`). -/
theorem planner_answers :
    2731600 / apply celsiusRow (1 / 100) = 10000 ∧
    2 * apply celsiusRow (297646 / 10000) = 1514573 / 2500 ∧
    3 * apply celsiusRow (419527 / 1000) = 2078031 / 1000 ∧
    2 * apply celsiusRow (1 / 100) / 1000 = 6829 / 12500 ∧
    4686312 / apply celsiusRow (-388344 / 10000) = 20000 ∧
    1 * apply celsiusRow (96178 / 100) = 123493 / 100 := by
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_⟩ <;> norm_num [apply, celsiusRow]

/-- **The aluminium gap.** The element register's aluminium melting point,
`933.437 K`, lies `9/250 K` below the ITS-90 aluminium freezing point carried
from `660.323 °C`. -/
theorem aluminium_gap :
    apply celsiusRow (660323 / 1000) - 933437 / 1000 = 9 / 250 := by
  norm_num [apply, celsiusRow]

end GLM.CelsiusRegister
