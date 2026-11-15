#!/usr/bin/env python3
r"""theta225_push.py — Run 5: complete the rotated-block family program.

Directive: the Leech-map report recommended expanding the algebraic
certificates to the 22.5-degree nested quartic field Q(sqrt(2+sqrt(2))),
hoping to convert numerical Level-0 puzzles into higher-tier certified
beats.  This script carries the whole program to its honest end:

  Phase A — re-sweep n <= 1050 at all 7 special angles (45, 36.870,
            30, 26.565, 22.5, 18.435, 15) with the shared theta_family
            machinery (exact sympy states -> packlib SAT verification ->
            finalize).  Every verified member is recorded with its exact
            container value, grid bound and current table record.
  Phase B — certificates: EVERY verified member enters
            galois_certificates.json (dedup by family,a,p).  Fields:
            Q(45°), Q(36.870° rational), Q(sqrt3)(30°), Q(sqrt5)(26.565°),
            Q(sqrt(2+sqrt2))(22.5°, C4), Q(sqrt10)(18.435°),
            Q(sqrt2,sqrt3)(15°, V4).
  Phase C — Level-0 analysis: which unresolved table puzzles are
            reachable by the family at all, and the measured gap
            (best family s vs table L) for each.  This quantifies the
            "conversion" question directly.
  Phase D — extended-range sweep 1001 <= n <= 5000 against
            extended_table_5000.json bounds (3195/4000 are still the
            plain grid).  Verified improvements are applied with states.
  Phase E — summary JSON (download/run5_push.json) + English console
            report.  NOTHING is applied anywhere without packlib
            verification; candidates that fail verification are dropped
            and counted.
"""
import json
import math
import os
import sys
from math import ceil, sqrt

import sympy as sp

HERE = "/home/z/my-project/scripts"
sys.path.insert(0, HERE)
import packlib as P
import theta_family as TF   # special_angles, s_formula, feasible, k_clears, build_state

SUB = "/home/z/my-project/workspace/submission"
DL = "/home/z/my-project/download"
TAB = os.path.join(SUB, "table.json")
EXT = os.path.join(SUB, "extended_table_5000.json")
CERTS = os.path.join(SUB, "galois_certificates.json")

x = sp.symbols("x")


# ---------------------------------------------------------------- helpers
def to_float_state(st):
    out = []
    for (X, Y, T) in st:
        t = float(T.evalf(40)) % (math.pi / 2)
        out.append((float(X.evalf(40)), float(Y.evalf(40)), t))
    return out


def _gf2_basis(vectors):
    basis = []
    for v in vectors:
        w = list(v)
        for pivot, b in basis:
            if w[pivot]:
                w = [a ^ c for a, c in zip(w, b)]
        if any(w):
            basis.append((w.index(1), tuple(w)))
    return basis


def _in_span(v, basis):
    w = list(v)
    for pivot, b in basis:
        if w[pivot]:
            w = [a ^ c for a, c in zip(w, b)]
    return not any(w)


def field_of(sex):
    """Canonical field name from the exact expression: collect integer
    squarefree radicands, build the GF(2) span of their prime-exponent
    vectors, and name by unit vectors (√p) when available (Q(√2,√3)
    convention), else by the 1-dim generator (√6, √10)."""
    s = str(sex)
    if "2 + sqrt(2)" in s or "2 - sqrt(2)" in s or "sqrt(2 + sqrt(2" in s:
        return "Q(√(2+√2))"
    rads = set()
    nested = False

    def walk(e):
        nonlocal nested
        if isinstance(e, sp.Pow) and e.exp == sp.Rational(1, 2):
            if isinstance(e.base, sp.Integer):
                rads.add(int(e.base))
            else:
                nested = True
            return
        for a in e.args:
            walk(a)

    walk(sp.expand(sex))
    if nested:
        return "Q(√(2+√2))"
    ints = set()
    for r in rads:
        f = sp.factorint(r)
        sq = 1
        for p_, m in f.items():
            if m % 2 == 1:
                sq *= p_
        if sq > 1:
            ints.add(sq)
    if not ints:
        return "Q"
    primes = sorted({q for i in ints for q in sp.factorint(i)})
    vecs = [tuple(1 if q in sp.factorint(i) else 0 for q in primes)
            for i in sorted(ints)]
    basis = _gf2_basis(vecs)
    d = len(basis)
    units = [q for k, q in enumerate(primes)
             if _in_span(tuple(1 if j == k else 0 for j in range(len(primes))),
                         basis)]
    if len(units) == d:
        if d == 0:
            return "Q"
        if d == 1:
            return f"Q(√{units[0]})"
        return "Q(" + ",".join(f"√{u}" for u in units) + ")"
    if d == 1:
        pivot, b = basis[0]
        rad = 1
        for k, q in enumerate(primes):
            if b[k]:
                rad *= q
        return f"Q(√{rad})"
    return "Q(" + ",".join(f"√{i}" for i in sorted(ints)) + ")"


def galois_of(poly, field):
    try:
        G, _ = sp.galois_group(poly, x)
        order = int(G.order())
        if order == 1:
            return "trivial", 1
        if G.is_cyclic:
            return f"C{order}", order
        if order == 4 and G.is_abelian:
            return "V4", 4
        return f"order-{order}", order
    except Exception:
        pass
    if field == "Q":
        return "trivial", 1
    if field == "Q(√(2+√2))":
        return "C4", 4        # x^4-4x^2+2, real subfield of Q(zeta16)
    if field == "Q(√2,√3)":
        return "V4", 4
    if "√" in field:
        return "C2", 2
    return "?", 0


def certify(name, a, p, n, sex, stf, r, grid, cur):
    poly = sp.minimal_polynomial(sex, x)
    field = field_of(sex)
    grp, gord = galois_of(poly, field)
    return {
        "family": f"θ={name}°", "angle": name, "a": a, "p": p, "n": n,
        "s_exact": str(sex),
        "s_float": round(float(sex.evalf(30)), 12),
        "field": field, "degree": int(sp.degree(poly, x)),
        "minimal_polynomial": str(poly),
        "galois_group": grp, "galois_order": gord,
        "verified_worst_pen": float(r["worst_pen"]),
        "verified_L": round(float(r["L"]), 12),
        "grid": grid, "record": cur,
        "beats_grid": bool(r["L"] < grid - 1e-9),
        "beats_record": bool(cur is not None and r["L"] < cur - 1e-9),
    }


def sweep(angles, a_lo, a_hi, n_lo, n_hi, bound_of, verbose=False):
    """Generic sweep: all (a,p,theta) with n_lo<=n<=n_hi.  bound_of(n)
    returns the value to beat (None -> no comparison target).  Returns
    verified member dicts."""
    members = []
    cand = verified = 0
    for a in range(a_lo, a_hi + 1):
        base = 2 * a * (a + 1)
        if base + 1 > n_hi:
            break
        for p in range(1, 200):
            n = base + p * p
            if n > n_hi:
                break
            if n < n_lo:
                continue
            for name, (c, s_) in angles.items():
                s_val, M, m = TF.s_formula(a, p, c, s_)
                ok, why = TF.feasible(a, p, c, s_, s_val)
                if not ok:
                    continue
                if not TF.k_clears(a, p, c, s_, s_val):
                    continue
                target = bound_of(n)
                s_num = float(s_val.evalf(40))
                if target is not None and not (s_num < target - 1e-9):
                    continue          # cannot beat the target: skip verify
                cand += 1
                st = TF.build_state(a, p, c, s_, s_val)
                stf = to_float_state(st)
                assert len(stf) == n
                try:
                    r = P.verify(stf)
                    if r["worst_pen"] > 1e-9:
                        continue
                    stf2, r2 = P.finalize(stf, gap=2e-9)
                except MemoryError:
                    print(f"  [mem] skip verify n={n} ({name} a={a} p={p})")
                    continue
                if not r2["ok"]:
                    continue
                if target is not None and not (r2["L"] < target - 1e-9):
                    continue          # verified value fails to beat
                verified += 1
                grid = ceil(sqrt(n))
                cur = bound_of(n)
                members.append(certify(name, a, p, n, s_val, stf2, r2,
                                       grid, cur))
                if verbose:
                    print(f"  VERIFIED {name}° a={a} p={p} n={n} "
                          f"s={float(r2['L']):.9f} (target {cur})")
    return members, cand, verified


def main():
    tab = json.load(open(TAB))
    ext = json.load(open(EXT))
    certs = json.load(open(CERTS))
    have = {(c.get("family"), c.get("a"), c.get("p")) for c in certs}
    angles = TF.special_angles()
    report = {}

    # ---------------- Phase A+B: main range n <= 1050 -----------------
    print("=== Phase A/B: full sweep n<=1050, 7 angles ===")

    def table_bound(n):
        rec = tab.get(str(n))
        return float(rec["L"]) if rec else None

    members, cand, ver = sweep(angles, 1, 25, 1, 1000, table_bound)
    # NOTE: for the main range the target is the TABLE record; the sweep
    # above therefore only kept members that BEAT the table.  For the
    # certificate census we need ALL verified members -> redo with no
    # target but reuse the verify results via a second pass:
    members_all, cand2, ver2 = sweep(angles, 1, 25, 1, 1050, lambda n: None)
    report["main_range"] = {
        "candidates_verified": ver2,
        "beats_table_n_le_1000": len(members),
        "beats_table_list": [(m["family"], m["a"], m["p"], m["n"],
                              m["verified_L"]) for m in members],
    }
    print(f"verified members (all): {ver2}; beating the table: {len(members)}")

    # quartic-level members with states (the deliverable object file)
    quartic = [m for m in members_all if m["degree"] == 4]
    qmembers = []
    for m in quartic:
        if not m["beats_grid"]:
            continue
        c, s_ = angles[m["angle"]]
        st = TF.build_state(m["a"], m["p"], c, s_,
                            sp.sympify(m["s_exact"]))
        stf = to_float_state(st)
        stf2, r2 = P.finalize(stf, gap=2e-9)
        qmembers.append({"n": m["n"], "a": m["a"], "p": m["p"],
                         "angle": m["angle"],
                         "s": round(float(r2["L"]), 12),
                         "s_exact": m["s_exact"],
                         "grid": m["grid"],
                         "record": (float(tab[str(m["n"])]["L"])
                                    if str(m["n"]) in tab else None),
                         "state": [[round(q[0], 12), round(q[1], 12),
                                    round(q[2], 12)] for q in stf2]})
    json.dump(qmembers, open(os.path.join(SUB, "theta_quartic_members.json"), "w"),
              indent=1)
    print(f"quartic (deg-4) members: {len(quartic)}, of which beat grid: {len(qmembers)}"
          f" -> theta_quartic_members.json")

    # append all new members to the certificate collection
    added = 0
    for m in members_all:
        key = (m["family"], m["a"], m["p"])
        if key in have:
            continue
        have.add(key)
        certs.append(m)
        added += 1
    byf = {}
    for m in members_all:
        byf[m["field"]] = byf.get(m["field"], 0) + 1
    report["certificates"] = {
        "before": 54, "added": added, "after": len(certs),
        "members_by_field": byf,
    }
    print(f"certificates: 54 -> {len(certs)} (+{added}); by field: {byf}")
    json.dump(certs, open(CERTS, "w"), indent=1)

    # ---------------- Phase C: Level-0 gap analysis --------------------
    lm = json.load(open(os.path.join(DL, "leech_map.json")))
    lvl0 = [r["n"] for r in lm["rows"] if r["level"] == 0]
    # family footprint per n: collect ALL verified members per n
    per_n = {}
    for m in members_all:
        per_n.setdefault(m["n"], []).append(m)
    reach0 = sorted(set(lvl0) & set(per_n))
    gaps = []
    for n in reach0:
        best = min(per_n[n], key=lambda m: m["verified_L"])
        cur = float(tab[str(n)]["L"])
        gaps.append({"n": n, "level0_L": cur,
                     "best_family_s": best["verified_L"],
                     "best_family": f"{best['family']} a={best['a']} p={best['p']}",
                     "gap": round(best["verified_L"] - cur, 9),
                     "reachable_converted": False})
    report["level0"] = {
        "count": len(lvl0),
        "reachable_by_family": len(reach0),
        "reachable_ns": reach0,
        "gaps": gaps,
        "conversions": 0,
    }
    print(f"Level-0: {len(lvl0)} puzzles, {len(reach0)} reachable by the family")
    for g in gaps[:12]:
        print(f"  n={g['n']}: table {g['level0_L']:.9f} vs best family "
              f"{g['best_family_s']:.9f} ({g['best_family']}) gap {g['gap']:.6f}")

    # ---------------- Phase D: extended range 1001..5000 ---------------
    print("=== Phase D: extended sweep 1001..5000 ===")

    def ext_bound(n):
        e = ext.get(str(n))
        return float(e["bound"]) if e else None

    ext_members, ecand, ever = sweep(angles, 1, 49, 1001, 5000, ext_bound)
    # keep only the BEST improver per n (several angles may qualify)
    best_by_n = {}
    for m in ext_members:
        cur = best_by_n.get(m["n"])
        if cur is None or m["verified_L"] < cur["verified_L"] - 1e-12:
            best_by_n[m["n"]] = m
    applied = []
    for n in sorted(best_by_n):
        m = best_by_n[n]
        e = ext[str(n)]
        c, s_ = angles[m["angle"]]
        st = TF.build_state(m["a"], m["p"], c, s_, sp.sympify(m["s_exact"]))
        stf = to_float_state(st)
        stf2, r2 = P.finalize(stf, gap=2e-9)
        e["L"] = round(float(r2["L"]), 12)
        e["bound"] = e["L"]
        e["src"] = f"theta{m['angle']}:a{m['a']}p{m['p']}"
        e["state"] = [[round(q[0], 12), round(q[1], 12), round(q[2], 12)]
                      for q in stf2]
        applied.append({"n": n, "old": m["record"], "new": e["L"],
                        "src": e["src"]})
    if applied:
        json.dump(ext, open(EXT, "w"))
    report["extended"] = {
        "candidates_past_bound_gate": ecand,
        "candidates_verified": ever,
        "improvements": applied,
    }
    print(f"extended sweep: {ecand} candidates passed the bound gate, "
          f"{ever} verified, {len(applied)} improvements applied")
    for ap in applied:
        print(f"  n={ap['n']}: {ap['old']} -> {ap['new']} ({ap['src']})")

    # ---------------- Phase E: summary ---------------------------------
    # family footprint + per-angle census for the report
    report["census"] = {
        "angles": sorted({m["family"] for m in members_all}),
        "footprint_ns": len(per_n),
        "verified_total": len(members_all),
    }
    json.dump(report, open(os.path.join(DL, "run5_push.json"), "w"), indent=1)
    print("=== summary ===")
    print(f"verified members: {len(members_all)} across {len(per_n)} distinct n")
    print(f"table beats (n<=1000): {len(members)}; extended improvements: {len(applied)}")
    print(f"certificates: 54 -> {len(certs)}")
    print("wrote", os.path.join(DL, "run5_push.json"))


if __name__ == "__main__":
    main()
