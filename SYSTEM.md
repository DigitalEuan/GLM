# The system — what the GLM is now, and how to re-verify it

## Tier 0 — the coarse read

**Question.** What is the GLM system made of now, what does each instrument report, and how is all of it re-verified?

**Verdict.** This is the standing description of the system, the instrument table, and the commands that re-verify it; what is still to do is in [`STATUS.md`](STATUS.md).

**Deciding figure.** Every instrument in the table below reports its own result on demand.

**Recomputed by.** `glm_universal.signoff.ledger.suite_totals`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

This is the standing description of the system, the instrument table, and the commands that re-verify it; what is still to do is in [`STATUS.md`](STATUS.md).

*Split out of [`STATUS.md`](STATUS.md) in Phase 111, so that the status
document can be a list of what is still to do. This file holds the present
tense: what the system is, what each instrument reports, and how to re-verify
it. The record of the rounds that built it is
[`MASTER_PLAN.md`](MASTER_PLAN.md); the status document's own round-by-round
account is in
[`archive/STATUS_ROUNDS_ARCHIVE.md`](archive/STATUS_ROUNDS_ARCHIVE.md).*

## 1. Where the work stands, in one table

| instrument | command | result |
|---|---|---|
| test suite | `python3 -m pytest glm_universal/tests -q` | **<!--figure:suite-->5,334 tests across 175 of the 177 test files, 18,873 subtests, outside the document checks<!--/figure-->**, zero failures |
| end-to-end CLI evaluation | `python3 -m glm_universal.evaluation --jobs 8` | **<!--figure:evaluation-case-count-->179<!--/figure--> / <!--figure:evaluation-case-count-->179<!--/figure-->** — 149 answered, 28 refused as expected (all `boundary`, no `gap`), 0 unexpected refusals, 0 confidently wrong, 0 errored |
| benchmark suites | `python3 -m glm_universal.benchmarks` | **2,389 / 2,390** across 5 suites, every suite above its baseline |
| capability probes | `python3 -m glm_universal.capabilities` | 33 probes — 20 hold, 13 break, 0 errored, 0 surprises |
| Lean development | `lake build` (repository root) | <!--figure:lean-files-->199 Lean files<!--/figure-->, **0 `sorry`** |
| figures | `python3 -m glm_universal.figures --write` | regenerates `overlay/FIGURES.md`; every documented count |
| corpus | `python3 -m glm_universal.corpus --check` | the tier contract, the archive partition, the coverage claim of `ENTRY.md`, every generated block and every derived cache — **current**, no drift |
| construction ladder | `python3 -m glm_universal.tools ladder` | **462 / 568** queries named correctly with **0** wrong on the eleven-rung ladder, against **327** for the note's five rungs and **283** for the best single rung |
| norm-family ladder | `python3 -m glm_universal.tools normladder` | the repaired **<!--figure:normesc-rungs-->10<!--/figure-->**-rung norm ladder names **<!--figure:normesc-correct-->467<!--/figure-->** of **<!--figure:normesc-queries-->568<!--/figure-->** correctly with **<!--figure:normesc-wrong-->0<!--/figure-->** wrong; the full **<!--figure:normesc-family-rungs-->12<!--/figure-->**-rung family it repairs answers **<!--figure:normesc-family-wrong-->1<!--/figure-->** wrongly and is **not safe** |
| escalated operations | `python3 -m glm_universal.tools operations` | **<!--figure:opesc-count-->7<!--/figure-->** operations other than retrieval measured against substrate-removed controls; every one gains, and **one of them — program text — answers <!--figure:opesc-program-wrong-->13<!--/figure--> queries wrongly and is reported unsafe** |
| second reading | `python3 -m glm_universal.tools second-reading` | **<!--figure:secondread-adopted-->1<!--/figure-->** of **<!--figure:secondread-configurations-->6<!--/figure-->** declared guard configurations is adopted — `<!--figure:secondread-shipped-->strict+margin<!--/figure-->` takes the program-text operation to **<!--figure:secondread-program-correct-->366<!--/figure-->** correct and **<!--figure:secondread-program-wrong-->0<!--/figure-->** wrong, giving up **<!--figure:secondread-given-up-->150<!--/figure-->** answers where matched refusal removes **<!--figure:secondread-matched-removes-->2<!--/figure-->** of the thirteen |
| field surface | `python3 -m glm_universal.tools fieldsurface` | the surface answers **<!--figure:fieldsurface-moved-->9<!--/figure-->** of the **<!--figure:fieldsurface-held-->10<!--/figure-->** questions the oracle found held and unreachable — exactly the **<!--figure:fieldsurface-predicted-->9<!--/figure-->** declared reachable before the run — taking the probe from **<!--figure:fieldsurface-parsed-before-->6<!--/figure-->** parsed to **<!--figure:fieldsurface-parsed-after-->15<!--/figure-->**; it is `table`, not reasoning |
| ordering operation | `python3 -m glm_universal.tools ordering` | the operation answers **<!--figure:ordering-answered-->4<!--/figure-->** of the **<!--figure:ordering-declared-count-->7<!--/figure-->** comparisons declared before the run and refuses **<!--figure:ordering-refused-->3<!--/figure-->** under **<!--figure:ordering-reasons-->3<!--/figure-->** named reasons — **<!--figure:ordering-as-declared-->7<!--/figure-->** of **<!--figure:ordering-declared-count-->7<!--/figure-->** as declared — and closes the last held-and-unreachable probe question, taking it to **<!--figure:ordering-parsed-after-->16<!--/figure-->** parsed |
| typed planner | `python3 -m glm_universal.tools plans` | the frozen probe through the planner scores **<!--figure:plans-probe-correct-->19<!--/figure-->** correct, **<!--figure:plans-probe-wrong-->0<!--/figure-->** wrong, **<!--figure:plans-probe-refused-->1<!--/figure-->** refused; **<!--figure:plans-held-correct-->86<!--/figure-->** correct and **<!--figure:plans-held-correct-refusal-->22<!--/figure-->** correct refusals of **<!--figure:plans-held-total-->110<!--/figure-->** held-out questions with **<!--figure:plans-held-wrong-->1<!--/figure-->** wrong; the hostile stress set **<!--figure:plans-stress-wrong-->0<!--/figure-->** wrong |
| extremum operation | `python3 -m glm_universal.tools extremum` | the operation folds **<!--figure:extremum-answered-->4<!--/figure-->** of the **<!--figure:extremum-declared-count-->8<!--/figure-->** columns declared before the run and refuses **<!--figure:extremum-refused-->4<!--/figure-->** under all **<!--figure:extremum-reasons-->4<!--/figure-->** of its named reasons — **<!--figure:extremum-as-declared-->8<!--/figure-->** of **<!--figure:extremum-declared-count-->8<!--/figure-->** as declared — and reports **<!--figure:extremum-ties-->1<!--/figure-->** tie as a tie rather than resolving it |
| scale conversions | `python3 -m glm_universal.tools scales` | the declared table of **<!--figure:scales-rows-->10<!--/figure-->** scales over **<!--figure:scales-quantities-->4<!--/figure-->** quantities answers **<!--figure:scales-answered-->7<!--/figure-->** of the **<!--figure:scales-declared-->12<!--/figure-->** questions declared before the run and refuses **<!--figure:scales-refused-->5<!--/figure-->** — **<!--figure:scales-as-declared-->12<!--/figure-->** of **<!--figure:scales-declared-->12<!--/figure-->** as declared — and relates **<!--figure:scales-bridged-->8<!--/figure-->** of the **<!--figure:scales-pairs-->7,875<!--/figure-->** pairs of the **<!--figure:scales-numeric-->126<!--/figure-->** numeric scales, leaving every other pair refused |
| corpus resample | `python3 -m glm_universal.tools corpus-resample` | every sub-corpus that drops one Lean file (**171**) and every stride offset (**22** and **45**), read off one census of **4,572** declaration and **4,572** goal queries under ten rankings: **1** effect among **18** reading-and-set pairs (`native2` ≥ `features` on the declarations, **99.4 %** / **95.5 %**); W2, W4, W6, N1, N2 and the three post-hoc readings draws; the control `native2` = `features2` holds in **88.3 %** / **77.3 %**; **6 / 7** marks met; the citation index reads one-letter bound variables as citations (**3,231** of **15,012** edges) |
| document tree | `python3 -m glm_universal.tools document-tree` | the document rankings on a frozen snapshot of the corpus (**1,506** units, **136** documents), every unit a query: the place word in the third layer **324** / **413** (hit@5 / relatives in the top five) against the raw lexical vector **323** / **414**, identical to the two-book ranking on every query; ties at the top-five boundary **30**; the oracle third layer **325** / **414**; the path word first **1,506** hits at 1 (the leak control); **3 / 6** marks met |
| AST index | `python3 -m glm_universal.tools ast-index` | the statement-level expressions of the live code (**3,438**) and the archive (**8,231**) in a frozen index of **4,818** buckets and **4,864** structural classes (**307** shared by both); under rename-and-commute, hit@1 on **467** query sites: structural key **467**, Phase 64 address **456**, its carrier **412**, token overlap **343**; bucket key unmoved **467 / 467**; matcher and reference agree on **8,398 / 8,398** calls; **0** failures in **3,350** integer evaluations; **12 / 12** questions and **5 / 5** refusals; **5 / 7** marks met |
| derivations and proofs | `python3 -m glm_universal.tools derivation` | four operations that derive (propositional proof, equations of motion, transfer functions, boundary value profiles): **16 / 16** proofs, **8 / 8** equations of motion, **6 / 6** transfer models, **6 / 6** profiles, **8 / 8** refusals as declared; **36 / 36** column-3 scripts verify and **36 / 36** mutants rejected; **2000** random formulas, **0** unsound, **0** gaps, every classical verdict with a Kripke countermodel; **4 / 4** outside class-P questions answered, **0** of **299** other texts moved; **9 / 9** marks met |
| the rest of track P | `python3 -m glm_universal.tools derivation-two` | eight more operations that derive (information inequalities with certificates or witnesses, unique decodability and prefix codes, rate distortion, rate posterior, maximum entropy, eigenvalue problems, transmission, the radix-2 FFT): **16 / 16** inequalities, **11 / 11** codes, **5 / 5** rate distortion, **4 / 4** maximum entropy, **6 / 6** eigenvalue problems, **13 / 13** transmission/FFT/posterior, **14 / 14** refusals as declared; **55 / 55** column-3 scripts verify and **55 / 55** mutants rejected; **400** random inequalities and **600** random codes, **0** unsound, **0** undecided, **0** disagreements; **11 / 11** outside class-P questions answered, 29, 39 and 96 still refused, **0** of **292** other texts moved; **11 / 11** marks met |
| past the second derivation study | `python3 -m glm_universal.tools derivation-three` | information inequalities past the Shannon cone (Zhang–Yeung with copy-lemma certificates, exact entropic counterexamples), Hamming rate distortion on the whole range, eigenvalue problems with a Robin end: **8 / 8** inequalities, **5 / 5** sources, **8 / 8** Robin problems, **5 / 5** refusals as declared; **21 / 21** column-3 scripts verify and **21 / 21** mutants rejected; **120** random inequalities (**12** proved past Shannon, **3** left undecided), **150** random sources and **60** random Robin problems, **0** unsound, **0** failures; Phase 107 **11 / 11**, **0** of **304** other texts moved; **10 / 10** marks met ([`DERIVATION_THREE_STUDY.md`](studies/DERIVATION_THREE_STUDY.md)) |
| meta questions | `python3 -m glm_universal.tools meta-questions` | the eighteen class-M outside questions answered from the project's own studies, code and Lean development: **18 / 18** with the declared fragment, **30** quotes and **24** theorems found at read time, **11** declared disputes and no others, every mutation of the evidence caught, **35 / 36** paraphrases and **17 / 18** held out, **0** of 296 other texts read; 6 of 7 marks ([`META_QUESTIONS_STUDY.md`](studies/META_QUESTIONS_STUDY.md)) |
| explanations anchored in the registers | `python3 -m glm_universal.tools explanations` | the thirty-five outside questions that ask why (class E and questions 29, 39 and 96), answered where the element register, the nuclide register or an exact derivation decides them, the account refused `EXPLANATION`: **35 / 35** with the declared fragment (3 FULL), **25** reading a register, **3** declared disputes and no others, **35 / 35** scripts verify, script-claim **35 / 35** and register-row **21 / 21** caught, **35 / 35** paraphrases and **5 / 35** held out (0 misread), **0** of 279 other texts read; 10 of 10 marks ([`EXPLANATION_ANCHOR_STUDY.md`](studies/EXPLANATION_ANCHOR_STUDY.md)) |
| share-carrying rungs (lattice item 6) | `python3 -m glm_universal.tools share-separation` | the deep-hole ladder's readings over its ensembles extended to 30720 starts: the ladder's **16 / 16** cells reproduced exactly; the bound sorted shift ≤ vertex-matched shift at **80 / 80** instances; no share-carrying cell below `rho = 1` (best **2.3508** at `(L4, 7680)`); the per-hole criterion certifies **8 / 10** holes at `(L4, 15360)` and `(L4, 30720)`, leaving the 28-vertex pair `E_6^4`/`D_6^4`; 3 of 6 marks ([`SHARE_SEPARATION_STUDY.md`](studies/SHARE_SEPARATION_STUDY.md)) |
| configuration reading (lattice item 6, the 28-vertex pair) | `python3 -m glm_universal.tools configuration-reading` | the rung `L5` over the same stored ensembles — arrival shares pushed forward along each vertex's component size and degree in the affine diagram the arrival vertices form: **20 / 20** declared diagrams read back; the bound configuration shift ≤ vertex-matched shift at **80 / 80** instances; `rho` **0.1261** at `(L5, 30720)`, below 1 at every size from 1920; the per-hole criterion certifies **10 / 10** holes, `E_6^4`/`D_6^4` included; 6 of 6 marks ([`CONFIGURATION_READING_STUDY.md`](studies/CONFIGURATION_READING_STUDY.md)) |
| the lattice round (`L5` answers, all 23 types, the empty norms) | `python3 -m glm_universal.tools configuration-classifier`, `hole-census`, `empty-rungs`, `frozen-path`; `report hole configuration` | the answer rule names **44 / 44** deep-hole queries correctly, 0 refused, with **396** certified absences and **0** false; **20 / 23** Niemeier types certified as declared, **23 / 23** post hoc, `rho` **0.1929** at `(L5, 7680)` over all 23; norm 2 filled by `D12^2`, norm 256 empty; the frozen path kept **178 / 178** earlier cases' status; 10 of 14 marks ([`LATTICE_COMPLETION_STUDY.md`](studies/LATTICE_COMPLETION_STUDY.md)) |
| the probe budget (the certifying reading's stopping rule) | `python3 -m glm_universal.tools probe-budget` | no barren stop and a budget of 1056 starts, proved enough for every type under a union-bound model (`GLM.ProbeBudget.budget_serves_every_type`); the model's share hypothesis holds on **46 / 46** (hole, seed) pairs; **23 / 23** references and **256 / 256** held-out deep holes certified, against **252 / 256** under a 60-start patience; median **96**, maximum **254** starts; 6 of 6 marks ([`PROBE_BUDGET_STUDY.md`](studies/PROBE_BUDGET_STUDY.md)) |
| the operations ladder and GLM-BAT (an old-style machine learnt as a language) | `python3 -m glm_universal.tools ops-ladder` | the owner's DevOps note as a **97**-term register (0 layering violations, 97 distinct carriers, **14 / 14** cross-overs resolve); **25 / 25** machine runs, **18 / 18** English questions and **6 / 6** English-written programs as declared, 0 wrong; **78 / 78** lines read back; **41 / 41** column-3 scripts verify, **158 / 158** mutations rejected; H **185 / 242** edges monotone; 9 of 9 marks ([`OPERATIONS_LADDER_STUDY.md`](studies/OPERATIONS_LADDER_STUDY.md)) |
| GLM-BAT's inert-variable certificate (a loop with a growing counter, certified never to halt) | `python3 -m glm_universal.tools inert-counter` | **10 / 10** battery programs and **9 / 9** questions as declared, 0 wrong; **8 / 8** `never_inert` scripts verify, **40 / 40** mutations rejected; Phase 125's answers unchanged but M15's, **299 / 299** decided generated programs unchanged; **0 / 4** certified programs halt within 200000 steps; 7 of 7 marks ([`INERT_COUNTER_STUDY.md`](studies/INERT_COUNTER_STUDY.md)) |
| norm 256 and the hex colour (lattice item 3) | `python3 -m glm_universal.tools norm256-hex` | the norm-256 rung filled by `H16` (each coordinate read by its first hex digit): **0** wrong on the 568 queries and **0** on 568 held-out ones (119 and 77 correct), no answer added on the 568; the `√2`-rotated Leech rung `R256` (2 wrong) and `16Z` (4 wrong) retired; the hex shortcut — a `2C` point is on `R256` exactly when the hex colour of its half lies in a **4096**-colour subspace — agrees on **2,000 / 2,000** points; the ladder answers **8 / 568** held-out queries wrongly, with or without `H16` |
| conversation layer | `python3 -m glm_universal.tools conversation` | the layer binds **<!--figure:conversation-answered-->8<!--/figure-->** of the **<!--figure:conversation-declared-count-->15<!--/figure-->** follow-ups declared before the run and refuses **<!--figure:conversation-refused-->7<!--/figure-->** under all **<!--figure:conversation-reasons-->3<!--/figure-->** of its named reasons — **<!--figure:conversation-as-declared-->15<!--/figure-->** of **<!--figure:conversation-declared-count-->15<!--/figure-->** as declared — against **<!--figure:conversation-alone-->0<!--/figure-->** answered by a session with no memory, and the recency control differs on **<!--figure:conversation-control-wrong-->3<!--/figure-->** of **<!--figure:conversation-control-rows-->10<!--/figure-->** |
| discourse state | `python3 -m glm_universal.tools discourse-state` | a tie carried as a column, the fourth shape and follow-ups on every surface: **7 / 7** column, **16 / 16** fourth-shape and **6 / 6** surface cases as declared, **0** wrong; Phase 55's layer gives 0 of the 20 new-behaviour cases as declared, the session alone 0 of the 5 surface answers; **15 / 15** of Phase 55's follow-ups hold but the 1 declared move; **32 / 32** column cells equal the answer asked alone; no answer to any of 3056 earlier strings changes; 8 of 8 marks met |
| role--filler binding | `python3 -m glm_universal.tools binding` | a typed relation written as one 24-bit word gives the filler's reading back with no side condition; naming the filler recovers **<!--figure:binding-recovered-->6<!--/figure-->** of the **<!--figure:binding-declared-count-->12<!--/figure-->** bindings declared before the run and refuses **<!--figure:binding-refused-->6<!--/figure-->** — **<!--figure:binding-as-declared-->12<!--/figure-->** of **<!--figure:binding-declared-count-->12<!--/figure-->** as declared — because only **<!--figure:binding-nameable-->424<!--/figure-->** of the **<!--figure:binding-carriers-->1,143<!--/figure-->** carriers read uniquely, the worst fibre holding **<!--figure:binding-largest-fibre-->136<!--/figure-->** |
| plan store | `python3 -m glm_universal.runtime.plan_store` | a resolved follow-up kept against a digest of the whole conversation replays **<!--figure:planstore-replayed-->15<!--/figure-->** of **<!--figure:planstore-declared-count-->15<!--/figure-->** unchanged, refusals included (**<!--figure:planstore-refusals-replayed-->7<!--/figure-->** of **<!--figure:planstore-refusals-->7<!--/figure-->**), taking the licensing trials from **<!--figure:planstore-trials-first-->27<!--/figure-->** to **<!--figure:planstore-trials-replayed-->0<!--/figure-->**; keyed by the follow-up text alone it answers **<!--figure:planstore-coarse-wrong-->8<!--/figure-->** of the fifteen with another conversation's antecedent |
| engineering surface | `python3 -m glm_universal.tools engineering` | on **63** engineering questions committed before the code: **53** correct, **10** correct refusals, **0** wrong (both existing paths: 0 correct, 53 refused); formula wheels **41 / 41** at SI7 and EXT10; Smith chart **16 / 16**; force-voltage analogy **9 / 9** laws each way; delta-sigma **6 / 6** |
| carried fork | `python3 -m glm_universal.tools carried-fork` | the six deep-hole candidates carried until a later decision: **0 wrong** from every certified stage; 592,268 of 658,812 declared-case reads answered (the 90 % mark missed at 32 cases), 4,224 / 4,224 second readings, 3,840 / 3,840 unsure-set reads; 1,771 / 1,771 ties lift to a certified A₁²⁴ Leech deep hole; the soft estimate right on 512 / 768 (mark missed) |
| second view | `python3 -m glm_universal.tools second-view` | one carrier read through the framed register's views: three views resolve **680,064 / 680,064** common-mode four-error reads, **0 wrong**; two views leave 174 of 10,626 bursts open, as predicted on every read; the composition with the declared cases **658,258 / 658,812**, 0 wrong, open as predicted; the Leech escalation on the views' soft reading equals the intersection on **46,728 / 46,728** reads; 7 of 9 marks met (V4, V8 not met) |
| unpacking and the third view on demand | `python3 -m glm_universal.tools unpacking` | argument unpacking in the dialect: Phase 96's refused program answered equal to CPython, **33 / 33** declared programs and refusals as declared (0 before), 0 of 311 earlier programs moved; the third view on demand gives the three-view answer on **680,064 / 680,064** reads with **1,371,264** views read instead of 2,040,192; independent faults, three views **84,480 / 84,480**, 0 wrong; 346 open second errors for every frame; 12 of 12 marks met |
| symbolic parameters | `python3 -m glm_universal.tools symbolic` | formulas in letters: **13 / 13** class-S outside questions answered and verified, **0** wrong; **13 / 13** variants, **18 / 18** systems, **8 / 8** refusals, **44 / 44** mutants rejected; the class-T crossover bracketed to 1/10000; 27 / 27 framed outside answers and 14 / 14 Set B verdicts unchanged; `--battery` 87 / 87 random systems verified; 8 of 8 marks met (S5 after a control repair) |
| Celsius register | `python3 -m glm_universal.tools celsius-register` | the ITS-90 fixed points held in degrees Celsius and the scale table's offset row: **14 / 14** points carried onto ITS-90's kelvin column; **10 / 10** ordering, **3 / 3** column and **9 / 9** planner cases as declared, **0** wrong; offset dropped: 3 verdicts flip, **6 / 6** planner answers wrong; **6 / 6** chain scripts verified, every mutation and offset lie rejected; 8 of 8 marks met |
| connected machine | `python3 -m glm_universal.tools connected` | one path (`GLM.py --ask`) to the toolbox, Python, engineering and the planner: **0** of 177 contract cases diverted; **136** more declared questions answered correctly than by the planner alone, **0** wrong added; **8 / 8** tools answer; wiring audit **0** of 96 reasoning modules unreached; across wheels, naive union **3** right / **158** wrong, licensed union **3** right / **0** wrong |
| reverse TCT | `python3 -m glm_universal.tools reverse-tct` | the language column generated from the mathematics: **176,617 / 176,617** battery terms round-trip, **0** collisions (infix control **5,684**); every declared `say`, `entails`, `solve`, `bounds`, `equivalent`, `negate` case as declared, **0** wrong; **94 / 94** column-3 scripts `VERIFIED True`, **69 / 69** mutated certificates rejected; the default path without the surface answers **0** of 58 |
| native parity | `python3 -m glm_universal.tools native-parity` | where a standard method ties a native one, the native one refined: the two-book native ranking **90** hits at 5 against **82** for the raw features (205 declaration queries) and **30** against **27** (103 goal queries), equal to the like-for-like standard and ahead of the raw features at every cut-off at the Phase 76 re-reading (N6 met again); the read-back scorer **24 / 24** controller tasks against **18**; read-back exact on **4,070 / 4,070** addresses |
| native words | `python3 -m glm_universal.tools native-words` | word overlap computed on Golay words of the tokens: the Golay names carry the token overlap exactly, and the native word ranking has **171** hits at 5 against **171** for the standard (205 declaration queries), **85** against **83** (103 goal queries) and **45** against **44** on the 60 document queries; 3 of 6 marks met at the Phase 76 re-reading (W2 missed by four declaration queries at k = 1 while level at 5 and ahead at 3 and 10, both tie-break draws missed), 4 of 6 at the Phase 74 re-reading, 5 of 6 at Phase 71's close (at the Phase 72 and 73 re-readings W4 missed by one query and W6 met, the reverse of Phase 71's close; at Phase 74's both tie-break draws are missed, by one query each) |
| reverse TCT, round two | `python3 -m glm_universal.tools reverse-tct --two` | the widened fragment, disjunction and the planner loop: **216,723 / 216,723** widened and **18,500 / 18,500** mask terms round-trip, **0** collisions; **36** of 83 dialect programs inside, **36** agree; **650 / 650** negated normal forms certified; every declared case as declared, **0** wrong; relay **20 / 20**, **32 / 32** handoffs agree or consistent, **0** disagree (verbatim control **0 / 15**); **92 / 92** scripts `VERIFIED True`, **84 / 84** mutants rejected |
| stepwise planner | `python3 -m glm_universal.tools stepwise` | the typed planner as the executive of a chain of steps: **30 / 30** composition cases, **21 / 21** goal cases, **6 / 6** narratives and **4 / 4** follow-ups as declared, **0** wrong (the planner alone answers 0 of the 30 compound cases); the first-found control answers the **3** cases the veto refuses; **43 / 43** chain scripts `VERIFIED`, **149 / 149** steps aligned, every mutation rejected; 8 of 8 marks met |
| stepwise planner, round three | `python3 -m glm_universal.tools stepwise-three` | declared comparatives, further count nouns, tera and pico, and folds over a column: **18 / 18** comparative, **6 / 6** count-noun, **6 / 6** prefix and **17 / 17** fold cases and **2 / 2** follow-ups as declared, **0** wrong (round two's reader answers 0 of the 47; the machine answered 6 before the round and 32 after); the present-rows control answers all **3** declared holes; the classes partition the column; **34 / 34** chain scripts `VERIFIED`, **327 / 327** steps aligned, every mutation rejected (member lie **13 / 13**, word lie **11 / 11**); rounds one and two unchanged; 8 of 8 marks met |
| stepwise planner, round five | `python3 -m glm_universal.tools stepwise-five` | frames generated from a declaration: **638 / 638** texts read alike by the generated and hand-written readers; **12 / 12** order, **12 / 12** superlative, **12 / 12** bound, **6 / 6** class, **6 / 6** prefix and **6 / 6** molecule cases and **2 / 2** follow-ups as declared, **0** wrong (round four's reader answers 0 of the 54; the machine answered 5 before the round and 41 after); **10 / 10** bounded answers sound and sharp over 200 completions; **41 / 41** chain scripts `VERIFIED`, **858 / 858** steps aligned, every mutation rejected; **3 / 3** declared moves; 9 of 9 marks met |
| stepwise planner, round two | `python3 -m glm_universal.tools stepwise-two` | *how many more*, parity, averages, givens with units and register values in the wheels: **21 / 21** frame, **18 / 18** unit and **14 / 14** register cases, **2 / 2** narratives and **2 / 2** follow-ups as declared, **0** wrong (round one's reader answers 0 of the 53); strip-the-units control wrong on **6** answered cases and answers **7** unit refusals; **39 / 39** chain scripts `VERIFIED`, **178 / 178** steps aligned, every mutation rejected (unit lie **22 / 22**); round one's corpus unchanged; 8 of 8 marks met |
| law register | `python3 -m glm_universal.tools law-register` | the 65 retained UBP laws re-read: the 16 exact rows **8** structural, **2** overclaimed, **3** definitional, **2** arithmetic, **1** near-miss, every structural row citing Lean; the decoder right exactly up to error weight 3 (refused at 4, wrong at 5), `LAW_STORAGE_HARDENED_001` refuted, refusal at a six-way tie withholding **5** wrong answers per right answer given up; of the 49 numeric rows **30** not predictions and **2** of **21** external formulas admitted by the look-elsewhere test; 9 of 9 marks met |
| law absorption | `python3 -m glm_universal.tools law-absorption` | each retained law tested and given a fate: **11** absorbed as computed substrate facts, **2** already GLM definitions, **3** retested and refused, **49** retired; **36 / 36** declared substrate questions through the typed planner as declared, **0** wrong (0 answered before the round); **0** of 4,687 existing evaluation texts read by the new frame; odd errors never refused, proved; 8 of 8 marks met |
| held precision | `python3 -m glm_universal.tools held-precision` | a register value's stated precision carried through a derivation: **4** of **35** goal and narrative chains read a register value and state the exact interval of their answer; since Phase 86 **0** exact because the held value cancels and **0** strictly wider (both earlier witnesses read a temperature level as a difference and are now refused); 4 of 5 marks met (H3 no longer) |
| measurand register | `python3 -m glm_universal.tools measurand-register` | register values read through their measurand, conversions through a stated efficiency, the elementary charge: **12 / 12** register, **14 / 14** conversion and **4 / 4** charge cases as declared, **0** wrong; the naive control answers **7** conversion cases, all wrongly; **18 / 18** chain scripts verified; 8 of 8 marks met |
| measurands | `python3 -m glm_universal.tools measurands` | kinds of quantity, temperature levels and differences, the SI's defining constants: **10 / 10** kind, **15 / 15** temperature and **6 / 6** constant cases as declared, **0** wrong; the dimension-only control answers all **5** kind mismatches; **5 / 5** amended earlier verdicts; rounds one to four held; **17 / 17** chain scripts `VERIFIED`, every mutation rejected; 7 of 7 marks met |
| integer decision | `python3 -m glm_universal.tools integer-decision` | the Omega test behind `INTEGER_UNDECIDED`: **22 / 22** declared questions as declared, **0** wrong (round three refused all 22); the declared battery **600 / 600** in agreement with enumeration, **0** undecided (round three **31**); **22 / 22** scripts `VERIFIED True`, **22 / 22** mutated Omega trees rejected; round three's corpus unchanged; 6 of 6 marks met |
| confidence floor | `python3 -m glm_universal.tools confidence-floor` | a declared grid of **7** thresholds hunted at **5** rates over an exact channel census: the working threshold **9999/10000** up to 1/50, **999/1000** at 1/20, **none** at 1/10 (there the graded answer, not a refusal); the promise `P(wrong \| answered) ≤ 1 − t` kept in **210 / 210** cells, and in **210 / 210** with the rate overdeclared (**30** broken underdeclared); **15 / 16** runtime programs as declared, one declaration wrong; **6 / 7** marks |
| blockers probe | `python3 -m glm_universal.tools blockers` | the pre-registered language probe scores **<!--figure:probe-correct-->2<!--/figure-->** correct, **<!--figure:probe-wrong-->1<!--/figure-->** wrong, **<!--figure:probe-refused-->17<!--/figure-->** refused of **<!--figure:probe-questions-->20<!--/figure-->** — **below the declared pass mark of <!--figure:probe-pass-mark-->10<!--/figure-->**, a declared failure |

The test-suite row is the sign-off ledger's own count, recorded by
`python3 -m glm_universal.signoff --release`, which runs each test file in its
own process with the `exhaustive` tests selected. One `pytest` process over the
same tree, with `GLM_EXHAUSTIVE=1` so that nothing is deselected, collects
**4,018 tests** — which is the ledger's 3,990 plus the 28 tests of the document
check the ledger's total leaves out, because a round that adds a document or a
figure fails that check until the documents are reconciled. Without that switch the `exhaustive`
tests — which certify rather than sample — are reported as skipped with their
reason rather than dropped silently, which is why the ledger's own count is
taken from a run that selects them.

The package is `glm_universal` **v1.23.0**: eleven sub-packages, 152 modules,
**<!--figure:registers-->8 registers<!--/figure-->** holding 1,143 carriers (physics 726, chemistry 118, molecules
51, mathematics 22, lexicon 149, spatial 28, harmonics 28, economics 21) beside
a 45-class comparison register, **<!--figure:query-kinds-->24 query kinds<!--/figure-->**
one of which dispatches **<!--figure:report-subjects-->67 report subjects<!--/figure-->**, and 3 tasks.

---

## 2. What the system is now

This section is the **standing description**: what the machine is made of
today, with the thing that recomputes each part named beside it. It is
deliberately short. What each round *did* — the argument, the controls and the
negative results — is the record, and the record is in
[`MASTER_PLAN.md`](MASTER_PLAN.md) under *The delivered record*, phase by
phase, with the study for each finding in `studies/`.

**Substrate and algebra.** Complete syndrome decoding with no silent tie-break;
the full Leech lattice in place of Construction A (kissing number 196,560); the
exact 2A Sakuma product in place of the XOR shortcut; the six-facet orthogonal
decomposition with the lattice index that says what a facet reading loses; the
`LEGACY_TO_CORE` frame bridge, verified an isometry. The quantiser decodes
through the LLVQ class table rather than by scanning the code, on integers
scaled by a common denominator, which is exact and is what makes a whole-corpus
measurement affordable. Write-up:
[`LLVQ_TABLE_STUDY.md`](studies/LLVQ_TABLE_STUDY.md).

**The ladders it reads at.** The construction ladder — `Z²⁴`, `D₂₄`,
Construction `A`, `B` and `C`, all generated from their conditions, and the
scalings that fill the gap between them — is eleven rungs, and an escalated
reading over it names **462** of 568 declared queries correctly with **0**
wrong against **283** for the best single rung. Indexed instead by minimum
squared norm it becomes a family of
**<!--figure:normfamily-rung-count-->25<!--/figure-->** rungs over
**<!--figure:normfamily-norms-->12<!--/figure-->** norms with no power of two
missing; the full family is **not safe** — it answers
**<!--figure:normesc-family-wrong-->1<!--/figure-->** query wrongly — and the
repaired **<!--figure:normesc-rungs-->10<!--/figure-->**-rung ladder names
**<!--figure:normesc-correct-->467<!--/figure-->** of
**<!--figure:normesc-queries-->568<!--/figure-->** with
**<!--figure:normesc-wrong-->0<!--/figure-->** wrong. The containments are
proved in `RequestProject/GLM/NormFamily.lean`. Write-ups:
[`CONSTRUCTION_LADDER_STUDY.md`](studies/CONSTRUCTION_LADDER_STUDY.md),
[`NORM_FAMILY_STUDY.md`](studies/NORM_FAMILY_STUDY.md).

**Escalation, and the second reading that makes one operation safe.**
**<!--figure:opesc-count-->7<!--/figure-->** operations other than retrieval
are measured under the same discipline against substrate-removed controls;
every one gains, and one of them — program text — used to answer
**<!--figure:opesc-program-wrong-->13<!--/figure-->** queries wrongly. A second
reading at another layer removes all thirteen:
`<!--figure:secondread-shipped-->strict+margin<!--/figure-->`, the
**<!--figure:secondread-adopted-->1<!--/figure-->** of
**<!--figure:secondread-configurations-->6<!--/figure-->** declared
configurations that meets all four pre-registered marks, answers
**<!--figure:secondread-program-correct-->366<!--/figure-->** correctly and
**<!--figure:secondread-program-wrong-->0<!--/figure-->** wrongly, giving up
**<!--figure:secondread-given-up-->150<!--/figure-->** answers where matched
refusal removes only **<!--figure:secondread-matched-removes-->2<!--/figure-->**
of the thirteen. What the guards promise rather than score is proved in
`RequestProject/GLM/SecondReading.lean`. Write-ups:
[`OPERATION_ESCALATION_STUDY.md`](studies/OPERATION_ESCALATION_STUDY.md),
[`SECOND_READING_STUDY.md`](studies/SECOND_READING_STUDY.md).

**What blocks fuller reasoning, measured rather than asserted.** The
pre-registered language probe — **<!--figure:probe-questions-->20<!--/figure-->**
questions, pass mark **<!--figure:probe-pass-mark-->10<!--/figure-->** — scores
**<!--figure:probe-correct-->2<!--/figure-->** correct,
**<!--figure:probe-wrong-->1<!--/figure-->** wrong,
**<!--figure:probe-refused-->17<!--/figure-->** refused: a declared failure,
kept as one. Widening the lexicon to
**<!--figure:probe-lexicon-held-->57<!--/figure-->** of the probe's
**<!--figure:probe-lexicon-words-->69<!--/figure-->** content words moved the
score by nothing, so the binding blocker is the absence of a parser from open
language to a query kind, and only
**<!--figure:probe-derived-->2<!--/figure-->** measured results are derivation
rather than lookup or addressing. Write-up:
[`BLOCKERS_STUDY.md`](studies/BLOCKERS_STUDY.md).

**One question path, and the tools on it.** `runtime/router.py` gives a text
to the first surface of `runtime/toolbox.py`'s catalogue that reads it — the
toolbox (`tools`, `tool <name>`), reverse Three Column Thinking (a text that
starts with one of its operation prefixes), the Python dialect (a program whose loaded
names are all bound), the engineering surface (its eight frames), then the
typed planner — and `GLM.py --ask` prints the surface beside the answer. The
eight tools are the modules the wiring audit found unreached (`moonshine`,
`llvq`, `pcgs`, `salvage`, `salvage second`, `deep dive`, and `tie break` and
`stability` for one named Lean declaration). `-q` still reads through the
planner and the grammar. The engineering surface's eighth frame derives
*across wheels* over the union of the ten wheels, with a shared name one
variable only where a declared junction identifies it
(`engineering/union.py`). Recomputed by `tools connected`; proved in
`RequestProject/GLM/ConnectedMachine.lean`. Write-up:
[`CONNECTED_MACHINE_STUDY.md`](studies/CONNECTED_MACHINE_STUDY.md).

**Chains of steps, each step in three columns.** When the typed planner
refuses, the router hands the text to `runtime/stepwise.py`, which composes
planner answers (operator words, function forms, predicates, `then`), finds
unasked steps over the wheels (goal and narrative questions), refuses by name
where readings or derivations disagree, and remembers the chain for `then …`
and `why?` under a SHA-256 digest of the conversation. Each step is checked in
columns 1 and 2, and `reasoning/stepwise_script.py` writes one column-3 script
that re-derives every step in a fresh interpreter. `GLM.py --steps TEXT` asks
it directly; recomputed by `tools stepwise`; proved in
`RequestProject/GLM/StepwisePlanner.lean`. Write-up:
[`STEPWISE_PLANNER_STUDY.md`](studies/STEPWISE_PLANNER_STUDY.md). Since
Phase 73 its leaves also read *how many more … than*, *how much larger (higher,
lower) … than*, *is … odd / even* and *the average of …*, and its goal mode
reads givens and targets written with units — through the declared exact unit
table of `runtime/quantity_units.py`, dimension-checked and converted into SI
— and givens read from the register through the Phase 55 scale table;
recomputed by `tools stepwise-two`; proved in
`RequestProject/GLM/StepwiseFrames.lean`. Write-up:
[`STEPWISE_TWO_STUDY.md`](studies/STEPWISE_TWO_STUDY.md). Since Phase 84 it
also reads comparatives through the declared table of
`runtime/declared_frames.py` (*heavier*, *lighter*, *denser*, *older*,
*newer*), the count nouns *electrons* and *valence electrons*, the tera- and
pico- prefixes, and folds — a sum, a mean or a parity count — over every
element or a declared class, one looked-up step per member and a column with
a missing reading refused `COLUMN_HOLE`; recomputed by `tools
stepwise-three`; proved in `RequestProject/GLM/StepwiseWiden.lean`. Write-up:
[`STEPWISE_THREE_STUDY.md`](studies/STEPWISE_THREE_STUDY.md). Since Phase
85 it also reads the median, the largest and the smallest value and the rank
of a row over a declared set, answers a median or a rank over a column with
holes as the exact interval over every completion of the holes (one value
when it closes, `COLUMN_HOLE` when a side is open), and answers the
present-rows question asked as its own with the missing rows named;
recomputed by `tools stepwise-four`; proved in
`RequestProject/GLM/HoleBounds.lean`. Write-up:
[`HOLE_FOLDS_STUDY.md`](studies/HOLE_FOLDS_STUDY.md). Since Phase 86 it
checks kinds of quantity as well as dimensions (`runtime/measurands.py`):
a unit restricted by the SI to one kind is refused for another
(`KIND_MISMATCH`), a Celsius or Fahrenheit temperature is read as a level or a
difference by the law that reads it and the conflations are refused by name,
and the defining constants `h` and `c` are supplied only when the givens alone
derive nothing; recomputed by `tools measurands`; proved in
`RequestProject/GLM/MeasurandKinds.lean`. Write-up:
[`MEASURANDS_STUDY.md`](studies/MEASURANDS_STUDY.md). Since Phase 87 it reads
a register value through a declared register of measurands
(`runtime/measurand_register.py`): an ionization energy or an electron
affinity is read per atom as a photon's energy on wheel W10, a radius feeds
no wheel by name, a power crosses a motor, generator, pump or turbine only
through a stated efficiency in (0, 1] (`EFFICIENCY_OUT_OF_RANGE`,
`EFFICIENCY_UNDECLARED`), and the elementary charge and the percent are
exact units; recomputed by `tools measurand-register`; proved in
`RequestProject/GLM/MeasurandRegister.lean`. Write-up:
[`MEASURAND_REGISTER_STUDY.md`](studies/MEASURAND_REGISTER_STUDY.md). Since
Phase 91 its fold frames are generated from one declaration
(`runtime/frame_declarations.py`) rather than written by hand, and the
widenings are entries in it: the `k`-th largest and smallest value and the
quartiles over a declared set, superlatives and the top `k`, *the bounds on* a
sum, a mean (through a declared physical range) or a parity count under holes,
the present-rows parity count, *the metals* and *the rare earths*, the twelve
remaining exact SI prefixes and *heavier*/*lighter* over the molecule table,
refusing `ORDER_OUT_OF_RANGE`, `TOP_K_TIE`, `RANGE_UNDECLARED`,
`TABLE_MISMATCH` and `COMPARATIVE_UNDECLARED`; recomputed by `tools
stepwise-five`; proved in `RequestProject/GLM/DeclaredFrames.lean`. Write-up:
[`DECLARED_FRAMES_STUDY.md`](studies/DECLARED_FRAMES_STUDY.md).

**The loop through the planner.** Since Phase 88 the Python dialect calls
the rest of the machine: `derive`, `ask` and `solve` return exact values from
the stepwise planner's goal mode, one stepwise question and the reverse
surface's linear solve (`runtime/planner_bridge.py`, builtins in
`reasoning/python_speech.py`), refusing `BRIDGE_UNAVAILABLE`,
`DERIVE_REFUSED`, `ASK_REFUSED` or `SOLVE_REFUSED`; a declared frame hands a
question about a Python expression to the evaluator; the router's Python
surface and `GLM.py` speak through it. The column-3 script re-runs each
sub-answer's own script, checks the value against its record and re-runs the
program under CPython against the checked table; recomputed by `tools
planner-loop`; proved in `RequestProject/GLM/PlannerLoop.lean`. Write-up:
[`PLANNER_LOOP_STUDY.md`](studies/PLANNER_LOOP_STUDY.md).

**The law register.** `reasoning/law_register.py` re-reads the 65 laws an
older GLM-lens review of the UBP knowledge base retained, frozen as
`reasoning/_data/law_register_65.csv`. Structural laws are cited to their Lean
theorems; the decoder's behaviour at every error weight is tabulated exactly
from the coset weight enumerators (right up to weight 3, refused at 4, wrong at
5, mixed above), with exact probabilities at any bit-flip rate and the price of
refusing at a six-way tie; and `look_elsewhere` is a refusal test for any
claimed numeric coincidence — the chance that the claim's own template, its
small integers varied over declared ranges, hits a target in `[T/2, 2T]` as
closely. `admit(law_id)` gives a verdict with its reason. Recomputed by
`tools law-register`; toolbox tool `law register`; proved in
`RequestProject/GLM/LawRegister.lean`. Write-up:
[`LAW_REGISTER_STUDY.md`](studies/LAW_REGISTER_STUDY.md).

**The laws absorbed.** `reasoning/law_absorption.py` gives each retained law
a fate — absorbed, already GLM, retested, retired — with its reason, and
computes the absorbed ones live from the substrate (`FACTS`): the code's
size, rate, weight counts, minimum distance and covering radius, the
decoder's outcome and exact probability at an error weight or noise rate, the
confidence of a decoding at a distance, the kissing number, XOR closure and
descent. The typed planner reaches them through the `substrate` frame of
`runtime/semantic_plan.py`, and every answer cites the law it was absorbed
from. Recomputed by `tools law-absorption`; proved in
`RequestProject/GLM/LawAbsorption.lean`. Write-up:
[`LAW_ABSORPTION_STUDY.md`](studies/LAW_ABSORPTION_STUDY.md).

**Held precision.** `reasoning/held_precision.py` writes the answer of a goal
or narrative chain as one monomial in its leaves, reads each register lookup
at the precision it was written to, and states the answer's exact interval
(attained at two corners of the box) as a note on the chain; a leaf whose
exponent is 0 has cancelled and the answer is stated as exact. Recomputed by
`tools held-precision`; proved in `RequestProject/GLM/HeldPrecision.lean`.
Write-up: [`HELD_PRECISION_STUDY.md`](studies/HELD_PRECISION_STUDY.md).

**Decoder confidence.** `reasoning/decoder_confidence.py` attaches the
absorbed confidence law to the decoder's own readings at a declared bit-flip
rate: the complete decoder's answer with its posterior (`TIE` at a deep hole),
the carried fork pruned to declared cases with the survivor's posterior under
the closed world, and the second reading's agreed codeword with the posterior
of the product of the reads' likelihoods — reached in the Python dialect as
`decode_confidence` and `agree_confidence`. Recomputed by
`tools decoder-confidence`; proved in
`RequestProject/GLM/DecoderConfidence.lean`. Write-up:
[`DECODER_CONFIDENCE_STUDY.md`](studies/DECODER_CONFIDENCE_STUDY.md).

**Confidence floor.** `reasoning/confidence_floor.py` gives `resolve` and
`agree` two readings at a declared bit-flip rate: the graded answer — the
value with its exact confidence and a band word (*near-certain*, *confident*,
*probable*, *uncertain*), never refused on confidence — and the floor, which
answers only at or above a declared confidence and otherwise refuses
`BELOW_FLOOR`, naming the confidence it had. Reached in the Python dialect as
`resolve_at`, `agree_at`, `resolve_floor` and `agree_floor`.
`reasoning/confidence_floor_marks.py` holds the exact channel census of the
decoder and the context stage and the hunt over a declared grid of rates and
thresholds. Recomputed by `tools confidence-floor`; proved in
`RequestProject/GLM/ConfidenceFloor.lean`. Write-up:
[`CONFIDENCE_FLOOR_STUDY.md`](studies/CONFIDENCE_FLOOR_STUDY.md).

**The second reading's channel.** `reasoning/agree_channel_marks.py` holds an
exact census of every pair of reads of one carrier, reduced by verified code
automorphisms to 28 rate-independent histograms, and places `agree` in the
confidence-floor hunt (working threshold 999/1000 at 1/10). Recomputed by
`tools agree-channel`; proved in `RequestProject/GLM/Agree.lean`. Write-up:
[`AGREE_CHANNEL_STUDY.md`](studies/AGREE_CHANNEL_STUDY.md).

**The rate from the reads.** `reasoning/rate_posterior.py` estimates the
bit-flip rate from the reads — an exact posterior over a declared grid with a
guard point — and answers with a confidence marginalized over it, refusing
`RATE_GRID_EXCEEDED` when the reads lean above the grid; the dialect reaches
it as `decode_soft`, `decode_soft_floor` and `agree_soft`.
`reasoning/rate_posterior_marks.py` measures its operating characteristics
exactly over every count vector. Recomputed by `tools rate-posterior`; proved
in `RequestProject/GLM/RatePosterior.lean`. Write-up:
[`RATE_POSTERIOR_STUDY.md`](studies/RATE_POSTERIOR_STUDY.md).

**The framed register.** `reasoning/second_view.py` stores a codeword in
views rotated by `0, 1, 3` and reads it by carrying the fork of view 0 and
pruning it by every further view, so a second reading of one carrier is
produced by the runtime itself; three views resolve every common-mode
four-error burst. The dialect reaches it as `store_views` and `read_views`.
Recomputed by `tools second-view`; proved in
`RequestProject/GLM/SecondView.lean`. Write-up:
[`SECOND_VIEW_STUDY.md`](studies/SECOND_VIEW_STUDY.md).

**The third view on demand, and argument unpacking.** `read_on_demand`
reads a framed register's first two views and the third only while the fork
is open: the three-view answer on every read inside the fault model, for
about two views a read; outside it, it answers where two views answer, so
the caller chooses it only where the fault model is trusted. The Python
dialect admits argument unpacking, `f(*xs)` and `def f(a, *rest)`, each a
named step re-derived in column 3. Recomputed by `tools unpacking`; proved
in `RequestProject/GLM/OnDemandView.lean`. Write-up:
[`UNPACKING_RESCORE_STUDY.md`](studies/UNPACKING_RESCORE_STUDY.md).

**The unresolved laws, triaged.** `reasoning/law_triage.py` gives each of the
106 `UNRESOLVED-UBP` knowledge-base laws one fate under a service rule (0
absorbed, 3 already served, 3 refuted, 100 retired with a reason). A record,
not consulted at run time. Recomputed by `tools law-triage`. Write-up:
[`LAW_TRIAGE_STUDY.md`](studies/LAW_TRIAGE_STUDY.md).

**Reverse Three Column Thinking.** `reasoning/reverse_tct.py` runs Three
Column Thinking backwards: the mathematics (column 2), given directly or read
off dialect source (column 3), generates the language column through a
declared prefix-first grammar (`the sum of A and B`), and a declared reader
parses the sentence back, so column 1 carries exactly the information of
column 2. Operations taken on the mathematics come back as sentences with
certificates: `say`, `equivalent`, `paraphrase`, `negate`, `solve for x`,
`entails` (Fourier–Motzkin with Farkas multipliers over ℚ, or two witness
points) and `bounds of x`. The router reads them by their prefix (`GLM.py
--ask "say: 2 * x + 3 == 7"`), and `GLM.py --reverse` prints the three
columns; `reasoning/reverse_tct_script.py` writes the column-3 script that
re-reads column 1 and re-checks the certificate. Recomputed by `tools
reverse-tct`; proved in `RequestProject/GLM/ReverseTCT.lean`. Write-up:
[`REVERSE_TCT_STUDY.md`](studies/REVERSE_TCT_STUDY.md).
Since round two the grammar also speaks the integer layer (`the floor
quotient of`, `the remainder of`, `the absolute value of`, `the minimum of`,
`the maximum of`, negative exponents), the bitwise operators and shifts, and
Golay masks as a second sort (`the mask of three positions one, two, three`,
the set operators, `the size of`, `is in`, `is contained in`); a statement is a
conjunction of clauses (`either A, or B, and C`), so `negate` answers any
statement by De Morgan followed by a meaning-preserving simplification;
`entails`, `bounds` and `equivalent` split disjunctions and `abs`, `min`,
`max` into cases. `relay: Q` (`runtime/reverse_relay.py`) answers Q, hands its
values and relations to the planner as questions in the planner's own input
language (`approximate v to 20 places`, `what fraction rounds to R`, `is a
less than b`), reads each answer back into column 2 (`AGREES`, `CONSISTENT`,
`DISAGREES`, `UNREAD`) and realises it as sentences of the reverse grammar,
which the column-3 script re-checks. Recomputed by `tools reverse-tct --two`;
proved in `RequestProject/GLM/ReverseTCTTwo.lean`. Since Phase 94 the
grammar has a third sort — strings, tuples and ranges with count-first
literals (`reasoning/reverse_tct_seq.py`, `tools third-sort`,
`RequestProject/GLM/ThirdSort.lean`) — and since Phase 95 an imperative
grammar for programs with state (`reasoning/reverse_tct_imp.py`: assignment,
loops, branches, functions and `match`, run with counted steps and bounded
depth, a trace of assignments in column 1 replayed by the script; `tools
imperative`, `RequestProject/GLM/ImperativeGrammar.lean`). Write-ups:
[`THIRD_SORT_STUDY.md`](studies/THIRD_SORT_STUDY.md),
[`IMPERATIVE_GRAMMAR_STUDY.md`](studies/IMPERATIVE_GRAMMAR_STUDY.md).

**A conversation, and what a reference costs.** `runtime/conversation.py` puts
an episodic register of turns in front of the session, so that a turn may
refer back to an earlier one. Three declared shapes are follow-ups and nothing
else is — a pronoun (*describe it*), an end-flip (*and the smallest?*) and a
subject substitution (*and oxygen?*) — and a candidate antecedent is
**licensed** exactly when the query it produces solves, so the reference is
decided by what the registers hold. Recency decides between turns, licensing
within one, and where the deciding side offers two licensed candidates the
layer refuses rather than choosing: the fourteen rows tied at the top of the
lexicon's `abstract_concrete` column give *describe it* fourteen equally good
referents. It binds **<!--figure:conversation-answered-->8<!--/figure-->** of
**<!--figure:conversation-declared-count-->15<!--/figure-->** declared
follow-ups and refuses **<!--figure:conversation-refused-->7<!--/figure-->**,
all **<!--figure:conversation-as-declared-->15<!--/figure-->** as declared,
where a session with no memory answers
**<!--figure:conversation-alone-->0<!--/figure-->**. No answer is new: every
rewritten query is answered by the solver that would have answered it written
out in full. Proved in `RequestProject/GLM/Conversation.lean`. Write-up:
[`CONVERSATION_STUDY.md`](studies/CONVERSATION_STUDY.md). Since Phase 92
`runtime/discourse.py` carries the state further: a fold's tie is a set the
turn produced and *it* names it, answered as a column of the rows' own
answers (`column-incomplete` under a hole); *the one before that*, *them*,
*both of them* (`number-mismatch`) and *why?* are read; the router is the
licence, so a follow-up any surface answers is bound; and `GLM.py --converse`
holds the conversation over every surface; recomputed by `tools
discourse-state`; proved in `RequestProject/GLM/DiscourseState.lean`.
Write-up: [`DISCOURSE_STATE_STUDY.md`](studies/DISCOURSE_STATE_STUDY.md).

**A relation written as one word, and a resolved follow-up kept.**
`reasoning/role_binding.py` writes a typed relation *R(A, B)* into a single
24-bit word by exclusive-or over parity readings, the role carried by a
permutation of the coordinates rather than by a carrier. Unbinding returns the
filler's reading with **no side condition** — proved in
`RequestProject/GLM/RoleBinding.lean` — and turning that reading into a *name*
is worth exactly what the registers are worth:
**<!--figure:binding-nameable-->424<!--/figure-->** of the
**<!--figure:binding-carriers-->1,143<!--/figure-->** carriers read uniquely
and the other **<!--figure:binding-ambiguous-->719<!--/figure-->** force a
refusal, the largest fibre holding
**<!--figure:binding-largest-fibre-->136<!--/figure-->** physics carriers at
all-zero parity. The product binding the same material offers beside it is
**refuted**: one zero coordinate makes two fillers bind alike, and
**<!--figure:binding-product-zero-->1,133<!--/figure-->** of the carriers read
zero somewhere. Beside it, `runtime/plan_store.py` keeps a resolved follow-up
— refusals exactly as bindings — under a digest of the whole conversation it
was resolved in, and `Conversation` takes one as an optional `store=`: all
**<!--figure:planstore-replayed-->15<!--/figure-->** declared follow-ups replay
unchanged and the licensing trials fall from
**<!--figure:planstore-trials-first-->27<!--/figure-->** to
**<!--figure:planstore-trials-replayed-->0<!--/figure-->**. Proved in
`RequestProject/GLM/PlanStore.lean`. Write-up:
[`SUPPLIED_PORTS_STUDY.md`](studies/SUPPLIED_PORTS_STUDY.md).

**Frames that derive, with a certificate.** The typed planner, the default
reading of every command-line question since Phase 63, carries frames whose
answers no register holds, each checked by `reasoning/certificates.py`:
Bézout, linear Diophantine equations and bounded factorisation (Phase 62);
consistency of a register value with a quoted value or the declared standard,
read at the precision each is held to, with an ordering between overlapping
readings refused; the simplest fraction a decimal pins down, answered only
when every rival's denominator is at least twice the answer's; and dimensional
equations solved exactly, with a certificate for unique, impossible and
undetermined. `python3 -m glm_universal.tools cognition` runs every experiment
of the study; the certificates are proved in
`RequestProject/GLM/CognitionRoundTwo.lean`. Write-up:
[`SUBSTRATE_NATIVE_COGNITION_STUDY.md`](studies/SUBSTRATE_NATIVE_COGNITION_STUDY.md).

**Python, spoken exactly.** `GLM.py --python SOURCE` evaluates a declared
dialect of Python — `int`, `Fraction`, `bool`, `str` with slicing, tuples of
up to 24 items, frozensets of coordinates `0..23`, `range`, pure functions,
loops and `match` — on the substrate, and answers with three columns whose
third is a script run in a fresh `python3 -I`; floats, non-deterministic
calls, deep-hole ties, uncorrectable distances and cross-scale comparisons are
named refusals. `python3 -m glm_universal.tools python-speech` re-takes the
measurement; the substrate operations are proved in
`RequestProject/GLM/PythonSpeech.lean`. Write-up:
[`PYTHON_SPEECH_STUDY.md`](studies/PYTHON_SPEECH_STUDY.md).

**Question frames, for questions written outside the project.**
`runtime/question_frames.py` holds declared frames that read a question as
written by someone else — a Routh range, a per-unit rebase, a reflection
coefficient, an aliasing fold, an entropy, a Huffman code, a water-filling
allocation, a Golay coset question, and the Set B items — and each answer is
re-derived by its own column-3 script before it is printed. `GLM.py -q` goes
through the multi-surface router (`--plan` keeps the typed planner's path).
The plain readings print their confidence under the production contract of
the 4-way matrix: the upper-credible rate rule over the session's reads
(`reasoning/contract_matrix.py`, `rate_posterior.PRODUCTION_RULE`).
Recomputed by `tools question-set-b` and `tools contract-matrix`. Write-ups:
[`QUESTION_SET_B_STUDY.md`](studies/QUESTION_SET_B_STUDY.md),
[`CONTRACT_MATRIX_STUDY.md`](studies/CONTRACT_MATRIX_STUDY.md).

**Formulas in letters.** `reasoning/symbolic.py` computes exactly with
rational functions of named parameters; `solve symbolically for T: EQ; EQ`
(`runtime/symbolic_frames.py`) eliminates unknowns by declared substitution,
or by Cramer's rule with Bareiss determinants for a square linear system of
four or more, and prints the formula with its nonzero conditions; its
column-3 script checks every law at six rational points. Fourteen outside
frames (`runtime/symbolic_outside.py`) answer the class-S questions and the
class-T crossover. Recomputed by `tools symbolic`; proved in
`RequestProject/GLM/SymbolicParameters.lean`. Write-up:
[`SYMBOLIC_PARAMETERS_STUDY.md`](studies/SYMBOLIC_PARAMETERS_STUDY.md).
A second layer, the branch layer (`reasoning/symbolic_nonlinear.py`, with
`reasoning/symbolic_algebraic.py` for exact real algebra), answers what
substitution refuses `NONLINEAR`, and also what it answers only by the
positive-root convention: it gives every real solution as a branch —
square roots, towers of square roots, Cardano's root, or bracketed algebraic
numbers `root(f, lo, hi)` — with stated real conditions, checks every branch
against every equation, and keeps the substitution reading beside its own
when that reading verifies. A cubic in letters with three real roots is
answered as a ratio of the letters times a bracketed algebraic number, or by
Viète's trigonometric form. Numeric polynomials are factored over the
rationals up to degree 24 (Kronecker's search to degree 6, Zassenhaus's
algorithm past it, `reasoning/symbolic_factor.py`). A root of an irreducible
factor of prime degree at least 5 with exactly two non-real roots is stated
to have no expression in radicals. So is a root of an irreducible factor of
prime degree whose factorisation modulo some prime has a cycle shape no
affine map has (Galois's theorem, read through a Frobenius element), which
reaches `x^5 - x - 1` and Trinks's septic. In composite degree, a root is
stated to have none when one prime shows the cycle type `(n - 1, 1)` and some
prime shows a cycle type with a power that is a single transposition or
3-cycle (primitivity and Jordan's theorem), which reaches `x^6 - x - 1`; the
same test is applied on the `modes.higher` route, so the normal modes of a
chain pendulum of five or six links carry the reason. A polynomial that is a
composition `g(h(x))` with an imprimitive group, out of reach of those tests,
is decomposed exactly, and a root is stated to have no expression in radicals
when the outer polynomial `g` passes one of them, which reaches
`x^10 - x^2 - 1`. In a degree that is not a prime power (6, 10, 12, …) the
one element of cycle type `(n - 1, 1)` is enough, because a solvable
primitive group has prime-power degree (Galois), which reaches sextics whose
group is `PGL(2, 5)` or `PSL(2, 5)` on six points. When a polynomial in letters of
such a degree is refused, the refusal names a rational point of the letters
where that holds, so no formula in radicals of the letters exists. Recomputed by
`tools nonlinear`, `tools cubic-radical`, `tools cubic-trig`,
`tools quintic-radical`, `tools frobenius-radical`,
`tools primitive-radical`, `tools composed-radical` and
`tools primitive-degree`; proved in
`RequestProject/GLM/NonlinearElimination.lean`,
`RequestProject/GLM/CubicRadicals.lean`,
`RequestProject/GLM/CubicTrig.lean`,
`RequestProject/GLM/QuinticRadicals.lean`,
`RequestProject/GLM/FrobeniusRadicals.lean`,
`RequestProject/GLM/PrimitiveRadicals.lean`,
`RequestProject/GLM/ComposedRadicals.lean` and
`RequestProject/GLM/PrimitiveDegree.lean`. Write-ups:
[`NONLINEAR_ELIMINATION_STUDY.md`](studies/NONLINEAR_ELIMINATION_STUDY.md),
[`CUBIC_RADICAL_STUDY.md`](studies/CUBIC_RADICAL_STUDY.md),
[`CUBIC_TRIG_STUDY.md`](studies/CUBIC_TRIG_STUDY.md),
[`QUINTIC_RADICAL_STUDY.md`](studies/QUINTIC_RADICAL_STUDY.md),
[`FROBENIUS_RADICAL_STUDY.md`](studies/FROBENIUS_RADICAL_STUDY.md),
[`PRIMITIVE_RADICAL_STUDY.md`](studies/PRIMITIVE_RADICAL_STUDY.md),
[`COMPOSED_RADICAL_STUDY.md`](studies/COMPOSED_RADICAL_STUDY.md),
[`PRIMITIVE_DEGREE_STUDY.md`](studies/PRIMITIVE_DEGREE_STUDY.md).

**Where an expression is already computed.** `reasoning/ast_index.py` holds
a frozen index of the 11,669 statement-level expressions that compute
something in the live code and in the archived GLM tree, bucketed by a key
that renaming and operand order cannot move and decided by an exact
structural matcher; ``where is `EXPR` computed?``
(`runtime/ast_index_frames.py`) lists every structurally equal site with
its witnessing renaming, and its column-3 script re-decides the whole bucket
with a separately written reference. Recomputed by `tools ast-index`;
proved in `RequestProject/GLM/AstIndex.lean`. Write-up:
[`AST_INDEX_STUDY.md`](studies/AST_INDEX_STUDY.md).

**Derivations and proofs.** `reasoning/proof_search.py` proves or refutes
a propositional sequent (`prove: PREMISES |- GOAL`) with a G4ip proof, a
classical proof from the fewest excluded-middle instances plus a Kripke
countermodel, or a falsifying valuation; `reasoning/derivation.py` derives
Euler–Lagrange equations with their linearisation and normal modes, transfer
functions of a linearised dynamic model, and flux-form boundary value
profiles. The frames are `runtime/derivation_frames.py`, and every answer's
column-3 script (`runtime/derivation_scripts.py`) re-decides it in exact
arithmetic without importing the package. Recomputed by `tools derivation`;
proved in `RequestProject/GLM/Derivations.lean`. Write-up:
[`DERIVATION_STUDY.md`](studies/DERIVATION_STUDY.md).

**The rest of track P.** `reasoning/info_inequality.py` decides a linear
information inequality of up to four variables: a Shannon-type certificate
from an exact simplex, a GF(2) linear distribution that violates it, or —
when neither exists — a Farkas polymatroid witness and the verdict
`NOT_SHANNON`. `reasoning/coding_theory.py` decides unique decodability
(Sardinas–Patterson, the shortest ambiguous string), builds canonical prefix
codes, derives the Hamming rate–distortion function where the Shannon lower
bound is tight (`NOT_TIGHT` on the gap) and the BSC rate posterior on the
machine's grid; `reasoning/maxent.py`, `reasoning/spectral.py` (eigenvalue
problems and transmission at one point) and `reasoning/fft_derivation.py`
complete the eight operations. The frames are
`runtime/derivation_two_frames.py`; every answer's column-3 script
(`runtime/derivation_two_scripts.py`) re-decides it without importing the
package. Recomputed by `tools derivation-two`; proved in
`RequestProject/GLM/DerivationsTwo.lean`. Write-up:
[`DERIVATION_TWO_STUDY.md`](studies/DERIVATION_TWO_STUDY.md).

**Past the second derivation study.** A claim the inequality prover leaves
`NOT_SHANNON` goes on to `reasoning/non_shannon.py`: a certificate using the
Zhang–Yeung inequality, each instance certified by the copy lemma over five
variables (`proved_non_shannon`), or a rational distribution from a pool
whose entropies, as sums of logarithms of primes, violate the claim exactly
(`NOT_VALID_ENTROPIC`). `reasoning/hamming_rd.py` takes Hamming rate
distortion past the Shannon lower bound, piece by piece, with a rational test
channel and dual point meeting exactly; `reasoning/robin.py` answers
eigenvalue problems with one Robin end, with certified enclosures of the
roots. The readings (`runtime/derivation_three_frames.py`) are handed over
from the Phase 107 operations; every answer's column-3 script
(`runtime/derivation_three_scripts.py`) re-decides it without importing the
package. Recomputed by `tools derivation-three`; proved in
`RequestProject/GLM/NonShannon.lean`. Write-up:
[`DERIVATION_THREE_STUDY.md`](studies/DERIVATION_THREE_STUDY.md).

**Past the third derivation study.** A four-variable claim still
`NOT_SHANNON` after Zhang–Yeung and the pool goes on to
`reasoning/copy_chain.py`: chains of copies (a copy of one variable over a
set, then a copy of the same variable over the set and the first copy) with an
exact Shannon-type certificate over six variables (`proved_by_copies`); the
same module reads five-variable claims (the exact search, Zhang–Yeung on every
four, rational laws lifted to five). `reasoning/general_rd.py` encloses the
rate-distortion function of any finite distortion matrix between a channel of
distortion at most `D` and a dual point, both bracketed in integer fixed
point. `reasoning/robin_two.py` answers Robin conditions at both ends, a
symbolic coefficient (case by case in its sign class), a negative coefficient
on a symbolic interval (case by case in `L`), and closed-form arctangent
bounds on a symbolic interval. The readings (`runtime/derivation_four_frames.py`)
are handed over from the Phase 107 and Phase 118 readings; every answer's
column-3 script (`runtime/derivation_four_scripts.py`) re-decides it without
importing the package. Recomputed by `tools derivation-four`; proved in
`RequestProject/GLM/CopyLemma.lean` (the copy lemma and Zhang–Yeung for every
finite distribution) and `RequestProject/GLM/RobinBoth.lean`. Write-up:
[`DERIVATION_FOUR_STUDY.md`](studies/DERIVATION_FOUR_STUDY.md).

**Questions about the machine, answered from its documents.**
`reasoning/meta_evidence.py` holds eighteen topics, each a cue, the
sentences it quotes from six studies (found by a declared fragment when the
question is read, with the section they sit in), the Lean declarations it
cites (found in the stored address book), code facts and the premises the
documents contradict. `runtime/meta_frames.py` reads a question that names
the machine and one topic, last among the frames, and answers with the
quotes, the theorems, the disputes and a column-3 script that re-checks all
three; a quote or theorem that has moved makes the reading the refusal
`CITATION_MOVED`. Recomputed by `tools meta-questions`; proved in
`RequestProject/GLM/MetaAnswers.lean`. Write-up:
[`META_QUESTIONS_STUDY.md`](studies/META_QUESTIONS_STUDY.md).

**Why questions, answered in the part that is decided.**
`data_objects/nuclides.py` is a nuclide register: the AME2020 mass table and
NUBASE2020, frozen with the digests of the raw IAEA files, 3558 ground states
with exact mass excesses, half-lives and decay modes; binding energies,
Q-values and separation energies are computed from it exactly, and a value
from systematics is refused unless asked for. `reasoning/explanation_anchors.py`
holds thirty-five topics, each answering the part of a *why* question that the
element register, the nuclide register or an exact derivation decides, and
stating the account it asks for as refused `EXPLANATION`; a register that
contradicts the question's premise is reported as a dispute. Each answer's
column-3 script embeds the rows it read and fails if its claim or a row is
altered. `runtime/explanation_frames.py` reads the questions last among the
frames. Recomputed by `tools explanations`; proved in
`RequestProject/GLM/ExplanationAnchors.lean`. Write-up:
[`EXPLANATION_ANCHOR_STUDY.md`](studies/EXPLANATION_ANCHOR_STUDY.md).

**The share-carrying rungs, read at 30720 starts.**
`reasoning/share_ensemble.py` extends the deep-hole ladder's ensembles from
1920 to 30720 starts at both seeds for the ten reference holes and stores
them as sufficient statistics beside the digest of the code that emitted
them; `reasoning/share_separation.py` applies the ladder's own readings to
them at every size, with a per-hole ratio beside the ladder's global one and
the bound that the sorted share shift never exceeds the vertex-matched shift.
No share-carrying cell reaches `rho < 1`: the arrival shares approach a
near-uniform profile, so holes with equal vertex counts converge on each
other, and the per-hole criterion certifies all but the 28-vertex pair.
Recomputed by `tools share-separation` (the ensembles by `tools
share-ensemble --write`); proved in `RequestProject/GLM/ShareSeparation.lean`.
Write-up: [`SHARE_SEPARATION_STUDY.md`](studies/SHARE_SEPARATION_STUDY.md).

**The configuration reading.** `reasoning/configuration_reading.py` reads the
same stored ensembles through the vertex configuration rather than a sorted
list of shares: the arrival vertices are joined as the affine Dynkin diagram
of the hole (one edge at squared distance `3r²`, two at `4r²`), each vertex is
keyed by its component size and degree, and the arrival shares are pushed
forward along the key. The rung `L5` has `rho < 1` at every size from 1920
starts and certifies all ten reference holes, the 28-vertex pair
`E_6^4`/`D_6^4` included. Recomputed by `tools configuration-reading`; proved
in `RequestProject/GLM/ConfigurationReading.lean` (the bound, the
uniform-limit distance `4/7` of the pair and the separation floor). Write-up:
[`CONFIGURATION_READING_STUDY.md`](studies/CONFIGURATION_READING_STUDY.md).

**The configuration reading in the answering path.** `report hole
configuration` answers a deep-hole query by `L5` only inside half the
distance from its nearest reference to the next — inside that radius the
answer is provably the strict nearest
(`GLM.LatticeCompletion.config_answer_sound`) — and refuses otherwise; every
other type further than its certified radius is issued as an absence, a
theorem under faithfulness (`config_absent`). A reference centre now exists
for all 23 Niemeier types (three certified post hoc), and the power-of-two
ladder has a rung at norm 2 (`D12^2`); norm 256 is still empty. Recomputed by
`tools configuration-classifier`, `hole-census`, `patience-census`,
`empty-rungs` and `frozen-path`; proved in
`RequestProject/GLM/LatticeCompletion.lean`. Write-up:
[`LATTICE_COMPLETION_STUDY.md`](studies/LATTICE_COMPLETION_STUDY.md).

**The probe budget.** `reasoning/probe_budget.py` gives the certifying
reading of a deep hole a declared stop: no barren stop, and a budget of 1056
starts, which `RequestProject/GLM/ProbeBudget.lean` proves keeps the union
bound on an unseen vertex at `1/1000` for every Niemeier type when every
vertex's share is at least `1/(2k)` — a hypothesis that holds on every stored
ensemble. It certifies every reference centre and every deep hole of 256
held-out walks. Recomputed by `tools probe-budget`. Write-up:
[`PROBE_BUDGET_STUDY.md`](studies/PROBE_BUDGET_STUDY.md).

**The operations ladder.** `reasoning/ops_ladder.py` holds the owner's
DevOps-ladder note as a register of 97 terms, each a declared composition of
lower ones, which the GLM reads for *part of*, shared parts and ground
overlap, and projects onto the Geometric–Cybernetic ladder; 14 cross-overs
name objects the package already held (drift, fixed point, the reversible
gates, delta-sigma, the probe budget, the router, the sign-off). Its lowest
tiers are GLM-BAT (`reasoning/batch_machine.py`,
`reasoning/batch_speech.py`), an old-style batch machine whose programs the
GLM says and reads as English sentences: `tool machine QUESTION :: PROGRAM`
answers what a program prints, leaves or exits with, whether it halts (a
trace, or a repeated control state, which
`RequestProject/GLM/OperationsLadder.lean` proves sufficient) or is
idempotent, each with a column-3 Python certificate, and refuses by name
otherwise. Recomputed by `tools ops-ladder`. Write-up:
[`OPERATIONS_LADDER_STUDY.md`](studies/OPERATIONS_LADDER_STUDY.md).
Since Phase 126 a run whose control state does not recur within the budget is
read once more with its *inert* variables forgotten — those no line reads
except to update an inert variable (`batch_machine.inert_variables`) — so a
loop with a growing counter is answered *never halts*, with the forgotten
names in the answer and a column-3 script that re-checks both the closure and
the recurrence; `RequestProject/GLM/InertCounter.lean` proves the forgetful
recurrence sufficient. Recomputed by `tools inert-counter`. Write-up:
[`INERT_COUNTER_STUDY.md`](studies/INERT_COUNTER_STUDY.md).

**Norm 256 and the hex colour.** Since Phase 127 the power-of-two family has
a rung at norm 256, measured beside the ladder rather than in the answering
path: `H16` reads each coordinate by its first hex digit `⌊v/16⌋`, the
nearest point of `16ℤ + 8` (`RequestProject/GLM/HexRung.lean`,
`floor_bucket_nearest`). The same file builds the Leech lattice rotated by
`√2` — `(1 + hexRot)(2Λ₂₄)`, minimum norm 256 (`rotLeech_min_norm`) — which was
retired for wrong answers, and `reasoning/norm256_hex.py` measures the hex
shortcut it carries: the classes of `Λ₂₄/2Λ₂₄` are the 2²⁴ hex colours, and a
`2C` point lies on the rotated rung exactly when the colour of its half is in
a 4096-colour subspace. Recomputed by `tools norm256-hex`. Write-up:
[`NORM_256_HEX_STUDY.md`](studies/NORM_256_HEX_STUDY.md).

**Temperatures on two scales.** The field surface's table `fixed_point`
holds the fourteen ITS-90 fixed points in degrees Celsius
(`data_objects/fixed_points.py`), and the scale table's row
`fixed_point:temperature_C` is its one offset row (273.15): the ordering and
extremum operations carry a Celsius reading into kelvins before comparing,
and the stepwise planner reads it as a level through
`quantity_units.scale_into_si_affine`, while `scale_into_si` (a factor alone)
refuses an offset row `OFFSET_UNIT`. Recomputed by `tools celsius-register`;
proved in `RequestProject/GLM/CelsiusRegister.lean`. Write-up:
[`CELSIUS_REGISTER_STUDY.md`](studies/CELSIUS_REGISTER_STUDY.md).

**Which retrieval leads are results.** `reasoning/corpus_resample.py` ranks
every declaration of the Lean corpus as a query under the native-words and
native-parity rankings once, and reads off that census every sub-corpus that
drops one file and every offset of the query stride
(`GLM.CorpusResample.sorted_perm_filter_eq` is why filtering is exact,
`take_filter_take` why 108 places are enough). Under the declared rule the
two-book native ranking's lead over the raw structural vector on declaration
queries is an effect, and the other resampled leads are draws. Recomputed by
`tools corpus-resample`; proved in `RequestProject/GLM/CorpusResample.lean`.
Write-up: [`CORPUS_RESAMPLE_STUDY.md`](studies/CORPUS_RESAMPLE_STUDY.md).

**Registers.** Eight of them. Physics (726 quantities, EXT10 exponents and
unit strings cross-checked against each other), chemistry (118 elements),
molecules (51 species and ions, every coordinate derived from the element
register at load time), mathematics, lexicon (95 concepts, 380 explicit
relation triples), spatial, harmonics (28 musical intervals as exact rational
frequency ratios) and economics (21 quoted prices as exact rationals), beside
a 45-class comparison register.

**Reasoning.** 80 modules. Analogy by named relation, dimensional
verification, Buckingham-Pi from an exact rational nullspace, the
Walsh–Hadamard transform decoder, the deep-hole walk, term arithmetic, unit
parsing with the steradian priced rather than silently redefined, and
element-coverage widening that labels every widened cell by provenance.

**Values.** Reals held as processes with no float anywhere; written arithmetic
over them including `exp`, `log`, `sin`, `cos`, `tan` and real powers; decided
inequality and refused equality; the delta–sigma modulator with its proved
`1/N` rate and, in 24 coordinates, the separating functional that proves a
target outside the hull unreachable.

**Meaning.** The grounded graph — 357 meanings, 1,705 notations, 12,859 edges,
every one re-derived on demand. The inherited ARC-era concept graph was
audited and demoted to evidence, and `tests/test_inherited_graph.py` enforces
that by walking the imports of every module that answers a question.

**Measurement.** Three instruments that do not trust each other: probes
(library boundaries), benchmarks (solver functions) and the end-to-end
evaluation (the CLI in a fresh interpreter per question, scored asymmetrically
so a confident wrong answer is worse than a refusal). Write-up:
[`CAPABILITY_ASSESSMENT.md`](CAPABILITY_ASSESSMENT.md).

**The Lean development, addressed.** `reasoning/lean_address.py` gives each of
the <!--figure:lean-declarations-->4,975<!--/figure--> declarations a deterministic Leech address computed from 24 structural
counts of its statement. Read back exactly <!--figure:lean-declarations-->4,975<!--/figure-->/<!--figure:lean-declarations-->4,975<!--/figure--> with 0 coordinate errors;
3989 distinct addresses, and the quantiser adds no conflation of its own;
nearest-by-address shares a file 817 times against 35 for a SHA-256 control and
29 for a seeded reshuffle, with chance at ≈ 0.80 %. `report lean`.
Write-up: [`LEAN_ADDRESS_STUDY.md`](studies/LEAN_ADDRESS_STUDY.md).

**The register where the address is the only reader.** In the anonymous
register a query's identifiers are not the corpus's, by theorem
(`GLM.Anonymous.overlap_anonymise_eq_zero`): over 883 queries the text search
falls 767 → 85 and the identifier address book 413 → 46 against 49 by chance,
where the structural address holds 258 → 182. Write-up:
[`ANONYMOUS_REGISTER_STUDY.md`](studies/ANONYMOUS_REGISTER_STUDY.md).

**The standing rules, as instruments.**
[`PROJECT_DIRECTIVES.md`](PROJECT_DIRECTIVES.md) states <!--figure:directives-->16 standing rules<!--/figure--> and
names the instrument for each. `reasoning/directives.py` parses that file and
gives each instrument a live verdict (`report directives`) — **16 of 16** with
every named instrument present; `reasoning/pipeline.py` reads the stage each
piece of work has reached off the tree rather than from prose — **30 of 30
rows** through all six stages (`report pipeline`); `glm_universal/signoff/`
computes a module's dependency closure with `ast` and plans a run against
recorded digests, so nothing unchanged is checked twice (§4.1); and
`glm_universal/integrity.py` holds every SHA-256 use one module above the six
core sub-packages, which the purity audit enforces. `glm_universal/tools.py`
is their command line, kept out of the core for the same reason.

**What a refusal is evidence of.** `reasoning/probe_oracle.py` translates each
of the twenty pre-registered probe questions into the query grammar by hand
and classifies it: `parsed` when a query already answers it at a declared
field, `surface` when a register row or a shipped function holds the answer
and no query kind returns it, `absent` when nothing holds it. The split is
<!--figure:oracle-parsed-->6<!--/figure--> /
<!--figure:oracle-surface-->10<!--/figure--> /
<!--figure:oracle-absent-->4<!--/figure--> of
<!--figure:oracle-questions-->20<!--/figure-->. It keeps no measurement cache
— a live session answers twenty queries in seconds — and
`GLM.ProbeOracle.counts_partition` is why the three counts read the same
twenty questions rather than three samples. `tools oracle`. Write-up:
[`PROBE_ORACLE_STUDY.md`](studies/PROBE_ORACLE_STUDY.md).

**The field surface, and what it was worth.** `runtime/fields.py` answers one
named field of one named row — `field atomic_weight_u of carbon` — over
<!--figure:fieldsurface-tables-->14<!--/figure--> declared tables holding
<!--figure:fieldsurface-rows-->13,190<!--/figure--> rows and
<!--figure:fieldsurface-pairs-->77,588<!--/figure--> addressable `(row,
field)` pairs: the element and molecule source rows, one table per register's
carrier attributes, the Lean address book, the package's own top-level
definitions, and a registry of declared zero-argument functions whose returned
mapping is addressable by key. Its second shape, `fields of <row>`, names the
fields a row answers to. It refuses at three boundaries — an unknown row, an
unknown field of a known row, and a field the register records as missing —
and it says of itself, in every answer, that it is `table`: it derives
nothing. Measured against the oracle's prediction it answers
<!--figure:fieldsurface-moved-->9<!--/figure--> of the
<!--figure:fieldsurface-held-->10<!--/figure--> held-and-unreachable
questions, which is exactly the <!--figure:fieldsurface-predicted-->9<!--/figure-->
declared reachable before the run, taking the probe from
<!--figure:fieldsurface-parsed-before-->6<!--/figure--> parsed to
<!--figure:fieldsurface-parsed-after-->15<!--/figure-->; the tenth is a
comparison across two rows and needs an operation rather than a surface.
`GLM.FieldSurface` proves the boundary is the tables' rather than a search's.
`tools fieldsurface`. Write-up:
[`FIELD_SURFACE_STUDY.md`](studies/FIELD_SURFACE_STUDY.md).

**The ordering operation, and the refusal it is built around.**
`reasoning/coordinate_order.py` reads one coordinate off *two* rows through
the field surface and orders them exactly in rationals — `order
abstract_concrete of energy and water`, the `ordering` query kind. Each side
is a *reading*: a value together with the scale it was read on, `table:field`,
and a coordinate held inside a mapping field — which is how the lexicon
register keeps its ten semantic primitives — is read as a coordinate of that
field. It refuses in <!--figure:ordering-reasons-->3<!--/figure--> named ways:
a coordinate the row does not hold, a reading that is a label rather than a
quantity, and two readings on different scales. The last is the point of it,
and it is proved rather than asserted:
`GLM.CoordinateOrder.naive_order_is_not_scale_free` exhibits a positive
rescaling that flips the comparison of two raw numbers, while
`order_scale_invariant` shows that no rescaling of a shared scale can.
Measured on <!--figure:ordering-declared-count-->7<!--/figure--> comparisons
declared before the run it answers <!--figure:ordering-answered-->4<!--/figure-->
and refuses <!--figure:ordering-refused-->3<!--/figure-->, every one as
declared, and it closes the one probe question the field surface named as
unreachable — all <!--figure:ordering-held-->10<!--/figure-->
held-and-unreachable questions are now parsed. `tools ordering`. Write-up:
[`ORDERING_STUDY.md`](studies/ORDERING_STUDY.md).

**The column, not the pair.** The `extremum` query kind reads one coordinate
off **every** row of one declared table and returns the end of it, or refuses.
The end is read off the word that opens the question — `largest`, `highest`,
`maximum` against `smallest`, `lowest`, `minimum` — and every row attaining it
is named rather than one of them picked: fourteen of the lexicon register's
rows sit at the concrete end of `abstract_concrete`, and choosing between them
would be a choice the register does not make. It refuses in
<!--figure:extremum-reasons-->4<!--/figure--> named ways, two of them boundaries
the system had no way to state before. A column with a hole in it has no
extremum — 23 of the element register's 118 rows record
`electronegativity_pauling` as missing, and
`GLM.ColumnExtremum.extremum_over_present_is_not_the_extremum` exhibits a
column where the extremum over the rows that are filled in is a different value
at a different row, so an answer over the present rows is wrong rather than
partial. A column gathered from two scales is not one column, which is the
ordering operation's `different-scale` one level up, and
`extremum_not_invariant_under_one_row_rescaling` is why. Measured on
<!--figure:extremum-declared-count-->8<!--/figure--> columns declared before the
run it folds <!--figure:extremum-answered-->4<!--/figure--> and refuses
<!--figure:extremum-refused-->4<!--/figure-->, every one as declared.
`tools extremum`. Write-up:
[`COLUMN_EXTREMUM_STUDY.md`](studies/COLUMN_EXTREMUM_STUDY.md).

**The scales, written down.** `reasoning/scale_conversion.py` holds the
declared table the two operations above did not have: one row per scale,
naming the quantity it measures, the canonical unit of that quantity and the
exact positive-affine map into it, together with the source the numbers came
from. <!--figure:scales-rows-->10<!--/figure--> rows over
<!--figure:scales-quantities-->4<!--/figure--> quantities — mass in `u`, molar
energy in `kJ·mol⁻¹`, temperature in `K`, length in `pm`. The ordering
operation consults it when the two readings are on different scales and the
extremum operation when a column is gathered by quantity rather than by table,
so `largest mass` now folds the element rows and the molecule rows together;
neither gains an answer anywhere the table is silent, and
`GLM.ScaleConversion.orderWith_conservative` is that stated rather than
hoped. That a conversion may be composed into a comparison at all is
`cmpQ_apply` and `order_conversion_invariant`; that the declaration and not
the code is what licenses a bridge is `the_table_carries_the_claim`; the two
things it must not do are `negative_factor_flips_the_verdict` and
`raw_gather_names_the_wrong_row`. Measured on
<!--figure:scales-declared-->12<!--/figure--> questions declared before the run
it answers <!--figure:scales-answered-->7<!--/figure--> and refuses
<!--figure:scales-refused-->5<!--/figure-->, every one as declared, and across
the whole field surface it relates
<!--figure:scales-bridged-->8<!--/figure--> of
<!--figure:scales-pairs-->7,875<!--/figure--> pairs of
<!--figure:scales-numeric-->126<!--/figure--> numeric scales — the rest stay
refused, which is what *declared* costs. `tools scales`. Write-up:
[`SCALE_CONVERSION_STUDY.md`](studies/SCALE_CONVERSION_STUDY.md).

**Typed question plans.** `runtime/semantic_plan.py` is the bridge from an
English question to the operations the session already has:
**<!--figure:plans-frames-->20<!--/figure-->** frames, each of which reads one
shape of question into a plan whose slots are grounded against the field
surface and the row's own fields, run, and accepted only when every licensed
plan agrees; with none licensed the answer is the grammar's own. Two frames
compute — exact integer arithmetic, and conversion over a declared table of
**<!--figure:plans-units-->17<!--/figure-->** units whose factors are
definitions. Reached with `GLM.py --plan` or
`GeometricSession.ask_planned`; measured by `tools plans` on the frozen probe
and four sets in `evaluation/heldout.py`, three of them committed before the
planner existed. Proved in `RequestProject/GLM/SemanticPlan.lean`. Write-up:
[`SEMANTIC_PLAN_STUDY.md`](studies/SEMANTIC_PLAN_STUDY.md).

**The round loop itself, measured and cut.** A named `.lean` file resolves to
itself rather than to the whole development, so a median Lean file makes **26**
units stale rather than 84 of 97, and a unit's closure is **116** files rather
than 332. On top of that, a documents check no longer recomputes a stale
derived artefact: it names the artefact and the refresh that rebuilds it, so
`corpus --check` is a matter of seconds whatever else has moved, and the
minutes are paid once by `corpus --refresh`. Write-up:
[`ITERATION_COST_STUDY.md`](studies/ITERATION_COST_STUDY.md) §5a and §5b.


---

## 3. What the evaluation finds, and what is ongoing

### 3.1 The evaluation finds no gap

The end-to-end set is **177 of 177** and every one of its twenty-eight refusals is a
`boundary` — a theorem or a stated commitment — rather than a `gap`. What
remains open is listed below, and none of it is a question the evaluation set
asks.


### 3.2 Ongoing rather than finishable

* **`related_to` as a residue.** 66 of the lexicon's 380 triples record that a
  link exists without saying which; all 66 are now *decided* rather than
  declined, 34 without a person, and `closure()` reports **0 triples waiting on
  a lookup**. What stays ongoing is that the lexicon can always grow another
  vague triple ([`DENOTATION_STUDY.md`](studies/DENOTATION_STUDY.md),
  [`VAGUENESS_STUDY.md`](studies/VAGUENESS_STUDY.md)).
* **Sparse chemistry.** 1,257 of 1,652 element cells are measured; the
  completed view reaches 1,344 by rules admitted only for halving the field's
  own out-of-sample mean and for surviving a nested holdout of their own
  selection (Phase 93), and each of the remaining 308 carries a stated
  reason. The register is read against cited outside values, never written
  ([`REGISTER_WORLD_STUDY.md`](studies/REGISTER_WORLD_STUDY.md)). Nothing is written back into the register, deliberately. What
  stays ongoing is the data
  ([`ELEMENT_COMPLETION_STUDY.md`](studies/ELEMENT_COMPLETION_STUDY.md)).


---

## 4. Re-verifying the whole thing

**The operating manual is [`ITERATE.md`](ITERATE.md)**, which states the three
gates — the document check after prose, the changed-unit run after code or
Lean, the release once at the close of a round — and which to run when. This
section is the detail behind them.

### 4.1 The short way — run only what has changed

**First, the test runner.** pytest is not installed in this environment by
default and every test file runs under it: `python3 -m pip install pytest`
before any gate that runs tests ([`ITERATE.md`](ITERATE.md) §0). The sign-off
commands check for it and stop with that line if it is missing.

**Start here.** Everything is signed off in `overlay/.glm_signoff.json`: each
test file and each instrument carries the SHA-256 of everything its last
passing result depended on — the file itself, every module it imports
transitively, the frozen data those modules read, the documents and Lean
sources they name, the harness and the interpreter. If that digest holds,
re-running proves nothing; if a byte in the closure differs, the unit is run
again. Nothing is skipped silently.

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.corpus --check            # documents, ~30 s
PYTHONPATH=. python3 -m glm_universal.signoff --verify          # what still holds
PYTHONPATH=. python3 -m glm_universal.signoff --plan            # what would run
PYTHONPATH=. python3 -m glm_universal.signoff --why             # and why each unit would
PYTHONPATH=. python3 -m glm_universal.signoff --impact ../DIGEST.md  # what an edit would cost
PYTHONPATH=. python3 -m glm_universal.signoff --run-everything --jobs 8
PYTHONPATH=. python3 -m glm_universal.signoff --release --jobs 8   # closing a round
PYTHONPATH=. python3 -m glm_universal.signoff --release --resume --jobs 8  # after one was interrupted
```

A release writes each signature as it is earned rather than at the end, so an
interrupted one is resumed rather than restarted: `--release --resume` runs
only the units the release question still calls stale, and
`--verify-release` — which re-checks every signature and reports anything
signed without the exhaustive cases as `partial` — is still what decides the
round.

`--why` splits a unit's closure into five disjoint groups — scaffolding, data,
documents, Lean, code — and names the ones that moved, so a long plan says
which entries are a prose edit and which are not. `--impact PATH` asks the
same relation in the other direction and *before* the edit: 32 of the 123
units reach `PROJECT_DIRECTIVES.md` (120 before Phase 78; see
[`studies/ITERATION_COST_STUDY.md`](studies/ITERATION_COST_STUDY.md) §5g).

The six instruments in the ledger beside the
<!--figure:test-files-->177 test files<!--/figure--> are `lean-build`,
`lean-sorry-free`, `capabilities`, `benchmarks`, `evaluation` and `figures`.
(The seventh, `lean-copies-identical`, went with the second copy of the Lean
tree in Phase 78: the development lives only in `overlay/glm_lean/`.) Editing a document makes exactly the units that
read that document stale — `test_figures.py` yes, `test_substrate.py` no — so
writing up a finding costs one short re-run rather than a quarter of an hour.
A median Lean edit makes **27** units stale and a unit's closure is **129**
files. [`studies/ITERATION_COST_STUDY.md`](studies/ITERATION_COST_STUDY.md)
§5a is the measurement; `glm_universal.corpus.cost.lean_blast_radius`
recomputes it; directive **D16** is the rule.

That selectivity is a property of the tree and not of the rule alone, and a
feature undid it once: the field surface loaded its Lean rows by parsing the
development, on the runtime's own import path, so the whole development
re-entered nearly every closure and a median Lean edit made **79** of 98 units
stale. The rows come from the stored address book now — `lean_address.py`
builds the book, `lean_book.py` answers from it and reads no source — and the
property is pinned by a test rather than by a paragraph
(`test_signoff.py`, `test_corpus.py`). §5e of the same study is the
measurement.

**The documents gate skips a question whose inputs have not moved.** The
verdict of a passing `corpus --check` is stored beside a digest of everything
that check can read — the documents, the rendering code, the data it reads and
the Lean sources its blocks quote. A check over an unchanged tree answers from
that record in about three seconds instead of re-rendering 97 blocks and 201
figures; only a pass is recorded, so a failure is never skipped, and
`--check --all` ignores the record. §5f of the same study.

The same rule now applies to the ledger's own sources. `signoff/rules.py` is
the **rule** — what a closure is, what a digest covers, how a unit is run —
and is in every closure, so editing it costs the whole suite. `signoff/ledger.py`
is the **record** and costs 6 units; `signoff/checks.py` costs 2 and
`signoff/__main__.py` costs 1. §5c of the same study is the measurement.

**A stale derived artefact is reported, never paid for inside a check.** The
expensive derivations — the planner's fallback reading over the evaluation set,
the type-2 class table, the economic lattice points — are kept beside the
digest of the code they came from. `corpus --check` runs with recomputation
forbidden, so a stale one is named together with the command that rebuilds it
rather than silently costing a quarter of an hour; `corpus --refresh` is where
that cost is paid, once.

### 4.2 The long way — run everything from scratch

In order, from the repository root; the last step is the one that catches a
document drifting from the code.

```bash
lake build                                                   # the Lean files, no sorry
rg -n 'sorry|admit' -g '*.lean' overlay/glm_lean             # expect nothing

cd overlay
PYTHONPATH=. GLM_EXHAUSTIVE=1 python3 -m pytest glm_universal/tests -q
PYTHONPATH=. python3 -m glm_universal.capabilities           # 33 probes
PYTHONPATH=. python3 -m glm_universal.benchmarks             # 5 suites
PYTHONPATH=. python3 -m glm_universal.evaluation --jobs 8    # <!--figure:evaluation-cases-->179 CLI cases<!--/figure-->
PYTHONPATH=. python3 -m glm_universal.figures --write        # regenerate FIGURES.md
PYTHONPATH=. python3 -m glm_universal.corpus --refresh       # every derived artefact
PYTHONPATH=. python3 -m glm_universal.corpus --check          # exit 1 on any drift
```

Spot checks that exercise the runtime the way a user does — each returns
`VERIFIED True`, because the Three Column Thinking template regenerates the
answer's figures in a fresh interpreter and compares them with what was
printed:

```bash
cd overlay
PYTHONPATH=. python3 GLM.py -q "report analogies"  --verify-tct
PYTHONPATH=. python3 GLM.py -q "report chemistry coverage" --verify-tct
PYTHONPATH=. python3 GLM.py -q "report lean"       --verify-tct
PYTHONPATH=. python3 GLM.py -q "report escalation" --verify-tct
PYTHONPATH=. python3 -m glm_universal.tools pipeline      # the wiring stages
PYTHONPATH=. python3 -m glm_universal.tools directives    # the standing rules
PYTHONPATH=. python3 -m glm_universal.tools signoff       # the ledger summary
```

---
