module

public import RequestProject.GLM.Rule30.PrefixSearch

/-!
# Round 26: what the conjecture loop proposed for the half-line machine

Two outcomes of the Round 26 loop on the half-line machine of Rounds 21–22, plus one reduction
for To Do item 2.

## 1. The post-edge counting statement: window form refuted, amortised form proposed

`aliveCodes bd d k` — the codes of length exactly `d` (top bit `d − 1` set, i.e. the cells of a
left-white half-line with its edge at distance `d`) that pass every check before time `k`.
Round 22 proved that the checks before the edge halve the survivors exactly (`survivors_card`).
To Do items 1/10 suggested the natural continuation:

* **`WindowHalving p m num den`** — "after the edge, every window of `m` steps keeps at most a
  fraction `num/den < 1` of the codes alive".  The loop **refutes** it for every window it tests:
  survivors can sit on a plateau (`not_windowHalving_of_plateau`; certified witnesses in
  `ConjectureLoopData.lean`).  A lone survivor cannot be "halved".
* **`AmortizedHalving p c e`** — the repaired, *amortised* form proposed by the loop: after `m`
  steps past the edge, at most `2^(d − 1 + e) / 2^⌊m / c⌋` codes are alive (one halving every `c`
  steps *on average*, with slack `2^e`).  Plateaus are allowed.
* **`halfLineLinear_of_amortized`** — `AmortizedHalving p c e → HalfLineLinear p (c + 1) (c·e)`,
  hence **`halfLineDies_of_amortized`**: it implies the one-sided target `HalfLineDies p` and so
  the period-`p` rung of Problem 1.
* `amortizedHalvingUpTo_of_check` — a finite check certifies it for `d ≤ D` and **all** `m`
  (once the bound forces zero survivors, they stay zero: `aliveCodes_antitone`).

## 2. Drive symmetry: one drive word per rotation class (To Do item 2)

* `WordDies bd` — every non-empty half-line driven by `bd` eventually fails a check.
* **`wordDies_of_shift`** — if the machine dies for the drive started `s` steps late, it dies for
  the original drive.  **`wordDies_shift_iff_of_periodic`** — for a periodic drive, all rotations
  are equivalent.
* **`halfLineDies_two_iff`** — `HalfLineDies 2` is equivalent to the single word `10`
  (`driveN 2 1`); **`halfLineDies_three_iff`** — `HalfLineDies 3` is equivalent to the two
  words `100` and `110`.  (The constant word is the proved period-1 case.)

All results use only the standard axioms.
-/

@[expose] public section

namespace GLM.Rule30

/-! ## Alive codes of exact length `d` -/

/-- The codes of length exactly `d` that pass every check before time `k`. -/
def aliveCodes (bd : ℕ → Bool) (d k : ℕ) : Finset ℕ :=
  (Finset.Ico (2 ^ (d - 1)) (2 ^ d)).filter fun S => dDiesBy bd S k = false

theorem mem_aliveCodes {bd : ℕ → Bool} {d k S : ℕ} :
    S ∈ aliveCodes bd d k ↔ (2 ^ (d - 1) ≤ S ∧ S < 2 ^ d) ∧ dDiesBy bd S k = false := by
  simp [aliveCodes]

/-- Survivors only decrease with time. -/
theorem aliveCodes_antitone (bd : ℕ → Bool) (d : ℕ) {k k' : ℕ} (h : k ≤ k') :
    aliveCodes bd d k' ⊆ aliveCodes bd d k := by
  intro S hS
  rw [mem_aliveCodes] at *
  refine ⟨hS.1, ?_⟩
  by_contra hne
  have := dDiesBy_mono (Bool.eq_true_of_not_eq_false hne) h
  rw [hS.2] at this
  exact Bool.noConfusion this

/-! ## The window form (refuted) and the amortised form (proposed) -/

/-- **Window halving** (the To Do 1/10 suggestion, refuted by the loop): after the edge, every
window of `m` steps keeps at most the fraction `num / den` of the alive codes. -/
def WindowHalving (p m num den : ℕ) : Prop :=
  ∀ k, 0 < k → k < 2 ^ p → ∀ d t, 1 ≤ d → d - 1 ≤ t →
    den * (aliveCodes (driveN p k) d (t + m)).card ≤ num * (aliveCodes (driveN p k) d t).card

/-- **A plateau refutes window halving.** If, for some drive word and length, the number of alive
codes is positive and unchanged over a window of `m` steps after the edge, no fraction `< 1`
works for that window. -/
theorem not_windowHalving_of_plateau {p m num den k d t : ℕ} (hnd : num < den)
    (hk0 : 0 < k) (hk : k < 2 ^ p) (hd : 1 ≤ d) (ht : d - 1 ≤ t)
    (hpos : 0 < (aliveCodes (driveN p k) d t).card)
    (heq : (aliveCodes (driveN p k) d (t + m)).card = (aliveCodes (driveN p k) d t).card) :
    ¬ WindowHalving p m num den := by
  intro h
  have := h k hk0 hk d t hd ht
  rw [heq] at this
  have : num * (aliveCodes (driveN p k) d t).card < den * (aliveCodes (driveN p k) d t).card :=
    Nat.mul_lt_mul_of_pos_right hnd hpos
  omega

/-- **Amortised halving** (proposed by the loop): `m` steps after the edge, at most
`2^(d − 1 + e) / 2^⌊m / c⌋` codes of length `d` are alive, for every non-zero drive word of
period `p`. -/
def AmortizedHalving (p c e : ℕ) : Prop :=
  ∀ k, 0 < k → k < 2 ^ p → ∀ d m, 1 ≤ d →
    (aliveCodes (driveN p k) d (d - 1 + m)).card * 2 ^ (m / c) ≤ 2 ^ (d - 1 + e)

/-- Amortised halving forces every code to die by time `d − 1 + c·(d + e)`. -/
theorem dDiesBy_of_amortized {p c e : ℕ} (hc : 0 < c) (h : AmortizedHalving p c e) {k : ℕ}
    (hk0 : 0 < k) (hk : k < 2 ^ p) {d S : ℕ} (hd : 1 ≤ d) (hS1 : 2 ^ (d - 1) ≤ S)
    (hS2 : S < 2 ^ d) : dDiesBy (driveN p k) S (d - 1 + c * (d + e)) = true := by
  have h1 := h k hk0 hk d (c * (d + e)) hd
  rw [Nat.mul_div_cancel_left _ hc] at h1
  have hlt : 2 ^ (d - 1 + e) < 2 ^ (d + e) := Nat.pow_lt_pow_right (by norm_num) (by omega)
  have h0 : (aliveCodes (driveN p k) d (d - 1 + c * (d + e))).card = 0 := by
    by_contra hne
    have : 2 ^ (d + e) ≤ (aliveCodes (driveN p k) d (d - 1 + c * (d + e))).card * 2 ^ (d + e) :=
      Nat.le_mul_of_pos_left _ (Nat.pos_of_ne_zero hne)
    omega
  rw [Finset.card_eq_zero] at h0
  by_contra hne
  have : S ∈ aliveCodes (driveN p k) d (d - 1 + c * (d + e)) :=
    mem_aliveCodes.2 ⟨⟨hS1, hS2⟩, Bool.eq_false_iff.2 hne⟩
  rw [h0] at this
  exact Finset.notMem_empty _ this

/-- **Amortised halving gives a linear run bound.** -/
theorem halfLineLinear_of_amortized {p c e : ℕ} (hc : 0 < c) (h : AmortizedHalving p c e) :
    HalfLineLinear p (c + 1) (c * e) := by
  intro k hk0 hk d S hd hS1 hS2
  apply dDiesBy_mono (dDiesBy_of_amortized hc h hk0 hk hd hS1 hS2)
  have : c * (d + e) = c * d + c * e := by ring
  have : (c + 1) * d = c * d + d := by ring
  omega

/-- **Amortised halving implies the one-sided target**, hence the period-`p` rung. -/
theorem halfLineDies_of_amortized {p c e : ℕ} (hc : 0 < c) (h : AmortizedHalving p c e) :
    HalfLineDies p :=
  halfLineDies_of_linear (halfLineLinear_of_amortized hc h)

/-! ### Finite certificates for the amortised form -/

/-- Amortised halving for the lengths `1 ≤ d ≤ D` (all times). -/
def AmortizedHalvingUpTo (p c e D : ℕ) : Prop :=
  ∀ k, 0 < k → k < 2 ^ p → ∀ d m, 1 ≤ d → d ≤ D →
    (aliveCodes (driveN p k) d (d - 1 + m)).card * 2 ^ (m / c) ≤ 2 ^ (d - 1 + e)

/-- The Boolean check: every word, every `1 ≤ d ≤ D`, every `m ≤ c·(d + e)`. -/
def amortCheck (p c e D : ℕ) : Bool :=
  (List.range (2 ^ p)).all fun k => k == 0 ||
    (List.range (D + 1)).all fun d => d == 0 ||
      (List.range (c * (d + e) + 1)).all fun m =>
        decide ((aliveCodes (driveN p k) d (d - 1 + m)).card * 2 ^ (m / c) ≤ 2 ^ (d - 1 + e))

theorem amortizedHalvingUpTo_of_check {p c e D : ℕ} (hc : 0 < c)
    (h : amortCheck p c e D = true) : AmortizedHalvingUpTo p c e D := by
  intro k hk0 hk d m hd hdD
  have hk' := List.all_eq_true.1 h k (List.mem_range.2 hk)
  simp only [Bool.or_eq_true, beq_iff_eq, show k ≠ 0 by omega, false_or] at hk'
  have hd' := List.all_eq_true.1 hk' d (List.mem_range.2 (by omega))
  simp only [Bool.or_eq_true, beq_iff_eq, show d ≠ 0 by omega, false_or] at hd'
  have hm := fun m (hm : m ≤ c * (d + e)) =>
    of_decide_eq_true (List.all_eq_true.1 hd' m (List.mem_range.2 (by omega)))
  rcases le_or_gt m (c * (d + e)) with hle | hlt
  · exact hm m hle
  · -- at `m₀ = c (d + e)` the bound already forces zero survivors
    have h0 := hm (c * (d + e)) le_rfl
    rw [Nat.mul_div_cancel_left _ hc] at h0
    have hlt2 : 2 ^ (d - 1 + e) < 2 ^ (d + e) := Nat.pow_lt_pow_right (by norm_num) (by omega)
    have hz : (aliveCodes (driveN p k) d (d - 1 + c * (d + e))).card = 0 := by
      by_contra hne
      have : 2 ^ (d + e) ≤
          (aliveCodes (driveN p k) d (d - 1 + c * (d + e))).card * 2 ^ (d + e) :=
        Nat.le_mul_of_pos_left _ (Nat.pos_of_ne_zero hne)
      omega
    have hsub := Finset.card_le_card
      (aliveCodes_antitone (driveN p k) d (show d - 1 + c * (d + e) ≤ d - 1 + m by omega))
    rw [hz, Nat.le_zero] at hsub
    rw [hsub, zero_mul]
    exact Nat.zero_le _

/-! ## Drive symmetry: one word per rotation class -/

/-- Every non-empty half-line driven by `bd` eventually fails a check. -/
def WordDies (bd : ℕ → Bool) : Prop := ∀ S, 0 < S → ∃ T, dDiesBy bd S T = true

/-- One step of the machine keeps a non-empty half-line non-empty (the edge moves left). -/
theorem halfStep_pos {b : Bool} {S : ℕ} (hS : 0 < S) : 0 < halfStep b S := by
  rw [Nat.pos_iff_ne_zero]
  intro h0
  unfold halfStep at h0
  rw [Nat.xor_eq_zero_iff] at h0
  have h1 : S <<< 1 ≤ S ||| ((S <<< 1) ||| b.toNat) :=
    le_trans Nat.left_le_or Nat.right_le_or
  rw [← h0, Nat.shiftLeft_eq, Nat.shiftRight_eq_div_pow] at h1
  have : S / 2 ^ 1 ≤ S := Nat.div_le_self _ _
  omega

theorem halfStateD_pos (bd : ℕ → Bool) {S : ℕ} (hS : 0 < S) (t : ℕ) : 0 < halfStateD bd S t := by
  induction t with
  | zero => exact hS
  | succ t ih => exact halfStep_pos ih

/-- Running `s + t` steps is running `s` steps, then `t` steps of the drive started `s` late. -/
theorem halfStateD_add (bd : ℕ → Bool) (S s t : ℕ) :
    halfStateD bd S (s + t) = halfStateD (fun u => bd (u + s)) (halfStateD bd S s) t := by
  induction t with
  | zero => rfl
  | succ t ih =>
    rw [← Nat.add_assoc, halfStateD, ih, halfStateD, Nat.add_comm s t]

/-- A failure of the late-started machine is a failure of the original one. -/
theorem dDiesBy_of_shift {bd : ℕ → Bool} {S s T : ℕ}
    (h : dDiesBy (fun u => bd (u + s)) (halfStateD bd S s) T = true) :
    dDiesBy bd S (s + T) = true := by
  rw [dDiesBy_spec] at *
  obtain ⟨t, ht, hb, hw⟩ := h
  refine ⟨s + t, by omega, by rw [Nat.add_comm]; exact hb, ?_⟩
  rw [halfStateD_add, hw, show t + 1 + s = s + t + 1 by omega]

/-- **Dying for a late-started drive implies dying for the drive.** -/
theorem wordDies_of_shift {bd : ℕ → Bool} (s : ℕ) (h : WordDies (fun u => bd (u + s))) :
    WordDies bd := by
  intro S hS
  obtain ⟨T, hT⟩ := h (halfStateD bd S s) (halfStateD_pos bd hS s)
  exact ⟨s + T, dDiesBy_of_shift hT⟩

theorem drive_periodic_mul {bd : ℕ → Bool} {p : ℕ} (hper : ∀ t, bd (t + p) = bd t) (t k : ℕ) :
    bd (t + p * k) = bd t := by
  induction k with
  | zero => simp
  | succ k ih => rw [Nat.mul_succ, ← Nat.add_assoc, hper, ih]

/-- **For a periodic drive, every rotation is equivalent.** -/
theorem wordDies_shift_iff_of_periodic {bd : ℕ → Bool} {p : ℕ} (hp : 0 < p)
    (hper : ∀ t, bd (t + p) = bd t) (s : ℕ) :
    WordDies (fun u => bd (u + s)) ↔ WordDies bd := by
  refine ⟨wordDies_of_shift s, fun h => wordDies_of_shift (p * s - s) ?_⟩
  have hps : s ≤ p * s := Nat.le_mul_of_pos_left s hp
  have : (fun u => (fun u => bd (u + s)) (u + (p * s - s))) = bd := by
    funext u
    simp only
    rw [show u + (p * s - s) + s = u + p * s by omega, drive_periodic_mul hper]
  rw [this]
  exact h

theorem driveN_periodic {p : ℕ} (k t : ℕ) : driveN p k (t + p) = driveN p k t := by
  simp [driveN, Nat.add_mod_right]

/-- The constant black drive kills every non-empty half-line (the period-1 rung). -/
theorem wordDies_const : WordDies (fun _ => true) := fun S _ =>
  ⟨S + 2, constDrive_dies S S Nat.lt_two_pow_self⟩

theorem halfLineDies_iff (p : ℕ) :
    HalfLineDies p ↔ ∀ k, 0 < k → k < 2 ^ p → WordDies (driveN p k) := Iff.rfl

theorem wordDies_congr {bd bd' : ℕ → Bool} (h : bd = bd') : WordDies bd ↔ WordDies bd' := h ▸ Iff.rfl

/-- **Period 2 needs one drive word**: `HalfLineDies 2` iff the alternating drive `1, 0, 1, 0, …`
kills every non-empty half-line. -/
theorem halfLineDies_two_iff : HalfLineDies 2 ↔ WordDies (driveN 2 1) := by
  refine ⟨fun h => h 1 (by norm_num) (by norm_num), fun h k hk0 hk => ?_⟩
  have hper := driveN_periodic (p := 2) 1
  interval_cases k
  · exact h
  · rw [← wordDies_shift_iff_of_periodic (by norm_num) hper 1] at h
    refine (wordDies_congr (funext fun t => ?_)).1 h
    have : t % 2 < 2 := Nat.mod_lt _ (by norm_num)
    simp only [driveN]
    interval_cases ht : t % 2 <;> simp_all [Nat.add_mod] <;> decide
  · refine (wordDies_congr (funext fun t => ?_)).2 wordDies_const
    have : t % 2 < 2 := Nat.mod_lt _ (by norm_num)
    simp only [driveN]
    interval_cases ht : t % 2
    · simp_all
    · simp_all; decide

/-- **Period 3 needs two drive words**: `HalfLineDies 3` iff the drives `1, 0, 0, …` and
`1, 1, 0, …` kill every non-empty half-line. -/
theorem halfLineDies_three_iff :
    HalfLineDies 3 ↔ WordDies (driveN 3 1) ∧ WordDies (driveN 3 3) := by
  refine ⟨fun h => ⟨h 1 (by norm_num) (by norm_num), h 3 (by norm_num) (by norm_num)⟩,
    fun ⟨h1, h3⟩ k hk0 hk => ?_⟩
  have key : ∀ (j s : ℕ), WordDies (driveN 3 j) → (∀ t, driveN 3 j (t + s) = driveN 3 k t) →
      WordDies (driveN 3 k) := fun j s hj hs => by
    rw [← wordDies_shift_iff_of_periodic (by norm_num) (driveN_periodic (p := 3) j) s] at hj
    exact (wordDies_congr (funext hs)).1 hj
  interval_cases k
  · exact h1
  · refine key 1 2 h1 fun t => ?_
    have : t % 3 < 3 := Nat.mod_lt _ (by norm_num)
    simp only [driveN]
    interval_cases ht : t % 3 <;> simp_all [Nat.add_mod] <;> decide
  · exact h3
  · refine key 1 1 h1 fun t => ?_
    have : t % 3 < 3 := Nat.mod_lt _ (by norm_num)
    simp only [driveN]
    interval_cases ht : t % 3 <;> simp_all [Nat.add_mod] <;> decide
  · refine key 3 1 h3 fun t => ?_
    have : t % 3 < 3 := Nat.mod_lt _ (by norm_num)
    simp only [driveN]
    interval_cases ht : t % 3 <;> simp_all [Nat.add_mod] <;> decide
  · refine key 3 2 h3 fun t => ?_
    have : t % 3 < 3 := Nat.mod_lt _ (by norm_num)
    simp only [driveN]
    interval_cases ht : t % 3 <;> simp_all [Nat.add_mod] <;> decide
  · refine (wordDies_congr (funext fun t => ?_)).2 wordDies_const
    have : t % 3 < 3 := Nat.mod_lt _ (by norm_num)
    simp only [driveN]
    interval_cases ht : t % 3 <;> simp_all <;> decide

end GLM.Rule30
