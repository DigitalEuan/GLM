import Mathlib
import RequestProject.GLM.ThirdSort

/-!
# The imperative grammar: count-first trees, fuel, and three programs with state

The second half of round 7 of the order of work
(`glm_universal.reasoning.reverse_tct_imp`, Phase 95,
`studies/IMPERATIVE_GRAMMAR_STUDY.md`) gives sentences to programs with
state: assignment, loops, branches, functions and `match`.  This file proves
what the round rests on.

* **Count-first trees are uniquely readable** (`decT_encT`,
  `encT_injective`): every construct of the grammar is a head followed by a
  counted list of parts (a program's steps, a block's steps, a call's
  arguments, a `match`'s cases, a pattern's alternatives).  For any spelling
  of heads and of counts that has a left inverse on its own prefix, the
  spelling *head, count, part, …, part* of a tree has one too: a sentence
  followed by anything reads back to its tree and leaves the rest, and no
  two trees share a sentence.
* **A step limit only withholds** (`exec_mono`, `exec_agree`): the fuel
  semantics of a while language is monotone in its fuel, so an answer given
  under one limit is the answer under every larger limit, and two limits
  never give different answers.
* **Three of the Phase 64 programs with state, proved** (`euclidLoop_gcd`,
  `sum_telescope`, `factFuel_eq`): the loop `while b: a, b = b, a % b`
  returns `gcd a b` once its fuel exceeds `b`; the accumulation of `loop-acc`
  telescopes, `∑_{k=1}^{n} 1/(k(k+1)) = n/(n+1)`; and the recursion of
  `def-fact` returns `n!` once its fuel exceeds `n`.
-/

namespace GLM.ImperativeGrammar

open GLM.ThirdSort

/-! ## Count-first trees -/

/-- A tree whose every node is a head with a list of parts. -/
inductive CTree (H : Type) where
  | node : H → List (CTree H) → CTree H

variable {W H : Type}

/-- The spelling: head, count, then the parts in order. -/
def encT (hc : PrefixCode W H) (nc : PrefixCode W ℕ) : CTree H → List W
  | .node h ts => hc.enc h ++ nc.enc ts.length ++ encList hc nc ts
where
  /-- The parts, one after another. -/
  encList (hc : PrefixCode W H) (nc : PrefixCode W ℕ) : List (CTree H) → List W
    | [] => []
    | t :: ts => encT hc nc t ++ encList hc nc ts

/-- How deep a tree is: the fuel its reading needs. -/
def depth : CTree H → ℕ
  | .node _ ts => depthList ts + 1
where
  /-- The greatest depth of a list of trees. -/
  depthList : List (CTree H) → ℕ
    | [] => 0
    | t :: ts => max (depth t) (depthList ts)

/-- Read `k` items with a reader `d`. -/
def iterDec {α : Type} (d : List W → Option (α × List W)) :
    ℕ → List W → Option (List α × List W)
  | 0, ws => some ([], ws)
  | k + 1, ws =>
    match d ws with
    | none => none
    | some (a, r) => (iterDec d k r).map fun p => (a :: p.1, p.2)

/-- Read a tree with `n` units of fuel. -/
def decT (hc : PrefixCode W H) (nc : PrefixCode W ℕ) :
    ℕ → List W → Option (CTree H × List W)
  | 0, _ => none
  | n + 1, ws =>
    match hc.dec ws with
    | none => none
    | some (h, r) =>
      match nc.dec r with
      | none => none
      | some (k, r') =>
        (iterDec (decT hc nc n) k r').map fun p => (CTree.node h p.1, p.2)

theorem iterDec_encList (hc : PrefixCode W H) (nc : PrefixCode W ℕ)
    (d : List W → Option (CTree H × List W)) :
    ∀ ts : List (CTree H),
      (∀ t ∈ ts, ∀ rest, d (encT hc nc t ++ rest) = some (t, rest)) →
      ∀ rest, iterDec d ts.length (encT.encList hc nc ts ++ rest) =
        some (ts, rest)
  | [], _, rest => by simp [iterDec, encT.encList]
  | t :: ts, h, rest => by
    have ht := h t (by simp) (encT.encList hc nc ts ++ rest)
    have ih := iterDec_encList hc nc d ts
      (fun u hu => h u (by simp [hu])) rest
    simp only [List.length_cons, encT.encList, List.append_assoc, iterDec, ht,
      ih, Option.map_some]

theorem depth_lt_of_mem {h : H} {ts : List (CTree H)} {t : CTree H}
    (ht : t ∈ ts) : depth t < depth (.node h ts) := by
  have key : ∀ us : List (CTree H), t ∈ us → depth t ≤ depth.depthList us := by
    intro us hu
    induction us with
    | nil => simp at hu
    | cons u us ih =>
      rcases List.mem_cons.mp hu with rfl | hu
      · simp [depth.depthList]
      · simp only [depth.depthList]
        exact le_max_of_le_right (ih hu)
  have := key ts ht
  simp only [depth]
  omega

/-- **Count-first trees are uniquely readable**: with fuel at least the
tree's depth, the spelling of a tree followed by anything reads back to the
tree and leaves the rest. -/
theorem decT_encT (hc : PrefixCode W H) (nc : PrefixCode W ℕ) :
    ∀ n (t : CTree H), depth t ≤ n → ∀ rest,
      decT hc nc n (encT hc nc t ++ rest) = some (t, rest) := by
  intro n
  induction n with
  | zero =>
    intro t ht
    cases t with
    | node h ts => simp [depth] at ht
  | succ n ih =>
    intro t ht rest
    cases t with
    | node h ts =>
      have hchild : ∀ u ∈ ts, ∀ rest,
          decT hc nc n (encT hc nc u ++ rest) = some (u, rest) := by
        intro u hu rest
        have := depth_lt_of_mem (h := h) hu
        exact ih u (by omega) rest
      have hl := iterDec_encList hc nc (decT hc nc n) ts hchild rest
      simp only [encT, List.append_assoc, decT, hc.dec_enc, nc.dec_enc, hl,
        Option.map_some]

/-- No two trees share a spelling. -/
theorem encT_injective (hc : PrefixCode W H) (nc : PrefixCode W ℕ) :
    Function.Injective (encT hc nc) := by
  intro s t hst
  have h1 := decT_encT hc nc (max (depth s) (depth t)) s (le_max_left _ _) []
  have h2 := decT_encT hc nc (max (depth s) (depth t)) t (le_max_right _ _) []
  rw [hst, h2] at h1
  exact (Prod.mk.inj (Option.some.inj h1)).1.symm

/-! ## A step limit only withholds -/

/-- A state: a value for every name. -/
abbrev State := String → ℤ

/-- A while language: the statement shapes of the imperative grammar, with
expressions and conditions as functions of the state. -/
inductive Com where
  | skip : Com
  | assign : String → (State → ℤ) → Com
  | seq : Com → Com → Com
  | ite : (State → Bool) → Com → Com → Com
  | loop : (State → Bool) → Com → Com

/-- The fuel semantics: every step spends one unit; no fuel, no answer. -/
def exec : ℕ → Com → State → Option State
  | 0, _, _ => none
  | _ + 1, .skip, s => some s
  | _ + 1, .assign x e, s => some (Function.update s x (e s))
  | n + 1, .seq c d, s => (exec n c s).bind (exec n d)
  | n + 1, .ite b c d, s => if b s then exec n c s else exec n d s
  | n + 1, .loop b c, s =>
    if b s then (exec n c s).bind (exec n (.loop b c)) else some s

/-- **The fuel semantics is monotone**: an answer under a limit is the
answer under every larger limit. -/
theorem exec_mono : ∀ {n m : ℕ} {c : Com} {s s' : State},
    exec n c s = some s' → n ≤ m → exec m c s = some s' := by
  intro n
  induction n with
  | zero => intro m c s s' h; simp [exec] at h
  | succ n ih =>
    intro m c s s' h hm
    obtain ⟨m, rfl⟩ : ∃ k, m = k + 1 := ⟨m - 1, by omega⟩
    have hnm : n ≤ m := by omega
    cases c with
    | skip => simpa [exec] using h
    | assign x e => simpa [exec] using h
    | seq c d =>
      simp only [exec, Option.bind_eq_some_iff] at h ⊢
      obtain ⟨t, h1, h2⟩ := h
      exact ⟨t, ih h1 hnm, ih h2 hnm⟩
    | ite b c d =>
      simp only [exec] at h ⊢
      split_ifs at h ⊢ <;> exact ih h hnm
    | loop b c =>
      simp only [exec] at h ⊢
      split_ifs at h ⊢ with hb
      · simp only [Option.bind_eq_some_iff] at h ⊢
        obtain ⟨t, h1, h2⟩ := h
        exact ⟨t, ih h1 hnm, ih h2 hnm⟩
      · exact h

/-- Two limits never give different answers. -/
theorem exec_agree {n m : ℕ} {c : Com} {s a b : State}
    (ha : exec n c s = some a) (hb : exec m c s = some b) : a = b := by
  rcases le_total n m with h | h
  · rw [exec_mono ha h] at hb; exact Option.some.inj hb
  · rw [exec_mono hb h] at ha; exact (Option.some.inj ha).symm

/-! ## Three programs with state -/

/-- `while b: a, b = b, a % b` then `a`, with fuel. -/
def euclidLoop : ℕ → ℕ → ℕ → Option ℕ
  | 0, _, _ => none
  | f + 1, a, b => if b = 0 then some a else euclidLoop f b (a % b)

/-- **The loop of `while-gcd` computes the gcd** once its fuel exceeds `b`. -/
theorem euclidLoop_gcd : ∀ f a b : ℕ, b < f → euclidLoop f a b = some (Nat.gcd a b) := by
  intro f
  induction f with
  | zero => intro a b h; omega
  | succ f ih =>
    intro a b hb
    by_cases h0 : b = 0
    · subst h0; simp [euclidLoop]
    · have hlt : a % b < f := by
        have := Nat.mod_lt a (Nat.pos_of_ne_zero h0)
        omega
      simp only [euclidLoop, h0, if_false]
      rw [ih b (a % b) hlt, Nat.gcd_comm b (a % b), ← Nat.gcd_rec,
        Nat.gcd_comm]

/-- The Phase 64 case itself: `gcd(1071, 462) = 21`. -/
theorem euclidLoop_1071_462 : euclidLoop 463 1071 462 = some 21 := by
  rw [euclidLoop_gcd 463 1071 462 (by norm_num)]
  norm_num

/-- **The accumulation of `loop-acc` telescopes**:
`∑_{k=1}^{n} 1/(k(k+1)) = n/(n+1)`. -/
theorem sum_telescope (n : ℕ) :
    ∑ k ∈ Finset.range n, (1 : ℚ) / ((k + 1) * (k + 2)) = n / (n + 1) := by
  induction n with
  | zero => simp
  | succ n ih =>
    rw [Finset.sum_range_succ, ih]
    push_cast
    field_simp
    ring

/-- The Phase 64 case itself: ten rounds give `10/11`. -/
theorem loop_acc_value :
    ∑ k ∈ Finset.range 10, (1 : ℚ) / ((k + 1) * (k + 2)) = 10 / 11 := by
  rw [sum_telescope]
  norm_num

/-- `def fact(n): if n == 0: return 1; return n * fact(n - 1)`, with fuel
(one unit per call). -/
def factFuel : ℕ → ℕ → Option ℕ
  | 0, _ => none
  | f + 1, n => if n = 0 then some 1 else (factFuel f (n - 1)).map (n * ·)

/-- **The recursion of `def-fact` computes `n!`** once its fuel exceeds `n`. -/
theorem factFuel_eq : ∀ f n : ℕ, n < f → factFuel f n = some n.factorial := by
  intro f
  induction f with
  | zero => intro n h; omega
  | succ f ih =>
    intro n hn
    by_cases h0 : n = 0
    · subst h0; simp [factFuel]
    · obtain ⟨m, rfl⟩ : ∃ m, n = m + 1 := ⟨n - 1, by omega⟩
      simp only [factFuel, Nat.add_one_ne_zero, if_false, Nat.add_sub_cancel]
      rw [ih m (by omega)]
      simp [Nat.factorial_succ]

end GLM.ImperativeGrammar
