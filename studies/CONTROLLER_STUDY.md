# The loop: propose, check, refuse — and whether the substrate can steer it

**What this document is.**
[`SEARCH_LOOP_STUDY.md`](SEARCH_LOOP_STUDY.md) retrieved the archive's
procedure — filter on every observation, then rank — and proved what one pass
of it guarantees. It is a *gate*, not a controller: it decides a candidate set
in one shot. Everything else in the system answers in one shot too. What was
missing, and what the brief named, is a loop that takes a question it cannot
answer in one step, decomposes it, tries, checks, and either revises or gives
up.

This study is that loop, built on the one register where every step can be
checked exactly, and then used to ask the founding question a second time in a
sharper form:

> [`ADDRESS_RETRIEVAL_STUDY.md`](ADDRESS_RETRIEVAL_STUDY.md) showed the
> geometry does not do the *retrieving*. Can it do the *steering*?

The task: build a physical quantity out of the ten EXT10 generators, one
factor at a time. The cycle: **propose** the twenty moves, **check** the state
against the target exactly, **refuse or refine**. The experiment: run the same
loop with six different scorers, one of which is the Leech address, and count
what each one solves.

The answer, before the tables:

1. **The loop works, and everything it returns is checked by an instrument
   that did not build it.** Of the 24 reachable tasks, every plan any scorer
   returned was re-verified end to end by
   `verifier.verify_expression_pair` through the digit stack — **100 %**, under
   every scorer.
2. **It refuses in two different ways, and only one of them is a budget.**
   127 of the register's 726 quantities are refused *with a proof* — an
   invariant no move can change — without a single node being expanded. A beam
   that runs out of depth is refused too, and never dressed up as an answer.
3. **The substrate can steer.** The Leech-address scorer solves **18 of 24**
   against **8** for no guidance and **12** for a scorer that knows nothing
   about the target. The geometry is doing real work here, which is more than
   it managed in the retrieval experiment.
4. **And it steers no better than the same distance measured without the
   lattice.** The raw 24-coordinate carrier scores **17 of 24** on the same
   tasks — one behind, and with a better minimality record. Once again the
   lattice transports the information faithfully and adds nothing to it.
5. **At the register's own resolution the address stops working entirely.**
   Decoded at scale 1 instead of 9 the scorer solves **8 of 24** — *exactly*
   the no-guidance figure, proposal for proposal. This is what `Address.lean`'s
   read-back bound predicts: the covering radius is 4 and adjacent states are
   `sqrt(2)` apart, so the decoder conflates them and the signal is gone. The
   prediction was measured rather than asserted.
6. **And it costs three orders of magnitude more per node.** Scoring one state
   by address needs a lattice decode — about twenty milliseconds — against
   microseconds for counting exponents. The 1,195 decodes the task set needs
   are computed once and stored, which is the only reason the report runs in
   seconds.

The formal half is
[`RequestProject/GLM/Controller.lean`](../RequestProject/GLM/Controller.lean),
the computational half is `glm_universal.reasoning.controller`, the test that
pins them together is `overlay/glm_universal/tests/test_controller.py`
(25 tests, 181 subtests), and the report prints with

```bash
cd overlay
PYTHONPATH=. python3 GLM.py -q "report controller" --verify-tct
```

---

## 1. The task, and why it can be checked

A state is the ten integer EXT10 exponents `(L, M, T, I, H, N, J, A, S, B)`. A
move multiplies or divides by one of the ten generators — `length`, `mass`,
`time`, `current`, `temperature`, `amount`, `luminous_intensity`, `angle`,
`solid_angle`, `information` — each of which is *checked* against the register
to be the unit quantity of its axis, not assumed to be. There are twenty moves,
in a stated order, and a tie is broken by that order rather than by which
proposal arrived first.

A plan is a list of moves; the answer it stands for is an expression such as

```
energy = length * length * mass / time / time
```

and that expression is handed to `verifier.verify_expression_pair`, which turns
both sides into 24-coordinate carriers and compares them plane by plane through
the digit stack. **The loop's own arithmetic decides when to stop; a different
instrument decides whether it was right.**

---

## 2. Two refusals, and only one of them is a budget

`GLM.Controller.unreachable_of_invariant` says: if a homomorphism vanishes on
every move, it is constant along every plan, so a target where it differs is
unreachable *at any depth*. Three such invariants apply, and the controller
evaluates them before it searches:

| invariant | why no move can change it | register quantities refused |
| --- | --- | --- |
| the denominator of an exponent | a move adds `±1` to one exponent | e.g. quantities with a `1/2` power |
| the decimal scale | no move touches the scale coordinate (`scale_invariant`) | `gigahertz`, `kilometre`, `nanosecond`, `microradian` |
| the tensor rank and the P/T/C gradings | every generator is a rank-0, even scalar | `acceleration`, `electric_displacement`, `magnetization` |

**127 of the 726** register quantities are refused this way; **599** are
reachable. The refusal names the invariant and expands no nodes — it is a
proof, in the same sense as
`GLM.Retrieval.filterRadius_eq_nil_certifies_absence`.

The other refusal is the honest one. Beam search is incomplete —
`GLM.Controller.beam_can_miss` exhibits a width-one loop missing a plan that
exists — so when the beam runs out of depth the controller says *the search
failed*, not *the target is unreachable*, and never returns its closest state
as if it were the answer. The counts below are the counts of that refusal.

---

## 3. The six scorers on the same 24 tasks

Beam width 2, depth 16, tasks a stated stride through the 599 reachable
quantities. "Minimal" means the plan had exactly `‖t‖₁` moves, which
`GLM.Controller.minimal_length_eq_l1` proves is the true optimum. "Verified"
means the digit-stack verifier confirmed the finished expression.

| scorer | solved | minimal | verified | mean proposals scored |
| --- | --- | --- | --- | --- |
| **exponent** — the exact remaining-move count | **24 / 24** | 24 | 24 | 89.2 |
| **address** — Leech address at scale 9 | **18 / 24** | 17 | 18 | 209.2 |
| *carrier* — the same distance, undecoded (ablation) | 17 / 24 | 17 | 17 | 205.8 |
| *address_native* — Leech address at scale 1 | 8 / 24 | 8 | 8 | 417.5 |
| *none* — no guidance at all | 8 / 24 | 8 | 8 | 417.5 |
| *random* — a scorer blind to the target | 12 / 24 | 12 | 12 | 315.8 |

Four readings.

**The exact scorer is the ceiling, and it is a theorem, not a tuning.**
`exists_descent` says there is always a move that reduces `‖state − target‖₁`
by one, so a loop driven by that number never backtracks and always returns a
minimal plan. It solves everything. Everything else is measured against it.

**The substrate steers.** 18 against 8 for no guidance is not a marginal
effect, and 18 against 12 for a scorer that reads the state but not the target
rules out the possibility that the gain is just tie-breaking noise. The
geometry carries enough of the dimensional structure to guide a search through
it. That is a real functional role, and it is the first one the lattice has
earned in a *reasoning* loop rather than in coding or addressing.

**It steers no better than its own coordinates do.** The carrier heuristic is
the same distance with the decoder removed: 17 solved, 17 of them minimal
against the address's 17 of 18. The lattice neither adds nor destroys the
guidance at scale 9 — which is exactly what `Address.lean`'s lossless read-back
says it should do, and exactly the pattern
[`ADDRESS_RETRIEVAL_STUDY.md`](ADDRESS_RETRIEVAL_STUDY.md) found for retrieval.
Two independent experiments, the same conclusion: **the substrate is a
faithful carrier of whatever structure it is given and not a source of extra
structure.**

**And the resolution is not free.** At scale 1 the address scorer is
*identical* to no guidance — 8 solved, 417.5 proposals, the same targets — not
approximately, exactly. The covering radius is 4, adjacent states are `sqrt(2)`
apart, and the decoder therefore sends whole neighbourhoods of states to one
point. `Address.lean` requires a scale above `2ρ = 8` for the encoding to be
lossless; the loop is a direct measurement of what happens below it.

---

## 4. What it costs

| operation | per state |
| --- | --- |
| exponent distance | a few microseconds |
| carrier distance | a few microseconds |
| Leech address | about 20 ms — a lattice decode |

The stated task set needs **1,195** distinct decodes across the two scales.
They are computed once and stored in
`reasoning/_data/controller_addresses.json`, keyed by the task set, the beam
width and the depth, so the stored table is `stale` the moment any of those
changes. Rebuilding it takes about two minutes; reading it takes milliseconds,
and the report records how many decodes it had to perform itself — **zero**,
when the table is fresh.

This is worth stating plainly because it bears on the founding question. Even
where the geometry *does* guide the search, it guides it at about a thousand
times the cost of the arithmetic that guides it better.

---

## 5. What would falsify this

* **The steering result.** If the random control ever reaches the address's
  solve count, the gain is tie-breaking and not guidance;
  `test_controller.py` fails when it does.
* **The ablation.** If the address were to pull clearly ahead of the
  undecoded carrier on a larger task set, the claim that the lattice adds
  nothing would be wrong. They currently differ by one task out of 24, which is
  within the noise of a set this size — the honest statement is *no measured
  difference*, not *proved identical*.
* **The collapse.** If the native-resolution scorer stopped matching
  no-guidance exactly, either the covering radius or the carrier spacing is not
  what `Address.lean` assumes.
* **The soundness.** One plan the loop returns and the digit-stack verifier
  rejects would break the central claim that the answer is checked rather than
  asserted. The test re-runs that check on every plan under every scorer.

---

## 6. What this says about the founding question

Taken with [`ADDRESS_RETRIEVAL_STUDY.md`](ADDRESS_RETRIEVAL_STUDY.md), this
study says something narrower and firmer than either could alone.

The substrate can carry a reasoning loop: it supplies a metric in which
*getting closer* means something, and a loop steered by that metric solves
twice as many multi-step derivations as one steered by nothing. It also supplies
the refusals — the invariant that proves a target unreachable is a fact about
the algebra of the carriers, and it is what lets the loop give up honestly
instead of guessing.

What it does not supply is any advantage over reading the same coordinates
without it. In both experiments the lattice matched its own undecoded carrier
and lost to the exact quantity underneath. The fair summary of the substrate
after both is: **an exact, deterministic, provably lossless carrier and
addressing layer, whose contribution to reasoning is faithfulness and refusal
rather than insight.** That is a smaller claim than the framing has sometimes
suggested, and it is one the measurements support.
