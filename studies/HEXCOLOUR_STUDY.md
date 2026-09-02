# Hexcolour addresses: are they carrying anything?

*What `substrate/isomorphism.py`, `migration/state.py`, `migration/store.py`,
`RequestProject/GLM/Endianness.lean` and `report state migration` say about the
address layer, and what auditing it measured.*

Every figure below is recomputed by the code that reports it. Run

```bash
cd overlay
PYTHONPATH=. python3 GLM.py -q "report state migration" --verify-tct
```

and the third column re-derives the whole study in a fresh interpreter and
checks it key by key (`VERIFIED True`).

---

## 1. What a hexcolour is, and what it is not

A carrier in this package is a 24-bit mask: a subset of the 24 coordinates the
Golay code and the Leech lattice live on. A **hexcolour** is that mask written
as six hexadecimal digits, `#57c1ff`, one digit per four coordinates.

That is *all* it is. It is an **address** in the sense of directive D3: it
fixes the carrier exactly and it means nothing beyond it. It is not a colour,
nothing renders it, and the fact that it can be pasted into a stylesheet is a
coincidence of width. Six hex digits is exactly 24 bits, which is why the
rendering is lossless, and losslessness is the whole content of the claim.

The upstream pipelines used the same word for the same thing, so the layer is
inherited rather than invented; what was missing was any measurement of whether
it still does its job on the data that was migrated.

## 2. The one real question, and the one real correction

The layer is trivial arithmetic, so the only way it can go wrong is at the
boundary: *which* bit is coordinate 0.

The migration audit found the answer in the data rather than in the prose. Of
the **15** per-task addresses the supplied ARC pipeline left behind:

* read least-significant-bit first (coordinate `i` at bit `i`): **0 of 15** are
  Golay codewords;
* read most-significant-bit first (coordinate `i` at bit `23 − i`): **15 of
  15** are.

Fifteen out of fifteen is not a coincidence — the code has 4,096 words out of
16,777,216, so a wrong reading lands one on it with probability about 1 in
4,096 — so the writer snapped to a codeword before writing and stored
coordinate `i` at bit `23 − i`. The correction is a *reading* convention, and
not one bit of stored data changes.

`RequestProject/GLM/Endianness.lean` is why that correction is free rather than
merely convenient. Reversing bit order is the coordinate permutation
`Fin.revPerm`, so:

* `bitsMSB_eq_bitReverse_bitsLSB` — the two readings of one stored integer
  differ exactly by bit reversal, which makes this a frame question rather than
  a corruption question;
* `hdist_bitReverse` — bit reversal preserves Hamming distance, hence weight;
* `nearest_bitReverse_iff` — nearest-codeword decoding therefore commutes with
  it;
* `min_distance_bitReverse` — the reversed image is again a `[24, 12, 8]` code,
  so the three-error correction guarantee survives.

No guarantee that held in one frame is lost in the other. That is the whole
justification for the fix, and it is machine-checked.

The *other* candidate correction is refused, and refused on measurement: the
shipped `LEGACY_TO_CORE` coordinate permutation would move **4,088** of the
4,096 codewords off the code, so it must not be applied to data already written
in the canonical frame. The two frames coincide; only the bit order did not.

## 3. The audit

`hexcolour_audit()` asks whether the layer is doing its job on the shipped
data, and every number is measured at call time:

| question | measured |
|---|---|
| concepts carrying an address | **4,680** |
| distinct addresses | **4,680** |
| collisions | **0** |
| addresses that do not read back to their own mask | **0** |
| addresses disagreeing with the mask stored beside them | **0** |
| addresses that fail to commute with the legacy-to-core relabelling | **0** |
| legacy per-task addresses | **15** |
| …of which Golay codewords | **15** |
| …failing to round-trip | **0** |
| **faithful** | **True** |

Distinctness is the one that matters. Four thousand six hundred and eighty
concepts, four thousand six hundred and eighty addresses: the rendering
separates everything it addresses, so an address determines a concept.

The falsifier is exercised too: `test_a_corrupted_address_is_caught` flips one
bit of one stored address and the audit reports exactly one round-trip failure,
one recomputation disagreement and `faithful: False`. An audit that cannot fail
is not an audit.

## 4. Are they *used*?

Two senses, and they are worth separating.

**Carried faithfully** — yes, and §3 is the measurement. `verify_canonical`
also refuses to accept a payload whose addresses do not recompute from their
carriers, so the layer cannot silently rot.

**Used as a key** — now yes. `ConceptStore.by_hexcolour(colour)` recovers a
concept from its six digits alone, with no name and no search; the index is
well defined precisely because §3 measured the addresses to be distinct, and
`test_every_concept_round_trips_through_its_address` walks all 4,680 of them
through address and back. Before this round the addresses were written,
verified and displayed but nothing looked anything up by them, which is a
weaker thing than the word "address" claims.

## 5. What an address does *not* tell you

An address is the carrier, and the carrier is a received word rather than a
codeword. Of the 4,680 concepts only **463** sit on the Golay code; 2,389
decode to a unique nearest codeword and **1,828** are genuinely ambiguous —
six equally near codewords and no answer — and those are recorded as ambiguous
rather than snapped. So `#57c1ff` names a point exactly, and says nothing about
whether that point is anchored. Reading the address as if it were a codeword is
the mistake this separation exists to prevent.

## 6. A stale figure, annotated rather than deleted

`overlay/README.md`'s legacy ARC-AGI v35 results block reports **66 hexcolour
addresses**. The shipped table `arc_agi_17/results/hexcolour_addresses.json`
holds **15**. The 66 is the upstream run's own count and has been annotated in
place rather than removed, since the archive block is a record of what that run
reported. The live, audited counts are the ones in §3.

## 7. Where each piece lives

| piece | file |
|---|---|
| the converters, and the coordinate permutations | `overlay/glm_universal/substrate/isomorphism.py` |
| the address audit and the frame audit | `overlay/glm_universal/migration/state.py` |
| lookup by address | `ConceptStore.by_hexcolour` (`overlay/glm_universal/migration/store.py`) |
| bit order as an isometry, machine-checked | `RequestProject/GLM/Endianness.lean` |
| the report subject | `report state migration` (`runtime/session.py`), step 6 |
| the column-3 template | `_body_report_state_migration` (`runtime/tct_engine.py`) |
| the tests | `overlay/glm_universal/tests/test_state_migration.py` |
