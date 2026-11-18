# 33 — The cent-compiler contract, audited, and the T1 branch flip, implemented (Run 70)

Two cards were drafted for the cent compiler: a Target Operation Contract
(`cent-operation/1`, `jamming_branch_escape`) and a Mechanism Card
(`cent-mechanism/1`, `t1-dislocation-glide`). This record checks the figures they
lean on against our ledgers, implements the mechanism they specify, and reports
what it earned. Nothing here changes a row: the delivered total is still
`22.218056945`, 553 beats, and `sqscore.guard()` holds.

## 1. What the cards ask for

The contract is: with the current poses, the tight-pair contact graph and an
algebra of allowed tilt words, find a discrete change `(B', theta')` such that the
LP side falls, `L_next < L_current`. The mechanism is a T1 swap: change *which
axis, and which owner*, separates a tight pair (a SAT disjunction flip), couple it
to an algebraic angle step, then contract with the LP.

That is a real degree of freedom and it is genuinely new here. Run 69 changed
words but always **re-derived** each pair's axis from the trial geometry, and the
run-67 LP takes the delivered `argmin` branch. Choosing the branch *by name* and
rebuilding the constraint system from it is what these cards add.

## 2. The figures checked, and what survived

| card claim | verdict |
|---|---|
| "0.76 % tight pairs" | true **at n = 1000 only**: 3811 / 499500 (`disj_census.json`), 0.76 %. At the rows this mechanism is aimed at the fraction is 28.95 % (n = 20), 20.46 % (n = 30), 16.99 % (n = 18), 16.99 → 9.18 % (n = 39). The M-card invariant "branching restricted to ≤1 % of pairs" is false for every mid-size row. |
| "n = 5 rotational lock, L = 2.7081" | **wrong twice.** `s(5) = 2 + √2/2 = 2.707107`, 0.001 below the quoted value; and it is *proved* (Stromquist). Test `escape_n5_rotational_trap` asks a search to beat a proved optimum, so it cannot be "certified" — it is ill-posed, exactly the trap Run 69 caught at n = 11. |
| "0/8 gated" | real, but it is **run 41's** pressure-push result across four weightings (`notes/run41_NOTES.md`), not a run-64/65 measurement. |
| "run 50: 0/300 vs 25/150" | **unverifiable.** There is no Run 50 entry in `04-RUN-LOG.md`, no `notes/run50_NOTES.md`, and neither ratio appears anywhere in the tree in that sense. The provenance line "runs 50, 64, 67" cites a run this record does not have. |
| `exact_authority: Fraction`, `floats_allowed: false` | **not achievable in this pipeline, as stated.** The contraction is a float HiGHS LP and the certificate is `packlib.verify` at 12 dp with ~2e-9 clearance. Exact arithmetic in this project is the integer Leech layer, not the packing pipeline. The honest semantics are "float LP proposes, the SAT gate at 12 dp certifies". |
| `oracle_gate: packlib.verify(poses_next, L_next) == True` | not the API: `verify` takes a state (and a tolerance) and returns a dict whose `ok` is the verdict; `L` is recomputed from the state, not passed. |
| `tight_pairs` typed `list[tuple[int,int,str]]`, edges "i, j, axis_branch" | fine as a concept; implemented here as an explicit branch map `(i,j) → {u_i, v_i, u_j, v_j}`. |

## 3. The mechanism, implemented

`scripts/t1_glide.py`. For each pair the disjunction is `a ∈ {0:u_i, 1:v_i,
2:u_j, 3:v_j}`; the delivered branch is `argmin` penetration. With a branch frozen
the constraint is linear in the translations:

    sgn · ((c_j + D_j) − (c_i + D_i))·q  ≥  0.5 + ext_q(other square)

The gate is `packlib.verify(tol=0)` on the 12-dp state plus `sqscore.row_gain`.

Cells per row:

* **base** — delivered branches (the run-67 fixed point, as a control);
* **flip1** — one contact edge incident to an extreme achiever, each of the 3
  alternative branches;
* **flip1+word** — that flip plus one endpoint re-worded from the exact alphabet
  `{0, √2−1, 1/2, 1/3, 1/4}` (`t = tan(θ/2)`, so cos and sin are rational);
* **flip2** — two such edges flipped together (capped; see the table).

Side ladders `L0 − eps`, eps ∈ {1e−2, 3e−3, 1e−3, 1e−4, 1e−6}, 5e−10 pad on
every declared axis, every translation free.

## 4. Results

| row | `L0` | contacts / pairs | extreme squares | edges at extreme | cells | LP-feasible | gate-accepted | gains |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 18 | 4.822875657 | 26 / 153 (17.0 %) | 10 | 14 | 1,071 | 0 | 0 | 0 |
| 20 | 5.000000002 | 55 / 190 (28.9 %) | 14 | 44 | 4,572 | 0 | 0 | 0 |
| 30 | 6.000000002 | 89 / 435 (20.5 %) | 18 | 60 | 2,160 | 0 | 0 | 0 |

**7,803 cells, 0 LP-feasible, 0 gated, 0 gains.** Not one flipped branch admits
even a 1e−6 contraction, and the base cell is infeasible at 1e−2 on all three
rows — the same rigidity Run 69 measured (3.1e−8 at n = 18).

## 5. Controls

| control | expectation | outcome |
|---|---|---|
| base path on a loose 2×2 grid at side 2.2 | shrinks and gates | **2.2 → 2.19, gated** |
| forced `u_i` branch on two stacked unit squares at side 2.001 | realizable and gates | **feasible, gate ok, L = 2.001** |
| the same forced branch at side 1.5 | refused | **refused** |
| base cell, delivered branches, at `L0 − 1e−2` on rows 18/20/30 | refused (jammed) | **refused** |

The second control is the one that matters: it shows the branch machinery is not
vacuous — a flip that geometry permits is found and certified, so the 7,803
refusals are refusals of those branches, not a broken instrument. (A first
version of this control asked for 1.99 and failed; two unit squares need exactly
2, so the failure was the control's, and it is recorded here rather than hidden.)

## 6. What the contract earned

* The mechanism is implementable, bounded and auditable, and it has now been run
  exhaustively over its declared cell space at three rows (7,803 cells).
* It is **not** certified anywhere. The card's own `utility.unblock_condition` —
  a verified `L_next < L_current` on one open row — is **not met**.
* Its negative-control test (`no_branch_change`) is satisfied for the right
  reason: the base cell is refused, consistent with run 67.
* Its positive test should be **replaced**: n = 5 is proved optimal, so
  `escape_n5_rotational_trap` can only ever refuse. A live test needs an open row
  and a slack-positive seed.
* The `<=1 %` branching invariant should read "of all pairs" — it is not a claim
  about work: the cell space is set by edges-at-extreme (14 / 44 / 60 here).

## 7. Limits, stated plainly

A branch belongs to a pair and a pair is named by index, so a flip that would
need a *new* contact (a non-contact pair becoming the separating one) is outside
this cell space; refusals are conservative in the branch declaration. The flip
space is also not the whole contact topology: two flips far apart are enumerated
only up to the cap, and the settle pass of run 69 was not repeated here. And n =
20 and n = 30 may be among the 152 proved floors at the grid — our record does
not enumerate which rows those are — so a refusal at a grid row is not evidence
that room existed. No row of the table changed.

## 8. Re-running

    python3 scripts/t1_glide.py --control-only           # base + flip controls
    python3 scripts/t1_glide.py 18 20 --cap2 420         # 1,071 + 4,572 cells
    python3 scripts/t1_glide.py 30 --cap2 120            # 2,160 cells
    python3 scripts/declp.py --selftest                  # 6/6, the shared LP
    python3 scripts/sqscore.py                           # 22.218056945
    python3 scripts/record_guard.py                      # no stale total as current

Ledger: `workspace/push/t1_glide.json` (schema `t1glide/1`), one record per row
plus the controls. It never writes to the submission.
