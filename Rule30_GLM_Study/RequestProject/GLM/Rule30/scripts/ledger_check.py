#!/usr/bin/env python3
"""Ledger check for the Rule 30 / GLM package (Round 21).

Checks that every Lean name cited in `claims.csv` exists in the built package, records the axiom
footprint of each, and flags inconsistencies between a row's evidence class and its footprint:

* a cited name that does not exist                         -> ERROR
* an axiom outside the standard set                        -> ERROR
  (allowed: propext, Classical.choice, Quot.sound, and for CERT/EXH rows also
   Lean.ofReduceBool / Lean.trustCompiler, which `native_decide` introduces)
* a FORMAL row whose names use `native_decide`             -> WARNING (should probably be CERT)
* a row marked proved with no Lean name and class FORMAL   -> WARNING

Optionally writes the ledger as JSON "wheel carriers" for the GLM's theorem wheel
(`--wheel out.json`): one object per row with id, claim, class, status, Lean names and axioms.

Usage (from the project root, after `lake build RequestProject.GLM.Rule30`):

    python3 RequestProject/GLM/Rule30/scripts/ledger_check.py [--wheel wheel.json]

Exit status 0 if there are no ERRORs.
"""
import csv
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)                       # RequestProject/GLM/Rule30
ROOT = os.path.abspath(os.path.join(PKG, "..", "..", ".."))
LEDGER = os.path.join(PKG, "claims.csv")
NAMESPACE = "GLM.Rule30"
STANDARD = {"propext", "Classical.choice", "Quot.sound"}
COMPILER = {"Lean.ofReduceBool", "Lean.trustCompiler"}
NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_'.!?]*$")


EXTRA_DIRS = [os.path.join(PKG, "..", "HypothesisEngine"),   # Round 39: the portable engine
              os.path.join(PKG, "..", "Escalation")]         # Round 43: escalation boundaries
EXTRA_IMPORTS = ["RequestProject.GLM.HypothesisEngine.BenchmarksData",
                 "RequestProject.GLM.HypothesisEngine.DialogueChecks",   # Round 41
                 "RequestProject.GLM.HypothesisEngine.TaxChecksData",    # Round 42
                 "RequestProject.GLM.Escalation",                         # Round 43
                 "RequestProject.GLM.HypothesisEngine.NeedsWheel",        # Round 44
                 "RequestProject.GLM.HypothesisEngine.WheelChecksData",   # Round 44
                 "RequestProject.GLM.HypothesisEngine.GateLoop",          # Round 45
                 "RequestProject.GLM.HypothesisEngine.GateLoopData",      # Round 45
                 "RequestProject.GLM.HypothesisEngine"]                   # Round 46 (Wheel) and later


def _lean_paths():
    for d in [PKG] + [x for x in EXTRA_DIRS if os.path.isdir(x)]:
        for f in os.listdir(d):
            if f.endswith(".lean"):
                yield d, f


def namespaces():
    found = {NAMESPACE, "GLM"}
    for d, f in _lean_paths():
        stack = []  # nested namespaces (Round 48: `namespace A` inside `namespace B.C`)
        for line in open(os.path.join(d, f)):
            m = re.match(r"^namespace\s+(\S+)", line)
            if m:
                stack.append(m.group(1))
                found.add(m.group(1))
                found.add(".".join(stack))
                continue
            m = re.match(r"^end\s+(\S+)", line)
            if m and stack and stack[-1] == m.group(1):
                stack.pop()
    return sorted(found, key=lambda n: (n != NAMESPACE, n))


def lean_files():
    return {f[:-5] for _, f in _lean_paths()}


def parse_refs(field, files):
    """Split a lean_reference field into (file, declaration) pairs; bare names inherit the
    previous file.  Non-Lean tokens (paths, '(none)', prose) are ignored."""
    out, current = [], None
    for tok in field.split(";"):
        tok = tok.strip()
        if not tok or not NAME_RE.match(tok):
            continue
        head, _, rest = tok.partition(".")
        if rest and head in files:
            current = head
            out.append((head, rest))
        else:
            out.append((current or "?", tok))
    return out


def main():
    wheel_path = None
    if "--wheel" in sys.argv:
        wheel_path = sys.argv[sys.argv.index("--wheel") + 1]
    files = lean_files()
    rows = list(csv.DictReader(open(LEDGER, newline="")))
    refs = {r["id"]: parse_refs(r["lean_reference"], files) for r in rows}
    names = sorted({d for v in refs.values() for _, d in v})

    spaces = namespaces()
    # One Lean process per chunk of commands: a single file with tens of thousands of
    # `#print axioms` commands overflows Lean's stack, silently dropping later results.
    cmds = [f"#print axioms {ns}.{d}" for d in names for ns in spaces]
    chunk = 4000
    texts = []
    for i in range(0, len(cmds), chunk):
        with tempfile.NamedTemporaryFile("w", suffix=".lean", delete=False) as fh:
            fh.write("import RequestProject.GLM.Rule30\n")
            for imp in EXTRA_IMPORTS:
                fh.write(f"import {imp}\n")
            fh.write("\n".join(cmds[i:i + chunk]) + "\n")
            tmp = fh.name
        res = subprocess.run(["lake", "env", "lean", "-DmaxErrors=1000000", tmp], cwd=ROOT,
                             capture_output=True, text=True)
        os.unlink(tmp)
        out = res.stdout + res.stderr
        if "Stack overflow" in out or res.returncode not in (0, 1):
            print(f"FATAL: Lean aborted on chunk {i // chunk} (return code {res.returncode})")
            sys.exit(2)
        texts.append(out)
    text = "\n".join(texts)
    if os.environ.get("LEDGER_RAW"):
        open(os.environ["LEDGER_RAW"], "w").write(text)

    axioms, fullname, missing = {}, {}, set()
    text = re.sub(r"\s+", " ", text)
    for ns in spaces:
        pre = re.escape(ns) + r"\."
        for m in re.finditer(r"'" + pre + r"([^']+)' depends on axioms: \[([^\]]*)\]", text):
            if m.group(1) not in axioms:
                axioms[m.group(1)] = sorted(a.strip() for a in m.group(2).split(",") if a.strip())
                fullname[m.group(1)] = f"{ns}.{m.group(1)}"
        for m in re.finditer(r"'" + pre + r"([^']+)' does not depend on any axioms", text):
            if m.group(1) not in axioms:
                axioms[m.group(1)] = []
                fullname[m.group(1)] = f"{ns}.{m.group(1)}"
    for d in names:
        if d not in axioms:
            missing.add(d)

    errors, warnings, carriers = [], [], []
    for r in rows:
        cls, rid = r["evidence_class"], r["id"]
        used = set()
        for f, d in refs[rid]:
            if d in missing:
                errors.append(f"{rid}: Lean name {f}.{d} not found")
            else:
                used |= set(axioms.get(d, []))
        allowed = STANDARD | (COMPILER if cls in ("CERT", "EXH") else set())
        extra = {a for a in used if a not in allowed and a not in COMPILER}
        if extra:
            errors.append(f"{rid}: non-standard axioms {sorted(extra)}")
        if cls == "FORMAL" and used & COMPILER and "native_decide" not in r.get("notes", ""):
            warnings.append(f"{rid}: class FORMAL but uses native_decide (consider CERT)")
        if cls == "FORMAL" and r["status"] == "proved" and not refs[rid]:
            warnings.append(f"{rid}: FORMAL/proved row without a parsable Lean name")
        carriers.append({"id": rid, "claim": r["claim"], "class": cls, "status": r["status"],
                         "lean": [fullname.get(d, d) for _, d in refs[rid]],
                         "axioms": sorted(used), "notes": r.get("notes", "")})

    print(f"rows: {len(rows)}   distinct Lean names: {len(names)}   missing: {len(missing)}")
    for e in errors:
        print("ERROR  ", e)
    for w in warnings:
        print("WARNING", w)
    if wheel_path:
        json.dump(carriers, open(wheel_path, "w"), indent=1)
        print(f"wrote {len(carriers)} carriers to {wheel_path}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
