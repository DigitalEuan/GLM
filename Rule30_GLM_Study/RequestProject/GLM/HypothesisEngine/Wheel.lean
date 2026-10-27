module

public import Mathlib

/-!
# Round 46: the contract of the v18 wheel

Engine v18 (`glm_engine/hypothesis_engine.py`, self-contained) puts every claim on a wheel with
three rings — KNOWS, THINKS-TRUE, DOESN'T-KNOW — plus a NEEDS ring and a LANGUAGE wheel, and it can
TURN a previous wheel: re-gate every entry and merge what is known. Its conjecture loop lifts a
bound from development data, reads it at larger scales, and re-lifts after a flip. This file
states and proves what those mechanisms guarantee. Everything here is FORMAL (no `native_decide`).

## 1. Rings
* `assertion_isSome_iff` — a status asserts a truth value exactly when it is on the KNOWS ring;
* `thinksTrue_asserts_nothing` — "survives every read" asserts nothing (it is a need for a proof,
  not knowledge);
* `speak_sound` — speaking only from the language wheel of a sound wheel never utters a false
  sentence.

## 2. Turning a wheel
`merge old new` keeps every KNOWS entry of the old wheel and takes the new status elsewhere.
* `merge_sound` — merging two sound wheels gives a sound wheel;
* `knows_merge` — the KNOWS ring after a turn contains the KNOWS rings of both wheels (knowledge
  never regresses), and `dontKnow_merge` — the DOESN'T-KNOW ring only shrinks;
* `conflict_unsound` — if the two wheels assert different values for a claim, one of them is
  unsound: a gate-versus-ledger conflict is an alarm, never something to resolve by voting.

## 3. The conjecture loop's arrow
For a bound family `∀ n, f n ≤ b`, the lift at scale `s` is the exact maximum of `f` on `[0, s]`.
* `lift_holds` — the lifted bound holds on its own data;
* `lift_mono` — lifts never go down as the scale grows;
* `lift_lt_of_fail` — when a read at a larger scale refutes the lifted bound, the re-lift is
  strictly larger: every flip moves the parameter in one direction (the loop's arrow);
* `relift_holds` — the re-lifted bound holds on everything read so far.
-/

@[expose] public section

namespace GLM.Wheel

/-- The statuses of engine v18, abstracted. -/
inductive Status
  | proved | verified | measured | refuted
  | survives | open_ | estimate | untested | unchecked | retracted
  deriving DecidableEq, Repr

/-- The three rings. -/
inductive Ring
  | knows | thinksTrue | dontKnow
  deriving DecidableEq, Repr

/-- The ring of a status (`ring_of` in the engine). -/
def ring : Status → Ring
  | .proved | .verified | .measured | .refuted => .knows
  | .survives => .thinksTrue
  | _ => .dontKnow

/-- What a status asserts about its claim (`answer_of` in the engine). -/
def assertion : Status → Option Bool
  | .proved | .verified | .measured => some true
  | .refuted => some false
  | _ => none

/-- A status asserts a truth value exactly when it is on the KNOWS ring. -/
theorem assertion_isSome_iff (s : Status) : (assertion s).isSome ↔ ring s = .knows := by
  cases s <;> simp [assertion, ring]

/-- "Survives every read" asserts nothing. -/
theorem thinksTrue_asserts_nothing {s : Status} (h : ring s = .thinksTrue) : assertion s = none := by
  cases s <;> simp_all [assertion, ring]

variable {α : Type*}

/-- A wheel assigns a status to every claim; it is sound if every assertion matches the truth. -/
def Sound (truth : α → Bool) (w : α → Status) : Prop :=
  ∀ a b, assertion (w a) = some b → truth a = b

/-- The language wheel: the claims of the KNOWS ring, each with the value it asserts. -/
def language (w : α → Status) (a : α) (b : Bool) : Prop := assertion (w a) = some b

/-- Speaking only from the language wheel of a sound wheel never utters a false sentence. -/
theorem speak_sound {truth : α → Bool} {w : α → Status} (hw : Sound truth w) {a : α} {b : Bool}
    (h : language w a b) : truth a = b :=
  hw a b h

/-- One turn: keep what the old wheel knows, take the new status everywhere else. -/
def merge (old new : α → Status) (a : α) : Status :=
  if ring (old a) = .knows then old a else new a

/-- Merging two sound wheels gives a sound wheel. -/
theorem merge_sound {truth : α → Bool} {old new : α → Status} (ho : Sound truth old)
    (hn : Sound truth new) : Sound truth (merge old new) := by
  intro a b h
  unfold merge at h
  split_ifs at h
  · exact ho a b h
  · exact hn a b h

/-- After a turn, the KNOWS ring contains the KNOWS rings of both wheels. -/
theorem knows_merge (old new : α → Status) (a : α) :
    ring (merge old new a) = .knows ↔ ring (old a) = .knows ∨ ring (new a) = .knows := by
  unfold merge
  split_ifs with h <;> simp [h]

/-- After a turn, the DOESN'T-KNOW ring has only shrunk (relative to the new wheel). -/
theorem dontKnow_merge (old new : α → Status) (a : α)
    (h : ring (merge old new a) = .dontKnow) : ring (new a) = .dontKnow := by
  unfold merge at h
  split_ifs at h with h'
  · rw [h'] at h; cases h
  · exact h

/-- Two wheels that assert different values for a claim cannot both be sound. -/
theorem conflict_unsound {truth : α → Bool} {w w' : α → Status} {a : α} {b b' : Bool}
    (h : assertion (w a) = some b) (h' : assertion (w' a) = some b') (hne : b ≠ b') :
    ¬ (Sound truth w ∧ Sound truth w') := by
  rintro ⟨hw, hw'⟩
  exact hne ((hw a b h).symm.trans (hw' a b' h'))

/-! ## The conjecture loop's arrow -/

/-- The lift of a bound family at scale `s`: the exact maximum of `f` on `[0, s]`. -/
def lift (f : ℕ → ℕ) (s : ℕ) : ℕ := (Finset.range (s + 1)).sup f

/-- The lifted bound holds on its own data. -/
theorem lift_holds (f : ℕ → ℕ) (s : ℕ) {n : ℕ} (hn : n ≤ s) : f n ≤ lift f s :=
  Finset.le_sup (f := f) (Finset.mem_range.2 (Nat.lt_succ_of_le hn))

/-- Lifts never go down as the scale grows. -/
theorem lift_mono (f : ℕ → ℕ) : Monotone (lift f) := by
  intro s t hst
  exact Finset.sup_mono (Finset.range_subset_range.2 (by omega))

/-- When a read at scale `t` refutes the bound lifted at scale `s`, the re-lift at `t` is
strictly larger: every flip of the loop moves the parameter up. -/
theorem lift_lt_of_fail (f : ℕ → ℕ) {s t n : ℕ} (hn : n ≤ t) (hfail : lift f s < f n) :
    lift f s < lift f t :=
  lt_of_lt_of_le hfail (lift_holds f t hn)

/-- The re-lifted bound holds on everything read so far. -/
theorem relift_holds (f : ℕ → ℕ) {s t : ℕ} (hst : s ≤ t) :
    (∀ n ≤ s, f n ≤ lift f t) ∧ ∀ n ≤ t, f n ≤ lift f t :=
  ⟨fun _ hn => lift_holds f t (le_trans hn hst), fun _ hn => lift_holds f t hn⟩

/-- A refuting read is never at a scale covered by the lift: the flip happens strictly above. -/
theorem fail_above (f : ℕ → ℕ) {s n : ℕ} (hfail : lift f s < f n) : s < n := by
  by_contra h
  exact absurd (lift_holds f s (not_lt.1 h)) (not_le.2 hfail)

end GLM.Wheel
