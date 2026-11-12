# Typed wheel bridges and graph grounding

Discovery carries three distinct wheel-evidence classes: exact **graph-proof**
relations from the global axiom graph, explicit **declared-bridge** mappings,
and non-scoring **text-only** candidates. A text hit is not a proof or a port
mapping. This note documents the declared bridge layer and the graph-grounding
query that sits beside it.

The implementations are `cent_compiler/wheel_mapping.py` and
`cent_compiler/axiom_graph.py`.

## 1. What a declared bridge contains

A bridge is selected only when all of the following match:

- the exact primitive;
- the route kind (for example `certified-enclosure`);
- the wheel id;
- an explicit bridge law;
- route ports and device quantities that actually exist in the method payload;
- unit strings that agree with the expected dimensions;
- wheel quantities whose SI exponent vectors can be read.

The result records:

| Field | Meaning |
|---|---|
| `bridge_id` | stable declared bridge name |
| `bridge_law` | equations connecting route, device and wheel quantities |
| `ports` | method port → device symbol → wheel quantity |
| `quantities` | auxiliary device quantity → wheel quantity |
| `wheel_dimension` | dimensions read from `wheels/*.json` |
| `expected_dimension` | dimensions declared independently by the bridge |
| `residual` | non-zero axis differences; empty means the vectors agree |
| `status` | `declared` only when every check passes; otherwise `gap` |
| `gaps` | missing data, unit mismatch or the limits of the claim |

`status: declared` means **declared dimensional bridge**, not axiom proof,
semantic identity, measured device model or fabrication netlist.

## 2. The first bridge: log-domain square root ↔ W24

The log-domain route is the exact compute route that evaluates
`exp((1/2) ln x)` with a diode log/antilog pair.  Its declared device binding
has the matching semiconductor quantities.  The bridge connects them to
**W24 Semiconductor Device Physics**.

### Ports

| Route port | Device quantity | Wheel quantity | Unit | Residual |
|---|---|---|---|---:|
| `x` | `I_in` | `current` | A | 0 |
| `root` | `I_out` | `current` | A | 0 |

The mapping uses the declared device relations:

```text
I_in  = I_ref * x
I_out = I_s * root
V_out = R_out * I_out
```

`root` is the normalized antilog current; the output resistor converts
`I_out` to the physical output voltage.  The bridge records that conversion
instead of pretending the wheel's current is the final voltage.

### Auxiliary quantities

| Device quantity | Wheel quantity | Unit | Residual |
|---|---|---|---:|
| `V_T` | `thermal_voltage` | V | 0 |
| `I_s` | `saturation_current` | A | 0 |

The bridge law is:

```text
I_in = I_ref*x
I_out = I_s*root
V_T = k_B*T/q
I_out = I_s*exp((1/2)*ln(I_in/I_s))
V_out = R_out*I_out
```

The dimension vectors come directly from `wheels/W24.json`; the expected
vectors are declared independently in the bridge table.  The `residual` field
is empty only when every axis agrees.

### Discovery output

The log-domain candidate now carries:

```text
wheel bridge: W24 declared [x→I_in→current, root→I_out→current]; residual=0
```

The other sqrt candidates carry graph proofs for W21/W25/W29.  The
analog-feedback candidate's W24 match remains text-only and has no declared
bridge:

```text
wheel graph proof: W21 axiom:W21:01 → (...)^(1/2)
wheel graph proof: W25 axiom:W25:01 → (...)^(1/2)
wheel graph proof: W29 axiom:W29:01 → (...)^(1/2)
wheel grounding gap: text-only candidates are not scored: W24
```

This is intentional.  A shared square-root symbol or an electrical word is not
enough to claim a semantic mapping or graph proof.

## 3. JSON shape

Each method now has a `wheel_mappings` list parallel to `wheel_material`:

```json
{
  "wheel": "W24",
  "status": "declared",
  "bridge_id": "log-domain-diode-w24",
  "bridge_law": "I_in = I_ref*x; ...",
  "ports": [
    {
      "method_port": "x",
      "device_symbol": "I_in",
      "wheel_quantity": "current",
      "unit": "A",
      "expected_dimension": {"I": "1"},
      "wheel_dimension": {"I": "1"},
      "residual": [],
      "status": "pass"
    }
  ],
  "residual": [],
  "residual_empty": true
}
```

A candidate without a bridge has `status: "gap"`, `bridge_id: null` and an
explicit reason.  A candidate with a bad dimension also has `status: "gap"` and
a non-empty `residual`.

## 4. Graph-backed grounding

`axiom_graph.ground_primitive(op)` replaces keyword selection for primitives
with a declared exact relation query. The current queries are:

| Primitive | Relation query | Acceptance |
|---|---|---|
| `sqrt` | `half-exponent` | an axiom contains a quantity with exponent `±1/2` |
| `mult` | `product` | one positive target is a product of at least two negative-exponent inputs |

Each candidate must re-derive its target from the other quantities with exactly
one declared axiom. The result carries the axiom id, equation, target, inputs,
exact exponents, formula, and proof steps. Discovery exposes it as
`wheel_grounding.candidates` with `basis: graph-proof`.

A primitive with no declared monomial query, such as `log` or `delay`, returns
`status: gap` and no candidates; it never falls back to `WHEEL_TERMS`. A
declared nonlinear bridge such as the W24 Shockley law is listed separately
under `declared_bridges` and is not presented as a graph proof. Text matches
remain under `wheel_material`/`wheel_grounding.text_only` for inspection only
and do not earn grounding score.

## 5. Limits

- This is a **declared bridge table**, not inference over the global axiom
  graph.  Only the log-domain/W24 combination is registered so far.
- A zero dimensional residual is necessary but not sufficient for a physical
  analogy.  The bridge law and the declared semantics carry the rest of the
  claim.
- No bridge is a proof, a quantity measurement, a netlist or a layout.
- No cross-wheel junction is traversed automatically.  The bridge table is
  scoped to W24, and no second bridge is manufactured from a junction.
- The bridge does not claim that a thermal voltage is an arbitrary signal
  voltage; the auxiliary quantity is mapped to the wheel quantity that actually
  supplies the diode slope.

## 6. Checks

```bash
python3 tests/test_discovery.py
python3 cent discover "compute an irrational value with an analog method"
```

`test_discovery.py` checks the declared bridge, both port mappings, the
auxiliary thermal-voltage quantity, the empty residual, an explicit gap for the
op-amp candidate, rejection of a deliberately mismatched dimension, the
W21/W25/W29 graph proofs, and the non-scoring `text_only` W24 candidate on the
op-amp route.

D4 is complete for exact monomial graph grounding and declared-bridge
separation. Proving arbitrary nonlinear physical laws from the wheel axioms is
not claimed and remains outside the graph algebra.
