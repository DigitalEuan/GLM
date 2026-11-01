# The Leech kissing number from the lattice's definition — the minimal shell proved both ways and counted in Lean

## Tier 0 — the coarse read

**Question.** Can the GLM prove in Lean the two steps Phase 164 left argued about the minimal shell of the Leech lattice — the converse of the shapes theorem, and that the count `759 · 128 + 276 · 4 + 4096 · 24` is the number of lattice vectors of squared length 32?

**Verdict.** Yes. The minimal shell is built as the image of three parameter families and proved to be exactly the set of lattice vectors of squared length 32, the converse needs no sum condition for the odd shape because the code is doubly even, and the shell is proved to have 196,560 elements on the Golay census and nothing else; the same families enumerated in Python give 196,560 distinct vectors, every one in the lattice by the definition.

**Deciding figure.** 5 of 5 marks; `minimal_iff` and `leech_kissing_number` (196,560 = 759 · 128 + 276 · 4 + 4096 · 24) with 0 `sorry`; 196,560 distinct vectors enumerated, all in the lattice and of squared length 32; no answer moved.

**Recomputed by.** `glm_universal.reasoning.leech_shells.minimal_shell_check`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

*Created 31 October 2026. Reconstructed 31 October 2026 from the round records; the original was lost in the October 2026 reorganisation.* The original was written on 19 October 2026 (the date of the Phase 165 record); its marks (L1, L2, P1, P2, F1) were written before the measurement in the same session.

> **How this reconstruction was made.** From the Phase 165 record of
> [`MASTER_PLAN.md`](../MASTER_PLAN.md), the "Leech kissing number from the
> lattice's definition" row of [`SYSTEM.md`](../SYSTEM.md), §20.39 and the
> study table of [`GLM_ACADEMIC_PAPER.md`](GLM_ACADEMIC_PAPER.md), To-Do item
> 2 of [`STATUS.md`](../STATUS.md), the row of `tests/README.md` for
> `test_leech_kissing.py`, the docstring of `reasoning/leech_shells.py`, and
> the lines of §7.3 that [`PI_MACHINE_STUDY.md`](PI_MACHINE_STUDY.md) and
> [`LEECH_SHELL_COUNT_STUDY.md`](LEECH_SHELL_COUNT_STUDY.md) quote. The marks'
> wording was not recorded anywhere that survived; the records give their
> outcome (5 of 5). The Python half was re-run for this reconstruction (§7.4);
> no other figure appears that the records do not give.

## 0. What this document is

A study for Phase 165, taken from `STATUS.md` §2.1 item 2 (*the machine's
reading, the rest*: the converse of `minimal_shape` and the procedure's
correctness argued, not proved), the first line of
[`LEECH_SHELLS_STUDY.md`](LEECH_SHELLS_STUDY.md) §7.3.

Phase 164 proved one direction about the minimal shell (every minimal vector
has one of the three shapes) and left two steps argued: the converse of the
shapes theorem, and that the count `759 · 128 + 276 · 4 + 4096 · 24` is the
number of lattice vectors. This round proves both in Lean.

## 1. What was built

* **`src/lean/RequestProject/GLM/LeechKissing.lean`** (0 `sorry`): the three
  parameter families — an octad with an even set of minus signs
  (`octadParams`), a pair of positions with any signs (`pairParams`), a
  codeword with the position of its `±3` (`oddParams`) — and their images;
  `minimalShell`; `mem_minimalShell` (the finite set is exactly the lattice
  vectors of squared length 32); `minimal_iff` (the converse, with the odd
  shape's sum condition derived from the code being doubly even);
  `card_minimalShell` and `leech_kissing_number` (196,560 = 759 · 128 + 276 · 4
  + 4096 · 24, by injectivity and disjointness, on the Golay census of
  `GolayWeightEnum.lean`).
* **`reasoning/leech_shells.py`**: `minimal_shell_vectors` (the same finite
  set the Lean file builds, from the same three parameter families) and
  `minimal_shell_check` (every vector tested against the definition);
  `KISSING_LEAN_FILE` and `KISSING_LEAN_THEOREMS`.

## 2. The control

Control variants that must be rejected by the membership test: an octad with
an odd number of minus signs, and the odd shape with the wrong sign of the `3`.

## 3. What is not claimed

Only the minimal shell is proved; the generating-function procedure of Phase
164 for the other shells is still argued. GLM-BAT's REM line for the kissing
number still cites `minimal_shape`.

## 4. Faculties

*Derivation*, made formal: the kissing number the machine counts is now a
theorem about the lattice. No answer moved.

## 5. The marks

| mark | what the records attach to it |
|---|---|
| **L1** | not recorded one by one |
| **L2** | not recorded one by one |
| **P1** | not recorded one by one |
| **P2** | not recorded one by one |
| **F1** | not recorded one by one |

The wording of the five marks is lost. What the round's tests checked
(`tests/test_leech_kissing.py`, 4): the Lean file's theorems and no `sorry`;
the explicit minimal shell built from the three parameter families is 196,560
distinct lattice vectors of squared length 32; the split 759·128 + 276·4 +
4096·24; the control variants rejected.

## 6. How it is measured

`PYTHONPATH=src python3 -c "from glm_universal.reasoning import leech_shells as L; print(L.minimal_shell_check())"`;
the Lean file by `lake build`; the tests by hand: 4 of 4 passed, and
`tests/test_leech_shells.py` 5 of 5 (pytest was not installed).

## 7. What came out

### 7.1 The marks

| mark | outcome |
|---|---|
| **L1** | met |
| **L2** | met |
| **P1** | met |
| **P2** | met |
| **F1** | met |

**5 of 5 marks.**

### 7.2 What this answers

Yes. The minimal shell is built as the image of three parameter families and proved to be exactly the set of lattice vectors of squared length 32, the converse needs no sum condition for the odd shape because the code is doubly even, and the shell is proved to have 196,560 elements on the Golay census and nothing else; the same families enumerated in Python give 196,560 distinct vectors, every one in the lattice by the definition.

The parameter maps are injective and their images disjoint, so the shell has
196,560 elements (`leech_kissing_number`). **Answers moved — none** from
answering code. The evaluation's two Lean-corpus pins (`report relay`, `report
anonymous`) were re-pinned for the corpus refreshed with `LeechKissing.lean`,
claims unchanged; 223 of 223.

### 7.3 What is left

* The generating-function procedure for `t ≥ 3` — *the procedure's correctness
  for the shells `t ≥ 3` is still argued, not proved* (proved by Phase 180,
  [`LEECH_SHELL_COUNT_STUDY.md`](LEECH_SHELL_COUNT_STUDY.md)).
* GLM-BAT's REM line still cites `minimal_shape` (changed by Phase 166).
* *`π`'s enclosure is a declared constant (Mathlib's proved bounds), where a
  series the machine sums would make it computed like `e`* (taken by Phase
  166, [`PI_MACHINE_STUDY.md`](PI_MACHINE_STUDY.md)).

### 7.4 State of the files at this reconstruction (31 October 2026)

`reasoning/leech_shells.py` is in the tree. Re-run for this reconstruction on
31 October 2026, `minimal_shell_check()` gives 196,560 vectors, 196,560
distinct, 196,560 in the lattice by the definition, 196,560 of squared length
32. `LeechKissing.lean` and `tests/test_leech_kissing.py` are not in the tree
(the Lean file is recorded missing in
[`_lean_files_needed.md`](_lean_files_needed.md)); `GolayWeightEnum.lean` is
present.

## In one paragraph

Phase 164 left two steps about the Leech lattice's minimal shell argued. Phase
165 proves both in Lean: the shell is the image of three parameter families —
an octad with an even set of minus signs, a pair of positions with any signs,
a codeword with the position of its `±3` — and exactly the lattice vectors of
squared length 32 (`mem_minimalShell`); the converse `minimal_iff` needs no sum
condition for the odd shape because the code is doubly even; and the maps are
injective with disjoint images, so the shell has 196,560 elements
(`leech_kissing_number`), on the Golay census and nothing else. The same
families enumerated in Python give 196,560 distinct vectors, each in the
lattice by the definition. 5 of 5 marks; no answer moved.
