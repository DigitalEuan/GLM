# The AST address as a retrieval key

## Tier 0 — the coarse read

**Question.** Can the structural address of a Python expression be indexed as a retrieval key, beside the Lean corpus addresses, so that the GLM finds the places — in its own code and in the archived scripts — where a structurally equal expression is already computed?

**Verdict.** Yes: the structural key finds a structurally equal site at rank 1 for every perturbed query, where the token overlap finds one for 343 of 467, and the new operation answers where an expression is computed in the live code and in the archive, with a column-3 script that re-decides every member of the bucket. The Phase 64 address, read as it is, is not a usable key: it changes under renaming on a fifth of the queries and merges 23 classes that are not structurally equal. 5 of 7 marks met; A2 missed by one declaration error, A4 missed as predicted by reading the code.

**Deciding figure.** On 467 query sites of the 11,669-site index under rename-and-commute, hit@1: `ast_v2` 467, `ast_v1` 456, `carrier` 412, `text` 343 (discordance against `text` 124 : 0); the bucket key unmoved on 467 of 467 under every perturbation; the matcher and the reference agree on 8,398 of 8,398 calls; 106 integer classes, 3,350 evaluations, 0 failures; marks A1, A3, A5, A6 and A7 met, A2 and A4 not met.

**Recomputed by.** `glm_universal.runtime.ast_index_report.ast_index_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

Round 9 of the order of work in [`STATUS.md`](../STATUS.md) §3.4, retrieval,
continued after Phase 102: **I3**. Phase 64
([`PYTHON_SPEECH_STUDY.md`](PYTHON_SPEECH_STUDY.md) §7) left it as:

> Use the AST address as a retrieval key: the structural address of a
> Python expression could be indexed alongside the Lean corpus addresses, so
> that the GLM finds prior derivations of a structurally equal expression.

The address exists (`reasoning/python_substrate.ast_address`, Phase 64): an
expression is canonicalised — commutative operands sorted, variables renamed
by first appearance, the two repeated until nothing moves — and embedded in
`Q^24` as a sum of Golay codewords of its node kinds weighted by a dyadic
code of their path. Nothing reads it except the carrier line `speak` prints.
No index of expressions exists.

Three facts about that canonical form were read from its code before
anything was declared, and they decide how the item has to be asked:

* **It drops information.** A call's keyword arguments are not in the form
  (`round(x, ndigits=2)` and `round(x)` share one), and every non-integer
  constant is reduced to its type (`a + 0.5` and `a + 0.25` share one). So
  as a retrieval key it can claim a match that is not one.
* **It renames incompletely.** The receiver of a method call is kept as
  text inside the function name (`u.norm(k)` and `w.norm(k)` differ), so a
  renamed query can miss its own source.
* **It is a fixpoint, not a canonical form.** Sorting by the printed form
  and renaming by first appearance depend on each other; repeating them
  until nothing moves need not reach the same form from two orderings of
  the same expression.

So the round declares two keys: the Phase 64 address **as it is**
(`ast_v1`), measured, and a structural key built for the purpose
(`ast_v2`): a bucket key that cannot be changed by a renaming or a
commutation, followed by an exact matcher that decides structural equality
inside the bucket. The relation the operation answers — *structurally equal*
— is the matcher's by definition; what is measured is whether each key
finds it, whether the matcher is right, and what the relation is worth
against a lexical baseline.

## 1. The objects

**Structural equality.** Two expressions are structurally equal when one
becomes the other under a one-to-one renaming of variables and a choice of
order for the two operands of each `+ * & | ^` and each single `==` / `!=`.
Nothing else: no associativity, no constant folding, no algebra. Function
names and attribute names are fixed; a method's receiver is a variable like
any other. Keyword arguments are part of the expression; constants are
compared by type and exact value. (`+` is treated as commutative for every
operand, which is false of strings and tuples; §2's A6 measures where that
matters, and the Lean file proves the arithmetic case and the string
counterexample.)

**The index.** One frozen snapshot of every *statement-level* expression —
the value of an assignment, an augmented or annotated assignment, or a
`return` — in two corpora:

* `live` — every Python file under `overlay/glm_universal/`, as it stood when
  the snapshot was taken (after §0–§2 of this study were written, before any
  measuring code existed);
* `archive` — every Python file in `source_material/GLM-main.zip`, the
  owner's earlier GLM tree (the scripts the original salvage task asked
  about).

An expression is admitted when it parses on its own, uses only names,
constants, arithmetic, boolean and comparison operators, calls (positional
and keyword arguments, no starred ones), attributes, subscripts, slices,
tuples and conditional expressions, has between 3 and 64 nodes, and
contains at least one arithmetic operator (binary, or a unary minus or
inversion) — the expressions that compute something. Each site keeps its
corpus, file, line, column and its text as `ast.unparse` prints it. The
snapshot is stored once, beside the SHA-256 of its canonical content, and
every figure of this study is read from it. The zip itself is not tracked
by the repository's version control, so the snapshot is also what makes
the archive half reproducible on a machine that does not hold it.

**The keys.**

| key | what it is |
|---|---|
| `ast_v2` | the subject: the bucket key — the expression's form with every variable erased and the operands of each commutative operator sorted by the erased form — then the exact matcher inside the bucket |
| `ast_v1` | the Phase 64 canonical form, as it is |
| `carrier` | the Phase 64 carrier in `Q^24`, by L1 distance (reported, no mark) |
| `text` | the standard: Jaccard overlap of the token sets (identifiers, numbers, operators), no structure |

Each ranking orders the index for a query: first by its key (in the class
or not; the distance for `carrier`; the overlap for `text`), then by token
overlap, then by the site's stored order.

**The matcher** walks two forms together, binds variables one to one, and
tries both operand orders at a commutative node, backtracking. A separate
**brute-force reference** enumerates every operand order of the second
form and checks each against the first by one pass that builds the
renaming; it shares no code with the matcher, and it is what every
column-3 script carries.

**The operation.** *Where is `EXPR` computed?* (also *where else is …*,
*where in the archive is …*, *where in the live code is …*): every site of
the index structurally equal to `EXPR`, with the renaming that witnesses
each, the count per corpus, and a column-3 script that recomputes the
bucket key of the query and of every member of its bucket, and re-decides
each member by the brute-force reference. An empty answer is an answer: the
bucket holds no match, and since the bucket key cannot be moved by a
renaming or a commutation (proved in Lean), no other bucket can.

## 2. Declarations — written before any measuring code

The cases are `evaluation/ast_index_cases.py`, committed with this section.
The query sites are every 25th site of the snapshot in its stored order.
Perturbations: `rename` (every variable to a fresh name, one to one),
`commute` (the operands of every commutative node swapped), `both`. Exact
throughout (D7): integers and `Fraction`; the A6 evaluation uses integers
only and skips an environment where either side divides by zero.

* **A1 — frozen.** The snapshot's stored digest matches its content, and
  the measurement re-taken from it equals the stored measurement.
* **A2 — the matcher is right.** Every declared pair gets its declared
  verdict, and the matcher agrees with the brute-force reference on every
  query-and-candidate pair the measurement asks it about (0 disagreements).
* **A3 — the bucket key is invariant.** Under every perturbation of every
  query site, the perturbed text has the source's bucket key and matches
  the source structurally (100 %).
* **A4 — the Phase 64 address is nearly invariant.** Its canonical form is
  unchanged under `both` on at least 95 % of the query sites. Its false
  merges (two sites in one `ast_v1` class that are not structurally equal)
  are reported beside it.
* **A5 — retrieval.** Under `both`, `ast_v2` has a site structurally equal
  to the source at rank 1 on every query, `text` at rank 1 on at most 75 %
  of them, and the discordance runs `ast_v2`'s way with a two-sided sign
  test at most 0.05.
* **A6 — soundness on arithmetic.** On every structural class of the index
  with two different spellings whose nodes are all integer arithmetic
  (variables, integer constants, `+ - * // % **` with a literal exponent of
  at most 8, unary minus, `& | ^ ~`, shifts by a literal of at most 16),
  the matcher's renaming gives equal values on every one of five declared
  integer environments (0 failures). The classes that commute `+` across a
  string constant are counted and reported.
* **A7 — the operation.** Every declared question answered and every
  declared refusal refused by its code; every answer's column-3 script
  verifies and every mutated script (a site removed, or one claimed that is
  not a match) fails.

**Wiring, declared now.** The operation joins the frame layer as a new
frame, consulted before the typed frames like the dependency frame, behind
a switch that restores the layer as it was. No existing answer changes:
the new phrasings were read by no frame before. `python_substrate` is not
edited — the Phase 64 address keeps its carrier line, and its defects are
recorded here, not repaired under it.

**What would count as moving the target (D15).** A5 and A7 met move
**address**: an expression is found where it is computed when the query is
not its stored spelling. A refusal of an expression outside the index's
kinds moves **refusal** only in the sense that it is not answered with an
empty list it has no right to.

**What it does not claim.** Structural equality is not semantic equality:
`x ** 2` and `x * x` are different here, as are `(a + b) + c` and
`a + (b + c)`. The index holds what the code computes at statement level,
not every subexpression.

## 3. Results

Everything below is read from the stored report
(`reasoning/_data/ast_index.json`, `tools ast-index --write`), which is
current while the snapshot and the measuring code are unchanged.

**The index.** 11,669 sites: 3,438 in the live code (483 files read, none
skipped) and 8,231 in the archive (593 files read, 3 that do not parse
skipped). They fall into 4,818 buckets and 4,864 structural classes, of
which 1,621 hold more than one site. 307 classes hold sites of both
corpora: the expressions the live code computes that the archive already
computed, among them `(y + dy, x + dx)` (287 sites), `counts.get(word, 0) + 1`
(195) and `1 << index` (116).

**Invariance (A3, A4).** Over the 467 query sites (every 25th):

| perturbation | bucket key unmoved | matches the source | Phase 64 form unmoved |
|---|---|---|---|
| `rename` | 467 | 467 | 373 |
| `commute` | 467 | 467 | 464 |
| `both` | 467 | 467 | 373 |

The Phase 64 form fails exactly where §0 said it would: a method call keeps
its receiver as text inside the function name, so renaming the receiver
(`counts.get(...)`) or commuting inside it (`(y1 ^ c).bit_count()`) moves
the form. No failure came from the fixpoint itself.

**Retrieval (A5).** Under `both`, ranked over all 11,669 sites:

| ranking | hit@1 | hit@5 |
|---|---|---|
| `ast_v2` | 467 | 467 |
| `ast_v1` | 456 | 465 |
| `carrier` | 412 | 418 |
| `text` | 343 | 402 |

Discordance at rank 1: `ast_v2` against `text` 124 : 0, sign test
1/10,633,823,966,279,326,983,230,456,482,242,756,608 (that is, 2^-123); against `ast_v1` 11 : 0
(1/1,024); against `carrier` 55 : 0. The Golay carrier of Phase 64, read as
an L1 distance, beats the token overlap (412 against 343) even though it is
not invariant: it is a usable *near* key, not an exact one.

**The Phase 64 address's false merges.** 23 of its 4,995 classes join sites
that are not structurally equal, 146 sites in all. Every one is a dropped
keyword or a dropped constant value: `_d(L=2, M=1, T=-3, I=-2)` with
`_d(L=2, M=1, T=-2)`; `z_offset_10 / 10.0` with `sw / 12.0`; `1.0 + 0j`
with `15.0 + 0j`.

**The matcher (A2).** On the 40 declared pairs the matcher and the
reference agree 40 of 40, and on all 8,398 calls the measurement made
(partitioning the buckets and matching the perturbed queries) they agree
with none undecided. The matcher's verdict differs from the declared one on
one pair, and the declaration is wrong (§4). A2 is scored as declared: not
met.

**Soundness (A6).** 106 structural classes have two or more spellings made
only of integer arithmetic; their 670 pairs were evaluated under the
matcher's renaming in the five declared environments, 3,350 evaluations,
none skipped, 0 failures. 4 classes with two spellings commute `+` across a
string constant; they are counted, not claimed, and `string_append_not_comm`
says why.

**The operation (A7).** All 12 declared questions answered through the
frame layer, every script verifying under `python3 -I` and every mutant
failing; all 5 refusals by their declared code (`NOT_AN_EXPRESSION`,
`OUTSIDE_INDEX` twice, `NO_ARITHMETIC` twice). Six answers hold sites and
six are empty answers:

| question | answer |
|---|---|
| Q1 `n * (n + 1) // 2` | 6 sites, all archive — five copies of `ubp_unified_v5.py` and `DIM * (DIM + 1) // 2` in `glm_moonshine.py` |
| Q2 `x * x + y * y` | 6 sites: 3 live (`outside_frames.py`, `typed_operators.py`), 3 archive (`ubp_v28_oracle.py`, two copies of `value_geometry.py`) |
| Q3 `(lo + hi) // 2` | 2 sites, live (`engineering/speak.py`, `reasoning/symbolic.py`) |
| Q8 `len(s) - 1` | 8 sites, live |
| Q10 `w >> 12 & 4095` | 1 site, archive (`arc_agi_15/vendor/colour_space_bridge.py`) |
| Q11 `sum(row) / len(row)` | 28 sites, archive |
| Q4, Q5, Q6, Q7, Q9, Q12 | no site; Q4's bucket holds 92 expressions of the same shape, none structurally equal |

Q4 is the instructive empty answer: the archive computes `value ^ value >> 1`
(the Gray code), which uses one variable twice, so it is not structurally
equal to `a ^ b >> 1`, and the operation says so rather than offering the
nearest thing.

**Through the system.** The question asked on the command line,

```bash
python3 GLM.py -q "where is \`x * x + y * y\` computed?"
```

routes to the frame (`SURFACE frames`), and `tools ast-index --ask` asks it
directly.

**The marks, read together.** A1, A3, A5, A6 and A7 met; A2 missed by one
declaration error (§4); A4 missed, as §0 predicted from reading the code:
the Phase 64 form moves under renaming on a fifth of the query sites (94 of
467). So the answer to the question is yes — the structural key is a usable
retrieval key and the operation answers — while the Phase 64 address, read
as it is, is not one.

## 4. The declaration error, as it is

The pair `(a + b) + c` / `a + (b + c)` was declared *not* equal, under the
note "no associativity". It is equal: swap the outer operands of the second
to get `(b + c) + a`, then rename `b → a`, `c → b`, `a → c`. No
associativity is used; with three different variables, a renaming does the
work associativity would. Both procedures say so, and
`GLM.AstIndex.assoc_by_renaming` proves it. The pair is left in the cases
as declared, the reason is recorded in `DECLARATION_ERRORS` (added after
the measurement), and A2 is not met.

## 5. What is proved

`RequestProject/GLM/AstIndex.lean`, on a model of integer expressions
(variables, literals, `+ * -`):

* `structEq_sound` — if renaming `s` by `σ` gives `t` up to operand order,
  `t` under `ρ` has the value of `s` under `ρ ∘ σ`: A6 for every
  environment, not five;
* `bucket_complete` (from `key_rename` and `key_commEq`) — structurally
  equal terms share a key, so searching one bucket loses no match and an
  empty answer is an answer; `key_sub_ne_add` — the key is not constant;
* `sub_not_comm`, `string_append_not_comm` — the edges of the relation;
* `assoc_by_renaming` — the declaration error of §4.

It builds with no `sorry` and only the standard axioms.

## 6. Wiring

The frame `ast_index` (`runtime/ast_index_frames.py`) joins
`question_frames.frame_of` before the typed frames, behind the switch
`question_frames.AST_INDEX`; with it off, the layer is as it was. No earlier
phrasing is read by it: it needs `where … is` with the expression between
backticks. `python_substrate` is unchanged.

## 7. Defects found on the way

* **The rename perturbation renamed function names.** The first measurement
  renamed every `Name` node, including the name a call calls, which §1
  fixes; 173 of 467 queries then "failed" invariance for a reason that was
  the harness's, not the key's. It was repaired (a called name is not
  renamed) before any mark was read off, and the figures above are the
  repaired ones.
* **The reference's first draft skipped variables.** Its order enumeration
  compared a variable's name as an atom and so yielded nothing for any
  renamed pair; the declared pairs caught it before the measurement.

## 8. Limits, and what the round leaves

* **Statement level only.** A subexpression is not a site; `x * x + y * y`
  inside a larger return is not found. Indexing every subexpression is the
  next widening, and the bucket key extends to it unchanged.
* **No semantics.** `x ** 2` and `x * x`, or `a - b` and `a + -b`, are
  different here. A normal form for commutative-ring expressions would
  answer *semantically* equal, at the price of the exactness this relation
  has.
* **Duplicates in the archive.** `ubp_unified_v5.py` and `value_geometry.py`
  are present in several folders of the archive, so some classes count one
  expression several times; the answer lists every copy, which is the
  truth of the archive.
* **The Lean corpus.** The index sits *beside* the Lean corpus addresses (it
  is a third book of the system's own text), but a Lean term and a Python
  expression are not yet compared; a shared form for the arithmetic both
  write is the item that would join them.
* **The carrier as a near key.** The Phase 64 carrier ranks better than the
  token overlap; whether a repaired carrier (receiver renamed, keywords and
  constants kept) is a good *near-match* key for the queries that have no
  exact match is open.

## Disposition (Phase 106)

At the owner's direction the open items of §8 are **parked**: the structural
key does what it was measured to do — exact structural matches, at rank 1 for
every perturbed query — but an exact-match index of expressions was judged not
to move the machine's reasoning, and the follow-ups (a semantic normal form,
a near-match carrier, joining Lean terms) would extend retrieval further
rather than reasoning. What stays in the system, unchanged and still tested:
the index, the `where is … computed?` operation and `tools ast-index`.
Nothing was removed. The work taken instead is
[`DERIVATION_STUDY.md`](DERIVATION_STUDY.md) — derivations and proofs.

## 9. Re-running it

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.tools ast-index            # the stored report
PYTHONPATH=. python3 -m glm_universal.tools ast-index --live     # measure now (about a minute)
PYTHONPATH=. python3 -m glm_universal.tools ast-index --write    # re-take and store
PYTHONPATH=. python3 -m glm_universal.tools ast-index --ask "where is \`x * x + y * y\` computed?"
PYTHONPATH=. python3 -m pytest -q glm_universal/tests/test_ast_index.py
```

The snapshot is never re-taken by these; `tools ast-index --freeze` takes a
new one, which is a new study.
