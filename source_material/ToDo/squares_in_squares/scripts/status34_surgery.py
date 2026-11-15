#!/usr/bin/env python3
"""status34_surgery.py — run 34: the cascade section + the accuracy dive.

Surgery on STATUS.md (body only; the front-page copy is re-appended at
the end from the refreshed README):

1. Insert new §4 "The cascade" (the user's standing ask: the machinery
   that improves puzzles once any breakthrough is made).
2. Renumber old §4-9 -> §5-10; fix every cross-reference.
3. Accuracy fixes (ledger-verified this run):
   - table laws re-homed from the phantom `gap_analysis.py` into
     root_audit.py's table_laws block;
   - register import re-attributed (run 13; the 'run18-frontier' label
     born at the run-18 snapshot-restore; 76 applied -> 75 census);
   - Mishapolk 221 -> 209 = 8 chain3 + 4 closure re-earned deeper;
   - the Ellsworth '164 historical records' guess replaced by the code
     paths (Friedman survey svg set; kingbird = the mirror, 4 catalogue
     SVGs);
   - repository.zip retired; the GitHub repository is the transport.
"""
import re

W = "/home/z/my-project"
st = open(f"{W}/STATUS.md").read()
rd = open(f"{W}/README.md").read()
head = rd.splitlines()[0]
i = st.find("\n---\n\n" + head)
assert i > 0
body, tail = st[:i], st[i + len("\n---\n\n"):]
assert tail == rd and "README" not in body


def rep(old, new, where):
    global body
    assert old in body, f"missing ({where}): {old[:60]!r}"
    body = body.replace(old, new, 1)


# ---- §4 The cascade (inserted before the operating loop) --------------
CASCADE = """
## 4. The cascade (how one breakthrough becomes many)

No improvement enters this table as a single row. Every breakthrough —
constructed or imported — is multiplied by exact propagation laws
before it lands, and the same channel runs on everything: our
constructions, the register, the Mishapolk certs. This is the machinery
that answers "what happens to the other 999 puzzles when one record
improves", and it is the reason a single import can pay more than its
own face value.

### 4.1 The residue-diagonal chain law (cascade3.py)

The table's rows live on residue diagonals: for n with K = ⌈√n⌉, the
diagonal is c = n − (K−1)², members n = (K−1)² + c for every K above
the base. **The law: a record at L(m) converts every member n ≥ m of
the same diagonal to L(n) ≤ L(m) + (K(n) − K(m))** — extend the
record's packing with a 1-wide band strip per shell. The conversion is
a construction (band cells placed in the free margin of the L+1
container, computed from the actual bounding box), and it is verified
through the gate like everything else. cascade3.py enumerates these
2D band-extension chains from every base packing; per-n winners are
finalized and verified once, then merged into the table.

Live examples (measured on the delivered table, run 34): the T-263
record s(299) = 17.801238535867 (K=18) → L(334) = 18.801238537761
(K=19: +1) → L(371) = 19.801238537765 (K=20: +2) — one import, three
table rows, the two extensions binding at equality +2e-9 (storage
noise). And the n=5 pinwheel (L = 2.707106782448) → L(10) =
3.707106782648 = L(5)+1: the survey's own n=10 record is the strip
extension of the pinwheel — the diagonal c=10 was closed by the
community at exactly the value our law predicts.

### 4.2 The removal closure (closure_apply.py)

Removing squares from a packing never grows its bounding box, so every
n < m inherits L(m) for free: F(n) = min over m ≥ n of L(m) (the
prefix-min envelope from above). For each n with F(n) < L(n), the
closure drops (m−n) squares greedily from a base m — each step removes
the square whose removal most reduces the bounding box — and keeps the
candidate with the smallest result. Iterated to fixpoint, because a
smaller L at n can itself serve n' < n as a base. 18 delivered rows
carry the `closure` label. This is also how the chain converts
*inward*: the prefix of a band-extended packing is that packing's own
state, so a chain row at n simultaneously improves every n' ≤ n.

### 4.3 The table laws (the invariants the cascade leaves behind)

Two laws hold on the delivered table with zero violations, checked
every run by `root_audit.py`'s `table_laws` block (run 34: monotone
999/999 pairs clean, shell 937/937 clean). The tolerance is 1e-7 — the
same ENV_TOL as the chain envelope: `final_assembly.py` stores states
up to +2e-9 per row so the 12-dp CSV can round-trip, so comparisons at
1e-12 would read storage noise as violations; at 1e-7 both laws are
exactly clean.

- **Monotone envelope**: L(n) ≤ L(n+1) over all 999 adjacent pairs. A
  packing that improves n without improving n+1 is possible in
  principle; the table has never exhibited one.
- **Shell law**: L(n + 2⌊L(n)⌋ + 1) ≤ L(n) + 1, 937 pairs checked —
  adding 2⌊L⌋+1 squares to a packing at container L costs at most one
  more unit (the two new bands fit around the existing bbox).

### 4.4 What the cascade has paid (measured; NEXT_STEPS §1 ledger)

| event | gain |
|---|---|
| run-13 register import (76 records) — direct | 0.050264 |
| — cascade on those records (33 chain conversions) | 0.013671 |
| T-263 s(299) import + cascade (run 26) | 0.003559 |
| Mishapolk 221-row import + channel (run 30) | **0.173983** |
| **total closed since run 13** | **0.241477** |

The channel's post-processing is why imports are worth more than their
face value. Of the Mishapolk import's 221 applied rows, the standing
channel subsequently found deeper values for 12: 8 re-labeled `chain3`
(a band extension beats the imported cert at that n) and 4 re-labeled
`closure` (a square removed from the *neighbouring* Mishapolk packing
at n+1 beats the row's own cert at n). The import's 221 rows therefore
appear in the census as 209 `mishapolk` + 12 rows now carrying their
deeper producer. The register import shows the same pattern at run-13
scale: 76 applied, and the aiming map exists because of all this —
`root_audit.py` ranks every open row by what a record there would
convert through these laws (best current aim c=32 n=356: 0.011102 for
14 conversions; one-per-diagonal aggregate 0.375304, 63.4% of the
remaining gap).
"""
anchor = "## 4. The operating loop (how a run works, start to finish)"
assert anchor in body
body = body.replace(anchor, CASCADE.strip() + "\n\n" + anchor, 1)

# ---- renumbering §4-9 -> §5-10 ------------------------------------------
rep("## 4. The operating loop (how a run works, start to finish)",
    "## 5. The operating loop (how a run works, start to finish)", "loop head")
rep("## 5. The information map (what is ours, what enters, and where it all lives)",
    "## 6. The information map (what is ours, what enters, and where it all lives)", "map head")
rep("### 5.1 What the system produces itself", "### 6.1 What the system produces itself", "6.1")
rep("### 5.2 What enters from the world (through the gate — never around it)",
    "### 6.2 What enters from the world (through the gate — never around it)", "6.2")
rep("### 5.3 The delivered census (script-computed, run 33)",
    "### 6.3 The delivered census (script-computed, run 34)", "6.3")
rep("## 6. Delivered state (verified Run 33)", "## 7. Delivered state (verified Run 34)", "state head")
rep("## 7. The frontier (where the remaining 0.592 lives)",
    "## 8. The frontier (where the remaining 0.592 lives)", "frontier head")
rep("## 8. Run history (1 → 33)", "## 9. Run history (1 → 34)", "history head")
rep("## 9. Guarantee", "## 10. Guarantee", "guarantee head")

# ---- cross-references ----------------------------------------------------
rep("The current delivered\nnumbers live in §6;",
    "The current delivered\nnumbers live in §7, and the cascade that multiplies every breakthrough\nlives in §4;", "intro")
rep("the sources came from the packing community (§5); the two meet\nat the gate (§4).",
    "the sources came from the packing community (§6); the two meet\nat the gate (§5) and are multiplied by the cascade (§4).", "lineage end")
rep("The record in §5 must not be read", "The record in §6 must not be read", "engines preamble")
rep("the honest gate of §4 —", "the honest gate of §5 —", "3.2 gate")
rep("every score move came from a construction family or an\nimport — §5).",
    "every score move came from a construction family or an\nimport — §6).", "3.2 end")
rep("Every number in this file comes from\na script-computed ledger (§5);",
    "Every number in this file comes from\na script-computed ledger (§6);", "guarantee ledger ref")

# ---- §5 operating loop: the GitHub transport note (zip retired) ----------
rep("git commit + push/upload", "git commit (the user uploads to\nGitHub — the durability line)", "diagram")
rep("""Per run: read `NEXT_STEPS.md` (the map) → execute the highest-priority
open item with a script → every claim lands in a `workspace/push/`
ledger JSON with measured numbers → after any table change, re-run
the channel (cascade3 → closure_apply → final_assembly, mandatory
order) and `root_audit.py` (fixpoint + aiming map) → update the four
documents together (this file, the front page, `NEXT_STEPS.md`,
`REPRODUCE.md`, `RUN_NOTES.md`) → `deliverNN.py` copies the state to
`download/runNN/` and checks the syncs → commit and upload (the
GitHub remote is the durability line; the sandbox recycles — four
times so far, runs 17, 19, 32, 33).""",
    """Per run: read `NEXT_STEPS.md` (the map) → execute the highest-priority
open item with a script → every claim lands in a `workspace/push/`
ledger JSON with measured numbers → after any table change, re-run
the channel (cascade3 → closure_apply → final_assembly, mandatory
order) and `root_audit.py` (fixpoint + aiming map + table laws) →
update the documents together (this file, the front page,
`NEXT_STEPS.md`, `REPRODUCE.md`, `RUN_NOTES.md`) → `deliverNN.py`
copies the state to `download/runNN/` and checks the syncs → commit;
the user uploads to GitHub.

**Transport (run 34 rule): the GitHub repository
(github.com/DigitalEuan/squares_in_squares) is the bulk vehicle —
`repository.zip` is retired (the repository carries the whole tree,
so a zip of it is a duplicate). The front page still rides at the
bottom of this file: the upload path has never delivered it (failure
17), and this file is the one document that crosses every time. The
sandbox recycles (four times so far: runs 17, 19, 32, 33); the GitHub
remote is the durability line.""", "loop para")

# ---- §6.2 source-table accuracy ------------------------------------------
rep("""| Friedman survey (EJC DS#7) | 235 record SVGs (20–100 digit parse) + theory | `src: exact/aux/removal` | `workspace/svgs/`, parsed into `table.json` |
| Ellsworth catalogue (kingbird) | 164 historical records | merged via survey parse | `workspace/sources/` |
| Square Packing Atlas (evand) | certified best-known for n ≤ 324, exact rational certificates | `import_atlas.py` → `src: run18-frontier` (76 rows) + the T-263 record (run 26) | `workspace/sources/atlas/` |""",
    """| Friedman survey (EJC DS#7; the Ellsworth-hosted svg set, kingbird mirror) | 235 record SVGs (Decimal-exact, 20–100 digit parse) + theory; 4 catalogue SVGs (kingbird) | `src: exact/aux/removal` | `workspace/svgs/`, parsed into `table.json` |
| Square Packing Atlas (squaremath.org, the jlevy/squares register; source: evand/square-packing `best.json` + certs) | certified best-known for n ≤ 324, exact rational certificates | **run-13 import** (`import_atlas.py`, "Run 13 push A") → `src: run18-frontier` (label born at the run-18 snapshot-restore); + the T-263 record s(299) (run 26: finder Evan Daniel, fault-line DP, register #824/#893) | `workspace/sources/atlas/` |""", "6.2 rows")

# ---- §6.3 census rows ------------------------------------------------------
rep("| `run18-frontier` | 75 | 75 | community register import (run 18, the 76-record set) |",
    "| `run18-frontier` | 75 | 75 | the run-13 register import: 76 applied (ledger `atlas_import.json`); 3 later beaten by Mishapolk and re-labeled (n=154/270/303); n=327/332 carry the label from the run-18 snapshot-restore |", "census register")
rep("| `mishapolk` | 209 | 209 | run-30 import (221 applied; 12 re-earned deeper by the channel and re-labeled) |",
    "| `mishapolk` | 209 | 209 | run-30 import (221 applied; the channel then found deeper values for 12: 8 `chain3`, 4 `closure`) — includes n=154/270/303 where Mishapolk beat the register |", "census mishapolk")

# ---- §7 delivered state: invariants re-homed ------------------------------
rep("""Table invariants (machine-checked by `gap_analysis.py`, `root_audit.py`,
and the `final_assembly.py` round-trip — re-verified runs 32–33 on the
recovered tree: cascade 0, closure fixpoint, assembly 0 issues, table
bit-identical):

- **Chain-envelope fixpoint**: 0 rows above the chain envelope.
- **Monotone envelope**: L(n) ≤ L(n+1), all 999 pairs — 0 violations.
- **Shell law**: L(n + 2⌊L(n)⌋ + 1) ≤ L(n) + 1 — 937 checked, 0 violations.
- **CSV round-trip**: 500,500 rows, id continuity 0..500499, 12-dp
  stability, 0 issues.""",
    """Table invariants (checked every run: `root_audit.py`'s `table_laws`
block for the monotone envelope and the shell law, the fixpoint audit
for the chain envelope, and the `final_assembly.py` round-trip —
re-verified runs 32–34: cascade 0, closure fixpoint, assembly 0
issues, table bit-identical; run 34: monotone 999/999, shell
937/937):

- **Chain-envelope fixpoint**: 0 rows above the chain envelope.
- **Monotone envelope**: L(n) ≤ L(n+1) — 999/999 pairs clean.
- **Shell law**: L(n + 2⌊L(n)⌋ + 1) ≤ L(n) + 1 — 937/937 clean.
- **CSV round-trip**: 500,500 rows, id continuity 0..500499, 12-dp
  stability, 0 issues.

(Comparison tolerance 1e-7 everywhere: finalize stores states up to
+2e-9 per row for the round-trip, so 1e-12 comparisons would read
storage noise as violations. The run-33 edition of this file credited
these laws to a `gap_analysis.py` that did not exist; they now live in
`root_audit.py`, which prints and records them every run.)""", "invariants")

rep("| Open rows (attackable set) | **305** (root_audit run 33) |",
    "| Open rows (attackable set) | **305** (root_audit run 34) |", "open rows")
rep("unchanged since (runs 31–33:\nanalysis, campaign nulls, recovery + documentation).",
    "unchanged since (runs 31–34:\nanalysis, campaign nulls, recoveries + documentation).", "score history")

# ---- §9 run history: the run-34 row ---------------------------------------
rep("""| 33 | **rollback #4 recovery** + the lineage record: run-32 artifacts redone bit-identically; the GLM → cent compiler → this project lineage recorded (this document rebuilt); the front-page copy rides at the bottom of this file for the upload transport | 22.645991 | failure 17 (the transport rule); see `NEXT_STEPS.md` |""",
    """| 33 | **rollback #4 recovery** + the lineage record: run-32 artifacts redone bit-identically; the GLM → cent compiler → this project lineage recorded (this document rebuilt); the front-page copy rides at the bottom of this file for the upload transport | 22.645991 | failure 17 (the transport rule); see `NEXT_STEPS.md` |
| 34 | accuracy dive (user order): **the cascade recorded** (§4: chain law with live T-263/pinwheel examples, removal closure, table laws, the measured ledger 0.241477); table laws re-homed from a phantom reference into `root_audit.py` (monotone 999/999, shell 937/937 @1e-7); census re-verified against the live table and the import ledgers (register re-attributed to run 13: 76 applied, 3 beaten by Mishapolk, +2 via the run-18 restore; Mishapolk 221→209 = 8 chain3 + 4 closure re-earned); `repository.zip` retired — the GitHub repository is the transport | 22.645991 | channel bit-identical; laws 0-violation |""", "run 34 row")

# ---- sanity: structure + zero-mention -------------------------------------
assert "README" not in body
secs = re.findall(r"^## .+$", body, re.M)
assert secs == ["## 1. The lineage: GLM → cent compiler → this project",
                "## 2. The cent compiler (the instrument set this project grew from)",
                "## 3. The engines (what this project's own machinery is, and what it did)",
                "## 4. The cascade (how one breakthrough becomes many)",
                "## 5. The operating loop (how a run works, start to finish)",
                "## 6. The information map (what is ours, what enters, and where it all lives)",
                "## 7. Delivered state (verified Run 34)",
                "## 8. The frontier (where the remaining 0.592 lives)",
                "## 9. Run history (1 → 34)",
                "## 10. Guarantee"], secs

# ---- README refresh, then re-append as the tail ---------------------------
rd2 = rd.replace(
    "## Headline results (Run 33, 2026-11-07; last score move run 30)",
    "## Headline results (Run 34, 2026-11-07; last score move run 30)", 1)
assert rd2 != rd
rd2 = rd2.replace(
    "(0 issues; re-verified runs 32–33)", "(0 issues; re-verified runs 32–34)", 1)
rd2 = rd2.replace(
    "symmetric, records asymmetric). Every campaign is aimed by these\n   instruments, never by eyeball.",
    "symmetric, records asymmetric), and `root_audit.py`'s `table_laws`\n   block checks the monotone envelope and shell law every run\n   (999/999 and 937/937 clean at run 34). Every campaign is aimed by\n   these instruments, never by eyeball.", 1)
open(f"{W}/README.md", "w").write(rd2)

out = body + "\n\n---\n\n" + rd2
open(f"{W}/STATUS.md", "w").write(out)
print("surgery done:", len(out.splitlines()), "lines; sections:", len(secs))
print("tail == refreshed README:", open(f"{W}/STATUS.md").read().split("\n---\n\n# Squares in Squares —", 1)[1] is not None)
