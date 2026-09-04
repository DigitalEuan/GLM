/-
# Literal Data Physics: the archive's "internal experience" table, settled

`GMHGL/ldp_complete_mapping.md` in the supplied archive claims a physics for a
24-bit word: an *energy* (its syndrome weight), a *ground state* (a codeword),
a *gradient* every excited state can descend, a *relaxation* that reaches the
ground state, a conserved *charge* (parity), a *mass defect* for the AND of two
codewords, and a *rigidity* under a one-bit flip.  Each of those was measured
there by sampling — "100% of vectors can descend", "mean energy 6.05", "mean
mass lost 13.39", "reaches ground in ~3.81 steps".

This file replaces the sample by a proof, for the code the substrate actually
uses (`Golay/Code.lean`, `H = [B | I₁₂]`):

* `energy_eq_zero_iff` — the ground states are exactly the codewords, so the
  archive's "energy" really is a potential for the code;
* `energy_descent` — *every* excited word has a neighbour of energy exactly one
  lower.  The measured 100% is not a sampling artefact: the systematic half of
  `H` supplies the descending coordinate outright;
* `exists_relaxation` / `dist_le_energy` — descending `energy v` times reaches a
  codeword, and the flips can be named in advance;
* `energy_le_twelve` — so relaxation never takes more than twelve steps;
* `mean_energy` — the *exact* mean energy over the 4,096 cosets is `6`, not the
  sampled `6.05`;
* `rigidity` — a one-bit flip of a codeword is never a codeword;
* `parity_conservation` — XOR conserves weight mod 2 (this one holds for any
  sets at all, and is proved that way);
* `mass_defect` — for two distinct nonzero codewords `12 ≤ wt (a ∪ b)`, i.e.
  `wt a + wt b - wt (a ∩ b) ≥ 12`, the archive's "mass defect ≥ 12".  It is a
  consequence of minimum weight 8 alone, and is proved for an arbitrary code of
  minimum weight 8 before being specialised;
* `forbidden_zone` — no codeword has a weight in `{1,…,7} ∪ {9,10,11}`.

The one item of the archive's table that does *not* survive as stated is the
claim that the mean energy is `6.05`; the true value is `6` exactly, and the
discrepancy is the sampling error the measurement did not report.
-/
import Mathlib
import RequestProject.GLM.Golay.Code
import RequestProject.GLM.Golay.Sextet
import RequestProject.GLM.GolayWeightEnum

namespace GLM.Golay24

open Finset

/-! ## 1. Energy: the weight of the syndrome -/

/-- The weight of a syndrome: how many of the twelve parity bits are set. -/
def synWt (f : Syn) : ℕ := #(univ.filter (fun i : Fin 12 => f i = 1))

/-- The archive's *energy* of a word: the weight of its syndrome.  Zero exactly
on the code, and the quantity its "gradient" descends. -/
def energy (v : Word) : ℕ := synWt (syn v)

theorem synWt_eq_zero_iff {f : Syn} : synWt f = 0 ↔ f = 0 := by
  unfold synWt
  rw [Finset.card_eq_zero, Finset.filter_eq_empty_iff]
  constructor
  · intro h
    funext i
    have hi := h (mem_univ i)
    revert hi
    have : ∀ x : ZMod 2, ¬ x = 1 → x = 0 := by decide
    exact fun hx => this (f i) hx
  · rintro rfl i _
    have : ∀ x : ZMod 2, x = 0 → ¬ x = 1 := by decide
    exact this _ rfl

/-- **The ground states are exactly the codewords.** -/
theorem energy_eq_zero_iff {v : Word} : energy v = 0 ↔ IsCodeword v :=
  synWt_eq_zero_iff

/-- The energy of a word never exceeds twelve, there being twelve parity bits. -/
theorem energy_le_twelve (v : Word) : energy v ≤ 12 := by
  unfold energy synWt
  simpa using Finset.card_filter_le (univ : Finset (Fin 12)) _

/-! ## 2. The gradient: every excited word can descend -/

/-- The coordinate carrying the `j`-th parity bit: position `12 + j`, where the
identity block of `H = [B | I₁₂]` sits. -/
def unitPos (j : Fin 12) : Fin 24 := ⟨12 + (j : ℕ), by omega⟩

/-- The `j`-th unit syndrome. -/
def unitSyn (j : Fin 12) : Syn := fun i => if i = j then 1 else 0

/-- Its parity-check column is the `j`-th unit vector.  This is the whole
content of "systematic": the code carries its own descent directions. -/
theorem col_unitPos (j : Fin 12) : col (unitPos j) = unitSyn j := by
  funext i
  revert i j
  decide

/-- Flipping one coordinate of a word. -/
def flip (v : Word) (k : Fin 24) : Word := symmDiff v {k}

theorem syn_singleton (k : Fin 24) : syn ({k} : Word) = col k := by
  simp [syn]

theorem syn_flip (v : Word) (k : Fin 24) : syn (flip v k) = syn v + col k := by
  unfold flip
  rw [syn_symmDiff, syn_singleton]

/-- Clearing a set parity bit lowers the syndrome weight by exactly one. -/
theorem synWt_add_unit {f : Syn} {j : Fin 12} (hj : f j = 1) :
    synWt (f + unitSyn j) + 1 = synWt f := by
  have hset : (univ.filter (fun i : Fin 12 => (f + unitSyn j) i = 1))
      = (univ.filter (fun i : Fin 12 => f i = 1)).erase j := by
    ext i
    simp only [Finset.mem_filter, Finset.mem_univ, true_and, Finset.mem_erase,
      Pi.add_apply]
    by_cases h : i = j
    · subst h
      have hu : unitSyn i i = (1 : ZMod 2) := by simp [unitSyn]
      rw [hj, hu]
      constructor
      · intro hc; exact absurd hc (by decide)
      · rintro ⟨hne, -⟩; exact absurd rfl hne
    · have hu : unitSyn j i = (0 : ZMod 2) := by simp [unitSyn, h]
      rw [hu, add_zero]
      simp [h]
  have hmem : j ∈ univ.filter (fun i : Fin 12 => f i = 1) := by simp [hj]
  unfold synWt
  rw [hset, Finset.card_erase_of_mem hmem]
  have : 1 ≤ #(univ.filter (fun i : Fin 12 => f i = 1)) := Finset.card_pos.mpr ⟨j, hmem⟩
  omega

/-- **The gradient.**  Every excited word has a neighbour of energy exactly one
lower — the archive's "100% of vectors can descend", proved rather than
sampled. -/
theorem energy_descent {v : Word} (hv : ¬ IsCodeword v) :
    ∃ k : Fin 24, energy (flip v k) + 1 = energy v := by
  have hne : syn v ≠ 0 := hv
  obtain ⟨j, hj⟩ : ∃ j : Fin 12, syn v j = 1 := by
    by_contra h
    push_neg at h
    exact hne (funext fun i => by
      have := h i
      revert this
      have : ∀ x : ZMod 2, ¬ x = 1 → x = 0 := by decide
      exact fun hx => this _ hx)
  refine ⟨unitPos j, ?_⟩
  rw [energy, energy, syn_flip, show col (unitPos j) = unitSyn j from col_unitPos j]
  exact synWt_add_unit hj

/-- A codeword, by contrast, has no lower neighbour: it is a strict local
minimum, since no parity-check column vanishes. -/
theorem col_ne_zero (k : Fin 24) : col k ≠ 0 := by
  revert k; decide

theorem codeword_local_min {c : Word} (hc : IsCodeword c) (k : Fin 24) :
    0 < energy (flip c k) := by
  rw [energy, syn_flip, hc, zero_add]
  have : synWt (col k) ≠ 0 := fun h => col_ne_zero k (synWt_eq_zero_iff.mp h)
  omega

/-- **Rigidity.**  A one-bit flip of a codeword is never a codeword. -/
theorem rigidity {c : Word} (hc : IsCodeword c) (k : Fin 24) :
    ¬ IsCodeword (flip c k) := by
  intro h
  have := codeword_local_min hc k
  rw [energy_eq_zero_iff.mpr h] at this
  exact absurd this (lt_irrefl 0)

/-! ## 3. Relaxation: the descent terminates, and where -/

/-- The flips that clear the syndrome: the coordinates `12 + j` of the parity
bits that are set. -/
def relaxSet (v : Word) : Word :=
  (univ.filter (fun i : Fin 12 => syn v i = 1)).image unitPos

theorem unitPos_injective : Function.Injective unitPos := by
  intro a b h
  have : (12 : ℕ) + (a : ℕ) = 12 + (b : ℕ) := congrArg Fin.val h
  exact Fin.ext (by omega)

theorem wt_relaxSet (v : Word) : wt (relaxSet v) = energy v := by
  unfold relaxSet wt energy synWt
  exact Finset.card_image_of_injective _ unitPos_injective

theorem syn_relaxSet (v : Word) : syn (relaxSet v) = syn v := by
  have hsum : syn (relaxSet v)
      = ∑ j ∈ univ.filter (fun i : Fin 12 => syn v i = 1), col (unitPos j) := by
    unfold relaxSet syn
    exact Finset.sum_image (fun a _ b _ h => unitPos_injective h)
  rw [hsum]
  funext i
  simp only [col_unitPos, unitSyn, Finset.sum_apply]
  rw [Finset.sum_ite_eq (univ.filter (fun i : Fin 12 => syn v i = 1)) i
    (fun _ => (1 : ZMod 2))]
  by_cases h : syn v i = 1
  · simp [h]
  · have hz : ∀ x : ZMod 2, ¬ x = 1 → x = 0 := by decide
    simp [hz _ h]

/-- **Relaxation.**  Every word reaches a codeword by flipping exactly `energy v`
coordinates, and they can be named in advance. -/
theorem exists_relaxation (v : Word) :
    ∃ u : Word, wt u = energy v ∧ IsCodeword (symmDiff v u) := by
  refine ⟨relaxSet v, wt_relaxSet v, ?_⟩
  unfold IsCodeword
  rw [syn_symmDiff, syn_relaxSet]
  funext i
  have : ∀ x : ZMod 2, x + x = 0 := by decide
  exact this _

/-- Consequently the distance from a word to the code is at most its energy. -/
theorem dist_le_energy (v : Word) : ∃ c : Word, IsCodeword c ∧ hdist v c ≤ energy v := by
  obtain ⟨u, hu, hc⟩ := exists_relaxation v
  exact ⟨symmDiff v u, hc, by
    rw [hdist_eq_wt_symmDiff, symmDiff_symmDiff_cancel_left, hu]⟩

/-! ## 4. The exact mean energy -/

/-- The all-ones syndrome. -/
def onesSyn : Syn := fun _ => 1

/-- Complementing a syndrome complements its weight. -/
theorem synWt_add_ones (f : Syn) : synWt f + synWt (f + onesSyn) = 12 := by
  have hcompl : (univ.filter (fun i : Fin 12 => (f + onesSyn) i = 1))
      = univ.filter (fun i : Fin 12 => ¬ (f i = 1)) := by
    ext i
    have hx : ∀ x : ZMod 2, (x + 1 = 1) ↔ ¬ (x = 1) := by decide
    simpa [onesSyn] using hx (f i)
  unfold synWt
  rw [hcompl]
  have := Finset.card_filter_add_card_filter_not
    (s := (univ : Finset (Fin 12))) (p := fun i : Fin 12 => f i = 1)
  simpa using this

theorem card_univ_syn : #(univ : Finset Syn) = 4096 := by simp

theorem sum_synWt : (∑ f : Syn, synWt f) = 24576 := by
  have hshift : (∑ f : Syn, synWt (f + onesSyn)) = ∑ f : Syn, synWt f :=
    Fintype.sum_equiv (Equiv.addRight onesSyn) _ _ (fun f => rfl)
  have hsum : (∑ f : Syn, (synWt f + synWt (f + onesSyn))) = 12 * 4096 := by
    rw [Finset.sum_congr rfl (fun f _ => synWt_add_ones f), Finset.sum_const,
      card_univ_syn, smul_eq_mul]
  rw [Finset.sum_add_distrib, hshift] at hsum
  omega

/-- **The mean energy is `6` exactly**, over the 4,096 cosets — the archive
sampled `6.05`. -/
theorem mean_energy : (∑ f : Syn, (synWt f : ℚ)) / 4096 = 6 := by
  have h : (∑ f : Syn, (synWt f : ℚ)) = ((∑ f : Syn, synWt f : ℕ) : ℚ) := by
    push_cast; ring
  rw [h, sum_synWt]
  norm_num

/-! ## 5. Charge: parity is conserved by XOR -/

/-- **Parity conservation**, for arbitrary finite sets: the weight of a
symmetric difference agrees mod 2 with the sum of the weights. -/
theorem card_symmDiff_add_two_inter {α : Type*} [DecidableEq α] (a b : Finset α) :
    #(symmDiff a b) + 2 * #(a ∩ b) = #a + #b := by
  have hsub : a ∩ b ⊆ a ∪ b := (Finset.inter_subset_left).trans Finset.subset_union_left
  have h : symmDiff a b = (a ∪ b) \ (a ∩ b) := by
    rw [symmDiff_eq_sup_sdiff_inf]; rfl
  have h1 : #((a ∪ b) \ (a ∩ b)) = #(a ∪ b) - #(a ∩ b) := by
    rw [Finset.card_sdiff, Finset.inter_eq_left.mpr hsub]
  have h2 := Finset.card_union_add_card_inter a b
  have hle : #(a ∩ b) ≤ #(a ∪ b) := Finset.card_le_card hsub
  rw [h, h1]
  omega

theorem parity_conservation {α : Type*} [DecidableEq α] (a b : Finset α) :
    #(symmDiff a b) % 2 = (#a + #b) % 2 := by
  have h1 := card_symmDiff_add_two_inter a b
  omega

theorem wt_symmDiff_parity (a b : Word) : wt (symmDiff a b) % 2 = (wt a + wt b) % 2 :=
  parity_conservation a b

/-! ## 6. Mass defect -/

/-- **Mass defect, in general.**  In any code whose nonzero words have weight at
least `d` and whose distinct words are at distance at least `d`, the union of
two distinct nonzero words has weight at least `3d/2`: from
`2·wt (a ∪ b) = wt (a ∆ b) + wt a + wt b`. -/
theorem card_union_ge_of_min_weight {α : Type*} [DecidableEq α] {a b : Finset α}
    {d : ℕ} (ha : d ≤ #a) (hb : d ≤ #b) (hab : d ≤ #(symmDiff a b)) :
    3 * d ≤ 2 * #(a ∪ b) := by
  have hcard := card_symmDiff_add_two_inter a b
  have hui := Finset.card_union_add_card_inter a b
  omega

/-- **Mass defect** for the substrate's code: two distinct nonzero codewords
occupy at least twelve of the twenty-four cells between them, so
`wt a + wt b - wt (a ∩ b) ≥ 12`. -/
theorem mass_defect {a b : Word} (ha : IsCodeword a) (hb : IsCodeword b)
    (hane : a ≠ ∅) (hbne : b ≠ ∅) (hne : a ≠ b) : 12 ≤ wt (a ∪ b) := by
  have h8a : 8 ≤ wt a := golay_min_weight ha hane
  have h8b : 8 ≤ wt b := golay_min_weight hb hbne
  have hsd : IsCodeword (symmDiff a b) := by
    unfold IsCodeword
    rw [syn_symmDiff, ha, hb, add_zero]
  have hsdne : symmDiff a b ≠ ∅ := by
    intro h
    exact hne (symmDiff_eq_bot.mp h)
  have h8 : 8 ≤ wt (symmDiff a b) := golay_min_weight hsd hsdne
  have := card_union_ge_of_min_weight (d := 8) h8a h8b h8
  unfold wt at *
  omega

/-! ## 7. The forbidden zone -/

/-- **The forbidden zone.**  No codeword has a weight in `{1,…,7}` or
`{9,10,11}`: the allowed masses are `0, 8, 12, 16, 24`. -/
theorem forbidden_zone {c : Word} (hc : IsCodeword c) :
    ¬ (1 ≤ wt c ∧ wt c ≤ 7) ∧ ¬ (9 ≤ wt c ∧ wt c ≤ 11) := by
  rcases golay_weight_mem hc with h | h | h | h | h <;> rw [h] <;> omega

end GLM.Golay24
