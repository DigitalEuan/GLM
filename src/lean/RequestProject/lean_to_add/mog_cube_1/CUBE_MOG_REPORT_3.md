# Report 3 — connecting words, conversation, Zipf, and plans

This report continues `CUBE_MOG_REPORT.md` and `CUBE_MOG_REPORT_2.md`.  Report 2
ended with a system that could say true single sentences about a measurable
micro-world and answer single questions without lying.  The obvious complaint
about it was that nothing *connected*: every sentence stood alone, and the only
joining word was "and".

This round adds the joining words, a conversation that remembers, a check of the
resulting language against Zipf's law, and the ability to say what to **do**.

Everything below is machine-checked in Lean.  Every count is computed inside the
proof, not typed in by hand, and every claim that failed is written down as it
failed.  A dependency-free Python mirror, `glm_discourse.py`, reproduces every
number and every sentence in this report; run it with `python3 glm_discourse.py`.

---

## 1. `and`, `but`, `so` — connectives with measured meanings
(`RequestProject/Discourse.lean`)

The system keeps a list of what it has already said.  The worlds still
compatible with all of it are the **live worlds**.  A next clause `q` is judged
against them, and that judgement chooses the word:

| word | condition on the live worlds | what it means |
|------|------------------------------|---------------|
| `so q`  | `q` holds in **all** of them | a deduction: the paragraph is already committed to it |
| `and q` | `q` holds in **at least half**, but not all | news, and unsurprising |
| `but q` | `q` holds in **fewer than half** | news the hearer would not have expected |

`but` is the first thing in this project that is not strict logic: it is a
defeasible expectation.  It is still perfectly deterministic — it is a count
over the 512 worlds, not an opinion — which is what lets it be proved about.

Proved (not sampled):

* `para_sound` — every clause of a paragraph is true in the world it describes;
* `so_is_a_deduction` — after "so", every live world satisfies the clause;
* `but_is_contrastive` — after "but", strictly fewer than half do, and the
  clause is still news;
* `and_is_informative` — after "and", some live world fails the clause, so it
  rules something out;
* `para_no_repetition` — a paragraph never says the same thing twice;
* `para_topic_continuity` — every clause has the same subject, which is what
  makes the pronoun "it" unambiguous;
* `para_information_increases` — each `and`/`but` clause strictly shrinks the
  set of live worlds.

The generator was then run **over every one of the 512 worlds for each of the
three things — 1536 paragraphs — and every one of them was checked to be a valid
paragraph** (`corpus_facts`).  Of the 9216 clauses it joins, 4824 are `and`,
1512 `but`, 2880 `so`.

Three real examples (the demo world: water −10 °C 1 kg, stone 20 °C 10 kg,
lamp 100 °C 1 kg):

> the water is frozen, and it is not heavy, and it is not hotter than the stone,
> and it is not hotter than the lamp, so it is not boiling, so it is not warm,
> so it is not heavier than the stone.

> the stone is not frozen, but it is not hotter than the lamp, but it is heavier
> than the water, and it is not boiling, and it is hotter than the water, and it
> is heavier than the lamp, so it is warm.

> the lamp is not frozen, and it is boiling, and it is not heavy, and it is
> hotter than the water, and it is hotter than the stone, so it is not warm,
> so it is not heavier than the water.

Read the second one carefully: the "but"s are earned.  Most worlds in which
something is not frozen have it hotter than the lamp, so "but it is not hotter
than the lamp" is a genuine reversal of expectation; and the closing "so it is
warm" is a deduction — once you know it is not frozen and not boiling, warm
follows in every world.

**Honest limit.** Every paragraph is exactly seven clauses long because the
generator's fuel runs out, not because the system runs out of things to say.

### 1b. Paragraphs that change the subject
(`RequestProject/WideDiscourse.lean`)

Keeping one topic is what makes "it" safe, but it also blocks the most
interesting inferences in this world, because they join facts about *different*
things.  Lifting the restriction — judging each clause by the same test applied
to its own subject — gives, in the demo world:

> the water is frozen, but the lamp is boiling, but the stone is warm, but it is
> heavier than the water, and the lamp is not heavy, so the stone is not frozen,
> so the lamp is not frozen.

The pronoun is used exactly once, and only where it is safe: right after the
stone has been named.  Everywhere else the thing is named again.

Because the licensing test is literally the one-topic test applied to each
clause's own subject (`wstepOK ctx s = Discourse.stepOK ctx (subj s.lit.1) s`),
every guarantee transfers: soundness, no repetition, `so` as deduction, `but` as
contrast, and strictly increasing information.  Measured over all 512 worlds
(`wcorpus_facts`): 512 valid paragraphs, 3072 joined clauses, **2524 of them
changing the subject, of which 330 are `so` clauses** — cross-subject deductions
that the one-topic system could not state at all.

---

## 2. A conversation that remembers
(`RequestProject/Dialogue.lean`)

A paragraph is a monologue.  The dialogue layer carries a state — the current
topic (what "it" refers to) and everything asserted so far — and answers
"tell me about …", "tell me more", "is it warm?", "why is it warm?", "is it
hotter than …?".

A real transcript in the demo world:

```
> tell me about the water       the water is frozen
> tell me more                  and it is not heavy
> tell me more                  and it is not hotter than the stone
> is it warm?                   the water is not warm
> why is it warm?               as I said, the water is not warm because the water is frozen
> tell me about the stone       the stone is not frozen
> tell me more                  but it is not hotter than the lamp
> tell me more                  but it is heavier than the lamp
> is it hotter than the water?  the stone is hotter than the water
> tell me more                  and it is not boiling
```

Note the fourth line: the question contained a false premise and the answer
contradicted it instead of going along with it.  Note the seventh: the topic
moved to the stone and "it" moved with it.

Proved:

* `reply_true` — the reply is true in the world, for **every** state, **every**
  utterance and **every** world;
* `reply_fresh` — "tell me more" never repeats itself, and the connective it
  uses is licensed by everything said so far;
* `reply_on_topic`, `topic_only_changes_when_asked` — "it" never drifts;
* `run_no_contradiction` — the conversation can never assert something it has
  already denied;
* `again_iff_already_said` — a yes/no answer is marked "as I said" exactly when
  the fact it states is already one of the conversation's commitments, which is
  where the "as I said" in the transcript above comes from;
* `script_facts` — the ten-turn script above was run in **all 512 worlds**:
  every reply true in every one of them, and at least eight distinct
  commitments held at the end.

**Honest limits.** A *question* can make the system restate a fact it already
volunteered ("is it warm?" after it has said it is not warm), so the commitment
list is not duplicate-free; the proof states the true thing (no contradictions,
at least eight distinct commitments) instead of the false one (no repeats).
When the system has nothing new to say about the topic it falls back to a bare
fact rather than inventing one.

---

## 3. Zipf's law, tested honestly
(`RequestProject/Zipf.lean`)

Zipf's law says the `n`-th commonest word appears about `f₁/n` times, and Zipf
explained it by a principle of least effort.  Both halves were tested.

**The test.**  The 1536 paragraphs above are 66288 word tokens over 17 types.
Ranked:

| rank | word | observed | Zipf `f₁/n` | ratio |
|-----:|------|---------:|------------:|------:|
| 1 | is | 10752 | 10752 | 1.00 |
| 2 | it | 9216 | 5376 | 1.71 |
| 3 | not | 7152 | 3584 | 2.00 |
| 4 | the | 6912 | 2688 | 2.57 |
| 5 | than | 5376 | 2150 | 2.50 |
| 6 | and | 4824 | 1792 | 2.69 |
| 7 | hotter | 3072 | 1536 | 2.00 |
| 8 | so | 2880 | 1344 | 2.14 |
| 9 | water | 2560 | 1194 | 2.14 |
| 10 | stone | 2304 | 1075 | 2.14 |
| … | … | … | … | … |
| 17 | heavy | 960 | 632 | 1.52 |

**The result is negative, and it is instructive.**  Every rank sits *above* the
Zipf prediction (`corpus_is_flatter_than_zipf`), and from rank 4 to rank 12 it
sits at more than twice it (`zipf_worst_case`).  This language is far flatter
than English.  Two causes, both visible in the design:

1. the vocabulary is 17 words, and Zipf's shape is mostly a statement about the
   long tail — this micro-world has no tail to have;
2. every content clause is *required to be news* (`and_is_informative`), which
   actively suppresses the repetition that makes "the" dominate English.

So Zipf's law is a good diagnostic here: it says, correctly, that the system is
not yet talking about enough different things.

**The principle of least effort, applied.**  Frequencies still buy something
concrete, because a cube has exactly 24 cells.  A fixed-length code over 17
words needs 5 bits per word — 4 words to a cube.  A Huffman code built inside
Lean from the measured counts gives `is`, `it`, `not`, `the` three bits and
`heavy` six, and is checked to be

* prefix-free, so a cube's worth of bits parses one way only;
* exactly invertible — every one of the 1536 paragraphs encodes and decodes back
  word for word;
* cheaper: **249528 bits against 331440 — 10397 cubes instead of 13810**, a 25%
  saving (`huffman_facts`, `least_effort_is_cheaper`).

---

## 4. Saying what to do
(`RequestProject/Narrative.lean`)

The most useful sentences are instructions.  `plan w goal` searches all action
sequences of length at most three and returns the shortest one that makes the
goal true; `storyData` walks it and records what *became* true at each step.

In the demo world, asked to make the water boil:

```
to make the water boil: 3 step(s)
  we heat the water, and nothing changes yet
  we heat the water, and now the water is not frozen, and the water is warm,
                            and the stone is not hotter than the water
  we heat the water, and now the water is boiling, and the water is not warm,
                            and the water is hotter than the stone,
                            and the lamp is not hotter than the water
so the water is boiling
```

The first line is worth keeping: heating water from −10 °C to 0 °C changes
nothing that this vocabulary can express, and the system says so rather than
padding.

Proved:

* `plan_correct` — a returned plan reaches its goal;
* `story_reports_real_changes` — every fact the story reports is true after that
  action and was false before it, so the narration is a record of change;
* `plan_facts` — over **all 512 worlds and all 48 contingent goals**: the plan
  found is never longer than any other sequence of at most three actions that
  works (so it is a shortest plan), 22080 of the 24576 goal/world pairs are
  reachable, and the remaining 2496 are reported unreachable rather than
  answered with an invented plan.

**Honest limit.** The horizon is three actions; the actions saturate at the ends
of the scales; and the system can exhibit the resulting measurements but cannot
yet explain *why* heating raises a temperature.

---

## 5. What is still missing

1. **Vocabulary.** Three things, six properties, three actions.  Everything
   above scales in principle, but nothing above proves that it does.
2. **No tail, hence no Zipf.** §3 measures this precisely; the fix is more
   things and more properties, not a different generator.
3. **Paragraph length is fuel, not content** (§1) — the generator stops at seven
   clauses by construction.
4. **Questions can cause repetition** (§2).  The system now *notices* — it says
   "as I said" — but it still has no way to answer a repeated question with
   anything more useful than the same fact again.
5. **Cross-subject pronouns.**  §1b names the thing again whenever the subject
   changes; it cannot yet say "the stone … the lamp … *the latter* is hotter".
6. **`because` is still entailment, not causation** — carried over from
   report 2, and unchanged.
7. **Planning has a three-action horizon** and no notion of cost or preference
   between plans of equal length.
8. **The cube is still storage, not thought.** §3 shows the least-effort code
   makes the cube hold 33% more language, and report 2 showed clauses can be
   stored with three-cell repair, but the reasoning itself does not happen on
   the cube.

## 6. Where to go next

* Widen the world (more things, more properties, ranges rather than four
  temperature steps) and re-measure the Zipf fit; that is the single change
  most likely to move the frequency curve.
* Let one clause refer to another clause ("that is why …"), which is the first
  step past subject-continuity anaphora.
* Give actions costs, so a plan can be argued for as well as exhibited.
* Detect that an answer repeats a commitment and say "as I said" instead.
