# Fluid pipe-junction sum and difference route

This note records the route-design choice for the second independent method for
a non-`sqrt` operation. The route is `sum-fluid`: an exact normalized sum or
reversed-port difference at a declared fluid pipe junction.

## Why this route

The declared `sum` substrate rows were compared before selecting one:

| Declared row | Domain | Law | Decision |
|---|---|---|---|
| KCL node | electrical | `ΣI_in = ΣI_out` | Existing baseline route; not independent. |
| KVL loop | electrical | `ΣV = 0` | Same electrical domain; a loop sum is not a two-input sum without an added source convention. |
| Rigid body | mechanical | `ΣF = m·a` | Requires a mass/inertia value and a choice between net-force and acceleration outputs; neither is declared for the `sum` contract. |
| Rigid rotor | rotational | `Στ = I·α` | Same missing inertia/output-convention issue. |
| Pipe junction | fluidic | `ΣQ_in = ΣQ_out` | Two normalized flows produce the sum directly; no extra physical parameter is declared or invented. Selected. |

The choice is not a claim that the fluid row is uniquely optimal. It is the
candidate that preserves the declared two-input `sum` contract with the fewest
new assumptions and the clearest exact audit.

## Contract

- Route id: `sum-fluid`
- Kind: `exact-fluid-sum`
- Component: `fluid pipe junction (continuity node)`
- Source: `DELTA_SUBSTRATE: sum / fluid pipe junction`
- Law: `q_total = q_a + q_b at a declared flow-conservation junction`
- Difference law: `q_total = q_a - q_b` via a declared reversed port
- Ports: `q_a`, `q_b` (normalized exact flows), `q_total`
- State: none
- Sum program: one exact `sum` instruction; no hidden physical constant or `sqrt`
- Difference program: exact `neg` on `q_b`, then the same exact `sum`

The route carries a `topology_audit` and a typed `cent-typed-graph/1` with one
component node and no feedback edge. It is registered as the
`fluid-continuity` mechanism card, so `cent transfer sum` and
`cent transfer difference` retrieve it alongside `kcl-conservation`. The
independent `glm-reference` adapters execute `exact_fluid_sum` and
`exact_fluid_difference` over three fixed normalized-flow vectors each. Either
mechanism can be selected explicitly with `--mechanism`; without one, retrieval
order selects fluid first.

## Run it

```bash
python3 cent assemble sum-fluid --input 1/2 --input-b 1/3
python3 cent assemble sum-fluid --operation difference --input 1/2 --input-b 1/3
python3 cent assemble sum-fluid --input 1/2 --input-b 1/3 --json
python3 cent graph sum-fluid --operation difference --json
python3 cent matrix --operation difference --json
python3 cent transfer "sum" --mechanism "fluid-continuity" --validate --json
python3 cent transfer "difference" --mechanism "fluid-continuity" --validate --json
```

`1/2 + 1/3` evaluates to `5/6`; `1/2 - 1/3` evaluates to `1/6`. The operation
matrix exposes both `sum-kcl` (electrical) and `sum-fluid` (fluidic) as exact
`sum` and `difference` routes. The mechanism registry exposes the same
separation as `kcl-conservation` and `fluid-continuity`, and the target adapters
certify the normalized-flow arithmetic against the source routes. They are
`target-simulated`, not physical flow measurements.

## Limits

- Inputs are normalized flows; there is no pressure/flow scaling or device
  binding.
- Leakage, compressibility, junction loss and finite response are not modeled.
- The target certificate covers normalized arithmetic only; there is no
  reference netlist, fabrication geometry or measured-flow evidence.
- The route is a declared substrate method, not a proof that fluidic continuity
  is a physical realization of an abstract addition or subtraction device.
- Reversal is an ideal signed-flow convention; no valve, pump or measured
  reversal mechanism is modeled.
- No isomorphism, performance or optimality claim is made.

The KCL physical path remains blocked on declared values; the fluid route does
not remove that gap or claim a fabricated junction.
