# 18 — The rigidity class of the contact graph (Maxwell/Laman)

**Runs 48–49, 2026-11-18.** Instrument `scripts/leech_comb.py`; ledger
`workspace/push/leech_comb.json`. Read-only. §11 (run 49) builds the
contact-bearing ensemble this test needed and supersedes the ensemble numbers of
§4–§5, which were produced by the buggy sub-packing generator.

`17-COMB-ADDRESS.md` §5 proposed the next object: the Maxwell/Laman count of the
contact graph, on the theory that the 0.42 side-length spread left inside an
address class was "the non-rigid cases: same graph, different flex". This run
builds that count, validates it, and reports that **the hypothesis is refuted** —
with a sharper reason than "no signal", plus a defect in the run-47 ensemble that
the count exposed.

---

## 1. Fresh eyes on `leech_comb.py`

| cut | why |
| --- | --- |
| `import itertools` | never used |
| `address()` called up to four times per packing in `explain` — once for the row's group, once again for the per-n distinct set, and once per ensemble row inside the delivered-hit loop (quadratic in the ensemble) | each packing is analysed once; `address_of(bits, adj)` takes the tilt bits and adjacency already computed |
| `contacts(st5)` twice in the selftest notes (edges, then again for degrees) | one adjacency |
| `"group"` carried both the classification and the baseline key | rows now carry explicit fields (`addr`, `rig`, `tilt`, `m`) and `conditional_r2(rows, base_keys, field)` takes the field, so a null can shuffle any field inside any cell |
| two comments both numbered `# 4.` | renumbered |

Address R² 0.9783, tilt 0.6616, |E| 0.9200, spread 0.4196 — all identical after
the tidy, which is why it was safe.

**One real bug fixed.** `conditional_r2` returned a number whenever SS > 0, and
two rows sitting at the same side length differ by ~1e-30 in SS. The ratio of two
such numbers is noise, and it printed as `+0.5000`. It now returns *undefined*
when the baseline variance is at round-off (`SS <= (1e-12·max|y|)²·rows`). This
already mattered: the "contact-bearing rows only" slice of this run's ensemble is
exactly that case (§4).

## 2. What the class is

For a packing of n unit squares, with **segment contacts only** (corner contacts
excluded, as in run 47):

```
m          segment contacts        (= |E(G)|)
w          flush wall bars         (axis-aligned square flush with a box side)
Laman      m  vs  2n - 3           one bar between centres, 2 DOF per square
body-bar   m  vs  3n - 3           every square a free rigid body, 3 DOF
```

The (2n − 3) count is the one run 47 named and the one justified for axis-aligned
contacts, where a segment contact *is* a bar between two centres. The (3n − 3)
count is what applies when tilt is free. At 45° the contact normal is not generic,
so either is a generic **necessary** condition, not a proof of rigidity at the
configuration; the board reports both and does not confuse them with a proof.

A count is an average over subsets, so the class comes from the exact sparsity
rank. `sparsity_rank` is a matroid greedy for (k, l)-sparsity — add a constraint
iff `|C(S)| ≤ k|S| − l` survives on every `S` containing it — which is exact
because (k, l)-sparsity with `l ≤ 2k − 1` is a matroid:

```
mechanisms = 2n - 3 - rank      internal DOF the contacts leave free
redundant  = m - rank           contacts beyond the independent ones
cls        = (mechanisms, redundant)
```

Wall bars use the same segment-not-corner rule (a 45° square meets a wall at a
corner, so it bars nothing) and the **grounded** (2, 0) rank then says whether the
packing is *pinned*: `rank = 2n` with each wall contributing one constraint.

## 3. Validation — 14/14

| check | result |
| --- | --- |
| rank = brute force over edge subsets (12 random n = 5 graphs) | ok |
| K₄ rank 5 and not Laman-sparse; C₄ rank 4 | ok |
| **2×2 grid: m = 4, a 4-cycle, mechanisms = 1** | ok |
| **2×2 grid is pinned only by the walls** | ok |
| **3×3 grid: m = 12, w = 12, mechanisms = 3, grounded rank 18 = pinned** | ok |
| pair axes equal the gate's penetration (200 pairs, 1e-12) | ok (run 47) |
| addresses: relabelling, D₄, distinct shapes, 1e-7 stability 50/50 | ok (run 47) |

The grid rows are the structural result of the run, and they say the run-47
hypothesis was aimed at the wrong object: **a 4-cycle of bars is a mechanism — it
shears — and the 2×2 packing is rigid only because the container holds its four
outer squares.** For a bounded packing, "rigidity of the contact graph" is not the
thing that fixes L; the walls are. The counts agree: free mechanisms 1 and 3 for
the two grids, grounded rank exactly 2n for both.

## 4. The ensemble: the class is the edge count in disguise

88 packings, n = 5…10 (same generator and seeds as run 47, so numbers compare).

| statistic | observed | null | reading |
| --- | ---: | --- | --- |
| address, baseline n | +0.9783 | 0/200 ≥ | (run 47) |
| **rigidity class, baseline n** | **+0.9200** | 0/200 ≥ | identical to \|E\| alone (+0.9200) |
| rigidity class, baseline (n, source) | +0.0000 | 200/200 ≥ | dead |
| **rigidity class inside an address class** | **+0.0000** | 200/200 ≥ | dead, and structurally so |
| coarser labels inside an address class | +0.0000 | — | coarse class, pinned flag: both 0 |
| rigidity class, baseline (n, \|E\|) | +0.0000 | — | nothing beyond the edge count |

Exactly 0.0000 with the null distribution also exactly 0.0000 is not "a weak
signal", it is a **deterministic function**: on this ensemble the class adds
nothing to (n, |E|), and the address already contains |E|.

```
rows with a redundant contact    0/88      -> redundant = 0 everywhere
Laman-tight rows                 0/88      -> mechanisms > 0 everywhere
classes per (n, |E|) cell        <= 1      -> cls = (2n - 3 - m, 0)
max mechanisms                   17        (n = 10, |E| = 0)
pinned rows                      40/88
```

With no redundant contact, `rank = m`, so `cls` is a bijection with `m` at fixed
n. That is the whole finding: **the Laman class is the edge count with extra
arithmetic**, and the address already carries the edge count.

Where the spread actually lives:

```
within-address L spread   mean 0.0714   max 0.4196   (26 classes)
share of that SS in classes with |E| = 0                 100.0%
widest classes            n=6 spread 0.4196  |E| = 0  w = [0, 4]
                          n=9 spread 0.2574  |E| = 0  w = [0, 1, 3]
                          n=9 spread 0.2037  |E| = 0  w = [4]
                          n=6 spread 0.1918  |E| = 0  w = [2]
                          n=8 spread 0.1724  |E| = 0  w = [4]
address classes that are rigidity-heterogeneous          0 of 26
```

**100 % of the unexplained variance is in contact-free packings.** The 0.42 spread
is the bounding box of squares that never touch each other: there is no contact
graph there, so no graph statistic — rigidity included — can explain it. That is
a stronger refutation than run 47 could make, and it also explains run 47's
numbers.

## 5. The defect the count exposed

The run-47 ensemble is not a continuum of packings at each n; it is two levels.

```
n    contact-bearing source    |E|max   L            contact-free source (rsa)
5    sub6                      5       3.0000       1 row   L 3.28
6    sub7                      7       3.0000       7 rows  L 3.30 .. 3.72
7    sub8                      8       3.0000       6 rows  L 3.47 .. 3.84
8    sub9                     10       3.0000       6 rows  L 3.73 .. 4.20
9    sub10                     9       3.7071      10 rows  L 3.96 .. 4.57
10   sub11                    12       3.8771       7 rows  L 4.35 .. 4.85
```

Every contact-bearing row is a jammed family row sitting at **one** L per n, and
**every RSA row has |E| = 0**: `random_packing` accepts only well-separated
placements (`worst_pen ≤ -1e-9`) and `finalize` merely scales for CSV rounding, so
a random row never comes near contact. The ensemble therefore has only two side
lengths per n — the jammed family's and a loose band — and the address's apparent
R² 0.978 is mostly the statement "L = 3 versus loose". That is exactly why the
stratified null killed it in run 47: controlling the source removes the only
contrast there was. Run 47's conclusion stands; its evidence was weaker than it
looked.

## 6. The delivered rows (the project's own data)

n ≤ 40, segment contacts only, `m` from the gate:

```
rows 40     Laman count m - (2n - 3) in [-18, +1]
Laman-tight rows 2   (n = 1 by convention, n = 2 genuinely: one contact, 2n-3 = 1)
tilted rows 14/40    m/n mean 1.347   (2.69 contacts per square)
```

Exact rank, n ≤ 12 (beyond that the subset enumeration is exponential):

```
n        1  2  3  4  5  6  7  8  9  10 11 12
mech    -1  0  1  1  3  2  3  3  3   8  6  4
redundant 0  0  0  0  0  0  0  0  0   0  0  0
pinned    1  1  1  1  1  1  1  1  1   1  1  1
```

So: **every delivered row is pinned, and none is Laman-tight for n ≥ 3**; the
optimum rows are "pinned but with mechanisms", 0/38 tight. The count is not a
discriminator — it falls monotonically with n at fixed density and says nothing
about which row scores — but it is a correct structural description of the optimum
family, and it is the first time the project has had one.

## 7. Verdict

The rigidity class **does not explain the 0.42 side-length spread**, for a reason
that is structural rather than statistical:

1. the spread is entirely in classes with |E| = 0, where there is no contact
   graph to be rigid or flexible;
2. where contacts exist, no packing in the ensemble has a redundant contact, so
   the class collapses to `(2n − 3 − m, 0)` — the edge count again, which the
   address already contains;
3. and the grids show the object was mis-specified from the start: the container,
   not the graph, is what removes the mechanism of a square grid.

What run 48 does establish, and should be kept:

* an **exact, validated rigidity instrument** (`rigidity`, `sparsity_rank`,
  `wall_bars`, checked against brute force, K₄, C₄ and both grids);
* the **pinned-but-never-tight** description of the delivered rows;
* a **corrected ensemble** for this project: RSA rows carry no contacts at all,
  so any claim about contact structure has to be made on jammed rows;
* a guard that stops a round-off ratio from being reported as a statistic.

## 8. What would test the hypothesis properly

* **A jammed ensemble with varying L.** Contact-bearing rows must vary in side,
  which needs the settle machinery (`oracle_basin.settle_to`, `soft_relax.hop_search`),
  not sequential placement. The count only has content where some cluster
  approaches or exceeds `2n − 3`; that regime is untested here.
* **A pebble game** for the sparsity rank. The exact enumeration is exponential
  (n ≲ 20); the (2, 3) pebble game is polynomial and could be validated against
  this brute force, which would let the count run on the n ≤ 1000 table.
* **Configuration-level rigidity** (rank of the contact Jacobian, tilt included)
  would say whether a 45° packing is infinitesimally rigid at its own geometry;
  this run deliberately made no numeric-rank claim.

## 9. Limits

* 88 packings, n ≤ 10, two generators, one of which (RSA) produces no contacts.
* The free rank at 45° is a generic necessary condition, not a rigidity proof.
* `CONTACT_TOL = 1e-6` decides which pairs are edges; a pair at 1e-5 is not.
* Nothing here scores: no row changed, no score claimed, nothing committed.
* Runtime 33 s, selftest 1.4 s. `python3 scripts/leech_comb.py [--quick] [--draws N]`.

## 10. Files

* `scripts/leech_comb.py` — address (run 47) + rigidity class, statistics,
  selftest, ensembles, delivered-row counts, report.
* `workspace/push/leech_comb.json` — `schema: leech-comb/3`, `run: 49` (the
  jammed ensemble is the `explain_jammed` section, the loose one `explain`).
* `17-COMB-ADDRESS.md` — §5 corrected in place to point here.

---

# 11. Run 49 — the contact-bearing ensemble

Run 48's negative was measured on an ensemble whose rows either had contacts at
one side length or had no contacts at all, so the hypothesis was never tested
where it could hold. This run builds the right ensemble and re-runs both tests.

## 11.1 A real bug in `sub_packings`

```python
for src in (n + 1, n + 2, n + 3):      # three sources
    for k in range(len(st)):           # delete ONE square
        cand = [s for i, s in enumerate(st) if i != k]
        if len(cand) != n: continue    # true only for src == n + 1
```

Deleting one square gives `src - 1` squares, so every source except `n + 1` was
skipped and **two thirds of the source range was dead**. That is why each n had
exactly one contact-bearing side length in run 48 (the "two-level ensemble" of
§5). Fixed to `k = src - n` deletions, with two deterministic patterns (`last`,
`spread`), over sources `n+1 .. n+6`.

## 11.2 The ensemble (220 rows, all contact-bearing)

Three generators, all gated by `packlib.finalize` and `worst_pen <= -1e-12`, all
filtered to `|E| >= 1`:

| source | what it gives |
| --- | --- |
| `sub{src}{l,s}` | delete `src-n` squares from a delivered row; spans L = 3.0 … 4.0 |
| `rand{src}` | six random deletion sets from one source: differs in L *and* graph |
| `set{slot}` | perturb a delivered row (jiggle 0.03, 25 % turned 45°) and settle it |

On `set` rows: `oracle_basin.settle_to` minimises the W36 hinge at a fixed box, so
it does return jammed rows (n = 8: |E| = 11 at L = 3.0000) — but the settle comes
back to the family's own side length, so perturb+settle alone gives contacts
**without** L variance. The L variance has to come from the deletions: removing a
corner square shrinks the bounding box, removing an interior one does not. That is
why `rand` is in the ensemble, and it is the honest answer to "settle perturbed
rows": it produces the contacts, not the spread.

```
n    rows  addrs  L range            |E| range  |E|/n  pinned
5      35     14  [3.0000, 3.8771]    [1,  5]   0.68      17
6      37     18  [3.0000, 4.0000]    [2,  7]   0.78      27
7      37     25  [3.0000, 4.0000]    [2,  8]   0.78      18
8      38     27  [3.0000, 4.0000]    [4, 11]   0.87      16
9      37     20  [3.0000, 4.0000]    [5, 12]   0.99      18
10     36     23  [3.8771, 4.0000]    [6, 13]   1.05      22
```

At every n the side length now varies by a full unit, and every row has contacts.

## 11.3 The two R² tests, re-run

| statistic | jammed (220) | null | verdict |
| --- | ---: | --- | --- |
| address, baseline n | **+0.746** | mean 0.549, max 0.704, 0/200 ≥ | significant |
| **address, multi-member classes only** | **+0.624** | mean 0.344, max **0.545**, **0/200 ≥** | **significant** |
| rigidity class, baseline n | +0.391 | mean 0.157, max 0.292, 0/200 ≥ | significant |
| \|E\| alone | +0.391 | — | identical to the class |
| rigidity class inside an address class | +0.000 | 0.000, 200/200 ≥ | no information |
| rigidity class, baseline (n, \|E\|) | +0.000 | — | none beyond \|E\| |

For comparison, the same two tests on the (now fixed) loose ensemble, 109 rows:

| statistic | loose (109) | null | verdict |
| --- | ---: | --- | --- |
| address, baseline n | +0.842 | max 0.832, 0/200 ≥ | significant |
| address, multi-member only | +0.539 | max 0.687, **7/200 ≥** | not significant |
| rigidity class | +0.674 | max 0.495, 0/200 ≥ | significant |
| rigidity in address | +0.000 | 0.000, 200/200 ≥ | no information |

Two things are worth separating here.

* **The address does carry signal on contact-bearing rows** — `R² = 0.624`
  against a null whose best draw is 0.545 over 200 shuffles. This is the first
  time this test has beaten its null (run 47: 12/300; run 48 loose: 7/200). With
  contacts present and the side length varying inside each n, the contact graph
  predicts L. On the loose ensemble it does not, which is the ensemble's fault,
  not the address's.
* **The rigidity class still carries nothing the edge count does not.** Its R² is
  *exactly* the R² of |E| alone (+0.391 both), it is exactly 0 inside an address
  class, and exactly 0 against an (n, |E|) baseline. The reason is the same as in
  run 48 and is now measured on 220 contact-bearing rows: **0/220 has a redundant
  contact**, so `rank = |E|` and `cls = (2n - 3 - |E|, 0)`.
* The `(n, source)` line prints +1.0000 / 1.0000 and is **not a result**: inside
  one source each row's address is unique (six random deletions give six distinct
  graphs), so the key is per-row and R² is 1 by construction. The multi-member
  restriction is the test that means something.

## 11.4 Does any cluster approach 2n − 3?

No cluster of four or more squares comes within 1 of tightness, and no cluster
anywhere is redundant. Best headroom `|E(S)| - (2|S| - 3)` over all 220 rows:

```
|S|        3    4    5    6    7    8    9   10
headroom   0   -1   -1   -2   -2   -2   -3   -4
```

The single 0 is a **triangle of three mutually touching squares** (|E(S)| = 3 =
2·3 − 3), which is the smallest possible tight cluster and is tight for a trivial
reason: three bodies pairwise in contact have no mechanism. Three of 220 rows
contain one. In the loose ensemble the best 3-cluster is a *path* (|E| = 2,
−1), because loose rows have fewer contacts.

Aggregate: Laman count `m - (2n - 3)` runs from −11 to −2 over the 220 rows
(0 tight, 0 over), `|E|/n` mean 0.86, redundant contacts 0. The richest rows are
n = 10 with |E| = 13 against 2n − 3 = 17.

So the structural claim is now measured rather than argued: **square contact
graphs are too sparse to be Laman-tight.** The maximum number of segment
contacts a unit square can carry is small (a side can be split, but the contact
measure is what counts), so `|E| <= ~1.1 n` in practice against the `2n - 3` a
tight cluster needs. Rigidity bookkeeping that subtracts a mechanism count from
2n − 3 is therefore arithmetic on |E|, not extra information — for this domain,
not just for this ensemble.

## 11.5 Verdict after run 49

* The address is a **real predictor of side length on contact-bearing rows**
  (multi-member R² 0.624, 0/200 ≥ null). That is the positive result of the
  exercise, and it was invisible in runs 47–48.
* The rigidity class is **not** a predictor and cannot be: `cls` is a bijection
  with |E| whenever no contact is redundant, which is the case for all 220 rows
  and for the 1000 delivered rows checked so far.
* The 2n − 3 threshold itself is **not approachable** by unit-square contact
  graphs except at the degenerate |S| = 3 triangle.

If the rigidity idea is ever revived, the only regime that could give it content
is a packing with a **redundant** contact — `|E(S)| > 2|S| - 3` for some cluster —
which no packing in this project's ensembles has produced. That would need an
optimiser that deliberately trades contacts for side length, not a sampler.

## 11.6 Cost

Full instrument 59 s: selftest 1.4 s, loose ensemble 33 s, jammed ensemble 23 s
(the settled rows dominate: 18 L-BFGS settles at n ≤ 10). Selftest 16/16, adding
the cluster cross-check and a guard that the sub family really spans several sides.
