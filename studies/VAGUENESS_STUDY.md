# The standing rule for a vague `related_to` triple

## Tier 0 — the coarse read

**Question.** The lexicon's `related_to` triples say *that* two concepts are linked without saying how. Two earlier rounds decided the 66 it holds, the second of them by hand. What decides the next one?

**Verdict.** A router of four routes tried in order, of which only the last asks a person, and a gate that admits a proposer rule only for agreeing with every hand decision it fires on.

**Deciding figure.** 34 of the 66 triples are decided without a person — 27 dimensionally, 1 by the conjugate register, 6 by the one proposer rule of 4 that passed the gate — and the other 32 are referred with the evidence collected.

**Recomputed by.** `glm_universal.reasoning.vagueness.vagueness_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 1. The gap was never the 66

`related_to` is the lexicon's admission that two concepts are connected without
a statement of how. It transports nothing: the analogy layer refuses it by name,
because "A is related to B" licenses no step from C.

Two rounds had already worked on them. `measure_view.relation_repair` converts
the 27 the physics register can decide — same dimension, or differing by one
quantity of a fixed basis. `data_objects/denotation.py` then decided the
endpoints of the remaining 39 **by hand**, in a register of 36 verdicts, and
that register is complete: nothing waits on a lookup.

So the 66 were closed, and the note left behind was honest about what still was
not:

> the lexicon's vague `related_to` triples as new ones are added.

Every addition brought the hand work back. A discipline that needs a person for
each new triple is one that will quietly stop being followed — the person will
be busy, the triple will sit undecided, and the register will be silently
stale. What was missing was not more decisions. It was a **standing rule**.

## 2. The four routes

`reasoning/vagueness.py` puts a triple to four routes **in order**, of which
only the last asks a person:

1. **`dimensional`** — the physics register decides both endpoints: they share
   a dimension, or they differ by exactly one quantity of the basis. 27 of 66.
2. **`conjugate`** — both endpoints are columns of one row of the
   energy-conjugate register ([`CONJUGATE_STUDY.md`](CONJUGATE_STUDY.md)), so
   the relation between them is `effort_of`, `extent_of` or `conjugate_of`.
   1 of 66 is decided *here and nowhere else*.
3. **`proposed`** — an admitted proposer rule classifies an endpoint the
   registers do not dimension. 6 of 66.
4. **`referred`** — a person is asked, and is handed the evidence rather than
   the failure. 32 of 66.

The order is part of the specification, not an artefact. `heat`/`temperature`
is decided by two routes and is routed `dimensional`, because the register that
measures is asked before the register that classifies. The Lean file states this
as `route_eq_conjugate_iff` carrying `¬ dimensional t` rather than leaving the
priority to the order of the `if`s.

The routing is total and single-valued: `every_triple_routed` is true, and
27 + 1 + 6 + 32 = 66.

## 3. What the conjugate route adds

The conjugate register fires on 4 triples. Three of them the dimensional route
also decides, and where both fire **they agree** — the sharper reading wins on
information, not on precedence: the dimensional rule says `heat` and
`temperature` differ by a factor, and the conjugate register names that factor's
role, `entropy` being the extent that `temperature` acts through.

The fourth, `entropy`/`temperature`, is reached by no other rule. It is not a
difference of dimension at all; it is the relation between an effort and its own
extent, which the physics register has no way to express.

Two pairs — `torque`/`force` and `pressure`/`force` — have **both endpoints
placed and are deliberately not converted**, because they are placed in
different rows. The register relates a name to its own row's columns; letting it
relate one domain's effort to another's would have produced an answer with
nothing behind it. Sixty of the 66 have an endpoint the conjugate register does
not place at all.

## 4. The gate on a proposer rule

A proposer rule reads the lexicon — a part of speech, a suffix, a countability —
and proposes a denotation verdict for an endpoint the registers do not
dimension. That is exactly the kind of rule that is easy to write and dangerous
to trust, so it is scored against the 36 names the hand register already
decided, and the rule never sees that register while it runs.

> The gate admits a rule only for agreeing with every hand decision it fires
> on: a rule is admitted only if it fires on at least **5** of the hand-decided
> names and agrees with the hand decision on **every one** of them. A wrong
> verdict is worse than an abstention, so the gate is agreement without
> exception rather than accuracy on average.

Four rules were tried. One passed.

| rule | proposes | fired on | agreed | admitted | the disagreement that refused it |
| --- | --- | --- | --- | --- | --- |
| `verb_is_a_process` | `process` | 10 | 10 | **yes** | — |
| `nominalisation_of_a_verb` | `process` | 2 | 1 | no | `measurement` is polymorphic, not process (and 2 is not a test) |
| `abstract_noun_is_an_abstraction` | `abstraction` | 5 | 3 | no | `function` is polymorphic; `space` is ambiguous |
| `mass_noun_is_a_carrier` | `carrier` | 7 | 5 | no | `function` is polymorphic; `reaction` is process, not carrier |

The refused rules are kept, with their disagreements named. A rule refused on a
named disagreement is a finding: `mass_noun_is_a_carrier` agreed on 5 of the 7
names it fired on — a clear majority — and is refused, which is the gate doing
work rather than describing an outcome a looser gate would have reached anyway.

The admitted rule covers 10 of the 36 hand-decided names, leaving 26 that still
rest on a person's judgement. The rule does not replace the hand register; it
means the next verb does not need one.

## 5. A referral is a decision, not a failure

The 32 referred triples are not a residue. Each carries the evidence the three
mechanical routes collected: which endpoint the physics register dimensions,
whether the conjugate register places either, what the lexicon says each is, and
whether the hand register has already ruled on either name. The person is told
what was tried.

This is the difference the round was really about. Before it, an undecided
triple was a lookup that returned nothing. Now it is a decision to ask, with a
record of why asking is necessary.

## 6. The formal side

[`RequestProject/GLM/Vagueness.lean`](../RequestProject/GLM/Vagueness.lean)
carries the part that is not a measurement:

* the router is **total** — every triple gets a route, so a referral cannot be
  a crash;
* it is **single-valued**, which is what makes the counts a partition;
* the order is **real**: each route's `iff` names the routes that must have
  declined first, so priority is specified rather than implemented;
* a referral **certifies** that all three mechanisms declined, which is what
  makes it informative;
* and the gate buys exactly one thing, stated as `proposal_correct_of_admitted`:
  an admitted rule never contradicts the hand register, so it may be trusted at
  the names the register is silent about — the only place it is ever consulted.

`majority_is_not_enough` exhibits the gate refusing a rule that agreed on 5 of
7, so the theorem file contains the counterexample as well as the guarantee.

## 7. How to re-run it

```bash
cd overlay
PYTHONPATH=. python3 -c "from glm_universal.runtime.session import GeometricSession as S; print(S().ask('report vagueness').answer)"
PYTHONPATH=. python3 -m pytest glm_universal/tests/test_vagueness.py -q
cd .. && lake build RequestProject.GLM.Vagueness
```

## 8. Limits

The routes do not decide every triple and are not meant to. Half of them are
still referred, and the honest reading of 34 of 66 is that the mechanical part
of this work was about half of it.

Three of four proposer rules were refused, which is the measurement's own
warning: the temptation to add a fourth rule because it feels right is exactly
what the gate exists to resist, and a rule added without being scored against
the hand register would not be admitted by this module — it would simply not be
in it.

Nothing here revisits the 66 already-decided triples' verdicts. The hand
register remains the ground truth; the router's contribution is that it agrees
with it where it fires, and that the next triple has somewhere to go.
