# Second readings: a framed register that reads one carrier through several views

## Tier 0 — the coarse read

**Question.** Can the runtime itself produce a second, independent view of one stored carrier, so that the deep-hole fork is resolved by a routine second reading rather than by a read the caller supplies; does the composition of the declared cases and a second reading hold on a fresh probe; and does a Leech escalation on a soft channel built from the machine's own readings add anything?

**Verdict.** Partly: the framed register reads one carrier through its own views, and three views resolve every common-mode four-error burst with 0 wrong. The composition of the declared cases and a second reading holds on a fresh probe. Escalating to the Leech lattice on the views' own soft reading adds nothing, and that is proved. Seven of the nine declared marks were met: V4 (X1's probe through two views) resolved 4,160 of 4,224, and V8 refused one declared program because the dialect has no argument unpacking.

**Deciding figure.** 680,064 of 680,064 three-view reads resolved, 0 wrong; 658,258 of 658,812 composed reads answered, 0 wrong, open count as predicted at every `k`; 0 forks resolved by the escalation beyond the intersection in 46,728 reads; 7 of 9 marks met.

**Recomputed by.** `glm_universal.runtime.second_view_report.second_view_full_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

Round 8 of the order of work in [`ROADMAP_STUDY.md`](ROADMAP_STUDY.md) and
[`STATUS.md`](../STATUS.md) §3.4, *second readings*: J2 with H's X1, then J1,
then J3. All three are named in [`CARRIED_FORK_STUDY.md`](CARRIED_FORK_STUDY.md)
§6:

1. **J1, a declared composition mark.** Phase 65 resolved 35,872 of the 48,320
   forks the declared cases left open at `k = 32` by carrying them to a second
   read, 0 wrong — post hoc, so reported and not scored.
2. **J2 (with H's X1), a second view of one carrier at runtime.** X1's second
   reading answered 4,224 of 4,224 double reads, and Phase 65 wired it into the
   dialect as `agree`; but only a caller who already holds two reads can use
   it. What would make it routine is a runtime path that produces two
   independent views of one stored value.
3. **J3, a soft channel worth escalating.** K4b's soft ensemble came from a
   declared formula; the honest test of the Leech lift is a channel whose
   reliabilities come from the machine's own readings. Phase 82
   ([`RATE_POSTERIOR_STUDY.md`](RATE_POSTERIOR_STUDY.md)) made the rate itself
   a posterior over the machine's reads.

The lattice items 3, 6, 7 and 10 of §3.4, which sit beside this track, are not
taken by this round.

## 1. The object: a framed register

A **framed register** stores one Golay codeword `c` in several **views**. View
`k` stores `c` rotated down by `k` coordinates (package order, cyclic); it is
read back by rotating up by `k`. The declared frames are `k ∈ {0, 1, 3}`.

A **common-mode burst** `e` is an error that lands on the same stored
positions of every view — the fault model in which a second copy is worth
least, because a plain duplicate would read the same wrong word twice. Read
back through view `k`, the burst becomes the error `rot(e, k)`: the frames are
what make the views differ. An **independent** fault gives each view its own
error, which is X1's model.

A read of the register carries the fork of view 0 and prunes it by the fork of
every further view: the second-reading stage of Phase 65, with the reason
naming the frame. Nothing is chosen by order; a fork is resolved when one
candidate survives, open when several do, contradicted when none does.

**Why the frames should work — the structure the marks are declared from.**
For a codeword `c` and a weight-4 error `e`, every codeword at distance 4 from
`c ⊕ e` is `c` itself or `c ⊕ o` for an octad `o ⊇ e` (five of them, since
four points lie in exactly five octads). So the codewords every view allows
are `c` and the `c ⊕ o` for octads `o` containing the union of the errors the
views read. Hence:

* two views resolve a burst exactly when no octad contains `e ∪ rot(e, 1)`,
  and a burst that leaves one octad leaves exactly two live candidates;
* no single second frame — no permutation of the 24 coordinates whatever —
  can resolve every burst, because some four-set always meets its image in
  three points, and any five points lie in an octad;
* three views resolve every burst exactly when no octad contains
  `e ∪ rot(e, 1) ∪ rot(e, 3)` for any of the 10,626 four-sets.

**The scoping search, reported as such.** The frames were chosen by a search,
run before this declaration, that counted the bursts leaving an octad through
the union: one second frame at offset 1 leaves 174 of 10,626; the frames
`(0, 1, 3)` leave none; their mirror `(0, −1, −3)` leaves 2. These figures
are what the frames were chosen on; they are not results of the round, and
`evaluation/second_view_cases.py` records them under `SCOPED`.

## 2. Declarations — written before any code of the round

Every probe is a fixed stride or a full census; no random source (D7). The
codeword probe is X1's: the 64 codewords at stride 64 through the sorted
4,096. The bursts are all 10,626 four-sets unless a mark says otherwise.

**V1 — two views: the live count is predicted.** For every probe codeword and
every weight-4 common-mode burst, the two-view register (frames `0, 1`)
leaves exactly `1 + |{octads ⊇ e ∪ rot(e, 1)}|` live candidates, the truth
among them; 0 wrong. The resolved count is reported.

**V2 — three views resolve every common-mode burst.** For every probe
codeword and every weight-4 common-mode burst, the three-view register
answers, and answers the truth: 680,064 of 680,064, 0 wrong.

**V3 — one second frame never suffices.** For each single second frame
`k = 1, …, 23`, the number of weight-4 common-mode bursts the two-view
register leaves open is positive. Lean states it for every permutation.

**V4 — X1 through the register.** X1's probe (64 codewords, 12 weight-4
errors) read through the two-view register with independent faults — view 0
reads error `e_i`, view 1 error `e_j`, `i ≠ j` — answers 4,224 of 4,224, 0
wrong, as X1 and Phase 65's K2 did when the caller supplied the reads.

**V5 — inside the packing radius.** Every common-mode burst of weight at
most 3 (2,325 of them) on every probe codeword is answered, and answered
right, by the two- and three-view registers.

*Reported, not a mark:* common-mode bursts of weight 5 on the probe codewords,
outside the declared fault model: how many the single view, the two-view and
the three-view register answer, answer wrongly, refuse as open and refuse as
contradicted.

**V6 — J1, the composition, on a fresh probe.** Case sets `S'_k` are the
codewords at indices `2 + j·⌊4096/k⌋`, `j < k`, for `k ∈ {2, 4, 8, 16, 32}`
(Phase 65's K1 began at index 1, so no set is shared). For every case `c` and
every weight-4 error `e`, the read `c ⊕ e` is carried, pruned to the declared
cases (the context stage, closed world named), and then by the second view
of the two-view register under the same burst. *Marks:* **0 wrong**; the
number left open equals, exactly, the number of pairs `(c, e)` for which some
other declared case `c'` has `c ⊕ c'` an octad containing `e ∪ rot(e, 1)`;
and at least **99 %** of the reads answered at every `k`. The context stage
alone is reported beside it.

**V7 — J3, the soft channel of the views.** The machine's own soft reading of
a carrier is the mean of its aligned views, coordinate by coordinate: `1` or
`0` where the views agree, `1/2` where two views disagree. The Leech
escalation of Phase 65 (`carried_fork.escalate`, the hole vertices nearest the
lifted reading) is applied to the fork of view 0 with that reading. *Mark:*
on every two-view read of V1 and V4 and every three-view read of V2, the
escalation's nearest candidates are exactly the candidates the intersection
leaves live — so the escalation resolves no fork the second reading leaves
open, and contradicts none it resolves. (The escalation costs about 5 ms a
read, so V1 and V2 enter V7 on their first two probe codewords: 21,252
two-view and 21,252 three-view reads, beside V4's 4,224.) Declared from two identities: the
squared distance from the mean of two views to a codeword is half the sum of
the two view distances minus a quarter of the views' disagreement, and the
sum of the two view distances is at least 8 on a burst, with equality exactly
on the live candidates. *Also marked:* at every rate of Phase 82's grid `G`,
the pair likelihood `p^D (1 − p)^(48 − D)` ranks the fork as `D` does, so the
rate posterior cannot change which candidates the soft reading prefers.

**V8 — the dialect.** Two builtins: `store_views(c)` returns the three stored
words of a codeword, and `read_views(*views)` reads one to three views in
frame order. Every program of `DIALECT_CASES` equals CPython with the prelude
in type and value, its column-3 script verifies in a fresh `python3 -I`, and
a mutated script is rejected; every program of `DIALECT_REFUSALS` is refused
by the declared name.

**V9 — no regression.** The carried-fork figures of Phase 65 and the Python
speech cases are unchanged.

**What would count as moving the target (D15).** V2 and V4 move **address**:
the second reading becomes a path the runtime takes on its own. V1, V3 and
V5's report sharpen **refusal**. V6 moves **refusal → derivation** for the
deep hole under the closed world, now as a declared mark. V7 moves nothing if
it is met — it would say, with a proof, that the Leech lift adds no
information on the machine's own soft channel.

## 3. What was built

* **`reasoning/second_view.py`** — the framed register: `rot`, `store_views`,
  `align`, `read_views` (the fork of view 0 pruned by every further view, each
  elimination naming its frame), `soft_mean` (the views' own soft reading),
  the `FramedRegister` object with common-mode and independent fault
  injection, and the measurements V1–V7 with the weight-5 report.
* **The dialect** gains `store_views(c)` and `read_views(*views)`
  (`reasoning/python_substrate.py`, `reasoning/python_speech.py`), each
  answered as a Three Column payload whose column-3 script re-derives it in a
  fresh `python3 -I`, and each refusing by name (`OUTSIDE_SUBSTRATE`,
  `PYTHON_ERROR`, `AMBIGUOUS`, `UNCORRECTABLE`).
* **`runtime/second_view_report.py`** adds V8 and V9;
  `python3 -m glm_universal.tools second-view` prints everything (`--json`,
  `--quick`); `tests/test_second_view.py` holds the facts at the sampled scale.
* **`RequestProject/GLM/SecondView.lean`** — §5.

## 4. Results

Every figure is recomputed by `python3 -m glm_universal.tools second-view`.
**Seven of the nine declared marks were met** (V1, V2, V3, V5, V6, V7, V9);
**two were not** (V4, V8). The round is therefore met partly. No certified stage gave a wrong answer anywhere.

| mark | declared | measured | |
|---|---|---|---|
| V1 | live count `1 + |octads ⊇ e ∪ rot(e,1)|` on every read, 0 wrong | 680,064 reads, 0 off the prediction, 0 wrong; 668,928 resolved, 11,136 open (174 bursts × 64 codewords, each with exactly 2 live) | met |
| V2 | three views: every burst answered right | 680,064 of 680,064, 0 wrong | met |
| V3 | every single second frame leaves a burst open | open bursts by offset `k = 1..23`: least 156 (`k = 6, 18`), most 1,026 (`k = 12`) | met |
| V4 | X1's probe, two views, independent faults: 4,224 of 4,224 | 4,160 resolved, 64 open, 0 wrong | **not met** |
| V5 | every burst of weight ≤ 3 answered right | 148,800 of 148,800 (two views) and 148,800 of 148,800 (three) | met |
| V6 | composition on a fresh probe: 0 wrong, open as predicted, ≥ 99 % | 658,258 of 658,812, 0 wrong, open = predicted at every `k`, least share 99.89 % (`k = 32`) | met |
| V7 | escalation = intersection; rate ranking = `D` ranking | 46,728 of 46,728 reads both; 0 forks resolved beyond the intersection | met |
| V8 | 6 programs and 3 refusals as declared | 5 of 6 programs (equal to CPython, scripts verified, mutants rejected); 3 of 3 refusals | **not met** |
| V9 | Phase 65's K2 unchanged | 4,224 of 4,224, 0 wrong | met |

### 4.1 J2 and X1 — the second view, produced by the register

**Two views (V1, V3).** The two-view register resolves 10,452 of the 10,626
common-mode four-error bursts on every probe codeword and leaves 174 open,
each with exactly two live candidates — the truth and the truth plus the one
octad through `e ∪ rot(e, 1)` — and the live count equals the prediction on
all 680,064 reads. That 174 is also a theorem
(`GLM.SecondView.pair_frame_open_count`). No single second frame does better
than leave 156 open among the 23 rotations, and
`GLM.SecondView.no_single_frame_separates` says no permutation whatever can
leave none.

**Three views (V2).** The frames `(0, 1, 3)` resolve all 680,064 common-mode
reads with 0 wrong: the second reading is now a path the runtime takes on its
own, with no read supplied by the caller. `GLM.SecondView.three_frames_separate`
proves that no octad contains `e ∪ (e + 1) ∪ (e + 3)` for any four-set, so
the census is a consequence of a theorem rather than a sample of one.

**Independent faults (V4): not met.** X1's probe read through the two-view
register answers 4,160 of 4,224, 0 wrong, and leaves 64 open — one pair of
X1's twelve errors on each of the 64 codewords. The declaration expected the
register to reproduce X1's figure, but the register's second view does not
read X1's second error: it reads that error rotated by one, and for the pair
`(e₃, e₈)` of the declared list the union `e₃ ∪ rot(e₈, 1)` lies in an octad.
So the mark was declared on a false analogy and is missed as declared. *Post
hoc, not a mark:* through all three views, each with its own error, every
triple of the twelve on every probe codeword is resolved, 14,080 of 14,080,
0 wrong.

**Outside the fault model (reported, not a mark).** On common-mode bursts of
weight 5, a single view answers all 2,720,256 reads and every answer is
wrong, because a five-error read lies within three of another codeword. The two-view register answers 384 of
them, all wrong, and refuses the rest because the views contradict each other. The three-view register answers none and
refuses all 2,720,256. Moving from one view to three takes the wrong answers
on this ensemble from 2,720,256 to 0, at the cost of a refusal on every read.
That moves **refusal**.

### 4.2 J1 — the composition, declared and met

On the fresh case sets `S'_k` (offset 2), the context stage alone answers
the same shares K1 measured (21,112, 41,676, 81,256, 156,512, 291,712). Adding
the register's second view under the same burst leaves open exactly the
reads the theorem predicts — 2, 8, 32, 128 and 384 — and answers the rest
with 0 wrong: 658,258 of 658,812 in all, 99.89 % at `k = 32` where the
context stage alone reached 85.8 %. Phase 65's post-hoc composition is now a
declared mark, met on a probe it never saw.

### 4.3 J3 — the Leech escalation on the machine's own soft channel

On every read of the three probes (21,252 two-view, 21,252 three-view and
X1's 4,224), the Leech escalation of Phase 65 applied to the fork of view 0
with the views' mean as its soft reading picks exactly the candidates the
intersection leaves live. It resolves nothing the second reading leaves open,
and it contradicts nothing the second reading resolves. At every rate of
Phase 82's grid the pair likelihood ranks the fork as the summed view
distance does. This is what the declaration predicted from the theorems of
§5. The squared distance from the mean of two views to a word is half the
summed view distance minus a constant of the read (`soft_mean_dist`). The
summed distance is at least 8, with equality exactly on the codewords both
forks allow (`pair_dist_eq_iff`). The likelihood at any rate below one half
is strictly decreasing in that sum (`pair_likelihood_strictAnti`). So on a
soft channel built only from the machine's own views, the Leech lift adds no
information, as a theorem: the two survivors of an open fork are at equal
distance from every view. J3's question is answered in the negative and
closed. A soft channel that could help would need reliabilities from outside
the views.

### 4.4 The dialect (V8): not met as declared

Five of the six declared programs are answered equal to CPython, every
column-3 script verifies, and every mutated script is rejected. The three
declared refusals are given by name. The sixth, `views-clean`, writes
`read_views(*store_views(...))`, and the dialect has never admitted argument
unpacking (`UNSUPPORTED`). The declaration assumed a construct the dialect
does not have, so the mark is missed as declared. The dialect was not widened
to meet it.

## 5. What is proved rather than measured

`RequestProject/GLM/SecondView.lean` builds with no `sorry`. Its finite
checks (`frameUnion_check`, `pairUnion_check`) are discharged by
`native_decide`, as `Golay/Sextet.lean` already does, so beyond the standard
axioms they rest on the compiler (`Lean.ofReduceBool`). The rest depends only
on the standard axioms, apart from what it inherits from the Golay
development.

* `dist_ge_four`, `dist_eq_four_iff` — every codeword is at distance at least
  4 from a four-error read `c ∆ e`, and exactly `c` and the `c ∆ o` with `o`
  an octad through `e` are at distance 4.
* `common_iff`, `resolved_iff`, `five_leaves_one`, `through_eq_empty_of_nine`
  — two views allow exactly `c` and the `c ∆ o` with `o ⊇ e ∪ f`, resolve
  exactly when no octad contains the union, leave one octad when the errors
  share three points, and always resolve when the union has nine points.
* `pair_dist_ge`, `pair_dist_eq_iff`, `soft_mean_dist`,
  `pair_likelihood_strictAnti` — the soft channel of the views is the second
  reading (§4.3).
* `no_single_frame_separates` — for every permutation of the 24 coordinates
  some burst stays open under a single second frame.
* `three_frames_separate`, `pair_frame_open_count`, `noOctadAbove_iff` — the
  frames `(0, 1, 3)` separate every burst; one frame at offset 1 leaves
  exactly 174.

## 6. Limits, and what the round leaves

* **The fault model is declared.** A common-mode burst of weight 4, or an
  independent weight-4 error per view, is the model every certificate quotes;
  weight 5 is reported outside it.
* **Which register values are framed is the caller's choice.** The register
  is reachable from the dialect and from `FramedRegister`. No existing
  register of the machine (the element register, the migration state) has
  been rewritten to store its values in frames. That would be the next step if the owner wants
  the second reading on by default.
* **J3 is closed in the negative.** A soft channel worth escalating needs
  reliabilities from outside the views (a physical channel model, or a second
  instrument), and nothing in the repository supplies one.
* **The lattice items 3, 6, 7 and 10** of `STATUS.md` §3.4, which sit beside
  this track, were not taken by this round and remain open as named.

## 7. Re-running it

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.tools second-view            # every mark, about 8 minutes
PYTHONPATH=. python3 -m glm_universal.tools second-view --quick    # one probe codeword
PYTHONPATH=. python3 -m unittest glm_universal.tests.test_second_view
lake build RequestProject.GLM.SecondView                            # from the repository root
```
