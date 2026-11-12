module

public import RequestProject.GLM.Rule30.TuningByEar

/-!
# Round 26: the tuning excess is the longest echo

Round 25 measured how far the best periodic tune runs ahead of what it memorises: the
*excess* `n − tuneCost s n`.  This file identifies it exactly with a classical, cheap quantity.

* `Echo s n k` — the last `k` notes of the first `n` already occurred `p ≥ 1` places earlier
  (an *echo* of length `k`).
* **`costFits_iff_echo`** — a tune of size `n − k` fits the first `n` notes iff there is an echo of
  length `k` (the tune *is* the echo: transient `n − k − p`, period `p`).
* **`excess_le_iff_not_echo`** — `n ≤ tuneCost s n + e` iff there is **no echo of length `e + 1`**.
  So the excess after `n` notes is exactly the length of the longest suffix of the first `n` notes
  that occurred before.
* `tuneExcessBound_iff_noEcho` — the open target `TuneExcessBound g` is "no echo longer than
  `g n` ends at any `n`".
* `excess_succ_le` — the excess grows by at most one per note (`Echo.pred`).
* The narrowing family of Round 26: **`EchoLogBound a b`** (`excess ≤ a·log₂ n + b`), graded in
  both parameters (`echoLogBound_mono`), with `TuneExcessLog = EchoLogBound 2 2`
  (`tuneExcessLog_iff`).  **Every member implies Problem 1** (`problem1_of_echoLogBound`).

For a random binary sequence the longest echo in the first `n` bits is about `2 log₂ n`, so the
slope `a = 2` is the natural frontier; the certificates and the narrowed frontier are in
`ConjectureLoopData.lean`.  All results here use only the standard axioms.
-/

@[expose] public section

namespace GLM.Rule30

/-- **An echo of length `k` at `n`**: the last `k` of the first `n` notes occurred `p ≥ 1`
places earlier. -/
def Echo (s : ℕ → Bool) (n k : ℕ) : Prop :=
  ∃ p, 0 < p ∧ k + p ≤ n ∧ ∀ j < k, s (n - k - p + j) = s (n - k + j)

/-- **The tune is the echo.** A periodic tune of size `n − k` fits the first `n` notes iff the
last `k` notes are an echo. -/
theorem costFits_iff_echo (s : ℕ → Bool) {n k : ℕ} (hk : k < n) :
    CostFits s n (n - k) ↔ Echo s n k := by
  constructor
  · rintro ⟨τ, hτ, hf⟩
    refine ⟨n - k - τ, by omega, by omega, fun j hj => ?_⟩
    have := hf (τ + j) (by omega) (by omega) (by omega)
    rw [show n - k - (n - k - τ) + j = τ + j by omega]
    rw [show τ + j + (n - k - τ) = n - k + j by omega] at this
    exact this.symm
  · rintro ⟨p, hp, hkp, he⟩
    refine ⟨n - k - p, by omega, fun i hi hτi hip => ?_⟩
    rw [show n - k - (n - k - p) = p by omega]
    have := he (i - (n - k - p)) (by omega)
    rw [show n - k - p + (i - (n - k - p)) = i by omega,
      show n - k + (i - (n - k - p)) = i + p by omega] at this
    exact this.symm

/-- A tune that fits with size `c` also fits with size `c + 1` (one more transient note). -/
theorem costFits_succ_of {s : ℕ → Bool} {n c : ℕ} (h : CostFits s n c) : CostFits s n (c + 1) := by
  obtain ⟨τ, hτ, hf⟩ := h
  refine ⟨τ + 1, by omega, fun i hi hτi hip => ?_⟩
  rw [show c + 1 - (τ + 1) = c - τ by omega] at hip ⊢
  exact hf i hi (by omega) hip

theorem costFits_of_le {s : ℕ → Bool} {n c c' : ℕ} (h : CostFits s n c) (hc : c ≤ c') :
    CostFits s n c' := by
  obtain ⟨d, rfl⟩ := Nat.exists_eq_add_of_le hc
  induction d with
  | zero => simpa using h
  | succ d ih => exact costFits_succ_of (ih (by omega))

theorem tuneCost_le_iff (s : ℕ → Bool) (n c : ℕ) : tuneCost s n ≤ c ↔ CostFits s n c :=
  ⟨fun h => costFits_of_le (tuneCost_spec s n) h, fun h => Nat.find_min' _ h⟩

theorem not_costFits_zero (s : ℕ → Bool) (n : ℕ) : ¬ CostFits s n 0 := by
  rintro ⟨τ, hτ, -⟩; omega

/-- **The excess is the longest echo.** `n ≤ tuneCost s n + e` holds iff no echo of length
`e + 1` ends at `n`. -/
theorem excess_le_iff_not_echo (s : ℕ → Bool) (n e : ℕ) :
    n ≤ tuneCost s n + e ↔ ¬ Echo s n (e + 1) := by
  rcases Nat.lt_or_ge (e + 1) n with h | h
  · rw [← costFits_iff_echo s h, ← tuneCost_le_iff]
    omega
  · constructor
    · rintro - ⟨p, hp, hkp, -⟩; omega
    · intro _
      rcases Nat.lt_or_ge n (e + 1) with h' | h'
      · omega
      · have : 1 ≤ tuneCost s n := by
          by_contra h0
          exact not_costFits_zero s n (by
            have := tuneCost_spec s n; rwa [show tuneCost s n = 0 by omega] at this)
        omega

/-- The open target `TuneExcessBound g`, as a statement about echoes of the centre column. -/
theorem tuneExcessBound_iff_noEcho (g : ℕ → ℕ) :
    TuneExcessBound g ↔ ∀ n, ¬ Echo centerCol n (g n + 1) :=
  forall_congr' fun n => excess_le_iff_not_echo centerCol n (g n)

/-! ## The logarithmic family -/

/-- **The narrowing family**: the excess (longest echo) after `n` notes is at most
`a · log₂ n + b`. -/
def EchoLogBound (a b : ℕ) : Prop := TuneExcessBound (fun n => a * Nat.log 2 n + b)

/-- The family is graded: larger slope or offset is a weaker statement. -/
theorem echoLogBound_mono {a b a' b' : ℕ} (ha : a ≤ a') (hb : b ≤ b') (h : EchoLogBound a b) :
    EchoLogBound a' b' := fun n => by
  have := h n
  have : a * Nat.log 2 n ≤ a' * Nat.log 2 n := Nat.mul_le_mul_right _ ha
  dsimp only at *
  omega

/-- Round 25's target is the member `(a, b) = (2, 2)`. -/
theorem tuneExcessLog_iff : TuneExcessLog ↔ EchoLogBound 2 2 := Iff.rfl

theorem five_sq_lt_sixteen_pow (K : ℕ) (hK : 1 ≤ K) : 5 * K ^ 2 < 16 ^ K := by
  induction K with
  | zero => omega
  | succ K ih =>
    rcases Nat.eq_zero_or_pos K with rfl | hK0
    · norm_num
    · have := ih hK0
      rw [pow_succ (16 : ℕ) K]
      nlinarith [sq_nonneg (K - 1 : ℕ), Nat.mul_le_mul hK0 hK0]

/-- Every logarithmic bound is sublinear. -/
theorem logLinear_sublinear (a b : ℕ) : ∀ B, ∃ n, (a * Nat.log 2 n + b) + B < n := by
  intro B
  set K := a + b + B + 1
  refine ⟨2 ^ (4 * K), ?_⟩
  rw [Nat.log_pow (by norm_num)]
  have h1 : 5 * K ^ 2 < 16 ^ K := five_sq_lt_sixteen_pow K (by omega)
  have h2 : (2 : ℕ) ^ (4 * K) = 16 ^ K := by rw [pow_mul]; norm_num
  rw [h2]
  have : a * (4 * K) + b + B ≤ 5 * K ^ 2 := by
    have ha : a ≤ K := by omega
    have hb : b + B ≤ K := by omega
    have : a * (4 * K) ≤ K * (4 * K) := Nat.mul_le_mul_right _ ha
    nlinarith
  omega

/-- **Every member of the family implies Problem 1.** -/
theorem problem1_of_echoLogBound {a b : ℕ} (h : EchoLogBound a b) : Problem1 :=
  problem1_of_tuneExcessBound (logLinear_sublinear a b) h

/-- Dropping the last note shortens an echo by one. -/
theorem Echo.pred {s : ℕ → Bool} {n k : ℕ} (h : Echo s (n + 1) (k + 1)) : Echo s n k := by
  obtain ⟨p, hp, hkp, he⟩ := h
  refine ⟨p, hp, by omega, fun j hj => ?_⟩
  have := he j (by omega)
  rwa [show n + 1 - (k + 1) - p + j = n - k - p + j by omega,
    show n + 1 - (k + 1) + j = n - k + j by omega] at this

/-- **The excess grows by at most one per note** (a structural lemma proposed by the loop and
proved outright): if the excess after `n` notes is at most `e`, after `n + 1` notes it is at most
`e + 1`. -/
theorem excess_succ_le {s : ℕ → Bool} {n e : ℕ} (h : n ≤ tuneCost s n + e) :
    n + 1 ≤ tuneCost s (n + 1) + (e + 1) := by
  rw [excess_le_iff_not_echo] at *
  exact fun he => h he.pred

/-! ## Certificates by sorting: no repeated block -/

/-- An echo stays an echo when shortened. -/
theorem Echo.of_le {s : ℕ → Bool} {n k k' : ℕ} (h : Echo s n k') (hk : k ≤ k') : Echo s n k := by
  obtain ⟨p, hp, hkp, he⟩ := h
  refine ⟨p, hp, by omega, fun j hj => ?_⟩
  have := he (j + (k' - k)) (by omega)
  rw [show n - k' - p + (j + (k' - k)) = n - k - p + j by omega,
    show n - k' + (j + (k' - k)) = n - k + j by omega] at this
  exact this

/-- Echoes only read the first `n` notes. -/
theorem echo_congr {s s' : ℕ → Bool} {n k : ℕ} (hag : ∀ i < n, s i = s' i) :
    Echo s n k ↔ Echo s' n k := by
  constructor <;> rintro ⟨p, hp, hkp, he⟩ <;> refine ⟨p, hp, hkp, fun j hj => ?_⟩
  · rw [← hag _ (by omega), ← hag _ (by omega)]; exact he j hj
  · rw [hag _ (by omega), hag _ (by omega)]; exact he j hj

/-- No block of length `L` occurs twice among the first `N` notes. -/
def RepeatFree (s : ℕ → Bool) (N L : ℕ) : Prop :=
  ∀ i j, i < j → j + L ≤ N → ¬ ∀ t < L, s (i + t) = s (j + t)

/-- No repeated block means no echo of that length ending at any `n ≤ N`. -/
theorem not_echo_of_repeatFree {s : ℕ → Bool} {N L n : ℕ} (h : RepeatFree s N L) (hn : n ≤ N) :
    ¬ Echo s n L := by
  rintro ⟨p, hp, hkp, he⟩
  exact h (n - L - p) (n - L) (by omega) (by omega) he

/-- The block of length `L` starting at `i`, as a number (bit `t` = note `i + t`). -/
def blockKey (s : ℕ → Bool) (i : ℕ) : ℕ → ℕ
  | 0 => 0
  | L + 1 => (if s i then 1 else 0) + 2 * blockKey s (i + 1) L

theorem blockKey_congr {s : ℕ → Bool} {i j L : ℕ} (h : ∀ t < L, s (i + t) = s (j + t)) :
    blockKey s i L = blockKey s j L := by
  induction L generalizing i j with
  | zero => rfl
  | succ L ih =>
    simp only [blockKey]
    have h0 : s i = s j := by simpa using h 0 (by omega)
    have h1 : blockKey s (i + 1) L = blockKey s (j + 1) L :=
      ih (i := i + 1) (j := j + 1) fun t ht => by
        rw [show i + 1 + t = i + (t + 1) by omega, show j + 1 + t = j + (t + 1) by omega]
        exact h (t + 1) (by omega)
    rw [h0, h1]

/-- **The sorting check**: the keys of all blocks of length `L` among the first `N` notes, sorted,
are strictly increasing (so no two are equal). -/
def repeatFreeB (s : ℕ → Bool) (N L : ℕ) : Bool :=
  decide (List.IsChain (· < ·)
    (((List.range (N + 1 - L)).map fun i => blockKey s i L).mergeSort (fun a b => decide (a ≤ b))))

theorem repeatFree_of_check {s : ℕ → Bool} {N L : ℕ} (h : repeatFreeB s N L = true) :
    RepeatFree s N L := by
  intro i j hij hjN heq
  have hc := of_decide_eq_true h
  have hnd : (((List.range (N + 1 - L)).map fun i => blockKey s i L).mergeSort
      (fun a b => decide (a ≤ b))).Nodup :=
    (List.isChain_iff_pairwise.1 hc).nodup
  have hnd' := hnd.perm (List.mergeSort_perm _ _)
  have := List.inj_on_of_nodup_map hnd' (List.mem_range.2 (show i < N + 1 - L by omega))
    (List.mem_range.2 (show j < N + 1 - L by omega)) (blockKey_congr heq)
  omega

/-- **The logarithmic check**: for every dyadic band `[2^j, 2^(j+1))` up to `N`, no block of
length `a·j + b + 1` repeats below the end of the band. -/
def echoLogCheck (s : ℕ → Bool) (a b N : ℕ) : Bool :=
  (List.range (Nat.log 2 N + 1)).all fun j => repeatFreeB s (min (2 ^ (j + 1) - 1) N) (a * j + b + 1)

/-- The logarithmic check bounds every echo up to `N`. -/
theorem not_echo_of_echoLogCheck {s : ℕ → Bool} {a b N : ℕ} (h : echoLogCheck s a b N = true)
    {n : ℕ} (hn : n ≤ N) : ¬ Echo s n (a * Nat.log 2 n + b + 1) := by
  rcases Nat.eq_zero_or_pos n with rfl | hn0
  · rintro ⟨p, hp, hkp, -⟩; omega
  · have hj : Nat.log 2 n < Nat.log 2 N + 1 := Nat.lt_succ_of_le (Nat.log_mono_right hn)
    have hrf := repeatFree_of_check (List.all_eq_true.1 h _ (List.mem_range.2 hj))
    apply not_echo_of_repeatFree hrf
    have : n < 2 ^ (Nat.log 2 n + 1) := Nat.lt_pow_succ_log_self (by norm_num) n
    omega

/-- **Certificate for the centre column**: if `s` agrees with the centre column below `N` and
the logarithmic check passes, the excess bound `a·log₂ n + b` holds for every `n ≤ N`. -/
theorem echoLogBound_upto_of_check {s : ℕ → Bool} {a b N : ℕ}
    (hag : ∀ i < N, s i = centerCol i) (h : echoLogCheck s a b N = true) :
    ∀ n ≤ N, n ≤ tuneCost centerCol n + (a * Nat.log 2 n + b) := by
  intro n hn
  rw [excess_le_iff_not_echo, ← echo_congr (fun i hi => hag i (by omega))]
  exact not_echo_of_echoLogCheck h hn

/-- The Boolean form of an echo witness. -/
def echoB (s : ℕ → Bool) (n k p : ℕ) : Bool :=
  decide (0 < p) && decide (k + p ≤ n) &&
    (List.range k).all fun j => s (n - k - p + j) == s (n - k + j)

theorem echo_of_echoB {s : ℕ → Bool} {n k p : ℕ} (h : echoB s n k p = true) : Echo s n k := by
  simp only [echoB, Bool.and_eq_true, decide_eq_true_eq, List.all_eq_true, List.mem_range,
    beq_iff_eq] at h
  exact ⟨p, h.1.1, h.1.2, h.2⟩

/-- **A refutation from one echo**: an echo of length `a·log₂ n + b + 1` in the centre column
refutes `EchoLogBound a b`. -/
theorem not_echoLogBound_of_echo {a b n : ℕ} (h : Echo centerCol n (a * Nat.log 2 n + b + 1)) :
    ¬ EchoLogBound a b := fun hb =>
  (excess_le_iff_not_echo centerCol n _).1 (hb n) h

end GLM.Rule30
