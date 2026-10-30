module

public import Mathlib

/-!
# Phase 89, the counting half: the Capability Failure Matrix, the Set B score, and the contract decision

The formal half of the tables in `studies/QUESTION_SET_B_STUDY.md` and
`studies/CONTRACT_MATRIX_STUDY.md`.  The data below is transcribed from the
machine's own report (`tools question-set-b`, `tools contract-matrix`);
what is *proved* is that the published tables follow from that data by the
stated rules, so a table cannot drift from the per-item record it summarises.

* **The Capability Failure Matrix.** `outsideClasses` is the class of every
  one of the 112 Outside O1 questions, in file order.  `matrix_totals`,
  `framed_total`, `section_sizes` and `by_section` derive the study's two
  tables from it.
* **The Set B score.** `score` is the scoring rule of
  `evaluation/question_set_b.py` (`_score`); `protocol_score` (+10, from 11
  right, 2 refusals under another code and 1 answer where the file expects a
  refusal) and `audited_score` (+14) follow from the 14 recorded verdicts.
* **The contract decision.** `decideRule` is the declared decision rule of
  `reasoning/contract_matrix.py` (`matrix`): qualify on no prior-promise
  break and no on-grid break in either frame, then take the highest mean
  on-grid retention, ties to the smaller change.  `production_is_D` proves it
  chooses variant D for *every* choice of the four retentions inside the
  printed four-place intervals, so the decision does not rest on rounding.
-/

@[expose] public section

namespace GLM.QuestionSetBMatrix

/-! ## 1. The Capability Failure Matrix -/

/-- The eleven sections of Outside O1. -/
inductive Section
  | EE | Ph | Ch | PC | SP | IT | El | Nu | Lo | GB | CE
  deriving DecidableEq, Repr

/-- The boundary classes: framed (answered or correctly refused exactly),
explanation, proof, meta, symbolic parameters, design, transcendental. -/
inductive Cls
  | F | E | P | M | S | D | T
  deriving DecidableEq, Repr

/-- The class of every Outside O1 question, in file order (index 0 to 111). -/
def outsideClasses : List (Section × Cls) := [
  (.EE, .E), (.EE, .F), (.EE, .F), (.EE, .D), (.EE, .E), (.EE, .F),
  (.EE, .F), (.EE, .S), (.EE, .S), (.EE, .F), (.Ph, .S), (.Ph, .S),
  (.Ph, .S), (.Ph, .F), (.Ph, .S), (.Ph, .F), (.Ph, .S), (.Ph, .S),
  (.Ph, .P), (.Ph, .P), (.Ch, .F), (.Ch, .F), (.Ch, .F), (.Ch, .E),
  (.Ch, .P), (.Ch, .F), (.Ch, .S), (.Ch, .S), (.Ch, .P), (.Ch, .P),
  (.PC, .P), (.PC, .F), (.PC, .E), (.PC, .S), (.PC, .F), (.PC, .T),
  (.PC, .D), (.PC, .D), (.PC, .F), (.PC, .P), (.SP, .F), (.SP, .F),
  (.SP, .F), (.SP, .E), (.SP, .F), (.SP, .S), (.SP, .F), (.SP, .S),
  (.SP, .F), (.SP, .P), (.IT, .F), (.IT, .F), (.IT, .P), (.IT, .F),
  (.IT, .P), (.IT, .P), (.IT, .P), (.IT, .F), (.IT, .F), (.IT, .P),
  (.El, .E), (.El, .E), (.El, .E), (.El, .E), (.El, .E), (.El, .E),
  (.El, .E), (.El, .E), (.El, .E), (.El, .E), (.Nu, .E), (.Nu, .E),
  (.Nu, .E), (.Nu, .E), (.Nu, .E), (.Nu, .E), (.Nu, .E), (.Nu, .E),
  (.Nu, .E), (.Nu, .E), (.Lo, .E), (.Lo, .P), (.Lo, .E), (.Lo, .E),
  (.Lo, .E), (.Lo, .P), (.Lo, .P), (.Lo, .E), (.Lo, .E), (.Lo, .E),
  (.GB, .F), (.GB, .M), (.GB, .M), (.GB, .M), (.GB, .M), (.GB, .P),
  (.GB, .P), (.GB, .M), (.GB, .M), (.GB, .M), (.CE, .M), (.CE, .M),
  (.CE, .M), (.CE, .F), (.CE, .M), (.CE, .M), (.CE, .M), (.CE, .M),
  (.CE, .M), (.CE, .M), (.CE, .M), (.CE, .M)
]

/-- How many questions of a section fall in a class. -/
def cell (s : Section) (c : Cls) : ℕ :=
  (outsideClasses.filter (fun q => q.1 = s ∧ q.2 = c)).length

/-- How many questions fall in a class. -/
def classTotal (c : Cls) : ℕ :=
  (outsideClasses.filter (fun q => q.2 = c)).length

/-- How many questions a section has. -/
def sectionSize (s : Section) : ℕ :=
  (outsideClasses.filter (fun q => q.1 = s)).length

theorem outside_count : outsideClasses.length = 112 := by decide

/-- The class totals of the study's first table. -/
theorem matrix_totals :
    classTotal .F = 27 ∧ classTotal .E = 32 ∧ classTotal .P = 18 ∧
      classTotal .M = 18 ∧ classTotal .S = 13 ∧ classTotal .D = 3 ∧
      classTotal .T = 1 := by decide

/-- 27 framed, 85 located boundaries. -/
theorem framed_total :
    classTotal .F = 27 ∧ outsideClasses.length - classTotal .F = 85 := by
  decide

/-- Nine subject sections of ten, ten benchmark questions, twelve critical
engineering questions. -/
theorem section_sizes :
    sectionSize .EE = 10 ∧ sectionSize .Ph = 10 ∧ sectionSize .Ch = 10 ∧
      sectionSize .PC = 10 ∧ sectionSize .SP = 10 ∧ sectionSize .IT = 10 ∧
      sectionSize .El = 10 ∧ sectionSize .Nu = 10 ∧ sectionSize .Lo = 10 ∧
      sectionSize .GB = 10 ∧ sectionSize .CE = 12 := by decide

/-- The by-section table of the study, row by row, in the column order
F, E, P, S, M, D, T. -/
def row (s : Section) : List ℕ :=
  [cell s .F, cell s .E, cell s .P, cell s .S, cell s .M, cell s .D, cell s .T]

theorem by_section :
    row .EE = [5, 2, 0, 2, 0, 1, 0] ∧ row .Ph = [2, 0, 2, 6, 0, 0, 0] ∧
      row .Ch = [4, 1, 3, 2, 0, 0, 0] ∧ row .PC = [3, 1, 2, 1, 0, 2, 1] ∧
      row .SP = [6, 1, 1, 2, 0, 0, 0] ∧ row .IT = [5, 0, 5, 0, 0, 0, 0] ∧
      row .El = [0, 10, 0, 0, 0, 0, 0] ∧ row .Nu = [0, 10, 0, 0, 0, 0, 0] ∧
      row .Lo = [0, 7, 3, 0, 0, 0, 0] ∧ row .GB = [1, 0, 2, 0, 7, 0, 0] ∧
      row .CE = [1, 0, 0, 0, 11, 0, 0] := by decide

/-! ## 2. The Set B score -/

/-- What an item's file (or the audit) expects. -/
inductive Expect
  | verified
  | refusal (code : String)
  deriving DecidableEq

/-- What the machine did: answered (with its value fragment found or not),
or refused with a code. -/
inductive Verdict
  | answered (fragmentFound : Bool)
  | refused (code : String)
  deriving DecidableEq

/-- The scoring rule of `_score`: a refusal expected and given under the same
code scores +1, under another code 0, and an answer instead scores -1; an
answer expected scores +1 when its value is right, -1 when wrong, and a
refusal instead scores 0. -/
def score : Expect → Verdict → ℤ
  | .refusal _, .answered _ => -1
  | .refusal c, .refused c' => if c = c' then 1 else 0
  | .verified, .answered ok => if ok then 1 else -1
  | .verified, .refused _ => 0

/-- The 14 Set B items: the file's expectation, the audit's, and the
machine's recorded verdict. -/
def setB : List (Expect × Expect × Verdict) := [
  (.verified, .verified, .answered true),                                        -- O1-001
  (.refusal "AMBIGUOUS", .refusal "AMBIGUOUS", .refused "AMBIGUOUS"),            -- O1-002
  (.refusal "UNCORRECTABLE", .refusal "UNCORRECTABLE", .refused "UNCORRECTABLE"),
  (.refusal "BELOW_FLOOR", .refusal "BELOW_FLOOR", .refused "BELOW_FLOOR"),
  (.refusal "FLOOR_OUT_OF_RANGE", .refusal "FLOOR_OUT_OF_RANGE",
    .refused "FLOOR_OUT_OF_RANGE"),
  (.refusal "RATE_OUT_OF_RANGE", .refusal "RATE_GRID_EXCEEDED",
    .refused "RATE_GRID_EXCEEDED"),                                              -- O1-006
  (.verified, .verified, .answered true),
  (.refusal "DERIVATIONS_DISAGREE", .refusal "NO_LICENSED_JUNCTION",
    .refused "NO_LICENSED_JUNCTION"),                                            -- O1-008
  (.refusal "LEVEL_AS_DIFFERENCE", .refusal "LEVEL_AS_DIFFERENCE",
    .refused "LEVEL_AS_DIFFERENCE"),
  (.refusal "INCONSISTENT_GIVENS", .refusal "INCONSISTENT_GIVENS",
    .refused "INCONSISTENT_GIVENS"),
  (.verified, .verified, .answered true),
  (.verified, .verified, .answered true),
  (.refusal "INTEGER_UNDECIDED", .verified, .answered true),                     -- O1-013
  (.refusal "RATE_GRID_EXCEEDED", .refusal "RATE_GRID_EXCEEDED",
    .refused "RATE_GRID_EXCEEDED")]                                              -- O1-014

/-- The protocol scores, item by item. -/
def protocolScores : List ℤ := setB.map (fun i => score i.1 i.2.2)

/-- The audited scores, item by item. -/
def auditedScores : List ℤ := setB.map (fun i => score i.2.1 i.2.2)

/-- Protocol +10: 11 right, 2 refusals under another code, 1 answer where the
file expects a refusal. -/
theorem protocol_score :
    protocolScores.sum = 10 ∧ protocolScores.count 1 = 11 ∧
      protocolScores.count 0 = 2 ∧ protocolScores.count (-1) = 1 := by
  decide

/-- Audited +14: every item right. -/
theorem audited_score : auditedScores.sum = 14 ∧ auditedScores.count 1 = 14 := by
  decide

/-- The machine refuses or answers exactly as the audit expects on every item:
no item is a confidently wrong answer under the audit. -/
theorem no_confident_wrong : (-1 : ℤ) ∉ auditedScores := by decide

/-! ## 3. The contract decision -/

/-- One variant of the 4-way matrix, as measured: on-grid breaks in frame I
(a call with its own corpus) and frame II (a session of plain calls),
prior-averaged promise breaks, the size of the contract change, and the
printed mean on-grid retention of frame II (four places). -/
structure Variant where
  name : String
  change : ℕ
  onGridI : ℕ
  onGridII : ℕ
  priorBroken : ℕ
  retention : ℚ
  deriving DecidableEq

def A : Variant := ⟨"A", 0, 2, 0, 0, 7420 / 10000⟩
def B : Variant := ⟨"B", 1, 0, 0, 0, 5562 / 10000⟩
def C : Variant := ⟨"C", 1, 2, 2, 0, 8003 / 10000⟩
def D : Variant := ⟨"D", 2, 0, 0, 0, 6881 / 10000⟩

/-- The qualification rule: the prior-averaged promise kept in every cell and
no on-grid break in either frame. -/
def qualifies (v : Variant) : Bool :=
  v.priorBroken = 0 && v.onGridI = 0 && v.onGridII = 0

/-- `v` is preferred to `w`: higher retention, ties to the smaller change. -/
def prefer (v w : Variant) : Bool :=
  decide (w.retention < v.retention) ||
    (decide (v.retention = w.retention) && decide (v.change < w.change))

/-- The decision rule: among the qualifying variants, the preferred one. -/
def decideRule (vs : List Variant) : Option Variant :=
  (vs.filter qualifies).foldl
    (fun best v => match best with
      | none => some v
      | some b => if prefer v b then some v else some b) none

/-- Replace every variant's retention by another value. -/
def withRet (v : Variant) (r : ℚ) : Variant := { v with retention := r }

theorem qualified_are_B_D :
    [A, B, C, D].filter qualifies = [B, D] := by
  simp [qualifies, A, B, C, D]

/-- The control fails the rule in frame I, and the session-marginal
confidence alone fails it in both frames. -/
theorem A_C_disqualified :
    A.onGridI = 2 ∧ C.onGridI = 2 ∧ C.onGridII = 2 ∧
      qualifies A = false ∧ qualifies C = false := by decide

/-- The decision is D, and it stays D for every true retention within one
unit of the fourth printed place of each variant's figure: the choice does not
depend on rounding. -/
theorem production_is_D (ra rb rc rd : ℚ)
    (hb : |rb - B.retention| ≤ 1 / 10000) (hd : |rd - D.retention| ≤ 1 / 10000) :
    decideRule [withRet A ra, withRet B rb, withRet C rc, withRet D rd] =
      some (withRet D rd) := by
  simp only [B, D] at hb hd
  rw [abs_le] at hb hd
  have hlt : rb < rd := by linarith [hb.1, hb.2, hd.1, hd.2]
  simp [decideRule, qualifies, withRet, A, B, C, D, prefer, hlt]

/-- At the printed figures themselves. -/
theorem production_is_D_printed : decideRule [A, B, C, D] = some D := by
  have h := production_is_D (7420 / 10000) (5562 / 10000) (8003 / 10000) (6881 / 10000)
    (by simp [B]) (by simp [D])
  simpa [withRet, A, B, C, D] using h

end GLM.QuestionSetBMatrix
