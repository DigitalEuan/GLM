# Run 41 notes — 17 November 2026

Two independent jobs this round: **PL-14** (rebuild the λ training grid on the
proven-optimal rows, lift the clamp, fit once, test once) and **PL-16** (the
owner's call to widen the window past 1000 and find the easy rows up there).

---

# Part 1 — PL-14: the proven grid, the lifted clamp, one interior fit

## The grid

| | |
| --- | --- |
| rows | 8 proven-optimal rows: **n = 13, 32, 45, 60, 76, 96, 120, 143** (all in `proven_floors`) |
| amps | **0.002, 0.005, 0.01, 0.02, 0.06** — spans excess 0.003 … 0.30 |
| λ | 0, 1, 10, 100, 1e3, **1e4, 1e6, 1e8** |
| seeds | 1 (declared; the test keeps 2) |
| clamp | lifted to 1e12 in the rule *and* in the fit; candidate e0 range widened to 1e-9 … 1e2 |
| cost | 40 cells × 8 λ = 320 chains + refit + 16 test cells + 8 push cells ≈ 22 min |

The λ grid runs to 1e8 because PL-13's fit sat at the 1e4 clamp: a fit that
cannot look above its own ceiling has not found an interior optimum.

## The fit — interior, and it tracks the ladder

**e0 = 0.008577**; max regret **0.554**, mean regret **0.106**.

λ by cell (5 amps × 8 rows):

| amp | measured excess | λ from the rule |
| ---: | ---: | --- |
| 0.002 | 0.0028–0.0055 | **0.10 – 0.30** |
| 0.005 | 0.0081–0.013 | **0.89 – 2.17** |
| 0.01 | 0.020–0.028 | **5.4 – 10.7** |
| 0.02 | 0.045–0.055 | **41 – 62** |
| 0.06 | 0.30–0.35 | **1189 – 1935** |

The two-parameter form `λ = (excess/e0)²` reproduces the measured optimum
ladder across four decades. The max regret of 0.554 (3.5×) is the honest cost
of that form: within one amp the optimum still varies by n, and no monotone
law in excess alone can follow both.

## The 16 cells, once, with the frozen rule

| | geo mean | median | ≥5% better | ≥5% worse | best | worst |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| best-of-seven (§7, biased) | 0.674 | 0.935 | 9 | 0 | 0.183 | 1.029 |
| mean-\|log\| rule (§10) | 0.898 | 0.977 | 5 | 1 | 0.417 | 1.055 |
| min-max, clamped (§11) | 1.143 | 0.981 | 8 | 7 | 0.255 | 10.60 |
| **proven-grid, interior (§12)** | **0.975** | 0.954 | 8 | 2 | 0.246 | 9.06 |

By corruption:

| amp | §11 clamped | **§12 interior** |
| ---: | ---: | ---: |
| 0.005 | 3.575× worse | **1.016× (neutral)** |
| 0.01 | 1.469× worse | 2.677× worse |
| 0.04 | 0.488× | **0.507×** |
| 0.08 | 0.667× | **0.656×** |

**This is the first rule in the project that beats switching the term off**
while actually engaging it: 2.5% better overall, and the heavy-corruption
gains (0.51×, 0.66×) are preserved intact. Covering the gentle regime cost
nothing at the heavy end — it only removed the 3.58× gentle wreckage.

## What it did not fix: the amp-0.01 band is bimodal

| n | λ | control E | rule E | ratio |
| ---: | ---: | ---: | ---: | ---: |
| 20 | 8.03 | 1.330e-04 | 8.288e-04 | **6.23×** |
| 60 | 6.28 | 5.423e-04 | 5.009e-04 | 0.92× |
| 110 | 2.06 | 7.094e-04 | 6.428e-03 | **9.06×** |
| 240 | 1.94 | 4.417e-03 | 4.348e-03 | 0.98× |

Same amp, same λ band, outcomes flipping between 0.9× and 9× — and on
sub-milli absolute energies (the control at n=20 is already at 1.3e-4, i.e.
nearly feasible; 8.3e-4 is not a quality loss, it is a different basin). The
training cells at amp 0.01 all measured 0.89–1.31× at λ = 10, so the grid did
not predict it either: this is **per-n bimodality**, not a mis-weighted term.
Logged as PL-15; the discriminating experiment is 6 seeds at amp 0.01 only.

## The push, third weighting

λ = 11–55 at excess ≈ 0.03 (genuinely engaged, no clamp, no saturation):

**0 of 8 gated `L`, 0 of 8 below the record** — geo 1.069, median 1.028, best
0.906, worst 1.419. Rules *off* (§10), *saturated* (§11) and *interior* (§12)
now all give 0/8. The wall is not a weighting choice.

---

# Part 2 — PL-16: the window above 1000

Instrument `scripts/beyond1000.py`, ledger `workspace/push/beyond1000.json`,
record `08-BEYOND-1000.md`.

For k = 32..99: the k × k integer lattice gives `square k^2` (L = k) and
`k^2−i` for i = 1..4 (L = k, **provably optimal** by T-084/T-086/T-064/T-081);
the lattice plus j squares in a new row gives `k^2+j` for j = 1..k (L = k+1).

Validity is exact and elementary: two axis-aligned unit squares with integer
centres overlap only if their centres coincide, because distinct integer
points differ by ≥ 1 on some axis. So the check is "centres distinct", O(n),
no tolerance. `--gate` confirms the argument against `packlib` on 24 spread
states.

| | |
| --- | ---: |
| rows built | **4,794** |
| distinct n | 4,794 |
| n range | 1020 … 9900 |
| invalid | **0** |
| share of the 9,000-row window | **53.27%** |
| provably optimal | 340 |

Gate sample: **24 rows, all_match True**, gate `L` == design `L` exactly
(drift 0.0).

**What it means for the bigger picture.** More than half of the range above
1000 is closed-form constructible, and 340 of those rows are proven optimal.
The covered half is the *lower* half of every band (j ≤ k); the uncovered 47%
is n = k²+j with j > k, the upper half of every band, where `L = k+1` stops
being plausible and a real arrangement is required. That half is where the
non-vacuum work above 1000 lives, and this tree says nothing about it.

**The corollary that matters for training.** Every easy row above 1000 is a
lattice row — 100% of them, by construction. Widening the window with the easy
rows widens the **vacuum**, not the vocabulary: 4,454 of the new rows are
axis-aligned lattices whose contacts all fall in the two relation cells the
run-40 census found to be 99.99% of the proved end of the table. That is not an
argument against the wider window — it is what the wider window is *for*: a
much larger sample of the vacuum phase, the exact depth ladder above 1000, and
a precise statement of where the non-vacuum work is. It is not a training set
for the seam vocabulary, because the easy rows have no seams.

---

---

# Part 3 — PL-17: all 156 proved rows, and PL-15 settled

**Order.** The grid should be **all 156 proved rows**, not the 8; then the
amp-0.01 probe with six seeds to settle whether those two failures were
variance.

## Cost, and what the infrastructure learned

Measured: ≈ 0.077 · n^0.77 s per chain, so 156 rows × 5 amps × 8 λ = **780
cells = 10.6 h serial**, **27.5 min on 8 workers**. Two cloud-runner restarts
killed the run at 430 and 686 cells with *nothing persisted* — my error: the
grid lived only in memory. It is now checkpointed per cell to
`workspace/push/train_proven_all.jsonl` and relaunched by
`scripts/_run_proven_all.sh`, which resumes from the checkpoint; the third
attempt lost nothing. ~25 min was thrown away learning that, which is the same
lesson as the science: do not expect one uninterrupted run to be the truth.

## The fit

| grid | e0 | max regret | mean regret | λ at amp 0.06 |
| --- | ---: | ---: | ---: | ---: |
| 8 rows (§12) | 0.008577 | 0.554 | 0.106 | 1189–1935 |
| **156 rows** | **0.036869** | **1.463** | **0.0882** | **≈ 77** |

λ by amp (median): **0.009 / 0.068 / 0.367 / 2.42 / 77.1** for amps 0.002 …
0.06.

**Mechanism check — it is not n.** The cells' own best λ is flat across n
bands: amp 0.06 gives **1000 / 1000 / 1000** for n < 100 / 100–399 /
400–961. So the full set is gentler not because big packings want a weaker
term, but because 156 heterogeneous rows make min-max buy uniformity instead of
sitting on anyone's optimum. That shows up as **worse max regret (0.554 →
1.463) with better mean regret (0.106 → 0.088)**.

## The 16 cells, once

| | geo mean | median | ≥5% better | ≥5% worse | best | worst |
|---|---:|---:|---:|---:|---:|---:|
| best-of-seven (§7, biased) | 0.674 | 0.935 | 9 | 0 | 0.183 | 1.029 |
| mean-\|log\| rule (§10) | 0.898 | 0.977 | 5 | 1 | 0.417 | 1.055 |
| min-max clamped (§11) | 1.143 | 0.981 | 8 | 7 | 0.255 | 10.60 |
| min-max, 8 proved (§12) | 0.975 | 0.954 | 8 | 2 | 0.246 | 9.06 |
| **min-max, 156 proved** | **0.782** | 0.946 | **8** | **0** | 0.32 | **1.028** |

By amp: 0.005 **1.011×**, 0.01 **0.885×**, 0.04 **0.592×**, 0.08 **0.705×**.
**The first rule in the project with no bad cells**: 22% lower polished energy
at equal budget, worst cell 1.028 (noise floor), and still within 16% of the
*biased* best-of-seven oracle.

## The push, fourth weighting

λ = 0.6–3.0, engaged: **0 of 8 gated, 0 of 8 below the record** (geo 1.049,
best 0.929). Off, saturated, interior-8, interior-156 — one answer.

## PL-15, settled in two halves

Six seeds per cell at amp 0.01, paired arms:

| n | λ | geo6 | first 2 | spread | per-seed ratios |
| ---: | ---: | ---: | ---: | ---: | --- |
| 20 | 0.509 | 1.020 | 1.016 | 1.66× | 0.79 1.31 1.00 1.09 1.00 1.00 |
| 60 | 0.294 | 0.980 | 0.936 | 1.15× | 1.00 0.88 1.01 1.00 1.00 1.00 |
| 110 | 0.115 | 1.018 | 1.006 | 1.25× | 1.01 1.00 1.02 0.93 1.16 1.00 |
| 240 | 0.104 | **0.551** | 0.316 | **4.01×** | 0.30 0.34 1.00 1.00 0.26 1.06 |

1. **The 6.23× / 9.06× failures were λ, not the band.** They ran at λ = 2–8,
   which is what the *eight-row* fit assigned. At the full-set λ the same two
   cells are **1.02× and 1.02×**.
2. **The residual wobble is bistability.** At n = 240 four seeds are inert and
   two engage (0.30, 0.34) — modes ~3.4× apart. Two seeds said 0.316; six say
   0.551. A single chain cannot report the value of λ.

## The ⅀Δ reading, applied

Five results in a row landed on a boundary, and each time the answer lived just
outside the window drawn: the 1e4 clamp, the degenerate criterion, the grid's
missing gentle regime, the eight-row sample, the bistable cell whose two-seed
estimate was 1.8× wrong. That is a limit cycle around the truth rather than a
static crystal, and it changes three practices — all of which are now in the
instrument, not just in prose:

* **Report distributions.** `--probe-amp01` prints six seeds and the spread.
* **Saturation means the window is wrong.** Both fits that pinned to a bound
  were re-measured further out, and both moved inside.
* **Prefer the compromise, and do not read a jam as a tuning failure.** The
  rule that travels best has the *worse* max regret. The push's 0/8 under four
  weightings is a jam, and `delta_sigma_push.py` — unrun, `finds_DS.json`
  absent — already classifies a jam as **RIGID_WALL** (ρ > 0.5: change motif)
  or **liquid** (ρ ≤ 0.5: retry rotation-rich). That is PL-18, the experiment
  that asks what λ cannot answer.

---

# Part 4 — flag audit, and PL-18: the jam is liquid

## The flag surface

`--dither` parsed, sat in the dispatch guard, and had **no body** — it ran
nothing and said nothing. That is the worst kind of CLI defect: a flag that
looks like it did work. Removed, along with the superseded 8-row training path
that PL-17 replaced:

* `--dither` and its guard entry;
* `--fit-proven`, `--rule-proven`, `--push-proven`, the serial `train_grid`
  they used, and `PROVEN_TRAIN_ROWS`. §12's measured results stay in the
  record; only the code path is gone.

Added so the class cannot recur:

* **`audit_flags`** — an explicit flag → section map. After the action block,
  any requested flag that left `res` untouched makes `main` exit 2 and names
  the flag. Verified with a stub (`['--check']` when `res` is empty, `[]` when
  satisfied); `--dither` is now an argparse error.
* **`--dump-jam-states`** — reproduces the eight push cells' final states and
  writes `workspace/push/jam_states.json`, so the push table's energies now
  come with the states that produced them.

Also fixed: `sa_push.py` and `delta_sigma_push.py` hardcoded `/home/z/my-project`
at import, so the classifier could not even be imported off the owner's
machine. Both resolve relative to the scripts directory when that root is
absent.

## The classification

`delta_sigma_push.py --from-states`: contact bit-stream over squares sorted by
x, lag-1 autocorrelation ρ, ρ > 0.5 → RIGID_WALL else ONE_PARAM_JAM.

| n | d | seed | ρ | contacts | verdict |
| ---: | ---: | ---: | ---: | ---: | --- |
| 20 | 1%/2% | 0 | nan (0.95) | 19/20 | RIGID_WALL *(degenerate)* |
| 20 | 1%/2% | 1 | −0.056 | 19/20 | ONE_PARAM_JAM |
| 60 | 1%/2% | 0 | **+1.000** | **60/60** | **RIGID_WALL** |
| 60 | 1%/2% | 1 | +0.482 | 58/60 | ONE_PARAM_JAM |
| 110 | 1% | 0 | +0.090 | 98/110 | ONE_PARAM_JAM |
| 110 | 1% | 1 | +0.315 | 107/110 | ONE_PARAM_JAM |
| 110 | 2% | 0 | +0.190 | 105/110 | ONE_PARAM_JAM |
| 110 | 2% | 1 | +0.315 | 107/110 | ONE_PARAM_JAM |
| 240 | 1% | 0 | −0.039 | 231/240 | ONE_PARAM_JAM |
| 240 | 1% | 1 | −0.026 | 234/240 | ONE_PARAM_JAM |
| 240 | 2% | 0 | +0.145 | 234/240 | ONE_PARAM_JAM |
| 240 | 2% | 1 | −0.019 | 235/240 | ONE_PARAM_JAM |

**4/16 rigid, 12/16 liquid, 2 degenerate.**

* **Every state at n ≥ 110 is liquid.** The jam is a one-parameter family with
  an 89–98% saturated contact network: the missing freedom is **rotational**,
  which is the classifier's own prescription (`rotate_frac = 0.5`) and is
  PL-19.
* **Rigid only where the lattice is total**: n = 60 seed 0 has all 60 squares
  in contact (ρ = 1.000), and n = 20 is below the classifier's resolution
  (19/20 leaves ρ undefined).
* **The verdict flips with the seed** at fixed n and depth — §13's
  bistability, now visible in contact order rather than energy.

**Correction to the record.** §11–§13 said "the wall is mechanical, not a
weighting choice". That was an inference from four weightings agreeing at 0/8,
and it is wrong: the wall is mechanical only at n = 60 seed 0. At the cells
that matter it is a liquid jam, i.e. a limit of the move grammar, not of the
target.

## A silent wrong answer inside the classifier

The first run printed `rho=nan -> ONE_PARAM_JAM`. With 19 of 20 squares
touching, one lag slice is constant, `np.corrcoef` returns nan, and the old
`if rho > 0.5` fell through to the liquid branch **without comment**. Fixed:
`classify` falls back to the contact fraction (≥ 0.9 = crystalline) when ρ is
undefined, keeps ρ as nan, and the ledger records `degenerate: true`. The same
failure class as `--dither`, one layer down — which is why the audit exists.

## The wider perspective, from three angles

1. **Objective**: a rule fitted on all 156 solved rows gives 22% lower polished
   energy at equal budget with no bad cells (§13). That part is settled.
2. **Contact word**: still not recovered (Jaccard 0.018–0.054). The term is a
   prior, not a decoder.
3. **Jam**: liquid, not rigid. The 0/8 is about what the move grammar can
   reach, not about what packings exist.

And the census above 1000 closes it: the easy rows there are crystalline by
construction, while the hard half (n = k²+j, j > k) is exactly where a
rotation-starved liquid jam would live. The classifier labels a state in O(n²)
with no tolerance and no feasibility gate, so it is the one instrument here
that can be pointed at the >1000 rows without a packlib pass first.

---

# Part 5 — PL-19: rotation-rich moves, negative

## Cleanup

Deleted `scripts/_patch_flags.py` (the one-shot patcher). The only file left in
`scripts/` matching `_*` is `_run_proven_all.sh`, which is the documented
resume wrapper and is referenced from the record.

## What the annealer actually did before

`relax_graded` already rotated — `rotate_frac = 0.3`, and the angular step was
tied to the anneal temperature (`0.9*T`), collapsing to **±0.0015 rad** in the
polish phase. So angles were frozen exactly where the jam forms. PL-19 is about
the amplitude, not the presence of rotation.

## The change

* `relax_graded(..., rotate_frac=0.3, rot_amp=None)`. Defaults reproduce the
  old code bit for bit: the λ = 0 recovery test still matches (2.333e-03,
  9.208e-02), and the rule arm below reproduces the stored `push_proven_all`
  geo exactly (1.0486 vs 1.0486).
* `--push-rotation`: four arms (ctl / rule / rot_only / rot_rule) over the
  eight cells, `rotate_frac = 0.5`, `rot_amp = 0.05` (**33× the polish step**).
* Registered in `FLAG_SECTION`, so the audit covers it — a new flag cannot be
  added without a section to show for it.

## The result

| n | d | λ | rule | rot_only | rot_rule |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 20 | 1% | 2.97 | 1.040× | 1.163× | **2.472×** |
| 20 | 2% | 2.97 | 1.024× | 0.994× | 1.359× |
| 60 | 1% | 2.41 | 1.030× | 1.000× | 1.000× |
| 60 | 2% | 2.41 | 1.005× | 1.000× | 1.000× |
| 110 | 1% | 0.99 | 1.344× | 0.951× | **2.776×** |
| 110 | 2% | 0.99 | 1.072× | 0.986× | 1.755× |
| 240 | 1% | 0.61 | 0.929× | 1.071× | 1.123× |
| 240 | 2% | 0.61 | 0.991× | 0.942× | 1.120× |

| arm | geo | median | best | worst | gated |
| --- | ---: | ---: | ---: | ---: | ---: |
| rule | 1.049 | 1.027 | 0.929 | 1.344 | **0/8** |
| rot_only | 1.011 | 0.997 | 0.942 | 1.163 | **0/8** |
| rot_rule | **1.459** | 1.241 | 1.000 | 2.776 | **0/8** |

**No arm gated a single cell.** The treatment is 46% worse in energy; rotation
alone is neutral.

## Contact order after rotation

| | PL-18 | after |
| --- | ---: | ---: |
| RIGID_WALL | 4/16 | **7/16** |
| ONE_PARAM_JAM | 12/16 | 9/16 |
| all squares in contact | 2/16 | **7/16** |

n = 20 is 20/20 at both seeds and both depths. Extra angular freedom is being
spent **closing contacts**, not opening space — the opposite of breaking a jam,
and consistent with the container being over-full for this grammar at d = 1–2%.

## What this refutes

* **"Liquid ⇒ rotation-rich retry" does not transfer.** It is a heuristic from
  the shrink-loop campaign on other targets. Here: 0/8 and a 46% penalty.
  `ONE_PARAM_JAM` means "not crystalline", not "rotation-limited".
* The wall has now survived **five** distinct attacks: four weightings
  (§10–§13) and angular freedom (§16). It is neither a weighting artefact nor
  an angular artefact.
* Remaining explanations are about **reach**: budget too small to find a state
  that exists, or no state exists at that L for this square set. Those are
  different claims, and distinguishing them is PL-20 (bisect d in (0, 1%] for
  the smallest depth that ever gates; plus the existing *collective* patch move
  as a second, non-angular freedom).



* Ledger keeps every arm: `rule_fit`, `rule`, `push_rule`, `rule_fit_minmax`,
  `rule_minmax`, `push_rule_minmax`, **`rule_fit_proven`, `rule_proven`,
  `push_proven`**, `proven_census`, and the new `workspace/push/beyond1000.json`.
* The λ = 0 recovery test still reproduces run 39's stored medians exactly.
* Nothing committed.

---

# Part 6 — the cascade, modelled and derived backwards (run 42)

Full record: `09-CASCADE.md`. Short form:

## Two corrections to our own record

* **`table.json` is stale.** It scores 22.645991 (543 beats); the delivered
  `submission.csv` scores **22.218056945 (553 beats)** and **357 rows
  disagree**. "table.json and submission.csv untouched" was true but hid that
  they disagree. Any script writing `table.json` back regresses by 0.43. PL-23.
* **"No packings above 1000" was wrong.** `extended_table_5000.json` has 4,000
  rows (n = 1001-5000), 805 non-grid, 33 with states (gated True, e.g. n=1028
  at 32.556349) — but **772 of the 805 have no state**. PL-24.

## The cascade as arithmetic

Slack `delta(n) = L(n) - floor(sqrt(n))`; a row beats grid iff `delta < 1`. One
step adds the `2k+1`-cell band and increments k, so `(r, delta)` is invariant:

> if some row `k0^2 + r` has slack `delta < 1`, then every `k^2 + r`, `k >= k0`,
> is packed in container `k + delta`.

The first draft claimed container `k` (delta = 0), refuted by the area bound; the
documented chain 5@2.8 -> 10@3.8 -> 17@4.8 (r = 1, delta = 0.8) witnesses that
the invariant is the pair. Backwards: `L(n) <= k + running_min delta(k0^2 + r)`,
so 1000 targets collapse to **60 residuals with one slack each**.

## Measurement against the CSV table

| | |
| --- | ---: |
| rows covered by the model | 931 / 969 |
| table >= prediction | 491 |
| table worse | 25 (gain 2e-9 — rounding) |
| table **better** | 415, worth **0.481427** |
| residues with a base | 37 / 60 |

**The cascade is saturated** — it has been applied, and nothing is left in
applying it. Construction beats the chain by 0.481 across 415 rows, so the
cascade is a floor generator, not the engine.

## Where the score is

22.218056945 = **15.022691** in 553 beating rows + **7.195366** in 447 grid
rows. The upside is concentrated in the **23 residues with no base** (r = 38-60),
the upper half of every band. A base with slack delta in residue r banks
`(1 - delta) * W(r)` with `W(r) = sum 1/sqrt(n)` over the column: r = 38 gives
**0.257** at delta 0.5 and **0.103** at delta 0.8. The run-35 source import
gained 0.0036 — one mediocre base is 28x that. These are the same rows §08 called
unconstructible above 1000: `r > k` is the top of every band.

## Repository survey

`cascade2/3.py` (planner; chains saturated), `closure_apply.py` (removal
closure; already applied, gain 0), `packlib` (the gate), `delta_sigma_push.py`
(run, PL-18/19), `extended_table_5000` (above 1000, partly unverified), the
import pipeline (run 35's gain). `src/lean/RequestProject/GLM/Cascade.lean` is a
**different** cascade — MASH 1-1 with an exact `O(1/M^2)` triangular-window
theorem. It says nothing about packings; only the discipline of stating a gain
exactly transfers, which §2 of `09-CASCADE.md` does. No measurement supports
importing it further and I will not claim otherwise.

---

# Part 7 — Leech addresses (run 43), and what they refute

Proposal: 24 Leech coordinates as 24 pockets of data, arranged systematically,
as a higher language for the packings. Instrument `scripts/leech_address.py`,
record `10-LEECH-ADDRESS.md`.

Room grounding: `LeechResidue.lean` gives the exact integer form of Λ₂₄ from the
GLM's Golay code **and proves that syndromes mod 8/144/256 carry no information**
(Λ₂₄ + mℤ²⁴ = Λ₂₄ for 8|m); `leechlean/3_leech_bridge/out/codebook.json` is 39,992
tokens already stored as 24-pocket integer vectors. So 24 pockets holding data
is established practice here.

Mapping: 24 = 6 angle sectors (θ mod π/2) × 4 radial shells of |centre − centre|
in units of L/2. 24 counts → normalise → threshold at the mean → 24-bit word →
snap to nearest extended Golay codeword (4096 words, min nonzero weight 8,
verified).

Measured: **50 distinct addresses** over 1000 rows, entropy **2.811 bits** of 12;
snap distance median 4; **MI(address; beats grid) = 0.1930** against a
permutation null of 0.0431 (so ~0.15 bits of real signal); MI with residue r =
0.9198 and with band k = 0.5626 — the address mostly encodes **n**. Pocket
profile is skewed: **82% of squares in sector 0**, one pocket 46%, emptiest
0.07%. Stability: every distinct address is **≥ 8 bits away** (the code's own
minimum distance), so a perturbation raising E by 2e-3 and one raising it by
4.6e-1 are *equally* far. No metric survives the snap.

Diagnosis: two structural failures — the address describes the puzzle rather
than the packing, and snapping to the code annihilates gradation. Same failure
shape as `LeechResidue.lean`'s warning and as the CRAM contact word.

What is not refuted: Λ₂₄ as the **quantiser** for a per-square feature (G =
0.0658 vs cubic 0.0833, 21% less error at equal density; covering 4× better).
Keep real-valued counts, take the nearest lattice point, use the residual
vector. Falsifier: residual norm must correlate with ΔE; residual direction must
repeat across PL-15's bistable seeds. That is PL-26, not yet run.

---

# Part 8 — snapping is a measurement (run 44)

Pushed the Leech thread on the reframe that snapping is a measurement, not an
action. Instrument `scripts/leech_measure.py`, controls
`scripts/leech_snap_controls.py`; `10-LEECH-ADDRESS.md` §8.

Three corrections to my own part 7:

* The hard distance is **graded**: `{1:5, 2:27, 3:296, 4:672}`, variance 0.316.
  Part 7 quoted "median 4, max 4" and implied it was constant. It is not, and
  MI(hard d; beats) = 0.0831.
* My first soft statistic was degenerate: uncentred correlation scored exactly
  1.0000 for all 1000 rows because the pocket support fits inside a weight-16/24
  codeword. Centring fixes it (995 distinct values, sd 0.061).
* "No metric left" is true of codeword Hamming only; distance-to-code and the
  soft profile are graded.

The reframe pays: the **decisiveness gap** ρ₁−ρ₂ has MI **0.2955** with beating
grid against a permutation null of 0.0019–0.0046. Controls: I(band; beats) =
0.0163; I(residue; beats) = 0.4438; I(gap; beats | band) = **0.3619** (rises);
I(gap; beats | residue) = **0.1356**. Within-residue permutation, 300 reps:
null 0.0549 ± 0.0082, max 0.0785, **z = +9.87** → **≈0.081 bits genuine**, about
9% of H(beats) = 0.881. First 24-pocket statistic in the project to survive
controls.

Negative recorded: it does **not** track energy — Spearman(Δgap, ΔE) = −0.061 /
−0.132 / +0.108 for n = 60/240/961, pooled −0.124. Static property, not a local
gauge. PL-26's falsifier fails in that direction.

Open: the sign of the effect (PL-28), and whether the gap ranks rows inside a
base-less residue column well enough to guide PL-21's base search.

---

# Part 9 — the prior is a rotation detector (run 45), and 39 columns not 23

Continued PL-28 logically. Instrument `scripts/leech_prior.py`, control
`scripts/leech_rotation_control.py`; `10-LEECH-ADDRESS.md` §9-11.

Sign first: beating rows are more decisive (mean gap 0.03155 vs 0.01772),
AUC 0.7540, permutation null 0.4999 +- 0.0189 (z = +13.48),
per-column median AUC 0.716 over 22 columns with both classes.

Then the mechanism: grid rows have gap median 0.0000, 63.4% exactly
zero; beating rows median 0.02287, 10/300 zero. Gap 0 means the
pocket vector sits ON a codeword, which is exactly what an axis-aligned grid
does. The statistic measures rotation.

Controls: AUC(rotation -> beats) = 0.8193 vs AUC(gap) 0.7540;
AUC(gap) among rotated rows only 0.3495 (below chance);
MI(rotation;beats) 0.3312, MI(gap;beats) 0.2276,
MI(gap;beats | rotation) **0.0304**, MI(rotation;beats | gap)
0.1340. 87% of the gap's information is rotation, and a one-bit
flag read off the angles explains it better. Among rotated beating rows
Spearman(gap, delta) = +0.166 -- more decisive means a
WORSE packing, so no value prior either. Attack list from PL-28 retracted.

Correction to part 8: the "first 24-pocket statistic to survive controls" claim
was tested against the residue control only; it does not survive the rotation
control. Retracted.

Separate correction, measured from the delivered table rather than from the
cascade model: **21 residues contain a beating row and 39 do not** (r = 0, 22,
24-60). Part 6's "37 of 60 residues with a base" came from the planner's model,
not the delivered packings. PL-21's population is therefore 39 columns, not 23,
and the ceiling is larger than the lever table in 09-CASCADE.md §5 showed.

---

# Part 10 — the area ceiling, and why PL-21 is the wrong plan (run 46)

Instrument `scripts/area_ceiling.py`; record `11-AREA-CEILING.md`.

Before searching the 39 base-less columns, computed the bound that decides
whether the search can pay: gain at a row is at most 10/sqrt(n) - 10/(k+1)
(zero-waste limit, never attained), exact in 30-digit Decimal.

Numbers: total headroom over all 1000 rows 24.7311; ceiling over the
700 grid rows 15.776054. Split: base-less columns 429 rows,
ceiling **1.759753** (0.0041/row); columns with a base
271 rows, ceiling **14.016300** (0.0517/row). So PL-21 could
win at most 1.7598 over 429 rows of search -- 13x worse per row than the
columns already open. PL-30 made that plan look bigger; it was never good.
**PL-21 deprioritised.**

Where the ceiling is: small r. r=1 5.8677, r=2
3.8517, r=3 2.4747, decaying from there; all
columns that already beat (30/31, 28/31, 25/31 rows).

Exchange rate: since a column's slack is set by its base and inherited
(09-CASCADE §2), dScore/dslack = Sum 10/L^2 = **41.6828 per unit** over the 21
based columns, i.e. **0.4168 per 0.01**. r=1 alone 6.3277. Gaining 1.0
needs slack down ~0.02 everywhere -- construction work, an order of magnitude
more than the whole delta range measured so far (best 0.5208).

Next: PL-32, tighten the r=1 base and let the cascade carry it to 31 rows.

---

# Part 11 — two instrument errors, and what they cost (run 47)

Building the area ceiling exposed two bugs in my own instruments. Both are mine,
both are in parts 7-10, and both are now fixed and re-measured.

Error 1: score scale. I scored rows as 10/L. The repository scores
sum(L/sqrt(n) - 1): my formula gave 593.279 where the delivered table scores
22.218056945.

Error 2: inflated bbox. Every Leech instrument computed
L = max(x) + max(ex) - (min(x) - min(ex)) instead of the per-square
max(x_i + ex_i) - min(x_i - ex_i). Inflating L reclassified 253 of the 553
beating rows as grid; the instruments saw 300 beats where the table has 553.
Every `beats` label used since part 7 came from that.

Re-measured with scripts/leech_audit_fix.py (reproduces the delivered table to
1.3e-10, 553 beats, 20 rows cross-checked against packlib.verify):

  AUC(rotation -> beats) 1.0000; MI(rot;beats) 0.9919;
  every beating row rotated, every grid row unrotated.
  AUC(gap -> beats) 0.9861; MI(gapQ;beats) 0.8687;
  MI(gap;beats | rotation) = 0.0000 -- exactly nothing.

Withdrawn in full: part 8's "first 24-pocket statistic to survive controls,
~0.081 bits genuine". It was an artefact of the mislabelled target. Withdrawn:
PL-30's "39 base-less columns" -- the corrected target gives 37 residues with a
beating row and 24 without, the record's original figure. The 15 phantom columns
were columns whose beating rows the bug hid.

Area ceiling, rebuilt on the correct scale: grid rows' zero-waste ceiling
7.195366 (which is exactly the grid part of the score), beating rows'
headroom 15.022691 (the beating part). Base-less columns would win
0.8068 over 177 rows (0.0046/row); open columns' grid rows
6.3886 over 270 (0.0237/row). PL-21 stays deprioritised, now on
the right number.

The actionable figure: slack is worth 52.3830 per unit over the open
columns, so 0.01 of slack = 0.5238 score and 0.05 = 2.6192 --
more than four times the entire unopened ceiling. Next: PL-32, tighten r=1
(31 rows, 3.6453 per unit slack).

---

# Part 12 — the guard, and PL-32 (run 48)

## The guard

`scripts/sqscore.py` is now the only scorer: `extent` (per-square box), `grid`
(exact isqrt), `row_score = L/sqrt(n)-1`, `row_gain`, `marginal = 1/sqrt(n)`, and
`guard()` which recomputes submission.csv and RAISES unless it is exactly
22.218056945 with 553 beats over 1000 rows (447 grid). Every instrument imports
it and calls it at start-up: leech_address, leech_measure, leech_prior,
leech_snap_controls, leech_rotation_control, area_ceiling, cascade_predict,
leech_audit_fix. A grep for the old private computations (ex = 0.5, max(ex),
10 / dsqrt, 10.0 / L, ceil(sqrt(n)) - 1e-12) returns nothing.

Re-run once each, all agreeing: leech_address MI 0.5856 (H 0.992, null 0.0466);
leech_measure AUC 0.9861; leech_prior per-column AUC median 1.000 over 37
columns; leech_rotation_control AUC(rot->beats) 1.0000, MI(rot;beats) 0.9919,
MI(gap;beats|rot) 0.0000; leech_snap_controls I(gap;beats|res) 0.5740, z = +47.50;
area_ceiling score 22.218056945 (553/447) -- it had still been printing 27.979
and 300 beats until the last fix, which is exactly the bug class the guard exists
for.

## PL-32: no base found

Target: slack below the column's best 0.520815. relax+coordinate_polish from the
delivered state returns it UNCHANGED (k=8: 8.535534 in, 8.535534 out, target
8.5155) -- the delivered packings are fixed points of the project's own
relaxation. sa_push.anneal from compressed grid seeds fails the gate on every
attempt (overlaps at the target side). cram_relax.project was dropped from the
chain because its docstring records it as measured to hurt; soft_relax.hop_search
cannot be imported at all -- cent_discovery is imported by boundary_demo,
boundary_scan and fine_probe but does not exist in this tree.

No base found; nothing claimed. Not a proof of impossibility: a failed search
with the tooling that exists.

## The carrier, validated

Carried from every existing base, every band gated by packlib:
n=5 slack 0.707107 -> 29 bands, 0 failures, 0 improved, dscore +0.000000000
n=65 slack 0.535534 -> 23 bands, 0 failures, 0 improved, dscore +0.000000000
n=626 slack 0.520815 -> 6 bands, 0 failures, 1 improved, dscore -0.000000000 (1e-9)

Two defects found and fixed while building it: the delivered states are not
corner-anchored (the first strips cut the old packing and every band from n=5 and
n=65 was rejected), and successive bands touch the previous strip exactly, which
packlib rejects at tol=0 (the gap now accumulates 1e-9 off the real top).

Measured score change from carrying every existing base to the end of its column:
0.000000000. The table is not chain-limited; it beats its own chains.

---

# Part 13 — cent_discovery was never in git (run 49)

Searched the tree and the whole history: cent_discovery.py does not exist and
never did. git log --all -- "*cent_discovery*" returns nothing; grepping every
commit finds only references, in REPRODUCE.md, boundary_demo, boundary_scan,
fine_probe, root_probe, run19_docs, soft_relax and two JSON ledgers (commits
db74f9e and 41489c7). hop_search also needs engine_variants (finalize_gate,
lattice_seed, transduce) and oracle_basin (settle_to, ramp_settle) -- both
equally absent, so the whole soft-relaxation engine was broken.

Rebuilt all three to the call sites' contract, each marked RECONSTRUCTION:
cent_discovery.rsa_seed/attempt, oracle_basin.settle_to/ramp_settle,
engine_variants.finalize_gate/lattice_seed/transduce (finalize_gate wraps
packlib.verify so the gate stays the only authority).

Imports after the work: soft_relax OK, boundary_demo OK, boundary_scan OK,
p1p_insert31 OK, p2_seed_polish OK; fine_probe still fails on a missing
lm_exactify; root_probe and lattice_scan still fail on a missing pressure_settle.
Those two modules are outside what hop_search needs, so they are recorded, not
reconstructed.

Validation: settle_to is sound -- from the delivered n=5 record it reaches E=0,
gate ok, L=2.707107 (the documented control). rsa_seed is feasible at n=5
(pen -8.3e-3) and n=11 (-1.4e-2) but still ~5e-2 overlapping at n=65/626.
hop_search is NOT validated: at n=5, 2.7081 it returns 0/8 hard hops where the
docstring records the control as passing. Cause: from a random seed settle_to
plateaus at E=2.8e-2 and L-BFGS-B exits (250/1000/4000 iterations give the same
state, L=2.902716), so cold settle sticks in a local minimum.

Two of my own defects found and fixed: SAT used hw instead of half-side 0.5 (up
to 41% over-conservative), and the seed fallback ignored squares already placed
(pen 0.46 at n=5, 1.03 at n=65).

PL-32 with hop_search: started, NOT complete. k=8 (78s) and k=9 (97s) both 0/1
hard hops, no gated find; k=10..25 skipped on the time budget. At 78-97s per seed
an 18-value sweep does not fit here, and the engine is unvalidated anyway. No base
below 0.520815 found; the search is explicitly incomplete.

area_ceiling.py deleted; leech_audit_fix is the only scorer of that quantity and
prints the same numbers: base-less 0.806788 over 177 rows, open columns 6.388578
over 270 rows, total grid ceiling 7.195366, beating-row headroom 15.022691.

---

# Part 14 — penalty vectorised (exact), settle improved, control still fails (run 50)

Vectorisation: sa_push.total_pen was a Python loop over n calls to pair_pen_k.
Now one matrix product via pair_pen_matrix (delegating to cram_relax.margin_matrix).
Verified identical: pair part 48.360341919152 old vs 48.360341919152 new on a
random n=40 state. total_pen n=40 = 0.15 ms. hop_search at n=5: 67s -> 17s, hard
hops 0/8 -> 1/4.

Two of my own defects caught by the check: a hand-rolled matrix that disagreed
(48.36 vs 27.90), replaced by delegation; and a triu rewrite that halved the
penalty (the old loop summed ordered pairs) -- ordered scale restored.

Cold settle: settle_to no longer uses L-BFGS-B on the Python penalty (which
exited at E=2.8e-2 from every seed). It now uses cram_relax.relax +
coordinate_polish and reports cram_relax.energy.

Control still FAILS: n=5 target 2.7081, best arrangement 3.080452 (known
2.7071068); shrink-and-repair from three seeds gives L 2.870-2.906, E ~4e-2.
Diagnosis: the optimum is the 4-around-1 pattern with a 45-degree centre square;
single-body descent and SA at a fixed infeasible side cannot restructure a random
seed into it. A rotation-aware collective move (or a family seed) is what is
missing.

Therefore the k=8..25 sweep was NOT run: with the control failing its numbers
would be meaningless. Nothing claimed about the geometry this round.
