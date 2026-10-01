/-
# The weight enumerator of the substrate's Golay code

`Golay/Code.lean` defines the code as the kernel of the syndrome map `syn`, and
`Golay/Sextet.lean` proves the facts that the covering radius needs — minimum
weight 8, the six-fold tie, the sextet partition. What neither file supplies is
the *census of the code itself*: how many codewords there are of each weight.

This file supplies it, by giving the kernel its generator-side description and
counting there:

* `encode` — the systematic encoder `m ↦ (m ∣ mB)` for the parity block `Bmat`
  of `Golay/Code.lean`;
* `encode_isCodeword`, `encode_injective`, `exists_encode` — the encoder lands
  in the kernel, is injective, and *every* codeword is encoded, so `encode` is
  a bijection from the 4,096 messages onto the code;
* `card_codewords` — the code has exactly 4,096 words;
* `golay_weight_enumerator` — `1 + 759·x⁸ + 2576·x¹² + 759·x¹⁶ + x²⁴`;
* `golay_doubly_even` — every codeword weight is divisible by 4;
* `golay_weight_mem` — every codeword weight lies in `{0, 8, 12, 16, 24}`.

The counting steps are `native_decide` over the 4,096 messages, which is the
raw computation directive D2 asks for rather than a sampled shortcut; the
structural steps are ordinary proofs.

The last section is the bridge the light chain needs
(`Calibration.lean` §7): among nonzero codewords the substrate's symmetry tax
`GLM.tax` is minimised exactly by the weight-8 words — the octads — with value
`8Y + 1 = 3.117…`, whose integer part is the `3` of "24 bits + 3 TAX".
-/
import Mathlib
import RequestProject.GLM.Golay.Code
import RequestProject.GLM.Golay.Sextet
import RequestProject.GLM.Calibration

namespace GLM.Golay24

open Finset

/-! ## 1. The systematic encoder -/

/-- The bit of the encoded word at coordinate `k`: the message bit itself on the
twelve information positions, and the parity `∑ᵢ mᵢ Bᵢⱼ` on position `12 + j`. -/
def encBit (m : Fin 12 → ZMod 2) (k : Fin 24) : ZMod 2 :=
  if h : (k : ℕ) < 12 then m ⟨(k : ℕ), h⟩
  else ∑ i : Fin 12, m i * Bmat i ⟨(k : ℕ) - 12, by have := k.isLt; omega⟩

/-- The systematic encoding of a message, held as its support. -/
def encode (m : Fin 12 → ZMod 2) : Word := univ.filter (fun k => encBit m k = 1)

theorem mem_encode {m : Fin 12 → ZMod 2} {k : Fin 24} :
    k ∈ encode m ↔ encBit m k = 1 := by
  simp [encode]

/-- Every encoded message is a codeword. This is where the symmetry of `Bmat`
does its work: the information half of the syndrome is `∑ₖ mₖ Bᵢₖ` and the
parity half is `∑ₖ mₖ Bₖᵢ`, and over `ZMod 2` the two cancel. -/
theorem encode_isCodeword (m : Fin 12 → ZMod 2) : IsCodeword (encode m) := by
  revert m; unfold IsCodeword; native_decide

/-! ## 2. The encoder is a bijection onto the code -/

/-- The message read back off the twelve information positions of a word. -/
def decode (c : Word) : Fin 12 → ZMod 2 :=
  fun i => if (⟨(i : ℕ), by have := i.isLt; omega⟩ : Fin 24) ∈ c then 1 else 0

theorem decode_encode (m : Fin 12 → ZMod 2) : decode (encode m) = m := by
  funext i
  have hlt : ((⟨(i : ℕ), by have := i.isLt; omega⟩ : Fin 24) : ℕ) < 12 := i.isLt
  have hbit : encBit m ⟨(i : ℕ), by have := i.isLt; omega⟩ = m i := by
    simp [encBit, hlt]
  by_cases h : m i = 1
  · simp [decode, mem_encode, hbit, h]
  · have h0 : m i = 0 := by
      revert h; generalize m i = x; revert x; decide
    simp [decode, mem_encode, hbit, h0]

theorem encode_injective : Function.Injective encode := by
  intro m m' h
  rw [← decode_encode m, ← decode_encode m', h]

/-- A codeword supported entirely in the twelve parity positions is empty: on
those positions the parity-check matrix is the identity, so the syndrome *is*
the word. -/
theorem eq_empty_of_parity_support {d : Word}
    (hsupp : ∀ k ∈ d, ¬ ((k : ℕ) < 12)) (hd : IsCodeword d) : d = ∅ := by
  by_contra hne
  obtain ⟨k, hk⟩ := Finset.nonempty_iff_ne_empty.2 hne
  have hk12 : ¬ ((k : ℕ) < 12) := hsupp k hk
  have hklt := k.isLt
  obtain ⟨i, hik⟩ : ∃ i : Fin 12, (i : ℕ) + 12 = (k : ℕ) :=
    ⟨⟨(k : ℕ) - 12, by omega⟩, by simp; omega⟩
  have hcol : ∀ j ∈ d, col j i = if j = k then 1 else 0 := by
    intro j hj
    have hj12 : ¬ ((j : ℕ) < 12) := hsupp j hj
    simp only [col, dif_neg hj12, hik]
    by_cases hjk : j = k
    · subst hjk; simp
    · have hv : (j : ℕ) ≠ (k : ℕ) := fun h => hjk (Fin.ext h)
      simp [hv, hjk]
  have hsyn : syn d i = 1 := by
    have : syn d i = ∑ j ∈ d, col j i := by simp [syn]
    rw [this, Finset.sum_congr rfl hcol, Finset.sum_ite_eq' d k (fun _ => (1 : ZMod 2))]
    simp [hk]
  rw [hd] at hsyn
  simp at hsyn

/-- **Every codeword is encoded.** -/
theorem exists_encode {c : Word} (hc : IsCodeword c) : ∃ m, encode m = c := by
  refine ⟨decode c, ?_⟩
  set d : Word := symmDiff (encode (decode c)) c with hdef
  have hdcode : IsCodeword d := by
    have := syn_symmDiff (encode (decode c)) c
    unfold IsCodeword at *
    rw [hdef, this, encode_isCodeword, hc, add_zero]
  have hsupp : ∀ k ∈ d, ¬ ((k : ℕ) < 12) := by
    intro k hk hk12
    have hmem : k ∈ symmDiff (encode (decode c)) c := hk
    rw [Finset.mem_symmDiff] at hmem
    have hbit : encBit (decode c) k = (if k ∈ c then 1 else 0) := by
      have : k = (⟨((⟨(k : ℕ), hk12⟩ : Fin 12) : ℕ), by omega⟩ : Fin 24) := by
        apply Fin.ext; simp
      simp [encBit, hk12, decode]
    have hk' : k ∈ encode (decode c) ↔ k ∈ c := by
      rw [mem_encode, hbit]
      by_cases h : k ∈ c <;> simp [h]
    rcases hmem with ⟨h1, h2⟩ | ⟨h1, h2⟩
    · exact h2 (hk'.1 h1)
    · exact h2 (hk'.2 h1)
  have hempty : d = ∅ := eq_empty_of_parity_support hsupp hdcode
  have := symmDiff_eq_bot.1 (by simpa [hdef] using hempty)
  exact this

/-- The code, as a finite set of words. -/
def codewords : Finset Word := univ.filter (fun c : Word => IsCodeword c)

theorem mem_codewords {c : Word} : c ∈ codewords ↔ IsCodeword c := by
  simp [codewords]

/-- `encode` is a bijection from the message space onto the code, so the code
has `2¹² = 4096` words. -/
theorem card_codewords : codewords.card = 4096 := by
  have himg : (univ : Finset (Fin 12 → ZMod 2)).image encode = codewords := by
    ext c
    simp only [Finset.mem_image, Finset.mem_univ, true_and, mem_codewords]
    constructor
    · rintro ⟨m, rfl⟩; exact encode_isCodeword m
    · intro hc; exact exists_encode hc
  rw [← himg, Finset.card_image_of_injective _ encode_injective]
  simp

/-- **The code is closed under symmetric difference**, which is its `F₂`
linearity written in the `Finset` model: the syndrome is additive
(`syn_symmDiff`), so two zero syndromes give a third. Every closure argument
in `Combiner.lean` and `Steiner.lean` reduces to this one. -/
theorem isCodeword_symmDiff {a b : Word} (ha : IsCodeword a) (hb : IsCodeword b) :
    IsCodeword (symmDiff a b) := by
  unfold IsCodeword at *
  rw [syn_symmDiff, ha, hb, add_zero]

/-! ## 3. The census, computed over the 4,096 messages -/

/-- Every codeword weight lies in `{0, 8, 12, 16, 24}`. -/
theorem encode_wt_mem (m : Fin 12 → ZMod 2) :
    wt (encode m) = 0 ∨ wt (encode m) = 8 ∨ wt (encode m) = 12 ∨
      wt (encode m) = 16 ∨ wt (encode m) = 24 := by
  revert m; unfold wt; native_decide

theorem golay_weight_mem {c : Word} (hc : IsCodeword c) :
    wt c = 0 ∨ wt c = 8 ∨ wt c = 12 ∨ wt c = 16 ∨ wt c = 24 := by
  obtain ⟨m, rfl⟩ := exists_encode hc
  exact encode_wt_mem m

/-- **The code is doubly even.** -/
theorem golay_doubly_even {c : Word} (hc : IsCodeword c) : 4 ∣ wt c := by
  rcases golay_weight_mem hc with h | h | h | h | h <;> rw [h] <;> decide

/-! The five counts, computed over the 4,096 messages. -/

private theorem card_msgs_wt0 :
    #((univ : Finset (Fin 12 → ZMod 2)).filter (fun m => wt (encode m) = 0)) = 1 := by
  unfold wt; native_decide

private theorem card_msgs_wt8 :
    #((univ : Finset (Fin 12 → ZMod 2)).filter (fun m => wt (encode m) = 8)) = 759 := by
  unfold wt; native_decide

private theorem card_msgs_wt12 :
    #((univ : Finset (Fin 12 → ZMod 2)).filter (fun m => wt (encode m) = 12)) = 2576 := by
  unfold wt; native_decide

private theorem card_msgs_wt16 :
    #((univ : Finset (Fin 12 → ZMod 2)).filter (fun m => wt (encode m) = 16)) = 759 := by
  unfold wt; native_decide

private theorem card_msgs_wt24 :
    #((univ : Finset (Fin 12 → ZMod 2)).filter (fun m => wt (encode m) = 24)) = 1 := by
  unfold wt; native_decide

/-- Transfer of a count from the messages to the code. -/
private theorem card_codewords_wt_eq (w : ℕ) :
    #(codewords.filter (fun c => wt c = w)) =
      #((univ : Finset (Fin 12 → ZMod 2)).filter (fun m => wt (encode m) = w)) := by
  have himg : (univ : Finset (Fin 12 → ZMod 2)).image encode = codewords := by
    ext c
    simp only [Finset.mem_image, Finset.mem_univ, true_and, mem_codewords]
    exact ⟨by rintro ⟨m, rfl⟩; exact encode_isCodeword m, fun hc => exists_encode hc⟩
  rw [← himg, Finset.filter_image,
    Finset.card_image_of_injective _ encode_injective]

/-- **The weight enumerator of the Golay code**:
`1 + 759 x⁸ + 2576 x¹² + 759 x¹⁶ + x²⁴`. -/
theorem golay_weight_enumerator :
    #(codewords.filter (fun c => wt c = 0)) = 1 ∧
    #(codewords.filter (fun c => wt c = 8)) = 759 ∧
    #(codewords.filter (fun c => wt c = 12)) = 2576 ∧
    #(codewords.filter (fun c => wt c = 16)) = 759 ∧
    #(codewords.filter (fun c => wt c = 24)) = 1 := by
  refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> rw [card_codewords_wt_eq]
  · exact card_msgs_wt0
  · exact card_msgs_wt8
  · exact card_msgs_wt12
  · exact card_msgs_wt16
  · exact card_msgs_wt24

/-- The census sums back to the whole code: `1 + 759 + 2576 + 759 + 1 = 4096`. -/
theorem golay_weight_enumerator_total :
    1 + 759 + 2576 + 759 + 1 = codewords.card := by
  rw [card_codewords]

/-! ## 4. The octads minimise the symmetry tax

This is the bridge to `Calibration.lean`: the tick budget "24 bits + 3 TAX" of
the light chain takes its `3` from the cheapest nonzero state of the code. -/

/-- The `0/1` carrier of a word: its indicator vector. -/
def indicator (c : Word) : Fin 24 → ℤ := fun i => if i ∈ c then 1 else 0

theorem hammingWeight_indicator (c : Word) : GLM.hammingWeight (indicator c) = wt c := by
  classical
  simp only [GLM.hammingWeight, indicator, wt]
  congr 1
  ext i
  by_cases h : i ∈ c <;> simp [h]

/-- The substrate tax of a codeword is `GLM.Calibration.codewordTax` of its
weight — the light chain's cost function is this repository's own. -/
theorem tax_indicator_eq (c : Word) :
    GLM.tax (indicator c) = GLM.Calibration.codewordTax (wt c) := by
  rw [GLM.Calibration.tax_indicator (indicator c) (fun i => by
        by_cases h : i ∈ c <;> simp [indicator, h]),
    hammingWeight_indicator]

/-- **The octads minimise the symmetry tax among nonzero codewords.** This is
the precise — and true — form of the "photon = minimum-TAX octad" claim: it
holds on the *code* layer. -/
theorem octad_min_tax {c : Word} (hc : IsCodeword c) (hne : c ≠ ∅) :
    GLM.Calibration.codewordTax 8 ≤ GLM.tax (indicator c) := by
  rw [tax_indicator_eq]
  have h8 : 8 ≤ wt c := golay_min_weight hc hne
  rcases eq_or_lt_of_le h8 with h | h
  · rw [← h]
  · exact le_of_lt (GLM.Calibration.codewordTax_strictMono h)

/-- Equality holds only for the octads. -/
theorem octad_min_tax_strict {c : Word} (hc : IsCodeword c) (hne : c ≠ ∅) (h8 : wt c ≠ 8) :
    GLM.Calibration.codewordTax 8 < GLM.tax (indicator c) := by
  rw [tax_indicator_eq]
  have h : 8 ≤ wt c := golay_min_weight hc hne
  exact GLM.Calibration.codewordTax_strictMono (lt_of_le_of_ne h (Ne.symm h8))

/-- An octad exists, so the minimum is attained: the count is 759. -/
theorem exists_octad : ∃ c : Word, IsCodeword c ∧ wt c = 8 := by
  have h : #(codewords.filter (fun c => wt c = 8)) = 759 := golay_weight_enumerator.2.1
  have hpos : 0 < #(codewords.filter (fun c => wt c = 8)) := by rw [h]; norm_num
  obtain ⟨c, hc⟩ := Finset.card_pos.1 hpos
  rw [Finset.mem_filter, mem_codewords] at hc
  exact ⟨c, hc.1, hc.2⟩

end GLM.Golay24
