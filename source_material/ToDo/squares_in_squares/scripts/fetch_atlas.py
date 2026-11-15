#!/usr/bin/env python3
r"""fetch_atlas.py — (re)fetch the community register snapshot into
workspace/sources/atlas/lists/ (best.json + certs), for import_atlas.py.

Source: github.com/evand/square-packing  search/regularize/lists/
(best.json + certs/n-XXX.cert.gz), the Square Packing Atlas register.
Register rows with n <= 1000 are fetched (cert paths as in best.json,
mirrored locally after 'lists/').  Idempotent: existing files are kept
unless --refresh.  Prints the snapshot's n-range and entry count so a
weekly watch can diff it (P3).
"""
import concurrent.futures as cf
import json
import os
import sys
import urllib.request

ROOT = __import__("os").path.dirname(__import__("os").path.dirname(
    __import__("os").path.abspath(__file__)))
ATLAS = ROOT + "/workspace/sources/atlas/lists"
BASE = ("https://raw.githubusercontent.com/evand/square-packing/"
        "main/search/regularize/lists/")
MAXN = 1000


def fetch(url, path, refresh=False):
    if os.path.exists(path) and not refresh and os.path.getsize(path) > 0:
        return "kept"
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            data = r.read()
        with open(path, "wb") as f:
            f.write(data)
        return "ok"
    except Exception as e:
        return f"fail {e}"


def main():
    refresh = "--refresh" in sys.argv
    os.makedirs(ATLAS, exist_ok=True)
    st = fetch(BASE + "best.json", ATLAS + "/best.json", refresh)
    if st.startswith("fail"):
        print("best.json fetch failed:", st)
        sys.exit(1)
    best = json.load(open(ATLAS + "/best.json"))
    rows = [b for b in best if b["n"] <= MAXN]
    print(f"best.json: {st} | entries n<=1000: {len(rows)} "
          f"(n range {rows[0]['n']}..{rows[-1]['n']})")
    jobs = []
    for b in rows:
        rel = b["cert"].split("lists/")[-1]
        p = os.path.join(ATLAS, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        jobs.append((BASE + rel, p))
    with cf.ThreadPoolExecutor(12) as ex:
        res = list(ex.map(lambda j: fetch(j[0], j[1], refresh), jobs))
    ok = sum(1 for r in res if r == "ok")
    kept = sum(1 for r in res if r == "kept")
    fails = [r for r in res if r.startswith("fail")]
    print(f"certs: {ok} fetched, {kept} kept, {len(fails)} failed")
    for f in fails[:5]:
        print("  ", f)
    # snapshot summary for the weekly watch
    snap = {"entries": len(rows), "n_max": rows[-1]["n"],
            "sides": {b["n"]: b["side"] for b in rows}}
    json.dump(snap, open(ATLAS + "/snapshot.json", "w"))
    print("snapshot ->", ATLAS + "/snapshot.json")


if __name__ == "__main__":
    main()
