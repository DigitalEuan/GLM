# Tool values — a tool's answer handed to the planner as a number

## Tier 0 — the coarse read

**Question.** Can the stepwise planner take a number from a tool — a continued-fraction term, a convergent, the nearest fraction under a denominator bound, a gate distance, a Leech shell count — and compose it with arithmetic, predicates and function forms, without changing any answer the GLM already gives?

**Verdict.** The planner does now: there are ten noun-phrase patterns in nine shapes. A part the typed planner refuses is now read as one number a tool computes, with a selector that picks it out of the tool's figures. The step goes through the same step gate as any planner step, and the chain's column-3 script re-runs the tool in a fresh interpreter. Two new tools answer with a fraction rather than a term list: `convergent` and `best approximation`. The second is checked by trying every denominator, with no continued fractions, up to a bound of 20,000. All 8 marks were met. On the held-out rewordings, 10 of 12 were read and all 10 were right; three values on the hand-written answer sheet were wrong and are recorded as such.

**Deciding figure.** 8 of 8 marks; 17 of 17 composed questions as declared (13 answered, 4 refused as declared); 13 of 13 chains verified in a fresh interpreter, 65 of 65 mutants caught; 136 of 136 surd convergents and 14 of 14 pi convergents agree with independent references; 100 of 100 nearest fractions agree with the exhaustive search; 0 of 404 declared texts read and 0 of 30 stepwise cases moved; 8 of 8 single-value questions; 10 of 12 held-out rewordings read, 10 right, 0 wrong.

**Recomputed by.** `glm_universal.evaluation.tool_values_cases.measure`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. What this document is

The study of Phase 137. The owner asked for the GLM's reasoning abilities and
scope to grow, and allowed experiments. This round takes the first line of
`STATUS.md` §2.2, *the connected machine, the rest*: a tool's answer was not
handed to the planner as a value, so *twice the third term of the continued
fraction of pi* was refused (`UNKNOWN_STEP: the planner does not answer 'what
is the third term of the continued fraction of pi'`).

The stepwise planner of Phase 72 already reads the shape of such a question
(*twice …*, *… minus …*, *the gcd of … and …*, *is … prime?*, *then …*). What it
lacked was a **leaf**: every part that is not a number is asked of the typed
planner, and the typed planner holds no continued fraction. The round adds that
leaf, and two tools whose answers are worth composing.

**Order of work, stated plainly.** The rational-approximation module and the
two tools were written and tried by hand first. Then the tool-values reader and
its hook in the stepwise planner, then `RequestProject/GLM/ToolValues.lean`
(built with every proof complete), then the batteries and marks of §§3–4. The
held-out rewordings (§3.3) were written before they were first run, with the
value each should get; the rest of the batteries were written by someone who
had already seen the tools answer. Two things were changed after the first
measurement, and both are recorded in §5.

## 1. What was built

### 1.1 The leaf (`runtime/tool_values.py`)

`read_value(phrase)` reads a noun phrase naming one number a tool computes and
returns the `tool …` text that computes it and a **selector** that picks the
number out of the tool's figures. There are ten noun-phrase patterns in nine
shapes (the Leech-shell shape has two spellings):

| pattern | example | tool text | selector |
|---|---|---|---|
| `cf-term` | *the third term of the continued fraction of pi* | `tool continued fraction pi terms 3` | `index terms 2` |
| `cf-term-number` | *term 7 of the continued fraction of pi* | `… pi terms 7` | `index terms 6` |
| `cf-fold` | *the sum of the first 5 terms of the continued fraction of sqrt(2)* | `… sqrt(2) terms 5` | `fold terms sum 5` |
| `convergent` | *the (numerator of the) fourth convergent of pi* | `tool convergent 4 of pi` | `value value` / `part value numerator` |
| `approximation` | *the closest fraction to sqrt(2) with denominator at most 100* | `tool best approximation sqrt(2) denominator 100` | `value value` |
| `gates` | *the number of gate moves from 0x000007 to 0x000005* | `tool gates 0x000007 to 0x000005` | `value moves` |
| `kissing` | *the kissing number of the Leech lattice* | `tool llvq` | `value kissing_number` |
| `leech-shell` (×2) | *the number of vectors of norm 6 in the Leech lattice* | `tool llvq` | `entry shell_counts 24` |
| `moonshine` | *the dimension of V_3* | `tool moonshine` | `index graded_dimensions 3` |

The folds are `sum`, `product`, `max`, `min` and `mean`. *Below*, *less than*,
*under* and *smaller than* lower the denominator bound by one. A tag-length
pattern was written and then removed before any measurement: the proved
quantity is a floor (`GLM.Golay24.tag_length_floor`), and reading *the smallest
number of bits a tag needs* as that floor would have stated a bound as if it
were the answer.

### 1.2 The hook in the stepwise planner (`runtime/stepwise.py`)

`Leaves._ask` asks the typed planner first, exactly as before. Only when it
refuses (or answers with a number this chain cannot re-derive) does
`Leaves._tool_value` try the reader. If the tool refuses, the step refuses, by
name, and so does every reading that needs it. The step is an ordinary
`planned` step whose computation is `tool <name>` and whose detail carries the
tool text and the selector; it goes through the same step gate
(`stepwise_script.step_check`). Where the typed planner holds the number but
the chain could not re-derive it (the kissing number), the tool's number is
used only if the two agree, and otherwise the step is refused
`DERIVATIONS_DISAGREE`. `stepwise.TOOL_VALUES` switches the leaf off, for the
round's control.

The chain's column-3 script (`stepwise_script._SCRIPT`, `tool_value`) re-runs
the tool in a fresh `python3 -I` and applies the selector with its own code.

### 1.3 A question that is only a tool value (`runtime/router.py`)

After every surface has refused and no Phase 136 opening matches,
`_phrased_tool` now tries `tool_values.answer_text`. As before, the result is
kept only if the tool answers, so no answer changes and no refusal is replaced
by another refusal.

### 1.4 Two tools (`reasoning/rational_approx.py`, `runtime/toolbox.py`)

Both answer with a fraction rather than a term list.

* **`tool convergent K of X`** gives the `K`-th convergent from the certified
  terms, using the forward recurrence `p_k = a_k p_(k-1) + p_(k-2)`. A rational
  written plainly is expanded exactly, and a convergent past its last term is
  refused.
* **`tool best approximation X denominator N`** gives the fraction nearest `X`
  among those with denominator at most `N`. The candidates are the last
  convergent within the bound and the semiconvergent below the next one. The
  nearer is decided by the side of their midpoint the value lies on, read at
  rising precision up to `2^-4096`; if that precision is reached without a
  decision, the tool refuses. For `N ≤ 20000`
  (`rational_approx.EXHAUSTIVE_CAP`) the answer is also checked by trying every
  denominator with the two numerators either side of `q·mid`. That check uses
  no continued fractions, and a disagreement makes the tool refuse. Above the
  cap the answer says the check was not run.

The Leech-shell tool `llvq` now also returns its shell counts as a figure
(`shell_counts`), so the selector can read them.

## 2. What is proved (`RequestProject/GLM/ToolValues.lean`)

All of these build with no `sorry` and use only the standard axioms
(`propext`, `Classical.choice`, `Quot.sound`).

| theorem | statement |
|---|---|
| `cfPrefix_take`, `cfPrefix_getElem`, `cfPrefix_length` | the first `k` entries of a longer prefix are the shorter prefix; entry `k` is `cfTerm k x` |
| `select_certified` | entry `k` of the prefix certified from `[lo, hi]` is the `k`-th term of every `x` in the interval |
| `fold_certified` | the sum of the first `m` entries of that prefix is the sum of the first `m` terms of `x` |
| `conv_append`, `conv_cons` | appending a term multiplies the convergent matrix on the right: the forward recurrence |
| `conv_det`, `det_cvM` | `det (conv l) = (-1)^length` |
| `conv_coprime` | so the convergent the tool prints is in lowest terms |
| `conv_pos`, `cfValue_eq_conv` | with every term after the first at least one, `p / q` is the value of the finite expansion |
| `closer_iff_midpoint` | `\|x − c₁\| < \|x − c₂\|` iff `0 < (c₁ − c₂)(x − (c₁ + c₂)/2)` |
| `nearer_of_margin` | a reading within `ε` that separates two fractions by more than `2ε` decides the nearer |
| `farther_than_candidate` | for denominator `q`, every numerator other than `⌊q·mid⌋` and `⌊q·mid⌋ + 1` is at least `1/q` farther from `mid` than one of them |
| `conv_pi_four` | `conv [3, 7, 15, 1] = !![355, 333; 113, 106]` |

**Not proved here:** the classical theorem that the nearest fraction with a
bounded denominator is always the last convergent within the bound or the
semiconvergent below the next one. The tool relies on it to pick its two
candidates. Up to the cap, the exhaustive check, whose soundness is the last
three rows, stands in for it.

## 3. The batteries (`evaluation/tool_values_cases.py`)

### 3.1 Composed questions (`COMPOSED`, 17)

There are 13 that should be answered, each with its exact value: the questions
of §0, a sum of two tool values, a primality test, a gcd and an lcm with a
convergent's parts, a quotient of the kissing number, a gate distance plus one,
and a fold over a product. There are 4 that should be refused: a 50th term,
above the 40-term cap; the continued fraction of *banana*; an unreachable gate
target; and the fourth convergent of `7/3`, which has two terms.

### 3.2 Single values (`SINGLE`, 8)

Eight questions that are one tool value each, routed through the router, each
with the fragment its answer must contain.

### 3.3 Held out (`HELD_OUT`, 12)

Twelve rewordings, each with the value it should get. They were written before
they were first run and were not tuned afterwards. The mark (V8) was declared
with them: no answer may be wrong, and at least 8 must be right.

### 3.4 The grid (`APPROX_GRID`, 100)

Ten reals (pi, e, `sqrt(2)`, `sqrt(3)`, `sqrt(5)`, `2^(1/3)`, the golden ratio,
`pi^2`, `sqrt(11)/3`, `1/7 + sqrt(2)`), each taken with ten bounds from 1 to
4000.

## 4. The marks

| mark | what is measured | pass |
|---|---|---|
| V1 | the Lean file | present, every theorem of §2 named, no `sorry` |
| V2 | `COMPOSED` through the router | every value as declared, every refusal a refusal |
| V3 | column 3 | every answered composed chain verifies in a fresh interpreter; every declared mutation of it (value lie, read lie, column 1, reorder, answer) is caught |
| V4 | `tool convergent` against independent references | convergents 1, 3, 5 and 8 of `sqrt(n)` for every non-square `n ≤ 40`, against the integer recurrence folded from the right, in lowest terms; convergents 1–14 of pi against the published terms |
| V5 | `tool best approximation` on the grid | equal to the exhaustive search on all 100 |
| V6 | non-interference | none of the 404 declared texts is read by a tool value, and the 30 stepwise composition cases give the same verdict with the leaf switched off |
| V7 | `SINGLE` through the router | answered by the toolbox, with the declared fragment |
| V8 | `HELD_OUT` | no wrong answer, at least 8 right, and every corrected sheet value re-derived independently (§5.3) |

**Controls.** V4 and V5 use references that share no code with the tools: the
integer recurrence uses no exact-real layer, and the exhaustive search uses no
continued fraction. V6 is the conservative rule
(`GLM.StepwisePlanner.fallback_conservative`) taken as a count, with the
round's own switch as the control. The refusals of V2 check that a tool's
refusal stays a refusal and is never turned into an answer.

## 5. The measurement

`python3 -m glm_universal.tools tool-values`, at the close of the round:

```
V1 Lean           RequestProject/GLM/ToolValues.lean: missing [], sorry False
V2 composed       17 of 17 as declared (13 answered)
V3 column 3       13 of 13 chains verified; 65 of 65 mutants caught
V4 convergents    136 of 136 surd cases and 14 of 14 pi cases agree with the references
V5 nearest        100 of 100 agree with the exhaustive search
V6 interference   0 of 404 declared texts read; 0 of 30 stepwise cases moved
V7 single         8 of 8 as declared
V8 held out       10 of 12 read, 10 right, 0 wrong; 3 of 3 corrected sheet values re-derived
marks met         8 of 8
```

The end-to-end evaluation still passes 188 of 188 (156 answered, 32 refused as
`boundary`), and `tools connected-two` still meets its 8 marks.

### 5.1 The verdict

All 8 marks were met. A question that composes a tool with arithmetic is now
answered, and the answer can be checked: each step is gated, and the chain
re-runs the tool and the selector in a fresh interpreter. Nothing the GLM
answered before changed.

### 5.2 First change after the first measurement: the step gate refused a label

On the first run V2 met 16 of 17. *The number of gate moves from 0x000007 to
0x000005 plus 1* was refused, and the refusal came from the step gate: the
step's sentence *Step 1: the number of gate moves … is 2, computed by …* read
back under the literal template (*Step k: the number …*). The gate did its job,
since it would not admit a step whose sentence reads two ways. The fix is in
`stepwise._build`: a tool step whose label begins *the number* drops the
article. The battery was not changed.

### 5.3 Second change: three answer-sheet values were wrong

On the first run of V8, 10 of 12 were read, and 3 of the 10 disagreed with the
sheet. In each case the hand-written sheet was wrong and the GLM was right:

| question | as written | correct | re-derived by |
|---|---|---|---|
| the best rational approximation of `sqrt(3)` with denominator up to 50, plus 1 | 123/41 | 112/41 | exhaustive search: 71/41, plus 1 |
| the mean of the first 4 terms of the continued fraction of `sqrt(7)` | 7/4 | 5/4 | integer recurrence: [2, 1, 1, 1] |
| the numerator of the closest fraction to pi with a denominator under 100, squared | 97344 | 96721 | exhaustive search: 311/99, and 311² = 96721 |

The sheet now holds the corrected values, and `HELD_OUT_CORRECTED` records the
original ones. V8 re-derives all three each time it runs, without continued
fractions and without the GLM's tools. A fourth disagreement was the
measurement's own fault: it read the value out of the router's sentence for a
single value badly. That is fixed in `_verdict`. After both fixes: 10 read,
10 right, 0 wrong.

The two held-out rewordings that were not read are *the second partial
quotient of pi* (no *of the continued fraction*) and *the convergent number 4
of pi*. Both stay refused, so neither is wrong.

### 5.4 What it answers

Under directive D15 the round moves **derivation**. *The kissing number of the
Leech lattice divided by 24*, *is the numerator of the third convergent of
`sqrt(3)` prime* and *the lcm of the denominator of the fourth convergent of pi
and 7* are answers no register holds and no single tool gives; they come from
composing what the tools compute. The nearest-fraction tool is a new kind of
answer: an optimum over a finite set, certified by exhaustion where that is
cheap. The round also moves **refusal**: a tool's refusal now propagates
through a chain, by name, to every reading that needs it.

## 6. What this round does not do

* The patterns are patterns, not a parser, so rewordings outside them are not
  read (§5.3).
* Only numbers are handed on. A tool's verdict (reachable or not, a ladder
  relation) is not yet a value the planner can test.
* The classical best-approximation theorem is not proved (§2). Above a bound
  of 20,000 the nearest-fraction answer rests on it alone, and says so.
* No evaluation case was added. The contract set is pinned by the router's
  census, and the new questions live in their own batteries.

## 7. Files

* `overlay/glm_lean/RequestProject/GLM/ToolValues.lean`, the proofs.
* `overlay/glm_universal/runtime/tool_values.py`, the reader and the
  selectors.
* `overlay/glm_universal/runtime/stepwise.py` (`Leaves._tool_value`,
  `TOOL_VALUES`, the label rule in `_build`) and
  `overlay/glm_universal/reasoning/stepwise_script.py` (`tool_value` in the
  column-3 script).
* `overlay/glm_universal/runtime/router.py` (`_phrased_tool`).
* `overlay/glm_universal/reasoning/rational_approx.py` and the two tools in
  `overlay/glm_universal/runtime/toolbox.py`.
* `overlay/glm_universal/evaluation/tool_values_cases.py`, the batteries and
  `measure()`. `python3 -m glm_universal.tools tool-values` prints the marks.
* `overlay/glm_universal/tests/test_tool_values.py`.

### 7.1 What this round leaves

* Rewordings: *the K-th partial quotient of X* without *continued fraction*,
  and *convergent number K*. These are the two unread held-out forms; reading
  them now would be a post-hoc fit, so they wait for a fresh held-out set.
* Verdicts as values (a gate reachability, a ladder relation, a law's fate).
* The classical best-approximation theorem in Lean, which would let the tool
  drop its cap.
