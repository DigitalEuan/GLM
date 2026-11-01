# Review: `hypothesis_engine_v16.py`, `glm_wheel.py`, `glm_wheel.json` (Round 44)

## 1. Running them

* `hypothesis_engine_v16.py` imports `hypothesis_engine_v15`, which is not in the upload. It also
  imports `glm_guards` and `tax_guards`, which live in `rule30_round42/`. As uploaded, v16 does
  not run, so its own verdicts could not be reproduced.
* `glm_wheel.py` needs matplotlib and numpy, and writes to a hard-coded
  `/home/z/my-project/download`.
* The **wheel content** is in `glm_wheel.json` and was used directly: 40 statements in the rings
  *doesn't know*, *thinks is true*, *thinks is needed*, plus the verifications and the language
  wheel.

To make the package portable, ship v15 with v16 (or fold the needed functions into v16), and make
the output directory a command-line argument.

## 2. The layer-aware guards

v16 attaches the labels "mod 2 / 4 / 8 / 144 / 256" to five **domain scales** (D < 10, 50, 200,
2000, all) and five **sample sizes** (N ≤ 10, 50, 200, 2000, all). No residue mod 144 or 256 is
ever computed. The moduli are names for cut-offs and carry no arithmetic meaning. The corrected
escalation document (`RequestProject/GLM/Escalation/GLM_Escalation_Boundaries_Exploration_CORRECTED.md` in the Lean project, §3 and §5)
shows that the modulus cascade itself does not hold together:

* 144 refines 8;
* 256 does not refine 144;
* 8, 144 and 256 give the same Leech syndrome.

Recommendation: call these levels *scale 1–5*.

The aggregation also points the wrong way. `explained_away_guard_layered` declares a claim
**explained away overall if it is explained at any scale**. Small samples are the easiest to
"explain": at D < 10 there are almost no events. So the rule makes the guard stricter exactly
where the evidence is weakest. A defensible rule is that the verdict is the verdict at the
**largest** scale, with the smaller scales reported as a trend.

## 3. What the wheel says, checked

Each entry of `glm_wheel.json` was given a ground truth from a source fixed **before** any run.
The sources are a Lean theorem, an exact computation, or "open". They are listed in the `TRUTH`
table of `needs_rule30.py`. Highlights:

| Entry | Wheel says | Truth | Source |
|---|---|---|---|
| H19 linear complexity of the centre column: \|2L(n) − n\| ≤ 10 for all n | thinks true | **false**: at n = 11101, 2L − n = 11 | Lean certificate `wheel_H19_false` |
| ledger C160 "2L − n within 6 up to 2·10⁴" | (earlier ledger) | **false**: at n = 19521, 2L − n = 13 | Lean certificate `ledger_C160_overstated` |
| H16 no eventual period p ≤ 64 with preperiod ≤ 10000 | thinks true | true | Lean `wheel_H16_true` |
| H36 centre column less uniform than Thue–Morse | thinks true | **inverted**: 2-bit gap 185 < 10000, so it is *more* uniform | exact |
| H39 wobble limit independent of the seed | thinks true | **false** (owner's own verification) | exact |
| H17 \|D(N)\| ≤ 3√N | thinks true | open; holds to N = 10⁶ (max ratio 2.651 at N = 24979) | exact |
| H30 next jump estimate | thinks true | open; conflicts with the Round 40 run-up prediction 2,107,985,255 | ledger |
| L-H01, L-H04, L-H06 (language wheel) | "verified concepts" | **false**: period 16 at D = 400; whites 399, 53207, …; period 32 at D = 87867 | Lean ledger |

So the language wheel contains three statements that the Lean ledger already refutes. A
"verified" vocabulary must be checked against the ledger before it is reused.

## 4. The needs-wheel protocol (new this round)

`glm_needs.py` holds the protocol, and Lean `NeedsWheel.lean` proves what a wheel can and cannot do.

1. The engine states, for each task, what it **needs**: a range, a tool, a test, a fact, or a
   checked implication.
2. Provisions are registered on the wheel with the needs they serve and their trust level.
3. The answer comes from the first provision that speaks; otherwise the engine's base answer is
   passed through an honesty guard.
4. Results are scored against a ground truth fixed beforehand: right / wrong / overclaim
   (asserting an open question) / abstain.

What the Lean file proves:

* adding **sound** provisions never loses a right answer and never creates a wrong one;
* the effect of a provision is confined to the needs it serves;
* the order of sound provisions does not matter;
* a single unsound provision can hurt.

So the protocol is safe exactly when the provisions are themselves checked. Also,
`finite_data_never_forces_infinitely_many` shows that no finite amount of data soundly answers
"infinitely many?". Such needs must be met by a proof or left open.

## 5. Results (`python3 run_round44.py`, outputs in `out/`)

**Rule 30 (40 statements).**

| Condition | right | wrong | overclaim | abstain |
|---|---|---|---|---|
| base | 8 | 12 | 15 | 5 |
| guard only | 18 | 0 | 0 | 22 |
| requested provisions | 28 | 0 | 12 | 0 |
| requested + guard | 40 | 0 | 0 | 0 |

Leave-one-out shows which provisions carry the gain:

* without LEDGER: 30 right, 10 abstain;
* without IMPLICATIONS: 37 right;
* without the centre or seed ranges: 39 right;
* without the other three: no change.

*Caveat.* The ledger provision and the ground truth draw on the same Lean results. The 40/40
therefore measures that the engine **routes each question to the right checked source** and stops
asserting open questions. It is not independent discovery. All seven provisions were requested,
so the random same-size control coincides with the requested set; leave-one-out replaces it.

**Synthetic ARC (held-out families, 120 puzzles).**

| Condition | right | wrong | refused |
|---|---|---|---|
| base | 19 | 0 | 101 |
| requested from development needs (7 provisions) | 72 | 0 | 48 |
| random 7 provisions | 55–73 (mean 64.4) | 0–2 | — |
| all 15 provisions | 106 | 0 | 14 |
| on-demand (per-puzzle stated needs) | 108 | 0 | 12 |

On held-out refusals, the stated need was served and solved the puzzle in 89 of 89 cases where a
need was stated. In 12 cases the solver said "unknown" rather than guess.

**Real ARC (53 test grids from the 50 tasks in `glm_repo.zip`).** The base solves 0 and the
on-demand wheel solves 2, with no wrong answers. The most frequent stated need was "unknown"
(37), then object-wise recolouring (12). Adding a feature-based recolouring provision (V2) did not
add a solve. **The needs wheel does not yet help on real ARC.** Its honest output is that the
primitives real ARC needs are not on the wheel, and that most refusals cannot even be described
by the present need vocabulary.

## 6. Recommendations for the GLM

1. Keep the needs → wheel → measured-effect loop. It is safe for checked provisions (Lean
   `answer_right_of_right`, `answer_wrong_of_wrong`) and measurable (`answer_local`).
2. Only put **checked** provisions on the wheel (Lean `unsound_can_hurt`).
3. Score with *overclaim* as a separate category. Most of the base engine's errors on Rule 30 were
   open questions asserted as true.
4. Always run a control: random provisions of the same size, or leave-one-out.
5. Treat "unknown" needs as the main output on real ARC. The need vocabulary is the bottleneck.
