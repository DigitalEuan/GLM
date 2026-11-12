# Declared Fabrication Geometry

`cent_compiler/fabrication.py` derives a millimetre-scale geometry from a
*selected* reference topology. It is a declared prototype geometry with an
independent rule check, **not** a manufactured, DRC-signed-off or measured
board. Every number remains an exact `Fraction`.

```bash
# Derived automatically (advisory) into a solved cent-design/1 result
python3 cent solve sqrt-log --range 1/2:1 --json

# Derive geometry, DRC, parasitics and thermal rows for a selected design
python3 cent fabricate sqrt-log --range 1/2:1

# Machine-readable payload
python3 cent fabricate delta-sigma --json

# HTTP API
GET  /api/fabricate?route=sqrt-log&range=1/2:1
POST /api/fabricate  {"route":"sqrt-feedback"}
```

The browser **Design solver** card exposes the same call as
**Fabricate geometry**.

## Pipeline

```
selected design (design.py)
  -> reference parts, nets and schematic stages (physical.py)
  -> generic footprint per part
  -> declared four-layer stackup
  -> channel placement: one row per stage + a quiet row for sensitive parts
  -> orthogonal escape/bus route
  -> exact lumped parasitics
  -> single-node junction temperatures
  -> independent design-rule check
```

The module consumes a `PhysicalPlan`; it does not re-solve the design or
replace any device quantity.

## Footprints and placement

Footprints are declared generic land patterns chosen by part kind and pin
count: `test-point-2`, `chip-0603`, `module-2` and `module-4`. Each carries a
body, a courtyard, a pad pitch, a pad count and a declared `theta_ja`.

Parts are packed left-to-right in one row per declared stage. Parts whose law
is temperature-sensitive (`BLOG`, `BANTI`, `EMULT`) are moved to a quiet row
below the stage rows. Pad columns are assigned so that pads of different parts
stay at least `pad_width + min_clearance` apart; the packer nudges a part right
until that holds.

## Stackup

Four declared copper layers, all 35 um thick, separated by 0.36 mm dielectric
with `epsilon_r = 22/5`:

| layer | kind | use |
|-------|------|-----|
| `top` | signal | pads and part bodies |
| `in1` | signal | vertical pad escapes |
| `in2` | signal | horizontal per-net buses |
| `bottom` | plane | inset ground plane |

Total declared thickness is `61/50 mm`. No impedance control, tolerance or
manufacturer stackup is implied.

## Router

Every non-ground multi-pin net gets:

1. a via from each pad to `in1`;
2. a vertical escape on `in1` at the pad column;
3. a via at the bus level;
4. one horizontal bus on `in2` spanning the net's pad columns.

Ground pins get a via straight to the bottom plane. Nets with a single pad are
*behavioral control labels* read by an ideal block (for example `level`, `off`,
`ref`, `thr` in delta-sigma, or `half` in the log route). They are reported in
`unrouted_nets` and are not copper-routed; the geometry does not invent a
connection that the reference topology does not declare.

## Parasitics

For each routed net, with `L` in mm, `w` in mm, `t = 35/1000 mm`:

- `R = rho * L / (w * t)`, `rho = 1.68e-8 ohm m`;
- `C = eps0 * eps_r * w * L / (1000 * h)`, a parallel-plate lumped estimate
  with `h = 0.36 mm`;
- `L_par = 1 nH/mm * L`, a declared per-unit-length constant.

These are first-order lumped estimates. There is no field solve, fringing,
skin effect, temperature coefficient or mutual coupling.

## Thermal model

For each part:

```
T_j = T_ambient + P * theta_ja
```

`P` is not invented. It is one of:

- delta-sigma `RIN`: worst-case `V_in^2 / R_in`;
- delta-sigma `RFB`: worst-case `V_ref^2 / R_in`;
- log-domain `RIN`: `V_in^2 / R_in`;
- log-domain `ROUT`: certified `|I_out|` upper bound squared times `R_out`;
- zero for ideal behavioral blocks and capacitors, with that boundary stated.

`T_ambient = 298 K`, `theta_ja` is declared per package. The model is a
single-node junction-to-ambient rise; there is no spreading, coupling,
transient heating or measured thermal resistance.

## Design-rule checks

`build_fabrication(plan, rules)` returns one `FabricationCheck` per rule, each
with status, exact compared value, exact limit and a detail string:

1. **Reference coverage** — every reference net and pad appears in the
   geometry.
2. **Net routability** — every non-ground net with at least two pads is routed;
   single-pin control labels are listed.
3. **Board edge** — all copper lies at least `edge_margin` inside the outline.
4. **Trace width** — every trace meets `min_width`.
5. **Footprint courtyards** — no two placed footprints overlap.
6. **Copper clearance** — different nets keep at least `min_clearance` on the
   same layer.
7. **Via annular ring** — `(via_pad - drill) / 2` meets `min_annular_ring`.
8. **Thermal keep-out** — sensitive parts keep `thermal_keepout` from
   dissipators, or no such pair is declared.
9. **Junction temperature** — the hottest declared junction stays below the
   limit.
10. **Stackup** — four positive copper layers and a dielectric are declared.

A failed check produces `status = "drc-gap"`; the geometry is still emitted so
the failure can be inspected. `DRCRules` rejects non-positive rules, a trace
below the minimum width, and a drill larger than the via pad.

`tests/test_fabrication.py` covers the three routes, exact dissipation and
parasitic formulas, placement rows, JSON safety, CLI/API behavior and forced
rule failures (bus pitch, thermal keep-out, junction limit, annular ring).

## Remaining gaps

- generic land patterns, not vendor drawings or DFM-verified pads;
- fixed orthogonal router, not a placement or routing optimiser;
- lumped parasitics without field solving or coupling;
- single-node thermal model without spreading or measurement;
- ideal blocks declare zero dissipation and no package/reliability model;
- no panelisation, impedance control, stackup tolerance, yield, EMC, safety or
  fabrication sign-off.
