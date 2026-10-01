module

public import Mathlib

/-!
# The stepwise planner: a chain of steps, and when it may answer

The typed planner answers one question with one plan.  The stepwise planner
(`glm_universal.runtime.stepwise`, Phase 72,
`studies/STEPWISE_PLANNER_STUDY.md`) makes it the executive of a *chain*:
compound questions are read into readings whose steps the planner answers one
at a time, and goal questions over the formula wheels are answered by
derivations whose intermediate steps nobody asked for (*stitched*).  This file
proves the facts the module's refusals and answers rest on.

* **A derivation is sound** (`eval_eq_model`): a tree of rule steps from the
  givens evaluates to the value of the target in every model that satisfies
  the rules and agrees with the givens.  So two derivations of one quantity
  that disagree leave **no model at all** (`disagreement_refutes_model`), and
  neither does a given that the other givens re-derive with another value
  (`rederived_given_refutes_model`).  That is why the module refuses
  `DERIVATIONS_DISAGREE` and `INCONSISTENT_GIVENS` rather than choosing one.
* **Solving an axiom for a variable of power one is exact**
  (`solve_power_one`, `solve_power_neg_one`), through non-zero values.
* **Bracketings.**  Every bracketing of a sum agrees with the sum of its
  leaves (`bracketing_sum`), so *a plus b plus c* is answered although it has
  two readings (`sum_bracketings_agree`); subtraction's bracketings do not
  agree (`sub_bracketings_disagree`), nor do *2 times c plus o*'s two readings
  (`times_plus_readings_disagree`), and the module refuses both as ambiguous.
* **Agreement is order-free** (`agreed_perm`, `agreed_eq_some_iff`): the
  answer over readings is a value every licensed reading gives, whatever
  order the readings were tried in.
* **The step gate** (`checked_iff_recomputed`): a chain passes every local
  step check exactly when its claimed values are the values recomputed from
  scratch, so one lie anywhere in the chain fails some step's check.
* **The fallback is conservative** (`fallback_conservative`,
  `fallback_sound`): consulted only when the planner refused, the stepwise
  layer never changes an answer the planner gave.
-/

namespace GLM.StepwisePlanner

/-! ## Derivations -/

/-- A rule: an axiom solved for one quantity, `out = f (values of ins)`. -/
public structure Rule (X : Type) where
  /-- How many quantities the rule reads. -/
  arity : ℕ
  /-- The quantity it gives. -/
  out : X
  /-- The quantities it reads. -/
  ins : Fin arity → X
  /-- How it computes. -/
  f : (Fin arity → ℚ) → ℚ

/-- A derivation: a given, or a rule applied to derivations of its inputs. -/
public inductive Tree (X : Type) where
  /-- A given quantity. -/
  | given : X → Tree X
  /-- A rule step, one sub-derivation per input. -/
  | step : (r : Rule X) → (Fin r.arity → Tree X) → Tree X

namespace Tree

variable {X : Type}

/-- The quantity a derivation derives. -/
public def root : Tree X → X
  | given x => x
  | step r _ => r.out

/-- The value a derivation computes from the values of the givens. -/
public def eval (g : X → ℚ) : Tree X → ℚ
  | given x => g x
  | step r k => r.f (fun i => eval g (k i))

/-- A derivation is admissible over rules `R` and givens `G` when every
leaf is a given, every step is a rule of `R`, and every sub-derivation
derives the input it is plugged into. -/
public def Admissible (R : Set (Rule X)) (G : Set X) : Tree X → Prop
  | given x => x ∈ G
  | step r k => r ∈ R ∧ ∀ i, (k i).root = r.ins i ∧ Admissible R G (k i)

end Tree

open Tree

variable {X : Type}

/-- A model satisfies a rule when the rule's output is the rule applied to
the model's values of its inputs. -/
public def Satisfies (m : X → ℚ) (r : Rule X) : Prop :=
  m r.out = r.f (fun i => m (r.ins i))

/-- A model of rules `R` and givens `G` with values `g`. -/
@[expose] public def IsModel (R : Set (Rule X)) (G : Set X) (g : X → ℚ) (m : X → ℚ) :
    Prop :=
  (∀ r ∈ R, Satisfies m r) ∧ ∀ x ∈ G, m x = g x

/-- **Soundness of a derivation.**  An admissible derivation evaluates to
the model's value of what it derives, in every model. -/
public theorem eval_eq_model {R : Set (Rule X)} {G : Set X} {g m : X → ℚ}
    (hm : IsModel R G g m) :
    ∀ t : Tree X, t.Admissible R G → t.eval g = m t.root := by
  intro t
  induction t with
  | given x =>
      intro h
      exact (hm.2 x h).symm
  | step r k ih =>
      rintro ⟨hr, hk⟩
      have hs := hm.1 r hr
      simp only [Tree.eval, Tree.root]
      rw [hs]
      congr 1
      funext i
      rw [ih i (hk i).2, (hk i).1]

/-- Two admissible derivations of one quantity agree whenever a model
exists. -/
public theorem derivations_agree {R : Set (Rule X)} {G : Set X}
    {g m : X → ℚ} (hm : IsModel R G g m) {t₁ t₂ : Tree X}
    (h₁ : t₁.Admissible R G) (h₂ : t₂.Admissible R G)
    (hroot : t₁.root = t₂.root) : t₁.eval g = t₂.eval g := by
  rw [eval_eq_model hm t₁ h₁, eval_eq_model hm t₂ h₂, hroot]

/-- **Two derivations that disagree leave no model**: the givens are
inconsistent with the rules, so no value of the target is right, and the
refusal `DERIVATIONS_DISAGREE` is the only honest verdict. -/
public theorem disagreement_refutes_model {R : Set (Rule X)} {G : Set X}
    {g : X → ℚ} {t₁ t₂ : Tree X} (h₁ : t₁.Admissible R G)
    (h₂ : t₂.Admissible R G) (hroot : t₁.root = t₂.root)
    (hne : t₁.eval g ≠ t₂.eval g) : ¬ ∃ m, IsModel R G g m := by
  rintro ⟨m, hm⟩
  exact hne (derivations_agree hm h₁ h₂ hroot)

/-- **A given re-derived with another value leaves no model**: the refusal
`INCONSISTENT_GIVENS`. -/
public theorem rederived_given_refutes_model {R : Set (Rule X)} {G : Set X}
    {g : X → ℚ} {x : X} (hx : x ∈ G) {t : Tree X} (ht : t.Admissible R G)
    (hroot : t.root = x) (hne : t.eval g ≠ g x) : ¬ ∃ m, IsModel R G g m := by
  rintro ⟨m, hm⟩
  apply hne
  rw [eval_eq_model hm t ht, hroot, hm.2 x hx]

/-! ## Solving an axiom for one variable -/

/-- An axiom `x · rest = K` with `rest ≠ 0` gives `x = K / rest`. -/
public theorem solve_power_one {x rest K : ℚ} (h : rest ≠ 0) :
    x * rest = K ↔ x = K / rest := by
  constructor
  · intro hx
    rw [← hx, mul_div_cancel_right₀ _ h]
  · intro hx
    rw [hx, div_mul_cancel₀ _ h]

/-- An axiom `x⁻¹ · rest = K` with `rest ≠ 0` and `K ≠ 0` gives
`x = rest / K`. -/
public theorem solve_power_neg_one {x rest K : ℚ} (h : rest ≠ 0)
    (hK : K ≠ 0) : x⁻¹ * rest = K ↔ x = rest / K := by
  constructor
  · intro hx
    have hx0 : x ≠ 0 := by
      rintro rfl
      simp at hx
      exact hK hx.symm
    rw [← hx]
    field_simp
  · intro hx
    rw [hx]
    field_simp

/-! ## Bracketings of a compound question -/

/-- A bracketing: leaves and binary nodes. -/
public inductive Bracketing where
  /-- A value. -/
  | leaf : ℚ → Bracketing
  /-- Two bracketed parts. -/
  | node : Bracketing → Bracketing → Bracketing

namespace Bracketing

/-- The leaves, left to right. -/
public def frontier : Bracketing → List ℚ
  | leaf q => [q]
  | node a b => a.frontier ++ b.frontier

/-- The value with one operation at every node. -/
public def evalWith (op : ℚ → ℚ → ℚ) : Bracketing → ℚ
  | leaf q => q
  | node a b => op (a.evalWith op) (b.evalWith op)

end Bracketing

/-- Every bracketing of a sum is the sum of its leaves. -/
public theorem bracketing_sum (t : Bracketing) :
    t.evalWith (· + ·) = t.frontier.sum := by
  induction t with
  | leaf q => simp [Bracketing.evalWith, Bracketing.frontier]
  | node a b iha ihb =>
      simp [Bracketing.evalWith, Bracketing.frontier, iha, ihb,
        List.sum_append]

/-- Every bracketing of a product is the product of its leaves. -/
public theorem bracketing_prod (t : Bracketing) :
    t.evalWith (· * ·) = t.frontier.prod := by
  induction t with
  | leaf q => simp [Bracketing.evalWith, Bracketing.frontier]
  | node a b iha ihb =>
      simp [Bracketing.evalWith, Bracketing.frontier, iha, ihb,
        List.prod_append]

/-- **Two readings of a sum always agree**: *a plus b plus c* is answered
although it has two bracketings. -/
public theorem sum_bracketings_agree {t₁ t₂ : Bracketing}
    (h : t₁.frontier = t₂.frontier) :
    t₁.evalWith (· + ·) = t₂.evalWith (· + ·) := by
  rw [bracketing_sum, bracketing_sum, h]

/-- The same for products. -/
public theorem prod_bracketings_agree {t₁ t₂ : Bracketing}
    (h : t₁.frontier = t₂.frontier) :
    t₁.evalWith (· * ·) = t₂.evalWith (· * ·) := by
  rw [bracketing_prod, bracketing_prod, h]

/-- Subtraction's bracketings do not agree: case `c20`, the atomic numbers
of gold, copper and carbon, `(79 − 29) − 6 = 44` against
`79 − (29 − 6) = 56`. -/
public theorem sub_bracketings_disagree :
    (Bracketing.node (.node (.leaf 79) (.leaf 29)) (.leaf 6)).evalWith
        (· - ·) ≠
      (Bracketing.node (.leaf 79) (.node (.leaf 29) (.leaf 6))).evalWith
        (· - ·) := by
  simp [Bracketing.evalWith]
  norm_num

/-- *2 times the atomic number of carbon plus the atomic number of oxygen*
(case `c11`): its two readings give 20 and 28. -/
public theorem times_plus_readings_disagree :
    (2 * 6 + 8 : ℚ) ≠ 2 * (6 + 8) := by norm_num

/-! ## Agreement over readings -/

/-- The answer over the licensed readings' values: the value, when they
all give one; otherwise none (ambiguous, or nothing licensed). -/
public def agreed {V : Type} [DecidableEq V] (vs : List V) : Option V :=
  match vs.dedup with
  | [v] => some v
  | _ => none

/-- Agreement does not depend on the order the readings were tried in. -/
public theorem agreed_perm {V : Type} [DecidableEq V] {vs ws : List V}
    (h : vs.Perm ws) : agreed vs = agreed ws := by
  unfold agreed
  have hd := h.dedup
  rcases hvs : vs.dedup with _ | ⟨a, _ | ⟨b, l⟩⟩ <;>
    rcases hws : ws.dedup with _ | ⟨c, _ | ⟨d, l'⟩⟩ <;>
    rw [hvs, hws] at hd <;> simp_all [List.perm_singleton]

/-- An agreed answer is a value every licensed reading gives. -/
public theorem agreed_eq_some_iff {V : Type} [DecidableEq V] (vs : List V)
    (v : V) : agreed vs = some v ↔ vs ≠ [] ∧ ∀ w ∈ vs, w = v := by
  unfold agreed
  constructor
  · intro h
    split at h
    · rename_i v' hv
      cases h
      refine ⟨?_, ?_⟩
      · rintro rfl
        simp at hv
      · intro w hw
        have : w ∈ vs.dedup := List.mem_dedup.mpr hw
        rw [hv] at this
        simpa using this
    · cases h
  · rintro ⟨hne, hall⟩
    have hsub : vs.dedup = [v] := by
      obtain ⟨w, hw⟩ := List.exists_mem_of_ne_nil vs hne
      have hv : v ∈ vs := by simpa [hall w hw] using hw
      have hnd := List.nodup_dedup vs
      have hmem : ∀ x ∈ vs.dedup, x = v := fun x hx =>
        hall x (List.mem_dedup.mp hx)
      have hvd : v ∈ vs.dedup := List.mem_dedup.mpr hv
      rcases hd : vs.dedup with _ | ⟨a, _ | ⟨b, l⟩⟩
      · simp [hd] at hvd
      · have := hmem a (by simp [hd]); simp [this]
      · have ha := hmem a (by simp [hd])
        have hb := hmem b (by simp [hd])
        rw [hd] at hnd
        simp [ha, hb] at hnd
    rw [hsub]

/-! ## The step gate -/

/-- One recorded step: how it computes from earlier values, which earlier
steps it reads, and the value it claims. -/
public structure CStep where
  /-- The computation, from the values it reads. -/
  f : List ℚ → ℚ
  /-- The positions of the earlier steps it reads. -/
  ins : List ℕ
  /-- The value the step claims. -/
  val : ℚ

/-- What a step computes from the values before it. -/
public def CStep.compute (s : CStep) (prev : List ℚ) : ℚ :=
  s.f (s.ins.map fun j => prev.getD j 0)

/-- Every step's claim checked against the claims before it. -/
public def checked : List ℚ → List CStep → Prop
  | _, [] => True
  | acc, s :: ss => s.val = s.compute acc ∧ checked (acc ++ [s.val]) ss

/-- Every value recomputed from scratch, ignoring the claims. -/
public def recompute : List ℚ → List CStep → List ℚ
  | acc, [] => acc
  | acc, s :: ss => recompute (acc ++ [s.compute acc]) ss

private lemma prefix_recompute (acc : List ℚ) (ss : List CStep) :
    acc <+: recompute acc ss := by
  induction ss generalizing acc with
  | nil => exact List.prefix_refl _
  | cons s ss ih =>
      exact (List.prefix_append acc _).trans (ih _)

/-- **The step gate.**  A chain passes every local step check exactly when
its claimed values are the values recomputed from scratch: one lie anywhere
fails some step's check. -/
public theorem checked_iff_recomputed (acc : List ℚ) (ss : List CStep) :
    checked acc ss ↔ recompute acc ss = acc ++ ss.map CStep.val := by
  induction ss generalizing acc with
  | nil => simp [checked, recompute]
  | cons s ss ih =>
      simp only [checked, recompute, List.map_cons]
      constructor
      · rintro ⟨hs, hrest⟩
        rw [← hs, (ih _).mp hrest]
        simp
      · intro h
        have hp := prefix_recompute (acc ++ [s.compute acc]) ss
        rw [h] at hp
        have hx : s.compute acc = s.val := by
          rw [List.prefix_append_right_inj, List.cons_prefix_cons] at hp
          exact hp.1
        refine ⟨hx.symm, (ih _).mpr ?_⟩
        rw [hx] at h
        simpa using h

/-! ## The fallback -/

/-- The router's rule: the planner's answer when it gave one, the stepwise
layer's otherwise. -/
public def fallback {V : Type} (planner stepwise : Option V) : Option V :=
  match planner with
  | some v => some v
  | none => stepwise

/-- **Conservative**: an answer the planner gave is never changed. -/
public theorem fallback_conservative {V : Type} {planner : Option V} {v : V}
    (stepwise : Option V) (h : planner = some v) :
    fallback planner stepwise = some v := by
  subst h; rfl

/-- **Sound**: every answer is the planner's, or the stepwise layer's on a
question the planner refused. -/
public theorem fallback_sound {V : Type} {planner stepwise : Option V}
    {v : V} (h : fallback planner stepwise = some v) :
    planner = some v ∨ (planner = none ∧ stepwise = some v) := by
  cases planner with
  | some w => left; simpa [fallback] using h
  | none => right; exact ⟨rfl, by simpa [fallback] using h⟩

end GLM.StepwisePlanner
