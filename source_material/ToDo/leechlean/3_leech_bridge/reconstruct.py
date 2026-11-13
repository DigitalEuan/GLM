#!/usr/bin/env python3
"""Rebuild the Leech-lattice study's move corpus from its 442 Lean files.

Uses the study's own flat modules, unmodified, via a temporary package copy.
Writes a cent-move-corpus/1 document and a small JSON summary.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path('/workspace/chats/863ec1a1838f4c88d2f16be6')
sys.path.insert(0, str(ROOT / 'leech_bridge'))

from leechlean.parts_stats import build_inventory, granularity_counts  # noqa: E402
from leechlean.embed import build_directions  # noqa: E402
from leechlean.addressing import assign_addresses  # noqa: E402
from leechlean.moves import MoveAlgebra  # noqa: E402

CORPUS = ROOT / 'glm-study/src/lean'
OUT = ROOT / 'leech_bridge/out'
OUT.mkdir(parents=True, exist_ok=True)


def main() -> int:
    t0 = time.time()
    inv = build_inventory(CORPUS)
    print(f'inventory: files={len(inv.files)} tokens={inv.total_token_parts} '
          f'parts={len(inv.counts)} granularity={granularity_counts(inv)}', flush=True)

    dirs = build_directions(inv)
    print(f'directions: {len(dirs.table)} identity_directed={len(dirs.identity_directed)} '
          f'svd_variance={dirs.svd_variance:.6f} elapsed={time.time()-t0:.1f}s', flush=True)

    addr = assign_addresses(inv, dirs)
    print(f'addressing: {addr.stats} elapsed={time.time()-t0:.1f}s', flush=True)

    (OUT / 'codebook.json').write_text(
        json.dumps({k: list(v) for k, v in addr.addresses.items()},
                   separators=(',', ':')), encoding='utf-8')

    alg = MoveAlgebra()
    missing = 0
    for rec in inv.files:
        keys = [t.key for t in rec.toks]
        try:
            points = [addr.addresses[k] for k in keys]
        except KeyError:
            missing += 1
            continue
        alg.add_stream(points, rec.rel)
    print(f'moves: files={len(alg.moves_by_file)} missing_files={missing} '
          f'distinct={len(alg.counts)} total={sum(alg.counts.values())} '
          f'elapsed={time.time()-t0:.1f}s', flush=True)

    stats = alg.stats()
    print(f'move stats: {json.dumps(stats, sort_keys=True)}', flush=True)

    # Stable ids: most frequent first, then vector lexicographic.
    ordered = sorted(alg.counts, key=lambda k: (-alg.counts[k], k))
    mid = {k: f'm{i:05d}' for i, k in enumerate(ordered)}
    doc = {
        'schema': 'cent-move-corpus/1',
        'provenance': ('Derived from DigitalEuan/GLM src/lean (442 .lean files) using '
                       'the uploaded Leech-lattice study code; addresses are the '
                       'study codebook, not a new lattice model.'),
        'moves': {mid[k]: {'vector': list(k)} for k in ordered},
        'sequences': [
            [mid[k] for k in alg.moves_by_file[rel]]
            for rel in sorted(alg.moves_by_file)
        ],
    }
    path = OUT / 'leech-move-corpus.json'
    path.write_text(json.dumps(doc, separators=(',', ':')), encoding='utf-8')
    summary = {
        'source_files': len(inv.files),
        'source_tokens': inv.total_token_parts,
        'inventory_parts': len(inv.counts),
        'granularity': granularity_counts(inv),
        'addresses': len(addr.addresses),
        'address_stats': addr.stats,
        'move_files': len(alg.moves_by_file),
        'distinct_moves': len(alg.counts),
        'total_moves': sum(alg.counts.values()),
        'move_stats': stats,
        'corpus_bytes': path.stat().st_size,
        'elapsed_seconds': round(time.time() - t0, 1),
    }
    (OUT / 'summary.json').write_text(json.dumps(summary, indent=2),
                                      encoding='utf-8')
    print(f'exported {path} ({path.stat().st_size} bytes)', flush=True)
    print(f'summary {OUT / "summary.json"}', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
