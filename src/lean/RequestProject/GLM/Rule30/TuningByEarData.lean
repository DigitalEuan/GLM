import RequestProject.GLM.Rule30.TuningByEar
import RequestProject.GLM.Rule30.PowerSeriesLadderData

/-!
# Round 25 certificates: tuning the centre column by ear

(Not a `module`: the checks use `native_decide`.)  All statements are `CERT`: theorems about the
stated finite ranges only.  No finite range decides Problem 1 (`no_finite_confirmation`,
`no_finite_certificate_problem1`).

* `tuneCost_centerCol_19999` — after 19999 notes every consistent periodic tune has size
  `≥ 10000` (from the linear-complexity certificate and `lcProfile_le_tuneCost`).
* `tuneExcess_le_16` — for every `n ≤ 1000` the best periodic tune predicts at most 16 notes
  beyond its own size: `n ≤ tuneCost centerCol n + 16`.
* `tuneExcess_16_sharp` — the 16 is attained at `n = 448` (tune `τ = 282`, `p = 150`).
* `tuneExcessLog_upto` — the logarithmic target `TuneExcessLog` holds for every `n ≤ 2000`.
-/

namespace GLM.Rule30

/-- The first 2001 centre bits as a fast sequence. -/
def centreArr2001 : Array Bool := (fastList 2001).toArray

def fastCentre (i : ℕ) : Bool := centreArr2001.getD i false

theorem agrees_fastCentre {n : ℕ} (hn : n ≤ 2001) : Agrees fastCentre centerCol n := by
  intro i hi
  simp only [fastCentre, centreArr2001, fastList_eq, Array.getD_eq_getD_getElem?,
    List.getElem?_toArray, List.getElem?_map, List.getElem?_range (show i < 2001 by omega),
    Option.map_some, Option.getD_some]

theorem tuneCost_fastCentre {n : ℕ} (hn : n ≤ 2001) :
    tuneCost centerCol n = tuneCost fastCentre n :=
  (tuneCost_congr (agrees_fastCentre hn)).symm

/-! ## A fast checker for tunes -/

/-- Boolean check of `PeriodFits` that only visits the positions it tests. -/
def pfB (s : ℕ → Bool) (τ p n : ℕ) : Bool :=
  (List.range (n - (τ + p))).all fun j => s (τ + j + p) == s (τ + j)

theorem periodFits_of_pfB {s : ℕ → Bool} {τ p n : ℕ} (h : pfB s τ p n = true) :
    PeriodFits s τ p n := by
  intro i _ h1 h2
  have := List.all_eq_true.1 h (i - τ) (List.mem_range.2 (by omega))
  rw [show τ + (i - τ) = i by omega] at this
  simpa using this

/-- Boolean check that no tune of size `< m` fits the first `n` notes (for `m ≤ n`): for every
period `1 ≤ p < m` there is a wrong note at some position `i ≥ m - 1 - p` with `i + p < n`. -/
def noTuneBelow (s : ℕ → Bool) (n m : ℕ) : Bool :=
  (List.range m).all fun p => p == 0 ||
    (List.range (n + 1 - m)).any fun j => s (m - 1 - p + j) != s (m - 1 + j)

theorem le_tuneCost_of_noTuneBelow {s : ℕ → Bool} {n m : ℕ} (hm : m ≤ n)
    (h : noTuneBelow s n m = true) : m ≤ tuneCost s n := by
  by_contra hlt
  push_neg at hlt
  obtain ⟨τ, hτ, hf⟩ := tuneCost_spec s n
  set c := tuneCost s n
  have h1 := List.all_eq_true.1 h (c - τ) (List.mem_range.2 (by omega))
  simp only [Bool.or_eq_true, beq_iff_eq, List.any_eq_true, List.mem_range, bne_iff_ne,
    ne_eq] at h1
  rcases h1 with h0 | ⟨j, hj, hne⟩
  · omega
  · apply hne
    have := hf (m - 1 - (c - τ) + j) (by omega) (by omega) (by omega)
    rw [show m - 1 - (c - τ) + j + (c - τ) = m - 1 + j by omega] at this
    exact this.symm

/-! ## Certificates -/

/-- After 19999 notes, every periodic tune consistent with the centre column has size `≥ 10000`. -/
theorem tuneCost_centerCol_19999 : 10000 ≤ tuneCost centerCol 19999 :=
  le_trans lcProfile_centerCol_19999 (lcProfile_le_tuneCost _ _)

/-- Excess check: `n ≤ tuneCost s n + g n` for all `n ≤ N`. -/
def excessCheck (s : ℕ → Bool) (g : ℕ → ℕ) (N : ℕ) : Bool :=
  (List.range (N + 1)).all fun n => noTuneBelow s n (n - g n)

theorem excess_of_check {s : ℕ → Bool} {g : ℕ → ℕ} {N : ℕ} (h : excessCheck s g N = true) :
    ∀ n ≤ N, n ≤ tuneCost s n + g n := by
  intro n hn
  have := le_tuneCost_of_noTuneBelow (by omega)
    (List.all_eq_true.1 h n (List.mem_range.2 (by omega)))
  omega

/-- The constant-bound form of `excess_of_check`. -/
theorem excess_const_of_check {s : ℕ → Bool} {E N : ℕ} (h : excessCheck s (fun _ => E) N = true) :
    ∀ n ≤ N, n ≤ tuneCost s n + E :=
  excess_of_check h

theorem eq_of_two_bounds {x : ℕ} (h1 : x ≤ 282 + 150) (h2 : 448 ≤ x + 16) : x = 432 := by
  omega

theorem excessCheck_16 : excessCheck fastCentre (fun _ => 16) 1000 = true := by native_decide

/-- **For `n ≤ 1000` the best periodic tune predicts at most 16 notes beyond its own size.** -/
theorem tuneExcess_le_16 : ∀ n ≤ 1000, n ≤ tuneCost centerCol n + 16 := by
  intro n hn
  rw [tuneCost_fastCentre (by omega)]
  exact excess_const_of_check excessCheck_16 n hn

theorem pfB_448 : pfB fastCentre 282 150 448 = true := by native_decide

/-- **The 16 is attained**: at `n = 448` the tune `τ = 282`, `p = 150` fits, so the excess is
exactly 16. -/
theorem tuneExcess_16_sharp : tuneCost centerCol 448 = 432 := by
  rw [tuneCost_fastCentre (by norm_num)]
  exact eq_of_two_bounds (tuneCost_le_of_periodFits (by norm_num) (periodFits_of_pfB pfB_448))
    (excess_const_of_check excessCheck_16 448 (by norm_num))

theorem excessCheck_log : excessCheck fastCentre (fun n => 2 * Nat.log 2 n + 2) 2000 = true := by
  native_decide

/-- **The logarithmic target holds on the first 2000 prefixes.** -/
theorem tuneExcessLog_upto : ∀ n ≤ 2000, n ≤ tuneCost centerCol n + (2 * Nat.log 2 n + 2) := by
  intro n hn
  rw [tuneCost_fastCentre (by omega)]
  exact excess_of_check excessCheck_log n hn

/-- **Round 25 frontier**: Problem 1 is exactly "the periodic tuning loop never settles"; it
follows from a logarithmic excess bound, which holds on the first 2000 prefixes; the excess is at
most 16 up to 1000 notes, and attains 16. -/
theorem frontier_round25 :
    (Problem1 ↔ ∀ B, ∃ n, B < tuneCost centerCol n) ∧
    (TuneExcessLog → Problem1) ∧
    (∀ n ≤ 2000, n ≤ tuneCost centerCol n + (2 * Nat.log 2 n + 2)) ∧
    (∀ n ≤ 1000, n ≤ tuneCost centerCol n + 16) ∧
    tuneCost centerCol 448 = 432 ∧
    10000 ≤ tuneCost centerCol 19999 :=
  ⟨problem1_iff_tuneCost_unbounded, problem1_of_tuneExcessLog, tuneExcessLog_upto,
    tuneExcess_le_16, tuneExcess_16_sharp, tuneCost_centerCol_19999⟩

end GLM.Rule30
