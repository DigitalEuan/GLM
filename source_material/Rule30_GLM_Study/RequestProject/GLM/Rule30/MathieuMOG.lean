import RequestProject.GLM.Rule30.MathieuOrbitsData

/-!
# Round 47: MOG subgroups — octad, sextet and trio stabilisers (To Do 33)

(Not a `module`: the checks use `native_decide`.)

Generators of the three classical maximal subgroups of `M₂₄` that the MOG makes visible, in the
GLM's labelling of the 24 cells, with their orbits certified by the Round 32 tool (`certOK`).

* **The octad stabiliser** `octStab` fixes the octad `theOctad`.  On the cells it has two orbits
  (the 8 cells of the octad, the other 16: `octStab_cells_in`, `octStab_cells_out`).  On the
  759 octads it has four orbits, by how many cells they share with `theOctad`: 8, 0, 4, 2 cells,
  sizes 1, 30, 280, 448 (`octStab_octads_meet`, `octStab_octads_sizes`).
* **The sextet stabiliser** `sexStab` permutes the six tetrads of the sextet `tetrads` (any two of
  them make an octad: `sextet_facts`).  It is transitive on the cells; on the octads it has three
  orbits: unions of two tetrads (15), octads meeting some tetrad in 3 cells (384), the rest (360)
  (`sexStab_octads_…`).
* **The trio stabiliser** `trioStab` permutes the three disjoint octads `trio`.  It is transitive
  on the cells; on the octads it has three orbits: the trio (3), octads disjoint from a trio
  octad (84), the rest (672) (`trioStab_octads_…`).

Every generator is an automorphism of the GLM code (`…_preserve`), so each orbit lies inside a
`M₂₄` orbit of the census.  **Not proved here:** that these generators give the *whole*
stabilisers (orders 322560, 138240, 64512).  That would follow from `|M₂₄| = 244823040` by the
orbit–stabiliser theorem, together with a proof that the generated subgroups are the full
stabilisers; `|M₂₄|` itself is not certified in this package (measured only, by a randomised
Schreier–Sims run; `EMP`).
-/

namespace GLM.Rule30.Mathieu
namespace MOG

/-! ## Generators -/

/-- Octad stabiliser generator 0. -/
def oS0 : Equiv.Perm (Fin 24) :=
  ⟨tbl [19, 12, 8, 21, 0, 4, 15, 20, 23, 2, 7, 10, 17, 18, 16, 3, 13, 22, 14, 5, 11, 6, 1, 9],
   tbl [4, 22, 9, 15, 5, 19, 21, 10, 2, 23, 11, 20, 1, 16, 18, 6, 14, 12, 13, 0, 7, 3, 17, 8],
   by decide, by decide⟩

/-- Octad stabiliser generator 1. -/
def oS1 : Equiv.Perm (Fin 24) :=
  ⟨tbl [20, 16, 10, 23, 8, 0, 4, 5, 9, 3, 7, 11, 22, 13, 1, 2, 18, 12, 17, 19, 15, 6, 14, 21],
   tbl [5, 14, 15, 9, 6, 7, 21, 10, 4, 8, 2, 11, 17, 13, 22, 20, 1, 18, 16, 19, 0, 23, 12, 3],
   by decide, by decide⟩

/-- Sextet stabiliser generator 0. -/
def sS0 : Equiv.Perm (Fin 24) :=
  ⟨tbl [13, 16, 1, 11, 8, 4, 23, 7, 5, 14, 6, 3, 18, 17, 22, 15, 0, 2, 9, 20, 19, 12, 21, 10],
   tbl [16, 2, 17, 11, 5, 8, 10, 7, 4, 18, 23, 3, 21, 0, 9, 15, 1, 13, 12, 20, 19, 22, 14, 6],
   by decide, by decide⟩

/-- Sextet stabiliser generator 1. -/
def sS1 : Equiv.Perm (Fin 24) :=
  ⟨tbl [20, 6, 3, 4, 9, 2, 16, 0, 21, 11, 17, 5, 10, 23, 15, 18, 13, 14, 12, 7, 8, 19, 1, 22],
   tbl [7, 22, 5, 2, 3, 11, 1, 19, 20, 4, 12, 9, 18, 16, 17, 14, 6, 10, 15, 21, 0, 8, 23, 13],
   by decide, by decide⟩

/-- Sextet stabiliser generator 2. -/
def sS2 : Equiv.Perm (Fin 24) :=
  ⟨tbl [19, 17, 3, 15, 7, 8, 14, 4, 5, 20, 12, 23, 18, 22, 16, 13, 2, 0, 21, 10, 6, 11, 9, 1],
   tbl [17, 23, 16, 2, 7, 8, 20, 4, 5, 22, 19, 21, 10, 15, 6, 3, 14, 1, 12, 0, 9, 18, 13, 11],
   by decide, by decide⟩

/-- Sextet stabiliser generator 3. -/
def sS3 : Equiv.Perm (Fin 24) :=
  ⟨tbl [4, 15, 8, 14, 22, 16, 0, 18, 17, 5, 21, 1, 10, 23, 6, 9, 11, 20, 19, 12, 13, 7, 3, 2],
   tbl [6, 11, 23, 22, 0, 9, 14, 21, 2, 15, 12, 16, 19, 20, 3, 1, 5, 8, 7, 18, 17, 10, 4, 13],
   by decide, by decide⟩

/-- Trio stabiliser generator 0. -/
def tS0 : Equiv.Perm (Fin 24) :=
  ⟨tbl [5, 14, 7, 0, 4, 15, 19, 10, 8, 23, 9, 2, 16, 17, 12, 21, 13, 18, 1, 3, 11, 6, 22, 20],
   tbl [3, 18, 11, 19, 4, 0, 21, 2, 8, 10, 7, 20, 14, 16, 1, 5, 12, 13, 17, 6, 23, 15, 22, 9],
   by decide, by decide⟩

/-- Trio stabiliser generator 1. -/
def tS1 : Equiv.Perm (Fin 24) :=
  ⟨tbl [17, 5, 10, 18, 16, 22, 14, 2, 20, 7, 9, 8, 0, 3, 4, 1, 6, 21, 19, 13, 23, 12, 15, 11],
   tbl [12, 15, 7, 13, 14, 1, 16, 9, 11, 10, 2, 23, 21, 19, 6, 22, 4, 0, 3, 18, 8, 17, 5, 20],
   by decide, by decide⟩

/-- Trio stabiliser generator 2. -/
def tS2 : Equiv.Perm (Fin 24) :=
  ⟨tbl [4, 13, 20, 3, 5, 6, 21, 2, 11, 9, 8, 7, 17, 22, 16, 19, 1, 14, 18, 0, 23, 15, 12, 10],
   tbl [19, 16, 7, 3, 0, 4, 5, 11, 10, 9, 23, 8, 22, 1, 17, 21, 14, 12, 18, 15, 2, 6, 13, 20],
   by decide, by decide⟩

/-- Trio stabiliser generator 3. -/
def tS3 : Equiv.Perm (Fin 24) :=
  ⟨tbl [15, 10, 18, 3, 6, 21, 5, 16, 12, 14, 1, 22, 23, 20, 8, 19, 11, 7, 9, 4, 17, 0, 2, 13],
   tbl [21, 10, 22, 3, 19, 6, 4, 17, 14, 18, 1, 16, 8, 23, 9, 0, 7, 20, 2, 15, 13, 5, 11, 12],
   by decide, by decide⟩

/-- The octad stabiliser generators. -/
def octStab : List (Equiv.Perm (Fin 24)) := [oS0, oS1]
/-- The sextet stabiliser generators. -/
def sexStab : List (Equiv.Perm (Fin 24)) := [sS0, sS1, sS2, sS3]
/-- The trio stabiliser generators. -/
def trioStab : List (Equiv.Perm (Fin 24)) := [tS0, tS1, tS2, tS3]

/-- The octad fixed by `octStab`. -/
def theOctad : ℕ := 4681730
/-- The six tetrads of the sextet fixed by `sexStab`. -/
def tetrads : List ℕ := [432, 28674, 1574920, 2097669, 4653056, 8422464]
/-- The three disjoint octads fixed by `trioStab`. -/
def trio : List ℕ := [2654329, 4681730, 9441156]

/-! ## The generators are code automorphisms and fix their structures -/

theorem preserve_of_all {gens : List (Equiv.Perm (Fin 24))} (h : gens.all rowsOK = true) :
    ∀ g ∈ gens, PreservesCode g := fun g hg =>
  (preservesCode_iff_rows g).2 (List.all_eq_true.1 h g hg)

theorem octStab_preserve : ∀ g ∈ octStab, PreservesCode g := preserve_of_all (by native_decide)
theorem sexStab_preserve : ∀ g ∈ sexStab, PreservesCode g := preserve_of_all (by native_decide)
theorem trioStab_preserve : ∀ g ∈ trioStab, PreservesCode g := preserve_of_all (by native_decide)

/-- `theOctad` is an octad, and the octad stabiliser fixes it. -/
theorem octad_facts : theOctad ∈ code ∧ weight theOctad = 8 ∧
    ∀ g ∈ octStab, pmask g theOctad = theOctad := by
  refine ⟨(mem_code_iff _).2 (by native_decide), by native_decide, ?_⟩
  have h : octStab.all (fun g => pmask g theOctad == theOctad) = true := by native_decide
  intro g hg
  simpa using List.all_eq_true.1 h g hg

/-- The sextet: six disjoint tetrads covering the 24 cells, any two forming an octad; the sextet
stabiliser permutes them. -/
theorem sextet_facts :
    tetrads.all (fun t => weight t == 4) = true ∧
    tetrads.foldl (· ^^^ ·) 0 = 2 ^ 24 - 1 ∧
    tetrads.all (fun t => tetrads.all (fun t' => t == t' || (t &&& t' == 0 && isCode (t ||| t')))) = true ∧
    ∀ g ∈ sexStab, ∀ t ∈ tetrads, pmask g t ∈ tetrads := by
  refine ⟨by native_decide, by native_decide, by native_decide, ?_⟩
  have h : sexStab.all (fun g => tetrads.all (fun t => tetrads.contains (pmask g t))) = true := by
    native_decide
  intro g hg t ht
  have := List.all_eq_true.1 (List.all_eq_true.1 h g hg) t ht
  simpa using this

/-- The trio: three pairwise disjoint octads; the trio stabiliser permutes them. -/
theorem trio_facts :
    trio.all (fun o => isCode o && weight o == 8) = true ∧
    trio.foldl (· ^^^ ·) 0 = 2 ^ 24 - 1 ∧
    ∀ g ∈ trioStab, ∀ o ∈ trio, pmask g o ∈ trio := by
  refine ⟨by native_decide, by native_decide, ?_⟩
  have h : trioStab.all (fun g => trio.all (fun o => trio.contains (pmask g o))) = true := by
    native_decide
  intro g hg o ho
  have := List.all_eq_true.1 (List.all_eq_true.1 h g hg) o ho
  simpa using this

/-! ## Orbit checks for any generator list -/

/-- The orbit certificate of `x` under `gens`, checked, and its values compared with `T`. -/
def orbitCheckG (gens : List (Equiv.Perm (Fin 24))) (T : List ℕ) (x : ℕ) : Bool :=
  let c := bfsCert gens x
  certOK gens x c &&
    (T.mergeSort (fun a b => decide (a ≤ b)) == (certValues c).mergeSort (fun a b => decide (a ≤ b)))

/-- `T` is closed under the generators. -/
def closedG (gens : List (Equiv.Perm (Fin 24))) (T : List ℕ) : Bool :=
  gens.all (fun g => T.all (fun y => T.contains (pmask g y)))

theorem orbit_eq_of_checkG {gens : List (Equiv.Perm (Fin 24))} {T : List ℕ} {x : ℕ}
    (h : orbitCheckG gens T x = true) (hx : x ∈ T) (hT : closedG gens T = true) (y : ℕ) :
    Reach gens x y ↔ y ∈ T := by
  constructor
  · refine fun hr => reach_invariant (· ∈ T) (fun g hg z hz => ?_) hx hr
    have := List.all_eq_true.1 (List.all_eq_true.1 hT g hg) z hz
    simpa using this
  · intro hy
    simp only [orbitCheckG, Bool.and_eq_true, beq_iff_eq] at h
    apply reach_of_mem_certValues h.1
    rw [← List.mem_mergeSort (le := fun a b => decide (a ≤ b)), ← h.2, List.mem_mergeSort]
    exact hy

/-! ## Orbits of the octad stabiliser -/

/-- The cells of `theOctad`, and the other cells, as one-cell patterns. -/
def cellsIn : List ℕ := ((List.range 24).filter (fun i => theOctad.testBit i)).map (2 ^ ·)
def cellsOut : List ℕ := ((List.range 24).filter (fun i => !theOctad.testBit i)).map (2 ^ ·)

theorem octStab_cells_in (y : ℕ) : Reach octStab 2 y ↔ y ∈ cellsIn :=
  orbit_eq_of_checkG (by native_decide) (by native_decide) (by native_decide) y

theorem octStab_cells_out (y : ℕ) : Reach octStab 1 y ↔ y ∈ cellsOut :=
  orbit_eq_of_checkG (by native_decide) (by native_decide) (by native_decide) y

theorem cells_sizes : cellsIn.length = 8 ∧ cellsOut.length = 16 := by native_decide

/-- Octads sharing exactly `m` cells with `O`. -/
def octadsMeeting (O m : ℕ) : List ℕ := (codeTargets 8).filter (fun y => weight (y &&& O) == m)

theorem mem_octadsMeeting {O m y : ℕ} :
    y ∈ octadsMeeting O m ↔ y ∈ code ∧ weight y = 8 ∧ weight (y &&& O) = m := by
  simp [octadsMeeting, mem_codeTargets, and_assoc]

/-- **The octad stabiliser on the octads**: four orbits, by the number of cells shared with
`theOctad` (8, 0, 4 or 2). -/
theorem octStab_octads_meet (y : ℕ) :
    (Reach octStab 4681730 y ↔ y ∈ code ∧ weight y = 8 ∧ weight (y &&& theOctad) = 8) ∧
    (Reach octStab 36125 y ↔ y ∈ code ∧ weight y = 8 ∧ weight (y &&& theOctad) = 0) ∧
    (Reach octStab 29106 y ↔ y ∈ code ∧ weight y = 8 ∧ weight (y &&& theOctad) = 4) ∧
    (Reach octStab 9335 y ↔ y ∈ code ∧ weight y = 8 ∧ weight (y &&& theOctad) = 2) := by
  refine ⟨?_, ?_, ?_, ?_⟩ <;> rw [← mem_octadsMeeting] <;>
    exact orbit_eq_of_checkG (by native_decide) (by native_decide) (by native_decide) y

/-- The four orbit sizes: `759 = 1 + 30 + 280 + 448`, and no octad meets `theOctad` in 1, 3, 5,
6 or 7 cells. -/
theorem octStab_octads_sizes :
    (octadsMeeting theOctad 8).length = 1 ∧ (octadsMeeting theOctad 0).length = 30 ∧
    (octadsMeeting theOctad 4).length = 280 ∧ (octadsMeeting theOctad 2).length = 448 ∧
    ∀ m ∈ [1, 3, 5, 6, 7], octadsMeeting theOctad m = [] := by native_decide

/-! ## Orbits of the sextet stabiliser -/

theorem sexStab_cells (y : ℕ) : Reach sexStab 1 y ↔ y < 2 ^ 24 ∧ weight y = 1 := by
  rw [orbit_eq_of_checkG (T := targets 1 anyP) (by native_decide) (by native_decide)
    (by native_decide) y, mem_targets]
  simp [anyP]

/-- Octads that are the union of two tetrads; octads meeting some tetrad in 3 cells; the rest. -/
def sexA : List ℕ := (codeTargets 8).filter (fun y => tetrads.any (fun t => weight (y &&& t) == 4))
def sexB : List ℕ := (codeTargets 8).filter (fun y => tetrads.any (fun t => weight (y &&& t) == 3))
def sexC : List ℕ := (codeTargets 8).filter (fun y =>
  !tetrads.any (fun t => weight (y &&& t) == 4) && !tetrads.any (fun t => weight (y &&& t) == 3))

/-- **The sextet stabiliser on the octads**: three orbits, of sizes 15, 384 and 360. -/
theorem sexStab_octads (y : ℕ) :
    (Reach sexStab 29106 y ↔ y ∈ sexA) ∧ (Reach sexStab 67215 y ↔ y ∈ sexB) ∧
    (Reach sexStab 9335 y ↔ y ∈ sexC) :=
  ⟨orbit_eq_of_checkG (by native_decide) (by native_decide) (by native_decide) y,
   orbit_eq_of_checkG (by native_decide) (by native_decide) (by native_decide) y,
   orbit_eq_of_checkG (by native_decide) (by native_decide) (by native_decide) y⟩

theorem sexStab_octads_sizes : sexA.length = 15 ∧ sexB.length = 384 ∧ sexC.length = 360 := by
  native_decide

/-! ## Orbits of the trio stabiliser -/

theorem trioStab_cells (y : ℕ) : Reach trioStab 1 y ↔ y < 2 ^ 24 ∧ weight y = 1 := by
  rw [orbit_eq_of_checkG (T := targets 1 anyP) (by native_decide) (by native_decide)
    (by native_decide) y, mem_targets]
  simp [anyP]

/-- The trio octads; octads disjoint from a trio octad (but not in the trio); the rest. -/
def trioA : List ℕ := (codeTargets 8).filter (fun y => trio.contains y)
def trioB : List ℕ := (codeTargets 8).filter (fun y =>
  !trio.contains y && trio.any (fun o => weight (y &&& o) == 0))
def trioC : List ℕ := (codeTargets 8).filter (fun y => !trio.any (fun o => weight (y &&& o) == 0))

/-- **The trio stabiliser on the octads**: three orbits, of sizes 3, 84 and 672. -/
theorem trioStab_octads (y : ℕ) :
    (Reach trioStab 2654329 y ↔ y ∈ trioA) ∧ (Reach trioStab 36125 y ↔ y ∈ trioB) ∧
    (Reach trioStab 9335 y ↔ y ∈ trioC) :=
  ⟨orbit_eq_of_checkG (by native_decide) (by native_decide) (by native_decide) y,
   orbit_eq_of_checkG (by native_decide) (by native_decide) (by native_decide) y,
   orbit_eq_of_checkG (by native_decide) (by native_decide) (by native_decide) y⟩

theorem trioStab_octads_sizes : trioA.length = 3 ∧ trioB.length = 84 ∧ trioC.length = 672 := by
  native_decide

end MOG
end GLM.Rule30.Mathieu
