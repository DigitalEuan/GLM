#!/usr/bin/env python3
"""restore_from_repo.py — restore the project state from the GitHub
repository after a sandbox recycle (idempotent; safe to re-run).

NOTE (run 19 lesson): this script REPLACES sandbox scripts/ wholesale
with the repo's — any script that exists only in the sandbox (like this
one) is deleted in the process.  The repo is the source of truth: push
new scripts to the repo, or re-create them from the run ledgers.

Sources of truth: /tmp/sqs2 clone (created by REPRODUCE.md A11 if
missing) — workspace/scripts/json/docs + certs.zip; the frontier table
is REBUILT from submission/submission.csv (12-dp states): rows whose
csv-L matches the repo table keep the repo row (full precision,
original src); improved rows take the csv state (src run18-frontier).
Verification: final_assembly.py round-trip (expected 22.823536).
"""
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = "/tmp/sqs2"


def sh(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-2000:])
        print(r.stderr[-2000:])
        raise SystemExit(f"failed: {cmd}")
    return r.stdout


def main():
    if not os.path.exists(os.path.join(REPO, "workspace")):
        sh("git clone --depth 1 "
           "https://github.com/DigitalEuan/squares_in_squares /tmp/sqs2")
    for tgt in ("workspace", "scripts", "json"):
        dst = os.path.join(ROOT, tgt)
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(os.path.join(REPO, tgt), dst)
        print(f"copied {tgt}/ "
              f"({sh(f'find {dst} -type f | wc -l').strip()} files)")
    for f in ("README.md", "REPRODUCE.md", "LICENSE", ".gitattributes"):
        srcf = os.path.join(REPO, f)
        if os.path.exists(srcf):
            shutil.copy(srcf, os.path.join(ROOT, f))
            print(f"copied {f}")

    lists = os.path.join(ROOT, "workspace/sources/atlas/lists")
    certs = os.path.join(lists, "certs")
    if os.path.exists(os.path.join(lists, "certs.zip")):
        if os.path.exists(certs):
            shutil.rmtree(certs)
        sh(f"cd {lists} && unzip -qo certs.zip -x '__MACOSX/*' "
           f"&& rm -rf __MACOSX")
        print("certs extracted:",
              len([f for f in os.listdir(certs) if f.endswith(".cert.gz")]))

    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    import packlib as P
    by_n = P.read_csv(os.path.join(
        ROOT, "workspace/submission/submission.csv"))
    repo_tab = json.load(open(os.path.join(
        ROOT, "workspace/submission/table.json")))
    tab, kept, improved = {}, 0, 0
    for n in range(1, 1001):
        st = by_n[n]
        assert len(st) == n, f"n={n}: {len(st)} squares in csv"
        L_csv = P.verify(st)["L"]
        row = repo_tab[str(n)]
        if abs(L_csv - row["L"]) <= 1e-9:
            tab[str(n)] = row
            kept += 1
        else:
            tab[str(n)] = {"L": L_csv, "state": st, "src": "run18-frontier"}
            improved += 1
    json.dump(tab, open(os.path.join(
        ROOT, "workspace/submission/table.json"), "w"))
    print(f"table rebuilt: {kept} kept, {improved} from csv")
    score = sum(tab[str(n)]["L"] / (n ** 0.5) - 1 for n in range(1, 1001))
    print(f"score: {score:.6f} (expected 22.823536)")

    outp = subprocess.run([sys.executable,
                           os.path.join(ROOT, "scripts/final_assembly.py")],
                          capture_output=True, text=True)
    print(outp.stdout[-800:])
    if outp.returncode != 0:
        print(outp.stderr[-800:])
        raise SystemExit("final_assembly failed")


if __name__ == "__main__":
    main()
