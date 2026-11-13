import RequestProject.GolayInvolution

/-!
# Golay codes on the cube's surface that the cube's symmetries do preserve

`GolayInvolution.lean` proved the two negative rows of the invariance table:
no Golay code on the 24 surface cells survives the full cube group `O_h`, nor
the tetrahedral group with its diagonal mirrors `T_d`.  This file proves the two
positive rows, in the same language — as statements about `IsGolay` codes and
the action `c ↦ c ∘ cellPerm g` — and one of them, the `T_h` row, was the last
claim in the package still resting on a Python search.

*The method.*  A candidate code is `Packed`: twelve 24-bit patterns together
with twelve *information cells*.  Everything needed of it is then a finite
check, and `Packed.isGolay` and `Packed.invariant` turn those checks into the
abstract statements:

* `dec_combo` — reading the information cells off a combination returns its
  coefficients.  That makes the twelve generators independent, so the code has
  dimension 12 and `4096` words, and it makes membership decidable in one step;
* `wt_mem` — every word weighs `0`, `8`, `12`, `16` or `24`.  Minimum weight 8
  and double evenness both follow;
* `orth` — the twelve generators are pairwise orthogonal, which spreads to the
  whole code by bilinearity, so the code is self-orthogonal;
* `gen_invariant` — each group element carries each generator back into the
  code, which spreads to the whole code by linearity.

*The two witnesses.*  `oPack` is preserved by the 24 rotations `O`, and
`thPack` by the 24 elements of the pyritohedral group

    T_h = { g : the axis permutation of g is even },

the tetrahedral rotations together with the inversion and the three face
mirrors.  In each case the group is proved to be the *whole* stabiliser inside
the 48-element cube group (`o_stabiliser_exact`, `th_stabiliser_exact`) — as it
must be, since anything larger would contain a diagonal mirror, which
`no_diagonal_mirror_invariant_golay` forbids.

With this file the invariance table of the reports is completely proved:

| group | order | verdict |
|---|---|---|
| `O_h` | 48 | no invariant Golay code (`no_Oh_invariant_golay`) |
| `T_d` | 24 | no invariant Golay code (`no_Td_invariant_golay`) |
| `O`   | 24 | an invariant Golay code exists (`exists_O_invariant_golay`) |
| `T_h` | 24 | an invariant Golay code exists (`exists_Th_invariant_golay`) |
-/

namespace GolayInv

open Finset CubeStab

/-! ## 1. A code packed as twelve bit patterns -/

/-- A weightless vector is the zero vector. -/
theorem eq_zero_of_wt_eq_zero {c : V} (h : wt c = 0) : c = 0 := by
  have hs : supp c = ∅ := Finset.card_eq_zero.mp h
  funext i
  simp only [Pi.zero_apply]
  have h1 : c i ≠ 1 := fun hc => by
    have hmem : i ∈ supp c := mem_supp.mpr hc
    rw [hs] at hmem
    exact absurd hmem (Finset.notMem_empty i)
  revert h1
  generalize c i = x
  revert x
  decide

/-- A candidate code: twelve generators, packed as bit patterns of the 24
coordinates, together with twelve *information cells* meant to carry the
coefficients. -/
structure Packed where
  /-- Generator `k`, bit `i` being coordinate `i`. -/
  word : Fin 12 → Nat
  /-- The information cells. -/
  info : Fin 12 → Fin 24

namespace Packed

variable (P : Packed)

/-- Generator `k`, unpacked. -/
def basis (k : Fin 12) : V := fun i => if Nat.testBit (P.word k) i.val then 1 else 0

/-- The word with coefficients `m`. -/
def combo (m : Fin 12 → ZMod 2) : V := ∑ k, m k • P.basis k

theorem combo_apply (m : Fin 12 → ZMod 2) (i : Fin 24) :
    P.combo m i = ∑ k, m k * P.basis k i := by
  simp [combo, Finset.sum_apply]

/-- Reading the coefficients back off a vector. -/
def dec (c : V) : Fin 12 → ZMod 2 := fun k => c (P.info k)

/-- Membership, decidably: a vector is a word of the code exactly when it is the
combination of its own information cells. -/
def mem (c : V) : Bool := decide (P.combo (P.dec c) = c)

/-- The code the twelve generators span. -/
def code : Submodule (ZMod 2) V := Submodule.span (ZMod 2) (Set.range P.basis)

theorem mem_code_iff {c : V} : c ∈ P.code ↔ ∃ m, P.combo m = c :=
  Submodule.mem_span_range_iff_exists_fun _

variable {P}

theorem mem_iff (hdec : ∀ m, P.dec (P.combo m) = m) {c : V} :
    P.mem c = true ↔ c ∈ P.code := by
  constructor
  · intro h
    exact P.mem_code_iff.mpr ⟨P.dec c, of_decide_eq_true h⟩
  · intro h
    obtain ⟨m, rfl⟩ := P.mem_code_iff.mp h
    simp [mem, hdec m]

theorem linearIndependent (hdec : ∀ m, P.dec (P.combo m) = m) :
    LinearIndependent (ZMod 2) P.basis := by
  rw [Fintype.linearIndependent_iff]
  intro g hg i
  have h := hdec g
  rw [show P.combo g = 0 from hg] at h
  rw [← h]
  simp [dec]

theorem finrank_code (hdec : ∀ m, P.dec (P.combo m) = m) :
    Module.finrank (ZMod 2) P.code = 12 := by
  rw [code, finrank_span_eq_card (linearIndependent hdec)]
  simp

/-- The dot product against a combination, expanded. -/
theorem dotp_combo (m : Fin 12 → ZMod 2) (d : V) :
    dotp (P.combo m) d = ∑ k, m k * dotp (P.basis k) d := by
  simp only [dotp, combo_apply, Finset.sum_mul, Finset.mul_sum]
  rw [Finset.sum_comm]
  exact Finset.sum_congr rfl fun k _ => Finset.sum_congr rfl fun i _ => by ring

/-- Orthogonal generators make a self-orthogonal code. -/
theorem selfOrth (horth : ∀ k l : Fin 12, dotp (P.basis k) (P.basis l) = 0) :
    ∀ c ∈ P.code, ∀ d ∈ P.code, dotp c d = 0 := by
  intro c hc d hd
  obtain ⟨m, rfl⟩ := P.mem_code_iff.mp hc
  obtain ⟨m', rfl⟩ := P.mem_code_iff.mp hd
  rw [dotp_combo]
  refine Finset.sum_eq_zero fun k _ => ?_
  have hk : dotp (P.basis k) (P.combo m') = 0 := by
    rw [show dotp (P.basis k) (P.combo m') = dotp (P.combo m') (P.basis k) from by
      simp [dotp, mul_comm], dotp_combo]
    exact Finset.sum_eq_zero fun l _ => by rw [horth, mul_zero]
  rw [hk, mul_zero]

/-- **The three finite checks make the packed code a Golay code.** -/
theorem isGolay (hdec : ∀ m, P.dec (P.combo m) = m)
    (hwt : ∀ m : Fin 12 → ZMod 2, wt (P.combo m) = 0 ∨ wt (P.combo m) = 8 ∨
      wt (P.combo m) = 12 ∨ wt (P.combo m) = 16 ∨ wt (P.combo m) = 24)
    (horth : ∀ k l : Fin 12, dotp (P.basis k) (P.basis l) = 0) : IsGolay P.code where
  dim := finrank_code hdec
  selfOrth := selfOrth horth
  minWt := by
    intro c hc hne
    obtain ⟨m, rfl⟩ := P.mem_code_iff.mp hc
    rcases hwt m with h | h | h | h | h
    · exact absurd (eq_zero_of_wt_eq_zero h) hne
    all_goals omega
  doublyEven := by
    intro c hc
    obtain ⟨m, rfl⟩ := P.mem_code_iff.mp hc
    rcases hwt m with h | h | h | h | h <;> rw [h] <;> decide

/-- **A symmetry that fixes every generator fixes the whole code.** -/
theorem invariant (hdec : ∀ m, P.dec (P.combo m) = m) {g : CubeSym}
    (hgen : ∀ k : Fin 12, P.mem (fun i => P.basis k (cellPerm g i)) = true) :
    ∀ c ∈ P.code, (fun i => c (cellPerm g i)) ∈ P.code := by
  intro c hc
  obtain ⟨m, rfl⟩ := P.mem_code_iff.mp hc
  have hsum : (fun i => P.combo m (cellPerm g i))
      = ∑ k, m k • (fun i => P.basis k (cellPerm g i) : V) := by
    funext i
    simp [combo_apply, Finset.sum_apply]
  rw [hsum]
  refine Submodule.sum_mem _ fun k _ => Submodule.smul_mem _ _ ?_
  exact (mem_iff hdec).mp (hgen k)

end Packed

/-! ## 2. A code the rotation group preserves -/

/-- The witness for the rotation group `O`: twelve generators in reduced row
echelon form, with their pivots as information cells. -/
def oPack : Packed where
  word := fun k =>
    [8455026, 4261422, 2163991, 1118020, 592995, 330073,
     199221, 34635, 19230, 11565, 7800, 255].getD k.val 0
  info := fun k =>
    ⟨[23, 22, 21, 20, 19, 18, 17, 15, 14, 13, 12, 7].getD k.val 0, by
      have := k.isLt
      interval_cases h : k.val <;> simp⟩

theorem oPack_dec : ∀ m, oPack.dec (oPack.combo m) = m := by native_decide

theorem oPack_wt : ∀ m : Fin 12 → ZMod 2, wt (oPack.combo m) = 0 ∨ wt (oPack.combo m) = 8 ∨
    wt (oPack.combo m) = 12 ∨ wt (oPack.combo m) = 16 ∨ wt (oPack.combo m) = 24 := by
  native_decide

theorem oPack_orth : ∀ k l : Fin 12, dotp (oPack.basis k) (oPack.basis l) = 0 := by native_decide

/-- **The rotation witness is a Golay code.** -/
theorem oPack_isGolay : IsGolay oPack.code := Packed.isGolay oPack_dec oPack_wt oPack_orth

/-- Each of the 24 rotations carries each generator back into the code. -/
theorem oPack_gen_invariant :
    ∀ g : CubeSym, IsRot g = true → ∀ k : Fin 12,
      oPack.mem (fun i => oPack.basis k (cellPerm g i)) = true := by native_decide

/-- **The third row of the invariance table.**  There is a Golay code on the
cube's surface invariant under all 24 rotations. -/
theorem exists_O_invariant_golay :
    ∃ C : Submodule (ZMod 2) V, IsGolay C ∧
      ∀ g : CubeSym, IsRot g = true → ∀ c ∈ C, (fun i => c (cellPerm g i)) ∈ C :=
  ⟨oPack.code, oPack_isGolay, fun g hg => Packed.invariant oPack_dec (oPack_gen_invariant g hg)⟩

/-- **And the rotations are its whole stabiliser**: every reflection carries some
generator out of it. -/
theorem o_stabiliser_exact :
    ∀ g : CubeSym, IsRot g = false →
      ∃ k : Fin 12, oPack.mem (fun i => oPack.basis k (cellPerm g i)) = false := by
  native_decide

/-! ## 3. A code the pyritohedral group preserves -/

/-- The witness for the pyritohedral group `T_h`. -/
def thPack : Packed where
  word := fun k =>
    [8455725, 4264554, 2163483, 1120006, 594253, 329059,
     201844, 38451, 21850, 13116, 3925, 255].getD k.val 0
  info := fun k =>
    ⟨[23, 22, 21, 20, 19, 18, 17, 15, 14, 13, 11, 7].getD k.val 0, by
      have := k.isLt
      interval_cases h : k.val <;> simp⟩

theorem thPack_dec : ∀ m, thPack.dec (thPack.combo m) = m := by native_decide

theorem thPack_wt : ∀ m : Fin 12 → ZMod 2, wt (thPack.combo m) = 0 ∨ wt (thPack.combo m) = 8 ∨
    wt (thPack.combo m) = 12 ∨ wt (thPack.combo m) = 16 ∨ wt (thPack.combo m) = 24 := by
  native_decide

theorem thPack_orth : ∀ k l : Fin 12, dotp (thPack.basis k) (thPack.basis l) = 0 := by
  native_decide

/-- **The pyritohedral witness is a Golay code.** -/
theorem thPack_isGolay : IsGolay thPack.code := Packed.isGolay thPack_dec thPack_wt thPack_orth

/-- Each of the 24 elements of `T_h` carries each generator back into the
code. -/
theorem thPack_gen_invariant :
    ∀ g : CubeSym, axEven g.1 = true → ∀ k : Fin 12,
      thPack.mem (fun i => thPack.basis k (cellPerm g i)) = true := by native_decide

/-- **The fourth row of the invariance table**, and the last claim of the
package that rested on a search.  There is a Golay code on the cube's surface
invariant under the 24-element pyritohedral group `T_h`. -/
theorem exists_Th_invariant_golay :
    ∃ C : Submodule (ZMod 2) V, IsGolay C ∧
      ∀ g : CubeSym, axEven g.1 = true → ∀ c ∈ C, (fun i => c (cellPerm g i)) ∈ C :=
  ⟨thPack.code, thPack_isGolay,
    fun g hg => Packed.invariant thPack_dec (thPack_gen_invariant g hg)⟩

/-- **And `T_h` is its whole stabiliser**: every cube symmetry with an odd axis
permutation carries some generator out of it. -/
theorem th_stabiliser_exact :
    ∀ g : CubeSym, axEven g.1 = false →
      ∃ k : Fin 12, thPack.mem (fun i => thPack.basis k (cellPerm g i)) = false := by
  native_decide

/-- The two witnesses are genuinely different placements: `T_h` contains twelve
improper symmetries — the inversion and the mirrors — which no rotation-invariant
code can afford, while `O` is all proper. -/
theorem th_contains_improper :
    (univ.filter fun g : CubeSym => axEven g.1 = true ∧ IsRot g = false).card = 12 ∧
    (univ.filter fun g : CubeSym => axEven g.1 = true).card = 24 ∧
    (univ.filter fun g : CubeSym => IsRot g = true).card = 24 := by
  refine ⟨by decide, by decide, by decide⟩

end GolayInv
