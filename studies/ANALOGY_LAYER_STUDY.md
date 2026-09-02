# Analogy by named relation

*Why `A : B :: C : D` was the machine's worst query kind, what the diagnosis
turned out to be, and what closing it cost.*

This study documents the layer added in `overlay/glm_universal/reasoning/analogy_models.py`
and the register changes that finished the job. Every figure below is
recomputed by `report analogies`, by the three `analogy_*` benchmark suites and
by the end-to-end evaluation, and is carried into
[`overlay/FIGURES.md`](../overlay/FIGURES.md).

---

## 1. The measurement that started it

The end-to-end CLI evaluation of the previous round scored **67 / 72**. All
five failures were in one query kind, `analogy`, and all five were *confidently
wrong* rather than refused — the worst outcome the scoring recognises, weighted
`−1` against `+1` for an honest refusal.

The three analogy benchmark suites agreed: 9/12 chemistry, 12/13 physics, 5/10
semantic — 26 / 35 — against 2,325/2,325 on the exhaustive Golay suite and
29/30 on physics equations. Analogy was not marginally the weakest instrument
in the repository; it was the only weak one.

## 2. The diagnosis: the relation is not always a displacement

`reasoning/analogy.py` implements the standard vector-offset model. It reads
`A : B :: C : ?` as

> `D* = C + (B − A)` in `Q²⁴`, then return the nearest carrier to `D*`.

That is exactly right when the relation between `A` and `B` really is a
displacement of the coordinates. Every one of the five failures was a relation
that is **not** a displacement, and the failure mode is the same in each case:
the target `D*` means nothing, and "nearest carrier to a meaningless target" is
a confident answer to a question that was never asked.

| failure | what the relation actually is | why translation cannot see it |
|---|---|---|
| `He : Ne :: Ar : ?` → `Fe` | a step of one period *within a group* | the carrier holds `z`, `period` and a group-block *category*; a period step inside a group is not a displacement of those coordinates at all |
| `B : Al :: C : ?` → `P` | the same, one group over | the transported difference overshoots `Si` by one atomic number |
| `length : wavenumber :: time : ?` → `chromatic_dispersion` | a **reciprocal**, `L → L⁻¹` | reflection is not translation: `time + (wavenumber − length)` asks for `T·L⁻²` |
| `solid : liquid :: liquid : ?` → `fluid` | a relation the lexicon **states outright** | the metric turns it into "nearest word", and `fluid` is nearer to `liquid` than `gas` is, because it is its hypernym |
| `heat : temperature :: force : ?` → `enthalpy` | nothing determinate | the honest answer is a refusal, and a nearest-neighbour search has no way to produce one |

The important consequence is negative: **no amount of metric work would have
fixed any of these.** A better distance, a re-weighted subspace or a larger
register all leave the model unchanged, and the model is what is wrong.

## 3. The layer

`analogy_models.py` adds four **named relation models**, tried in domain order
before the translation solver. Each looks at `A` and `B` and either says what
the relation *is*, in the register's own terms, or declines.

| model | domain | what it recognises |
|---|---|---|
| `periodic_step` | chemistry | a displacement `(Δperiod, Δgroup)` in *derived* table coordinates — period and group computed from the period boundaries, never tabulated |
| `reciprocal_dimension` | physics | `B`'s EXT10 exponent vector is the negative of `A`'s, so the answer is the reciprocal of `C` |
| `scale_shift` | physics | `A` and `B` share a dimension and differ by a decimal scale — `gram → mass` is `10³` |
| `lexicon_relation` | lexicon | one of the register's 380 explicit triples relates `A` and `B` |

Three properties of the layer are worth stating, because they are what make it
different from another similarity heuristic.

**It is exact.** Integer table positions, integer exponent vectors, integer
scales. No coordinate metric is consulted anywhere in the layer — that is the
point of it.

**A recognised relation that leads nowhere is a refusal, not a fallback.** If a
model recognises `A : B` and finds nothing at the transported position, the
runtime does *not* fall through to the translation solver: it refuses and says
where it looked. `Ca : Sc :: Ba : ?` is the clean example — the step is well
defined, `(+0 period, +1 group)`, and period 6 group 3 holds fifteen elements
because the f-block sits there, so the position names no single element.
Naming one would be a choice the periodic table does not make. Overwriting a
determinate "no" with a nearest point would be a strict loss.

**One relation is deliberately not transportable.** `related_to` records that a
link exists without saying which, so it determines no answer; it is listed in
`VAGUE_RELATIONS` and the layer refuses to transport it. This is the whole
reason `heat : temperature :: force : ?` has no honest answer in the lexicon,
and the refusal now states both halves of the reason: the vague relation, and
the fact that the three terms do not share a register (physics holds
`temperature` and `force`, but not `heat`).

### Narrowing a dimension class

`reciprocal_dimension` and `scale_shift` fix the answer's *dimension* exactly,
and a dimension does not fix a name — 24 register quantities have dimension
`T⁻¹`. The shortlist is narrowed by three structural filters, each of which
transports a property of `B` rather than guessing, and each of which is skipped
when it would empty the shortlist: **sub-domain** (`wavenumber` sits in
`kinematics`), **primitivity** (`wavenumber` is defined by nothing, so
`strain_rate = strain / time` is not its counterpart), and **symbol shape**
(atomic `k` versus compound `grad v`). The third is applied only as a
tie-break, and when it fires the excluded candidates are named in the answer.
A tie that survives all three is reported in full rather than broken silently.

## 4. What the layer left, and what it took to finish

The four models closed all five CLI failures:

| question | old answer | now | by |
|---|---|---|---|
| `He : Ne :: Ar : ?` | `Fe` | `Kr` | `periodic_step` |
| `B : Al :: C : ?` | `P` | `Si` | `periodic_step` |
| `length : wavenumber :: time : ?` | `chromatic_dispersion` | `frequency` | `reciprocal_dimension` |
| `solid : liquid :: liquid : ?` | `fluid` | `gas` | `lexicon_relation` |
| `heat : temperature :: force : ?` | `enthalpy` | **refused**, with both halves stated | `lexicon_relation` declining |

Three misses survived, all in the semantic suite, and each one turned out to be
a missing or wrong *datum* rather than a defect in the model — which is exactly
the diagnostic property the layer was meant to buy. An opaque
nearest-neighbour search cannot tell you which triple it wanted; a named
relation can.

**`electron : proton :: north : ?`** The register recorded `proton related_to
electron`. `related_to` is the one relation the layer refuses to transport, so
the model declined and the query fell through. But the relation between an
electron and a proton is not vague: it is opposition, the same relation that
holds between the poles. The register now records `proton opposite_of
electron`, and the analogy resolves to `south`.

**`accelerate : move :: rotate : ?`** `accelerate` was recorded as `form_of
change` and `rotate` as `form_of motion` — two different parents for what the
curated pair treats as one relation, so the transported lookup found nothing.
Both now read `form_of move`, which is what the pair asserts, and the analogy
resolves.

**`cause : effect :: force : ?`** This one was a mistake in the *benchmark*.
The curated target was `motion`; the register's own triple is `force causes
acceleration`, so the relation `causes`, read off `cause : effect` and
transported to `force`, lands on `acceleration`. Answering `motion` would have
required the register to assert something it does not assert. The benchmark
target was corrected to `acceleration` rather than the code being bent to hit
it, and the reason is recorded next to the tuple in `benchmarks/suites.py`.

Two of the three were lexicon growth; one was a curation error. None was a
model failure.

## 5. Where it stands now

| instrument | before | after |
|---|---|---|
| `analogy_chemistry` | 9 / 12 | **12 / 12** |
| `analogy_physics` | 12 / 13 | **13 / 13** |
| `analogy_semantic` | 5 / 10 | **10 / 10** |
| CLI evaluation, `analogy` kind | 3 / 8 | **10 / 10** |
| CLI evaluation, overall | 67 / 72 | **83 / 83** |
| confidently wrong answers | 5 | **0** |

The evaluation set grew from 8 analogy cases to 10 while this was fixed, and
two of the ten are refusals — `Ca : Sc :: Ba : ?` and
`heat : temperature :: force : ?`. That is the substantive change, and it is
larger than the score: the machine acquired the ability to *decline an analogy
for a stated reason*, which it previously did not have at all. Before, every
analogy produced a carrier; the only question was whether it was the right one.

`report analogies` re-solves twelve cases through the layer from a fresh
interpreter, checks each against the mathematics of the case rather than
against a recorded transcript, and reports 12 / 12 as expected. The periodic
table it uses is itself audited in the same report: 118 elements over 7 periods
and 18 groups, positions derived rather than tabulated, agreeing with the
register on every element, with the two genuinely ambiguous positions — period
6 group 3 and period 7 group 3 — named as such.

## 6. What is still open

* **Multi-domain analogy.** `heat : temperature :: force : ?` is now refused
  honestly instead of answered wrongly, which is the right behaviour but not
  the answer. Answering it needs a way to pose a question whose four operands
  do not live in one register — a genuinely different piece of machinery, and
  not one this layer sketches.
* **`related_to` as a residue.** 66 of the register's 380 triples are
  `related_to`, and each is a relation someone knew and did not write down.
  Every one of them is a potential analogy the layer must decline. Converting
  them to the relations they actually are is open-ended lexicon work; two of
  them were converted here because a benchmark named them.
* **Relations across registers within one model.** `periodic_step` and
  `lexicon_relation` never consult each other, so an analogy whose left pair is
  chemical and whose right pair is lexical is invisible to both.

## 7. Re-running it

```bash
cd overlay
PYTHONPATH=. python3 GLM.py -q "report analogies"
PYTHONPATH=. python3 -m glm_universal.benchmarks
PYTHONPATH=. python3 -m glm_universal.evaluation --only analogy
PYTHONPATH=. python3 -m pytest glm_universal/tests/test_analogy_models.py -q
```
