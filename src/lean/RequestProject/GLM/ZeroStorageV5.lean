import RequestProject.GLM.ZeroStorage

/-!
# The zero-storage substrate, v5: the syndrome, the tracker, and the repair

`studies/scripts/glm_zero_storage_substrate_v5.py` closes the last corner of the
"generate, don't store" claim and adds a cost ledger.  Three of its
mechanisms are mathematical claims rather than engineering choices, and they
are proved here.

## §1 Membership is twelve parities, not a table

v4's membership test still consulted a 4096-entry set of codewords.  The
extended binary Golay code is *self-dual*, so the twelve generator rows are
also a parity-check matrix: `check j c` is the parity of `pop (c &&& row j)`,
and

* `synZero_of_isGolay` — a codeword passes all twelve checks;
* `isGolay_of_synZero` — a 24-bit word that passes all twelve checks is a
  codeword;
* `syndromeZero_iff_isGolay` — the two are equivalent, so the table can go;
* `syndromeSieve_iff_isLeech` — and the whole Leech membership test of the
  script (parity read off coordinate 0, twelve parity checks, one mod-8 sum)
  decides exactly `IsLeech`.

The proof of the hard direction is the systematic-encoder argument: subtract
the codeword carried by the low twelve bits, and what is left is a word with
no information bits whose syndrome vanishes — and the twelve-bit block matrix
is injective, which is a finite check.

## §2 The register tracks a moving target

`retarget` no longer zeroes the accumulator, so the register carries its phase
across a write.  The accumulator of a first-order loop stays in `[0,1)`
whatever the target schedule does (`dsAcc_mem_Ico`), which gives the exact
count identity `Σ bits = Σ targets − accumulator` (`dsAcc_eq`) and hence

* `ds_track_bound` — `|average − mean target| < 1/N`, for a *moving* target;
* `ds_track_moving_target` — against a fixed target the error picks up
  exactly the mean deviation of the trajectory.

## §3 One ±4 move is the cheapest repair

Inside a Construction-C coset the coordinates are independent and the only
coupling is the mod-8 sum, which flips exactly when the number of ±4 moves is
odd.  `coset_cost_ge` says no odd repair can beat the cheapest single move,
and `coset_repair_attained` says that move attains the minimum — which is why
the decoder of the script returns the true nearest point of each coset.

## §4 The decoder returns the nearest point of the lattice

§3 is the integer core; §4 states it for a rational target and closes the
remaining gap:

* `coset_min_cost` — no point of a Construction-C coset is closer to the
  target than the per-coordinate nearest point plus, when the mod-8 sum
  demands it, the cheapest single ±4 repair;
* `coset_min_attained` — and a point of the coset achieves exactly that;
* `leech_in_coset` — every Leech point lies in one of the 8,192 cosets, so
* `lattice_dist_ge` — a bound that holds on every coset holds on `Λ₂₄`.

Together: the decoder's minimum over the cosets is the distance to the
nearest lattice point, which v4 could only check empirically.
-/

namespace GLM.ZeroStorageV5

open GLM.LatticeShortcut

set_option maxRecDepth 40000

/-! ## §1 The syndrome -/

/-- The `j`-th parity check of a 24-bit word against the generator rows.
Because the code is self-dual, the generator rows are a parity-check matrix. -/
def check (j c : ℕ) : ℕ := pop (c &&& golayRows.getD j 0) % 2

/-- A word has zero syndrome when all twelve checks vanish. -/
def SynZero (c : ℕ) : Prop := ∀ j < 12, check j c = 0

/-- The parity checks are `𝔽₂`-linear. -/
theorem check_xor (j a b : ℕ) : check j (a ^^^ b) = (check j a + check j b) % 2 := by
  set r := golayRows.getD j 0 with hr
  have key : ∀ i ∈ Finset.range 24, bit ((a ^^^ b) &&& r) i % 2
      = (bit (a &&& r) i + bit (b &&& r) i) % 2 := by
    intro i _
    simp only [bit_eq_testBit, Nat.testBit_and, Nat.testBit_xor]
    cases a.testBit i <;> cases b.testBit i <;> cases r.testBit i <;> simp
  have h1 : pop ((a ^^^ b) &&& r) % 2 = (pop (a &&& r) + pop (b &&& r)) % 2 := by
    rw [pop, Finset.sum_nat_mod, Finset.sum_congr rfl key, ← Finset.sum_nat_mod,
      Finset.sum_add_distrib]
    rfl
  show pop ((a ^^^ b) &&& r) % 2 = (pop (a &&& r) % 2 + pop (b &&& r) % 2) % 2
  rw [h1, Nat.add_mod]

theorem check_zero (j : ℕ) : check j 0 = 0 := by
  simp [check, pop, bit]

/-- The `144` pairwise checks of the generator rows, decided by the kernel. -/
theorem rows_orthogonal :
    ((List.range 12).all fun i => (List.range 12).all fun j =>
      check j (golayRows.getD i 0) == 0) = true := by decide +kernel

/-- Every generator row passes every check: the code is self-dual. -/
theorem check_row (i j : ℕ) (hj : j < 12) : check j (golayRows.getD i 0) = 0 := by
  by_cases hi : i < 12
  · have h1 := List.all_eq_true.1 rows_orthogonal i (List.mem_range.mpr hi)
    have h2 := List.all_eq_true.1 h1 j (List.mem_range.mpr hj)
    simpa using h2
  · have hz : golayRows.getD i 0 = 0 := by
      refine List.getD_eq_default _ _ ?_
      simp [golayRows]
      omega
    rw [hz]
    exact check_zero j

/-- Every codeword has zero syndrome. -/
theorem check_encAux (j : ℕ) (hj : j < 12) :
    ∀ fuel jj m, check j (encAux fuel jj m) = 0 := by
  intro fuel
  induction fuel with
  | zero => intro jj m; rw [encAux]; exact check_zero j
  | succ f ih =>
    intro jj m
    rw [encAux, check_xor, ih (jj + 1) (m / 2)]
    have h1 : check j (if m % 2 = 1 then golayRows.getD jj 0 else 0) = 0 := by
      split
      · exact check_row jj j hj
      · exact check_zero j
    rw [h1]

theorem check_cw (j : ℕ) (hj : j < 12) (m : ℕ) : check j (cw m) = 0 :=
  check_encAux j hj 12 0 m

theorem synZero_of_isGolay {c : ℕ} (h : IsGolay c) : SynZero c := by
  obtain ⟨m, -, rfl⟩ := h
  exact fun j hj => check_cw j hj m

/-- The encoder is systematic: the low twelve bits of `cw m` are `m`. -/
theorem cw_low_bits :
    ((List.range 4096).all fun m => cw m % 4096 == m) = true := by decide +kernel

theorem cw_mod_4096 {m : ℕ} (hm : m < 4096) : cw m % 4096 = m := by
  have := List.all_eq_true.1 cw_low_bits m (List.mem_range.mpr hm)
  simpa using this

/-- The twelve-bit parity block is injective: a word with no information bits
and zero syndrome is zero. -/
theorem high_injective :
    ((List.range 4096).all fun h =>
      !((List.range 12).all fun j => check j (h * 4096) == 0) || h == 0) = true := by
  decide +kernel

theorem eq_zero_of_synZero_of_low {d : ℕ} (hd : d < 2 ^ 24) (hlow : d % 4096 = 0)
    (h : SynZero d) : d = 0 := by
  have hdiv : d = d / 4096 * 4096 := by omega
  have hlt : d / 4096 < 4096 := by omega
  have hall : ((List.range 12).all fun j => check j (d / 4096 * 4096) == 0) = true := by
    refine List.all_eq_true.2 fun j hj => ?_
    have := h j (List.mem_range.mp hj)
    rw [← hdiv]
    simpa using this
  have hmain := List.all_eq_true.1 high_injective (d / 4096) (List.mem_range.mpr hlt)
  rw [hall] at hmain
  simp at hmain
  omega

/-- **A word of zero syndrome is a codeword.** -/
theorem isGolay_of_synZero {c : ℕ} (hc : c < 2 ^ 24) (h : SynZero c) : IsGolay c := by
  have hm : c % 4096 < 4096 := Nat.mod_lt _ (by norm_num)
  have hcw : IsGolay (cw (c % 4096)) := ⟨c % 4096, hm, rfl⟩
  have hcwlt : cw (c % 4096) < 2 ^ 24 := golay_lt hcw
  have hdlt : c ^^^ cw (c % 4096) < 2 ^ 24 := Nat.xor_lt_two_pow hc hcwlt
  have hlow : (c ^^^ cw (c % 4096)) % 4096 = 0 := by
    have h12 : (4096 : ℕ) = 2 ^ 12 := by norm_num
    rw [h12, Nat.xor_mod_two_pow, ← h12, cw_mod_4096 hm, Nat.xor_self]
  have hsyn : SynZero (c ^^^ cw (c % 4096)) := by
    intro j hj
    rw [check_xor, h j hj, check_cw j hj]
  have hzero : c ^^^ cw (c % 4096) = 0 := eq_zero_of_synZero_of_low hdlt hlow hsyn
  have : c = cw (c % 4096) := Nat.xor_eq_zero_iff.mp hzero
  exact ⟨c % 4096, hm, this.symm⟩

/-- **The twelve parity checks decide the Golay code.**  This is what allows
the script to delete its 4096-word lookup: membership costs twelve
AND-popcount-parity operations against 36 bytes of generator, and when the
word is not a codeword the same twelve operations produce its syndrome. -/
theorem syndromeZero_iff_isGolay {c : ℕ} (hc : c < 2 ^ 24) : SynZero c ↔ IsGolay c :=
  ⟨isGolay_of_synZero hc, synZero_of_isGolay⟩

/-- The membership test of the v5 script, transcribed: the parity is read off
coordinate 0, every coordinate must match it mod 2, the coordinates congruent
to it mod 4 must have **zero Golay syndrome**, and the coordinate sum must be
`≡ 4m (mod 8)`. -/
def SyndromeSieve (x : Fin 24 → ℤ) : Prop :=
  (∀ i, (2 : ℤ) ∣ (x i - x 0 % 2)) ∧
    SynZero (maskOf fun i => decide ((4 : ℤ) ∣ (x i - x 0 % 2))) ∧
    (8 : ℤ) ∣ ((∑ i : Fin 24, x i) - 4 * (x 0 % 2))

/-- **The syndrome sieve decides exactly the Leech lattice.**  The companion of
`GLM.ZeroStorage.refinedSieve_iff_isLeech`, with the stored codeword table
replaced by twelve parity checks. -/
theorem syndromeSieve_iff_isLeech {x : Fin 24 → ℤ} : SyndromeSieve x ↔ IsLeech x := by
  rw [← GLM.ZeroStorage.refinedSieve_iff_isLeech]
  have hmask := maskOf_lt fun i => decide ((4 : ℤ) ∣ (x i - x 0 % 2))
  constructor
  · rintro ⟨h1, h2, h3⟩
    exact ⟨h1, isGolay_of_synZero hmask h2, h3⟩
  · rintro ⟨h1, h2, h3⟩
    exact ⟨h1, synZero_of_isGolay h2, h3⟩

/-! ## §2 The register with a moving target -/

/-- The accumulator of a first-order Δ-Σ loop after `n` ticks of the target
schedule `t`.  Retargeting is just a change of `t`: the accumulator is never
zeroed, which is the continuous-retargeting mode of the v5 register. -/
def dsAcc (t : ℕ → ℚ) : ℕ → ℚ
  | 0 => 0
  | n + 1 => if 1 ≤ dsAcc t n + t n then dsAcc t n + t n - 1 else dsAcc t n + t n

/-- The bit emitted at tick `n`. -/
def dsBit (t : ℕ → ℚ) (n : ℕ) : ℚ := if 1 ≤ dsAcc t n + t n then 1 else 0

/-- The accumulator never leaves `[0,1)`, whatever the target does. -/
theorem dsAcc_mem_Ico {t : ℕ → ℚ} (ht : ∀ n, 0 ≤ t n ∧ t n ≤ 1) (n : ℕ) :
    0 ≤ dsAcc t n ∧ dsAcc t n < 1 := by
  induction n with
  | zero => simp [dsAcc]
  | succ n ih =>
    obtain ⟨h0, h1⟩ := ih
    obtain ⟨ht0, ht1⟩ := ht n
    rw [dsAcc]
    split
    · next h => constructor <;> linarith
    · next h => constructor <;> [linarith; linarith [not_le.1 h]]

/-- One step of the loop: the accumulator absorbs exactly the discrepancy. -/
theorem dsAcc_succ (t : ℕ → ℚ) (n : ℕ) :
    dsAcc t (n + 1) = dsAcc t n + t n - dsBit t n := by
  rw [dsAcc, dsBit]
  split <;> ring

/-- **The count identity.**  The bits emitted differ from the targets asked for
by exactly the accumulator — no matter how often the target was rewritten. -/
theorem dsAcc_eq (t : ℕ → ℚ) (n : ℕ) :
    ∑ i ∈ Finset.range n, dsBit t i = ∑ i ∈ Finset.range n, t i - dsAcc t n := by
  induction n with
  | zero => simp [dsAcc]
  | succ n ih =>
    rw [Finset.sum_range_succ, Finset.sum_range_succ, ih]
    have h := dsAcc_succ t n
    linarith

/-- **The read-out bound survives a moving target.**  With continuous
retargeting the average of the stream is within `1/N` of the *mean* of the
targets held during the window. -/
theorem ds_track_bound {t : ℕ → ℚ} (ht : ∀ n, 0 ≤ t n ∧ t n ≤ 1) {n : ℕ} (hn : 0 < n) :
    |(∑ i ∈ Finset.range n, dsBit t i) / n - (∑ i ∈ Finset.range n, t i) / n|
      < 1 / n := by
  have hnQ : (0 : ℚ) < n := by exact_mod_cast hn
  obtain ⟨h0, h1⟩ := dsAcc_mem_Ico ht n
  have hsum := dsAcc_eq t n
  have : (∑ i ∈ Finset.range n, dsBit t i) / n - (∑ i ∈ Finset.range n, t i) / n
      = -(dsAcc t n) / n := by
    rw [hsum]; ring
  rw [this, abs_div, abs_of_pos hnQ, abs_neg, abs_of_nonneg h0]
  gcongr

/-- **Tracking a moving target.**  Against a fixed target `s` the error is the
read-out bound plus exactly the mean deviation of the trajectory from `s` —
the price of the target moving, and nothing else. -/
theorem ds_track_moving_target {t : ℕ → ℚ} (ht : ∀ n, 0 ≤ t n ∧ t n ≤ 1)
    {n : ℕ} (hn : 0 < n) (s : ℚ) :
    |(∑ i ∈ Finset.range n, dsBit t i) / n - s|
      ≤ 1 / n + (∑ i ∈ Finset.range n, |t i - s|) / n := by
  have hnQ : (0 : ℚ) < n := by exact_mod_cast hn
  have key : |(∑ i ∈ Finset.range n, dsBit t i) / n - (∑ i ∈ Finset.range n, t i) / n|
      < 1 / n := ds_track_bound ht hn
  have hdrift : |(∑ i ∈ Finset.range n, t i) / n - s|
      ≤ (∑ i ∈ Finset.range n, |t i - s|) / n := by
    have hcard : (∑ i ∈ Finset.range n, t i) - n * s
        = ∑ i ∈ Finset.range n, (t i - s) := by
      rw [Finset.sum_sub_distrib]
      simp [mul_comm]
    have : (∑ i ∈ Finset.range n, t i) / n - s
        = (∑ i ∈ Finset.range n, (t i - s)) / n := by
      field_simp
      linarith [hcard]
    rw [this, abs_div, abs_of_pos hnQ]
    gcongr
    exact Finset.abs_sum_le_sum_abs _ _
  calc |(∑ i ∈ Finset.range n, dsBit t i) / n - s|
      ≤ |(∑ i ∈ Finset.range n, dsBit t i) / n - (∑ i ∈ Finset.range n, t i) / n|
        + |(∑ i ∈ Finset.range n, t i) / n - s| := abs_sub_le _ _ _
    _ ≤ 1 / n + (∑ i ∈ Finset.range n, |t i - s|) / n := by
        exact add_le_add key.le hdrift

/-! ## §3 The cheapest ±4 repair -/

/-- Moving a coordinate off its nearest class member never helps: with the
residual `a` at most half the class spacing, any nonzero multiple of `4`
costs at least as much as the corresponding single step. -/
theorem quad_step_bound {a k : ℤ} (ha : |a| ≤ 2) (hk : k ≠ 0) :
    min ((a + 4) ^ 2) ((a - 4) ^ 2) ≤ (a + 4 * k) ^ 2 := by
  have h2 : -2 ≤ a := neg_le_of_abs_le ha
  have h3 : a ≤ 2 := le_of_abs_le ha
  rcases lt_trichotomy k 0 with hlt | heq | hgt
  · have hk1 : k ≤ -1 := by omega
    refine le_trans (min_le_right _ _) ?_
    nlinarith
  · exact absurd heq hk
  · have hk1 : 1 ≤ k := hgt
    refine le_trans (min_le_left _ _) ?_
    nlinarith

/-- Staying put is optimal coordinate by coordinate. -/
theorem quad_zero_bound {a k : ℤ} (ha : |a| ≤ 2) : a ^ 2 ≤ (a + 4 * k) ^ 2 := by
  have h2 : -2 ≤ a := neg_le_of_abs_le ha
  have h3 : a ≤ 2 := le_of_abs_le ha
  rcases lt_trichotomy k 0 with hlt | heq | hgt
  · have hk1 : k ≤ -1 := by omega
    nlinarith
  · simp [heq]
  · have hk1 : 1 ≤ k := hgt
    nlinarith

/-- The penalty of the cheapest single ±4 move on coordinate `i`. -/
def penalty (a : Fin 24 → ℤ) (i : Fin 24) : ℤ :=
  min ((a i + 4) ^ 2) ((a i - 4) ^ 2) - (a i) ^ 2

/-- **No odd repair beats the cheapest single move.**  If the mod-8 sum forces
an odd number of ±4 moves, the cost is at least the unconstrained cost plus
the smallest single-move penalty. -/
theorem coset_cost_ge {a k : Fin 24 → ℤ} (ha : ∀ i, |a i| ≤ 2)
    (hodd : ¬ (2 ∣ ∑ i, k i)) :
    (∑ i, (a i) ^ 2) + (Finset.univ.inf' Finset.univ_nonempty (penalty a))
      ≤ ∑ i, (a i + 4 * k i) ^ 2 := by
  obtain ⟨j, hj⟩ : ∃ j, k j ≠ 0 := by
    by_contra h
    push_neg at h
    exact hodd (by simp [h])
  have hsplit : ∀ f : Fin 24 → ℤ,
      ∑ i, f i = f j + ∑ i ∈ Finset.univ.erase j, f i := by
    intro f
    rw [Finset.add_sum_erase _ _ (Finset.mem_univ j)]
  have h1 : ∑ i ∈ Finset.univ.erase j, (a i) ^ 2
      ≤ ∑ i ∈ Finset.univ.erase j, (a i + 4 * k i) ^ 2 :=
    Finset.sum_le_sum fun i _ => quad_zero_bound (ha i)
  have hp : penalty a j = min ((a j + 4) ^ 2) ((a j - 4) ^ 2) - (a j) ^ 2 := rfl
  have h2 : (a j) ^ 2 + penalty a j ≤ (a j + 4 * k j) ^ 2 := by
    have := quad_step_bound (ha j) hj
    rw [hp]; linarith
  have h3 : Finset.univ.inf' Finset.univ_nonempty (penalty a) ≤ penalty a j :=
    Finset.inf'_le _ (Finset.mem_univ j)
  rw [hsplit fun i => (a i) ^ 2, hsplit fun i => (a i + 4 * k i) ^ 2]
  linarith

/-- **And that move attains it.**  Some single ±4 move realises the bound, so
the decoder's "cheapest repair" really is the minimum over the coset. -/
theorem coset_repair_attained (a : Fin 24 → ℤ) :
    ∃ k : Fin 24 → ℤ, ¬ (2 ∣ ∑ i, k i) ∧
      ∑ i, (a i + 4 * k i) ^ 2
        = (∑ i, (a i) ^ 2) + (Finset.univ.inf' Finset.univ_nonempty (penalty a)) := by
  obtain ⟨j, -, hj⟩ :=
    Finset.exists_mem_eq_inf' (Finset.univ_nonempty (α := Fin 24)) (penalty a)
  classical
  set s : ℤ := if (a j + 4) ^ 2 ≤ (a j - 4) ^ 2 then 1 else -1 with hs
  refine ⟨fun i => if i = j then s else 0, ?_, ?_⟩
  · have hsum : ∑ i, (if i = j then s else 0) = s := by simp
    rw [hsum, hs]
    split <;> decide
  · have hsplit : ∀ f : Fin 24 → ℤ,
        ∑ i, f i = f j + ∑ i ∈ Finset.univ.erase j, f i := by
      intro f
      rw [Finset.add_sum_erase _ _ (Finset.mem_univ j)]
    have hzero : ∑ i ∈ Finset.univ.erase j,
        (a i + 4 * (if i = j then s else 0)) ^ 2
          = ∑ i ∈ Finset.univ.erase j, (a i) ^ 2 :=
      Finset.sum_congr rfl fun i hi => by
        rw [if_neg (Finset.ne_of_mem_erase hi)]; ring
    have hstep : (a j + 4 * s) ^ 2 = (a j) ^ 2 + penalty a j := by
      have hp : penalty a j = min ((a j + 4) ^ 2) ((a j - 4) ^ 2) - (a j) ^ 2 := rfl
      rw [hp, hs]
      split
      · next h => rw [min_eq_left h]; ring
      · next h => rw [min_eq_right (not_le.1 h).le]; ring
    rw [hsplit fun i => (a i + 4 * (if i = j then s else 0)) ^ 2,
      hsplit fun i => (a i) ^ 2, hzero, if_pos rfl, hstep, hj]
    ring

/-! ## §4 The coset decoder returns the nearest point

The two lemmas above are the integer core.  This section carries them to the
statement the script actually relies on: for a *rational* target, the point the
decoder builds inside a Construction-C coset is the nearest point of that
coset, and the 8,192 cosets exhaust `Λ₂₄`, so the winner over them is the
nearest lattice point. -/

/-- A Construction-C coset: every coordinate is confined to a residue class
mod 4, and the coordinate sum is pinned mod 8. -/
def InCoset (r : Fin 24 → ℤ) (s : ℤ) (x : Fin 24 → ℤ) : Prop :=
  (∀ i, (4 : ℤ) ∣ (x i - r i)) ∧ (8 : ℤ) ∣ ((∑ i, x i) - s)

/-- The residue pattern of the coset named by a parity `m` and a codeword `c`:
coordinate `i` sits in class `m` mod 4 when `i ∈ c`, and in class `m + 2`
otherwise. -/
def cosetRes (m : ℤ) (c : ℕ) (i : Fin 24) : ℤ :=
  if bit c (i : ℕ) = 1 then m else m + 2

/-- Squared distance from a rational target to an integer point. -/
def dist2 (y : Fin 24 → ℚ) (x : Fin 24 → ℤ) : ℚ := ∑ i, ((x i : ℚ) - y i) ^ 2

/-- The penalty of the cheapest single ±4 move at coordinate `i`, measured from
the per-coordinate nearest point `n`. -/
def penaltyQ (y : Fin 24 → ℚ) (n : Fin 24 → ℤ) (i : Fin 24) : ℚ :=
  min (((n i : ℚ) + 4 - y i) ^ 2) (((n i : ℚ) - 4 - y i) ^ 2) - ((n i : ℚ) - y i) ^ 2

/-- Staying put is optimal coordinate by coordinate, over `ℚ`. -/
theorem quadQ_zero_bound {a : ℚ} (ha : |a| ≤ 2) (k : ℤ) : a ^ 2 ≤ (a + 4 * k) ^ 2 := by
  rw [abs_le] at ha
  rcases lt_trichotomy k 0 with hk | hk | hk
  · have : (k : ℚ) ≤ -1 := by exact_mod_cast (by omega : k ≤ -1)
    nlinarith [ha.1, ha.2]
  · simp [hk]
  · have : (1 : ℚ) ≤ k := by exact_mod_cast hk
    nlinarith [ha.1, ha.2]

/-- No nonzero multiple of 4 beats the cheapest single ±4 step, over `ℚ`. -/
theorem quadQ_step_bound {a : ℚ} (ha : |a| ≤ 2) {k : ℤ} (hk : k ≠ 0) :
    min ((a + 4) ^ 2) ((a - 4) ^ 2) ≤ (a + 4 * k) ^ 2 := by
  rw [abs_le] at ha
  rcases lt_or_gt_of_ne hk with h | h
  · have hk1 : (k : ℚ) ≤ -1 := by exact_mod_cast (by omega : k ≤ -1)
    refine le_trans (min_le_right _ _) ?_
    nlinarith [ha.1, ha.2]
  · have hk1 : (1 : ℚ) ≤ k := by exact_mod_cast h
    refine le_trans (min_le_left _ _) ?_
    nlinarith [ha.1, ha.2]

/-- Splitting a sum over `Fin 24` at one index. -/
theorem sum_split_at {M : Type*} [AddCommMonoid M] (j : Fin 24) (f : Fin 24 → M) :
    ∑ i, f i = f j + ∑ i ∈ Finset.univ.erase j, f i :=
  (Finset.add_sum_erase _ _ (Finset.mem_univ j)).symm

/-- **The decoder's point is the nearest point of its coset.**  If `n` is a
per-coordinate nearest member of the coset's residue classes — each residual at
most half the class spacing — then no point of the coset is closer than `n`,
plus the cheapest single ±4 repair when the mod-8 sum forces one. -/
theorem coset_min_cost {y : Fin 24 → ℚ} {r : Fin 24 → ℤ} {s : ℤ} {n x : Fin 24 → ℤ}
    (hn : ∀ i, (4 : ℤ) ∣ (n i - r i)) (hres : ∀ i, |(n i : ℚ) - y i| ≤ 2)
    (hx : InCoset r s x) :
    dist2 y n + (if (8 : ℤ) ∣ (∑ i, n i) - s then 0
        else Finset.univ.inf' Finset.univ_nonempty (penaltyQ y n))
      ≤ dist2 y x := by
  obtain ⟨hxr, hxs⟩ := hx
  have hdvd : ∀ i, (4 : ℤ) ∣ (x i - n i) := fun i => by
    have := dvd_sub (hxr i) (hn i)
    simpa using this
  choose k hk using fun i => (hdvd i)
  have hxi : ∀ i, x i = n i + 4 * k i := fun i => by have := hk i; omega
  have hcast : ∀ i, ((x i : ℚ) - y i) = ((n i : ℚ) - y i) + 4 * (k i : ℚ) := by
    intro i
    rw [hxi i]
    push_cast
    ring
  have hterm : dist2 y x = ∑ i, (((n i : ℚ) - y i) + 4 * (k i : ℚ)) ^ 2 :=
    Finset.sum_congr rfl fun i _ => by rw [hcast i]
  by_cases hs : (8 : ℤ) ∣ (∑ i, n i) - s
  · rw [if_pos hs, add_zero, hterm]
    exact Finset.sum_le_sum fun i _ => quadQ_zero_bound (hres i) (k i)
  · rw [if_neg hs, hterm]
    -- the mod-8 sum forces an odd number of ±4 moves
    have hsumx : (∑ i, x i) = (∑ i, n i) + 4 * ∑ i, k i := by
      rw [Finset.mul_sum, ← Finset.sum_add_distrib]
      exact Finset.sum_congr rfl fun i _ => hxi i
    have hodd : ¬ (2 : ℤ) ∣ ∑ i, k i := by
      intro he
      obtain ⟨u, hu⟩ := he
      obtain ⟨v, hv⟩ := hxs
      exact hs ⟨v - u, by rw [hsumx, hu] at hv; omega⟩
    obtain ⟨j, hj⟩ : ∃ j, k j ≠ 0 := by
      by_contra h
      push_neg at h
      exact hodd ⟨0, by simp [h]⟩
    have h1 : ∑ i ∈ Finset.univ.erase j, ((n i : ℚ) - y i) ^ 2
        ≤ ∑ i ∈ Finset.univ.erase j, (((n i : ℚ) - y i) + 4 * (k i : ℚ)) ^ 2 :=
      Finset.sum_le_sum fun i _ => quadQ_zero_bound (hres i) (k i)
    have hp : penaltyQ y n j
        = min (((n j : ℚ) - y j + 4) ^ 2) (((n j : ℚ) - y j - 4) ^ 2)
          - ((n j : ℚ) - y j) ^ 2 := by
      unfold penaltyQ
      ring_nf
    have h2 : ((n j : ℚ) - y j) ^ 2 + penaltyQ y n j
        ≤ (((n j : ℚ) - y j) + 4 * (k j : ℚ)) ^ 2 := by
      have := quadQ_step_bound (a := (n j : ℚ) - y j) (hres j) hj
      rw [hp]; linarith
    have h3 : Finset.univ.inf' Finset.univ_nonempty (penaltyQ y n) ≤ penaltyQ y n j :=
      Finset.inf'_le _ (Finset.mem_univ j)
    rw [dist2, sum_split_at j fun i => ((n i : ℚ) - y i) ^ 2,
      sum_split_at j fun i => (((n i : ℚ) - y i) + 4 * (k i : ℚ)) ^ 2]
    linarith

/-- **And that minimum is attained inside the coset.**  When the sum condition
is already met, `n` itself is in the coset; otherwise a single ±4 move both
repairs the sum and realises the cheapest penalty. -/
theorem coset_min_attained {y : Fin 24 → ℚ} {r : Fin 24 → ℤ} {s : ℤ} {n : Fin 24 → ℤ}
    (hn : ∀ i, (4 : ℤ) ∣ (n i - r i)) (hcompat : (4 : ℤ) ∣ (∑ i, n i) - s) :
    ∃ x, InCoset r s x ∧
      dist2 y x = dist2 y n + (if (8 : ℤ) ∣ (∑ i, n i) - s then 0
        else Finset.univ.inf' Finset.univ_nonempty (penaltyQ y n)) := by
  by_cases hs : (8 : ℤ) ∣ (∑ i, n i) - s
  · exact ⟨n, ⟨hn, hs⟩, by rw [if_pos hs, add_zero]⟩
  · obtain ⟨j, -, hj⟩ :=
      Finset.exists_mem_eq_inf' (Finset.univ_nonempty (α := Fin 24)) (penaltyQ y n)
    classical
    set e : ℚ := (n j : ℚ) - y j with he
    set sg : ℤ := if (e + 4) ^ 2 ≤ (e - 4) ^ 2 then 1 else -1 with hsg
    refine ⟨fun i => if i = j then n i + 4 * sg else n i, ⟨?_, ?_⟩, ?_⟩
    · intro i
      by_cases hij : i = j
      · subst hij
        simp only [ite_true]
        have := hn i
        omega
      · simp only [if_neg hij]
        exact hn i
    · have hsum : (∑ i, if i = j then n i + 4 * sg else n i) = (∑ i, n i) + 4 * sg := by
        rw [sum_split_at j fun i => if i = j then n i + 4 * sg else n i,
          sum_split_at j fun i => n i, if_pos rfl]
        have : ∑ i ∈ Finset.univ.erase j, (if i = j then n i + 4 * sg else n i)
            = ∑ i ∈ Finset.univ.erase j, n i :=
          Finset.sum_congr rfl fun i hi => by rw [if_neg (Finset.ne_of_mem_erase hi)]
        rw [this]; ring
      rw [hsum]
      obtain ⟨u, hu⟩ := hcompat
      obtain ⟨w, hw⟩ : ∃ w, u = 2 * w + 1 := by
        rcases Int.even_or_odd u with ⟨v, hv⟩ | ⟨v, hv⟩
        · exact absurd ⟨v, by omega⟩ hs
        · exact ⟨v, hv⟩
      have hsg2 : sg = 1 ∨ sg = -1 := by
        rw [hsg]; split
        · exact Or.inl rfl
        · exact Or.inr rfl
      rcases hsg2 with h | h
      · exact ⟨w + 1, by rw [h]; omega⟩
      · exact ⟨w, by rw [h]; omega⟩
    · rw [if_neg hs, dist2, dist2,
        sum_split_at j fun i => (((if i = j then n i + 4 * sg else n i : ℤ) : ℚ) - y i) ^ 2,
        sum_split_at j fun i => ((n i : ℚ) - y i) ^ 2]
      have hrest : ∑ i ∈ Finset.univ.erase j,
          (((if i = j then n i + 4 * sg else n i : ℤ) : ℚ) - y i) ^ 2
          = ∑ i ∈ Finset.univ.erase j, ((n i : ℚ) - y i) ^ 2 :=
        Finset.sum_congr rfl fun i hi => by rw [if_neg (Finset.ne_of_mem_erase hi)]
      have hstep : (((if j = j then n j + 4 * sg else n j : ℤ) : ℚ) - y j) ^ 2
          = ((n j : ℚ) - y j) ^ 2 + penaltyQ y n j := by
        rw [if_pos rfl]
        have hpq : penaltyQ y n j = min ((e + 4) ^ 2) ((e - 4) ^ 2) - e ^ 2 := by
          unfold penaltyQ; rw [he]; ring_nf
        rw [hpq, hsg]
        split
        · next h =>
            rw [min_eq_left h, he]
            push_cast
            ring
        · next h =>
            rw [min_eq_right (not_le.1 h).le, he]
            push_cast
            ring
      rw [hrest, hstep, hj]
      ring

/-! ### The cosets exhaust the lattice -/

/-- **Every Leech point lies in one of the 8,192 cosets.**  The parity is read
off coordinate 0 and the codeword is the mod-4 mask — the same two data the
sieve computes. -/
theorem leech_in_coset {x : Fin 24 → ℤ} (h : IsLeech x) :
    ∃ m : ℤ, (m = 0 ∨ m = 1) ∧ ∃ c : ℕ, IsGolay c ∧ c < 2 ^ 24 ∧
      InCoset (cosetRes m c) (4 * m) x := by
  obtain ⟨m, hm, h2, hgol, h8⟩ := h
  refine ⟨m, hm, maskOf fun i => decide ((4 : ℤ) ∣ (x i - m)), hgol, maskOf_lt _, ?_, h8⟩
  intro i
  have hb := bit_maskOf (fun i => decide ((4 : ℤ) ∣ (x i - m))) i
  by_cases hd : (4 : ℤ) ∣ (x i - m)
  · simp only [cosetRes, hb, hd, decide_true]
    exact hd
  · have hbit : bit (maskOf fun i => decide ((4 : ℤ) ∣ (x i - m))) (i : ℕ) = 0 := by
      rw [hb]; simp [hd]
    simp only [cosetRes, hbit]
    norm_num
    obtain ⟨u, hu⟩ := h2 i
    rcases Int.even_or_odd u with ⟨v, hv⟩ | ⟨v, hv⟩
    · exact absurd ⟨v, by omega⟩ hd
    · exact ⟨v, by omega⟩

/-- The hypotheses above are satisfiable, and on a coset that really occurs:
the all-twos vector lies in the coset named by parity 0 and the zero codeword,
and is a Leech point. -/
theorem allTwos_inCoset : InCoset (cosetRes 0 0) (4 * 0) (fun _ => (2 : ℤ)) := by
  refine ⟨fun i => ?_, ?_⟩
  · simp [cosetRes, bit]
  · simp [Finset.sum_const]

/-- **A lower bound that holds on every coset holds on the whole lattice.**
This is the exhaustion half of the decoder's global optimality: the decoder
minimises over the 8,192 cosets, and nothing in `Λ₂₄` escapes them. -/
theorem lattice_dist_ge {y : Fin 24 → ℚ} {best : ℚ}
    (h : ∀ m : ℤ, (m = 0 ∨ m = 1) → ∀ c : ℕ, IsGolay c → c < 2 ^ 24 →
      ∀ z : Fin 24 → ℤ, InCoset (cosetRes m c) (4 * m) z → best ≤ dist2 y z)
    {x : Fin 24 → ℤ} (hx : IsLeech x) : best ≤ dist2 y x := by
  obtain ⟨m, hm, c, hc, hc24, hin⟩ := leech_in_coset hx
  exact h m hm c hc hc24 x hin

end GLM.ZeroStorageV5
