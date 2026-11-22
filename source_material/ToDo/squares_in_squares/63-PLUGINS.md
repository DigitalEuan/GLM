# 63 — Two composable exact plugins, and the chain between them

Run 100, 22 November 2026. A build run: no row moves, no score is claimed, `submission.csv` and
root `WHITEBOARD.md` are untouched.

The request was for two small, deterministic, float-free *plugins* — a rational Bernstein enclosure
and a quadratic-norm residue mask — written as domain-agnostic modules and wired into
`exact_field.py` and `glm_wheels.py`, plus a doc explaining how such stages chain.

Both exist, both are exercised by control 31, and both are honest about being **partial**: each is
sound everywhere it speaks and silent where it cannot decide. That is the whole design. A filter
that is never wrong but sometimes says nothing can be composed safely; a filter that is right
"usually" cannot be composed at all.

| | |
|---|---|
| generic modules | `exact_field.py`: `bernstein_coeffs`, `bernstein_enclosure`, `bernstein_quadratic`, `bernstein_nodes`, `norm_residue`, `residue_norm_filter` |
| domain drivers | `glm_wheels.py`: `bernstein_axis_certificate`, `bernstein_pair_slide`, `bernstein_interval_certificate`, `bernstein_cage_crosscheck`, `plugin_bernstein_demo`, `plugin_bernstein_cage`, `pair_tangency_residuals`, `residue_pair_screen`, `residue_benchmark` |
| control | 31 (`--selftest`, 31 controls, 2 m 37 s) |
| audit | 294 functions, **0** naming `float` |
| run modes | `--plugin-bernstein`, `--plugin-residue` (ledgers in `workspace/push/`) |

## 1. Bernstein: an exact basis change that decides a continuum

A polynomial written in the power basis is awkward to bound: its coefficients are derivatives at
one point, not values anywhere. The Bernstein form on `[a, b]` is different. With `h = b − a` and

    p(a + h t) = Σ_k c_k · C(n, k) t^k (1 − t)^{n−k},

the basis functions are non-negative and sum to 1, so for every `t ∈ [0, 1]`

    min_k c_k  ≤  p(a + h t)  ≤  max_k c_k .

That is the convex-hull property, and it is exact: no sampling, no interval arithmetic, no
tolerance. `bernstein_coeffs(poly, a, b)` performs the two steps — Horner in `t` for the affine
substitution, then `c_k = Σ_{j ≤ k} C(k,j)/C(n,j) · b_j` for the change of basis — in the same
exact scalar class as the input (`Q` or any `Quad(d)`), using integer binomials only.

`bernstein_enclosure(poly, a, b, splits=1)` returns `{coeffs, lo, hi, sign, positive, negative,
degree, splits}`, where `sign` is `+1` iff `lo > 0`, `−1` iff `hi < 0`, and `0` when the enclosure
straddles zero. A `sign` is a proof about every point of `[a, b]` at once. `splits > 1` cuts the
interval into equal parts and unions the enclosures: still exact, still one pass per part, strictly
tighter.

**It is sound, and deliberately incomplete.** On `[−1, 1]`, `x² + 1` has Bernstein coefficients
`[2, 0, 2]`, so the coarse pass reports `lo = 0`, `sign = 0`: true but useless, because the
minimum 1 sits *between* coefficients. One subdivision gives `lo = 1`, `sign = +1`. The convex
quadratic `(t − ½)² + 1/100` behaves the same way (`sign = 0` at one part, `lo = 1/100` at two).
Refinement is not decoration — it is where the stage earns the word "certificate".

**The cross-check is a second instrument.** `bernstein_nodes(poly, a, b, steps)` evaluates `p` at
`steps + 1` equally spaced exact nodes by Horner. Soundness of the enclosure means every node lies
in `[lo, hi]`; control 31 asserts exactly that at `splits = 1, 2, 4`. The enclosure bounds the
continuum and the staircase checks it — the same pairing the run-95/96 cage and chord proofs use
(a box cover that bounds, a node walk that witnesses), and a disagreement in either direction is a
bug in one of them.

### 1.1 The domain driver: a slide, not a sample

A unit-tangency condition along an axis is `|Δ·u| = need`, `need = ½ + ext(other, u)`. Slide one
square along `d` and the projection becomes `d0 + t·d1`; the condition becomes

    q(t) = (d0 + t d1)² − need² .

`bernstein_quadratic(c0, c1, need, a, b, splits)` encloses that quadratic. `q > 0` on `[a, b]`
means `|c0 + t c1| > need` for **every** `t` in the slide, i.e. the pair is strictly separated
along that axis throughout — one algebraic pass, no sampling.

On the certified `Block45(5, 4)` sentence, the first contact pair `(0, 1)` has a tight axis
`(−½√2, ½√2)` with `d0 = d1 = 1`, `need = 1`:

* on `[½, 1]` the enclosure is positive with `lo = 5/4`, so the slide *away* from the contact is
  certified separated;
* on `[−1, 1]` the chord `1 + t` passes through zero, the quadratic vanishes, and the enclosure
  returns `sign = 0` — a correct refusal, not a failure;
* the exact gate at the two endpoints returns slacks `½` and `1`, both positive, so the certificate
  and the gate agree where the gate can speak.

That last line is the discipline: a stage's certificate is checked against the decision procedure,
not against a float.

### 1.2 Re-reading the cage witness with the plugin

Run 95/96 closed the 151st square of the Q(√7) staircase with a cover cage (5/8 × 3/4) and a
free-chord union (span 0.624681). `plugin_bernstein_cage()` replays that object through the stage:

    cells 149, capacity 1, L = 23/2 + ½√7
    extent_u 5/8 → short      extent_v 3/4 → short      chord 1/12 + 11/48√7 → short
    agree True

Both extents and the chord are below 1, each certified by its own Bernstein pass, and the verdicts
match the cage's capacity reading. On `Block45(5, 4)` the same cross-check runs the other way: the
cage's extents are `33/4` and `23/2`, the chord instrument *refuses* (`pair_not_excluded` — the
free span reaches 1), and the Bernstein verdicts are all "not short", so
`bernstein_cage_crosscheck` still agrees. An agreeing disagreement is the point: the plugin is not
allowed to invent tightness where the sentence has room.

## 2. The residue mask: a projection that can only refute

For an integral residual `A + B√d` in `Z[√d]`, the field norm

    N(A + B√d) = A² − d B²

is multiplicative and vanishes exactly when the element does. Hence: **a nonzero norm residue mod
`m` proves the residual is nonzero**, and a nonzero residual on every one of the eight signed axes
proves the pair cannot be tight there at all. `norm_residue(x, mod)` and
`residue_norm_filter(cls, elements, mods=(8, 12, 24))` implement that; the filter returns, per
modulus, the residues, the indices of the zeros, `all_nonzero`, and whether it abstained.

Two details decide whether the mask is worth anything, and both were found the hard way.

**(i) The scaling that makes reduction legal.** The residual is a rational field element. Multiply
it by `2D²` (`D` the even common denominator of coordinates and words) and every component is an
integer, so `mod m` is a statement about an exact integer rather than a rounded value. In the
driver that scaling is `pair_tangency_residuals`, which computes the eight residuals in pure
integer arithmetic in `Z[√d]` — no `Quad` multiplication, no `Fraction` growth — and returns them
as integral `Quad`s.

**(ii) The content division that makes it informative.** Scaling by `2D²` alone is fatal: every
residual is then divisible by a power of `D`, so at `D = 4` *every* residue is 0 mod 8 and the mask
rejects nothing. It measured as a 0.0 % rejection rate on the first benchmark run and was fixed
before anything was reported. Each residual is divided by its own content `gcd(|A|, |B|)`; that is
a scaling by a nonzero rational, which cannot change the zero set, so soundness is untouched while
the residues become informative. (If both components are zero the content is 0 and the element is
kept as `(0, 0)` — a true tangency.)

**(iii) What the mask is exact about.** After the content division the vectors are primitive, and
for `d ∈ {2, 5, 7}` — our fields Q(√2), Q(√5), Q(√7) — a primitive `A + B√d` is never `0 mod 8`:

    N ≡ 0 (mod 8) with B odd  ⇒  A² ≡ d·B² ≡ d (mod 8), impossible for d ≡ 2, 3, 5, 6, 7
    N ≡ 0 (mod 8) with B even ⇒  A² ≡ 0 or 4 (mod 8) ⇒ A even ⇒ gcd(A, B) ≥ 2, not primitive

So at mod 8 the mask decides *exactly* whether some axis is tight. It is still only a **necessary**
condition for a contact: `Q.gate` counts a pair as a contact when the largest of the four slacks is
0, and a pair can have one tight axis and a loose one (a diagonal neighbour), which the mask cannot
see. On cells with no such pairs the survivors are the contacts; elsewhere they are a superset.

**(iv) The measured table.** `residue_benchmark()` over the four certified cells plus one synthetic
sparse lattice (timings are `perf_counter_ns` integers, so even the benchmark is float-free):

| cell | pairs | contacts | rejected (mod 8) | survivors | extra | speedup |
|---|---:|---:|---:|---:|---:|---:|
| Block45(5,4) | 266 | 172 | 70 (26 %) | 196 | 24 | 1.15–1.24× |
| Block45(10,8) | 1102 | 794 | 252 (23 %) | 850 | 56 | 1.11–1.13× |
| Block45Half(5,4) | 182 | 112 | 70 (38 %) | 112 | **0** | 1.36× |
| Block45Half(17,14) | 2978 | 2256 | 722 (24 %) | 2256 | **0** | 1.12–1.14× |
| Lattice(3/2,1) *(synthetic)* | 342 | 90 | 90 (26 %) | 252 | 162 | 1.14–1.15× |

The counts are exact and identical on every run: **0** false rejections at mod 8, 12 and 24 in
every row, and every contact survived (172/172, 794/794, 112/112, 2256/2256, 90/90). The speedup
is a wall-clock ratio and moves by a few per cent between runs — hence the ranges, and hence the
ledger is the record of a *single* run rather than a stable number. Mod 8, 12 and 24 select the *same* pairs on all five rows —
mod 8 is already complete there, so the larger moduli have nothing left to add. The mask costs
about an eighth of the exact pass (9.4 ms vs 72.5 ms at Block45(5,4); 103 ms vs 801 ms at
Block45Half(17,14)).

**Why the speedup is only 1.1–1.4×, said plainly.** These sentences are contact-dense: 65–76 % of
the candidate pairs are contacts, and those must survive. With 75 % surviving, Amdahl gives a
ceiling near 1.3× no matter how cheap the mask becomes. The synthetic lattice shows the other
blind spot: 162 of its 252 survivors are diagonal neighbours with one tight axis and one loose
one, which no modular test can refute. So the honest claim is not "the mask is fast", it is:

* on the two Block45Half cells the mask is **exact** (survivors = contacts, zero error, 24–38 % of
  the exact pass skipped);
* everywhere it is **sound** (never rejects a tangency) and it never decides a packing;
* its end-to-end gain is bounded by contact density, and that bound is measured, not hoped for.

## 3. The chain, and why it composes

Each stage is a pure function of exact values that returns a *value* rather than throwing: an
abstention is `sign = 0`, `all_nonzero = False`, `certified = False`. That single convention is
what makes the stages composable, in the same way a signal chain composes because a filter passes
its stopband to the next stage instead of halting.

    candidates  ──►  residue mask  ──►  Bernstein slide  ──►  exact 4-axis gate  ──►  witnesses
    (prune |Δ|<2)    (refute pairs     (certify a sign       (decide the pair       (topology,
                      with no tight      on an interval)      exactly)               conservation,
                      axis)                                                       70-digit Decimal)

* **The prune** is the gate's own `|Δ| < 2` on every axis — cheap, exact, and already there.
* **The mask** removes pairs that provably have no tight axis (rung-2 arithmetic on a rung-3
  object). It can only refute, never place.
* **The Bernstein slide** turns a *range* question into a sign question: rather than asking "is
  this pair separated somewhere", it certifies "separated everywhere on this interval".
* **The gate** still decides. This is deliberate: the chain removes work it can prove is wasted
  and never replaces the decision procedure.
* **The witnesses** (node staircase, chord union, cage capacity, contact graph, Decimal replay) are
  independent instruments over the same sentence.

Two properties make the composition safe rather than merely convenient. First, **every stage is
sound**: a refusal is never wrong, only incomplete, so passing a survivor onward cannot corrupt a
later verdict. Second, **no stage reads a float**: the audit checks the bytecode of every function
for the name `float`, so a stage cannot smuggle a tolerance in through a decimal literal or a
library call. The mask's own benchmark timings use integer nanoseconds for the same reason.

### 3.1 On the 7-rung ladder

Doc 59's ladder is rungs of *representation*, and the two plugins sit on it at different heights:

| stage | rung it reads | rung it writes | what it cannot see |
|---|---|---|---|
| prune `|Δ| < 2` | 2 (integer) | 2 | anything tilted that is close on one axis only |
| residue mask | 2 (modular shadow of a rung-3 element) | 2 | the loose side of a pair with one tight axis; sign, and any magnitude |
| Bernstein enclosure | 3 (exact field algebra) | 7 (a sign certificate over an interval) | nothing about the interval — but the interval must be supplied, and a coarse enclosure may straddle |
| exact gate | 3 | 7 | poses outside the field (the table's 424 continuous rows) |
| witnesses | 7 | 7 | they certify; they cannot propose |

The interesting line is the mask's: it is a **projection** from rung 3 to rung 2. A projection can
prove nonexistence (a nonzero residue is a fact about the exact element) and can never prove
existence, which is exactly why the completeness at mod 8 had to be *derived* from the primitive
vector fact and not measured into existence. The Bernstein stage is the opposite move: it stays at
rung 3 and *produces* a rung-7 object, which is why it is allowed to be incomplete but must be
sound.

## 4. Verification

Control 31 asserts, in order:

1. the rational rung compares (`Q(1) < Q(2)`), which is a regression guard: comparing `Q` used to
   drop to `Fraction` and lose the mixin's `sign`, fixed this run by `Q._diff`;
2. Bernstein coefficients on `[0,1]` and `[0,2]` (`[0,0,1] → [0,0,4]`), the sound-but-loose
   enclosure of `x² + 1` on `[−1,1]` (`lo = 0, hi = 2, sign = 0`), its refinement at `splits = 2`,
   the convex quadratic at one and two parts, and node containment at `splits = 1, 2, 4`;
3. the slide certificate on `Block45(5,4)` — certified on `[½,1]`, refused on `[−1,1]`, gate
   endpoints positive;
4. `bernstein_cage_crosscheck` on `Block45(5,4)` — 65 cells, capacity `>=2`, extents
   `33/4` and `23/2`, chord instrument refusing, all Bernstein verdicts "not short", `agree`;
5. the residue screen on `Block45(5,4)` — 266 pairs, 172 contacts, 70 rejected, 196 survivors,
   24 extra, 0 false rejections, invariants `survivors + rejected == pairs` at every modulus;
6. the same screen on `Block45Half(5,4)` — 182 pairs, 112 contacts, survivors exactly the contacts;
7. the plugin itself on three contact pairs — a residual is zero, so its norm residue is zero at
   mod 8, 12 and 24.

`--audit` reports **294 functions, 0 naming `float`**. That number is a fact about bytecode, not
about mathematics: it proves no stage can read a float and says nothing about whether the stages
are correct. Control 31 is what says they are correct — and its assertions are the ones above, so
the two checks cover different things on purpose.

## 5. What this run does not claim

* **No row moved.** Neither plugin proposes a sentence; they certify or refute ones that exist.
* **The mask is not a contact classifier.** It is exact on the Block45Half cells and a superset
  elsewhere; the gate remains the decision procedure.
* **The speedup is small and explained.** 1.1–1.4× end-to-end on contact-dense cells, limited by
  Amdahl, not by the mask's cost — and it is a timing, so it is quoted as a range, while the
  rejection counts beside it are exact and repeat identically.
* **Bernstein is incomplete.** A coarse enclosure can straddle a true sign, and no number of
  splits is guaranteed to fix it; the stage certifies, it does not decide.
* **The Lean cross-references remain informational.** Nothing here is verified in Lean or exported
  to it.

## 6. Next

The natural next stage is the one the ladder and the mask's blind spot both point at: a **pair
predicate that also reads the loose side**, i.e. a cheap exact bound on `max slack` rather than on
"some axis is tight". That is the quantity the gate actually counts, and a sound bound on it would
reject the diagonal survivors the residue mask must keep. It is a different instrument from both
plugins here — a bound, not a residue and not a basis change — which is exactly the kind of stage
this pipeline is built to accept.

**Update (run 101).** The stage above now exists: `pair_max_slack_bound` bounds a pair's **max**
slack — not its tightest axis — by `|A + B√d| ≥ 1/(|A| + |B|S)`, which is exact integer
arithmetic on the `2D²`-scaled residuals. On `Block45(5,4)` it rejects all 94 non-contacts and
leaves exactly the 172 contacts for the gate; on the synthetic lattice it removes the 162 diagonal
survivors the mod-8 mask had to pass (252 → 90). Two findings moved numbers rather than prose:
the gate's own `Quad` prune, not the pair test, was the benchmark's bottleneck (the chain now
prunes on integer components, which is where most of the end-to-end 1.9–5.1× comes from), and the
mask turns out to be **contact-safe but not verdict-safe** — an overlap has no tight axis either,
so the mask hides violations unless feasibility is already assumed, while the bound never does.
Doc 64 §5 records the chain, the correction and the counter-example.
