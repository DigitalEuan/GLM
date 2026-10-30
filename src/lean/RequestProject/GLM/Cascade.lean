/-
# Cascaded loops: what a second wobble buys

`DeltaSigma.lean` builds the first-order modulator that chases a constant
target `t` and proves its `O(1/N)` law: the time average of `N` emitted bits is
within `1/N` of the target.  That file leaves two questions open, and they are
the two the noise directions of the to-do list ask.

**First, can the loop chase a *signal* rather than a constant?**  Everything in
`DeltaSigma.lean` is stated for a fixed `t`.  A modulated wobble — a target
whose amplitude and frequency vary with time, or two tones added together —
is not a constant, and nothing said so far applies to it.  `mState` and `mBit`
here are the same quantiser driven by an arbitrary input sequence `u : ℕ → ℝ`
with values in `[0, 1)`, and

* `mState_mem_Ico` — the accumulator is still bounded, whatever the input does;
* `mSum_eq` — the bits still carry the input exactly: `∑ bits = ∑ input − state`;
* `mAverage_error_le` — so the emitted bits track the input's *running mean* to
  within `1/N`, for every input.  The homeostasis does not depend on the target
  standing still.

And such a wobble can be a closed orbit rather than a drift: if the input is
`P`-periodic and its sum over one period is a whole number then the
accumulator is empty at the end of every period (`mState_period_eq_zero`), so
state and bits are exactly `P`-periodic (`mState_periodic`, `mBit_periodic`).
Two tones added together satisfy this exactly when their mixed period sum is an
integer, which is a decidable question about the input, not a property of the
loop.

**Second, what does cascading two loops buy?**  The cascade (a MASH 1-1, in the
converter literature) feeds the first loop's error into a second loop and
recombines:

```
y n = b₁ n + b₂ (n+1) − b₂ n
```

`casOut_error` is the exact statement of what that does: the instantaneous
error is a **second difference** of a bounded sequence,

```
t − y n = s₂ (n+2) − 2 · s₂ (n+1) + s₂ n .
```

A single loop shapes its error as a *first* difference, and one difference
telescopes once: the plain average is `O(1/N)` and no better.  Two differences
telescope twice, and the gain is visible as soon as the average is read with a
window that sums twice —

* `casDouble_sum` — the doubly accumulated error is exactly `s₂ M`, so it is
  bounded by `1` for all time, where a single loop's grows linearly;
* `casTriangular_error_lt` — hence the triangular (Bartlett) window average of
  the cascade's output is within `2 / (M (M − 1))` of the target: `O(1/M²)`.

And the improvement is real rather than an artefact of the bound:

* `firstOrder_triangular_error_ge` — on the target `1/2` the *same* triangular
  window over a single loop's bits is off by at least `1 / (2M)`.

So `2/(M(M−1))` against `1/(2M)`: the second wobble is worth an order, and the
statement of what it is worth is exact, with no probabilistic model of the
noise anywhere.  Nothing here is random; the "noise" is a deterministic
trajectory and its shaping is an algebraic identity.
-/
import RequestProject.GLM.DeltaSigma

namespace GLM.Info

open Finset

/-! ## A modulator driven by a signal -/

/-- The error accumulator of a first-order quantiser driven by the input
sequence `u`.  With `u` constant this is `dsState`. -/
noncomputable def mState (u : ℕ → ℝ) : ℕ → ℝ
  | 0 => 0
  | n + 1 => if 1 ≤ mState u n + u n then mState u n + u n - 1 else mState u n + u n

/-- The bit emitted at step `n` by the signal-driven quantiser. -/
noncomputable def mBit (u : ℕ → ℝ) (n : ℕ) : ℕ :=
  if 1 ≤ mState u n + u n then 1 else 0

@[simp] lemma mState_zero (u : ℕ → ℝ) : mState u 0 = 0 := rfl

lemma mBit_le_one (u : ℕ → ℝ) (n : ℕ) : mBit u n ≤ 1 := by
  unfold mBit; split_ifs <;> simp

/-- The defining recurrence with the bit made explicit. -/
lemma mState_succ (u : ℕ → ℝ) (n : ℕ) :
    mState u (n + 1) = mState u n + u n - (mBit u n : ℝ) := by
  show (if 1 ≤ mState u n + u n then mState u n + u n - 1 else mState u n + u n) = _
  unfold mBit
  split_ifs <;> simp

/-- **The accumulator is bounded, whatever the signal does.**  As long as the
input stays in `[0, 1)` the state does too, so a modulated target — varying
amplitude, varying frequency, several tones added — is chased with the same
homeostasis a constant target is. -/
lemma mState_mem_Ico {u : ℕ → ℝ} (hu : ∀ n, 0 ≤ u n ∧ u n < 1) (n : ℕ) :
    0 ≤ mState u n ∧ mState u n < 1 := by
  induction n with
  | zero => simp
  | succ k ih =>
      obtain ⟨hk0, hk1⟩ := ih
      obtain ⟨hu0, hu1⟩ := hu k
      show 0 ≤ (if 1 ≤ mState u k + u k then mState u k + u k - 1 else mState u k + u k) ∧
        (if 1 ≤ mState u k + u k then mState u k + u k - 1 else mState u k + u k) < 1
      split_ifs with h
      · constructor <;> linarith
      · constructor <;> linarith

/-- **The bits carry the signal.**  The sum of the first `N` bits is the sum of
the first `N` inputs, less the part the accumulator still holds. -/
theorem mSum_eq (u : ℕ → ℝ) (N : ℕ) :
    ∑ i ∈ range N, (mBit u i : ℝ) = (∑ i ∈ range N, u i) - mState u N := by
  induction N with
  | zero => simp
  | succ k ih =>
      rw [sum_range_succ, ih, sum_range_succ (f := u), mState_succ]
      ring

/-- **The `O(1/N)` law for a signal.**  The mean of the first `N` bits is
within `1/N` of the mean of the first `N` inputs. -/
theorem mAverage_error_le {u : ℕ → ℝ} (hu : ∀ n, 0 ≤ u n ∧ u n < 1) {N : ℕ}
    (hN : 0 < N) :
    |(∑ i ∈ range N, (mBit u i : ℝ)) / N - (∑ i ∈ range N, u i) / N| ≤ 1 / N := by
  have hNpos : (0 : ℝ) < N := by exact_mod_cast hN
  obtain ⟨hs0, hs1⟩ := mState_mem_Ico hu N
  have key : (∑ i ∈ range N, (mBit u i : ℝ)) / N - (∑ i ∈ range N, u i) / N
      = -(mState u N / N) := by
    rw [mSum_eq]
    field_simp
    ring
  rw [key, abs_neg, abs_of_nonneg (div_nonneg hs0 hNpos.le),
    div_le_div_iff_of_pos_right hNpos]
  exact hs1.le

/-! ## When the wobble closes its orbit -/

/-- **A periodic signal whose period sum is a whole number empties the
accumulator.**  After one period the state is the period sum less an integer
number of emitted bits, so it is an integer lying in `[0, 1)`, so it is zero. -/
theorem mState_period_eq_zero {u : ℕ → ℝ} (hu : ∀ n, 0 ≤ u n ∧ u n < 1)
    {P : ℕ} {k : ℤ} (hk : ∑ i ∈ range P, u i = (k : ℝ)) :
    mState u P = 0 := by
  have hsum := mSum_eq u P
  set B : ℤ := (∑ i ∈ range P, (mBit u i : ℕ) : ℤ) with hB
  have hcast : ∑ i ∈ range P, (mBit u i : ℝ) = (B : ℝ) := by
    rw [hB]; push_cast; ring
  have hstate : mState u P = ((k - B : ℤ) : ℝ) := by
    rw [hcast, hk] at hsum
    push_cast
    linarith [hsum]
  obtain ⟨h0, h1⟩ := mState_mem_Ico hu P
  rw [hstate] at h0 h1
  have h0' : (0 : ℤ) ≤ k - B := by exact_mod_cast h0
  have h1' : k - B < 1 := by exact_mod_cast h1
  have : k - B = 0 := by omega
  rw [hstate, this]
  norm_num

/-- **So the trajectory is exactly periodic.**  Two tones added together, or
any periodic input at all, drive the accumulator around a closed orbit as soon
as the period sum is a whole number: the "noise" is a cycle, not a drift. -/
theorem mState_periodic {u : ℕ → ℝ} (hu : ∀ n, 0 ≤ u n ∧ u n < 1)
    {P : ℕ} {k : ℤ} (hk : ∑ i ∈ range P, u i = (k : ℝ))
    (hper : ∀ n, u (n + P) = u n) :
    ∀ n, mState u (n + P) = mState u n := by
  intro n
  induction n with
  | zero => simpa using mState_period_eq_zero hu hk
  | succ m ih =>
      have hbit : mBit u (m + P) = mBit u m := by
        unfold mBit
        rw [ih, hper m]
      have hidx : m + 1 + P = (m + P) + 1 := by omega
      rw [hidx, mState_succ, mState_succ, ih, hper m, hbit]

/-- The emitted bits inherit the period. -/
theorem mBit_periodic {u : ℕ → ℝ} (hu : ∀ n, 0 ≤ u n ∧ u n < 1)
    {P : ℕ} {k : ℤ} (hk : ∑ i ∈ range P, u i = (k : ℝ))
    (hper : ∀ n, u (n + P) = u n) :
    ∀ n, mBit u (n + P) = mBit u n := by
  intro n
  unfold mBit
  rw [mState_periodic hu hk hper n, hper n]

/-- With a constant input the signal-driven modulator is the modulator of
`DeltaSigma.lean`. -/
lemma mState_const (t : ℝ) : ∀ n, mState (fun _ => t) n = dsState t n
  | 0 => rfl
  | n + 1 => by
      show (if 1 ≤ mState (fun _ => t) n + t then mState (fun _ => t) n + t - 1
            else mState (fun _ => t) n + t) = dsState t (n + 1)
      rw [mState_const t n]
      rfl

lemma mBit_const (t : ℝ) (n : ℕ) : mBit (fun _ => t) n = dsBit t n := by
  unfold mBit dsBit
  rw [mState_const t n]

/-! ## The cascade -/

/-- Stage one of the cascade: the ordinary first-order loop chasing `t`.  Its
error accumulator, `casErr`, is the signal the second stage is given. -/
noncomputable def casErr (t : ℝ) : ℕ → ℝ := dsState t

/-- The state of stage two: a first-order loop whose input is stage one's
error. -/
noncomputable def casState (t : ℝ) : ℕ → ℝ := mState (casErr t)

/-- The bit stage two emits. -/
noncomputable def casBit2 (t : ℝ) : ℕ → ℕ := mBit (casErr t)

/-- **The cascade's output.**  Stage one's bit plus the first difference of
stage two's bit — the recombination that cancels stage one's error and leaves a
second difference in its place.  The output is an integer in `{-1, 0, 1, 2}`
(`casOut_mem`), so the price of the extra order is a slightly wider alphabet,
not a finer one. -/
noncomputable def casOut (t : ℝ) (n : ℕ) : ℤ :=
  (dsBit t n : ℤ) + (casBit2 t (n + 1) : ℤ) - (casBit2 t n : ℤ)

lemma casErr_mem_Ico {t : ℝ} (ht0 : 0 ≤ t) (ht1 : t < 1) (n : ℕ) :
    0 ≤ casErr t n ∧ casErr t n < 1 :=
  dsState_mem_Ico ht0 ht1 n

lemma casOut_mem (t : ℝ) (n : ℕ) : -1 ≤ casOut t n ∧ casOut t n ≤ 2 := by
  have h1 : dsBit t n ≤ 1 := dsBit_le_one t n
  have h2 : casBit2 t (n + 1) ≤ 1 := mBit_le_one _ _
  have h3 : casBit2 t n ≤ 1 := mBit_le_one _ _
  unfold casOut
  omega

/-- Stage two's recurrence, in the form the recombination uses: its bit is
stage one's error less the first difference of its own state. -/
lemma casBit2_eq (t : ℝ) (n : ℕ) :
    (casBit2 t n : ℝ) = casErr t n - (casState t (n + 1) - casState t n) := by
  have h := mState_succ (casErr t) n
  show (mBit (casErr t) n : ℝ) = casErr t n - (mState (casErr t) (n+1) - mState (casErr t) n)
  linarith [h]

/-- Stage one's bit is the target less the first difference of its own state:
first-order noise shaping, stated exactly. -/
lemma dsBit_eq_sub (t : ℝ) (n : ℕ) :
    (dsBit t n : ℝ) = t - (casErr t (n + 1) - casErr t n) := by
  have h := dsState_succ t n
  show (dsBit t n : ℝ) = t - (dsState t (n + 1) - dsState t n)
  linarith [h]

/-- **The cascade shapes its error as a second difference.**  This is the whole
content of cascading: what separates the output from the target at each tick is
`Δ²` of a sequence that never leaves `[0, 1)`. -/
theorem casOut_error (t : ℝ) (n : ℕ) :
    t - (casOut t n : ℝ) =
      casState t (n + 2) - 2 * casState t (n + 1) + casState t n := by
  have hb1 := dsBit_eq_sub t n
  have hb2 := casBit2_eq t (n + 1)
  have hb2' := casBit2_eq t n
  have hcast : (casOut t n : ℝ)
      = (dsBit t n : ℝ) + (casBit2 t (n + 1) : ℝ) - (casBit2 t n : ℝ) := by
    unfold casOut; push_cast; ring
  rw [hcast, hb1, hb2, hb2']
  have : n + 1 + 1 = n + 2 := rfl
  rw [this]
  ring

lemma casState_zero (t : ℝ) : casState t 0 = 0 := rfl

lemma casState_one (t : ℝ) : casState t 1 = 0 := by
  have he : casErr t 0 = 0 := rfl
  have hb : mBit (casErr t) 0 = 0 := by
    unfold mBit
    rw [he]
    simp
  have h := mState_succ (casErr t) 0
  rw [he, hb] at h
  show mState (casErr t) 1 = 0
  simpa using h

/-- The accumulated error of the cascade telescopes once: it is the first
difference of stage two's state. -/
theorem casSum_error (t : ℝ) (N : ℕ) :
    ∑ i ∈ range N, (t - (casOut t i : ℝ))
      = casState t (N + 1) - casState t N := by
  induction N with
  | zero => simp [casState_zero, casState_one]
  | succ k ih =>
      rw [sum_range_succ, ih, casOut_error]
      have : k + 1 + 1 = k + 2 := rfl
      rw [this]
      ring

/-- Reading the sum twice telescopes twice: **the doubly accumulated error of
the cascade is exactly stage two's state**, hence bounded by `1` for all time,
where a single first-order loop's grows linearly
(`firstOrder_double_sum_half`). -/
theorem casDouble_sum (t : ℝ) (M : ℕ) :
    ∑ N ∈ range M, ∑ i ∈ range N, (t - (casOut t i : ℝ)) = casState t M := by
  induction M with
  | zero => simp [casState_zero]
  | succ k ih =>
      rw [sum_range_succ, ih, casSum_error]
      ring

/-! ## Reading the output through a triangular window -/

/-- Exchanging the order of a double partial sum: summing the running sums up
to `M` weights the `i`-th term by `M - 1 - i`, the triangular (Bartlett)
window. -/
lemma sum_range_sum_range (f : ℕ → ℝ) (M : ℕ) :
    ∑ N ∈ range M, ∑ i ∈ range N, f i
      = ∑ i ∈ range M, ((M : ℝ) - 1 - i) * f i := by
  induction M with
  | zero => simp
  | succ k ih =>
      have hcast : ((k + 1 : ℕ) : ℝ) = (k : ℝ) + 1 := by push_cast; ring
      rw [sum_range_succ, ih, hcast, sum_range_succ]
      rw [show ((k : ℝ) + 1 - 1 - (k : ℝ)) * f k = 0 by ring, add_zero]
      rw [show ∑ i ∈ range k, ((k : ℝ) + 1 - 1 - (i : ℝ)) * f i
            = ∑ i ∈ range k, (((k : ℝ) - 1 - (i : ℝ)) * f i + f i) from
          sum_congr rfl fun i _ => by ring]
      rw [sum_add_distrib]

/-- The triangular window's total weight. -/
lemma sum_triangular_weights (M : ℕ) :
    ∑ i ∈ range M, ((M : ℝ) - 1 - i) = (M : ℝ) * ((M : ℝ) - 1) / 2 := by
  induction M with
  | zero => simp
  | succ k ih =>
      have hcast : ((k + 1 : ℕ) : ℝ) = (k : ℝ) + 1 := by push_cast; ring
      rw [hcast, sum_range_succ]
      rw [show ∑ i ∈ range k, ((k : ℝ) + 1 - 1 - (i : ℝ))
            = ∑ i ∈ range k, (((k : ℝ) - 1 - (i : ℝ)) + 1) from
          sum_congr rfl fun i _ => by ring]
      rw [sum_add_distrib, ih]
      simp only [sum_const, card_range, nsmul_eq_mul, mul_one]
      ring

/-- The triangular-window average of the cascade's output after `M` ticks: a
rational combination of the emitted symbols, with no floating point and no
model of the noise. -/
noncomputable def casTriangular (t : ℝ) (M : ℕ) : ℝ :=
  (∑ i ∈ range M, ((M : ℝ) - 1 - i) * (casOut t i : ℝ)) / ((M : ℝ) * ((M : ℝ) - 1) / 2)

/-- **The `O(1/M²)` law of the cascade.**  Read through the triangular window,
the cascade's output is within `2 / (M (M − 1))` of the target — an order
better than the `1/N` a single loop achieves, and again an exact bound rather
than an asymptotic one. -/
theorem casTriangular_error_lt {t : ℝ} (ht0 : 0 ≤ t) (ht1 : t < 1) {M : ℕ}
    (hM : 2 ≤ M) :
    |casTriangular t M - t| < 2 / ((M : ℝ) * ((M : ℝ) - 1)) := by
  have hM2 : (2 : ℝ) ≤ (M : ℝ) := by exact_mod_cast hM
  have hMpos : (0 : ℝ) < M := by linarith
  have hM1 : (0 : ℝ) < (M : ℝ) - 1 := by linarith
  have hW : (0 : ℝ) < (M : ℝ) * ((M : ℝ) - 1) / 2 := by positivity
  have hsplit : ∑ i ∈ range M, ((M : ℝ) - 1 - i) * (t - (casOut t i : ℝ))
      = casState t M := by
    rw [← sum_range_sum_range (fun i => t - (casOut t i : ℝ)) M]
    exact casDouble_sum t M
  have hexp : ∑ i ∈ range M, ((M : ℝ) - 1 - i) * (t - (casOut t i : ℝ))
      = (∑ i ∈ range M, ((M : ℝ) - 1 - i)) * t
        - ∑ i ∈ range M, ((M : ℝ) - 1 - i) * (casOut t i : ℝ) := by
    rw [sum_mul, ← sum_sub_distrib]
    exact sum_congr rfl fun i _ => by ring
  rw [sum_triangular_weights] at hexp
  have hS : ∑ i ∈ range M, ((M : ℝ) - 1 - i) * (casOut t i : ℝ)
      = ((M : ℝ) * ((M : ℝ) - 1) / 2) * t - casState t M := by
    linarith [hexp, hsplit]
  have hs := mState_mem_Ico (u := casErr t) (fun n => casErr_mem_Ico ht0 ht1 n) M
  have hstate : casState t M = mState (casErr t) M := rfl
  have hkey : casTriangular t M - t
      = -(casState t M / ((M : ℝ) * ((M : ℝ) - 1) / 2)) := by
    unfold casTriangular
    rw [hS]
    field_simp
    ring
  rw [hkey, abs_neg,
    abs_of_nonneg (div_nonneg (by rw [hstate]; exact hs.1) hW.le), div_lt_iff₀ hW]
  have hone : 2 / ((M : ℝ) * ((M : ℝ) - 1)) * ((M : ℝ) * ((M : ℝ) - 1) / 2) = 1 := by
    field_simp
  rw [hone, hstate]
  exact hs.2

/-! ## What a single loop cannot do -/

/-- On the target `1/2` the first-order accumulator is two-periodic: `0` at
even times and `1/2` at odd ones. -/
lemma dsState_half (k : ℕ) :
    dsState (1/2 : ℝ) (2 * k) = 0 ∧ dsState (1/2 : ℝ) (2 * k + 1) = 1/2 := by
  induction k with
  | zero =>
      refine ⟨rfl, ?_⟩
      show (if (1 : ℝ) ≤ dsState (1/2 : ℝ) 0 + 1/2 then dsState (1/2 : ℝ) 0 + 1/2 - 1
            else dsState (1/2 : ℝ) 0 + 1/2) = 1/2
      norm_num
  | succ k ih =>
      obtain ⟨he, ho⟩ := ih
      have hnext : dsState (1/2 : ℝ) (2 * k + 1 + 1) = 0 := by
        show (if (1 : ℝ) ≤ dsState (1/2 : ℝ) (2 * k + 1) + 1/2 then
                dsState (1/2 : ℝ) (2 * k + 1) + 1/2 - 1
              else dsState (1/2 : ℝ) (2 * k + 1) + 1/2) = 0
        rw [ho]; norm_num
      have heven : dsState (1/2 : ℝ) (2 * (k + 1)) = 0 := by
        rw [show 2 * (k + 1) = 2 * k + 1 + 1 by ring]
        exact hnext
      refine ⟨heven, ?_⟩
      show (if (1 : ℝ) ≤ dsState (1/2 : ℝ) (2 * (k+1)) + 1/2 then
              dsState (1/2 : ℝ) (2 * (k+1)) + 1/2 - 1
            else dsState (1/2 : ℝ) (2 * (k+1)) + 1/2) = 1/2
      rw [heven]
      norm_num

lemma dsState_half_eq (n : ℕ) :
    dsState (1/2 : ℝ) n = if n % 2 = 0 then 0 else 1/2 := by
  obtain ⟨k, hk | hk⟩ := Nat.even_or_odd' n
  · subst hk; rw [if_pos (by omega)]; exact (dsState_half k).1
  · subst hk; rw [if_neg (by omega)]; exact (dsState_half k).2

/-- The accumulated error of a single loop is its state. -/
lemma firstOrder_sum_error (t : ℝ) (N : ℕ) :
    ∑ i ∈ range N, (t - (dsBit t i : ℝ)) = dsState t N := by
  induction N with
  | zero => simp
  | succ k ih =>
      rw [sum_range_succ, ih, dsState_succ]
      ring

/-- **The doubly accumulated error of a single loop grows linearly.**  On the
target `1/2` it is `⌊M/2⌋ / 2`, where the cascade's stays below `1`. -/
theorem firstOrder_double_sum_half (M : ℕ) :
    ∑ N ∈ range M, ∑ i ∈ range N, ((1/2 : ℝ) - (dsBit (1/2 : ℝ) i : ℝ))
      = ((M / 2 : ℕ) : ℝ) / 2 := by
  induction M with
  | zero => simp
  | succ k ih =>
      rw [sum_range_succ, ih, firstOrder_sum_error, dsState_half_eq]
      obtain ⟨j, hj | hj⟩ := Nat.even_or_odd' k
      · subst hj
        rw [if_pos (by omega), show (2 * j + 1) / 2 = j by omega,
          show 2 * j / 2 = j by omega]
        ring
      · subst hj
        rw [if_neg (by omega), show (2 * j + 1 + 1) / 2 = j + 1 by omega,
          show (2 * j + 1) / 2 = j by omega]
        push_cast
        ring

/-- The same triangular window, applied to a single loop's bits. -/
noncomputable def firstOrderTriangular (t : ℝ) (M : ℕ) : ℝ :=
  (∑ i ∈ range M, ((M : ℝ) - 1 - i) * (dsBit t i : ℝ)) / ((M : ℝ) * ((M : ℝ) - 1) / 2)

/-- **The single loop does not reach `O(1/M²)`.**  Read through the very window
that puts the cascade within `2/(M(M−1))` of the target, a single first-order
loop chasing `1/2` is still off by at least `1/(2M)`.  The extra order the
cascade buys is therefore real, and not an artefact of the estimate. -/
theorem firstOrder_triangular_error_ge {M : ℕ} (hM : 2 ≤ M) :
    1 / (2 * (M : ℝ)) ≤ |firstOrderTriangular (1/2 : ℝ) M - 1/2| := by
  have hM2 : (2 : ℝ) ≤ (M : ℝ) := by exact_mod_cast hM
  have hMpos : (0 : ℝ) < M := by linarith
  have hM1 : (0 : ℝ) < (M : ℝ) - 1 := by linarith
  have hW : (0 : ℝ) < (M : ℝ) * ((M : ℝ) - 1) / 2 := by positivity
  have hD : ∑ i ∈ range M, ((M : ℝ) - 1 - i) * ((1/2 : ℝ) - (dsBit (1/2 : ℝ) i : ℝ))
      = ((M / 2 : ℕ) : ℝ) / 2 := by
    rw [← sum_range_sum_range (fun i => (1/2 : ℝ) - (dsBit (1/2 : ℝ) i : ℝ)) M]
    exact firstOrder_double_sum_half M
  have hexp : ∑ i ∈ range M, ((M : ℝ) - 1 - i) * ((1/2 : ℝ) - (dsBit (1/2 : ℝ) i : ℝ))
      = (∑ i ∈ range M, ((M : ℝ) - 1 - i)) * (1/2)
        - ∑ i ∈ range M, ((M : ℝ) - 1 - i) * (dsBit (1/2 : ℝ) i : ℝ) := by
    rw [sum_mul, ← sum_sub_distrib]
    exact sum_congr rfl fun i _ => by ring
  rw [sum_triangular_weights] at hexp
  have hS : ∑ i ∈ range M, ((M : ℝ) - 1 - i) * (dsBit (1/2 : ℝ) i : ℝ)
      = ((M : ℝ) * ((M : ℝ) - 1) / 2) * (1/2) - ((M / 2 : ℕ) : ℝ) / 2 := by
    linarith [hexp, hD]
  have hkey : firstOrderTriangular (1/2 : ℝ) M - 1/2
      = -((((M / 2 : ℕ) : ℝ) / 2) / ((M : ℝ) * ((M : ℝ) - 1) / 2)) := by
    unfold firstOrderTriangular
    rw [hS]
    field_simp
    ring
  have hfloor : ((M : ℝ) - 1) / 2 ≤ ((M / 2 : ℕ) : ℝ) := by
    have h1 : M ≤ 2 * (M / 2) + 1 := by omega
    have h2 : (M : ℝ) ≤ 2 * ((M / 2 : ℕ) : ℝ) + 1 := by exact_mod_cast h1
    linarith
  rw [hkey, abs_neg, abs_of_nonneg (div_nonneg (by positivity) hW.le), le_div_iff₀ hW]
  have hval : 1 / (2 * (M : ℝ)) * ((M : ℝ) * ((M : ℝ) - 1) / 2) = ((M : ℝ) - 1) / 4 := by
    field_simp
    ring
  rw [hval]
  linarith [hfloor]

end GLM.Info
