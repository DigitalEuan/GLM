# The iteration lane: what a round costs, which CPUs it may use, and what can be done before a close

## Tier 0 — the coarse read

**Question.** A development round of this repository on this workspace cost most of a session in gates rather than in work; which of that cost is real, which was the working method, and what can be done before a full sign-off?

**Verdict.** Two thirds of it was method, not work. The machine offers eight CPUs, the working notes said two and advised `--jobs 2`, and the evaluation's default was four; measured, eight cases run 7.3× faster at `--jobs 8` than at `--jobs 1`, and the whole evaluation takes 248 seconds at eight with the same 237 answers. The round's cheap lane — `corpus --check`, the touched test files, `--only KIND`, `--case` — costs about a minute and can carry most of a round, and the close has one correct order: every code and document edit, then `figures --write`, then `corpus --refresh`, then the two answer censuses last, then `corpus --check`.

**Deciding figure.** 8 usable CPUs, the defaults now following them; 8 cases in 8.9 s at `--jobs 8` against 64.4 s at `--jobs 1`; the evaluation 237 of 237 in 248 s; the cheap lane about 35 s for `corpus --check` and 20 s for a touched test file.

**Recomputed by.** `glm_universal.evaluation.harness.default_jobs`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

*Created 14 November 2026 (Phase 188, pre-registered and measured 14 November 2026 in the same session; the marks were written before the last of them was run and none was restated).*

---

## 0. What this document is

The working method of a round, measured on this workspace, in answer to the
owner's question of 14 November 2026: *can the repository's working method be
improved so it does not take ages and use heaps of resources each iteration,
perhaps by doing a fair amount of the work before full sign-offs, or by taking
only the parts that have to be done?*

It is a study of the **method**, not of the machine: no answer the GLM gives
changes, and the one code path it alters — how many processes the evaluation
runs at once — was already a parameter. What changes is what a round is told to
do.

The measurements were taken in the session that closed
[`CHAT_SURFACE_STUDY.md`](CHAT_SURFACE_STUDY.md) (Phase 187), which is where
the problem showed: the round's own work took minutes and its gates took hours,
and one hour of that was a wrong `--jobs` setting and an order that staled the
two answer censuses twice.

## 1. What the session actually cost

| what | measured | why |
|---|---|---|
| the machine | `os.cpu_count()` 8, `os.sched_getaffinity(0)` 8, `nproc` 8 | `ITERATE.md` §0.5 said *2 vCPU* and advised `--jobs 2`: the note is stale for this runner, and following it wasted a 4× factor |
| the evaluation, 8 cases | 64.4 s at `--jobs 1`, 8.9 s at `--jobs 8` | one CLI process per case, so it parallelises almost linearly up to the number of CPUs |
| the evaluation, all cases | 248 s at `--jobs 8`, 237 of 237 | the full run fits in one tool call, where at two it did not |
| one case | 7.4 s at any `--jobs` | start-up dominates: a case is one fresh `GLM.py` |
| `corpus --check` | about 35 s, `--refresh` about 10 minutes | the refresh recomputes the derived artefacts (`sandbox_planner_report`, `now_receipt_report`) |
| the two answer censuses | about 8 and 15 minutes | each runs the evaluation, its own 237 readings and the replay gate |
| a test file | 2 s to 20 s; 4 minutes for `test_corpus.py` | the suite is not the cost; running all of it is |

Two costs in that table are not method: the censuses re-run the evaluation by
design, because they record what it answered. The rest — 2 vCPU believed where
eight are offered, `--jobs 2` where eight work, a duplicate evaluation started
by hand while another was running, and two extra census cycles from editing
documents after them — was the method, and is what this study fixes.

## 2. The lane

**The defaults.** `evaluation.harness.default_jobs()` answers with the CPUs the
process may run beside (`os.sched_getaffinity`), capped at 8, and the evaluation
and the replay gate both take it when `--jobs` is not given. On this workspace
that is 8 where the command line used to default to 4. The cap is the
repository's: past 8, a case's own interpreter start-up dominates.

**The cheap lane** — what a round does *before* any close, and what a round
should do most of its work behind:

```bash
PYTHONPATH=src python3 -m glm_universal.corpus --check                 # ~35 s
~/glm/venv/bin/python -m pytest src/glm_universal/tests/<touched>.py -q  # seconds
PYTHONPATH=src python3 -m glm_universal.evaluation --only <kind>         # one kind
PYTHONPATH=src python3 -m glm_universal.evaluation --case <id>           # one case
PYTHONPATH=src python3 -m glm_universal.intake check
PYTHONPATH=src python3 -m glm_universal.lean_check
```

None of these signs anything off; together they catch a wrong answer on the
kinds a round touched, a broken document, a stale manifest and a Lean tree
that contradicts its own registry, which is what most rounds break.

**The close, in one order** — the order matters, and every wrong order costs a
census cycle. `ITERATE.md` §2 and §4.2 already carried this order
(`signoff --close` runs it, `signoff.CENSUS_LAST` re-takes the censuses last);
what §0.5 said contradicted them, and a round that followed §0.5 paid for it:

1. every code and document edit of the round, including its study and manifests;
2. `PYTHONPATH=src python3 -m glm_universal.corpus.study_manifest --sync`;
3. `PYTHONPATH=src python3 -m glm_universal.figures --write`;
4. `PYTHONPATH=src python3 -m glm_universal.corpus --refresh` (blocks, address
   books, derived artefacts);
5. **the two answer censuses, last, in order**: `tools evidence-model --write`,
   then `tools evidence-in-use --write`;
6. `PYTHONPATH=src python3 -m glm_universal.corpus --check`.

Why last: both censuses digest `GLM.py`, the document address book and every
stored measurement their answers quote (`QUOTED_MEASUREMENTS_STUDY.md`). Any
document edit moves the address book, and step 4 rewrites it, so a census taken
before step 4 is stale the moment step 4 runs. Step 5 changes no document, so
it does not stale itself.

**The long run.** A background job started inside a tool call does not survive
that call in this workspace. Anything over five minutes runs in the right-side
terminal panel (`PYTHONPATH=src python3 -m glm_universal.evaluation --jobs 8 >
~/glm/x.log 2>&1`) and is polled — which is also how the censuses run here.

**What not to chase.** On the tree this round inherited, four test units fail
before any change is made, and a round should not read them as its own: the
iteration-cost blast-radius rows and `test_the_checks_hold`
(`test_corpus.py`), one row of `FIGURES.md` (`test_figures.py`, the `collected`
figure cannot be recomputed at write time), and the 10 MB bound
(`test_repository_hygiene.py`, two supplied `leechlean` data files are tracked).
They were confirmed on a clean worktree at `HEAD`.

## 3. What is not claimed

The censuses themselves are not made cheaper here: they still run the
evaluation, their own readings and the replay gate, and that is where a close's
half hour goes. Nor is `signoff --close` made affordable in this workspace: its
ledger holds no signature (every unit reports *new*), so a close here would run
all 263 test files and the 7 instruments — about 67 minutes, once. Paying that
one-off is what turns the close into "only what moved", and it is left for a
session that can sit through it. Caching a case's answer against a digest of the code it reads
would cut it, and would be a change to what a measurement means, so it is left
as its own round. The suite as a whole is still not run at a close here; the
sign-off ledger is empty in this workspace (every unit reports *new*), so
`signoff --close` would run all 263 files and was not attempted. The machine
figures are this runner's: another workspace may offer fewer CPUs, and the
lane is written to be measured again rather than believed.

## 4. The surface's other refusal

The round carried the platform plan's P5 a step on as well, because the line it
left was a surface line rather than a reading: a question that parsed to a real
kind and then failed to resolve now gets the same kind of hint as a question
with no declared reading — *no enabled register names it; `:domains` lists the
registers, and the carriers each one holds* — in the interactive surface only.
`test_interactive_names_the_registers_a_refusal_searched` holds both halves:
the hint is there, and the batch line the evaluation pins is not.

## 5. What came out

| Mark | What | Result |
|---|---|---|
| L1 | the default worker count is the machine's usable CPUs, capped at 8 | `default_jobs()` = 8 here (`min(8, affinity)`), where the evaluation's own default was 4 — **met** |
| L2 | parallel speedup measured, and the answers unchanged | 8 cases 64.4 s → 8.9 s (7.3×); the full set 237 of 237 in 248 s at `--jobs 8` — **met** |
| L3 | the cheap lane declared and the close order made consistent, with the reason the censuses come last | `ITERATE.md` §0.5 now carries the lane, the measured CPU count and the censuses-last reason, and no longer contradicts §2 and §4.2, which already carried that order — **met** |
| L4 | the round closes inside the lane | the round's own close ran it: manifests, figures, refresh, both censuses, then `corpus --check` — **met** |

4 of 4 marks.

## In one paragraph

Two thirds of it was method, not work. The machine offers eight CPUs, the working notes said two and advised `--jobs 2`, and the evaluation's default was four; measured, eight cases run 7.3× faster at `--jobs 8` than at `--jobs 1`, and the whole evaluation takes 248 seconds at eight with the same 237 answers. The round's cheap lane — `corpus --check`, the touched test files, `--only KIND`, `--case` — costs about a minute and can carry most of a round, and the close has one correct order: every code and document edit, then `figures --write`, then `corpus --refresh`, then the two answer censuses last, then `corpus --check`.

The figures: 8 usable CPUs, the defaults now following them; 8 cases in 8.9 s at `--jobs 8` against 64.4 s at `--jobs 1`; the evaluation 237 of 237 in 248 s; the cheap lane about 35 s for `corpus --check` and 20 s for a touched test file.
