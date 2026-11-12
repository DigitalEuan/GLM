# Bresenham / delta-sigma evidence

This audit separates a real exact correspondence from a false claim about the
existing route. No graphics, hardware or performance claim is made.

## Definition

Take an integer line from `(0,0)` to `(dx,dy)` with `dx > 0` and
`0 <= dy <= dx`. The integer DDA member of the Bresenham error-accumulation
family is

```text
y_n = floor(n * dy / dx)
q_n = y_{n+1} - y_n  in {0, 1}   for n = 0..dx-1
r_n = n * dy / dx - y_n
```

This is the declared member used here. It is not the centered-phase tie variant;
the proof and test apply to this exact floor/DDA convention.

The declared one-tick floor delta-sigma reconstruction is

```text
r_0 = 0
for each step:
    r += dy / dx
    q = floor(r)
    r -= q
```

One delay, one accumulator, one feedback subtraction. This is a one-tick
variant. It is **not** the existing two-tick nearest-level route in
`cent_compiler/targets/glm.py`.

## Proof

Claim: for every `n` before `dx`,

```text
r_n = n * dy / dx - y_n
```

Base: `r_0 = 0 = 0 - y_0`.

Step: `q_n = floor(r_n + dy/dx)`. Since

```text
r_n + dy/dx = (n+1)dy/dx - y_n
```

the floor is `y_{n+1} - y_n` by the definition of `y_{n+1}`. Therefore

```text
r_{n+1} = r_n + dy/dx - q_n
        = (n+1)dy/dx - y_{n+1}
```

The update and the line walk are the same sequence. This is exact rational
arithmetic; there is no approximation or floating-point step.

The output mean obeys

```text
sum(q_n) / dx = y_dx / dx = dy / dx
```

because `y_dx = floor(dx * dy/dx) = dy`. The prefix state is the exact fractional
part of `n dy/dx`.

## Exact test

`check.py` compares the line walk and the one-tick loop for every integer pair

```text
1 <= dx <= 32
0 <= dy <= dx
```

and additionally checks representative sequences. It also compares the existing
two-tick target:

```text
input 1/2, 6 samples:
  Bresenham/one-tick  0 1 0 1 0 1
  existing target     1 1 1 0 0 0
```

The two-tick feedback history changes the code sequence. Other declared vectors
show the same mismatch. So the lead is valid for the one-tick variant, but it is
not an equivalence proof for the existing two-tick `quantized_carry` route.

## Negative control

The stateless uniform quantizer in
`cent_compiler.targets.glm.uniform_quantizer_carry` is not an error-feedback
walk. For `dy/dx = 3/8` it emits a constant zero code; the Bresenham walk emits
ones. The check asserts that difference. The control is not a Bresenham
implementation and must not be promoted as one.

## Consequence

Keep the lead only as a narrowed one-tick variant: the proof, exact test and
negative control meet the three declared needs for that variant. Do not claim
equivalence to the existing two-tick target. Promotion would require a separate
mechanism card and route with the one-tick timing declared.

## Reproduce

```bash
python3 docs/evidence/bresenham/check.py
```
