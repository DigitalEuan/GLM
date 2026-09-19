# The anonymous register: where a structural address is the only reader

## Tier 0 — the coarse read

**Question.** Is there a register in which the geometric address is not a useful second opinion but the only faculty that can read the query at all?

**Verdict.** Yes: take the names away and the text search and the identifier address book fall to chance while the structural address holds.

**Deciding figure.** At k = 5 over 838 queries the text search falls from 714 hits to 73 and the identifier address book from 411 to 44 — chance is 49 — while the structural address holds 169 of its 238.

**Recomputed by.** `glm_universal.reasoning.anonymous.anonymous_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

**What this document is.**
[`ADDRESS_RETRIEVAL_STUDY.md`](ADDRESS_RETRIEVAL_STUDY.md) recorded a negative
result that has stood since it was taken: asked to retrieve a relevant
declaration, the geometric address beats chance several times over and is
beaten decisively by a plain lexical overlap of the statement text.
[`STACK_RELAY_STUDY.md`](STACK_RELAY_STUDY.md) then found the arrangement in
which the address still earns its place — gated on the text layer's own
confidence, the geometry *carries* the queries the text layer cannot read — and
was honest about the size of it: 14 queries out of 1,676, mostly constants and
calibration lemmas whose identifiers say very little. The question that round
left, in its own words, was whether the carry set is a **residue** or a
**class**:

> Is there a register where a geometric address is structurally the only
> reader?

This study answers yes, names the register before measuring it, and says what
the answer does and does not settle.

**The register.** A query is **anonymous** when its identifiers are not the
corpus's identifiers. That is the everyday situation of a goal that arrives
from somewhere else: a second formalisation of the same mathematics chooses
different names, a generated goal has none yet, an autoformalised statement
carries the vocabulary of its source rather than of the target library. The
exactly reproducible form of it — the one a measurement can be taken over — is
renaming: every identifier outside a small declared vocabulary is replaced by a
positional placeholder, and the placeholders are *checked* to be fresh against
the corpus rather than assumed to be. The declared vocabulary is Lean's own
words and the type names the structural feature map already counts, because
those belong to the language and to Mathlib rather than to this development.

**What was predicted, before the tables.**

1. The **text** search falls to chance, because its evidence is shared
   identifiers and there are none. §1.
2. The **identifier address book** falls with it, because it reads the same
   evidence through a coarser lens — which is the control that matters: it
   separates "geometry survives" from "this particular projection survives".
   §1.
3. The **structural address** does not fall, because a renaming cannot move a
   count of the syntax. §2.
4. Therefore the stack's **existing gate**, not re-tuned and not told about the
   register, fires on most of it and hands the query to the geometry. §3.

All four hold. Every table below is a **generated block**, emitted from the
measurement cache that `python3 -m glm_universal.corpus --remeasure` fills,
guarded by the digest of the Lean sources it was taken from. The formal half is
[`RequestProject/GLM/Anonymous.lean`](../RequestProject/GLM/Anonymous.lean);
the computational half is `glm_universal.reasoning.anonymous`; the test that
pins the two against each other is
`overlay/glm_universal/tests/test_anonymous.py`; and the report prints with

```bash
cd overlay
PYTHONPATH=. python3 GLM.py -q "report anonymous" --verify-tct
```

whose third column re-derives every figure below in a fresh interpreter.

---

## 1. What the renaming does to each faculty

The same 838 queries, twice: once as the statement is written, once with every
identifier outside the declared vocabulary replaced. Nothing else changes — the
corpus, the relevance ground truth, the depth each faculty is read to and the
window it is scored at are all the relay study's.

<!-- generated: anonymous-faculties -->
| faculty | hit@5, names kept | hit@5, names replaced |
|---|---|---|
| text — exact overlap of the identifiers | 722 (85.3 %) | 73 (8.6 %) |
| lexical — the identifier address book | 417 (49.3 %) | 44 (5.2 %) |
| **address — the structural address book** | 236 (27.9 %) | 161 (19.0 %) |
| name — substring search over the names | 267 (31.6 %) | 17 (2.0 %) |
| digest — a control that knows nothing | 57 (6.7 %) | 41 (4.8 %) |
| random — a seeded permutation | 34 (4.0 %) | 34 (4.0 %) |

846 queries over a corpus of 3383 declarations; chance at k = 5 is 5.7 %.  The text search collapses: yes; the identifier address book collapses with it: yes; the structural address holds: yes; and it leads every other faculty in this register: yes.
<!-- end generated -->

In numbers, and as a sentence rather than a table: take the names away and the
text search falls from 714 hits at k = 5 to 73 over the 838 queries; the
identifier address book falls from 411 to 44, at the 49 hits chance gives at
that depth; and the structural address holds 169 of its 238.
Yes, then, to the question at the head of this document — every faculty that
reads identifiers falls to chance, and the structural one does not.

Three readings.

**The leader is not merely reduced; it is emptied.** The text search loses more
than nine tenths of what it had and lands beside the seeded permutation. That
is not a surprise — it is the definition of the register — but it is worth
saying plainly that the standing negative result of this project is a statement
about a register in which names are informative, and that register is not the
only one.

**The identifier address book falls with it, and that is the control that
matters.** It is a geometric scheme: 24 coordinates, the same quantiser, the
same lattice. It collapses anyway, because what it projects onto the lattice is
the identifiers. So the result below is not "geometry survives anonymisation";
it is "the *structural* reading survives anonymisation", which is a sharper and
more falsifiable claim.

**The structural address keeps most of what it had.** What it loses is the one
coordinate a renaming genuinely destroys — how many declarations of the corpus
the statement cites, because a citation is a name — and §2 shows that this is
the only thing it loses.

---

## 2. Why: a renaming cannot move a count of the syntax

`GLM.Anonymous.features_anonymise` is the reason, and it is a theorem rather
than an observation: the kept skeleton of a statement is unchanged by renaming
anything outside the declared vocabulary, so *any* reading that is a function
of the skeleton is unchanged with it. The twenty-four structural counts are
such a reading.

The Lean statement is about an idealised token list, so the measurement checks
it against the **shipped** feature map, coordinate by coordinate, on every
query.

<!-- generated: anonymous-invariance -->
| reading | queries | what it means |
|---|---|---|
| queries whose syntax coordinates are untouched | 815 | 96.3 % of 846 |
| queries where a type-word coordinate moves | 31 | the declaration's own name spells `Nat`, `Int`, `Rat`, `Set` or `Decidable`, and the shipped map counts those words wherever they occur |
| queries where any other syntax coordinate moves | 0 | none, which is `GLM.Anonymous.features_anonymise` holding of the code |

The declared vocabulary a query keeps is 39 words.  Placeholders fresh against the corpus: yes.
<!-- end generated -->

That middle row is an audit finding rather than a rounding error, and it is
reported here rather than smoothed away. The shipped feature map counts the
type vocabulary — `Nat`, `Int`, `Rat`, `Real`, `Fin`, the containers, the
proposition types — *wherever those words occur in the statement text*,
including inside an identifier. So a declaration named
`proton_relErr_bounds` contributes to the rationals-and-reals coordinate
through the `Rat` inside `relErr`, and a renaming takes that contribution away.
The structural map is therefore not perfectly name-blind, and the exact extent
of the leak is now a measured number instead of an assumption: it touches 30 of
838 queries — the 808 others keep every syntax coordinate exactly — and moves
only those six coordinates, never a logical, numeric, bracket-depth or length
coordinate.

---

## 3. The stack hands the register over on its own

The gate is the relay study's gate, `1/10`, unchanged. Nothing in the stack was
told that this register exists.

<!-- generated: anonymous-relay -->
| reading | queries | gate fires on | text alone, hit@5 | the relay, hit@5 |
|---|---|---|---|---|
| names kept | 846 | 32 | 722 (85.3 %) | **726 (85.8 %)** |
| names replaced | 846 | 562 | 73 (8.6 %) | **120 (14.2 %)** |

The gate is 1/10, the one the relay study already carries, not re-tuned for this register.  It hands over on most of the register: yes; and the relay beats the text leader here: yes.
<!-- end generated -->

The hand-over is a theorem in the limit case: `GLM.Anonymous.relay_hands_over`
says that a leader whose confidence is the overlap it achieves has confidence
zero against a fresh renaming, so for any positive gate `Relay.relay` returns
the interleave. What the table adds is that the *measured* overlap is not
always exactly zero — the declared vocabulary is shared, so a query can still
score a little — and the gate fires on most of the register rather than all of
it.

---

## 4. Every claim, as it fell

<!-- generated: anonymous-verdict -->
| claim | verdict |
|---|---|
| `address_holds` | holds |
| `address_is_above_twice_chance` | holds |
| `address_is_the_clear_leader` | holds |
| `address_stays_above_the_control` | holds |
| `gate_hands_over` | holds |
| `lexical_collapses_too` | holds |
| `only_the_type_vocabulary_moves` | holds |
| `placeholders_are_fresh` | holds |
| `relay_beats_text_in_the_register` | holds |
| `text_collapses_without_the_names` | holds |
| `text_is_within_twice_chance` | holds |
| `text_leads_when_the_names_are_there` | holds |
<!-- end generated -->

---

## 5. What this settles, and what it does not

**Settled.** The carry set of the relay study is not only a residue. There is a
register — stated independently of the measurement, and reproducible from the
corpus alone — in which the structural address is the leading faculty by more
than a factor of two, and in which every faculty that reads identifiers is at
chance. The mechanism that finds it is the one already shipped: the gate fires,
the relay hands over, and the theorem says it must.

**Not settled, and worth stating plainly.**

* **This is not a reversal of the standing negative result.** Where names are
  informative the text search is still by a wide margin the better faculty, and
  nothing here changes that. The claim is about a different register, not a
  better score in the old one.
* **The absolute rate is modest.** One anonymous query in five is answered at
  k = 5 against roughly one in seventeen by chance. That is a real signal and
  a long way from a usable index; a register where a faculty is the only reader
  is not the same as a register where it reads well.
* **The register is constructed, not observed.** Renaming is a faithful model
  of a cross-vocabulary goal, but it *is* a model. The honest next step is a
  register that arrives anonymous on its own — goals from a second Lean
  development, or from a generator — scored against the same controls.
* **The citation coordinate is genuinely lost**, and the leak in the type
  coordinates found in §2 is a defect of the feature map rather than of the
  register. Both are recorded; neither is repaired here, because widening or
  narrowing the map is a design decision with its own measurement.
