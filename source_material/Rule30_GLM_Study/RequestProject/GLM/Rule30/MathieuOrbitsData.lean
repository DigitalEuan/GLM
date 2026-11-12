import RequestProject.GLM.Rule30.MathieuOrbits

/-!
# Round 32 certificates: `M₂₄` orbits of seed patterns, and the symmetry Rule 30 keeps

(Not a `module`: the checks use `native_decide`.)

Finite checks (`native_decide`, class `CERT`) on top of the exact framework of
`MathieuOrbits.lean`.  Every statement is about the 24-cell patterns and the GLM's Golay code.

**Two generators.**  `gM0`, `gM1` are automorphisms of the GLM code (`gens_preserve`), found by a
deterministic backtracking search (`scripts/m24_search.py`).  Their words act
5-homogeneously (below), so by the classical theory (Livingstone–Wagner; the 5-transitive
subgroups of `M₂₄`) they generate all of `M₂₄`; that identification is background, not re-proved.

**Orbits of seed patterns (the enumeration tool at work).**
* `orbit_weight_one … orbit_weight_five`: every pattern with `k ≤ 5` marked cells is reached
  from `cells {0, …, k−1}`: up to 5 defects there is **one** symmetry type.
* `orbit_octads`: the orbit of an octad is exactly the 759 octads (the 8-defect arrangement of
  maximal symmetry); `orbit_dodecads`: the orbit of a dodecad is exactly the 2576 dodecads.
* `orbit_hexads_special`, `orbit_hexads_umbral`: 6 defects fall into exactly **two** types —
  inside an octad (21252 patterns) or not (113344 patterns); `hexad_types_distinct`.

**What Rule 30 keeps.**
* `no_rot_one`: for **every** labelling of the ring cells by the code coordinates, turning the
  ring by one cell is not a code automorphism (`M₂₄` contains no 24-cycle).  Proof: an octad of
  a rotation-invariant laid-out code would satisfy a weight test that only 423 of the 735471
  eight-cell patterns pass, but there are 759 octads.
* **`shared_card_le_twelve`**: for every labelling, at most 12 of the 24! permutations of the
  cells are both Rule 30 symmetries and code automorphisms.
* **`shared_card_tau0`**: 12 is attained (an explicit labelling `tau0`).
* `shared_card_glm`: in the GLM's own labelling exactly 2 are shared (the identity and the
  half-turn).
* `octad_rule30_weights`: the 759 octads — one `M₂₄` orbit — have one-step Rule 30 images with
  every weight from 6 to 21: symmetric seeds in the `M₂₄` sense do **not** have symmetric futures.
-/

namespace GLM.Rule30.Mathieu

/-! ## Two generators of `M₂₄` for the GLM code -/

/-- A map of the 24 cells given by its table of images. -/
def tbl (l : List ℕ) (i : Fin 24) : Fin 24 := Fin.ofNat 24 (l.getD i 0)

/-- First generator (the images of cells `0 … 23`, then the inverse table). -/
def gM0 : Equiv.Perm (Fin 24) :=
  ⟨tbl [1, 2, 3, 4, 5, 0, 8, 22, 23, 10, 12, 6, 21, 19, 13, 20, 14, 18, 16, 17, 9, 15, 11, 7],
   tbl [5, 0, 1, 2, 3, 4, 11, 23, 6, 20, 9, 22, 10, 14, 16, 21, 18, 19, 17, 13, 15, 12, 7, 8],
   by decide, by decide⟩

/-- Second generator. -/
def gM1 : Equiv.Perm (Fin 24) :=
  ⟨tbl [23, 22, 21, 20, 19, 0, 2, 7, 3, 10, 13, 16, 18, 5, 9, 4, 15, 11, 17, 6, 12, 8, 1, 14],
   tbl [5, 22, 6, 8, 15, 13, 19, 7, 21, 14, 9, 17, 20, 10, 23, 16, 11, 18, 12, 4, 3, 2, 1, 0],
   by decide, by decide⟩

/-- The generator list. -/
def gensM : List (Equiv.Perm (Fin 24)) := [gM0, gM1]

/-- Both generators are automorphisms of the GLM code. -/
theorem gens_preserve : ∀ g ∈ gensM, PreservesCode g := by
  have h0 : rowsOK gM0 = true := by native_decide
  have h1 : rowsOK gM1 = true := by native_decide
  intro g hg
  simp only [gensM, List.mem_cons, List.not_mem_nil, or_false] at hg
  rcases hg with rfl | rfl
  · exact (preservesCode_iff_rows _).2 h0
  · exact (preservesCode_iff_rows _).2 h1

/-! ## Enumerating all patterns with `k` marked cells -/

/-- The pattern with the cells of the list `s` marked. -/
def maskOfList (s : List (Fin 24)) : ℕ := mk24 (fun i => decide (i ∈ s))

/-- The patterns with `k` marked cells, satisfying `P`. -/
def targets (k : ℕ) (P : ℕ → Bool) : List ℕ :=
  (((List.finRange 24).sublistsLen k).map maskOfList).filter P

theorem weight_maskOfList {s : List (Fin 24)} (hs : s.Sublist (List.finRange 24)) :
    weight (maskOfList s) = s.length := by
  rw [weight_eq_card]
  have : Finset.univ.filter (fun i : Fin 24 => (maskOfList s).testBit i.val) = s.toFinset := by
    ext i; simp [maskOfList, testBit_mk24_fin]
  rw [this, List.toFinset_card_of_nodup (hs.nodup (List.nodup_finRange 24))]

theorem mem_targets {k : ℕ} {P : ℕ → Bool} {y : ℕ} :
    y ∈ targets k P ↔ y < 2 ^ 24 ∧ weight y = k ∧ P y = true := by
  simp only [targets, List.mem_filter, List.mem_map, List.mem_sublistsLen]
  constructor
  · rintro ⟨⟨s, ⟨hs, hl⟩, rfl⟩, hp⟩
    exact ⟨mk24_lt _, by rw [weight_maskOfList hs, hl], hp⟩
  · rintro ⟨hy, hw, hp⟩
    refine ⟨⟨(List.finRange 24).filter (fun i : Fin 24 => y.testBit i.val),
      ⟨List.filter_sublist, hw⟩, ?_⟩, hp⟩
    apply eq_of_cells (mk24_lt _) hy
    intro i
    simp [testBit_mk24_fin]

/-! ## Breadth-first orbit certificates -/

/-- Breadth-first search with a visited bitmap; produces a certificate for `certOK`. Its
correctness is never assumed: every certificate it returns is checked by `certOK`. -/
def bfsAux (gens : List (Equiv.Perm (Fin 24))) :
    ℕ → ℕ → Array (ℕ × ℕ × ℕ) → ByteArray → Array (ℕ × ℕ × ℕ)
  | 0, _, arr, _ => arr
  | fuel + 1, i, arr, vis =>
    if h : i < arr.size then
      let v := arr[i].1
      let r := (gens.zipIdx).foldl (fun (acc : Array (ℕ × ℕ × ℕ) × ByteArray) gk =>
          let z := pmask gk.1 v
          if acc.2.get! z == 0 then (acc.1.push (z, i, gk.2), acc.2.set! z 1) else acc) (arr, vis)
      bfsAux gens fuel (i + 1) r.1 r.2
    else arr

/-- The orbit certificate of the seed `x`. -/
def bfsCert (gens : List (Equiv.Perm (Fin 24))) (x : ℕ) : Array (ℕ × ℕ × ℕ) :=
  bfsAux gens (2 ^ 24 + 1) 0 #[(x, 0, 0)]
    ((ByteArray.mk (Array.replicate (2 ^ 24) 0)).set! x 1)

/-- One combined check: the certificate is valid, and its values, sorted, are exactly the list
`T`, sorted. -/
def orbitCheckL (T : List ℕ) (x : ℕ) : Bool :=
  let c := bfsCert gensM x
  certOK gensM x c &&
    (T.mergeSort (fun a b => decide (a ≤ b)) == (certValues c).mergeSort (fun a b => decide (a ≤ b)))

/-- From a passed check: every pattern of `T` is in the orbit of `x`. -/
theorem reach_of_orbitCheckL {T : List ℕ} {x : ℕ} (h : orbitCheckL T x = true)
    {y : ℕ} (hy : y ∈ T) : Reach gensM x y := by
  simp only [orbitCheckL, Bool.and_eq_true, beq_iff_eq] at h
  apply reach_of_mem_certValues h.1
  rw [← List.mem_mergeSort (le := fun a b => decide (a ≤ b)), ← h.2, List.mem_mergeSort]
  exact hy

/-- **The orbit is exactly the target set `T`**, when membership of `T` is kept by the
generators. -/
theorem orbit_eq_of_checkL {T : List ℕ} {x : ℕ} (h : orbitCheckL T x = true) (hx : x ∈ T)
    (hT : ∀ g ∈ gensM, ∀ y ∈ T, pmask g y ∈ T) (y : ℕ) : Reach gensM x y ↔ y ∈ T :=
  ⟨fun hr => reach_invariant (· ∈ T) hT hx hr, reach_of_orbitCheckL h⟩

/-- Target-set invariance for `targets k P`, from invariance of `P`. -/
theorem targets_invariant {k : ℕ} {P : ℕ → Bool}
    (hP : ∀ g ∈ gensM, ∀ y, P y = true → P (pmask g y) = true) :
    ∀ g ∈ gensM, ∀ y ∈ targets k P, pmask g y ∈ targets k P := by
  intro g hg z hz
  rw [mem_targets] at hz ⊢
  exact ⟨pmask_lt _ _, by rw [weight_pmask, hz.2.1], hP g hg z hz.2.2⟩

/-! ## Orbits with at most 5 marked cells: one type each -/

/-- The predicate accepting every pattern. -/
def anyP : ℕ → Bool := fun _ => true

theorem anyP_inv : ∀ g ∈ gensM, ∀ y, anyP y = true → anyP (pmask g y) = true :=
  fun _ _ _ _ => rfl

theorem check_w1 : orbitCheckL (targets 1 anyP) 1 = true := by native_decide
theorem check_w2 : orbitCheckL (targets 2 anyP) 3 = true := by native_decide
theorem check_w3 : orbitCheckL (targets 3 anyP) 7 = true := by native_decide
theorem check_w4 : orbitCheckL (targets 4 anyP) 15 = true := by native_decide
theorem check_w5 : orbitCheckL (targets 5 anyP) 31 = true := by native_decide

theorem orbit_all_of_check {k x : ℕ} (h : orbitCheckL (targets k anyP) x = true)
    (hx : x < 2 ^ 24) (hw : weight x = k) (y : ℕ) :
    Reach gensM x y ↔ y < 2 ^ 24 ∧ weight y = k := by
  rw [orbit_eq_of_checkL h (mem_targets.2 ⟨hx, hw, rfl⟩) (targets_invariant anyP_inv), mem_targets]
  simp [anyP]

/-- One marked cell: the orbit of cell `0` is all 24 cells. -/
theorem orbit_weight_one (y : ℕ) : Reach gensM 1 y ↔ y < 2 ^ 24 ∧ weight y = 1 :=
  orbit_all_of_check check_w1 (by norm_num) (by decide) y

/-- Two marked cells: one orbit (all 276 pairs). -/
theorem orbit_weight_two (y : ℕ) : Reach gensM 3 y ↔ y < 2 ^ 24 ∧ weight y = 2 :=
  orbit_all_of_check check_w2 (by norm_num) (by decide) y

/-- Three marked cells: one orbit (all 2024 triples). -/
theorem orbit_weight_three (y : ℕ) : Reach gensM 7 y ↔ y < 2 ^ 24 ∧ weight y = 3 :=
  orbit_all_of_check check_w3 (by norm_num) (by decide) y

/-- Four marked cells: one orbit (all 10626 sets). -/
theorem orbit_weight_four (y : ℕ) : Reach gensM 15 y ↔ y < 2 ^ 24 ∧ weight y = 4 :=
  orbit_all_of_check check_w4 (by norm_num) (by decide) y

/-- **Five marked cells: one orbit (all 42504 sets)** — the action is 5-homogeneous. -/
theorem orbit_weight_five (y : ℕ) : Reach gensM 31 y ↔ y < 2 ^ 24 ∧ weight y = 5 :=
  orbit_all_of_check check_w5 (by norm_num) (by decide) y

theorem targets_counts :
    (List.range 6).map (fun k => (targets k anyP).length) = [1, 24, 276, 2024, 10626, 42504] := by
  native_decide

/-! ## Octads and dodecads -/

/-- The codewords with `w` marked cells. -/
def codeTargets (w : ℕ) : List ℕ := ((List.range 4096).map golayWord).filter (fun y => weight y == w)

theorem mem_codeTargets {w y : ℕ} : y ∈ codeTargets w ↔ y ∈ code ∧ weight y = w := by
  simp [codeTargets, code]

theorem codeTargets_invariant (w : ℕ) : ∀ g ∈ gensM, ∀ y ∈ codeTargets w, pmask g y ∈ codeTargets w := by
  intro g hg y hy
  rw [mem_codeTargets] at hy ⊢
  exact ⟨gens_preserve g hg y hy.1, by rw [weight_pmask, hy.2]⟩

theorem codeTargets_counts : (codeTargets 8).length = 759 ∧ (codeTargets 12).length = 2576 ∧
    (codeTargets 8).Nodup ∧ (codeTargets 12).Nodup := by native_decide

theorem check_octads : orbitCheckL (codeTargets 8) 9335 = true := by native_decide
theorem check_dodecads : orbitCheckL (codeTargets 12) 8190 = true := by native_decide

/-- **The orbit of an octad is exactly the 759 octads** (the most symmetric 8-defect
arrangement: one orbit of minimal size). -/
theorem orbit_octads (y : ℕ) : Reach gensM 9335 y ↔ y ∈ code ∧ weight y = 8 := by
  rw [orbit_eq_of_checkL check_octads (by native_decide) (codeTargets_invariant 8), mem_codeTargets]

/-- **The orbit of a dodecad is exactly the 2576 dodecads.** -/
theorem orbit_dodecads (y : ℕ) : Reach gensM 8190 y ↔ y ∈ code ∧ weight y = 12 := by
  rw [orbit_eq_of_checkL check_dodecads (by native_decide) (codeTargets_invariant 12),
    mem_codeTargets]

/-! ## Six and seven marked cells: exactly two types each -/

theorem pmask_and (σ : Equiv.Perm (Fin 24)) (x y : ℕ) :
    pmask σ (x &&& y) = pmask σ x &&& pmask σ y := by
  apply eq_of_cells (pmask_lt _ _) (Nat.and_lt_two_pow _ (pmask_lt _ _))
  intro i
  simp only [testBit_pmask, Nat.testBit_and]

/-- `y` lies inside some octad ("special" in Conway's terms). -/
def special (y : ℕ) : Bool := (codeTargets 8).any (fun o => y &&& o == y)

theorem special_iff (y : ℕ) : special y = true ↔ ∃ o ∈ code, weight o = 8 ∧ y &&& o = y := by
  simp [special, List.any_eq_true, mem_codeTargets, and_assoc]

theorem special_pmask {g : Equiv.Perm (Fin 24)} (hg : PreservesCode g) {y : ℕ}
    (h : special y = true) : special (pmask g y) = true := by
  rw [special_iff] at h ⊢
  obtain ⟨o, ho, hw, hy⟩ := h
  exact ⟨pmask g o, hg o ho, by rw [weight_pmask, hw], by rw [← pmask_and, hy]⟩

/-- `y` is a 24-cell pattern lying in no octad ("umbral"). -/
def umbral (y : ℕ) : Bool := decide (y < 2 ^ 24) && !special y

theorem special_inv : ∀ g ∈ gensM, ∀ y, special y = true → special (pmask g y) = true :=
  fun g hg _ h => special_pmask (gens_preserve g hg) h

theorem umbral_inv : ∀ g ∈ gensM, ∀ y, umbral y = true → umbral (pmask g y) = true := by
  intro g hg y h
  simp only [umbral, Bool.and_eq_true, decide_eq_true_eq, Bool.not_eq_true'] at h ⊢
  refine ⟨pmask_lt _ _, ?_⟩
  by_contra hs
  rw [Bool.not_eq_false] at hs
  have := special_pmask (gens_preserve g hg).symm hs
  rw [pmask_symm_pmask g h.1, h.2] at this
  exact Bool.false_ne_true this

theorem check_hex_special : orbitCheckL (targets 6 special) 119 = true := by native_decide
theorem check_hex_umbral : orbitCheckL (targets 6 umbral) 63 = true := by native_decide
theorem check_hept_special : orbitCheckL (targets 7 special) 475 = true := by native_decide
theorem check_hept_umbral : orbitCheckL (targets 7 umbral) 127 = true := by native_decide

theorem types_counts : (targets 6 special).length = 21252 ∧ (targets 6 umbral).length = 113344 ∧
    (targets 7 special).length = 6072 ∧ (targets 7 umbral).length = 340032 := by native_decide

/-- Six cells inside an octad: one orbit. -/
theorem orbit_hexads_special (y : ℕ) :
    Reach gensM 119 y ↔ y < 2 ^ 24 ∧ weight y = 6 ∧ special y = true := by
  rw [orbit_eq_of_checkL check_hex_special (by native_decide) (targets_invariant special_inv),
    mem_targets]

/-- Six cells in no octad: one orbit. -/
theorem orbit_hexads_umbral (y : ℕ) :
    Reach gensM 63 y ↔ y < 2 ^ 24 ∧ weight y = 6 ∧ umbral y = true := by
  rw [orbit_eq_of_checkL check_hex_umbral (by native_decide) (targets_invariant umbral_inv),
    mem_targets]

/-- Seven cells inside an octad: one orbit. -/
theorem orbit_heptads_special (y : ℕ) :
    Reach gensM 475 y ↔ y < 2 ^ 24 ∧ weight y = 7 ∧ special y = true := by
  rw [orbit_eq_of_checkL check_hept_special (by native_decide) (targets_invariant special_inv),
    mem_targets]

/-- Seven cells in no octad: one orbit. -/
theorem orbit_heptads_umbral (y : ℕ) :
    Reach gensM 127 y ↔ y < 2 ^ 24 ∧ weight y = 7 ∧ umbral y = true := by
  rw [orbit_eq_of_checkL check_hept_umbral (by native_decide) (targets_invariant umbral_inv),
    mem_targets]

/-- The two six-cell types are different orbits (no symmetry maps one to the other). -/
theorem hexad_types_distinct : ¬ Reach gensM 119 63 := by
  rw [orbit_hexads_special]; native_decide

theorem heptad_types_distinct : ¬ Reach gensM 475 127 := by
  rw [orbit_heptads_special]; native_decide

end GLM.Rule30.Mathieu
