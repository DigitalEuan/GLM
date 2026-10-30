# Every Leech shell, counted and proved — the generating-function procedure proved correct for every shell

## Tier 0 — the coarse read

**Question.** Can the GLM prove, from Conway's definition of the Leech lattice, that its generating-function counting procedure gives the number of lattice vectors on every shell — the step Phases 164 and 165 left argued for every shell but the minimal one?

**Verdict.** Yes. For every `t` the number of lattice vectors of squared length `16t` is proved to be the generating-function count, written in Lean as the same three steps the Python procedure takes; the Phase 164 procedure is proved to give the lattice's counts on the shells it was run on, and the first eight shells are theorems about the definition, read by the Python package and set beside its own count and the theta series.

**Deciding figure.** 6 of 6 marks; `shellArr_correct` for every `t`, 0 `sorry`; the first eight shells proved (`1, 0, 196560, 16773120, 398034000, 4629381120, 34417656000, 187489935360`), 8 of 8 rows agreeing three ways; the Lean file builds in under a minute; the end-to-end evaluation's one Leech shell case unchanged.

**Recomputed by.** `glm_universal.reasoning.leech_shells.proved_shells_check`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

*Created 22 October 2026 (pre-registered and measured 22 October 2026, in the
same session: the marks of §5 were written before the proofs were finished,
but not committed separately).*

## 0. What this document is

A study for Phase 180. It takes the line of To-Do item 2 (*the machine's
reading, the rest*) that [`LEECH_SHELLS_STUDY.md`](LEECH_SHELLS_STUDY.md) §7.3
and [`LEECH_KISSING_STUDY.md`](LEECH_KISSING_STUDY.md) §7.3 left:

* *the procedure's correctness for the shells `t ≥ 3` is still argued, not
  proved.*

Phase 164 defined the lattice in Lean (`GLM.LeechShells.IsLeech`) and ran the
counting procedure there, but the step from "the procedure's number" to "the
number of lattice vectors" was the paragraph *the count on a codeword depends
only on its weight*. Phase 165 proved the count for the minimal shell by an
explicit bijection with three parameter families, which does not extend to
other shells. This round proves the procedure itself.

## 1. What is proved

**The Lean file** (`glm_lean/RequestProject/GLM/LeechShellCount.lean`,
over `IsLeech`, `normSq` and the census of `LeechShells.lean`).

* **Generating functions.** `GF` is Mathlib's `AddMonoidAlgebra ℕ (ℕ × ZMod 8)`:
  a monomial records a squared length and a coordinate sum mod 8. `gfOne r B`
  is the sum of the monomials of the integers `≡ r (mod 4)` in `[-B, B]`.
* `coeff_prod` — the product over the 24 coordinates of their generating
  functions has, at `p`, the number of vectors whose coordinates lie in their
  classes and whose exponents sum to `p`. (The product of sums is the sum
  over the box of products, `Finset.prod_univ_sum`, and a product of
  monomials is the monomial of the sum.)
* `prod_pattern` — **the study's argument as a theorem**: when coordinate
  `i` has class `a` on a set `c` and `b` off it, the product is
  `gfOne a ^ |c| * gfOne b ^ (24 − |c|)`, a function of `|c|` alone.
* `card_shellSet` — the lattice vectors of squared length `16t` are the
  disjoint union, over the parity `m ∈ {0, 1}` and the codeword `c`, of the
  vectors whose residues mod 4 follow `c`'s pattern for `m` (`2` on `c` and
  `0` off it, or `1` on `c` and `3` off it) with coordinate sum `≡ 4m (mod 8)`
  (`isLeech_iff`, `pat_inj`); `card_fib` counts each piece as a coefficient,
  `sum_codewords` sums by weight against the census, and `shell_card_gf`
  puts them together.
* **The procedure.** `oneArr`, `mulArr`, `powArr`, `patternArr`, `shellArr`:
  arrays indexed `8n + s`, truncated at squared length `16t`, with the same
  three steps as `reasoning/leech_shells.py` (one-coordinate tables, powers
  and products, the coefficient at `(16t, 4m)`). `Rep lim A P` says the array
  holds `P`'s coefficients up to `lim`; `rep_one`, `mul_coeff` (a coefficient
  of a product is a truncated convolution), `rep_mul`, `rep_pow`,
  `patternArr_eq`.
* `shellArr_correct` — **for every `t`, the number of lattice vectors of
  squared length `16t` is `shellArr t`.** `shellFast_correct` — the same for
  `shellFast`, which forms the powers `8, 12, 16, 24` once by squaring and
  reads one coefficient.
* `shellCount_correct` — the procedure of `LeechShells.lean` itself gives the
  lattice's counts for `t ≤ 4`, the range Phase 164 ran it on
  (`shellFast_eq_shellCount`, an evaluation).
* `leech_shell_sizes` — the first eight shells, true norms `0` to `14`:
  `1, 0, 196560, 16773120, 398034000, 4629381120, 34417656000,
  187489935360`.

The correctness proof uses no computation beyond the Golay census of
`GolayWeightEnum.lean` (`golay_weight_enumerator`, `golay_weight_mem`); the
shell sizes are `native_decide` evaluations of a procedure proved correct.
The minimal shell's 196,560 is now proved twice, by Phase 165's bijection and
by this procedure.

**The Python reading.** `leech_shells.proved_shell_sizes` reads the eight
sizes out of the statement of `leech_shell_sizes` in the Lean file (nothing
stored), and `proved_shells_check` sets them beside the package's own count
(`shells`) and the theta series (`modular_shells`), which uses no Golay code.

## 2. The control

The theta series `E₄³ − 720Δ`, as in Phase 164: an independent derivation. A
proved size that disagreed with it would be a failure of the round.

## 3. What is not claimed

The Python procedure of `reasoning/leech_shells.py` is not itself proved: the
Lean procedure is the same three steps written over arrays, and the two agree
on every shell read (§7). The proof says nothing about the theta series, which
stays a check rather than a theorem. GLM-BAT still counts only the minimal
shell.

## 4. Faculties

**Derivation**, made formal: a counting procedure the GLM used on an argument
is now a theorem about the lattice, for every shell.

## 5. The marks

| mark | what is met |
|---|---|
| **L1** | `LeechShellCount.lean` builds with no `sorry` and is in `AxiomAuditAll.lean`; the audit passes (standard axioms only) |
| **L2** | `shellArr_correct` and `shellFast_correct` are stated for every `t`, with the set of lattice vectors on the left |
| **L3** | `shellCount_correct`: the Phase 164 procedure is the lattice's count on `t ≤ 4` |
| **S1** | `leech_shell_sizes` proves eight shells, and the eight agree with the Python count and the theta series (`proved_shells_check`) |
| **B1** | the file builds in under two minutes on this machine |
| **F1** | no evaluation answer moves |

## 6. How it is measured

`lake build RequestProject.GLM.LeechShellCount` and `lake build` (the audit);
`PYTHONPATH=. python3 -c "from glm_universal.reasoning import leech_shells as
L; print(L.proved_shells_check(7))"` from ``;
`tests/test_leech_shell_count.py`; and the evaluation case
`tool-leech-norm-12`.

## 7. What came out

### 7.1 The marks

| mark | result | met |
|---|---|---|
| **L1** | builds, 0 `sorry`; `AxiomAuditAll` passes with 9,922 theorems, standard axioms only | yes |
| **L2** | `shellArr_correct (t : ℕ) : {x \| IsLeech x ∧ normSq x = 16 * t}.ncard = shellArr t`, and the same for `shellFast` | yes |
| **L3** | `shellCount_correct {t} (ht : t < 5)` | yes |
| **S1** | 8 of 8 rows agree: 1, 0, 196,560, 16,773,120, 398,034,000, 4,629,381,120, 34,417,656,000, 187,489,935,360 | yes |
| **B1** | 42 seconds | yes |
| **F1** | the evaluation case `tool-leech-norm-12` still answers 34,417,656,000 *counted from the Golay census*; no other case reads a shell | yes |

**Disclosed.** The first build of the file took 523 seconds: the shell sizes
were evaluated with the straightforward procedure, which recomputes every
power for every weight, through Mathlib's `Finset` sums. `shellFast` (powers
shared by squaring, list sums, one coefficient read) was added and proved
correct the same way; the build fell to 42 seconds. `shellArr` and its
theorem stay, as the direct form of the procedure.

### 7.2 What this answers

The procedure the GLM has used since Phase 164 to count every Leech shell is
now proved: the sizes of the shells — including the norm-12 shell whose stored
value the GLM had repeated wrongly until Phase 164 — are theorems about
Conway's definition, not values of a procedure resting on an argument.

### 7.3 What is left

* The Python procedure is checked against the Lean one on every shell read,
  not proved; a proof of the Python code is outside the Lean development.
* The `llvq` tool's answer still says *counted from the Golay census*; citing
  `shellArr_correct` there changes answers that frozen paths record, so it
  needs those re-takes.
* GLM-BAT counts only the minimal shell; the generating-function count could
  be said as GLM-BAT, at a cost the machine-step budget would have to price.

## In one paragraph

Phase 164 counted every shell of the Leech lattice by a generating-function
procedure, on the argument that the count on a codeword depends only on its
weight; Phase 165 proved the minimal shell's count by a bijection.
`LeechShellCount.lean` proves the procedure for every shell: the product of
per-coordinate generating functions counts vectors, over a codeword pattern
the product depends only on the weight (`prod_pattern`), the shell splits over
parity and codeword, and the array procedure computes the coefficients
(`shellArr_correct`). The Phase 164 procedure is the lattice's count on the
shells it ran, and the first eight shells are theorems, agreeing with the
Python count and the theta series. 6 of 6 marks.
