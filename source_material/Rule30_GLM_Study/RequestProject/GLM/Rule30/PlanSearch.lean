module

public import Mathlib

/-!
# Round 29: multi-step plans — the stepwise planner for puzzles, made exact

Round 28 (`LocalRuleInduction.lean`) proved the GLM's *one-step* induction discipline: keep every
rule that reproduces the demonstrations, answer only when all of them agree.  Most puzzles are not
one step.  A typical ARC task is *crop the object, then mirror it, then recolour it*.  The GLM
already has a planner of this shape for text questions (`stepwise.py`: a chain is licensed when
every step is, and the answer is given only when every licensed reading agrees) and a search loop
for candidate programs (`search_loop.py`: the hard gate D1 and the Occam rule C5).  This file
states the *planner over chains of grid steps* and proves what it guarantees, so that the GLM-side
implementation (`rule30_round29/glm_glm_universal/reasoning/grid_planner.py`) can be
checked against exact statements.

## The setting

* `X` — the states (grids); `step : A → X → Option X` — what each step of the alphabet `A` does
  (a step may fail, e.g. *crop to the object* on an empty grid);
* a **plan** is a list of steps, run left to right (`run`);
* a **finisher** `fin : Θ → X → Option Y` is a final step whose parameter `θ` is *fitted* from the
  data (a colour map, or a local rule from `LocalRuleInduction.lean`); a **hypothesis** is a plan
  together with a finisher parameter (`sem`).

## Results (all `FORMAL`, standard axioms only)

* `run_append`, `run_concat_eq_some` — chains compose; the last step can be *regressed*: a plan
  `p ++ [a]` reaches `y` from `x` iff `p` reaches some `z` with `step a z = some y` (the backward,
  goal-directed reading of a chain).
* `agree_correct` — the **agreement rule** is sound: if the true hypothesis is among those searched
  and every searched hypothesis that reproduces the demonstrations gives answer `a`, the true
  answer is `a`.
* `consistent_antitone`, `inconsistent_mono` — more demonstrations only remove hypotheses
  (refutation is permanent).
* `separating_example_refutes` — when two hypotheses disagree on the query, the query's true
  output, given as one more demonstration, refutes at least one of them (so "ask for the
  separating example" always makes progress; To Do 21).
* `sig_append_congr`, `consistent_congr`, `sem_congr` — two plans with the same **signature**
  (the intermediate states on every probe input: the demonstration inputs *and* the queries) are
  interchangeable in every continuation.  This is what licenses merging them during the search.
* `dedup_sub`, `dedup_rep` — the merge step keeps one plan per signature and loses none.
* `layer_sound`, `layer_complete` — the breadth-first planner with merging (`layer`) only produces
  plans of the right length over the alphabet, and **every** plan of length `n` has a
  representative of the same signature in layer `n`.
* `exists_consistent_iff_layer`, `agree_iff_layer` — consistency and agreement can be decided on
  the merged layer instead of on all `|A|^n` plans: nothing is lost.
* `planner_minimal`, `planner_agree_all`, `planner_correct` — the planner (first depth with a
  consistent plan; answer only if every consistent plan there agrees) never answers at a depth
  above the shortest consistent explanation, every consistent plan of that depth agrees with its
  answer, and the answer is correct whenever the true transformation is a shortest explanation
  (the Occam premise, rule C5 of the archive's search loop).
* `minAgree_correct`, `minAgree_unique`, `minAgree_needs_occam` — the same rule over any cost
  order (the implementation orders hypotheses by plan length, then finisher rank, then the steps'
  Occam weight): correct when the truth is a cheapest consistent hypothesis, unique, and *not*
  correct without that premise (a two-hypothesis witness).  Extra gates such as leave-one-out
  only shrink the consistent set, so `agree_correct` still applies whenever the truth passes them.
* `train_only_signature_unsound` — a **negative control**: merging plans by their states on the
  demonstration inputs alone (forgetting the queries) is unsound; a concrete instance shows the
  merged layer agreeing on an answer that the full layer does not determine.
-/

@[expose] public section

namespace GLM.PlanSearch

variable {A X Y Θ : Type*}

/-! ## Plans and hypotheses -/

/-- Run a plan: apply its steps left to right; a failing step makes the whole plan fail. -/
def run (step : A → X → Option X) : List A → X → Option X
  | [], x => some x
  | a :: p, x => (step a x).bind (run step p)

variable (step : A → X → Option X)

@[simp] theorem run_nil (x : X) : run step [] x = some x := rfl

@[simp] theorem run_cons (a : A) (p : List A) (x : X) :
    run step (a :: p) x = (step a x).bind (run step p) := rfl

/-- **Chains compose.** -/
theorem run_append (p q : List A) (x : X) :
    run step (p ++ q) x = (run step p x).bind (run step q) := by
  induction p generalizing x with
  | nil => simp
  | cons a p ih =>
    simp only [List.cons_append, run_cons]
    cases step a x with
    | none => simp
    | some z => simp [ih]

/-- **Goal regression.** The last step of a chain can be read backwards: `p ++ [a]` reaches `y`
from `x` iff `p` reaches an intermediate `z` from which `a` reaches `y`. -/
theorem run_concat_eq_some (p : List A) (a : A) (x y : X) :
    run step (p ++ [a]) x = some y ↔ ∃ z, run step p x = some z ∧ step a z = some y := by
  rw [run_append]
  cases h : run step p x with
  | none => simp
  | some z =>
    simp only [Option.bind_some, run_cons, run_nil]
    constructor
    · intro hy
      refine ⟨z, rfl, ?_⟩
      cases hz : step a z <;> simp_all
    · rintro ⟨z', hz', hy⟩
      cases hz'
      simp [hy]

variable (fin : Θ → X → Option Y)

/-- A hypothesis is a plan followed by a fitted finisher; its prediction on input `x`. -/
def sem (h : List A × Θ) (x : X) : Option Y := (run step h.1 x).bind (fin h.2)

/-- A hypothesis reproduces every demonstration exactly (the hard gate D1). -/
def Consistent (demos : List (X × Y)) (h : List A × Θ) : Prop :=
  ∀ d ∈ demos, sem step fin h d.1 = some d.2

variable {step fin}

/-- **The agreement rule is sound.** If the true hypothesis is among the searched ones, reproduces
the demonstrations, and every searched hypothesis that reproduces them answers `a` on the query,
then the true answer is `a`. -/
theorem agree_correct {S : Set (List A × Θ)} {demos : List (X × Y)} {htrue : List A × Θ}
    (hmem : htrue ∈ S) (hcons : Consistent step fin demos htrue) {q : X} {a : Y}
    (hagree : ∀ h ∈ S, Consistent step fin demos h → sem step fin h q = some a) :
    sem step fin htrue q = some a :=
  hagree htrue hmem hcons

/-- More demonstrations only remove consistent hypotheses. -/
theorem consistent_antitone {demos demos' : List (X × Y)} (hsub : demos ⊆ demos')
    {h : List A × Θ} (hc : Consistent step fin demos' h) : Consistent step fin demos h :=
  fun d hd => hc d (hsub hd)

/-- **Refutation is permanent.** -/
theorem inconsistent_mono {demos demos' : List (X × Y)} (hsub : demos ⊆ demos')
    {h : List A × Θ} (hn : ¬ Consistent step fin demos h) : ¬ Consistent step fin demos' h :=
  fun hc => hn (consistent_antitone hsub hc)

/-- **The separating example.** If two hypotheses disagree on the query, then whatever the true
output `y` of the query is, adding the demonstration `(q, y)` refutes at least one of them.  So
when the planner refuses because plans disagree, asking for the query's output (or for one cell
where they differ) is guaranteed to make progress. -/
theorem separating_example_refutes {demos : List (X × Y)} {h h' : List A × Θ} {q : X}
    (hne : sem step fin h q ≠ sem step fin h' q) (y : Y) :
    ¬ (Consistent step fin ((q, y) :: demos) h ∧ Consistent step fin ((q, y) :: demos) h') := by
  rintro ⟨hc, hc'⟩
  exact hne ((hc (q, y) List.mem_cons_self).trans (hc' (q, y) List.mem_cons_self).symm)

/-! ## Signatures: when two partial plans can be merged -/

variable (step) in
/-- The signature of a plan: its intermediate states on the probe inputs. -/
def sig (probes : List X) (p : List A) : List (Option X) := probes.map (run step p)

theorem run_eq_of_sig_eq {probes : List X} {p p' : List A}
    (h : sig step probes p = sig step probes p') {x : X} (hx : x ∈ probes) :
    run step p x = run step p' x := by
  unfold sig at h
  exact List.map_inj_left.mp h x hx

/-- **Merging is safe for continuations.** Equal signatures stay equal under every suffix. -/
theorem sig_append_congr {probes : List X} {p p' : List A}
    (h : sig step probes p = sig step probes p') (s : List A) :
    sig step probes (p ++ s) = sig step probes (p' ++ s) := by
  unfold sig
  refine List.map_congr_left fun x hx => ?_
  rw [run_append, run_append, run_eq_of_sig_eq h hx]

/-- Plans with equal signatures predict the same on every probe, with any suffix and finisher. -/
theorem sem_congr {probes : List X} {p p' : List A}
    (h : sig step probes p = sig step probes p') (s : List A) (θ : Θ) {x : X}
    (hx : x ∈ probes) :
    sem step fin (p ++ s, θ) x = sem step fin (p' ++ s, θ) x := by
  unfold sem
  rw [run_eq_of_sig_eq (sig_append_congr h s) hx]

/-- Plans with equal signatures are consistent together, with any suffix and finisher, provided
every demonstration input is a probe. -/
theorem consistent_congr {probes : List X} {demos : List (X × Y)}
    (hprobe : ∀ d ∈ demos, d.1 ∈ probes) {p p' : List A}
    (h : sig step probes p = sig step probes p') (s : List A) (θ : Θ) :
    Consistent step fin demos (p ++ s, θ) ↔ Consistent step fin demos (p' ++ s, θ) := by
  constructor
  · intro hc d hd
    rw [← sem_congr h s θ (hprobe d hd)]
    exact hc d hd
  · intro hc d hd
    rw [sem_congr h s θ (hprobe d hd)]
    exact hc d hd

/-! ## The breadth-first planner with merging -/

section Search

variable [DecidableEq X]

variable (step) in
/-- Add `p` to the kept list unless a kept plan already has its signature. -/
def keepNew (probes : List X) (acc : List (List A)) (p : List A) : List (List A) :=
  if ∃ q ∈ acc, sig step probes q = sig step probes p then acc else acc ++ [p]

variable (step) in
/-- Keep the first plan of each signature. -/
def dedup (probes : List X) (L : List (List A)) : List (List A) :=
  L.foldl (keepNew step probes) []

theorem foldl_keepNew_spec (probes : List X) (L acc : List (List A)) :
    (∀ r ∈ L.foldl (keepNew step probes) acc, r ∈ acc ∨ r ∈ L) ∧
    (∀ p, p ∈ acc ∨ p ∈ L →
      ∃ q ∈ L.foldl (keepNew step probes) acc, sig step probes q = sig step probes p) := by
  induction L generalizing acc with
  | nil =>
    simp only [List.foldl_nil, List.not_mem_nil, or_false]
    exact ⟨fun r hr => hr, fun p hp => ⟨p, hp, rfl⟩⟩
  | cons x L ih =>
    obtain ⟨ih1, ih2⟩ := ih (keepNew step probes acc x)
    simp only [List.foldl_cons, List.mem_cons]
    refine ⟨fun r hr => ?_, fun p hp => ?_⟩
    · rcases ih1 r hr with h | h
      · unfold keepNew at h
        split_ifs at h with hx
        · exact Or.inl h
        · rcases List.mem_append.mp h with h | h
          · exact Or.inl h
          · exact Or.inr (Or.inl (List.mem_singleton.mp h))
      · exact Or.inr (Or.inr h)
    · rcases hp with hp | rfl | hp
      · apply ih2
        left
        unfold keepNew
        split_ifs
        · exact hp
        · exact List.mem_append_left _ hp
      · by_cases hx : ∃ q ∈ acc, sig step probes q = sig step probes p
        · have e : keepNew step probes acc p = acc := if_pos hx
          rw [e] at ih2 ⊢
          obtain ⟨q, hq, hqs⟩ := hx
          obtain ⟨r, hr, hrs⟩ := ih2 q (Or.inl hq)
          exact ⟨r, hr, hrs.trans hqs⟩
        · have e : keepNew step probes acc p = acc ++ [p] := if_neg hx
          rw [e] at ih2 ⊢
          exact ih2 p (Or.inl (List.mem_append_right _ (List.mem_singleton_self p)))
      · exact ih2 p (Or.inr hp)

/-- Merging only keeps plans that were there. -/
theorem dedup_sub {probes : List X} {L : List (List A)} {q : List A}
    (hq : q ∈ dedup step probes L) : q ∈ L := by
  rcases (foldl_keepNew_spec probes L []).1 q hq with h | h
  · simp at h
  · exact h

/-- **Merging loses nothing**: every plan has a kept representative of the same signature. -/
theorem dedup_rep {probes : List X} {L : List (List A)} {p : List A} (hp : p ∈ L) :
    ∃ q ∈ dedup step probes L, sig step probes q = sig step probes p :=
  (foldl_keepNew_spec probes L []).2 p (Or.inr hp)

/-- Extend every plan by every step of the alphabet. -/
def expand (steps : List A) (F : List (List A)) : List (List A) :=
  F.flatMap fun p => steps.map fun a => p ++ [a]

theorem mem_expand {steps : List A} {F : List (List A)} {q : List A} :
    q ∈ expand steps F ↔ ∃ p ∈ F, ∃ a ∈ steps, q = p ++ [a] := by
  unfold expand
  simp only [List.mem_flatMap, List.mem_map]
  constructor
  · rintro ⟨p, hp, a, ha, rfl⟩
    exact ⟨p, hp, a, ha, rfl⟩
  · rintro ⟨p, hp, a, ha, rfl⟩
    exact ⟨p, hp, a, ha, rfl⟩

variable (step) in
/-- Layer `n` of the breadth-first planner: plans of length `n`, one per signature. -/
def layer (steps : List A) (probes : List X) : ℕ → List (List A)
  | 0 => [[]]
  | n + 1 => dedup step probes (expand steps (layer steps probes n))

/-- Layer `n` holds plans of length `n` over the alphabet. -/
theorem layer_sound {steps : List A} {probes : List X} :
    ∀ {n : ℕ} {q : List A}, q ∈ layer step steps probes n →
      q.length = n ∧ ∀ a ∈ q, a ∈ steps
  | 0, q, hq => by
    simp only [layer, List.mem_singleton] at hq
    subst hq
    simp
  | n + 1, q, hq => by
    have h := dedup_sub hq
    obtain ⟨p, hp, a, ha, rfl⟩ := mem_expand.mp h
    obtain ⟨hl, hs⟩ := layer_sound hp
    refine ⟨by simp [hl], fun b hb => ?_⟩
    rcases List.mem_append.mp hb with hb | hb
    · exact hs b hb
    · rw [List.mem_singleton.mp hb]; exact ha

/-- **Completeness of the merged search.** Every plan of length `n` over the alphabet has a
representative in layer `n` with the same signature. -/
theorem layer_complete {steps : List A} {probes : List X} :
    ∀ (n : ℕ) (p : List A), p.length = n → (∀ a ∈ p, a ∈ steps) →
      ∃ q ∈ layer step steps probes n, sig step probes q = sig step probes p
  | 0, p, hp, _ => by
    rw [List.length_eq_zero_iff] at hp
    subst hp
    exact ⟨[], by simp [layer], rfl⟩
  | n + 1, p, hp, hs => by
    obtain ⟨r, a, rfl⟩ : ∃ r a, p = r ++ [a] := by
      rcases List.eq_nil_or_concat p with h | ⟨r, a, h⟩
      · subst h; simp at hp
      · exact ⟨r, a, by simpa using h⟩
    have hr : r.length = n := by simpa using hp
    have hrs : ∀ b ∈ r, b ∈ steps := fun b hb => hs b (List.mem_append_left _ hb)
    have ha : a ∈ steps := hs a (List.mem_append_right _ (List.mem_singleton_self a))
    obtain ⟨q, hq, hqs⟩ := layer_complete n r hr hrs
    have hmem : q ++ [a] ∈ expand steps (layer step steps probes n) :=
      mem_expand.mpr ⟨q, hq, a, ha, rfl⟩
    obtain ⟨q', hq', hq's⟩ := dedup_rep (step := step) (probes := probes) hmem
    exact ⟨q', hq', hq's.trans (sig_append_congr hqs [a])⟩

/-- All plans of length `n` over the alphabet. -/
def AllPlans (steps : List A) (n : ℕ) : Set (List A) :=
  {p | p.length = n ∧ ∀ a ∈ p, a ∈ steps}

theorem layer_subset_allPlans {steps : List A} {probes : List X} {n : ℕ} {q : List A}
    (hq : q ∈ layer step steps probes n) : q ∈ AllPlans steps n :=
  layer_sound hq

variable {probes : List X} {demos : List (X × Y)} {steps : List A} {F : Set Θ}

/-- **Consistency can be decided on the merged layer.** -/
theorem exists_consistent_iff_layer (hprobe : ∀ d ∈ demos, d.1 ∈ probes) (n : ℕ) :
    (∃ p ∈ AllPlans steps n, ∃ θ ∈ F, Consistent step fin demos (p, θ)) ↔
      (∃ q ∈ layer step steps probes n, ∃ θ ∈ F, Consistent step fin demos (q, θ)) := by
  constructor
  · rintro ⟨p, ⟨hl, hs⟩, θ, hθ, hc⟩
    obtain ⟨q, hq, hqs⟩ := layer_complete (step := step) (probes := probes) n p hl hs
    refine ⟨q, hq, θ, hθ, ?_⟩
    have := (consistent_congr (fin := fin) hprobe hqs [] θ).2
    simpa using this (by simpa using hc)
  · rintro ⟨q, hq, θ, hθ, hc⟩
    exact ⟨q, layer_subset_allPlans hq, θ, hθ, hc⟩

/-- **Agreement can be decided on the merged layer**, provided the query is a probe. -/
theorem agree_iff_layer (hprobe : ∀ d ∈ demos, d.1 ∈ probes) {query : X}
    (hq : query ∈ probes) (n : ℕ) (a : Y) :
    (∀ p ∈ AllPlans steps n, ∀ θ ∈ F, Consistent step fin demos (p, θ) →
        sem step fin (p, θ) query = some a) ↔
      (∀ q ∈ layer step steps probes n, ∀ θ ∈ F, Consistent step fin demos (q, θ) →
        sem step fin (q, θ) query = some a) := by
  constructor
  · intro h q hql θ hθ hc
    exact h q (layer_subset_allPlans hql) θ hθ hc
  · intro h p ⟨hl, hs⟩ θ hθ hc
    obtain ⟨q, hql, hqs⟩ := layer_complete (step := step) (probes := probes) n p hl hs
    have hc' : Consistent step fin demos (q, θ) := by
      have := (consistent_congr (fin := fin) hprobe hqs [] θ).2
      simpa using this (by simpa using hc)
    have := h q hql θ hθ hc'
    have e := sem_congr (fin := fin) hqs [] θ hq
    simp only [List.append_nil] at e
    rw [← e]
    exact this

/-! ## The planner: first consistent depth, answer only on agreement -/

variable (step fin) in
/-- The planner answers `a` at depth `n`: no merged layer below `n` has a consistent hypothesis,
layer `n` has one, and every consistent hypothesis in layer `n` answers `a` on the query. -/
def PlannerAnswers (steps : List A) (probes : List X) (F : Set Θ) (demos : List (X × Y))
    (query : X) (n : ℕ) (a : Y) : Prop :=
  (∀ m < n, ∀ q ∈ layer step steps probes m, ∀ θ ∈ F, ¬ Consistent step fin demos (q, θ)) ∧
  (∃ q ∈ layer step steps probes n, ∃ θ ∈ F, Consistent step fin demos (q, θ)) ∧
  (∀ q ∈ layer step steps probes n, ∀ θ ∈ F, Consistent step fin demos (q, θ) →
    sem step fin (q, θ) query = some a)

/-- **The planner's depth is the shortest explanation**: no plan (merged or not) shorter than the
answering depth reproduces the demonstrations. -/
theorem planner_minimal (hprobe : ∀ d ∈ demos, d.1 ∈ probes) {query : X} {n : ℕ} {a : Y}
    (hP : PlannerAnswers step fin steps probes F demos query n a) {m : ℕ} (hm : m < n)
    {p : List A} (hp : p ∈ AllPlans steps m) {θ : Θ} (hθ : θ ∈ F) :
    ¬ Consistent step fin demos (p, θ) := by
  intro hc
  obtain ⟨q, hq, θ', hθ', hc'⟩ :=
    (exists_consistent_iff_layer (fin := fin) (F := F) hprobe m).1 ⟨p, hp, θ, hθ, hc⟩
  exact hP.1 m hm q hq θ' hθ' hc'

/-- **Every consistent plan of the answering depth agrees** — not just the kept representatives. -/
theorem planner_agree_all (hprobe : ∀ d ∈ demos, d.1 ∈ probes) {query : X}
    (hq : query ∈ probes) {n : ℕ} {a : Y}
    (hP : PlannerAnswers step fin steps probes F demos query n a) :
    ∀ p ∈ AllPlans steps n, ∀ θ ∈ F, Consistent step fin demos (p, θ) →
      sem step fin (p, θ) query = some a :=
  (agree_iff_layer (fin := fin) (F := F) hprobe hq n a).2 hP.2.2

/-- **Planner correctness under the Occam premise.** If the demonstrations come from a true
hypothesis that is a plan over the alphabet with a finisher in `F`, then the planner never answers
at a depth above its length, and if the true plan is a *shortest* explanation (its length is the
answering depth), the planner's answer is the true answer. -/
theorem planner_correct (hprobe : ∀ d ∈ demos, d.1 ∈ probes) {query : X}
    (hq : query ∈ probes) {n : ℕ} {a : Y}
    (hP : PlannerAnswers step fin steps probes F demos query n a)
    {p : List A} {θ : Θ} (hp : ∀ b ∈ p, b ∈ steps) (hθ : θ ∈ F)
    (hc : Consistent step fin demos (p, θ)) :
    n ≤ p.length ∧ (p.length = n → sem step fin (p, θ) query = some a) := by
  refine ⟨?_, fun hl => planner_agree_all hprobe hq hP p ⟨hl, hp⟩ θ hθ hc⟩
  by_contra hlt
  exact planner_minimal hprobe hP (not_le.mp hlt) ⟨rfl, hp⟩ hθ hc

end Search

/-! ## Cost tiers: the agreement rule over any Occam order -/

section Tiers

variable {H : Type*}

/-- The tiered agreement rule over hypotheses `H` with a cost (e.g. plan length, then finisher
rank, then the steps' Occam weight, encoded lexicographically as one number): tier `t` is the
least cost of a consistent hypothesis, and every consistent hypothesis of cost `t` answers `a`. -/
def MinAgree (cost : H → ℕ) (Cons : H → Prop) (ans : H → Option Y) (t : ℕ) (a : Y) : Prop :=
  (∀ h, Cons h → t ≤ cost h) ∧ (∃ h, Cons h ∧ cost h = t) ∧
    ∀ h, Cons h → cost h = t → ans h = some a

variable {cost : H → ℕ} {Cons : H → Prop} {ans : H → Option Y}

/-- **Tiered agreement is correct under the Occam premise**: if the true hypothesis is consistent
and of least cost, the answer is the true answer. -/
theorem minAgree_correct {t : ℕ} {a : Y} (hM : MinAgree cost Cons ans t a) {htrue : H}
    (hc : Cons htrue) (hcost : cost htrue = t) : ans htrue = some a :=
  hM.2.2 htrue hc hcost

/-- The tier and the answer of the tiered rule are unique. -/
theorem minAgree_unique {t t' : ℕ} {a a' : Y} (hM : MinAgree cost Cons ans t a)
    (hM' : MinAgree cost Cons ans t' a') : t = t' ∧ a = a' := by
  obtain ⟨h1, ⟨h, hc, hct⟩, h3⟩ := hM
  obtain ⟨h1', ⟨h', hc', hct'⟩, h3'⟩ := hM'
  have ht : t = t' := le_antisymm (hct' ▸ h1 h' hc') (hct ▸ h1' h hc)
  refine ⟨ht, ?_⟩
  have e1 := h3 h hc hct
  have e2 := h3' h hc (hct.trans ht)
  rw [e1] at e2
  exact Option.some_injective _ e2

/-- **Without the Occam premise the rule can be wrong**: a consistent hypothesis of higher cost
may answer differently.  (Two hypotheses, both consistent, costs `0` and `1`, answers `0`, `1`.) -/
theorem minAgree_needs_occam :
    MinAgree (fun b : Bool => if b then 1 else 0) (fun _ => True)
      (fun b => some (if b then 1 else 0)) 0 (0 : ℕ) ∧
    (fun b : Bool => some (if b then 1 else 0)) true ≠ some (0 : ℕ) := by
  refine ⟨⟨fun _ _ => Nat.zero_le _, ⟨false, trivial, rfl⟩, ?_⟩, by simp⟩
  intro h _ hc
  cases h <;> simp_all

end Tiers

/-! ## Negative control: merging on the demonstrations alone is unsound -/

/-- Two steps on `ℕ`: `false` is the identity, `true` adds one to every non-zero number. -/
def ctrlStep : Bool → ℕ → Option ℕ
  | false, x => some x
  | true, x => some (if x = 0 then 0 else x + 1)

/-- **Negative control.** With demonstration `0 ↦ 0` and query `1`, merging plans by their
states on the demonstration input alone keeps one plan of length one, and every consistent kept
plan answers `1`; but the unmerged layer has a consistent plan answering `2`.  So the probes must
include the queries (as in `agree_iff_layer`). -/
theorem train_only_signature_unsound :
    (∀ q ∈ layer ctrlStep [false, true] [0] 1,
        Consistent ctrlStep (fun (_ : Unit) x => some x) [(0, 0)] (q, ()) →
        sem ctrlStep (fun (_ : Unit) x => some x) (q, ()) 1 = some 1) ∧
      Consistent ctrlStep (fun (_ : Unit) x => some x) [(0, 0)] ([true], ()) ∧
      sem ctrlStep (fun (_ : Unit) x => some x) ([true], ()) 1 = some 2 := by
  refine ⟨?_, ?_, ?_⟩
  · intro q hq _
    have : layer ctrlStep [false, true] [0] 1 = [[false]] := by decide
    rw [this, List.mem_singleton] at hq
    subst hq
    rfl
  · intro d hd
    simp only [List.mem_singleton] at hd
    subst hd
    rfl
  · rfl

end GLM.PlanSearch
