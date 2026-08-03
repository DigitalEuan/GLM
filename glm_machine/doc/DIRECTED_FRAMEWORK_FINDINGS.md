# Directed Framework Test — Findings (v3.16.0)

## Question
Can a hand-designed, step-by-step curriculum of chat() queries — deliberately
co-occurring a target word with a *chosen*, semantically-related partner set —
drive GLM24's continuous learner to produce a more coherent representation of
that word than the same volume of *undirected* (random-partner) reinforcement?

## Method
- Target word: `river` (`ubp_id=MR_river`, NOT in the protected-category exclusion
  list, so genuinely eligible for refinement — see bug #1 below for why the
  first attempt with `oxygen` was invalid).
- Directed condition: 60 queries, `river` paired cyclically with 8 real semantic
  partners (water, flow, bank, stream, current, valley, bridge, fish).
- Random-control conditions: 60 queries each, `river` paired with a uniformly
  random vocabulary word each time, 6 different seeds (1,2,3,4,5,99).
- Every condition run via the real `chat()` pipeline (no shortcuts), measured
  in a genuinely fresh subprocess (new interpreter, state reloaded from disk)
  to prove any effect is real persistence, not in-session artifact.
- Coherence scored objectively: Laplace-smoothed bigram log-probability
  against the real corpus, plus fraction of generated word-pairs never once
  seen together anywhere in the corpus. Not eyeballed.

## Result
Directed: −9.1857 avg log-prob, 100% never-seen pairs, 15 vectors refined.
Six random seeds: −8.9617 to −9.1858 avg log-prob, 88%–100% never-seen pairs,
7–41 vectors refined. **Directed sits inside the random spread, not above it.**
One random seed (seed=1) produced a vector *byte-for-byte identical* to the
directed run's final vector, despite completely different co-occurrence input
(52 pairs / 126 edges for directed vs 328 pairs / 66 edges for that random
seed). The single best-scoring condition in the whole set was an undirected
random run (seed=2).

## Verdict
❌ Clean, well-controlled null. In this exact mechanism (average co-occurring
partner vectors → median-threshold binarize → preserve grammatical quadrant →
snap to nearest Golay codeword), *which* words you deliberately co-occur with
the target does not detectably matter — only volume/statistics of the churn
does, and not in a monotonic or coherence-improving way either. The bottleneck
isn't "the curriculum wasn't smart enough" — it's that the refinement
mechanism itself discards the distinguishing semantic signal at the
median-threshold + Golay-snap step, before it could ever matter which partner
words were chosen.

## Three real bugs found en route (independent of the main question)
1. **Protected-category exclusion invalidates naive target choice**: words
   with `ubp_id` prefixed `ELEM_/LAW_/PARTICLE_/MOLECULE_/MATH_/PVE_` are
   silently excluded from `_refine_vectors()`. `oxygen` was invalidated as a
   test target for this reason — confirmed via direct `ubp_id` inspection.
2. **`learned_edges` are recorded to disk but never re-applied to the live
   CRG graph on reload** — same bug class as the already-patched
   `vectors_refined`-was-a-bare-counter issue, but the edge-side fix was
   never made. `edges_learned` count is preserved across restarts; the
   actual usable graph structure is not. Confirmed: 214 saved edges
   involving `oxygen`, zero showing up in `rt.crg.out['oxygen']` after reload.
3. **No flush-on-exit save**: `state.save()` only fires at `query_count % 5
   == 0`. A session ending on a non-multiple-of-5 query count silently loses
   up to 4 queries' worth of real, already-computed learning. Confirmed
   directly: an 8-query curriculum showed `queries_processed=8` in-session
   but reloaded as `queries_processed=5` from disk.
4. (Related, minor) Stopword leakage: casual phrasing like "relate to each
   other" lets "other"/"each" through content-word filtering as if they were
   meaningful co-occurrence partners, polluting the learned edge set.

## Reusable tool
`test_directed_framework.py` (in GLM/) — runs baseline / directed / random-N
conditions with equal, explicit query volume, true fresh-process persistence
verification, and objective bigram-based coherence scoring. Can be rerun
against any target word/partner set/volume without rebuilding any of this.
