# The declared majority rule — conflicting evidence, and when believing the majority is sound

## Tier 0 — the coarse read

**Question.** Phase 183's dispersion guard refuses every set of examples that disagree, although on two good examples and one decoy the majority target answered 155 of 300 right and 0 wrong. Can that majority be declared as a rule with its own soundness condition, and what does it cost where the condition fails?

**Verdict.** The rule is declared and proved: split the examples into agreeing groups, each a null vector in the evidence space, and answer the target a strict majority of the weight states; it is never wrong while the honest examples hold at least half the weight and always right above half, the condition is tight because agreeing decoys below half carry it, a wrong answer needs decoys weighing at least the answer's own group, and wherever the guard answers the rule answers the same; in measurement it recovers every right answer the guard gave up on honest majorities at no wrong answer, refuses where a plurality vote is misled by a colluding pair, but refuses as well where a plurality would have been right because the decoys happened to disagree.

**Deciding figure.** 8 of 8 marks; decoy3 155 right, 0 wrong (guard 0 right); decoy5 161 right, 0 wrong (guard 0 right); collude5 0 wrong where the plurality vote is wrong 150 times; collude3 148 wrong, exactly the queries the tightness theorem predicts; decoy4 0 right where the vote has 149.

**Recomputed by.** `glm_universal.reasoning.lorentzian_majority_study.lorentzian_majority_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

*Created 23 October 2026. Pre-registered 23 October 2026: the marks (§5) were
written into `reasoning/lorentzian_majority_study.py` and committed before the
measurement was first run. Measured 23 October 2026, one take.*

## 0. What this document is

**In one paragraph.** The rule is declared and proved: split the examples into agreeing groups, each a null vector in the evidence space, and answer the target a strict majority of the weight states; it is never wrong while the honest examples hold at least half the weight and always right above half, the condition is tight because agreeing decoys below half carry it, a wrong answer needs decoys weighing at least the answer's own group, and wherever the guard answers the rule answers the same; in measurement it recovers every right answer the guard gave up on honest majorities at no wrong answer, refuses where a plurality vote is misled by a colluding pair, but refuses as well where a plurality would have been right because the decoys happened to disagree.

Phase 184, taken from [`STATUS.md`](../STATUS.md) §2.1 item 11, its first
line: *a declared majority rule for conflicting examples (the vote answered
155 of 300 right, 0 wrong, where the dispersion guard refused all 300), with
its own soundness condition*
([`LORENTZIAN_EVIDENCE_STUDY.md`](LORENTZIAN_EVIDENCE_STUDY.md) §4 and §8).

## 1. The rule, in the evidence space

Phase 183 showed that a set of cues sums to one vector, the lifted consensus
plus the Weyl vector times the disagreement, and that the vector is null
exactly when every cue agrees (`evid_null_iff`). A conflicting set is
time-like; the guard refuses it. But a conflicting set is also a sum of
**agreeing groups** — the cues that state one target — and each group is
null on its own (`group_disp_zero`, `group_evid_null`): a light-like vector,
one lifted point scaled by the group's weight. The majority rule reads the
conflict as a choice between those light-like pieces:

> answer the target `v` whose group holds a strict majority of the weight,
> `W < 2 · W_v`; refuse when no target does.

The analogy the owner's method asks for ([`ITERATE.md`](../ITERATE.md) §1)
is a **jury that must be more than half unanimous**: a verdict needs more
than half the votes on one answer, and the promise it makes is about the
jurors, not the answer — if more than half are honest, the verdict is right,
whatever the dishonest ones do. A plurality (the most votes wins) makes no
such promise: two colluding jurors outvote one honest juror and two
disagreeing ones.

## 2. What is proved

**[`glm_lean/RequestProject/GLM/LorentzianMajority.lean`](../glm_lean/RequestProject/GLM/LorentzianMajority.lean)**
— over `ℚ` weights, any finite index set, and targets in any type with
decidable equality (the evidence-space statements in any dimension `n`),
built on Phase 183's `LorentzianEvidence.lean`.

* `majority_unique` — with non-negative weights at most one target holds a
  strict majority, so the rule is well defined;
* `majorityRule_eq_some_iff`, `majorityRule_eq_none_iff` — the rule answers
  `v` exactly when `v` holds a strict majority, and refuses exactly when none
  does;
* `majority_never_wrong` — **the soundness condition**: if the cues stating
  the true target `d` hold at least half the weight, the rule answers nothing
  but `d`;
* `majority_sound` — strictly more than half, and it answers `d`;
* `majority_misled` — **tight**: strictly less than half, with every other
  cue stating one wrong target `e`, and it answers `e`;
* `majority_wrong_needs_decoys` — a wrong answer `v` needs cues off the true
  target weighing at least `W_v`: an answer stated by `g` of `k` unit-weight
  examples is wrong only if at least `g` of them are decoys;
* `majority_sound_count`, `majority_never_wrong_count` — unit weights:
  fewer than half the examples decoys, right; at most half, never wrong;
* `group_disp_zero`, `group_evid_null` — each agreeing group has dispersion
  0 and a null evidence vector;
* `majority_extends_guard` — when the dispersion is 0 (the guard answers the
  common target), the rule answers the same target.

The file is in `AxiomAuditAll.lean`, so the whole-development audit checks it
on the standard axioms.

The condition is the **caller's obligation**. No rule that reads only the
targets can check it: by `majority_misled`, a set with one honest example and
two agreeing decoys looks exactly like a set with two honest examples and one
decoy. What the rule can say about any one answer is the price of its being
wrong, and `tool majority` says it with every answer.

## 3. Relations over the physics register

Phase 183's surface unchanged: a relation is a displacement of EXT10
exponents from the curated physics analogies (8 relations with at least four
example pairs), its examples are register pairs stating it, a query applies
it to a register quantity, 300 queries per condition, the same seed. A
condition is *(good, colluding, independent)*: good examples of the relation,
decoys that all state one wrong relation, and decoys each stating a
different wrong relation. `decoy2` and `decoy3` make exactly Phase 183's
calls, so its figures come back.

| condition | (good, colluding, independent) | honest share | `guarded` | `vote` (plurality) | `majority` |
|---|---|---|---|---|---|
| clean1 | (1, 0, 0) | 1 | 148 / 0 / 152 | 148 / 0 / 152 | 148 / 0 / 152 |
| clean2 | (2, 0, 0) | 1 | 166 / 0 / 134 | 166 / 0 / 134 | 166 / 0 / 134 |
| clean3 | (3, 0, 0) | 1 | 146 / 0 / 154 | 146 / 0 / 154 | 146 / 0 / 154 |
| decoy2 | (1, 0, 1) | 1/2 | 0 / 0 / 300 | 0 / 0 / 300 | 0 / 0 / 300 |
| decoy3 | (2, 0, 1) | 2/3 | 0 / 0 / 300 | 155 / 0 / 145 | 155 / 0 / 145 |
| decoy4 | (2, 0, 2) | 1/2 | 0 / 0 / 300 | 149 / 0 / 151 | 0 / 0 / 300 |
| decoy5 | (3, 0, 2) | 3/5 | 0 / 0 / 300 | 161 / 0 / 139 | 161 / 0 / 139 |
| collude3 | (1, 2, 0) | 1/3 | 0 / 0 / 300 | 0 / 148 / 152 | 0 / 148 / 152 |
| collude5 | (1, 2, 2) | 1/5 | 0 / 0 / 300 | 0 / 150 / 150 | 0 / 0 / 300 |

(right / wrong / refused; a query whose target class is not in the register
should be refused.)

* **Where the honest examples are a majority** (clean, decoy3, decoy5) the
  rule is right on every query whose target is in the register and refuses
  the rest — the guard's answers on the clean sets, and 155 and 161 right
  answers the guard gave up on the decoy sets, with 0 wrong.
* **At exactly half** (decoy2, decoy4) it never answers wrong; it refuses.
* **Below half with the decoys agreeing** (collude3) it is wrong 148 times —
  exactly the 148 queries whose colluding target is a register class, as
  `majority_misled` says. The plurality vote is wrong on the same 148.
* **Below half with the decoys split** (collude5) it refuses all 300; the
  plurality vote follows the colluding pair and is wrong 150 times.

**Where it costs.** On decoy4 the plurality vote is right 149 times and the
rule 0: two honest examples against two decoys of *different* relations are
not a strict majority, though they are the largest group. The vote is right
there only because the decoys did not agree; on collude5 the same reading
(trust the largest group) is wrong 150 times. Which rule to use is a claim
about the source of the examples — whether wrong examples are independent
accidents or may agree — and the rule declared here is the one whose promise
does not depend on that. Recorded as it is.

## 4. Identities

300 random weighted target sets (points of a 3 × 3 grid, weights in
`{0, 1/2, 1, 2, 3}`, one target planted): the rule agrees with its definition
on 300 of 300; in the 229 sets where the planted target holds at least half
the weight it never answers anything else; in the 133 sets whose
positive-weight cues agree it answers their target (dispersion 0); and each of
the 40 wrong answers has decoys weighing at least its own group.

## 5. Marks

| mark | declared | result |
|---|---|---|
| M1 | honest majority (clean1–3, decoy3, decoy5): never wrong, right on every present target, refusing the rest | met |
| M2 | honest exactly half (decoy2, decoy4): never wrong | met |
| M3 | right at least as often as `guarded` everywhere, strictly more on decoy3 and decoy5 | met (155 and 161 against 0) |
| M4 | decoy3 right exactly 155 times, Phase 183's vote figure | met |
| M5 | collude3 wrong on exactly the queries whose colluding target is present, at least once | met (148 of 148) |
| M6 | collude5: refuses all 300, and the plurality vote is wrong at least once | met (vote 150 wrong) |
| M7 | identities on 300 random weighted sets | met |
| L | the Lean file, no `sorry`, audited | met |

8 of 8 marks.

## 6. What it gives the GLM's reasoning

Under the standing target ([`PROJECT_DIRECTIVES.md`](../PROJECT_DIRECTIVES.md)),
assigned as [`BLOCKERS_STUDY.md`](BLOCKERS_STUDY.md) §1 asks:

* **Address.** `tool majority` answers a relation whose examples conflict,
  when more than half agree: 155 and 161 right answers on the decoy
  conditions where `tool evidence` refuses, with the outvoted examples named.
* **Refuse.** It refuses where no strict majority exists, including the
  collude5 sets on which a plurality would be wrong 150 times; and every
  answer carries its price — *right unless at least `g` of the `k` examples
  are wrong*.
* **Derive.** Nothing new: every answer is a register class.

`tool evidence` is unchanged: it still refuses every conflict. The two tools
are two declared policies over the same evidence — refuse any disagreement,
or believe a strict majority — and the study measures both.

## 7. What this does not do, and what is next

* **The condition is not checked.** No reading-only rule can tell an honest
  majority from an agreeing set of decoys (§2); a record of where each example
  came from — the same kind of instrument as Phase 133's sender tag, which the
  27 Golay decoy errors of Phase 183 also need — is what would.
* **Independent decoys.** Where wrong examples are known to be independent,
  a plurality rule with its own condition (the honest group larger than any
  decoy group) would answer decoy4's 149; its soundness rests on a claim about
  the source that this register cannot supply. Not declared here.
* **Weights.** Every example here weighs 1; the theorems allow any
  non-negative weights (a trusted source counting more), and nothing yet
  supplies them.
* **The Golay readings.** The rule applies to readings of one message as
  well, but a Golay reading is not a target that is right or wrong as a
  whole; Phase 182's summed score already uses the readings' distances.
* **Item 11's other lines** — the evidence space on Leech-level address ties,
  holding `tool lorentz`'s five-bit question open across turns — are
  untouched.

## 8. Reproduce

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.tools lorentzian-majority          # the stored marks
PYTHONPATH=. python3 -m glm_universal.tools lorentzian-majority --write  # re-take (~10 seconds)
python3 GLM.py -q "tool majority velocity : acceleration, length : velocity, mass : density :: momentum"
python3 GLM.py -q "tool majority velocity : acceleration, mass : density :: momentum"   # refused: one against one
lake build RequestProject.GLM.LorentzianMajority
```

The mechanism is `glm_universal/reasoning/lorentzian_majority.py`,
the measurement `glm_universal/reasoning/lorentzian_majority_study.py`,
the tests `glm_universal/tests/test_lorentzian_majority.py`.
