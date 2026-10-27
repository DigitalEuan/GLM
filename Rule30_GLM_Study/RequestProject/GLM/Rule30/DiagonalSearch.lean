module

public import RequestProject.GLM.Rule30.PrefixSearch

/-!
# Round 35: the diagonal search — a faster verified checker (To Do 37)

The prefix search of `PrefixSearch.lean` re-simulates the machine from time `0` at every node of
the search tree: a prefix of length `k` costs `k` machine steps.  By the light cone
(`halfStateD_testBit_congr`) the bit `k` of the code enters the space-time picture along one
**anti-diagonal** only: the cells `(t, k - t)`, `t ≤ k` (cell `i` at time `t`).  So, walking down
the tree, it suffices to compute one new diagonal per node from the two previous ones.

Write `cell S t i` for bit `i` of the state at time `t`.  Rule 30 on the half-line gives, for
`t < k`,

  `cell S (t+1) (k-t-1) = cell S t (k-t) xor (cell S t (k-1-t) or cell S t (k-2-t))`,

with the drive bit `bd t` in place of the last cell when `k - 1 - t = 0`.  Along the new diagonal
this is a **prefix xor**: the new diagonal is the running xor of `(old diagonals) <<< 1`, seeded
with the new code bit.  A prefix xor of a bit vector takes `⌈log₂ k⌉` shift-xor rounds
(`pxor`), so a node costs a handful of word operations instead of `k` machine steps.

* `pxor j sh X` — `j` rounds of `X ↦ X xor (X <<< sh)`, doubling `sh`; with `sh = 1` its bit `t`
  is the xor of the bits `≤ t` of `X` whenever `t < 2^j` (`testBit_pxor_succ`, `testBit_pxor_zero`).
* `nextDiag bd k D1 D2 s` — the diagonal `k` from the diagonals `k - 1` (`D1`) and `k - 2` (`D2`)
  and the new code bit `s`; **`nextDiag_spec`**: it is exact.
* `diagSearch bd T n k P D1 D2` — the search tree of `prefixSearch`, with the check at time `k`
  read off the new diagonal; at the leaves the complete code is simulated as before.
* **`diagSearch_sound`**, **`dDiesBy_of_diagSearch`** — soundness: a successful search kills every
  code of length `d` before `T`.
* `diagCheck p d T` and **`drivenCheck_of_diagCheck`**, **`halfLineLinear_upTo_of_diagCheck`** — the
  drop-in replacements of the Round 22 checks.

The certificates that use it are in `DiagonalSearchData.lean`.
-/

@[expose] public section

namespace GLM.Rule30

/-! ## Prefix xor in logarithmically many rounds -/

/-- `j` rounds of `X ↦ X xor (X <<< sh)`, doubling the shift each round. -/
def pxor : ℕ → ℕ → ℕ → ℕ
  | 0, _, X => X
  | j + 1, sh, X => pxor j (2 * sh) (X ^^^ (X <<< sh))

/-- The xor of the window `X t, X (t-1), …, X (t-a+1)` (stopping at bit `0`). -/
def winXor (X : ℕ) : ℕ → ℕ → Bool
  | 0, _ => false
  | a + 1, t => xor (winXor X a t) (decide (a ≤ t) && X.testBit (t - a))

theorem winXor_add (X a : ℕ) : ∀ b t,
    winXor X (a + b) t = xor (winXor X a t) (decide (a ≤ t) && winXor X b (t - a)) := by
  intro b
  induction b with
  | zero => intro t; simp [winXor]
  | succ b ih =>
    intro t
    rw [show a + (b + 1) = (a + b) + 1 by ring, winXor, ih, winXor]
    by_cases hat : a ≤ t
    · have e : t - (a + b) = t - a - b := by omega
      by_cases hb : b ≤ t - a
      · simp [hat, hb, show a + b ≤ t by omega, e]
      · simp [hat, hb, show ¬ a + b ≤ t by omega]
    · simp [hat, show ¬ a + b ≤ t by omega]

/-- One shift-xor round doubles the window. -/
theorem testBit_xor_shift_window (X Y a : ℕ) (hY : ∀ t, Y.testBit t = winXor X a t) (t : ℕ) :
    (Y ^^^ (Y <<< a)).testBit t = winXor X (a + a) t := by
  rw [Nat.testBit_xor, Nat.testBit_shiftLeft, winXor_add, hY]
  by_cases h : a ≤ t
  · simp [h, hY]
  · simp [h]

theorem testBit_pxor_window (X : ℕ) : ∀ j sh Y, (∀ t, Y.testBit t = winXor X sh t) →
    ∀ t, (pxor j sh Y).testBit t = winXor X (sh * 2 ^ j) t := by
  intro j
  induction j with
  | zero => intro sh Y hY t; simpa [pxor] using hY t
  | succ j ih =>
    intro sh Y hY t
    rw [pxor, ih (2 * sh) _ (fun t => by rw [testBit_xor_shift_window X Y sh hY]; congr 1; ring)]
    congr 1
    ring

theorem winXor_one (X t : ℕ) : winXor X 1 t = X.testBit t := by simp [winXor]

/-- A window longer than `t + 1` reaches bit `0`: extending it changes nothing. -/
theorem winXor_succ_of_gt (X a t : ℕ) (h : t < a) : winXor X (a + 1) t = winXor X a t := by
  simp [winXor, show ¬ a ≤ t by omega]

theorem winXor_succ_index (X : ℕ) : ∀ a t, t + 1 < a →
    winXor X a (t + 1) = xor (winXor X a t) (X.testBit (t + 1)) := by
  intro a t h
  obtain ⟨b, rfl⟩ : ∃ b, a = 1 + b := ⟨a - 1, by omega⟩
  rw [winXor_add, winXor_one]
  simp only [show 1 ≤ t + 1 by omega, decide_true, Bool.true_and, Nat.add_sub_cancel]
  have : winXor X (1 + b) t = winXor X b t := by
    rw [add_comm]; exact winXor_succ_of_gt X b t (by omega)
  rw [this, Bool.xor_comm]

theorem winXor_zero_index (X a : ℕ) (h : 0 < a) : winXor X a 0 = X.testBit 0 := by
  obtain ⟨b, rfl⟩ : ∃ b, a = b + 1 := ⟨a - 1, by omega⟩
  induction b with
  | zero => exact winXor_one X 0
  | succ b ih => rw [winXor_succ_of_gt X _ 0 (by omega), ih (by omega)]

/-- **Prefix xor, bit `0`.** -/
theorem testBit_pxor_zero (j X : ℕ) : (pxor j 1 X).testBit 0 = X.testBit 0 := by
  rw [testBit_pxor_window X j 1 X (fun t => (winXor_one X t).symm), one_mul]
  exact winXor_zero_index X _ (Nat.two_pow_pos j)

/-- **Prefix xor, next bit.** For `t + 1 < 2^j`, bit `t + 1` of the prefix xor is bit `t` xor
bit `t + 1` of the input. -/
theorem testBit_pxor_succ (j X t : ℕ) (ht : t + 1 < 2 ^ j) :
    (pxor j 1 X).testBit (t + 1) = xor ((pxor j 1 X).testBit t) (X.testBit (t + 1)) := by
  have hw := testBit_pxor_window X j 1 X (fun t => (winXor_one X t).symm)
  rw [hw, hw, one_mul]
  exact winXor_succ_index X _ t ht

/-! ## One diagonal from the two before -/

/-- Bit `i` of the machine state at time `t`. -/
abbrev cellD (bd : ℕ → Bool) (S t i : ℕ) : Bool := (halfStateD bd S t).testBit i

/-- The diagonal `k` (cells `(t, k - t)`, `t ≤ k`) from the diagonals `k - 1` and `k - 2` and the
new code bit `s`. -/
def nextDiag (bd : ℕ → Bool) (k D1 D2 : ℕ) (s : Bool) : ℕ :=
  let E := if k = 0 then 0 else D2 ||| ((bd (k - 1)).toNat <<< (k - 1))
  pxor (Nat.log2 k + 1) 1 (((D1 ||| E) <<< 1) ||| s.toNat) % 2 ^ (k + 1)

/-- The two diagonals carried by the search, for a code `S` at depth `k`. -/
def DiagInv (bd : ℕ → Bool) (S k D1 D2 : ℕ) : Prop :=
  (∀ t, D1.testBit t = (decide (t + 1 ≤ k) && cellD bd S t (k - 1 - t))) ∧
  (∀ t, D2.testBit t = (decide (t + 2 ≤ k) && cellD bd S t (k - 2 - t)))

theorem testBit_toNat_shift (b : Bool) (m t : ℕ) :
    ((b.toNat) <<< m).testBit t = (decide (t = m) && b) := by
  cases b <;> simp [Nat.one_shiftLeft, Nat.testBit_two_pow, eq_comm]

/-- **The new diagonal is exact.** -/
theorem nextDiag_spec (bd : ℕ → Bool) {S k D1 D2 : ℕ} (h : DiagInv bd S k D1 D2) :
    ∀ t, (nextDiag bd k D1 D2 (S.testBit k)).testBit t =
      (decide (t ≤ k) && cellD bd S t (k - t)) := by
  obtain ⟨h1, h2⟩ := h
  set E := if k = 0 then 0 else D2 ||| ((bd (k - 1)).toNat <<< (k - 1)) with hE
  set X := ((D1 ||| E) <<< 1) ||| (S.testBit k).toNat with hX
  have hlt : k < 2 ^ (Nat.log2 k + 1) := Nat.lt_log2_self
  -- the input bits
  have hX0 : X.testBit 0 = S.testBit k := by
    simp only [hX, Nat.testBit_or, Nat.testBit_shiftLeft]
    cases S.testBit k <;> simp
  have hXs : ∀ t, t < k → X.testBit (t + 1) =
      (cellD bd S t (k - 1 - t) || (if k - 1 - t = 0 then bd t else cellD bd S t (k - 2 - t))) := by
    intro t ht
    have hb : (S.testBit k).toNat.testBit (t + 1) = false := by
      cases S.testBit k <;> simp [Nat.testBit_succ]
    simp only [hX, Nat.testBit_or, Nat.testBit_shiftLeft, hb, Bool.or_false,
      show 1 ≤ t + 1 by omega, decide_true, Bool.true_and, Nat.add_sub_cancel, h1,
      show t + 1 ≤ k from ht, Bool.true_and]
    have hk0 : k ≠ 0 := by omega
    simp only [hE, if_neg hk0, Nat.testBit_or, testBit_toNat_shift, h2]
    by_cases hkt : k - 1 - t = 0
    · have : t = k - 1 := by omega
      subst this
      simp [show ¬ k - 1 + 2 ≤ k by omega]
    · simp only [if_neg hkt, show t + 2 ≤ k by omega, decide_true, Bool.true_and,
        show ¬ t = k - 1 by omega, decide_false, Bool.false_and, Bool.or_false]
  intro t
  simp only [nextDiag, ← hE, ← hX, Nat.testBit_mod_two_pow]
  by_cases htk : t ≤ k
  · simp only [show t < k + 1 by omega, decide_true, Bool.true_and, htk]
    induction t with
    | zero =>
      rw [testBit_pxor_zero, hX0]
      rfl
    | succ t ih =>
      rw [testBit_pxor_succ _ _ _ (by omega), ih (by omega), hXs t (by omega)]
      simp only [cellD, halfStateD, testBit_halfStep]
      rw [show k - (t + 1) + 1 = k - t by omega, show k - (t + 1) - 1 = k - 2 - t by omega,
        show k - (t + 1) = k - 1 - t by omega]
  · simp [htk, show ¬ t < k + 1 by omega]

/-- Shifting the invariant one level down. -/
theorem diagInv_succ (bd : ℕ → Bool) {S k D1 D2 : ℕ} (h : DiagInv bd S k D1 D2) :
    DiagInv bd S (k + 1) (nextDiag bd k D1 D2 (S.testBit k)) D1 := by
  refine ⟨fun t => ?_, fun t => ?_⟩
  · rw [nextDiag_spec bd h]
    congr 2
    simp
  · rw [h.1 t]
    congr 2
    simp

theorem diagInv_zero (bd : ℕ → Bool) (S : ℕ) : DiagInv bd S 0 0 0 :=
  ⟨fun t => by simp, fun t => by simp⟩

/-! ## The diagonal search -/

/-- The tail of the diagonal search: all remaining code bits are `0`; walk down the diagonals
until a check fails (or the fuel runs out). -/
def diagTail (bd : ℕ → Bool) (T : ℕ) : ℕ → ℕ → ℕ → ℕ → Bool
  | 0, _, _, _ => false
  | f + 1, k, D1, D2 =>
    let D := nextDiag bd k D1 D2 false
    (decide (k < T) && bd k && (D.testBit k == bd (k + 1))) || diagTail bd T f (k + 1) D D1

/-- The diagonal search: the tree of `prefixSearch`, with the check at time `k` read off the new
diagonal `k` instead of a re-simulation.  `D1`, `D2` are the diagonals `k - 1` and `k - 2` (they
determine everything the checks before time `k` can see); at `n = 0` the top bit `k` is set and the tail of zero bits is walked by
`diagTail` up to time `T`. -/
def diagSearch (bd : ℕ → Bool) (T : ℕ) : ℕ → ℕ → ℕ → ℕ → Bool
  | 0, k, D1, D2 =>
    let D := nextDiag bd k D1 D2 true
    (decide (k < T) && bd k && (D.testBit k == bd (k + 1))) || diagTail bd T T (k + 1) D D1
  | n + 1, k, D1, D2 =>
    let D0 := nextDiag bd k D1 D2 false
    let D1' := nextDiag bd k D1 D2 true
    ((decide (k < T) && bd k && (D0.testBit k == bd (k + 1))) ||
        diagSearch bd T n (k + 1) D0 D1) &&
      ((decide (k < T) && bd k && (D1'.testBit k == bd (k + 1))) ||
        diagSearch bd T n (k + 1) D1' D1)

/-- A failed check read off a diagonal is a failure of the machine. -/
theorem dDiesBy_of_diag_check (bd : ℕ → Bool) {S k D1 D2 T : ℕ} (hinv : DiagInv bd S k D1 D2)
    (hkT : k < T) (hb : bd k = true)
    (hc : (nextDiag bd k D1 D2 (S.testBit k)).testBit k = bd (k + 1)) :
    dDiesBy bd S T = true := by
  rw [dDiesBy_spec]
  refine ⟨k, hkT, hb, ?_⟩
  rw [nextDiag_spec bd hinv k] at hc
  simpa using hc

/-- **Soundness of the tail.** -/
theorem diagTail_sound (bd : ℕ → Bool) (T : ℕ) :
    ∀ f k D1 D2, diagTail bd T f k D1 D2 = true →
      ∀ S, DiagInv bd S k D1 D2 → (∀ i, k ≤ i → S.testBit i = false) →
        dDiesBy bd S T = true := by
  intro f
  induction f with
  | zero => intro k D1 D2 h; simp [diagTail] at h
  | succ f ih =>
    intro k D1 D2 h S hinv hz
    simp only [diagTail, Bool.or_eq_true, Bool.and_eq_true, beq_iff_eq,
      decide_eq_true_eq] at h
    have hk := hz k le_rfl
    rcases h with ⟨⟨hkT, hb⟩, hc⟩ | hr
    · exact dDiesBy_of_diag_check bd hinv hkT hb (by rw [hk]; exact hc)
    · have hinv' := diagInv_succ bd hinv
      rw [hk] at hinv'
      exact ih (k + 1) _ D1 hr S hinv' fun i hi => hz i (by omega)

/-- **Soundness of the diagonal search.** -/
theorem diagSearch_sound (bd : ℕ → Bool) (T : ℕ) :
    ∀ n k D1 D2, diagSearch bd T n k D1 D2 = true →
      ∀ S, DiagInv bd S k D1 D2 → 2 ^ (k + n) ≤ S → S < 2 ^ (k + n + 1) →
        dDiesBy bd S T = true := by
  intro n
  induction n with
  | zero =>
    intro k D1 D2 h S hinv h1 h2
    simp only [diagSearch, Bool.or_eq_true, Bool.and_eq_true, beq_iff_eq,
      decide_eq_true_eq] at h
    simp only [add_zero] at h1 h2
    have hk : S.testBit k = true := by
      rw [Nat.testBit_eq_decide_div_mod_eq]
      have : S / 2 ^ k = 1 := by
        apply Nat.div_eq_of_lt_le
        · simpa using h1
        · rw [pow_succ] at h2; omega
      simp [this]
    rcases h with ⟨⟨hkT, hb⟩, hc⟩ | hr
    · exact dDiesBy_of_diag_check bd hinv hkT hb (by rw [hk]; exact hc)
    · have hinv' := diagInv_succ bd hinv
      rw [hk] at hinv'
      refine diagTail_sound bd T T (k + 1) _ D1 hr S hinv' fun i hi => ?_
      exact Nat.testBit_lt_two_pow (lt_of_lt_of_le h2 (Nat.pow_le_pow_right (by norm_num) hi))
  | succ n ih =>
    intro k D1 D2 h S hinv h1 h2
    simp only [diagSearch, Bool.and_eq_true, Bool.or_eq_true, beq_iff_eq,
      decide_eq_true_eq] at h
    obtain ⟨hA, hB⟩ := h
    have e1 : k + 1 + n = k + (n + 1) := by ring
    -- the branch actually taken by `S`
    have key : ∀ s : Bool, S.testBit k = s →
        ((k < T ∧ bd k = true) ∧ (nextDiag bd k D1 D2 s).testBit k = bd (k + 1) ∨
          diagSearch bd T n (k + 1) (nextDiag bd k D1 D2 s) D1 = true) →
        dDiesBy bd S T = true := by
      intro s hs hbr
      have hinv' := diagInv_succ bd hinv
      rw [hs] at hinv'
      rcases hbr with ⟨⟨hkT, hb⟩, hc⟩ | hr
      · exact dDiesBy_of_diag_check bd hinv hkT hb (by rw [hs]; exact hc)
      · exact ih (k + 1) _ D1 hr S hinv' (by rw [e1]; exact h1) (by rw [e1]; exact h2)
    cases hs : S.testBit k
    · exact key false hs hA
    · exact key true hs hB

/-- Every code of length `d ≥ 1` fails before `T` if the diagonal search from the root succeeds. -/
theorem dDiesBy_of_diagSearch {bd : ℕ → Bool} {T d S : ℕ} (hd : 1 ≤ d)
    (h : diagSearch bd T (d - 1) 0 0 0 = true) (h1 : 2 ^ (d - 1) ≤ S) (h2 : S < 2 ^ d) :
    dDiesBy bd S T = true :=
  diagSearch_sound bd T (d - 1) 0 0 0 h S (diagInv_zero bd S)
    (by simpa using h1) (by rw [show 0 + (d - 1) + 1 = d by omega]; exact h2)

/-- The diagonal check for period `p`, distance `d`, horizon `T`. -/
def diagCheck (p d T : ℕ) : Bool :=
  (List.range (2 ^ p - 1)).all fun j => diagSearch (driveN p (j + 1)) T (d - 1) 0 0 0

/-- **The diagonal check implies the full Round 21 check.** -/
theorem drivenCheck_of_diagCheck {p d T : ℕ} (hd : 1 ≤ d) (h : diagCheck p d T = true) :
    drivenCheck p d T = true := by
  unfold diagCheck at h
  unfold drivenCheck
  rw [List.all_eq_true] at h ⊢
  intro j hj
  rw [List.all_eq_true]
  intro k hk
  rw [List.mem_range] at hk
  have hd' : 2 ^ d = 2 ^ (d - 1) + 2 ^ (d - 1) := by
    rw [← two_mul, ← pow_succ']; congr 1; omega
  exact dDiesBy_of_diagSearch hd (h j hj) (by omega) (by omega)

/-- Diagonal checks give the linear target on a range of `d`. -/
theorem halfLineLinear_upTo_of_diagCheck {p a b D : ℕ}
    (h : ∀ d ≤ D, 1 ≤ d → diagCheck p d (a * d + b) = true) :
    ∀ k, 0 < k → k < 2 ^ p → ∀ d S : ℕ, d ≤ D → 1 ≤ d → 2 ^ (d - 1) ≤ S → S < 2 ^ d →
      dDiesBy (driveN p k) S (a * d + b) = true := by
  intro k hk0 hk d S hd hd1 h1 h2
  have hc := h d hd hd1
  unfold diagCheck at hc
  rw [List.all_eq_true] at hc
  have := hc (k - 1) (List.mem_range.2 (by omega))
  rw [show k - 1 + 1 = k by omega] at this
  exact dDiesBy_of_diagSearch hd1 this h1 h2

end GLM.Rule30
