# Pressure Settling Engine — packing as a cross-domain relaxation

`cent discover "find an optimal 2D square packing for n squares"` now returns a
declared **Pressure Settling Engine** candidate. It is built from two wheels
that were already present:

- **W36 — Numerical SAT Substrate:** `pair_energy = pair_penetration^2` and
  `wall_energy = container_violation^2`.
- **W37 — Viscoelastic Settling:** `relaxation_time = viscosity / modulus` and
  `strain_rate = stress / viscosity`.

The declared junction reads W36 `pair_penetration` as W37 `stress`. The
primitive chain is `mult → sum → div → scale → accum → sat → dissipate`.

## What is implemented

`cent_compiler/packing.py` is an exact-rational probe for **axis-aligned unit
squares in a fixed square container**. It measures the W36 objective

```text
sum(pair_penetration^2) + sum(container_violation^2)
```

and performs a deterministic projection along each pair's minimum-penetration
axis. The relaxation fraction is

```text
alpha = min(1, dt / (viscosity / modulus))
```

so the W37 relaxation time is used rather than an undeclared damping constant.
The exact probe can reduce overlap and wall violation to zero for a declared
initial state.

```bash
python3 cent packing --n 2 --side 3 --iterations 12
python3 cent packing --n 2 --side 3 --iterations 12 --json
```

The default probe starts both unit squares at the container centre. Its first
state has energy `1`; the final state has zero overlap and zero wall violation.

## What is not claimed

This is a **feasibility heuristic**, not an optimal square-packing solver:

- it does not search all configurations;
- it has no lower bound or global optimality certificate;
- it only handles axis-aligned unit squares in a fixed container;
- it has no rotation, arbitrary square-size or variable-container search;
- it is a declared computational analogy, not a physical device;
- there is no device binding, fabrication netlist or measured result.

The method card therefore keeps `optimality: not claimed` and a first gap of
“no global optimality certificate or exhaustive configuration search.” The
response corrects the earlier audit finding: `cent` should propose this
cross-domain method, while still refusing to call its output optimal.

The method also records a **39-wheel scan**. W36 and W37 are selected because
together they declare the objective and relaxation laws. Adjacent candidates
such as W5 force/energy, W6 pressure/force, W21 stress/energy, W32/W34
viscosity/pressure and W40 stress/force are listed but not promoted: they do
not declare both the squared-penetration objective and the relaxation law.

## Why discovery previously missed it

The old query path looked for an exact vocabulary primitive. `packing` is not a
`¢` primitive, so the query stopped before the wheel search. The new path
decomposes the problem into overlap energy, stress/relaxation and container
constraints first, then exposes the W36/W37 material. This is the intended
operation → primitive → cross-domain-isomorphism path, not a search restricted
to a “packing domain.”
