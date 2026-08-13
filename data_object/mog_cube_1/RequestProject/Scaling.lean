import Mathlib
import RequestProject.Relative

/-!
# Scaling: the counts as functions of `n`

`FINAL_REPORT.md` §8 item 2:

> **A real scaling theorem.**  Stage 4 is evidence that the constructions
> survive an eight-fold widening.  A statement that soundness holds for every
> `n`, with the counts as functions of `n`, is within reach for the parts that
> are already schematic and out of reach for the parts that are finite checks.

This file supplies the statement.  Three counts that the package had measured
at `n = 24` by compiled evaluation are here *derived*, as polynomials in `n`,
for every world of every size:

| quantity | measured at `n = 24` | proved for all `n` |
|---|---|---|
| contingent literals | 3600 | `6n + 6n²` (`usefulLits_length_formula`) |
| facts stated about a world | 1800 | `3n + 3n²` (`describe_length_formula`) |
| quantified sentences uttered | 12 | `12`, independent of `n` (`describeQ_length_formula`) |
| relative-clause sentences uttered | 144 | `144`, independent of `n` (`describeR_length_formula`) |

The middle two are the interesting ones.  The first says the system's
description of a world is *exactly half* of its contingent vocabulary — no
world is more or less describable than any other, and the length of what the
system says is a function of the lexicon alone.  The last two say the opposite
for the quantified layers: what the system can say about a world in quantified
form does not grow with the world at all.

The engine of all of it is `wcontingent_iff_not_reflexive`: a literal of the
wide lexicon fails to be contingent exactly when its word is a comparison of a
thing with itself.  That is proved by exhibiting worlds, not by enumeration, so
it holds for every `n` — and it turns `WideWorld.noncontingent_are_reflexive`,
which was a finite check at `n = 24`, into a theorem.
-/

namespace Scaling

open WideWorld

/-! ## 1. Contingency, decided by the word alone -/

/-- The reflexive comparisons: *hotter than itself*, *heavier than itself*,
*the same temperature as itself*. -/
def isRefl {n} : Atom n → Bool
  | .hotter e f => decide (e = f)
  | .heavier e f => decide (e = f)
  | .sameTemp e f => decide (e = f)
  | _ => false

/-- A world in which everything reads the same. -/
def constW {n} (t : Fin 6) (m : Fin 3) : World n := fun _ => (t, m)

/-- A world in which one thing reads `s₁` and everything else `s₂`. -/
def splitW {n} (e : Fin n) (s₁ s₂ : LS) : World n := fun x => if x = e then s₁ else s₂

/-- **Every non-reflexive word is contingent**, witnessed by two worlds that are
written down rather than searched for. -/
theorem atom_takes_both {n} (a : Atom n) (h : isRefl a = false) :
    (∃ w : World n, evalAtom a w = true) ∧ (∃ w : World n, evalAtom a w = false) := by
  cases a with
  | frozen e => exact ⟨⟨constW 0 0, by simp [evalAtom, tp, constW, tempVal]⟩,
      ⟨constW 2 0, by simp [evalAtom, tp, constW, tempVal]⟩⟩
  | warm e => exact ⟨⟨constW 2 0, by simp [evalAtom, tp, constW, tempVal]⟩,
      ⟨constW 0 0, by simp [evalAtom, tp, constW, tempVal]⟩⟩
  | hot e => exact ⟨⟨constW 3 0, by simp [evalAtom, tp, constW, tempVal]⟩,
      ⟨constW 0 0, by simp [evalAtom, tp, constW, tempVal]⟩⟩
  | boiling e => exact ⟨⟨constW 4 0, by simp [evalAtom, tp, constW, tempVal]⟩,
      ⟨constW 0 0, by simp [evalAtom, tp, constW, tempVal]⟩⟩
  | heavy e => exact ⟨⟨constW 0 1, by simp [evalAtom, ms, constW, massVal]⟩,
      ⟨constW 0 0, by simp [evalAtom, ms, constW, massVal]⟩⟩
  | massive e => exact ⟨⟨constW 0 2, by simp [evalAtom, ms, constW, massVal]⟩,
      ⟨constW 0 0, by simp [evalAtom, ms, constW, massVal]⟩⟩
  | hotter e f =>
      have hne : e ≠ f := by simpa [isRefl] using h
      exact ⟨⟨splitW e (5, 0) (0, 0), by simp [evalAtom, tp, splitW, Ne.symm hne, tempVal]⟩,
        ⟨splitW e (0, 0) (0, 0), by simp [evalAtom, tp, splitW, tempVal]⟩⟩
  | heavier e f =>
      have hne : e ≠ f := by simpa [isRefl] using h
      exact ⟨⟨splitW e (0, 2) (0, 0), by simp [evalAtom, ms, splitW, Ne.symm hne, massVal]⟩,
        ⟨splitW e (0, 0) (0, 0), by simp [evalAtom, ms, splitW, massVal]⟩⟩
  | sameTemp e f =>
      have hne : e ≠ f := by simpa [isRefl] using h
      exact ⟨⟨constW 0 0, by simp [evalAtom, tp, constW]⟩,
        ⟨splitW e (5, 0) (0, 0), by simp [evalAtom, tp, splitW, Ne.symm hne, tempVal]⟩⟩

/-- **And every reflexive word is constant**: nothing is hotter or heavier than
itself, and everything is the same temperature as itself. -/
theorem refl_atom_constant {n} (a : Atom n) (h : isRefl a = true) :
    (∀ w : World n, evalAtom a w = true) ∨ (∀ w : World n, evalAtom a w = false) := by
  cases a with
  | frozen e => simp [isRefl] at h
  | warm e => simp [isRefl] at h
  | hot e => simp [isRefl] at h
  | boiling e => simp [isRefl] at h
  | heavy e => simp [isRefl] at h
  | massive e => simp [isRefl] at h
  | hotter e f =>
      have hef : e = f := by simpa [isRefl] using h
      subst hef; exact Or.inr fun w => by simp [evalAtom]
  | heavier e f =>
      have hef : e = f := by simpa [isRefl] using h
      subst hef; exact Or.inr fun w => by simp [evalAtom]
  | sameTemp e f =>
      have hef : e = f := by simpa [isRefl] using h
      subst hef; exact Or.inl fun w => by simp [evalAtom]

/-- **Contingency is a property of the word, not of the world size.**  A literal
of the wide lexicon says something exactly when its word is not a comparison of
a thing with itself.  `WideWorld.noncontingent_are_reflexive` checked this at
`n = 24`; here it is for every `n`. -/
theorem wcontingent_iff_not_reflexive {n} (l : Lit n) :
    wcontingent l = true ↔ isRefl l.1 = false := by
  obtain ⟨a, b⟩ := l
  constructor
  · intro hc
    by_contra hr
    have hr' : isRefl a = true := by simpa using hr
    obtain ⟨hw, hw'⟩ := (wcontingent_iff (a, b)).mp hc
    obtain ⟨w1, h1⟩ := hw
    obtain ⟨w2, h2⟩ := hw'
    rcases refl_atom_constant a hr' with hall | hall
    · rw [evalLit] at h1 h2
      simp only [hall w1, hall w2] at h1 h2
      cases b <;> simp at h1 h2
    · rw [evalLit] at h1 h2
      simp only [hall w1, hall w2] at h1 h2
      cases b <;> simp at h1 h2
  · intro hr
    obtain ⟨⟨wT, hT⟩, ⟨wF, hF⟩⟩ := atom_takes_both a hr
    refine (wcontingent_iff (a, b)).mpr ?_
    cases b
    · exact ⟨⟨wF, by simp [evalLit, hF]⟩, ⟨wT, by simp [evalLit, hT]⟩⟩
    · exact ⟨⟨wT, by simp [evalLit, hT]⟩, ⟨wF, by simp [evalLit, hF]⟩⟩

/-- The same as a Boolean identity, ready for counting. -/
theorem wcontingent_eq {n} (a : Atom n) (b : Bool) : wcontingent (a, b) = !isRefl a := by
  cases h : isRefl a
  · simpa using (wcontingent_iff_not_reflexive (a, b)).mpr h
  · simp only [Bool.not_true]
    by_contra hc
    have : wcontingent ((a, b) : Lit n) = true := by simpa using hc
    rw [wcontingent_iff_not_reflexive] at this
    simp [h] at this

/-! ## 2. Counting the words -/

private theorem sum_map_ite_zero {α : Type _} (L : List α) (p : α → Bool) (c : ℕ) :
    (L.map (fun x => if p x = true then 0 else c)).sum = c * L.countP (fun x => !p x) := by
  induction L with
  | nil => simp
  | cons x t ih =>
      rw [List.map_cons, List.sum_cons, List.countP_cons, ih]
      cases h : p x
      · simp
        ring
      · simp

private theorem countP_ne_finRange (n : ℕ) (e : Fin n) :
    (List.finRange n).countP (fun f => decide ¬(e = f)) = n - 1 := by
  have hfun : (fun f : Fin n => decide (f = e)) = (fun f : Fin n => f == e) := rfl
  have h1 : (List.finRange n).countP (fun f => decide (f = e)) = 1 := by
    rw [hfun, ← List.count_eq_countP]
    exact List.count_eq_one_of_mem (List.nodup_finRange n) (List.mem_finRange e)
  have h2 := List.length_eq_countP_add_countP
    (l := List.finRange n) (p := fun f => decide (f = e))
  simp only [List.length_finRange] at h2
  have h3 : (List.finRange n).countP (fun f => decide ¬decide (f = e) = true)
      = (List.finRange n).countP (fun f => decide ¬(e = f)) := by
    refine List.countP_congr fun f _ => ?_
    by_cases hfe : f = e
    · subst hfe; simp
    · simp [hfe, Ne.symm hfe]
  omega

/-- **The words that say something, counted as a polynomial in `n`**: of the
`6n + 3n²` words, the `3n` reflexive comparisons say nothing and the rest do. -/
theorem contentful_atom_count (n : ℕ) :
    (allAtoms n).countP (fun a => !isRefl a) = 3 * n + 3 * n ^ 2 := by
  rw [allAtoms, List.countP_append]
  have hA : ((ents n).flatMap fun e =>
      [Atom.frozen e, .warm e, .hot e, .boiling e, .heavy e, .massive e]).countP
        (fun a => !isRefl a) = 6 * n := by
    rw [List.countP_flatMap]
    have : ∀ e : Fin n, (List.countP (fun a => !isRefl a) ∘
        (fun e : Fin n => [Atom.frozen e, Atom.warm e, Atom.hot e, Atom.boiling e,
          Atom.heavy e, Atom.massive e])) e = 6 := by
      intro e; simp [isRefl]
    rw [List.map_congr_left fun e _ => this e]
    simp [ents, List.sum_replicate, Nat.mul_comm]
  have hB : ((ents n).flatMap fun e => (ents n).flatMap fun f =>
      [Atom.hotter e f, .heavier e f, .sameTemp e f]).countP
        (fun a => !isRefl a) = 3 * n * (n - 1) := by
    rw [List.countP_flatMap]
    have hinner : ∀ e : Fin n, (List.countP (fun a => !isRefl a) ∘
        (fun e : Fin n => (ents n).flatMap fun f =>
          [Atom.hotter e f, Atom.heavier e f, Atom.sameTemp e f])) e = 3 * (n - 1) := by
      intro e
      simp only [Function.comp_apply]
      rw [List.countP_flatMap]
      have h3 : ∀ f : Fin n, (List.countP (fun a => !isRefl a)
          [Atom.hotter e f, Atom.heavier e f, Atom.sameTemp e f])
            = if e = f then 0 else 3 := by
        intro f
        by_cases hef : e = f <;> simp [isRefl, hef]
      have : ((ents n).map (fun f => List.countP (fun a => !isRefl a)
          [Atom.hotter e f, Atom.heavier e f, Atom.sameTemp e f])).sum
          = ((ents n).map (fun f => if e = f then 0 else 3)).sum := by
        exact congrArg List.sum (List.map_congr_left fun f _ => h3 f)
      simp only [Function.comp_def]
      rw [this]
      have hsum : ((ents n).map (fun f => if e = f then 0 else 3)).sum
          = 3 * (ents n).countP (fun f => decide ¬(e = f)) := by
        have := sum_map_ite_zero (ents n) (fun f => decide (e = f)) 3
        simpa using this
      rw [hsum, ents, countP_ne_finRange n e]
    rw [List.map_congr_left fun e _ => hinner e]
    simp [ents, List.sum_replicate, Nat.mul_comm]
    ring
  rw [hA, hB]
  cases n with
  | zero => simp
  | succ m => simp only [Nat.add_sub_cancel]; ring

/-- **The contingent lexicon is a polynomial in `n`.**  At `n = 24` this is the
3600 of `WideWorld.wide_vocab_counts`; here it is for every world size. -/
theorem usefulLits_length_formula (n : ℕ) : (usefulLits n).length = 6 * n + 6 * n ^ 2 := by
  have hstep : (usefulLits n).length = 2 * (allAtoms n).countP (fun a => !isRefl a) := by
    rw [usefulLits, allLits, ← List.countP_eq_length_filter, List.countP_flatMap]
    have h2 : ∀ a : Atom n, (List.countP wcontingent ∘
        (fun a : Atom n => [(a, true), (a, false)])) a
          = if isRefl a = true then 0 else 2 := by
      intro a
      cases h : isRefl a <;>
        simp [wcontingent_eq, h]
    rw [List.map_congr_left fun a _ => h2 a, sum_map_ite_zero]
  rw [hstep, contentful_atom_count]
  ring

/-! ## 3. How much the system says about a world -/

/-- **The length of a description is a function of the lexicon, not of the
world.**  For every `n` and every one of the `18ⁿ` worlds, the system states
exactly `3n + 3n²` facts — exactly half of its contingent vocabulary, since of
each literal and its denial precisely one is true.  At `n = 24` this is the 1800
of `WideWorld.demoWide_count`, now proved for all worlds at once. -/
theorem describe_length_formula {n : ℕ} (w : World n) :
    (describe w).length = 3 * n + 3 * n ^ 2 := by
  have hfilter : describe w
      = (allLits n).filter (fun l => evalLit l w && wcontingent l) := by
    rw [describe, usefulLits, List.filter_filter]
  rw [hfilter, allLits, ← List.countP_eq_length_filter, List.countP_flatMap]
  have h2 : ∀ a : Atom n, (List.countP (fun l => evalLit l w && wcontingent l) ∘
      (fun a : Atom n => [(a, true), (a, false)])) a = if isRefl a = true then 0 else 1 := by
    intro a
    cases h : isRefl a <;>
      cases hv : evalAtom a w <;>
        simp [wcontingent_eq, h, evalLit, hv]
  rw [List.map_congr_left fun a _ => h2 a, sum_map_ite_zero, contentful_atom_count]
  ring

/-- The instantiated case, no longer a compiled evaluation. -/
theorem describe_length_24 (w : World 24) : (describe w).length = 1800 := by
  rw [describe_length_formula]; norm_num

/-! ## 4. The quantified layers do not grow with the world -/

/-- **Twelve quantified sentences, whatever the world.**  Of each quantified
sentence and its denial the system says exactly one, so the count is the number
of denial pairs — independent of `n`, and of the world. -/
theorem describeQ_length_formula {n : ℕ} (w : World n) :
    (Quantified.describeQ w).length = 12 := by
  have hpair : ∀ q : Quantified.QSent,
      (List.filter (fun s => Quantified.evalQ s w) [q, Quantified.negQ q]).length = 1 := by
    intro q
    have hn := Quantified.evalQ_negQ q w
    cases hq : Quantified.evalQ q w <;> simp [List.filter, hq, hn]
  have hp1 : ∀ p : Quantified.Prop1, (List.filter (fun s => Quantified.evalQ s w)
      [(⟨true, p, true⟩ : Quantified.QSent), ⟨false, p, false⟩]).length = 1 := by
    intro p; simpa [Quantified.negQ] using hpair ⟨true, p, true⟩
  have hp2 : ∀ p : Quantified.Prop1, (List.filter (fun s => Quantified.evalQ s w)
      [(⟨true, p, false⟩ : Quantified.QSent), ⟨false, p, true⟩]).length = 1 := by
    intro p; simpa [Quantified.negQ] using hpair ⟨true, p, false⟩
  simp only [Quantified.describeQ, Quantified.allQSents, Quantified.allProp1,
    List.flatMap_cons, List.flatMap_nil, List.append_nil, Bool.not_true, Bool.not_false,
    List.filter_append, List.length_append, hp1, hp2]

/-- **And 144 sentences with a relative clause, whatever the world**, for the
same reason: `Relative.allRSents` is a list of denial pairs, and `evalR_flip`
says exactly one of each pair is true.  The 144 measured in the demonstration
world was not a fact about that world. -/
theorem describeR_length_formula {n : ℕ} (w : World n) :
    (Relative.describeR w).length = 144 := by
  have hpair : ∀ a b : Relative.Cond,
      ([(⟨true, a, b⟩ : Relative.RSent), ⟨false, a, Relative.negC b⟩].filter
        (fun r => Relative.evalR r w)).length = 1 := by
    intro a b
    have hn := Relative.evalR_flip ⟨true, a, b⟩ w
    simp only [Relative.flipR, Bool.not_true] at hn
    cases hq : Relative.evalR (⟨true, a, b⟩ : Relative.RSent) w <;>
      simp [List.filter, hq, hn]
  have hinner : ∀ (a : Relative.Cond) (M : List Relative.Cond),
      ((M.flatMap fun b => [(⟨true, a, b⟩ : Relative.RSent), ⟨false, a, Relative.negC b⟩]).filter
        (fun r => Relative.evalR r w)).length = M.length := by
    intro a M
    induction M with
    | nil => simp
    | cons b t ih =>
        rw [List.flatMap_cons, List.filter_append, List.length_append, ih, hpair a b]
        simp [Nat.add_comm]
  have houter : ∀ L : List Relative.Cond,
      ((L.flatMap fun a => Relative.litConds.flatMap fun b =>
        [(⟨true, a, b⟩ : Relative.RSent), ⟨false, a, Relative.negC b⟩]).filter
          (fun r => Relative.evalR r w)).length = 12 * L.length := by
    intro L
    induction L with
    | nil => simp
    | cons a t ih =>
        rw [List.flatMap_cons, List.filter_append, List.length_append, ih,
          hinner a Relative.litConds, Relative.litConds_length, List.length_cons]
        ring
  rw [Relative.describeR, Relative.allRSents, houter, Relative.litConds_length]

end Scaling
