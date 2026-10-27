import RequestProject.GLM.Rule30.ProofRoutesData
import RequestProject.GLM.Rule30.SidewaysView

/-!
# Round 31, To Do 3: the barrier diagonals depend on the drive word

(Not a `module`: the checks use `native_decide`.)

**Question (To Do 3, AUDIT §5.1).** For the two-sided period-2 run bound, the position
`d + B(d)` at which a longest run ends takes only a few values for `d ≤ 28` ("barrier
diagonals").  Do the longest lives of the half-line machine also end on a few fixed left
diagonals, and is the diagonal independent of the drive word?  If so, a barrier lemma could be
stated about the machine.

**Answer (CERT, exact; finite range only).** No, in both respects.

* `lmaxWord_spec`: for the drive words `100`, `110`, `1000`, `1100`, `1110` (as
  `driveN p k`, i.e. `(p, k) = (3,1), (3,3), (4,1), (4,3), (4,7)`) and every code length
  `d ≤ 20`, the exact longest life `Lmax d` (first failure time) with a code attaining it.
  The period-2 word `10` is `lmaxTwo_spec` (Round 27, `d ≤ 32`).
* `barrier_depends_on_word`: at the same length `d = 8` the six words end their longest lives on
  the diagonals `d + Lmax d = 18, 32, 20, 36, 20, 24` — five different diagonals.
* `barrier_set_not_small_two`: for the word `10` the diagonals `d + Lmax d`, `d ≤ 32`, take
  `28` distinct values (`lmaxTwo_spec`).  The plateau pattern of the two-sided run bound
  (`7` values for `d ≤ 28`) is **not** reproduced by the machine.
* `lmax_ratio_word`: the ratio `Lmax d / d` depends strongly on the word: for `1000`,
  `Lmax 16 = 72 = 4.5 · 16`, while for `1110`, `Lmax 16 = 20`.

So a barrier lemma, if one exists, must depend on the drive word; the "few fixed diagonals"
picture belongs to the two-sided run bound, not to the half-line machine.  The search is
`scripts/barrier_diagonals.c` (exact integer arithmetic; output to `d = 28` in
`scripts/barrier_diagonals_output.txt`, EMP beyond `d = 20`).

`frontier_round31` collects Round 31: the sideways reformulation of `HalfLineDies`
(`SidewaysView.lean`), the blocked window-quotient route, and the barrier finding.
-/

namespace GLM.Rule30

/-- The certified check of one row `(d, L, S)` for the drive `bd`: the code `S` has length `d`,
first fails exactly at time `L`, and every code of length `d` fails by time `L + 1`. -/
def lmaxWordCheck (bd : ℕ → Bool) (d L S : ℕ) : Bool :=
  decide (1 ≤ d) && decide (2 ^ (d - 1) ≤ S) && decide (S < 2 ^ d) &&
    !dDiesBy bd S L && dDiesBy bd S (L + 1) && prefixSearch bd (L + 1) (d - 1) 0 0

/-- `(p, k, [(d, Lmax d, witness)])` for five drive words, `d = 1 … 20`
(from `scripts/barrier_diagonals.c`). -/
def lmaxWords : List (ℕ × ℕ × List (ℕ × ℕ × ℕ)) :=
  [(3, 1, [(1, 6, 1), (2, 6, 3), (3, 15, 5), (4, 3, 9), (5, 12, 17), (6, 12, 39), (7, 12, 67),
      (8, 24, 225), (9, 18, 469), (10, 24, 519), (11, 27, 1493), (12, 27, 3253), (13, 27, 7057),
      (14, 27, 8689), (15, 39, 23187), (16, 39, 42353), (17, 39, 74225), (18, 39, 225091),
      (19, 45, 490917), (20, 54, 685299)]),
   (3, 3, [(1, 0, 1), (2, 1, 2), (3, 7, 4), (4, 3, 8), (5, 6, 16), (6, 7, 36), (7, 7, 80),
      (8, 12, 164), (9, 15, 496), (10, 13, 644), (11, 15, 1924), (12, 16, 2544), (13, 19, 4260),
      (14, 22, 8656), (15, 22, 18308), (16, 25, 58064), (17, 24, 74448), (18, 22, 161008),
      (19, 27, 296836), (20, 30, 543216)]),
   (4, 1, [(1, 12, 1), (2, 12, 3), (3, 4, 5), (4, 12, 15), (5, 8, 21), (6, 16, 43), (7, 16, 79),
      (8, 28, 249), (9, 32, 289), (10, 32, 591), (11, 32, 1461), (12, 36, 2091), (13, 32, 5857),
      (14, 44, 13405), (15, 60, 16705), (16, 72, 62781), (17, 44, 68139), (18, 52, 168463),
      (19, 64, 500815), (20, 72, 560419)]),
   (4, 3, [(1, 0, 1), (2, 1, 2), (3, 5, 4), (4, 9, 12), (5, 5, 16), (6, 12, 36), (7, 12, 112),
      (8, 12, 176), (9, 12, 296), (10, 17, 872), (11, 21, 1896), (12, 20, 2084), (13, 24, 4132),
      (14, 24, 13360), (15, 32, 20364), (16, 28, 48176), (17, 33, 95116), (18, 29, 209804),
      (19, 32, 317324), (20, 40, 542308)]),
   (4, 7, [(1, 0, 1), (2, 2, 2), (3, 4, 6), (4, 4, 14), (5, 6, 22), (6, 6, 62), (7, 8, 86),
      (8, 16, 254), (9, 10, 342), (10, 10, 894), (11, 14, 1494), (12, 12, 2302), (13, 14, 5462),
      (14, 16, 16254), (15, 18, 26494), (16, 20, 56790), (17, 22, 83414), (18, 25, 220630),
      (19, 24, 288638), (20, 28, 606078)])]

theorem lmaxWords_check :
    lmaxWords.all (fun w => w.2.2.all (fun e => lmaxWordCheck (driveN w.1 w.2.1) e.1 e.2.1 e.2.2))
      = true := by
  native_decide

/-- **Exact longest lives for five drive words, `d ≤ 20`** (CERT). For each listed word
`driveN p k` and row `(d, L, S)`: every code of length `d` fails by time `L + 1`, and the code
`S` of length `d` first fails exactly at time `L`. -/
theorem lmaxWord_spec : ∀ w ∈ lmaxWords, ∀ e ∈ w.2.2,
    (∀ S, 2 ^ (e.1 - 1) ≤ S → S < 2 ^ e.1 → dDiesBy (driveN w.1 w.2.1) S (e.2.1 + 1) = true) ∧
    (2 ^ (e.1 - 1) ≤ e.2.2 ∧ e.2.2 < 2 ^ e.1 ∧ dDiesBy (driveN w.1 w.2.1) e.2.2 e.2.1 = false ∧
      dDiesBy (driveN w.1 w.2.1) e.2.2 (e.2.1 + 1) = true) := by
  intro w hw e he
  have h := List.all_eq_true.1 (List.all_eq_true.1 lmaxWords_check w hw) e he
  simp only [lmaxWordCheck, Bool.and_eq_true, decide_eq_true_eq, Bool.not_eq_true'] at h
  obtain ⟨⟨⟨⟨⟨hd, h1⟩, h2⟩, hL⟩, hL1⟩, hP⟩ := h
  exact ⟨fun S a b => dDiesBy_of_prefixSearch hd hP a b, h1, h2, hL, hL1⟩

/-- The longest life of length `d` under the drive `bd` is exactly `L`: every code of length `d`
fails by time `L + 1`, and some code of length `d` first fails at time `L`. -/
def IsLmax (bd : ℕ → Bool) (d L : ℕ) : Prop :=
  (∀ S, 2 ^ (d - 1) ≤ S → S < 2 ^ d → dDiesBy bd S (L + 1) = true) ∧
    ∃ S, 2 ^ (d - 1) ≤ S ∧ S < 2 ^ d ∧ dDiesBy bd S L = false

/-- A passing row check gives the exact longest life. -/
theorem isLmax_of_check {bd : ℕ → Bool} {d L S : ℕ} (h : lmaxWordCheck bd d L S = true) :
    IsLmax bd d L := by
  simp only [lmaxWordCheck, Bool.and_eq_true, decide_eq_true_eq, Bool.not_eq_true'] at h
  obtain ⟨⟨⟨⟨⟨hd, h1⟩, h2⟩, hL⟩, -⟩, hP⟩ := h
  exact ⟨fun S a b => dDiesBy_of_prefixSearch hd hP a b, S, h1, h2, hL⟩

/-- `Lmax` is a function of the drive and the length. -/
theorem isLmax_unique {bd : ℕ → Bool} {d L L' : ℕ} (h : IsLmax bd d L) (h' : IsLmax bd d L') :
    L = L' := by
  obtain ⟨hall, S, hS1, hS2, hS⟩ := h
  obtain ⟨hall', S', hS1', hS2', hS'⟩ := h'
  by_contra hne
  rcases Nat.lt_or_gt_of_ne hne with hlt | hlt
  · have := dDiesBy_mono (hall S' hS1' hS2') (show L + 1 ≤ L' by omega)
    rw [hS'] at this; exact Bool.noConfusion this
  · have := dDiesBy_mono (hall' S hS1 hS2) (show L' + 1 ≤ L by omega)
    rw [hS] at this; exact Bool.noConfusion this

/-- **The barrier diagonal depends on the drive word** (CERT). At `d = 8` the six drive words
`10, 100, 110, 1000, 1100, 1110` have longest lives `10, 24, 12, 28, 12, 16`, so they end on
the left diagonals `d + Lmax d = 18, 32, 20, 36, 20, 24`. -/
theorem barrier_depends_on_word :
    IsLmax (driveN 2 1) 8 10 ∧ IsLmax (driveN 3 1) 8 24 ∧ IsLmax (driveN 3 3) 8 12 ∧
      IsLmax (driveN 4 1) 8 28 ∧ IsLmax (driveN 4 3) 8 12 ∧ IsLmax (driveN 4 7) 8 16 :=
  ⟨isLmax_of_check (S := 253) (by native_decide),
   isLmax_of_check (S := 225) (by native_decide),
   isLmax_of_check (S := 164) (by native_decide),
   isLmax_of_check (S := 249) (by native_decide),
   isLmax_of_check (S := 176) (by native_decide),
   isLmax_of_check (S := 254) (by native_decide)⟩

/-- **The period-2 barrier set is not small** (CERT, `d ≤ 32`): the diagonals `d + Lmax d` of
the word `10` take `28` distinct values. -/
theorem barrier_set_not_small_two :
    ((lmaxTwo.map (fun e => e.1 + e.2.1)).dedup).length = 28 := by
  native_decide

/-- **Longest lives scale differently for different words** (CERT): `Lmax 16 = 72` for the word
`1000` and `Lmax 16 = 20` for `1110`. -/
theorem lmax_ratio_word : IsLmax (driveN 4 1) 16 72 ∧ IsLmax (driveN 4 7) 16 20 :=
  ⟨isLmax_of_check (S := 62781) (by native_decide),
   isLmax_of_check (S := 56790) (by native_decide)⟩

/-- **Round 31 in one statement.**
* `HalfLineDies p` is exactly a statement about which time-`0` rows the sideways reader can
  reconstruct from an admissible first column (`halfLineDies_iff_sideways`);
* rows with infinitely many black cells survive forever under every drive, so finiteness of the
  row is essential (`infinite_row_survives`);
* the barrier diagonal of the longest life depends on the drive word (`barrier_depends_on_word`).
-/
theorem frontier_round31 :
    (∀ p, HalfLineDies p ↔
      ∀ k, 0 < k → k < 2 ^ p → ∀ u, Admissible (driveN p k) u →
        ∀ S, 0 < S → ¬ ∀ i, S.testBit i = recon (driveN p k) u (i + 1) 0) ∧
    (∀ bd : ℕ → Bool, ∃ σ : ℕ → Bool, ∀ t, bd t = true → halfStateInf bd σ t 0 = !bd (t + 1)) ∧
    (IsLmax (driveN 2 1) 8 10 ∧ IsLmax (driveN 3 1) 8 24) :=
  ⟨halfLineDies_iff_sideways, infinite_row_survives,
    barrier_depends_on_word.1, barrier_depends_on_word.2.1⟩

end GLM.Rule30
