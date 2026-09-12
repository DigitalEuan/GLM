# Open vocabulary: the door a new name comes in by

## Tier 0 — the coarse read

**Question.** "Open vocabulary" has stood for several rounds as a commitment rather than a mechanism: the machine refuses to invent a coordinate for `justice`. What is missing is the other half — how does a name get *in*?

**Verdict.** A name is admissible exactly when a stated route gives it coordinates computed from a register the machine already checks: stated, reproducible, grounded.

**Deciding figure.** Over 27 probes the door admits 20 and refuses 7, writing nothing back into a held vocabulary of 1093 names.

**Recomputed by.** `glm_universal.reasoning.admission.admission_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 1. A commitment is not a mechanism

The untouched list carried this item for a long time, with a note beside it
saying it was *a commitment, not an oversight*: the vocabulary is exactly the
registers, there is no coordinate for `justice`, and the semantics layer refuses
rather than inventing one.

That is the right commitment, and the note was doing something slightly
dishonest by standing alone. A commitment says what the machine will **not** do.
Two things were never stated:

1. **What makes a name admissible** — as a criterion someone could check, not a
   judgement someone makes. Names *did* get in; the vocabulary grew across
   rounds; nobody had written down the rule by which.
2. **What a refusal is a refusal of** — whether `justice` is outside the
   vocabulary permanently, or merely until something specific is supplied.

Without the first, "open" was an adjective. Without the second, the refusal was
indistinguishable from a claim about what kinds of things can be measured, which
is a much larger claim than this project makes.

## 2. The criterion

> A name is admissible exactly when some **stated** route gives it coordinates
> that are **reproducibly computed** from a register the machine already
> checks, and are therefore **grounded** in a register rather than invented for
> the name.

The three clauses are separable, and each rules something out.

* **stated** — the route is one of the four in `admission.ROUTES`, written down
  in the module. A name admitted "because it obviously belongs" is not
  admitted.
* **reproducible** — the coordinates are recomputed from the registers on
  demand. Nothing is typed in at admission time, so admission survives being
  re-run, and the audit checks that asking twice gives the same answer.
* **grounded** — the coordinates come *out of* a register rather than being
  made for the name. This is the clause that does the refusing, and it is the
  same discipline `element_coverage` follows when it widens the element
  register by derivation and writes nothing back
  ([`ELEMENT_COMPLETION_STUDY.md`](ELEMENT_COMPLETION_STUDY.md)).

## 3. The four routes

Three admit; the fourth refuses. They are tried in order.

| route | admits | how it grounds the coordinates |
| --- | --- | --- |
| `held` | the name is already a carrier in one of the nine registers | the register's own |
| `unit` | the name parses as a unit expression — `J`, `kg*m/s^2`, `mol/L` | the unit register, ten exact EXT10 exponents |
| `arithmetic` | the name is an expression over register names — `energy divided by time` | term arithmetic, evaluated exactly |
| `refused` | nothing reached it | there are none, and that is the point |

The order matters and is checked: `energy` is held, so it is admitted by the
first route even though the third would also reach it. The Lean file states the
priority as part of each route's characterisation rather than leaving it to the
order of the branches.

The `arithmetic` route is what makes the vocabulary genuinely open rather than
merely large. The registers hold 1093 names, of which 726 are physics
quantities, and the expressions over them do not run out.

## 4. What the door was measured on

Twenty-seven probes, of which 20 are admitted and 7 refused: carriers drawn from every register, a spread of unit
expressions, a spread of arithmetic over register names, and the six standing
ungrounded words (`justice`, `beauty`, `irony`, `nostalgia`, `fairness`,
`dignity`).

| route | probes |
| --- | --- |
| `held` | 11 |
| `unit` | 5 |
| `arithmetic` | 4 |
| `refused` | 7 |

Four things are checked, each of which could have gone wrong:

* **totality** — every probe gets exactly one route, so a refusal is a decision;
* **grounding** — no refused name is given coordinates, and both computing
  routes always produce them;
* **determinacy** — asking twice gives the same route and the same coordinates;
* **the register is unchanged** — the 9 names admitted by computation are still
  not carriers afterwards.

All four hold. The coordinates are also checked against the register they claim
to come from rather than merely being present: `J` admitted by the unit route
carries the same ten exponents as `energy` in the physics register, and
`energy divided by time` carries `power`'s.

## 5. What the vocabulary actually is

`admission.vocabulary()` enumerates it rather than describing it: 1093 names,
each mapped to the register it lives in, in a fixed register order so that a
name held twice is reported consistently.

| register | names |
| --- | --- |
| physics | 726 |
| chemistry | 118 |
| semantic lexicon | 68 |
| molecules | 51 |
| comparison classes | 45 |
| harmonics | 28 |
| mathematics | 22 |
| economics | 21 |
| lexicon | 9 |
| conjugate pairs | 5 |

## 6. Two shapes of refusal, and the honest boundary the door turned up

Seven probes are refused, and they are not all refused for the same reason.

**Six are ungrounded.** No register reaches `justice`. The refusal is
**conditional and names its condition**: `justice` is admitted by the first
route the moment a register that measures it is admitted, and the door needs no
change for that to happen. So the claim being made is "no register reaches it",
never "it is not the kind of thing that has coordinates" — and the difference is
the whole reason for writing the door down.

**One is a gap in a register rather than in the door.** `km/h` is refused
because the unit register is SI-coherent and does not hold the hour. The refusal
says *which symbol is missing*, which is something a reader can act on, and the
same expression over a symbol the register does hold — `km/s` — is admitted
immediately. This was not designed in; it fell out of running the door over the
probes, and it is kept because a boundary discovered by measurement is worth
more than one asserted in a docstring.

The near miss is claimed narrowly: only for a compound expression in which at
least one symbol parses on its own. Without that clause every unknown word would
be reported as a missing unit symbol, and `justice` would come back as a
malformed unit — which would be noise dressed up as a finding.

## 7. The formal side

[`RequestProject/GLM/Admission.lean`](../RequestProject/GLM/Admission.lean)
models the door as three partial functions from a name to something a register
computed. There is deliberately no fourth field: the door **cannot make** a
coordinate, only pass one on, which is the `grounded` clause expressed as a
type.

* `route_mem`, `route_unique` — the door is total and single-valued, so a
  refusal is a decision rather than a crash;
* `route_eq_unit_iff`, `route_eq_arithmetic_iff` — the order is real: a name a
  register holds is never taken by a computing route;
* `no_coordinates_of_refused`, `coordinates_grounded` — every coordinate handed
  back is some register's own value at that name, and a refused name gets none;
* `held_unchanged_of_computed` — admitting a name by computation writes nothing
  back;
* `refusal_is_conditional` — a register that holds a refused name admits it by
  the first route, and **every other name is routed exactly as before**, so
  meeting the condition costs nothing elsewhere;
* `refused_mono`, `admissible_mono` — widening a register can only take names
  off the refused list, never add one.

## 8. How to re-run it

```bash
cd overlay
PYTHONPATH=. python3 -c "from glm_universal.runtime.session import GeometricSession as S; print(S().ask('report admission').answer)"
PYTHONPATH=. python3 -m pytest glm_universal/tests/test_admission.py -q
cd .. && lake build RequestProject.GLM.Admission
```

## 9. Limits

Two of the three admitting routes compute a **dimension**. A name that is not a
quantity can only get in by already being held, so the door widens the
vocabulary of *measurable* names and says so rather than pretending to more.
Admitting `justice` still requires someone to build a register that measures
something and to defend it; what the door supplies is that the requirement is
now a stated one, and that the machinery on this side of it will not need to
change.

The probe set is a sample, not a census: 27 names chosen to exercise each route
and each failure mode. The properties it checks — totality, grounding,
determinacy, and that nothing is written back — are proved for all names in the
Lean file and measured on the 27 here.
