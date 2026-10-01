# The integer decision, completed — the Omega test behind `INTEGER_UNDECIDED`

## Tier 0 — the coarse read

**Question.** Can the integer sort of Reverse Three Column Thinking decide every linear question it reads, with a certificate a fresh interpreter checks, instead of refusing `INTEGER_UNDECIDED`?

**Verdict.** Every question round three refused `INTEGER_UNDECIDED` in the declared corpus and the declared battery is now decided, as declared and in agreement with enumeration, each refutation a tree the column-3 script checks step by step; nothing round three decided moved. The refusal is kept only for a declared limit of search steps.

**Deciding figure.** 22 of 22 declared questions answered as declared, 0 wrong (round three refused all 22); 600 of 600 battery questions agree with enumeration, 0 undecided (round three: 31); 22 of 22 scripts `VERIFIED`, 22 of 22 mutants rejected; 6 of 6 marks met.

**Recomputed by.** `glm_universal.reasoning.integer_decision.decision_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

Candidate M of [`STATUS.md`](../STATUS.md) §3.4, its third item, named by
[`REVERSE_TCT_STUDY.md`](REVERSE_TCT_STUDY.md) §12: *a complete integer
decision. The Omega test's dark shadow and splinters would decide what
`INTEGER_UNDECIDED` now refuses, with certificates of the same derivation
shape plus finitely many splinter cases.*

Round three (Phase 69) decides a case over ℤ by elimination with rounding:
every row is tightened to coprime integer coefficients, a variable with a unit
coefficient in an equation is substituted, and otherwise Fourier–Motzkin runs
with every derived row tightened. That is sound and not complete. When it
neither refutes a case nor finds an integer point by a bounded search, the
answer is `INTEGER_UNDECIDED`. The standard example is Pugh's parallelogram,
`27 ≤ 11x + 13y ≤ 45`, `−10 ≤ 7x − 9y ≤ 4`: it has rational points and no
integer point, and round three refuses it.

## 1. Declarations — written before any code of this round

**The object.** A case refutation gains a second shape. Round three's shape —
input rows, a list of combinations `a·rowᵢ + b·rowⱼ` (positive integer
multipliers, each result tightened), and a contradiction `0 + k ≤ 0` with
`k > 0` — is kept, and is still what the round-three elimination emits. The
new shape is a tree of three steps over the same rows:

* **combine** — as above;
* **substitute** — replace a variable `v` everywhere by `σ + Σ qᵢ·xᵢ + q₀` for
  a fresh variable `σ` and integer `qᵢ`, `q₀`. This is a bijection of the
  integer points, so a refutation after it refutes before it;
* **split** — at a row `s ≤ 0` and a count `K ≥ 0`, one child for each of
  `s = 0, s = −1, …, s = −K` and one for `s ≤ −K − 1`. Over ℤ the children
  cover every point the row allows.

A leaf is a contradiction row. Every step is checked by arithmetic alone; no
theorem is trusted by the checker. The Omega test is what *finds* the tree:
exact elimination where a variable's coefficients allow it, equalities solved
by the least-remainder substitution, and otherwise the real shadow (refuted:
done), the dark shadow (satisfied: an integer point exists and is built), or
the splinters — the split above at each lower bound of the variable with
`K = ⌊(m·b − m − b)/m⌋`, `m` the largest upper coefficient and `b` the lower
bound's own, the last child then eliminated exactly.

**Z1. Nothing that was decided moves.** Every question of round three's
corpus (29 `entails`, 10 `bounds`) and every question of the X4 battery gets
the same answer as before; where round three's elimination refuted a case,
the certificate is byte-identical, because the new search runs only on a case
the old elimination left open.

**Z2. The declared corpus.** The 22 questions of
`glm_universal/evaluation/integer_decision_cases.py` — 16 `entails` (Pugh's
example among them) and 6 `bounds`, every one refused `INTEGER_UNDECIDED` by
round three when this section was committed, every one bounded so that its
declared answer is the enumerated truth — are all answered as declared: 22 of
22, 0 wrong, 0 refused.

**Z3. The declared battery.** The battery of the same file (seed 79, 300
systems in two or three variables inside the box `[−6, 6]`, each asked once as
`entails` and once as `bounds` of `x`) agrees with enumeration of the box on
all 600 questions; the number round three refuses `INTEGER_UNDECIDED` on it is
reported, and none of the 600 is refused `INTEGER_UNDECIDED` now.

**Z4. Column three.** Every Z2 answer carries a certificate that its generated
script verifies in a fresh interpreter (`VERIFIED True`), and for every Z2
answer whose certificate holds an Omega refutation, a mutant — the last
child of a split dropped, or the last step of a leaf removed — prints
`VERIFIED False`.

**Z5. `INTEGER_UNDECIDED` narrowed to a declared limit.** The refusal is kept
for exactly one reason: a case spends more than `NODE_LIMIT` (5000) steps. Its
message says so.

**Z6. In Lean** (`RequestProject/GLM/IntegerDecision.lean`): the dark-shadow
row guarantees an integer between the two bounds; the splinter bound — an
integer point outside every splinter satisfies the dark-shadow row; the split
covers every integer the row allows; and the substitution is a bijection of
`ℤ`. Builds with no `sorry` and only the standard axioms.

## 2. Results

`glm_universal.reasoning.integer_decision.decision_report` recomputes Z1–Z3
and Z5 in process; `python3 -m glm_universal.tools integer-decision` adds Z4
(each script run in a fresh `python3 -I`). The implementation is
`reasoning/integer_decision.py`; `reasoning/reverse_tct_int.py` hands it a
case only after its own elimination and its bounded witness search have both
left the case open, and its column-3 script checks the tree with its own
copy of the arithmetic.

*On the order of work.* Section 1, the corpus file and the battery generator
were written before any code of the round and are unchanged since; they were
committed to the repository together, after a first draft of the search had
been written in a scratch copy outside it. No declaration was edited after
the code existed. One word of §1 does not describe the code: the equality
step is written there as the *least*-remainder substitution (Pugh's
symmetric remainder); the code uses the floor remainder, which shrinks the
smallest coefficient just as surely and so terminates the same way.

| mark | declared | measured | |
|---|---|---|---|
| Z1 | round three unchanged | 29 / 29 `entails` and 10 / 10 `bounds` as declared; 0 Omega trees in their certificates; X4 battery 116 questions, 0 disagreements | met |
| Z2 | 22 / 22 as declared, 0 wrong, 0 refused | 22 / 22, 0 wrong, 0 refused; round three refuses all 22 `INTEGER_UNDECIDED` | met |
| Z3 | 600 / 600 agree, 0 undecided | 300 / 300 `entails` and 300 / 300 `bounds` agree; 0 undecided; round three undecided on 11 and 20 (31 in all), wrong on 0 | met |
| Z4 | every script `VERIFIED`, every Omega mutant rejected | 22 / 22 `VERIFIED True`; 22 / 22 mutants `VERIFIED False` | met |
| Z5 | the refusal only past 5000 steps | the limit is 5000 steps, the refusal's message names it, 0 refusals on the corpus and the battery | met |
| Z6 | the Lean file, no `sorry` | `RequestProject/GLM/IntegerDecision.lean`: `exact_shadow`, `dark_shadow_gap`, `splinter_count`, `splinter_tail`, `split_cover`, `substitution_bijective`, and Pugh's example checked by exhaustion (`pugh_no_integer_point`, `pugh_in_box`); standard axioms only | met |

**What round three was missing.** Of the 22 declared questions, 20 are
decided without a single split. In 18 of them the tree holds a floor-remainder
substitution: an equality with no unit coefficient, which round three's
elimination treated as two inequalities — where rounding loses the lattice —
is solved exactly instead. The other two (`d04`, `d05`) have no equality and
are refuted by the Omega test's own choice of elimination (an exact
elimination where one exists, the real shadow otherwise), which round three's
fixed choice missed. Two need the splinters: Pugh's
parallelogram (`d01`, 95 steps, 2 splits) and `d08` (35 steps, 1 split). In
the battery the complete decision is reached on 11 `entails` and 20 `bounds`
questions — exactly the ones round three left undecided.

**The certificate.** A refutation tree is checked without trusting any
theorem: a combination is re-added and re-tightened, a substitution is
checked to use a variable no row holds, and a split is checked to have one
child per value `0 … K` and one for the tail. The theorems of Z6 are what make
the *search* complete — the dark shadow's integer, the splinter bound and the
exactness of a unit-coefficient elimination — not what the checker relies on.

## 3. What this is, under D15

**Refusal turned into derivation.** Round three refused, by name, every
question its elimination could not settle; this round settles them, each with
a checkable certificate, and moves no answer that was already given. The one
refusal left is a resource limit, declared and never reached here.

## 4. What it is not

The fragment is unchanged: linear rows over ℤ after round three's residue
and piecewise splits. Nothing here decides a product of two variables, a
remainder by a variable, or quantifier alternation. The Omega test is
exponential in the worst case; the declared limit is what bounds it, and the
systems measured have at most three variables. The corpus and the battery
were written by the author of the code.

## 5. Next

The other items of candidate M in [`STATUS.md`](../STATUS.md) §3.4 are
untouched: strings, tuples and ranges as a sort; programs with state; and the
loop — `relay:` reading the integer certificate kinds, an `INDEPENDENT`
verdict's witness handed to the question layer.
