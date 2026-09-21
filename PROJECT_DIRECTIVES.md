# Project directives


## Tier 0 — the coarse read

**Question.** What standing rules does work in this repository follow, and what enforces each?

**Verdict.** A digest addresses integrity, never meaning.

**Deciding figure.** 201 of the package's 203 non-test modules contain no float site at all.

**Recomputed by.** `glm_universal.reasoning.directives.directives_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

## Positioning — read this before starting a round

*This is the only place the positioning is stated. Every other document points
here rather than repeating it, so there is one sentence to change if it ever
changes.*

### The claim

**We are not claiming that the lattice generates the universe.** The claim is
narrower, and it is testable: there is an *exact* substrate — the Golay code,
the Leech lattice, and the arithmetic on them, integer and `Fraction` exact
throughout (D7) — and reality maps onto it with unusual fidelity.

"Unusual fidelity" is a measurement, not an adjective. Wherever this repository
asserts it, there is a control beside it — a digest, a reshuffle, a chance
baseline — and the assertion stands only by the margin over that control. Where
the margin is not there, the study says so; nine of the retrieved results are
negative results, kept because a refuted claim is a result.

### What the GLM is

The **Geometric Language Machine (GLM)** is the experimental implementation of
that mapping. It exists to answer four questions, and each one is a question
about what the machine can be made to do rather than about what the substrate
is:

1. Can language, mathematics and program text be mapped onto the Leech lattice,
   using the Golay code and the other systems developed here?
2. Can the GLM *reason* with the information that mapping gives it?
3. Can it be generative — work with what it holds, rather than only recall it?
4. Can it solve problems and produce results that are real, accurate and
   checkable?

Every one of those is answerable by running something.
[`CAPABILITY_ASSESSMENT.md`](CAPABILITY_ASSESSMENT.md) is where the current
answers live, and each is a probe that either holds or breaks.

### Layers, and why an absence is not a refutation

Some of what the substrate holds is hidden by the layer it is read at. Every
carrier here is a **projection at a stated resolution** — the 24-bit word, the
syndrome, the MOG cell, the Leech point, the shell — so a correspondence that
is invisible at one layer can be exact one layer up.

The working consequence: **check a claim from several layers and resolutions
before calling it absent.** An absence at one resolution is a statement about
that resolution, not about the substrate.

Two studies measure exactly what each step down discards, so that this is a
measurement rather than an excuse:

* [`studies/COMBINER_STUDY.md`](studies/COMBINER_STUDY.md) — what XOR loses
  (uniformly `2²⁴`-to-one, which is the pigeonhole bound for *any* combiner of
  that output width), and what a wider output buys back.
* [`studies/INFORMATION_LOSS_STUDY.md`](studies/INFORMATION_LOSS_STUDY.md) —
  what each layer of the stack cannot see, listed pair by pair rather than
  asserted.

### What follows from this in practice

* A result is stated at the layer it was measured at, and the layer is named.
* A negative result is recorded, not discarded; it is the cheapest thing this
  project produces and the most easily lost.
* No claim of correspondence is made without the control it was measured
  against.
* The substrate stays exact: integers and `Fraction`, no floats (D7).

## The target — what a round is for

The standing target is **reasoning improvement**, and it is deliberately
narrow: a round moves the target when it makes the system *derive*, *address*
or *refuse* better than it did, measured under a perturbation declared before
the measurement.

* **Derive** — produce an answer no register holds. This is the scarce one.
* **Address** — recover an answer from the geometry when the query is not the
  stored key. This is where most of the measured gain has been, and calling it
  reasoning without the qualifier would be overclaiming.
* **Refuse** — withhold an answer that would have been wrong, at a counted
  cost in answers given up.

[`studies/BLOCKERS_STUDY.md`](studies/BLOCKERS_STUDY.md) §1 separates the three
mechanically — table lookup, geometric addressing, derivation — and assigns
every measured result of a round to exactly one of them; D15 makes that
assignment a condition of closing the round. A round that moves none of the
three is a round that cleaned up, and its record says so in those words.

**Price an instrument before building it.** A round is allowed to spend
itself measuring what a capability *would* be worth, and that is often the
better spend: [`studies/PROBE_ORACLE_STUDY.md`](studies/PROBE_ORACLE_STUDY.md)
priced two of them against each other in an afternoon — a parser at four
questions of twenty, a surface onto what the registers already hold at ten —
and in doing so showed that the expensive one was the smaller prize. When a
priced instrument is `table` rather than `derive` or `address`, the round that
builds it says so under this heading rather than claiming the target.

## How to work in this repository

**The operating manual is [`ITERATE.md`](ITERATE.md)**: how to pick the work
up, the three gates and which to run when, where a finding is written down,
and what to do when a check fails. Read it once; it is short, and it is what
keeps a round from re-running the whole tree.

**Commit and push after each completed step, not once at the end.** A step is
anything that leaves the tree in a working state — one document reconciled,
one test added, one lemma proved. Never leave a session's work sitting
uncommitted: a commit is cheap, and an interrupted session that has been
committing as it goes hands over something that runs. This is the practical
face of D1 below, and the same block heads [`STATUS.md`](STATUS.md).

---

**Standing rules for anyone — person or machine — working on this repository.**

These are not style preferences. Each one exists because ignoring it has cost
this project time or fidelity, and each one names the **instrument** that
enforces it, so that a directive can be checked rather than remembered.
`glm_universal/reasoning/directives.py` parses this file, and
`report directives` prints the table with each instrument's current verdict;
`tests/test_project_directives.py` fails if a directive loses its instrument or
if this file and the module disagree.

| id | rule, in one line | instrument |
| --- | --- | --- |
| D1 | Save progress to the documents *during* the session, not at the end. | `report directives`, the change log in `overlay/README.md` |
| D2 | Prefer the raw computation to fighting for a shortcut. | `report pipeline`, `glm_universal.signoff` |
| D3 | A digest addresses integrity, never meaning. | `report lean`, `glm_universal.reasoning.lean_address` |
| D4 | Reuse a result only against a recorded digest of everything it depended on. | `glm_universal.signoff` |
| D5 | A study is not finished until it is implemented, wired, tested, formalised and verified. | `report pipeline` |
| D6 | Every figure a document quotes is generated by the code that reports it. | `glm_universal.figures`, `tests/test_figures.py` |
| D7 | No floats. Exact integers and `Fraction` everywhere. | `glm_universal.reasoning.exactness`, `tests/test_exactness.py` |
| D8 | Where a Lean file and a Python module disagree, the Lean file is the specification. | `glm_lean/RequestProject/GLM/README.md` |
| D9 | An operation that is not the substrate's own is used only where it is warranted, and every such site is declared. | `glm_universal.reasoning.exactness`, `glm_universal.reasoning.combiner`, `tests/test_exactness.py` |
| D10 | A document is data: classified by rule, generated where it can be, addressed, and checked. | `glm_universal.corpus`, `tests/test_corpus.py` |
| D11 | A forbidden operation never cancels an experiment: run it, declare the site, and carry the cost. | `glm_universal.reasoning.exactness`, `glm_universal.reasoning.combiner`, `tests/test_exactness.py` |
| D12 | A layer ships with its refinement check: declared edges verified, declared non-edges witnessed. | `glm_universal.reasoning.cumulativity`, `tests/test_cumulativity.py` |
| D13 | An escalated re-reading is declared before it is taken, and it is costed. | `glm_universal.runtime.escalation_loop`, `glm_universal.reasoning.query_escalation`, `glm_universal.reasoning.review_sweep`, `tests/test_query_escalation.py`, `tests/test_review_sweep.py` |
| D14 | Something not yet relied on lives in the sandbox, with a computed promotion checklist. | `glm_universal.sandbox.planner`, `tests/test_sandbox_planner.py` |
| D15 | A round says which of derivation, addressing and refusal it moved, or that it moved none. | `glm_universal.reasoning.blockers`, `CAPABILITY_ASSESSMENT.md`, `report capabilities` |
| D16 | Run the cheapest gate that could fail; sign off only what moved. | `glm_universal.signoff`, `glm_universal.corpus.cost`, `ITERATE.md` |

---

## The round, end to end

The whole loop, in one place. [`ITERATE.md`](ITERATE.md) is the long form of
it; nothing below replaces reading that once.

1. **Orient.** This section and the target above; [`STATUS.md`](STATUS.md) §1
   for where the work stands and §3.4 for the candidates, sharpest first;
   [`DIGEST.md`](DIGEST.md) to find the two or three studies that bear on the
   one you take. Confirm the tree is where the last round left it with
   `corpus --check` and `signoff --verify`.
2. **Take a candidate from §3.4, or say in the record why not.** A round aimed
   at nothing on that list is a round that will be hard to judge against the
   target.
3. **Declare before you measure.** The ladder, the controls, the pass mark and
   the perturbation are written down *before* the measurement, not after
   (D13). A result that was not declared in advance is evidence, not a finding.
4. **Work against the cheapest gate that could fail** (D16), and make the edits
   in one batch before running it rather than gate-checking between them.
5. **Record it where it belongs** (D1, D15): the finding and its controls in a
   `studies/*_STUDY.md`; what the system *is* now in [`STATUS.md`](STATUS.md)
   §2; what is open in §3; the round itself as a phase in
   [`MASTER_PLAN.md`](MASTER_PLAN.md); anything proved rather than measured in
   `RequestProject/GLM/`. Name which faculty moved, or that none did.
6. **Close** with `corpus --refresh`, then `corpus --check`, then
   `signoff --release`, in that order, and commit.

**What a round is judged on**, again, because it is the only thing that
matters: did the system *derive*, *address* or *refuse* better than it did?
Everything else — a faster gate, a tidier document, a cache that stops going
stale — is maintenance, and maintenance is worth doing precisely because it
buys the time the next round spends on the target. It is never reported as
progress against it.

## How the rest of this file is arranged

Each rule below states itself in one paragraph and names the instrument that
enforces it. The argument it was written with — what ignoring it cost, and the
examples that were current when it was learned — is kept in
[`archive/PROJECT_DIRECTIVES_RATIONALE_ARCHIVE.md`](archive/PROJECT_DIRECTIVES_RATIONALE_ARCHIVE.md),
which is a record of a round rather than a statement of the rules: its figures
are frozen where they were measured and are not reconciled.

---

## D1 — Save progress to the documents during the session

**The rule.** Write the finding into the document *when it is measured*, not
when the work is finished. A session can end at any moment — a timeout, a lost
workspace, a full context — and whatever is only in a scratch buffer or a
half-finished thought is lost completely, while whatever reached
`STATUS.md`, `MASTER_PLAN.md`, a study document or a README survives and the
next session starts from it instead of from rediscovery.

**Checked by** `report directives`, the change log in `overlay/README.md`. The argument this rule was written with —
what it cost to learn, and the examples current at the time — is `D1`
in [`archive/PROJECT_DIRECTIVES_RATIONALE_ARCHIVE.md`](archive/PROJECT_DIRECTIVES_RATIONALE_ARCHIVE.md).

---

## D2 — Prefer the raw computation to fighting for a shortcut

**The rule.** When a computation is merely long, run it. Reach for a shortcut
only when the shortcut is *cheaper to build and run than the computation it
avoids*, and record what it cost either way.

**Checked by** `report pipeline`, `glm_universal.signoff`. The argument this rule was written with —
what it cost to learn, and the examples current at the time — is `D2`
in [`archive/PROJECT_DIRECTIVES_RATIONALE_ARCHIVE.md`](archive/PROJECT_DIRECTIVES_RATIONALE_ARCHIVE.md).

---

## D3 — A digest addresses integrity, never meaning

**The rule.** SHA-256 answers exactly one question: *are these the same
bytes I checked before?* It must never be used to encode, address or index
anything whose *content* is supposed to matter. Anything that must mean
something is encoded from real, recoverable information about its subject.

**Checked by** `report lean`, `glm_universal.reasoning.lean_address`. The argument this rule was written with —
what it cost to learn, and the examples current at the time — is `D3`
in [`archive/PROJECT_DIRECTIVES_RATIONALE_ARCHIVE.md`](archive/PROJECT_DIRECTIVES_RATIONALE_ARCHIVE.md).

---

## D4 — Reuse a result only against a recorded digest

**The rule.** A previous result may be reused if and only if a digest of
*everything it depended on* is recorded and still matches. Otherwise recompute.
"It is probably still fine" is not a verification and is not permitted as one.

**Checked by** `glm_universal.signoff`. The argument this rule was written with —
what it cost to learn, and the examples current at the time — is `D4`
in [`archive/PROJECT_DIRECTIVES_RATIONALE_ARCHIVE.md`](archive/PROJECT_DIRECTIVES_RATIONALE_ARCHIVE.md).

---

## D5 — Study, test, implement, wire, formalise, verify

**The rule.** A study is not finished when it is written. It is finished when
every claim in it has passed through six stages, and the stage a study has
reached is *computed from the tree*, not asserted in prose.

**Checked by** `report pipeline`. The argument this rule was written with —
what it cost to learn, and the examples current at the time — is `D5`
in [`archive/PROJECT_DIRECTIVES_RATIONALE_ARCHIVE.md`](archive/PROJECT_DIRECTIVES_RATIONALE_ARCHIVE.md).

---

## D6 — Figures are generated

Any count quoted in any document — tests, modules, report subjects,
declarations, carriers — is produced by `python -m glm_universal.figures
--write` and checked by `tests/test_figures.py`, which also holds a list of
superseded phrases so a retired number cannot silently return. Do not type a
figure into a document by hand; add it to `figures.py` and quote what it
computes.

**Checked by** `glm_universal.figures`, `tests/test_figures.py`. The argument this rule was written with —
what it cost to learn, and the examples current at the time — is `D6`
in [`archive/PROJECT_DIRECTIVES_RATIONALE_ARCHIVE.md`](archive/PROJECT_DIRECTIVES_RATIONALE_ARCHIVE.md).

---

## D7 — No floats

**The rule.** The package constructs no floating-point number anywhere: `int`,
`fractions.Fraction`, and exact `F_2` arithmetic only. Comparisons that would
be a tolerance elsewhere are exact here, and quantities that would be a
logarithm elsewhere are integer bit counts. If a computation seems to need a
float, it needs a different formulation.

**Where it stands.** 201 of the package's 203 non-test modules contain no float
site at all. Two contain one. The first is `capabilities/probes.py`, whose
`carrier_rejects_floats` probe hands `0.5` and `2.0` to four entry points of
the substrate and requires each to raise `TypeError`: the floats are the
adversarial input, and the result of the probe is that none of them was
accepted. That probe is also the run-time half of the rule, since a static scan
can only show that no float is *written*. The second is
`reasoning/now_float_control.py`, which runs the delta-sigma loop in floating
point beside the exact one in order to settle a supplied study's claim that a
float substrate cannot hold the accumulator: the float is the thing under test,
nothing the system computes with imports the module, and
[`studies/NOW_RECEIPT_STUDY.md`](studies/NOW_RECEIPT_STUDY.md) §5 is what it
found.

**Checked by** `glm_universal.reasoning.exactness`, `tests/test_exactness.py`. The argument this rule was written with —
what it cost to learn, and the examples current at the time — is `D7`
in [`archive/PROJECT_DIRECTIVES_RATIONALE_ARCHIVE.md`](archive/PROJECT_DIRECTIVES_RATIONALE_ARCHIVE.md).

---

## D8 — The Lean file is the specification

Where `RequestProject/GLM/*.lean` and a Python module state the same thing and
disagree, the Lean file is right and the Python is a bug. The Lean development
is deliberately stated more generally than the code it specifies — for an
arbitrary code with the right weights, an arbitrary quantiser with a covering
bound — so that the Python may supply the particular instance and inherit the
theorem.

**Checked by** `glm_lean/RequestProject/GLM/README.md`. The argument this rule was written with —
what it cost to learn, and the examples current at the time — is `D8`
in [`archive/PROJECT_DIRECTIVES_RATIONALE_ARCHIVE.md`](archive/PROJECT_DIRECTIVES_RATIONALE_ARCHIVE.md).

---

## D9 — Only warranted operations, and an inventory of each

**The rule.** An operation that is not the substrate's own arithmetic — a
cryptographic digest, a XOR used as anything but the code's group law, a float,
an arbitrary function or fitted constant — is used **only where it is
warranted**, and every site where it is used is **declared in an inventory that
the suite checks against the tree**. A rule of this kind is worthless as a
memory and useful only as an instrument: what stops the next module from
hashing a meaning is not that someone remembers the rule, it is that the
inventory fails.

**Checked by** `glm_universal.reasoning.exactness`, `glm_universal.reasoning.combiner`, `tests/test_exactness.py`. The argument this rule was written with —
what it cost to learn, and the examples current at the time — is `D9`
in [`archive/PROJECT_DIRECTIVES_RATIONALE_ARCHIVE.md`](archive/PROJECT_DIRECTIVES_RATIONALE_ARCHIVE.md).

---

## D10 — A document is data

**The rule.** The prose of this project is held the way the substrate holds
data, and not by memory. A document is **classified by rule** — archive
membership is decided by the path and nothing else, never by judgement; it is
**generated** wherever it can be, so `DIGEST.md` and every in-document
`<!-- generated: ... -->` block is emitted from the measurement it reports
rather than typed; it is **addressed**, so a question returns a shortlist that
is complete up to a stated radius and an empty shortlist is a proof of absence;
and it is **checked**, so drift fails a run instead of misleading a reader.

**Checked by** `glm_universal.corpus`, `tests/test_corpus.py`. The argument this rule was written with —
what it cost to learn, and the examples current at the time — is `D10`
in [`archive/PROJECT_DIRECTIVES_RATIONALE_ARCHIVE.md`](archive/PROJECT_DIRECTIVES_RATIONALE_ARCHIVE.md).

---

## D11 — A forbidden operation never cancels an experiment

**The rule.** The operations this repository avoids — a cryptographic digest
used for anything but integrity, a call to a random source, a stored table
standing in for a computation, a lossy XOR, a float, a truncation or a
rounding — are avoided **wherever it is possible to avoid them**, which is
almost everywhere. Where an experiment genuinely cannot be run without one,
the experiment is still run. It is not dropped, and the round is not
abandoned: the site is declared in the inventory of D9, the study says in
words which step needed it and what the step would have cost without it, and
the finding is reported with that dependence attached.

**Checked by** `glm_universal.reasoning.exactness`, `glm_universal.reasoning.combiner`, `tests/test_exactness.py`. The argument this rule was written with —
what it cost to learn, and the examples current at the time — is `D11`
in [`archive/PROJECT_DIRECTIVES_RATIONALE_ARCHIVE.md`](archive/PROJECT_DIRECTIVES_RATIONALE_ARCHIVE.md).

---

## D12 — A layer ships with its refinement check

**The rule.** A new layer, rung or perspective ships only if it arrives with
the machine-checked statement that it **refines** the layer below it: every
pair of carriers the lower reading separates is separated by the higher one, on
a declared probe set. A layer family also declares its **non**-edges — the
pairs of rungs where refinement is *not* claimed — and each of those must come
with a witnessing pair, because "B does not refine A" is a claim too, and an
unwitnessed claim is not a declaration but an excuse. Cumulativity is a
property, not an intention: a layer without its check does not ship.

**Checked by** `glm_universal.reasoning.cumulativity`, `tests/test_cumulativity.py`. The argument this rule was written with —
what it cost to learn, and the examples current at the time — is `D12`
in [`archive/PROJECT_DIRECTIVES_RATIONALE_ARCHIVE.md`](archive/PROJECT_DIRECTIVES_RATIONALE_ARCHIVE.md).

---

## D13 — An escalated re-reading is declared before it is taken, and it is costed

**The rule.** Re-reading a refusal, a stall or a negative result at a finer
layer is legitimate, and it is the project's most productive move. It is
legitimate **only** under three conditions, all of which precede the
measurement: the ladder of rungs is declared in advance and is finite; every
cell actually tried is counted and reported, including the ones that failed;
and the original refusal or negative stays on the record beside whatever the
escalated reading returns. An escalated answer is reported as more expensive
than a direct one, and a refusal carries the layer it was refused at.

**Checked by** `glm_universal.runtime.escalation_loop`, `glm_universal.reasoning.query_escalation`, `glm_universal.reasoning.review_sweep`, `tests/test_query_escalation.py`, `tests/test_review_sweep.py`. The argument this rule was written with —
what it cost to learn, and the examples current at the time — is `D13`
in [`archive/PROJECT_DIRECTIVES_RATIONALE_ARCHIVE.md`](archive/PROJECT_DIRECTIVES_RATIONALE_ARCHIVE.md).

---

## D14 — Not yet relied on means the sandbox, with a computed promotion checklist

**The rule.** Work that is worth running and not yet worth relying on goes in
`glm_universal/sandbox/`, and nothing the system computes with may import from
there. Each sandbox module carries a **promotion checklist** whose lines are
measured on every call rather than asserted in prose, and it leaves the sandbox
when every line is true — not when it looks promising.

**Checked by** `glm_universal.sandbox.planner`, `tests/test_sandbox_planner.py`. The argument this rule was written with —
what it cost to learn, and the examples current at the time — is `D14`
in [`archive/PROJECT_DIRECTIVES_RATIONALE_ARCHIVE.md`](archive/PROJECT_DIRECTIVES_RATIONALE_ARCHIVE.md).

---

## D15 — A round names which faculty it moved

**The rule.** Every round states, in its record, which of the three faculties
it moved — **derivation**, **geometric addressing** or **refusal** — and
assigns each measured result of the round to exactly one of them. A round that
moved none says so in those words: "this round cleaned up".

**Checked by** `glm_universal.reasoning.blockers`, `CAPABILITY_ASSESSMENT.md`, `report capabilities`. The argument this rule was written with —
what it cost to learn, and the examples current at the time — is `D15`
in [`archive/PROJECT_DIRECTIVES_RATIONALE_ARCHIVE.md`](archive/PROJECT_DIRECTIVES_RATIONALE_ARCHIVE.md).

---

## D16 — Run the cheapest gate that could fail

**The rule.** Work against the cheapest check that could fail on what was just
changed, and let the sign-off ledger decide what to re-run. Three gates, in
[`ITERATE.md`](ITERATE.md) §2: the document check after prose, the changed-unit
run after code or Lean, and the full release once, at the close of the round.
Never re-run a unit whose closure has not moved, and never skip one whose
closure has.

**Checked by** `glm_universal.signoff`, `glm_universal.corpus.cost`, `ITERATE.md`. The argument this rule was written with —
what it cost to learn, and the examples current at the time — is `D16`
in [`archive/PROJECT_DIRECTIVES_RATIONALE_ARCHIVE.md`](archive/PROJECT_DIRECTIVES_RATIONALE_ARCHIVE.md).

---
