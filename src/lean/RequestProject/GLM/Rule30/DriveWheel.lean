module

public import RequestProject.GLM.Rule30.TestCountPeriods
public import RequestProject.GLM.Rule30.AmortizedHalving

/-!
# Round 36: the drive wheel — the whole family of periodic drives as one object

The half-line machine of Round 21 is driven by a periodic column.  Rounds 21–35 treated the
drives **one period and one word at a time** (period 2, then 3, then 4, …; for each period every
non-white word `0 < k < 2^p`).  Most of that work repeats itself, because the drives form a
*wheel*:

* **turning the wheel** — reading the same periodic column from a later phase `s` gives the word
  `wheelTurn p k s`; its drive is the old drive started `s` steps later (`driveN_wheelTurn`);
  turns compose (`wheelTurn_add`) and `p` turns are the identity (`wheelTurn_mod`);
* **one turn changes nothing that matters** — a word kills every half-line iff each of its turns
  does (`wordDies_wheelTurn_iff`); on the observer's clock a turn costs at most `2` slack per step
  (`testSlack_wheelTurn`);
* **smaller wheels inside** — a word whose drive repeats after `g ∣ p` steps *is* a word of
  period `g` (`driveN_eq_of_period`); periods combine by `gcd` (`period_gcd`).

So each wheel (necklace) needs one representative, and only the **primitive** wheels: the
representative `WheelRep p k` is the least turn of a word with no smaller period (a Lyndon word,
read as a binary number with the first time in bit `0`).

* **`wordDies_of_wheelReps`** — if every representative of every period `q ∣ p` kills every
  half-line, then every non-white word of period `p` does.
* **`halfLineDies_iff_wheel`** — `HalfLineDies p` ⟺ the representatives of the divisors of `p`
  kill every half-line.
* **`WheelDies`** — the single statement "every primitive wheel kills every non-empty half-line";
  **`wheelDies_iff`**: it is equivalent to `HalfLineDies p` for every period;
  **`problem1_of_wheelDies`**: it implies Problem 1;
  **`wheelDies_iff_periodic`**: it is the statement "every periodic non-white drive kills every
  non-empty half-line" (no reference to words, periods or phases).
* **`testCountLinear_of_wheel`** — on the observer's clock: a slack `c` for the representatives
  of the divisors of `p` gives `TestCountLinear p (c + 2 (p - 1))`.

All results use only the standard axioms.  The finite tables (how many representatives each
period has) are in `DriveWheelData.lean`.
-/

@[expose] public section

namespace GLM.Rule30

/-! ## Periodic sequences -/

/-- `bd` repeats after `a` steps. -/
def HasPeriod (bd : ℕ → Bool) (a : ℕ) : Prop := ∀ t, bd (t + a) = bd t

theorem HasPeriod.mul {bd : ℕ → Bool} {a : ℕ} (h : HasPeriod bd a) (m : ℕ) :
    HasPeriod bd (a * m) := fun t => drive_periodic_mul h t m

theorem HasPeriod.mod {bd : ℕ → Bool} {a b : ℕ} (ha : HasPeriod bd a) (hb : HasPeriod bd b) :
    HasPeriod bd (b % a) := by
  intro t
  have h := hb t
  rw [← Nat.mod_add_div b a, ← Nat.add_assoc, ha.mul] at h
  exact h

/-- **Periods combine by `gcd`.** -/
theorem period_gcd {bd : ℕ → Bool} {a b : ℕ} (ha : HasPeriod bd a) (hb : HasPeriod bd b) :
    HasPeriod bd (Nat.gcd a b) := by
  induction a, b using Nat.gcd.induction with
  | H0 n => simpa using hb
  | H1 m n _ ih =>
    rw [Nat.gcd_rec]
    exact ih (ha.mod hb) ha

theorem HasPeriod.eq_mod {bd : ℕ → Bool} {g : ℕ} (h : HasPeriod bd g) (t : ℕ) :
    bd t = bd (t % g) := by
  conv_lhs => rw [← Nat.mod_add_div t g]
  rw [h.mul]

/-- **A drive that repeats after `g` steps is the drive of its first `g` values.** -/
theorem driveN_eq_of_period {bd : ℕ → Bool} {g : ℕ} (hg : 0 < g) (h : HasPeriod bd g) :
    bd = driveN g (bitsOf bd g) := by
  funext t
  rw [driveN, testBit_bitsOf, h.eq_mod t]
  simp [Nat.mod_lt t hg]

theorem driveN_hasPeriod (p k : ℕ) : HasPeriod (driveN p k) p := driveN_periodic k

/-! ## Turning the wheel -/

/-- **One turn of the wheel**: the period word read from phase `s`. -/
def wheelTurn (p k s : ℕ) : ℕ := bitsOf (fun t => driveN p k (t + s)) p

theorem wheelTurn_lt (p k s : ℕ) : wheelTurn p k s < 2 ^ p := bitsOf_lt _ _

/-- The turned word drives the machine like the old one started `s` steps later. -/
theorem driveN_wheelTurn {p : ℕ} (hp : 0 < p) (k s : ℕ) :
    driveN p (wheelTurn p k s) = fun t => driveN p k (t + s) := by
  have hper : HasPeriod (fun t => driveN p k (t + s)) p := fun t => by
    simp only
    rw [show t + p + s = t + s + p by ring, driveN_periodic]
  exact (driveN_eq_of_period hp hper).symm

/-- Turns compose. -/
theorem wheelTurn_add {p : ℕ} (hp : 0 < p) (k a b : ℕ) :
    wheelTurn p (wheelTurn p k a) b = wheelTurn p k (a + b) := by
  show bitsOf (fun t => driveN p (wheelTurn p k a) (t + b)) p = _
  rw [driveN_wheelTurn hp, wheelTurn]
  congr 1
  funext t
  show driveN p k (t + b + a) = _
  rw [Nat.add_assoc, Nat.add_comm b a]

/-- `p` turns are the identity. -/
theorem wheelTurn_mod (p : ℕ) (k s : ℕ) : wheelTurn p k s = wheelTurn p k (s % p) := by
  unfold wheelTurn
  congr 1
  funext t
  have h := (driveN_hasPeriod p k).eq_mod (t + s)
  have h' := (driveN_hasPeriod p k).eq_mod (t + s % p)
  rw [h, h', Nat.add_mod_mod]

theorem wheelTurn_zero {p k : ℕ} (hk : k < 2 ^ p) : wheelTurn p k 0 = k := by
  apply Nat.eq_of_testBit_eq
  intro i
  rw [wheelTurn, testBit_bitsOf, driveN, Nat.add_zero]
  by_cases hi : i < p
  · simp [hi, Nat.mod_eq_of_lt hi]
  · have : k.testBit i = false :=
      Nat.testBit_eq_false_of_lt (lt_of_lt_of_le hk (Nat.pow_le_pow_right (by norm_num) (by omega)))
    simp [hi, this]

/-- A turned word is non-white iff the word is. -/
theorem wheelTurn_pos {p k : ℕ} (hp : 0 < p) (hk0 : 0 < k) (hk : k < 2 ^ p) (s : ℕ) :
    0 < wheelTurn p k s := by
  rw [Nat.pos_iff_ne_zero]
  intro h0
  have hback := wheelTurn_add hp k s (p - s % p)
  rw [h0, wheelTurn_mod p k (s + (p - s % p)), show (s + (p - s % p)) % p = 0 by
    have h1 := Nat.mod_add_div s p
    have h2 := Nat.mod_lt s hp
    rw [show s + (p - s % p) = p * (s / p + 1) by rw [Nat.mul_add]; omega]
    exact Nat.mul_mod_right _ _, wheelTurn_zero hk] at hback
  have hz : wheelTurn p 0 (p - s % p) = 0 := by
    apply Nat.eq_of_testBit_eq
    intro i
    simp [wheelTurn, testBit_bitsOf, driveN]
  omega

/-- **A turn changes nothing about dying.** -/
theorem wordDies_wheelTurn_iff {p : ℕ} (hp : 0 < p) (k s : ℕ) :
    WordDies (driveN p (wheelTurn p k s)) ↔ WordDies (driveN p k) := by
  rw [driveN_wheelTurn hp]
  exact wordDies_shift_iff_of_periodic hp (driveN_periodic k) s

/-! ## Wheel representatives -/

/-- **A wheel representative of period `p`**: a non-white word that is the least of its turns and
is primitive (no proper turn returns it).  In word language: a Lyndon word of length `p` other
than `0`, with time `0` in bit `0`. -/
def WheelRep (p k : ℕ) : Prop :=
  0 < k ∧ k < 2 ^ p ∧ (∀ s < p, k ≤ wheelTurn p k s) ∧ ∀ s < p, 0 < s → wheelTurn p k s ≠ k

instance (p k : ℕ) : Decidable (WheelRep p k) := by
  unfold WheelRep; infer_instance

/-- A non-white word has a black time inside its period. -/
theorem exists_black_of_pos {p k : ℕ} (hk0 : 0 < k) (hk : k < 2 ^ p) :
    ∃ i < p, driveN p k i = true := by
  obtain ⟨i, hi⟩ : ∃ i, k.testBit i = true := by
    by_contra h
    push_neg at h
    have : k = 0 := Nat.eq_of_testBit_eq fun i => by simpa using h i
    omega
  have hip : i < p := by
    by_contra hge
    rw [Nat.testBit_eq_false_of_lt
      (lt_of_lt_of_le hk (Nat.pow_le_pow_right (by norm_num) (by omega)))] at hi
    exact Bool.noConfusion hi
  exact ⟨i, hip, by simp [driveN, Nat.mod_eq_of_lt hip, hi]⟩

/-- The word of a periodic drive with a black cell is non-white. -/
theorem bitsOf_pos_of_black {bd : ℕ → Bool} {g t : ℕ} (hg0 : 0 < g) (hg : HasPeriod bd g)
    (ht : bd t = true) : 0 < bitsOf bd g := by
  rw [Nat.pos_iff_ne_zero]
  intro h0
  have := testBit_bitsOf bd g (t % g)
  rw [h0, Nat.zero_testBit, ← hg.eq_mod, ht] at this
  simp [Nat.mod_lt t hg0] at this

/-- **Every non-white word reduces to a wheel representative of a divisor period.** -/
theorem exists_wheelRep (p : ℕ) (hp : 0 < p) (k : ℕ) (hk0 : 0 < k) (hk : k < 2 ^ p) :
    ∃ q j s, 0 < q ∧ q ∣ p ∧ WheelRep q j ∧ driveN q j = fun t => driveN p k (t + s) := by
  induction p using Nat.strong_induction_on generalizing k with
  | _ p ih =>
  obtain ⟨s₀, hs₀, hmin⟩ : ∃ s₀ < p, ∀ s < p, wheelTurn p k s₀ ≤ wheelTurn p k s := by
    have hne : (Finset.range p).Nonempty := ⟨0, by simp [hp]⟩
    obtain ⟨s₀, hs, hm⟩ := Finset.exists_min_image (Finset.range p) (wheelTurn p k) hne
    exact ⟨s₀, Finset.mem_range.1 hs, fun s hs' => hm s (Finset.mem_range.2 hs')⟩
  have hk₀0 := wheelTurn_pos hp hk0 hk s₀
  have hk₀ := wheelTurn_lt p k s₀
  have hmin₀ : ∀ s < p, wheelTurn p k s₀ ≤ wheelTurn p (wheelTurn p k s₀) s := fun s _ => by
    rw [wheelTurn_add hp, wheelTurn_mod p k (s₀ + s)]; exact hmin _ (Nat.mod_lt _ hp)
  by_cases hprim : ∀ s < p, 0 < s → wheelTurn p (wheelTurn p k s₀) s ≠ wheelTurn p k s₀
  · exact ⟨p, _, s₀, hp, dvd_rfl, ⟨hk₀0, hk₀, hmin₀, hprim⟩, driveN_wheelTurn hp k s₀⟩
  · push_neg at hprim
    obtain ⟨s, hs, hs0, heq⟩ := hprim
    have hper_s : HasPeriod (driveN p (wheelTurn p k s₀)) s := by
      intro t
      have := congrFun (driveN_wheelTurn hp (wheelTurn p k s₀) s) t
      rw [heq] at this
      exact this.symm
    have hg := period_gcd hper_s (driveN_hasPeriod p (wheelTurn p k s₀))
    have hgp : Nat.gcd s p ∣ p := Nat.gcd_dvd_right s p
    have hg0 : 0 < Nat.gcd s p := Nat.gcd_pos_of_pos_right s hp
    have hglt : Nat.gcd s p < p := lt_of_le_of_lt (Nat.gcd_le_left p hs0) hs
    have hbd := driveN_eq_of_period hg0 hg
    obtain ⟨i, -, hi⟩ := exists_black_of_pos hk₀0 hk₀
    have hj0 := bitsOf_pos_of_black hg0 hg hi
    obtain ⟨q, j', s', hq, hqg, hj', he⟩ := ih _ hglt hg0 _ hj0 (bitsOf_lt _ _)
    refine ⟨q, j', s' + s₀, hq, dvd_trans hqg hgp, hj', ?_⟩
    rw [he, ← hbd]
    funext t
    rw [driveN_wheelTurn hp]
    simp only [Nat.add_assoc]

/-- **The wheel reduction.**  If every representative of every period `q ∣ p` kills every
non-empty half-line, so does every non-white word of period `p`. -/
theorem wordDies_of_wheelReps {p : ℕ} (hp : 0 < p)
    (h : ∀ q, 0 < q → q ∣ p → ∀ j, WheelRep q j → WordDies (driveN q j)) :
    ∀ k, 0 < k → k < 2 ^ p → WordDies (driveN p k) := by
  intro k hk0 hk
  obtain ⟨q, j, s, hq, hqp, hj, he⟩ := exists_wheelRep p hp k hk0 hk
  have := h q hq hqp j hj
  rw [he] at this
  exact (wordDies_shift_iff_of_periodic hp (driveN_periodic k) s).1 this

/-- **`HalfLineDies p` is a statement about the primitive wheels of the divisors of `p`.** -/
theorem halfLineDies_iff_wheel {p : ℕ} (hp : 0 < p) :
    HalfLineDies p ↔ ∀ q, 0 < q → q ∣ p → ∀ j, WheelRep q j → WordDies (driveN q j) := by
  refine ⟨fun h q hq hqp j hj => ?_, fun h => wordDies_of_wheelReps hp h⟩
  exact halfLineDies_of_dvd hqp hp h j hj.1 hj.2.1

/-- **The full wheel**: every primitive wheel, of every period, kills every non-empty half-line. -/
def WheelDies : Prop := ∀ q j, 0 < q → WheelRep q j → WordDies (driveN q j)

theorem wheelDies_iff : WheelDies ↔ ∀ p, 0 < p → HalfLineDies p := by
  constructor
  · intro h p hp
    exact (halfLineDies_iff_wheel hp).2 fun q hq _ j hj => h q j hq hj
  · intro h q j hq hj
    exact h q hq j hj.1 hj.2.1

/-- **The full wheel settles Problem 1.** -/
theorem problem1_of_wheelDies (h : WheelDies) : Problem1 :=
  problem1_of_halfLineDies (wheelDies_iff.1 h)

/-- **The full wheel without words**: every periodic drive with a black cell kills every
non-empty half-line. -/
theorem wheelDies_iff_periodic :
    WheelDies ↔ ∀ bd : ℕ → Bool, (∃ p, 0 < p ∧ HasPeriod bd p) → (∃ t, bd t = true) →
      WordDies bd := by
  constructor
  · rintro h bd ⟨p, hp, hper⟩ ⟨t, ht⟩
    have hbd := driveN_eq_of_period hp hper
    rw [hbd]
    exact wheelDies_iff.1 h p hp _ (bitsOf_pos_of_black hp hper ht) (bitsOf_lt _ _)
  · intro h q j hq hj
    obtain ⟨i, -, hi⟩ := exists_black_of_pos hj.1 hj.2.1
    exact h _ ⟨q, hq, driveN_hasPeriod q j⟩ ⟨i, hi⟩

/-! ## The wheel on the observer's clock -/

theorem testSlack_mono {bd : ℕ → Bool} {c c' : ℕ} (hc : c ≤ c') (h : TestSlack bd c) :
    TestSlack bd c' := by
  intro d S hd h1 h2
  obtain ⟨t, hb, hn, hf⟩ := h d S hd h1 h2
  exact ⟨t, hb, by omega, hf⟩

/-- **A turn on the observer's clock.**  A slack `c` for a word gives slack `c + 2 (p - 1)` for
each of its turns. -/
theorem testSlack_wheelTurn {p : ℕ} (hp : 0 < p) {k c : ℕ} (h : TestSlack (driveN p k) c)
    (s : ℕ) : TestSlack (driveN p (wheelTurn p k s)) (c + 2 * (p - 1)) := by
  rw [wheelTurn_mod, driveN_wheelTurn hp]
  have hs := Nat.mod_lt s hp
  rcases Nat.eq_zero_or_pos (s % p) with h0 | hpos
  · rw [h0]
    simpa using testSlack_mono (by omega) h
  · apply testSlack_mono (show c + 2 * (p - s % p) ≤ c + 2 * (p - 1) by omega)
    apply testSlack_of_shift_iter _ c (p - s % p)
    have : (fun u => (fun t => driveN p k (t + s % p)) (u + (p - s % p))) = driveN p k := by
      funext u
      simp only
      rw [show u + (p - s % p) + s % p = u + p by omega, driveN_periodic]
    rw [this]
    exact h

/-- **The wheel reduction on the observer's clock.**  A slack `c` for the representatives of
the divisors of `p` gives the per-period law with slack `c + 2 (p - 1)`. -/
theorem testCountLinear_of_wheel {p c : ℕ} (hp : 0 < p)
    (h : ∀ q, 0 < q → q ∣ p → ∀ j, WheelRep q j → TestSlack (driveN q j) c) :
    TestCountLinear p (c + 2 * (p - 1)) := by
  intro k hk0 hk
  obtain ⟨q, j, s, hq, hqp, hj, he⟩ := exists_wheelRep p hp k hk0 hk
  have hdrive : driveN p k = driveN q (wheelTurn q j (p * s - s)) := by
    rw [driveN_wheelTurn hq, he]
    funext u
    have hs : s ≤ p * s := Nat.le_mul_of_pos_left s hp
    simp only
    rw [show u + (p * s - s) + s = u + p * s by omega, drive_periodic_mul (driveN_periodic k)]
  rw [hdrive]
  exact testSlack_mono (by have := Nat.le_of_dvd hp hqp; omega)
    (testSlack_wheelTurn hq (h q hq hqp j hj) _)

/-! ## The wheel on a finite range of code lengths

The same reduction for certificates: a turn by `m` steps lengthens every code by `m` cells
(`halfStep_length`), so a representative certified on code lengths `≤ D + (p - 1)` covers every
turn on code lengths `≤ D`. -/

/-- The slack of one drive, for the code lengths `1 ≤ d ≤ D`. -/
def TestSlackUpTo (bd : ℕ → Bool) (c D : ℕ) : Prop :=
  ∀ d S, 1 ≤ d → d ≤ D → 2 ^ (d - 1) ≤ S → S < 2 ^ d → FailsWithinTests bd S (d + c)

theorem testSlackUpTo_mono {bd : ℕ → Bool} {c c' D D' : ℕ} (hc : c ≤ c') (hD : D' ≤ D)
    (h : TestSlackUpTo bd c D) : TestSlackUpTo bd c' D' := by
  intro d S hd hdD h1 h2
  obtain ⟨t, hb, hn, hf⟩ := h d S hd (by omega) h1 h2
  exact ⟨t, hb, by omega, hf⟩

/-- One step of phase on a finite range. -/
theorem testSlackUpTo_of_shift {bd : ℕ → Bool} {c D : ℕ}
    (h : TestSlackUpTo (fun u => bd (u + 1)) c (D + 1)) : TestSlackUpTo bd (c + 2) D := by
  intro d S hd hdD h1 h2
  obtain ⟨l1, l2⟩ := halfStep_length (b := bd 0) hd h1 h2
  obtain ⟨t, hb, hn, hf⟩ := failsWithinTests_of_shift (h (d + 1) (halfStep (bd 0) S) (by omega)
    (by omega) (by simpa using l1) l2)
  refine ⟨t, hb, ?_, hf⟩
  have : (bd 0).toNat ≤ 1 := by cases bd 0 <;> simp
  omega

/-- `s` steps of phase on a finite range. -/
theorem testSlackUpTo_of_shift_iter (bd : ℕ → Bool) (c s D : ℕ)
    (h : TestSlackUpTo (fun u => bd (u + s)) c (D + s)) : TestSlackUpTo bd (c + 2 * s) D := by
  induction s generalizing c D with
  | zero => simpa using h
  | succ s ih =>
    have h' : TestSlackUpTo (fun u => (fun u => bd (u + s)) (u + 1)) c (D + s + 1) := by
      simpa [Nat.add_assoc, Nat.add_comm 1 s] using h
    have := ih (c + 2) D (testSlackUpTo_of_shift h')
    rwa [show c + 2 + 2 * s = c + 2 * (s + 1) by ring] at this

/-- **A turn on a finite range.** -/
theorem testSlackUpTo_wheelTurn {p : ℕ} (hp : 0 < p) {k c D : ℕ}
    (h : TestSlackUpTo (driveN p k) c (D + (p - 1))) (s : ℕ) :
    TestSlackUpTo (driveN p (wheelTurn p k s)) (c + 2 * (p - 1)) D := by
  rw [wheelTurn_mod, driveN_wheelTurn hp]
  have hs := Nat.mod_lt s hp
  rcases Nat.eq_zero_or_pos (s % p) with h0 | hpos
  · rw [h0]
    simpa using testSlackUpTo_mono (by omega) (by omega) h
  · apply testSlackUpTo_mono (show c + 2 * (p - s % p) ≤ c + 2 * (p - 1) by omega) le_rfl
    apply testSlackUpTo_of_shift_iter _ c (p - s % p)
    have : (fun u => (fun t => driveN p k (t + s % p)) (u + (p - s % p))) = driveN p k := by
      funext u
      simp only
      rw [show u + (p - s % p) + s % p = u + p by omega, driveN_periodic]
    rw [this]
    exact testSlackUpTo_mono le_rfl (by omega) h

/-- **The wheel reduction for certificates.**  Slack `c` for the representatives of the
divisors of `p` on code lengths `≤ D + (p - 1)` gives slack `c + 2 (p - 1)` for every non-white
word of period `p` on code lengths `≤ D`. -/
theorem testSlackUpTo_of_wheel {p c D : ℕ} (hp : 0 < p)
    (h : ∀ q, 0 < q → q ∣ p → ∀ j, WheelRep q j → TestSlackUpTo (driveN q j) c (D + (p - 1))) :
    ∀ k, 0 < k → k < 2 ^ p → TestSlackUpTo (driveN p k) (c + 2 * (p - 1)) D := by
  intro k hk0 hk
  obtain ⟨q, j, s, hq, hqp, hj, he⟩ := exists_wheelRep p hp k hk0 hk
  have hdrive : driveN p k = driveN q (wheelTurn q j (p * s - s)) := by
    rw [driveN_wheelTurn hq, he]
    funext u
    have hs : s ≤ p * s := Nat.le_mul_of_pos_left s hp
    simp only
    rw [show u + (p * s - s) + s = u + p * s by omega, drive_periodic_mul (driveN_periodic k)]
  have hqle := Nat.le_of_dvd hp hqp
  rw [hdrive]
  exact testSlackUpTo_mono (by omega) le_rfl (testSlackUpTo_wheelTurn hq
    (testSlackUpTo_mono le_rfl (by omega) (h q hq hqp j hj)) _)

end GLM.Rule30
