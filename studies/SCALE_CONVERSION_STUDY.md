# The scales neither operation could bridge — what a declared table of conversions buys, and what it must leave refused

## Tier 0 — the coarse read

**Question.** The ordering operation refuses two readings on two scales and the extremum operation refuses a column gathered from two, both because they hold no conversions. Declared, what does a table of conversions answer, and what must stay refused?

**Verdict.** It answers seven of the twelve questions declared before the run and refuses five, every one of the twelve as declared, and it removes nothing the two operations underneath it already did: both come out on their own declared sets exactly as before. A conversion is a row someone wrote down, so the table reaches nine scales of four quantities and leaves every other pair of scales refused.

**Deciding figure.** <!--figure:scales-as-declared-->12<!--/figure--> of <!--figure:scales-declared-->12<!--/figure--> declared questions came out as declared, <!--figure:scales-answered-->7<!--/figure--> answered and <!--figure:scales-refused-->5<!--/figure--> refused, off a table of <!--figure:scales-rows-->9<!--/figure--> rows that relates <!--figure:scales-bridged-->6<!--/figure--> of the <!--figure:scales-pairs-->7,750<!--/figure--> pairs of the <!--figure:scales-numeric-->125<!--/figure--> numeric scales the field surface holds.

**Recomputed by.** `glm_universal.reasoning.scale_conversion.conversion_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 1. What this round took, and from where

[`STATUS.md`](../STATUS.md) §3.4 carried this as candidate 1, the sharpest of
the list, and both studies it comes from state the boundary in the same words.
[`ORDERING_STUDY.md`](ORDERING_STUDY.md) §8:

> **`different-scale` is conservative by construction.** Two readings of the
> same quantity in two tables under two field names are refused even when a
> conversion between them exists, because the operation holds no conversions.
> What would relax it is a declared table of conversions between scales, and
> that is a round with its own pre-registration.

and [`COLUMN_EXTREMUM_STUDY.md`](COLUMN_EXTREMUM_STUDY.md) §7 the same thing
one level up: *a column is one table*, and gathering the same quantity from
two of them is refused for the reason two readings on two scales are.

What §3.4 asked for was named before the work started: a **declared** table of
conversions, *declared* so that a conversion is a fact someone wrote down
rather than a guess from a name; the measurement of how many of the refusals
it removes; and the proof that a conversion composed into the comparison
leaves `order_scale_invariant` intact. This study is those three things.

The shipped half is `glm_universal.reasoning.scale_conversion`, read through
the `ordering` and `extremum` query kinds, which is deliberate: the round adds
no query kind. The two operations refuse less, in exactly the places a row of
the table licenses. The proved half is
`RequestProject/GLM/ScaleConversion.lean`.

## 2. What a conversion is here

One row per scale. A row names the quantity the scale measures, the canonical
unit of that quantity, and the affine map that carries a reading on the scale
into that unit:

```
value  ->  factor * value + offset          with factor > 0
```

Three things about that shape are decisions, and each is checked.

**The factor is positive.** That is the whole of what makes a conversion a
conversion rather than a re-ordering: a negative factor turns *below* into
*above*, which `GLM.ScaleConversion.negative_factor_flips_the_verdict`
exhibits and a test pins on every declared row.

**An offset is admitted, and no declared row uses one.** A temperature scale
that does not start at absolute zero needs one; every scale here is a ratio
scale or is already in kelvin, so all nine offsets are `0`. That is reported
rather than hidden, because the mechanism being more general than the table is
the sort of thing that quietly becomes untrue.

**The table declares a unit, not a measurand.** `atomic_radius_pm` and
`covalent_radius_pm` are two different measurements and both are lengths in
picometres. The table says they are lengths in picometres and nothing more,
and an answer comparing them names both field names, so whether the comparison
is interesting is the reader's judgement rather than the operation's.

Comparisons are taken in the canonical unit, and that is sound because there
is no path to choose: `GLM.ScaleConversion.verdict_independent_of_target_scale`
shows that carrying both readings on into any further scale of the quantity
gives the same verdict.

## 3. The table

<!-- generated: scales-table -->
| scale | quantity | unit | factor | offset | declared from |
|---|---|---|---|---|---|
| `element:atomic_weight_u` | mass | `u` | `1` | `0` | the element register's own unit: the standard atomic weight is a mass in unified atomic mass units |
| `molecule:molar_mass_u` | mass | `u` | `1` | `0` | the molecule register's derived molar mass, summed from the same atomic weights and so in the same unit |
| `element:ionization_energy_eV` | molar energy | `kJ/mol` | `120606665154137523/1250000000000000` | `0` | one electronvolt per atom is N_A e joules per mole, exactly, from the 2019 SI definitions of the elementary charge and the Avogadro constant |
| `element:electron_affinity_eV` | molar energy | `kJ/mol` | `120606665154137523/1250000000000000` | `0` | the same conversion: an electron affinity in electronvolts is an energy per atom |
| `element:homonuclear_bde_kJ_per_mol` | molar energy | `kJ/mol` | `1` | `0` | the element register's bond dissociation energies are already per mole, in kilojoules |
| `element:melting_point_K` | temperature | `K` | `1` | `0` | the register holds thermodynamic temperatures in kelvin |
| `element:boiling_point_K` | temperature | `K` | `1` | `0` | the register holds thermodynamic temperatures in kelvin |
| `element:atomic_radius_pm` | length | `pm` | `1` | `0` | the register holds radii in picometres |
| `element:covalent_radius_pm` | length | `pm` | `1` | `0` | the register holds radii in picometres |

9 rows over 4 quantities, 2 of them with a factor other than 1 and 0 with an offset.  Of the 7,750 pairs of the 125 numeric scales the field surface holds, the table relates 6 and leaves 7,744 refused.
<!-- end generated -->

The one factor in the table that is not `1` is worth stating separately,
because it is exact rather than measured: one electronvolt per particle is
`N_A e` joules per mole, and both constants have been SI *definitions* since
2019 — the elementary charge `1.602176634e-19` coulombs and the Avogadro
constant `6.02214076e23` per mole. Their product is an exact rational, so the
conversion enters the system as a `Fraction` and nothing on the path rounds.

## 4. What the table lets the two operations do

**The ordering operation may now be asked about two coordinates.** The
question shape grows by one clause — the second side may name its own
coordinate — and the answer says which conversions it used:

```
order atomic_weight_u of carbon and molar_mass_u of water
  -> atomic_weight_u of C = 12011/1000 is below molar_mass_u of water
     = 3603/200, by an exact 1501/250, compared in u by the declared
     conversions element:atomic_weight_u x1 and molecule:molar_mass_u x1
```

**The extremum operation may now gather a column by quantity.** `largest mass`
is a column no table holds: 118 element rows under `atomic_weight_u` and 51
molecule rows under `molar_mass_u`, 169 readings in one unit, folded exactly.
The answer is `iron(III) sulfate` at `199939/500` u.

**And the refusals that remain are the same refusals.** Where no row of the
table licenses a comparison the operation refuses exactly as it did before.
`largest temperature`
gathers melting and boiling points and is refused as `incomplete`, because 40
of the 236 rows record no reading; `largest line` is still `mixed-scale`,
because neither `lean:line` nor `python:line` is declared; and
`atomic_weight_u` against `melting_point_K` is refused because the table
relates scales of one quantity and declares no conversion between two.

## 5. The declared set

Twelve questions were written down before they were run: six the declared
conversions must answer, spanning all four quantities and both directions of
the mass pair; three refusals the table must leave standing — an undeclared
scale, two quantities, and a coordinate that is a label rather than a
quantity; and three columns, one gathered by quantity and answered, one
gathered by quantity and refused for holes, one gathered from two undeclared
scales and refused. Each row states the outcome expected of it, and the
measurement is whether the outcome is that one.

<!-- generated: scales-declared -->
| question | asked as | declared | outcome | compared in | as declared |
|---|---|---|---|---|---|
| `mass-atom-molecule` | `atomic_weight_u` of `carbon` against `molar_mass_u` of `water` | `lt` | `lt` | `u` | yes |
| `mass-molecule-atom` | `molar_mass_u` of `glucose` against `atomic_weight_u` of `uranium` | `lt` | `lt` | `u` | yes |
| `energy-eV-kJ` | `ionization_energy_eV` of `hydrogen` against `homonuclear_bde_kJ_per_mol` of `hydrogen` | `gt` | `gt` | `kJ/mol` | yes |
| `energy-eV-eV` | `electron_affinity_eV` of `chlorine` against `ionization_energy_eV` of `sodium` | `lt` | `lt` | `kJ/mol` | yes |
| `temperature-melt-boil` | `melting_point_K` of `tungsten` against `boiling_point_K` of `mercury` | `gt` | `gt` | `K` | yes |
| `length-covalent-atomic` | `covalent_radius_pm` of `fluorine` against `atomic_radius_pm` of `cesium` | `lt` | `lt` | `pm` | yes |
| `undeclared-scale` | `line` of `GLM.NormFamily.family_tower` against `line` of `rung_audit` | `different-scale` | `different-scale` | -- | yes |
| `different-quantity` | `atomic_weight_u` of `carbon` against `melting_point_K` of `iron` | `different-scale` | `different-scale` | -- | yes |
| `still-nominal` | `kind` of `energy` against `kind` of `water` | `not-ordered` | `not-ordered` | -- | yes |
| `column-mass` | largest `mass` | `answer` | `answer` | `u` | yes |
| `column-temperature` | largest `temperature` | `incomplete` | `incomplete` | -- | yes |
| `column-line` | largest `line` | `mixed-scale` | `mixed-scale` | -- | yes |

the declared table is 9 rows over 4 quantities, 2 of them with a factor other than 1 and 0 with an offset. It answers 7 of the 12 declared questions and refuses 5, every one of them as declared before the run. Of the 7750 pairs of the 125 numeric scales the field surface holds it makes 6 comparable and leaves 7744 refused. The two operations it widens are unchanged on their own declared sets: 7 of 7 comparisons and 8 of 8 columns, exactly as before.

a conversion here is a declaration and not a derivation: the factor and the offset are written down with a source, and a scale the table does not mention is refused exactly as it was. The table declares a unit rather than a measurand, so a comparison across two measurements of one quantity -- an atomic radius against a covalent radius -- is answered with both field names named, and whether that comparison is interesting is the reader's judgement rather than the operation's. Nothing here parses English.
<!-- end generated -->

## 6. What it removes, measured rather than asserted

The honest denominator is the whole surface. The field surface holds
<!--figure:scales-numeric-->125<!--/figure--> numeric scales — every
`table:field` on which at least one row answers with a quantity — which is
<!--figure:scales-pairs-->7,750<!--/figure--> unordered pairs. The declared
table relates <!--figure:scales-bridged-->6<!--/figure--> of them and leaves
<!--figure:scales-still-refused-->7,744<!--/figure--> refused.

That ratio is the point rather than a disappointment. A conversion is admitted
one row at a time, with a source; nothing here infers a conversion from a
field name, and the six pairs it reaches are exactly the pairs somebody
declared. A table that reached more would be a table that had guessed.

The second measurement is the one that matters more, because it is a
conservativity claim rather than a coverage one: **nothing the two operations
underneath already answered has moved.** The ordering round's seven declared
comparisons and the extremum round's eight declared columns are re-run inside
this round's report, and both come out on their own declared sets exactly as
before. That is the shipped form of
`GLM.ScaleConversion.orderWith_conservative`.

## 7. What is proved rather than measured

`RequestProject/GLM/ScaleConversion.lean` states the conversion and the wider
operation over the same `Reading` and `Column` types the two earlier files use,
and proves:

* `cmpQ_apply` and `apply_lt_iff` — a positive-affine conversion composed into
  the comparison leaves the verdict exactly as it was. `apply_sub` says what
  does move: the gap is multiplied by the factor, so a reported difference is
  a difference in the target unit.
* `order_conversion_invariant` — the same statement at the ordering operation
  itself, which is `GLM.CoordinateOrder.order_scale_invariant` with an offset
  allowed. The side condition asked for in §3.4 is therefore intact: a
  conversion composed into the comparison does not disturb it.
* `orderWith_nil` and `orderWith_conservative` — with no conversions declared
  the wider operation *is* the operation it extends, and whatever the table
  says, every verdict the bare operation gave is given the same way. A
  declared conversion can only turn a refusal into an answer.
* `orderWith_eq_none_iff` and `orderWith_across_scales` — it is silent exactly
  when a reading is missing, or the scales differ and the table does not
  relate them under one quantity; and when it answers across two scales, the
  verdict is the comparison of the two converted values and nothing else.
* `verdict_independent_of_target_scale` — the verdict does not depend on which
  unit of the quantity it is taken in, which is why a table pointing at one
  canonical unit is enough to relate every scale of a quantity to every other.
* `negative_factor_flips_the_verdict` and `the_table_carries_the_claim` — the
  positivity is load-bearing, and so is the declaration: the same two readings
  order one way under one table and the other way under another, so the answer
  is only as good as the row someone wrote down.
* `extremum_convert_invariant`,
  `gathered_winner_is_a_row_of_one_of_the_two_columns` and
  `raw_gather_names_the_wrong_row` — at the column level, converting a column
  moves the value by the map and keeps the winning rows; two columns carried
  into one unit may be gathered and folded, and the winner is a row of one of
  them; and gathering the same two columns *without* the conversion names the
  wrong row.

## 8. What it decides, and what it does not

Under the standing target of [`PROJECT_DIRECTIVES.md`](../PROJECT_DIRECTIVES.md),
and as directive **D15** requires, this round moves one faculty and sharpens a
second:

* **Refusal**, on a declared task set. The interesting half is what the table
  does *not* do: five of the twelve declared questions are refusals, three of
  them refusals the table was specifically given the chance to remove and
  declined, because no row licenses them.
* **Derivation**, at the same weak end as the two rounds it widens: one exact
  multiplication and addition per reading, over readings that were already
  addressed. What is new is that a fold may now run over rows of two tables at
  once, which no register holds.

It decides nothing about **addressing**, and nothing here parses English: both
question shapes are still hand-translated into the system's own grammar.

## 9. Limits

* **Nine rows is a small table.** It covers the chemistry registers and
  nothing else; the Lean address book, the source walk, the harmonic register
  and the lexicon's primitives are all undeclared, and comparisons across them
  stay refused. Growing the table is data work, and each row needs a source.
* **No declared row uses an offset.** The affine shape is proved and
  exercised in Lean, but the shipped table exercises only the multiplicative
  half of it. A register holding a temperature in degrees Celsius would be the
  first real test of the other half.
* **A unit is not a measurand.** The table cannot say that comparing an atomic
  radius with a covalent radius is a strange thing to want; it can only say
  that both are lengths in picometres. Declaring measurands as well as units
  would be a second table, and a much harder one to write down honestly.
* **The census counts pairs, not questions.** 6 of 7,750 is the share of the
  surface the table reaches, not the share of the questions anyone asks; no
  claim is made here about what a user would want to compare.
* **Conversions do not compose across quantities.** There is no derived
  quantity algebra: the table cannot get from a mass and a volume to a
  density, and nothing here tries.

## 10. Re-running it

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.tools scales          # the measurement
python3 GLM.py -q "order atomic_weight_u of carbon and molar_mass_u of water"
python3 GLM.py -q "largest mass"
python3 GLM.py -q "largest temperature"
python3 GLM.py -q "largest line"
python3 -m pytest glm_universal/tests/test_scale_conversion.py -q
```

and, for the proved half, `lake build RequestProject.GLM.ScaleConversion` from
the repository root.
