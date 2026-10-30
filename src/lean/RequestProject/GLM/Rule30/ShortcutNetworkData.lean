import RequestProject.GLM.Rule30.Compute

/-!
# Round 14: finite facts about the shortcut network and about jump rules

**The GLM's Golay/Leech network.**  The twelve generator rows below are those of the GLM's
lattice-shortcut layer (`G = [I₁₂ | B]`, 24-bit masks).  The network's points are the 4096
codewords `golayWord m`; a hop between two points is again a codeword (`golayWord_xor`), and
its weight is the hop's squared jump norm `d²` (twice a codeword is a Leech vector).

* `golay_weight_census` : the hop norms are `0, 8, 12, 16, 24` with multiplicities
  `1, 759, 2576, 759, 1`.
* `golay_octad_distance` : measured in minimal (kissing, `d² = 8`) hops, every point is within
  **3** hops of every other: a `d² = 12` or `16` hop is exactly 2 minimal hops, the `d² = 24` hop
  exactly 3.  So *every* walk on this network "jumps all over the place": there is nowhere far
  away to go.
* `hop_twice` : repeating a hop returns to the start — the network has no straight lines longer
  than one step, so "straight path versus shortcut" cannot be read off the network itself.

**Jump rules on the centre column (finite certificates).**

* `centerCol_no_linear_rule_128` : no linear jump rule with taps in `1..128` reproduces the
  centre column on times `128 … 256` (an infeasibility certificate of 67 equations).
* `centerCol_no_tap_rule` : no rule with 2 taps in `1..64`, 3 taps in `1..32` or 4 taps in
  `1..24`, whatever its Boolean function, reproduces the centre column on `J … J+63`.

These are statements about finite stretches only; by `problem1_iff_no_jumpRule` the open
question is whether some jump rule takes over on an infinite tail.
-/

namespace GLM.Rule30

/-! ## The Golay code of the GLM's lattice shortcut -/

/-- The generator rows `G = [I₁₂ | B]` of the GLM lattice-shortcut layer, as 24-bit masks. -/
def golayRows : List ℕ :=
  [16769025, 4681730, 10727428, 13750280, 6877200, 11825184,
   14299200, 15536256, 7770368, 3887616, 1946624, 9361408]

/-- XOR of the generator rows selected by the bits of `m`, starting from `acc`. -/
def golayFold (m : ℕ) (acc : ℕ) (js : List ℕ) : ℕ :=
  js.foldl (fun acc j => if m.testBit j then acc ^^^ golayRows.getD j 0 else acc) acc

/-- The codeword with message `m` (a point of the network). -/
def golayWord (m : ℕ) : ℕ := golayFold m 0 (List.range 12)

/-- Hamming weight of the low 24 bits (the squared jump norm `d²` of a hop). -/
def pop24 (x : ℕ) : ℕ := ((List.range 24).filter (fun i => x.testBit i)).length

theorem golayFold_xor (m m' : ℕ) (js : List ℕ) :
    ∀ acc acc', golayFold (m ^^^ m') (acc ^^^ acc') js = golayFold m acc js ^^^ golayFold m' acc' js := by
  induction js with
  | nil => intro acc acc'; rfl
  | cons j js ih =>
    intro acc acc'
    simp only [golayFold, List.foldl_cons] at ih ⊢
    rw [Nat.testBit_xor]
    set r := golayRows.getD j 0
    cases hm : m.testBit j <;> cases hm' : m'.testBit j <;> simp only [Bool.false_xor,
      Bool.xor_false, Bool.true_xor, Bool.not_true, if_true, if_false,
      Bool.false_eq_true]
    · exact ih _ _
    · rw [← ih]; congr 1; ac_rfl
    · rw [← ih]; congr 1; ac_rfl
    · rw [← ih]; congr 1
      rw [Nat.xor_assoc, Nat.xor_comm r, Nat.xor_assoc, Nat.xor_self, Nat.xor_zero]

/-- **The network is a group**: the hop between two points is itself a point. -/
theorem golayWord_xor (m m' : ℕ) : golayWord (m ^^^ m') = golayWord m ^^^ golayWord m' := by
  unfold golayWord
  rw [← golayFold_xor, Nat.xor_self]

/-- **Repeating a hop returns to the start**: there are no straight lines of length 2. -/
theorem hop_twice (x h : ℕ) : x ^^^ h ^^^ h = x := by
  rw [Nat.xor_assoc, Nat.xor_self, Nat.xor_zero]

/-- The 4096 points are distinct. -/
theorem golayWord_nodup : ((List.range 4096).map golayWord).Nodup := by native_decide

/-- **Hop norms of the network.** `d² = pop24` of a codeword takes the values `0, 8, 12, 16, 24`
with multiplicities `1, 759, 2576, 759, 1`, and no other value. -/
theorem golay_weight_census :
    (List.range 25).map (fun w => ((List.range 4096).filter (fun m => pop24 (golayWord m) = w)).length)
      = [1, 0, 0, 0, 0, 0, 0, 0, 759, 0, 0, 0, 2576, 0, 0, 0, 759, 0, 0, 0, 0, 0, 0, 0, 1] ∧
    ∀ m < 4096, pop24 (golayWord m) ≤ 24 := by
  native_decide

/-- The message is a minimal (kissing) hop: an octad, `d² = 8`. -/
def IsOctadMsg (m : ℕ) : Prop := pop24 (golayWord m) = 8

instance : DecidablePred IsOctadMsg := fun m => inferInstanceAs (Decidable (pop24 (golayWord m) = 8))

/-- The 759 octad messages. -/
def octadMsgs : List ℕ := (List.range 4096).filter (fun m => pop24 (golayWord m) = 8)

theorem mem_octadMsgs {o : ℕ} : o ∈ octadMsgs ↔ o < 4096 ∧ IsOctadMsg o := by
  simp [octadMsgs, IsOctadMsg]

/-- **Every point is within 3 minimal hops.** A hop of norm `8` is one octad; a hop of norm
`12` or `16` is not an octad but is the sum of two; the hop of norm `24` is the sum of three
octads and of no fewer. -/
theorem golay_octad_distance : ∀ m < 4096,
    (pop24 (golayWord m) = 8 → IsOctadMsg m) ∧
    ((pop24 (golayWord m) = 12 ∨ pop24 (golayWord m) = 16) →
      ¬ IsOctadMsg m ∧ ∃ o ∈ octadMsgs, IsOctadMsg (m ^^^ o)) ∧
    (pop24 (golayWord m) = 24 →
      ¬ IsOctadMsg m ∧ (∀ o ∈ octadMsgs, ¬ IsOctadMsg (m ^^^ o)) ∧
      ∃ o₁ ∈ octadMsgs, ∃ o₂ ∈ octadMsgs, IsOctadMsg (m ^^^ o₁ ^^^ o₂)) := by
  native_decide

/-! ## Jump-rule certificates for the centre column -/

/-- Bits as elements of `ZMod 2`. -/
def bitZ (b : Bool) : ZMod 2 := if b then 1 else 0

/-- The linear jump rule with coefficients `c 1, …, c L` reproduces `a` at every time in
`[s, n)`: `a t = ∑_{j=1}^{L} c j · a (t - j)` over `ZMod 2`. -/
def LinearRuleOn (a : ℕ → Bool) (L : ℕ) (c : ℕ → ZMod 2) (s n : ℕ) : Prop :=
  ∀ t ∈ Finset.Ico s n, bitZ (a t) = ∑ j ∈ Finset.Icc 1 L, c j * bitZ (a (t - j))

/-- **Soundness of an infeasibility certificate.** If a set `T` of the equations sums to
`0 = 1`, no linear rule exists. -/
theorem no_linearRule_of_certificate (a : ℕ → Bool) (L s n : ℕ) (T : Finset ℕ)
    (hT : T ⊆ Finset.Ico s n) (hrow : ∀ j ∈ Finset.Icc 1 L, ∑ t ∈ T, bitZ (a (t - j)) = 0)
    (hrhs : ∑ t ∈ T, bitZ (a t) = 1) (c : ℕ → ZMod 2) : ¬ LinearRuleOn a L c s n := by
  intro h
  have : ∑ t ∈ T, bitZ (a t) = 0 := by
    calc ∑ t ∈ T, bitZ (a t) = ∑ t ∈ T, ∑ j ∈ Finset.Icc 1 L, c j * bitZ (a (t - j)) :=
          Finset.sum_congr rfl (fun t ht => h t (hT ht))
      _ = ∑ j ∈ Finset.Icc 1 L, c j * ∑ t ∈ T, bitZ (a (t - j)) := by
          rw [Finset.sum_comm]; simp_rw [Finset.mul_sum]
      _ = 0 := Finset.sum_eq_zero (fun j hj => by rw [hrow j hj, mul_zero])
  rw [this] at hrhs
  exact zero_ne_one hrhs

/-- The 67 equations whose sum is `0 = 1` (found by Gaussian elimination, `r14_jump_rules.py`). -/
def linCertT : List ℕ :=
  [128, 129, 130, 131, 132, 134, 137, 139, 143, 144, 149, 151, 152, 153, 154, 156, 157, 158, 159,
   160, 162, 163, 164, 167, 169, 170, 171, 172, 173, 174, 180, 183, 185, 186, 189, 190, 193, 195,
   197, 200, 202, 207, 208, 211, 212, 214, 216, 217, 219, 221, 224, 225, 227, 230, 231, 232, 234,
   238, 239, 240, 241, 243, 244, 248, 254, 255, 256]

theorem centerCol_eq_fastCenter : centerCol = fastCenter := funext centerCol_eq_fast

/-- **No linear jump rule with taps in `1..128` reproduces the centre column on `128 … 256`**
(so the linear complexity of `c(0) … c(256)` exceeds 128; a rule of smaller order is the case of
coefficients vanishing beyond it). -/
theorem centerCol_no_linear_rule_128 (c : ℕ → ZMod 2) : ¬ LinearRuleOn centerCol 128 c 128 257 := by
  apply no_linearRule_of_certificate centerCol 128 128 257 linCertT.toFinset
  · intro t ht
    simp only [List.mem_toFinset] at ht
    simp only [Finset.mem_Ico]
    revert t; native_decide
  · rw [centerCol_eq_fastCenter]; native_decide
  · rw [centerCol_eq_fastCenter]; native_decide

/-- A rule with taps `taps` (any Boolean function `f` of the tapped bits) reproduces `a` at every
time in `[s, n)`. -/
def TapRuleOn (a : ℕ → Bool) (taps : List ℕ) (f : List Bool → Bool) (s n : ℕ) : Prop :=
  ∀ t ∈ Finset.Ico s n, a t = f (taps.map (fun j => a (t - j)))

/-- A conflict — two times with the same tapped bits and different values — refutes every rule
with those taps. -/
theorem no_tapRule_of_conflict (a : ℕ → Bool) (taps : List ℕ) (s n t₁ t₂ : ℕ)
    (h₁ : t₁ ∈ Finset.Ico s n) (h₂ : t₂ ∈ Finset.Ico s n)
    (hsame : taps.map (fun j => a (t₁ - j)) = taps.map (fun j => a (t₂ - j)))
    (hdiff : a t₁ ≠ a t₂) (f : List Bool → Bool) : ¬ TapRuleOn a taps f s n := by
  intro h
  exact hdiff (by rw [h t₁ h₁, h t₂ h₂, hsame])

/-- The first 128 bits of the centre column, computed once. -/
def centerBits : Array Bool := (Array.range 128).map fastCenter

theorem centerBits_getD {t : ℕ} (ht : t < 128) : centerBits.getD t false = centerCol t := by
  rw [centerCol_eq_fastCenter]
  simp [centerBits, Array.getD, ht]

/-- Decision procedure: every tap set in `sets` has a conflict on `[s, n)` in the stored bits. -/
def allConflict (sets : List (List ℕ)) (s n : ℕ) : Bool :=
  let a := fun t => centerBits.getD t false
  sets.all fun taps => (List.range' s (n - s)).any fun t₁ => (List.range' s (n - s)).any fun t₂ =>
    taps.map (fun j => a (t₁ - j)) == taps.map (fun j => a (t₂ - j)) && a t₁ != a t₂

theorem no_tapRule_of_allConflict {sets : List (List ℕ)} {s n : ℕ} (hn : n ≤ 128)
    (h : allConflict sets s n = true) :
    ∀ taps ∈ sets, ∀ f, ¬ TapRuleOn centerCol taps f s n := by
  intro taps htaps f
  simp only [allConflict, List.all_eq_true, List.any_eq_true, Bool.and_eq_true, beq_iff_eq,
    bne_iff_ne, ne_eq, List.mem_range'_1] at h
  obtain ⟨t₁, ht₁, t₂, ht₂, hsame, hdiff⟩ := h taps htaps
  have e : ∀ t, t < 128 → centerBits.getD t false = centerCol t := fun t ht => centerBits_getD ht
  apply no_tapRule_of_conflict centerCol taps s n t₁ t₂
    (Finset.mem_Ico.2 ⟨ht₁.1, by omega⟩) (Finset.mem_Ico.2 ⟨ht₂.1, by omega⟩)
  · rw [List.map_inj_left] at hsame ⊢
    intro j hj
    rw [← e _ (by omega), ← e _ (by omega)]
    exact hsame j hj
  · rwa [← e _ (by omega), ← e _ (by omega)]

/-- **No short jump rule reproduces even 64 consecutive bits of the centre column.** For every
choice of 2 taps in `1..64`, 3 taps in `1..32` or 4 taps in `1..24` (`sublistsLen` lists the
increasing tap sets), and every Boolean function `f` of the tapped bits, the rule fails somewhere
on the times `J … J+63`. -/
theorem centerCol_no_tap_rule :
    (∀ taps ∈ (List.range' 1 64).sublistsLen 2, ∀ f, ¬ TapRuleOn centerCol taps f 64 128) ∧
    (∀ taps ∈ (List.range' 1 32).sublistsLen 3, ∀ f, ¬ TapRuleOn centerCol taps f 32 96) ∧
    (∀ taps ∈ (List.range' 1 24).sublistsLen 4, ∀ f, ¬ TapRuleOn centerCol taps f 24 88) :=
  ⟨no_tapRule_of_allConflict (by norm_num) (by native_decide),
   no_tapRule_of_allConflict (by norm_num) (by native_decide),
   no_tapRule_of_allConflict (by norm_num) (by native_decide)⟩

end GLM.Rule30
