import RequestProject.WideWorld

/-!
# Saying *every* and *some*

Everything the system has said so far names its subject: "the water is frozen",
"the stone is heavier than the lamp".  `FINAL_REPORT.md` §8 lists grammar as the
next structural step, and this file takes the first part of it — quantification
over the things of the world:

    every thing is hot          some thing is not heavy

A quantified sentence is not a longer sentence, it is a *different kind* of
sentence, and the point of the file is that the difference is real and priced:

* it is sound and complete against the world (`evalQ_univ`, `evalQ_ex`), and it
  behaves as quantification must: `evalQ_negQ` is the duality
  `¬∀ = ∃¬`, `universal_instantiates` and `universal_generalises` are the two
  halves of instantiation, and `witness` produces the thing an existential
  claims to exist (`witness_sound`, `witness_isSome_iff`);
* the system can *speak* it: `describeQ` says every quantified sentence true in
  a world, `describeQ_sound` proves each one true, and `describeQ_decides`
  proves it says exactly one of each sentence/denial pair — no gaps, no
  contradictions;
* and it is **not expressible in the old language**: for a world of three
  things or more, no single literal of `WideWorld` has the truth value of
  "every thing is hot" (`universal_not_a_literal`, `existential_not_a_literal`).
  Quantification is not sugar over the lexicon; it says something the 3744
  literals cannot.

Everything is proved for an arbitrary number of things `n`, with no enumeration
of worlds — the same discipline as `WideWorld.lean`.  Only the rendering and the
demonstration transcript are fixed at `n = 24`.
-/

namespace Quantified

open WideWorld

/-! ## 1. Quantified sentences -/

/-- The six measured properties of a single thing. -/
inductive Prop1
  | frozen | warm | hot | boiling | heavy | massive
deriving DecidableEq, Repr

/-- All six of them. -/
def allProp1 : List Prop1 := [.frozen, .warm, .hot, .boiling, .heavy, .massive]

theorem mem_allProp1 (p : Prop1) : p ∈ allProp1 := by cases p <;> simp [allProp1]

/-- The word for a property of a given thing. -/
def atomOf {n} : Prop1 → Fin n → Atom n
  | .frozen, e => .frozen e
  | .warm, e => .warm e
  | .hot, e => .hot e
  | .boiling, e => .boiling e
  | .heavy, e => .heavy e
  | .massive, e => .massive e

/-- The literal "`e` is (or is not) `p`". -/
def litOf {n} (p : Prop1) (b : Bool) (e : Fin n) : Lit n := (atomOf p e, b)

/-- A quantified sentence: *every* (or *some*) thing *is* (or *is not*) `p`. -/
structure QSent where
  /-- `true` for "every", `false` for "some". -/
  univ : Bool
  /-- The property quantified over. -/
  prop : Prop1
  /-- `true` for "is", `false` for "is not". -/
  pos : Bool
deriving DecidableEq, Repr

/-- Its truth in a world. -/
def evalQ {n} (q : QSent) (w : World n) : Bool :=
  if q.univ then (List.finRange n).all fun e => evalLit (litOf q.prop q.pos e) w
  else (List.finRange n).any fun e => evalLit (litOf q.prop q.pos e) w

theorem evalQ_univ {n} (p : Prop1) (b : Bool) (w : World n) :
    evalQ ⟨true, p, b⟩ w = true ↔ ∀ e, evalLit (litOf p b e) w = true := by
  simp [evalQ, List.all_eq_true]

theorem evalQ_ex {n} (p : Prop1) (b : Bool) (w : World n) :
    evalQ ⟨false, p, b⟩ w = true ↔ ∃ e, evalLit (litOf p b e) w = true := by
  simp [evalQ, List.any_eq_true]

/-! ## 2. It behaves as quantification must -/

/-- The denial of a quantified sentence: *every … is* becomes *some … is not*. -/
def negQ (q : QSent) : QSent := ⟨!q.univ, q.prop, !q.pos⟩

@[simp] theorem negQ_negQ (q : QSent) : negQ (negQ q) = q := by
  simp [negQ]

private theorem bool_eq_not_of_iff : ∀ x y : Bool, (x = true ↔ ¬(y = true)) → x = !y := by decide

/-- Denying the copula denies the literal. -/
theorem evalLit_litOf_not {n} (p : Prop1) (b : Bool) (e : Fin n) (w : World n) :
    evalLit (litOf p (!b) e) w = !evalLit (litOf p b e) w := by
  have h : litOf p (!b) e = negL (litOf p b e) := rfl
  rw [h, evalLit_negL]

/-- **Duality**: the denial of a quantified sentence is true exactly when the
sentence is false — `¬∀ = ∃¬` and `¬∃ = ∀¬`. -/
theorem evalQ_negQ {n} (q : QSent) (w : World n) : evalQ (negQ q) w = !evalQ q w := by
  obtain ⟨u, p, b⟩ := q
  refine bool_eq_not_of_iff _ _ ?_
  cases u
  · rw [show negQ ⟨false, p, b⟩ = ⟨true, p, !b⟩ from rfl, evalQ_univ, evalQ_ex]
    simp only [evalLit_litOf_not, Bool.not_eq_true', Bool.not_eq_true, not_exists]
  · rw [show negQ ⟨true, p, b⟩ = ⟨false, p, !b⟩ from rfl, evalQ_univ, evalQ_ex]
    simp only [evalLit_litOf_not, Bool.not_eq_true', Bool.not_eq_true, not_forall]

/-- **Instantiation.**  A universal sentence licenses every one of its
instances — the system may say "the water is hot" on the strength of "every
thing is hot", and be right. -/
theorem universal_instantiates {n} {p : Prop1} {b : Bool} {w : World n}
    (h : evalQ ⟨true, p, b⟩ w = true) (e : Fin n) : evalLit (litOf p b e) w = true :=
  (evalQ_univ p b w).mp h e

/-- **Generalisation.**  Conversely, if every instance holds the system may say
so in one sentence. -/
theorem universal_generalises {n} {p : Prop1} {b : Bool} {w : World n}
    (h : ∀ e, evalLit (litOf p b e) w = true) : evalQ ⟨true, p, b⟩ w = true :=
  (evalQ_univ p b w).mpr h

/-- The thing an existential sentence is about: the first one that fits. -/
def witness {n} (p : Prop1) (b : Bool) (w : World n) : Option (Fin n) :=
  (List.finRange n).find? fun e => evalLit (litOf p b e) w

/-- **The witness really is one**: whatever `witness` names has the property
claimed. -/
theorem witness_sound {n} {p : Prop1} {b : Bool} {w : World n} {e : Fin n}
    (h : witness p b w = some e) : evalLit (litOf p b e) w = true := by
  have := List.find?_some (p := fun e => evalLit (litOf p b e) w) (l := List.finRange n) h
  simpa using this

/-- **And there is a witness exactly when the existential sentence is true.** -/
theorem witness_isSome_iff {n} (p : Prop1) (b : Bool) (w : World n) :
    (witness p b w).isSome = true ↔ evalQ ⟨false, p, b⟩ w = true := by
  rw [evalQ_ex]
  constructor
  · intro h
    obtain ⟨e, he⟩ := Option.isSome_iff_exists.mp h
    exact ⟨e, witness_sound he⟩
  · rintro ⟨e, he⟩
    rw [Option.isSome_iff_exists]
    rcases hw : witness p b w with _ | e'
    · exact absurd (List.find?_eq_none.mp hw e (List.mem_finRange e)) (by simp [he])
    · exact ⟨e', rfl⟩

/-- **In a world with something in it, *every* implies *some*.**  (With nothing
in it, "every thing is hot" is vacuously true and "some thing is hot" false, as
it should be.) -/
theorem univ_implies_ex {n} (hn : 0 < n) {p : Prop1} {b : Bool} {w : World n}
    (h : evalQ ⟨true, p, b⟩ w = true) : evalQ ⟨false, p, b⟩ w = true :=
  (evalQ_ex p b w).mpr ⟨⟨0, hn⟩, universal_instantiates h _⟩

/-! ## 3. Speaking the quantified language -/

/-- The whole quantified lexicon: twenty-four sentences, in denial pairs. -/
def allQSents : List QSent :=
  allProp1.flatMap fun p =>
    [true, false].flatMap fun b => [⟨true, p, b⟩, ⟨false, p, !b⟩]

theorem allQSents_length : allQSents.length = 24 := by decide

theorem mem_allQSents (q : QSent) : q ∈ allQSents := by
  obtain ⟨u, p, b⟩ := q
  have hp := mem_allProp1 p
  simp only [allQSents, List.mem_flatMap]
  refine ⟨p, hp, ?_⟩
  cases u <;> cases b <;> simp

theorem negQ_mem_allQSents (q : QSent) : negQ q ∈ allQSents := mem_allQSents _

/-- Everything quantified that is true in a world. -/
def describeQ {n} (w : World n) : List QSent := allQSents.filter fun q => evalQ q w

/-- **Soundness**: every quantified sentence the system utters is true. -/
theorem describeQ_sound {n} {w : World n} {q : QSent} (h : q ∈ describeQ w) :
    evalQ q w = true := by
  simpa using (List.mem_filter.mp h).2

/-- **Completeness**: it utters every quantified sentence that is true. -/
theorem describeQ_complete {n} {w : World n} {q : QSent} (h : evalQ q w = true) :
    q ∈ describeQ w :=
  List.mem_filter.mpr ⟨mem_allQSents q, by simpa using h⟩

/-- **It decides.**  For every sentence, the system says either it or its denial,
and never both: the quantified language has no gaps and no contradictions. -/
theorem describeQ_decides {n} (w : World n) (q : QSent) :
    (q ∈ describeQ w ∧ negQ q ∉ describeQ w) ∨ (q ∉ describeQ w ∧ negQ q ∈ describeQ w) := by
  have hneg := evalQ_negQ q w
  by_cases h : evalQ q w = true
  · refine Or.inl ⟨describeQ_complete h, fun hc => ?_⟩
    have := describeQ_sound hc
    rw [hneg, h] at this
    exact Bool.noConfusion this
  · have hf : evalQ q w = false := by simpa using h
    refine Or.inr ⟨fun hc => h (describeQ_sound hc), describeQ_complete ?_⟩
    rw [hneg, hf]
    rfl

/-! ## 4. Quantification is not in the lexicon -/

/-- A local state that has the property, and one that has not. -/
def satLS : Prop1 → LS
  | .frozen => (0, 0)
  | .warm => (2, 0)
  | .hot => (3, 0)
  | .boiling => (4, 0)
  | .heavy => (0, 1)
  | .massive => (0, 2)

def unsatLS : Prop1 → LS
  | .frozen => (5, 0)
  | .warm => (0, 0)
  | .hot => (0, 0)
  | .boiling => (0, 0)
  | .heavy => (0, 0)
  | .massive => (0, 0)

theorem evalAtom_satLS {n} (p : Prop1) (w : World n) (e : Fin n) (h : w e = satLS p) :
    evalAtom (atomOf p e) w = true := by
  cases p <;> simp [atomOf, evalAtom, tp, ms, h, satLS, tempVal, massVal]

theorem evalAtom_unsatLS {n} (p : Prop1) (w : World n) (e : Fin n) (h : w e = unsatLS p) :
    evalAtom (atomOf p e) w = false := by
  cases p <;> simp [atomOf, evalAtom, tp, ms, h, unsatLS, tempVal, massVal]

/-- With three things or more there is always one a given word does not
mention. -/
theorem exists_unmentioned {n} (h3 : 3 ≤ n) (a : Atom n) : ∃ e : Fin n, e ∉ atomEnts a := by
  by_contra hc
  push_neg at hc
  have hsub : (Finset.univ : Finset (Fin n)) ⊆ (atomEnts a).toFinset := by
    intro e _
    exact List.mem_toFinset.mpr (hc e)
  have h1 : (Finset.univ : Finset (Fin n)).card ≤ (atomEnts a).toFinset.card :=
    Finset.card_le_card hsub
  have h2 : (atomEnts a).toFinset.card ≤ (atomEnts a).length := List.toFinset_card_le _
  have h3' := atomEnts_length_le a
  simp only [Finset.card_univ, Fintype.card_fin] at h1
  omega

/-- **"Every thing is `p`" is not any word of the lexicon.**  For a world of
three things or more, and for each of the 3744 literals, there are two worlds
the literal cannot tell apart but the universal sentence can.  Quantification is
new expressive power, not an abbreviation. -/
theorem universal_not_a_literal {n} (h3 : 3 ≤ n) (p : Prop1) (l : Lit n) :
    ∃ w w' : World n, evalLit l w = evalLit l w' ∧
      evalQ ⟨true, p, true⟩ w ≠ evalQ ⟨true, p, true⟩ w' := by
  obtain ⟨e, he⟩ := exists_unmentioned h3 l.1
  refine ⟨(fun _ => satLS p : World n),
    (fun x => if x = e then unsatLS p else satLS p : World n), ?_, ?_⟩
  · have hcongr : evalAtom l.1 (fun _ => satLS p)
        = evalAtom l.1 (fun x => if x = e then unsatLS p else satLS p) := by
      refine evalAtom_congr _ _ _ fun f hf => ?_
      have : f ≠ e := fun hfe => he (hfe ▸ hf)
      simp [this]
    simp [evalLit, hcongr]
  · have hw : evalQ ⟨true, p, true⟩ (fun _ => satLS p : World n) = true := by
      refine (evalQ_univ p true _).mpr fun f => ?_
      have hf : evalAtom (atomOf p f) (fun _ => satLS p : World n) = true :=
        evalAtom_satLS p _ f rfl
      simp [evalLit, litOf, hf]
    have hw' : evalQ ⟨true, p, true⟩
        (fun x => if x = e then unsatLS p else satLS p : World n) = false := by
      by_contra hc
      have hct : evalQ ⟨true, p, true⟩
          (fun x => if x = e then unsatLS p else satLS p : World n) = true := by simpa using hc
      have h1 := universal_instantiates hct e
      have h2 : evalAtom (atomOf p e)
          (fun x => if x = e then unsatLS p else satLS p : World n) = false :=
        evalAtom_unsatLS p _ e (by simp)
      simp [litOf, evalLit, h2] at h1
    rw [hw, hw']
    simp

/-- The same for "some thing is `p`", by duality. -/
theorem existential_not_a_literal {n} (h3 : 3 ≤ n) (p : Prop1) (l : Lit n) :
    ∃ w w' : World n, evalLit l w = evalLit l w' ∧
      evalQ ⟨false, p, false⟩ w ≠ evalQ ⟨false, p, false⟩ w' := by
  obtain ⟨w, w', hl, hq⟩ := universal_not_a_literal h3 p l
  refine ⟨w, w', hl, ?_⟩
  have h1 : evalQ ⟨false, p, false⟩ w = !evalQ ⟨true, p, true⟩ w := evalQ_negQ ⟨true, p, true⟩ w
  have h2 : evalQ ⟨false, p, false⟩ w' = !evalQ ⟨true, p, true⟩ w' := evalQ_negQ ⟨true, p, true⟩ w'
  rw [h1, h2]
  simpa using hq

/-! ## 5. Saying it in English -/

/-- The English for a property. -/
def propWord : Prop1 → String
  | .frozen => "frozen"
  | .warm => "warm"
  | .hot => "hot"
  | .boiling => "boiling"
  | .heavy => "heavy"
  | .massive => "massive"

/-- The English for a quantified sentence. -/
def renderQ (q : QSent) : String :=
  (if q.univ then "everything is " else "something is ") ++
    (if q.pos then "" else "not ") ++ propWord q.prop

/-- What the demonstration world of `WideWorld.lean` affords, quantified. -/
def demoQ : List String := (describeQ demoWide).map renderQ

/-- **The quantified transcript, pinned.**  Twelve sentences — exactly one of
each denial pair, as `describeQ_decides` requires.  Every one of them is
existential: the demonstration world of `WideWorld.lean` runs its twenty-four
things through all six temperatures and all three masses, so for each property
both "something is …" and "something is not …" hold, and no universal sentence
is true of it. -/
theorem demoQ_transcript :
    demoQ =
      ["something is not frozen", "something is frozen",
       "something is not warm", "something is warm",
       "something is not hot", "something is hot",
       "something is not boiling", "something is boiling",
       "something is not heavy", "something is heavy",
       "something is not massive", "something is massive"] := by
  native_decide

/-- No universal sentence survives that world. -/
theorem demoQ_no_universal (q : QSent) (h : q ∈ describeQ demoWide) : q.univ = false := by
  revert h
  revert q
  native_decide

/-- …and the count is twelve, as it must be. -/
theorem demoQ_length : (describeQ demoWide).length = 12 := by native_decide

end Quantified
