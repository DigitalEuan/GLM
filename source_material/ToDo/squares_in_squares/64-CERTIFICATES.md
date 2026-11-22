# 64 — The certificate boundary: exact ground truth on rungs 3 and 7, projections on rung 4

Run 101, 22 November 2026. A build-and-boundary run: no row moves, no score is claimed,
`submission.csv` and root `WHITEBOARD.md` are untouched.

Doc 63 ended with a stage it did not have yet — a cheap bound on a pair's max slack — and with a
chain whose stages were all sound but not all *verdict-safe*. This run adds that stage, adds the
serialized certificate and its standalone verifier, and then draws the line the request asked for:
**what in this project is exact ground truth (rungs 3 and 7) and what is a projection (rung 4)**.

The one-sentence version: a certificate is the object; every decimal in this project is a view of
it, and the verifier never reads a view.

| | |
|---|---|
| certificate file | `workspace/push/galois_certificates.json` (302 KB of exact strings, 7 certificates) |
| verifier | `scripts/verify_certificates.py` — standalone, imports the tower only, 27 decision functions, 0 naming `float` |
| new stage | `pair_max_slack_bound` (driver) on `integral_sign` / `abs_lower_bound` (tower) |
| chain modes | `--chain` (ledger `workspace/push/plugin_chain.json`), `--certificates` (+ the verifier's 9 mutation tests) |
| controls | **32** (control 32 is new), 2 m 37 s |
| audit | **324** functions checked, **0** naming `float` (the verifier module is audited too) |

## 1. The format

`galois-certificate/1`. One document, an explicit `conventions` block, an explicit `display_only`
block, and a list of certificates. A certificate is:

```
{ id, family, field, N, L, origin, cells: [ {x, y, r: [ux, vx, uy, vy]} ], expected, note }
```

* **`field`** is a tag: `Q`, `Quad(2)`, `Quad(5)`, `Quad(7)`, … Every number in that certificate
  is a scalar of that field.
* **a scalar** is a *string* under `Q` and an `[a, b]` pair under `Quad(d)`, meaning `a + b√d`.
  The strings are canonical reduced fractions (`"-7/4"`, `"1/2"`). A decimal spelling is refused
  by the parser, not rounded: `1.5` has an exact rational value, but in this format it is a
  display spelling, and a display spelling is a projection.
* **`r`** is the rotation matrix row-major: `[ux, vx, uy, vy]`, i.e. `R = [[ux, vx], [uy, vy]]`.
  Storing both rows is what makes `R^T R = I` and `det R = 1` *checkable* rather than assumed —
  the word is `u`, and `v` must be its quarter turn, exactly.
* **`L` and `origin`** are the exact container: the box `[ox, ox + L] × [oy, oy + L]`. `origin`
  is the sentence's own bounding-box corner and `L` its exact side, so the box is *tight* rather
  than a family convention — which is why the ring's certificate has a negative origin
  (`-7/4 - 1/4√7`) and the block's does not (`0`). Both are correct; neither is assumed.
* **`expected`** is the gate's own summary (`ok`, `contacts`, `violations`, `clearance`). The
  verifier recomputes it and refuses a document whose declaration the object does not have.

The path is not new, and what it held is worth naming. `workspace/push/galois_certificates.json`
previously carried an older export: a flat list of `{family, n, s_exact, s_float, degree,
minimal_polynomial, galois_group, verified_worst_pen}` records. That is a *report about* exact
values — it has an `s_float` and a float penetration, no frame, no centres and no container — so it
could not be verified, only read. This run replaces it with the schema above; the old file stays in
git history (commit `3668c31`) and is preserved as the example of the thing this doc separates out:
a summary that mentions exactness is not a certificate.

A ring cell, exactly as written:

```json
{"x": ["-5/4","-1/4"], "y": ["-5/4","-1/4"], "r": [["1","0"],["0","0"],["0","0"],["1","0"]]}
```

That is `x = -5/4 - 1/4√7`, `y = -5/4 - 1/4√7`, and the axis rotation `((1,0),(0,1))` — all in
`Quad(7)`, no decimal anywhere.

## 2. The verifier, and the two ways a certificate can fail

`scripts/verify_certificates.py` is a reader: it loads the file, rebuilds every sentence from the
file alone, and decides it. It does not import `glm_wheels`, does not build a sentence, and never
sees a float (it is in the bytecode audit's module list).

The checks, in the order that makes the first failure meaningful:

1. **schema** — format tag, id, `N == len(cells)`, non-empty cells;
2. **number format** — canonical exact strings only (this is where a decimal dies);
3. **`R^T R = I`** — `u·u = 1`, `v·v = 1`, `u·v = 0`;
4. **`det R = 1`** — an orthogonal frame that is a reflection fails here, not at (3);
5. **walls** — every cell inside the declared box, by exact comparison;
6. **declared side** — `L` equals the sentence's own span (a looser `L` is a different container,
   and the certificate does not get to claim one);
7. **SAT** — for every pair, all four axes (`|Δ·q| − (½ + ext_other(q))`), the witness axis and
   the exact gap recorded, `≥ 0` accepted at clearance 0 — decided on **integer components**, see
   below;
8. **declared summary** — contacts, violations, clearance recomputed and compared.

**The SAT pass does not reuse the gate's formulation.** The producer multiplies `Quad` values
(`qsqrt2.pair_axes`, `Q.gate`). The verifier instead takes one even common denominator `D` over
every coordinate and every frame component, so each is an integer pair of `Z[√d]`, and carries
each slack as the exact integer residual

```
2 D² · slack  =  2 |Δ · q|  −  ( D² + |u_other · q| + |v_other · q| )
```

with `Δ` and `q` the `D`-scaled centre difference and axis. Since `2D² > 0`, the sign of that
integer pair *is* the sign of the real slack; `abs` is the tower's exact sign rule on integer
components, `max` is an integer comparison, and nothing here is `Quad` arithmetic. The only place
a field element is rebuilt is `_scaled_str`, which prints the gap into the report **after** the
verdict. `sat_pass_reference` keeps the `Quad` formulation alive as a *witness* — it never decides
a certificate; `cross_check` (run by `--selftest`) compares the two implementations pair for pair,
and on the shipped document all **4,532 candidate pairs** agree on the sign *and* on the exact
largest slack of the pair (the reference value scaled by `2D²` equals the integer residual
exactly). That is independence of implementation, and it is measured rather than asserted.

One document only exercises the pairs it happens to contain, so the two passes are also
**fuzzed against each other** (`fuzz`, `--fuzz [N] [SEED]`, and 30 sentences inside `--selftest`).
A random sentence is a field tag, 2–7 centres drawn from mixed denominators (halves, thirds,
quarters, fifths) with random `√d` parts, and frames from that field's exact unit words — found
by one small integer search, `ab + ce = 0` and `a² + d b² + c² + d e² = m²`, so no word is
hard-coded. A third of the centres are copies of an earlier one, or a copy pushed by `1/10`,
`9/10`, `1/2` or `3/5`, so coincidences (strict overlaps), near-overlaps, exact contacts and
separated pairs all occur, and the common denominator reaches the lcm of the denominators (120 in
practice). Every pair's exact largest slack is compared (`2D²` times the witness value against the
integer residual), along with verdict signs, contact and violation counts and the printed
clearance: **9,729 pairs over four seeds of 400 sentences, 0 mismatches** (64 contacts, 5,314
overlaps, 4,351 separated).

The fuzz paid for itself on its first run. The printed clearance and the printed gap divided the
integer residual by `D` instead of `2D²`, so a violation of `1/10` was reported as `1` when `D =
10`; the shipped document's clearances are all exactly `0`, where the divisor is invisible, and
only the fuzz saw it. Verdicts, contacts and orderings were unaffected — the bug was in the number
printed, not the decision — and the scaled comparison is now part of what the fuzz checks.

The failure is always *the first exact inequality that is wrong*, and it carries one of two kinds:

| kind | meaning | examples |
|---|---|---|
| `infeasible` | the object is representable and an inequality is false | a pair overlaps (with the exact gap), a cell crosses a wall, a frame is a reflection, a frame is not orthonormal |
| `outside_representation` | the file does not represent an exact sentence at all | a decimal string, a wrong scalar shape, an unknown tag, a duplicate id, a declared `L` that is not the sentence's side, a declared summary the object does not have |

That distinction is the whole point of the exercise. "This sentence overlaps by 1/10" and "this
file spells a coordinate as `0.5`" are different failures: the first is mathematics, the second is
a serialization that cannot carry the mathematics. A verifier that reported both as "invalid"
would hide the difference — and the difference is exactly where rung 4 leaks into rung 3.

The verifier's own test mutates the shipped document nine ways and asserts each fails at its own
check:

    decimal string · reflection frame · non-unit frame · centre pushed through the wall
    loose declared side · wrong format tag · duplicate id · declared count · declared summary

All nine are refused, and the untouched document still verifies — a verifier that only ever says
"yes" would pass the first half of that sentence, which is why the second half is asserted.

## 3. What is serialized

Seven representatives, one per field tag we hold, and the four families the request named:

| id | field | N | L | contacts | void |
|---|---|---:|---|---:|---|
| `tile2` | Q | 4 | `2` | 6 | `0` |
| `ring18` | Quad(7) | 18 | `7/2 + 1/2√7` | 26 | `-4 + 7/2√7` |
| `staircase149` | Quad(7) | 149 | `23/2 + 1/2√7` | 449 | `-15 + 23/2√7` |
| `staircase150` | Quad(7) | 150 | `23/2 + 1/2√7` | 451 | `-16 + 23/2√7` |
| `block45_5_4` | Quad(2) | 65 | `5 + 5/2√2` | 172 | `-55/2 + 25√2` |
| `block45half_17_14` | Quad(2) | 653 | `29/2 + 17/2√2` | 2256 | `-1193/4 + 493/2√2` |
| `slope21` | Quad(5) | 5 | `2 + 1/3√5` | 4 | `-4/9 + 4/3√5` |

Every summary above is the verifier's recomputation, not the builder's claim — the builder's
claim is the `expected` block, and a mismatch is a failure. The void is `L² − N` in the
certificate's own field, so it is an exact algebraic number, not an area estimate.

The document also carries a `display_only` ledger, and it is the answer to "what is a
projection?" in one place:

| surface | exact? | what it is |
|---|---|---|
| `submission.csv` | **no** | 12-dp decimal strings: a projection of the pose, never an input to an exact check |
| `README.md` / `STATUS.md` tables | **no** | rounded for reading; each number has an exact source elsewhere |
| CLI and event prints | **no** | Decimal shadows at 12 dp; where a decision is printed, the exact string is printed beside it |
| `galois_certificates.json` | **yes** | the object: exact tags, rotations, centres, side, summary |

## 4. The exact / display ledger, area by area

The request named eight areas. For each: what is exact, what is a projection, and which one
decides.

| area | exact surface (rungs 3 and 7) | projection (rung 4) | who decides |
|---|---|---|---|
| **angle t-basis** | `word_t(t)` returns rational `(cos, sin)` in `Q`; `_sqrt7_word()` returns the census word in `Quad(7)`; `R^T R = I` is checked per cell | the row's stored 12-dp angle string, `atan2` prints | the exact word: a pose whose cosine is not in the field cannot be *represented*, and the verifier says `outside_representation` rather than rounding it in |
| **composition** | `strip_field`, `staircase_field`, `p_ring`, `p_ridge` build from declared contacts and derive `L`; every builder output is gated | the census's 12-dp centres are used to *choose* which contact is which (`lift_sentence`, `cage_segment`) | the gate: topology may be chosen by a projection, but the sentence is re-decided exactly |
| **container bounds** | `Q.side` (exact), the certificate's `L` and `origin`, wall and tightness checks | "L = 8.535534" style columns, CSV extents | the verifier: `L` must equal the sentence's own span |
| **SAT gate** | `Q.gate`, `Q.pair_axes`, `pair_max_slack_bound`, the verifier's own four-axis pass | `packlib.verify` (a float-side witness, declared exempt in the audit), CSV clearances ~2e-9 | the exact gate; the float gate is a witness and never a verdict |
| **coordinate lifting** | `lift_sentence` with `recover_side` / `recover_point`: exact comparisons, height-bounded recovery | the 12-dp decimal pose that supplies the topology | the recovered sentence, gated at clearance 0; the input decimals are rung 4 and are said to be |
| **seam solver** | `seam_floor` (`min(x, 1/x)`), `two_word_need` (`28/25` for the 3-4-5 pair), the `w*(m)` roots | printed widths and seams (`2.221392`) | the exact law; the printed value is orientation only |
| **delta-sigma stream** | the accumulator is a field element and legality is the sign of its error (`(r − √2)/2` for the Pell map) | the retired float-fed carrier, and every `1/N`-convergence plot | the exact legality test; the stream is a construction device, not a certificate |
| **field-tagged carriers** | `Claim.payload` holds `Quad` values; the certificate's `field` tag; `field_triage`'s exact recovery | `field_triage`'s 70-digit Decimal *classification* of a delivered row (a measurement; "continuous" when no field fits) | the tag: a carrier either is in the field or the document is refused, and a measured classification is never promoted to a tag without a gate |

Two of those rows are worth spelling out because they are the ones that could go wrong quietly.

**Lifting is rung 4 in, rung 3 out.** A delivered row is a 12-decimal pose; recovering it exactly
means *guessing* a topology from decimals and then deciding it exactly. The guess is a projection
and is labelled one; the decision is not. That is why the mixed lift is 99/100 poses and 100/100
topologies: the projection can fail without the mathematics being wrong.

**The float gate is a witness, not a verdict.** `packlib.verify` is declared exempt from the float
audit for exactly this reason: it is an independent instrument on the *other* side of the
boundary, and every verdict reported in this project comes from the exact side. The audit's
exemption list is the machine-readable form of that sentence.

## 5. The stage doc 63 §6 asked for: a max-slack bound

Doc 63 §6 said the next stage should be "a cheap exact bound on max slack rather than on 'some
axis is tight'". It is now `pair_max_slack_bound`, and the phrasing needed one correction.

**The correction.** The request's phrasing — "pairs whose tightest axis still has positive
separation" — names the *minimum* slack. That is the wrong object: a diagonal neighbour has one
axis exactly tight (`slack = 0`) and one loose (`slack > 0`), so its tightest axis is the tight
one and a bound on the minimum would keep every diagonal survivor. What decides the pair is the
**maximum** slack: the gate calls it a contact iff `max = 0`, a violation iff `max < 0`, so a pair
with `max > 0` is neither and may be dropped. The stage bounds the max.

**The bound.** For an integral residual `z = A + B√d`, `|N(z)|` is a positive integer when `z` is
nonzero, so

    |z| = |N(z)| / |z̄| ≥ 1 / (|A| + |B| S)      for any rational S ≥ √d,

and `z > 0` is an integer comparison of `A²` with `dB²`. So a positive residual comes with a
positive rational lower bound on the pair's max slack, computed with no division by a field
element and no `Quad` at all. The scan stops at the first axis it can prove positive.

**What it buys, measured.** On `Block45(5,4)` it speaks for all 94 non-contacts and leaves exactly
the 172 contacts for the gate; on the synthetic lattice it turns the mask's 252 survivors into
the 90 contacts, i.e. it removes the 162 diagonal survivors the mod-8 mask had to pass.

The chained pipeline (`--chain`, ledger `plugin_chain.json`), five rows and three configurations.
`gate` is the exact 4-axis pass on the survivors; "filters alone" is the ratio of the exact pass
over *all* candidates to the filters plus the survivor pass, with the prune held fixed:

| cell | pairs | contacts | mask drops | bound drops | gate calls | hidden | pipeline vs gate | filters alone |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Block45(5,4) | 266 | 172 | 70 | 24 | 172 | 0 | 2.1× | 1.26× |
| Block45(10,8) | 1102 | 794 | 252 | 56 | 794 | 0 | 2.9× | 1.14× |
| Block45Half(5,4) | 182 | 112 | 70 | 0 | 112 | 0 | 2.2× | 1.33× |
| Block45Half(17,14) | 2978 | 2256 | 722 | 0 | 2256 | 0 | 5.0× | 1.08× |
| Lattice(3/2,1) *(synthetic)* | 342 | 90 | 90 | 162 | 90 | 0 | 4.7× | 2.55× |

Two honest readings, both of which moved a number rather than a claim.

**The prune, not the pair test, was the bottleneck.** The first version of this benchmark reported
4–6× for the filters alone — and it was measuring only the post-prune work, while `Q.gate` was
timing its own `Quad` prune over all `n(n−1)/2` pairs (212,878 of them at N = 653). Timing the
chain's prune as its own stage, and deciding it on integer components (`_zabs_ge`: `|z| ≥ s` iff
`z ≥ s` or `z ≤ −s`, one integer sign test each), fixed both: the end-to-end gain is 1.9–5.1×,
and the filters' own contribution is the 1.08–2.55× column. The lesson is not flattering to the
filters: on contact-dense cells their ceiling is small, and a cheaper exact prune was worth more.

**The mask is contact-safe, the bound is verdict-safe.** An overlapping pair has no exactly tight
axis either, so the mod-8 mask drops it — hiding a violation. The bound drops only pairs with
`max slack > 0`, which cannot be a violation. Control 32 puts a 1/10 overlap in front of both: the
mask hides the violation, the bound keeps it and the gate reports it. So the chain's contract is
recorded, not glossed: the mask may be used where feasibility is already assumed (which is every
certified cell here, and the benchmark reports `hidden = 0` for all of them), while the bound is
safe unconditionally. A stage's *soundness* and its *verdict-safety* are different properties, and
doc 63 §3's "every stage is sound, so the composition is safe" needed this qualification.

## 6. What the certificate does not establish

* It certifies **containment and non-overlap in the declared box** and the exact side of *that*
  sentence. It says nothing about optimality, and nothing about rows it does not contain.
* A tight `L` means the box is the sentence's own span — not that the sentence is better than any
  delivered row. No comparison with `submission.csv` happens in the verifier.
* The eleven mutation tests (ten distinct manipulations — the SAT overlap is written at two rungs)
  prove the verifier *fails closed* on those manipulations, including the one that reaches the
  integer pass: a three-square sentence inside its box, with the span exactly its declared `L`,
  whose cells at `(1/2, 1/2)` and `(7/5, 1/2)` overlap by `1/10`, is refused at `sat` with pair
  `[0, 1]` and gap `-1/10` (in `Q`, and again in `Quad(2)`). They are not a security audit: a
  determined forger can write a different valid sentence, and the verifier will accept it —
  correctly, because a certificate is a claim about a sentence, not a signature on one.
* `expected` is checked against the verifier's own recomputation, and that recomputation no longer
  copies the producer's arithmetic: the deciding SAT pass is integer-scaled and is cross-checked
  against the `Quad` witness pair for pair (4,532 pairs, exact value and sign). What this buys is
  **independence of implementation**; both formulations were still written by the same author, so
  a shared misreading of the SAT statement itself would survive the cross-check. What rules that
  out is external: the certificates agree with `Q.gate` on contacts, clearance and void, and the
  nine mutations are each refused at their own check.

## 7. State

32 controls (control 32: the bound's soundness and reach, the chain's equivalence and its one
counter-example, the integer/Quad mask agreement, the four-certificate round-trip, the refused
decimal, and the SAT pass's independence — its own `co_names` name no producer function, and
`cross_check` matches it against the `Quad` witness pair for pair, and the fuzz compares them on
random exact sentences with overlaps and mixed denominators), `--audit` **342 functions, 0 naming
`float`** (the verifier's 30 included), `--certificates` 7/7 verified plus **11 mutations**
refused — two of them genuine SAT overlaps, refused at `sat` with the exact gap `-1/10` — with the
same seven summaries and contact counts as before the change, `--chain` with its ledger, the
verifier's own `--selftest` (7 verified, 11 mutations, 4,532 pairs cross-checked, 145 fuzz pairs),
bare run exit 0, `record_guard.py` OK, README/STATUS footers byte-identical. Doc 63 §6 is updated with what actually landed.

**No row changed, no score claimed, `submission.csv` and root `WHITEBOARD.md` untouched.**
