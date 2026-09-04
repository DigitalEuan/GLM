/-
# Why XOR keeps appearing, exactly what it discards, and what replaces it

XOR turns up all over this substrate, and the reasonable suspicion is that it
is a habit of bit-twiddling rather than a decision — and that it throws
information away.  Both halves of that suspicion are answered here, and the
answers point in opposite directions, which is why the question is worth
settling rather than arguing.

**1. At the `F₂` layer XOR is not a choice.**  `closed_iff_affine` proves that
of the sixteen coordinatewise binary Boolean operations, exactly the eight
**affine** ones — `0`, `1`, `a`, `b`, `ā`, `b̄`, `a ⊕ b`, `a ⊕ b ⊕ 1` — carry
codewords to codewords, and the other eight do not.  Every one of the eight is
`a ⊕ b` composed with complementation and projection, because the all-ones word
is itself a codeword (`isCodeword_univ`).  So the only operation that combines
two codewords into a third is XOR, up to relabelling: `AND`, `OR`, `NAND`,
`NOR` and the rest all leave the code.  The single obstruction is the term
`a ∧ b`, and `inter_not_codeword` is one explicit pair of octads whose
intersection has weight 4 — which kills all eight non-affine operations at
once, since each is an affine function of `a`, `b` XOR-ed with `a ∧ b`.

**2. As a combiner, XOR discards exactly 24 of the 48 bits — and nothing in the
carrier can do better.**  `xor_fibre_card`: every value of `a ⊕ b` is hit by
exactly `2²⁴` pairs, so the operation is 2²⁴-to-one, uniformly.  What it
forgets is precisely the overlap: `a ⊕ b` fixes `a ∆ b` and says nothing about
`a ∩ b`.  `exists_large_fibre` shows this is not XOR's fault:
*any* map `Word × Word → Word` has a fibre of at least `2²⁴` pairs, by counting
alone, and XOR attains that bound at every single value.  Inside a 24-bit
carrier, a two-word combiner cannot keep more than half of what it is given.

**3. The information is recoverable one layer up, and the layer is the one the
substrate already has.**  Add the two words as integers instead of over `F₂`:
`tsum a b : Fin 24 → Fin 3` records `0`, `1` or `2` per coordinate.  It is
surjective (`tsum_surjective`), so it takes `3²⁴ = 282,429,536,481` values
against XOR's `2²⁴` — between `2³⁸` and `2³⁹` (`three_pow_bounds`), i.e. it
keeps roughly 38 of the 48 bits rather than 24.  And it keeps the right ones:
`tsum_inter` and `tsum_symmDiff` recover `a ∩ b` *and* `a ∆ b` from it, hence
`a ∪ b` and every weight the archive's "mass defect" talks about.  Carry the
signed difference alongside and nothing at all is lost:
`tsum_tdiff_injective`.

**What this means for the runtime.**  Where XOR appears as the group law of the
code — encoding a message as a XOR of basis rows, adding a syndrome, moving
inside a coset — it is forced by (1) and loses nothing, because the other
operand is still in hand.  Where it appears as a *combiner* that discards an
operand, (2) says the loss is real and (3) says the fix is to combine at the
integer layer rather than the `F₂` layer.  The package has already made that
move twice, and both times the exact statement is the one above:
`substrate/superposition.py` replaces the XOR bundle of a six-fold tie — which
is the constant all-ones word, so it destroys the tie completely — with the
rational bundle, which is invertible (`Superposition.lean`); and
`reasoning/monster_stack.py` retired XOR composition of Monster addresses for
the Sakuma product, which keeps the terms XOR drops.

`glm_universal.reasoning.combiner` recomputes all of it, and
`studies/COMBINER_STUDY.md` is the reading, including the inventory of every
place the runtime uses XOR and which of the three cases it falls under.
-/
import Mathlib
import RequestProject.GLM.Golay.Code
import RequestProject.GLM.GolayWeightEnum

namespace GLM.Golay24

open Finset

set_option maxRecDepth 8000

/-! ## 1. Coordinatewise operations, and which of them stay on the code -/

/-- The word a coordinatewise binary Boolean operation builds from two words. -/
def apply2 (f : Bool → Bool → Bool) (a b : Word) : Word :=
  univ.filter (fun i => f (decide (i ∈ a)) (decide (i ∈ b)) = true)

/-- `f` is affine over `F₂`: `f x y = c₀ ⊕ c₁x ⊕ c₂y`.  Eight of the sixteen
binary Boolean operations are. -/
def IsAffine (f : Bool → Bool → Bool) : Prop :=
  ∃ c₀ c₁ c₂ : Bool, ∀ x y, f x y = xor c₀ (xor (c₁ && x) (c₂ && y))

instance : DecidablePred IsAffine := fun _ => by unfold IsAffine; infer_instance

/-- The word built by an affine operation is a symmetric difference of the two
words, the whole set and the empty set. -/
theorem apply2_affine (a b : Word) (c₀ c₁ c₂ : Bool) :
    apply2 (fun x y => xor c₀ (xor (c₁ && x) (c₂ && y))) a b
      = symmDiff (symmDiff (if c₀ then (univ : Word) else ∅)
          (if c₁ then a else ∅)) (if c₂ then b else ∅) := by
  ext i
  by_cases hia : i ∈ a <;> by_cases hib : i ∈ b <;> cases c₀ <;> cases c₁ <;> cases c₂ <;>
    simp [apply2, Finset.mem_symmDiff, hia, hib]

/-- Every non-affine operation is an affine one XOR-ed with `a ∧ b`.  There are
sixteen operations, so this is a finite check. -/
theorem affine_or_inter (f : Bool → Bool → Bool) :
    IsAffine f ∨ ∃ c₀ c₁ c₂ : Bool,
      ∀ x y, f x y = xor (xor c₀ (xor (c₁ && x) (c₂ && y))) (x && y) := by
  revert f; decide

theorem apply2_affine_inter (a b : Word) (c₀ c₁ c₂ : Bool) :
    apply2 (fun x y => xor (xor c₀ (xor (c₁ && x) (c₂ && y))) (x && y)) a b
      = symmDiff (symmDiff (symmDiff (if c₀ then (univ : Word) else ∅)
          (if c₁ then a else ∅)) (if c₂ then b else ∅)) (a ∩ b) := by
  ext i
  by_cases hia : i ∈ a <;> by_cases hib : i ∈ b <;> cases c₀ <;> cases c₁ <;> cases c₂ <;>
    simp [apply2, Finset.mem_symmDiff, Finset.mem_inter, hia, hib]

/-! ## 2. The all-ones word is a codeword, so complementation is XOR -/

/-- The extended Golay code contains the all-ones word: complementing a word is
XOR-ing with a codeword, which is why the eight affine operations are eight and
not four. -/
theorem isCodeword_univ : IsCodeword (univ : Word) := by
  unfold IsCodeword syn; decide

theorem isCodeword_ite (c : Bool) {a : Word} (ha : IsCodeword a) :
    IsCodeword (if c then a else ∅) := by
  cases c
  · simpa using isCodeword_empty
  · simpa using ha

/-! ## 3. Two octads whose intersection is not a codeword -/

/-- An octad of the substrate's code. -/
def octadA : Word := {0, 1, 2, 4, 5, 6, 10, 13}

/-- A second octad, meeting the first in four coordinates. -/
def octadB : Word := {0, 1, 3, 4, 5, 9, 11, 14}

theorem isCodeword_octadA : IsCodeword octadA := by
  unfold IsCodeword syn octadA; decide

theorem isCodeword_octadB : IsCodeword octadB := by
  unfold IsCodeword syn octadB; decide

/-- **The single obstruction.**  Their intersection has weight 4, and the code
has no word of weight 4, so `AND` leaves the code. -/
theorem inter_not_codeword : ¬ IsCodeword (octadA ∩ octadB) := by
  unfold IsCodeword syn octadA octadB; decide

/-! ## 4. The theorem: closed under a coordinatewise operation iff affine -/

/-- **XOR is not a choice.**  A coordinatewise binary Boolean operation carries
codewords to codewords if and only if it is affine — that is, if and only if it
is built from `a ⊕ b`, projection and complementation.  `AND`, `OR`, `NAND`,
`NOR`, and every other non-affine operation, leave the code. -/
theorem closed_iff_affine (f : Bool → Bool → Bool) :
    (∀ a b : Word, IsCodeword a → IsCodeword b → IsCodeword (apply2 f a b))
      ↔ IsAffine f := by
  constructor
  · intro hclosed
    rcases affine_or_inter f with haff | ⟨c₀, c₁, c₂, hf⟩
    · exact haff
    · exfalso
      have hfun : f = fun x y => xor (xor c₀ (xor (c₁ && x) (c₂ && y))) (x && y) := by
        funext x y; exact hf x y
      have hcw := hclosed octadA octadB isCodeword_octadA isCodeword_octadB
      rw [hfun, apply2_affine_inter] at hcw
      -- the affine part is a codeword, so the intersection would have to be one
      set g : Word := symmDiff (symmDiff (if c₀ then (univ : Word) else ∅)
        (if c₁ then octadA else ∅)) (if c₂ then octadB else ∅) with hg
      have hgc : IsCodeword g := by
        refine isCodeword_symmDiff (isCodeword_symmDiff ?_ ?_) ?_
        · exact isCodeword_ite c₀ isCodeword_univ
        · exact isCodeword_ite c₁ isCodeword_octadA
        · exact isCodeword_ite c₂ isCodeword_octadB
      have : IsCodeword (octadA ∩ octadB) := by
        have h := isCodeword_symmDiff hgc hcw
        rwa [symmDiff_symmDiff_cancel_left] at h
      exact inter_not_codeword this
  · rintro ⟨c₀, c₁, c₂, hf⟩ a b ha hb
    have hfun : f = fun x y => xor c₀ (xor (c₁ && x) (c₂ && y)) := by
      funext x y; exact hf x y
    rw [hfun, apply2_affine]
    refine isCodeword_symmDiff (isCodeword_symmDiff ?_ ?_) ?_
    · exact isCodeword_ite c₀ isCodeword_univ
    · exact isCodeword_ite c₁ ha
    · exact isCodeword_ite c₂ hb

/-! ## 5. What XOR discards, and that no in-carrier combiner discards less -/

/-- Fixing the first operand determines the second, so the pairs with a given
symmetric difference are indexed by the words. -/
def xorFibreEquiv (t : Word) : Word ≃ {p : Word × Word // symmDiff p.1 p.2 = t} where
  toFun a := ⟨(a, symmDiff a t), symmDiff_symmDiff_cancel_left a t⟩
  invFun p := p.1.1
  left_inv _ := rfl
  right_inv p := by
    obtain ⟨⟨a, b⟩, hp⟩ := p
    have hb : symmDiff a t = b := by rw [← hp, symmDiff_symmDiff_cancel_left]
    simp [hb]

/-- **XOR is uniformly `2²⁴`-to-one.**  Every word is the symmetric difference
of exactly `2²⁴` ordered pairs, so what the value forgets is exactly which of
the `2²⁴` overlaps `a ∩ b` was in play. -/
theorem xor_fibre_card (t : Word) :
    Fintype.card {p : Word × Word // symmDiff p.1 p.2 = t} = 2 ^ 24 := by
  rw [← Fintype.card_congr (xorFibreEquiv t), Fintype.card_finset, Fintype.card_fin]

/-- **And no combiner into the same carrier does better.**  Whatever map is
used to fold two words into one, some value of it is shared by at least `2²⁴`
of the `2⁴⁸` pairs; XOR attains that bound at *every* value, so it is as
faithful as an in-carrier combiner can be. -/
theorem exists_large_fibre (f : Word × Word → Word) :
    ∃ t : Word, 2 ^ 24 ≤ Fintype.card {p : Word × Word // f p = t} := by
  by_contra h
  push_neg at h
  have hsum : ∑ t : Word, Fintype.card {p : Word × Word // f p = t}
      = Fintype.card (Word × Word) := by
    rw [← Fintype.card_sigma]
    exact Fintype.card_congr (Equiv.sigmaFiberEquiv f)
  have hlt : ∑ t : Word, Fintype.card {p : Word × Word // f p = t} < 2 ^ 24 * 2 ^ 24 := by
    calc ∑ t : Word, Fintype.card {p : Word × Word // f p = t}
        ≤ ∑ _t : Word, (2 ^ 24 - 1) := Finset.sum_le_sum (fun t _ => by have := h t; omega)
      _ = 2 ^ 24 * (2 ^ 24 - 1) := by
          simp [Finset.sum_const, Finset.card_univ, Fintype.card_finset, Fintype.card_fin]
      _ < 2 ^ 24 * 2 ^ 24 := by norm_num
  rw [hsum] at hlt
  simp [Fintype.card_prod, Fintype.card_finset, Fintype.card_fin] at hlt

/-! ## 6. The layer above: adding the words as integers -/

/-- The integer combiner: coordinatewise `0`, `1` or `2`. -/
def tsum (a b : Word) : Fin 24 → Fin 3 :=
  fun i => (if i ∈ a then 1 else 0) + (if i ∈ b then 1 else 0)

/-- The signed companion, over `ℤ`. -/
def tdiff (a b : Word) : Fin 24 → ℤ :=
  fun i => (if i ∈ a then 1 else 0) - (if i ∈ b then 1 else 0)

/-- The overlap is recovered: it is where the integer sum is `2`. -/
theorem tsum_inter (a b : Word) :
    univ.filter (fun i => tsum a b i = 2) = a ∩ b := by
  ext i
  by_cases hia : i ∈ a <;> by_cases hib : i ∈ b <;> simp [tsum, hia, hib]

/-- And the symmetric difference is where it is `1`, so the integer sum carries
both of the quantities `a ⊕ b` splits, and therefore `a ∪ b` as well. -/
theorem tsum_symmDiff (a b : Word) :
    univ.filter (fun i => tsum a b i = 1) = symmDiff a b := by
  ext i
  by_cases hia : i ∈ a <;> by_cases hib : i ∈ b <;>
    simp [tsum, Finset.mem_symmDiff, hia, hib]

/-- **The integer layer is strictly wider.**  Every ternary vector occurs, so
the combiner takes `3²⁴` values against XOR's `2²⁴`. -/
theorem tsum_surjective : Function.Surjective (fun p : Word × Word => tsum p.1 p.2) := by
  intro t
  refine ⟨(univ.filter (fun i => t i ≠ 0), univ.filter (fun i => t i = 2)), ?_⟩
  funext i
  have : ∀ x : Fin 3, ((if x ≠ 0 then (1 : Fin 3) else 0)
      + (if x = 2 then (1 : Fin 3) else 0)) = x := by decide
  simpa [tsum] using this (t i)

theorem card_ternary : Fintype.card (Fin 24 → Fin 3) = 3 ^ 24 := by
  simp

/-- `3²⁴` sits between `2³⁸` and `2³⁹`: the integer layer keeps about 38 of the
48 bits of a pair of words, where XOR keeps 24. -/
theorem three_pow_bounds : 2 ^ 38 < 3 ^ 24 ∧ 3 ^ 24 < 2 ^ 39 := by
  constructor <;> norm_num

/-- **Nothing at all need be lost.**  The integer sum and the signed difference
together determine both words, so a combiner at the integer layer can be made
exactly invertible — which is what the rational bundle of `Superposition.lean`
does for a six-fold tie. -/
theorem tsum_tdiff_injective :
    Function.Injective (fun p : Word × Word => (tsum p.1 p.2, tdiff p.1 p.2)) := by
  rintro ⟨a, b⟩ ⟨c, d⟩ h
  have hd : tdiff a b = tdiff c d := (Prod.ext_iff.mp h).2
  have hs : tsum a b = tsum c d := (Prod.ext_iff.mp h).1
  have hac : a = c := by
    ext i
    have h1 : tdiff a b i = tdiff c d i := congrFun hd i
    have h2 : tsum a b i = tsum c d i := congrFun hs i
    by_cases hia : i ∈ a <;> by_cases hic : i ∈ c <;>
      by_cases hib : i ∈ b <;> by_cases hid : i ∈ d <;>
        simp_all [tdiff, tsum]
  subst hac
  have hbd : b = d := by
    ext i
    have h1 : tdiff a b i = tdiff a d i := congrFun hd i
    by_cases hia : i ∈ a <;> by_cases hib : i ∈ b <;> by_cases hid : i ∈ d <;>
      simp_all [tdiff]
  simp [hbd]

end GLM.Golay24
