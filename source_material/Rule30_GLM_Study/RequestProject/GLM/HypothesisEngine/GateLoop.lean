module

public import Mathlib

/-!
# Round 45: the contract of the v17 gate loop

Engine v17 (`rule30_round45/hypothesis_engine_v17.py`) runs a cascade of gates after every stage,
reads claims at five layers, escalates before it speaks, and retracts dependent claims when a
claim is refuted. This file states and proves what those mechanisms guarantee, and where the v16
versions went wrong. Everything here is FORMAL (no `native_decide`).

## 1. Layered reads on nested domains
A claim `P` is read at layer `k` on the domain `dom k`; v17's domains grow with `k`.
* `holdsAt_anti` — the layers at which a universal claim holds form a prefix;
* `holdsAll_iff_top` — so it holds at every layer iff it holds at the largest one;
* `firstFail_spec` — the first failing layer is well defined, with every layer below passing and
  every layer from it on failing (`refuted_stable`): reading higher never undoes a refutation;
* `anyScale_vacuous`, `anyScale_ne_largest` — v16's "explained at ANY layer" rule is satisfied
  by any layer with no data, and can disagree with the verdict at the largest layer;
* `exclusive_mono` — for an "only at `S`" claim, loosening `S` can only help: the passing layers
  form a suffix, and the claim as stated is the tightest layer.

## 2. Escalate before assert
* `escalate` reads a list of scales and stops at the first failing one;
* `escalate_eq_some` — a reported failure is a real counterexample (`escalate_refutes`);
* `escalate_eq_none` — no failure means the claim holds on every scale read, and nothing more:
  `finite_range_never_proves_forall` shows survival to any `N` is compatible with failure;
* `escalate_append` — extending the ladder never undoes a refutation already found;
* `reads_prefix`, `reads_sorted` — **the arrow**: the scales read are an initial segment of the
  ladder, so on an increasing ladder the read position never goes down.

## 3. Typed transitive rollback
`dep c p` means "the claim `c` uses the claim `p`". `Retracted dep R` is everything that depends,
through any chain, on a refuted claim in `R`.
* `subset_retracted`, `retracted_closed`, `retracted_least` — the least dependency-closed set
  containing `R`;
* `retracted_union`, `retracted_idem` — order does not matter: processing refutations one at a
  time, in any order, gives the same retracted set;
* `rollback_sound` — if every dependency edge is truthful (a true child has a true parent),
  rollback never retracts a true claim;
* `derived_edge_unsound` — propagating along a *derived* edge (a narrowed claim from its refuted
  parent) would retract a true claim; v17 propagates along dependency edges only;
* `loop_eq_retracted`, `loop_terminates` — the engine's loop (add every child of the current set
  until nothing changes) stops on a finite set of claims, and its result is exactly `Retracted`.

## 4. The gate cascade
A verdict is `proved`, `refuted` or `none`. A gate is sound if it keeps sound verdicts sound.
* `cascade_sound` — a cascade of sound gates, started from a sound verdict, is sound: it never
  calls a true claim refuted or a false claim proved;
* `cascade_no_wrong` — so a run scored right / wrong / overclaim / abstain has no wrong answers;
* `survives_as_proved_unsound` — v16's reading "survived the data ⇒ true" is not a sound gate.
-/

@[expose] public section

namespace GLM.GateLoop

open Relation

variable {α : Type*}

/-! ## 1. Layered reads on nested domains -/

/-- The claim `P` holds on the whole domain of layer `k`. -/
def HoldsAt (dom : ℕ → Set α) (P : α → Prop) (k : ℕ) : Prop := ∀ x ∈ dom k, P x

/-- On nested domains, a universal claim that holds at a layer holds at every lower layer. -/
theorem holdsAt_anti {dom : ℕ → Set α} (hmono : Monotone dom) {P : α → Prop} {k j : ℕ}
    (hkj : k ≤ j) (h : HoldsAt dom P j) : HoldsAt dom P k :=
  fun x hx => h x (hmono hkj hx)

/-- A universal claim holds at every layer up to `top` iff it holds at `top`. -/
theorem holdsAll_iff_top {dom : ℕ → Set α} (hmono : Monotone dom) {P : α → Prop} (top : ℕ) :
    (∀ k ≤ top, HoldsAt dom P k) ↔ HoldsAt dom P top :=
  ⟨fun h => h top le_rfl, fun h _ hk => holdsAt_anti hmono hk h⟩

/-- A refutation read at layer `k` is a refutation at every higher layer. -/
theorem refuted_stable {dom : ℕ → Set α} (hmono : Monotone dom) {P : α → Prop} {k j : ℕ}
    (hkj : k ≤ j) (h : ¬ HoldsAt dom P k) : ¬ HoldsAt dom P j :=
  fun hj => h (holdsAt_anti hmono hkj hj)

/-- The first failing layer: every layer below it passes, every layer from it on fails. -/
theorem firstFail_spec {dom : ℕ → Set α} (hmono : Monotone dom) {P : α → Prop}
    [DecidablePred (fun k => ¬ HoldsAt dom P k)] (h : ∃ k, ¬ HoldsAt dom P k) :
    (∀ k < Nat.find h, HoldsAt dom P k) ∧ ∀ k, Nat.find h ≤ k → ¬ HoldsAt dom P k := by
  refine ⟨fun k hk => ?_, fun k hk => refuted_stable hmono hk (Nat.find_spec h)⟩
  have := Nat.find_min h hk
  simpa using this

/-- v16's aggregation "explained at ANY layer" is satisfied as soon as one layer has no data,
whatever the claim. -/
theorem anyScale_vacuous (dom : ℕ → Set α) (h0 : dom 0 = ∅) (P : α → Prop) :
    ∃ k, HoldsAt dom P k :=
  ⟨0, fun x hx => by simp [h0] at hx⟩

/-- … and it can disagree with the verdict at the largest layer, even on nested domains. -/
theorem anyScale_ne_largest :
    ∃ (dom : ℕ → Set ℕ) (P : ℕ → Prop), Monotone dom ∧ (∃ k, HoldsAt dom P k) ∧
      ¬ HoldsAt dom P 4 := by
  refine ⟨fun k => {n | n < k}, fun n => n < 1, ?_, ⟨0, fun x hx => by simp at hx⟩, ?_⟩
  · intro a b hab x hx
    simp only [Set.mem_setOf_eq] at hx ⊢
    omega
  · intro h
    have := h 1 (by simp)
    omega

/-- Exclusivity "the feature `F` lies in `S r`": with `S` growing in `r`, a claim that holds at
radius `r` holds at every larger radius. -/
theorem exclusive_mono (S : ℕ → Set α) (hS : Monotone S) (F : Set α) {r s : ℕ} (hrs : r ≤ s)
    (hr : F ⊆ S r) : F ⊆ S s :=
  hr.trans (hS hrs)

/-! ## 2. Escalate before assert -/

/-- Read the scales in order; return the first one whose check fails. -/
def escalate (check : ℕ → Bool) : List ℕ → Option ℕ
  | [] => none
  | s :: ss => if check s then escalate check ss else some s

/-- The scales actually read: up to and including the first failure. -/
def reads (check : ℕ → Bool) : List ℕ → List ℕ
  | [] => []
  | s :: ss => if check s then s :: reads check ss else [s]

theorem escalate_eq_some {check : ℕ → Bool} {l : List ℕ} {s : ℕ} (h : escalate check l = some s) :
    s ∈ l ∧ check s = false := by
  induction l with
  | nil => simp [escalate] at h
  | cons a l ih =>
    simp only [escalate] at h
    split_ifs at h with ha
    · exact ⟨List.mem_cons_of_mem _ (ih h).1, (ih h).2⟩
    · cases h
      exact ⟨List.mem_cons_self, by simpa using ha⟩

theorem escalate_eq_none {check : ℕ → Bool} {l : List ℕ} (h : escalate check l = none) :
    ∀ s ∈ l, check s = true := by
  induction l with
  | nil => simp
  | cons a l ih =>
    simp only [escalate] at h
    split_ifs at h with ha
    · intro s hs
      rcases List.mem_cons.1 hs with rfl | hs
      · exact ha
      · exact ih h s hs

/-- With the check "the claim holds below the scale", a reported failure refutes the claim. -/
theorem escalate_refutes (P : ℕ → Prop) [DecidablePred P] {l : List ℕ} {s : ℕ}
    (h : escalate (fun s => decide (∀ n < s, P n)) l = some s) : ¬ ∀ n, P n := by
  intro hall
  have := (escalate_eq_some h).2
  simp only [decide_eq_false_iff_not] at this
  exact this fun n _ => hall n

/-- Surviving every scale up to `N` is compatible with the claim being false. -/
theorem finite_range_never_proves_forall (N : ℕ) :
    ∃ Q : ℕ → Prop, (∀ n < N, Q n) ∧ ¬ ∀ n, Q n :=
  ⟨fun n => n < N, fun _ h => h, fun h => lt_irrefl N (h N)⟩

/-- Extending the ladder never undoes a refutation already found. -/
theorem escalate_append (check : ℕ → Bool) (l l' : List ℕ) :
    escalate check (l ++ l') = (escalate check l).orElse fun _ => escalate check l' := by
  induction l with
  | nil => simp [escalate, Option.orElse]
  | cons a l ih =>
    simp only [List.cons_append, escalate]
    split_ifs
    · exact ih
    · rfl

/-- The scales read are an initial segment of the ladder. -/
theorem reads_prefix (check : ℕ → Bool) (l : List ℕ) : reads check l <+: l := by
  induction l with
  | nil => simp [reads]
  | cons a l ih =>
    simp only [reads]
    split_ifs
    · exact List.cons_prefix_cons.2 ⟨rfl, ih⟩
    · exact List.cons_prefix_cons.2 ⟨rfl, List.nil_prefix⟩

/-- **The arrow.** On an increasing ladder, the read position never goes down. -/
theorem reads_sorted (check : ℕ → Bool) {l : List ℕ} (hl : l.Pairwise (· ≤ ·)) :
    (reads check l).Pairwise (· ≤ ·) :=
  hl.sublist (reads_prefix check l).sublist

/-! ## 3. Typed transitive rollback -/

/-- Everything that depends, through a chain of dependency edges, on a claim in `R`. -/
def Retracted (dep : α → α → Prop) (R : Set α) : Set α :=
  {x | ∃ r ∈ R, ReflTransGen dep x r}

variable {dep : α → α → Prop}

theorem subset_retracted (R : Set α) : R ⊆ Retracted dep R :=
  fun r hr => ⟨r, hr, ReflTransGen.refl⟩

/-- A claim that depends on a retracted claim is retracted. -/
theorem retracted_closed {R : Set α} {c p : α} (hp : p ∈ Retracted dep R) (hcp : dep c p) :
    c ∈ Retracted dep R := by
  obtain ⟨r, hr, hpr⟩ := hp
  exact ⟨r, hr, ReflTransGen.head hcp hpr⟩

/-- `Retracted dep R` is the least dependency-closed set containing `R`. -/
theorem retracted_least {R T : Set α} (hRT : R ⊆ T)
    (hT : ∀ c p, p ∈ T → dep c p → c ∈ T) : Retracted dep R ⊆ T := by
  rintro x ⟨r, hr, hxr⟩
  induction hxr using ReflTransGen.head_induction_on with
  | refl => exact hRT hr
  | head hcp _ ih => exact hT _ _ ih hcp

/-- Order independence: the retractions caused by two batches of refutations add up. -/
theorem retracted_union (R R' : Set α) :
    Retracted dep (R ∪ R') = Retracted dep R ∪ Retracted dep R' := by
  ext x
  simp only [Retracted, Set.mem_union, Set.mem_setOf_eq]
  constructor
  · rintro ⟨r, hr | hr, h⟩
    · exact Or.inl ⟨r, hr, h⟩
    · exact Or.inr ⟨r, hr, h⟩
  · rintro (⟨r, hr, h⟩ | ⟨r, hr, h⟩)
    · exact ⟨r, Or.inl hr, h⟩
    · exact ⟨r, Or.inr hr, h⟩

theorem retracted_idem (R : Set α) : Retracted dep (Retracted dep R) = Retracted dep R :=
  le_antisymm (retracted_least le_rfl fun _ _ hp hcp => retracted_closed hp hcp)
    (subset_retracted _)

/-- If every dependency edge is truthful (a true child has a true parent) and every claim in `R`
is false, rollback retracts only false claims. -/
theorem rollback_sound (truth : α → Prop) (hdep : ∀ c p, dep c p → truth c → truth p)
    {R : Set α} (hR : ∀ r ∈ R, ¬ truth r) : ∀ x ∈ Retracted dep R, ¬ truth x := by
  rintro x ⟨r, hr, hxr⟩
  induction hxr using ReflTransGen.head_induction_on with
  | refl => exact hR r hr
  | head hcp _ ih => exact fun hc => ih (hdep _ _ hcp hc)

/-- A derived edge is not truthful: the narrowed claim "every `n < 5` is `< 10`" is true while
its refuted parent "every `n` is `< 10`" is false. Propagating along it would retract a true
claim. -/
theorem derived_edge_unsound :
    (∀ n : ℕ, n < 5 → n < 10) ∧ ¬ (∀ n : ℕ, n < 10) :=
  ⟨fun _ h => by omega, fun h => by have := h 10; omega⟩

/-- One round of the engine's rollback loop: add every child of the current set. -/
def rollbackStep (dep : α → α → Prop) (S : Set α) : Set α := S ∪ {c | ∃ p ∈ S, dep c p}

theorem rollbackStep_mono : Monotone (rollbackStep dep) := by
  intro S T hST x hx
  rcases hx with hx | ⟨p, hp, hcp⟩
  · exact Or.inl (hST hx)
  · exact Or.inr ⟨p, hST hp, hcp⟩

theorem iterate_subset_retracted (R : Set α) (n : ℕ) :
    (rollbackStep dep)^[n] R ⊆ Retracted dep R := by
  induction n with
  | zero => exact subset_retracted R
  | succ n ih =>
    rw [Function.iterate_succ_apply']
    rintro x (hx | ⟨p, hp, hcp⟩)
    · exact ih hx
    · exact retracted_closed (ih hp) hcp

theorem le_iterate (R : Set α) (n : ℕ) : R ⊆ (rollbackStep dep)^[n] R := by
  induction n with
  | zero => exact le_rfl
  | succ n ih =>
    rw [Function.iterate_succ_apply']
    exact ih.trans Set.subset_union_left

/-- When the loop stops (nothing changes), its result is exactly `Retracted dep R`. -/
theorem loop_eq_retracted (R : Set α) (n : ℕ)
    (hfix : rollbackStep dep ((rollbackStep dep)^[n] R) = (rollbackStep dep)^[n] R) :
    (rollbackStep dep)^[n] R = Retracted dep R := by
  refine le_antisymm (iterate_subset_retracted R n) (retracted_least (le_iterate R n) ?_)
  intro c p hp hcp
  rw [← hfix]
  exact Or.inr ⟨p, hp, hcp⟩

/-- On finitely many claims the loop stops. -/
theorem loop_terminates [Finite α] (R : Set α) :
    ∃ n, rollbackStep dep ((rollbackStep dep)^[n] R) = (rollbackStep dep)^[n] R := by
  by_contra hne
  push_neg at hne
  have hlt : ∀ n, ((rollbackStep dep)^[n] R).ncard < ((rollbackStep dep)^[n + 1] R).ncard := by
    intro n
    rw [Function.iterate_succ_apply']
    exact Set.ncard_lt_ncard
      (HasSubset.Subset.ssubset_of_ne Set.subset_union_left (hne n).symm) (Set.toFinite _)
  have hge : ∀ n, n ≤ ((rollbackStep dep)^[n] R).ncard := by
    intro n
    induction n with
    | zero => exact Nat.zero_le _
    | succ n ih => exact lt_of_le_of_lt ih (hlt n)
  have hle := Set.ncard_le_card ((rollbackStep dep)^[Nat.card α + 1] R)
  have := hge (Nat.card α + 1)
  omega

/-! ## 4. The gate cascade -/

/-- What a status asserts about a claim. -/
inductive Verdict
  | proved
  | refuted
  | none
  deriving DecidableEq

/-- A verdict is sound for a claim of truth value `t` if it never contradicts `t`. -/
def SoundAt (t : Prop) : Verdict → Prop
  | .proved => t
  | .refuted => ¬ t
  | .none => True

/-- A gate reads a claim and the current verdict and returns a new verdict. It is sound if it
keeps sound verdicts sound. -/
def SoundGate (truth : α → Prop) (g : α → Verdict → Verdict) : Prop :=
  ∀ x v, SoundAt (truth x) v → SoundAt (truth x) (g x v)

/-- Run a list of gates in order. -/
def cascade (gs : List (α → Verdict → Verdict)) (x : α) (v : Verdict) : Verdict :=
  gs.foldl (fun v g => g x v) v

theorem cascade_sound (truth : α → Prop) (gs : List (α → Verdict → Verdict))
    (hgs : ∀ g ∈ gs, SoundGate truth g) (x : α) (v : Verdict) (hv : SoundAt (truth x) v) :
    SoundAt (truth x) (cascade gs x v) := by
  induction gs generalizing v with
  | nil => exact hv
  | cons g gs ih =>
    exact ih (fun g' hg' => hgs g' (List.mem_cons_of_mem _ hg'))
      (g x v) (hgs g List.mem_cons_self x v hv)

/-- A sound cascade never gives a wrong answer: no true claim refuted, no false claim proved. -/
theorem cascade_no_wrong (truth : α → Prop) (gs : List (α → Verdict → Verdict))
    (hgs : ∀ g ∈ gs, SoundGate truth g) (x : α) :
    (cascade gs x .none = .proved → truth x) ∧ (cascade gs x .none = .refuted → ¬ truth x) := by
  have h := cascade_sound truth gs hgs x .none trivial
  constructor
  · intro he
    rw [he] at h
    exact h
  · intro he
    rw [he] at h
    exact h

open Classical in
/-- v16's reading "the claim survived the data I have (`n < N`), so it is true" is not a sound
gate, for any amount of data `N`: the claim "every `n` is `< N`" survives the data and is false. -/
theorem survives_as_proved_unsound (N : ℕ) :
    ¬ SoundGate (fun Q : ℕ → Prop => ∀ n, Q n)
      (fun Q v => if ∀ n < N, Q n then Verdict.proved else v) := by
  intro h
  have := h (fun n => n < N) .none trivial
  have hs : (∀ n < N, (fun n => n < N) n) := fun _ h => h
  simp only [if_pos hs, SoundAt] at this
  exact lt_irrefl N (this N)

end GLM.GateLoop
