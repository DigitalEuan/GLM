# The second reading's channel — an exact measure for `agree`, and its place in the hunt

## Tier 0 — the coarse read

**Question.** Can the second reading (`agree`, two reads of one carrier) be given an exact channel measure, so that it joins the confidence-floor hunt, and what does it add where the decoder alone has no working floor?

**Verdict.** The second reading has an exact channel measure: every pair of reads is counted in one census of rate-independent integer tables, and in the hunt it has a working threshold at every declared rate — 9999/10000 up to 1/20 and 999/1000 at 1/10, where the decoder alone has none. The owner's expectation holds; the seven-reading grid still has none at 1/10, because the decoder binds.

**Deciding figure.** 8 of 8 marks met; 164,051,805 pairs in 62 census groups with 28 distinct histograms; the promise kept in 35 of 35 cells of the second reading; 245 cells classified; at 1/10 and floor 999/1000 the second reading keeps 0.9796 of its answers at residual 4.61e-5; 10 of 10 runtime programs as computed.

**Recomputed by.** `glm_universal.reasoning.agree_channel_marks.agree_channel_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

Candidate P of [`STATUS.md`](../STATUS.md) §3.4, item **P4**, named by
[`CONFIDENCE_FLOOR_STUDY.md`](CONFIDENCE_FLOOR_STUDY.md) §3: *the second
reading has no exact channel measure: its reads are pairs, and the hunt covers
the decoder and the context stage only.* Phase 80 declared a sum over every
pair of received words out of reach, and gave `agree` the floor and the graded
answer in the runtime without a place in the hunt.

The owner's instruction for this round: find an exact measure for the second
reading by testing, and take the most effective method. The owner supplied one
route — extend the census from outcomes to per-candidate masses and distance
profiles, so that every (rate, threshold) cell becomes a rational evaluation of
one-time integer tables — with five decision points. This study answers them
as follows.

1. **The pair model.** Two were offered: (a) one truth, two independent reads
   at the same rate; (b) one received word read at two layers. The runtime
   fixes it: `agree_confidence` already declares *the reads are of one
   carrier, each bit of each read flipping independently at the declared
   rate* and multiplies the two reads' likelihoods. So the measure is (a);
   (b) has no pair and is not the runtime's reading.
2. **Are the case sets subgroups?** Measured, not assumed (mark G1). The
   runtime's `agree` takes no cases: it intersects the two reads' carried
   forks over all 4096 codewords. So the case sets do not enter this measure;
   whether they are subgroups is recorded because the owner asked.
3. and 4. belong to the rate round (item P5), not this one.
5. **The class collapse** (a pair's confidence as a function of a few integers
   of the pair) is taken as a declared finite check, not a Lean theorem (mark
   G2), as the owner allowed.

**What the owner's factorization measures, and what the runtime does.** The
suggested route squares single-read masses: `P(both reads decode to j) =
A_j²`. That is the measure of *strict* agreement — both reads decoded
uniquely, to the same codeword. The runtime's `agree` answers more: it
intersects the carried forks, so a read decoded uniquely to `c` and a read at
coset weight 4 whose six nearest codewords include `c` resolve to `c`, and two
coset-weight-4 reads whose sextets share exactly one codeword resolve to it.
So the factorization is kept as a second route for the part of the census it
covers (G1), and the measure of the runtime's reading needs the pairs
themselves.

**Scoping, declared.** Before these declarations were written, a throwaway
prototype of the census below was run to learn whether it was feasible in pure
Python: it was (a few seconds). That prototype printed the unfloored figures
and the floor table of the second reading at all five rates, so the hunt's
outcome for `agree` is **not** a blind prediction in this round, and the key of
G2 was found by that scoping. The owner's own declared expectation — *at 1/10,
where the decoder alone has no working threshold, decoder-plus-agreement may
have one* — was written before any computation; it is kept as the owner wrote
it. The marks below are about whether the measure is right, which scoping
cannot settle.

## 1. Declarations — written before the module that measures them

**The reading.** `agree(y1, y2)` at a declared rate `p`: the carried fork of
`y1` (its nearest codewords — one at coset weight `≤ 3`, six at weight 4)
intersected with that of `y2`; resolved when exactly one codeword survives,
refused `AMBIGUOUS` when more than one does and `UNCORRECTABLE` when none does.
Its confidence is Phase 77's: the posterior of the survivor under the product
of the two reads' likelihoods, over all 4096 codewords.

**The channel measure.** The truth is drawn uniformly from the 4096 codewords;
the two reads are that truth with independent errors, every bit of each read
flipping independently at the true rate. Every probability is exact.

**The census — how every pair is counted.** By linearity the truth is the
zero word. Every resolved pair is `(v + λ1, v + λ2)` for a codeword `v` (the
survivor) and a pair `(λ1, λ2)` in

`R = { (λ1, λ2) : wt λ1 ≤ 4, wt λ2 ≤ 4 } minus { both of weight 4, λ1 ∪ λ2 inside one octad }`

— the pairs whose forks meet exactly at zero. (A weight-4 error lies in its own
fork's sextet; a second common codeword would be an octad containing both.)
For such a pair the right mass is `w(λ1) w(λ2)` and the wrong mass is
`Σ_{v ≠ 0} w(v + λ1) w(v + λ2)`, where `w(e) = p^wt(e) q^(24−wt(e))`; the pair's
confidence is `ρ^D(0) / Σ_c ρ^D(c)` with `ρ = p/q` and `D(c) = d(λ1, c) + d(λ2,
c)`. All three depend on the pair only through the **histogram of `D`** over
the 4096 codewords — a rate-independent integer table. So the census is: for
each distinct histogram, how many pairs of `R` have it.

**The symmetry that makes it one pass.** A permutation of the 24 coordinates
that maps every codeword to a codeword preserves every histogram and the octad
condition. Automorphisms are found by a declared search (images of five points
completed by backtracking over the octads), each verified to map all 4096
codewords into the code; the group they generate is verified transitive on the
subsets of each size `w ≤ 4`. Then every `λ1` of weight `w` has the same census
row, and the census is `Σ_w C(24, w) × (the row of one λ1 of weight w)` — 12,951
second errors for each of five first errors.

**G1 — the census is right.** (i) `|R|` counted by the census equals
`12,951² − 3,676,596`, the octad pairs counted by hand (759 octads × 70 × 69
ordered pairs of distinct 4-subsets, plus the 10,626 equal pairs). (ii) The
strict-agreement mass — pairs with both errors of weight `≤ 3` — equals
`Σ_c A_c²`, with `A_c = P(one read decodes uniquely to c)` taken from the
distance distribution of the code, exactly, at every rate of the hunt. (iii)
The mixed mass — one error of weight `≤ 3`, the other of weight 4 — equals
`2 Σ_c A_c T_c`, with `T_c` the probability that a read lies at coset weight 4
with `c` among its six nearest codewords, exactly. (iv) On a declared stride of
pairs of `R`, each translated by a codeword, the census's value and confidence
equal the runtime's `agree_confidence` and a brute-force `Fraction` sum, 0
disagreements; and on a stride of the excluded octad pairs, the runtime
refuses `AMBIGUOUS`. (v) The automorphisms preserve the code and generate a
group transitive on every weight `≤ 4`. (vi) Recorded, as the owner asked:
whether each of K1's case sets `S_2 … S_32` is a subgroup.

**G2 — the class collapse, a declared finite check.** Over every pair of `R`,
the histogram of `D` (hence the confidence at every rate, and both masses) is a
function of the key `(wt λ1, wt λ2, |λ1 ∩ λ2|, m, e)`, where `m` is the largest
number of points of `λ1 ∪ λ2` in one octad and `e` says whether an octad
meeting the union in `m` points contains `λ1` or `λ2`. Recorded beside it: how
many keys of the owner's coarser key `(wt λ1, wt λ2, |λ1 ∩ λ2|)` split.

**G3 — the promise.** In every cell of the second reading (five rates, seven
thresholds), `P(wrong | answered) ≤ 1 − t` exactly.

**G4 — the hunt, enlarged.** Seven readings (the decoder, the context stage
over `S_2 … S_32`, and `agree`) × five rates × seven thresholds: 245 cells, each
classified. Phase 80's 210 cells are unchanged, figure for figure. The working
threshold is named per rate for the seven-reading grid and for `agree` alone,
and the classification is monotone in the threshold and in the rate.

*Declared expectations, not marks:* (E1) the second reading's own working
threshold is at least the decoder's at every rate; (E2) the owner's — at 1/10,
where the decoder alone has no working threshold, the second reading has one.

**G5 — agreement lowers the residual.** At every rate, the second reading's
unfloored `P(wrong | answered)` is at most the decoder's, and so is strict
agreement's; the Lean theorem of G8 proves the second for any reading whose
truth is its modal answer, and G5 also checks that hypothesis (`A_0 ≥ A_c` for
every codeword `c`) at every rate.

**G6 — the declared rate.** With the rate overdeclared (reads at `p/2`,
confidence at `p`) the second reading's promise holds in all 35 cells; with it
underdeclared (reads at `2p`) every broken cell is reported.

**G7 — the runtime, computed not reasoned.** A declared set of `agree_at` and
`agree_floor` programs, each with its outcome **computed from the census**
(the class of its pair, its confidence, the floor) before the runtime is run —
the lesson of Phase 80's one missed program. Every program as computed, 0
wrong; every answer's script prints `VERIFIED True`.

**G8 — Lean** (`RequestProject/GLM/Agree.lean`). `agree_answered_sq`: two
conditionally independent reads decode to `j` together with probability
`A_j²`. `agree_residual_le_single`: if the truth is the modal answer, strict
agreement's `P(wrong | answered)` is at most the single reading's.
`agree_conf_sum`: the product of two reads' likelihoods on the binary symmetric
channel is the likelihood at the summed distance. `pair_distance_split`: bit
by bit, `[x ≠ c] + [y ≠ c] = [x ≠ y] + 2 [x = y ≠ c]` — two reads are an
erasure where they differ and a doubled read where they agree. No `sorry`; the
standard axioms only.

## 2. Results

Recomputed by `agree_channel_report` (about 17 seconds, pure Python,
`Fraction` throughout); `tests/test_agree_channel.py` keeps every figure below.

### 2.1 G1 — the census: met

(i) The census counts 164,051,805 pairs in `R`, equal to `12,951² − 3,676,596`
exactly; they fall in 62 census groups. (ii) and (iii) At every rate of the
hunt the strict-agreement mass and the mixed mass from the census equal the
factorized routes `Σ_c A_c²` and `2 Σ_c A_c T_c` exactly — the owner's
factorization and the pair census are two routes to the same rationals where
they overlap. (iv) On a stride of 195 pairs, each translated by a codeword,
the census's value and confidence equal the runtime's `agree_confidence` and
the brute-force `Fraction` sum: 0 disagreements; 25 of 25 excluded octad pairs
are refused `AMBIGUOUS` by the runtime. (v) 4 verified automorphisms generate a
group with one orbit on the 24, 276, 2,024 and 10,626 subsets of sizes 1–4
(transitive). (vi) None of `S_2 … S_32` is a subgroup — so the owner's
translation shortcut is not available for the case sets, and the per-set
modal-truth hypothesis stays a checked mark rather than a consequence.

### 2.2 G2 — the class collapse: met

The fine key `(wt λ1, wt λ2, |λ1 ∩ λ2|, m, e)` takes 63 values and none of them
splits: every pair's histogram, hence its confidence at every rate and both
its masses, is a function of the key. There are only 28 distinct histograms.
The owner's coarser key `(wt λ1, wt λ2, |λ1 ∩ λ2|)` takes 53 values and 9 of
them split (for example `(3, 3, 0)` and `(4, 4, 0)`) — the octad type of the
union matters, as the owner anticipated for the disjoint case.

### 2.3 G3 — the promise: met

In 35 of 35 cells of the second reading, `P(wrong | answered) ≤ 1 − t`
exactly; 0 broken.

### 2.4 G4 — the hunt, enlarged: met

245 cells, each classified; Phase 80's 210 cells are unchanged, and so are its
working thresholds. The classification is monotone in the threshold and in the
rate, for the seven-reading grid and for the second reading alone.

| rate | decoder | seven readings | second reading alone |
|---|---|---|---|
| 1/1000 | 9999/10000 | 9999/10000 | 9999/10000 |
| 1/100 | 9999/10000 | 9999/10000 | 9999/10000 |
| 1/50 | 9999/10000 | 9999/10000 | 9999/10000 |
| 1/20 | 999/1000 | 999/1000 | 9999/10000 |
| 1/10 | none | none | 999/1000 |

The second reading at 1/10:

| floor | works | retention | residual | wrong removed |
|---|---|---|---|---|
| 9/10 | yes | 1 | 3.84e-4 | 0 |
| 99/100 | yes | 0.9809 | 4.92e-5 | 0.874 |
| 999/1000 | yes | 0.9796 | 4.61e-5 | 0.882 |
| 9999/10000 | no | 0.8508 | 2.31e-6 | 0.995 |

At 9999/10000 the promise is kept but the retention falls below the hunt's
declared bar (retention ≥ 9/10), so it is not a working threshold. *Expectations:* E1 holds (the
second reading's threshold is at least the decoder's at every rate, and higher
at 1/20 and 1/10); E2, the owner's, holds — at 1/10, where the decoder alone
has no working threshold, the second reading has one, 999/1000. The owner's
back-of-envelope guess of "999/1000 or higher" is met at exactly 999/1000, not
higher. The seven-reading grid still has none at 1/10: the grid needs every
reading to work, and the decoder binds.

### 2.5 G5 — agreement lowers the residual: met

| rate | P(right) | P(wrong) | refused | residual, second reading | residual, decoder | residual, strict agreement |
|---|---|---|---|---|---|---|
| 1/1000 | 1 | 5.81e-21 | 8.37e-11 | 5.81e-21 | 4.17e-11 | 2.29e-24 |
| 1/100 | 1 | 4.67e-12 | 7.25e-6 | 4.67e-12 | 3.53e-6 | 1.64e-14 |
| 1/50 | 0.9998 | 1.85e-9 | 1.98e-4 | 1.85e-9 | 9.40e-5 | 1.17e-11 |
| 1/20 | 0.9881 | 3.01e-6 | 0.0119 | 3.05e-6 | 0.00539 | 3.87e-8 |
| 1/10 | 0.8365 | 3.21e-4 | 0.1631 | 3.84e-4 | 0.0784 | 9.50e-6 |

The modal-truth hypothesis `A_0 ≥ A_c` holds at every rate. At 1/10 the second
reading answers more often right than the decoder (0.8365 against 0.7857) and
wrong about 200 times less often (3.21e-4 against 0.0668), at the price of
refusing 0.1631 of pairs.

### 2.6 G6 — the declared rate: met

Overdeclared (reads at `p/2`): 0 of 35 cells broken. Underdeclared (reads at
`2p`): 4 broken, all at declared rate 1/10 — floors 49/50, 199/200, 999/1000
and 9999/10000; the worst is 999/1000, residual 0.00851 against the promised
0.001. As in Phase 80, underdeclaring the rate is the dangerous direction —
the motive of the rate round (Phase 82).

### 2.7 G7 — the runtime, computed not reasoned: met

10 of 10 `agree_at` / `agree_floor` programs returned the outcome computed
from the census before they ran (answers, `BELOW_FLOOR`, `AMBIGUOUS`,
`UNCORRECTABLE`); 0 wrong; every answer's script prints `VERIFIED True`.

### 2.8 G8 — Lean: met

`RequestProject/GLM/Agree.lean` proves `agree_answered_sq`,
`agree_residual_le_single`, `agree_conf_sum` and `pair_distance_split`, with
the helpers `bsc_mul_bsc` and `bit_split`; no `sorry`, axioms `propext`,
`Classical.choice` and `Quot.sound` only.

## 3. What this round moved, and what it leaves

**Moved.** The second reading is in the hunt: an exact measure, one census,
and a working threshold at 1/10. The most effective method found by testing
was not the owner's centered-profile convolution: the runtime's reading
intersects carried forks, so it needs the pairs, and the pairs collapse under
the code's automorphisms to 5 × 12,951 rows and 28 histograms. The owner's
factorization survives as the second route of G1.

**Leaves.** The floor at 1/10 for the grid is still refused by the decoder;
the rate must still be declared by the caller — Phase 82 measures what it
costs to estimate it instead.
