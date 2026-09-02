# The noise experiment

*What the wobble can compute once it stops being a way of writing a number
down. Cascaded loops, interacting tones, closed orbits, dither and error
feedback through a matrix — each measured exactly and each bound to a
theorem.*

Code: [`overlay/glm_universal/reasoning/noise_lab.py`](../overlay/glm_universal/reasoning/noise_lab.py).
Query: `report noise` (aliases `report wobble`, `report wiggle`,
`report dither`, `report cascade`).
Formal development: [`RequestProject/GLM/Cascade.lean`](../RequestProject/GLM/Cascade.lean)
and [`RequestProject/GLM/Feedback.lean`](../RequestProject/GLM/Feedback.lean).
Tests: `overlay/glm_universal/tests/test_noise_lab.py`.

---

## 1. The question

The to-do list puts it as *"the outside is the whole number, the inside is the
infinite"*, and complains — correctly — that the machine has so far used the
delta–sigma wobble only to **represent** values. A target `t ∈ [0, 1)` is
chased by a one-bit quantiser, the time average of the bits converges to `t` at
rate `1/N`, and that is the whole of it. The request was to use the
trajectory's geometry as the computation: cascaded loops, error feedback,
subtractive dither with an equidistributed sequence, and *"interacting noise
frequencies / amplitudes / patterns"*.

Everything below was built for that, and the discipline is the one the rest of
the repository uses: no float is constructed anywhere, no random number is
drawn, and each measurement is checked against a theorem rather than against an
expectation. "Noise" here always means a **deterministic trajectory whose
statistics are computed**, never a sample.

---

## 2. A loop can chase a signal, not just a constant

The first thing in the way was that everything previously proved — that the
accumulator never leaves `[0, 1)`, that the bits sum to `N·t` less the state,
that the average is within `1/N` — was stated for a *fixed* target. A wobble
whose amplitude and frequency vary, or two tones added together, is not a fixed
target, and none of it applied.

`mState` / `mBit` in `Cascade.lean` are the same quantiser driven by an
arbitrary input sequence `u : ℕ → ℝ` with values in `[0, 1)`, and the three
statements survive verbatim:

| theorem | what it says |
|---|---|
| `mState_mem_Ico` | the accumulator stays in `[0, 1)` for **every** input |
| `mSum_eq` | `∑ bits = ∑ input − state` — exactly |
| `mAverage_error_le` | so the bits track the input's *running mean* to `1/N` |

Measured, on `square(4, 1/8) + triangle(6, 1/6)` about `1/2` — two tones of
different periods, beating with period 12 — after 128 ticks:

```
mean input = 287/576     mean bits = 63/128     error = 7/1152 ≤ 1/128
```

The homeostasis does not depend on the target standing still. That is what
makes a modulated wobble usable as an input channel at all.

## 3. When the wobble closes its orbit

An interacting-tone input either settles into a cycle or never repeats, and
which one happens is not a property of the loop. It is decided by a single
arithmetic fact about the input:

> **`mState_period_eq_zero` / `mState_periodic`.** If the input is
> `P`-periodic and its sum over one period is a **whole number**, the
> accumulator is empty at the end of every period, so state and bits are
> exactly `P`-periodic.

The proof is one line of arithmetic once the two earlier theorems are in hand:
after one period the state is the period sum less an integer number of emitted
bits, so it is an integer that lies in `[0, 1)`, so it is zero.

Measured both ways:

| signal | period sum | orbit closes | bits repeat |
|---|---|---|---|
| `square(4, 1/4)` about `1/2` | `2` | yes | yes |
| `square(4, 1/8)` about `1/3` | `4/3` | no | no |

So "does this wobble settle?" is a decidable question about the input, and the
machine answers it by deciding rather than by running and looking.

## 4. What a second loop buys: an order, exactly

The cascade (a MASH 1-1) feeds stage one's error into a second loop and
recombines the outputs:

```
y n  =  b₁ n  +  b₂ (n+1)  −  b₂ n
```

**The identity that makes this worth anything** (`casOut_error`) is that the
instantaneous error becomes a *second* difference of a bounded sequence:

```
t − y n  =  s₂ (n+2)  −  2 · s₂ (n+1)  +  s₂ n
```

A single loop shapes its error as a *first* difference, and one difference
telescopes once — which is exactly why the plain average is `O(1/N)` and no
better, however long it runs. Two differences telescope twice, so the gain
appears the moment the output is read with a window that sums twice:

* `casDouble_sum` — the **doubly accumulated** error is exactly stage two's
  state, hence below `1` for all time. A single loop's doubly accumulated
  error grows linearly (`firstOrder_double_sum_half`: on the target `1/2` it is
  `⌊M/2⌋ / 2`).
* `casTriangular_error_lt` — hence the triangular (Bartlett) window average is
  within `2 / (M (M − 1))` of the target: **`O(1/M²)`**.
* `firstOrder_triangular_error_ge` — and read through the *same* window, a
  single loop chasing `1/2` is off by at least `1 / (2M)`. The order is really
  gained; it is not an artefact of the estimate.

Measured on the target `1/3`, where neither reading is exact:

| window `M` | cascade, triangular | proved bound | single loop, same window | ratio |
|---:|---|---|---|---:|
| 8 | `1/84` | `1/28` | `1/12` | 7 |
| 16 | `0` | `1/120` | `1/24` | — |
| 32 | `1/1488` | `1/496` | `1/48` | 31 |
| 64 | `0` | `1/2016` | `1/96` | — |
| 128 | `1/24384` | `1/8128` | `1/192` | 127 |

Where the cascade's error is not exactly zero the ratio is exactly `M − 1`:
one whole order, measured rather than asserted. On the target `1/2` the
cascade's windowed reading is **exact** at every window measured, while the
single loop is off by `1/(2M − 2)` — never below its proved floor `1/(2M)`.

The price is a slightly wider output alphabet: `y n ∈ {−1, 0, 1, 2}`
(`casOut_mem`) rather than a bit. It is a wider alphabet, not a finer one —
nothing here needs a smaller quantiser step.

## 5. Idle tones, and what dither costs

A rational target drives the loop into a cycle (§3), and a cyclic bit stream is
a line in the spectrum — an *idle tone*, the artefact that makes a modulator
audible. The package already has an exact Walsh–Hadamard transform, so the
tone can be measured without leaving exact arithmetic: transform the ±1 output
over a power-of-two window and take the largest coefficient away from DC, as a
fraction of the window.

On the target `1/2` over 256 ticks the undithered output is a **pure** tone:
peak `1` — every unit of energy on one Walsh line.

Subtractive dither `amplitude · (frac(n·α) − 1/2)`, with `α = 4181/6765` (a
ratio of consecutive Fibonacci numbers, so the sequence walks the interval as
evenly as a rational can), breaks it up. Turning the amplitude up:

| dither amplitude | Walsh peak | bias left behind |
|---|---|---|
| none | `1` | `0` |
| `1/16` | `113/128` | `−167/1847296` |
| `1/8` | `113/128` | `−167/923648` |
| `1/4` | `113/128` | `−167/461824` |
| `1/2` | `105/128` | `−167/230912` |
| `3/4` | `59/128` | `−501/461824` |
| `9/10` | `33/128` | `−1503/1154560` |

The peak falls monotonically. What it costs is stated rather than assumed to
vanish: the dither's own mean over a finite window is not exactly `1/2`, and
the residue times the amplitude is a **bias**, computed exactly in the table
above. At `9/10` the tone is down to a quarter of its undithered height for a
bias below `1.4 × 10⁻³`. That is the trade, in exact numbers, with no
probabilistic model of the dither anywhere.

---

## 6. Error feedback through a matrix, and the symmetry it keeps

Everything above quantises one coordinate. The remaining direction the to-do
list asks for is the vector case: several coordinates modulated at once, with
each tick's quantisation error returned through a rational matrix `A` chosen to
commute with a symmetry of the carrier. It is built
(`noise_lab.feedback_run`, `feedback_tracking`, `equivariance_check`,
`dead_zone`) and proved (`RequestProject/GLM/Feedback.lean`), and the three
things worth saying about it are these.

**The loop is bounded whatever `A` is.** `efErr_abs_le_half`: the instantaneous
quantisation error stays in `[−1/2, 1/2]` in every coordinate, however the
linear part behaves. The nonlinearity is never the thing that runs away.

**Only the identity tracks the input, and it tracks it *better* than a scalar
accumulator does.** `efSum_eq` is the exact accounting identity
`∑_{k<N}(u_k − y_k) = ∑ e_k − ∑ s_k` with `s_{k+1} = A e_k`; at `A = 1` the
second sum is the first one shifted, everything cancels but a single bounded
term, and `efAverage_error_le_identity` gives

> `|average of the bits − running mean of the input| ≤ 1/(2N)`,

in *every* coordinate and for *every* input. That is the vector form of the
`1/N` law with a factor of two to spare, because what survives is one
quantisation step rather than one accumulator state. Run on the four targets
`1/3, 2/5, 3/4, 1/8` for 128 ticks, the measured coordinate errors are inside
the bound `1/256` and two of them are exactly zero.

**Contracting the feedback does not slow the loop, it kills it.**
`halfFeedback_dead_zone`: with `A = 1/2` on the constant input `1/4` the
quantiser never fires at all — every output is `0` and the running average
error is exactly `1/4` for ever. A feedback matrix is not a free parameter.

**The symmetry is exact, not asymptotic.** `efOut_equivariant`: if a coordinate
permutation `σ` leaves `A` invariant then permuting the input permutes the
output tick for tick, so noise shaping through a symmetry-commuting matrix
commutes with that symmetry over the whole trajectory, with no averaging and no
limit. The hypothesis is seen to be doing work rather than assumed: the same
check is run with a matrix that is *not* invariant under `σ`, and the outputs
no longer permute.

All four figures are in `report noise`, whose column 3 re-derives them in a
fresh interpreter.

---

## 7. What this does and does not settle

**Settled.** Cascading is worth exactly one order and the statement of what it
is worth is a theorem with an explicit constant; a modulated, multi-tone input
is tracked with the same guarantee a constant is; whether a wobble settles into
a cycle is decided by its period sum; and dither buys tone suppression at a
computable bias.

**Not settled, and not claimed.** The to-do list's other noise directions are
untouched by this round and remain open:

* **Broadening the hull by expanding the emitted alphabet** — emitting Leech
  points or scaled codewords rather than Golay codewords. `HullExpansion.lean`
  states what the current hull costs; nothing here widens it.
* **Self-organised criticality at the covering radius** — treating the
  weight-4 six-fold tie as a branching point. The tie itself is built and
  measured (`report superposition`, `Golay/Sextet.lean`); using the visit
  frequencies as a parallel computation is not.
* **Niemeier classification by trajectory distribution** — replacing the
  Voronoi search with a long-run frequency reading.
* **Sigma-delta *on the shells*** rather than on a scalar — error feedback
  through a symmetry-commuting rational matrix, which was on this list, is now
  §6 above.

Nothing above is blocked by what this round found; they are simply not done.

---

## 8. Reproducing it

```bash
cd overlay
PYTHONPATH=. python3 GLM.py -q "report noise" --verify-tct   # VERIFIED True
PYTHONPATH=. python3 -m pytest glm_universal/tests/test_noise_lab.py -q
```

and, for the theorems,

```bash
lake build RequestProject.GLM.Cascade      # no sorry
lake build RequestProject.GLM.Feedback     # no sorry
```

`--verify-tct` regenerates every figure quoted by the report in a fresh
interpreter and compares them key by key with what was printed, so the numbers
in §2–§5 cannot drift away from the code without the check failing.
