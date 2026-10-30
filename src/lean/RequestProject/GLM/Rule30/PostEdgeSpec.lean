module

public import RequestProject.GLM.Rule30.AmortizedHalving

/-!
# Round 27: the transition specification of the half-line machine

Before a finite-state graph is used to certify the driven half-line machine, one has to know what
the machine's state is and what determines its next step.  This file proves the facts, for
**every** drive sequence:

* **The state grows by exactly one cell per step** (`halfStateD_width`): a code of length `d`
  (top bit `d - 1`) has length exactly `d + t` at time `t`.  Rule 30 is left-permutive, so the
  far-left black cell always produces a new black cell to its left.
* **No state ever repeats** (`halfStateD_strictMono`, `halfStateD_ne`).  The graph of full driven
  states reachable from a non-zero code is an infinite simple path: it has **no cycle**, so
  "no reachable cycle" certifies nothing, and "a reachable cycle" can never be found.  Pairing the
  state with the drive phase changes nothing (`halfStateD_phase_ne`).
* **No fixed width is closed** (`window_not_closed`): for every width `w ≥ 1` two states that
  agree on their `w` cells next to the column can have different next `w` cells.  So a graph whose
  nodes are `w`-cell windows does not determine its transitions.
* **What does determine the next step** (`halfStep_mod`): `w + 1` cells now determine `w` cells
  next step.  The sound finite object is therefore the *shrinking* window: `n` code bits determine
  the first `n` tests (`dDiesBy_congr`, Round 22).  This is the prefix tree used by
  `PrefixSearch.lean`.
* **The column history is a complete record** (`colHistory_determines`): the values of the cell
  next to the column at times `0, …, n - 1` determine the first `n` code bits.  No quotient of the
  state that keeps the whole column history is smaller than the state itself; a useful finite
  quotient has to forget part of the history (for period 2, the odd times, which are not tested).

## Width reduction in its sound form: inner columns

* `halfStep_shiftRight` / `halfStateD_shiftRight` — the cells left of the inner column `c - k`
  form the same kind of machine, driven by the inner column itself (`innerCol`).
* **`inner_never_fails`** — that inner machine, driven by its true column, never fails a test (a
  Rule 30 identity).
* **`inner_alternation_bound`** — so if the inner column follows a drive `bd'` on `[0, T]`, the
  machine with code `S >>> k` driven by `bd'` survives to `T`.  Contrapositive: an inner column
  cannot follow the alternating drive for longer than the inner code survives.  This is the
  precise form of "a wide survivor contains a narrower survivor".
-/

@[expose] public section

namespace GLM.Rule30

/-! ## The state grows by exactly one cell per step -/

theorem halfStep_lt {b : Bool} {S d : ℕ} (hS : S < 2 ^ d) : halfStep b S < 2 ^ (d + 1) := by
  have hz : ∀ j, d ≤ j → S.testBit j = false := fun j hj =>
    Nat.testBit_lt_two_pow (lt_of_lt_of_le hS (Nat.pow_le_pow_right (by norm_num) hj))
  apply Nat.lt_pow_two_of_testBit
  intro i hi
  rw [testBit_halfStep, if_neg (by omega), hz _ (by omega), hz _ (by omega), hz _ (by omega)]
  rfl

theorem halfStep_testBit_top {b : Bool} {S d : ℕ} (hd : 1 ≤ d) (h1 : 2 ^ (d - 1) ≤ S)
    (h2 : S < 2 ^ d) : (halfStep b S).testBit d = true := by
  have hz : ∀ j, d ≤ j → S.testBit j = false := fun j hj =>
    Nat.testBit_lt_two_pow (lt_of_lt_of_le h2 (Nat.pow_le_pow_right (by norm_num) hj))
  have ht : S.testBit (d - 1) = true :=
    Nat.testBit_of_two_pow_le_and_two_pow_add_one_gt h1 (by rwa [Nat.sub_add_cancel hd])
  rw [testBit_halfStep, if_neg (by omega), hz _ (by omega), hz _ le_rfl, ht]
  rfl

theorem halfStep_ge {b : Bool} {S d : ℕ} (hd : 1 ≤ d) (h1 : 2 ^ (d - 1) ≤ S) (h2 : S < 2 ^ d) :
    2 ^ d ≤ halfStep b S :=
  Nat.ge_two_pow_of_testBit (halfStep_testBit_top hd h1 h2)

/-- **Exact width.** A code of length `d ≥ 1` has length exactly `d + t` at time `t`. -/
theorem halfStateD_width (bd : ℕ → Bool) {S d : ℕ} (hd : 1 ≤ d) (h1 : 2 ^ (d - 1) ≤ S)
    (h2 : S < 2 ^ d) (t : ℕ) :
    2 ^ (d + t - 1) ≤ halfStateD bd S t ∧ halfStateD bd S t < 2 ^ (d + t) := by
  induction t with
  | zero => simpa using ⟨h1, h2⟩
  | succ t ih =>
    refine ⟨?_, ?_⟩
    · have := halfStep_ge (b := bd t) (d := d + t) (by omega) ih.1 ih.2
      simpa [halfStateD, show d + (t + 1) - 1 = d + t by omega] using this
    · have := halfStep_lt (b := bd t) ih.2
      simpa [halfStateD, Nat.add_assoc] using this

/-- **The driven state strictly increases.** -/
theorem halfStateD_strictMono (bd : ℕ → Bool) {S : ℕ} (hS : 0 < S) :
    StrictMono (halfStateD bd S) := by
  set d := Nat.log2 S + 1 with hd
  have h1 : 2 ^ (d - 1) ≤ S := by
    simp only [hd, Nat.add_sub_cancel]; exact Nat.log2_self_le hS.ne'
  have h2 : S < 2 ^ d := Nat.lt_log2_self
  apply strictMono_nat_of_lt_succ
  intro t
  have a := halfStateD_width bd (by omega) h1 h2 t
  have b := halfStateD_width bd (by omega) h1 h2 (t + 1)
  rw [show d + (t + 1) - 1 = d + t by omega] at b
  omega

/-- **No state ever repeats**: the reachable state graph has no cycle. -/
theorem halfStateD_ne (bd : ℕ → Bool) {S : ℕ} (hS : 0 < S) {s t : ℕ} (hst : s ≠ t) :
    halfStateD bd S s ≠ halfStateD bd S t :=
  fun h => hst ((halfStateD_strictMono bd hS).injective h)

/-- Pairing the state with the drive phase (any period) gives no cycle either. -/
theorem halfStateD_phase_ne (bd : ℕ → Bool) (p : ℕ) {S : ℕ} (hS : 0 < S) {s t : ℕ}
    (hst : s ≠ t) : (halfStateD bd S s, s % p) ≠ (halfStateD bd S t, t % p) :=
  fun h => halfStateD_ne bd hS hst (Prod.ext_iff.1 h).1

/-! ## Which window determines the next step -/

/-- **`w + 1` cells determine `w` cells one step later.** -/
theorem halfStep_mod (b : Bool) {S S' w : ℕ} (h : S % 2 ^ (w + 1) = S' % 2 ^ (w + 1)) :
    halfStep b S % 2 ^ w = halfStep b S' % 2 ^ w := by
  have hb : ∀ i, i < w + 1 → S.testBit i = S'.testBit i := fun i hi => by
    have := congrArg (fun x => x.testBit i) h
    simpa [Nat.testBit_mod_two_pow, hi] using this
  apply Nat.eq_of_testBit_eq
  intro i
  rw [Nat.testBit_mod_two_pow, Nat.testBit_mod_two_pow]
  by_cases hi : i < w
  · simp only [hi, decide_true, Bool.true_and]
    rw [testBit_halfStep, testBit_halfStep, hb (i + 1) (by omega), hb i (by omega)]
    split
    · rfl
    · rw [hb (i - 1) (by omega)]
  · simp [hi]

/-- **No fixed width is closed.** For every `w ≥ 1` and drive bit, the states `0` and `2^w` agree
on their `w` cells next to the column but have different next windows. -/
theorem window_not_closed (b : Bool) {w : ℕ} (hw : 1 ≤ w) :
    0 % 2 ^ w = 2 ^ w % 2 ^ w ∧ halfStep b 0 % 2 ^ w ≠ halfStep b (2 ^ w) % 2 ^ w := by
  refine ⟨by simp, fun h => ?_⟩
  have := congrArg (fun x => x.testBit (w - 1)) h
  simp only [Nat.testBit_mod_two_pow, show w - 1 < w by omega, decide_true, Bool.true_and,
    testBit_halfStep, Nat.zero_testBit, Nat.testBit_two_pow] at this
  rcases Nat.eq_or_lt_of_le hw with rfl | hw'
  · cases b <;> simp_all
  · simp [show w - 1 ≠ 0 by omega, show w ≠ w - 1 by omega, show w ≠ w - 1 - 1 by omega,
      show w - 1 + 1 = w by omega] at this

/-- **The column history determines the code.** If the cell next to the column has the same
values at times `0, …, n - 1` for two codes, the codes agree on their first `n` bits. -/
theorem colHistory_determines (bd : ℕ → Bool) {S S' n : ℕ}
    (h : ∀ t < n, (halfStateD bd S t).testBit 0 = (halfStateD bd S' t).testBit 0) :
    S % 2 ^ n = S' % 2 ^ n := by
  by_contra hne
  have hex : ∃ m, m < n ∧ S.testBit m ≠ S'.testBit m := by
    by_contra hc
    push_neg at hc
    apply hne
    apply Nat.eq_of_testBit_eq
    intro i
    rw [Nat.testBit_mod_two_pow, Nat.testBit_mod_two_pow]
    by_cases hi : i < n
    · simp [hi, hc i hi]
    · simp [hi]
  classical
  let m := Nat.find hex
  have hm : m < n ∧ S.testBit m ≠ S'.testBit m := Nat.find_spec hex
  have hlow : ∀ i < m, S.testBit i = S'.testBit i := by
    intro i hi
    by_contra hc
    exact Nat.find_min hex hi ⟨by omega, hc⟩
  have := halfStateD_testBit_flip bd hlow hm.2 m le_rfl
  rw [Nat.sub_self] at this
  exact this (h m hm.1)

/-! ## Inner columns -/

/-- The inner column `c - k` of the machine (bit `k - 1` of the state). -/
def innerCol (bd : ℕ → Bool) (S k : ℕ) (t : ℕ) : Bool := (halfStateD bd S t).testBit (k - 1)

theorem halfStep_shiftRight (b : Bool) (S : ℕ) {k : ℕ} (hk : 1 ≤ k) :
    halfStep b S >>> k = halfStep (S.testBit (k - 1)) (S >>> k) := by
  apply Nat.eq_of_testBit_eq
  intro i
  rw [Nat.testBit_shiftRight, testBit_halfStep, testBit_halfStep, if_neg (by omega),
    Nat.testBit_shiftRight, Nat.testBit_shiftRight, show k + i + 1 = k + (i + 1) by omega]
  split
  · next hi => subst hi; simp
  · next hi => rw [Nat.testBit_shiftRight, show k + i - 1 = k + (i - 1) by omega]

/-- **The cells left of an inner column form a driven machine**, driven by that column. -/
theorem halfStateD_shiftRight (bd : ℕ → Bool) (S : ℕ) {k : ℕ} (hk : 1 ≤ k) (t : ℕ) :
    halfStateD bd S t >>> k = halfStateD (innerCol bd S k) (S >>> k) t := by
  induction t with
  | zero => rfl
  | succ t ih =>
    rw [halfStateD, halfStateD, halfStep_shiftRight _ _ hk, ih]
    rfl

/-- **The inner machine driven by its true column never fails.** -/
theorem inner_never_fails (bd : ℕ → Bool) (S : ℕ) {k : ℕ} (hk : 1 ≤ k) (T : ℕ) :
    dDiesBy (innerCol bd S k) (S >>> k) T = false := by
  rw [Bool.eq_false_iff]
  intro h
  rw [dDiesBy_spec] at h
  obtain ⟨t, -, hb, hw⟩ := h
  rw [← halfStateD_shiftRight bd S hk, Nat.testBit_shiftRight, Nat.add_zero] at hw
  unfold innerCol at hb hw
  rw [halfStateD, testBit_halfStep, show k - 1 + 1 = k by omega, hb, Bool.true_or] at hw
  cases h' : (halfStateD bd S t).testBit k <;> simp_all

/-- Machines with drives agreeing before `T` have the same states up to `T`. -/
theorem halfStateD_congr_drive {bd bd' : ℕ → Bool} {T : ℕ} (h : ∀ t < T, bd t = bd' t) (S : ℕ) :
    ∀ t ≤ T, halfStateD bd S t = halfStateD bd' S t := by
  intro t
  induction t with
  | zero => intro; rfl
  | succ t ih => intro ht; rw [halfStateD, halfStateD, ih (by omega), h t (by omega)]

/-- **Width reduction, sound form.** If the inner column `c - k` follows the drive `bd'` at times
`0, …, T`, the machine with the inner code `S >>> k` driven by `bd'` survives every test before
`T`. -/
theorem inner_alternation_bound (bd bd' : ℕ → Bool) (S : ℕ) {k T : ℕ} (hk : 1 ≤ k)
    (h : ∀ t ≤ T, innerCol bd S k t = bd' t) : dDiesBy bd' (S >>> k) T = false := by
  have key := inner_never_fails bd S hk T
  rw [Bool.eq_false_iff] at key ⊢
  intro h'
  apply key
  rw [dDiesBy_spec] at h' ⊢
  obtain ⟨t, ht, hb, hw⟩ := h'
  refine ⟨t, ht, by rw [h t (by omega)]; exact hb, ?_⟩
  rw [halfStateD_congr_drive (fun s hs => h s (by omega)) (S >>> k) t (le_refl t), hw,
    h (t + 1) (by omega)]

/-- **Contrapositive: an inner column cannot follow a drive past the inner code's failure.** -/
theorem innerCol_breaks (bd bd' : ℕ → Bool) (S : ℕ) {k T : ℕ} (hk : 1 ≤ k)
    (h : dDiesBy bd' (S >>> k) T = true) : ∃ t ≤ T, innerCol bd S k t ≠ bd' t := by
  by_contra hc
  push_neg at hc
  rw [inner_alternation_bound bd bd' S hk hc] at h
  exact Bool.noConfusion h

end GLM.Rule30
