#!/usr/bin/env python3
"""
Runnable mirror of the machine-checked system in RequestProject/*.lean.

No external dependencies, no randomness, no XOR-as-composition, no hashing.
Everything here is a re-implementation in Python of definitions that are proved
correct in Lean:

  Semantics.lean    -> World, evalAtom, entails, speak            (soundness proved)
  Chat.lean         -> answer, render                              (cannot lie: proved)
  ThreeCube.lean    -> rule A / Turyn glue                         (distance 8: proved)
  SentenceCode.lean -> clauseCode                                  (3-cell repair: proved)
  IntegerCube.lean  -> two's-complement dimension records          (precision 1.0: proved)

The numbers this script prints are the same numbers that appear as theorems in
the Lean files; if it prints something different, the Python is wrong, not the
Lean.  Run:  python3 glm_chat2.py
"""

from itertools import product

# ──────────────────────────────────────────────────────────────────────────
# 1. The measurable micro-world  (Semantics.lean §1)
# ──────────────────────────────────────────────────────────────────────────

ENTS = ["water", "stone", "lamp"]
TEMP_SCALE = [-10, 0, 20, 100]      # °C
MASS_SCALE = [1, 10]                # kg

# a world is (temp index per entity, mass index per entity)
ALL_WORLDS = [
    (t, m)
    for t in product(range(4), repeat=3)
    for m in product(range(2), repeat=3)
]

def temp(w, e):
    return TEMP_SCALE[w[0][ENTS.index(e)]]

def mass(w, e):
    return MASS_SCALE[w[1][ENTS.index(e)]]

# ──────────────────────────────────────────────────────────────────────────
# 2. Atoms: truth is measurement  (Semantics.lean §2)
# ──────────────────────────────────────────────────────────────────────────

def all_atoms():
    # exactly Semantics.allAtoms: all "frozen", then all "boiling", … then the
    # two relations; the order matters because the system answers with the
    # first reason it finds.
    out = []
    for k in ("frozen", "boiling", "warm", "heavy"):
        out += [(k, e) for e in ENTS]
    out += [("hotter", e, f) for e in ENTS for f in ENTS]
    out += [("heavier", e, f) for e in ENTS for f in ENTS]
    return out

ATOMS = all_atoms()

def eval_atom(a, w):
    k = a[0]
    if k == "frozen":   return temp(w, a[1]) <= 0
    if k == "boiling":  return temp(w, a[1]) >= 100
    if k == "warm":     return 0 < temp(w, a[1]) < 100
    if k == "heavy":    return mass(w, a[1]) >= 10
    if k == "hotter":   return temp(w, a[2]) < temp(w, a[1])
    if k == "heavier":  return mass(w, a[2]) < mass(w, a[1])
    raise ValueError(a)

# a literal is (atom, polarity)
LITS = [(a, p) for a in ATOMS for p in (True, False)]

def eval_lit(l, w):
    return eval_atom(l[0], w) == l[1]

def neg(l):
    return (l[0], not l[1])

def satisfiable(l):
    return any(eval_lit(l, w) for w in ALL_WORLDS)

def contingent(l):
    return satisfiable(l) and satisfiable(neg(l))

USEFUL = [l for l in LITS if contingent(l)]

def entails(l, m):
    return all((not eval_lit(l, w)) or eval_lit(m, w) for w in ALL_WORLDS)

def entails2(m, n, l):
    return all((not (eval_lit(m, w) and eval_lit(n, w))) or eval_lit(l, w)
               for w in ALL_WORLDS)

# ──────────────────────────────────────────────────────────────────────────
# 3. Actions and the world after them  (Semantics.lean §2)
# ──────────────────────────────────────────────────────────────────────────

UP_T = [1, 2, 3, 3]
DOWN_T = [0, 0, 1, 2]

def step(act, w):
    kind, e = act
    i = ENTS.index(e)
    t, m = list(w[0]), list(w[1])
    if kind == "heat":   t[i] = UP_T[t[i]]
    elif kind == "cool": t[i] = DOWN_T[t[i]]
    elif kind == "load": m[i] = 1
    else: raise ValueError(act)
    return (tuple(t), tuple(m))

ACTS = [(k, e) for k in ("heat", "cool", "load") for e in ENTS]

# ──────────────────────────────────────────────────────────────────────────
# 4. Sentences and what the system will say  (Semantics.lean §3-4)
# ──────────────────────────────────────────────────────────────────────────

def law_ok(l, m):
    return entails(l, m) and contingent(l) and contingent(m) and l != m

def lit_idx(l):
    return 2 * ATOMS.index(l[0]) + (0 if l[1] else 1)

def canonical_law(l, m):
    return 100 * lit_idx(l) + lit_idx(m) <= 100 * lit_idx(neg(m)) + lit_idx(neg(l))

def eval_sent(s, w):
    k = s[0]
    if k == "lit":      return eval_lit(s[1], w)
    if k == "law":      return law_ok(s[1], s[2])
    if k == "because":
        l, m = s[1], s[2]
        return (eval_lit(l, w) and eval_lit(m, w) and entails(m, l)
                and l != m and contingent(l))
    if k == "because2":
        l, m, n = s[1], s[2], s[3]
        return (eval_lit(l, w) and eval_lit(m, w) and eval_lit(n, w)
                and entails2(m, n, l) and l != m and l != n and m != n
                and contingent(l) and not entails(m, l) and not entails(n, l))
    if k == "after":    return eval_lit(s[2], step(s[1], w))
    if k == "conj":     return eval_sent(s[1], w) and eval_sent(s[2], w)
    raise ValueError(s)

def speak(w):
    lits = [("lit", l) for l in USEFUL if eval_lit(l, w)]
    laws = [("law", l, m) for l in USEFUL for m in USEFUL
            if law_ok(l, m) and canonical_law(l, m)]
    becs = [("because", l, m) for l in USEFUL for m in USEFUL
            if eval_sent(("because", l, m), w)]
    afts = [("after", c, l) for c in ACTS for l in USEFUL
            if eval_lit(l, step(c, w)) and not eval_lit(l, w)]
    return lits, laws, becs, afts

# ──────────────────────────────────────────────────────────────────────────
# 5. The chat  (Chat.lean)
# ──────────────────────────────────────────────────────────────────────────

def reason_for(l, w):
    for m in USEFUL:
        if eval_sent(("because", l, m), w):
            return m
    return None

def reason_pair_for(l, w):
    for m in USEFUL:
        for n in USEFUL:
            if eval_sent(("because2", l, m, n), w):
                return (m, n)
    return None

def answer(q, w):
    k = q[0]
    if k == "isIt":
        a = q[1][0]
        return ("lit", (a, eval_atom(a, w)))
    if k == "why":
        l = q[1]
        if not eval_lit(l, w):
            return ("lit", (l[0], eval_atom(l[0], w)))
        m = reason_for(l, w)
        if m is not None:
            return ("because", l, m)
        p = reason_pair_for(l, w)
        if p is not None:
            return ("because2", l, p[0], p[1])
        return ("lit", l)
    if k == "whatIf":
        c, a = q[1], q[2]
        return ("after", c, (a, eval_atom(a, step(c, w))))
    if k == "compare":
        e, f = q[1], q[2]
        if eval_atom(("hotter", e, f), w):
            return ("lit", (("hotter", e, f), True))
        if eval_atom(("hotter", f, e), w):
            return ("lit", (("hotter", f, e), True))
        return ("conj", ("lit", (("hotter", e, f), False)),
                        ("lit", (("hotter", f, e), False)))
    if k == "tellMe":
        e = q[1]
        parts = [("lit", ((p, e), eval_atom((p, e), w)))
                 for p in ("frozen", "boiling", "warm", "heavy")]
        s = parts[-1]
        for p in reversed(parts[:-1]):
            s = ("conj", p, s)
        return s
    raise ValueError(q)

# ── English ───────────────────────────────────────────────────────────────

def r_ent(e):
    return "the " + e

def r_lit(l):
    a, p = l
    neg_s = " is " if p else " is not "
    if a[0] in ("frozen", "boiling", "warm", "heavy"):
        return r_ent(a[1]) + neg_s + a[0]
    if a[0] == "hotter":
        return r_ent(a[1]) + neg_s + "hotter than " + r_ent(a[2])
    if a[0] == "heavier":
        return r_ent(a[1]) + neg_s + "heavier than " + r_ent(a[2])
    raise ValueError(l)

def r_lit_q(l):
    a, p = l
    neg_s = " " if p else " not "
    if a[0] in ("frozen", "boiling", "warm", "heavy"):
        return "is " + r_ent(a[1]) + neg_s + a[0]
    if a[0] == "hotter":
        return "is " + r_ent(a[1]) + neg_s + "hotter than " + r_ent(a[2])
    if a[0] == "heavier":
        return "is " + r_ent(a[1]) + neg_s + "heavier than " + r_ent(a[2])
    raise ValueError(l)

def r_act(c):
    return "we " + c[0] + " " + r_ent(c[1])

def render(s):
    k = s[0]
    if k == "lit":      return r_lit(s[1])
    if k == "law":      return "if " + r_lit(s[1]) + " then " + r_lit(s[2])
    if k == "because":  return r_lit(s[1]) + " because " + r_lit(s[2])
    if k == "because2": return (r_lit(s[1]) + " because " + r_lit(s[2])
                                + " and " + r_lit(s[3]))
    if k == "after":    return "after " + r_act(s[1]) + ", " + r_lit(s[2])
    if k == "conj":     return render(s[1]) + ", and " + render(s[2])
    raise ValueError(s)

def render_q(q):
    k = q[0]
    if k == "isIt":    return r_lit_q(q[1]) + "?"
    if k == "why":     return "why " + r_lit_q(q[1]) + "?"
    if k == "whatIf":  return "if " + r_act(q[1]) + ", " + r_lit_q((q[2], True)) + "?"
    if k == "compare": return ("which is hotter, " + r_ent(q[1]) + " or "
                               + r_ent(q[2]) + "?")
    if k == "tellMe":  return "tell me about " + r_ent(q[1])
    raise ValueError(q)

# ──────────────────────────────────────────────────────────────────────────
# 6. The three cubes and the clause record  (ThreeCube.lean, SentenceCode.lean)
# ──────────────────────────────────────────────────────────────────────────

VERTS = list(product([0, 1], repeat=3))
SIGMA = [0, 1, 2, 4, 3, 6, 7, 5]

def affine(c0, c1, c2, c3):
    return tuple((c0 + c1 * v[0] + c2 * v[1] + c3 * v[2]) % 2 for v in VERTS)

def cube_of_nat(k):
    return affine(k % 2, (k // 2) % 2, (k // 4) % 2, (k // 8) % 2)

def turyn(a, b, x):
    xs = tuple(x[SIGMA[i]] for i in range(8))
    c0 = tuple((a[i] + xs[i]) % 2 for i in range(8))
    c1 = tuple((b[i] + xs[i]) % 2 for i in range(8))
    c2 = tuple((a[i] + b[i] + xs[i]) % 2 for i in range(8))
    return c0 + c1 + c2

PRED_IDX = {"frozen": 0, "boiling": 1, "warm": 2, "heavy": 3, "hotter": 4, "heavier": 5}

def clause_code(l):
    a, p = l
    subj = ENTS.index(a[1]) + (0 if p else 8)
    pred = PRED_IDX[a[0]]
    obj = (ENTS.index(a[2]) + 1) if a[0] in ("hotter", "heavier") else 0
    return turyn(cube_of_nat(subj), cube_of_nat(pred), cube_of_nat(obj))

def dist(u, v):
    return sum(1 for i in range(24) if u[i] != v[i])

# ──────────────────────────────────────────────────────────────────────────
# 7. The integer dimension record  (IntegerCube.lean)
# ──────────────────────────────────────────────────────────────────────────

DIMS = {
    "length": (1, 0, 0, 0, 0, 0), "mass": (0, 1, 0, 0, 0, 0),
    "time": (0, 0, 1, 0, 0, 0), "current": (0, 0, 0, 1, 0, 0),
    "velocity": (1, 0, -1, 0, 0, 0), "acceleration": (1, 0, -2, 0, 0, 0),
    "force": (1, 1, -2, 0, 0, 0), "energy": (2, 1, -2, 0, 0, 0),
    "action": (2, 1, -1, 0, 0, 0), "momentum": (1, 1, -1, 0, 0, 0),
    "power": (2, 1, -3, 0, 0, 0), "charge": (0, 0, 1, 1, 0, 0),
}

def enc_int(v):
    """Face j carries exponent j as four two's-complement cells."""
    cells = []
    for e in v:
        u = e % 16
        cells += [(u >> i) & 1 for i in range(4)]
    return tuple(cells)

def enc_parity(v):
    """The older encoding: one parity bit per dimension."""
    return tuple(e % 2 for e in v)

def phrases():
    base = [(k, DIMS[k]) for k in DIMS]
    prods = [(f"{p[0]}*{q[0]}", tuple(a + b for a, b in zip(p[1], q[1])))
             for p in base for q in base]
    return base + prods

# ──────────────────────────────────────────────────────────────────────────
# 8. Run everything and print the numbers
# ──────────────────────────────────────────────────────────────────────────

DEMO_WORLD = ((0, 2, 3), (0, 1, 0))   # water -10 °C 1 kg, stone 20 °C 10 kg, lamp 100 °C 1 kg

DEMO_QUESTIONS = [
    ("tellMe", "water"),
    ("isIt", (("frozen", "water"), True)),
    ("isIt", (("warm", "water"), True)),
    ("why", (("warm", "water"), False)),
    ("why", (("frozen", "water"), True)),
    ("why", (("boiling", "lamp"), True)),
    ("compare", "water", "lamp"),
    ("compare", "water", "stone"),
    ("whatIf", ("heat", "water"), ("warm", "water")),
    ("whatIf", ("heat", "lamp"), ("boiling", "lamp")),
    ("whatIf", ("load", "water"), ("heavy", "water")),
    ("isIt", (("heavier", "stone", "water"), True)),
    ("why", (("heavier", "stone", "water"), True)),
    ("why", (("heavy", "water"), True)),
]

def main():
    print("=" * 72)
    print("worlds:", len(ALL_WORLDS), " atoms:", len(ATOMS),
          " contingent literals:", len(USEFUL))

    lits, laws, becs, afts = speak(DEMO_WORLD)
    print("\nwhat the system will say about the demo world")
    print(f"  measured reports : {len(lits)}   (Lean: 24)")
    print(f"  laws             : {len(laws)}   (Lean: 39)")
    print(f"  explanations     : {len(becs)}   (Lean: 30)")
    print(f"  predictions      : {len(afts)}   (Lean: 14)")
    print(f"  total            : {len(lits)+len(laws)+len(becs)+len(afts)}   (Lean: 107)")
    print("  all true in the world:",
          all(eval_sent(s, DEMO_WORLD) for s in lits + laws + becs + afts))

    print("\nsample laws")
    for s in laws[:5]:
        print("   ", render(s))

    print("\ntranscript")
    for q in DEMO_QUESTIONS:
        a = answer(q, DEMO_WORLD)
        assert eval_sent(a, DEMO_WORLD), "the system said something false"
        print(f"  > {render_q(q)}")
        print(f"    {render(a)}")

    single = sum(1 for l in USEFUL
                 if reason_for((l[0], eval_atom(l[0], DEMO_WORLD)), DEMO_WORLD) is not None)
    pair = 0
    none = 0
    for l in USEFUL:
        lt = (l[0], eval_atom(l[0], DEMO_WORLD))
        if reason_for(lt, DEMO_WORLD) is None:
            if reason_pair_for(lt, DEMO_WORLD) is not None:
                pair += 1
            else:
                none += 1
    print(f"\nwhy-questions: {single} single reasons, {pair} pair reasons, "
          f"{none} unexplained   (Lean: 32 / 16 / 0)")

    codes = {l: clause_code(l) for l in LITS}
    dmin = min(dist(codes[l], codes[m]) for l in LITS for m in LITS if l != m)
    print(f"\nclause records: {len(set(codes.values()))} distinct out of {len(LITS)}; "
          f"minimum distance {dmin}   (Lean: 60 distinct, distance >= 8)")
    print(f"  -> any {(dmin - 1) // 2} damaged cells still decode uniquely")

    ph = phrases()
    pairs = [(p, q) for p in ph for q in ph if p[0] != q[0]]
    true_eqs = [(p, q) for p, q in pairs if p[1] == q[1]]
    par_acc = [(p, q) for p, q in pairs if enc_parity(p[1]) == enc_parity(q[1])]
    int_acc = [(p, q) for p, q in pairs if enc_int(p[1]) == enc_int(q[1])]
    print(f"\ndimension experiment on {len(ph)} phrases   (Lean: 156)")
    print(f"  dimensionally true equations : {len(true_eqs)}   (Lean: 356)")
    print(f"  parity cube accepts          : {len(par_acc)}   (Lean: 1758)"
          f"  -> precision {len(true_eqs)/len(par_acc):.2f}")
    print(f"  integer cube accepts         : {len(int_acc)}   (Lean: 356)"
          f"  -> precision {len(true_eqs)/len(int_acc):.2f}")
    print("=" * 72)


if __name__ == "__main__":
    main()
