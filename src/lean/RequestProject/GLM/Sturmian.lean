/-
# The wobble signature: what the delta-sigma stream actually is

`DeltaSigma.lean` builds the first-order modulator and proves that its time
average reaches the target with an explicit `1/N` rate.  That answers *does it
converge*.  The external studies catalogued in `glm_study_findings_catalog.md`
ask a different question of the same loop: they run it for ten thousand steps
and then *measure the stream itself* — Shannon entropy of the emitted bits,
mean and maximum run length, the density of ones — and report those numbers as
the "vibrational signature" of the target, distinguishing algebraic irrationals
from transcendentals from the fine-structure constant.

Every one of those measurements is a theorem about the target, not an
experimental finding, and this file proves it.  The bridge is the observation
that the exact modulator *is* an irrational rotation:

* `dsState_eq_fract` — the accumulator after `n` ticks is exactly
  `Int.fract (n * t)`.  The loop is the orbit of `0` under rotation by `t`.
* `dsBit_eq_floor_diff` — hence the emitted bit is `⌊(n+1)t⌋ - ⌊n t⌋`.  The
  stream is the **mechanical (Sturmian) word of slope `t`**, which is what the
  catalogue's "Sturmian quasiperiodicity" observation names.
* `dsOnes_eq_floor` — so the number of ones in the first `N` bits is exactly
  `⌊N t⌋`: the ones-density is pinned, not estimated.

From that everything the studies report follows as an exact bound.

**Run lengths** (catalogue §2.3, the *max run length* and *mean run length*
columns).

* `ds_fires_within` — the quantiser fires at least once in any window of
  length `L` with `1 ≤ L t`.
* `ds_zero_run_lt` / `ds_zero_run_length_lt` — therefore a run of zeros is
  strictly shorter than `1/t`, and `ds_one_run_lt` gives the dual bound
  `1/(1-t)` for a run of ones.  The catalogue's max run of 137 for the
  fine-structure constant (`1/0.007297 = 137.04…`) and 1110 for `e^π - π` are
  this bound, not a property of the sample.
* `ds_no_adjacent_ones` — below slope `1/2` no two ones are adjacent, so runs
  of ones are single bits.
* `dsTransitions_eq` — the exact transition count, `2⌊N t⌋ + bit N`, and
  `dsMeanRunLength_tendsto` — the mean run length converges to `1/(2t)`.  The
  catalogue's column (1.50 at slope 1/3, 1.21 at `√2-1`, 3.53 at `π-3`,
  4.55 at Liouville, 68.49 at `α`) is that single formula evaluated.

**Entropy** (catalogue §2.3 and §6.1).  `wobbleEntropy` is the binary entropy
in bits.  The studies' two separate tables — the "wobble Shannon entropy" of a
constant and the "SNR is wobble entropy" table of an electrical oscillator —
are the *same* function of the ones-density:

* `ds_wobbleEntropy_tendsto` — the entropy of the observed density converges to
  `wobbleEntropy t`;
* `wobbleEntropy_eq_zero_iff` — it vanishes exactly at density `0` and `1`, and
  `ds_wobbleEntropy_zero_iff_silent` turns that into a statement about the
  stream: zero entropy *is* a constant stream;
* `ds_resonance_lock` and `ds_resonance_entropy` — at exact resonance (gain
  one) the modulator emits nothing but ones and the entropy is exactly zero,
  which is the catalogue's "resonance IS zero wobble entropy";
* `wobbleEntropy_le_one`, `wobbleEntropy_eq_one_iff` — one bit per symbol, and
  only at density `1/2`, which is the `SNR = 0 dB` row;
* `wobbleEntropy_strictAntiOn_high` — and between those the entropy falls
  strictly as the signal purifies, which is what makes the table a measure of
  signal quality rather than a coincidence.

Nothing here is approximate and nothing is sampled: every statement is an
identity or a strict bound valid for every target `t ∈ [0, 1)`.
-/
import RequestProject.GLM.DeltaSigma

namespace GLM.Info

open Filter Topology

/-! ## 1.  The modulator is an exact rotation

The accumulator of the first-order loop, started at zero, is the orbit of zero
under the rotation `x ↦ x + t` of the circle.  This is the fact that turns
every later statement into arithmetic on floors. -/

/-- **The accumulator is the fractional part.**  After `n` ticks the state of
the modulator chasing `t` is exactly `Int.fract (n · t)`. -/
theorem dsState_eq_fract {t : ℝ} (ht0 : 0 ≤ t) (ht1 : t < 1) (n : ℕ) :
    dsState t n = Int.fract ((n : ℝ) * t) := by
  induction n with
  | zero => simp
  | succ k ih =>
      have h0 : (0 : ℝ) ≤ Int.fract ((k : ℝ) * t) := Int.fract_nonneg _
      have h1 : Int.fract ((k : ℝ) * t) < 1 := Int.fract_lt_one _
      have hfl : (⌊(k : ℝ) * t⌋ : ℝ) + Int.fract ((k : ℝ) * t) = (k : ℝ) * t :=
        Int.floor_add_fract _
      have hcast : ((k + 1 : ℕ) : ℝ) * t
          = (⌊(k : ℝ) * t⌋ : ℝ) + (Int.fract ((k : ℝ) * t) + t) := by
        push_cast
        rw [add_mul, one_mul]
        linarith
      have hfract : Int.fract (((k + 1 : ℕ) : ℝ) * t)
          = Int.fract (Int.fract ((k : ℝ) * t) + t) := by
        rw [hcast, Int.fract_intCast_add]
      show (if 1 ≤ dsState t k + t then dsState t k + t - 1 else dsState t k + t)
          = Int.fract (((k + 1 : ℕ) : ℝ) * t)
      rw [ih, hfract]
      set a := Int.fract ((k : ℝ) * t)
      split_ifs with h
      · have hsub : Int.fract (a + t - 1) = Int.fract (a + t) := by
          simp
        rw [← hsub, Int.fract_eq_self.2 ⟨by linarith, by linarith⟩]
      · rw [Int.fract_eq_self.2 ⟨by linarith, by linarith⟩]

/-- **The stream is a mechanical word.**  The bit emitted at tick `n` is
`⌊(n+1)t⌋ - ⌊n t⌋`: the delta-sigma output of slope `t` is the Sturmian word of
slope `t`, which is why the studies see quasiperiodic structure in it rather
than noise. -/
theorem dsBit_eq_floor_diff {t : ℝ} (ht0 : 0 ≤ t) (ht1 : t < 1) (n : ℕ) :
    (dsBit t n : ℤ) = ⌊((n : ℝ) + 1) * t⌋ - ⌊(n : ℝ) * t⌋ := by
  have h1 := dsState_succ t n
  rw [dsState_eq_fract ht0 ht1 (n + 1), dsState_eq_fract ht0 ht1 n] at h1
  simp only [Int.fract] at h1
  push_cast at h1
  have hR : ((dsBit t n : ℤ) : ℝ) = ((⌊((n : ℝ) + 1) * t⌋ - ⌊(n : ℝ) * t⌋ : ℤ) : ℝ) := by
    push_cast
    linarith
  exact_mod_cast hR

/-! ## 2.  Counting ones -/

/-- The number of ones emitted in the first `N` ticks. -/
noncomputable def dsOnes (t : ℝ) (N : ℕ) : ℕ := ∑ i ∈ Finset.range N, dsBit t i

@[simp] lemma dsOnes_zero (t : ℝ) : dsOnes t 0 = 0 := by simp [dsOnes]

lemma dsOnes_succ (t : ℝ) (N : ℕ) : dsOnes t (N + 1) = dsOnes t N + dsBit t N := by
  simp [dsOnes, Finset.sum_range_succ]

/-- **The ones-count is exact.**  Not "about `N t`": exactly `⌊N t⌋`. -/
theorem dsOnes_eq_floor {t : ℝ} (ht0 : 0 ≤ t) (ht1 : t < 1) (N : ℕ) :
    (dsOnes t N : ℤ) = ⌊(N : ℝ) * t⌋ := by
  induction N with
  | zero => simp
  | succ k ih =>
      rw [dsOnes_succ, Nat.cast_add, ih, dsBit_eq_floor_diff ht0 ht1 k]
      push_cast
      ring

/-- The same statement for a window that does not start at zero. -/
theorem dsWindow_eq_floor_diff {t : ℝ} (ht0 : 0 ≤ t) (ht1 : t < 1) (n L : ℕ) :
    ∑ i ∈ Finset.Ico n (n + L), (dsBit t i : ℤ)
      = ⌊((n : ℝ) + L) * t⌋ - ⌊(n : ℝ) * t⌋ := by
  have hle : n ≤ n + L := Nat.le_add_right n L
  have hsplit : ∑ i ∈ Finset.Ico n (n + L), (dsBit t i : ℤ)
      = (∑ i ∈ Finset.range (n + L), (dsBit t i : ℤ))
        - ∑ i ∈ Finset.range n, (dsBit t i : ℤ) :=
    Finset.sum_Ico_eq_sub _ hle
  have hA : (∑ i ∈ Finset.range (n + L), (dsBit t i : ℤ)) = ⌊((n + L : ℕ) : ℝ) * t⌋ := by
    have := dsOnes_eq_floor ht0 ht1 (n + L)
    simpa [dsOnes, Nat.cast_sum] using this
  have hB : (∑ i ∈ Finset.range n, (dsBit t i : ℤ)) = ⌊(n : ℝ) * t⌋ := by
    have := dsOnes_eq_floor ht0 ht1 n
    simpa [dsOnes, Nat.cast_sum] using this
  rw [hsplit, hA, hB]
  push_cast
  ring

/-- **Balance, from below.**  A window of `L` ticks emits more than `L t - 1`
ones. -/
theorem dsWindow_gt {t : ℝ} (ht0 : 0 ≤ t) (ht1 : t < 1) (n L : ℕ) :
    (L : ℝ) * t - 1 < ((∑ i ∈ Finset.Ico n (n + L), (dsBit t i : ℤ) : ℤ) : ℝ) := by
  rw [dsWindow_eq_floor_diff ht0 ht1 n L]
  have h1 : ((n : ℝ) + L) * t - 1 < (⌊((n : ℝ) + L) * t⌋ : ℝ) := Int.sub_one_lt_floor _
  have h2 : (⌊(n : ℝ) * t⌋ : ℝ) ≤ (n : ℝ) * t := Int.floor_le _
  push_cast
  nlinarith

/-- **Balance, from above.**  A window of `L` ticks emits fewer than `L t + 1`
ones. -/
theorem dsWindow_lt {t : ℝ} (ht0 : 0 ≤ t) (ht1 : t < 1) (n L : ℕ) :
    ((∑ i ∈ Finset.Ico n (n + L), (dsBit t i : ℤ) : ℤ) : ℝ) < (L : ℝ) * t + 1 := by
  rw [dsWindow_eq_floor_diff ht0 ht1 n L]
  have h1 : (⌊((n : ℝ) + L) * t⌋ : ℝ) ≤ ((n : ℝ) + L) * t := Int.floor_le _
  have h2 : (n : ℝ) * t - 1 < (⌊(n : ℝ) * t⌋ : ℝ) := Int.sub_one_lt_floor _
  push_cast
  nlinarith

/-! ## 3.  Run lengths -/

/-- **The quantiser cannot stay silent.**  In any window of `L` consecutive
ticks with `1 ≤ L t`, at least one bit is a one. -/
theorem ds_fires_within {t : ℝ} (ht0 : 0 ≤ t) (ht1 : t < 1) {n L : ℕ}
    (h : 1 ≤ (L : ℝ) * t) : ∃ i, n ≤ i ∧ i < n + L ∧ dsBit t i = 1 := by
  have hgt := dsWindow_gt ht0 ht1 n L
  have hpos : (0 : ℝ) < ((∑ i ∈ Finset.Ico n (n + L), (dsBit t i : ℤ) : ℤ) : ℝ) := by
    linarith
  have hposZ : 0 < ∑ i ∈ Finset.Ico n (n + L), (dsBit t i : ℤ) := by exact_mod_cast hpos
  by_contra hcon
  push_neg at hcon
  have hzero : ∀ i ∈ Finset.Ico n (n + L), (dsBit t i : ℤ) = 0 := by
    intro i hi
    rw [Finset.mem_Ico] at hi
    have hne := hcon i hi.1 hi.2
    have hle := dsBit_le_one t i
    have hz : dsBit t i = 0 := by omega
    simp [hz]
  rw [Finset.sum_congr rfl hzero] at hposZ
  simp at hposZ

/-- **A run of zeros is short.**  If the modulator emits nothing but zeros for
`L` consecutive ticks then `L t < 1`. -/
theorem ds_zero_run_lt {t : ℝ} (ht0 : 0 ≤ t) (ht1 : t < 1) {n L : ℕ}
    (h : ∀ i, n ≤ i → i < n + L → dsBit t i = 0) : (L : ℝ) * t < 1 := by
  by_contra hcon
  push_neg at hcon
  obtain ⟨i, hi1, hi2, hi3⟩ := ds_fires_within ht0 ht1 (n := n) hcon
  rw [h i hi1 hi2] at hi3
  exact zero_ne_one hi3

/-- The same bound in the form the studies quote it: a run of zeros is strictly
shorter than `1/t`, so the longest possible run is `⌈1/t⌉ - 1`. -/
theorem ds_zero_run_length_lt {t : ℝ} (ht0 : 0 < t) (ht1 : t < 1) {n L : ℕ}
    (h : ∀ i, n ≤ i → i < n + L → dsBit t i = 0) : (L : ℝ) < 1 / t := by
  have := ds_zero_run_lt ht0.le ht1 h
  rw [lt_div_iff₀ ht0]
  linarith

/-- **A run of ones is short.**  Dually, `L` consecutive ones force
`L (1 - t) < 1`. -/
theorem ds_one_run_lt {t : ℝ} (ht0 : 0 ≤ t) (ht1 : t < 1) {n L : ℕ}
    (h : ∀ i, n ≤ i → i < n + L → dsBit t i = 1) : (L : ℝ) * (1 - t) < 1 := by
  have hsum : ∑ i ∈ Finset.Ico n (n + L), (dsBit t i : ℤ) = (L : ℤ) := by
    have hone : ∀ i ∈ Finset.Ico n (n + L), (dsBit t i : ℤ) = 1 := by
      intro i hi
      rw [Finset.mem_Ico] at hi
      rw [h i hi.1 hi.2]
      norm_num
    rw [Finset.sum_congr rfl hone]
    simp
  have hlt := dsWindow_lt ht0 ht1 n L
  rw [hsum] at hlt
  push_cast at hlt
  nlinarith

/-- The dual length bound: a run of ones is strictly shorter than
`1/(1 - t)`. -/
theorem ds_one_run_length_lt {t : ℝ} (ht0 : 0 ≤ t) (ht1 : t < 1) {n L : ℕ}
    (h : ∀ i, n ≤ i → i < n + L → dsBit t i = 1) : (L : ℝ) < 1 / (1 - t) := by
  have hpos : 0 < 1 - t := by linarith
  have := ds_one_run_lt ht0 ht1 h
  rw [lt_div_iff₀ hpos]
  linarith

/-- **Below slope one half the ones are isolated.**  No two consecutive ticks
both fire, so every run of ones has length one. -/
theorem ds_no_adjacent_ones {t : ℝ} (ht0 : 0 ≤ t) (ht : t < 1 / 2) (n : ℕ) :
    dsBit t n = 0 ∨ dsBit t (n + 1) = 0 := by
  by_contra hcon
  push_neg at hcon
  obtain ⟨h1, h2⟩ := hcon
  have hb1 : dsBit t n = 1 := by
    have := dsBit_le_one t n
    omega
  have hb2 : dsBit t (n + 1) = 1 := by
    have := dsBit_le_one t (n + 1)
    omega
  have hrun : ∀ i, n ≤ i → i < n + 2 → dsBit t i = 1 := by
    intro i hi1 hi2
    rcases Nat.lt_or_ge i (n + 1) with hlt | hge
    · have : i = n := by omega
      subst this; exact hb1
    · have : i = n + 1 := by omega
      subst this; exact hb2
  have hbound := ds_one_run_lt ht0 (by linarith) hrun
  push_cast at hbound
  linarith

/-- The first bit of a stream of slope below one is a zero. -/
@[simp] lemma dsBit_zero_eq_zero {t : ℝ} (ht1 : t < 1) : dsBit t 0 = 0 := by
  unfold dsBit
  rw [dsState_zero, if_neg (by linarith)]

/-! ## 4.  Transitions and the mean run length -/

/-- The number of ticks in the first `N` at which the emitted bit changes.  The
number of maximal runs in a window differs from this by one, so it is the
quantity the studies' *mean run length* column inverts. -/
noncomputable def dsTransitions (t : ℝ) (N : ℕ) : ℕ :=
  ∑ i ∈ Finset.range N, (if dsBit t (i + 1) = dsBit t i then 0 else 1)

@[simp] lemma dsTransitions_zero (t : ℝ) : dsTransitions t 0 = 0 := by
  simp [dsTransitions]

/-- **The exact transition count.**  Below slope one half every one is isolated,
so each one contributes exactly two transitions and the count is
`2⌊N t⌋ + bit N`. -/
theorem dsTransitions_eq {t : ℝ} (ht0 : 0 ≤ t) (ht : t < 1 / 2) (N : ℕ) :
    dsTransitions t N = 2 * dsOnes t N + dsBit t N := by
  induction N with
  | zero => simp [dsBit_zero_eq_zero (by linarith : t < 1)]
  | succ k ih =>
      have hstep : dsTransitions t (k + 1)
          = dsTransitions t k + (if dsBit t (k + 1) = dsBit t k then 0 else 1) := by
        simp [dsTransitions, Finset.sum_range_succ]
      have hkey : (if dsBit t (k + 1) = dsBit t k then 0 else 1)
          = dsBit t k + dsBit t (k + 1) := by
        have hk := dsBit_le_one t k
        have hk1 := dsBit_le_one t (k + 1)
        rcases ds_no_adjacent_ones ht0 ht k with h | h
        · rw [h]; split_ifs with he <;> omega
        · rw [h]; split_ifs with he <;> omega
      rw [hstep, ih, hkey, dsOnes_succ]
      omega

/-- The transition count, as a real number, sits within `2` of `2 N t`. -/
lemma dsTransitions_sub_le {t : ℝ} (ht0 : 0 ≤ t) (ht : t < 1 / 2) (N : ℕ) :
    |(dsTransitions t N : ℝ) - 2 * N * t| ≤ 2 := by
  have hfloor : (dsOnes t N : ℤ) = ⌊(N : ℝ) * t⌋ :=
    dsOnes_eq_floor ht0 (by linarith) N
  have hR : (dsOnes t N : ℝ) = (⌊(N : ℝ) * t⌋ : ℝ) := by
    have hcast : ((dsOnes t N : ℤ) : ℝ) = ((⌊(N : ℝ) * t⌋ : ℤ) : ℝ) := by rw [hfloor]
    push_cast at hcast
    exact hcast
  have hle : (⌊(N : ℝ) * t⌋ : ℝ) ≤ (N : ℝ) * t := Int.floor_le _
  have hgt : (N : ℝ) * t - 1 < (⌊(N : ℝ) * t⌋ : ℝ) := Int.sub_one_lt_floor _
  have hb0 : (0 : ℝ) ≤ (dsBit t N : ℝ) := by positivity
  have hb1 : (dsBit t N : ℝ) ≤ 1 := by
    have := dsBit_le_one t N
    exact_mod_cast this
  have heq : (dsTransitions t N : ℝ) = 2 * (dsOnes t N : ℝ) + (dsBit t N : ℝ) := by
    rw [dsTransitions_eq ht0 ht N]
    push_cast
    ring
  rw [heq, hR, abs_le]
  constructor <;> linarith

/-- **The transition rate.**  Transitions per tick converge to `2t`: the
studies' "mean transitions per step". -/
theorem dsTransitions_rate_tendsto {t : ℝ} (ht0 : 0 ≤ t) (ht : t < 1 / 2) :
    Tendsto (fun N : ℕ => (dsTransitions t N : ℝ) / N) atTop (𝓝 (2 * t)) := by
  have hbound : ∀ N : ℕ, 0 < N → |(dsTransitions t N : ℝ) / N - 2 * t| ≤ 2 / N := by
    intro N hN
    have hNpos : (0 : ℝ) < N := by exact_mod_cast hN
    have hkey : (dsTransitions t N : ℝ) / N - 2 * t
        = ((dsTransitions t N : ℝ) - 2 * N * t) / N := by
      field_simp
    rw [hkey, abs_div, abs_of_pos hNpos]
    gcongr
    exact dsTransitions_sub_le ht0 ht N
  have h0 : Tendsto (fun N : ℕ => (2 : ℝ) / N) atTop (𝓝 0) := by
    simpa using tendsto_const_nhds.div_atTop (tendsto_natCast_atTop_atTop (R := ℝ))
  have hdiff : Tendsto (fun N : ℕ => (dsTransitions t N : ℝ) / N - 2 * t) atTop (𝓝 0) := by
    refine squeeze_zero_norm' ?_ h0
    filter_upwards [eventually_gt_atTop 0] with N hN
    simpa [Real.norm_eq_abs] using hbound N hN
  have := hdiff.add (tendsto_const_nhds : Tendsto (fun _ : ℕ => 2 * t) atTop (𝓝 (2 * t)))
  simpa using this

/-- **The mean run length.**  Ticks per transition converge to `1/(2t)` — the
studies' *mean run length* column, which is that formula and nothing else:
`1.5` at slope `1/3`, `1/(2(√2-1)) = 1.207…`, `1/(2(π-3)) = 3.53…`. -/
theorem dsMeanRunLength_tendsto {t : ℝ} (ht0 : 0 < t) (ht : t < 1 / 2) :
    Tendsto (fun N : ℕ => (N : ℝ) / dsTransitions t N) atTop (𝓝 (1 / (2 * t))) := by
  have hne : (2 : ℝ) * t ≠ 0 := by positivity
  have hinv := (dsTransitions_rate_tendsto ht0.le ht).inv₀ hne
  have hfun : ∀ N : ℕ, ((dsTransitions t N : ℝ) / N)⁻¹ = (N : ℝ) / dsTransitions t N := by
    intro N
    rw [inv_div]
  simpa [hfun, one_div] using hinv

/-! ## 5.  Wobble entropy

The studies report a "wobble Shannon entropy" in bits for each target, and — in
a different study, on an electrical oscillator — an "SNR is wobble entropy"
table.  Both are the binary entropy of the ones-density, so both are the single
function below evaluated at the density the loop is proved to produce. -/

/-- The binary entropy in **bits** (Mathlib's `Real.binEntropy` is in nats). -/
noncomputable def wobbleEntropy (p : ℝ) : ℝ := Real.binEntropy p / Real.log 2

lemma log_two_pos : 0 < Real.log 2 := Real.log_pos (by norm_num)

lemma log_two_ne_zero : Real.log 2 ≠ 0 := ne_of_gt log_two_pos

@[simp] lemma wobbleEntropy_zero : wobbleEntropy 0 = 0 := by simp [wobbleEntropy]

@[simp] lemma wobbleEntropy_one : wobbleEntropy 1 = 0 := by simp [wobbleEntropy]

/-- One bit per symbol at density one half, exactly. -/
@[simp] lemma wobbleEntropy_half : wobbleEntropy (1 / 2 : ℝ) = 1 := by
  have h : (1 / 2 : ℝ) = 2⁻¹ := by norm_num
  rw [wobbleEntropy, h, Real.binEntropy_two_inv]
  exact div_self log_two_ne_zero

lemma wobbleEntropy_one_sub (p : ℝ) : wobbleEntropy (1 - p) = wobbleEntropy p := by
  simp [wobbleEntropy]

lemma wobbleEntropy_nonneg {p : ℝ} (h0 : 0 ≤ p) (h1 : p ≤ 1) : 0 ≤ wobbleEntropy p :=
  div_nonneg (Real.binEntropy_nonneg h0 h1) log_two_pos.le

lemma wobbleEntropy_pos {p : ℝ} (h0 : 0 < p) (h1 : p < 1) : 0 < wobbleEntropy p :=
  div_pos (Real.binEntropy_pos h0 h1) log_two_pos

/-- **Zero entropy is a constant stream.**  The entropy of a density vanishes
exactly at the two pure densities. -/
theorem wobbleEntropy_eq_zero_iff {p : ℝ} : wobbleEntropy p = 0 ↔ p = 0 ∨ p = 1 := by
  rw [wobbleEntropy, div_eq_zero_iff]
  constructor
  · rintro (h | h)
    · exact Real.binEntropy_eq_zero.1 h
    · exact absurd h log_two_ne_zero
  · intro h
    exact Or.inl (Real.binEntropy_eq_zero.2 h)

/-- **At most one bit per symbol.** -/
theorem wobbleEntropy_le_one (p : ℝ) : wobbleEntropy p ≤ 1 := by
  rw [wobbleEntropy, div_le_one log_two_pos]
  exact Real.binEntropy_le_log_two

/-- **And exactly one bit only at density one half** — the `SNR = 0 dB` row of
the oscillator table. -/
theorem wobbleEntropy_eq_one_iff {p : ℝ} : wobbleEntropy p = 1 ↔ p = 1 / 2 := by
  rw [wobbleEntropy, div_eq_one_iff_eq log_two_ne_zero, Real.binEntropy_eq_log_two]
  constructor
  · intro h; rw [h]; norm_num
  · intro h; rw [h]; norm_num

@[fun_prop] lemma wobbleEntropy_continuous : Continuous wobbleEntropy :=
  Real.binEntropy_continuous.div_const _

/-- **Entropy falls strictly as the signal purifies.**  On densities above one
half — the regime of the oscillator's SNR sweep, where the loop mostly fires —
raising the density strictly lowers the entropy. -/
theorem wobbleEntropy_strictAntiOn_high :
    StrictAntiOn wobbleEntropy (Set.Icc (1 / 2 : ℝ) 1) := by
  intro a ha b hb hab
  have h : Real.binEntropy b < Real.binEntropy a := by
    refine Real.binEntropy_strictAntiOn ?_ ?_ hab
    · simpa [one_div] using ha
    · simpa [one_div] using hb
  simp only [wobbleEntropy]
  exact div_lt_div_of_pos_right h log_two_pos

/-! ## 6.  The stream's entropy, and resonance -/

/-- **The measured entropy converges to the target's.**  Running the loop and
taking the Shannon entropy of the observed ones-density — which is what the
studies do — converges to `wobbleEntropy t`. -/
theorem ds_wobbleEntropy_tendsto {t : ℝ} (ht0 : 0 ≤ t) (ht1 : t < 1) :
    Tendsto (fun N : ℕ => wobbleEntropy (dsAverage t N)) atTop (𝓝 (wobbleEntropy t)) :=
  (wobbleEntropy_continuous.tendsto t).comp (dsAverage_tendsto ht0 ht1)

/-- **Silence.**  For a target below one, zero entropy is exactly a stream that
never fires. -/
theorem ds_wobbleEntropy_zero_iff_silent {t : ℝ} (ht0 : 0 ≤ t) (ht1 : t < 1) :
    wobbleEntropy t = 0 ↔ ∀ n, dsBit t n = 0 := by
  constructor
  · intro h
    rcases wobbleEntropy_eq_zero_iff.1 h with h0 | h1
    · intro n
      subst h0
      exact dsBit_eq_zero_of_lt le_rfl (by simp)
    · exact absurd h1 (ne_of_lt ht1)
  · intro h
    have havg : ∀ N : ℕ, dsAverage t N = 0 := by
      intro N
      simp [dsAverage, h]
    have h1 : Tendsto (fun N : ℕ => dsAverage t N) atTop (𝓝 t) := dsAverage_tendsto ht0 ht1
    have h2 : Tendsto (fun N : ℕ => dsAverage t N) atTop (𝓝 0) := by
      simp only [havg]
      exact tendsto_const_nhds
    have : t = 0 := tendsto_nhds_unique h1 h2
    rw [this]
    simp

/-- **Lock-in at resonance.**  At gain exactly one the quantiser fires at every
tick. -/
theorem ds_resonance_lock (n : ℕ) : dsBit (1 : ℝ) n = 1 := by
  have hstate : ∀ m : ℕ, dsState (1 : ℝ) m = 0 := by
    intro m
    induction m with
    | zero => simp
    | succ k ih =>
        show (if 1 ≤ dsState (1 : ℝ) k + 1 then dsState (1 : ℝ) k + 1 - 1
              else dsState (1 : ℝ) k + 1) = 0
        rw [ih, if_pos (by norm_num)]
        norm_num
  unfold dsBit
  rw [hstate n, if_pos (by norm_num)]

/-- **Resonance is zero wobble entropy.**  The stream at gain one is constant,
its density is one, and its entropy is exactly zero — the sharp dip the
oscillator study measures. -/
theorem ds_resonance_entropy :
    (∀ n, dsBit (1 : ℝ) n = 1) ∧ wobbleEntropy 1 = 0 :=
  ⟨ds_resonance_lock, wobbleEntropy_one⟩

end GLM.Info
