# Run 91 — one gate, parametrised by its field

Run 90 added the higher rungs by *copying* `qsqrt2.gate` into `glm_wheels` and
parameterising the copy. That left two decision procedures where there should be one, and
a control that compared them on three sentences. This run removes the copy, moves the
field argument into `qsqrt2`, and widens the control to every spatial cell.

## 1. The gate takes a field class

`qsqrt2`'s gate functions now accept `cls` — the `exact_field.Quad` subclass — with the
default read off the state:

```python
def field_of(state, cls=None):
    if cls is not None:
        return cls
    for p in state:
        if p is not None:
            return type(p[0])
    return Q2
```

and every constant inside is built from it: `cls(F(1, 2))` for the half-extent,
`cls(2)` for the prune, `cls(0)` for the empty sentence. `frame_extent`, `axis_extent`,
`side`, `pair_axes` and `gate` each take `cls=None`.

Two consequences, both deliberate:

- **every existing caller is unchanged.** `Q.gate(state, words)` still infers `Q2` from a
  Q(√2) state, and the numbers it returns are the same objects it returned before — the
  old code hard-coded `HALF` and `Q2(2)`, which are exactly `cls(F(1,2))` and `cls(2)`
  for `cls = Q2`.
- **a higher rung is verified by the same procedure**, not by a faithful copy of it:
  `g = Q.gate(state, words, cls)` in the ridge builder, and the witnesses go through
  `gate_of(claim)` / `pairs_of(claim, i, j)`, which pass the claim's field class.

## 2. What was deleted

`glm_wheels` no longer carries `qgate`, `qpairs`, `qside`, `qframe_extent` or
`qaxis_extent` — about 60 lines of duplicated algebra. Also removed, because run 90 left
them unused: `field_class(claim)` (nothing called it; `gate_of` reads the discriminant
directly) and `sqrt_in(d, n)` (written for a `sqrt`-in-field path the families do not
take — `unit_word` computes the coefficients itself).

The float audit drops from 197 to **191** decision functions: seven helpers removed, one
added (`field_of`), which is the arithmetic the audit is meant to make visible.

## 3. Control 21 now compares on every spatial cell

Instead of three sentences, the control builds **every cell of the spatial wheel** through
the domain (`pk.build(cell.family, **cell.params)`, the same path `Wheel.spin` uses) and
checks, for all 40:

- `Q.gate(state, words)` (field inferred) and `Q.gate(state, words, cls)` (field declared)
  agree on `ok`, `L`, `clearance`, `contacts` and `violations`;
- `gate_of(claim)` — the witness path — equals that verdict;
- and for **every pair** in the sentence, `Q.pair_axes(...)` and `pairs_of(claim, i, j)`
  produce the same axis vectors and the same slack signs.

That is the real claim: the parametrisation is transparent, cell by cell and pair by pair,
across Q(√2), Q(√5) and Q(√7) sentences. The ridge assertions stay (the 45° member equals
`S(k,1)`; every rung gates at clearance 0 with its exact side and its calibration).

## 4. Verification

| check | result |
|---|---|
| `glm_wheels --selftest` | **21 controls**, exit 0; control 21 covers 40 cells |
| `glm_wheels` spin | spatial **40/40**, sequences 6/7, lattice 24/28 |
| `glm_wheels --audit` | **191 functions, 0 offenders** (was 197) |
| `qsqrt2 --selftest` | 11/11 — the parametrised gate still passes the cage controls |
| `grammar_induction --selftest` | 3/3 |
| `field_triage --selftest` | 4/4 |
| `record_guard.py` | OK |

## 5. What this run does not claim

No number moved: not a cell's N, L, void or gain, not a verdict, not a row of the table.
This is a refactor of where a decision procedure lives, plus the deletion of two helpers
that nothing called. `submission.csv` and the root whiteboard are untouched.

Entries `54-ONE-GATE.md`; records `31`–`54`.
