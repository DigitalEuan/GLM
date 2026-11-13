# Computational machines — experimental side-arm

**Status:** experimental side-arm, not a D-item and not part of the transfer
scoreboard. The canonical gate covers its fixed tests, but it does not promote
the machine to a measured-device capability.

A transfer candidate answers one question: can this operation be mapped to a
mechanism? A **machine** answers the surrounding question: what complete signal
chain does the concept need, which parts are supplied by the compiler, and which
stages are actually executed?

The first machine is `sigma-delta-sqrt`. It turns the mathematical-function-tree
sketch for a one-bit ∆Σ √2 carrier into a staged, inspectable payload and runs
its digital branch. The same side-arm can wrap any assembled exact route
(`delta-sigma`, `sqrt-log`, `sqrt-feedback`, `sum-kcl`, `sum-fluid`,
`sum-opamp`) in the four-stage template, selecting compatible compiler parts for
the primitive operations in its typed graph.

## Commands

```bash
# List the declared machines.
python3 cent machine list

# Build the full tree, select compiler-ranked parts and run the executable branch.
python3 cent machine sigma-delta-sqrt

# Same payload as JSON.
python3 cent machine sigma-delta-sqrt --json

# Wrap an assembled exact route in the four-stage template.
python3 cent machine sqrt-log
python3 cent machine sum-kcl --load mechanical
python3 cent machine sum-fluid --load fluid

# Write machine.json, machine.md and the behavioral core netlist.
python3 cent machine sigma-delta-sqrt --out examples/machines/sigma-delta-sqrt
```

The CLI accepts `--samples` and `--osr`; the default is 100,000 samples at
OSR=64. The default is the configuration that reproduces the sketch's measured
36.9 dB in-band suppression and 28.0 dB/decade noise slope.

## What the first machine contains

The hand-authored tree has four top-level branches and 21 nodes (the root plus
20 stages):

1. **Input and reference conditioning** — physical source, first-order RC
   anti-alias filter and reference rail.
2. **Core sigma-delta loop** — summing junction, loop filter, one-bit
   quantizer, one-bit feedback DAC and closed-loop output node.
3. **Timing and energy backbone** — master-clock sampling and supply rejection.
4. **Reconstruction and demodulation** — a digital decimator branch and an
   analog reconstruction/buffer branch.

Each stage declares its law, ports, status, implementation and gaps. The text
view renders the whole tree, the compiler-selected parts and the executed
metrics in one place.

### Compiler-selected core parts

The machine uses the existing transfer retrieval rather than a private lookup
table. For each core stage it retrieves the top three candidates and selects the
highest-ranked candidate whose source domain is compatible with the declared
electrical/audio path:

| Stage | Selected part | Compiler rank | Why this one |
|---|---|---:|---|
| Summing junction | `sum -> kcl-conservation` | 2 | `fluid-continuity` ranks first for the bare sum contract, but a fluid junction is not composable with this electrical loop |
| One-bit quantizer | `sign -> threshold-comparator` | 1 | exact three-level threshold law |
| Quantized carrier | `quantized_carry -> delta-sigma-error-feedback` | 1 | the declared error-feedback carrier |

This is a **domain-constrained ranking**, not a claim of a global optimum. The
alternatives and their ranks stay in the payload.

## Executable evidence

`cent machine sigma-delta-sqrt` runs the first-order `DeltaSigmaEngine` over
100,000 samples:

```text
input scale         0.700035713374682  (sqrt(2) -> 0.99 normalized)
reconstruction      1.428498547851611  (0.99 / input_scale)
decimated output    1.414208989714491
target sqrt(2)      1.414213562373095
absolute error      4.573e-06  (tolerance 1e-04)
bitstream           all 100,000 samples are exactly -1 or +1
in-band suppression 36.92 dB
NTF slope           28.02 dB/decade
```

The input and reconstruction scales are also recorded on node 1.3, so the
normalized bitstream and the reconstructed result are traceable in the tree. The
28.02 dB/decade figure is a finite-window log-PSD fit (50 bins, from
`sample_rate / samples` to `sample_rate / 4`), not an asymptotic filter order;
the ideal first-order NTF is 20.00 dB/decade. The fit note is carried in the
validation payload and on node 2.5.

The four executable checks pass. This is a **bitstream-level model**; the
36.92 dB figure is the existing benchmark's in-band suppression against an
unshaped reference, not an independently measured physical SQNR.

## Coverage and gaps

The hand-authored payload requires twelve surrounding roles and reports all
twelve present. Five stages are explicitly unmodeled:

- master-clock jitter;
- supply rejection;
- the analog reconstruction filter;
- the power buffer/actuator;
- the analog output branch as a whole.

The source, anti-alias filter and reference rail are declared but not
transient-simulated. The executed loop is the first-order error-feedback
baseline; the sketch's leaky second-order loop is recorded as an alternative
gap, not silently claimed as executed. `machine.cir` is the behavioral
electrical core only, not a fabrication netlist or a complete mixed-signal
design.

## Schema

The portable bundle is `cent-machine/1`:

| Field | Meaning |
|---|---|
| `tree` | `cent-machine-tree/1` nested function tree; the root owns the only child list (no duplicate `tree.stages`) |
| `selections.sum`, `.sign`, `.quantized_carry` | compiler-ranked part selections |
| `coverage` | required roles, present roles and unmodeled roles |
| `validation` | `cent-machine-validation/1` executable checks and metrics |
| `checks` | machine-level role, selection and execution checks |
| `gaps` | declared physical and evidence gaps |
| `claim` | explicit non-fabrication/non-measurement boundary |

A bundle written with `--out` contains `machine.json`, `machine.md` and
`machine.cir`. The Markdown is the human review view; the JSON is the portable
payload; the `.cir` is the core delta-sigma stage's behavioral netlist. The
`.cir` is explicitly marked `active_transient: false` and `fabrication: false`
in the payload and header; `cent fabricate` and `cent physical` do not consume
it. A route wrapper writes a comment-only `.cir` and records its artifact as a
`declared-gap`: a route-specific electrical netlist emitter does not exist yet.

## Route wrappers and load domains

Any declared assembled route can be wrapped without a new handcrafted tree. The
wrapper keeps the route's own `cent-typed-graph/1` nodes, lowers each node from
its existing contract, and asks the transfer retrieval for selections for every
primitive that maps to an operation contract. Unmapped glue (`neg`, `accum`,
`delay`, `sat`) remains an exact-core or declared node, not a fabricated part.

The `--load` choice is explicit:

| `--load` | Stage 4B | Evidence |
|---|---|---|
| `analog` / `electrical` | Sallen-Key reconstruction + power buffer | declared, not simulated |
| `mechanical` | TIER 3 electromechanical / rotational-linear transducer + mechanical load | declared, not simulated |
| `fluid` | TIER 3 electro-hydrodynamic / Paynter transducer + fluid load | declared, not simulated |

The load selection changes the declared stage and its gathered equations; it does
not make the load executable. `unit_scale_matrix` entries are illustrative
declared values with units, not calibrated device parameters, and no arithmetic
consumes them. A route wrapper remains exact-core evidence, not
a measured cross-domain machine. The wrapper records the route's own typed graph,
not a second simulation; its `.cir` is a declared gap rather than a fabricated or
active netlist.

## Adding another machine

Add one declarative function tree, one executable model and one fixed test to
the side-arm. The machine must state which stages are executed and which are
declared or gaps; a new machine is not accepted on a plausible tree alone. The
future work is to make each physical branch executable in turn (starting with
the analog reconstruction filter and clock/supply constraints), not to add more
trees that stop at the same boundary.
