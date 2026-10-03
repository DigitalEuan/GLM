# The register against the world: every element row against cited outside values, and a completion gate that survives its own selection

## Tier 0 — the coarse read

**Question.** Does the element register agree with the outside world, in every row and every field an outside source holds — read at the precision each value is held to, never writing to the register — and do the chemistry completion rules still earn their place once the choice of rule is itself held out?

**Verdict.** Yes, except where it is now named: every one of the 354 cells is decided, 24 ionization energies and one configuration are discrepant with the cited source, every atomic weight agrees (eleven only at the register's stated precision), and the register is not written; the completion gate now reads the nested holdout, so the covalent radius rule is demoted and the electron affinity rule is narrowed to the main group.

**Deciding figure.** 354 of 354 cells decided (atomic weight 73 / 11 / 0 discrepant / 34 world-silent; ionization energy 10 / 68 / 24 discrepant / 6 register-silent / 10 both-silent; configuration 107 / 1 discrepant / 10 world-silent); 24 of 24 declared questions as declared, 0 wrong, where the machine answered 2 of them before; 186 of 186 injected errors caught and 0 of 186 world values flagged; 51 of 51 molecules decided; completed view 1,442 → 1,344 of 1,652 (185 → 87 estimates); 8 of 8 marks met.

**Recomputed by.** `glm_universal.runtime.register_world_report.register_world_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

Round 6 of the order of work in [`ROADMAP_STUDY.md`](ROADMAP_STUDY.md) and
[`STATUS.md`](../STATUS.md) §3.4: *the register against the world* —
candidate C with H's first item.

* **Candidate C.** Phase 63 let one question ask whether one atomic weight was
  consistent with a 30-row table transcribed by hand
  ([`SUBSTRATE_NATIVE_COGNITION_STUDY.md`](SUBSTRATE_NATIVE_COGNITION_STUDY.md)
  §7, Y1). The planner's one known wrong answer was the register holding
  iron's atomic weight as `55.84` where the standard is `55.845`. What C asked
  for was the whole report — *a discrepancy report of register values against
  cited standard values, never overwriting the register* — that finds every
  such row rather than the one a question happened to reach.
* **H's first item.** The same study's Y5 measured each admitted chemistry
  completion rule by a nested holdout — the rule re-chosen without each
  held-out element, then scored on it — because each rule had been picked as
  the best of about fourteen on the same errors it then reported. Two rules
  did not survive (`covalent_radius_pm` at 0.631, `electron_affinity_eV` at
  0.823, against a gate of one half). Its §8 named the next step: demote them,
  or keep them for the narrower subset on which they survive, and quote the
  nested skill beside the reported one.

Both are the same question asked two ways: does a number the register (or the
completed view) gives deserve to be believed, measured against something
outside the step that produced it.

## 1. The world, frozen

Two outside sources, fetched once and frozen in
`overlay/glm_universal/data_objects/_data/` with their URL, retrieval date
(2026-10-03) and the SHA-256 of the page each was parsed from:

| file | source | rows | holds |
|---|---|---|---|
| `world_ciaaw_2024.json` | CIAAW, *Standard Atomic Weights* (the 2024 table: the Atomic Weights 2021 report with the 2024 revisions of Gd, Lu and Zr) | 118 | 84 standard atomic weights (an interval `[a, b]` or `v(u)`); 34 elements with none |
| `world_nist_ie.json` | NIST Atomic Spectra Database, ionization energies of the neutral atoms H I – Og I | 108 | the first ionization energy with its uncertainty and the database's theoretical `( )` / semi-empirical `[ ]` marks, and the ground-state configuration, for H to Hs |

Nothing is fetched at run time. The snapshot is what the report is about, and
moving to a newer table is a new snapshot with a new digest.

## 2. The reading — written before any code of the round

The reading is stated at the head of
[`register_world_cases.py`](../overlay/glm_universal/evaluation/register_world_cases.py),
committed before any code. What was seen first is said there too: the
snapshots were checked for transcription by a throw-away comparison, so the
*counts* in the list cases were seen before the declaration. What the
declaration fixed before code is the reading and the marks.

**Six verdicts, one per cell.** For each of the 354 cells of
`atomic_weight_u`, `ionization_energy_eV` and `electron_configuration`:

* `agrees` — the register's point value lies inside the world's interval
  (a configuration: the two occupations are equal);
* `agrees_at_stated_precision` — the point lies outside, but the register's
  value read at the precision it is held to (half a unit of its last place
  either side, `Interval.as_held`) meets the world's interval: some value both
  allow exists, so the register may be a correct rounding;
* `discrepant` — no value both allow exists;
* `world_silent`, `register_silent`, `both_silent` — one side, or neither,
  holds a value. A register-silent cell is a cell the world could fill; it is
  reported, never written.

**The world's interval.** CIAAW `[a, b]` is itself; `v(u)` is `v ± u` with `u`
in the last places of `v` (`55.845(2)` is `[55.843, 55.847]`). NIST `v ± u` is
itself; a NIST value with no stated uncertainty is read at the precision it is
quoted to, the same rule the register's own values get.

**A configuration is an occupation**: the map from subshell to electron count,
after expanding a noble-gas core by the cores the database lists. The order
the subshells are written in is not part of it (`[Ar]4s2 3d6` is
`[Ar].3d6.4s2`); a `(predicted)` or `(calculated)` tag is carried, not
compared.

**A molecule** is checked through its elements: the register's interval is the
sum of `count ×` each element's held interval, the world's the sum of
`count ×` each element's standard interval.

**The completion gate.** A rule is admitted only if it passes the Phase 61 gate
**and** its nested holdout skill is at most one half. A field whose rule fails
over every element may be narrowed to one declared domain, the main-group
elements (groups 1, 2 and 13–18), if the nested skill re-measured inside it
passes on at least 20 scored folds and the selection inside the domain chose
the field's own rule on every scored fold. The domain was chosen after
measuring three (every element, the main group, and the d- and f-block as the
periodic-table module places them in groups 3–12), which is itself a selection
— a small one, since the third gave no scored fold for either field — and it
is reported as one.

**The marks.** R1 every cell decided once; R2 the register not written; R3
every declared question as declared, 0 wrong; R4 injected errors caught and
the world's own values never flagged; R5 every molecule decided, none
discrepant while all its elements agree; R6 Phase 63's eight interval
questions hold but the one declared move; R7 the completion gate's declared
outcome, with the measured layer still the register; R8 the Lean file.

## 3. What was built

* [`runtime/register_world.py`](../overlay/glm_universal/runtime/register_world.py)
  — the report. It reads the two snapshots and the register, opens nothing for
  writing, and gives every cell its verdict, both sides as written, and the
  reason; molecules through their elements; the mutation audit.
* The consistency frame of
  [`runtime/semantic_plan.py`](../overlay/glm_universal/runtime/semantic_plan.py)
  — *is the atomic weight of X consistent with the standard value* — now reads
  the frozen world for every element in all three fields and for a molecule's
  molar mass, and refuses by name: `WORLD_SILENT`, `REGISTER_SILENT`,
  `STANDARD_UNDECLARED`. A new frame, *which elements have an X inconsistent
  with the standard value*, lists a field's discrepant rows. Both are reached
  through the router and `GLM.py -q`.
* [`reasoning/element_completion.py`](../overlay/glm_universal/reasoning/element_completion.py)
  — the nested holdout moved here from the substrate-cognition module (its Y5
  figures are unchanged: it now reads them from here), the second gate, the
  narrowing domain, and a `domain` on each rule. The nested figures take about
  half a minute of exact arithmetic, so they are kept beside the digest of the
  files they read (`_derived/completion_nested_gate.json`) and recomputed only
  when one of them moves. `report completion` gains a step for the nested gate.
* [`runtime/register_world_report.py`](../overlay/glm_universal/runtime/register_world_report.py)
  and `tools register-world` — the marks.

## 4. Results

*Recomputed by `glm_universal.runtime.register_world_report.register_world_report`
(`python3 -m glm_universal.tools register-world`).*

**The report.** 354 of 354 cells decided (R1):

| field | agrees | at stated precision | discrepant | world silent | register silent | both silent |
|---|---|---|---|---|---|---|
| `atomic_weight_u` | 73 | 11 | 0 | 34 | 0 | 0 |
| `ionization_energy_eV` | 10 | 68 | 24 | 0 | 6 | 10 |
| `electron_configuration` | 107 | 0 | 1 | 10 | 0 | 0 |

* **Atomic weights.** None is discrepant. Eleven agree only at the register's
  stated precision — Li, O, Al, Mn, Fe, Co, Cu, Br, Ru, Sm, Ir — and iron is
  among them: the planner's one wrong answer is now a located row of a report,
  not a question someone happened to ask. The 34 world-silent rows are the
  elements CIAAW gives no standard atomic weight; the register holds a
  mass number or an isotope mass for each, which the report does not judge.
* **Ionization energies.** 24 are discrepant with NIST. By size: nine are off
  by more than 0.1 eV (Tc, Ta, W, Os, Ir, At, Fr, Ac, Th — tantalum's 7.89
  against 7.549571(25) is the largest), ten by between 0.01 and 0.1 eV (As,
  Sb, Pm, Re, Pu, Am, Cm, Bk, Es, No), and five by less than 0.01 eV (Pr, Bi,
  Po, Rn, Ra) — for these the register's last digit is not a correct rounding
  of the current value (radium's 5.279 against 5.2784239(25)). Praseodymium's
  NIST value is marked semi-empirical. The report says *discrepant*; it does
  not say which side is wrong, and the register is not corrected. Most of the
  register's values agree only at stated precision (68), because the register
  holds three decimals and NIST holds six or more. The six register-silent
  rows are Lr, Rf, Db, Sg, Bh and Hs: NIST holds a value the register lacks.
* **Configurations.** 107 agree; lawrencium is the one discrepancy — the
  register holds `[Rn]7s2 5f14 6d1`, NIST `[Rn].5f14.7s2.7p`.

**Molecules.** 51 of 51 decided: 48 agree, 3 agree at stated precision
(aluminium oxide, potassium permanganate, ozone), none discrepant (R5).

**The questions** (R3). 24 of 24 as declared, 0 wrong: 7 on atomic weights, 9
on ionization energies, 5 on configurations, 3 on molecules — 17 answers and 7
refusals, each refusal naming its code. Before the round the machine answered
2 of the 24 (iron's and carbon's weights) and refused the other 22 with
reasons that named no side: *no standard value is declared for Au*, *a standard
value is declared only for atomic weights*, *not a held number*.

**The register is not written** (R2): its file digest and a digest of every
loaded value are identical before and after the whole report and every
question.

**Injected errors** (R4). For each of the 186 numeric cells where both sides
hold a value, a register value held at the same precision but wholly above
the world's interval is reported discrepant: 186 of 186. The world's own
central value rounded to the register's precision is never flagged: 0 of 186.

**Earlier verdicts** (R6). Phase 63's eight interval questions: eight of eight
correct, and the one move is the declared one — *is the atomic weight of gold
consistent with the standard value*, refused while gold was outside the 30-row
table, is now *yes*. The held-out label is amended in
`evaluation/cognition_heldout.py` with the reason, and so is the
substrate-cognition test that pinned it.

**The completion gate** (R7). As declared:

| field | rule | reported | nested, every element | nested, main group | now |
|---|---|---|---|---|---|
| `covalent_radius_pm` | linear on atomic radius | 0.457 | 0.631 | 0.631 (22 folds) | **demoted** |
| `electron_affinity_eV` | group interpolation | 0.489 | 0.823 | 0.187 (31 folds, own rule 31 of 31) | **narrowed to the main group** |
| the other seven | unchanged | — | 0.184 – 0.493 | — | admitted as before |

The completed view goes from 1,442 to **1,344** of 1,652 cells: of the 185
estimates the first gate made, 98 are withdrawn — all 75 covalent radii and the
23 electron affinities outside the main group — and 87 remain. The 395 empty
cells are still every one decided (87 estimated, 62 inputs absent, 233 no
admitted rule, 13 not derivable), and read at the measured provenance the
completed view is still the register, cell for cell.

## 5. What is proved rather than measured

`RequestProject/GLM/RegisterWorld.lean` builds with the standard axioms only
and no `sorry` (R8):

* **A discrepancy is earned.** `compare_discrepant_iff`: a cell is
  `discrepant` exactly when no value is allowed by both the held register value
  and the world. Hence `not_discrepant_of_correct_rounding`: a register value
  that is a correct rounding of any value the world allows is never reported
  discrepant. `compare_agrees_iff` and `compare_atPrecision_iff` say what the
  other two numeric verdicts mean, and `compare_cases` that the six are
  exhaustive and fixed by which side is silent.
* **An injected error is caught.** `discrepant_of_above`,
  `discrepant_of_below`: a value held wholly outside the world's interval is
  discrepant — the audit of R4, for every value rather than 186.
* **A molecule inherits its discrepancy.** `sum_meets` and
  `exists_disjoint_of_sum_disjoint`: with non-negative counts, if every
  element's held interval meets its standard, so does the molecule's; so a
  molecule can be discrepant only if one of its elements is. `sum_mem` is the
  same for points.
* **A configuration is an occupation.** `occ_perm`: the occupation does not
  depend on the order the subshells are written in; `occ_append`: expanding a
  core adds the core's occupation.
* **The nested gate only removes.** Over `GLM.Completion`'s cells:
  `filled_of_restrict` and `coverage_restrict` — a stricter gate (fewer fields
  admitted, or a rule admitted on fewer elements) fills no cell the looser one
  left empty — and `measured_restrict`: the measured layer is the register
  under either gate.
* `world_ledger`, `nested_ledger`, `nested_loss` check that the counts above
  partition what they are about.

## 6. Limits, and what the round leaves

* **Three fields, two sources.** Atomic weight, ionization energy and
  configuration are checked because those are what the two snapshots hold.
  Electronegativity, radii, melting and boiling points, density, electron
  affinity and the discovery year are refused `STANDARD_UNDECLARED` rather
  than guessed at; each would need a source of its own, cited and frozen the
  same way. Electron affinity (NIST, or the Hotop–Lineberger compilation) and
  melting and boiling points are the obvious next ones.
* **A discrepancy is not a correction.** The report never says which side is
  wrong. Several of the 24 ionization-energy discrepancies look like older
  measured values the outside table has since replaced (tantalum, actinium,
  thorium, francium); five are last-digit rounding differences. Whether to
  write any of it back is the owner's decision, and nothing in this round
  makes it.
* **The 34 world-silent atomic weights** hold mass numbers or isotope masses
  for radioactive elements. A second outside source — the mass of the
  longest-lived isotope — would let them be checked too.
* **The narrowing was chosen after looking.** Three domains were measured and
  one was kept. The study states it; a held-out check would be a fresh
  register of electron affinities, which is the same outside material the
  first item of this section asks for.
* **What it does not move.** No earlier answer changes except the one declared
  move. The completed view is smaller, by design: 98 estimates that had been
  admitted on a skill the selection flattered are withdrawn.

**Which faculty moved.** Refusal, in both halves of the round. 98 estimates
are no longer given where the selection that admitted them did not survive
being held out, and 22 questions the machine refused without naming a side
are now answered or refused with the side named. Addressing moved through the
list frame: a whole field's discrepancies are recovered from one question.

## 7. Re-running it

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.tools register-world          # R1-R7
PYTHONPATH=. python3 -m pytest -q glm_universal/tests/test_register_world.py
python3 GLM.py -q "which elements have an ionization energy inconsistent with the standard value"
python3 GLM.py -q "is the electron configuration of lawrencium consistent with the standard value"
python3 GLM.py -q "report completion"
cd .. && lake build RequestProject.GLM.RegisterWorld                  # R8
```
