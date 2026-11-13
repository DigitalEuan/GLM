# Knowledge atlas — addressed parts and stitches

The repository has more prose than code. That is useful only while a reader can
find the one section that owns a claim. This page defines the file-keeping
method used to keep that true as the system grows.

## The method, borrowed from `leechlean`

The adjacent `leechlean` study treats a Lean development as recurring **parts**
with **addresses**, records where a part is used as its **context**, and builds
a new file by **stitching** addressed parts rather than retyping them. Its
lattice geometry is not needed here. The same discipline applies to Markdown:

| `leechlean` | This repository |
|---|---|
| part | one Markdown section, under one heading |
| address | `kp-<hash>` derived from path + heading, not from line number |
| context | document, heading trail, outgoing links, neighbouring section |
| joining | a local Markdown link or the next section in the same document |
| stitch | a selected reading path over addresses |
| projection | open the source path at the recorded line; the Markdown is canonical |

The atlas is an index, not a second copy. It records addresses and pointers;
`cent knowledge stitch --full` prints bodies only for the current reading.

## Commands

```bash
python3 cent knowledge atlas
python3 cent knowledge find "operation trial wheel"
python3 cent knowledge stitch "operation trial wheel"
python3 cent knowledge stitch "operation trial wheel" --full
python3 cent knowledge stitch kp-e724000d9e kp-e4d4fe9ec1 --full
python3 cent knowledge duplicates
python3 cent knowledge atlas --json
```

`find` ranks sections by heading, summary and body terms. `stitch` returns a
deduplicated reading path; a query and explicit `kp-...` addresses are both
accepted. `duplicates` reports exact repeated sections above a size threshold.
`--json` carries the schema, addresses, hashes and edges for tooling.

Addresses stay stable while a section keeps its path and heading. Editing the
body changes the `content_hash`, which is how repeated knowledge and drift are
detected. Moving a heading changes the address deliberately: the address names
a location in the knowledge structure, not a transient line.

## File-keeping rules

1. **One question, one owner.** A claim lives in the document named by the
   authority table in [`../DIRECTIVE.md`](../DIRECTIVE.md) §7. Other documents
   link to it; they do not restate it with a different value.
2. **Do not add a status document.** Status belongs to the owner that already
   exists. Cross-cutting reading is a stitch, not a new page.
3. **Extract on the third repetition.** If a section appears in three places,
   move it to a shared part and leave links. The 22 application proposals now
   point at [`../applications/README.md`](../applications/README.md) for their
   pipeline, parameters, run commands and W1↔W6 table.
4. **Live counts have one home.** The canonical gate count is the README
   statistics row, produced by `tests/run_all.py`. Commands in other documents
   say `python3 tests/run_all.py` without freezing today's number. Historical
   phase records may keep the count that was true at that phase.
5. **A stitch is not a source.** It is a temporary reading path. If a stitch
   becomes a durable claim, put it in the owning document and address it there.

## What this round changed

- added the atlas, `find`, `stitch` and `duplicates` commands;
- replaced 46 repeated application sections (22 pipeline copies, 22 parameter
  copies and two W1↔W6 copies) with links to one canonical page;
- removed the current gate count from documents that were pinning an earlier
  number; the README row and the gate output own the live number;
- added the atlas to the documentation index and the contribution checklist.

Exact duplicate groups went from three (46 parts) to zero at the time of this
audit. The tool reports the current number; this page does not freeze it.

## Limits

The index is lexical, not semantic: there are no embeddings and no claim that a
high score means the section answers the question. Only exact repeated sections
are reported; near-duplicates still need review. A stable address is not a
proof that the section is correct, current or authoritative. The claim and its
evidence still have to satisfy the project's normal rules.

The method is indebted to `leechlean`'s part/address/stitch discipline, not to
its Leech-lattice claims. No lattice, codebook or Lean verification result is
imported by this page.
