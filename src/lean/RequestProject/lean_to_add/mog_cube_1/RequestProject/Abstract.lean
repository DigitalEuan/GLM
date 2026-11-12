import Mathlib
import RequestProject.WideWorld

/-!
# Abstract words: meanings that are not thresholds on a reading

Report 2 §7.3, third of the things that were *not* achieved:

> **No abstract nouns yet.** Every word still bottoms out in a threshold on a
> reading. "Mother" is no closer than it was.

This file adds a second kind of word.  A *structured world* carries the same
measurements as `WideWorld`, and in addition a **mother pointer** — a partial
map `mom : Fin n → Option (Fin n)` saying, of each thing, what it came from.
The pointer is required to run downwards (`acyclic`), so the things form a
forest.

On top of that pointer sit words that no threshold can express:

* `isMother m e` — read straight off the structure;
* `isAncestor a e` — the transitive closure, computed by following the pointer;
* `isGrandmother`, `isSibling`, `isOrphan`.

## What is proved

* `mother_not_definable_by_readings` — the honest statement of what has been
  added.  *No* function of the measurements whatsoever, threshold or otherwise,
  agrees with `isMother`: two structured worlds can have identical readings and
  disagree about who the mother is.  Conversely `readings_not_definable_by_kin`
  shows the measured words are equally unreachable from the structure, so the
  two halves of the lexicon are genuinely independent.
* The laws, as schemas proved for every `n` and every structured world, with no
  enumeration: `mother_implies_ancestor`, `ancestor_trans`, `ancestor_irrefl`,
  `ancestor_asymm`, `grandmother_implies_ancestor`, `sibling_symm`,
  `sibling_irrefl`, `orphan_has_no_ancestor`.
* `kin_vocab_counts` — the size of the added lexicon.
* `describeK_sound` — description in the combined language is sound in every
  structured world of every size.
-/

namespace Abstract

set_option maxRecDepth 20000

open WideWorld

/-! ## 1. Structured worlds -/

/-- A world with structure: the measurements of `WideWorld`, plus a partial
"came from" pointer that runs downwards, so that nothing descends from
itself. -/
structure SWorld (n : ℕ) where
  read : World n
  mom : Fin n → Option (Fin n)
  acyclic : ∀ e m, mom e = some m → m.val < e.val

/-! ## 2. The kin words -/

/-- `m` is the mother of `e`. -/
def isMother {n} (s : SWorld n) (m e : Fin n) : Bool := s.mom e = some m

/-- `a` is an ancestor of `e`: follow the pointer.  The recursion terminates
because the pointer runs downwards. -/
def isAncestor {n} (s : SWorld n) (a : Fin n) (e : Fin n) : Bool :=
  match h : s.mom e with
  | none => false
  | some m => decide (m = a) || isAncestor s a m
termination_by e.val
decreasing_by exact s.acyclic e m h

/-- `g` is a grandmother of `e`. -/
def isGrandmother {n} (s : SWorld n) (g e : Fin n) : Bool :=
  match s.mom e with
  | none => false
  | some m => isMother s g m

/-- `e` and `f` are siblings: same mother, different things. -/
def isSibling {n} (s : SWorld n) (e f : Fin n) : Bool :=
  (s.mom e).isSome && (s.mom e == s.mom f) && (e != f)

/-- `e` is an orphan: it came from nothing in this world. -/
def isOrphan {n} (s : SWorld n) (e : Fin n) : Bool := (s.mom e).isNone

/-! ## 3. The laws, proved as schemas -/

theorem isAncestor_none {n} (s : SWorld n) (a e : Fin n) (h : s.mom e = none) :
    isAncestor s a e = false := by
  rw [isAncestor]
  split
  · rfl
  · rename_i m h'; rw [h] at h'; exact absurd h' (by simp)

theorem isAncestor_some {n} (s : SWorld n) (a e m : Fin n) (h : s.mom e = some m) :
    isAncestor s a e = (decide (m = a) || isAncestor s a m) := by
  rw [isAncestor]
  split
  · rename_i h'; rw [h] at h'; exact absurd h' (by simp)
  · rename_i m' h'
    rw [h] at h'
    have : m' = m := by simpa using h'.symm
    subst this; rfl

/-- **An ancestor is always lower down.** -/
theorem ancestor_lt {n} (s : SWorld n) (a : Fin n) :
    ∀ k (e : Fin n), e.val = k → isAncestor s a e = true → a.val < e.val := by
  intro k
  induction k using Nat.strong_induction_on with
  | _ k ih =>
    intro e he h
    rcases hm : s.mom e with _ | m
    · rw [isAncestor_none s a e hm] at h; simp at h
    · rw [isAncestor_some s a e m hm] at h
      have hlt : m.val < e.val := s.acyclic e m hm
      simp only [Bool.or_eq_true, decide_eq_true_eq] at h
      rcases h with h | h
      · subst h; exact hlt
      · have := ih m.val (by omega) m rfl h
        omega

/-- **Nothing is its own ancestor.** -/
theorem ancestor_irrefl {n} (s : SWorld n) (e : Fin n) : isAncestor s e e = false := by
  by_contra hc
  have h : isAncestor s e e = true := by simpa using hc
  have := ancestor_lt s e e.val e rfl h
  omega

/-- **Ancestry has a direction.** -/
theorem ancestor_asymm {n} (s : SWorld n) (a e : Fin n) (h : isAncestor s a e = true) :
    isAncestor s e a = false := by
  have h1 := ancestor_lt s a e.val e rfl h
  by_contra hc
  have h2 := ancestor_lt s e a.val a rfl (by simpa using hc)
  omega

/-- **A mother is an ancestor.** -/
theorem mother_implies_ancestor {n} (s : SWorld n) (m e : Fin n) (h : isMother s m e = true) :
    isAncestor s m e = true := by
  have hm : s.mom e = some m := by simpa [isMother] using h
  rw [isAncestor_some s m e m hm]
  simp

/-- **Ancestry is transitive.** -/
theorem ancestor_trans {n} (s : SWorld n) (b : Fin n) :
    ∀ k (e a : Fin n), e.val = k → isAncestor s a e = true → isAncestor s b a = true →
      isAncestor s b e = true := by
  intro k
  induction k using Nat.strong_induction_on with
  | _ k ih =>
    intro e a he hae hba
    rcases hm : s.mom e with _ | m
    · rw [isAncestor_none s a e hm] at hae; simp at hae
    · rw [isAncestor_some s a e m hm] at hae
      have hlt : m.val < e.val := s.acyclic e m hm
      simp only [Bool.or_eq_true, decide_eq_true_eq] at hae
      rw [isAncestor_some s b e m hm]
      rcases hae with rfl | hae
      · simpa using Or.inr hba
      · have := ih m.val (by omega) m a rfl hae hba
        simpa using Or.inr this

/-- **A grandmother is an ancestor.** -/
theorem grandmother_implies_ancestor {n} (s : SWorld n) (g e : Fin n)
    (h : isGrandmother s g e = true) : isAncestor s g e = true := by
  rcases hm : s.mom e with _ | m
  · rw [isGrandmother, hm] at h; simp at h
  · rw [isGrandmother, hm] at h
    exact ancestor_trans s g e.val e m rfl (mother_implies_ancestor s m e (by simp [isMother, hm]))
      (mother_implies_ancestor s g m h)

/-- **Sibling is symmetric.** -/
theorem sibling_symm {n} (s : SWorld n) (e f : Fin n) (h : isSibling s e f = true) :
    isSibling s f e = true := by
  simp only [isSibling, Bool.and_eq_true, beq_iff_eq, bne_iff_ne, ne_eq] at h ⊢
  obtain ⟨⟨h1, h2⟩, h3⟩ := h
  exact ⟨⟨by rw [← h2]; exact h1, h2.symm⟩, fun hc => h3 hc.symm⟩

/-- **Nothing is its own sibling.** -/
theorem sibling_irrefl {n} (s : SWorld n) (e : Fin n) : isSibling s e e = false := by
  simp [isSibling]

/-- **Siblings share their ancestors.** -/
theorem siblings_share_mother {n} (s : SWorld n) (e f m : Fin n)
    (h : isSibling s e f = true) (hm : isMother s m e = true) : isMother s m f = true := by
  simp only [isSibling, Bool.and_eq_true, beq_iff_eq, bne_iff_ne, ne_eq] at h
  simp only [isMother, decide_eq_true_eq] at hm ⊢
  rw [← h.1.2, hm]

/-- **An orphan has no ancestors at all.** -/
theorem orphan_has_no_ancestor {n} (s : SWorld n) (e a : Fin n) (h : isOrphan s e = true) :
    isAncestor s a e = false := by
  have hm : s.mom e = none := by
    rcases hx : s.mom e with _ | m
    · rfl
    · rw [isOrphan, hx] at h; simp at h
  rw [isAncestor_none s a e hm]

/-- **An orphan is nobody's child, and a thing with a mother is no orphan.** -/
theorem orphan_iff_no_mother {n} (s : SWorld n) (e : Fin n) :
    isOrphan s e = true ↔ ∀ m, isMother s m e = false := by
  constructor
  · intro h m
    rcases hx : s.mom e with _ | m'
    · simp [isMother, hx]
    · rw [isOrphan, hx] at h; simp at h
  · intro h
    rcases hx : s.mom e with _ | m'
    · simp [isOrphan, hx]
    · have := h m'
      simp [isMother, hx] at this

/-! ## 4. Why these words are new

The point of the file, stated as a theorem rather than a hope: the measurements
do not determine kinship, and kinship does not determine the measurements. -/

/-- Two structured worlds with **the same readings** that disagree about who the
mother is.  Both are legal: the pointer runs downwards in each. -/
def kinYes {n} (h2 : 2 ≤ n) (w : World n) : SWorld n where
  read := w
  mom := fun e => if e.val = 1 then some ⟨0, by omega⟩ else none
  acyclic := by
    intro e m he
    by_cases hb : e.val = 1
    · rw [if_pos hb] at he
      have hm : m = (⟨0, by omega⟩ : Fin n) := by simpa using he.symm
      rw [hm]
      show (0 : ℕ) < e.val
      omega
    · rw [if_neg hb] at he; exact absurd he (by simp)

/-- The same readings, and no mothers at all. -/
def kinNo {n} (w : World n) : SWorld n where
  read := w
  mom := fun _ => none
  acyclic := by intro e m he; exact absurd he (by simp)

theorem kinYes_mother {n} (h2 : 2 ≤ n) (w : World n) :
    isMother (kinYes h2 w) ⟨0, by omega⟩ ⟨1, by omega⟩ = true := by
  simp [isMother, kinYes]

theorem kinNo_mother {n} (h2 : 2 ≤ n) (w : World n) :
    isMother (kinNo w) ⟨0, by omega⟩ ⟨1, by omega⟩ = false := by
  simp [isMother, kinNo]

/-- **"Mother" is not a threshold, nor any function of the measurements at
all.**  Whatever function `F` of the readings you propose — a threshold, a
comparison, a Boolean combination of thousands of them — it cannot agree with
`isMother` everywhere, because two structured worlds with *identical* readings
differ on the mother question. -/
theorem mother_not_definable_by_readings {n} (h2 : 2 ≤ n) :
    ¬ ∃ F : World n → Bool, ∀ s : SWorld n,
        isMother s ⟨0, by omega⟩ ⟨1, by omega⟩ = F s.read := by
  rintro ⟨F, hF⟩
  set w : World n := fun _ => (0, 0) with hw
  have h1 := hF (kinYes h2 w)
  have h0 := hF (kinNo w)
  rw [kinYes_mother h2 w] at h1
  rw [kinNo_mother h2 w] at h0
  have : (kinYes h2 w).read = (kinNo w).read := rfl
  rw [this, ← h0] at h1
  exact absurd h1 (by simp)

/-- The same in the other direction: two structured worlds with **the same
kinship** and different readings, so no function of the structure can express a
measured word either.  The two halves of the lexicon are independent. -/
theorem readings_not_definable_by_kin {n} (h2 : 2 ≤ n) :
    ¬ ∃ G : (Fin n → Option (Fin n)) → Bool, ∀ s : SWorld n,
        evalAtom (Atom.boiling ⟨0, by omega⟩) s.read = G s.mom := by
  rintro ⟨G, hG⟩
  let cold : SWorld n := kinNo (fun _ => (0, 0))
  let hot : SWorld n := kinNo (fun _ => (5, 0))
  have h1 := hG cold
  have h2' := hG hot
  have e1 : evalAtom (Atom.boiling (⟨0, by omega⟩ : Fin n)) cold.read = false := by
    simp [evalAtom, tp, cold, kinNo, tempVal]
  have e2 : evalAtom (Atom.boiling (⟨0, by omega⟩ : Fin n)) hot.read = true := by
    simp [evalAtom, tp, hot, kinNo, tempVal]
  rw [e1] at h1; rw [e2] at h2'
  have : (cold : SWorld n).mom = hot.mom := rfl
  rw [this] at h1
  rw [← h2'] at h1
  exact absurd h1 (by simp)

/-! ## 5. The combined lexicon -/

/-- A word of the combined language: a measurement word or a kin word. -/
inductive KAtom (n : ℕ)
  | measured (a : Atom n)
  | mother (m e : Fin n)
  | ancestor (a e : Fin n)
  | grandmother (g e : Fin n)
  | sibling (e f : Fin n)
  | orphan (e : Fin n)
deriving DecidableEq, Repr

/-- Truth in a structured world. -/
def evalK {n} : KAtom n → SWorld n → Bool
  | .measured a, s => evalAtom a s.read
  | .mother m e, s => isMother s m e
  | .ancestor a e, s => isAncestor s a e
  | .grandmother g e, s => isGrandmother s g e
  | .sibling e f, s => isSibling s e f
  | .orphan e, s => isOrphan s e

/-- A literal of the combined language. -/
abbrev KLit (n : ℕ) := KAtom n × Bool

def evalKLit {n} (l : KLit n) (s : SWorld n) : Bool := decide (evalK l.1 s = l.2)

def negK {n} (l : KLit n) : KLit n := (l.1, !l.2)

theorem evalKLit_negK {n} (l : KLit n) (s : SWorld n) :
    evalKLit (negK l) s = !evalKLit l s := by
  obtain ⟨a, p⟩ := l
  simp only [evalKLit, negK]
  have h : ∀ x q : Bool, decide (x = !q) = !decide (x = q) := by
    intro x q; cases q <;> cases x <;> simp
  exact h _ _

/-- The kin words of a lexicon of `n` things. -/
def kinAtoms (n : ℕ) : List (KAtom n) :=
  ((List.finRange n).flatMap fun e => (List.finRange n).flatMap fun f =>
      [KAtom.mother e f, .ancestor e f, .grandmother e f, .sibling e f]) ++
  ((List.finRange n).map fun e => KAtom.orphan e)

/-- Every word of the combined language. -/
def allKAtoms (n : ℕ) : List (KAtom n) := (allAtoms n).map KAtom.measured ++ kinAtoms n

/-- **The abstract half of the lexicon is bigger than the measured half.**  At
`n = 24`: `1872` measured words and `2328` kin words, `4200` in all, `8400`
literals. -/
theorem kin_vocab_counts :
    (kinAtoms 24).length = 2328 ∧ (allKAtoms 24).length = 4200 := by
  constructor
  · simp [kinAtoms, List.length_flatMap]
  · simp [allKAtoms, kinAtoms, List.length_flatMap, allAtoms_length]

/-- The formula behind the count, for every `n`. -/
theorem kinAtoms_length (n : ℕ) : (kinAtoms n).length = 4 * n ^ 2 + n := by
  simp [kinAtoms, List.length_flatMap]; ring

/-! ## 6. Speaking the combined language -/

/-- Everything true in a structured world, among a given stock of literals. -/
def describeK {n} (stock : List (KLit n)) (s : SWorld n) : List (KLit n) :=
  stock.filter fun l => evalKLit l s

/-- **Soundness, for every structured world of every size.** -/
theorem describeK_sound {n} {stock : List (KLit n)} {s : SWorld n} {l : KLit n}
    (h : l ∈ describeK stock s) : evalKLit l s = true := (List.mem_filter.mp h).2

/-- **It never contradicts itself.** -/
theorem describeK_consistent {n} (stock : List (KLit n)) (s : SWorld n) (l : KLit n) :
    ¬(l ∈ describeK stock s ∧ negK l ∈ describeK stock s) := by
  rintro ⟨h1, h2⟩
  have e1 := describeK_sound h1
  have e2 := describeK_sound h2
  rw [evalKLit_negK, e1] at e2
  simp at e2

/-- English for the combined language over the twenty-four named things. -/
def renderK (l : KLit 24) : String :=
  let neg := if l.2 then " is " else " is not "
  match l.1 with
  | .measured a => render (a, l.2)
  | .mother m e => name24 m ++ neg ++ "the mother of " ++ name24 e
  | .ancestor a e => name24 a ++ neg ++ "an ancestor of " ++ name24 e
  | .grandmother g e => name24 g ++ neg ++ "a grandmother of " ++ name24 e
  | .sibling e f => name24 e ++ neg ++ "a sibling of " ++ name24 f
  | .orphan e => name24 e ++ neg ++ "an orphan"

/-! ## 7. A demonstration -/

/-- A family tree over the twenty-four things: the things are the nodes of a
binary tree, so that `the water` is the root, everything else came from the
thing at `(e-1)/2`, and each mother has two children. -/
def demoS : SWorld 24 where
  read := demoWide
  mom := fun e => if 1 ≤ e.val then some ⟨(e.val - 1) / 2, by omega⟩ else none
  acyclic := by
    intro e m he
    by_cases h : 1 ≤ e.val
    · rw [if_pos h] at he
      have hm : m = (⟨(e.val - 1) / 2, by omega⟩ : Fin 24) := by simpa using he.symm
      rw [hm]
      show (e.val - 1) / 2 < e.val
      omega
    · rw [if_neg h] at he; exact absurd he (by simp)

/-- Every literal of the combined language over twenty-four things. -/
def allKLits (n : ℕ) : List (KLit n) := (allKAtoms n).flatMap fun a => [(a, true), (a, false)]

theorem allKLits_length_gen (n : ℕ) : (allKLits n).length = 2 * (allKAtoms n).length := by
  simp only [allKLits]
  induction allKAtoms n with
  | nil => rfl
  | cons a t ih => simp [List.flatMap_cons, ih]; omega

theorem allKLits_length : (allKLits 24).length = 8400 := by
  rw [allKLits_length_gen, kin_vocab_counts.2]

/-- The positive kin facts of the demonstration world. -/
def demoKinFacts : List (KLit 24) :=
  ((kinAtoms 24).map fun a => (a, true)).filter fun l => evalKLit l demoS

/-- **What the abstract half of the language says about the demonstration
world.** -/
theorem demoKin_count : demoKinFacts.length = 137 := by native_decide

/-- The first sentences the abstract half produces. -/
def demoKinText : List String := (demoKinFacts.take 6).map renderK

/-- **Every one of them is true**, by soundness of filtering. -/
theorem demoKinFacts_true : ∀ l ∈ demoKinFacts, evalKLit l demoS = true := by
  intro l hl
  exact (List.mem_filter.mp hl).2

end Abstract
