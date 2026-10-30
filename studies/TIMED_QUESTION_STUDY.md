# Time and the question — resolving a tie by information that comes later

## Tier 0 — the coarse read

**Question.** When the GLM meets a tie it cannot separate with what it has, can it hold the tie open and let **time** resolve it — information that a later step supplies — and can it work out and **ask for exactly the information it needs**, rather than refusing or waiting for whatever happens to arrive?

**Verdict.** The intuition holds where it can be measured. Held open as a tie, a refusal becomes a question: time resolves the Golay fork when later steps report sure coordinates (all 768 forks, to the transmitted word, after 8.71 reports on average), and asking resolves it faster — the GLM's own halving questions take 2.66 on average and never more than 3, the proved minimum. Waiting can never resolve a junction, because every observation of the coordinates is constant on it (proved, and 104 of 104 measured); asking for what the coordinates do not carry resolves all 387 junction runs with 0 wrong. A single false answer is undetectable without a confirming question and always caught with one. All 9 marks met.

**Deciding figure.** 9 of 9 marks; Golay fork: waiting 768/768 resolved (mean 209/24 reports, max 13), coordinate questions mean 13/4 (max 5), set questions mean 1021/384 (max 3 = `Nat.clog 2 6`), 0 wrong in each; one false answer: 1536/1536 resolved wrong without confirmation, 1536/1536 contradicted with it; junctions: 104/104 unchanged by waiting, 387/387 resolved by asking, 0 wrong, 385 without the direct choice, mean 1280/387 questions against a `Nat.clog 2` mean of 1174/387 and a one-by-one mean of 1253/129; 6 of 6 dialogues.

**Recomputed by.** `glm_universal.reasoning.timed_question.timed_question_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. What this document is

A **pre-registration** for Phase 145, committed with its Lean file and before
the module that takes the measurement exists. §§0–6 are as they were
committed; §7 is what came out.

**The owner's intuition, as given for this round.** *Time is required for the
GLM to process some of the more complicated things. When something is
ambiguous or tied, the GLM needs information to resolve the tie — information
that comes with time, in the way that a later step can prune incorrect sets or
clarify the ambiguity. Sometimes the GLM needs to give it time to find that
information, or simply ask for exactly what it needs. At this stage of the
system's development we (the developers) provide that information; later a
user will.*

**Where the system already stands.** The GLM refuses at a tie, by design:
the complete Golay decoder at coset weight 4 finds six equidistant codewords
and does not choose; the `locate` read answers a *junction* (carriers with
equal coordinates, Phase 144) and cannot name a member, because no read of the
coordinates can (`GLM.CoordinateJunction.no_read_separates`). Phase 65's
carried fork ([`CARRIED_FORK_STUDY.md`](CARRIED_FORK_STUDY.md)) already holds
the six Golay candidates open and lets *declared stages* prune them. What no
round has done is the other half of the intuition:

1. treat a later step's information as **time** — observations that arrive
   whether or not the GLM asked — and measure what waiting costs;
2. let the GLM **compute the question** whose answer it needs, put it, take
   the answer from an **informant** (at this stage the developer; the
   interface is the one a user will later sit behind), and measure what
   asking costs against waiting and against the proved minimum;
3. say, provably, **when waiting can never help** — so that the GLM knows it
   must ask, and for what.

## 1. What is proved before any code

`RequestProject/GLM/TimedQuestion.lean` (namespace `GLM.TimedQuestion`),
committed with this document; no `sorry`, standard axioms only.

* `after_eq_filter`, `after_subset`, `after_perm`, `after_append` — a history
  of questions and answers only removes candidates, and the order in which the
  information arrives does not matter.
* `truth_mem_after`, `resolved_eq_truth`, `contradicted_not_truthful`,
  `resolved_stays` — under truthful answers the truth is never removed; a tie
  left with one candidate holds the truth; a tie left with none proves an
  answer was false (it is reported, never resolved); a resolved tie stays
  resolved under later truthful information.
* `no_time_resolves`, `no_time_resolves_card` — if every observation that can
  arrive takes one value on the tie, waiting removes nothing.
* `no_coordinate_question_resolves` — in particular, for a junction, no
  observation that is a function of the coordinates ever resolves it: the GLM
  has to ask for something the coordinates do not carry.
* `prune_ssubset_iff`, `splits_iff` — a question is worth asking exactly when
  it takes two values on the live set; then every answer removes something.
* `exists_halving`, `halveRun_eq_singleton` — a yes/no question leaving at
  most half (rounded up) always exists, and asking such questions resolves
  `n` candidates in `Nat.clog 2 n` questions, to the truth.
* `adversary`, `questions_needed`, `optimal` — no adaptive yes/no strategy
  does better: with fewer than `Nat.clog 2 n` questions some truth leaves the
  tie open. `six_needs_three`: for the six Golay candidates that is three.

## 2. The rule

### 2.1 The open tie

`reasoning/timed_question.py` holds an **open tie**: the candidates, the
live set, and a **ledger** of time steps. Each step records whether the
information was *waited for* (an observation a later step made) or *asked
for* (a question the GLM put), the question's text, the answer, the
informant, and the candidates it removed. The tie is `open` (two or more
live), `resolved` (one) or `contradicted` (none). It is never resolved by
choosing.

### 2.2 Asking

A **question** is a declared text and a function from candidates to answers.
The GLM may put only questions from a declared **vocabulary** for the kind of
tie. To choose one it takes, over the questions that split the live set
(`splits_iff`), the one whose worst answer leaves the fewest candidates
(minimax), ties broken by vocabulary order. If no question in the vocabulary
splits the live set, it says so and asks the **direct choice** — *which of
these do you mean?* — naming the live candidates; that question always
resolves, and it is counted separately.

### 2.3 The informant

An **informant** answers a question. At this stage the informant is the
developer: a *declared* informant that is told the truth and answers every
question as the truth would (and, for the control, one that answers one
question falsely). The interactive informant reads the answer from the person
at the terminal; it is the same interface a user will later answer through.

### 2.4 Waiting

A **stream** is a declared sequence of observations that arrive at later
steps whether asked for or not. Waiting applies them in arrival order.

### 2.5 Confirming

After a tie resolves, the GLM may put one **confirming** question — *is it
exactly this one?* — which costs one more step and turns a single false
answer into a contradiction instead of a wrong resolution.

## 3. The two ties, and the dialogues declared here

**The Golay fork.** The probe of Phase 65 (`carried_fork.x1_probe`): 64
codewords at stride 64, 12 weight-4 errors, 768 forks of six candidates, the
transmitted codeword always among them. Vocabularies: *coordinate questions*
— "was coordinate j received correctly?" for the 24 coordinates — and *set
questions* the GLM constructs from the live tetrads — "did the error fall
among coordinates S?", with S the union of the first half of the live
tetrads. The stream: "coordinate j was received correctly" for the 20
coordinates that were, in the declared order `(13 j + 7 i) mod 24` for fork
`i`.

**The register junctions.** All 104 junctions of the six full registers
(387 carriers, Phase 144's census), each member in turn as the truth.
Observations of the coordinates (each of the 24 coordinates, and the
junction read itself) are the stream. The vocabulary: "what is its
*attribute*?" for each declared register attribute other than the name, the
symbol and the gloss (the unit, the domain, the shape of a matrix, …), then,
for each word of four or more letters in the members' glosses, "does its
description mention '*word*'?"; the name and the symbol are not in the
vocabulary, since asking for them is asking the answer.

**Dialogues** (mark D1), through `tools timed-ask`, with the developer as
declared informant:

| id | tie | truth supplied | declared outcome |
|---|---|---|---|
| T-D1 | `locate albedo` | `physics:albedo` | resolved to `physics:albedo` in 1 question |
| T-D2 | `locate absorptance` | `physics:absorptance` | resolved to `physics:absorptance` in 1 question |
| T-D3 | `locate acoustic_power_level` | `physics:acoustic_power_level` | resolved, at most 2 questions |
| T-D4 | `locate filled_4x6` | `mathematics:filled_4x6` | resolved, at most 3 questions |
| T-D5 | `locate C` | — | no tie: the read names `chemistry:C`, nothing asked |
| T-D6 | the first probe fork | its transmitted codeword | resolved in at most 3 questions |

## 4. The marks, declared before the code

| mark | claim |
|---|---|
| **L1** | `TimedQuestion.lean` builds with the full `lake build`, no `sorry`, standard axioms only |
| **G1** | waiting on the stream resolves all 768 forks, to the transmitted codeword, 0 wrong; the most reports any fork needs is at most 17 (after 17 of the 20 reports a wrong tetrad cannot be wholly unreported); the mean lies in [7, 10.5] |
| **G2** | asking coordinate questions resolves all 768, 0 wrong; the worst fork needs exactly 5 questions (each splits off at most one candidate) |
| **G3** | asking set questions resolves all 768, 0 wrong, in at most 3 questions, and some fork needs 3 (`six_needs_three`, `optimal`): the minimum possible, and a mean at most half of G1's |
| **G4** | an informant that answers one set question falsely: without confirmation every such run resolves to a wrong candidate (the lie is undetectable); with the confirming question every such run ends contradicted, 0 resolved wrongly |
| **R1** | for all 104 junctions, waiting on the coordinate observations removes nothing (`no_coordinate_question_resolves`) |
| **R2** | asking the vocabulary resolves all 387 runs, 0 wrong; at least 90% without the direct choice |
| **R3** | the mean number of questions in R2 is at most the mean of `Nat.clog 2 n` plus 1, and below the one-by-one baseline ("is it X?" in carrier order) |
| **D1** | the six dialogues come out as declared in §3 |

## 5. What this round does not do

* It does not put the open tie into the answering path: no query kind, no
  evaluation case and no pinned answer changes. The `locate` read still
  answers a junction exactly as in Phase 144; the timed tie is opened on top
  of it, by the tool. Putting the question into `GLM.py`'s answer needs a
  frozen-path comparison and is left as a To-Do line.
* It does not decide which information a *user* will want to be asked for;
  the vocabularies are declared here, by the developer.
* It does not weigh questions by cost or answers by probability: every
  candidate counts as one, and the question chosen is the minimax one.

## 6. Files

* `glm_lean/RequestProject/GLM/TimedQuestion.lean` — §1.
* `glm_universal/reasoning/timed_question.py` — the open tie, the
  informants, the two vocabularies, the measurement.
* `glm_universal/tools.py` — `tools timed-question` (the marks) and
  `tools timed-ask` (one tie, with a declared or an interactive informant).
* `glm_universal/tests/test_timed_question.py`.

## 7. What came out

Measured by `PYTHONPATH=. python3 -m glm_universal.tools timed-question`
(about ten seconds; computed live, no cache) after §§0–6 were committed.

| mark | result | |
|---|---|---|
| **L1** | `TimedQuestion.lean` builds in the full `lake build`, no `sorry`, axioms `propext`, `Classical.choice`, `Quot.sound` | met |
| **G1** | 768/768 resolved by waiting, 0 wrong; reports max 13, mean 209/24 (8.71) | met |
| **G2** | 768/768 resolved, 0 wrong; questions max 5, mean 13/4 (3.25) | met |
| **G3** | 768/768 resolved, 0 wrong; questions max 3, min 2, mean 1021/384 (2.66) | met |
| **G4** | without confirmation 1536/1536 resolved wrong; with it 1536/1536 contradicted, 0 wrong | met |
| **R1** | 104/104 junctions unchanged by waiting on their coordinates | met |
| **R2** | 387/387 resolved, 0 wrong; 385 (99.5%) without the direct choice | met |
| **R3** | mean 1280/387 (3.31) questions; `Nat.clog 2` mean 1174/387 (3.03); one-by-one mean 1253/129 (9.71) | met |
| **D1** | 6/6 dialogues as declared | met |

### 7.1 The Golay fork: waiting against asking (G1–G3)

Waiting works. Every one of the 768 forks resolves to the codeword that was
sent, once enough later reports of correctly received coordinates have
arrived: between 5 and 13 reports (histogram 5: 64, 6: 64, 7: 128, 8: 128,
9: 160, 10: 32, 11: 96, 13: 96), 8.71 on average, close to the 8.64 a
uniformly random arrival order would give. Time is enough here — but the GLM
does not choose what arrives, so it pays for every report that removes
nothing.

Asking with the coordinate vocabulary is barely better (3.25 questions on
average) and worse in the worst case (5, taken by 320 forks): a question about
one coordinate can split off at most one candidate. Asking the question the
GLM constructs — *did the error fall among coordinates S?*, with S the union
of half the live tetrads — resolves every fork in 2 or 3 questions (262 and
506 forks), 2.66 on average. Three is the least any strategy of yes/no
questions can guarantee for six candidates (`GLM.TimedQuestion.optimal`,
`six_needs_three`): the GLM asks for exactly the information it needs.

### 7.2 One false answer (G4)

Every answer the halving strategy receives is consistent with some candidate,
so a single false answer leads silently to a wrong resolution: 1536 of 1536
runs (each fork, the false answer at the first or at the second question).
One confirming question — *is it exactly this one?* — catches every one: 1536
of 1536 end `contradicted`, none resolved wrongly
(`GLM.TimedQuestion.contradicted_not_truthful`). A resolution by an informant
therefore always states what it rests on: that the answers were true.

### 7.3 The junctions: waiting cannot help, asking can (R1–R3)

For each of the 104 junctions of the full registers, each of the 24
coordinates and the junction read itself were delivered as later
observations, truthfully, with each member in turn as the truth: no
candidate was ever removed (104/104). This is
`GLM.TimedQuestion.no_coordinate_question_resolves` measured: for a
junction, time spent on the coordinates is time wasted, and the only way on
is to ask for something the coordinates do not carry.

Asking the declared vocabulary resolves all 387 runs, 0 wrong. The first
question put was a description word in 348 runs, the unit in 29, the
matrix shape (`cols`) in 8 and the field order in 2. Only 2 runs needed the
direct choice: `chromaticity_x` and `chromaticity_y`, whose descriptions
differ only in the one-letter words *x* and *y*, below the vocabulary's
four-letter floor.

The mean, 3.31 questions, is within 0.28 of the `Nat.clog 2` mean (3.03) and
a third of the one-by-one baseline (9.71). The worst runs are in the
78-member junction of dimensionless physics quantities, where up to 22
questions are put: a description word is usually shared by few of the 78,
so the minimax word splits off only a handful. That is a limit of the
vocabulary, not of the method — the halving question exists
(`exists_halving`), but no declared question expresses it.

### 7.4 The dialogues (D1)

`tools timed-ask` with the developer as the declared informant:

| id | tie | questions put | result |
|---|---|---|---|
| T-D1 | `locate albedo` | *does its description mention 'absorbed'?* → no | `physics:albedo`, 1 question |
| T-D2 | `locate absorptance` | the same → yes | `physics:absorptance`, 1 question |
| T-D3 | `locate acoustic_power_level` | *what is its unit?* → 'dB'; *does its description mention 'intensity'?* → no | `physics:acoustic_power_level`, 2 questions |
| T-D4 | `locate filled_4x6` | *what is its cols?* → 6 | `mathematics:filled_4x6`, 1 question |
| T-D5 | `locate C` | none | no tie: the read names `chemistry:C` |
| T-D6 | `fork 0` | two set questions | the transmitted word `0x000000`, 2 questions |

`--interactive` puts the same questions to the person at the terminal, each
with its possible answers and *none of these* (which, if chosen, leaves the
tie contradicted rather than resolved). That is the interface a user will
later sit behind; at this stage the developer answers.

### 7.5 What the answering path does not yet do

The open tie is reached through `tools timed-ask` only. `GLM.py -q "locate
albedo"` still answers the junction exactly as in Phase 144 and does not put
the question; carrying the question into the answer (and accepting the
answer as a follow-up turn of the session) changes answers the evaluation
pins, so it needs a frozen-path comparison. The other refusals at a tie — the
crowded zero cell of the address read, `report hole` ties, the decoder's
`classify` refusal — have no declared vocabulary yet.

### 7.6 Verdict, and what it leaves

The intuition holds where it can be measured. Held open as a tie, a refusal becomes a question: time resolves the Golay fork when later steps report sure coordinates (all 768 forks, to the transmitted word, after 8.71 reports on average), and asking resolves it faster — the GLM's own halving questions take 2.66 on average and never more than 3, the proved minimum. Waiting can never resolve a junction, because every observation of the coordinates is constant on it (proved, and 104 of 104 measured); asking for what the coordinates do not carry resolves all 387 junction runs with 0 wrong. A single false answer is undetectable without a confirming question and always caught with one. All 9 marks met.

It leaves: the question in the answering path, under a frozen-path
comparison, with the answer taken as the session's next turn; vocabularies
for the other ties (§7.5); a question that halves the 78-member
dimensionless junction (a declared measurand coordinate would be one, which
is the owner's open decision of Phase 144); and a vocabulary chosen by what a
user can answer, not only by what splits.
