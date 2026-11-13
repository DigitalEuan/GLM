# Application show-work

These 22 files are the legacy physical-backend show-work proposals. They record
how a declared £ was decomposed, enumerated, escalated and emitted as a `.cir`
example. They are **not** current transfer proposals: current proposal bundles
live in [`../examples/transfer/`](../examples/transfer/README.md), and the
`.cir` files are declared reference artifacts, not measured devices.

The repeated parts live here once. Each proposal links to this page instead of
copying the pipeline, the declared escalation parameters or the run commands.

## Show-work pipeline

Run `python3 tests/show_work.py` to see the full trace. The eight steps are:

1. **¢ DAG decomposition** — formula parsed into atomic ¢ operations
2. **∆ enumeration** — all valid physical implementations enumerated
3. **¢_cost ranking** — top 5 ranked by 6-axis cost function
4. **5-layer escalation** — ideal → parasitic → thermal → quantum → fabricated
5. **Conjecture loop** — re-lift with next-best substrate if rank-1 fails
6. **SPICE netlist emission** — `.cir` file written to `examples/`
7. **Parametric certification** — exact parameter ranges certified
8. **Knowledge state** — assigned to Cent Wheel ring (THINKS-TRUE if converged)

## Declared escalation parameters

These values are the declared screening inputs shared by the show-work
proposals. They are not measured device parameters.

| Parameter | Value | Used in | How |
|-----------|-------|---------|-----|
| opamp_gain | 100000.0 | parasitic layer | equilibrium error ≈ 1/(2·gain) |
| bandwidth_hz | 1000000.0 | thermal layer | Johnson noise V_n = √(4kTR·BW) |
| temperature | 300 | thermal layer | noise floor V_n ∝ √T |
| resistance | 1000 | thermal layer | noise magnitude V_n ∝ √R |
| signal_level | 1.0 | thermal+quantum | SNR = 20·log₁₀(signal/noise) |
| current | 0.001 | quantum layer | shot noise I_n = √(2qI·BW) |
| component_tolerance | 0.01 | fabricated layer | worst-case stack-up |
| n_components | 3 | fabricated layer | scales tolerance |

## How to run

```bash
cd cent_compiler_v12
python3 tests/show_work.py                  # trace all 22 proposals
python3 cent compile "y = sqrt(5)"          # compile one relation
```

Each proposal's own `## SPICE Output` section names its template and reference
`.cir` file. The command above is the shared entry point; use the proposal's
relation in place of `y = sqrt(5)` when tracing one case.

## The W1↔W6 Paynter table

The electrical/fluidic correspondence used by proposals 01 and 06 is declared
once here:

| Electrical (W1) | Fluidic (W6) | Physical meaning |
|-----------------|-------------|------------------|
| Voltage (V) | Pressure (P) | "Effort" — across variable |
| Current (I) | Volume flow rate (Q) | "Flow" — through variable |
| Resistance (R) | Hydraulic resistance | Effort/flow ratio |
| Power (V·I) | Hydraulic power (P·Q) | Effort × flow |

The table is an analogy declaration, not a measured fluidic device.
