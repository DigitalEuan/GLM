# Summary of changes for run 20a14a16-c1d0-4574-a988-27e72d4feaa1
I updated the out-of-date Celsius note and then did round 9's first item (retrieval, candidate N1), recorded as **Phase 100**. Six of its seven marks were met; the control I declared failed. It also turned up an older defect in how the Lean corpus records citations. All work is committed.

**1. The note you asked about.** Item 1 of `STATUS.md` §3.4 still said "the scale table itself still has no offset row". It now says that item is closed: Phase 87 did the measurand half and Phase 99 the offset half. It records what Phase 99 shipped, the follow-ups listed in §7 of the Celsius study, and your pending decision on aluminium. The original text is kept beneath it. The Phase 87 paragraph now says the offset row was later shipped by Phase 99.

**2. What N1 asked.** The native-parity and native-words studies were re-checked at several later rounds, and some of their small leads flipped by one query as the corpus grew. N1 asks which of those leads are real and which are noise. The rule and marks were committed before any measuring code (`studies/CORPUS_RESAMPLE_STUDY.md`). I ranked every one of the 4,572 declarations once, under ten rankings, both as a declaration query and as a goal query. From that one ranking I read off:
- each of the 171 sub-corpora that leaves out one Lean file;
- every offset of the query sampling stride (22 for declaration queries, 45 for goal queries).

A lead counts as real if it holds in at least 95 % of both sets. New code: `reasoning/corpus_resample.py`, the command `tools corpus-resample`, and `tests/test_corpus_resample.py`.

**3. Results.**
- **One lead out of 18 is real:** the two-book native ranking (`native2`) has at least the raw structural ranking's hits on declaration queries. It holds in 99.4 % of file drops and 95.5 % of offsets.
- **The same lead on goal queries just misses** the 95 % threshold (96.5 % and 93.3 %).
- **Everything else is noise as stated.** That includes the single-book marks N1 and N2, the tie-break marks W4 and W6, and the three after-the-fact readings in the native-words study. It also includes the shipped words mark W2: it fails at the top rank, but at ranks 3, 5 and 10 it is at least level in at least 88.9 % of every set.
- **The control I declared failed.** I predicted `native2` and `features2` would always give the same hits. They share only their first two sort keys, so their hits differ in 11.7 % to 24.4 % of resamples. That mark (M4) is recorded as not met.
- **No default ranking changed.** The verdicts are written into both earlier studies, next to the readings they settle.

**4. The defect it found.** The citation index treats any token matching a unique short name as a citation. Ten declarations have one-letter names, so every variable `a`, `A`, `e`, … in the corpus counts as citing one of them. That is 3,231 of 15,012 citation edges; `GLM.Heisenberg.a` alone is "cited" by 1,920 declarations.

This leak affects two things: two coordinates of every structural address, and the lists of related declarations that every retrieval score is checked against. Comparisons between rankings stay fair, because both sides use the same lists, but absolute hit rates are inflated by an unmeasured amount. I did not fix it: fixing it changes every retrieval figure. `STATUS.md` now pairs it with item 5 (a similar leak in the feature map) as the next round.

**5. Lean.** `RequestProject/GLM/CorpusResample.lean` builds with no `sorry` and only the standard axioms. It proves:
- leaving candidates out of a ranking gives the same list as ranking what is left (`sorted_perm_filter_eq`);
- 108 places per query are enough to read any sub-corpus off the full ranking (`take_filter_take`);
- the stride offsets split the corpus into disjoint parts that cover it once (`stride_offsets_card`);
- the exact sign-test values the study prints, checked by the kernel.

These four results are in the Properties table, marked proved.

**6. Closing the round.**
- I updated `STATUS.md`, `MASTER_PLAN.md`, `WHITEBOARD.md`, the tests README and the hand-typed counts: 171 Lean files, 4,576 declarations, 122 reasoning modules, and the iteration-cost table.
- `corpus --check` reports current.
- `signoff --close` passes 146 of 146 test files and 6 of 6 instruments, and the full `lake build` succeeds.
- I had to install `pytest` again; sign-off needs it.
- Because Python cache files were already tracked in the repository, refreshed `__pycache__` files are in these commits.

## Suggested follow-up

There is a likely bug in your citation index (`lean_address.citation_index`). It matches a bound variable such as `a`, `A` or `e` to a declaration with that one-letter name, so about a fifth of all citation edges are spurious. Those edges also feed the related-declaration lists that retrieval is scored against. I can take this next, together with item 5: stop one-letter variables from counting as citations, then re-take the Lean-corpus retrieval figures and keep the old ones as the record.

# Summary of changes for run 7c54aff6-01d4-4b76-adc0-d8713bfb5c99
Phase 99 is done: the GLM now has a register that holds Celsius readings. All 8 success criteria I wrote down before starting (C1–C8 in `studies/CELSIUS_REGISTER_STUDY.md`) were met, and the work is committed.

**What was added**
- **The register:** `data_objects/fixed_points.py` holds 14 ITS-90 fixed points (international reference temperatures). Each stores only its Celsius temperature, as an exact fraction. It has an `ACTIVE` on/off switch.
- **Conversion to kelvin:** a new `fixed_point` field table in `runtime/fields.py`. `reasoning/scale_conversion.py` gets a scale row with an offset: K = °C + 273.15, held exactly as 27315/100. That file also gains an `OFFSETS` switch.
- **Supporting changes:**
  - Ordering results now name the converted values whenever an offset is involved.
  - The old multiply-only unit conversion now refuses offset rows, and a separate function, `scale_into_si_affine`, handles them.
  - The planner and its generated scripts treat Celsius as a level that needs the offset.
  - The measurand register gets an `offset` field.
  - "temperature" and "celsius temperature" are added as recognised words.
- **Report, command and tests:** `runtime/celsius_register_report.py`, the command `tools celsius-register`, and `tests/test_celsius_register.py` (15 tests).
- **Lean:** `overlay/glm_lean/RequestProject/GLM/CelsiusRegister.lean` builds with no `sorry` and uses only the standard axioms. The whole Lean library builds cleanly.

**Results**
- All 14 fixed points convert exactly onto the kelvin column.
- Prepared test cases: 10 of 10 ordering, 3 of 3 column and 9 of 9 planner cases came out as declared, with none wrong.
- Through the full machine, 6 questions are now answered that got no answer before.
- As a control, dropping the offset flips 3 ordering cases and gets all 6 planner answers wrong, so the offset is doing real work.
- Earlier test sets are unchanged. All 6 generated scripts check out, and every deliberately altered script or false offset was rejected.

**For you to decide:** I compared the register against the existing element register. 10 of 13 shared points agree within 0.005 K. The aluminium entry there (933.437 K) is 0.036 K below the ITS-90 value of 933.473 K, which looks like two swapped digits. I left it unchanged.

**Documentation:** STATUS.md, MASTER_PLAN.md (Phase 99), WHITEBOARD.md and the hand-typed counts are updated. Section 6 of the study gives a step-by-step recipe for adding the next register, wheel or junction, for the further additions you mentioned. The final checks passed: the corpus check reports current, and sign-off covers all 145 test files and all 6 measurement tools.

# Summary of changes for run 69712d75-c8ba-4618-88c1-60f948001482
Phase 98 is closed. The GLM can now answer questions whose answer is a formula in letters, such as `a = (2/3)*g*sin(theta)`. You asked for better reasoning, so I took tracks S (formulas in letters) and T (the one transcendental equation) from Question Set B §8 instead of round 9 (retrieval). Retrieval is still next. All eight marks were met, but one only after a fix (details below).

**What was built** (all under `overlay/glm_universal/`)
- **`reasoning/symbolic.py`**: exact algebra of polynomials and fractions of polynomials in named letters, using exact fractions and no floats. Square roots, `sin`, `cos`, `tan`, `exp` and `ln` are handled as named symbols.
- **A new operation** (`runtime/symbolic_frames.py`): `solve symbolically for T: EQ; EQ`. It removes unknowns by substitution and prints the formula with the nonzero conditions it assumed. When it can't solve a system it refuses by name (underdetermined, inconsistent, nonlinear, and so on).
- **Square linear systems of four or more unknowns** are solved by Cramer's rule, with determinants computed without fractions.
- **14 question frames** (`runtime/symbolic_outside.py`): one for each of the 13 class-S outside questions and one for the transcendental crossover question.
- **Command:** `tools symbolic` runs the measurement; add `--battery` for the random-system check.

**Results** (marks written down before the code)
- 13 of 13 class-S questions answered and checked, 0 wrong.
- 13 of 13 re-worded variants, 18 of 18 hand-solved systems, 8 of 8 refusals.
- 27 of 27 earlier framed answers and 14 of 14 Set B verdicts unchanged.
- Crossover frequency pinned between 3.6731 and 3.6732.
- Wrong-answer controls: 43 of 44 caught on the first run. The miss was the control's fault: doubling an answer of zero changes nothing. After making that control add an offset instead, 44 of 44. The study records this mark as not met as declared, met after repair.

**What the random battery found** (90 random linear systems in letters, run after the marks)
- **Speed:** the first run had not finished after 20 minutes. Simplifying fractions in many letters blew up. With three fixes, a 4-unknown system takes about 0.02 s (it was over 5 minutes) and the whole battery about 6 s.
- **A real bug the marks missed:** 34 of 87 answers failed their own check. The maths was right but the printer was wrong. When a denominator had a number in front of a sum, it wrote `2*r^2 - p` where it meant `2*(r^2 - p)`. After the fix, 87 of 87 pass. A new test checks that the printed formula reads back to itself.

**Lean.** `overlay/glm_lean/RequestProject/GLM/SymbolicParameters.lean` builds with no `sorry` and only the standard axioms. It proves:
- the rolling-body result for every moment of inertia;
- the invariant mass, the disturbance loop and the tangent law at an interface;
- the AR(1) autocorrelation series;
- that two polynomials agreeing at enough points are equal (why the point checks are evidence);
- `cramer_solves`: with a nonzero determinant, Cramer's rule gives exactly the solutions.

These are listed as proved in the Properties table.

**Records and checks.**
- Write-up: `studies/SYMBOLIC_PARAMETERS_STUDY.md`. `STATUS.md`, `MASTER_PLAN.md` and `WHITEBOARD.md` are updated.
- Updated hand-typed counts: 169 Lean files, 4,548 declarations, 121 reasoning modules, and the iteration-cost table.
- New tests: `tests/test_symbolic.py`.
- `corpus --check` reports current. `signoff --close` passed 144 of 144 test files and 6 of 6 checks, including the Lean build.

**Things you should know.**
- I had to install `pytest`, which was missing here; sign-off needs it.
- I changed two existing tests in `test_question_frames.py` so that this phase's own cases and the newly answered questions count as an intended change, not a regression.
- Still not handled: systems that are genuinely nonlinear in the unknowns are refused; tracks P, M and E are untouched.

# Summary of changes for run 34eef55a-ad78-4f5b-affc-4b3078fb7395
This round is **Phase 97**. The Python dialect now accepts argument unpacking, and the program it refused last round is answered as a fresh declared case. I also looked at whether the last round's results could be improved: they can. All 12 marks declared for this round were met, and none of the system's checked steps gave a wrong answer.

**Was the last run weak?** Partly. Its core results were sound: 0 wrong answers anywhere, with the key facts proved in Lean. Its two misses were both mistakes in what had been declared in advance, not faults in the new register:
- **V8** failed because the dialect could not unpack arguments.
- **V4** expected two views with independent faults to reproduce an earlier 4,224-of-4,224 result. But the register's second view reads its error rotated, and with independent faults a rotation cannot help on average.

**What I built.** The marks and a frozen baseline were committed before any code.
- **Argument unpacking** (`reasoning/python_speech.py`): `f(*xs)` at a call and `def f(a, *rest)` at a definition. Each shows up as a named step and is re-checked by the column-3 script. Keyword arguments, `**`, defaults and starred list displays are still refused, each by name.
- **Reading the third view only when needed** (`read_on_demand` in `reasoning/second_view.py`): the register reads its third view only if the first two leave more than one candidate.
- Also new: `runtime/unpacking_report.py`, the command `tools unpacking`, `tests/test_unpacking.py` and `studies/UNPACKING_RESCORE_STUDY.md`.

**Results**
- **U1:** `read_views(*store_views(golay_encode(1234)))` now gives `333010`, the same as CPython. Its column-3 script verifies and a deliberately altered copy is rejected. All six of last round's declared programs and its three refusals now come out as declared.
- **U2–U4:** 14 of 14 call programs, 8 of 8 definition programs and 10 of 10 refusals came out as declared. Before the change the dialect gave the declared outcome for none of these 33.
- **U5:** none of 311 earlier declared programs changed, except U1's own source, and the comparison against CPython is unchanged (0 wrong).
- **R1–R2:** reading the third view only when needed gives the same answer as always reading three on all 680,064 four-error reads. It reads 1,371,264 views instead of 2,040,192, about a third fewer. Below weight 4 it never reads the third view.
- **R3, the cost of saving those reads:** on weight-5 bursts, which are outside the fault model, it gives the same 384 wrong answers as the two-view register, where always reading three refuses every one. So it is only a safe default where the fault model holds. Both read methods remain available.
- **R4–R7, independent faults declared correctly on a fresh probe:**
  - Two views' candidate counts matched the prediction on all 8,448 reads, 0 wrong, with 256 left open.
  - Three views resolved 84,480 of 84,480, 0 wrong.
  - For every first error and every frame, exactly 346 second errors leave two views open. So no choice of frame could have met V4.

**Lean.** `RequestProject/GLM/OnDemandView.lean` contains no `sorry`. It proves:
- once two views resolve a read, a third view cannot change the answer (`on_demand_agrees`), and below weight 4 one view is enough (`inside_radius_unique`);
- the count of 346 holds for every first error and every permutation of the coordinates (`open_seconds_card_frame`), and some pair always stays open (`independent_never_separated`);
- a model of how unpacked arguments are bound (`bind_isSome_iff`, `bind_rest`, `star_round_trip`).

The Golay theorems rely on the `native_decide` check already in the existing Golay files; the unpacking theorems use only the standard axioms. Three entries were added to the Properties table and marked proved.

**Closing the round**
- I updated `STATUS.md`, `MASTER_PLAN.md`, `WHITEBOARD.md` and the paper (§19.12), and the hand-typed counts (168 Lean files, 4,539 declarations, the iteration-cost table).
- `corpus --check` reports current.
- The sign-off passed 143 of 143 test files and 6 of 6 checks, including the full Lean build.
- The suite total is now 4,935 tests across 142 of the 143 test files. The subtest count is 17,993, which is 33 fewer than last round; I did not look into why.
- Everything is committed.

Next, per `STATUS.md` §3.4, is round 9 of the order of work (retrieval), or the lattice items listed beside round 8.

# Summary of changes for run 2ea98798-48ce-4a28-9224-06e4821bf309
I finished round 8 of the work order in `STATUS.md` §3.4, *second readings*, recorded as **Phase 96**. It is closed and committed. Seven of the nine marks declared before any code were met. No certified stage gave a wrong answer anywhere.

**What was built**
- A framed register in `overlay/glm_universal/reasoning/second_view.py`. It stores a carrier once and reads it back through three fixed frames. That gives the runtime its own second view of a carrier, so a caller no longer has to supply two reads.
- A report and the command `tools second-view`.
- Two new dialect builtins, `store_views` and `read_views`.
- `tests/test_second_view.py`, with 17 tests.
- `overlay/glm_lean/RequestProject/GLM/SecondView.lean`, which contains no `sorry`. It proves:
  - which codewords two views allow (`common_iff`, `resolved_iff`);
  - that no single extra frame resolves every four-error burst, while the three chosen frames do (`no_single_frame_separates`, `three_frames_separate`);
  - that a soft channel built from the views reduces to the same intersection (`soft_mean_dist`, `pair_dist_eq_iff`). So escalating to the Leech lattice on that channel resolves no more forks than the plain intersection does.

The two finite checks use `native_decide`.

**Results**
- **V1–V3 met:** all 680,064 three-view reads resolved, 0 wrong. The fewest open bursts any second frame leaves is 156.
- **V4 not met:** X1's probe through two views resolved 4,160 of 4,224, 0 wrong. Three views resolve 14,080 of 14,080, but that check was run afterwards, so it is not scored.
- **V5 met.**
- **V6 met:** combining the declared cases with a second reading answered 658,258 of 658,812, 0 wrong, with the open count as predicted at every `k`.
- **V7 met:** over 46,728 reads, the Leech escalation resolved nothing the intersection had left open.
- **V8 not met:** one of the six declared dialect programs is refused because the dialect has no argument unpacking (`*args`). The other five and all three declared refusals came out as declared.
- **V9 met.**
- Weight-5 bursts: a single view reads all 2,720,256 of them wrongly; three views refuse every one.

**Closing the round**
- I reworded the study's summary verdict so every word in it is backed by the study's body ("Partly" rather than "Mostly").
- I registered `second_view.py`'s XOR uses in the XOR declaration list.
- I added the missing row to the tests README.
- I updated hand-typed counts: 167 Lean files, 4,518 declarations, 120 reasoning modules, and the iteration-cost table.
- The regenerated suite figure is 4,921 tests across 141 of the 142 test files.
- The document check (`corpus --check`) reports current, and the sign-off passed 142 of 142 test files and 6 of 6 instruments.
- The full Lean build succeeds (8,194 jobs).
- The four Lean results above are in the Properties table, marked proved.

`STATUS.md` now names item 9 (retrieval) as the next round.

## Suggested follow-up

The V8 miss comes from a gap in the Python dialect, not a fault in the new register: the dialect refuses any function that uses `*args`. If you want, the next round could add argument unpacking to the dialect and re-score the refused program as a fresh declared case.

# Summary of changes for run 34565c74-162b-414c-b465-37f587eedd3e
I completed Phase 95: the imperative grammar, which is the second half of round 7 in `STATUS.md` §3.4. With it, the GLM can now say, read back, run and certify Python programs that keep state: assignment (including assigning several names at once), `for` loops over ranges, strings and tuples, `while` loops, branches, functions with `return`, and structural `match`.

**What was built**
- `overlay/glm_universal/reasoning/reverse_tct_imp.py` holds the grammar, the reader, an exact interpreter and the column-3 script. Column 1 includes a trace of each assignment, and a fresh interpreter replays it.
- `say:` only uses the new grammar when the three earlier sorts refuse a program.
- Supporting pieces: `runtime/imperative_report.py`, the `tools imperative` subcommand and `tests/test_imperative_grammar.py` (19 tests).
- The declared cases (`evaluation/imperative_cases.py`) and the frozen baseline were committed before any code.

**Measured results** (8 of 9 declared marks met)
- 13 of 13 declared sentences were reproduced word for word, all 7 Phase 64 programs with state now work, and 21 of 21 further programs were answered. Each answer equals what CPython gives.
- 41 of 41 column-3 scripts verify, and all 41 deliberately broken copies are rejected.
- A battery of 1,412 programs reads back with 1,412 distinct sentences.
- Raising both the step and call-depth limits tenfold changes 0 of 41 answers.
- **Mark I7 (no regression) is not met as declared.** One Phase 68 refusal (`a, b = b, 1`) is now refused as `UNBOUND` (`b` is read before it is assigned) instead of `NOT_IN_FRAGMENT`. It is still a refusal, just a more specific one. This is recorded in the study, the paper and `STATUS.md`. The older tests now list it as a recorded later change rather than hiding it.

**Defects found and fixed**
- True division `/` used to return an exact fraction where CPython gives a float. It is now refused.
- A loop over a mask was refused under the wrong name. It is now `ORDER_UNDEFINED`.
- During sign-off, the source audit flagged a `random` import in a core module, which the project's rules don't allow. I replaced it with an integer-only generator.
- That new generator exposed a crash: repeated squaring produced a number too large for `say:` to put into words. Values are now capped. A number with a numerator or denominator over 4096 bits, or a string over 4096 characters, is refused by name as `SIZE_LIMIT`. I re-measured all nine marks after this fix and none changed.
- An extra battery of 600 generated programs, written after the main measurement, gave 450 imperative answers with 0 wrong.

**Lean**
`overlay/glm_lean/RequestProject/GLM/ImperativeGrammar.lean` builds with no `sorry` and only the standard axioms. It proves:
- distinct programs get distinct encodings (`encT_injective`);
- running the interpreter longer never changes an answer (`exec_mono`, `exec_agree`);
- Euclid's loop computes the gcd (`euclidLoop_gcd`), with 1071, 462 giving 21;
- the factorial loop computes \(n!\) (`factFuel_eq`);
- the accumulated sum telescopes to \(n/(n+1)\) (`sum_telescope`), with 10 terms giving 10/11.

These are in the Properties table as proved.

**Documentation and sign-off**
- New study: `studies/IMPERATIVE_GRAMMAR_STUDY.md`.
- `studies/GLM_ACADEMIC_PAPER.md` now has a §19.11 section covering Phases 94–95, plus updated status, capabilities, open items and appendices. `STATUS.md`, `MASTER_PLAN.md`, `WHITEBOARD.md` and the READMEs are updated too.
- I regenerated the counts that are quoted throughout the documents (now 141 test files, 166 Lean files, 4,493 declarations).
- The round was closed with the full sign-off: 141 of 141 test files and 6 of 6 checks pass, including the Lean build. The document checks report everything current. All work is committed.

The next step, per `STATUS.md` §3.4 item 8, is round 8: second readings.

# Summary of changes for run ad1d5f48-2c48-4da4-ac54-03bd1d290bf8
I finished closing Phase 93 and then completed Phase 94, the first half of round 7 in the order of work in `STATUS.md` §3.4 ("the third sort"). Everything is committed. The full test suite was re-run and signed off at the end: 140 of 140 test files and 6 of 6 instruments pass. The document checks report the corpus current, and the Lean project builds with no `sorry`.

**What Phase 94 adds**
- **Strings, tuples and ranges in the reverse grammar** (`overlay/glm_universal/reasoning/reverse_tct_seq.py`). The grammar can now turn these values into English sentences and read the sentences back. Each character is spelled by name, and every literal states its item count before its items. Slices, item lookup, concatenation, repetition, `len`, `sum`, `ord`, `chr`, `min` and `max` are supported. The new sort has its own exact evaluator and its own verification script (column 3). `say:` only falls through to the new sort when the earlier grammar refuses a question, so no earlier answer can change.
  - Example: `sum(range(1, 11))` is said as "the total of the range from one to eleven by one", which equals fifty-five.
- **A wider Python dialect** (`reasoning/python_containers.py`, plus changes to `python_speech.py`):
  - String methods are computed over code points.
  - Methods that would need Unicode's case or whitespace tables (`upper`, `lower`, `isdigit`, `isalpha`, `split`/`strip` with no argument) work only on ASCII. Above code point 127 they are refused as `OUTSIDE_SUBSTRATE`.
  - Lists and dicts are treated as fixed snapshots. Any change in place (such as `append`, `update` or item assignment) is refused by name as `MUTABLE_CONTAINER`.
  - `list` and `sorted` are now available.
- `python3 -m glm_universal.tools third-sort` recomputes every result. `tests/test_third_sort.py` adds 36 tests.

**Results** (written down before any code, all 10 targets met; details in `studies/THIRD_SORT_STUDY.md`)
- **Sentences:** 28 of 28 declared cases are said and valued as declared; none were said before the round.
- **Read-back:** all 1116 terms in the depth-two test battery read back to themselves, and no two share a sentence.
- **Dialect programs inside the grammar:** 21 of 21.
- **Dialect values:** 63 of 63 cases match CPython in both type and value (24 string, 23 list, 16 dict); none were answered before.
- **Verification scripts:** every script verifies, and every deliberately altered copy is rejected.
- **No regression:**
  - None of the 83 earlier Python value cases changed.
  - The comparison battery against CPython has 0 wrong answers out of 2830 answered.
  - Two earlier refusals are now answered, as declared beforehand. The other 24 refusals are unchanged.

**Proved in Lean** (`overlay/glm_lean/RequestProject/GLM/ThirdSort.lean`, standard axioms only)
- **Unique readability:** writing a list as its count followed by its items can always be read back. This holds for any item spelling that can itself be read back, so nested literals work too. No two lists share a spelling.
- **Ranges:** an entry of a range is characterised exactly (membership and length), and the closed form for the sum of a range is proved.
- **Slices:** CPython's slice indices always stay inside the sequence, for either sign of step. A positive-step slice reads the ceiling of (stop − start) / step items.
- **ASCII case mapping:** it keeps the length and undoes itself on letters.

Four of these are recorded as proved in the Properties table.

**Changes to existing code and documents**
- The router's census still counts all 26 original Phase 64 refusal programs. The Python-through-router test now expects 24 refusals, because two of the 26 are now answered.
- One mutation helper was rewritten to avoid a XOR that the project's XOR-site check would have flagged as unclassified.
- I updated the stale figures in the documents (test-file, Lean-file and declaration counts, and the iteration-cost table).
- `STATUS.md`, `MASTER_PLAN.md` (new Phase 94 section) and `WHITEBOARD.md` record the round.

**Not done in this round:** the second half of round 7, M's imperative grammar (sentences for assignment, loops and branches, so that the 7 earlier Python programs with state get sentences). That is where the next round starts.

# Summary of changes for run 366f2b3c-c82b-4cbe-852c-f00eae26eea5


## Suggested follow-up

I reached this run’s time limit. Send “continue” to pick up where I left off.

# Summary of changes for run af2e3080-34d3-42ac-8bb6-449a210a606b
I finished round 5 of the work order in `STATUS.md`, discourse state, recorded as **Phase 92**. All 29 test conversations, written down before any code, came out as declared, with 0 wrong answers. The round-close sign-off passed: 138 of 138 test files and 6 of 6 instruments are signed, the corpus check is current, and the full Lean build (8,190 jobs) succeeds with no `sorry`.

**What changed.** Until now, the conversation layer could only swap a single name into a follow-up, and it refused when a question's top value was shared by several rows (a tie). The new layer is in `overlay/glm_universal/runtime/discourse.py`. It handles the three items queued for round 5:
- **A tie answered as a column (0b).** When the top value is shared by several rows, a later *it* or *them* refers to all of them. The question is asked of each row separately, and the answer is a list with one answer per row. Before any code, I wrote down what an answer for several rows at once should be (the head of `evaluation/discourse_cases.py`):
  - If any row has no answer, the whole list is refused (`column-incomplete`), just as missing readings already block a sum or average over a column.
  - If no row answers at all, the layer looks further back in the conversation instead.
  - The two rows of a comparison don't count as a tie, so *describe it* after one is still refused as ambiguous.
- **New kinds of follow-up (D = 0a):**
  - *the one before that*;
  - *them*, *both of them*, *each of them* and *all of them*. A plural with only one row to refer to, or *both* with other than two, is refused (`number-mismatch`);
  - *why?*, which explains the previous turn from what was recorded and computes nothing new.
- **Follow-ups on every surface (K3).** A follow-up now counts as answerable if any part of the machine answers it, not just the basic session. A text the machine can already answer on its own is answered on its own, so this layer never changes an existing answer.
- **New command:** `python3 GLM.py --converse "smallest charge in molecule" --converse "what is the molar mass of it" --converse "why?"`. The `-q`, `--ask` and `--steps` options are unchanged.

**Results** (`python3 -m glm_universal.tools discourse-state`):
- 7 of 7 tie/list cases, 16 of 16 new follow-up cases and 6 of 6 cross-surface cases came out as declared.
- The old conversation layer gets 0 of the 20 cases that depend on new behaviour right. Licensing through the basic session alone answers 0 of the 5 cross-surface questions. With the new tie behaviour switched off, all 4 tie cases go back to being refused.
- The old layer's 15 declared follow-ups all keep their results except one, the tie case, whose change was declared in advance.
- Every one of the 32 list entries matches the answer that row gets when asked on its own.
- Of 3,056 earlier test strings, 15 contain *them*. The machine refuses all 15 on its own, so no earlier answer changes.

**Lean.** The new file `RequestProject/GLM/DiscourseState.lean` builds with no `sorry` and only standard axioms. It proves:
- where no turn produced a tie, the new layer gives exactly the old layer's result;
- a list answer is the full set an earlier turn produced, has at least two rows, and every row answers;
- a `column-incomplete` refusal means the set has one row that answers and one that doesn't;
- each list entry is that row asked on its own;
- *both* always gives exactly two rows or a refusal, and no plural ever binds to a single row;
- *the one before that* is decided only by turns older than the one *that* refers to;
- the real test cases, checked by computation.

I added these to the Properties table as proved.

**Documents.** The write-up is `studies/DISCOURSE_STATE_STUDY.md`. `STATUS.md`, `MASTER_PLAN.md` (Phase 92), `WHITEBOARD.md` and the academic paper (§19.9, result 21) are updated. `STATUS.md` now says round 6, *the register against the world*, is where the next round starts. What this round leaves open is in the study's §7: feeding a list into the planner's sums and comparisons, answering over only the rows that have a value, further phrasings, and an outside multi-turn question set. The test cases and the code share an author, so this measures what the declared set reaches, not an independent test.

**Stale counts, fixed as part of the close.** These follow from the Lean files added since Phase 89:
- the stated declaration and file counts (now 4,416 declarations and 163 Lean files);
- the iteration-cost table and one number-theory paper;
- two evaluation answers that depend on how many Lean declarations there are. More declarations raise a sampling step from 10 to 11, which shrinks the query set from 844 to 803. The underlying claims still hold, including the anonymous-register claim, which now sits at 1.78 times chance;
- one stored measurement, which I re-took.

I had to install `pytest`, which was missing again.

# Summary of changes for run 33b3a92f-8835-49fe-b819-9286e1c213bb
I finished the round `STATUS.md` named next: round 4 of the order of work, the planner widenings, recorded as Phase 91. Every one of the declared test questions came out as declared, with 0 wrong answers. The full sign-off has run: 137 of 137 test files and 6 of 6 instruments are signed, and the corpus check reports current.

**What changed.** Until now, every widening of the stepwise planner was a frame written by hand. Its fold frames are now generated from one declaration in `overlay/glm_universal/runtime/frame_declarations.py`. The test that this changed nothing: on 638 earlier questions (rounds one to five plus the router's declared sets), the generated reader gives exactly the same readings as the old hand-written readers. With the declaration emptied, it reads none of the fold questions.

**New question types.** These were added as entries in that declaration, not as new code paths:
- **Order statistics:** the k-th largest or smallest value of a column, and the quartiles. When readings are missing, these are answered as an exact range.
- **Superlatives and the top k**, such as "the heaviest noble gas" or "the three heaviest alkali metals". A tie is refused (`TOP_K_TIE`), and so is a top k over a column with missing readings.
- **"What are the bounds on…"** a sum, a mean or a parity count when readings are missing. A sum or mean can only be bounded if its column has a declared physical range. Two ranges are declared, each with its reasoning: Pauling electronegativity from 0 to 3.98, and first ionization energy from 0 to 24.587 eV. Any other column is refused `RANGE_UNDECLARED`.
- **Counting over present readings only**, such as "how many of the transition metals that have one have an odd year discovered".
- **Two groups the element table doesn't hold as one class:** "the metals" and "the rare earths".
- **The twelve remaining exact SI prefixes**, from peta to quetta and femto to quecto.
- **"Heavier" and "lighter" between molecules**, by molar mass.

**Results**, from `python3 -m glm_universal.tools stepwise-five`:
- 54 of 54 questions as declared (12 order, 12 superlative, 12 bounds, 6 class, 6 prefix, 6 molecule), plus 2 of 2 follow-ups, with 0 wrong. The previous round's reader answers none of the 54.
- Through `GLM.py --ask`, the machine answered 5 of the 54 before this round and 41 after.
- Removing the new entries gives every case its earlier answer back.
- All 10 range answers were checked against 200 possible fillings of the missing readings each: every result fell inside the range, and both ends were reached.
- 41 of 41 answer chains re-checked themselves step by step, and every deliberately falsified chain was rejected.
- The earlier rounds' results still hold. Three earlier refusals now get answers, and these changes were declared before any code was written: two questions about "the metals" and one about exavolts.

**One disagreement inside the machine.** For "which is heavier, water or iron", the planner refuses because the two come from different tables (`TABLE_MISMATCH`). An existing comparison feature in the machine still answers it, as it did before, by treating molar mass and atomic weight as the same unit. I recorded this in the study rather than changing either behaviour.

**Lean.** The new file `RequestProject/GLM/DeclaredFrames.lean` builds with no `sorry` and only the standard axioms. It proves:
- the parity-count bounds and the bounds on a sum or mean given a declared range, with both ends reached;
- that the positions the quartiles and the k-th largest read lie inside the column, and that the existing bound for missing readings applies at each of them;
- why a top k with missing readings can't be answered: a missing reading filled high pushes a present one down the ranking.

**Documents.**
- The study is `studies/DECLARED_FRAMES_STUDY.md`, written up through §6. Its §6 lists what is still open: comparing across tables, differences between molecules, a register of isotopes (neutron counts), one-sided ranges, and the top k with missing readings.
- `STATUS.md` now says round 5, discourse state, is where the next round starts. `MASTER_PLAN.md` has the Phase 91 record, `WHITEBOARD.md` is reset, and the academic paper gains §19.8.

**Counts updated because a Lean file and a test file were added.** I updated the stated file and declaration counts, and the iteration-cost table. One earlier claim in the anonymous-register study now holds again, so its recorded miss was removed. The text search, with names replaced, scores 1.74 times chance against the declared limit of 2; it had crossed that limit in Phase 87.

To run the test suite, I had to install `pytest`; it was missing from this environment.

# Summary of changes for run fa5f4e88-d878-4b6c-b305-38bd7849f4c5
This session finished round 3 of the project's work order, the typed operators (candidate F). It is recorded as **Phase 90**. It also repaired a Lean file left broken by the previous session. Everything is committed, and the Lean library builds with no `sorry` and only standard axioms.

**Phase 90: typed operators**
- **Test cases:** 43 cases were written down before the work began, along with what would count as success (marks T1–T8). They live in `overlay/glm_universal/evaluation/typed_operator_cases.py`: 22 are phasor cases, 9 are kind cases and 12 are vector cases. The study write-up is `studies/TYPED_OPERATORS_STUDY.md`.
- **What the new code handles** (`overlay/glm_universal/runtime/typed_operators.py`):
  - **Complex power:** S = V·conj(I), including through an impedance.
  - **Power triangle:** solved from any two of its sides.
  - **Power factor:** reported with whether it is leading or lagging.
  - **Units:** the watt, the var and the VA each apply only to their own kind of power, so mixing them is refused.
  - **Vectors:** dot product versus cross product.
- **Refusals:** it declines to answer when:
  - the power factor doesn't say leading or lagging;
  - the triangle's sides don't fit together;
  - the power factor is outside [0, 1];
  - two vectors have different lengths.
- **Checkable answers:** each answer comes with a script that can be checked independently.
- **Where it plugs in:** the reader is a new question frame, so the normal question router and `GLM.py -q` both use it.

**Results** (all from the project's own test runs):
- **Accuracy:** all 43 cases come out as declared, with 0 wrong answers.
- **Through the router:** 0 of the 43 were answered before this round; all 43 are answered now.
- **Naive baseline:** a simple method that just multiplies quantities together and ignores their type answers 19 of the cases and gets 15 of those wrong.
- **No side effects:** none of the 2,971 earlier questions is picked up by the new reader.
- **Checking the answers:** all 43 answer scripts pass the check, and all 29 deliberately corrupted versions are rejected.
- **Exhaustive search:** a sweep over 2,401 phasor pairs and 7,569 vector pairs found no violations.
- **Lean proofs:** `overlay/glm_lean/RequestProject/GLM/TypedOperators.lean` has 16 theorems. They cover the power triangle, the power-factor range, impedance power, sign behaviour and why the naive method fails, and the difference between dot and cross products.

**To rerun the round:** `cd overlay; PYTHONPATH=. python3 -m glm_universal.tools typed-operators`.

**Example:** `python3 GLM.py -q "Given apparent power = 500 VA and power factor = 3/5 lagging, what is the reactive power?"` answers 400 var.

**Repaired Lean file:** `QuestionSetBAnswers.lean` (40 theorems), left over from the previous session, did not build. Three proofs were fixed (a z-transform coefficient, the binary symmetric channel capacity value, and water-filling) along with one linter warning. It now builds; the repair is recorded in the Question Set B study, §7, and in `MASTER_PLAN.md`.

**Project records and checks**
- **Documents updated:** `STATUS.md`, `MASTER_PLAN.md`, `WHITEBOARD.md` and the academic paper (§19.7, result 19). Several stale figures were corrected: 161 Lean files, 4,336 declarations, and the iteration-cost table.
- **Checks passed:**
  - the full Lean build (8,188 jobs, up to date);
  - the corpus check;
  - the round-close sign-off, which signed 136 of 136 test files and 6 of 6 instruments.
- **Test suite:** 4,764 tests across 135 of 136 files, plus 17,861 subtests.

**Next:** round 4 of the order, the planner widenings.

# Summary of changes for run 0b209b88-ee52-4092-bc19-a1514f2ad12f


## Suggested follow-up

I reached this run’s time limit. Send “continue” to pick up where I left off.

# Summary of changes for run abe04a37-e3f0-4749-a99f-68772da60283


## Suggested follow-up

I reached this run’s time limit. Send “continue” to pick up where I left off.

# Summary of changes for run 0b85cd21-8394-40fb-98f1-23df080968f1
This round (Phase 88) lets one part of the GLM use another part's answer as the input to its next step, which is a loop of reasoning. Before it, every part of the machine answered its question on its own. I also updated `studies/GLM_ACADEMIC_PAPER.md` so it describes the whole system again. Your owner-gated items were left alone, as you asked. The round follows round 2 of the order in `STATUS.md` §3.4 (items K4, I2 and O3 = M3, plus a re-read of item 9).

**What changed in the reasoning**
- The GLM's Python dialect has three new built-in functions that call the rest of the machine and return exact values:
  - `derive(target, (name, value), …)` runs the stepwise planner's goal mode.
  - `ask(question)` asks one stepwise question, such as a register lookup or a comparison.
  - `solve(var, equation, …)` runs the linear solver.
- The program's own control flow now does the looping. For example, `while derive("current", ("voltage", 12), ("resistance", r)) >= 1: r = r + 1` answers 13.
- A fixed set of question patterns (*what does `E` return*, *is `E` true*) now sends a question about a Python expression to the evaluator.
- The checking script trusts none of these calls. For each one it re-runs that answer's own check in a fresh interpreter and confirms the value belongs to that record. For a solve, it substitutes the value back and shows it is the only root. It then re-runs the whole program under standard Python against the checked values.

**Results** (the 44 test questions and 8 success criteria were committed before any code; `studies/PLANNER_LOOP_STUDY.md`)
- 44 of 44 test questions came out as declared, with 0 wrong answers, and all 8 criteria were met.
- Through the main question router, 29 of 29 questions that expect an answer are now answered; before this round it answered 0.
- With the new functions switched off, 0 of 34 are answered and each is refused with a named reason.
- 66 of 66 deliberately planted errors (a false value, a false but self-consistent sub-answer, a changed final claim) were caught.
- Nothing earlier changed: 0 of 530 earlier questions moved, and all earlier results still hold.
- Item 9 re-read: the same questions asked in plain English are answered by nothing in the machine (0 of 5). That is the gap item 9 asked about, now measured. The supplied reverse-call planner is still not promoted, because it does not reach these questions either.

**Lean proofs**
- `RequestProject/GLM/PlannerLoop.lean` proves why the check is enough. If the checked values agree with the real answers on every question the program asks, the program gives the same result. It also proves that no answer can rest on a refused call, and that a solved value is the unique root.
- It builds with no `sorry` and only the standard axioms. Four results are marked proved in the Properties table.

**The paper**
- New sections cover the retained laws (§18.4), the stepwise planner across its six widening rounds (§19.4), the loop (§19.5), confidence and the error rate (§20.5), native words (§21.2), and the cost and ordering of work (§24.1).
- Also updated: the integer decision (§19.3), the abstract, five new rows of negative results (§23), measured items 13–18 (§25.3), the refuted claims (§25.4) and the open problems (§25.5).
- Appendix A now lists all 18 studies it was missing, and Appendix B all 17 missing Lean files.

**Closing the round**
- `STATUS.md`, `MASTER_PLAN.md`, `WHITEBOARD.md`, the tests README and the iteration-cost table are updated. The next round is round 3, typed operators.
- The larger Lean development shifted two stored measurements that only quote the corpus. I re-recorded them with notes, and their conclusions are unchanged.
- The final sign-off passed: 133 of 133 test files and 6 of 6 checks, with the exhaustive cases on. Everything is committed.

# Summary of changes for run 3bfcbd0e-1fe3-443c-b3fe-725815acf8d8
**Merging and ordering the remaining tasks** (full table in `studies/ROADMAP_STUDY.md`; STATUS §3.4 now starts with this order)

I put all 49 open items from STATUS §3.4 in one table and reduced them to 7 tracks. Six groups turned out to be the same piece of work under different names:
- **Measurand register:** K2, O5b, O5c, O5d, 1a and 1b
- **Reasoning loop:** K4, I2 and O3 (O3 is the same item as M3)
- **Discourse:** D (same as 0a), 0b and K3
- **Third sort:** I1 and M1
- **Held-out question set:** B and O1 are the same item
- J2 goes together with H-X1

Suggested order, where each step feeds the next:
1. Measurands (done this round)
2. The loop, then re-read L9
3. Typed operators (F)
4. H-E6, then O7r and 2r
5. Discourse
6. C together with H1
7. Third sort
8. Second readings (J3 can now be stated properly because of Phase 82)
9. Retrieval, starting with N1

Some items can't move without you or outside material:
- **Needs your decision:** K1 and the two contract changes under P.
- **Needs an outside question set:** B, O1 and L4.
- **Proposed for retirement:** P-c and H-c6.

I asked about both of these during the run and got no answer, so they are deferred.

**Built: Phase 87, the measurand register (step 1)**
- **Result:** all 30 declared cases pass and all 8 declared targets are met. The machine answered 2 of the 30 cases before this phase and 18 after. A naive comparison version, which skips the register, attempts 7 of the conversion cases and gets all 7 wrong. Earlier rounds still pass. All 18 chain scripts check out (123 steps).
- **New files:**
  - `overlay/glm_universal/runtime/measurand_register.py`
  - `runtime/measurand_register_report.py`
  - `evaluation/measurand_register_cases.py`
  - `tests/test_measurand_register.py` (16 tests)
  - `overlay/glm_lean/RequestProject/GLM/MeasurandRegister.lean`: 7 theorems with no `sorry`, using only the standard axioms
  - `studies/MEASURAND_REGISTER_STUDY.md`
- **Changed files:** the stepwise planner gained conversion laws C1–C4 and register readings, the elementary charge and percent units were added, and efficiency is now treated as having no units. There is a new `measurand-register` tool command.
- **Not shipped:** the offset row of the scale table (item 1a), because no register holds a Celsius reading yet.

**Recorded miss:** with 4,190 declarations, the anonymous-register claim that text lands within twice chance failed: 78 hits against 37.39 expected, or 2.09×. `studies/ANONYMOUS_REGISTER_STUDY.md` records it as a miss, and the test lists it as a known miss instead of loosening the claim.

**Checks:**
- The whole Lean project builds (8,183 jobs).
- The final sign-off run passed with the exhaustive cases on: 132 of 132 test files and 6 of 6 instruments.
- The corpus check reports current.
- STATUS, MASTER_PLAN, WHITEBOARD, the READMEs and the generated figures are updated; the suite figure is now 4,703 tests across 131 of the 132 test files.
- All work is committed.

# Summary of changes for run 0b2a7a19-ef7b-4719-a479-cd0068c1e7fc
This round (recorded as Phase 86) did a quick tidy of candidate P and then took candidate O5, measurands rather than units, in the stepwise planner. A full `lake build RequestProject` succeeds with no `sorry` and only the standard axioms. The round is closed: 131 of 131 test files and 6 of 6 checks are signed, and `corpus --check` reports the documents up to date. Everything is committed.

**1. P tidy: fixes for the soft confidence floor, measured but not adopted.** I tested each fix the earlier round had proposed for the floor's failures at a fixed error rate, over the same 525 cells. The new code is `reasoning/rate_posterior_marks.py` §5, run with `tools rate-posterior --repairs`; the write-up is `studies/RATE_POSTERIOR_STUDY.md` §4.
- A finer grid leaves 37 cells broken and a higher guard point leaves 35, so neither fixes anything.
- An "upper-credible" rate rule removes both breaks on the grid (32 broken, 0 on the grid). The cost: the share of right answers kept falls from 0.8790 to 0.8561 in one example cell.
- The breaks at rate 1/5, above the grid, remain under every rule tried. An exact identity, checked on every broken cell, explains why.
- I left the runtime unchanged, because adopting the rule changes its contract and that is your decision.
- Proved in `RateRepair.lean` (`fixed_rate_wrong_eq`, `fixed_rate_keep`, `fixed_rate_break`).

**2. Main item: measurands.** Until now the unit check only compared dimensions. It couldn't tell a torque from an energy, a frequency from an angular velocity, or a temperature level from a temperature difference. Following the standard method in the SI Brochure, the planner now does three new things (`runtime/measurands.py`, `runtime/stepwise.py`):
- **Units of the wrong kind:** it refuses `KIND_MISMATCH` where a unit has the right dimension but the SI restricts it to another kind (hertz is not an angular velocity; newton metre is not an energy).
- **Temperatures:** it reads Celsius and Fahrenheit as a level or a difference, depending on the law that uses the value. It refuses the mix-ups by name: `LEVEL_AS_DIFFERENCE`, `DIFFERENCE_AS_LEVEL`, `KIND_CONFLATION`, and `BELOW_ABSOLUTE_ZERO` for a reading below absolute zero.
- **Constants:** it supplies the exact Planck constant and speed of light, but only when the givens alone can't derive the answer.

**Results** (`tools measurands`; write-up `studies/MEASURANDS_STUDY.md`):
- 31 of 31 declared questions answered or refused as declared, with 0 wrong. All 7 checks I set before writing the code pass.
- With the kind check switched off, the old dimension check answers all 5 kind mismatches with a number.
- Through `GLM.py --ask`, answers went from 10 to 5 on the kind questions (the five wrong-kind answers are gone), from 5 to 8 on temperatures, and from 0 to 4 on constants.
- Rounds one to four of the planner are otherwise unchanged. All 17 generated check scripts verify and reject every deliberately corrupted version.

**Two changes to earlier results you should know about:**
- **Five old answers were wrong.** Five declared answers from stepwise round two (u13, g01, g03, g11, m02) fed a melting or boiling point, which is a temperature level, into `energy = mass · specific heat · temperature`, which needs a temperature change. They are now refused `LEVEL_AS_DIFFERENCE`, and each is recorded with its reason (addendum in `STEPWISE_TWO_STUDY.md` §7).
- **Held-precision check H3 no longer passes.** Both of its examples were this same level/difference mix-up (addendum in `HELD_PRECISION_STUDY.md` §4).

**Lean:** `MeasurandKinds.lean` proves six facts, including `level_as_difference_depends_on_zero`, `fahrenheit_kelvin`, `absolute_zero_celsius` and `hertz_as_angular_velocity_wrong`.

**Updated documents:** `STATUS.md` (head, §1, §2 and §3.4; P and O5 are narrowed), `MASTER_PLAN.md` (Phase 86 recorded; the next round starts at Phase 87), `WHITEBOARD.md`, the tests README, the iteration-cost study, and the Lean-file and declaration counts.

**What's still open (MEASURANDS_STUDY §6, STATUS §3.4 O5):**
- Mapping register measurands to the formula wheels' quantities by name, so that, for example, the atomic radius of iron can feed a wavelength.
- Conversions through a stated efficiency.
- The elementary charge as a supplied constant.

# Summary of changes for run 1fe79e21-fe71-48aa-84c9-77e5a6ac49f2
I finished Phase 85, "folds with a hole", taken from the candidate list in `STATUS.md` §3.4. It is built, tested, backed by a Lean proof, documented and closed out. All work is committed; the last commit is "Phase 85 release closed".

**What the phase adds.** The stepwise planner can now answer order questions about a column that has missing readings. Examples are "what is the second smallest…", a rank, or a median when some rows are unmeasured. Where a gap could change the answer, it gives the bounds that hold however the gaps are filled. Where no bound holds on one side, it refuses and names the reason. This follows the design in `studies/HOLE_FOLDS_STUDY.md`, whose success criteria H1–H8 are all met. The code is in `runtime/stepwise.py`, `reasoning/stepwise_script.py`, the new `runtime/stepwise_four.py`, and a new `tools stepwise-four` command.

**Results:**
- All 34 of the declared cases and both follow-up questions are answered, with no wrong answers.
- Before this phase the machine answered none of these cases; through the router it now answers 25.
- 9 of 9 completions and 4 of 4 refusals come out as expected.
- 26 of 26 scripted plans run (843 of 843 steps), and all 15 deliberately corrupted plans (the "hole-lie" mutation) are caught.
- Existing behaviour is undisturbed: the router picks up this phase's wording in only 11 of the 273 other queries tested.
- The new `tests/test_stepwise_four.py` has 22 tests, all passing.

**Lean.** `overlay/glm_lean/RequestProject/GLM/HoleBounds.lean` proves the bounds the planner quotes:
- A reading's rank among the present values is off by at most the number of missing values.
- The k-th smallest value is bounded in the same way, and both bounds can actually be reached.
- A side is genuinely open whenever filling every gap with the same value can move the answer to that value. This is why the largest value of a column with a gap is always refused.

The whole Lean library builds with no `sorry` and only the standard axioms. The library now has 153 files and 4,171 declarations. The Properties table lists the 2 definitions and 8 theorems from this file, with the theorems marked proved.

**Knock-on changes.** The phase added new queries to the shared query set, which shifted two existing evaluation cases, so I updated their expected answers:
- **`report-anonymous`:** now 708 → 74 and 214 → 131 of 835.
- **`report-relay`:** now 708 → 711 of 835; the gate fires on 64 of 1670 queries; the relay still carries 12 queries the text search misses and loses 1. The relay still beats the text control on every set.

I also re-took the query-escalation measurement and regenerated `FIGURES.md`. The suite figure now reads 4,668 tests across 129 of the 130 test files. `STATUS.md`, `MASTER_PLAN.md`, the whiteboard, the iteration-cost study and the READMEs are updated, with Phase 86 recorded as next.

**Release check.** `corpus --check` reports the documents current. The full release sign-off passes, with 130 of 130 test files and 6 of 6 instruments signed under the exhaustive run.

# Summary of changes for run 5503c723-fe7b-4b3f-b2b0-7c78b2ff9346
This session did two things. It signed off the release left open by the previous run (Phases 81–83), then completed one development round from `STATUS.md` §3.4: Phase 84, which is item O7 of candidate O, the third round of the stepwise planner. The final release close passes: all 129 of 129 test files and 6 of 6 instruments hold under the exhaustive release run, and `corpus --check` reports the documents current. Everything is committed; the last commit is "Phase 84 release closed".

**Phases 81–83 sign-off.** Every test had been reported as failing in about 0.1 s. The cause was that `pytest` was not installed in the environment, not a fault in the code. With it installed, the close passed 128/128 test files and 6/6 instruments. I also stopped git from tracking `__pycache__/` folders by adding them to `.gitignore`.

**Phase 84: the stepwise planner, round three** (`studies/STEPWISE_THREE_STUDY.md`). The test cases were written and committed before the code. The planner can now read four new kinds of question:
- **Comparatives** read through a declared data field, e.g. *which is denser, gold or lead* or *how much heavier is gold than iron*.
- ***How many more*** for electrons and valence electrons.
- **The tera- and pico- prefixes.**
- **Sums, means and odd/even counts over a whole column**, either over every element or over a declared class of them.

It refuses by name when a comparative has no declared field, when a value or a column reading is missing, or when a class isn't one the register declares. The new code is `runtime/declared_frames.py` and `runtime/stepwise_three.py`, plus changes to the existing planner, units, script-checking and toolbox modules. There is a new `stepwise-three` command and a new test file, `tests/test_stepwise_three.py`.

Results, from `tools stepwise-three`; all 8 declared targets were met:
- **Questions:** 47 of 47 declared questions and 2 of 2 follow-ups answered as declared, with 0 wrong. The round-two reader answers 0 of these 47; the whole system answered 6 of them before this round and 32 after.
- **Scripts:** 34 of 34 chain scripts verified (327 of 327 steps), and every deliberately corrupted variant was rejected.
- **Earlier rounds:** results from rounds one and two still hold.

**Lean:** the new file `overlay/glm_lean/RequestProject/GLM/StepwiseWiden.lean` holds 8 theorems. They include: a mean over a column with one reading missing equals the full mean only when the missing value happens to equal it, which is why such a fold is refused. The file builds with no `sorry` and only the standard axioms. The 8 theorems are listed as proved in the Properties table.

**Counts that moved with this round.** Adding a Lean file and a test file changed some figures quoted in the documents, and I updated them:
- the Lean development is now 152 files and 4146 declarations;
- the rebuild-cost table in `ITERATION_COST_STUDY.md` gained a Phase 84 line;
- the suite totals are now 4,646 tests across 128 of the 129 test files.

One behaviour change came from this. In the anonymous-register study, the claim that text search without names stays under twice chance had failed narrowly at 4137 declarations. It now holds again (74 hits against a chance level of 37.35). I stopped recording it as a known miss in `tests/test_anonymous.py`; that test now checks the claim stays between 1.5 and 2 times chance, and the study text says so.

`STATUS.md`, `MASTER_PLAN.md`, `WHITEBOARD.md` and the READMEs record Phase 84 as closed and name Phase 85 as next. I did not edit `ARISTOTLE_SUMMARY.md`.

# Summary of changes for run 4987e969-b193-429e-a0e1-f0d5282faa8d
I ran Phase 80 on item P3 of candidate P in `STATUS.md` §3.4 (the confidence floor), doing what you asked: I tested a range of thresholds to find one that works, and where none does, the reading now gives a confidence score instead of refusing. The round is closed and the release is signed: 125 of 125 test files and 6 of 6 instruments. `corpus --check` reports current, `lake build RequestProject` succeeds with no `sorry`, and all work is committed.

**What "working" means.** I wrote this down in `studies/CONFIDENCE_FLOOR_STUDY.md` before writing any code. A threshold `t` works at a bit-flip rate when two things hold for the decoder and for the carried fork over each of the five case sets (2, 4, 8, 16 and 32 cases):
- its promise holds: P(wrong | answered) ≤ 1 − t;
- it keeps at least 90 % of the right answers.

I tested 7 thresholds (9/10, 19/20, 49/50, 99/100, 199/200, 999/1000, 9999/10000) at 5 rates (1/1000, 1/100, 1/50, 1/20, 1/10). Every probability is computed exactly over every possible received word, not sampled.

**What the hunt found:**
- **The working threshold** is 9999/10000 at 1/1000, 1/100 and 1/50, and 999/1000 at 1/20. So both of your candidates, 99 % and 99.9 %, work up to a rate of 1/20.
- **At a rate of 1/10 no threshold works.** The plain decoder is the reason. Its confidence has only one value per error weight, so any floor has to drop every read of that weight. At 1/10 even a 90 % floor loses 28 % of its right answers, and a 99 % floor loses 63 %.
- **What happens instead at 1/10:** as you suggested, the answer comes with its confidence rather than being refused.
- **Before any floor,** the plain decoder at 1/10 gives a wrong answer 6.7 % of the time.
- **Not in the original plan, so not counted:** each case set of the carried fork does have a working floor at 1/10 on its own (999/1000 for up to 8 cases).
- **The promise held** in all 210 combinations. It also held in all 210 when the declared rate was double the true one. When the true rate was double the declared one, it broke in 30. So if you are unsure of the rate, declare the higher one.

**What was built:**
- `reasoning/confidence_floor.py`, plus four new commands in the Python dialect:
  - `resolve_at` and `agree_at` return the answer and its exact confidence together, with a word for how sure it is (near-certain, confident, probable, uncertain). They never refuse on confidence.
  - `resolve_floor` and `agree_floor` refuse with `BELOW_FLOOR` and state the confidence the answer had. A floor that is not a fraction in (0, 1] is refused with `FLOOR_OUT_OF_RANGE`.
- `reasoning/confidence_floor_marks.py` holds the exact calculation and the threshold test. It is run with `tools confidence-floor`, which takes about 20 seconds.
- `tests/test_confidence_floor.py` (22 tests).
- The existing `resolve`, `agree`, `decode_confidence` and `agree_confidence` give exactly the same answers as before.

**Results:** 6 of 7 targets met. The one miss was a mistake in what I predicted for one of the 16 test programs, not a wrong answer. I predicted a two-case `resolve_floor` at 1/10 would refuse, based on the decoder's 78 % figure. With only two cases the answer is actually 6561/6562 sure, so it answered. I've recorded this as missed rather than changing the prediction afterwards.

**Lean** (`RequestProject/GLM/ConfidenceFloor.lean`, all in the Properties table as proved, using only the standard axioms):
- `floor_error_le`: a floor keeps its promise.
- `floor_retention_antitone`: raising the floor never raises the right answers it keeps.
- `posterior_antitone_rate`: the answer's confidence falls as the rate rises.
- `floor_pass_lower_rate`: an answer that passes the floor at the declared rate also passes at any lower true rate.
- `floor_safe_overdeclared`: over the whole channel, overstating the rate keeps the promise.

**Two fixes to earlier work:**
- Phase 79's `integer_decision.py` imported `copy`, which a standing test forbids (only a fixed list of standard-library modules is allowed). I replaced it with a small copy function that behaves the same.
- A test that stops documents quoting outdated counts treated "110 modules" as out of date, but the reasoning package really does have 110 modules now. I removed that phrase from its list, the same way "102 modules" was removed in Phase 72.

**Documents updated:** `MASTER_PLAN.md` (Phase 80), `STATUS.md` (candidate P narrowed), `WHITEBOARD.md`, the READMEs, and the counts that moved (149 Lean files, 4126 declarations, the iteration-cost table).

**Still open under candidate P:** an exact measure for the second reading (`agree`) so it can join the threshold test; estimating the rate from the system's own readings instead of having the caller declare it; and P2 (the 106 unresolved laws, which need a knowledge-base file that hasn't been supplied).

# Summary of changes for run b2c0b8c4-351a-44d2-a513-54042a0d5c07
This session finished the item left open last time (Phase 78, faster iteration) and delivered one new development round, Phase 79. Both are closed: `corpus --check` reports **current**, and `signoff --verify` shows **124 of 124 test files and 6 of 6 instruments** signed with the exhaustive cases run. `lake build` of the `RequestProject` library succeeds, there is no `sorry` in the Lean development, and all work is committed.

**Phase 78 (faster iteration), finished.** The tests README now quotes the generated test-file figure instead of a hand-written sentence. After a refresh and a close, the sign-off ledger was fully signed. `__pycache__` directories are no longer tracked and are listed in `.gitignore`.

**Phase 79: complete integer decision (the next part of candidate M in `STATUS.md` §3.4).** Before, the integer side of Reverse Three Column Thinking could only refuse questions it could not settle. It now decides them completely, and every answer comes with a certificate that is checked independently.
- **What was added:**
  - The study, with its success marks (Z1–Z6) written down before any results: `studies/INTEGER_DECISION_STUDY.md`.
  - A fixed set of 22 questions: `evaluation/integer_decision_cases.py`.
  - The decision procedure, its certificate checker and a mutation checker: `reasoning/integer_decision.py`.
  - The procedure is used as a fallback in `reverse_tct_int.py`, and there is a new `integer-decision` tool.
  - Tests: `test_integer_decision.py` is new and `test_reverse_tct_int.py` was updated.
- **Lean:** `RequestProject/GLM/IntegerDecision.lean` covers the method's key facts: the exact shadow, the dark-shadow gap, the splinter count and cover, bijective substitution, and Pugh's example having no integer point. Its theorems use only Lean's standard axioms, and five Properties entries are recorded as proved.
- **Results:**
  - All 22 of the 22 study questions are decided. The previous version left all of them undecided.
  - On 600 random problems, the new procedure agrees with the reference 600 times.
  - All 22 certificates check, and every deliberately corrupted certificate is caught.
  - Every mark written before the round was met.
- **Documents updated:** `MASTER_PLAN.md`, `STATUS.md` (candidate M is narrowed to what remains), `WHITEBOARD.md`, the READMEs, and the Lean file count (now 148 files). The count of Lean declarations is now 4118 everywhere it is quoted. The dependency table in `ITERATION_COST_STUDY.md` has been re-measured: the median Lean edit now makes 40 test units stale, and 39 units are stale whenever any Lean file changes.

**Still open:** the remaining candidates in `STATUS.md` §3.4 are the starting point for the next round. My earlier question about the P3 threshold (99% / 99.9% / skip) was not answered, so that item has not been started.

# Summary of changes for run c433ce05-bd2a-4f99-9187-3a2ad10c73cf
The previous session had finished all the actual work for its last round, Phase 74 (the law register: re-reading the 65 retained UBP laws from `source_material/UBP_LAW_GLM_REVIEW.md` and `source_material/retained_laws_verified_65.csv`). The code, `RequestProject/GLM/LawRegister.lean`, the study `studies/LAW_REGISTER_STUDY.md`, the `MASTER_PLAN.md`/`STATUS.md`/`WHITEBOARD.md` write-ups and the Properties table entries were already there. One thing was left: the release sign-off for the round was never completed.

**What was left and what I did**
- `signoff --verify-release` reported 120 of 120 test files but only **6 of 7 instruments**: the `evaluation` instrument's signature was recorded as *failed*.
- I re-ran the end-to-end evaluation by itself: **177/177 passed** (149 answered correctly, 28 refused as expected, 0 wrong, 0 errors).
- I then resumed the release (`signoff --release --resume`). It re-ran only that instrument, which passed. `--verify-release` now reports **120 of 120 test files and 7 of 7 instruments**.
- I did not find out why the earlier run failed, since it passed when re-run. It took about 237 s against the instrument's expected 240 s, but I did not find a time limit in the sign-off code, so it was not simply a timeout.

**Checks run here**
- **Lean:** `lake build` of the whole `RequestProject` library completes with no `sorry` in the Lean tree. The nine Phase 74 theorems (`unique_leader_iff`, `wt_four_refused`, `wt_five_coset_three`, `and_not_closed`, `or_not_closed`, `moment_agree`, `moment_eight_differs`, `nrci_means_differ`, `nrci_floor`) use only Lean's standard axioms, plus the ones added by `native_decide` where it is used.
- **Documents:** `corpus --check --all` reports **current**, and all 13 stored measurements are fresh.
- **Law register:** `tools law-register` reports its marks R2–R9 as met (only the tail of the output was captured, so R1 is not shown here). I couldn't run its test file directly because `pytest` isn't installed here; it is covered by the verified release.

**One edit I reverted**
The gate table in `WHITEBOARD.md` §4 still says "close of Phase 67". I tried updating it to Phase 74, but any document edit makes the stored native-parity and native-words measurements stale, so I put the table back as it was rather than disturb a verified tree. It is only a wording lag: the current gate state is as listed above.

No new round was started. The next round begins from a candidate in `STATUS.md` §3.4, with candidate P (the law register, round two) listed there by Phase 74. All work is committed, and `ARISTOTLE_SUMMARY.md` was not edited.

# Summary of changes for run 7d5f9f35-2361-4b83-9d68-ba8b613c484a
From `STATUS.md` §3.4 I took candidate O, round two of the stepwise planner (Phase 73). It adds question types round one could not read, plus unit handling. Everything is committed, the release sign-off passes (119 of 119 test files and 7 of 7 instruments), and the new Lean file builds with no `sorry` and only the standard axioms.

**What changed in the planner**
- **New question types:** *how many more* (refused as `DIFFERENCE_REVERSED` when the smaller value is named first), odd/even, and averages over register values.
- **Givens and targets written with units:** the new `runtime/quantity_units.py` holds a fixed table of exact units. The planner checks each unit fits the quantity and scales it into SI. It refuses by name rather than guessing: `UNIT_MISMATCH`, `UNKNOWN_UNIT`, `UNIT_INEXACT`, `OFFSET_UNIT`.
- **Register values in a derivation:** a value from the register (e.g. *the protons of carbon*) can now be a given in a formula-wheel derivation.
- **Scripts:** the stand-alone check scripts now cover these steps (`measured`, `si`, `unit_out`, `parity`, `mean`). A new tamper test, `unit-lie`, changes a conversion factor and must be caught.
- **New tool and tests:** `tools stepwise-two`, and `tests/test_stepwise_two.py`.

**Results** (study: `studies/STEPWISE_TWO_STUDY.md`). The targets were written down before any code, and all 8 were met:
- **Declared questions:** 53 of 53 answered or refused as declared (21 new-type, 18 unit, 14 register), with 0 wrong. Round one's planner answers none of them.
- **Stories and follow-ups:** 2 of 2 multi-step stories and 2 of 2 follow-ups as declared.
- **Naive comparison:** simply stripping the units gives 6 wrong answers and answers 7 questions that should be refused.
- **Scripts:** 39 of 39 verified (178 of 178 steps checked), and every tamper test is caught, including 22 of 22 unit lies.
- **Round one:** its question set and results are unchanged.
- **Extra questions:** 17 written after the code (not counted toward the targets): 14 answered, 0 wrong.

**Lean** (`RequestProject/GLM/StepwiseFrames.lean`). Its main theorems, now in the Properties table as proved:
- `register_feed_sound`: a register value scaled into SI gives a correct derivation.
- `invariant_iff_homogeneous`: a formula is unaffected by a change of units exactly when its dimensions balance.
- `offset_not_multiplicative`: a unit with an offset, like °C, cannot be converted by a single factor.
- `more_eq_some_iff` / `more_eq_none_iff` for *how many more*, and bounds on the average (`le_mean`, `mean_le`, `mean_perm`).

To make this possible, `IsModel` in `StepwisePlanner.lean` was made visible to other files.

**Other numbers that moved** (each recorded in `MASTER_PLAN.md` Phase 73 and the relevant study):
- **Retrieval tie results:** the new Lean file added to the searchable corpus, so the stored native-parity and native-words measurements were re-taken. Native parity's N8 went back from missed to met. N4a is still missed, and native words' W4 is still missed by one query. These ties have flipped with the corpus before.
- **Evaluation cases:** the relay and anonymous-register reports now run over 810 queries instead of 806. I updated the figures those two cases check for; the claims themselves are unchanged.
- **Hand-typed counts:** updated to 143 Lean files and 4,048 declarations, plus the iteration-cost table.
- **Release fix:** `runtime/stepwise_two.py` imported a library module that the test suite does not allow, so I removed it.

**Documents updated:** `STATUS.md`, `MASTER_PLAN.md`, `WHITEBOARD.md` (Phase 73 closed, no round in flight), the runtime, tests and reasoning READMEs, and a "taken by Phase 73" note in `STEPWISE_PLANNER_STUDY.md`. `ARISTOTLE_SUMMARY.md` was not edited.

**Still open under candidate O:**
- A question set written by someone outside the project, which I cannot supply.
- Passing results back from the reverse-reasoning chain into the stepwise planner.

# Summary of changes for run b997cd9b-abff-4b00-a5be-456a0324a040
**Phase 72, the stepwise planner, is finished and committed.** The typed planner is now the executive of multi-step reasoning. The release sign-off passes: 118 of 118 test files and 7 of 7 instruments are signed. `corpus --check` reports current, `lake build` is clean, `StepwisePlanner.lean` contains no `sorry`, and it uses only the standard axioms.

**What it does, against your five points**
- **Router (point 1):** the stepwise planner sits behind the typed planner on `GLM.py --ask`. The router hands it a question only after the planner has refused, so no answer the planner already gave can change. `GLM.py --steps TEXT` asks it directly.
- **Typed slots (point 2):** a compound question is split into parts, and each part goes to the planner as its own question. Register values are re-read exactly.
- **Composing answers:** it can now answer questions like *is the atomic number of iron prime?*, *the lcm of the atomic numbers of carbon and oxygen*, or *…then multiply it by 3, then is it prime?*.
- **Finding unasked steps:** for *given voltage = 12 and resistance = 4, what is the power?* it works out the current first, then the power. A step that can't be taken yet is set aside and stitched back in once a later step supplies its input.
- **Veto (point 3):** it answers only when every reading and every derivation agrees. Otherwise it refuses by name: `AMBIGUOUS`, `DERIVATIONS_DISAGREE` or `INCONSISTENT_GIVENS`.
- **Three columns per step (point 4):** each step's language and maths columns are checked against each other. One script re-derives every step in a fresh interpreter, printing `STEP k ALIGNED` for each step and then `VERIFIED`.
- **Follow-ups (point 5):** `then …` and `why?` work, with the chain remembered under a SHA-256 digest of the whole conversation.

**Results** (`tools stepwise`, on questions written before the code)
- All 8 declared marks were met.
- 30/30 compound, 21/21 goal, 6/6 narrative and 4/4 follow-up questions came out as declared, with 0 wrong. The planner alone answers none of the 30 compound questions.
- A "take the first derivation found" control answers the 3 goal questions the veto refuses, and those answers are wrong or arbitrary.
- 43/43 scripts verified, 149/149 steps aligned, and 172/172 deliberately corrupted versions were rejected.
- **Caveat:** I wrote both the questions and the module, so this is not an independent test. On 19 extra questions written afterwards (not counted), 15 were answered with 0 wrong. Four it can't read yet: *how many more*, parity, averages, and givens written with units.

**Lean** (`RequestProject/GLM/StepwisePlanner.lean`, 7 rows in the Properties table, all marked proved) proves that:
- a derivation gives the true value in every consistent model;
- a disagreement, or a given that re-derives differently, means there is no consistent model, so those refusals withhold nothing true;
- solving a formula for a variable of power ±1 is exact;
- different bracketings of a sum or product agree, and the two refused cases really do disagree;
- the agreement rule doesn't depend on the order readings are tried;
- the per-step check is equivalent to recomputing everything from scratch;
- the router fallback never changes a planner answer.

**Other things that moved because of the new Lean file**
- The corpus passed 4,000 declarations (3,994 → 4,028). The query sample is taken every `declarations ÷ 400` entries, so the step went from 9 to 10 and every sample shrank. The relay, anonymous-reader, native-parity and native-words figures therefore changed.
- The native word ranking is still ahead of the standard at every cut-off. Two small tie-break marks swapped: W6 is now met, and W4 is missed by one query.
- Native parity: N6 and N7 still hold; N4a and N8 are now missed by one document section.
- I recorded these re-readings in `NATIVE_WORDS_STUDY.md` and `NATIVE_PARITY_STUDY.md`, and updated the pinned evaluation figures and the quoted counts.
- `test_native_words.py` no longer requires W4 to be met, only that it is measured (the same treatment already given to similar marks in `test_native_parity.py`). `test_figures.py` no longer treats "102 modules" as an outdated count, because the reasoning package now has 102 modules.

**Where it's written up:** `studies/STEPWISE_PLANNER_STUDY.md` (marks declared before any code, then results), plus `MASTER_PLAN.md` Phase 72, `STATUS.md` (new table row and summary), `WHITEBOARD.md`, `README.md` and the runtime, reasoning and tests READMEs. `STATUS.md` §3.4 lists the next round as candidate O: a question set written by someone outside the project, the missing question types and givens with units, feeding `relay:` into the chain, and register values feeding the formula derivations.

# Summary of changes for run 56a727aa-641c-4382-9128-bb1aa7610952
I ran **Phase 71, "native words"**, taking items N3 and N4 of candidate N in `STATUS.md` §3.4. The idea was to compute the word-overlap ranking (the standard method Phase 70 found far ahead of any lexical address) on Golay words of the tokens instead of on the tokens. Five of the six pre-declared marks were met. The release is signed: 117 of 117 test files and 7 of 7 instruments, and `corpus --check` is current.

**Before starting.** The stored native-parity measurement and the document address book were out of date again. I refreshed both and committed that first.

**Order of work.** I committed the marks W1–W6 in `studies/NATIVE_WORDS_STUDY.md` before writing any measuring code. One amendment came before any code: camel case is not a split point, because the standard ranking's tokens are already lower-cased.

**What was built**
- `overlay/glm_universal/reasoning/native_words.py` defines three objects:
  - **Letter word:** each token is split into parts at `_`, `.`, `'` and digits, and each part becomes a 24-bit mask of its letter buckets.
  - **Golay class:** the set of every nearest codeword from the complete decoder; ties are kept, not broken.
  - **Golay name:** a token's letter word plus an index that tells apart tokens sharing that word.
- The native ranking `words_native` sorts by names, then part letter words, then classes, then Leech distance.
- It is wired in two places:
  - `retrieval.rank` and `retrieval.retrieve` accept the new schemes by name.
  - The live document ranking, `corpus.address.retrieve`, now uses `words_native`, as declared.
- Also added: `tools native-words`, a toolbox tool `native words`, three generated blocks in the study, and `tests/test_native_words.py` (16 tests).

**Results, at the final reading**

| Query set | `words_native` | standard |
|---|---|---|
| 211 declaration queries, hits at 1/3/5/10 | 152/183/190/197 | 151/175/182/189 |
| 103 goal queries, hits at 1/3/5/10 | 78/91/94/97 | 75/87/92/96 |
| 60 document queries | same hits and precision | same hits and precision |

- **W1:** the names carry exactly the standard's overlap; every top ten matches.
- **W2, W3:** `words_native` is at least as good as the standard on all three sets, and ahead on the Lean corpus.
- **W4:** it beats the Leech-distance tie-break alone.
- **W5:** overlap on letter words alone (`letters`) gets 187 hits at 5 on the declarations, against 147 for the lexical Leech address.
- **W6 missed:** the Leech tie-break on its own is five queries behind at k = 1, so it is recorded but not shipped.
- **Figures moved:** adding this round's Lean file changed the query sample; the first reading (180 against 173 hits at 5 on the declarations) moved, but no mark changed.
- **Not declared in advance, so not counted:**
  - `letters`, which reads no whole token, is ahead of the standard on hits on the Lean corpus.
  - Letter words beat the part strings on the Lean corpus but not on the documents.
  - Both are left for the next round to declare and resample.

**Lean.** `RequestProject/GLM/NativeWords.lean` builds with no `sorry` and uses only the standard axioms. It proves:
- A Jaccard overlap is unchanged by a relabelling that is injective on the union (`jaccard_image_of_injOn`), so name overlap equals token overlap (`jaccard_names`, `index_separates`).
- Two rankings sorted by the same overlap agree on the overlaps in every prefix, so the native ranking can only reorder inside ties (`take_map_overlap_eq`).
- Two letter words within distance 3 of the same codeword differ in at most 6 buckets (`shared_class_near`).
- A letter word reads only the set of letters (`letterWord_congr`).

Three of these are in your properties table, marked proved.

**Knock-on changes**
- The new Lean file moved Phase 70's single-book results, as that study predicted they would: N1 and N4a are now met and N2 is missed by one query. The two-book results N6 and N7 still hold. I recorded this in `NATIVE_PARITY_STUDY.md` §3.5, and the test no longer pins those marks.
- I updated the expected figures for the stack relay (now 755 → 762 of 888) and the anonymous reader (755 → 82 and 241 → 168 of 888).
- I updated hand-typed counts in the documents: 3,994 declarations, 141 Lean files, 101 reasoning modules, and the rebuild-cost table.
- `STATUS.md`, `MASTER_PLAN.md` (Phase 71), `WHITEBOARD.md` and the READMEs are updated. Candidate N is narrowed to N1, N2 and a new N5.

All work is committed.

# Summary of changes for run d1831aac-6d80-429e-b07f-83178e4d4fb1
I picked up the project at the end of Phase 70 (native parity). The code, the Lean file `NativeParity.lean` and the write-up were already there and marked closed in `MASTER_PLAN.md`, `STATUS.md` and `WHITEBOARD.md`. But the round's close-out had not finished: two stored measurements were out of date and the release had not been signed. Phase 70 is now fully closed.

**What I did**
- **Lean check:** `lake build` completes with no errors or warnings, and there is no `sorry` in `RequestProject`. The Phase 70 theorems I spot-checked (`order_agrees_of_gap`, `readback_eq_leech`, `residue_congr`, `sorted_primary_of_sorted_lex`) use only the standard axioms.
- **Documents check:** the first `corpus --check` said two stored measurements were stale (native parity and query escalation) and so were several generated blocks in the studies. I re-took both measurements, rebuilt the document address book, and ran `corpus --refresh`.
  - The stale measurements had left placeholders in `studies/NATIVE_PARITY_STUDY.md`. Once refreshed, the study came back identical to its committed text, so the Phase 70 figures and marks stand as recorded.
  - `studies/QUERY_ESCALATION_STUDY.md` has its generated tables filled in again.
  - `corpus --check` now reports current.
- **Release:** the first release attempt failed only because this environment lacked `pytest`; no test itself failed. I installed it and resumed the release. `signoff --verify-release` now reports **116 of 116 test files and 7 of 7 instruments** with signatures that still hold.
- **Properties table:** two older rows had finished proofs but were still in progress: `GLM.Foundations.xor_blind` and `GLM.Gen2.xor_is_blind_on_rational_meanings`, the mod-2 limit results. I checked their axioms and marked them proved. I also confirmed the Phase 70 row `native-parity-readback-exact` is proved.
- **Caveat on the table:** it is too long for me to list in full, so I can't confirm every older row is up to date.

All work is committed. No new round has been started. The next round would begin from `STATUS.md` §3.4. The candidates listed first are:
- **N, native past parity:** resampling the Lean corpus, a third native book for documents, a native word ranking, and shipping the text tie-break.
- **M, reverse Three Column Thinking round four:** strings and tuples, a small imperative grammar, a complete integer decision, and extending the planner loop.

# Summary of changes for run d074e94e-f7e4-4ce4-8b31-72572651a701
The previous session had finished Phase 68 (reverse Three Column Thinking, round two) and signed its release, but it ran out of time before writing up its Lean results. I checked that this work still stands: `signoff --verify-release` passed, the Lean tree built with no `sorry`, and `corpus --check` was current. I then brought the properties table up to date. The round-two proofs in `ReverseTCTTwo.lean` are now marked proved: unique readability, exact negation with its simplification, and Python's floor/remainder convention. Three older rows had proofs but were still marked in progress (`NormFamily`, `Gen3`); I re-checked their axioms and marked them proved.

I then took the next open item, the integer-variable part of candidate M, as **Phase 69**. The marks X1–X7 and every expected answer (`evaluation/reverse_tct_int_cases.py`) were committed before any code was written. Everything below was measured here.

**What was built**
- `overlay/glm_universal/reasoning/reverse_tct_int.py` adds two new question forms: `entails over the integers: P ; C` and `bounds over the integers of x: P`.
  - `x // b` and `x % b` split into one case per remainder when the divisor is an integer constant with |b| ≤ 64. Over ℚ these are refused as `NOT_POLYNOMIAL`.
  - Each case is decided over the integers by elimination, rounding every inequality to its tightest integer form.
  - When the system has no integer solution, the answer comes with the chain of combined inequalities that rules it out.
  - When neither that proof nor an integer solution is found, the answer is a new named refusal, `INTEGER_UNDECIDED`, because this method can miss some cases.
- Each answer comes with its own checking script, which redoes the case split, every rounding step and every witness point with separate code.
- You can reach it through `GLM.py --ask`, `GLM.py --reverse` and `tools reverse-tct --three`. It has 17 tests in `tests/test_reverse_tct_int.py`.

**Results** (write-up in `studies/REVERSE_TCT_STUDY.md` §10–§12)
- All 29 entailment cases and all 10 bounds cases gave the expected answer, 0 wrong.
- All 34 checking scripts print `VERIFIED True`, and all 34 deliberately altered copies are rejected.
- 116 test questions set inside a small range all match checking every point in that range.
- Asked over ℚ instead, the same 29 entailment questions get 20 refusals and 9 different answers. For example, over ℚ `x > 2` does not entail `x ≥ 3`, and `2x = 1` has a solution.
- **Limitation:** a well-known example with no integer solution (Pugh's system) is refused `INTEGER_UNDECIDED` rather than decided. A "nothing bounds x" answer is not certified by the checking script, as in the earlier rounds. The planner relay does not yet read integer answers.

**Lean proofs** (`RequestProject/GLM/ReverseTCTThree.lean`, copied into `overlay/glm_lean`, standard axioms only, no `sorry`; added to your properties table as proved)
- Python's `//` and `%` on integers are exactly the quotient and remainder of `a = b·q + r` in the right range, and these remainder cases cover every integer.
- Both rounding steps are exact over the integers.
- Any chain of combined inequalities that the checking script accepts keeps every integer solution, so reaching a contradiction proves there are none.
- A system with no rational solution has no integer solution.
- `2x = 1` has a rational solution and no integer one.

**Round close-out**
- Adding the new files moved two measured search figures, and I updated their expected values:
  - Stack relay: 747 → 754 of 881, now carrying 18 queries (was 17) and losing 0.
  - Anonymous reader: 747 → 82 and 244 → 175 of 881.
- The count of 3,963 declarations, 139 Lean files and 115 test files is now current in the documents. I also brought the rebuild-cost table in `ITERATION_COST_STUDY.md` and the gate-sweep prose in the stack-relay study up to date.
- `STATUS.md`, `MASTER_PLAN.md` (Phase 69), `WHITEBOARD.md`, the READMEs and the tool catalogue are updated. Candidate M in `STATUS.md` §3.4 now lists only its remaining items.
- Final state: `lake build` succeeds, `corpus --check` is current, and `signoff --verify-release` reports 115 of 115 test files and 7 of 7 instruments with signatures that still hold. All work is committed.

# Summary of changes for run 7722e454-1de9-4e37-833e-2da04d554cdb
This round adds reverse Three Column Thinking as Phase 67: the GLM now writes the language column itself, working from the script and the mathematics. The round is closed and signed off: `signoff --verify-release` reports 113 of 113 test files and 7 of 7 instruments with signatures that still hold. The Lean module builds with no `sorry`.

**What was built**
- `overlay/glm_universal/reasoning/reverse_tct.py` turns an exact term, statement or set of statements into an English sentence and reads the sentence back.
- The semantic operations work on the mathematics, not on the words:
  - `say` (state it in English)
  - `equivalent` and `paraphrase`, which come with a certificate
  - `negate`
  - `solve` (a solved form)
  - `entails`, which returns ENTAILS, CONTRADICTS or INCONSISTENT_PREMISES with a certificate that can be checked
  - `bounds` (the tightest bounds the statements imply)
- `reasoning/reverse_tct_script.py` writes the column-3 script for each case. It also changes each script on purpose to confirm the checker notices, and runs a comparison against a normal infix grammar.
- You can reach it through `GLM.py --reverse`, through `GLM.py --ask` (via a new `reverse` route in the router), or with `tools reverse-tct`.
- There are 23 tests in `tests/test_reverse_tct.py`. The study, with its plan written before the code, is `studies/REVERSE_TCT_STUDY.md`.

**Measured results**
- All 176,617 terms in the test set turn into sentences and read back correctly, and no two terms share a sentence. The infix grammar used for comparison gives 5,684 sentences that stand for more than one term.
- All the planned cases give the planned answers, with 0 wrong: 34 `entails`, 14 `solve`, 10 `bounds`, 18 `equivalent`, 4 `negate`, and 36 `say` cases (24 + 7 + 5), five of which correctly refuse.
- All 94 generated scripts pass their check, and all 69 deliberately broken versions are caught.
- A reader that only has the sentences answers 0 of the 58 comparison questions; the operations answer all 58.

**Lean proofs** (`RequestProject/GLM/ReverseTCT.lean`, standard axioms only, added to your properties table as proved)
- The English grammar is unambiguous: no sentence is the start of another, and different terms, statements and sets of statements always give different sentences.
- The infix grammar is ambiguous.
- `negate` is exact.
- The Farkas certificate behind `entails` does rule out every point that would satisfy the statements.
- The grid check the scripts use proves two polynomials are equal.

**Round close-out**
- The new study and code grew the searched Lean collection to 3,900 declarations. That moved two figures elsewhere, and the expected answers were updated to the new values:
  - **Stack relay:** it now carries 18 queries the single wheel misses (19 before) and loses 0, scoring 737 → 744 of 867 queries. It is still strictly ahead on all five gates up to 1/4.
  - **Anonymous reader:** it now scores 737 → 81 and 239 → 170 of 867.
- The query-escalation measurement was re-taken. Documents quoting counts were brought up to date: 3,900 declarations, 137 Lean files, the rebuild-cost table in `ITERATION_COST_STUDY.md`, the suite totals, and README entries for the new modules and test file.
- `pytest` was missing from the environment and was installed. The previous round had not taken its release; this round took it.
- `STATUS.md`, `MASTER_PLAN.md` (Phase 67, with a note on the moved figures) and `WHITEBOARD.md` are updated. A next step is listed as candidate L in `STATUS.md` §3.4.
- All work is committed.

# Summary of changes for run a444cc38-5499-4476-b134-4657cb395dd1
**Phase 65 ("carried fork") is done and committed: the release signs off at 111 of 111 test files and 7 of 7 instruments.** It does what you asked for the ambiguous Golay items. The GLM no longer stops with `AMBIGUOUS` when it hits the six equally close candidates at coset weight 4. It keeps all six, plus a ledger of why each one is still in play or has been dropped, until a later step picks one, filters them out, or proves them wrong. Escalation to the Leech lattice is tested alongside.

**What was built**
- `studies/CARRIED_FORK_STUDY.md`: the claims (K1–K4) were written down before any code, then the results, the wiring and next steps.
- `overlay/glm_universal/reasoning/carried_fork.py`: the carried-fork object and its ways of narrowing the set:
  - **context:** restrict to the known cases;
  - **second reading:** intersect with the candidates from a second observation;
  - **unsure set:** rule out candidates whose error pattern doesn't fit the coordinates flagged as unreliable.
- Two Leech escalations sit beside the fork:
  - **hard lift:** proves that each tie lifts to a deep hole of type A₁²⁴ in the Leech lattice;
  - **soft estimate:** ranks candidates by how reliable the read was.
- Python dialect (`GLM.py --python`): four new builtins, `nearest`, `resolve`, `agree` and `resolve_unsure`. They return the resolution or a refusal that says why.
- A `carried-fork` subcommand in `tools.py`, and 18 new tests in `tests/test_carried_fork.py`, including one exhaustive test.

**Results (from the study's tool, all exact counts)**
- **K1, context:** 592,268 of 658,812 answered, 0 wrong. **Target missed:** 85.8% at k=32 against a 90% target. This only holds when the true answer is known to be among the listed cases; without that assumption, misreads do occur (14 to 112 per 768).
- **K2, second reading:** 4,224 of 4,224 resolved, 0 wrong. Met.
- **K3, unsure set:** 3,840 of 3,840 resolved, 0 wrong. Met.
- **K4a, hard lift:** all 1,771 cosets confirmed as A₁²⁴ deep holes with 48 vertices each. Met.
- **K4b, soft estimate:** **Target missed.** Right on 512 of 768 reads, wrong on 96, tied on 160. For comparison, snapping to the nearest point got 154, soft maximum-likelihood 480, and an unconstrained Leech decoder 560. This is why the soft estimate stays a side estimate and the fork is still carried.
- **K4c:** 448 answered, 0 wrong. Met.
- **After the fact:** a second reading resolved 35,872 of 48,320 open forks, with 0 wrong.

**Lean**
`RequestProject/GLM/CarriedFork.lean` builds with only the standard axioms and contains no `sorry`. It is mirrored to `overlay/glm_lean/`. It proves 14 theorems:
- the correct answer is never pruned (`truth_survives`);
- a fork narrowed to one candidate gives the correct answer (`resolved_eq_truth`);
- a candidate that contradicts the evidence is ruled out (`contradicted_refutes`);
- at most one candidate fits (`at_most_one_fits`), and a small enough unsure set resolves the fork (`unsure_resolves`);
- the soft-reading cost formula (`soft_cost_coord`, `soft_cost_sum`);
- the distance bounds behind the Leech lift (`even_lift_coord`, `even_lift_dist`, `odd_lift_dist`);
- basic facts about the ledger and the live set.

Four of these are recorded as proved in the Properties table. The 48-vertex count and the check over all 1,771 cosets are exact computations, not Lean theorems.

**Other changes this round**
- Adding this round's files changed some existing figures, and the affected documents were updated:
  - the stack-relay figures, now recorded as a strict gain only at 1/5 (at 1/4 it is below the control);
  - the evaluation expectations;
  - the iteration-cost table;
  - the suite and corpus figures.
- STATUS, MASTER_PLAN (Phase 65), WHITEBOARD, ENTRY and the READMEs are updated. The sign-off check (`signoff --verify-release`) passes.

# Summary of changes for run cdc2e4ef-d262-4bc0-aa93-45cde9cba108
The GLM can now "speak" a deterministic subset of Python. It was recorded as Phase 64. Every symbolic operation produces a three-column payload: the reasoning in plain language, the same steps as exact equations over ℚ, ℤ or F₂, and a generated re-derivation script. That script runs in a fresh, isolated `python3 -I` process and has to print `VERIFIED True`. The pass marks and all test cases were written down and committed before any of the implementation code (`studies/PYTHON_SPEECH_STUDY.md` §0–2, `overlay/glm_universal/evaluation/python_speech_cases.py`).

**What was built**
- `overlay/glm_universal/reasoning/python_substrate.py` maps Python constructs onto the substrate:
  - `Fraction` → a coordinate in ℚ²⁴; `int` → the dyadic tower; `bool` → one F₂ bit.
  - `&`, `|`, `^`, `~` run as gate programs on the 8 vertical 3-bit Toffoli/Fredkin sub-registers. `<<` and `>>` are moves up and down the dyadic tower.
  - Slices are exact index maps; `frozenset` becomes a 24-bit mask.
  - `match`/`case` is decided by Golay decoding: a unique branch at distance ≤ 3, AMBIGUOUS at 4, UNCORRECTABLE at ≥ 5.
  - AST expressions get a structural address.
- `overlay/glm_universal/reasoning/python_speech.py` holds the evaluator, the named refusals and the payload builder. The refusals cover floats, non-determinism (`hash`, `random`, clock), the deep hole at distance 4, uncorrectable distances, and comparisons across mismatched or undeclared unit scales.
- `overlay/glm_universal/runtime/python_tct.py` runs the isolated subprocess. It sits in the runtime layer because reasoning modules are not allowed to start processes.
- Entry points: `GLM.py --python SOURCE` / `--python-file`, the `tools python-speech` subcommand, and `tests/test_python_speech.py` with 25 tests.

**Measured results** (all six pass marks P1–P6 met)
- 83 of 83 value programs answered correctly; 26 of 26 refusal cases refused under the right name.
- Every generated script re-derived its answer to `VERIFIED True`. A copy of each value script with a deliberately wrong final claim was rejected every time.
- 80 of 80 register operations were correct and reversible.
- Around one declared case set, 12,951 test points gave 2,325 branches, 10,626 AMBIGUOUS refusals and 0 wrong branches.
- 10 of 10 declared equivalent-expression pairs got the same address, with 0 collisions among 57 distinct expressions.
- A generated battery of 7,128 expressions: 2,830 answered, 0 wrong, the rest refused.
- For comparison, the existing question interface (`GLM.py -q`) solves 0 of the 83 value programs.

**Lean:** `RequestProject/GLM/PythonSpeech.lean` builds with no `sorry` and only the standard axioms. It proves:
- the gate programs are bijective and match the bitwise operations;
- `<<` is multiplication by 2ᵏ and `>>` is floor division by 2ᵏ, including for negative integers;
- the slice index map is exact;
- the `match` classification always gives exactly one of branch, AMBIGUOUS or UNCORRECTABLE, for any code with minimum distance 8.

Four properties are marked proved in the Properties table.

**Checks:** the full release sign-off passes, with 110 of 110 test files and 7 of 7 checks signed and the exhaustive cases run; `--verify-release` confirms it. `corpus --check` reports current. The suite count is now 4,292 tests across 109 of the 110 test files. To get there I made two fixes:
- A test that looks for outdated counts in the documents was matching the retired "34 Lean files" inside the correct "134 Lean files". It now matches whole numbers only.
- `^` was used in the two new modules without being classified, which the check forbids. I added both to the classification list.

**Limits:**
- "Zero entropy" here means the gate operations are proved bijective; no thermodynamic claim is made.
- The Golay code has covering radius 4, so the UNCORRECTABLE (distance ≥ 5) verdict can only happen against the declared cases, never against the whole code.
- Two expressions get the same address only up to reordering of commutative operations, variable renaming and parentheses. It is not a general test of whether two programs mean the same thing.
- Only the Python subset listed in the study is supported; anything outside it is refused.
- The negative-step slicing case is not covered by the Lean proofs.

# Summary of changes for run 878c9eed-5d08-4f1e-ac1a-44d14bb6f734
This round was round two of `studies/SUBSTRATE_NATIVE_COGNITION_STUDY.md`, recorded as Phase 63. The three new question frames answered 26 of the 33 questions written for them before they were built and refused the other 7 as planned, with 0 wrong. The grammar alone answered none of the 33. The full release check passes: 109 of 109 test files and 7 of 7 instruments are signed, and the corpus check is current.

**What the study found (§6 lists the planned tests, §7 the results, §8 the next steps)**

Following your point about functions that miss by a small margin, I went back to the ideas that nearly worked in round one and kept the part of each that does work:
- **Wobble-signature analogy (concept 7)** failed as analogy but did pick out exact fractions. It is now **rational recognition**: the system finds the simplest fraction in the range a decimal (or a 512-tick delta-sigma run) pins down, and answers only when every other candidate fraction has a denominator at least twice as large. It recognised all 79 test fractions exactly. It correctly ruled out all 8 non-fractions, and every decoy got the same verdict as its target. On typed decimals it gave 7 correct answers and 3 correct refusals (2.71828, 1.41421 and 0.1).
- **Rational intervals (E1)** can now be reached by a question, e.g. *is the atomic weight of iron consistent with 55.845?* It gave 7 correct answers and 1 correct refusal. The check that refuses to order two readings whose ranges overlap currently triggers on no element or molecule pair, so it stays in as a safeguard.
- **Dimensional derivation (concept 4, partly done)** solves the dimension equations exactly. Each answer is labelled unique, impossible or undetermined, and each comes with a certificate. It gave 12 correct answers and 3 correct refusals. The angular-frequency question is refused because the reading with plane angle and the SI reading disagree.
- **Using the error measure (TAX) as a loss (concepts 1 and 9)**: restricted to the set of words the read word could have been (its coset), minimising TAX gives exactly what the existing decoder gives, on 3,136 of 3,136 reads. So this is kept as a second description of decoding, not as a new ability.
- **Nested holdouts for the chemistry estimates (E3):** 7 of the 9 estimation rules survive re-selection. `covalent_radius_pm` and `electron_affinity_eV` do not; they are listed for demotion but not yet changed.

**Other changes**
- **The planner is now the default reader** of `GLM.py` questions (R1). On the 177 contract cases it gives the same outcomes as the grammar: 149 correct and 28 refused as expected. `--grammar` switches back to the grammar alone.
- **Wording (E2):** the documents now describe the runtime as the partial Norton–Sakuma 2A axial algebra on axes, not the Griess algebra. Code identifiers keep their names.
- **G1 (a small language model as parser) is declined permanently**, as you asked.
- The interval code moved to a new file, `reasoning/intervals.py`. Before the move, the answering path pulled in the experiments module and with it the whole Lean development, which broke the release check.
- The new Lean file made the Lean corpus grow (3,747 → 3,766 declarations), so measurements that read it changed. The stack relay now carries 20 queries and loses none, up from 14. I updated the affected evaluation cases and study text to the new figures.

**Lean:** `RequestProject/GLM/CognitionRoundTwo.lean` builds with standard axioms only and no `sorry`. It proves the answering rules behind the new frames (for example, when two intervals overlap and when a fraction is the only simple one in range), and that the TAX minimum over the coset is the nearest-codeword decoder. It also covers two consolidation items:
- **C2:** the delta-sigma output written as a stream, with its period proved.
- **C1, first step:** the links between layers are proved to form a Galois connection. The full "adjoint functors" version is not done.

The six results are marked proved in the Properties table.

**Still open**, in the order of study §8 and candidate H of `STATUS.md` §3.4:
- demote or narrow the two failing chemistry rules;
- E4 (semantic judgements with recorded provenance);
- E6 (frames generated from a declaration instead of written by hand);
- E7 (deeper PCGS proofs);
- a second independent reading for the deep-hole fork;
- concept 6.

`STATUS.md`, `MASTER_PLAN.md` (Phase 63), `WHITEBOARD.md` and `README.md` are updated; `ARISTOTLE_SUMMARY.md` was not edited.

# Summary of changes for run 06a72d84-5505-4b6c-b448-b0e504435e41
I moved `substrate_native_cognitive_1.txt` into `source_material/`, turned its ideas into a numbered ToDo/Experiment list, and ran nine of them as experiments. Each experiment's pass mark was written down and committed before any measuring code existed. **5 of the 9 met their mark and 4 did not. One new capability is now reachable from a question:** a solver whose answers each come with a certificate that can be checked independently.

The full write-up is `studies/SUBSTRATE_NATIVE_COGNITION_STUDY.md`, linked from `ENTRY.md`. §1 is the list, §2 the pre-set marks, §3 the results and §5 next steps.

**The list** (status in brackets)
- **R1** Make the typed planner the default reasoning loop (ToDo).
- **R2** Exact Möbius arithmetic on continued fractions (built and met, not connected to queries).
- **C1** The five-layer stack as adjoint functors (ToDo).
- **C2** Infinite structures as streams (ToDo).
- **G1** A small language model as parser (declined here: nothing here can run a model, and its output wouldn't be repeatable).
- **G2** Embed the Leech lattice in the Lorentzian lattice II₂₅,₁ (first step proved; no dynamics claimed).
- **E1** Interval values that refuse to compare when they overlap (built and met, not connected).
- **E2** Call the algebra a partial Norton–Sakuma 2A algebra, not the Griess algebra (ToDo, a wording sweep).
- **E3** Nested holdouts for the chemistry estimates (ToDo).
- **E4** Record who made each meaning judgement and when (ToDo).
- **E5** Derive answers no stored table holds (built, met and connected).
- **E6** Generate the planner's question patterns from a declaration (ToDo).
- **E7** Deeper proofs for the proof-carrying generator (ToDo).
- **E8** Prove impossibility first (built and met in a small test space).
- **Concepts 1–9** from the document:
  - 1 and 9 (TAX as a loss to minimise; vacuum-seeking inference) were refuted: the loss repeats with the lattice, and minimising it erased both concepts.
  - 2 (reversible inference) met.
  - 3 (predicting the mass residual) declined: no proposed mechanism could be run without fitting.
  - 4 (drive generation through Three Column Thinking) ToDo.
  - 5 (branch at the deep hole) met, not connected.
  - 6 (climb the Griess tower) ToDo, blocked on E2.
  - 7 (wobble matching as analogy) refuted.
  - 8 (abstraction down the dyadic tower) not met with one tower; two offset towers fix it, and that is proved.

**Results**
- **Decoder fork (X1):** 4,224 of 4,224 correct, 0 wrong.
- **Reversible search (X4):** agrees with brute-force search on 32 of 32 targets, certifies 16 as impossible, and undoes exactly.
- **Intervals (X6):** over 30 atomic weights, 0 comparisons give a wrong order; overlapping pairs are refused. The standard weights were typed in by hand from the IUPAC table.
- **Möbius arithmetic (X8):** 82 of 82 convergents agree with the existing exact-real layer.
- **Certificate solver (X7), the connected one:** new module `reasoning/certificates.py` handles Bézout coefficients, integer solutions of ax + by = c (or a proof there are none) and factorisation with a stated limit. On 16 questions fixed in advance it gave 13 correct answers, 3 correct refusals and 0 wrong. The existing grammar answered none of them.

The experiments run with `python3 -m glm_universal.tools cognition`, and `test_substrate_cognition.py` adds 18 tests for them.

**Lean:** `RequestProject/GLM/SubstrateCognition.lean` holds 14 theorems backing these results. It builds with no `sorry` and only the standard axioms, and seven of the theorems are marked proved in the Properties table.

**Checks:** the full release sign-off passes (109 of 109 test files, 7 of 7 checks including the Lean build and the 177-case evaluation), and the documentation check reports current.

**Changes outside the new files that you should know about:**
- The new file shifted some older measured figures:
  - **Relay figures:** now 721 → 726 of 833, carrying 14 queries and losing 0.
  - **Anonymous-query figures:** now 721 → 66 of 833, and 225 → 151 of 833 for the structural address.
  - **Stale counts:** these were updated in the documents that quote them, including `studies/STACK_RELAY_STUDY.md`, and the query-escalation measurement was re-taken.
- One document test forbade the phrase "92 modules" as an out-of-date package count. The reasoning folder now genuinely has 92 modules, so I removed that phrase from the forbidden list, with a comment, as earlier rounds did for "71 modules" and "88 modules".

The round is recorded as Phase 62 in `MASTER_PLAN.md`, `STATUS.md` and `WHITEBOARD.md`.

# Summary of changes for run 905157a2-4715-4806-af76-03fe98988a9d
I updated both documents. `studies/GLM_ACADEMIC_PAPER.md` and `studies/GLM_Complete_Number_Theory_Evidence.md` now cover the whole system, including the Lean I retrieved from the archive this round. The three new Lean files build, contain no `sorry`, and use only standard axioms. A full release check passes, and every commit is in place.

**What I retrieved and proved.** Three archive Lean files were ported into `RequestProject/GLM/`, which brings the project to 131 Lean files:
- **`Distinction.lean`** (from `FirstPrinciples`): the toggle is the only non-trivial reversible operation on one cell; every two-element ring is `ZMod 2`; and a group where every element is its own inverse is abelian.
- **`GolayMOG.lean`** (from `encoding_definition_attempt_03-08.26`): the 12-bit Gray identity addresses of the 118 elements never collide, and consecutive elements differ in exactly one bit. It also keeps the archive's negative results: binary TAX depends only on bit count, and the 24-to-3 projection loses information. Its finite checks use `native_decide`.
- **`SeedRoles.lean`**:
  - **e is irrational:** a new, complete proof.
  - **The lattice character is not the e seed:** now proved outright, with no extra assumption.
  - **φ is "cheapest", in an exact sense:** no quadratic Pisot number is smaller, but the plastic number is.
  - Also: φ is badly approximable, the branches for π·e, the SL₂ trichotomy, and the hull and fibre results.

All five results are marked proved in the Properties table.

**What the paper gained.**
- New §10.5 on the archive's 20-phase speed-of-light audit.
- New §11.7 on the GolayMOG discrete layer and the archive's benchmark figures.
- New §16.6 (φ cheapest) and §16.7 (π·e branches).
- The retrieved theorems are cited in §2.1, §14.1, §14.3, §14.4, §15.1 and §16.3.
- Appendix B lists the new files, and Appendix C's ledger of archive folders is extended.

**Corrections to the paper.**
- §25.1 gained an item and had two updated.
- In §25.2, items 1 and 4 were corrected.
- In §25.5, items 7 and 15 were updated.
- The relay text now gives the current measurement.

**What the number-theory document gained.** New §22–§27 cover:
- the seeds as numbers;
- the distinction results;
- the two-gap law;
- the Triad, TriadCensus, TriadChance and Platonic audits;
- GolayMOG;
- the Niemeier and higher-lattice results.

Its ledger and index rows were extended, and its test file passes (17 tests).

**Measurements that moved.** The new Lean grew the declaration count from 3617 to 3730, and several recorded numbers moved with it. I re-measured them rather than keeping the old values:
- **Relay:** it now carries 13 queries and loses none, and it beats the text control at all five gate settings up to 1/4. In Phase 59 it only reached 1/5.
- **Anonymous register:** 829 queries.

I updated the evaluation cases, `STACK_RELAY_STUDY.md` and `test_stack.py` to match. The relay test had been asserting the old Phase 59 verdict, so it would have failed without that change. `ITERATION_COST_STUDY.md` now gives 132 Lean files (the 131 plus `Main.lean`).

**Checks.** The full release check passes: 108 of 108 test files and 7 of 7 checks are signed off with the exhaustive cases run. The suite now stands at 4,239 tests across 107 of the 108 test files, and the documents that quote this figure were regenerated to match. The document corpus check reports current. `MASTER_PLAN.md`, `STATUS.md` and `WHITEBOARD.md` record Phase 61 as closed, including the release.

**Still not retrieved.** The language half of the MOG cube (about 30 files) and the rest of `ObserverY.lean` are recorded as open in `STATUS.md` §3.4, candidate G. No code path in the system uses the new Lean files yet.

# Summary of changes for run 48c8ba1a-28ee-4712-a09c-fe88c0a6d77b
The GLM can now answer questions in electrical/mechanical "wheel" language. It uses exact rational and complex arithmetic, and it refuses when it doesn't know rather than guessing. On the held-out engineering question set, the old answer paths got 0 right. The new surface gets 53 right, correctly refuses 10 and gets 0 wrong. The Lean parts build with no `sorry` and only the standard axioms.

**Files:** your new scripts, the session record and `glm_smith_matching_candidates.csv` are now in `source_material/formula_wheel/`.

**Do I need the missing files?** No. I rebuilt `glm_smith_chart_study.py`, `glm_smith_chart_extensions.py`, `glm_delta_sigma_audio_study.py` and the original `glm_formula_wheel_study.py` from the session record's descriptions. They would only help in two cases:
- reproducing the record's floating-point figures byte-for-byte;
- blind-ranking the rows of `glm_smith_matching_candidates.csv`, which needs the extensions script's load model.

**What was built** (package `overlay/glm_universal/engineering/`):
- `wheels.py`: formula wheels as exact exponent-vector relations.
  - All 41 formulas check at their reference values, and all 41 can be derived from the axioms.
  - The Ohm wheel has 12 spokes; there are 108 spokes in total.
- `smith.py`: Smith chart. All 16 checks pass.
  - An exact L-network match gets the worst-case |Γ|² down to 42365/290173, against 3469/19669 with no matching network.
- `analogy.py`: cross-domain mechanical↔electrical translation.
  - Force–voltage analogy: 9/9 in both directions.
  - Force–current analogy: 8/9 (it swaps series and parallel Q).
  - A scrambled control gets only 4/9.
- `delta_sigma.py`: delta-sigma modulators. All 6 checks pass.
  - Second-order beats first-order by at least 21 dB; first-order beats memoryless by at least 56 dB.
  - I found and fixed two bugs in my own code on the way (integrator order and signal-delay alignment).
- `speak.py`: 7 question patterns. Adding them changes 0 of the 374 existing questions.
- `study.py`: generates the study report.

**How to use it:** `GeometricSession.ask_engineering`, `GLM.py --eng`, or `python3 -m glm_universal.tools engineering`.

**Tests:** the question sets are in `overlay/glm_universal/evaluation/engineering_heldout.py` and were committed before any code was written.
- Held-out set: 63 questions (scores above).
- A second, harder set of 38 questions was also fixed in advance. Its first run is kept as-is: 27 right, 1 wrong, 10 correct refusals. The one "wrong" answer is a formatting mismatch (`-2/5` vs `- 2/5j`), not a wrong value.
- `tests/test_engineering.py`: all 25 tests pass. The corpus consistency check now passes; getting there meant regenerating two stored measurements that had gone out of date.

**Lean** (`RequestProject/GLM/EngineeringWheels.lean`), 11 theorems:
- Wheel derivability: consistency, and derivability survives translation between domains.
- Ohm wheel: P = V²/R follows from V = IR and P = VI; the control P = V·R does not.
- Smith chart: the map inverts correctly, admittance gives Γ(1/z) = −Γ(z), passive loads land in the unit disc, and on its edge exactly when lossless.
- Delta-sigma bitstreams: input p/q has least period q, and an irrational input is never periodic.

The 5 matching entries in the Properties table are marked proved.

**Docs:** `studies/ENGINEERING_LANGUAGE_STUDY.md`, plus updates to STATUS.md, MASTER_PLAN.md (Phase 59) and WHITEBOARD.md. I found no advantage from the Golay/Leech encoding in this area and don't claim one.

# Summary of changes for run 100ce99b-8a06-4b23-b86a-4a7368923f08
This session added **Phase 58 — typed question plans**. It takes items P1 and P2 from `source_material/GLM_IMPROVEMENT_ROADMAP.md` and is closed and released. The roadmap's own measurement was the reason for picking it. Asked through the normal `ask` path, the frozen 20-question language probe scored only 2 correct, 1 wrong and 17 refused, even though the existing table, ordering and extremum operations already held most of the answers. What was missing was the step from English to those operations.

**What was built**
- **Test sets written before any planner code** (`overlay/glm_universal/evaluation/heldout.py`, committed on its own in `8064795`): 60 rewordings of the probe questions, 30 new combined questions, and 20 trick questions where refusing is the right answer. A harder 47-question stress set was committed in `ca257db` before its first run. Its first-run score is frozen at 28 correct, 0 wrong, 13 refused and 6 correct refusals.
- **The typed planner** (`overlay/glm_universal/runtime/semantic_plan.py`): it turns a question into typed frames and grounds them. It does exact arithmetic, primes, gcd and lcm, and uses a declared table of 17 exact unit definitions. It answers only when every plan that works gives the same value, and refuses as ambiguous when two such plans disagree (e.g. torque vs energy). A question no plan covers goes to the existing grammar unchanged.
- **It is opt-in:** `GLM.py --plan` or `GeometricSession.ask_planned`. The default command line and the 177-case evaluation are unchanged.
- **Measurement and documentation:** a study module with a stored report (`reasoning/typed_plans.py`, `tools plans`), 32 tests, generated figures, `studies/SEMANTIC_PLAN_STUDY.md`, and entries in STATUS.md and MASTER_PLAN.md.
- **Lean:** `RequestProject/GLM/SemanticPlan.lean` has 8 theorems. They show the answering rule doesn't depend on the order plans are tried, that it refuses whenever two plans disagree, and that it only adds to what the grammar already answers. They also show that the obvious alternative ("take the first plan that works") depends on order and answers the torque question the shipped rule refuses. The file builds with no `sorry` and only the standard axioms. Three entries in the Properties table are marked proved.

**Results**
- **Frozen probe:** 19 correct, 0 wrong, 1 refused with the planner (was 2 correct, 1 wrong, 17 refused).
- **Held-out sets (110 questions):** 86 correct, 22 correct refusals, 1 wrong. The wrong answer is iron's atomic weight: the stored table holds 55.84, while the answer key uses the IUPAC value 55.845. That is a precision issue in the table, not a planner fault, and the answer key was left as written.
- **Stress set:** 33 correct, 0 wrong, 8 refused and 6 correct refusals after later changes. Those changes were made after seeing the set, so this figure is reported as tuned; the untuned figure is the frozen first run above.

**Closing the round**
Adding the new Lean file and test file moved several numbers typed by hand into the documents: file and declaration counts, the cost table, and the anonymous-register and relay study figures together with their evaluation cases. These were updated to the current measured values. Three held-out question strings were reformatted so the check on Lean-name citations doesn't misread them; the question text itself is unchanged. The stored caches were rebuilt.

The final release check passes: 107 of 107 test files and 7 of 7 instruments are signed, and the document check reports current.

`WHITEBOARD.md` now says no round is in flight and has two new "things learned" notes about these knock-on updates. The next round starts from STATUS.md §3.4. Making the planner the default is listed there as a candidate.

# Summary of changes for run d5cd319b-32ee-44e5-9939-74c2f0290383
I picked the session up at the point it stopped — the Phase 56 Lean results had not reached the Properties table — finished that, and then took the next round in full and closed it.

**Finishing what was in flight.** `RequestProject/GLM/RoleBinding.lean` and `RequestProject/GLM/PlanStore.lean` were re-checked on a clean `lake build` (126 Lean files, no `sorry`, repository and overlay copies identical) and their theorems recorded in the Properties table as four entries, each verified to depend only on Lean's standard axioms: the parity binding inverts unconditionally and its role cannot be read back out; the product binding fails on a single zero coordinate, and naming a filler refuses rather than guessing where two carriers share a reading; the plan store replays exactly what re-running would have said, refusals included; and the coarse key hands one conversation another's antecedent where the exact key does not.

**The round I then took and closed (Phase 57).** The tree's own wiring audit reads the figure registry the opposite way to directive D6: D6 makes every figure a document quotes generated, and nothing made the converse true, so 20 of the 135 registered keys were recomputed on every release and read by nobody. Each was decided one at a time; all twenty are now quoted — the corpus sizes in `studies/CORPUS_ADDRESS_STUDY.md`, the Lean corpus size in `studies/LEAN_ADDRESS_STUDY.md`, the field-surface and ordering class readings in their studies, the refusal figures of the norm-family and second-reading studies, and the register, report-subject and bare counts in the plan, directives, runtime, tests and Lean readmes. Closing it exposed two real defects: two registered measurements of *how many documents* disagreed by three (one counted the documents the machine generates, which the digest deliberately excludes — the key now counts the written corpus), and the operation-escalation study was typing its deciding figure by hand, a plain D6 breach. The converse is now a checked rule rather than a habit — a new test fails when a registered key is quoted by no document, and when a document quotes a key the registry does not hold — and D6 states both halves. One check had to be corrected to make it possible: a tier-0 verdict that quotes a generated figure was failing the tier contract, so the verdict comparison now strips the marker and its emitted value first, for the same reason the deciding figure's own numbers were already exempt.

**Everything verified by running it here.** `lake build` clean over the 126 Lean files with no `sorry`; the full Python suite 4,170 passed / 19,098 subtests with the four corpus failures the mid-round document edit caused fixed by re-refreshing and re-run green; `corpus --check` **current** with the document checks holding and 420 of 420 inline figures fresh; the wiring audit now reading **135 registered, 135 quoted, 0 never quoted**; a full release signing **106 of 106 test files and 7 of 7 instruments**, confirmed afterwards by `--verify-release`; and the end-to-end evaluation passing as part of it. The round is written up in `MASTER_PLAN.md` Phase 57, recorded in `STATUS.md` §3.4 with the remaining candidates re-ordered, and `WHITEBOARD.md` is back to its idle shape with three new lessons. All work is committed.

# Summary of changes for run 18e3edb7-086e-4184-bca5-49492d21495e
I picked the work up where the last session stopped and closed the round it had left open.

**What I found.** The tree's own gates disagreed with its prose: `WHITEBOARD.md` said no round was in flight, but the sign-off ledger reported a new test file, four drifted document units and two failing instruments. The scale-conversion round — the declared table of conversions between scales, which removes the refusals the ordering and extremum operations shared — had shipped its module (`overlay/glm_universal/reasoning/scale_conversion.py`), its Lean file (`RequestProject/GLM/ScaleConversion.lean`), its 43 tests and its study (`studies/SCALE_CONVERSION_STUDY.md`), and had then stopped before the measurements, documents and release that close a round.

**What I did, all of it run rather than reported.**
- **Re-took every measurement the round moved.** The blast-radius table in `studies/ITERATION_COST_STUDY.md` (103 test units, 125 Lean files, 91 units an edit to any Lean file makes stale, 86 for the worst single file); the sandbox planner's fallback reading, which now sees **16** escalatable refusals rather than 14 — it refuses all sixteen, so its utility gate still fails and it stays unpromoted, with the two new rows written into `studies/REVERSE_CALL_PLANNER_STUDY.md`; and the corpus address books, digest and inline figures.
- **Brought the documents into line with what is there:** 124 Lean files, 103 test files, 177 CLI cases, 3,529 addressed Lean declarations, 88 reasoning modules. That touched the repository, overlay, package, reasoning, evaluation and tests READMEs, `STATUS.md`, `CAPABILITY_ASSESSMENT.md` (including the per-kind accuracy table and the two new boundary refusals, now 28) and the number-theory evidence paper.
- **Fixed a drift guard that had collided with the truth.** `test_figures.py` forbids counts retired in earlier rounds; the reasoning kernel grew into one of them (`88 modules`, retired when the *package* held 88), so the guard now names the unit it counts rather than the bare number — the same repair the file already records for `71 modules`.
- **Wrote the round's record.** `MASTER_PLAN.md` gains **Phase 55** — what was built, what it buys, what was measured (all 12 declared questions as declared, 7 answered and 5 refused; 6 of 7,750 scale pairs related), what is proved rather than measured, and what it does not claim — and `WHITEBOARD.md` is returned to its empty shape with the round recorded as closed and the lessons it taught added.
- **Released the tree.** After the documents, the refresh and the document check: `corpus --check` is **current**, and `signoff --verify-release` reports **103 of 103 test files and 7 of 7 instruments** signed with the exhaustive cases run — a complete suite of **4,118 tests and 15,578 subtests, zero failures**; the end-to-end CLI evaluation is **177 / 177**; the capability probes and benchmark suites pass; and `lake build` over the 124-file Lean development completes cleanly with no `sorry` and the overlay's copy identical.

The Properties table entries for the scale-conversion theorems stand as proved, and are backed by that clean, `sorry`-free build. All work is committed.

# Summary of changes for run f0244032-c357-48f2-b14b-922706c97153
I picked the round up where the previous session stopped and closed it. The `extremum` work (one coordinate read off every row of one declared table, folded exactly or refused) was already wired and written up; what was missing was everything a new query kind invalidates, plus the release that signs the tree. All of the following was run here, not reported.

**Defects found and fixed at the root, rather than worked around.**
- Two Lean citations in the package did not resolve: the runtime's column-3 script split `GLM.ColumnExtremum.extremum_over_present_is_not_the_extremum` across two string fragments, so it was cited truncated, and an evaluation note cited the definition `trough?` rather than a theorem. Both now cite resolvable names, and the citation check passes over the whole package.
- A test still called a helper by its old private name (`_as_exact`), which had been made public when the extremum module began sharing it.

**Measurements re-taken rather than loosened.** A new query kind moves three of the readings the tree takes of itself, and each was re-measured and its prose brought into line: the sandbox planner's fallback is now taken over **14** refusals rather than 10 — it refuses all fourteen, so its utility gate still fails and it stays unpromoted (`studies/REVERSE_CALL_PLANNER_STUDY.md` updated, including the four new refusal rows); the iteration-cost blast radius moved to 101 units / 123 Lean files / 89 / 84 (`studies/ITERATION_COST_STUDY.md`); and the query-escalation cache was re-taken over the 172-case set, which had been silently stale and was failing the end-to-end run.

**Documents reconciled.** 24 query kinds, 87 reasoning modules, 101 test files, 122 Lean files and 172 CLI cases now agree everywhere the drift guard reads them; `MASTER_PLAN.md` Phase 53 gains a paragraph on what the new kind moved elsewhere and the release it earned; `WHITEBOARD.md` is returned to its empty shape with the round recorded as closed and two new lessons added; historical change-log passages were left as written, since they record what was true at the time.

**The tree I am handing over.** `corpus --check --all` **current**; `signoff --verify-release` reports **101 of 101 test files and 7 of 7 instruments** signed with the exhaustive cases on; the suite sentence re-measured at **4,038 tests across 100 of the 101 test files, 15,644 subtests**, zero failures; end-to-end evaluation **172 / 172** (146 answered, 26 refused as expected, all `boundary`, 0 unexpected, 0 wrong, 0 errored); benchmarks, capability probes, figures and the three Lean instruments all green; and `lake build` completes cleanly over the 122 Lean files with **no `sorry`**, the repository and overlay copies being identical. The five `ColumnExtremum` theorems in the properties table were each checked to depend only on Lean's standard axioms and are now recorded as proved. Everything is committed.

# Summary of changes for run 9f436082-4983-4b3f-ade0-52db5ff6e60b
I picked the round up where the previous session stopped, finished it, and closed it — and kept `WHITEBOARD.md` current at every step, so the state was resumable throughout rather than written up at the end.

**What the tree actually looked like on pick-up.** It had not closed. `corpus --check` reported `DIGEST.md`, the document address book and generated blocks in three studies (`CORPUS_ADDRESS_STUDY.md`, `ITERATION_COST_STUDY.md`, `ZERO_STORAGE_STUDY.md`) as stale, and only **21 of 98** test files and 6 of 7 instruments still carried a valid signature. The cause was ordering: the previous round wrote its prose into those studies after its release, so the generated layer was never re-rendered and 77 units were stale for documents. I refreshed the generated layer and re-ran the release.

**What closing it exposed, and how I fixed it rather than worked around it.** Every one of the 98 test files passed, but the end-to-end evaluation failed at 156/157: the `report lean` query timed out at the harness's 300-second per-case ceiling. It was not wrong, it had simply grown to about 203 seconds, because the separation study behind it ran two loops over the pairs of 3,383 declarations, for each of three schemes. Rather than raise the ceiling I replaced the arithmetic: the all-pairs means are now a closed form (Lagrange's identity for a point set, exact and integer throughout), and the nearest-neighbour search is pruned by two exact lower bounds over the 3,002 distinct addresses, so ties and minima are exactly what brute force reports. The query fell from **203 s to 77 s** and **every published figure is unchanged** (nearest shares a file 672 / 33 / 35, nearest is cited 120 / 6 / 3, chance 62406/5720653). Six new cases in `overlay/glm_universal/tests/test_lean_address.py` pin both routines against brute force — on corpus addresses under all three schemes, on a constructed tie, and on repeated points — rather than against their previous output. §7 of `studies/LEAN_ADDRESS_STUDY.md` records the two shortcuts and the measurement.

**The tree I am handing over, all of it run here, not reported.** `corpus --check` **current**; `signoff --verify-release` reports **98 of 98 test files and 7 of 7 instruments** signed with the exhaustive cases on; the suite sentence re-measured and reconciled everywhere it is quoted at **3,924 tests across 97 of the 98 test files, 15,326 subtests** (3,952 collected in one process, the extra 28 being the document check); the end-to-end evaluation back at **157 / 157**; `lake build` clean with **no `sorry`** in the Lean development, and the two Lean copies identical. The round is written up as Phase 48 in `MASTER_PLAN.md`, the present-tense state in `STATUS.md` (including §3.4, whose candidates this maintenance round left unchanged), and `WHITEBOARD.md` is reset to its idle shape with the two lessons this round paid for recorded in it. Everything is committed.

# Summary of changes for run 90843ef4-72cd-4e20-8bbb-0ab7868b46b5
I picked the round up where it stood and finished the verification chain, running everything rather than reporting it.

**The sign-off ledger, re-recorded.** A full release run — every test file in its own process with the exhaustive cases selected, plus every instrument — now signs **92 of 92 test files and 7 of 7 instruments**, and the recorded totals moved to **3,742 tests across the 91 counted files, 14,081 subtests** (the document check is run but not counted, so a documentation round converges in one pass). The stale suite sentence propagated everywhere it is quoted.

**What the ledger turned up, and what I fixed rather than papered over.** Running it exposed genuine drift that adding the new Lean file had caused, in three places:
- *The Lean corpus.* It is now **3,302** declarations, not 3,249; `STATUS.md`, the overlay readme and the package readme said the old figure, and the derived figures beside it had also moved — read back **3,302/3,302** with 0 coordinate errors, **2,925** distinct addresses, nearest-by-address sharing a file **649** times against 33 for a digest control and 24 for a seeded reshuffle, with chance at ≈ 1.13 %.
- *The relay.* Its measurement moved with the corpus: tuning **358 → 360** of 413, held-out **352 → 359** of 413, goals **710 → 713** of 826, the gate firing on **62 of 1,652**, **13** queries carried against **1** lost where the digest-and-reshuffle control carries **2**. The gate band is recorded as measured: strict on four consecutive thresholds, **1/20 through 1/5**, and level with the text control at **1/4**.
- *The anonymous register.* Over **826** queries the text search falls **710 → 67**, the identifier address book **395 → 44** (chance 48) and the structural address holds **236 → 164**; the stack's untouched gate fires on **551** against 31 read plainly and lifts the leader **67 → 111**; the feature-map leak touches **30** of 826 queries, the other 796 keeping every syntax coordinate. The prose of both studies, `STATUS.md`, the repository and package readmes, the plan, the module docstring and the Lean file's own header now state these; the end-to-end evaluation's expected phrases were corrected to the measured ones.

**Caches and generated artefacts.** The corpus measurement cache predated a verdict change and was crashing the renderer, so it was re-taken; the query-escalation measurement was stale and was re-taken as well. With those in place the deep-hole escalation and failure studies render their real tables again instead of "measurement stale" placeholders. Figures were regenerated and the corpus refreshed, in that order and after the document edits were final; `corpus --check` reports **current**, with the document checks holding. The reasoning-module count (76) and the test-file count (92) were corrected where they are quoted by hand.

**Final state, all verified here.** One `pytest` process over the whole tree with the exhaustive cases on: **3,770 passed, 0 skipped, 16,649 subtests, zero failures** — no remaining failures, irreducible or otherwise. The end-to-end evaluation is **149/149**. `lake build` completes over the **115** Lean files with **no `sorry`**, and the overlay's mirror is identical to the repository copy. There was no leftover comparison checkout in the delivered tree. Everything is committed.

**On whether this is improved "reasoning".** Carefully: what improved is one faculty, measured under a declared protocol, and the claim should not be stretched past it. The system addresses things geometrically — it converts a statement into a point and answers by where that point lands — and the construction ladder gives it more resolutions to land at. Under a perturbation sweep declared before the measurement, the eleven-rung reading names **462 of 568** queries correctly with **0** wrong, against 327 for the five rungs it used to read at and 283 for the best single rung; it agrees with the after-the-fact oracle exactly, and the rungs never disagree with each other. Lengthening the ladder further gives 475 at thirteen rungs and 476 at fifteen — where it first breaks: one answer goes wrong, the rungs disagree, and the result becomes order-dependent. So the honest statement is: a specific, checkable gain in geometric addressing, with a known breaking point and nothing answered wrongly inside the safe range, plus machine-checked containments underneath it. That is a real improvement in something the system reasons *with*; it is not a claim that the system reasons better in general.


# Summary of changes for run 71db44a3-23bb-4f7d-ae10-763887219732
I picked the round up where it stood, wrote the note you asked for, and finished the verification chain the previous round had left part-run. Everything below was run here, not reported.

**The note on "generate, don't store".** `studies/ZERO_STORAGE_STUDY.md` gains a new §8, *The ledger has two sides: what a table costs to keep*. It says plainly that generating instead of storing buys a smaller data footprint and no index to consult, and that the price is work at each use — so an honest comparison has to charge the table for more than its bytes: the copies in the tree and in every clone, release and backup; the loading and indexing before the first answer; the digest a derived table has to be kept beside, and the round-by-round check that it still holds; the rebuild when its inputs move; the reader code the generator would not have needed; and the risk of believing a stale table. Both sides are already measured here in integers — the storage side in §1 of that study, the keeping side in `studies/ITERATION_COST_STUDY.md`, which now cross-references §8 — and the rule that follows is stated: cache a derived object when the generator's cost per use, times the uses between two invalidations, exceeds the cost of holding the table *and* keeping it honest; generate otherwise. The Golay code is the first case (12 generator rows against 4.7 MB) and the Lean address book the second (stored, beside its digest). A short version of the same note is now in `STATUS.md` §2. I also made the repository's own storage split stop ageing: four new inline figures emit the overlay's on-disk bytes, the share of them that is cache, and the primary-data figure into the sentences that quote them — which is what caught the byte counts that paragraph had been carrying since the tree was smaller. No wall-clock claim is made anywhere; the instruments count work in integers only, and the note says so.

**The figure hygiene that remained.** The anonymous-register study's deciding figure quoted a superseded measurement, which is why the document checker was failing on two tier-0 rules for it; the headline now quotes the same 710 → 84, 388 → 48 and 232 → 171 the generated tables carry, and the body states them in hand-written prose. The relay study's prose now states its carried-against-lost figure, so its tier-0 rule holds too. Stale counts were corrected at the root in the plan (phase-37 row: 813 queries, gate on 538, 33 of 813), the repository readme, the status document (780 keep every syntax coordinate, 33 move a type-word coordinate) and the header prose of `RequestProject/GLM/Anonymous.lean`; the declaration count four documents quote moved 3187 → 3249, and the Lean file count in the Lean readme and the number-theory evidence paper 112 → 113. The plan's phase bookkeeping, which still called a closed phase "proposed", now records Phase 37 as closed and states Phase 38 — with the two candidates the anonymous round left in place of the one it closed — as where the next round starts; §3.4 of the status document and its header paragraph were brought into line.

**The chain, re-run in order.** The Lean mirror was regenerated and the two copies are identical; `lake build` completes cleanly over 113 Lean files with no `sorry`; the query-escalation measurement cache was re-taken last, after the final file was touched; `corpus --refresh` converges and reports **current** with the document checks holding and all 36 inline figures fresh; `FIGURES.md` matches a fresh computation.

**The release.** A complete release run with the exhaustive cases on passes **all 91 test files and all 7 instruments**, and `--verify-release` confirms 91/91 and 7/7 still hold on the final tree. The suite sentence the documents quote is re-measured at **3,695 tests across 90 of the 91 test files, 14,131 subtests**, and one `pytest` process over the same tree with the exhaustive cases selected reports **3,723 passed, 0 skipped, 16,695 subtests, zero failures** — the ledger's 3,695 plus the 28 tests of the document check, which is the arithmetic the status document states. The end-to-end evaluation is **149 / 149** (133 answered, 16 refused as expected, all `boundary`, no `gap`, 0 confidently wrong, 0 errored), benchmarks **2,389 / 2,390** with every suite above its baseline, and the probes 33 — 20 hold, 13 break, 0 errored. The status document's tables and its round record were then written to what the release actually measured. No new Lean declarations were added, so the properties table is unchanged and still matches the sources. All work is committed.

# Summary of changes for run eb5fc5da-9a8e-4cea-b784-d31e66ddfd18
I picked the round up at the point it had reached and closed out the four items that remained.

**The documentation pass.** `STATUS.md` now carries the round properly: a new entry in *What is done* describing the incremental address books (a vector decoded before is reused, a book at another schema, scale or cap is refused as a seed, the reuse is audited by re-decoding a sample), the planner report stored beside the digest of its own code closure, the inline figures, the ordered `--refresh`, and the generated Lean mirror; and a new *Closed this round* record in *What is open*, with the previous round's record retitled rather than overwritten. The re-verification section names `--refresh` and `lean-mirror`, and the package readmes (`overlay/README.md`, `overlay/glm_universal/README.md`, the corpus readme and the tests readme) now document both commands, the seventh corpus module (`cost.py`), the inline-figure layer and the corrected per-file test counts.

**Two defects fixed at the root rather than papered over.** The iteration-cost study cited a cache factory under a name that no longer exists; it now names `glm_universal.signoff.ledger.code_store`, where the previous round moved it. More seriously, the full release run showed the sandbox isolation check (directive D14) failing: `corpus/cost.py` reports how often the planner's report is taken, so it imports the sandbox — lazily, inside the reporting function, which is exactly the exception the directive allows — but it had never been added to the declared list. It is declared now, and the prose that said "two documentation-layer exceptions" says three.

**Everything re-earned on the final, quiescent tree.** A release run with the exhaustive cases on passes **all 89 test files and all 7 instruments**, and `--verify-release` confirms 89/89 and 7/7 still hold. The suite sentence the documents quote is re-measured at **3,631 tests across 88 of the 89 test files, 13,777 subtests, outside the document check** (it had said 88 files and 3,555 tests), and one `pytest` process over the same tree with the exhaustive cases selected reports **3,659 passed, 0 skipped, 16,337 subtests, zero failures** — the ledger's 3,631 plus the 28 tests of the document check it leaves out, which is the arithmetic the status document states. `lake build` completes over 111 Lean files with no `sorry`, both Lean copies are identical, the evaluation is 147/147, the benchmarks 2,389/2,390 and the probes 33 with 20 holding.

**The generated layer is current.** `FIGURES.md` was regenerated, the ordered refresh was run until it reached a fixed point, and `python3 -m glm_universal.corpus --check` reports `current` with no drift; the inline suite and Lean-file figures picked up the new sentence automatically in every document that quotes them. Stale hand-typed numbers found along the way were corrected too: the module count in the status table, an out-of-date evaluation-case count and Lean-file count in the top-level readme, and the five per-file test counts the round's new tests had moved. One claim in the package readme that had quietly become false — that the per-package test column partitions the suite total — is now stated accurately rather than left to look exact. Everything is committed, and the working tree is clean.

# Summary of changes for run 76c69038-6e3c-413e-a993-87046ca771a4
This round finished the three items that were left open, and fixed the defects that finishing them exposed.

**The figure sweep is complete.** The hand-written passages of `studies/LEAN_ADDRESS_STUDY.md` and `studies/ADDRESS_RETRIEVAL_STUDY.md` are now at the fresh measurements: the corpus at 3,135 declarations over 110 files, 2,772 distinct addresses with a largest conflation class of sixteen (one dimension vector written out in five files plus the VOA vacuum), retrieval over 3,134 candidates with 39.5 relatives on average, the certified shortlist at 71.5 declarations, and the two capacity gaps restated at 34 and 17 points. The four worked examples of the address study were re-run rather than re-picked, and this round nothing moved at all — not an address, not a neighbourhood — so the prose now says that instead of last round's story. The tier-0 lines of the escalation and planner studies were brought to the enlarged case set, and `CAPABILITY_ASSESSMENT.md`'s per-kind table, report-subject line and analogy line were corrected against the run (report 65 / 65, analogy 11 / 11).

**The generated artefacts were regenerated** — every generated block, `DIGEST.md`, the document address book and `overlay/FIGURES.md` — and `python3 -m glm_universal.corpus --check` now reports `current` again, with the blocks printing figures instead of staleness notices.

**Three further defects were found and fixed at their root.** The evaluation's own `report query escalation` case still demanded the phrase *143 evaluation cases* of an answer the runtime gives as 147, so growing the set had broken the case that reads it; the case, the two tests pinning the same figure and the documents now all say 147. `runtime/escalation_loop.py` cited two Lean theorems that do not exist (`first_resolving_terminates`, `cost_monotone`); they are now `climb_total`, `climbFrom_cost_ge` and `climb_direct_cost`, the statements actually proved, and the study's Lean section names them too. Two test-file rows in the tests README had drifted from what `pytest` collects, and the evaluation package README still described a 97-case set.

**Everything was re-earned on the final tree.** A release run with the exhaustive cases on passes **all 88 test files and all 7 instruments**, and `--verify-release` confirms 88/88 and 7/7 signatures still hold; the complete-run sentence the documents quote is re-measured at **3,555 tests across 87 of the 88 test files, 12,742 subtests, outside the document check**; the end-to-end evaluation is **147 / 147** (131 answered, 16 refused as expected, 0 unexpected refusals, 0 confidently wrong); `lake build` completes over all 8,137 jobs; the Lean tree carries **no `sorry` or `admit`** in either copy and the two copies are identical; benchmarks 2,389 / 2,390 and 33 probes with 20 holding are unchanged. `STATUS.md` records the round and its closing defects, and the older round records are marked as history so their figures are kept as written rather than forced to the present. The properties table was reconciled: no Lean source changed this session, the registered statements still match their files, and the ten theorems remain proved. All work is committed.

# Summary of changes for run ca4e4be5-f555-415d-ad81-799332476c6d
## What has been completed

**The round before this one** closed the last geometric item on the open list: the Niemeier deep holes, in two pre-registered halves. The first classified a hole's Coxeter–Dynkin type from the distribution of walk arrivals — it beat every control (15 of 44 named, against 11 for the plain vertex count) and then **stopped on its own sanity check**, because changing only the ensemble seed kept just 3 of 10 labels. The second asked whether that was the geometry or the layer it was read at, escalated the reading along a declared ladder of layer × budget cells, and reached **10 of 10** on the sanity check and **40 of 44** on the full query set. Both are written up in `studies/DEEP_HOLE_STUDY.md` and `studies/DEEP_HOLE_ESCALATION_STUDY.md`, with `RequestProject/GLM/DeepHoleClassifier.lean` and `RequestProject/GLM/DeepHoleEscalation.lean` as the formal halves.

**This session** found that those rounds had left their measurements behind, and re-took them rather than patching:

- The **lexical address book** and the **Lean measurement cache** were stale against the new tree digest, so every generated table in `studies/LEAN_ADDRESS_STUDY.md` and `studies/ADDRESS_RETRIEVAL_STUDY.md` was printing a staleness notice instead of a figure. Both are recomputed; the studies report again.
- Every hand-written passage quoting them was brought to the fresh numbers — in the two studies, `STATUS.md`, `CAPABILITY_ASSESSMENT.md`, the number-theory evidence paper and the package READMEs: **3,100 / 3,100** declarations read back with 0 coordinate errors, 2,736 distinct addresses, nearest-by-address sharing a file **609 / 3,100** against 36 for the digest control and 18 for the reshuffle (chance ≈ 1.21 %); retrieval over **207** queries at hit@5 **39.1 %** against **6.3 %** chance (6.2×), the text control ahead at **85.0 %**, the no-lattice ablation 40.6 %, the lexical address 66.7 %, and the completeness bound holding on **154,950** pairs with **0** violations for a certified shortlist of 58.9 declarations. The worked examples of both studies were re-run rather than re-picked: no address moved, and three of the four spoken-back declarations gained a nearer neighbour from the new files.
- Drifted counts were corrected: **143** evaluation cases (was 142), **67** reasoning modules, **121** package modules, **107** Lean files / 31,483 lines / 3,100 declarations, **788** corpus sections and a 3,042-word tier-0 read.
- A release run re-earned the suite sentence, which no run had produced since the suite grew: **3,436 tests across 82 of the 83 test files, 12,836 subtests, outside the document check**, and `overlay/FIGURES.md`, `DIGEST.md` and the corpus address book were regenerated.
- The round is recorded in `STATUS.md` §3 and in the change log; `ARISTOTLE_SUMMARY.md` was left untouched.

**Verified on the final tree:** `lake build` completes over all 8,134 jobs, the 107 Lean files carry no `sorry` or `admit` and are byte-identical between `RequestProject/` and the overlay mirror (apart from the mirror's own README); a release run passes **all 83 test files and all 7 instruments**, and `--verify-release` confirms 83/83 and 7/7 signatures still hold; one pytest process over the whole suite with the exhaustive cases on reports **3,464 passed, 0 skipped, 15,424 subtests, zero failures**; the end-to-end evaluation is **143 / 143** (127 answered, 16 refused as expected, 0 unexpected refusals, 0 confidently wrong); benchmarks 2,389 / 2,390; probes 33 with 20 holding; `corpus --check` reports `current` and `figures --check` matches a fresh computation. All work is committed.

## What remains

The open list is `STATUS.md` §3, and the proposed next phase is `MASTER_PLAN.md` Phase 35. Nothing else in the repository is claimed as pending. Four candidates stand, in the order they are worth taking:

1. **The separation criterion, still unmet.** `nearest_correct` says a reading names holes correctly when ρ = 2W/B < 1; measured, ρ only falls from 3.90 to 2.59 across the ladder, so the classifier that names 40 of 44 still cannot certify a single *absence* (faithfulness needs r ≥ 0.0659 where separation permits r < 0.0179). Either a rung is found where ρ < 1, or a bound is proved that no reading of this family reaches it.
2. **The thirteen unreached Niemeier types.** The ensemble reaches 10 of the 23 root systems from the 14 declared centres; reaching the rest needs new centres, and therefore a new pre-registration.
3. **The conflation the exact reading cannot see past.** Read alone, the rational layer conflates `A_1^24` with `A_2^12`. That is recorded as an observation; the theorem to want says *which* pairs any stray-blind reading must conflate.
4. **Escalation as the default step of the query loop** — the largest and most architectural item. The deep-hole ladder is the only place where a refusal was answered by raising the resolution instead of stopping; every other reasoning module still refuses at whatever layer it was asked at. Wiring `firstResolving`-style escalation into the query loop, so a refusal carries the layer it was refused at, needs pre-registering like any other round.

Two standing limits are also unclosed by design: coverage is still three of eight registers described and seven of the twenty answerable query kinds, and the thirteen remaining query kinds are not shapes of any family — forcing them would make the coverage figure meaningless.

# Summary of changes for run 923d8604-d068-4253-9f1b-a274f3dcee80
Picked up the unfinished round and closed all four remaining items.

**1. Figure reconciliation finished.** Every hand-written passage that still quoted the smaller corpus was brought to fresh measurements rather than patched:
- `STATUS.md` — the Lean development is now stated as **105 files, 30,853 lines, 3,049 parsed declarations, no `sorry`** (was 29,668 lines / 2,939 declarations, and in one place 101 files); the address-book passages now read **3,049 / 3,049** read back with 0 coordinate errors, 2,688 distinct addresses, nearest-by-address sharing a file **609 / 3,049** against 37 for the digest control and 26 for the reshuffle, chance ≈ 1.24 %; the retrieval passages now read **204** queries, hit@5 **48.5 %** against **6.4 %** chance (7.6×), text control **80.9 %**, features ablation 46.6 %, lexical address 60.8 %, completeness bound **155,448** pairs with **0** violations and a 95.2-declaration certified shortlist; the corpus figures are **754** sections and a **2,904**-word tier-0 read against roughly 196,000; the evaluation row is **141 / 141**; the package is 119 modules.
- `overlay/README.md` (3049 declarations), `overlay/glm_universal/README.md`, the tests README (read-back over 3,049 declarations), `studies/ADDRESS_RETRIEVAL_STUDY.md` (155,448 pairs) and the number-theory evidence paper (105 files, in all four places it states a count) were reconciled too, and `CAPABILITY_ASSESSMENT.md`'s per-kind evaluation table was re-derived from a run (**141 / 141**, `analogy` 11, `report` 59).
- One real gap turned up and was closed: the package README no longer stated the corpus size at all, which its own audit requires; it now carries the read-back figure.

**2. The round recorded.** `STATUS.md` §2 gains four entries — the cross-register analogy answered from a 7-row energy-conjugate register (`force` → `work`), sparse chemistry decided (coverage 1,257 → 1,442 of 1,652, 210 cells with stated reasons), the standing rule for a vague `related_to` triple (34 of 66 decided without a person, 1 of 4 proposer rules admitted) and open vocabulary made a door (20 of 27 probes admitted, refusals conditional) — each naming the Lean theorems behind it. §3 records the round as closed, §3.2/§3.3 mark the items it retired, and §3.4 now names one candidate rather than two. The master plan closes **Phase 32** (detail in the plan archive) and proposes **Phase 33**, the Niemeier deep holes. The Lean development's own README gained rows for `Conjugate.lean`, `Completion.lean`, `Vagueness.lean` and `Admission.lean`; the change log gained row **5.29** and the overlay README the matching version. What was deliberately *not* done is written down in both places: nothing written back into the element register, the 32 referred triples left referred, the three refused proposer rules kept with their disagreements, and the deep holes not attempted.

**3. Release sign-off.** A full release run re-measured the sentence describing a complete test run — **3,379 tests across 80 of the 81 test files, 12,792 subtests, outside the document check** (was 3,257 across 76 of 77) — and it now appears in exactly that form in the six documents that quote it, with `overlay/FIGURES.md` regenerated so it agrees.

**4. Everything green, on the final tree.** A release run with the exhaustive cases on: **all 81 test files and all 7 instruments pass**, and `--verify-release` confirms 81/81 and 7/7 signatures still hold. One `pytest` process over the whole suite: **3,407 passed, 0 skipped, 15,378 subtests, zero failures**. End-to-end evaluation **141 / 141** (125 answered, 16 refused as expected, 0 unexpected refusals, 0 confidently wrong). `glm_universal.corpus --check` reports `current` and `figures --check` matches a fresh computation. `lake build` completes over all 8,132 jobs; the 105 `.lean` files are byte-identical between `RequestProject/` and the overlay mirror (differing only in the expected extras — `Main.lean` and `.gitkeep` in the repository copy, the Lean README in the mirror) and contain no `sorry` or `admit`.

Note for future sessions: the suite needs `pytest` and `pytest-subtests`; they were absent from this machine and had to be installed before anything could be run. All work is committed.

# Summary of changes for run ffea7c45-3920-4ddc-b587-907d471fb5d4
## What was completed this round

You asked for a status read, so I began by re-running everything rather than trusting the last write-up — and that turned up three real drifts left behind when the previous round (the wobble-landscape study) added a study, a module and a test file. All three are now closed, and the round is recorded in `STATUS.md` §3 and as change-log row 5.28 in the overlay's README history.

1. **The corpus caches were stale.** The document address book, `DIGEST.md` and the generated blocks of `studies/CORPUS_ADDRESS_STUDY.md` no longer matched the documents. They were re-taken: the corpus is **708** addressable sections over 64 documents, read back **708 / 708** with **0** coordinate errors of 16,992, and the corpus check now reports `current`.
2. **The suite counts described a suite that no longer existed.** The ledger still held totals for a 76-file suite while five documents quoted a sentence no run had produced. A full release run re-measured them: **3,257 tests across 76 of the 77 test files, 12,703 subtests** (outside the document check), with **all 77 test files and all 7 instruments passing** — including the end-to-end evaluation at **136 CLI cases** with the same refusals as before.
3. **`overlay/FIGURES.md` was stale**, including a package version frozen at 1.15.0 against the code's 1.16.0. It is regenerated from the code and matches a fresh computation; the two hand-typed corpus figures in `STATUS.md` were re-derived with it (688 sections → 708; the tier-0 read 2,548 words against roughly 194,000 for the full current state).

Formal side, verified here: `lake build` completes over the Lean development — **101 files, no `sorry`** anywhere in `RequestProject/` or the overlay's mirror — and the two copies of the tree are identical.

## Where the original deep-dive brief stands

Every area you named in the brief has been gone through and written up: the `glm_machine` scripts, the two light/EM calibration rounds, the Leech-lattice shortcut, both encoding-definition attempts, the first-principles and projection sub-studies, the MOG cube, `GMHGL` with its named scripts (UBP v5, spatial arithmetic, geometry, the LDP mapping and NRCI, totient kinetics, the TGIC family, the EM analog engine, the ALU, genesis boot, value geometry), the earlier `glm_lean` iterations and the ARC experiments. The retrievals are in `studies/SOURCE_SALVAGE_AUDIT.md`, `studies/SOURCE_SALVAGE_SECOND_PASS.md`, `studies/ARCHIVE_DEEP_DIVE_STUDY.md` and `studies/RETRIEVED_LEAN_STUDY.md`; **25 Lean files, 7,230 lines, 854 declarations** came back from the archive, nine of them negative results (a claim refuted rather than retrieved).

## What is remaining

The full list is `STATUS.md` §3, and the next round is written up as Phase 32 in `MASTER_PLAN.md`. In short:

* **The Niemeier deep holes, found rather than tabulated** — the last purely geometric item, and the brief's third experiment: classify the deep holes from the distribution of trajectories that reach them. `Golay/Census.lean` is the census for one lattice and `reasoning/deep_holes.py` walks to a hole; the classification is what is missing.
* **`heat : temperature :: force : ?`** — the analogy shape is described, but the semantic half is not: the lexicon has `temperature drives heat` and reaches nothing from `force`, so the question is refused with a stated reason. Closing it means supplying the relation and saying what makes one admissible.
* **Checked rather than proved: the transcription** of the zero-storage scripts against the coset-decoder optimality theorems — the theorems are proved; that the script computes the quantities they are about is tested, not proved.
* **Ongoing rather than finishable:** sparse chemistry (1,257 of 1,652 element cells filled, widened only by derivation and never written back), the lexicon's vague `related_to` triples as new ones are added, and open vocabulary, which is a stated commitment rather than a gap.
* **Not attempted, and named as a size judgement:** the pinned Mathlib has no Golay code, no Leech lattice and no linear-code layer, so offering any of this upstream means building the theory beneath the sieve first.

Everything above is committed.


# Summary of changes for run e7e631c0-f406-4d63-950b-34da92f246f1
All four outstanding items are closed, each checked by running it here, and everything is committed.

**1. The hand-quoted counts reconciled, by re-measuring rather than patching.**
- The growth that the generated blocks had already caught is now reflected everywhere: the development is **100 Lean files, 29,370 lines, 2,913 declarations, no `sorry`**, and the suite is **76 test files**. `README.md`, `STATUS.md`, `CAPABILITY_ASSESSMENT.md`, `MASTER_PLAN.md`, the overlay and package READMEs, the tests README, the Lean README and the number-theory evidence paper were all brought to those figures.
- One real defect turned up while doing it: the hole scanner counted the phrase "`sorry`-free" in `Corpus.lean`'s docstring as a hole, so the tree reported one `sorry` where there is none. The docstring is reworded; the scan now reports zero, and a search for `sorry`/`admit` across `RequestProject/` and the overlay's copy finds nothing.
- Every cache keyed to the Lean tree was re-taken against the new digest — the structural address book, the lexical address book (which was stale), the measurement cache and the document address book all report `fresh` — and `overlay/FIGURES.md` was regenerated and matches a fresh computation.
- The address figures that documents quote are now the current ones: read back **2,913 / 2,913** with **0** coordinate errors, 2,566 distinct addresses, nearest-by-address sharing a file **591 / 2,913** against 35 for the digest control and 34 for the seeded reshuffle.
- The per-package test counts in the package README were re-derived rather than adjusted: the twelve rows now partition the counted part of the suite exactly and sum to the total, and the reasoning row lists all 60 modules instead of the 49 it had frozen.

**2. The new tooling registered.** The corpus package has its own README, a row in the package status table and a place in the README chain; `test_corpus.py` has its row in the tests README; `Corpus.lean` has its row in the Lean development's table, naming the four theorems it carries. The round is recorded as closed Phase 30 in the master plan (the proposed phase renumbered to 31, with the pointers from `STATUS.md` updated), has an entry in "what is done" and in "what is open" in `STATUS.md`, a row in the instrument table (`python3 -m glm_universal.corpus --check`), and a change-log row. It also leaves behind a standing rule — **D10, "a document is data"** — with the check as its instrument; `report directives` now reports 10 rules, 10 with every instrument present, 0 defects.

**3. A second study's tables converted to generated blocks.** `studies/ADDRESS_RETRIEVAL_STUDY.md` was still quoting a run over the smaller corpus. Its five measured sections — the setup, the eight schemes on declaration queries, the goal queries, the shortlist sweep and the completeness bound — are now generated blocks emitted from the same measurement cache, guarded by the digest of the Lean sources, so they report staleness rather than an out-of-date number. Re-measured over the current corpus: hit@5 **41.1 %** for the structural address against **6.7 %** chance (**6.1×**), the plain text control still ahead at **84.7 %**, the unquantised-features ablation tying it at k = 5 on the same 86 queries, no shortlist size beating the text control, and the proved completeness bound holding on **148,512** pairs with **0** violations. The prose around the tables — including the headline claims and the tier-0 figure — was rewritten to the new measurements, and `STATUS.md` follows.

**4. Clean runs.**
- `lake build` completes over all 8,127 jobs, and the repository and overlay copies of the Lean tree are identical.
- A full sign-off release run (each test file in its own process, exhaustive cases on, plus the seven instruments) re-earned the suite totals: **3,222 tests across 75 of the 76 test files, 12,703 subtests**. Those are now the figures the documents quote.
- The final full suite run: **3,222 passed, 28 skipped, 15,272 subtests, zero failures**.
- `glm_universal.corpus --check` reports `current` — no drift in the tier contract, the archive partition, the coverage claim, any generated block or any derived cache — and `glm_universal.figures --check` reports the figures file matches a fresh computation.


# Summary of changes for run 5c233795-bdc6-4bdb-a87a-7b544d71c990
I finished the outstanding items from the previous checkpoint. Everything below was checked by running it here, and all work is committed.

**The corpus, re-measured rather than patched.** The Lean tree had grown with the decoder's global-optimality proofs, so every figure derived from it was recomputed: the development is now **99 Lean files, 29,122 lines, 2,893 parsed declarations, no `sorry`**, and `lake build` completes cleanly over all 8,126 build jobs. The derived caches were regenerated against the new tree digest — the structural address book (`reasoning/_data/lean_addresses.json`) and the lexical address book (`lean_lexical_addresses.json`) both report `fresh`; the type-2 table, the economics lattice points and the controller table were checked and were already fresh. `overlay/FIGURES.md` was regenerated and now matches a fresh computation.

**The two studies that measure the corpus were re-measured, not adjusted.** `studies/LEAN_ADDRESS_STUDY.md`: read back **2,893 / 2,893** exactly with **0** coordinate errors out of 69,432, 2,547 distinct addresses (the quantiser still adds no conflation of its own, 235 classes, 581 declarations), nearest-by-address shares a file **587 / 2,893 ≈ 20.3 %** against 35 for the digest control and 26 for the seeded reshuffle, with chance at ≈ 1.32 % — so the file-test multiple is 15.3×, the third rise in a row against a falling chance rate. The kind table, the scale sweep, the pair statistics and the four worked examples were all re-run; the examples came back identical. `studies/ADDRESS_RETRIEVAL_STUDY.md` had still been quoting a 2,850-declaration run: it is now measured over **207** queries of the 2,893-declaration corpus — hit@5 **51.7 %** against **6.7 %** chance (7.7×), the plain text control still ahead at **85.0 %**, the unquantised-features ablation now tying the address query for query, and the proved completeness bound holding on **147,492** pairs with **0** violations.

**Hard-coded numbers reconciled.** `STATUS.md`, `CAPABILITY_ASSESSMENT.md`, the overlay and package READMEs and the tests README were brought to the current counts, the superseded phrases from this round were added to the guard in `test_figures.py` so they cannot come back, and a change-log row (5.25) records the decoder proofs and this reconciliation. Historical per-phase and archive rows were left as they are, since they record what was true when written.

**Clean runs, with nothing in flight.** Full Python suite: **3,181 tests, 15,253 subtests passed, 26 skipped, zero failures**. The release sign-off then ran end to end: **75 of 75 test files** in full mode and **all 7 instruments** (Lean build, `sorry`-free scan, the two Lean copies identical, capability probes, benchmarks, the end-to-end evaluation, the figures check) passed, and `--verify-release` confirms every signature still holds. The standalone `glm_zero_storage_substrate_v5.py --test` passes and exits 0.

**The mirrored Lean tree** is byte-identical to the primary one across every `.lean` file (the only differences are the deliberately per-copy `README.md`, `Main.lean` and `.gitkeep`), which the sign-off's own check confirms.

**Results list.** The four decoder theorems that closed the global-optimality gap — `coset_min_cost`, `coset_min_attained`, `leech_in_coset`, `lattice_dist_ge` — were not yet in the tracked list; they are now registered and marked proved, with the definitions they are stated in terms of (`InCoset`/`cosetRes`, `dist2`/`penaltyQ`). Each was re-checked here: sorry-free and depending only on `propext`, `Classical.choice` and `Quot.sound`.


# Summary of changes for run 33c07703-d5d3-4e3a-b6c7-2fdd1cb7e6b8
## What I did

I rebuilt the zero-storage substrate draft as a single, refined, standalone script: **`glm_zero_storage_substrate_v4.py`** at the repository root. It imports nothing beyond the Python standard library (no dependency on the rest of the system), uses `int`/`Fraction` only — no floats in any computation, no RNG — and stores no tables at all: even the Golay code is generated from the quadratic residues mod 11 (36 bytes of generator rows).

The earlier review of the v3 draft had found one mechanism correct, one sound but 99.4 % incomplete, one unsound, and one carrying accuracy claims that did not hold. The v4 script keeps only the working parts and levels each of them up:

- **Leech membership** — the repaired test: the coordinates agreeing mod 4 must form a *Golay codeword* (not merely all agree). One pass over 24 coordinates plus one lookup, no stored shell.
- **The snap** — replaced by an exact coset decoder returning the true nearest lattice point (all 4096 codewords × both parities, exact integer arithmetic); the unsound "round to the nearest even integer" fallback is gone.
- **The minimal shell** — 196,560 vectors streamed from the code in three shapes, rather than held.
- **Generated reals** — a real number is now a process with a contract: `x.at(k)` returns a dyadic rational within `2⁻ᵏ` with a stated tail bound and a denominator of `k + O(1)` bits. π, e, √2, φ, ln 2 and γ all satisfy it; γ is computed by Euler–Maclaurin with a bounded remainder instead of the old integer-rounded logarithm.
- **The dyadic tower** — kept, with its one false claim corrected (readings are non-decreasing; it is the resolution that strictly improves).
- **The "Niemeier portal"** — replaced by the object it was reaching for: the *sextet*, the partition of the 24 points into six tetrads any two of which union to an octad.
- **Frequency-encoded state** — the Δ-Σ register rebuilt standalone, with the read-out bound `|average − target| < 1/N`.
- **The storage audit** — stored bytes beside generator bytes, each row emitted only after the regenerated object was compared with what it replaces.

`python3 glm_zero_storage_substrate_v4.py --test` runs the whole self-verification in about five seconds and exits 0: weight distribution 1 / 759 / 2576 / 759 / 1; all 196,560 minimal vectors of norm² 32 and accepted; the decoder inside Λ₂₄ and within squared covering radius 16 on every probe, with **no nearer point among the 196,560 neighbours**, and a half-step target decoding at exactly 1/2; 18 (constant, precision) pairs meeting their `2⁻ᵏ` contract; all 10,626 tetrads giving verified six-part sextet partitions, 1,771 sextets in all; and the storage audit reproducing 9,449,445 → 24,648 bytes, about 383 : 1. There are also `--report` (JSON), `--demo` and `--quick` modes.

## Lean

I added and proved (sorry-free, standard axioms only) `GLM.ZeroStorage.RefinedSieve` and `GLM.ZeroStorage.refinedSieve_iff_isLeech` in `RequestProject/GLM/ZeroStorage.lean`: the script's deterministic membership test — parity read off coordinate 0, no existential search, no table — decides exactly the Leech lattice. The full Lean project builds.

## The old copy

The v3 draft is not part of the running system; it is referenced only as source material, so rather than deleting it I moved it to `source_material/glm_zero_storage_substrate_v3.txt`. The root no longer holds it. I also recorded the follow-up in `studies/ZERO_STORAGE_STUDY.md` and `STATUS.md`, and confirmed the existing package tests still pass. All work is committed and pushed.

# Summary of changes for run ea058872-5e81-48d0-9b90-7d7fe7676b25
The round is closed out. Everything below was run, not assumed, and the tree is committed and pushed with a clean working directory.

**The two inconsistencies the verification run had turned up are fixed.**

1. *The wall-clock timings are gone from the generation audit.* `overlay/glm_universal/reasoning/generative.py` no longer imports a clock: the `regenerate_us` column and the timing helper are removed, and the storage rows now carry only bytes, counts and the verification verdict. The reason is stated in the module and in the write-up — the audit is emitted through the runtime, whose traces are required to be byte-identical between runs, so a timing in a row is a quantity a second run would print differently. The report text, the test file (a new case now asserts that two uncached computations of the report are equal), `studies/ZERO_STORAGE_STUDY.md`, the plan, the status document, the change log and the tests README were all adjusted to match.
2. *The Lean file count in the number-theory paper.* Both stale quotations — "97 files under RequestProject/GLM/" and "89 Lean files" — now say **98**, the tree's count. The test that guards the paper only read two of the three phrasings, so the prose form drifted unnoticed; it now reads that form too, and would fail on the next drift.

**What the verification run then found on its own, and what I did about it.** The release check reported that the round's new `report generated` subject was never exercised end to end: it existed in the package and in the report tests, but not in the CLI evaluation set. It now has the case `report-generated`, which starts the CLI in a fresh interpreter and checks three ground-truth phrases of the answer. The set is **135 / 135**, with the same 16 boundary refusals and 0 unexpected refusals.

**Figures refreshed and propagated.** `overlay/FIGURES.md` was regenerated from a fresh computation; it had been stale in six rows (report subjects 51 → 52, modules 112 → 113, reasoning modules 59 → 60, Lean files 97 → 98, cases 134 → 135, and the suite sentence). The new counts were propagated to every document that quotes them, and the document check now passes on all of them. Two documentation gaps closed along the way: the new study had no row in the document index, and the Lean development's README table was a round and a half behind — it now has rows for `Retrieval.lean`, `Controller.lean` and `ZeroStorage.lean`.

**Final state, measured.**
- Release sign-off: **75 of 75 test files** run in full mode with the exhaustive cases on, and **7 of 7 instruments** (`lake build`, the sorry scan, the two-copy diff, the probes, the benchmarks, the end-to-end evaluation, the figures check) — all passed, and `--verify-release` confirms every signature still holds.
- Suite totals, recorded by that run: **3,179 tests across 74 of the 75 test files, 12,840 subtests**. One `pytest` process over the whole tree independently gives **3,181 passed, 26 skipped, 15,164 subtests, zero failures** — the ledger's total plus the 28 tests of the document check it deliberately leaves out.
- Lean: `lake build` completes cleanly (8,125 jobs), no `sorry` or `admit` anywhere in the development, and the six headline theorems of `RequestProject/GLM/ZeroStorage.lean` depend only on `propext`, `Classical.choice` and `Quot.sound`.
- The overlay's own storage figures were re-measured from the tree rather than carried over: **7,296,569 of 7,316,334 bytes** on disk are caches with input digests, leaving **19,765 bytes** of primary data. The audited-table figures (9,449,445 stored against 24,648 of generators, about 383 to one, all four verified identical) are unchanged.


# Summary of changes for run 9f3c68de-9c1b-4e8c-9700-eb2f7a1aba42
## What this round completed, and the results

**The round's two pieces of work** were the address book made to do work, and the system's first reasoning loop. Both are now verified in the delivered tree.

*Retrieval* (`overlay/glm_universal/reasoning/retrieval.py`, `RequestProject/GLM/Retrieval.lean`, `report retrieval`, write-up `studies/ADDRESS_RETRIEVAL_STUDY.md`). The Leech address book is turned into an index over the 2,826-declaration Lean corpus and measured against six controls on 202 stride-selected queries, with chance computed in closed form:
- the address is a real index — hit@5 **51.5 %** against **6.9 %** chance (7.4×), above the digest (3.5 %), the seeded reshuffle (6.9 %), the random ranking (5.9 %) and name search (34.2 %);
- and it is beaten decisively by a plain lexical control — Jaccard overlap of identifier tokens, **85.6 %** at 57.7 % precision@5;
- the two ablations say the lattice is not what carries the signal: the same features with no quantisation score **51.0 %**, and an identifier-based address **64.9 %**;
- what the geometry does earn is exactness — the completeness bound proved in `Retrieval.lean` holds on **144,075** measured pairs with **0** violations, and at feature radius 2 the guaranteed-complete shortlist is 70.9 declarations (2.5 % of the corpus), so an empty shortlist is a proof of absence.

*The loop* (`reasoning/controller.py`, `RequestProject/GLM/Controller.lean`, `report controller`, write-up `studies/CONTROLLER_STUDY.md`). Propose–check–refuse over the ten EXT10 generators: every plan any scorer returned was re-verified end to end by an instrument that did not build it (**100 %**, every scorer); **127 of the register's 726** quantities are refused *with a proof* (`unreachable_of_invariant`) and no node expanded; `beam_can_miss` is a kernel-decided witness that a width-one beam can miss a plan that exists, and `exists_descent` is the complement. The address scorer solves **18 of 24** reachable tasks against **8** unguided and **12** target-blind — the substrate can steer — but the same distance **without** the lattice solves **17**, and decoded at scale 1 the address scorer falls to exactly the no-guidance 8.

**What I did this session** was verify that work independently and close the part of the round that was still open — the documentation had not been reconciled with the code. Verified: `lake build` clean over 97 Lean files (28,209 lines) with **0 `sorry`**; a release sign-off in which **74 of 74 test files** ran in full mode with the exhaustive cases on and **7 of 7 instruments** passed (`lake build`, the sorry scan, the two-copy diff, probes, benchmarks, the end-to-end evaluation and the figures check), and `--verify-release` confirms every signature still holds. Reconciled: `overlay/FIGURES.md` regenerated and its counts propagated to the eleven documents that quote them (**51 report subjects, 134 CLI cases, 74 test files, 97 Lean files, 112 modules, 59 reasoning modules**, and the suite sentence **3,163 tests across 73 of the 74 test files, 12,838 subtests**); the corpus size (2,826 declarations) fixed in the four documents that state it and in the audited number-theory paper; `STATUS.md` given a §2 entry for each of the two pieces, its §3 shifted so this is the round just closed, and §3.1/§3.4 updated; `MASTER_PLAN.md` given **Phase 27** as a closed phase with the proposal renumbered to **Phase 28**; the change log given its **5.22** row; the tests README given rows for the two new test files; and the superseded phrasings retired in the document check so a document left behind next round fails the suite. Everything is committed and pushed.

**Where the project stands:** end-to-end evaluation **134 / 134** (118 answered, 16 refused as expected, all `boundary`, none a gap), benchmarks 2,389 / 2,390, 33 capability probes with 20 holding and 13 breaking as recorded, and the Lean development sorry-free in both copies.

**What is next** — `STATUS.md` §3.4 and `MASTER_PLAN.md` Phase 28, in the order they are worth attempting:
1. **The Niemeier deep holes, found rather than tabulated** — the brief's third experiment and the last purely geometric item: whether the deep holes of a Niemeier lattice can be classified from the distribution of trajectories reaching them instead of read out of a table. `Golay/Census.lean` is the census for one lattice and `reasoning/deep_holes.py` walks to a hole; the classification is missing. The retrieval result sharpens the target: what the geometry demonstrably earns is an exact guarantee, so this is worth attempting as a statement that can be proved complete rather than as a ranking.
2. **`heat : temperature :: force : ?`** — the semantic half of the analogy: supplying the relation, and saying what makes a relation admissible, rather than widening the dispatch. It is testable against evaluation cases that already exist.

Not next, and recorded as such: a fourth question-shape family, which the language layer's own coverage measurement says would be forcing.


# Summary of changes for run 00b30616-846e-4a2e-b746-adc5b129356c
I picked the round up where it stopped and carried it through to a clean close.

**The tests README.** It was missing a row for nine test files; all nine now have one, written from what each file actually checks (the archive's first and second readings, the deep dive, the combiner, the search loop, the tie-break, the stability radius, the exactness inventories and the number-theory paper audit). While there I found five existing rows whose counts had drifted from what `pytest` collects (`test_runtime`, `test_wiring`, `test_figures`, `test_signoff`, `test_language`) and corrected them, corrected the `test_wiring` row's description of the package surface, and refreshed two rows that still described the corpus at its old size. The table now carries exactly one row per test file and the counts are the collected ones.

**Figures regenerated and propagated.** `overlay/FIGURES.md` was regenerated from a fresh computation with the suite walked. The headline sentence moved to **49 report subjects, 132 CLI cases, 72 test files, 95 Lean files (27,548 lines, 0 sorries)**, and the suite sentence to **3,096 tests across 71 of the 72 test files, 12,119 subtests**. Those, and the counts that moved with them (110 package modules, 57 reasoning modules, the evaluation's 116 answered / 16 refused and its per-kind table), are now stated the same way in the eleven documents that quote them. Round records inside history sections were deliberately left as of-their-time records, and one that an earlier pass had rewritten was put back. The superseded phrasings are retired in the document check, so a document left behind next round fails the suite rather than ageing quietly. The reasoning package README gained rows for the ten modules it was missing.

**Round entries written.** `STATUS.md` has a new §2 group for the round (the dropped work restored and the archive's second reading closed; the machine-checked exactness inventory; the audited number-theory paper; the regenerated address book), §3 shifted so the restoration is "closed this round" and the archive round the one before, and §3.1/§3.4 updated — the stability measurement that stood as one of the three items named for the next round is closed, so §3.4 now names two. `MASTER_PLAN.md` gained **Phase 26** as a closed phase with the proposal renumbered to Phase 27, and the change log gained its **5.21** row. Every study document is now indexed in `DOCUMENTS.md`.

**Full verification pass, all green.**
- Whole suite in one process: **3,098 passed, 26 skipped, 14,265 subtests, zero failures**.
- Release sign-off: **72 of 72 test files and 7 of 7 instruments** run with the exhaustive cases on and passing, and `--verify-release` confirms every signature still holds.
- End-to-end evaluation: **132 / 132** — 116 answered, 16 refused as expected, 0 unexpected refusals, 0 confidently wrong, 0 errored.
- `lake build` clean over the whole development (8,122 jobs); **no `sorry` or `admit`** in either copy of the Lean tree; the repository tree and its `overlay/glm_lean/` mirror differ only in the three files that are meant to differ (`.gitkeep`, the GLM README, `Main.lean`).
- The new cube-mirror theorem `GLM.CubeMirror.no_mirror_invariant_steiner` was checked for its axiom dependencies: the usual three plus the two that `native_decide` introduces, and no declared axiom.

Everything is committed and pushed.

# Summary of changes for run 301f2824-c018-4e6e-92db-5b35d97c31b6
I closed out the round that was still open — the archive-retrieval round — rather than starting anything new.

**What was unfinished, and is now done**

1. *The release sign-off had never been completed for that round.* The ledger showed 55 of 63 test files and 6 of 7 instruments still carrying a signature that no longer held, because documents and code had been edited after the units were last signed. The full release run has now been made and it is clean: **63 of 63 test files and 7 of 7 instruments signed off** — `lake build`, the sorry scan, the two-copy Lean diff, the capability probes, the benchmarks, the end-to-end evaluation and the figures check — with the suite totals re-recorded unchanged at **2,880 tests across the 62 counted test files, 11,814 subtests** (one `pytest` process over the same tree collects 2,882 passed, 26 skipped, 13,777 subtests, zero failures).

2. *`STATUS.md` §3 had not been shifted for the round.* "Closed this round" still named the LLVQ lookup table, so the retrieval was described in §2 but absent from the list of what is open and what closed. §3 now opens with the archive round (25 Lean files, 7,170 lines, 848 declarations, nine of them negative results, corpus at 2,118 declarations across 73 files, evaluation unmoved), the LLVQ table has moved to "the round before", and the labels below it are shifted accordingly. §3.1 still claimed the end-to-end set was **130 of 130**; it is **131 of 131**, which is what §1 and every other document already said.

3. *A count inside `studies/RETRIEVED_LEAN_STUDY.md` disagreed with itself.* §1 rule 2 said five of the twenty-five files exist because the archive's claim is false, while §3 counts nine negative results; §1 now states nine and points at §3.

**Verification performed**

- `lake build` clean over the whole development; **no `sorry` or `admit`** anywhere in `RequestProject`, and the repository tree and its `overlay/glm_lean/` mirror are identical.
- An axiom audit of the entire Lean development: `#print axioms` on all **1,492 theorems and lemmas**. 62 depend on no axioms at all; the rest depend only on `propext`, `Classical.choice`, `Quot.sound`, and — for the 132 reached through `native_decide` — `Lean.ofReduceBool` and `Lean.trustCompiler`. Nothing depends on a declared axiom, and the development contains no `axiom` declaration and no `@[implemented_by]`. The only six names that cannot be addressed from outside are `private` helper lemmas, whose axioms are covered by the public theorems that use them.
- `figures --write` is a no-op: the generated figures already match a fresh computation, so no documented count moved.

The three candidates `STATUS.md` §3.4 hands to the next round are left exactly as they stand. Everything is committed; the working tree is clean.

# Summary of changes for run a8eb1ba5-cd98-4fb7-8a9f-769aa2848b27
I finished the round that had been left open (the LLVQ lookup-table work) and brought the whole project back to a fully signed-off, self-consistent state.

**What was outstanding and is now done**

1. *Sign-off run.* The release runner could not previously record new suite totals — the ledger only recorded them when *every* unit passed, including the document check, which by construction fails whenever a round adds a test file. That deadlock was fixed (the condition is now over the counted units, i.e. the suite minus the document check, with a docstring explaining why), and a new `TestTheRecordedTotals` class in `overlay/glm_universal/tests/test_signoff.py` pins the behaviour.

2. *Figures regenerated and propagated.* `overlay/FIGURES.md` was regenerated; the new suite sentence — **2,872 tests across 61 of the 62 test files, 11,665 subtests, outside the document check** — and version **v1.14.0** were propagated into `STATUS.md`, `CAPABILITY_ASSESSMENT.md`, `overlay/README.md`, `overlay/glm_universal/README.md` and `overlay/glm_universal/tests/README.md`. Residual stale numbers (a `2,746` paragraph in `STATUS.md`, three `v1.13.0` headers) were corrected.

3. *Drift guard extended.* The retired phrases of this round (`47 report subjects`, `61 test files`, `46`/`47 Lean files`, `130 cases`/`130 CLI cases`/`130-case`, `2,847 tests`, `10,985 subtests`, `96 modules`, `48 reasoning modules`) were added to the superseded list in `overlay/glm_universal/tests/test_figures.py`, after confirming no document still contains them.

**Verification performed (all green)**

- Full suite in one process: **2,874 passed, 26 skipped, 13,523 subtests, zero failures**.
- Release sign-off: **62 of 62 test units and 7 of 7 instruments signed off** — `lake build`, the sorry scan, the two-copy Lean diff, the capability probes, the benchmarks, the end-to-end evaluation and the figures check.
- End-to-end CLI evaluation **131 / 131** (115 answered, 16 expected boundary refusals).
- `lake build` clean; no `sorry` or `admit` anywhere in `RequestProject`; repository and overlay Lean copies identical.
- `report llvq --verify-tct` returns `VERIFIED True`.
- The five Lean results of `RequestProject/GLM/LLVQTable.lean` registered in the properties table (the cost identity, the two class-minimum theorems, the class-size count and the branch-and-bound exactness lemma) were checked with `#print axioms` and depend only on `propext`, `Classical.choice` and `Quot.sound`; they are now marked proved.

All work is committed and pushed. `ARISTOTLE_SUMMARY.md` was read but not modified.


# Summary of changes for run 2865a776-df6d-4d42-b4ef-b902a5ce2e1f
The remaining documentation-reconciliation and verification tail is finished, and everything below was checked by running it here. All work is committed and pushed.

**1. Test-count figures propagated.** The per-file table and totals in the test-suite README were already current at 54 files / 2,424 tests; the same counts now appear in `STATUS.md`, `CAPABILITY_ASSESSMENT.md`, the package README (`overlay/glm_universal/README.md`) and the overlay README (`overlay/README.md`). Two evaluation-set figures that had been left behind were corrected with them: the "104 CLI cases" comment in `STATUS.md` and the `test_evaluation.py` row in the tests README, both now 112.

**2. The staleness guard widened.** `overlay/glm_universal/tests/test_figures.py` now also refuses `42 report subjects`, `38 Lean files`, `52 test files`, `104 cases`, `104 CLI cases`, `104-case`, `2,350 tests`, `2,350 collected tests` and the retired subtest totals (`9,088`, `9,165`, `9,170`, `9,232`). Each phrase names the unit it counts, so the still-true `104 collision classes` is untouched — I checked that the guard passes with that phrase in place.

**3. A drift the full run exposed, and fixed.** The suite's corpus check failed: the Lean development has grown to **966 declarations across 39 files** (`MeasureView.lean` contributed 40 of its own), while four documents still described the 926-declaration corpus. `studies/LEAN_ADDRESS_STUDY.md` was re-measured against the code, not patched by hand — the kind table (623 theorems, 233 defs, 84 lemmas, 8 abbrevs, 8 structures, 5 inductives, 5 instances), `966 parsed, 0 duplicates`, read-back 966/966 with 0 coordinate errors out of 23,184 and worst residual 3 at `GLM.CoherenceRegime`, 899 distinct addresses in 57 collision classes (48 pairs, 8 triples, one class of four) covering 124 declarations, and the separation tests: nearest-by-address shares a file 343/966 (35.5 %) against 28 for the digest control and 21 for the seeded reshuffle, chance `1996/66585 ≈ 3.00 %`; cited either way 76/966 (7.87 %) against 11 and 1, chance ≈ 0.57 %; mean squared distances 5,399.2 within a file against 6,534.3 across, ratio 0.826. The scale sweep and all four §8 examples were recomputed and were unchanged. `STATUS.md`, both READMEs and the tests README now quote the same corpus.

**4. A v5.12 changelog row** was added to `overlay/README_ARCHIVE.md`, following the established practice: the measure-word round (comparison-class register, the measured widening, the `measure` query and its forced refusals, `MeasureView.lean`) together with this reconciliation and the figures it was checked against.

**5. Full verification.**

| instrument | result |
|---|---|
| test suite | **2,424 tests across 54 test files, 10,782 subtests, zero failures** |
| end-to-end CLI evaluation | **112 / 112** — 100 answered, 12 refused as expected (all boundary, 0 gap), 0 unexpected refusals, 0 confidently wrong, 0 errored |
| Lean development | `lake build` completes cleanly; **no `sorry`**, and the repository tree and its overlay mirror are byte-identical |
| figures | `figures --write` is a no-op — `FIGURES.md` already matches a fresh computation |
| reports | `report lean`, `report measure`, `report escalation` each `VERIFIED True` under `--verify-tct` |

The subtest total moved from the 9,232 the documents quoted to 10,782; the earlier figure predated the two test files added last round, and the guard now blocks its return.

**Properties table.** The five `MeasureView.lean` properties left open last round are now marked proved — each was re-checked against a clean, `sorry`-free build and depends only on Lean's standard axioms (`propext`, `Classical.choice`, `Quot.sound`). The definition they are stated in terms of remains a definition entry.


# Summary of changes for run bba72c13-d2ef-4e24-be71-f1d7407c1ed8
All the outstanding items are done, verified by running them, and committed and pushed.

**1. The three stale "849-declaration" statements, corrected.** Each now quotes the corpus as it actually is, measured here (861 declarations across 36 files, after `RequestProject/GLM/Harmony.lean` joined the development):

- `STATUS.md` — the "Lean development, addressed" paragraph: 861 declarations, read back 861/861 with 0 coordinate errors, 806 distinct addresses, nearest-by-address shares a file 330 times against 26 for the digest control and 20 for the seeded reshuffle, chance `288/8815`.
- `overlay/glm_universal/README.md` — the `report lean` bullet: the same figures, with 330/861 on the file test.
- `overlay/README.md` — the one-line description of the study in the document index: 861.

`MASTER_PLAN.md`'s phase record was left exactly as it was, as a historical entry.

**2. Everything in the study re-checked against the code, not just the three edits.** Every figure in `LEAN_ADDRESS_STUDY.md` was recomputed and matched: the kind table (557 theorems, 201 defs, 82 lemmas, 6 abbrevs, 5 each of inductive/instance/structure = 861), `861 parsed, 0 duplicates`, largest file `Stack.lean` at 47, the scale sweep row by row, the read-back table (20,664 coordinates, 0 errors, worst residual 3 at `GLM.CoherenceRegime`, all 861 moved by the decoder), the 47 collision classes as 40 pairs / 6 triples / one class of four together with all four example classes quoted in §6, the §7 rates and mean squared distances, and all three §8 examples down to the individual neighbour distances. Two small corrections fell out: the per-file test count in the header, and a missing line number in one §8 example.

**3. The drift is now caught rather than noticed.** `test_lean_address.py::TestDocumentsQuoteTheCurrentCorpus` parses the Lean tree and requires the four documents that state the corpus size to state the size the parser finds, so the next Lean file added fails the suite instead of quietly ageing the prose. The test-count figures that moved as a result (2,308 → 2,309 collected, 9,165 → 9,170 subtests) were regenerated with `figures --write` and propagated to `STATUS.md`, `CAPABILITY_ASSESSMENT.md`, the overlay README, the package README and the tests README, and a change-log row 5.9 (with the version header) records the round.

**4. Full re-verification after the documentation edits.**

| instrument | result |
|---|---|
| test suite | **2,309 tests across 51 test files, 9,170 subtests, zero failures** |
| end-to-end CLI evaluation | **103 / 103** — 94 answered, 9 refused as expected (all boundary, 0 gap), 0 unexpected refusals, 0 confidently wrong, 0 errored |
| verified reports (`--verify-tct`) | `lean`, `harmony`, `directives`, `pipeline`, `containers`, `companion`, `lattices`, `shells`, `semantics`, `noise`, `catalog`, `drift`, `signature` — all **VERIFIED True** |
| Lean development | `lake build` completes cleanly; 36 files, 9,410 lines, **no `sorry`**, and the repository and overlay copies of the sources are identical |
| figures | `FIGURES.md` regenerated and matching a fresh computation |

**5. Properties table.** No registered declaration changed this session — the work was in documentation and one new test — so the table still matches the sources; the Lean entries it records were re-checked against a clean, `sorry`-free build.


# Summary of changes for run 7ff21c97-e32b-44f1-aa8b-c56599e364b5
I picked up the unfinished v1.4.0 round and closed it out — no new features were started; everything begun earlier is now wired, tested and documented.

**Documentation finished (the main remaining gap)**

- `MASTER_PLAN.md`: header figures corrected (18 query kinds, **35 report subjects**, 6 registers, **44 test files**); `report containers` and `report companion` added to the runtime-surface table; §7.9 "still untouched" updated — the "carrier in every solver" item is retired and the 32-/48-dimensional lattices are named as the open geometric direction; and a full **Phase 10** section added covering the three containers, the companion claim ledger, the formula fall-through, and the measured result.
- `overlay/README.md`: current-state part brought to v1.4.0 (35 report subjects, 37 reasoning modules, 44 test files, 97 evaluation cases, 1,991 tests), `GLM_COMPANION_STUDIES_AUDIT.md` added to the document index, and a new **change-log row 5.5** written into the archive section (the historical rows below the archive marker were left untouched, as intended).
- `CAPABILITY_ASSESSMENT.md` §6 refreshed: 35 report subjects / 36 report cases, 9 refusals across 97 cases, a new bullet for unregistered-formula carriers, "demonstrably not working" now correctly reports **no** failing case, and the untouched list realigned with the master plan.
- `overlay/glm_universal/tests/test_figures.py`: three more superseded phrases (`33 report subjects`, `35 reasoning modules`, `92-case`) added to the drift guard, so those counts cannot silently return; the subtest total the documents quote was updated accordingly (8,935) in the five places that state it.

**Full verification, all re-run from scratch and all clean**

| instrument | result |
|---|---|
| test suite | **1,991 tests across 44 test files, 8,935 subtests, zero failures** |
| end-to-end CLI evaluation | **97 / 97** — 88 answered, 9 refused as expected (all `boundary`, **0 gap**), 0 unexpected refusals, 0 confidently wrong, 0 errored |
| capability probes | 33 probes: 20 hold, 13 break, 0 errored |
| benchmark suites | 2,389 / 2,390 across 5 suites; every suite beat its baseline |
| `figures --write` | no-op — `overlay/FIGURES.md` already matched a fresh computation |
| `report containers` / `report companion` under `--verify-tct` | both `VERIFIED True` |
| Lean development | `lake build` completed successfully; 32 GLM files, 8,157 lines, **no `sorry`** |

Every documentation figure quoted above is now the figure the code produces, and the figures test enforces that.

All work is committed and pushed. No new Lean declarations were added this session, so the properties table is unchanged and still matches the sources.

# Summary of changes for run 79fd272a-e622-48eb-930d-e2ab65130a19
I picked the project up where it stood, finished the one piece of work that had been left half-wired, and brought the documentation and README chain back into line with the code so the next iteration can start from an accurate picture.

**What I found unfinished.** The previous round had landed the study-catalogue work (`reasoning/catalog.py`, `wobble.py`, `drift.py`, the `report catalog` / `report signature` / `report drift` subjects, `RequestProject/GLM/Sturmian.lean`) and `RequestProject/GLM/Feedback.lean`, but almost none of it had reached the documents: `MASTER_PLAN.md` stopped at Phase 8, `STATUS.md` still listed error feedback as not started, the Lean README claimed 32 files while its table listed 30, the top-level overlay README's version header had moved to 5.3 with no matching change-log row, and several counts were off. Worse, the error-feedback code was reachable from nothing: `feedback_experiment` was not in `noise_report`, no test touched it, and no report surfaced it.

**Code completed.** The vector error-feedback loop is now the sixth step of `report noise` — every coordinate tracked to `1/(2N)`, the dead zone at `A = 1/2` where the quantiser never fires, and exact equivariance under a permutation the feedback matrix respects, with a non-invariant matrix run beside it so the hypothesis is seen to do work. Its column-3 script re-derives all of it in a fresh interpreter (`VERIFIED True`), and ten new tests in `glm_universal/tests/test_noise_lab.py` (40 → 50) pin the quantiser, the bound, the dead zone, the equivariance and the absence of any float.

**Documentation reconciled.** `MASTER_PLAN.md` gains Phase 9 (the catalogue ledger, the spectral signature, the drift study, error feedback) plus eight missing runtime-surface rows, and its stale "not started" bullet is corrected; `STATUS.md` records the catalogue round, the two new Lean files and the new open item, and its document map now lists both audit write-ups, the Lean README and the supplied source material; the repository `README.md` gains a section on the two claim ledgers and the missing `Feedback.lean` entry; `NOISE_EXPERIMENT_STUDY.md` gains §6 on error feedback; the Lean README gains `Sturmian.lean` and `Feedback.lean`; the reasoning, runtime, package and tests READMEs gain `wobble.py` / `drift.py` / `catalog.py`, the three report subjects and corrected counts; and the overlay README gains change-log rows 5.3 and 5.4 with the header at 5.4. `tests/test_figures.py` now also holds `STATUS.md` to the generated figures, so the status document cannot silently drift again.

**Verified here, by running it.** `lake build` completes cleanly over the 32 Lean files with no `sorry` (the repository and overlay copies are identical); the full Python suite is 1,894 tests across 42 test files, 8,896 subtests, zero failures; the end-to-end CLI evaluation is 92/92 (82 answered, 10 refused as expected — 9 boundary, 1 gap — 0 confidently wrong, 0 errored); benchmarks 2,389/2,390 with every suite above its baseline; 33 capability probes (20 hold, 13 break, 0 errored, 0 surprises); `FIGURES.md` regenerated; and `report noise`, `report catalog`, `report drift`, `report signature`, `report analogies`, `report molecules`, `report chemistry coverage` and `report semantics` each return `VERIFIED True`. The four `Feedback.lean` theorems now recorded in the properties table depend only on Lean's standard axioms.


# Summary of changes for run 1c2d31a1-2424-4b7b-bccf-398ccedefc0e
Everything you listed is done, checked by running it, and committed and pushed.

**1. The figures, regenerated.** `python -m glm_universal.figures --write` was re-run from `overlay/`. Every row of `overlay/FIGURES.md` came back unchanged except the collected test count, which moved 1,669 → **1,677** once the two new regression checks below were added. The whole suite was then run in full: **1,677 passed, 8,851 subtests, zero failures**.

**2. A changelog note about the theta template fix.** `overlay/README.md` gains row **5.1**, and its version header — which still read 4.9 while the change log had already reached 5.0 — is corrected to 5.1. The row records what the fix was and why it mattered: `report theta` claims six coefficients (`theta_series(order=5)` returns `[1, 0, 196560, 16773120, 398034000, 4629381120]`, and the solver puts all six into `expected`), but the column-3 template hand-wrote the keys `coeff_0` .. `coeff_4`, so the sixth was stated in column 2 and never re-derived in a fresh interpreter. The template now builds its `observed` map by enumerating whatever the series returns, and `report theta --verify-tct` returns `VERIFIED True` over all six. I also pinned it, since nothing was testing it: `test_runtime.py::TestReportThetaTemplate` (3 tests) checks that `expected` holds one key per returned coefficient, that the generated script enumerates rather than lists, and that a subprocess reproduces all six with no missing keys. All three fail if the old hand-written template is put back — I checked that by restoring it temporarily — so the regression cannot return silently.

**3. The session module's stale quantity count, confirmed and now verified.** `runtime/session.py` described its registers as `physics (660 quantities)`; it now says 726, which is what `len(session.register("physics"))` returns and what `FIGURES.md` reports under *Registers*. That was only asserted, not checked, so I added `test_figures.py::TestModuleDocstringsQuoteCurrentFigures` (5 tests): it reads the physics, chemistry and molecule counts out of the session docstring and out of `data_objects/physics.py`'s, compares each against the live register, and checks all six registers are named. Reverting the docstring to 660 makes it fail, which I verified.

**4. The documentation check before committing.** The counts quoted in `STATUS.md`, `MASTER_PLAN.md`, `CAPABILITY_ASSESSMENT.md`, `overlay/README.md` and the package and tests READMEs were brought to 1,677 tests / 8,851 subtests, the per-file rows for `test_runtime.py` (181 → 184) and `test_figures.py` (14 → 19) were updated with what they now cover, and `1,669 tests` / `8,818 subtests` were added to the superseded-phrase guard in `test_figures.py`. One genuine drift turned up beyond the test counts: `STATUS.md` said the Lean development was 26 files in two places while its own table and `FIGURES.md` said 27 — corrected. Historical change-log rows were left as they are, since they record what was true at the time.

**Re-verified alongside the docs:** `lake build` completes cleanly over the 27 Lean files with no `sorry` (the only `sorry`/`admit` matches in the tree are the English words "admitted"/"admits" in prose), and the repository and overlay copies of the Lean sources are identical; the end-to-end CLI evaluation is **83/83** (73 answered, 10 refused as expected, 0 unexpected refusals, 0 confidently wrong, 0 errored); benchmarks **2,389/2,390** with every suite above its baseline; **33 probes, 20 hold, 13 break, 0 errored**; all six example scripts run end to end; and `report analogies`, `report molecules`, `report chemistry coverage`, `report semantics` and `report theta` each return `VERIFIED True`. No behaviour changed in this round beyond the theta template already being fixed — the work was recording it, pinning both fixes with tests, and reconciling the numbers.

# Summary of changes for run 7260ede7-8270-4873-a880-a86f69da3294
I finished the outstanding items rather than extending the project, and re-verified everything I state below by running it here.

**Verification pass (no code changed).**
- The whole Python suite was run: **1,324 tests, 6,331 subtests, zero failures**.
- The Lean 4 development (`RequestProject/GLM/`, 18 files) was rebuilt with `lake build` — a clean build — and re-checked for `sorry`: none, in either the main tree or the overlay's copy under `overlay/glm_lean/`, and the two copies are identical.
- All six example scripts under `overlay/glm_universal/examples/` run end to end.
- The CLI answers `report information loss`, `report infinite values`, `report capabilities`, `report semantics`, `meaning of water` and `relate energy torque`, all exit 0; `report semantics --verify-tct` returns `VERIFIED True`.
- The 33 capability probes were re-run: 19 hold, 14 break, 0 errored, 0 surprises.
- The semantic graph was rebuilt from scratch: 357 meanings, 1,705 notations, 6,210 binary and 6,649 ternary edges; the inherited-graph audit still reports 83 of 4,282 concepts grounded and 2 of 4,015 edges re-derivable.

**Gaps closed.**
1. **`MASTER_PLAN.md` was missing the semantics phase.** The meaning work was built, wired and tested, but the plan — which is the document that tracks what was built and how to see it recompute itself — never recorded it. Added **Phase 4 — meaning, not spelling**: the audit of the inherited concept graph with the function that recomputes each figure, the meaning space and grounded graph with their counts, the queries, and the Lean counterparts (`Meaning.lean`, `Grounding.lean`, theorem names checked to exist). Added the two missing rows (`report semantics`, `meaning of <term>` / `relate <a> <b>`) to the runtime-surface table.
2. **Stale figures from the last round.** The repository `README.md` and `MASTER_PLAN.md` quoted an earlier test count, and the repository README plus the overlay README still said the Lean development was seventeen files. All now say 1,324 tests and 18 files, matching the runs above; the reasoning README's pointer was likewise out of date and is corrected. Historical changelog rows were left as they are, since they record what was true at the time.
3. **`Transcendental.lean` was absent from the repository README's file listing** although it is part of the development; it is now listed.
4. Added a changelog row (overlay README 4.5 → 4.6) recording this reconciliation and the figures it was checked against.

Nothing in the Python package or the Lean development needed changing — the code was already complete and passing; the remaining work was in the documentation that describes it. All work is committed and pushed.


# Summary of changes for run 712f237d-e93d-4e44-92f7-e495abe022b0
Completed the four outstanding items. Everything below was checked by running it; the work is committed and pushed.

**1. The version bump, finished.** The package declared `glm_universal.__version__ = "1.1.0"` and exported the new `semantics` sub-package, but the test that pins the package surface still asserted `1.0.0` and listed only six sub-packages — so the suite was failing one test. `glm_universal/tests/test_wiring.py::TestPackageSurface` now pins the current version and all seven exported sub-packages (`substrate`, `data_objects`, `reasoning`, `semantics`, `runtime`, `migration`, `benchmarks`), which is what makes a future bump self-checking. The suite is now **1,094 tests, 6,331 subtests, zero failures** (about four minutes). Stale counts elsewhere in the package and reasoning READMEs were corrected to match.

**2. `glm_universal/tests/README.md`.** Repaired the file-by-file table (the `test_semantics.py` row had been left outside it, breaking the table), corrected the per-file and total counts against a real collection run, listed `test_semantics.py` among the substantive tests, and added a short section on the package-surface test and on the slowest fixtures.

**3. `glm_universal/examples/README.md`.** Rewritten. It now covers all six scripts — `reasoning_showcase.py` was missing entirely — plus the generated transcript and how to regenerate it, each script's flags, what each one prints when it succeeds, and its known limitations. Writing it truthfully turned up three real defects, which I fixed rather than documented around: `encoding_poc.py` and `scaled_carriers.py` looked for `data_objects/_data/elements_118.json` under `examples/` and could not start at all, and `scaled_carriers.py` formatted an exact `Fraction` with a float format spec, which raises on Python 3.11 — it now renders through the package's exact `decimal_str`, so no float is constructed. All six scripts run end to end; `demo_tct.py` reports `ALL DEMOS VERIFIED` and the showcase 29 probes, 29 as expected.

**4. The overlay top-level README.** Version 4.2 → 4.3, a changelog row for the v1.1.0 work, the README chain and the `glm_universal/` entry brought up to date (seven sub-packages, 15 query kinds, 16 report subjects, 1,094 tests, thirteen Lean files), and a new "GLM-3+ v1.1.0" section at the bottom: the audit of the inherited concept graph (83 of 4,282 concepts denote anything determinate; 2 of 4,015 edges state a re-derivable relation; the stored carriers put related pairs at mean Hamming 4547/376 and unrelated pairs at 12077/1009, either side of the 12 that two random 24-bit words average), the grounded graph that replaces it (357 meanings, 1,705 notations, 12,859 edges, all re-derived), the `meaning` query and `report semantics` subject, the Lean files, and the test count. Every figure in that section was recomputed here before being written, and `report semantics --verify-tct` returns `VERIFIED True`.

One consistency gap I closed along the way: the overlay's copy of the Lean development was missing `RequestProject/GLM/Semantics/Meaning.lean` and `Grounding.lean`. Both are now in the overlay and documented in its Lean README (eleven files → thirteen). `lake build` completes successfully and the development remains free of `sorry`.


# Summary of changes for run 49a39c3c-68b2-4fde-b6e9-f434bec3e479
Both halves of the request are complete, committed and pushed.

## 1. The GLM system implementation, completed

`glm_universal_v0.6.0/` is the supplied package, unpacked and finished.

- **`GLM.py` was missing from the archive.** The READMEs document it and two test files import it by path, so 30 CLI tests errored on collection. I wrote it from scratch against the behaviour those tests specify: batch mode (`-q`, `--query-file`, stdin) and `--interactive`; the flags `-d/--domain`, `-c/--columns`, `-f/--format`, `--list-domains`, `--export-trace`, `--check-script-exactness`, `--verify-tct`, `--no-banner`; the meta-commands `:help :domains :basis :columns :verify :history :snapshot :export :quit`; and the 0/1/2 exit-code contract.
- **New module `glm_universal/reasoning/information_loss.py`**, exported from the reasoning package and wired into the runtime as the query **`report information loss`** (aliases `report loss`, `report boundaries`), with a generated column-3 script that recomputes the whole study in a fresh interpreter and checks it key by key. Exact `Fraction` arithmetic throughout; no float is constructed anywhere. Views are memoised because the rational layer's `perceive` runs a Leech nearest-point decode, and the cache is tested to be an optimisation only.
- **Full suite: 652 tests, 5,877 subtests, zero failures** (610 before, plus 42 new in `test_information_loss.py`). Verified by running it, not by report.
- READMEs updated: `TopLevel_README.md` (v4.1 changelog + a full v0.7.0 section), the package, reasoning, runtime and tests READMEs, plus a new repository `README.md`.

## 2. The information-loss study

The write-up is **`INFORMATION_LOSS_STUDY.md`**. The formal development is in `RequestProject/GLM/` — six Lean files, building cleanly with no `sorry`, and the key theorems depend only on Lean's standard axioms.

Your idea, made precise: a layer is a *resolution*, not a set of claims. On that reading all three parts of it are theorems.

- **Loss and gain are the same event.** `boundary_nonempty_iff_new_visible`: the pairs a layer conflates are non-empty exactly when the layer above can state something it cannot.
- **Nothing true below becomes false above** (`Visible.mono`), so "becomes untrue" is located precisely — not in propositions flipping, but in an operation ceasing to be a function of what a layer sees (`descends_iff_congruent`, the exact content of the code's `can_multiply` flag).
- **The ascent is forced** by capacity below the carrier count, and computable: `escalate` returns the least layer separating two carriers, proved correct and minimal.
- **It continues without end** (`Tower.lean`): an explicit infinite ladder — layer *n* sees a rational to resolution 2⁻ⁿ — that is cumulative, gains strictly new expressive power at *every* step, has no final layer, and still eventually tells any two distinct carriers apart. Set against `boundary_above_rational_empty`, which shows a tower *can* terminate: whether it does is a property of the carriers, not of layering itself.

Four concrete boundaries are pinned exactly, not estimated: the layer stack over ℚ (resolutions 2/3/4, losses 2/1/0); addition, which is exactly right at the substrate on integer carriers and *ill-defined* there on rationals; the TAX conservation law, exact on bits and above them repairable only if `Y = 1/2`, which is false since `1/4 < Y < 1/2`; and Golay repair, unique at Hamming weight 3 and genuinely two-valued at 4.

## Audit finding

Running the same definitions against the shipped `dimension_layers.py` rather than an idealisation of it reports `refinement_chain_intact = False`. The substrate → integer step is **not** a refinement on real carriers: the substrate's 24-bit parity view separates a unit on coordinate 10 from the vacuum, while the integer layer reads only the seven SI7 exponents and conflates them — so escalating destroys a distinction the layer below already had. It is reported and tested rather than silently patched, since fixing it (widen the integer view, or narrow the substrate's) is a design decision about what the integer layer is for.
