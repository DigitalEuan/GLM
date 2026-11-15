#!/usr/bin/env python3
r"""fetch_candidates.py — run 35/36 P3 source watch: mirror the evand/
square-packing candidate certificates (the register's intake pipeline).

Source (external data, attributed):
  github.com/evand/square-packing  search/packer/candidates/*.cert
  "exact certificate: unit squares, centre (x, y), rotation
   (c, s) = ((1-t^2)/(1+t^2), 2t/(1+t^2))" — exact rationals, side S.

Method: one codeload tarball of the repo tip (no API — the API is
rate-limited; codeload and raw are not), extracted in /tmp; every
*.cert under search/packer/candidates/ is mirrored into
workspace/sources/candidates/ (skipped if already present with the
same sha).  Writes snapshot.json (name -> sha) for the weekly diff.

The 21 noise-level "wins" (~1.8e-9: the same packings as our stored
rows less the +2e-9 finalize inflation) are handled downstream by
import_candidates.py's MIN_GAIN = 1e-7 — the table must not churn on
re-runs.
"""
import hashlib
import json
import os
import shutil
import sys
import tarfile
import tempfile
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, "workspace/sources/candidates")
TARBALL = ("https://codeload.github.com/evand/square-packing/tar.gz/"
           "refs/heads/main")


def sha(b):
    return hashlib.sha256(b).hexdigest()[:16]


def main():
    force = "--refresh" in sys.argv
    os.makedirs(DST, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        req = urllib.request.Request(TARBALL, headers={"User-Agent": "pack-watch"})
        blob = urllib.request.urlopen(req, timeout=120).read()
        tgz = os.path.join(td, "repo.tgz")
        open(tgz, "wb").write(blob)
        with tarfile.open(tgz) as tf:
            wanted = [m for m in tf.getmembers()
                      if m.name.count("/search/packer/candidates/") == 1
                      and m.name.endswith(".cert")
                      and m.isfile()]
            tf.extractall(td, members=wanted)
        certs = {}
        for m in wanted:
            name = os.path.basename(m.name)
            certs[name] = open(os.path.join(td, m.name), "rb").read()
    old = {}
    snap_path = os.path.join(DST, "snapshot.json")
    if os.path.exists(snap_path):
        old = json.load(open(snap_path))
    snap, fetched, kept = {}, 0, 0
    for name in sorted(certs):
        path = os.path.join(DST, name)
        digest = sha(certs[name])
        snap[name] = digest
        if not force and os.path.exists(path) and sha(open(path, "rb").read()) == digest:
            kept += 1
            continue
        open(path, "wb").write(certs[name])
        fetched += 1
    json.dump(snap, open(snap_path, "w"), indent=1, sort_keys=True)
    print(f"mirrored: {len(certs)} candidate certs ({fetched} fetched, "
          f"{kept} unchanged); snapshot.json written")


if __name__ == "__main__":
    main()
