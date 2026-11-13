import Mathlib

/-!
# A deterministic micro-world, and sentences that make logical sense in it

Everything so far has been about *dimensional* logic: whether `E = mc²`
balances.  That is real meaning, but it is not yet language — it cannot say
"the water is not warm because the water is frozen".

This file builds the smallest honest thing that can: a **tangible, measurable
micro-world** and a sentence algebra over it whose truth conditions are decided
by measurement, plus the connectives that let sentences grow — `not`, `and`,
`if … then …`, `because`, and `after we …`.

## The world

Three tangible things (`Ent`: water, stone, lamp), each with a **temperature**
on the scale `-10, 0, 20, 100 °C` and a **mass** on the scale `1, 10 kg`.  That
is `4³ · 2³ = 512` worlds (`allWorlds_length`), and the list `allWorlds` is
complete (`mem_allWorlds`): every quantifier below really does range over all
of them.

## The words

* Measured properties: `frozen`, `boiling`, `warm`, `heavy` — each is a
  threshold on a measurement, so nothing is stipulated.
* Measured relations: `hotter`, `heavier`.
* Negation: a *literal* is a property together with a polarity.
* Deterministic actions: `heat`, `cool`, `load`, each moving the world one step
  along a scale (`step`).
* Connectives: `conj` (and), `law` (if … then …), `because`, `after`.

## What "makes logical sense" means here, and what is proved

The two connectives that carry logic are given **law-like** truth conditions,
not truth-in-this-world conditions:

* `law l m` is true iff `l` implies `m` in *every one of the 512 worlds*
  (`speak_laws_nonvacuous`), so a stated law is a real law;
* `because l m` is true in `w` iff `m` and `l` both hold in `w`, `m ≠ l`, **and**
  `m` implies `l` in every world (`because_is_explanatory`) — a stated reason
  really is a sufficient ground, not a coincidence.

`speak w` generates the sentences the system is willing to say in `w`:

* `speak_sound` — every one of them is true in `w`;
* `speak_consistent` — it never says both a thing and its denial, and the whole
  set is jointly satisfiable (by `w`);
* `speak_lits_contingent` — the properties it reports are contingent: each is
  false in some world, so each says something;
* `speak_laws_nonvacuous` — the laws it states have satisfiable antecedents, so
  no law holds merely for want of a case;
* `speakLaws_no_contrapositive_duplicate` — and it does not state the same law
  twice in contrapositive disguise;
* `modus_ponens_sound`, `law_trans` — the sentences chain: what it says can be
  reasoned with;
* `after_sound` — a prediction is checked against the world the action
  produces.

The counts for a concrete world are measured, not asserted (`demo_counts`), and
`Chat.lean` turns this into a conversation.
-/

namespace Semantics

set_option maxRecDepth 100000

/-! ## 1. The world -/

/-- The tangible things the system can talk about. -/
inductive Ent
  | water | stone | lamp
deriving DecidableEq, Fintype, Repr

/-- The temperature scale, in °C. -/
def tempVal : Fin 4 → ℤ := ![-10, 0, 20, 100]

/-- The mass scale, in kg. -/
def massVal : Fin 2 → ℤ := ![1, 10]

/-- A world: a temperature reading and a mass reading for each thing. -/
abbrev World := (Ent → Fin 4) × (Ent → Fin 2)

/-- The measured temperature of a thing. -/
def temp (w : World) (e : Ent) : ℤ := tempVal (w.1 e)

/-- The measured mass of a thing. -/
def mass (w : World) (e : Ent) : ℤ := massVal (w.2 e)

/-- All temperature assignments. -/
def assign4 : List (Ent → Fin 4) :=
  (List.finRange 4).flatMap fun a => (List.finRange 4).flatMap fun b =>
    (List.finRange 4).map fun c => fun e =>
      match e with | .water => a | .stone => b | .lamp => c

/-- All mass assignments. -/
def assign2 : List (Ent → Fin 2) :=
  (List.finRange 2).flatMap fun a => (List.finRange 2).flatMap fun b =>
    (List.finRange 2).map fun c => fun e =>
      match e with | .water => a | .stone => b | .lamp => c

/-- Every world. -/
def allWorlds : List World := assign4.flatMap fun t => assign2.map fun m => (t, m)

theorem allWorlds_length : allWorlds.length = 512 := by native_decide

/-- The enumeration really is complete. -/
theorem mem_allWorlds (w : World) : w ∈ allWorlds := by
  obtain ⟨t, m⟩ := w
  have ht : t = fun e => match e with
      | .water => t .water | .stone => t .stone | .lamp => t .lamp := by
    funext e; cases e <;> rfl
  have hm : m = fun e => match e with
      | .water => m .water | .stone => m .stone | .lamp => m .lamp := by
    funext e; cases e <;> rfl
  simp only [allWorlds, List.mem_flatMap, List.mem_map, assign4, assign2]
  exact ⟨_, ⟨t .water, List.mem_finRange _, t .stone, List.mem_finRange _,
      t .lamp, List.mem_finRange _, rfl⟩,
    _, ⟨m .water, List.mem_finRange _, m .stone, List.mem_finRange _,
      m .lamp, List.mem_finRange _, rfl⟩, by rw [← ht, ← hm]⟩

/-! ## 2. The words -/

/-- The measured properties and relations the system can assert. -/
inductive Atom
  | frozen (e : Ent)
  | boiling (e : Ent)
  | warm (e : Ent)
  | heavy (e : Ent)
  | hotter (e f : Ent)
  | heavier (e f : Ent)
deriving DecidableEq, Fintype, Repr

/-- **Truth is measurement.**  Every atom is a threshold or a comparison on the
readings of the world; nothing is stipulated. -/
def evalAtom : Atom → World → Bool
  | .frozen e, w => decide (temp w e ≤ 0)
  | .boiling e, w => decide (100 ≤ temp w e)
  | .warm e, w => decide (0 < temp w e ∧ temp w e < 100)
  | .heavy e, w => decide (10 ≤ mass w e)
  | .hotter e f, w => decide (temp w f < temp w e)
  | .heavier e f, w => decide (mass w f < mass w e)

/-- A literal: a property, asserted (`true`) or denied (`false`). -/
abbrev Lit := Atom × Bool

/-- The truth of a literal in a world. -/
def evalLit (l : Lit) (w : World) : Bool := decide (evalAtom l.1 w = l.2)

/-- The denial of a literal. -/
def negL (l : Lit) : Lit := (l.1, !l.2)

@[simp] theorem negL_negL (l : Lit) : negL (negL l) = l := by
  simp [negL]

theorem evalLit_negL (l : Lit) (w : World) : evalLit (negL l) w = !evalLit l w := by
  obtain ⟨a, p⟩ := l
  simp only [evalLit, negL]
  have h : ∀ x q : Bool, decide (x = !q) = !decide (x = q) := by
    intro x q; cases q <;> cases x <;> simp
  exact h _ _

/-- Deterministic actions on the world. -/
inductive Act
  | heat (e : Ent)
  | cool (e : Ent)
  | load (e : Ent)
deriving DecidableEq, Fintype, Repr

/-- One step up the temperature scale (saturating). -/
def upT : Fin 4 → Fin 4 := ![1, 2, 3, 3]
/-- One step down the temperature scale (saturating). -/
def downT : Fin 4 → Fin 4 := ![0, 0, 1, 2]

/-- **The world after an action** — deterministic, no randomness anywhere. -/
def step : Act → World → World
  | .heat e, w => (fun x => if x = e then upT (w.1 x) else w.1 x, w.2)
  | .cool e, w => (fun x => if x = e then downT (w.1 x) else w.1 x, w.2)
  | .load e, w => (w.1, fun x => if x = e then 1 else w.2 x)

/-! ## 3. Sentences -/

/-- A sentence.  `lit l` states a literal; `law l m` states "if `l` then `m`";
`because l m` states "`l`, because `m`"; `after c l` states "after we `c`, `l`";
`conj` is "and". -/
inductive Sent
  | lit (l : Lit)
  | law (l m : Lit)
  | because (l m : Lit)
  | because2 (l m n : Lit)
  | after (c : Act) (l : Lit)
  | conj (s t : Sent)
deriving DecidableEq, Repr

/-- Two literals together imply a third in **every** world. -/
def entails2 (m n l : Lit) : Bool :=
  allWorlds.all fun w => !(evalLit m w && evalLit n w) || evalLit l w

/-- `l` implies `m` in **every** world. -/
def entails (l m : Lit) : Bool := allWorlds.all fun w => !evalLit l w || evalLit m w

/-- The characterisation of `entails`: it is exactly implication in all worlds. -/
theorem entails_iff (l m : Lit) :
    entails l m = true ↔ ∀ w : World, evalLit l w = true → evalLit m w = true := by
  constructor
  · intro h w hl
    have := (List.all_eq_true.mp h) w (mem_allWorlds w)
    simp [hl] at this
    exact this
  · intro h
    refine List.all_eq_true.mpr ?_
    intro w _
    by_cases hl : evalLit l w = true
    · simp [hl, h w hl]
    · simp at hl
      simp [hl]

theorem entails2_iff (m n l : Lit) :
    entails2 m n l = true ↔
      ∀ w : World, evalLit m w = true → evalLit n w = true → evalLit l w = true := by
  constructor
  · intro h w hm hn
    have := (List.all_eq_true.mp h) w (mem_allWorlds w)
    simp [hm, hn] at this
    exact this
  · intro h
    refine List.all_eq_true.mpr ?_
    intro w _
    by_cases hm : evalLit m w = true
    · by_cases hn : evalLit n w = true
      · simp [hm, hn, h w hm hn]
      · simp at hn; simp [hn]
    · simp at hm; simp [hm]

/-- `l` is possible: some world satisfies it. -/
def satisfiable (l : Lit) : Bool := allWorlds.any fun w => evalLit l w

/-- `l` is contingent: it holds somewhere and fails somewhere.  A contingent
literal is one whose assertion carries information. -/
def contingent (l : Lit) : Bool := satisfiable l && satisfiable (negL l)

/-- Whether a law is worth stating: it holds everywhere, both sides are
contingent, and it is not the trivial `l → l`. -/
def lawOK (l m : Lit) : Bool :=
  entails l m && contingent l && contingent m && decide (l ≠ m)

/-- **The truth conditions of a sentence.**  Note that `law`, and the
entailment clause of `because`, are checked against *every* world, so they are
laws and reasons, not coincidences of the present state. -/
def evalS : Sent → World → Bool
  | .lit l, w => evalLit l w
  | .law l m, _ => lawOK l m
  | .because l m, w =>
      evalLit l w && evalLit m w && entails m l && decide (l ≠ m) && contingent l
  | .because2 l m n, w =>
      evalLit l w && evalLit m w && evalLit n w && entails2 m n l &&
        decide (l ≠ m) && decide (l ≠ n) && decide (m ≠ n) && contingent l &&
        !entails m l && !entails n l
  | .after c l, w => evalLit l (step c w)
  | .conj s t, w => evalS s w && evalS t w

theorem evalS_law_indep (l m : Lit) (w w' : World) : evalS (.law l m) w = evalS (.law l m) w' := rfl

/-! ## 4. The vocabulary, and what the system is willing to say -/

/-- The things. -/
def ents : List Ent := [.water, .stone, .lamp]

/-- Every atom. -/
def allAtoms : List Atom :=
  ents.map .frozen ++ ents.map .boiling ++ ents.map .warm ++ ents.map .heavy ++
  (ents.flatMap fun e => ents.map fun f => Atom.hotter e f) ++
  (ents.flatMap fun e => ents.map fun f => Atom.heavier e f)

theorem mem_allAtoms (a : Atom) : a ∈ allAtoms := by revert a; decide

theorem allAtoms_length : allAtoms.length = 30 := by decide

/-- Every literal. -/
def allLits : List Lit := allAtoms.flatMap fun a => [(a, true), (a, false)]

theorem mem_allLits (l : Lit) : l ∈ allLits := by
  obtain ⟨a, p⟩ := l
  refine List.mem_flatMap.mpr ⟨a, mem_allAtoms a, ?_⟩
  cases p <;> simp

/-- Every action. -/
def allActs : List Act := ents.map .heat ++ ents.map .cool ++ ents.map .load

/-- The literals worth asserting: the contingent ones. -/
def usefulLits : List Lit := allLits.filter contingent

/-- The position of a literal in the vocabulary, used only to state each law in
one canonical direction. -/
def litIdx (l : Lit) : Nat := 2 * allAtoms.idxOf l.1 + (if l.2 then 0 else 1)

/-- Of a law and its contrapositive, keep exactly one. -/
def canonicalLaw (l m : Lit) : Bool :=
  decide (100 * litIdx l + litIdx m ≤ 100 * litIdx (negL m) + litIdx (negL l))

/-- The measured properties of `w`, reported as literals. -/
def speakLits (w : World) : List Sent :=
  (usefulLits.filter fun l => evalLit l w).map Sent.lit

/-- The laws the system knows.  These do not depend on the world. -/
def speakLaws : List Sent :=
  (usefulLits.flatMap fun l => usefulLits.map fun m => Sent.law l m).filter
    fun s => match s with | .law l m => lawOK l m && canonicalLaw l m | _ => false

/-- The explanations available in `w`. -/
def speakBecause (w : World) : List Sent :=
  (usefulLits.flatMap fun l => usefulLits.map fun m => Sent.because l m).filter
    fun s => evalS s w

/-- The predictions worth making in `w`: those where the action actually
changes the answer. -/
def speakAfter (w : World) : List Sent :=
  (allActs.flatMap fun c => usefulLits.map fun l => Sent.after c l).filter
    fun s => match s with
      | .after c l => evalLit l (step c w) && !evalLit l w
      | _ => false

/-- **Everything the system is willing to say in `w`.** -/
def speak (w : World) : List Sent :=
  speakLits w ++ speakLaws ++ speakBecause w ++ speakAfter w

/-! ## 5. What is guaranteed about what it says -/

theorem speakLits_sound {w : World} {s : Sent} (h : s ∈ speakLits w) : evalS s w = true := by
  obtain ⟨l, hl, rfl⟩ := List.mem_map.mp h
  exact (List.mem_filter.mp hl).2

theorem speakLaws_sound {w : World} {s : Sent} (h : s ∈ speakLaws) : evalS s w = true := by
  obtain ⟨hmem, hfil⟩ := List.mem_filter.mp h
  obtain ⟨l, _, hb⟩ := List.mem_flatMap.mp hmem
  obtain ⟨m, _, rfl⟩ := List.mem_map.mp hb
  simp only [Bool.and_eq_true] at hfil
  exact hfil.1

theorem speakBecause_sound {w : World} {s : Sent} (h : s ∈ speakBecause w) : evalS s w = true :=
  (List.mem_filter.mp h).2

theorem speakAfter_sound {w : World} {s : Sent} (h : s ∈ speakAfter w) : evalS s w = true := by
  obtain ⟨hmem, hfil⟩ := List.mem_filter.mp h
  obtain ⟨c, _, ha⟩ := List.mem_flatMap.mp hmem
  obtain ⟨l, _, rfl⟩ := List.mem_map.mp ha
  simp only [Bool.and_eq_true] at hfil
  exact hfil.1

/-- **Soundness.**  Everything the system says in `w` is true in `w`. -/
theorem speak_sound {w : World} {s : Sent} (h : s ∈ speak w) : evalS s w = true := by
  rcases List.mem_append.mp h with h | h
  · rcases List.mem_append.mp h with h | h
    · rcases List.mem_append.mp h with h | h
      · exact speakLits_sound h
      · exact speakLaws_sound h
    · exact speakBecause_sound h
  · exact speakAfter_sound h

/-- **Consistency.**  It never asserts a literal and its denial. -/
theorem speak_consistent (w : World) (l : Lit) :
    ¬ (Sent.lit l ∈ speak w ∧ Sent.lit (negL l) ∈ speak w) := by
  rintro ⟨h1, h2⟩
  have e1 := speak_sound h1
  have e2 := speak_sound h2
  simp only [evalS] at e1 e2
  rw [evalLit_negL, e1] at e2
  simp at e2

/-- **The whole set is jointly satisfiable** — by the world it describes. -/
theorem speak_satisfiable (w : World) : ∀ s ∈ speak w, evalS s w = true :=
  fun _ hs => speak_sound hs

/-- **The reports are informative.**  Every literal it asserts is contingent:
there is a world in which that very sentence is false. -/
theorem speak_lits_contingent {w : World} {l : Lit} (h : Sent.lit l ∈ speakLits w) :
    ∃ w' : World, evalS (.lit l) w' = false := by
  obtain ⟨m, hm, hEq⟩ := List.mem_map.mp h
  have hml : m = l := by cases hEq; rfl
  subst hml
  have hc : contingent m = true := (List.mem_filter.mp (List.mem_filter.mp hm).1).2
  simp only [contingent, Bool.and_eq_true, satisfiable, List.any_eq_true] at hc
  obtain ⟨_, ⟨w', _, hw'⟩⟩ := hc
  refine ⟨w', ?_⟩
  rw [evalLit_negL] at hw'
  simpa [evalS] using hw'

/-- **The laws are laws.**  A stated `if l then m` holds in every one of the 512
worlds, its antecedent is satisfiable — so it is not true for want of a case —
and both sides are contingent. -/
theorem speak_laws_nonvacuous {l m : Lit} (h : Sent.law l m ∈ speakLaws) :
    (∀ w : World, evalLit l w = true → evalLit m w = true) ∧
      (∃ w : World, evalLit l w = true) ∧ l ≠ m := by
  obtain ⟨_, hfil⟩ := List.mem_filter.mp h
  simp only [Bool.and_eq_true, lawOK, decide_eq_true_eq] at hfil
  obtain ⟨⟨⟨⟨hent, hsat⟩, _⟩, hne⟩, _⟩ := hfil
  refine ⟨(entails_iff l m).mp hent, ?_, hne⟩
  simp only [contingent, Bool.and_eq_true, satisfiable, List.any_eq_true] at hsat
  obtain ⟨⟨w, _, hw⟩, _⟩ := hsat
  exact ⟨w, hw⟩

/-- **No law is stated twice in contrapositive disguise.** -/
theorem speakLaws_no_contrapositive_duplicate :
    speakLaws.all (fun s => match s with
      | .law l m => !speakLaws.contains (.law (negL m) (negL l))
      | _ => true) = true := by native_decide

/-- **A pair of reasons is a reason, and a minimal one.**  When the system says
"`l`, because `m` and `n`", the two together force `l` in every world, both hold
here, and neither of them would have sufficed alone. -/
theorem because2_is_minimal_explanation {w : World} {l m n : Lit}
    (h : evalS (.because2 l m n) w = true) :
    evalLit l w = true ∧ evalLit m w = true ∧ evalLit n w = true ∧
      (∀ w' : World, evalLit m w' = true → evalLit n w' = true → evalLit l w' = true) ∧
      entails m l = false ∧ entails n l = false := by
  simp only [evalS, Bool.and_eq_true, decide_eq_true_eq, Bool.not_eq_true'] at h
  refine ⟨by tauto, by tauto, by tauto, ?_, by tauto, by tauto⟩
  exact (entails2_iff m n l).mp (by tauto)

/-- **A reason is a reason.**  When the system says "`l` because `m`", `m` really
does force `l` — in every world, not just this one — and both are the case
here. -/
theorem because_is_explanatory {w : World} {l m : Lit} (h : Sent.because l m ∈ speakBecause w) :
    evalLit l w = true ∧ evalLit m w = true ∧
      (∀ w' : World, evalLit m w' = true → evalLit l w' = true) ∧ l ≠ m := by
  have hs := speakBecause_sound h
  simp only [evalS, Bool.and_eq_true, decide_eq_true_eq] at hs
  obtain ⟨⟨⟨⟨hl, hm⟩, hent⟩, hne⟩, _⟩ := hs
  exact ⟨hl, hm, (entails_iff m l).mp hent, hne⟩

/-- **A prediction is checked against the world it predicts** — and it is a
prediction of a *change*: the literal is false now and true afterwards. -/
theorem after_sound {w : World} {c : Act} {l : Lit} (h : Sent.after c l ∈ speakAfter w) :
    evalLit l (step c w) = true ∧ evalLit l w = false := by
  obtain ⟨_, hfil⟩ := List.mem_filter.mp h
  simp only [Bool.and_eq_true, Bool.not_eq_true'] at hfil
  exact hfil

/-- **The sentences chain: modus ponens.**  If the system states the law
`if l then m` and reports `l`, then `m` is true. -/
theorem modus_ponens_sound {w : World} {l m : Lit}
    (hlaw : Sent.law l m ∈ speakLaws) (hlit : Sent.lit l ∈ speak w) :
    evalS (.lit m) w = true := by
  obtain ⟨himp, _, _⟩ := speak_laws_nonvacuous hlaw
  exact himp w (speak_sound hlit)

/-- **…and they chain further: laws compose.** -/
theorem law_trans {l m n : Lit} (h₁ : entails l m = true) (h₂ : entails m n = true) :
    entails l n = true :=
  (entails_iff l n).mpr fun w hl => (entails_iff m n).mp h₂ w ((entails_iff l m).mp h₁ w hl)

/-! ## 6. A concrete world, counted -/

/-- Water at −10 °C and 1 kg, stone at 20 °C and 10 kg, lamp at 100 °C and 1 kg. -/
def demoWorld : World :=
  (fun e => match e with | .water => 0 | .stone => 2 | .lamp => 3,
   fun e => match e with | .water => 0 | .stone => 1 | .lamp => 0)

/-- The size of the working vocabulary: contingent literals. -/
theorem usefulLits_length : usefulLits.length = 48 := by native_decide

/-- **What the system can say about `demoWorld`, counted.** -/
theorem demo_counts :
    (speakLits demoWorld).length = 24 ∧
    speakLaws.length = 39 ∧
    (speakBecause demoWorld).length = 30 ∧
    (speakAfter demoWorld).length = 14 ∧
    (speak demoWorld).length = 107 := by
  refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> native_decide

end Semantics
