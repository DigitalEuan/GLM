# Op-amp + analog-multiplier square root

This is the third exact compute route in the physical compiler. It models the
classic analog feedback topology:

```text
x ──► Σ ──► high-gain amplifier ──► drive y
      ▲                              │
      │                              ▼
      └──── analog multiplier ◄── y · y
```

The multiplier is in the feedback path, so the amplifier drives `y` until
`y² = x`. The route is solved at **steady state**; it is not an explicit Euler
transient.

## 1. Finite-gain law

The typed route declares a finite amplifier gain `A` and a multiplier gain `k`:

```text
residual(y) = A * (x - k*y²) - y
```

The equilibrium is the positive root of this residual. For the default
`A = 1,000,000` and `k = 1`, the route intentionally retains the small
finite-gain bias instead of silently replacing the loop with `sqrt(x)`.

The typed components are:

| Role | Primitive | Declared material | Law |
|---|---|---|---|
| `multiplier` | `mult` | Gilbert-cell / AD633 analog multiplier | `product = k·a·b` |
| `error_amp` | `amp` | op-amp error amplifier | `drive = A·error` |

The error sum `x - k·y²` is arithmetic glue. The route has no exact-core
`Program`, because the algebraic feedback loop is not acyclic; the solver and
its residual are recorded explicitly in the route payload.

## 2. Exact solution

The compiler brackets the positive root with:

```text
lo = 0
hi = max(1, x/k)
```

For `A,k > 0`, the residual is positive at `lo` and negative at `hi`, and it is
monotone on `y ≥ 0`. Bisection then uses exact rational midpoints. The default
64 iterations avoid the denominator growth that made an explicit Euler
multiplier loop impractical: the bracket denominator is a power of two, not a
product of growing polynomial terms.

The independent checker is the quadratic formula:

```text
y = (sqrt(1 + 4·A²·k·x) - 1) / (2·A·k)
```

It uses the core's certified `sqrt_q` enclosure. That checker is not an
instruction in the route.

A separate ideal `sqrt_q(x)` bracket is reported for comparison. The
finite-gain output is expected to sit just below the ideal square root; the
difference is the reported `finite-gain error`.

## 3. Run it

```bash
python3 cent assemble sqrt-feedback --input 2 --precision 64 --iterations 64
```

Representative output:

```text
Exact algebraic-feedback simulation
  input: 2
  amplifier gain: 1000000
  multiplier gain: 1
  iterations: 64
  tolerance: 1/10000
  root: ≈ [1.4142130623731834, 1.4142130623731834]
  quadratic checker: ≈ [1.4142130623731834, 1.4142130623731834]
  ideal sqrt bracket: ≈ [1.4142135623730950, 1.4142135623730950]
  overlap: [1.4142130623731834, 1.4142130623731834]
  finite-gain error: 0.000000499999911611
  residual: 0.000000000000023229
  root width: 0.000000000000000000
  passed: True
```

The displayed width is truncated at 18 decimal places. The JSON payload carries
the exact rational endpoints; at 64 iterations the bracket width for `x = 2` is
`1/9223372036854775808`.

```bash
python3 cent assemble sqrt-feedback --input 2 --precision 64 --json
```

`passed` requires the root enclosure to overlap the independent quadratic
checker, the bracket width to stay inside the declared tolerance, and the
finite-gain bias to stay inside that tolerance.

## 4. Relationship to the log-domain route

The log-domain route is an explicit pipeline:

```text
log x → scale by 1/2 → exp
```

It targets the ideal `sqrt(x)` and returns a certified enclosure; its main
physical risk is junction matching, temperature gradient and saturation-current
mismatch.

This feedback route is an implicit algebraic loop:

```text
drive y → multiply y·y → compare with x → amplify the error → drive y
```

It targets the finite-gain equilibrium, not the ideal irrational. Its main
physical risks are amplifier gain, multiplier nonlinearity and loop stability.
The route is useful as a comparison because it reaches the same function by a
different topology and exposes a different error mechanism.

Neither route is a fabrication netlist. Both now have declared device bindings
documented in [`DEVICE_BINDING.md`](DEVICE_BINDING.md). The feedback binding uses
`V_in = V_ref·x`, `V_out = V_ref·y` and `V_fb = k·V_out²/V_ref`, checks loop
closure independently, and reports a static budget of `0.0031014207` at the
default point (`x = 2`, `A = 10⁶`, `k = 1`, 20-bit target enclosure) against a
`0.01` limit. Its dominant terms are the declared amplifier and multiplier
offsets, not the finite gain.

## 5. Limits

- Adds a declared slope-normalized adaptive nonlinear large-signal closed-loop
  transient with continuous bounded-state and monotone-stability certificates;
  it does not model slew rate, oscillation or startup. Its certified
  local-truncation global bound still exceeds the 1e-3 V target.
- The declared reference design uses `k = 1`; a non-unit gain is supported and
  retargets the ideal to `sqrt(x/k)`. The AD633 `/10` transfer factor and
  multiplier nonlinearity are not modeled; offsets are only declared bounds.
- No measured amplifier, multiplier or passive data.
- No noise, drift, saturation recovery or fabrication evidence.
- The finite-gain bias is reported, not corrected by an ideal `sqrt` stage.

Run `python3 cent dynamics sqrt-feedback` for the declared nonlinear transient.

## 6. Checks

```bash
python3 tests/test_assembly.py
python3 tests/test_binding.py
python3 tests/test_discovery.py
python3 cent bind sqrt-feedback --input 2
```

The assembly suite covers both exact compute routes, the no-`sqrt` solver
payload, the finite-gain bias, non-unit multiplier gain, invalid inputs and the
CLI. The binding suite covers the physical loop closure, headroom, offsets and
the static budget. Discovery reports `3/3` exact typed routes and `3/3` declared
device bindings.
