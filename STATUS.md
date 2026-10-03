# Status


## Tier 0 — the coarse read

**Question.** Where does the work stand now, what is open, and how is it re-verified?

**Verdict.** This is the current state: what is done, what is open, and how to re-verify it.

**Deciding figure.** Every instrument in the table at the head of the document reports its own result on demand.

**Recomputed by.** `glm_universal.signoff.ledger.suite_totals`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

> **Positioning.** Before starting a round, read the Positioning section of
> [`PROJECT_DIRECTIVES.md`](PROJECT_DIRECTIVES.md): what is claimed, what is
> not, and why an absence at one layer is not a refutation. It is stated once,
> there, and every document in this repository is written under it.

## How to work in this repository

**Commit and push after each completed step, not once at the end.** A step is
anything that leaves the tree in a working state — one document reconciled,
one test added, one lemma proved. Never leave a session's work sitting
uncommitted: a commit is cheap, and an interrupted session that has been
committing as it goes hands over something that runs. The same rule is at the
head of [`PROJECT_DIRECTIVES.md`](PROJECT_DIRECTIVES.md) and is directive D1.

---

*The current state: what is done now, what is open, and how to check any of it
without recomputing anything by hand. The record of earlier rounds is in
[`MASTER_PLAN.md`](MASTER_PLAN.md); how to run a round is
[`ITERATE.md`](ITERATE.md).*

**Starting a new round? Read [`ITERATE.md`](ITERATE.md), then §3.4, "Named for
the next round", before anything else.**

**The round just closed (Phase 97) re-scored round 8's two misses, at the
owner's request** ([`UNPACKING_RESCORE_STUDY.md`](studies/UNPACKING_RESCORE_STUDY.md))
— Phase 96's V8 was a gap in the dialect and its V4 a declaration on a false
analogy. The Python dialect now admits argument unpacking: `f(*xs)` at a
call, spliced in place through the same iteration a `for` loop uses, and
`def f(a, *rest)` at a definition, each a named step re-checked in column 3;
keywords, `**`, defaults and starred displays stay refused by name. The
program Phase 96 refused, `read_views(*store_views(golay_encode(1234)))`, is
answered equal to CPython as a fresh declared case, beside 21 further
programs and 10 refusals as declared (0 of the 33 before); none of 311
earlier declared programs moves but U1's own source, and the differential
battery is unchanged. The framed register gains `read_on_demand`, which
reads the third view only while two views leave the fork open: on Phase 96's
full common-mode probe it gives the three-view answer on 680,064 of 680,064
reads while reading 1,371,264 views instead of 2,040,192, and on weight-5
bursts, outside the fault model, it costs Phase 96's two-view 384 wrong
answers where three views refuse. Independent faults, declared correctly on
a fresh probe: two views' live count predicted on all 8,448 reads, three
views resolve 84,480 of 84,480, 0 wrong, and for every first error exactly
346 second errors leave two views open whatever the frame — so no frame
could have met V4. 12 of 12 marks met. Proved in
`RequestProject/GLM/OnDemandView.lean`: a third view cannot change a read
two views resolve, the 346 for every permutation, and the binding of
unpacked arguments. Round 9 of the order, retrieval, or the lattice items 3,
6, 7 and 10 beside round 8, is where the next round starts.
[`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 97 is the record.

**The round before it (Phase 96) took round 8 of the order, second
readings** ([`SECOND_VIEW_STUDY.md`](studies/SECOND_VIEW_STUDY.md)) — J2 with
H's X1, then J1, then J3. `reasoning/second_view.py` is a framed register: a
codeword stored in views rotated by `0, 1, 3`, read by carrying the fork of
view 0 and pruning it by every further view, so the second reading is a path
the runtime takes on its own rather than a read the caller supplies; the
dialect reaches it as `store_views` and `read_views`. Under a common-mode
four-error burst, two views leave 174 of 10,626 bursts open (each with
exactly two live candidates, as predicted on all 680,064 reads) and three
views resolve 680,064 of 680,064 with 0 wrong; no single second frame can
resolve every burst. J1's composition, declared this time and run on a fresh
probe, answers 658,258 of 658,812 with 0 wrong and leaves open exactly the
predicted 2, 8, 32, 128 and 384. J3 is closed in the negative: the Leech
escalation on the views' own soft reading equals the intersection on 46,728
of 46,728 reads and resolves nothing beyond it, and that is a theorem.
On weight-5 bursts outside the fault model one view is wrong on every read
and three views refuse every read. 7 of 9 marks met: V4 (X1's probe through
two views, 4,160 of 4,224, 0 wrong — the register's second view reads X1's
second error rotated) and V8 (one declared program uses argument unpacking,
which the dialect refuses) are not. Proved in
`RequestProject/GLM/SecondView.lean`: the fork of a four-error read is the
truth and the truth plus each octad through the error, so views allow exactly
the octads through the union of their errors; no permutation suffices as one
second frame; the frames `(0, 1, 3)` separate every burst; the views' soft
channel ranks as the summed view distance, whose minimum is the
intersection. Its two misses were re-scored by the next round (Phase 97).
[`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 96 is the record.

**The round before that (Phase 95) took the second half of round 7 of the
order, M's imperative grammar** ([`IMPERATIVE_GRAMMAR_STUDY.md`](studies/IMPERATIVE_GRAMMAR_STUDY.md))
— sentences for assignment, simultaneous assignment, `for` and `while`
loops, branches, conditional expressions, functions with recursion and
`match`. `reasoning/reverse_tct_imp.py` spells every construct head first
with every list counted (*the program of two steps: …; while b is nonzero,
do one step: set together two names a, b to b, the remainder of a and b. the
result is a.*), reads it back, runs it on an interpreter with CPython's
semantics for the fragment, counted steps and bounded depth (`STEP_LIMIT`,
`DEPTH_LIMIT`, `NO_RESULT`, `UNBOUND`, `ARITY`), and puts a trace of the
first 24 assignments, the final values and the result in column 1, which its
own column-3 script replays. `say:` asks it only after the third sort cannot
read the text. All 7 Phase 64 programs with state are said (0 before), 13 of
13 declared sentences word for word, 21 of 21 further programs equal CPython,
41 of 41 scripts verified and 41 mutants rejected, a battery of 1412
programs with 1412 distinct sentences, 0 of 41 answers moved by limits ×10,
and 0 wrong of 450 on a post-hoc battery of 600 programs (values past 4096
bits or characters are refused `SIZE_LIMIT`). 8 of 9 marks met:
I7 is not met as declared, because Phase 68's `unpack-self` refusal is now
the more specific `UNBOUND`. Proved in
`RequestProject/GLM/ImperativeGrammar.lean`: any grammar whose every
construct is a head with a counted list of parts is uniquely readable, a
step limit only withholds, and the Euclid loop, the telescoping accumulation
and the factorial recursion of the Phase 64 programs compute what they say.
Round 8 of the order, second readings, was taken by the next round
(Phase 96). [`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 95 is the record.

**The round before that (Phase 94) took the first half of round 7 of the
order, the third sort** ([`THIRD_SORT_STUDY.md`](studies/THIRD_SORT_STUDY.md))
— I1 with M's strings, tuples and ranges. `reasoning/reverse_tct_seq.py` adds
a third sort beside numbers and Golay masks to the reverse grammar: strings
(every character spelled by name), tuples of any sort and ranges, each literal
spelled with its count first, with slices, items, concatenation, repetition,
`len`, `sum`, `ord`, `chr`, `min` and `max`, an exact evaluator and its own
column-3 script. `say:` asks the earlier grammar first, so no earlier answer
can move. The Python dialect now answers string methods over code points
(ASCII where Unicode tables would be needed) and admits lists and dicts as
immutable snapshots, refusing every in-place change `MUTABLE_CONTAINER`
(`reasoning/python_containers.py`). 28 of 28 say cases as declared (0 before);
the depth-two battery of 1116 terms reads back with 1116 distinct sentences;
21 of 21 dialect programs inside the grammar; 63 of 63 dialect cases equal
CPython in type and value (0 before), every script verified and every mutant
rejected; the differential battery 0 wrong of 2830 answered; 10 of 10 marks
met. Proved in `RequestProject/GLM/ThirdSort.lean`: count-first literals are
uniquely readable for any item spelling that is, ranges and slices read what
the evaluator says. M's imperative grammar, the second half of round 7, was
left to the next round, which took it (Phase 95). [`MASTER_PLAN.md`](MASTER_PLAN.md)
Phase 94 is the record.

**The round before that (Phase 93) took round 6 of the order, the register
against the world** ([`REGISTER_WORLD_STUDY.md`](studies/REGISTER_WORLD_STUDY.md))
— candidate C with H's first item. Two outside sources were fetched once and
frozen with their URL, date and digest (CIAAW 2024 standard atomic weights;
NIST ASD first ionization energies and ground configurations).
`runtime/register_world.py` reads every one of the register's 354 cells of
atomic weight, ionization energy and configuration against them at the
precision each side is held to, with six verdicts (agrees, agrees at the
register's stated precision, discrepant, and three silences), and never writes
to the register: atomic weight 73 / 11 / 0 discrepant / 34 world-silent,
ionization energy 10 / 68 / 24 discrepant / 6 register-silent / 10 both-silent,
configuration 107 / 1 discrepant (lawrencium) / 10 world-silent. The
consistency frame now answers any element and any of the three fields, and a
list frame returns a field's discrepancies from one question. 24 of 24 declared
questions came out as declared, with 0 wrong (2 before); 186 of 186 injected
errors are caught and 0 of 186 world values flagged. The completion gate now
reads the nested holdout as well: the covalent-radius rule is demoted and the
electron-affinity rule narrowed to the main group (nested skill 0.187, 31 of
31 folds), so the completed view is 1,344 rather than 1,442 — 98 estimates
withdrawn. The one declared move is Phase 63's iron question, now answered
*yes* at the register's stated precision. Proved in
`RequestProject/GLM/RegisterWorld.lean`. [`MASTER_PLAN.md`](MASTER_PLAN.md)
Phase 93 is the record.

**The round before that (Phase 92) took round 5 of the order, discourse
state** ([`DISCOURSE_STATE_STUDY.md`](studies/DISCOURSE_STATE_STUDY.md)) —
0b first, then D = 0a, then K3. The conversation layer of Phase 55 bound one
substituted name or refused, and its sharpest refusal was the tie.
`runtime/discourse.py` reads a fold's tie as a set the turn **produced**: *it*
or *them* names the set, the question is asked of every row by the asker that
would answer it written out, and the answer is the column of their answers —
refused `column-incomplete` when some row does not answer, as a hole refuses
a fold. The fourth shape is read: *the one before that* (the deciding turn
before the one *that* names), *them* and *both of them* (a set, the rows a
turn was about, or for *both* two single-row turns; `number-mismatch`
otherwise) and *why?* (the turn before, explained from the record). With the
router as the licence a follow-up whose rewritten question only the typed or
the stepwise planner answers is bound, and a text the machine answers as
written is answered as written (whole first). `GLM.py --converse` holds one
conversation over every surface. 29 of 29 declared follow-ups came out as
declared, with 0 wrong; Phase 55's layer gives 0 of the 20 new-behaviour
cases as declared, the session alone as the licence 0 of the 5 surface
answers, and `carry=False` returns every tie to the refusal. 15 of 15 of
Phase 55's follow-ups hold but the one declared move, 32 of 32 column cells
equal the answer asked alone, and no answer to any of 3056 earlier strings changes. Proved in
`RequestProject/GLM/DiscourseState.lean`. [`MASTER_PLAN.md`](MASTER_PLAN.md)
Phase 92 is the record.

**The round before that (Phase 91) took round 4 of the order, the planner
widenings** ([`DECLARED_FRAMES_STUDY.md`](studies/DECLARED_FRAMES_STUDY.md))
— H's E6 first, then O7's remainder and candidate 2's §6. Every widening of
the stepwise planner before it was a hand-written frame. Its fold frames are
now generated from one declaration (`runtime/frame_declarations.py`): 638 of
638 texts of rounds one to five and of the router's declared sets read alike
by the generated and the hand-written readers, and with the declaration
emptied no fold question is read. The widenings are entries in it: the
`k`-th largest and smallest value and the quartiles (bounded under holes by
round four's rule), superlatives and the top `k` (`TOP_K_TIE`; refused
`COLUMN_HOLE` under a hole), *the bounds on* a sum, a mean or a parity count
(a sum or a mean only through a declared, argued physical range —
electronegativity and ionization energy — else `RANGE_UNDECLARED`), the
present-rows parity count, *the metals* and *the rare earths*, the twelve
remaining exact SI prefixes, and *heavier*/*lighter* over the molecule table.
54 of 54 declared questions and 2 of 2 follow-ups came out as declared, with
0 wrong; round four's reader answers 0 of them, and the whole machine
answered 5 before and 41 after. Removing the round-five entries returns
every case to round four's verdict. 10 of 10 bounded answers hold over 200
completions with both ends attained, 41 of 41 scripts verify, every mutation
is rejected, and three earlier refusals move as declared. Proved in
`RequestProject/GLM/DeclaredFrames.lean`. [`MASTER_PLAN.md`](MASTER_PLAN.md)
Phase 91 is the record.

**The round before that (Phase 90) took round 3 of the order, typed
operators** ([`TYPED_OPERATORS_STUDY.md`](studies/TYPED_OPERATORS_STUDY.md))
— candidate F. Monomial wheels multiply magnitudes, so they could not tell
real, reactive and apparent power apart, nor the work (a dot product) from
the torque (a cross product). `runtime/typed_operators.py` computes complex
power `S = V * conj(I)` over the Smith chart's Gaussian rationals (and
through an impedance), the real power, reactive power, apparent power and
power factor with its sense as exact values and surds, the power triangle
from any two sides, and the dot against the cross product of rational
vectors. The watt, the var and the volt-ampere are kind-restricted names, so
*the reactive power in watts* is refused `KIND_MISMATCH`. A reactive power
whose sign the question leaves open is refused `PF_SENSE_UNDECLARED`. A
declared frame read ahead of the planner's *given* phrasing reaches all of it
through the router and `GLM.py -q`, gated by each reading's own column-3
script. 43 of 43 declared cases came out as declared, with 0 wrong. Through
the router 0 were answered before and 43 after. The naive monomial control
answers 19 and gets 15 of them wrong. 0 of 2971 earlier questions are read,
43 of 43 scripts verify, and 29 of 29 mutated claims are rejected. Proved in
`RequestProject/GLM/TypedOperators.lean`. [`MASTER_PLAN.md`](MASTER_PLAN.md)
Phase 90 is the record.

**The round before that (Phase 89) took the owner's outside material and
gated decisions** ([`QUESTION_SET_B_STUDY.md`](studies/QUESTION_SET_B_STUDY.md),
[`CONTRACT_MATRIX_STUDY.md`](studies/CONTRACT_MATRIX_STUDY.md)) — out of the
order of §3.4, at the owner's request. Two outside question sets were
supplied: Set B (14 items, each with an expected status and refusal code) and
Outside O1 (112 questions written to find boundaries). Before this round the
router read none of the 126. Declared question frames
(`runtime/question_frames.py`), each answer re-derived by its own column-3
script before output, now read every Set B item — 14 of 14 by audit (protocol
+10: 11 right, two refusals under a code other than the file's, and one
answer where the file expects a refusal, which the audit finds right:
`3x + 5y = 1` is decided by `gcd(3, 5) = 1`) — and 27 of the
112 outside questions, answered or correctly refused exactly, with **0
confidently wrong**. The other 85 are located boundaries, classed in a
Capability Failure Matrix: explanations 32, derivations and proofs 18, meta
questions about the GLM's own engineering 18, symbolic parameters 13,
designs 3, one transcendental equation. K1 is taken: `GLM.py -q` goes through
the multi-surface router, and all 177 contract questions give byte-identical
output through the routed `-q` and the old `--plan` path. Candidate P's two
contract changes were run as a 4-way matrix over 525 exact cells in two
frames: the combined change (variant D, the upper-credible rule over the
session's reads) breaks no on-grid cell in either frame and keeps more right
answers than the upper rule alone (mean on-grid retention 0.6881 against
0.5562), so it is the production baseline; the control and the
session-marginal confidence alone each break 2 on-grid cells. On the 41
framed questions the four variants give identical verdicts. Proved in
`RequestProject/GLM/QuestionSetB.lean`. [`MASTER_PLAN.md`](MASTER_PLAN.md)
Phase 89 is the record.

**The round before that (Phase 88) took round 2 of the order, the loop
through the planner** ([`PLANNER_LOOP_STUDY.md`](studies/PLANNER_LOOP_STUDY.md))
— candidates K4, I2 and O3 = M3, then a re-reading of item 9. Every surface
answered its question alone; a question whose next step depends on the value
of the last answer had no reader. The Python dialect now has three builtins
that call the rest of the machine and return exact values — `derive(target,
(name, value), …)` (the stepwise planner's goal mode), `ask(question)` (one
stepwise question) and `solve(var, equation, …)` (the reverse surface's
linear solve) — and a declared frame (*what does `E` return*, *is `E` true*)
hands a question about a Python expression to the evaluator, so a loop is the
program's own control flow: `while derive("current", ("voltage", 12),
("resistance", r)) >= 1: r = r + 1` answers 13. The program's column-3 script
re-runs every sub-answer's own script in a fresh interpreter, checks the
value is bound to that record (a solve's root substituted back and shown
unique), and re-runs the program under CPython against the checked table.
44 of 44 declared cases as declared, 0 wrong; through the router 29 of 29
answer cases answered where 0 were before; with the bridge off 0 of 34; all 66
declared mutations rejected, each at the check written for it; the contract
census unmoved (0 of 530); earlier rounds unchanged. Item 9 re-read: the same
questions asked in English are answered by no surface — the first measured
instance of a tool a problem-driven front end reaches and the kind-driven
dispatcher does not; the reverse-call planner is still not promoted (D14).
Proved in `RequestProject/GLM/PlannerLoop.lean`. [`MASTER_PLAN.md`](MASTER_PLAN.md)
Phase 88 is the record.

**Earlier, Phase 87 began by reading the open candidates
together** ([`ROADMAP_STUDY.md`](studies/ROADMAP_STUDY.md)), at the owner's
request: the 49 open items of §3.4 reduce to seven tracks, several items are
one piece of work under two or three letters, and the rounds are now ordered
so that each reads what the one before built (the order is at the head of
§3.4). **It then took round 1 of that order, the measurand register**
([`MEASURAND_REGISTER_STUDY.md`](studies/MEASURAND_REGISTER_STUDY.md)) —
candidate K2, the rest of O5 and the second half of candidate 1. The
stepwise planner now reads a register value through the measurand it holds:
a first ionization energy or an electron affinity is the least energy one
photon must carry to ionize the atom or detach the electron, so *given the
ionization energy of hydrogen and wave speed = 299792458, what is the
wavelength in nanometres* is answered (about 91.18 nm, the Lyman limit),
where before the value was a molar energy no wheel could read. A power
crosses a motor, generator, pump or turbine only through a stated efficiency
in (0, 1] — a law of its own across the junction table's non-identities —
and an efficiency outside that range, stated or derived, is refused
`EFFICIENCY_OUT_OF_RANGE`, one that names no declared conversion
`EFFICIENCY_UNDECLARED`. The elementary charge is an exact unit. 30 of 30
declared questions as declared, 0 wrong; through `GLM.py --ask` the machine
answered 2 of the 30 before and 18 after; the naive control (the conversion
read as an identity) answers 7 conversion cases, all wrongly; earlier rounds
unchanged. The scale table's offset row (candidate 1's first half) is still
not shipped: no register holds a Celsius reading. Proved in
`RequestProject/GLM/MeasurandRegister.lean`. [`MASTER_PLAN.md`](MASTER_PLAN.md)
Phase 87 is the record.

**The round before that (Phase 86) began with a quick tidy of candidate P
and then took candidate O5** ([`MEASURANDS_STUDY.md`](studies/MEASURANDS_STUDY.md)):
measurands rather than units. The unit check compared dimensions only, so it
could not tell a torque from an energy or a frequency from an angular
velocity. The stepwise planner now holds the SI Brochure's restrictions on
special unit names (the hertz is not an angular velocity, the newton metre
not an energy) and refuses `KIND_MISMATCH`; it reads a temperature in degrees
Celsius or Fahrenheit as a level or a difference by the quantity it feeds,
refusing `LEVEL_AS_DIFFERENCE`, `DIFFERENCE_AS_LEVEL`, `KIND_CONFLATION` and
`BELOW_ABSOLUTE_ZERO`; and it supplies the exactly defined Planck constant and
speed of light when the givens alone derive nothing (*given frequency = 5
terahertz, what is the energy*). 31 of 31 declared questions as declared, 0
wrong; the dimension check alone answers all 5 declared kind mismatches with
a number. Five earlier declared verdicts of stepwise round two were wrong in
the physics — they fed a melting point, a temperature level, to `energy =
mass · specific heat · temperature`, which reads a difference — and are
amended to `LEVEL_AS_DIFFERENCE`; as a consequence mark H3 of the
held-precision study is no longer met (both its witnesses were that
conflation). The P tidy measured the soft floor's named repairs: a finer grid
or a higher guard repairs nothing; an upper-credible rate rule removes both
on-grid breaks; the breaks above the grid stay (runtime contract unchanged,
the owner's call). Proved in `RequestProject/GLM/MeasurandKinds.lean` and
`RequestProject/GLM/RateRepair.lean`. [`MASTER_PLAN.md`](MASTER_PLAN.md)
Phase 86 is the record.

**The round before that (Phase 85) took candidate 2 and the last item of
O7** ([`HOLE_FOLDS_STUDY.md`](studies/HOLE_FOLDS_STUDY.md)): folds with a
hole. The stepwise planner now reads the median, the largest and the smallest
value and the rank of a row (*the rank of gold by density among the
transition metals*) over every element or a declared class. Over a column with
missing readings, a median or a rank is answered as the exact interval every
completion of the holes lands in — *between 6 and 15*; the median valence
electrons of the transition metals is `2` with four readings missing, because
the interval closes — and a side the holes leave open is refused
`COLUMN_HOLE` by name (the largest density of the transition metals is open
above). The present-rows question asked as its own (*the average
electronegativity of the noble gases that have one*) is answered over the rows
that hold a reading, with the missing rows named in the answer; `NOT_A_MEMBER`
and `COLUMN_EMPTY` are the new refusals. 34 of 34 declared questions and 2 of
2 follow-ups as declared, 0 wrong; through `GLM.py --ask` the machine
answered 0 of the 34 before the round and 25 after; every bounded answer held
on each of 200 completions with both ends attained; 26 of 26 chain scripts
verified with every mutation rejected; round three unchanged (8 of 8 marks).
The rule is proved in `RequestProject/GLM/HoleBounds.lean`.
[`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 85 is the record.

**Before that, Phase 84 took item O7 of candidate O**
([`STEPWISE_THREE_STUDY.md`](studies/STEPWISE_THREE_STUDY.md)): the stepwise
planner's widenings. It now reads comparatives through a declared register
field (*which is denser, gold or lead*, *is oxygen older than hydrogen*, *how
much heavier is gold than iron*), *how many more* electrons and valence
electrons, the tera- and pico- prefixes, and sums, means and parity counts over
every element or a declared `group_block` class (*the average atomic number of
the noble gases*, *how many of the lanthanides have an odd atomic number*). It
refuses by name where a comparative has no declared field
(`COMPARATIVE_UNDECLARED`), where the register records a value as missing
(`VALUE_MISSING`), where a column has a missing reading (`COLUMN_HOLE`, the
missing rows named), and where a class is not the register's
(`SET_UNDECLARED`). 47 of 47 declared questions and 2 of 2 follow-ups as
declared, 0 wrong; through `GLM.py --ask` the machine answered 6 of the 47
before the round and 32 after; 34 of 34 chain scripts verified with every
mutation rejected; rounds one and two unchanged (8 of 8 marks).
[`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 84 is the record.

**The round before it (Phases 81–83) finished candidate P.** Phase 81
([`AGREE_CHANNEL_STUDY.md`](studies/AGREE_CHANNEL_STUDY.md)) gave the second
reading (`agree`) an exact channel measure — a census of every pair of reads,
164,051,805 resolved pairs in 28 rate-independent histograms — and put it in
the confidence-floor hunt: its working threshold is 9999/10000 up to 1/20 and
999/1000 at 1/10, where the decoder alone has none (8 of 8 marks). Phase 82
([`RATE_POSTERIOR_STUDY.md`](studies/RATE_POSTERIOR_STUDY.md)) estimates the
rate from the reads: an exact posterior over a declared grid with a guard
point, a marginal confidence, `RATE_GRID_EXCEEDED`, and the dialect builtins
`decode_soft`, `decode_soft_floor`, `agree_soft`; the soft floor keeps its
promise on the prior average in every cell, but at a fixed rate it broke in 2
grid cells (1/10, floor 9999/10000) and at 1/5, above the grid (7 of 7 marks;
one declared expectation failed). Phase 83
([`LAW_TRIAGE_STUDY.md`](studies/LAW_TRIAGE_STUDY.md)) triaged the 106
unresolved knowledge-base laws under a service rule: 0 absorbed, 3 already
served, 3 refuted, 100 retired with a reason (5 of 5 marks).
[`MASTER_PLAN.md`](MASTER_PLAN.md) Phases 81–83 are the record.

**The round before that (Phase 80) moved the target**: under directive
**D15** it moved **refusal**. It took item P3 of candidate P
([`CONFIDENCE_FLOOR_STUDY.md`](studies/CONFIDENCE_FLOOR_STUDY.md)): a
confidence floor as a refusal. At the owner's direction no threshold was
picked in advance: a declared grid of seven thresholds was hunted at five
bit-flip rates over an exact channel census — every probability a sum over
every received word — against a declared meaning of *working* (the floor keeps
its promise `P(wrong | answered) ≤ 1 − t` and keeps at least 9/10 of the right
answers, for the decoder and the context stage over each of K1's case sets).
The working threshold is 9999/10000 up to 1/50 and 999/1000 at 1/20, so the
owner's candidates 99 % and 99.9 % both work there; at 1/10 no threshold
works, because the complete decoder's confidence takes one value per coset
weight and any floor costs it more than a tenth of its right answers. There
the owner's fallback applies: the graded answer, the value with its exact
confidence beside it and nothing refused on confidence. The Python dialect
reaches both as `resolve_at` / `agree_at` (graded) and `resolve_floor` /
`agree_floor` (`BELOW_FLOOR`). Overstating the rate is proved safe
(`RequestProject/GLM/ConfidenceFloor.lean`); understating it breaks the
promise in 30 of 210 cells. 6 of 7 marks met; the miss is one program whose
declared refusal was wrong. [`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 80 is the
record.

**The round before that (Phase 79) moved the target**: under directive
**D15** it moved **refusal into derivation**. It took the third item of
candidate M: a complete integer decision behind the integer sort of Reverse
Three Column Thinking
([`INTEGER_DECISION_STUDY.md`](studies/INTEGER_DECISION_STUDY.md)). Where round
three's elimination with rounding left a case open and refused
`INTEGER_UNDECIDED`, the Omega test now decides it — an integer point, or a
refutation tree of combinations, fresh-variable substitutions and splits that
the column-3 script checks by arithmetic alone. 22 of 22 declared questions
(Pugh's parallelogram among them) are answered as declared with 0 wrong, where
round three refused all 22; a declared battery of 600 questions agrees with
enumeration everywhere, 0 undecided against 31; nothing round three answered
moved. `INTEGER_UNDECIDED` is kept only for a declared limit of 5000 search
steps. The facts the search relies on are proved in
`RequestProject/GLM/IntegerDecision.lean`; `tools integer-decision` re-takes
the marks. The round began by completing Phase 78's release, which had been
written up but not signed. [`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 79 is the
record.

**The round before that (Phase 78) cut the cost of an iteration**, at the
owner's request. The Lean development is held once, in
`overlay/glm_lean/RequestProject/`, and `lake build` compiles it in place; the
repository-root copy, its mirror step and the instrument that compared the
two are gone. A unit's closure now follows what the unit reads: data files by
name, docstrings not dependencies, and the generated figure and block regions
of a document masked from every unit except the three that render or check
them — so a refresh that only moves counts (they all live in
`corpus/render.py`, recomputed into [`overlay/FIGURES.md`](overlay/FIGURES.md))
no longer re-opens the units that quote them. The mean closure fell from 284
files to 183. A round closes with one command, `signoff --close`, which re-runs
only what is stale and then verifies the release
([`ITERATION_COST_STUDY.md`](studies/ITERATION_COST_STUDY.md) §5g;
[`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 78 is the record).

**The round before it (Phase 77) moved the target**: under directive
**D15** it moved **refusal** and **derivation**. It took item P1 of candidate
P ([`DECODER_CONFIDENCE_STUDY.md`](studies/DECODER_CONFIDENCE_STUDY.md)): the
confidence law Phase 75 absorbed is now attached to the decoder's own
readings. At a declared bit-flip rate, the complete decoder, the carried
fork's context stage and the second reading each give their answer with the
exact probability that it is the codeword sent, and refuse where they refused
before, by the same name; the Python dialect reaches them as
`decode_confidence(rate, s, *cases)` and `agree_confidence(rate, *reads)`,
each answer with a fresh-interpreter script that recomputes the posterior by a
brute-force sum. The measurement K1's *0 wrong* could not give: at a rate of
1/10, 294,976 of the 592,268 resolved forks fall below 99 %, the least at
0.909 with 32 cases, and every one of them is at least the floor proved in
`RequestProject/GLM/DecoderConfidence.lean`. 5 of 6 marks met; the sixth
missed on a wrongly declared clause about the witness (an exact tie, each
survivor just below one half, not exactly one half). Closing the round also
repaired a closure leak the two rounds before had opened (three provenance
labels in `salvage.py` had put the whole Lean development into every unit that
builds a session; [`ITERATION_COST_STUDY.md`](studies/ITERATION_COST_STUDY.md)
§5). [`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 77 is the record.

**The two rounds before it (Phases 75 and 76) moved the target**: under
directive **D15** they moved **derivation** and **refusal**. *Phase 75* took
the owner's reading of candidate P — not another subsystem, but each retained
law tested, improved where it can be, and absorbed where it is of use
([`LAW_ABSORPTION_STUDY.md`](studies/LAW_ABSORPTION_STUDY.md)). Eleven laws
are absorbed as computed self-knowledge of the substrate: the typed planner
now answers questions about the GLM's own code, decoder and lattice (the
codewords, the rate, the minimum distance, the covering radius, how many
errors are corrected, the outcome and exact probability of a decoding at an
error weight or a noise rate, the confidence of a decoding at a distance, the
kissing number, XOR closure, descent) by computing from the running
substrate, and each answer names the law it was absorbed from — 36 of 36
declared questions as declared, 0 wrong, against 0 answered before; two laws
were already GLM definitions, three were retested in dimensionless form and
refused, forty-nine are retired with a reason each. Absorbing the decoder laws
turned up a statement none of them made, now proved: an odd-weight error is
never refused, and one of weight 5 or more is always miscorrected
(`RequestProject/GLM/LawAbsorption.lean`). *Phase 76* took item O6
([`HELD_PRECISION_STUDY.md`](studies/HELD_PRECISION_STUDY.md)): every answered
derivation that reads a register value now states the exact interval its
answer lies in, carried from the precision the register wrote the value at —
8 of 39 goal and narrative chains, 2 of them exact because the held value
cancels, where step-by-step interval arithmetic would have reported a spread;
the corner bound is proved in `RequestProject/GLM/HeldPrecision.lean`. No
existing verdict or value moved in either round.
[`MASTER_PLAN.md`](MASTER_PLAN.md) Phases 75 and 76 are the record.

**The round before (Phase 74) moved the target**: under directive
**D15** it moved **refusal**. It took the owner's request to review two files
from an older study rather than a candidate of §3.4: a GLM-lens review of the
426 laws of the UBP knowledge base and the 65 laws it retained
(`source_material/UBP_LAW_GLM_REVIEW.md`,
`source_material/retained_laws_verified_65.csv`;
[`LAW_REGISTER_STUDY.md`](studies/LAW_REGISTER_STUDY.md)). The sixteen exact
rows re-grade as 8 structural, 2 overclaimed, 3 definitional, 2 arithmetic and
1 near-miss; every structural row now cites a Lean theorem, most of which were
already in the tree. Three decoder laws are made exact — a complete decoder is
right exactly when the error has weight at most 3, a weight-4 error is always
refused, a weight-5 error is always wrong — and the outcome of every error
weight is tabulated, which refutes "hardened storage guarantees 100% integrity
at noise ≤ 3%" (0.005321 not right, 0.0005925 silently wrong) and prices the
GLM's own refusal at a six-way tie: 5 wrong answers withheld per right answer
given up. `LAW_LOGIC_GEO_001` holds for XOR only (AND and OR are not code
operations), the review's "descent in exactly d steps" is contradicted by the
exhaustive descent census, and the review's two "equal" NRCI means differ by
2.3 × 10⁻⁸ (the first seven weight moments of the code are binomial, the
eighth is not). Of the forty-nine numeric rows, 30 are not predictions of a
measured dimensionless number (unit-dependent, a bound or range, KB-internal,
a restatement, a duplicate); of the 21 external formulas a within-template
look-elsewhere test admits 2, both for m_μ/m_e, and both miss the measurement
by over a hundred standard deviations. `reasoning/law_register.py` is the
refusal faculty (`admit`, and `look_elsewhere` for any new claim), reachable
as `tools law-register` and the toolbox tool `law register`;
`RequestProject/GLM/LawRegister.lean` proves the decoder, closure and moment
facts. [`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 74 is the record.

**Two rounds before (Phase 73) moved the target**: under directive
**D15** it moved **derivation** and **refusal**. It took items two and four
of candidate O below — the frames the stepwise planner's leaves lacked, givens
written with units, and register values fed to the wheels
([`STEPWISE_TWO_STUDY.md`](studies/STEPWISE_TWO_STUDY.md)). The stepwise
planner now reads *how many more protons does iron have than carbon* (20;
the reverse order is refused `DIFFERENCE_REVERSED`), *is the atomic number of
gold odd* (with the witness `79 = 2 x 39 + 1`) and *the average of the
melting points of iron, copper and gold* (45061/30). A given may be written
with a unit (*voltage = 12 kilovolts*, *36 kilometres per hour*) and a target
asked in one (*the current in milliamperes*): the unit is read through a
declared exact table whose dimensions are derived from the register's own
unit definitions (`runtime/quantity_units.py`), checked against the wheel
quantity's dimension and converted into SI, and a unit that is unknown, of
another dimension, inexact (π, the dalton) or offset (degrees Celsius) is
refused by name. A given may be a register value (*temperature = the melting
point of iron*), carried into SI through the Phase 55 scale table, so the
entropy of 2 kg at iron's melting point is derived with the stored heat
stitched in. Every new step has its own three columns and the chain's script
re-derives each conversion factor from the tables. On 53 declared questions,
2 narratives and 2 follow-ups: all as declared, 0 wrong, where round one's
reader answers 0 of the 53; a strip-the-units reading gets 6 of them wrong and
answers 7 of the unit refusals; 39 of 39 scripts verified and 22 of 22 unit
lies rejected; round one's corpus unchanged. It also fixed a round-one defect:
a decimal given failed its own script. `RequestProject/GLM/StepwiseFrames.lean`
proves the mean order-free and bounded, a monomial law unit-invariant exactly
when dimensionally homogeneous, an offset no multiplication, and a register
feed sound when the register is right. [`MASTER_PLAN.md`](MASTER_PLAN.md)
Phase 73 is the record.

**An earlier round (Phase 71) moved the target**: under directive
**D15** it moved **address**. It took items N3 and N4 of candidate N
([`NATIVE_WORDS_STUDY.md`](studies/NATIVE_WORDS_STUDY.md)): the word-overlap
ranking — the standard method Phase 70's ledger left far ahead of every
lexical address — computed on Golay words of the tokens. A token's parts
(split at `_`, `.`, `'` and digits) each give a **letter word**, the 24-bit
mask of their letter buckets, whose **Golay class** is every nearest codeword
of the complete decoder; a token's **Golay name** is its letter word and an
index that separates the vocabulary's tokens sharing it. The names carry the
token overlap exactly (W1; `jaccard_names`), so the native ranking
`words_native` — names, then part letter words, then classes, then Leech
distance — can move a candidate only inside a tie of the standard's overlap
(`take_map_overlap_eq`), and it moves them well: 190 against 182 hits at 5 on
211 declaration queries, 94 against 92 on 103 goal queries, and level on 60
document queries. The live document ranking (`corpus.address.retrieve`)
now reads it. Overlap on Golay letter words alone beats the lexical Leech
address of ledger rows 4 and 5 (187 against 147 on the declarations). The
Leech tie-break alone (`text_leech`) loses five queries at k = 1 and is not shipped
(W6). `RequestProject/GLM/NativeWords.lean` proves the name overlap exact, the
refinement confined to ties and a shared Golay class a near letter set.
[`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 71 is the record.

**An earlier round (Phase 70) moved the target**: under directive
**D15** it moved **address**. It took the owner's instruction — *where a
standard method is equal to or only slightly better than a Golay-Leech or 24D
native method, retain the native method and refine it to match or beat the
standard one* — rather than a candidate of §3.4
([`NATIVE_PARITY_STUDY.md`](studies/NATIVE_PARITY_STUDY.md)). Every measured
native/standard pair was put in one ledger (8 rows: 3 native ahead, 1 parity,
1 standard narrowly ahead, 3 standard far ahead) and the middle classes were
taken. A Leech address at scale 9 is `9f + e` with every `|eᵢ| ≤ 4`, so it
reads back to its features exactly by rounding (3,976 of 3,976 stored and 102
of 102 goal addresses). Reading **two** native books (structural, then
identifier-letter), each in its two layers, gives 83 hits at 5 on 210
declaration queries against 80 for the raw features and 31 against 27 on 102
goal queries, identical query for query to the like-for-like standard
ranking; `retrieval.retrieve` defaults to it (`native2`). The controller's
read-back scorer solves 24 of 24 tasks, all minimal, with the exact scorer's
2,140 proposals, where the shipped Leech scorer solves 18. One book in two
layers is a draw that moves with the corpus, as `residue_congr` predicts (the
residue is a function of the features). On the documents the native rankings
stay within one relevant section of the raw vector, and the live word-overlap
ranking now breaks its ties by Leech distance at no cost. `RequestProject/GLM/NativeParity.lean`
proves the read-back exact, the residue a function of the features, and that
a refinement can reorder only inside ties. [`MASTER_PLAN.md`](MASTER_PLAN.md)
Phase 70 is the record.

**An earlier round (Phase 69) moved the target**: under directive
**D15** it moved **derivation** and **refusal**. It took the integer-sort item
of candidate M ([`REVERSE_TCT_STUDY.md`](studies/REVERSE_TCT_STUDY.md)
§10–§12). `entails over the integers:` and `bounds over the integers of x:`
decide the round-two statements with every variable an integer: a floor
quotient or remainder of a variable by a constant is split into one case per
residue with a fresh integer quotient, and each case is decided by elimination
with every row tightened over ℤ, a refutation certified by its derivation.
All 29 declared entailment cases and all 10 bounds cases are answered as
declared, 0 wrong; 34 of 34 column-3 scripts `VERIFIED True` and 34 of 34
mutated certificates rejected; 116 battery questions agree with brute force
over a box. Over ℚ the same 29 questions get 20 `NOT_POLYNOMIAL` refusals and
9 different answers (`x > 2` does not entail `x ≥ 3` there). Where
elimination with rounding stops the answer is the new refusal
`INTEGER_UNDECIDED` (Pugh's system). `RequestProject/GLM/ReverseTCTThree.lean`
proves the residue split exact and exhaustive, the tightenings exact and the
derivation sound. [`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 69 is the record.

**An earlier round (Phase 68) moved the target**: under directive
**D15** it moved **derivation** and **refusal**. It was candidate L, round
two of [`REVERSE_TCT_STUDY.md`](studies/REVERSE_TCT_STUDY.md) (§7–§9), on the
owner's three notes. **The fragment is wider**: floor quotient, remainder,
`abs`, `min`, `max`, negative exponents, the bitwise operators and shifts, and
Golay masks as a second sort (count-first literals, the four set operators,
`len`, Hamming distance, `in`, subset) — 216,723 widened terms and 18,500 mask
terms round-trip with 0 collisions, and 36 of the 83 Phase 64 dialect programs
are now inside, each agreeing with the dialect's value (8 before).
**Disjunction** (`either …, or …`) makes a statement a conjunction of clauses,
so `negate` is closed under De Morgan: the `NOT_IN_FRAGMENT` refusal for a
compound negation is gone, and over a declared battery of 650 normal forms the
double negation is certified for all 650 and the negation is exact at every
grid point. `entails`, `bounds` and `equivalent` split disjunctions and
`abs`/`min`/`max` into cases. **The loop**: `relay:` hands what column 2
holds to the planner as a question in the planner's own language, reads the
answer back into column 2 and realises it as reverse-grammar sentences — 20
of 20 relay cases as declared, 32 of 32 handoffs agree or are consistent,
0 disagree, where the relayed sentences given verbatim are answered 0 of 15 and
the planner chained to itself recovers 11 of 13 values. 92 of 92 round-two
column-3 scripts `VERIFIED True`, 84 of 84 mutated certificates rejected; the
Phase 67 cases all hold (four superseded on purpose).
`RequestProject/GLM/ReverseTCTTwo.lean` proves the widened and clause grammars
uniquely readable, negation by distribution and its simplification exact, the
case splits exact, and Python's floor-remainder convention.
[`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 68 is the record.

**An earlier round (Phase 67) moved the target**: under directive
**D15** it moved **derivation** and **refusal**. It took the owner's
instruction — *a reverse three column thinking function where the script and
math generate the language column* — rather than a candidate of §3.4
([`REVERSE_TCT_STUDY.md`](studies/REVERSE_TCT_STUDY.md)). Column 1 is now a
function of column 2: a declared prefix-first grammar realises an exact term
or statement over ℚ as English, a declared reader parses it back, and
`RequestProject/GLM/ReverseTCT.lean` proves the realisation uniquely readable.
All 176,617 terms of the declared battery round-trip with 0 collisions where
the natural infix realiser has 5,684. On that footing seven semantic
operations are taken on the mathematics and realised back into sentences —
`say`, `equivalent`, `paraphrase`, `negate`, `solve`, `entails`, `bounds` —
and every declared case is answered as declared, 0 wrong, where the default
path answered 0 of the 58 entailment, solve and bounds questions. Each
answer's column-3 script re-reads column 1 and re-checks the certificate in a
fresh interpreter: 94 of 94 `VERIFIED True`, 69 of 69 mutated certificates
rejected. `GLM.py --ask "entails: … ; …"` (a fifth surface on the router) and
`GLM.py --reverse TEXT` reach it. [`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 67
is the record.

**An earlier round (Phase 66) moved the target**: under directive
**D15** it moved **derivation** and **refusal**, and connected what was
already built. It took the owner's instruction — *find a way to increase GLM
capability and ensure the working parts are connected and available as
needed* — together with candidates E and 3 of §3.4
([`CONNECTED_MACHINE_STUDY.md`](studies/CONNECTED_MACHINE_STUDY.md)). One
path, `GLM.py --ask TEXT`, now gives any text to the first surface that reads
it — the toolbox, the Python dialect, the engineering surface, then the
planner — and names the surface: 136 more of the declared questions are
answered correctly on it than on the planner alone, with no wrong answer
added, and none of the 177 contract cases changes surface. The eight tested
modules nothing reached are tools (`--ask "tool moonshine"`, …), and the
wiring audit reads 0 of 96 reasoning modules unreached. The engineering
surface derives *across wheels*: naive composition of the ten wheels licenses
161 formulas no wheel does and 158 of them are wrong
(`energy = 2 * mass * speed_of_light^2` among them); with a declared junction
table it answers the 3 laws and refuses the 158, 0 wrong.
`RequestProject/GLM/ConnectedMachine.lean` proves the router's rule and the
soundness of splitting. [`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 66 is the
record.

**An earlier round (Phase 65) moved the target**: under directive
**D15** it moved **refusal** and **address**, and moved **derivation**
conditionally. It took the owner's instruction on the `AMBIGUOUS` Golay reads
rather than a candidate of §3.4: the six equidistant candidates of a
deep-hole read are now **carried** as a fork with a ledger until a later
decision resolves them, and the read is escalated to the Leech lattice
([`CARRIED_FORK_STUDY.md`](studies/CARRIED_FORK_STUDY.md)). Four of the six
marks declared before the module existed were met and two were not. Every
certified stage — the declared cases (under a named closed-world assumption),
a second reading, an unsure set — gave 0 wrong: 592,268 of the 658,812
declared-case reads that `classify` refuses are answered, the declared 90 %
mark missed at 32 cases (85.8 %); X1's second reading is reproduced (4,224 of
4,224) and reachable; the unsure set answers all 3,840 of its reads. Escalated
without new information, every one of the 1,771 ties lifts to a certified
**A₁²⁴** deep hole of the Leech lattice (48 vertices, 8 over each candidate);
the soft-reading estimate is right on 512 of 768 and missed its mark. The
Python dialect reaches it through `nearest`, `resolve`, `agree` and
`resolve_unsure`; `tools carried-fork` re-takes it.
[`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 65 is the record.

**An earlier round (Phase 64) moved the target**: under directive
**D15** it moved **derivation**, **refusal** and **address**. The GLM now
speaks a declared dialect of Python
([`PYTHON_SPEECH_STUDY.md`](studies/PYTHON_SPEECH_STUDY.md)): it evaluates a
program exactly on the substrate — bitwise operations through the eight
Toffoli/Fredkin sub-registers, shifts as dyadic moves, slices as index maps
onto MOG cells, sets as Golay masks, `match` by coset decoding — and returns a
Three Column payload whose third column re-derives every step in a fresh
`python3 -I`. All six pass marks declared before the module existed were met:
83 of 83 declared programs equal CPython in type and value with every script
`VERIFIED True` and every mutated claim caught, 26 of 26 refusals named, and
0 wrong over a 7128-expression differential battery; the existing question
surface solves 0 of the 83. `GLM.py --python SOURCE` reaches it.
[`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 64 is the record.

**An earlier round (Phase 63) moved the target**: under directive
**D15** it moved **derivation** and **address**, and sharpened **refusal**. It
was round two of
[`SUBSTRATE_NATIVE_COGNITION_STUDY.md`](studies/SUBSTRATE_NATIVE_COGNITION_STUDY.md):
three near misses of the first round were looked at again and refined into
planner frames — interval consistency, rational recognition with a uniqueness
certificate, and dimensional derivation — which answer 26 of 33 declared
questions and refuse the other 7 as declared, with 0 wrong where the grammar
answers none. The typed planner is now the default path of `GLM.py`
(`--grammar` asks the grammar alone); the 177 contract cases give the same
outcomes either way. A language model as parser (G1) is declined for good.
[`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 63 is the record.

**An earlier round (Phase 60) was a documentation round** taken at the
owner's request: it moved none of **derivation**, **address** or **refusal**
(D15). [`GLM_ACADEMIC_PAPER.md`](studies/GLM_ACADEMIC_PAPER.md) now covers
the system as a whole (the machine, addressing, measured capability, negative
results, method, and a ledger of the supplied material taken and left), and
[`GLM_Complete_Number_Theory_Evidence.md`](studies/GLM_Complete_Number_Theory_Evidence.md)
gained §15–§21. It also resynced the overlay Lean mirror, which Phase 59 had
left one file short. [`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 60 is the
record.

**The round before it (Phase 59) moved the target**: under directive
**D15** it moved **derivation** and **refusal**, with five **address**
answers and no **table**. It took the supplied formula-wheel session record
(`source_material/formula_wheel/`) rather than a candidate of §3.4, because
the request was to have the GLM reason in electrical and mechanical terms and
the record's own first priority is to run its studies against the GLM's
substrate. `glm_universal.engineering` reads formula wheels as rational spans
with certificates, the Smith chart over Gaussian rationals, the force-voltage
and force-current analogies as maps on laws, and the delta-sigma loop by
theorem, and `engineering/speak.py` lets the machine be asked in words
(`GLM.py --eng`, `GeometricSession.ask_engineering`). On 63 questions
committed before any of that code, both existing paths refused all 53
answerable ones; through the surface it answers **53** correctly and refuses
**10** correctly with **0** wrong, and it reads none of the 374 questions the
machine already answers. The register agrees with the corrected formula study
on all 41 cases at SI7 and at EXT10, the force-voltage analogy preserves 9 of
9 laws each way, and `RequestProject/GLM/EngineeringWheels.lean` proves the
licensing rules (span membership, translation, the Smith disc, the periods of
the bitstream). [`studies/ENGINEERING_LANGUAGE_STUDY.md`](studies/ENGINEERING_LANGUAGE_STUDY.md)
is the study and [`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 59 the record.

**The round before that (Phase 58) moved the target**: under directive
**D15** it moved **derivation** and **refusal**, and most of what it gained
is **table** — coverage of operations the machine already had. It took the
supplied roadmap (`source_material/GLM_IMPROVEMENT_ROADMAP.md`) rather than a
candidate of §3.4, because the measurement the roadmap quotes still held: the
frozen language probe, asked through `GeometricSession.ask`, scored two
correct of twenty although the answers to most of it were held behind the
formal grammar. `glm_universal.runtime.semantic_plan` reads a question into
typed plans over the operations the session already has — each slot grounded
against what the registers hold, each plan run, and an answer given only when
every licensed plan agrees — and adds two things that compute rather than
route: exact integer arithmetic and conversion between units whose relation
is a definition. Through it the frozen probe scores
**<!--figure:plans-probe-correct-->19<!--/figure-->** correct and
**<!--figure:plans-probe-wrong-->0<!--/figure-->** wrong, passing the mark
declared before the probe was first run; on the
**<!--figure:plans-held-total-->110<!--/figure-->** held-out questions
committed before the planner existed it answers
**<!--figure:plans-held-correct-->86<!--/figure-->** correctly and refuses
**<!--figure:plans-held-correct-refusal-->22<!--/figure-->** correctly with
**<!--figure:plans-held-wrong-->1<!--/figure-->** wrong — a register holding
iron's atomic weight to four figures where the world uses five, recorded as a
data-truth finding rather than edited away. Two readings that disagree are
refused, not chosen between: *does energy have the same dimensions as
torque?* is yes in the SI projection and no in the extended vector, and the
answer names both. It is opt-in (`GLM.py --plan`,
`GeometricSession.ask_planned`), so the 177-case contract set is untouched.
`RequestProject/GLM/SemanticPlan.lean` proves the licensing rule order-free,
sound and conservative over the grammar, and refutes the first-licensed rule.
[`studies/SEMANTIC_PLAN_STUDY.md`](studies/SEMANTIC_PLAN_STUDY.md) is the study
and [`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 58 the record.

The round before these (Phase 55) **moved the
target**: under directive **D15** it moved **refusal**, and widened
**derivation** to a fold over rows of two tables at once. It took candidate 1
of §3.4 — the scales neither operation could bridge — and wrote them down.
`glm_universal.reasoning.scale_conversion` declares nine scales over four
quantities (mass in `u`, molar energy in `kJ·mol⁻¹`, temperature in `K`,
length in `pm`), each row an exact positive-affine map into its quantity's
canonical unit with the source its numbers came from, so that a conversion is
a fact someone wrote down rather than a guess from a name. Seven of twelve
questions declared before the run are answered and five refused, every one of
the twelve as declared; the ordering and extremum operations come out on their
own declared sets exactly as they did — 7 of 7 and 8 of 8 — and `largest mass`
now gathers the element rows and the molecule rows into one unit and folds
them. What the table does not reach it still refuses: it relates 6 of the
7,750 pairs of the 125 numeric scales the field surface holds, and every other
pair is `different-scale` with the table's own reason.
`RequestProject/GLM/ScaleConversion.lean` is the proved half —
`cmpQ_apply` and `order_conversion_invariant` that a positive conversion
leaves the verdict alone, `orderWith_conservative` that the wider operation
never changes an answer the bare one gave, `orderWith_eq_none_iff` that its
silence is still exactly stated, `the_table_carries_the_claim` that the
declaration and not the code is what licenses a bridge, and
`negative_factor_flips_the_verdict` and `raw_gather_names_the_wrong_row` for
the two things it must not do.
[`studies/SCALE_CONVERSION_STUDY.md`](studies/SCALE_CONVERSION_STUDY.md) is
the study and [`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 55 the record.

The round before it **moved the target** too: under directive **D15** it moved
**addressing** and **refusal**. It
did not take a candidate from §3.4; it took the material supplied with it —
`source_material/conversation_experiment/`, eight scripts and a research
document on a conversational GLM, every one of which runs unmodified against
the package — tested its claims, and built the one thing in it this system
could not do at all: a **turn that refers back to an earlier turn**. *describe
it*, *and the smallest?* and *and oxygen?* are now bound to what the
conversation has already said, by the only test that makes the reference a
reading of the registers rather than a guess about word order — a candidate is
**licensed** when the query it produces actually solves. Eight of fifteen
declared follow-ups are bound and seven refused, every one of the fifteen as
declared, where the same fifteen texts asked of a session with no memory are
answered **none** of the time; and the rule a reader would assume — bind to
the most recent mention — differs on three of the ten pronoun follow-ups,
losing one answer the registers hold and giving two confident answers to
questions that have no single answer.
`GLM.Conversation.most_recent_mention_is_not_the_antecedent` is that control
refuted as a theorem rather than as a measurement. Two claims of the supplied
material did **not** survive being re-run, and are recorded as refuted: the
higher-order analogy whose second constraint has no exact solution and
contributes nothing, and the periodic-table reading that is a renaming of two
carrier coordinates.
[`studies/CONVERSATION_STUDY.md`](studies/CONVERSATION_STUDY.md) is the study,
`RequestProject/GLM/Conversation.lean` the proved half, and
[`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 54 the record.

The round before that **moved the target** too: under directive **D15** it
moved **derivation** and **refusal**. It
took candidate 1 of §3.4 — the column rather than the pair — and built the
operation that closes it: `extremum`, one coordinate read off *every* row of
one declared table and folded to its end, or refused. Four of eight declared
columns are folded and four refused, every one of the eight as declared before
the run, and the two refusals it was built for are the result rather than the
cost: a column with a hole in it has no extremum, because
`GLM.ColumnExtremum.extremum_over_present_is_not_the_extremum` exhibits a
column whose extremum over the rows that are filled in is a different value at
a different row, and a column gathered from two scales is not one column,
because `extremum_not_invariant_under_one_row_rescaling` exhibits a one-row
rescaling that moves the winner where `extremum_scale_invariant` shows that
rescaling the shared scale cannot. Where the end is a tie every row attaining
it is named — fourteen of them, on the lexicon register's `abstract_concrete`.
What it does **not** move is addressing: the table and the coordinate are the
names the question already gives.
[`studies/COLUMN_EXTREMUM_STUDY.md`](studies/COLUMN_EXTREMUM_STUDY.md) is the
study, `RequestProject/GLM/ColumnExtremum.lean` the proved half, and
[`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 53 the record.

The round before that was **maintenance**, and said so: under directive **D15**
it moved none of derivation, addressing or refusal. It finished the round
before it — which
had stopped with its counts re-taken in the working note but not written into
the documents, and with no release run — by re-taking eight counts the tree
quotes about itself, four of them measurements rather than tallies: the formal
development at 3,422 declarations, the relay's strict gain now holding across
the whole declared gate band with 19 queries carried and none lost, the
planner consulted on ten refusals rather than four, and the end-to-end set at
164 cases with 22 expected refusals. One unit was brittle rather than wrong —
it asserted that a two-digit sentinel never reaches the recorded totals, and
the suite reached 99 counted test files — and was fixed at the root. The
release then earned: **every test file of that suite and all 7 instruments**
signed with the exhaustive cases on. [`MASTER_PLAN.md`](MASTER_PLAN.md)
Phase 52 is the record.

The round before that **moved the target** too: under directive **D15** it
moved **derivation** and **refusal**. It took candidate 1 of §3.4 as it then
stood — the comparison a field surface
could not make — and built the operation that closes it: `ordering`, one
coordinate read off two rows and ordered exactly in rationals, or refused.
Four of seven declared comparisons are answered and three refused, every one
of the seven as declared before the run, and the refusals are the result
rather than the cost — two readings are comparable only on one scale, and
`GLM.CoordinateOrder.naive_order_is_not_scale_free` exhibits a positive
rescaling that flips the comparison of the bare numbers where
`order_scale_invariant` shows that no rescaling of a shared scale can. It
closes the last of the probe's ten held-and-unreachable questions: *is energy
more abstract than water?* is answered *energy*, by an exact `3/4`, on the
lexicon register's own scale and its own declared poles. What it does **not**
move is addressing, and the derivation it moves is one exact subtraction over
two addressed readings, which is the honest size of it.
[`studies/ORDERING_STUDY.md`](studies/ORDERING_STUDY.md) is the study,
`RequestProject/GLM/CoordinateOrder.lean` the twelve theorems, and
[`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 51 the record.

The round before it was **maintenance**, and said so: under directive **D15**
it moved none of derivation, addressing or refusal. It asked the release
question the round before it had left unasked, and repaired the six units that
failed it — the UBP source audit, which had no way to say that a float inside
the core was a *declared* site and now reads the declared list off the D11
inventory rather than loosening the check; the reasoning kernel's import
audit, told about the one integer-nanosecond timing; two counts of the tree
that had drifted; and two measurements that had moved with the corpus and were
re-taken. [`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 50 is the record.

The round before *that* took the four supplied *History Recorded in the Now*
studies seriously enough to decide them. Under directive **D15** it moved
**refusal**, on a declared task set: the supplied recipe answers all nine
history questions and is wrong on the four whose answer the receipt does not
determine, and the module answers five and refuses four, each refusal carrying
the pair of histories that share the receipt.
[`studies/NOW_RECEIPT_STUDY.md`](studies/NOW_RECEIPT_STUDY.md) is the study and
`RequestProject/GLM/NowReceipt.lean` the nine theorems; Phases 21–51 of
[`MASTER_PLAN.md`](MASTER_PLAN.md) are the rest of the record.

Last reconciled against a full re-run on 2026-09-21.

Every count below is produced by `overlay/glm_universal/figures.py` and written
to [`overlay/FIGURES.md`](overlay/FIGURES.md);
`overlay/glm_universal/tests/test_figures.py` fails if this document and the
code disagree. If a number here looks wrong, regenerate rather than edit:

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.figures --write
```

---

## 1. Where the work stands, in one table

| instrument | command | result |
|---|---|---|
| test suite | `python3 -m pytest glm_universal/tests -q` | **<!--figure:suite-->4,935 tests across 142 of the 143 test files, 17,993 subtests, outside the document check<!--/figure-->**, zero failures |
| end-to-end CLI evaluation | `python3 -m glm_universal.evaluation --jobs 8` | **<!--figure:evaluation-case-count-->177<!--/figure--> / <!--figure:evaluation-case-count-->177<!--/figure-->** — 149 answered, 28 refused as expected (all `boundary`, no `gap`), 0 unexpected refusals, 0 confidently wrong, 0 errored |
| benchmark suites | `python3 -m glm_universal.benchmarks` | **2,389 / 2,390** across 5 suites, every suite above its baseline |
| capability probes | `python3 -m glm_universal.capabilities` | 33 probes — 20 hold, 13 break, 0 errored, 0 surprises |
| Lean development | `lake build` (repository root) | <!--figure:lean-files-->168 Lean files<!--/figure-->, **0 `sorry`** |
| figures | `python3 -m glm_universal.figures --write` | regenerates `overlay/FIGURES.md`; every documented count |
| corpus | `python3 -m glm_universal.corpus --check` | the tier contract, the archive partition, the coverage claim of `ENTRY.md`, every generated block and every derived cache — **current**, no drift |
| construction ladder | `python3 -m glm_universal.tools ladder` | **462 / 568** queries named correctly with **0** wrong on the eleven-rung ladder, against **327** for the note's five rungs and **283** for the best single rung |
| norm-family ladder | `python3 -m glm_universal.tools normladder` | the repaired **<!--figure:normesc-rungs-->10<!--/figure-->**-rung norm ladder names **<!--figure:normesc-correct-->467<!--/figure-->** of **<!--figure:normesc-queries-->568<!--/figure-->** correctly with **<!--figure:normesc-wrong-->0<!--/figure-->** wrong; the full **<!--figure:normesc-family-rungs-->12<!--/figure-->**-rung family it repairs answers **<!--figure:normesc-family-wrong-->1<!--/figure-->** wrongly and is **not safe** |
| escalated operations | `python3 -m glm_universal.tools operations` | **<!--figure:opesc-count-->7<!--/figure-->** operations other than retrieval measured against substrate-removed controls; every one gains, and **one of them — program text — answers <!--figure:opesc-program-wrong-->13<!--/figure--> queries wrongly and is reported unsafe** |
| second reading | `python3 -m glm_universal.tools second-reading` | **<!--figure:secondread-adopted-->1<!--/figure-->** of **<!--figure:secondread-configurations-->6<!--/figure-->** declared guard configurations is adopted — `<!--figure:secondread-shipped-->strict+margin<!--/figure-->` takes the program-text operation to **<!--figure:secondread-program-correct-->366<!--/figure-->** correct and **<!--figure:secondread-program-wrong-->0<!--/figure-->** wrong, giving up **<!--figure:secondread-given-up-->150<!--/figure-->** answers where matched refusal removes **<!--figure:secondread-matched-removes-->2<!--/figure-->** of the thirteen |
| field surface | `python3 -m glm_universal.tools fieldsurface` | the surface answers **<!--figure:fieldsurface-moved-->9<!--/figure-->** of the **<!--figure:fieldsurface-held-->10<!--/figure-->** questions the oracle found held and unreachable — exactly the **<!--figure:fieldsurface-predicted-->9<!--/figure-->** declared reachable before the run — taking the probe from **<!--figure:fieldsurface-parsed-before-->6<!--/figure-->** parsed to **<!--figure:fieldsurface-parsed-after-->15<!--/figure-->**; it is `table`, not reasoning |
| ordering operation | `python3 -m glm_universal.tools ordering` | the operation answers **<!--figure:ordering-answered-->4<!--/figure-->** of the **<!--figure:ordering-declared-count-->7<!--/figure-->** comparisons declared before the run and refuses **<!--figure:ordering-refused-->3<!--/figure-->** under **<!--figure:ordering-reasons-->3<!--/figure-->** named reasons — **<!--figure:ordering-as-declared-->7<!--/figure-->** of **<!--figure:ordering-declared-count-->7<!--/figure-->** as declared — and closes the last held-and-unreachable probe question, taking it to **<!--figure:ordering-parsed-after-->16<!--/figure-->** parsed |
| typed planner | `python3 -m glm_universal.tools plans` | the frozen probe through the planner scores **<!--figure:plans-probe-correct-->19<!--/figure-->** correct, **<!--figure:plans-probe-wrong-->0<!--/figure-->** wrong, **<!--figure:plans-probe-refused-->1<!--/figure-->** refused; **<!--figure:plans-held-correct-->86<!--/figure-->** correct and **<!--figure:plans-held-correct-refusal-->22<!--/figure-->** correct refusals of **<!--figure:plans-held-total-->110<!--/figure-->** held-out questions with **<!--figure:plans-held-wrong-->1<!--/figure-->** wrong; the hostile stress set **<!--figure:plans-stress-wrong-->0<!--/figure-->** wrong |
| extremum operation | `python3 -m glm_universal.tools extremum` | the operation folds **<!--figure:extremum-answered-->4<!--/figure-->** of the **<!--figure:extremum-declared-count-->8<!--/figure-->** columns declared before the run and refuses **<!--figure:extremum-refused-->4<!--/figure-->** under all **<!--figure:extremum-reasons-->4<!--/figure-->** of its named reasons — **<!--figure:extremum-as-declared-->8<!--/figure-->** of **<!--figure:extremum-declared-count-->8<!--/figure-->** as declared — and reports **<!--figure:extremum-ties-->1<!--/figure-->** tie as a tie rather than resolving it |
| scale conversions | `python3 -m glm_universal.tools scales` | the declared table of **<!--figure:scales-rows-->9<!--/figure-->** scales over **<!--figure:scales-quantities-->4<!--/figure-->** quantities answers **<!--figure:scales-answered-->7<!--/figure-->** of the **<!--figure:scales-declared-->12<!--/figure-->** questions declared before the run and refuses **<!--figure:scales-refused-->5<!--/figure-->** — **<!--figure:scales-as-declared-->12<!--/figure-->** of **<!--figure:scales-declared-->12<!--/figure-->** as declared — and relates **<!--figure:scales-bridged-->6<!--/figure-->** of the **<!--figure:scales-pairs-->7,750<!--/figure-->** pairs of the **<!--figure:scales-numeric-->125<!--/figure-->** numeric scales, leaving every other pair refused |
| conversation layer | `python3 -m glm_universal.tools conversation` | the layer binds **<!--figure:conversation-answered-->8<!--/figure-->** of the **<!--figure:conversation-declared-count-->15<!--/figure-->** follow-ups declared before the run and refuses **<!--figure:conversation-refused-->7<!--/figure-->** under all **<!--figure:conversation-reasons-->3<!--/figure-->** of its named reasons — **<!--figure:conversation-as-declared-->15<!--/figure-->** of **<!--figure:conversation-declared-count-->15<!--/figure-->** as declared — against **<!--figure:conversation-alone-->0<!--/figure-->** answered by a session with no memory, and the recency control differs on **<!--figure:conversation-control-wrong-->3<!--/figure-->** of **<!--figure:conversation-control-rows-->10<!--/figure-->** |
| discourse state | `python3 -m glm_universal.tools discourse-state` | a tie carried as a column, the fourth shape and follow-ups on every surface: **7 / 7** column, **16 / 16** fourth-shape and **6 / 6** surface cases as declared, **0** wrong; Phase 55's layer gives 0 of the 20 new-behaviour cases as declared, the session alone 0 of the 5 surface answers; **15 / 15** of Phase 55's follow-ups hold but the 1 declared move; **32 / 32** column cells equal the answer asked alone; no answer to any of 3056 earlier strings changes; 8 of 8 marks met |
| role--filler binding | `python3 -m glm_universal.tools binding` | a typed relation written as one 24-bit word gives the filler's reading back with no side condition; naming the filler recovers **<!--figure:binding-recovered-->6<!--/figure-->** of the **<!--figure:binding-declared-count-->12<!--/figure-->** bindings declared before the run and refuses **<!--figure:binding-refused-->6<!--/figure-->** — **<!--figure:binding-as-declared-->12<!--/figure-->** of **<!--figure:binding-declared-count-->12<!--/figure-->** as declared — because only **<!--figure:binding-nameable-->424<!--/figure-->** of the **<!--figure:binding-carriers-->1,143<!--/figure-->** carriers read uniquely, the worst fibre holding **<!--figure:binding-largest-fibre-->136<!--/figure-->** |
| plan store | `python3 -m glm_universal.runtime.plan_store` | a resolved follow-up kept against a digest of the whole conversation replays **<!--figure:planstore-replayed-->15<!--/figure-->** of **<!--figure:planstore-declared-count-->15<!--/figure-->** unchanged, refusals included (**<!--figure:planstore-refusals-replayed-->7<!--/figure-->** of **<!--figure:planstore-refusals-->7<!--/figure-->**), taking the licensing trials from **<!--figure:planstore-trials-first-->27<!--/figure-->** to **<!--figure:planstore-trials-replayed-->0<!--/figure-->**; keyed by the follow-up text alone it answers **<!--figure:planstore-coarse-wrong-->8<!--/figure-->** of the fifteen with another conversation's antecedent |
| engineering surface | `python3 -m glm_universal.tools engineering` | on **63** engineering questions committed before the code: **53** correct, **10** correct refusals, **0** wrong (both existing paths: 0 correct, 53 refused); formula wheels **41 / 41** at SI7 and EXT10; Smith chart **16 / 16**; force-voltage analogy **9 / 9** laws each way; delta-sigma **6 / 6** |
| carried fork | `python3 -m glm_universal.tools carried-fork` | the six deep-hole candidates carried until a later decision: **0 wrong** from every certified stage; 592,268 of 658,812 declared-case reads answered (the 90 % mark missed at 32 cases), 4,224 / 4,224 second readings, 3,840 / 3,840 unsure-set reads; 1,771 / 1,771 ties lift to a certified A₁²⁴ Leech deep hole; the soft estimate right on 512 / 768 (mark missed) |
| second view | `python3 -m glm_universal.tools second-view` | one carrier read through the framed register's views: three views resolve **680,064 / 680,064** common-mode four-error reads, **0 wrong**; two views leave 174 of 10,626 bursts open, as predicted on every read; the composition with the declared cases **658,258 / 658,812**, 0 wrong, open as predicted; the Leech escalation on the views' soft reading equals the intersection on **46,728 / 46,728** reads; 7 of 9 marks met (V4, V8 not met) |
| unpacking and the third view on demand | `python3 -m glm_universal.tools unpacking` | argument unpacking in the dialect: Phase 96's refused program answered equal to CPython, **33 / 33** declared programs and refusals as declared (0 before), 0 of 311 earlier programs moved; the third view on demand gives the three-view answer on **680,064 / 680,064** reads with **1,371,264** views read instead of 2,040,192; independent faults, three views **84,480 / 84,480**, 0 wrong; 346 open second errors for every frame; 12 of 12 marks met |
| connected machine | `python3 -m glm_universal.tools connected` | one path (`GLM.py --ask`) to the toolbox, Python, engineering and the planner: **0** of 177 contract cases diverted; **136** more declared questions answered correctly than by the planner alone, **0** wrong added; **8 / 8** tools answer; wiring audit **0** of 96 reasoning modules unreached; across wheels, naive union **3** right / **158** wrong, licensed union **3** right / **0** wrong |
| reverse TCT | `python3 -m glm_universal.tools reverse-tct` | the language column generated from the mathematics: **176,617 / 176,617** battery terms round-trip, **0** collisions (infix control **5,684**); every declared `say`, `entails`, `solve`, `bounds`, `equivalent`, `negate` case as declared, **0** wrong; **94 / 94** column-3 scripts `VERIFIED True`, **69 / 69** mutated certificates rejected; the default path without the surface answers **0** of 58 |
| native parity | `python3 -m glm_universal.tools native-parity` | where a standard method ties a native one, the native one refined: the two-book native ranking **90** hits at 5 against **82** for the raw features (205 declaration queries) and **30** against **27** (103 goal queries), equal to the like-for-like standard and ahead of the raw features at every cut-off at the Phase 76 re-reading (N6 met again); the read-back scorer **24 / 24** controller tasks against **18**; read-back exact on **4,070 / 4,070** addresses |
| native words | `python3 -m glm_universal.tools native-words` | word overlap computed on Golay words of the tokens: the Golay names carry the token overlap exactly, and the native word ranking has **171** hits at 5 against **171** for the standard (205 declaration queries), **85** against **83** (103 goal queries) and **45** against **44** on the 60 document queries; 3 of 6 marks met at the Phase 76 re-reading (W2 missed by four declaration queries at k = 1 while level at 5 and ahead at 3 and 10, both tie-break draws missed), 4 of 6 at the Phase 74 re-reading, 5 of 6 at Phase 71's close (at the Phase 72 and 73 re-readings W4 missed by one query and W6 met, the reverse of Phase 71's close; at Phase 74's both tie-break draws are missed, by one query each) |
| reverse TCT, round two | `python3 -m glm_universal.tools reverse-tct --two` | the widened fragment, disjunction and the planner loop: **216,723 / 216,723** widened and **18,500 / 18,500** mask terms round-trip, **0** collisions; **36** of 83 dialect programs inside, **36** agree; **650 / 650** negated normal forms certified; every declared case as declared, **0** wrong; relay **20 / 20**, **32 / 32** handoffs agree or consistent, **0** disagree (verbatim control **0 / 15**); **92 / 92** scripts `VERIFIED True`, **84 / 84** mutants rejected |
| stepwise planner | `python3 -m glm_universal.tools stepwise` | the typed planner as the executive of a chain of steps: **30 / 30** composition cases, **21 / 21** goal cases, **6 / 6** narratives and **4 / 4** follow-ups as declared, **0** wrong (the planner alone answers 0 of the 30 compound cases); the first-found control answers the **3** cases the veto refuses; **43 / 43** chain scripts `VERIFIED`, **149 / 149** steps aligned, every mutation rejected; 8 of 8 marks met |
| stepwise planner, round three | `python3 -m glm_universal.tools stepwise-three` | declared comparatives, further count nouns, tera and pico, and folds over a column: **18 / 18** comparative, **6 / 6** count-noun, **6 / 6** prefix and **17 / 17** fold cases and **2 / 2** follow-ups as declared, **0** wrong (round two's reader answers 0 of the 47; the machine answered 6 before the round and 32 after); the present-rows control answers all **3** declared holes; the classes partition the column; **34 / 34** chain scripts `VERIFIED`, **327 / 327** steps aligned, every mutation rejected (member lie **13 / 13**, word lie **11 / 11**); rounds one and two unchanged; 8 of 8 marks met |
| stepwise planner, round five | `python3 -m glm_universal.tools stepwise-five` | frames generated from a declaration: **638 / 638** texts read alike by the generated and hand-written readers; **12 / 12** order, **12 / 12** superlative, **12 / 12** bound, **6 / 6** class, **6 / 6** prefix and **6 / 6** molecule cases and **2 / 2** follow-ups as declared, **0** wrong (round four's reader answers 0 of the 54; the machine answered 5 before the round and 41 after); **10 / 10** bounded answers sound and sharp over 200 completions; **41 / 41** chain scripts `VERIFIED`, **858 / 858** steps aligned, every mutation rejected; **3 / 3** declared moves; 9 of 9 marks met |
| stepwise planner, round two | `python3 -m glm_universal.tools stepwise-two` | *how many more*, parity, averages, givens with units and register values in the wheels: **21 / 21** frame, **18 / 18** unit and **14 / 14** register cases, **2 / 2** narratives and **2 / 2** follow-ups as declared, **0** wrong (round one's reader answers 0 of the 53); strip-the-units control wrong on **6** answered cases and answers **7** unit refusals; **39 / 39** chain scripts `VERIFIED`, **178 / 178** steps aligned, every mutation rejected (unit lie **22 / 22**); round one's corpus unchanged; 8 of 8 marks met |
| law register | `python3 -m glm_universal.tools law-register` | the 65 retained UBP laws re-read: the 16 exact rows **8** structural, **2** overclaimed, **3** definitional, **2** arithmetic, **1** near-miss, every structural row citing Lean; the decoder right exactly up to error weight 3 (refused at 4, wrong at 5), `LAW_STORAGE_HARDENED_001` refuted, refusal at a six-way tie withholding **5** wrong answers per right answer given up; of the 49 numeric rows **30** not predictions and **2** of **21** external formulas admitted by the look-elsewhere test; 9 of 9 marks met |
| law absorption | `python3 -m glm_universal.tools law-absorption` | each retained law tested and given a fate: **11** absorbed as computed substrate facts, **2** already GLM definitions, **3** retested and refused, **49** retired; **36 / 36** declared substrate questions through the typed planner as declared, **0** wrong (0 answered before the round); **0** of 4,687 existing evaluation texts read by the new frame; odd errors never refused, proved; 8 of 8 marks met |
| held precision | `python3 -m glm_universal.tools held-precision` | a register value's stated precision carried through a derivation: **4** of **35** goal and narrative chains read a register value and state the exact interval of their answer; since Phase 86 **0** exact because the held value cancels and **0** strictly wider (both earlier witnesses read a temperature level as a difference and are now refused); 4 of 5 marks met (H3 no longer) |
| measurand register | `python3 -m glm_universal.tools measurand-register` | register values read through their measurand, conversions through a stated efficiency, the elementary charge: **12 / 12** register, **14 / 14** conversion and **4 / 4** charge cases as declared, **0** wrong; the naive control answers **7** conversion cases, all wrongly; **18 / 18** chain scripts verified; 8 of 8 marks met |
| measurands | `python3 -m glm_universal.tools measurands` | kinds of quantity, temperature levels and differences, the SI's defining constants: **10 / 10** kind, **15 / 15** temperature and **6 / 6** constant cases as declared, **0** wrong; the dimension-only control answers all **5** kind mismatches; **5 / 5** amended earlier verdicts; rounds one to four held; **17 / 17** chain scripts `VERIFIED`, every mutation rejected; 7 of 7 marks met |
| integer decision | `python3 -m glm_universal.tools integer-decision` | the Omega test behind `INTEGER_UNDECIDED`: **22 / 22** declared questions as declared, **0** wrong (round three refused all 22); the declared battery **600 / 600** in agreement with enumeration, **0** undecided (round three **31**); **22 / 22** scripts `VERIFIED True`, **22 / 22** mutated Omega trees rejected; round three's corpus unchanged; 6 of 6 marks met |
| confidence floor | `python3 -m glm_universal.tools confidence-floor` | a declared grid of **7** thresholds hunted at **5** rates over an exact channel census: the working threshold **9999/10000** up to 1/50, **999/1000** at 1/20, **none** at 1/10 (there the graded answer, not a refusal); the promise `P(wrong \| answered) ≤ 1 − t` kept in **210 / 210** cells, and in **210 / 210** with the rate overdeclared (**30** broken underdeclared); **15 / 16** runtime programs as declared, one declaration wrong; **6 / 7** marks |
| blockers probe | `python3 -m glm_universal.tools blockers` | the pre-registered language probe scores **<!--figure:probe-correct-->2<!--/figure-->** correct, **<!--figure:probe-wrong-->1<!--/figure-->** wrong, **<!--figure:probe-refused-->17<!--/figure-->** refused of **<!--figure:probe-questions-->20<!--/figure-->** — **below the declared pass mark of <!--figure:probe-pass-mark-->10<!--/figure-->**, a declared failure |

The test-suite row is the sign-off ledger's own count, recorded by
`python3 -m glm_universal.signoff --release`, which runs each test file in its
own process with the `exhaustive` tests selected. One `pytest` process over the
same tree, with `GLM_EXHAUSTIVE=1` so that nothing is deselected, collects
**4,018 tests** — which is the ledger's 3,990 plus the 28 tests of the document
check the ledger's total leaves out, because a round that adds a document or a
figure fails that check until the documents are reconciled. Without that switch the `exhaustive`
tests — which certify rather than sample — are reported as skipped with their
reason rather than dropped silently, which is why the ledger's own count is
taken from a run that selects them.

The package is `glm_universal` **v1.23.0**: eleven sub-packages, 151 modules,
**8 registers** holding 1,143 carriers (physics 726, chemistry 118, molecules
51, mathematics 22, lexicon 149, spatial 28, harmonics 28, economics 21) beside
a 45-class comparison register, **<!--figure:query-kinds-->24 query kinds<!--/figure-->**
one of which dispatches **65 report subjects**, and 3 tasks.

---
## 2. What the system is now

This section is the **standing description**: what the machine is made of
today, with the thing that recomputes each part named beside it. It is
deliberately short. What each round *did* — the argument, the controls and the
negative results — is the record, and the record is in
[`MASTER_PLAN.md`](MASTER_PLAN.md) under *The delivered record*, phase by
phase, with the study for each finding in `studies/`.

**Substrate and algebra.** Complete syndrome decoding with no silent tie-break;
the full Leech lattice in place of Construction A (kissing number 196,560); the
exact 2A Sakuma product in place of the XOR shortcut; the six-facet orthogonal
decomposition with the lattice index that says what a facet reading loses; the
`LEGACY_TO_CORE` frame bridge, verified an isometry. The quantiser decodes
through the LLVQ class table rather than by scanning the code, on integers
scaled by a common denominator, which is exact and is what makes a whole-corpus
measurement affordable. Write-up:
[`LLVQ_TABLE_STUDY.md`](studies/LLVQ_TABLE_STUDY.md).

**The ladders it reads at.** The construction ladder — `Z²⁴`, `D₂₄`,
Construction `A`, `B` and `C`, all generated from their conditions, and the
scalings that fill the gap between them — is eleven rungs, and an escalated
reading over it names **462** of 568 declared queries correctly with **0**
wrong against **283** for the best single rung. Indexed instead by minimum
squared norm it becomes a family of
**<!--figure:normfamily-rung-count-->25<!--/figure-->** rungs over
**<!--figure:normfamily-norms-->12<!--/figure-->** norms with no power of two
missing; the full family is **not safe** — it answers
**<!--figure:normesc-family-wrong-->1<!--/figure-->** query wrongly — and the
repaired **<!--figure:normesc-rungs-->10<!--/figure-->**-rung ladder names
**<!--figure:normesc-correct-->467<!--/figure-->** of
**<!--figure:normesc-queries-->568<!--/figure-->** with
**<!--figure:normesc-wrong-->0<!--/figure-->** wrong. The containments are
proved in `RequestProject/GLM/NormFamily.lean`. Write-ups:
[`CONSTRUCTION_LADDER_STUDY.md`](studies/CONSTRUCTION_LADDER_STUDY.md),
[`NORM_FAMILY_STUDY.md`](studies/NORM_FAMILY_STUDY.md).

**Escalation, and the second reading that makes one operation safe.**
**<!--figure:opesc-count-->7<!--/figure-->** operations other than retrieval
are measured under the same discipline against substrate-removed controls;
every one gains, and one of them — program text — used to answer
**<!--figure:opesc-program-wrong-->13<!--/figure-->** queries wrongly. A second
reading at another layer removes all thirteen:
`<!--figure:secondread-shipped-->strict+margin<!--/figure-->`, the
**<!--figure:secondread-adopted-->1<!--/figure-->** of
**<!--figure:secondread-configurations-->6<!--/figure-->** declared
configurations that meets all four pre-registered marks, answers
**<!--figure:secondread-program-correct-->366<!--/figure-->** correctly and
**<!--figure:secondread-program-wrong-->0<!--/figure-->** wrongly, giving up
**<!--figure:secondread-given-up-->150<!--/figure-->** answers where matched
refusal removes only **<!--figure:secondread-matched-removes-->2<!--/figure-->**
of the thirteen. What the guards promise rather than score is proved in
`RequestProject/GLM/SecondReading.lean`. Write-ups:
[`OPERATION_ESCALATION_STUDY.md`](studies/OPERATION_ESCALATION_STUDY.md),
[`SECOND_READING_STUDY.md`](studies/SECOND_READING_STUDY.md).

**What blocks fuller reasoning, measured rather than asserted.** The
pre-registered language probe — **<!--figure:probe-questions-->20<!--/figure-->**
questions, pass mark **<!--figure:probe-pass-mark-->10<!--/figure-->** — scores
**<!--figure:probe-correct-->2<!--/figure-->** correct,
**<!--figure:probe-wrong-->1<!--/figure-->** wrong,
**<!--figure:probe-refused-->17<!--/figure-->** refused: a declared failure,
kept as one. Widening the lexicon to
**<!--figure:probe-lexicon-held-->57<!--/figure-->** of the probe's
**<!--figure:probe-lexicon-words-->69<!--/figure-->** content words moved the
score by nothing, so the binding blocker is the absence of a parser from open
language to a query kind, and only
**<!--figure:probe-derived-->2<!--/figure-->** measured results are derivation
rather than lookup or addressing. Write-up:
[`BLOCKERS_STUDY.md`](studies/BLOCKERS_STUDY.md).

**One question path, and the tools on it.** `runtime/router.py` gives a text
to the first surface of `runtime/toolbox.py`'s catalogue that reads it — the
toolbox (`tools`, `tool <name>`), reverse Three Column Thinking (a text that
starts with one of its operation prefixes), the Python dialect (a program whose loaded
names are all bound), the engineering surface (its eight frames), then the
typed planner — and `GLM.py --ask` prints the surface beside the answer. The
eight tools are the modules the wiring audit found unreached (`moonshine`,
`llvq`, `pcgs`, `salvage`, `salvage second`, `deep dive`, and `tie break` and
`stability` for one named Lean declaration). `-q` still reads through the
planner and the grammar. The engineering surface's eighth frame derives
*across wheels* over the union of the ten wheels, with a shared name one
variable only where a declared junction identifies it
(`engineering/union.py`). Recomputed by `tools connected`; proved in
`RequestProject/GLM/ConnectedMachine.lean`. Write-up:
[`CONNECTED_MACHINE_STUDY.md`](studies/CONNECTED_MACHINE_STUDY.md).

**Chains of steps, each step in three columns.** When the typed planner
refuses, the router hands the text to `runtime/stepwise.py`, which composes
planner answers (operator words, function forms, predicates, `then`), finds
unasked steps over the wheels (goal and narrative questions), refuses by name
where readings or derivations disagree, and remembers the chain for `then …`
and `why?` under a SHA-256 digest of the conversation. Each step is checked in
columns 1 and 2, and `reasoning/stepwise_script.py` writes one column-3 script
that re-derives every step in a fresh interpreter. `GLM.py --steps TEXT` asks
it directly; recomputed by `tools stepwise`; proved in
`RequestProject/GLM/StepwisePlanner.lean`. Write-up:
[`STEPWISE_PLANNER_STUDY.md`](studies/STEPWISE_PLANNER_STUDY.md). Since
Phase 73 its leaves also read *how many more … than*, *how much larger (higher,
lower) … than*, *is … odd / even* and *the average of …*, and its goal mode
reads givens and targets written with units — through the declared exact unit
table of `runtime/quantity_units.py`, dimension-checked and converted into SI
— and givens read from the register through the Phase 55 scale table;
recomputed by `tools stepwise-two`; proved in
`RequestProject/GLM/StepwiseFrames.lean`. Write-up:
[`STEPWISE_TWO_STUDY.md`](studies/STEPWISE_TWO_STUDY.md). Since Phase 84 it
also reads comparatives through the declared table of
`runtime/declared_frames.py` (*heavier*, *lighter*, *denser*, *older*,
*newer*), the count nouns *electrons* and *valence electrons*, the tera- and
pico- prefixes, and folds — a sum, a mean or a parity count — over every
element or a declared class, one looked-up step per member and a column with
a missing reading refused `COLUMN_HOLE`; recomputed by `tools
stepwise-three`; proved in `RequestProject/GLM/StepwiseWiden.lean`. Write-up:
[`STEPWISE_THREE_STUDY.md`](studies/STEPWISE_THREE_STUDY.md). Since Phase
85 it also reads the median, the largest and the smallest value and the rank
of a row over a declared set, answers a median or a rank over a column with
holes as the exact interval over every completion of the holes (one value
when it closes, `COLUMN_HOLE` when a side is open), and answers the
present-rows question asked as its own with the missing rows named;
recomputed by `tools stepwise-four`; proved in
`RequestProject/GLM/HoleBounds.lean`. Write-up:
[`HOLE_FOLDS_STUDY.md`](studies/HOLE_FOLDS_STUDY.md). Since Phase 86 it
checks kinds of quantity as well as dimensions (`runtime/measurands.py`):
a unit restricted by the SI to one kind is refused for another
(`KIND_MISMATCH`), a Celsius or Fahrenheit temperature is read as a level or a
difference by the law that reads it and the conflations are refused by name,
and the defining constants `h` and `c` are supplied only when the givens alone
derive nothing; recomputed by `tools measurands`; proved in
`RequestProject/GLM/MeasurandKinds.lean`. Write-up:
[`MEASURANDS_STUDY.md`](studies/MEASURANDS_STUDY.md). Since Phase 87 it reads
a register value through a declared register of measurands
(`runtime/measurand_register.py`): an ionization energy or an electron
affinity is read per atom as a photon's energy on wheel W10, a radius feeds
no wheel by name, a power crosses a motor, generator, pump or turbine only
through a stated efficiency in (0, 1] (`EFFICIENCY_OUT_OF_RANGE`,
`EFFICIENCY_UNDECLARED`), and the elementary charge and the percent are
exact units; recomputed by `tools measurand-register`; proved in
`RequestProject/GLM/MeasurandRegister.lean`. Write-up:
[`MEASURAND_REGISTER_STUDY.md`](studies/MEASURAND_REGISTER_STUDY.md). Since
Phase 91 its fold frames are generated from one declaration
(`runtime/frame_declarations.py`) rather than written by hand, and the
widenings are entries in it: the `k`-th largest and smallest value and the
quartiles over a declared set, superlatives and the top `k`, *the bounds on* a
sum, a mean (through a declared physical range) or a parity count under holes,
the present-rows parity count, *the metals* and *the rare earths*, the twelve
remaining exact SI prefixes and *heavier*/*lighter* over the molecule table,
refusing `ORDER_OUT_OF_RANGE`, `TOP_K_TIE`, `RANGE_UNDECLARED`,
`TABLE_MISMATCH` and `COMPARATIVE_UNDECLARED`; recomputed by `tools
stepwise-five`; proved in `RequestProject/GLM/DeclaredFrames.lean`. Write-up:
[`DECLARED_FRAMES_STUDY.md`](studies/DECLARED_FRAMES_STUDY.md).

**The loop through the planner.** Since Phase 88 the Python dialect calls
the rest of the machine: `derive`, `ask` and `solve` return exact values from
the stepwise planner's goal mode, one stepwise question and the reverse
surface's linear solve (`runtime/planner_bridge.py`, builtins in
`reasoning/python_speech.py`), refusing `BRIDGE_UNAVAILABLE`,
`DERIVE_REFUSED`, `ASK_REFUSED` or `SOLVE_REFUSED`; a declared frame hands a
question about a Python expression to the evaluator; the router's Python
surface and `GLM.py` speak through it. The column-3 script re-runs each
sub-answer's own script, checks the value against its record and re-runs the
program under CPython against the checked table; recomputed by `tools
planner-loop`; proved in `RequestProject/GLM/PlannerLoop.lean`. Write-up:
[`PLANNER_LOOP_STUDY.md`](studies/PLANNER_LOOP_STUDY.md).

**The law register.** `reasoning/law_register.py` re-reads the 65 laws an
older GLM-lens review of the UBP knowledge base retained, frozen as
`reasoning/_data/law_register_65.csv`. Structural laws are cited to their Lean
theorems; the decoder's behaviour at every error weight is tabulated exactly
from the coset weight enumerators (right up to weight 3, refused at 4, wrong at
5, mixed above), with exact probabilities at any bit-flip rate and the price of
refusing at a six-way tie; and `look_elsewhere` is a refusal test for any
claimed numeric coincidence — the chance that the claim's own template, its
small integers varied over declared ranges, hits a target in `[T/2, 2T]` as
closely. `admit(law_id)` gives a verdict with its reason. Recomputed by
`tools law-register`; toolbox tool `law register`; proved in
`RequestProject/GLM/LawRegister.lean`. Write-up:
[`LAW_REGISTER_STUDY.md`](studies/LAW_REGISTER_STUDY.md).

**The laws absorbed.** `reasoning/law_absorption.py` gives each retained law
a fate — absorbed, already GLM, retested, retired — with its reason, and
computes the absorbed ones live from the substrate (`FACTS`): the code's
size, rate, weight counts, minimum distance and covering radius, the
decoder's outcome and exact probability at an error weight or noise rate, the
confidence of a decoding at a distance, the kissing number, XOR closure and
descent. The typed planner reaches them through the `substrate` frame of
`runtime/semantic_plan.py`, and every answer cites the law it was absorbed
from. Recomputed by `tools law-absorption`; proved in
`RequestProject/GLM/LawAbsorption.lean`. Write-up:
[`LAW_ABSORPTION_STUDY.md`](studies/LAW_ABSORPTION_STUDY.md).

**Held precision.** `reasoning/held_precision.py` writes the answer of a goal
or narrative chain as one monomial in its leaves, reads each register lookup
at the precision it was written to, and states the answer's exact interval
(attained at two corners of the box) as a note on the chain; a leaf whose
exponent is 0 has cancelled and the answer is stated as exact. Recomputed by
`tools held-precision`; proved in `RequestProject/GLM/HeldPrecision.lean`.
Write-up: [`HELD_PRECISION_STUDY.md`](studies/HELD_PRECISION_STUDY.md).

**Decoder confidence.** `reasoning/decoder_confidence.py` attaches the
absorbed confidence law to the decoder's own readings at a declared bit-flip
rate: the complete decoder's answer with its posterior (`TIE` at a deep hole),
the carried fork pruned to declared cases with the survivor's posterior under
the closed world, and the second reading's agreed codeword with the posterior
of the product of the reads' likelihoods — reached in the Python dialect as
`decode_confidence` and `agree_confidence`. Recomputed by
`tools decoder-confidence`; proved in
`RequestProject/GLM/DecoderConfidence.lean`. Write-up:
[`DECODER_CONFIDENCE_STUDY.md`](studies/DECODER_CONFIDENCE_STUDY.md).

**Confidence floor.** `reasoning/confidence_floor.py` gives `resolve` and
`agree` two readings at a declared bit-flip rate: the graded answer — the
value with its exact confidence and a band word (*near-certain*, *confident*,
*probable*, *uncertain*), never refused on confidence — and the floor, which
answers only at or above a declared confidence and otherwise refuses
`BELOW_FLOOR`, naming the confidence it had. Reached in the Python dialect as
`resolve_at`, `agree_at`, `resolve_floor` and `agree_floor`.
`reasoning/confidence_floor_marks.py` holds the exact channel census of the
decoder and the context stage and the hunt over a declared grid of rates and
thresholds. Recomputed by `tools confidence-floor`; proved in
`RequestProject/GLM/ConfidenceFloor.lean`. Write-up:
[`CONFIDENCE_FLOOR_STUDY.md`](studies/CONFIDENCE_FLOOR_STUDY.md).

**The second reading's channel.** `reasoning/agree_channel_marks.py` holds an
exact census of every pair of reads of one carrier, reduced by verified code
automorphisms to 28 rate-independent histograms, and places `agree` in the
confidence-floor hunt (working threshold 999/1000 at 1/10). Recomputed by
`tools agree-channel`; proved in `RequestProject/GLM/Agree.lean`. Write-up:
[`AGREE_CHANNEL_STUDY.md`](studies/AGREE_CHANNEL_STUDY.md).

**The rate from the reads.** `reasoning/rate_posterior.py` estimates the
bit-flip rate from the reads — an exact posterior over a declared grid with a
guard point — and answers with a confidence marginalized over it, refusing
`RATE_GRID_EXCEEDED` when the reads lean above the grid; the dialect reaches
it as `decode_soft`, `decode_soft_floor` and `agree_soft`.
`reasoning/rate_posterior_marks.py` measures its operating characteristics
exactly over every count vector. Recomputed by `tools rate-posterior`; proved
in `RequestProject/GLM/RatePosterior.lean`. Write-up:
[`RATE_POSTERIOR_STUDY.md`](studies/RATE_POSTERIOR_STUDY.md).

**The framed register.** `reasoning/second_view.py` stores a codeword in
views rotated by `0, 1, 3` and reads it by carrying the fork of view 0 and
pruning it by every further view, so a second reading of one carrier is
produced by the runtime itself; three views resolve every common-mode
four-error burst. The dialect reaches it as `store_views` and `read_views`.
Recomputed by `tools second-view`; proved in
`RequestProject/GLM/SecondView.lean`. Write-up:
[`SECOND_VIEW_STUDY.md`](studies/SECOND_VIEW_STUDY.md).

**The third view on demand, and argument unpacking.** `read_on_demand`
reads a framed register's first two views and the third only while the fork
is open: the three-view answer on every read inside the fault model, for
about two views a read; outside it, it answers where two views answer, so
the caller chooses it only where the fault model is trusted. The Python
dialect admits argument unpacking, `f(*xs)` and `def f(a, *rest)`, each a
named step re-derived in column 3. Recomputed by `tools unpacking`; proved
in `RequestProject/GLM/OnDemandView.lean`. Write-up:
[`UNPACKING_RESCORE_STUDY.md`](studies/UNPACKING_RESCORE_STUDY.md).

**The unresolved laws, triaged.** `reasoning/law_triage.py` gives each of the
106 `UNRESOLVED-UBP` knowledge-base laws one fate under a service rule (0
absorbed, 3 already served, 3 refuted, 100 retired with a reason). A record,
not consulted at run time. Recomputed by `tools law-triage`. Write-up:
[`LAW_TRIAGE_STUDY.md`](studies/LAW_TRIAGE_STUDY.md).

**Reverse Three Column Thinking.** `reasoning/reverse_tct.py` runs Three
Column Thinking backwards: the mathematics (column 2), given directly or read
off dialect source (column 3), generates the language column through a
declared prefix-first grammar (`the sum of A and B`), and a declared reader
parses the sentence back, so column 1 carries exactly the information of
column 2. Operations taken on the mathematics come back as sentences with
certificates: `say`, `equivalent`, `paraphrase`, `negate`, `solve for x`,
`entails` (Fourier–Motzkin with Farkas multipliers over ℚ, or two witness
points) and `bounds of x`. The router reads them by their prefix (`GLM.py
--ask "say: 2 * x + 3 == 7"`), and `GLM.py --reverse` prints the three
columns; `reasoning/reverse_tct_script.py` writes the column-3 script that
re-reads column 1 and re-checks the certificate. Recomputed by `tools
reverse-tct`; proved in `RequestProject/GLM/ReverseTCT.lean`. Write-up:
[`REVERSE_TCT_STUDY.md`](studies/REVERSE_TCT_STUDY.md).
Since round two the grammar also speaks the integer layer (`the floor
quotient of`, `the remainder of`, `the absolute value of`, `the minimum of`,
`the maximum of`, negative exponents), the bitwise operators and shifts, and
Golay masks as a second sort (`the mask of three positions one, two, three`,
the set operators, `the size of`, `is in`, `is contained in`); a statement is a
conjunction of clauses (`either A, or B, and C`), so `negate` answers any
statement by De Morgan followed by a meaning-preserving simplification;
`entails`, `bounds` and `equivalent` split disjunctions and `abs`, `min`,
`max` into cases. `relay: Q` (`runtime/reverse_relay.py`) answers Q, hands its
values and relations to the planner as questions in the planner's own input
language (`approximate v to 20 places`, `what fraction rounds to R`, `is a
less than b`), reads each answer back into column 2 (`AGREES`, `CONSISTENT`,
`DISAGREES`, `UNREAD`) and realises it as sentences of the reverse grammar,
which the column-3 script re-checks. Recomputed by `tools reverse-tct --two`;
proved in `RequestProject/GLM/ReverseTCTTwo.lean`. Since Phase 94 the
grammar has a third sort — strings, tuples and ranges with count-first
literals (`reasoning/reverse_tct_seq.py`, `tools third-sort`,
`RequestProject/GLM/ThirdSort.lean`) — and since Phase 95 an imperative
grammar for programs with state (`reasoning/reverse_tct_imp.py`: assignment,
loops, branches, functions and `match`, run with counted steps and bounded
depth, a trace of assignments in column 1 replayed by the script; `tools
imperative`, `RequestProject/GLM/ImperativeGrammar.lean`). Write-ups:
[`THIRD_SORT_STUDY.md`](studies/THIRD_SORT_STUDY.md),
[`IMPERATIVE_GRAMMAR_STUDY.md`](studies/IMPERATIVE_GRAMMAR_STUDY.md).

**A conversation, and what a reference costs.** `runtime/conversation.py` puts
an episodic register of turns in front of the session, so that a turn may
refer back to an earlier one. Three declared shapes are follow-ups and nothing
else is — a pronoun (*describe it*), an end-flip (*and the smallest?*) and a
subject substitution (*and oxygen?*) — and a candidate antecedent is
**licensed** exactly when the query it produces solves, so the reference is
decided by what the registers hold. Recency decides between turns, licensing
within one, and where the deciding side offers two licensed candidates the
layer refuses rather than choosing: the fourteen rows tied at the top of the
lexicon's `abstract_concrete` column give *describe it* fourteen equally good
referents. It binds **<!--figure:conversation-answered-->8<!--/figure-->** of
**<!--figure:conversation-declared-count-->15<!--/figure-->** declared
follow-ups and refuses **<!--figure:conversation-refused-->7<!--/figure-->**,
all **<!--figure:conversation-as-declared-->15<!--/figure-->** as declared,
where a session with no memory answers
**<!--figure:conversation-alone-->0<!--/figure-->**. No answer is new: every
rewritten query is answered by the solver that would have answered it written
out in full. Proved in `RequestProject/GLM/Conversation.lean`. Write-up:
[`CONVERSATION_STUDY.md`](studies/CONVERSATION_STUDY.md). Since Phase 92
`runtime/discourse.py` carries the state further: a fold's tie is a set the
turn produced and *it* names it, answered as a column of the rows' own
answers (`column-incomplete` under a hole); *the one before that*, *them*,
*both of them* (`number-mismatch`) and *why?* are read; the router is the
licence, so a follow-up any surface answers is bound; and `GLM.py --converse`
holds the conversation over every surface; recomputed by `tools
discourse-state`; proved in `RequestProject/GLM/DiscourseState.lean`.
Write-up: [`DISCOURSE_STATE_STUDY.md`](studies/DISCOURSE_STATE_STUDY.md).

**A relation written as one word, and a resolved follow-up kept.**
`reasoning/role_binding.py` writes a typed relation *R(A, B)* into a single
24-bit word by exclusive-or over parity readings, the role carried by a
permutation of the coordinates rather than by a carrier. Unbinding returns the
filler's reading with **no side condition** — proved in
`RequestProject/GLM/RoleBinding.lean` — and turning that reading into a *name*
is worth exactly what the registers are worth:
**<!--figure:binding-nameable-->424<!--/figure-->** of the
**<!--figure:binding-carriers-->1,143<!--/figure-->** carriers read uniquely
and the other **<!--figure:binding-ambiguous-->719<!--/figure-->** force a
refusal, the largest fibre holding
**<!--figure:binding-largest-fibre-->136<!--/figure-->** physics carriers at
all-zero parity. The product binding the same material offers beside it is
**refuted**: one zero coordinate makes two fillers bind alike, and
**<!--figure:binding-product-zero-->1,133<!--/figure-->** of the carriers read
zero somewhere. Beside it, `runtime/plan_store.py` keeps a resolved follow-up
— refusals exactly as bindings — under a digest of the whole conversation it
was resolved in, and `Conversation` takes one as an optional `store=`: all
**<!--figure:planstore-replayed-->15<!--/figure-->** declared follow-ups replay
unchanged and the licensing trials fall from
**<!--figure:planstore-trials-first-->27<!--/figure-->** to
**<!--figure:planstore-trials-replayed-->0<!--/figure-->**. Proved in
`RequestProject/GLM/PlanStore.lean`. Write-up:
[`SUPPLIED_PORTS_STUDY.md`](studies/SUPPLIED_PORTS_STUDY.md).

**Frames that derive, with a certificate.** The typed planner, the default
reading of every command-line question since Phase 63, carries frames whose
answers no register holds, each checked by `reasoning/certificates.py`:
Bézout, linear Diophantine equations and bounded factorisation (Phase 62);
consistency of a register value with a quoted value or the declared standard,
read at the precision each is held to, with an ordering between overlapping
readings refused; the simplest fraction a decimal pins down, answered only
when every rival's denominator is at least twice the answer's; and dimensional
equations solved exactly, with a certificate for unique, impossible and
undetermined. `python3 -m glm_universal.tools cognition` runs every experiment
of the study; the certificates are proved in
`RequestProject/GLM/CognitionRoundTwo.lean`. Write-up:
[`SUBSTRATE_NATIVE_COGNITION_STUDY.md`](studies/SUBSTRATE_NATIVE_COGNITION_STUDY.md).

**Python, spoken exactly.** `GLM.py --python SOURCE` evaluates a declared
dialect of Python — `int`, `Fraction`, `bool`, `str` with slicing, tuples of
up to 24 items, frozensets of coordinates `0..23`, `range`, pure functions,
loops and `match` — on the substrate, and answers with three columns whose
third is a script run in a fresh `python3 -I`; floats, non-deterministic
calls, deep-hole ties, uncorrectable distances and cross-scale comparisons are
named refusals. `python3 -m glm_universal.tools python-speech` re-takes the
measurement; the substrate operations are proved in
`RequestProject/GLM/PythonSpeech.lean`. Write-up:
[`PYTHON_SPEECH_STUDY.md`](studies/PYTHON_SPEECH_STUDY.md).

**Question frames, for questions written outside the project.**
`runtime/question_frames.py` holds declared frames that read a question as
written by someone else — a Routh range, a per-unit rebase, a reflection
coefficient, an aliasing fold, an entropy, a Huffman code, a water-filling
allocation, a Golay coset question, and the Set B items — and each answer is
re-derived by its own column-3 script before it is printed. `GLM.py -q` goes
through the multi-surface router (`--plan` keeps the typed planner's path).
The plain readings print their confidence under the production contract of
the 4-way matrix: the upper-credible rate rule over the session's reads
(`reasoning/contract_matrix.py`, `rate_posterior.PRODUCTION_RULE`).
Recomputed by `tools question-set-b` and `tools contract-matrix`. Write-ups:
[`QUESTION_SET_B_STUDY.md`](studies/QUESTION_SET_B_STUDY.md),
[`CONTRACT_MATRIX_STUDY.md`](studies/CONTRACT_MATRIX_STUDY.md).

**Registers.** Eight of them. Physics (726 quantities, EXT10 exponents and
unit strings cross-checked against each other), chemistry (118 elements),
molecules (51 species and ions, every coordinate derived from the element
register at load time), mathematics, lexicon (95 concepts, 380 explicit
relation triples), spatial, harmonics (28 musical intervals as exact rational
frequency ratios) and economics (21 quoted prices as exact rationals), beside
a 45-class comparison register.

**Reasoning.** 80 modules. Analogy by named relation, dimensional
verification, Buckingham-Pi from an exact rational nullspace, the
Walsh–Hadamard transform decoder, the deep-hole walk, term arithmetic, unit
parsing with the steradian priced rather than silently redefined, and
element-coverage widening that labels every widened cell by provenance.

**Values.** Reals held as processes with no float anywhere; written arithmetic
over them including `exp`, `log`, `sin`, `cos`, `tan` and real powers; decided
inequality and refused equality; the delta–sigma modulator with its proved
`1/N` rate and, in 24 coordinates, the separating functional that proves a
target outside the hull unreachable.

**Meaning.** The grounded graph — 357 meanings, 1,705 notations, 12,859 edges,
every one re-derived on demand. The inherited ARC-era concept graph was
audited and demoted to evidence, and `tests/test_inherited_graph.py` enforces
that by walking the imports of every module that answers a question.

**Measurement.** Three instruments that do not trust each other: probes
(library boundaries), benchmarks (solver functions) and the end-to-end
evaluation (the CLI in a fresh interpreter per question, scored asymmetrically
so a confident wrong answer is worse than a refusal). Write-up:
[`CAPABILITY_ASSESSMENT.md`](CAPABILITY_ASSESSMENT.md).

**The Lean development, addressed.** `reasoning/lean_address.py` gives each of
the 4539 declarations a deterministic Leech address computed from 24 structural
counts of its statement. Read back exactly 4539/4539 with 0 coordinate errors;
3989 distinct addresses, and the quantiser adds no conflation of its own;
nearest-by-address shares a file 817 times against 35 for a SHA-256 control and
29 for a seeded reshuffle, with chance at ≈ 0.80 %. `report lean`.
Write-up: [`LEAN_ADDRESS_STUDY.md`](studies/LEAN_ADDRESS_STUDY.md).

**The register where the address is the only reader.** In the anonymous
register a query's identifiers are not the corpus's, by theorem
(`GLM.Anonymous.overlap_anonymise_eq_zero`): over 883 queries the text search
falls 767 → 85 and the identifier address book 413 → 46 against 49 by chance,
where the structural address holds 258 → 182. Write-up:
[`ANONYMOUS_REGISTER_STUDY.md`](studies/ANONYMOUS_REGISTER_STUDY.md).

**The standing rules, as instruments.**
[`PROJECT_DIRECTIVES.md`](PROJECT_DIRECTIVES.md) states <!--figure:directives-->16 standing rules<!--/figure--> and
names the instrument for each. `reasoning/directives.py` parses that file and
gives each instrument a live verdict (`report directives`) — **16 of 16** with
every named instrument present; `reasoning/pipeline.py` reads the stage each
piece of work has reached off the tree rather than from prose — **30 of 30
rows** through all six stages (`report pipeline`); `glm_universal/signoff/`
computes a module's dependency closure with `ast` and plans a run against
recorded digests, so nothing unchanged is checked twice (§4.1); and
`glm_universal/integrity.py` holds every SHA-256 use one module above the six
core sub-packages, which the purity audit enforces. `glm_universal/tools.py`
is their command line, kept out of the core for the same reason.

**What a refusal is evidence of.** `reasoning/probe_oracle.py` translates each
of the twenty pre-registered probe questions into the query grammar by hand
and classifies it: `parsed` when a query already answers it at a declared
field, `surface` when a register row or a shipped function holds the answer
and no query kind returns it, `absent` when nothing holds it. The split is
<!--figure:oracle-parsed-->6<!--/figure--> /
<!--figure:oracle-surface-->10<!--/figure--> /
<!--figure:oracle-absent-->4<!--/figure--> of
<!--figure:oracle-questions-->20<!--/figure-->. It keeps no measurement cache
— a live session answers twenty queries in seconds — and
`GLM.ProbeOracle.counts_partition` is why the three counts read the same
twenty questions rather than three samples. `tools oracle`. Write-up:
[`PROBE_ORACLE_STUDY.md`](studies/PROBE_ORACLE_STUDY.md).

**The field surface, and what it was worth.** `runtime/fields.py` answers one
named field of one named row — `field atomic_weight_u of carbon` — over
<!--figure:fieldsurface-tables-->13<!--/figure--> declared tables holding
<!--figure:fieldsurface-rows-->11,345<!--/figure--> rows and
<!--figure:fieldsurface-pairs-->66,982<!--/figure--> addressable `(row,
field)` pairs: the element and molecule source rows, one table per register's
carrier attributes, the Lean address book, the package's own top-level
definitions, and a registry of declared zero-argument functions whose returned
mapping is addressable by key. Its second shape, `fields of <row>`, names the
fields a row answers to. It refuses at three boundaries — an unknown row, an
unknown field of a known row, and a field the register records as missing —
and it says of itself, in every answer, that it is `table`: it derives
nothing. Measured against the oracle's prediction it answers
<!--figure:fieldsurface-moved-->9<!--/figure--> of the
<!--figure:fieldsurface-held-->10<!--/figure--> held-and-unreachable
questions, which is exactly the <!--figure:fieldsurface-predicted-->9<!--/figure-->
declared reachable before the run, taking the probe from
<!--figure:fieldsurface-parsed-before-->6<!--/figure--> parsed to
<!--figure:fieldsurface-parsed-after-->15<!--/figure-->; the tenth is a
comparison across two rows and needs an operation rather than a surface.
`GLM.FieldSurface` proves the boundary is the tables' rather than a search's.
`tools fieldsurface`. Write-up:
[`FIELD_SURFACE_STUDY.md`](studies/FIELD_SURFACE_STUDY.md).

**The ordering operation, and the refusal it is built around.**
`reasoning/coordinate_order.py` reads one coordinate off *two* rows through
the field surface and orders them exactly in rationals — `order
abstract_concrete of energy and water`, the `ordering` query kind. Each side
is a *reading*: a value together with the scale it was read on, `table:field`,
and a coordinate held inside a mapping field — which is how the lexicon
register keeps its ten semantic primitives — is read as a coordinate of that
field. It refuses in <!--figure:ordering-reasons-->3<!--/figure--> named ways:
a coordinate the row does not hold, a reading that is a label rather than a
quantity, and two readings on different scales. The last is the point of it,
and it is proved rather than asserted:
`GLM.CoordinateOrder.naive_order_is_not_scale_free` exhibits a positive
rescaling that flips the comparison of two raw numbers, while
`order_scale_invariant` shows that no rescaling of a shared scale can.
Measured on <!--figure:ordering-declared-count-->7<!--/figure--> comparisons
declared before the run it answers <!--figure:ordering-answered-->4<!--/figure-->
and refuses <!--figure:ordering-refused-->3<!--/figure-->, every one as
declared, and it closes the one probe question the field surface named as
unreachable — all <!--figure:ordering-held-->10<!--/figure-->
held-and-unreachable questions are now parsed. `tools ordering`. Write-up:
[`ORDERING_STUDY.md`](studies/ORDERING_STUDY.md).

**The column, not the pair.** The `extremum` query kind reads one coordinate
off **every** row of one declared table and returns the end of it, or refuses.
The end is read off the word that opens the question — `largest`, `highest`,
`maximum` against `smallest`, `lowest`, `minimum` — and every row attaining it
is named rather than one of them picked: fourteen of the lexicon register's
rows sit at the concrete end of `abstract_concrete`, and choosing between them
would be a choice the register does not make. It refuses in
<!--figure:extremum-reasons-->4<!--/figure--> named ways, two of them boundaries
the system had no way to state before. A column with a hole in it has no
extremum — 23 of the element register's 118 rows record
`electronegativity_pauling` as missing, and
`GLM.ColumnExtremum.extremum_over_present_is_not_the_extremum` exhibits a
column where the extremum over the rows that are filled in is a different value
at a different row, so an answer over the present rows is wrong rather than
partial. A column gathered from two scales is not one column, which is the
ordering operation's `different-scale` one level up, and
`extremum_not_invariant_under_one_row_rescaling` is why. Measured on
<!--figure:extremum-declared-count-->8<!--/figure--> columns declared before the
run it folds <!--figure:extremum-answered-->4<!--/figure--> and refuses
<!--figure:extremum-refused-->4<!--/figure-->, every one as declared.
`tools extremum`. Write-up:
[`COLUMN_EXTREMUM_STUDY.md`](studies/COLUMN_EXTREMUM_STUDY.md).

**The scales, written down.** `reasoning/scale_conversion.py` holds the
declared table the two operations above did not have: one row per scale,
naming the quantity it measures, the canonical unit of that quantity and the
exact positive-affine map into it, together with the source the numbers came
from. <!--figure:scales-rows-->9<!--/figure--> rows over
<!--figure:scales-quantities-->4<!--/figure--> quantities — mass in `u`, molar
energy in `kJ·mol⁻¹`, temperature in `K`, length in `pm`. The ordering
operation consults it when the two readings are on different scales and the
extremum operation when a column is gathered by quantity rather than by table,
so `largest mass` now folds the element rows and the molecule rows together;
neither gains an answer anywhere the table is silent, and
`GLM.ScaleConversion.orderWith_conservative` is that stated rather than
hoped. That a conversion may be composed into a comparison at all is
`cmpQ_apply` and `order_conversion_invariant`; that the declaration and not
the code is what licenses a bridge is `the_table_carries_the_claim`; the two
things it must not do are `negative_factor_flips_the_verdict` and
`raw_gather_names_the_wrong_row`. Measured on
<!--figure:scales-declared-->12<!--/figure--> questions declared before the run
it answers <!--figure:scales-answered-->7<!--/figure--> and refuses
<!--figure:scales-refused-->5<!--/figure-->, every one as declared, and across
the whole field surface it relates
<!--figure:scales-bridged-->6<!--/figure--> of
<!--figure:scales-pairs-->7,750<!--/figure--> pairs of
<!--figure:scales-numeric-->125<!--/figure--> numeric scales — the rest stay
refused, which is what *declared* costs. `tools scales`. Write-up:
[`SCALE_CONVERSION_STUDY.md`](studies/SCALE_CONVERSION_STUDY.md).

**Typed question plans.** `runtime/semantic_plan.py` is the bridge from an
English question to the operations the session already has:
**<!--figure:plans-frames-->20<!--/figure-->** frames, each of which reads one
shape of question into a plan whose slots are grounded against the field
surface and the row's own fields, run, and accepted only when every licensed
plan agrees; with none licensed the answer is the grammar's own. Two frames
compute — exact integer arithmetic, and conversion over a declared table of
**<!--figure:plans-units-->17<!--/figure-->** units whose factors are
definitions. Reached with `GLM.py --plan` or
`GeometricSession.ask_planned`; measured by `tools plans` on the frozen probe
and four sets in `evaluation/heldout.py`, three of them committed before the
planner existed. Proved in `RequestProject/GLM/SemanticPlan.lean`. Write-up:
[`SEMANTIC_PLAN_STUDY.md`](studies/SEMANTIC_PLAN_STUDY.md).

**The round loop itself, measured and cut.** A named `.lean` file resolves to
itself rather than to the whole development, so a median Lean file makes **26**
units stale rather than 84 of 97, and a unit's closure is **116** files rather
than 332. On top of that, a documents check no longer recomputes a stale
derived artefact: it names the artefact and the refresh that rebuilds it, so
`corpus --check` is a matter of seconds whatever else has moved, and the
minutes are paid once by `corpus --refresh`. Write-up:
[`ITERATION_COST_STUDY.md`](studies/ITERATION_COST_STUDY.md) §5a and §5b.

---

## 3. What is open

This is the whole list. Nothing else in the repository is claimed as pending.

### 3.1 The evaluation finds no gap

The end-to-end set is **177 of 177** and every one of its twenty-eight refusals is a
`boundary` — a theorem or a stated commitment — rather than a `gap`. What
remains open is listed below, and none of it is a question the evaluation set
asks.

### 3.2 Named as untouched — all closed, and what each closure left

Every item that used to stand on this list is closed; each is recorded in
[`MASTER_PLAN.md`](MASTER_PLAN.md) with the study that closed it. What the
closures left behind is §3.4.

* **The infinite-dimensional half of the VOA bridge.** `VOA.lean` builds the
  state–field map at the Griess layer (the partial 2A axial algebra on axes) and shows where a finite model stops
  (`borcherds_commutator_fails`); `Heisenberg.lean` builds the Fock space of
  one free boson and proves `no_finite_dimensional_model`.
* **`heat : temperature :: force : ?`** — closed by the energy-conjugate
  register, with the four criteria a transportable relation must meet
  ([`CONJUGATE_STUDY.md`](studies/CONJUGATE_STUDY.md)).
* **The `O(1)` LLVQ table** — built and on the hot path, with the claim
  narrowed to *constant-bounded* and measured rather than asserted.
* **The Niemeier deep-hole census** — the trajectory distribution classifies
  (**40 of 44** at the escalated reading, **10 of 10** labels kept under a
  change of seed); what it does not do is certify, which is §3.4 item 1a
  ([`DEEP_HOLE_STUDY.md`](studies/DEEP_HOLE_STUDY.md),
  [`DEEP_HOLE_ESCALATION_STUDY.md`](studies/DEEP_HOLE_ESCALATION_STUDY.md)).
* **Open vocabulary** — closed as a mechanism: a name is admissible exactly
  when a stated route gives it coordinates computed from a register the machine
  already checks, and *justice* is refused by a condition it names rather than
  by kind ([`ADMISSION_STUDY.md`](studies/ADMISSION_STUDY.md)).
* **Words as projections** — closed for all twelve lexicon adjectives and for
  the comparative; what is open is data, which
  `replacement_witness()` keeps measured
  ([`RELATIVE_MEASURE_STUDY.md`](studies/RELATIVE_MEASURE_STUDY.md)).
* **The geometric items** — sigma–delta on the Leech shells, the 32- and
  48-dimensional lattices, the harmonic register and the economic register are
  all built, the last two with the honest verdict `not reproduced` against
  their controls ([`HIGHER_LATTICE_STUDY.md`](studies/HIGHER_LATTICE_STUDY.md),
  [`HARMONY_STUDY.md`](studies/HARMONY_STUDY.md),
  [`ECONOMICS_STUDY.md`](studies/ECONOMICS_STUDY.md)).

### 3.3 Ongoing rather than finishable

* **`related_to` as a residue.** 66 of the lexicon's 380 triples record that a
  link exists without saying which; all 66 are now *decided* rather than
  declined, 34 without a person, and `closure()` reports **0 triples waiting on
  a lookup**. What stays ongoing is that the lexicon can always grow another
  vague triple ([`DENOTATION_STUDY.md`](studies/DENOTATION_STUDY.md),
  [`VAGUENESS_STUDY.md`](studies/VAGUENESS_STUDY.md)).
* **Sparse chemistry.** 1,257 of 1,652 element cells are measured; the
  completed view reaches 1,344 by rules admitted only for halving the field's
  own out-of-sample mean and for surviving a nested holdout of their own
  selection (Phase 93), and each of the remaining 308 carries a stated
  reason. The register is read against cited outside values, never written
  ([`REGISTER_WORLD_STUDY.md`](studies/REGISTER_WORLD_STUDY.md)). Nothing is written back into the register, deliberately. What
  stays ongoing is the data
  ([`ELEMENT_COMPLETION_STUDY.md`](studies/ELEMENT_COMPLETION_STUDY.md)).

### 3.4 Named for the next round

**Read this section first on the next development push.** The head of
[`MASTER_PLAN.md`](MASTER_PLAN.md) names where the next round
starts and points back here.

**The order of work — merged and sequenced in Phase 87**
([`ROADMAP_STUDY.md`](studies/ROADMAP_STUDY.md)). The candidates below are
kept under the letters they were named with, but they are no longer taken in
that order. The 49 open items reduce to seven tracks; several items are one
piece of work under two or three letters, and the rounds are ordered so that
each reads what the one before built:

1. **The measurand register** — K2, O5b, O5c, O5d, 1a and 1b, one round:
   **taken by Phase 87** ([`MEASURAND_REGISTER_STUDY.md`](studies/MEASURAND_REGISTER_STUDY.md));
   all but 1a met, and 1a waits on a register that holds a Celsius reading.
2. **The loop through the planner** — K4 (`derive` as a value), I2 (a Python
   expression as a planner question), O3 = M3 (the planner's answer chooses
   the next reverse operation); then re-read item 9, the utility gate:
   **taken by Phase 88** ([`PLANNER_LOOP_STUDY.md`](studies/PLANNER_LOOP_STUDY.md));
   every mark met. Item 9 re-read: the loop's questions asked in English are
   answered by no surface, so the problem-driven reach item 9 asked about
   now exists and is measured; promoting the supplied planner is still not
   earned.
3. **Typed operators** — F, on the measurand register: **taken by Phase 90**
   ([`TYPED_OPERATORS_STUDY.md`](studies/TYPED_OPERATORS_STUDY.md)); every
   mark met.
4. **Planner widenings** — H's E6 (frames from a declaration) first, then
   O7's remainder and candidate 2's §6: **taken by Phase 91**
   ([`DECLARED_FRAMES_STUDY.md`](studies/DECLARED_FRAMES_STUDY.md)); every
   mark met. What it leaves is that study's §6 (cross-table comparison,
   differences between molecules, a nuclide register, one-sided ranges, the
   top `k` under a hole).
5. **Discourse state** — 0b (a tie carried as a column, now that set folds
   exist), then D = 0a, then K3: **taken by Phase 92**
   ([`DISCOURSE_STATE_STUDY.md`](studies/DISCOURSE_STATE_STUDY.md)); every
   mark met. What it leaves is that study's §7 (the column handed to the
   planner's folds, a present-rows column, further phrasings, the plan store
   for the new shapes, an outside multi-turn set).
6. **The register against the world** — C with H's first item: **taken by
   Phase 93** ([`REGISTER_WORLD_STUDY.md`](studies/REGISTER_WORLD_STUDY.md));
   every mark met. What it leaves is that study's §6 (sources for the other
   fields — electron affinity, melting and boiling points; isotope masses for
   the 34 world-silent weights; a held-out check of the narrowing; the owner's
   decision on writing any discrepancy back).
7. **The third sort** — I1 with M's strings, tuples and ranges; then M's
   imperative grammar. The first half is **taken by Phase 94**
   ([`THIRD_SORT_STUDY.md`](studies/THIRD_SORT_STUDY.md)); every mark met.
   What it leaves is that study's §6 (Unicode case and whitespace tables as a
   register, booleans as a term of the grammar, sets and comprehensions).
   M's imperative grammar is **taken by Phase 95**
   ([`IMPERATIVE_GRAMMAR_STUDY.md`](studies/IMPERATIVE_GRAMMAR_STUDY.md));
   8 of 9 marks met (I7 not met: one earlier refusal made more specific).
   What it leaves is that study's §6 (`break`, closures, the truth of
   sequences, a trace inside calls, a program with state handed to the
   planner as a sentence).
8. **Second readings** — J2 with H's X1, then J1, then J3 (now well-posed
   on Phase 82's rate posterior); the lattice items 3, 6, 7 and 10 beside it.
   J2, X1, J1 and J3 are **taken by Phase 96**
   ([`SECOND_VIEW_STUDY.md`](studies/SECOND_VIEW_STUDY.md)); 7 of 9 marks met
   (V4 and V8 not met). J3 is closed in the negative by a theorem: a soft
   channel built from the machine's own views adds nothing to the second
   reading. What it leaves is that study's §6 (framing an existing register
   by default, a soft channel with reliabilities from outside the views), and
   the lattice items 3, 6, 7 and 10, not taken. Its two misses were
   **re-scored by Phase 97** at the owner's request
   ([`UNPACKING_RESCORE_STUDY.md`](studies/UNPACKING_RESCORE_STUDY.md)):
   argument unpacking added to the dialect and the refused program answered;
   independent faults re-declared (three views, 0 wrong; no frame helps two);
   the third view read on demand; 12 of 12 marks met. What it leaves is that
   study's §6 (keywords and defaults, starred displays, unpacking in the
   imperative grammar).
9. **Retrieval** — N1 first, then item 5, then N2, N5 and I3. **This is where
   the next round starts**, unless the owner prefers the lattice items
   beside round 8 first.

**Taken out of order by Phase 89, at the owner's request**
([`QUESTION_SET_B_STUDY.md`](studies/QUESTION_SET_B_STUDY.md),
[`CONTRACT_MATRIX_STUDY.md`](studies/CONTRACT_MATRIX_STUDY.md)): the gated
items the owner released — K1 (`-q` routed through the multi-surface router,
Option A; the contract set gives 177 of 177 identical verdicts through the
command line), P's two contract changes (run as a 4-way matrix; the combined
change, variant D, is the production baseline and the other two are set
aside), and B = O1 (two outside question sets supplied: Set B 14 of 14 by
audit, Outside O1 27 of 112 framed and correct with 0 confidently wrong and
85 located boundaries). The boundaries it located are new tracks, ordered in
that study's §8: symbolic parameters (13), derivations and proofs (18), meta
questions about the GLM's own engineering (18), explanations (32), designs
and one transcendental equation, and the planner's two vacuous denotation
answers. **Round 9 of the order, retrieval, is where the next round starts** (round 8
was taken by Phase 96), unless the owner prefers the §8 boundary tracks or
the lattice items beside round 8 first.

Gated on outside material: item 4. Proposed
for retirement: P's 42 PIPELINE laws and H's concept 6. The letters below
are the record of what each item is.

The candidates as they were named follow.

**P. The laws in use — named by Phase 74, reworded and taken by Phase 75,
P1 taken by Phase 77, P3 by Phase 80, P4 by Phase 81, P5 by Phase 82, P2 by
Phase 83: closed; the named repairs measured by Phase 86.** At the owner's direction this was never a second law
subsystem: each law tested, improved where it can be, and absorbed only where
it is of use. What the closed items leave, for a later round if the owner
wants it: the soft floor's fixed-rate misses — Phase 86 measured the repairs
([`RATE_POSTERIOR_STUDY.md`](studies/RATE_POSTERIOR_STUDY.md) §4): a finer
grid and a higher guard point repair nothing, an upper-credible rate rule
removes every on-grid break at a small retention cost, and the breaks above
the grid remain; adopting the upper-credible rule is a change of contract and
the owner's call; the
plain `resolve` and `agree` printing a session-marginal confidence (a change
of contract, the owner's call) — *both decided by Phase 89's 4-way matrix*
([`CONTRACT_MATRIX_STUDY.md`](studies/CONTRACT_MATRIX_STUDY.md)): the combined
change (D) breaks no on-grid cell in either frame and keeps more right answers
than the upper rule alone, so it is the production baseline; the upper rule
alone and the session-marginal confidence alone are set aside; the breaks at
1/5 remain under every variant; and the 42 PIPELINE laws, which could only be
re-read through UBP pipelines the GLM does not implement.
[`AGREE_CHANNEL_STUDY.md`](studies/AGREE_CHANNEL_STUDY.md) §3,
[`RATE_POSTERIOR_STUDY.md`](studies/RATE_POSTERIOR_STUDY.md) §3,
[`LAW_TRIAGE_STUDY.md`](studies/LAW_TRIAGE_STUDY.md) §3.

**O. The stepwise planner, round four — named by Phase 72, narrowed by
Phases 73 and 84.** In order: (O1) a held-out set of compound, goal, unit and register
questions written by someone outside the project (the corpora and the module
share an author, and every mark of both rounds was met on the first reading;
this is candidate B's point, sharpest here); (O3) the reverse relay into the
chain, so that `relay:` hands a column-2 value to the stepwise planner and its
multi-step answer chooses the next reverse operation (the last item of
candidate M) — *taken by Phase 88* as a program: a branch on a derived value
chooses which reverse equation `solve` reads
([`PLANNER_LOOP_STUDY.md`](studies/PLANNER_LOOP_STUDY.md)); (O5) measurands by name — Phase 86 took the kinds of quantity
(a torque is no longer an energy, a temperature level no longer a
difference: [`MEASURANDS_STUDY.md`](studies/MEASURANDS_STUDY.md)), and
Phase 87 took the rest — the declared map from register measurands to wheel
quantities, conversions through a stated efficiency and the elementary charge
([`MEASURAND_REGISTER_STUDY.md`](studies/MEASURAND_REGISTER_STUDY.md)); a
radius, argued, feeds no wheel by name. What it leaves is that study's §6;
(O7) the widenings of
[`STEPWISE_TWO_STUDY.md`](studies/STEPWISE_TWO_STUDY.md) §6 (tera and pico,
*heavier* with a declared field, folds over a whole column).
[`STEPWISE_PLANNER_STUDY.md`](studies/STEPWISE_PLANNER_STUDY.md) §6,
[`STEPWISE_TWO_STUDY.md`](studies/STEPWISE_TWO_STUDY.md) §6. *O2 (the frames
and givens with units) and O4 (register values feeding a wheel derivation)
were taken by Phase 73 and are met: every mark of the round-two study is
met. O7's first widenings (declared comparatives, *electrons* and *valence
electrons*, tera and pico, folds over every element or a declared class) were
taken by Phase 84 and are met ([`STEPWISE_THREE_STUDY.md`](studies/STEPWISE_THREE_STUDY.md));
the present-rows question asked as its own was taken by Phase 85 and is met
([`HOLE_FOLDS_STUDY.md`](studies/HOLE_FOLDS_STUDY.md)); the molecule table's
comparatives, further prefixes and the classes the register does not hold as
one value were taken by Phase 91 and are met
([`DECLARED_FRAMES_STUDY.md`](studies/DECLARED_FRAMES_STUDY.md)); what O7
still holds is neutrons (a nuclide register) and differences between
molecules. O6 (a register value's stated precision carried through a derivation)
was taken by Phase 76 and is met ([`HELD_PRECISION_STUDY.md`](studies/HELD_PRECISION_STUDY.md)).*

**N. Native past parity — named by Phase 70, narrowed by Phase 71.** In
order: (N1) a declared resampling of the Lean corpus (every sub-corpus that
drops one file), to say whether the single-book figures of
[`NATIVE_PARITY_STUDY.md`](studies/NATIVE_PARITY_STUDY.md) and the post-hoc
readings of [`NATIVE_WORDS_STUDY.md`](studies/NATIVE_WORDS_STUDY.md) §3.3 —
Golay letter words alone ahead of the token overlap on hits, and ahead of the
part strings on the Lean corpus — are draws or effects; (N2) a third native
book for the documents — a section's position in the document tree as a Golay
word — to move the document rankings past parity with the raw vector; (N5) a
native word ranking with the part letter words as its **first** layer, which
would change the order outside the standard's ties, and a document letter word
that collides less on prose (study §6). *N3 (the native word ranking) was
taken by Phase 71 and is met; N4 (ledger row 6 on the live Lean ranking) was
measured there and missed at k = 1 (mark W6), so it is recorded, not shipped.*
*The owner's standing instruction: where a standard method ties or narrowly
beats a native one, keep the native one and refine it.*

**M. Reverse Three Column Thinking, round four — named by Phase 68, narrowed
by Phases 69 and 79; its first two items taken by Phases 94 and 95.** In the order of the study's §12: strings, tuples and
ranges as a third sort with count-first literals (22 of the 47 dialect
programs still outside act on them); a small imperative grammar, so that the
7 programs with state have sentences; and the loop further — let `relay:` read the integer certificate kinds, hand an
`INDEPENDENT` verdict's witness to the question layer as a follow-up, and let
the planner's answer choose the next reverse operation.
[`REVERSE_TCT_STUDY.md`](studies/REVERSE_TCT_STUDY.md) §12. *The integer sort
(§9's third item) was taken by Phase 69 and is closed: every mark of §10.2 is
met (§11). The complete integer decision (§12's second item) was taken by
Phase 79 and is closed: every mark of
[`INTEGER_DECISION_STUDY.md`](studies/INTEGER_DECISION_STUDY.md) is met.*

*L (Reverse Three Column Thinking, round two, named by Phase 67) was taken by
Phase 68 and is closed: every mark of the study's §7.2 is met (§8).*

**K. The connected machine, round two — named by Phase 66.** In the order of
the study's §6: (K1) route `-q` itself, once the owner agrees, and re-run the
contract set through the command line rather than by census — *taken by
Phase 89* on the owner's Option A: 177 of 177 contract questions identical
through the routed `-q` and `--plan`
([`QUESTION_SET_B_STUDY.md`](studies/QUESTION_SET_B_STUDY.md) §5); (K2) a register
of **measurands** — *taken by Phase 87*: conversions through a stated
efficiency are laws across the junction table's non-identities
([`MEASURAND_REGISTER_STUDY.md`](studies/MEASURAND_REGISTER_STUDY.md));
(K3) bind conversation follow-ups on every surface, not only the planner's —
*taken by Phase 92*: the router is the licence, and `GLM.py --converse` holds
the conversation ([`DISCOURSE_STATE_STUDY.md`](studies/DISCOURSE_STATE_STUDY.md));
(K4) a Python builtin `derive(target, y, z)` so a derivation is a value a
program can use — *taken by Phase 88*
([`PLANNER_LOOP_STUDY.md`](studies/PLANNER_LOOP_STUDY.md)). [`CONNECTED_MACHINE_STUDY.md`](studies/CONNECTED_MACHINE_STUDY.md) §6.

**J. The carried fork, round two — named by Phase 65.** In the order of
the study's §6: declare and measure the composition of stages (the declared
cases, then a second reading, which resolved 35,872 of the 48,320 forks left
open at 32 cases post hoc, 0 wrong); give the runtime a second independent
view of one carrier so the second reading is routine rather than supplied by
the caller; and test the Leech escalation on a soft channel whose
reliabilities come from the machine's own readings rather than a declared
formula. [`CARRIED_FORK_STUDY.md`](studies/CARRIED_FORK_STUDY.md) §6.
*All three taken by Phase 96*
([`SECOND_VIEW_STUDY.md`](studies/SECOND_VIEW_STUDY.md)): the composition
declared and met on a fresh probe, the second view produced by a framed
register, and the soft channel of the machine's own views proved to add
nothing to the second reading.

**I. Python speech, round two — named by Phase 64.** In the order of the
study's §7: widen the dialect where the refusals cluster (string methods over
code points; list and dict literals as immutable snapshots); route a
question about a Python expression through a typed planner frame to the
evaluator (*taken by Phase 88*,
[`PLANNER_LOOP_STUDY.md`](studies/PLANNER_LOOP_STUDY.md)); and index the AST address beside the Lean corpus addresses as a
retrieval key. [`PYTHON_SPEECH_STUDY.md`](studies/PYTHON_SPEECH_STUDY.md) §7.

**H. Substrate-native cognition, round three — named by Phase 63.** In the
order of the study's §8: demote (or narrow) the two chemistry completion rules
that fail nested holdouts, `covalent_radius_pm` and `electron_affinity_eV`
(*taken by Phase 93 and met*: the first demoted, the second narrowed to the
main group, [`REGISTER_WORLD_STUDY.md`](studies/REGISTER_WORLD_STUDY.md));
semantic judgements as annotated provenance (E4); frames generated from a
declaration rather than written by hand (E6, *taken by Phase 91 and met*,
[`DECLARED_FRAMES_STUDY.md`](studies/DECLARED_FRAMES_STUDY.md)); deeper PCGS proofs (E7); a second
independent reading for the deep-hole fork (X1, *taken by Phase 96*: the
framed register produces it); and concept 6, which waits on
a trilinear object in the runtime.
[`SUBSTRATE_NATIVE_COGNITION_STUDY.md`](studies/SUBSTRATE_NATIVE_COGNITION_STUDY.md) §8.

**E. Derivation across a declared union of wheels — done in Phase 66**, as the
*across wheels* frame with a declared junction table (study §3.5–§3.7). What
follows is the note as it was written. The
engineering surface derives inside one wheel at a time, as the formula study's
protocol does, and so refuses *derive power from pressure and volume flow
rate*; across the union of the ten wheels that formula (hydraulic power)
follows from W5 and W6. A second mode that names the union it used in the
answer, measured on a set written for it, would say what composition gains
and what it gets wrong. [`ENGINEERING_LANGUAGE_STUDY.md`](studies/ENGINEERING_LANGUAGE_STUDY.md) §3.

**F. Typed physical operators — named by Phase 59, taken by Phase 90: closed.**
Monomial wheels cannot separate real, reactive and apparent power (W2-03),
nor dot from cross product. Complex power with conjugation, over the Gaussian
rationals the Smith chart already uses, is the smallest step. The record's
Priority 5. *Taken by Phase 90* ([`TYPED_OPERATORS_STUDY.md`](studies/TYPED_OPERATORS_STUDY.md)):
every mark met. What it leaves is that study's §6: polar phasors, three-phase
power and power-factor correction, the planner's own DC `power` with an
alternating question (an earlier verdict, the owner's call), and the
verifier's rank algebra joined to the typed values.

**G. The archive Lean left behind — named by Phase 60, narrowed by Phase 61.**
Phase 61 rebuilt the small files the supplied-material ledger named —
`GolayMOG.lean`, `Distinction.lean`, `Seeds.lean`, `Fibre.lean`,
`Cheapest.lean` and `Independence.lean` — as `RequestProject/GLM/GolayMOG.lean`,
`Distinction.lean` and `SeedRoles.lean`, proving the irrationality of `e` that
they had assumed. What remains (Appendix C.3 of
[`GLM_ACADEMIC_PAPER.md`](studies/GLM_ACADEMIC_PAPER.md)) is the language half of
`mog_cube_1`, about thirty files, and the unported part of `ObserverY.lean`; no
code path reads either yet. The vision experiments script
(`glm_vision_experiments_v14.py`) is the same kind of candidate on the Python
side.

**A. The planner as the default path — done in Phase 63.** The planner now
reads first, and `--grammar` opts out. What follows is the note as it was
written: the typed planner was opt-in because the command line renders every answer as a three-column
trace and a computed plan (an exact sum, a conversion, a primality witness)
has no trace kind yet. Asked in-process, the 177 contract cases differ in two
answers through the planner and both still pass; what remains is a trace for
the planner's own computations, then the switch, then the contract set run
through it. [`SEMANTIC_PLAN_STUDY.md`](studies/SEMANTIC_PLAN_STUDY.md) §8.

**B. A held-out set nobody on the project wrote — named this round.** The
held-out sets were committed before the planner and share its author; an
independently written set of questions, with labels from outside the
registers, is the test that would separate reach from anticipation. The
scoring rule and the harness exist (`evaluation/heldout.py`,
`reasoning/typed_plans.py`). *Taken by Phase 89 with the owner's two outside
sets* ([`QUESTION_SET_B_STUDY.md`](studies/QUESTION_SET_B_STUDY.md)): before
any frame the router read none of the 126 questions; with declared question
frames Set B is 14 of 14 by audit and Outside O1 27 of 112, 0 confidently
wrong. What it leaves is that study's §8, the located boundaries.

**C. The register against the world — partly done in Phase 63, taken by
Phase 93** ([`REGISTER_WORLD_STUDY.md`](studies/REGISTER_WORLD_STUDY.md): all
354 cells of atomic weight, ionization energy and configuration read against
frozen CIAAW and NIST sources; 24 ionization energies and one configuration
discrepant; the register never written). What follows is the note as it was
written. A question
can now ask whether a register value is consistent with the declared standard
table, at the precision each is held to; the full discrepancy report over
every row is still open. The planner's one
wrong answer is the element register holding iron's atomic weight as `55.84`
where the IUPAC value is `55.845`. The roadmap's external-truth layer — a
discrepancy report of register values against cited standard values, never
overwriting the register — would find every such row rather than the one a
question happened to reach.

**D. Discourse state, typed — taken by Phase 92**
([`DISCOURSE_STATE_STUDY.md`](studies/DISCOURSE_STATE_STUDY.md): *the one
before that*, the plurals and *why?* are read). The conversation layer bound
three surface shapes of follow-up; the planner's typed slots are the state a fourth shape
needs (*the one before that*, *both of them*), and a set-valued referent is
what candidate 0 below asks for.

**0. The second turn, carried further — named the round before last; both
halves taken by Phase 92** ([`DISCOURSE_STATE_STUDY.md`](studies/DISCOURSE_STATE_STUDY.md):
the tie is carried as a column, refused `column-incomplete` under a hole, and
the fourth shape is read). The conversation
layer binds three declared shapes of follow-up and refuses everything else,
and the two things it most obviously cannot do are each a round: a **fourth
shape** that is not a surface pattern at all — *the one before that*, *both of
them*, *why?* — and a **tie carried forward rather than refused**, so that
*describe it* after a fourteen-row tie asks its question of all fourteen and
reports a column rather than a refusal. The second is the more interesting:
it turns the layer's sharpest refusal into the extremum operation's kind of
answer, and it needs a statement of what *the answer for several rows at once*
is before it needs any code.
[`CONVERSATION_STUDY.md`](studies/CONVERSATION_STUDY.md) §8, whose §9 now
records the outcome of every piece of the supplied material: four were taken
in Phase 56 — two shipped, one measured into the sandbox and one refuted — and
the rest stand with what they would have to measure to earn a round.

**1. The two halves of the conversion table that are not yet earned — named
by Phase 55; the offset half partly shipped by Phase 86; the measurand half
taken by Phase 87** ([`MEASURAND_REGISTER_STUDY.md`](studies/MEASURAND_REGISTER_STUDY.md):
every scale of the table has a declared measurand, and every pair the table
relates is a pair of one kind, so none is withdrawn). What stays open is the
offset row, which waits on a register holding a Celsius reading. Phase 86 reads
Celsius and Fahrenheit givens in the stepwise planner with their offsets, as
a level or a difference ([`MEASURANDS_STUDY.md`](studies/MEASURANDS_STUDY.md));
the scale table itself still has no offset row. The declared table relates nine scales over four quantities, and two
of its commitments are written but untested. The affine shape admits an
**offset** and no declared row uses one, so the half of
`GLM.ScaleConversion.cmpQ_apply` that the offset exercises is proved and not
shipped: a register holding a temperature in degrees Celsius, or any scale
that does not start at its quantity's zero, is what would settle it. And the
table declares a **unit** rather than a measurand, so it cannot say that an
atomic radius and a covalent radius are two different measurements that happen
to share picometres. A second declaration — measurands, and which pairs of
them are comparable — is the harder and more interesting of the two, because
it is the first thing in this system that would have to be argued for rather
than looked up.
[`SCALE_CONVERSION_STUDY.md`](studies/SCALE_CONVERSION_STUDY.md) §9.

**2. What a fold other than a maximum does with a hole — done in Phase 85**
([`HOLE_FOLDS_STUDY.md`](studies/HOLE_FOLDS_STUDY.md)): a median or a rank
over a column with holes is the exact interval every completion lands in,
proved sharp in `RequestProject/GLM/HoleBounds.lean`; the ends are refused as
open; the present-rows question is answered as its own with the missing rows
named. What it leaves is the study's §6: top-*k* and other quantiles as
frames, a mean bounded by a declared range, and present-rows parity counts —
all three taken by Phase 91 and met
([`DECLARED_FRAMES_STUDY.md`](studies/DECLARED_FRAMES_STUDY.md)), the top
*k* under a hole refused whole.
What follows is the note as it was written. The extremum
operation refuses a column with a missing reading, and proves why. A rank, a
median or a top-*k* over the same column each need their own statement of what
a hole does to them — a median over the present rows is not the median, but it
is wrong in a different way and by a different amount — and none of the three
is built. The narrower question beside it is the answerable one the refusal
declines: *of the rows that are filled in, which is the largest?* is a
different question, and it would have to be asked as one, with the missing
rows named in the answer rather than in the refusal.
[`COLUMN_EXTREMUM_STUDY.md`](studies/COLUMN_EXTREMUM_STUDY.md) §7.

**3. The eight reasoning modules nothing runs — done in Phase 66**: each is
reachable as a tool, and the audit reads 0 of 96 unreached. What follows is
the note as it was written. **The other half of the wiring
audit.** The wiring
audit recorded in [`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 56 reads the import
graph of the package from every entry point it actually runs from, and finds **8** of the
**89** `reasoning/` modules outside the closure: `deep_dive`, `llvq`,
`moonshine`, `pcgs`, `salvage`, `salvage_second`, `stability` and `tie_break`.
Every one of them has a test file and a study, so each is a result that was
reached, checked and written up — and then left where nothing on the machine's
own path can call it. Two of them (`llvq`, `salvage`) are named only inside a
generated recompute script, which is real but runs only when a reader
recomputes a receipt; three more (`deep_dive`, `pcgs`, `salvage_second`) are
catalogued as file paths in `reasoning/combiner.py`'s source table without
ever being imported. The round this becomes is not a port: it is one decision
per module, *reachable or retired*, taken with its study open, and the honest
outcome for some of them is the archive. Re-read it with
`python3 studies/scripts/wiring_audit.py`.

*Closed this round (Phase 57):* candidate 4 of the list as it stood, *the
measurements no reader sees*. All **20** registered figure keys that no
document quoted are now quoted — none was retired, because each was a number
its document was already saying by hand or should have been saying — and the
converse of **D6** is a checked rule rather than a habit:
`tests/test_figures.py::TestEveryRegisteredFigureIsQuoted` fails when a
registered key is read by no document, and when a document quotes a key the
registry does not hold. Closing it exposed a defect worth the round on its
own: `corpus-documents` counted **98** documents where the corpus study's own
inventory counted **95**, because the key counted the three documents the
machine *generates*, which are outputs of the corpus rather than parts of it;
the three document-count keys are now taken over the written corpus, the set
the digest guards. It also turned up a plain D6 breach — the
operation-escalation study was typing its deciding figure by hand. The audit
now reads **135 registered, 135 quoted, 0 never quoted**
(`python3 studies/scripts/wiring_audit.py`).
[`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 57.

*Closed in Phase 56:* not a candidate from this list but the four
rows of [`CONVERSATION_STUDY.md`](studies/CONVERSATION_STUDY.md) §9 — the
supplied conversational material Phase 54 read, ran and left unported. The
**role–filler binding** and the **procedural-plan store** ship:
`reasoning/role_binding.py` writes a typed relation between two named carriers
as one 24-bit word whose inverse is itself, and `runtime/plan_store.py` keeps
a resolved follow-up — refusals exactly as answers — under a digest of the
whole conversation it was resolved in, wired into `runtime/conversation.py` as
an optional `store=`. `RequestProject/GLM/RoleBinding.lean` and
`RequestProject/GLM/PlanStore.lean` prove what is a theorem rather than a rate:
unbinding inverts binding for every role and pair, recovery by name is sound
and refuses exactly when the reading is not unique, replay agrees with running
and preserves a refusal, and the exact key separates two conversations that
share a follow-up where the coarse one does not. The **four-register memory
split** and the **Lean-source generator** were measured and declined: both sit
in `glm_universal/sandbox/` with a computed checklist that says `ready is
False`. Under directive **D15** it moved **addressing** and **refusal**.
[`SUPPLIED_PORTS_STUDY.md`](studies/SUPPLIED_PORTS_STUDY.md). It also carried
the wiring audit that became candidate 3 above and the round Phase 57 then
took, and it closed on two
defects of its own that the suite found: the plan store's digest went round
`hashlib` instead of `glm_universal.integrity`, which breaks **D3**, and the
binding was an unclassified exclusive-or site in `reasoning/combiner.py`'s
table. Both are fixed, and the sandbox now reads its own occupancy rather than
asserting it (`glm_universal.sandbox.occupancy_report`).

*Closed in Phase 55:* candidate 1 of the list as it then stood — the scales
neither operation could bridge. `glm_universal.reasoning.scale_conversion`
declares nine scales over four quantities, each row an exact positive-affine
map into the quantity's canonical unit with the source its numbers came from,
and `RequestProject/GLM/ScaleConversion.lean` proves that a positive
conversion composed into the comparison leaves the verdict alone, that the
wider operation never changes an answer the bare one gave, that its silence is
still exactly stated, and that the declaration itself carries the claim. On a
declared set of twelve questions it answers seven and refuses five, all twelve
as declared, and it leaves the two operations underneath it unchanged on their
own declared sets. Under directive **D15** it moved **refusal** — three of the
five refusals are comparisons the table was given the chance to license and
did not — and widened **derivation** to a fold over rows of two tables at
once. [`SCALE_CONVERSION_STUDY.md`](studies/SCALE_CONVERSION_STUDY.md).

*Closed in Phase 54:* not a candidate from this list but the
material supplied with the round — `source_material/conversation_experiment/`,
tested rather than believed. All eight of its scripts run unmodified against
the package; two of its headline claims are refuted (the higher-order analogy
whose second constraint has no exact solution, and the periodic-table reading
that renames two carrier coordinates); and the one thing in it the system
could not do is built, measured, proved and released: a turn that refers back
to an earlier turn, bound by licensing, `8` of `15` declared follow-ups bound
and `7` refused against `0` for a session with no memory. Under directive
**D15** it moved **addressing** and **refusal**.
[`CONVERSATION_STUDY.md`](studies/CONVERSATION_STUDY.md).

*Closed in Phase 53:* candidate 1 of the round before it — the column
rather than the pair. The `extremum` query kind and
`reasoning/column_extremum.py` read one coordinate off every row of one
declared table and fold it exactly, naming every row that attains the end, or
refuse under one of four named reasons, and
`RequestProject/GLM/ColumnExtremum.lean` proves that the silence is exactly
the second scale, the hole and the empty column, that the value returned is
one of the column's own with nothing past it, that the rows named are exactly
the rows attaining it, and that both refusals are results rather than
fussiness. Under directive **D15** it moved **derivation** — a fold over
addressed readings, which no register holds — and **refusal**, on a declared
task set of eight columns, all eight as declared.
[`COLUMN_EXTREMUM_STUDY.md`](studies/COLUMN_EXTREMUM_STUDY.md).

*Closed in Phase 51:* candidate 1 of the last round — the comparison
the field surface could not make. The `ordering` query kind and
`reasoning/coordinate_order.py` read one coordinate off two rows and order it
exactly, or refuse under one of three named reasons, and
`RequestProject/GLM/CoordinateOrder.lean` proves that the silence is exactly
the missing reading and the mismatched scale, that the answer is the order of
the two values, and that *same scale* is the right side condition because a
rescaling of one reading alone flips the comparison. Under directive **D15**
it moved **derivation** — of the weakest interesting kind, one exact
subtraction over two addressed readings — and **refusal**, on a declared task
set of seven comparisons, all seven as declared. All
<!--figure:ordering-held-->10<!--/figure--> of the probe's held-and-unreachable
questions are now parsed. [`ORDERING_STUDY.md`](studies/ORDERING_STUDY.md).

*Closed in Phase 50 (maintenance):* the release Phase 49 had not run,
and the six units that failed it — the UBP source audit taught to read the
declared float sites off the D11 inventory, the reasoning kernel's import
audit, the Lean file count, the query-escalation cache, and the relay and
anonymous measurements re-taken over the grown corpus. It moved none of
derivation, addressing or refusal, and leaves the candidates above unchanged.

*Closed in Phase 49:* the supplied *History Recorded in the Now*
material, decided rather than illustrated — nine claims settled, three of them
refuted, the refusal faculty moved on a declared task set, and the shipped
modulator's loop replaced by the closed form it was always computing.
[`NOW_RECEIPT_STUDY.md`](studies/NOW_RECEIPT_STUDY.md). It leaves two things
named there and not taken: the v4 query-loop reading, which has no control, and
the v4 higher-lattice escalation, which was argued rather than run.

*Closed in Phase 48 (maintenance):* the handover the round before it
left open — the generated layer refreshed and every unit re-signed — and the
cost of `report lean`, which had grown through the evaluation's 300-second
ceiling. It is now 77 seconds, by an exact identity and an exact pruning
bound, with every figure of
[`LEAN_ADDRESS_STUDY.md`](studies/LEAN_ADDRESS_STUDY.md) §7 unchanged. Neither
is a claim about reasoning, and the candidates above are unchanged by it.

*Closed in Phase 47 (maintenance):* the round loop itself. The
ledger's Lean selectivity, undone by the field surface reading the development
on the runtime's import path, is restored and pinned by tests — a median Lean
edit costs **27** of 98 units rather than 79 — and a passing documents check
is no longer re-derived over a tree in which nothing has moved. Neither is a
claim about reasoning; both are recorded as what they are, in §5e and §5f of
[`ITERATION_COST_STUDY.md`](studies/ITERATION_COST_STUDY.md). The candidates
above are unchanged by it.

*Closed in Phase 46:* the field surface itself — candidate 1 of the round
before it. It answers <!--figure:fieldsurface-moved-->9<!--/figure--> of the
<!--figure:fieldsurface-held-->10<!--/figure--> questions the translation
experiment found held and unreachable, exactly the number declared reachable
before the run, and it is reported as coverage rather than reasoning:
[`FIELD_SURFACE_STUDY.md`](studies/FIELD_SURFACE_STUDY.md), with the
description in §2 and the proved boundary in `GLM.FieldSurface`.

**3. The empty rungs of the power-of-two family.** The family is complete as a
family and deliberately incomplete as a *ladder*: norms 2 and 256 are empty in
the ladder actually used, because the rungs that would fill them conflate. What
would close it is a rung at those norms that does not — Construction `A` over a
shortened code, or the `D₄`/`E₈` layers, which the scaling does not generate.
[`NORM_FAMILY_STUDY.md`](studies/NORM_FAMILY_STUDY.md).

**4. A register that arrives anonymous on its own.** Renaming is a faithful
model of a cross-vocabulary goal and it is still a model. The measurement to
want is the same table over goals from a second Lean development, or from a
generator, scored against the same controls — a register nobody constructed.

**5. The leak in the feature map.** The shipped map counts the type vocabulary
wherever it occurs, including inside an identifier, so 39 of 883 queries lose a
coordinate when their names go: a name creeping into a reading that is supposed
to be structural. Either the map is narrowed to count type words only where
they are types, or the leak is priced.

**6. The separation criterion, still unmet.** `nearest_correct` in
`DeepHoleLadder.lean` says a reading names holes correctly whenever
`ρ = 2W/B < 1`. Measured, `ρ` falls from `3.90` to **`2.59`** across the ladder
and never crosses `1`, so a classifier that names 40 of 44 still cannot certify
a single *absence*: faithfulness needs `r ≥ 0.0659` where separation permits
`r < 0.0179`. Either a rung is found where `ρ < 1`, or a bound is proved saying
no reading of this family reaches it. Its companion is
`GLM.DeepHoleFailure.per_type_absent`, the certificate whose hypothesis is
currently unmet, so the theorem is instantiated nowhere.

**7. The thirteen unreached Niemeier types.** The ensemble reaches **10** of
the 23 root systems from the 14 declared centres; the other **13** are reported
as unreached and nothing is claimed about them. Reaching them means new
centres, and new centres mean a new pre-registration.

**8. What the adopted guard costs, and why the metric reading is safe.** The
guard refuses 137 queries it used to answer correctly. The room is in the
*reading* rather than in the contract — the weaker guard is measured and never
reaches safety — and the metric reading answers nothing wrongly on any of the
six operations while losing to the primary on four, which is a decomposition
worth understanding. A margin other than twice the nearest distance is the
obvious sweep. [`SECOND_READING_STUDY.md`](studies/SECOND_READING_STUDY.md) §9.

**9. The planner's utility gate.** The reverse-call planner satisfies every
safety line of its promotion checklist and fails the one that decides it: on
this project's own evaluation set it gains nothing, because the refusals it is
offered are refusals it agrees with. The question that would close it is about
the **tool registry** — whether a tool exists that a problem-driven front end
could reach and the kind-driven dispatcher cannot. Until one does, directive
**D14** keeps the planner in the sandbox, imported by nothing the system
computes with. *Re-read by Phase 88*
([`PLANNER_LOOP_STUDY.md`](studies/PLANNER_LOOP_STUDY.md)): the loop's
questions are answered when written as programs and by no surface when asked
in English — the first measured instance of the reach this item asks for. The
promotion line is still failed, because the supplied planner itself does not
reach them; reading such a question from English is the next measurable step.

**10. A conflation the rational reading must make.** Read alone, the exact
distance measure conflates `A_1^24` with `A_2^12`. That is a capacity boundary
of the kind [`INFORMATION_LOSS_STUDY.md`](studies/INFORMATION_LOSS_STUDY.md) is
about, and it is recorded as an observation rather than as a theorem. The
theorem to want says *which* pairs any stray-blind reading must conflate.

**The discipline any of them is taken under**, unchanged: the thing must be
described or measured rather than asserted, what does not generalise must be
counted rather than hidden, the path it replaces must be frozen so the new one
has something to agree with, and the end-to-end evaluation must return the same
answers and the same refusals. What should **not** generalise is the
judgements — which brackets count as ordinary cases, which factor basis may
explain a dimensional difference, which pole a word names, which phrasings are
the same question — and a `Phrasing` cannot be constructed without the sentence
that justifies it. Coverage stays two figures rather than one: three of the
eight registers are described, and seven of the twenty-three answerable query
kinds are.

---

## 4. Re-verifying the whole thing

**The operating manual is [`ITERATE.md`](ITERATE.md)**, which states the three
gates — the document check after prose, the changed-unit run after code or
Lean, the release once at the close of a round — and which to run when. This
section is the detail behind them.

### 4.1 The short way — run only what has changed

**Start here.** Everything is signed off in `overlay/.glm_signoff.json`: each
test file and each instrument carries the SHA-256 of everything its last
passing result depended on — the file itself, every module it imports
transitively, the frozen data those modules read, the documents and Lean
sources they name, the harness and the interpreter. If that digest holds,
re-running proves nothing; if a byte in the closure differs, the unit is run
again. Nothing is skipped silently.

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.corpus --check            # documents, ~30 s
PYTHONPATH=. python3 -m glm_universal.signoff --verify          # what still holds
PYTHONPATH=. python3 -m glm_universal.signoff --plan            # what would run
PYTHONPATH=. python3 -m glm_universal.signoff --why             # and why each unit would
PYTHONPATH=. python3 -m glm_universal.signoff --impact ../DIGEST.md  # what an edit would cost
PYTHONPATH=. python3 -m glm_universal.signoff --run-everything --jobs 8
PYTHONPATH=. python3 -m glm_universal.signoff --release --jobs 8   # closing a round
PYTHONPATH=. python3 -m glm_universal.signoff --release --resume --jobs 8  # after one was interrupted
```

A release writes each signature as it is earned rather than at the end, so an
interrupted one is resumed rather than restarted: `--release --resume` runs
only the units the release question still calls stale, and
`--verify-release` — which re-checks every signature and reports anything
signed without the exhaustive cases as `partial` — is still what decides the
round.

`--why` splits a unit's closure into five disjoint groups — scaffolding, data,
documents, Lean, code — and names the ones that moved, so a long plan says
which entries are a prose edit and which are not. `--impact PATH` asks the
same relation in the other direction and *before* the edit: 32 of the 123
units reach `PROJECT_DIRECTIVES.md` (120 before Phase 78; see
[`studies/ITERATION_COST_STUDY.md`](studies/ITERATION_COST_STUDY.md) §5g).

The six instruments in the ledger beside the
<!--figure:test-files-->143 test files<!--/figure--> are `lean-build`,
`lean-sorry-free`, `capabilities`, `benchmarks`, `evaluation` and `figures`.
(The seventh, `lean-copies-identical`, went with the second copy of the Lean
tree in Phase 78: the development lives only in `overlay/glm_lean/`.) Editing a document makes exactly the units that
read that document stale — `test_figures.py` yes, `test_substrate.py` no — so
writing up a finding costs one short re-run rather than a quarter of an hour.
A median Lean edit makes **27** units stale and a unit's closure is **129**
files. [`studies/ITERATION_COST_STUDY.md`](studies/ITERATION_COST_STUDY.md)
§5a is the measurement; `glm_universal.corpus.cost.lean_blast_radius`
recomputes it; directive **D16** is the rule.

That selectivity is a property of the tree and not of the rule alone, and a
feature undid it once: the field surface loaded its Lean rows by parsing the
development, on the runtime's own import path, so the whole development
re-entered nearly every closure and a median Lean edit made **79** of 98 units
stale. The rows come from the stored address book now — `lean_address.py`
builds the book, `lean_book.py` answers from it and reads no source — and the
property is pinned by a test rather than by a paragraph
(`test_signoff.py`, `test_corpus.py`). §5e of the same study is the
measurement.

**The documents gate skips a question whose inputs have not moved.** The
verdict of a passing `corpus --check` is stored beside a digest of everything
that check can read — the documents, the rendering code, the data it reads and
the Lean sources its blocks quote. A check over an unchanged tree answers from
that record in about three seconds instead of re-rendering 97 blocks and 201
figures; only a pass is recorded, so a failure is never skipped, and
`--check --all` ignores the record. §5f of the same study.

The same rule now applies to the ledger's own sources. `signoff/rules.py` is
the **rule** — what a closure is, what a digest covers, how a unit is run —
and is in every closure, so editing it costs the whole suite. `signoff/ledger.py`
is the **record** and costs 6 units; `signoff/checks.py` costs 2 and
`signoff/__main__.py` costs 1. §5c of the same study is the measurement.

**A stale derived artefact is reported, never paid for inside a check.** The
expensive derivations — the planner's fallback reading over the evaluation set,
the type-2 class table, the economic lattice points — are kept beside the
digest of the code they came from. `corpus --check` runs with recomputation
forbidden, so a stale one is named together with the command that rebuilds it
rather than silently costing a quarter of an hour; `corpus --refresh` is where
that cost is paid, once.

### 4.2 The long way — run everything from scratch

In order, from the repository root; the last step is the one that catches a
document drifting from the code.

```bash
lake build                                                   # the Lean files, no sorry
rg -n 'sorry|admit' -g '*.lean' overlay/glm_lean             # expect nothing

cd overlay
PYTHONPATH=. GLM_EXHAUSTIVE=1 python3 -m pytest glm_universal/tests -q
PYTHONPATH=. python3 -m glm_universal.capabilities           # 33 probes
PYTHONPATH=. python3 -m glm_universal.benchmarks             # 5 suites
PYTHONPATH=. python3 -m glm_universal.evaluation --jobs 8    # 177 CLI cases
PYTHONPATH=. python3 -m glm_universal.figures --write        # regenerate FIGURES.md
PYTHONPATH=. python3 -m glm_universal.corpus --refresh       # every derived artefact
PYTHONPATH=. python3 -m glm_universal.corpus --check          # exit 1 on any drift
```

Spot checks that exercise the runtime the way a user does — each returns
`VERIFIED True`, because the Three Column Thinking template regenerates the
answer's figures in a fresh interpreter and compares them with what was
printed:

```bash
cd overlay
PYTHONPATH=. python3 GLM.py -q "report analogies"  --verify-tct
PYTHONPATH=. python3 GLM.py -q "report chemistry coverage" --verify-tct
PYTHONPATH=. python3 GLM.py -q "report lean"       --verify-tct
PYTHONPATH=. python3 GLM.py -q "report escalation" --verify-tct
PYTHONPATH=. python3 -m glm_universal.tools pipeline      # the wiring stages
PYTHONPATH=. python3 -m glm_universal.tools directives    # the standing rules
PYTHONPATH=. python3 -m glm_universal.tools signoff       # the ledger summary
```

---

## 5. The document map

There is no hand-kept index any more, because a hand-kept index is a stored
table and this project's rule is that a table may be kept only beside the
digest of what it came from.

* [`ENTRY.md`](ENTRY.md) states the reading order and the coverage claim:
  these documents describe the system as it is, everything else is a record of
  a round.  The claim is tested — `glm_universal.corpus.checks` fails if a
  current-state document is unreachable from it or an archived one is missing
  from its list.
* [`DIGEST.md`](DIGEST.md) is that list at tier 0, one row per document —
  question, verdict, deciding figure, and the function that recomputes it.  It
  is **generated** from the documents' own tier-0 blocks by
  `python3 -m glm_universal.corpus --write`, so it cannot drift from them.
