/-
# The UBP law register, read through the code the GLM runs on

`studies/LAW_REGISTER_STUDY.md` reviews the sixty-five laws of
`source_material/retained_laws_verified_65.csv`.  Most of the structural laws
it keeps are already theorems elsewhere in this development (the census of
cosets, the Steiner system, the weight enumerator).  This file proves the four
statements the review needed and did not find:

* **When a complete decoder is right** (`unique_leader_iff`): an error pattern
  is the unique lightest word of its coset — so a complete decoder returns it —
  exactly when it has weight at most `3`.  This is the precise form of the
  register's "hardened storage", "fourth flip" and "1-bit correction" laws.
* **Weight five is always miscorrected** (`wt_five_coset_three`): a weight-5
  error sits in a coset of weight `3`, through the unique octad on its five
  points, so the decoder answers — wrongly — instead of refusing.
* **Only XOR is a code operation** (`and_not_closed`, `or_not_closed`): the
  intersection and the union of two codewords need not be codewords, so the
  register's "Boolean logic is isomorphic to vector arithmetic in the Golay
  substrate" holds for exclusive-or only.
* **Why the two means agreed to six decimals** (`moment_agree`,
  `moment_eight_differs`): the first seven moments of the codeword weight equal
  those of a uniformly random 24-bit word, and the eighth does not.  So any
  statistic that is a polynomial of degree at most seven in the weight has the
  same mean over the code as over all words, and the NRCI — not a polynomial —
  agrees only approximately (`nrci_means_differ`).
-/
import Mathlib
import RequestProject.GLM.Golay.Census
import RequestProject.GLM.Steiner

namespace GLM.LawRegister

open Finset GLM.Golay24

/-! ## 1. When a complete decoder is right -/

/-- `e` is the unique lightest word of its coset: every other word with the
same syndrome is strictly heavier.  A complete (maximum-likelihood) decoder
returns `e` as the error exactly in this case. -/
def IsUniqueLeader (e : Word) : Prop :=
  ∀ u : Word, syn u = syn e → u ≠ e → wt e < wt u

/-- A nonzero codeword has weight at least `8`. -/
theorem eight_le_wt_of_codeword {c : Word} (hc : IsCodeword c) (hne : c ≠ ∅) :
    8 ≤ wt c :=
  golay_min_weight hc hne

/-- Adding a codeword that contains `e` leaves the syndrome, and the
complement of `e` inside it is what remains. -/
theorem syn_sdiff_of_subset {e o : Word} (ho : IsCodeword o) (h : e ⊆ o) :
    syn (o \ e) = syn e := by
  have : symmDiff e o = o \ e := symmDiff_of_le h
  rw [← this, syn_symmDiff, ho, add_zero]

/-- **The decoder is right exactly up to weight three.** -/
theorem unique_leader_iff (e : Word) : IsUniqueLeader e ↔ wt e ≤ 3 := by
  constructor
  · intro hU
    by_contra hgt
    push_neg at hgt
    rcases Nat.lt_or_ge (wt e) 5 with h5 | h5
    · have h4 : e.card = 4 := by unfold wt at hgt h5; omega
      have hne : (through e).Nonempty := by
        rw [← Finset.card_pos, card_octads_through_four h4]; norm_num
      obtain ⟨o, ho⟩ := hne
      obtain ⟨hoct, heo⟩ := mem_through.1 ho
      obtain ⟨hoc, how⟩ := mem_octads.1 hoct
      have hsyn := syn_sdiff_of_subset hoc heo
      have hcard : wt (o \ e) = 4 := by
        unfold wt at how ⊢; rw [Finset.card_sdiff_of_subset heo, how, h4]
      have hne' : o \ e ≠ e := by
        intro h
        have hdisj : Disjoint (o \ e) e := Finset.sdiff_disjoint
        rw [h] at hdisj
        have : e = ∅ := (Finset.disjoint_self_iff_empty e).1 hdisj
        rw [this] at h4; simp at h4
      have := hU _ hsyn hne'
      omega
    · obtain ⟨u, hsu, hwu⟩ := exists_wt_eq_cosetWt (syn e)
      have hle := cosetWt_le_four (syn e)
      have hne' : u ≠ e := by intro h; rw [h] at hwu; omega
      have := hU u hsu hne'
      omega
  · intro he u hsu hne
    have hc : IsCodeword (symmDiff e u) := (syn_eq_iff_isCodeword_symmDiff e u).1 hsu.symm
    have hne' : symmDiff e u ≠ ∅ := by
      intro h
      exact hne (symm (symmDiff_eq_bot.1 h))
    have h8 := golay_min_weight hc hne'
    have htri : (symmDiff e u).card ≤ e.card + u.card := by
      calc (symmDiff e u).card ≤ (e ∪ u).card :=
            Finset.card_le_card (symmDiff_le_sup (a := e) (b := u))
        _ ≤ e.card + u.card := Finset.card_union_le _ _
    unfold wt at h8 he ⊢
    omega

/-- **A weight-5 error is miscorrected.**  Its coset has weight `3`: the decoder
does not refuse, and the word it returns is not the one that was sent. -/
theorem wt_five_coset_three {e : Word} (he : wt e = 5) : cosetWt (syn e) = 3 := by
  obtain ⟨o, ⟨hoct, heo⟩, -⟩ := unique_octad (T := e) he
  obtain ⟨hoc, how⟩ := mem_octads.1 hoct
  have hsyn := syn_sdiff_of_subset hoc heo
  have hcard : wt (o \ e) = 3 := by
    unfold wt at how he ⊢; rw [Finset.card_sdiff_of_subset heo, how, he]
  rw [← hsyn, cosetWt_of_wt_le_three (le_of_eq hcard), hcard]

/-- **A weight-4 error is refused, never miscorrected**: its coset has weight
`4`, where six lightest words tie (`Golay24.tetrad_class_card`). -/
theorem wt_four_refused {e : Word} (he : wt e = 4) : cosetWt (syn e) = 4 :=
  cosetWt_of_wt_four he

/-! ## 2. Only XOR is a code operation -/

/-- Row 1 of the generator `[I₁₂ | B]`: an octad. -/
def row1 : Word := {1, 12, 13, 14, 16, 17, 18, 22}

/-- Row 2 of the generator `[I₁₂ | B]`: an octad. -/
def row2 : Word := {2, 12, 13, 15, 16, 17, 21, 23}

theorem row1_codeword : IsCodeword row1 := by
  unfold IsCodeword row1; decide

theorem row2_codeword : IsCodeword row2 := by
  unfold IsCodeword row2; decide

/-- The exclusive-or of two codewords is a codeword (linearity). -/
theorem xor_closed {a b : Word} (ha : IsCodeword a) (hb : IsCodeword b) :
    IsCodeword (symmDiff a b) :=
  isCodeword_symmDiff ha hb

/-- **AND is not a code operation.** -/
theorem and_not_closed : ∃ a b : Word, IsCodeword a ∧ IsCodeword b ∧ ¬ IsCodeword (a ∩ b) := by
  refine ⟨row1, row2, row1_codeword, row2_codeword, fun h => ?_⟩
  have hw : wt (row1 ∩ row2) = 4 := by decide
  rcases golay_weight_mem h with h' | h' | h' | h' | h' <;> omega

/-- **OR is not a code operation.** -/
theorem or_not_closed : ∃ a b : Word, IsCodeword a ∧ IsCodeword b ∧ ¬ IsCodeword (a ∪ b) := by
  refine ⟨row1, row2, row1_codeword, row2_codeword, fun h => ?_⟩
  have hw : wt (row1 ∪ row2) = 12 := by decide
  have hx : symmDiff (row1 ∪ row2) (symmDiff row1 row2) = row1 ∩ row2 := by decide
  have hc := isCodeword_symmDiff h (isCodeword_symmDiff row1_codeword row2_codeword)
  rw [hx] at hc
  have hw4 : wt (row1 ∩ row2) = 4 := by decide
  rcases golay_weight_mem hc with h' | h' | h' | h' | h' <;> omega

/-! ## 3. The weight moments of the code -/

/-- The `k`-th weight moment of the code, summed over the codewords. -/
def codeMoment (k : ℕ) : ℕ := ∑ c ∈ codewords, (wt c) ^ k

/-- The `k`-th weight moment of all `2²⁴` words, summed. -/
def wordMoment (k : ℕ) : ℕ := ∑ w ∈ range 25, Nat.choose 24 w * w ^ k

/-- The code moment through the weight enumerator. -/
theorem codeMoment_eq (k : ℕ) :
    codeMoment k = 0 ^ k + 759 * 8 ^ k + 2576 * 12 ^ k + 759 * 16 ^ k + 24 ^ k := by
  unfold codeMoment
  have hmaps : ∀ c ∈ codewords, wt c ∈ ({0, 8, 12, 16, 24} : Finset ℕ) := by
    intro c hc
    rcases golay_weight_mem (mem_codewords.1 hc) with h | h | h | h | h <;> rw [h] <;> decide
  rw [← Finset.sum_fiberwise_of_maps_to hmaps]
  have key : ∀ w, ∑ c ∈ codewords with wt c = w, wt c ^ k =
      #(codewords.filter fun c => wt c = w) * w ^ k := by
    intro w
    rw [Finset.sum_congr rfl (fun c hc => by rw [(Finset.mem_filter.1 hc).2]),
      Finset.sum_const, smul_eq_mul]
  obtain ⟨h0, h8, h12, h16, h24⟩ := golay_weight_enumerator
  rw [Finset.sum_insert (by decide), Finset.sum_insert (by decide), Finset.sum_insert (by decide),
    Finset.sum_insert (by decide), Finset.sum_singleton, key, key, key, key, key,
    h0, h8, h12, h16, h24]
  ring

/-- **The first seven moments agree**: averaged over the `4096` codewords or
over all `2²⁴` words, `wt ^ k` has the same mean for every `k ≤ 7`. -/
theorem moment_agree {k : ℕ} (hk : k ≤ 7) : 4096 * codeMoment k = wordMoment k := by
  rw [codeMoment_eq]
  interval_cases k <;> simp [wordMoment, Finset.sum_range_succ, Nat.choose]

/-- **The eighth does not.** -/
theorem moment_eight_differs : 4096 * codeMoment 8 ≠ wordMoment 8 := by
  rw [codeMoment_eq]
  simp [wordMoment, Finset.sum_range_succ, Nat.choose]

/-- The 15-digit read quantum `Y` of `glm_universal.reasoning.coherence`. -/
def Yq : ℚ := 264675430404527 / 10 ^ 15

/-- The shell-0 NRCI of a `0/1` carrier of weight `w`: `10 / (10 + w (Y + 1/8))`. -/
def nrciW (w : ℕ) : ℚ := 10 / (10 + w * (Yq + 1 / 8))

/-- The NRCI averaged over the code and over all words are *not* equal (they
differ by about `2.3 × 10⁻⁸`): the agreement to the six decimals the review
quotes comes from the moment agreement above, not from an identity. -/
theorem nrci_means_differ :
    (nrciW 0 + 759 * nrciW 8 + 2576 * nrciW 12 + 759 * nrciW 16 + nrciW 24) / 4096 ≠
      (∑ w ∈ range 25, (Nat.choose 24 w : ℚ) * nrciW w) / 2 ^ 24 := by
  simp only [Finset.sum_range_succ, Finset.sum_range_zero, nrciW, Yq]
  norm_num [Nat.choose]

/-- The lowest NRCI any `0/1` carrier can have is that of the all-ones word,
`nrciW 24 > 1/2`: the register's claimed noise floor `0.42` is unreachable. -/
theorem nrci_floor {w : ℕ} (hw : w ≤ 24) : nrciW 24 ≤ nrciW w ∧ (1 / 2 : ℚ) < nrciW 24 := by
  have hq : (0 : ℚ) < Yq + 1 / 8 := by norm_num [Yq]
  have hw' : (w : ℚ) ≤ 24 := by exact_mod_cast hw
  constructor
  · unfold nrciW
    apply div_le_div_of_nonneg_left (by norm_num) (by positivity)
    push_cast
    nlinarith
  · norm_num [nrciW, Yq]

end GLM.LawRegister
