module

public import RequestProject.GLM.Rule30.PlanSearch

/-!
# Round 30: the GLM pipeline — regress, prune, ask, gate

Round 29 (`PlanSearch.lean`) proved what the stepwise planner guarantees.  Round 30 joins the
four follow-up items of that round (To Do 23–26) into one pipeline
(`rule30_round30/glm_overlay/glm_universal/reasoning/glm_pipeline.py` in the study folder): one
search per puzzle, re-read by every stage.  This file states what each stage adds and proves it.

## Stage 1 — fitted middle steps by goal regression (To Do 23)

* `runBack` reads a suffix of steps *backwards* from the goal, given each step's exact preimage
  (`pre a y = some z ↔ step a z = some y`, e.g. a symmetry of the square, or an upscale, whose
  preimage is the downscale when it exists).
* `run_eq_some_iff_runBack`, `run_append_eq_some_iff_runBack` — a plan followed by an invertible
  suffix reaches `y` iff the plan reaches the regressed goal `runBack pre s y`.
* `semMid_eq_some_iff` — so a **fitted middle step** (a finisher fitted from the data, followed by
  an invertible suffix) is fitted exactly by fitting the finisher to the regressed outputs.  This
  is how the pipeline fits e.g. *recolour objects by size, then rotate*.
* `shapePrune_sound` — **pruning by the goal's shape**: if each step has an exact shape map and
  every finisher respects a shape relation `R`, a plan `p ++ [a]` can reproduce a demonstration
  only if `R (σ a (shape of p's state)) (shape of the output)`.  So steps failing this test are
  skipped before they are applied, with no consistent plan lost.

## Stage 2 — the ask loop (To Do 24)

A finite set of surviving hypotheses `S`, each with an answer `ans h q` for every query cell `q`;
asking cell `q` keeps the hypotheses that agree with the truth there (`askFilter`).

* `truth_mem_askFilter` — the truth is never removed;
* `askFilter_card_lt` — if `q` separates two survivors, at least one is removed;
* `askLoop` — ask separating cells until all survivors agree;
  `askLoop_truth_mem`, `askLoop_questions_add_card_le` (questions + survivors ≤ |S|),
  `askLoop_questions_lt` (at most `|S| − 1` questions when the truth is in `S`), and
  `askLoop_correct` — with fuel `|S|`, the loop stops with every survivor giving the true answer.

## Stage 3 — Occam failures and gates (To Do 26)

* `minAgree_wrong_imp` — **every wrong answer of the tiered rule is an Occam failure**: if the
  truth is consistent and the answer is wrong, then the truth is strictly more expensive than the
  answering tier, and a strictly cheaper consistent rival gives the wrong answer (the formal form
  of the Round 29 observation C288).
* `occam_premise_mono` — more demonstrations preserve the Occam premise: if the truth is a
  cheapest consistent hypothesis for some demonstrations, it stays one for any superset it
  reproduces.  So more demonstrations can only remove Occam failures.
* `gated_correct` — an extra gate (e.g. leave-one-out) keeps the rule correct whenever the truth
  passes it; `gate_can_fix` and `gate_can_drop_truth` — a gate can turn a wrong answer into a
  right one, and can also remove the truth and turn a right answer into a wrong one.  Which effect
  wins is an empirical question; the pipeline measures it (`pipeline_bench.py`, section C).

All results use only the standard axioms.
-/

@[expose] public section

namespace GLM.Pipeline

open GLM.PlanSearch

variable {A X Y Θ : Type*}

/-! ## Stage 1: goal regression through an invertible suffix -/

/-- Read a suffix of steps backwards from the goal, using each step's exact preimage. -/
def runBack (pre : A → X → Option X) : List A → X → Option X
  | [], y => some y
  | a :: s, y => (runBack pre s y).bind (pre a)

/-- **Goal regression through an invertible suffix.** -/
theorem run_eq_some_iff_runBack (step : A → X → Option X) (pre : A → X → Option X)
    (hpre : ∀ a z y, step a z = some y ↔ pre a y = some z) (s : List A) (z y : X) :
    run step s z = some y ↔ runBack pre s y = some z := by
  induction s generalizing z with
  | nil => simp [runBack, eq_comm]
  | cons a s ih =>
    simp only [run_cons, runBack]
    constructor
    · intro h
      obtain ⟨z1, hz1, hrest⟩ := Option.bind_eq_some_iff.1 h
      rw [(ih z1).1 hrest, Option.bind_some]
      exact (hpre a z z1).1 hz1
    · intro h
      obtain ⟨z1, hz1, hpz⟩ := Option.bind_eq_some_iff.1 h
      rw [(hpre a z z1).2 hpz, Option.bind_some]
      exact (ih z1).2 hz1

/-- A plan followed by an invertible suffix reaches `y` iff the plan reaches the regressed goal. -/
theorem run_append_eq_some_iff_runBack (step : A → X → Option X) (pre : A → X → Option X)
    (hpre : ∀ a z y, step a z = some y ↔ pre a y = some z) (p s : List A) (x y : X) :
    run step (p ++ s) x = some y ↔ ∃ z, run step p x = some z ∧ runBack pre s y = some z := by
  rw [run_append]
  constructor
  · intro h
    obtain ⟨z, hz, hs⟩ := Option.bind_eq_some_iff.1 h
    exact ⟨z, hz, (run_eq_some_iff_runBack step pre hpre s z y).1 hs⟩
  · rintro ⟨z, hz, hs⟩
    rw [hz, Option.bind_some]
    exact (run_eq_some_iff_runBack step pre hpre s z y).2 hs

/-- A hypothesis with a **fitted middle step**: a plan `p`, a finisher with fitted parameter `θ`
(mapping states to states), then a fixed suffix `s`. -/
def semMid (step : A → X → Option X) (fin : Θ → X → Option X) (p : List A) (θ : Θ)
    (s : List A) (x : X) : Option X :=
  ((run step p x).bind (fin θ)).bind (run step s)

/-- **Fitting a middle step is fitting the finisher to the regressed outputs.** -/
theorem semMid_eq_some_iff (step : A → X → Option X) (pre : A → X → Option X)
    (hpre : ∀ a z y, step a z = some y ↔ pre a y = some z) (fin : Θ → X → Option X)
    (p : List A) (θ : Θ) (s : List A) (x y : X) :
    semMid step fin p θ s x = some y ↔
      ∃ z, (run step p x).bind (fin θ) = some z ∧ runBack pre s y = some z := by
  unfold semMid
  constructor
  · intro h
    obtain ⟨z, hz, hs⟩ := Option.bind_eq_some_iff.1 h
    exact ⟨z, hz, (run_eq_some_iff_runBack step pre hpre s z y).1 hs⟩
  · rintro ⟨z, hz, hs⟩
    rw [hz, Option.bind_some]
    exact (run_eq_some_iff_runBack step pre hpre s z y).2 hs

/-- **Pruning by the goal's shape is sound.**  Let `α` read the shape of a state and `β` the shape
of an output, let each step have an exact shape map `σ` (`step a x = some y → α y = σ a (α x)`),
and let every finisher respect a shape relation `R`.  If the plan `p ++ [a]` with any finisher
reproduces a demonstration `(x, y)`, then `R (σ a (α m)) (β y)` for the state `m` that `p` reaches.
So a step for which this fails on some demonstration can be skipped *before it is applied*. -/
theorem shapePrune_sound {S S' : Type*} {step : A → X → Option X} {fin : Θ → X → Option Y}
    (α : X → S) (β : Y → S') (σ : A → S → S) (R : S → S' → Prop)
    (hσ : ∀ a x y, step a x = some y → α y = σ a (α x))
    (hR : ∀ θ m y, fin θ m = some y → R (α m) (β y))
    {p : List A} {a : A} {θ : Θ} {x : X} {y : Y}
    (hcons : sem step fin (p ++ [a], θ) x = some y) :
    ∃ m, run step p x = some m ∧ R (σ a (α m)) (β y) := by
  unfold sem at hcons
  obtain ⟨z, hz, hfin⟩ := Option.bind_eq_some_iff.1 hcons
  obtain ⟨m, hm, ha⟩ := (run_concat_eq_some step p a x z).1 hz
  refine ⟨m, hm, ?_⟩
  rw [← hσ a m z ha]
  exact hR θ z y hfin

/-- The pruning rule in the form the pipeline uses: a step whose predicted shape fails the goal
relation on one demonstration leaves no consistent hypothesis `p ++ [a]`. -/
theorem shapePrune_skip {S S' : Type*} {step : A → X → Option X} {fin : Θ → X → Option Y}
    (α : X → S) (β : Y → S') (σ : A → S → S) (R : S → S' → Prop)
    (hσ : ∀ a x y, step a x = some y → α y = σ a (α x))
    (hR : ∀ θ m y, fin θ m = some y → R (α m) (β y))
    {demos : List (X × Y)} {p : List A} {a : A} {d : X × Y} (hd : d ∈ demos)
    (hbad : ∀ m, run step p d.1 = some m → ¬ R (σ a (α m)) (β d.2)) (θ : Θ) :
    ¬ Consistent step fin demos (p ++ [a], θ) := by
  intro hc
  obtain ⟨m, hm, hR'⟩ := shapePrune_sound α β σ R hσ hR (hc d hd)
  exact hbad m hm hR'

/-! ## Stage 2: the ask loop -/

section Ask

variable {H Q V : Type*} [DecidableEq V]

/-- Ask cell `q`: keep the hypotheses that agree with the true answer there. -/
def askFilter (ans : H → Q → V) (truth : Q → V) (S : Finset H) (q : Q) : Finset H :=
  S.filter fun h => ans h q = truth q

theorem askFilter_subset (ans : H → Q → V) (truth : Q → V) (S : Finset H) (q : Q) :
    askFilter ans truth S q ⊆ S :=
  Finset.filter_subset _ _

/-- **The truth is never removed by a question.** -/
theorem truth_mem_askFilter {ans : H → Q → V} {S : Finset H} {hstar : H} (hm : hstar ∈ S)
    (q : Q) : hstar ∈ askFilter ans (ans hstar) S q :=
  Finset.mem_filter.2 ⟨hm, rfl⟩

/-- **A separating question removes at least one hypothesis**, whatever the true answer. -/
theorem askFilter_card_lt {ans : H → Q → V} {truth : Q → V} {S : Finset H} {q : Q}
    {h₁ h₂ : H} (h₁S : h₁ ∈ S) (h₂S : h₂ ∈ S) (hne : ans h₁ q ≠ ans h₂ q) :
    (askFilter ans truth S q).card < S.card := by
  apply Finset.card_lt_card
  refine ⟨askFilter_subset ans truth S q, fun hsub => ?_⟩
  by_cases e : ans h₁ q = truth q
  · have : h₂ ∈ askFilter ans truth S q := hsub h₂S
    exact hne (e.trans (Finset.mem_filter.1 this).2.symm)
  · exact e (Finset.mem_filter.1 (hsub h₁S)).2

/-- The ask loop with fuel `n`: while the question rule `sep` names a cell, ask it.  Returns the
survivors and the number of questions asked. -/
def askLoop (ans : H → Q → V) (truth : Q → V) (sep : Finset H → Option Q) :
    ℕ → Finset H → Finset H × ℕ
  | 0, S => (S, 0)
  | n + 1, S =>
    match sep S with
    | none => (S, 0)
    | some q =>
      let r := askLoop ans truth sep n (askFilter ans truth S q)
      (r.1, r.2 + 1)

variable {ans : H → Q → V} {sep : Finset H → Option Q}

/-- A **separating question rule**: a named cell separates two survivors, and no cell is named
only when all survivors agree on every cell. -/
structure SepRule (ans : H → Q → V) (sep : Finset H → Option Q) : Prop where
  some_sep : ∀ S q, sep S = some q → ∃ h₁ ∈ S, ∃ h₂ ∈ S, ans h₁ q ≠ ans h₂ q
  none_agree : ∀ S, sep S = none → ∀ h₁ ∈ S, ∀ h₂ ∈ S, ans h₁ = ans h₂

theorem askLoop_subset (truth : Q → V) (n : ℕ) (S : Finset H) :
    (askLoop ans truth sep n S).1 ⊆ S := by
  induction n generalizing S with
  | zero => exact subset_rfl
  | succ n ih =>
    simp only [askLoop]
    cases sep S with
    | none => exact subset_rfl
    | some q => exact (ih _).trans (askFilter_subset ans truth S q)

/-- **The truth survives the whole loop.** -/
theorem askLoop_truth_mem {hstar : H} (n : ℕ) {S : Finset H} (hm : hstar ∈ S) :
    hstar ∈ (askLoop ans (ans hstar) sep n S).1 := by
  induction n generalizing S with
  | zero => exact hm
  | succ n ih =>
    simp only [askLoop]
    cases sep S with
    | none => exact hm
    | some q => exact ih (truth_mem_askFilter hm q)

/-- **Every question removes a hypothesis**: questions asked plus survivors is at most `|S|`. -/
theorem askLoop_questions_add_card_le (hs : SepRule ans sep) (truth : Q → V) (n : ℕ)
    (S : Finset H) :
    (askLoop ans truth sep n S).2 + (askLoop ans truth sep n S).1.card ≤ S.card := by
  induction n generalizing S with
  | zero => simp [askLoop]
  | succ n ih =>
    simp only [askLoop]
    cases hq : sep S with
    | none => simp
    | some q =>
      obtain ⟨h₁, h₁S, h₂, h₂S, hne⟩ := hs.some_sep S q hq
      have hlt := askFilter_card_lt (truth := truth) h₁S h₂S hne
      have := ih (askFilter ans truth S q)
      simp only
      omega

/-- **At most `|S| − 1` questions** when the truth is among the hypotheses. -/
theorem askLoop_questions_lt (hs : SepRule ans sep) {hstar : H} (n : ℕ) {S : Finset H}
    (hm : hstar ∈ S) : (askLoop ans (ans hstar) sep n S).2 < S.card := by
  have h1 := askLoop_questions_add_card_le hs (ans hstar) n S
  have h2 : 0 < (askLoop ans (ans hstar) sep n S).1.card :=
    Finset.card_pos.2 ⟨hstar, askLoop_truth_mem n hm⟩
  omega

/-- If the loop asked fewer questions than its fuel, it stopped because no cell separates the
survivors. -/
theorem askLoop_stopped (truth : Q → V) (n : ℕ) (S : Finset H)
    (h : (askLoop ans truth sep n S).2 < n) : sep (askLoop ans truth sep n S).1 = none := by
  induction n generalizing S with
  | zero => omega
  | succ n ih =>
    simp only [askLoop] at h ⊢
    cases hq : sep S with
    | none => simp [hq]
    | some q =>
      simp only [hq] at h ⊢
      exact ih _ (by omega)

/-- **The ask loop is correct.**  With a separating question rule, fuel at least `|S|`, and the
truth among the hypotheses, the loop stops with every survivor giving the true answer on every
cell, after at most `|S| − 1` questions. -/
theorem askLoop_correct (hs : SepRule ans sep) {hstar : H} {n : ℕ} {S : Finset H}
    (hm : hstar ∈ S) (hn : S.card ≤ n) :
    (∀ h ∈ (askLoop ans (ans hstar) sep n S).1, ans h = ans hstar) ∧
      (askLoop ans (ans hstar) sep n S).2 < S.card := by
  have hq := askLoop_questions_lt hs n hm
  have hstop := askLoop_stopped (ans := ans) (sep := sep) (ans hstar) n S (by omega)
  exact ⟨fun h hh => hs.none_agree _ hstop h hh hstar (askLoop_truth_mem n hm), hq⟩

end Ask

/-! ## Stage 3: Occam failures and gates -/

section Occam

variable {H : Type*} {cost : H → ℕ} {Cons : H → Prop} {ans : H → Option Y}

/-- **Every wrong answer is an Occam failure.**  If the truth reproduces the demonstrations and
the tiered rule answers `a` but the truth does not, then the truth is strictly more expensive than
the answering tier, and a strictly cheaper consistent hypothesis gives the answer `a`. -/
theorem minAgree_wrong_imp {t : ℕ} {a : Y} (hM : MinAgree cost Cons ans t a) {htrue : H}
    (hc : Cons htrue) (hwrong : ans htrue ≠ some a) :
    t < cost htrue ∧ ∃ h, Cons h ∧ cost h < cost htrue ∧ ans h = some a := by
  obtain ⟨hmin, ⟨h, hch, hct⟩, hall⟩ := hM
  have hne : cost htrue ≠ t := fun e => hwrong (hall htrue hc e)
  have hlt : t < cost htrue := lt_of_le_of_ne (hmin htrue hc) (Ne.symm hne)
  exact ⟨hlt, h, hch, hct ▸ hlt, hall h hch hct⟩

/-- **More demonstrations preserve the Occam premise.**  If the truth is no more expensive than
any hypothesis consistent with `demos`, the same holds for any larger set `demos'` (whose
consistent hypotheses are among those of `demos`). -/
theorem occam_premise_mono {A' X' : Type*} {step : A' → X' → Option X'}
    {fin : Θ → X' → Option Y} {demos demos' : List (X' × Y)} (hsub : demos ⊆ demos')
    {cst : List A' × Θ → ℕ} {htrue : List A' × Θ}
    (hocc : ∀ h, Consistent step fin demos h → cst htrue ≤ cst h) :
    ∀ h, Consistent step fin demos' h → cst htrue ≤ cst h :=
  fun h hh => hocc h (consistent_antitone hsub hh)

/-- **A gate is harmless when the truth passes it**: the tiered rule over the gated hypotheses
is correct whenever the truth is consistent, passes the gate, and is a cheapest gated hypothesis. -/
theorem gated_correct {gate : H → Prop} {t : ℕ} {a : Y}
    (hM : MinAgree cost (fun h => Cons h ∧ gate h) ans t a) {htrue : H} (hc : Cons htrue)
    (hg : gate htrue) (hcost : cost htrue = t) : ans htrue = some a :=
  minAgree_correct hM ⟨hc, hg⟩ hcost

/-- **A gate can fix an Occam failure.**  Two consistent hypotheses (`false` cheap, `true` the
truth); without the gate the cheap one answers `0`, wrongly; the gate removes it and the rule
answers `1`, rightly. -/
theorem gate_can_fix :
    MinAgree (fun b : Bool => if b then 1 else 0) (fun _ => True)
      (fun b => some (if b then 1 else 0)) 0 (0 : ℕ) ∧
    MinAgree (fun b : Bool => if b then 1 else 0) (fun b => True ∧ b = true)
      (fun b => some (if b then 1 else 0)) 1 (1 : ℕ) := by
  refine ⟨⟨fun _ _ => Nat.zero_le _, ⟨false, trivial, rfl⟩, ?_⟩,
    ⟨?_, ⟨true, ⟨trivial, rfl⟩, rfl⟩, ?_⟩⟩
  · intro h _ hc
    cases h <;> simp_all
  · rintro h ⟨_, rfl⟩
    simp
  · rintro h ⟨_, rfl⟩ _
    simp

/-- **A gate can drop the truth.**  Two consistent hypotheses (`false` the truth and cheapest,
`true` costlier); without the gate the rule answers `0`, rightly; a gate that rejects the truth
leaves the costlier one, and the rule answers `1`, wrongly. -/
theorem gate_can_drop_truth :
    MinAgree (fun b : Bool => if b then 1 else 0) (fun _ => True)
      (fun b => some (if b then 1 else 0)) 0 (0 : ℕ) ∧
    MinAgree (fun b : Bool => if b then 1 else 0) (fun b => True ∧ b = true)
      (fun b => some (if b then 1 else 0)) 1 (1 : ℕ) ∧
    (fun b : Bool => some (if b then 1 else 0)) false ≠ some (1 : ℕ) :=
  ⟨gate_can_fix.1, gate_can_fix.2, by simp⟩

end Occam

end GLM.Pipeline
