# The search loop, retrieved from the archive's ARC generations

**What this document is.**
[`SOURCE_SALVAGE_AUDIT.md`](SOURCE_SALVAGE_AUDIT.md) read the archive area by
area for *exact claims* — counts, identities, bounds — and closed
`arc_agi_15/` with "kept as a record": its one piece of new mathematics was the
topological mass `M(N) = ⌊N/2⌋ − φ(N)/2`, which `Totient.lean` already proves,
and everything else in it was a solve rate on fifty tasks, which is not a claim
about anything the current system runs on.

That reading was right about the numbers and incomplete about the folder,
because `arc_agi_15/METHODS_TRIED.md` is not a table of numbers. It is a ledger
of *methods*, and its three surviving verdicts are a procedure:

| the ledger's row | what it says |
| --- | --- |
| **D1**, the hard gate | a candidate is kept only if it reproduces every observed example exactly — "the ONLY reliable filter", "non-negotiable" |
| **D2**, the soft gate | accepting on a coherence score is "catastrophic — accepts wrong candidates"; "drop, never use" |
| **C5**, Occam | among the survivors take the cheapest description, because "all coherence-based rankers conflate stability with correctness" |

A procedure is retrievable in exactly the way a number is: state it for an
arbitrary candidate set, prove what it guarantees, and *measure* what it leaves
undetermined. This study is that, and the measurement is the part the archive
never had.

The formal half is
[`RequestProject/GLM/SearchLoop.lean`](../RequestProject/GLM/SearchLoop.lean),
the computational half is `glm_universal.reasoning.search_loop`, the test that
pins the two against each other is
`overlay/glm_universal/tests/test_search_loop.py`, and the report prints with

```bash
cd overlay
PYTHONPATH=. python3 GLM.py -q "report searchloop" --verify-tct
```

whose third column re-derives every figure below in a fresh interpreter
(`VERIFIED True`).

---

## 1. The loop, proved

Write `sem h : α → β` for what candidate `h` computes, and let an observation
be an input paired with the output that was seen. The hard gate is

```
survivors sem H obs = { h ∈ H | ∀ (a, b) ∈ obs, sem h a = b }
```

and that one definition carries the whole of the ledger's procedure:

| statement | what it says | Lean |
| --- | --- | --- |
| soundness | whatever produced the observations is never discarded | `gate_sound` |
| looping = batching | filtering by `o₁` then `o₂` is filtering by `o₁ ++ o₂`, so an incremental loop and a single pass agree exactly | `survivors_append` |
| monotonicity | more observations only ever remove candidates | `survivors_antitone`, `card_survivors_le` |
| idempotence | re-filtering by the same observations changes nothing | `survivors_idem` |
| termination | a descending chain of candidate sets reaches a fixed point in at most `#H` productive rounds | `loop_stabilises` |
| separation | a candidate computing a different function can always be refuted by one further observation, and the truth survives it | `separating_observation` |
| completeness | observing every input leaves exactly the candidates that compute the same function — never fewer, never more | `full_information` |

Two of these are the ones worth stating aloud, because they are why the
ledger's C5 is *forced* rather than chosen.

**The gate is blind to its own residue** (`gate_blind`). Any two survivors
agree on every observed input. So no quantity computed from the observed
behaviour — no coherence score, no NRCI, no energy — can separate them: they
are, by construction, indistinguishable to the data. A tie-break must come from
outside the data, and "the shortest description" is the honest default because
it does not pretend otherwise.

**A score without a gate is unsound** (`score_gate_unsound`). Two candidates
over one bit, one observation, and a score that prefers the candidate the
observation has already refuted. Four lines, and it is exactly the failure the
ledger records under D2.

**Occam is well defined** (`occam_unique`). If the description cost is
injective on the survivors there is exactly one cheapest survivor, so the
loop's answer is determined rather than picked.

---

## 2. What the gate leaves, when the candidates are symmetries

The archive's geometric operators — rotate, flip, transpose and their
composites — are a group acting on the data, and in that case the residue has a
name.

* **The survivors of one example are a coset of the stabiliser of its input**
  (`symSurvivors_eq_coset`), so exactly `|Stab g|` candidates survive, whatever
  the observed output was (`card_symSurvivors`), and that number divides the
  number of candidates (`card_stabF_dvd`, Lagrange).
* **The ambiguity of the answer is an orbit.** What a solver cares about is not
  how many candidates survive but how many different answers they give on a
  fresh input `t`, and that set is the orbit of `t` under `Stab g`
  (`card_predictions_eq_orbit`). Its size divides the number of survivors
  (`card_predictions_dvd_card_stab`), and it is **1** exactly when every
  symmetry of the example is also a symmetry of the question
  (`predictions_card_eq_one_iff`).

That last equivalence is the useful one: it says when one example is *enough*,
in terms of the data rather than the search.

---

## 3. The census

The instance is the smallest one the archive's own solvers ran on: the eight
symmetries of the square acting on `3 × 3` binary grids. A grid is one of the
`2⁹ = 512` bitmasks, a candidate is one of the eight symmetries, and the
`d4_closed` and `d4_faithful` theorems check that the eight tables really are
eight distinct permutations closed under composition.

**What one example leaves** (`stab_census`, `stab_total`, `burnside_orbits`):

| survivors | 1 | 2 | 4 | 8 |
| --- | --- | --- | --- | --- |
| grids | 288 | 200 | 16 | 8 |

The total is `816 = 8 · 102`, so by Burnside the 512 grids fall into **102
orbits** and the mean number of survivors of one example is `816/512 = 51/32 ≈
1.59`. More than half the grids pin the candidate down on their own; the rest
are the symmetric ones, and the more symmetric the example the less it says.

**What that leaves undetermined** (`ambiguity_census`, `ambiguity_total`), over
all `512 · 512 = 262,144` pairs of (example, question):

| distinct answers | 1 | 2 | 4 | 8 |
| --- | --- | --- | --- | --- |
| pairs | 160,320 | 91,776 | 7,744 | 2,304 |

The answer is determined in `160,320` pairs — `2505/4096`, just over three
fifths — the mean number of distinct answers is `393280/262144 = 6145/4096 ≈
1.50`, and every entry of the census is a power of two dividing eight, which is
§2's divisibility checked on every pair (`ambiguity_dvd_stab`). The criterion
of §2 is checked on every pair too (`ambiguity_eq_one_iff`): the answer is
unique exactly where every symmetry of the example fixes the question.

**What a second example buys** (`second_example_census`). Two examples leave
the candidates fixing both, so the survivor count is `|Stab g₁ ∩ Stab g₂|`:

| survivors | 1 | 2 | 4 | 8 |
| --- | --- | --- | --- | --- |
| ordered pairs of examples | 245,760 | 15,936 | 384 | 64 |

against `147,456 / 102,400 / 8,192 / 4,096` for a single example scaled to the
same total. The second example closes about two thirds of what the first left
open — `245,760` against `147,456` — and the mean survivor count falls from
`51/32` to `2185/2048 ≈ 1.07`. The loop is worth running; it is also nearly
finished after two rounds, which is what the ledger's practice of "verify on
every train pair" was already doing.

---

## 4. The counts, in one place

| quantity | value | Lean | Python |
| --- | --- | --- | --- |
| grids | 512 | `gridsN` | `GRIDS` |
| candidates | 8 | `d4Table` | `GROUP_ORDER` |
| the eight tables are a closed, faithful group | yes | `d4_closed`, `d4_faithful` | `group_is_closed`, `group_is_faithful` |
| survivors of one example | `|Stab g|` | `survivorsN_card_eq_stabCard` | `survivors` |
| stabiliser census | 288, 200, 16, 8 | `stab_census` | `stabiliser_census` |
| its total | 816 | `stab_total` | `stabiliser_census` |
| orbits, by Burnside | 102 | `burnside_orbits` | `orbit_count` |
| mean survivors | 51/32 | — | `mean_survivors` |
| pairs walked | 262,144 | `ambiguity_census_total` | `ambiguity_census` |
| ambiguity census | 160320, 91776, 7744, 2304 | `ambiguity_census` | `ambiguity_census` |
| total ambiguity | 393,280 | `ambiguity_total` | `ambiguity_census` |
| mean ambiguity | 6145/4096 | — | `mean_ambiguity` |
| determined fraction | 2505/4096 | — | `determined_fraction` |
| every ambiguity divides eight | yes | `ambiguity_dvd_stab` | `search_loop_report` |
| unique answer ⟺ question fixed | yes | `ambiguity_eq_one_iff`, `predictions_card_eq_one_iff` | `ambiguity` |
| two examples pin the candidate | 245,760 of 262,144 | — | `second_example_census` |
| one example pins the candidate | 147,456 of 262,144 | — | `second_example_census` |
| mean survivors after two | 2185/2048 | — | `second_example_census` |

---

## 5. What this changes, and what it does not

**It does not retrieve a solve rate.** The archive's `9/50` is a measurement of
a program on a task set neither of which is carried here, and nothing in this
study says anything about it. What is retrieved is the *shape* of the search
the ledger converged on, and the exact price of the ambiguity that shape leaves
behind.

**It does say what a loop in this system may and may not claim.** Three things
follow directly, and each is a statement about any future loop, not only about
grids:

1. *Filtering may be incremental without loss.* `survivors_append` says a loop
   that consumes observations one at a time reaches exactly the set a batch
   would, so a loop is a scheduling choice and never a semantic one.
2. *A loop may stop when the candidate set stops moving,* and it does so after
   at most `#H` productive rounds (`loop_stabilises`); on the census instance
   two rounds already leave 245,760 of 262,144 pairs with a single candidate.
3. *A loop may not rank its survivors by anything it read from the data*
   (`gate_blind`). If a tie-break is wanted it must be declared, like the
   description cost of `occam_unique`, and reported as a choice.

The third is the one this project's own directives already say in another form:
D3 forbids a digest from carrying meaning, and this forbids a score from
carrying information the data does not contain. Both are the same rule against
a number that looks like evidence and is not — and
[`ARCHIVE_DEEP_DIVE_STUDY.md`](ARCHIVE_DEEP_DIVE_STUDY.md) §1 is the worked
example of what happens when one is trusted.

**What is still open here.** The census is one group on one grid size, chosen
because it is the smallest instance the archive itself used and because it can
be walked exhaustively in both halves. What a *larger* candidate set does — the
archive's 162 DSL operators, of which its ledger says only about twenty ever
win — is a different question, and the honest answer is that the ledger's
"about twenty" is not a count anybody can reproduce from what the archive
carries. It is recorded here as unretrieved, for the same reason the chemistry
correlations are.
