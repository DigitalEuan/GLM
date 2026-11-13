# Reference netlist and schematic floorplan

`cent physical` adds a topology-derived physical artifact to a **selected**
declared design. It is deliberately narrower than a fabrication flow:

```text
exact selected device binding
  -> declared route roles and component values
  -> reference part list + connected nets
  -> SPICE-shaped behavioral deck
  -> schematic stage floorplan in declared grid units
  -> checks and explicit fabrication gaps
```

The implementation is `cent_compiler/physical.py`; focused tests are in
`tests/test_physical.py`.

## Usage

```bash
python3 cent physical delta-sigma
python3 cent physical sqrt-log --range 1/2:1
python3 cent physical sqrt-feedback --json
```

`--input`, `--range`, `--accuracy`, `--max-cost` and `--min-bandwidth` use the
same exact constraints as `cent solve`. If no declared design satisfies them, the command
exits with status 2 and emits nothing.

The browser **Design solver** tab exposes the same operation after a successful
solve. The HTTP endpoint is:

```text
GET  /api/physical?route=sqrt-log&range=1/2:1
POST /api/physical  {"route": "delta-sigma", "accuracy": "1/500"}
```

The response wraps a `cent-physical/1` payload under `physical`.

## Parts and topology

The part list is derived from the selected route and binding, not from the old
template-based `spice_emitter.py`.

| Route | Declared stages | Reference parts |
|---|---|---|
| `delta-sigma` | input, integrator, quantizer, feedback | `VIN`, `RIN`, `CINT`, ideal `EINT`, threshold/offset sources, comparator `BQ`, reference, feedback resistor and switch |
| `sqrt-log` | input, logger, half-gain, antilog | `VIN`, `RIN`, exponential junction `BLOG`, `EDIV`, antilog source `BANTI`, `ROUT` |
| `sqrt-feedback` | input, error amplifier, multiplier | `VIN`, `VREF`, finite-gain `EOUT`, multiplier feedback `EMULT` |

Ideal behavioral blocks are labelled in their notes. They are not vendor
models or transistor-level circuits. The log junction is represented by the
declared exponential law `I = I_s exp(V/V_T)` and the antilog by its inverse;
the feedback route uses the declared finite-gain loop.

## Exact values versus SPICE representation

Every numeric part value remains an exact rational in the JSON payload, encoded
as `{"num": "...", "den": "..."}`. Exact parameter values such as `V_T`, `I_s`
and `k` are also retained under `parameters`.

SPICE has no rational literal, so numeric fields use deterministic decimal
text. The exact authority remains the JSON and the underlying binding. The deck
header states this explicitly.

## Floorplan

The geometry is a **schematic stage floorplan**:

- integer coordinates in a declared schematic grid unit;
- one non-overlapping rectangle per stage;
- parts assigned to their stage;
- net-derived links between stages;
- no millimetres, footprints, copper, stackup, keep-outs, DRC or thermal
  placement.

The canvas and block coordinates are exact integers, so overlap is checked
without floating point. The `coordinate_unit` and `gaps` fields state that this
is not manufacturing geometry.

## Checks and remaining gaps

The payload contains status rows for:

- selected design availability;
- exact part values or declared behavioral expressions;
- unique references, connected nodes and stage roles;
- floorplan assignment and non-overlap;
- route-role coverage;
- SPICE emission;
- fabrication geometry (`gap` in this payload; `cent fabricate` derives a
  declared prototype geometry separately).

The emitter checks structure, not electrical performance. It does **not** claim
that the deck simulates, converges, meets bandwidth/stability/noise limits, or
can be fabricated. Those remain explicit gaps alongside the missing BOM,
parasitics, DRC, thermal model and measured-device evidence. The separate
[`DYNAMICS.md`](DYNAMICS.md) layer runs the declared sampled and nonlinear
transients; it does not validate this SPICE deck.

## Tests

```bash
python3 tests/test_physical.py   # 36 checks
python3 tests/test_design.py     # 60 checks
python3 tests/test_webui.py      # 92 checks, including /api/physical, /api/dynamics and /api/compare
```

The physical suite covers all three routes, exact value preservation, net and
stage mapping, non-overlap, JSON safety, the no-solution path, CLI JSON/human
output and the non-fabrication wording.
