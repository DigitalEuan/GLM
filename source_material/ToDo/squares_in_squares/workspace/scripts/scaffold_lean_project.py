#!/usr/bin/env python3
"""Scaffold a Lean 4 Lake project from a TCT lemma spec.
Spec JSON: {"module":"TCT","imports":[],"definitions":[{"name","type","value"}],
"axioms":[{"name","type","note"}],"lemmas":[{"name","type","proof" or null,"gap" or null}]}
proof=null -> sorry + GAP comment. Writes lean-toolchain=leanprover/lean4:stable (elan resolves it).
Usage: python3 scaffold_lean_project.py --spec spec.json --out proj/ [--with-mathlib] [--toolchain TAG]
"""
import argparse, json, os, sys

LAKEFILE = """import Lake
open Lake DSL
package {name} where
  moreServerArgs := #["-DwarningAsError=false"]
lean_lib {mod} where
@[default_target] lean_exe «check» where
  root := «Main»
"""
MAIN = """import {mod}
def main : IO Unit := pure ()
"""
TOOLCHAIN_DEFAULT = "leanprover/lean4:stable"

def render_lemma(lem):
    name, typ = lem["name"], lem["type"].strip()
    proof, gap = lem.get("proof"), lem.get("gap")
    if proof and proof.strip():
        return f"theorem {name} : {typ} := by\n  {proof.strip()}\n"
    gap_line = f"  -- GAP: {gap}" if gap else "  -- GAP: (no description)"
    return f"theorem {name} : {typ} := by\n  sorry\n{gap_line}\n"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--name", default="tct")
    ap.add_argument("--toolchain", default=TOOLCHAIN_DEFAULT)
    ap.add_argument("--with-mathlib", action="store_true")
    args = ap.parse_args()
    spec = json.load(open(args.spec))
    mod = spec.get("module", "TCT")
    imports = list(spec.get("imports", []))
    if args.with_mathlib:
        imports = ["Mathlib"] + [i for i in imports if i != "Mathlib"]
    os.makedirs(os.path.join(args.out, mod), exist_ok=True)
    open(os.path.join(args.out, "lean-toolchain"), "w").write(args.toolchain + "\n")
    lakefile = LAKEFILE.format(name=args.name, mod=mod)
    if args.with_mathlib:
        lakefile = lakefile.replace("package " + args.name + " where",
            f'require mathlib from git "https://github.com/leanprover-community/mathlib4" @ "{args.toolchain.split(":")[-1]}"\n\npackage {args.name} where')
    open(os.path.join(args.out, "lakefile.lean"), "w").write(lakefile)
    open(os.path.join(args.out, "Main.lean"), "w").write(MAIN.format(mod=f"{mod}.Basic"))
    lines = []
    for imp in imports: lines.append(f"import {imp}")
    if imports: lines.append("")
    lines.append(f"namespace {mod}\n")
    proved = sorry = axioms = defs = 0
    sorry_list, axiom_list = [], []
    for d in spec.get("definitions", []):
        defs += 1; lines.append(f"def {d['name']} : {d['type']} := {d['value']}")
    if defs: lines.append("")
    for a in spec.get("axioms", []):
        axioms += 1; lines.append(f"axiom {a['name']} : {a['type']}")
        if a.get("note"): lines.append(f"-- assumed premise: {a['note']}")
        axiom_list.append((a["name"], a["type"], a.get("note", "")))
    if axioms: lines.append("")
    for lem in spec.get("lemmas", []):
        if lem.get("proof"): proved += 1
        else:
            sorry += 1; sorry_list.append((lem["name"], lem["type"], lem.get("gap", "")))
        lines.append(render_lemma(lem))
    lines.append(f"end {mod}\n")
    open(os.path.join(args.out, mod, "Basic.lean"), "w").write("\n".join(lines))
    ledger = [f"# Development-required ledger — {args.name}", "",
        f"- lemmas total: {proved+sorry}", f"- proved (sorry-free): **{proved}**",
        f"- `sorry` (development required): **{sorry}**", f"- axioms: **{axioms}**", f"- definitions: {defs}", ""]
    if sorry_list:
        ledger += ["## sorry lemmas", ""]
        for n, t, g in sorry_list: ledger += [f"- `{n}` : `{t}`", f"  - gap: {g or '(undescribed)'}"]
        ledger.append("")
    if axiom_list:
        ledger += ["## axioms (assumed)", ""]
        for n, t, note in axiom_list: ledger.append(f"- `{n}` : `{t}` — {note}")
        ledger.append("")
    fence = chr(96) * 3
    ledger += ["## To verify", "", fence + "bash", f"cd {args.out} && lake build", fence,
        "0 sorry = fully described; each sorry above is exactly what remains."]
    open(os.path.join(args.out, "SORRY_LEDGER.md"), "w").write("\n".join(ledger) + "\n")
    print(f"Scaffolded {args.out}: {proved} proved, {sorry} sorry, {axioms} axioms, {defs} defs; toolchain {args.toolchain}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
