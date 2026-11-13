# Orientation envelope

`cent envelope` is an exact computational method for a minimum-area bounding
rectangle over a **declared finite set of rational directions**. It is not a
physical simulation and does not require a physical realization.

## Method

For each point `p = (x, y)` and each nonzero rational direction `d = (dx, dy)`:

```text
u = dx*x + dy*y
v = -dy*x + dx*y
```

The `u` and `v` ranges define an enclosing rectangle. Its exact area is

```text
area = (max(u) - min(u)) * (max(v) - min(v)) / (dx^2 + dy^2)
```

because the projection basis has determinant `dx^2 + dy^2`. The four corners
are converted back to the original coordinates by the exact inverse:

```text
x = (dx*u - dy*v) / (dx^2 + dy^2)
y = (dy*u + dx*v) / (dx^2 + dy^2)
```

The method returns the minimum-area candidate over the declared direction set.
The default set includes the axes and several rational diagonals. Directions are
normalized to primitive integer pairs, so `(1,1)`, `(2,2)` and `(1/2,1/2)` are
one candidate.

## Commands

```bash
python3 cent envelope --point 0,1 --point 1,0 --point 0,-1 --point=-1,0
python3 cent envelope --point 0,1 --point 1,0 --point 0,-1 --point=-1,0 --json
python3 cent envelope --point 0,0 --point 2,0 --direction 1,1 --json
```

The diamond example has an axis-aligned area of `4` and a diagonal envelope of
area `2`.

## Contract

- Schema: `cent-envelope/1`
- Method: `finite-direction-minimax`
- Inputs: one or more exact rational points, plus optional rational directions
- Output: candidates, best direction, exact area, exact corners and containment
  checks
- `optimal_over_declared_directions: true`
- `global_optimal: false`

## Limits

- The minimum is over the finite declared direction set, not every real angle.
- The projected extents are not unit-normalized; the area is exact.
- No physical, optical, liquid-crystal or fabrication behavior is simulated.
- The result is a computational envelope, not a claim that a physical system
  realizes it.

A liquid-crystal or quadrupolar-orientation story can be attached as an optional
interpretation. It is not part of the method contract and is not a test
requirement.
