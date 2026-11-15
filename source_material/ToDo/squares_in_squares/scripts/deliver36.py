#!/usr/bin/env python3
r"""deliver36.py — run 36 deliverables (the re-establishment).

The user's ask: re-establish the elsewhere run-35 session here and run
through to an updated csv. Checks (mechanical, script-computed):
the updated submission.csv/table.json at 22.642386651/543; the
re-executed import matches the run-35 record to the digit; the census
== the live table; the transport rule (STATUS tail byte-identical,
body zero-mention); the syncs (NEXT_STEPS/RUN_NOTES/table/csv/docs
into download/); run36/ artifact tree + MANIFEST.
"""
import json
import math
import os
import shutil
import collections

W = "/home/z/my-project"
DL = f"{W}/download"
R36 = f"{DL}/run36"
TAB = f"{W}/workspace/submission/table.json"

tab = json.load(open(TAB))
score = sum(r["L"] / math.sqrt(int(k)) - 1 for k, r in tab.items())
assert abs(score - 22.642386651) < 2e-9, score
beats = sum(1 for k in tab if tab[k]["L"] < math.ceil(math.sqrt(int(k))) - 1e-12)
assert beats == 543, beats

# the re-executed import matches the run-35 record to the digit
led = json.load(open(f"{W}/workspace/push/import_candidates35.json"))
assert led["mode"] == "applied" and led["applied_total"] == 9
assert abs(led["direct_gain"] - 0.003359) < 1e-6
RECORD = {172: 13.617935700, 175: 13.764050053, 182: 13.970916438,
          204: 14.804361386, 260: 16.633520953, 268: 16.872499520,
          293: 17.623065214, 303: 17.901832753, 304: 17.920944095}
# the applied set = the rows whose cert won best-L per n and is in the table
by_n = {}
for r in led["rows"]:
    if isinstance(r.get("tid"), str) and r.get("new") is not None:
        n = r["n"]
        if n not in by_n or r["new"] < by_n[n]["new"]:
            by_n[n] = r
assert sorted(by_n) == sorted(RECORD), sorted(by_n)
for n, r in by_n.items():
    # the table row must match the record; and the table's src must
    # carry the winning cert's T-id
    assert abs(tab[str(n)]["L"] - RECORD[n]) < 5e-10, (n, tab[str(n)]["L"], RECORD[n])
    assert r["tid"] in tab[str(n)]["src"], (n, tab[str(n)]["src"])
    assert abs(r["new"] - RECORD[n]) < 5e-10, (n, r["new"])

ra = json.load(open(f"{W}/workspace/push/root_audit35.json"))
assert ra["table_laws"]["monotone_envelope"]["violations"] == []
assert ra["table_laws"]["shell_law"]["violations"] == []
assert ra["fixpoint_audit"]["above_env"] == 0
assert ra["fixpoint_audit"]["open_rows"] == 305
assert abs(ra["aggregate"]["gap_to_leader"] - 0.587965) < 1e-5

probe = json.load(open(f"{W}/workspace/push/probe_wedges36.json"))
assert probe["cores"] == 217 and probe["total_extra_squares"] == 0

# ---------------------------------------------------------------- ledger
out = {
 "run": 36, "date": "2026-11-07",
 "user_request": ("I ran a session elsewhere but it stopped abruptly "
                   "leaving only these documents attached, it was a "
                   "successful run - can we get it established here and "
                   "run through to an updated csv please."),
 "found_at_turn_start": {
  "local_tree": "rolled back to the run-27 era (runs 28-35 gone)",
  "git_remote": "missing from config; restored by URL - the GitHub "
                 "remote carried the run-34 state (table 22.645990613/543, "
                 "116 scripts, 68 ledgers, Lean base, notes through 34)",
  "run35_tree": "lost with its elsewhere session; 5 documents survived "
                "and were attached (installed as canonical)"},
 "executed": {
  "adoption": ("sandbox-lineage-27 preserved; upload/ protected + "
               "md5-verified; channel bit-identity verified BEFORE any "
               "edit (22.645990613/543, cascade 0, closure fixpoint, "
               "assembly 0 issues)"),
  "portability_patch": ("12 channel scripts re-patched "
                        "(portable_paths36.py); channel re-run stayed "
                        "bit-identical"),
  "run35_reexecuted": {
   "import": "fetch_candidates.py (tarball) + import_candidates.py: "
             "9 rows, direct 0.003359 - matches the record to the digit",
   "cascade": "n=338 converted (+0.000245) from the n=303 record",
   "channel": "closure fixpoint 0 rounds; assembly 0 issues",
   "rescore": "independent score_submission.py agrees 22.642387",
   "wedge_probe": "re-verified: 217 cores, 0 extra squares",
   "formal_layer": "TCT/Laws.lean reconstructed statement-for-statement "
                   "from the paper §9 table (3 defs + 11 theorems + 2 "
                   "axioms); SORRY_LEDGER refreshed; honest no-elan "
                   "build note"},
  "docs": ("run-35 documents installed as canonical; README from the "
           "STATUS tail; run-36 updates applied (STATUS row 36; "
           "NEXT_STEPS rows 33-36 + failure 17/17c ported + entry 10; "
           "REPRODUCE A24-A26; RUN_NOTES Run 35 port + Run 36; "
           "notes/run35+36_NOTES.md")},
 "score": {"before": 22.645990613, "after": 22.642386651,
           "delta": -0.003603962,
           "note": "the run-35 score move, reproduced exactly"},
 "beats_grid": 543,
 "gap_to_leader": 0.587965,
 "updated_csv": "download/submission.csv (500,500 rows, round-trip 0 "
                "issues) - the user's ask",
 "next": ["P3 weekly (the only item that has paid)",
          "start of turn: fetch origin, compare eras (failure 16a/18)",
          "every run: update all documents together + push (failure 18)"],
}
os.makedirs(R36, exist_ok=True)
os.makedirs(f"{R36}/scripts", exist_ok=True)
os.makedirs(f"{R36}/workspace/push", exist_ok=True)
json.dump(out, open(f"{W}/download/run36_outcomes.json", "w"), indent=1)
json.dump(out, open(f"{W}/workspace/push/run36_outcomes.json", "w"), indent=1)
print("1. ledgers -> download/run36_outcomes.json + workspace/push/")

# ------------------------------------------------------------ run36 tree
for s in ("portable_paths36.py", "fetch_candidates.py",
          "import_candidates.py", "probe_wedges36.py", "docs36.py",
          "deliver36.py"):
    shutil.copy(f"{W}/scripts/{s}", f"{R36}/scripts/{s}")
for j in ("import_candidates35.json", "root_audit35.json",
          "probe_wedges36.json", "run36_outcomes.json"):
    shutil.copy(f"{W}/workspace/push/{j}", f"{R36}/workspace/push/{j}")
for d in ("STATUS.md", "NEXT_STEPS.md", "REPRODUCE.md", "README.md",
          "GLM_INVESTIGATION.md"):
    shutil.copy(f"{W}/{d}", f"{R36}/{d}")
shutil.copy(f"{W}/notes/RUN_NOTES.md", f"{R36}/RUN_NOTES.md")
shutil.copy(f"{W}/notes/run35_NOTES.md", f"{R36}/run35_NOTES.md")
shutil.copy(f"{W}/notes/run36_NOTES.md", f"{R36}/run36_NOTES.md")
shutil.copy(f"{W}/workspace/lean/tct_squares/TCT/Laws.lean",
            f"{R36}/Laws.lean")
shutil.copy(f"{W}/workspace/lean/tct_squares/SORRY_LEDGER.md",
            f"{R36}/SORRY_LEDGER.md")
man = """# Run 36 — the re-establishment of run 35 (MANIFEST)

Run ledger: `download/run36_outcomes.json`. **Score 22.642386651**
(543/1000 beat grid; gap 0.587965) — the run-35 score move reproduced
exactly from its five surviving documents, with the updated
`submission.csv` the user asked for.

## What is here

| file | role |
|---|---|
| `STATUS.md` / `NEXT_STEPS.md` / `REPRODUCE.md` / `README.md` / `GLM_INVESTIGATION.md` | the run-36 documents (base: the attached run-35 set, installed as canonical) |
| `RUN_NOTES.md` / `run35_NOTES.md` / `run36_NOTES.md` | the run ledger (Run 35 ported + Run 36) |
| `scripts/fetch_candidates.py` + `import_candidates.py` | the re-executed run-35 import (73 certs; 9 records, direct 0.003359) |
| `scripts/portable_paths36.py` | the portability patch (12 channel scripts) |
| `scripts/probe_wedges36.py` | the wedge probe re-verification (217 cores, 0 extra) |
| `scripts/docs36.py` / `deliver36.py` | this run's doc + delivery scripts |
| `workspace/push/import_candidates35.json` | the import ledger (dry + applied) |
| `workspace/push/root_audit35.json` | laws 999/999 + 937/937; fixpoint 0/305; gap 0.587965 |
| `workspace/push/probe_wedges36.json` | the wedge-probe ledger |
| `Laws.lean` / `SORRY_LEDGER.md` | the reconstructed formal layer (run-35 state; build note) |

## The updated csv

`download/submission.csv` (500,500 rows; round-trip 0 issues) and
`download/table.json` — both at the run-35/36 state.
"""
open(f"{R36}/MANIFEST.md", "w").write(man)
print("2. download/run36/ + MANIFEST")

# ------------------------------------------------------- 3-copy syncs
shutil.copy(f"{W}/NEXT_STEPS.md", f"{DL}/NEXT_STEPS.md")
shutil.copy(f"{W}/notes/RUN_NOTES.md", f"{DL}/RUN_NOTES.md")
shutil.copy(TAB, f"{DL}/table.json")
shutil.copy(f"{W}/workspace/submission/submission.csv", f"{DL}/submission.csv")
shutil.copy(f"{W}/notes/run36_NOTES.md", f"{DL}/run36_NOTES.md")
print("3. syncs -> download/ (NEXT_STEPS, RUN_NOTES, run36_NOTES, table, csv)")

# --------------------------------------------------- transport checks
st = open(f"{W}/STATUS.md").read()
rd = open(f"{W}/README.md").read()
head = rd.splitlines()[0]
i = st.find("\n---\n\n" + head)
assert i > 0
body, tail = st[:i], st[i + len("\n---\n\n"):]
assert tail == rd, "STATUS tail != README (byte-for-byte)"
assert "README" not in body, "body mentions the other file"
for needle in ("22.642387", "0.587965", "543 / 1000", "305"):
    assert needle in body, needle
# census == live table
cnt = collections.Counter()
for k, r in tab.items():
    b = r.get("src", "?").split(":")[0]
    if b.startswith("gobel"):
        b = "gobel"
    cnt[b] += 1
assert dict(cnt) == {"grid": 457, "mishapolk": 207, "chain3": 88,
                     "exact": 77, "run18-frontier": 68, "gobel": 54,
                     "removal": 18, "closure": 18, "register": 10,
                     "aux": 3}, dict(cnt)
print("4. transport checks: tail byte-identical; zero-mention; census == live")
