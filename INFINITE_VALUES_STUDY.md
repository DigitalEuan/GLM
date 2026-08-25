# Infinite values and irrational numbers in the GLM

**What this document answers.** Does the attached material —
`cardinal_geometry_synthesis.md`, `DYNAMIC_CARRIER_STUDY.md` and
`geometric_substrate_study.py` — provide what is needed to get the GLM working
with infinite values and irrational numbers? **Yes, and it has now been built.**
This document says what was built, what it can do, and — in more detail — what
it provably cannot, because that second list is the one that tells you where to
push next.

Every number quoted below is produced by running the code. Nothing here is
asserted from the outside: the package recomputes it on demand with

```bash
cd overlay && PYTHONPATH=. python3 GLM.py -q "report infinite values" -c 1
cd overlay && PYTHONPATH=. python3 -m glm_universal.capabilities
```

and the mathematical claims are machine-checked in Lean under
`RequestProject/GLM/` with no `sorry` and no axioms beyond `propext`,
`Classical.choice` and `Quot.sound`.

---

## 1. The short answer

The synthesis document put it as *"the outside is the whole number, the inside
is the infinite"*. That intuition is right, and it now has a precise form:

> **A carrier is finite. A process is not. The GLM holds an irrational as the
> process, not as the carrier — and the process is a first-class object it can
> add, multiply, compare, print, refine and refuse.**

Three separate things had to be true for that to work, and each is now either
proved or measured:

| Claim | Status |
|---|---|
| No finite carrier holds an irrational — the wall is real | **Proved** (`no_countable_layer_lossless`, a cardinality argument) |
| Every real *is* reached, as the limit of a finite carrier that moves | **Proved** (`dsAverage_error_le`, `dsAverage_tendsto`) and measured |
| The moving carrier is bounded by geometry in 24 dimensions | **Proved** (`avgVec_mem_hull`, `not_tendsto_avg_of_separating`) and certified in exact arithmetic |

## 2. What the machine can now do

### 2.1 Values

`reasoning/exact_real.py` holds a real as a rule: `x.at(k)` returns an exact
`Fraction` within `2⁻ᵏ` of the value, for any `k`. There is no floating point
anywhere in the module, and no ceiling on `k` but time.

```
sqrt(2) = 1.41421356237309504880
pi      = 3.14159265358979323846
e       = 2.71828182845904523536
phi     = 1.61803398874989484820
```

Roots of any degree are available in integer arithmetic (`nth_root`, via an
integer `n`-th root), so `root(3, 2) = 1.25992104989487316476` is as exact as
`sqrt(2)`.

### 2.2 Written arithmetic (new)

`reasoning/real_expr.py` reads ordinary written expressions over those
processes:

```
(1+sqrt(5))/2   = 1.61803398874989484820      (agrees with phi to 2**-58)
sqrt(2)+sqrt(3) = 3.14626436994197234232
pi/4            = 0.78539816339744830961
root(3, 2)      = 1.25992104989487316476
0.1+0.2         = 3/10, exactly
```

The grammar is `+ - * /`, integer powers, brackets, `sqrt`, `cbrt`,
`root(degree, x)`, the constants `pi`, `e`, `phi`, and any rational or decimal
literal. A decimal literal is read as the rational it names, so `0.1+0.2` is
*exactly* `3/10` and not `0.30000000000000004`.

`reasoning/transcendental.py` extends it past the algebraic operations with
`exp`, `log` (natural, or `log(base, x)`), `sin`, `cos`, `tan` and a
non-integer exponent:

```
exp(1)   = 2.71828182845904523536      (= e, to 2**-78)
log(2)   = 0.69314718055994530941
sin(1)   = 0.84147098480789650665
cos(1)   = 0.54030230586813971740
tan(1)   = 1.55740772465490223050
2^pi     = 8.82497782707628762385
2^(1/3)  = 1.25992104989487316476      (= root(3, 2))
log(2,8) = 3.00000000000000000000
```

Each is a process like the rest: exact rational arithmetic throughout, no
float constructed anywhere, and an error budget that is stated and paid for.
The budgets are machine-checked in `RequestProject/GLM/Transcendental.lean` —
`exp_error_le` (`|exp x − exp a| ≤ exp(max x a)·|x − a|`), `sin_error_le` and
`cos_error_le` (both 1-Lipschitz, so one extra bit), `log_error_le`
(`|log x − log a| ≤ |x − a|/c` for a lower bound `c`), and
`rpow_eq_exp_mul_log`, which is the route `x^y` takes for a positive base.

### 2.3 Questions

The runtime answers two new kinds of question, each with the usual third
column — a generated script that re-derives the answer in a fresh interpreter
and asserts it key by key:

```
approximate sqrt(2) to 20 places        -> 1.41421356237309504880; no carrier holds it
approximate (1+sqrt(5))/2 to 12 places  -> 1.618033988749
is pi less than 355/113                 -> true: pi < 355/113  (separated at 2**-32)
is sqrt(2)*sqrt(2) equal to 2           -> not distinguished at 2**-256; equality of
                                           two processes is not decidable
```

### 2.4 Carriers that move

The dynamic carrier of `DYNAMIC_CARRIER_STUDY.md` is implemented exactly (no
floats, exact error accumulator):

* **One dimension.** After `N` ticks the time average is a rational `k/N` and
  differs from the target by at most `1/N` — a theorem
  (`GLM.Info.dsAverage_error_le`), reproduced here at `N = 10, 100, 1000`. So a
  one-bit carrier reaches *every* real, irrational included, in the limit; and
  `N` ticks carry `log₂(N+1)` bits, which is where the resolution comes from.
* **Twenty-four dimensions, target inside the code's hull.** The all-½ vector
  is reached with deviation **0** using two codewords; a constant *irrational*
  target (`sqrt(2)-1` in all 24 coordinates) is tracked to within `1/N`.
* **Twenty-four dimensions, target outside.** See §3.3.

---

## 3. Where it stops — and why each stop is where it is

This is the part worth reading. Five of these are theorems and will not move;
three were work items and the machine said exactly what would move each. One
of the three — the transcendental functions of §3.5 — has since been built,
which moved the boundary rather than removing it; the other two are still
open.

### 3.1 No carrier holds an irrational (theorem)

A carrier is 24 exact rationals. The rationals are countable; the reals are
not; so any layer whose views form a countable set conflates two distinct
reals. Formally, `GLM.Info.no_countable_layer_lossless`. The dyadic tower's
level `n` holds `⌊x·2ⁿ⌋/2ⁿ` — a *stand-in*, indistinguishable from the target
at that resolution and exposed by a higher level:

```
stand-ins for sqrt(2):  1, 1, 5/4, 11/8, 11/8, 45/32, 45/32, 181/128
exposed at level:       0->2, 1->2, 2->3, 3->5
```

No stand-in squares to 2, at any level. But the tower *as a whole* is faithful
(`towerView_injective`): what is lost is lost at every single level and at no
level of the whole.

### 3.2 Equality of two processes is undecidable (theorem)

`sqrt(2)*sqrt(2)` and `2` are still "not distinguished" at `2⁻²⁵⁶`, and no
precision settles it. Inequality *is* decidable and is decided — the machine
reports the precision it took. Equality is refused. The Lean counterpart is
`eq_of_forall_abs_sub_le`: two processes never separated are equal, but "never"
quantifies over all precisions at once, which no finite computation reaches.

### 3.3 The 24-D carrier cannot hold an arbitrary target (theorem, with certificate)

Every state the 24-coordinate dynamic carrier emits is a Golay codeword, so
every reading it takes is a convex combination of codewords
(`GLM.Info.avgVec_mem_hull`) and any limit lies in their convex hull. The ramp
target (coordinate `i` holds `i/24`) is outside that hull:

```
deviation after 200 ticks   19/300  (~1/16, and not shrinking)
accumulator excursion       311/24  (growing linearly, ~N/16)
separating functional       verified against all 4,096 codewords, gap 13/5760
```

The certificate is what makes this a *proof* rather than an observation: a
single linear functional puts the target strictly above every codeword, and
`GLM.Info.not_tendsto_avg_of_separating` turns that into "no run of any
quantiser rule converges here". The complementary positive statement is now
also proved: a carrier that cycles through `N` states reads back *exactly* the
mean of its cycle (`GLM.Info.avgVec_periodic`), so the reachable set is pinned
from both sides — the hull, and nothing but the hull.

**What would move it:** nothing about the decoder. Only changing the emitted
set — a larger alphabet than the 4,096 codewords, e.g. emitting lattice points
or scaled codewords — changes the hull.

### 3.4 Division needs a witness (theorem)

`1/x` is computable only from a bound `|x| ≥ 2⁻ᵐ`. No algorithm produces that
bound for an arbitrary process, because doing so would decide whether the
process is zero. So `real_expr.divide` searches for the witness to a stated
depth (`WITNESS_DEPTH = 96`) and refuses beyond it, naming the depth. Three
Lean theorems make this exact:

* `nonzero_iff_witness` — a real is nonzero **iff** such an `m` exists, so the
  witness is precisely the missing information;
* `inv_error_le` — with the witness, division is computable at the cost the
  implementation actually pays (`x` to `2⁻⁽ᵏ⁺²ᵐ⁺²⁾` gives `1/x` to `2⁻ᵏ`);
* `witness_depth_not_uniform` — no fixed depth works for every divisor.

`1/(sqrt(3)-sqrt(2))` goes through and equals `sqrt(3)+sqrt(2)`;
`1/(sqrt(2)-sqrt(2))` is refused.

### 3.5 The transcendental functions — built, and where they now stop

This section recorded the largest single gap in the value layer: `sin`, `log`,
`exp` and a non-integer exponent such as `2^pi` were refused *by name* rather
than approximated. They are now built (`reasoning/transcendental.py`, §2.2),
to the same standard as the rest of the layer, and the section is kept because
the boundary did not disappear — it moved twice, and both new positions are
informative.

**It moved to the inverse family.** `asin`, `acos`, `atan`, the hyperbolic
functions and their inverses, `erf`, `gamma` and `zeta` are refused by name,
and the list is explicit (`real_expr.UNBUILT_FUNCTIONS`) rather than a parse
failure, so the refusal says which function is missing. Each needs its own
convergent process with a stated error bound; the six that are built are the
pattern to follow. This is the same kind of gap as before, one level up.

**It moved to positivity.** `log(x)` needs a witness `x ≥ 2⁻ᵐ`, for exactly
the reason `1/x` needs `|x| ≥ 2⁻ᵐ`: producing one for an arbitrary process
would decide whether the process is zero. `GLM.Info.pos_iff_witness` says a
witness *is* what positivity is, and `witness_depth_not_uniform` says no fixed
depth suffices, so `log(sqrt(2)-sqrt(2))` is refused with its depth named
while `log(2)` goes through. `x^y` inherits the refusal through
`rpow_eq_exp_mul_log`: `2^pi` is computable and `0^pi` is not. This second
stop is a theorem and will not move.

One cost is worth naming: no reduction modulo `pi` is attempted, because such
a reduction would itself need `pi` to a precision depending on the argument.
`sin(10)` is therefore correct (`-0.54402111088936981341`) and slower than
`sin(1)`, and the cost grows with the argument rather than the precision.

### 3.6 The vocabulary is the registers (work item)

'justice' has no determinate referent and is refused. The machine knows 1,768
named terms — numerals, SI constants, 118 elements and their formulae, the
physics quantities, the operators — of which 66 are ambiguous and are refused
rather than resolved by resolver order. Widening the vocabulary means widening
the registers, not the parser: a meaning here is 24 exact rationals, and there
is no coordinate for 'justice'.

### 3.7 No arithmetic inside a description (work item)

`what is energy` works; `what is energy divided by time` does not. The
*describe* route resolves a name, and that is an expression over names. Both
halves of the machinery exist — the verifier checks relations between
quantities, the value grammar does arithmetic over reals — but no query kind
joins them. **This is the largest single gap in the language layer**, and it is
a plumbing job rather than a mathematical one.

### 3.8 Twenty-four is not a parameter (theorem, in a weak sense)

A 25th coordinate is refused rather than silently dropped. The Leech lattice,
the Golay code and the MOG all live in 24 coordinates. Wider data must be
projected first, and a projection conflates — which is exactly the subject of
`INFORMATION_LOSS_STUDY.md`.

---

## 4. How to see all of this at once

The `capabilities` sub-package is new and exists for precisely the question
"where does it break?". It declares 33 capability probes, each phrased as a
question a user would ask, each answered by running the real code, and each
reporting the exact place the capability stops:

```bash
cd overlay && PYTHONPATH=. python3 -m glm_universal.capabilities
cd overlay && PYTHONPATH=. python3 -m glm_universal.capabilities --area reals
cd overlay && PYTHONPATH=. python3 GLM.py -q "report capabilities" -c 1
```

At the time of writing: **33 probes, 19 hold, 14 break, 0 errors, 0
surprises.** A probe that breaks is a success — the boundary has been located.
A probe whose verdict differs from its declared expectation is reported as a
*surprise*, so a capability won and a capability lost are both visible
immediately instead of being buried in a diff.

The fourteen breaks are the map of what to build next. Twelve of them are
theorems and will never move; two are work items — §3.6 and §3.7. The
third work item, §3.5, was closed by building the transcendental functions,
and the probe that recorded it now reports `holds` and checks the identities
instead of the refusal. That is the intended lifecycle of a probe: a
capability won is as visible as a capability lost, and the count moved from
18/15 to 19/14 on its own.

---

## 5. Answering the framing question directly

> *Does the attached information provide what is needed to get the GLM to work
> with infinite values and irrational numbers?*

Yes — with one correction to the framing, which turned out to be the useful
part.

The synthesis document proposed that irrationals be reached through the
carrier's *relationships* (the Leech lattice, the Griess algebra, the Moonshine
grading), because the carrier itself is finite. That is true but it is not the
mechanism. The mechanism is simpler and stronger: **a finite carrier that is
allowed to move reaches every real**, and the rate is a theorem, not a hope
(`|average − target| ≤ 1/N`). The relationships are what make the *reached*
value meaningful — they tell you which lattice class, which axis, which
grade — but the reaching is done by the tower and the modulator.

The dynamic-carrier study's own proposal survives its own test in one
dimension and fails in twenty-four, and the failure is the more interesting
result: the reachable set is the convex hull of the code, and we can now hand
you a certificate for any target outside it. That is a genuine "level up" of
the kind the request asked about — the level above "which values can I write
down" is "which values can this geometry reach at all", and it has an exact
answer.

---

## 6. Where the pieces live

| Piece | File |
|---|---|
| Reals as processes; roots; comparison; the modulator | `overlay/glm_universal/reasoning/exact_real.py` |
| Written arithmetic over them | `overlay/glm_universal/reasoning/real_expr.py` |
| `exp`, `log`, `sin`, `cos`, `tan`, real powers | `overlay/glm_universal/reasoning/transcendental.py` |
| Capability probes and their harness | `overlay/glm_universal/capabilities/` |
| `approximate` / `compare` queries and their scripts | `overlay/glm_universal/runtime/` |
| Tests for all of it | `overlay/glm_universal/tests/test_exact_real.py`, `test_transcendental.py`, `test_capabilities.py` |
| The `1/N` law and the separating tower | `RequestProject/GLM/DeltaSigma.lean` |
| The wall, the stand-ins, the faithful tower | `RequestProject/GLM/Irrational.lean` |
| The hull, the certificate, periodic reachability | `RequestProject/GLM/Reachable.lean` |
| What is computable about an approximated value | `RequestProject/GLM/Computable.lean` |
| The error budgets of the transcendental functions | `RequestProject/GLM/Transcendental.lean` |
