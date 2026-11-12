# Sampled-data and adaptive nonlinear dynamics

`cent dynamics` adds a time-domain check to the static route, device and
reference-netlist layers. It runs a model only when the declared binding
contains enough timing quantities to define one.

```bash
python3 cent dynamics delta-sigma --samples 64
python3 cent dynamics sqrt-log --samples 64
python3 cent dynamics sqrt-feedback --samples 64
python3 cent dynamics sqrt-log --json
```

The implementation is `cent_compiler/dynamics.py`; focused tests are in
`tests/test_dynamics.py`.

All three routes currently return `status: "partial"`. That is intentional: the
delta-sigma model exposes a static/dynamic gain mismatch, and the two compute
routes use adaptive backward Euler with exact step doubling. All three results
also expose a `nonlinear_transient` coverage block. Delta-sigma now runs a
separate continuous-time, four-substep RC transient with a clocked comparator;
the two compute routes expose their existing adaptive nonlinear transients.
The compute routes carry a continuous forward-invariance **bounded-state
certificate**, which passes for the declared boxes and can fail explicitly
when a caller supplies a too-small box. The controller still controls only a
**local** coarse/fine difference; the global certificate now uses certified
local truncation terms, but its conservative bound still exceeds the 1e-3 V
target.

## 1. Delta-sigma sampled RC/clock loop

The delta-sigma binding declares `R_in`, `C_int`, `f_clock`, `tau`, `T_clock`,
`V_ref`, `V_threshold`, `V_offset` and `V_int_limit`. The model treats the
integrator as a first-order RC response sampled once per clock:

```text
alpha      = 1 - exp(-T_clock / tau)
V_fb[n]    = V_ref * level[n]
V_int[n+1] = V_int[n] + alpha * (V_in - V_fb[n])
```

The comparator samples `V_int[n]` at the start of the tick and compares it with
`V_threshold + V_offset`. Input and feedback are held constant over the tick.
The exponential is an exact rational enclosure, not a binary float. The trace
stores exact interval endpoints at every tick.

The route also runs a continuous-time transient with four substeps per clock.
Feedback is decided at each clock edge and held for that clock; between edges
the state follows the exact first-order step

```text
drive = V_in - V_fb
V(t + dt) = drive + (V(t) - drive) * exp(-dt / tau)
```

with `dt = T_clock / 4`. The clocked comparator is the nonlinear element.
State endpoints are rounded outward to a 12-place decimal grid after each
substep so a long exact trace stays serializable; containment is preserved.
The coverage block reports the substep trace, peak, final state, comparator
uncertainties and checks. This is deliberately a bounded clocked model, not a
claim of a smooth nonlinear ODE, switch-level device behavior or SPICE.

At the declared point:

```text
tau       = 1/10000 s
T_clock   = 1/10000 s
alpha     = 1 - exp(-1) = 0.6321205588285577...
```

The static binding uses one full normalized increment per clock. That is the
asymptotic gain, not the physical one-tick response. At `x = 1/2` and 64 ticks
the loop mean is `31/64`, the mean error is `-1/64`, and the peak excursion is
about `0.6321 V` against an 8 V limit.

## 2. Log-domain adaptive nonlinear diode/load transient

The log-domain binding declares:

| Parameter | Value | Meaning |
|---|---:|---|
| `C_j` | 10 pF | reference junction capacitance at the declared input |
| `C_out` | 10 pF | output load plus antilog junction |
| `R_out` | 1 MΩ | declared output resistance |
| `V_T` | approx. 25.85 mV | thermal voltage at 300 K |
| `I_in` | 1 mA at `x = 1` | declared input current |
| `r_d = n*V_T/I_in` | approx. 25.85 Ω | reported small-signal reference, not the model |
| `tau_log = r_d*C_j` | approx. 258 ps | reported small-signal reference, not the model |
| `tau_out = R_out*C_out` | 10 µs | dominant output pole |

The transient is the two-node nonlinear ODE

```text
C_j   dV_log/dt = I_in - I_s * exp(V_log / V_T)
C_out dV_out/dt = I_s * exp(G * V_log / V_T) - V_out / R_out
```

The logging junction is not linearized: it keeps the full declared Shockley
exponential with `I_s = 1 nA` and `n = 1`. The antilog stage uses the declared
half-gain `G = 1/2`.

Each trial uses backward Euler on both nodes:

```text
C_j/h   * (V_log[n+1] - V_log[n])
        + I_s * exp(V_log[n+1] / V_T) = I_in
C_out/h * (V_out[n+1] - V_out[n])
        = I_s * exp(G * V_log[n+1] / V_T) - V_out[n+1] / R_out
```

The log-node root is bracketed between the previous state and the open-circuit
voltage `V_oc = V_T * ln(I_in / I_s)`, then bisected on a fixed `1e-9 V` grid.
The output node is the exact backward-Euler linear update from the enclosed
antilog current.

### Adaptive step control

Each trial computes one step of size `h` and two steps of size `h/2`. The
enclosed coarse/fine difference is compared with the declared local budgets:

```text
log-node: 1e-5 V + 1e-6 * |V_log|
output:   1e-4 V + 1e-6 * |V_out|
```

A trial is accepted only when the normalized difference is at most `1`. The
initial step is `min(t_final/(4*samples), tau_log/8)`; accepted steps are grown
when the ratio is below `4/5`, rejected steps are shrunk by up to `10x`, and
step sizes are rounded to a `1e-21 s` grid to bound exact denominators. The
trial budget is 20,000.

At the default `x = 1` and 64 samples:

```text
297 accepted steps, 10 rejected trials
step range: approx. 1.185e-11 s .. 1.875e-6 s
max accepted local error ratio: approx. 0.989
V_log  settles at approx. 0.357158576 V   (trace aux)
V_out  rises 0.1701, 0.3114, 0.4158 ... V
V_out  reaches approx. 0.9999913 V at 120 us
target declared device-law output, approx. 1 V with a 1.6e-5-wide enclosure
final relative error approx. 1.4e-5
```

The result is `partial`: the local step-doubling budget, the declared reference
capacitances, the bounded-state and monotone-stability certificates are
explicit, and the global error bound is certified but still exceeds the 1e-3 V
target.

## 3. Feedback adaptive nonlinear quadratic closed-loop transient

The feedback binding declares:

| Parameter | Value | Meaning |
|---|---:|---|
| `tau_cl` | 100 ns | declared small-signal closed-loop pole |
| `R_out` | 1 kΩ | declared output resistance |
| `C_out` | 10 pF | declared load capacitance |
| `tau_out = R_out*C_out` | 10 ns | reported output load pole |
| target | approx. 1.414213062 V | finite-gain equilibrium at `x = 2` |

The loop residual is the same quadratic device law used by the static binding:

```text
F(V)     = A * (V_in - k * V^2 / V_ref) - V
tau_cl * dV/dt = F(V) / (1 + 2 * A * k * V / V_ref)
```

The denominator is the local slope of `F`. The normalization is not cosmetic:
using `tau_cl` directly on the raw residual would make the linearized
closed-loop pole `tau_cl / (1 + 2*A*k*V/V_ref)`, about 35 fs at the default
point, not the declared 100 ns. Dividing by the slope preserves the same
equilibrium and quadratic feedback, but makes the small-signal linearization
exactly `dV/dt = -dV / tau_cl` at every operating point.

Backward Euler becomes a quadratic in the new state:

```text
a*V^2 + b*V - (V_old + r*A*V_in) = 0
a = A*k*(2 + r)/V_ref
b = 1 + r - 2*A*k*V_old/V_ref
r = h / tau_cl
```

The constant term is negative, so the physical root is the unique positive
root. It is solved directly with a certified `sqrt_q` enclosure rather than
bisected, which also avoids bracketing the unphysical negative root.

The same step-doubling controller is used, with the output budget
`1e-4 V + 1e-6 * |V_out|` and initial step
`min(t_final/(4*samples), tau_cl/16)`. At the default `x = 2` and 64 samples:

```text
291 accepted steps, 7 rejected trials
step range: approx. 3.005e-14 s .. 1.875e-8 s
max accepted local error ratio: approx. 0.831
V_out  rises 0.5827, 0.7885, 0.8548 ... V
V_out  reaches approx. 1.4142068 V at 1.2 us
target approx. 1.414213062 V
final relative error approx. 4.4e-6
```

The load pole is reported but not separately integrated; the loop uses the
declared `tau_cl`. The result is `partial` because the local step-doubling estimate does not by
itself prove the 1e-3 V target; the global bound now uses certified local
truncation terms and remains above that target, even though the continuous
bounded-state and stability certificates pass.

### Bounded-state certificate and global envelope

For the log route the declared box is

```text
V_log in [0, v_open_hi]
V_out in [0, max(R_out * I_s * exp(G*v_open_hi/V_T), V_out_target_hi)]
```

The certificate evaluates the continuous rates at the box faces with interval
arithmetic. It requires `f_log(0) >= 0`, `f_log(v_open_hi) <= 0`,
`f_out(0,0) >= 0` and `f_out(v_open_hi, v_out_hi) <= 0`. The log rate does not
depend on `V_out`, and the output rate increases with `V_log`, so these face
checks cover the whole box. The feedback route uses the scalar box
`V_out in [0, v_hi]` and requires `f(0) >= 0` and `f(v_hi) <= 0`.

Forward invariance is a property of the **continuous declared ODE**. The
certificate separately checks that every sampled numerical interval is inside
the box. A caller-supplied box is checked without expansion: a too-small box
returns `gap` and reports the failing boundary signs and trace containment. The
focused tests exercise that failure path for both routes.

The global certificate uses certified backward-Euler local truncation terms,
`h^2 M2 / 2`, over the continuous state box. The log route combines them with
its triangular contraction; the feedback route uses a certified negative scalar
derivative. Both `certified` flags are true. The conservative bounds are about
`5.46e8 V` (log) and `1.80e19 V` (feedback), far above the `1e-3 V` target, so
`within_target` is false and the status remains `gap`. The old row-sum
Gronwall/step-doubling path is retained only as a conditional fallback if a
local bound is unavailable.

## 4. Checks and status

Every compute-route report contains:

- **Nonlinear ODE state** — the declared diode/load or quadratic loop is
  integrated as an exact interval state.
- **Large-signal settling** — final relative error against the declared target.
- **Monotonic output** — the response stays nondecreasing at the accepted steps.
- **Output range** — the output stays inside the declared supply.
- **Adaptive step control** — `pass` when every accepted trial stayed inside
  the declared local step-doubling budget. Rejected trials and the accepted
  step range are reported in the metrics.
- **Bounded-state certificate** — continuous forward-invariance on a declared
  box plus containment of every numerical interval; `gap` when a face sign or
  the trace check fails.
- **Global error envelope** — certified backward-Euler local truncation plus
  the route contraction. It is `gap` with `certified: true` and
  `within_target: false` because the conservative bound exceeds `1e-3 V`.

The metrics include `integration_steps`, `rejected_steps`,
`min_step_seconds`, `max_step_seconds`, `max_local_error_ratio`,
`max_rejected_error_ratio`, `local_defect_sum`, `bounded_state_status`,
`global_error_status`, `global_lipschitz_bound`, `global_envelope_exponent`,
`local_atol` and `local_rtol`. The `certificates` object carries the box,
boundary signs, trace containment and envelope details.

The delta-sigma report additionally checks RC/clock ratio, one-tick settling
gain, sampled loop tracking, integrator range and comparator resolution.

Status is `pass` only when the model is complete and every check passes;
`partial` when a trace is produced but a declared gap remains; `gap` when a
hard check fails or no model can be defined.

Both compute-route transients use exact rational enclosures. Exponential
intermediates are rounded outward to a 12-decimal grid during the run to bound
exact denominator growth; containment is preserved, and the grid is far below
the settling tolerance. Step-doubling acceptance is exact, but it remains a
local estimate. The bounded-state certificate proves the continuous box, not
discrete-time invariance of the adaptive integrator; the separately checked
trace containment covers the sampled run.

## 5. CLI, HTTP and browser

```bash
python3 cent dynamics delta-sigma --input 1/2 --samples 64
python3 cent dynamics sqrt-log --input 1 --samples 128 --json
python3 cent dynamics sqrt-feedback --input 2 --range 1:4
python3 cent dynamics sqrt-log --samples 8 \
  --certificate-box '{"v_log_hi":"1/10","v_out_hi":"1/10"}'
```

`--input`, `--range`, `--accuracy`, `--max-cost` and `--min-bandwidth` mirror
`cent solve`;
`--samples` is bounded to `1..256` (default 64) and sets the trace resolution,
not a fixed internal step. `--certificate-box` takes a JSON object of positive
exact bounds: `v_log_hi` and `v_out_hi` for `sqrt-log`, or `v_hi` for
`sqrt-feedback`. A valid but too-small box returns the normal `gap` report;
malformed or wrong-shaped boxes are rejected before the dynamic run. The JSON
payload uses schema `cent-dynamics/1` and wraps the result under `dynamics`.

```text
GET  /api/dynamics?route=delta-sigma&samples=64
GET  /api/dynamics?route=sqrt-log&samples=64
GET  /api/dynamics?route=sqrt-log&samples=8&v_log_hi=0.1&v_out_hi=0.1
POST /api/dynamics  {"route": "sqrt-feedback", "samples": "64"}
POST /api/dynamics  {"route": "sqrt-log", "certificate_box":
                     {"v_log_hi": "1/10", "v_out_hi": "1/10"}}
```

GET requests accept the flat bound names; POST requests accept either those
names or a nested `certificate_box` object. Missing keys, extra keys, a box on
the delta-sigma route, or binary floats return HTTP 400. A valid too-small box
returns HTTP 200 with `status: gap` and the failing boundary/trace evidence.

The browser **Design solver** card exposes **Run dynamic check** after a
successful solve. Delta-sigma renders state/level/feedback; the compute routes
render time/output/target. The log payload also carries the diode-node `aux`
interval. Metrics, checks, certificates and gaps are shown alongside the trace.

## 6. Limits

- Delta-sigma: ideal sampled first-order RC integrator plus the four-substep
  continuous-time clocked-comparator/RC transient, ideal comparator and
  one-bit feedback. No switch resistance, leakage, op-amp slew, clock jitter,
  metastability, thermal drift or noise.
- Log-domain: declared reference `C_j` and `C_out`, full Shockley logging
  junction and declared half-gain antilog stage. No buffer pole, bias-network
  bandwidth, saturation recovery, thermal coupling, 1/f noise or measured
  parasitics.
- Feedback: declared slope-normalized quadratic loop. No slew, stability proof,
  startup, multiplier nonlinearity beyond the declared square law, noise or
  measured op-amp poles. The load pole is reported but not separately
  integrated.
- Adaptive step doubling controls the enclosed coarse/fine difference inside a
  declared local budget. The certified global bound uses the declared local truncation terms, while the
  local tolerances remain model declarations rather than measured requirements.
- The bounded-state certificate covers only the declared continuous model and
  the checked numerical trace. It does not cover every possible numerical step
  sequence, unmodeled poles, or startup outside the declared box.
- No route has measured R/C values, tolerance distributions, Monte Carlo,
  thermal coupling or transistor-level transient simulation.
- The SPICE deck from `cent physical` is a reference artifact; these models are
  independent exact calculations, not simulator runs of that deck.

## 7. Tests

```bash
python3 tests/test_dynamics.py   # 41 checks
python3 tests/test_webui.py      # 92 checks, including /api/dynamics and /api/compare
```

The suite covers the `1 - e^-1` enclosure, exact sampled means, the delta-sigma
continuous-time substep trace, all three nonlinear coverage blocks and dynamic
traces, the nonlinear compute-route equations, adaptive acceptance, settling,
trace shape, the bounded-state certificates, the forced too-small-box failures
through the public route, CLI and HTTP paths, the certified global bound,
stability certificate, sample bounds, JSON safety, the CLI and the browser API.
The full seventeen-suite run is 824/824 checks.
