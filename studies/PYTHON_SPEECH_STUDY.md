# Python speech: the GLM reading and evaluating Python on the substrate

## Tier 0 — the coarse read

**Question.** Can the GLM speak Python?

**Verdict.** Yes, as verified symbolic state transformation: all six pass marks declared before the measuring module existed were met, with 83 of 83 declared programs answered equal to CPython in type and value, 26 of 26 declared refusals named correctly, and 0 wrong.

**Deciding figure.** 83 of 83 value cases equal to CPython with every column-3 script printing VERIFIED True and every mutated claim caught; 26 of 26 refusals named; 0 wrong answers over a 7128-expression differential battery.

**Recomputed by.** `glm_universal.reasoning.python_speech.python_speech_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

The owner asked for the GLM to "speak" Python: to read Python symbols and
strings, evaluate them exactly on the substrate, and hand back every result
as a Three Column Thinking payload (language, exact mathematics, and a script
that re-derives the mathematics in an isolated interpreter), refusing by name
instead of estimating. "Reasoning" here means **verified symbolic state
transformation**: the machine does not guess what code returns, it derives it
and carries a certificate.

The request gave a construct-by-construct mapping (reproduced as §1) and a
refusal contract. This study turns each row into something that runs, fixes
the pass marks before the measuring code exists (§2), and reports what held
and what did not (§3 onwards).

## 1. The mapping, one line per construct

| Python construct | substrate reading | layer | what is built |
|---|---|---|---|
| `fractions.Fraction` | one exact coordinate `q_i ∈ ℚ` of a 24-coordinate carrier | rational | exact arithmetic; a float anywhere is refused |
| `int` | integer coordinate; dyadic plane `⌊q·2^k⌋` | integer | arbitrary precision; plane readings |
| `bool` | one `F₂` bit on a sub-register line | substrate | control inputs of the gates |
| `str`, `s[a:b:c]` | one code point per 24-bit block; position `i` is MOG cell `i mod 24` of carrier `⌊i/24⌋` | rational/integer | slice as the index map `i ↦ start + i·step`, with CPython's clamping |
| `& \| ^ ~` | the 8 vertical 3-bit Toffoli/Fredkin sub-registers | substrate | gate programs; the inverse program restores the inputs |
| `<< >>` | moves on the dyadic tower | integer | exact `n·2^k`, `⌊n/2^k⌋` |
| `tuple` (≤ 24) | one carrier, coordinates in order | rational | a longer tuple is refused (`CARRIER_OVERFLOW`) |
| `frozenset` | a 24-bit Golay mask | substrate | set algebra as mask algebra; Hamming distance |
| comparisons | sign of `a − b` over `ℚ` | rational | cross-scale or undeclared-unit comparison refused |
| `range` | tick generator `x_k = x_0 + kΔ` | integer | step cost counted; drives the delta-sigma loop (`ds_bits`) |
| `match`/`case` and `classify` | coset decoding against declared case codewords | substrate | branch at `d ≤ 3`; `AMBIGUOUS` at `d = 4`; `UNCORRECTABLE` at `d ≥ 5` |
| `ast.AST` | node types as Golay codewords, depth as dyadic plane | universal | a structural address in `ℚ²⁴` |

**Refusal contract** (named refusals, each a subclass of one exception):
`FLOAT` (a float literal, `float()`, or an operation whose Python result is a
float, such as `int / int`), `NONDETERMINISTIC` (`hash`, `id`, `random`,
clocks, `input`), `AMBIGUOUS` (deep hole, `d = 4`), `UNCORRECTABLE`
(`d ≥ 5`), `SCALE_MISMATCH`, `ORDER_UNDEFINED` (iteration over a set, whose
order CPython does not promise), `OUTSIDE_SUBSTRATE`, `CARRIER_OVERFLOW`,
`MUTABLE_CONTAINER`, `UNSUPPORTED`, `BUDGET`, and `PYTHON_ERROR` (CPython
itself would raise).

## 2. Pass marks, declared before the measuring module existed

The corpus is `overlay/glm_universal/evaluation/python_speech_cases.py`,
written and committed together with this section. CPython is the reference
for every value: the same source is run by CPython with the same pure-Python
prelude, and the GLM's value must equal CPython's in type and value.

* **P1 — values (derive).** Every value case is answered, and the answer
  equals CPython's in type and value. 0 wrong, 0 refused.
* **P2 — refusals (refuse).** Every refusal case is refused with the declared
  name. 0 answered.
* **P3 — Three Column Thinking.** Every answered case gives three columns; the
  column 3 script passes the exactness scan and prints `VERIFIED True` when
  run with `python3 -I` in a fresh process. **Mutation control:** changing
  the claimed final value makes the script fail, for every answered case.
* **P4 — reversible registers.** Each gate program (AND, OR, XOR, NOT, copy,
  multiplex) computes its Boolean function on all 8 lane states and its
  inverse program restores the lane exactly; on every declared operand pair
  the register result equals CPython's operator, including negative integers
  and integers wider than 24 bits.
* **P5 — Golay branching.** Over the whole radius-4 ball around a declared
  case codeword (12,951 words), with the declared cases held fixed: every
  word at distance ≤ 3 takes that branch, every word at distance 4 is refused
  `AMBIGUOUS` with six candidates in its coset, and no word is branched
  wrongly.
* **P6 — AST addresses (address).** (a) Every declared equivalent pair
  (commutative reordering, redundant parentheses, whitespace, consistent
  renaming of variables) shares one address. (b) Over the declared corpus of
  structurally distinct expressions, 0 address collisions.

A mark that is not met is recorded as not met; nothing here is re-declared
after the measurement.

## 3. What was built

* `overlay/glm_universal/reasoning/python_substrate.py` — where each Python
  construct lives on the substrate: the eight vertical 3-lane registers and
  their gate programs, the two's-complement register tower, dyadic shifts
  and plane readings, CPython's slice clamping as an index map with MOG cell
  addresses, frozensets as 24-bit masks, `classify` on the complete Golay
  decoder, the delta-sigma tick generator, AST canonical forms and addresses,
  and the plain-Python prelude.
* `overlay/glm_universal/reasoning/python_speech.py` — the evaluator
  (expressions, assignment and unpacking, `if`/`for`/`while`, `break`,
  `continue`, pure `def` functions with recursion, `match`/`case` with value,
  capture, wildcard, or- and sequence patterns and guards, `assert`), the
  static refusal gate, the payload with its three columns, the column-3
  script, the mutation control and the measurement.
* `GLM.py --python SOURCE` (repeatable) and `--python-file PATH` print the
  three columns (`-c 1,2,3`), `--verify-tct` runs column 3 in a fresh
  `python3 -I`, and `-f json` emits the payload. Exit code 0 when every
  program was answered.
* `python3 -m glm_universal.tools python-speech` re-takes P1–P6 and the
  battery.
* `RequestProject/GLM/PythonSpeech.lean` — the proofs behind the substrate
  operations (§5).

**How the registers are read.** A 24-bit word is eight registers of three
lanes (`reversible.BLOCKS_8x3`). A binary operation lines up three banks —
operand `a`, operand `b`, target `t` started at 0 — and runs one gate program
*vertically* through each lane `(a_i, b_i, t_i)`, with a constant rail `1`
available as a control. AND is one Toffoli; XOR is two rail-controlled
Toffolis; OR is `ab ⊕ a ⊕ b`, three Toffolis; NOT is two; COPY (used to load a
code point for `ord` and `chr`) is one; frozenset difference is one Fredkin
gate, which moves `a ∧ b` into `t` rather than erasing it. Every lane is run
back through the inverse program and must return `(a_i, b_i, 0)`; an
integer of any width and sign is laid on as many 24-bit carriers as its
two's-complement form needs, with the top bit as the sign, which reproduces
CPython's infinite two's complement.

**What is independent of what.** Integer and rational arithmetic is Python's
own exact `int` and `Fraction` arithmetic: that *is* the rational layer, and
nothing is gained by re-implementing it. Everything else the evaluator does
itself: bitwise operations through the gate programs, shifts as dyadic
multiplication and floor division, slices through the computed index map,
comparisons as the sign of `a − b` and ordinal-by-ordinal for strings, set
algebra as mask algebra, `classify` through the coset decoder. Column 3 then
checks every step with CPython's native operators, and re-runs the whole
program under CPython with the prelude, whose `classify` is a brute-force
distance search and shares no code with the decoder.

## 4. Results

**Summary.** Yes, as verified symbolic state transformation: all six pass marks declared before the measuring module existed were met, with 83 of 83 declared programs answered equal to CPython in type and value, 26 of 26 declared refusals named correctly, and 0 wrong.

*Recomputed by `glm_universal.reasoning.python_speech.python_speech_report`
and `differential_battery`; `tests/test_python_speech.py` holds them.*

| mark | faculty (D15) | declared | measured | verdict |
|---|---|---|---|---|
| P1 values | derive | every value case equals CPython, 0 wrong | 83 of 83 equal in type and value, 0 wrong, 0 refused | **met** |
| P2 refusals | refuse | every refusal case named as declared | 26 of 26; every refusal's own column 3 also verified (26 of 26) | **met** |
| P3 Three Column Thinking | derive | every script exact and VERIFIED True; every mutant fails | 83 of 83 exact and verified; 83 of 83 mutants caught | **met** |
| P4 registers | derive | all programs compute and invert; every operand pair equals CPython | 6 of 6 programs on all 8 lane states; 80 of 80 operations over 16 operand pairs, negative and wider than 24 bits included | **met** |
| P5 Golay branching | refuse | the 12951-word ball: branch at ≤ 3, AMBIGUOUS with six candidates at 4, none wrong | 2325 branched, 10626 refused AMBIGUOUS with six candidates, 0 wrong | **met** |
| P6 AST addresses | address | 10 of 10 equivalent pairs share an address; 0 collisions over the distinct corpus | 10 of 10 shared; 0 collisions over 57 distinct expressions | **met** |

**Post-hoc probe: the differential battery.** Declared after P1–P6, so it
is a probe and not a pass mark. Every expression `(a) op (b)` over 18
operand atoms (integers, booleans, fractions, strings, tuples, frozensets, a
range, `None`, and integers of 31 and 41 bits) and 22 operators: 7128
expressions. The dialect answered 2830, and **0 differ from CPython**. Of the
rest, 4150 are refusals where CPython raises the same exception class, 78
are float or complex results refused as `FLOAT`, 34 are budget refusals
(huge powers and shifts, not run under CPython), 4 are string formatting
(`'ab' % ()`), which the dialect declines, and 32 are string formatting
where CPython raises `TypeError` and the dialect refuses `UNSUPPORTED`. Two
defects were found by the battery before this write-up and fixed: `0 / 0` and
`0 ** Fraction(-5, 4)` were refused as `FLOAT` where CPython raises
`ZeroDivisionError` first, and a negative shift was refused without naming
its exception class.

**Control.** The same 83 value programs put to the existing question surface
(`GLM.py -q`, typed planner then grammar, newlines written as `; `): **0 of
83 solved**, each reported as an unrecognised query
(`glm_universal.runtime.python_tct.question_surface_control`). So P1 is
new derivation, not a relabelling of something the system already did.

## 5. What the Lean proves

`RequestProject/GLM/PythonSpeech.lean`, standard axioms only, no `sorry`:

* each gate program computes its function on a lane started at `t = false`
  and is a bijection of the eight lane states, undone by its reversed gates
  (`andP_spec` … `andnotP_spec`, `andP_inv` … `andnotP_inv`,
  `andP_bijective` … `andnotP_bijective`);
* bitwise operations act window by window, which is why a wide integer can be
  processed one 24-bit carrier at a time (`xor_mod_two_pow`,
  `xor_div_two_pow`, and the `and`/`or` versions);
* `n <<< k = n * 2 ^ k`, and over `ℤ`, `m >>> k = ⌊m / 2^k⌋`, which is
  Python's `>>` on negative numbers (`int_shiftRight_eq_floor_div`);
* with CPython's slice count, position `i` is read exactly when
  `start + i·step < stop` (`mem_slice_iff`, `slice_index_lt`);
* for any code of minimum distance 8, a subject within 3 of a declared case
  is within 4 of no other codeword (`branch_unique`), at exactly 4 no
  codeword is nearer (`deep_hole_no_nearer`), and the three verdicts are
  exhaustive and exclusive (`classify_trichotomy`). The Golay code is such a
  code (`GLM.Golay24.golay_min_distance_eight`), and the tie at 4 is exactly
  six codewords (`GLM.Golay24.ties_card_eq_six`).

## 6. Where it stops, said plainly

* **`d ≥ 5` never happens against the whole Golay code.** Its covering radius
  is 4 (`GLM.Golay24.covering_radius_le_four`), so every 24-bit word is
  within 4 of some codeword. `UNCORRECTABLE` is a verdict *relative to the
  declared cases*: it fires when the decoder's own codeword is not one of
  them. The request's table reads as if `d ≥ 5` were a region of the space;
  it is a region of the space minus the undeclared codewords.
* **Zero entropy means a bijection.** What is measured and proved is that
  every gate program is a bijection of the lane states, undone exactly. The
  thermodynamic reading (no Landauer cost) follows only for hardware that
  implements the gates reversibly; nothing here measures heat.
* **Equivalence is structural, up to stated rewrites.** Two expressions share
  an address when they agree up to commutative reordering, redundant
  parentheses, whitespace and consistent renaming. `+` and `*` are sorted as
  if commutative, which is true of numbers and false of strings and tuples.
  Deciding whether two programs compute the same function is undecidable in
  general (Rice's theorem), so no address could do it. The canonical form is
  the exact test; the `Q^24` carrier is its geometric shadow, and 0
  collisions over 57 expressions is a measurement, not an injectivity proof.
* **The dialect is a subset of Python.** No lists, dicts or sets outside
  `frozenset(...)` (`MUTABLE_CONTAINER`), no lambdas, classes, comprehensions,
  string methods, formatting, keyword arguments, exceptions or imports beyond
  `fractions` (`UNSUPPORTED`). A refusal is never a wrong answer; each is a
  place where a later round could widen the dialect.
* **Iteration over a frozenset is refused** (`ORDER_UNDEFINED`): under
  CPython 3.11 `frozenset({1, 9})` iterates as `1, 9` and the equal set
  `frozenset({9, 1})` as `9, 1`, because the order follows the hash table and
  the insertion history, not the value. A derivation that depended on it
  could not be re-derived from the value alone.
* **`int / int` is refused even when it divides evenly.** `6 / 3` is the
  float `2.0` in Python 3, and the contract forbids floats; the refusal
  names `Fraction(6, 3)` as the exact spelling.

## 7. Next

* Widen the dialect where the refusals cluster: string methods over code
  points (`upper`, `find`, `split`) are exact and cheap; list and dict
  literals could be admitted as immutable snapshots.
* Connect the planner to it: a question such as *what does
  `sum(range(3, 100, 7))` return?* could route through a typed frame to
  `speak`, so the grammar's surface reaches the same certificates.
* Use the AST address as a retrieval key: the structural address of a
  Python expression could be indexed alongside the Lean corpus addresses, so
  that the GLM finds prior derivations of a structurally equal expression.
