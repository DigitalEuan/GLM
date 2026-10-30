# The protected tag — a carrier read in the answering path, and a sender tag with a code of its own

## Tier 0 — the coarse read

**Question.** Can the GLM answer a question about a carrier with the stages Phase 133 proved sound, and can the sender tag be made to survive its own corruption?

**Verdict.** The GLM can now be asked about a carrier, and a sender tag protected by a code of its own absorbs two flipped tag bits where the seven-bit tag absorbs none. The new query kind reads a 24-bit word through the carried fork and the stages the request supplies information for, answers only when one candidate survives and refuses an open tie or a contradicted read; all nine declared questions came out as declared. Proved in the GLM's Lean development: a tag absorbs as many flipped bits as the least tag weight over the octads allows, which is none for the seven-bit tag and two for the fifteen-bit tag, and an intact tag disagrees with every wrong decode on up to seven flips. Measured, both protected tags resolve all 680,064 tied reads with up to their radius of flipped tag bits, 0 wrong, where the seven-bit tag with one flip answers 28,096 wrongly; on 523,204 reads with five to seven flips the decoder alone answers 409,860 wrongly and a tag none. Six of seven marks were met; P5 was missed on a declared three-flip pattern that never misled radius 2.

**Deciding figure.** 6 of 7 marks; 680,064 of 680,064 tied reads resolved by each protected tag, 0 wrong (28,096 wrong for the seven-bit tag with one flip); 409,860 wrong decodes of 523,204 heavy reads by the decoder alone, 0 with a tag; 9 of 9 declared questions as declared.

**Recomputed by.** `glm_universal.reasoning.carrier_read.protected_tag_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. What this document is

A **pre-registration** for Phase 134. §§0–6 are as they were committed,
before any measurement in §3 was taken (the tier-0 block above was filled in
at the close); §7 is what came out.

Phase 133 ([`DESIGNED_SUBSTRATE_STUDY.md`](DESIGNED_SUBSTRATE_STUDY.md)) left
three lines in `STATUS.md` §2.2, "The designed substrate, the rest", and this
round takes the first two:

1. **No query kind reads a carrier.** The sender-tag and soft-certificate
   stages were measured beside the carried fork only; no question could reach
   them. (This is also the first step of `STATUS.md` §2.1 item 1, which
   observed that the placement guard has no answering path to guard until a
   query kind reads a carrier.)
2. **The tag has no protection.** With one tag bit flipped, the seven-bit tag
   resolves 28,096 of 680,064 tied reads to the wrong carrier. Phase 133
   recommended "a small code of its own".

The third line — the soft certificate on a soft reading the GLM produces
itself — is not taken: the GLM still produces no soft reading of its own. The
query kind below *accepts* a soft reading, so the certificate is reachable,
but the reading has to be supplied.

**Order of work, stated plainly.** Before this was written:
`RequestProject/GLM/ProtectedTag.lean` was written and built, with every
proof complete (§1); the two protected tags of §2 were chosen by construction
(the seven tag bits followed by the parities of a textbook code on them), and
their smallest octad weights (3 and 5) and the two witnesses of §1 were found
by an exploration over the 759 octads, disclosed here so that P2 is read as a
reproduction; `reasoning/carrier_read.py` was written, and the nine
evaluation questions of P7 were worked out by running its read on the one
carrier they use. No mark of §3 was run before this was committed.

## 1. What is proved (`RequestProject/GLM/ProtectedTag.lean`)

On the GLM's code, as in `DesignedSubstrate.lean`. A *mask tag* `mtag M r w`
is the `r` parities of a word's overlap with the masks `M`; the seven-bit tag
of Phase 133 is `mtag tagMasks 7` (`mtag_tagMasks`, by definition).

* `close_pair_octad` — two distinct codewords at most 11 apart differ by an
  octad.
* `mtag_separation` — if every octad's tag has weight at least `D`, then for
  two distinct codewords at most 11 apart and **any** received tag `τ`,
  `D ≤ d(τ, tag c) + d(τ, tag c')`. Two candidates of one fork are at most
  8 apart; a sent carrier that took at most 7 flips and a wrong codeword
  within 4 of the received word are at most 11 apart.
* `mtag_resolves` — so a stage keeping the candidates whose tag lies within
  `s` of `τ`, with `2s < D`, keeps at most one candidate of a fork.
* `tag_flags_miscorrection` — the intact seven-bit tag of the sent carrier
  differs from the tag of every other codeword within 4 of the received word,
  whenever the carrier took at most **7** flips. A decoder's silent wrong
  answer on heavy corruption is therefore always caught by an intact tag.
* `tag7_one_flip_misleads` — an explicit fork and a received tag one flip
  from the sent carrier's tag and *equal* to another candidate's: the
  seven-bit tag absorbs no flip at all.
* `tag11_octad_weight`, `tag15_octad_weight` — every octad has an
  eleven-bit tag of weight ≥ 3 and a fifteen-bit tag of weight ≥ 5 (checked
  over the 4,096 messages).
* `tag11_corrects_one`, `tag15_corrects_two` — for a carrier that took at
  most 7 flips and a received tag within 1 (resp. 2) flips of its tag, every
  other codeword within 4 of the received word has its tag more than 1
  (resp. 2) flips away.
* `tag15_radius_one_safe` — read at radius 1, the fifteen-bit tag never names
  a wrong candidate when its tag took up to 3 flips.
* `tag15_three_flips_mislead` — radius 2 is sharp: three flips can bring the
  received tag within two of another candidate's.

The theorems say nothing about the Python computing these objects; P2 checks
the constants against the Lean file and re-derives the octad weights.

## 2. The stages and the query kind

**The protected tags.** `TAG11_MASKS` is the seven tag masks followed by four
masks giving the parities of the shortened Hamming `[11,7,3]` code (generator
`x⁴ + x + 1`) on the seven tag bits; `TAG15_MASKS` the seven followed by the
eight parities of the `[15,7,5]` BCH code (generator
`x⁸ + x⁷ + x⁶ + x⁴ + 1`). Because each parity of the tag bits is itself a
parity of the carrier, the protected tag is a mask tag over the carrier and
the first seven bits are the old tag. The stage `protected tag` keeps the
candidates whose tag is within the radius of the received tag; the answering
path reads the fifteen-bit tag at radius 2. *Assumption*, quoted on every
elimination: "the protected tag was computed by the sender from the carrier
and took at most two flips, and the carrier took at most seven".

**The query kind `carrier`.** Opened by `carrier`, `read carrier` or
`decode carrier`, start-only (an ordinary use of the word in another question
is not a carrier read). The request is
`carrier <word> [tag <t>] [protected tag <p>] [soft <s1>, ..., <s24>]`,
numbers in hex (`0x`), binary (`0b`) or decimal, soft values exact
rationals or decimals in `[0, 1]` (the chance each bit is a one; the K4b
convention). Without a word the hard word is the soft reading thresholded at
1/2. The read is the carried fork (`carried_fork.carry`) followed by each
stage the request supplies information for: sender tag, protected tag, soft
certificate. It **answers** only when exactly one candidate survives — the
codeword, its twelve message bits (coordinates 0–11) and the flips corrected —
and it **refuses**, as a `boundary`, when the fork stays open (the six-way tie
with nothing to resolve it), when it is contradicted (no candidate is
consistent with the tag or the soft reading: corruption beyond the stage's
assumption), and when the request is malformed (not a 24-bit word, a tag of
the wrong width, a soft reading of the wrong length, words it does not take).

## 3. The marks, declared before the measurement

The tied battery is Phase 133's: the 64 probe codewords of
`carried_fork.x1_probe` × all 10,626 weight-4 errors, 680,064 reads, read `i`
in that order. Flip positions are declared: for the fifteen-bit tag the first
`f` of `i, i+5, i+10 (mod 15)`; for the eleven-bit tag position `i mod 11`;
for the seven-bit tag `i mod 7` (Phase 133's control).

| mark | what is measured | pass |
|---|---|---|
| **P1** | `RequestProject/GLM/ProtectedTag.lean` | builds, no `sorry`, standard axioms plus those of `native_decide` |
| **P2** | the constants | `TAG11_MASKS`, `TAG15_MASKS` equal `tagMasks11`, `tagMasks15` in the Lean file; their first seven are `TAG_MASKS`; over the 759 octads the smallest tag weight is 1 (seven-bit), 3 (eleven-bit), 5 (fifteen-bit) |
| **P3** | the protected tags on the tied battery with `f ≤` radius flips: the fifteen-bit tag at radius 2 with `f = i mod 3`; the eleven-bit tag at radius 1 with `f = i mod 2` | both: 680,064 resolved, 0 wrong |
| **P4** | the seven-bit tag with one flip, on the same battery | reproduces Phase 133's control: exactly 28,096 wrong |
| **P5** | the fifteen-bit tag with three flips (beyond radius 2) | at radius 2, at least one wrong (radius 2 is sharp); at radius 1, 0 wrong (`tag15_radius_one_safe`) |
| **P6** | heavy corruption: for probe codeword `k` and each weight 5, 6, 7, every 64th error in combinations order starting at index `k`; the decoder alone, the intact seven-bit tag, and the fifteen-bit tag with `f = i mod 3` flips at radius 2 | the decoder alone answers at least one read wrongly; both tags answer 0 wrongly |
| **P7** | the `carrier` kind: nine declared evaluation cases (§3.1), and the end-to-end evaluation | all nine as declared; every earlier case keeps its outcome; 0 confidently wrong |

### 3.1 The nine questions

All on one carrier: message `0x5a3`, codeword `0x8ad5a3`; its tag `0x54`, its
fifteen-bit tag `0x1a54`. The weight-4 error is coordinates 1, 9, 14, 22
(read `0xca97a1`, a six-way tie); adding coordinate 5 gives a weight-5 read
`0xca9781`, which the decoder alone corrects to the wrong codeword `0x428781`.

| id | question | declared |
|---|---|---|
| `carrier-clean` | `carrier 0x8ad5a3` | answer: `0x8ad5a3`, message `0x5a3`, 0 flips |
| `carrier-two-flips` | `carrier 0x88d5ab` | answer: `0x8ad5a3`, message `0x5a3`, 2 flips |
| `carrier-tie` | `carrier 0xca97a1` | refusal, `boundary`: six candidates, nothing to resolve them |
| `carrier-tag` | `carrier 0xca97a1 tag 0x54` | answer: `0x8ad5a3`, by the sender tag |
| `carrier-protected-tag` | `carrier 0xca97a1 protected tag 0x1256` (two flips) | answer: `0x8ad5a3`, by the protected tag |
| `carrier-flagged` | `carrier 0xca9781 tag 0x54` | refusal, `boundary`: the tag contradicts the only candidate |
| `carrier-soft` | `carrier soft` + read 0 of the gentle ensemble G of Phase 133 | answer: `0x8ad5a3`, by the soft certificate |
| `carrier-not-a-word` | `carrier 0x1000000` | refusal, `boundary` |
| `carrier-tag-width` | `carrier 0xca97a1 tag 0x154` | refusal, `boundary` |

## 4. Controls

* The seven-bit tag with one flip (P4) is the control for P3: the same
  battery, the same kind of corruption, no code on the tag.
* The decoder alone (P6) is the control for the tags on heavy corruption.
* Beyond the radius (P5) the assumption is false, and the counts are reported
  as its price.

## 5. What this round does not do

* It does not make the GLM produce a soft reading; the certificate is
  reachable only through a supplied one.
* It does not guard the carrier read with the placement guard (`STATUS.md`
  §2.1 item 1). The read is the Golay layer only; the ladder the guard
  protects is not reached from it.
* It does not choose a tag shorter than eleven or fifteen bits by search, and
  makes no claim that these lengths are least possible.

## 6. Files

| file | what |
|---|---|
| `glm_lean/RequestProject/GLM/ProtectedTag.lean` | §1 |
| `glm_universal/reasoning/carrier_read.py` | the protected tags, the read, the marks, `protected_tag_report` |
| `glm_universal/runtime/parser.py`, `runtime/session.py` | the `carrier` kind and its solver |
| `glm_universal/evaluation/cases.py` | the nine cases of §3.1 |
| `glm_universal/tests/test_carrier_read.py` | the tests |
| `glm_universal/tools.py` | `tools protected-tag` |

## 7. The measurement

`PYTHONPATH=. python3 -m glm_universal.tools protected-tag` (about two
minutes); `tests/test_carrier_read.py` pins every figure below.

### 7.1 The verdict

The GLM can now be asked about a carrier, and a sender tag protected by a code of its own absorbs two flipped tag bits where the seven-bit tag absorbs none. The new query kind reads a 24-bit word through the carried fork and the stages the request supplies information for, answers only when one candidate survives and refuses an open tie or a contradicted read; all nine declared questions came out as declared. Proved in the GLM's Lean development: a tag absorbs as many flipped bits as the least tag weight over the octads allows, which is none for the seven-bit tag and two for the fifteen-bit tag, and an intact tag disagrees with every wrong decode on up to seven flips. Measured, both protected tags resolve all 680,064 tied reads with up to their radius of flipped tag bits, 0 wrong, where the seven-bit tag with one flip answers 28,096 wrongly; on 523,204 reads with five to seven flips the decoder alone answers 409,860 wrongly and a tag none. Six of seven marks were met; P5 was missed on a declared three-flip pattern that never misled radius 2.

### 7.2 The marks

| mark | measured | met |
|---|---|---|
| **P1** | `ProtectedTag.lean` builds, no `sorry`; `#print axioms` on `mtag_resolves`, `tag_flags_miscorrection`, `tag15_corrects_two`, `tag15_radius_one_safe`, `tag11_corrects_one`, `tag7_one_flip_misleads` and `tag15_three_flips_mislead` gives `propext`, `Classical.choice`, `Quot.sound` and the axioms of `native_decide` (the octad-weight checks, the witnesses, and `tag_nonzero_on_octads` through the seven-bit tag) | yes |
| **P2** | the masks equal `tagMasks11` and `tagMasks15`, and their first seven are `TAG_MASKS`; least octad tag weight 1 (42 of 759 octads), 3 (78) and 5 (108) | yes |
| **P3** | 680,064 tied reads: the fifteen-bit tag at radius 2 with `i mod 3` flipped tag bits resolves 680,064, 0 wrong; the eleven-bit tag at radius 1 with `i mod 2` resolves 680,064, 0 wrong | yes |
| **P4** | the seven-bit tag with one flip: 28,096 wrong, 651,968 contradicted, 0 right — Phase 133's control, reproduced | yes |
| **P5** | three flips at `i, i+5, i+10 (mod 15)`: radius 2 contradicts all 680,064 reads and answers **0** wrongly, where at least one was declared; radius 1 contradicts all 680,064, 0 wrong | **no** |
| **P6** | 523,204 reads with 5, 6 or 7 flips (42,504; 134,596; 346,104 — every error of each weight once, spread over the 64 probe codewords): the decoder alone answers 409,860 wrongly (42,504; 21,252; 346,104) and leaves 113,344 weight-6 reads tied; the intact seven-bit tag and the fifteen-bit tag with up to two flips at radius 2 answer 0 wrongly and refuse every read | yes |
| **P7** | the nine questions of §3.1 through the end-to-end evaluation: five answered as declared, four refused as `boundary`; every column-3 script of an answer verifies in a fresh interpreter and is exact; the evaluation's earlier cases keep their outcomes (the close's sign-off) | yes |

**Why P5 missed.** The mark expected the declared three-flip pattern to bring
the received tag within two flips of a wrong candidate's tag at least once.
That needs the three flipped positions to lie inside the support of a
weight-5 tag difference between two candidates of the read's fork. The
`[15,7,5]` code is cyclic, and the declared positions form a coset of the
subgroup `{0, 5, 10}` of the fifteen positions; the measurement shows that on
this battery the declared coset never lies inside such a difference, so the
pattern never misleads.
The expectation was wrong, not the stage: radius 2 is sharp by
`tag15_three_flips_mislead`, and with three consecutive flips
`i, i+1, i+2 (mod 15)` — run post hoc, after the miss, and reported as such —
radius 2 answers **26,681** of the 680,064 reads wrongly and radius 1 still
none.

### 7.3 Controls

* **The seven-bit tag with one flip** (P4) against the protected tags (P3):
  the same battery and the same kind of corruption; 28,096 wrong against 0.
* **The decoder alone on heavy corruption** (P6): every five- and seven-flip
  read is decoded to a wrong codeword at distance 3 or less — 388,608 silent
  wrong answers — and 21,252 of the six-flip reads too; with a tag every one
  of them is refused. This is `tag_flags_miscorrection` at work: a wrong
  codeword within 4 of a read of a carrier with up to seven flips is an octad
  from the sent one, and the tag of an octad is never zero.
* **Beyond the radius** (P5 and its post-hoc run): three flipped tag bits can
  mislead radius 2 (26,681 of 680,064 with consecutive flips); radius 1 never
  misleads on three, at the price of correcting only one.
* **The question path.** `carrier 0xca9781` — the five-flip read of §3.1 —
  is answered by the decoder alone as `0x428781`, a wrong codeword at
  distance 3, which is the right reading of that word alone; with the tag
  (`carrier-flagged`) it is refused.

### 7.4 What it answers

**Is the carrier read in the answering path?** Yes. Phase 133's two stages
and the protected tag are reached from a question, and the question path
refuses exactly where the substrate cannot decide: the six-way tie, by name,
and a read no candidate of which agrees with the information supplied. It is
derivation in the sense of directive D15 — no register holds the codeword of
a received word and its tag — and it is refusal: a tag turns the decoder's
silent wrong answers into refusals.

**Does the tag survive its own corruption?** The seven-bit tag does not, and
now provably so (`tag7_one_flip_misleads`). The fifteen-bit tag does, up to
two flipped bits, for a carrier that took up to seven flips; the price is
eight more bits per carrier (fifteen against seven). Radius 1 is the safer
reading of the same tag: it corrects one flipped bit and never names a wrong
candidate on three.

### 7.5 What this round leaves

* **A soft reading of the GLM's own.** The certificate is reached only
  through a supplied soft reading; where the GLM has a soft reading of its own
  the acceptance rate on it is the figure that matters, and none exists yet.
* **A guard for the carrier read.** Three or more flipped tag bits can
  mislead radius 2; a deployment that cannot bound the tag's corruption should
  read it at radius 1.
* **The placement guard's answering path** (`STATUS.md` §2.1 item 1) still
  needs a query kind that reads a *ladder* carrier by its address; the
  `carrier` kind reads a 24-bit Golay word and is the pattern to follow.
* **Shorter tags.** Eleven and fifteen bits come from textbook codes on the
  seven tag bits; whether a shorter tag over the carrier reaches octad weight
  3 or 5 was not searched.
