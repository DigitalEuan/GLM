# Reverse Three Column Thinking: the language column generated from the mathematics and the script

## Tier 0 — the coarse read

**Question.** Can the script and the mathematics generate the language column, rather than the other way round, so that every generated sentence reads back to exactly the mathematics it came from, and do semantic operations taken on the mathematics give sentences with certificates — and, in round two (Phase 68), does that still hold over the integer layer, the bitwise operators, Golay masks and disjunction, with the generated questions handed on to the planner — and, in round three (Phase 69), over the integers, with floor quotient and remainder split into residue cases?

**Verdict.** Every declared mark of all three rounds is met: the widened language column reads back to exactly the mathematics with 0 collisions, negation is closed under De Morgan with no compound statement refused, 36 of the 83 dialect programs are now inside the fragment (8 before), and every relayed question is read, answered and read back by the planner with 0 disagreements, each answer checked by a script; round three decides entailment and bounds over the integers, every declared case as declared and every answer checked by a script.

**Deciding figure.** 216,723 widened terms and 18,500 mask terms round-trip with 0 collisions; 650 of 650 negated normal forms certified; 36 of 83 dialect programs inside, 36 agreeing; 32 of 32 planner handoffs agree or are consistent, against 0 of 15 answered when the sentences are given verbatim; 92 of 92 round-two scripts VERIFIED True and 84 of 84 mutated certificates rejected; over the integers 29 of 29 entailment and 10 of 10 bounds cases as declared, 34 of 34 scripts VERIFIED True and 34 of 34 mutants rejected.

**Recomputed by.** `glm_universal.reasoning.reverse_tct_script.reverse_two_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

The owner, opening the round:

> *I would like to try a reverse three column thinking function where the
> script and math generate the language column (if possible) as it may allow
> new extended semantic operations.*

Forward Three Column Thinking (`runtime/tct_engine.py`, and the Python
dialect's payload of Phase 64) goes *language → mathematics → script*: a
solver takes a question, and column 1 is a sentence **template** filled in by
the step that ran (*Compute 2 * 3 exactly on the integer layer*). Column 3
re-derives column 2 in a fresh interpreter; nothing re-derives column 1. A
column-1 sentence cannot be read back into the mathematics it describes, so it
is a caption, not a column.

The reverse direction makes column 1 a **function of column 2**: a declared
grammar realises an exact term or statement over ℚ as English, and a declared
reader parses that English back. When the realisation is injective and the
reader inverts it, column 1 carries exactly the information of column 2 and
can be checked the way column 3 is — by reading it back and comparing. That is
what makes semantic operations possible *on sentences*: an operation taken on
the mathematics (normalise, solve, negate, project, decide entailment) is
realised back into language, and the sentence it produces inherits the
operation's certificate.

## 1. The objects

**The fragment (column 2).** Exact terms over ℚ: rational literals,
variables (lower-case identifiers that are not grammar words), sum,
difference, product, quotient, negation, and a power with a literal
non-negative integer exponent. Statements: two terms related by one of `=`,
`≠`, `<`, `≤`, `>`, `≥`; a conjunction of statements. A program: assignments
followed by a result expression.

**Column 3 in.** A Python expression, chained comparison, `and` of
comparisons, or a program of assignments, in the Phase 64 dialect's syntax:
`int` and `Fraction(p, q)` literals, `+ - * / **`, unary `-`. It is read as
column 2 by the declared map: `/` is exact division over ℚ (as the dialect's
`Fraction` gives it), `-n` on a literal is the negative literal, `a < b < c`
is the conjunction of `a < b` and `b < c`. Anything else is refused as
`NOT_IN_FRAGMENT`.

**The realiser (column 2 → column 1).** Every term is realised *prefix
first*, so its extent is fixed by its head word:

| term | sentence |
|---|---|
| integer `n ≥ 0` | its number words (`twenty-one`, `one hundred five`), up to 10¹² − 1; digits beyond |
| integer `n < 0` | `negative` then the words of `−n` |
| non-integer `p/q` | `the fraction` P `over` Q |
| variable `x` | `x` |
| `A + B` | `the sum of` A `and` B |
| `A − B` | `the difference of` A `and` B |
| `A × B` | `the product of` A `and` B |
| `A ÷ B` | `the quotient of` A `and` B |
| `−A` | `the negation of` A |
| `A²`, `A³`, `Aⁿ` | `the square of` A, `the cube of` A, `the power of` A `with exponent` N |

Statements: `A equals B`, `A does not equal B`, `A is less than B`, `A is at
most B`, `A is greater than B`, `A is at least B`; a conjunction is its
statements joined by `, and`. A program is `let x be A.` per assignment and
`the result is A.` last.

**The reader (column 1 → column 2).** A recursive-descent parser for exactly
that grammar. Because every term production begins with a word no other
production begins with and has a fixed number of arguments, the grammar is
Polish notation spelled in words; unique readability is proved in Lean (§2,
V7) rather than hoped.

**The operations (the extended semantics).** Each takes sentences (in the
grammar above, or as dialect source), works on the mathematics, and realises
its answer back into a sentence, with a certificate a separate script can
check without the operation's code.

| operation | question form | answer |
|---|---|---|
| **say** | `say: SOURCE` | column 1 generated from the program; each step's equation also realised |
| **equivalent** | `equivalent: S1 ; S2` | `SAME` or `DIFFERENT`, decided exactly (polynomial normal form for terms; mutual entailment for linear statements) |
| **paraphrase** | `paraphrase: S` | generated sentences, each read back and certified equivalent to S |
| **negate** | `negate: S` | the sentence true at exactly the points where S is false (a relation statement) |
| **solve** | `solve for x: S` | `x equals …` (or a bound on `x` for an inequality), with the coefficient certificate |
| **entails** | `entails: P1, and P2 ; C` | `ENTAILS`, `CONTRADICTS` or `INDEPENDENT` with a Farkas certificate or two witness points |
| **bounds** | `bounds of x: P1, and P2` | the tightest bounds on `x` the premises imply, as a sentence, each bound certified |

Named refusals: `NOT_IN_FRAGMENT`, `UNREADABLE` (a sentence outside the
grammar), `DIVISION_BY_ZERO`, `NOT_POLYNOMIAL` (division by a term with a
variable), `NONLINEAR` (entailment, solve or bounds on a statement of degree
above one), `NONCONSTANT_COEFFICIENT`, `NO_UNIQUE_SOLUTION`,
`INCONSISTENT_PREMISES` (entailment or bounds from premises nothing satisfies
— the answer would be vacuous).

## 2. Declarations — written before any realiser, reader or operation code

The declared cases are
`overlay/glm_universal/evaluation/reverse_tct_cases.py`, committed with this
section and before `reasoning/reverse_tct.py` existed.

* **V1 — round trip.** Over the declared battery (every term of depth at most
  two over the atoms `x`, `y`, `0`, `1`, `2`, `-1`, `1/2` and the five binary
  and unary operators) and every declared case, `read(realise(t)) = t`: 100 %,
  and every declared sentence of `SAY_CASES` is produced word for word.
* **V2 — unambiguity, against a control.** Over the same battery, **0** pairs
  of distinct terms share a sentence. The control is the natural infix
  realiser (`two plus x times y`, no scope words): its collisions are counted
  and reported, not marked.
* **V3 — column 1 checked by a script.** For every answered declared case, a
  generated column-3 script, run in a fresh `python3 -I`, re-reads the
  column-1 sentence, compares it with the column-2 structure, re-checks the
  certificate with plain `Fraction` arithmetic, and prints `VERIFIED True`;
  a copy with a mutated certificate is rejected. 100 %.
* **V4 — entailment.** On `ENTAIL_CASES`, every declared verdict given, **0
  wrong**, every declared refusal refused by its name. The existing default
  path (`GLM.py --ask` through the router) is the control: its correct answers
  on the same questions are counted.
* **V5 — solve and bounds.** On `SOLVE_CASES` and `BOUNDS_CASES`, 0 wrong;
  every generated answer sentence is read back and certified: a solved form
  is equivalent to the equation (mutual entailment), every bound is entailed
  by the premises, and every non-strict bound is attained by a witness.
* **V6 — equivalence and paraphrase.** On `EQUIVALENCE_CASES`, 0 wrong; for
  every sentence of `PARAPHRASE_CASES`, every generated paraphrase reads back
  and is certified equivalent (0 non-equivalent paraphrases), and at least two
  distinct paraphrases are produced for each.
* **V7 — proved, not measured.** Lean: realisation is injective and
  prefix-free (unique readability), the infix control is not injective,
  negation is exact, a Farkas certificate refutes a system, the linear solved
  form is equivalent to its equation, and unsatisfiability of the premises
  with the negated conclusion is entailment.
* **V8 — the dialect's programs.** Over the 83 value programs of Phase 64,
  every program inside the fragment is given a generated column 1 that reads
  back to a program with the dialect's value: 0 wrong. How many are inside the
  fragment is reported, not marked — the fragment is narrower than the
  dialect by design.

## 3. Results

Every figure below is re-taken by `python3 -m glm_universal.tools
reverse-tct` (add `--quick` to skip the 163 fresh interpreters of V3 and the
control of V4); the suite holds them in `tests/test_reverse_tct.py`, the
battery, the scripts and the control as exhaustive cases.

### 3.1 V1 — round trip: met

The declared battery is 176,617 distinct terms. Every one reads back to
itself: 176,617 of 176,617. All 24 declared sentences of `SAY_CASES` are
produced word for word, and each reads back to the column 2 its source gives;
the 7 declared `SAY_REFUSALS` are refused as `NOT_IN_FRAGMENT` and the 5
`READ_REFUSALS` as `UNREADABLE`. Number words read back for every natural
number below twenty thousand (a test), and a spelling is accepted only in its
canonical form, so no second spelling of a number exists.

### 3.2 V2 — unambiguity against the control: met

**0** pairs of distinct battery terms share a sentence. The natural infix
realiser gives the same 176,617 terms only 170,933 distinct sentences —
**5,684** collisions, the familiar ones (`x plus y plus one` for both
groupings; `minus one` for the literal and for the negation of one). The
scope words are what the reverse direction pays for being readable, and the
sentences are long: `the sum of the product of two and x and three equals
seven` is the price of never being ambiguous.

### 3.3 V3 — column 1 checked by a script: met

94 answered declared cases carry a certificate; each one's column-3 script,
run in a fresh `python3 -I`, re-reads every column-1 sentence with the
declared reader, compares it with the column-2 structure and realises the
structure back to the sentence, requires every statement the certificate is
about to be a sentence of column 1, and re-checks the certificate with its
own evaluator: 94 of 94 print `VERIFIED True`. 69 of them carry a number or a
claim that can be changed so that the certificate no longer certifies (a
Farkas multiplier set to zero, a witness moved until the pattern of which
statements hold changes, a pairing's claim negated); all 69 mutated scripts
are rejected. The 25 without a mutation are the 24 `say` payloads, whose
check is the read-back alone, and the answer `nothing bounds x`, whose
certificate is empty.

Two mutations first *escaped*, and both were right to: moving a witness of
*x > 0 ⊬ y > 0* along `x` by seven leaves it a witness, and the scale of a
pairing between two identically-zero differences (`x * y == y * x` against
`x == x`) is free. The mutation was changed to move a witness until it
genuinely fails, and to negate the claimed relation when the numbers carry no
information; a certificate that stays valid under a change is not a detected
fault, and the first version of the mutant counted it as one.

### 3.4 V4 — entailment: met

34 of 34 `ENTAIL_CASES` get their declared verdict, **0 wrong**: 17
`ENTAILS`, 6 `CONTRADICTS`, 5 `INDEPENDENT` and the declared refusals
(`INCONSISTENT_PREMISES` once, `NONLINEAR` three times, `NOT_POLYNOMIAL`
once, `DIVISION_BY_ZERO` once). Linearity is judged on the normal form, so
`x * x - x * x + x == 1` is linear and `(x + 1) * 2 == 8` is decided.

The control: the 58 declared entailment, solve and bounds questions, as
question texts, on the default path as it stood before the reverse surface
(the Python dialect, the engineering surface, then the planner). All 58 go to
the planner; it answers **0** of them. Through the reverse surface **58 of
58** get the declared answer.

### 3.5 V5 — solve and bounds: met

14 of 14 `SOLVE_CASES` and 10 of 10 `BOUNDS_CASES` as declared, 0 wrong.
Every solved form carries a pairing certificate (the difference of the
equation is the coefficient times the difference of the solved form, checked
as a polynomial identity on a grid), every bound an entailment certificate,
and every non-strict bound a witness point where it is attained. `bounds of
t` under `t != 0` takes the hull of the two cases the disequality splits into,
and says so: the hole at zero is not a bound.

### 3.6 V6 — equivalence and paraphrase: met

18 of 18 `EQUIVALENCE_CASES` as declared, 0 wrong, including the declared
refusal of `x ** 2 >= 0` against `x == x`: the two are equivalent over ℚ, but
their normal forms differ and neither is linear, so the operation does not
decide it rather than guess. Every one of the 6 `PARAPHRASE_CASES` gets at
least two generated paraphrases (two to three), each read back and certified
equivalent; the paraphrase of `2 * x + 3 == 7` includes the derived sentence
`x equals two`.

### 3.7 V7 — proved: met

`RequestProject/GLM/ReverseTCT.lean` builds with the standard axioms only and
no `sorry`: `render_prefix_free` (unique readability), `render_injective`,
`renderStmt_injective`, `renderConj_injective`, `infix_not_injective`,
`negate_exact`, `farkas_refutes`, `entails_of_refuted`, the five pairing
lemmas, `solve_eq`, `solve_le_pos`, `solve_le_neg`, and `grid_identity` (the
polynomial identity check the scripts use, from Mathlib's combinatorial
Nullstellensatz). A literal's spelling is one token in the Lean model; that
the spelling is canonical is the Python check of §3.1, not a theorem.

### 3.8 V8 — the dialect's programs: met, narrowly

8 of the 83 Phase 64 value programs are inside the fragment (closed
arithmetic over `int` and `Fraction`, chained comparisons); all 8 get a
generated column 1 that reads back to a program with the dialect's value.
The other 75 use builtins, bitwise operators, strings, slices, floor division
or `match`, which have no sentence in this grammar yet.

## 4. What this is, under D15

**Derivation** moved: `solve`, `bounds` and `entails` produce answers no
register holds — a solved form, the tightest bounds the premises imply, a
verdict with a Farkas certificate — and realise them as sentences nobody
wrote. **Refusal** moved: eight named refusals, including the one that
declines to decide an equivalence it cannot certify. Nothing here is
**address**. The grammar itself is not reasoning; it is what makes the
reasoning's output language that can be checked.

## 5. What it is not

* The fragment is exact linear and polynomial arithmetic over ℚ. The
  sentences are canonical, not idiomatic: a reader who wants *two x plus
  three is seven* gets *the sum of the product of two and x and three equals
  seven*, because the idiomatic form is the ambiguous one (§3.2).
* Entailment is decided for linear statements only; nonlinear statements are
  refused rather than approximated.
* The reverse surface reads its own grammar and the dialect's syntax. It does
  not read the planner's questions, and none of the 177 contract cases, 63
  engineering questions, 33 cognition questions or 109 Python programs is
  read by it (the router census).

## 6. Next

* **Widen the fragment toward the dialect** where V8's 75 programs sit: floor
  division and modulus (integer layer), `abs`, `min`, `max`, and a sentence
  for a Golay mask, so that more of the Python payloads can be spoken and
  read back.
* **A disjunction** (`either … or …`) would make the negation of a
  conjunction expressible and close the one `NOT_IN_FRAGMENT` refusal of
  `negate`.
* **Hand a generated sentence to the planner** as a question, so that the
  language column of one surface becomes the input of another — the loop the
  reverse direction was asked for.

## 7. Round two — declarations, written before any round-two code

The owner, opening the round (Phase 68), on the three items of §6:

> *Only 8 of 83 Phase 64 programs fell inside the current linear arithmetic
> fragment over ℚ. Expanding the realiser to handle integer floor division
> (//), modulus (%), min/max, and Golay binary masks will bring a much larger
> portion of the execution engine into Reverse-TCT.* — *Adding disjunctive
> grammar will allow full negation closure for conjunctions (De Morgan's
> laws), eliminating the NOT_IN_FRAGMENT refusal when negating compound
> statements.* — *Connecting Reverse-TCT directly to the planner — so
> generated sentences become verified input prompts for downstream GLM layers
> — will complete the full bidirectionally certified language-math feedback
> loop.*

The declared cases are
`overlay/glm_universal/evaluation/reverse_tct_two_cases.py`, committed with
this section and before any round-two code. The Phase 67 corpus is not
edited; the four of its cases whose answer the widening changes on purpose
are listed there as `SUPERSEDED`, with the answer each must now give.

### 7.1 The widened objects

**Terms.** Beside the Phase 67 terms, each spelled head first with a fixed
number of arguments, so the grammar stays Polish notation in words:

| dialect | term | sentence |
|---|---|---|
| `a // b` | ⌊a / b⌋ | `the floor quotient of` A `and` B |
| `a % b` | a − b⌊a / b⌋ (the sign of b, as Python) | `the remainder of` A `and` B |
| `abs(a)` | \|a\| | `the absolute value of` A |
| `min(a, b, …)`, `max(…)` | right-nested binary | `the minimum of` A `and` B, `the maximum of` A `and` B |
| `a ** -n` | a⁻ⁿ, a ≠ 0 | `the power of` A `with exponent negative` N |
| `a & b`, `a \| b`, `a ^ b` on integers | two's-complement bitwise | `the bitwise and of`, `the bitwise or of`, `the exclusive or of` |
| `~a` | −a − 1 | `the complement of` A |
| `a << n`, `a >> n` | a·2ⁿ, ⌊a / 2ⁿ⌋ | `the left shift of` A `and` N, `the right shift of` A `and` N |
| `pow(a, n, m)` | (aⁿ) mod m | the remainder of the power |
| `sum((a, b, …))` | the left-nested sum | the sums |

The bitwise operators and shifts act on the integers of ℚ: an operand that is
not an integer is refused `NOT_INTEGER`, a negative shift `NEGATIVE_SHIFT`.
The dialect's `int` and `Fraction` are not told apart in column 2, which is
over ℚ.

**Golay masks — a second sort.** A mask is a set of positions of the 24-bit
Golay word, 0 to 23 (the dialect's `frozenset`). A literal is spelled with its
count first, so its extent is fixed before its positions are read: `the empty
mask`, `the mask of one position` P, `the mask of` K `positions` P₁`,` …`,` Pₖ
with the positions strictly increasing. Mask terms: `the intersection of`,
`the union of`, `the symmetric difference of`, `the set difference of` (the
dialect's `& | ^ -` on sets); numbers of masks: `the size of` A (`len`), `the
distance between` A `and` B (`hamming`); statements: P `is in` A (`in`), A `is
contained in` B (`<=` on sets), and `equals` / `does not equal`. A term of the
wrong sort is refused `SORT_MISMATCH`. Mask variables are not admitted.

**Statements — disjunction.** A statement is a conjunction of clauses, a
clause a relation or a disjunction: `either` R₁ `, or` R₂ … — conjunctive
normal form, spelled so that `either` opens every disjunction and `, or`
occurs only inside one, `, and` only between clauses. The dialect's `and`,
`or` and `not` over comparisons are read into this normal form by
distribution (so `x < 0 or x > 2 and y == 1` is two clauses).

**The operations, widened.** `negate` takes any statement: the negation of a
conjunctive normal form is the distribution of the negated relations (De
Morgan), which is again conjunctive normal form. `entails`, `bounds` and the
statement half of `equivalent` split every disjunction and every `abs`,
`min` and `max` over a term with a variable into cases (the splitting
condition joins the case), and decide each case as Phase 67 did: a certificate
is a Farkas refutation per case. Two terms with `abs`, `min` or `max` are
compared by entailment of their equation. A closed subterm is folded to its
value first, so `x > 7 // 2` is linear. Floor quotient, remainder and the
bitwise operators over a term with a variable are refused `NOT_POLYNOMIAL`:
over ℚ they are not piecewise linear with finitely many pieces.

**The relay — the planner loop.** `relay: Q` answers the reverse question Q
(a bare term or statement is `say:`), then hands what its column 2 holds to
the planner **as a question in the planner's own input language**, generated
from column 2, never from the English: a closed value v becomes `approximate
v to 20 places` and `what fraction rounds to R` (R the exact nearest 20-place
decimal of v); a closed relation, and every premise and conclusion of an
`INDEPENDENT` verdict at its witness points, becomes `is a less than b`. Each
handoff question is sent through the router, must be read by the planner
surface, and its answer is read back into column 2 by a declared answer
reader: `AGREES` (the planner's decimal is within 10⁻²⁰ of v, its fraction is
v, its order is the order of a and b), `CONSISTENT` (the planner declines to
order two equal values), `DISAGREES`, or `UNREAD`. What the planner returned is
then realised as sentences of the reverse grammar — *the absolute value of the
difference of D and v is less than …*, *F equals v*, *a is less than b* — so
the downstream answer re-enters column 1, and the column-3 script re-reads the
handoff questions, the planner's answers and those sentences, and re-checks
them with its own arithmetic. Named refusals: `NOTHING_TO_RELAY` (no closed
value, relation or witness), `OUT_OF_RANGE` (every value to hand off has a
numerator or denominator of 10¹² or more).

### 7.2 The marks

* **W1 — round trip, widened.** Every term of depth at most two over `x`,
  `1`, `1/2` with the three unary and thirteen binary operators, and every
  mask term of depth at most two over the four declared mask literals with
  the four set operators, reads back to itself with **0** collisions; the
  176,617-term Phase 67 battery still does; every `SAY_CASES` sentence is
  produced word for word; every `SAY_REFUSALS` and `READ_REFUSALS` case is
  refused by its name.
* **W2 — the dialect's programs.** Every program of `DIALECT_INSIDE` (36 of
  the 83) is inside the fragment, gets a generated column 1 that reads back,
  and evaluates to the dialect's value: **0 wrong**. The count inside is
  reported whatever it is.
* **W3 — negation closure.** Every `NEGATE_CASES` answer as declared, and
  over a declared battery of conjunctive normal forms (up to two clauses of
  up to two relations, over a set of relations in `x` and `y`), the negation
  is answered for every one, the double negation is certified equivalent,
  and the negation holds exactly where the statement fails at every point of
  a grid: **0 failures**.
* **W4 — the operations over disjunctions and pieces.** Every
  `ENTAIL_CASES`, `BOUNDS_CASES` and `EQUIVALENCE_CASES` answer as declared,
  **0 wrong**.
* **W5 — column 3.** Every answered round-two case and every answered Phase
  67 case gets a script that prints `VERIFIED True` in a fresh `python3 -I`,
  and every mutated certificate is rejected. Closed `say` answers now carry
  their value, so they can be mutated too.
* **W6 — the loop.** Every `RELAY_CASES` verdict as declared; every handoff
  question of a `RELAYED` case is read by the planner surface, answered and
  read back; **0** `DISAGREES`; every handoff question reads back to its
  column-2 value. Controls, counted and not marked: (A) the column-1 sentence
  of each relayed answer given verbatim to the default path — how many it
  answers; (B) the planner chained to itself without column 2 (its own
  `approximate` decimal handed to its own rational recognition) — how many
  values come back.
* **W7 — proved.** Lean: the widened term grammar (with the count-first mask
  literal and the negative exponent) is prefix-free and injective; the
  conjunctive-normal-form statement grammar is injective; negation by
  distribution is exact; the case splits of `abs`, `min` and `max` are
  exhaustive and exact; a refutation of every case is entailment; the
  floor-remainder identity with Python's sign convention; and the fact
  behind control B.
* **W8 — no regression.** Every Phase 67 declared case gives its declared
  answer, except the four `SUPERSEDED`, which give the new declared answer.

## 8. Round two — results

Taken by `PYTHONPATH=. python3 -m glm_universal.tools reverse-tct --two`
(W1–W6, W8) and `tests/test_reverse_tct_two.py`; the Lean file is
`RequestProject/GLM/ReverseTCTTwo.lean` (W7).

| mark | declared | measured | |
|---|---|---|---|
| W1 | 0 collisions; say, refusals, unreadable as declared | wide battery 216,723 terms and mask battery 18,500 terms, all round trips, 0 collisions; the Phase 67 battery 176,617 still round-trips; say 29 of 29 word for word (29 read back); refusals 9 of 9; unreadable 7 of 7 | met |
| W2 | the 36 of `DIALECT_INSIDE` inside, 0 wrong | 36 of 83 inside, 36 agree with the dialect's value, none inside that was not listed | met |
| W3 | negate as declared; the battery with 0 failures | negate 7 of 7; battery of 650 normal forms: answered 650, double negation certified 650, grid-exact 650 on 121 points | met |
| W4 | 0 wrong | entails 29 of 29, bounds 8 of 8, equivalent 12 of 12 | met |
| W5 | every script VERIFIED, every mutant rejected | round two 92 of 92 VERIFIED True, 84 of 84 mutants rejected (say 29, entails 23, bounds 7, equivalent 11, negate 7, relay 15); Phase 67 95 of 95 VERIFIED True, 80 of 80 mutants rejected | met |
| W6 | relay as declared; 0 `DISAGREES` | 20 of 20 relay cases as declared (15 relayed, 5 refused by name); 32 handoffs, 32 agree or consistent, 0 disagreements, 32 questions read back | met |
| W7 | the Lean statements | proved, standard axioms only (below) | met |
| W8 | Phase 67 as declared, 4 superseded | 111 of 111 right, 4 superseded | met |

**The controls of W6.** (A) The 15 relayed column-1 sentences given verbatim
to the default path: **0 of 15** answered — the planner reads its own input
language, not the reverse grammar, which is why the relay generates the
handoff question from column 2 and never from the English. (B) The planner
chained to itself without column 2: **11 of 13** values recovered. The two it
loses, −7/3 and 2/3, fail because the planner's `approximate` floors its last
place (`-2.33333333333333333334`, `0.66666666666666666666`), and the floored
decimal lies outside the half-unit interval its own rational recognition
reads; the relay hands over the nearest decimal instead and recovers both.
`chain_floor_misses` and `relay_nearest_hits` prove the 2/3 case.

**W7 in Lean** (`RequestProject/GLM/ReverseTCTTwo.lean`): `render_prefix_free`
and `render_injective` for the widened terms (count-first mask literal,
negative exponent); `renderStmt_injective` over the ten relations;
`renderClause_prefix_free` (a clause followed by nothing or by `, and`) and
`renderCNF_injective`; `negate_product_exact` (negation by distribution is
exact for any atoms whose negation is exact); `simplify_preserves` (dropping
duplicate atoms and clauses, tautologies and absorbed clauses keeps the
meaning); `abs_split`, `min_split`, `max_split`; `entails_of_cases_refuted`;
`floor_mod_identity`, `mod_sign_bounds`, `mod_sign_bounds_neg`,
`py_floor_example`, `py_mod_example`. As in round one, each head phrase and
each spelled number is one token in the model; that the phrases are distinct
and the spellings canonical is what the W1 batteries check.

**What went wrong on the way, recorded.** The first run of the W3 battery
certified the double negation of only 250 of the 650 normal forms: the
distributed negation of a negation grows as a product of clause lengths, and
the rest were refused as case blow-up. Adding the simplification
(`simplify_clauses`: duplicate atoms, tautologies, duplicate clauses,
absorption) brought it to 650 of 650, and `simplify_preserves` is the proof
that it keeps the meaning. A first run of W5 found one Phase 67 script failing
(e30): the script's affine check compared coefficients syntactically; it is now
a grid identity, which is what round one proved (`grid_identity`). The planner
does not return on some inputs — integers of 10¹² or more, and a floored
decimal whose half-interval misses the value — so the relay refuses the first
(`OUT_OF_RANGE`) and control B only asks the recogniser for a value inside the
half-interval.

**What the count means.** 36 of 83 is the fragment the reverse direction can
now speak *and* read back exactly. The other 47 are all refused
`NOT_IN_FRAGMENT`: 13 act on strings, 12 call a helper or method (`divmod`,
`plane`, `ds_bits`, `classify`, `bit_length`, `bit_count`, `.numerator`, a
`Fraction` read from a string), 7 are programs with state (loops, functions,
`match`, a conditional expression), 5 act on tuples, 4 on ranges, 4 mix
booleans with arithmetic, and 2 carry units. Floor quotient, remainder and
the bitwise operators over a *variable* stay refused `NOT_POLYNOMIAL`: over ℚ
they are not piecewise linear with finitely many pieces.

## 9. Next

* **Strings, tuples and ranges as sorts.** 22 of the 47 programs outside act
  on strings, tuples or ranges; each is a finite sequence, and a third sort
  with count-first literals (as the masks have) would bring most of them in.
* **Programs, not only terms.** 7 are programs with state; a sentence per
  assignment and loop (a small imperative grammar with the same count-first
  discipline) would bring them in.
* **Integer variables.** Floor quotient and remainder over a variable are
  piecewise linear over ℤ with a bounded divisor; admitting a declared integer
  sort would let `entails` split them into finitely many residue cases.
* **The loop, further.** The relay hands values and orders to the planner; the
  next step is to hand a whole `INDEPENDENT` verdict's witness to the
  question layer as a follow-up question, and to let the planner's answer
  choose the next reverse operation.

## 10. Round three — the integer sort: declarations, written before any round-three code

Phase 69 takes the third item of §9 (candidate M of `STATUS.md` §3.4): *an
integer sort, so that floor quotient and remainder over a variable split into
finitely many residue cases instead of being refused `NOT_POLYNOMIAL`.* The
declared cases are `overlay/glm_universal/evaluation/reverse_tct_int_cases.py`,
committed with this section and before any round-three code; every expected
answer in it was worked by hand. The Phase 67 and Phase 68 corpora are not
edited, and no answer of theirs changes: the integer sort is asked for by its
own question forms, so the rational operations answer exactly as before.

### 10.1 The objects

**Two question forms.** `entails over the integers: P1 ; P2 ; C` and
`bounds over the integers of x: P1 ; P2`. The premises and conclusion are the
sentences (or dialect sources) of round two; every variable in them ranges
over ℤ. The verdicts are those of round one (`ENTAILS`, `CONTRADICTS`,
`INDEPENDENT`, `BOUNDED`, `FREE`) and the refusal `INCONSISTENT_PREMISES`,
now meaning *no integer point*; each answer sentence says *over the integers*.

**The residue split.** A floor quotient or remainder `A // b`, `A % b` whose
dividend `A` has a variable is admitted when the divisor `b` is a nonzero
integer constant with `|b| ≤ 64` and `A` is linear with integer coefficients
and an integer constant. It is replaced by a fresh integer `q` (the quotient)
and a literal residue `r`, one case per residue — `0 … b − 1` for `b > 0` and
`b + 1 … 0` for `b < 0`, Python's sign convention — with the equation
`A = b·q + r` joining the case. The same `(A, b)` gets the same `q` in every
occurrence. Innermost first, so a nested floor quotient is split after the one
inside it. Refusals: a dividend of degree above one `NONLINEAR`; a divisor or
dividend that is not integer-valued `NOT_INTEGER`; `|b| > 64`
`NOT_IN_FRAGMENT`. The bitwise operators over a variable stay refused
`NOT_POLYNOMIAL`.

**The integer decision, per case.** Every row is scaled to integer
coefficients; a strict row `e < 0` becomes `e + 1 ≤ 0` (over ℤ); every row
`Σ aᵢxᵢ + k ≤ 0` is divided by `g = gcd(aᵢ)` with the constant rounded up,
`Σ (aᵢ/g)xᵢ + ⌈k/g⌉ ≤ 0` (exact over ℤ). Fourier–Motzkin elimination then
runs with every derived row tightened the same way, variables with a unit
coefficient in an equation eliminated first. A derived row `0 + k ≤ 0` with
`k > 0` refutes the case, and the **certificate is the derivation**: the input
rows, and for each derived row the two rows and the positive multipliers that
combine it, pruned to the ancestry of the contradiction. When no contradiction
is derived, an integer witness is sought — back-substitution choosing an
integer in each interval, then a bounded search around it — and checked
exactly against every row. If neither a refutation nor an integer witness is
found the answer is the new refusal `INTEGER_UNDECIDED`, by name: integer
elimination with rounding is sound but not complete, and the refusal is the
honest place where it stops.

**Bounds over the integers.** The rational projection gives a candidate
integer bound `c` (rounded inward). It is certified by refuting the premises
with `x ≤ c − 1` (resp. `x ≥ c + 1`) and shown tight by an integer witness at
`x = c`; if the witness is not found, `c` moves one step inward after a
refutation at `c`, at most 64 steps, else `INTEGER_UNDECIDED`.

### 10.2 The marks

* **X1 — entailment over the integers.** Every `ENTAIL_CASES` verdict as
  declared, **0 wrong**, every declared refusal by its name.
* **X2 — bounds over the integers.** Every `BOUNDS_CASES` answer as declared,
  word for word, **0 wrong**; every bound certified by a refutation and
  attained by an integer witness.
* **X3 — column 3.** Every answered case gets a generated script that re-reads
  column 1 and re-checks the certificate with its own arithmetic — the residue
  cover, each tightening, each combination, each witness — and prints
  `VERIFIED True` in a fresh `python3 -I`; a copy with a mutated certificate is
  rejected. 100 %.
* **X4 — against brute force.** Over the declared battery (every ordered pair
  of distinct atoms of `BATTERY_ATOMS_X` and of `BATTERY_ATOMS_XY`, each
  question carrying the box `−6 ≤ v ≤ 6` for its variables, and every atom
  alone as a `bounds` question), every answered verdict and bound agrees with
  enumerating the box: **0 disagreements**. How many are answered rather than
  refused `INTEGER_UNDECIDED` is reported, not marked.
* **X5 — the control.** The same `ENTAIL_CASES` and `BOUNDS_CASES` asked over
  ℚ (`entails:`, `bounds of x:`): how many are refused `NOT_POLYNOMIAL` and how
  many are answered with a different verdict — counted, not marked.
* **X6 — proved.** Lean: the residue split is exact and exhaustive with
  Python's sign convention; the tightening (strict to non-strict, division by
  the gcd with the constant rounded up) is exact over ℤ; a non-negative
  combination of valid rows is valid; a refuted derivation leaves no integer
  point; and the example behind `i22` — `2x = 1` has a rational solution and no
  integer one.
* **X7 — no regression.** Every Phase 67 and Phase 68 declared case gives its
  declared answer.

## 11. Round three — results

Taken by `PYTHONPATH=. python3 -m glm_universal.tools reverse-tct --three`
(X1–X5) and `tests/test_reverse_tct_int.py`; the Lean file is
`RequestProject/GLM/ReverseTCTThree.lean` (X6); the code is
`reasoning/reverse_tct_int.py`.

Round three decides entailment and bounds over the integers: every declared
case is answered as declared, and every answer is checked by a script.

| mark | declared | measured | |
|---|---|---|---|
| X1 | every `ENTAIL_CASES` verdict, 0 wrong | 29 of 29 as declared (24 verdicts, 5 refusals by name), 0 wrong | met |
| X2 | every `BOUNDS_CASES` answer word for word, 0 wrong | 10 of 10 as declared, 0 wrong; every bound refuted beyond and attained by an integer witness | met |
| X3 | every script VERIFIED, every mutant rejected | 34 of 34 scripts VERIFIED True (24 entailment, 10 bounds), 34 of 34 mutated certificates rejected | met |
| X4 | 0 disagreements with the box | 102 entailment and 14 bounds questions, all 116 answered (0 `INTEGER_UNDECIDED`), 0 disagreements | met |
| X5 | counted, not marked | over ℚ: 20 of the 29 entailment cases refused `NOT_POLYNOMIAL` and the other 9 answered differently (`INDEPENDENT` or `CONTRADICTS` where the integers decide `ENTAILS` or `INCONSISTENT_PREMISES`); 5 of the 10 bounds cases refused, the other 5 answered with the rational bounds; 0 answered the same | — |
| X6 | the Lean statements | proved, standard axioms only (below) | met |
| X7 | Phase 67 and 68 cases as declared | `tests/test_reverse_tct.py` and `tests/test_reverse_tct_two.py` pass with the exhaustive cases on; the rational operations answer as before | met |

**What the control shows.** The integer sort does not only admit the
floor-and-remainder cases the rational decision refuses; it changes nine
answers the rational decision *gives*: `x > 2` does not entail `x ≥ 3` over ℚ
and does over ℤ, and `2x = 1` is consistent over ℚ and has no integer point.
Asking over the wrong domain gives a confident answer to a different question,
which is why the domain is part of the question form and each answer's column
1 says *over the integers*.

**X6 in Lean** (`RequestProject/GLM/ReverseTCTThree.lean`):
`residue_split_pos` and `residue_split_neg` (Python's floor quotient and
remainder of integers, as round two defines them over ℚ, are exactly the
quotient and residue of `a = b·q + r` in the residue range of `b`),
`residue_exists_pos` and `residue_exists_neg` (the residue cases are
exhaustive), `strict_tighten` and `gcd_tighten` (both tightenings exact over
ℤ), `combine_sound`, `step_sound`, `derivation_sound` and `refuted_no_point`
(a derivation of positive combinations each followed by a gcd tightening, as
the column-3 script checks it, keeps every integer point, so a derived
contradiction leaves none), `rational_refutation_suffices`, and
`two_x_eq_one` (declared case `i22`).

**Where it stops, recorded.** Elimination with rounding is sound and not
complete. Pugh's system `27 ≤ 11x + 13y ≤ 45`, `−10 ≤ 7x − 9y ≤ 4` has
rational points and no integer point, and neither the tightened elimination
nor the bounded witness search settles it: the answer is `INTEGER_UNDECIDED`,
by name, and the test suite holds that. No declared case and no battery
question reached the refusal. A `FREE` side of a bound is claimed from a
rationally unbounded case that has an integer point (an integer hull has the
recession cone of its polyhedron when it is non-empty); the script checks
every stated bound but does not certify unboundedness, as in rounds one and
two.

**What it is not.** The integer sort is asked for by its own two question
forms; the rational operations are unchanged, and `relay:` on an integer
answer is refused `NOTHING_TO_RELAY` — the relay reads only the certificate
kinds of rounds one and two.

## 12. Next

* **Strings, tuples and ranges as sorts**, and **programs, not only terms** —
  §9's first two items, still open.
* **A complete integer decision.** The Omega test's dark shadow and splinters
  would decide what `INTEGER_UNDECIDED` now refuses, with certificates of the
  same derivation shape plus finitely many splinter cases.
* **The loop, further.** Let `relay:` read the integer certificate kinds (a
  bound's witness, an `INDEPENDENT` verdict's two integer points), and hand an
  `INDEPENDENT` verdict's witness to the question layer as a follow-up.
