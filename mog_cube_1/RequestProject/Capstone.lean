import Mathlib
import RequestProject.Learning
import RequestProject.Chat

/-!
# The capstone: sentences that are learned, uttered, and true

Every earlier file supplies one half of the original question.  `Learning.lean`
shows that the law table is not an assumption — twelve observations of the world
are enough to fit it.  `Chat.lean` shows that the system can put a law into
English and that it cannot say a false thing.  This file joins the two halves,
so that the chain from *data* to *English sentence* is closed with no
hand-written law anywhere in it:

```
12 observed worlds  ──learn──▶  78 pairs  ──render──▶  78 English conditionals
```

and then asks the three questions that matter about the result.

* `learned_sentences_are_assertible` — every one of the 78 sentences passes the
  system's *own* test for a law: the antecedent entails the consequent in all
  512 worlds, both halves are contingent, and they are distinct.  Nothing
  uttered is a coincidence of the observed data and nothing is vacuous.
* `learned_sentences_are_complete` — and the converse: *any* law of the world
  expressible in the lexicon is one of the sentences uttered.  Nothing true is
  left unsaid.
* `why_answer_is_a_learned_law` — the sentences are not a separate list bolted
  on.  Whenever the system answers a *why* question with a reason, the pair it
  used is one the learner recovers, from any corpus at all.  The explanations
  the system gives are licensed by what it learned.

The failure is recorded in the same terms.  `premature_sentence_is_false`
exhibits an English sentence the system would have uttered after sixteen worlds
— *if the water is not hotter than the lamp then the water is not boiling* —
which is false, and which the twelve-world teaching corpus does not produce.
Learning from more data in the wrong order is not the same as learning.
-/

namespace Capstone

open Semantics Learning

set_option maxRecDepth 100000

/-! ## 1. What the trained system says -/

/-- The English the system utters after learning from a corpus: one conditional
per learned pair. -/
def learnedSentences (ws : List World) : List String :=
  (learn ws).map fun p => Chat.render (.law p.1 p.2)

/-- **Seventy-eight sentences, all different**, learned from twelve worlds. -/
theorem learned_sentences_count :
    (learnedSentences teachingSet).length = 78 ∧
    (learnedSentences teachingSet).eraseDups.length = 78 := by
  refine ⟨?_, by native_decide⟩
  rw [learnedSentences, List.length_map, teaching_set_learns_the_table]
  exact CubeThought.law_words_counted.1

/-- The first five, pinned. -/
theorem learned_sentences_sample :
    (learnedSentences teachingSet).take 5 =
      ["if the water is frozen then the water is not boiling",
       "if the water is frozen then the water is not warm",
       "if the stone is frozen then the stone is not boiling",
       "if the stone is frozen then the stone is not warm",
       "if the lamp is frozen then the lamp is not boiling"] := by
  native_decide

/-! ## 2. Everything uttered passes the system's own test -/

/-- **Soundness of the trained system.**  Each learned pair, read as the
sentence *if … then …*, is true in every world — and `evalS` of a `law` is not a
statement about the present world but the full test `lawOK`: entailment across
all 512 worlds, both halves contingent, the two halves distinct.  So the trained
system asserts no coincidence, no tautology and no vacuity. -/
theorem learned_sentences_are_assertible :
    ∀ p ∈ learn teachingSet, ∀ w : World, evalS (.law p.1 p.2) w = true := by
  have h : CubeThought.lawPairs.all (fun p => lawOK p.1 p.2) = true := by native_decide
  intro p hp w
  rw [teaching_set_learns_the_table] at hp
  have hEq : evalS (.law p.1 p.2) w = lawOK p.1 p.2 := rfl
  rw [hEq]
  exact List.all_eq_true.mp h p hp

/-- **Completeness of the trained system.**  Every law of the world that the
lexicon can state — a genuine entailment between two distinct contingent
literals — is among the sentences uttered.  Together with the previous theorem
the trained system says all the laws and only the laws. -/
theorem learned_sentences_are_complete {l m : Lit}
    (hl : contingent l = true) (hm : contingent m = true) (hne : l ≠ m)
    (hent : entails l m = true) :
    Chat.render (.law l m) ∈ learnedSentences teachingSet := by
  refine List.mem_map.mpr ⟨(l, m), ?_, rfl⟩
  exact laws_are_never_missed teachingSet hl hm hne hent

/-! ## 3. The explanations are licensed by the learning -/

/-- A literal entailed by a contingent one, and true somewhere, is itself
contingent: it holds where the premise holds and fails where the conclusion
fails. -/
theorem contingent_of_entails {l m : Lit} {w : World}
    (hent : entails m l = true) (hl : contingent l = true) (hm : evalLit m w = true) :
    contingent m = true := by
  have hsat : satisfiable m = true :=
    List.any_eq_true.mpr ⟨w, mem_allWorlds w, hm⟩
  have hnl : satisfiable (negL l) = true := (Bool.and_eq_true _ _).mp hl |>.2
  obtain ⟨w', -, hw'⟩ := List.any_eq_true.mp hnl
  have hlf : evalLit l w' = false := by
    rw [evalLit_negL] at hw'; simpa using hw'
  have hmf : evalLit m w' = false := by
    by_contra hc
    have := (entails_iff m l).mp hent w' (by simpa using hc)
    rw [this] at hlf; exact Bool.noConfusion hlf
  have hsatn : satisfiable (negL m) = true :=
    List.any_eq_true.mpr ⟨w', mem_allWorlds w', by rw [evalLit_negL, hmf]; rfl⟩
  simp [contingent, hsat, hsatn]

/-- **The explanations are learned, not stipulated.**  Whenever the system
answers *why is …?* with a reason, the implication it leaned on is a pair the
learner recovers — from the twelve-world teaching corpus, and in fact from any
corpus whatsoever, since recall is 1. -/
theorem why_answer_is_a_learned_law (w : World) (l m : Lit) (ws : List World)
    (h : Chat.answer (.why l) w = .because l m) : (m, l) ∈ learn ws := by
  have hev : evalS (.because l m) w = true := by
    have := Chat.answer_true (.why l) w
    rwa [h] at this
  simp only [evalS, Bool.and_eq_true, decide_eq_true_eq] at hev
  obtain ⟨⟨⟨⟨-, hmw⟩, hent⟩, hne⟩, hcl⟩ := hev
  exact laws_are_never_missed ws (contingent_of_entails hent hcl hmw) hcl
    (Ne.symm hne) hent

/-- **The case occurs**, so the previous theorem is not vacuous: in world 59 the
system explains why the water is not warm by saying that it is frozen, and the
implication behind that explanation is one of the seventy-eight sentences it
learned. -/
theorem why_answer_witness :
    Chat.render (Chat.answer (.why (Atom.warm .water, false)) allWorlds[59]!)
        = "the water is not warm because the water is frozen" ∧
    ((Atom.frozen .water, true), (Atom.warm .water, false)) ∈ learn teachingSet ∧
    "if the water is frozen then the water is not warm" ∈ learnedSentences teachingSet := by
  refine ⟨by native_decide, by native_decide, ?_⟩
  exact List.mem_map.mpr ⟨_, (by native_decide :
    ((Atom.frozen .water, true), (Atom.warm .water, false)) ∈ learn teachingSet), rfl⟩

/-! ## 4. The failure, in the same terms -/

/-- **What a half-trained system says.**  After sixteen worlds the learner still
holds a false law, and the system would utter it as a plain English sentence.
The sentence is false — the lamp can boil while nothing is hotter than it — and
the twelve-world teaching corpus never produces it.  More data read in the wrong
order is not the same as the right data. -/
theorem premature_sentence_is_false :
    "if the water is not hotter than the lamp then the water is not boiling"
        ∈ learnedSentences (prefix_ 16) ∧
    entails (Atom.hotter .water .lamp, false) (Atom.boiling .water, false) = false ∧
    "if the water is not hotter than the lamp then the water is not boiling"
        ∉ learnedSentences teachingSet := by
  refine ⟨?_, learned_law_is_false_witness.2, ?_⟩
  · exact List.mem_map.mpr ⟨_, learned_law_is_false_witness.1, rfl⟩
  · native_decide

/-- The measured size of the mistake: sixteen worlds leave 1099 sentences
standing, of which 1021 are false; twelve chosen worlds leave exactly the 78
true ones. -/
theorem premature_sentence_count :
    (learnedSentences (prefix_ 16)).length = 1099 ∧
    ((learn (prefix_ 16)).filter (fun p => !entails p.1 p.2)).length = 1021 := by
  refine ⟨?_, by native_decide⟩
  rw [learnedSentences, List.length_map]
  exact (by native_decide : (learn (prefix_ 16)).length = 1099)

end Capstone
