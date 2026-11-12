import RequestProject.GLM.Rule30.RunBoundData

/-!
# Round 16: period-2 run bounds by a verified pruned search

Round 13 (`RunBoundData.lean`) checked the period-2 run bound for `d ≤ 7` by enumerating all
`2^(d+L+1)` windows.  This file replaces the enumeration by a **pruned depth-first search** along
the *left diagonals* of the space-time diagram and proves the search sound for every left-white
row.  The exact bounds are now certified much further out.

## Left diagonals

In a left-white row with edge `ℓ`, the cell `(t, ℓ + m − t)` lies on the `m`-th diagonal parallel
to the left edge.  Rule 30 reads diagonal `m` from diagonals `m − 1`, `m − 2` and itself:

  `cell(t+1, on diag m) = cell(t, diag m−2) XOR (cell(t, diag m−1) OR cell(t, diag m))`

(`evolve_diag_succ`), and diagonal `m` starts with the initial cell `x (ℓ + m)`.  The column at
distance `d` meets diagonal `d + t` at time `t`.  So the cells right of the edge can be chosen one
at a time, `x ℓ, x (ℓ+1), …`: choosing `x (ℓ + m)` fixes diagonal `m` and the column value at time
`m − d`, and a branch can be abandoned as soon as the column stops being periodic.

* `diagStep` — the next diagonal from the two previous ones (`diagStep_spec`).
* `searchDead p d k m pp cur hist` — the search; `searchDead_sound` proves that `true` means that
  no left-white row keeps the column `p`-periodic up to the corresponding time.
* `runSearch_sound`, `runBoundUpTo_of_searches` — the interface to `RunBoundUpTo`.
* **`runBound_two_upTo_sixteen`** (`CERT`) — exact-value period-2 run bounds for `d ≤ 16`:
  `1, 7, 6, 5, 5, 8, 9, 9, 16, 15, 14, 13, 14, 16, 19, 21, 25`.
* `runBound_two_witness` (`CERT`) — each bound is attained (an explicit left-white row).

These are still finite certificates (`no_finite_certificate_problem1`): they cover the first
seventeen rows of the stack, not the infinite statement.
-/

namespace GLM.Rule30

/-! ## Diagonals -/

/-- **The diagonal recursion.** Valid for every row and every integer diagonal index `m`. -/
theorem evolve_diag_succ (x : Config) (ℓ m : ℤ) (t : ℕ) :
    evolve x (t + 1) (ℓ + m - (t + 1 : ℕ)) =
      xor (evolve x t (ℓ + (m - 2) - t)) (evolve x t (ℓ + (m - 1) - t) || evolve x t (ℓ + m - t)) := by
  rw [evolve_succ]
  have e1 : ℓ + m - ((t + 1 : ℕ) : ℤ) - 1 = ℓ + (m - 2) - t := by push_cast; ring
  have e3 : ℓ + m - ((t + 1 : ℕ) : ℤ) + 1 = ℓ + m - t := by push_cast; ring
  have e2 : ℓ + m - ((t + 1 : ℕ) : ℤ) = ℓ + (m - 1) - t := by push_cast; ring
  rw [e1, e3, e2]
  rfl

/-- The next diagonal (as a list indexed by time) from the two previous ones and its first cell. -/
def diagStep : List Bool → List Bool → Bool → List Bool
  | a :: pp, c :: p, v => v :: diagStep pp p (xor a (c || v))
  | _, _, v => [v]

theorem diagStep_length_ge (pp p : List Bool) (v : Bool) :
    min pp.length p.length + 1 ≤ (diagStep pp p v).length := by
  induction pp generalizing p v with
  | nil => simp [diagStep]
  | cons a pp ih =>
    cases p with
    | nil => simp [diagStep]
    | cons c p =>
      simp only [diagStep, List.length_cons]
      have := ih p (xor a (c || v))
      omega

theorem diagStep_spec (pp p : List Bool) (v : Bool) (f g h : ℕ → Bool) (N : ℕ)
    (hN : N ≤ min pp.length p.length)
    (hf : ∀ t < N, pp.getD t false = f t) (hg : ∀ t < N, p.getD t false = g t)
    (h0 : h 0 = v) (hs : ∀ t < N, h (t + 1) = xor (f t) (g t || h t)) :
    ∀ t ≤ N, (diagStep pp p v).getD t false = h t := by
  induction pp generalizing p v f g h N with
  | nil => intro t ht; simp at hN; subst hN; simp at ht; subst ht; simp [diagStep, h0]
  | cons a pp ih =>
    cases p with
    | nil => intro t ht; simp at hN; subst hN; simp at ht; subst ht; simp [diagStep, h0]
    | cons c p =>
      intro t ht
      cases t with
      | zero => simp [diagStep, h0]
      | succ t =>
        simp only [diagStep, List.getD_cons_succ]
        have ha : a = f 0 := by simpa using hf 0 (by omega)
        have hc : c = g 0 := by simpa using hg 0 (by omega)
        simp only [List.length_cons] at hN
        refine ih p _ (fun s => f (s + 1)) (fun s => g (s + 1)) (fun s => h (s + 1)) (N - 1)
          (by omega)
          (fun s hs' => by simpa using hf (s + 1) (by omega))
          (fun s hs' => by simpa using hg (s + 1) (by omega))
          ?_ (fun s hs' => hs (s + 1) (by omega)) t (by omega)
        show h (0 + 1) = _
        rw [hs 0 (by omega), ha, hc, h0]

/-! ## The search -/

/-- The pruned search.  State at depth `m`: `pp`, `cur` are diagonals `m − 1`, `m` (indexed by
time); `hist` lists the column values `a(m − d), …, a(0)` already fixed.  Returns `true` if every
choice of the next `k` cells breaks `p`-periodicity of the column. -/
def searchDead (p d : ℕ) : ℕ → ℕ → List Bool → List Bool → List Bool → Bool
  | 0, _, _, _, _ => false
  | k + 1, m, pp, cur, hist => [false, true].all fun b =>
      let nr := diagStep pp cur b
      if d ≤ m + 1 then
        let a := nr.getD (m + 1 - d) false
        if p ≤ m + 1 - d && a != hist.getD (p - 1) false then true
        else searchDead p d k (m + 1) cur nr (a :: hist)
      else searchDead p d k (m + 1) cur nr hist

/-- The diagonal `m` of the row `x` (edge `ℓ`), up to time `T`, as the specification of a list. -/
def DiagOK (x : Config) (ℓ m : ℤ) (T : ℕ) (r : List Bool) : Prop :=
  T < r.length ∧ ∀ t ≤ T, r.getD t false = evolve x t (ℓ + m - t)

/-- The column history at depth `m`: `hist = [a(m − d), …, a(0)]` (empty if `m < d`). -/
def HistOK (x : Config) (ℓ : ℤ) (d m : ℕ) (hist : List Bool) : Prop :=
  hist.length = m + 1 - d ∧ ∀ i < hist.length, hist.getD i false = evolve x (m - d - i) (ℓ + d)

theorem diagStep_ok {x : Config} {ℓ : ℤ} {m : ℕ} {T : ℕ} {pp cur : List Bool}
    (hpp : DiagOK x ℓ ((m : ℤ) - 1) T pp) (hcur : DiagOK x ℓ m T cur) :
    DiagOK x ℓ ((m + 1 : ℕ) : ℤ) T (diagStep pp cur (x (ℓ + (m + 1 : ℕ)))) := by
  have h1 := hpp.1
  have h2 := hcur.1
  refine ⟨lt_of_lt_of_le (by omega) (diagStep_length_ge pp cur _), fun t ht => ?_⟩
  refine diagStep_spec pp cur _ (fun s => evolve x s (ℓ + ((m : ℤ) - 1) - s))
    (fun s => evolve x s (ℓ + (m : ℤ) - s))
    (fun s => evolve x s (ℓ + ((m + 1 : ℕ) : ℤ) - s)) T (by omega)
    (fun s hs => hpp.2 s (by omega)) (fun s hs => hcur.2 s (by omega)) (by simp) ?_ t ht
  intro s _
  have := evolve_diag_succ x ℓ ((m + 1 : ℕ) : ℤ) s
  simp only at this ⊢
  rw [this]
  congr 3 <;> push_cast <;> ring_nf

/-- **Soundness of the search.** -/
theorem searchDead_sound (x : Config) (ℓ : ℤ) (p d T : ℕ) (hp : 1 ≤ p) :
    ∀ k m (pp cur hist : List Bool), m + k ≤ d + T →
      DiagOK x ℓ ((m : ℤ) - 1) T pp → DiagOK x ℓ m T cur → HistOK x ℓ d m hist →
      searchDead p d k m pp cur hist = true →
      ¬ ∀ t, p ≤ t → d + t ≤ m + k → evolve x t (ℓ + d) = evolve x (t - p) (ℓ + d) := by
  intro k
  induction k with
  | zero => intro m pp cur hist _ _ _ _ h; simp [searchDead] at h
  | succ k ih =>
    intro m pp cur hist hmk hpp hcur hhist h hall
    simp only [searchDead, List.all_cons, List.all_nil, Bool.and_true, Bool.and_eq_true] at h
    set b := x (ℓ + (m + 1 : ℕ))
    have hb : (if d ≤ m + 1 then
        (if p ≤ m + 1 - d && (diagStep pp cur b).getD (m + 1 - d) false !=
            hist.getD (p - 1) false then true
         else searchDead p d k (m + 1) cur (diagStep pp cur b)
           ((diagStep pp cur b).getD (m + 1 - d) false :: hist))
        else searchDead p d k (m + 1) cur (diagStep pp cur b) hist) = true := by
      cases hbv : b
      · simpa [hbv] using h.1
      · simpa [hbv] using h.2
    have hnr := diagStep_ok hpp hcur
    have hcur' : DiagOK x ℓ (((m + 1 : ℕ) : ℤ) - 1) T cur := by
      convert hcur using 2; push_cast; ring
    -- the new column value
    by_cases hd : d ≤ m + 1
    · rw [if_pos hd] at hb
      have ha : (diagStep pp cur b).getD (m + 1 - d) false = evolve x (m + 1 - d) (ℓ + d) := by
        rw [hnr.2 _ (by omega)]; congr 1; push_cast [hd]; ring
      by_cases hc : (p ≤ m + 1 - d && (diagStep pp cur b).getD (m + 1 - d) false !=
          hist.getD (p - 1) false) = true
      · simp only [Bool.and_eq_true, decide_eq_true_eq, bne_iff_ne, ne_eq] at hc
        apply hc.2
        rw [ha, hall (m + 1 - d) hc.1 (by omega), hhist.2 (p - 1) (by rw [hhist.1]; omega)]
        congr 1; omega
      · rw [if_neg hc] at hb
        refine ih (m + 1) cur _ _ (by omega) hcur' hnr ?_ hb
          (fun t h1 h2 => hall t h1 (by omega))
        refine ⟨by simp [hhist.1]; omega, fun i hi => ?_⟩
        cases i with
        | zero => simpa [ha]
        | succ i =>
          simp only [List.getD_cons_succ]
          rw [hhist.2 i (by simp at hi; omega)]
          congr 1; omega
    · rw [if_neg hd] at hb
      refine ih (m + 1) cur _ _ (by omega) hcur' hnr ?_ hb (fun t h1 h2 => hall t h1 (by omega))
      exact ⟨by rw [hhist.1]; omega, fun i hi => by rw [hhist.1] at hi; omega⟩

/-- The search for distance `d` and window `L`, started at the edge. -/
def runSearch (p d L : ℕ) : Bool :=
  searchDead p d (d + L) 0 (List.replicate (L + 1) false) (List.replicate (L + 1) true)
    (if d = 0 then [true] else [])

/-- **The search decides the run bound for every left-white row.** -/
theorem runSearch_sound {p d L : ℕ} (hp : 1 ≤ p) (hc : runSearch p d L = true) (x : Config)
    (ℓ : ℤ) (hw : ∀ j, j < ℓ → x j = false) (hb : x ℓ = true) :
    ¬ ∀ t, t + p ≤ L → evolve x (t + p) (ℓ + d) = evolve x t (ℓ + d) := by
  intro hrun
  refine searchDead_sound x ℓ p d L hp (d + L) 0 _ _ _ (by omega) ?_ ?_ ?_ hc ?_
  · refine ⟨by simp, fun t ht => ?_⟩
    rw [List.getD_eq_getElem _ _ (by simp; omega), List.getElem_replicate]
    exact (evolve_white_left x ℓ hw t _ (by push_cast; omega)).symm
  · refine ⟨by simp, fun t ht => ?_⟩
    rw [List.getD_eq_getElem _ _ (by simp; omega), List.getElem_replicate]
    have := evolve_left_edge x ℓ hw hb t
    rw [show ℓ + ((0 : ℕ) : ℤ) - t = ℓ - t by push_cast; ring]
    exact this.symm
  · by_cases hd : d = 0
    · subst hd
      refine ⟨by simp, fun i hi => ?_⟩
      simp at hi; subst hi; simpa using hb.symm
    · exact ⟨by simp [hd]; omega, fun i hi => by simp [hd] at hi⟩
  · intro t h1 h2
    obtain ⟨s, rfl⟩ : ∃ s, t = s + p := ⟨t - p, by omega⟩
    rw [Nat.add_sub_cancel]
    exact hrun s (by omega)

theorem runBoundUpTo_of_searches {p D : ℕ} {B : ℕ → ℕ} (hp : 1 ≤ p)
    (hc : ∀ d ≤ D, runSearch p d (B d + 1) = true) : RunBoundUpTo p B D := by
  intro x ℓ hw hb d L hd hrun
  by_contra hL
  exact runSearch_sound hp (hc d hd) x ℓ hw hb fun t ht => hrun t (by omega)

/-! ## The certificates -/

/-- The exact period-2 run bounds for `d = 0, …, 16`. -/
def runBoundTwoExt (d : ℕ) : ℕ :=
  [1, 7, 6, 5, 5, 8, 9, 9, 16, 15, 14, 13, 14, 16, 19, 21, 25].getD d 0

theorem runSearch_two_upTo_sixteen : ∀ d ≤ 16, runSearch 2 d (runBoundTwoExt d + 1) = true := by
  native_decide

/-- **Period-2 run bound for `d ≤ 16` (`CERT`).** In every left-white row, the column at distance
`d ≤ 16` from the edge stays 2-periodic for at most `runBoundTwoExt d` steps. -/
theorem runBound_two_upTo_sixteen : RunBoundUpTo 2 runBoundTwoExt 16 :=
  runBoundUpTo_of_searches (by norm_num) runSearch_two_upTo_sixteen

/-- Agreement with Round 13's enumeration on `d ≤ 7`. -/
theorem runBoundTwoExt_agrees : ∀ d ≤ 7, runBoundTwoExt d = runBoundTwo d := by decide

/-! ## Sharpness: explicit rows attaining the bounds -/

/-- Check that the row `maskConfig 0 m` (cells `0, 1, …` given by the bits of `m`, white
elsewhere) is black at the edge and keeps the column at distance `d` `p`-periodic on `[0, L]`. -/
def witnessCheck (p d L m : ℕ) : Bool :=
  m.testBit 0 && (List.range (L + 1 - p)).all fun t =>
    (rowStep^[t + p] m).testBit (d + t + p) == (rowStep^[t] m).testBit (d + t)

theorem exists_run_of_witness {p d L m : ℕ} (hc : witnessCheck p d L m = true) :
    ∃ x : Config, (∀ j, j < 0 → x j = false) ∧ x 0 = true ∧
      ∀ t, t + p ≤ L → evolve x (t + p) (0 + d) = evolve x t (0 + d) := by
  simp only [witnessCheck, Bool.and_eq_true, List.all_eq_true, List.mem_range] at hc
  obtain ⟨h0, hall'⟩ := hc
  refine ⟨maskConfig 0 m, maskConfig_white 0 m, by simpa [maskConfig] using h0, fun t ht => ?_⟩
  rw [zero_add, evolve_maskConfig_fast, evolve_maskConfig_fast,
    show d + (t + p) = d + t + p by ring]
  exact beq_iff_eq.mp (hall' t (by omega))

/-- Rows (as bit patterns, found by the search outside Lean and checked here) attaining the
period-2 bounds for `d = 0, …, 16`. -/
def runBoundTwoWitness (d : ℕ) : ℕ :=
  [1, 257, 263, 37, 21, 277, 297, 22593, 147585, 1053009, 37523, 33813, 4217565, 38029,
    4464809, 2113665, 67676289].getD d 0

theorem witnessCheck_two_upTo_sixteen :
    ∀ d ≤ 16, witnessCheck 2 d (runBoundTwoExt d) (runBoundTwoWitness d) = true := by
  native_decide

/-- **The period-2 bounds are exact for `d ≤ 16` (`CERT`):** some left-white row has a
2-periodic run of length `runBoundTwoExt d` at distance `d`. -/
theorem runBound_two_witness (d : ℕ) (hd : d ≤ 16) :
    ∃ x : Config, (∀ j, j < 0 → x j = false) ∧ x 0 = true ∧
      ∀ t, t + 2 ≤ runBoundTwoExt d → evolve x (t + 2) (0 + d) = evolve x t (0 + d) :=
  exists_run_of_witness (witnessCheck_two_upTo_sixteen d hd)

/-! ## The open target, stated -/

/-- **Conjectured linear period-2 run bound (OPEN).**  In every left-white row the column at
distance `d` stays 2-periodic for at most `2d + 7` steps.  Consistent with the certified exact
values for `d ≤ 16` (`runBoundTwoExt_le_linear`) and with the search outside Lean up to `d = 26`. -/
def PeriodTwoLinearBound : Prop := RunBound 2 (fun d => 2 * d + 7)

theorem runBoundTwoExt_le_linear : ∀ d ≤ 16, runBoundTwoExt d ≤ 2 * d + 7 := by decide

/-- **What the conjecture would give:** no column of any left-white row (in particular, of the
seed's run) is eventually alternating or constant. -/
theorem leftWhiteAperiodic_two_of_linearBound (h : PeriodTwoLinearBound) :
    LeftWhiteAperiodic 2 :=
  leftWhiteAperiodic_of_runBound h

end GLM.Rule30
