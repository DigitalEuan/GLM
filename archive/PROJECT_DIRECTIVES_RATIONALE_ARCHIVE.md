# Project directives — the rationale, as it was written

*A record, not the state now.* The standing rules are
[`../PROJECT_DIRECTIVES.md`](../PROJECT_DIRECTIVES.md), which states each rule,
names the instrument that enforces it, and points here. This file keeps the
long-form argument each rule was written with — what it cost to learn, and the
examples that were current when it was learned. Figures in it are frozen at the
round they were measured in and are not reconciled: the corpus of 902 Lean
declarations named below, for instance, is now several times that size.

---

## D1 — Save progress to the documents during the session

**The rule.** Write the finding into the document *when it is measured*, not
when the work is finished. A session can end at any moment — a timeout, a lost
workspace, a full context — and whatever is only in a scratch buffer or a
half-finished thought is lost completely, while whatever reached
`STATUS.md`, `MASTER_PLAN.md`, a study document or a README survives and the
next session starts from it instead of from rediscovery.

**In practice.**

1. When a module starts working, add its row to the relevant README *then*.
2. When a number is measured, put it in the study document *then*, with the
   command that recomputes it.
3. Commit after each closed piece of work, not once per session. A commit is
   cheap; a lost afternoon is not.
4. `STATUS.md` §"what is not done" is edited *before* starting the next thing,
   so that an interrupted session leaves an accurate map rather than a stale
   one.
5. Leave the tree buildable and the suite green at every commit, so an
   interrupted session hands over something that runs.
6. Sign the run off as it happens. `python -m glm_universal.signoff --run-everything`
   writes a signature into `overlay/.glm_signoff.json` after *each* unit, not
   at the end, so an interrupted session keeps the checks it has already
   earned and the next one starts by re-running only what it changed.

**Why it is a directive and not advice.** Three of this project's rounds ended
with code that worked and documents that did not know about it — the
error-feedback loop that no report reached, the study-catalogue work that
`MASTER_PLAN.md` stopped short of, the higher-lattice modules whose study
document had not been written. Each cost the following session an audit before
it could do anything new. The work was not lost, but the account of it was, and
the account is most of the value.

---

## D2 — Prefer the raw computation to fighting for a shortcut

**The rule.** When a computation is merely long, run it. Reach for a shortcut
only when the shortcut is *cheaper to build and run than the computation it
avoids*, and record what it cost either way.

**Why.** Engineering around a slow computation routinely costs more —- in
thinking, in code, in the bugs the cleverness introduces — than the computation
would have cost in wall-clock time on a machine that is not otherwise busy.
Worse, the shortcut usually throws away the by-product: the shape of the
computational work itself is often the finding. This project's most useful
numbers came from doing the whole thing: 196,560 minimal vectors enumerated
rather than sampled, all 4,096 Golay cosets walked, every one of the 902 Lean
declarations decoded to a lattice point at a tenth of a second each.

**The test, applied before optimising.**

* How long does the direct computation take? *Measure it; do not estimate it.*
* How long would the shortcut take to build, and how much does it save per run,
  and how many runs will there be?
* Does the direct computation produce something the shortcut destroys — a
  census, a distribution, a counterexample?

If the answers do not clearly favour the shortcut, run the computation. Two
mechanisms in this repository passed that test and are therefore built: the
address book of `reasoning/lean_address.py` (one 90-second computation, cached
behind a digest, read thousands of times) and the sign-off ledger of
`glm_universal.signoff` (a few milliseconds of hashing against a quarter-hour
of tests). Both are cheap to build, cheap to run, and lose nothing: the full
computation stays available and is what a release check runs.

**The corollary.** An expensive computation may be cached, but never
*silently*. A cache in this repository always carries the digest of its inputs
and reports itself stale when they change (D4).

---

## D3 — A digest addresses integrity, never meaning

**The rule.** SHA-256 answers exactly one question: *are these the same
bytes I checked before?* It must never be used to encode, address or index
anything whose *content* is supposed to matter. Anything that must mean
something is encoded from real, recoverable information about its subject.

**The two consequences.**

* An encoding that carries meaning must be **read back**. If you cannot
  recover the subject's properties from its code, the code does not carry
  them. `reasoning/lean_address.py` recovers all 24 feature coordinates from
  every one of the 902 addresses, and `RequestProject/GLM/Address.lean`
  (`readback_unique`) proves why that is guaranteed rather than lucky.
* An encoding that carries meaning must be **measured against a control that
  carries none**. The same module addresses every declaration a second time by
  the SHA-256 of its name, and scores both on the same statistic. The
  structural address puts a same-file declaration nearest in 333 of 902 cases;
  the digest address, 26 — against a chance rate of `12916/406351`, about 29 in
  902. That difference
  *is* the meaning, and it is the reason the digest scheme is kept in the code
  under the name `hash_control` and used for nothing else.

---

## D4 — Reuse a result only against a recorded digest

**The rule.** A previous result may be reused if and only if a digest of
*everything it depended on* is recorded and still matches. Otherwise recompute.
"It is probably still fine" is not a verification and is not permitted as one.

**What "everything it depended on" means** is computed, never declared: for a
test file, the file itself, every package module it imports transitively, every
frozen data file those modules read, **every document and Lean source those
modules name**, the test scaffolding, and the interpreter version.
`glm_universal.signoff` does that with `ast`, without importing the modules it
hashes.

The documents are not an afterthought, they are the case that makes the rule
bite. `tests/test_figures.py` exists to catch a stale count in `STATUS.md`; a
closure built from imports alone does not contain `STATUS.md`, so the ledger
would have gone on reporting that check as signed off while the document was
being rewritten — a saving bought with a false statement. A module that names
a document depends on it; a module that names a `.lean` file depends on the
whole Lean development and its build files. Writing up a finding therefore
makes exactly the units that read that write-up stale, and nothing else.

**Not only pytest.** `lake build`, the `sorry` scan, the diff of the two Lean
copies, the capability probes, the benchmark suites, the end-to-end evaluation
and the figures check are units of the same ledger, with the same rule and the
same ``--verify``; the command a unit runs is part of its digest, so changing
what a check does invalidates its signature.

**The discipline around it.**

* A failure is recorded as a failure and is never a signature.
* Changing the sign-off rules invalidates every signature (the package's own
  sources are inside every closure).
* `--verify` re-checks every signature without running a test, and says which
  files are covered and which are not.
* `--run-all` ignores the ledger entirely and is what a release check runs.

Over-hashing is preferred to under-hashing throughout: the cost of hashing too
much is a re-run, and the cost of hashing too little is a wrong answer.

---

## D5 — Study, test, implement, wire, formalise, verify

**The rule.** A study is not finished when it is written. It is finished when
every claim in it has passed through six stages, and the stage a study has
reached is *computed from the tree*, not asserted in prose.

| stage | what it means | how it is detected |
| --- | --- | --- |
| studied | a document states the claim | the document exists and names its module |
| implemented | a module computes it | the module exists and exports a report |
| wired | the runtime can be asked for it | a report subject dispatches to it |
| tested | the claim is pinned | a test file imports the module |
| formalised | the general statement is a theorem | a Lean file names it |
| verified | column 3 re-derives the figures in a fresh interpreter | `--verify-tct` returns `VERIFIED True` |

`reasoning/pipeline.py` walks the tree and reports the stage of every study;
`report pipeline` prints the table and names the first missing stage of each
incomplete row. A study that reaches "studied" and stops is a liability: it
states things nothing checks. A module that reaches "implemented" and stops is
worse — it is code nothing reaches, which is how the error-feedback loop sat
unreachable for a whole round.

**The order matters.** Write the study *against* the code as it is measured,
so the document is never ahead of the tree; wire it before testing it, so the
tests exercise the path a user takes; formalise the general statement last,
when it is clear which statement is the general one.

---

## D6 — Figures are generated

Any count quoted in any document — tests, modules, report subjects,
declarations, carriers — is produced by `python -m glm_universal.figures
--write` and checked by `tests/test_figures.py`, which also holds a list of
superseded phrases so a retired number cannot silently return. Do not type a
figure into a document by hand; add it to `figures.py` and quote what it
computes.

---

## D7 — No floats

**The rule.** The package constructs no floating-point number anywhere: `int`,
`fractions.Fraction`, and exact `F_2` arithmetic only. Comparisons that would
be a tolerance elsewhere are exact here, and quantities that would be a
logarithm elsewhere are integer bit counts. If a computation seems to need a
float, it needs a different formulation.

**The instrument.** `glm_universal.reasoning.exactness` parses every module of
the package and looks for the four ways a float enters a Python program — a
literal with a decimal point or an exponent, a call to the `float` builtin, a
float-valued clock (`time.time`, `time.monotonic`, `time.perf_counter`), and an
import of or a call into an inexact library (`statistics`, `decimal`, `numpy`,
`random`'s float generators, or any `math` function outside the exact integer
set `isqrt`, `gcd`, `lcm`, `comb`, `perm`, `factorial`, `prod`). It parses
rather than greps, so the word *float* in a docstring is not a float and
`math.isqrt` is not an inexact call. `FLOAT_SITES` declares the sites that are
warranted, and `tests/test_exactness.py` fails both when an undeclared site
appears and when a declared one goes away.

**Where it stands.** 153 of the package's 154 non-test modules contain no float
site at all. The one that does is `capabilities/probes.py`, whose
`carrier_rejects_floats` probe hands `0.5` and `2.0` to four entry points of
the substrate and requires each to raise `TypeError`: the floats are the
adversarial input, and the result of the probe is that none of them was
accepted. That probe is also the run-time half of the rule, since a static scan
can only show that no float is *written*.

**What this cost, in practice.**

1. *Timing.* Every timing layer measures with `time.monotonic_ns` and keeps
   integer nanoseconds, converting to whole milliseconds for the ledger and to
   an exact `Fraction` of seconds for a saving. Nothing is timed by
   subtracting two floats, and elapsed time is rendered for a human by integer
   division (`_seconds_text`, `_seconds`, `_percent`) rather than by `%.1f`.
2. *Division.* `a / b` is exact when either side is a `Fraction` and a float
   when both are plain `int`. `certain_float_divisions` convicts the case the
   syntax settles — both sides certainly integers — and finds none: the exact
   quotients here are all built from a `Fraction` on at least one side.
3. *Tables.* A table written as `3/4` is a float in Python. The word carriers
   of `examples/integrated_nrci.py` were written that way and are now
   `F(3, 4)`; the values are dyadic, so the carriers are unchanged bit for bit,
   which was checked before and after.

---

## D8 — The Lean file is the specification

Where `RequestProject/GLM/*.lean` and a Python module state the same thing and
disagree, the Lean file is right and the Python is a bug. The Lean development
is deliberately stated more generally than the code it specifies — for an
arbitrary code with the right weights, an arbitrary quantiser with a covering
bound — so that the Python may supply the particular instance and inherit the
theorem.

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

**Why.** The whole claim of this project is that the correspondences it reports
are properties of the substrate **and** of the machinery used to read it. The
reading is never free and never neutral: every carrier here is a projection at
a stated resolution, so a correspondence is always a joint fact about what the
substrate holds and what the reader can see of it. That is why the reader is
declared rather than hidden — the inventories below are the reader's parts
list, and a result that a declared operation was load-bearing for is a result
about that pairing and is stated as one.

Each of these four operations is a way of smuggling structure in from outside:
a digest manufactures an address that has nothing to do with the thing
addressed; a lossy XOR collapses distinct inputs and makes an agreement out of
the collapse; a float invents agreement in the last bits; an arbitrary function
or constant fits the answer. A result that depended on one of them is measuring
the reader as much as the read — which is not a reason to suppress it, and is
every reason to say which parts of the reader it depended on, so that the cost
of the reading can be subtracted from the finding. That is D11.

**The three inventories.** `warranted_operations_report` runs all three and
holds only if all three do.

| operation | inventory | what it currently says |
| --- | --- | --- |
| float | `exactness.FLOAT_SITES` | 1 declared module, 1 found; the rejection probe |
| digest | `exactness.DIGEST_SITES` | 3 declared modules, 3 found; all integrity (D3) |
| XOR | `combiner.XOR_SITES` | 31 modules, 117 uses, each classified by role |

Every digest site is an integrity use, as D3 requires: `integrity.py` itself,
the benchmark harness's digest of a suite's inputs, and the sign-off ledger's
signature over what a unit depended on. No module of the substrate, the
reasoning kernel, the semantics layer or the runtime hashes at all. The XOR
inventory classifies each site as the code's group law, a Hamming metric, a
digest, or *retired* — a lossy combiner kept only so that what it discarded can
still be counted.

**The fourth class, arbitrary functions and constants.** This one is not
decidable from the syntax, so it is enforced by D6 instead: every figure a
document quotes is produced by the code that reports it, so a constant that was
fitted rather than computed has nowhere to hide — there is no generator that
would reproduce it. Where a quantity genuinely is a choice (a scale, a
resolution, a cut-off), it is stated as a parameter with the sweep across it
reported, not hidden in a formula.

**When something is warranted.** Add the row, say in one sentence what the
operation buys and what it would cost to do without it, and name the exact
computation it stands beside. A site that cannot be described that way is not
warranted; retire it, and leave the retired row in place with an explanation,
which is what happened to the two XOR sites that no longer XOR and to the
lossy `bundle_f2` that `bundle_rational` replaced.


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

**In practice.**

1. Every current-state document opens with a tier-0 block: the question, the
   verdict, the one figure that decides it, and the function that recomputes
   that figure. Nothing below a tier 0 may contradict it.
2. A study's measured table is a generated block, not a typed one. When the
   sources it was taken from move, the block reports staleness and one command
   re-takes the measurement.
3. A new document is reachable from [`ENTRY.md`](../ENTRY.md) or it is archive;
   there is no third state, and the coverage claim is tested rather than
   asserted.
4. Run the check before committing:

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.corpus --check
```

**Why.** A document that quotes a number is a cache of that number, and a cache
with no digest goes stale silently. This is D6 applied to the prose itself, and
the part of it that is a theorem — the soundness of the tiered read, the
archive partition, the freshness rule and certified absence — is
`RequestProject/GLM/Corpus.lean`.

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

**Why.** This repository exists to develop the GLM, so a round is worth
running when it either finds a solution or marks a boundary; a round dropped
because one step would need a disallowed operation marks nothing. And the
declaration is not bookkeeping — it is the measurement this project wants
most. Each of these operations destroys information in a stated way (D9's
inventory records how much: XOR is uniformly `2²⁴`-to-one at 24 bits, a digest
carries none of the addressed thing, a truncation discards a stated tail),
so a site where one was unavoidable is a place where the **cost** of reading
the substrate can be priced. A path with a declared cost can be compared with
another path, and the cheaper one preferred; a path with no declared cost
cannot be compared with anything.

**In practice.**

1. Reach for the exact form first: `int` and `Fraction`, enumeration rather
   than sampling, a computation rather than a table, the code's group law
   rather than a bare XOR (D7, D2).
2. If a step will not go without a disallowed operation, run it, and add the
   site to `exactness.FLOAT_SITES`, `exactness.DIGEST_SITES` or
   `combiner.XOR_SITES` with its role, in the same commit.
3. Say in the study, in one sentence, what the operation bought and what it
   destroyed — the pigeonhole factor, the bits dropped, the tail truncated.
4. Report the finding twice where the difference can be computed: with the
   operation, and with the exact path where an exact path exists at reduced
   scope. The gap between the two is the price of the reading.
5. A control that *must* use the operation — the digest control that D3
   requires beside every correspondence — is a declared site like any other,
   and is the clearest case of the rule: the experiment needs it precisely
   because the operation carries no meaning.

**Where it stands.** The declared sites are D9's three inventories, and the
suite fails both when an undeclared site appears and when a declared one
silently goes away. The current reading is one float module (the probe that
hands floats to the substrate and requires them to be refused), three digest
modules (all integrity), and 31 modules of XOR, each classified by role, two
of them retired and kept only so that what they discarded can still be
counted.

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

**Why.** Refinement is exactly the condition under which an operation defined
at one layer remains a function of what the layer above it sees. Where it
fails, an answer computed above cannot be pushed down to a statement below, and
an escalation ladder stops being well defined — "the least rung that resolves"
presupposes that climbing never loses what the climb was for. The rule has
already earned itself: the first run of this check at scale found a real design
flaw in the shipped layer code, the substrate → integer step, which was not a
refinement on real carriers. It was reported rather than silently patched, and
the shipped integer reading now carries the substrate's bits alongside the
exponents because of it.

**A conflation is not a cumulativity failure, and the remedies differ.** Every
rung below the finest conflates something; that is what a coarse reading *is*,
and the check reports conflations beside the edges rather than as defects. The
distinction matters because the two are repaired differently: a cumulativity
failure is a constraint on how the higher rung is **constructed**, whereas a
conflation is repaired only by a **joint** reading with a rung that sees
something else. The `A_1^24` / `A_2^12` pair is the second kind — the exact
rational reading conflates it because neither type emits a stray, and no
refinement of that reading separates them. Cumulativity stops a new layer
re-inflicting a loss; it does not repair one.

**In practice.**

1. Register the family in `glm_universal.reasoning.cumulativity` with its
   rungs, its probe set, its edges and its non-edges — before running the
   check.
2. Run it: `python3 -m glm_universal.tools cumulativity`. A defect is a
   violated edge or an unwitnessed non-edge, and either one blocks shipping.
3. Where a family is rejected, keep it registered with `shipped=False` and its
   witness, so what it would have cost stays on the record.
4. State the theorem-shaped version in Lean where the property is general
   rather than probe-set-sized: `RequestProject/GLM/CumulativityRule.lean`.

**Where it stands.** Three families are registered, two of them shipped; seven
declared refinement edges hold, two declared non-edges are witnessed, and no
shipped family carries a defect. The round is written up in
[`studies/CUMULATIVITY_STUDY.md`](../studies/CUMULATIVITY_STUDY.md).

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

**Why.** Because the failure mode is severe and quiet. Re-reading a negative at
layer after layer until one of them passes is an unbounded multiple-comparison
search, and the pass then means considerably less than the original negative
did. The deep-hole escalation round survived that objection only because its
ladder of layer × budget cells was declared before it was climbed, its
extension rung was labelled as an extension everywhere it appears, and its
multiplicity correction was widened to pay for the extra cells. Declaration is
what separates escalation from shopping. The converse also matters: where a
stall is caused by absence of signal rather than by loss in the reading, no
rung resolves it, and a declared ladder makes the apparatus say so instead of
climbing indefinitely.

**Escalation must not convert a principled refusal.** Some refusals are correct
at every layer — a question that is ill formed, one that is underdetermined,
one whose relation is grounded in no register. These are classified as
non-escalatable *before* the ladder is climbed. Without that rule the loop
grinds to the top of the tower on every such question and the verdict "refused
at the top of the declared tower" stops meaning anything.

**In practice.**

1. Declare the ladder — rungs, costs, and which query kinds get which ladder —
   in `glm_universal.runtime.escalation_loop`, and the probe set in the study,
   before measuring.
2. Rank candidates for re-reading by whether there is an **identifiable
   discarded quantity** at the coarse reading, not by how disappointing the
   original result was. Where nothing was discarded, escalation has nothing to
   recover.
3. Report the cost. An answer reached at the third rung is reported as costing
   what three rungs cost, so accuracy cannot be bought with unbounded work.
4. Keep the original negative in the document, in its own section, unedited.

**Where it stands.** The loop is wired into the session and measured over the
whole evaluation set: no answer moves, no principled refusal is converted, and
four declared probes resolve above the first rung. See
[`studies/QUERY_ESCALATION_STUDY.md`](../studies/QUERY_ESCALATION_STUDY.md), and
[`studies/DEEP_HOLE_FAILURE_STUDY.md`](../studies/DEEP_HOLE_FAILURE_STUDY.md) for
a round run under this rule with **no** search on the layer axis at all.
Practice clause 2 is kept as a register rather than as an intention:
`glm_universal.reasoning.review_sweep` ranks every stalled result the
repository carries by whether the coarse reading discarded anything
identifiable, and `report review sweep` prints it. It is written before the
next re-reading, which is the only time it can constrain one; see
[`studies/REVIEW_SWEEP_STUDY.md`](../studies/REVIEW_SWEEP_STUDY.md).

---

## D14 — Not yet relied on means the sandbox, with a computed promotion checklist

**The rule.** Work that is worth running and not yet worth relying on goes in
`glm_universal/sandbox/`, and nothing the system computes with may import from
there. Each sandbox module carries a **promotion checklist** whose lines are
measured on every call rather than asserted in prose, and it leaves the sandbox
when every line is true — not when it looks promising.

**Why.** The alternative is a module that is half-trusted, which in practice
means trusted by whatever calls it and disclaimed in the document nobody reads
at the point of use. Isolation makes the disclaimer structural: while a module
is in the sandbox, deleting the directory cannot change a single answer the
system gives, and that is a fact a test can check rather than a promise. The
computed checklist then makes promotion a decision against a standard declared
in advance, instead of a judgement made after seeing an encouraging number.

**In practice.**

1. Put the module in `glm_universal/sandbox/`, with a `promotion_checklist`
   function returning one boolean per condition and their conjunction.
2. Include at least one gate measured against the **whole** evaluation set, not
   only against a task set the module chose for itself. A set a module picked
   for itself can be an existence proof and never a gate.
3. Test that no shipped module imports the sandbox. The documentation layer may
   import it lazily in order to report on it; that exception is declared and
   checked.
4. Write the round up like any other: the checklist as it stands, and the false
   line named as the work remaining.

**Where it stands.** One occupant, the reverse-call planner. Its safety gate
holds and its utility gate does not, so it is not promoted; see
[`studies/REVERSE_CALL_PLANNER_STUDY.md`](../studies/REVERSE_CALL_PLANNER_STUDY.md).

## D15 — A round names which faculty it moved

**The rule.** Every round states, in its record, which of the three faculties
it moved — **derivation**, **geometric addressing** or **refusal** — and
assigns each measured result of the round to exactly one of them. A round that
moved none says so in those words: "this round cleaned up".

**Why.** The standing target of this project is reasoning improvement, and the
easiest way to lose it is to keep measuring things that are real and are not
the target. Register lookup by exact name is not addressing; addressing is not
derivation; a higher hit rate at a threshold nobody declared is not either. The
three are mechanically distinguishable — `glm_universal.reasoning.blockers`
classifies a result by what actually produced the answer, not by how it reads —
so the assignment is a computation rather than a matter of taste, and writing
it down is what keeps a run of rounds from drifting into decoration.

**In practice.**

1. Before the round closes, take the ledger of §1 of
   [`studies/BLOCKERS_STUDY.md`](../studies/BLOCKERS_STUDY.md) and add this
   round's measured results to it, each with the mechanism that produced it.
2. In the round record, name the faculty moved and the size of the movement,
   with the control it was measured against.
3. Where a round bought an improvement by giving something up — a guard that
   removes wrong answers by refusing more — count both sides. A refusal that is
   not costed is not a result.
4. Where the honest answer is "none of the three", write that. It is a true
   record of a maintenance round, and it is what makes the next round pick a
   candidate from §3.4 of [`STATUS.md`](../STATUS.md) rather than drift.

**Where it stands.** The blockers ledger assigns every result of the last
measuring round: three addressed, two derived, one table. `report capabilities`
and [`CAPABILITY_ASSESSMENT.md`](../CAPABILITY_ASSESSMENT.md) are the standing
measurement the claim is checked against.

## D16 — Run the cheapest gate that could fail

**The rule.** Work against the cheapest check that could fail on what was just
changed, and let the sign-off ledger decide what to re-run. Three gates, in
[`ITERATE.md`](../ITERATE.md) §2: the document check after prose, the changed-unit
run after code or Lean, and the full release once, at the close of the round.
Never re-run a unit whose closure has not moved, and never skip one whose
closure has.

**Why.** Everything here is recomputed from the tree, which is what makes it
honest and what makes it slow. A full pass is over an hour of work, so a
session that takes one after every edit spends the round watching tests it has
already passed. The ledger exists precisely so that it does not have to: each
unit is signed against the digest of its whole closure, so "nothing changed"
is a fact rather than a hope. The rule is cheap to follow and the failure it
prevents — a round that ran out of time before it wrote its finding down — is
the most expensive one this project has.

**In practice.**

1. `signoff --plan` before running anything: it says what is stale and why.
2. Batch the edits that invalidate widely — the directives, a readme, the Lean
   tree — and pay for them once rather than per edit.
3. `signoff --run-everything` runs the stale units and the stale instruments.
   `--release` ignores the ledger and is for closing the round.
4. Keep the closure honest rather than convenient: `glm_universal.corpus.cost`
   measures what one edit makes stale, and a dependency that is too coarse is
   a defect to fix, not a cost to absorb. One line resolving a named Lean file
   to the whole development was costing 83 units of 96 on every Lean edit.

**Where it stands.** Measured in
[`studies/ITERATION_COST_STUDY.md`](../studies/ITERATION_COST_STUDY.md) §5a: an
edit to one Lean file now makes a median of 25 units stale rather than 83, and
a unit's closure is 116 files rather than 332.
