# Round 42 study folder: engine v13 checked, v14 with reasoning guards

Everything in this folder is **EMP** (programs, not machine-checked), except where a Lean name is
given. The Lean side of Round 42 is `RequestProject/GLM/HypothesisEngine/TaxChecks.lean` (FORMAL)
and `TaxChecksData.lean` (CERT, `native_decide`). Standard library only, exact arithmetic only.

## 1. The three prize questions after Round 42

None is answered. Nothing in v13 or in this round changes that, and the engine does not claim
otherwise.

| | question | status | what the package proves toward it |
|---|---|---|---|
| P1 | is the centre column never eventually periodic? | **open** | period 1 excluded; P1 follows from each of several one-sided targets (`HalfLineDies p` for all `p`, `EchoLogBound`, AP-balance of the seed …), all collected in `Frontier.lean`; the period-2 rung is certified to `d = 36` |
| P2 | do black and white cells have frequency 1/2? | **open** | P1 and P2 both follow from `SeedAPBalanced`; the wobble bound `|D(N)| ≤ C√N` would give P2 but is probably false (iterated logarithm) |
| P3 | does computing cell `n` need more than `O(n)`-ish work? | **open** | no sufficient statement known; Round 41 showed aperiodicity alone would not settle it (`aperiodic_but_automatic`) |

What the GLM *can* do with these questions is state them exactly, test candidate statements on
exact data, refute the false ones, and say which proved facts would close each one. What it cannot
do (yet) is produce the missing uniform argument; that is the gap between "survives every test" and
"proved", and the guards below exist to keep that gap visible.

## 2. What `hypothesis_engine_v13.py` adds, checked

`v13_audit.py` runs v13 unmodified (quick mode, about 20 s) and applies the guards; results in
`v13_audit.md` / `v13_audit.json`.

**Good.** v13 is self-contained and runs. Its question ("do TAX defects explain the period
doublings?") is tested three ways, and the answer it gives, *no*, is right. It also noticed
by itself that every doubling has TAX defect 0, which refutes the v12 claim.

**Wrong or overstated** (each now settled):

| v13 statement | verdict | where |
|---|---|---|
| "because `Y` is irrational, conservation ⟺ the quadratic identity" | true for **every** real `Y`; irrationality not needed | `tax_conserved_iff_defect_zero` |
| "⟺ `w(a AND b) ∈ {0, w(a), w(b)}`" | false both ways; the right criterion is `3c² − 2c(a+b) + ab = 0` | `tax_defect_eq`, `docstring_criterion_wrong` |
| "TAX breakdown is NECESSARY for a jump" | false at **every** doubling | `tax_conserved_at_doubling` |
| "positive finding: TAX is conserved at the jumps; the white pattern is the common cause" | true but not a finding: any pair with a white member is conserved, and every doubling needs `white(D−1)` | `tax_conserved_of_right_empty`; explained-away guard |
| "TAX is conserved only at the white diagonals" | false: 116 conserved pairs below 6000, 8 with a white member; 15 non-trivial ones below 400 certified | `tax_conserved_not_only_white`, `tax_conserved_pairs_below_400` |
| "a jump occurs exactly when the (D−1) pattern is white" | needs odd parity of `D−2` too (`white(D−1)` alone fails at 53208) | `ldiag_doubles`, `ldiag_keeps_of_even` |
| header: "exact integer permutation test over C(N, k)" | not implemented | now in `glm_guards.coincidence_test` |
| "H38: NEW TO THE LEDGER" | printed for a refuted hypothesis | patched in v14 |

## 3. v14 = v13 + reasoning guards

`make_v14.py` builds `hypothesis_engine_v14.py` from v13 with 19 named patches (listed in
`v14_patches.md`; each must match exactly once). v13 itself is not modified.

The guards are in `glm_guards.py`, which is portable (nothing in it is about Rule 30):

| guard | catches | v13 example |
|---|---|---|
| `identity_guard` | a criterion stated in prose that is false | `c ∈ {0, a, b}` |
| `explained_away_guard` | a "finding" that is forced by a known law's premise | defect 0 at the jumps (forced by `white(D−1)`) |
| `coincidence_test` | exact hypergeometric tail (all placements counted) | 4 of 4 jumps conserved: `P ≈ 1.3·10⁻⁷`, yet fully explained |
| `exclusivity_guard` | "only at S" claims | "only at the white diagonals" |
| `consistency_guard` | a sentence asserting a claim whose hypothesis was refuted | "NECESSARY" after H38 was refuted |

The coincidence row is the general lesson: a statistics-only engine would report the jump/TAX
coincidence as highly significant. Before reporting a coincidence, check whether a known law
forces it.

`tax_guards.py` applies the guards to the TAX section; v14 runs it after its TAX stage, uses the
guard sentences in place of v13's fixed TAX conclusions, and runs it again over the whole run.
In the quick run, the guards flag 3 of the 6 checked statements, and the consistency guard
passes on v14's own output (`v14_quick_out.txt`, `r42_engine_report_v14_quick.*`). The full run
(`python3 hypothesis_engine_v14.py`, about 30 s, `D < 20000`) gives the same verdicts: 344
conserved pairs, 8 of them with a white member; output in `r42_engine_report_v14.*` and
`v14_full_out.txt`.

## 4. Reproduce

    python3 test_round42.py          # 6 checks, about 45 s
    python3 v13_audit.py             # writes v13_audit.md / .json
    python3 make_v14.py              # rebuilds hypothesis_engine_v14.py from ../hypothesis_engine_v13.py
    python3 hypothesis_engine_v14.py --quick

Lean: `lake build RequestProject.GLM.HypothesisEngine.TaxChecks RequestProject.GLM.HypothesisEngine.TaxChecksData`.
