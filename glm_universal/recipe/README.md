# `glm_universal/recipe` — the recipe made into an object

**Parent:** [`../README.md`](../README.md) · **Repository root:**
[`../../README.md`](../../README.md)

```
recipe/
├── spec.py          a DomainSpec — the declarative description of a domain —
│                    and the 25 shared primitives one is written in, with the
│                    domain-specific judgements marked apart so they can be
│                    counted rather than hidden
├── build.py         the one generic path: description → carriers, readings,
│                    widening audit, query surface, refusal boundary.  Knows
│                    nothing about any domain
├── descriptions.py  three domains built by hand in earlier rounds —
│                    comparison classes, harmonics, prices — written down as
│                    descriptions and nothing else
├── report.py        the measured result (`recipe_report`) and the query
│                    surface (`ask`)
└── __init__.py      public API exports
```

## The problem this package solves

Every register in the package was built the same way, by hand: carriers whose
coordinates are *derived* from something already held, a reading over them, an
audit of what the reading gains and gives up, a query that answers where the
registers decide and refuses where they do not, and a machine-checked statement
of the part that is not a measurement. Comparison classes, harmonics and prices
are that recipe applied three times, each application paying for its own
carrier method, codec, audit, report subject and parsing rule.

This package makes the recipe's *input* an object. A `DomainSpec` says what a
domain's objects are, which held quantity each coordinate derives from, which
coordinates recover the object, what a reading is, and what must be refused.
`build.py` turns any such description into the whole apparatus.

The test is subtractive, and it is run rather than asserted
(`build.regeneration`): the three hand-written registers are deleted and
rebuilt from their descriptions alone, and every figure measured off them has
to come back unchanged.

| what is compared | result |
|---|---|
| carriers, coordinate by coordinate, against the shipped registers | **94 / 94 identical** (comparison 45, harmonics 28, economics 21) |
| objects rebuilt through the read-back | all equal |
| figures the reasoning modules measure, with the regenerated register installed | **9 unchanged** — 11 with the two exhaustive ones |
| verdict | `regenerated`, 3 of 3 domains |

## Derivations and judgements

A coordinate is either a **derivation** — one of the 25 shared primitives,
which serve a frequency ratio, a quoted price and a comparison bracket alike —
or a **judgement** the domain has to state for itself. The distinction is
reported, not hidden:

| domain | objects | coordinates | derivations | judgements |
|---|---|---|---|---|
| comparison | 45 | 24 | 24 | 0 |
| harmonics | 28 | 24 | 18 | 6 |
| economics | 21 | 24 | 24 | 0 |

The six judgements are exactly the musical conventions — Euler's gradus, the
twelve-tone step and its error, the harmonic and subharmonic readings, and what
counts as a comma. A universal method should make such rules cheap to state and
impossible to state twice; it should not pretend to eliminate them.

Of the 25 primitives, 23 are used: `held` by all three domains, seven by two or
more, sixteen by exactly one, and `collection_size` and `minimum` by none —
reported as unused rather than deleted, since a vocabulary that exactly fits
three domains would prove nothing about a fourth.

## The chain, and what each widening gains

| domain | readings | classes | pairs gained | lossless |
|---|---|---|---|---|
| comparison | `bracket` (2) → `measured` (9) → `full` (24) | 42 → 43 → 45 | 1, then 2 | yes |
| harmonics | `ratio` (2) → `arithmetic` (14) → `full` (24) | 28 → 28 → 28 | 0, then 0 | yes |
| economics | `price` (2) → `magnitude` (7) → `full` (24) | 21 → 21 → 21 | 0, then 0 | yes |

Every chain is a refinement chain, and every register is recovered from its own
carriers with no two objects sharing one.

## Reachable as

```bash
cd overlay
PYTHONPATH=. python3 GLM.py -q "report recipe" --verify-tct
PYTHONPATH=. python3 GLM.py -q "derive span_ratio of tea"
PYTHONPATH=. python3 GLM.py -q "derive euler_gradus of perfect_fifth"
PYTHONPATH=. python3 GLM.py -q "derive cents of perfect_fifth"   # refused
```

A coordinate no description derives is refused with the reason, and an object
no register holds is refused with a different reason. Neither is a gap:
`GLM.Recipe.Spec.answer_eq_none_iff` says the answerable coordinates are
exactly the described ones.

## Where the rest of it is

* `RequestProject/GLM/Recipe.lean` — the part that is not a measurement:
  widening refines and is least, what a widening gains is the pairs it splits,
  keys give a lossless carrier, the refusal boundary is decidable, and two
  descriptions that agree on the coordinates agree on the carriers, the reading
  and every answer, which is regeneration stated formally.
* `../tests/test_recipe.py` — 87 tests over the descriptions, the primitives,
  the carrier, the widening, the refusal boundary, the query surface,
  regeneration, exactness and the runtime.
* [`../../../studies/RECIPE_STUDY.md`](../../../studies/RECIPE_STUDY.md) — the
  write-up, with every figure above and what the round does *not* do.
