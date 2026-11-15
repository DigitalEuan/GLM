# Proposal 04: Mechanical ∆Σ Oscillator (W4↔W5)

## £ (Target Relation)

```
angular_velocity = (2 * energy / moment_of_inertia)^(1/2)
```

## ¢ Primitive

¢_sqrt

## Wheels Involved

W4↔W5


## Pipeline (8 steps)

Run `python3 tests/show_work.py` to see the full trace. The steps are:

1. **¢ DAG decomposition** — formula parsed into atomic ¢ operations
2. **∆ enumeration** — all valid physical implementations enumerated
3. **¢_cost ranking** — top 5 ranked by 6-axis cost function
4. **5-layer escalation** — ideal → parasitic → thermal → quantum → fabricated
5. **Conjecture loop** — re-lift with next-best substrate if rank-1 fails
6. **SPICE netlist emission** — .cir file written to `examples/`
7. **Parametric certification** — exact parameter ranges certified
8. **Knowledge state** — assigned to Cent Wheel ring (THINKS-TRUE if converged)

## Parameters

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

## SPICE Output

Template: `opamp_sqrt` → `examples/proposal_04_opamp_sqrt.cir`

## How to Run

```bash
cd cent_compiler_v1
python3 tests/show_work.py                        # trace all 22 proposals
python3 cent compile "angular_velocity = (2 * energy / moment_of_inertia)^(1/2)"                    # compile just this one
