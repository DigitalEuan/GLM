#!/usr/bin/env python3
"""Export the study's move streams using its already-built codebook."""
from __future__ import annotations
import json, sys, time
from pathlib import Path
ROOT = Path('/workspace/chats/863ec1a1838f4c88d2f16be6')
sys.path.insert(0, str(ROOT / 'leech_bridge'))
from leechlean.parts_stats import build_inventory
from leechlean.moves import MoveAlgebra

t0=time.time()
inv=build_inventory(ROOT/'glm-study/src/lean')
codebook={k: tuple(v) for k,v in json.loads((ROOT/'leech_bridge/out/codebook.json').read_text()).items()}
alg=MoveAlgebra()
missing=0
for rec in inv.files:
    keys=[t.key for t in rec.toks]
    try:
        pts=[codebook[k] for k in keys]
    except KeyError:
        missing+=1; continue
    alg.add_stream(pts, rec.rel)
print('files',len(alg.moves_by_file),'missing',missing,'distinct',len(alg.counts),'total',sum(alg.counts.values()),'elapsed',round(time.time()-t0,1), flush=True)
ordered=sorted(alg.counts,key=lambda k:(-alg.counts[k],k))
mid={k:f'm{i:05d}' for i,k in enumerate(ordered)}
doc={'schema':'cent-move-corpus/1',
     'provenance':'DigitalEuan/GLM src/lean (442 .lean files), addresses from the uploaded Leech-lattice study codebook; reconstructed from source, not a new lattice model.',
     'moves':{mid[k]:{'vector':list(k)} for k in ordered},
     'sequences':[[mid[k] for k in alg.moves_by_file[rel]] for rel in sorted(alg.moves_by_file)]}
path=ROOT/'leech_bridge/out/leech-move-corpus.json'
path.write_text(json.dumps(doc,separators=(',',':')),encoding='utf-8')
summary={'source_files':len(inv.files),'source_tokens':inv.total_token_parts,'inventory_parts':len(inv.counts),
         'addresses':len(codebook),'move_files':len(alg.moves_by_file),'distinct_moves':len(alg.counts),
         'total_moves':sum(alg.counts.values()),'corpus_bytes':path.stat().st_size,'elapsed_seconds':round(time.time()-t0,1)}
(ROOT/'leech_bridge/out/summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print('exported',path,path.stat().st_size,'bytes', flush=True)
print(json.dumps(summary,indent=2), flush=True)
