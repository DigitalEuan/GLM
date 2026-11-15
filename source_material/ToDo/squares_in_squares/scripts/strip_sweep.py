#!/usr/bin/env python3
r"""strip_sweep.py — run 25 P1: the generalized Gobel strip, exactly.

Parametrization (decoded from the imported member states; see
scripts/strip_decode.py — run 25 verified it reproduces n=5,10,27,38,
52,67 to the last stored digit).  In the (p,q) frame (p=(x+y)/sqrt2
along the container diagonal, q=(x-y)/sqrt2), container |p|+|q| <= C
with C = L/sqrt2, the strip is:

  - chain band: w chains (w in {1,2,3}) of theta=pi/4 squares (axis-
    aligned unit squares in (p,q)), q-centres spaced 1, band
    q in [-w/2, w/2]; chain squares p-spaced 1, centered;
  - 2 tip diamonds (theta=0) in the acute corners at (+-(C-1/sqrt2), 0);
  - per q-side an INDEPENDENT staircase (a_1 up, a_2 down): levels
    k=1..a_s at |q| = w/2 + k/sqrt2, diamonds at
    p = ((a_s-k)-2j)/sqrt2, j=0..a_s-k  (edge-to-edge, every level's
    outer vertex touches the container edge).

Tightness: L(a,w) = a+1+w/sqrt2, a = max(a1,a2), makes every outer
vertex touch simultaneously (each wing level AND both tips).

Capacity (per-chain p-window [-(C-sqrt2), C-sqrt2] from the tips for
w<=2; for w=3 the outer chains are instead edge-limited at their
outer corner, giving m_out = floor(sqrt2(a+1)) < m_mid):
  w=1,2:  n_max = w*floor(sqrt2(a-1)+w) + 2 + a(a+1)
  w=3:    n_max = floor(sqrt2(a+1)) + floor(sqrt2(a-1)+3)
                 + 2*floor(sqrt2(a+1)) + 2 + a(a+1)
Deletion closes the family downward: any n <= n_max packs at the same
L, so the per-n family value is the frontier
  L_fam(n) = min{ L(a,w) : n <= n_max(a,w) }.

Sweep (NEXT_STEPS P1(a) as written): n = K^2 - r, r in [5, K+4],
K <= 32 (n <= 1000).  Acceptance test: beat grid at n = 44/58/31.
Gates: every claimed design is packlib.finalize-verified (0 overlap,
count, L = formula + finalize's uniform +2e-9 scale); a find is
verified L < min(grid(n), table[n]) - 1e-9.  Nothing is claimed that
is not measured.
"""
import json
import math
import os
import subprocess
import sys

W = "/home/z/my-project"
sys.path.insert(0, W + "/scripts")
import packlib as P

SQ2 = math.sqrt(2.0)
INV = 1.0 / SQ2
TAB = W + "/workspace/submission/table.json"
OUT = W + "/workspace/push/strip_run25.json"
ACCEPT = (44, 58, 31)          # NEXT_STEPS P1(a) acceptance roots
ACC_NAME = {44: "grid 7 (r=5)", 58: "grid 8 (r=6)", 31: "grid 6 (r=5)"}


def L_formula(a, w):
    return a + 1 + w * INV


def chain_plan(w, a):
    """Per-chain lengths, outermost-first (q-centres -w/2 .. +w/2)."""
    if w == 1:
        return [math.floor(SQ2 * (a - 1) + 1)]
    if w == 2:
        m = math.floor(SQ2 * (a - 1) + 2)
        return [m, m]
    m_mid = math.floor(SQ2 * (a - 1) + 3)
    m_out = math.floor(SQ2 * (a + 1))
    return [m_out, m_mid, m_out]


def n_max(w, a):
    chains = sum(chain_plan(w, a))
    return chains + 2 + a * (a + 1)


def build_strip(w, a1, a2, plan=None):
    """Exact state, container centred at the origin.
    Returns list of (x, y, th) with x=(p+q)/sqrt2, y=(p-q)/sqrt2."""
    a = max(a1, a2)
    L = L_formula(a, w)
    C = L * INV
    if plan is None:
        plan = chain_plan(w, a)
    sq = []
    # chain band: w chains at q-centres c-(w-1)/2 .. c+(w-1)/2
    for c in range(w):
        m = plan[c]
        if m <= 0:
            continue
        qc = c - (w - 1) / 2.0
        p0 = -(m - 1) / 2.0
        for j in range(m):
            p, q = p0 + j, qc
            sq.append(((p + q) * INV, (p - q) * INV, math.pi / 4))
    # tip diamonds in the acute corners
    for pt in (C - INV, -(C - INV)):
        sq.append(((pt) * INV, (pt) * INV, 0.0))
    # two independent staircases
    for s, a_s in ((+1, a1), (-1, a2)):
        for k in range(1, a_s + 1):
            q = s * (w / 2.0 + k * INV)
            for j in range(a_s - k + 1):
                p = ((a_s - k) - 2 * j) * INV
                sq.append(((p + q) * INV, (p - q) * INV, 0.0))
    return sq


def frontier_designs():
    """All (w, a) with n_max <= 1000, plus w=1 a<=31 (table range)."""
    des = []
    for w in (1, 2, 3):
        a = 1
        while True:
            n = n_max(w, a)
            if n > 1050 and w == 1 and a > 31:
                break
            if n > 1000 and not (w == 1):
                break
            if n <= 1050:
                des.append((w, a, L_formula(a, w), n))
            a += 1
            if a > 40:
                break
    # keep only what the table can use
    return [d for d in des if d[3] <= 1000]


def main():
    tab = json.load(open(TAB))
    score0 = sum(r["L"] / math.sqrt(int(k)) - 1
                 for k, r in tab.items())
    print(f"table score before: {score0:.9f}")

    # ---- 1. verify every design (the authority is packlib.finalize)
    designs = frontier_designs()
    verified, bad = [], []
    for (w, a, L, n) in designs:
        state = build_strip(w, a, a)
        if len(state) != n:
            bad.append((w, a, "count", len(state), n))
            continue
        stf, rf = P.finalize(state, gap=2e-9)
        if (not rf["ok"]) or rf["worst_pen"] > 0:
            bad.append((w, a, "pen", rf["worst_pen"]))
            continue
        if abs(rf["L"] - L) > 5e-9:
            bad.append((w, a, "L", rf["L"], L))
            continue
        verified.append({"w": w, "a": a, "L_design": L, "n": n,
                         "L_verified": rf["L"], "count": len(stf),
                         "worst_pen": rf["worst_pen"]})
    print(f"designs verified: {len(verified)}/{len(designs)}"
          + (f"  BAD: {bad}" if bad else ""))
    if bad:
        print("ABORT: capacity formula != built geometry")
        json.dump({"designs_verified": verified, "bad": bad},
                  open(OUT, "w"), indent=1)
        return

    # ---- 2. member rows AND deletion rows: family value vs table.
    # deletion closes the family downward: for any n <= n_max(w,a) the
    # same design packs n at the same L (drop squares, keep geometry).
    # so the family value of n is the frontier L_fam(n) (recomputed per
    # row via the design list), evaluated at BOTH member points and the
    # r in [5,K+4] sweep points.  find gate: frontier-L(family design,
    # finalize-verified) < min(grid(n), table[n]) - 1e-9.
    members = [d for d in verified if d["w"] == 1]
    comp, finds = [], []
    for m in members:
        n = m["n"]
        row = tab.get(str(n))
        tabL = row["L"] if row else None
        entry = {"n": n, "a": m["a"], "L_design": m["L_design"],
                 "L_verified": m["L_verified"], "table_L": tabL}
        if tabL is None:
            entry["verdict"] = "missing row"
        elif m["L_verified"] < min(P.grid_L(n), tabL) - 1e-9:
            entry["verdict"] = "FIND"
            finds.append({"n": n, "grid": P.grid_L(n), "old": tabL,
                          "L": m["L_verified"],
                          "state": build_strip(1, m["a"], m["a"]),
                          "src": f"strip25:w1a{m['a']}"})
        elif tabL < m["L_verified"] - 1e-9:
            entry["verdict"] = "table better"
        else:
            entry["verdict"] = "same design (finalize noise)"
        comp.append(entry)
    print(f"member rows: {len(members)}; member-point finds: {len(finds)}")
    for e in comp:
        print(f"  n={e['n']:4d} a={e['a']:2d} design {e['L_design']:.9f} "
              f"verified {e['L_verified']:.9f} table {e['table_L']} "
              f"-> {e['verdict']}")

    # ---- 3. frontier + sweep n = K^2 - r, r in [5, K+4], WITH find gate
    # (family value at n = frontier L over designs with n_max >= n; the
    # applied design is the argmin member m* = the design achieving it —
    # a deletion of m*'s exact state, rebuilt and finalize-verified).
    def best_design(n):
        cands = [d for d in verified if d["n"] >= n]
        if not cands:
            return None
        return min(cands, key=lambda d: d["L_design"])
    sweep = []
    beats_grid = []
    for K in range(3, 33):
        for r in range(5, K + 5):
            n = K * K - r
            if not (1 <= n <= 1000):
                continue
            g = P.grid_L(n)
            row_t = tab.get(str(n))
            tabL = row_t["L"] if row_t else None
            bd = best_design(n)
            lf = bd["L_design"] if bd else None
            row = {"n": n, "K": K, "r": r, "grid": g, "table_L": tabL,
                   "family_L": lf, "design": (bd["w"], bd["a"]) if bd else None}
            if lf is not None and lf < g - 1e-9:
                row["beats_grid"] = True
                beats_grid.append(n)
            # find gate on the sweep rows too (not just member points)
            if bd is not None and tabL is not None:
                lv = bd["L_verified"]
                if lv < min(g, tabL) - 1e-9:
                    # confirm the DELETION build is real before claiming
                    full = build_strip(bd["w"], bd["a"], bd["a"])
                    state = full[:n] if len(full) >= n else None
                    ok = False
                    if state is not None and len(state) == n:
                        stf, rf = P.finalize(state, gap=2e-9)
                        ok = rf["ok"] and rf["worst_pen"] <= 0
                        if ok and rf["L"] < min(g, tabL) - 1e-9:
                            finds.append({"n": n, "grid": g, "old": tabL,
                                          "L": rf["L"], "state": stf,
                                          "src": f"strip25:w{bd['w']}a{bd['a']}del"})
                            row["find"] = True
                    row["deletion_ok"] = ok
            sweep.append(row)
    bg = sorted(set(beats_grid))
    members_ns = sorted(m["n"] for m in members)
    print(f"\nsweep rows: {len(sweep)} (K=3..32, r in [5,K+4])")
    print(f"family beats grid at: {bg}")
    print(f"w=1 member points:    {members_ns}")
    print(f"identical (family grid-beaters == member points): "
          f"{bg == members_ns}")
    print(f"total finds (members + deletions): {len(finds)}")

    # ---- 3b. full-range closure check: the sweep window is the spec,
    # but the closure claim needs the find gate on EVERY n <= 1000
    # (deletion ranges outside the window, e.g. n=65,66 between the
    # a=7 member and its neighbors).
    full_rows = []
    for n in range(1, 1001):
        g = P.grid_L(n)
        row_t = tab.get(str(n))
        tabL = row_t["L"] if row_t else None
        bd = best_design(n)
        if bd is None or tabL is None:
            continue
        lv = bd["L_verified"]
        ent = {"n": n, "grid": g, "table_L": tabL,
               "family_L": lv, "design": (bd["w"], bd["a"])}
        if lv < g - 1e-9:
            ent["beats_grid"] = True
        if lv < min(g, tabL) - 1e-9:
            full = build_strip(bd["w"], bd["a"], bd["a"])
            state = full[:n]
            stf, rf = P.finalize(state, gap=2e-9)
            if rf["ok"] and rf["worst_pen"] <= 0 and rf["L"] < min(g, tabL) - 1e-9:
                ent["FIND"] = True
                finds.append({"n": n, "grid": g, "old": tabL,
                              "L": rf["L"], "state": stf,
                              "src": f"strip25:w{bd['w']}a{bd['a']}del"})
                print(f"  FULL-RANGE FIND n={n}: {tabL} -> {rf['L']}")
        full_rows.append(ent)
    n_bg_full = sorted(e["n"] for e in full_rows if e.get("beats_grid"))
    n_tab_wins = sorted(e["n"] for e in full_rows
                        if e["table_L"] < e["family_L"] - 1e-9)
    n_same = sorted(e["n"] for e in full_rows
                    if abs(e["table_L"] - e["family_L"]) <= 1e-9
                    or (e["table_L"] < e["family_L"]))
    print(f"\nfull-range (1..1000): rows {len(full_rows)}; "
          f"family beats grid at {len(n_bg_full)} rows: {n_bg_full}")
    print(f"table strictly deeper than family: {len(n_tab_wins)} rows")
    print(f"table <= family everywhere (0 finds): "
          f"{not any(e.get('FIND') for e in full_rows)}")

    # ---- 4. acceptance test 44/58/31 + capacity ceiling
    accept = []
    for n in ACCEPT:
        g = P.grid_L(n)
        ceil_n = max((d["n"] for d in verified if d["L_design"] < g - 1e-9),
                     default=0)
        best = min((d["L_design"] for d in verified if d["n"] >= n),
                   default=None)
        accept.append({"n": n, "grid": g, "family_L": best,
                       "ceiling_below_grid": ceil_n,
                       "pass": bool(best is not None and best < g - 1e-9)})
        print(f"acceptance n={n}: grid {g}, family L {best}, "
              f"capacity ceiling below grid: {ceil_n} "
              f"-> {'PASS' if accept[-1]['pass'] else 'FAIL'}")

    # ---- 5. apply channel (only real, verified finds; dedup by n)
    applied = False
    if finds:
        seen = {}
        for f in finds:
            if f["n"] in seen and seen[f["n"]]["L"] <= f["L"]:
                continue
            seen[f["n"]] = f
        for n in sorted(seen):
            f = seen[n]
            stf, rf = P.finalize(f["state"], gap=2e-9)
            tab[str(n)] = {"L": rf["L"], "state": stf, "src": f["src"]}
            print(f"applied n={n}: {f['old']} -> {rf['L']}")
        json.dump(tab, open(TAB, "w"))
        for cmd in ("scripts/cascade3.py", "scripts/closure_apply.py",
                    "scripts/final_assembly.py"):
            rr = subprocess.run([sys.executable, f"{W}/{cmd}"],
                                capture_output=True, text=True)
            print(" ", cmd, "->", (rr.stdout or rr.stderr).strip().split("\n")[-1])
        applied = True
    else:
        print("no applicable finds — table unchanged (honest).")

    tab2 = json.load(open(TAB))
    score1 = sum(r["L"] / math.sqrt(int(k)) - 1
                 for k, r in tab2.items())
    print(f"table score after: {score1:.9f}")

    json.dump({
        "run": 25, "part": "P1 generalized Gobel strip",
        "parametrization": "(p,q) frame; see module docstring; verified "
                           "against imported member states (strip_decode.py)",
        "designs_verified": verified,
        "member_comparison": comp,
        "sweep": {"rows": len(sweep), "beats_grid_at": bg,
                  "member_points": members_ns,
                  "identical": bg == members_ns,
                  "detail": sweep},
        "full_range": {"rows": len(full_rows),
                       "beats_grid_at": n_bg_full,
                       "table_strictly_deeper": n_tab_wins,
                       "any_find": any(e.get("FIND") for e in full_rows),
                       "detail": full_rows},
        "acceptance": accept,
        "finds": [{k: f[k] for k in ("n", "grid", "old", "L")}
                  for f in finds],
        "applied": applied,
        "score_before": score0, "score_after": score1,
    }, open(OUT, "w"), indent=1)
    print("ledger ->", OUT)


if __name__ == "__main__":
    main()
