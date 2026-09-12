# The cross-register analogy: what makes `heat : temperature :: force : ?` answerable

## Tier 0 — the coarse read

**Question.** The analogy layer transports a relation within a register; `heat : temperature :: force : ?` asks it to transport one across registers, and the machine refused. Can the question be answered without inventing a relation?

**Verdict.** It can, by admitting the register the question was already about: an energy-conjugate table of 7 rows, each an effort, an extent and the transfer they make, checked against the physics register. `force` reaches `work`.

**Deciding figure.** All 7 rows pass the register check — effort and extent exponents and decimal scales sum to those of energy — and 11 of 11 transport cases behave as stated, 8 answered and 3 refused.

**Recomputed by.** `glm_universal.reasoning.conjugate.conjugate_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 1. The question, and why it was refused

`studies/ANALOGY_LAYER_STUDY.md` measures what the analogy layer does with a
relation it can name: it transports it. The failure it left open was of a
different kind, and it was written down as a shape rather than as a gap:

> `heat : temperature :: force : ?` — the analogy shape is described, but the
> semantic half is not: the lexicon has *temperature drives heat* and reaches
> nothing from `force`, so the question is refused with a stated reason.

Both halves of that sentence matter. The refusal was **correct**: the lexicon's
`drives` triple is a fact about two words, not a relation with a direction and
a type, and nothing in the register said what `force` would drive. A machine
that answered anyway would have been guessing. But a refusal that never becomes
answerable is a wall, and the reason the question felt answerable to a reader is
that it *is*: `heat = temperature × entropy` and `work = force × length` are the
same sentence in two domains, and the domain both sentences live in is a
register the machine did not have.

So the work is not to weaken the refusal. It is to see what admitting the
missing register buys, and which questions survive it.

## 2. The energy-conjugate register

`glm_universal/data_objects/conjugate_pairs.py` holds seven rows. Each row is
one energy domain and gives three names: the **effort** (the intensive variable,
the thing that is *at* a value), the **extent** (the extensive variable, the
thing there is an *amount* of), and the **transfer** their product makes.

| domain | effort | extent | transfer | definition |
| --- | --- | --- | --- | --- |
| thermal | `temperature` | `entropy` | `heat` | `heat = temperature × entropy` |
| mechanical | `force` | `length` | `work` | `work = force × length` |
| hydraulic | `pressure` | `volume` | `flow_work` | `flow_work = pressure × volume` |
| electrical | `voltage` | `charge` | `electrical_work` | `electrical_work = voltage × charge` |
| rotational | `torque` | `angle` | `rotational_work` | `rotational_work = torque × angle` |
| chemical | `chemical_potential` | `amount` | `chemical_work` | `chemical_work = chemical_potential × amount` |
| surface | `surface_tension` | `area` | `surface_work` | `surface_work = surface_tension × area` |

Twenty-one names over seven rows, and no name occupies two roles.

## 3. What makes a row admissible

A table of analogies is worth nothing if a row can be added because it reads
well. Every row is checked against a register the machine already has, in exact
integer arithmetic, by `conjugate_pairs.conjugate_audit`:

1. the effort and the extent are both **quantities the physics register holds**
   (`endpoints_in_register`);
2. their EXT10 exponents **sum to those of energy**, `L^2 M T^-2`, and their
   decimal scales sum to energy's scale (`all_dimensional`) — this is the check
   that fails for a row someone wanted to be true;
3. **no name occupies two roles** (`roles_unique`), which is what makes
   `role_of` a function and therefore what makes the transport single-valued.

All 7 rows pass all three. The audit reports `sound = True`, and it is run by
`tests/test_conjugate.py` rather than asserted here.

The second clause is the load-bearing one. It is not a coincidence that it
holds: it is the definition of a conjugate pair, and the point of checking it is
that the *register* is now the thing that decides membership. A row proposed for
`information : ?` or for `justice : ?` fails at clause 1 and never reaches the
table.

## 4. The relations, and the transport rule

Three relations run along the register, and each is a **bijection between two
columns** rather than a link:

* `effort_of` — between the effort column and the transfer column
  (`temperature` `effort_of` `heat`);
* `extent_of` — between the extent column and the transfer column
  (`entropy` `extent_of` `heat`);
* `conjugate_of` — between the effort column and the extent column
  (`temperature` `conjugate_of` `entropy`).

`A : B :: C : ?` is answered by reading the relation off `A : B`, checking that
`C` may occupy the role `A` occupies, and following the same relation from `C`.
An answer is produced only when four criteria hold, and each one refuses
something real:

| criterion | what it requires | what it rules out |
| --- | --- | --- |
| `determinate` | the relation names a step, not the bare existence of a link | `related_to`, which transports nothing |
| `role_typed` | the relation runs between two named columns, so which side a term may occupy is decidable | a term that occupies no column, and a term on the wrong side |
| `functional` | the relation is single-valued in the direction used | an answer chosen from several |
| `grounded` | the register can check its own rows | a row added because it sounded right |

This is the part the earlier round asked for: *closing it means supplying the
relation and saying what makes one admissible.* The four criteria are the
answer to the second half, and they are stated as data in
`conjugate.CRITERIA` so that a refusal can name the criterion it failed.

## 5. What the register answers, and what it still refuses

Eleven cases are run, and all eleven behave exactly as the module says they
should (`cases_as_expected = 11`). Eight are answered:

```
heat : temperature :: force : ?          -> work
temperature : heat :: voltage : ?        -> electrical_work
heat : temperature :: pressure : ?       -> flow_work
temperature : entropy :: force : ?       -> length
pressure : volume :: voltage : ?         -> charge
heat : entropy :: work : ?               -> length
entropy : heat :: area : ?               -> surface_work
work : force :: heat : ?                 -> temperature
```

Three are refused, and the refusals are the interesting half, because each names
the criterion it failed rather than declining in general:

* `heat : temperature :: entropy : ?` fails **`role_typed`**: `entropy` is in
  the extent column, and `effort_of` runs between the effort and transfer
  columns. The term is in the register and still may not go there.
* `heat : temperature :: justice : ?` fails **`role_typed`**: `justice`
  occupies no column at all, so the relation has no side to start from. This is
  the same refusal the semantics layer has always made, now made by a rule
  rather than by absence.
* `heat : temperature :: temperature : ?` fails **`functional`**:
  `temperature` is in the same thermal row as both `heat` and `temperature`, so
  transporting the relation would return the source rather than derive
  anything.

The standing example from the brief — `heat : temperature :: acceleration : ?`
— is refused for the first reason: `acceleration` is a quantity the physics
register holds and is in no row of the conjugate register, so the criterion it
fails is `role_typed`, and the refusal says so.

## 6. The negative result worth keeping

Two pairs have **both endpoints placed and are still not converted**:
`torque`/`force` and `pressure`/`force`. Both are efforts, in different rows.

The register relates a name to its **own row's** columns; it does not relate one
domain's effort to another's. It would have been easy to let it, and the result
would have been a machine that answered `torque : force :: ?` with something —
but there is no relation there, only a shared column heading. The two pairs are
reported by name in `conjugate.placed_in_different_rows` rather than being
silently dropped, so the boundary is visible in the measurement instead of
living in a docstring.

## 7. What it buys elsewhere

The register is not a private answer to one question. It is a fourth route in
the standing rule that decides a vague `related_to` triple
([`VAGUENESS_STUDY.md`](VAGUENESS_STUDY.md)): of the 66 vague triples the
lexicon holds, the conjugate register converts 4, and 1 of those is reached by
no other rule — `entropy`/`temperature`, which the physics register cannot
decide because it is a relation between an effort and its own extent rather
than a difference of dimension. Where both routes fire they agree, and the
conjugate reading is the sharper one: the dimensional rule says `heat` and
`temperature` differ by a factor, and the conjugate register names that
factor's role.

## 8. The formal side

[`RequestProject/GLM/Conjugate.lean`](../RequestProject/GLM/Conjugate.lean)
carries the part of the argument that is not a measurement:

* the register is sound — a row's effort and extent exponents sum to energy's,
  and this is what admits it;
* the roles are unique, so `role_of` is a function;
* each relation is functional and injective on the column it runs between;
* the answer in the `force` case is **unique** — not merely produced, but the
  only term that can be produced;
* and an unplaced term has no answer at all, which is the refusal as a theorem
  rather than as a branch of an implementation.

## 9. How to re-run it

```bash
cd overlay
PYTHONPATH=. python3 -c "from glm_universal.runtime.session import GeometricSession as S; print(S().ask('report conjugates').answer)"
PYTHONPATH=. python3 -m pytest glm_universal/tests/test_conjugate.py -q
cd .. && lake build RequestProject.GLM.Conjugate
```

## 10. Limits

Seven rows are not the energy domains; they are the seven this register holds,
and each was admitted by the check in §3 rather than by enumeration of physics.
Adding an eighth is a matter of passing the check, and a row that cannot pass it
does not belong here whatever its physical merit — magnetic work, for instance,
needs the register to hold both its columns as quantities first.

The transport is over one register. It does not make the analogy layer
cross-register in general; it makes *this* crossing checkable, and states the
four criteria a future crossing would have to meet.
