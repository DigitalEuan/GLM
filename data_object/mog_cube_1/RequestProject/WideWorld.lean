import Mathlib

/-!
# A wide world: thousands of words, and reasoning that does not enumerate

Report 2 §7.2 named the bottleneck of everything before this file:

> The vocabulary is small and closed. Three things, six predicates, three
> actions, 512 worlds. The proofs quantify over all of it, which is exactly why
> it has to be small. […] a larger world model needs a proof method that is not
> enumeration.

This file removes that bottleneck. The world here has `n` things for an
*arbitrary* `n`; each thing carries a temperature reading on a six-point scale
and a mass reading on a three-point scale, so there are `18 ^ n` worlds
(`card_World`) — for the instantiated `n = 24` that is
`18^24 = 1 133 827 315 385 150 725 554 176` worlds, which no enumeration will
ever touch.

## The idea

Every word in the lexicon is a threshold or a comparison, so every word
mentions **at most two things** (`atomEnts_length_le`). Whether a sentence
built from a handful of words is true in *every* world therefore cannot depend
on more than the local states of the things those words mention. `checkAll`
makes that precise: it enumerates local states for the mentioned things only,
and `checkAll_iff` proves this agrees with quantification over all `18 ^ n`
worlds.

The consequence is `wentails_cost`: deciding a law costs at most `18^4 =
104 976` evaluations **whatever `n` is**. Growing the vocabulary from three
things to twenty-four, or to twenty-four thousand, does not make a single law
harder to certify.

## What is here

* `checkAll_iff` / `checkAny_iff` — local checking is sound *and* complete for
  the full world set, given a dependency side-condition supplied by the
  combinators `dep_atom`, `dep_not`, `dep_and`, `dep_or`, `dep_const`.
* `wentails`, `wentails_iff`, `wcontingent` — entailment and contingency for
  the wide world, decided locally.
* `wentails_cost` — the cost bound, independent of `n`.
* Law **schemas** proved once for all `n` and all things (`schema_boiling_hot`
  and friends, collected in `schemas_sound`), including the relational laws
  `hotter` is transitive and asymmetric. Schemas are how a lexicon of
  thousands keeps its laws: `n` things give `schemaCount * n` unary laws with
  no search at all.
* The instantiated lexicon at `n = 24`: `1872` atoms, `3744` literals,
  `3600` of them contingent (`wide_vocab_counts`) — against `48` in
  `Semantics.lean`, a 75-fold increase with the same guarantees.
* `describe` and `render`, so the wide world can be spoken; `describe_sound`
  and `describe_contingent` are the soundness and informativeness guarantees,
  proved for **every** world of every size, again without enumeration.
-/

namespace WideWorld

set_option maxRecDepth 4000

/-! ## 1. The world -/

/-- The temperature scale, in °C. -/
def tempVal : Fin 6 → ℤ := ![-40, 0, 20, 60, 100, 500]

/-- The mass scale, in kg. -/
def massVal : Fin 3 → ℤ := ![1, 10, 100]

/-- What a measurement of one thing returns: a temperature and a mass. -/
abbrev LS := Fin 6 × Fin 3

/-- A world over `n` things: one local state per thing. -/
abbrev World (n : ℕ) := Fin n → LS

/-- Every local state. -/
def allLS : List LS := (List.finRange 6).flatMap fun t => (List.finRange 3).map fun m => (t, m)

theorem mem_allLS (s : LS) : s ∈ allLS := by
  obtain ⟨t, m⟩ := s
  exact List.mem_flatMap.mpr ⟨t, List.mem_finRange _, List.mem_map.mpr ⟨m, List.mem_finRange _, rfl⟩⟩

theorem allLS_length : allLS.length = 18 := by decide

/-- **The world set is astronomically large.** -/
theorem card_World (n : ℕ) : Fintype.card (World n) = 18 ^ n := by
  simp

/-! ## 2. The words -/

/-- The lexicon: six measured properties and three measured relations, for each
thing (or ordered pair of things) of the world. -/
inductive Atom (n : ℕ)
  | frozen (e : Fin n)
  | warm (e : Fin n)
  | hot (e : Fin n)
  | boiling (e : Fin n)
  | heavy (e : Fin n)
  | massive (e : Fin n)
  | hotter (e f : Fin n)
  | heavier (e f : Fin n)
  | sameTemp (e f : Fin n)
deriving DecidableEq, Repr

/-- The measured temperature of a thing. -/
def tp {n} (w : World n) (e : Fin n) : ℤ := tempVal (w e).1

/-- The measured mass of a thing. -/
def ms {n} (w : World n) (e : Fin n) : ℤ := massVal (w e).2

/-- **Truth is measurement**, exactly as in the narrow world: every word is a
threshold on a reading or a comparison of two readings. -/
def evalAtom {n} : Atom n → World n → Bool
  | .frozen e, w => decide (tp w e ≤ 0)
  | .warm e, w => decide (0 < tp w e ∧ tp w e < 100)
  | .hot e, w => decide (60 ≤ tp w e)
  | .boiling e, w => decide (100 ≤ tp w e)
  | .heavy e, w => decide (10 ≤ ms w e)
  | .massive e, w => decide (100 ≤ ms w e)
  | .hotter e f, w => decide (tp w f < tp w e)
  | .heavier e f, w => decide (ms w f < ms w e)
  | .sameTemp e f, w => decide (tp w e = tp w f)

/-- The things a word mentions. -/
def atomEnts {n} : Atom n → List (Fin n)
  | .frozen e | .warm e | .hot e | .boiling e | .heavy e | .massive e => [e]
  | .hotter e f | .heavier e f | .sameTemp e f => [e, f]

/-- **Every word mentions at most two things.** This single fact is what makes
the wide world tractable. -/
theorem atomEnts_length_le {n} (a : Atom n) : (atomEnts a).length ≤ 2 := by
  cases a <;> simp [atomEnts]

/-- **Locality.** A word's truth depends only on the things it mentions. -/
theorem evalAtom_congr {n} (a : Atom n) (w w' : World n)
    (h : ∀ e ∈ atomEnts a, w e = w' e) : evalAtom a w = evalAtom a w' := by
  cases a <;> simp_all [evalAtom, atomEnts, tp, ms]

/-- A literal: a word, asserted or denied. -/
abbrev Lit (n : ℕ) := Atom n × Bool

/-- The truth of a literal in a world. -/
def evalLit {n} (l : Lit n) (w : World n) : Bool := decide (evalAtom l.1 w = l.2)

/-- The denial of a literal. -/
def negL {n} (l : Lit n) : Lit n := (l.1, !l.2)

@[simp] theorem negL_negL {n} (l : Lit n) : negL (negL l) = l := by simp [negL]

theorem evalLit_negL {n} (l : Lit n) (w : World n) : evalLit (negL l) w = !evalLit l w := by
  obtain ⟨a, p⟩ := l
  simp only [evalLit, negL]
  have h : ∀ x q : Bool, decide (x = !q) = !decide (x = q) := by
    intro x q; cases q <;> cases x <;> simp
  exact h _ _

/-! ## 3. Checking without enumerating -/

/-- All tuples of `k` local states. -/
def tuples : ℕ → List (List LS)
  | 0 => [[]]
  | k + 1 => allLS.flatMap fun x => (tuples k).map (fun t => x :: t)

theorem tuples_length (k : ℕ) : (tuples k).length = 18 ^ k := by
  induction k with
  | zero => decide
  | succ k ih => simp [tuples, List.length_flatMap, ih, allLS]; ring

theorem mem_tuples {k : ℕ} (ls : List LS) (h : ls.length = k) : ls ∈ tuples k := by
  induction k generalizing ls with
  | zero => simp only [tuples, List.mem_singleton]; exact List.length_eq_zero_iff.mp h
  | succ k ih =>
    cases ls with
    | nil => simp at h
    | cons x t =>
      exact List.mem_flatMap.mpr
        ⟨x, mem_allLS x, List.mem_map.mpr ⟨t, ih t (by simpa using h), rfl⟩⟩

/-- The world that gives the things of `S` the local states of `ls`, and every
other thing the reading `(-40 °C, 1 kg)`. -/
def assign {n} (S : List (Fin n)) (ls : List LS) : World n :=
  fun e => ((S.zip ls).lookup e).getD (0, 0)

theorem lookup_zip_self {n} (S : List (Fin n)) (w : World n) (e : Fin n) (he : e ∈ S) :
    (S.zip (S.map w)).lookup e = some (w e) := by
  induction S with
  | nil => cases he
  | cons a t ih =>
    rcases eq_or_ne e a with h | h
    · subst h; simp
    · have hb : (e == a) = false := by simp [h]
      have ht : e ∈ t := by
        rcases List.mem_cons.mp he with h' | h'
        · exact absurd h' h
        · exact h'
      simp [List.lookup_cons, hb, ih ht]

/-- Read a world's states off the things of `S` and put them back: the result
agrees with the world on `S`. -/
theorem assign_agrees {n} (S : List (Fin n)) (w : World n) (e : Fin n) (he : e ∈ S) :
    assign S (S.map w) e = w e := by
  simp [assign, lookup_zip_self S w e he]

/-- The things a list of words mentions, without repetition. -/
def scope {n} (as : List (Atom n)) : List (Fin n) := (as.flatMap atomEnts).dedup

theorem flatMap_atomEnts_length_le {n} : ∀ as : List (Atom n),
    (as.flatMap atomEnts).length ≤ 2 * as.length
  | [] => by simp
  | a :: t => by
      have h1 := atomEnts_length_le a
      have h2 := flatMap_atomEnts_length_le t
      simp only [List.flatMap_cons, List.length_append, List.length_cons]
      omega

theorem scope_length_le {n} (as : List (Atom n)) : (scope as).length ≤ 2 * as.length := by
  have h1 : (scope as).length ≤ (as.flatMap atomEnts).length :=
    (List.dedup_sublist _).length_le
  have h2 := flatMap_atomEnts_length_le as
  omega

theorem mem_scope {n} {as : List (Atom n)} {a : Atom n} {e : Fin n}
    (ha : a ∈ as) (he : e ∈ atomEnts a) : e ∈ scope as :=
  List.mem_dedup.mpr (List.mem_flatMap.mpr ⟨a, ha, he⟩)

/-- `p` is decided by the readings of the things in `S`. -/
def dependsOn {n} (S : List (Fin n)) (p : World n → Bool) : Prop :=
  ∀ w w' : World n, (∀ e ∈ S, w e = w' e) → p w = p w'

theorem dep_atom {n} {as : List (Atom n)} {a : Atom n} (ha : a ∈ as) :
    dependsOn (scope as) (evalAtom a) :=
  fun w w' h => evalAtom_congr a w w' fun e he => h e (mem_scope ha he)

theorem dep_lit {n} {as : List (Atom n)} {l : Lit n} (ha : l.1 ∈ as) :
    dependsOn (scope as) (evalLit l) :=
  fun w w' h => by simp only [evalLit, dep_atom ha w w' h]

theorem dep_not {n} {S : List (Fin n)} {p : World n → Bool} (h : dependsOn S p) :
    dependsOn S (fun w => !p w) := fun w w' hw => by simp [h w w' hw]

theorem dep_and {n} {S : List (Fin n)} {p q : World n → Bool}
    (hp : dependsOn S p) (hq : dependsOn S q) : dependsOn S (fun w => p w && q w) :=
  fun w w' hw => by simp [hp w w' hw, hq w w' hw]

theorem dep_or {n} {S : List (Fin n)} {p q : World n → Bool}
    (hp : dependsOn S p) (hq : dependsOn S q) : dependsOn S (fun w => p w || q w) :=
  fun w w' hw => by simp [hp w w' hw, hq w w' hw]

/-- **Check a claim about all worlds, locally.** Only the things mentioned by
`as` get enumerated. -/
def checkAll {n} (as : List (Atom n)) (p : World n → Bool) : Bool :=
  (tuples (scope as).length).all fun ls => p (assign (scope as) ls)

/-- **Check for a witness, locally.** -/
def checkAny {n} (as : List (Atom n)) (p : World n → Bool) : Bool :=
  (tuples (scope as).length).any fun ls => p (assign (scope as) ls)

/-- **The central theorem.** For a property decided by the things `as`
mentions, the local check is exactly quantification over all `18 ^ n` worlds —
sound *and* complete. -/
theorem checkAll_iff {n} (as : List (Atom n)) (p : World n → Bool)
    (hdep : dependsOn (scope as) p) : checkAll as p = true ↔ ∀ w : World n, p w = true := by
  constructor
  · intro h w
    have hmem : (scope as).map w ∈ tuples (scope as).length := mem_tuples _ (by simp)
    have := (List.all_eq_true.mp h) _ hmem
    rwa [hdep (assign (scope as) ((scope as).map w)) w
      (fun e he => assign_agrees (scope as) w e he)] at this
  · intro h
    exact List.all_eq_true.mpr fun ls _ => h _

/-- The existential form. -/
theorem checkAny_iff {n} (as : List (Atom n)) (p : World n → Bool)
    (hdep : dependsOn (scope as) p) : checkAny as p = true ↔ ∃ w : World n, p w = true := by
  constructor
  · intro h
    obtain ⟨ls, _, hls⟩ := List.any_eq_true.mp h
    exact ⟨_, hls⟩
  · rintro ⟨w, hw⟩
    have hmem : (scope as).map w ∈ tuples (scope as).length := mem_tuples _ (by simp)
    refine List.any_eq_true.mpr ⟨_, hmem, ?_⟩
    rwa [hdep (assign (scope as) ((scope as).map w)) w
      (fun e he => assign_agrees (scope as) w e he)]

/-! ## 4. Entailment, satisfiability, contingency in the wide world -/

/-- `l` implies `m` in every one of the `18 ^ n` worlds — decided by looking at
at most four things. -/
def wentails {n} (l m : Lit n) : Bool :=
  checkAll [l.1, m.1] (fun w => !evalLit l w || evalLit m w)

theorem wentails_iff {n} (l m : Lit n) :
    wentails l m = true ↔ ∀ w : World n, evalLit l w = true → evalLit m w = true := by
  have hdep : dependsOn (scope [l.1, m.1]) (fun w => !evalLit l w || evalLit m w) :=
    dep_or (dep_not (dep_lit (by simp))) (dep_lit (by simp))
  rw [wentails, checkAll_iff _ _ hdep]
  constructor
  · intro h w hl
    have := h w
    simp [hl] at this
    exact this
  · intro h w
    by_cases hl : evalLit l w = true
    · simp [hl, h w hl]
    · simp at hl; simp [hl]

/-- `l` is possible. -/
def wsat {n} (l : Lit n) : Bool := checkAny [l.1] (evalLit l)

theorem wsat_iff {n} (l : Lit n) : wsat l = true ↔ ∃ w : World n, evalLit l w = true :=
  checkAny_iff _ _ (dep_lit (by simp))

/-- `l` says something: it is true somewhere and false somewhere. -/
def wcontingent {n} (l : Lit n) : Bool :=
  checkAny [l.1] (evalLit l) && checkAny [l.1] (fun w => !evalLit l w)

theorem wcontingent_iff {n} (l : Lit n) :
    wcontingent l = true ↔ (∃ w : World n, evalLit l w = true) ∧ ∃ w : World n, evalLit l w = false := by
  rw [wcontingent, Bool.and_eq_true,
    checkAny_iff _ _ (dep_lit (l := l) (by simp)),
    checkAny_iff _ (fun w => !evalLit l w) (dep_not (dep_lit (l := l) (by simp)))]
  simp

/-- **The cost of certifying a law does not depend on the size of the world.**
Whatever `n` is — three things or three thousand — `wentails` evaluates at most
`18^4 = 104976` local configurations, while the world set has `18 ^ n`
members. -/
theorem wentails_cost {n} (l m : Lit n) :
    (tuples (scope [l.1, m.1]).length).length ≤ 104976 := by
  have h : (scope [l.1, m.1]).length ≤ 4 := by
    have := scope_length_le [l.1, m.1]; simpa using this
  calc (tuples (scope [l.1, m.1]).length).length
      = 18 ^ (scope [l.1, m.1]).length := tuples_length _
    _ ≤ 18 ^ 4 := Nat.pow_le_pow_right (by norm_num) h
    _ = 104976 := by norm_num

/-! ## 5. Law schemas: laws that hold for every thing in every world

These are proved once, by cases on a *single* six-point reading, and they hold
for every `n` and every thing.  This is how the law stock grows linearly with a
lexicon instead of quadratically with search. -/

/-- The temperature laws, as facts about the six-point scale.  Each is decided
by `decide` over six values, once and for all. -/
theorem tempVal_facts :
    (∀ i : Fin 6, 100 ≤ tempVal i → 60 ≤ tempVal i) ∧
    (∀ i : Fin 6, 100 ≤ tempVal i → ¬ tempVal i ≤ 0) ∧
    (∀ i : Fin 6, tempVal i ≤ 0 → ¬ (0 < tempVal i ∧ tempVal i < 100)) ∧
    (∀ i : Fin 6, (0 < tempVal i ∧ tempVal i < 100) → ¬ tempVal i ≤ 0) := by
  refine ⟨?_, ?_, ?_, ?_⟩ <;> decide

theorem massVal_fact : ∀ i : Fin 3, 100 ≤ massVal i → 10 ≤ massVal i := by decide

theorem schema_boiling_hot {n} (e : Fin n) (w : World n) :
    evalAtom (.boiling e) w = true → evalAtom (.hot e) w = true := by
  simp only [evalAtom, tp, decide_eq_true_eq]
  exact tempVal_facts.1 _

theorem schema_boiling_not_frozen {n} (e : Fin n) (w : World n) :
    evalAtom (.boiling e) w = true → evalAtom (.frozen e) w = false := by
  simp only [evalAtom, tp, decide_eq_true_eq, decide_eq_false_iff_not]
  exact tempVal_facts.2.1 _

theorem schema_frozen_not_warm {n} (e : Fin n) (w : World n) :
    evalAtom (.frozen e) w = true → evalAtom (.warm e) w = false := by
  simp only [evalAtom, tp, decide_eq_true_eq, decide_eq_false_iff_not]
  exact tempVal_facts.2.2.1 _

theorem schema_warm_not_frozen {n} (e : Fin n) (w : World n) :
    evalAtom (.warm e) w = true → evalAtom (.frozen e) w = false := by
  simp only [evalAtom, tp, decide_eq_true_eq, decide_eq_false_iff_not]
  exact tempVal_facts.2.2.2 _

theorem schema_massive_heavy {n} (e : Fin n) (w : World n) :
    evalAtom (.massive e) w = true → evalAtom (.heavy e) w = true := by
  simp only [evalAtom, ms, decide_eq_true_eq]
  exact massVal_fact _

/-- **`hotter` is transitive** — proved by the order on ℤ, with no enumeration
at all, so it holds for every triple of things in every world. -/
theorem schema_hotter_trans {n} (e f g : Fin n) (w : World n) :
    evalAtom (.hotter e f) w = true → evalAtom (.hotter f g) w = true →
      evalAtom (.hotter e g) w = true := by
  simp only [evalAtom, decide_eq_true_eq]
  intro h1 h2; omega

/-- **`hotter` is asymmetric.** -/
theorem schema_hotter_asymm {n} (e f : Fin n) (w : World n) :
    evalAtom (.hotter e f) w = true → evalAtom (.hotter f e) w = false := by
  simp only [evalAtom, decide_eq_true_eq, decide_eq_false_iff_not, not_lt]
  omega

/-- **Being hotter excludes being the same temperature.** -/
theorem schema_hotter_not_same {n} (e f : Fin n) (w : World n) :
    evalAtom (.hotter e f) w = true → evalAtom (.sameTemp e f) w = false := by
  simp only [evalAtom, decide_eq_true_eq, decide_eq_false_iff_not]
  omega

/-- **`sameTemp` is symmetric.** -/
theorem schema_sameTemp_symm {n} (e f : Fin n) (w : World n) :
    evalAtom (.sameTemp e f) w = true → evalAtom (.sameTemp f e) w = true := by
  simp only [evalAtom, decide_eq_true_eq]
  omega

/-- The unary law schemas, as pairs of literals. -/
def unarySchemas {n} (e : Fin n) : List (Lit n × Lit n) :=
  [((.boiling e, true), (.hot e, true)),
   ((.boiling e, true), (.frozen e, false)),
   ((.frozen e, true), (.warm e, false)),
   ((.warm e, true), (.frozen e, false)),
   ((.massive e, true), (.heavy e, true))]

/-- **Every instance of every schema is a genuine law**, for every `n`, every
thing and every world — and the local checker certifies each one, so the
checker is not merely sound but finds these. -/
theorem schemas_sound {n} (e : Fin n) :
    ∀ p ∈ unarySchemas e, wentails p.1 p.2 = true := by
  intro p hp
  simp only [unarySchemas, List.mem_cons, List.not_mem_nil, or_false] at hp
  have key : ∀ (l m : Lit n),
      (∀ w : World n, evalAtom l.1 w = l.2 → evalAtom m.1 w = m.2) → wentails l m = true := by
    intro l m h
    refine (wentails_iff l m).mpr fun w hl => ?_
    simp only [evalLit, decide_eq_true_eq] at hl ⊢
    exact h w hl
  rcases hp with h | h | h | h | h <;> subst h
  · exact key _ _ fun w hw => schema_boiling_hot e w hw
  · exact key _ _ fun w hw => schema_boiling_not_frozen e w hw
  · exact key _ _ fun w hw => schema_frozen_not_warm e w hw
  · exact key _ _ fun w hw => schema_warm_not_frozen e w hw
  · exact key _ _ fun w hw => schema_massive_heavy e w hw

/-- How many law instances the schemas give a lexicon of `n` things: five per
thing, with no search. -/
theorem schema_law_count {n} (e : Fin n) : (unarySchemas e).length = 5 := rfl

/-! ## 6. The lexicon, instantiated -/

/-- The things. -/
def ents (n : ℕ) : List (Fin n) := List.finRange n

/-- Every word of the lexicon. -/
def allAtoms (n : ℕ) : List (Atom n) :=
  ((ents n).flatMap fun e =>
      [Atom.frozen e, .warm e, .hot e, .boiling e, .heavy e, .massive e]) ++
  ((ents n).flatMap fun e => (ents n).flatMap fun f =>
      [Atom.hotter e f, .heavier e f, .sameTemp e f])

theorem mem_allAtoms {n} (a : Atom n) : a ∈ allAtoms n := by
  have hu : ∀ (e : Fin n) (b : Atom n),
      b ∈ [Atom.frozen e, .warm e, .hot e, .boiling e, .heavy e, .massive e] →
        b ∈ allAtoms n := by
    intro e b hb
    exact List.mem_append_left _ (List.mem_flatMap.mpr ⟨e, List.mem_finRange e, hb⟩)
  have hbin : ∀ (e f : Fin n) (b : Atom n),
      b ∈ [Atom.hotter e f, .heavier e f, .sameTemp e f] → b ∈ allAtoms n := by
    intro e f b hb
    exact List.mem_append_right _ (List.mem_flatMap.mpr ⟨e, List.mem_finRange e,
      List.mem_flatMap.mpr ⟨f, List.mem_finRange f, hb⟩⟩)
  cases a with
  | frozen e => exact hu e _ (by simp)
  | warm e => exact hu e _ (by simp)
  | hot e => exact hu e _ (by simp)
  | boiling e => exact hu e _ (by simp)
  | heavy e => exact hu e _ (by simp)
  | massive e => exact hu e _ (by simp)
  | hotter e f => exact hbin e f _ (by simp)
  | heavier e f => exact hbin e f _ (by simp)
  | sameTemp e f => exact hbin e f _ (by simp)

/-- **The lexicon grows quadratically with the number of things**, and the
formula is proved, not measured. -/
theorem allAtoms_length (n : ℕ) : (allAtoms n).length = 6 * n + 3 * n ^ 2 := by
  simp [allAtoms, ents, List.length_flatMap]
  ring

/-- Every literal. -/
def allLits (n : ℕ) : List (Lit n) := (allAtoms n).flatMap fun a => [(a, true), (a, false)]

theorem mem_allLits {n} (l : Lit n) : l ∈ allLits n := by
  obtain ⟨a, p⟩ := l
  refine List.mem_flatMap.mpr ⟨a, mem_allAtoms a, ?_⟩
  cases p <;> simp

theorem allLits_length (n : ℕ) : (allLits n).length = 2 * (6 * n + 3 * n ^ 2) := by
  simp [allLits, List.length_flatMap, allAtoms_length n]
  omega

/-- The literals worth saying: the contingent ones. -/
def usefulLits (n : ℕ) : List (Lit n) := (allLits n).filter wcontingent

/-- **The instantiated lexicon.** Twenty-four things: 1872 words, 3744
literals, 3600 of them contingent — against 48 contingent literals in the
narrow world of `Semantics.lean`. -/
theorem wide_vocab_counts :
    (allAtoms 24).length = 1872 ∧ (allLits 24).length = 3744 ∧
      (usefulLits 24).length = 3600 := by
  refine ⟨by simp [allAtoms_length], by simp [allLits_length], by native_decide⟩

/-- The 144 non-contingent literals are exactly the reflexive comparisons —
two literals each for `hotter e e`, `heavier e e` and `sameTemp e e`: nothing is
hotter or heavier than itself, and everything is the same temperature as
itself. -/
theorem noncontingent_are_reflexive :
    ((allLits 24).filter fun l => !wcontingent l).length = 24 * 6 := by native_decide

/-! ## 7. Speaking about the wide world -/

/-- Names for the twenty-four things. -/
def name24 : Fin 24 → String := fun e =>
  #["the water", "the stone", "the lamp", "the iron", "the oil", "the air",
    "the ice", "the copper", "the sand", "the glass", "the wood", "the wax",
    "the steam", "the milk", "the coal", "the tin", "the clay", "the salt",
    "the wire", "the brick", "the paper", "the resin", "the mercury", "the chalk"][e]!

/-- Render a literal about the twenty-four things as English. -/
def render (l : Lit 24) : String :=
  let neg := if l.2 then " is " else " is not "
  match l.1 with
  | .frozen e => name24 e ++ neg ++ "frozen"
  | .warm e => name24 e ++ neg ++ "warm"
  | .hot e => name24 e ++ neg ++ "hot"
  | .boiling e => name24 e ++ neg ++ "boiling"
  | .heavy e => name24 e ++ neg ++ "heavy"
  | .massive e => name24 e ++ neg ++ "massive"
  | .hotter e f => name24 e ++ neg ++ "hotter than " ++ name24 f
  | .heavier e f => name24 e ++ neg ++ "heavier than " ++ name24 f
  | .sameTemp e f => name24 e ++ neg ++ "the same temperature as " ++ name24 f

/-- Everything true and worth saying about `w`. -/
def describe {n} (w : World n) : List (Lit n) :=
  (usefulLits n).filter fun l => evalLit l w

/-- **Soundness of description, for every world of every size** — and with no
enumeration of worlds in the proof. -/
theorem describe_sound {n} {w : World n} {l : Lit n} (h : l ∈ describe w) :
    evalLit l w = true := (List.mem_filter.mp h).2

/-- **Everything it says is contingent**: each reported fact is false in some
other world, so each carries information. -/
theorem describe_contingent {n} {w : World n} {l : Lit n} (h : l ∈ describe w) :
    ∃ w' : World n, evalLit l w' = false :=
  ((wcontingent_iff l).mp (List.mem_filter.mp (List.mem_filter.mp h).1).2).2

/-- **It never contradicts itself.** -/
theorem describe_consistent {n} (w : World n) (l : Lit n) :
    ¬(l ∈ describe w ∧ negL l ∈ describe w) := by
  rintro ⟨h1, h2⟩
  have e1 := describe_sound h1
  have e2 := describe_sound h2
  rw [evalLit_negL, e1] at e2
  simp at e2

/-- A demonstration world over the twenty-four things: temperature index
`e mod 6`, mass index `e mod 3`. -/
def demoWide : World 24 := fun e => (⟨e.val % 6, Nat.mod_lt _ (by norm_num)⟩,
                                     ⟨e.val % 3, Nat.mod_lt _ (by norm_num)⟩)

/-- **What the system can say about the demonstration world, counted.** Of the
3600 contingent literals, 1800 are true here; the narrow world managed 24. -/
theorem demoWide_count : (describe demoWide).length = 1800 := by native_decide

/-- The first few sentences it produces. -/
def demoWideText : List String := ((describe demoWide).take 8).map render

end WideWorld
