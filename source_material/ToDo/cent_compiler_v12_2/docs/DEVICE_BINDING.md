# Declared device bindings

This note documents the layer between the normalized exact routes and a
physical design point. It is intentionally **not** a fabrication netlist. It
answers a narrower question:

> If the normalized route is built with these declared components, what
> voltages, currents, resistances, capacitance and clock does it imply, and
> which device laws can be checked exactly?

The three physical design routes can be handed to `cent physical` for a
reference netlist and schematic stage floorplan; that downstream artifact is
documented in [`PHYSICAL_NETLIST.md`](PHYSICAL_NETLIST.md). It is still not
manufacturing geometry. The KCL binding is normalized and has no physical
artifact path yet. The binding itself answers:

> If the normalized route is built with these declared components, what
> voltages, currents, resistances, capacitance and clock does it imply, and
> which device laws can be checked exactly?

The implementation is `cent_compiler/device.py`, and the CLI entry point is
`cent bind`.

All numeric values are exact `fractions.Fraction` values. The design points are
**declared reference specifications**, not datasheet values, measurements or
proof that a circuit has been fabricated. Each binding also exposes `poles`:
name, symbol, time constant, source and status. The design solver checks those
poles against an optional exact `min_bandwidth`; the binding itself does not
claim a measured frequency response.

## 1. Delta-sigma carry route

### Declared design point

| Quantity | Value | Unit | Status |
|---|---:|---|---|
| `V_ref` | 1 | V | declared |
| `R_in` | 100000 | ohm | declared |
| `C_int` | 1e-9 | F | declared |
| `f_clock` | 10000 | Hz | declared |
| `offset_ratio` | 1/200 | of `V_lsb` | declared |
| `tau = R_in * C_int` | 1e-4 | s | derived |
| `T_clock = 1 / f_clock` | 1e-4 | s | derived |
| `RC_f = R_in * C_int * f_clock` | 1 | dimensionless | check |
| `V_lsb` | 1 | V | derived |
| `V_threshold` | 1/2 | V | derived |
| `V_offset` | 1/200 | V | derived |
| `V_int_peak` for input 1/2 | 1 | V | simulated |
| `V_int_limit` | 8 | V | declared |
| `V_supply` | 9 | V | derived |

The key scaling relation is exact:

```text
R_in * C_int * f_clock = 1
```

so one clock tick defines the normalized scale. It does **not** mean the RC
integrator settles to a full increment in one tick: with `tau = T_clock` the
exact first-order step gain is `1 - exp(-1) = 0.6321205588...`. `cent dynamics`
reports this finite settling explicitly. The one-bit quantizer maps to a 1 V
step with a 0.5 V threshold. The reference-voltage
headroom is one volt above the declared 8 V integrator range.

### Checks

`cent bind delta-sigma` runs eight checks:

- the RC/clock product is exactly one;
- the comparator offset is below the nearest threshold;
- the RC and clock tolerances stay inside the declared coefficient margin;
- the exact run's peak maps inside the integrator range;
- the integrator range has supply headroom;
- the static error budget is inside the declared limit;
- the static budget is below half an LSB;
- the normalized exact route still passes.

### Static error budget

| Term | Relative bound | Source |
|---|---:|---|
| comparator offset | 0.005 | offset / `V_lsb` |
| reference gain error | 0.0001 | declared `V_ref` tolerance |
| integrator gain error | 0.00011 | RC tolerance + clock tolerance |
| **total** | **0.00521** | worst-case sum |
| **limit** | **0.01** | declared acceptance limit |

This is a static, input-referred budget. It excludes shaped quantization noise,
leakage, finite op-amp gain, slew, clock jitter, metastability and thermal
drift. It is a sum of bounds, not a Monte Carlo distribution.

### Sampled-data consequence

`cent dynamics delta-sigma` runs the declared RC/clock loop with exact interval
arithmetic. At the default point and 64 ticks the loop mean is `31/64`, within
one LSB of `1/2`, while the one-tick gain gap is about `0.368`. The overall
dynamic status is `partial`: tracking passes, but the static budget does not
model finite settling. See [`DYNAMICS.md`](DYNAMICS.md).

## 2. Log-domain square-root compute route

### Declared design point

| Quantity | Value | Unit | Status |
|---|---:|---|---|
| `V_ref` | 1 | V | declared |
| `R_in` | 1000 | ohm | declared |
| `I_ref = V_ref / R_in` | 1e-3 | A | derived |
| `I_s` | 1e-9 | A | declared |
| `T` | 300 | K | declared |
| `V_T = k_B T / q` | approx. 0.025852 | V | derived |
| `n` | 1 | dimensionless | declared |
| `G` | 1/2 | V/V | declared |
| `R_out` | 1000000 | ohm | declared |
| `V_out_ref` | 1 | V | declared |
| `V_supply` | 2 | V | derived |
| `C_j` | 10 pF | F | declared |
| `C_out` | 10 pF | F | declared |
| `r_d = n * V_T / I_in` | approx. 25.85 | ohm | derived |
| `tau_log = r_d * C_j` | approx. 2.58e-10 | s | derived |
| `tau_out = R_out * C_out` | 1e-5 | s | derived |

The nominal current path is:

```text
V_in = V_ref * x
I_in = V_in / R_in
V_log = V_T * ln(I_in / I_s)
V_half = (1/2) * V_log
I_out = I_s * exp(V_half / V_T)
V_out = R_out * I_out
```

The full-scale component choice is checked by squaring the relation instead of
solving for an irrational value:

```text
V_out_ref^2 = R_out^2 * I_s * I_ref
```

For the default point this is exactly `1 = 1`. At `x = 1/2` the independently
evaluated device law gives:

```text
V_out    = [0.7071067733, 0.7071067876] V
V_target = [0.7071065902, 0.7071070671] V
```

The intervals overlap, and the output width is far below the declared `1/10000`
route tolerance.

### Exact-rational size control

The exact thermal voltage uses the SI constants `k_B = 1.380649e-23 J/K` and
`q = 1.602176634e-19 C`. An exact exponential enclosure of a logarithm with a
large denominator can grow thousands of bits long. The device-law logarithm is
therefore rounded **outward** to 12 decimal places before exponentiation. This
preserves containment, keeps the JSON practical, and adds a negligible width
compared with the route tolerance. The route itself is unchanged.

### Static error budget at `x = 1/2`

| Term | Relative bound | Source |
|---|---:|---|
| input resistor tolerance | 0.00005 | output scales as `sqrt(1/R_in)` |
| output resistor tolerance | 0.0001 | output scales as `R_out` |
| reference voltage tolerance | 0.00005 | output scales as `sqrt(V_ref)` |
| junction saturation mismatch | 0.001 | declared `I_s` mismatch |
| gain / temperature / ideality mismatch | 0.0066998410 | upper bound `exp(delta * ln(I_ref/I_s)) - 1` |
| log-stage input offset | 0.0001 | declared offset at this input |
| output offset | 0.0001 | declared output-referred offset |
| route enclosure tolerance | 0.0001 | normalized route tolerance |
| **total** | **0.0081998410** | worst-case sum |
| **limit** | **0.01** | declared acceptance limit |

The dominant term is the declared 0.1 K temperature gradient plus ideality and
gain mismatch across the log range. The budget is conservative: it uses the
worst-case log range and adds independent bounds.

### Declared dynamic reference

`C_j` and `C_out` are **declared reference capacitances**, not measured diode or
board parasitics. The derived `r_d = n*V_T/I_in` and `tau_log = r_d*C_j` remain
reported small-signal reference quantities. `cent dynamics sqrt-log` does not
use a linearized envelope: it integrates the full Shockley diode law and the
declared half-gain antilog stage as a two-node nonlinear ODE. At the default
point the output pole `tau_out = R_out*C_out = 10 us` dominates. The run spans
12 output poles with adaptive backward Euler; at 64 samples it accepts 297
steps and rejects 10 trials, the output reaches about `0.999991 V`, the diode
node about `0.357159 V`, and the final relative error is about `1.4e-5`. The
result is `partial`: the continuous bounded-state certificate passes, while the
step-doubling local budget, monotone-stability certificate and certified
local-truncation global bound are explicit; the bound still exceeds the 1e-3 V
target.

## 3. Op-amp + analog-multiplier feedback compute route

### Declared design point

| Quantity | Value | Unit | Status |
|---|---:|---|---|
| `V_ref` | 1 | V | declared |
| `V_in = V_ref * x` | 2 | V | derived |
| `A` | 1000000 | V/V | declared |
| `k` | 1 | dimensionless | declared |
| `V_supply` | 5 | V | declared |
| `V_headroom = V_ref / 2` | 1/2 | V | derived |
| `C_out` | 10 pF | F | declared |
| `R_out` | 1000 | ohm | declared |
| `tau_cl` | 1e-7 | s | declared |
| `tau_out = R_out * C_out` | 1e-8 | s | derived |
| `offset_ratio` | 1/200 of `V_ref` | V | declared |
| `V_os`, `V_os_mult` | 0.005 | V | declared |
| `V_fb = k * V_out^2 / V_ref` | approx. 1.9999985857 | V | simulated |
| `V_error = V_in - V_fb` | approx. 0.0000014142 | V | simulated |
| `V_drive = A * V_error` | approx. 1.4142130623 | V | simulated |
| `V_out = V_ref * y` | approx. 1.4142130623 | V | simulated |
| `V_target = V_ref * sqrt(x/k)` | approx. [1.4142131805, 1.4142141342] | V | check |
| `V_gain_error` | approx. 0.0000005950 | V | derived |

The normalized mapping is exact:

```text
V_in  = V_ref * x
V_out = V_ref * y
V_fb  = k * V_out^2 / V_ref
V_out = A * (V_in - V_fb)
```

The finite-gain route deliberately does not output the ideal irrational. Its
output is the equilibrium of the declared loop. At the default point the
finite-gain bias is about `5.95e-7 V`, and the target interval is shown
separately so the bias is not mistaken for a wider enclosure. The target uses
the binding's default 20-bit `sqrt_q` enclosure; the algebraic root itself is
solved by exact bisection with 64 iterations.

### Checks

`cent bind sqrt-feedback` runs eleven checks:

- the normalized finite-gain route passes its independent quadratic check;
- the route root and quadratic checker overlap;
- the physical output enclosure is narrower than `V_ref * route tolerance`;
- the finite-gain bias from the ideal `sqrt(x/k)` target is bounded;
- the independently evaluated multiplier and amplifier laws close the loop;
- the error-amplifier differential input stays in its declared linear range;
- the input, multiplier feedback and op-amp output stay inside the supply
  headroom;
- the static error budget stays inside the declared limit;
- the declared `tau_cl` and `R_out*C_out` dynamic poles are positive.

### Static error budget at `x = 2`

| Term | Relative bound | Source |
|---|---:|---|
| reference voltage gain | 0.0001 | output scales linearly with `V_ref` |
| multiplier gain tolerance | 0.0005 | output scales as `1/sqrt(k)` |
| finite amplifier gain | 0.0000004207 | finite-gain bias relative to `sqrt(x/k)` |
| amplifier gain tolerance | 0.0000000000 | finite-gain bias scales with `A` tolerance |
| amplifier input offset | 0.00125 | declared input offset / `(2*x)` |
| multiplier feedback offset | 0.00125 | declared feedback offset / `(2*x)` |
| route enclosure tolerance | 0.000001 | normalized route tolerance |
| **total** | **0.0031014207** | worst-case sum |
| **limit** | **0.01** | declared acceptance limit |

The dominant terms are the two declared offsets, not the finite gain. This is a
different failure profile from the log-domain binding, whose dominant term is
the gain/temperature/ideality mismatch over the log range. The two totals are
not a like-for-like accuracy comparison: they use different inputs, references
and declared component assumptions.

This is a static, declared design point. It excludes loop stability, slew,
noise, offset drift, multiplier nonlinearity and the AD633 `/10` scaling. A
separate declared dynamic reference uses `C_out = 10 pF`, `R_out = 1000 ohm`,
`tau_cl = 100 ns` and `tau_out = 10 ns`. `cent dynamics sqrt-feedback` integrates
the quadratic multiplier feedback as a slope-normalized nonlinear loop; the
normalization preserves `tau_cl` as the small-signal closed-loop pole instead
of silently turning it into a much faster open-loop integrator pole. At 64
samples adaptive step doubling accepts 291 steps and rejects 7 trials; the
output rises to about `1.414207 V` against a `1.414213062 V` finite-gain target,
with final relative error about `4.4e-6`. This is not a slew or measured-pole proof. The continuous bounded-state and
scalar-stability certificates pass; the certified local-truncation global bound
still exceeds the 1e-3 V target.

## 4. KCL normalized sum binding

The KCL route has a declared **normalized reference binding**, not a physical
design point. `cent bind sum-kcl` binds two normalized exact inputs and the
selected operation:

| Quantity | Value | Unit | Status |
|---|---:|---|---|
| `a` | 1/2 | 1 | declared |
| `b` | 1/3 | 1 | declared |
| `total` for `sum` | 5/6 | 1 | simulated |
| `total` for `difference` | 1/6 | 1 | simulated |
| `expected` | `a + b` or `a - b` | 1 | check |
| error limit | 1/100 | 1 | declared |

No resistor, voltage, current, noise, offset, tolerance, source/load or thermal
parameter is declared. The binding therefore has no error terms and reports an
exact zero total; that zero is an exact normalized result, not a physical error
budget. The explicit gaps record the missing voltage/current mapping, source and
load compliance, finite-bandwidth and fabrication evidence.

`cent bind sum-kcl` runs two checks:

- the normalized KCL route simulation passes;
- the result is exactly `a + b` for `sum` or `a - b` for `difference`.

The independent parameter audit recomputes `total` from the two stored inputs
and the operation recorded in the route simulation. It does not repair a
mismatch. No physical artifact is emitted for this route yet; `cent physical`
has no KCL design space or reference netlist.

## 5. Reference emission and its boundary

After `cent solve` selects a declared point, `cent physical` maps the exact
binding onto the route's declared stage roles. It emits a connected reference
part list, a SPICE-shaped deck and non-overlapping schematic stage rectangles.
The exact quantities remain in JSON; SPICE numeric fields are decimal
representations.

This is a real handoff, but narrowly scoped. The deck uses ideal behavioral
blocks for integration, comparison, logging, antilog and multiplication. It has
not been simulator-validated. There are no footprints, parasitics, PCB
coordinates, DRC, thermal placement, supplier parts or measured-device models.
Those are explicit gaps in the payload.

## 6. Run it

```bash
python3 cent bind delta-sigma
python3 cent bind sqrt-log --input 1/2
python3 cent bind sqrt-log --input 1/2 --json
python3 cent bind sqrt-feedback --input 2
python3 cent bind sqrt-feedback --input 2 --json
python3 cent bind sum-kcl --input 1/2 --input-b 1/3
python3 cent bind sum-kcl --input 1/2 --input-b 1/3 --operation difference --json
python3 cent dynamics delta-sigma --samples 64
python3 cent dynamics sqrt-log --samples 64
python3 cent dynamics sqrt-feedback --samples 64
```

The human output lists the declared quantities, every device-law check, the
error terms and the remaining gaps. The JSON payload contains the exact
rational values, including the interval endpoints and widths.

`cent discover` includes a **Bind device quantities** stage. The separate
`cent physical` command is the reference-emission stage:

```text
[pass ] Bind device quantities: 3/3 declared reference binding(s) pass; no fabrication netlist
[gap  ] Emit physical design: 3 exact route graph(s) and 3 device binding(s); no fabrication netlist or geometry
```

The discovery pipeline still marks full physical design as a gap because it
does not itself emit geometry. `cent physical` fills the reference-netlist and
schematic-floorplan part, while a manufactured board and measured evidence
remain open.

## 7. What this establishes

- The three normalized routes have declared voltage, current, resistance,
  capacitance, clock, temperature, gain and junction parameters.
- The delta-sigma RC/clock scaling, the log-domain squared reference relation
  and the feedback multiplier/amplifier fixed point are checked exactly.
- The log-domain device law is evaluated independently of the route program and
  compared with the certified square-root target.
- The feedback square law and error amplifier are evaluated independently of
  the algebraic route solver.
- Each binding reports a conservative static error budget and whether it stays
  inside the declared limit.
- All three bindings expose declared dynamic quantities: the delta-sigma
  RC/clock, the log-domain junction/output capacitance and the feedback
  closed-loop and load timing. `cent dynamics` runs the sampled RC loop and
  nonlinear large-signal compute-route transients from those quantities.
- The KCL binding preserves both exact inputs and the exact sum or difference,
  and its independent audit recomputes the normalized total.
- Every unmodeled effect is listed as a gap, not hidden behind a passing check.

## 8. What this does not establish

- The binding itself is not a device netlist. `cent physical` can emit a
  reference netlist and schematic floorplan for the three physical routes, but
  not a transistor-level model, bias network or manufacturing layout.
- The KCL route has no physical artifact path: no voltage/current mapping,
  source/load model, component values, error budget or reference netlist is
  declared.
- It does not use measured resistor, capacitor, comparator, reference, diode,
  op-amp or multiplier model data.
- It does not simulate full nonlinear dynamic large-signal behavior, startup,
  saturation recovery, noise, 1/f drift, thermal coupling or frequency response.
- The delta-sigma route has an exact sampled RC/clock trace; the compute routes
  have declared adaptive step-doubling nonlinear transients with continuous
  bounded-state and monotone-stability certificates. None is a transistor-level
  simulation or a measured-device model; the certified local-truncation global
  bound still exceeds the 1e-3 V target.
- It does not model feedback loop stability, slew, full settling or multiplier
  nonlinearity.
- It does not prove that the declared design point can be purchased,
  fabricated or calibrated to the stated tolerances.
- The error budgets are sums of declared bounds, not statistical yield claims.

Wheel text grounding now has a declared typed bridge, and `cent solve` selects a
declared design point under accuracy, range and cost constraints. The same
solver is exposed in the browser **Design solver** tab and through
`/api/design`, `/api/solve`, `/api/compare`, `/api/physical` and `/api/dynamics`; bound method
cards link to it directly. The three physical routes have declared reference bindings,
and a selected binding can emit a reference netlist and schematic floorplan or
a declared dynamic model. The KCL route has a normalized binding only. None is
a fabrication netlist. See
[`DESIGN_SOLVER.md`](DESIGN_SOLVER.md), [`PHYSICAL_NETLIST.md`](PHYSICAL_NETLIST.md)
and [`DYNAMICS.md`](DYNAMICS.md).

## Independent parameter audit

Every `DeviceBinding.as_dict()` payload includes `parameter_audit`. The audit
recomputes the declared derived quantities from independent algebraic
relations rather than trusting the constructor values: RC/clock timing and
supply relations for delta-sigma, `V_T`, diode resistance, junction/output
poles and input scaling for the log route, input, headroom and load-pole
relations for the feedback route, and the two-input normalized total for the
KCL route. A missing or mismatched quantity is a visible `gap`; the audit never
repairs a binding in place.
