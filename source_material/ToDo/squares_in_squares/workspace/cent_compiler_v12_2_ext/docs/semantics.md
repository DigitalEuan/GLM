# Exact-core semantics (CentCalculus2)

This document fixes the conventions that the exact core checks. It is a
companion to the modules `exact`, `interval`, `port`, `density`, `geometry`,
`state`, `vocabulary`, `program`, `evaluator` and `resolution`. Where code and
document disagree, the code is wrong and a check in `tests/test_core.py` should
fail.

The v2.0 compiler in `cent_compiler/grammar.py` and friends is unchanged and
still uses floating point for its SPICE/simulation work. The exact core is a
separate execution layer; the two surfaces do not call each other.

---

## 1. Scalars are exact rationals

Every numeric wire carries a `fractions.Fraction`. There is no binary floating
point in the core:

| Input | Accepted? | Rule |
|-------|-----------|------|
| `int` | yes | exact integer, guarded at `MAX_BITS = 2^20` bits |
| `Fraction` | yes | as-is |
| decimal string `"0.1"` | yes | parsed through `decimal.Decimal`, so `q("0.1") == 1/10` |
| `float` | **no** | raises `type_error`; convert explicitly with `from_float_exact`, which yields the *stored dyadic value* (`0.1 → 3602879701896397/36028797018963968`) |
| `NaN`, `±inf` | **no** | no rational value exists, raises `domain_error` |

`from_float_exact` is the only float entry point, and it makes the loss of
intent explicit rather than silent.

### Error taxonomy

Failures are `CentError` values with a stable machine-readable code. They are
never caught and turned into a value; `resolution` records them instead.

| Code | Meaning |
|------|---------|
| `division_by_zero` | exact zero divisor, or an interval straddling zero |
| `domain_error` | argument outside the primitive's domain (log of a nonpositive, T ≤ 0, inconsistent port set) |
| `invalid_input` | malformed program, matrix, index or parameter shape |
| `unsupported` | unknown ¢ primitive, or an operation the core does not implement |
| `resource_budget_exhausted` | series/size budget hit before the requested precision |
| `validation_error` | missing/unknown parameter, double-assigned wire |
| `type_error` | value outside the ¢ type system |
| `cycle_detected` | combinational loop (a back edge not produced by a stateful primitive) |
| `approximation_unproved` | an enclosure invariant failed (defensive) |

---

## 2. Certified intervals

`sqrt`, `exp`, `log` and `π` return an `Interval` with exact rational
endpoints. Each enclosure is proved by construction, never by rounding a float:

| Function | Construction | Certificate |
|----------|--------------|-------------|
| `sqrt_q(x, p)` | scaled integer square root, `S = isqrt(n·d·4^p)` | `(S/(d·2^p))² ≤ x < ((S+1)/(d·2^p))²`, checked before return; perfect rational roots collapse to a point |
| `exp_q(x, p)` | halve until `|y| ≤ 1/2`, Taylor series, exact repeated squaring | Lagrange remainder `≤ 2|y|^{N+1}/(N+1)!` added as a positive upper bound |
| `log_q(x, p)` | `x = m·2^k`, `m ∈ [1,2)`, `atanh` series for `log m`, plus `k·log 2` | positive tail bound `2z^{2N+1}/((2N+1)(1−z²))` |
| `pi_interval(p)` | Machin: `π = 16·arctan(1/5) − 4·arctan(1/239)` | alternating-series (Leibniz) bracket per arctan |

`pi_interval` uses no float constant. Interval arithmetic is outward-rounded:
addition adds endpoints, multiplication takes the min/max of the four products,
reciprocal swaps endpoints, and a divisor whose interval contains zero raises
`division_by_zero` rather than producing an unbounded result.

**Widening rule.** A wire declared `numeric` may carry an interval (the consumer
must be interval-closed); a wire declared `interval` may carry an exact rational,
which is a degenerate enclosure. No other cross-kind assignment is allowed.

---

## 3. Wire kinds

| Kind | Python value |
|------|--------------|
| `numeric` | `Fraction` (or an interval, see above) |
| `interval` | `Interval` |
| `port` | `PhysicalPort(effort, flow)` |
| `field` | `ScalarField` |
| `vector_field` | `VectorField` |
| `two_form` | `TwoForm` |
| `vector` | tuple of `Fraction` |
| `bit` | `0` / `1` |

`Program` is single-assignment over named wires. Static analysis rejects
unknown primitives, unknown parameters, missing required parameters, wrong
arity, double assignment, unknown wires, kind mismatches, and combinational
cycles. Evaluation lives in `evaluator.py`; the checker never computes a value.

---

## 4. Tick semantics and state

A tick builds a fresh `EvalContext` over the pre-tick `MachineState`. Writes go
to a pending map; `commit()` produces the next state. A raised error discards
the pending map, so a failed tick leaves the machine byte-identical. Every
stateful *instruction* owns a slot keyed by its output wire: two `rate` nodes
in one program keep separate histories.

| Primitive | Slot contents | First-tick output |
|-----------|---------------|-------------------|
| `accum` | running sum | `0` |
| `rate` | previous input | `0` |
| `delay` | ring buffer of `ticks` | `initial` |
| `hysteresis` | latched bit | `initial` |
| `store_pot` | stored charge | `(0, 0)` port |
| `store_kin` | stored flux | `(0, 0)` port |
| `noise` | PRNG state word | `±amplitude` |
| `pid` | integral, previous error | `kp·e` |
| `phase_locked_loop` | VCO phase | `initial_phase` |
| `transmission_line` | delay cells | `initial` |
| `kalman_observer` | estimate, covariance | `initial_x` |
| `delta_sigma_modulator` | integrator(s), last bit | `0` |

### Feedback

An input wire produced later in the schedule is a **back edge**: it reads the
previous tick's value. A cycle is accepted only if *every* back edge is produced
by a stateful primitive; otherwise it is a combinational loop and rejected with
`cycle_detected`. On the first tick a back edge reads the producer's documented
initial value from the table above.

### Noise

`¢_noise` is a deterministic two-point law: `+a` or `−a` with probability `1/2`,
driven by SplitMix64 seeded per instruction. Its mean is `0` and its second
moment is exactly `a²`. It is a deterministic stream, **not** a physical entropy
source; `test_core.py` checks both the support and the exact second moment.

---

## 5. Ports and sign conventions

A port is a conjugate effort/flow pair; instantaneous exact power is `e·f`,
positive when delivered.

| Element | Map | Power |
|---------|-----|-------|
| 0-junction (common flow) | resolved `e = −Σ other e` | `Σ e·f = 0` |
| 1-junction (common effort) | resolved `f = −Σ other f` | `Σ e·f = 0` |
| gyrator `G(r)` | `(e, f) ↦ (r·f, −e/r)` | exactly negated |
| transformer `T(n)` | `(e, f) ↦ (e/n, −n·f)` | exactly negated |
| transducer `η ∈ (0,1]` | `(e, f) ↦ (k·e, −η·f/k)` | loss `= P_in + P_out ≥ 0` |
| dissipator | `f = e/R`, entropy rate `P/T` | `P = e²/R ≥ 0` |
| entropy | `P/T`, requires `P ≥ 0` and `T > 0` | active ports are rejected |

Note the gyrator minus sign. The frequently quoted pair `e₁ = r·f₂`,
`e₂ = r·f₁` is *not* power conserving (`P₁ + P₂ = 2r·f₁·f₂`); the
power-preserving convention is the one implemented and tested. A junction whose
inputs violate its constitutive constraint (mixed flows on a 0-junction, mixed
efforts on a 1-junction) raises `domain_error` instead of averaging
inconsistent data.

`thermo_electric` returns a thermal port with effort `T` and flow
`(S·T·I + I²·R)/T`, so its power is the Peltier plus Joule heat; the sign is
physical and may be negative (cooling).

---

## 6. Spatial carriers and stencils

A point in the 24-D carrier is not a field. `geometry.py` separates
`Carrier24` (an exact point), `ScalarField` (a samplable scalar field),
`VectorField` (component fields) and `TwoForm`.

All stencils are central differences with spacing `h > 0`:

| Operator | Formula | Result |
|----------|---------|--------|
| `grad ψ` | `(ψ_{i+1} − ψ_{i−1}) / 2h` per axis | 24-component vector field (unused axes are identically zero) |
| `div v` | `Σ ∂ᵢvᵢ` | scalar |
| `curl v` | `ωᵢⱼ = ∂ᵢvⱼ − ∂ⱼvᵢ` | antisymmetric 2-form, `C(24,2) = 276` independent components |
| `laplacian ψ` | `Σ (ψ_{i+1} − 2ψᵢ + ψ_{i−1}) / h²` | scalar |

Because central differences commute exactly over rationals, `curl ∘ grad = 0`
and `div ∘ curl = 0` hold **identically** on interior points for these stencils;
both are checked exactly in `test_core.py`. `curl_3d` is the documented
three-component projection of the 2-form, not the object itself.

### Boundary conditions

`GridDomain` carries one condition for all faces:
`αψ + β(∂ψ/∂n) = γ`, with the outward derivative discretised as
`(ψ_face − ψ_interior)/(h·gap)`. Therefore

```
ψ_face = (γ + β·ψ_int/(h·gap)) / (α + β/(h·gap))
```

Dirichlet fixes `ψ_face = value`; Neumann (`β ≠ 0, α = 0, γ = 0`) mirrors the
interior sample, giving a zero one-sided difference; Robin uses the formula
above and raises `domain_error` when the denominator vanishes. `¢_boundary`
in a program is a projection operator: it resamples a field through the
declared domain and condition.

---

## 7. Layered resolution

`resolution.resolve(candidates, run, layers)` tries each candidate through each
fidelity layer (`ideal → parasitic → thermal → quantum → fabricated` by
default), records every failure as a structured `Attempt`, and returns:

| Status | Meaning |
|--------|---------|
| `converged` | one candidate survived every layer |
| `diverging` | no candidate survived some layer |
| `refused` | `strict=True` and the first candidate failed the first layer |

The trace is never discarded: `Resolution.failures` keeps each
`CentError.as_dict()` payload. `require_converged` converts a non-converged
resolution into `approximation_unproved` rather than returning a substitute
value.

---

## 8. Material bundles and the exact program format

`cent report --save DIR` writes a self-contained bundle (`cent-material/1`):

| Key | Contents |
|-----|----------|
| `relation`, `target`, `expression` | the £ as typed and as parsed |
| `dag` | declared inputs/outputs and every `COp` with its `const` |
| `summary` | primitive census, atomic/composite split, ∆ counts |
| `program` | a `cent-program/1` exact program, or `null` |
| `bindings` | initial values for synthetic wires (`_one` for numeric literals) |
| `spice` | chosen template name and the netlist text |
| `notes` | why an exact program is unavailable, when it is |

Program JSON encodes every rational as `{"num": "...", "den": "..."}`, so a
bundle round-trips without a float. `program_from_dict` re-validates the loaded
program with the same static checker used at compile time. `run_material`
supplies the bundle's `bindings`, accepts overrides, defaults any remaining
numeric input to `0`, and refuses to invent a value for any other kind of
input.
