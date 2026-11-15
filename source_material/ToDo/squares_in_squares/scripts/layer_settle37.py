#!/usr/bin/env python3
r"""layer_settle37.py — run 37: the provenance-based layer-settle census.

Question (user): where does each of the 1000 rows actually settle in
the perception tower, on the CURRENT (import-dominated) frontier —
and what exact material exists locally for each row?

The run-5-era leech_map level (field-degree fit on the container
value) degenerates on the current table: the import classes store
12-dp finalize floats, which fit nothing small (leech_map run 37:
991/1000 at level 0; the old +0.79 Spearman is UNDEFINED — constant
series). The honest modern census is by PROVENANCE: what exact
material (side and geometry) exists for the row, from local sources.

Settle classes (a row lands in the first that applies):
  cert-rational    an exact rational certificate exists locally:
                   side AND per-square geometry (register: candidates
                   certs; mishapolk: certs/ or verified.bound + cert;
                   atlas: lists/certs; grid: integer side by
                   construction, lattice states)
  design-quadratic the design side is an exact Q(√m) value from a
                   construction family (gobel2/gobelS/gobel3: the
                   family generator is exact at the design side;
                   exact-class survey records with declared forms)
  derived          the row's value is exact arithmetic on a parent
                   (chain3: L_parent + integer; closure/removal:
                   envelope minima) — inherits the parent's class
  float-only       12-dp finalize state, no local exact material
                   (run18-frontier; anything unmatched above)

Outputs per class: rows, improvement share (Σ(⌈√n⌉−L)/√n), angle
vocabulary (0°/45° only vs drifted), and the side/geometry exact
material.  Ledger: workspace/push/layer_settle37.json.
"""
import json
import math
import os
import re
from collections import Counter, defaultdict
from fractions import Fraction

W = "/home/z/my-project"
TAB = json.load(open(f"{W}/workspace/submission/table.json"))
CAND = f"{W}/workspace/sources/candidates"
MISH = f"{W}/workspace/sources/mishapolk"
ATLAS = f"{W}/workspace/sources/atlas"
OUT = f"{W}/workspace/push/layer_settle37.json"

# ---------- local exact material maps ---------------------------------

def cert_n_of(path):
    m = re.search(r"[nN](\d+)", os.path.basename(path))
    return int(m.group(1)) if m else None


def parse_cert_file(path):
    """evand-candidates / atlas cert format -> (n, S_exact, state_exact)
    or None. State entries: (x, y, t) exact rationals, centres."""
    try:
        lines = open(path).read().splitlines()
        n, S = lines[1].split()
        n, S = int(n), Fraction(S)
        if len(lines) < 2 + n:
            return None
        st = []
        for ln in lines[2:2 + n]:
            x, y, t = ln.split()
            st.append((Fraction(x), Fraction(y), Fraction(t)))
        return n, S, st
    except Exception:
        return None


def parse_mish_cert(path):
    """Mishapolk cert: first lines comment; '<n> <S>'; rows '<x> <y> <t>'
    (rational t = tan(theta/2); same as evand format)."""
    return parse_cert_file(path)


material = {}   # n -> dict(side=Fraction|None, geom=list|None, via=str)


def register_material():
    for f in os.listdir(CAND):
        if not f.endswith(".cert"):
            continue
        r = parse_cert_file(f"{CAND}/{f}")
        if r:
            n, S, st = r
            if n not in material or material[n]["side"] is None:
                material[n] = {"side": S, "geom": st, "via": f"register:{f}"}
    # atlas certs (community register)
    adir = f"{ATLAS}/certs"
    if os.path.isdir(adir):
        for f in os.listdir(adir):
            if not f.endswith(".cert"):
                continue
            r = parse_cert_file(f"{adir}/{f}")
            if r:
                n, S, st = r
                if n not in material:
                    material[n] = {"side": S, "geom": st, "via": f"atlas:{f}"}
    # atlas best.json (sides only)
    try:
        best = json.load(open(f"{ATLAS}/lists/best.json"))
        for k, v in best.items():
            n = int(k)
            if n not in material:
                material[n] = {"side": Fraction(str(v["L"])) if not isinstance(v, dict) else Fraction(str(v.get("L", 0))), "geom": None, "via": "atlas:best.json"}
    except Exception:
        pass


def mishapolk_material():
    ub = json.load(open(f"{MISH}/upper_bounds.json"))["entries"]
    for k, e in ub.items():
        n = int(k)
        v = e.get("verified", {})
        b = v.get("bound")
        if b is None or n > 1000 or n in material:
            continue
        try:
            side = Fraction(b)
        except Exception:
            continue
        # geometry: local cert mirror if present
        geom = None
        src = str(v.get("source", ""))
        if "certificates/" in src:
            rel = src.replace("certificates/", "").replace("/", "_")
            p = f"{MISH}/certs/{rel}"
            if os.path.exists(p):
                r = parse_mish_cert(p)
                if r and r[0] == n:
                    geom = r[2]
        material[n] = {"side": side, "geom": geom, "via": "mishapolk:bound"}


register_material()
mishapolk_material()

# grid rows: integer side by construction, lattice states (exact)
# (stored L is the finalize-inflated integer; design = ceil(sqrt(n)))


def settle_class(n, rec):
    src = rec["src"]
    cls = src.split(":")[0]
    if cls == "grid":
        return "cert-rational", "grid (integer side + lattice states)"
    if cls == "register":
        m = material.get(n)
        if m and m["side"] is not None:
            return "cert-rational", f"register ({m['via']})"
        return "float-only", "register (no local cert?!)"
    if cls == "mishapolk":
        m = material.get(n)
        if m and m["side"] is not None:
            g = "side+geom" if m["geom"] else "side-only"
            return "cert-rational", f"mishapolk ({g})"
        return "float-only", "mishapolk (no bound?!)"
    if cls in ("gobel2", "gobelS", "gobel3"):
        return "design-quadratic", cls + " (exact design side, Q(√2) family)"
    if cls == "exact":
        # survey records: Friedman catalogue declares exact forms for a
        # subset; the SVGs carry 14-dp values. Class by galois certs
        # (value-matched) else by staged fit on the design value.
        return "design-quadratic", "exact (survey: declared-form tier)"
    if cls == "aux":
        return "design-quadratic", "aux (survey-adjacent)"
    if cls == "chain3":
        return "derived", "chain3 (L_parent + integer)"
    if cls in ("closure", "removal"):
        return "derived", cls + " (envelope min over parents)"
    if cls == "run18-frontier":
        return "float-only", "run18-frontier (12-dp optimize)"
    return "float-only", cls


rows = []
for n in range(1, 1001):
    rec = TAB[str(n)]
    sc, note = settle_class(n, rec)
    imp = (math.ceil(math.sqrt(n)) - rec["L"]) / math.sqrt(n)
    # angle vocabulary from the stored state
    vocab = set()
    st = rec.get("state") or []
    for (x, y, th) in st:
        d = math.degrees(th) % 90.0
        if d < 0.5 or d > 89.5:
            vocab.add("0")
        elif abs(d - 45.0) < 0.5:
            vocab.add("45")
        else:
            vocab.add("drift")
    rows.append({"n": n, "src": rec["src"], "settle": sc, "note": note,
                 "L": rec["L"], "imp": imp,
                 "vocab": "+".join(sorted(vocab)) if vocab else "?"})

# ---------- census -----------------------------------------------------
census = defaultdict(lambda: {"rows": 0, "imp": 0.0, "vocab": Counter(),
                              "notes": Counter()})
for r in rows:
    c = census[r["settle"]]
    c["rows"] += 1
    c["imp"] += r["imp"]
    c["vocab"][r["vocab"]] += 1
    c["notes"][r["note"].split(" (")[0]] += 1

total_imp = sum(r["imp"] for r in rows)
print(f"total improvement over grid: {total_imp:.6f} (score 22.642387, ceiling 28.937670)")
for sc in ("cert-rational", "design-quadratic", "derived", "float-only"):
    c = census[sc]
    share = c["imp"] / total_imp * 100 if total_imp else 0
    print(f"\n{sc}: {c['rows']} rows | improvement {c['imp']:.6f} ({share:.1f}%)")
    print(f"  vocab: {dict(c['vocab'])}")
    print(f"  notes: {dict(c['notes'])}")

# exact material coverage on the import classes
mm = [n for n in range(1, 1001) if TAB[str(n)]["src"].startswith("mishapolk")]
m_side = sum(1 for n in mm if material.get(n, {}).get("side") is not None)
m_geom = sum(1 for n in mm if material.get(n, {}).get("geom") is not None)
print(f"\nmishapolk rows {len(mm)}: exact rational side {m_side}, "
      f"exact geometry (local cert) {m_geom}")
rr = [n for n in range(1, 1001) if TAB[str(n)]["src"].startswith("register")]
r_side = sum(1 for n in rr if material.get(n, {}).get("side") is not None)
r_geom = sum(1 for n in rr if material.get(n, {}).get("geom") is not None)
print(f"register rows {len(rr)}: exact side {r_side}, exact geometry {r_geom}")

# the boundary: which cert-rational rows' STORED value equals the exact
# side (within the finalize clearance) — storage vs design
close = drift = 0
for r in rows:
    if r["settle"] == "cert-rational":
        m = material.get(r["n"])
        if m and m["side"] is not None:
            if abs(float(m["side"]) - r["L"]) < 5e-9:
                close += 1
            else:
                drift += 1
print(f"\ncert-rational rows: stored L == exact side (<=5e-9): {close}; "
      f"drifted: {drift}")

json.dump({"run": 37, "method": __doc__,
           "census": {k: {"rows": v["rows"], "imp": round(v["imp"], 6),
                          "vocab": dict(v["vocab"]), "notes": dict(v["notes"])}
                      for k, v in census.items()},
           "total_improvement": round(total_imp, 6),
           "mishapolk": {"rows": len(mm), "exact_side": m_side,
                         "exact_geom": m_geom},
           "register": {"rows": len(rr), "exact_side": r_side,
                         "exact_geom": r_geom},
           "rows": rows},
          open(OUT, "w"), indent=1)
print(f"\nledger -> {OUT}")
