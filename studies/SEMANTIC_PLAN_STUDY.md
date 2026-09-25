# Typed question plans — a bridge from English to the operations the machine already has

## Tier 0 — the coarse read

**Question.** The frozen language probe is refused seventeen times of twenty although the registers hold most of the answers behind the formal grammar. Does a typed planner that reads a question into operations the machine already has, and answers only when every licensed reading agrees, reach those answers without a wrong one?

**Verdict.** Through the planner the frozen probe passes the mark declared before it was first run, and the held-out questions committed before the planner existed are answered or correctly refused in all but one; the one wrong answer is a register reading that disagrees with the world, not a misreading of the question, and two licensed readings that disagree are refused with both named.

**Deciding figure.** The frozen probe scores <!--figure:plans-probe-correct-->19<!--/figure--> correct, <!--figure:plans-probe-wrong-->0<!--/figure--> wrong and <!--figure:plans-probe-refused-->1<!--/figure--> refused through the planner, against <!--figure:plans-bare-probe-correct-->2<!--/figure-->, <!--figure:plans-bare-probe-wrong-->1<!--/figure--> and <!--figure:plans-bare-probe-refused-->17<!--/figure--> through the grammar; of <!--figure:plans-held-total-->110<!--/figure--> held-out questions it answers <!--figure:plans-held-correct-->86<!--/figure--> correctly and refuses <!--figure:plans-held-correct-refusal-->22<!--/figure--> correctly, with <!--figure:plans-held-wrong-->1<!--/figure--> wrong.

**Recomputed by.** `glm_universal.reasoning.typed_plans.plans_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 1. What this round took, and from where

Not a candidate of [`STATUS.md`](../STATUS.md) §3.4. The round took the
supplied roadmap, `source_material/GLM_IMPROVEMENT_ROADMAP.md`, whose first
two work packages are a typed intermediate representation between text and
the session, and a held-out evaluation that the runtime's own tables did not
generate. The reason for taking it over §3.4 is a measurement the roadmap
quotes and this round re-took before writing anything: the frozen probe of
[`BLOCKERS_STUDY.md`](BLOCKERS_STUDY.md), asked through
`GeometricSession.ask`, still scored two correct of twenty — although
[`PROBE_ORACLE_STUDY.md`](PROBE_ORACLE_STUDY.md),
[`FIELD_SURFACE_STUDY.md`](FIELD_SURFACE_STUDY.md) and
[`ORDERING_STUDY.md`](ORDERING_STUDY.md) had between them made sixteen of the
twenty expressible in the formal grammar. The answers were held; the English
could not reach them. Widening the vocabulary had already been measured and
moved nothing.

## 2. What a plan is

`glm_universal.runtime.semantic_plan` is not a parser that answers. It reads
a question into **typed plans** and lets the existing operations decide which
of them hold.

* **A frame** recognises one shape of question — *the F of X*, *is A more P
  than B*, *which element has the largest F*, *convert Q U to U*, *is N
  prime*, fourteen in all (<!--figure:plans-frames-->18<!--/figure-->) — and
  emits a plan: an intent, typed slots (row, field, table, number, unit,
  comparative), and for each slot the words it was read from and the rule that
  grounded them.
* **Grounding** is against what the machine holds, never against a guess. A
  row slot is grounded by the field surface's own aliases, with class words
  (*the element*, *the ratio*) stripped, spaces joined to underscores, a
  rational literal read against the declared `ratio` fields, or a module
  component of a declared function surface. A field slot is grounded only
  against the fields **that row answers to**, by the register's own field
  names read as words (`atomic_weight_u` is *atomic weight*) and a short
  declared synonym table. A slot that grounds to nothing produces no plan.
* **Licensing.** Every plan runs — a formal query through the session, or an
  exact computation — and is licensed when it solves. The answer is given
  only when the licensed plans agree on one value. Two licensed plans that
  disagree are refused as ambiguous, both named. With no plan at all, or none
  licensed, the question falls through to the grammar unchanged.

`RequestProject/GLM/SemanticPlan.lean` proves the rule rather than measuring
it: the verdict does not depend on the order the frames ran in
(`accept_perm`); an answer is exactly a value every licensed plan gave
(`accept_eq_answered_iff`); two licensed readings that disagree are refused
(`disagreement_is_ambiguous`); with no licensed plan the planned path says
exactly what the grammar says (`planned_conservative`), it never says what
neither a licensed plan nor the grammar said (`planned_sound`), and it refuses
what the grammar answered only on a disagreement
(`planned_refuses_only_on_disagreement`). The obvious rule — take the first
plan that solves — is refuted twice over on the torque question:
`first_licensed_order_dependent` and `first_licensed_answers_a_disagreement`.

## 3. The derivation half

Two kinds of plan compute rather than route, and they are what this round adds
that is not a translation.

* **Exact integer arithmetic.** Sums, differences, products and quotients as
  exact rationals; primality by trial division with the least factor as
  witness; gcd and lcm of any number of integers. A quotient by zero, a
  primality question about a non-integer, a gcd of zeros, is refused with the
  precondition that failed.
* **Conversion between units whose relation is a definition.** A declared
  table of <!--figure:plans-units-->17<!--/figure--> units — the metre and its
  SI multiples, the 1959 international inch, foot, yard, mile, pound and
  ounce, the minute, hour and day — each with its exact factor and the
  definition that makes it exact. A conversion between two quantities is
  refused; a unit the table does not hold is not converted. A non-terminating
  result is written `n/d` beside a decimal rounded half-even, and the rounding
  is said.

No float is constructed on either path.

## 4. The sets, and when each was written

| set | size | written | labels from |
|---|---|---|---|
| `probe-canonical`, `probe-paraphrase` | 20 + 20 | frozen in the blockers round | the probe's own fragments |
| `paraphrases` | 60 | commit `8064795`, before any planner code | the probe's fragments, narrowed |
| `compositions` | 30 | commit `8064795` | IUPAC atomic weights, the 1959 definitions, number theory |
| `adversarial` | 20 | commit `8064795` | the right outcome is a refusal, or one narrow answer |
| `stress` | 47 | commit `ca257db`, after the planner's first cut and before it was run | the same sources |

The three sets of `8064795` are the evidence of reach: nothing in them was
edited after the planner first ran. The stress set was written by an author
who had read the frames and was trying to break them, so it is weaker
evidence of reach and stronger evidence of safety. Its first run is frozen in
`glm_universal.reasoning.typed_plans.STRESS_FIRST_RUN`:
<!--figure:plans-stress-first-correct-->28<!--/figure--> correct,
<!--figure:plans-stress-first-refused-->13<!--/figure--> refused and no wrong
answer. Five general frame extensions followed that run — an n-ary gcd, a
comparison introduced by *which element is*, a trailing *proved in*, the
inverse relation by value, and the two-term dimensional check read at two
layers — and the set now scores
<!--figure:plans-stress-correct-->33<!--/figure--> correct,
<!--figure:plans-stress-wrong-->0<!--/figure--> wrong,
<!--figure:plans-stress-refused-->8<!--/figure--> refused and
<!--figure:plans-stress-correct-refusal-->6<!--/figure--> correct refusals.
That second figure was taken knowing the first and is reported beside it, not
in its place. The grammar alone, on the same set, gives
<!--figure:plans-stress-bare-correct-->2<!--/figure--> correct answers and
<!--figure:plans-stress-bare-wrong-->2<!--/figure--> wrong ones: `tell me
about oxygen` and `describe Fe` answer with a carrier's geometry and never say
what the row is, which the planner's describe frame repairs by adding the
row's own name.

## 5. What happened

<!-- generated: plans-sets -->
| set | path | correct | wrong | refused | correct refusal |
|---|---|---|---|---|---|
| `probe-canonical` | bare | 2 | 1 | 16 | 1 |
|  | planned | 19 | 0 | 0 | 1 |
| `probe-paraphrase` | bare | 2 | 0 | 17 | 1 |
|  | planned | 19 | 0 | 0 | 1 |
| `paraphrases` | bare | 4 | 0 | 53 | 3 |
|  | planned | 57 | 0 | 0 | 3 |
| `compositions` | bare | 0 | 0 | 30 | 0 |
|  | planned | 29 | 1 | 0 | 0 |
| `adversarial` | bare | 0 | 0 | 1 | 19 |
|  | planned | 0 | 0 | 1 | 19 |
| `stress` | bare | 2 | 2 | 37 | 6 |
|  | planned | 33 | 0 | 8 | 6 |

through the planner the frozen probe scores 19 correct, 0 wrong and 1 refused of 20 against the grammar's 2, 1 and 17, and passes the mark declared before the probe was first run; on the 110 held-out questions committed before the planner existed it gives 86 correct answers and 22 correct refusals with 1 wrong, against 4, 22 and 0 through the grammar.

the held-out sets were written by the same author as the frames, an hour before them, so they measure phrasing the author anticipated as well as phrasing he did not; the stress set was written knowing the frames and is evidence of safety rather than of reach. Every gained answer is an operation the system already had, reached from English: the table gains are coverage, not reasoning.
<!-- end generated -->

Scored exactly as the blockers study scores it, the frozen probe passes the
mark of ten correct and at most one wrong declared before it was first run.
In all, <!--figure:plans-questions-->197<!--/figure--> questions were asked
both ways. The <!--figure:plans-held-bare-correct-->4<!--/figure--> correct
answers, <!--figure:plans-held-bare-correct-refusal-->22<!--/figure--> correct
refusals and <!--figure:plans-held-bare-wrong-->0<!--/figure--> wrong answers
of the grammar on the held-out sets are the control the planner is measured
against.

## 6. The exceptions, by name

<!-- generated: plans-exceptions -->
| set | question key | asked | outcome | what it said |
|---|---|---|---|---|
| `compositions` | `c-weight-iron` | how heavy is an iron atom? | wrong | atomic_weight_u of Fe = 1396/25 (= 55.84) -- from the element table (source), read as it is held; nothing on this path computes it |
| `stress` | `s-verify-two` | does energy have the same dimensions as torque? | ambiguous | refused: 2 licensed readings disagree: energy = torque -> False; same-field -> True |
<!-- end generated -->

**The wrong answer is a data-truth finding, not a misreading.** The register
reading disagrees with the world. *How heavy is an iron atom?* is
read as the element register's `atomic_weight_u` for `Fe`, which holds
`1396/25`, that is `55.84`. The label, written before the planner existed, is
the IUPAC standard atomic weight `55.845`. The register holds iron to four
significant figures where it holds carbon (`12.011`) and oxygen (`15.999`) to
five. The planner read the question correctly and the register answered at a
precision the world does not use; the label is not edited, and the row is
the first entry of the external-truth work the roadmap names as its P5.

**The ambiguity is the layers principle, measured.** *Does energy have the
same dimensions as torque?* has two licensed readings: the session's `verify`
reads the extended dimension vector, which keeps the plane angle, and says no;
the `dimension_si7` field is the SI projection, which drops it, and says yes.
[`PROJECT_DIRECTIVES.md`](../PROJECT_DIRECTIVES.md) asks that a claim be read
at more than one layer before it is called absent; here it is read at two, the
two disagree, and the answer names both instead of choosing the one that came
first.

## 7. What was gained, classified

Every answer the planner gives that the grammar did not is classified by the
faculty of the plan that licensed it (directive D15):
<!--figure:plans-gains-table-->76<!--/figure--> are `table` — a field read,
a dimension, a relation, a description; <!--figure:plans-gains-derive-->70<!--/figure-->
are `derive` — an exact computation, a conversion, a comparison of two
readings, a fold over a column, a dimensional check, a molar mass recomputed
from its formula; and <!--figure:plans-gains-address-->1<!--/figure--> is
`address`, the inverse relation found by value. In all
<!--figure:plans-gained-->147<!--/figure--> gains, and
<!--figure:plans-ambiguous-->1<!--/figure--> ambiguity refusal.

The `table` gains are coverage and nothing more: the operation existed, and
only the English was in the way. The `derive` gains are answers no register
holds — 91 is not prime because 7 divides it, 3 metres is `1250/127` feet —
and they are the part of the round that moves the target.

## 8. What it does not do

* **It is opt-in.** `GLM.py --plan` and `GeometricSession.ask_planned` use
  it; `GLM.py -q` and `GeometricSession.ask` do not, so the 177-case contract
  evaluation is untouched. Asked in-process through both paths, the 177 cases
  differ in two answers, both still correct and neither an expected refusal.
  Making the planner the default needs the three-column trace to describe a
  computed plan, and is named for the next round.
* **It reads one question at a time.** A follow-up — *and oxygen?* — is the
  conversation layer's, and a question naming two rows at once (*the atomic
  weight of carbon and oxygen*) is refused rather than half-answered.
* **The frames are a fixed table.** A shape no frame reads falls through to
  the grammar. Of the stress set's refusals, most are shapes of that kind or
  facts no register holds (the boiling point of water, the atomic weight of
  carbon-14, velocity as an integral).
* **The held-out sets share an author with the frames.** They were written
  first and committed first, and that is the whole of their independence. An
  independently written set is the stronger test, and is named for the next
  round.
