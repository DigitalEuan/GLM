# Constrained design solver

`cent solve` selects a **declared design point** for a bound route.  It does not
invent component values, and the solver itself is not a netlist generator.  The
solver searches a finite, explicit set of alternatives, evaluates each one
through the real device binding, and emits a verification plan.  A solved
design can then be handed to `cent physical` for a reference netlist and
schematic stage floorplan, or to `cent dynamics` for the declared sampled-data
model.  The browser exposes the same solver in its **Design solver** tab, and
bound method cards link directly to the matching declared space.

The implementation is `cent_compiler/design.py`; the focused tests are in
`tests/test_design.py`, with browser and API coverage in `tests/test_webui.py`.

## 1. Constraints

The solver accepts five exact constraints:

| Constraint | Meaning |
|---|---|
| `input` | the declared operating point |
| `range` | `MIN:MAX`; the endpoints and the operating point are probed |
| `accuracy` | maximum total relative error from the binding |
| `max_cost` | ceiling in declared complexity units |
| `min_bandwidth` | minimum declared small-signal pole bandwidth in Hz |

All numbers are exact rationals.  Fractions such as `1/500`, exact decimals and
integers are accepted; binary floats are not.

`range` is evaluated at its endpoints and the operating point, then certified
continuously when the route declares a monotone error/bandwidth direction.  A
single-point request is a one-point certificate.  An unknown or non-monotone
direction stays `gap`; the certificate is declared evidence, not sampling.

`min_bandwidth` is checked at every probe against every pole the binding
declares.  The frequency of a pole is `1 / (2 * pi * tau)`.  Because `pi` is
irrational, the solver uses a certified rational enclosure: a candidate passes
only when the lower frequency bound from that enclosure meets the target, fails
only when the upper bound misses it, and otherwise records a conservative
`gap`.  The slowest pole is the limiting one.  This is a small-signal pole
check; large-signal stability is certified separately for the compute routes.

## 2. Declared design spaces

The alternatives are intentionally small and visible.  The cost is a declared
complexity unit, not currency, BOM cost or yield.

### Delta-sigma carry

| Option | Parameter | Cost |
|---|---|---:|
| `offset-1/200` | comparator offset fraction `1/200` | 1 |
| `offset-1/500` | `1/500` | 2 |
| `offset-1/1000` | `1/1000` | 3 |
| `offset-1/2000` | `1/2000` | 4 |

The default accuracy `1/100` selects `offset-1/200`.  At `1/500`, the
`offset-1/1000` grade is the cheapest passing option.

### Log-domain square root

| Option | Parameter | Cost |
|---|---|---:|
| `precision-8` | 8-bit enclosure | 1 |
| `precision-20` | 20-bit enclosure | 2 |
| `precision-32` | 32-bit enclosure | 3 |
| `precision-64` | 64-bit enclosure | 4 |

The default single-point request selects `precision-8`.  For the range
`1/2:1`, the 8-bit candidate fails the enclosure-width check at `1/2`, so the
solver selects `precision-20`.

### Op-amp + multiplier feedback

| Option | Parameter | Cost |
|---|---|---:|
| `gain-100000` | error-amplifier gain `100000` | 1 |
| `gain-1000000` | `1000000` | 2 |
| `gain-10000000` | `10000000` | 3 |

The lower gains fail the finite-gain bias check at the default 1% accuracy.
`gain-1000000` is the cheapest passing feedback design.  A `max_cost` of `1`
therefore returns an explicit no-solution result rather than silently weakening
the accuracy target.

## 3. Exact evaluation

For each option and each probe point, the solver calls the corresponding
`bind_*` function with:

```text
input_value = probe point
error_limit = requested accuracy
parameters  = the alternative's declared parameters
```

A candidate passes only when:

1. the binding constructs successfully;
2. every exact device-law check passes;
3. the total relative error is within the requested accuracy;
4. every declared small-signal pole meets `min_bandwidth` when a target is given;
5. the declared cost is within `max_cost` when a ceiling is given.

The solver first applies the hard constraints above. It then sorts the feasible
candidates into exact Pareto layers over the declared objectives: `cost` and
`max_relative_error` in the `exact-static` profile, plus the certified lower
bound of the slowest declared pole in `dynamic-aware`. Rank 1 is the Pareto
front; no weighted scalar score is used.

`auto` selects `dynamic-aware` only when `min_bandwidth` is requested, otherwise
`exact-static`. `dynamic-aware` requires a bandwidth target. This split matters
in practice: in a noiseless exact comparison the declared alternatives are a
strict cost/accuracy trade-off, so every feasible option is non-dominated and
the front is the whole feasible set; a dynamic target adds a certified bandwidth
axis without inventing a noise or SNR model. The selected point is the
lowest-cost member of the front, with lowest max relative error and then option
name breaking exact ties:

```bash
python3 cent solve sqrt-feedback --min-bandwidth 100000 --ranking dynamic-aware
python3 cent solve delta-sigma --min-bandwidth 1000 --ranking exact-static
```

A candidate that passes its device checks but exceeds the cost ceiling is marked
`gap`, not `pass`; the result shows the exact cost violation.  If no alternative
passes, the solver returns a no-solution result with every candidate and failure
visible.

## 4. Verification plan

A solved result contains an ordered plan:

| Step | Status |
|---|---|
| Declared exact binding | `pass`; includes the exact `cent bind` command |
| Accuracy and cost | `pass`; reports the exact selected option and limit |
| Pareto ranking | `pass` when a feasible front exists; reports the profile, exact front, layers and tie-break |
| Declared-pole bandwidth | `pass` when requested and certified; `gap` otherwise; reports the slowest pole and its certified interval |
| Continuous range certificate | `pass` when the declared monotone error and bandwidth directions cover the endpoints; `gap` otherwise |
| Reference netlist / floorplan | `pass`; includes the exact `cent physical` and `cent fabricate` commands, while a manufactured board remains a gap |
| Measured device evidence | `gap` |
| Dynamic behavior | `partial` for all three routes; includes the exact `cent dynamics` command. Delta-sigma uses the sampled RC/clock loop plus a continuous-time four-substep clocked-comparator/RC transient; the compute routes use nonlinear large-signal backward-Euler transients with adaptive step-doubling. All three expose a `nonlinear_transient` coverage block; the compute routes pass continuous bounded-state and monotone-stability certificates. Their certified local-truncation global bound is valid but still exceeds the 1e-3 V target |
| Fabrication / yield | `gap` |

The plan is therefore a mixture of what was actually executed and what remains
open.  A gap is never converted into a pass by the solver.  The reference row
means that the selected binding can be emitted as a declared topology; it does
not mean the SPICE deck was simulated or that a board can be fabricated.

## 5. Commands

```bash
# Cheapest default delta-sigma design
python3 cent solve delta-sigma

# Tighten accuracy; the solver changes the comparator grade
python3 cent solve delta-sigma --accuracy 1/500

# Probe both ends of the declared log-domain range
python3 cent solve sqrt-log --range 1/2:1

# Enforce a cost ceiling; this one has no feasible declared design
python3 cent solve sqrt-feedback --max-cost 1

# Require at least 100 kHz from the declared small-signal poles
python3 cent solve sqrt-feedback --min-bandwidth 100000

# Machine-readable result, including the full selected binding
python3 cent solve sqrt-feedback --json

# Emit the selected design's reference netlist and schematic floorplan
python3 cent physical sqrt-log --range 1/2:1
python3 cent physical sqrt-feedback --json

# Run the declared sampled-data and nonlinear-compute checks
python3 cent dynamics delta-sigma --samples 64
python3 cent dynamics sqrt-log --samples 64
```

### Browser and HTTP API

`python3 cent web` serves a **Design solver** tab containing all three spaces.
Each card has exact input, optional `MIN:MAX` range, accuracy, maximum-cost and
minimum-bandwidth fields. Solving renders every candidate, the selected parameters, rejected
candidates with their exact reasons, the verification plan and the remaining
gaps. A solved card also exposes **Emit reference netlist / floorplan**, which
renders the part list, stages, reference SPICE deck and physical gaps, and
**Run dynamic check**, which renders the sampled or nonlinear transient,
its certificates and dynamic gaps. A separate **Method comparison** card solves
any chosen subset of the routes independently under shared requests and
downloads JSON or Markdown. Method cards in **Find methods** carry a link to the
matching design card.

The same solver is available over the local HTTP API:

```text
GET  /api/design
GET  /api/solve?route=sqrt-log&range=1/2:1
GET  /api/solve?route=sqrt-feedback&min_bandwidth=100000
POST /api/solve  {"route": "delta-sigma", "accuracy": "1/500"}
GET  /api/compare?routes=sqrt-log,delta-sigma&range=1/2:1
POST /api/compare  {"routes": "sqrt-feedback,sqrt-log", "min_bandwidth": "1000"}
GET  /api/physical?route=sqrt-log&range=1/2:1
POST /api/physical  {"route": "delta-sigma", "accuracy": "1/500"}
GET  /api/dynamics?route=delta-sigma&samples=64
GET  /api/dynamics?route=sqrt-log&samples=8&v_log_hi=0.1&v_out_hi=0.1
POST /api/dynamics  {"route": "sqrt-log", "samples": "8",
                     "certificate_box": {"v_log_hi": "1/10", "v_out_hi": "1/10"}}
```

All design-constraint values must be exact strings (fractions, exact decimals
or integers). A binary float is rejected rather than converted through its
stored representation. Constants use `input`, `range`, `accuracy`, `max_cost` and `min_bandwidth`;
`range` is `MIN:MAX`. Certificate-box bounds are exact strings or
integers, and binary floats are rejected there too. The response wraps the
`cent-design/1` result under `design`.

### Cross-route comparison

`python3 cent compare [routes...]` solves each selected route independently with
the same requested constraints; with no routes it compares all three. A blank
input leaves each route on its declared default input. The result keeps each
route's own Pareto front, selected option, constraints and gaps, and exports
`cent-comparison/1` JSON or a Markdown table:

```bash
python3 cent compare --range 1/2:1
python3 cent compare sqrt-log delta-sigma --json
python3 cent compare --markdown
```

The HTTP endpoint accepts `routes` as a comma-separated string or JSON list, plus
the same `input`, `range`, `accuracy`, `max_cost`, `min_bandwidth` and `ranking`
fields as the solver. The payload carries compact `rows`, full `results` keyed by
route, the comparison `note` and `markdown`. It deliberately does not compute a
cross-route scalar winner: costs are declared complexity units, and Pareto ranks
remain within a route.

A solved browser result remains a declared design point; the reference emitter
is a separate step and returns a `cent-physical/1` payload, while the dynamic
check returns `cent-dynamics/1`. The plan and gaps are rendered alongside both
so the app does not turn a successful search, a reference deck or a finite
trace into a fabrication or convergence claim.

Representative human output:

```text
Route: Log-domain square-root compute route
Status: solved

Declared candidates
  [gap ] precision-8        cost=1   max_error=0.0082220858
        1/2: failed checks: enclosure width
  [pass] precision-20       cost=2   max_error=0.0081998410
  [pass] precision-32       cost=3   max_error=0.0081998409
  [pass] precision-64       cost=4   max_error=0.0081998409

Selected design
  option           precision-20
  cost             2
  parameters       precision=20
  max error        0.0081998410  (limit 1/100; exact value in JSON)
```

## 6. JSON result

The result uses schema `cent-design/1`:

```json
{
  "schema": "cent-design/1",
  "route": "sqrt-log-domain",
  "status": "solved",
  "constraints": {
    "input": {"num": "1", "den": "1"},
    "input_range": {"min": {"num": "1", "den": "2"}, "max": {"num": "1", "den": "1"}},
    "accuracy": {"num": "1", "den": "100"},
    "max_cost": null,
    "min_bandwidth": null
  },
  "selected": {
    "option": {"name": "precision-20", "cost": {"num": "2", "den": "1"}},
    "binding": {"schema": "cent-device/1", "passed": true}
  },
  "verification_plan": []
}
```

The actual payload includes every candidate, every probe, the full selected
binding and the full plan.

## 7. Advisory fabrication audit

A solved design carries a separate `fabrication_audit` block under
`cent-design/1`. It is built by the existing physical and fabrication layers,
not by a second geometry model:

```text
selected design
  -> physical.build_physical()
  -> fabrication.build_fabrication()
  -> exact DRC, thermal and parasitic checks
  -> cent-fabrication-audit/1 (advisory)
```

The audit reports `status` (`drc-pass`, `drc-gap`, `not-run` or `gap`),
`checks_passed`/`check_count`, the exact checks, failed-check names, the
maximum junction temperature and limit, sensitive references, unrouted nets,
exact parasitic rows and the declared fabrication gaps. It does **not** filter
candidates or change the selected design. The full geometry remains available
through `cent fabricate`.

The default audit passes all 10 declared checks for the three default routes.
A forced rule failure, such as `DRCRules(bus_pitch=1/4)`, returns `drc-gap` and
names `Copper clearance`; an unsolved design returns `not-run` with no invented
geometry.

## 8. Limits

- Only the three declared design spaces above are searched.  There is no
  arbitrary resistor/capacitor/gain synthesis.
- Range checking uses the declared endpoints and operating point only; it does
  not prove behavior at every point between them.
- Cost is an abstract declared complexity unit.  It is not a price, availability
  or yield model.
- Bandwidth is checked only over the declared small-signal poles at the probe
  points.  It is not a full frequency response, large-signal stability proof or
  measured pole model.
- Device limits come from the existing bindings.  The delta-sigma route has an
  exact sampled RC/clock trace; the log and feedback routes have declared
  adaptive step-doubling nonlinear large-signal transients with continuous
  bounded-state and monotone-stability certificates.  Their certified
  local-truncation global bound is still far above the 1e-3 V target; noise,
  drift, thermal coupling and measured settling remain unmodeled.
- `cent physical` emits a reference netlist and schematic floorplan, but no
  transistor-level model, measured-device report, manufacturing geometry,
  calibration procedure or fabrication claim.
- The firmware/measurement plan needed to validate a physical build is not
  generated.

## 9. Tests

```bash
python3 tests/test_design.py
```

The suite checks:

- exact Pareto ranking and cheapest-front default selection for all three routes;
- tighter accuracy selecting a tighter comparator grade;
- cost ceilings rejecting technically passing candidates with an exact reason;
- range endpoints forcing a higher log-domain precision;
- declared-pole bandwidth passing the feedback route, rejecting the slower log
  route, and leaving a target inside the π enclosure as a gap;
- the feedback route's honest no-solution result below its achievable accuracy;
- JSON serialization, the selected binding and the advisory fabrication audit,
  including a forced DRC gap and an unsolved `not-run` result;
- invalid accuracy, inverted range, out-of-range operating point and unknown
  route errors;
- the human plan renderer and the `cent solve` CLI, including JSON;
- independent cross-route comparison, shared constraints, per-route ranks,
  JSON/Markdown export and the `cent compare` CLI;
- the browser catalog, range/POST solve paths, comparison API, no-solution
  result and invalid route/range/float rejection.

Browser suite: `python3 tests/test_webui.py` (92/92), including `/api/physical`,
`/api/fabricate`, `/api/dynamics`, `/api/compare` and the ranking profiles. The
constrained solver has `python3 tests/test_design.py` (60/60). The reference emitter has its own
`python3 tests/test_physical.py` (36/36). The declared fabrication layer has
`python3 tests/test_fabrication.py` (53/53). The dynamics layer has
`python3 tests/test_dynamics.py` (41/41). Discovery exposes the solver metadata
and is covered by `python3 tests/test_discovery.py` (133/133). The canonical
seventeen-suite gate is `python3 tests/run_all.py` (824/824).
