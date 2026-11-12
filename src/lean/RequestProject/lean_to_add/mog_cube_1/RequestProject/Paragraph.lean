import Mathlib
import RequestProject.WideDiscourse

/-!
# Paragraphs that end when there is nothing left to say

Report 3 §5.3:

> **Paragraph length is fuel, not content** — the generator stops at seven
> clauses by construction.

`Discourse.grow` and `WideDiscourse.wgrow` both take a number and count down, so
`corpus_facts` could prove the flat and unflattering fact that *every* paragraph
in the corpus has exactly seven clauses.  That is a property of the counter, not
of the world.

This file removes the counter.  `cgrow` recurses on the **stock of things left
to say**: each clause it utters is removed from the stock, so the recursion is
structural on a shrinking list and needs no fuel.  The paragraph therefore ends
in exactly one circumstance — `cpick` finds no licensed clause
(`cgrow_ends_only_when_nothing_is_licensed`) — which is content, not
arithmetic.

## What is measured

Two stocks are tried, and they say different things.

* Given **everything contingent that is true** — assertions and denials alike —
  the paragraph runs to 24 clauses in every world (`content_lengths`).  That is
  still a constant, but now for a reason about the world rather than about the
  generator: each of the 24 words is either true or false, so exactly 24
  contingent literals hold in every world, and the generator says all of them
  (`ccorpus_exhausts_the_stock`).
* Given only the **assertions**, the length follows the world: between 3 and 10
  clauses, seven different lengths across the 512 worlds
  (`assertion_lengths_vary`), and in each world exactly as many clauses as there
  are true facts to report (`assertion_length_is_the_fact_count`).

Every paragraph of both corpora is valid in the original sense — sound,
non-repeating, every connective licensed (`ccorpus_facts`, `pcorpus_facts`).

-/

namespace Paragraph

open Semantics Discourse WideDiscourse

set_option maxRecDepth 100000

/-! ## 1. A generator with no fuel -/

/-- The clause `wpick` chooses is one of the candidates it was offered. -/
theorem wpick_mem {cs : List Lit} {live : List World} {ctx : Ctx} {s : Step}
    (h : wpick cs live ctx = some s) : s.lit ∈ cs := by
  unfold wpick at h
  split at h
  · rename_i l hl
    cases h; exact List.mem_of_find?_eq_some hl
  · split at h
    · rename_i l hl
      cases h; exact List.mem_of_find?_eq_some hl
    · split at h
      · rename_i l hl
        cases h; exact List.mem_of_find?_eq_some hl
      · exact absurd h (by simp)

/-- **The fuel-free generator.**  Every clause uttered is struck off the stock,
so the recursion is structural on the stock and stops only when nothing further
is licensed. -/
def cgrow (cs : List Lit) (live : List World) (ctx : Ctx) : List Step :=
  match h : wpick cs live ctx with
  | none => []
  | some s => s :: cgrow (cs.erase s.lit) (liveWith live s.lit) (s.lit :: ctx)
termination_by cs.length
decreasing_by
  have hmem : s.lit ∈ cs := wpick_mem h
  have h1 := List.length_erase_of_mem hmem
  have h2 := List.length_pos_of_mem hmem
  omega

/-- **The paragraph ends only because there is nothing left to say.** -/
theorem cgrow_ends_only_when_nothing_is_licensed (cs : List Lit) (live : List World) (ctx : Ctx)
    (h : cgrow cs live ctx = []) : wpick cs live ctx = none := by
  rw [cgrow] at h
  split at h
  · assumption
  · exact absurd h (by simp)

/-- Unfolding, in the form used below. -/
theorem cgrow_cons {cs : List Lit} {live : List World} {ctx : Ctx} {s : Step}
    (h : wpick cs live ctx = some s) :
    cgrow cs live ctx = s :: cgrow (cs.erase s.lit) (liveWith live s.lit) (s.lit :: ctx) := by
  rw [cgrow]
  split
  · rename_i h'; rw [h] at h'; exact absurd h' (by simp)
  · rename_i s' h'
    rw [h] at h'
    have : s' = s := by simpa using h'.symm
    subst this; rfl

/-- Every clause the generator utters was on the stock it started from. -/
theorem cgrow_subset : ∀ (cs : List Lit) (live : List World) (ctx : Ctx) (s : Step),
    s ∈ cgrow cs live ctx → s.lit ∈ cs := by
  intro cs
  induction hn : cs.length using Nat.strong_induction_on generalizing cs with
  | _ k ih =>
    intro live ctx s hs
    rcases hp : wpick cs live ctx with _ | s'
    · rw [cgrow] at hs
      split at hs
      · simp at hs
      · rename_i s'' h''; rw [hp] at h''; exact absurd h'' (by simp)
    · rw [cgrow_cons hp] at hs
      rcases List.mem_cons.mp hs with rfl | hs'
      · exact wpick_mem hp
      · have hmem : s'.lit ∈ cs := wpick_mem hp
        have hlt : (cs.erase s'.lit).length < cs.length := by
          have h1 := List.length_erase_of_mem hmem
          have h2 := List.length_pos_of_mem hmem
          omega
        have := ih (cs.erase s'.lit).length (by omega) (cs.erase s'.lit) rfl
          (liveWith live s'.lit) (s'.lit :: ctx) s hs'
        exact List.mem_of_mem_erase this

/-- **Soundness, without enumerating anything.**  If everything on the stock is
true in `w`, every clause of the paragraph is true in `w`. -/
theorem cgrow_sound {w : World} {cs : List Lit} {live : List World} {ctx : Ctx}
    (hcs : ∀ l ∈ cs, evalLit l w = true) (s : Step) (hs : s ∈ cgrow cs live ctx) :
    evalLit s.lit w = true := hcs _ (cgrow_subset cs live ctx s hs)

/-! ## 2. The paragraph about a world -/

/-- The fuel-free paragraph the system offers about a whole world. -/
def cdescribe (w : World) : Option WPara :=
  let cs := wcandidates w
  match cs.head? with
  | none => none
  | some l => some ⟨l, cgrow (cs.erase l) (liveWith allWorlds l) [l]⟩

/-- Everything said in the fuel-free paragraph about `w` is true in `w`. -/
theorem cdescribe_sound {w : World} {p : WPara} (h : cdescribe w = some p) :
    ∀ l ∈ wparaLits p, evalLit l w = true := by
  intro l hl
  have hcand : ∀ m ∈ wcandidates w, evalLit m w = true := by
    intro m hm
    exact (List.mem_filter.mp hm).2
  simp only [cdescribe] at h
  split at h
  · exact absurd h (by simp)
  · rename_i m hm
    have hp : p = ⟨m, cgrow ((wcandidates w).erase m) (liveWith allWorlds m) [m]⟩ := by
      simpa using h.symm
    subst hp
    simp only [wparaLits, List.mem_cons, List.mem_map] at hl
    rcases hl with rfl | ⟨s, hs, rfl⟩
    · exact hcand _ (List.mem_of_mem_head? hm)
    · exact hcand _ (List.mem_of_mem_erase
        (cgrow_subset _ _ _ s hs))

/-! ## 3. Measured over every world -/

/-- One fuel-free paragraph per world. -/
def ccorpus : List (World × WPara) :=
  allWorlds.filterMap fun w => (cdescribe w).map fun p => (w, p)

/-- The number of clauses of each paragraph. -/
def clengths : List Nat := ccorpus.map fun wp => (wparaLits wp.2).length

/-- **The corpus of fuel-free paragraphs is still valid** — every clause true,
every connective licensed, nothing repeated — and it is far longer than the
fuelled one: 11776 joined clauses over the 512 worlds against 3072. -/
theorem ccorpus_facts :
    ccorpus.length = 512 ∧
    (ccorpus.all fun wp => wvalid wp.1 wp.2) = true ∧
    (ccorpus.flatMap fun wp => wp.2.steps).length = 11776 := by
  refine ⟨?_, ?_, ?_⟩ <;> native_decide

/-- **Length is now the size of the stock.**  Every paragraph has 24 clauses,
which is not a fuel constant but the number of contingent literals true in a
world: each of the 24 words holds or fails, and the generator says every one of
those 24 facts. -/
theorem content_lengths :
    clengths.min? = some 24 ∧ clengths.max? = some 24 ∧ clengths.sum = 12288 := by
  refine ⟨?_, ?_, ?_⟩ <;> native_decide

/-- The paragraph really does exhaust the stock: in every world it has exactly
as many clauses as there are true contingent literals. -/
theorem ccorpus_exhausts_the_stock :
    (ccorpus.all fun wp => decide ((wparaLits wp.2).length = (wcandidates wp.1).length)) = true := by
  native_decide

/-- Everything in every one of these paragraphs is true. -/
theorem ccorpus_sound : ∀ wp ∈ ccorpus, ∀ l ∈ wparaLits wp.2, evalLit l wp.1 = true := by
  intro wp hwp l hl
  exact wpara_sound (List.all_eq_true.mp ccorpus_facts.2.1 wp hwp) l hl

/-! ## 4. Assertions only, where the length follows the world

Saying "the stone is not boiling" is as true as saying "the stone is frozen",
and counting both is why the paragraph above has the same length everywhere.
Restricting the stock to what the world *positively* affords makes the length a
property of the world. -/

/-- The positive facts of a world. -/
def factStock (w : World) : List Lit := (wcandidates w).filter fun l => l.2

/-- The paragraph of assertions about a world. -/
def pdescribe (w : World) : Option WPara :=
  match (factStock w).head? with
  | none => none
  | some l => some ⟨l, cgrow ((factStock w).erase l) (liveWith allWorlds l) [l]⟩

/-- Everything said in the assertion paragraph about `w` is true in `w`. -/
theorem pdescribe_sound {w : World} {p : WPara} (h : pdescribe w = some p) :
    ∀ l ∈ wparaLits p, evalLit l w = true := by
  intro l hl
  have hstock : ∀ m ∈ factStock w, evalLit m w = true := by
    intro m hm
    exact (List.mem_filter.mp (List.mem_filter.mp hm).1).2
  simp only [pdescribe] at h
  split at h
  · exact absurd h (by simp)
  · rename_i m hm
    have hp : p = ⟨m, cgrow ((factStock w).erase m) (liveWith allWorlds m) [m]⟩ := by
      simpa using h.symm
    subst hp
    simp only [wparaLits, List.mem_cons, List.mem_map] at hl
    rcases hl with rfl | ⟨s, hs, rfl⟩
    · exact hstock _ (List.mem_of_mem_head? hm)
    · exact hstock _ (List.mem_of_mem_erase (cgrow_subset _ _ _ s hs))

def pcorpus : List (World × WPara) :=
  allWorlds.filterMap fun w => (pdescribe w).map fun p => (w, p)

def plengths : List Nat := pcorpus.map fun wp => (wparaLits wp.2).length

/-- **The assertion corpus is valid too**, and joins 3712 clauses. -/
theorem pcorpus_facts :
    pcorpus.length = 512 ∧
    (pcorpus.all fun wp => wvalid wp.1 wp.2) = true ∧
    (pcorpus.flatMap fun wp => wp.2.steps).length = 3712 := by
  refine ⟨?_, ?_, ?_⟩ <;> native_decide

/-- **Length now depends on the world.**  The shortest paragraph is 3 clauses
and the longest 10, and seven distinct lengths occur — against the flat 7 of the
fuelled generator. -/
theorem assertion_lengths_vary :
    plengths.min? = some 3 ∧ plengths.max? = some 10 ∧ plengths.sum = 4224 ∧
      plengths.eraseDups.length = 7 := by
  refine ⟨?_, ?_, ?_, ?_⟩ <;> native_decide

/-- …and the length is exactly the number of facts the world affords. -/
theorem assertion_length_is_the_fact_count :
    (pcorpus.all fun wp => decide ((wparaLits wp.2).length = (factStock wp.1).length)) = true := by
  native_decide

/-- Everything in every assertion paragraph is true. -/
theorem pcorpus_sound : ∀ wp ∈ pcorpus, ∀ l ∈ wparaLits wp.2, evalLit l wp.1 = true := by
  intro wp hwp l hl
  exact wpara_sound (List.all_eq_true.mp pcorpus_facts.2.1 wp hwp) l hl

/-- The fuel-free paragraph about the demonstration world. -/
def cdemo : String :=
  match cdescribe demoWorld with
  | some p => renderWPara p
  | none => "nothing to say"

/-- The assertion paragraph about the demonstration world. -/
def pdemo : String :=
  match pdescribe demoWorld with
  | some p => renderWPara p
  | none => "nothing to say"

end Paragraph
