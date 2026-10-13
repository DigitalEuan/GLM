# The designed substrate — is the Golay–Leech carrier optimal for the GLM, and what resolves its ties?

## Tier 0 — the coarse read

**Question.** Is the Golay–Leech 24-dimensional substrate optimal for the GLM, can a designed dimensional system improve on it, and does bringing the owner's substrate study into the GLM measurably widen what its reasoning can resolve?

**Verdict.** In the GLM's regime the Golay carrier is optimal and cannot be beaten by any design of the same size; what can be improved is how its six-way tie is resolved, and the two new certified stages measurably widen that. Proved in the GLM's own Lean development, for every 4,096-word design with any decoder: none decodes correctly more often on the bit-flip channel, every one leaves at least 7,254,016 received words at distance 4 or more, and none that corrects three flips can correct more than one sixth of the four-flip corruptions. The eight declared alternative codes tie or lose and each silently miscorrects 2,695 to 4,480 four-flip corruptions, where the GLM's code miscorrects none. The sender-tag stage resolves every one of 680,064 tied reads to the sent codeword at seven bits per carrier, where the hard word alone resolves none; the soft-certificate stage resolves every read of the gentle ensemble and refuses every read of the existing K4b ensemble, whose noise lies outside its radius. Seven of eight marks were met; S7 was missed on a declaration that wrongly expected one sixth on a 64-codeword sample.

**Deciding figure.** 7 of 8 marks; 680,064 of 680,064 tied reads resolved by the tag, 0 wrong (0 by the hard word alone); 768 of 768 gentle reads resolved by the soft certificate, 0 wrong, and 0 of 768 K4b reads; 0 silent four-flip miscorrections for the GLM's code against 2,695 to 4,480 for each declared alternative; 7,254,016 received words at distance 4, equal to the proved floor.

**Recomputed by.** `glm_universal.reasoning.designed_substrate.designed_substrate_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. What this document is

A **pre-registration** for Phase 133, committed with its Lean file and before
the code that measures it exists. §§0–6 are as they were committed; §7 is what
came out.

The owner brought in a separate study, *Designed Dimensions × GLM*, now kept
at [`source_material/substrate_study/`](../source_material/substrate_study/README.md)
(its record is `glm_package/README.md` there, its theorem index
`glm_package/THEOREMS.md`, its reference implementation `glm_substrate.py`).
That study asked whether the Golay–Leech substrate is optimal or whether a
designed substrate could beat it, and answered, in its own Lean project:

* for the GLM's regime — 24-bit carriers holding 12 bits, corrupted by bit
  flips — the extended Golay code is optimal among *all* 4,096-word designs
  with any decoder;
* the six-way tie at coset weight 4 (the "negative space") is forced by the
  parameters, not by Golay: every design has at least as much of it;
* the freedom that remains is in **how the tie is resolved**, and it
  recommends a *triggered sextet mirror with soft resolution*: a sender tag of
  seven bits, a corruption-aware label of three bits, or a soft reading with a
  proved certificate.

The owner's question for this round is whether this can be brought in and
**measurably increase the GLM's reasoning abilities or scope**. The GLM already
holds much of the substrate side: the complete decoder that refuses to break a
tie (`substrate/golay_decode.py`), the carried fork that keeps all six
candidates and lets certified stages remove them
([`CARRIED_FORK_STUDY.md`](CARRIED_FORK_STUDY.md)), exact confidences
([`DECODER_CONFIDENCE_STUDY.md`](DECODER_CONFIDENCE_STUDY.md)), the sphere
bound and the 7,254,016-word deficit of 24 against 23
(`RequestProject/GLM/Packing.lean`), and rungs above Leech at 32 and 48
dimensions ([`HIGHER_LATTICE_STUDY.md`](HIGHER_LATTICE_STUDY.md)). What it
does not hold is:

1. a proof that **no other design** of the same size does better — the GLM's
   `Packing.lean` bounds codes that correct three errors, it does not compare
   decoders on the channel;
2. a proof that the share of the tie *any* design can resolve is capped;
3. a certified fork stage that resolves a tie **from information the sender
   supplies**, rather than from the closed world, a second read or an unsure
   set; and
4. a certified stage that resolves a tie **from a soft reading**. The carried
   fork's soft escalation is an *estimate*, right on 512 of 768 reads, and it
   missed its 90 % mark (`CARRIED_FORK_STUDY.md`, K4b).

This round brings those four in, on the GLM's own code and in its own Lean
development, and measures what they add.

**Order of work, stated plainly.**

1. *What was known before this was written.* The substrate study's record
   and its reference implementation, whose self-test passes (12 of 12). Two
   explorations were run on the GLM's code before this was committed, and
   are disclosed so that the marks they bear on are read as reproductions,
   not blind results: (a) a seeded random search for seven tag masks that
   give every octad a non-zero tag found the masks of §2 after 80,901 trials;
   (b) on the K4b soft ensemble of the carried fork (768 reads), **no** read
   lies within squared distance 8 of the sent carrier's ±1 image, so the soft
   certificate fires on none of them, while the least reliable of the six
   tetrads is the sent one on 576 of 768.
2. *The Lean file before this was committed.*
   `RequestProject/GLM/DesignedSubstrate.lean` was written with its statements
   and built (§1); its proofs are completed in the round.
3. **No code of the stages or of the measurement existed, and the gentle
   ensemble G of §2 had not been generated, when this was committed.**

## 1. What is proved (`RequestProject/GLM/DesignedSubstrate.lean`)

On the GLM's code (`Golay/Code.lean`: words are supports, `Finset (Fin 24)`,
the code is the kernel of `syn`). A *design* is any finite set `C` of words and
any decoder `D` with `D y ∈ C` for every `y`; nothing is assumed about either.

* `decoder_sum_le` — for weights `w` with `w i ≥ w 4` for `i ≤ 3` and
  `w i ≤ w 4` for `i ≥ 4`, `Σ_y w(d(y, D y)) ≤ |C| · Σ_{wt e ≤ 3}(w(wt e) − w 4)
  + 2²⁴ · w 4`.
* `golay_attains` — the GLM's code with any nearest-codeword decoder meets it
  with equality.
* `golay_optimal` — on the binary symmetric channel with flip rate
  `0 ≤ p ≤ 1/2`, no 4,096-word design with any decoder decodes correctly
  more often than the GLM's code.
* `negative_space_floor`, `negative_space_floor_4096` — every design leaves at
  least `2²⁴ − |C| · 2325` received words at distance ≥ 4 from its answer;
  7,254,016 for 4,096 words.
* `weight4_resolved_le`, `weight4_resolved_le_4096` — a design that corrects
  every corruption of weight ≤ 3 corrects at most 7,254,016 of the
  43,524,096 (codeword, weight-4 corruption) pairs: one sixth.
* `tag_nonzero_on_octads`, `tag_resolves` — the seven-bit tag of §2: no octad
  has tag zero (checked over the 4,096 messages), so two codewords within
  distance 4 of one received word with the same tag are equal.
* `soft_certificate`, `soft_certificate_sharp` — a soft reading within squared
  distance 8 of one codeword's ±1 image is more than 8 from every other; the
  radius 8 cannot be enlarged.

The theorems say nothing about the Python computing these objects correctly;
the measurement checks the constants against the Lean file and re-derives the
facts it relies on (S3).

## 2. The stages

Both stages are new fork stages over `reasoning/carried_fork.CarriedFork`.
They live in the new module `reasoning/designed_substrate.py` and write
ordinary `Elimination` records into the fork's ledger, so the rules of
`RequestProject/GLM/CarriedFork.lean` (the ledger partitions the candidates;
if every stage is true of the truth, a resolved fork holds the truth) apply to
them unchanged. `carried_fork.py` is not edited.

**The sender tag.** `TAG_MASKS = (7442265, 11191954, 5298992, 12955048,
9854244, 14599079, 3151149)`; the tag of a word is the seven parities of its
overlap with the masks (bit `i` is mask `i`). The sender stores or sends the
tag of the carrier beside it — seven bits per 24-bit carrier. The stage
`sender tag` removes every live candidate whose tag differs from the received
tag. *Assumption*, quoted on every elimination: "the tag was computed by the
sender from the carrier and arrived intact, and the carrier took at most four
flips".

**The soft certificate.** A soft reading is the K4b convention of the carried
fork (`0` is bit 0, `1` is bit 1, rationals), mapped to the ±1 picture by
`x = 1 − 2s`. The stage `soft certificate` removes every live candidate whose
image is at squared distance ≥ 8 from `x`, exactly in `Fraction`. *Assumption*:
"the soft reading lies within squared distance 8 of the sent carrier's ±1
image". By `soft_certificate` at most one candidate survives.

**The gentle ensemble G** (declared here, generated only after this is
committed). For read `i` of the K4b probe (`carried_fork.x1_probe`: 64
codewords × 12 weight-4 errors, in that order), sent codeword `c`, error `e`,
hard word `y = c ⊕ e`: at coordinate `j`, the reliability is
`ρ = ((3i + j) mod 4 + 1)/16` if `j` is in the error and
`ρ = ((i + j) mod 4 + 5)/8` otherwise, and the soft value is `(1 + ρ)/2` where
`y` has a 1 and `(1 − ρ)/2` where it has a 0 — the K4b formula with smaller
reliabilities on the flipped bits and larger ones elsewhere.

**Designed alternatives.** The punctured code `[23,12,7]` is the GLM's code
with coordinate 23 removed; its *one-bit extensions* append a 24th bit equal to
coordinate 23 of the Golay word plus the parity of the message bits selected by
a 12-bit mask `λ` (the message is coordinates 0–11; `λ = 0` gives the GLM's
code). Eight are declared: `λ ∈ {1, 2, 4, 8, 3, 7, 15, 4095}`. A weight-4
corruption of a codeword is *silently miscorrected* when the nearest codeword
to the received word is unique and is not the one sent.

## 3. The marks, declared before the code

| mark | what is measured | pass |
|---|---|---|
| **S1** | `RequestProject/GLM/DesignedSubstrate.lean` | builds, no `sorry`, standard axioms plus those of `native_decide` |
| **S2** | the sender-tag stage on all 64 probe codewords × all 10,626 weight-4 errors (680,064 reads, each carried with `carry`) | every read resolved, to the sent codeword: 680,064 resolved, 0 wrong, 0 contradicted |
| **S3** | the constants and the facts the stages rely on | `TAG_MASKS` equal `tagMasks` in the Lean file; all 759 octads have a non-zero tag; every carried weight-4 read has six candidates whose ±1 images are pairwise at squared distance 32 |
| **S4** | the soft-certificate stage on the K4b ensemble (768 reads) | 0 wrong; it resolves 0 reads (the disclosed exploration); the carried fork's K4b figures are unchanged (estimate right on 512) |
| **S5** | the soft-certificate stage on the gentle ensemble G (768 reads) | at least 90 % resolved, 0 wrong, and every resolved read resolved to the least reliable tetrad's candidate |
| **S6** | the eight declared one-bit extensions and the GLM's code, every weight-4 corruption of the zero word (10,626 each; all codes are linear, so the zero word stands for every codeword) | every extension silently miscorrects at least one; the GLM's code silently miscorrects none |
| **S7** | the floor and the one-sixth cap on the GLM's own decoder | the complete decoder's census puts exactly 7,254,016 received words at distance 4 (= the floor); on the 64 probe codewords the legacy snap decoder corrects exactly 64 × 1,771 = 113,344 of the 680,064 weight-4 reads (= one sixth) |
| **S8** | non-interference | no existing module of `glm_universal` is edited; `carried_fork_report` returns its recorded figures |

## 4. Controls

* **A corrupted tag** (reported, not a mark). The tag stage is run on the 680,064
  reads of S2 with the received tag's bit `i mod 7` flipped. The assumption is
  then false, and the stage may contradict the fork or resolve it wrongly; the
  counts are reported as the price of the assumption.
* **The soft stage with its assumption false** (reported). On K4b the truth is
  never within the radius, so the stage's verdict is "contradicted" — a
  refusal, never an answer; reported as such.
* **The closed world without a tag** (reported). For comparison with S2, the
  share of the same reads that the existing certified stages resolve with no
  extra information: the context stage over the K1 case set of 32 codewords
  and the hard word alone.

## 5. What this round does not do

* It does not put either stage into a query kind. Reading a carrier together
  with its tag or a soft reading is not something a query can supply yet;
  that is left as a To-Do line.
* It does not re-prove the substrate study's other results (the mirror floor
  of four labels, the five-label code, the Delsarte bound, the quantum
  verdicts, the Leech kissing number); they are cited from its record and its
  theorem index, which the owner holds in full.
* It does not compare against other dimensions by experiment. The 32- and
  48-dimensional rungs are measured in
  [`HIGHER_LATTICE_STUDY.md`](HIGHER_LATTICE_STUDY.md); outside the 24-bit,
  12-bit, bit-flip regime the optimality theorem does not apply, and §7 says
  what that leaves.

## 6. Files

| file | what |
|---|---|
| `overlay/glm_lean/RequestProject/GLM/DesignedSubstrate.lean` | §1 |
| `overlay/glm_universal/reasoning/designed_substrate.py` | the stages, the ensembles, the marks, `designed_substrate_report` |
| `overlay/glm_universal/tests/test_designed_substrate.py` | the tests |
| `overlay/glm_universal/tools.py` | `tools designed-substrate` |
| `source_material/substrate_study/` | the owner's study, as supplied |

## 7. The measurement

`PYTHONPATH=. python3 -m glm_universal.tools designed-substrate` (about a
minute); `tests/test_designed_substrate.py` pins every figure below.

### 7.1 The verdict

In the GLM's regime the Golay carrier is optimal and cannot be beaten by any design of the same size; what can be improved is how its six-way tie is resolved, and the two new certified stages measurably widen that.

### 7.2 The marks

| mark | measured | met |
|---|---|---|
| **S1** | `DesignedSubstrate.lean` builds, no `sorry`; `#print axioms` on `golay_optimal`, `tag_resolves`, `soft_certificate` gives `propext`, `Classical.choice`, `Quot.sound` and the two axioms of `native_decide` (through the GLM's existing Golay census and the tag check); `negative_space_floor_4096` and `weight4_resolved_le_4096` use the standard three only | yes |
| **S2** | sender tag on 680,064 tied reads: 680,064 resolved, 0 wrong, 0 open, 0 contradicted | yes |
| **S3** | the masks equal the Lean file's; 759 of 759 octads have a non-zero tag; 680,064 of 680,064 reads carry six candidates pairwise at squared distance 32 | yes |
| **S4** | soft certificate on K4b: 0 of 768 resolved, 0 wrong, 768 refused (contradicted); the sent carrier is within the radius on 0 reads | yes |
| **S5** | soft certificate on the gentle ensemble G: 768 of 768 resolved, 0 wrong, every one to the least reliable tetrad's candidate | yes |
| **S6** | silent four-flip miscorrections: the GLM's code 0 (it has no weight-7 word); `λ = 1, 2, 4, 8`: 2,695 each; `λ = 3`: 3,920; `λ = 7`: 4,375; `λ = 15`: 4,480; `λ = 4095`: 3,920 | yes |
| **S7** | the complete decoder's census puts 7,254,016 received words at distance 4, equal to the floor; but on the 64 probe codewords the legacy snap decoder corrects **120,604** weight-4 reads, not the declared 113,344 | **no** |
| **S8** | no existing reasoning or substrate module edited (`tools.py` only gained the command); the carried fork's stages are still the three it had; its K4b estimate is still right on 512 of 768 | yes |

**Why S7 missed.** The declaration expected exactly one sixth on a 64-codeword
sample. The one-sixth figure is a statement about all 4,096 codewords
together: each of the 7,254,016 received words at distance 4 is decoded to one
of its six candidates, so a decoder that picks one corrects exactly that many
(codeword, weight-4 error) pairs in total, which is the cap of
`weight4_resolved_le_4096`. How those corrections fall across codewords
depends on the scan order, and on the probe's 64 codewords they come to
120,604. The floor clause of S7 held; the sample clause was a wrong
expectation, not a wrong answer. The module reports the total over all
codewords beside the declared figure (`all_codewords_snap_right_by_coset`),
marked post hoc.

### 7.3 Controls

* **A corrupted tag.** With one tag bit flipped, the stage contradicts the fork
  on 651,968 of 680,064 reads (95.9 %) and resolves it **wrongly** on 28,096
  (4.1 %); it never resolves to the truth. The assumption that the tag arrives
  intact is load-bearing: a tag must be stored or sent where it cannot be
  corrupted, or protected by its own code.
* **The soft stage with its assumption false.** On K4b every read is refused
  (contradicted), never answered. The least reliable tetrad, which the carried
  fork already computes as its Euclidean estimate, is the sent one on 576 of
  768; the certificate is what says when that estimate is safe, and on K4b it
  never is.
* **The closed world without a tag.** The context stage over the K1 case set
  of 32 codewords resolves 291,712 of 340,032 reads (85.7 %), 0 wrong, under
  the closed-world assumption; the hard word alone resolves 0 of 680,064.
* **Figures elsewhere that move with the Lean corpus.** Adding
  `DesignedSubstrate.lean` moved the stack relay's gate sweep forward: strict
  on all five gates, to 1/4 (354 against 350 of 423 on the tuning stride),
  where Phase 132 had left it at 1/5. It is recorded as measured in
  `test_stack.py` and `STACK_RELAY_STUDY.md`; no answer of this study depends
  on it.

### 7.4 What it answers

**Is Golay–Leech/24D optimal for the GLM?** For what the GLM does with it —
24-bit carriers holding 12 bits, read back after bit flips — yes, and now by a
theorem of the GLM's own development rather than by quotation:
`golay_optimal` compares the GLM's code against *every* 4,096-word design with
*any* decoder. The negative space (`negative_space_floor_4096`) and the
one-sixth cap on four-flip corrections (`weight4_resolved_le_4096`) belong to
the parameters, so no designed substrate of the same size removes them.

**Can a designed system improve on it?** Not inside the regime; S6 shows what
the nearest designs cost: they tie on the channel (each one-bit extension of
the perfect `[23,12,7]` code has every received word within distance 4 and
disjoint radius-3 balls, which is all the argument of `golay_attains` uses),
but they silently miscorrect thousands of four-flip corruptions that the GLM's
code flags. Outside it the theorem says
nothing: soft information, longer blocks, other rates and other noise all fall
outside, and the GLM's 32- and 48-dimensional rungs
([`HIGHER_LATTICE_STUDY.md`](HIGHER_LATTICE_STUDY.md)) are where a larger
substrate is measured. The substrate study's other results — the mirror needs
at least four labels for any design, five are achievable, a sender tag needs at
least eight values for any design and between 86 and 128 for Golay — are cited
from its record, not re-proved here.

**Does it widen what the GLM can resolve?** Yes, measurably, at the carried
fork. Before this round a tied read could be resolved only by the closed world,
a second read or an unsure set. With seven bits stored per carrier it is
resolved every time without any of them (S2), and a soft reading that is good
enough is resolved for free with a certificate (S5) where the existing
escalation could only estimate. Neither stage is reached from a query yet.

### 7.5 What this round leaves

* **The tag and the soft certificate in the answering path.** No query kind
  reads a carrier together with its tag or a soft reading; adding one changes
  what the runtime accepts and needs its own evaluation cases.
* **A protected tag.** The corrupted-tag control resolves 4.1 % of reads
  wrongly; a tag carried by its own small code would turn those into refusals.
* **A soft ensemble from the GLM's own data.** S4 and S5 are declared
  ensembles; where the GLM has a soft reading of its own (a rational
  coordinate before quantisation), the certificate's acceptance rate on it is
  the figure that matters.
