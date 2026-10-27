# Round 9: the cellular-automaton carrier ("the Wheel") for the GLM

The formal results of this round are in the Lean package:
`RequestProject/GLM/Rule30/WholeCone.lean` and `RequestProject/GLM/Rule30/ElementaryCA.lean`
(see "Round 9" in the package README). This folder holds the GLM side. Nothing in it is a proof.
Each value it reports names the Lean theorem it comes from, or is marked `EMP` (exact
computation, not a theorem) or `OPEN`.

## 1. Your `lattice_geometry.py`

It works. It needs one more module that is not in `glm_repo.zip`: `reports/lattice_geometry.py`
imports `reasoning/lattice_completion.py`, and that file imports `reasoning/frozen_path.py` when it
loads. `frozen_path_standin.py` is a stand-in for that one file. Its single function,
`frozen_path_report`, refuses with a message naming the missing file. Replace it with your real
module.

With your files and that stand-in, the full session imports. The lattice reports answer from your
code: `report facets`, `report lattices`, `report subalgebra`, `report fusion` (see
`lattice_geometry_check_output.txt`). The Round 8 stand-in `rule30_round8/lattice_geometry_standin.py`
is no longer needed.

## 2. The new enabled domain `automata` (the Wheel)

| File | Goes to | What it is |
|---|---|---|
| `glm_overlay/glm_universal/data_objects/automata.py` | `glm_universal/data_objects/` | the register: exact engine and carriers |
| `glm_overlay/glm_universal/runtime/wheel_report.py` | `glm_universal/runtime/` | `describe` / `report wheel` answers for it |
| `glm_overlay/glm_universal/runtime/session.py` | `glm_universal/runtime/` | your `session.py` with the domain wired in |
| `glm_overlay/glm_universal/runtime/parser.py` | `glm_universal/runtime/` | your `parser.py` with `automata` in `DOMAIN_PRIORITY` |
| `session_automata.patch`, `parser_automata.patch` | | exactly what changed in your two files (unified diffs) |
| `test_automata.py` | | plain-assert self-test; each check names the Lean theorem it mirrors |
| `glm_wheel_probe.py`, `glm_wheel_probe_output.txt` | | 26 queries and the GLM's full three-column answers |

Setup, from a GLM checkout (the directory holding `GLM.py`):

```
cp parser.py session.py tct_engine.py            glm_universal/runtime/
cp __init__.py lattice_geometry.py               glm_universal/runtime/reports/
cp rule30_round9/frozen_path_standin.py          glm_universal/reasoning/frozen_path.py
cp -r rule30_round9/glm_overlay/glm_universal/.  glm_universal/
PYTHONPATH=. python3 rule30_round9/test_automata.py
PYTHONPATH=. python3 rule30_round9/glm_wheel_probe.py
```

The changes to `session.py` are small and marked `Round 9`. They add `"automata"` to `DOMAINS`,
a loader, `"automata": None` in `DEFAULT_SUBSPACE`, and the subject `wheel` in
`REPORT_SUBJECTS`. They also make three routing changes:
* `describe` sends automata carriers to `wheel_report.describe`;
* `report wheel` (also `wheels`, `automata`, `eca`) goes to `wheel_report.report_wheel`;
* in `compare` and `real`, a register name is replaced by its exact value before the
  exact-real grammar reads the expression. A step labelled `carriers` records the substitution with
  its evidence class and Lean theorem.
Nothing else in the session changes, and the other domains behave as before (for example,
`describe chlorine` gives the same answer). Your test suite was not run here because `pytest` is
not installed in this environment. Running it is the first thing to do on your side.

### What the register holds

* **256 wheels**, named by their truth table, so the rule is carried in the name.
  `wheel_00011110` is the local map `f(L,C,R) = bit(4L+2C+R) of 0b00011110 = L + C + R + C·R` over
  GF(2). The alias is `wheel_30`. Each wheel's 24-coordinate carrier holds:
  * the 8 output bits;
  * the 8 ANF coefficients;
  * left/right permutivity and affinity flags;
  * the mirror number, the complement number and the class representative;
  * the local degree and the number itself.
* **`wheel_family`**: 88 classes and 16 left-permutive wheels (`card_equivalence_classes`,
  `card_leftPermutive`).
* **Run carriers** for wheel `00011110` from the impulse row `δ₀`, read at column 0:

| Carrier (aliases) | Value | Evidence |
|---|---|---|
| `r30_wobble_D_N`, N = 10, 100, 1000, 10000 | `D(N) = 2·#ones − N`: 4, 4, −38, 64 | EMP (computed when the register loads) |
| `r30_wobble_D_1000000` | 1536 | CERT, `wobble_1e6` |
| `r30_delta_sigma_accumulator` | none | OPEN; the definition, the proved facts and the arrow `−sign D(N)` |
| `r30_anf_degree_n`, n = 1..20 | `2n − 1` (2 for n = 1) | FORMAL, `center_anfDegree_eq` |
| `r30_essential_inputs_n` = `r30_light_cone_dependency_n`, n = 0..20 | `2n + 1` | FORMAL, `wholeConeDependence_holds` (**new this round**) |
| `r30_cone_separation_derivative` | 1 | FORMAL, `evolve_flip_left_edge`; family form `ecaEvolve_flip_left_edge` |
| `r30_lag_predictor` = `r30_fs_observer_error_rate` | least lag error rate on `t < 10⁴`, `p ≤ 16`: `4940/9989` at `p = 11` | EMP; P1 ⟺ every finite-state observer errs infinitely often (FORMAL) |
| `r30_question_aperiodicity` / `_balance` / `_cost` | none | OPEN; exact statement plus the proved partial results |
| `wheel_90_impulse_centre` | column 0 = 1,0,0,… | FORMAL; questions 1 and 2 answer NO for wheel 90 |

`describe <carrier>` gives five or six steps:
1. the carrier and its exact statement;
2. its coordinates;
3. its evidence class and Lean theorem;
4. an **independent recomputation** where one is finite: the run is evolved again, and the ANF
   and essential inputs are tabulated over all `2^(2n+1)` rows for `n ≤ 8`;
5. for `D(N)`, the observer's arrow;
6. the **boundary**: what the carrier does not establish.

## 3. Speaking to the GLM in its own terms

You were right that the GLM refuses "Rule 30" because no register holds the object. That is still
true for plain English: `describe rule 30` is refused, and the refusal now suggests `wheel_30`.
The object has to arrive as a carrier. These query forms work (all are in
`glm_wheel_probe_output.txt`):

```
report wheel
describe wheel_00011110
describe r30_wobble_D_1000000
is r30_wobble_D_1000000 greater than 0
real value r30_wobble_D_1000000 / 1000000
describe r30_anf_degree_7
is r30_anf_degree_10 greater than 18
describe r30_light_cone_dependency_10
describe r30_cone_separation_derivative
describe r30_lag_predictor
describe r30_question_balance
```

Two of Qwen's eight query forms are not in the GLM's grammar, for any values, not only these:
* `compare A to B` and `compare A greater than B`: the parser reads one value. Use
  `compare A and B` or `is A greater than B`.
* `derive A from B`: `derive` expects `<coordinate> of <object>`.
These forms are refused exactly as they would be for `sqrt(2)`. The parser grammar was not
changed.

`is r30_anf_degree_10 equal to 19` gives "not distinguished … does not claim equality". That is the
GLM's own rule for `compare`: equality of two processes is never asserted. The degree is still
certified, by the Lean theorem shown in `describe r30_anf_degree_10`.

## 4. What the GLM does and does not certify (audit of Qwen's predicted outputs)

* **Matches.** `D(10⁶) = 1536`, and "separated at a finite dyadic level" for
  `D(10⁶) > 0` (the GLM separates it at `2^-8`).
* **Over-claims; the GLM does not produce them.**
  * "proving that the sequence is a fair-coin Delta-Sigma process";
  * "Regime: Random-Walk Wobble … the accumulator grows as `O(√N)`";
  * "the spatial asymmetry that prevents the Wheel from locking into a periodic attractor";
  * "formally certifies that the algorithmic complexity cannot be compressed below the full
    light-cone width".

  A finite value or a map-level theorem cannot carry any of these (Lean:
  `no_finite_certificate_problem1/2`, `map_properties_cannot_decide_periodicity`,
  `wholeCone_compatible_with_periodicity`). The register therefore prints a **boundary** step
  instead.
* **Misattributed number.** `4968/9964` is not a lag-predictor error rate. It is the number of
  times `n < 10⁴` at which the column follows the wobble arrow, out of the times the arrow is
  non-zero (`arrow_stats_10000`, `Perspective.lean`). The lag-predictor rates are in
  `r30_lag_predictor`.

## 5. Where the three questions stand

All three remain **open**. Proved this round:
* the whole light cone is essential, with at least `t` gates, for every `t` (Track C, map level);
* the family form of the questions and their symmetries;
* wheels 0, 90 and 204 settled.

The precise remaining targets are in the package README ("Where the prize problems stand after
Round 9"). A proof must use the impulse row itself: every fact about the map from all rows also
holds for rows whose centre column is periodic.
