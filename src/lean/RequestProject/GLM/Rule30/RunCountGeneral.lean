module

public import RequestProject.GLM.Rule30.RunCountLaw
public import RequestProject.GLM.Rule30.XorAlternatives

/-!
# Round 24: the counting law needs the XOR, not the OR

Round 23 proved the exact counting law `runCount_law` for Rule 30: for `p - 1 ≤ T < d`, exactly
`2^(d + p - 1)` of the left-white contexts keep the column at distance `d` `p`-periodic through
time `T`.  The proof used one fact about Rule 30: it is *left-permutive* (`L xor …`).

Here the law is proved for **every** left-permutive wheel, i.e. (`leftPermutive_iff_innerRule`)
for every wheel `L xor h(C, R)`, whatever the gate `h` in place of the OR.

* `ecaEvolve_flip_left` : left-permutive wheels propagate a flip of the far-left cell.
* `RunCountW r p d T` : the count for wheel `r`; `runCountW_thirty` : for `r = 30` it is
  Round 23's `RunCount`.
* **`runCountW_law`** : `RunCountW r p d T = 2^(d + p - 1)` for every left-permutive `r`.
* **`innerRule_runCount_law`** : the same for every `L xor h(C, R)`.
* **`outer_runCount_law_iff`** : among the 16 wheels `g(L, C or R)`, the period-2 law holds exactly
  for the left-permutive ones (`g` = `xor`, `xnor`, `L`, `not L`); for the other twelve it fails
  already at `d = 3` or `d = 4` (`outer_law_fails`, finite check; these checks are in
  `XorAlternativesData.lean`).  E.g. AND (wheel 224) gives 21
  and OR (wheel 254) gives 17 contexts instead of 16 (`outer_and_breaks_law`,
  `outer_or_breaks_law`).
* **`runCountW_law_right`** : for a *right*-permutive wheel the law holds for **every** `T`, with no
  edge: the fresh cell of each test is then the far-right cell `d + t`, and the right side of a
  left-white row is free for ever.  In particular for wheel 86, the mirror image of Rule 30, which
  has the same centre column, `RunCountW 86 2 d T = 2^(d+1)` for all `T ≥ 1`
  (`runCountW_eightySix`), while for Rule 30 `RunCountW 30 2 3 3 = 20` (`runCountW_thirty_edge`).
  Which side of the column carries the XOR, relative to the white side of the row, decides whether
  the observer's tests stay fair for ever or run into the edge.

So the counting law, which is the part of the Round 21–23 picture that *is* proved, is a property
of the XOR alone; the OR plays no role in it.  Conversely (`XorAlternatives.lean`) the XOR alone
does not keep the centre column from collapsing: `inner_alternative_periodic` settles every
non-OR-type gate `h`.  The open problem lives exactly where the two ingredients meet.
-/

@[expose] public section

namespace GLM.Rule30

open Finset

/-- **Left-permutivity on the whole line, for every left-permutive wheel.** If two rows agree on
`(j, j + 2t]` and differ at `j`, then after `t` steps they differ at `j + t`. -/
theorem ecaEvolve_flip_left {r : ℕ} (hr : IsLeftPermutive r) (x y : Config) (j : ℤ) :
    ∀ t : ℕ, x j ≠ y j → (∀ i, j < i → i ≤ j + 2 * t → x i = y i) →
      ecaEvolve r x t (j + t) ≠ ecaEvolve r y t (j + t) := by
  intro t
  induction t with
  | zero => intro h _; simpa using h
  | succ t ih =>
    intro hj hagree
    have e1 : ecaEvolve r x t (j + (t + 1 : ℕ)) = ecaEvolve r y t (j + (t + 1 : ℕ)) :=
      ecaEvolve_congr r x y t _ fun i h1 h2 => hagree i (by push_cast at *; omega)
        (by push_cast at *; omega)
    have e2 : ecaEvolve r x t (j + (t + 1 : ℕ) + 1) = ecaEvolve r y t (j + (t + 1 : ℕ) + 1) :=
      ecaEvolve_congr r x y t _ fun i h1 h2 => hagree i (by push_cast at *; omega)
        (by push_cast at *; omega)
    have hl := ih hj fun i h1 h2 => hagree i h1 (by push_cast; omega)
    rw [ecaEvolve_succ, ecaEvolve_succ, e2,
      show j + ((t + 1 : ℕ) : ℤ) - 1 = j + t by push_cast; ring, e1]
    generalize ecaEvolve r y t (j + (t + 1 : ℕ)) = C at *
    generalize ecaEvolve r y t (j + (t + 1 : ℕ) + 1) = R at *
    revert hl
    cases ecaEvolve r x t (j + t) <;> cases ecaEvolve r y t (j + t) <;>
      simp [hr C R]

/-- The column at distance `d` of wheel `r` repeats with period `p` at time `t`. -/
def PeriodTestW (r p d : ℕ) (x : Config) (t : ℕ) : Prop :=
  ecaEvolve r x t d = ecaEvolve r x (t - p) d

instance (r p d : ℕ) (x : Config) (t : ℕ) : Decidable (PeriodTestW r p d x t) := by
  unfold PeriodTestW; infer_instance

/-- The contexts `P < 2^n` passing every period test of wheel `r` at the times `p ≤ t ≤ T`. -/
def passingW (r p d n T : ℕ) : Finset ℕ :=
  (range (2 ^ n)).filter fun P => ∀ t ∈ Icc p T, PeriodTestW r p d (ctxRow n P) t

/-- **`RunCountW r p d T`**: the number of left-white contexts (black edge at `0`, free cells
`x 1 … x (d + T)`) for which wheel `r` keeps the column at distance `d` `p`-periodic through time
`T`. -/
def RunCountW (r p d T : ℕ) : ℕ := (passingW r p d (d + T) T).card

/-- For wheel 30 this is Round 23's count. -/
theorem runCountW_thirty (p d T : ℕ) : RunCountW 30 p d T = RunCount p d T := by
  simp only [RunCountW, RunCount, passingW, passing, PeriodTestW, PeriodTest, ecaEvolve_thirty]

theorem column_flipW {r : ℕ} (hr : IsLeftPermutive r) (n P d t : ℕ) (ht : t < d) (hn : d ≤ n) :
    (∀ s < t, ecaEvolve r (ctxRow n (P ^^^ 2 ^ (d - t - 1))) s d =
        ecaEvolve r (ctxRow n P) s d) ∧
      ecaEvolve r (ctxRow n (P ^^^ 2 ^ (d - t - 1))) t d ≠ ecaEvolve r (ctxRow n P) t d := by
  have hx := ctxRow_xor n P (d - t - 1) (by omega)
  constructor
  · intro s hs
    refine ecaEvolve_congr r _ _ s _ fun i h1 h2 => ?_
    rw [hx i, if_neg (by push_cast; omega)]
  · have := ecaEvolve_flip_left hr (ctxRow n (P ^^^ 2 ^ (d - t - 1))) (ctxRow n P)
      ((d : ℤ) - t) t
      (by rw [hx, if_pos (by push_cast; omega)]; simp)
      (fun i h1 h2 => by rw [hx i, if_neg (by push_cast; omega)])
    simpa using this

/-- **Each fresh test halves the survivors, exactly**, for every left-permutive wheel. -/
theorem card_testsW_succ {r : ℕ} (hr : IsLeftPermutive r) (p d n T : ℕ) (hp : 1 ≤ p)
    (hpT : p ≤ T + 1) (hTd : T + 1 < d) (hn : d ≤ n) :
    2 * (passingW r p d n (T + 1)).card = (passingW r p d n T).card := by
  set k := d - (T + 1) - 1
  have hk : k < n := by omega
  have hsplit : passingW r p d n (T + 1) =
      (passingW r p d n T).filter fun P => PeriodTestW r p d (ctxRow n P) (T + 1) := by
    ext P
    simp only [passingW, mem_filter, mem_range, mem_Icc]
    constructor
    · rintro ⟨h1, h2⟩; exact ⟨⟨h1, fun t ht => h2 t ⟨ht.1, by omega⟩⟩, h2 _ ⟨hpT, le_rfl⟩⟩
    · rintro ⟨⟨h1, h2⟩, h3⟩
      refine ⟨h1, fun t ht => ?_⟩
      rcases Nat.lt_or_ge t (T + 1) with h | h
      · exact h2 t ⟨ht.1, by omega⟩
      · rwa [show t = T + 1 by omega]
  have hcf : ∀ P, (∀ s < T + 1, ecaEvolve r (ctxRow n (P ^^^ 2 ^ k)) s d =
      ecaEvolve r (ctxRow n P) s d) ∧
      ecaEvolve r (ctxRow n (P ^^^ 2 ^ k)) (T + 1) d ≠ ecaEvolve r (ctxRow n P) (T + 1) d :=
    fun P => column_flipW hr n P d (T + 1) (by omega) hn
  have hkeep : ∀ P, ∀ t ≤ T, (PeriodTestW r p d (ctxRow n (P ^^^ 2 ^ k)) t ↔
      PeriodTestW r p d (ctxRow n P) t) := by
    intro P t ht
    unfold PeriodTestW
    rw [(hcf P).1 t (by omega), (hcf P).1 (t - p) (by omega)]
  have htog : ∀ P, (PeriodTestW r p d (ctxRow n (P ^^^ 2 ^ k)) (T + 1) ↔
      ¬ PeriodTestW r p d (ctxRow n P) (T + 1)) := by
    intro P
    unfold PeriodTestW
    rw [(hcf P).1 (T + 1 - p) (by omega)]
    have := (hcf P).2
    cases h1 : ecaEvolve r (ctxRow n (P ^^^ 2 ^ k)) (T + 1) d <;>
      cases h2 : ecaEvolve r (ctxRow n P) (T + 1) d <;>
      cases ecaEvolve r (ctxRow n P) (T + 1 - p) d <;> simp_all
  have hmem : ∀ P, P ∈ passingW r p d n T → P ^^^ 2 ^ k ∈ passingW r p d n T := by
    intro P hP
    simp only [passingW, mem_filter, mem_range, mem_Icc] at hP ⊢
    exact ⟨xor_two_pow_lt hP.1 hk, fun t ht => (hkeep P t ht.2).2 (hP.2 t ht)⟩
  have hbij : ((passingW r p d n T).filter fun P => PeriodTestW r p d (ctxRow n P) (T + 1)).card =
      ((passingW r p d n T).filter fun P =>
        ¬ PeriodTestW r p d (ctxRow n P) (T + 1)).card := by
    refine Finset.card_nbij' (fun P => P ^^^ 2 ^ k) (fun P => P ^^^ 2 ^ k) ?_ ?_ ?_ ?_
    · intro P hP
      simp only [coe_filter, Set.mem_setOf_eq] at hP ⊢
      exact ⟨hmem P hP.1, fun h => (htog P).1 h hP.2⟩
    · intro P hP
      simp only [coe_filter, Set.mem_setOf_eq] at hP ⊢
      exact ⟨hmem P hP.1, (htog P).2 hP.2⟩
    · intro P _
      show (P ^^^ 2 ^ k) ^^^ 2 ^ k = P
      rw [Nat.xor_assoc, Nat.xor_self, Nat.xor_zero]
    · intro P _
      show (P ^^^ 2 ^ k) ^^^ 2 ^ k = P
      rw [Nat.xor_assoc, Nat.xor_self, Nat.xor_zero]
  have := Finset.card_filter_add_card_filter_not (s := passingW r p d n T)
    (fun P => PeriodTestW r p d (ctxRow n P) (T + 1))
  rw [hsplit]
  omega

theorem passingW_card_of_lt (r p d n T : ℕ) (hT : T < p) :
    (passingW r p d n T).card = 2 ^ n := by
  rw [passingW, Finset.filter_true_of_mem, card_range]
  intro P _ t ht
  simp only [mem_Icc] at ht
  omega

theorem passingW_card {r : ℕ} (hr : IsLeftPermutive r) (p d n : ℕ) (hp : 1 ≤ p) (hn : d ≤ n) :
    ∀ T, T < d → (passingW r p d n T).card * 2 ^ (T + 1 - p) = 2 ^ n := by
  intro T
  induction T with
  | zero =>
    intro _; rw [passingW_card_of_lt r p d n 0 (by omega)]; simp [show 1 - p = 0 by omega]
  | succ T ih =>
    intro hT
    rcases Nat.lt_or_ge (T + 1) p with h | h
    · rw [passingW_card_of_lt r p d n (T + 1) h, show T + 1 + 1 - p = 0 by omega]; simp
    · have h2 := card_testsW_succ hr p d n T hp h (by omega) hn
      rw [← ih (by omega), ← h2, show T + 1 + 1 - p = (T + 1 - p) + 1 by omega, pow_succ]
      ring

/-- **The counting law for every left-permutive wheel.** For every period `p ≥ 1` and
`p - 1 ≤ T < d`, exactly `2^(d + p - 1)` of the `2^(d + T)` left-white contexts keep the column
at distance `d` `p`-periodic through time `T`. -/
theorem runCountW_law {r : ℕ} (hr : IsLeftPermutive r) (p d T : ℕ) (hp : 1 ≤ p)
    (hpT : p ≤ T + 1) (hTd : T < d) : RunCountW r p d T = 2 ^ (d + p - 1) := by
  have h := passingW_card hr p d (d + T) hp (by omega) T hTd
  have h2 : 2 ^ (d + T) = 2 ^ (d + p - 1) * 2 ^ (T + 1 - p) := by
    rw [← pow_add]; congr 1; omega
  rw [h2] at h
  exact Nat.eq_of_mul_eq_mul_right (by positivity) h

/-- **The counting law does not see the OR.** For every gate `h`, the wheel `L xor h(C, R)` obeys
the same exact counting law as Rule 30. -/
theorem innerRule_runCount_law (h : BinGate) (p d T : ℕ) (hp : 1 ≤ p) (hpT : p ≤ T + 1)
    (hTd : T < d) : RunCountW (innerRule h) p d T = 2 ^ (d + p - 1) :=
  runCountW_law (innerRule_leftPermutive h) p d T hp hpT hTd

/-! ## The mirror image: right-permutive wheels obey the law for all times

The law above stops at `T = d` because the far-left cell of the light cone reaches the black
edge.  For a *right-permutive* wheel (`… xor R`) the fresh cell of each test is the far-right one,
`d + t`, and in a left-white row the right side is free for ever.  So the law never stops. -/

/-- Wheel `r` is right-permutive: flipping `R` always flips the output. -/
def IsRightPermutive (r : ℕ) : Prop := ∀ L C : Bool, ecaRule r L C true = !ecaRule r L C false

instance (r : ℕ) : Decidable (IsRightPermutive r) := by unfold IsRightPermutive; infer_instance

theorem rightPermutive_eightySix : IsRightPermutive 86 := by decide

theorem not_rightPermutive_thirty : ¬ IsRightPermutive 30 := by decide

/-- **Right-permutivity on the whole line.** If two rows agree on `[j - 2t, j)` and differ at `j`,
then after `t` steps they differ at `j - t`. -/
theorem ecaEvolve_flip_right {r : ℕ} (hr : IsRightPermutive r) (x y : Config) (j : ℤ) :
    ∀ t : ℕ, x j ≠ y j → (∀ i, j - 2 * t ≤ i → i < j → x i = y i) →
      ecaEvolve r x t (j - t) ≠ ecaEvolve r y t (j - t) := by
  intro t
  induction t with
  | zero => intro h _; simpa using h
  | succ t ih =>
    intro hj hagree
    have e1 : ecaEvolve r x t (j - (t + 1 : ℕ) - 1) = ecaEvolve r y t (j - (t + 1 : ℕ) - 1) :=
      ecaEvolve_congr r x y t _ fun i h1 h2 => hagree i (by push_cast at *; omega)
        (by push_cast at *; omega)
    have e2 : ecaEvolve r x t (j - (t + 1 : ℕ)) = ecaEvolve r y t (j - (t + 1 : ℕ)) :=
      ecaEvolve_congr r x y t _ fun i h1 h2 => hagree i (by push_cast at *; omega)
        (by push_cast at *; omega)
    have hl := ih hj fun i h1 h2 => hagree i (by push_cast; omega) h2
    rw [ecaEvolve_succ, ecaEvolve_succ, e1, e2,
      show j - ((t + 1 : ℕ) : ℤ) + 1 = j - t by push_cast; ring]
    generalize ecaEvolve r y t (j - (t + 1 : ℕ) - 1) = L at *
    generalize ecaEvolve r y t (j - (t + 1 : ℕ)) = C at *
    revert hl
    cases ecaEvolve r x t (j - t) <;> cases ecaEvolve r y t (j - t) <;>
      simp [hr L C]

theorem column_flipW_right {r : ℕ} (hr : IsRightPermutive r) (n P d t : ℕ) (ht : 1 ≤ t)
    (hn : d + t ≤ n) :
    (∀ s < t, ecaEvolve r (ctxRow n (P ^^^ 2 ^ (d + t - 1))) s d =
        ecaEvolve r (ctxRow n P) s d) ∧
      ecaEvolve r (ctxRow n (P ^^^ 2 ^ (d + t - 1))) t d ≠ ecaEvolve r (ctxRow n P) t d := by
  have hx := ctxRow_xor n P (d + t - 1) (by omega)
  constructor
  · intro s hs
    refine ecaEvolve_congr r _ _ s _ fun i h1 h2 => ?_
    rw [hx i, if_neg (by push_cast; omega)]
  · have := ecaEvolve_flip_right hr (ctxRow n (P ^^^ 2 ^ (d + t - 1))) (ctxRow n P)
      ((d : ℤ) + t) t
      (by rw [hx, if_pos (by push_cast; omega)]; simp)
      (fun i h1 h2 => by rw [hx i, if_neg (by push_cast; omega)])
    simpa using this

/-- **Each test halves the survivors, at every time**, for a right-permutive wheel. -/
theorem card_testsW_succ_right {r : ℕ} (hr : IsRightPermutive r) (p d n T : ℕ) (hp : 1 ≤ p)
    (hpT : p ≤ T + 1) (hn : d + T + 1 ≤ n) :
    2 * (passingW r p d n (T + 1)).card = (passingW r p d n T).card := by
  set k := d + (T + 1) - 1
  have hk : k < n := by omega
  have hsplit : passingW r p d n (T + 1) =
      (passingW r p d n T).filter fun P => PeriodTestW r p d (ctxRow n P) (T + 1) := by
    ext P
    simp only [passingW, mem_filter, mem_range, mem_Icc]
    constructor
    · rintro ⟨h1, h2⟩; exact ⟨⟨h1, fun t ht => h2 t ⟨ht.1, by omega⟩⟩, h2 _ ⟨hpT, le_rfl⟩⟩
    · rintro ⟨⟨h1, h2⟩, h3⟩
      refine ⟨h1, fun t ht => ?_⟩
      rcases Nat.lt_or_ge t (T + 1) with h | h
      · exact h2 t ⟨ht.1, by omega⟩
      · rwa [show t = T + 1 by omega]
  have hcf : ∀ P, (∀ s < T + 1, ecaEvolve r (ctxRow n (P ^^^ 2 ^ k)) s d =
      ecaEvolve r (ctxRow n P) s d) ∧
      ecaEvolve r (ctxRow n (P ^^^ 2 ^ k)) (T + 1) d ≠ ecaEvolve r (ctxRow n P) (T + 1) d :=
    fun P => column_flipW_right hr n P d (T + 1) (by omega) (by omega)
  have hkeep : ∀ P, ∀ t ≤ T, (PeriodTestW r p d (ctxRow n (P ^^^ 2 ^ k)) t ↔
      PeriodTestW r p d (ctxRow n P) t) := by
    intro P t ht
    unfold PeriodTestW
    rw [(hcf P).1 t (by omega), (hcf P).1 (t - p) (by omega)]
  have htog : ∀ P, (PeriodTestW r p d (ctxRow n (P ^^^ 2 ^ k)) (T + 1) ↔
      ¬ PeriodTestW r p d (ctxRow n P) (T + 1)) := by
    intro P
    unfold PeriodTestW
    rw [(hcf P).1 (T + 1 - p) (by omega)]
    have := (hcf P).2
    cases h1 : ecaEvolve r (ctxRow n (P ^^^ 2 ^ k)) (T + 1) d <;>
      cases h2 : ecaEvolve r (ctxRow n P) (T + 1) d <;>
      cases ecaEvolve r (ctxRow n P) (T + 1 - p) d <;> simp_all
  have hmem : ∀ P, P ∈ passingW r p d n T → P ^^^ 2 ^ k ∈ passingW r p d n T := by
    intro P hP
    simp only [passingW, mem_filter, mem_range, mem_Icc] at hP ⊢
    exact ⟨xor_two_pow_lt hP.1 hk, fun t ht => (hkeep P t ht.2).2 (hP.2 t ht)⟩
  have hbij : ((passingW r p d n T).filter fun P => PeriodTestW r p d (ctxRow n P) (T + 1)).card =
      ((passingW r p d n T).filter fun P =>
        ¬ PeriodTestW r p d (ctxRow n P) (T + 1)).card := by
    refine Finset.card_nbij' (fun P => P ^^^ 2 ^ k) (fun P => P ^^^ 2 ^ k) ?_ ?_ ?_ ?_
    · intro P hP
      simp only [coe_filter, Set.mem_setOf_eq] at hP ⊢
      exact ⟨hmem P hP.1, fun h => (htog P).1 h hP.2⟩
    · intro P hP
      simp only [coe_filter, Set.mem_setOf_eq] at hP ⊢
      exact ⟨hmem P hP.1, (htog P).2 hP.2⟩
    · intro P _
      show (P ^^^ 2 ^ k) ^^^ 2 ^ k = P
      rw [Nat.xor_assoc, Nat.xor_self, Nat.xor_zero]
    · intro P _
      show (P ^^^ 2 ^ k) ^^^ 2 ^ k = P
      rw [Nat.xor_assoc, Nat.xor_self, Nat.xor_zero]
  have := Finset.card_filter_add_card_filter_not (s := passingW r p d n T)
    (fun P => PeriodTestW r p d (ctxRow n P) (T + 1))
  rw [hsplit]
  omega

theorem passingW_card_right {r : ℕ} (hr : IsRightPermutive r) (p d n : ℕ) (hp : 1 ≤ p) :
    ∀ T, d + T ≤ n → (passingW r p d n T).card * 2 ^ (T + 1 - p) = 2 ^ n := by
  intro T
  induction T with
  | zero =>
    intro _; rw [passingW_card_of_lt r p d n 0 (by omega)]; simp [show 1 - p = 0 by omega]
  | succ T ih =>
    intro hT
    rcases Nat.lt_or_ge (T + 1) p with h | h
    · rw [passingW_card_of_lt r p d n (T + 1) h, show T + 1 + 1 - p = 0 by omega]; simp
    · have h2 := card_testsW_succ_right hr p d n T hp h (by omega)
      rw [← ih (by omega), ← h2, show T + 1 + 1 - p = (T + 1 - p) + 1 by omega, pow_succ]
      ring

/-- **The counting law with no edge.** For a right-permutive wheel, for every period `p ≥ 1`,
every distance `d` and **every** `T ≥ p - 1`, exactly `2^(d + p - 1)` left-white contexts keep the
column at distance `d` `p`-periodic through time `T`. -/
theorem runCountW_law_right {r : ℕ} (hr : IsRightPermutive r) (p d T : ℕ) (hp : 1 ≤ p)
    (hpT : p ≤ T + 1) : RunCountW r p d T = 2 ^ (d + p - 1) := by
  have h := passingW_card_right hr p d (d + T) hp T le_rfl
  have h2 : 2 ^ (d + T) = 2 ^ (d + p - 1) * 2 ^ (T + 1 - p) := by
    rw [← pow_add]; congr 1; omega
  rw [h2] at h
  exact Nat.eq_of_mul_eq_mul_right (by positivity) h

/-- **Rule 30 and its mirror, Rule 86, in the same left-white frame.** They have the same centre
column from the single black cell (`problem1_iff_eightySix`), but for wheel 86 the period-2
counting law is exact for ever, while for Rule 30 it breaks at the edge `T = d`
(`RunCount 2 3 3 = 20`, `runCountW_thirty_edge`). -/
theorem runCountW_eightySix (d T : ℕ) (hT : 1 ≤ T) : RunCountW 86 2 d T = 2 ^ (d + 1) :=
  runCountW_law_right rightPermutive_eightySix 2 d T (by norm_num) (by omega)

end GLM.Rule30
