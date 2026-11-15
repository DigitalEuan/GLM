#!/usr/bin/env python3
"""portable_paths36.py — run 36: re-apply the run-35 portability fix.

The run-35 session (lost; recorded in upload/run35_NOTES.md part (d))
fixed the active-channel scripts' hard-coded /home/z/my-project root so
paths resolve from the script location. The remote carries the
pre-run-35 scripts; this patcher re-applies the fix to the same list:
cascade3, closure_apply, final_assembly, root_audit, verify_current,
score_submission, import_mishapolk, fetch_mishapolk, leech_core,
octad_moves, leech_map, galois_certs. (import_atlas.py was already
portable; historical scripts stay replay-only, as recorded.)

Behavior is unchanged in this sandbox (same absolute paths); verified
by a channel re-run requiring a bit-identical table.
"""
import py_compile
import re

W = "/home/z/my-project"
ROOT_EXPR = 'os.path.dirname(os.path.dirname(os.path.abspath(__file__)))'

PATCHES = {
    "scripts/cascade3.py": [
        ('SUB = "/home/z/my-project/workspace/submission"',
         f'SUB = {ROOT_EXPR} + "/workspace/submission"'),
    ],
    "scripts/closure_apply.py": [
        ('SUB = "/home/z/my-project/workspace/submission"',
         f'SUB = {ROOT_EXPR} + "/workspace/submission"'),
    ],
    "scripts/final_assembly.py": [
        ('SUB = "/home/z/my-project/workspace/submission"',
         f'SUB = {ROOT_EXPR} + "/workspace/submission"'),
    ],
    "scripts/root_audit.py": [
        ('W = "/home/z/my-project"',
         f'W = {ROOT_EXPR}'),
    ],
    "scripts/verify_current.py": [
        ('WS = "/home/z/my-project/workspace"',
         f'WS = {ROOT_EXPR} + "/workspace"'),
    ],
    "scripts/score_submission.py": [
        ('path = sys.argv[1] if len(sys.argv) > 1 else "/home/z/my-project/workspace/submission/submission.csv"',
         f'path = sys.argv[1] if len(sys.argv) > 1 else {ROOT_EXPR} + "/workspace/submission/submission.csv"'),
    ],
    "scripts/import_mishapolk.py": [
        ('sys.path.insert(0, "/home/z/my-project/scripts")',
         'sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))'),
        ('W = "/home/z/my-project"',
         f'W = {ROOT_EXPR}'),
    ],
    "scripts/fetch_mishapolk.py": [
        ('W = "/home/z/my-project"',
         f'W = {ROOT_EXPR}'),
    ],
    "scripts/leech_core.py": [
        ('OUT = "/home/z/my-project/download/leech_core.json"',
         f'OUT = {ROOT_EXPR} + "/download/leech_core.json"'),
    ],
    "scripts/octad_moves.py": [
        ('OUT = "/home/z/my-project/download/octad_moves.json"',
         f'OUT = {ROOT_EXPR} + "/download/octad_moves.json"'),
    ],
    "scripts/leech_map.py": [
        ('TABLE = json.load(open("/home/z/my-project/download/table.json"))',
         f'TABLE = json.load(open({ROOT_EXPR} + "/download/table.json"))'),
        ('CERTS = json.load(open("/home/z/my-project/download/galois_certificates.json"))',
         f'CERTS = json.load(open({ROOT_EXPR} + "/download/galois_certificates.json"))'),
        ('OUT = "/home/z/my-project/download/leech_map.json"',
         f'OUT = {ROOT_EXPR} + "/download/leech_map.json"'),
    ],
    "scripts/galois_certs.py": [
        ('HERE = "/home/z/my-project/scripts"',
         'HERE = os.path.dirname(os.path.abspath(__file__))'),
        ('TAB = "/home/z/my-project/workspace/submission/table.json"',
         f'TAB = {ROOT_EXPR} + "/workspace/submission/table.json"'),
        ('json.dump(certs, open("/home/z/my-project/workspace/submission/galois_certificates.json", "w"),',
         f'json.dump(certs, open({ROOT_EXPR} + "/workspace/submission/galois_certificates.json", "w"),'),
        ('json.dump(new_members, open("/home/z/my-project/workspace/submission/theta30_new_members.json", "w"),',
         f'json.dump(new_members, open({ROOT_EXPR} + "/workspace/submission/theta30_new_members.json", "w"),'),
    ],
}

for rel, pairs in PATCHES.items():
    src = open(f"{W}/{rel}").read()
    for old, new in pairs:
        if new in src:            # already applied (idempotent re-run)
            continue
        assert old in src, f"{rel}: pattern not found: {old[:60]!r}"
        src = src.replace(old, new, 1)
    # the replacement uses os.path — make sure os is imported
    body = re.sub(r'""".*?"""', "", src, count=1, flags=re.S)
    if not re.search(r"^import os\b", body, re.M):
        # insert after the first import line
        m = re.search(r"^import .*$", body, re.M)
        src = src.replace(m.group(0), "import os\n" + m.group(0), 1)
    open(f"{W}/{rel}", "w").write(src)
    py_compile.compile(f"{W}/{rel}", doraise=True)
    print(f"patched + compiles: {rel}")

# no active-channel script may still hardcode the root
ACTIVE = list(PATCHES) + ["scripts/fetch_candidates.py", "scripts/import_candidates.py"]
for rel in ACTIVE:
    try:
        s = open(f"{W}/{rel}").read()
    except FileNotFoundError:
        continue
    assert "/home/z/my-project" not in s, f"{rel} still hardcodes the root"
print("all 12 patched, compiled, root-free")
