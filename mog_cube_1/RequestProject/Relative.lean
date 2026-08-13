import Mathlib
import RequestProject.Quantified

/-!
# Relative clauses: *every thing that is boiling is hot*

`FINAL_REPORT.md` §8 item 5 is the other structural gap:

> **A grammar.**  Clauses are joined, not nested.  Relative clauses and
> quantifiers are the next structural step, and neither is a decoding problem.

`Quantified.lean` did the quantifiers.  This file does the nesting.  A sentence
now has a *restrictor* — a clause inside a clause:

    every thing that is boiling is hot
    some thing that is frozen is not heavy
    every thing that is hot and not heavy is warm

The restrictor and the scope are conditions on a single thing, built from the
six measured properties with `and`, `or` and `not` (`Cond`), so the grammar is
genuinely recursive rather than a longer flat sentence.

## What is proved

*The semantics is the standard one, and it behaves:*

* `evalR_univ_iff`, `evalR_ex_iff` — the two determiners are the material
  implication and the conjunction, as they must be;
* `evalR_flip` — duality: the denial of *every A is B* is *some A is not B*;
* `restricted_is_conservative` — **conservativity**, the property that separates
  natural-language determiners from arbitrary relations: *every A is B* says the
  same as *every A is A-and-B*.  Both determiners have it (`ex_conservative`);
* `univ_downward_in_restrictor`, `univ_upward_in_scope` — the monotonicity
  profile of *every*: narrowing the restrictor or widening the scope preserves
  truth.  `ex_upward_in_both` is the profile of *some*;
* `vacuous_universal` — and the classical embarrassment, with a witness: in a
  world where nothing is boiling, *every thing that is boiling is frozen* is
  true.  `existential_import_fails` states it as the failure it is.

*Which restricted universals are laws — for every world of every size:*

* `valid_iff_local` — a restricted universal holds in **all** `18^n` worlds, for
  all `n` at once, exactly when it holds of each of the 18 local states.  The
  proof is a reduction, not an enumeration of worlds.
* `law_schemas_count`, `law_schemas` — of the 144 literal-restricted universals
  exactly **12** are laws, and they are listed: *frozen ⇒ not warm*,
  *boiling ⇒ hot*, *massive ⇒ heavy*, and their companions.  This is the law
  table of `CubeThought` and `Learning`, now proved schematically for a world of
  any size rather than checked over 512 worlds.

*Speaking:*

* `describeR_sound`, `describeR_complete`, `describeR_decides` — the system says
  every true restricted sentence, no false one, and exactly one of each
  sentence/denial pair;
* `demoR_counts` — in the demonstration world of `WideWorld.lean`: 288
  sentences, **144 true** — exactly half, as duality forces — of which 28
  universal and 116 existential.

*The expressive step is real, and so is the trap:*

* `relative_clause_is_new` — two worlds of two things that agree on **all 24**
  unrestricted quantified sentences of `Quantified.lean` and disagree on *every
  hot thing is heavy*.  A relative clause is not an abbreviation of anything the
  previous grammar could say.
* `accidental_generalisations` — **the honest one.**  Of the 28 restricted
  universals true in the demonstration world, 24 hold in every world (12 laws
  and the 12 trivial *every A is A*) and **four do not**: among them *every
  thing that is boiling is heavy*, an accident of that world's pairing of
  temperatures with masses (`boiling_heavy_is_an_accident`).  A generaliser that
  reads one world and states what it finds gets four of its sixteen substantive
  generalisations wrong.
-/

namespace Relative

open WideWorld Quantified

/-! ## 1. Conditions: the clause inside the clause -/

/-- A condition on a single thing: a measured property, asserted or denied, and
closed under `and`, `or`, `not`.  This is the recursion the old grammar lacked. -/
inductive Cond
  | lit (p : Prop1) (b : Bool)
  | and (c d : Cond)
  | or (c d : Cond)
  | not (c : Cond)
deriving DecidableEq, Repr

/-- A measured property, read off one thing's local state. -/
def propLS : Prop1 → LS → Bool
  | .frozen, s => decide (tempVal s.1 ≤ 0)
  | .warm, s => decide (0 < tempVal s.1 ∧ tempVal s.1 < 100)
  | .hot, s => decide (60 ≤ tempVal s.1)
  | .boiling, s => decide (100 ≤ tempVal s.1)
  | .heavy, s => decide (10 ≤ massVal s.2)
  | .massive, s => decide (100 ≤ massVal s.2)

/-- The lexicon's words really are functions of the local state alone. -/
theorem propLS_eq {n} (p : Prop1) (w : World n) (e : Fin n) :
    evalAtom (atomOf p e) w = propLS p (w e) := by
  cases p <;> rfl

/-- The truth of a condition at a local state. -/
def evalCLS : Cond → LS → Bool
  | .lit p b, s => decide (propLS p s = b)
  | .and c d, s => evalCLS c s && evalCLS d s
  | .or c d, s => evalCLS c s || evalCLS d s
  | .not c, s => !evalCLS c s

/-- The truth of a condition of a thing in a world. -/
def evalC {n} (c : Cond) (w : World n) (e : Fin n) : Bool := evalCLS c (w e)

/-- A literal condition is the literal of the old lexicon: the new grammar
extends the old one rather than replacing it. -/
theorem evalC_lit {n} (p : Prop1) (b : Bool) (w : World n) (e : Fin n) :
    evalC (.lit p b) w e = evalLit (litOf p b e) w := by
  simp [evalC, evalCLS, evalLit, litOf, propLS_eq]

/-! ## 2. Restricted quantification -/

/-- *Every / some thing that is `restr` is `scope`.* -/
structure RSent where
  /-- `true` for *every*, `false` for *some*. -/
  univ : Bool
  /-- The relative clause. -/
  restr : Cond
  /-- What is predicated of the things it picks out. -/
  scope : Cond
deriving DecidableEq, Repr

/-- Its truth in a world. -/
def evalR {n} (r : RSent) (w : World n) : Bool :=
  if r.univ then (List.finRange n).all fun e => !evalC r.restr w e || evalC r.scope w e
  else (List.finRange n).any fun e => evalC r.restr w e && evalC r.scope w e

theorem evalR_univ_iff {n} (a b : Cond) (w : World n) :
    evalR ⟨true, a, b⟩ w = true ↔ ∀ e, evalC a w e = true → evalC b w e = true := by
  have hdef : evalR ⟨true, a, b⟩ w
      = (List.finRange n).all fun e => !evalC a w e || evalC b w e := rfl
  rw [hdef, List.all_eq_true]
  constructor
  · intro h e he
    have h' := h e (List.mem_finRange e)
    simpa [he] using h'
  · intro h e _
    cases hc : evalC a w e
    · simp
    · simp [h e hc]

theorem evalR_ex_iff {n} (a b : Cond) (w : World n) :
    evalR ⟨false, a, b⟩ w = true ↔ ∃ e, evalC a w e = true ∧ evalC b w e = true := by
  have hdef : evalR ⟨false, a, b⟩ w
      = (List.finRange n).any fun e => evalC a w e && evalC b w e := rfl
  rw [hdef, List.any_eq_true]
  constructor
  · rintro ⟨e, _, he⟩
    exact ⟨e, by simpa using he⟩
  · rintro ⟨e, he1, he2⟩
    exact ⟨e, List.mem_finRange e, by simp [he1, he2]⟩

/-- The denial of a condition: for a literal it is the literal denied, so that
the language stays inside its own lexicon. -/
def negC : Cond → Cond
  | .lit q b => .lit q !b
  | c => .not c

theorem evalCLS_negC (c : Cond) (s : LS) : evalCLS (negC c) s = !evalCLS c s := by
  cases c with
  | lit q b => cases b <;> cases h : propLS q s <;> simp [negC, evalCLS, h]
  | and c d => rfl
  | or c d => rfl
  | not c => rfl

theorem evalC_negC {n} (c : Cond) (w : World n) (e : Fin n) :
    evalC (negC c) w e = !evalC c w e := evalCLS_negC c (w e)

/-- The denial of a restricted sentence. -/
def flipR (r : RSent) : RSent := ⟨!r.univ, r.restr, negC r.scope⟩

private theorem bool_eq_not_of_iff' : ∀ x y : Bool, (x = true ↔ ¬(y = true)) → x = !y := by decide

/-- **Duality**: the denial of *every A is B* is *some A is not B*, and back. -/
theorem evalR_flip {n} (r : RSent) (w : World n) : evalR (flipR r) w = !evalR r w := by
  obtain ⟨u, a, s⟩ := r
  refine bool_eq_not_of_iff' _ _ ?_
  cases u
  · rw [show flipR ⟨false, a, s⟩ = ⟨true, a, negC s⟩ from rfl, evalR_univ_iff, evalR_ex_iff]
    simp [evalC_negC, not_exists, not_and, Bool.not_eq_true]
  · rw [show flipR ⟨true, a, s⟩ = ⟨false, a, negC s⟩ from rfl, evalR_univ_iff, evalR_ex_iff]
    simp [evalC_negC, not_forall, Bool.not_eq_true]

/-- **Conservativity.**  *Every A is B* and *every A is A-and-B* say the same
thing.  Every determiner of a natural language has this property and almost no
arbitrary relation between sets does; it is the sharpest available check that
the semantics above is a determiner and not a coincidence. -/
theorem restricted_is_conservative {n} (a b : Cond) (w : World n) :
    evalR ⟨true, a, b⟩ w = evalR ⟨true, a, .and a b⟩ w := by
  have hfun : (fun e => !evalC a w e || evalC b w e)
      = (fun e => !evalC a w e || evalC (.and a b) w e) := by
    funext e
    simp only [evalC, evalCLS]
    cases evalCLS a (w e) <;> cases evalCLS b (w e) <;> rfl
  have h1 : evalR ⟨true, a, b⟩ w
      = (List.finRange n).all fun e => !evalC a w e || evalC b w e := rfl
  have h2 : evalR ⟨true, a, .and a b⟩ w
      = (List.finRange n).all fun e => !evalC a w e || evalC (.and a b) w e := rfl
  rw [h1, h2, hfun]

/-- The same for *some*. -/
theorem ex_conservative {n} (a b : Cond) (w : World n) :
    evalR ⟨false, a, b⟩ w = evalR ⟨false, a, .and a b⟩ w := by
  have hfun : (fun e => evalC a w e && evalC b w e)
      = (fun e => evalC a w e && evalC (.and a b) w e) := by
    funext e
    simp only [evalC, evalCLS]
    cases evalCLS a (w e) <;> cases evalCLS b (w e) <;> rfl
  have h1 : evalR ⟨false, a, b⟩ w
      = (List.finRange n).any fun e => evalC a w e && evalC b w e := rfl
  have h2 : evalR ⟨false, a, .and a b⟩ w
      = (List.finRange n).any fun e => evalC a w e && evalC (.and a b) w e := rfl
  rw [h1, h2, hfun]

/-- *Every* is downward monotone in its restrictor: narrowing the relative
clause preserves truth. -/
theorem univ_downward_in_restrictor {n} {a a' b : Cond} {w : World n}
    (hsub : ∀ e, evalC a' w e = true → evalC a w e = true)
    (h : evalR ⟨true, a, b⟩ w = true) : evalR ⟨true, a', b⟩ w = true :=
  (evalR_univ_iff a' b w).mpr fun e he => (evalR_univ_iff a b w).mp h e (hsub e he)

/-- …and upward monotone in its scope. -/
theorem univ_upward_in_scope {n} {a b b' : Cond} {w : World n}
    (hsup : ∀ e, evalC b w e = true → evalC b' w e = true)
    (h : evalR ⟨true, a, b⟩ w = true) : evalR ⟨true, a, b'⟩ w = true :=
  (evalR_univ_iff a b' w).mpr fun e he => hsup e ((evalR_univ_iff a b w).mp h e he)

/-- *Some* is upward monotone in both arguments. -/
theorem ex_upward_in_both {n} {a a' b b' : Cond} {w : World n}
    (ha : ∀ e, evalC a w e = true → evalC a' w e = true)
    (hb : ∀ e, evalC b w e = true → evalC b' w e = true)
    (h : evalR ⟨false, a, b⟩ w = true) : evalR ⟨false, a', b'⟩ w = true := by
  obtain ⟨e, he1, he2⟩ := (evalR_ex_iff a b w).mp h
  exact (evalR_ex_iff a' b' w).mpr ⟨e, ha e he1, hb e he2⟩

/-- A world of two cold, light things. -/
def coldWorld : World 2 := fun _ => (0, 0)

/-- **The vacuous universal, with a witness.**  Nothing in `coldWorld` boils, so
*every thing that is boiling is frozen* comes out true — and so would *every
thing that is boiling is not frozen*.  The system says both. -/
theorem vacuous_universal :
    evalR ⟨true, .lit .boiling true, .lit .frozen true⟩ coldWorld = true ∧
    evalR ⟨true, .lit .boiling true, .lit .frozen false⟩ coldWorld = true := by
  refine ⟨by decide, by decide⟩

/-- Stated as the failure it is: a true universal need not have a single
instance.  Existential import is not part of this semantics — as in classical
logic, and unlike ordinary English. -/
theorem existential_import_fails :
    evalR ⟨true, .lit .boiling true, .lit .frozen true⟩ coldWorld = true ∧
    evalR ⟨false, .lit .boiling true, .lit .frozen true⟩ coldWorld = false := by
  refine ⟨by decide, by decide⟩

/-! ## 3. Which restricted universals are laws, for every world of every size -/

/-- A restricted universal is *valid* when it holds at every local state. -/
def validR (a b : Cond) : Bool := allLS.all fun s => !evalCLS a s || evalCLS b s

/-- **The reduction that replaces enumeration.**  A restricted universal is true
in every one of the `18 ^ n` worlds, for every `n` at once, exactly when it is
true of each of the eighteen local states.  Deciding a law of the wide world
therefore costs 18 evaluations, whatever `n` is. -/
theorem valid_iff_local (a b : Cond) :
    validR a b = true ↔ ∀ (n : ℕ) (w : World n), evalR ⟨true, a, b⟩ w = true := by
  constructor
  · intro h n w
    refine (evalR_univ_iff a b w).mpr fun e he => ?_
    have := List.all_eq_true.mp h (w e) (mem_allLS (w e))
    simp only [evalC] at he ⊢
    simpa [he] using this
  · intro h
    refine List.all_eq_true.mpr fun s _ => ?_
    have hw : evalR ⟨true, a, b⟩ (fun _ => s : World 1) = true := h 1 _
    have := (evalR_univ_iff a b (fun _ => s : World 1)).mp hw ⟨0, Nat.one_pos⟩
    simp only [evalC] at this
    by_cases hs : evalCLS a s = true
    · simp [hs, this hs]
    · have hfalse : evalCLS a s = false := by simpa using hs
      simp [hfalse]

/-- The twelve literal conditions: each property, asserted and denied. -/
def litConds : List Cond := allProp1.flatMap fun p => [Cond.lit p true, Cond.lit p false]

theorem litConds_length : litConds.length = 12 := by decide

/-- The literal-restricted sentences: both determiners, both clauses a literal.
288 sentences, closed under denial. -/
def allRSents : List RSent :=
  litConds.flatMap fun a => litConds.flatMap fun b => [⟨true, a, b⟩, ⟨false, a, negC b⟩]

theorem allRSents_length : allRSents.length = 288 := by native_decide

/-- The laws among them. -/
def lawSchemas : List (Cond × Cond) :=
  litConds.flatMap fun a =>
    (litConds.filter fun b => decide (a ≠ b) && validR a b).map fun b => (a, b)

/-- **Twelve law schemas, and no more.**  Of the 144 literal-restricted
universals exactly twelve hold in every world of every size. -/
theorem law_schemas_count : lawSchemas.length = 12 := by native_decide

/-- And they are exactly these: the temperature ladder, the mass ladder, and
their contrapositives. -/
theorem law_schemas :
    lawSchemas.map (fun p => (p.1, p.2)) =
      [(.lit .frozen true, .lit .warm false), (.lit .frozen true, .lit .hot false),
       (.lit .frozen true, .lit .boiling false), (.lit .warm true, .lit .frozen false),
       (.lit .warm true, .lit .boiling false), (.lit .hot true, .lit .frozen false),
       (.lit .hot false, .lit .boiling false), (.lit .boiling true, .lit .frozen false),
       (.lit .boiling true, .lit .warm false), (.lit .boiling true, .lit .hot true),
       (.lit .heavy false, .lit .massive false), (.lit .massive true, .lit .heavy true)] := by
  native_decide

/-- Every one of them really is a law of every world, of every size — the
schematic form of `CubeThought.laws_are_sound_on_the_surface`, proved without
enumerating worlds. -/
theorem law_schemas_sound :
    ∀ p ∈ lawSchemas, ∀ (n : ℕ) (w : World n), evalR ⟨true, p.1, p.2⟩ w = true := by
  intro p hp
  refine (valid_iff_local p.1 p.2).mp ?_
  have h : lawSchemas.all (fun p => validR p.1 p.2) = true := by native_decide
  exact List.all_eq_true.mp h p hp

/-! ## 4. Speaking the language with relative clauses -/

/-- Everything with a relative clause that is true in a world. -/
def describeR {n} (w : World n) : List RSent := allRSents.filter fun r => evalR r w

theorem describeR_sound {n} {w : World n} {r : RSent} (h : r ∈ describeR w) :
    evalR r w = true := by simpa using (List.mem_filter.mp h).2

theorem describeR_complete {n} {w : World n} {r : RSent}
    (hmem : r ∈ allRSents) (h : evalR r w = true) : r ∈ describeR w :=
  List.mem_filter.mpr ⟨hmem, by simpa using h⟩

/-- The denial of a listed sentence is listed. -/
theorem flipR_mem : ∀ r ∈ allRSents, flipR r ∈ allRSents := by native_decide

/-- **No gaps and no contradictions**: of each sentence and its denial the
system says exactly one. -/
theorem describeR_decides {n} (w : World n) {r : RSent} (hmem : r ∈ allRSents) :
    (r ∈ describeR w ∧ flipR r ∉ describeR w) ∨ (r ∉ describeR w ∧ flipR r ∈ describeR w) := by
  have hneg := evalR_flip r w
  by_cases h : evalR r w = true
  · refine Or.inl ⟨describeR_complete hmem h, fun hc => ?_⟩
    have := describeR_sound hc
    rw [hneg, h] at this
    exact Bool.noConfusion this
  · have hf : evalR r w = false := by simpa using h
    refine Or.inr ⟨fun hc => h (describeR_sound hc), describeR_complete (flipR_mem r hmem) ?_⟩
    rw [hneg, hf]; rfl

/-- **Measured in the demonstration world** of `WideWorld.lean`: of the 288
sentences 144 are true — exactly half, as `evalR_flip` forces — of which 28 are
universal and 116 existential. -/
theorem demoR_counts :
    (describeR demoWide).length = 144 ∧
    ((describeR demoWide).filter (fun r => r.univ)).length = 28 ∧
    ((describeR demoWide).filter (fun r => !r.univ)).length = 116 := by
  refine ⟨by native_decide, by native_decide, by native_decide⟩

/-! ## 5. A relative clause says something new -/

/-- Two things: a hot heavy one and a cold light one. -/
def wA : World 2 := ![(3, 1), (0, 0)]

/-- The same two temperatures and the same two masses, paired the other way. -/
def wB : World 2 := ![(3, 0), (0, 1)]

/-- **Nesting is new expressive power.**  `wA` and `wB` agree on every one of
the 24 unrestricted quantified sentences of `Quantified.lean` — they have the
same temperatures and the same masses, only differently paired — and they
disagree on *every hot thing is heavy*.  So no unrestricted sentence, and no
Boolean combination of them, has the truth value of a relative clause. -/
theorem relative_clause_is_new :
    (∀ q ∈ allQSents, evalQ q wA = evalQ q wB) ∧
    evalR ⟨true, .lit .hot true, .lit .heavy true⟩ wA = true ∧
    evalR ⟨true, .lit .hot true, .lit .heavy true⟩ wB = false := by
  refine ⟨by native_decide, by native_decide, by native_decide⟩

/-! ## 6. The trap: accidental generalisation -/

/-- **The honest measurement.**  Twenty-eight restricted universals are true in
the demonstration world.  Twenty-four of them hold in every world — the twelve
law schemas and the twelve trivial *every A is A* — and four do not: *every
frozen thing is not massive*, *every boiling thing is heavy*, *every thing that
is not heavy is not boiling*, *every massive thing is not frozen*.  They are
accidents of that world's pairing of temperatures with masses. -/
theorem accidental_generalisations :
    ((describeR demoWide).filter (fun r => r.univ)).length = 28 ∧
    ((describeR demoWide).filter (fun r => r.univ && validR r.restr r.scope)).length = 24 ∧
    ((describeR demoWide).filter (fun r => r.univ && !validR r.restr r.scope)).length = 4 := by
  refine ⟨by native_decide, by native_decide, by native_decide⟩

/-- One of the four, exhibited: true where it was read, false one world along. -/
theorem boiling_heavy_is_an_accident :
    evalR ⟨true, .lit .boiling true, .lit .heavy true⟩ demoWide = true ∧
    evalR ⟨true, .lit .boiling true, .lit .heavy true⟩ (fun _ => ((4 : Fin 6), (0 : Fin 3)) :
      World 1) = false := by
  refine ⟨by native_decide, by decide⟩

/-! ## 7. Saying it in English -/

/-- The English for a condition — recursive, like the condition. -/
def condStr : Cond → String
  | .lit p b => (if b then "" else "not ") ++ propWord p
  | .and c d => condStr c ++ " and " ++ condStr d
  | .or c d => condStr c ++ " or " ++ condStr d
  | .not c => "not (" ++ condStr c ++ ")"

/-- The English for a restricted sentence. -/
def renderR (r : RSent) : String :=
  (if r.univ then "every thing that is " else "some thing that is ") ++
    condStr r.restr ++ " is " ++ condStr r.scope

/-- The twelve law schemas, in English. -/
def lawSentences : List String := lawSchemas.map fun p => renderR ⟨true, p.1, p.2⟩

/-- **The pinned transcript**: what the system knows to be true of any world
whatsoever, said in English. -/
theorem lawSentences_pinned :
    lawSentences =
      ["every thing that is frozen is not warm", "every thing that is frozen is not hot",
       "every thing that is frozen is not boiling", "every thing that is warm is not frozen",
       "every thing that is warm is not boiling", "every thing that is hot is not frozen",
       "every thing that is not hot is not boiling", "every thing that is boiling is not frozen",
       "every thing that is boiling is not warm", "every thing that is boiling is hot",
       "every thing that is not heavy is not massive",
       "every thing that is massive is heavy"] := by
  native_decide

/-- A sentence with a compound relative clause, to show the recursion is real:
*every thing that is hot and not heavy is warm*.  It is true in the
demonstration world — where the only hot light thing reads 60 °C — but it is not
a law: one world along, a thing at 500 °C weighing a kilogram refutes it. -/
theorem compound_relative_clause :
    renderR ⟨true, .and (.lit .hot true) (.lit .heavy false), .lit .warm true⟩ =
      "every thing that is hot and not heavy is warm" ∧
    evalR ⟨true, .and (.lit .hot true) (.lit .heavy false), .lit .warm true⟩ demoWide = true ∧
    evalR ⟨true, .and (.lit .hot true) (.lit .heavy false), .lit .warm true⟩
      (fun _ => ((5 : Fin 6), (0 : Fin 3)) : World 1) = false := by
  refine ⟨by native_decide, by native_decide, by decide⟩

end Relative
