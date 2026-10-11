# Citations read in Lean's scope, checked against the elaborator

## Tier 0 — the coarse read

**Question.** Once the citation index stops reading a bound variable, a comment word or an out-of-scope short name as a citation, and the feature map stops counting a type word inside an identifier, how many of the citation edges the GLM reads are edges the Lean elaborator confirms, and which Lean-corpus retrieval findings survive the repaired relevance?

**Verdict.** The repaired reader is a reader of Lean: 99.1 % of its citation edges are edges the elaborator confirms, against 52.1 % for the legacy reader, it finds more of the real ones, and the one-letter sink is gone; the type-word repair leaves no structural coordinate that a renaming can move; every qualitative retrieval verdict survives the repaired relevance, and the structural address gains on it. The repaired graph then carries a new operation: whether one Lean result rests on another, answered with a checkable witness.

**Deciding figure.** Precision against the elaborator 9,834 of 9,920 edges (legacy 7,795 of 14,949); visible recall 9,834 of 10,819 (legacy 7,778); edges into the ten one-letter declarations unconfirmed 4 (legacy 3,162); goals moved by anonymisation 0 of 836 (legacy 41); address hits at 5 on 209 declaration queries 79 (legacy 77); 7 of 7 marks met (L1–L7) when the round closed, L6 recorded as a miss by construction since Phase 114's re-take of the headline, and of the dependency marks D2–D4 met, D1 not met as declared (7 of 12, 0 wrong, 5 refused as ambiguous) and met after a scope repair (12 of 12).

**Recomputed by.** `glm_universal.reasoning.citation_scope.citation_scope_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

Round 9 of the order of work in [`STATUS.md`](../STATUS.md) §3.4, retrieval,
continued: **item 5 with the citation leak**. Phase 100
([`CORPUS_RESAMPLE_STUDY.md`](CORPUS_RESAMPLE_STUDY.md) §4.4) found that
`lean_address.citation_index` resolves a token by its short name whenever
that short name is unique in the development, so every bound variable `a`,
`A`, `e`, … reads as a citation of one of the ten declarations with a
one-letter name — 3,231 of 15,012 edges, `GLM.Heisenberg.a` "cited" by 1,920
declarations. Item 5 of §3.4 is the same kind of leak in the feature map: the
type vocabulary is counted wherever it occurs, inside an identifier included,
so renaming a statement's identifiers moves a coordinate that is meant to be
structural. The owner asked for the citation leak to be rectified this round.

## 1. The objects

* **The legacy reader** (`lean_address.legacy_citation_graph`, kept as the
  record): every identifier token of a declaration's statement and body,
  comments included, looked up by full name, by namespace-qualified tail, and
  — failing both — by its unique short name anywhere in the development, a
  dotted token falling back to its last component.
* **The repaired reader** (`lean_address.citation_graph`, the default from
  this round): comments and string literals are not read; a name bound by the
  declaration itself (signature binders, quantifiers, `fun`, tactic
  introductions, match arms) or by a `variable` line of its file shadows
  every declaration; a dotted token whose head is a local is field notation
  and is not read; every other identifier `x` names `P.x` for the longest
  prefix `P` of the citing declaration's own name that makes it a
  declaration, then `O.x` for a namespace an `open` line made visible, then
  `x` at the root. Nothing resolves by a short name that is out of scope.
* **The reference** (`citation_reference`, taken by
  `glm_lean/tools/CitationReference.lean` with `lake env lean`): for every
  constant the development declares, the development's constants in its
  elaborated type or value, folded onto the parsed declarations by longest
  name prefix (`f.eq_1`, `f._proof_1`, a structure's projections count as
  `f`). It is the compiler's answer, not a reading.
* **Precision** of a textual graph: the share of its edges the reference
  confirms. **Visible recall**: the share of the reference's edges whose
  target's short name the citing declaration's code spells that the reader
  finds (an instance, a `simp`-set lemma or an elaborated type puts constants
  in a term no text names; those are not counted against a text reader).
* **The type-word repair** (item 5): the six type-vocabulary coordinates
  count a type word only as a whole identifier (`Nat`, `Finset`, `Prop`, …,
  and the head of `Nat.succ`), never inside a longer one (`natCast`,
  `IsFinsetLike`), beside the symbols `ℕ ℤ ℚ ℝ` as before.

## 2. Declarations — written before the reference was taken

Observed before this section was written, and therefore not a mark: the
repaired reader gives 9,953 edges against the legacy reader's 15,022 on the
current tree, 7,482 of them shared, and 153 of its edges point at a
one-letter declaration.

| mark | declaration |
|---|---|
| L1 | The repaired reader's precision against the elaborator is at least 95 %, and strictly above the legacy reader's. |
| L2 | Of the repaired reader's edges into the ten one-letter declarations, at most 5 are unconfirmed by the elaborator (the legacy reader's count is reported beside it). |
| L3 | The repaired reader's visible recall is no more than 2 percentage points below the legacy reader's: the repair removes false edges without losing the real ones. |
| L4 | After the type-word repair, anonymisation moves no syntax coordinate of any goal of the anonymous register (it was 39 of 883 before). |
| L5 | Under the repaired relevance and the repaired features, the qualitative verdicts of the address-retrieval study hold on the declaration queries at `k = 5`: the structural address beats the digest, the shuffle, random and exact chance, and the plain text search beats the address. |
| L6 | Every Lean-corpus retrieval figure re-taken this round is stated beside its legacy value, so the old figures are kept as the record. |
| L7 | The scope rule is proved in Lean: a bound name is never read as a citation, a resolved name is always a declaration of the corpus, and resolution is the first match in Lean's order; the type-word count is invariant under any renaming that fixes the type vocabulary. |

### 2.1 Declared second, before any of its code: what the repaired graph is for

Written after L1–L6 were measured and before a line of the operation below
existed. A citation graph that the elaborator confirms is a graph the machine
can *reason over*: the question "does this result rest on that one?" is a
reachability question with a checkable witness. Track M of Question Set B
([`QUESTION_SET_B_STUDY.md`](QUESTION_SET_B_STUDY.md) §8) asks for frames
that answer from the project's own corpus; this is the first.

**The operation.** `does A rest on B`, `what does A rest on`, `what rests
on A` (with `depend on` as a synonym), answered over the elaborator's graph
while it is of the current tree. A *yes* carries a path of edges as its
witness; a *no* carries the whole closure of `A` as the certificate of
absence; the column-3 script re-derives either from the edges it embeds.

**The declared cases** (all from `RequestProject/GLM/CitationScope.lean`,
read from its source before the operation was written):

| # | question | declared |
|---|---|---|
| 1 | does `cites_mem` rest on `resolve_mem` | yes |
| 2 | does `cites_mem` rest on `resolve` | yes |
| 3 | does `resolve_first` rest on `candidates` | yes |
| 4 | does `candidates` rest on `prefixes` | yes |
| 5 | does `scoped_reads_in_scope` rest on `toyCorpus` | yes |
| 6 | does `legacy_reads_bound_variable` rest on `legacy` | yes |
| 7 | does `typeCount_rename` rest on `typeCount` | yes |
| 8 | does `infixCount_not_rename_invariant` rest on `typeCount` | yes |
| 9 | does `resolve_mem` rest on `cites` | no |
| 10 | does `typeCount` rest on `resolve` | no |
| 11 | does `prefixes` rest on `candidates` | no |
| 12 | does `resolve_mem` rest on `GLM.Heisenberg.a` | no |

| mark | declaration |
|---|---|
| D1 | The 12 declared questions are answered as declared, 0 wrong. |
| D2 | Every answer passes its column-3 gate, and every mutated reading (the verdict flipped, or one edge of the witness path replaced by a non-edge) fails it. |
| D3 | Three named refusals: an unknown name (`UNKNOWN_DECLARATION`), an ambiguous short name (`AMBIGUOUS_NAME`), and a reference taken over another tree (`REFERENCE_STALE`). |
| D4 | The earlier framed answers are unchanged: Question Set B 14 of 14, the 27 framed answers of Outside O1, the 13 class-S answers. |

## 3. Measurements

Taken by `tools citation-scope --write` (the reference by
`tools citation-scope --reference`) on the tree of 4,596 declarations that
includes `CitationScope.lean`. The reference holds 11,790 elaborated
constants, folded onto 4,552 of the parsed declarations (the other 44 are
unnamed instances, macros and examples, which no reader cites).

### 3.1 The two readers against the elaborator (L1–L3)

| reader | edges | confirmed | precision | visible edges found | visible recall | edges into one-letter declarations | of them unconfirmed |
|---|---|---|---|---|---|---|---|
| legacy | 14,949 | 7,795 | 52.1 % | 7,778 of 10,819 | 71.9 % | 3,237 | 3,162 |
| repaired | 9,920 | 9,834 | **99.1 %** | 9,834 of 10,819 | **90.9 %** | 153 | **4** |

The reference holds 12,857 edges over the shared declarations, 10,819 of
them visible (the target's short name occurs in the citing code). **L1 met**
(99.1 % ≥ 95 % and above 52.1 %), **L2 met** (4 ≤ 5), **L3 met** — the
repaired reader's recall is *higher*, not merely within two points: the
legacy reader dropped every short name that was ambiguous anywhere in the
development, and the scoped reader resolves those in scope.

**Where the remaining 86 unconfirmed edges come from.** Read by hand from
the list `citation_reference.audit` produces: mostly a definition named in
`simp [d]`, `unfold d` or before `decide`, which the tactic unfolds so the
elaborated term no longer contains `d` (`coldStar_hotterThan_hotTea` names
`tea` in `simp [hotTea, …, tea, …]`) — a citation in the source that the
term erases, so the reference under-states rather than the reader
over-states; and a constructor read as the namespace's declaration of the
same short name (`D` inside `QuestionSetBMatrix.Cls` is the constructor
`Cls.D`, which the line reader does not list, so it resolves to the
definition `QuestionSetBMatrix.D`). Those four are the four unconfirmed
one-letter edges, so the one-letter sink is gone: 3,162 unconfirmed edges
into those ten declarations under the legacy reader, 4 under the repaired one.

### 3.2 The type-word repair (L4)

On the 836 goals of the anonymous register (both strides of the relay study
on the current corpus), anonymisation moved a syntax coordinate of **41**
under the Phase 100 count and of **0** under the repaired one. **L4 met.**
Phase 100's corpus gave 39 of 883; the register's query set moves with the
corpus. The repaired count is the anonymiser's own token rule, so the
invariance is not measured but proved (`typeCount_rename`); the measurement
checks the implementation.

### 3.3 The Lean-corpus retrieval figures, re-taken (L5, L6)

The legacy column is the Phase 100 code run on this round's tree
(`_data/citation_scope_legacy.json`, a frozen record): the same
declarations, the same queries, only the readers differ. Hits at
`k = 1, 3, 5, 10`.

| set | ranking | legacy | repaired |
|---|---|---|---|
| declarations (209) | address | 41, 64, 77, 89 | **54, 70, 79, 101** |
| | features | 43, 64, 75, 87 | 53, 70, 84, 102 |
| | lexical | 71, 98, 108, 126 | 71, 98, 108, 125 |
| | text | 145, 168, 178, 182 | 147, 168, 177, 181 |
| | name | 31, 42, 48, 59 | 29, 40, 46, 56 |
| | digest | 3, 5, 7, 13 | 3, 5, 7, 12 |
| | shuffled | 0, 2, 6, 17 | 1, 7, 13, 19 |
| | random | 4, 7, 10, 18 | 4, 7, 10, 19 |
| goals (103) | address | 7, 14, 18, 25 | 9, 11, 18, 28 |
| | lexical | 24, 35, 42, 52 | 23, 34, 41, 52 |
| | text | 69, 83, 85, 90 | 69, 83, 85, 91 |
| | name | 15, 23, 26, 34 | 15, 19, 23, 32 |
| | digest | 0, 0, 1, 8 | 0, 0, 1, 7 |
| | random | 2, 3, 4, 9 | 2, 3, 4, 9 |

Beside them: citation edges over the whole corpus 15,036 → 9,986; mean
relatives per declaration query 37.1 → 35.4; exact chance at 5 on the
declarations 8.27 → 7.90 hits; nearest-by-address neighbour in the same file
831 → 1,009 of 4,596 and joined by a citation 141 → 166; distinct addresses
4,109 → 3,899 (collision classes 325 → 442, the largest 16 → 19).

**L5 met**: at 5 on the declarations the address's 79 beats the digest's 7,
the shuffle's 13, random's 10 and chance's 7.90, and text's 177 beats it.
**L6 met**: every figure above is stated beside its legacy value, both
records are of the same tree.

**Re-read at the close of Phase 114.** Phase 114 edited a module the stored
measurement digests (`reasoning/retrieval.py`, whose import of the Golay
words moved to the new `golay_words.py`), so the close re-took the headline, on the tree of that day: 4,739
declarations against the legacy record's 4,596. The legacy figures were taken
by Phase 100's code and cannot be re-taken, so L6 — both records of one tree
— cannot hold again, and `tests/test_citation_scope.py` records it as a miss
by construction rather than letting it fail. The legacy record is kept
unchanged as the record, and the table above, taken on the Phase 101 tree,
stands as written; L1 to L5 and L7 hold on the re-taken headline.

**What moved, read.** The address gains most at the top rank (41 → 54 at 1,
89 → 101 at 10) and the raw features more (75 → 84 at 5): the leak put
noise into two of the 24 coordinates — `cites` counted every bound `a`, and
`cited by` gave `GLM.Heisenberg.a` 1,920 — and noise in a coordinate is
distance between relatives. The shuffle rises because the address
distribution is more clumped (fewer distinct addresses, larger classes), so
a reshuffled pairing lands on a relative's class more often; it stays well
below the address. Text and lexical scarcely move: they never read the
citation graph, and their small changes are the relevance sets' alone.

### 3.4 The dependency operation (D1–D4)

`tools dependency`. The twelve declared questions, as first declared: **7
answered as declared, 0 wrong, 5 refused `AMBIGUOUS_NAME`** — `resolve` and
`candidates` are short names of two declarations each (`GLM.Conversation.
resolve`, `GLM.Golay24.candidates`), which the declaration did not foresee.
**D1 not met as declared.** The repair is the round's own rule applied to
the question: in a two-name question an ambiguous name is read in the scope
of the other (`proof_dependency._pair`; the switch `SCOPED_QUESTIONS` keeps
the operation as declared), exactly as Lean would read `candidates` inside
`resolve_first`. After it, 12 of 12 as declared, 0 wrong; a single
ambiguous name with nothing to read it against is still refused.

**D2 met**: all 12 answers and 3 closure questions (`what does
cites_antitone rest on` — 5 declarations; `what rests on prefixes` — 11;
`which declarations rest on GLM.Golay24.Word` — 316, 272 directly) pass
their column-3 gate, and all 15 mutated readings (verdict flipped with a
fabricated one-step path, or the closure count moved by one) are rejected.
**D3 met**: `UNKNOWN_DECLARATION`, `AMBIGUOUS_NAME` and `REFERENCE_STALE` as
declared. **D4 met**: the frame is consulted only for the three phrasings,
before the other frames, and the suites that pin the earlier framed answers
(`tests/test_question_frames.py`, `tests/test_symbolic.py`) pass unchanged.

### 3.5 The Lean half (L7)

`RequestProject/GLM/CitationScope.lean`, no `sorry`, standard axioms only:
`resolve_bound` (a local shadows every declaration), `resolve_mem` (a
resolved name is a declaration of the corpus), `resolve_first` (it is the
first candidate in Lean's order that is one), `cites_mem`, `cites_ne_self`,
`cites_antitone` (binding more names only removes citations); the leak as a
counter-model, `legacy_reads_bound_variable` against
`scoped_ignores_bound_variable` and `scoped_reads_in_scope`; and the
type-word repair, `typeCount_rename` (a renaming that fixes the type words
and sends nothing else to one leaves the count unchanged) with its
counterexample for the old rule, `infixCount_not_rename_invariant`. **L7
met.**

### 3.6 The native and resampled figures, re-taken

Every measurement that reads the Lean address book or the relevance sets was
re-taken on this tree (209 declaration and 103 goal queries; census 4,596
queries over 172 files). They are re-readings, not new claims, and each is
written beside the reading it updates.

* **Native parity** ([`NATIVE_PARITY_STUDY.md`](NATIVE_PARITY_STUDY.md)):
  `native2` = `features2` at 65, 80, 91 and 112 hits (k = 1/3/5/10) on the
  declarations, against 53, 70, 84 and 102 for `features`. N3, N4a, N4b, N5, N7 and N8 met; N1, N2 and N6 not — N6 by
  one goal query at k = 5, the half Phase 100's resampling had already
  called a draw.
* **Native words** ([`NATIVE_WORDS_STUDY.md`](NATIVE_WORDS_STUDY.md)): W1,
  W3, W4, W5 met; W2 missed by one declaration query at k = 1, W6 by one
  goal query at k = 1. The document mark W3, on which the live ranking
  rests, holds.
* **The resampling** ([`CORPUS_RESAMPLE_STUDY.md`](CORPUS_RESAMPLE_STUDY.md)
  §4.7): every verdict survives. The one effect is still `native2` ahead of
  `features` on the declarations (95.3 % of file drops, 95.5 % of offsets,
  census 227 : 29); the control still fails; M4 still not met. **M5** — the
  number of structural addresses outside a dropped file that the drop would
  change — falls from 12,541 over 167 drops (largest 1,880, the
  `Heisenberg.a` sink) to **1,881 over 109 drops (largest 343,
  `Golay/Code.lean`)**: the held-fixed price is now the price of real
  citations.

## 4. What changed in the system

* `lean_address.citation_graph` is the repaired reader;
  `legacy_citation_graph` is kept, and so is `citation_index`, which nothing
  shipped reads any more. A free goal's citations are read with the
  development's namespace open (`goal_citations`).
* The carrier coordinates count whole type words (`type_words`).
* The Lean address book, the lexical book, and the measurement caches that
  read them were re-taken.
* `citation_reference` holds the elaborator's graph beside the tree digest;
  `glm_lean/tools/CitationReference.lean` produces it.
* The frame layer answers `does A rest on B`, `what does A rest on`, `what
  rests on A` (`runtime/dependency_frames.py`), switched by
  `question_frames.DEPENDENCIES`.

## 5. Re-running

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.tools citation-scope              # the stored measurement
PYTHONPATH=. python3 -m glm_universal.tools citation-scope --reference --write   # re-take (needs lake build)
PYTHONPATH=. python3 -m glm_universal.tools dependency
python3 GLM.py -q "does cites_mem rest on resolve_mem" -c 1,2,3
```

Tests: `tests/test_citation_scope.py`, `tests/test_proof_dependency.py`.

## 6. What this leaves

* **The reference goes stale with every Lean edit.** The dependency
  operation refuses rather than answer from a graph of another tree; a round
  that adds a Lean file re-takes it (`--reference`, a few minutes over the
  compiled library). Reading the reference straight from the `.olean` files
  would remove the Lean run.
* **The 86 erased citations** (§3.1) are a known under-statement of the
  reference; reading `simp [d]` and `unfold d` arguments from the source
  would separate them from genuine reader errors.
* **Constructors and structure fields** are not declarations to the line
  reader, so a constructor that shares a short name with a definition is
  misread (the four one-letter cases).
* **Dependency questions in English**: *which of the lattice results use the
  Golay decoder?* needs a set of declarations named by a description, not a
  name — the field surface's Lean table and this operation, composed.
* N2, N5 and I3 of the retrieval round are untouched, and the native-parity,
  native-words and resampling figures were re-taken under the repaired
  readers (§3.6).

## Disposition (Phase 106)

At the owner's direction the items of §6 are **parked**, not carried as the
next round: the study did what it set out to do (the repaired reader and the
dependency operation), and further work on the citation graph was judged not
to move the machine's reasoning. What stays in the system, unchanged and
still tested: the repaired citation reader, the repaired feature map, and the
dependency operation (`runtime/dependency_frames.py`, `tools dependency`).
Nothing was removed. The work taken instead is
[`DERIVATION_STUDY.md`](DERIVATION_STUDY.md) — derivations and proofs.
