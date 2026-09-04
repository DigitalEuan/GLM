/-
# The tie-break: the part of an address that geometry does not decide

`overlay/glm_universal/reasoning/stability.py` measured something awkward about
this development's address book.  A declaration's address is the Leech point
nearest to `9 ·` its feature vector — but for most declarations that point is
**not unique**.  The scaled feature vector is an integer vector and the lattice
is an integral lattice, so the input lands exactly equidistant from several
lattice points, and which of them becomes the address is settled by the
decoder's *tie-break*: an implementation detail, inherited rather than chosen.

This file is the tie-break written down.  It proves four things.

## 1.  A nearest-point map is not determined by being one

`Nearest L x` is the set of points of `L` closest to `x`.  `mem_nearest` says a
quantiser lands in it, `dist_eq_of_mem_nearest` that its members are
indistinguishable by the property that defines them, and
`quantiser_of_choice` builds a quantiser out of *any* selection from it.  So
the three axioms of `Address.Quantiser` fix the address only up to `Nearest`,
and a tie-break is exactly the extra data.

## 2.  Choosing the least member is well defined; choosing per branch is not

`IsLexLeast` names the stated rule — take the lexicographically least member of
the tie class — and `isLexLeast_unique` says a set has at most one, while
`exists_isLexLeast` says a finite nonempty one has exactly one.  Being
quantified over the *set*, the rule cannot depend on the order the candidates
were enumerated in, which is the sense in which it is well defined.

The rule the decoder actually runs is not of that form.  It resolves each
coordinate before it compares whole points: it rounds every tied coordinate
*down*, and then, when the coordinate sum fails the lattice's mod-8 condition,
raises the **earliest** tied coordinate.  `decoder_not_lexLeast` shows that
this is never the lexicographically least admissible point once two
coordinates are tied — the least one raises the **last** tied coordinate
(`lexLeast_of_odd`).  The two rules therefore disagree, and
`reasoning/tie_break.py` counts how often on the real corpus.

## 3.  The size of a tie class is a closed form, not a search

Within one congruence branch the tied coordinates may be raised
independently, and raising one shifts the coordinate sum by 4 — half of the
lattice's modulus.  So admissibility depends only on the parity of how many
were raised (`sum_raise_mod_eight`), and exactly half of the `2 ^ k` choices
are admissible (`card_odd_subsets`, `card_even_subsets`).  That is the
`2 ^ (k - 1)` that `tie_break.branch_minimum` returns without enumerating
anything.

`nearest_in_residue_class_differ_by_four` is the coordinate-level fact the
whole picture rests on: two nearest integers in a class mod 4 differ by
exactly 4, and the value they surround is their midpoint.

## 4.  The tie-break cannot change what the address is read back as

`readback_of_tie_class`: every member of the tie class lies within the
covering radius of `scale · f`, and `Address.readback_unique` then forces them
all to read back to the same feature vector.  So every sentence the machine
speaks off an address is invariant under the tie-break, and only the figures
computed from *pairs* of addresses — collisions, nearest-neighbour separation
— can move.  Those are measured, not proved, in
[`studies/TIE_BREAK_STUDY.md`](../../../studies/TIE_BREAK_STUDY.md).
-/
import Mathlib
import RequestProject.GLM.Address

namespace GLM.TieBreak

open Finset

/-! ## 1.  The tie class of a nearest-point map -/

section Nearest

variable {X : Type*} [MetricSpace X] {L : Set X} {rho : ℝ}

/-- **The tie class.**  The points of `L` at minimum distance from `x`: what a
nearest-point map has to choose between. -/
def Nearest (L : Set X) (x : X) : Set X :=
  {p | p ∈ L ∧ ∀ q ∈ L, dist x p ≤ dist x q}

/-- A quantiser's answer is always in the tie class. -/
theorem mem_nearest (Q : Address.Quantiser X L rho) (x : X) :
    Q.toFun x ∈ Nearest L x :=
  ⟨Q.mem x, Q.best x⟩

/-- Members of a tie class are equidistant: nothing in the definition of a
nearest point tells them apart. -/
theorem dist_eq_of_mem_nearest {x p q : X} (hp : p ∈ Nearest L x)
    (hq : q ∈ Nearest L x) : dist x p = dist x q :=
  le_antisymm (hp.2 q hq.1) (hq.2 p hp.1)

/-- **Any selection from the tie class is a quantiser.**  The three axioms of
`Address.Quantiser` do not determine the map: they determine `Nearest`, and a
tie-break supplies the rest. -/
def quantiserOfChoice (c : X → X) (hmem : ∀ x, c x ∈ Nearest L x)
    (hclose : ∀ x, dist x (c x) ≤ rho) : Address.Quantiser X L rho where
  toFun := c
  mem x := (hmem x).1
  close := hclose
  best x q hq := (hmem x).2 q hq

end Nearest

/-! ## 2.  Lexicographic selection, and why it is well defined -/

section Lex

variable {n : ℕ}

/-- Lexicographic strict order on integer vectors, spelled out: they agree
before some coordinate, and there the first is smaller. -/
def LexLt (p q : Fin n → ℤ) : Prop :=
  ∃ i : Fin n, (∀ j : Fin n, j < i → p j = q j) ∧ p i < q i

theorem lexLt_iff_toLex (p q : Fin n → ℤ) : LexLt p q ↔ toLex p < toLex q :=
  Iff.rfl

theorem lexLt_irrefl (p : Fin n → ℤ) : ¬ LexLt p p := by
  rw [lexLt_iff_toLex]; exact lt_irrefl _

theorem lexLt_asymm {p q : Fin n → ℤ} (h : LexLt p q) : ¬ LexLt q p := by
  rw [lexLt_iff_toLex] at *; exact asymm h

theorem lexLt_trans {p q r : Fin n → ℤ} (h₁ : LexLt p q) (h₂ : LexLt q r) :
    LexLt p r := by
  rw [lexLt_iff_toLex] at *; exact lt_trans h₁ h₂

theorem lexLt_total {p q : Fin n → ℤ} (h : p ≠ q) : LexLt p q ∨ LexLt q p := by
  rw [lexLt_iff_toLex, lexLt_iff_toLex]
  rcases lt_trichotomy (toLex p) (toLex q) with h' | h' | h'
  · exact Or.inl h'
  · exact absurd h' (fun he => h (by simpa using he))
  · exact Or.inr h'

/-- **The stated rule.**  `p` is the lexicographically least member of `S`.
This is a property of the *set*: no enumeration order appears in it. -/
def IsLexLeast (S : Set (Fin n → ℤ)) (p : Fin n → ℤ) : Prop :=
  p ∈ S ∧ ∀ q ∈ S, q ≠ p → LexLt p q

/-- **The rule is well defined.**  A set has at most one lexicographically
least member, so the tie-break it defines is a function of the tie class. -/
theorem isLexLeast_unique {S : Set (Fin n → ℤ)} {p q : Fin n → ℤ}
    (hp : IsLexLeast S p) (hq : IsLexLeast S q) : p = q := by
  by_contra hne
  exact lexLt_asymm (hp.2 q hq.1 (Ne.symm hne)) (hq.2 p hp.1 hne)

/-- And a finite nonempty tie class has one. -/
theorem exists_isLexLeast (s : Finset (Fin n → ℤ)) (hs : s.Nonempty) :
    ∃ p, IsLexLeast (↑s : Set (Fin n → ℤ)) p := by
  classical
  have himg : (s.image (toLex : (Fin n → ℤ) → Lex (Fin n → ℤ))).Nonempty :=
    hs.image _
  set m := (s.image (toLex : (Fin n → ℤ) → Lex (Fin n → ℤ))).min' himg with hm
  have hmem : m ∈ s.image (toLex : (Fin n → ℤ) → Lex (Fin n → ℤ)) :=
    Finset.min'_mem _ _
  obtain ⟨p, hps, hpm⟩ := Finset.mem_image.mp hmem
  refine ⟨p, hps, ?_⟩
  intro q hq hqp
  have : m ≤ toLex q :=
    Finset.min'_le _ _ (Finset.mem_image_of_mem _ hq)
  rw [← hpm] at this
  rw [lexLt_iff_toLex]
  exact lt_of_le_of_ne this (fun he => hqp (by simpa using he.symm))

end Lex

/-! ## 3.  One congruence branch: raising the tied coordinates -/

section Branch

variable {n : ℕ}

/-- The point that raises exactly the coordinates in `S` from their lower
nearest option to their upper one.  The two options of a tied coordinate
differ by 4 — that is `nearest_in_residue_class_differ_by_four`. -/
def raise (a : Fin n → ℤ) (S : Finset (Fin n)) : Fin n → ℤ :=
  fun i => a i + if i ∈ S then 4 else 0

theorem sum_raise (a : Fin n → ℤ) (S : Finset (Fin n)) :
    ∑ i, raise a S i = (∑ i, a i) + 4 * S.card := by
  classical
  simp [raise, Finset.sum_add_distrib, Finset.sum_ite_mem, Finset.sum_const,
    mul_comm]

/-- **Raising a coordinate flips the sum modulo 8.**  The coordinate moves by
4, half the lattice's modulus, so whether a choice satisfies the sum condition
depends only on the parity of how many coordinates were raised. -/
theorem sum_raise_mod_eight (a : Fin n → ℤ) (S : Finset (Fin n)) :
    (∑ i, raise a S i) % 8 = ((∑ i, a i) + 4 * ((S.card : ℤ) % 2)) % 8 := by
  rw [sum_raise]
  omega

/-- The two parities of subset are exchanged by toggling one fixed element, so
they are equinumerous. -/
theorem card_odd_eq_card_even (T : Finset (Fin n)) (hT : T.Nonempty) :
    (T.powerset.filter (fun S => S.card % 2 = 1)).card
      = (T.powerset.filter (fun S => S.card % 2 = 0)).card := by
  classical
  obtain ⟨a, ha⟩ := hT
  set f : Finset (Fin n) → Finset (Fin n) :=
    fun S => if a ∈ S then S.erase a else insert a S with hf
  have hmem : ∀ S ⊆ T, f S ⊆ T := by
    intro S hS
    by_cases h : a ∈ S <;> simp [hf, h]
    · exact (Finset.erase_subset _ _).trans hS
    · exact Finset.insert_subset ha hS
  have hparity : ∀ S : Finset (Fin n), (f S).card % 2 ≠ S.card % 2 := by
    intro S
    by_cases h : a ∈ S
    · simp only [hf, if_pos h, Finset.card_erase_of_mem h]
      have : 1 ≤ S.card := Finset.card_pos.mpr ⟨a, h⟩
      omega
    · simp only [hf, if_neg h, Finset.card_insert_of_notMem h]
      omega
  have hinv : ∀ S : Finset (Fin n), f (f S) = S := by
    intro S
    by_cases h : a ∈ S
    · simp [hf, h, Finset.insert_erase h]
    · simp [hf, h, Finset.erase_insert h]
  refine Finset.card_nbij' f f ?_ ?_ ?_ ?_
  · intro S hS
    simp only [Finset.coe_filter, Set.mem_setOf_eq, Finset.mem_powerset] at hS ⊢
    exact ⟨hmem S hS.1, by have := hparity S; omega⟩
  · intro S hS
    simp only [Finset.coe_filter, Set.mem_setOf_eq, Finset.mem_powerset] at hS ⊢
    exact ⟨hmem S hS.1, by have := hparity S; omega⟩
  · intro S _; exact hinv S
  · intro S _; exact hinv S

/-- The two parities exhaust the power set. -/
theorem card_odd_add_card_even (T : Finset (Fin n)) :
    (T.powerset.filter (fun S => S.card % 2 = 1)).card
      + (T.powerset.filter (fun S => S.card % 2 = 0)).card = 2 ^ T.card := by
  classical
  have hdisj : Disjoint (T.powerset.filter (fun S => S.card % 2 = 1))
      (T.powerset.filter (fun S => S.card % 2 = 0)) := by
    refine Finset.disjoint_left.mpr ?_
    intro S h1 h0
    simp only [Finset.mem_filter] at h1 h0
    omega
  rw [← Finset.card_union_of_disjoint hdisj, ← Finset.card_powerset]
  congr 1
  ext S
  simp only [Finset.mem_union, Finset.mem_filter]
  constructor
  · rintro (h | h) <;> exact h.1
  · intro h
    rcases Nat.mod_two_eq_zero_or_one S.card with he | ho
    · exact Or.inr ⟨h, he⟩
    · exact Or.inl ⟨h, ho⟩

/-- Exactly half of the subsets of a nonempty set have odd cardinality. -/
theorem card_odd_subsets (T : Finset (Fin n)) (hT : T.Nonempty) :
    (T.powerset.filter (fun S => S.card % 2 = 1)).card = 2 ^ (T.card - 1) := by
  have hcard := card_odd_eq_card_even T hT
  have hsplit := card_odd_add_card_even T
  have hpos : 1 ≤ T.card := Finset.card_pos.mpr hT
  have h2 : 2 ^ T.card = 2 * 2 ^ (T.card - 1) := by
    rw [← pow_succ']
    congr 1
    omega
  omega

/-- …and half have even cardinality.  Together these are the `2 ^ (k - 1)`
that `tie_break.branch_minimum` returns as the size of a branch's minimiser
set without enumerating one of them. -/
theorem card_even_subsets (T : Finset (Fin n)) (hT : T.Nonempty) :
    (T.powerset.filter (fun S => S.card % 2 = 0)).card = 2 ^ (T.card - 1) :=
  (card_odd_eq_card_even T hT).symm.trans (card_odd_subsets T hT)

/-- **The least admissible point raises the last tied coordinate.**  Among the
choices with an odd number of raised coordinates — the admissible half, when
the unraised point fails the sum condition — the lexicographically least
raises only `T.max'`. -/
theorem lexLeast_of_odd (a : Fin n → ℤ) (T : Finset (Fin n)) (hT : T.Nonempty)
    (S : Finset (Fin n)) (hS : S ⊆ T) (hodd : S.card % 2 = 1)
    (hne : S ≠ {T.max' hT}) :
    LexLt (raise a {T.max' hT}) (raise a S) := by
  classical
  set M := T.max' hT with hM
  set D := (Finset.univ : Finset (Fin n)).filter (fun i => ¬ (i ∈ S ↔ i = M))
    with hD
  have hDne : D.Nonempty := by
    by_contra hemp
    apply hne
    ext i
    have hi : i ∉ D := by
      rw [Finset.not_nonempty_iff_eq_empty] at hemp
      simp [hemp]
    simp only [hD, Finset.mem_filter, Finset.mem_univ, true_and, not_not] at hi
    simpa [Finset.mem_singleton] using hi
  set i₀ := D.min' hDne with hi₀
  have hi₀D : i₀ ∈ D := Finset.min'_mem _ _
  have hi₀ne : i₀ ≠ M := by
    intro heq
    have hMD : M ∈ D := heq ▸ hi₀D
    simp only [hD, Finset.mem_filter, Finset.mem_univ, true_and] at hMD
    have hMS : M ∉ S := by tauto
    have hSe : S = ∅ := by
      by_contra hSne
      obtain ⟨j, hj⟩ := Finset.nonempty_iff_ne_empty.mpr hSne
      have hjM : j ≠ M := fun h => hMS (h ▸ hj)
      have hjD : j ∈ D := by
        simp only [hD, Finset.mem_filter, Finset.mem_univ, true_and]
        exact fun hiff => hjM (hiff.mp hj)
      have h1 : i₀ ≤ j := Finset.min'_le _ _ hjD
      have h2 : j ≤ M := Finset.le_max' T j (hS hj)
      rw [heq] at h1
      exact hjM (le_antisymm h2 h1)
    rw [hSe] at hodd
    simp at hodd
  have hi₀S : i₀ ∈ S := by
    simp only [hD, Finset.mem_filter, Finset.mem_univ, true_and] at hi₀D
    by_contra hno
    exact hi₀D ⟨fun h => absurd h hno, fun h => absurd h hi₀ne⟩
  refine ⟨i₀, ?_, ?_⟩
  · intro j hj
    have hjD : j ∉ D := fun h => absurd (Finset.min'_le _ _ h) (not_le.mpr hj)
    simp only [hD, Finset.mem_filter, Finset.mem_univ, true_and, not_not] at hjD
    simp only [raise, Finset.mem_singleton]
    by_cases h : j ∈ S
    · rw [if_pos (hjD.mp h), if_pos h]
    · rw [if_neg (fun hc => h (hjD.mpr hc)), if_neg h]
  · simp only [raise, Finset.mem_singleton, if_pos hi₀S, if_neg hi₀ne]
    omega

/-- **The decoder's rule is not the lexicographic one.**  It raises the
earliest tied coordinate; as soon as two coordinates are tied that point is
strictly larger than the least admissible one. -/
theorem decoder_not_lexLeast (a : Fin n → ℤ) (T : Finset (Fin n))
    (hT : 1 < T.card) :
    LexLt (raise a {T.max' (Finset.card_pos.mp (by omega))})
      (raise a {T.min' (Finset.card_pos.mp (by omega))}) := by
  have hT' : T.Nonempty := Finset.card_pos.mp (by omega)
  refine lexLeast_of_odd a T hT' {T.min' hT'} ?_ ?_ ?_
  · simpa using Finset.min'_mem T hT'
  · simp
  · have : T.min' hT' < T.max' hT' := Finset.min'_lt_max'_of_card T hT
    simp only [ne_eq, Finset.singleton_inj]
    exact ne_of_lt this

end Branch

/-! ## 4.  The coordinate-level tie -/

/-- **Two nearest integers in a residue class mod 4 differ by exactly 4**, and
the value they surround is their midpoint.  So a coordinate is tied exactly
when it is an odd multiple of 2 away from the class, and a tie offers exactly
two options — which is what `raise` encodes. -/
theorem nearest_in_residue_class_differ_by_four {v r x y : ℤ}
    (hx : x % 4 = r % 4) (hy : y % 4 = r % 4)
    (hmin : ∀ z : ℤ, z % 4 = r % 4 → (v - x) ^ 2 ≤ (v - z) ^ 2)
    (hcost : (v - x) ^ 2 = (v - y) ^ 2) (hne : x ≠ y) :
    2 * v = x + y ∧ (y = x + 4 ∨ x = y + 4) := by
  have hprod : (y - x) * (2 * v - x - y) = 0 := by nlinarith [hcost]
  have hyx : y - x ≠ 0 := sub_ne_zero.mpr (Ne.symm hne)
  have hsum : 2 * v = x + y := by
    rcases mul_eq_zero.mp hprod with h | h
    · exact absurd h hyx
    · linarith
  refine ⟨hsum, ?_⟩
  obtain ⟨k, hk⟩ : (4 : ℤ) ∣ (y - x) := by omega
  have hk0 : k ≠ 0 := by rintro rfl; simp at hk; omega
  rcases lt_or_gt_of_ne hk0 with hneg | hpos
  · have hz : (x - 4) % 4 = r % 4 := by omega
    have hle := hmin (x - 4) hz
    right
    nlinarith [hle, hsum, hk]
  · have hz : (x + 4) % 4 = r % 4 := by omega
    have hle := hmin (x + 4) hz
    left
    nlinarith [hle, hsum, hk]

/-! ## 5.  What the tie-break cannot touch -/

/-- **The whole tie class reads back to the same feature vector.**  Every
nearest point lies within the covering radius `rho` of `scale • f`, and
`Address.readback_unique` then says any feature vector read off any of them is
`f`.  So the tie-break moves the address but not the sentence: this is the
theorem behind `stability.py`'s "the read-back is the stabler object". -/
theorem readback_of_tie_class {n : ℕ} {scale rho : ℤ} (hrho : 0 ≤ rho)
    (hscale : 2 * rho < scale) {f g h : Fin n → ℤ} {p q : Fin n → ℤ}
    (hp : ∀ i, |p i - scale * f i| ≤ rho) (hq : ∀ i, |q i - scale * f i| ≤ rho)
    (hpg : ∀ i, |p i - scale * g i| ≤ rho)
    (hqh : ∀ i, |q i - scale * h i| ≤ rho) : g = h := by
  have h₁ : g = f := Address.readback_unique hrho hscale p g f hpg hp
  have h₂ : h = f := Address.readback_unique hrho hscale q h f hqh hq
  rw [h₁, h₂]

end GLM.TieBreak
