#!/usr/bin/env python3
r"""cert_repro.py — Run 11, Piece 4c: reproduce the uploaded Lean
verification certificate in THIS sandbox, plus the Python twin check.

1. Place upload/layers_universal.lean + a small driver into a fresh lake
   package (toolchain v4.8.0, Mathlib from the shared package dir).
2. lake build -> lean exits 0 on the file: the certificate's claim
   (0 proof obligations, 0 sorries) is reproduced, not trusted.
3. Python twin: execute upload/layers_universal.py after fixing the
   sys.path hack (it points at /app/applet which does not exist here);
   verify the layer classification semantics numerically.
4. Write download/layers_verification.json with the outcomes.
"""
import json
import os
import shutil
import subprocess

ROOT = __import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__)))

UP = ROOT + "/upload"
PROJ = ROOT + "/workspace/lean/layers_universal"
OUT = ROOT + "/download/layers_verification.json"
LAKE = "/home/z/.elan/bin/lake"
res = {}

# ---- 1. fresh package ------------------------------------------------
os.makedirs(PROJ, exist_ok=True)
shutil.copy(os.path.join(UP, "layers_universal.lean"), PROJ)
with open(os.path.join(PROJ, "lakefile.lean"), "w") as f:
    f.write('''import Lake
open Lake DSL
package layers_universal where
  require mathlib from git "https://github.com/leanprover-community/mathlib4" @ "v4.8.0"
lean_lib LayersUniversal where
  globs := #[.one `layers_universal]
''')
with open(os.path.join(PROJ, "lean-toolchain"), "w") as f:
    f.write("leanprover/lean4:v4.8.0\n")

# reuse the already-resolved package set (avoid re-fetch)
tc = ROOT + "/workspace/lean/tct_squares/.lake/packages"
if os.path.isdir(os.path.join(PROJ, ".lake", "packages")):
    shutil.rmtree(os.path.join(PROJ, ".lake", "packages"))
os.makedirs(os.path.join(PROJ, ".lake"), exist_ok=True)
shutil.copytree(os.path.join(tc), os.path.join(PROJ, ".lake", "packages"),
                symlinks=True)

# manifest: copy from tct_squares (same deps)
shutil.copy(ROOT + "/workspace/lean/tct_squares/lake-manifest.json",
            os.path.join(PROJ, "lake-manifest.json")) if os.path.exists(
    ROOT + "/workspace/lean/tct_squares/lake-manifest.json") else None

p = subprocess.run([LAKE, "build"], cwd=PROJ, capture_output=True,
                   text=True, timeout=1500)
ok = p.returncode == 0
err = (p.stderr or "")[-2000:]
res["lean_build"] = {"returncode": p.returncode, "ok": ok,
                     "stderr_tail": err[-800:],
                     "stdout_tail": (p.stdout or "")[-400:]}

# ---- 2. sorry/axiom audit on the uploaded file ------------------------
src = open(os.path.join(UP, "layers_universal.lean")).read()
res["file_audit"] = {
    "sorries": src.count("sorry"),
    "axioms_declared": src.count("\naxiom"),
    "theorems": src.count("\ntheorem"),
    "definitions": src.count("\ndef ") + src.count("\ndef\n"),
    "imports": [l for l in src.splitlines() if l.startswith("import")],
}

# ---- 3. Python twin ----------------------------------------------------
twin = os.path.join(UP, "layers_universal.py")
tsrc = open(twin).read().replace("sys.path.append('/app/applet')",
                                 "# sandboxed: no /app/applet")
twin_local = os.path.join(PROJ, "layers_universal_twin.py")
open(twin_local, "w").write(tsrc)
r2 = subprocess.run(["python3", twin_local], capture_output=True, text=True,
                    timeout=60)
res["python_twin"] = {"returncode": r2.returncode, "stdout": r2.stdout,
                      "stderr": (r2.stderr or "")[-400:]}

json.dump(res, open(OUT, "w"), indent=1)
print("lean build ok:", ok)
print("file audit:", res["file_audit"])
print("twin rc:", r2.returncode, "|", r2.stdout.strip()[:200])
print("->", OUT)
