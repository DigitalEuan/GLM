/-
# The shortest tag: how many tag bits a tie needs

The formal half of `studies/SHORTEST_TAG_STUDY.md` (Phase 135).
`DesignedSubstrate.lean` gave the GLM a seven-bit sender tag and
`ProtectedTag.lean` an eleven- and a fifteen-bit tag carrying codes of their
own. Phase 134 left open whether shorter tags would do. This file proves the
floor every linear tag must stand on, whatever its masks.

**The floor.** A tag stage can resolve the ties of a fork only if no octad has
an all-zero tag (`mtag_separation` needs every octad's tag weight `≥ 1`).

* `octadFree_avoiding_card_le` — the Plotkin step. A set of codewords closed
  under symmetric difference that contains no octad and avoids one coordinate
  has at most `24` words: each of the other 23 coordinates is set in at most
  half of them, while every nonzero word has weight at least `12`.
* `kernel_card_ge` — a map from the code to `k` bits that is additive kills
  at least `4096 / 2ᵏ` codewords.
* `short_tag_kills_octad` — so every additive tag of at most six bits (in
  particular every mask tag) sends some octad to zero: six bits plus the
  avoided coordinate leave at least `32 > 24` codewords in that set, so one
  of them is an octad.
* `tag_length_floor` — if every octad's `r`-bit tag has weight at least
  `D ≥ 1`, then `r ≥ D + 6`: forgetting `D − 1` tag bits leaves a tag of
  `r − D + 1` bits that still gives every octad a nonzero tag.
* `tag7_shortest` — the seven-bit tag of Phase 133 is therefore the shortest
  tag that resolves every tie. In general a tag correcting one flipped bit
  (`D = 3`) needs at least nine bits, and one correcting two (`D = 5`) at
  least eleven (`protected_tag_floors`).

**Tags built on the seven-bit tag.** The protected tags of Phase 134 are
parities of the seven tag bits (`tag11_built`, `tag15_built`). For every tag of
that shape the floor is the coding bound, and it is met:

* `tag7_octads_onto` — a seven-bit tag that gives every octad a nonzero value
  takes all `127` nonzero values on the octads (a coset of its kernel without
  an octad would make a closed octad-free set of `64` codewords).
* `built_tag_floor` — so a tag `L ∘ T` giving every octad weight `≥ 3` is a
  `[r, 7, 3]` code and needs `r ≥ 11` (sphere packing); weight `≥ 5` makes it
  a `[r, 7, 5]` code and needs `r ≥ 15` (`no_14_7_5`: the parity extension, a
  residual of nine positions, and the first moment).
* `protected_tags_shortest_of_shape` — the eleven- and fifteen-bit protected
  tags are the shortest tags of their shape. Whether a tag *not* built on
  seven bits could be shorter (nine or ten bits for `D = 3`, eleven to
  fourteen for `D = 5`) is not settled here; the study reports a search.
-/
import Mathlib
import RequestProject.GLM.ProtectedTag

namespace GLM.Golay24

open Finset

/-! ## 1. The Plotkin step -/

/-- In a set of words closed under symmetric difference, a coordinate is set
in at most half the words. -/
theorem two_mul_card_mem_le (K : Finset Word)
    (hcl : ∀ a ∈ K, ∀ b ∈ K, symmDiff a b ∈ K) (j : Fin 24) :
    2 * #(K.filter fun c => j ∈ c) ≤ #K := by
  by_cases hy : ∃ y ∈ K, j ∈ y
  · obtain ⟨y, hyK, hjy⟩ := hy
    have hinj : #(K.filter fun c => j ∈ c) ≤ #(K.filter fun c => j ∉ c) := by
      apply Finset.card_le_card_of_injOn (fun c => symmDiff c y)
      · intro c hc
        simp only [Finset.coe_filter, Set.mem_setOf_eq] at hc ⊢
        refine ⟨hcl c hc.1 y hyK, ?_⟩
        rw [Finset.mem_symmDiff]
        tauto
      · intro a _ b _ hab
        exact symmDiff_left_injective y hab
    have := Finset.card_filter_add_card_filter_not (s := K) (fun c => j ∈ c)
    omega
  · push_neg at hy
    have : (K.filter fun c => j ∈ c) = ∅ := by
      rw [Finset.filter_eq_empty_iff]; exact hy
    rw [this]; simp

/-- **The Plotkin step.** A set of codewords closed under symmetric
difference, containing no octad and avoiding coordinate `j₀`, has at most
`24` words. -/
theorem octadFree_avoiding_card_le (K : Finset Word) (hK : ∀ c ∈ K, IsCodeword c)
    (hcl : ∀ a ∈ K, ∀ b ∈ K, symmDiff a b ∈ K) (hfree : ∀ c ∈ K, wt c ≠ 8)
    (j₀ : Fin 24) (hav : ∀ c ∈ K, j₀ ∉ c) : #K ≤ 24 := by
  -- double counting: the total weight is the sum over coordinates
  have hdc : ∑ c ∈ K, wt c = ∑ j : Fin 24, #(K.filter fun c => j ∈ c) := by
    unfold wt
    simp_rw [Finset.card_filter]
    rw [Finset.sum_comm]
    refine Finset.sum_congr rfl fun c _ => ?_
    rw [← Finset.card_filter, Finset.filter_mem_eq_inter, Finset.univ_inter]
  -- upper bound: each coordinate other than `j₀` is set in at most half the words
  have hup : 2 * ∑ c ∈ K, wt c ≤ 23 * #K := by
    rw [hdc, Finset.mul_sum]
    have hj₀ : (K.filter fun c => j₀ ∈ c) = ∅ := by
      rw [Finset.filter_eq_empty_iff]; exact hav
    rw [← Finset.add_sum_erase _ _ (Finset.mem_univ j₀), hj₀]
    have : ∑ j ∈ (univ : Finset (Fin 24)).erase j₀, 2 * #(K.filter fun c => j ∈ c)
        ≤ ∑ j ∈ (univ : Finset (Fin 24)).erase j₀, #K :=
      Finset.sum_le_sum fun j _ => two_mul_card_mem_le K hcl j
    simp only [Finset.sum_const, Finset.card_erase_of_mem (Finset.mem_univ j₀),
      Finset.card_univ, Fintype.card_fin, smul_eq_mul] at this
    simpa using this
  -- lower bound: every nonzero word has weight at least 12
  have hlow : 12 * #(K.erase ∅) ≤ ∑ c ∈ K, wt c := by
    have h1 : ∑ c ∈ K.erase ∅, 12 ≤ ∑ c ∈ K.erase ∅, wt c := by
      refine Finset.sum_le_sum fun c hc => ?_
      obtain ⟨hne, hcK⟩ := Finset.mem_erase.1 hc
      have h8 := golay_min_weight (hK c hcK) hne
      have := hfree c hcK
      rcases golay_weight_mem (hK c hcK) with h | h | h | h | h <;> omega
    have h2 : ∑ c ∈ K.erase ∅, wt c ≤ ∑ c ∈ K, wt c :=
      Finset.sum_le_sum_of_subset (Finset.erase_subset _ _)
    simp only [Finset.sum_const, smul_eq_mul] at h1
    omega
  have hcard : #K ≤ #(K.erase ∅) + 1 := by
    have := Finset.pred_card_le_card_erase (s := K) (a := ∅)
    omega
  omega

/-! ## 2. Kernels of additive maps -/

/-- An additive map from words to `k` bits vanishes on at least `4096 / 2ᵏ`
codewords. -/
theorem kernel_card_ge {ι : Type*} [Fintype ι] [DecidableEq ι]
    (f : Word → (ι → ZMod 2)) (hf : ∀ a b, f (symmDiff a b) = f a + f b) :
    4096 ≤ 2 ^ Fintype.card ι * #(codewords.filter fun c => f c = 0) := by
  have hself : ∀ x : ι → ZMod 2, x + x = 0 := by
    intro x; funext i
    have : ∀ y : ZMod 2, y + y = 0 := by decide
    exact this (x i)
  have hfib : ∀ a ∈ codewords.image f,
      #(codewords.filter fun x => f x = a) ≤ #(codewords.filter fun c => f c = 0) := by
    intro a ha
    obtain ⟨c₀, hc₀, rfl⟩ := Finset.mem_image.1 ha
    apply Finset.card_le_card_of_injOn (fun x => symmDiff x c₀)
    · intro x hx
      simp only [Finset.coe_filter, Set.mem_setOf_eq, mem_codewords] at hx ⊢
      rw [mem_codewords] at hc₀
      refine ⟨isCodeword_symmDiff hx.1 hc₀, ?_⟩
      rw [hf, hx.2, hself]
    · intro x _ y _ hxy
      exact symmDiff_left_injective c₀ hxy
  have h1 := Finset.card_le_mul_card_image codewords _ hfib
  have h2 : #(codewords.image f) ≤ 2 ^ Fintype.card ι := by
    calc #(codewords.image f) ≤ Fintype.card (ι → ZMod 2) := Finset.card_le_univ _
      _ = 2 ^ Fintype.card ι := by simp
  rw [card_codewords] at h1
  calc 4096 ≤ _ := h1
    _ ≤ #(codewords.filter fun c => f c = 0) * 2 ^ Fintype.card ι :=
        Nat.mul_le_mul_left _ h2
    _ = _ := Nat.mul_comm _ _

/-! ## 3. Six bits are not enough -/

/-- **Every additive tag of at most six bits sends some octad to zero.** -/
theorem short_tag_kills_octad {ι : Type*} [Fintype ι] [DecidableEq ι]
    (hι : Fintype.card ι ≤ 6)
    (f : Word → (ι → ZMod 2)) (hf : ∀ a b, f (symmDiff a b) = f a + f b) :
    ∃ c, IsCodeword c ∧ wt c = 8 ∧ f c = 0 := by
  classical
  -- add the avoided coordinate `0` as one more tag bit
  let g : Word → (Option ι → ZMod 2) := fun c o =>
    match o with
    | none => if (0 : Fin 24) ∈ c then 1 else 0
    | some i => f c i
  have hg : ∀ a b, g (symmDiff a b) = g a + g b := by
    intro a b; funext o
    cases o with
    | none =>
      simp only [g, Pi.add_apply, Finset.mem_symmDiff]
      by_cases ha : (0 : Fin 24) ∈ a <;> by_cases hb : (0 : Fin 24) ∈ b <;>
        simp [ha, hb, show (1 : ZMod 2) + 1 = 0 from rfl]
    | some i => simp only [g, hf, Pi.add_apply]
  have hZ := kernel_card_ge g hg
  have hcardι : Fintype.card (Option ι) ≤ 7 := by simp; omega
  have hpow : 2 ^ Fintype.card (Option ι) ≤ 2 ^ 7 := Nat.pow_le_pow_right (by norm_num) hcardι
  have h32 : 32 ≤ #(codewords.filter fun c => g c = 0) := by
    have := le_trans hZ (Nat.mul_le_mul_right _ hpow)
    omega
  have hmem : ∀ c ∈ codewords.filter (fun c => g c = 0),
      IsCodeword c ∧ f c = 0 ∧ (0 : Fin 24) ∉ c := by
    intro c hc
    rw [Finset.mem_filter, mem_codewords] at hc
    refine ⟨hc.1, ?_, ?_⟩
    · funext i; exact congrFun hc.2 (some i)
    · intro h0
      have := congrFun hc.2 none
      simp [g, h0] at this
  by_contra hno
  push_neg at hno
  have := octadFree_avoiding_card_le (codewords.filter fun c => g c = 0)
    (fun c hc => (hmem c hc).1)
    (fun a ha b hb => by
      rw [Finset.mem_filter, mem_codewords] at ha hb ⊢
      exact ⟨isCodeword_symmDiff ha.1 hb.1, by rw [hg, ha.2, hb.2, add_zero]⟩)
    (fun c hc h8 => hno c (hmem c hc).1 h8 (hmem c hc).2.1)
    0 (fun c hc => (hmem c hc).2.2)
  omega

/-- The mask tags are among them: every mask tag of at most six bits sends
some octad to zero. -/
theorem short_mtag_kills_octad (M : List ℕ) (r : ℕ) (hr : r ≤ 6) :
    ∃ c, IsCodeword c ∧ wt c = 8 ∧ mtag M r c = 0 :=
  short_tag_kills_octad (by simpa using hr) (mtag M r) (mtag_symmDiff M r)

/-- **The tag-length floor.** If every octad's `r`-bit mask tag has weight at
least `D ≥ 1`, then `r ≥ D + 6`. -/
theorem tag_length_floor (M : List ℕ) (r D : ℕ) (hD : 1 ≤ D)
    (hM : ∀ m : Fin 12 → ZMod 2, wt (encode m) = 8 → D ≤ hammingNorm (mtag M r (encode m))) :
    D + 6 ≤ r := by
  by_contra hlt
  -- forget the first `D - 1` tag bits
  let f : Word → (Fin (r - (D - 1)) → ZMod 2) := fun c j =>
    mtag M r c ⟨(j : ℕ) + (D - 1), by have := j.isLt; omega⟩
  have hf : ∀ a b, f (symmDiff a b) = f a + f b := by
    intro a b; funext j
    simp only [f, mtag_symmDiff, Pi.add_apply]
  obtain ⟨c, hc, h8, hc0⟩ := short_tag_kills_octad (by simp; omega) f hf
  obtain ⟨m, rfl⟩ := exists_encode hc
  have hD := hM m h8
  -- the surviving tag lies in the first `D - 1` bits
  have hle : hammingNorm (mtag M r (encode m)) ≤ D - 1 := by
    unfold hammingNorm
    calc #(univ.filter fun i => mtag M r (encode m) i ≠ 0)
        ≤ #(range (D - 1)) := by
          apply Finset.card_le_card_of_injOn (fun i : Fin r => (i : ℕ))
          · intro i hi
            simp only [Finset.coe_filter, Finset.mem_univ, true_and, Set.mem_setOf_eq] at hi
            simp only [Finset.coe_range, Set.mem_Iio]
            by_contra hge
            push_neg at hge
            apply hi
            have := congrFun hc0 ⟨(i : ℕ) - (D - 1), by have := i.isLt; omega⟩
            simp only [f, Pi.zero_apply] at this
            have hi' : (⟨(i : ℕ) - (D - 1) + (D - 1), by have := i.isLt; omega⟩ : Fin r) = i :=
              Fin.ext (by simp; omega)
            rw [hi'] at this
            exact this
          · intro a _ b _ hab
            exact Fin.ext hab
      _ = D - 1 := by simp
  omega

/-- **The seven-bit tag is the shortest that resolves every tie**: it gives
every octad a nonzero tag, and no tag of six or fewer bits does. -/
theorem tag7_shortest :
    (∀ m : Fin 12 → ZMod 2, wt (encode m) = 8 → 1 ≤ hammingNorm (mtag tagMasks 7 (encode m))) ∧
    ∀ (M : List ℕ) (r : ℕ),
      (∀ m : Fin 12 → ZMod 2, wt (encode m) = 8 → 1 ≤ hammingNorm (mtag M r (encode m))) →
      7 ≤ r := by
  refine ⟨fun m hm => ?_, fun M r hM => tag_length_floor M r 1 le_rfl hM⟩
  rw [Nat.one_le_iff_ne_zero, Ne, hammingNorm_eq_zero, mtag_tagMasks]
  exact tag_nonzero_on_octads m hm

/-- A tag that corrects one flipped tag bit (`D = 3`) needs at least nine
bits; one that corrects two (`D = 5`) at least eleven. -/
theorem protected_tag_floors (M : List ℕ) (r : ℕ) :
    ((∀ m : Fin 12 → ZMod 2, wt (encode m) = 8 → 3 ≤ hammingNorm (mtag M r (encode m))) →
      9 ≤ r) ∧
    ((∀ m : Fin 12 → ZMod 2, wt (encode m) = 8 → 5 ≤ hammingNorm (mtag M r (encode m))) →
      11 ≤ r) :=
  ⟨tag_length_floor M r 3 (by norm_num), tag_length_floor M r 5 (by norm_num)⟩

/-! ## 4. Tags built on a seven-bit tag

The protected tags of Phase 134 are the seven-bit tag followed by parities of
its own bits: an additive map `L` applied to a seven-bit tag. For every tag of
that shape the floor rises to the coding bound. -/

/-- A set of codewords closed under symmetric difference with no octad has at
most `48` words. -/
theorem octadFree_closed_card_le (K : Finset Word) (hK : ∀ c ∈ K, IsCodeword c)
    (hcl : ∀ a ∈ K, ∀ b ∈ K, symmDiff a b ∈ K) (hfree : ∀ c ∈ K, wt c ≠ 8) :
    #K ≤ 48 := by
  have h1 := two_mul_card_mem_le K hcl 0
  have h2 := Finset.card_filter_add_card_filter_not (s := K) (fun c => (0 : Fin 24) ∈ c)
  have h3 := octadFree_avoiding_card_le (K.filter fun c => (0 : Fin 24) ∉ c)
    (fun c hc => hK c (Finset.mem_filter.1 hc).1)
    (fun a ha b hb => by
      rw [Finset.mem_filter] at ha hb ⊢
      refine ⟨hcl a ha.1 b hb.1, ?_⟩
      rw [Finset.mem_symmDiff]; tauto)
    (fun c hc => hfree c (Finset.mem_filter.1 hc).1) 0
    (fun c hc => (Finset.mem_filter.1 hc).2)
  omega

/-- **Every value of a seven-bit tag is the tag of an octad.** Let `T` be an
additive map to seven bits that gives every octad a nonzero value. Then every
codeword's value is also the value of some octad: if a coset of the kernel
held no octad, the kernel and that coset together would be a set of at least
`64` codewords, closed and octad-free, against `octadFree_closed_card_le`. -/
theorem tag7_value_is_octad_value (T : Word → (Fin 7 → ZMod 2))
    (hT : ∀ a b, T (symmDiff a b) = T a + T b)
    (h7 : ∀ c, IsCodeword c → wt c = 8 → T c ≠ 0)
    {c : Word} (hc : IsCodeword c) (hTc : T c ≠ 0) :
    ∃ o, IsCodeword o ∧ wt o = 8 ∧ T o = T c := by
  classical
  have hself : ∀ x : Fin 7 → ZMod 2, x + x = 0 := by
    intro x; funext i
    have : ∀ y : ZMod 2, y + y = 0 := by decide
    exact this (x i)
  set K := codewords.filter fun k => T k = 0 with hKdef
  have hK32 : 32 ≤ #K := by
    have h := kernel_card_ge T hT
    simp only [Fintype.card_fin] at h
    change 4096 ≤ 2 ^ 7 * #K at h
    omega
  by_contra hno
  push_neg at hno
  have hmemK : ∀ k ∈ K, IsCodeword k ∧ T k = 0 := fun k hk => by
    rw [hKdef, Finset.mem_filter, mem_codewords] at hk; exact hk
  set K' := K ∪ K.image (fun k => symmDiff c k) with hK'def
  have hmem' : ∀ x ∈ K', IsCodeword x ∧ (T x = 0 ∨ T x = T c) := by
    intro x hx
    rcases Finset.mem_union.1 hx with h | h
    · exact ⟨(hmemK x h).1, Or.inl (hmemK x h).2⟩
    · obtain ⟨k, hk, rfl⟩ := Finset.mem_image.1 h
      refine ⟨isCodeword_symmDiff hc (hmemK k hk).1, Or.inr ?_⟩
      rw [hT, (hmemK k hk).2, add_zero]
  have hinK : ∀ x, IsCodeword x → T x = 0 → x ∈ K := fun x hx h0 => by
    rw [hKdef, Finset.mem_filter, mem_codewords]; exact ⟨hx, h0⟩
  have hcl' : ∀ a ∈ K', ∀ b ∈ K', symmDiff a b ∈ K' := by
    intro a ha b hb
    have hab := isCodeword_symmDiff (hmem' a ha).1 (hmem' b hb).1
    rcases (hmem' a ha).2 with h1 | h1 <;> rcases (hmem' b hb).2 with h2 | h2
    · exact Finset.mem_union_left _ (hinK _ hab (by rw [hT, h1, h2, add_zero]))
    · refine Finset.mem_union_right _ (Finset.mem_image.2 ⟨symmDiff c (symmDiff a b),
        hinK _ (isCodeword_symmDiff hc hab) ?_, ?_⟩)
      · rw [hT, hT, h1, h2, zero_add, hself]
      · rw [← symmDiff_assoc, symmDiff_self, bot_symmDiff]
    · refine Finset.mem_union_right _ (Finset.mem_image.2 ⟨symmDiff c (symmDiff a b),
        hinK _ (isCodeword_symmDiff hc hab) ?_, ?_⟩)
      · rw [hT, hT, h1, h2, add_zero, hself]
      · rw [← symmDiff_assoc, symmDiff_self, bot_symmDiff]
    · exact Finset.mem_union_left _ (hinK _ hab (by rw [hT, h1, h2, hself]))
  have hfree' : ∀ x ∈ K', wt x ≠ 8 := by
    intro x hx h8
    rcases (hmem' x hx).2 with h | h
    · exact h7 x (hmem' x hx).1 h8 h
    · exact hno x (hmem' x hx).1 h8 h
  have hdisj : Disjoint K (K.image fun k => symmDiff c k) := by
    rw [Finset.disjoint_left]
    intro x hxK hxI
    obtain ⟨k, hk, rfl⟩ := Finset.mem_image.1 hxI
    have := (hmemK _ hxK).2
    rw [hT, (hmemK k hk).2, add_zero] at this
    exact hTc this
  have hcardI : #(K.image fun k => symmDiff c k) = #K :=
    Finset.card_image_of_injective _ (symmDiff_right_injective c)
  have hcard' : #K' = 2 * #K := by
    rw [hK'def, Finset.card_union_of_disjoint hdisj, hcardI]; ring
  have := octadFree_closed_card_le K' (fun x hx => (hmem' x hx).1) hcl' hfree'
  omega

/-- **A seven-bit tag that gives every octad a nonzero value takes every
value on the octads.** -/
theorem tag7_octads_onto (T : Word → (Fin 7 → ZMod 2))
    (hT : ∀ a b, T (symmDiff a b) = T a + T b)
    (h7 : ∀ c, IsCodeword c → wt c = 8 → T c ≠ 0) (v : Fin 7 → ZMod 2) (hv : v ≠ 0) :
    ∃ o, IsCodeword o ∧ wt o = 8 ∧ T o = v := by
  classical
  have hself : ∀ x : Fin 7 → ZMod 2, x + x = 0 := by
    intro x; funext i
    have : ∀ y : ZMod 2, y + y = 0 := by decide
    exact this (x i)
  -- the values on the code fill all `128` vectors
  set Im := codewords.image T with hIm
  have hK48 : #(codewords.filter fun k => T k = 0) ≤ 48 := by
    apply octadFree_closed_card_le
    · intro c hc; exact mem_codewords.1 (Finset.mem_filter.1 hc).1
    · intro a ha b hb
      rw [Finset.mem_filter, mem_codewords] at ha hb ⊢
      exact ⟨isCodeword_symmDiff ha.1 hb.1, by rw [hT, ha.2, hb.2, add_zero]⟩
    · intro c hc h8
      rw [Finset.mem_filter, mem_codewords] at hc
      exact h7 c hc.1 h8 hc.2
  have hfib : ∀ a ∈ Im,
      #(codewords.filter fun x => T x = a) ≤ #(codewords.filter fun k => T k = 0) := by
    intro a ha
    obtain ⟨c₀, hc₀, rfl⟩ := Finset.mem_image.1 ha
    apply Finset.card_le_card_of_injOn (fun x => symmDiff x c₀)
    · intro x hx
      simp only [Finset.coe_filter, Set.mem_setOf_eq, mem_codewords] at hx ⊢
      rw [mem_codewords] at hc₀
      refine ⟨isCodeword_symmDiff hx.1 hc₀, ?_⟩
      rw [hT, hx.2, hself]
    · intro x _ y _ hxy
      exact symmDiff_left_injective c₀ hxy
  have h1 := Finset.card_le_mul_card_image codewords _ hfib
  rw [card_codewords] at h1
  change 4096 ≤ #(codewords.filter fun k => T k = 0) * #Im at h1
  have hIm86 : 86 ≤ #Im := by
    by_contra hlt
    push_neg at hlt
    have := Nat.mul_le_mul hK48 (Nat.le_of_lt_succ hlt)
    omega
  have hv_in : v ∈ Im := by
    by_contra hvn
    have hdisj : Disjoint Im (Im.image fun x => v + x) := by
      rw [Finset.disjoint_left]
      intro x hx hx'
      obtain ⟨y, hy, rfl⟩ := Finset.mem_image.1 hx'
      obtain ⟨cy, hcy, rfl⟩ := Finset.mem_image.1 hy
      obtain ⟨cx, hcx, hcxe⟩ := Finset.mem_image.1 hx
      apply hvn
      refine Finset.mem_image.2 ⟨symmDiff cx cy, ?_, ?_⟩
      · rw [mem_codewords] at hcx hcy ⊢; exact isCodeword_symmDiff hcx hcy
      · rw [hT, hcxe, add_assoc, hself, add_zero]
    have hcardI : #(Im.image fun x => v + x) = #Im :=
      Finset.card_image_of_injective _ (add_right_injective v)
    have hunion := Finset.card_le_univ (Im ∪ Im.image fun x => v + x)
    rw [Finset.card_union_of_disjoint hdisj, hcardI] at hunion
    simp at hunion
    omega
  obtain ⟨c, hc, rfl⟩ := Finset.mem_image.1 hv_in
  exact tag7_value_is_octad_value T hT h7 (mem_codewords.1 hc) hv

/-- The `0/1` vector of a set of tag positions. -/
def indVec {r : ℕ} (S : Finset (Fin r)) : Fin r → ZMod 2 := fun i => if i ∈ S then 1 else 0

theorem hammingNorm_indVec {r : ℕ} (S : Finset (Fin r)) : hammingNorm (indVec S) = #S := by
  unfold hammingNorm indVec
  congr 1
  ext i
  by_cases h : i ∈ S <;> simp [h]

theorem indVec_injective {r : ℕ} : Function.Injective (indVec (r := r)) := by
  intro S S' h
  ext i
  have := congrFun h i
  unfold indVec at this
  by_cases h1 : i ∈ S <;> by_cases h2 : i ∈ S' <;> simp_all

/-- The number of sets of at most `t` positions out of `r`. -/
theorem card_small_sets (r t : ℕ) :
    #((univ : Finset (Finset (Fin r))).filter fun S => #S ≤ t) =
      ∑ k ∈ range (t + 1), r.choose k := by
  have h : ((univ : Finset (Finset (Fin r))).filter fun S => #S ≤ t) =
      (range (t + 1)).biUnion fun k => (univ : Finset (Fin r)).powersetCard k := by
    ext S
    simp [Finset.mem_powersetCard]
  rw [h, Finset.card_biUnion]
  · refine Finset.sum_congr rfl fun k _ => ?_
    rw [Finset.card_powersetCard, Finset.card_univ, Fintype.card_fin]
  · intro a _ b _ hab
    rw [Function.onFun, Finset.disjoint_left]
    intro S ha hb
    rw [Finset.mem_powersetCard] at ha hb
    exact hab (ha.2.symm.trans hb.2)

set_option maxRecDepth 4000 in
/-- **Sphere packing for a tag built on seven bits.** If an additive map `L`
from seven bits to `r` bits gives every nonzero vector weight at least
`2t + 1`, the `128` balls of radius `t` around its values are disjoint. -/
theorem built_tag_packing {r : ℕ} (t : ℕ) (L : (Fin 7 → ZMod 2) → (Fin r → ZMod 2))
    (hL : ∀ u v, L (u + v) = L u + L v)
    (hmin : ∀ v, v ≠ 0 → 2 * t + 1 ≤ hammingNorm (L v)) :
    128 * ∑ k ∈ range (t + 1), r.choose k ≤ 2 ^ r := by
  classical
  have hselfr : ∀ x : Fin r → ZMod 2, x + x = 0 := by
    intro x; funext i
    have : ∀ y : ZMod 2, y + y = 0 := by decide
    exact this (x i)
  have hself7 : ∀ x : Fin 7 → ZMod 2, x + x = 0 := by
    intro x; funext i
    have : ∀ y : ZMod 2, y + y = 0 := by decide
    exact this (x i)
  set B := (univ : Finset (Finset (Fin r))).filter fun S => #S ≤ t
  have hinj : Set.InjOn (fun p : (Fin 7 → ZMod 2) × Finset (Fin r) => L p.1 + indVec p.2)
      ↑((univ : Finset (Fin 7 → ZMod 2)) ×ˢ B) := by
    rintro ⟨u, S⟩ hu ⟨u', S'⟩ hu' heq
    simp only [Finset.coe_product, Set.mem_prod, Finset.coe_univ, Set.mem_univ, true_and,
      Finset.coe_filter, Set.mem_setOf_eq, B] at hu hu' heq
    have hL' : L (u + u') = indVec S + indVec S' := by
      rw [hL]
      calc L u + L u' = (L u + indVec S) + indVec S + L u' := by
            rw [add_assoc (L u), hselfr, add_zero]
        _ = (L u' + indVec S') + indVec S + L u' := by rw [heq]
        _ = indVec S + indVec S' := by
            rw [show L u' + indVec S' + indVec S + L u' = (L u' + L u') + (indVec S + indVec S')
              by abel, hselfr, zero_add]
    have huu : u + u' = 0 := by
      by_contra hne
      have h1 := hmin _ hne
      rw [hL'] at h1
      have h2 : hammingNorm (indVec S + indVec S') ≤ hammingNorm (indVec S) + hammingNorm (indVec S') := by
        have hneg : -indVec S' = indVec S' := by
          funext i
          have : ∀ y : ZMod 2, -y = y := by decide
          exact this _
        have hsub : indVec S + indVec S' = indVec S - indVec S' := by
          rw [sub_eq_add_neg, hneg]
        have := hammingDist_triangle (indVec S) 0 (indVec S')
        rw [hammingDist_zero_right, hammingDist_zero_left, hammingDist_eq_hammingNorm] at this
        rw [hsub]
        exact this
      rw [hammingNorm_indVec, hammingNorm_indVec] at h2
      omega
    have hu_eq : u = u' := by
      have := congrArg (· + u') huu
      simpa [add_assoc, hself7] using this
    subst hu_eq
    have : indVec S = indVec S' := by
      have := congrArg (L u + ·) heq
      simpa [← add_assoc, hselfr] using heq
    rw [indVec_injective this]
  have hcard := Finset.card_le_card_of_injOn (t := (univ : Finset (Fin r → ZMod 2))) _
    (fun p _ => Finset.mem_coe.2 (Finset.mem_univ _)) hinj
  rw [Finset.card_product, Finset.card_univ, Finset.card_univ, card_small_sets] at hcard
  simpa using hcard

/-! ## 5. Fourteen bits are not enough for two flips

A tag built on seven bits that corrects two flipped bits is a `[r, 7, 5]` code.
Fourteen bits do not suffice: append the parity bit to get fifteen bits with
every nonzero weight even and at least `6`; a word of weight exactly `6` leaves
a residual of nine positions in which `64` classes sit pairwise at distance at
least `3`, too many for `2⁹`; and if every weight is at least `8` the average
weight is too large (`8 · 127 > 15 · 64`). -/

theorem card_symmDiff_eq_sdiff {α : Type*} [DecidableEq α] (s t : Finset α) :
    #(symmDiff s t) = #(s \ t) + #(t \ s) := by
  rw [symmDiff_def, Finset.sup_eq_union, Finset.card_union_of_disjoint]
  exact disjoint_sdiff_sdiff

set_option maxRecDepth 4000 in
/-- The first moment of an additive family of position sets over seven bits:
each position lies in at most half of the `128` sets. -/
theorem first_moment {n : ℕ} (P : (Fin 7 → ZMod 2) → Finset (Fin n))
    (hP : ∀ u v, P (u + v) = symmDiff (P u) (P v)) :
    ∑ v, #(P v) ≤ n * 64 := by
  classical
  have hself7 : ∀ x : Fin 7 → ZMod 2, x + x = 0 := by
    intro x; funext i
    have : ∀ y : ZMod 2, y + y = 0 := by decide
    exact this (x i)
  have hdc : ∑ v, #(P v) = ∑ j : Fin n, #(univ.filter fun v => j ∈ P v) := by
    simp_rw [Finset.card_filter]
    rw [Finset.sum_comm]
    refine Finset.sum_congr rfl fun v _ => ?_
    rw [← Finset.card_filter, Finset.filter_mem_eq_inter, Finset.univ_inter]
  have hj : ∀ j : Fin n, 2 * #(univ.filter fun v => j ∈ P v) ≤ 128 := by
    intro j
    have htot : #(univ.filter fun v => j ∈ P v) + #(univ.filter fun v => j ∉ P v) = 128 := by
      rw [Finset.card_filter_add_card_filter_not]; simp
    by_cases hy : ∃ v₁, j ∈ P v₁
    · obtain ⟨v₁, hv₁⟩ := hy
      have : #(univ.filter fun v => j ∈ P v) ≤ #(univ.filter fun v => j ∉ P v) := by
        apply Finset.card_le_card_of_injOn (fun v => v + v₁)
        · intro v hv
          simp only [Finset.coe_filter, Finset.mem_univ, true_and, Set.mem_setOf_eq] at hv ⊢
          rw [hP, Finset.mem_symmDiff]
          rintro (⟨_, h⟩ | ⟨_, h⟩)
          · exact h hv₁
          · exact h hv
        · intro a _ b _ hab
          exact add_right_cancel hab
      omega
    · push_neg at hy
      have : (univ.filter fun v => j ∈ P v) = ∅ := by
        rw [Finset.filter_eq_empty_iff]; exact fun v _ => hy v
      rw [this]; simp
  rw [hdc]
  calc ∑ j : Fin n, #(univ.filter fun v => j ∈ P v) ≤ ∑ _j : Fin n, 64 :=
        Finset.sum_le_sum fun j _ => by have := hj j; omega
    _ = n * 64 := by simp

set_option maxRecDepth 4000 in
/-- **No even `[15, 7, ≥ 6]` code.** No additive family of subsets of fifteen
positions, indexed by seven bits, gives every nonzero index an even number of
positions, at least `6`. -/
theorem no_even_15_7_6 (P : (Fin 7 → ZMod 2) → Finset (Fin 15))
    (hP : ∀ u v, P (u + v) = symmDiff (P u) (P v))
    (hw : ∀ v, v ≠ 0 → 6 ≤ #(P v) ∧ Even #(P v)) : False := by
  classical
  have hself7 : ∀ x : Fin 7 → ZMod 2, x + x = 0 := by
    intro x; funext i
    have : ∀ y : ZMod 2, y + y = 0 := by decide
    exact this (x i)
  have hP0 : P 0 = ∅ := by
    have := hP 0 0
    rw [add_zero, symmDiff_self] at this
    exact this
  by_cases h8 : ∀ v, v ≠ 0 → 8 ≤ #(P v)
  · -- the average weight is too large
    have hfm := first_moment P hP
    have hlow : 8 * 127 ≤ ∑ v, #(P v) := by
      rw [← Finset.add_sum_erase _ _ (Finset.mem_univ (0 : Fin 7 → ZMod 2)), hP0]
      have : ∑ v ∈ (univ : Finset (Fin 7 → ZMod 2)).erase 0, 8 ≤
          ∑ v ∈ (univ : Finset (Fin 7 → ZMod 2)).erase 0, #(P v) :=
        Finset.sum_le_sum fun v hv => h8 v (Finset.ne_of_mem_erase hv)
      simp only [Finset.sum_const, Finset.card_erase_of_mem (Finset.mem_univ _),
        Finset.card_univ, smul_eq_mul] at this
      simp at this ⊢
      omega
    omega
  · push_neg at h8
    obtain ⟨v₀, hv₀, hlt⟩ := h8
    have h6 : #(P v₀) = 6 := by
      obtain ⟨h1, k, hk⟩ := hw v₀ hv₀
      omega
    set S := P v₀ with hS
    -- the residual bound
    have hres : ∀ x, x ≠ 0 → x ≠ v₀ → 3 ≤ #(P x \ S) := by
      intro x hx hxv
      have hx0 : x + v₀ ≠ 0 := by
        intro h
        apply hxv
        have := congrArg (· + v₀) h
        simpa [add_assoc, hself7] using this
      have h1 := (hw x hx).1
      have h2 := (hw (x + v₀) hx0).1
      rw [hP, ← hS, card_symmDiff_eq_sdiff] at h2
      have h3 := Finset.card_sdiff_add_card_inter (P x) S
      have h4 := Finset.card_sdiff_add_card_inter S (P x)
      rw [Finset.inter_comm] at h4
      omega
    -- the packing
    set B : Finset (Finset (Fin 15)) := insert ∅ (Sᶜ.image fun i => {i})
    have hB : #B = 10 := by
      have hnot : (∅ : Finset (Fin 15)) ∉ Sᶜ.image fun i => {i} := by
        simp
      rw [Finset.card_insert_of_notMem hnot,
        Finset.card_image_of_injective _ Finset.singleton_injective, Finset.card_compl, h6]
      simp
    have hBsub : ∀ e ∈ B, e ⊆ Sᶜ ∧ #e ≤ 1 := by
      intro e he
      rcases Finset.mem_insert.1 he with rfl | he
      · simp
      · obtain ⟨i, hi, rfl⟩ := Finset.mem_image.1 he
        simpa using hi
    let F : (Fin 7 → ZMod 2) × Finset (Fin 15) → Finset (Fin 15) :=
      fun p => symmDiff (P p.1 \ S) p.2
    have himg : (((univ : Finset (Fin 7 → ZMod 2)) ×ˢ B).image F) ⊆ Sᶜ.powerset := by
      intro y hy
      obtain ⟨⟨v, e⟩, hve, rfl⟩ := Finset.mem_image.1 hy
      rw [Finset.mem_product] at hve
      rw [Finset.mem_powerset]
      intro i hi
      rcases Finset.mem_symmDiff.1 hi with ⟨hi1, _⟩ | ⟨hi1, _⟩
      · rw [Finset.mem_compl]; exact (Finset.mem_sdiff.1 hi1).2
      · exact (hBsub e hve.2).1 hi1
    have hfib : ∀ y ∈ ((univ : Finset (Fin 7 → ZMod 2)) ×ˢ B).image F,
        #(((univ : Finset (Fin 7 → ZMod 2)) ×ˢ B).filter fun p => F p = y) ≤ 2 := by
      intro y hy
      obtain ⟨⟨v₁, e₁⟩, hve₁, hF₁⟩ := Finset.mem_image.1 hy
      have hsub : (((univ : Finset (Fin 7 → ZMod 2)) ×ˢ B).filter fun p => F p = y) ⊆
          ({v₁, v₁ + v₀} : Finset (Fin 7 → ZMod 2)).image
            (fun w => (w, symmDiff (P w \ S) y)) := by
        rintro ⟨v, e⟩ hp
        rw [Finset.mem_filter, Finset.mem_product] at hp
        obtain ⟨⟨-, heB⟩, hFe⟩ := hp
        rw [Finset.mem_image]
        have he : e = symmDiff (P v \ S) y := by
          rw [← hFe]; simp only [F]
          rw [← symmDiff_assoc, symmDiff_self, bot_symmDiff]
        -- the two indices differ by `0` or `v₀`
        have hvv : v + v₁ = 0 ∨ v + v₁ = v₀ := by
          by_contra hne
          push_neg at hne
          have h3 := hres (v + v₁) hne.1 hne.2
          have hR : P (v + v₁) \ S = symmDiff e e₁ := by
            rw [Finset.mem_product] at hve₁
            have hFe' : symmDiff (P v \ S) e = symmDiff (P v₁ \ S) e₁ := by
              simp only [F] at hFe hF₁
              rw [hFe, hF₁]
            rw [hP]
            ext i
            have hi := congrArg (fun s => i ∈ s) hFe'
            simp only [Finset.mem_symmDiff, Finset.mem_sdiff, eq_iff_iff] at hi ⊢
            by_cases a : i ∈ P v <;> by_cases b : i ∈ P v₁ <;> by_cases c : i ∈ S <;>
              by_cases d : i ∈ e <;> by_cases f : i ∈ e₁ <;> simp only [a, b, c, d, f] at hi ⊢ <;>
              simp at hi ⊢
          rw [hR] at h3
          have hle : #(symmDiff e e₁) ≤ #e + #e₁ := by
            rw [card_symmDiff_eq_sdiff]
            exact Nat.add_le_add (Finset.card_le_card Finset.sdiff_subset)
              (Finset.card_le_card Finset.sdiff_subset)
          have := (hBsub e heB).2
          have := (hBsub e₁ (Finset.mem_product.1 hve₁).2).2
          omega
        refine ⟨v, ?_, by rw [he]⟩
        rcases hvv with h | h
        · have : v = v₁ := by
            have := congrArg (· + v₁) h
            simpa [add_assoc, hself7] using this
          simp [this]
        · have : v = v₁ + v₀ := by
            have := congrArg (· + v₁) h
            simp only [add_assoc, hself7, add_zero] at this
            rw [this, add_comm]
          simp [this]
      calc _ ≤ _ := Finset.card_le_card hsub
        _ ≤ #({v₁, v₁ + v₀} : Finset (Fin 7 → ZMod 2)) := Finset.card_image_le
        _ ≤ 2 := Finset.card_le_two
    have h1 := Finset.card_le_mul_card_image _ 2 hfib
    have h2 := Finset.card_le_card himg
    rw [Finset.card_powerset, Finset.card_compl, h6, Finset.card_product, hB] at *
    simp at h1 h2
    omega

/-- The positions where a vector over `ZMod 2` is nonzero. -/
def suppV {n : ℕ} (x : Fin n → ZMod 2) : Finset (Fin n) := univ.filter fun i => x i ≠ 0

theorem suppV_add {n : ℕ} (x y : Fin n → ZMod 2) :
    suppV (x + y) = symmDiff (suppV x) (suppV y) := by
  ext i
  simp only [suppV, Finset.mem_filter, Finset.mem_univ, true_and, Finset.mem_symmDiff,
    Pi.add_apply]
  generalize x i = a
  generalize y i = b
  revert a b
  decide

/-- The vector extended by its overall parity. -/
def parityExt (x : Fin 14 → ZMod 2) : Fin 15 → ZMod 2 := Fin.snoc x (∑ i, x i)

theorem parityExt_add (x y : Fin 14 → ZMod 2) :
    parityExt (x + y) = parityExt x + parityExt y := by
  funext i
  refine Fin.lastCases ?_ (fun j => ?_) i
  · simp only [parityExt, Fin.snoc_last, Pi.add_apply, Finset.sum_add_distrib]
  · simp [parityExt, Fin.snoc_castSucc]

theorem sum_eq_hammingNorm (x : Fin 14 → ZMod 2) : ∑ i, x i = (hammingNorm x : ZMod 2) := by
  have h : ∀ i, x i = if x i ≠ 0 then 1 else 0 := by
    intro i
    generalize x i = a
    revert a; decide
  rw [Finset.sum_congr rfl fun i _ => h i, Finset.sum_boole]
  rfl

theorem hammingNorm_parityExt (x : Fin 14 → ZMod 2) :
    hammingNorm (parityExt x) = hammingNorm x + (if Even (hammingNorm x) then 0 else 1) := by
  have h1 : hammingNorm (parityExt x) = ∑ i : Fin 15, if parityExt x i ≠ 0 then 1 else 0 := by
    unfold hammingNorm; rw [Finset.card_filter]
  have h2 : hammingNorm x = ∑ i : Fin 14, if x i ≠ 0 then 1 else 0 := by
    unfold hammingNorm; rw [Finset.card_filter]
  rw [h1, Fin.sum_univ_castSucc]
  simp only [parityExt, Fin.snoc_castSucc, Fin.snoc_last]
  rw [← h2, sum_eq_hammingNorm]
  congr 1
  by_cases he : Even (hammingNorm x)
  · simp [he, (ZMod.natCast_eq_zero_iff_even).2 he]
  · have : (hammingNorm x : ZMod 2) ≠ 0 := fun h => he ((ZMod.natCast_eq_zero_iff_even).1 h)
    simp [he, this]

/-- **There is no `[14, 7, 5]` code**: no additive map from seven bits to
fourteen gives every nonzero vector weight at least `5`. -/
theorem no_14_7_5 (L : (Fin 7 → ZMod 2) → (Fin 14 → ZMod 2))
    (hL : ∀ u v, L (u + v) = L u + L v)
    (hmin : ∀ v, v ≠ 0 → 5 ≤ hammingNorm (L v)) : False := by
  apply no_even_15_7_6 (fun v => suppV (parityExt (L v)))
  · intro u v
    rw [hL, parityExt_add, suppV_add]
  · intro v hv
    have hcard : #(suppV (parityExt (L v))) = hammingNorm (parityExt (L v)) := rfl
    rw [hcard, hammingNorm_parityExt]
    have h5 := hmin v hv
    by_cases he : Even (hammingNorm (L v))
    · obtain ⟨k, hk⟩ := he
      rw [if_pos ⟨k, hk⟩, add_zero]
      exact ⟨by omega, ⟨k, hk⟩⟩
    · rw [if_neg he]
      rw [Nat.not_even_iff_odd] at he
      obtain ⟨k, hk⟩ := he
      exact ⟨by omega, ⟨k + 1, by omega⟩⟩

/-- **The floor for tags built on a seven-bit tag.** Let `T` be any additive
seven-bit tag that gives every octad a nonzero value (such as the tag of
Phase 133), and `L` any additive map from seven bits to `r` bits. If every
octad's tag `L (T o)` has weight at least `3`, the tag has at least eleven
bits; at least `5`, at least fifteen. The two protected tags of Phase 134
(eleven and fifteen bits, both of this shape) are therefore the shortest of
their shape. -/
theorem built_tag_floor (T : Word → (Fin 7 → ZMod 2))
    (hT : ∀ a b, T (symmDiff a b) = T a + T b)
    (h7 : ∀ c, IsCodeword c → wt c = 8 → T c ≠ 0)
    {r : ℕ} (L : (Fin 7 → ZMod 2) → (Fin r → ZMod 2)) (hL : ∀ u v, L (u + v) = L u + L v)
    (D : ℕ) (hD : ∀ c, IsCodeword c → wt c = 8 → D ≤ hammingNorm (L (T c))) :
    (3 ≤ D → 11 ≤ r) ∧ (5 ≤ D → 15 ≤ r) := by
  have hall : ∀ v, v ≠ 0 → D ≤ hammingNorm (L v) := by
    intro v hv
    obtain ⟨o, ho, h8, rfl⟩ := tag7_octads_onto T hT h7 v hv
    exact hD o ho h8
  refine ⟨fun h3 => ?_, fun h5 => ?_⟩
  · have := built_tag_packing 1 L hL (fun v hv => by have := hall v hv; omega)
    simp [Finset.sum_range_succ] at this
    by_contra hlt
    push_neg at hlt
    interval_cases r <;> omega
  · have h14 : 14 ≤ r := by
      have := built_tag_packing 2 L hL (fun v hv => by have := hall v hv; omega)
      simp [Finset.sum_range_succ] at this
      by_contra hlt
      push_neg at hlt
      interval_cases r <;> simp [Nat.choose] at this
    by_contra hlt
    obtain rfl : r = 14 := by omega
    exact no_14_7_5 L hL fun v hv => le_trans h5 (hall v hv)

/-! ## 6. The protected tags are the shortest of their shape -/

/-- The seven-bit tag gives every octad a nonzero value. -/
theorem tag7_ne (c : Word) (hc : IsCodeword c) (h8 : wt c = 8) : tagOf c ≠ 0 := by
  obtain ⟨m, rfl⟩ := exists_encode hc
  exact tag_nonzero_on_octads m h8

/-- The additive map from seven bits to `r` bits given by a `r × 7` matrix. -/
def parityHom {r : ℕ} (A : Fin r → Fin 7 → ZMod 2) : (Fin 7 → ZMod 2) →+ (Fin r → ZMod 2) :=
  AddMonoidHom.mk' (fun v i => ∑ j, A i j * v j) (by
    intro u v; funext i
    simp [mul_add, Finset.sum_add_distrib])

/-- A matrix whose row `i` is read from the bits of `R[i]`. -/
def selMat (R : List ℕ) (r : ℕ) : Fin r → Fin 7 → ZMod 2 :=
  fun i j => if (R.getD i 0).testBit j then 1 else 0

/-- Which of the seven tag bits each bit of the eleven-bit tag is the parity
of: the seven tag bits themselves, then the four Hamming parities. -/
def selRows11 : List ℕ := [1, 2, 4, 8, 16, 32, 64, 89, 107, 86, 44]

/-- The same for the fifteen-bit tag: the seven tag bits, then the eight BCH
parities. -/
def selRows15 : List ℕ := [1, 2, 4, 8, 16, 32, 64, 11, 22, 44, 88, 59, 118, 103, 69]

/-- A mask tag whose every column is the image of the seven-bit tag's column
is that image on every word. -/
theorem mtag_eq_of_cols (M : List ℕ) (r : ℕ) (A : Fin r → Fin 7 → ZMod 2)
    (hcol : ∀ k, mtagCol M r k = parityHom A (tagCol k)) (w : Word) :
    mtag M r w = parityHom A (tagOf w) := by
  unfold mtag tagOf
  rw [map_sum]
  exact Finset.sum_congr rfl fun k _ => hcol k

/-- The eleven-bit protected tag is built on the seven-bit tag. -/
theorem tag11_built (w : Word) :
    mtag tagMasks11 11 w = parityHom (selMat selRows11 11) (tagOf w) :=
  mtag_eq_of_cols _ _ _ (by native_decide) w

/-- The fifteen-bit protected tag is built on the seven-bit tag. -/
theorem tag15_built (w : Word) :
    mtag tagMasks15 15 w = parityHom (selMat selRows15 15) (tagOf w) :=
  mtag_eq_of_cols _ _ _ (by native_decide) w

/-- **The protected tags are the shortest of their shape.** The eleven-bit
tag corrects one flipped tag bit and the fifteen-bit tag two
(`tag11_corrects_one`, `tag15_corrects_two`); both are parities of the seven
tag bits; and every tag built that way on the seven-bit tag needs at least
eleven bits to give every octad weight `3`, and fifteen for weight `5`. -/
theorem protected_tags_shortest_of_shape :
    (∀ w, mtag tagMasks11 11 w = parityHom (selMat selRows11 11) (tagOf w)) ∧
    (∀ w, mtag tagMasks15 15 w = parityHom (selMat selRows15 15) (tagOf w)) ∧
    (∀ m : Fin 12 → ZMod 2, wt (encode m) = 8 → 3 ≤ hammingNorm (mtag tagMasks11 11 (encode m))) ∧
    (∀ m : Fin 12 → ZMod 2, wt (encode m) = 8 → 5 ≤ hammingNorm (mtag tagMasks15 15 (encode m))) ∧
    ∀ {r : ℕ} (L : (Fin 7 → ZMod 2) → (Fin r → ZMod 2)), (∀ u v, L (u + v) = L u + L v) →
      ((∀ c, IsCodeword c → wt c = 8 → 3 ≤ hammingNorm (L (tagOf c))) → 11 ≤ r) ∧
      ((∀ c, IsCodeword c → wt c = 8 → 5 ≤ hammingNorm (L (tagOf c))) → 15 ≤ r) := by
  refine ⟨tag11_built, tag15_built, tag11_octad_weight, tag15_octad_weight,
    fun L hL => ⟨fun h => ?_, fun h => ?_⟩⟩
  · exact (built_tag_floor tagOf tagOf_symmDiff tag7_ne L hL 3 h).1 le_rfl
  · exact (built_tag_floor tagOf tagOf_symmDiff tag7_ne L hL 5 h).2 le_rfl

end GLM.Golay24
