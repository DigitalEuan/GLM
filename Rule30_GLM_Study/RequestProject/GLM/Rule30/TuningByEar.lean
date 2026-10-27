module

public import RequestProject.GLM.Rule30.PowerSeriesLadder

/-!
# Round 25: tuning by ear — iterative, pruned search for the law behind a sequence

The question of the round (the user's input): *if we do not know the axiom at the fundamental
level and cannot sweep for it by brute force, can we iterate through plausible symbol arrangements,
pruning and directing, looping the resolution closer and closer — like tuning a note by ear?*

This file makes that loop exact and proves what it can and cannot do.

## Part 1: the general loop (any family of candidate laws)

A *candidate law* `h : H` predicts a sequence `pred h : ℕ → Bool`.  Listening to the first `n`
values of the true sequence `s` **prunes** every candidate that disagrees with them
(`Survives pred s n h`).  The theorems, for every family:

* `pruned_forever` — pruning is permanent: a wrong note heard once is never un-heard.
* `survives_of_eq` — pruning is sound: the true law (if present) is never pruned.
* `eq_of_survives_all` — surviving all listening is the same as being exactly right.
* `finite_lockIn` — **a finite family locks in**: after a finite time every survivor is exactly
  right (or nothing survives).  This is how rows `0..4` single out wheel 30 among all 256
  (`Observer.lean`).
* `graded_settles_iff` — **graded families**: when candidates have sizes with finitely many of
  each size, the size needed to stay consistent stays bounded iff the true law is in the family.
* `tuneIndex_eventually` — **directed search over an infinite enumerated family**: the loop
  "take the first surviving candidate" settles for ever on a correct law, provided some candidate
  in the enumeration is correct (identification in the limit).
* `tuneIndex_diverges` — if no candidate is correct, the guess drifts for ever: every fixed
  initial block of candidates is eventually pruned for good.
* `no_finite_confirmation` — **no finite amount of listening confirms a candidate**: for every
  `n` and every `h` there is a sequence agreeing with `s` on the first `n` values that `h` gets
  wrong.  The loop can refute, never certify; it does not know *when* it has converged.

## Part 2: the periodic instrument and Problem 1

The family of eventually periodic laws, directed by size (Occam): `tuneCost s n` is the least
`τ + p` (transient plus period, `p ≥ 1`) of a periodic law consistent with the first `n` values.
It is the "pitch error" of the best tune after `n` notes.

* `tuneCost_mono`, `tuneCost_le_succ`, `tuneCost_le_of_periodFits` — basic behaviour.
* `tuneCost_congr` — it only depends on the first `n` values (it is a listening quantity).
* `periodic_of_tuneCost_bounded` — **the compactness step**: if every prefix admits a tune of
  size `≤ B`, a single tune of size `≤ B` is exactly right.
* `resolution_iff` — **each resolution level is decided by finite listening**: "no eventual period
  with `τ + p ≤ B`" holds iff some prefix forces `tuneCost > B`.
* `eventuallyPeriodic_iff_tuneCostBounded`, **`problem1_iff_tuneCost_unbounded`** — Problem 1 is
  exactly the statement that the tuning loop never settles: the resolution climbs for ever.
* `lcProfile_le_tuneCost` — the linear-recurrence instrument (Berlekamp–Massey, Round 23) is at
  least as fine as the periodic one.
* `TuneExcessBound`, `problem1_of_tuneExcessBound` — the *excess* `n − tuneCost s n` is the
  number of notes the best periodic tune actually predicts beyond what it memorises.  Any
  sublinear bound on the excess implies Problem 1.  The certificates are in `TuningByEarData.lean`.

All results here use only the standard axioms.
-/

@[expose] public section

namespace GLM.Rule30

open Finset

/-! ## Part 1: the general loop -/

section General

variable {H : Type*}

/-- Two sequences agree on the first `n` values. -/
def Agrees (f g : ℕ → Bool) (n : ℕ) : Prop := ∀ i < n, f i = g i

instance (f g : ℕ → Bool) (n : ℕ) : Decidable (Agrees f g n) := by
  unfold Agrees; infer_instance

theorem Agrees.mono {f g : ℕ → Bool} {n m : ℕ} (h : Agrees f g n) (hm : m ≤ n) :
    Agrees f g m := fun i hi => h i (by omega)

/-- Candidate `h` survives the first `n` notes of `s`. -/
def Survives (pred : H → ℕ → Bool) (s : ℕ → Bool) (n : ℕ) (h : H) : Prop :=
  Agrees (pred h) s n

/-- **Pruning is permanent.** -/
theorem pruned_forever {pred : H → ℕ → Bool} {s : ℕ → Bool} {n m : ℕ} {h : H}
    (hpr : ¬ Survives pred s n h) (hm : n ≤ m) : ¬ Survives pred s m h :=
  fun hs => hpr (Agrees.mono hs hm)

/-- **Pruning is sound**: the true law is never pruned. -/
theorem survives_of_eq {pred : H → ℕ → Bool} {s : ℕ → Bool} {h : H} (hh : pred h = s) (n : ℕ) :
    Survives pred s n h := fun i _ => by rw [hh]

/-- Surviving every amount of listening is the same as being exactly right. -/
theorem eq_of_survives_all {pred : H → ℕ → Bool} {s : ℕ → Bool} {h : H}
    (hh : ∀ n, Survives pred s n h) : pred h = s :=
  funext fun i => hh (i + 1) i (by omega)

/-- A wrong candidate is pruned at some finite time. -/
theorem exists_pruned {pred : H → ℕ → Bool} {s : ℕ → Bool} {h : H} (hh : pred h ≠ s) :
    ∃ n, ¬ Survives pred s n h := by
  by_contra hc
  push_neg at hc
  exact hh (eq_of_survives_all hc)

/-- **A finite family locks in**: after some finite time every surviving candidate is exactly
right (if no candidate is right, nothing survives). -/
theorem finite_lockIn [Finite H] (pred : H → ℕ → Bool) (s : ℕ → Bool) :
    ∃ N, ∀ h, Survives pred s N h → pred h = s := by
  classical
  have := Fintype.ofFinite H
  let t : H → ℕ := fun h => if hh : pred h = s then 0 else Classical.choose (exists_pruned hh)
  refine ⟨Finset.univ.sup t, fun h hs => ?_⟩
  by_contra hh
  have hle : t h ≤ Finset.univ.sup t := Finset.le_sup (Finset.mem_univ h)
  have ht : t h = Classical.choose (exists_pruned hh) := by simp [t, hh]
  exact pruned_forever (Classical.choose_spec (exists_pruned hh)) (ht ▸ hle) hs

/-- **Graded families: the loop settles iff the true law is in the family.** Give every candidate
a size, with only finitely many candidates of each size.  Then "some prefix-consistent candidate
of size `≤ B` exists after every amount of listening" (the resolution needed stays bounded) holds
for some `B` iff some candidate is exactly right.  So if the true law is not in the family, the
size of the best consistent candidate climbs past every bound. -/
theorem graded_settles_iff (pred : H → ℕ → Bool) (size : H → ℕ)
    (hfin : ∀ B, Set.Finite {h | size h ≤ B}) (s : ℕ → Bool) :
    (∃ B, ∀ n, ∃ h, size h ≤ B ∧ Survives pred s n h) ↔ ∃ h, pred h = s := by
  constructor
  · rintro ⟨B, hB⟩
    have : Finite {h | size h ≤ B} := (hfin B).to_subtype
    obtain ⟨N, hN⟩ := finite_lockIn (fun h : {h | size h ≤ B} => pred h.1) s
    obtain ⟨h, hsz, hs⟩ := hB N
    exact ⟨h, hN ⟨h, hsz⟩ hs⟩
  · rintro ⟨h, hh⟩
    exact ⟨size h, fun n => ⟨h, le_rfl, survives_of_eq hh n⟩⟩

open Classical in
/-- **The directed loop over an enumerated family** `e : ℕ → H`: after `n` notes, guess the first
candidate among `e 0, …, e (n-1)` that survives (or `none`). -/
noncomputable def tuneIndex (pred : H → ℕ → Bool) (e : ℕ → H) (s : ℕ → Bool) (n : ℕ) :
    Option ℕ :=
  if hx : ∃ k, k < n ∧ Survives pred s n (e k) then some (Nat.find hx) else none

/-- **Identification in the limit.** If some candidate in the enumeration is exactly right, the
directed loop settles, after finitely many notes, for ever on one exactly right candidate. -/
theorem tuneIndex_eventually {pred : H → ℕ → Bool} {e : ℕ → H} {s : ℕ → Bool}
    (hex : ∃ k, pred (e k) = s) :
    ∃ k₀, pred (e k₀) = s ∧ ∃ N, ∀ n ≥ N, tuneIndex pred e s n = some k₀ := by
  classical
  let k₀ := Nat.find hex
  have hk₀ : pred (e k₀) = s := Nat.find_spec hex
  have hwrong : ∀ j < k₀, pred (e j) ≠ s := fun j hj => Nat.find_min hex hj
  let t : ℕ → ℕ := fun j => if hj : pred (e j) = s then 0 else
    Classical.choose (exists_pruned hj)
  refine ⟨k₀, hk₀, max (k₀ + 1) ((range k₀).sup t), fun n hn => ?_⟩
  have hx : ∃ k, k < n ∧ Survives pred s n (e k) :=
    ⟨k₀, by omega, survives_of_eq hk₀ n⟩
  unfold tuneIndex
  rw [dif_pos hx]
  congr 1
  rw [Nat.find_eq_iff]
  refine ⟨⟨by omega, survives_of_eq hk₀ n⟩, fun j hj ⟨_, hs⟩ => ?_⟩
  have hjw := hwrong j hj
  have hle : t j ≤ (range k₀).sup t := Finset.le_sup (Finset.mem_range.2 hj)
  have ht : t j = Classical.choose (exists_pruned hjw) := by simp [t, hjw]
  exact pruned_forever (Classical.choose_spec (exists_pruned hjw)) (by omega) hs

/-- **Without a correct candidate the guess drifts for ever**: every fixed block
`e 0, …, e K` is eventually pruned for good. -/
theorem tuneIndex_diverges {pred : H → ℕ → Bool} {e : ℕ → H} {s : ℕ → Bool}
    (hno : ∀ k, pred (e k) ≠ s) (K : ℕ) :
    ∃ N, ∀ n ≥ N, ∀ k ≤ K, tuneIndex pred e s n ≠ some k := by
  classical
  let t : ℕ → ℕ := fun j => Classical.choose (exists_pruned (hno j))
  refine ⟨(range (K + 1)).sup t, fun n hn k hk hkn => ?_⟩
  unfold tuneIndex at hkn
  split_ifs at hkn with hx
  · have hkk := Option.some.inj hkn
    have hs := (Nat.find_spec hx).2
    rw [hkk] at hs
    have hle : t k ≤ (range (K + 1)).sup t := Finset.le_sup (Finset.mem_range.2 (by omega))
    have htk : t k = Classical.choose (exists_pruned (hno k)) := rfl
    exact pruned_forever (Classical.choose_spec (exists_pruned (hno k))) (by omega) hs

/-- **No finite confirmation.** For every amount of listening `n` and every candidate `h`, some
sequence agrees with `s` on the first `n` notes and is not `pred h`.  So the loop can refute
candidates, but no finite stage can confirm one. -/
theorem no_finite_confirmation (pred : H → ℕ → Bool) (s : ℕ → Bool) (n : ℕ) (h : H) :
    ∃ s' : ℕ → Bool, Agrees s' s n ∧ pred h ≠ s' := by
  refine ⟨fun i => if i = n then !pred h n else s i, fun i hi => by simp [show i ≠ n by omega],
    fun heq => ?_⟩
  have := congrFun heq n
  simp at this

end General

/-! ## Part 2: the periodic instrument -/

/-- The tune "transient `τ`, period `p`" is consistent with the first `n` notes of `s`. -/
def PeriodFits (s : ℕ → Bool) (τ p n : ℕ) : Prop :=
  ∀ i < n, τ ≤ i → i + p < n → s (i + p) = s i

instance (s : ℕ → Bool) (τ p n : ℕ) : Decidable (PeriodFits s τ p n) := by
  unfold PeriodFits; infer_instance

theorem PeriodFits.mono {s : ℕ → Bool} {τ p n m : ℕ} (h : PeriodFits s τ p n) (hm : m ≤ n) :
    PeriodFits s τ p m := fun i _ h1 h2 => h i (by omega) h1 (by omega)

/-- Some tune of size exactly `c` (`τ < c`, period `c - τ ≥ 1`) fits the first `n` notes. -/
def CostFits (s : ℕ → Bool) (n c : ℕ) : Prop := ∃ τ, τ < c ∧ PeriodFits s τ (c - τ) n

instance (s : ℕ → Bool) (n c : ℕ) : Decidable (CostFits s n c) := by
  unfold CostFits; infer_instance

theorem costFits_succ (s : ℕ → Bool) (n : ℕ) : CostFits s n (n + 1) :=
  ⟨n, by omega, fun i _ h1 h2 => by omega⟩

/-- **The best periodic tune after `n` notes**: the least `τ + p` (`p ≥ 1`) of an eventually
periodic law consistent with the first `n` values of `s`. -/
def tuneCost (s : ℕ → Bool) (n : ℕ) : ℕ := Nat.find ⟨n + 1, costFits_succ s n⟩

theorem tuneCost_spec (s : ℕ → Bool) (n : ℕ) : CostFits s n (tuneCost s n) :=
  Nat.find_spec ⟨n + 1, costFits_succ s n⟩

theorem tuneCost_le_succ (s : ℕ → Bool) (n : ℕ) : tuneCost s n ≤ n + 1 :=
  Nat.find_min' _ (costFits_succ s n)

theorem tuneCost_le_of_periodFits {s : ℕ → Bool} {τ p n : ℕ} (hp : 0 < p)
    (h : PeriodFits s τ p n) : tuneCost s n ≤ τ + p :=
  Nat.find_min' _ ⟨τ, by omega, by rwa [show τ + p - τ = p by omega]⟩

theorem costFits_mono {s : ℕ → Bool} {n m c : ℕ} (h : CostFits s n c) (hm : m ≤ n) :
    CostFits s m c := by
  obtain ⟨τ, hτ, hf⟩ := h
  exact ⟨τ, hτ, hf.mono hm⟩

/-- More listening never lowers the pitch error. -/
theorem tuneCost_mono (s : ℕ → Bool) : Monotone (tuneCost s) := by
  intro m n hmn
  exact Nat.find_mono (fun c hc => costFits_mono hc hmn)

theorem periodFits_congr {s s' : ℕ → Bool} {τ p n : ℕ} (hag : Agrees s s' n)
    (h : PeriodFits s τ p n) : PeriodFits s' τ p n := fun i hi h1 h2 => by
  rw [← hag i hi, ← hag (i + p) h2]; exact h i hi h1 h2

/-- `tuneCost s n` depends only on the first `n` notes. -/
theorem tuneCost_congr {s s' : ℕ → Bool} {n : ℕ} (hag : Agrees s s' n) :
    tuneCost s n = tuneCost s' n := by
  have hag' : Agrees s' s n := fun i hi => (hag i hi).symm
  apply le_antisymm
  · obtain ⟨τ, hτ, hf⟩ := tuneCost_spec s' n
    exact Nat.find_min' _ ⟨τ, hτ, periodFits_congr hag' hf⟩
  · obtain ⟨τ, hτ, hf⟩ := tuneCost_spec s n
    exact Nat.find_min' _ ⟨τ, hτ, periodFits_congr hag hf⟩

/-- An exact eventual period is a tune that fits every prefix. -/
theorem periodFits_of_periodic {s : ℕ → Bool} {τ p : ℕ} (h : ∀ i ≥ τ, s (i + p) = s i)
    (n : ℕ) : PeriodFits s τ p n := fun i _ h1 _ => h i h1

/-- A tune that fits every prefix is an exact eventual period. -/
theorem periodic_of_periodFits_all {s : ℕ → Bool} {τ p : ℕ} (h : ∀ n, PeriodFits s τ p n) :
    ∀ i ≥ τ, s (i + p) = s i := fun i hi => h (i + p + 1) i (by omega) hi (by omega)

/-- **The compactness step.** If every prefix admits a tune of size `≤ B`, then one single tune of
size `≤ B` is an exact eventual period. -/
theorem periodic_of_tuneCost_bounded {s : ℕ → Bool} {B : ℕ} (hB : ∀ n, tuneCost s n ≤ B) :
    ∃ τ p, 0 < p ∧ τ + p ≤ B ∧ ∀ i ≥ τ, s (i + p) = s i := by
  classical
  by_contra hno
  push_neg at hno
  -- every tune of size `≤ B` is refuted by some prefix
  have hfail : ∀ x : ℕ × ℕ, ∃ n, x.1 < x.2 → x.2 ≤ B → ¬ PeriodFits s x.1 (x.2 - x.1) n := by
    intro x
    by_cases hx : x.1 < x.2 ∧ x.2 ≤ B
    · obtain ⟨i, hi, hne⟩ := hno x.1 (x.2 - x.1) (by omega) (by omega)
      exact ⟨i + (x.2 - x.1) + 1, fun _ _ hf => hne (hf i (by omega) hi (by omega))⟩
    · exact ⟨0, fun h1 h2 => absurd ⟨h1, h2⟩ hx⟩
  let t : ℕ × ℕ → ℕ := fun x => Classical.choose (hfail x)
  let M := ((range (B + 1)) ×ˢ (range (B + 1))).sup t
  obtain ⟨τ, hτ, hf⟩ := tuneCost_spec s M
  have hc := hB M
  have hmem : (τ, tuneCost s M) ∈ (range (B + 1)) ×ˢ (range (B + 1)) := by
    simp only [mem_product, mem_range]; omega
  have hle : t (τ, tuneCost s M) ≤ M := Finset.le_sup hmem
  exact Classical.choose_spec (hfail (τ, tuneCost s M)) hτ hc (hf.mono hle)

/-- **Each resolution level is decided by finite listening.** There is no eventual period with
`τ + p ≤ B` iff some finite prefix forces every consistent tune to have size `> B`. -/
theorem resolution_iff (s : ℕ → Bool) (B : ℕ) :
    (∀ τ p, 0 < p → τ + p ≤ B → ¬ ∀ i ≥ τ, s (i + p) = s i) ↔ ∃ n, B < tuneCost s n := by
  constructor
  · intro h
    by_contra hc
    push_neg at hc
    obtain ⟨τ, p, hp, hle, hper⟩ := periodic_of_tuneCost_bounded hc
    exact h τ p hp hle hper
  · rintro ⟨n, hn⟩ τ p hp hle hper
    have := tuneCost_le_of_periodFits hp (periodFits_of_periodic hper n)
    omega

/-- The tuning loop settles: the pitch error is bounded. -/
def TuneCostBounded (s : ℕ → Bool) : Prop := ∃ B, ∀ n, tuneCost s n ≤ B

/-- **A sequence is eventually periodic iff the tuning loop settles.** -/
theorem eventuallyPeriodic_iff_tuneCostBounded (s : ℕ → Bool) :
    EventuallyPeriodic s ↔ TuneCostBounded s := by
  constructor
  · rintro ⟨p, hp, N, h⟩
    exact ⟨N + p, fun n => tuneCost_le_of_periodFits hp (periodFits_of_periodic h n)⟩
  · rintro ⟨B, hB⟩
    obtain ⟨τ, p, hp, -, hper⟩ := periodic_of_tuneCost_bounded hB
    exact ⟨p, hp, τ, hper⟩

/-- **Problem 1 in tuning form**: listening to the centre column, the best periodic tune never
settles — its size climbs past every bound. -/
theorem problem1_iff_tuneCost_unbounded :
    Problem1 ↔ ∀ B, ∃ n, B < tuneCost centerCol n := by
  rw [Problem1, eventuallyPeriodic_iff_tuneCostBounded]
  simp only [TuneCostBounded, not_exists, not_forall, not_le]

/-- A tune that fits a prefix is a linear recurrence fitting the same prefix. -/
theorem fits_of_periodFits {s : ℕ → Bool} {τ p m : ℕ} (hp : 0 < p) (h : PeriodFits s τ p m) :
    Fits s (τ + p) (fun i => decide (i = p - 1)) m := by
  intro n hn hnm
  unfold recVal
  rw [Finset.sum_eq_single (p - 1)]
  · have := h (n - p) (by omega) (by omega) (by omega)
    rw [show n - p + p = n by omega] at this
    simp only [decide_true, Bool.true_and]
    rw [this, show n - 1 - (p - 1) = n - p by omega]
  · intro b _ hb; simp [hb, b2]
  · intro hh; simp at hh; omega

/-- **The linear instrument is at least as fine as the periodic one**: the linear-complexity
profile (Berlekamp–Massey's quantity) never exceeds the periodic pitch error. -/
theorem lcProfile_le_tuneCost (s : ℕ → Bool) (n : ℕ) : lcProfile s n ≤ tuneCost s n := by
  obtain ⟨τ, hτ, hf⟩ := tuneCost_spec s n
  have := lcProfile_le_of_fits (fits_of_periodFits (by omega) hf)
  rwa [show τ + (tuneCost s n - τ) = tuneCost s n by omega] at this

/-! ### The excess: how many notes the best periodic tune really predicts -/

/-- **Open target.** The excess `n − tuneCost centerCol n` (notes predicted beyond what the best
periodic tune memorises) is at most `g n` for every `n`. -/
def TuneExcessBound (g : ℕ → ℕ) : Prop := ∀ n, n ≤ tuneCost centerCol n + g n

/-- Any sublinear bound on the excess proves Problem 1. -/
theorem problem1_of_tuneExcessBound {g : ℕ → ℕ} (hg : ∀ B, ∃ n, g n + B < n)
    (h : TuneExcessBound g) : Problem1 := by
  rw [problem1_iff_tuneCost_unbounded]
  intro B
  obtain ⟨n, hn⟩ := hg B
  exact ⟨n, by have := h n; omega⟩

/-- The logarithmic bound `g n = 2 log₂ n + 2` is sublinear. -/
theorem logBound_sublinear : ∀ B, ∃ n, (2 * Nat.log 2 n + 2) + B < n := by
  intro B
  refine ⟨2 ^ (B + 4), ?_⟩
  rw [Nat.log_pow (by norm_num)]
  have : 3 * (B + 4) < 2 ^ (B + 4) := by
    induction B with
    | zero => norm_num
    | succ k ih => rw [pow_succ]; omega
  omega

/-- **Open target, logarithmic form**: the best periodic tune never predicts more than
`2 log₂ n + 2` notes beyond its own size.  (Certified for `n ≤ 1000` in `TuningByEarData.lean`.) -/
def TuneExcessLog : Prop := TuneExcessBound (fun n => 2 * Nat.log 2 n + 2)

theorem problem1_of_tuneExcessLog (h : TuneExcessLog) : Problem1 :=
  problem1_of_tuneExcessBound logBound_sublinear h

end GLM.Rule30
