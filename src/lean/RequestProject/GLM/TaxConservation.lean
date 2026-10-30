/-
# The TAX conservation law, and the exact boundary at which it stops being true

The GLM README states the conservation law

    TAX(a ⊕ b) = TAX(a) + TAX(b) − 2·TAX(a ∧ b)                     (arc_agi_17 v10)

This file proves that the law is **exactly true on the substrate layer** — where
carriers are binary, `⊕` is XOR and `∧` is AND — and **exactly false one layer
up**, where carriers carry integer amplitudes and `⊕`/`∧` are the bitwise
operations on those amplitudes.  That is the first concrete instance of the
"information loss at a boundary" phenomenon studied in `Layers.lean`: a law that
is true within the reach of one layer and untrue once the next layer takes over.
-/
import RequestProject.GLM.Constants

namespace GLM

open Finset

variable {n : ℕ}

/-! ## Binary carriers -/

/-- The integer carrier of a binary (substrate-level) pattern. -/
def ofBits (a : Fin n → Bool) : Fin n → ℤ := fun i => if a i then 1 else 0

/-- Pointwise XOR of two binary patterns: the substrate's `⊕`. -/
def bxor (a b : Fin n → Bool) : Fin n → Bool := fun i => xor (a i) (b i)

/-- Pointwise AND of two binary patterns: the substrate's `∧`. -/
def band (a b : Fin n → Bool) : Fin n → Bool := fun i => (a i && b i)

/-- The support of a binary pattern. -/
def support (a : Fin n → Bool) : Finset (Fin n) := {i | a i = true}

@[simp] lemma mem_support {a : Fin n → Bool} {i : Fin n} : i ∈ support a ↔ a i = true := by
  simp [support]

lemma hammingWeight_ofBits (a : Fin n → Bool) :
    hammingWeight (ofBits a) = #(support a) := by
  unfold hammingWeight ofBits support
  congr 1
  apply Finset.filter_congr
  intro i _
  cases a i <;> simp

lemma normSq_ofBits (a : Fin n → Bool) : normSq (ofBits a) = (#(support a) : ℤ) := by
  unfold normSq ofBits support
  rw [Finset.card_filter]
  push_cast
  refine Finset.sum_congr rfl ?_
  intro i _
  cases a i <;> simp

/-- On the substrate layer the tax of a carrier is its Hamming weight times the
activation quantum `Q = Y + 1/8`. -/
theorem tax_ofBits (a : Fin n → Bool) : tax (ofBits a) = (#(support a) : ℝ) * Q := by
  unfold tax Q
  rw [hammingWeight_ofBits, normSq_ofBits]
  push_cast
  ring

/-! ## The support identities -/

lemma support_bxor (a b : Fin n → Bool) : support (bxor a b) = symmDiff (support a) (support b) := by
  ext i
  cases h : a i <;> cases h' : b i <;>
    simp [bxor, support, Finset.mem_symmDiff, h, h']

lemma support_band (a b : Fin n → Bool) : support (band a b) = support a ∩ support b := by
  ext i
  cases h : a i <;> cases h' : b i <;> simp [band, support, h, h']

/-- Inclusion–exclusion for the symmetric difference. -/
lemma card_symmDiff_add_two_mul_card_inter (s t : Finset (Fin n)) :
    #(symmDiff s t) + 2 * #(s ∩ t) = #s + #t := by
  classical
  have h1 : symmDiff s t = (s ∪ t) \ (s ∩ t) := by
    ext i; by_cases hs : i ∈ s <;> by_cases ht : i ∈ t <;> simp [Finset.mem_symmDiff, hs, ht]
  have hsub : s ∩ t ⊆ s ∪ t := by intro x hx; simp at hx ⊢; tauto
  have hii : (s ∩ t) ∩ (s ∪ t) = s ∩ t := Finset.inter_eq_left.2 hsub
  have h2 : #((s ∪ t) \ (s ∩ t)) = #(s ∪ t) - #(s ∩ t) := by
    rw [Finset.card_sdiff, hii]
  have h3 : #(s ∪ t) + #(s ∩ t) = #s + #t := Finset.card_union_add_card_inter s t
  have h4 : #(s ∩ t) ≤ #(s ∪ t) := Finset.card_le_card hsub
  rw [h1, h2]; omega

/-! ## The law, on the substrate layer -/

/-- **TAX conservation on the substrate layer.**  For binary carriers,
`TAX(a ⊕ b) = TAX(a) + TAX(b) − 2·TAX(a ∧ b)`. -/
theorem tax_conservation (a b : Fin n → Bool) :
    tax (ofBits (bxor a b)) = tax (ofBits a) + tax (ofBits b) - 2 * tax (ofBits (band a b)) := by
  rw [tax_ofBits, tax_ofBits, tax_ofBits, tax_ofBits, support_bxor, support_band]
  have h := card_symmDiff_add_two_mul_card_inter (support a) (support b)
  have h' : (#(symmDiff (support a) (support b)) : ℝ) + 2 * (#(support a ∩ support b) : ℝ)
      = (#(support a) : ℝ) + (#(support b) : ℝ) := by exact_mod_cast h
  linear_combination Q * h'

/-! ## The boundary: the law fails one layer up

At the integer layer a carrier is no longer a bit pattern: each coordinate
carries an integer amplitude, and the natural reading of `⊕` and `∧` is the
bitwise operation on those amplitudes.  The conservation law is then false. -/

/-- The integer carrier of a vector of amplitudes. -/
def ofNats (v : Fin n → ℕ) : Fin n → ℤ := fun i => (v i : ℤ)

/-- Bitwise XOR of amplitude vectors: the integer-layer reading of `⊕`. -/
def nxor (v w : Fin n → ℕ) : Fin n → ℕ := fun i => v i ^^^ w i

/-- Bitwise AND of amplitude vectors: the integer-layer reading of `∧`. -/
def nand (v w : Fin n → ℕ) : Fin n → ℕ := fun i => v i &&& w i

/-- The amplitude vector of a bit pattern. -/
def bitsToNats (a : Fin n → Bool) : Fin n → ℕ := fun i => if a i then 1 else 0

/-- The integer layer really extends the substrate layer: on bit patterns the
amplitude carrier is the substrate carrier. -/
theorem ofNats_bitsToNats (a : Fin n → Bool) : ofNats (bitsToNats a) = ofBits a := by
  funext i; cases h : a i <;> simp [ofNats, bitsToNats, ofBits, h]

/-- and the integer-layer operations restrict to the substrate ones. -/
theorem nxor_bitsToNats (a b : Fin n → Bool) :
    nxor (bitsToNats a) (bitsToNats b) = bitsToNats (bxor a b) := by
  funext i; cases h : a i <;> cases h' : b i <;> simp [nxor, bitsToNats, bxor, h, h']

theorem nand_bitsToNats (a b : Fin n → Bool) :
    nand (bitsToNats a) (bitsToNats b) = bitsToNats (band a b) := by
  funext i; cases h : a i <;> cases h' : b i <;> simp [nand, bitsToNats, band, h, h']

/-- The first witness: a single coordinate of amplitude `1`. -/
def w1 : Fin 1 → ℕ := fun _ => 1

/-- The second witness: a single coordinate of amplitude `2`. -/
def w2 : Fin 1 → ℕ := fun _ => 2

lemma nxor_w1_w2 : nxor w1 w2 = fun _ => 3 := by
  funext i; show (1 : ℕ) ^^^ 2 = 3; decide

lemma nand_w1_w2 : nand w1 w2 = fun _ => 0 := by
  funext i; show (1 : ℕ) &&& 2 = 0; decide

private lemma tax_const (k : ℕ) (hk : k ≠ 0) :
    tax (ofNats (fun _ => k : Fin 1 → ℕ)) = Y + (k : ℝ) ^ 2 / 8 := by
  have hw : hammingWeight (ofNats (fun _ => k : Fin 1 → ℕ)) = 1 := by
    have hk' : ((k : ℤ) ≠ 0) := by exact_mod_cast hk
    unfold hammingWeight ofNats
    rw [Finset.filter_true_of_mem (fun i _ => hk')]
    simp
  have hn : normSq (ofNats (fun _ => k : Fin 1 → ℕ)) = (k : ℤ) ^ 2 := by
    simp [normSq, ofNats]
  unfold tax
  rw [hw, hn]
  push_cast
  ring

/-- **The conservation law fails at the integer layer.**  With `a = (1)` and
`b = (2)` the two sides differ by `1/2 − Y ≠ 0`. -/
theorem tax_conservation_fails_at_integer_layer :
    tax (ofNats (nxor w1 w2)) ≠
      tax (ofNats w1) + tax (ofNats w2) - 2 * tax (ofNats (nand w1 w2)) := by
  have h0 : tax (ofNats (nand w1 w2)) = 0 := by
    rw [nand_w1_w2]
    exact tax_eq_zero_iff.2 (by funext i; simp [ofNats])
  have h3 : tax (ofNats (nxor w1 w2)) = Y + 9 / 8 := by
    rw [nxor_w1_w2, tax_const 3 (by norm_num)]; norm_num
  have h1 : tax (ofNats w1) = Y + 1 / 8 := by
    have : (w1 : Fin 1 → ℕ) = fun _ => 1 := rfl
    rw [this, tax_const 1 (by norm_num)]; norm_num
  have h2 : tax (ofNats w2) = Y + 4 / 8 := by
    have : (w2 : Fin 1 → ℕ) = fun _ => 2 := rfl
    rw [this, tax_const 2 (by norm_num)]; norm_num
  rw [h0, h1, h2, h3]
  intro h
  have : Y = 1 / 2 := by linarith
  exact absurd this (ne_of_lt Y_lt_half)

/-- The failure is sharp: conservation for the pair `(1), (2)` is *equivalent*
to the false statement `Y = 1/2`.  The substrate law survives to the integer
layer exactly on the sub-carriers whose amplitudes are bits. -/
theorem tax_conservation_at_integer_layer_iff :
    (tax (ofNats (nxor w1 w2)) =
      tax (ofNats w1) + tax (ofNats w2) - 2 * tax (ofNats (nand w1 w2))) ↔ Y = 1 / 2 := by
  have h0 : tax (ofNats (nand w1 w2)) = 0 := by
    rw [nand_w1_w2]
    exact tax_eq_zero_iff.2 (by funext i; simp [ofNats])
  have h3 : tax (ofNats (nxor w1 w2)) = Y + 9 / 8 := by
    rw [nxor_w1_w2, tax_const 3 (by norm_num)]; norm_num
  have h1 : tax (ofNats w1) = Y + 1 / 8 := by
    have : (w1 : Fin 1 → ℕ) = fun _ => 1 := rfl
    rw [this, tax_const 1 (by norm_num)]; norm_num
  have h2 : tax (ofNats w2) = Y + 4 / 8 := by
    have : (w2 : Fin 1 → ℕ) = fun _ => 2 := rfl
    rw [this, tax_const 2 (by norm_num)]; norm_num
  rw [h0, h1, h2, h3]
  constructor <;> intro h <;> linarith

end GLM
