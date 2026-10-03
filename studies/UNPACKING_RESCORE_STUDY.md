# Argument unpacking and the third view on demand: Phase 96's two misses, re-declared and re-scored

## Tier 0 — the coarse read

**Question.** Phase 96 missed two of its nine marks, V8 and V4. Can the dialect be given argument unpacking so that the refused program is answered, and can the framed register's results be improved: a correct declaration for independent faults in place of V4's false analogy, and fewer view reads for the same answers?

**Verdict.** Yes, on every mark: the dialect now admits argument unpacking, and the refused program answers equal to CPython as a fresh declared case. Reading the third view only on demand gives the three-view answer on every read inside the fault model while reading a third fewer views. Re-declared correctly, independent faults are resolved by three views with 0 wrong, and two views cannot be helped by any frame, which is proved. All twelve declared marks were met.

**Deciding figure.** 12 of 12 marks met; 33 of 33 declared programs and refusals as declared (0 before); 680,064 of 680,064 on-demand reads equal to three views with 1,371,264 views read instead of 2,040,192; 84,480 of 84,480 independent three-view reads resolved, 0 wrong; 346 open second errors for every first error and every frame.

**Recomputed by.** `glm_universal.runtime.unpacking_report.unpacking_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

[`SECOND_VIEW_STUDY.md`](SECOND_VIEW_STUDY.md) (Phase 96, round 8 of the
order of work in [`STATUS.md`](../STATUS.md) §3.4) closed with 7 of 9 marks
met and no wrong answer from any certified stage. The owner asked whether
that round's results could be improved, and named the first repair: the
dialect refuses any call that uses argument unpacking, so the declared program
`read_views(*store_views(golay_encode(1234)))` was refused, and mark V8 was
missed for a reason that had nothing to do with the register.

Reading the two misses again:

* **V8 was a gap in the dialect.** Argument unpacking was refused
  `UNSUPPORTED` at every call (`keyword or starred arguments`) and every
  definition (`only plain positional parameters`). The repair is to add it,
  and re-score the refused program as a fresh declared case.
* **V4 was a declaration on a false analogy.** It expected the two-view
  register under independent faults to reproduce X1's 4,224 of 4,224. But the
  register's second view reads its error *rotated*, and under independent
  faults a rotation is only a relabelling of the second error: it cannot
  make two views better or worse on average. X1's figure was a property of
  its twelve errors, not of two views. The repair is a correct declaration:
  predict the live count of every read, measure three views as well as two,
  and prove what the frame can and cannot do.

The round also asks whether the register can be made cheaper without changing
an answer: three views are read on every read, but two views already resolve
10,452 of every 10,626 common-mode bursts.

## 1. The objects

**Argument unpacking in the dialect.** At a call, every argument written
`*value` is iterated as a `for` loop iterates it and its items are spliced in
place, left to right; the step is named in column 1 ("Unpack … into 3
positional arguments") and re-checked in column 3. At a definition, one
parameter written `*rest` after the positional parameters collects the
arguments past them into a tuple, again a named step. Everything CPython does
here the dialect does: a value that is not iterable is CPython's `TypeError`,
too few arguments for the positional parameters is `TypeError`. What stays
outside is named: keyword arguments and `**` unpacking, keyword-only
parameters, defaults, starred items in a list display (`UNSUPPORTED`); a set
unpacked (`ORDER_UNDEFINED`, since CPython promises no order); a `*rest`
wider than one carrier (`CARRIER_OVERFLOW`).

**The third view on demand.** `read_on_demand` reads views 0 and 1, and reads
view 3 only while the fork is still open. Inside the fault model the carrier
is in every view's fork, so once two views leave only the carrier a third
view can only keep it (`OnDemandView.on_demand_agrees`). Outside the fault
model a third view could refuse what two views answered, so the saving has a
price there, which R3 measures.

**Independent faults.** Each view carries its own weight-4 error. Through
view `k` the error `f` is read as `rot(f, k)`. Two views leave a read open
exactly when an octad contains `e ∪ rot(f, k)`, and since the map
`f ↦ rot(f, k)` is a bijection on the four-sets, the number of open second
errors does not depend on the frame.

## 2. Declarations — written before any code of the round

`evaluation/unpacking_cases.py` and the frozen baseline
`reasoning/_data/unpacking_baseline.json` were committed before the dialect
or the register was changed. The baseline holds the outcome of 311 earlier
declared dialect programs (Phases 64, 83, 84, 89, 94, 95 and 96), the
differential battery's counts, and this round's 33 programs as the old
dialect answered them (all 33 refused `UNSUPPORTED`). Nothing is random
(D7): every probe is a fixed stride or a full census.

**U1 — the refused program, re-scored.**
`read_views(*store_views(golay_encode(1234)))` is answered equal to CPython
with the prelude, in type and value; its column-3 script verifies in a fresh
`python3 -I`; a mutated script is rejected; and Phase 96's V8 (6 programs, 3
refusals) is met as declared.

**U2 — unpacking at a call.** 14 programs (user functions, builtins, a
string method, the register's builtins; tuples, lists, ranges, strings and
dicts unpacked; two stars in one call; a star between positional arguments)
are answered equal to CPython, scripts verified, mutants rejected.

**U3 — `*rest` at a definition.** 8 programs (alone and after positional
parameters, with a loop, with recursion through `mx(*rest)`, with fractions,
wrapping `read_views`) likewise.

**U4 — the refusals.** 10 programs refused by their declared names:
`max(*5)`, too many arguments after unpacking, too few for a `*rest`
definition (`PYTHON_ERROR`); `**kw`, a keyword-only parameter, `f(**d)`,
`[*range(3)]`, a default (`UNSUPPORTED`); a set unpacked
(`ORDER_UNDEFINED`); a `*rest` of 30 (`CARRIER_OVERFLOW`).

**U5 — no regression.** None of the 311 earlier programs changes its value
or its refusal name, and the differential battery's counts are unchanged.
(Phase 96's `views-clean` is the very source U1 re-scores, so it moves by
U1's declaration; the report lists it as the one declared move.)

**R1 — on demand, common-mode bursts.** On Phase 96's probe (64 codewords,
all 10,626 four-error bursts) the on-demand register gives the three-view
answer on every read, 0 wrong, and reads the third view on exactly
174 × 64 = 11,136 reads — the open bursts of two views.

**R2 — inside the packing radius.** On every burst of weight at most 3 the
answer is right and the third view is never read.

**R3 — the price outside the fault model.** On weight-5 common-mode bursts
the on-demand register gives the two-view register's verdict on every read,
so it answers wrongly exactly where two views did: 384 of 2,720,256, where
three views refuse all of them.

**R4 — independent faults, two views, fresh probe.** The codewords at
indices `32 + 64 i` (64 of them; X1's began at 0) and twelve fresh errors at
indices `5 + 883 j` of the lexicographic four-sets; every ordered pair of
distinct errors: the live count equals `1 + |octads ⊇ e ∪ rot(f, 1)|` on
every read, the truth always live, 0 wrong.

**R5 — independent faults, three views.** Every ordered triple of distinct
fresh errors: the live count equals `1 + |octads ⊇ e ∪ rot(f, 1) ∪ rot(g, 3)|`,
0 wrong.

**R6 — independent faults, on demand.** On every read of R5 the on-demand
register gives the three-view answer, and reads the third view exactly when
two views leave the read open.

**R7 — the frame cannot help two views.** For the 24 first errors at indices
`442 j` and every single second frame `k = 1, …, 23`, exactly 346 of the
10,626 second errors leave two views open. Lean states it for every first
error and every permutation.

**The scoping figures, reported as such.** Before the declaration, an
inclusion–exclusion over the size of the union gave the census over all
errors: two views leave 3,676,596 of 112,911,876 ordered pairs open
(3.26 %), whatever the frame; three views leave 260,294,496 of
1,199,801,594,376 ordered triples open (0.0217 %). They are recorded under
`SCOPED`, computed and not proved, and are not results of the round.

**What would count as moving the target (D15).** U1–U3 move **derivation**:
33 programs the dialect refused are answered, each re-derived in a fresh
interpreter. U4 keeps **refusal** where it belongs. R1, R2 and R6 move no
answer — they move the cost of an answer, and they say so. R3 is a measured
loss of **refusal** that the on-demand read would cost outside the fault
model. R4, R5 and R7 sharpen **refusal**: the open reads of two views are
predicted exactly and shown to be no frame's fault.

## 3. What was built

* **The dialect** (`reasoning/python_speech.py`): `Evaluator.call_args`
  splices every `*value` in place at a call, through the same iteration a
  `for` loop uses, with a named step and a column-3 check; `_Function` gains a
  `rest` parameter; `call_function` binds the arguments past the positional
  parameters into a tuple, refused `CARRIER_OVERFLOW` past one carrier. The
  refusal for keywords is now named `keyword arguments (and ** unpacking)`.
  The imperative grammar of Phase 95 (`say:` on programs) still refuses
  starred arguments; only the dialect was widened.
* **The register** (`reasoning/second_view.py`): `read_on_demand` and
  `FramedRegister.read_on_demand`, returning the fork and the number of views
  read; the marks R1–R7 (`on_demand_report`).
* **`runtime/unpacking_report.py`** — U1–U5, the frozen baseline and the
  before column; `python3 -m glm_universal.tools unpacking` prints every mark
  (`--json`, `--quick`, `--no-scripts`); `tests/test_unpacking.py` holds the
  facts at the sampled scale.
* **`RequestProject/GLM/OnDemandView.lean`** — §5.

## 4. Results

Every figure is recomputed by `python3 -m glm_universal.tools unpacking`.
**All twelve declared marks were met.** No certified stage gave a wrong
answer anywhere. So the answer to the round's question is yes: the dialect
admits argument unpacking and answers the program Phase 96 refused; the
on-demand read gives the three-view answer for a third fewer view reads;
and independent faults, declared correctly this time, are resolved by three
views with 0 wrong, while two views cannot be helped by any frame.

| mark | declared | measured | |
|---|---|---|---|
| U1 | the refused program equal to CPython, verified, mutant rejected; Phase 96's V8 as declared | answered `333010` = CPython, script verified, mutant rejected; V8 6 of 6 programs and 3 of 3 refusals | met |
| U2 | 14 call programs | 14 of 14 | met |
| U3 | 8 definition programs | 8 of 8 | met |
| U4 | 10 refusals by name | 10 of 10 | met |
| U5 | 311 earlier programs and the battery unchanged | 0 moved (1 declared move, U1's own source); battery 2,830 answered, 0 wrong, every count unchanged | met |
| R1 | on demand = three views, third view on 11,136 | 680,064 of 680,064 equal, 0 wrong; third view on 11,136 | met |
| R2 | weight ≤ 3 right, third view never | 148,800 of 148,800 right; third view on 0 | met |
| R3 | weight 5: the two-view verdict, 384 wrong | 2,720,256 of 2,720,256 equal to two views; 384 wrong, 2,719,872 contradicted | met |
| R4 | live count predicted, 0 wrong | 8,448 reads, 0 off the prediction, 0 wrong; 8,192 resolved, 256 open | met |
| R5 | live count predicted, 0 wrong | 84,480 reads, 0 off, 0 wrong; 84,480 resolved | met |
| R6 | on demand = three views; third view exactly when open | 84,480 of 84,480 equal; third view on 2,560, each where two views were open | met |
| R7 | 346 for every first error and frame | 24 first errors × 23 frames, every count 346 | met |

### 4.1 Argument unpacking (U1–U5)

Before the round the dialect answered **0 of the 33** declared programs;
after it, all 22 programs are answered equal to CPython in type and value,
every column-3 script verifies in a fresh interpreter and every mutated
script is rejected, and all 11 refusals (U1's three from Phase 96 and U4's
ten) come out by their declared names. The program Phase 96 refused is
answered `333010`, the codeword `golay_encode(1234)` read back through all
three of its views. A recursive maximum written `mx(a, *rest)` and called as
`mx(*rest)` shows both halves of the construct in one column 1: *pack the 3
arguments past the 1 positional parameter of mx into the tuple rest … unpack
(9, 2, 7) in place into 3 positional arguments*.

None of the 311 earlier declared programs moved, apart from the one U1
declared: Phase 96's `views-clean`, which is the very source U1 re-scores.
The differential battery of 7,128 operator cases is unchanged (2,830
answered, 0 wrong).

### 4.2 The third view on demand (R1–R3)

Inside the fault model the on-demand register is the three-view register,
read for less: on Phase 96's full common-mode probe it gives the same answer
on all 680,064 reads and reads **1,371,264** views instead of **2,040,192**
— 2.016 views a read, a third fewer — because the third view is read only on
the 174 bursts per codeword that two views leave open. Inside the packing
radius it never reads the third view.

**The price, measured.** On weight-5 bursts, outside the declared fault
model, the on-demand register stops wherever two views stop, and gives the
two-view register's 384 wrong answers among 2,720,256 reads, where the
always-three register refused all of them. So the on-demand read is the
right default only where the fault model is trusted: it changes no answer
inside it, and it gives back part of Phase 96's weight-5 refusal outside it.
The register keeps both reads, `read` (every view) and `read_on_demand`, and
the choice is the caller's.

### 4.3 Independent faults, re-declared (R4–R7)

On a fresh probe (64 codewords, 12 fresh errors), the two-view register's
live count matched the octad prediction on all 8,448 reads, with the truth
always live and 0 wrong; 256 reads (4 of the 132 error pairs on every
codeword) stay open. Three views resolve **84,480 of 84,480** reads, 0 wrong,
and the on-demand register gives the same answers while reading the third
view on 2,560 reads, each one a read two views left open. This is what V4
should have declared: three views, not two, are what the register needs under
independent faults, as Phase 96's post-hoc 14,080 of 14,080 suggested.

And no frame could have rescued two views. R7 counts, for each of 24 first
errors and each of the 23 rotations, the second errors that leave two views
open: 346 every time, the figure `OnDemandView.open_seconds_card_frame`
proves for every first error and every permutation. The five octads through a
four-set hold 70 four-sets each and any two share only the four-set itself, so
5 × 69 + 1 = 346: about one second error in 31 leaves two views open, whatever
the frame. X1's 4,224 of 4,224 was a property of its twelve errors.

## 5. What is proved rather than measured

`RequestProject/GLM/OnDemandView.lean` builds with no `sorry`. The theorems
about the Golay code inherit `Lean.ofReduceBool` from the Golay development
(`Golay/Sextet.lean`'s `native_decide`); the unpacking theorems use only the
standard axioms.

* `inter_eq_of_resolved`, `through_eq_empty_mono`, `on_demand_agrees` — once
  two views resolve a read, a third view cannot change the answer.
* `inside_radius_unique` — below weight 4 one view already leaves only the
  carrier, so the third view is never needed.
* `through_union_nonempty_iff`, `inter_eq_of_through`, `openSeconds_eq`,
  `open_seconds_card` — for a first error of weight four exactly 346 second
  errors leave two views open.
* `open_seconds_card_frame` — the same 346 for every permutation applied to
  the second view: the frame cannot help two views under independent faults.
* `independent_never_separated` — for every frame and every first error some
  second error leaves five octads open.
* `flatten_append`, `flatten_length`, `flatten_pos` — a call's arguments with
  every `*xs` spliced in place, as `Evaluator.call_args` builds them.
* `bind_isSome_iff`, `bind_rest`, `star_round_trip` — which argument lists a
  definition with `k` positional parameters (and possibly `*rest`) accepts,
  what `rest` holds, and `def f(*r)` called as `f(*xs)` binds `r` to `xs`.

## 6. Limits, and what the round leaves

* **Keywords stay outside.** Keyword arguments, `**` unpacking, keyword-only
  parameters and defaults are still refused by name; a dialect with keywords
  would need a declared order for keyword binding and is not taken here.
* **Starred displays and starred assignment** (`[*xs]`, `a, *b = xs`) stay
  outside; they are iterable unpacking rather than argument unpacking.
* **The imperative grammar** (`say:` on a program) still refuses starred
  arguments; only the dialect was widened.
* **The on-demand read is not the default.** It is cheaper and equal inside
  the fault model, and R3 measures what it gives back outside it; which read
  a register uses remains the caller's choice, as framing a register by
  default remains the owner's (Phase 96 §6).
* **The scoping census over all errors** (3.26 % open for two views, 0.0217 %
  for three) is computed by inclusion–exclusion and not proved; the
  per-first-error count 346, which implies the two-view figure, is proved.

## 7. Re-running it

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.tools unpacking            # every mark, a few minutes
PYTHONPATH=. python3 -m glm_universal.tools unpacking --quick    # one probe codeword
PYTHONPATH=. python3 -m pytest glm_universal/tests/test_unpacking.py -q
lake build RequestProject.GLM.OnDemandView                        # from the repository root
```
