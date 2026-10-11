# Meta questions answered from the project's own documents

## Tier 0 — the coarse read

**Question.** Eighteen of the outside questions (class M of the Capability Failure Matrix, track M of `QUESTION_SET_B_STUDY.md` §8) ask about the GLM itself: how it compares distances without a square root, why it refuses `UNCORRECTABLE` past weight 3, how its integer procedure stops, how Lean checks a rational inverse. Can the machine answer them from its own studies, code and Lean development, quoting what it reads at the time it reads it, and say so when a question's premise is not what the documents say?

**Verdict.** Yes for the eighteen declared questions, and with a recognition gap on rewordings. Every one is read by its declared topic and answered with quotes found in the studies at read time, Lean declarations found in the stored address book, and the disputed premises the documents contradict; a moved quote or a renamed theorem turns the reading into the refusal `CITATION_MOVED`. Six of the seven marks were met: the paraphrase mark missed one rewording, which an earlier frame reads and answers correctly, and one held-out rewording is not read at all.

**Deciding figure.** 6 of 7 marks met; 18 of 18 questions answered with the declared fragment; 30 quotes and 24 theorems found at read time; 11 of 11 declared disputes and no others; 4 of 4 mutation kinds caught on 18 of 18 questions; 35 of 36 paraphrases (31 of 36 at the first run); 17 of 18 held-out rewordings; 0 of 296 other texts read; 10 named theorems, 0 `sorry`.

**Recomputed by.** `glm_universal.runtime.meta_report.meta_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

Code: [`glm_universal/reasoning/meta_evidence.py`](../overlay/glm_universal/reasoning/meta_evidence.py),
[`glm_universal/runtime/meta_frames.py`](../overlay/glm_universal/runtime/meta_frames.py),
[`glm_universal/runtime/meta_report.py`](../overlay/glm_universal/runtime/meta_report.py),
[`glm_universal/evaluation/meta_question_cases.py`](../overlay/glm_universal/evaluation/meta_question_cases.py),
[`glm_universal/runtime/question_frames.py`](../overlay/glm_universal/runtime/question_frames.py).
Tests: [`glm_universal/tests/test_meta_questions.py`](../overlay/glm_universal/tests/test_meta_questions.py),
[`glm_universal/tests/test_question_frames.py`](../overlay/glm_universal/tests/test_question_frames.py).
Lean: [`RequestProject/GLM/MetaAnswers.lean`](../overlay/glm_lean/RequestProject/GLM/MetaAnswers.lean).

---

## 0. Where this comes from

[`QUESTION_SET_B_STUDY.md`](QUESTION_SET_B_STUDY.md) §8 item 3 left the
eighteen class-M questions of `Outside_Question_Set_B_candidate_O1.txt`
(indices 91–94, 97–102 and 104–111) unanswered: each names the machine and
asks how it does something, and no frame read a question about the machine.
Most of the answers were already written down — in the paper, the
integer-decision study, the carried-fork study, the Lean-address study and
the symbolic-parameters study — and some rested on theorems already in the
development (`GLM.Golay.snap_ambiguous_at_four`,
`GLM.Golay24.unique_octad`, `GLM.IntegerDecision.dark_shadow_gap`). Six did
not have a theorem behind them; this round proved those.

**Order of work, stated plainly.** The Lean file was written and built
first. The cases and marks
(`glm_universal/evaluation/meta_question_cases.py`) were written and
committed **before any code of the round**; the held-out rewordings were
written after the first run and committed **before any cue was changed**;
the evidence layer and the frames came after. The commit history holds that
order.

## 1. What was added

* **`RequestProject/GLM/MetaAnswers.lean`** (namespace `GLM.MetaAnswers`).
  Distance by squares: `euclid_le_iff`, `euclid_lt_iff` and
  `euclid_le_euclid_iff` say that a bound on the Euclidean distance of two
  rational points is the same bound on the squared distance, so no square
  root is needed. `torricelli_crossing` says the outflow speed crosses a
  critical speed `v ≥ 0` exactly when `v^2 < 2gh`. The Cayley transform:
  for a rational skew-symmetric `A`, `1 - A` and `1 + A` are invertible
  (`isUnit_det_one_sub_of_skew`, `isUnit_det_one_add_of_skew`), and
  `(1 + A)(1 - A)^-1` is orthogonal with determinant 1 (`cayley_orthogonal`,
  `cayley_det`), so rotations with rational entries come with no sines.
  `lattice_map_rational`: a real map that sends a rational basis to integer
  combinations of it is itself rational, `B M B^-1`. Inverse certificates:
  `inverse_of_certificate` (`A * B = 1` gives `A^-1 = B`) and
  `certificate_example` on a 3 × 3 matrix. Standard axioms only.
* **`reasoning/meta_evidence.py`**, the evidence layer, kept below the
  frames. Eighteen topics, each with its cue, the quotes it takes from the
  six cited studies (a declared fragment, extracted as the sentence, table
  row or list item that holds it, with its section heading), the Lean
  declarations it cites (looked up in the stored address book
  `reasoning/_data/lean_addresses.json`, never the tree), code facts read
  from the package, the disputed premises and a column-3 script. A fragment
  no longer in its document, or a declaration no longer in the book, makes
  the reading the refusal `CITATION_MOVED`.
* **`runtime/meta_frames.py`**, a thin wrapper producing `META_FRAMES`
  (source `M`), appended last in `question_frames._all_frames` behind a
  `META` switch, so every earlier frame keeps its claim on a text.
* **`runtime/meta_report.py`** and `tools meta-questions` (`--json`,
  `--quick`), which compute the marks.
* The Lean address book rebuilt (4763 declarations, the new ones among them).

## 2. The marks

| mark | what it asks | result |
|---|---|---|
| T1 | each question read by its declared topic, answered with the declared fragment | 18/18 |
| T2 | every declared quote in its document and every declared theorem in the development, at read time | 18/18; 30 quotes, 24 theorems |
| T3 | exactly the declared disputed premises | 18/18; 11 disputes |
| T4 | every column-3 script prints `VERIFIED True` in a fresh `python3 -I`; every mutation kind caught | 18/18; quote-moved, lean-moved, script-quote and script-claim each 18/18 |
| T5 | every declared paraphrase read by its topic with the same fragment | **35/36 — missed** |
| T6 | the meta frames read none of the other texts, and switching them on changes no other text's frame | 0 of 296 read; 0 changed |
| T7 | the Lean file proves the named theorems with no `sorry` | met |

**The first run.** At the first run 31 of the 36 paraphrases were read
(missed: p92a, p99b, p100b, p102a, p102b). The eighteen held-out rewordings
were then written, before any cue changed, and after the cues of
`beyond_radius`, `squared_distance` and `rational_rotation` were widened from
the paraphrase misses alone, 17 of 18 held-out texts were read (missed: h92).
The first run also found two other outside questions meeting a meta cue
below the router — question 35 met `transcendental_delay` through "transfer
function", question 95 met `exact_growth` through "overflow" — each masked on
the router by an earlier frame. Those two cues were narrowed ("integer
overflow"; a PID or controller), and both are recorded in
`meta_report.FIRST_RUN`.

**The miss.** p92a is read by the earlier `deep_hole_tie` frame, which
answers it correctly (6 nearest codewords, `AMBIGUOUS`) but not by the
declared topic, so T5 is not met. The mark is reported missed rather than
redeclared. h92 ("coset weight is 4") is not read by any frame.

**Question 101.** It was first expected to be refused `NOT_IN_CORPUS`, but
the symbolic-parameters study records exactly that growth and its repair —
fraction-free Bareiss elimination — so all eighteen are answered. The
declaration's docstring first gave the study's sections as "§0 and §1"; they
are §1 and §4.1, and the docstring now says so.

## 3. What is proved and what is quoted

Six answers (91, 97, 98, 100, 102, 110) rest on this round's Lean file as
well as on documents. Twelve (92, 93, 94, 99, 101, 104–109, 111) rest only on
material that existed before the round. Four answers cite no theorem (101,
107, 109, 111): they are about the machine's engineering — exact arithmetic,
symbolic delays, the sandbox gate, the scoring verdict — and quote the
documents and the code. The disputes are the documents' words against the
question's premise: the Omega test has no "shadow graphs", the documents name
no "close holes" of the Leech lattice, Lean does not run per payload, a
runtime exception is not scored -1, the gate runs once per reading rather
than per token, and so on.

## 4. Faculty

Under D15 the round moves **addressing** (an answer recovered from the
corpus, by a cue, with its citations checked when read) and **refusal** (a
false premise disputed with the document's words, and `CITATION_MOVED` when
the evidence has gone).

## 5. Limits, and what the round leaves

* **Recognition.** The cues are keyword sets. p92a goes to an earlier frame
  and h92 is not read; a reworded question can fall through.
* **The questions are the declared eighteen.** A question about the machine
  on a nineteenth topic is not read; the frames do not search the corpus for
  an answer they were not given.
* **Quotes are checked, not understood.** A study whose sentence keeps its
  fragment but changes its meaning would still be quoted.

**The verdict, in the body.** Yes for the eighteen declared questions, and with a recognition gap on rewordings. Every one is read by its declared topic and answered with quotes found in the studies at read time, Lean declarations found in the stored address book, and the disputed premises the documents contradict; a moved quote or a renamed theorem turns the reading into the refusal `CITATION_MOVED`. Six of the seven marks were met: the paraphrase mark missed one rewording, which an earlier frame reads and answers correctly, and one held-out rewording is not read at all.

T7 names 10 theorems of the Lean file (`meta_question_cases.LEAN_THEOREMS`).

## 6. What citing studies costs

The router now imports the evidence layer, which names the six studies it
quotes, so every unit that reaches the router holds them. Measured by
`signoff --impact` before and after the round:

| study | units it makes stale, before | after |
|---|---|---|
| `GLM_ACADEMIC_PAPER.md` | 2 | 48 |
| `INTEGER_DECISION_STUDY.md` | 3 | 48 |
| `SYMBOLIC_PARAMETERS_STUDY.md` | 3 | 48 |
| `QUESTION_SET_B_STUDY.md` | 50 | 51 |
| `CARRIED_FORK_STUDY.md` | 53 | 54 |
| `LEAN_ADDRESS_STUDY.md` | 62 | 63 |

The dependency is real — the answers are read from those files — so it is
recorded, not hidden. A stored, digest-checked copy of the quoted sentences,
the way the Lean address book is stored, would take it back out; that is
left as a To-Do line. `test_meta_questions.py` itself stays below the frames
and does not take the whole Lean development; the median cost of one Lean
edit (75) stands at half the any-Lean-file row (150), so the recorded excess
of [`ITERATION_COST_STUDY.md`](ITERATION_COST_STUDY.md) §5k is not used.

## 7. Re-running it

From `overlay/`:

```
PYTHONPATH=. python3 -m glm_universal.tools meta-questions
PYTHONPATH=. python3 -m glm_universal.tools meta-questions --json
PYTHONPATH=. python3 -m pytest -q glm_universal/tests/test_meta_questions.py
```

and `lake build` at the repository root for the Lean file.
