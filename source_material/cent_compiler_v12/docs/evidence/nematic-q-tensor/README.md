# Nematic Q-tensor evidence

This is a computational audit of the lead
`nematic-q-tensor-bounding-box`. It makes no liquid-crystal, optical or
fabrication claim.

## Definition

For a uniform two-dimensional nematic field, use the symmetric traceless
Q-tensor

```text
Q = S * (2 n n^T - I2)
n = (cos(theta), sin(theta))
||n|| = 1
S in [0, 1]
n ~ -n
```

`S` is the scalar order parameter and `n` is the director. The field is uniform:
there is no spatial boundary-value problem in this test. The sign equivalence
`n ~ -n` is the standard director redundancy. At `S = 0` the tensor is isotropic
and has no director.

The `+S` eigenvector is `n`; the `-S` eigenvector is `n_perp = (-n_y, n_x)`.

## Invariants

For the matrix above:

```text
tr(Q)   = 0
tr(Q^2) = 2 S^2
det(Q)  = -S^2
```

The two scalar invariants depend only on `S`. For a fixed `S` they are identical
for every director angle `theta`. The orientation is carried by the eigenvector,
not by the scalar invariants.

## Proof of the obstruction

Set `S = 1` and compare two exact Q-tensors.

For `n1 = (1, 0)`:

```text
Q1 = [[ 1,  0],
      [ 0, -1]]
```

For `n2 = (3/5, 4/5)`:

```text
Q2 = [[-7/25, 24/25],
      [24/25,  7/25]]
```

Both have:

```text
tr(Q1^2) = tr(Q2^2) = 2
det(Q1)  = det(Q2)  = -1
```

Therefore any function `F(tr(Q^2), det(Q))` returns the same value for `Q1` and
`Q2`. It cannot select the `n1` eigenframe over the `n2` eigenframe, and it
cannot produce different finite-direction projections for the two tensors.

So a map from the scalar Q-tensor invariants alone to the envelope's
finite-direction projections does not exist. The missing input is orientation,
not another scalar definition.

Using the full Q-tensor changes the statement: the `+S` eigenvector supplies
`n`, and the direction set can be `{n, n_perp}`. That bridge exists, but it is
orientation-only; it uses the eigenvector and does not use `tr(Q^2)` or `det(Q)`.
It is a rotation of the envelope, not an invariant map. The scalar order `S`
does not affect the envelope directions.

## Exact comparison

For the point set

```text
(0, 0), (2, 0), (0, 1)
```

the eigenframe directions produce:

```text
Q1 directions (1,0), (0,1)       -> exact area 2/1
Q2 directions (3/5,4/5), (-4/5,3/5) -> exact area 66/25
```

The invariants are identical; the envelopes are not. `check.py` asserts the
matrices, the invariants, the two exact areas and the differing best directions.

## Consequence

The original lead's first need, “map Q-tensor invariants to the envelope's
finite-direction projections”, cannot be met as worded. Retiring this lead is
therefore based on a proved obstruction, not on a missing file.

A separate lead for the orientation-only eigenframe bridge could be declared,
but it would have to state that the scalar invariants do not participate. It
should not inherit the original invariant claim.

## Reproduce

```bash
python3 docs/evidence/nematic-q-tensor/check.py
```
