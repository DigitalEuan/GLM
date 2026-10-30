import RequestProject.GLM.PipelineInduction

/-!
# Asking for the separating example (Phase 176)

*Created 21 October 2026.*

The formal half of `studies/PIPELINE_ASK_STUDY.md`. When `tool induce` refuses because two
hypotheses that fit every demonstration disagree on the query
(`GLM.PipelineInduction.ambiguous_forces_refusal`), the GLM now names an input grid on which the
fitting hypotheses disagree and asks for its output (`reasoning/pipeline_ask.py`). This file proves
what that buys, for any input type `α`, output type `β` and hypothesis class `H`, with the reply
given by the true rule `f`:

* `separating_demo_removes` — after the reply to a separating input, the two hypotheses it
  separated cannot both still fit;
* `consistentIn_cons` — a new demonstration filters the survivors by agreement on it;
* `separating_strict_shrink` — so the number of surviving members of `H` drops by at least one;
* `truth_survives_asks` — the true rule keeps fitting however many replies are added;
* `asks_shrink` — after `k` separating asks, at least `k` members have gone;
* `asks_bounded` — if the true rule is in `H`, at most `|H| − 1` separating asks can ever be
  made: the loop of asking stops;
* `ask_then_sound` — whatever the gate answers after the asks is the true rule's answer.

What is *not* proved: that one ask suffices, or that a separating input exists among the grids
the GLM considers. The study measures both.
-/

namespace GLM.PipelineAsk

open GLM.PipelineInduction

variable {α β : Type*}

/-- `x` separates the class `H` under the demonstrations: two members of `H` that fit every
demonstration give `x` different outputs. -/
def Separates (demos : List (α × β)) (H : List (α → β)) (x : α) : Prop :=
  ∃ h₁ ∈ H, ∃ h₂ ∈ H, Consistent demos h₁ ∧ Consistent demos h₂ ∧ h₁ x ≠ h₂ x

/-- Add the true rule's reply on each asked input, most recent first. -/
def extend (f : α → β) : List α → List (α × β) → List (α × β)
  | [], demos => demos
  | x :: xs, demos => extend f xs ((x, f x) :: demos)

/-- Every ask in the sequence separates the class under the demonstrations seen so far. -/
def AllSeparate (f : α → β) (H : List (α → β)) : List (α × β) → List α → Prop
  | _, [] => True
  | demos, x :: xs => Separates demos H x ∧ AllSeparate f H ((x, f x) :: demos) xs

/-- After the reply `f x` to a separating input, the two hypotheses it separated cannot both
still fit. -/
theorem separating_demo_removes {f : α → β} {demos : List (α × β)} {x : α} {h₁ h₂ : α → β}
    (hne : h₁ x ≠ h₂ x) :
    ¬ (Consistent ((x, f x) :: demos) h₁ ∧ Consistent ((x, f x) :: demos) h₂) := by
  rintro ⟨c₁, c₂⟩
  exact hne ((c₁ _ (List.mem_cons_self ..)).trans (c₂ _ (List.mem_cons_self ..)).symm)

/-- The true rule keeps fitting however many of its replies are added. -/
theorem truth_survives_asks {f : α → β} :
    ∀ (xs : List α) {demos : List (α × β)}, Consistent demos f → Consistent (extend f xs demos) f
  | [], _, hc => hc
  | x :: xs, demos, hc => by
    apply truth_survives_asks xs
    intro d hd
    rcases List.mem_cons.mp hd with rfl | hd
    · rfl
    · exact hc d hd

section Counting

variable [DecidableEq β]

/-- A new demonstration filters the survivors by agreement on it. -/
theorem consistentIn_cons (x : α) (y : β) (demos : List (α × β)) (H : List (α → β)) :
    consistentIn ((x, y) :: demos) H = (consistentIn demos H).filter (fun h => decide (h x = y)) := by
  unfold consistentIn
  rw [List.filter_filter]
  congr 1
  funext h
  simp only [Consistent, List.mem_cons, forall_eq_or_imp]
  by_cases e : h x = y <;> simp [e]

/-- **A separating ask removes at least one survivor.** -/
theorem separating_strict_shrink {f : α → β} {demos : List (α × β)} {H : List (α → β)}
    {x : α} (hs : Separates demos H x) :
    (consistentIn ((x, f x) :: demos) H).length < (consistentIn demos H).length := by
  obtain ⟨h₁, m₁, h₂, m₂, c₁, c₂, hne⟩ := hs
  rw [consistentIn_cons, List.length_filter_lt_length_iff_exists]
  by_cases e : h₁ x = f x
  · refine ⟨h₂, mem_consistentIn.mpr ⟨m₂, c₂⟩, ?_⟩
    simp only [decide_eq_true_eq]
    exact fun e₂ => hne (e.trans e₂.symm)
  · exact ⟨h₁, mem_consistentIn.mpr ⟨m₁, c₁⟩, by simpa using e⟩

/-- **After `k` separating asks, at least `k` members of the class have gone.** -/
theorem asks_shrink {f : α → β} {H : List (α → β)} :
    ∀ (xs : List α) {demos : List (α × β)}, AllSeparate f H demos xs →
      (consistentIn (extend f xs demos) H).length + xs.length ≤ (consistentIn demos H).length
  | [], _, _ => by simp [extend]
  | x :: xs, demos, ⟨hs, hrest⟩ => by
    have ih := asks_shrink xs hrest
    have hlt := separating_strict_shrink (f := f) hs
    simp only [extend, List.length_cons]
    omega

/-- **The loop of asking stops.** If the true rule is in `H` and fits the demonstrations, a
sequence of separating asks has length at most `|H| − 1`. -/
theorem asks_bounded {f : α → β} {H : List (α → β)} {demos : List (α × β)} {xs : List α}
    (hf : f ∈ H) (hc : Consistent demos f) (hall : AllSeparate f H demos xs) :
    xs.length + 1 ≤ H.length := by
  have h1 := asks_shrink xs hall
  have hmem : f ∈ consistentIn (extend f xs demos) H :=
    mem_consistentIn.mpr ⟨hf, truth_survives_asks xs hc⟩
  have hpos : 0 < (consistentIn (extend f xs demos) H).length :=
    List.length_pos_of_mem hmem
  have hle : (consistentIn demos H).length ≤ H.length := List.length_filter_le _ _
  omega

/-- **What the gate answers after the asks is the true rule's answer.** -/
theorem ask_then_sound {f : α → β} {H : List (α → β)} {demos : List (α × β)} {xs : List α}
    {q : α} {a : β} (hf : f ∈ H) (hc : Consistent demos f)
    (hs : solve [H] (extend f xs demos) q = some a) : f q = a :=
  solve_sound (pre := []) (post := []) (by simp) hf (truth_survives_asks xs hc) hs

end Counting

end GLM.PipelineAsk
