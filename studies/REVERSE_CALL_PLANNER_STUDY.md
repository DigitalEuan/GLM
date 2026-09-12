# The reverse-call planner — a problem-driven front end, in the sandbox

## Tier 0 — the coarse read

**Question.** The runtime decides a query's *kind* before it looks at the
problem, and one kind means one solver. An older proposal in the source
material inverts that: parse the string into a problem, then let a planner
select every tool whose declared precondition the problem satisfies. Does that
inversion buy anything the current system does not already have — and can it be
made safe enough to promote out of a sandbox?

**Verdict.** It buys something on the declared task set and nothing at all on the project's own evaluation set, and it is therefore not promoted. The safety gate holds and the utility gate does not: the planner answers five declared tasks the plain runtime refuses, every answer it gives is checked by a second tool, and no principled refusal ever reaches it — but of the four evaluation refusals it is offered, it correctly refuses all four, so under the declared fallback rule it would add nothing to the shipped system today.

**Deciding figure.** 10 of 15 declared tasks answered, all 10 independently checked, 5 of them beyond the plain runtime; and over 147 evaluation cases, 4 refusals offered to the planner and 0 answers gained.

**Recomputed by.** `glm_universal.sandbox.planner.planner_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0a. The reading in one paragraph

It buys something on the declared task set and nothing at all on the project's own evaluation set, and it is therefore not promoted. The safety gate holds and the utility gate does not: the planner answers five declared tasks the plain runtime refuses, every answer it gives is checked by a second tool, and no principled refusal ever reaches it — but of the four evaluation refusals it is offered, it correctly refuses all four, so under the declared fallback rule it would add nothing to the shipped system today. In figures: 10 of 15 declared tasks answered, all 10 independently checked, 5 of them beyond the plain runtime; and over 147 evaluation cases, 4 refusals offered to the planner and 0 answers gained.

The same reading, recomputed rather than written:

<!-- generated: plannersandbox-tier -->
**The planner answers 10 of 15 declared tasks, and every answer it gives is independently checked (10 of 10).**  5 of them are questions the plain runtime refuses: 'derive energy', 'derive pressure', 'describe energie', 'nearest to k_B', 'layers energy and torque'.  The remaining 5 are refusals, each classified before it is reported.  Every one of the 7 promotion lines is measured here, and 1 do not: answers_something_the_runtime_does_not.
<!-- end generated -->

---

## 0. What this document is

A **sandbox round**. The module it measures,
`glm_universal.sandbox.planner`, lives in `glm_universal/sandbox/`, and the
rule of that directory is that nothing the system computes with may import from
it — so the planner cannot change a single answer the runtime gives while this
document is being written. The one declared exception is the block renderer
above, which imports it lazily in order to report on it, and that exception is
itself checked by a test.

The source is `source_material/REVERSE_CALL_PLANNER_README.md` and
`source_material/glm_reverse_call_planner_v2.py`, an earlier design that was
supplied rather than written here. (Both were moved into `source_material/`,
where supplied material lives, when this round started; nothing in them was
edited.) The v2 script does not run in this repository — it is written against
absolute paths in a scratch directory that does not exist here, and against a
sixty-seven-tool registry that never existed in this tree. What is taken from
it is the *idea*, restated against the modules this project actually has.

---

## 1. The inversion, stated exactly

The shipped runtime is a **kind dispatcher**:

    string -> a kind, decided by the parser -> the one solver for that kind
           -> an answer, or that solver's refusal

The planner is **problem-driven**:

    string -> Problem (goal, operands, domain, constraints)
           -> every tool whose declared precondition the problem satisfies
           -> those tools run cheapest first, each checked where a check exists
           -> the cheapest verified answer, or a refusal naming every tool tried

Three consequences follow, and they are the whole of the case for it:

1. **A refusal names what was tried.** A kind dispatcher's refusal is one
   solver's refusal. The planner's refusal is a list: tool, precondition,
   reason. That is a more informative negative and a much easier one to act on.
2. **Answers can be cross-checked.** When two tools apply to the same problem,
   the second is an independent check on the first, and the plan reports
   whether it agreed. Ten of ten answers below are checked this way.
3. **Cost becomes visible.** Each tool carries a declared integer price and the
   plan reports the total, so a cheap answer and an expensive one are not
   reported as the same thing.

---

## 2. What it takes from the escalation round

The planner is not a free-running tool loop, and three rules from
[`QUERY_ESCALATION_STUDY.md`](QUERY_ESCALATION_STUDY.md) are what stop it being
one.

* **A principled refusal stops the plan.** The planner uses the shipped
  classifier `glm_universal.runtime.escalation_loop.classify`. A refusal that
  is ill formed, underdetermined, or grounded in no register ends the plan
  immediately; the remaining tools are not tried. A planner that tries eleven
  tools against an underdetermined question has not been thorough, it has been
  noisy.
* **Cost is charged, not assumed away.** Rungs and tools both cost, and a
  budget of 12 caps a plan. A tool skipped for want of budget is recorded as
  skipped, so the plan cannot look cheaper than it was by forgetting what it
  could not afford.
* **The escalation loop is itself one of the tools.** Where the plain register
  reading refuses, the planner may pay to climb the declared ladder, and the
  answer carries the layer it was found at.

---

## 3. The registry

<!-- generated: plannersandbox-tools -->
| tool | cost | goals | checked | postcondition |
|---|---|---|---|---|
| `reference` | 1 | describe, meaning | no | the meaning a term denotes |
| `runtime` | 1 | describe, nearest, verify, analogy, report, coherence, meaning, approximate | no | the register reading of the question |
| `verifier` | 2 | verify | no | whether an equation is dimensionally consistent |
| `term_arithmetic` | 2 | describe, evaluate | no | the dimension of a written expression |
| `escalated_runtime` | 3 | describe, nearest, verify, analogy, report, coherence, meaning, approximate | no | the register reading, escalated along the declared ladder |
| `controller` | 3 | derive | yes | a derivation plan for a register quantity |
| `layers` | 4 | layers | yes | the first layer of the stack that separates two carriers |
| `exact_real` | 4 | approximate | yes | an exact real read to a stated number of places |

The plan's budget is 12 and its sub-goal depth is 2: both are declared in the module, and a tool skipped for want of budget is recorded as skipped rather than dropped.
<!-- end generated -->

Eight tools, not sixty-seven. A tool is registered when it has a precondition
that can be checked cheaply and a postcondition that can be stated; registering
the rest of the system this way is real work, and it is exactly the work the
promotion checklist is waiting on.

---

## 4. The declared task set

Fifteen tasks, declared in the module, including the five the planner is
expected to refuse. A task set consisting of things that work measures nothing.

<!-- generated: plannersandbox-tasks -->
| task | goal | outcome | tool | cost | checked | runtime |
|---|---|---|---|---|---|---|
| `derive energy` | `derive` | answered | `controller` | 9 | yes | refuses |
| `derive pressure` | `derive` | answered | `controller` | 9 | yes | refuses |
| `derive unobtainium` | `derive` | refused (no-tool) | — | 0 | no | refuses |
| `verify energy = force * length` | `verify` | answered | `verifier` | 6 | yes | answers |
| `verify energy = force * time` | `verify` | answered | `verifier` | 6 | yes | answers |
| `describe energy` | `describe` | answered | `escalated_runtime` | 5 | yes | answers |
| `describe energie` | `describe` | answered | `escalated_runtime` | 5 | yes | refuses |
| `describe unobtainium` | `describe` | refused (absent) | — | 5 | no | refuses |
| `describe justice` | `describe` | refused (absent) | — | 5 | no | refuses |
| `meaning of H2O` | `meaning` | answered | `escalated_runtime` | 5 | yes | answers |
| `nearest to k_B` | `nearest` | answered | `escalated_runtime` | 4 | yes | refuses |
| `layers energy and torque` | `layers` | answered | `layers` | 4 | yes | refuses |
| `approximate sqrt(2)+1 to 20 places` | `approximate` | answered | `escalated_runtime` | 8 | yes | answers |
| `approximate banana to 20 places` | `approximate` | refused (absent) | — | 8 | no | refuses |
| `Ca : Sc :: Ba : ?` | `analogy` | refused (underdetermined) | — | 1 | no | refuses |

Every task is reported, including the 5 the planner is expected to refuse: a task set of things that work measures nothing.
<!-- end generated -->

---

## 5. The fallback reading — the whole evaluation set

The task set above is the planner's own; a set a module chose for itself can
only ever be an existence proof. The gate that decides promotion is measured
over the project's **entire evaluation set**, under a rule declared before it
was run:

> The runtime answers first and its answers are untouched. The planner is
> consulted only where the runtime refuses, and only where the shipped
> classifier calls that refusal escalatable.

Under that rule the runtime's answers cannot move — not because the planner
agrees with them, but because it is never asked. That makes the safety gate
structural, and leaves the utility gate to carry the whole weight of the
argument.

<!-- generated: plannersandbox-fallback -->
| reading | value |
|---|---|
| evaluation cases | 147 |
| the runtime answers | 133 |
| the runtime refuses | 14 |
| of those, classified principled | 10 |
| the planner is consulted on | 4 |
| principled refusals reaching the planner | 0 |
| answers the runtime does not give | 0 |
| **safety gate** | **True** |
| **utility gate** | **False** |

The rule measured is: the runtime answers first and its answers are untouched; the planner is consulted only on a refusal, and only on a refusal the escalation classifier calls escalatable.
<!-- end generated -->

**And the utility gate fails.** Of the 14 refusals in the evaluation set, 10
are classified principled and are never offered to the planner at all. The
remaining 4 are offered, and the planner refuses all four — correctly:

| case | question | what the planner did |
|---|---|---|
| `describe-unknown-word` | `describe unobtainium` | refused; the escalated reading certifies the absence within two edits |
| `trilinear-nonaxes` | `trilinear 1 2 3` | refused, and its own reading of the refusal calls the question ill formed, so the plan stopped |
| `unknown-nonsense` | `please compute the square root of a banana` | refused, ill formed, plan stopped |
| `report-unknown-subject` | `report nonsense subject` | refused; no tool's precondition is met |

So the honest reading of this round is not *the planner is worse*; it is that
**the evaluation set contains no headroom for it**. Every question in it that
the runtime refuses is a question that ought to be refused. The five gains on
the declared task set are real, and they are all off-set: derivations the
controller finds and the verifier confirms, a misspelling the escalated reading
resolves, a constant reached through the reference layer, and a layer
comparison. None of those has a case in the evaluation set yet.

A useful by-product, and a candidate change to the shipped classifier: on two
of the four — `trilinear 1 2 3` and the banana — the planner's *own* reading of
the refusal text classifies the question as ill formed where the runtime's
refusal text does not carry a marker that
`glm_universal.runtime.escalation_loop.PRINCIPLED_MARKERS` recognises. Those
two are climbed by the escalation loop today and stopped by the planner. The
loop reaches the same verdict, so nothing is wrong; but two markers are missing
from the shipped list, and the planner found them.

---

## 6. The promotion checklist

<!-- generated: plannersandbox-promotion -->
| line | reading |
|---|---|
| deterministic | True |
| exact | True |
| no regression against the runtime | True |
| every refusal classified | True |
| every answer independently checked | True |
| no principled refusal reaches the planner | True |
| answers something the runtime does not | False |
| **ready to leave the sandbox** | **False** |

The planner ships when every line above is true.  While any is false it stays in the sandbox, and the false line is the work that remains -- not a caveat to be written around.

Eight tools, not sixty-seven: a tool is registered here when it has a precondition that can be checked cheaply and a postcondition that can be stated, and registering the rest is the work the promotion checklist is waiting on.  The parser is deliberately thin, so a problem it reads wrongly is planned wrongly -- which is a reason the planner is in the sandbox.
<!-- end generated -->

The checklist is computed on every call, and `ready` is the conjunction. It is
`False`, and the line that is false is the one that matters: the planner does
not yet answer anything the shipped system does not. That is the work
remaining, and it is a statement about the evaluation set as much as about the
planner — extending the evaluation set with cases the planner's tools *can*
reach would make the line true without the planner improving at all, which is
why the line must be read together with §5 and not on its own.

**What would honestly earn promotion.** Either (a) evaluation cases that the
runtime refuses and a registered tool can answer, added to the evaluation set
for reasons independent of the planner; or (b) enough of the system registered
as tools that the fallback has real headroom. (b) is the substantial version,
and it is the version the source proposal was reaching for.

---

## 7. What this round does not do

* It does **not** change any answer the system gives. The sandbox rule is
  checked, not intended: no shipped module imports the planner, and the one
  documentation-layer import is tested for.
* It does **not** claim the parser is adequate. It is deliberately thin, and a
  problem it reads wrongly is planned wrongly. That is a reason the module is
  in the sandbox, and it is why the goal it inferred is reported beside every
  task in §4.
* It does **not** re-run the source proposal's own measurements. The v2 script
  does not run here, and re-creating its sixty-seven-tool registry in order to
  reproduce numbers it reports about itself would not be evidence about this
  system.
* It does **not** search for a task set that makes the utility gate pass. The
  fifteen tasks were declared before they were run, and the fallback rule was
  declared before the evaluation set was read.

---

## 8. How to re-take every number

```
python3 -m glm_universal.tools planner        # the report, recomputed
python3 -m pytest glm_universal/tests/test_sandbox_planner.py
```

Integers and `Fraction` only; no float is constructed and no random source is
consulted. Nothing here is cached: the whole report takes a few seconds and is
recomputed whenever the corpus is rendered.
