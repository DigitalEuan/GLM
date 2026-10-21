module

public import Mathlib.Data.List.Basic

/-!
# The evidence model in use: the replay gate (Phase 171)

*Created 20 October 2026.*

The formal half of `studies/EVIDENCE_IN_USE_STUDY.md`. The evaluation's replay
gate (`evaluation/replay.py`) reads every case the evaluation expects answered
into a row: whether the result model reads it as answered, and whether its
column 3 was replayed and verified (`some true`), replayed and failed
(`some false`), or absent (`none`, a surface with no column 3). A process error
is a row that is not answered.

* `gate_sound` — a passing gate leaves no failed replay and no unanswered row.
* `gate_fails_of_failed` — one failed replay, anywhere, fails the gate.
* `gate_absent_ok` — a row with no column 3 never fails the gate.
* `gate_append` — the gate on two batches passes exactly when every row of
  both is good and one of them replayed something.
* `read_keeps_answer` — reading a routed answer into a result keeps its text
  and its answered flag: the model adds no answer and removes none.
-/

@[expose] public section

namespace GLM.EvidenceInUse

/-- One replayed case: answered or not, and its replay. -/
structure Row where
  answered : Bool
  replayed : Option Bool

/-- A row the gate accepts: answered, and no replay that failed. -/
def Row.good (r : Row) : Bool := r.answered && r.replayed != some false

/-- A row whose column 3 ran. -/
def Row.replayable (r : Row) : Bool := r.replayed.isSome

/-- The gate: every row good, and at least one replay ran. -/
def gate (rows : List Row) : Bool := rows.all Row.good && rows.any Row.replayable

/-- **A passing gate leaves no failed replay and no unanswered row.** -/
theorem gate_sound {rows : List Row} (h : gate rows = true) :
    ∀ r ∈ rows, r.answered = true ∧ r.replayed ≠ some false := by
  intro r hr
  simp only [gate, Bool.and_eq_true, List.all_eq_true, List.any_eq_true] at h
  have := h.1 r hr
  simp only [Row.good, Bool.and_eq_true, bne_iff_ne, ne_eq] at this
  exact ⟨this.1, this.2⟩

/-- **One failed replay, anywhere, fails the gate.** -/
theorem gate_fails_of_failed {rows : List Row} {r : Row} (hr : r ∈ rows)
    (hf : r.replayed = some false) : gate rows = false := by
  by_contra h
  have h' : gate rows = true := by simpa using h
  exact (gate_sound h' r hr).2 hf

/-- **A row with no column 3 never fails the gate**: adding it to a passing
batch keeps the gate passing, if the row is answered. -/
theorem gate_absent_ok {rows : List Row} (h : gate rows = true) {r : Row}
    (ha : r.answered = true) (hn : r.replayed = none) :
    gate (r :: rows) = true := by
  simp only [gate, Bool.and_eq_true, List.all_eq_true, List.any_eq_true] at h ⊢
  refine ⟨?_, ?_⟩
  · intro x hx
    rcases List.mem_cons.mp hx with rfl | hx
    · simp [Row.good, ha, hn]
    · exact h.1 x hx
  · obtain ⟨x, hx, hxr⟩ := h.2
    exact ⟨x, List.mem_cons_of_mem _ hx, hxr⟩

/-- **The gate on two batches** passes exactly when every row of both is good
and one of the two replayed something. -/
theorem gate_append (a b : List Row) :
    gate (a ++ b) = ((a.all Row.good && b.all Row.good) &&
      (a.any Row.replayable || b.any Row.replayable)) := by
  simp [gate, List.all_append, List.any_append]

/-- A routed answer, as the surfaces return it. -/
structure Routed where
  text : String
  answered : Bool

/-- The result model's reading of a routed answer (the fields that carry the
answer; the others describe it). -/
structure Result where
  answer : String
  answered : Bool

/-- The reading. -/
def read (r : Routed) : Result := ⟨r.text, r.answered⟩

/-- **The model adds no answer and removes none.** -/
theorem read_keeps_answer (r : Routed) :
    (read r).answer = r.text ∧ (read r).answered = r.answered :=
  ⟨rfl, rfl⟩

end GLM.EvidenceInUse
