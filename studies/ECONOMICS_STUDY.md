# The economic register, and the last third of the universality claim

*What `data_objects/economics_register.py`, `reasoning/economics.py`,
`RequestProject/GLM/LogBucket.lean` and `report economics` are for, and what
they measured.*

Every figure below is recomputed by the code that reports it. Run

```bash
cd overlay
PYTHONPATH=. python3 GLM.py -q "report economics" --verify-tct
```

and the third column re-derives the whole study in a fresh interpreter and
checks it key by key (`VERIFIED True`).

---

## 1. Why there is an economic register at all

`glm_study_findings_catalog.md` §6.2 makes a universality claim:

> the mathematics of homeostasis is universal — chemical equilibria, musical
> harmony and market price discovery all map to Leech proximity.

`HARMONY_STUDY.md` settled the musical third. The economic third stayed
**not implemented** for one round longer, and for the same honest reason: the
package held nothing economic to run the sentence against, and a claim nothing
can be run against is not a finding, it is a sentence.

The awkwardness of the economic third is that, unlike an interval, a price is
not arithmetic. It is a measurement, with a unit, a denominator and a date, and
it arrives as a decimal string. Two commitments make it admissible anyway:

* **exact rationals only.** The shipped CSV stores every price as a fraction
  of integers — silver as `47/2`, the euro as `109/100`, natural gas as
  `43/20` — and it is read as a `Fraction`, never as a float. Directive D2 is
  not negotiable, and it is what makes the sweep below reproducible bit for
  bit.
* **a named denominator.** Every non-currency instrument must name a physical
  quantity the *physics* register already holds — `energy`, `mass`, `volume` —
  and the record refuses to construct if it does not. A currency pair names
  none, because a ratio of two currencies is dimensionless, and the register
  says so explicitly rather than by omission.

## 2. The register

`load_price_register()` reads the shipped CSV and returns **21 records**: **7
instruments** across **4 sectors** (Agriculture, Currency, Energy, Precious
Metals) in **3 consecutive quarters** (2024-Q1 to 2024-Q3). **6** of the 21
records — the yen and the euro, in all three windows — are dimensionless
currency pairs; the denominators in play are `dimensionless`, `energy`, `mass`
and `volume`. **7** of the 21 prices are integral; the rest are exact
fractions.

Three quarters per instrument is not decoration. It is what turns *"prices are
points"* into something that can be **wrong**: with one window per instrument
every record is its own nearest neighbour class and no prediction is available.

## 3. Magnitude, by integer comparison alone

The carrier's first four coordinates are the exact base-2 and base-10
**magnitude buckets** and **mantissas**. The bucket is the unique integer `k`
with `base**k ≤ p < base**(k+1)`, and `compute_exact_log_bucket` finds it by
multiplying integers — for `p = n/q` and `k ≥ 0`, by comparing `q·base**k`
against `n` — so no logarithm is evaluated, nothing is rounded, and the answer
is exact at any magnitude. The base-2 buckets present in the register run from
**−1 to 11**, a span of **12**.

The tests exercise it at magnitudes no float reaches: `10**400 + 1/3` lands in
base-10 bucket **400** and `(10**-400)/3` in bucket **−401**, and the defining
inequality is then checked on the rationals themselves rather than on the
integer comparisons that produced the answer.

`RequestProject/GLM/LogBucket.lean` closes the same statements for every
rational and every base:

* `bucket_spec` — `base^(bucket p) ≤ p < base^(bucket p + 1)`;
* `bucket_unique` / `exists_unique_bucket` — the bucket is the *only* integer
  with that property, so the Python loop cannot be computing something else
  that happens to agree;
* `bucket_mono` — the bucket is monotone in the price;
* `bucket_zpow` — multiplying by `base^s` shifts the bucket by exactly `s`,
  which is the sense in which the coordinate is a *magnitude* and not a price;
* `mantissa_mem_Ico` — the leftover mantissa lies in `[1, base)`;
* `order_preserved_by_scaling` / `strict_order_preserved_by_scaling` — scaling
  every vector by one positive factor does not reorder squared distances.

That last pair is why the control in §5 is a single set of numbers rather than
a sweep, and it is worth being explicit about: it is a *proof* that the sweep
cannot be hiding a scale at which the control does worse.

## 4. The geometry, and the sweep

`price_vector` places each record in `Q^24`: the two buckets, the two
mantissas, the ten EXT10 exponents of its denominator quantity, and a
dimensionless flag — fifteen coordinates carrying content, nine zero. Each is
multiplied by an integer scale and decoded to the nearest Leech point.

| scale | distinct points (of 21) | τ against magnitude | nearest neighbour is same instrument |
|---|---|---|---|
| 1 | 7 | 39/70 | 21/21 |
| 8 | 11 | 39/70 | 21/21 |
| 64 | 18 | 39/70 | 21/21 |
| 256 | 20 | 39/70 | 21/21 |
| 512 | 20 | 39/70 | 21/21 |
| **1024** | **21** | 39/70 | 21/21 |

The lattice does not separate the register until **scale 1024**. The plateau at
20 across 256 and 512 is one pair and nothing else — the euro in 2024-Q1 at
`109/100` and in 2024-Q3 at `273/250`, a fifth of a percent apart — which has
to be pushed past the covering radius before the decoder stops rounding both to
the same point.

## 5. The verdict: not reproduced

Two of the three conditions hold, and they hold impressively.

* **Separation.** At scale 1024 every one of the 21 records has its own
  lattice point.
* **Tracking.** Every record's nearest neighbour is another quarter of the
  same instrument: **21 of 21**, against a chance rate of **1/10**. Kendall's
  τ of distance against magnitude is **39/70**.

The third condition is the one that decides it, and it fails.

* **The control.** The same distances taken on the *undecoded* vectors give
  **21 of 21** and **τ = 39/70** as well — identical, to the last digit.

So `21/21` is real and it is not evidence for the sentence under test. Two
quarters of one instrument have nearly equal prices, hence nearly equal
buckets, mantissas and exponents, hence nearby vectors in `Q^24` before any
lattice is involved; the decoder inherits that and adds nothing to it. The
claim is therefore recorded as **not reproduced**: *what was measured is real,
and it is not what the sentence says.* `reasoning/catalog.py` takes claim
§6.2's economic half straight from this module, so the ledger says the same.

This is the same shape of answer `HARMONY_STUDY.md` reached for the musical
third, by the same instrument, and the agreement is itself the result: across
two independent domains the Leech decoder is not contributing the structure the
claim attributes to it.

## 6. What would change the verdict

Not a bigger register — a register whose *undecoded* geometry is worse. The
control fails to be beaten because the price vector already encodes the answer;
a genuine test needs a question whose answer is not a monotone function of a
single coordinate. Two candidates, neither implemented here:

* **cross-instrument** structure — does a lattice neighbourhood collect
  instruments that co-move for an economic reason (crude and gasoline, gold and
  silver) rather than quarters of one instrument?
* **out-of-sample** structure — decode Q1 and Q2 only, and ask the lattice
  where Q3 should be.

Both are stated here rather than claimed, and neither is measured by anything
in the package as it stands.

## 7. Where each piece lives

| piece | file |
|---|---|
| the register, the record, the codec, the exact bucket | `overlay/glm_universal/data_objects/economics_register.py` |
| the vectors, the sweep, the control, the verdict | `overlay/glm_universal/reasoning/economics.py` |
| the machine-checked bucket and the scaling argument | `RequestProject/GLM/LogBucket.lean` |
| the report subject | `report economics` (`runtime/session.py`) |
| the column-3 template | `_body_report_economics` (`runtime/tct_engine.py`) |
| the tests | `overlay/glm_universal/tests/test_economics.py` |
| the catalogue entry it settles | §6.2, economic half (`reasoning/catalog.py`) |
