# The recipe made into an object

*What `glm_universal/recipe/`, `RequestProject/GLM/Recipe.lean`,
`report recipe` and `derive <coordinate> of <object>` are for, and what they
measured.*

Every figure below is recomputed by the code that reports it. Run

```bash
cd overlay
PYTHONPATH=. python3 GLM.py -q "report recipe" --verify-tct
```

and the third column re-derives the whole study in a fresh interpreter and
checks it key by key (`VERIFIED True`).

---

## 1. The thing this round was trying to remove

Every capability in this package was built the same way, by hand, one round at
a time:

1. a **register** of carriers whose coordinates are *derived* from something
   already held;
2. a **reading** — a layer — over them;
3. an **audit** of what the reading gains and whether it gives anything up;
4. a **query kind** that answers where the registers decide and refuses where
   they do not;
5. a **machine-checked statement** of the part that is not a measurement.

Comparison classes, harmonics and prices are that recipe applied three times,
and each application cost its own carrier method, its own codec, its own layer
audit, its own report subject and its own parsing rule. The recipe was
therefore the most-used object in the project and the only one that had never
been written down.

This round writes it down. The input is a **domain description**; the output is
one generic path from a description to the carrier encoding, the readings, the
widening audit, the query surface and the refusal boundary. The test is not
that the path works on something new — it is **subtractive**: three domains
built by hand in earlier rounds are deleted and regenerated from their
descriptions alone, and every figure measured off them has to come back
unchanged.

## 2. What a description says

A `DomainSpec` (`recipe/spec.py`) is five things and no code:

| part | what it says |
|---|---|
| `facts()` | what the domain's objects *hold*, before any coordinate is derived |
| `coordinates` | one rule per coordinate, each derived from the held facts |
| `keys` | the coordinates from which the object is recovered |
| `readings` | the named selections of coordinates that make up the layer chain |
| `refuses` | coordinates that must be declined rather than guessed |

The descriptions themselves are in `recipe/descriptions.py`, and nothing else
is: no carrier is built there, no codec is written there, no audit is run
there. `recipe/build.py` does all of that generically, knowing nothing about
any domain.

A coordinate is written in **derivations**, and they compose — every primitive
takes either the name of a held fact or another derivation, so
`log_bucket(quotient("high", "low"), base=10)` is an ordinary coordinate rather
than a special case. Two kinds are distinguished, and the distinction is
*reported* rather than hidden:

* a **derivation** uses one of the 25 shared primitives — the same rule serving
  a frequency ratio, a quoted price and a comparison bracket;
* a **judgement** is a rule the domain has to state for itself, marked as such
  by `judgement(...)`, so that "this domain is described, not coded" is a
  measurement instead of a claim.

Every value a derivation produces is an `int` or a `Fraction`; nothing here
constructs a float, and the generated carriers go through the same
`exact_vector` guard the shipped registers do.

## 3. The three descriptions

| domain | objects | gloss | keys | readings (coordinates) |
|---|---|---|---|---|
| comparison | 45 | a comparison class as an exact bracket on one held quantity | `low`, `high`, `typical`, `quantity_index` | `bracket` (2) → `measured` (9) → `full` (24) |
| harmonics | 28 | an interval as an exact frequency ratio | `numerator`, `denominator`, `diatonic_degree` | `ratio` (2) → `arithmetic` (14) → `full` (24) |
| economics | 21 | a quoted price as an exact rational, in a stated window | 9 coordinates, from `numerator` to `quantity_index` | `price` (2) → `magnitude` (7) → `full` (24) |

Together: **3 descriptions, 94 objects, 72 coordinates** — 24 apiece, because
the substrate's dimension is fixed by the Leech lattice.

## 4. What generalised, and what did not

Of the 72 coordinates, **66 are shared primitives and 6 are judgements**, and
the judgements fall in one domain:

| domain | derivations | judgements |
|---|---|---|
| comparison | 24 | 0 |
| harmonics | 18 | 6 |
| economics | 24 | 0 |

The six are exactly the musical conventions, and each is stated in the
description rather than buried in a method:

| judgement | what has to be stated |
|---|---|
| `euler_gradus` | Euler's *gradus suavitatis* weights a prime by `p − 1` |
| `tet_step` | twelve-tone equal temperament is the tuning a step is measured against, decided by comparing `r²⁴` against powers of two |
| `tet_error` | the miss is `(n/d)¹² / 2^step` against that tuning |
| `harmonic_index` | a ratio with a power of two below is read as a harmonic of a fundamental |
| `subharmonic_index` | a ratio with a power of two above is read as a subharmonic |
| `is_comma` | an interval within a tempered semitone of the unison, and not the unison, is a comma |

That is the shape the plan predicted: what does not generalise is the
judgements, and the point of a description is to make them *countable* rather
than to pretend they are gone. Two registers built entirely out of held
quantities — the brackets and the prices — need none at all.

The shared vocabulary is measured the same way. Of the **25** primitives,
**23** are used; `held` is the only one every domain uses, 7 are used by two
domains or more (`borrowed`, `denominator`, `held`, `indicator_equals`,
`log_bucket`, `numerator`, `vocabulary_index`), and 16 by exactly one. The two
unused ones — `collection_size` and `minimum` — are reported as unused rather
than deleted, because a vocabulary that exactly fits the three domains
described so far would prove nothing about a fourth.

## 5. The path, run over each description

`recipe/build.py` takes a description and produces, in the order the recipe
used to be applied by hand:

1. **the carrier encoding** — `carrier`, `carriers`, `register`: one coordinate
   per description entry, each derived, all 24 required;
2. **the read-back** — `read_back_audit`: every object recovered from its own
   carrier, and no two objects sharing one;
3. **the readings** — `view`, `classes`: each declared reading as a `Layer` in
   the sense of `Layers.lean`;
4. **the widening audit** — `widening_audit`: for each step of the chain, does
   it refine the one below, what does it gain, and does the top tell every
   object apart;
5. **the query surface and its refusal boundary** — `answer`: the value of a
   coordinate the description derives, and `None` with a stated reason for one
   it does not.

Measured over the three descriptions:

| domain | chain a refinement chain | classes along the chain | pairs gained | read-back | distinct carriers |
|---|---|---|---|---|---|
| comparison | yes | 42 → 43 → 45 | 1, then 2 | 45 / 45 | 45 |
| harmonics | yes | 28 → 28 → 28 | 0, then 0 | 28 / 28 | 28 |
| economics | yes | 21 → 21 → 21 | 0, then 0 | 21 / 21 | 21 |

The comparison chain is the one that does work: reading the bracket alone
conflates `room_volume` with `household_lamp`, and the measured reading splits
them; two more pairs, `ship` against `ocean_depth` among them, are split only
by the full reading. The other two chains gain nothing because their narrowest
reading — the ratio, the price — already separates every object the register
holds, which is a fact about those registers rather than a defect of the path:
the audit reports it instead of asserting that a widening must gain something.

The refusal audit is the fifth step run as a check: each description names
three coordinates it must decline (`colour`, `loudness`, `prototypicality`;
`cents`, `beat_rate`, `timbre`; `volatility`, `bid_ask_spread`,
`market_capitalisation`), and for all three domains every named refusal is
refused and every described coordinate is answered.

## 6. Regeneration — the subtractive test

`build.regeneration` deletes the domain and rebuilds it from its description,
comparing three things of increasing strength:

* the **carriers** it generates against the carriers the hand-written module
  ships, coordinate by coordinate;
* the **objects** rebuilt through the read-back against the register's own;
* the **figures** the reasoning modules measure, recomputed with the
  regenerated register installed in the shipped one's place.

| domain | carriers identical | objects agree | figures re-measured |
|---|---|---|---|
| comparison | 45 / 45 | yes | register summary, lexicon agreement, transport audit, comparative audit (+ the widening audit, exhaustively) |
| harmonics | 28 / 28 | yes | register summary, temperament table, consonance orderings (+ the harmony report, exhaustively) |
| economics | 21 / 21 | yes | register summary, magnitude table |
| **total** | **94 / 94** | **yes** | **9 figures, all unchanged — 11 with the exhaustive two** |

The verdict is therefore `regenerated`, 3 of 3 domains, *because* each domain's
carriers, objects and measured figures came back identical from its description
alone. That is the test the plan set, and it is the reason the claim is
subtractive rather than additive: the hand-written carrier methods are now
re-derivable, not merely accompanied by a description of themselves.

## 7. The query surface, driven off the descriptions

`derive <coordinate> of <object>` is a query kind of its own, and it is
answered off whichever description derives the coordinate, so a fourth
description costs no new parsing rule:

| question | answer |
|---|---|
| `derive span_ratio of tea` | `373/293`, by `quotient(high / low)`, from the comparison description |
| `derive numerator of perfect_fifth` | `3`, from the harmonic description — a second domain, same surface |
| `derive euler_gradus of perfect_fifth` | `4`, and reported as a **judgement**, not as a derivation |
| `derive cents of perfect_fifth` | **refused**: no description derives `cents`; the described domains are comparison, harmonics, economics |
| `derive span_ratio of cup_of_coffee` | **refused**: the comparison description derives `span_ratio`, but no register holds that object |

The two refusals are different refusals, and the reason says which. Neither is
a gap: a cent is a logarithm, so no description derives it, and
`GLM.Recipe.Spec.answer_eq_none_iff` says the answerable coordinates are
exactly the described ones.

## 8. The part that is not a measurement

`RequestProject/GLM/Recipe.lean` states the path itself. A `Spec Obj Val` is
the description in the abstract — `coords`, `derive`, `keys` — and everything
the recipe produced by hand is a function of it:

* `Spec.readingOn` generates the reading of a selection of coordinates as a
  `Layer`, so the whole widening machinery of `Layers.lean` and
  `Cumulative.lean` applies without knowing what the domain is about;
* `readingOn_mono` — widening a selection never gives anything up — and
  `readingOn_append_least`, that the widened reading is exactly the cumulative
  layer of its parts, so it adds nothing beyond keeping both;
* `boundary_readingOn_nonempty_iff` — what a widening *gains* is exactly a pair
  the narrower selection conflates and a new coordinate splits, which is the
  "pairs gained" column of §5 as a theorem;
* `lossless_readingOn_iff`, `lossless_full_of_keys`, `encode_injective_of_keys`
  and `rebuild_encode` — a description whose keys determine the object gives a
  lossless encoding with an exact inverse, which is the hypothesis the
  read-back audit checks on each register;
* `answer`, `answer_eq_some_iff`, `answer_eq_none_iff` — the query surface and
  its refusal boundary, both read off the description and decidable;
* `encode_congr`, `indist_congr`, `answer_congr` — **regeneration** stated
  formally: two descriptions agreeing on the coordinates agree on the carriers,
  on the reading (hence on its classes, hence on any figure counted off them)
  and on every answer, refusals included.

`ratioSpec` instantiates all of it on one real description — an interval as an
exact ratio, keys `numerator` and `denominator`. `ratioSpec_full_lossless` is
the read-back; `ratioSpec_product_not_lossless` shows the derived Tenney height
alone is *not* a reading of the domain, since it conflates `3/2` with `6/1`;
`ratioSpec_boundary_full_keys_empty` and
`ratioSpec_boundary_full_product_nonempty` are the two boundaries, empty where
the keys already decide and non-empty where they do not; and
`ratioSpec_refuses_cents` is the refusal the CLI makes, proved.

## 9. What it does not do

* **Three domains are described, not eight.** The physics, chemistry, molecule,
  mathematics and lexicon registers are still hand-written. Nothing measured
  here says they *can* be described — only that three that were built by hand
  can be deleted and regenerated.
* **The judgements are counted, not removed**, and they should not be: which
  tuning a step is measured against is a decision, and a method that hid it
  would be worse than one that prints it.
* **The surface language is still a keyword.** `derive <coordinate> of
  <object>` is generic in the coordinate and the object but is itself a
  hand-written phrase; a genuinely open vocabulary needs the query layer driven
  off the same descriptions.
* **A description is trusted about its own facts.** `facts()` reads the shipped
  register, so the round proves the *coordinates* are re-derivable, not the
  underlying data.

## 10. Where the code is

| piece | file |
|---|---|
| the description, and the 25 primitives | `overlay/glm_universal/recipe/spec.py` |
| the one generic path | `overlay/glm_universal/recipe/build.py` |
| the three descriptions | `overlay/glm_universal/recipe/descriptions.py` |
| the measured result, and `ask` | `overlay/glm_universal/recipe/report.py` |
| the report subject | `report recipe` (`runtime/session.py`, column 3 in `runtime/tct_engine.py`) |
| the query kind | `derive <coordinate> of <object>` (`runtime/parser.py`) |
| the machine-checked half | `RequestProject/GLM/Recipe.lean` |
| the tests | `overlay/glm_universal/tests/test_recipe.py` (87 tests) |
| the CLI cases | `report-recipe`, `derive-span-ratio-tea`, `derive-numerator-perfect-fifth`, `derive-euler-gradus`, `derive-undescribed-coordinate` |
