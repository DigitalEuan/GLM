# History recorded in the now — what the receipt actually holds

## Tier 0 — the coarse read

**Question.** Four supplied studies claim that the present state of an exact-rational process is the exact integral of everything that led to it, so the state is the receipt of its own history. Restated exactly, which parts of that hold, and does any of it buy the GLM anything measurable?

**Verdict.** The identity holds and the reading of it does not: the accumulator is exactly the fractional part of the integral of its input, which makes it a function of the program and the tick count rather than a record of the run, and the supplied recoveries succeed just as well with the state withheld. What the corrected statement is worth is a shipped path made cheap and a class of question the system can now refuse with a witness rather than answer wrongly.

**Deciding figure.** 4,096 enumerated histories leave 4 distinct receipts; 20 of 20 recoveries succeed with the state withheld; and the 512 ticks the `real` query kind runs per question are now one multiplication rather than 512 loop steps.

**Recomputed by.** `glm_universal.reasoning.now_receipt.now_receipt_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0a. The reading in one paragraph

The identity holds and the reading of it does not: the accumulator is exactly the fractional part of the integral of its input, which makes it a function of the program and the tick count rather than a record of the run, and the supplied recoveries succeed just as well with the state withheld. What the corrected statement is worth is a shipped path made cheap and a class of question the system can now refuse with a witness rather than answer wrongly. In figures: 4,096 enumerated histories leave 4 distinct receipts; 20 of 20 recoveries succeed with the state withheld; and the 512 ticks the `real` query kind runs per question are now one multiplication rather than 512 loop steps.

The same reading, recomputed rather than written:

<!-- generated: now-tier -->
**The accumulator is exactly the fractional part of the integral of its input, and that is all it is.**  Over 20 runs of the supplied demonstrations the state recovers the emitted count 20 times out of 20 — and so does the target and the tick count with the state withheld, 20 times out of 20, so the receipt adds nothing to what the program already says.  Enumerated exhaustively, 4,096 histories leave 4 distinct receipts, the largest class holding 1,024 of them.  The same identity is what makes the shipped modulator cheap: at the 512 ticks the `real` query kind runs, the average costs 2 µs read off the target against 1988 µs run as a loop, with identical output.
<!-- end generated -->

---

## 0. What this document is

The supplied material is four studies and a script, kept in `source_material/`
where supplied material lives and unedited:

* [`HISTORY_RECORDED_NOW_STUDY.md`](../source_material/HISTORY_RECORDED_NOW_STUDY.md) — the six-dimensional `NowMoment`, the delta-sigma "2", the three levels of recovery;
* [`HISTORY_RECORDED_NOW_V2_STUDY.md`](../source_material/HISTORY_RECORDED_NOW_V2_STUDY.md) — the same, self-contained, with recovery run out to 1,024 ticks;
* [`HISTORY_RECORDED_NOW_V3_STUDY.md`](../source_material/HISTORY_RECORDED_NOW_V3_STUDY.md) — collisions between moments, the geometric tax as an arrow of time, an information-theoretic "holographic bound";
* [`HISTORY_RECORDED_NOW_V4_STUDY.md`](../source_material/HISTORY_RECORDED_NOW_V4_STUDY.md) — the framework wired into a query loop, higher-lattice escalation, a differential tax, a zero-storage rollback;
* [`history_recorded_now.py`](../source_material/history_recorded_now.py) — the v1 script, which imports this package and **runs here unmodified**.

That last point matters and is the reason this round was worth taking: the
supplied work is not a description of a system somewhere else, it is a program
against *this* substrate. Its claims are therefore decidable here, and nine of
them are decided below.

What is new in this document, and not in the supplied material:

1. the claim stated as an identity, and proved
   (`RequestProject/GLM/NowReceipt.lean`, nine theorems, no `sorry`);
2. the control the supplied recoveries omit — predict the answer with the state
   withheld;
3. an exhaustive collision census, where the supplied studies argue from the
   size of the mask space;
4. a capacity measurement, where v3 extrapolates one;
5. the float comparison actually run, under a declared float site (D11);
6. the consequence for the shipped system, in both directions: a path made
   cheap, and a class of question refused rather than answered.

---

## 1. The claim, stated exactly

The loop is the one this package ships and this repository has proved things
about since `DeltaSigma.lean`:

    state_0     = 0
    bit_n       = 1 if state_n + input_n >= 1 else 0
    state_(n+1) = state_n + input_n - bit_n

The supplied claim, in the studies' own words, is that *the accumulator state
IS the exact integral of the history*, so that "given the state (and the
target), we can recover the emitted count exactly", and that this is what a
float substrate cannot do.

Stated exactly, for any admissible input schedule:

* the emitted count after `n` ticks is `⌊∑ input⌋`
  (`GLM.NowReceipt.count_eq_floor`);
* the accumulator after `n` ticks is `fract(∑ input)`
  (`GLM.NowReceipt.acc_eq_fract`);
* two runs leave the same accumulator **exactly when** their input integrals
  agree modulo one (`GLM.NowReceipt.acc_eq_iff_fract_eq`).

The third of those is the whole of the matter. The receipt is one rational —
the integral mod 1 — and everything below is a consequence of its being one
rational rather than a log.

---

## 2. What the accumulator records, and the control the supplied studies omit

The supplied demonstrations run a constant target and then recover the emitted
count as `round(target × n − state)`. They report the recovery as a success of
the substrate. The control they omit is to *withhold the state* and predict the
count from the target and the tick count alone, which is `⌊n·t⌋` by
`GLM.NowReceipt.const_count_eq_floor`.

<!-- generated: now-levels -->
| target | ticks | ones | level 2: from the state | level 0: from the target alone | state denominator (bits) |
|---|---:|---:|---:|---:|---:|
| `2/32` | 32 | 2 | 2 | 2 | 0 |
| `2/32` | 128 | 8 | 8 | 8 | 0 |
| `2/32` | 512 | 32 | 32 | 32 | 0 |
| `2/32` | 1,024 | 64 | 64 | 64 | 0 |
| `2/32` | 10,000 | 625 | 625 | 625 | 0 |
| `3/32` | 32 | 3 | 3 | 3 | 0 |
| `3/32` | 128 | 12 | 12 | 12 | 0 |
| `3/32` | 512 | 48 | 48 | 48 | 0 |
| `3/32` | 1,024 | 96 | 96 | 96 | 0 |
| `3/32` | 10,000 | 937 | 937 | 937 | 1 |
| `1/4` | 32 | 8 | 8 | 8 | 0 |
| `1/4` | 128 | 32 | 32 | 32 | 0 |
| `1/4` | 512 | 128 | 128 | 128 | 0 |
| `1/4` | 1,024 | 256 | 256 | 256 | 0 |
| `1/4` | 10,000 | 2,500 | 2,500 | 2,500 | 0 |
| `sqrt(2)/2 at 2**-53` | 32 | 22 | 22 | 22 | 46 |
| `sqrt(2)/2 at 2**-53` | 128 | 90 | 90 | 90 | 44 |
| `sqrt(2)/2 at 2**-53` | 512 | 362 | 362 | 362 | 42 |
| `sqrt(2)/2 at 2**-53` | 1,024 | 724 | 724 | 724 | 41 |
| `sqrt(2)/2 at 2**-53` | 10,000 | 7,071 | 7,071 | 7,071 | 47 |

Every row recovers the count both ways, so the state is not what recovers it: 20 of 20 are right with the state withheld.  The state's denominator never exceeds the target's: True.
<!-- end generated -->

Both columns are right on every row. The state is not what recovered the
count: the program did. For a constant target the trajectory, the accumulator
and the count are all functions of `(t, n)` — the emitted stream is the
mechanical word of slope `t`, which this repository had already proved in
`Sturmian.lean` (`dsState_eq_fract`, `dsOnes_eq_floor`) before the supplied
studies were written.

So the honest form of the supplied claim is: **the state is the exact integral,
and the exact integral is not new information.** The demonstrations recover
nothing that the program did not already determine.

One detail of the supplied runs is worth recording because it bears on D7. The
"irrational target" the v2 and v3 scale runs use is `math.sqrt(2)/2` — a
*float*, and therefore exactly a dyadic rational of denominator `2**53`. That
is why the "state information content" column of those studies sits at 52–60
bits and drifts *down* as the run lengthens: it is reporting the target's
precision, not a growing record. This study's fourth target is that same value,
stated exactly.

---

## 3. What the accumulator does not record

### 3.1 How many receipts there can ever be

v3 measures `log2(denominator)` of the state against `log2(n_ticks)`, calls the
ratio a capacity, and extrapolates that a 24-rational carrier holds about
`10**20` ticks of history. The extrapolation has nothing behind it: the state's
denominator divides the input grid's denominator for every tick, so the number
of *distinct* receipts a run can leave is bounded by the grid and does not grow
with the run at all.

<!-- generated: now-capacity -->
| grid | target | 10 ticks | 100 ticks | 1,000 ticks | 10,000 ticks | bound | bits |
|---|---|---:|---:|---:|---:|---:|---:|
| 1/4 | `3/4` | 4 | 4 | 4 | 4 | 4 | 2 |
| 1/8 | `7/8` | 8 | 8 | 8 | 8 | 8 | 3 |
| 1/16 | `15/16` | 10 | 16 | 16 | 16 | 16 | 4 |
| 1/32 | `31/32` | 10 | 32 | 32 | 32 | 32 | 5 |

The count of distinct receipts saturates at the grid and stays there: running for a thousand times as long adds none. `GLM.NowReceipt.acc_mem_grid` is the statement and `GLM.NowReceipt.receipt_pigeonhole` the consequence.
<!-- end generated -->

The bound is `GLM.NowReceipt.acc_mem_grid`, and
`GLM.NowReceipt.receipt_pigeonhole` is the consequence: among any `q + 1`
schedules on the `1/q` grid, two leave the same receipt, however long they run.
A carrier of 24 rationals on a `2**k` grid separates at most `24k` bits of
history — a statement about the grid, and not about `10**20` ticks.

### 3.2 How many histories share one receipt

Where the supplied studies argue from the size of the mask space, this counts.
Every schedule of length 6 over a four-value alphabet is enumerated and grouped
by the receipt it leaves:

<!-- generated: now-collisions -->
| reading | value |
|---|---|
| alphabet | `0`, `1/4`, `1/2`, `3/4` |
| schedule length | 6 |
| histories enumerated | 4,096 |
| distinct receipts | 4 |
| largest class of histories sharing one | 1,024 |
| distinct (receipt, count) pairs | 19 |
| largest class sharing one of those | 580 |
| the receipt identifies the history | False |

The first colliding pair the enumeration meets is `(0, 0, 0, 0, 0, 1/4)` and `(0, 0, 0, 0, 1/4, 0)`.
<!-- end generated -->

Two-tick instances of the same collapse are the witnesses proved in
`GLM.NowReceipt.receipt_collision`: `(3/4, 3/4)` and `(1/2, 1)` leave the same
accumulator `1/2` and the same emitted count `1`, and differ at tick 1.

---

## 4. The seven dimensions, and how many of them there are

The supplied `NowMoment` carries seven dimensions and v2 states that they are
independent — "each records a different aspect of the history". Four of them
are functions of one of them.

<!-- generated: now-dimensions -->
| reading | value |
|---|---|
| dimensions claimed | 7 |
| free readings | 3 (composition, previous composition, neighbour coordinates) |
| labels | layer, tick |
| determined by the composition | coordinate, entropy, scale, tax |
| determined by the coordinate | entropy |
| carrier pairs built to share a coordinate | 128 |
| entropy reading agrees on every pair | True |
| tax differs on | 128 of them |
| compositions sharing one coordinate | 4,722,366,482,869,645,213,696 on the 16-value grid |
<!-- end generated -->

The measurement is made on carrier pairs built to share a coordinate: every
coordinate is moved to the other value on its own side of a half, so the
24-bit coordinate cannot change. The entropy reading (coset weight, codeword,
candidate count) agrees on every such pair, because it is a function of the
coordinate; the tax and the composition differ on them, because they are not.

So the snapshot is **three free readings and two labels**: the composition, the
previous composition (which is what the momentum is a difference of), the
neighbours' coordinates (which is what the topology is a distance to), plus the
layer name and the tick number. The coordinate, the entropy, the scale and the
tax are all readings of the composition. That is not a criticism of the
snapshot — it is a useful object — but "seven dimensions of the Now" is a
count of readings, not of independent facts.

It does carry the supplied study's own honest boundary, and this study confirms
it in the sharper form: a coordinate is shared by an exact number of
compositions, which the table above gives for the grid it samples.

---

## 5. The float control

v2 rests its case for the substrate on a comparative claim: "float-based
systems cannot do this — the accumulator state is corrupted by rounding at
every step". That cannot be settled without running floating point, so it is
run, in the one declared float site of the package
(`glm_universal.reasoning.now_float_control`, D9 and D11). The exact loop and
the float loop chase the same number — a target that is exactly a double, so
the only difference is the rounding of the additions.

<!-- generated: now-float -->
| ticks | exact ones | float ones | recovered from the float state |
|---:|---:|---:|---:|
| 100 | 70 | 70 | 70 |
| 10,000 | 7,071 | 7,071 | 7,071 |
| 100,000 | 70,710 | 70,710 | 70,710 |

Over 100,000 ticks the two loops emit the same bit at every tick (no divergence), and the supplied recovery holds from the float state as well as from the exact one: True.  What exactness buys is the bound, not this horizon.
<!-- end generated -->

The comparative claim is **not supported at any scale the supplied studies
ran**, nor two orders of magnitude beyond it: the two loops emit the same bit
at every tick, and the supplied recovery works from the float state as well as
from the exact one. What exactness buys here is not a measured difference but a
*bound*: the exact accumulator is provably in `[0, 1)` at every tick
(`GLM.ZeroStorageV5.dsAcc_mem_Ico`), while the float loop's error is only
bounded by an accumulation argument that runs out at around `2/eps` ticks. The
right statement is "the exact loop needs no error budget", not "the float loop
fails".

This is a negative result about the argument, not about the substrate, and it
is kept for that reason.

---

## 6. The arrow of time

v3 reports as its key finding that the cumulative geometric tax strictly
increases. That is true, and it is true of every non-negative quantity
whatever: a running total of non-negative terms is monotone, which is
`GLM.NowReceipt.cumulative_mono` and is two lines. It is not evidence about the
tax.

v4 replaces it with a differential tax, `max(0, ΔTAX)`, and reports —
honestly — that the accumulation of it is flat for a decaying carrier. This
study reproduces all three readings on a decaying carrier: the per-tick tax is
not monotone, the cumulative tax is, the differential is non-negative, and the
cumulative differential is flat. The v4 boundary is confirmed, and the v3
finding is empty.

What would make an arrow of time out of the tax is a statement that the tax
*cannot* be paid back — that some quantity is monotone along every admissible
trajectory rather than along a chosen one. Nothing in the supplied material or
here establishes that, and this study does not claim it.

---

## 7. What the system gains

Two things, measured separately, because they are different kinds of gain.

### 7.1 A shipped path made cheap

The corrected statement — the count is `⌊n·t⌋` and the `n`-th bit is
`⌊(n+1)t⌋ − ⌊n·t⌋` — is a closed form for exactly the quantity the shipped
modulator computes by looping. `exact_real.delta_sigma_average` and
`exact_real.delta_sigma_bits` now read it off the target. The
`real` query kind runs 512 ticks on every question it answers.

<!-- generated: now-shortcut -->
| ticks | average: loop | average: read off | bits: loop | bits: read off |
|---:|---:|---:|---:|---:|
| 512 | 1988 µs | 2 µs | 1973 µs | 54 µs |
| 4,096 | 15790 µs | 2 µs | 15778 µs | 408 µs |

Identical output on every case measured: True. The shipped `real` query kind runs 512 ticks per question, which is the first row.  The theorems are `GLM.NowReceipt.const_count_eq_floor`, `GLM.NowReceipt.const_bit_eq_floor_diff`.
<!-- end generated -->

The output is identical on every case measured, and the raw loop
(`DeltaSigma.run`) is still there and is what the closed form is pinned against
in `tests/test_now_receipt.py`, target by target, including a 20,000-tick case
with the exhaustive switch on. That is the discipline D2 asks for: the shortcut
is allowed because the raw computation stays available and the two are checked
against each other, and because the shortcut is a theorem rather than an
optimisation.

One further control came free. The wobble landscape's measurement cache reads
the modulator for eight constants at ten thousand ticks each, and its closure
includes `exact_real`, so the change made it stale. Re-taken, the file differs
from its previous contents **in the digest of the code it was taken from and in
nothing else** — every emitted bit, run length, entropy and tone of that study
is unchanged.

This is **maintenance**, not a movement of the target, and it is reported as
such: no answer changed.

### 7.2 A class of question refused with a witness

The supplied recipe `round(target × n − state)` answers every question of the
shape "what was the history?". Four of the nine declared below have no answer:
the receipt does not determine them, and §3.2 is why.

<!-- generated: now-tasks -->
| task | outcome |
|---|---|
| count from target and ticks | answered |
| state from target and ticks | answered |
| count from the integral | answered |
| state from the integral | answered |
| distinguish two targets | answered |
| schedule from the receipt | refused — the receipt does not determine the history |
| first tick from the receipt | refused — the receipt does not determine the history |
| tick count from the receipt | refused — the receipt does not determine the history |
| input from the receipt | refused — the receipt does not determine the history |

The supplied recipe answers all 9, so it is wrong on 4: the four questions whose answer the receipt does not determine.  Refusing those four removes 4 wrong answers at a cost of 4 refusals, and every refusal carries the colliding pair that justifies it (True).
<!-- end generated -->

Against the plain runtime the five answered questions are questions it refuses;
against the supplied recipe the four refusals are four wrong answers removed,
each carrying the colliding pair that justifies it. That is the **refusal**
faculty of the standing target, on a declared task set: wrong answers removed
at a counted cost in refusals.

The honest limit, stated the same way the planner sandbox round stated it: none
of these nine questions is in the project's evaluation set, and this round adds
none to it, so the gain is on the declared task set and the evaluation set is
unchanged. The module is a study instrument, not a new query kind; nothing in
the runtime dispatches to it.

---

## 8. Every claim, and how it fell

<!-- generated: now-claims -->
| claim of the supplied studies | verdict | settled by |
|---|---|---|
| the state is the exact integral of the history | **holds** | `receipt_levels` |
| the state recovers the emitted count | **holds, and so does the target and tick count alone** | `receipt_levels` |
| the coordinate alone is not the receipt | **holds** | `dimension_dependence` |
| a 24-rational carrier holds about 10**20 ticks of history | **refuted** | `grid_capacity` |
| float systems cannot keep the state exactly | **not supported at any scale measured** | `now_float_control` |
| the seven dimensions are independent readings | **refuted** | `dimension_dependence` |
| cumulative tax increases, which is the arrow of time | **holds of any non-negative quantity** | `tax_arrow` |
| the differential tax is a strict arrow of time | **refuted** | `tax_arrow` |
| the receipt identifies the history | **refuted** | `collision_census` |
<!-- end generated -->

Four hold, one holds vacuously, one holds with its reading corrected, and three
are refuted. The two refutations that matter are the capacity extrapolation and
the independence of the seven dimensions; the third — that the receipt
identifies the history — is the one the supplied studies half-state themselves
in their "honest boundary" sections, and this study finishes it.

---

## 9. What this study does not settle

* **Whether physical reality records its history this way.** The supplied
  studies raise the question and decline it; so does this one. Everything here
  is a statement about a loop.
* **The v4 higher-lattice escalation.** v4 claims that a 48-dimensional ternary
  lattice breaks a deep-hole tie that the Leech lattice cannot, by an argument
  about the minimum distance of the underlying code rather than by a
  computation on the carrier — and notes itself that the 32-dimensional
  escalation it also claims did not run. This study does not treat either; the
  tree's own deep-hole ladder is measured in
  [`DEEP_HOLE_ESCALATION_STUDY.md`](DEEP_HOLE_ESCALATION_STUDY.md).
* **The v4 query-loop integration.** Its "6 of 6 resolved" reading has no
  control — nothing establishes that a nonsense string would not resolve at the
  same rung — and rebuilding it with one is a round of its own.
* **Whether a receipt is worth carrying at all.** The three free readings of §4
  are a reasonable snapshot, and nothing here says otherwise; what is settled
  is only what a receipt can be asked to *prove*.

---

## 10. What this round changed in the tree

| what | where |
|---|---|
| nine theorems about what the accumulator records | `RequestProject/GLM/NowReceipt.lean` |
| the audit, and every figure above | `overlay/glm_universal/reasoning/now_receipt.py` |
| the declared float site, and only it | `overlay/glm_universal/reasoning/now_float_control.py` |
| the closed forms on the shipped path | `overlay/glm_universal/reasoning/exact_real.py` |
| the tests, pinned against the raw loop | `overlay/glm_universal/tests/test_now_receipt.py` |
| the supplied material, unedited | `source_material/HISTORY_RECORDED_NOW*_STUDY.md`, `source_material/history_recorded_now.py` |
