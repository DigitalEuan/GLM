# Delta-Sigma Demonstration

Delta-sigma is a **carrier**, not a square-root algorithm. It represents a value
as a temporal sequence of quantized levels whose running average tracks that
value. This distinction is enforced by `cent discover`: delta-sigma is grouped
under **carry / represent**, while square-root routes are grouped under
**compute**.

## 1. Exact typed route

The current exact assembly is a first-order loop assembled from three declared
physical ingredient contracts:

```text
x ──► Σ ──► accum ──► quantize ──► level
      ▲       (integrator) (flash ADC)   │
      │                                 │
      └──── delay ◄─────────────────────┘
            (clocked register)
```

```bash
python3 cent assemble delta-sigma --input 1/2 --samples 12
```

The route is a checked exact-core `Program`; every numeric wire is a
`fractions.Fraction`. The default quantizer has levels `0` and `1`. Its exact
law is:

```text
level = clamp(quantum * round(signal / quantum), 0, full_scale)
```

The saturation at the ADC reference rails is part of the declared quantizer
contract. Without it, the raw nearest-level operation would emit negative
levels outside the ADC range and the loop would not be a bounded bitstream.

For the half-scale input the first twelve levels are:

```text
1 1 1 0 0 0 1 1 1 0 0 0
```

Their exact average is `1/2`. For one-third:

```bash
python3 cent assemble delta-sigma --input 1/3 --samples 12
```

the repeating code is `0 1 1 0 0 0 0 1 1 0 0 0`, whose exact average is `1/3`.
These are finite exact runs, not a proof of convergence for every input.

## 2. Device binding

The companion declared binding maps the normalized loop to an RC/clock design
point:

```bash
python3 cent bind delta-sigma
```

At the default point `V_ref = 1 V`, `R_in = 100 kΩ`, `C_int = 1 nF` and
`f_clock = 10 kHz`, the exact check `R_in * C_int * f_clock = 1` makes one clock
tick equal one normalized integrator increment. The one-bit quantizer maps to
`V_lsb = 1 V` with a `0.5 V` threshold; the exact run peaks at `1 V`, inside the
declared `8 V` range with `9 V` supply. The static input-referred budget is
`0.00521` against a `0.01` limit.

These are declared specifications, not datasheet or measured values. See
[`DEVICE_BINDING.md`](DEVICE_BINDING.md) for the quantities, checks and gaps.

## 3. What is typed

The route's physical ingredients are:

| Role | ¢ primitive | Typed law | Declared material |
|---|---|---|---|
| Integrator | `accum` | `y_t = y_{t-1} + x_t` | switched-capacitor / op-amp integrator |
| Quantizer | `quantize` | nearest level, clamped to `[0, full_scale]` | flash ADC / comparator bank |
| Feedback memory | `delay` | `y_t = x_{t-1}` | clocked register / sample-and-hold |

`sum` and `neg` are exact arithmetic glue in the generated program, not
standalone device claims. The route plan records ports, parameters, laws,
failure modes and material sources; `route.as_dict()` is the machine-readable
form.

## 4. What this does not prove

- It is a **normalized exact route model** with a declared reference binding,
  not a fabrication netlist.
- The binding maps the loop to a declared RC/clock point, but does not generate
  a switch-level schematic, bias network, layout or geometry.
- The binding budgets comparator offset, reference tolerance and RC/clock
  tolerance. `cent dynamics` now runs the declared RC/clock loop over time, but
  it does not model metastability, clock jitter, capacitor leakage, finite
  op-amp gain or a transistor-level transient.
- The `cent showcase` command remains a separate floating-point spectral demo
  (100,000 samples, FFT, noise shaping). It is evidence for the modulation
  principle, not for the exact assembly.
- A finite exact run is not a convergence theorem.

## 5. Reproduce the checks

```bash
python3 tests/test_assembly.py
python3 tests/test_discovery.py
python3 tests/test_dynamics.py
python3 cent dynamics delta-sigma --samples 64
python3 cent discover "carry an irrational value as a physical signal"
```

The discovery payload should report the delta-sigma method as a carry route
with an exact typed route model, a passing exact simulation, and a remaining
gap for the device/fabrication netlist.
