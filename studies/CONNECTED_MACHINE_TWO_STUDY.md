# The connected machine, second pass — every reasoning module reached, or declared not to be

## Tier 0 — the coarse read

**Question.** Which operations that earlier studies built and measured could no question reach, and can they be put in the answering path without changing any answer the GLM already gives?

**Verdict.** Before this round 24 of the 177 reasoning modules were reached by no query, only by the measurement command line. Six new tools (certified continued fractions, Möbius transforms of continued fractions, role binding, reversible-gate reachability, the proved tag-length floors, and the wiring census itself) and a law-triage fallback in the law register now reach four of them, and a refused English question reaches a tool through eleven declared openings. The other 20 are declared measurement-only, each with its reason, and a test fails if a new module is neither reached nor declared. The stream tools rest on two new Lean theorems. All 8 marks were met, and none of the 404 declared questions changed route.

**Deciding figure.** 8 of 8 marks; 157 of 177 reasoning modules reached from the answering path (153 before), 20 declared; 43 of 43 surds, pi, e and phi agree with independent references; 12 of 12 Möbius transforms agree with the integer recurrence; 0 of 404 declared texts match an opening; 20 of 20 phrased questions and 21 of 21 tool questions as declared; the gate certificate equals search on 48 of 48 pairs.

**Recomputed by.** `glm_universal.evaluation.connected_two_cases.measure`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. What this document is

The study of Phase 136. The owner's instruction for the run was to "pull
things together a bit tighter": there were experiments that had been run and
measured but never wired in, so the GLM could not use what they built. This
round finds them mechanically, wires in the ones that carry an operation a
caller can ask for, and makes the rest a declared, tested list rather than
an accident.

**Order of work, stated plainly.** The census of §1 was taken first. Then
`RequestProject/GLM/CertifiedStreams.lean` was written and built, with every
proof complete. The tools of §2 were then written and tried by hand. The
batteries and marks of §§3–4
(`glm_universal/evaluation/connected_two_cases.py`) were written after that
and before `measure()` was first run. So the marks are not a blind
pre-registration. They were fixed before the measurement that grades them,
but by someone who had already seen the tools answer by hand.

## 1. The census: what no question reached

`studies/scripts/wiring_audit.py` (Phase 66) takes the import closure from
*every* entry package, including the measurement command line `tools.py`,
the corpus and the sign-off. By that reading all 177 reasoning modules are
reached, but "reached" there includes "reached by the command that measures
it". The narrower question is which modules a **query** can reach: the
closure from `glm_universal.runtime`, the answering path (router, toolbox,
parser, session, reports).

Taken at the start of the round: **153 of 177** reached, **24** not. Of the
24, 13 are imported only by `tools.py` or the corpus layer, and the other 11
also by one another.

| group | modules | what they hold |
|---|---|---|
| GLM-BAT batteries | `affine_output`, `constant_bound`, `counter_lasso`, `inert_counter`, `operations` | batteries and marks; the rules live in `batch_machine`, which `tool machine` reaches |
| ladder and deep holes | `cell_guard`, `placement_guard`, `norm256_hex`, `probe_budget`, `stray_blind` | guards and censuses over a ladder no query reads yet (`STATUS.md` §2.1, items 1–2) |
| corpus measurements | `citation_scope`, `document_tree`, `corpus_resample`, `native_parity`, `native_words` | measurements of the repository's own text; the last two are the measuring halves of existing tools |
| audits | `now_receipt`, `now_float_control`, `operation_escalation`, `second_reading`, `typed_plans` | audits of a supplied study and of the answering path itself |
| **operations** | `substrate_cognition`, `role_binding`, `shortest_tag`, `law_triage` | certified continued fractions and Gosper's transform, reversible-gate reachability; typed role binding; the proved tag floors; the fates of the 106 triaged laws |

The last row is the one this round wires in. Each of the others has a reason
it is not a tool, and that reason is now written down beside it
(`toolbox.MEASUREMENT_ONLY`).

## 2. What was built

**Tools** (`runtime/toolbox.py`, `tool <name> [argument]`):

* `tool continued fraction X [terms N]` (derive). Certified terms of a
  written real (`sqrt(n)`, `pi`, `e`, `phi` and arithmetic over them). A term
  is emitted only when both ends of the interval `x.at(k) ± 2⁻ᵏ` agree on it.
  The precision doubles up to `2⁻⁴⁰⁹⁶` and then stops. A written rational is
  expanded exactly. A rational written as an expression (`sqrt(4)`) has an
  expansion that ends, and the interval can never certify a term past its
  last one, so the tool emits the certified prefix and refuses the rest. The
  old `cf_terms` would loop forever on such a value; the new
  `substrate_cognition.cf_certified` is the capped version.
* `tool mobius a b c d of X [terms N]` (derive). The continued fraction of
  `(aX + b)/(cX + d)`, streamed from the certified terms of `X` by Gosper's
  rule (`substrate_cognition.mobius_stream`) and cross-checked against the
  direct expansion of the composed real. It refuses when `ad − bc = 0` or the
  denominator vanishes.
* `tool bind ROLE A B in DOMAIN` (address, refusal). The typed relation as one
  24-bit word (`role_binding.bind_names`), and the filler read back from it.
  The read-back is refused by name (`ambiguous-recovery`, `unknown-role`,
  `unknown-name`) where the register cannot name a single carrier.
* `tool gates SOURCE to TARGET` (derive, refusal). The least number of
  Toffoli/Fredkin moves between two 24-bit words, or the block that makes the
  target unreachable, with the theorem that says why.
* `tool tag length D` (derive). The proved floors of Phase 135: at least
  `D + 6` bits for any parity tag, and 7, 11 and 15 bits for tags built on
  seven bits.
* `tool wiring [module]` (address). The census of §1, computed when asked:
  which modules a query reaches, and the declared reason for each one it
  does not.
* `tool law register LAW_…`, for a law outside the 65 retained ones, now
  answers with the fate the law triage gave it (`law_triage.fate_of`) instead
  of refusing. Before this round that fate was a record no question reached.

**English openings** (`toolbox.TOOL_PHRASES`, `router._phrased_tool`). These
are eleven declared full-match patterns, such as "what is the continued
fraction of X", "how many tag bits are needed for distance D", "can W reach
V by reversible gates" and "what happened to LAW_…". Each stands for one
`tool …` text. The router consults them only after the planner, the grammar
and the stepwise planner have all refused, and keeps the tool's verdict only
if it answers. So no answer is changed and no refusal is swapped for another
refusal. The command line (`GLM.py --ask`, `-q`) prints such a verdict as
`SURFACE toolbox (phrased, after the planner refused)`.

**The guard against drift** (`toolbox.wiring_census`,
`tests/test_connected_two.py`). The census is taken from source on each run.
A reasoning module that is neither reached nor declared fails the test, and
so does a declaration whose module has since been wired in.

## 3. What is proved (`RequestProject/GLM/CertifiedStreams.lean`)

* `cfPrefix n x` is the first `n` continued-fraction terms of a real (`⌊x⌋`,
  then the expansion of `1 / fract x`).
* `step_between` and `fract_pos_of_prefix` are the step lemmas: equal floors
  put the three values in one unit cell, and their remainders come back in
  reverse order.
* `cfPrefix_between` says a value strictly between two reals that share `n`
  terms shares them too, whichever order the two ends are in.
  `cfPrefix_certified` is the closed-interval form, which is what the tool
  has, so **every term `tool continued fraction` emits is a term of the
  value**.
* `mobius_between_pos` and `mobius_between`: for a tail `t ≥ 1`, with `c` and
  `c + d` of one sign, `(at + b)/(ct + d)` lies between `(a + b)/(c + d)`
  and `a/c`. It is a weighted average of the two, with weights `c(t − 1)` and
  `c + d`.
* `gosper_emit_sound`: if `⌊a/c⌋ = ⌊(a + b)/(c + d)⌋ = q`, every tail gives
  floor `q`. So **every term `tool mobius` emits is a term of the transformed
  value**, whatever the unread input.
* `sqrt2_interval_prefix` is a worked instance: `[1.4142, 1.4143]` already
  decides the terms `1, 2, 2` of `√2`.

The file builds with no `sorry`. Its theorems use only `propext`,
`Classical.choice` and `Quot.sound`.

## 4. The marks

| mark | what is measured | pass |
|---|---|---|
| W1 | the wiring census | 0 undeclared modules, 0 stale declarations |
| W2 | the Lean file | present, every theorem of §3 named, no `sorry` |
| W3 | `cf_certified` against independent references | the integer recurrence for `sqrt(n)` at every non-square `n ≤ 50` (20 terms), the published terms of pi (20, OEIS A001203), the pattern of e (30), phi (30): all agree |
| W4 | `tool mobius` on 12 transforms of square roots | agrees with the continued fraction of the quadratic irrational `(P + √D)/Q` by the integer recurrence (20 terms), and the direct expansion agrees |
| W5 | six rationals written as expressions | every emitted term is a term of the value, and none is reported complete |
| W6 | non-interference | none of the 404 declared texts (the 188 contract cases, 63 engineering, 33 cognition, 109 Python and the 11 routed mixed texts) matches an opening |
| W7 | 20 phrased questions through the router | 14 answered by the declared tool with the declared fragment, 6 left refused as declared |
| W8 | 21 tool questions; the gate certificate | every tool question as declared; on 48 pairs one to three random moves apart, the certificate equals breadth-first search over all 16 moves on the whole word |

**Controls.** W3 and W4 use references that share no code with the tools:
the integer recurrence uses no exact-real layer and no interval. W5 is the
case the certification exists for. W6 is the non-interference rule of
`ConnectedMachine.lean` (`route_cons_none`) taken as a count. The six
refusals in W7 include an opening the tool refuses (`continued fraction of
banana`, an ambiguous binding, a law in neither register), so the fallback
is seen to keep a refusal rather than invent an answer.

## 5. What this round does not do

* It does not put the ladder guards in the answering path
  (`STATUS.md` §2.1, items 1–2). They wait on a query kind that reads a
  ladder carrier, and that work is still to do; it is declared beside the
  modules.
* The openings are patterns, not a parser. A rewording outside the eleven
  patterns is not read, just as with the meta and explanation frames.
* `now_receipt.capture_now` takes a 24-coordinate composition that no
  question supplies, so it is declared measurement-only rather than given a
  tool with an awkward argument.
* No evaluation case was added. The contract set is pinned by the router's
  census (`test_connected_machine`), and the new questions live in their own
  batteries.

## 6. Files

* `glm_lean/RequestProject/GLM/CertifiedStreams.lean`, the proofs.
* `glm_universal/runtime/toolbox.py`: the six tools, the law-triage
  fallback, `TOOL_PHRASES`, `MEASUREMENT_ONLY`, `wiring_census`.
* `glm_universal/runtime/router.py` (`_phrased_tool`) and
  `GLM.py` (`_print_phrased`), the refusal-only fallback.
* `glm_universal/reasoning/substrate_cognition.py`
  (`cf_certified`).
* `glm_universal/evaluation/connected_two_cases.py`, the batteries
  and `measure()`. `python3 -m glm_universal.tools connected-two` prints the
  marks.
* `glm_universal/tests/test_connected_two.py`.

## 7. The measurement

`python3 -m glm_universal.tools connected-two`, at the close of the round:

```
W1 wiring         157 of 177 reasoning modules reached, 20 declared, undeclared [], stale []
W2 Lean           RequestProject/GLM/CertifiedStreams.lean: missing [], sorry False
W3 cf             43 of 43 surds agree; pi True, e True, phi True
W4 mobius         12 of 12 agree with the quadratic recurrence, 12 with the direct expansion
W5 rational       sqrt(4): 0 term(s) emitted, sound True, complete False
W5 rational       sqrt(9)/2: 1 term(s) emitted, sound True, complete False
W5 rational       sqrt(2)*sqrt(2): 0 term(s) emitted, sound True, complete False
W5 rational       sqrt(49/4): 1 term(s) emitted, sound True, complete False
W5 rational       (sqrt(2)+1)*(sqrt(2)-1): 0 term(s) emitted, sound True, complete False
W5 rational       sqrt(16)/5: 2 term(s) emitted, sound True, complete False
W6 interference   0 of 404 declared texts match an opening
W7 phrased        20 of 20 as declared (14 answered)
W8 tools          21 of 21 as declared; gate certificate equals search on 48 of 48
marks met         8 of 8
```

### 7.1 The verdict

All 8 marks were met. Four of the 24 unreached modules (`substrate_cognition`,
`role_binding`, `shortest_tag`, `law_triage`) now answer questions, through
the stream, binding, gate, tag-length and wiring tools and the law register,
so 157 of 177 reasoning modules are reached from the answering path, up from
153. The other 20 are declared, each with its reason.
The end-to-end evaluation still passes 188 of 188 (156 answered, 32 refused
as `boundary`), and no declared question changed route.

### 7.2 What it answers

The GLM can now be asked for a continued fraction of an irrational, a
homographic transform of one, a typed binding and its read-back, a
reversible-gate distance, a tag length, the fate of a triaged law, and its
own wiring. Each answer is recomputed when asked, and the two stream answers
rest on proved emission rules. Under directive D15 the round moves
**derivation**, since a continued-fraction term, a transformed expansion and
a gate distance are answers no register holds, computed and certified. It
also moves **refusal**: a rational written as an expression gets the
certified prefix and a refusal for the rest, where the old routine would
never have returned. The openings move neither by themselves. They are
**addressing** of a question to the tool that can answer it, which is the
reach the round set out to add.

### 7.3 What this round leaves

* The placement guard and the budget rule (`STATUS.md` §2.1, items 1–2) are
  still not in the answering path. The census now names them as the two
  ladder modules waiting on a carrier-address query kind.
* The openings are eleven patterns. Recognising rewordings, as for the meta
  and explanation frames, is still open.
* Multi-step use: a tool's answer is not yet handed to the planner as a
  value. Phrasings such as "the third term of the continued fraction of pi
  times two" are refused.
