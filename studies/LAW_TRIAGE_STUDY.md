# The 106 unresolved laws triaged — a law comes in only if it does measurable work

## Tier 0 — the coarse read

**Question.** Do any of the 106 laws the law review left unresolved give the GLM a measurable service it does not already have?

**Verdict.** No. None of the 106 laws passes the service rule, so none is absorbed: three are already served by code the GLM runs, three are refuted by computation from the substrate, and one hundred are retired with a reason each — most because they rest on a pipeline the GLM does not implement or make claims about the world it cannot observe.

**Deciding figure.** 5 of 5 marks met; 106 laws: 0 absorbed, 3 already served, 3 refuted, 100 retired (42 PIPELINE, 31 WORLD, 12 NUMEROLOGY, 12 UNDERSPECIFIED, 1 DEFINITION, 2 DUPLICATE); 8 of 8 declared checks as declared.

**Recomputed by.** `glm_universal.reasoning.law_triage.law_triage_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

Candidate P of [`STATUS.md`](../STATUS.md) §3.4, item **P2**. The law review
(`source_material/UBP_LAW_GLM_REVIEW.md`, Round 2 §6) filed 106 of the
knowledge base's 426 `LAW` rows as `UNRESOLVED-UBP`: *lives in a UBP pipeline
the GLM does not implement*. Phases 74–75
([`LAW_REGISTER_STUDY.md`](LAW_REGISTER_STUDY.md),
[`LAW_ABSORPTION_STUDY.md`](LAW_ABSORPTION_STUDY.md)) dealt with the 65
strongest retained laws; the 106 were never read one by one.

The owner's instruction for this round: the knowledge base is available (the
file `GLM-main/long_term_memory/ubp_system_kb.json`, inside
`source_material/GLM-main.zip`), and its laws **are not to become large parts
of the GLM unless they provide a measurably useful service**. So the default
fate of a law here is *retired with a reason*; a law is absorbed only by
passing the service rule below.

**The 106, frozen.** `reasoning/_data/unresolved_laws_106.json` holds the 106
rows (id, text, tags, vector, math) — the `LAW` rows of the knowledge base not
named in the review's verdict lists (§6 to §8) and whose text is not *No
definition* — with the knowledge base's SHA-256 and size, and the 14 carrier
vectors of the elements and particles some laws name. It was frozen in Phase
81's commit, before this study.

**Scoping, declared.** The laws were read, and a handful of the checks in §1.3
were tried by hand, before these declarations were written. So the fates are
not blind predictions; what the marks test is that every fate is stated, every
check is computed by the module from the substrate, and every *already served*
names code that runs.

## 1. Declarations — written before the module that measures them

### 1.1 The service rule

A law is **absorbed** only if all three hold:

* **S1 — computable.** Its content, corrected if needed, is a statement the
  GLM can compute from its own substrate (the extended Golay code, the Leech
  lattice, the decoder, the coherence measures), with no constant, pipeline or
  data outside the GLM.
* **S2 — new.** The GLM does not already compute it.
* **S3 — useful.** Absorbing it makes the GLM answer a declared question it
  refused before, or improves a declared figure of an existing study.

### 1.2 One fate per law

| fate | meaning |
|---|---|
| **absorbed** | passes S1–S3 |
| **already served** | the law's usable content (S1) is something the GLM already computes (fails S2); the callable is named and run |
| **refuted** | the law's substrate content is computable and the computation contradicts it |
| **retired** | fails S1, with one reason: **WORLD** (a claim about physical, biological, chemical, engineering or cosmological phenomena, which the GLM cannot observe), **PIPELINE** (rests on a UBP pipeline or data the GLM does not implement — the 256-dimensional bulk, the NoiseALU, SHA-256 coordinates, runes, BitTab, BitLumen, TGIC, CARFE and the like), **NUMEROLOGY** (a numeric coincidence built on knowledge-base constants; Phase 74's look-elsewhere test is where such numbers go, and none of these carries a declared template), **UNDERSPECIFIED** (not defined enough to compute), **DEFINITION** (a definition no GLM computation uses), **DUPLICATE** (a verbatim copy of another row) |

### 1.3 The computed checks

Each check is computed by the module, exactly, from the running substrate;
the carriers are read with character `i` of the knowledge-base string as
coordinate `i` (under that reading every one of the 14 carriers is a Golay
codeword, as the review found for the elements).

| law | the substrate content | check | declared fate |
|---|---|---|---|
| `LAW_HEMISPHERIC_COHERENCE_001` | "below 2% noise objective, above 5% a cliff with 51% success", read as the decoder's `P(dH ≤ 3)` | exact P(right) at 1/50, 1/20, 1/10, and the least rate on a declared grid where it falls below 51% | refuted |
| `LAW_PARTICLE_6D` | electron and positron within the correction radius (d ≤ 3), lepton–quark pairs at the deep hole (d = 4) | Hamming distances between the carriers | refuted |
| `LAW_LEPTON_004` | a "Norm2 = 2" shell of the Leech lattice | the least nonzero norm of the Leech lattice, true scale | refuted |
| `LAW_COSMO_003` | a 54.56% even-weight bias | the even-weight fraction of all words and of the code | retired, WORLD |
| `LAW_DODECAD_DUALITY_001` | Neon ⊕ Photon is a dodecad | the weight of the sum and whether it is a codeword | already served |
| `LAW_TOPOLOGICAL_COMPLETION_001` | tax(16) = tax(9) + tax(7) | shell-0 tax of weight-`w` carriers | already served |
| `LAW_SQUEEZE_001` | a 24-bit state as a 15-bit coordinate | read as the decoded 12-bit message plus the 3-bit coset weight; the round trip recovers the codeword exactly when the coset weight is at most 3 | already served |
| `LAW_BIO_HYSTERESIS_001` | a state at `d = 0` survives more stress than one at `d = 3` | the least number of further flips that makes decoding fail from distance `d` | retired, WORLD (the code content is already served) |

### 1.4 The marks

**B1 — one fate per law.** Every one of the 106 frozen rows has exactly one
fate and, if retired, exactly one reason; no fate is given to an id outside
the 106.

**B2 — the checks.** Every check of §1.3 is computed and its outcome is the
declared fate.

**B3 — already served, run.** Every *already served* names a GLM callable that
imports and, run on the law's content, returns the value the law needs.

**B4 — absorption.** Every absorbed law passes S1–S3 with its question named.
*Declared expectation, not a mark:* none is absorbed.

**B5 — the source.** Where `source_material/GLM-main.zip` is present, the
knowledge base inside it has the frozen SHA-256, and each of the 106 rows'
text equals the text of the same id there. *Amended when the module met
directive D3 (the core computes no digests): the module compares the
knowledge base's frozen size in bytes instead of recomputing its SHA-256; the
SHA-256 stays recorded in the frozen file.*

## 2. Results

Recomputed by `law_triage_report` (under a second); `tools law-triage` prints
the table and `tools law-triage --law ID` any one law's fate, reason and note;
`tests/test_law_triage.py` keeps the figures below.

### 2.1 B1 — one fate per law: met

| fate | n |
|---|---|
| absorbed | 0 |
| already served | 3 |
| refuted | 3 |
| retired | 100 |

The 100 retired, by reason: 42 PIPELINE (15 of them the 256-dimensional bulk,
the NoiseALU or SHA-256 coordinates), 31 WORLD (claims about the world the GLM
cannot observe), 12 NUMEROLOGY, 12
UNDERSPECIFIED, 1 DEFINITION (`LAW_COMP_WORK`) and 2 DUPLICATE
(`LAW_DRUG_004`, `LAW_MINERAL_003`, as the review's defect list said).

### 2.2 B2 — the checks: met

8 of 8 as declared:

* `LAW_HEMISPHERIC_COHERENCE_001` — **refuted**. Read as the decoder's
  `P(dH ≤ 3)`, the probability that decoding is right is 0.9988 at 1/50,
  0.9702 at 1/20 and 0.7857 at 1/10; on a grid of hundredths it first falls
  below 51% at 3/20. There is no cliff to 51% above 5%.
* `LAW_PARTICLE_6D` — **refuted**. All 14 carriers are Golay codewords, so
  two distinct carriers are at least 8 apart: electron and positron are 8
  apart (not within 3), and the lepton–quark distances are 8, 12 and 16 (never
  4).
* `LAW_LEPTON_004` — **refuted**. The least nonzero norm of the Leech lattice
  is 4 (true scale); it has no norm-2 shell for iron and sterile neutrinos to
  share.
* `LAW_COSMO_003` — **retired, WORLD**. Words of even weight are exactly 1/2
  of all words and all of the code; 54.56% is neither, so the law is about
  a physical stream, not the substrate.
* `LAW_DODECAD_DUALITY_001` — **already served**. Neon ⊕ Photon has weight 12
  and is a codeword: a dodecad, as the law says — and as every sum of two
  codewords at distance 12 is. The code's closure under XOR and its 2576
  dodecads are Phase 75 facts.
* `LAW_TOPOLOGICAL_COMPLETION_001` — **already served**. The shell-0 tax of a
  weight-`w` carrier is `w (Y + 1/8)` for every `w`, so tax(16) = tax(9) +
  tax(7) exactly, as for every split: "zero net increase" is linearity.
* `LAW_SQUEEZE_001` — **already served**, under the declared reading: the
  decoded 12-bit message plus the 3-bit coset weight is a 15-bit coordinate
  (1/512 of the states' information), and the round trip recovers the
  codeword exactly when the coset weight is at most 3 (7 of 7 reads as read).
  That is the complete decoder.
* `LAW_BIO_HYSTERESIS_001` — **retired, WORLD**; its code content is that a
  word at distance `d ≤ 3` fails after `4 − d` further flips (4 from `d = 0`,
  1 from `d = 3`) — the decoder's covering radius, already served.

### 2.3 B3 — already served, run: met

`law_absorption.fact_value('weight-count', 12)` returns 2576;
`coherence.tax_shell0` gives tax(16) = tax(9) + tax(7);
`substrate.golay_decode.decode_complete` returns the codeword and coset weight
2 for a codeword with two flips.

### 2.4 B4 — absorption: met (vacuously)

No law passes S1–S3, so there is nothing to absorb. The declared expectation —
none absorbed — holds. The three refuted laws are the only ones whose content
the GLM could compute and did not already: a correction of a false claim is
recorded here, and adds no reading.

### 2.5 B5 — the source: met

The knowledge base inside `source_material/GLM-main.zip` has the frozen size
(1,706,840 bytes), and 106 of 106 frozen texts equal the knowledge base's text
for the same id. The SHA-256 (`f1087c53…`) is recorded in the frozen file and
was checked when it was frozen; the module does not recompute it, because the
core computes no digests (directive D3). The reasoning core also does not open
archives, so the knowledge base's bytes are read by the caller: `tools
law-triage` and `tests/test_law_triage.py` read them and take B5;
`law_triage_report()` called without them takes B1–B4 only.

## 3. What this round moved, and what it leaves

**Moved.** The 106 are closed one by one under a stated rule; nothing was
added to the GLM, as the owner asked unless a law earns it. The triage is a
record the GLM does not consult at run time.

**Leaves.** The 42 PIPELINE laws could be retested only through the UBP's own
pipelines (the review's Round 3 candidate); if one of those pipelines is ever
built in the GLM, its laws would be re-read under the same rule.
