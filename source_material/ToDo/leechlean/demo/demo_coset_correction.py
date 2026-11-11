#!/usr/bin/env python3
"""Demo: coset syndromes and error correction of an address stream.

Run:  python3 demo_coset_correction.py [model] [level]

Encodes the bundled Lean file to Leech addresses, corrupts the stream
(jitter | flip | slip), and shows the three defensive layers measured in the
investigation: the congruence sieve (which Leech condition the corruption
breaks), the Lambda/2Lambda class syndrome (detection of on-lattice slips),
and correction back to the exact original part stream.
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from leechlean import cosets as CS
from leechlean import correction as CR
from leechlean.lean_parts import tokenize
from leechlean.leech_core import in_leech_many

codebook = json.load(open(HERE.parent / "data/codebook.json"))
PARTS = codebook["parts"]
ADDR = {k: tuple(p["address"]) for k, p in PARTS.items()}

model = sys.argv[1] if len(sys.argv) > 1 else "slip"
level = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
rng = np.random.default_rng(7)

text = (HERE / "sample_Golay_Code.lean").read_text(encoding="utf-8",
                                                   errors="replace")
toks = tokenize(text)
A = np.array([ADDR[t.key] for t in toks], dtype=np.int64)
print(f"file: sample_Golay_Code.lean | ticks: {len(A)}")
print(f"corruption model: {model} (level {level})")

if model == "jitter":
    X = CR.corrupt(A, "jitter", rng, p=level)
elif model == "flip":
    X = CR.corrupt(A, "flip_k", rng, k=int(level))
elif model == "slip":
    X = CR.corrupt(A, "slip", rng, p=level)
else:
    sys.exit("model must be jitter | flip | slip")

# layer 1: the congruence sieve
sieve = CR.sieve_report(X)
n = sum(sieve.values())
print(f"sieve: parity {sieve['mod2']}, Golay cond. {sieve['mod4-golay']}, "
      f"sum {sieve['mod8-sum']}, clean {sieve['clean']}  (of {n} sampled)")

# layer 2: the class syndrome + layer 3: correction
cb = CR.CodebookIndex(ADDR)
L = CR.nearest_leech(X.astype(np.float64))
syn = CR.syndrome_analysis(A, X, cb, L=L)
print(f"class syndrome: {syn['class_changing']} of {syn['n']} ticks change "
      f"their Lambda/2Lambda class; error class types {syn['error_class_types']}")
print(f"detection: {syn['n_detected']} of {syn['n_corrupted']} corrupted ticks "
      f"detected, {syn['false_alarms']} false alarms")

pos, stats = CR.decode_stream(X, cb, mode="class_assisted", L=L)
decoded = [cb.keys[p] for p in pos]
correct = sum(d == t.key for d, t in zip(decoded, toks))
print(f"correction: {correct}/{len(toks)} ticks decoded to the true part "
      f"({correct/len(toks):.1%}); {stats.get('class_unique', 0)} resolved by "
      f"class lookup alone")

# the class of a well-known part, for the record
k = "kw:theorem"
print(f"class of {k}: type {CS.class_type(CS.class_key(ADDR[k]))} "
      f"of Lambda/2Lambda (Monster index space)")
