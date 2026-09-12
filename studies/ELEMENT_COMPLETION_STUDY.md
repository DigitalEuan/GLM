# Sparse chemistry: deciding every empty cell of the element register

## Tier 0 — the coarse read

**Question.** The element register measures 1257 of its 1652 cells and leaves the rest blank. Can the blanks be *decided* — filled where a rule earns it, and named as something specific where it does not — without writing an estimate into the register?

**Verdict.** Every empty cell is decided: 9 fields take a rule that beat the field's own mean out of sample, 185 cells are filled by estimate, and each cell still empty carries one of three stated reasons.

**Deciding figure.** Coverage rises from 1257 to 1442 of 1652 cells, the 210 that stay empty are 100 inputs absent, 97 no admitted rule and 13 not derivable, and the register itself is unchanged.

**Recomputed by.** `glm_universal.reasoning.element_completion.element_completion_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 1. The gap as it stood

`studies/RELATIVE_MEASURE_STUDY.md` and the coverage report before this round
said the true thing about the chemistry register and stopped there: it is
sparse. 118 elements × 14 fields is 1652 cells; 1257 of them hold a
measurement; the rest are blank. `element_coverage` could already *widen* a
query by derivation — it would compute a covalent radius from an atomic radius
when asked — but it wrote nothing back, and a blank cell was blank for no
recorded reason. A reader could not tell the difference between "nobody has
measured this", "this cannot be derived from what we hold" and "we did not
try".

That is the gap this round closes: every empty cell is decided, and each cell
still empty afterwards carries one of three stated reasons rather than none.
The shape of the closure matters more than the count. **Deciding a cell is not the same as filling it.** A cell that
cannot be filled honestly should come back with the reason, and the reason
should be one of a small fixed set, so that "we did not try" is not one of the
available answers.

## 2. The rule that decides whether a rule is allowed

Anything can fill a table. The question is what earns the right, and it is
settled before any cell is filled, by a gate that the module states as data:

> A rule is admitted only if its **leave-one-out** mean absolute error is at
> most **half** the error of predicting the field's own mean, scored on at
> least **20** elements.

Three deliberate choices are in that sentence.

* **Leave one out, not in sample.** The rule is fitted without the element it is
  scored on, so a rule that memorises cannot pass.
* **The field's own mean is the control.** Predicting the mean is what you can
  do knowing nothing but the field. Admission is therefore a claim that the rule
  found something, measured against the cheapest thing that is not a rule.
* **Half, and 20.** The margin and the sample size are fixed before the
  measurement rather than chosen after it. A rule scored on three elements has
  not been tested, and a rule that is 5% better than the mean is not worth the
  provenance it costs.

Fourteen rule families are tried per field — exact rational least squares on
each other numeric field, and interpolation in period within the element's
group — and the arithmetic is `Fraction` throughout (directive D7). The errors
below are quoted to three decimal places; the module carries them exactly.

## 3. What was admitted

Nine of the fourteen fields take a rule.

| field | family | predictor | scored on | skill (error ÷ mean's error) |
| --- | --- | --- | --- | --- |
| `electronegativity_pauling` | linear | `ionization_energy_eV` | 94 | 0.421 |
| `atomic_radius_pm` | linear | `covalent_radius_pm` | 24 | 0.451 |
| `covalent_radius_pm` | linear | `atomic_radius_pm` | 24 | 0.457 |
| `valence_electrons` | group | group and period | 93 | 0.197 |
| `ionization_energy_eV` | group | group and period | 88 | 0.384 |
| `electron_affinity_eV` | group | group and period | 57 | 0.489 |
| `melting_point_K` | group | group and period | 88 | 0.288 |
| `boiling_point_K` | group | group and period | 86 | 0.359 |
| `density_g_per_cm3` | group | group and period | 87 | 0.460 |

Every one is below the gate of 0.5, and two of them — `electron_affinity_eV` at
0.489 and `density_g_per_cm3` at 0.460 — are close enough to it to show the gate
is a real edge rather than a formality.

The group rule is the periodic table doing the work it exists to do: an
element's value is interpolated in period between the nearest known member of
its own group above it and the nearest below. That it beats the field mean by a
factor of two to five is not a discovery about chemistry; it is a check that the
register's own structure is intact.

## 4. What was refused, and why that is the useful half

**`homonuclear_bde_kJ_per_mol` is refused.** Its best rule — linear on
`covalent_radius_pm` — scores 0.68, worse than the gate. Ninety-seven cells that
a looser rule would have filled are left empty and marked `no_admitted_rule`.
This is the single most valuable row in the study: the gate cost 97 cells, which
is nearly half of what filling gained, and it was applied anyway.

**`year_discovered` is refused as `not_derivable`.** Thirteen cells. The year an
element was first isolated is a fact about people and laboratories; no rule over
this register could reach it, and calling that a rule failure would be a
category error. It is named as its own disposition so the two kinds of "we
cannot" are never added together.

**`atomic_weight_u`, `group_block_code` and `standard_state_code` have no empty
cells** and need no rule.

## 5. The four dispositions

Every one of the 395 cells the register does not measure gets exactly one
disposition, and the four are exhaustive and mutually exclusive:

| disposition | cells | what it says |
| --- | --- | --- |
| `estimated` | 185 | an admitted rule had its inputs and produced a value |
| `inputs_absent` | 100 | the field has an admitted rule; this element lacks the input it needs |
| `no_admitted_rule` | 97 | every rule tried on this field failed the gate |
| `not_derivable` | 13 | no rule over this register could reach this field at all |

By field:

| field | estimated | inputs absent | other |
| --- | --- | --- | --- |
| `covalent_radius_pm` | 75 | 19 | |
| `electron_affinity_eV` | 29 | 32 | |
| `boiling_point_K` | 17 | 8 | |
| `density_g_per_cm3` | 16 | 6 | |
| `ionization_energy_eV` | 15 | 1 | |
| `melting_point_K` | 15 | 0 | |
| `valence_electrons` | 10 | 0 | |
| `electronegativity_pauling` | 8 | 15 | |
| `atomic_radius_pm` | 0 | 19 | |
| `homonuclear_bde_kJ_per_mol` | 0 | 0 | 97 no admitted rule |
| `year_discovered` | 0 | 0 | 13 not derivable |

`atomic_radius_pm` is the instructive line: it *has* an admitted rule, and fills
nothing, because the 19 elements missing an atomic radius are exactly the ones
missing a covalent radius. A rule is not a source of data.

Coverage therefore goes 1257 → 1442 of 1652, and the 210 cells that remain are
100 + 97 + 13.

## 6. What is not done to the register

The estimates are a **layer above** the register. `element_completion` reads the
register and produces a view; the register file is not written to, and asking
for measurements returns exactly the 1257 measured cells. Every estimate carries
its provenance: the rule that produced it, in a form that can be checked by
hand, and that rule's out-of-sample error.

```
He  electronegativity_pauling  5.682  =  12463665690/53492743693 * ionization_energy_eV
                                          - 251756942531/5349274369300   (fitted on 94)
He  covalent_radius_pm         64.601 =  40097/37562 * atomic_radius_pm - 910587/10732
N   electron_affinity_eV        0.682  interpolated in period within group 15
```

The layering is checked, not asserted: `safety.holds` is true, meaning no
estimate sits on a cell the register measures, and no estimate disagrees with a
measurement it could be compared against.

Two of those numbers deserve a word. `He` at 5.68 on the Pauling scale is
higher than fluorine, and the interpolation for `N` reproduces a value the
register happens to hold elsewhere. The first is what the admitted rule says,
carried with its 0.421 error rather than suppressed for being surprising; the
estimate layer's job is to be reproducible, not to be plausible. A reader who
wants only measurements asks for measurements and gets them.

## 7. The formal side

[`RequestProject/GLM/Completion.lean`](../RequestProject/GLM/Completion.lean)
proves what the layering claims, so that the claims do not rest on the
implementation being careful:

* a completed view can never overwrite a measurement — reading a measured cell
  returns the measurement whatever the estimate layer holds;
* coverage only rises: filling cells never reduces what the register answers;
* the four dispositions are exhaustive and mutually exclusive, so every empty
  cell is decided exactly once;
* and what the gate actually claims, stated as an inequality on the two errors
  rather than as a description of it.

## 8. How to re-run it

```bash
cd overlay
PYTHONPATH=. python3 -c "from glm_universal.runtime.session import GeometricSession as S; print(S().ask('report completion').answer)"
PYTHONPATH=. python3 -m pytest glm_universal/tests/test_element_completion.py -q
cd .. && lake build RequestProject.GLM.Completion
```

## 9. Limits

An estimate is an estimate. Nothing here claims that the 185 filled cells are
measurements, that the linear fits are physics, or that the leave-one-out error
of a rule is the error of any particular cell it filled — it is the rule's
error, and it is quoted as such.

The gate is a threshold, and thresholds are conventions. 0.5 and 20 were fixed
before the measurement and are stated in the module, so a reader who prefers
0.25 can re-run and see which of the nine survive; what would not be legitimate
is choosing the threshold after seeing which rules it admits.

Finally, the 210 undecided cells are not a residue to be cleared. Ninety-seven
of them are a field this register cannot predict, thirteen are a field no
register could, and the honest thing was to say so.
