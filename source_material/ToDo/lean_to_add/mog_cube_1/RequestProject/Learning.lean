import Mathlib
import RequestProject.CubeThought

/-!
# Learning the law table from a corpus of worlds

`FINAL_REPORT.md` §8 item 1 is the largest remaining hole in the package:

> **Learning.**  Nothing in the package is induced from data.  The smallest
> honest step would be fitting the law table of `CubeThought` from a corpus of
> worlds rather than writing it, and measuring how many of the 78 entailing
> pairs are recovered.

This file takes that step.  The law table is no longer written down: it is
*fitted*.  The learner is the simplest honest one — version-space elimination.
It starts from the hypothesis that **every** ordered pair of distinct
contingent literals is a law (2256 hypotheses) and deletes a hypothesis the
first time a world refutes it.  There is no scoring, no threshold and no
randomness; the corpus does all the work.

## What is proved, in order

*About the learner itself, for every corpus, with no finite check:*

* `learn_holds_on_corpus` — everything learned is true of the data it was
  learned from;
* `laws_are_never_missed` — every genuine entailment is learned from **any**
  corpus, so the learner's error is one-sided: it over-generates, it never
  misses.  Recall is 1 at every corpus size;
* `learn_antitone` — more data is never worse: a larger corpus learns a subset.

*What the data buys, measured inside Lean:*

* `learn_all_worlds` — from the complete corpus the learner returns **exactly**
  the hand-written table of `CubeThought.lawPairs`, as a list, not merely as a
  count.  The 78 pairs are recovered and nothing else is.
* `learning_curve` — the whole curve: `2256` hypotheses before any data, then
  `1680, 1545, 1394, 1227, 1099, 904, 762, 521, 365, 177, 84, 78` at
  `1, 2, 4, 8, 16, 32, 64, 128, 256, 384, 480, 481` worlds.  Precision rises
  from `78/2256 ≈ 3%` to 1.
* `prefix_corpus_needs_481` — reading the worlds in their natural order,
  **481 of the 512** are needed.  480 leave six false laws standing.
* `generalisation_error_at_256` — trained on half the worlds the learner keeps
  365 laws, of which **287 are refuted by the held-out half**: a 78.6% test
  error.  Learning from half the data is not nearly learning.
* `learned_law_is_false_witness` — an explicit false law that survives 16
  worlds, printed as the sentence it is.

*Which data, not how much:*

* `teaching_set_learns_the_table` — a corpus of **12** worlds, found by greedy
  search and verified here, learns exactly the table.  Forty times less data
  than the prefix needs.
* `teaching_set_irredundant` — and none of its 12 worlds can be dropped.
* `teaching_lower_bound` — no corpus of fewer than **4** worlds can ever learn
  the table, for any choice of worlds.  This is proved, not searched: one world
  refutes at most 576 hypotheses (`one_world_kills_at_most_576`) and 2178 must
  go.  So the true optimum lies in `[4, 12]`; the gap is honest and unclosed.

*On the cube:*

* `learned_table_on_the_surface` — the learned pairs, turned into law words by
  `CubeThought.lawWord`, are exactly the 27 distinct translations of the
  hand-written table, and every one is a genuine entailment.  The learner
  reconstructs the cube's law table, not just a list of pairs.
* `law_word_curve` — how the surface sees the learning: `172, 155, 93, 27`
  distinct translations at `16, 64, 256, 481` worlds.

## The honest limit

This is induction over a *fixed, finite, correctly labelled* hypothesis space:
the learner is told which literals exist and sees perfect data.  It does not
invent atoms, it does not tolerate a mislabelled world, and its bias — "a law
is a material implication between two literals" — is written by hand.  What it
does show is that the hand-written table of the package is not an assumption:
it is recoverable from twelve observations of the world.
-/

namespace Learning

open Semantics ThreeCube SentenceCode ClauseStore

set_option maxRecDepth 100000

/-! ## 1. The hypothesis space and the learner -/

/-- A hypothesis survives a world when the world does not refute it: either the
premise fails there, or the conclusion holds. -/
def surv (w : World) (p : Lit × Lit) : Bool := !evalLit p.1 w || evalLit p.2 w

/-- The hypothesis space: every ordered pair of distinct contingent literals is
a candidate law.  Nothing is presupposed about which ones hold. -/
def hyps : List (Lit × Lit) :=
  usefulLits.flatMap fun l => (usefulLits.filter fun m => decide (l ≠ m)).map fun m => (l, m)

theorem hyps_card : hyps.length = 2256 := by native_decide

/-- **The learner.**  Version-space elimination: keep exactly the hypotheses no
world of the corpus refutes. -/
def learn (ws : List World) : List (Lit × Lit) :=
  hyps.filter fun p => ws.all fun w => surv w p

/-! ## 2. What holds for every corpus -/

/-- Everything learned is true of the data it was learned from. -/
theorem learn_holds_on_corpus {ws : List World} {p : Lit × Lit} (h : p ∈ learn ws) :
    ∀ w ∈ ws, evalLit p.1 w = true → evalLit p.2 w = true := by
  have h' := (List.mem_filter.mp h).2
  intro w hw hp
  have := List.all_eq_true.mp h' w hw
  simp only [surv, hp, Bool.not_true, Bool.false_or] at this
  exact this

/-- Membership in the hypothesis space is exactly distinctness and contingency. -/
theorem mem_hyps_iff (p : Lit × Lit) :
    p ∈ hyps ↔ contingent p.1 = true ∧ contingent p.2 = true ∧ p.1 ≠ p.2 := by
  revert p; native_decide

/-- **Recall is 1, at every corpus size.**  A genuine entailment between
distinct contingent literals is learned from *any* corpus whatsoever: the
learner's error is one-sided.  It over-generates; it never misses. -/
theorem laws_are_never_missed (ws : List World) {l m : Lit}
    (hl : contingent l = true) (hm : contingent m = true) (hne : l ≠ m)
    (hent : entails l m = true) : (l, m) ∈ learn ws := by
  refine List.mem_filter.mpr ⟨(mem_hyps_iff _).mpr ⟨hl, hm, hne⟩, ?_⟩
  refine List.all_eq_true.mpr fun w _ => ?_
  by_cases h : evalLit l w = true
  · simp only [surv, h, Bool.not_true, Bool.false_or]
    exact (entails_iff l m).mp hent w h
  · simp only [surv, Bool.not_eq_true] at h ⊢
    simp [h]

/-- **More data is never worse.**  A corpus containing another learns a subset
of what the smaller one learns. -/
theorem learn_antitone {ws ws' : List World} (h : ∀ w ∈ ws, w ∈ ws') :
    ∀ p ∈ learn ws', p ∈ learn ws := by
  intro p hp
  refine List.mem_filter.mpr ⟨(List.mem_filter.mp hp).1, ?_⟩
  refine List.all_eq_true.mpr fun w hw => ?_
  exact List.all_eq_true.mp (List.mem_filter.mp hp).2 w (h w hw)

/-! ## 3. Complete data recovers the hand-written table exactly -/

/-- **The table is not an assumption.**  From the complete corpus the learner
returns exactly `CubeThought.lawPairs` — the same list, in the same order, that
the package previously wrote down by hand. -/
theorem learn_all_worlds : learn allWorlds = CubeThought.lawPairs := by native_decide

/-- Which in particular recovers all 78 laws and invents none. -/
theorem learn_all_worlds_card : (learn allWorlds).length = 78 := by
  rw [learn_all_worlds]; exact CubeThought.law_words_counted.1

/-- Everything the learner returns from complete data is a genuine entailment:
at the limit, precision is 1 as well as recall. -/
theorem learn_all_worlds_sound :
    ∀ p ∈ learn allWorlds, ∀ w : World, evalLit p.1 w = true → evalLit p.2 w = true := by
  rw [learn_all_worlds]; exact CubeThought.laws_are_sound_on_the_surface

/-! ## 4. The learning curve -/

/-- The corpus of the first `k` worlds, in the enumeration order of `allWorlds`. -/
def prefix_ (k : Nat) : List World := allWorlds.take k

/-- **The learning curve**, counted inside Lean.  With no data every one of the
2256 hypotheses stands; the false ones die off slowly, and the last of them only
at the 481st world. -/
theorem learning_curve :
    [0, 1, 2, 4, 8, 16, 32, 64, 128, 256, 384, 480, 481].map (fun k => (learn (prefix_ k)).length)
      = [2256, 1680, 1545, 1394, 1227, 1099, 904, 762, 521, 365, 177, 84, 78] := by
  native_decide

/-- **Volume is not the issue, coverage is.**  Read in their natural order the
worlds have to be read almost to the end: at 480 worlds six false laws are still
standing, and only the 481st kills the last of them. -/
theorem prefix_corpus_needs_481 :
    (learn (prefix_ 480)).length = 84 ∧ learn (prefix_ 481) = CubeThought.lawPairs := by
  refine ⟨by native_decide, by native_decide⟩

/-- **Generalisation, measured.**  Trained on the first half of the worlds the
learner keeps 365 laws; the held-out half refutes 287 of them.  Only the 78 true
ones survive the test set, which is the recall-1/precision-low picture again,
now as a train/test split. -/
theorem generalisation_error_at_256 :
    (learn (prefix_ 256)).length = 365 ∧
    ((learn (prefix_ 256)).filter
      (fun p => (allWorlds.drop 256).any (fun w => !surv w p))).length = 287 ∧
    ((learn (prefix_ 256)).filter
      (fun p => (allWorlds.drop 256).all (fun w => surv w p))).length = 78 := by
  refine ⟨by native_decide, by native_decide, by native_decide⟩

/-- An explicit casualty: after sixteen worlds the learner still believes that
whatever is *not hotter than the lamp* is *not boiling* — false, since the lamp
itself can boil, and refuted later in the corpus. -/
theorem learned_law_is_false_witness :
    ((Atom.hotter .water .lamp, false), (Atom.boiling .water, false)) ∈ learn (prefix_ 16) ∧
    entails (Atom.hotter .water .lamp, false) (Atom.boiling .water, false) = false := by
  refine ⟨by native_decide, by native_decide⟩

/-! ## 5. Which worlds, rather than how many -/

/-- Twelve worlds, found by greedy elimination over the 512 and verified below —
the corpus is given by index into `allWorlds` so that the list is small enough
to read. -/
def teachingIdx : List Nat := [59, 421, 110, 478, 499, 381, 266, 148, 193, 82, 273, 324]

/-- The teaching set itself. -/
def teachingSet : List World := teachingIdx.map fun i => allWorlds[i]!

theorem teachingSet_card : teachingSet.length = 12 := by native_decide

/-- **Twelve worlds suffice.**  From this corpus — 2.3% of the data the natural
order needs — the learner returns exactly the table. -/
theorem teaching_set_learns_the_table : learn teachingSet = CubeThought.lawPairs := by
  native_decide

/-- …and every one of the twelve is doing work: delete any single world and a
false law survives. -/
theorem teaching_set_irredundant :
    ∀ j < 12, 78 < (learn ((teachingIdx.eraseIdx j).map fun i => allWorlds[i]!)).length := by
  native_decide

/-! ### The lower bound: no corpus of three worlds can do it -/

private theorem length_filter_or_le {α : Type _} (l : List α) (f g : α → Bool) :
    (l.filter (fun x => f x || g x)).length ≤ (l.filter f).length + (l.filter g).length := by
  induction l with
  | nil => simp
  | cons a t ih =>
      by_cases hf : f a = true <;> by_cases hg : g a = true <;>
        simp [hf, hg] <;> omega

/-- The hypotheses a corpus has killed. -/
def killed (ws : List World) : List (Lit × Lit) :=
  hyps.filter fun p => !(ws.all fun w => surv w p)

theorem learn_add_killed (ws : List World) :
    (learn ws).length + (killed ws).length = 2256 := by
  rw [learn, killed, ← hyps_card]
  induction hyps with
  | nil => simp
  | cons a t ih =>
      by_cases h : (ws.all fun w => surv w a) = true <;>
        simp [h] <;> omega

/-- **One world is not very informative**: whatever it is, it refutes at most 576
of the 2256 hypotheses. -/
theorem one_world_kills_at_most_576 (w : World) :
    (hyps.filter fun p => !surv w p).length ≤ 576 := by
  have h : ∀ w ∈ allWorlds, (hyps.filter fun p => !surv w p).length ≤ 576 := by native_decide
  exact h w (mem_allWorlds w)

theorem killed_le (ws : List World) : (killed ws).length ≤ 576 * ws.length := by
  induction ws with
  | nil => simp [killed]
  | cons w t ih =>
      have hrw : killed (w :: t)
          = hyps.filter (fun p => (!surv w p) || !(t.all fun v => surv v p)) := by
        simp only [killed, List.all_cons, Bool.not_and]
      calc (killed (w :: t)).length
          = (hyps.filter (fun p => (!surv w p) || !(t.all fun v => surv v p))).length := by
            rw [hrw]
        _ ≤ (hyps.filter fun p => !surv w p).length
              + (hyps.filter fun p => !(t.all fun v => surv v p)).length :=
            length_filter_or_le _ _ _
        _ ≤ 576 + 576 * t.length := by
            have := one_world_kills_at_most_576 w
            have h2 : (hyps.filter fun p => !(t.all fun v => surv v p)).length ≤ 576 * t.length := ih
            omega
        _ = 576 * (w :: t).length := by simp [List.length_cons]; ring

/-- **A proved lower bound, for every corpus and not merely the ones a search
reached.**  2178 hypotheses have to die and no world kills more than 576 of them,
so no corpus of three worlds or fewer can learn the table.  With the twelve-world
witness above, the smallest teaching set has size between 4 and 12. -/
theorem teaching_lower_bound (ws : List World) (h : learn ws = CubeThought.lawPairs) :
    4 ≤ ws.length := by
  have h78 : (learn ws).length = 78 := by rw [h]; exact CubeThought.law_words_counted.1
  have hsum := learn_add_killed ws
  have hle := killed_le ws
  omega

/-! ## 6. The learned table on the cube -/

/-- The law words of the learned table. -/
def learnedTable (ws : List World) : List Tri :=
  (learn ws).map fun p => CubeThought.lawWord p.1 p.2

/-- **The learner reconstructs the cube's law table.**  Turned into translations
of the surface, the pairs learned from complete data are the same 27 distinct
words the hand-written table used — and each is a genuine entailment. -/
theorem learned_table_on_the_surface :
    (learnedTable allWorlds).eraseDups.length = 27 ∧
    (∀ p ∈ learn allWorlds,
      dxor (encode (clauseRec p.1)) (CubeThought.lawWord p.1 p.2) = encode (clauseRec p.2)) := by
  refine ⟨?_, fun p _ => CubeThought.apply_law p.1 p.2⟩
  rw [learnedTable, learn_all_worlds]
  exact CubeThought.law_words_counted.2

/-- How the surface sees the learning: the number of distinct translations the
learner would have to store, as the corpus grows.  A half-learned table is not a
small table — it is six times too big. -/
theorem law_word_curve :
    [16, 64, 256, 481].map (fun k => (learnedTable (prefix_ k)).eraseDups.length)
      = [172, 155, 93, 27] := by
  native_decide

end Learning
