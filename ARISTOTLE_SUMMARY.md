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
