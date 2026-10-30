"""List every glm_universal module that some file imports but the checkout does not contain.

Run from a GLM checkout (the directory holding GLM.py):
    python3 rule30_round10/find_missing_modules.py
Static scan only (the AST of every .py file); nothing is imported or executed.
"""
import ast
import os

files = [os.path.join(d, f) for d, _, fs in os.walk("glm_universal") for f in fs
         if f.endswith(".py")] + ["GLM.py"]


def modpath(m):
    p = m.replace(".", "/")
    if os.path.isfile(p + ".py"):
        return p + ".py"
    if os.path.isfile(p + "/__init__.py"):
        return p + "/__init__.py"
    return None


def defined(path):
    """Names a package __init__ defines itself (not 'from . import x' re-exports)."""
    names = set()
    for n in ast.walk(ast.parse(open(path).read())):
        if isinstance(n, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
            names.add(n.name)
        elif isinstance(n, ast.Assign):
            for tg in n.targets:
                names.update(x.id for x in ast.walk(tg) if isinstance(x, ast.Name))
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
            names.add(n.target.id)
        elif isinstance(n, ast.ImportFrom) and n.module:
            names.update((a.asname or a.name).split(".")[0] for a in n.names)
        elif isinstance(n, ast.Import):
            names.update((a.asname or a.name).split(".")[0] for a in n.names)
    return names


missing = {}
for p in files:
    pkg = os.path.dirname(p).replace("/", ".")
    for n in ast.walk(ast.parse(open(p).read())):
        if isinstance(n, ast.ImportFrom):
            if n.level:
                base = pkg.split(".")
                base = base[:len(base) - (n.level - 1)]
                m = ".".join(base + ([n.module] if n.module else []))
            else:
                m = n.module or ""
            if not m.startswith("glm_universal"):
                continue
            mp = modpath(m)
            if mp is None:
                missing.setdefault(m, set()).add(p)
            elif mp.endswith("__init__.py"):
                dn = defined(mp)
                for a in n.names:
                    if a.name != "*" and modpath(m + "." + a.name) is None and a.name not in dn:
                        missing.setdefault(m + "." + a.name, set()).add(p)
        elif isinstance(n, ast.Import):
            for a in n.names:
                if a.name.startswith("glm_universal") and modpath(a.name) is None:
                    missing.setdefault(a.name, set()).add(p)

for m, ps in sorted(missing.items()):
    print(f"{m}  <- {len(ps)} file(s): {', '.join(sorted(ps)[:4])}{' ...' if len(ps) > 4 else ''}")
print(f"{len(missing)} missing module(s)")
