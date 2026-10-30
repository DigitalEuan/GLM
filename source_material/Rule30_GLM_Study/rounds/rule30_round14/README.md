# Round 14: what a proof would take, and are there hidden shortcut paths?

**Where the prize stands.** All three Rule 30 problems are still open. This round answers your two
questions.

1. Can a proof be obtained, and what exactly would it take?
2. Is the centre column "jumping through shortcut paths", with a pattern hidden inside the network?

The Lean work is in the package `RequestProject/GLM/Rule30`: files `ShortcutNetwork.lean` and
`ShortcutNetworkData.lean`, rows C149–C162 of `claims.csv`, and the "Round 14" section of the
package README. Everything builds with no `sorry` and no added axioms. The scripts are in this
folder. Labels:

* `FORMAL`: Lean proof for all parameters.
* `CERT`: a finite computation checked in Lean (`native_decide`).
* `EMP`: computed outside Lean; not a theorem.
* `OPEN`: not settled.

---

## 1. Can we obtain a proof? What will it take, exactly?

**Short answer.** Not from data, and not from more vocabulary. The missing piece is one new
theorem per problem, each with a precise statement. Neither I nor anyone else has a proof of any of
them. Below is the exact gap for each problem and the kind of mathematics that would close it.

**Why more computation cannot do it.** For Problem 1, `no_finite_certificate_problem1` (Round 6,
`FORMAL`) shows that any finite stretch of bits fits both a periodic and a non-periodic
continuation. The same holds for Problem 2 (`no_finite_certificate_problem2`). So every proof must
contain an argument that covers infinitely many times at once: an induction, an invariant, or a
compactness step.

### Problem 1: is the centre column eventually periodic?

Round 14 adds two more proved equivalent forms. All of them say the same thing:

| Equivalent form (all `FORMAL`) | Statement |
|---|---|
| `problem1_iff_fsObservers_fail` (R5) | every finite-memory observer makes infinitely many mistakes |
| `problem1_iff_strobes` (R12) | for every stride, some strobe phase keeps changing |
| **`problem1_iff_no_jumpRule`** (R14) | **no shortcut rule `c(t) = f(c(t−j₁), …, c(t−j_k))` (any taps, any `f`) ever takes over** |
| **`problem1_iff_no_linearJumpRule`** (R14) | the same with `f` = XOR of the taps |
| **`problem1_iff_lensWalk_not_evPeriodic`** (R14) | the walk through any lossless lattice lens never settles into a cycle |

**The proof chain and its first missing link.** A proof has to rule out every jump rule. Sort the
rules by look-back:

* **Look-back 1** has four rules: copy the last bit, flip it, always black, always white. Round 7
  proved that the column is never eventually constant (`centerCol_not_eventually_constant`).
  **`centerCol_lookback_one`** (R14, `FORMAL`) shows that this leaves exactly one rule: *flip the
  last bit*, that is, eventual alternation `0101…`.
* **The first missing link** is therefore the theorem *"the centre column does not eventually
  alternate"* (the period-2 case). Even this is not proved. Round 13 lifted it to all left-white
  rows (`LeftWhiteAperiodic 2`). There it is equivalent to a uniform bound on how long a column can
  alternate (`leftWhiteAperiodic_iff_runBound`). That bound is checked exactly for distances
  `d ≤ 7` (`CERT`), and a search dies within 38 steps for `d ≤ 24` (`EMP`).
* **What closing it would take.** The bound must hold at *every* distance from the edge, and the
  centre column's distance from the edge grows with time. The argument needs a quantity that
  alternation would cap but that the seed's evolution provably drives without bound. Known general
  tools cannot supply this:
  * properties of the n-step maps also hold for rows with periodic columns
    (`map_properties_cannot_decide_periodicity`);
  * there is no conservation law of small range (`seed_run_no_conservation_law`);
  * the measure-theory results cover almost every row, but not the seed (`ae_fsTypical`).
* After period 2, the same argument is needed for every period `p`. One argument uniform in `p` is
  what Problem 1 asks for.

### Problem 2: is the frequency of black cells 1/2?

The weakest sufficient target on the theorem wheel is still `SeedAPBalanced`: every arithmetic
progression of the column is balanced. This round adds `lens_freq_of_blockNormal`: if every `k`-bit
word appears with frequency `2^-k` (normality), then every network statistic equals the exact
"pattern-free" prediction computed in §2. Its `k = 1` case is Problem 2
(`hasFrequencyHalf_of_blockNormal_one`).

**What it would take:** a balance theorem for one deterministic, nonlinear system started from one
specific point. For comparison, the normality of `√2` has the same character and is also open. No
known technique proves such a statement for Rule 30.

### Problem 3: must computing c(n) cost about n steps?

**What it would take:** a lower bound on the running time of *every* algorithm for one explicit
sequence. This round's certificates show that no short shortcut exists on finite stretches (§2.5).
They say nothing about all algorithms, and no known lower-bound method reaches a statement of this
kind for a sequence like this.

### What the GLM should say

The GLM can now state each problem completely and in several equivalent forms. The honest output is
the following.

* "P1 reduces to: no shortcut rule ever takes over. The first unproved instance is: the column does
  not eventually alternate."
* "P2 reduces to a balance theorem about the seed."
* "P3 needs a lower-bound method."

None of these is a proof. Each one names the single theorem whose proof would be the answer.

---

## 2. Is the column jumping through shortcut paths?

### 2.1 Two exact meanings of "shortcut path"

1. **Through the column's own past (jump rules).** Bit `t` might be computable from a few earlier
   bits at fixed jump distances (`c(t) = f(c(t−j₁), …, c(t−j_k))`) rather than by running Rule 30.
   An LFSR is the classic sequence that looks random but has such a rule.
2. **Through the GLM's lattice network (lenses).** The GLM reads 24-bit words. It snaps each word
   to the nearest Golay codeword (a network point; twice a codeword is a Leech vector) and walks
   from point to point. The hop norm `d²` is the weight of the XOR of the two codewords, and
   `d² = 8` is a minimal, kissing-sphere hop. This round uses three lenses:
   * **block**: words `c(24k..24k+23)`;
   * **block+gray**: the same words after the GLM's byte-wise Gray map;
   * **slide**: words `c(t..t+23)`, one point per step.

### 2.2 What is proved (Lean)

* **A pattern in the network is a pattern of the column** (`evPeriodic_lensWalk`): a lens walk is a
  sliding-block image of the column. So the network cannot show a pattern the column lacks.
  Conversely (`problem1_of_lensWalk_not_evPeriodic`), proving that *any* lens walk never cycles
  would prove Problem 1. For lossless lenses (raw words before snapping) this is exactly equivalent
  to Problem 1.
* **Under normality, the network statistics are fixed** (`lens_freq_of_blockNormal`): every point
  and every hop type occurs with frequency `#preimage / 2^k`. These are the predictions computed
  below.
* **A shortcut that takes over forever is eventual periodicity** (`eventuallyPeriodic_iff_jumpRule`).
  So "the path follows a hidden shortcut" is exactly the negation of Problem 1. Under the
  Seed-Typicality target every jump rule is right exactly half the time
  (`jumpRule_hits_half_of_seedFSTypical`).

### 2.3 The network itself: everywhere is close (`ShortcutNetworkData.lean`, `CERT`)

* `golay_weight_census`: the hop norms are `0, 8, 12, 16, 24`, with multiplicities
  `1, 759, 2576, 759, 1`.
* `golay_octad_distance`: counting in minimal hops, a `d² = 12` or `16` hop is exactly 2 minimal
  hops and the `d² = 24` hop exactly 3. **Every point is within 3 minimal hops of every other.**
* `hop_twice`: making the same hop twice returns to the start. **The network has no straight line
  longer than one step.**

So **every** walk on this network looks as if it is "jumping all over the place". That is a
property of the network, not of Rule 30: a random sequence, a periodic one and Rule 30 all jump.
Seeing jumps tells you nothing. Only the *statistics* of the jumps can carry a pattern.

### 2.4 Experiment 1: the walk statistics (`r14_shortcut_network.py`, `EMP`)

Setup:

* **Data:** 4,194,304 centre-column bits (`r14_centre.c`), plus controls of known status.
* **Prediction:** for each lens, the exact pattern-free prediction, obtained by enumerating all
  `2^24`, `2^25` or `2^26` windows.
* **Five statistics:** chi-square tests on visited points, on hop vectors, on hop norms and on
  consecutive norm pairs, plus the rate of returning to a point two steps later. Each is converted
  to a z-score against 40 independent fair-coin walks of the same length.

| Sequence | Known status | Result (all three lenses) |
|---|---|---|
| **Rule 30 centre column** | open | **all \|z\| ≤ 1.6**: consistent with the no-pattern prediction |
| PCG64 fair coin | reference | all \|z\| ≤ 1.7 |
| digits of √2 | believed normal | consistent, except one statistic (block lens, return-in-2, z = +5.2); see below |
| LFSR `x³¹+x²⁸+1` | **has** a hidden linear shortcut | **detected** on every lens (z up to several hundred) |
| Thue–Morse, Fibonacci word, period 7 | structured | detected trivially (z in the thousands to millions) |

The tie-break check gives the same picture with the GLM's own coset-leader table (from
`Decoder.lean`, which breaks 1,348 ties differently): Rule 30 has all |z| ≤ 2.1 and the LFSR is
detected.

**About the √2 flag.** Rare-event statistics on overlapping windows cluster, so even a sequence
believed to be normal can reach z ≈ 5. Read the threshold with that in mind; it matters for §2.6.

### 2.5 Experiment 2: shortcut rules (`r14_jump_rules.py`, `EMP` plus `CERT`)

* **Linear shortcuts.** The Berlekamp–Massey linear-complexity profile of the first 20,000 bits stays
  within 6 of `n/2`. A fair coin stays within 7. The LFSR stops at 31.
* **Lean certificate.** `centerCol_no_linear_rule_128` (`CERT`): no linear jump rule with taps in
  `1..128` reproduces `c(128..256)`.
* **k-tap shortcuts** on `2^20` bits, searching every tap set and the best `f` for each:

  | Search | Rule 30 best accuracy | Fair coin best accuracy |
  |---|---|---|
  | 1 tap in 1..64 | 0.5010 | 0.5014 |
  | 2 taps in 1..48 | 0.5018 | 0.5018 |
  | 3 taps in 1..32 | 0.5023 | 0.5023 |
  | 4 taps in 1..20 | 0.5027 | 0.5028 |

  The LFSR reaches 1.0000 with taps (28, 31). Lean (`centerCol_no_tap_rule`, `CERT`): no rule with
  2 taps ≤ 64, 3 taps ≤ 32 or 4 taps ≤ 24 holds on even 64 consecutive bits.
* **Shortcuts that change from place to place** (your "jumping between shortcut paths"). For each
  of 4,096 segments of 256 bits I found the best 2-tap rule and the segment's own linear
  complexity.

  | Sequence | Mean best-rule accuracy | Mean local linear complexity |
  |---|---|---|
  | Rule 30 | 0.5993 | 128.22 |
  | fair coin | 0.5996 | 128.19 |
  | LFSR | 0.6233 | 31 |

  Comparing Rule 30 with the coin gives z = −1.2 and +1.4. Rule 30 does not switch between local
  shortcuts any more than a coin appears to.

### 2.6 The one thing that did show up: an early-time transient (`r14_early_sparse.py`, `EMP`)

In the first `2^17 = 131,072` steps, the centre column has unusually many 24-bit windows with at
most 3 black (or at most 3 white) cells:

* Rule 30 has **125** such windows.
* A fair coin gives mean 36.4 and sd 13.9; the maximum over 5,000 fair-coin sequences is 103.

These windows all snap to one network point, so they make the slide-lens walk return to the same
point unusually often. The anomaly was first seen there.

Caveats:

* It is confined to the **first** of 32 segments; the other 31 are within the fair-coin range.
* From step 131,072 to 4,194,304 the rate matches a fair coin (ratio 1.05).
* Allowing for the 32 segments, a coin would do this about 0.6% of the time.
* I chose this statistic after seeing the data.

So it is a lead worth explaining (long, almost-white stretches near the centre early in the run),
not a confirmed pattern. A transient can never be the shortcut a prize answer needs, because all
three problems are about the infinite tail.

### 2.7 Answer to the question

* **Is the path jumping through shortcut paths rather than straight known paths?** In the GLM's
  network every path jumps, because the network has diameter 3 and no straight lines. So "jumping"
  carries no information. The question becomes: do the jumps have a pattern? Over 4.2 million steps,
  through three lenses and two tie-break rules, they do not; the only exception is the early
  transient of §2.6. The test does find a planted hidden shortcut (the LFSR), so this is a real
  negative result, not a blind test.
* **"There should still be a pattern within that network."** One pattern is certain: the walk is
  produced by a fixed finite rule (Rule 30 followed by the lens). Lean shows that this is the only
  kind of pattern the network can contain. Anything else visible in the network would already be a
  pattern of the column (`evPeriodic_lensWalk`). A finite-memory shortcut that took over forever
  would make the column periodic (`eventuallyPeriodic_iff_jumpRule`). And if the column is normal,
  the network statistics are exactly the pattern-free ones (`lens_freq_of_blockNormal`), which is
  what the experiments show.

---

## 3. Files

| File | What it does |
|---|---|
| `r14_centre.c` | the centre column (or column `k`) to N steps, bit-parallel: `gcc -O3 -o r14_centre r14_centre.c && ./r14_centre 4194304 centre4M.bin` |
| `sources.py` | Rule 30 and the six controls |
| `golay_net.py` | the GLM's Golay network: generator rows, syndromes, complete decoding (min-weight leaders with smallest-value tie-break, or the GLM's own table read from `glm_repo.zip`) |
| `stats.py` | chi-square without scipy |
| `r14_shortcut_network.py` → `r14_shortcut_network_output.txt` | Experiment 1 (about 4 minutes) |
| `r14_jump_rules.py` → `r14_jump_rules_output.txt`, `r14_linear_certificate.txt` | Experiment 2 and the certificate used in Lean (about 8 minutes) |
| `r14_early_sparse.py` → `r14_early_sparse_output.txt` | the early-time transient (`./r14_centre 524288 col1.bin 1` etc. for the neighbouring columns) |

Run order: build `r14_centre` and produce `centre4M.bin`, then run the three Python scripts. They
need `numpy`, and `glm_repo.zip` one folder up for the tie-break check.
