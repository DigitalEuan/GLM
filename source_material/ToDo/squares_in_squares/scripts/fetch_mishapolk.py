#!/usr/bin/env python3
r"""fetch_mishapolk.py — run 30, P3: fetch Mishapolk/square-packing-records.

The weekly watch (run 30) found that Mishapolk's upper_bounds.json
carries entries at 676 n in 325..1000 — the band our atlas
(squaremath.org, 1..324 only) never showed us.  Exact certified
bounds (exact rationals; many with in-repo certificates).

This script (idempotent, like fetch_atlas.py):
  1. fetch upper_bounds.json -> workspace/sources/mishapolk/;
  2. compare every verified bound for n in 1..1000 against our table;
  3. for entries that beat the table, classify by verified.source:
     direct certificate ("certificates/...") vs construction-only;
  4. fetch the direct certificates needed (dedup by path);
  5. ledger workspace/push/fetch_mishapolk30.json.

No table change here (import_mishapolk.py does that, gated).
"""
import json
import math
import os
import urllib.request

W = "/home/z/my-project"
DST = W + "/workspace/sources/mishapolk"
TAB = W + "/workspace/submission/table.json"
OUT = W + "/workspace/push/fetch_mishapolk30.json"
BASE = "https://raw.githubusercontent.com/Mishapolk/square-packing-records/main/"


def fetch(url, path, refresh=False):
    if os.path.exists(path) and not refresh:
        return "kept"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "squares/30"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    tmp = path + ".tmp"
    open(tmp, "wb").write(data)
    os.replace(tmp, path)
    return "fetched"


def _num(x):
    """'5/2' / 1.5 / 0 -> float."""
    if x in (None, "", 0, "0"):
        return 0.0
    if isinstance(x, (int, float)):
        return float(x)
    x = str(x)
    if "/" in x:
        num, den = x.split("/")
        return float(num) / float(den)
    return float(x)


def bound_value(entry):
    """verified.bound as float: the field is an exact rational or has an
    expression form r + c*sqrt(2) (exact_bound: rational, sqrt2)."""
    v = entry["verified"]
    eb = v.get("exact_bound") or {}
    r = _num(eb.get("rational", 0))
    c = _num(eb.get("sqrt2", 0))
    if c:
        return r + c * math.sqrt(2)
    b = v["bound"]
    try:
        return float(b)
    except (TypeError, ValueError):
        num, den = b.split("/")
        return float(num) / float(den)


def main():
    st = fetch(BASE + "upper_bounds.json", DST + "/upper_bounds.json")
    print("upper_bounds.json:", st)
    doc = json.load(open(DST + "/upper_bounds.json"))
    entries = doc["entries"]

    tab = json.load(open(TAB))
    beats, ties = [], []
    for k in range(1, 1001):
        e = entries.get(str(k))
        if not e or "verified" not in e:
            continue
        b = bound_value(e)
        cur = tab[str(k)]["L"]
        if b < cur - 1e-9:
            beats.append((k, b, cur, e))
        elif b < cur + 1e-9 and "certificates/" in str(e["verified"].get("source", "")):
            ties.append(k)

    direct, constru = [], []
    for k, b, cur, e in beats:
        src = e["verified"].get("source", "")
        (direct if src.startswith("certificates/") else constru).append(
            (k, b, cur, src, e["verified"].get("credit", "")))

    print(f"entries with verified bounds: "
          f"{sum(1 for k in range(1,1001) if entries.get(str(k), {}).get('verified'))}")
    print(f"beat our table: {len(beats)} | tied w/ direct cert: {len(ties)}")
    print(f"  direct certificate: {len(direct)}")
    print(f"  construction-only : {len(constru)}")

    # fetch the needed certs (dedup by source path; one cert can serve
    # several n via deleted_squares, but here source_n == n typically)
    need = {}
    for k, b, cur, src, credit in direct:
        need.setdefault(src, []).append(k)
    fetched = kept = failed = 0
    for src, ns in sorted(need.items()):
        rel = src.replace("certificates/", "").replace("/", "_")
        path = f"{DST}/certs/{rel}"
        try:
            stc = fetch(BASE + src, path)
        except Exception as ex:
            print(f"  FAIL {src}: {ex}")
            failed += 1
            continue
        fetched += stc == "fetched"
        kept += stc == "kept"
    print(f"certs: {fetched} fetched, {kept} kept, {failed} failed "
          f"({len(need)} paths)")

    json.dump({
        "upper_bounds": st,
        "entries_1_1000_verified": sum(
            1 for k in range(1, 1001) if entries.get(str(k), {}).get("verified")),
        "beat_table": len(beats),
        "direct": [{"n": k, "new": b, "old": cur, "src": s, "credit": c}
                   for k, b, cur, s, c in direct],
        "construction_only": [{"n": k, "new": b, "old": cur, "src": s, "credit": c}
                              for k, b, cur, s, c in constru],
        "cert_paths": sorted(need),
        "certs_fetched": fetched, "certs_kept": kept, "certs_failed": failed,
    }, open(OUT, "w"), indent=1)
    print("ledger ->", OUT)


if __name__ == "__main__":
    main()
