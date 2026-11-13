# Log-domain square root — the first exact compute route

This note documents the second assembled route in the physical compiler. The
first route, delta-sigma, **carries** a known value as a bitstream. This route
**computes** a square root from an input:

```text
sqrt(x) = exp((1/2) * ln(x))
```

It is deliberately not a physical transistor netlist. It is a typed,
parameterized route whose finite-precision result is a certified rational
enclosure, checked independently against the compiler's exact `sqrt_q` bracket.

## D3 sibling: log-domain arithmetic

The same declared log and antilog junctions also support the generated
`log-domain-arithmetic` card under the `transcendental-identity` principle.
`exp` and `log` are the single junctions; `mult` is
`log → log → sum → exp`; `div` is `log → log → neg → sum → exp`; and
`reciprocal` is `log → neg → exp`. `tests/test_log_domain.py` exercises the
source routes, fifteen fixed target vectors and the declared `1/10000`
tolerance. The sqrt card remains separate and
sqrt-specific, so a control that refuses the cam Δ for `exp`/`log` still
refuses the wrong Δ while naming this sibling as the unblock. No measured
junction is claimed.

## Typed components

| Role | Primitive | Declared material | Law |
|------|-----------|-------------------|-----|
| `logger` | `log` | diode / BJT logging stage | `y = ln(x)` as a rational enclosure |
| `half_gain` | `scale` | resistor divider / op-amp gain | `y = (1/2)·x` |
| `antilog` | `exp` | diode / BJT antilog stage | `y = exp(x)` as a rational enclosure |

The route has an explicit `precision` parameter (default 20 bits) and a
`tolerance` parameter (default `1/10000`). Both are declared model parameters,
not hidden floating-point settings.

## Exact program

```text
inputs: x
1. ln_x    <- ¢_log(x)
2. half_ln <- ¢_scale(ln_x, factor=1/2)
3. root    <- ¢_exp(half_ln)
outputs: root, ln_x, half_ln
```

There is no `sqrt` instruction in the generated program. The square root is
constructed from the declared log/antilog stages.

## Run it

```bash
python3 cent assemble sqrt-log --input 2 --precision 20
```

Representative output:

```text
Exact certified-enclosure simulation
  input: 2
  precision: 20 bits
  tolerance: 1/10000
  route root: ≈ [1.4142135569336852, 1.4142135673303303]
  independent sqrt bracket: ≈ [1.4142131805419921, 1.4142141342163085]
  overlap: [1.4142135569336852, 1.4142135673303303]
  root width: 0.000000010396645082
  passed: True
```

The displayed decimals are truncated for readability. The JSON payload carries
the exact rational numerator/denominator pairs for every endpoint and width.

```bash
python3 cent assemble sqrt-log --input 1/2 --precision 24 --json
```

## Device binding

The companion declared binding maps the normalized route to a reference
circuit design point:

```bash
python3 cent bind sqrt-log --input 1/2
```

At the default point `V_ref = 1 V`, `R_in = 1 kΩ`, `I_s = 1 nA`,
`R_out = 1 MΩ`, `T = 300 K` and `n = 1`. The squared reference relation
`V_out_ref^2 = R_out^2 * I_s * I_ref` is checked exactly, so no irrational
square root is used to choose a component value. The independent device-law
result at `x = 1/2` is `[0.7071067733, 0.7071067876] V`, overlapping the
certified target `[0.7071065902, 0.7071070671] V`. The declared worst-case
static budget is `0.0081998410` against a `0.01` limit.

These are declared specifications, not datasheet or measured values. See
[`DEVICE_BINDING.md`](DEVICE_BINDING.md) for the quantities, checks, budget
terms and remaining model gaps.

## What this establishes

- The route is assembled from three typed component contracts, each with
  declared ports, laws, operating conditions, material source and failure modes.
- The exact core evaluates the route with rational arithmetic; no binary float
  enters the evaluator.
- The result is a certified enclosure, not an exact irrational scalar.
- `passed` requires two things: the route enclosure overlaps the independent
  `sqrt_q` enclosure, and the route width is within the declared tolerance.
- Input `x <= 0` is rejected, not silently clipped.
- A perfect-square input still produces a consistent enclosure; it is not
  special-cased into an exact rational answer.

## Target handoff

```bash
python3 cent transfer "sqrt" --target glm-reference --validate
```

The `glm-reference` target executes a target-side
`exp((1/2) * log(x))` adapter over three fixed positive vectors. It checks the
source and target enclosures against each other and against the independent
`sqrt_q` baseline, then emits a `cent-transfer-certificate/1`. The certificate
is `target-simulated`: the route remains a declared software model, not a
fabricated or measured junction. It adds no measured latency, bit budget or
device accuracy.

## What this does not establish

- It is not a fabrication netlist or geometry.
- The route itself is normalized; the companion binding maps it to a declared
  electrical reference point, but not to a fabrication netlist or bias network.
- The binding declares reference `C_j` and `C_out` and an adaptive nonlinear
  large-signal diode/load transient, but does not model a buffer pole,
  bias-network bandwidth, thermal drift, 1/f noise or measured parasitics. The
  continuous bounded-state and monotone-stability certificates pass for the
  declared box. The certified local-truncation global bound is valid but still
  exceeds the 1e-3 V target.
- The precision parameter is a model of finite resolution, not a measured
  device accuracy.
- The log/antilog physical realization is declared material, not a fabricated or
  measured circuit.

Run `python3 cent dynamics sqrt-log` for the declared nonlinear transient. These
gaps are reported by `cent discover`, the route plan, the device binding and the
dynamic payload itself. A third compute route, the op-amp + analog-multiplier
finite-gain feedback square root, is now assembled and documented in
[`OPAMP_MULTIPLIER_SQRT.md`](OPAMP_MULTIPLIER_SQRT.md). It targets a nearby
finite-gain equilibrium rather than the ideal irrational, so the two routes
should be compared on their declared error mechanisms and device bindings, not
only on bracket width. Its declared static budget is `0.0031014207` at the
default point, versus `0.0081998410` here; the feedback route's dominant terms
are input and multiplier offsets, while this route's dominant term is the
log-range gain/temperature/ideality mismatch.
