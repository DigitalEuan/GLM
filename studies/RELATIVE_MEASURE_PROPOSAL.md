# Measure words as relative measures — what is already here, and what is missing

*Scope note.* This is a **proposal**, not a result. Everything in §1 is
measured from the code as it stands today; everything in §2 onwards is a design
argument and is marked as such. Nothing in this document is implemented yet,
and no count here should be quoted as a capability.

The question it answers: *can a meaning-measure like `hot` stop being a static
concept and become a relative measure label — a family of words that measure in
different ways — is the project set up to test that now, and will it translate
to other domains?*

---

## 1. What is already here (measured)

| piece | where | what it currently does |
|---|---|---|
| semantic primitives | `data_objects/semantic_lexicon.py` | 10 named primitives, each an exact `Fraction` in `[0, 1]` on a 1/8 grid, occupying coordinates 0–9 of a concept's carrier |
| relations | same | at most **4** per concept (`MAX_SEMANTIC_RELATIONS`, coordinates 12–19), drawn from an open vocabulary of predicate names |
| the lexicon register | same | **95** concepts carrying **380** relation triples |
| the physics register | `data_objects/physics.py` | **726** quantities, each with EXT10 exponents and a unit string, cross-checked against each other |
| analogy by named relation | `reasoning/analogy.py`, `reasoning/analogy_models.py` | transports a *named* relation rather than a coordinate similarity; includes `scale_shift`, which already transports a pure **decimal-scale offset** between two quantities of the same dimension |
| the layer stack | `reasoning/dimension_layers.py` | five layers, now a genuine refinement chain (`refinement_chain_intact = True`) — see [`INFORMATION_LOSS_STUDY.md`](INFORMATION_LOSS_STUDY.md) |

The relation vocabulary in use, counted from the register today, is led by
`form_of` (77), `related_to` (66), `has_property` (32), `opposite_of` (30),
`measured_in` (27), `property_of` (24) and `is_a` (19).

`hot` today is a `SemanticConcept` with primitives
`positive_negative = 1`, `causal_passive = 3/4`, `temporal_stable = 1/8`
(and seven others), and the four relations

```
property_of temperature      opposite_of cold
related_to  heat             form_of     property
```

`cold` is the same concept with `positive_negative = 0` and
`active_stative = 0`.

**So a small amount of "relative" information is already encoded, and a large
amount is not.** What *is* there: a polarity (`positive_negative`), the
quantity the word is a property of (`property_of temperature`), the opposite
pole (`opposite_of cold`), and — through `temperature` in the physics register
— a dimension and a unit. What is **not** there:

1. **A position on the scale.** `hot` and `warm` would receive the same
   `positive_negative = 1`; nothing orders them.
2. **A comparison class.** *Hot* for a cup of tea, for a summer day and for a
   star are three different thresholds. There is no slot for the class.
3. **A comparative form.** There is no `hotter_than`, no `as_hot_as`, and no
   way to ask one.
4. **A way for the answer to be a measurement rather than a word.** The machine
   can say *`hot : temperature :: fast : velocity`*; it cannot say *how hot*.

`STATUS.md` §3.2 already records this honestly, as "**Words as projections** —
`hot` is a standalone concept, not 'temperature at high scale'".

**Is there a test that would catch a wrong answer here?** No — because there is
no query that asks one. The nearest tests (`test_semantic_lexicon.py`,
`test_lexicon_subspaces.py`, `test_analogy_models.py`) pin the concept vectors,
the subspaces and the named-relation transport. None of them would fail if the
machine had a wrong opinion about whether 300 K is hot, because it has no
opinion at all.

---

## 2. The shape the fix should take (proposal)

The decision just taken for the layer chain is the right template, and it is
worth reusing deliberately. When the substrate → integer step turned out not to
be a refinement, the two options were to **widen** the layer above or **narrow**
the layer below, and the project committed to widening: nothing a lower view
could say is given up. The same discipline applies here.

> **Add the relative reading as a widening of the concept view, never as a
> replacement for the static one.**

Concretely: a measure word keeps everything it carries today, and gains a
*measure view* beside it. Then the static reading remains exactly as
expressive as it is now, the relative reading is a strict gain, and the audit
in `information_loss.py` can be pointed at the new view and asked the same
question it now answers for the layer stack — does the widened view refine the
narrow one? — with a real answer rather than a hand-wave.

### 2.1 What a measure view would have to carry

Four fields, all exact, all derivable rather than typed twice:

| field | example for `hot` | derived from |
|---|---|---|
| the quantity | `temperature` | the existing `property_of` relation |
| the dimension | SI7 exponents of `temperature` | the physics register — **no new data** |
| the comparison class | `tea`, `weather`, `stellar_surface` | new: a small register of classes, each with a typical magnitude |
| the position | a `Fraction` in `[0, 1]` on the class's scale, or a comparative relation to another word on the same scale | new |

Only the last two are new information. The first two are already in the
machine and are being re-derived rather than re-entered — which is the
project's existing rule for the molecules register (every coordinate derived
from the element register at load time).

### 2.2 The relation family

Rather than one relation, a *family* that says how a word measures:

```
measures            hot   -> temperature        (which quantity)
measures_relative_to hot  -> tea                (which comparison class)
above_on             hot  -> warm               (ordering within a class)
opposite_pole        hot  -> cold               (already have this as opposite_of)
```

`above_on` is the load-bearing one: it makes *warm < hot < scalding* a chain
inside a class, and a chain is exactly what the analogy layer already knows how
to transport. `related_to` — 66 of the 380 triples, and the residue the
analogy layer deliberately refuses — is where several of these should have
been all along; converting some of those 66 is a cheap first win and is already
on the open list in `STATUS.md` §3.3.

Note the hard constraint: `MAX_SEMANTIC_RELATIONS` is **4**, and `hot` already
uses all four. A measure family therefore cannot be bolted onto the existing
relation slots; it needs its own view, which is the widening argued for above.
That is a real design consequence, not a detail.

---

## 3. Will it translate to other domains?

**Yes, exactly where the domain supplies two things, and honestly no elsewhere.**
The two things are:

1. a quantity with a dimension the physics register already holds, and
2. a comparison class with a typical magnitude.

On that test:

| domain | quantity | translates? |
|---|---|---|
| temperature (`hot`, `warm`, `cold`) | in the register | yes |
| size (`large`, `small`) | in the register | yes |
| speed (`fast`, `slow`) | in the register | yes |
| mass (`heavy`, `light`) | in the register | yes |
| loudness, brightness | acoustics and photometry are in the register | yes |
| musical intervals (`consonant`, `sharp`) | the harmonics register holds exact ratios | yes, and the class is the tuning system |
| chemistry (`reactive`, `stable`) | element register, sparse (1,257 of 1,652 cells filled) | partly — the class exists, the magnitudes are incomplete |
| prices (`expensive`) | **no economic register exists** | no, and this is already recorded as the untestable third of the catalogue's universality claim |
| ethics (`just`) | no coordinate, by commitment | no — and the machine should keep refusing rather than inventing one |

That table is the honest scope. The mechanism is domain-general; the *data* is
not, and the project's existing rule — refuse rather than invent a coordinate —
should not be relaxed to make the mechanism look more general than it is.

---

## 4. Growing the registers, and what that does to escalation

This is the part the layer work just made cheap, and it is worth stating
precisely because it is a real consequence of what was proved rather than a
hope.

* `information_loss_report(carriers)` **already takes the carrier set as an
  argument**. The seven-carrier set it defaults to is a fixture, not a
  limitation. Pointing it at a carrier set drawn from the registers is a data
  change, not a code change.
* The Lean statement of the chain is **universally quantified over carriers**:
  `GLM.Info.glmChain_refines_of_le` is a statement about the layers, not about
  any particular seven points, so it continues to hold however the carrier set
  grows. Growing the registers cannot break the chain; it can only reveal more
  of what each boundary costs.
* What *will* move as the registers grow are the measured numbers — resolution,
  loss count, and which pairs each boundary gains. Those are exactly the
  figures `report information loss` recomputes, so growth is self-documenting.

The suggested order of work, cheapest first:

1. **Make the carrier set for the audit generated rather than hand-picked.**
   Draw it from the registers (say, one carrier per physics quantity) and
   re-run `report information loss`. This measures escalation at scale for the
   first time and costs no new theory. It is the single highest-value next step
   and it is independent of everything else here.
2. **Convert a slice of the 66 `related_to` triples** into the relations they
   actually are, prioritising the ones between a measure word and its quantity.
   Measurable, incremental, already on the open list.
3. **Add the comparison-class register** — small, a few dozen classes, each
   with a typical magnitude and a dimension taken from the physics register.
4. **Add the measure view as a widening**, with `above_on` ordering words inside
   a class, and prove it refines the static view with the same machinery the
   layer chain now uses (`GLM.Layer.cumulative` and its four lemmas in
   `RequestProject/GLM/Cumulative.lean`).
5. **Only then** add a query, and pin it with tests that can fail — including
   at least one question the machine should *refuse* (a measure word in a
   domain with no register), because a refusal that is never exercised is not a
   tested refusal.

Step 1 is worth doing before any of the rest: it answers "how does escalation
work out as the databases grow" using only what is already proved and already
wired, and its result should inform whether steps 3–5 are shaped the way this
document guesses.

---

## 5. Where to look

| file | what it holds |
|---|---|
| `overlay/glm_universal/data_objects/semantic_lexicon.py` | the 10 primitives, the 4-relation cap, the 95 concepts |
| `overlay/glm_universal/data_objects/physics.py` | the 726 quantities the dimensions would come from |
| `overlay/glm_universal/reasoning/analogy_models.py` | named-relation transport, and `scale_shift` as the existing precedent for a relative reading |
| `overlay/glm_universal/reasoning/information_loss.py` | the audit, already parameterised by the carrier set |
| [`INFORMATION_LOSS_STUDY.md`](INFORMATION_LOSS_STUDY.md) §3.1 | the widen-rather-than-narrow decision this proposal reuses |
| `RequestProject/GLM/Cumulative.lean`, `RequestProject/GLM/LayerChain.lean` | the machinery a widened view would be proved correct with |
