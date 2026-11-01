# The Leech shells from the lattice's definition — the shapes proved, every shell counted from the Golay census

## Tier 0 — the coarse read

**Question.** Can the GLM define the Leech lattice by Conway's construction from the Golay code, prove the shapes of its minimal vectors from that definition, and count every shell from the Golay census alone — checked against the theta series, which uses no Golay code — instead of reading the shells from a stored table?

**Verdict.** Yes. The minimal shapes are proved in Lean from Conway's definition, and every shell is counted from the Golay census walked from the generator, agreeing with the theta series on every shell through norm 14; the stored table's norm-12 shell was wrong and is corrected.

**Deciding figure.** 6 of 6 marks; the weight census `1, 759, 2576, 759, 1` walked from the generator; 8 of 8 shells agreeing with the theta series `E₄³ − 720Δ` through norm 14; the norm-12 shell 34,408,430,950 → 34,417,656,000.

**Recomputed by.** `glm_universal.reasoning.leech_shells.shell_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

*Created 31 October 2026. Reconstructed 31 October 2026 from the round records; the original was lost in the October 2026 reorganisation.* The original was written on 19 October 2026 (the date of the Phase 164 record); its marks (L1, S1–S3, T1, F1) were written before the measurement in the same session.

> **How this reconstruction was made.** From the Phase 164 record of
> [`MASTER_PLAN.md`](../MASTER_PLAN.md), the "Leech shells from the lattice's
> definition" row of [`SYSTEM.md`](../SYSTEM.md), §20.38 and the study table of
> [`GLM_ACADEMIC_PAPER.md`](GLM_ACADEMIC_PAPER.md), To-Do item 2 of
> [`STATUS.md`](../STATUS.md), the row of `tests/README.md` for
> `test_leech_shells.py`, the docstring of `reasoning/leech_shells.py`, and the
> lines of §7.3 that [`LEECH_SHELL_COUNT_STUDY.md`](LEECH_SHELL_COUNT_STUDY.md)
> and the Phase 165 record quote. The marks' wording was not recorded anywhere
> that survived; the records give their outcome (6 of 6) and what the round
> established. The Python half of the deciding figure was re-run for this
> reconstruction (§7.4); no other figure appears that the records do not give.

## 0. What this document is

A study for Phase 164, taken from `STATUS.md` §2.1 item 2 (*the machine's
reading, the rest*: the shapes rule declared, not derived; only the minimal
shell counted), under the owner's note for this iteration: the GLM is to
reason, not repeat, using the MOG, Golay and Leech structure where it works.

Phase 163 ([`TOOL_MACHINE_STUDY.md`](TOOL_MACHINE_STUDY.md)) counted the Golay
code from its generator and formed the kissing number by a shapes rule it
declared; the other shells were a stored table in the `llvq` tool
([`LLVQ_TABLE_STUDY.md`](LLVQ_TABLE_STUDY.md)).

## 1. What was built

* **`src/lean/RequestProject/GLM/LeechShells.lean`** (0 `sorry`): `IsLeech`
  (Conway's construction); `minimal_shape` — every minimal vector has one of
  the three shapes: eight coordinates `±2` on an octad with an even number of
  minus signs, two coordinates `±4`, or one `±3` and the rest `±1` on a
  codeword — with `minimal_even_support` and `minimal_odd_pattern`; the
  counting procedure `patternCount`/`shellCount` with `minimal_pattern_counts`,
  `shells_from_census` and `shellCount_eq` (`native_decide` evaluations).
* **`reasoning/leech_shells.py`**: the weight census walked from the generator
  (`weight_census`: `1, 759, 2576, 759, 1`); the generating-function count per
  codeword weight (`pattern_count`) — the number of vectors on one codeword
  depends on its weight alone, and is a coefficient of a product of
  one-coordinate generating functions over the squared value and the sum mod
  8; every shell (`shell_count`, `shells`); and `shell_report`, which sets the
  count beside the theta series.
* **`reasoning/llvq.py`**: the shell table became `leech_shells()`, derived and
  checked, raising on a disagreement; its stored fifth entry (34,408,430,950)
  was wrong.

## 2. The control

The modular theta series `E₄³ − 720Δ`
(`glm_universal.substrate.leech2.theta_series`), which uses no Golay code: an
independent derivation. A disagreement on any shell is a failure, not a
correction of either side.

## 3. What is not claimed

The converse of `minimal_shape` and the procedure's correctness for every
shell are argued, not proved: the step from "the procedure's number" to "the
number of lattice vectors" is the paragraph *the count on a codeword depends
only on its weight*. GLM-BAT still counts only the minimal shell.

## 4. Faculties

*Derivation:* a stored table is replaced by a count derived from the
definition. One answer moved (§7.2).

## 5. The marks

| mark | what the records attach to it |
|---|---|
| **L1** | not recorded one by one |
| **S1** | not recorded one by one |
| **S2** | not recorded one by one |
| **S3** | not recorded one by one |
| **T1** | not recorded one by one |
| **F1** | not recorded one by one |

The wording of the six marks is lost. What the round's tests checked
(`tests/test_leech_shells.py`, 5): the Lean file's theorems and no `sorry`; the
Golay weight census walked from the generator; the minimal shapes per codeword
checked against a direct membership test; the Golay count and the modular
theta series agreeing for `t = 0 .. 7`; the `llvq` catalogue the derived one,
fifth shell 34,417,656,000.

## 6. How it is measured

`PYTHONPATH=src python3 -c "from glm_universal.reasoning import leech_shells as L; print(L.shell_report(7))"`;
the Lean file by `lake build`; the tests by hand: 5 of 5 passed (pytest was
not installed).

## 7. What came out

### 7.1 The marks

| mark | outcome |
|---|---|
| **L1** | met |
| **S1** | met |
| **S2** | met |
| **S3** | met |
| **T1** | met |
| **F1** | met |

**6 of 6 marks.**

### 7.2 What this answers

Yes. The minimal shapes are proved in Lean from Conway's definition, and every shell is counted from the Golay census walked from the generator, agreeing with the theta series on every shell through norm 14; the stored table's norm-12 shell was wrong and is corrected.

The theta series agrees on every shell through norm 14 (8 of 8). The stored
table had the norm-12 shell as 34,408,430,950 where the lattice has
34,417,656,000, and the GLM answered a question about it confidently wrong.
**Answers moved — one:** *the number of vectors of norm 12 in the leech
lattice*, 34,408,430,950 → 34,417,656,000; every `llvq` answer's quoted text
now says *counted from the Golay census*, and the tool raises if the two
derivations ever disagree. The evaluation's two Lean-corpus pins (`report
relay`, `report anonymous`) were re-pinned for the corpus refreshed with
`LeechMachine.lean`, `ToolMachine.lean` (Phase 163) and `LeechShells.lean`.

### 7.3 What is left

* The converse of `minimal_shape` and the procedure's correctness, argued, not
  proved — *the procedure's correctness for the shells `t ≥ 3` is still
  argued, not proved.* Phase 165 ([`LEECH_KISSING_STUDY.md`](LEECH_KISSING_STUDY.md))
  took the converse and the minimal shell; Phase 180
  ([`LEECH_SHELL_COUNT_STUDY.md`](LEECH_SHELL_COUNT_STUDY.md)) proved the
  procedure for every shell.
* GLM-BAT still counts only the minimal shell.
* `π` still a declared enclosure (taken by Phase 166,
  [`PI_MACHINE_STUDY.md`](PI_MACHINE_STUDY.md)).

### 7.4 State of the files at this reconstruction (31 October 2026)

`reasoning/leech_shells.py` is in the tree. Re-run for this reconstruction on
31 October 2026, `shell_report(7)` gives the census `1, 759, 2576, 759, 1` and
8 of 8 rows agreeing with the theta series, the norm-12 row 34,417,656,000 on
both sides. But the `catalogue` it prints, read from `llvq.shell_summary()`,
still holds 34,408,430,950: `reasoning/llvq.py` in the tree is the version from
before this round (its stored table again, without `leech_shells()`), so the
Phase 164 correction of the `llvq` table was lost in the reorganisation; this
was reported for repair the same day. `LeechShells.lean` and
`tests/test_leech_shells.py` are not in the tree (the Lean file is recorded
missing in [`_lean_files_needed.md`](_lean_files_needed.md), and two held files
wait for it).

## In one paragraph

Phase 164 defines the Leech lattice in Lean by Conway's construction from the
Golay code and proves that every minimal vector has one of the three shapes
(`minimal_shape`). A counting procedure given only the definition and the
weight census it walks from the generator (`1, 759, 2576, 759, 1`) counts every
shell; the theta series `E₄³ − 720Δ`, which uses no Golay code, agrees on every
shell through norm 14 (8 of 8). The stored table had the norm-12 shell as
34,408,430,950 where the lattice has 34,417,656,000; the tool now answers from
the derived count. 6 of 6 marks.
