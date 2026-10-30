import RequestProject.GLM.Rule30.MathieuOrbitsData

/-!
# Round 32 certificates: how much of `M₂₄` Rule 30 keeps

(Not a `module`: the checks use `native_decide`.)

`MathieuOrbits.commutes_iff_rot` proved that the only permutations of the 24 ring cells that
commute with Rule 30 are the 24 rotations.  So whatever labelling `τ` places the GLM's Golay code
on the ring, the symmetries that are **both** in (the laid-out) `M₂₄` and Rule 30 symmetries are the
rotations that happen to be code automorphisms.  This file determines how many there can be.

* `no_rot_one`: for **every** labelling `τ`, turning the ring by one cell is not an automorphism
  of the laid-out code.  (Equivalently: the Golay code is not equivalent to a cyclic code, and
  `M₂₄` contains no 24-cycle.)  Proof: if it were, every laid-out octad `w` would have
  `w xor (w turned by k)` in the code for every `k`, so of weight `0, 8, 12, 16` or `24`; only
  423 of the 735471 eight-cell patterns pass that test (`survivors_count`), but the 759 octads
  would all have to pass.
* **`shared_card_le_twelve`**: for every labelling, at most 12 permutations of the 24 cells are
  shared symmetries (out of `24! ≈ 6.2·10²³` permutations and the `244823040` elements of `M₂₄`).
* **`shared_card_tau0`**: the bound 12 is attained, by the explicit labelling `tau0`, under which
  turning the ring by two cells is a code automorphism.
* `shared_card_glm`: in the GLM's own labelling (cell `i` = coordinate `i`) exactly 2 are shared:
  the identity and the half-turn by 12 cells.
* `octad_rule30_weights`, `octad_futures_differ`, `octad_cycles`: the 759 octads form one `M₂₄`
  orbit, but after one Rule 30 step their weights range over every value from 6 to 21, and their
  futures settle into cycles of different lengths.  An `M₂₄` orbit of seeds is
  therefore **not** a family of dynamically equivalent seeds.
* `single_cell_futures`: the exception is Wolfram's own seed.  The orbit of a single black cell
  is the 24 single cells, which are exactly its rotations, so all of them have the same future up
  to rotation.
-/

namespace GLM.Rule30.Mathieu

open Classical

/-! ## No labelling makes the one-cell turn a code automorphism -/

/-- The weights that codewords can have. -/
def allowedW (w : ℕ) : Bool := w == 0 || w == 8 || w == 12 || w == 16 || w == 24

/-- The test every octad of a rotation-invariant laid-out code would pass. -/
def survives (w : ℕ) : Bool :=
  (List.finRange 24).all fun k => allowedW (weight (w ^^^ pmask (rot k) w))

theorem code_weights : (List.range 4096).all (fun m => allowedW (weight (golayWord m))) = true := by
  native_decide

theorem allowed_of_code {c : ℕ} (hc : c ∈ code) : allowedW (weight c) = true := by
  obtain ⟨m, hm, rfl⟩ := hc
  exact List.all_eq_true.1 code_weights m (List.mem_range.2 hm)

/-- **Only 423 eight-cell patterns pass the rotation test.** -/
theorem survivors_count : (targets 8 survives).length = 423 := by native_decide

theorem placed_lt {τ : Equiv.Perm (Fin 24)} {a : ℕ} (ha : a ∈ placed τ) : a < 2 ^ 24 := by
  obtain ⟨c, -, rfl⟩ := ha; exact pmask_lt _ _

theorem placed_xor {τ : Equiv.Perm (Fin 24)} {a b : ℕ} (ha : a ∈ placed τ) (hb : b ∈ placed τ) :
    a ^^^ b ∈ placed τ := by
  obtain ⟨c, hc, rfl⟩ := ha
  obtain ⟨d, hd, rfl⟩ := hb
  exact ⟨c ^^^ d, xor_mem_code hc hd, pmask_xor _ _ _⟩

theorem placed_allowed {τ : Equiv.Perm (Fin 24)} {a : ℕ} (ha : a ∈ placed τ) :
    allowedW (weight a) = true := by
  obtain ⟨c, hc, rfl⟩ := ha
  rw [weight_pmask]; exact allowed_of_code hc

/-- If the one-cell turn preserves the laid-out code, so does every turn. -/
theorem preserves_all_rot {τ : Equiv.Perm (Fin 24)} (h : PreservesSet (rot 1) (placed τ)) :
    ∀ k, PreservesSet (rot k) (placed τ) := by
  have key : ∀ n : ℕ, ∀ k : Fin 24, k.val = n → PreservesSet (rot k) (placed τ) := by
    intro n
    induction n with
    | zero =>
      intro k hk
      have : k = 0 := Fin.ext hk
      subst this
      intro x hx
      have : rot 0 = 1 := by ext i; simp
      rw [this, pmask_one (placed_lt hx)]; exact hx
    | succ n ih =>
      intro k hk
      have hn : n < 24 := by omega
      have hk' : k = (⟨n, hn⟩ : Fin 24) + 1 := by
        apply Fin.ext; rw [Fin.val_add]; simp; omega
      rw [hk', ← rot_add]
      exact (ih _ rfl).mul h
  intro k; exact key _ k rfl

/-- **For every labelling of the ring, the one-cell turn is not a code automorphism.** -/
theorem no_rot_one (τ : Equiv.Perm (Fin 24)) : ¬ PreservesSet (rot 1) (placed τ) := by
  intro h
  have hall := preserves_all_rot h
  have hsub : ∀ o ∈ codeTargets 8, pmask τ o ∈ targets 8 survives := by
    intro o ho
    rw [mem_codeTargets] at ho
    have hw : pmask τ o ∈ placed τ := ⟨o, ho.1, rfl⟩
    rw [mem_targets]
    refine ⟨pmask_lt _ _, by rw [weight_pmask, ho.2], ?_⟩
    simp only [survives, List.all_eq_true]
    intro k _
    exact placed_allowed (placed_xor hw (hall k _ hw))
  obtain ⟨h759, -, hnd, -⟩ := codeTargets_counts
  have hinj : ((codeTargets 8).map (pmask τ)).Nodup := by
    apply List.Nodup.map_on _ hnd
    intro x hx y hy hxy
    exact pmask_injOn τ (code_lt (mem_codeTargets.1 hx).1) (code_lt (mem_codeTargets.1 hy).1) hxy
  have hle : ((codeTargets 8).map (pmask τ)).toFinset ⊆ (targets 8 survives).toFinset := by
    intro y hy
    simp only [List.mem_toFinset, List.mem_map] at hy ⊢
    obtain ⟨o, ho, rfl⟩ := hy
    exact hsub o ho
  have h1 := Finset.card_le_card hle
  have h2 := List.toFinset_card_le (targets 8 survives)
  rw [List.toFinset_card_of_nodup hinj, List.length_map, h759] at h1
  rw [survivors_count] at h2
  omega

/-- **At most 12 shared symmetries, for every labelling.** Of all permutations of the 24 ring
cells, at most 12 both commute with Rule 30 and are automorphisms of the laid-out Golay code. -/
theorem shared_card_le_twelve (τ : Equiv.Perm (Fin 24)) :
    (Finset.univ.filter (Shared τ)).card ≤ 12 :=
  shared_card_le_of_not_one τ (no_rot_one τ)

/-! ## The bound is attained -/

/-- A labelling under which the two-cell turn is a code automorphism: code coordinate `i` sits
at ring cell `tau0 i`. -/
def tau0 : Equiv.Perm (Fin 24) :=
  ⟨tbl [0, 1, 14, 7, 2, 15, 13, 4, 23, 6, 3, 16, 22, 12, 5, 8, 17, 20, 10, 18, 11, 21, 9, 19],
   tbl [0, 1, 4, 10, 7, 14, 9, 3, 15, 22, 18, 20, 13, 6, 2, 5, 11, 16, 19, 23, 17, 21, 12, 8],
   by decide, by decide⟩

theorem tau0_even_rows : ∀ k : Fin 24, k.val % 2 = 0 → rowsOK (tau0.symm * rot k * tau0) = true := by
  native_decide

theorem rot_injective : Function.Injective rot := by
  intro a b h
  have := congrArg (fun σ : Equiv.Perm (Fin 24) => σ 0) h
  simpa using this

/-- **Exactly 12 shared symmetries under `tau0`**: the turns by an even number of cells. -/
theorem shared_card_tau0 : (Finset.univ.filter (Shared tau0)).card = 12 := by
  apply le_antisymm (shared_card_le_twelve _)
  have hsub : (Finset.univ.filter (fun k : Fin 24 => k.val % 2 = 0)).image rot ⊆
      Finset.univ.filter (Shared tau0) := by
    intro σ hσ
    obtain ⟨k, hk, rfl⟩ := Finset.mem_image.1 hσ
    simp only [Finset.mem_filter, Finset.mem_univ, true_and] at hk ⊢
    exact ⟨rot_commutes k, (preservesSet_placed_iff _ _).2
      ((preservesCode_iff_rows _).2 (tau0_even_rows k hk))⟩
  have := Finset.card_le_card hsub
  rw [Finset.card_image_of_injective _ rot_injective] at this
  exact le_trans (by decide : 12 ≤ (Finset.univ.filter (fun k : Fin 24 => k.val % 2 = 0)).card) this

/-! ## The GLM's own labelling -/

theorem glm_rot_rows : ∀ k : Fin 24, rowsOK (rot k) = decide (k = 0 ∨ k = 12) := by native_decide

/-- **In the GLM's labelling exactly two symmetries are shared**: the identity and the half-turn. -/
theorem shared_glm_iff (σ : Equiv.Perm (Fin 24)) : Shared 1 σ ↔ σ = rot 0 ∨ σ = rot 12 := by
  rw [shared_iff, placed_one]
  constructor
  · rintro ⟨k, rfl, hk⟩
    have := (preservesCode_iff_rows _).1 hk
    rw [glm_rot_rows] at this
    rcases of_decide_eq_true this with rfl | rfl
    · left; rfl
    · right; rfl
  · rintro (rfl | rfl)
    · exact ⟨0, rfl, (preservesCode_iff_rows _).2 (by rw [glm_rot_rows]; decide)⟩
    · exact ⟨12, rfl, (preservesCode_iff_rows _).2 (by rw [glm_rot_rows]; decide)⟩

theorem shared_card_glm : (Finset.univ.filter (Shared 1)).card = 2 := by
  have : Finset.univ.filter (Shared 1) = ({0, 12} : Finset (Fin 24)).image rot := by
    ext σ
    simp only [Finset.mem_filter, Finset.mem_univ, true_and, shared_glm_iff, Finset.mem_image,
      Finset.mem_insert, Finset.mem_singleton]
    constructor
    · rintro (rfl | rfl)
      · exact ⟨0, Or.inl rfl, rfl⟩
      · exact ⟨12, Or.inr rfl, rfl⟩
    · rintro ⟨k, rfl | rfl, rfl⟩
      · left; rfl
      · right; rfl
  rw [this, Finset.card_image_of_injective _ rot_injective]
  decide

/-! ## Symmetric seeds, different futures -/

/-- **The 759 octads (one `M₂₄` orbit) after one Rule 30 step on the ring**: the number of
octads whose image has `w` black cells, for `w = 0 … 24`. -/
theorem octad_rule30_weights :
    (List.range 25).map (fun w => ((codeTargets 8).filter (fun o => weight (ring30 o) == w)).length)
      = [0, 0, 0, 0, 0, 0, 2, 2, 16, 16, 89, 72, 126, 112, 106, 72, 64, 50, 17, 10, 3, 2, 0, 0, 0] := by
  native_decide

/-- Two octads related by a symmetry of `M₂₄` whose one-step Rule 30 images differ in weight. -/
theorem octad_futures_differ :
    Reach gensM 9335 19003 ∧ weight (ring30 9335) = 10 ∧ weight (ring30 19003) = 11 := by
  refine ⟨(orbit_octads _).2 ⟨(mem_code_iff _).2 (by native_decide), by native_decide⟩,
    by native_decide, by native_decide⟩

/-- **Same orbit, different cycles.** Three octads (one `M₂₄` orbit) whose Rule 30 futures on the
ring settle into repetitions of different lengths: `55512` returns to itself after 5448 steps,
`101266` repeats with period dividing 102 from step 1872 on, and `9335` repeats with period
dividing 185040 from step 89 on.  (That 5448, 102 and 185040 are the exact cycle lengths, and that
712, 8 and 39 of the 759 octads reach the three cycles, is computed in
`scripts/m24_rule30_octads.c`, EMP.) -/
theorem octad_cycles :
    (55512 ∈ codeTargets 8 ∧ 101266 ∈ codeTargets 8 ∧ 9335 ∈ codeTargets 8) ∧
    ring30^[5448] 55512 = 55512 ∧
    ring30^[1872 + 102] 101266 = ring30^[1872] 101266 ∧
    ring30^[89 + 185040] 9335 = ring30^[89] 9335 := by
  native_decide

/-- The single black cell moved by the turn `i` is the cell `i`. -/
theorem single_cells : ∀ i : Fin 24, pmask (rot i) 1 = 2 ^ (i : ℕ) := by native_decide

/-- **Wolfram's seed is the exception**: the `M₂₄` orbit of a single black cell (all 24 single
cells, `orbit_weight_one`) consists of its rotations, so every member has the same Rule 30
future up to that rotation. -/
theorem single_cell_futures (i : Fin 24) (n : ℕ) :
    ring30^[n] (2 ^ (i : ℕ)) = pmask (rot i) (ring30^[n] 1) := by
  rw [← single_cells]; exact rot_transport i n (by norm_num)

end GLM.Rule30.Mathieu
