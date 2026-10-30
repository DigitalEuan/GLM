module

public import Mathlib

/-!
# The budget rule in the answering path (Phase 147)

The formal half of `studies/BUDGET_READING_STUDY.md`
(`glm_universal.reasoning.hole_reading`, the `hole` query kind and
`report deep holes`).

Phase 124 (`GLM.ProbeBudget`) proved the arithmetic of a stopping rule for the
certifying reading of a deep hole: no barren stop, and a budget of 1056 starts
fixed in advance. This file states what replacing the *patience* reading of
the answering path by that rule can and cannot change.

**The model.** The reading runs starts `0, 1, …, B - 1`; the sweep is
deterministic, so everything after start `n` is a function of `n`:

* `V n` — the vertices in hand after start `n`, growing with `n`, and never
  more than the hole's own vertex set `T`;
* `cl` — the closure step run after the probe stops, monotone, and never adding
  a point outside `T` to a subset of `T`;
* `cert n` — the stop predicate (the marked-barycentre identity on the raw
  vertices), which holds only when the closed set is already `T`;
* `barren n` — the barren tail after start `n`.

The reading is **certified** at its stop `s` when `cl (V s) = T` — that is the
check the code makes after closure. The **patience reading** stops at the
first start where `cert` holds *or* the barren tail has reached the patience
`p`; the **budget reading** stops at the first start where `cert` holds, and
otherwise at the end of its budget.

* `certified_mono` — once a reading is certified, a later stop is too.
* `budget_agrees` — **the frozen path is kept**: whenever the patience reading
  is certified, the budget reading with any budget at least as large is
  certified, and both return the same vertex set `T` — so the same type.
  The number of starts may differ; nothing else can.
* `budget_refuses_only_without_cert` — the budget reading is uncertified only
  if no start inside its budget carries the stop certificate: it never gives up
  early.
* `patience_may_refuse` — the converse of `budget_agrees` fails: a reading the
  patience stops before its certificate is refused by the patience rule and
  certified by the budget rule. This is the only way an answer can move.
-/

@[expose] public section

namespace GLM.BudgetReading

/-- Where the budget reading stops: the first start below `B` carrying the
certificate, and otherwise the last start of the budget. -/
def budgetStop (cert : ℕ → Bool) (B : ℕ) : ℕ :=
  ((List.range B).find? cert).getD (B - 1)

/-- Where the patience reading stops: the first start below `B` carrying the
certificate or with a barren tail of at least `p`, and otherwise the last
start of the budget. -/
def patienceStop (cert : ℕ → Bool) (barren : ℕ → ℕ) (p B : ℕ) : ℕ :=
  ((List.range B).find? fun n => cert n || decide (p ≤ barren n)).getD (B - 1)

/-- Every stop lies inside the budget. -/
theorem patienceStop_le {cert : ℕ → Bool} {barren : ℕ → ℕ} {p B : ℕ} :
    patienceStop cert barren p B ≤ B - 1 := by
  unfold patienceStop
  cases h : (List.range B).find? (fun n => cert n || decide (p ≤ barren n)) with
  | none => simp
  | some m =>
    have hm := List.mem_range.mp (List.mem_of_find?_eq_some h)
    simp only [Option.getD_some]
    omega

section

variable {β : Type*} {V : ℕ → Set β} {cl : Set β → Set β} {T : Set β}

/-- **Certified stays certified**: if the closed vertex set at start `m` is the
hole's, so is the closed set at every later start. -/
theorem certified_mono (hV : Monotone V) (hcl : Monotone cl)
    (hsub : ∀ n, cl (V n) ⊆ T) {m n : ℕ} (hmn : m ≤ n) (hm : cl (V m) = T) :
    cl (V n) = T :=
  le_antisymm (hsub n) (hm ▸ hcl (hV hmn))

/-- **The frozen path is kept.** If the patience reading is certified — its
closed vertex set is the hole's — then so is the budget reading with any budget
`B' ≥ B`, and both return the same vertex set `T`. -/
theorem budget_agrees (hV : Monotone V) (hcl : Monotone cl)
    (hsub : ∀ n, cl (V n) ⊆ T) {cert : ℕ → Bool}
    (hcert : ∀ n, cert n = true → cl (V n) = T) {barren : ℕ → ℕ} {p B B' : ℕ}
    (hB : B ≤ B') (h : cl (V (patienceStop cert barren p B)) = T) :
    cl (V (budgetStop cert B')) = T := by
  unfold budgetStop
  cases hf : (List.range B').find? cert with
  | some m =>
    simp only [Option.getD_some]
    exact hcert m (List.find?_some hf)
  | none =>
    simp only [Option.getD_none]
    refine certified_mono hV hcl hsub ?_ h
    have := patienceStop_le (cert := cert) (barren := barren) (p := p) (B := B)
    omega

/-- **The budget reading never gives up early**: it is uncertified only if no
start inside the budget carries the stop certificate. -/
theorem budget_refuses_only_without_cert {cert : ℕ → Bool}
    (hcert : ∀ n, cert n = true → cl (V n) = T) {B : ℕ}
    (h : cl (V (budgetStop cert B)) ≠ T) : ∀ n < B, cert n = false := by
  intro n hn
  by_contra hc
  apply h
  unfold budgetStop
  cases hf : (List.range B).find? cert with
  | some m =>
    simp only [Option.getD_some]
    exact hcert m (List.find?_some hf)
  | none =>
    rw [List.find?_eq_none] at hf
    exact absurd (Bool.not_eq_false _ ▸ hc) (by simpa using hf n (List.mem_range.mpr hn))

end

/-- **The converse fails.** With vertices `V n = {k | k < n}` of a hole whose
vertex set is `{k | k < 5}`, read off start by start, the certificate first
holds at start `5`; a patience of `3` against a barren tail equal to the start
index stops the patience reading at start `3`, uncertified, while the budget
reading stops at start `5`, certified. -/
theorem patience_may_refuse :
    patienceStop (fun n => decide (5 ≤ n)) (fun n => n) 3 10 = 3 ∧
      budgetStop (fun n => decide (5 ≤ n)) 10 = 5 := by
  decide

end GLM.BudgetReading
