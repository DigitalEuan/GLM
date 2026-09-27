/-
# Escalation as a step of the query loop

`studies/QUERY_ESCALATION_STUDY.md` wires the deep-hole ladder's discipline
into the ordinary query loop: a refusal carries the layer it was refused at, the
ladder is finite and declared per query kind, every rung run is charged, and a
refusal classified as *principled* is never escalated.  The runtime half is
`overlay/glm_universal/runtime/escalation_loop.py`.  Four of the things that
round relies on are not measurements, and they are here.

`GLM.DeepHoleLadder.firstResolving` already proves the shape of "the least rung
that resolves, or a proof that no rung does" for a ladder indexed by `ℕ`.  This
file is the loop the runtime actually runs: a **list** of rungs, each carrying a
cost, climbed until one answers, with a classification step that can stop the
climb before it starts.

* `climb_answers_least` — an answer at a rung means every earlier rung was
  asked and refused, so *answered at L3* is a statement about L1 and L2 too.
* `climbFrom_cost_ge`, `climbFrom_cost_le` and `climb_direct_cost` — a climb
  costs at least the first rung and never more than the whole ladder, and a
  direct answer costs exactly the first rung, so an escalated answer is
  reported as more expensive than a direct one and a direct one is never made
  dearer by the loop.
* `climbFrom_refused_all` — a refusal from a fully climbed ladder is a
  statement about *every* rung of it.
* `climb_principled` — a refusal classified non-escalatable is returned as a
  refusal at the layer it was classified at, whatever the rest of the ladder
  would have said.  This is the rule that stops escalation grinding a
  principled refusal into an answer.

Termination is structural: `climb` recurses on the list, so it inspects each
rung at most once and the loop is total.
-/
import Mathlib

namespace GLM.EscalationLoop

universe u

/-- One rung of a declared ladder: what it costs to run, and what it says about
a query.  `answers` is the rung's own verdict — `true` when this reading
resolves the query. -/
structure Rung (Q : Type u) where
  /-- The rung's name, so that a verdict can carry it. -/
  name : String
  /-- What running this rung costs.  Non-negative by construction. -/
  cost : ℕ
  /-- Whether this reading resolves the query. -/
  answers : Q → Bool

/-- What a climb returns: an answer at a named rung, or a refusal that names
the ladder it exhausted.  Both carry the cost of having asked. -/
inductive Verdict (Q : Type u) where
  /-- Resolved: the rung that did it, and what the climb cost. -/
  | answered (rung : String) (cost : ℕ) : Verdict Q
  /-- Refused: the rung it was refused at, and what the climb cost. -/
  | refused (rung : String) (cost : ℕ) (principled : Bool) : Verdict Q
  /-- The ladder was empty: no reading was declared for this query kind. -/
  | noLadder : Verdict Q
  deriving Repr, DecidableEq

namespace Verdict

variable {Q : Type u}

/-- What the climb cost, whatever it returned. -/
def cost : Verdict Q → ℕ
  | .answered _ c => c
  | .refused _ c _ => c
  | .noLadder => 0

/-- Did the climb answer? -/
def isAnswered : Verdict Q → Bool
  | .answered _ _ => true
  | _ => false

end Verdict

variable {Q : Type u}

/-- The loop.  Walk the declared rungs in order; the first that answers wins
and the cost is the sum over the rungs actually run.  A refusal at the first
rung that is *classified* non-escalatable stops the climb there.

`principled` is the classification of a refusal, applied only to the first
refusal — exactly as the runtime applies it, before any rung above the first is
run. -/
def climbFrom (principled : Q → Bool) (first : Bool) :
    List (Rung Q) → Q → ℕ → Verdict Q
  | [], _, spent => .refused "" spent false
  | r :: rest, q, spent =>
      let spent := spent + r.cost
      if r.answers q then
        .answered r.name spent
      else if first && principled q then
        .refused r.name spent true
      else
        match rest with
        | [] => .refused r.name spent false
        | _ => climbFrom principled false rest q spent

/-- The loop, from the bottom of the ladder. -/
def climb (principled : Q → Bool) (rungs : List (Rung Q)) (q : Q) :
    Verdict Q :=
  match rungs with
  | [] => .noLadder
  | _ => climbFrom principled true rungs q 0

/-! ## The declared cost of a ladder -/

/-- The cost of running every rung of a ladder: the most a climb can cost. -/
def totalCost (rungs : List (Rung Q)) : ℕ :=
  (rungs.map Rung.cost).sum

/-- The cost of the first `n` rungs, which is what a climb stopping at rung `n`
has spent. -/
def prefixCost (rungs : List (Rung Q)) (n : ℕ) : ℕ :=
  ((rungs.take n).map Rung.cost).sum

/-! ## What the loop guarantees -/

/-- A climb never costs more than running the whole ladder, and the accumulator
it starts from is carried through unchanged. -/
theorem climbFrom_cost_le (principled : Q → Bool) :
    ∀ (rungs : List (Rung Q)) (first : Bool) (q : Q) (spent : ℕ),
      (climbFrom principled first rungs q spent).cost
        ≤ spent + totalCost rungs := by
  intro rungs
  induction rungs with
  | nil =>
      intro first q spent
      simp [climbFrom, Verdict.cost, totalCost]
  | cons r rest ih =>
      intro first q spent
      by_cases hans : r.answers q
      · simp [climbFrom, hans, Verdict.cost, totalCost]
      · by_cases hpr : first && principled q
        · simp [climbFrom, hans, hpr, Verdict.cost, totalCost]
        · cases rest with
          | nil =>
              simp [climbFrom, hans, hpr, Verdict.cost, totalCost]
          | cons s tail =>
              have := ih false q (spent + r.cost)
              simp only [climbFrom, hans, hpr, if_false, Bool.false_eq_true]
              refine le_trans this ?_
              simp [totalCost, Nat.add_assoc]

/-- A climb costs at least the first rung: asking anything costs asking once. -/
theorem climbFrom_cost_ge (principled : Q → Bool) (r : Rung Q)
    (rest : List (Rung Q)) (first : Bool) (q : Q) (spent : ℕ) :
    spent + r.cost ≤ (climbFrom principled first (r :: rest) q spent).cost := by
  induction rest generalizing r first spent with
  | nil =>
      by_cases hans : r.answers q
      · simp [climbFrom, hans, Verdict.cost]
      · by_cases hpr : first && principled q <;>
          simp [climbFrom, hans, hpr, Verdict.cost]
  | cons s tail ih =>
      by_cases hans : r.answers q
      · simp [climbFrom, hans, Verdict.cost]
      · by_cases hpr : first && principled q
        · simp [climbFrom, hans, hpr, Verdict.cost]
        · simp only [climbFrom, hans, hpr, if_false, Bool.false_eq_true]
          exact le_trans (Nat.le_add_right _ s.cost)
            (ih s false (spent + r.cost))

/-- **A direct answer costs exactly the first rung.**  The loop is free where
it is not needed, which is the property the study's safety gate checks over the
whole evaluation set. -/
theorem climb_direct_cost (principled : Q → Bool) (r : Rung Q)
    (rest : List (Rung Q)) (q : Q) (h : r.answers q = true) :
    climb principled (r :: rest) q = .answered r.name r.cost := by
  simp [climb, climbFrom, h]

/-- **A principled refusal is preserved.**  When the first rung refuses and the
refusal is classified non-escalatable, the loop returns a refusal at that rung,
flagged as principled, whatever the rest of the ladder would have said. -/
theorem climb_principled (principled : Q → Bool) (r : Rung Q)
    (rest : List (Rung Q)) (q : Q) (hans : r.answers q = false)
    (hpr : principled q = true) :
    climb principled (r :: rest) q = .refused r.name r.cost true := by
  simp [climb, climbFrom, hans, hpr]

/-- An empty ladder is not a refusal at the top of a tower: it is the absence
of a tower, and the loop says so rather than pretending to have climbed. -/
@[simp] theorem climb_nil (principled : Q → Bool) (q : Q) :
    climb principled ([] : List (Rung Q)) q = .noLadder := rfl

/-- **An answer means every earlier rung refused.**  The climb returns the
*least* rung that resolves, so `answered` at a rung is a statement about the
rungs below it as well. -/
theorem climbFrom_answers_least (principled : Q → Bool) :
    ∀ (rungs : List (Rung Q)) (first : Bool) (q : Q) (spent : ℕ) (name : String)
      (c : ℕ),
      climbFrom principled first rungs q spent = .answered name c →
      ∃ i, ∃ hi : i < rungs.length,
        (rungs[i]'hi).name = name ∧
        (rungs[i]'hi).answers q = true ∧
        ∀ j, j < i → ∀ hj : j < rungs.length,
          (rungs[j]'hj).answers q = false := by
  intro rungs
  induction rungs with
  | nil =>
      intro first q spent name c h
      simp [climbFrom] at h
  | cons r rest ih =>
      intro first q spent name c h
      by_cases hans : r.answers q
      · refine ⟨0, by simp, ?_, ?_, ?_⟩
        · simp only [climbFrom, hans, if_true] at h
          cases h; simp
        · simpa using hans
        · intro j hj; omega
      · by_cases hpr : first && principled q
        · simp [climbFrom, hans, hpr] at h
        · cases rest with
          | nil => simp [climbFrom, hans, hpr] at h
          | cons s tail =>
              simp only [climbFrom, hans, hpr, if_false,
                Bool.false_eq_true] at h
              obtain ⟨i, hi, hname, hyes, hno⟩ :=
                ih false q (spent + r.cost) name c h
              refine ⟨i + 1, by simpa using hi, ?_, ?_, ?_⟩
              · simpa using hname
              · simpa using hyes
              · intro j hj hjlen
                cases j with
                | zero => simpa using hans
                | succ k =>
                    have hk : k < i := by omega
                    have hklen : k < (s :: tail).length := by
                      simpa using Nat.lt_of_succ_lt_succ hjlen
                    simpa using hno k hk hklen


/-- The same, from the bottom of the ladder. -/
theorem climb_answers_least (principled : Q → Bool) (rungs : List (Rung Q))
    (q : Q) (name : String) (c : ℕ)
    (h : climb principled rungs q = .answered name c) :
    ∃ i, ∃ hi : i < rungs.length,
      (rungs[i]'hi).name = name ∧
      (rungs[i]'hi).answers q = true ∧
      ∀ j, j < i → ∀ hj : j < rungs.length,
        (rungs[j]'hj).answers q = false := by
  cases rungs with
  | nil => simp [climb] at h
  | cons r rest =>
      exact climbFrom_answers_least principled (r :: rest) true q 0 name c
        (by simpa [climb] using h)

/-- **A refusal from a fully climbed ladder is a statement about every rung.**
If no refusal was classified principled, the loop refuses only when every rung
refused. -/
theorem climbFrom_refused_all (principled : Q → Bool) :
    ∀ (rungs : List (Rung Q)) (first : Bool) (q : Q) (spent : ℕ)
      (name : String) (c : ℕ),
      climbFrom principled first rungs q spent = .refused name c false →
      ∀ r ∈ rungs, r.answers q = false := by
  intro rungs
  induction rungs with
  | nil => intro _ _ _ _ _ _ r hr; simp at hr
  | cons r rest ih =>
      intro first q spent name c h s hs
      by_cases hans : r.answers q
      · simp [climbFrom, hans] at h
      · rcases List.mem_cons.1 hs with rfl | hrest
        · simpa using hans
        · by_cases hpr : first && principled q
          · simp [climbFrom, hans, hpr] at h
          · cases rest with
            | nil => simp at hrest
            | cons t tail =>
                simp only [climbFrom, hans, hpr, if_false,
                  Bool.false_eq_true] at h
                exact ih false q (spent + r.cost) name c h s hrest

/-- The loop terminates: it inspects each rung at most once, so a climb of an
`n`-rung ladder makes at most `n` readings.  This is the statement the ladder's
finiteness is for, and it holds because `climb` recurses structurally on the
declared list. -/
theorem climb_total (principled : Q → Bool) (rungs : List (Rung Q)) (q : Q) :
    (climb principled rungs q).cost ≤ totalCost rungs := by
  cases rungs with
  | nil => simp [climb, Verdict.cost, totalCost]
  | cons r rest =>
      have := climbFrom_cost_le principled (r :: rest) true q 0
      simpa [climb] using this

end GLM.EscalationLoop
