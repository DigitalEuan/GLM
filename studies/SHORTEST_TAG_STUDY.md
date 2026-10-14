# The shortest tag — how many tag bits a tie needs

## Tier 0 — the coarse read

**Question.** Are the GLM's sender tags (seven bits) and protected tags (eleven and fifteen bits) as short as such tags can be, or would fewer bits do?

**Verdict.** The seven-bit sender tag is proved to be the shortest tag that resolves every tie, and the eleven- and fifteen-bit protected tags are proved to be the shortest tags built as parities of seven tag bits. Every parity tag whose octad tags have weight at least D needs at least D + 6 bits, so 9 and 11 bits is the proved floor for tags of any other shape. The gap between the floors is searched, not settled: the search found no shorter tag at any gap length, but its control found the 15-bit length on none of three seeds, so for two flipped bits the empty search is weak evidence. Five of six marks were met; S5 was missed on that control.

**Deciding figure.** 5 of 6 marks; floors 7, 9, 11 bits for any tag and 7, 11, 15 for tags built on seven bits, met by the tags in use; least deficit in the gap 35 and 9 (D = 3, 9 and 10 bits) and 179, 99, 45, 15 (D = 5, 11 to 14 bits); control found 7 bits on 3 of 3 seeds, 11 bits on 2 of 3, 15 bits on 0 of 3.

**Recomputed by.** `glm_universal.reasoning.shortest_tag.shortest_tag_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. What this document is

A **pre-registration** for Phase 135. §§0–6 are as they were committed,
before the search of §3 was read (the tier-0 block above is filled in at the
close); §7 is what came out.

Phase 134 ([`PROTECTED_TAG_STUDY.md`](PROTECTED_TAG_STUDY.md)) ended on the
line "tags shorter than eleven or fifteen bits were not searched for"
(`STATUS.md` §2.2, "The designed substrate, the rest"), and its §5 said
plainly that it "makes no claim that these lengths are least possible". This
round asks the question in the GLM's Lean development first and measures only
what the proofs leave open.

**Order of work, stated plainly.** Before this was written:
`RequestProject/GLM/ShortestTag.lean` was written and built, with every proof
complete (§1); `reasoning/shortest_tag.py` was written; a throw-away annealing
prototype (outside the repository) was run on the gap lengths of §3 to choose
the search's budget, and it found no tag in the gap and found the 11- and
15-bit constructions again. That prototype is disclosed so that S6 is read as
a reproduction by the module's own search, not a first look. The module's
search was started at the same commit as this document and its output was not
read before the commit.

## 1. What is proved (`RequestProject/GLM/ShortestTag.lean`)

On the GLM's code, as in `ProtectedTag.lean`. A tag of `r` bits is any list
of parity masks; it resolves every tie at radius `s` when every octad's tag
has weight `D > 2s` (`mtag_separation`). The three tags in use have
`(r, D) = (7, 1), (11, 3), (15, 5)`.

**The general floor.**

* `octadFree_avoiding_card_le` — the Plotkin step: a set of codewords closed
  under symmetric difference, with no octad, avoiding one coordinate, has at
  most 24 words (each of the other 23 coordinates is set in at most half of
  them; every nonzero word has weight at least 12).
* `kernel_card_ge` — an additive map from the code to `k` bits vanishes on at
  least `4096 / 2ᵏ` codewords.
* `short_tag_kills_octad`, `short_mtag_kills_octad` — every additive tag of at
  most six bits sends some octad to zero (six bits and the avoided coordinate
  leave at least 32 codewords, more than 24).
* `tag_length_floor` — octad weight `≥ D ≥ 1` needs `r ≥ D + 6` bits.
* `tag7_shortest` — the seven-bit tag is the shortest that resolves every
  tie. `protected_tag_floors` — one flipped tag bit needs at least nine bits,
  two at least eleven.

**Tags built on the seven-bit tag.** Both protected tags are parities of the
seven tag bits (`tag11_built`, `tag15_built`, with the selector rows
`selRows11`, `selRows15`).

* `tag7_octads_onto` — a seven-bit tag that gives every octad a nonzero value
  takes all 127 nonzero values on the octads (`tag7_value_is_octad_value`: a
  coset of its kernel with no octad would give a closed octad-free set of at
  least 64 codewords, against `octadFree_closed_card_le`, at most 48).
* `built_tag_floor` — so a tag `L ∘ T` built on such a tag, with octad weight
  `≥ 3`, is a `[r, 7, 3]` code and needs `r ≥ 11` (`built_tag_packing`,
  sphere packing); with octad weight `≥ 5` it is a `[r, 7, 5]` code and needs
  `r ≥ 15` (`no_14_7_5`: append the parity bit; a word of weight 6 leaves a
  nine-position residual where 64 classes sit pairwise at distance `≥ 3`,
  `no_even_15_7_6`; if every weight is `≥ 8`, `first_moment` gives
  `8 · 127 > 15 · 64`).
* `protected_tags_shortest_of_shape` — the eleven- and fifteen-bit protected
  tags are the shortest tags of their shape.

**What is not proved.** A tag *not* built on seven bits — one whose
functionals span more than seven dimensions — might sit in the gap: nine or
ten bits for `D = 3`, eleven to fourteen for `D = 5`.

## 2. The module

`reasoning/shortest_tag.py` holds the floors as constants (`FLOOR_GENERAL`,
`FLOOR_BUILT`), the census functions the marks read, and a search.

**The search.** Every functional on the code is realised by a mask on the
twelve low coordinates (the 4,095 nonzero such masks give 4,095 distinct
hit-sets over the 759 octads). A tag of `r` bits is `r` of them. Its
*deficit* is `Σ_octads max(0, D − weight)`, zero exactly when the tag works.
`local_search(r, D, moves, seed)` anneals single-bit replacements chosen by a
fixed integer recurrence (no float, no RNG), the temperature falling from 2 to
0.05; `gap_search` runs it with 2,000,000 proposals for each of three seeds.

## 3. The marks, declared before the measurement

| mark | what is measured | pass |
|---|---|---|
| **S1** | `RequestProject/GLM/ShortestTag.lean` | builds, no `sorry`, every theorem of `LEAN_THEOREMS` present; axioms standard plus those of `native_decide` |
| **S2** | the constructions | least octad weight 1, 3, 5 for the 7-, 11- and 15-bit tags; lengths equal `FLOOR_BUILT`; both protected tags are built on the seven-bit tag with the selector rows of the Lean file |
| **S3** | the Plotkin step on the seven-bit tag's own kernel | 32 codewords, no octad, at most 24 avoiding any one coordinate |
| **S4** | `tag7_octads_onto` on the seven-bit tag | all 127 nonzero values taken by octads, zero not taken |
| **S5** | the search's control: `(r, D) = (7, 1), (11, 3), (15, 5)` | for each, at least one of the three seeds reaches deficit 0, and the tag found is verified |
| **S6** | the search on the gap: `D = 3` with `r = 9, 10`; `D = 5` with `r = 11, …, 14` | every gap length ends with a positive least deficit (no shorter tag found) |

S6 is declared in the direction the prototype pointed. A deficit of zero
there would be a shorter tag and the more interesting result; it would be
reported as such, verified, and the mark recorded as missed.

## 4. Controls

* S5 is the control for S6: the same search, the same budget, on lengths
  where a tag is known to exist.
* The ranks of the control's finds are reported: a 15-bit tag of rank above
  seven would show that the gap is not covered by the built-on-seven proof's
  shape alone.

## 5. What this round does not do

* It does not prove that the gap is empty: S6 is a search, and a positive
  deficit is a failure to find, never a proof of absence.
* It does not change the tags in use, the carrier read or any answer the
  evaluation pins.
* It does not take the other parts of "The designed substrate, the rest"
  (a soft reading the GLM produces itself; the cited substrate results).

## 6. Files

| file | what |
|---|---|
| `overlay/glm_lean/RequestProject/GLM/ShortestTag.lean` | §1 |
| `overlay/glm_universal/reasoning/shortest_tag.py` | the floors, the census, the search, `shortest_tag_report` |
| `overlay/glm_universal/tests/test_shortest_tag.py` | the tests |
| `overlay/glm_universal/tools.py` | `tools shortest-tag` |

## 7. The measurement

`PYTHONPATH=. python3 -m glm_universal.tools shortest-tag` (about nine
minutes, one process; `--moves` lowers the search budget);
`tests/test_shortest_tag.py` pins every figure below except the gap search,
which is the tool's.

### 7.1 The verdict

The seven-bit sender tag is proved to be the shortest tag that resolves every tie, and the eleven- and fifteen-bit protected tags are proved to be the shortest tags built as parities of seven tag bits. Every parity tag whose octad tags have weight at least D needs at least D + 6 bits, so 9 and 11 bits is the proved floor for tags of any other shape. The gap between the floors is searched, not settled: the search found no shorter tag at any gap length, but its control found the 15-bit length on none of three seeds, so for two flipped bits the empty search is weak evidence. Five of six marks were met; S5 was missed on that control.

### 7.2 The marks

| mark | measured | met |
|---|---|---|
| **S1** | `ShortestTag.lean` builds (`lake build RequestProject.GLM.ShortestTag`), no `sorry`, all 19 theorems of `LEAN_THEOREMS` present; `#print axioms` on `tag_length_floor`, `tag7_shortest`, `protected_tag_floors`, `built_tag_floor` and `protected_tags_shortest_of_shape` gives `propext`, `Classical.choice`, `Quot.sound` and the axioms of `native_decide` (the octad checks of Phases 133–134 and the two column checks `tag11_built`, `tag15_built`); `no_14_7_5` uses only the three standard axioms | yes |
| **S2** | least octad weight 1, 3, 5 at 7, 11, 15 bits; both protected tags are parities of the seven tag bits, with selector rows equal to `selRows11` and `selRows15` in the Lean file | yes |
| **S3** | the seven-bit tag's kernel on the code: 32 codewords of weights 0, 12 and 16, no octad; at most 16 avoid any one coordinate (the Plotkin cap is 24) | yes |
| **S4** | all 127 nonzero values of the seven-bit tag are taken by octads, each by 3 or 6 of them; zero is not taken | yes |
| **S5** | control, 2,000,000 proposals × seeds 1, 2, 3: 7 bits for `D = 1` found by 3 of 3 seeds, 11 bits for `D = 3` by 2 of 3, 15 bits for `D = 5` by **0 of 3** | **no** |
| **S6** | gap, same budget, least deficit over the three seeds: `D = 3` — 35 at 9 bits, 9 at 10 bits; `D = 5` — 179, 99, 45, 15 at 11, 12, 13, 14 bits | yes |

### 7.3 Controls

* **S5 against S6.** For `D = 3` the control works (the 11-bit length is
  found by two seeds of three), so the 10-bit search ending at deficit 9 is
  evidence, though not proof, that ten bits do not suffice. For `D = 5` the
  same search never reaches the 15-bit length a construction shows possible,
  so its failure at 11–14 bits says little about those lengths. The mark is
  missed as declared; the search is not re-tuned after the fact.
* **The shape of what the search finds.** Every tag the control found has
  functionals of rank exactly 7 (the three 7-bit finds and the two 11-bit
  finds) — tags of the
  shape the built-on-seven floor covers. This is reported, not claimed: it
  is a property of what one search reached.
* **The Plotkin step is not tight here.** S3 shows the seven-bit tag's kernel
  has at most 16 words avoiding a coordinate, against the proved cap of 24;
  the floor `r ≥ D + 6` uses the cap, which is why it stays below the coding
  bounds.

### 7.4 What it answers

The three tags the GLM uses are no longer just constructions: the seven-bit
tag is proved minimal among all parity tags, and the two protected tags are
proved minimal among tags of their own shape (parities of seven tag bits),
with the `[14, 7, 5]` code's non-existence proved in the development itself
rather than quoted from tables. Under directive D15 the round moves
**derivation** — the length a tag needs is now computed from proved bounds
rather than chosen — and reports its own limit plainly: a tag of another
shape in the gap is neither found nor excluded.

### 7.5 What this round leaves

* **The gap between the floors.** Nine or ten bits for one flipped tag bit,
  eleven to fourteen for two, for tags whose functionals span more than seven
  dimensions. A proof would need more than the Plotkin step (its cap is not
  tight, S3); an exhaustive search would need the code's symmetry group to be
  feasible. The search here is weak for two flipped bits (S5).
* **A stronger search**, one whose control reaches 15 bits, before the
  `D = 5` gap result is quoted as evidence.
* The other parts of "The designed substrate, the rest" are unchanged: a soft
  reading the GLM produces itself, a guard of the carrier read's own, and the
  substrate study's cited results.
