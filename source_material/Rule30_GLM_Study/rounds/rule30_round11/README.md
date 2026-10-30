# Round 11: the seed's right edge, the off-centre observer, and the claim checker

**Where the prize stands.** The three Rule 30 problems are still open. This round adds proved
results around them. None of these results decides Problem 1, 2 or 3 for the centre column.

The formal results are in the Lean package (`RequestProject/GLM/Rule30/RightDiagonalBalance.lean`
and `ChiralLeak.lean`; see "Round 11" in the package README). This folder holds the GLM side,
which is Python, not proofs. Each value names its Lean theorem, or is marked `EMP` (an exact
computation, not a theorem) or `OPEN`.

## 1. How much of the GLM now runs

Seven of the files you attached fill modules that were missing: `batch_machine`, `llvq`,
`nearest_address`, `semantic_plan`, `speak`, `stepwise` and `timed_question`. Three others were
already in the archive, byte for byte: `lorentzian_evidence`, `word_address` and `harness`. Your
`harness.py` is `capabilities/harness.py`. It is **not** `evaluation/harness.py`, which is still
missing.

I added four small stand-ins (in `standins/`, each labelled in its docstring). None of them
supplies an answer:

| Stand-in | Why it is needed | What it does |
|---|---|---|
| `evaluation_harness_standin.py` → `evaluation/harness.py` | `evaluation/__init__.py` imports it, and *every* `evaluation.*` import runs that `__init__`, so without it `stepwise`, `speak` and `GLM.py --ask` cannot even import | defines the five imported names; every scoring call raises `NotImplementedError` |
| `respell_standin.py`, `sinter_standin.py` | `GLM.py -q` imports both on every question | respelling switched off (`enabled() → False`): a refused question stays refused |
| `colour_induction_standin.py` | `tool induce` and `tool arc` import it first | only the gate: binary one-shape tasks go to your `pipeline_kit` unchanged; colour tasks and `tool arc` refuse |

With these in place, **`GLM.py -q`, `GLM.py --ask`, `tool induce` (your pipeline kit plus the wheel
family) and the toolbox all run**, and `--verify-tct` replays column 3. Still missing, by static
scan (`../rule30_round10/find_missing_modules.py`): `runtime/evidence` (blocks `--result`),
`reasoning/planner_ladder`, `combiner`, `carried_read`, `budget_guard_frozen`,
`frame_plane_study`, `adversarial_dialogue_study`, `nearest_address_study`,
`nearest_question_study`, and the packages `glm_universal.tools` and `glm_universal.knowledge`
(the latter has files but no `__init__.py`). That is 11 in all. Your test suite was not run,
because `pytest` is not installed here.

Two bugs from Rounds 9 and 10 surfaced once `GLM.py -q` ran, and both are fixed:
* `report wheel …` stopped with `render_script: unknown template`. The wheel report templates are
  now registered.
* `compare` and `real` on automata carriers failed the column-3 replay (`VERIFIED False`). The
  replay now repeats the carrier substitution itself.

All of these now give `VERIFIED True`.

**Setup** (from the directory holding `GLM.py`; tested from a fresh unzip of `glm_repo.zip`):
```
STUDY=/path/to/this/study sh $STUDY/rule30_round11/setup_round11.sh   # ends "round 11: all checks pass"
PYTHONPATH=. python3 rule30_round11/glm_round11_probe.py                # = glm_round11_probe_output.txt
PYTHONPATH=. python3 rule30_round11/r11_benchmark.py                    # = r11_benchmark_output.txt
```

## 2. Track A — the seed's right edge as a carrier

| Carrier | Value / statement | Evidence |
|---|---|---|
| `r30_seed_right_edge_zero` | `rdiag D 0 = [D = 0]`, diagonals `D < 0` white, `rdiag D (t+1) = rdiag D t + (rdiag(D−1) t ∨ rdiag(D−2) t)` | FORMAL |
| `r30_rdiag_D`, `D = 0..39` | least period, black cells per period, anti-periodic?, frequency | EMP (D = 5, 7: FORMAL) |
| `r30_rdiag_balanced` | infinitely many right diagonals are exactly balanced with bounded wobble | FORMAL |

**What the right edge forces (new theorems):**
* **Periodic or anti-periodic.** Every diagonal is either periodic or *anti-periodic* with the
  period of its input: `rdiag D (t+Q) = ¬ rdiag D t` (`rdiag_periodic_or_antiPeriodic`).
* **Anti-periodic means bounded wobble.** An anti-periodic diagonal has `|D(N)| ≤ Q` for **every**
  `N` and frequency exactly 1/2 (`wobble_antiPeriodic_bound`). This is your *bounded* (ideal
  delta-sigma) regime, and it occurs in the seed pattern.
* **Infinitely many.** Infinitely many diagonals are anti-periodic
  (`infinitely_many_balanced_rdiag`).
* **But not all.** Diagonal 5 has frequency 3/8 (`rdiag_five_not_half`). Diagonal 7 is
  anti-periodic with `|D(N)| ≤ 16` (`rdiag_seven_bounded`).
* To `D = 39` (EMP, `r11_diagonals.c`): 17 diagonals are anti-periodic. Diagonals 8, 10, 17 and 18
  are balanced without being anti-periodic. The rest are unbalanced.

**On the feedback's track A goal** (the right-edge zero boundary forces `D(N) = o(N)`): this is
**false as stated.** A white right half alone forces nothing at the centre.
`exists_row_with_biased_column` (Round 4) builds a right-white row whose centre column has
frequency 1/3. What the right edge *does* force is the diagonal structure above. The centre
column `a(t) = rdiag t t` crosses every diagonal once, so that structure does not reach it.

**The observer riding the right edge.** If the observer moves with the right edge (depth
coordinates), Rule 30 becomes **wheel 86, its mirror image, with the frame moving one cell per
step** (`rdiag_moving_frame`, FORMAL). The stationary wheel family finds no rule in that view.
`wheel_induction.py` now also fits a frame velocity, and from 4 diagonal rows it induces
*(wheel 86, velocity −1)* and predicts the next row correctly. This is the "read position / angle"
of the observer `Y` made exact: a perspective consists of a velocity and an orientation, and the
GLM can infer both from data.

## 3. Track B — the off-centre observer

| Carrier | Content | Evidence |
|---|---|---|
| `r30_wobble_D_N_column_c` | `D_c(N)` for `c = −5..5`, `N = 10², 10³, 10⁴` (computed), `10⁵, 10⁶` (quoted) | EMP (`c=0, N=10⁶`: CERT) |
| `r30_chiral_gap_c_N` | `D_c(N) − D_{−c}(N)`, which also equals wheel 30 minus wheel 86 at column `c` | EMP (identities FORMAL) |
| `r30_chiral_gap_first_c` | first `N` with a non-zero gap: 3, 6, 5, 9, 7 for `c = 1..5` | FORMAL (`chiralGap_first`) |

**Answer to the feedback's question (the rate at which chiral information leaks into the
wobble):**
* It leaks **immediately**: within 9 steps at every column `1..5`.
* It **does not accumulate**. To `N = 10⁶` the gap stays within ±886 … ±2918 (EMP), the size of
  the difference of two random walks, with no drift.

So the off-centre wobble gives no growing chiral signal from which `SeedFSTypical` could be
derived. What *is* proved for observer pairs: of the observers at column 0 and any column `c ≠ 0`,
at least one sees a sequence that is not eventually periodic (`offCentre_pair_problem1`).

## 4. Track C — the parity count

This is already settled, and more than the feedback says. `whiteDiagonalCount n` is odd for
**every** `n ≥ 2`, and `deg a(n)(c) = 2n − 1` for every cell (Round 8:
`whiteDiagonalCount_odd`, `topMonomialConjecture_holds`). The check to `n = 14` / `36` that the
feedback quotes predates that proof. The GF(2) recurrence it asks for is the triangle parity law
`triQ_succ`, and the parity sequence is the constant 1, so there is nothing left to induce. The
carrier is `r30_white_diagonal_parity` (FORMAL). Point 2 above shows `tool induce` on the next
open question: the diagonal view.

## 5. Track D — the reasoning benchmark (`tool claim`)

`reasoning/wheel_claims.py` adds `tool claim <claim>`, reachable through English as well
("Is it true that …", "check the claim: …"). It answers with
**VERDICT / MISSING HYPOTHESIS / WITNESS-REFERENCE / NEXT TEST**:
* **Computed frames** compute the verdict from the register, then name the theorem: column C
  distinguishes wheel R from wheel S; the wobble at column C equals the wobble at column −C; right
  diagonal D is balanced; rows 0..T determine wheel 30.
* **Settled frames** carry a proved theorem or non-implication. This is retrieval with a reason,
  and the output says so.

Your example, *"The center column observer can distinguish wheel 30 from wheel 86"*, gets
`REJECT [FORMAL]`. Missing hypothesis: the centre column is mirror-invariant. Reference:
`centre_column_class`. Next test: column 1 (`column_one_separates_mirror`).

**Score** (`r11_benchmark_output.txt`, 30 claims, each run through `GLM.py -q`):

| Split | Score |
|---|---|
| frame wording | 23/23 |
| held-out rephrasings | 2/5 |
| outside every frame (refusal expected) | 2/2 |

All three held-out misses are **refusals, not wrong answers**. I did not tune the frames to the
held-out items afterwards. The frames and the suite were written by the same hand, so the score
measures correctness inside declared frames, not open-ended reading.

## 6. Corrections to the Round 10 feedback

* The parity count is proved for all `n` (Round 8). It is not merely checked to 14/36.
* The right-edge boundary alone cannot force balance (`exists_row_with_biased_column`).
* "The GLM has fully internalised Rule 30" is too strong. It computes exactly inside declared
  frames and carriers, which these rounds wrote and tied to Lean theorems. Outside them it refuses.
* The wall described in that feedback is real and unchanged. Every new result in this round is
  about the diagonals, about pairs of columns, or about the reasoning machinery, not about the
  centre column's limit.

## Files

| File | What it is |
|---|---|
| `glm_glm_universal/data_objects/automata.py`, `automata_round11.py` | register plus the Round 11 carriers |
| `glm_glm_universal/runtime/wheel_report.py` | `report wheel diagonals / chirality / claims`; column-3 templates; `compare` / `real` replay fix |
| `glm_glm_universal/reasoning/wheel_induction.py` | adds the moving-frame (velocity) family |
| `glm_glm_universal/reasoning/wheel_claims.py` | `tool claim` |
| `toolbox_claim.patch` | registers `tool claim` and its English openings (apply after the Round 10 patch) |
| `standins/` | the four stand-ins above |
| `setup_round11.sh` | the whole setup, from a fresh `glm_repo.zip` |
| `test_round11.py` | plain-assert self-test; each check names its Lean theorem |
| `glm_round11_probe.py`, `glm_round11_probe_output.txt` | 20 `GLM.py -q --verify-tct` queries |
| `make_r11_suite.py`, `r11_reasoning_suite.json`, `r11_benchmark.py`, `r11_benchmark_output.txt` | the claim benchmark |
| `r11_diagonals.c`, `r11_diagonals_output.txt` | right diagonals 0..39 (EMP, exact) |
| `r11_offcentre_wobble.c`, `r11_offcentre_wobble_output.txt` | wobble of columns −5..5 to `10⁶` and the chirality gaps (EMP, exact) |
