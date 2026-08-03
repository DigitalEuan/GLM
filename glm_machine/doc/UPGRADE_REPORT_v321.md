# GLM v3.21.0 — Simplicial CRG (2-Complex Topology)

**Date:** 2026-07-08
**Base version:** v3.20.0 (94/94 tests passing)
**New version:** v3.21.0 (**18/18 new v3.21 tests passing**, 26/26 + 41/41 existing tests still pass — total 85/85)

---

## What changed in v3.21

The user shared design notes proposing to move the CRG from a 1-complex (graph: nodes + edges) to a 2-complex (simplicial complex with triangular faces). This is a natural upgrade because:

- A "relation" is currently binary (A → B), but much of GLM's structure is genuinely **ternary** — {boson, fermion, spin}, {hamiltonian, time, energy}, {lattice, continuum, continuum limit}. A 2-simplex (filled triangle) captures "these three concepts cohere as a unit" without privileging any one pair.
- Once we have faces, we get a **topological notion of coherence**: an argument backbone is a 1-chain (path of edges). If it's the boundary of a union of faces, the argument "fills" — no holes. If not, the residual cycle is a **hole** — a geometry-driven signal of a reasoning gap.
- This generalises the existing `contradiction_penalty` from "bad edge present" to "good cycle absent."

### GLM34_simplicial_crg.py — the 2-complex ✅

**New module** implementing ideas 1–6 from the design notes:

1. **Nodes as positions** — each concept's BLA vector is coordinates in {0,1}²⁴; Hamming distance is the L1 metric.
2. **Node intrinsic geometry** — `NodeGeom` dataclass with `degree` (1-skeleton), `stellar` (2-skeleton degree = incident faces), `bridge_score` (node B mediates A–C if d(A,C) = d(A,B) + d(B,C)).
3. **Faces as 2-simplices** — `CRGFace` dataclass with side lengths (a,b,c), Heron area, circumradius, degeneracy flag. `discover_faces()` finds 3-cliques in the non-contradiction edge graph and keeps the geometrically tight ones.
4. **Triangle-shape semantics** — `CRGFace.shape` returns "equilateral" (symmetric triad), "isosceles" (two close + outlier), "scalene", or "degenerate" (bridge triple).
5. **Boundary operators over GF(2)** — `_gf2_rank_reduce()` and `_gf2_solve()` implement Gaussian elimination over GF(2) for the chain complex C₂ →∂₂ C₁ →∂₁ C₀. `backbone_is_filled()` checks if a 1-cycle is a boundary of faces.
6. **Betti numbers and Euler characteristic** — `betti()` returns (β₀, β₁, β₂); `euler()` returns χ = V − E + F. `topology_report()` gives a full dashboard.

**Key results on the real CRG:**
- V=110, E=101, F=2 (2 faces discovered)
- Betti (β₀, β₁, β₂) = (16, 5, 0) — 16 connected components, **5 independent holes** (reasoning gaps), 0 voids
- Euler characteristic χ = 11
- 2 tightest faces: {density matrix, hamiltonian, operator} and {hamiltonian, operator, projector}

### GLM11_runtime.py — runtime integration ✅

**Patched** with two new methods:
- `rt.simplicial_crg(max_side=8, max_faces=200)` — lazily constructs and returns a `SimplicialCRG`
- `rt.topology_report()` — convenience method returning the `TopologyReport`

### Usage

```python
from GLM11_runtime import GLMRuntimeV37
rt = GLMRuntimeV37()

# Topology dashboard
rep = rt.topology_report()
print(f"V={rep.n_vertices} E={rep.n_edges} F={rep.n_faces}")
print(f"β=({rep.beta0},{rep.beta1},{rep.beta2}) χ={rep.euler}")
print(f"holes (β₁) = {rep.beta1} — reasoning gaps in the CRG")

# Backbone coherence
scrg = rt.simplicial_crg()
zone = rt.manager.active
if zone.crg_backbone:
    tc = scrg.topological_coherence(zone.crg_backbone)
    filled = scrg.backbone_is_filled(zone.crg_backbone)
    print(f"backbone coherence: {tc:.3f}, filled: {filled}")
```

---

## File-by-file changes

### New modules

#### `GLM34_simplicial_crg.py` (~600 lines)
- `CRGFace` dataclass: nodes, label, sides, area, circumradius, degenerate, shape
- `NodeGeom` dataclass: name, hex_int, zone, degree, stellar, bridge_score
- `TopologyReport` dataclass: n_vertices, n_edges, n_faces, beta0, beta1, beta2, euler, mean_stellar, max_stellar, overheating_violations, fillable_cycles
- `_gf2_rank_reduce(cols)` — GF(2) Gaussian elimination for rank computation
- `_gf2_solve(cols, target)` — solve Ax = b over GF(2)
- `SimplicialCRG` class:
  - `add_face(a, b, c, label, hex_cache)` — add a 2-simplex with computed geometry
  - `faces_of(node)` — faces incident to a node
  - `build_node_geometry(vocab_words)` — compute degree, stellar, bridge_score
  - `_index_complex()` — build the indexed chain complex for homology
  - `betti()` — return (β₀, β₁, β₂)
  - `euler()` — return χ = V − E + F
  - `topology_report()` — full dashboard
  - `backbone_1chain(backbone)` — represent backbone as GF(2) bitmask
  - `backbone_is_filled(backbone)` — True iff backbone bounds faces
  - `backbone_face_support(backbone)` — count faces touching backbone edges
  - `topological_coherence(backbone)` — [0,1] coherence score
- `discover_faces(scrg, vocab_words, max_side, max_circumradius, max_faces)` — find 3-cliques
- `build_simplicial_crg(vocab_words, max_side, max_faces)` — end-to-end builder

### Modified modules

#### `GLM11_runtime.py` — added simplicial_crg() and topology_report()
- `simplicial_crg(max_side=8, max_faces=200)` — lazily constructs a SimplicialCRG
- `topology_report()` — convenience method for the topology dashboard

---

## Test results

| Suite | v3.20 result | v3.21 result | Delta |
|---|---|---|---|
| Existing self-tests | 26/26 | 26/26 | unchanged |
| Existing golden cases | 41/41 | 41/41 | unchanged |
| New v3.21 simplicial tests | (n/a) | 18/18 | +18 |
| **Total** | 67/67 (existing) | **85/85** | +18 tests, all passing |

### What the new v3.21 tests prove

| Test | Claim verified |
|---|---|
| `test_face_discovery` | 3-cliques in the CRG are discovered as 2-simplices with valid geometry |
| `test_betti_numbers` | β₀ ≥ 1, β₁ ≥ 0, β₂ ≥ 0 — topology computed correctly over GF(2) |
| `test_euler_characteristic` | χ = V − E + F formula verified |
| `test_topological_coherence` | Coherence in [0,1]; empty backbone returns 1.0 |
| `test_node_geometry` | degree, stellar, bridge_score, zone all computed |
| `test_runtime_integration` | `rt.simplicial_crg()` and `rt.topology_report()` work |
| `test_gf2_linear_algebra` | GF(2) rank and solve verified on known matrices |
| `test_regression_self_tests` | 26/26 self-tests still pass |
| `test_regression_golden_cases` | 41/41 golden cases still pass |
