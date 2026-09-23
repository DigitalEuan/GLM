# The four pieces left in the source material — two ported, two measured and left in the sandbox

## Tier 0 — the coarse read

**Question.** Phase 54 read, ran and left four parts of the supplied conversational material unported: a role–filler binding, a content-addressed store of resolved plans, a four-register memory split and a generator of Lean source from carriers. Taken one at a time, with the measurement each was told to make, which of them is worth shipping?

**Verdict.** Two are. The parity binding inverts with no side condition and is proved to; recovering a **name** from it is worth exactly what the registers' parity readings are worth, which is 424 of 1,143 carriers and a forced refusal on the rest, and the product binding offered beside it is refuted. The plan store keeps a refusal as it keeps an answer, replays all fifteen declared follow-ups unchanged and takes their licensing trials from 27 to 0, while the key that ignores the conversation answers 8 of the 15 with another conversation's antecedent. The other two are not. The four-register split is recency with a decay rate once a pronoun has named no concept: it agrees with licensing on 5 of the 8 follow-ups the shipped layer binds and answers 6 of the 7 it refuses, mostly by choosing a member of the ambiguity the refusal exists to keep open. The Lean generator's own round-trip check never reads what it generated — it passes for a generator that emits the empty string — and the real round trip returns the reading it was generated from on 0 of 12 carriers.

**Deciding figure.** <!--figure:binding-as-declared-->12<!--/figure--> of <!--figure:binding-declared-count-->12<!--/figure--> declared bindings came out as declared, with <!--figure:binding-nameable-->424<!--/figure--> of <!--figure:binding-carriers-->1,143<!--/figure--> carriers nameable; the store replayed <!--figure:planstore-replayed-->15<!--/figure--> of <!--figure:planstore-declared-count-->15<!--/figure--> follow-ups including <!--figure:planstore-refusals-replayed-->7<!--/figure--> of <!--figure:planstore-refusals-->7<!--/figure--> refusals; and the two sandbox pieces are unpromoted.

**Recomputed by.** `glm_universal.reasoning.role_binding.binding_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 1. What this round took, and from where

[`CONVERSATION_STUDY.md`](CONVERSATION_STUDY.md) §9 is a table of six things
the supplied material holds and what each would have to measure to earn a
round. Four of them were named again in [`STATUS.md`](../STATUS.md) §3.4 as
the part of Phase 54 that was read and run and then left in
`source_material/`. This round takes those four, and holds each to the line
§9 wrote for it rather than to a line written afterwards.

| piece | what §9 asked for | what happened |
|---|---|---|
| role–filler binding `R⊗A⊗B` | *recoverability is a theorem, not a demo: state it over the substrate and prove it, with the collision rate as the control* | **shipped** — §2, §3; `GLM.RoleBinding` |
| content-addressed procedure store | *a speed-up is a cost result, not a target result (D15); it would have to show a refusal preserved across replay, or it is maintenance* | **shipped** — §4; `GLM.PlanStore` |
| four-register memory split | *which questions are answered because of the split that are not answered without it* | **sandbox** — §5; the answer is none |
| Lean generation from carriers | *these compile to `sorry`; a round would have to close one of them, and D8 says the Lean file is the specification, not the output* | **sandbox** — §6; the check is refuted before the question arises |

The two remaining rows of §9 — trajectory licensing and the missing-node
proposer — are untouched and stay there.

## 2. The binding: one word, and what comes out of it

A typed relation *R(A, B)* is written as a single 24-bit word. The role `R`
has no carrier: it is a permutation of the coordinates, one per relation type,
and `glm_universal.reasoning.role_binding.ROLES` is the supplied table of
seven of them, unchanged. Writing `parity` for the substrate's 24-bit reading
of a carrier and `σ` for the role's permutation,

```
bind(σ, a, b)   = σ·parity(a) ⊕ parity(a) ⊕ parity(b)
unbind(σ, a, w) =  w ⊕ σ·parity(a) ⊕ parity(a)
```

and the two are the same operation, which is the whole of why this half of the
supplied claim is true. The readings are an elementary abelian 2-group, the
role acts on it by permuting coordinates, and `GLM.RoleBinding.unbind_bind`
has no hypothesis at all: the binding inverts with no side condition, and the
filler's reading comes back exactly, for every role, every known side and
every filler.

Three things follow, and each is proved rather than observed:

* the binding is **injective in the filler**
  (`GLM.RoleBinding.bind_injective_right`) and **surjective** onto readings
  (`bind_surjective_right`) — so a bound word on its own says nothing, and it
  is the pair *(role, known side)* that makes it say something;
* two roles bind alike exactly when they agree on the known side
  (`bind_eq_iff_role_agrees`), and they can:
  `roles_differ_but_bind_alike` exhibits two different roles binding a pair
  identically, so **the relation type cannot be read back out of the word**;
* the recovery does not depend on the role or the known side at all
  (`recover_bind_independent_of_role`), which is why what a binding is worth
  here is a measurement of the **registers** and not of the binding.

### The other binding, refuted

The material offered a second binding beside it and calls both recoverable: the
elementwise product of the three exact rational 24-vectors, undone by
elementwise division. It is invertible only where the key reads nowhere zero
(`GLM.RoleBinding.hbind_recover`), and a single zero coordinate makes two
different fillers bind to the same vector
(`GLM.RoleBinding.hbind_not_injective_of_zero`) — so no procedure recovers the
filler, division or search.

<!--figure:binding-product-zero-->1,133<!--/figure--> of the
<!--figure:binding-carriers-->1,143<!--/figure--> carriers this system loads
read zero somewhere. The
<!--figure:binding-product-recoverable-->10<!--/figure--> that do not are all
in the mathematics register and take three distinct values between them —
eight of the ten are one and the same vector, the eight `filled_r×c` shapes.
So the only known sides a product binding could be recovered from are carriers
that seven others are identical to. The claim is refuted rather than
qualified.

## 3. From a reading to a name — the collision rate, which is the control

Unbinding returns a *reading*. Turning a reading into a **name** is a second
step and it is where the cost is: recovering a name is worth exactly what the
registers' parity readings are worth. A reading is 24 parity bits, a register
is a list of carriers, and what a recovery holds is a fibre of the parity map. A
name comes back when the fibre holds one (`GLM.RoleBinding.recover_ok_iff`,
`recover_sound`); two or more is `ambiguous-recovery` and none is
`no-carrier`, and neither is a failed search — both are statements about the
register.

<!-- generated: binding-fibres -->
| register | carriers | distinct readings | nameable | largest fibre |
|---|---|---|---|---|
| `physics` | 726 | 128 | 57 | 136 |
| `chemistry` | 118 | 117 | 116 | 2 |
| `molecules` | 51 | 43 | 37 | 3 |
| `mathematics` | 22 | 10 | 8 | 8 |
| `lexicon` | 149 | 145 | 141 | 2 |
| `spatial` | 28 | 25 | 22 | 2 |
| `harmonics` | 28 | 28 | 28 | 1 |
| `economics` | 21 | 18 | 15 | 2 |
| **all** | 1,143 | 514 | 424 | 136 |
<!-- end generated -->

<!--figure:binding-nameable-->424<!--/figure--> carriers read uniquely and can
be named. The other
<!--figure:binding-ambiguous-->719<!--/figure--> cannot, and the physics
register is where it hurts: 726 carriers take 128 distinct readings, and the
largest fibre holds <!--figure:binding-largest-fibre-->136<!--/figure--> of
them — every dimensionless quantity reads as all-zero parity. One register,
`harmonics`, is injective: 28 carriers, 28 readings.

The refusal is not fussiness, because the cheap alternative is wrong. The
supplied code, when the fibre is not a singleton, returns the nearest carrier
by Hamming distance and says nothing about having chosen. That rule is right
once per fibre — it returns whichever member the register lists first — so
over the whole corpus it names the bound carrier
<!--figure:binding-readings-->514<!--/figure--> times and another carrier
<!--figure:binding-control-wrong-->629<!--/figure--> times, with nothing in
its answer to distinguish the two.
`GLM.RoleBinding.nearest_names_the_wrong_carrier` is that statement proved on
a two-row register.

### The declared set

Twelve bindings, written down before they were run: six that must name their
filler, three that must refuse because the register's readings collide, and
three that must refuse because a role or a name is not declared.

<!-- generated: binding-declared -->
| binding | role | known / filler | register | declared | outcome | nearest-mask control | as declared |
|---|---|---|---|---|---|---|---|
| `element-recovered` | `causes` | `C` / `O` | `chemistry` | `O` | `O` | `O` | yes |
| `element-other-role` | `derived_from` | `C` / `O` | `chemistry` | `O` | `O` | `O` | yes |
| `element-far-apart` | `part_of` | `H` / `Og` | `chemistry` | `Og` | `Og` | `Og` | yes |
| `molecule-recovered` | `affected_by` | `water` / `methane` | `molecules` | `methane` | `methane` | `methane` | yes |
| `harmonic-recovered` | `contrasts_with` | `unison` / `perfect_fifth` | `harmonics` | `perfect_fifth` | `perfect_fifth` | `perfect_fifth` | yes |
| `lexicon-recovered` | `mentioned_after` | `force` / `mass` | `lexicon` | `mass` | `mass` | `mass` | yes |
| `element-collision` | `causes` | `C` / `Ba` | `chemistry` | `ambiguous-recovery` | `ambiguous-recovery` | `Ba` | yes |
| `lexicon-collision` | `equals` | `force` / `energy` | `lexicon` | `ambiguous-recovery` | `ambiguous-recovery` | `energy` | yes |
| `physics-collision` | `derived_from` | `acceleration` / `absorptance` | `physics` | `ambiguous-recovery` | `ambiguous-recovery` | `abbe_dispersion_number` | yes |
| `unknown-role` | `rhymes_with` | `C` / `O` | `chemistry` | `unknown-role` | `unknown-role` | -- | yes |
| `unknown-name` | `causes` | `C` / `phlogiston` | `chemistry` | `unknown-name` | `unknown-name` | -- | yes |
| `unknown-known-side` | `causes` | `phlogiston` / `O` | `chemistry` | `unknown-name` | `unknown-name` | -- | yes |

the parity binding writes a typed relation into one 24-bit word and gives the filler's reading back exactly, with no side condition; naming the filler is a second step, and on the 12 declared bindings it names 6 and refuses 6 under 3 of its 4 named reasons, every one of them as declared before the run. Across the 1143 carriers the session loads, 424 read uniquely and so can be named; the other 719 share a reading with another carrier of their own register, the worst fibre holding 136 of them in physics. The product binding of the same material is recoverable from 10 of 1143 known sides: one zero coordinate is enough to make two fillers bind alike, 1133 carriers read zero somewhere, and the 10 that do not take only 3 distinct values between them.

what comes back is a reading, not a name, and whether a reading names a carrier is a property of the register rather than of the binding: the same word recovers the same reading under every role and every known side. The nearest-mask control -- the supplied search, which answers whatever the fibre holds -- names a carrier other than the one that was bound on 1 of the 9 bindings it applies to and answers without comment on every one of the 3 the operation refuses; taken over every carrier rather than the declared set it is right once per fibre, which is 514 of 1143 and wrong on the other 629. Nothing here is a claim that a relation type means anything: a role is a permutation someone wrote down, and two roles that agree on the known side bind identically.
<!-- end generated -->

The collisions are real rows of the shipped registers rather than fixtures:
barium and lead read alike in the chemistry table, *energy* and *work* in the
lexicon, and `absorptance` sits in the 136-strong all-zero fibre of physics.

## 4. The plan store: a refusal kept

Resolving a follow-up is not free. The conversation layer decides a referent
by **licensing** — substitute the candidate, ask the session whether the query
solves — so *describe it* after a fourteen-row tie costs fourteen trial solves
and then refuses. The supplied store keeps *successful* plans against the
SHA-256 of the plan, which means the one case worth keeping is the case it
does not keep.

`glm_universal.runtime.plan_store` keeps both, and
`glm_universal.runtime.conversation.Conversation` takes one as an optional
`store=`. What is stored is the whole of what resolving decided: the turns
asked before it, the follow-up, the shape, and either the antecedent and the
rewritten query or the refusal with its reason and its wording. What is
**not** stored is any answer — the rewritten query is asked of the session on
every pass, so the store can save trials and cannot make an answer stale.

Three properties, proved in `GLM.PlanStore`:

* what is recorded comes back (`lookup_record`), refusals included
  (`refusal_survives_replay`);
* a store is a memo and not a second opinion: with a key that separates plans,
  a hit on a sound store is exactly what resolving again would have said
  (`replay_agrees_with_run`), and where resolving refuses it is that refusal
  (`replay_preserves_refusal`);
* and the key has to cover the conversation
  (`coarse_key_answers_the_wrong_question`, `exactKey_injective`).

The key is the SHA-256 of the prefix and the follow-up together, which is
directive **D4** kept rather than quoted. The digest addresses integrity and
never meaning (**D3**): a hit is checked against the stored plan's own prefix
and text before it is used, so a digest collision costs a miss and cannot cost
an answer.

<!-- generated: planstore-declared -->
| follow-up | the turn asked | outcome | a refusal | trials first | trials replayed | replayed | coarse-key control |
|---|---|---|---|---|---|---|---|
| `pronoun-describe` | `describe it` | `C` | no | 1 | 0 | yes | `no-antecedent` |
| `pronoun-after-extremum` | `describe it` | `Og` | no | 1 | 0 | yes | `no-antecedent` |
| `pronoun-licensing-skips` | `field electronegativity_pauling of it` | `C` | no | 2 | 0 | yes | `unlicensed` |
| `pronoun-licensing-agrees` | `field molar_mass_u of it` | `water` | no | 1 | 0 | yes | `water` |
| `pronoun-analogy-answer` | `describe it` | `Ne` | no | 1 | 0 | yes | `no-antecedent` |
| `pronoun-nearest-subject` | `describe it` | `O` | no | 1 | 0 | yes | `no-antecedent` |
| `end-flip` | `and the smallest?` | `answer` | no | 1 | 0 | yes | `no-antecedent` |
| `subject-substitution` | `and oxygen?` | `oxygen` | no | 1 | 0 | yes | `oxygen` |
| `pronoun-tie-refused` | `describe it` | `ambiguous-antecedent` | yes | 14 | 0 | yes | `no-antecedent` |
| `pronoun-two-subjects` | `describe it` | `ambiguous-antecedent` | yes | 2 | 0 | yes | `no-antecedent` |
| `pronoun-first-turn` | `describe it` | `no-antecedent` | yes | 0 | 0 | yes | `no-antecedent` |
| `pronoun-unlicensed` | `field electronegativity_pauling of it` | `unlicensed` | yes | 1 | 0 | yes | `unlicensed` |
| `end-flip-no-column` | `and the smallest?` | `no-antecedent` | yes | 0 | 0 | yes | `no-antecedent` |
| `subject-ambiguous` | `and nitrogen?` | `ambiguous-antecedent` | yes | 0 | 0 | yes | `ambiguous-antecedent` |
| `subject-unlicensed` | `and water?` | `unlicensed` | yes | 1 | 0 | yes | `unlicensed` |

the store keeps all 15 resolved follow-ups, 7 of them refusals, under 15 distinct keys, and replays every one of them unchanged -- 15 of 15 outcomes and 7 of 7 refusals, reason and wording included. The licensing trials the fifteen cost fall from 27 to 0, the worst single follow-up being 14 trials. Keyed by the follow-up text alone, the same store answers 8 of the 15 with another conversation's antecedent.

the store saves the licensing trials and nothing else: the rewritten query is still asked of the session on every pass, so no answer is stored and none can go stale. 3 follow-up texts are shared by more than one declared script, which is why the key covers the whole conversation; a hit is checked against the stored plan's own prefix and text before it is used, so a digest collision costs a miss rather than an answer.
<!-- end generated -->

All <!--figure:planstore-replayed-->15<!--/figure--> replay unchanged,
including all <!--figure:planstore-refusals-replayed-->7<!--/figure-->
refusals with their reason and their wording. The licensing trials fall from
<!--figure:planstore-trials-first-->27<!--/figure--> to
<!--figure:planstore-trials-replayed-->0<!--/figure-->, and the worst single
follow-up — <!--figure:planstore-worst-case-->14<!--/figure--> trials — is the
tie, which is a refusal. That is the whole of the argument for storing
refusals: the expensive case is the one the supplied store throws away.

The control is the coarse key, which keys a plan by its follow-up text alone.
Six of the fifteen follow-ups are the words *describe it* and they have four
different antecedents between them, so the coarse store answers
<!--figure:planstore-coarse-wrong-->8<!--/figure--> of the fifteen with
another conversation's antecedent — silently, because a key that ignores the
conversation and cannot tell two conversations apart has nothing to report.

## 5. The four-register split, measured and left in the sandbox

The supplied split is episodic (decaying at 9/10 a turn), semantic,
procedural and preference registers, each with its own weighting of concept
overlap, recency, intent match and a constant, in exact rationals.
`glm_universal.sandbox.memory_split` is those weights, unchanged, run over the
conversation's own turns and compared with licensing on the same fifteen
declared follow-ups.

The result is structural rather than a matter of tuning. **A pronoun names no
concept**, so the concept-overlap component of every score is zero on every
pronoun follow-up, and what is left is recency and intent — the control
[`CONVERSATION_STUDY.md`](CONVERSATION_STUDY.md) §5 already ran. The split
names the same antecedent as licensing on **5 of the 8** follow-ups the
shipped layer binds, moves **3** of the answers the shipped layer gives, and
on the **7** it refuses it answers **6** — mostly by choosing a member of an
`ambiguous-antecedent`, which is the ambiguity the refusal exists to keep
open. **2** of the six produce a query the session really answers, and both
of those do it that way, which is the thing the refusal is for.

So the answer to the question §9 asked — *which questions are answered because
of the split that are not answered without it* — is **none**. The promotion
checklist is computed, and its utility line is the one that fails:

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.sandbox.memory_split
```

## 6. The Lean generator: a check that never read what it generated

The generator reads a carrier as a declaration's 24 structural counts — with
the shipped `reasoning.lean_address`, which is the reader the whole address
book is built on — and writes Lean source with those counts. Twelve such
declarations ship with the material as
`lean/glm_generated_theorems.lean`, each ending `:= by sorry`. Beside them is
the generator's own round-trip check, `round_trip_check`, which reports the
generation faithful.

**It never reads what was generated.** Its own comment says so — *we can't
actually parse the source without lean files set up* — and what it does
instead is re-quantise the original carrier and compare the result with the
reading it generated from, which is a comparison between a value and itself.
`glm_universal.sandbox.lean_generation.supplied_check_is_vacuous` makes the
point the only way worth making it: the same check, run against a generator
that emits the **empty string**, passes on all twelve.

**The real round trip fails.** Writing the generated source out and reading it
back with `lean_address.parse_file`:

| measurement | result |
|---|---|
| declarations the reader finds | 12 of 12, one each |
| readings a declaration could actually have | **1 of 12** |
| readings that survive the round trip | **0 of 12** |
| coordinates that agree, of 24 | between 14 and 21 |

Three causes, all structural. The reading of a *physical* carrier is not in
the range a declaration's counts live in — kind codes of 8, 16 and 20 where
only 1–5 name a kind, and negative quantifier counts. The generator takes the
absolute value of a negative count rather than refusing it, and maps an
out-of-range kind silently to `theorem`. And the counts it does not control —
statement size, parenthesis depth, namespace depth — are decided by whatever
text it happens to write.

**And none of the twelve is a statement.** Elaborated against this
repository's Mathlib:

```bash
cp source_material/conversation_experiment/lean/glm_generated_theorems.lean /tmp/gen.lean
sed -i '1i import Mathlib' /tmp/gen.lean && lake env lean /tmp/gen.lean
```

gives **44 errors on 12 lines, one line per declaration**: `(x1 : α)` where a
type is expected, `∑ i, f i` as a proposition, and `P`, `Q`, `f` and `n` free.
That run is not in the test suite — a Mathlib elaboration is minutes — so the
promotion checklist reports the elaboration line as *unmeasured* rather than
assuming it, which is the mistake this whole section is about.

Under **D8** a generator of Lean is a generator of *specifications*, so the
checklist's last line is that at least one generated statement is **proved**.
A `sorry` is not a claim that has been made.

## 7. What moved, under D15

**Addressing.** A filler recovered from a word that is not its key, the key
being the role and the known side — and the measured limit of that, which is
the parity map's fibres.

**Refusal.** Two new named refusals in the binding, one of which
(`ambiguous-recovery`) is forced by the registers on
<!--figure:binding-ambiguous-->719<!--/figure--> of their
<!--figure:binding-carriers-->1,143<!--/figure--> carriers; and, in the store,
a refusal that can now be kept, handed back unchanged and held to.

**Derivation.** Nothing. The binding computes no quantity, and the store
computes nothing at all — every answer is still the session's.

The two sandbox pieces moved none of the three, which is why they are in the
sandbox.

## 8. Limits

* **A role is a permutation somebody wrote down.** Nothing here says that
  `causes` means causation; the seven permutations are the supplied ones, and
  two roles that agree on the known side are indistinguishable.
* **The binding names a fibre, not a carrier.** Where the fibre is not a
  singleton the operation refuses, and 719 of 1,143 carriers are in that
  position. Widening the reading — parity is 24 bits of a rational
  24-vector — would shrink the fibres, and that is a different round with its
  own control.
* **The store replays a *binding*, never an answer.** It saves licensing
  trials and nothing else. A store that kept answers would have to say what
  invalidates them, and nothing here does.
* **The store is per-conversation by construction.** Two conversations with
  the same prefix and the same follow-up share a key, which is correct, and
  nothing carries a plan from one session to another.
* **The sandbox measurements are of the supplied constructions.** A different
  weighting of the four registers, or a generator that refused an out-of-range
  reading instead of taking its absolute value, might do better; what is
  measured here is what was supplied.

## 9. Re-running it

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.tools binding
PYTHONPATH=. python3 -m glm_universal.runtime.plan_store
PYTHONPATH=. python3 -m glm_universal.sandbox.memory_split
PYTHONPATH=. python3 -m glm_universal.sandbox.lean_generation
PYTHONPATH=. python3 -m pytest glm_universal/tests/test_role_binding.py \
    glm_universal/tests/test_plan_store.py \
    glm_universal/tests/test_supplied_sandbox.py -q
cd .. && lake build RequestProject.GLM.RoleBinding RequestProject.GLM.PlanStore
```
