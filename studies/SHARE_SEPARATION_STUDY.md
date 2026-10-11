# The separation criterion for the share-carrying rungs — lattice item 6

## Tier 0 — the coarse read

**Question.** Does a share-carrying rung of the deep-hole ladder reach the separation criterion `ρ = 2W/B < 1`, and what bounds the share part's seed shift?

**Verdict.** No share-carrying cell reaches the criterion: up to 30720 starts the best ratio is 2.3508, because the separation falls with the spread. The arrival shares approach a near-uniform profile, so holes with equal vertex counts converge on each other; the per-hole criterion certifies 8 of 10 holes at the joint rung and leaves exactly the two 28-vertex holes, E_6^4 and D_6^4. Sorting is proved non-expansive in L1, so the share part's seed shift is bounded by the vertex-matched shift, and that bound holds at all 80 measured instances.

**Deciding figure.** 3 of 6 marks met (H1–H3; H4–H6 missed); 16 of 16 ladder cells reproduced exactly; best share-carrying ratio 2.3508 at `(L4, 7680)`; per-hole certificate 8 of 10; 10 theorems, 0 `sorry`.

**Recomputed by.** `glm_universal.reasoning.share_separation.share_separation_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. What this document is

A **pre-registration**, committed before the modules that take the measurement
and before the Lean file exist. §§0–6 are as they were committed; §7 is what
came out.

[`STRAY_BLIND_STUDY.md`](STRAY_BLIND_STUDY.md) §3 closed lattice item 6 for the
distance-only rung `L₃`: a conflated pair of references makes the criterion
fail at every spread. It left the item open, narrowed, for the two
**share-carrying** rungs, `L₂` (arrival shares widened by the stray spectrum)
and `L₄` (`L₂` and `L₃` together), whose share part sees which vertex a start
reached and so separates `A_1^24` from `A_2^12`. At the ladder's best cell,
`(L₄, 1920)`, the ratio is `ρ = 2.5943`. The study asked for one of two things:
a rung with `ρ < 1`, or a bound on the share part's seed shift.

**Order of work, stated plainly.** The ladder's own table was read before this
was written: `ρ` at `L₄` fell from 3.2282 at 960 starts to 2.5943 at 1920. The
size rungs declared here are therefore decided *after* that trend was seen, as
the 1920 rung itself was, and they are reported as extension rungs of the
ladder, never as its pre-registered result. No emission beyond 1920 starts had
been computed when this was committed.

## 1. What is used rather than re-derived

* The ten reference holes, their centres and labels, the reference seed
  `20260825` and the sanity seed `20260826`:
  `deep_hole_escalation.reference_entries`, unchanged.
* The ensemble: `deep_hole_escalation.emissions`, unchanged. The declared
  sweep emits its starts in a fixed order, so every larger ensemble has the
  smaller ones as prefixes, and the first 1920 starts of the new ensembles
  *are* the ladder's ensembles.
* The readings and their metrics (`share_profile`, `stray_profile`,
  `rational_profile`, `layer_distance`) and the cell's statistics (`Q₀`, `W`,
  `B`, `ρ`): unchanged.

## 2. The two halves

**The bound (Lean).** The share part is a *sorted* profile: the arrival
shares in descending order, so that two holes with different vertex sets can
be compared at all. For the **same** centre under two seeds the vertices are
the same lattice points, so the two share vectors can also be compared vertex
by vertex. The theorem to prove is that sorting never increases an L1
distance: for any two vectors, the L1 distance between their descending
rearrangements is at most the L1 distance between them as given. So the share
part's seed shift is bounded by the **vertex-matched** shift: the L1 distance
between two empirical distributions on the same finite set. That is a
statement about counting alone, and it is the bound
[`STRAY_BLIND_STUDY.md`](STRAY_BLIND_STUDY.md) §4 asked for.

Beside it, a **per-hole criterion**: hole `T` is named correctly whenever its
own seed shift is less than half its distance to its nearest other reference.
That is `nearest_correct` with the worst spread replaced by `T`'s own, and it
certifies each hole on its own evidence rather than the worst hole's.

**The measurement (Python).** The ensembles extended to `N ∈ {3840, 7680,
15360, 30720}` starts at both seeds for all ten reference holes, by
`deep_hole_escalation.emissions` exactly; the readings are applied at every
prefix size of the ladder and of the extension. `20 × 30720 = 614,400` exact
decodes; the sufficient statistics (each emitted point with its exact squared
distance and its count, at every prefix size) are stored beside the digest of
the code that emitted them.

## 3. The marks, declared before the code

| mark | statement |
|---|---|
| H1 | The Lean file builds with no `sorry` and only the standard axioms, and proves (a) sorting is non-expansive in L1, (b) the share part's seed shift is at most the vertex-matched shift, and (c) the per-hole criterion. |
| H2 | **Reproduction.** At 240, 480, 960 and 1920 starts the new measurement returns the ladder's stored `Q₀`, `W`, `B` and `ρ` exactly, at all four readings. |
| H3 | **The bound holds where it is measured.** At every hole, every size and both seeds' pairing, the sorted share shift is at most the vertex-matched shift (an instance of H1(b), checked in exact arithmetic). |
| H4 | **The primary question.** Some share-carrying cell — `L₂` or `L₄`, at a size up to 30720 — has `ρ < 1`. |
| H5 | **The spread shrinks.** At `L₄`, the worst seed shift `W` falls at every doubling of `N` from 1920 to 30720. |
| H6 | **The gate holds once reached.** At `L₄`, `Q₀ = 10` at every size from 1920 to 30720. |

**What each outcome means.** H4 met answers lattice item 6 positively, at an
extension size, with the criterion's guarantee (`nearest_correct`) attached:
the cell's nearest-reference reading is then certified for every query within
`W` of its reference, not merely observed to be right on the sanity seed. H4
missed is a measured boundary at 30720 starts, and the study then reports the
smallest `ρ` reached and refuses to extrapolate past it.

**The prediction, stated as a number before it is taken.** If `W` falls as
`N^{-1/2}` and `B` stays where it is, `ρ` at `L₄` falls by `1/√2` per doubling:
from 2.5943 at 1920 to about 0.92 at 15360 and 0.65 at 30720. The ladder's last
doubling fell by 0.80 rather than 0.71; at that rate `ρ` is about 1.06 at
30720. So H4 is genuinely open when it is declared.

## 4. Controls

* **Reproduction** (H2) is the control on the code: the extension may not be
  read until the four ladder sizes come back exactly.
* **The vertex-matched shift** is reported beside the sorted one at every
  cell. It is the quantity the Lean bound says dominates the sorted shift; it
  is not a reading of the ladder (it cannot compare two holes) and no mark is
  on its size.
* **The multiplicity count.** The ladder's correction counted 20 statistics;
  these four sizes at four readings add 16 cells, and the count is reported as
  36. No bit score is computed in this round.

## 5. What this round does not do

* It does not change the reading, the holes, the seeds or the gate. A rung
  that reaches `ρ < 1` here reaches it with the ladder's own statistic.
* It does not extrapolate past 30720 starts, in either direction.
* It does not re-open the `L₃` rung, which Phase 110 settled.
* It says nothing about the thirteen Niemeier types the ensemble does not
  reach (lattice item 7) or the empty norms (item 3).

## 6. Files

* `RequestProject/GLM/ShareSeparation.lean` — H1.
* `overlay/glm_universal/reasoning/share_ensemble.py` — the extended ensembles
  and their stored sufficient statistics.
* `overlay/glm_universal/reasoning/share_separation.py` — the readings and the
  report, computed from the stored statistics.
* `python3 -m glm_universal.tools share-separation` — the report;
  `share-ensemble --write` re-takes the ensembles.
* `overlay/glm_universal/tests/test_share_separation.py`.

## 7. The measurement

*Written after the measurement. §§0–6 above are as they were committed.*

The ensembles were taken once (`python3 -m glm_universal.tools share-ensemble
--write`: 614,400 exact decodes, about 70 minutes on eight cores) and the
readings applied to them (`tools share-separation`, about fifteen seconds).

### 7.1 The verdict

No share-carrying cell reaches the criterion: up to 30720 starts the best ratio is 2.3508, because the separation falls with the spread. The arrival shares approach a near-uniform profile, so holes with equal vertex counts converge on each other; the per-hole criterion certifies 8 of 10 holes at the joint rung and leaves exactly the two 28-vertex holes, E_6^4 and D_6^4. Sorting is proved non-expansive in L1, so the share part's seed shift is bounded by the vertex-matched shift, and that bound holds at all 80 measured instances.

### 7.2 The marks

| mark | statement | result |
|---|---|---|
| H1 | the Lean file, no `sorry`, standard axioms | **met**: `RequestProject/GLM/ShareSeparation.lean`, 10 theorems; `#print axioms` shows `propext`, `Classical.choice`, `Quot.sound` only |
| H2 | the ladder reproduced at 240–1920 starts | **met**: 16 of 16 cells, `Q₀`, `W`, `B` and `ρ` equal exactly |
| H3 | sorted share shift ≤ vertex-matched shift | **met**: 80 of 80 instances (10 holes × 8 sizes), shares and stray spectra both |
| H4 | some `L₂`/`L₄` cell with `ρ < 1` | **missed**: the least ratio is 2.3508, at `(L₄, 7680)` |
| H5 | `W` at `L₄` falls at every doubling from 1920 | **missed**: 0.0465, 0.0539, 0.0291, 0.0277, 0.0192 — it rose once, at 3840 |
| H6 | `Q₀ = 10` at `L₄` from 1920 on | **missed**: 10, 9, 9, 9, 10 at 1920, 3840, 7680, 15360, 30720 |

### 7.3 The share-carrying cells at the extension sizes

| reading | starts | `Q₀` | `W` | `B` | `ρ` | per-hole certified |
|---|---|---|---|---|---|---|
| L2 | 1920 | 9 / 10 | 0.0424 | 0.0297 | 2.8520 | 6 / 10 |
| L2 | 3840 | 8 / 10 | 0.0453 | 0.0281 | 3.2234 | 5 / 10 |
| L2 | 7680 | 8 / 10 | 0.0238 | 0.0181 | 2.6273 | 6 / 10 |
| L2 | 15360 | 8 / 10 | 0.0252 | 0.0109 | 4.6467 | 6 / 10 |
| L2 | 30720 | 10 / 10 | 0.0162 | 0.0077 | 4.2003 | 6 / 10 |
| L4 | 1920 | 10 / 10 | 0.0465 | 0.0358 | 2.5943 | 6 / 10 |
| L4 | 3840 | 9 / 10 | 0.0539 | 0.0344 | 3.1343 | 5 / 10 |
| L4 | 7680 | 9 / 10 | 0.0291 | 0.0248 | 2.3508 | 7 / 10 |
| L4 | 15360 | 9 / 10 | 0.0277 | 0.0183 | 3.0359 | 8 / 10 |
| L4 | 30720 | 10 / 10 | 0.0192 | 0.0158 | 2.4231 | 8 / 10 |

The full table, all four readings at all eight sizes, is the output of
`tools share-separation`; the shares alone (`L₁`) never fall below a ratio of
2.75 and the distance-only reading (`L₃`) still has `B = 0`, as Phase 110
proved it must while `A_1^24` and `A_2^12` stay stray-free.

### 7.4 Why the ratio does not fall: the separation shrinks with the spread

The prediction of §3 assumed that `B` stays where it is while `W` falls. It
does not. At `L₄`, `B` fell from 0.0358 at 1920 starts to 0.0158 at 30720,
and the closest pair of references from 3840 on is always `E_6^4`/`D_6^4`.
The reason is visible in the profiles. The starts sit in a cube of half-width
1/4 around the centre, far inside the covering radius 4, so the share of each
vertex tends to the fraction of that small cube in the vertex's Voronoi cone,
and those fractions are close to equal: at 30720 starts every hole's shares
lie within a few thousandths of `1/k` for its vertex count `k` (48 for
`A_1^24`, 36 for `A_2^12`, 25 to 28 for the rest). A sorted profile then
mostly reads the vertex count, and two holes with the same count can only be
told apart by the small departures from uniform. Three holes have 27
vertices (`E_8^3`, `D_8^3`, `D_10 E_7^2`), two have 28 (`E_6^4`, `D_6^4`) and
two have 26 (`A_12^2`, `D_16 E_8`). At all 8 share-carrying cells of the
extension sizes the closest pair of references has equal vertex counts.

So both the spread and the separation of the equal-count pairs are, at these
sizes, of the order of the sampling fluctuation, and the ratio stays between
2.35 and 3.14 at `L₄`. Whether the 28-vertex pair's limit profiles differ at
all — whether `B` levels off above zero, so that some much larger ensemble
would reach `ρ < 1` — is not decided by these figures: `B` fell more slowly
than `N^{-1/2}` from 7680 to 30720 starts (0.0248 to 0.0158 against the 0.0124
that pure fluctuation would give), which is consistent with a positive limit,
and the study refuses to extrapolate it.

### 7.5 What the per-hole criterion does certify

`nearest_correct_local` certifies a hole on its own evidence. At `(L₄, 15360)`
and `(L₄, 30720)` it certifies 8 of the 10 holes, and the two it leaves are
exactly the 28-vertex pair: at 30720 starts their references are 0.0158 apart
and each moves by about 0.015 under a seed change, so the per-hole ratios are
1.85 and 1.91. The other eight have per-hole ratios between 0.054
(`A_1^24`) and 0.97 (`D_8^3`). For those eight the rung's nearest-reference
reading is now *certified* — correct for every query within the hole's own
measured spread, by the theorem rather than by the sanity seed. Lattice item
6 is therefore narrowed again: from the whole share-carrying family to one
pair of holes with equal vertex counts.

### 7.6 The gate that was passed at 1920 starts

The escalation study recorded that the gate `Q₀ = 10` was first reached at
`(L₄, 1920)`, an extension cell. The larger ensembles show that this was not
stable: `Q₀` is 9 at 3840, 7680 and 15360 starts (the hole that fails is
`D_6^4`, whose nearest other reference is `E_6^4`'s) and 10 again at 30720. A gate passed
on the sanity seed without the criterion behind it is an observation, which
is exactly why the study measures `ρ`; [`DEEP_HOLE_ESCALATION_STUDY.md`](DEEP_HOLE_ESCALATION_STUDY.md)
now carries a pointer to this section.

### 7.7 The bound

`share_shift_le_matched` is the bound Phase 110 asked for. Measured, the
vertex-matched shift is much larger than the sorted one (at 30720 starts the
matched share shift is between 2.6 and 6.1 times the sorted one at every hole —
0.0480 against 0.0107 for `A_1^24`), so the bound is
valid and loose: sorting removes most of the fluctuation that the vertex
identities carry, which is why the sorted profile was the right statistic to
compare holes with — and also why, once every vertex is near `1/k`, it has
little left to compare.

### 7.8 What is left

* **The 28-vertex pair.** A reading that separates `E_6^4` from `D_6^4`
  without sorting the vertex identity away: their vertex sets have different
  shapes (four `E_6` against four `D_6` components), which a profile of the
  vertex *configuration* — inner products between the vertices reached,
  weighted by share — would see and a sorted list of shares cannot.
  *Taken by Phase 122* ([`CONFIGURATION_READING_STUDY.md`](CONFIGURATION_READING_STUDY.md)):
  the configuration reading `L₅` certifies the pair, and every other hole,
  with `ρ = 0.1261` at 30720 starts.
* **Whether `B` has a positive limit** for the equal-count pairs, which no
  ensemble here decides.
* **The multiplicity count** is now 36 statistics; no bit score is computed.
