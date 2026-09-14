# Master plan: wiring status


## Tier 0 — the coarse read

**Question.** What has each phase of the wiring plan delivered, and what does the next round start from?

**Verdict.** Phase 37 is closed; Phase 38 is proposed and is where the next round starts.

**Deciding figure.** Every closed phase names what was built, where it lives, and how to see it recompute itself.

**Recomputed by.** (hand-written argument; nothing to recompute)

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

> ### Positioning — read this before starting a round
>
> **We are not claiming that the lattice generates the universe.** The claim is
> narrower, and it is testable: there is an *exact* substrate — the Golay code,
> the Leech lattice and the arithmetic on them, integer and `Fraction` exact
> throughout (D7) — and reality maps onto it with unusual fidelity, measured
> against a control every time it is asserted.
>
> The **Geometric Language Machine** is the experimental implementation of that
> mapping. Can language, mathematics and program text be mapped onto the Leech
> lattice using the Golay code and the other systems built here? Can the GLM
> reason with what that mapping gives it? Can it be generative, and solve
> problems, and return results that are real, accurate and checkable?
>
> Some of what the substrate holds is hidden by the layer it is read at. Every
> carrier here is a **projection at a stated resolution** — the 24-bit word, the
> syndrome, the MOG cell, the Leech point, the shell — so a correspondence that
> is invisible at one layer can be exact one layer up. **Check a claim from
> several layers and resolutions before calling it absent.**
> [`studies/COMBINER_STUDY.md`](studies/COMBINER_STUDY.md) and
> [`studies/INFORMATION_LOSS_STUDY.md`](studies/INFORMATION_LOSS_STUDY.md)
> measure what each step down actually discards.
>
> The full note, with what follows from it in practice, is the Positioning
> section of [`PROJECT_DIRECTIVES.md`](PROJECT_DIRECTIVES.md).

This document tracks the plan to fully wire the Geometric Language Machine,
eliminate the architectural simplifications, and implement multi-resolution
addressing. Each item says what was built, where it lives, and how to see it
recompute itself.

Everything below is reachable from the package's public API and from the query
runtime — **21 query kinds**, **65 report subjects** and **8 registers** — is
covered by the test suite (<!--figure:test-files-->91 test files<!--/figure-->),
and — where it is a report or a task — has a generated column-3 script that
recomputes the claim in a **fresh interpreter** and fails if anything differs.

No count in this document is typed by hand twice: every one of them is
recomputed by `glm_universal/figures.py` into
[`overlay/FIGURES.md`](overlay/FIGURES.md), and
`tests/test_figures.py` fails if a document drifts from it.

```bash
cd overlay
PYTHONPATH=. python3 -m pytest glm_universal/tests -q
PYTHONPATH=. python3 GLM.py -q "report migration"          -c 1
PYTHONPATH=. python3 GLM.py -q "report leech construction" -c 1
PYTHONPATH=. python3 GLM.py -q "task grid"                 -c 1
PYTHONPATH=. python3 GLM.py -q "report infinite values"    -c 1
PYTHONPATH=. python3 GLM.py -q "report capabilities"       -c 1
PYTHONPATH=. python3 GLM.py -q "report superposition"      -c 1
PYTHONPATH=. python3 -m glm_universal.evaluation --jobs 8
```

---

## The phases

Phases 1–13 are closed; each is recorded, as it was written, in
[`archive/MASTER_PLAN_ARCHIVE.md`](archive/MASTER_PLAN_ARCHIVE.md).

| phase | what it closed |
|---|---|
| 1 | core migration and substrate unification |
| 2 | algebra completion and simplification removal |
| 3 | the value layer, and the map of where the machine stops |
| 4 | meaning, not spelling |
| 5 | ambiguity as a value |
| 6 | measuring what the machine can actually do |
| 7 | closing what the evaluation found |
| 8 | the blueprint tested, and noise used as the computation |
| 9 | the external study catalogue, tested |
| 10 | the two companion preprints, and the last carrier gap |
| 11 | above 24 dimensions, addressing the Lean development, and the standing rules made into instruments |
| 12 | the sign-off ledger made sound, and every instrument in it |
| 13 | a harmonic register, and the third of a claim it makes testable |

The archive also holds three interstitial sections written between phases:
*Directive — multi-resolution Leech addressing*, *A task for the system* and
*Runtime surface added*.

**Phase 38 is proposed and is where the next round starts.** Phase 37 took the
question Phase 36 left — is the geometry's carry set a residue or a class? — and
answered it by naming the register first and measuring it second: a query is
*anonymous* when its identifiers are not the corpus's, and in that register the
text search and the identifier address book both fall to the hit rate chance
gives while the structural address holds most of what it had, with the stack's
existing gate handing the register over untuned. Phase 36 before it took the
standing negative result of the retrieval round and pushed it the other way by
making the faculties into a stack: a stated confidence gate, a stated quota,
and the geometry given only the queries the leading text faculty cannot read.
It is ahead of that leader on a tuning stride, on a disjoint held-out stride
and on goal queries, never below it at any window, and it carries **16**
queries against **1** lost where the matched controls carry **4** and **0** —
with `relay_confident` and `relay_carry` proved in Lean and the same relay run
in a register with no text in it. Phase 35 before it took
four of the five things the deep-hole rounds left behind and closed them as
mechanisms: escalation became a step of the ordinary query loop, the four
remaining failures were diagnosed and found to be the same mechanism as the
unmet separation criterion, cumulativity became a shipping condition with a
check, and the standing set of stalled results was ranked before the next
re-reading rather than after it. What stands now is §3.4 of
[`STATUS.md`](STATUS.md). Phase 32 took the four
items the untouched list had been carrying and closed each as a mechanism
rather than a stated limitation; Phase 31 took neither candidate but a
pre-registered question — is the fine-structure constant structurally
distinctive in the space the substrate permits? — and answered it with one
number under a stated null; Phase 28 took a supplied proposal — stop storing
the substrate's tables and generate them — and measured both the saving and
the generators; Phase 27 asked whether the substrate can do work rather than
hold a table.

---

Phases 14–36 are closed as well, and are recorded in the same archive.

| phase | what it closed |
|---|---|
| 14 | the layer chain made a real refinement, and the repository tidied |
| 15 | the layer chain audited at register scale |
| 16 | measure words as relative measures |
| 17 | the last third of the universality claim, the address layer audited, and the infinite-dimensional half of the VOA bridge |
| 18 | the two items Phase 16 left open, and a factor basis measured instead of asserted |
| 19 | the residue finished as a vocabulary decision |
| 20 | the recipe made into an object |
| 21 | the surface language driven off the descriptions |
| 22 | the branches deleted, and a second shape family |
| 23 | the four undescribed parts, and the four branches they were blocking |
| 24 | the quantiser's search, replaced by a lookup |
| 25 | the archive, read to the end |
| 26 | the dropped work, restored, and the archive's second reading closed |
| 27 | the address book made to do work, and the first loop |
| 28 | generated rather than stored, and the generators checked |
| 29 | the last stored table removed, and the cost of generating measured |
| 30 | the corpus itself made data: the tiered read, the entry point and its coverage claim, the addressed documents, and the studies' tables emitted rather than typed |
| 31 | the wobble landscape, pre-registered and measured: one statistic, two nulls, a gate fixed before the measurement, and **B = 1.79 bits** — weak, so the enumeration was not run |
| 32 | the four things the untouched list had been carrying: the cross-register analogy answered from an energy-conjugate register, sparse chemistry decided rather than blank, a standing rule for a vague `related_to` triple, and open vocabulary made a door — with every figure the growth moved re-measured |
| 33 | the Niemeier deep holes classified from trajectories: pre-registered, beating every control at **15 of 44** against 11 for the vertex count — and stopped by its own sanity check, which kept **3 of 10** labels under a bare seed change |
| 34 | the deep-hole ladder: the same question read one layer up, escalated over layer × budget cells until the law descends — **10 of 10** on the sanity check and **40 of 44** on the full query set at the joint reading with 1920 starts, with the separation criterion still unmet and said to be |
| 35 | what the deep-hole rounds left behind, taken as architecture rather than geometry: escalation made a step of the ordinary query loop (**no answer moves**, **no principled refusal converted**, **4 of 18** probes resolved above the first rung), the four remaining failures diagnosed as **rank-2 near misses on a closest pair** belonging to the very type whose spread stalls `ρ`, cumulativity made a shipping condition (**7** edges verified, **2** non-edges witnessed, **0** defects), the reverse-call planner built and **not promoted** behind directive D14, and the standing set of stalled results ranked before the next re-reading (**8** entries, **1** licensed) |
| 36 | the faculties made into a stack, and the standing negative result pushed the other way: a stated confidence gate of **1/10**, a stated quota and interleave, and the geometry given the queries the text layer cannot read — ahead of the text control on the tuning stride (**356 → 362** of 407), on a disjoint held-out stride (**354 → 358** of 406) and on goal queries (**710 → 715** of 813), never below it at any window; the gate fires on **66** of 1,614 queries and the geometry carries **16** against **1** lost, where a digest-and-reshuffle control carries **1** and a name search **none**; `relay_confident` and `relay_carry` in `RequestProject/GLM/Relay.lean` say what is a theorem rather than a hit rate; and the same relay run in a register with no text in it solves **2 of 50** ARC puzzles with a visual look that discards **95.3 %** of proposals |

| 37 | the register the relay's carry set pointed at, found and measured: a query whose identifiers are not the corpus's — a goal from another formalisation, modelled by renaming everything outside a declared vocabulary — where at k = 5 over **813** queries the text search falls **710 → 84** and the identifier address book **388 → 48**, both to the **48** hits chance gives, while the structural address holds **232 → 171** and leads every other faculty by more than a factor of two; a renaming cannot move a count of the syntax (`features_anonymise`), the identifier overlap it leaves is zero (`overlap_anonymise_eq_zero`) and the stack's existing gate therefore hands the register over (`relay_hands_over`, all in `RequestProject/GLM/Anonymous.lean`) — it fires on **538** of 813 where it fires on **24** of the same queries read plainly; and the shipped feature map is audited rather than idealised: it counts type words inside identifiers too, which moves a coordinate on **33** of 813 queries and never a logical, numeric, bracket or length coordinate |

The detail of each — what was built, where it lives and what recomputes it —
is in [`archive/MASTER_PLAN_ARCHIVE.md`](archive/MASTER_PLAN_ARCHIVE.md), kept as it was
written.  A phase is a record of a round, so it is archived by the same rule
as everything else: only the open phase is state.

---

## Phase 38 — what Phase 37 left behind

**Status: proposed. This is where the next round starts.**

It is §3.4 of [`STATUS.md`](STATUS.md), which points back here. Phase 36 took
the standing negative result of the retrieval round — retrieval by lattice
address beats chance and loses to plain text overlap — and answered it as an
architecture question rather than a geometry one: the faculties were made into
a stack, and the geometry was given only the queries the leading faculty cannot
read. Phase 37 then asked whether what the stack carries is a residue or a
class, and closed that question with the anonymous register. Both are closed.
Six candidates stand — the four the deep-hole rounds left, the one the stack
round added, and the two the anonymous round added in place of the one it
closed:

1. **The separation criterion, still unmet globally.** `nearest_correct` says a
   reading names holes correctly whenever `ρ = 2W/B < 1`. Phase 35 located the
   obstruction exactly — the stalling spread is `D_6^4`'s, and the four
   remaining failures belong to that same type — and showed that deleting
   references cannot earn the criterion (`resolves_of_subset`,
   `separation_mono`), so a deletion sweep is a floor and not a route. What is
   left is the honest pair of alternatives: find a reading whose `ρ < 1` over
   the whole ten-type set, or prove a bound saying no reading of this family
   reaches it. `per_type_correct` already certifies 3 of the 10 types, which is
   the shape a partial answer would take.
2. **The faithfulness radius.** `per_type_absent` states the absence the
   deep-hole rounds have been short of, and needs `∀ y of the type,
   dist y p ≤ w`. The measured radius and the certified radius are currently
   incompatible on this data (`r ≥ 0.0659` against `r < 0.0179`), so the
   theorem is instantiated nowhere. Either an ensemble is found whose within-
   type spread meets the bound, or the incompatibility is proved rather than
   observed.
3. **The thirteen unreached types.** Unchanged: the ensemble reaches 10 of the
   23 Niemeier root systems from the 14 declared centres, and reaching the rest
   means new centres and therefore a new pre-registration.
4. **A register that arrives anonymous on its own.** Phase 37 closed the
   question this item used to ask — the carry set is a class, not a residue —
   by renaming every identifier outside a declared vocabulary and measuring
   retrieval over the result. Renaming is a faithful model of a
   cross-vocabulary goal, and it is still a model. The measurement to want is
   the same table over goals that arrive anonymous without being made so:
   statements from a second Lean development, or from a generator, scored
   against the same controls. The gate is also still a stated constant: the
   sweep shows every threshold from 1/20 to 1/4 improves on the control, which
   is robustness, not calibration.
4a. **The leak the audit found in the feature map.** The shipped structural map
   counts the type vocabulary wherever those words occur, including inside an
   identifier, so a renaming moves a coordinate on 33 of 813 queries. The
   reading that is supposed to be name-blind is therefore not quite name-blind,
   and the extent of it is measured rather than assumed. Either the map is
   narrowed to count a type word only where it is a type, or the leak is
   priced — and either way it is a measurement with its own control, not a
   patch.
5. **The planner's utility gate.** The reverse-call planner satisfies every
   safety line and fails the one that matters: it adds nothing to the shipped
   system, because the refusals it is offered are refusals it agrees with. The
   question that would close it is whether a *tool* exists that the planner
   could reach and the dispatcher cannot — which is a question about the tool
   registry, not about the planner — and until one does, D14 keeps it where it
   is.

Whichever is taken, the discipline is that of Phases 20–24 and 31–35: the thing
must be *described* or *measured* rather than asserted, the study must be
committed before the code that measures it, what does not generalise must be
counted rather than hidden, the old path must be frozen so the new one has
something to agree with, and the end-to-end evaluation must return the same
answers and the same refusals.

---

<!-- figures:history -->

*The closed phases that used to follow live in
[`archive/MASTER_PLAN_ARCHIVE.md`](archive/MASTER_PLAN_ARCHIVE.md), unchanged.  The counts in
them were true when each phase was closed and are deliberately left alone; for
the project as it is now, see [`overlay/FIGURES.md`](overlay/FIGURES.md), which
is regenerated from the code.*
