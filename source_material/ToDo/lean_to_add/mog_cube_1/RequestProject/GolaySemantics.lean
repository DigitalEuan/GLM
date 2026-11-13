/-
# The Golay substrate of the Geometric Language Machine, formalised

This file proves the mathematical claims that the GLM's semantic layer rests
on.  The GLM encodes a sentence as a 24-cell MOG object whose cells record
*selectional violations*: cell `c` is set when the argument in a slot brings a
semantic class that the verb requires but the argument lacks, or that the verb
never takes.  The substrate is the extended binary Golay code `[24, 12, 8]`.

What is proved here:

* `golay_min_weight` — a nonzero codeword has weight at least 8.
* `violation_unique_of_wt_le_three` — two violation patterns of weight ≤ 3 with
  the same syndrome are equal.  So a sentence with at most three violated cells
  can be *diagnosed exactly* from its syndrome: the GLM can say which cells
  failed, and hence which word to change.
* `exists_two_wt_four_same_syndrome` — three is sharp: there are two different
  weight-4 patterns with the same syndrome, so at four simultaneous violations
  the diagnosis is genuinely ambiguous.
* `licensed_iff` — a sentence has an empty violation set exactly when every
  slot's requirements are met and nothing forbidden is supplied.
* `tax_eq`, `tax_eq_zero_iff`, `nrci_eq_one_iff`, `nrci_strictMono` — the
  TAX / NRCI readout of a violation pattern is `wt · Q` with `Q = Y + 1/8`,
  it vanishes exactly on licensed sentences, and NRCI decreases strictly as
  more cells are violated.

The two purely finite facts (the weight enumerator bound and the weight-4
witness) are settled by evaluation; everything else is proved algebraically.
-/
import Mathlib

set_option maxRecDepth 10000
set_option autoImplicit false
set_option relaxedAutoImplicit false

namespace GLM

/-! ## 1. The code -/

/-- A word of the substrate: `n` cells, each carrying a bit. -/
abbrev Word (n : Nat) := Fin n → ZMod 2

/-- Hamming weight: the number of cells that are set. -/
def wt {n : Nat} (w : Word n) : Nat := (Finset.univ.filter (fun j => w j ≠ 0)).card

/-- The standard `B` matrix of the extended binary Golay code: an all-ones
border and the circulant of the quadratic residues mod 11. -/
def Bmat : Fin 12 → Fin 12 → ZMod 2 := ![
  ![0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
  ![1, 1, 1, 0, 1, 1, 1, 0, 0, 0, 1, 0],
  ![1, 1, 0, 1, 1, 1, 0, 0, 0, 1, 0, 1],
  ![1, 0, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1],
  ![1, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 0],
  ![1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 0, 1],
  ![1, 1, 0, 0, 0, 1, 0, 1, 1, 0, 1, 1],
  ![1, 0, 0, 0, 1, 0, 1, 1, 0, 1, 1, 1],
  ![1, 0, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0],
  ![1, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 0],
  ![1, 1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 0],
  ![1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 0, 1]]

theorem Bmat_symm : ∀ i j : Fin 12, Bmat i j = Bmat j i := by decide

/-- Row `i` of the generator matrix `G = [I₁₂ | B]`. -/
def gen (i : Fin 12) : Word 24 := fun j =>
  if h : (j : Nat) < 12 then (if (j : Nat) = (i : Nat) then 1 else 0)
  else Bmat i ⟨(j : Nat) - 12, by omega⟩

/-- Encoding a 12-cell message into a 24-cell codeword. -/
def encode (m : Word 12) : Word 24 := fun j => ∑ i, m i * gen i j

/-- Row `i` of the parity-check matrix `H = [B | I₁₂]`. -/
def Hmat (i : Fin 12) : Word 24 := fun j =>
  if h : (j : Nat) < 12 then Bmat i ⟨(j : Nat), h⟩
  else (if (j : Nat) - 12 = (i : Nat) then 1 else 0)

/-- The syndrome: the substrate's loop-check.  `syn v = 0` says `v` is lawful. -/
def syn (v : Word 24) : Word 12 := fun i => ∑ j, Hmat i j * v j

/-- Being a codeword. -/
def IsCodeword (v : Word 24) : Prop := syn v = 0

/-! ## 2. Linearity of the syndrome -/

theorem syn_add (v w : Word 24) : syn (v + w) = syn v + syn w := by
  funext i
  simp only [syn, Pi.add_apply, mul_add]
  exact Finset.sum_add_distrib

theorem syn_zero : syn 0 = 0 := by
  funext i; simp [syn]

/-! ## 3. The code is the kernel of the syndrome -/

/-- The first twelve cells of a word. -/
def head12 (v : Word 24) : Word 12 := fun i => v ⟨(i : Nat), by omega⟩

theorem encode_head (m : Word 12) (i : Fin 12) :
    encode m ⟨(i : Nat), by omega⟩ = m i := by
  simp only [encode, gen]
  rw [Finset.sum_eq_single i]
  · simp
  · intro b _ hb
    have : ¬ ((i : Nat) = (b : Nat)) := fun h => hb (Fin.ext h.symm)
    simp [i.isLt, this]
  · intro h; exact absurd (Finset.mem_univ i) h

theorem encode_tail (m : Word 12) (t : Fin 12) :
    encode m ⟨12 + (t : Nat), by omega⟩ = ∑ i, m i * Bmat i t := by
  simp only [encode, gen]
  refine Finset.sum_congr rfl (fun i _ => ?_)
  have h : ¬ (12 + (t : Nat) < 12) := by omega
  rw [dif_neg h]
  congr 2
  apply Fin.ext
  simp

theorem syn_apply (v : Word 24) (i : Fin 12) :
    syn v i = (∑ j : Fin 12, Bmat i j * v ⟨(j : Nat), by omega⟩)
              + v ⟨12 + (i : Nat), by omega⟩ := by
  show (∑ j : Fin (12+12), Hmat i j * v j) = _
  rw [Fin.sum_univ_add]
  have h1 : ∀ j : Fin 12, Hmat i (Fin.castAdd 12 j) * v (Fin.castAdd 12 j)
      = Bmat i j * v ⟨(j : Nat), by omega⟩ := by
    intro j
    have hc : ((Fin.castAdd 12 j : Fin 24) : Nat) = (j : Nat) := rfl
    simp only [Hmat, hc, j.isLt, dif_pos]
    congr 2
  have h2 : ∑ j : Fin 12, Hmat i (Fin.natAdd 12 j) * v (Fin.natAdd 12 j)
      = v ⟨12 + (i : Nat), by omega⟩ := by
    rw [Finset.sum_eq_single i]
    · have hc : ((Fin.natAdd 12 i : Fin 24) : Nat) = 12 + (i : Nat) := rfl
      simp only [Hmat, hc]
      norm_num
      congr 1
      apply Fin.ext
      simp
      omega
    · intro b _ hb
      have hbn : ((Fin.natAdd 12 b : Fin 24) : Nat) = 12 + (b : Nat) := rfl
      have hne : ¬ (12 + (b:Nat) - 12 = (i:Nat)) := by
        intro h; exact hb (Fin.ext (by omega))
      simp only [Hmat, hbn, hne]
      norm_num
    · intro h; exact absurd (Finset.mem_univ i) h
  rw [Finset.sum_congr rfl (fun j _ => h1 j), h2]

theorem syn_encode (m : Word 12) : syn (encode m) = 0 := by
  funext i
  rw [syn_apply]
  have h1 : ∀ j : Fin 12, encode m ⟨(j : Nat), by omega⟩ = m j := encode_head m
  have h2 : encode m ⟨12 + (i : Nat), by omega⟩ = ∑ j, m j * Bmat j i := encode_tail m i
  simp only [h1, h2]
  have : ∀ j : Fin 12, Bmat i j * m j = m j * Bmat j i := by
    intro j; rw [Bmat_symm i j]; ring
  simp only [this]
  simp [CharTwo.add_self_eq_zero]

theorem encode_head12 (v : Word 24) (hv : syn v = 0) : encode (head12 v) = v := by
  funext j
  by_cases h : (j : Nat) < 12
  · have hj : j = (⟨((⟨(j : Nat), h⟩ : Fin 12) : Nat), by omega⟩ : Fin 24) := by
      apply Fin.ext; simp
    rw [hj, encode_head]
    simp [head12]
  · set t : Fin 12 := ⟨(j : Nat) - 12, by omega⟩ with ht
    have hj : j = (⟨12 + (t : Nat), by omega⟩ : Fin 24) := by
      apply Fin.ext; simp [ht]; omega
    rw [hj, encode_tail]
    have hs := congrFun hv t
    rw [syn_apply] at hs
    have hv2 : v ⟨12 + (t : Nat), by omega⟩ =
        ∑ k : Fin 12, Bmat t k * v ⟨(k : Nat), by omega⟩ := by
      have h0 : (0 : Word 12) t = 0 := rfl
      rw [h0] at hs
      have h2 := add_eq_zero_iff_neg_eq.mp hs
      rw [CharTwo.neg_eq] at h2
      exact h2.symm
    rw [hv2]
    refine Finset.sum_congr rfl (fun i _ => ?_)
    rw [Bmat_symm i t]
    simp only [head12]
    ring

/-! ## 4. Minimum weight 8 -/

private theorem min_weight_encode : ∀ m : Word 12, m ≠ 0 → 8 ≤ wt (encode m) := by
  native_decide

/-- A nonzero codeword of the substrate has at least eight cells set. -/
theorem golay_min_weight (v : Word 24) (hv : IsCodeword v) (h0 : v ≠ 0) : 8 ≤ wt v := by
  have hE : encode (head12 v) = v := encode_head12 v hv
  have hm : head12 v ≠ 0 := by
    intro h
    apply h0
    rw [← hE, h]
    funext j
    simp [encode]
  have := min_weight_encode (head12 v) hm
  rwa [hE] at this

/-! ## 5. Weight is subadditive -/

theorem wt_add_le (u v : Word 24) : wt (u + v) ≤ wt u + wt v := by
  classical
  have hsub : (Finset.univ.filter (fun j => (u + v) j ≠ 0)) ⊆
      (Finset.univ.filter (fun j => u j ≠ 0)) ∪ (Finset.univ.filter (fun j => v j ≠ 0)) := by
    intro j hj
    simp only [Finset.mem_filter, Finset.mem_univ, true_and, Pi.add_apply] at hj
    simp only [Finset.mem_union, Finset.mem_filter, Finset.mem_univ, true_and]
    by_contra hc
    push_neg at hc
    obtain ⟨h1, h2⟩ := hc
    exact hj (by rw [h1, h2, add_zero])
  calc wt (u + v) ≤ ((Finset.univ.filter (fun j => u j ≠ 0)) ∪
        (Finset.univ.filter (fun j => v j ≠ 0))).card := Finset.card_le_card hsub
    _ ≤ _ := Finset.card_union_le _ _

/-! ## 6. Exact diagnosis up to three violated cells -/

/-- Two violation patterns with at most three violated cells each and the same
syndrome are the same pattern.  The substrate can therefore name exactly which
cells a broken sentence violated, as long as there are at most three of them. -/
theorem violation_unique_of_wt_le_three (u v : Word 24)
    (hu : wt u ≤ 3) (hv : wt v ≤ 3) (h : syn u = syn v) : u = v := by
  by_contra hne
  have hcode : IsCodeword (u + v) := by
    unfold IsCodeword
    rw [syn_add, h]
    funext i; simp [CharTwo.add_self_eq_zero]
  have h0 : u + v ≠ 0 := by
    intro hz
    apply hne
    have : u = -v := by
      have := congrArg (fun x => x + (-v)) hz
      simpa using this
    rw [this]; funext j; simp [CharTwo.neg_eq]
  have h8 := golay_min_weight (u + v) hcode h0
  have := wt_add_le u v
  omega

/-- Three is sharp: two different patterns of four violated cells share a
syndrome, so at four violations the diagnosis is genuinely ambiguous.  (The
witnesses are the two halves of an octad: their sum is a codeword.) -/
theorem exists_two_wt_four_same_syndrome :
    ∃ u v : Word 24, u ≠ v ∧ wt u = 4 ∧ wt v = 4 ∧ syn u = syn v := by
  refine ⟨fun j => if (j : Nat) ∈ ({1, 12, 13, 14} : Finset Nat) then 1 else 0,
          fun j => if (j : Nat) ∈ ({16, 17, 18, 22} : Finset Nat) then 1 else 0,
          ?_, ?_, ?_, ?_⟩ <;> native_decide

/-! ## 7. The semantic layer -/

/-- What a verb expects of one argument slot, and what the argument supplies.
All three are sets of MOG cells. -/
structure Slot where
  /-- cells the verb needs the argument to carry -/
  required : Finset (Fin 24)
  /-- cells the verb never takes in this slot -/
  forbidden : Finset (Fin 24)
  /-- cells the argument actually carries -/
  provision : Finset (Fin 24)

/-- The violated cells: what the verb needs and the argument lacks, together
with what the argument brings and the verb refuses. -/
def Slot.violated (s : Slot) : Finset (Fin 24) :=
  (s.required \ s.provision) ∪ (s.provision ∩ s.forbidden)

/-- The violation pattern as a word of the substrate. -/
def Slot.pattern (s : Slot) : Word 24 := fun j => if j ∈ s.violated then 1 else 0

theorem Slot.wt_pattern (s : Slot) : wt s.pattern = s.violated.card := by
  classical
  unfold wt Slot.pattern
  congr 1
  ext j
  by_cases h : j ∈ s.violated <;> simp [h]

/-- A slot is licensed exactly when the argument meets every requirement and
supplies nothing forbidden. -/
theorem licensed_iff (s : Slot) :
    s.violated = ∅ ↔ s.required ⊆ s.provision ∧ Disjoint s.provision s.forbidden := by
  constructor
  · intro h
    rw [Slot.violated, Finset.union_eq_empty] at h
    obtain ⟨h1, h2⟩ := h
    refine ⟨?_, ?_⟩
    · intro x hx
      by_contra hn
      exact absurd (Finset.mem_sdiff.mpr ⟨hx, hn⟩) (by simp [h1])
    · rw [Finset.disjoint_iff_inter_eq_empty]; exact h2
  · rintro ⟨h1, h2⟩
    rw [Slot.violated, Finset.union_eq_empty]
    constructor
    · rw [Finset.sdiff_eq_empty_iff_subset]; exact h1
    · rwa [← Finset.disjoint_iff_inter_eq_empty]

/-! ## 8. TAX and NRCI -/

/-- The read quantum `Y = 1/(π + 2/π)`. -/
noncomputable def Y : ℝ := 1 / (Real.pi + 2 / Real.pi)

/-- The activation quantum `Q = Y + 1/8`. -/
noncomputable def Q : ℝ := Y + 1 / 8

/-- The coherence budget. -/
def Bbudget : ℝ := 10

theorem Y_pos : 0 < Y := by
  have h : 0 < Real.pi + 2 / Real.pi := by positivity
  simpa [Y] using (one_div_pos.mpr h)

theorem Q_pos : 0 < Q := by
  have := Y_pos; unfold Q; linarith

/-- `TAX(v) = HW(v)·Y + ‖v‖²/8`.  For a 0/1 pattern `‖v‖² = HW(v)`. -/
noncomputable def tax (v : Word 24) : ℝ := (wt v : ℝ) * Y + (wt v : ℝ) / 8

/-- The tax of a violation pattern is the number of violated cells times the
activation quantum. -/
theorem tax_eq (v : Word 24) : tax v = (wt v : ℝ) * Q := by
  unfold tax Q; ring

theorem wt_eq_zero_iff {n : Nat} (v : Word n) : wt v = 0 ↔ v = 0 := by
  classical
  constructor
  · intro h
    funext j
    by_contra hj
    have hj' : v j ≠ 0 := hj
    have : j ∈ Finset.univ.filter (fun k => v k ≠ 0) := by
      simp only [Finset.mem_filter, Finset.mem_univ, true_and]
      exact hj'
    rw [wt, Finset.card_eq_zero] at h
    rw [h] at this
    simp at this
  · intro h; subst h; simp [wt]

/-- A sentence costs nothing exactly when no cell is violated. -/
theorem tax_eq_zero_iff (v : Word 24) : tax v = 0 ↔ v = 0 := by
  rw [tax_eq, ← wt_eq_zero_iff v]
  constructor
  · intro h
    rcases mul_eq_zero.mp h with h1 | h2
    · exact_mod_cast h1
    · exact absurd h2 (ne_of_gt Q_pos)
  · intro h; rw [h]; simp

/-- The coherence index `NRCI(v) = B / (B + TAX(v))`. -/
noncomputable def nrci (v : Word 24) : ℝ := Bbudget / (Bbudget + tax v)

theorem tax_nonneg (v : Word 24) : 0 ≤ tax v := by
  rw [tax_eq]
  have := Q_pos
  positivity

theorem nrci_eq_one_iff (v : Word 24) : nrci v = 1 ↔ v = 0 := by
  have hB : (0:ℝ) < Bbudget := by norm_num [Bbudget]
  have hpos : 0 < Bbudget + tax v := by have := tax_nonneg v; linarith
  rw [nrci, div_eq_one_iff_eq (ne_of_gt hpos)]
  constructor
  · intro h; exact (tax_eq_zero_iff v).mp (by linarith)
  · intro h; rw [(tax_eq_zero_iff v).mpr h]; ring

/-- More violated cells means strictly less coherence. -/
theorem nrci_strictMono (u v : Word 24) (h : wt u < wt v) : nrci v < nrci u := by
  have hB : (0:ℝ) < Bbudget := by norm_num [Bbudget]
  have htu := tax_nonneg u
  have htv := tax_nonneg v
  have hlt : tax u < tax v := by
    rw [tax_eq, tax_eq]
    exact mul_lt_mul_of_pos_right (by exact_mod_cast h) Q_pos
  unfold nrci
  apply div_lt_div_of_pos_left hB (by linarith) (by linarith)

end GLM

/-! ## 9. Axiom audit -/
#print axioms GLM.golay_min_weight
#print axioms GLM.violation_unique_of_wt_le_three
#print axioms GLM.exists_two_wt_four_same_syndrome
#print axioms GLM.licensed_iff
#print axioms GLM.tax_eq_zero_iff
#print axioms GLM.nrci_strictMono
