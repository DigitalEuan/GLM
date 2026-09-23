# The turn that refers back — what the supplied conversation material was worth, and what licensing buys over recency

## Tier 0 — the coarse read

**Question.** A round's worth of supplied material builds a conversational GLM on top of this substrate. Run against the package as it is now, what in it is real, and what does the one operation worth keeping answer and refuse?

**Verdict.** All eight of the supplied scripts run unmodified against the package, and two of their claims do not survive being re-run: the higher-order analogy adds no constraint that was satisfied, and the periodic table reading is a renaming of two coordinates. What holds is the thing they were built around and this package as it stands cannot hold: a turn that refers back to an earlier turn. Built here as a binding licensed by the solver, it binds 8 of 15 declared follow-ups and refuses 7, every one as declared, where a session with no memory of the conversation answers 0 of them; and the rule a reader would assume, bind to the most recent mention, differs on 3 of the 10 pronoun follow-ups it applies to — once it loses an answer the registers hold, and twice it gives a wrong answer confidently.

**Deciding figure.** <!--figure:conversation-as-declared-->15<!--/figure--> of <!--figure:conversation-declared-count-->15<!--/figure--> declared follow-ups came out as declared, <!--figure:conversation-answered-->8<!--/figure--> bound and <!--figure:conversation-refused-->7<!--/figure--> refused under all <!--figure:conversation-reasons-->3<!--/figure--> named reasons, against <!--figure:conversation-alone-->0<!--/figure--> answered without the conversation.

**Recomputed by.** `glm_universal.runtime.conversation.conversation_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 1. What this round took, and from where

This round did not take a candidate from [`STATUS.md`](../STATUS.md) §3.4. It
took the material supplied with it —
`source_material/conversation_experiment/`: eight Python scripts (v1 through
v8), a research document, five output transcripts, four generated Lean files
and a small persistent store — and asked the two questions the standing rules
ask of any supplied material: *does it run?*, and *is what it claims true?*

**It runs.** Every one of the eight scripts executes to completion against the
package as it stands, with `PYTHONPATH` pointing at `overlay/` and no repair
of any kind — no shimmed import, no stubbed register, no edited call. That is
worth stating plainly because it is the strongest evidence that the material
belongs to this system rather than beside it: it was written against these
registers, and the registers have moved under it without breaking it.

```
glm_conversation.py                 exit 0      v1, the original
glm_conversation_v2.py              exit 0      five bug fixes, episodic memory
glm_conversation_v2_extensions.py   exit 0      four registers, binding, licensing
glm_experiments.py                  exit 0      procedural replay, benchmark
glm_experiments_v2.py               exit 0      coverage, Lean, higher-order analogy
glm_experiments_v3.py               exit 0      Lean generation, persistence
glm_experiments_v4.py               exit 0      Lean proofs, extension register
glm_experiments_v5.py               exit 0      Lean compile, round-trip
```

## 2. Two claims re-run, and what became of them

The material states its findings in the plain. Two of them are checkable in a
few seconds against the shipped analogy solver and the shipped registers, and
neither claim can survive being re-run as it is stated. They are recorded here because a refuted claim is
a result, and because the operation this round shipped was chosen *instead* of
them.

### 2a. The higher-order analogy recovers nothing the first analogy had not

> *"Higher-order analogies recover Planck's constant — the intersection of
> `force:momentum::energy:?` and `force:momentum::action:?` is
> `[planck_constant, reduced_planck_constant]`."*

Re-run:

| analogy | best | `d²` | tied |
|---|---|---|---|
| `force:momentum::energy:?` | `action` | **0** | `action`, `planck_constant`, `reduced_planck_constant` |
| `force:momentum::action:?` | `area` | **1/4** | nine, including `planck_constant` |

The first analogy is an **exact** transport — the displacement
`momentum − force` is a factor of time, `energy × time` is an action, and the
three carriers of that dimension are tied at distance zero. It recovers
Planck's constant on its own. The second has *no* exact solution: its nearest
set sits at `1/4`, and `planck_constant` appears in it as a near miss rather
than as a solution. Intersecting the two therefore adds no constraint that was
satisfied; what it does do is **drop `action`**, the one exactly correct
answer, because `action` is an input of the second analogy and inputs are
excluded from its pool. The intersection is a coincidence of two nearest sets,
and the honest statement of the finding is the first row of the table.

### 2b. Atomic number is the `forall` count because coordinate 0 is `z`

> *"Atomic number Z maps exactly to the Lean `forall` count; mass number A maps
> exactly to `exists`. This is invisible to LLMs."*

The element carrier's layout begins `('z', 'atomic_weight_u', ...)`, and the
Lean feature layout's first two coordinates are the `forall` and `exists`
counts. Reading an element carrier under the Lean layout's names therefore
reports `forall = z` and `exists ≈ atomic_weight_u` — exactly, and for every
element, because it is the same number read under a different name. The
correspondence is a renaming of two coordinates, and the exactness is a
property of renaming rather than a fact about the periodic table. Under the
Positioning section of [`PROJECT_DIRECTIVES.md`](../PROJECT_DIRECTIVES.md)
this is the case the rules are written for: no claim of correspondence without
the control, and the control here — read any other register under the same
layout and the same "exactness" appears — costs nothing to run.

## 3. What was kept: the turn that refers back

Everything in the supplied package is built around a conversation, and the
package as it stands cannot hold one. Each query is answered alone:

```
describe carbon                            -> answered
describe it                                -> resolve: 'it' names no carrier
and the smallest?                          -> not recognised as any query kind
and oxygen?                                -> not recognised as any query kind
```

`glm_universal.runtime.conversation` is that gap closed, and it is closed in
the way this repository closes things: three declared surface shapes, one
exact test, and three refusals with names.

**The three shapes.** A text is a follow-up when, and only when, it is one of

* `end-flip` — *and the smallest?*: the previous `extremum` turn asked again at
  the other end of the same column;
* `subject` — *and oxygen?*: the previous turn asked again about another row;
* `pronoun` — *describe it*, `field electronegativity_pauling of it`.

Anything else is a whole query and is passed to the session untouched, which
is what makes the layer additive rather than a second parser. The order
matters and is part of the rule: *and the smallest?* matches the subject
pattern too, and is an end-flip because `the smallest` names no carrier.

**The one test.** A candidate antecedent is **licensed** when the query it
produces *solves*. Not when it is near, not when it is recent, not when it
shares a domain — when the rewritten question has an answer. That is the whole
of the idea, and it is what makes the reference a reading of the registers:

```
describe carbon
describe water
field electronegativity_pauling of it     ->  binds carbon, not water
```

`water` is the most recent mention and the molecule table holds no
electronegativity; the element table does. The geometry of the registers
decides the reference, and the recency rule is simply wrong here — not less
careful, *wrong*, returning a name with no answer behind it.

**Recency between turns, licensing within one.** Turns are scanned newest
first; within a turn the **answer** side (the rows a fold produced, the
carrier an analogy named) is tried before the **subject** side, because a turn
that produced a name is a turn about that name. The first side holding exactly
one licensed candidate binds it.

**The three refusals.**

`no-antecedent`
: Nothing earlier offers a candidate at all — a follow-up as the first turn,
  or *and the smallest?* with no column behind it.

`ambiguous-antecedent`
: The deciding side offers two or more licensed candidates. This is the
  refusal the operation exists for: after *largest abstract_concrete in
  carrier:lexicon*, whose end is attained by fourteen rows, *describe it* has
  fourteen equally good referents and the conversation does not say which.
  After *order atomic_weight_u of carbon and oxygen* it has two.

`unlicensed`
: Candidates exist and not one of them answers. *What is the
  electronegativity of it?* after a conversation about `energy` is a question
  about nothing the registers hold.

## 4. The declared set

Fifteen follow-ups were written down before they were run: eight the operation
must bind, across all three shapes, and seven refusals covering every named
reason. Each row states the outcome expected of it — the bound name, or the
refusal reason — and the measurement is whether the outcome is that one. The
*recency control* column is the second control of §5, run on the same row.

<!-- generated: conversation-declared -->
| follow-up | the turn asked | turns before it | declared | outcome | recency control | as declared |
|---|---|---|---|---|---|---|
| `pronoun-describe` | `describe it` | 1 | `C` | `C` | `C` | yes |
| `pronoun-after-extremum` | `describe it` | 1 | `Og` | `Og` | `Og` | yes |
| `pronoun-licensing-skips` | `field electronegativity_pauling of it` | 2 | `C` | `C` | `unlicensed` | yes |
| `pronoun-licensing-agrees` | `field molar_mass_u of it` | 2 | `water` | `water` | `water` | yes |
| `pronoun-analogy-answer` | `describe it` | 1 | `Ne` | `Ne` | `Ne` | yes |
| `pronoun-nearest-subject` | `describe it` | 1 | `O` | `O` | `O` | yes |
| `end-flip` | `and the smallest?` | 1 | `answer` | `answer` | `n/a` | yes |
| `subject-substitution` | `and oxygen?` | 1 | `oxygen` | `oxygen` | `n/a` | yes |
| `pronoun-tie-refused` | `describe it` | 1 | `ambiguous-antecedent` | `ambiguous-antecedent` | `atom` | yes |
| `pronoun-two-subjects` | `describe it` | 1 | `ambiguous-antecedent` | `ambiguous-antecedent` | `C` | yes |
| `pronoun-first-turn` | `describe it` | 0 | `no-antecedent` | `no-antecedent` | `no-antecedent` | yes |
| `pronoun-unlicensed` | `field electronegativity_pauling of it` | 1 | `unlicensed` | `unlicensed` | `unlicensed` | yes |
| `end-flip-no-column` | `and the smallest?` | 1 | `no-antecedent` | `no-antecedent` | `n/a` | yes |
| `subject-ambiguous` | `and nitrogen?` | 1 | `ambiguous-antecedent` | `ambiguous-antecedent` | `n/a` | yes |
| `subject-unlicensed` | `and water?` | 1 | `unlicensed` | `unlicensed` | `n/a` | yes |

the conversation layer answers 8 of the 15 declared follow-ups and refuses 7, every one of them as declared before the run, with the refusals falling under all 3 of its named reasons (ambiguous-antecedent, no-antecedent, unlicensed). Asked of a session with no memory of the conversation, 0 of the same 15 texts are answered.

the reference is the whole of the addressing here: every rewritten query is answered by the session that would have answered it written out in full, so no answer is new and no answer is changed. The recency control -- bind the pronoun to the most recent mention, licensing unchecked -- differs from the operation on 3 of the 10 pronoun follow-ups it applies to (pronoun-licensing-skips, pronoun-tie-refused, pronoun-two-subjects), and nothing here parses English beyond three declared surface patterns.
<!-- end generated -->

One correction was made to the declaration before the run rather than after
it, and it is recorded rather than quietly folded in: the
`subject-substitution` row was first written with the placeholder expectation
`answer`, meaning *the name is not the point here*, and was rewritten to name
the row it substitutes (`oxygen`) so that every row of the set is checked
against a specific outcome. No expectation of *answered* versus *refused*, and
no refusal reason, was changed at any point.

## 5. The two controls

A capability claim needs a baseline, and this one has two, both declared
before the measurement.

**No context — the system as Phase 53 left it.** Each of the fifteen texts is
asked of a session with no memory of the conversation. This is not a weakened
version of the operation; it is the package as it stood at the head of this
round. It answers <!--figure:conversation-alone-->0<!--/figure--> of the
fifteen. Every one of the eight answers the operation gives is therefore an
answer the system did not have, and every one of the seven refusals is a
refusal with a reason where the system previously produced a parse error.

**Recency — bind to the most recent mention, licensing unchecked.** This is
the rule a reader would assume, and it is the one worth measuring against,
because where it agrees the operation has bought nothing. It applies to the
<!--figure:conversation-control-rows-->10<!--/figure--> pronoun follow-ups and
differs from the operation on
<!--figure:conversation-control-wrong-->3<!--/figure--> of them, in both of the
directions that matter:

| row | operation | recency control | what the difference is |
|---|---|---|---|
| `pronoun-licensing-skips` | binds `C`, answers `2.55` | binds `water`, no answer | the control **loses an answer** the registers hold |
| `pronoun-tie-refused` | refuses, fourteen referents | binds `atom`, answers | the control **gives a wrong answer** confidently |
| `pronoun-two-subjects` | refuses, two referents | binds `C`, answers | the same, on a comparison's two rows |

So the margin is one answer gained and two wrong answers withheld, out of ten:
once the control loses an answer the registers hold, and twice it gives a
wrong answer confidently.
On the other seven the two rules agree, and the study says so: most of the
time recency is right, and the operation's value is exactly the cases where it
is not.

## 6. What is proved rather than measured

`RequestProject/GLM/Conversation.lean` states the binding over a conversation
of turns — each a list of names it produced and a list it was about — with the
licence as an arbitrary predicate, and proves what the operation is worth
independently of any register:

* `resolve_bound_licensed` — a bound name always passes the licence. Nothing
  is bound that leaves the question unanswered.
* `resolve_bound_mem` — a bound name is one the conversation mentioned. The
  antecedent comes from the conversation and nowhere else.
* `resolve_noAntecedent_iff` — the first refusal is **exactly** the
  conversation that mentioned nothing: a fact about the conversation rather
  than a failed search.
* `resolve_unlicensed_all_refused` — the second refusal means every candidate
  was tried and every one failed.
* `resolve_ambiguous_two_licensed` — the third refusal is earned: some side
  held at least two candidates that both answer.
* `resolve_stable_under_unlicensed_turn` — interposing a newer turn whose
  every name fails the licence cannot move a binding already decided.
* `most_recent_mention_is_not_the_antecedent` — the control of §5, refuted by
  exhibit: a conversation in which the latest mention fails the licence and an
  older one passes, so the two rules return different names and the control's
  name has no answer. This is the `pronoun-licensing-skips` row, stated as a
  theorem rather than as a measurement.
* `tie_is_refused` and `nothing_said_yet_is_no_antecedent` — the two refusals
  the shipped set exhibits, decided by computation.

## 7. What it decides, and what it does not

Under directive **D15** this round moved **addressing** and **refusal**.

* **Addressing.** Eight answers recovered from a query that is not the stored
  key, the key being supplied by an earlier turn. This is addressing in the
  narrow sense the target insists on: the answer was reachable, and the
  question as asked did not reach it.
* **Refusal.** Seven refusals with named reasons on a declared set, two of
  them cases where the obvious rule answers and the answer would be wrong.
* **Not derivation.** Nothing here computes an answer. Every rewritten query
  is answered by the same solver that would have answered it written out in
  full, so the layer can add an answer and can never change one. Where the
  underlying kind derives — the `extremum` fold behind *describe it* — the
  derivation is that kind's and was counted in its own round.

## 8. Limits

* **Three shapes, and they are surface patterns.** *the one before that*,
  *both of them*, *why?* are not follow-ups to this operation, and a fourth
  pattern is a fourth declaration rather than a generalisation. Nothing here
  parses English.
* **Recency between turns is a rule, not a result.** It is declared, and the
  Lean file proves only that an *unlicensed* newer turn cannot displace a
  binding. A newer turn whose candidate *is* licensed takes precedence, and
  there are conversations where that is the wrong reading.
* **Licensing costs a solve per candidate.** The fourteen-row tie costs
  fourteen trial queries before it refuses. The trials are recorded in the
  session's own inference history, which is deliberate — a trial is an
  inference that was run — but it means a follow-up is not free, and a very
  wide tie is the worst case.
* **One pronoun set, one language.** `it` and `that`; a longer list buys
  coverage at the price of a rule nobody can state.
* **The licensing trials are paid again on every ask.** *Fixed in Phase 56:*
  `glm_universal.runtime.plan_store` keeps a resolved follow-up — refusals
  exactly as bindings — and `Conversation` takes one as an optional `store=`,
  which takes the fifteen declared follow-ups from 27 trials to 0 without
  changing an outcome. [`SUPPLIED_PORTS_STUDY.md`](SUPPLIED_PORTS_STUDY.md)
  §4.
* **Four of the six pieces below were taken in Phase 56**, two of them into
  the package and two into the sandbox; the other two are still where this
  study left them.

## 9. What the supplied material still holds, and what it would have to prove

The last column was written before any of these was attempted. The *outcome*
column is Phase 56's, and what it records is written up in
[`SUPPLIED_PORTS_STUDY.md`](SUPPLIED_PORTS_STUDY.md).

| piece | what it is | what a round taking it would have to measure | outcome |
|---|---|---|---|
| content-addressed procedure store | successful plans keyed by the SHA-256 of the plan, replayed on a second ask | a speed-up is a cost result, not a target result (D15); it would have to show a *refusal* preserved across replay, or it is maintenance | **shipped** — `runtime/plan_store.py`, `GLM.PlanStore`: 7 of 7 refusals replayed, trials 27 → 0 |
| four-register memory split | episodic / semantic / procedural / preference registers with different decay | which questions are answered *because* of the split that are not answered without it | **sandbox** — none are: a pronoun names no concept, so the split is recency with a decay rate |
| role-filler binding `R⊗A⊗B` | Hadamard-permutation and parity-XOR bindings, both said to be recoverable | recoverability is a theorem, not a demo: state it over the substrate and prove it, with the collision rate as the control | **shipped** — `reasoning/role_binding.py`, `GLM.RoleBinding`: the parity binding inverts unconditionally, the product binding is refuted, 424 of 1,143 carriers nameable |
| trajectory licensing | each step of a reasoning chain tagged registered / typed / derived / unlicensed | the strict mode's demotions, on a declared set, against the answers it gives up | not taken |
| Lean generation from carriers | theorem *shapes* emitted from carrier coordinates | these compile to `sorry`; a round would have to close one of them, and D8 says the Lean file is the specification, not the output | **sandbox** — the supplied round-trip check never reads what it generated, and the real one returns 0 of 12 |
| missing-node proposer | unlicensed transitions proposed as new carriers | a proposed carrier is a claim about the register: the control is whether the proposal survives the register's own admission test | not taken |

## 10. Re-running it

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.tools conversation        # the declared set, both controls
PYTHONPATH=. python3 -m glm_universal.runtime.conversation      # the same, terse
PYTHONPATH=. python3 -m pytest glm_universal/tests/test_conversation.py -q
cd .. && lake build RequestProject.GLM.Conversation
```

And the supplied material itself, unmodified:

```bash
cp source_material/conversation_experiment/scripts/*.py /tmp/ce && cd /tmp/ce
PYTHONPATH=/path/to/overlay python3 glm_experiments_v5.py
```
