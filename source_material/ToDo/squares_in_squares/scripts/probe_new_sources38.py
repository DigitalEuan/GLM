#!/usr/bin/env python3
r"""probe_new_sources38.py — run 38, P3+: probe the four NEW sources the
web search found (never seen by our watch):

  1. dostashev/square-packing        (exact certificates; Oct 12 2026)
  2. chelokot/square-packing-archive (Lean-verified; 1..100)
  3. jlevy/squares                   (archive of every known result; 1..324)
  4. forloopcodes/least-space-squares (squarepack)

Method: mirror each repo tarball via codeload.github.com (the
fetch_candidates.py pattern), list the record-bearing files, parse
any (n, side) pairs they carry, and compare against our table —
print ONLY the rows that would beat us.  Read-only probe: no table
change, no import.  Ledger: workspace/push/probe_new_sources38.json.
"""
import io
import json
import math
import os
import re
import tarfile
import urllib.request

W = "/home/z/my-project"
TAB = json.load(open(f"{W}/workspace/submission/table.json"))
OUT = f"{W}/workspace/push/probe_new_sources38.json"

REPOS = [
    ("dostashev/square-packing", ["main", "master"]),
    ("chelokot/square-packing-archive", ["main", "master"]),
    ("jlevy/squares", ["main", "master"]),
    ("forloopcodes/least-space-squares", ["main", "master"]),
]

# patterns that look like record data: any file with a number + side
DATA_EXT = (".json", ".csv", ".txt", ".md", ".cert", ".tsv", ".yaml",
             ".yml", ".py", ".lean", ".toml")


def mirror(repo, branch):
    url = f"https://codeload.github.com/{repo}/tar.gz/refs/heads/{branch}"
    req = urllib.request.Request(url, headers={"User-Agent": "pack-watch38"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def try_branches(repo, branches):
    for b in branches:
        try:
            return mirror(repo, b), b
        except Exception as ex:
            print(f"  {repo}@{b}: {ex}")
    return None, None


def parse_sides(text):
    """Extract (n, side) claims: JSON dicts keyed by n with L/s/side
    values; CSV/TSV rows 'n side'; 'n=11 s=...' md tables; cert
    '<n> <S>' lines."""
    found = {}
    # JSON dict of records
    try:
        j = json.loads(text)
        if isinstance(j, dict):
            for k, v in j.items():
                try:
                    n = int(k)
                except Exception:
                    continue
                if isinstance(v, dict):
                    for kk in ("L", "s", "side", "bound", "value"):
                        if kk in v and isinstance(v[kk], (int, float)):
                            found[n] = float(v[kk])
                            break
                elif isinstance(v, (int, float)):
                    found[n] = float(v)
    except Exception:
        pass
    # cert lines: '<n> <S>' where S rational or decimal
    for m in re.finditer(r"^\s*(\d{1,4})\s+(\d+(?:\.\d+)?(?:/\d+)?"
                         r"(?:\.\d+)?)\s*$", text, re.M):
        n = int(m.group(1))
        s = m.group(2)
        try:
            found.setdefault(n, float(eval(s)) if "/" in s else float(s))
        except Exception:
            pass
    # csv/tsv: n,side
    for m in re.finditer(r"^\s*(\d{1,4})\s*[,;\t]\s*(\d+\.\d+)\s*$",
                          text, re.M):
        found.setdefault(int(m.group(1)), float(m.group(2)))
    # md/lean 'n = 11' 's = 2.5': pair nearby
    for m in re.finditer(r"n\s*=\s*(\d{1,4}).{0,120}?[sS](?:ide)?\s*"
                         r"(?:=|:)\s*(\d+\.\d+)", text, re.S):
        found.setdefault(int(m.group(1)), float(m.group(2)))
    return found


def main():
    report = {}
    for repo, branches in REPOS:
        print(f"== {repo}")
        blob, br = try_branches(repo, branches)
        if blob is None:
            report[repo] = {"status": "unreachable"}
            continue
        tf = tarfile.open(fileobj=io.BytesIO(blob))
        members = tf.getmembers()
        files = {}
        for m in members:
            if m.isfile() and m.name.endswith(DATA_EXT) and m.size < 2_000_000:
                name = m.name
                if any(x in name for x in ("test", "node_modules", ".github")):
                    continue
                try:
                    files[name] = tf.extractfile(m).read().decode(
                        "utf-8", "ignore")
                except Exception:
                    pass
        # which files carry (n, side) pairs
        best = {}
        carriers = {}
        for name, text in files.items():
            got = parse_sides(text)
            got = {n: s for n, s in got.items() if 1 <= n <= 1000 and 0.5 < s < 120}
            if len(got) >= 3:
                carriers[name] = len(got)
                for n, s in got.items():
                    if n not in best or s < best[n]:
                        best[n] = s
        print(f"  branch {br}: {len(members)} members, "
              f"{len(files)} data files, {len(carriers)} carriers, "
              f"{len(best)} distinct (n, side)")
        for name, cnt in sorted(carriers.items(), key=lambda kv: -kv[1])[:6]:
            print(f"    carrier: {name} ({cnt})")
        # compare to table
        beats = []
        for n, s in sorted(best.items()):
            cur = TAB[str(n)]["L"]
            if s < cur - 1e-9:
                beats.append({"n": n, "their": s, "ours": cur,
                              "gain": (cur - s) / math.sqrt(n)})
        beats.sort(key=lambda b: -b["gain"])
        print(f"  WOULD BEAT US: {len(beats)}"
              + (f" (top: {[(b['n'], round(b['gain'],8)) for b in beats[:5]]})" if beats else ""))
        report[repo] = {"branch": br, "members": len(members),
                        "carriers": {k: v for k, v in carriers.items()},
                        "sides_found": len(best),
                        "would_beat": beats}
    json.dump(report, open(OUT, "w"), indent=1)
    print(f"ledger -> {OUT}")


if __name__ == "__main__":
    main()
