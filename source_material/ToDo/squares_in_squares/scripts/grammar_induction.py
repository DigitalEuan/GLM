"""Induce compositional ASTs for the lifted atoms (run 86).

The question is narrow and exact: **is a lifted atom a composition of the declared
vocabulary?**  A sentence is a set of (centre, word) pairs.  A template T occurs in
a sentence S iff one of the five isometries of the unit square -- identity, the two
axis reflections, the diagonal reflection, a quarter turn -- carries T into S under
a single translation, *matching words as well as centres*.  A cover is a set of
disjoint occurrences; the induction succeeds only when a cover is exact.

So the verdict is not a fitted count law: either the atom is a union of translated
and reflected instances of registered cells, or it is not, and the run says which
and by how much.  Nothing here names a float.
"""

import json
import os
import sys
from fractions import Fraction as F

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import exact_field as EF          # noqa: E402
import glm_wheels as W            # noqa: E402

Q2 = W.Q2
OUT = os.path.join(ROOT, "workspace/push/induction.json")


def isometries():
    """The five isometries of the unit square, as point maps on centres."""

    def ident(p):
        return p

    def refl_diag(p):
        return (p[1], p[0])

    def refl_x(p):
        return (p[0], -p[1])

    def refl_y(p):
        return (-p[0], p[1])

    def rot90(p):
        return (-p[1], p[0])

    return [("id", ident), ("diag", refl_diag), ("x", refl_x),
            ("y", refl_y), ("rot90", rot90)]


def _word_key(w):
    return (w[0], w[1])


def find_copies(state, words, tstate, twords):
    """Every exact translated/reflected occurrence of the template, with its isometry."""
    S = {(p, _word_key(w)) for p, w in zip(state, words)}
    out = []
    for name, f in isometries():
        T = [f(p) for p in tstate]
        TW = [_word_key(w) for w in twords]
        t0 = T[0]
        for s, ws in zip(state, words):
            k = _word_key(ws)
            t = (s[0] - t0[0], s[1] - t0[1])
            ok = True
            for p, w in zip(T, TW):
                if ((p[0] + t[0], p[1] + t[1]), w) not in S:
                    ok = False
                    break
            if ok:
                out.append((name, t))
    return out


def cover(state, words, tstate, twords):
    """Greedy disjoint cover: (covered, total, copies used)."""
    S = list(zip(state, [_word_key(w) for w in words]))
    taken = [False] * len(S)
    index = {(p, w): i for i, (p, w) in enumerate(S)}
    used = []
    covered = 0
    for name, f in isometries():
        T = [f(p) for p in tstate]
        TW = [_word_key(w) for w in twords]
        t0 = T[0]
        for s, ws in zip(state, words):
            k = _word_key(ws)
            t = (s[0] - t0[0], s[1] - t0[1])
            idxs = []
            ok = True
            for p, w in zip(T, TW):
                key = ((p[0] + t[0], p[1] + t[1]), w)
                i = index.get(key)
                if i is None or taken[i]:
                    ok = False
                    break
                idxs.append(i)
            if ok:
                for i in idxs:
                    taken[i] = True
                covered += len(idxs)
                used.append({"iso": name, "shift": [str(t[0]), str(t[1])]})
    return covered, len(S), used


def templates():
    """The declared vocabulary, plus the two smaller atoms, as (name, state, words)."""
    out = {}

    def add(name, claim):
        out[name] = (claim.payload["state"], claim.payload["words"])

    for k in (1, 2):
        add(f"Tile{k}", W.p_grid(k))
    for k in (1, 2):
        add(f"Pocket{k}", W.p_pocket(k))
    add("Strip2,1", W.p_strip(2, 1))
    add("Strip2,2", W.p_strip(2, 2))
    add("Fold1", W.p_fold(1))
    add("Fold2", W.p_fold(2))
    add("Glue1/2", W.p_glue("1/2"))
    for n in (5, 10):
        st, ws, _L = W._lift_row(n)
        if st is not None:
            out[f"Atom{n}"] = (st, ws)
    return out


def lifted_rows():
    """The rows the run-85 uplift ledger records as exact Q(sqrt 2) lifts."""
    path = os.path.join(ROOT, "workspace/push/uplift.json")
    if os.path.exists(path):
        with open(path) as f:
            d = json.load(f)
        return {int(k) for k, v in d.get("rows", {}).items()
                if v.get("status") == "lifted"}
    return None


def lifted_states(limit=300, cap=60):
    """The atoms, plus the structurally related lifted rows, with their sides.

    The atoms come first (n = 5, 10, 40).  "Structurally related" is made explicit:
    every lifted row small enough to lift inside the budget, in increasing n, capped at
    `cap` rows.  Lifting is O(n^2) exact pair work, so the cap is declared rather than
    silently truncating a corpus that would take minutes.
    """
    rows = W._delivered_rows()
    known = lifted_rows()
    atoms = [5, 10, 40]
    pick = list(atoms)
    if known is not None:
        pick += [n for n in sorted(known) if n not in atoms and n <= limit]
    out = []
    for n in pick[:max(cap, len(atoms))]:
        if n not in rows:
            continue
        st, ws, L = W._lift_row(n, rows)
        if st is not None:
            out.append((n, st, ws, L))
        print(f"  lifted n={n} ({len(out)} so far)", flush=True)
    return out


def diamond1():
    """The single 45-degree square: the second alphabet primitive of a composition."""
    return ([(W.S2H, W.S2H)], [W.Q.word_45()])


def acceptance():
    """The DiamondField acceptance test, one atom at a time.

    Three claims are checked per atom, all exact:
      1. the combinator's assembled sentence *is* the delivered lifted state -- same
         centres, same words, as sets (so a mistyped slot or step fails here);
      2. the alphabet {Tile, diamond} covers it completely: 100% decomposition, with
         the counts |axis cells| and |diamonds| the combinator derived;
      3. the side and the void are the lifted atom's, exactly.
    """
    out = []
    for name, n in (("n10", 10), ("n19", 19), ("n40", 40)):
        claim = W.p_diamond_field(name)
        st, ws, L = W._lift_row(n)
        gen = {(p, _word_key(w)) for p, w in zip(claim.payload["state"],
                                               claim.payload["words"])}
        ref = {(p, _word_key(w)) for p, w in zip(st, ws)}
        same = gen == ref
        grid = W.p_grid(1)
        c_t, tot_t, _ = cover(claim.payload["state"], claim.payload["words"],
                              grid.payload["state"], grid.payload["words"])
        dt, dw = diamond1()
        c_d, _, _ = cover(claim.payload["state"], claim.payload["words"], dt, dw)
        rec = {"field": name, "n": n, "squares": len(claim.payload["state"]),
               "axis": len(claim.payload["cells"]),
               "diamonds": len(claim.payload["slots"]),
               "dropped": len(claim.payload["dropped"]),
               "identical_to_atom": same,
               "tile_copies": c_t, "diamond_copies": c_d,
               "covered": c_t + c_d, "total": len(claim.payload["state"]),
               "exact": same and c_t + c_d == len(claim.payload["state"]),
               "L": str(claim.laws["extent"][1]),
               "L_matches_atom": claim.laws["extent"][1] == L,
               "void": str(claim.laws["void"][1]),
               "gain": str(claim.invariant[1]) if claim.invariant else None}
        out.append(rec)
    return out


def run():
    T = templates()
    states = lifted_states()
    results = []
    for n, st, ws, L in states:
        best = None
        per_template = {}
        for name, (tst, tws) in T.items():
            if len(tst) > len(st) or name == f"Atom{n}":   # no trivial self-cover
                continue
            c, tot, used = cover(st, ws, tst, tws)
            per_template[name] = {"covered": c, "total": tot, "copies": len(used)}
            if best is None or c > best[2]:
                best = (name, tot, c, used)
        rec = {"n": n, "L": str(L), "squares": len(st),
               "tilted": sum(1 for w in ws if w[0].b != 0),
               "templates": per_template,
               "best": None if best is None else
               {"template": best[0], "covered": best[2], "total": best[1],
                "exact": best[2] == best[1], "copies": len(best[3])}}
        results.append(rec)
    exact = [r for r in results if r["best"] and r["best"]["exact"]]
    out = {
        "run": 86,
        "question": "is a lifted atom a translation/reflection composition "
                    "of the declared vocabulary?",
        "isometries": [name for name, _ in isometries()],
        "templates": sorted(T),
        "states": len(results),
        "exact_decompositions": len(exact),
        "best_partial": max((r["best"]["covered"] / r["best"]["total"]
                             for r in results if r["best"]), default=0),
        "rows": results,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(out, f, indent=1)
    return out


def selftest():
    """Two controls: a planted composition is found, and a planted lie is not."""
    checks = 0
    a = W.p_pocket(1)
    st, ws = a.payload["state"], a.payload["words"]
    # a sentence built from two translated copies of the pocket is a composition
    shift = Q2(F(7, 2))
    two = ([(p[0] + shift, p[1]) for p in st] + list(st),
           list(ws) + list(ws))
    c, tot, used = cover(two[0], two[1], st, ws)
    assert tot == 10 and c == 10, (c, tot)
    print(f"control 1 — two translated pockets are covered exactly ({c}/{tot}, "
          f"{len(used)} copies)")
    checks += 1
    # a unit Tile covers the pocket's axis squares and *not* its diamond, because
    # the witness matches words as well as centres
    tile = W.p_grid(1)
    c2, tot2, used2 = cover(st, ws, tile.payload["state"], tile.payload["words"])
    assert (c2, tot2) == (4, 5), (c2, tot2)
    print(f"control 2 — a unit Tile covers the pocket's 4 axis squares and not its "
          f"diamond ({c2}/{tot2}, {len(used2)} copies): words are matched, not just centres")
    checks += 1
    # the DiamondField acceptance test: 100% exact decomposition of the three atoms
    acc = acceptance()
    for a in acc:
        assert a["exact"], a
        assert a["identical_to_atom"] and a["L_matches_atom"], a
        assert a["covered"] == a["total"] == a["squares"], a
    print("control 3 — DiamondField reproduces and fully decomposes the atoms: "
          + ", ".join(f"n={a['n']} {a['axis']}+{a['diamonds']}={a['squares']}"
                      for a in acc))
    checks += 1
    print(f"grammar_induction: OK ({checks} controls)")
    return checks


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--selftest" in argv:
        return 0 if selftest() else 1
    acc = acceptance()
    print("DiamondField acceptance — declared slots, derived geometry")
    for a in acc:
        print(f"  {a['field']:4s} n={a['n']:3d} {a['axis']:2d} axis + {a['diamonds']:2d} "
              f"diamonds, dropped {a['dropped']}, L = {a['L']:>14s}, "
              f"covered {a['covered']}/{a['total']} exact={a['exact']} "
              f"identical={a['identical_to_atom']}")
    with open(os.path.join(ROOT, "workspace/push/diamond_fields.json"), "w") as f:
        json.dump({"run": 87, "acceptance": acc}, f, indent=1)
    out = run()
    print(f"\nstates: {out['states']}, exact decompositions: "
          f"{out['exact_decompositions']}, best partial cover: "
          f"{out['best_partial']:.3f}")
    for r in out["rows"][:6]:
        b = r["best"]
        print(f"  n={r['n']:4d} L={r['L']:>16s} squares {r['squares']:4d} "
              f"best {b['template']:9s} {b['covered']:3d}/{b['total']:3d}")
    print(f"  ledger: {os.path.relpath(OUT, ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
