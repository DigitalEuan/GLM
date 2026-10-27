import RequestProject.GLM.Rule30.ShortcutNetworkData

/-!
# Round 43: complete syndrome decoding of the GLM's Golay substrate — where the ties are

§5 of `GLM_Escalation_Boundaries_Exploration.md` proposes complete syndrome decoding as the way
the snap resolves ambiguity "at the deep-hole boundary". The GLM already ships a complete decoder
for its 24-bit substrate (the extended binary Golay code of the lattice-shortcut layer,
`golayWord`). This file certifies, on that exact code, where nearest-codeword decoding is
ambiguous, so that the exploration's claim can be stated correctly at the substrate layer.

Write `countAt x w` for the number of codewords at Hamming distance exactly `w` from the 24-bit
word `x`.

* `golay_decoding_dichotomy` : **for every 24-bit word `x`, exactly one of two things holds.**
  Either exactly one codeword lies within distance 3 of `x` (it is then the unique nearest
  codeword), or no codeword lies within distance 3 and **exactly six** lie at distance 4.
  So the covering radius is 4, and the only ambiguity is a six-way tie at distance 4.
* `golay_coset_census` : of the 4096 cosets (syndromes), `1, 24, 276, 2024, 1771` have
  distance `0, 1, 2, 3, 4` to the code; the tie happens on exactly the 1771 weight-4 cosets.
* `golay_heavy_error_never_decoded` : if the error has weight at least 5, the transmitted
  codeword is never a nearest codeword: some codeword is strictly closer.

What this says about the exploration's §5. A complete decoder with a *fixed* table does not
remove the six-way tie — it hides it (that is exactly the order-dependent "snap" defect the GLM's
own `golay_decode` module retired by returning all six leaders and the status `ambiguous`).
The ambiguity set is not the 23 deep-hole types: at the substrate it is the set of words at the
covering radius, `1771 · 2^12` of the `2^24` words, and its structure (six leaders) is a property
of the code, not of a residue filter.

Trust: the three finite facts are `native_decide` certificates; the reduction from all `2^24`
words to the 4096 coset representatives is proved.
-/

namespace GLM.Escalation.Golay

open GLM.Rule30

/-- Number of codewords at Hamming distance exactly `w` from `x`. -/
def countAt (x w : ℕ) : ℕ :=
  ((Finset.range 4096).filter (fun m => pop24 (x ^^^ golayWord m) = w)).card

/-- Codewords are 24-bit words whose low 12 bits are the message. -/
theorem golayWord_bounds : ∀ m < 4096, golayWord m < 2 ^ 24 ∧ golayWord m % 4096 = m := by
  native_decide

/-- **Reduction to coset representatives.** The distance profile of `x` equals that of
`x ^^^ golayWord (x % 4096)`, a word with zero low 12 bits. -/
theorem countAt_reduce (x w : ℕ) :
    countAt x w = countAt (x ^^^ golayWord (x % 4096)) w := by
  set a := x % 4096 with ha
  have ha' : a < 2 ^ 12 := Nat.mod_lt _ (by norm_num)
  unfold countAt
  apply Finset.card_nbij' (fun m => m ^^^ a) (fun m => m ^^^ a)
  · intro m hm
    simp only [Finset.coe_filter, Finset.mem_range, Set.mem_setOf_eq] at hm ⊢
    refine ⟨Nat.xor_lt_two_pow (n := 12) hm.1 ha', ?_⟩
    rw [← hm.2, golayWord_xor]
    have : x ^^^ (golayWord m ^^^ golayWord a ^^^ golayWord a) = x ^^^ golayWord m := by
      rw [Nat.xor_assoc (golayWord m), Nat.xor_self, Nat.xor_zero]
    rw [← this]
    ac_rfl
  · intro m hm
    simp only [Finset.coe_filter, Finset.mem_range, Set.mem_setOf_eq] at hm ⊢
    refine ⟨Nat.xor_lt_two_pow (n := 12) hm.1 ha', ?_⟩
    rw [← hm.2, golayWord_xor]
    ac_rfl
  · intro m _; simp
  · intro m _; simp

/-- The profile of a coset representative `s · 4096`, all distances at once. -/
def repProfile (s : ℕ) : List ℕ :=
  (List.range 4096).map (fun m => pop24 ((s * 4096) ^^^ golayWord m))

/-- The finite check on the 4096 representatives, in list form. -/
def repOK (s : ℕ) : Bool :=
  let p := repProfile s
  (p.count 0 + p.count 1 + p.count 2 + p.count 3 == 1) ||
    (p.count 0 + p.count 1 + p.count 2 + p.count 3 == 0 && p.count 4 == 6)

theorem repOK_all : ∀ s < 4096, repOK s = true := by native_decide

theorem countAt_eq_count (x w : ℕ) :
    countAt x w = ((List.range 4096).map (fun m => pop24 (x ^^^ golayWord m))).count w := by
  unfold countAt
  rw [List.count_eq_length_filter, List.filter_map, List.length_map, Finset.card_def,
    Finset.filter_val, Finset.range_val, Multiset.range, Multiset.filter_coe, Multiset.coe_card]
  congr 1

/-- **The decoding dichotomy for every 24-bit word.** -/
theorem golay_decoding_dichotomy (x : ℕ) (hx : x < 2 ^ 24) :
    countAt x 0 + countAt x 1 + countAt x 2 + countAt x 3 = 1 ∨
    (countAt x 0 + countAt x 1 + countAt x 2 + countAt x 3 = 0 ∧ countAt x 4 = 6) := by
  set r := x ^^^ golayWord (x % 4096) with hr
  have hg := golayWord_bounds (x % 4096) (Nat.mod_lt _ (by norm_num))
  have hr24 : r < 2 ^ 24 := Nat.xor_lt_two_pow hx hg.1
  have hr0 : r % 4096 = 0 := by
    have := Nat.xor_mod_two_pow (a := x) (b := golayWord (x % 4096)) (n := 12)
    norm_num at this
    rw [hr, this, hg.2, Nat.xor_self]
  have hrs : r = (r / 4096) * 4096 := (Nat.div_mul_cancel (Nat.dvd_of_mod_eq_zero hr0)).symm
  have hs : r / 4096 < 4096 := by omega
  have hok := repOK_all _ hs
  simp only [repOK, repProfile, Bool.or_eq_true, Bool.and_eq_true, beq_iff_eq] at hok
  simp only [countAt_reduce x, ← hr, countAt_eq_count]
  rw [hrs]
  exact hok

/-- Distance from the representative `s · 4096` to the code (24 if the profile were empty). -/
def repDist (s : ℕ) : ℕ := (repProfile s).foldl min 24

/-- **Coset census.** Of the 4096 cosets, `1, 24, 276, 2024, 1771` lie at distance
`0, 1, 2, 3, 4` from the code, and none further. -/
theorem golay_coset_census :
    (List.range 6).map (fun w => ((List.range 4096).filter (fun s => repDist s = w)).length) =
      [1, 24, 276, 2024, 1771, 0] := by
  native_decide

theorem exists_of_countAt_pos {x w : ℕ} (h : 0 < countAt x w) :
    ∃ m < 4096, pop24 (x ^^^ golayWord m) = w := by
  obtain ⟨m, hm⟩ := Finset.card_pos.1 h
  simp only [Finset.mem_filter, Finset.mem_range] at hm
  exact ⟨m, hm.1, hm.2⟩

/-- Every 24-bit word is within distance 4 of the code (covering radius 4). -/
theorem golay_covering_radius (x : ℕ) (hx : x < 2 ^ 24) :
    ∃ m < 4096, pop24 (x ^^^ golayWord m) ≤ 4 := by
  rcases golay_decoding_dichotomy x hx with h | ⟨_, h⟩
  · have : 0 < countAt x 0 ∨ 0 < countAt x 1 ∨ 0 < countAt x 2 ∨ 0 < countAt x 3 := by omega
    rcases this with h | h | h | h <;>
      · obtain ⟨m, hm, hd⟩ := exists_of_countAt_pos h
        exact ⟨m, hm, by omega⟩
  · obtain ⟨m, hm, hd⟩ := exists_of_countAt_pos (show 0 < countAt x 4 by omega)
    exact ⟨m, hm, by omega⟩

/-- **Errors of weight at least 5 are never decoded correctly.** If codeword `golayWord m₀` is
sent and an error `e` of weight at least 5 is added, some codeword is strictly closer to the
received word than the one sent — so every nearest-codeword decoder, with any tie rule, fails. -/
theorem golay_heavy_error_never_decoded (m₀ e : ℕ) (hm₀ : m₀ < 4096) (he : e < 2 ^ 24)
    (hw : 5 ≤ pop24 e) :
    ∃ m < 4096, pop24 ((golayWord m₀ ^^^ e) ^^^ golayWord m) <
      pop24 ((golayWord m₀ ^^^ e) ^^^ golayWord m₀) := by
  have hy : golayWord m₀ ^^^ e < 2 ^ 24 := Nat.xor_lt_two_pow (golayWord_bounds m₀ hm₀).1 he
  obtain ⟨m, hm, hd⟩ := golay_covering_radius _ hy
  refine ⟨m, hm, ?_⟩
  have : golayWord m₀ ^^^ e ^^^ golayWord m₀ = e := by
    rw [Nat.xor_comm (golayWord m₀) e, Nat.xor_assoc, Nat.xor_self, Nat.xor_zero]
  rw [this]
  omega

end GLM.Escalation.Golay
