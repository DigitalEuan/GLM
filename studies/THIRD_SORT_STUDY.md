# The third sort: strings, tuples and ranges in the reverse grammar, and the dialect widened to string methods, lists and dicts

## Tier 0 — the coarse read

**Question.** Can the reverse grammar speak and read back strings, tuples and ranges — a third sort beside numbers and Golay masks, with count-first literals — and can the Python dialect answer string methods, list literals and dict literals exactly, refusing every mutation by name?

**Verdict.** Yes, for the declared fragment: the reverse grammar now speaks and reads back strings, tuples and ranges with count-first literals, and the dialect answers string methods, lists and dicts exactly as snapshots, refusing every mutation by name; no earlier answer moved, and the imperative grammar is not taken in this round.

**Deciding figure.** 28 of 28 say cases as declared (0 of 28 before the round); battery 1116 of 1116 terms read back, 1116 distinct sentences; 21 of 21 dialect programs inside; 63 of 63 dialect cases equal CPython (0 of 63 before), 63 scripts verified and 63 mutants rejected; battery 0 wrong of 2830 answered; 10 of 10 marks met.

**Recomputed by.** `glm_universal.runtime.third_sort_report.third_sort_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

Round 7 of the order of work in [`ROADMAP_STUDY.md`](ROADMAP_STUDY.md) and
[`STATUS.md`](../STATUS.md) §3.4: *the third sort* — I1 with M's strings,
tuples and ranges; then M's imperative grammar.

* **M's first item.** Reverse Three Column Thinking generates column 1 from
  column 2 through a declared grammar and reads it back. After Phase 68 the
  grammar spoke 36 of the 83 Phase 64 value programs; of the 47 outside, 22
  act on strings, tuples or ranges
  ([`REVERSE_TCT_STUDY.md`](REVERSE_TCT_STUDY.md) §8 and §9). Its §9 named the
  fix: *each is a finite sequence, and a third sort with count-first literals
  (as the masks have) would bring most of them in.*
* **I1.** The Phase 64 dialect refuses every list and dict
  (`MUTABLE_CONTAINER`) and every string method (`UNSUPPORTED`)
  ([`PYTHON_SPEECH_STUDY.md`](PYTHON_SPEECH_STUDY.md) §6, §7): *string methods
  over code points are exact and cheap; list and dict literals could be
  admitted as immutable snapshots.*

The two are one piece of work: the sequence values the dialect evaluates are
the values the grammar must be able to name.

M's second item, the imperative grammar (sentences for assignment, loops and
branches, so that the 7 programs with state have sentences), is the second
half of the round's track. It is not declared here; §6 says where it stands.

## 1. The grammar of the third sort

Every new term is spelled head first with a fixed number of arguments, and
every literal states its count before its items, so the extent of a literal
is fixed before its items are read — the same discipline that keeps the
mask literals of Phase 68 uniquely readable.

| dialect | term | sentence |
|---|---|---|
| `''` | the empty string | `the empty string` |
| `'Golay'` | a string of k ≥ 1 code points | `the string of` K `characters` C₁`,` …`,` Cₖ (`character` when K is one) |
| `()` | the empty tuple | `the empty tuple` |
| `(a, b, …)` | a tuple of k ≥ 1 entries of any sort | `the tuple of` K `entries` T₁`,` …`,` Tₖ (`entry` when K is one) |
| `range(a, b, c)` | the progression a, a + c, … short of b | `the range from` A `to` B `by` C (all three always spelled; `range(b)` is from zero, by one) |
| `s + t` | concatenation (two strings or two tuples) | `the concatenation of` S `and` T |
| `s * n` | repetition | `the repetition of` S `times` N |
| `s[a:b:c]` | CPython's clamped slice | `the slice of` S `from` A `to` B `by` C, with `the default` for an omitted start or stop; an omitted step is one |
| `s[i]` | the item at i (negative from the end) | `the item of` S `at` I |
| `chr(n)` | a one-character string | `the character of` N |
| `tuple(s)` | the entries of a sequence, as a tuple | `the entries of` S |
| `len(s)` | a number | `the length of` S (a mask's stays `the size of`) |
| `sum(s)` | a number (not a tuple literal, which stays the sum of its entries) | `the total of` S |
| `ord(s)` | a number | `the code point of` S |
| `min(s)`, `max(s)` of one sequence | an entry | `the least entry of` S, `the greatest entry of` S |

**Characters.** A character is spelled `capital` x for `A`–`Z`, `small` x
for `a`–`z` (x the lower-case letter), `digit` W for `0`–`9` (W the number
word), `space` for the space, and `code point` N for every other code point
up to `0x10FFFF`. The reader refuses `code point` N where one of the named
spellings exists, so every string has exactly one sentence.

**Statements.** `equals` and `does not equal` relate two terms of one sort;
`is in` and `is not in` relate an entry to a tuple or a range, or a string to
a string (a substring); `is less than`, `is at most`, `is greater than`,
`is at least` relate two strings or two tuples, in CPython's lexicographic
order.

**Closed.** A term of the third sort has no free variables: the sort is
asked for by `say:`, of closed terms, closed statements and programs whose
variables are bound by `let`. A program's variable may hold a sequence.

**Where it is asked.** `say:` asks the Phase 67–69 grammar first. Only when
that refuses (`NOT_IN_FRAGMENT` or `UNREADABLE`) is the text read with the
third sort; if the third sort reads it, its answer or its named refusal is
the answer, and otherwise the earlier refusal stands. So no earlier answer
can change.

**Refusals added:** `INDEX_OUT_OF_RANGE` (an item past either end),
`NOT_A_CHARACTER` (`ord` of other than one character, `chr` outside
`0 … 0x10FFFF`), `EMPTY_SEQUENCE` (the least or greatest entry of nothing),
`ZERO_STEP` (a range or slice by zero). An operation CPython rejects for its
types (a string concatenated with a tuple, the total of a string) is
`SORT_MISMATCH`; a free variable in a sequence term, or a boolean, is
`NOT_IN_FRAGMENT`.

## 2. Declarations — written before any code of the round

The declared cases are
`overlay/glm_universal/evaluation/third_sort_cases.py`, committed with this
section and before any code of the round. Every expected sentence was worked
by hand. CPython is the reference for every value and every truth.

### 2.1 The third sort (candidate M)

* **T1 — say.** Every `SAY_CASES` sentence is generated word for word; each
  answer carries the value (or the truth) CPython gives the source. **0
  wrong.**
* **T2 — refusals.** Every `SAY_REFUSALS` source is refused with its declared
  name, and every `READ_REFUSALS` sentence `UNREADABLE`.
* **T3 — read back, and the battery.** Every `SAY_CASES` sentence reads back
  to the structure read off its source. Over the battery — every term of
  depth at most two over `SEQ_BATTERY_ATOMS` with the sequence operators of
  §1 — every term's sentence reads back to the term, and no two distinct
  terms share a sentence.
* **T4 — column 3.** Every answered `SAY_CASES` case gets a generated script
  that re-reads every column-1 sentence with the declared reader, re-derives
  the value with its own evaluator (its own slice clamping, its own
  code-point arithmetic) and prints `VERIFIED True` in a fresh `python3 -I`;
  a copy with the claimed value mutated is rejected. 100 %.
* **T5 — the dialect's programs.** Each of the 21 `DIALECT_INSIDE` programs
  is read by the third sort, its sentence reads back to the same structure,
  and the value of the read-back structure equals CPython's and the
  dialect's. `tuple-concat` is declared to stay outside (a boolean).
* **T6 — no regression.** Every `say:` case and refusal declared by Phases
  67, 68 and 69 gives its declared answer (with Phase 68's `SUPERSEDED`
  list), and the round-two `W2` count of dialect programs inside the
  earlier grammar is unchanged.

### 2.2 The dialect widened (candidate I1)

* **D1 — values.** Every `STRING_METHOD_CASES`, `LIST_CASES` and
  `DICT_CASES` program is answered and equals CPython's value **in type and
  value** (a list is not a tuple; a dict's keys keep their insertion order).
  0 wrong, 0 refused.
* **D2 — refusals.** Every `DIALECT_REFUSALS` program is refused with its
  declared name; every Phase 64 refusal case keeps its name except the two
  `SUPERSEDED_REFUSALS`, which are answered and equal CPython.
* **D3 — column 3.** Every D1 answer's script prints `VERIFIED True` in a
  fresh `python3 -I`; a copy with the final claim mutated is rejected.
* **D4 — no regression.** Every Phase 64 value case is still answered and
  equals CPython, and the Phase 64 differential battery has 0 wrong answers.

**How the snapshot is kept immutable.** A list or a dict is a value, never a
place: a method that would change it (`append`, `update`, …), an item
assignment, and an augmented assignment to a name holding a list or a dict
(which CPython performs in place, visible through every alias) are refused
`MUTABLE_CONTAINER`. Building a new one (`xs + [3]`) is admitted. A list
holds at most 24 entries, as a tuple does (`CARRIER_OVERFLOW`). Set literals
and comprehensions stay refused.

**String methods over code points.** `find`, `index`, `count`,
`startswith`, `endswith`, `replace`, `split` with a separator, `join` and
`strip` with characters are computed over code points by the evaluator
itself. `upper`, `lower`, `isdigit`, `isalpha`, and `split` and `strip`
without arguments depend on Unicode's case and whitespace tables, which the
substrate does not hold; they are computed by code-point arithmetic over
ASCII and refused `OUTSIDE_SUBSTRATE` on a string holding any code point
above 127. A dict view (`keys`, `values`, `items`) is admitted where it is
consumed (iterated, counted, summed, turned into a list or a tuple) and
refused `UNSUPPORTED` as a final value, which no literal could rebuild.

### 2.3 What is proved

* **L — Lean.** Count-first literals are uniquely readable: for any item
  spelling with a left inverse on its own prefix, the count-first spelling
  of a list has a left inverse on its own prefix, so a literal followed by
  anything reads back to itself and leaves the rest. CPython's slice
  reading: every index the clamped index map produces lies inside the
  sequence, and for a positive step the slice's length is the ceiling of
  `(stop − start) / step` after clamping. A range's length and its
  membership test are the ones the evaluator uses. ASCII case mapping
  preserves the length and is undone on letters.

A mark that is not met is recorded as not met; nothing here is re-declared
after the measurement.

## 3. What was built

* [`reasoning/reverse_tct_seq.py`](../overlay/glm_universal/reasoning/reverse_tct_seq.py)
  — the third sort: its terms and statements, the realiser of §1 (characters
  spelled by name, every literal count first), a reader that extends the
  Phase 67 reader with the new heads and refuses a non-canonical spelling,
  the translation from CPython's AST, an exact evaluator with its own slice
  clamping and code-point arithmetic, `say_third_sort`, its own column-3
  script and mutation, and the depth-two battery.
* [`reasoning/reverse_tct.py`](../overlay/glm_universal/reasoning/reverse_tct.py)
  — `say` asks the earlier grammar first and falls to the third sort only on
  `NOT_IN_FRAGMENT` or `UNREADABLE`;
  [`reasoning/reverse_tct_script.py`](../overlay/glm_universal/reasoning/reverse_tct_script.py)
  dispatches a certificate of kind `say-seq` to the third sort's script.
* [`reasoning/python_containers.py`](../overlay/glm_universal/reasoning/python_containers.py)
  — the string methods over code points (ASCII where Unicode tables would be
  needed), the list and dict snapshots, and the dict views; the evaluator in
  [`reasoning/python_speech.py`](../overlay/glm_universal/reasoning/python_speech.py)
  admits list and dict displays, `list`, `sorted` and the methods, and refuses
  every in-place change `MUTABLE_CONTAINER`. The substrate prelude's `same`
  compares lists and dicts in type and value.
* [`evaluation/python_speech_cases.py`](../overlay/glm_universal/evaluation/python_speech_cases.py)
  — the Phase 64 refusals are kept as `PHASE64_REFUSAL_CASES`; the two the
  round answers are named in `SUPERSEDED_BY_PHASE94` (`list-literal`,
  `unsupported-attribute`) and `REFUSAL_CASES` is the other 24.
* [`runtime/third_sort_report.py`](../overlay/glm_universal/runtime/third_sort_report.py)
  and `tools third-sort` — the marks.

## 4. Results

*Recomputed by `glm_universal.runtime.third_sort_report.third_sort_report`
(`python3 -m glm_universal.tools third-sort`).*

| mark | result | met |
|---|---|---|
| T1 say | 28 of 28 sentences and values as declared, 0 wrong | yes |
| T2 refusals | 10 of 10 by name; 9 of 9 sentences `UNREADABLE` | yes |
| T3 read back | 28 of 28; battery 1116 of 1116 terms read back, 1116 distinct sentences | yes |
| T4 column 3 | 28 of 28 scripts `VERIFIED True`, 28 of 28 mutants rejected | yes |
| T5 the dialect's programs | 21 of 21 inside and agreeing with CPython and the dialect; `tuple-concat` outside, as declared | yes |
| T6 no regression | 69 earlier say cases and refusals, none moved; W2 inside 36, unchanged | yes |
| D1 values | 63 of 63 equal CPython in type and value (strings 24, lists 23, dicts 16) | yes |
| D2 refusals | 17 of 17 by name; 2 of 2 superseded Phase 64 refusals answered and equal CPython; the other Phase 64 refusals kept, 24 of 24 | yes |
| D3 column 3 | 63 scripts `VERIFIED True`, 63 mutants rejected | yes |
| D4 no regression | 0 of 83 Phase 64 values moved; differential battery 0 wrong of 2830 answered | yes |

**Before the round.** The same declared material, asked of the code as it
stood at the declarations' commit: 0 of the 28 say cases were said (the
earlier grammar refused each `NOT_IN_FRAGMENT`), and 0 of the 63 dialect cases
were answered — 30 refused `MUTABLE_CONTAINER`, 25 `UNSUPPORTED` (a string
method), and 8 failed with CPython's own `NameError` for `list` and `sorted`,
which the dialect did not hold.

**What a sentence looks like.** `"Golay"[1:4]` is said *the slice of the
string of five characters capital g, small o, small l, small a, small y from
one to four by one*, and column 1 continues *… equals the string of three
characters small o, small l, small a*. `sum(range(1, 11))` is *the total of
the range from one to eleven by one*, equal to fifty-five, the total taken by
the closed form rather than by listing. `"Golay"[9]` is refused
`INDEX_OUT_OF_RANGE: index 9 of a sequence of 5`.

**The battery.** Every term of depth at most two over the declared atoms with
the sequence operators — 1116 terms — is realised, read back to the same term,
and no two share a sentence: the measured counterpart of §5's unique
readability.

**In short.** Yes, for the declared fragment: the reverse grammar now speaks
and reads back strings, tuples and ranges with count-first literals, and the
dialect answers string methods, lists and dicts exactly as snapshots, refusing
every mutation by name; no earlier answer moved, and the imperative grammar is
not taken in this round.

**Which faculty moved.** Speech and verification: 28 sentences and 63
programs that were refused are now answered with a script a fresh interpreter
checks, and refusal stayed where it was — every mutation of a list or dict is
still refused by name, and no earlier answer changed.

## 5. What is proved rather than measured

`RequestProject/GLM/ThirdSort.lean` builds with the standard axioms only and
no `sorry` (L):

* **Count-first literals are uniquely readable.** For any item spelling
  `PrefixCode` (a spelling with a left inverse on its own prefix),
  `decItems_encItems` and `decLit_encLit`: the count-first literal followed by
  anything reads back to itself and leaves the rest; `listCode`: the literal is
  again a `PrefixCode`, so tuples of tuples of strings are as readable as
  tuples of numbers; `encLit_injective`: no two lists share a literal.
* **Ranges.** `length_rangeList` and `lt_rangeLen_iff`: `range(a, b, c)` with
  `c > 0` has exactly as many entries as there are `i` with `a + i·c < b`, the
  ceiling of `(b − a) / c`; `mem_rangeList_iff`: `x` is an entry exactly when
  `a ≤ x < b` and `c ∣ x − a`, the test the evaluator uses without listing;
  `two_mul_sum_rangeList`: twice the total of the `k` entries is
  `k · (2a + (k − 1)c)`, the closed form `sum` uses.
* **CPython's slice reading.** `clampIdx_bounds`; `slicePos_mem_bounds` and
  `sliceNeg_mem_bounds`: after negative indices are read from the end and both
  ends clamped, every index a slice reads lies in `0 … n − 1`, for either sign
  of step; `length_slicePos`: a positive-step slice reads the ceiling of
  `(stop − start) / step` indices after clamping.
* **ASCII case mapping.** `upper_lower_of_lower`, `lower_upper_of_upper`,
  `upper_idem`, `length_mapUpper`.

## 6. Limits, and what the round leaves

* **The imperative grammar is not taken.** M's second item — sentences for
  assignment, loops and branches, so that the 7 Phase 64 programs with state
  have sentences — was the second half of the round's track and was not
  declared here. It is the next item of the order of work.
* **Booleans stay outside the third sort.** `tuple-concat` is a comparison
  whose value is a boolean, and a boolean is not a term the grammar names;
  it stays outside as declared.
* **Unicode tables are not held.** `upper`, `lower`, `isdigit`, `isalpha`
  and whitespace `split`/`strip` are computed over ASCII and refused
  `OUTSIDE_SUBSTRATE` above code point 127. Holding Unicode's case and
  whitespace tables as a register would lift this.
* **Snapshots, not places.** A list or a dict is a value: aliasing and
  in-place change are refused rather than modelled. Sets and comprehensions
  stay refused. A dict view is not a final value.
* **The battery is depth two.** Unique readability is proved for every depth;
  the measurement covers depth two over the declared atoms.

## 7. Re-running it

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.tools third-sort            # T1-T6, D1-D4
PYTHONPATH=. python3 -m pytest -q glm_universal/tests/test_third_sort.py
python3 GLM.py -q "say: sum(range(1, 11))"
python3 GLM.py --python "'-'.join(sorted(['b', 'a']))"
cd .. && lake build RequestProject.GLM.ThirdSort                    # L
```
