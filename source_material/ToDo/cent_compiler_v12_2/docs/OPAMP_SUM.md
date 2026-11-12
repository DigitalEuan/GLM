# Op-amp summing/difference route

This note records the second promoted addition route: `sum-opamp`, an ideal
normalized-voltage op-amp summing amplifier with a declared difference mode.

## Why this route

The KCL route is a topological junction; the fluid route is a normalized
continuity junction. The op-amp route adds a third independent realization with
an explicit closed-loop gain block:

- **Sum:** a non-inverting summing amplifier with a matched input network
  (1/2 attenuation per input) and closed-loop gain 2 gives
  `total = a + b`.
- **Difference:** an ideal inverting buffer (`gain -1`) on the second input
  followed by the same summing block gives `total = a - b`.

Both are declared ideal block models. No resistor values, device part, supply
rails, source impedance or reference netlist are invented.

## Contract

- Route id: `sum-opamp`
- Kind: `exact-sum`
- Components:
  - `summing-amp`: op-amp non-inverting summing amplifier, matched input
    resistors, closed-loop gain 2
  - `inverting-input` (difference only): op-amp inverting buffer, matched
    resistors, gain -1
- Ports: `a`, `b` (normalized exact voltages), `total`
- State: none
- Sum program: one exact `sum` instruction
- Difference program: exact `neg` on `b`, then exact `sum`
- Source: `DELTA_SUBSTRATE: sum / op-amp summing amplifier`

The route carries a `topology_audit` and a typed `cent-typed-graph/1`. Sum has
one component node; difference has two component nodes and no feedback edge.

## Mechanism and target

The route is registered as the `opamp-summing` mechanism card, so
`cent transfer sum` and `cent transfer difference` retrieve it alongside
`kcl-conservation` and `fluid-continuity`. The independent `glm-reference`
adapters execute `exact_opamp_sum` and `exact_opamp_difference` over three fixed
normalized-voltage vectors each.

## Run it

```bash
python3 cent assemble sum-opamp --input 1/2 --input-b 1/3
python3 cent assemble sum-opamp --operation difference --input 1/2 --input-b 1/3
python3 cent assemble sum-opamp --input 1/2 --input-b 1/3 --json
python3 cent graph sum-opamp --operation difference --json
python3 cent pipeline difference --mechanism opamp-summing
python3 cent transfer "sum" --mechanism "opamp-summing" --validate --json
python3 cent transfer "difference" --mechanism "opamp-summing" --validate --json
```

`1/2 + 1/3` evaluates to `5/6`; `1/2 - 1/3` evaluates to `1/6`.

## Limits

- The route is an ideal block model, not a device binding or netlist.
- Resistor mismatch, finite open-loop gain and bandwidth, input offset, bias
  current, slew limiting, output saturation and source loading are not modeled.
- Inputs are normalized voltages; there is no physical voltage scaling.
- The target certificates are `target-simulated`, not live GLM or measured
  amplifier evidence.
- No fabrication, performance or optimality claim is made.
