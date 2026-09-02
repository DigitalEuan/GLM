# What the undimensioned names denote — the residue finished as a decision

*The lexicon's `related_to` triples were split by `reasoning/measure_view.py`
into 27 that the physics register converts and 39 that it declines. Thirty-eight
of those 39 declined for one reason — an endpoint reaches no dimension the
register holds — and that sentence reports a **lookup**, not a fact about the
word. This study closes the gap the sentence leaves open: each of the 36
undimensioned endpoints is decided by name, with its reason written down, and
the second pass then measures exactly what the decisions change.*

Registers:
[`overlay/glm_universal/data_objects/denotation.py`](../overlay/glm_universal/data_objects/denotation.py).
Reading:
[`overlay/glm_universal/reasoning/denotation_view.py`](../overlay/glm_universal/reasoning/denotation_view.py).
Query: `report denotations` (aliases `report denotation`, `report residue`,
`report related_to`, `report vocabulary`; the same subject as `report measure`,
whose §§10–12 are this study).
Formal development:
[`RequestProject/GLM/Denotation.lean`](../RequestProject/GLM/Denotation.lean).
Tests: `overlay/glm_universal/tests/test_denotation.py` (26 tests, 187
subtests).
Companion: [`RELATIVE_MEASURE_STUDY.md`](RELATIVE_MEASURE_STUDY.md), whose §4
is the split this study starts from.

---

## 1. The question

`relation_repair()` converts a `related_to` triple when the physics register can
decide it: `same_dimension_as` when both endpoints reach the same EXT10
exponent vector, `differs_by` when exactly one quantity of the factor basis
carries one vector to the other. **27 of the 66 convert**; **39 remain**, each
with a reason. The reasons partition:

| kind | count |
|---|---|
| `not_a_quantity` — an endpoint reaches no dimension the register holds | 38 |
| `no_single_factor` — both endpoints dimensioned, no basis quantity between them | 1 |

The single `no_single_factor` case (`entropy related_to temperature`) is a
statement about the world: the two dimensions differ by a heat capacity, which
is a quantity the basis deliberately does not carry, and a difference two basis
members could both explain is refused rather than guessed.

The other 38 are not. *"`motion` reaches no dimension the physics register
holds"* records that a lookup failed. It cannot distinguish

* a name the register merely **spells differently** — for which the honest
  action is to add an alias and convert the triple — from
* a name that denotes **no magnitude at all**, for which the honest action is to
  decline, permanently, and say why.

Until that difference is written down the residue is open in a way no amount of
searching would close, and the register cannot tell whether it is missing an
entry or has met a category boundary.

## 2. Why this is not a search problem

Before deciding words by hand it is worth knowing that the automatic half is
exhausted. `basis_sweep()` offers **every** quantity the physics register holds
and the factor basis does not — **713 candidates** — and measures what adding
each one would do:

| outcome | candidates |
|---|---|
| changes nothing | 571 |
| would make some attribution ambiguous, and is refused | 125 |
| strictly converts more | 17 |

The 17 that convert occupy **four dimensions**, two of which decide the same
triple, so the data decides **three** factors — the basis grew by `resistance`,
`entropy` and `angular_wavenumber` and stands at 16. Dimension is what the data
decides; the *name* inside a dimension class is not, and the sweep reports the
whole class beside each one (`impedance`, `reactance`, `von_klitzing_constant`,
… all sit in `resistance`'s class) so the spelling stays visible as a choice.

With the basis swept, the residue is what it is. Its 38 declines are a
vocabulary question, and the lexicon's own part of speech already says so:

| part of speech of the undimensioned endpoint | triples |
|---|---|
| verb | 11 |
| noun | 21 |
| absent from the lexicon | 6 |

No comparison class makes a verb a magnitude. That is a category boundary, not
a data gap — but a boundary is a claim, and a claim has to be stated.

## 3. The register of decisions

`data_objects/denotation.py` states it: **36 entries**, one per undimensioned
endpoint of the residue, each carrying a verdict and the reason the verdict was
reached. There are six verdicts and only the first makes a name dimensional.

| verdict | entries | what it says |
|---|---|---|
| `quantity` | 1 | the name denotes a quantity the register already holds, under an ordinary-language spelling |
| `ambiguous` | 3 | the name ranges over several quantities the register holds, and nothing in the word chooses |
| `polymorphic` | 4 | the name takes the dimension of whatever it is applied to |
| `carrier` | 9 | the name denotes a thing that *bears* quantities |
| `process` | 11 | the name denotes something that happens |
| `abstraction` | 8 | the name denotes no magnitude at all |

The one dimensional entry is **`gravity` → `gravitational_field`**: in ordinary
use *gravity* names the field a body falls in, 9.80665 m/s² at the Earth's
surface, which is the register's own entry in newtons per kilogram. The entry
supplies **no coordinate**. The ten EXT10 exponents continue to be read out of
the physics register, exactly as an alias does, so a denotation can no more
invent a quantity than an alias can. (The word's other use — the interaction,
*one of the four forces* — denotes no magnitude, and the decision recorded is
that a quantity register should follow the measurable use.)

The three `ambiguous` entries are the interesting refusals, because each names
what it is ambiguous *between*:

| name | candidates |
|---|---|
| `motion` | velocity, momentum, kinetic_energy |
| `space` | length, area, volume |
| `amplitude` | length, pressure, electric_field |

Newton's *quantity of motion* is momentum, a physicist's is kinetic energy, an
ordinary speaker's is velocity; they have three dimensions and the word chooses
none. An amplitude is the peak excursion of whatever is waving — metres for a
string, pascals for a sound wave, volts per metre for light. The decision **is**
the refusal: a machine that picked one would be guessing, and the candidates are
listed so that the guess it declines to make is visible.

The other three verdicts are the category boundary, split by *what kind* of
non-quantity the name is, because they are different reasons and a reader is
owed the difference: an electron, a photon, an ion, a magnet, a bond, a
boundary, an observer are **carriers** — they bear quantities and are none;
*move*, *rotate*, *react*, *measure*, *integrate* are **processes** — a rotation
is quantified by an angle and is not one; *electricity*, *cause*, *effect*,
*equilibrium*, *direction*, *north* are **abstractions** — a domain, a relation
between events, a condition, an orientation label.

### What the register is held to

`denotation_audit()` refuses to pass unless

* every verdict is one of the six;
* a `quantity` verdict names an entry the physics register holds, and no other
  verdict names one;
* an `ambiguous` verdict lists at least two candidates and every candidate is a
  quantity the register holds;
* no decided name is itself a registered quantity or an existing alias, so a
  denotation reaches the register and never shadows it;
* every entry carries a justification — an entry without one would be an
  assertion — and no two entries name the same word.

Measured: `sound: True`, with every list of offenders empty.

Coverage is checked from the other side, in `denotation_view.coverage()`: the
decided names must be **exactly** the residue's undimensioned endpoints.
Measured: **36 needed, 36 decided, 0 undecided, 0 idle**. The second half of
that is not decoration — an idle entry would be a judgement made about a
question the data never asked.

## 4. The second pass: what the decisions change

`denotation_view.second_pass()` re-runs the repair over the 39 residue triples
with the verdicts in hand. The two dimensional rules are applied unchanged, and
exactly one further rule is added — `names_process_of`, when one endpoint is a
`process` and the other reaches a dimension:

| outcome | triples |
|---|---|
| converted to a dimensional relation | **0** |
| repaired to `names_process_of` | 6 |
| declined, by a reason that now names what the endpoint *is* | 33 |

**Zero conversions is the result, not a disappointment.** One name became
dimensional — `gravity` — and its triple (`gravity related_to mass`) still
declines, now for the *other* reason: both endpoints are dimensioned and no
single basis factor carries a gravitational field to a mass. Deciding what words
denote is not a way of manufacturing relations, and the measurement says so.

The six repairs are `attract → force`, `rotate → angle`, `move → velocity`,
`change → time`, `predict → time` and `change ← time`: a process beside the
quantity that quantifies it.

The 33 declines are reported by the pair of verdicts that produced them —
`carrier+carrier` 3, `carrier+process` 3, `polymorphic` 4,
`polymorphic+process` 3, `ambiguous` 5, `abstraction` 4, and so on — so a reader
can see that *ion related_to electron* is two carriers and *large related_to
magnitude* is a degree word against the general term.

### What is deliberately not repaired

A `carrier` beside a dimensioned endpoint has the same shape as a `process`
beside one, and is **not** repaired. It would be wrong about half the time: a
magnet does bear a magnetic flux density, and a photon does not bear an
illuminance — the lexicon's `photon related_to light` is about what light is
made of, not about what a photon has. A rule that is right half the time is a
guess, and the register's whole discipline is that a guess is worse than a
refusal.

### The closure claim

This is what the study is for. `closure()` reports

| | measured |
|---|---|
| residue triples | 39 |
| accounted for | **39** |
| endpoints still undecided | **0** |
| triples declined for want of an entry | **0** |
| `decided` | **True** |

Every decline is now a decision. The residue is no longer a list of failed
lookups.

## 5. Do the conversions carry?

A converted relation is only worth having if the machine can use it. The
analogy layer never transports `related_to`, because the predicate is vague;
the repaired relations name their factor, so two pairs differing by *different*
quantities are not treated as the same step. `transport_audit()` measures it
over the analogies the 27 repaired triples license:

| | measured |
|---|---|
| repaired triples offered | 27 |
| distinct predicates | 16, of which 5 are transportable |
| analogy cases | 22 |
| answered | **12** |
| refused | 10 |
| answered with the repair suppressed (control) | **1** |

The control is the point: without the repair the analogy layer answers the one
analogy the lexicon could already state for itself. `temperature : heat :: hot :
?` is answered `heat` through `times_entropy` — the factor the sweep of §2 added
to the basis — and the ten refusals are the predicates that are not
transportable, refused rather than approximated.

## 6. What is proved

`RequestProject/GLM/Denotation.lean` (`sorry`-free, standard axioms only)
carries the part of the arrangement that is not a measurement: what a vocabulary
decision *can* and *cannot* do to a repair. A `Vocabulary` is the arrangement in
the abstract — what the register dimensions on its own (`base`), what has been
decided about the rest (`verdict`), what a quantity name's dimension is
(`dimOf`), and which basis quantities carry one dimension to another
(`factors`) — and `reach` is the lookup with the decisions in hand.

| Lean name | what it says | what it licenses here |
|---|---|---|
| `reach_invents_nothing` | a decided name reaches a dimension only by naming an entry `dimOf` already holds | §3: a denotation supplies no coordinate |
| `reach_eq_base_of_undenoted` | an undecided name reaches exactly what the register reached | the second pass extends the first |
| `secondPass_eq_firstPass_of_decided` | where the register could already decide a triple, the verdicts change nothing | §4: no decision *revises* a measurement |
| `secondPass_eq_firstPass_of_no_quantity_verdict` | with no `quantity` verdict, nothing new converts | §4: the measured `converted = 0` |
| `undecided_is_decided` | once every endpoint carries a verdict, an unclassified triple is one whose endpoint was decided not to be a quantity | §4: the closure claim |
| `repaired_not_converted` | the process rule applies only where the dimensional rules declined | §4: the three outcomes partition the residue |
| `gravity_reaches_the_register` / `gravity_mass_second_pass` | *gravity* reaches `gravitational_field`, and its triple still declines for want of a factor | §4: the one newly dimensioned name |
| `motion_is_decided_not_missing` | *motion* is left alone, and is left alone **by a decision** | §3: what `ambiguous` means |
| `move_velocity_repaired` / `move_velocity_not_converted` | a process beside a quantity is repaired, and the repair is not a conversion | §4: the one extra rule |

## 7. What this licenses, and what it does not

**It licenses** saying that the `related_to` residue is closed: not that every
triple converted — 0 of the 39 did — but that no triple is waiting on a lookup,
and every decline names what the endpoint is. It licenses treating the six
verdicts as a vocabulary the rest of the machine can read: a `process` beside a
quantity is repairable, a `carrier` beside one is not, and both facts are in the
data rather than in a comment.

**It does not license** calling the verdicts derived. They are judgements, made
one name at a time and written down with their reasons, and the audit checks
their *form* — that a `quantity` verdict names something held, that an
`ambiguous` one lists real candidates — never their content. Nothing here is
inferred from the shape of the relation graph: the graph asks the question, and
a person answers it. Nor does it license growing the register to make relations
appear. A conversion that exists because a quantity was added to produce it is
worth less than the residue it removed, which is exactly why the one addition
this round made — `gravity` — is reported beside a triple that still declines.

## 8. Reproducing every number here

```bash
cd overlay

# the whole thing, with the third column re-deriving it in a fresh interpreter
PYTHONPATH=. python3 GLM.py -q "report denotations" --no-banner
PYTHONPATH=. python3 GLM.py -q "report denotations" --verify-tct --no-banner

# the register, the coverage check, the second pass and the closure claim
PYTHONPATH=. python3 -c "from glm_universal.reasoning import denotation_view as d; \
    print(d.denotation_report()['closure'])"

# the sweep that says the search is exhausted, and the transport audit
PYTHONPATH=. python3 -c "from glm_universal.reasoning import measure_view as m; \
    print({k: v for k, v in m.basis_sweep().items() if isinstance(v, int)}); \
    print(m.transport_audit()['answered'], m.transport_audit()['control_answered'])"

# the tests
PYTHONPATH=. python3 -m pytest glm_universal/tests/test_denotation.py -q
```

The Lean side:

```bash
lake build
```
