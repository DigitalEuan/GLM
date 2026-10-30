import RequestProject.GLM.PipelineKit.Permutation

/-!
# Rule induction from demonstrations, with an agreement gate (Phase 175)

*Created 21 October 2026.*

The formal half of `studies/PIPELINE_KIT_STUDY.md`. The owner's pipeline kit
(`source_material/GLM_Pipeline_Kit/`) solves a task given as demonstration
pairs `(input, output)` by keeping **every** hypothesis consistent with the
demonstrations in superposition, and answering a query only when all of them
agree on it. Phase 175 brings that solver into the GLM
(`reasoning/pipeline_kit.py`, `tool induce`) with three additions: the region
fill and the two-point path writer (the kit's two open items), two-step
compositions searched only when no single step fits, and a last tier that
learns a cell permutation from the demonstrations. The hypotheses are kept in
**tiers**, tried in order; the first tier with a consistent member is the one
read.

What is proved, for any input type `α` and output type `β`:

* `truth_consistent` — the rule that produced the demonstrations is
  consistent with them;
* `agree_sound` — if the true rule is in a hypothesis class and every
  consistent member of the class gives the query the same answer, that answer
  is the true rule's;
* `ambiguous_forces_refusal` — if two consistent members disagree, then every
  possible answer is wrong for some member consistent with everything seen:
  refusing is forced, not cautious;
* `consistentIn_more_demos` — a further demonstration can only remove
  hypotheses (the superposition collapses monotonically);
* `solve_sound` — the tiered solver's answer is the true rule's whenever the
  true rule is in the tier the solver read: every earlier tier had no
  consistent member;
* `solve_refuses_disagreement`, `solve_answers_agreement` — it refuses exactly
  when the tier it read disagrees on the query;
* `solve_never_invents` — every answer it gives is the output of a hypothesis
  consistent with all the demonstrations;
* `solve_none_of_unfit` — with no consistent hypothesis anywhere it refuses.

And one fact tying a two-step composition back to the kit's lattice layer:
`perm_toggle_layer` — permuting the 24 cells and then toggling all of them
keeps a word on the same `4×` Leech layer (`GLMKit.leech_layer_perm`,
`GLMKit.leech_layer_toggle`).

What is *not* proved here: that the true rule of a given task lies in the tier
the solver reads. That is a property of the task family, and the study
measures it (its wrong-answer counts).
-/

namespace GLM.PipelineInduction

variable {α β : Type*}

/-- A hypothesis is consistent with the demonstrations when it maps every
demonstration input to that demonstration's output. -/
def Consistent (demos : List (α × β)) (h : α → β) : Prop :=
  ∀ d ∈ demos, h d.1 = d.2

/-- The rule that produced the demonstrations is consistent with them. -/
theorem truth_consistent {f : α → β} {demos : List (α × β)}
    (hd : ∀ d ∈ demos, d.2 = f d.1) : Consistent demos f :=
  fun d hm => (hd d hm).symm

/-- Fewer demonstrations constrain less: consistency passes to a subset. -/
theorem consistent_of_subset {demos demos' : List (α × β)} (hs : demos ⊆ demos')
    {h : α → β} (hc : Consistent demos' h) : Consistent demos h :=
  fun d hm => hc d (hs hm)

/-- **The agreement gate is sound.** If the true rule `f` lies in the class `H`
and every member of `H` consistent with the demonstrations answers the query
`q` with `a`, then `a` is what `f` gives. -/
theorem agree_sound {H : List (α → β)} {f : α → β} {demos : List (α × β)}
    {q : α} {a : β} (hf : f ∈ H) (hc : Consistent demos f)
    (hagree : ∀ h ∈ H, Consistent demos h → h q = a) : f q = a :=
  hagree f hf hc

/-- **Refusal is forced when the consistent hypotheses disagree.** Whatever
answer `a` is given, some member of the class that fits every demonstration
gives the query a different answer, so `a` is wrong if that member is the
truth. -/
theorem ambiguous_forces_refusal {H : List (α → β)} {demos : List (α × β)}
    {q : α} {h₁ h₂ : α → β} (m₁ : h₁ ∈ H) (m₂ : h₂ ∈ H)
    (c₁ : Consistent demos h₁) (c₂ : Consistent demos h₂) (hne : h₁ q ≠ h₂ q)
    (a : β) : ∃ h ∈ H, Consistent demos h ∧ h q ≠ a := by
  by_cases e : h₁ q = a
  · exact ⟨h₂, m₂, c₂, fun e₂ => hne (e.trans e₂.symm)⟩
  · exact ⟨h₁, m₁, c₁, e⟩

section Solver

variable [DecidableEq β]

instance (demos : List (α × β)) (h : α → β) : Decidable (Consistent demos h) := by
  unfold Consistent; infer_instance

/-- The members of `H` consistent with the demonstrations. -/
def consistentIn (demos : List (α × β)) (H : List (α → β)) : List (α → β) :=
  H.filter fun h => decide (Consistent demos h)

theorem mem_consistentIn {demos : List (α × β)} {H : List (α → β)} {h : α → β} :
    h ∈ consistentIn demos H ↔ h ∈ H ∧ Consistent demos h := by
  simp [consistentIn]

/-- A further demonstration can only remove hypotheses. -/
theorem consistentIn_more_demos (d : α × β) (demos : List (α × β))
    (H : List (α → β)) :
    consistentIn (d :: demos) H ⊆ consistentIn demos H := by
  intro h hm
  rw [mem_consistentIn] at hm ⊢
  exact ⟨hm.1, consistent_of_subset (List.subset_cons_self d demos) hm.2⟩

/-- The tier the solver reads: the consistent members of the first tier that
has any. -/
def selectTier (demos : List (α × β)) : List (List (α → β)) → List (α → β)
  | [] => []
  | H :: rest =>
      if consistentIn demos H = [] then selectTier demos rest else consistentIn demos H

/-- Collapse a list of hypotheses on the query: an answer only if all agree. -/
def collapse (q : α) : List (α → β) → Option β
  | [] => none
  | h :: rest => if rest.all (fun g => decide (g q = h q)) then some (h q) else none

/-- The tiered solver: read the first tier with a consistent member, and answer
only if all of its consistent members agree on the query. -/
def solve (tiers : List (List (α → β))) (demos : List (α × β)) (q : α) : Option β :=
  collapse q (selectTier demos tiers)

theorem collapse_some {q : α} {L : List (α → β)} {a : β} (hs : collapse q L = some a) :
    ∀ g ∈ L, g q = a := by
  cases L with
  | nil => simp [collapse] at hs
  | cons h rest =>
    simp only [collapse] at hs
    split_ifs at hs with hall
    · cases hs
      intro g hg
      rcases List.mem_cons.mp hg with rfl | hg
      · rfl
      · simpa using (List.all_eq_true.mp hall) g hg

theorem collapse_some_of_agree {q : α} {L : List (α → β)} {a : β} (hne : L ≠ [])
    (hall : ∀ g ∈ L, g q = a) : collapse q L = some a := by
  cases L with
  | nil => exact absurd rfl hne
  | cons h rest =>
    have hh : h q = a := hall h (List.mem_cons_self ..)
    simp only [collapse]
    rw [if_pos]
    · rw [hh]
    · apply List.all_eq_true.mpr
      intro g hg
      simp [hall g (List.mem_cons_of_mem _ hg), hh]

theorem collapse_none_of_disagree {q : α} {L : List (α → β)} {g₁ g₂ : α → β}
    (m₁ : g₁ ∈ L) (m₂ : g₂ ∈ L) (hne : g₁ q ≠ g₂ q) : collapse q L = none := by
  cases hc : collapse q L with
  | none => rfl
  | some a =>
    have h := collapse_some hc
    exact absurd ((h g₁ m₁).trans (h g₂ m₂).symm) hne

theorem mem_selectTier {demos : List (α × β)} :
    ∀ {tiers : List (List (α → β))} {g : α → β}, g ∈ selectTier demos tiers →
      ∃ H ∈ tiers, g ∈ H ∧ Consistent demos g
  | [], _, hg => by simp [selectTier] at hg
  | H :: rest, g, hg => by
    simp only [selectTier] at hg
    split_ifs at hg
    · obtain ⟨H', hH', hgH'⟩ := mem_selectTier hg
      exact ⟨H', List.mem_cons_of_mem _ hH', hgH'⟩
    · exact ⟨H, List.mem_cons_self .., mem_consistentIn.mp hg⟩

theorem selectTier_append {demos : List (α × β)} :
    ∀ (pre : List (List (α → β))) (T : List (α → β)) (post : List (List (α → β))),
      (∀ H ∈ pre, consistentIn demos H = []) → consistentIn demos T ≠ [] →
      selectTier demos (pre ++ T :: post) = consistentIn demos T
  | [], T, post, _, hT => by simp [selectTier, hT]
  | H :: pre, T, post, hpre, hT => by
    have hH : consistentIn demos H = [] := hpre H (List.mem_cons_self ..)
    simp only [List.cons_append, selectTier, hH, if_true]
    exact selectTier_append pre T post (fun H' h' => hpre H' (List.mem_cons_of_mem _ h')) hT

/-- **The tiered solver is sound.** If the true rule `f` fits the
demonstrations and lies in tier `T`, and every tier before `T` has no
consistent member, then any answer the solver gives is `f`'s. -/
theorem solve_sound {pre : List (List (α → β))} {T : List (α → β)}
    {post : List (List (α → β))} {demos : List (α × β)} {f : α → β} {q : α} {a : β}
    (hpre : ∀ H ∈ pre, consistentIn demos H = []) (hf : f ∈ T)
    (hc : Consistent demos f) (hs : solve (pre ++ T :: post) demos q = some a) :
    f q = a := by
  have hfT : f ∈ consistentIn demos T := mem_consistentIn.mpr ⟨hf, hc⟩
  have hT : consistentIn demos T ≠ [] := List.ne_nil_of_mem hfT
  unfold solve at hs
  rw [selectTier_append pre T post hpre hT] at hs
  exact collapse_some hs f hfT

/-- It refuses when two consistent members of the tier it reads disagree. -/
theorem solve_refuses_disagreement {tiers : List (List (α → β))}
    {demos : List (α × β)} {q : α} {g₁ g₂ : α → β}
    (m₁ : g₁ ∈ selectTier demos tiers) (m₂ : g₂ ∈ selectTier demos tiers)
    (hne : g₁ q ≠ g₂ q) : solve tiers demos q = none :=
  collapse_none_of_disagree m₁ m₂ hne

/-- It answers when the tier it reads is non-empty and agrees on the query. -/
theorem solve_answers_agreement {tiers : List (List (α → β))}
    {demos : List (α × β)} {q : α} {a : β} (hne : selectTier demos tiers ≠ [])
    (hall : ∀ g ∈ selectTier demos tiers, g q = a) : solve tiers demos q = some a :=
  collapse_some_of_agree hne hall

/-- **It never invents.** Every answer is the output, on the query, of some
hypothesis of some tier that fits all the demonstrations. -/
theorem solve_never_invents {tiers : List (List (α → β))} {demos : List (α × β)}
    {q : α} {a : β} (hs : solve tiers demos q = some a) :
    ∃ H ∈ tiers, ∃ h ∈ H, Consistent demos h ∧ h q = a := by
  unfold solve at hs
  cases hL : selectTier demos tiers with
  | nil => rw [hL] at hs; simp [collapse] at hs
  | cons h rest =>
    have hm : h ∈ selectTier demos tiers := by rw [hL]; exact List.mem_cons_self ..
    obtain ⟨H, hH, hhH, hc⟩ := mem_selectTier hm
    exact ⟨H, hH, h, hhH, hc, collapse_some hs h hm⟩

/-- With no consistent hypothesis in any tier, it refuses. -/
theorem solve_none_of_unfit {tiers : List (List (α → β))} {demos : List (α × β)}
    {q : α} (h : ∀ H ∈ tiers, ∀ g ∈ H, ¬ Consistent demos g) :
    solve tiers demos q = none := by
  cases hs : solve tiers demos q with
  | none => rfl
  | some a =>
    obtain ⟨H, hH, g, hg, hc, _⟩ := solve_never_invents hs
    exact absurd hc (h H hH g hg)

end Solver

open GLMKit in
/-- A two-step composition stays on the kit's lattice layer: permuting the 24
cells of a word and then toggling every cell keeps `4·b` in `Λ₂₄` exactly when
`4·b` was. -/
theorem perm_toggle_layer (b : Fin 24 → Bool) (σ : Equiv.Perm (Fin 24)) :
    Leech24 (fun i => 4 * bitZ (!(b ∘ σ) i)) ↔ Leech24 (fun i => 4 * bitZ (b i)) :=
  (leech_layer_toggle (b ∘ σ)).trans (leech_layer_perm b σ)

end GLM.PipelineInduction
