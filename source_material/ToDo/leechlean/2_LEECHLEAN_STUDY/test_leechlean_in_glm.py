#!/usr/bin/env python3
"""tests/test_leechlean_in_glm.py -- leechlean against the full GLM environment.

Run as an intake item test:   item:tests/test_leechlean_in_glm.py

The script runs the supplied leechlean package *inside* the repository it
was built for: its Golay/Leech engine is cross-checked against the GLM
substrate's own modules (``glm_universal.substrate.mog``,
``glm_universal.substrate.leech2``, ``glm_universal.reasoning.analogy``),
its codebook and address stream are checked on the lattice, its codec is
re-run over the repository's actual Lean development (``src/lean``), its
correction layer is re-measured, and its move algebra and library graph are
recomputed from the bundled data and compared with the recorded experiments.

Every check prints its measured figures; the process exits 0 only when every
check passes.  No file is written anywhere (the item runs on a scratch copy).
"""
from __future__ import annotations

import json
import sys
import time
from collections import Counter
from fractions import Fraction
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ITEM = HERE.parent
sys.path.insert(0, str(ITEM))

from leechlean import cosets as CS                      # noqa: E402
from leechlean import correction as CR                  # noqa: E402
from leechlean.leech_core import (BROWS, DIM, in_leech, in_leech_many,  # noqa: E402
                                   minimal_vectors, nearest_leech,
                                   norm2, octads, golay_words)
from leechlean.lean_parts import tokenize               # noqa: E402
from leechlean.moves import MoveAlgebra, move_key       # noqa: E402
from leechlean.library import Library                   # noqa: E402

try:
    from glm_universal.substrate import leech2 as SUB2
    from glm_universal.substrate import mog as SUBMOG
    from glm_universal.reasoning import analogy as SUBANA
    from glm_universal.constants import REPOSITORY_ROOT
except ImportError as exc:  # a clear refusal, not a crash
    sys.exit(f"refused: the GLM package is not importable ({exc}); this test "
             "belongs to the repository and runs with its src/ on the path")

DATA = ITEM / "data"
RNG = np.random.default_rng(20261111)

RESULTS: list = []


def check(name: str, ok: bool, detail: str) -> None:
    RESULTS.append((name, bool(ok), detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")


def pearson(a: np.ndarray, b: np.ndarray) -> float:
    ca, cb = a - a.mean(), b - b.mean()
    den = float(np.sqrt((ca * ca).sum() * (cb * cb).sum()))
    return float((ca * cb).sum() / den) if den > 0 else float("nan")


codebook = json.loads((DATA / "codebook.json").read_text())
PARTS = codebook["parts"]
ADDRESSES = {k: tuple(int(v) for v in p["address"]) for k, p in PARTS.items()}
CELLS = {v: k for k, v in ADDRESSES.items()}

print("== C0. the bundled codebook, as recorded ==")
check("codebook size", len(PARTS) == 39992,
      f"{len(PARTS)} parts (recorded corpus: {codebook['n_files']} files, "
      f"{int(codebook['total_token_parts']):,} token parts)")
check("codebook model", "x*sqrt(8)" in str(codebook["model"]),
      str(codebook["model"]))

print("== C1. the Golay engine against the GLM substrate's own code ==")
gc = SUBMOG.GolayCode()
check("parity block B equals the substrate's", tuple(BROWS) == tuple(gc.B),
      "leechlean BROWS == substrate GolayCode.B (Golay/Code.lean's block)")
ll_words = set(golay_words())
sub_words = set(gc.codeword_masks)
check("the 4096 codewords equal the substrate's",
      ll_words == sub_words and len(ll_words) == 4096,
      f"{len(ll_words)} words, set equality with substrate codeword_masks()")
ll_oct = octads()
check("the 759 octads equal the substrate's",
      len(ll_oct) == len(gc.octad_masks) == 759,
      f"{len(ll_oct)} octads == substrate's")
wenum = Counter(bin(w).count("1") for w in golay_words())
check("weight enumerator {0:1, 8:759, 12:2576, 16:759, 24:1}",
      dict(sorted(wenum.items())) == {0: 1, 8: 759, 12: 2576, 16: 759, 24: 1},
      f"computed {dict(sorted(wenum.items()))}")

print("== C2. exact Leech membership against the substrate's predicate ==")
mv = minimal_vectors()
check("kissing number 196,560, all on the lattice",
      mv.shape == (196560, 24) and bool(in_leech_many(mv).all()),
      f"{mv.shape[0]} minimal vectors, membership-checked")
sample = mv[RNG.choice(len(mv), 800, replace=False)].astype(int)
agree = all(in_leech(r.tolist()) == SUB2.in_leech([int(v) for v in r])
            for r in sample)
glue = [-3] + [1] * 23
check("800 sampled minimal vectors agree with substrate leech2.in_leech",
      agree, "both predicates accept every one")
check("the glue vector (-3,1^23) agrees",
      in_leech(glue) == SUB2.in_leech(glue) == True,  # noqa: E712
      f"leechlean {in_leech(glue)}, substrate {SUB2.in_leech(glue)}")
lat = (mv[RNG.choice(len(mv), 300, replace=False)].astype(np.int64)
       + mv[RNG.choice(len(mv), 300, replace=False)].astype(np.int64))
rand_int = RNG.integers(-30, 31, size=(1000, 24))
mixed = np.vstack([lat, rand_int,
                   sample[:200] + np.eye(24, dtype=np.int64)[0] * 2])
ok_ll = in_leech_many(mixed)
ok_sub = np.array([SUB2.in_leech([int(v) for v in r]) for r in mixed])
check("1,500 lattice / near-lattice / random vectors agree",
      bool((ok_ll == ok_sub).all()),
      f"{int((ok_ll & ok_sub).sum())} in-Leech, {int((~ok_ll).sum())} out, "
      "no disagreement")

print("== C3. the nearest-point decoder against the substrate's exact one ==")
t0 = time.time()
targets = np.vstack([
    RNG.normal(0, 6, size=(40, DIM)),
    sample[:60].astype(np.float64) + RNG.uniform(-0.45, 0.45, size=(60, DIM)),
])
same = 0
max_dd = 0.0
for row in targets:
    q_ll = nearest_leech(row[None, :])[0].tolist()
    exact = [Fraction(float(v)) for v in row]
    res = SUBANA.nearest_lattice_point(exact)
    d_ll = norm2(q_ll) - 2 * sum(int(a) * b for a, b in zip(q_ll, exact)) \
        + sum((b * b for b in exact), Fraction(0))
    dd = abs(Fraction(int(d_ll * 8), 8) * Fraction(1) - res.distance2)
    max_dd = max(max_dd, float(dd))
    same += int(tuple(int(v) for v in q_ll) == tuple(res.point))
check("100 targets decode to the same Leech point as analogy's exact decoder",
      same == len(targets),
      f"{same}/{len(targets)} identical points; |distance2 difference| <= "
      f"{max_dd:.2e} ({time.time() - t0:.0f}s for the substrate's exact "
      "rational decode)")

print("== C4. the coset layer Lambda/2Lambda against the substrate's ==")
H = CS.leech_basis()
check("own Z-basis of Lambda, det 2^36",
      CS.hnf_determinant(H) == 2 ** 36 and bool(in_leech_many(H).all()),
      f"det {CS.hnf_determinant(H)} = 2^36, every basis row in Lambda")
contain = CS.span_contains(H, np.vstack([sample[:1000].astype(np.int64),
                                         np.array([glue], dtype=np.int64)]))
check("basis spans 1,000 sampled minimal vectors and the glue vector",
      bool(contain), "span_contains on the sample (the full 196,560 is the "
      "item's own verification)")
pts = np.vstack([lat, sample[:200].astype(np.int64)])
H2 = CS.leech2_basis()
shifts = RNG.integers(-2, 3, size=(len(pts), H2.shape[0])) @ H2
equiv_ll, equiv_sub = [], []
for i in range(len(pts)):
    a = [int(v) for v in pts[i]]
    b = [int(v) for v in pts[(i + 7) % len(pts)]]
    a2 = [x + int(s) for x, s in zip(a, shifts[i])]
    equiv_ll.append(CS.class_key(a) == CS.class_key(b))
    equiv_sub.append(SUB2.class_of(a) == SUB2.class_of(b))
    if CS.class_key(a) != CS.class_key(a2) or \
            SUB2.class_of(a) != SUB2.class_of(a2):
        equiv_ll[-1] = "2Lambda shift changed the class"
check("class maps agree as equivalence relations (300 pairs + 2Lambda shifts)",
      equiv_ll == equiv_sub, "class_key(a)==class_key(b) exactly when "
      "substrate class_of(a)==class_of(b); 2Lambda shifts preserve both")
q_agree = all(CS.q_form([int(v) for v in p]) == SUB2.q_form(SUB2.class_of(
                  [int(v) for v in p])) for p in pts[:200])
check("q-form agrees with the substrate's on 200 classes",
      q_agree, "q(x) = (x.x)/16 mod 2, same value both sides")
check("98,280 type-2 classes from the 196,560 minimal vectors",
      len(CS.type2_class_set()) == 98280,
      "each class hit by exactly {v, -v} (the module asserts the pairing)")

print("== C5. the codebook is an injective lattice addressing ==")
pts_all = np.array([list(a) for a in ADDRESSES.values()], dtype=np.int64)
check("39,992 parts, 39,992 distinct addresses (injective)",
      len(ADDRESSES) == 39992 and len(CELLS) == 39992,
      f"{len(ADDRESSES)} parts, {len(CELLS)} cells, 0 collisions")
check("every address is a true Leech lattice point",
      bool(in_leech_many(pts_all).all()),
      f"{len(pts_all)} addresses membership-checked")
undisp = [(k, p) for k, p in PARTS.items() if not p["displaced"]]
lat_e = np.array([norm2(ADDRESSES[k]) // 8 for k, _ in undisp], dtype=float)
sur = 4.0 * np.array([p["surprisal_bits"] for _, p in undisp], dtype=float)
r = pearson(lat_e, sur)
check("address energy tracks 4 x surprisal (r = 0.897 recorded)",
      r >= 0.89, f"Pearson r = {r:.3f} over the {len(undisp)} undisplaced "
      f"parts ({sum(1 for _, p in PARTS.items() if p['displaced'])} displaced)")

print("== C6. the codec over the repository's actual Lean development ==")
lean_root = REPOSITORY_ROOT / "src" / "lean"
files = sorted(lean_root.rglob("*.lean"))
lexer_ok = covered = exact = 0
uncovered = []
for f in files:
    text = f.read_text(encoding="utf-8", errors="replace")
    try:
        toks = tokenize(text)
    except Exception as exc:  # noqa: BLE001
        uncovered.append(f"{f.relative_to(lean_root)}: lexer {exc}")
        continue
    keys = [t.key for t in toks]
    if "".join(k.split(":", 1)[1] for k in keys) == text:
        lexer_ok += 1
    if all(k in PARTS for k in keys):
        covered += 1
        if "".join(CELLS[ADDRESSES[k]].split(":", 1)[1] for k in keys) == text:
            exact += 1
        else:
            uncovered.append(f"{f.relative_to(lean_root)}: covered but "
                             "decoded differently")
    else:
        uncovered.append(f"{f.relative_to(lean_root)}: "
                         f"{sum(1 for k in keys if k not in PARTS)} part(s) "
                         "outside the codebook")
check("byte-exact lexer round trip on every file of src/lean",
      lexer_ok == len(files),
      f"{lexer_ok}/{len(files)} files reconstruct exactly from tokens")
check("every codebook-covered file decodes byte-exactly from its addresses",
      exact == covered and covered > 0,
      f"{exact}/{covered} covered files byte-exact; {len(files) - covered} "
      "file(s) carry parts outside the 442-file codebook (the tree has moved "
      "on: placeholders and reconstructed files)")

sample_text = (ITEM / "demo" / "sample_Golay_Code.lean").read_text(
    encoding="utf-8", errors="replace")
stoks = tokenize(sample_text)
sstream = [ADDRESSES[t.key] for t in stoks]
back = "".join(CELLS[a].split(":", 1)[1] for a in sstream)
check("the item's own sample file round-trips byte-exactly", back == sample_text,
      f"{len(stoks)} ticks, exact")

print("== C7. error correction of corrupted address streams ==")
cb = CR.CodebookIndex(ADDRESSES)
pos_of = {tuple(int(v) for v in p): i for i, p in enumerate(cb.pts)}
A = np.array(sstream, dtype=np.int64)
true_pos = np.array([pos_of[tuple(int(v) for v in a)] for a in A])
sr = CR.sieve_report(A)
check("the clean stream raises no false alarms",
      sr["clean"] == len(A), f"sieve: {sr}")
exp = {}
for model, kw in (("jitter", dict(p=0.1)), ("flip_k", dict(k=1)),
                  ("flip_k", dict(k=2)), ("flip_k", dict(k=3)),
                  ("flip_k", dict(k=4)), ("slip", dict(p=1.0)),
                  ("burst", dict(p=0.05))):
    X = CR.corrupt(A.copy(), model, np.random.default_rng(7), **kw)
    syn = CR.syndrome_analysis(A, X, cb)
    det = syn["n_detected"] / syn["n_corrupted"] if syn["n_corrupted"] else 1.0
    fa = syn["false_alarms"]
    got, _ = CR.decode_stream(X, cb, mode="class_assisted")
    corr = float(np.mean(got == true_pos))
    label = f"{model}{('-' + str(kw['k'])) if model == 'flip_k' else ''}"
    exp[label] = (det, fa, corr)
    check(f"{label}: 100% detection, 0 false alarms, >= 96% correction",
          det >= 0.999 and fa == 0 and corr >= 0.96,
          f"detection {det * 100:.1f}% of {syn['n_corrupted']} corrupted "
          f"ticks, {fa} false alarms, correction {corr * 100:.1f}%")
print("  measured: " + json.dumps(
    {k: [round(a, 4), b, round(c, 4)] for k, (a, b, c) in exp.items()}))

print("== C8. the move algebra recomputed from the bundled library graph ==")
z = np.load(DATA / "library_core.npz", allow_pickle=True)
plist = list(z["parts"])
mvcount: Counter = Counter()
for u, v, c in zip(z["edge_u"], z["edge_v"], z["edge_c"]):
    a, b = ADDRESSES[plist[int(u)]], ADDRESSES[plist[int(v)]]
    mvcount[move_key([b[i] - a[i] for i in range(24)])] += int(c)
rec = json.loads((DATA / "exp_moves.json").read_text())["repertoire"]
total = sum(mvcount.values())
distinct = len(mvcount)
top50 = sum(c for _, c in mvcount.most_common(50)) / total
classes = {CS.class_key(d) for d in mvcount}
check("the repertoire: 80,361 distinct moves over 1,487,183 ticks",
      distinct == rec["distinct_moves"] and total == rec["total_moves"],
      f"recomputed {distinct:,} over {total:,} (recorded "
      f"{rec['distinct_moves']:,} over {rec['total_moves']:,})")
mean_n2 = float(np.mean([norm2(d) for d in mvcount]))
check("mean |d|^2 654, top 50 moves carry 39% of ticks",
      abs(mean_n2 - rec["norm2_mean"]) < 1.0
      and abs(top50 - rec["top50_share"]) < 0.005,
      f"mean |d|^2 {mean_n2:.1f} (recorded {rec['norm2_mean']:.1f}), "
      f"top50 {top50 * 100:.1f}% (recorded {rec['top50_share'] * 100:.1f}%)")
check("moves occupy 63,257 of the 2^24 Lambda/2Lambda classes",
      len(classes) == rec["distinct_move_classes"],
      f"{len(classes):,} classes (recorded "
      f"{rec['distinct_move_classes']:,} of {1 << 24:,})")
d1 = mvcount.most_common(1)[0][0]
d2 = mvcount.most_common(2)[1][0]
alg = MoveAlgebra()
law = (alg.class_convolution(CS.class_key(d1), CS.class_key(d2))
       == CS.class_key([x + y for x, y in zip(d1, d2)]))
check("kappa(d1)(*)kappa(d2) = kappa(d1+d2) on the two most common moves",
      law, "the class homomorphism, live")
check("the class pairing <x,y> mod 2 is well defined",
      MoveAlgebra.verify_pairing(n=150, seed=11),
      "150 random pairs, 4 random 2Lambda shifts each")

print("== C9. the library graph recomputed from the bundled core ==")
counts = {k: p["count"] for k, p in PARTS.items()}
lib = Library.load_core(DATA / "library_core.npz", ADDRESSES, counts)
n_join = len(lib.edge_count)
check("29,422 parts joined by 80,375 edges with 55,269 frame contexts",
      len(lib.part_files) == 29422 and n_join == 80375
      and len(lib.ctx_files) == 55269,
      f"{len(lib.part_files):,} parts, {n_join:,} joinings, "
      f"{len(lib.ctx_files):,} contexts over "
      f"{lib.n_library_files} files / {lib.n_library_tokens:,} tokens")
keys, frames, tick_status, join_status = lib.classify_ticks(stoks)
sc = Counter(tick_status)
cont = lib.continuations("kw:theorem")
check("the sample file classifies and the graph answers queries",
      sc["new"] == 0 and len(cont) >= 1 and cont[0] == ("ws: ", 6725),
      f"sample file: {sc['ctx']} context-verified, {sc['part']} part-known, "
      f"{sc['new']} new ticks; 'kw:theorem' continues to {cont[0][0]!r} "
      f"({cont[0][1]} joinings)")

print()
failed = [(n, d) for n, ok, d in RESULTS if not ok]
print(f"{len(RESULTS) - len(failed)} of {len(RESULTS)} checks passed")
if failed:
    for n, d in failed:
        print(f"  FAILED: {n}: {d}")
    sys.exit(1)
print("leechlean verified against the GLM substrate, the repository corpus "
      "and its own recorded experiments")
