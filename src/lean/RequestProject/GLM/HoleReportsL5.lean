import RequestProject.GLM.DeepHoleFailure

/-!
# The configuration reading in the other deep-hole reports (Phase 149)

`studies/HOLE_REPORTS_L5_STUDY.md` gives the three deep-hole reports that
still named a hole with the ladder's readings — `report hole classifier`,
`report hole ladder` and `report hole failures` — the configuration reading
`L₅` and its answer rule.  Each report keeps its own round's record verbatim
and adds what `L₅` says to the question that round asked.  Three facts the
new clauses lean on are not measurements, and they are here.

* `rule_fires_of_resolvesAt` — **the rule answers wherever the failure
  round's criterion certifies.**  If a type's per-type criterion holds at
  spread `w` and a query lies within `w` of that type's reference, the answer
  rule (twice the query's distance below the distance to every other
  reference) fires.  So the rule is never more conservative than the
  criterion `report hole failures` reads.
* `gate_of_rule` — **the seed-change gate, from the rule.**  The gate of the
  first two rounds is that every reference hole, re-read under a bare seed
  change, is named as itself.  If every re-read query satisfies the answer
  rule against its own reference, its own reference is strictly the nearest:
  the gate holds, query by query, with no global criterion.
* `criterion_not_necessary` — **the global criterion is sufficient, not
  necessary.**  A two-reference table on the line in which the global
  criterion `ρ = 2W/B < 1` fails at the measured spread, and yet every query
  is named correctly.  This is why `L₅` can pass the gate at a cell where its
  `ρ` is above one (the 480-start cell of the configuration reading).
-/

namespace GLM.HoleReportsL5

open GLM.DeepHoleLadder GLM.DeepHoleFailure

universe u v

variable {C : Type u} {L : Type v}

/-- **The rule fires inside the criterion.**  The per-type criterion at
spread `w` and a query within `w` of the type's reference give the answer
rule against every other reference. -/
theorem rule_fires_of_resolvesAt {R : Reading C} {refs : List (L × C)} {t : L}
    {p x : C} {w : ℚ} (hres : ResolvesAt R refs t p w) (hx : R.dist x p ≤ w) :
    ∀ f ∈ refs, f.1 ≠ t → 2 * R.dist x p < R.dist p f.2 := by
  intro f hf hne
  have h := hres f hf hne
  linarith

/-- **The answer rule makes its answer the strict nearest reference**, for
any rung (the configuration reading's `config_answer_sound`, stated for an
abstract reading). -/
theorem rule_sound {R : Reading C} {refs : List (L × C)} {t : L} {p x : C}
    (hrule : ∀ f ∈ refs, f.1 ≠ t → 2 * R.dist x p < R.dist p f.2) :
    ∀ f ∈ refs, f.1 ≠ t → R.dist x p < R.dist x f.2 := by
  intro f hf hne
  exact per_type_correct (R := R) (refs := refs) (t := t) (p := p) (x := x)
    (w := R.dist x p) (fun g hg hgt => hrule g hg hgt) le_rfl hf hne

/-- **The gate, query by query.**  If every re-read query `(t, x)` satisfies
the answer rule against a reference of its own label `t`, then that reference
is strictly the nearest to `x`: every reference recognises itself. -/
theorem gate_of_rule {R : Reading C} {refs : List (L × C)} {qs : List (L × C)}
    (hrule : ∀ q ∈ qs, ∃ p, (q.1, p) ∈ refs ∧
      ∀ f ∈ refs, f.1 ≠ q.1 → 2 * R.dist q.2 p < R.dist p f.2) :
    ∀ q ∈ qs, ∃ p, (q.1, p) ∈ refs ∧
      ∀ f ∈ refs, f.1 ≠ q.1 → R.dist q.2 p < R.dist q.2 f.2 := by
  intro q hq
  obtain ⟨p, hp, hr⟩ := hrule q hq
  exact ⟨p, hp, rule_sound hr⟩

/-- The line `ℚ` with `|a - b|`, as a rung. -/
def lineReading : Reading ℚ where
  dist a b := |a - b|
  dist_self a := by simp
  dist_comm a b := abs_sub_comm a b
  dist_triangle a b c := abs_sub_le a b c

/-- **The global criterion is not necessary.**  References `0` (label `0`)
and `4` (label `1`); queries `0` of label `0` and `13/2` of label `1`.  The
measured spread is `5/2` (the second query's distance to its reference), and
the global criterion fails there (`2 · 5/2 = 5` is not below `4`), yet each
query is strictly nearer its own reference than the other. -/
theorem criterion_not_necessary :
    ¬ Resolves lineReading [((0 : ℕ), (0 : ℚ)), (1, 4)] (5 / 2) ∧
    (lineReading.dist 0 0 < lineReading.dist 0 4) ∧
    (lineReading.dist (13 / 2) 4 < lineReading.dist (13 / 2) 0) := by
  refine ⟨?_, ?_, ?_⟩
  · intro h
    have := h ((0 : ℕ), (0 : ℚ)) (by simp) (1, 4) (by simp) (by decide)
    simp only [lineReading] at this
    norm_num [abs_of_neg] at this
  · simp only [lineReading]; norm_num
  · simp only [lineReading]; norm_num [abs_of_pos]

end GLM.HoleReportsL5
