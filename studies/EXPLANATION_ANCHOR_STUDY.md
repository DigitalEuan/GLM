# Explanations anchored in the registers

## Tier 0 — the coarse read

**Question.** Thirty-two of the outside questions (class E of the Capability Failure Matrix, track E of `QUESTION_SET_B_STUDY.md` §8) ask *why*: why helium is inert, why technetium has no stable isotope, why beryllium-8 falls apart, why a series RLC circuit turns inductive above resonance, why material implication is paradoxical. Three more (29, 39 and 96) were refused by Phase 107 as accounts rather than derivations. Can the machine answer the part of each that a register or an exact derivation decides, refuse the rest by name, and say so when a register contradicts the question's premise?

**Verdict.** Yes for the thirty-five declared questions, with a large recognition gap on rewordings. Every one is read by its declared topic and answered with values read from the element register or a new nuclide register (AME2020 and NUBASE2020) or with an exact derivation, every causal or philosophical account it asks for is stated as refused EXPLANATION, three register contradictions are reported as disputed premises, and every answer carries a column-3 script that fails when its claim or a register row is altered. All ten marks were met, but only five of thirty-five held-out rewordings were read; none was read by a wrong topic.

**Deciding figure.** 10 of 10 marks met; 35 of 35 questions answered with the declared fragment (3 FULL, 32 with the account refused); 25 read a register; 35 of 35 scripts verified, script-claim 35 of 35 and register-row 21 of 21 caught; 3 of 3 disputes; 35 of 35 paraphrases; 5 of 35 held-out rewordings, 0 misread; 0 of 279 other texts read; 3558 ground states, 253 stable; 15 named theorems, 0 `sorry`.

**Recomputed by.** `glm_universal.runtime.explanation_report.explanation_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

Code: [`glm_universal/reasoning/explanation_anchors.py`](../glm_universal/reasoning/explanation_anchors.py),
[`glm_universal/data_objects/nuclides.py`](../glm_universal/data_objects/nuclides.py),
[`glm_universal/runtime/explanation_frames.py`](../glm_universal/runtime/explanation_frames.py),
[`glm_universal/runtime/explanation_report.py`](../glm_universal/runtime/explanation_report.py),
[`glm_universal/evaluation/explanation_cases.py`](../glm_universal/evaluation/explanation_cases.py),
[`glm_universal/runtime/question_frames.py`](../glm_universal/runtime/question_frames.py).
Tests: [`glm_universal/tests/test_explanations.py`](../glm_universal/tests/test_explanations.py).
Lean: [`RequestProject/GLM/ExplanationAnchors.lean`](../glm_lean/RequestProject/GLM/ExplanationAnchors.lean).

---

## 0. Where this comes from

[`QUESTION_SET_B_STUDY.md`](QUESTION_SET_B_STUDY.md) §8 left track E open:
the class-E questions of `Outside_Question_Set_B_candidate_O1.txt` ask for an
explanation, and no frame read one. `STATUS.md` named the line "32 outside
questions, including outside questions 29, 39 and 96". Read against
`question_set_b_cases.BOUNDARY`, class E holds 32 questions (0, 4, 23, 32,
43, 60–80 without 81, 82, 83, 84, 87, 88 and 89) and 29, 39 and 96 are class
P ([`DERIVATION_TWO_STUDY.md`](DERIVATION_TWO_STUDY.md) refused them as
accounts), so the line covers **35** questions. All 35 are declared; the
case file's docstring records the count.

**The position taken.** An explanation is not a value, and the machine does
not produce one. What it can do is answer the part of a *why* question that
is decided: the measured quantities the explanation would rest on (read from
a register, with the row named), and the closed statements an explanation
would have to agree with (derived exactly, and where it is general, proved
in Lean). The rest is stated, inside the answer, as `refused EXPLANATION`
with what it would need — the shell model, Mattauch's isobar rule, relativistic
quantum chemistry, a philosophical reading of a theorem.

**Order of work, stated plainly.** The cases and marks
(`glm_universal/evaluation/explanation_cases.py`), with every expected
fragment worked by hand from the questions, the element register and the
two outside tables, were written and committed **before any code of the
round**. The nuclide register and the Lean file came next, then the anchors,
frames and report. The paraphrases were written with the cases, so the cues
were built with them in view and the paraphrase mark is not a held-out
measure. The held-out rewordings were written after the first run and
committed **before any cue was changed**; they were then run once and are
reported as measured. The commit history holds that order.

## 1. What was added

* **A nuclide register**, `data_objects/nuclides.py` with its frozen copy
  `data_objects/_data/world_ame2020.json`: the Atomic Mass Evaluation 2020
  (`mass_1.mas20.txt`) and NUBASE2020 (`nubase_4.mas20.txt`), as published by
  the IAEA Nuclear Data Section, frozen with the SHA-256 of each raw file.
  Ground states only: 3558 of them, 253 marked stable. Mass excesses are kept
  as exact rationals parsed from the table strings; a value the table marks
  `#` (from systematics, not measured) keeps the mark and is refused unless a
  caller asks for estimates. Binding energies, Q-values and separation
  energies are computed from mass excesses exactly.
* **`RequestProject/GLM/ExplanationAnchors.lean`** (namespace
  `GLM.ExplanationAnchors`). Circuits: `reactance_pos_above_resonance`,
  `reactance_strictMonoOn` and `impedance_sq_strictMonoOn` (above resonance the
  reactance is positive and the impedance strictly increasing, for every
  `R, L, C > 0`); `filtered_derivative_gain_lt` and `pure_derivative_unbounded`
  (a filtered derivative's gain is bounded by `Kd/τ_f`, a pure one's is not).
  Nucleons: `nucleon_pair_channels` and `identical_pair_singlet` (the spin
  and isospin counting behind the deuteron's single bound state). Logic:
  `chain_em_fails`, `chain_dne_fails` and `chain_nn_em` (a two-world Kripke
  frame refutes excluded middle and double-negation elimination
  intuitionistically, while `¬¬(p ∨ ¬p)` holds), `strict_implication_fails`,
  `frechet_lower` and `not_truth_functional` (fuzzy conjunction against
  probability), `inconsistent_proves_all`, `countable_elementary_substructure`
  (downward Löwenheim–Skolem, from Mathlib). Questions 39 and 96:
  `mpc_instance_optimal`, `mpc_clipped_worse`, `real_root_no_rational_root`.
  Register certificates: `be8_unbound` (Q of beryllium-8 into two alpha
  particles from the AME2020 rows) and `technetium_unstable` (every one of
  the 28 technetium isotopes AME2020 measured is heavier than its molybdenum
  or its ruthenium isobar), with `technetiumTable_length`. Standard axioms
  only.
* **`reasoning/explanation_anchors.py`**, the anchor layer, kept below the
  frames: thirty-five topics, each with its cues, what it reads, what it
  derives (with outward-rounded rational enclosures for square and cube
  roots, logarithms, exponentials, π and the sine integral), the account it
  refuses, its disputes and a column-3 script that embeds the register rows
  it read and re-derives every anchor from them.
* **`runtime/explanation_frames.py`**, one frame per topic (source `E`),
  appended after the meta frames in `question_frames._all_frames` behind an
  `EXPLANATIONS` switch, so every earlier frame keeps its claim on a text.
* **`runtime/explanation_report.py`** and `tools explanations` (`--json`,
  `--quick`), which compute the marks.

## 2. The marks

| mark | what it asks | result |
|---|---|---|
| E1 | each question read through the router by its declared topic, answered, with the declared fragment | 35/35 |
| E2 | every ANCHORED answer states its account as refused EXPLANATION, no FULL answer does | 35/35; 3 FULL |
| E3 | every answer that reads a register names the rows it read | 35/35; 25 read a register |
| E4 | every column-3 script prints `VERIFIED True` in a fresh `python3 -I`; every control that applies caught | 35/35; script-claim 35/35, register-row 21/21 |
| E5 | exactly the declared disputed premises | 35/35; 3 disputes |
| E6 | at least 32 of the 35 paraphrases read by their topic with the same fragment | 35/35 |
| E7 | the explanation frames read none of the 10 near misses, the other 77 outside questions, Set B or the evaluation cases; switching them on moves no other text | 0 of 279 read; 0 changed |
| E8 | the nuclide register passes its read-back checks (raw digests, every mass excess round-tripping, the deuteron at 2224.566 keV, the binding peak at nickel-62, 250–260 stable) | 5/5 |
| E9 | the Lean file proves the 15 named theorems with no `sorry` | met |
| E10 | questions 29, 39 and 96 answered, every outside question answered before keeping its frame | met |

The register-row control applies to 21 of the 35 answers: the 25 that read a
register less the four logic answers (80, 82, 83, 88), which name the
machine's `proof_search` procedure as what decides them but embed no row of
it for a control to alter. The ten derivations read no register at all.

**The held-out record.** The thirty-five held-out rewordings were written
after the first run and before any cue changed. Run once: **5 of 35** were
read by their declared topic and answered; the other 30 were read by no
frame, and **none was read by a wrong topic**. The cues are keyword sets
built with the declared questions and their paraphrases in view, and a
rewording that swaps the key nouns ("imrefs" for "quasi-Fermi levels", "pn
diode" for "junction") falls through. The figure is reported, not
redeclared, and no cue was changed to read a held-out text.

**What the whole suite found.** E7's declared texts are the near misses,
the other outside questions, Set B and the evaluation cases. The suite's
wider scan — every string constant of the package — found four strings from
earlier rounds' case files read by two cues: three register-world questions
that name oganesson ("is the atomic weight of oganesson consistent with the
standard…") and one stepwise question, "what is the rank of osmium by density
among all the elements". Both cues were narrowed after the held-out record:
`oganesson` now also needs a relativity, spin-orbit or noble-gas word, and
`osmium_density` a *why*, *explain*, *peak* or *paradox* word. The marks were
re-taken (10 of 10) and the held-out rewordings re-run: still 5 of 35, none
misread. Two earlier records were brought level with the round, each
decided after the case file and recorded here: Phase 107's declaration that
questions 29, 39 and 96 stay unframed is now checked with the explanation
frames off (no frame before them reads the three; the report adds
`taken_by_phase_120`), and the discourse census now counts two texts the
layer would take as follow-ups that the machine answers alone (outside
question 67 and a rewording of 80) — answered whole first, they never reach
the layer, and no text is released.

## 3. What is answered, and what is refused

**FULL** (3): question 0 (above resonance a series RLC circuit is inductive
and its impedance rises — proved for every `R, L, C > 0`), question 32 (the
derivative kick of a PID, bounded by `Kd/τ_f` when the derivative is
filtered and unbounded when it is not) and question 74 (the double-beta
Q-value of germanium-76, 2039.06 keV, from AME2020).

**ANCHORED** (32): the decided part answered, the account refused. Examples:

* *Technetium* (65). Every technetium isotope AME2020 measured is heavier than
  a neighbouring isobar, so a decay is open for each (`technetium_unstable`);
  the narrowest margin is technetium-99 to ruthenium-99, 297.5 keV. Why the
  valley of stability skips `Z = 43` (Mattauch's rule, pairing) is refused.
* *Beryllium-8* (73). `Q(⁸Be → 2α) = 91.840 keV > 0` from the two AME2020
  rows (`be8_unbound`); why two alpha particles do not bind is refused.
* *The Hoyle state* (79), *the lithium problem* (78), *the deuteron* (70),
  *mirror nuclei* (71): thresholds, Q-values and binding differences read
  from AME2020 (7274.75 keV, 861.89 keV, 2224.566 keV, 2764.0 keV); the
  nuclear and cosmological accounts refused.
* *Periodic trends* (60–68): the register's ionisation energies,
  electronegativities, densities and configurations, with Slater effective
  charges and the Dirac factor `sqrt(1 - (Zα)²)` computed exactly; the
  quantum-chemical accounts refused.
* *Logic* (80–89): Kripke countermodels and counting arguments, several of
  them proved; the philosophical readings refused.
* *Questions 29, 39 and 96*, refused since Phase 107: the steady-state
  balances of the CSTR and the condition for three steady states, the MPC
  problem with its constraints and an exact instance (`mpc_instance_optimal`),
  and the transfer failure of Tarski–Seidenberg to the rationals
  (`real_root_no_rational_root`).

**The disputes** (3), each the register's figures against the question's
premise: oganesson's standard state, which the element register records as
"Expected to be a Gas"; lead-208's binding energy per nucleon, which AME2020
places below lead-206 and lead-207 (the closure shows in the neutron
separation energies, 7367.9 keV falling to 3937.4 keV); and question 96's
reading of the machine's `INTEGER_UNDECIDED` as forced by Matiyasevich's
theorem, which it is not — it is the node budget of the Omega test on
Presburger constraints.

## 4. Faculty

Under D15 the round moves **refusal** (an account refused by name inside an
answer that still gives what is decided, and a false premise disputed with a
register's figures) and **grounding** (a second outside register, read in
with its raw digests, whose rows every nuclear answer names and every script
embeds).

## 5. Limits, and what the round leaves

* **Recognition.** Five of thirty-five held-out rewordings are read. The
  cues are keyword sets; a question reworded away from them is not read,
  though none was misread.
* **E7 was declared too narrow.** Its text sets missed four strings of
  earlier case files that the package-wide scan caught; the cues were
  narrowed, but the mark as declared would not have seen the problem.
* **The questions are the declared thirty-five.** A *why* question on a
  thirty-sixth topic is not read; the anchors answer the declared question
  and do not re-parse it.
* **Explanations are still refused.** Nothing here produces a causal account;
  the round makes the refusal precise and puts the decided part beside it.
* **The nuclide register holds ground states.** Isomers, excited states (the
  Hoyle state's 7654 keV is quoted, not read), cross-sections and abundances
  are not in it.

**The verdict, in the body.** Yes for the thirty-five declared questions, with a large recognition gap on rewordings. Every one is read by its declared topic and answered with values read from the element register or a new nuclide register (AME2020 and NUBASE2020) or with an exact derivation, every causal or philosophical account it asks for is stated as refused EXPLANATION, three register contradictions are reported as disputed premises, and every answer carries a column-3 script that fails when its claim or a register row is altered. All ten marks were met, but only five of thirty-five held-out rewordings were read; none was read by a wrong topic.

E9 names 15 theorems of the Lean file (`explanation_cases.LEAN_THEOREMS`);
the file proves those and six more. The register holds 3558 ground states,
253 stable. The figures of §2: 10 of 10 marks; 35 of 35 with the declared
fragment, 3 FULL, 25 read a register; script-claim 35 of 35, register-row 21
of 21; 3 of 3 disputes; 35 of 35 paraphrases; 5 of 35 held out, 0 misread;
0 of 279 other texts; 0 `sorry`.

## 6. Re-running it

From ``:

```
PYTHONPATH=. python3 -m glm_universal.tools explanations
PYTHONPATH=. python3 -m glm_universal.tools explanations --json
PYTHONPATH=. python3 -m pytest -q glm_universal/tests/test_explanations.py
```

and `lake build RequestProject.GLM.ExplanationAnchors` at the repository root
for the Lean file.
