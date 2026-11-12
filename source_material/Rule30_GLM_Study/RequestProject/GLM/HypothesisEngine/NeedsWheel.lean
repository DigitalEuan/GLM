module

public import Mathlib

/-!
# Round 44: the needs wheel — what providing a tool can and cannot do

The owner's idea (`glm_wheel.py`): the engine says what it thinks it **needs**, and we supply those
things on a **wheel** it can use. This file states the contract that makes the effect of a wheel
measurable and safe.

A *provision* answers some questions and stays silent on the others: `α → Option Bool`
(`some b` = "the answer is `b`", `none` = "I cannot say"). The engine answers a question by asking
the provisions on the wheel in order and taking the first one that speaks; if none speaks it falls
back to its own base guess (for the engines of Rounds 38–43, "it survived the data I have").

A provision is **sound** for a ground truth `truth : α → Bool` when every answer it gives is
correct. Sound provisions are exactly the ones the engine should be given: a Lean theorem, a
finite certificate, an exact computation that decides the question.

* `answer_right_of_right` — adding sound provisions in front never loses a right answer;
* `answer_wrong_of_wrong` — and never creates a wrong one: every wrong answer of the extended
  engine was already wrong before;
* `card_wrong_le`, `card_right_le` — so on any finite task list the number of wrong answers can
  only go down and the number of right answers can only go up;
* `answer_local` — a provision changes nothing on questions where it is silent: the effect of a
  wheel is confined to the needs it serves (this is what lets a before/after measurement attribute
  a change to the provision that caused it);
* `answer_sound` — a sound base with a sound wheel never answers wrongly;
* `answer_perm` — among sound provisions the order on the wheel does not matter;
* `unsound_can_hurt` — the honest negative: one unsound provision can turn a right answer wrong,
  so "provide what it asks for" is only safe for provisions that are themselves checked.

Everything here is FORMAL (no `native_decide`).
-/

@[expose] public section

namespace GLM.NeedsWheel

variable {α : Type*}

/-- A provision answers a question with `some b`, or stays silent with `none`. -/
abbrev Provision (α : Type*) := α → Option Bool

/-- A provision is sound for `truth` if every answer it gives is correct. -/
def Sound (truth : α → Bool) (p : Provision α) : Prop := ∀ x b, p x = some b → b = truth x

/-- The engine with wheel `W` and base guess `base`: the first provision that speaks wins. -/
def answer : List (Provision α) → Provision α → Provision α
  | [], base => base
  | p :: W, base => fun x => match p x with
    | some b => some b
    | none => answer W base x

/-- The answer at `x` is right. -/
def Right (truth : α → Bool) (q : Provision α) (x : α) : Prop := q x = some (truth x)

/-- The answer at `x` is wrong. -/
def Wrong (truth : α → Bool) (q : Provision α) (x : α) : Prop := ∃ b, q x = some b ∧ b ≠ truth x

instance (truth : α → Bool) (q : Provision α) (x : α) : Decidable (Right truth q x) := by
  unfold Right; infer_instance

instance (truth : α → Bool) (q : Provision α) (x : α) : Decidable (Wrong truth q x) :=
  match h : q x with
  | none => isFalse (by rintro ⟨b, hb, -⟩; simp [h] at hb)
  | some b => if hb : b = truth x then isFalse (by rintro ⟨c, hc, hne⟩; simp [h] at hc; exact hne (hc ▸ hb))
    else isTrue ⟨b, h, hb⟩

theorem answer_nil (base : Provision α) : answer [] base = base := rfl

/-- What the engine says at `x`: the first speaking provision, else the base. -/
theorem answer_cons (p : Provision α) (W : List (Provision α)) (base : Provision α) (x : α) :
    answer (p :: W) base x = (match p x with | some b => some b | none => answer W base x) := rfl

/-- If all provisions on `W` are silent at `x`, the base decides. -/
theorem answer_of_silent {W : List (Provision α)} {base : Provision α} {x : α}
    (h : ∀ p ∈ W, p x = none) : answer W base x = base x := by
  induction W with
  | nil => rfl
  | cons p W ih =>
    rw [answer_cons, h p (by simp)]
    exact ih fun q hq => h q (by simp [hq])

/-- **Locality.** Provisions silent at `x` do not change the answer at `x`. -/
theorem answer_local {W V : List (Provision α)} {base : Provision α} {x : α}
    (h : ∀ p ∈ W, p x = none) : answer (W ++ V) base x = answer V base x := by
  induction W with
  | nil => rfl
  | cons p W ih =>
    rw [List.cons_append, answer_cons, h p (by simp)]
    exact ih fun q hq => h q (by simp [hq])

/-- With a sound wheel in front, the answer is either the truth or the old answer. -/
theorem answer_append_cases {truth : α → Bool} {W V : List (Provision α)} {base : Provision α}
    (hW : ∀ p ∈ W, Sound truth p) (x : α) :
    answer (W ++ V) base x = some (truth x) ∨ answer (W ++ V) base x = answer V base x := by
  induction W with
  | nil => exact Or.inr rfl
  | cons p W ih =>
    rw [List.cons_append, answer_cons]
    cases hp : p x with
    | some b => exact Or.inl (by rw [hW p (by simp) x b hp])
    | none => exact ih fun q hq => hW q (by simp [hq])

/-- **Adding sound provisions never loses a right answer.** -/
theorem answer_right_of_right {truth : α → Bool} {W V : List (Provision α)}
    {base : Provision α} (hW : ∀ p ∈ W, Sound truth p) {x : α}
    (h : Right truth (answer V base) x) : Right truth (answer (W ++ V) base) x := by
  unfold Right at *
  rcases answer_append_cases (base := base) (V := V) hW x with h' | h'
  · exact h'
  · rw [h', h]

/-- **Adding sound provisions never creates a wrong answer.** -/
theorem answer_wrong_of_wrong {truth : α → Bool} {W V : List (Provision α)}
    {base : Provision α} (hW : ∀ p ∈ W, Sound truth p) {x : α}
    (h : Wrong truth (answer (W ++ V) base) x) : Wrong truth (answer V base) x := by
  obtain ⟨b, hb, hne⟩ := h
  rcases answer_append_cases (base := base) (V := V) hW x with h' | h'
  · rw [h'] at hb; exact absurd (Option.some_injective _ hb).symm hne
  · exact ⟨b, h' ▸ hb, hne⟩

/-- **On a finite task list, wrong answers can only go down.** -/
theorem card_wrong_le [DecidableEq α] {truth : α → Bool} {W V : List (Provision α)}
    {base : Provision α} (hW : ∀ p ∈ W, Sound truth p) (T : Finset α) :
    (T.filter (Wrong truth (answer (W ++ V) base))).card ≤
      (T.filter (Wrong truth (answer V base))).card :=
  Finset.card_le_card fun x hx => by
    simp only [Finset.mem_filter] at hx ⊢
    exact ⟨hx.1, answer_wrong_of_wrong hW hx.2⟩

/-- **On a finite task list, right answers can only go up.** -/
theorem card_right_le [DecidableEq α] {truth : α → Bool} {W V : List (Provision α)}
    {base : Provision α} (hW : ∀ p ∈ W, Sound truth p) (T : Finset α) :
    (T.filter (Right truth (answer V base))).card ≤
      (T.filter (Right truth (answer (W ++ V) base))).card :=
  Finset.card_le_card fun x hx => by
    simp only [Finset.mem_filter] at hx ⊢
    exact ⟨hx.1, answer_right_of_right hW hx.2⟩

/-- **A sound base with a sound wheel never answers wrongly.** -/
theorem answer_sound {truth : α → Bool} {W : List (Provision α)} {base : Provision α}
    (hW : ∀ p ∈ W, Sound truth p) (hb : Sound truth base) : Sound truth (answer W base) := by
  intro x b h
  have := answer_append_cases (V := []) (base := base) hW x
  rw [List.append_nil] at this
  rcases this with h' | h'
  · rw [h'] at h; exact (Option.some_injective _ h).symm
  · rw [h'] at h; exact hb x b h

/-- The answer of a sound wheel: the truth if some provision speaks, else the fallback. -/
theorem answer_eq_of_sound {truth : α → Bool} {W V : List (Provision α)} {base : Provision α}
    (hW : ∀ p ∈ W, Sound truth p) (x : α) :
    answer (W ++ V) base x =
      if ∃ p ∈ W, p x ≠ none then some (truth x) else answer V base x := by
  split_ifs with h
  · obtain ⟨p, hp, hpx⟩ := h
    induction W with
    | nil => simp at hp
    | cons q W ih =>
      rw [List.cons_append, answer_cons]
      cases hq : q x with
      | some b => rw [hW q (by simp) x b hq]
      | none =>
        have hp' : p ∈ W := by
          rcases List.mem_cons.1 hp with rfl | h'
          · exact absurd hq hpx
          · exact h'
        exact ih (fun r hr => hW r (by simp [hr])) hp'
  · push_neg at h
    exact answer_local h

/-- **Order does not matter among sound provisions.** -/
theorem answer_perm {truth : α → Bool} {W W' V : List (Provision α)} {base : Provision α}
    (hW : ∀ p ∈ W, Sound truth p) (hperm : W.Perm W') (x : α) :
    answer (W ++ V) base x = answer (W' ++ V) base x := by
  have hW' : ∀ p ∈ W', Sound truth p := fun p hp => hW p (hperm.mem_iff.2 hp)
  rw [answer_eq_of_sound hW, answer_eq_of_sound hW']
  have : (∃ p ∈ W, p x ≠ none) ↔ (∃ p ∈ W', p x ≠ none) := by
    constructor
    · rintro ⟨p, hp, h⟩; exact ⟨p, hperm.mem_iff.1 hp, h⟩
    · rintro ⟨p, hp, h⟩; exact ⟨p, hperm.mem_iff.2 hp, h⟩
  simp only [this]

/-- **The honest negative.** One unsound provision can turn a right answer into a wrong one. -/
theorem unsound_can_hurt :
    ∃ (truth : Unit → Bool) (p base : Provision Unit),
      Right truth (answer [] base) () ∧ Wrong truth (answer [p] base) () :=
  ⟨fun _ => true, fun _ => some false, fun _ => some true, rfl, ⟨false, rfl, by decide⟩⟩

/-- **Why "survived the data" is not a sound provision for infinitary questions.** Any finite
prefix of a 0/1 sequence (for example the first `n` bits of Rule 30's centre column) is shared by a
sequence with only finitely many `1`s and by a sequence with infinitely many `1`s. So no rule that
looks only at finitely many bits can soundly answer "are there infinitely many `1`s?" — such a
question must stay OPEN unless a proof is provided. -/
theorem finite_data_never_forces_infinitely_many (f : ℕ → Bool) (n : ℕ) :
    (∃ g : ℕ → Bool, (∀ i < n, g i = f i) ∧ {i | g i = true}.Finite) ∧
    (∃ h : ℕ → Bool, (∀ i < n, h i = f i) ∧ {i | h i = true}.Infinite) := by
  refine ⟨⟨fun i => if i < n then f i else false, fun i hi => by simp [hi], ?_⟩,
    ⟨fun i => if i < n then f i else true, fun i hi => by simp [hi], ?_⟩⟩
  · apply (Set.finite_lt_nat n).subset
    intro i hi
    by_contra h
    simp_all
  · intro hfin
    obtain ⟨m, hm⟩ := hfin.bddAbove
    have h1 : n + m + 1 ∈ {i | (if i < n then f i else true) = true} := by
      simp only [Set.mem_setOf_eq, if_neg (show ¬ (n + m + 1 < n) by omega)]
    have h2 := hm h1
    omega

end GLM.NeedsWheel
