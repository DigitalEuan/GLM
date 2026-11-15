#!/usr/bin/env python3
"""Scan a Lean project for sorry/admit/axiom; optionally run `lake build`.
Usage: python3 lean_ledger.py PROJECT_DIR [--build]
"""
import argparse, os, re, subprocess, sys

SORRY_LINE = re.compile(r"^\s*(sorry|admit)\s*$")  # proof-body line only; ignores comments/identifiers
AXIOM_RE = re.compile(r"^\s*axiom\s+(\w+)")
DECL_RE = re.compile(r"^\s*(theorem|lemma|def|example|axiom)\s+(\w+)")

def scan_file(path):
    sorry, axioms, current = [], [], None
    for line in open(path):
        m = DECL_RE.match(line)
        if m: current = m.group(2)
        if AXIOM_RE.match(line): axioms.append(AXIOM_RE.match(line).group(1))
        if SORRY_LINE.match(line) and current: sorry.append(current)
    return sorry, axioms

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--build", action="store_true")
    args = ap.parse_args()
    all_sorry, all_axioms, n = [], [], 0
    for root, _, files in os.walk(args.project):
        for fn in files:
            if fn.endswith(".lean"):
                n += 1
                s, a = scan_file(os.path.join(root, fn))
                all_sorry += s; all_axioms += a
    print(f"Scanned {n} file(s): sorry={len(all_sorry)} {sorted(set(all_sorry)) or ''}, axioms={len(all_axioms)} {sorted(set(all_axioms)) or ''}")
    if args.build:
        on_path = any(os.path.exists(os.path.join(p, "lake")) for p in os.environ.get("PATH", "").split(os.pathsep))
        if not on_path:
            print("BUILD: lake not on PATH — project ready for `lake build` elsewhere."); return 0
        proc = subprocess.run(["lake", "build"], cwd=args.project, capture_output=True, text=True, timeout=600)
        print(proc.stdout)
        if proc.returncode == 0: print("BUILD: succeeded."); return 0
        print("BUILD FAILED:"); print(proc.stderr); return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
