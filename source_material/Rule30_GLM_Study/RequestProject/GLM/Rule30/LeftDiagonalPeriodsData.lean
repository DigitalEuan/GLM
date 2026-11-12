import RequestProject.GLM.Rule30.LeftDiagonalPeriods

/-!
# Round 38: left-diagonal periods, certified (data for the hypothesis engine)

(Not a `module`: it uses `native_decide`.)

**The certificate scheme.**  Bit `k` of a row read from the left edge depends only on bits `≤ k`
of the previous row, so the first `N` left diagonals, packed into one number `lrow N t`, evolve
**autonomously**: `lrow N (t+1) = lstep (2^N − 1) (lrow N t)` with
`lstep m r = ((r <<< 2) xor ((r <<< 1) or r)) and m` (`testBit_lrow`: bit `D` is `ldiag D t`).
Hence **one equality** `lrow N (s + p) = lrow N s` proves that all of the diagonals `D < N` are
periodic with period `p` from time `s` on, for **all** later times (`evPer_of_lrow`).  This turns
a finite check into a theorem about every `t` — the engine's cheap guess for this family is closed by
one computation.

**What is certified** (each is one `native_decide` comparison):

* `leftDiag_period_eight_below_400` : every left diagonal `D < 400` has eventual period `8`
  (from `t = 501`).  This extends the `EMP` observation C133 (`D ≤ 200`).
* `not_leftDiagPeriodDivides_eight` : **refutation** of the engine's first generalisation —
  diagonal `400` does not have eventual period `8` (it has least period `16`).
* `leftDiag_399_white` : the cause — diagonal `399` is eventually white, and diagonal `398` has odd
  parity over its period (the doubling law of `LeftDiagonalPeriods.lean`).
* `leftDiag_period_sixteen_below_87867` : every left diagonal `D < 87867` has eventual period `16`
  (from `t = 117324`).
* `not_leftDiagPeriodDivides_sixteen` : **refutation** of the engine's second generalisation —
  diagonal `87867` does not have eventual period `16`.  The engine **predicted** this diagonal
  from the period law (by running the law on period patterns) before it was checked.
* `leftDiag_white_below_87868` : the eventually white left diagonals below `87868` are exactly
  `2, 7, 28, 399, 53207, 58286, 87866`.
* `seed_first_difference` : for every row white on `(−∞, 0)` and black at `0`, the first left
  diagonal below `87868` on which it differs eventually from the single black cell is one of
  `3, 8, 29, 400, 53208, 58287, 87867` (the seed-forgetting law plus the white list).
* `leftDiag_transient_at_read`, `centerCol_read_in_transient` : for `20 ≤ D < 20000` left
  diagonal `D` is still in its transient at time `D`, so the centre column `a(D) = ldiag D D`
  always reads it before it settles (an engine survivor; C133 had it as `EMP` for `D ≤ 200`).

The least periods `1, 2, 4, 8, 16, 32` first occur at `D = 0, 3, 8, 29, 400, 87867`; each doubling
sits right after an eventually white diagonal, as the law requires.  Whether the periods are
unbounded stays open; by `infinitely_many_white_of_unbounded` it would need infinitely many
eventually white left diagonals.
-/

namespace GLM.Rule30

/-! ## The packed left-aligned row -/

/-- One step of the packed row, masked to the first bits of `m = 2^N − 1`. -/
def lstep (m r : ℕ) : ℕ := ((r <<< 2) ^^^ ((r <<< 1) ||| r)) &&& m

/-- The first `N` left diagonals at time `t`, packed: bit `D` is `ldiag D t`. -/
def lrow (N t : ℕ) : ℕ := (lstep (2 ^ N - 1))^[t] 1

theorem lrow_succ (N t : ℕ) : lrow N (t + 1) = lstep (2 ^ N - 1) (lrow N t) := by
  unfold lrow; rw [Function.iterate_succ_apply']

theorem lrow_add (N s n : ℕ) : lrow N (s + n) = (lstep (2 ^ N - 1))^[n] (lrow N s) := by
  unfold lrow; rw [add_comm, Function.iterate_add_apply]

theorem ldiag_zero_time (D : ℕ) : ldiag D 0 = decide (D = 0) := by
  simp [ldiag, seed]

/-- **Bit `D` of the packed row is the left diagonal `D`.** -/
theorem testBit_lrow {N D : ℕ} (hD : D < N) (t : ℕ) : (lrow N t).testBit D = ldiag D t := by
  induction t generalizing D with
  | zero =>
    rw [ldiag_zero_time]
    simp only [lrow, Function.iterate_zero, id_eq]
    rcases D with _ | D
    · simp
    · simp [Nat.testBit_succ]
  | succ t ih =>
    rw [lrow_succ, ldiag_succ]
    simp only [lstep, Nat.testBit_and, Nat.testBit_xor, Nat.testBit_or, Nat.testBit_shiftLeft,
      Nat.testBit_two_pow_sub_one, hD, decide_true, Bool.and_true]
    have h1 : ldiag ((D : ℤ) - 1) t = (decide (D ≥ 1) && (lrow N t).testBit (D - 1)) := by
      rcases D with _ | D
      · simp [ldiag_neg]
      · simp only [ge_iff_le, le_add_iff_nonneg_left, zero_le, decide_true, Bool.true_and,
          Nat.add_sub_cancel]
        rw [ih (by omega)]; push_cast; ring_nf
    have h2 : ldiag ((D : ℤ) - 2) t = (decide (D ≥ 2) && (lrow N t).testBit (D - 2)) := by
      rcases D with _ | _ | D
      · simp [ldiag_neg]
      · simp [ldiag_neg]
      · simp only [ge_iff_le, le_add_iff_nonneg_left, zero_le, decide_true, Bool.true_and]
        rw [ih (by omega)]; push_cast; ring_nf
    rw [h1, h2, ih hD]

/-- **The certificate lemma**: one equality of packed rows gives eventual periodicity of all
the first `N` left diagonals, for every later time. -/
theorem evPer_of_lrow {N s p : ℕ} (h : lrow N (s + p) = lrow N s) :
    ∀ D < N, ∀ t ≥ s, ldiag D (t + p) = ldiag D t := by
  intro D hD t ht
  obtain ⟨n, rfl⟩ := Nat.exists_eq_add_of_le ht
  have : lrow N (s + n + p) = lrow N (s + n) := by
    rw [show s + n + p = (s + p) + n by ring, lrow_add, h, ← lrow_add]
  rw [← testBit_lrow hD, ← testBit_lrow hD, this]

/-- A sequence periodic from `s` that differs from its shift by `q` once after `s` is not
eventually `q`-periodic. -/
theorem not_evPer_of_mismatch {u : ℕ → Bool} {p q s t₀ : ℕ} (hp0 : 0 < p)
    (hp : ∀ t ≥ s, u (t + p) = u t) (ht₀ : s ≤ t₀) (hne : u (t₀ + q) ≠ u t₀) :
    ¬ EvPer u q := by
  rintro ⟨T, hT⟩
  have hk : T ≤ t₀ + T * p := by nlinarith
  have key := hT (t₀ + T * p) hk
  rw [show t₀ + T * p + q = (t₀ + q) + T * p by ring, periodic_mul hp T _ (by omega),
    periodic_mul hp T _ ht₀] at key
  exact hne key

/-! ## Reading whiteness from the packed rows -/

/-- The bitwise `or` of `k` consecutive packed rows, starting from the row `r`. -/
def orRun (m r : ℕ) : ℕ → ℕ
  | 0 => 0
  | k + 1 => r ||| orRun m (lstep m r) k

theorem testBit_orRun (N s k D : ℕ) :
    (orRun (2 ^ N - 1) (lrow N s) k).testBit D = true ↔
      ∃ i < k, (lrow N (s + i)).testBit D = true := by
  induction k generalizing s with
  | zero => simp [orRun]
  | succ k ih =>
    simp only [orRun, Nat.testBit_or, Bool.or_eq_true]
    rw [← lrow_succ, ih]
    constructor
    · rintro (h | ⟨i, hi, h⟩)
      · exact ⟨0, by omega, by simpa using h⟩
      · exact ⟨i + 1, by omega, by rwa [show s + (i + 1) = s + 1 + i by ring]⟩
    · rintro ⟨i, hi, h⟩
      rcases i with _ | i
      · left; simpa using h
      · right; exact ⟨i, by omega, by rwa [show s + 1 + i = s + (i + 1) by ring]⟩

/-- A periodic diagonal whose bit is clear in the `or` of one period is eventually white. -/
theorem white_of_orRun {N s p D : ℕ} (hD : D < N) (hp : 0 < p) (h : lrow N (s + p) = lrow N s)
    (hw : (orRun (2 ^ N - 1) (lrow N s) p).testBit D = false) :
    ∀ t ≥ s, ldiag D t = false := by
  intro t ht
  obtain ⟨n, rfl⟩ := Nat.exists_eq_add_of_le ht
  have hper := evPer_of_lrow h D hD
  have e : ldiag D (s + n) = ldiag D (s + n % p) := by
    conv_lhs => rw [← Nat.mod_add_div n p, ← add_assoc, mul_comm]
    exact periodic_mul hper (n / p) _ (by omega)
  rw [e, ← testBit_lrow hD]
  by_contra hne
  have : (orRun (2 ^ N - 1) (lrow N s) p).testBit D = true :=
    (testBit_orRun N s p D).2 ⟨n % p, Nat.mod_lt _ hp, by simpa using hne⟩
  rw [hw] at this; exact absurd this (by decide)

/-- A periodic diagonal whose bit is set in the `or` of one period is not eventually white. -/
theorem not_white_of_orRun {N s p D : ℕ} (hD : D < N) (h : lrow N (s + p) = lrow N s)
    (hb : (orRun (2 ^ N - 1) (lrow N s) p).testBit D = true) :
    ¬ EventuallyWhite (ldiag D) := by
  obtain ⟨i, hi, hbit⟩ := (testBit_orRun N s p D).1 hb
  rintro ⟨T, hT⟩
  have hp : 0 < p := by omega
  have hper := evPer_of_lrow h D hD
  have := hT (s + i + T * p) (by nlinarith)
  rw [periodic_mul hper T _ (by omega), ← testBit_lrow hD, hbit] at this
  exact absurd this (by decide)

/-! ## Certificates -/

theorem lrow_400_period_8 : lrow 400 (501 + 8) = lrow 400 501 := by native_decide

/-- **CERT.** Every left diagonal `D < 400` has eventual period `8` (from `t = 501`). -/
theorem leftDiag_period_eight_below_400 :
    ∀ D : ℕ, D < 400 → ∀ t ≥ 501, ldiag (D : ℤ) (t + 8) = ldiag (D : ℤ) t :=
  evPer_of_lrow lrow_400_period_8

theorem lrow_401_period_16 : lrow 401 (501 + 16) = lrow 401 501 := by native_decide

theorem lrow_401_bit_400 : (lrow 401 (501 + 8)).testBit 400 ≠ (lrow 401 501).testBit 400 := by
  native_decide

/-- **Refutation.** Left diagonal `400` does not have eventual period `8`. -/
theorem ldiag_400_not_evPer_eight : ¬ EvPer (ldiag 400) 8 := by
  have hne := lrow_401_bit_400
  rw [testBit_lrow (by norm_num), testBit_lrow (by norm_num)] at hne
  exact not_evPer_of_mismatch (p := 16) (s := 501) (by norm_num)
    (evPer_of_lrow lrow_401_period_16 400 (by norm_num)) le_rfl hne

/-- **Refutation of the engine's first generalisation** (`period ≤ 8`, true for `D < 400`). -/
theorem not_leftDiagPeriodDivides_eight : ¬ LeftDiagPeriodDivides 8 :=
  fun h => ldiag_400_not_evPer_eight (h 400)

/-- No left-diagonal period `1, 2, 4` or `8` serves every diagonal. -/
theorem not_leftDiagPeriodDivides_of_dvd_eight {p : ℕ} (hp : p ∣ 8) :
    ¬ LeftDiagPeriodDivides p :=
  fun h => not_leftDiagPeriodDivides_eight (h.of_dvd hp)

theorem orRun_400_bit_399 : (orRun (2 ^ 400 - 1) (lrow 400 501) 8).testBit 399 = false := by
  native_decide

/-- Left diagonal `399` is white from `t = 501` on. -/
theorem leftDiag_399_white : ∀ t ≥ 501, ldiag 399 t = false :=
  white_of_orRun (by norm_num) (by norm_num) lrow_400_period_8 orRun_400_bit_399

theorem parity_398_packed :
    parityOn (fun t => (lrow 400 t).testBit 398) 501 8 = true := by native_decide

/-- Diagonal `398` has odd parity over its period `8`. -/
theorem parity_398 : parityOn (ldiag 398) 501 8 = true := by
  have : (fun t => (lrow 400 t).testBit 398) = ldiag 398 :=
    funext fun t => testBit_lrow (by norm_num) t
  rw [← this]; exact parity_398_packed

/-- **The cause, through the law.**  The doubling at `D = 400` follows from the period law:
diagonal `399` is eventually white and diagonal `398` has odd parity, so `ldiag_doubles` gives
"not period `8`, period `16`" with no further computation on diagonal `400`. -/
theorem ldiag_400_by_law : ¬ EvPer (ldiag 400) 8 ∧ EvPer (ldiag 400) 16 := by
  have h := ldiag_doubles (D := 400) (Q := 8) (T := 501)
    (by
      intro t ht
      have := leftDiag_period_eight_below_400 398 (by norm_num) t ht
      simpa using this)
    (by
      intro t ht
      have := leftDiag_399_white t ht
      simpa using this)
    (by simpa using parity_398)
  simpa using h

theorem lrow_87867_period_16 : lrow 87867 (117324 + 16) = lrow 87867 117324 := by native_decide

/-- **CERT.** Every left diagonal `D < 87867` has eventual period `16` (from `t = 117324`). -/
theorem leftDiag_period_sixteen_below_87867 :
    ∀ D : ℕ, D < 87867 → ∀ t ≥ 117324, ldiag (D : ℤ) (t + 16) = ldiag (D : ℤ) t :=
  evPer_of_lrow lrow_87867_period_16

theorem lrow_87868_period_32 : lrow 87868 (117324 + 32) = lrow 87868 117324 := by native_decide

theorem lrow_87868_mismatch :
    (lrow 87868 (117324 + 16)).testBit 87867 ≠ (lrow 87868 117324).testBit 87867 := by
  native_decide

/-- **Refutation of the engine's second generalisation** (`period ≤ 16`, true for
`D < 87867`): left diagonal `87867` does not have eventual period `16`. -/
theorem ldiag_87867_not_evPer_sixteen : ¬ EvPer (ldiag 87867) 16 := by
  have hne := lrow_87868_mismatch
  rw [testBit_lrow (by norm_num), testBit_lrow (by norm_num)] at hne
  exact not_evPer_of_mismatch (p := 32) (s := 117324) (by norm_num)
    (evPer_of_lrow lrow_87868_period_32 87867 (by norm_num)) le_rfl hne

theorem not_leftDiagPeriodDivides_sixteen : ¬ LeftDiagPeriodDivides 16 :=
  fun h => ldiag_87867_not_evPer_sixteen (h 87867)

/-- The `or` of one period-32 window of the first `87868` diagonals. -/
def whiteWitness : ℕ := orRun (2 ^ 87868 - 1) (lrow 87868 117324) 32

theorem whiteWitness_check :
    (List.range 87868).all (fun D => (!(whiteWitness.testBit D)) ==
      decide (D = 2 ∨ D = 7 ∨ D = 28 ∨ D = 399 ∨ D = 53207 ∨ D = 58286 ∨ D = 87866)) = true := by
  native_decide

/-- **CERT.** The eventually white left diagonals below `87868` are exactly
`2, 7, 28, 399, 53207, 58286, 87866`. -/
theorem leftDiag_white_below_87868 (D : ℕ) (hD : D < 87868) :
    EventuallyWhite (ldiag D) ↔
      D = 2 ∨ D = 7 ∨ D = 28 ∨ D = 399 ∨ D = 53207 ∨ D = 58286 ∨ D = 87866 := by
  have hc := List.all_eq_true.1 whiteWitness_check D (List.mem_range.2 hD)
  simp only [beq_iff_eq] at hc
  constructor
  · intro hw
    by_contra hne
    rw [← decide_eq_true_iff (p := ¬ _)] at hne
    have hb : whiteWitness.testBit D = true := by
      cases hbit : whiteWitness.testBit D
      · rw [hbit] at hc; simp at hc; exact absurd hc (by simpa using hne)
      · rfl
    exact not_white_of_orRun hD lrow_87868_period_32 hb hw
  · intro hmem
    have hb : whiteWitness.testBit D = false := by
      cases hbit : whiteWitness.testBit D
      · rfl
      · rw [hbit] at hc; simp at hc; exact absurd hmem (by push_neg; exact hc)
    exact ⟨117324, white_of_orRun hD (by norm_num) lrow_87868_period_32 hb⟩

theorem leftEdgeAtZero_seed : LeftEdgeAtZero seed :=
  ⟨fun j hj => by simp [seed]; omega, by simp [seed]⟩

/-- **Where any left-edge row can first differ from the seed.**  For every row white on
`(-∞, 0)` and black at `0`, the first left diagonal below `87868` whose eventual behaviour differs
from the single black cell's is one of `3, 8, 29, 400, 53208, 58287, 87867` — one past an
eventually white diagonal of the seed. -/
theorem seed_first_difference {y : Config} (hy : LeftEdgeAtZero y) {D : ℕ} (hD : D < 87868)
    (hbelow : ∀ D' : ℕ, D' < D → EventuallyEq (ldiag D') (ldiagOf y D'))
    (hne : ¬ EventuallyEq (ldiag D) (ldiagOf y D)) :
    D = 3 ∨ D = 8 ∨ D = 29 ∨ D = 400 ∨ D = 53208 ∨ D = 58287 ∨ D = 87867 := by
  obtain ⟨h2, hw⟩ := first_difference_after_white (x := seed) leftEdgeAtZero_seed hy
    (D := D) hbelow hne
  have e1 : ((D : ℤ) - 1) = ((D - 1 : ℕ) : ℤ) := by omega
  rw [ldiagOf_seed, e1] at hw
  have := (leftDiag_white_below_87868 (D - 1) (by omega)).1 hw
  omega

/-! ## The centre column reads the left diagonals inside their transients (engine survivor)

The engine's lift "for `D ≥ 20` the transient of left diagonal `D` is longer than `D`" (C133 had
it for `D ≤ 200`) survived every held-out range.  Since the centre column reads diagonal `D` at
time `D` (`centerCol_eq_ldiag`), it says that the centre column never reads a settled left
diagonal.  Here it is certified for `20 ≤ D < 20000`. -/

/-- Tail-recursive scan: `or` of `(row t xor row (t + 16))` restricted to the bits `≤ t`. -/
def transLoop (m : ℕ) : ℕ → ℕ → ℕ → ℕ → ℕ → ℕ
  | acc, _, _, _, 0 => acc
  | acc, r, r', t, k + 1 =>
      transLoop m (acc ||| ((r ^^^ r') &&& (2 ^ (t + 1) - 1))) (lstep m r) (lstep m r') (t + 1) k

theorem testBit_transLoop (N D : ℕ) :
    ∀ k acc t, (transLoop (2 ^ N - 1) acc (lrow N t) (lrow N (t + 16)) t k).testBit D = true ↔
      (acc.testBit D = true ∨ ∃ i < k, D ≤ t + i ∧
        (lrow N (t + i)).testBit D ≠ (lrow N (t + i + 16)).testBit D) := by
  intro k
  induction k with
  | zero => intro acc t; simp [transLoop]
  | succ k ih =>
    intro acc t
    simp only [transLoop]
    rw [← lrow_succ, ← lrow_succ, show t + 16 + 1 = t + 1 + 16 by ring, ih]
    simp only [Nat.testBit_or, Nat.testBit_and, Nat.testBit_xor, Nat.testBit_two_pow_sub_one,
      Bool.or_eq_true, Bool.and_eq_true, decide_eq_true_eq]
    constructor
    · rintro ((h | ⟨h1, h2⟩) | ⟨i, hi, hD, hne⟩)
      · exact Or.inl h
      · right; refine ⟨0, by omega, by omega, ?_⟩
        revert h1
        cases ha : (lrow N t).testBit D <;> cases hb : (lrow N (t + 16)).testBit D <;> simp_all
      · right; exact ⟨i + 1, by omega, by omega, by
          rwa [show t + (i + 1) = t + 1 + i by ring]⟩
    · rintro (h | ⟨i, hi, hD, hne⟩)
      · exact Or.inl (Or.inl h)
      · rcases i with _ | i
        · left; right
          refine ⟨?_, by omega⟩
          revert hne
          simp only [Nat.add_zero]
          cases ha : (lrow N t).testBit D <;> cases hb : (lrow N (t + 16)).testBit D <;> simp_all
        · right; exact ⟨i, by omega, by omega, by
            rwa [show t + 1 + i = t + (i + 1) by ring]⟩

/-- The scanned witness for the first `20000` diagonals over the times `t < 26834`. -/
def transientWitness : ℕ := transLoop (2 ^ 20000 - 1) 0 (lrow 20000 0) (lrow 20000 16) 0 26834

theorem transientWitness_check :
    (List.range 20000).all (fun D => decide (D < 20) || transientWitness.testBit D) = true := by
  native_decide

/-- **CERT.** For `20 ≤ D < 20000`, left diagonal `D` is still in its transient at time `D`:
it fails the period `16` at some time `t ≥ D`.  Since every left diagonal `D < 87867` is
eventually `16`-periodic, this says its preperiod exceeds `D`. -/
theorem leftDiag_transient_at_read {D : ℕ} (h20 : 20 ≤ D) (hD : D < 20000) :
    ∃ t ≥ D, ldiag D (t + 16) ≠ ldiag D t := by
  have hc := List.all_eq_true.1 transientWitness_check D (List.mem_range.2 hD)
  have hb : transientWitness.testBit D = true := by
    simpa [show ¬ D < 20 by omega] using hc
  obtain h | ⟨i, -, hle, hne⟩ := (testBit_transLoop 20000 D 26834 0 0).1 hb
  · simp at h
  · refine ⟨i, by omega, ?_⟩
    rw [← testBit_lrow hD, ← testBit_lrow hD]
    simpa [eq_comm] using hne

/-- **The centre column is read inside the transient** (CERT, `20 ≤ t < 20000`): the bit
`a(t) = ldiag t t` is read before left diagonal `t` has become periodic. -/
theorem centerCol_read_in_transient {t : ℕ} (h20 : 20 ≤ t) (ht : t < 20000) :
    centerCol t = ldiag t t ∧ ∃ t' ≥ t, ldiag t (t' + 16) ≠ ldiag t t' :=
  ⟨centerCol_eq_ldiag t, leftDiag_transient_at_read h20 ht⟩

end GLM.Rule30
