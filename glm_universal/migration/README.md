# `glm_universal/migration/` — the literal data migration

**Parent:** [`../README.md`](../README.md) · **Repository root:**
[`../../README.md`](../../README.md)

Three modules that take the repository's *actual persisted state* —
`arc_agi_17/results/glm_state.json` and its companions — and bring it into
the package in a form that is exact, audited, referentially intact and
verifiable from the carriers alone.

The emphasis is on **literal**. Nothing here re-derives the data from a
model, re-runs a growth loop, or invents plausible values. Every concept in
the canonical file is either a record that was in the source file or a
carrier minted deterministically for a name that the source file referred to
but never defined — and the two are labelled apart.

| module | lines | what it does |
|---|---|---|
| `frames.py` | 245 | Settles **by computation** which Golay frame and which bit order the stored data uses. |
| `state.py` | 680 | Performs the migration and writes `arc_agi_17/results/glm_state_canonical.json`; `verify_canonical` re-derives every field from the masks alone. |
| `store.py` | 239 | Consumes it: `ConceptStore` indexes the result and answers questions of it. |

Reachable from the runtime as `report state migration`, `report concept
store` and `task concepts`. Tested by
`glm_universal/tests/test_state_migration.py` (47 tests).

---

## 1. The frame audit, and a correction to the received story

Before a single record can be migrated, one question has to be settled: are
the stored 24-bit vectors in the same coordinate frame as the package's Golay
code? The repository ships a permutation `LEGACY_TO_CORE`, and the natural
assumption is that stored data needs it.

`frames.py` checks instead of assuming, and the answer is **no**:

```
engine_codewords    4096
canonical_codewords 4096
shared_codewords    4096
frames_coincide     True
correct_bridge      "identity"
```

The repository's `GolayCodeEngine` (parity block `B` in
`GMHGL/ubp_unified_v5.py`) generates **exactly the same 4,096 codewords**,
under the same coordinate numbering, as this package's canonical `GOLAY_SET`.
Both have weight distribution `{0:1, 8:759, 12:2576, 16:759, 24:1}`. So
concept vectors migrate by the **identity**.

Worse, applying `LEGACY_TO_CORE` to this data would be actively destructive:

```
codewords_leaving_the_code  4088
codewords_staying              8
is_automorphism            False
safe_for_engine_frame_data False
```

**This is a correction to the narrative attached to `report migration`.**
That machinery is about routing *legacy-frame words* through the audited
decoder, and it is correct on its own terms — `LEGACY_TO_CORE` is a genuine
coordinate permutation, and `Permutation.lean` proves that decoding commutes
with it. What is not true is that the repository's *stored state* is in the
legacy frame. It is not, and the permutation must not be applied to it.

### Bit order is a different question, with the opposite answer

Stored `hexcolour` addresses *are* in a different convention:

```
addresses                   15
codewords_read_lsb_first     0
codewords_read_msb_first    15
bit_reversal_required     True
```

The writer stored coordinate *i* at bit `23 − i` and snapped to a codeword
before writing, so reading an address without reversing it lands off the code
— every single time, and reversing it lands on the code — every single time.
A 15-for-15 / 0-for-15 split is not ambiguous.

Bit reversal is itself a coordinate permutation (`Fin.revPerm`), so it is an
isometry and nothing is lost by adopting it. That is proved in
`glm_lean/RequestProject/GLM/Endianness.lean` as
`endianness_is_a_frame_choice`.

## 2. The migration

`migrate_state()` reads the source, migrates each record, and writes
`glm_state_canonical.json` (3.6 MB, **float-free**).

```
concepts_imported            4282
concepts_minted               398
concepts_total               4680
masks_distinct               True
edges_migrated               4014
edges_dropped                   1
referentially_intact         True
quadrant_weights_agree       4680
roles_agree                  4680
addresses                      15   (all 15 codewords after reversal)
faces                         100   (all 100 resolved)
```

### Minting, and why it is separated

The source file's edge list dangles: 1,993 of its 4,015 edge endpoints name
something the file never defines. Those endpoints resolve to 399 distinct
values, of which 398 are names and one is `None`. Dropping those edges
would discard real relational
structure; inventing carriers silently would corrupt the record. So the
migration **mints** a carrier for each name, deterministically, by hashing
the name with FNV-1a and snapping to a Golay codeword — and marks every such
concept `minted` rather than `imported`. The one edge with a nameless
endpoint is dropped and counted.

After minting, `referentially_intact` is `True` and `dangling_edges` is `0`.

### Decoding status is recorded, not resolved

```
carriers_that_are_codewords   463
decode_corrected             2389
decode_ambiguous             1828
decode_guaranteed            2852
```

1,828 carriers sit at Hamming distance ≥ 4 from the code, where
nearest-codeword reading is not unique. The migration records
`ambiguous` and keeps the full list of equidistant codewords rather than
picking one. That boundary is exactly `snap_boundary_at_three` in
`glm_lean/RequestProject/GLM/GolayBoundary.lean`.

### Exactness

Everything is `int` or `fractions.Fraction`. `floats_in_payload` is `0` and a
test asserts it.

The migration also surfaces a real numeric discrepancy it did **not** paper
over: the pipeline's `Y_CONST` and the package's `Y` differ by
`41 / 1.25e18`, which propagates to a worst stored-versus-exact NRCI gap of
about `4.9e-7` across the 4,282 measured concepts. Both values are reported
as exact fractions under the `y` key; the canonical file stores the exact
one.

### Verification

`verify_canonical()` re-derives every field — weights, roles, quadrant
weights, NRCI, decoding status, address round-trips, face consistency — from
the masks alone, and compares:

```
fields_recomputed_and_agreeing True
disagreements                    []
dangling_edges                    0
addresses_round_trip           True
faces_consistent               True
floats_in_payload                 0
frames_coincide                True
```

## 3. Using it

```python
from glm_universal.migration import ConceptStore

store = ConceptStore.load()
len(store)                                # 4680
store.nrci("entropy")                     # exact Fraction
store.neighbours("entropy")               # labelled CRG neighbourhood
store.path("entropy", "energy")           # shortest labelled path
store.path("entropy", "energy",
           exclude_labels=("auto_proposed",))   # asserted knowledge only
store.hamming_neighbours("entropy")       # nearest carriers in the substrate
store.crosslinks(register_names)          # where CRG meets a register
```

The `exclude_labels` argument matters. Of 4,014 edges, **3,157 are
`auto_proposed`** by the growth loop and only **857 are asserted**. A path
that survives excluding the auto-proposed edges is knowledge someone put
there; a path that does not is machine speculation. `task concepts` reports
which kind it found.

## 4. A negative result, stated plainly

`store_report()` samples concepts and compares their graph neighbourhood with
their substrate (Hamming) neighbourhood:

```
samples_checked                          4
samples_where_graph_and_substrate_agree  0
```

For `entropy`, the graph neighbours are `adiabatic`, `antiferromagnet`,
`boltzmann`, … and the substrate neighbours are `amiability`, `cacodyl`,
`shot`, … — no overlap at all.

This is expected and is reported rather than hidden. Only 65 of the 4,282
imported concept vectors are codewords, and the carriers were assigned from
digests and hashes in the original pipeline (the lingo carriers used Python's
`hash()`, which is not even reproducible across runs). **Hamming distance
between concepts in this data is not a semantic distance.** Any reasoning
over the migrated state has to go through the graph labels or through the
register cross-links, and `task concepts` does exactly that.

## 5. Files written

| path | size | contents |
|---|---|---|
| `arc_agi_17/results/glm_state_canonical.json` | ~3.6 MB | the migrated state: 4,680 concepts, 4,014 edges, 15 addresses, 100 faces, all exact, no floats |

The source files are read and never modified.
