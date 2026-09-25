import Mathlib

/-!
# Typed question plans: answer only on one agreed value

A question in English can be read as more than one operation the machine
has.  *What is the atomic weight of carbon?* is one field of one row;
*does energy have the same dimensions as torque?* is a check that can be run
on the extended dimension vector, which keeps the plane angle, or on the SI
projection, which drops it — and the two readings disagree.

The planner (`glm_universal.runtime.semantic_plan`) turns a question into
candidate plans, runs every one, and calls a plan *licensed* when it solves.
This file states the rule that decides what is then said, `accept`, and the
four things it must and must not do.

* **Order does not matter** (`accept_perm`).  The frames are tried in a fixed
  order, and that order must not be what picks the answer: permuting the
  candidates leaves the verdict alone.
* **An answer is a value every licensed plan agrees on**
  (`accept_eq_answered_iff`), and so **two licensed readings that disagree
  are refused** (`disagreement_is_ambiguous`) rather than resolved by
  whichever came first.
* **The planner is conservative over the grammar** (`planned_conservative`):
  where no plan is licensed the question falls through, and the answer is
  exactly the grammar's.  So it never refuses what the grammar answered
  except where two licensed readings disagree
  (`planned_refuses_only_on_disagreement`), and it never says a value that
  neither a licensed plan nor the grammar produced (`planned_sound`).
* **The obvious rule fails both ways.**  Taking the first licensed plan is
  order-dependent (`first_licensed_order_dependent`) and answers a question
  whose two readings disagree (`first_licensed_answers_a_disagreement`) —
  the torque case, with `true` from one layer and `false` from the other.
-/

namespace GLM.SemanticPlan

/-- What running one plan gave: whether it solved, and the value it gave. -/
structure Outcome (V : Type) where
  /-- The plan solved. -/
  licensed : Bool
  /-- What it said (meaningless when it did not solve). -/
  value : V
deriving DecidableEq, Repr

/-- What the planner decides about a question. -/
inductive Verdict (V : Type) where
  /-- One value, agreed by every licensed plan. -/
  | answered (v : V)
  /-- Two licensed plans disagree. -/
  | ambiguous
  /-- Plans ran and none solved. -/
  | refused
  /-- No frame read the question at all. -/
  | fallthrough
deriving DecidableEq, Repr

variable {V : Type} [DecidableEq V]

/-- The values of the licensed outcomes, in order. -/
def licensedValues (os : List (Outcome V)) : List V :=
  (os.filter (fun o => o.licensed)).map (fun o => o.value)

/-- The licensing rule. -/
def accept (os : List (Outcome V)) : Verdict V :=
  if os = [] then .fallthrough
  else
    match (licensedValues os).dedup with
    | [] => .refused
    | [v] => .answered v
    | _ :: _ :: _ => .ambiguous

/-- The rule, read off a deduplicated list of licensed values. -/
private def ofDedup (os : List (Outcome V)) (d : List V) : Verdict V :=
  if os = [] then .fallthrough
  else
    match d with
    | [] => .refused
    | [v] => .answered v
    | _ :: _ :: _ => .ambiguous

private lemma accept_eq_ofDedup (os : List (Outcome V)) :
    accept os = ofDedup os (licensedValues os).dedup := rfl

omit [DecidableEq V] in
private lemma ofDedup_perm {os os' : List (Outcome V)} {d d' : List V}
    (hos : os = [] ↔ os' = []) (h : d.Perm d') :
    ofDedup os d = ofDedup os' d' := by
  unfold ofDedup
  by_cases h0 : os = []
  · simp [h0, hos.mp h0]
  · have h0' : os' ≠ [] := fun h' => h0 (hos.mpr h')
    simp only [h0, h0', if_false]
    rcases d with _ | ⟨a, _ | ⟨b, t⟩⟩
    · rw [List.Perm.nil_eq h]
    · have := List.singleton_perm.mp h
      subst this
      rfl
    · have hl := h.length_eq
      rcases d' with _ | ⟨a', _ | ⟨b', t'⟩⟩
      · simp at hl
      · simp at hl
      · rfl

/-- **Order does not matter.**  Permuting the candidate plans leaves the
verdict unchanged. -/
theorem accept_perm {os os' : List (Outcome V)} (h : os.Perm os') :
    accept os = accept os' := by
  rw [accept_eq_ofDedup, accept_eq_ofDedup]
  apply ofDedup_perm
  · constructor
    · intro h0; subst h0; exact List.Perm.nil_eq h |>.symm
    · intro h0; subst h0; exact List.Perm.eq_nil h
  · exact ((h.filter _).map _).dedup

omit [DecidableEq V] in
private lemma mem_licensedValues {os : List (Outcome V)} {v : V} :
    v ∈ licensedValues os ↔ ∃ o ∈ os, o.licensed = true ∧ o.value = v := by
  simp [licensedValues, List.mem_map, List.mem_filter, and_assoc]

private lemma dedup_eq_singleton_iff {l : List V} {v : V} :
    l.dedup = [v] ↔ v ∈ l ∧ ∀ w ∈ l, w = v := by
  constructor
  · intro h
    have hv : v ∈ l.dedup := by rw [h]; simp
    refine ⟨List.mem_dedup.mp hv, fun w hw => ?_⟩
    have : w ∈ l.dedup := List.mem_dedup.mpr hw
    rw [h] at this
    simpa using this
  · rintro ⟨hv, hall⟩
    have hsub : ∀ w ∈ l.dedup, w = v := fun w hw => hall w (List.mem_dedup.mp hw)
    have hnd : l.dedup.Nodup := List.nodup_dedup l
    have hmem : v ∈ l.dedup := List.mem_dedup.mpr hv
    rcases hd : l.dedup with _ | ⟨a, _ | ⟨b, t⟩⟩
    · rw [hd] at hmem; simp at hmem
    · rw [hd] at hmem; simp at hmem; rw [hmem]
    · rw [hd] at hsub hnd
      have ha := hsub a (by simp)
      have hb := hsub b (by simp)
      simp at hnd
      exact absurd (ha.trans hb.symm) hnd.1.1

/-- **What an answer is.**  The rule answers `v` exactly when some plan ran,
some licensed plan said `v`, and every licensed plan said `v`. -/
theorem accept_eq_answered_iff (os : List (Outcome V)) (v : V) :
    accept os = .answered v ↔
      (∃ o ∈ os, o.licensed = true ∧ o.value = v) ∧
      ∀ o ∈ os, o.licensed = true → o.value = v := by
  unfold accept
  by_cases h0 : os = []
  · subst h0; simp
  · simp only [h0, if_false]
    constructor
    · intro h
      rcases hd : (licensedValues os).dedup with _ | ⟨a, _ | ⟨b, t⟩⟩
      · rw [hd] at h; cases h
      · rw [hd] at h
        cases h
        have := dedup_eq_singleton_iff.mp hd
        refine ⟨mem_licensedValues.mp this.1, fun o ho hl => ?_⟩
        exact this.2 _ (mem_licensedValues.mpr ⟨o, ho, hl, rfl⟩)
      · rw [hd] at h; cases h
    · rintro ⟨hex, hall⟩
      have hd : (licensedValues os).dedup = [v] := by
        refine dedup_eq_singleton_iff.mpr ⟨mem_licensedValues.mpr hex, ?_⟩
        intro w hw
        obtain ⟨o, ho, hl, rfl⟩ := mem_licensedValues.mp hw
        exact hall o ho hl
      rw [hd]

/-- **Two licensed readings that disagree are refused as ambiguous.** -/
theorem disagreement_is_ambiguous {os : List (Outcome V)} {o₁ o₂ : Outcome V}
    (h₁ : o₁ ∈ os) (h₂ : o₂ ∈ os) (l₁ : o₁.licensed = true)
    (l₂ : o₂.licensed = true) (hne : o₁.value ≠ o₂.value) :
    accept os = .ambiguous := by
  have hne0 : os ≠ [] := by rintro rfl; simp at h₁
  have hv₁ : o₁.value ∈ (licensedValues os).dedup :=
    List.mem_dedup.mpr (mem_licensedValues.mpr ⟨o₁, h₁, l₁, rfl⟩)
  have hv₂ : o₂.value ∈ (licensedValues os).dedup :=
    List.mem_dedup.mpr (mem_licensedValues.mpr ⟨o₂, h₂, l₂, rfl⟩)
  unfold accept
  simp only [hne0, if_false]
  rcases hd : (licensedValues os).dedup with _ | ⟨a, _ | ⟨b, t⟩⟩
  · rw [hd] at hv₁; simp at hv₁
  · rw [hd] at hv₁ hv₂
    simp at hv₁ hv₂
    exact absurd (hv₁.trans hv₂.symm) hne
  · rfl

/-- The planned path: the rule's answer, or the grammar's when no plan is
licensed.  `none` is a refusal. -/
def planned (grammar : Option V) (os : List (Outcome V)) : Option V :=
  match accept os with
  | .answered v => some v
  | .ambiguous => none
  | .refused => grammar
  | .fallthrough => grammar

/-- **Conservative over the grammar.**  With no licensed plan, the planned
path says exactly what the grammar says. -/
theorem planned_conservative (grammar : Option V) (os : List (Outcome V))
    (h : ∀ o ∈ os, o.licensed = false) :
    planned grammar os = grammar := by
  unfold planned accept
  by_cases h0 : os = []
  · simp [h0]
  · have hlv : licensedValues os = [] := by
      unfold licensedValues
      rw [List.map_eq_nil_iff, List.filter_eq_nil_iff]
      intro o ho; simp [h o ho]
    simp [h0, hlv]

/-- **Sound.**  Whatever the planned path says was said by a licensed plan
or by the grammar. -/
theorem planned_sound (grammar : Option V) (os : List (Outcome V)) (v : V)
    (h : planned grammar os = some v) :
    (∃ o ∈ os, o.licensed = true ∧ o.value = v) ∨ grammar = some v := by
  unfold planned at h
  cases ha : accept os with
  | answered w =>
    rw [ha] at h
    cases h
    exact Or.inl ((accept_eq_answered_iff os _).mp ha).1
  | ambiguous => rw [ha] at h; cases h
  | refused => rw [ha] at h; exact Or.inr h
  | fallthrough => rw [ha] at h; exact Or.inr h

/-- **It refuses what the grammar answered only on a disagreement.** -/
theorem planned_refuses_only_on_disagreement (os : List (Outcome V)) (w : V)
    (h : planned (some w) os = none) :
    ∃ o₁ ∈ os, ∃ o₂ ∈ os, o₁.licensed = true ∧ o₂.licensed = true ∧
      o₁.value ≠ o₂.value := by
  unfold planned at h
  cases ha : accept os with
  | answered v => rw [ha] at h; cases h
  | refused => rw [ha] at h; cases h
  | fallthrough => rw [ha] at h; cases h
  | ambiguous =>
    by_contra hno
    push_neg at hno
    have h0 : os ≠ [] := by rintro rfl; simp [accept] at ha
    unfold accept at ha
    simp only [h0, if_false] at ha
    rcases hd : (licensedValues os).dedup with _ | ⟨a, _ | ⟨b, t⟩⟩
    · rw [hd] at ha; cases ha
    · rw [hd] at ha; cases ha
    · have hnd := List.nodup_dedup (licensedValues os)
      rw [hd] at hnd
      have ha' : a ∈ (licensedValues os).dedup := by rw [hd]; simp
      have hb' : b ∈ (licensedValues os).dedup := by rw [hd]; simp
      obtain ⟨o₁, h₁, l₁, rfl⟩ := mem_licensedValues.mp (List.mem_dedup.mp ha')
      obtain ⟨o₂, h₂, l₂, rfl⟩ := mem_licensedValues.mp (List.mem_dedup.mp hb')
      simp at hnd
      exact hnd.1.1 (hno o₁ h₁ o₂ h₂ l₁ l₂)

/-! ## The obvious rule, and why it is not the one shipped -/

/-- Take the first licensed plan's value. -/
def firstLicensed (os : List (Outcome V)) : Option V :=
  (os.find? (fun o => o.licensed)).map (fun o => o.value)

/-- The torque question: the extended-vector check says `false`, the SI
projection says `true`. -/
def torqueReadings : List (Outcome Bool) :=
  [⟨true, false⟩, ⟨true, true⟩]

/-- **The first licensed plan depends on the order the frames ran in.** -/
theorem first_licensed_order_dependent :
    torqueReadings.Perm torqueReadings.reverse ∧
      firstLicensed torqueReadings ≠ firstLicensed torqueReadings.reverse := by
  refine ⟨List.reverse_perm _ |>.symm, ?_⟩
  decide

/-- **And it answers a question whose two readings disagree**, where the
shipped rule refuses. -/
theorem first_licensed_answers_a_disagreement :
    firstLicensed torqueReadings = some false ∧
      accept torqueReadings = .ambiguous := by
  decide

end GLM.SemanticPlan
