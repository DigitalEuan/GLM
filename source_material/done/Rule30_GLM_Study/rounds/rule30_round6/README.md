# Rule 30, Round 6: GLM-side experiments (companion to the Lean package)

## Tier 0 — the coarse read

**Question.** With the whole GLM toolset and the stance "randomness is only undiscovered rule
space", how close can this round bring the three Rule 30 prize problems, and what exactly is
still missing?

**Verdict.** The three problems are still open. Every route proposed in feedback #1–#3 has been
either formalised as an exact equivalent of a prize problem or shown in Lean to be insufficient.
The remaining gap is one seed-specific statement per problem. The parity count behind the ANF
degree conjecture is halved by a proved reduction and is machine-checked to `n = 20`.

**Deciding figure.** Lean: P1 ⟺ escape from lag rules ⟺ escape from finite-state rules, and
P2 ⟺ total echo `o(N²)`, all proved with no `sorry` and no added axiom. Observer benchmark: the
best of ~100 frozen predictors scores 0.5058 on 32768 held-out centre bits. That matches the
SHA-256 control (0.5067). Every structured control (period 7, bias 1/3, Champernowne, the two
constructed Rule 30 rows) is captured, at 0.857 to 1.0 by its best predictor.

**Recomputed by.** `python3 r6_observer_benchmark.py`, `python3 r6_golay_census.py`,
`gcc -O3 r6_parity_reduction.c && ./a.out 2 36`, and `lake build RequestProject.GLM.Rule30`
(Lean package).

---

## Files

| File | What it is | Evidence class |
|---|---|---|
| `r6_common.py` | exact Rule 30 generator (same bit-parallel step as Lean `rowStep`), column-inverse row builder, control sequences | — |
| `r6_observer_benchmark.py` → `r6_observer_benchmark.md/.json` | frozen observer benchmark with controls and proof labels | EMP |
| `r6_golay_census.py` → `r6_golay_census.json` | GLM substrate observer: Golay-code coset census of 24-bit blocks | EMP |
| `r6_parity_reduction.c` → `r6_parity_reduction_output.txt` | the proved right-to-left scan, run in C to `n = 36` | EMP (n ≤ 20 also proved in Lean) |
| `r6_parity_bruteforce_check.py` | brute-force cross-check of the C program for `n ≤ 7` | EMP |
| `make_reasoning_suite.py` → `r6_reasoning_suite.json`, `r6_grade.py` | 23 paired claims (9 held out) for the GLM's accept/refuse reasoning, with grader | benchmark |

The GLM substrate is loaded from an unpacked `glm_repo.zip` (set `GLM_OVERLAY` to its ``
directory). The uploaded archive lacks the runtime front-end (`runtime/parser.py`, `session.py`,
`tct_engine.py`), so the `corpus --ask` query interface could not be run. The substrate modules
(`golay_decode`, `golay_paley`, `leech2`, `mog`) import and run directly.

## How the rule-space stance was used

"Randomness is undiscovered rule space" becomes a precise statement in Lean (`RuleSpace.lean`).
A sequence is never random absolutely. It can only **escape** a declared space of rules.

1. Every sequence is captured by some rule (`not_escapes_allRules`). The centre column is captured
   by Rule 30 itself.
2. P1 is escape from the smallest non-trivial space, the lag rules "bit t repeats bit t−p". It is
   provably the same as escape from all finite-state rules.
3. P2 is typicality for the one-rule space {always black}. The Seed Typicality target is typicality
   for all finite-state rules.
4. The wobble arrow (the observer's perspective `Y`) is the first rung above finite state: a
   counter rule.

The benchmark climbs that ladder on real data. Every control sequence is caught on a low rung,
including two Rule 30 rows that look like noise but have periodic or biased centre columns. The
seed's centre column is not caught by any rung tried, and neither is the SHA-256 control. The
correct reading is "no rule found in these spaces at this budget". A proof of escape needs a
seed-specific theorem.

## What would carry it over the line

| Problem | The one missing statement (all equivalences proved in Lean) |
|---|---|
| P1 | For every lag `p ≥ 1`, arbitrarily late mismatches `a(t+p) ≠ a(t)`, derived from the seed's initial data. First target: an infinite family of `p` (e.g. powers of two) |
| P2 | Total echo `Σ_{1≤k<N} echo(N,k) = o(N²)` for the seed, equivalently `D(N) = o(N)` |
| P3 | A lower bound exponential in the input length for one explicit function (beyond current techniques) |
| ANF degree (map-level) | A recurrence or involution showing the `(n−1)`-variable function `reducedPhi n` has an odd number of ones for all `n` |
