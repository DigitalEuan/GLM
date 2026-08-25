# `glm_universal.reasoning` — the algebraic and geometric reasoning kernel

**Parent:** [`../README.md`](../README.md) · **Repository root:**
[`../../README.md`](../../README.md)

**Status: implemented (GLM-3+ Step 3, extended since).** **27 modules**, one
frozen data file,
and a runnable audit. Everything is exact `int` / `fractions.Fraction` /
`F_2`; nothing here imports `random`; nothing here imports a third-party
package.

### The four original modules

| module | what it provides |
| --- | --- |
| `product.py` | the Norton–Sakuma `2A` algebra over the substrate's type-2 classes |
| `metric.py` | the positive-definite Griess form on `Q^24`, exact distances and exact clustering |
| `analogy.py` | `A : B :: C : D` by displacement, then projection onto candidates, the Golay code, or `Λ` |
| `verifier.py` | the 222 + 71 physical relations audited plane by plane, with 31-facet attribution |
| `_data/physics_relations.json` | frozen relation *statements* (data, not an oracle) |

Sections 1–4 below describe these in detail.

### Everything else in the folder

| module | what it provides | reachable as |
| --- | --- | --- |
| `coherence.py` | NRCI over five shells, the `Y` and `Q` constants, the TAX decomposition, the coherence regimes, and `RefinedNRCI` (per-shell weights, shells switchable off) | `coherence <concept>` |
| `dimension_layers.py` | the five cumulative dimension layers — substrate, integer, rational, griess, universal — each with its own `perceive` and `measure`, plus `escalate` | `project A B` |
| `information_loss.py` | what each layer conflates, where the boundaries are, whether addition descends, and the pigeonhole capacity bound | `report information loss` |
| `facets.py` | the six-facet partition of the 24 coordinates: strictly linear, mutually orthogonal, no facet redundant | `report facets` |
| `monster_stack.py` | the ten-plane 2-adic Monster stack, plane composition and pair repair | `report monster stack` |
| `multires.py` | the `F_2^4 <-> GF(4) x Z_4` fibration, column sub-lattices, cross-level inner and tensor products, the scale-invariance boundary | `report multiresolution` |
| `tasks.py` | three worked end-to-end tasks — a grid transformation, a physics derivation, a concept-graph walk | `task grid \| physics \| concepts` |
| `moonshine.py` | graded dimensions `V_0..V_10`, the j-function q-series, the Leech-to-Moonshine bridge | (library) |
| `niemeier.py` | the 23 Niemeier lattices as ADE root systems, with deep-hole types | (library) |
| `llvq.py` | Leech Lattice Vector Quantization: codebook-free angular search over the first six shells | (library) |
| `fwht.py` | the Fast Walsh-Hadamard Transform, `O(N log N)`, exact | (library) |
| `valorani.py` | Buckingham-Pi by exact rational nullspace of the EXT10 exponent matrix | `pi groups A, B, C, ...` |
| `exact_real.py` | a real held as a *process*: `x.at(k)` returns an exact `Fraction` within `2⁻ᵏ`, for any `k`. Roots of any degree by integer `n`-th root, `pi` (Machin), `e` (the exponential series) and `phi`; the dyadic tower of stand-ins and the level at which each is exposed; decidable inequality and refused equality; the delta-sigma modulator in one dimension (`\|average − target\| ≤ 1/N`) and in twenty-four over the Golay code, with the hull certificate for a target no quantiser can reach | `approximate <expr> to <n> places`, `report infinite values` |
| `real_expr.py` | written arithmetic over those processes: `+ - * /`, integer powers, brackets, `sqrt`, `cbrt`, `root(degree, x)`, `pi`, `e`, `phi`, and rational or decimal literals read as the rational they name (`0.1+0.2` is exactly `3/10`). Division searches for a nonzero witness to `WITNESS_DEPTH = 96` and refuses beyond it, naming the depth | `approximate ...`, `is <a> less than <b>` |
| `transcendental.py` | `exp`, `log` (natural, or `log(base, x)`), `sin`, `cos`, `tan` and a non-integer exponent `x^y`, each a process with a stated and paid-for error budget, all in exact rational arithmetic. `log` requires a positivity witness, searched to `POSITIVE_WITNESS_DEPTH = 96`, exactly as division requires a nonzero one; `x^y` is `exp(y·log x)` and inherits it | `approximate exp(1) to 20 places`, `is 2^pi less than 9` |
| `analogy_models.py` | analogy by **named relation** rather than by displacement: `periodic_step`, `reciprocal_dimension`, `scale_shift`, `lexicon_relation`. The first model that recognises `A : B` transports it to `C`; a model that recognises the pair but finds nothing there *refuses* and says where it looked | `A : B :: C : ?`, `report analogies` |
| `periodic_table.py` | period, group and block for every `Z`, computed from the period boundaries rather than tabulated — the coordinates `periodic_step` moves in | (library) |
| `element_coverage.py` | how sparse the element register is, and three widenings that invent no measurement: derive, estimate with the error measured, cross-check without merging | `report chemistry coverage` |
| `units.py` | the unit string of every quantity parsed and checked against its EXT10 exponents, and what an SI reading of the steradian would cost | `report units` |
| `term_arithmetic.py` | expressions written over register *names* — `energy divided by time`, `mass times velocity` — read into a dimension and back to the quantities that carry it | `compare`, `verify` |
| `fwht_decode.py` | the transform wired to something: all 4,096 Golay coset costs as one Walsh–Hadamard transform, with the tier at which the constant-time answer carries its own certificate | `report transform decoder` |
| `voronoi_walk.py` | walking to a hole of the Leech lattice and climbing to the covering radius, so a hole is *reached* rather than looked up among 196,560 facets | (library) |
| `deep_holes.py` | the Niemeier type of the hole a carrier sits in, read off the walk's trajectory and certified, against a derived catalogue | `report deep holes` |

---

## 1. `product.py` — the `2A` product algebra

Axes are indexed by the 98,280 **type-2 classes** of `Λ / 2Λ` that
`substrate.leech2` enumerates exhaustively. Two axes sit in one of four mutual
positions, decided by the `Co_0` pair invariant `|⟨λ, μ⟩| / 8`:

| invariant | position | product | count against a fixed axis |
| --- | --- | --- | --- |
| 4 | `1A` (same axis) | `a · a = a` | 2 |
| 2 | `2A` | `(1/8)(a + b − a_ab)` | 9,200 |
| 1 | **not modelled** | raises `PositionError` | 94,208 |
| 0 | `2B` | `0` | 93,150 |

The counts are the full census of the 196,560 minimal vectors, recomputed by
`leech2.pair_census`, not quoted.

**Why invariant 2 is the `2A` position.** It is the only position in which the
third axis exists inside the substrate: `a_ab` is the axis of the class
`u XOR v`, and `u XOR v` is of type 2 exactly when the invariant is 2 — because
`norm(λ ± μ) = 64 ± 2⟨λ, μ⟩` hits the minimum 32 precisely at `|⟨λ, μ⟩| = 16`.
This is an *operational* definition grounded in the substrate. The module
verifies that the Sakuma `2A` relations close there; it does not claim a proved
correspondence with the Monster's `2A` conjugacy class.

**What `two_a_subalgebra(u, v)` checks, per pair, from scratch:**

- closure in exactly three dimensions — `span{a_u, a_v, a_{u^v}}`;
- commutativity;
- **non-associativity**, with an explicit witness: `(a·a)·b ≠ a·(a·b)`;
- the Gram matrix is `1` on the diagonal and `1/8` off it.

**The Miyamoto maps are derived, not tabulated.** `fusion_spectrum` solves
`(ad_a − λI)x = 0` exactly over `Q^3` at the four Ising eigenvalues and finds
dimensions `1, 1, 1, 0` for `1, 0, 1/4, 1/32`. Since `τ_a` is by definition
`−1` on the `1/32`-eigenspace and that eigenspace is **empty**, `τ_a` comes out
as the **identity** on the `2A` subalgebra — which is the correct classical
answer (`⟨τ_0, τ_1⟩` is a Klein four-group, and conjugation in an abelian group
is trivial), and it is computed rather than assumed. The nontrivial
automorphism that fixes `a_u` and swaps `a_v ↔ a_{u^v}` is `σ_a`, `−1` on the
`1/4`-eigenspace; the module checks it is an algebra automorphism and an
isometry of the form.

Anyone expecting `τ_a` to permute the axes should read that paragraph twice:
the swap is real, but it belongs to `σ`, not `τ`.

## 2. `metric.py` — the Griess metric

`⟨u, v⟩ = (1/8) Σ u_i v_i`, extending `leech2.rational_inner` from the lattice
to all of `Q^24`; `d(u,v)² = ⟨u−v, u−v⟩`.

Positive definiteness is established **twice**, both exactly: the diagonal of
the form on the standard basis, and Sylvester's criterion on all 24 leading
principal minors of the Leech Gram matrix in integer arithmetic (its
determinant comes out `1` — `Λ` is unimodular).

Because `d` itself is usually irrational, **squared** distances are the primary
object and every ordering, merge height and comparison uses them. Two places
need care, and both are handled algebraically rather than numerically:

- **the triangle inequality** is genuinely a statement about `d`, not `d²`. With
  `s = d(u,v)² − d(u,w)² − d(w,v)²`, the claim is `s ≤ 2√(ab)`, decided by
  `s ≤ 0 or s² ≤ 4ab` — exact rationals throughout;
- **angles**: `signed_cosine_squared` returns `sign(⟨u,v⟩)·cos²`, a strictly
  increasing function of the cosine and always rational, so `compare_cosines`
  orders by angle exactly with no `arccos`.

`single_linkage` and `complete_linkage` are exact agglomerative clustering with
`Fraction` merge heights and deterministic tie-breaking by cluster id.

## 3. `analogy.py` — proportional analogy

`D* = C + (B − A)` exactly, then projection.

**Subspaces matter.** A raw 24-coordinate difference lets bookkeeping outvote
content, so `SUBSPACES` names the coordinate sets that make a question
well-posed — `physics.dimension` (the ten EXT10 exponents plus the SI7
projection), `chemistry.position` (`z`, period, group), and others. Projection
zeroes the other coordinates rather than slicing, so the result stays a point
of `Q^24`.

**Answers are tie classes, not single names.** Several register concepts share
a dimension vector exactly, so `AnalogyResult` reports `tied` and `unique`
alongside `answer`. Reporting just `answer` would overclaim.

**`nearest_lattice_point` is exact and provably optimal**, not a heuristic. `Λ`
is the disjoint union over a parity `m ∈ {0,1}` and a Golay codeword `c` of the
congruence cosets that `leech2.in_leech` tests. Inside one coset each
coordinate ranges over a step-4 progression, so the unconstrained nearest point
is coordinatewise rounding; the `sum ≡ 4m (mod 8)` condition is either met, or
flipped at minimum cost by moving one coordinate by `±4`. Enumerating the
`2 × 4096` cosets therefore searches all of `Λ`. The decoded point is checked
with `in_leech` before it is returned.

**A known boundary of the model:** `D* = C + (B − A)` expresses *translations
of the exponent vector and nothing else*. `time : frequency :: length : ?` is an
inversion, not a translation, so the model answers `L T^-2` (acceleration) and
not the reciprocal `L^-1` a reader expects. The audit records this case rather
than hiding it.

## 4. `verifier.py` — the multi-plane equation audit

Three layers, deliberately separate:

1. **the operator algebra** (`Sense`) — ten exact rational EXT10 exponents, a
   decimal scale, tensor rank, and `P` / `T` / `C` gradings. `dot` contracts two
   ranks away; `moment` is the cross product with one radian consumed (torque is
   an energy *per radian*, `E × H` is not); every differential operator is built
   from one `NABLA` with `L^-1`, rank 1, `P`-odd, so rank and parity bookkeeping
   is forced rather than tabulated;
2. **the parser** — recursive descent over `* / ^ ( ) ,` with exact rational
   exponents; numeric literals must be exact powers of ten, because the register
   tracks the decimal scale exactly and refuses to absorb other constants;
3. **the substrate audit** — both sides become 24-coordinate carriers,
   `digit_stack.verify_equation` compares them plane by plane, and every
   differing bit is attributed to each of the 31 named MOG facets containing it
   (3 trio bricks, 6 sextet columns, 4 frame rows, 18 cube faces).

Layer 3 is the point. A boolean says an equation is wrong; a facet attribution
says *where*.

| table | semantics | checked | held |
| --- | --- | --- | --- |
| scalar relations | scalar (exponents + scale) | 222 | 222 |
| scalar relations | full (+ rank, P, T, C) | 222 | 186 |
| tensor relations | full | 71 | 71 |

The middle row is the interesting one: 36 statements that a table of units gets
right are wrong once tensor character is included — `acceleration = speed / time`
fails because the left side is a rank-1 vector and the right side a scalar. The
discrepancy lands in coordinates `rank` (18) and `p` (19), which live in
`brick2/col5/row3/cube2.*` and `brick1/col3/row0/cube1.*` respectively, and
those are exactly the facets the verdict blames.

## Data provenance

`_data/physics_relations.json` holds the relation **statements** only, frozen
from the upstream register by `workflow/09_extract_physics_relations.py`, the
same way Step 2 froze the 660 concepts. Every verdict is recomputed here by this
module's own parser against `glm_universal`'s own frozen register. The upstream
tree is never imported at runtime.

That separation is what makes the tally a cross-validation: this kernel reports
222 / 71 / 186, and the upstream `glm2_library.library_audit()` — a separate
implementation over a separate copy of the register — reports the same three
numbers.

## Running it

```bash
PYTHONPATH=. python3 -m pytest glm_universal/tests/test_reasoning.py -q   # 94 tests
PYTHONPATH=. python3 -m pytest glm_universal/tests/ -q                    # the whole suite
```

The reasoning kernel is also covered by `test_coherence.py` (58),
`test_fusion.py` (23), `test_information_loss.py` (53),
`test_multires_tasks.py` (40), `test_directive.py` (31),
`test_reasoning_showcase.py` (14), `test_analogy_models.py` (53),
`test_element_coverage.py` (40), `test_units.py` (24),
`test_term_arithmetic.py` (40), `test_fwht_decode.py` (20) and
`test_deep_holes.py` (25).  The suite-wide counts are recomputed in
[`../../FIGURES.md`](../../FIGURES.md) rather than quoted here.

The first test that touches the `2A` algebra builds the exhaustive
98,280-class type-2 table (about six seconds); it is cached for the process and
the fixture is module-scoped, so the cost is paid once.

## Depends on

`glm_universal.substrate`, `glm_universal.data_objects`. Nothing else.

---

## v0.6.0 update: five new directive-mentioned modules

Five new modules were added to implement mechanisms the directive
(`ubp_universal_1.txt`) mentions but that had no code at all:

| Module | What it implements | Status |
|---|---|---|
| `moonshine.py` | The Moonshine layer: graded dimensions V_0..V_10, the j-function q-series, and the Leech-to-Moonshine bridge. V_0 = 1 (vacuum), V_1 = 0 (FLM theorem), V_2 = 196884 (Griess algebra). | ✓ graded dimensions + j-function + bridge. VOA state-field map is future work. |
| `niemeier.py` | The 23 Niemeier lattices (ADE root systems, Conway-Sloane). The Leech is the unique one with no roots (rank 0); the other 22 have rank-24 root systems. | ✓ catalogue + deep-hole types. Voronoi cell computation is future work. |
| `llvq.py` | Leech Lattice Vector Quantization: codebook-free angular search over Leech shells. The first 6 shells are catalogued. | ✓ shell classification. Full O(1) lookup table is future work. |
| `fwht.py` | The Fast Walsh-Hadamard Transform: O(N log N) instead of O(N^2). Verified: fwht(fwht(v)) = N*v exactly. | ✓ transform + incoherence_apply. Wiring into substrate group actions is future work. |
| `valorani.py` | Valorani's log-space SVD for Buckingham-Pi: rational nullspace (exact, float-free). | ✓ rational nullspace + `buckingham_pi_groups`, wired in v1.0.0 as the `pi_groups` query kind. The SVD step is documented as conceptual motivation; the rational approach is exact. |

## The pipeline is now complete

The directive's "unbroken mathematical pipeline" is:

    Golay → Leech Lattice → Griess Algebra → Moonshine Functions

All four stages are now implemented:

1. **Golay** (`substrate/mog.py`): 4,096 codewords, 759 octads, MOG trio/sextet.
2. **Leech** (`substrate/leech2.py`): 196,560 minimal vectors, 98,280 type-2 classes.
3. **Griess** (`reasoning/product.py`): Norton-Sakuma 2A algebra, trilinear form, Griess metric.
4. **Moonshine** (`reasoning/moonshine.py`): graded dimensions V_0..V_10, j-function q-series, Leech-to-Moonshine bridge.

The VOA state-field map Y(u, z) = sum u_n z^-n-1 is the
infinite-dimensional half of the Moonshine bridge and is explicitly
future work.

## v0.7.0 update: `information_loss.py` — loss at the layer boundaries

`dimension_layers.py` asserts that the GLM is a stack of perspectives, each
true within its range and each handing off to the next.  `information_loss.py`
measures *where* a range ends.  Everything is derived from one relation: two
carriers are **indistinguishable at a layer** when that layer's own `measure`
reports distance 0 between their views — the layer's own verdict that they are
the same thing.

| Function | What it answers |
|---|---|
| `classes`, `resolution`, `loss_count` | how much a layer tells apart, and how much it loses |
| `boundary(lower, higher, carriers)` | the pairs the lower layer conflates and the higher splits: the information lost, listed rather than asserted |
| `refinement_violations` | the pairs the *lower* layer splits and the *higher* conflates — holes in the escalation ladder |
| `congruence_witness`, `is_congruent` | four carriers showing that an operation escapes a layer's resolution; `None` means the law descends |
| `capacity` | the pigeonhole bound.  Only the substrate is finite (2²⁴); every layer above holds exponents or exact rationals |
| `view`, `clear_view_cache` | memoised `perceive`, because the rational layer runs a Leech nearest-point decode |
| `information_loss_report` | all of the above, recomputed on demand, never quoted |

Exact throughout: no float is constructed anywhere in the module.

Reachable from the runtime as `report information loss`.

### The v0.7.0 audit finding, and how it was repaired

v0.7.0 measured the stack as originally written and found that the substrate →
integer step was **not** a refinement (`refinement_chain_intact = False`): the
substrate's 24-bit parity view separated carriers that the integer layer's
seven SI7 exponents conflated, so escalating one step *lost* distinctions
instead of gaining them.  That is a real defect in an escalation ladder, and it
was fixed rather than documented away.

The repair is to make each view **cumulative**: `LAYER_INTEGER` now carries the
seven SI7 exponents *and* everything the substrate could already tell apart, so
it refines the layer below it by construction.  The discarded non-cumulative
reading is kept beside it as `LAYER_INTEGER_RAW` — outside `LAYERS`, so nothing
escalates through it — and `information_loss.non_cumulative_report()` measures
exactly what it costs, naming the two carrier pairs it violates.  Keeping the
rejected reading measurable is the point: the claim "cumulative layers repair
the chain" is checked against the alternative, not asserted.

The measured result on the fixed seven-carrier set is now:

| layer | dimension | resolves | loses | addition descends |
| --- | --- | --- | --- | --- |
| substrate | 24 | 3 / 7 | 4 | no |
| integer | 7 (cumulative) | 5 / 7 | 2 | no |
| rational | 10 | 7 / 7 | 0 | yes |
| griess | 196,884 | 7 / 7 | 0 | yes |
| universal | — | 7 / 7 | 0 | yes |

and `refinement_chain_intact` is **`True`**.  The non-cumulative reading, for
comparison, resolves only 4 of 7 and violates refinement on two pairs.

The counterpart formal development, with the same definitions proved as
theorems, is `RequestProject/GLM/Layers.lean`, `RequestProject/GLM/Stack.lean`
and `RequestProject/GLM/Cumulative.lean` at the repository root; the write-up
is `INFORMATION_LOSS_STUDY.md`.

## v1.2.0 update: `exact_real.py` and `real_expr.py` — values that are processes

`information_loss.py` says what a *layer* loses. These two modules say what a
*value* is when it cannot be held at all.

A carrier is 24 exact rationals, and no rational is `sqrt(2)`. The wall is a
theorem, not an engineering limit: the views of any layer whose readings form a
countable set conflate two distinct reals
(`RequestProject/GLM/Irrational.lean`, `no_countable_layer_lossless`). So a
real is not stored — it is held as the **process** that converges to it.

### `exact_real.py`

| Piece | What it provides |
|---|---|
| `ExactReal`, `x.at(k)` | a real as a rule: an exact `Fraction` within `2⁻ᵏ` of the value, for any `k`. No float anywhere; no ceiling on `k` but time |
| `sqrt`, `nth_root`, `pi`, `e`, `phi` | roots of any degree by integer `n`-th root; `pi` by Machin's formula, `e` by the exponential series, `phi` as `(1+sqrt(5))/2`. Each is checked against a relation it must satisfy |
| `surrogate`, `surrogate_sequence` | the dyadic tower's stand-in `⌊x·2ⁿ⌋/2ⁿ` at level `n`, and the level at which a higher reading exposes it. For `sqrt(2)`: `1, 1, 5/4, 11/8, 11/8, 45/32, 45/32, 181/128`, exposed at levels `2, 2, 3, 5` |
| `decide_equal`, comparison | inequality is decided and the precision it took is reported; equality is *refused* — two processes never separated are equal, but "never" quantifies over all precisions at once |
| `delta_sigma_*` | the one-bit modulator with an exact error accumulator: after `N` ticks the time average is a rational `k/N` within `1/N` of the target — the machine-checked `dsAverage_error_le` |
| `golay_delta_sigma`, `trajectory_stats` | the same loop in 24 coordinates, quantising to Golay codewords. The all-½ target is held with deviation **0** using two codewords |
| `hull_certificate` | why some targets cannot be held: every emitted state is a codeword, so every reading is in the convex hull of the code. For the ramp target `i/24` the module computes a linear functional that puts it strictly above all 4,096 codewords — gap `13/5760` — which is a *certificate* of unreachability, not an observation |
| `real_carrier` | the bridge back: the 24-coordinate carrier the tower holds for a vector of processes at a given level |
| `exact_real_report` | all of the above, recomputed on demand |

### `real_expr.py`

Ordinary written arithmetic over those processes: `+ - * /`, integer powers,
brackets, `sqrt`, `cbrt`, `root(degree, x)`, the constants `pi`, `e`, `phi`,
and any rational or decimal literal. A decimal literal is read as the rational
it names, so `0.1+0.2` is **exactly** `3/10`.

Division is the interesting case. `1/x` is computable only from a bound
`|x| ≥ 2⁻ᵐ`, and no algorithm produces that bound for an arbitrary process,
because doing so would decide whether the process is zero. So `divide` searches
for the witness to `WITNESS_DEPTH = 96` and refuses beyond it, naming the
depth: `1/(sqrt(3)-sqrt(2))` goes through and equals `sqrt(3)+sqrt(2)`;
`1/(sqrt(2)-sqrt(2))` is refused. The three Lean theorems that make this exact
are in `RequestProject/GLM/Computable.lean`.

### `transcendental.py`

The grammar reaches past the algebraic operations: `exp`, `log` (natural, or
`log(base, x)`), `sin`, `cos`, `tan`, and a non-integer exponent. `exp` halves
its argument until the series converges geometrically and squares back up,
paying for each squaring; `log` writes `a = f·2ˢ` with `f` in `[1, 2)` and
sums the `atanh` series; `sin` and `cos` use the alternating Taylor series,
where the error is below the first omitted term. Every bound is exact
rational arithmetic, and the Lipschitz constants they are budgeted against
are machine-checked in `RequestProject/GLM/Transcendental.lean`.

```
exp(1) = 2.71828182845904523536      log(2)    = 0.69314718055994530941
sin(1) = 0.84147098480789650665      2^pi      = 8.82497782707628762385
tan(1) = 1.55740772465490223050      2^(1/3)   = root(3, 2)
```

**Where the grammar stops.** Two places, of different kinds. `log(x)` needs a
positivity witness `x ≥ 2⁻ᵐ`, for exactly the reason `1/x` needs a nonzero
one — producing one for an arbitrary process would decide whether the process
is zero — so `log(2)` goes through while `log(sqrt(2)-sqrt(2))` is refused
with its depth named, and `x^y` inherits the refusal (`2^pi` computes,
`0^pi` does not). That stop is a theorem, `GLM.Info.pos_iff_witness`. The
other is a work item: the inverse and hyperbolic family — `asin`, `acos`,
`atan`, `sinh`, `cosh`, `tanh`, `erf`, `gamma`, `zeta` — is refused by the
explicit list `UNBUILT_FUNCTIONS`, so the message names the missing function
instead of failing to parse. Each needs its own convergent process with a
stated error bound; the six that are built are the pattern to follow.

Reachable from the runtime as `approximate <expr> to <n> places`, as
`is <a> less than <b>` and the other comparison surfaces, and as
`report infinite values`. The write-up is `INFINITE_VALUES_STUDY.md` at the
repository root; the capability probes that locate every boundary named here
are in `glm_universal/capabilities/`.

---

## `element_coverage.py` — a sparse register, widened honestly

The element register is not full, and the module says so before it does
anything else: **1,257 of 1,652 cells carry a value**, over 118 elements and
14 measured fields.  Three fields are complete (`atomic_weight_u`,
`group_block_code`, `standard_state_code`); the sparsest,
`homonuclear_bde_kJ_per_mol`, has 21.

There are three ways to widen coverage without inventing a measurement, and
the module keeps them apart and labels each one:

| Widening | What it does | Measured here |
|---|---|---|
| **derive** | attributes that are exact functions of fields already present — `liquid_range_K` is `boiling_point_K - melting_point_K` and nothing more | 4 attributes, **344 new cells**, no new information claimed |
| **estimate** | one linear fit, `covalent_radius_pm` against `atomic_radius_pm`, fitted on the 24 elements that have both — slope `40097/37562`, intercept `-910587/10732` pm, **mean absolute residual `5825791/450744` ≈ 12.9 pm**, worst element Mg at ≈ 41.2 pm | coverage goes from `12/59` to `99/118`; the remaining **19** superheavies have no atomic radius either, so they stay absent |
| **cross-check** | the element register's homonuclear bond enthalpy against the diatomic register's `D0`, compared and *not merged*: 14 elements comparable, **10 agree within 20 kJ/mol, 4 do not** (P, C, S, Si; largest difference P at `569/2`) | the disagreement is the finding — these are not the same quantity |

Nothing is written back into the element register, so a caller that wants
measurements still gets only measurements: an estimate is returned labelled
as an estimate, with its residual attached.  Reachable as
`report chemistry coverage`; the figures above are recomputed under
*Chemistry* in [`../../FIGURES.md`](../../FIGURES.md).
