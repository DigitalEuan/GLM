#!/usr/bin/env python3
"""Demo: the happening between addresses -- the algebra of moves.

Run:  python3 demo/demo_moves.py

Between two addressed parts there is a move d = B - A: a Leech lattice
vector.  This demo makes the algebra of moves concrete:

  1. THE REPERTOIRE.  From the bundled library graph (data/library_core.npz:
     every consecutive-tick joining of the 442-file corpus with counts) and
     the codebook addresses, the corpus's 80,361 distinct moves are derived
     with their |d|^2 and Lambda/2Lambda classes.  Moves are shorter than
     random part pairs, the top 50 carry 39% of all ticks, and the most
     common happenings are the micro-syntax gestures of Lean.

  2. THE INDEX SPACE.  Every move projects to its class in Lambda/2Lambda
     (the homomorphism kappa, verified: kappa(d1 + d2) = kappa(d1)(*)
     kappa(d2), classes composed by reduction of the sum).  The corpus's
     moves occupy 63,257 of the 2^24 classes -- the library walks in a tiny
     corner of index space.  The class pairing <x,y> mod 2 (the natural
     scalar product on Lambda/2Lambda, well defined because Lambda is
     doubly even) is verified live.

  3. THE JOURNEY OF A PROOF.  A real theorem from the bundled sample file
     (syn_eq_iff_isCodeword_symmDiff) is walked tick by tick: energy
     profile, per-move |d|^2 coloured by class type, statement/proof
     boundary, net displacement and tortuosity -- with the corpus-wide
     journey statistics from data/exp_moves.json alongside.

  4. DOES IT HELP BUILD?  The model head-to-head from the experiment
     record: predicting the next MOVE beats predicting the next part
     (45.8% vs 40.6% greedy top-1, leave-one-file-out) -- the happening is
     the more predictable primitive.
"""
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from leechlean.cosets import class_key, class_type
from leechlean.lean_parts import DECL_KW, tokenize, structural
from leechlean.moves import MoveAlgebra, move_key

codebook = json.load(open(HERE.parent / "data/codebook.json"))
PARTS = codebook["parts"]
ADDRESSES = {k: tuple(p["address"]) for k, p in PARTS.items()}
exp = json.load(open(HERE.parent / "data/exp_moves.json"))

# ---------------------------------------------------------------- 1. repertoire
z = np.load(HERE.parent / "data/library_core.npz", allow_pickle=True)
plist = list(z["parts"])
mv = Counter()
examples = {}
for u, v, c in zip(z["edge_u"], z["edge_v"], z["edge_c"]):
    a, b = ADDRESSES[plist[int(u)]], ADDRESSES[plist[int(v)]]
    d = move_key([b[i] - a[i] for i in range(24)])
    mv[d] += int(c)
    examples.setdefault(d, (plist[int(u)], plist[int(v)]))
rep = exp["repertoire"]
print(f"the repertoire: {rep['distinct_moves']:,} distinct moves over "
      f"{rep['total_moves']:,} ticks")
print(f"  mean |d|^2 {rep['norm2_mean']:.0f}, median "
      f"{rep['norm2_median']:.0f}  --  random part pairs: "
      f"{rep['null_norm2_mean']:.0f}")
print(f"  top 50 moves carry {rep['top50_share']*100:.0f}% of all ticks")
print("  the most frequent happenings:")
for d, c in mv.most_common(6):
    a, b = examples[d]
    print(f"    {c:7,}x  |d|^2 {sum(x*x for x in d):4}  "
          f"type {class_type(class_key(d))}   {a[:14]!r} -> {b[:14]!r}")

# ---------------------------------------------------------------- 2. index space
print(f"\nthe index space: moves occupy {rep['distinct_move_classes']:,} "
      f"of 2^24 = {1<<24:,} Lambda/2Lambda classes "
      f"({rep['moves_per_class_mean']:.2f} moves per occupied class)")
tc = rep["class_type_census"]["by_move_count"]
print(f"  class types of moves: type 2 (minimal-vector classes, the X_r "
      f"basis of the Griess algebra): {tc.get('2',0)}, type 3 (q=1): "
      f"{tc.get('3',0)}, type 4 (frames): {tc.get('4',0)}")
ok_pair = MoveAlgebra.verify_pairing(n=150, seed=11)
print(f"  class pairing <x,y> mod 2 well defined on Lambda/2Lambda: "
      f"{ok_pair}")
# the group law, live on the two most common moves
d1 = mv.most_common(1)[0][0]
d2 = mv.most_common(2)[1][0]
alg = MoveAlgebra()
kc = alg.class_convolution(class_key(d1), class_key(d2))
assert kc == class_key([x + y for x, y in zip(d1, d2)])
print(f"  class law verified live: kappa(d1)(*)kappa(d2) = kappa(d1+d2) "
      f"on the corpus's two most common moves")
print(f"  (classes compose by reduction of the sum -- the group algebra of "
      f"the {1<<24:,}-class index space)")

# ---------------------------------------------------------------- 3. a journey
text = (HERE / "sample_Golay_Code.lean").read_text(encoding="utf-8",
                                                   errors="replace")
toks = tokenize(text)
A = np.array([ADDRESSES[t.key] for t in toks], dtype=np.int64)
st = structural(toks)
starts = [i for i, (_, t) in enumerate(st)
          if t.kind == "kw" and t.text in DECL_KW and t.col == 0]
st_idx = [i for i, _ in st]
ni = next(i for i, s in enumerate(starts)
          if toks[st_idx[s]].text == "theorem" and
          any(t.key == "ident:syn_eq_iff_isCodeword_symmDiff"
              for t in toks[st_idx[s]:st_idx[s] + 4]))
lo = st_idx[starts[ni]]
hi = st_idx[starts[ni + 1]] if ni + 1 < len(starts) else len(toks)
As = A[lo:hi]
eq = next(j for j in range(lo, hi)
          if toks[j].kind == "sym" and toks[j].text == ":=")
E = (As * As).sum(axis=1) / 8.0
Dv = As[1:] - As[:-1]
dn2 = (Dv * Dv).sum(axis=1)
types = [class_type(class_key(d)) for d in Dv.tolist()]
net = As[-1] - As[0]
print(f"\nthe journey of a proof: syn_eq_iff_isCodeword_symmDiff "
      f"({len(As)} ticks, statement {eq-lo} + proof {hi-eq})")
print(f"  energy: statement mean {E[:eq-lo].mean():.0f} -> proof mean "
      f"{E[eq-lo:].mean():.0f} lattice units")
print(f"  moves: mean |d|^2 {dn2.mean():.0f}; class types "
      f"{dict(Counter(types))}")
print(f"  net displacement |A_end - A_0|^2 = {int((net*net).sum())} -- "
      f"shorter than one AVERAGE corpus move (654): proofs return closer "
      f"than they wander (this proof's own moves average {dn2.mean():.0f})")
print(f"  tortuosity path^2/net^2 = {dn2.sum()/max(int((net*net).sum()),1):.1f} "
      f"-- the corpus median for theorem|by is "
      f"{exp['journeys']['by_shape']['theorem|by']['median_tortuosity']:.1f} "
      f"(shuffled control "
      f"{exp['journeys']['by_shape']['theorem|by']['median_ctrl_tortuosity']:.1f})")
print("  the proof's first moves, as a word in the repertoire:")
words = []
loc_eq = eq - lo
for j in range(loc_eq + 1, min(loc_eq + 9, len(As) - 1)):
    d = move_key(As[j + 1] - As[j])
    known = "known" if d in mv else "NEW"
    words.append(f"|d|^2 {sum(x*x for x in d):4} ({known})")
print("    " + "  ".join(words[:4]))
print("    " + "  ".join(words[4:]))

# ---------------------------------------------------------------- 4. models
print("\ndoes the move algebra help build?  greedy top-1, leave-one-file-out:")
for k, label in [("part_bigram", "predict the next PART (baseline)"),
                 ("move_bigram", "predict the next MOVE"),
                 ("class_bigram", "predict the next CLASS"),
                 ("class_first_hybrid_k8", "class-first, then part")]:
    m = exp["models"][k]
    print(f"  {m['acc']*100:5.1f}%  {label}")
print("  the happening between addresses is the more predictable primitive.")
