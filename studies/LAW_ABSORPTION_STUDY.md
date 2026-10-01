# The UBP laws absorbed — each law tested, improved where it can be, and put to use

## Tier 0 — the coarse read

**Question.** Which of the sixty-five retained UBP laws, tested one by one and corrected where they overclaim, can the GLM actually use, and does using them make it reason better?

**Verdict.** Eleven laws are absorbed as computed self-knowledge of the substrate: questions the GLM refused before this round are now answered from the running code. Two were already GLM definitions, three were retested in dimensionless form and refused, and forty-nine are retired with a reason each.

**Deciding figure.** 36 of 36 declared substrate questions answered or refused as declared through the typed planner, 0 wrong, against 0 answered before the round; 0 of 4687 existing evaluation texts read by the new frame; 8 of 8 marks met.

**Recomputed by.** `glm_universal.reasoning.law_absorption.law_absorption_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Why this round, and what it is not

Phase 74 ([`LAW_REGISTER_STUDY.md`](LAW_REGISTER_STUDY.md)) re-graded the 65
laws of `source_material/retained_laws_verified_65.csv` and built a refusal
test for numeric coincidences. The owner's intention for the law register was
different: **not** another sub-system for the GLM to consult, but to take the
laws **one at a time** — test each, improve it where it can be improved, and
absorb it into the GLM wherever it is of real use.

Phase 74 did the testing. What it did not do is the absorption: after it, the
GLM — whose substrate *is* the extended Golay code and the Leech lattice —
still refused *how many codewords does the Golay code have?*, *what is the
minimum distance of the Golay code?*, *what is the kissing number of the Leech
lattice?* and *can the Golay decoder correct 4 bit errors?* (all four were run
through `GLM.py --ask` at the start of this round and every one came back
`UNSOLVED`). The laws that hold are exactly statements of that kind. This
round makes each surviving law — in its corrected form — something the GLM
**computes and answers from its own substrate**, with the law cited as the
provenance of the answer, and closes the book on the rest with a reason per
law.

## 1. Declarations — written before any code of this round

### 1.1 One fate per law

Every one of the 65 laws gets exactly one fate:

| fate | meaning |
|---|---|
| **absorbed** | the law, in its corrected form, is now a question the GLM answers by computing from the running substrate (never a stored string), and the answer cites the law |
| **already GLM** | the law is a definition the GLM already runs on; the module attribute is named |
| **retested** | the law was unit-bound; its dimensionless content is extracted and re-run through Phase 74's look-elsewhere test with a declared template |
| **retired** | nothing in it is usable at GLM resolution; the reason is named (and it is the Phase 74 reason unless this round found a new one) |

**A1.** Every one of the 65 laws has exactly one fate, and every absorbed law
names at least one fact of §1.2 that it is absorbed as.

### 1.2 The facts the absorbed laws become

Each fact is computed live from the substrate when asked. The corrected law is
the fact; the original wording is kept only as provenance.

| fact | computed from | laws |
|---|---|---|
| `codewords` — number of codewords | the 4,096 codeword masks | `COMP_009` |
| `rate` — information rate | the codeword count and the length | `COMP_009` |
| `weight-count` — codewords of a given weight (octads, dodecads, …) | weights of the codeword masks | `RELATION_ORTHO_001` |
| `min-distance` — minimum distance | least nonzero codeword weight (the code is linear) | `RELATION_002` |
| `covering-radius` | the largest coset-leader weight of the coset table | `FOURTH_FLIP_001` |
| `corrects` — errors always corrected | the decoder outcome table | `COMP_005` |
| `outcome` — what complete decoding does with `k` bit errors | the decoder outcome table (right / refused / wrong counts out of `C(24, k)`) | `COMP_005`, `FOURTH_FLIP_001` |
| `probability` — chance the decoder is right / refuses / is wrong at bit-flip rate `p` | exact polynomial in `p` | `STORAGE_HARDENED_001` (corrected) |
| `confidence` — chance a decoding at distance `d` is the sent codeword, at rate `p` | the coset weight enumerator of weight `d` | `FOURTH_FLIP_001`, `COMP_005` |
| `unique-fraction` — share of 24-bit words that decode uniquely | the coset table | `GATEWAY_002`, `GOLAY_UNIQUENESS_001` |
| `perfect` — whether the code (or its length-23 puncture) is perfect | sphere counts | `GOLAY_UNIQUENESS_001` |
| `kissing` — kissing number of the Leech lattice, by shape | enumeration of the minimal vectors | `KISSING_EXPANSION_001` |
| `closure` — whether XOR / AND / OR of two codewords is a codeword | linearity, and the census over all octad pairs | `LOGIC_GEO_001` (corrected) |
| `descent` — whether greedy descent reaches the nearest codeword in `d` steps | the exhaustive descent census | `PATH_LEAST_ACTION` (corrected) |

**A2.** Every fact is reachable from `GLM.py --ask`, through the typed
planner, by at least one declared question, and the value it gives equals the
Phase 74 figure or the Lean theorem it rests on.

### 1.3 The declared question set

`glm_universal/evaluation/law_absorption_cases.py`, committed before the
planner frame: questions in plain English, each with its declared outcome —
an expected value, or a refusal (a bit-flip rate outside `[0, 1]`, an error
weight outside `0 … 24`, a confidence asked at distance 4 where six codewords
tie).

**A3.** Every declared question is answered or refused as declared, with 0
wrong answers. The control: before the round, the planner answers none of
them (each was `UNSOLVED` or answered by a different, non-substrate reading).

**A4.** The new frame reads no question of the existing evaluation: the 177
contract cases, the connected-machine route table and the held-out sets keep
their verdicts, because the frame reads only a text that names the substrate
(`golay`, `leech`, `codeword`, `octad`, `dodecad`, `decoder`) *and* has one of
its declared shapes. `address of golay` and `golay` stay with the planner's
existing readings.

### 1.4 The corrections, proved

**A5.** The corrected storage law, in Lean
(`RequestProject/GLM/LawAbsorption.lean`): with each of the 24 bits flipped
independently at rate `p`, the probability that complete decoding is right is
**strictly less than 1 at every `0 < p < 1`** and equal to 1 at `p = 0`; what
*does* hold without exception is the worst-case form — every error pattern of
at most three flips is corrected, and some pattern of four is not.

**A6.** The decoder's refusal and its confidence, in Lean: at every
`0 < p < 1/2`, the unique coset leader is strictly the most probable error in
its coset (so complete decoding is the maximum-a-posteriori decision), and two
leaders of the same weight are exactly equally probable (so at a six-way tie
no choice is licensed). In Python, the `confidence` fact is checked by brute
force — summing over all 4,096 codewords — on declared received words.

### 1.5 The unit-bound laws, retested

Three unit-bound laws have a dimensionless content that can be extracted:

| row | dimensionless claim | template | slots | target |
|---|---|---|---|---|
| `LAW_FORCE_003` | `m_W/m_Z = 21/24` (the `1/Y` cancels) | `a/b` | a 1–24, b 1–24 | 80.377/91.1876 (PDG 2022) |
| `LAW_FORCE_005` with `LAW_FORCE_003` | `m_H/m_Z = (33 + 1/9)/24` (the `1/Y` cancels) | `(a + 1/b)/c` | a 1–48, b 1–24, c 1–24 | 125.25/91.1876 (PDG 2022) |
| `LAW_CHEM_002` | the water bond angle as a fraction of a turn, `(83(1+Y) − Y/2 − 1/(10Y))/360` | `(a(1+Y) − Y/b − 1/(cY))/360` | a 1–120, b 1–24, c 1–24 | 104.45/360 |

**A7.** Each is decided by Phase 74's look-elsewhere test, unchanged:
admitted when the chance coverage is below `1/100`, refused otherwise. The
other four unit-bound rows (`H0` in km/s/Mpc, `G` in SI, a period in seconds,
an MeV gap resting on the knowledge base's own energy unit) carry a free
scale that no ratio inside the row removes, and are retired.

### 1.6 Lean

**A8.** `RequestProject/GLM/LawAbsorption.lean` builds with no `sorry` and
only the standard axioms.

---

## 2. Results

**Summary.** Eleven laws are absorbed as computed self-knowledge of the substrate: questions the GLM refused before this round are now answered from the running code. Two were already GLM definitions, three were retested in dimensionless form and refused, and forty-nine are retired with a reason each.

Recomputed by `glm_universal.reasoning.law_absorption.law_absorption_report`
(`PYTHONPATH=. python3 -m glm_universal.tools law-absorption`); pinned by
`tests/test_law_absorption.py`; the corrections are theorems of
`RequestProject/GLM/LawAbsorption.lean`. All 8 of 8 marks met.

### 2.1 One fate per law (A1)

| fate | n |
|---|---|
| absorbed | 11 |
| already GLM | 2 |
| retested | 3 |
| retired | 49 |

The eleven absorbed laws are exactly the eight Phase 74 filed *structural*,
the two it filed *overclaimed* (in corrected form), and
`STORAGE_HARDENED_001` (in corrected form) — the test pins that. One change
from the declaration: `RESOLUTION_GAP_001` was expected to be *already GLM*,
but no GLM computation uses `ln φ / ln π` (its only uses were the near-miss
and a refused formula of the register itself), so it is **retired**; the
declared tier-0 count moved from three to two accordingly.

| law | fate | the GLM statement, or the reason | facts |
|---|---|---|---|
| `COMP_005` | absorbed | complete decoding is right exactly on errors of weight at most 3 (not only 1) | `corrects`, `outcome`, `confidence` |
| `COMP_009` | absorbed | the code has 2^12 of 2^24 words: rate 1/2 | `codewords`, `rate` |
| `FOURTH_FLIP_001` | absorbed | a weight-4 error always lands on a six-way tie and is refused; the covering radius is 4; a decoding at distance d ≤ 3 is right with a computable probability | `covering-radius`, `outcome`, `confidence` |
| `GATEWAY_002` | absorbed | 2325 of 4096 cosets decode uniquely | `unique-fraction` |
| `GOLAY_UNIQUENESS_001` | absorbed | the length-23 code is perfect, the extended code is not (1771 cosets tie) | `unique-fraction`, `perfect` |
| `KISSING_EXPANSION_001` | absorbed | 196560 = 1104 + 97152 + 98304 minimal Leech vectors, by shape | `kissing` |
| `LOGIC_GEO_001` | absorbed | corrected: XOR is a code operation, AND and OR are not | `closure` |
| `PATH_LEAST_ACTION` | absorbed | corrected: greedy descent does not reach the nearest codeword in d steps (792 cosets) | `descent` |
| `RELATION_002` | absorbed | the minimum distance is 8 | `min-distance` |
| `RELATION_ORTHO_001` | absorbed | the weight distribution 1, 759, 2576, 759, 1 | `weight-count` |
| `STORAGE_HARDENED_001` | absorbed | corrected: integrity is certain for every pattern of at most 3 flips per word, and never certain at a positive random bit-flip rate; the exact probabilities are computed | `probability`, `always-right` |
| `LEECH_TAX_001` | already GLM | `glm_universal.reasoning.coherence.tax_shell0` | |
| `METRIC_002` | already GLM | `glm_universal.reasoning.coherence.Y` | |
| `CHEM_002` | retested | §2.5 — refused | |
| `FORCE_003` | retested | §2.5 — refused | |
| `FORCE_005` | retested | §2.5 — refused | |

The 49 retired laws, by reason: 17 external formulas refused by the
look-elsewhere test; 2 external formulas admitted at their templates but
missing the measured m_μ/m_e by 158 and 13204 standard deviations
(`LEPTON_001`, `PHYSICS_MUON_002` — approximations no GLM computation needs);
14 knowledge-base-internal numbers; 4 unit-bound rows with a free scale (§1.5);
4 duplicates; 3 bounds, ranges or uncertainties; 1 textbook restatement
(`WEAK_ISOSPIN_001`, m_W/m_Z = cos θ_W — true, and not the register's); and
4 exact rows with nothing to use (`ARX_HORIZON_006` and `LEECH_TENSION_001`,
arithmetic; `INTERFACE_CLOSURE_001`, a near miss; `RESOLUTION_GAP_001`, a
definition nothing uses). `tools law-absorption --law ID` prints any one
law's fate and reason.

### 2.2 The facts, and what the GLM now says (A2)

Every fact of §1.2 is reached by at least one declared question and agrees
with the Phase 74 figure or the Lean theorem it rests on (minimum distance 8,
covering radius 4, corrects 3, unique fraction 2325/4096, kissing number
196560 = 1104 + 97152 + 98304 by enumeration, 4096 codewords, and the 3%
storage figure 0.005321). Asked through `GLM.py --ask`:

```
QUERY   What is the kissing number of the Leech lattice?
PLAN    substrate
ANSWER  196560 = 1104 (+-4^2, 0^22) + 97152 (+-2^8 on an octad) + 98304 (-+3, +-1^23)
        -- enumerated from the substrate's Leech construction
        (Lean: leechMinimalClass_counts) [absorbed from LAW_KISSING_EXPANSION_001]

QUERY   can the golay decoder correct 4 bit errors?
PLAN    substrate
ANSWER  refused: every such error lands on a six-way tie and the decoder refuses
        rather than guess -- of the 10626 patterns of 4 flips, 0 right, 10626
        refused, 0 wrong [absorbed from LAW_COMP_005, LAW_FOURTH_FLIP_001]
```

Every answer carries the law it was absorbed from; no answer is a stored
string — each is computed from the codeword masks, the coset table, the Leech
construction or the descent census when it is asked.

### 2.3 The declared questions (A3, A4)

36 of 36 answered or refused as declared (31 answers, 5 named refusals:
`WEIGHT_OUT_OF_RANGE` twice, `NOT_A_PROBABILITY`, `TIE`,
`BEYOND_COVERING_RADIUS`), 0 wrong — both by the module's own reader and
through the typed planner itself. **Control:** the same planner with the
`substrate` frame removed — the planner as it stood before this round —
answers 0 of the 36.

**One declared value amended.** Case `s16` (the chance the decoder is right at
3%) was declared as `0.994678`, copied from Phase 74's table, which truncates;
the exact value 0.99467897… rounds half-even — the case file's own rule — to
`0.994679`. The GLM's answer was right and the declaration wrong; the case is
amended in place with a comment, and this is the only amendment.

**Nothing else moved (A4).** The frame reads none of the six declared
near-misses (`golay`, `address of golay`, `describe golay`, a Python
expression, two report requests), and none of the **4687** string literals of
every other evaluation module (the contract cases, the connected-machine route
table, the held-out sets and the stepwise and reverse corpora).

### 2.4 The corrections, proved (A5, A6)

`RequestProject/GLM/LawAbsorption.lean`:

* `total_prob`: the pattern probabilities `p^wt · (1−p)^(24−wt)` sum to 1.
* `right_prob_lt_one`, `right_prob_eq_one_iff`: the right-probability of
  complete decoding is below 1 at every `0 < p < 1` and equal to 1 exactly at
  `p = 0` — the storage law's "100% at noise ≤ 3%" holds at no positive rate.
* `worst_case_integrity`: every pattern of at most three flips is corrected,
  some pattern of four is not — the form of the storage law that is true.
* `leader_most_likely`: below rate 1/2 the unique leader is strictly the most
  probable error of its coset — complete decoding is the maximum-a-posteriori
  decision, so the `confidence` fact is the posterior of the decoder's own
  answer.
* `tie_posterior_le_sixth` (with `equal_weight_equal_prob`): at a weight-4
  coset each tied codeword has posterior at most 1/6 — the refusal is the
  only licensed answer.
* **Not declared, found, proved:** `odd_error_never_refused` and
  `odd_heavy_miscorrected`. Every codeword has even weight, so a coset has one
  parity, and a six-way tie is reached only by an **even** error; every odd
  error of five or more flips is miscorrected without warning. The outcome
  table computed live shows it for every weight: 5, 7, 9, …, 23 all *wrong*;
  4 and 20 all *refused*; the other even weights *mixed*. This sharpens the
  register's "fourth flip": the deep hole is entered only by an even number
  of flips, and the GLM's `outcome` answer now says so.

The `confidence` fact agrees exactly with a brute-force sum over all 4096
codewords on declared received words at distances 0–3 and rates 1/100 and
1/10 (A6): at rate 1/100 a decoding at distance 3 is right with probability
0.99786, at rate 1/10 with probability 0.77755.

### 2.5 The unit-bound laws, retested (A7)

| row | dimensionless claim | value | target | error | members | chance coverage | verdict |
|---|---|---|---|---|---|---|---|
| `FORCE_003` | m_W/m_Z = 21/24 | 0.875000 | 0.881446 | 0.7313% | 576 | 0.9077 | refused |
| `FORCE_005` | m_H/m_Z = (33 + 1/9)/24 | 1.379629 | 1.373542 | 0.4432% | 27,648 | 0.9925 | refused |
| `CHEM_002` | water angle / turn | 0.290160 | 0.290138 | 0.0075% | 69,120 | 0.4705 | refused |

(values truncated, as Phase 74 displays them). The improvement is real — the
two boson laws lose their free GeV scale once `1/Y` cancels in the ratio, and
the bond angle's 360 is a fixed factor that the coverage ignores — but what
remains is a rational or a three-slot template, and each hits a random target
as closely half the time or more. None is admitted.

## 3. What this round moved

Against the standing target ([`PROJECT_DIRECTIVES.md`](../PROJECT_DIRECTIVES.md),
[`ITERATE.md`](../ITERATE.md) §5): **derivation**, first. Thirty-one questions
about the GLM's own substrate — its code, its decoder, its lattice — that the
planner refused before are now answered by computing from the running
substrate, with the law each answer was absorbed from named in it; none is a
stored string. **Refusal**, second: five named refusals where the question is
outside the fact's domain, and the six-way tie refused with a proof that no
choice among the six is licensed. Nothing else the GLM answers changed.

**What the laws gave.** The structural laws were already GLM mathematics
(Phase 74); what they had not been is *usable* — the GLM could not say them.
Two of them, corrected, gave the GLM something it did not have at all: the
exact probability of each decoding outcome at a noise rate, and the
confidence of a decoding at a given distance. Absorbing the decoder laws also
turned up one statement none of them made — an odd error is never refused —
which is now proved and said.

**Negative results kept.** 49 of the 65 laws are retired; the three
dimensionless retests are refused; `RESOLUTION_GAP_001` turned out not to be
a GLM definition after all; one declared value was wrong and is recorded as
such.

**Not done.** The 106 `UNRESOLVED-UBP` laws and the knowledge base itself
(`ubp_system_kb.json`) are still not supplied; the confidence fact is answered
as a question but not yet attached to the decoder's own readings inside the
runtime (the carried fork and the second reading still report a decoding
without it) — that is the next place the absorbed law would be of use. *Taken by Phase 77: the confidence is now attached to the decoder, the
carried fork's context stage and the second reading at a declared rate
([`DECODER_CONFIDENCE_STUDY.md`](DECODER_CONFIDENCE_STUDY.md)).*
