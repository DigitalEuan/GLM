# Entering a £

A **£** is one abstract relation: a target name followed by an expression.

```text
target = expression
```

Use ASCII, put the whole relation in quotes in the shell, and keep it on one
line. The target is a label, not a unit declaration.

## Accepted syntax

| Form | Meaning |
|---|---|
| `+`, `-`, `*`, `/` | arithmetic |
| `^`, `**` | exponentiation |
| `(`, `)` | grouping |
| `sqrt(x)` or `x^(1/2)` | square root |
| `exp(x)` | exponential |
| `log(x)` or `ln(x)` | natural logarithm |
| `tanh(x)` | saturation-shaped nonlinearity |

Numeric literals are parsed exactly as rationals where the expression allows
it. An unsupported function or malformed expression produces an explicit
parser error; the compiler does not guess a replacement. The error names the
nearest accepted function when one is close, lists the accepted forms, and ends
with a fixed copyable example. It never rewrites your relation into a made-up
one.

## First examples

```bash
# Mechanical / electrical relation
python3 cent compile "velocity = (2 * energy / mass)^(1/2)"

# Simple compute relation
python3 cent compile "y = sqrt(5)"

# Fluidic relation
python3 cent compile "pressure = force / area"

# Thermal relation
python3 cent compile "heat_rate = thermal_conductivity * area * temperature_gradient"

# Tooling view: ranked proposals, cost breakdown and certificate
python3 cent compile "y = sqrt(5)" --json
```

`--top N` is a ranking view, not a domain quota. It shows the first N distinct
domain/carrier/∆Σ signatures; it does not promise that every declared domain
appears in those rows.

The same command is used for every domain. The ∆ catalogue is not restricted to
electrical implementations; the ranking may still choose an electrical one if
its declared cost is lower. The proposal must show that reason rather than hide
the domain choice.

## What the compiler does

```text
£
  -> parse target and expression
  -> decompose into a typed ¢ DAG
  -> enumerate declared ∆ candidates across domains
  -> rank by exact ¢_cost and prune duplicates
  -> select the rank-1 proposal
  -> emit a structural SPICE template or an explicit template gap
```

`cent compile` is the compact view. `cent report` adds the material bundle,
exact-core program and saved artifacts. `cent ui` provides the same report in an
interactive shell. `cent discover` is for a problem statement, not a single
relation.

## Reading the result

1. **¢ DAG** — each operation, its inputs and its declared factor.
2. **∆ enumeration** — total candidates and delta-sigma count.
3. **Ranked ∆** — cost, domain, carrier and component list, followed by the
   rank-1 cost-axis rationale.
4. **Proposal** — rank-1 netlist when the full operation set matches a declared
   template. The template decision is structural: it has
   `proposal_effect: none`, and a missing template never removes or demotes a
   ranked ∆ proposal. The JSON form repeats the six cost axes and the
   `not-fabricated` boundary for every proposal, plus `spice.decision`.
5. **Gaps** — a missing template, material, fabrication or measurement is not a
   pass. Every ranked row is a declared proposal, not a fabricated or measured
   device; the text and JSON outputs state this boundary explicitly.

## Troubleshooting

- `parse: ...` from the parser: check parentheses, operators and function
  names. `nearest accepted function` and `example` are safe next steps, not a
  rewritten relation.
- No ∆ candidates: the ¢ DAG may be outside the declared substrate catalogue;
  this is a declared gap, not a reason to invent a route.
- No SPICE template: the complete ¢ operation set does not match; inspect the
  template detail. This is a template gap only; the ranked ∆ proposals remain
  intact, including non-electrical candidates.
- A non-electrical answer: compare the domain and carrier columns; cost ranking
  is not a physical proof.

For the architecture behind these stages, see
[`CENT_FRAMEWORK.md`](CENT_FRAMEWORK.md). For the forward plan, see
[`../PHYSICAL_COMPILER_ROADMAP.md`](../PHYSICAL_COMPILER_ROADMAP.md).
