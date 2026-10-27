module

public import RequestProject.GLM.Rule30.PostEdgeSpec

/-!
# Round 27: four proof routes for a driven half-line, stated and connected

The open core of the period-`p` rung of Problem 1 is `WordDies bd`: under the periodic drive `bd`,
every non-empty half-line code eventually fails a test.  There are four natural ways to prove it,
and they need different lemmas:

| Route | Needed lemma | Lean |
|---|---|---|
| individual termination | every surviving trajectory eventually fails | `WordDies` itself |
| ranking argument | a bounded measure drops during continued survival | `Ranking`, **`wordDies_of_ranking`** |
| population contraction | survivor counts obey a uniform decreasing bound | `AmortizedHalving` (Round 26) |
| width induction | a wider code dies soon after some narrower one | `WidthStep`, **`wordDies_of_widthStep`** |

Each route is proved here (or in Round 26) to give the target.  None of the needed lemmas is
proved; `ProofRoutesData.lean` refutes the declared ranking candidates and the small width-step
constants with finite counterexamples.

**How to read a ranking.**  `Ranking bd P c f` asks for a measure `P` of the state and the time
which is at most `f d` at the edge of a code of length `d` and drops strictly over every window of
`c` steps that the machine survives after the edge.  `ranking_dies_by` turns it into the run bound
`d − 1 + c·(f d + 1)`.  A measure that uses the time and the width freely can encode any run bound
(for example `B d − t`), so a ranking is informative only when `P` is local to the state; that is
what the declared family in `ProofRoutesData.lean` tests.
-/

@[expose] public section

namespace GLM.Rule30

/-! ## Ranking functions -/

/-- **A ranking for the drive `bd`.** `P` (of the state and the time) is at most `f d` at the
edge of every code of length `d`, and drops strictly across every window of `c` steps after the
edge during which the machine passes every test. -/
def Ranking (bd : ℕ → Bool) (P : ℕ → ℕ → ℕ) (c : ℕ) (f : ℕ → ℕ) : Prop :=
  ∀ d S, 1 ≤ d → 2 ^ (d - 1) ≤ S → S < 2 ^ d →
    P (halfStateD bd S (d - 1)) (d - 1) ≤ f d ∧
    ∀ t, d - 1 ≤ t → dDiesBy bd S (t + c) = false →
      P (halfStateD bd S (t + c)) (t + c) < P (halfStateD bd S t) t

/-- **A ranking gives a run bound.** -/
theorem ranking_dies_by {bd : ℕ → Bool} {P : ℕ → ℕ → ℕ} {c : ℕ} {f : ℕ → ℕ}
    (h : Ranking bd P c f) {d S : ℕ} (hd : 1 ≤ d) (h1 : 2 ^ (d - 1) ≤ S) (h2 : S < 2 ^ d) :
    dDiesBy bd S (d - 1 + c * (f d + 1)) = true := by
  obtain ⟨h0, hstep⟩ := h d S hd h1 h2
  by_contra hne
  have hsurv : ∀ j ≤ f d + 1, dDiesBy bd S (d - 1 + c * j) = false := by
    intro j hj
    by_contra hj'
    exact hne (dDiesBy_mono (Bool.eq_true_of_not_eq_false hj')
      (by have := Nat.mul_le_mul_left c hj; omega))
  have key : ∀ j ≤ f d + 1, P (halfStateD bd S (d - 1 + c * j)) (d - 1 + c * j) + j ≤ f d := by
    intro j
    induction j with
    | zero => intro _; simpa using h0
    | succ j ih =>
      intro hj
      have := hstep (d - 1 + c * j) (by omega)
        (by rw [show d - 1 + c * j + c = d - 1 + c * (j + 1) by ring]; exact hsurv _ hj)
      rw [show d - 1 + c * j + c = d - 1 + c * (j + 1) by ring] at this
      have := ih (by omega)
      omega
  have := key (f d + 1) le_rfl
  omega

/-- The length of a positive code: `2^(len S − 1) ≤ S < 2^(len S)`. -/
theorem code_length_bounds {S : ℕ} (hS : 0 < S) :
    1 ≤ Nat.log2 S + 1 ∧ 2 ^ (Nat.log2 S + 1 - 1) ≤ S ∧ S < 2 ^ (Nat.log2 S + 1) :=
  ⟨by omega, by simpa using Nat.log2_self_le hS.ne', Nat.lt_log2_self⟩

/-- **Ranking route: a ranking proves the target.** -/
theorem wordDies_of_ranking {bd : ℕ → Bool} {P : ℕ → ℕ → ℕ} {c : ℕ} {f : ℕ → ℕ}
    (h : Ranking bd P c f) : WordDies bd := by
  intro S hS
  have hb := code_length_bounds hS
  exact ⟨_, ranking_dies_by h hb.1 hb.2.1 hb.2.2⟩

/-- **Refuting a ranking.** One surviving window of `c` steps after the edge, across which `P`
does not drop, refutes `Ranking bd P c f` for every `f`. -/
theorem not_ranking_of_window {bd : ℕ → Bool} {P : ℕ → ℕ → ℕ} {c d S t : ℕ} (f : ℕ → ℕ)
    (hd : 1 ≤ d) (h1 : 2 ^ (d - 1) ≤ S) (h2 : S < 2 ^ d) (ht : d - 1 ≤ t)
    (hs : dDiesBy bd S (t + c) = false)
    (hP : P (halfStateD bd S t) t ≤ P (halfStateD bd S (t + c)) (t + c)) :
    ¬ Ranking bd P c f := fun h => by
  have := (h d S hd h1 h2).2 t ht hs
  omega

/-! ## Width induction -/

/-- **A width step of size `b`.** Every code of length `d + 2` dies at most `b` steps after some
code of length `d` dies. -/
def WidthStep (bd : ℕ → Bool) (b : ℕ) : Prop :=
  ∀ d S, 1 ≤ d → 2 ^ (d + 1) ≤ S → S < 2 ^ (d + 2) →
    ∃ S', 2 ^ (d - 1) ≤ S' ∧ S' < 2 ^ d ∧
      ∀ T, dDiesBy bd S' T = true → dDiesBy bd S (T + b) = true

/-- **Width-induction route.** A width step, together with the codes of length `1` and `2`,
proves the target. -/
theorem wordDies_of_widthStep {bd : ℕ → Bool} {b : ℕ} (h : WidthStep bd b)
    (hbase : ∀ S, 0 < S → S < 4 → ∃ T, dDiesBy bd S T = true) : WordDies bd := by
  have main : ∀ n, ∀ d S, d ≤ n → 1 ≤ d → 2 ^ (d - 1) ≤ S → S < 2 ^ d →
      ∃ T, dDiesBy bd S T = true := by
    intro n
    induction n using Nat.strong_induction_on with
    | _ n ih =>
      intro d S hdn hd h1 h2
      by_cases hd2 : d ≤ 2
      · apply hbase S (lt_of_lt_of_le (Nat.one_le_two_pow) h1)
        calc S < 2 ^ d := h2
          _ ≤ 2 ^ 2 := Nat.pow_le_pow_right (by norm_num) hd2
          _ = 4 := by norm_num
      · obtain ⟨S', h1', h2', hS'⟩ := h (d - 2) S (by omega)
          (by rwa [show d - 2 + 1 = d - 1 by omega]) (by rwa [show d - 2 + 2 = d by omega])
        obtain ⟨T, hT⟩ := ih (d - 2) (by omega) (d - 2) S' le_rfl (by omega) h1' h2'
        exact ⟨T + b, hS' T hT⟩
  intro S hS
  have hb := code_length_bounds hS
  exact main _ _ S le_rfl hb.1 hb.2.1 hb.2.2

/-- **Refuting a width step.** If every code of length `d` dies by `T`, and some code of length
`d + 2` survives to `T + b`, there is no width step of size `b`. -/
theorem not_widthStep_of_witness {bd : ℕ → Bool} {b d T S : ℕ} (hd : 1 ≤ d)
    (hall : ∀ S', 2 ^ (d - 1) ≤ S' → S' < 2 ^ d → dDiesBy bd S' T = true)
    (h1 : 2 ^ (d + 1) ≤ S) (h2 : S < 2 ^ (d + 2)) (hs : dDiesBy bd S (T + b) = false) :
    ¬ WidthStep bd b := fun h => by
  obtain ⟨S', h1', h2', hS'⟩ := h d S hd h1 h2
  rw [hS' T (hall S' h1' h2')] at hs
  exact Bool.noConfusion hs

/-! ## The route map -/

/-- **All four routes reach the period-2 rung.** Each of: a ranking (any measure, window, bound);
a width step (with the length-1 and length-2 base cases); amortised halving; or individual
termination of the word `10`, gives `HalfLineDies 2`. -/
theorem halfLineDies_two_of_routes :
    ((∃ P c f, Ranking (driveN 2 1) P c f) →  HalfLineDies 2) ∧
    ((∃ b, WidthStep (driveN 2 1) b) →
      (∀ S, 0 < S → S < 4 → ∃ T, dDiesBy (driveN 2 1) S T = true) → HalfLineDies 2) ∧
    ((∃ c e, 0 < c ∧ AmortizedHalving 2 c e) → HalfLineDies 2) ∧
    (WordDies (driveN 2 1) → HalfLineDies 2) := by
  refine ⟨?_, ?_, ?_, ?_⟩
  · rintro ⟨P, c, f, h⟩; exact halfLineDies_two_iff.2 (wordDies_of_ranking h)
  · rintro ⟨b, h⟩ hb; exact halfLineDies_two_iff.2 (wordDies_of_widthStep h hb)
  · rintro ⟨c, e, hc, h⟩; exact halfLineDies_of_amortized hc h
  · exact halfLineDies_two_iff.2

end GLM.Rule30
