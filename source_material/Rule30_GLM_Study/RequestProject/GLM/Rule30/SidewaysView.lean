module

public import RequestProject.GLM.Rule30.HalfLineMachine

/-!
# Round 31: the sideways observer — reading the half-line machine from the column outwards

The half-line machine of Round 21 (`halfStateD`, `dDiesBy`, `HalfLineDies`) is read **forwards in
time**: a row of `d` cells evolves while a periodic column drives it, and the machine dies when a
check fails.  Rule 30 is *left-permutive* (`new = L xor (C or R)` can be solved for `L`), so the
same space–time picture can also be read **sideways**: knowing two neighbouring columns for all
times determines the column to their left,

  `K (k+2) t = K (k+1) (t+1) xor (K (k+1) t || K k t)`.

This is the observer `Y` turned through 90°: it stands on the driving column and looks outwards
(leftwards) along the rows, instead of looking up the time axis.

* `recon bd u` — the sideways reconstruction: column `0` is the drive `bd`, column `1` is a chosen
  sequence `u` (the cell next to the drive), and every further column is forced.
* `Admissible bd u` — `u` passes every check: at a black drive time `t`, `u t = !bd (t+1)`
  (`col_black_forces_left`).  At white drive times `u` is free.
* **`survives_iff_sideways`** (exact, every drive, every code): the machine started from code `S`
  never fails **iff** some admissible `u` reconstructs the row `S` at time `0`
  (`S.testBit i = recon bd u (i+1) 0` for every `i`).
* **`halfLineDies_iff_sideways`**: hence `HalfLineDies p` is *exactly* the statement that, for
  every non-white drive word of length `p`, no admissible `u` reconstructs a row with finitely
  many (and at least one) black cells.  The open rung is a statement about which rows the
  sideways reader can reach.
* **`halfLineDies_one_sideways`**: the period-1 rung in one line of the sideways view — with
  no white drive times the admissible column is forced, and the forced row `0101…` is infinite.
  (For every other word the white drive times leave one free bit each; that freedom is exactly
  what an open rung has to control.)
* **`infinite_row_survives`** (blocked route, To Do 20): if the row is allowed infinitely many
  black cells, the machine survives **forever, for every drive** — the sideways reader with
  `u t = !bd (t+1)` produces such a row.  So any argument that never uses the finiteness of the
  row (for example a finite quotient that only looks at a bounded window next to the column and
  treats the far cells as free) cannot prove `HalfLineDies p` for any `p`.
* `survivor_for_every_horizon`: for every drive and every horizon `T` there is a finite code
  (of length `T + 2`) that survives `T` steps, so no bound on the death time independent of the
  code length exists.

Everything here is exact Boolean / natural-number arithmetic; there are no finite checks.
-/

@[expose] public section

namespace GLM.Rule30

/-- **The sideways reconstruction.** Column `0` is the drive, column `1` is `u`, and column
`k + 2` is forced by left-permutivity of Rule 30. -/
def recon (bd u : ℕ → Bool) : ℕ → ℕ → Bool
  | 0, t => bd t
  | 1, t => u t
  | k + 2, t => xor (recon bd u (k + 1) (t + 1)) (recon bd u (k + 1) t || recon bd u k t)

/-- The cell next to the drive passes every check of the driven machine. -/
def Admissible (bd u : ℕ → Bool) : Prop := ∀ t, bd t = true → u t = !bd (t + 1)

/-- Left-permutivity, read forwards: the reconstructed columns obey Rule 30. -/
theorem recon_rule (bd u : ℕ → Bool) (k t : ℕ) :
    recon bd u (k + 1) (t + 1) =
      xor (recon bd u (k + 2) t) (recon bd u (k + 1) t || recon bd u k t) := by
  simp only [recon]
  rw [Bool.xor_assoc, Bool.xor_self, Bool.xor_false]

/-- If an infinite row (bit `i` = cell `c - 1 - i`) is the time-`0` slice of the reconstruction,
then the driven machine follows the reconstruction at every time. -/
theorem halfStateD_testBit_recon (bd u : ℕ → Bool) (S : ℕ)
    (hS : ∀ i, S.testBit i = recon bd u (i + 1) 0) :
    ∀ t i, (halfStateD bd S t).testBit i = recon bd u (i + 1) t := by
  intro t
  induction t with
  | zero => exact hS
  | succ t ih =>
    intro i
    simp only [halfStateD]
    rw [testBit_halfStep, ih (i + 1), ih i]
    rcases i with _ | j
    · simp only [if_true]
      rw [recon_rule bd u 0 t]
      rfl
    · rw [if_neg (by omega), show j + 1 - 1 = j from rfl, ih j, recon_rule bd u (j + 1) t]

/-- Conversely, the columns of any driven machine are the sideways reconstruction from its own
drive and its own first column. -/
theorem recon_of_halfStateD (bd : ℕ → Bool) (S : ℕ) :
    ∀ i t, recon bd (fun s => (halfStateD bd S s).testBit 0) (i + 1) t =
      (halfStateD bd S t).testBit i := by
  intro i
  induction i using Nat.strong_induction_on with
  | _ i ih =>
    intro t
    match i, ih with
    | 0, _ => rfl
    | 1, _ =>
      have h := testBit_halfStep (bd t) (halfStateD bd S t) 0
      simp only [if_true] at h
      show xor _ (_ || _) = _
      simp only [recon]
      rw [show halfStep (bd t) (halfStateD bd S t) = halfStateD bd S (t + 1) from rfl] at h
      rw [h]
      cases (halfStateD bd S t).testBit 1 <;> cases (halfStateD bd S t).testBit 0 <;>
        cases bd t <;> rfl
    | j + 2, ih =>
      have h := testBit_halfStep (bd t) (halfStateD bd S t) (j + 1)
      rw [show halfStep (bd t) (halfStateD bd S t) = halfStateD bd S (t + 1) from rfl,
        if_neg (by omega), show j + 1 - 1 = j from rfl] at h
      show xor (recon _ _ (j + 2) (t + 1)) (recon _ _ (j + 2) t || recon _ _ (j + 1) t) = _
      rw [ih (j + 1) (by omega) (t + 1), ih (j + 1) (by omega) t, ih j (by omega) t, h]
      cases (halfStateD bd S t).testBit (j + 2) <;> cases (halfStateD bd S t).testBit (j + 1) <;>
        cases (halfStateD bd S t).testBit j <;> rfl

/-- The machine never fails, written with `dDiesBy`. -/
def SurvivesForever (bd : ℕ → Bool) (S : ℕ) : Prop := ∀ T, dDiesBy bd S T = false

theorem survivesForever_iff (bd : ℕ → Bool) (S : ℕ) :
    SurvivesForever bd S ↔ ∀ t, bd t = true → (halfStateD bd S t).testBit 0 = !bd (t + 1) := by
  constructor
  · intro h t ht
    have h1 := h (t + 1)
    cases hb : (halfStateD bd S t).testBit 0 <;> cases hn : bd (t + 1)
    · exfalso
      have : dDiesBy bd S (t + 1) = true :=
        (dDiesBy_spec bd S (t + 1)).2 ⟨t, by omega, ht, by rw [hb, hn]⟩
      rw [this] at h1; exact Bool.noConfusion h1
    · rfl
    · rfl
    · exfalso
      have : dDiesBy bd S (t + 1) = true :=
        (dDiesBy_spec bd S (t + 1)).2 ⟨t, by omega, ht, by rw [hb, hn]⟩
      rw [this] at h1; exact Bool.noConfusion h1
  · intro h T
    cases hd : dDiesBy bd S T
    · rfl
    · exfalso
      obtain ⟨t, _, ht, hfail⟩ := (dDiesBy_spec bd S T).1 hd
      rw [h t ht] at hfail
      cases hb : bd (t + 1) <;> simp [hb] at hfail

/-- **The sideways reformulation of survival** (exact, for every drive and every code).
The driven machine started from `S` never fails iff some admissible first column `u`
reconstructs the row `S` at time `0`. -/
theorem survives_iff_sideways (bd : ℕ → Bool) (S : ℕ) :
    SurvivesForever bd S ↔
      ∃ u, Admissible bd u ∧ ∀ i, S.testBit i = recon bd u (i + 1) 0 := by
  rw [survivesForever_iff]
  constructor
  · intro h
    refine ⟨fun s => (halfStateD bd S s).testBit 0, h, fun i => ?_⟩
    rw [recon_of_halfStateD bd S i 0]
    rfl
  · rintro ⟨u, hu, hS⟩ t ht
    rw [halfStateD_testBit_recon bd u S hS t 0]
    exact hu t ht

/-- **`HalfLineDies p`, read sideways.** For every non-white drive word `k` of length `p` and
every admissible first column `u`, the reconstructed time-`0` row is not the row of a positive
code: it is either all white or has infinitely many black cells. -/
theorem halfLineDies_iff_sideways (p : ℕ) :
    HalfLineDies p ↔
      ∀ k, 0 < k → k < 2 ^ p → ∀ u, Admissible (driveN p k) u →
        ∀ S, 0 < S → ¬ ∀ i, S.testBit i = recon (driveN p k) u (i + 1) 0 := by
  constructor
  · intro h k hk0 hk1 u hu S hS hrow
    obtain ⟨T, hT⟩ := h k hk0 hk1 S hS
    have := (survives_iff_sideways _ S).2 ⟨u, hu, hrow⟩ T
    rw [hT] at this; exact Bool.noConfusion this
  · intro h k hk0 hk1 S hS
    by_contra hne
    push_neg at hne
    have hsurv : SurvivesForever (driveN p k) S := fun T => by
      cases hd : dDiesBy (driveN p k) S T
      · rfl
      · exact absurd hd (by simpa using hne T)
    obtain ⟨u, hu, hrow⟩ := (survives_iff_sideways _ S).1 hsurv
    exact h k hk0 hk1 u hu S hS hrow

/-! ## Period 1, read sideways -/

/-- Under the constant black drive the only admissible first column is all white, and the
sideways reader then produces the fixed row `0, 1, 0, 1, …` at every time. -/
theorem recon_constBlack (i t : ℕ) :
    recon (fun _ => true) (fun _ => false) (i + 1) t = decide (i % 2 = 1) := by
  induction i using Nat.strong_induction_on generalizing t with
  | _ i ih =>
    match i, ih with
    | 0, _ => rfl
    | 1, _ => rfl
    | j + 2, ih =>
      show xor (recon _ _ (j + 2) (t + 1)) (recon _ _ (j + 2) t || recon _ _ (j + 1) t) = _
      rw [ih (j + 1) (by omega) (t + 1), ih (j + 1) (by omega) t, ih j (by omega) t]
      rcases Nat.mod_two_eq_zero_or_one j with hj | hj <;>
        simp [hj, Nat.add_mod]

/-- **`HalfLineDies 1` in one line of the sideways view.** The admissible first column is forced
(`u = 0`), the reconstructed row is `0101…` with infinitely many black cells, so it is not a
finite code.  (Independent of the forwards proof `halfLineDies_one`.) -/
theorem halfLineDies_one_sideways : HalfLineDies 1 := by
  rw [halfLineDies_iff_sideways]
  intro k hk0 hk1 u hu S _ hrow
  obtain rfl : k = 1 := by omega
  have hd : driveN 1 1 = fun _ => true := by funext t; simp [driveN, Nat.mod_one]
  rw [hd] at hu hrow
  have hu0 : u = fun _ => false := by funext t; simpa using hu t rfl
  subst hu0
  -- an odd position beyond the length of `S`
  have h := hrow (2 * S + 1)
  rw [recon_constBlack, Nat.testBit_eq_false_of_lt] at h
  · simp at h
  · calc S < 2 ^ S := Nat.lt_two_pow_self
      _ ≤ 2 ^ (2 * S + 1) := Nat.pow_le_pow_right (by norm_num) (by omega)

/-! ## Infinite rows survive forever: finiteness of the row is essential -/

/-- One step of the half-line machine on an **infinite** row (bit `i` = cell `c - 1 - i`). -/
def halfStepInf (b : Bool) (σ : ℕ → Bool) : ℕ → Bool :=
  fun i => xor (σ (i + 1)) (σ i || (if i = 0 then b else σ (i - 1)))

/-- The infinite-row machine driven by `bd`. -/
def halfStateInf (bd : ℕ → Bool) (σ : ℕ → Bool) : ℕ → ℕ → Bool
  | 0 => σ
  | t + 1 => halfStepInf (bd t) (halfStateInf bd σ t)

/-- On finite codes the infinite-row machine is the Round 21 machine. -/
theorem halfStateInf_testBit (bd : ℕ → Bool) (S : ℕ) :
    ∀ t i, halfStateInf bd (fun i => S.testBit i) t i = (halfStateD bd S t).testBit i := by
  intro t
  induction t with
  | zero => intro i; rfl
  | succ t ih =>
    intro i
    simp only [halfStateInf, halfStateD, halfStepInf, testBit_halfStep, ih]

/-- The infinite-row machine started from the sideways row follows the reconstruction. -/
theorem halfStateInf_recon (bd u : ℕ → Bool) :
    ∀ t i, halfStateInf bd (fun i => recon bd u (i + 1) 0) t i = recon bd u (i + 1) t := by
  intro t
  induction t with
  | zero => intro i; rfl
  | succ t ih =>
    intro i
    simp only [halfStateInf, halfStepInf, ih]
    rcases i with _ | j
    · simp only [if_true]
      rw [recon_rule bd u 0 t]; rfl
    · simp only [Nat.add_eq_zero_iff, one_ne_zero, and_false, if_false, Nat.add_sub_cancel]
      rw [recon_rule bd u (j + 1) t]

/-- **Blocked route (To Do 20).** For **every** drive sequence there is an infinite row whose
machine passes every check forever.  So no argument that is insensitive to the finiteness of the
row — in particular no finite quotient that keeps a bounded window next to the column and treats
the far cells as free — can prove `HalfLineDies p`. -/
theorem infinite_row_survives (bd : ℕ → Bool) :
    ∃ σ : ℕ → Bool, ∀ t, bd t = true → halfStateInf bd σ t 0 = !bd (t + 1) := by
  refine ⟨fun i => recon bd (fun s => !bd (s + 1)) (i + 1) 0, fun t _ => ?_⟩
  rw [halfStateInf_recon]
  rfl

/-- **Light cone of the infinite-row machine.** Bit `i` at time `t` depends only on the bits
`< i + t + 1` of the initial row. -/
theorem halfStateInf_congr (bd : ℕ → Bool) {σ σ' : ℕ → Bool} :
    ∀ t i, (∀ j, j < i + t + 1 → σ j = σ' j) → halfStateInf bd σ t i = halfStateInf bd σ' t i := by
  intro t
  induction t with
  | zero => intro i h; exact h i (by omega)
  | succ t ih =>
    intro i h
    simp only [halfStateInf, halfStepInf]
    rw [ih (i + 1) (fun j hj => h j (by omega)), ih i (fun j hj => h j (by omega))]
    rcases i with _ | j
    · rfl
    · rw [if_neg (by omega), if_neg (by omega), ih (j + 1 - 1) (fun l hl => h l (by omega))]

/-- **No uniform death time.** For every drive and every horizon `T` there is a positive finite
code (of length `T + 2`) whose machine passes every check before time `T`. -/
theorem survivor_for_every_horizon (bd : ℕ → Bool) (T : ℕ) :
    ∃ S, 2 ^ (T + 1) ≤ S ∧ S < 2 ^ (T + 2) ∧ dDiesBy bd S T = false := by
  obtain ⟨σ, hσ⟩ := infinite_row_survives bd
  -- keep the first `T + 1` cells of `σ` and put a black cell at position `T + 1`
  set S : ℕ := bitsOf (fun i => if i = T + 1 then true else σ i) (T + 2) with hSdef
  have hbits : ∀ j, j < T + 1 → S.testBit j = σ j := by
    intro j hj
    rw [hSdef, testBit_bitsOf, if_neg (by omega)]
    simp [show j < T + 2 by omega]
  have htop : S.testBit (T + 1) = true := by
    rw [hSdef, testBit_bitsOf]; simp
  have hlo : 2 ^ (T + 1) ≤ S := Nat.ge_two_pow_of_testBit htop
  have hhi : S < 2 ^ (T + 2) := bitsOf_lt _ _
  refine ⟨S, hlo, hhi, ?_⟩
  cases hd : dDiesBy bd S T
  · rfl
  · exfalso
    obtain ⟨t, ht, hb, hfail⟩ := (dDiesBy_spec bd S T).1 hd
    have hagree : halfStateInf bd (fun i => S.testBit i) t 0 = halfStateInf bd σ t 0 :=
      halfStateInf_congr bd t 0 (fun j hj => hbits j (by omega))
    rw [halfStateInf_testBit, hfail, hσ t hb] at hagree
    cases hn : bd (t + 1) <;> simp [hn] at hagree

end GLM.Rule30
