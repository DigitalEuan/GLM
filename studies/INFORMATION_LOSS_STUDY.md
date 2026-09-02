# Information loss at boundaries

A study of the thesis that a system is true up to a point, and that past that
point a different system takes over and is true in its own right, with the
former statement now false but built upon.

Two artifacts back this document:

* **`RequestProject/GLM/`** — a Lean 4 development in which every claim below
  marked *(proved)* is a machine-checked theorem, compiled with no `sorry` and
  depending only on Lean's standard axioms.
* **`overlay/glm_universal/reasoning/information_loss.py`** — the
  same definitions, executed on the GLM's real carriers, so the numbers are
  measured rather than asserted. It is reachable from the runtime as
  `report information loss` and is covered by
  `glm_universal/tests/test_information_loss.py`.

---

## 1. The thesis, stated precisely

The informal claim has three parts:

1. a layer is *true from its limited perspective*;
2. it *becomes untrue* when the next layer is required;
3. the next layer *builds on* it, and this continues upward.

Taken literally, part 2 is a contradiction: a proposition does not change truth
value. The study's first job is to find the reading on which all three parts
are simultaneously correct. That reading is:

> A layer is a **resolution**. What is true at a layer is not a proposition
> about carriers but a proposition about *views*. When the resolution changes,
> the propositions change with it — and a proposition that was well posed below
> may cease to be well posed above, or vice versa.

Formally (`RequestProject/GLM/Layers.lean`):

```lean
structure Layer (C : Type u) where
  View    : Type v
  perceive : C → View
```

Everything else is derived from `perceive`:

| Notion | Definition | Reading |
|---|---|---|
| `Indist L a b` | `L.perceive a = L.perceive b` | the layer's own verdict that two carriers are the same thing |
| `Refines L' L` | `∀ a b, L'.Indist a b → L.Indist a b` | `L'` distinguishes at least as much as `L` |
| `Visible L P` | `∀ a b, L.Indist a b → (P a ↔ P b)` | `P` is a proposition the layer can even state |
| `Boundary L' L` | `{(a,b) | L.Indist a b ∧ ¬ L'.Indist a b}` | what the lower layer loses |
| `CongruentOn L S op` | replacing operands by indistinguishables does not change the view of the result | the reach of a law |
| `capacity L` | `Fintype.card L.View` | how much the layer can hold at all |

With this, the three parts of the thesis become three theorems.

### Part 1 — a layer is genuinely true within its reach *(proved)*

`Layer.CongruentOn.mono`: if an operation is computable at a layer's resolution
on a region `T`, it is computable on every subregion `S ⊆ T`. A law's reach
shrinks, never grows; inside its reach it is exactly, not approximately, true.

`Layer.Visible.mono`: every proposition visible at a coarse layer stays visible
at every finer layer that refines it. **Nothing true below becomes false above,
so long as it was expressible below.** This is the precise sense in which the
tower is cumulative rather than a sequence of revolutions.

### Part 2 — where it stops being true *(proved)*

`Layer.boundary_nonempty_iff_new_visible`: for `L'` refining `L`,

```
(Boundary L' L).Nonempty  ↔  ∃ P, Visible L' P ∧ ¬ Visible L P
```

**Information lost at a boundary is exactly new expressive power.** The pairs
the lower layer conflates are in bijection, as a criterion, with the existence
of statements the higher layer can make and the lower one cannot. There is no
loss without a gain, and no gain without a loss.

This is where "becomes untrue" is located, and it is precise: the statement
that becomes available above is not one the layer below asserted and got wrong.
It is one the layer below could not state. What is *false* below is not the
statement but the layer's implicit claim to have separated everything.

`Layer.descends_iff_congruent`: an operation can be carried out entirely inside
a layer's view space **iff** the layer's indistinguishability is a congruence
for it. This is the exact content of the GLM's `can_multiply` flag: a layer
that cannot multiply is one for which the product is not a function of what the
layer sees. The law is true one level up and, at this level, not even
expressible as a function.

### Part 3 — the continuation, and why it must happen *(proved)*

`Layer.exists_indist_of_capacity_lt`: a layer whose capacity is smaller than the
carrier space **must** conflate two distinct carriers. Loss is not a defect of a
particular design; it is forced by the dimension count. A finite view of an
infinite (or merely larger) world always has a boundary, so there is always a
next layer to escalate to. This is the mechanism behind the user's "dimension
capacity", and it is why the ladder does not terminate.

**And it really does continue.** `RequestProject/GLM/Tower.lean` exhibits an
infinite tower on a single carrier type: the *dyadic layers*, where layer `n`
perceives a rational `q` as `⌊q · 2ⁿ⌋` — resolution `2⁻ⁿ`. Layer 0 is exactly
the GLM's integer layer (`dyadicLayer_zero`). Three theorems say everything the
user's "this continues, I think" needs:

* `dyadic_refines_succ` and `dyadic_refines_of_le` — every layer refines every
  layer below it, so (by `Visible.mono`) the tower is **cumulative**: nothing
  sayable at a coarse resolution is lost by going finer.
* `dyadic_boundary_nonempty` — **every** step has a non-empty boundary, and
  `dyadic_new_visible` converts that into an explicit gain: at every level there
  is a proposition the level below cannot state. `dyadic_not_lossless` confirms
  no layer is ever final. The ascent never runs out of work.
* `dyadic_separates` — and the ascent is not idle repetition: any two distinct
  carriers are told apart at some finite level.

So the ladder is unbounded, strictly increasing, cumulative, and exhaustive —
and none of its layers is the last. Contrast this with
`boundary_above_rational_empty` of §2.1: whether the tower terminates is a
property of the carrier space, not of the idea of layering. Both cases occur,
and both are proved.

`Stack.escalate` and its four correctness theorems make the ascent an algorithm:
given two carriers, `escalate` returns the **least** layer that separates them,
`escalate_eq_none_iff` characterises when no layer does, `escalate_separates`
and `escalate_minimal` prove it correct and minimal, and
`escalate_mem_boundary` places the returned index exactly on a boundary in the
sense above.

---

## 2. Four boundaries, measured

The abstract theory is worth only as much as the concrete boundaries it
locates. Four are established here, each of a different character.

### 2.1 A resolution boundary: the layer stack *(proved)*

`RequestProject/GLM/Stack.lean` builds the GLM's three lowest perspectives over
`ℚ`:

| Layer | `perceive` | Sees |
|---|---|---|
| substrate | `⌊q⌋ mod 2` in `ZMod 2` | one bit of parity |
| integer | `⌊q⌋` | the integer part |
| rational | `q` | everything |

`integer_refines_substrate`, `rational_refines_integer` and
`rational_refines_substrate` prove this is a genuine refinement chain, and
`rational_lossless` proves the top is exact.

On the region `{0, 1/2, 1, 2}` the resolutions are **2, 3, 4** and the loss
counts **2, 1, 0** (`resolution_substrate`, `resolution_integer`,
`resolution_rational`, `lossCount_substrate`, `lossCount_integer`,
`lossCount_rational`). `boundary_integer_substrate_nonempty` and
`boundary_rational_integer_nonempty` exhibit the lost pairs; and
`boundary_above_rational_empty` proves that **above the rational layer there is
nothing left to lose** on this carrier type — the ladder's continuation is not
automatic, it requires the carrier space itself to grow.

Escalation on this stack is computed, not stipulated:
`glmStack.escalate 0 1 = some 0` (parity already separates them),
`glmStack.escalate 0 2 = some 1` (parity does not; truncation does),
`glmStack.escalate 0 (1/2) = some 2` (only exact rationals do).

### 2.2 An operational boundary: where addition stops descending *(proved)*

The sharper phenomenon is not that a layer sees less, but that a *law* stops
being computable there.

* `substrate_congruent_on_integerCarriers` and
  `integer_congruent_on_integerCarriers` — on integer carriers, addition
  descends to both lower layers. **Within its reach the substrate is exactly
  right about addition.**
* `substrate_not_congruent_on_univ` and `integer_not_congruent_on_univ` — on all
  of `ℚ` it does not. `⌊1/2 + 1/2⌋ = 1` but `⌊0 + 0⌋ = 0`, while the integer
  layer cannot tell `1/2` from `0`.
* `rational_congruent_on_univ` and `rational_addition_descends` — one level up
  it descends again, and (by `descends_iff_congruent`) an explicit function on
  views exists.
* `integer_addition_does_not_descend` — and at the integer layer no such
  function exists *at all*.

This is the thesis in its strongest form: the *same law*, `a + b`, is exactly
true at the substrate on integer carriers, not merely inaccurate but
**ill-defined** at the substrate on rational carriers, and exactly true again
one layer up. The truth did not change; the domain of definition did.

### 2.3 A conservation boundary: the TAX law *(proved)*

`RequestProject/GLM/TaxConservation.lean`. The GLM assigns each carrier a cost

```
tax v = (hamming weight of v) · Y + ‖v‖² / 8,      Y = 1 / (π + 2/π)
```

On binary carriers, with `Q = Y + 1/8`, the law

```
tax (a XOR b) + 2 · tax (a AND b) = tax a + tax b            (tax_conservation)
```

holds **exactly**, for every `a` and `b` — proved from
`|s Δ t| + 2|s ∩ t| = |s| + |t|` on supports.

Raise the carriers from bits to naturals, keeping bitwise XOR and AND, and it
fails: `tax_conservation_fails_at_integer_layer` exhibits `1` and `2`, where
`1 XOR 2 = 3` and `1 AND 2 = 0`. And the failure is not a near miss to be
patched. `tax_conservation_at_integer_layer_iff` proves that conservation for
that single pair holds **iff** `Y = 1/2` — which is false, since
`Y_lt_half` gives `Y = 1/(π + 2/π) < 1/2` (in fact `1/4 < Y < 1/2`).

So the boundary is not blurry. The law is exact below it and provably
irreparable above it: the only value of the GLM's own constant that would save
it is one the constant does not have.

### 2.4 A decoding boundary: the Golay snap radius *(proved)*

`RequestProject/GLM/GolayBoundary.lean`. The GLM repairs a corrupted carrier by
snapping it to the nearest Golay codeword. For any code of minimum distance 8:

* `snap_unique_of_le_three` — at Hamming distance ≤ 3 from a codeword, the
  nearest codeword is **unique**. Repair is a total, correct function.
* `snap_ambiguous_at_four` — at distance exactly 4 from two codewords 8 apart,
  there are **two** codewords at distance 4, and `snap_ambiguous_ne` proves
  them distinct. Repair is not a function.
* `snap_boundary_at_three` — 3 is exactly the largest radius at which uniqueness
  survives.

The boundary here is a single integer. At weight 3 the substrate's repair is
truth; at weight 4 the same procedure returns two incompatible answers and the
question has to be handed up to a layer that carries more than parity.

---

## 3. The measurement on the real system

`information_loss.py` runs the same definitions against the GLM's actual
24-coordinate carriers and the real `dimension_layers` perceive maps, in exact
`Fraction` arithmetic. The carrier set is fixed and small, chosen to exercise
each handoff:

| # | carrier | what it is there for |
|---|---|---|
| 0 | the vacuum | the baseline every other carrier is compared against |
| 1 | `1/2` on coordinate 0 | an integer-layer boundary: truncation cannot see the half |
| 2 | `1` on coordinate 0 | the unit |
| 3 | `2` on coordinate 0 | a substrate boundary: parity cannot see an even amplitude |
| 4 | `1` on coordinate 10 | **outside the seven SI7 exponents** — the carrier that exposed the refinement defect of §3.1 |
| 5, 6 | two carriers repairing to one 2A axis | the pair that forces the Griess measure to carry the carrier term |

Measured (`report information loss`, and reproduced in a fresh interpreter by
the generated verification script):

| Layer | dimension | capacity | resolves | loses | addition descends |
|---|---|---|---|---|---|
| substrate | 24 | 2²⁴ = 16777216 | 3 / 7 | 4 | no |
| integer | 7 exponents, over the 24 substrate bits | unbounded | 5 / 7 | 2 | no |
| rational | 10 | unbounded | 7 / 7 | 0 | **yes** |
| griess | 196884 | unbounded | 7 / 7 | 0 | **yes** |
| universal | unbounded | unbounded | 7 / 7 | 0 | **yes** |

| Boundary | pairs lost | is a refinement |
|---|---|---|
| substrate → integer | 8 | **yes** |
| integer → rational | 2 | **yes** |
| rational → griess | 0 | **yes** |
| griess → universal | 0 | **yes** |

```
refinement_chain_intact : True
```

The eight pairs the substrate → integer boundary gains are `(0,3) (0,5) (0,6)
(1,3) (1,5) (1,6) (3,5) (3,6)`; the two the integer → rational boundary gains
are `(0,1)` — vacuum against a half, which truncation cannot see — and `(5,6)`,
the axis pair. Above the rational layer nothing is gained, because nothing is
left to gain: the rational view *is* the carrier.

The pattern of §2.2 reappears on the real system unchanged: addition descends
only from the rational layer up, and the witnesses are produced explicitly and
re-checked against the definition rather than trusted.

### 3.1 An audit finding, and the decision that closed it

An earlier round of this study ran the definitions against the shipped layer
definitions rather than an idealisation of them and found the chain broken:

```
substrate → integer :  (vacuum, unit-at-coordinate-10)  and  (half, unit-at-coordinate-10)
refinement_chain_intact : False
```

`refinement_violations` looks for the opposite of a boundary — pairs the
*lower* layer splits and the *higher* one conflates. The substrate perceives a
24-bit parity view, so it separates a unit on coordinate 10 from the vacuum. An
integer layer that perceives only the seven SI exponents does not: coordinate
10 is not among them. Escalating from the substrate to such an integer layer
**destroys a distinction the layer below already had**, and by `Visible.mono`
that is exactly the situation in which the cumulative guarantee fails — a
proposition visible at the substrate need not remain visible above.

**The two candidate fixes.** Only two things can be changed, because only two
perceive maps are involved:

1. **Widen the integer layer's view** so that it retains what the substrate
   separates: read the seven SI7 exponents *and* keep the substrate's parity
   reading beside them, making the integer view cumulative over the one below.
   The chain is then a refinement by construction, and the integer layer
   resolves strictly more than either reading alone.
2. **Narrow the substrate's view** so that it claims only what the layer above
   can keep: restrict parity to the seven coordinates SI7 reads, and let the
   substrate say nothing about coordinates 7–23. The chain is then a
   refinement because the lower layer has stopped making the distinction.

**Which one the project's own account of layers commits it to.** Widening.
The account of a layer in §1 is that a layer is a *view* of a fixed carrier
space, that a boundary is a place where the layer above can say something new,
and — Part 3, `Tower.lean` — that the ascent is *cumulative*: "every single
step is a strict gain in expressive power and no step loses anything earlier."
Narrowing would satisfy `refinement_chain_intact` by deleting a true
distinction the substrate can genuinely make: the substrate really does see a
unit on coordinate 10, and a repair that makes it stop seeing it buys the
invariant by making the machine less able. It would also break the reading of
capacity in §2.1, where the substrate's 2²⁴ bound is a fact about 24
coordinates, not about seven. Widening is the reading the rest of the document
already assumes, and it is the one that keeps the informal instruction the
project was given — *no information should be lost at any stage* — literally
true of the stack.

**What was implemented.** `dimension_layers.LAYER_INTEGER` is cumulative: its
view carries `substrate_bits` and `hamming_weight` from the substrate beside
the seven `exponents_SI7`, and its measure keeps the substrate term, so a
zero distance at the integer layer forces a zero distance at the substrate.
The same treatment repairs the rational → griess step: the Griess view carries
the carrier itself beside the algebra element, which is what separates carriers
5 and 6 — one 2A axis to the algebra, two carriers to the layer. The universal
layer carries the Griess view and the integer view at once.

The narrow reading is **kept beside the shipped one** rather than deleted, as
`dimension_layers.LAYER_INTEGER_RAW`, and the report measures what it would
have cost, so the decision stays legible and checkable rather than being
recorded only in a commit message:

| reading | resolves | loses | refines the substrate | violating pairs |
|---|---|---|---|---|
| `LAYER_INTEGER_RAW` (narrow, rejected) | 4 / 7 | 3 | **no** | `(0,4)`, `(1,4)` |
| `LAYER_INTEGER` (cumulative, shipped) | 5 / 7 | 2 | **yes** | none |

`LAYER_INTEGER_RAW` is not a member of `dimension_layers.LAYERS`; a test
asserts that.

**Machine-checked.** The layers as they now are, with their real 24-coordinate
carriers, are formalised in `RequestProject/GLM/LayerChain.lean` and the chain
is proved a refinement there — not on a special case and not on an
idealisation. The theorems, by full name:

| name | what it says |
|---|---|
| `GLM.Info.glmChain_refines_of_le` | `refinement_chain_intact` itself: for `m ≤ n`, layer `n` of the shipped chain refines layer `m` |
| `GLM.Info.glmChain_refines_succ` | each single step refines the one below it |
| `GLM.Info.glmChain_visible_mono` | nothing the substrate can state is lost anywhere up the chain |
| `GLM.Info.glmIntegerLayer_refines_glmSubstrateLayer` | the widened integer layer keeps the substrate's view |
| `GLM.Info.glmIntegerLayer_refines_glmSi7Layer` | it keeps the seven exponents too |
| `GLM.Info.glmIntegerLayer_least` | it is the *coarsest* reading that keeps both — widening adds no resolution beyond what the two views already had |
| `GLM.Info.glmSi7Layer_not_refines_glmSubstrateLayer` | the defect, as a theorem: the narrow SI7 reading does **not** refine the substrate |
| `GLM.Info.glmIntegerLayer_separates_unitOutside` | the shipped integer layer separates the exact pair that exposed it |
| `GLM.Info.substrate_separates_unitOutside`, `GLM.Info.si7_conflates_unitOutside` | the two halves of that witness, separately |
| `GLM.Info.boundary_glmIntegerLayer_glmSubstrateLayer_nonempty` | the substrate → integer boundary is still a real boundary: the repair did not collapse the two layers into one |
| `GLM.Info.glmRationalLayer_lossless`, `GLM.Info.glmGriessLayer_lossless`, `GLM.Info.glmUniversalLayer_lossless` | the top three layers lose nothing at all |
| `GLM.Info.glmGriessLayer_refines_glmRationalLayer`, `GLM.Info.glmUniversalLayer_refines_glmGriessLayer`, `GLM.Info.glmUniversalLayer_refines_glmIntegerLayer` | the remaining steps |

The chain itself is `GLM.Info.glmChain`, and the carriers are
`GLM.Info.vacuum24` and `GLM.Info.unitOutside` (a unit on coordinate 10) —
carriers 0 and 4 of `sample_carriers` above. The general machinery the repair
uses is `GLM.Layer.cumulative` with `GLM.Layer.cumulative_refines_left`,
`GLM.Layer.cumulative_refines_right`, `GLM.Layer.cumulative_least` and
`GLM.Layer.cumulative_lossless_left`, in `RequestProject/GLM/Cumulative.lean`.

**Pinned.** `tests/test_information_loss.py` holds the repair in place:
`TestRefinementChain` asserts `refinement_chain_intact is True` and that no
boundary has a violation; `TestCumulativity` asserts that the integer view
literally carries the substrate reading and that its measure dominates;
`TestTheClosedRefinementDefect` re-checks the specific carrier pair from every
angle — the substrate separates it, every layer of the stack separates it, no
boundary in the report conflates it, resolution never decreases going up, and
the narrow reading still fails on exactly that pair; and
`TestNonCumulativeReading` measures the rejected reading.

---

## 4. What the study concludes

1. **"True up to a point, then untrue" is correct, on one precise reading and
   not on another.** Propositions do not change truth value; what changes is
   which propositions are *expressible*, and whether an operation is a
   *function* of what a layer sees. Both are formalised, and the second is
   where the interesting failures live (§2.2, §2.3).

2. **Loss and gain are the same event.** `boundary_nonempty_iff_new_visible`
   makes them equivalent, so a layer boundary can be detected from either side:
   by what is conflated below or by what becomes sayable above.

3. **The ascent is forced, and it is computable.** Capacity below the carrier
   count forces conflation; `escalate` finds the least layer that resolves a
   given pair, provably minimally. The ladder continues as long as the carrier
   space outgrows the view space — and `boundary_above_rational_empty` shows
   the converse: when it does not, the ladder stops.

4. **"This continues" is a theorem, not a hope.** The dyadic tower is an
   explicit infinite ladder in which every single step is a strict gain in
   expressive power and no step loses anything earlier. Whether a particular
   tower terminates depends on the carriers, but nothing in the notion of a
   layer forces it to.

5. **Boundaries in this system are sharp, not gradual.** Weight 3 versus 4 for
   Golay repair; integer versus rational carriers for addition; bits versus
   naturals for TAX conservation, where the *only* repair would require
   `Y = 1/2`. In each case the exact location is a theorem, not an estimate.

6. **The method finds real defects, and closes them.** Applying the same
   definitions to the shipped code, rather than to an idealisation of it,
   located a genuine refinement hole between the substrate and integer layers.
   The hole was closed by widening the integer layer's view rather than
   narrowing the substrate's — the choice the project's own account of a
   cumulative ascent commits it to — and the chain is now a refinement on the
   real carriers, in the code (`refinement_chain_intact = True`) and in Lean
   (`GLM.Info.glmChain_refines_of_le`). The rejected reading is kept beside
   the shipped one and its cost is still measured (§3.1).

---

## 5. Where to look

| File | Contents |
|---|---|
| `RequestProject/GLM/Layers.lean` | the abstract theory: layers, refinement, visibility, boundaries, congruence, capacity, resolution, stacks, escalation |
| `RequestProject/GLM/Tower.lean` | the unbounded dyadic tower: cumulative, strictly increasing at every step, exhaustive, with no final layer |
| `RequestProject/GLM/Cumulative.lean` | how a view is widened to keep the one below it: `Layer.cumulative`, and the four lemmas that make it the least such widening |
| `RequestProject/GLM/LayerChain.lean` | the shipped five layers on the real 24-coordinate carriers, and the proof that the chain is a refinement — `GLM.Info.glmChain_refines_of_le` |
| `RequestProject/GLM/Stack.lean` | the concrete three-layer stack, its boundaries, the operational boundary for addition, resolution/loss measurements, worked escalations |
| `RequestProject/GLM/Constants.lean` | `Y`, `Q`, TAX, NRCI, the coherence regimes, and the proof that the NRCI bands are exactly TAX bands |
| `RequestProject/GLM/TaxConservation.lean` | the conservation law on bits and its irreparable failure above |
| `RequestProject/GLM/GolayBoundary.lean` | unique repair at weight ≤ 3, ambiguity at weight 4 |
| `glm_universal/reasoning/information_loss.py` | the executable counterpart |
| `glm_universal/tests/test_information_loss.py` | 60 tests pinning every number quoted in §3, the refinement chain, and the carrier pair that exposed the defect |
