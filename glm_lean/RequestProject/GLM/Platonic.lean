/-
# The archive's "144° Platonic structure", checked and deflated

This file is **retrieved material**, and it is retrieved as a *correction*.
`GMHGL/value_geometry.py` of the supplied archive
(`source_material/GLM-main.zip`) reports, as one of its headline findings, a
"144° Platonic structure": summing the interior angles of all the faces of each
of the five Platonic solids gives

```
  720°, 2160°, 1440°, 6480°, 3600°
```

— every one an exact multiple of 144° — and a grand total of `14 400° = 80π`
radians. The script presents this as a structural constant of the substrate,
alongside a "48° = 144°/3 trisection constant".

The arithmetic is right and it is reproduced here (`faceAngleSum_values`,
`total_faceAngleSum`, `total_eq_eighty_pi`). The interpretation is not. What is
proved below is that the whole pattern is Euler's formula:

* `faceAngleSum_eq` — for *any* polyhedron whose faces are all regular
  `f`-gons, the total of the face angles is `360·V − 720`, with no dependence on
  `f`, `E` or `F` beyond the Euler relation. (This is Descartes' theorem on the
  total angular defect, read forwards: the defect is always `720°`.)
* `dvd_144_iff_even_vertices` — such a total is a multiple of 144° exactly when
  the solid has an even number of vertices.

The five Platonic solids have `4, 8, 6, 20, 12` vertices, all even, so all five
totals are multiples of 144°; and the grand total is `360·50 − 5·720 = 14 400`.
There is no constant here that is not already the number 360 and the Euler
characteristic 2. The archive's `48°` is `144°/3` and inherits the same status.

Retained, then, as a fact about the substrate's geometry rather than a discovery
about it — and as a worked example of the kind of numerical coincidence the
audit was looking for.
-/
import Mathlib

namespace GLM.Platonic

open Finset

/-! ## 1. The general identity -/

/-- The sum of all the face angles of a polyhedron with `F` faces, each a
regular `f`-gon: each face contributes `f` angles of `180 − 360/f` degrees. -/
def faceAngleSum (F f : ℚ) : ℚ := F * f * (180 - 360 / f)

/-- **The total face angle is `360·V − 720`, always.** Given Euler's relation
`V − E + F = 2` and the incidence count `F·f = 2E`, the sum of the face angles
of a polyhedron with regular `f`-gonal faces depends on nothing but the number
of vertices. This is Descartes' theorem: the total angular defect is `720°`. -/
theorem faceAngleSum_eq {V E F f : ℚ} (hf : f ≠ 0) (heuler : V - E + F = 2)
    (hinc : F * f = 2 * E) : faceAngleSum F f = 360 * V - 720 := by
  have hexpand : faceAngleSum F f = 180 * (F * f) - 360 * F := by
    unfold faceAngleSum
    field_simp
  rw [hexpand, hinc]
  linarith

/-- **The deflation.** A total of the form `360·V − 720` is a whole multiple of
`144` exactly when `V` is even. -/
theorem dvd_144_iff_even_vertices (V : ℤ) :
    (144 : ℤ) ∣ (360 * V - 720) ↔ Even V := by
  constructor
  · rintro ⟨k, hk⟩
    have h2 : (2 : ℤ) ∣ V := by omega
    obtain ⟨r, hr⟩ := h2
    exact ⟨r, by omega⟩
  · rintro ⟨m, hm⟩
    exact ⟨5 * m - 5, by omega⟩

/-! ## 2. The five solids -/

/-- The five Platonic solids as `(name-free) (V, E, F, f)` data: vertices,
edges, faces, and the number of sides of a face. -/
def solids : List (ℚ × ℚ × ℚ × ℚ) :=
  [(4, 6, 4, 3),      -- tetrahedron  {3,3}
   (8, 12, 6, 4),     -- cube         {4,3}
   (6, 12, 8, 3),     -- octahedron   {3,4}
   (20, 30, 12, 5),   -- dodecahedron {5,3}
   (12, 30, 20, 3)]   -- icosahedron  {3,5}

/-- Each of the five satisfies Euler's relation and the incidence count. -/
theorem solids_euler :
    ∀ s ∈ solids, s.1 - s.2.1 + s.2.2.1 = 2 ∧ s.2.2.1 * s.2.2.2 = 2 * s.2.1 := by
  intro s hs
  fin_cases hs <;> norm_num

/-- The five face-angle totals, in degrees. -/
theorem faceAngleSum_values :
    solids.map (fun s => faceAngleSum s.2.2.1 s.2.2.2) = [720, 2160, 1440, 6480, 3600] := by
  simp [solids, faceAngleSum]
  norm_num

/-- Every one of them is a whole multiple of 144°, because every Platonic solid
has an even number of vertices. -/
theorem faceAngleSum_multiples_of_144 :
    solids.map (fun s => faceAngleSum s.2.2.1 s.2.2.2 / 144) = [5, 15, 10, 45, 25] := by
  simp [solids, faceAngleSum]
  norm_num

/-- **The grand total: `14 400°`.** -/
theorem total_faceAngleSum :
    (solids.map fun s => faceAngleSum s.2.2.1 s.2.2.2).sum = 14400 := by
  rw [faceAngleSum_values]
  norm_num

/-- `14 400° = 80π` radians, which is the form the archive reports. -/
theorem total_eq_eighty_pi :
    (solids.map fun s => faceAngleSum s.2.2.1 s.2.2.2).sum / 180 = 80 := by
  rw [total_faceAngleSum]
  norm_num

/-- And the total is `360·(sum of the vertex counts) − 5·720`, so it too says
nothing beyond Euler: the fifty vertices of the five solids. -/
theorem total_from_vertices :
    (solids.map fun s => faceAngleSum s.2.2.1 s.2.2.2).sum
      = 360 * (solids.map fun s => s.1).sum - 5 * 720 := by
  rw [total_faceAngleSum]
  simp [solids]
  norm_num

end GLM.Platonic
