# `glm_universal.capabilities` — what the machine can do, and where it stops

**Parent:** [`../README.md`](../README.md) · **Repository root:**
[`../../README.md`](../../README.md)

**Status: implemented (v1.2.0), current.** Four modules, **33 probes**, no
data file, no third-party dependency, and nothing here is float or random.

## Why this is not the test suite

`tests/` asks whether a mechanism still does what it did yesterday. A
**capability probe** asks the other question: *can the machine do this at all,
and if not, exactly where does it stop?* The second answer is the useful one,
because a located boundary is a work item and a passing test is not.

A probe that comes back `breaks` is therefore a **success**: the limit was
found and named. Of the 13 that break today, twelve are theorems and will never
move — the Golay repair radius, the undecidability of equality between two
processes, the convex hull that bounds the 24-D dynamic carrier — and one is a
work item.

## Running it

```bash
cd /path/to/GLM                       # repo root, where GLM.py lives
PYTHONPATH=. python3 -m glm_universal.capabilities
PYTHONPATH=. python3 -m glm_universal.capabilities --area reals
PYTHONPATH=. python3 -m glm_universal.capabilities --probe real_equality_is_decidable
PYTHONPATH=. python3 GLM.py -q "report capabilities" -c 1
```

```python
from glm_universal import capabilities as cap

cap.probe_names()                       # every declared capability
cap.run_probe("real_equality_is_decidable")
cap.capability_report()                 # all of them, grouped by area
```

The command-line entry point exits `1` only if a probe **errored** — that is,
fell over so that its evidence cannot be trusted. A probe that breaks exits
`0`, because breaking is a finding.

## The modules

| module | what it is |
| --- | --- |
| `harness.py` | `Outcome`, `Probe`, the `@probe` decorator and registry, `run_probe`, `run_all`, `capability_report`, and the nine `AREAS` a probe may declare |
| `probes.py` | the 22 numeric and structural probes: reals, the dynamic carrier, the substrate, carriers, layers, the algebra |
| `probes_language.py` | the 11 probes that go through the value grammar, the semantics layer and the query runtime |
| `__main__.py` | `python3 -m glm_universal.capabilities`, with `--area` and `--probe` |

## What a probe declares, and what it returns

Before it runs, a probe declares

* a **question**, in the words of someone using the machine rather than
  maintaining it;
* an **area** — one of `reals`, `dynamic carrier`, `substrate`, `carriers`,
  `layers`, `algebra`, `runtime`, `semantics`, `scale`;
* an **expectation**, `"holds"` or `"breaks"` — what is believed *now*.

After it runs it returns a **verdict** (`holds` / `breaks` / `error`), a
**boundary** stating exactly where the capability stops — a weight, a level, a
denominator, a certificate — and the **evidence**, as strings, so two runs can
be compared key by key.

A verdict that differs from the declared expectation is reported as a
**surprise**: a probe that breaks where it was expected to hold is a
regression, and one that holds where it was expected to break is a capability
newly won. Both are surfaced instead of being buried in a diff.

Nothing here scores anything. There is no pass rate.

## The current reading

**33 probes: 20 hold, 13 break, 0 errored, 0 surprises.** The counts are
recomputed under *Capability probes* in
[`../../FIGURES.md`](../../FIGURES.md).

| area | holds | breaks |
|---|---|---|
| reals | 6 | 4 |
| runtime | 5 | 0 |
| dynamic carrier | 4 | 2 |
| carriers | 2 | 1 |
| layers | 1 | 2 |
| semantics | 1 | 1 |
| scale | 1 | 1 |
| algebra | 0 | 1 |
| substrate | 0 | 1 |

The thirteen boundaries, each with the place it stops:

| probe | area | where it stops |
|---|---|---|
| `real_equality_is_decidable` | reals | `sqrt(2)*sqrt(2)` and `2` are still not distinguished at `2⁻⁶⁴`, and no precision settles it. Inequality is decidable; equality is refused. |
| `real_division_by_an_undecided_value` | reals | a divisor that has not moved away from zero by `2⁻⁶⁴` is refused: `1/x` needs a bound `\|x\| ≥ 2⁻ᵐ`, and producing one for an arbitrary process would decide whether it is zero. |
| `real_value_as_carrier` | reals | a carrier holds 24 rationals and no rational is `sqrt(2)`; the coordinate is refused rather than rounded. |
| `real_surrogate_on_a_grid_point` | reals | the floor of a process is not computable where the process sits exactly on the grid: 64 refinements of `sqrt(1/4)` do not settle which side of `1/2` it is on. |
| `dynamic_24d_arbitrary_target` | dynamic carrier | the reachable set is the convex hull of the 4,096 codewords; the ramp target `i/24` is outside it, with a separating functional verified against every codeword. |
| `dynamic_repair_is_single_valued` | dynamic carrier | on 36 of 100 ticks the driven word sat at distance 4 from six codewords at once, so repair has no single value; the tie is declared, not broken. |
| `layers_can_compute_addition` | layers | addition is not a function of what the substrate or integer layers see — the exact content of the `can_multiply` flag. |
| `tax_conservation_above_bits` | layers | exact on binary carriers; above them repairable only if `Y = 1/2`, and `1/4 < Y < 1/2`. |
| `substrate_repair_radius` | substrate | the repair radius is exactly 3; at weight 4 six codewords are equally near, and at weight 5 the answer is unique, confident and wrong. |
| `carrier_non_dyadic_denominator` | carriers | a coordinate of `1/12` has no dyadic exponent, so there is no depth at which the binary planes *are* the value. |
| `algebra_product_is_associative` | algebra | the Norton–Sakuma product is not associative: the two bracketings of a pairwise-2A triple give `−3/32` times *different* axes. |
| `semantics_open_vocabulary` | semantics | the vocabulary is exactly the registers; there is no coordinate for 'justice'. **Work item.** |
| `scale_more_than_24_coordinates` | scale | twenty-four is the substrate, not a parameter: a 25th coordinate is refused rather than silently dropped. |

The remaining work item, `semantics_open_vocabulary`, is written up with the
exact line at which it stops in
[`INFINITE_VALUES_STUDY.md`](../../../studies/INFINITE_VALUES_STUDY.md) §3.6 and §3.7.

Two probes have crossed from `breaks` to `holds` since that write-up, which is
what the lifecycle is for. `runtime_arithmetic_inside_a_describe` recorded
that `what is energy` worked while `what is energy divided by time` did not;
`reasoning/term_arithmetic.py` now rewrites the operator words into the
dimensional grammar, evaluates the expression exactly and names every register
quantity of the resulting dimension, so the probe holds and its evidence
carries the answer — dimension `L^2 M T^-3`, named six ways: `heat_flow`,
`luminosity`, `metabolic_rate`, `power`, `radiant_flux`. Note that the probe
does not accept an answer at face value: it fails the capability unless the
quotient's dimension *and* `power` both appear.

The other one crossed earlier. `real_transcendental_functions`
recorded that `sin`, `log`, `exp` and `2^pi` were refused by name; they are
now built in `reasoning/transcendental.py`, so the probe reports **holds**,
checks the identities `exp(log x) = x`, `sin² + cos² = 1`, `2^(1/3) =
root(3, 2)` and `log(2, 8) = 3` instead of the refusal, and records the new
boundary in its evidence: the inverse and hyperbolic family is still refused
by name, and a logarithm still needs a positivity witness. Between them the
totals moved 18/15 → 19/14 → **20/13**, and each move forced an edit to
`EXPECTED_VERDICTS` in `test_capabilities.py` — which is the point of
declaring the expectation up front.

## Adding a probe

```python
from .harness import Outcome, breaks, holds, probe

@probe("area_thing_it_can_do", "reals",
       "Can it do the thing?", "holds")
def _area_thing_it_can_do() -> Outcome:
    ...
    return holds("how far it was pushed", evidence_key=value)
    # or
    return breaks("exactly where it stops", evidence_key=value)
```

Register the name in the module's `*_PROBE_NAMES` tuple. `test_capabilities.py`
then picks it up automatically and checks that the two probe files account for
every registered probe, that the area and the expectation are among the
declared ones, that the probe's verdict agrees with its own expectation, that
it does not error, and — if it breaks — that it states where it stops.

## Covered by

`glm_universal/tests/test_capabilities.py` — 56 tests: the harness itself
(registration, error trapping, the surprise rule), every probe run for real,
and the `report capabilities` query with its column-3 script.
