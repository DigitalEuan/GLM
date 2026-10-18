# The corpus's definitions graded, and a word's place on the lattice

## Tier 0 — the coarse read

**Question.** When the GLM answers "what is X" from its corpus, is the answer a good definition — graded against a held-out glossary rather than counted as found — and can a word be given a Leech address from its corpus counts that carries how the word is used?

**Verdict.** Partly: graded against the held-out glossary, `define`'s own ranking chooses definitions no closer to the gloss than a term's first mention, but ranking the same candidates by the term's corpus context beats that control and is now how `define` answers; a word's Leech address read from its positional counts carries word use — number words land among number words — but not the singular-plural relation.

**Deciding figure.** 3 of 8 marks, 3 of 6 amended marks; graded agreement 26 against 17 for the first-mention control (context ranking), 17 against 17 (pattern ranking); number words 64 of 120 address neighbours against 1 of 120 for the control.

**Recomputed by.** `glm_universal.knowledge.definitions_study.corpus_definitions_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. What this document is

A **pre-registration** for Phase 155 (§§0–6 were committed before the stored
measurement was taken, §2.3 after the first measurement and before the
second; §7 is what came out). It takes the two items Phase
154 left in [`CORPUS_KNOWLEDGE_STUDY.md`](CORPUS_KNOWLEDGE_STUDY.md) §7.5 that
could be measured without changing what the evaluation pins:

1. **A graded term list.** Phase 154 measured `define` by whether it answered
   (K8, K8′), and the answered rate is a weak proxy for a correct definition.
   Here the 28 entries of the paper's glossary
   ([`GLM_ACADEMIC_PAPER.md`](GLM_ACADEMIC_PAPER.md), Appendix E) are held out
   of the corpus, `define` is asked for each term, and each answer is graded
   against the held-out gloss by the content words they share. 8 marks are declared
   before the measurement: 4 for the graded definitions (G1–G4), 4 for the word addresses (W1–W4).
2. **A Leech address for a word.** A word's counts against 24 declared anchor
   words, quantised onto the Leech lattice by the decoder the Lean
   declarations are addressed with, so that a word sits on the same lattice as
   a carrier, a declaration and a document section — and a measurement of
   whether nearness on the lattice carries word use, against a control in
   which the same addresses are dealt to the wrong words.

Nothing in either part samples, and nothing is a float.

## 1. What is built

* `overlay/glm_universal/knowledge/glossary.py` — the held-out glossary, the
  grade, the control, and G1–G4.
* `overlay/glm_universal/knowledge/word_address.py` — the anchors, the word
  coordinates, the addresses, the neighbours, and W1–W4.
* `overlay/glm_universal/knowledge/_data/corpus_definitions.json` — the stored
  measurement, beside the digest of the code that took it.
* `python3 -m glm_universal.tools corpus-definitions [--write]` — the
  instrument; and the `corpus address of X` reading, which gives a word's
  address and its nearest words on the lattice.

## 2. The rules, fixed before the measurement

### 2.1 The graded definitions

* **The glossary.** The sentences of the paper's Appendix E, one entry per
  list item `**Term:** gloss`. The term is the text before the colon; the
  gloss is the text after it. A term written with a slash
  (`Construction A/B/C`) is asked as written.
* **The hold-out.** Every sentence of the corpus, in any document, whose
  token sequence contains a gloss's tokens as a contiguous run is removed
  before `define` is asked — the appendix itself and every copy of an entry
  elsewhere (the paper is quoted in other documents, and the supplied archive
  holds earlier versions). Nothing else is removed. `define` reads only the
  sentences and their postings, so the hold-out is applied to those.
* **The grade.** The content words of a sentence are its tokens that are
  content words by the corpus model's rule (`model.is_content`: not a stop
  word, longer than one character), with a final `s` removed from a word of
  more than three letters, and without the term's own words. The grade of an
  answer is the number of content words it shares with the gloss. An answer
  **agrees** with the gloss when the grade is at least 2.
* **The control.** For each term, the term's **first mention**: the first
  sentence of the held-out corpus, in corpus order, that contains the term
  and is not a heading — an uninformed answer chosen by no rule about
  definitions, and by no chance.
* **The mismatched control.** Each answer graded against the gloss of the
  next term in glossary order (the last against the first): agreement that is
  only shared vocabulary of the project (*lattice*, *code*, *carrier*) scores
  as well against the wrong gloss.

| # | mark | pass |
|---|---|---|
| G1 | `define`'s first answer against the first-mention control | the summed grade over the 28 terms is greater, and `define` scores higher on more terms than the control does |
| G2 | `define`'s first answer agrees with the gloss | at least 14 of the 28 terms |
| G3 | one of `define`'s first three answers agrees | at least 18 of the 28 terms |
| G4 | the first answers graded against their own gloss and against the mismatched gloss | the own-gloss total is at least twice the mismatched total |

A term `define` refuses scores 0 on G1–G4, and the refusal is recorded with
its mention count.

### 2.2 The word addresses

* **The words.** Every word with an associated-context set (the set
  `similar` and K7 read: 11,149 words when this was written).
* **The anchors.** The 24 alphabetic content words of at least four letters
  with the largest document frequency, ties by spelling — chosen by count
  alone, not by meaning.
* **The coordinates.** For word `w` and anchor `a`, with `n(w,a)` the
  four-token-window count, `n(w)`, `n(a)` the token counts, `T` the tokens
  and `P` the window pairs: the coordinate is `0` when `n(w,a) < 2` (the
  model's `MIN_PAIR`), and otherwise `6 + ⌊log₂ L⌋` clamped to `[1, 12]`,
  where `L = n(w,a)·T² / (n(w)·n(a)·P)` is the exact lift (a `Fraction`; the
  floor of its base-2 logarithm is computed in integers). A word's own
  coordinate against itself (when it is an anchor) is `12`.
* **The address.** The nearest Leech point to 9 times the coordinate vector,
  by the same decoder and the same scale as the Lean declarations
  (`reasoning/lean_address.quantise`). With the scale at least twice the
  covering radius the read-back is exact (`Address.lean`, `readback_exact`).
* **The neighbours.** The 10 nearest other words by squared distance between
  addresses, ties by larger corpus count, then by spelling.
* **The control.** The same multiset of addresses dealt to the words by the
  project's deterministic null permutation
  (`integrity.seeded_permutation`, label `glm-word-address-null`): the same
  distances are available, only the pairing is destroyed.

| # | mark | pass |
|---|---|---|
| W1 | read-back: every word's coordinate vector recovered from its address | every word |
| W2 | the twelve number words *one* … *twelve*: the share of their 10 address neighbours that are number words | at least 1/4 on average, and at least ten times the control's share |
| W3 | singular and plural (the K7 pairs): the plural among the singular's 10 address neighbours | at least 10% of the pairs, and at least ten times the control's rate (or ten times chance, `10/N`, if the control finds none) |
| W4 | the address against the words: distinct words with distinct coordinate vectors get distinct addresses | every pair |

### 2.3 Amended marks, declared after the first measurement and before the second

The first measurement (§7, kept as `_data/corpus_definitions_first.json`)
met G4, W1 and W4 and missed G1, G2, G3, W2 and W3. Every miss is kept as a
miss. One correction of fact first: the glossary has **27** entries, not 28
(the count of 28 included the appendix heading). The thresholds are applied
as written — 14 for G2, 18 for G3 — which with 27 terms is, if anything,
stricter than declared.

Two amended readings are declared here, before they are measured, and are
reported beside the originals, never in place of them.

* **Context-ranked `define`.** The same definitional patterns and the same
  candidates; the candidates are ordered first by how many of the term's 12
  sentence-scale context words (`answer.context`, the held-out corpus) they
  contain — content words folded as in §2.1 — and then by `define`'s own
  order. The rule is: of the sentences that define X by a declared pattern,
  prefer the one that says most of what the corpus says around X. The gloss
  is never read by it.
* **Positional word addresses.** The first addresses read a word's company
  in a four-token window against 24 content words, and the anchors came out
  generic (*exactly*, *rather*, *never*); K6 and K7 found word use in the
  *positional* reading. The amended coordinates are the 12 most frequent
  tokens of the corpus (function words included), each read once as the
  word's left neighbour and once as its right neighbour: for anchor `a`,
  `n(a,w)` is the number of times `a` directly precedes `w` (and `n(w,a)` the
  times it follows), and the coordinate is `0` below a count of 2, otherwise
  `6 + ⌊log₂ L⌋` clamped to `[1, 12]` with the bigram lift
  `L = n·T / (n(a)·n(w))` — the same form as §2.2 with `P = T`, so
  `coord_le_cap` and `coord_mono` cover it. Address, neighbours and control
  as in §2.2.

| # | mark | pass |
|---|---|---|
| G1′ | G1 with context-ranked `define` | as G1 |
| G2′ | G2 with context-ranked `define` | at least 14 terms |
| G3′ | G3 with context-ranked `define` | at least 18 terms |
| G4′ | G4 with context-ranked `define` | as G4 |
| W2′ | W2 with positional addresses | as W2 |
| W3′ | W3 with positional addresses | as W3 |

## 3. What would count against

* G1 missed: the definitional patterns choose sentences no closer to what
  the term means than the first sentence that happens to mention it.
* G2/G3 missed: `define` answers, but most answers are not what the glossary
  says the term is — the K8 rates overstated it.
* G4 missed: the agreement is the project's shared vocabulary, not the term.
* W2/W3 missed: the 24 anchor counts do not carry word use at the lattice's
  resolution, and a word's address is an index without meaning.

## 4. What is not claimed

* **The glossary is not ground truth about the world**; it is the paper's
  own one-line statement of each term, and the grade measures agreement with
  it. Shared content words are a coarse grade: a good definition in other
  words scores low, and that is a limitation kept in view, not repaired after
  the fact.
* **The word address is a resolution**, in the sense of
  `RequestProject/GLM/Layers.lean`: it shows what its 24 coordinates carry and
  conflates the rest. Words with equal coordinate vectors share an address.

## 5. What is proved before the measurement

`RequestProject/GLM/CorpusDefinitions.lean`:

* the grade is symmetric, bounded by either side's size, and monotone in the
  answer (`grade_comm`, `grade_le_left`, `grade_mono`);
* the hold-out is complete: no sentence that survives the filter contains a
  gloss as a contiguous run (`heldout_clean`), and the filter removes nothing
  else (`heldout_keeps`);
* a word coordinate lies in `[0, 12]` and is monotone in the window count for
  fixed word and anchor counts (`coord_le_cap`, `coord_mono`).

## 6. Files

See §1. Tests: `overlay/glm_universal/tests/test_corpus_definitions.py`.

## 7. What came out

Two measurements were taken. The first (kept as
`_data/corpus_definitions_first.json`) met G4, W1 and W4 and missed G1, G2,
G3, W2 and W3; §2.3 was then declared and committed before anything was
changed, the two amended readings were built, and the second measurement
(`_data/corpus_definitions.json`, the stored one, `tools corpus-definitions`)
took the original marks again beside the amended ones. The corpus moved
between the two (this round's own files are part of it): the second
measurement reads 2,200 documents and 184,967 sentences, and its hold-out
removed 121 sentences — the appendix, its copies, and the glosses quoted in
the first measurement's own record, which the reader takes in as JSON prose.
Neither answer nor control of any term contains a held-out gloss (0 leaks).

### 7.1 The marks

| # | second (stored) | mark |
|---|---|---|
| G1 | grade 17 against 17 for the first mention; `define` higher on 4 terms, lower on 6 | **missed** |
| G2 | 5 of 27 first answers agree (the control: 4) | **missed** |
| G3 | 8 of 27 have an agreeing answer among the first three | **missed** |
| G4 | 17 against its own gloss, 1 against the mismatched gloss | met |
| W1 | 11,157 of 11,157 words read back exactly | met |
| W2 | number words: 1/12 of the address neighbours (10 of 120), control 1/60 | **missed** |
| W3 | plurals: 19 of 1,100 pairs (1.7%), control 1 | **missed** |
| W4 | 4,323 distinct coordinate vectors, 4,323 distinct addresses | met |
| G1′ | context ranking: grade **26 against 17**; higher on 9 terms, lower on 5 | met |
| G2′ | 7 of 27 first answers agree | **missed** |
| G3′ | 11 of 27 among the first three | **missed** |
| G4′ | 26 against its own gloss, 9 against the mismatched gloss | met |
| W2′ | positional addresses: number words **8/15** of the neighbours (64 of 120), control 1/120 | met |
| W3′ | positional addresses: plurals 6 of 1,100, control 1 | **missed** |

**3 of 8 marks; 3 of 6 amended marks.**

In one sentence: Partly: graded against the held-out glossary, `define`'s own ranking chooses definitions no closer to the gloss than a term's first mention, but ranking the same candidates by the term's corpus context beats that control and is now how `define` answers; a word's Leech address read from its positional counts carries word use — number words land among number words — but not the singular-plural relation.

### 7.2 What this answers

**`define` found definitions, but its own ranking did not find good ones.**
Phase 154's K8 counted a term as defined when some sentence matched a
definitional pattern. Graded against what the glossary says, `define`'s first
answer is no closer to the gloss than the first sentence of the corpus that
happens to mention the term (17 against 17). The pattern ranking prefers a
sentence of the form *X is …* from a state document, and many such sentences
are remarks about X rather than statements of what X is: *The tax is blind to
lawfulness*, *The deep hole is a genuine tie*, *Escalation is a step of the
loop and costs nothing where it is not needed*. They are true and well
placed, and they are not definitions.

**Ranking by the corpus's own context is better, and is adopted.** Ordering
the same candidates by how many of the term's sentence-scale context words
they hold — of the sentences that define X, prefer the one that says most of
what the corpus says around X — raises the graded total from 17 to 26 and
beats the first-mention control on 9 terms against 5 (G1′). It reads only
the corpus, never the gloss. It is still far from the 14 agreeing first
answers G2 asked for (7 of 27), so the ranking is better, not good: a
two-shared-word agreement is a demanding grade for one-line glosses, and
four terms (*TGIC*, *Construction A/B/C*, *Hull certificate*, *Licensing*)
are mentioned but never defined by a declared pattern once the glossary is
held out. The `corpus define` reading now uses the context ranking, and its
third column recomputes the context words and the ranking by brute force.

**The agreement is about the term, not the project's vocabulary.** Against
the next term's gloss the same answers score 1 (pattern) and 9 (context)
against 17 and 26 (G4, G4′).

**A word has a place on the lattice, and nearness there carries word use —
when the coordinates are positional.** Every one of the 11,157 words with a
context set gets an address, read back exactly, and distinct coordinate
vectors never share one (W1, W4) — the guarantee of `Address.lean`, observed.
With coordinates against 24 content anchors chosen by document frequency
(*exactly*, *exact*, *first*, … *rather*, *never*) the lattice neighbourhoods
carry little (W2, W3 missed). With coordinates against the 12 most frequent
tokens on either side — *the*, *a*, *is*, *of*, *and*, … — the twelve number
words find number words for 64 of their 120 neighbours, against 1 of 120 when
the same addresses are dealt to the wrong words (W2′); *seven*'s nearest
words are *six, ten, fourteen, fifteen, four, five, eight*. The rare two
fail: *eleven* finds none and *twelve* one, as they did under `similar`. That is the
positional reading of K6 (61 of 120 under `similar`) reproduced *on the
lattice*: a word now sits on the same 24-dimensional lattice as a carrier, a
declaration and a document section, and its neighbourhood there means
something measured. `corpus address of X` gives it.

**One negative result, kept.** Neither scheme puts a plural near its singular
(W3, W3′). The positional coordinates separate them by construction — *a* is
an anchor, and a singular follows *a* where a plural does not — and the window
coordinates are too coarse: 11,157 words share 4,323 addresses.

### 7.3 Faculties (D15)

* **address — moved.** A word of the corpus has a Leech address, with exact
  read-back and a measured neighbourhood (W2′); it is the first address in the
  package computed from corpus counts rather than from a declared feature
  table.
* **table — moved.** `define` answers with the context-ranked sentence.
* **refuse — moved.** `corpus address of` refuses a phrase (an address is for
  one word) and a word with too little company to have coordinates, each with
  the reason.
* **derive — not moved.**

### 7.4 What is left

* **A grade that is not word overlap.** Two shared content words is coarse; a
  good definition in other words scores low. The glossary terms' own context
  sets, compared with the answer's by the squared cosine already proved in
  `CorpusKnowledge.lean`, would grade meaning rather than spelling.
* **Definitions the patterns miss.** Four glossary terms are mentioned but
  never defined by a declared pattern once the glossary is held out. An
  appositive pattern (*X (the …)*, *X, which is …*) is the next candidate,
  declared before it is measured.
* **The plural on the lattice.** A coordinate pair that folds the determiner
  (*a* / *the*) would let singular and plural share company; it should be
  declared, then measured against W3.
* **Word addresses as the parser's *did you mean*.** Unchanged from Phase 154:
  it changes refusals the evaluation pins, so it needs a frozen-path
  comparison.
