# The Integer Wheel and the Monster Wheel — can the GLM name a sequence and a sporadic group, with nothing confidently wrong?

## Tier 0 — the coarse read

**Question.** Does the GLM, given the supplied Integer Wheel and Monster Wheel (`glm_wheels_bundle`), answer sequence-identification and sporadic-group-order questions that it currently refuses, with no answer confidently wrong?

**Verdict.** Yes, for these two kinds of question: with the audited wheels the GLM's query surface answers 89 of the 102 pre-registered questions right and 0 wrong (57 of the 70 sequence questions and all 32 sporadic-group questions), where the GLM's command line without them answers 0 of them; all 28 negative controls are refused or left alone, and no soundness check finds a false identification. The supplied data unaudited would have answered 6 of the questions wrongly, and on the item's own Rule 30 / ARC battery the Monster Wheel adds 0 identifications and finds 0 sporadic orders: no help there.

**Deciding figure.** 89 of 102 questions answered right and 0 wrong with the wheels (bar: at least 85, 0 wrong), against 0 of 102 through the command line without them; 28 of 28 negative controls refused or left alone; 0 false identifications in 8517 soundness checks.

**Recomputed by.** `glm_universal.wheels.integer_wheel_study.integer_wheel_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

*Created 31 October 2026 (intake of `source_material/ToDo/glm_wheels_bundle`, directive D22). §§0–6 were written on 31 October 2026 before any module of the round existed and before any question below was put to the GLM or to a wheel; §7 is what came out, measured on 31 October 2026. Last altered 31 October 2026 (§7 and the tier-0 block written from the measurement; in §§0–6 one word corrected, “committed” to “written” in §0, since the files of the round are committed by the integration and not by this intake).  Last altered 31 October 2026: the wheels installed provisionally by the owner's decision, awaiting the owner's Lean build (§7.4); S2 put to the command line without the wheels, now that the command line answers from them, and the wired command line measured (§7.5).*

*Last altered 1 November 2026 (Phase 186: the bundle is absorbed ahead of the owner's Lean build and filed in `source_material/done/glm_wheels_bundle/`; the link to it now points there.)*

## 0. What this document is

A **pre-registration** for the intake of one supplied item,
[`source_material/ToDo/glm_wheels_bundle`](../source_material/done/glm_wheels_bundle/)
(record `glm_wheels_bundle` in
[`source_material/INTAKE.yaml`](../source_material/INTAKE.yaml)), followed by
its measurement. The item offers two wheels: the **Integer Wheel**
(`integer_wheel.py`, data `oeis_seed.py`: 183 OEIS entries, a prefix of
integers answered with an OEIS identifier) and the **Monster Wheel**
(`monster_wheel.py`, data `cfsg_seed.py`: the Integer Wheel plus the 26
sporadic simple groups by order and by the exponent vector of the order, five
group-theory sequences and the sorted sporadic orders).

The order of work, so the reader can weigh it:

1. *Read first.* The item's code, its two notes and its tests were read, and
   its data listed (identifier, name, first terms). Nothing was put to the GLM
   or to a wheel. Reading the listing showed that several entries carry names
   with question marks or the word *placeholder*, and that some identifiers
   are not the OEIS identifiers of the terms they hold (for instance the
   entry filed as the decimal expansion of the square root of 2 is not
   `A002193`, which is). The Rule 30 centre column the item stores was
   recomputed from the rule and differs from it at the sixth term. That is
   why mark A (§3) exists, and why the control C is not blind: the questions
   of §4 were written by someone who had seen the data.
2. *Then this document*, with the marks and the question set, and the
   question set as data in `glm_universal/wheels/integer_wheel_study.py`
   (the constants `SEQUENCE_QUESTIONS`, `ORDER_QUESTIONS`,
   `PERTURBED_QUESTIONS`, `NONSPORADIC_QUESTIONS` and `OTHER_QUESTIONS`),
   written before the query surface or the ports existed.
3. *Then the code*: the ports, the audit, the query surface, the tests.
4. *Then the measurement* of §7, through the functions named there.

The Lean half — `Wheels/IntegerWheel.lean` and `Wheels/SporadicOrders.lean` —
was written in the same round by the parent of this intake, from the item's
own description; this document checks the Python against it (mark L).

## 1. What is taken, and what is left

Taken: the two wheels' mechanism (`OEISEntry`, `IntegerWheel` with `speak`,
`identify`, `merge`, `turn`, the soundness re-check; `MonsterWheel` with
`find_by_order`, `find_by_factorization`, `find_by_exponent_vector` and the
CFSG Lean-file parser) and their data, ported into
`src/glm_universal/wheels/` as package modules, with a query surface over them
(installed provisionally until the Lean build: §7.4). The network fetch of OEIS b-files stays, opt-in, never at import.

Left in the item: `glm_wheel.py` (the Rule 30 study's verification wheel with
the two wheels wired in; it needs matplotlib and the v16 hypothesis engine,
and its counterpart belongs to `Rule30_GLM_Study`), `bulk_parse_cfsg.py` and
`verify_cfsg_orders.py` (one-off scripts against a local CFSG clone at a path
of the author's machine; the order check they make is mark L's), and the two
notes.

Nothing supplied is relied on before it has passed a gate: an entry of the
data enters the absorbed wheel only if mark A's audit reproduces it (§2).

## 2. The objects

**The provision contract** (proved in `Wheels/IntegerWheel.lean`). An entry
`(id, terms)` speaks its id on a nonempty claim exactly when the claim is a
prefix of its stored terms. The wheel's `speak` is silent on the empty claim;
otherwise it answers from the *exact* matches (stored terms equal to the
claim) when there are any, else from the *prefix* matches, and returns the
least identifier of that tier. Whatever it says is the identifier of an entry
whose stored terms start with the claim (`speak_sound`).

**Soundness against the stored terms is not truth.** A sound wheel never
speaks an id whose *stored* terms fail to start with the claim; it can still
speak a wrong id when the stored terms under that id are not the OEIS
sequence of that id. The contract cannot see that; only a check of the data
against an independent source can.

**The audit** (mark A). An independent reference, written in this round
without reading the item's generators: for each OEIS identifier the round can
recompute, a generator of that sequence from its OEIS offset (closed forms,
recurrences, sieves, exact integer arithmetic for the digits of constants, the
Lucas–Lehmer test for the Mersenne exponents), and a short literal list for
the two famous sequences that cannot be recomputed here (`A000001`, `A000088`).
A supplied entry is **verified** when its identifier has a reference and its
stored terms equal a run of consecutive reference terms; it **disagrees** when
it has a reference and they do not; it is **not recomputed** when no reference
exists. The absorbed wheels hold the verified entries only; nothing is added
and no identifier is changed. The pairing of an identifier with its
definition is the reviewer's knowledge of the OEIS, not a fetch from
oeis.org (there is no network in this round); an entry is admitted only when
that knowledge and the item's author agree term for term.

**The query surface**, `glm_universal.wheels.sequence_query.answer_sequence_query(text)`,
returns `(code, reply)`: `0` answered, `1` a sequence or sporadic-order
question that nothing answers, `2` not such a question. A sequence question is
answered first by `speak` on the claim (the claim is a prefix of the stored
terms); when that is silent and the claim has at least four terms, by the
entry in whose stored terms the claim occurs earliest (a run starting after
the first term), said as such. A sporadic-order question names the word
*sporadic* and an order (an integer or a product of prime powers) and is
answered by `find_by_order`; the reverse question asks the order of a named
sporadic group.

## 3. The marks, declared before the code

| Mark | What is measured | Met when |
|---|---|---|
| A | the audit of the supplied data | every supplied sequence entry (183 of the Integer Wheel and 5 group-theory entries of the Monster Wheel) has a verdict, and the absorbed wheels hold exactly the verified ones (plus the 26 groups by order and by exponent vector, and the sorted sporadic orders under their local id) |
| S1 | soundness | on the whole absorbed data (every prefix of every entry) and on a held-out battery built from the independent reference (runs not at the start, and the same runs with one term changed), every identification the surface makes is true of the *reference* sequence of the spoken id at the stated position |
| S2 | the GLM without the wheels | the 102 questions of S3, put through the real command line `python3 src/GLM.py -q …`, receive the expected identification at most 10 times |
| S3 | the GLM with the wheels | of the 102 questions of §4.1–4.2, at least 85 receive the expected identification and 0 a wrong one |
| S4 | negative controls | all 12 perturbed sequences and all 10 non-sporadic orders are refused (code 1), and all 6 other questions are left alone (code 2) |
| C | the control: the supplied data unfiltered | the S3 and S4 questions are put to the same surface over the supplied, unaudited wheels and the right and wrong answers counted (reported, not passed or failed: it shows what the audit is for) |
| R | the item's own Rule 30 / ARC battery | the battery of `monster_wheel_rule30_arc_test.py` is re-run on the absorbed wheels and the Monster Wheel's additional identifications and the battery integers that are sporadic orders are reported (the item's own run reports 0 and 0: no help there) |
| L | the Lean half | `Wheels/IntegerWheel.lean` and `Wheels/SporadicOrders.lean` are in the build tree, imported by `AxiomAuditAll.lean`, `python3 -m glm_universal.lean_check` passes, and the tests that read them agree with the Python data (the eight `terms…` lists, the 26 names and orders, every `order_…` factorisation) |
| T | no regression | the new modules' tests pass, `tests/test_wheels.py` still passes (the W01–W15 registry is unchanged), and the exactness scan finds no float site in the new modules |

A wrong answer is a reply with code 0 whose first identification is not in
the question's set of acceptable answers (for a reverse question, whose order
is not the expected integer); any code-0 reply to a negative control is
wrong. A refusal is never wrong. The bars of S2–S4 were fixed with the
question set, before any question was put.

## 4. The question set, fixed before the wiring

The questions are the constants of `glm_universal/wheels/integer_wheel_study.py`.
Their expected answers come from the OEIS and the ATLAS as the reviewer knows
them, not from the item's data.

### 4.1 Sequence questions (70)

Seventy questions of the forms *what sequence is …*, *identify the sequence
…* and *which sequence starts …*, over famous sequences: Fibonacci (from 0 and
from 1), primes, powers of 2, Catalan, Bell, factorials, squares, cubes,
fourth powers, triangular, tetrahedral and square pyramidal numbers, Lucas,
Pell, partitions, partitions into distinct parts, Recamán, Kolakoski,
Thue–Morse, the digits of π, e, √2, √3, the golden ratio and ln 2, the Rule 30
centre column, central Delannoy, derangements, Motzkin, both Schröder
sequences, Jacobsthal, composites, highly composite numbers, perfect numbers,
Sylvester's sequence, Mersenne numbers, exponents and primes, primorials,
happy numbers, Stern's diatomic sequence, rooted trees, Ulam numbers, Sophie
Germain primes, squarefree numbers, lcm(1..n), evil and odious numbers, the
continued fractions of e and π, both Wythoff sequences, groups of order n,
graphs on n nodes, ordered Bell numbers, Woodall numbers, ⌊n√2⌋, the centred
cube numbers, the look-and-say lengths, the sums of odd squares, the sorted
sporadic orders, d(n), φ(n), σ(n), double factorials, Narayana's cows and
Padovan.

Eight of them ask for a sequence whose entry, from the listing read in step 1
of §0, the audit is expected to refuse or the item does not hold under its
identifier (√2, √3, the Rule 30 centre column, partitions into distinct parts,
⌊n√2⌋, the centred cube numbers, the look-and-say lengths, the sums of odd
squares): a refusal there is not wrong, and those eight are why the bar of S3
is 85 and not 102.

### 4.2 Sporadic-order questions (32)

The 26 questions *which sporadic group has order N*, one per group (phrased
three ways), two with the order written as a product of prime powers (M11 and
J1), and four reverse questions, *what is the order of …* (the Monster, M24,
the Baby Monster, the Janko group J1).

### 4.3 Negative controls (28)

* **Perturbed sequences (12)**: a famous prefix with one term changed
  (Fibonacci, primes, powers of 2, Catalan, π, Lucas, partitions, triangular
  numbers, Sylvester), the "lost numbers" 4, 8, 15, 16, 23, 42, and two Rule 30
  integer lists of the item's own battery (the period-doubling diagonals and
  the lag profile), which no OEIS entry holds.
* **Non-sporadic orders (10)**: 60, 168, 20160, 7919, 7921, 95041, 1, the
  product 2^4 · 3^2 · 5 · 13, the order of the Monster plus one, and the order
  of a group M13 that does not exist.
* **Other questions (6)**: the capital of France, 2 + 3, a sequence of
  events, the group with the most members, identifying a speaker, the order of
  operations.

## 5. Lean obligations

* `RequestProject.GLM.Wheels.IntegerWheel` — the provision contract:
  `provision_sound`, `provision_complete`, `speak_sound`, `speak_eq_none`,
  `speak_isSome`, `speak_exact` (exact matches first), `speak_least` (the
  least identifier of the chosen tier), `merge_keeps`, `mem_merge`,
  `merge_self`, `merge_speak_sound`; and the eight closed-form entries
  (`A000045`, `A000032`, `A000142`, `A000108`, `A000040`, `A000079`,
  `A000290`, `A000217`) equal to their closed forms.
* `RequestProject.GLM.Wheels.SporadicOrders` — the 26 sporadic orders, each
  equal to its prime factorisation (`order_M11` … `order_M`), the orders and
  the names distinct, and `findByOrder` sound and complete.

## 6. What this round does not do

* It does not fetch anything from oeis.org: the audit's pairing of an
  identifier with a definition is the reviewer's, and the opt-in fetch is
  left unused.
* It does not correct or relabel the supplied data: an entry that disagrees
  with the reference is held out of the absorbed wheel, not rewritten, and the
  supplied files stay as supplied.
* It does not wire the surface into `GLM.py`, `runtime/` or `tools.py`; the
  integration names the function to wire.
* It does not take `glm_wheel.py`, which belongs to `Rule30_GLM_Study`.
* It does not run `lake build`; the Lean build is the owner's, through
  `scripts/rebuild_lean.sh`.

## 7. The measurement

*Measured 31 October 2026 by
`glm_universal.wheels.integer_wheel_study.integer_wheel_report()` (all marks;
S2 runs the real command line, so a full run takes a minute or two; the
module's `__main__` prints the marks). The query surface measured is
`glm_universal.wheels.sequence_query.resolve_query`, the function behind
`answer_sequence_query`.*

### 7.0 What happened between §6 and the measurement

The ports, the audit, the query surface and the tests were written after
§§0–6, in that order. While the surface was being written it was tried on the
three example questions of the brief, which are questions of §4 (Q01, Q03 and
G01), and Q01 and G01 were put to the command line, which refused both. It was
also tried on probes outside the question set; one of them, *what is the order
of the B-tree*, it read as the Baby Monster, and the reading of a group's name
was narrowed before the measurement (a name that is also an everyday word or a
surname, or an identifier without a digit such as `B` or `He`, is read as a
group only when the question says *sporadic* or writes the name before
*group*). No question, expected answer or bar of §§3–4 was changed.

### 7.1 The verdict

Yes, for these two kinds of question: with the audited wheels the GLM's query surface answers 89 of the 102 pre-registered questions right and 0 wrong (57 of the 70 sequence questions and all 32 sporadic-group questions), where the GLM's command line without them answers 0 of them; all 28 negative controls are refused or left alone, and no soundness check finds a false identification. The supplied data unaudited would have answered 6 of the questions wrongly, and on the item's own Rule 30 / ARC battery the Monster Wheel adds 0 identifications and finds 0 sporadic orders: no help there.

The deciding figure: 89 of 102 questions answered right and 0 wrong with the
wheels (bar: at least 85, 0 wrong), against 0 of 102 through the command line
without them; 28 of 28 negative controls refused or left alone; 0 false
identifications in 8517 soundness checks.

### 7.2 The marks

| Mark | Bar (§3) | Measured | Met |
|---|---|---|---|
| A | every supplied entry has a verdict; the absorbed wheels hold exactly the verified ones | 188 supplied sequence entries (183 + 5), 188 verdicts: 109 verified, 33 disagree, 45 not recomputed, 1 short reference (`A001220`: the reference has the 2 known Wieferich primes and the item stores a third term, 1549333177, which is not even prime: it is divisible by 7); the absorbed Integer Wheel holds the 107 verified entries of the 183, the absorbed Monster Wheel 161 entries (those 107, `A000688`, the 26 groups, their 26 exponent vectors and the sorted orders; `A000001` is verified in both seeds with the same terms); the frozen list equals the live audit | yes |
| S1 | no identification false of the reference | 3652 stored prefixes through `speak`: 0 silent, 0 false; 3382 surface questions on the stored prefixes of three terms or more and on the 26 orders: 0 false, 0 unjudged; 1483 held-out claims (runs at positions 1, 3 and 6 of four and six terms, and each with its last term raised by one): 622 answered, 0 false, 0 unjudged. 8517 checks in all | yes |
| S2 | at most 10 of the 102 right through `python3 src/GLM.py -q` | 0 of 102 right; all 102 exit 1: 96 "unrecognised query", the 4 reverse questions "names no carrier in any enabled domain", the 2 product-form order questions refused by the stepwise planner | yes |
| S3 | at least 85 of the 102 right and 0 wrong | 89 right (57 of 70 sequence, 32 of 32 sporadic-group), 0 wrong, 13 refused | yes |
| S4 | 12 perturbed and 10 non-sporadic refused, 6 others left alone | 12 of 12 refused, 10 of 10 refused, 6 of 6 left alone; 0 wrong | yes |
| C | reported | the supplied, unaudited wheels (240 entries): 91 right, 6 wrong, 5 refused on the 102; 0 wrong on the 28 controls; 59 false identifications on the held-out battery (88 unjudged), and 395 stored prefixes spoken under an identifier whose reference they are not | reported |
| R | reported (the item's run: 0 and 0) | 21 sequences, 59 distinct integers. Absorbed wheels: the Integer Wheel speaks on 8, the Monster Wheel on the same 8, 0 additional identifications, 0 battery integers that are sporadic orders. Supplied wheels: 11 and 11, 0 additional, 0 orders | reported |
| L | both files built, audited, statically checked, and agreeing with the Python data | both in the build tree and imported by `AxiomAuditAll.lean`; `python3 -m glm_universal.lean_check` passes; all 24 named theorems stated; 8 of 8 `terms…` lists equal to the Python entries' first terms (and to their closed forms, recomputed); the 26 names and orders equal, in order; 26 of 26 `order_…` statements agree with the Python order, its factorisation and its exponent vector. The Lean build itself is confirmed only by the owner's rebuild log (`scripts/rebuild_lean.sh`); here the check is static | yes |
| T | the new tests and `tests/test_wheels.py` pass; W01–W15 unchanged; no float site | `python3 -m unittest` over `tests/test_integer_wheel.py` (46), `tests/test_monster_wheel.py` (24) and `tests/test_wheels.py` (34): 104 tests, OK; the 15-wheel registry unchanged, `PROVISION_WHEELS` (`IW`, `MW`) beside it; no float site in the nine new modules | yes |

### 7.3 What was seen

**The 13 refusals.** The 8 of §4.1, all refused as expected (√2, √3, the
Rule 30 centre column, partitions into distinct parts, ⌊n√2⌋, the centred cube
numbers, the look-and-say lengths, the sums of odd squares), and 5 that were
not predicted: central Delannoy (Q23), large Schröder (Q26), little Schröder
(Q27), rooted trees (Q40) and the Fubini numbers (Q55). The supplied terms of
each are right at first and then wrong — central Delannoy at stored term 11
(45225831 for 45046719), large Schröder at term 11, little Schröder and Fubini
at term 12, and the rooted trees, whose stored list starts at one node, at
stored term 16 even read from there — so the audit held them out and the
surface refused. A refusal is not wrong; the five are why the count is 89 and
not 94.

**How the 89 were answered.** Of the 57 sequence answers, 51 came from
`speak` (the claim is a prefix of the stored terms) and 6 from the run search,
each reply saying where the claim starts: Fibonacci from 1 (Q01), the cubes
from 1 (Q09), 2^n − 1 from 1 (Q34), Catalan without its first term (Q65), the
tetrahedral numbers from 1 (Q67) and the square pyramidal numbers from 1
(Q68). The 32 sporadic-group answers came from `find_by_order` (G01–G28, the
two product forms G27 and G28 included) and from the reverse reading
(G29–G32).

**What the audit is for.** Control C's 6 wrong answers are the supplied
data's mislabels: Q01 answered `A000009`, whose supplied entry ("partitions
into odd parts") stores the Fibonacci numbers after its first term; Q19
answered `A010505`, the item's identifier for the digits of √2 (the OEIS has
`A002193`); Q20 answered `A002193`, which the item uses for √3; Q21 answered
`A000447`, the item's identifier for n⁴ (the OEIS has `A000583`); Q59 answered
`A001155`, the item's identifier for the look-and-say lengths (the OEIS has
`A005341`); Q61 answered `A001034`, the item's identifier for the sorted
sporadic orders (`A001034` is the orders of the noncyclic simple groups; the
OEIS has the sporadic orders as `A001228`, and the absorbed wheel keeps them
under the local identifier `CFSG-SPORADIC-ORDERS`). Every one of these is sound
against the stored terms — the contract of `Wheels/IntegerWheel.lean` holds for
the supplied wheel too — and false of the sequence the identifier names, which
is the distinction §2 drew.

**The item's own battery.** The Monster Wheel adds nothing to the Integer
Wheel there, on the absorbed data as on the supplied: the same 8 (absorbed) or
11 (supplied) of the 21 sequences are spoken, and none of the 59 integers is a
sporadic order. Two of the supplied wheels' three extra
identifications are the item's Rule 30 centre-column lists spoken as
`A051023` — but those lists differ from Rule 30, run from a single cell, at
term 5, so the identification is false; the third is the triangular numbers
from 1 spoken as `A005583`, an entry the reference cannot check. The query
surface answers 12 of the 21 with 0 false identifications, all of them
ordinary sequences (powers of 2 and 3, the squares and the odd numbers from
their second term, the counting numbers, Catalan, triangular, Fibonacci,
primes, 2^n − 1): the Integer Wheel's doing, not the Monster Wheel's. No help
there, as the item itself reported.

**The Lean half against the Python.** No disagreement: the eight lists, the 26
names and orders and every factorisation read out of the two Lean files equal
the Python data. The tests `tests/test_integer_wheel.py` and
`tests/test_monster_wheel.py` read the files through
`glm_universal.wheels.lean_wheel_data` on every run, and they also check that
the Python `speak` is the Lean `speak` (exact tier first, least identifier,
silent on the empty claim and on no match) on every stored prefix of the
absorbed Monster Wheel, each prefix with its last term changed and the
held-out battery, and that `find_by_order` is the Lean `findByOrder`.

### 7.4 What was taken — provisionally

**Status, 31 October 2026: installed provisionally, awaiting the owner's Lean
build.** The modules below were ported, tested and measured in this round and
are in `src/glm_universal/wheels/`, where the GLM answers from them. Their
Lean files, `Wheels/IntegerWheel.lean` and `Wheels/SporadicOrders.lean`, are
written, statically checked and imported by the axiom audit, but no build has
confirmed them yet; the owner decided to keep the wheels "in the wheels folder
now, clearly marked provisional until my Lean build log confirms them". So the
intake item stands at *Lean written* in `source_material/ToDo/`, its wheel
parts are recorded `provisional`, the register
`src/glm_universal/wheels/_data/provisional.json` names the item, and every
answer that rests on these wheels says so: a sequence or sporadic-order answer
of `python3 src/GLM.py -q` ends with a bracketed *provisional* note, and
`ProvisionWheel.status` reads it. When `scripts/rebuild_lean.sh` passes,
`python3 -m glm_universal.intake advance glm_wheels_bundle absorbed` checks the
build record against both files and everything they import, runs every named
test again, marks the parts absorbed, removes the register entry and files the
item in `source_material/done/`.

`glm_universal.wheels.integer_wheel`, `monster_wheel`, `oeis_seed`,
`cfsg_seed`, `cfsg_import` and `factorint` (the item's files, ported; data
unchanged), with `oeis_reference` (the audit), `lean_wheel_data` (the Lean
statements read back), `sequence_query` (the surface) and `integer_wheel_study`
(this measurement); registered in `glm_universal.wheels` as the separate family
`PROVISION_WHEELS`. The function the GLM's query surface calls is
`glm_universal.wheels.sequence_query.answer_sequence_query(text) -> (code,
reply)`: code 0 answered, 1 a sequence or sporadic-order question nothing
answers, 2 not such a question. The item's supplied files are left as
supplied.

### 7.5 What is left

* Since the measurement the surface is wired into the command line as the
  `sequence` lookup kind (parser rule 0). S2 is the GLM *without* the wheels,
  so `glm_universal.wheels.integer_wheel_study.mark_s2` now runs `src/GLM.py`
  with that kind switched off in the subprocess (`WITHOUT_WHEELS`), and it
  still gives 0 of 102. With the wheels, the same 102 questions through
  `python3 src/GLM.py -q` give 89 right, 0 wrong and 13 refused — the
  surface's own figures (`glm_universal.wheels.integer_wheel_study.wired_cli`,
  31 October 2026).
* Five famous sequences of the question set (central Delannoy, both Schröder
  sequences, rooted trees, Fubini) and the eight of §4.1 stay unanswered until
  entries for them are supplied and pass the audit; the 45 entries without a
  reference stay out until a reference is written for them.
* The Lean build of `Wheels/IntegerWheel.lean` and `Wheels/SporadicOrders.lean`
  is the owner's to confirm (`scripts/rebuild_lean.sh`); until it does, the
  wheels are installed provisionally and say so (§7.4).
