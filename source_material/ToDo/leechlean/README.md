# leechlean — Lean parts on the Leech lattice

A functional investigation system built for the Geometric Language Machine (GLM)
repository (https://github.com/DigitalEuan/GLM): the recurring parts of the
repository's Lean 4 development are each mapped to an address in the Leech
lattice Λ₂₄, a Lean file becomes a sequence of addresses — one per token, one
per tick — and the geometry of those addresses is measured, not asserted.

**Version 2 adds** the coset layer (Λ/2Λ, the Monster's index space), error
correction of corrupted address streams, and the lattice-graph: files as
groups of addresses (words, symbols, machine instructions) linked by
joinings, with cross-file reuse measured.

**Version 3 adds** the application demonstration: the Lean library as a
lattice-graph you AUTHOR on — `leechlean/library.py` and
`demo/demo_stitching.py`. A new file is stitched from context-verified
library parts; only the genuinely new parts get fresh Leech addresses (on
the fly, keeping the codebook injective); the result still projects to
byte-exact Lean text, ready for a real toolchain; and queries walk the graph
to propose continuations. Leave-one-out: a new file is on average 96.7%
parts-known, 94.7% context-known, and only 8.4% of its structural ticks are
new.

**Version 4 adds** the happening between addresses — `leechlean/moves.py`
and `demo/demo_moves.py`. The transition from one addressed part to the next
is a MOVE d = B − A: a Leech lattice vector composing by addition, with the
class homomorphism κ: Λ → Λ/2Λ projecting every journey to a walk on the
2²⁴-class index space (the same Λ/2Λ structure the Griess algebra is graded
by — its 196,884 dimensions decompose as 300 + 98,280 + 98,304, the 98,280
piece indexed by the minimal-vector classes). Measured: 80,361 distinct
moves carry the whole corpus (the top 50 are 39% of all ticks), composed
moves land back in the repertoire 14× more often than chance (39.8% vs
2.8%), proofs are journeys that return (net displacement shorter than one
average move) yet are MORE tortuous than shuffled controls, proof bodies run
hotter than statements (energy ratio 1.10), and predicting the next MOVE
beats predicting the next part: **45.8% vs 40.6% greedy top-1,
leave-one-file-out — the happening is the more predictable primitive.**

## What is in here

```
leechlean/            the Python package
  leech_core.py       the Leech lattice engine: extended binary Golay code
                      (from the GLM substrate's parity block B), the exact
                      membership predicate of the Conway–Sloane construction,
                      the 196,560 minimal vectors, the norm-48 shell census,
                      and a vectorised exact nearest-point decoder
  lean_parts.py       Lean 4 lexer (byte-exact round trip on all 442 corpus
                      files) + declaration frames + tactic heads
  parts_stats.py      the part inventory (tokens, bigrams, frames, tactics)
                      with counts and syntactic role mixes
  embed.py            the 24-channel direction: 8 role channels + a 16-dim
                      PPMI/SVD co-occurrence embedding over the 2,048 most
                      frequent structural tokens
  addressing.py       part -> address: target radius sqrt(32*E) (one bit of
                      surprisal = 4 units of true lattice energy), exact
                      nearest-Leech-point quantisation, rank first-fit
                      collision displacement (the codebook is injective)
  codec.py            file -> address stream -> exact file bytes
  dynamics.py         tick walks, work integrals (which stay on the lattice),
                      real-vs-shuffled path statistics
  fingerprint.py      file fingerprints (lattice points), PCA, controls
  cosets.py           [v2] a Z-basis of Lambda built from an explicit
                      generating set (HNF, det 2^36, contains all 196,560
                      minimal vectors), the Lambda/2Lambda class map, the
                      q-form, class types (0/2/3/4), and the full 2^24-class
                      census verifying the singular count 2^23+2^11
  correction.py       [v2] corrupted address streams: corruption models
                      (jitter / single flip / minimal-vector slip / burst),
                      the congruence sieve, the class syndrome, and three
                      decoders (two-stage, class-assisted, raw)
  lattice_graph.py    [v2] the lattice-graph: constituents (words, symbols,
                      machine instructions), adjacency joinings as Leech
                      vectors with Lambda/2Lambda class types, cross-file
                      and cross-module reuse, file subgraphs
  library.py          [v3] the library as a lattice-graph: (part, frame)
                      verification contexts, the authoring classifier
                      (context-verified / part-known / new), on-the-fly
                      addressing of new parts, byte-exact projection, and
                      graph queries (joining-distribution continuations)
  moves.py            [v4] the happening between addresses: moves as Leech
                      vectors, the class homomorphism onto Lambda/2Lambda,
                      composition closure, the class pairing (verified well
                      defined), and the group-algebra convolution over the
                      2^24-class index space
data/
  codebook.json       all 39,992 parts with their Leech addresses
  addressing_stats.json, corpus_summary.json
  exp_codec.json, exp_dynamics.json, exp_fingerprint.json, exp_quantizer.json
  exp_cosets.json     [v2] the codebook's coset map (occupancy, class types)
  exp_correction.json [v2] all correction/syndrome/sieve measurements
  exp_graph.json      [v2] lattice-graph + reuse statistics
  file_subgraph_Golay_Code.json  [v2] one file as a graph artifact
  library_core.npz    [v3] the library graph in compact form (29,422 parts,
                      80,375 joinings, 55,269 part+frame contexts) -- this
                      is what demo_stitching.py runs on, no corpus needed
  exp_library.json    [v3] leave-one-out coverage, query accuracy, stitching
  v2_stitch_manifest.json  [v3] the delta manifest of the stitched file
  exp_moves.json      [v4] the move experiments: repertoire, composition
                      closure, 9,188 declaration journeys, the model
                      head-to-head, statement/proof energy split
  sample_address_stream.json   first 120 ticks of Golay/Code.lean
demo/
  demo_encode_decode.py          the codec demo (byte-exact round trip)
  demo_coset_correction.py       [v2] corrupt a stream, detect, correct
  demo_stitching.py              [v3] author a file by stitching the library
  demo_moves.py                  [v4] the algebra of moves, live
  sample_Golay_Code.lean, demo_output.txt, demo_correction_output.txt,
  demo_stitching_output.txt, stitched_Golay_Code_v2.lean,
  demo_moves_output.txt
figures/              the eighteen report figures
```

## How the addressing works

For a part p (a token, bigram, declaration frame or tactic name):

  * its **direction** u(p) is the unit 24-vector [role mix; PPMI-SVD
    co-occurrence embedding] — where and with what the part is used;
  * its **energy** is its surprisal E(p) = −log₂ f(p) bits;
  * its target is T(p) = √(32·E)·u(p) in the ×√8 integer model, so the true
    squared norm of the target is 4·E: **one bit of surprisal is four units
    of Leech energy, and the minimal shell (energy 4) is the one-bit sphere**;
  * its **address** A(p) is the exact nearest Leech point to T(p);
  * a part whose cell is already taken steps outward along its own direction
    (the commoner part of a pair keeps the cell), which makes the codebook
    injective: 39,992 parts, 39,992 distinct addresses, 0 collisions.

## Measured results

Round 1 (see the first report):

  * engine verified against the literature and the GLM substrate: 759 octads,
    S(5,8,24) on all 42,504 five-subsets, kissing number 196,560, norm-48
    shell exactly 16,773,120, decoder matches the GLM substrate's decoder to
    1.8e-15, and reproduces the Leech/Z²⁴ quantiser ratio 0.784 vs the
    theoretical 0.790 on white sources;
  * codec: **442/442 corpus files round-trip byte-exactly** through their
    address streams;
  * geometry: 1-nearest-neighbour module classification of file fingerprints
    77.6% (88.0% on the five modules with ≥8 files) against a 63.8%
    permuted-address control;
  * energy: address energy vs 4×surprisal, Pearson r = 0.897 over undisplaced
    parts; 3,659 parts are displaced outward (the measured cost of an
    injective codebook);
  * dynamics: every file's work integral stays on the lattice; real token
    order walks 15.6% further than the same addresses shuffled.

Round 2 (this version):

  * **cosets**: own Leech basis (det 2^36, contains all 196,560 minimal
    vectors, which generate the lattice — so the basis is the lattice);
    Λ/2Λ class map agreeing with the substrate's on the whole codebook;
    98,280 type-2 classes from the minimal vectors, each the pair {v, −v};
    the full 2^24-class census hits the Witt-index singular count exactly
    (8,390,656 = 2^23 + 2^11);
  * **error correction**: under jitter, single-coordinate flips (k = 1..6),
    minimal-vector slips (up to every tick) and bursts: **100% detection, 0
    false alarms, 96–100% correction**. The sieve names the broken
    congruence (±1/±3 flips break parity; ±2/±6 break the Golay condition —
    a weight-1 mod-4 error caught by the Golay parity check; ±4 breaks only
    the mod-8 sum); on-lattice slips are caught by the class syndrome, every
    error class type-2 exactly as the theory of minimal vectors predicts;
  * **the lattice-graph**: 20,458 word/symbol parts joined by 105,282
    adjacency edges; every joining is a Leech vector with a measured class
    type; **the reuse law: joinings shared by 10+ files have half the length
    of single-file joinings** (median |d|² 176 vs 384); 568 frame→tactic
    instruction joins connect the machine-instruction level; the 14 modules
    share parts measurably (Jaccard matrix in exp_graph.json); only 11 parts
    are used by all 14 modules — the universal core is the 8 symbols
    : := ( ) , [ ] =>.

Round 3 (this version — the application):

  * **the library**: the corpus as a queryable lattice-graph — 29,422 parts,
    80,375 joinings, 55,269 (part, declaration-frame) verification contexts
    over 1.49M tokens;
  * **leave-one-out**: authoring any corpus file against the other 441, on
    average 96.7% of its ticks use parts the library already has, 94.7% are
    attested under the same declaration frame, 92.4% of its joinings already
    exist — **the verification frontier (structural ticks new to the
    library) is on average 8.4%** (median 7.1%; most novel file:
    Rule30/scripts/theorem_wheel_axioms.lean; most derivative:
    RequestProject/GLM/AdversarialDialogue.lean);
  * **stitching**: authoring Golay/Code_v2.lean (renamed theorem + new
    corollary) — 1,741 of 1,746 ticks context-verified, delta = 4 new parts
    (2 comments, 2 identifiers) + 9 new joinings, all four new addresses
    assigned on the fly on the lattice (energies 78–90, near the 4×surprisal
    rule), the extended codebook stays injective, and the projection is
    **byte-exact** — the delta is the part in question, not the entire body;
  * **queries**: greedy top-1 continuation from the joining distribution is
    40.6% accurate per tick (only 2% of contexts unseen); sampled
    completions are plausible in shape and drift in content — honestly
    labelled unverified, they are proposals, not library material.

Round 4 (this version — the happening between addresses):

  * **the move algebra**: the transition between addressed parts is
    d = B − A ∈ Λ, composing by addition; the class homomorphism
    κ: Λ → Λ/2Λ (verified: κ(d1+d2) = κ(d1)(*)κ(d2), classes composed by
    reduction of the sum) projects journeys to walks on the 2²⁴-class index
    space, with the mod-2 class pairing ⟨x,y⟩ (verified well defined;
    Λ doubly even) — the same Λ/2Λ the Griess algebra is graded by;
  * **the repertoire**: 80,361 distinct moves carry all 1,487,183 ticks;
    mean |d|² 654 vs 954 for random part pairs; the top 50 moves (the
    micro-syntax gestures: space→`(`, `,`→space, space→`:` …) are 39% of
    all happenings; moves occupy only 63,257 of 2²⁴ classes (1.27 moves per
    class), overwhelmingly of class types 3 and 4 — the type-2
    (minimal-vector, Griess X_r-indexed) classes host only 526 moves;
  * **composition closure**: d1∘d2 = d1+d2 lands back in the repertoire for
    39.8% of consecutive move pairs (33.2% within the same file) against a
    2.8% null — the corpus's indexed multiplication largely stays inside
    its own repertoire, a 14× enrichment over chance;
  * **the journey of a proof** (9,188 declarations): proofs return —
    median net displacement |A_end−A_0|² = 368, shorter than one average
    move (654) — yet real orderings are MORE tortuous than shuffled
    controls of the same address multiset (theorem|by: 100.0 vs 85.8
    median tortuosity, p>control = 1.00); proof bodies run hotter than
    statements (energy ratio 1.10 for theorem|by, 1.15 for theorem|term);
    the class-type signature of a proof averages 1.06 bits entropy;
  * **it helps build**: same counts, same greedy leave-one-file-out
    protocol — predicting the next MOVE is 45.8% accurate against 40.6% for
    predicting the next part (+5.2 points), the class alone reaches 38.8%
    of a 63k-way choice, and class-first constrained decoding lifts the
    part model to 42.1%. The happening is the more predictable primitive,
    and it is free.

## Running

    python3 demo/demo_encode_decode.py                       # codec demo
    python3 demo/demo_coset_correction.py slip 1.0           # corrupt + correct
    python3 demo/demo_stitching.py                           # author by stitching
    python3 demo/demo_moves.py                               # the algebra of moves

Both demos need only numpy and the bundled codebook. Rebuilding everything
from a Lean tree: build_inventory → build_directions → assign_addresses
(~4 minutes), then cosets/correction/lattice_graph as in the project's
scripts/ (run_coset_experiments.py, run_graph_experiments.py).

## Relation to prior work in the GLM repository

This system extends the GLM's existing addressing work —
`glm_universal/reasoning/lean_address.py` and `RequestProject/GLM/Address.lean`
address **declarations** through a 24-feature vector and a nearest-Leech
quantiser with a proven readback — down to the level of the **common parts**
the owner's concept names, with frequency (energy), context (direction),
files as address paths over ticks, and every claim measured against controls.
The coset layer builds on `substrate/leech2.py`'s Λ/2Λ machinery (class map,
q-form, type census) — reimplemented here from the construction and verified
against it. The Golay parity block B is the substrate's own (`Golay/Code.lean`),
so the lattice here is the same lattice the GLM development already carries.
