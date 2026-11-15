#!/usr/bin/env python3
r"""docs36.py — run 36: bring every document to the run-36 state.

Base = the attached run-35 documents (installed verbatim earlier this
run). This script adds ONLY run-36 facts (and ports the run-33/34
NEXT_STEPS material lost with the elsewhere session — failure 17 +
17c and the §0 rows 33/34, §6 entry 9, from the conversation record
and the survived run33/34_outcomes ledgers).

STATUS: title + §6.3 label + §7 score-history + a §9 run-36 row;
the front-page tail is refreshed (Run 35 -> Run 36) and re-appended
byte-for-byte.  REPRODUCE: A24 (runs 32-34, reconstructed), A25
(run 35), A26 (run 36).  RUN_NOTES: port the run-35 narrative +
the run-36 section.  notes/run36_NOTES.md.
"""
import os

W = "/home/z/my-project"


def rep(path, old, new, where):
    src = open(path).read()
    if new in src:
        print(f"  skip (already applied): {where}")
        return
    assert old in src, f"{path}: missing ({where}): {old[:70]!r}"
    open(path, "w").write(src.replace(old, new, 1))
    print(f"  applied: {where}")


# ---------------------------------------------------------------- STATUS
S = f"{W}/STATUS.md"
rep(S, "# STATUS.md — Squares in Squares: the system and sources record (Run 35, 2026-11-07)",
       "# STATUS.md — Squares in Squares: the system and sources record (Run 36, 2026-11-07)", "title")
rep(S, "### 6.3 The delivered census (script-computed, run 34)",
       "### 6.3 The delivered census (script-computed, run 35)", "census label")
rep(S, "## 7. Delivered state (verified Run 35)",
       "## 7. Delivered state (verified Run 36)", "state head")
rep(S, "| Open rows (attackable set) | **305** (root_audit run 35) |",
       "| Open rows (attackable set) | **305** (root_audit run 35, re-verified run 36) |", "open rows")
rep(S, "## 9. Run history (1 → 34)",
       "## 9. Run history (1 → 36)", "history head")
rep(S, """Score history: 22.823536 (run 13) → 22.819978 (runs 26–27, T-263) →
22.645991 (run 30, Mishapolk) → **22.642387** (run 35: nine register
records T-243/T-257/T-267–T-273 + the n=338 chain conversion).""",
    """Score history: 22.823536 (run 13) → 22.819978 (runs 26–27, T-263) →
22.645991 (run 30, Mishapolk) → **22.642387** (run 35: nine register
records T-243/T-257/T-267–T-273 + the n=338 chain conversion; the
run-36 re-establishment reproduced it exactly, ledger
`import_candidates35.json` re-executed).""", "score history")
rep(S, """| 35 | **score move** (user order: deep exploration + advances + academic paper + Lean): P3 source watch found the register moving — 9 Evan Daniel records **T-243/T-257/T-267–T-273** (n=172/175/182/204/260/268/293/303/304) mirrored from evand/square-packing candidates and gate-imported (0.003359) + the n=338 chain conversion (0.000245); family-completeness probe (wedge/lattice fill): 0/217 frontier cores admit extra squares — the Göbel family is lattice-maximal at the frontier; `GLM_INVESTIGATION.md` rewritten as the academic-paper study record; **TCT/Laws.lean** (Lean 4): closure-fixpoint ⟹ monotone envelope, NRCI=1 ⟺ vacuum, family/chain arithmetic; scripts' `/home/z/my-project` hardcoding fixed for the active channel (paths now resolve from the repo) | **22.642387** | 9+1 rows applied; docs + formal layer updated together |""",
    """| 35 | **score move** (user order: deep exploration + advances + academic paper + Lean): P3 source watch found the register moving — 9 Evan Daniel records **T-243/T-257/T-267–T-273** (n=172/175/182/204/260/268/293/303/304) mirrored from evand/square-packing candidates and gate-imported (0.003359) + the n=338 chain conversion (0.000245); family-completeness probe (wedge/lattice fill): 0/217 frontier cores admit extra squares — the Göbel family is lattice-maximal at the frontier; `GLM_INVESTIGATION.md` rewritten as the academic-paper study record; **TCT/Laws.lean** (Lean 4): closure-fixpoint ⟹ monotone envelope, NRCI=1 ⟺ vacuum, family/chain arithmetic; scripts' `/home/z/my-project` hardcoding fixed for the active channel (paths now resolve from the repo) | **22.642387** | 9+1 rows applied; docs + formal layer updated together |
| 36 | **re-establishment** (user: the elsewhere run-35 session died after its docs; re-establish here + updated csv): sandbox had rolled back to run 27 AND the GitHub remote was missing from git config (restored; it carried the run-34 state, so runs 28–34 came back from it — the run-35 tree was lost with its session); adopted the remote, re-executed run 35 exactly from its five surviving documents: the 9-record import reproduced to the digit (direct 0.003359; every side, T-id and old src matches `run35_NOTES.md`), the n=338 cascade reproduced (+0.000245), score 22.642386651; the wedge probe re-verified 0/217; TCT/Laws.lean reconstructed statement-for-statement from the paper's §9 table (no elan here — honest note in SORRY_LEDGER.md; the run-35 record reports lake build passing); run-33/34 NEXT_STEPS material ported (failure 17 + 17c had been lost with the session); the 12-channel portability patch re-applied | 22.642387 | channel bit-identical pre-import; independent rescore agrees |""", "run 36 row")

# transport tail: Run 35 -> Run 36
st = open(S).read()
rd = st[st.find("\n---\n\n# Squares in Squares — Verified") + len("\n---\n\n"):]
rd2 = rd.replace(
    "## Current results (Run 35, 2026-11-07; score move run 35)",
    "## Current results (Run 36, 2026-11-07; score move run 35)", 1).replace(
    "| Certification | 1000/1000 packings SAT-verified + 500,500-row CSV round-trip (0 issues; re-verified runs 32–35) |",
    "| Certification | 1000/1000 packings SAT-verified + 500,500-row CSV round-trip (0 issues; re-verified runs 32–36) |", 1).replace(
    "| Latest score move | **run 35: register records T-243/T-257/T-267–T-273 (9 rows, Evan Daniel) + cascade**: 22.645991 → 22.642387 (−0.003604) |",
    "| Latest score move | **run 35: register records T-243/T-257/T-267–T-273 (9 rows, Evan Daniel) + cascade**: 22.645991 → 22.642387 (−0.003604; the run-36 re-establishment reproduced it exactly) |", 1)
if rd2 == rd:
    print("  skip (already applied): README tail refresh")
else:
    head = st[:st.find("\n---\n\n# Squares in Squares — Verified")]
    open(f"{W}/README.md", "w").write(rd2)
    open(S, "w").write(head + "\n\n---\n\n" + rd2)
    print("  applied: README tail refresh")

# ------------------------------------------------------------ NEXT_STEPS
N = f"{W}/NEXT_STEPS.md"
rep(N, "## 0. Execution status of this plan (updated Run 32, 2026-11-06)\n\nRuns 14–32 executed this plan. Measured outcomes, per item:",
       "## 0. Execution status of this plan (updated Run 36, 2026-11-07)\n\nRuns 14–36 executed this plan. Measured outcomes, per item:", "§0 head")
rep(N, "## 3. Failure → requirement (updated with runs 14–32)\n\nItems 1–13 stand (see run-26/27/28 revisions). Two additions:",
       "## 3. Failure → requirement (updated with runs 14–36)\n\nItems 1–13 stand (see run-26/27/28 revisions). Additions:", "§3 head")
rep(N, """## 4. Prioritized pushes (updated Run 32)""",
    """## 4. Prioritized pushes (updated Run 36)""", "§4 head")
rep(N, "## 6. What was executed (runs 14–32), measured",
       "## 6. What was executed (runs 14–36), measured", "§6 head")

# port the lost runs-33/34 material + the run-35/36 rows (§0 table)
rep(N, "| **Run 32** (recovery + docs) |",
       """ | **Run 33** (recovery + lineage) | **DONE (user order, 3 parts)** | rollback #4 recovery + the lineage record: run-32 artifacts redone bit-identically (root_audit32: 0/305/gap 0.591569); STATUS.md rebuilt as the system + sources record (the GLM → cent compiler → this project lineage; engines deep dive; information map + census); transport rule born: the front page rides at the bottom of STATUS.md, body zero-mention, tail byte-identical (deliver33 §6 checks). Failure 17. |
 | **Run 34** (accuracy dive) | **DONE (user order, 3 parts)** | the cascade recorded as STATUS §4 (chain law with live T-263/pinwheel examples, removal closure, table laws, the 0.241477 ledger); table laws re-homed from a phantom `gap_analysis.py` into root_audit.py's table_laws block (monotone 999/999 + shell 937/937 @1e-7); census re-verified against the live table and the import ledgers (register re-attributed to run 13: 76 applied → 75, 3 beaten by Mishapolk; Mishapolk 221→209 = 8 chain3 + 4 closure re-earned); `repository.zip` retired — the GitHub repository is the transport (failure 17c amendment). Score unchanged 22.645990613. |
 | **Run 35** (score move) | **DONE (user order; session died, re-established at run 36)** | P3 paid again: 9 Evan Daniel register records T-243/T-257/T-267–T-273 (n=172/175/182/204/260/268/293/303/304) mirrored from evand/square-packing candidates and gate-imported (direct 0.003359) + the n=338 chain conversion (0.000245): 22.645991 → **22.642387**. Wedge probe: 0/217 frontier cores admit extra squares (lattice-maximal at the frontier). GLM_INVESTIGATION.md rewritten as the academic paper; TCT/Laws.lean (closure_fixpoint_monotone, nrci_eq_one_iff_zero, family/chain arithmetic); the 12-channel portability patch. Score 22.642386651, 543 beats. |
 | **Run 36** (re-establishment) | **DONE (user order: re-establish the run-35 state here + updated csv)** | the sandbox had rolled back to run 27 and git had lost the remote config; the GitHub remote carried the run-34 state (runs 28–34 restored from it), the run-35 tree was lost with its elsewhere session — only its five documents survived (attached; installed as canonical). Run 35 re-executed exactly from the record: the import reproduced to the digit (9 rows, 0.003359 direct; T-ids, sides and old srcs all match `run35_NOTES.md`), cascade n=338 reproduced (+0.000245), wedge probe re-verified 0/217, Laws.lean reconstructed statement-for-statement from the paper §9 table (no elan here; honest note in SORRY_LEDGER.md), the run-33/34 NEXT_STEPS material ported (failure 17 + 17c, §0 rows, §6 entry 9 — lost with the session), the portability patch re-applied (12 scripts). Channel bit-identical pre-import; independent rescore 22.642387. |""",
    "§0 rows 33-36")

# failure 17 + 17c (lost with the session; ported from the record)
rep(N, """16. **A sandbox rollback is a failure mode, not a data event**""",
    """17. **The upload path has never delivered the README** (runs 32–33,
    user-reported; verified against the GitHub remote): the remote
    README froze at the run-13 era through six score moves. Requirement
    (the transport rule): the front page rides at the bottom of
    STATUS.md — a straight unedited copy, body zero-mention, tail
    byte-identical, checked mechanically by deliverNN every run;
    (17c) run 34 amendment: `repository.zip` is RETIRED — the GitHub
    repository itself is the bulk vehicle (it carries the whole tree;
    a zip of it is a duplicate). Never assume a file crossed the
    boundary: check what the remote actually holds, and put every
    document the user needs into one of the files that do cross.
18. **A session can die with its whole tree** (run 35 → run 36): the
    elsewhere run-35 session stopped abruptly after updating the
    documents — the docs crossed (they were attached here), but the
    tree (candidates import scripts, Laws.lean, the run-35 table,
    ledgers, deliver33/34.py) did not, and this sandbox had meanwhile
    rolled back to run 27 with the git remote config missing.
    Requirement: (a) commit + push every run — the GitHub remote is
    the durability line (it carried runs 28–34 here); (b) the run
    ledger (notes/runNN_NOTES.md + the doc updates) must carry every
    number needed to re-execute the run from its record alone —
    run 36 proved this works: the import reproduced to the digit from
    `run35_NOTES.md`; (c) at turn start, if the tree is at an older
    era than the documents claim, trust the documents + the remote,
    verify the claimed numbers by re-execution, and record what was
    lost (this file's §0 run-36 row lists it).""",
    "failures 17-18")

# §6 entry 9 (run 35, from the attached NEXT_STEPS) already present?
ns = open(N).read()
if "**Run 35 (user order: deep exploration + advances + academic paper\n   + Lean4)**" in ns:
    print("§6 entry 9 (run 35) already in NEXT_STEPS — kept")
# entry 10 = run 36
rep(N, """Score 22.823536149 → 22.819977568 (runs 26–27) → 22.645990613
(run 30) → **22.642386651** (run 35); beats-grid 543; runs 31–34
analysis/campaign nulls/recovery; submission.csv rebuilt and
round-trip verified every run.""",
    """10. **Run 36 (user order: re-establish the run-35 state + updated
    csv)**: the sandbox rollback (to run 27) + the lost remote config
    were found at turn start; the GitHub remote carried the run-34
    state — adopted (lineage preserved on sandbox-lineage-27; upload/
    protected through the reset; channel re-verified bit-identical
    22.645990613/543 before any edit). The five attached run-35
    documents installed as canonical; run 35 re-executed exactly:
    9 records imported (direct 0.003359 — every side/T-id/old-src
    matches the record), cascade converted n=338 (+0.000245), closure
    fixpoint, assembly 0 issues, independent rescore; score
    **22.642386651**, 543 beats; census re-verified (mishapolk 207,
    chain3 88, exact 77, run18-frontier 68, register 10);
    root_audit35 = root_audit34's structure with gap 0.587965. The
    wedge probe re-verified 0/217; Laws.lean reconstructed (paper §9
    table, statement for statement); failure 17/17c ported; this
    entry.

Score 22.823536149 → 22.819977568 (runs 26–27) → 22.645990613
(run 30) → **22.642386651** (run 35, reproduced at run 36); beats-grid
543; runs 31–34 analysis/campaign nulls/recovery; submission.csv
rebuilt and round-trip verified every run.""", "§6 entry 10")

# header + §1 + §5 numbers to run-36 state
rep(N, """Companion to `STATUS.md` (which now duplicates the README and carries
the system map — see its §2). Everything below is measured on the
delivered table (**Run 35, score 22.642387**, 543/1000 beat grid; the
run-35 register import — T-243/T-257/T-267–T-273 — landed after the
Mishapolk import of run 30; the channel is at fixpoint and the table
laws are clean) with `scripts/root_audit.py` (run 27; refreshed every
run), `scripts/sat_review.py` (run 28), `scripts/sat_measure.py`
(run 29) and `scripts/symmetry_audit.py` (run 31); nothing here is
aspirational without a number attached.""",
    """Companion to `STATUS.md` (the system + sources record; it carries a
straight unedited copy of the front page at its bottom for the upload
transport — failure 17). Everything below is measured on the delivered
table (**Run 36, score 22.642387** — the run-35 register import
T-243/T-257/T-267–T-273, re-established this run from the record;
543/1000 beat grid; the channel is at fixpoint and the table laws are
clean) with `scripts/root_audit.py` (refreshed every run),
`scripts/sat_review.py` (run 28), `scripts/sat_measure.py` (run 29)
and `scripts/symmetry_audit.py` (run 31); nothing here is
aspirational without a number attached.""", "header")
rep(N, "## 5. Value ladder (re-measured Run 32; values unchanged from run 30)",
       "## 5. Value ladder (re-measured Run 35; values unchanged from run 30)", "§5 head")

# ------------------------------------------------------------- REPRODUCE
R = f"{W}/REPRODUCE.md"
src = open(R).read().rstrip()
src += """

## A24. Runs 32–34: recoveries, the cascade record, the accuracy dive

```bash
# (runs 32-34 scripts survive in scripts/ from the GitHub remote)
python3 scripts/root_audit.py workspace/push/root_audit34.json 34
#    -> table laws monotone 999/999 + shell 937/937 @1e-7; fixpoint 0/305
python3 scripts/status34_surgery.py    # the run-34 STATUS surgery (on record)
```

## A25. Run 35: the register import + the paper + the Lean layer
(re-established at run 36 from the attached record)

```bash
python3 scripts/fetch_candidates.py    # mirrors 73 evand candidate certs
python3 scripts/import_candidates.py   # dry: 9 rows, direct 0.003359
python3 scripts/import_candidates.py --apply
python3 scripts/cascade3.py            # converts n=338 (+0.000245)
python3 scripts/closure_apply.py       # fixpoint, 0 rounds
python3 scripts/final_assembly.py      # 22.642387 / 543 (0 issues)
python3 scripts/root_audit.py workspace/push/root_audit35.json 35
#    -> laws clean; fixpoint 0/305; gap 0.587965
python3 scripts/probe_wedges36.py      # the wedge probe: 217 cores, 0 extra
```

## A26. Run 36: the re-establishment (this run)

```bash
# turn-start recovery (already applied; on record):
#   git fetch origin; adopt the remote (runs 28-34); protect upload/
#   channel bit-identity check BEFORE any edit (expect 22.645990613/543)
python3 scripts/portable_paths36.py    # re-apply the portability patch
#   (channel re-run after it must stay bit-identical)
python3 scripts/probe_wedges36.py      # re-verify 0/217
# Lean: TCT/Laws.lean reconstructed from the paper §9 table; no elan
#   toolchain here — see SORRY_LEDGER.md (build status note)
python3 scripts/docs36.py              # (already applied; on record)
python3 scripts/deliver36.py
```
"""
open(R, "w").write(src + "\n")

# ------------------------------------------------------------ RUN_NOTES
RN = f"{W}/notes/RUN_NOTES.md"
rn = open(RN).read().rstrip()
rn += """

---

# Run 35 (2026-11-07): deep exploration + advances + the paper + Lean

*Ported to notes/run35_NOTES.md at run 36 (this narrative); the run's
tree was lost with its elsewhere session and re-established at run 36
from this record — see the Run 36 section below.*

**User order.** Explore the project deeply; push any further advances;
turn `GLM_INVESTIGATION.md` into an academic-paper record; create Lean 4
lemmas/axioms that can be verified and fed back into the system.

**Score: 22.645990613 → 22.642386651 (−0.003604). Beats-grid 543/1000
unchanged (all 9 wins deepen below-grid rows). Gap to the reported
leader: 0.591569 → 0.587965.**

## (a) P3 source watch — the score move (9 register records)

The Mishapolk catalogue and the atlas `best.json` were both unchanged
upstream — but `evand/square-packing` had moved: a Nov-5 commit carries
candidate certificates "for jlevy registration", and the jlevy/squares
register had closed them as nine new upper bounds (issues
#806/#845/#914): T-257 n=172, T-267 n=175, T-243 n=182, T-268 n=204,
T-269 n=260, T-270 n=268, T-271 n=293, T-272 n=303, T-273 n=304 — all
by Evan Daniel. Procedure: `fetch_candidates.py` (73 certs mirrored;
the 21 noise-level "wins" skipped by MIN_GAIN = 1e-7), then
`import_candidates.py` (exact-rational parse, packlib gate, best-L
wins, T-id attribution; dry-run then apply; ledger
`import_candidates35.json`), then the channel: cascade3 converted
n=338 (chain from the 303 record: L(303)+1 = 18.9018327 <
18.9063328): +0.000245. Direct 0.003359 + cascade 0.000245 =
**0.003604**. Two independent rescore paths agree.

## (b) Constructive-advance attempt — the wedge probe (measured negative)

The G(a1,a2,b,c) contact triangles are exactly filled by the corner
staircases T(a) at contact, but the container-minus-diamond free
region is the union of the u-clear triangle and two v-clear wedge
strips — apparently room for edge-row extensions the sweep never
tries. Test (vectorized greedy maximal lattice fill, exact SAT
admission, all four corner anchorings): live-band cores = every
(a1,a2,b,c) whose family side beats or misses the table by < 0.01:
**217 cores; 0 of 217 admit any extra lattice square.** The family is
lattice-maximal at the frontier (analytic reading in
GLM_INVESTIGATION §4.2); the mid-band prize still needs a new
*architecture*, not a family completion.

## (c) The paper + the Lean layer (the user's deliverables)

1. **`GLM_INVESTIGATION.md` rewritten as the academic paper** —
   "Squares in Squares: Exact Construction, Verified Propagation, and
   the Measured Limits of Search": abstract; problem & state of the
   art; GLM lineage; method (gate + loop + ledgers); the Göbel family
   with the contact identity and the four competing hypotheses; the
   propagation algebra with the Lean upgrade; the measurement layer;
   the negative-search ledger; the source frontier; the Lean layer
   with the feedback map; results and the gap decomposition; open
   problems; guarantee; references (12).
2. **`workspace/lean/tct_squares/TCT/Laws.lean`** — the law layer:
   proved `closure_fixpoint_monotone` (the monotone-envelope table law
   is a corollary of the removal-closure fixpoint — the flagship
   feedback theorem), `nrci_eq_one_iff_zero` (the run-29 vacuum
   finding as a theorem), the family/chain arithmetic
   (`staircase_cells`, `gobel_count`, `ceil_sqrt_mono`,
   `chain_value_mono`), `sq_floor_of_area_bound`; axioms `Packable`
   and `area_bound` (cited style). SORRY_LEDGER refreshed (one
   deliberate sorry remains: `s11_optimal_value`).
3. **Feedback into the system**: if root_audit's monotone law ever
   fails on a candidate table, the closure/finalize is broken, not
   the mathematics; if NRCI ≠ 1 on a g = 0 contact word, the measure
   constants are wrong.

## (d) Housekeeping

The active-channel scripts' hard-coded `/home/z/my-project` root fixed
(12 scripts: paths now resolve from the script location). Lattice
layer re-verified: 28/28 + 14/14 integer-exact. Census: grid 457 ·
mishapolk 207 · chain3 88 · exact 77 · run18-frontier 68 · gobel 54
(2/3/S) · removal 18 · closure 18 · register 10 · aux 3.

---

# Run 36 (2026-11-07): the re-establishment of run 35

**User order.** "I ran a session elsewhere but it stopped abruptly
leaving only these documents attached, it was a successful run — can
we get it established here and run through to an updated csv please."

**Found at turn start:** the sandbox had rolled back to the run-27
era (runs 28–35 gone locally) and the git remote config was missing
(origin restored by URL — the GitHub remote carried the run-34 state:
table 22.645990613/543, the 116 scripts, the 68 ledgers, the Lean
base modules, notes through run 34). The elsewhere run-35 session's
tree was lost with it; its five documents survived and were attached
here.

**Re-established, exactly, from the record:**

1. **Adopted the remote** (lineage preserved on sandbox-lineage-27;
   upload/ protected and md5-verified through the reset); channel
   re-verified bit-identical (22.645990613/543, cascade 0, closure
   fixpoint, assembly 0 issues) before any edit — failure 16(d).
2. **Portability patch re-applied** to the 12 channel scripts
   (`portable_paths36.py`); the channel re-run after it stayed
   bit-identical.
3. **Run 35 re-executed** (`fetch_candidates.py` tarball mirror —
   73 certs; `import_candidates.py` dry-run then apply): 9 rows,
   direct **0.003359** — every side, T-id and old src matches the
   record to the digit; cascade converted exactly n=338 (+0.000245);
   closure fixpoint; assembly 0 issues; independent rescore.
   **Score 22.642386651, 543 beats, gap 0.587965.**
4. **root_audit35**: laws monotone 999/999 + shell 937/937 @1e-7;
   fixpoint 0/305; best aim c=32 n=356; aggregate 0.375304.
   Census re-verified == the run-35 record (mishapolk 207, chain3 88,
   exact 77, run18-frontier 68, register 10 at 172/175/182/204/260/
   268/293/299/303/304).
5. **The wedge probe re-verified**: 217 cores, 0 extra squares
   (`probe_wedges36.py`; probe ledger `probe_wedges36.json`).
6. **TCT/Laws.lean reconstructed** statement-for-statement from the
   paper's §9 table (3 defs + 11 theorems + the 2 cited axioms); this
   sandbox has no elan toolchain, so the build is not re-verified
   here — honest note in SORRY_LEDGER.md; the run-35 record reports
   `lake build` passing. SORRY_LEDGER refreshed to the run-35 state.
7. **Documents to run-36 state**: the five attached run-35 documents
   installed as canonical (STATUS/NEXT_STEPS/REPRODUCE/
   notes/run35_NOTES; GLM_INVESTIGATION was already identical on the
   remote); README extracted from the STATUS tail; then run-36
   updates (STATUS title/§6.3/§7/§9 row 36; NEXT_STEPS header, §0
   rows 33–36 with the ported failure 17 + 17c, §6 entry 10; REPRODUCE
   A24–A26; this section). Failure 18 recorded (a session can die
   with its whole tree — the docs crossed, the tree did not).

Score unchanged from run 35: **22.642386651** (the updated
submission.csv the user asked for is the run-35 csv, rebuilt and
round-trip-verified here). Copies: download/NEXT_STEPS.md,
download/RUN_NOTES.md, download/run36/ + MANIFEST.
"""
open(RN, "w").write(rn + "\n")

# notes/run36_NOTES.md
open(f"{W}/notes/run36_NOTES.md", "w").write(
    """# Run 36 notes (2026-11-07)

The re-establishment of run 35 (its elsewhere session died after the
docs; this sandbox had rolled back to run 27 with the git remote
config missing). Adopted the GitHub remote (run-34 state; runs 28–34
restored), re-executed run 35 exactly from its five surviving
documents: 9 register records imported (direct 0.003359, to the
digit), cascade n=338 (+0.000245), wedge probe re-verified 0/217,
Laws.lean reconstructed from the paper §9 table (no elan here —
SORRY_LEDGER.md build note), run-33/34 NEXT_STEPS material ported,
portability patch re-applied. Score 22.642386651, 543 beats, gap
0.587965; updated submission.csv rebuilt + round-trip verified.
Details: download/run36_outcomes.json, notes/RUN_NOTES.md (Run 36).
""")
print("docs36 done: STATUS/NEXT_STEPS/REPRODUCE/RUN_NOTES/notes at run-36 state")
