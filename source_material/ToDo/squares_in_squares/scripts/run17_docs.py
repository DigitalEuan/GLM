#!/usr/bin/env python3
"""run17_docs.py — save the run-17 ledger + download README section."""
import json

ledger = {
 "run": 17,
 "date": "2026-11-05",
 "event": ("SANDBOX RECYCLE ROLLED THE FILESYSTEM BACK TO THE NOV-2 "
           "SNAPSHOT; runs 9-16 (all post-Nov-2 work) were lost from "
           "disk. This run recovered the frontier and resumed the "
           "research program."),
 "score_recovered": 22.823536,
 "beats_grid_recovered": 454,
 "recovery_steps": [
  {"step": "register fetch (scripts/fetch_atlas.py, NEW weekly P3 tool)",
   "result": ("best.json + 324 certs from evand/square-packing@main, "
              "0 failures (the Oct-17 snapshot content, re-fetched live)")},
  {"step": "import_atlas.py (restored from upload/)",
   "result": ("76 applied / 4 skipped / 244 rejected, gain 0.050264 — "
              "identical to the lost run-13 import (idempotence across "
              "the recycle)")},
  {"step": "cascade3 + closure_apply fixpoint (pass 1)",
   "result": "71 chain conversions + closure; score 23.098511, 421/1000"},
  {"step": "gobel2.py REIMPLEMENTED from the run-9 spec (lost in recycle)",
   "result": ("four-parameter G(a1,a2,b,c); verified 7/7 identical to "
              "the surviving gobel_squares.py on the symmetric sub-case; "
              "first pass applied 0 — root cause: bogus self-overlap "
              "guards (2*a1<=s); the real geometry needs only the "
              "cross-corner guard a1+a2<=s (pair-self overlap requires "
              "a1>=s, never binding). After the fix: 83 applied, "
              "0 verify-fails")},
  {"step": "gobel3.py REIMPLEMENTED from the run-10 wave-A spec",
   "result": ("clipped G(a1,a2,b,c,t); 13 applied (lost run-10: 9), "
              "0 verify-fails")},
  {"step": "cascade3 + closure_apply fixpoint (pass 2) + final_assembly",
   "result": ("74 chains + 44 closure; SCORE 22.823536, 454/1000 — "
              "EXACTLY the lost run-16 frontier; round-trip clean "
              "(500500 rows, 0 issues)")}],
 "research_program": {
  "gobel5": ("re-sweep vs the recovered frontier (running); regenerates "
             "the near-miss seed map at workspace/push/gobel5_results.json"),
  "gobel6": ("two-band (split-angle) family — the frontier decode says "
             "records carry 2-3 sub-angles; run after gobel5's ledger "
             "lands: python3 scripts/gobel6.py"),
  "polish": ("fine-axis campaign (angle/anchor/phase) over the top-50 "
             "seeds: python3 scripts/polish.py (expected honest negative "
             "per the lost run-16 probe; complete it for the record)")},
 "lesson": ("run the recovery import FIRST, constructions SECOND — the "
            "import + chains absorbed 0.075 of the 0.275; also: never "
            "let a long bg run hold a stale table snapshot across a "
            "table-writing pass (gobel6 was killed mid-run to prevent "
            "a clobber of the recovered table)"),
 "gap": "leader 22.0544214515, gap 0.769115 — unchanged vs lost frontier"}

json.dump(ledger, open('download/run17_outcomes.json', 'w'), indent=1)
print('run17 ledger saved')

with open('download/README.md', 'a') as f:
    f.write("""

# Run 17 (2026-11-05): the recycle recovery

The sandbox was recycled to the Nov-2 snapshot between turns; runs 9-16
(all post-Nov-2 work) vanished from disk while the conversation kept
their results. Recovery, in the order that worked:

1. `fetch_atlas.py` (new): live re-fetch of the community register —
   324 certs, 0 failures. Also the standing weekly P3 watch.
2. `import_atlas.py` (restored from upload/): 76 rows, gain 0.050264 —
   identical to the lost run-13 import.
3. chains to fixpoint: 71 conversions; score 23.098511.
4. `gobel2.py` REIMPLEMENTED from the run-9 spec — the four-parameter
   G(a1,a2,b,c). First pass applied 0: my first guards were wrong
   (2*a1<=s etc.); the true geometry needs only a1+a2<=s. After the
   fix: 83 applied. Verified 7/7 identical to gobel_squares.py on the
   symmetric sub-case.
5. `gobel3.py` (run-10 wave A, clipped): 13 applied.
6. chains + assembly: **22.823536, 454/1000 — the lost run-16 frontier,
   exactly.** Round-trip clean.

Research program resumed on the recovered frontier: gobel5 seed-map
re-sweep, then gobel6 (two-band family), then polish (P2).
""")
print('download README appended')
