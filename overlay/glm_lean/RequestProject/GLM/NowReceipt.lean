/-
# The receipt in the now — what a delta-sigma accumulator actually records

The supplied study `source_material/HISTORY_RECORDED_NOW_STUDY.md` (and its v2,
v3 and v4 sequels) makes one central claim about this substrate: *the present
state of an exact-rational process is the exact integral of everything that led
to it, so the state is the "receipt" of its own history.*  The demonstrations
are all runs of the first-order delta-sigma loop already formalised here
(`GLM.Info.dsState` over `ℝ`, `GLM.ZeroStorageV5.dsAcc` over `ℚ`), and the
claim is tested by recovering the number of emitted ones from the final state.

This file states the claim exactly and settles it.  The answer is two-sided.

## What the accumulator does record (§1)

* `acc_eq_fract` — after `n` ticks the accumulator is exactly
  `Int.fract (∑ i < n, t i)`: the fractional part of the integral of the input,
  and nothing else.
* `count_eq_floor` — so the number of ones is exactly `⌊∑ i < n, t i⌋`.
* `acc_eq_iff_fract_eq` — two runs leave the same accumulator **iff** their
  input integrals agree modulo one.  That is the exact content of "the state is
  the receipt": the receipt is one rational, the integral mod 1.

## What it does not record (§2)

* `receipt_collision` — two explicit input schedules of the same length with
  the same final accumulator *and* the same emitted count, whose trajectories
  differ at tick 1.  The state is therefore not injective on histories, so no
  amount of exactness recovers the history from the state.
* `acc_mem_grid` — if every input lies on the `1/q` grid then every reachable
  accumulator is one of the `q` values `j/q`, `0 ≤ j < q`, **whatever the tick
  count is**.
* `receipt_pigeonhole` — hence among any `q + 1` such schedules two share a
  receipt.  The number of histories a receipt can separate is bounded by the
  grid, not by the length of the run: the v3 study's extrapolated "holographic
  bound" of about `10²⁰` ticks for a 24-rational carrier has no such bound
  behind it.

## The constant-target case, which is what the studies measured (§3)

* `const_count_eq_floor` and `const_acc_eq_fract` — for a constant target the
  count after `n` ticks is `⌊n·t⌋` and the accumulator is `Int.fract (n·t)`.
  Both are functions of `t` and `n` alone, so the "recovery" demonstrations
  recover nothing that the target and the tick count did not already give.
* `const_average_eq` — the time average is exactly `⌊n·t⌋ / n`, and
  `const_bit_eq_floor_diff` — the `n`-th bit is `⌊(n+1)·t⌋ - ⌊n·t⌋`.  These two
  are the closed forms the package's `exact_real.delta_sigma_average` and
  `delta_sigma_bits` use in place of the loop; they are the same statements as
  `GLM.Info.dsOnes_eq_floor` and `GLM.Info.dsBit_eq_floor_diff` over `ℝ`,
  restated for the exact rational loop the code actually runs.

## The arrow of time (§4)

* `cumulative_mono` — a running total of non-negative costs is monotone.  The
  v3 study reports this as its "key finding" about the geometric tax; it is
  true of any non-negative quantity whatever, so it says nothing about the tax.
-/
import RequestProject.GLM.ZeroStorageV5

namespace GLM.NowReceipt

open Finset
open GLM.ZeroStorageV5

variable {t u : ℕ → ℚ}

/-! ## §1  What the accumulator records -/

/-- Every emitted bit is `0` or `1`. -/
lemma dsBit_eq_zero_or_one (t : ℕ → ℚ) (n : ℕ) : dsBit t n = 0 ∨ dsBit t n = 1 := by
  unfold dsBit
  split <;> simp

/-- The number of ones after `n` ticks is a natural number. -/
lemma exists_count (t : ℕ → ℚ) (n : ℕ) :
    ∃ m : ℕ, ∑ i ∈ range n, dsBit t i = (m : ℚ) := by
  induction n with
  | zero => exact ⟨0, by simp⟩
  | succ n ih =>
      obtain ⟨m, hm⟩ := ih
      rcases dsBit_eq_zero_or_one t n with h | h
      · exact ⟨m, by rw [Finset.sum_range_succ, hm, h, add_zero]⟩
      · exact ⟨m + 1, by rw [Finset.sum_range_succ, hm, h]; push_cast; ring⟩

/-- **The receipt is the fractional part of the integral.**  After `n` ticks the
accumulator is exactly `Int.fract (∑ i < n, t i)`. -/
theorem acc_eq_fract (ht : ∀ n, 0 ≤ t n ∧ t n ≤ 1) (n : ℕ) :
    dsAcc t n = Int.fract (∑ i ∈ range n, t i) := by
  obtain ⟨m, hm⟩ := exists_count t n
  obtain ⟨h0, h1⟩ := dsAcc_mem_Ico ht n
  have hsum : ∑ i ∈ range n, t i = (m : ℤ) + dsAcc t n := by
    have := dsAcc_eq t n
    rw [hm] at this
    push_cast
    linarith [this]
  rw [hsum, Int.fract_intCast_add, Int.fract_eq_self.2 ⟨h0, h1⟩]

/-- **The count is the floor of the integral.** -/
theorem count_eq_floor (ht : ∀ n, 0 ≤ t n ∧ t n ≤ 1) (n : ℕ) :
    ∑ i ∈ range n, dsBit t i = (⌊∑ i ∈ range n, t i⌋ : ℚ) := by
  have hacc := acc_eq_fract ht n
  have := dsAcc_eq t n
  rw [hacc] at this
  rw [this, Int.self_sub_fract]

/-- **Two runs leave the same receipt exactly when their integrals agree mod 1.**
So the accumulator records the integral modulo one, and records nothing else. -/
theorem acc_eq_iff_fract_eq (ht : ∀ n, 0 ≤ t n ∧ t n ≤ 1)
    (hu : ∀ n, 0 ≤ u n ∧ u n ≤ 1) (n m : ℕ) :
    dsAcc t n = dsAcc u m ↔
      Int.fract (∑ i ∈ range n, t i) = Int.fract (∑ i ∈ range m, u i) := by
  rw [acc_eq_fract ht n, acc_eq_fract hu m]

/-! ## §2  What the accumulator does not record -/

/-- The first witness schedule: three quarters at every tick. -/
def schedA : ℕ → ℚ := fun _ => 3 / 4

/-- The second witness schedule: a half, then a full unit. -/
def schedB : ℕ → ℚ := fun i => if i = 0 then 1 / 2 else 1

/-- **The receipt does not determine the history.**  Two schedules of length two
leave the same accumulator and the same emitted count, and differ at tick 1. -/
theorem receipt_collision :
    dsAcc schedA 2 = dsAcc schedB 2 ∧
      (∑ i ∈ range 2, dsBit schedA i) = (∑ i ∈ range 2, dsBit schedB i) ∧
      dsAcc schedA 1 ≠ dsAcc schedB 1 := by
  have hsum : ∀ s : ℕ → ℚ, ∑ i ∈ range 2, dsBit s i = dsBit s 0 + dsBit s 1 := by
    intro s
    rw [Finset.sum_range_succ, Finset.sum_range_one]
  refine ⟨by norm_num [dsAcc, dsBit, schedA, schedB], ?_,
    by norm_num [dsAcc, dsBit, schedA, schedB]⟩
  rw [hsum, hsum]
  norm_num [dsAcc, dsBit, schedA, schedB]

/-- Both witness schedules are admissible inputs. -/
theorem schedA_mem (n : ℕ) : 0 ≤ schedA n ∧ schedA n ≤ 1 := by
  norm_num [schedA]

theorem schedB_mem (n : ℕ) : 0 ≤ schedB n ∧ schedB n ≤ 1 := by
  unfold schedB; split <;> norm_num

/-- **The reachable receipts are the grid, whatever the tick count.**  If every
input is a multiple of `1/q` then every accumulator is `j/q` for some
`0 ≤ j < q`. -/
theorem acc_mem_grid {q : ℕ} (hq : 0 < q) (ht : ∀ n, 0 ≤ t n ∧ t n ≤ 1)
    (hgrid : ∀ n, ∃ a : ℤ, t n = (a : ℚ) / q) (n : ℕ) :
    ∃ j : ℕ, j < q ∧ dsAcc t n = (j : ℚ) / q := by
  have hqQ : (0 : ℚ) < q := by exact_mod_cast hq
  have key : ∃ a : ℤ, dsAcc t n = (a : ℚ) / q := by
    induction n with
    | zero => exact ⟨0, by simp [dsAcc]⟩
    | succ n ih =>
        obtain ⟨a, ha⟩ := ih
        obtain ⟨b, hb⟩ := hgrid n
        rw [dsAcc_succ t n, ha, hb]
        unfold dsBit
        rw [ha, hb]
        split
        · exact ⟨a + b - q, by push_cast; field_simp⟩
        · exact ⟨a + b, by push_cast; field_simp; ring⟩
  obtain ⟨a, ha⟩ := key
  obtain ⟨h0, h1⟩ := dsAcc_mem_Ico ht n
  rw [ha] at h0 h1
  have ha0 : (0 : ℚ) ≤ a := by
    have := (div_nonneg_iff.1 h0)
    rcases this with ⟨h, _⟩ | ⟨_, h⟩
    · exact h
    · exact absurd h (not_le.2 hqQ)
  have haq : (a : ℚ) < q := by
    have := (div_lt_one hqQ).1 h1
    exact this
  have ha0' : (0 : ℤ) ≤ a := by exact_mod_cast ha0
  have haq' : a < (q : ℤ) := by exact_mod_cast haq
  refine ⟨a.toNat, by omega, ?_⟩
  rw [ha]
  congr 1
  exact_mod_cast (Int.toNat_of_nonneg ha0').symm

/-- **Pigeonhole on the receipts.**  Among any `q + 1` schedules on the `1/q`
grid, two leave the same accumulator after the same number of ticks — however
long the run.  The separating power of a receipt is bounded by the grid, not by
the length of the history. -/
theorem receipt_pigeonhole {q n : ℕ} (hq : 0 < q) (S : Finset (ℕ → ℚ))
    (hmem : ∀ s ∈ S, (∀ k, 0 ≤ s k ∧ s k ≤ 1) ∧ ∀ k, ∃ a : ℤ, s k = (a : ℚ) / q)
    (hcard : q < S.card) :
    ∃ a ∈ S, ∃ b ∈ S, a ≠ b ∧ dsAcc a n = dsAcc b n := by
  classical
  set T : Finset ℚ := (range q).image (fun j : ℕ => (j : ℚ) / (q : ℚ)) with hT
  have hmaps : ∀ s ∈ S, dsAcc s n ∈ T := by
    intro s hs
    obtain ⟨hb, hg⟩ := hmem s hs
    obtain ⟨j, hj, hval⟩ := acc_mem_grid hq hb hg n
    exact hT ▸ Finset.mem_image.2 ⟨j, Finset.mem_range.2 hj, hval.symm⟩
  have hTcard : T.card < S.card :=
    lt_of_le_of_lt (le_trans Finset.card_image_le (by simp)) hcard
  obtain ⟨a, ha, b, hb, hne, heq⟩ :=
    Finset.exists_ne_map_eq_of_card_lt_of_maps_to hTcard hmaps
  exact ⟨a, ha, b, hb, hne, heq⟩

/-! ## §3  The constant target — what the supplied studies actually measured -/

/-- For a constant target the count after `n` ticks is `⌊n·t⌋`. -/
theorem const_count_eq_floor {c : ℚ} (h0 : 0 ≤ c) (h1 : c ≤ 1) (n : ℕ) :
    ∑ i ∈ range n, dsBit (fun _ => c) i = (⌊(n : ℚ) * c⌋ : ℚ) := by
  have := count_eq_floor (t := fun _ => c) (fun _ => ⟨h0, h1⟩) n
  simpa [Finset.sum_const, nsmul_eq_mul] using this

/-- For a constant target the accumulator after `n` ticks is `Int.fract (n·t)` —
a function of the target and the tick count alone. -/
theorem const_acc_eq_fract {c : ℚ} (h0 : 0 ≤ c) (h1 : c ≤ 1) (n : ℕ) :
    dsAcc (fun _ => c) n = Int.fract ((n : ℚ) * c) := by
  have := acc_eq_fract (t := fun _ => c) (fun _ => ⟨h0, h1⟩) n
  simpa [Finset.sum_const, nsmul_eq_mul] using this

/-- The closed form behind `exact_real.delta_sigma_average`: the time average
after `n` ticks is exactly `⌊n·t⌋ / n`, with no loop to run. -/
theorem const_average_eq {c : ℚ} (h0 : 0 ≤ c) (h1 : c ≤ 1) (n : ℕ) :
    (∑ i ∈ range n, dsBit (fun _ => c) i) / n = (⌊(n : ℚ) * c⌋ : ℚ) / n := by
  rw [const_count_eq_floor h0 h1 n]

/-- The closed form behind `exact_real.delta_sigma_bits`: the `n`-th bit is
`⌊(n+1)·t⌋ - ⌊n·t⌋`. -/
theorem const_bit_eq_floor_diff {c : ℚ} (h0 : 0 ≤ c) (h1 : c ≤ 1) (n : ℕ) :
    dsBit (fun _ => c) n = (⌊((n : ℚ) + 1) * c⌋ : ℚ) - (⌊(n : ℚ) * c⌋ : ℚ) := by
  have hsucc := const_count_eq_floor h0 h1 (n + 1)
  have hn := const_count_eq_floor h0 h1 n
  have hsplit : ∑ i ∈ range (n + 1), dsBit (fun _ => c) i
      = (∑ i ∈ range n, dsBit (fun _ => c) i) + dsBit (fun _ => c) n :=
    Finset.sum_range_succ _ _
  rw [hsplit, hn] at hsucc
  have : ((n : ℚ) + 1) = ((n + 1 : ℕ) : ℚ) := by push_cast; ring
  rw [this]
  linarith [hsucc]

/-! ## §4  The arrow of time, and how little it says -/

/-- A running total of non-negative costs is monotone.  This is the whole of the
v3 study's "cumulative TAX strictly increases" finding: it holds of every
non-negative quantity, so it is not evidence about the geometric tax. -/
theorem cumulative_mono {w : ℕ → ℚ} (hw : ∀ i, 0 ≤ w i) :
    Monotone (fun n => ∑ i ∈ range n, w i) := by
  intro a b hab
  have hsub : range a ⊆ range b := by
    intro i hi
    exact Finset.mem_range.2 (lt_of_lt_of_le (Finset.mem_range.1 hi) hab)
  exact Finset.sum_le_sum_of_subset_of_nonneg hsub (fun i _ _ => hw i)

end GLM.NowReceipt
