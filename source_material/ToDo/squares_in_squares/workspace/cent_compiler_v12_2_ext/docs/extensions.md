# Extensions: the expanded ¢ vocabulary

`cent_compiler/vocabulary.py` is the single source of truth for what the exact
core claims. This note records how the expanded vocabulary reconciles with the
CentCalculus2 draft, what each capability status means, and what is verified.

---

## 1. The 29 / 23 reconciliation

CentCalculus2 announces a "24-primitive" atomic vocabulary. Its Lean
`CentAtomic` block enumerates **23** constructors, and it omits entries that its
own tier table requires:

`transform`, `store_pot`, `store_kin`, `transduce`, `quantize`, `entropy`

Dropping them would break the bond-graph closure that motivates the expansion:
without `transform` and `transduce` there is no two-port composition, and
without `store_pot` / `store_kin` there is no state in a conservative network.
The implementation therefore provides the **full closed set of 29 atomics** and
records the discrepancy here rather than silently following either count.

The **12 composite macros** match the document exactly.

| Tier | Count | Primitives |
|------|-------|------------|
| classical | 13 | `sum`, `neg`, `mult`, `scale`, `accum`, `rate`, `wrap`, `spatial`, `exp`, `log`, `sat`, `hysteresis`, `delay` |
| continuum | 5 | `grad`, `div_spatial`, `curl`, `laplacian`, `boundary` |
| conservative | 8 | `junction_0`, `junction_1`, `gyrator`, `transformer`, `dissipate`, `store_pot`, `store_kin`, `transduce` |
| stochastic/topological | 3 | `noise`, `quantize`, `entropy` |
| composite | 12 | `recip`, `div`, `sqrt`, `eq`, `translinear`, `state_space`, `pid`, `phase_locked_loop`, `transmission_line`, `kalman_observer`, `thermo_electric`, `delta_sigma_modulator` |

**Total: 29 atomic + 12 composite = 41 contracts.**

Two consequences of using the closed set are visible in the code:

* `¢_neg` is signed negation. Unit *complement* is a separate operation
  (`density.UnitDensity.complement`), so the two cannot be confused.
* `¢_sum` is pure addition and does **not** use the accumulator register;
  accumulation is `¢_accum`.

---

## 2. Capability statuses

Every contract carries one status:

| Status | Meaning |
|--------|---------|
| `implemented_verified` | covered by an exact check in `tests/test_core.py` |
| `implemented_tested` | implemented and exercised, but not by a dedicated invariant check |
| `implemented_proof_pending` | implementation exists; the named theorem is not proved |
| `specified_implementation_pending` | contract only |
| `unsupported` | deliberately not provided |

Theorem strings in contracts (for example
`power.junction_0_conserves_power (Lean pending)`) are honest labels: the
identities are *tested exactly*, not proved in Lean. No status in this
repository claims a Lean proof.

---

## 3. Rendering the registry

```bash
python3 tools/export_capabilities.py                     # stdout
python3 tools/export_capabilities.py --out capabilities.json
```

The exporter emits `cent-capabilities/1` JSON with:

* `atomic_count` = 29, `composite_count` = 12, `atomic`/`composite` name lists;
* `tiers` and `by_status` groupings;
* `contracts`: for each primitive, its signature, output, parameters, owned
  state, domain, error codes, theorem label, status and notes.

This is the file to diff when a contract changes; documentation quotes it rather
than restating it.

---

## 4. What is verified

`python3 tests/test_core.py` runs **73 checks** in ten groups and exits
non-zero on any failure:

| Group | Checks | Representative claims |
|-------|--------|-----------------------|
| exact | 7 | decimal strings are exact; floats rejected; `0.1` converts losslessly; structured errors |
| interval | 7 | `√2`, `e`, `log 2`, `π` enclosures certified and tight; outward-rounded algebra |
| port | 7 | gyrator/transformer conserve power exactly; junctions balance; entropy ≥ 0 |
| density | 2 | reject/clamp/widen policies; complement is not negation |
| geometry | 7 | exact stencils; `curl∘grad = 0`; `div∘curl = 0`; 276-component 2-form; boundary extrapolation |
| state | 2 | writes invisible until commit; deterministic PRNG stream |
| program | 8 | arity, parameters, single assignment, kinds, combinational vs stateful cycles |
| evaluator | 17 | tick semantics of accum/rate/delay/hysteresis/noise/quantize/pid/state-space/ΔΣ/fields/ports |
| coverage | 13 | every remaining primitive executes with its documented result |
| resolution | 3 | fallback selection, strict refusal, diverging outcome |

Also checked by the same suite: a failed tick leaves the machine untouched
(transactional state), and `run` is deterministic for a fixed seed.

---

## 5. Honest limitations

These are model limits, not bugs. Each is stated where it applies in the code.

* **No floating point.** Physical units are carried by the caller; the core
  computes exact rationals and enclosures only. A physically calibrated
  simulation belongs in the v2.0 layer.
* **`transmission_line` is a documented lossless delay-line model** with a load
  reflection coefficient — not a Telegrapher's-equation solution.
* **`kalman_observer` is scalar** and assumes exact rational variances.
* **`state_space` takes rational matrices** of consistent shape; it is not a
  general nonlinear integrator.
* **`noise` is deterministic** (two-point law, SplitMix64). It reproduces the
  documented moments exactly and is not an entropy source.
* **`boundary` is a projection operator** over a rectangular lattice with one
  condition for all faces; it is not a PDE solver.
* **The 2-form curl stores only nonzero components.** `C(24,2) = 276` is the
  dimension of the tensor, not the length of an arbitrary sparse instance.
* **Lean theorems are pending.** Everywhere a theorem is named, the identity is
  tested rather than proved.
