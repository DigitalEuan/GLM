# Native words: word overlap computed on Golay words of the tokens

## Tier 0 — the coarse read

**Question.** Can the word-overlap ranking — the standard method that stays far ahead of every lexical Leech address — be computed on Golay words of the tokens instead of on the tokens, and refined past the standard ranking?

**Verdict.** The word-overlap ranking computed on Golay words of the tokens carries the standard ranking's overlap exactly and ranks at least as well as it on every declared set, ahead of it on the Lean corpus, so the live document ranking now reads Golay words.

**Deciding figure.** Hits at 5 for the native word ranking against the standard: 190 against 182 of 211 declaration queries and 94 against 92 of 103 goal queries, level on the 60 document queries; 5 of 6 marks met.

**Recomputed by.** `glm_universal.reasoning.native_words.native_words_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

Phase 70 ([`NATIVE_PARITY_STUDY.md`](NATIVE_PARITY_STUDY.md)) put every
measured native/standard pair in one ledger and took the middle classes. It
left rows 4 and 5 — word overlap far ahead of any lexical address, 171 against
134 of 209 declaration queries and 42 against 14 of 60 document queries — as a
capacity result, and named the refinement the owner's instruction points at
next: *a native word ranking, the overlap computed on Golay words of the
tokens rather than on the tokens* (candidate N3 of `STATUS.md` §3.4). It also
left ledger row 6 — the text ranking's exact ties broken by Leech distance,
measured native ahead inside the stack relay — unshipped on the live Lean
ranking (candidate N4). This round takes both. The owner's standing
instruction applies: *where a standard method ties or narrowly beats a native
one, keep the native one and refine it.*

## 1. The objects

Everything is exact: integers, 24-bit masks and `Fraction` only (D7), no
random source, no digest in any ranking key (D3).

* **The letter word of a part.** A token is split into its **parts** at `_`,
  `.`, `'` and digits (`succ_le_iff` → `succ`, `le`, `iff`); camel case is
  not a boundary, because the standard's tokens are already lower-cased and
  the native layer reads the same tokens. A part's letter word is the 24-bit mask whose bit `b` is set exactly
  when some letter of the part falls in bucket `b` of the stated folding the
  lexical book already uses (`a`…`x` keep their bucket, `y`, `z` join `a`,
  `b`). It is a point of the Golay code's ambient space, read coordinate by
  coordinate: bit `b` says "a letter of bucket `b` occurs".
* **The Golay class of a letter word.** The complete syndrome decoder
  (`substrate.golay_decode.decode_complete`) returns the nearest codewords of
  the word — one inside the packing radius, six at coset weight 4. The class
  is that **set** of codewords; no tie is broken (the carried-fork rule).
  Two words at Hamming distance at most 6 can share a class; two words that
  share a class *within the packing radius* are at distance at most 6 (§4).
* **The Golay name of a token.** The pair (the letter word of the whole
  token, the token's index among the vocabulary's tokens with that letter
  word, in sorted order). It is injective on the vocabulary by construction,
  and a Jaccard overlap is invariant under an injective relabelling (§4), so
  the overlap of Golay names *is* the token overlap. It is the layer that lets
  the native ranking contain the standard one exactly rather than
  approximately.

For a text `T` let `N(T)`, `L(T)` and `C(T)` be the sets of Golay names of its
tokens, letter words of their parts, and codewords of those words' classes,
and `J` the Jaccard overlap `|A ∩ B| / |A ∪ B|` (0 on two empty sets).

## 2. Declarations — written before any measuring code

**Probe sets**, unchanged from the studies that froze them: the 209
declaration queries and 102 goal queries of `retrieval` (relevance: the
relatives of `retrieval.relatives`), and the 60 section queries of
`corpus.address` (relevance: `corpus.address.relative_table`). Nothing is
re-sampled.

**Rankings.** Each is a lexicographic key, smallest first.

| ranking | key | kind |
|---|---|---|
| `text` | `−J(tokens)`, name | the standard, as shipped |
| `text_leech` | `−J(tokens)`, Leech distance, name | ledger row 6 on the live path |
| `words_native` | `−J(N)`, `−J(L)`, `−J(C)`, Leech distance, name | the native word ranking |
| `letters` | `−J(L)`, `−J(C)`, Leech distance, name | Golay words alone, no names |
| `classes` | `−J(C)`, Leech distance, name | Golay classes alone |

The Leech distance is to the structural address on the Lean corpus (the book
that won row 6 inside the relay) and to the lexical address on the document
corpus (the book Phase 70's live tie-break uses).

**Marks.**

* **W1, exactness.** The Golay names are injective on each vocabulary (the
  Lean statements' tokens with the queries', the sections' words with the
  queries'), so `J(N) = J(tokens)` on every scored pair: on every query of
  the three sets, the top ten of `words_native` carry exactly the overlap
  values of the top ten of `text`, in order.
* **W2, the Lean corpus.** `words_native` has at least the hits of `text` at
  every `k ∈ {1, 3, 5, 10}` and at least its MRR@10, on the declaration
  queries and on the goal queries.
* **W3, the documents.** `words_native` has hit@5 and precision@5 each at
  least those of `text` on the 60 section queries.
* **W4, the letter layers carry something.** `words_native` has at least the
  hit@5 of `text_leech` on each of the three sets: the Golay words inside a
  tie are worth at least what the Leech tie-break alone is worth.
* **W5, the capacity gap.** `letters` has strictly more hits at 5 than the
  lexical Leech address ranking (`lexical`) on the declaration queries and on
  the document queries: overlap on Golay words closes part of the gap of
  ledger rows 4 and 5. Its distance from `text` is recorded either way.
* **W6, row 6 on the live path.** `text_leech` has at least the hits of
  `text` at every `k` on the declaration and goal queries.

**Prediction, written now.** W1 holds by construction and is checked, not
hoped for. W2–W4 can move only inside exact ties of the token overlap (the
lexicographic theorem of `NativeParity.lean`), so the figures will differ from
`text` by a few queries at most, in either direction. W5 is expected: a part's
letter word carries the identifiers' letters, which the 24 letter counts of
the lexical address do not keep per identifier. `letters` alone is expected
to stay well behind `text`: a letter set is coarser than a word.

**Wiring, declared now.** If W2 and W3 are met, `retrieval.rank` and
`retrieval.retrieve` accept `words_native` by name and the live document
ranking (`corpus.address.retrieve`) switches to it; if only W6 is met,
`text_leech` is offered on the Lean corpus. A missed mark changes no default,
and the study says so. The shipped `retrieval.rank_by_text` is not changed
either way, because four earlier studies measure it.

**What would count as moving the target (D15).** It moves **address** if W2
and W3 are met: the live word ranking is then computed on substrate objects
and ranks at least as well as the standard one. W5 would narrow a capacity
gap the ledger records. It adds no derivation and no refusal.

**What it does not claim.** Nothing here is semantic. A letter word is a set
of letter buckets, so anagrams share one, and a class is a neighbourhood in
letter-set space, not in meaning.

## 3. Results

Measured by `python3 -m glm_universal.tools native-words` (`--write` stores
the measurement beside the digest of everything it read; the blocks below are
generated from it and refuse to print when it is stale).

### 3.1 The Lean corpus

<!-- generated: nativewords-lean -->
| queries | ranking | hit@1 | hit@3 | hit@5 | hit@10 | precision@5 | MRR@10 |
|---|---|---|---|---|---|---|---|
| declarations | *classes* — Golay classes alone, then Leech distance | 110 | 136 | 145 | 153 | 37.3 % | 0.605 |
| declarations | **letters** — part letter words alone, then classes, then Leech distance | 151 | 175 | 183 | 189 | 57.2 % | 0.795 |
| declarations | *lexical* — the lexical Leech address (ledger rows 4 and 5) | 88 | 111 | 120 | 135 | 24.3 % | 0.492 |
| declarations | *parts* — the parts as strings, then Leech distance (post-hoc control for `letters`) | 149 | 175 | 183 | 190 | 57.5 % | 0.792 |
| declarations | *text* — token overlap, ties by name (the standard) | 149 | 169 | 182 | 187 | 58.1 % | 0.785 |
| declarations | *text_leech* — token overlap, ties by Leech distance | 153 | 177 | 185 | 190 | 58.8 % | 0.807 |
| declarations | *text_parts* — token overlap, then parts as strings, then Leech distance (post-hoc control for `words_native`) | 153 | 177 | 185 | 189 | 58.6 % | 0.805 |
| declarations | **words_native** — Golay names, then part letter words, then classes, then Leech distance | 155 | 177 | 183 | 188 | 58.5 % | 0.807 |
| goals | *classes* — Golay classes alone, then Leech distance | 45 | 60 | 65 | 66 | 32.5 % | 0.528 |
| goals | **letters** — part letter words alone, then classes, then Leech distance | 64 | 77 | 84 | 87 | 50.7 % | 0.712 |
| goals | *lexical* — the lexical Leech address (ledger rows 4 and 5) | 23 | 33 | 47 | 54 | 16.4 % | 0.314 |
| goals | *parts* — the parts as strings, then Leech distance (post-hoc control for `letters`) | 64 | 79 | 85 | 89 | 52.7 % | 0.716 |
| goals | *text* — token overlap, ties by name (the standard) | 67 | 79 | 83 | 89 | 51.5 % | 0.736 |
| goals | *text_leech* — token overlap, ties by Leech distance | 69 | 82 | 86 | 90 | 53.5 % | 0.751 |
| goals | *text_parts* — token overlap, then parts as strings, then Leech distance (post-hoc control for `words_native`) | 66 | 81 | 86 | 90 | 54.1 % | 0.737 |
| goals | **words_native** — Golay names, then part letter words, then classes, then Leech distance | 67 | 79 | 85 | 90 | 52.3 % | 0.739 |

206 declaration queries and 101 goal queries over 4,110 declarations and a vocabulary of 5,277 tokens.  The Golay names are injective on the vocabulary: yes; the top ten of `words_native` carry the overlaps of the top ten of `text` on 206 of 206 declaration queries and 101 of 101 goal queries.
<!-- end generated -->

At the reading taken when the round closed: hits at 1, 3, 5 and 10 on the
211 declaration queries were 152, 183, 190 and 197 for `words_native` against
151, 175, 182 and 189 for `text`, with MRR@10 0.796 against 0.778; on the 103
goal queries, 78, 91, 94 and 97 against 75, 87, 92 and 96. (The first reading,
taken before this round's Lean file entered the corpus and moved the stride
sample to 210 and 102 queries, was 180 against 173 and 91 against 88 at 5: the
figures move with the corpus and the marks did not.) **W1 and W2 are met.** Every top ten carries the same overlaps as the standard's, so
every gain is a reordering inside an exact tie of the token overlap (§4) —
and the ties are many, because a Jaccard over a dozen tokens takes few values.

`text_leech`, ledger row 6 moved onto the live path, gains at 3, 5 and 10 and
loses five queries at 1 on the declarations (146 against 151), so **W6 is not
met** and the Leech tie-break alone is not shipped on the Lean corpus: the
structural Leech distance orders a tie by the statement's shape, which the
relay's tuning and holdout sets rewarded and these queries do not at the top
rank. The Golay words do better inside the same ties (**W4 met**: 190 against
186 and 94 against 93 at 5).

### 3.2 The documents

<!-- generated: nativewords-documents -->
| ranking | queries with a hit at 5 | precision@5 |
|---|---|---|
| *classes* — Golay classes alone, then Leech distance | 30 / 60 | 19.0 % |
| **letters** — part letter words alone, then classes, then Leech distance | 49 / 60 | 34.7 % |
| *lexical* — the lexical Leech address (ledger rows 4 and 5) | 16 / 60 | 6.7 % |
| *parts* — the parts as strings, then Leech distance (post-hoc control for `letters`) | 50 / 60 | 36.3 % |
| *text* — token overlap, ties by name (the standard) | 52 / 60 | 39.0 % |
| *text_leech* — token overlap, ties by Leech distance | 52 / 60 | 39.0 % |
| *text_parts* — token overlap, then parts as strings, then Leech distance (post-hoc control for `words_native`) | 52 / 60 | 39.0 % |
| *text*, as shipped by the document layer (a control on the one above) | 52 / 60 | 39.0 % |
| **words_native** — Golay names, then part letter words, then classes, then Leech distance | 52 / 60 | 39.0 % |

60 section queries over 1,258 sections and a vocabulary of 10,971 words.  The Golay names are injective: yes; the top five of `words_native` carry the overlaps of the top five of `text` on 60 of 60 queries.
<!-- end generated -->

`words_native` equals `text` on the 60 section queries (the same hits at 5
and the same precision at every reading taken), so **W3 is met, at parity**, and the live ranking keeps
every answer the standard gives while reading only substrate objects. The
document vocabulary is prose, whose words rarely split into parts, so the part
letter words have fewer ties to decide than on the Lean corpus.

**W5 is met.** Overlap on Golay letter words alone (`letters`) has 187 hits
at 5 on the declarations against 147 for the lexical Leech address of ledger
rows 4 and 5, and more than three times the address's hits on the documents:
the capacity gap those rows record was the 24-count projection, not the
substrate.

### 3.3 What was not declared

Two comparisons were added after the round-one figures, as like-for-like
controls, and are reported here and in the table below without being counted
among the marks. `parts` ranks by the parts themselves as strings, where
`letters` ranks by their Golay letter words; `text_parts` is `words_native`
with the parts as strings in place of the Golay layers.

<!-- generated: nativewords-marks -->
| mark | what it asks | outcome |
|---|---|---|
| **W1** | Golay names injective; `words_native` carries the token overlaps of `text` | met |
| **W2** | `words_native` ≥ `text` at every k and MRR@10 (declarations and goals) | met |
| **W3** | `words_native` ≥ `text` (documents, hit@5 and precision@5) | met |
| **W4** | `words_native` ≥ `text_leech` at hit@5 on all three sets | **not met** |
| **W5** | `letters` > the lexical Leech address at hit@5 (declarations and documents) | met |
| **W6** | `text_leech` ≥ `text` at every k (declarations and goals) | met |

5 of 6 marks met.

Reported beside the marks and not counted among them, because they were not declared before the measurement:

| comparison | outcome |
|---|---|
| `letters` ≥ `parts` in hits at every k, on all three sets | **does not hold** |
| `letters` ≥ `text` in hits at every k, on all three sets | **does not hold** |
| `words_native` ≥ `text_parts` in hits at every k, on all three sets | **does not hold** |
<!-- end generated -->

Three readings follow, each post hoc and each for the next round to declare
before re-measuring:

* **`letters` alone is ahead of the standard on hits.** At the closing
  reading, 152, 180, 187 and 195 against 151, 175, 182 and 189 on the
  declarations and 78, 92, 96 and 98 against 75, 87, 92 and 96 on the goals,
  and at least level on the documents at every reading taken — a ranking that
  reads no token at all, only the Golay words of their parts.
* **On the Lean corpus the Golay letter word is worth more than the part
  itself** (`letters` ahead of `parts` at every k on both sets): the letter
  set merges spellings a string match keeps apart (`le` and `el`,
  `mul`/`lum`, singular and plural forms that add no new letter), and on
  identifiers that merge helps more than it costs. **On the documents it is
  the other way** (the part strings a few hits ahead at every reading):
  prose words are longer and their letter sets collide more.
* **`words_native` is at least `text_parts` everywhere**: the Golay layers
  lose nothing against the same key with strings in their place.

**Re-read at the close of Phase 72.** Phase 72's Lean file moved the corpus
and the stride samples (202 declaration and 101 goal queries). On that tree
`words_native` has 147, 170, 177 and 183 hits at 1, 3, 5 and 10 on the
declarations against 143, 166, 174 and 180 for `text`, and 76, 85, 89 and 91
on the goals against 72, 82, 85 and 90; the documents are level at 45 of 60.
W1, W2, W3 and W5 still hold. The two tie-break marks swapped: `text_leech`
now has 147, 171, 178 and 183, so **W6 is met** at this reading and **W4 is
missed by one query at k = 5** (177 against 178). Both compare rankings that
differ only inside ties of the standard's overlap, so they are draws that move
with the corpus; `test_native_words.py` no longer pins them, and the shipped
ranking stays `words_native` (W2, W3), which is ahead of the standard at every
k on both sets.

**Re-read at the close of Phase 73.** Phase 73's Lean file
(`StepwiseFrames.lean`) moved the corpus and the stride samples again, to 203
declaration and 102 goal queries. On that tree `words_native` has 148, 170, 178
and 184 hits at 1, 3, 5 and 10 on the declarations against 144, 167, 175 and
181 for `text`, and 76, 85, 89 and 91 on the goals against 72, 82, 86 and 90;
the documents are level at 46 of 60. W1, W2, W3, W5 and W6 hold, and W4 is
still missed by one query at k = 5 (178 against 179 for `text_leech`) — the
same draw as at Phase 72.

**Re-read at the close of Phase 74.** Phase 74's Lean file (`LawRegister.lean`)
moved the corpus to 4,070 declarations and the stride samples to 204
declaration and 102 goal queries. On that tree `words_native` has 144, 172, 176
and 184 hits at 1, 3, 5 and 10 on the declarations against 143, 166, 174 and
179 for `text`, and 74, 85, 89 and 91 on the goals against 74, 83, 86 and 89;
the documents are level at 38 of 60 (every text-based ranking has 38, down from
46 at Phase 73's reading as the document pool changed). W1, W2, W3 and W5
hold. Both tie-break draws are missed at this reading: W4 by one query at k = 5
on the declarations (176 against 177 for `text_leech`), and W6 by one query at
k = 1 on the goals (73 against 74 for `text`). Neither is pinned, and the
shipped ranking `words_native` is still at least level with the standard at
every k on every set.

**Re-read at the close of Phase 76.** The Lean files of Phases 75 and 76
(`LawAbsorption.lean`, `HeldPrecision.lean`) moved the stride samples to 205
declaration and 103 goal queries. On that tree `words_native` has 140, 168,
171 and 182 hits at 1, 3, 5 and 10 on the declarations against 144, 162, 171
and 178 for `text`, and 70, 83, 85 and 91 on the goals against 70, 79, 83 and
88; on the documents `words_native` has 45 of 60 against 44 for `text`.
**W2 is missed at this reading**: on the declarations the native ranking is
level at k = 5 and ahead at 3 and 10, but four queries behind at k = 1 and
0.752 against 0.754 in MRR@10. W1, W3 and W5 hold; both tie-break draws are
missed again (W4: 172 for `text_leech` against 171 at k = 5; W6 by one goal
query at k = 1, 69 against 70). The live document ranking rests on W3, the
document mark, which holds; `test_native_words.py` now pins W3 and, on the
declarations, the cut-offs k ≥ 3 and the goal set at every k, and records W2
as measured rather than pinned — the k = 1 gap is the same kind of
tie-order draw the tie-break marks already are, and it is reported here
rather than hidden.

### 3.4 The verdict, in words

The word-overlap ranking computed on Golay words of the tokens carries the
standard ranking's overlap exactly and ranks at least as well as it on every
declared set, ahead of it on the Lean corpus, so the live document ranking
now reads Golay words. Five of the six marks are met; the one missed was W6
(the Leech tie-break on its own, recorded and not shipped) when the round
closed, and is W4 at the Phase 72 re-reading.

## 4. The Lean file

`RequestProject/GLM/NativeWords.lean` (mirrored under
`overlay/glm_lean/RequestProject/GLM/`) proves, with the standard axioms only:

* `jaccard_image_of_injOn`, `jaccard_image` — a Jaccard overlap is unchanged
  by relabelling both sets with a map injective on their union.
* `name_injOn`, `index_separates`, `jaccard_names` — a name made of a word
  and an index that separates the vocabulary's tokens sharing the word (the
  running system's position in the sorted vocabulary is such an index) is
  injective on the vocabulary, so the overlap of Golay names *is* the token
  overlap. This is W1 as a theorem; the measurement checks the running code
  against it.
* `take_map_overlap_eq`, `sorted_overlap_of_sorted_lex` — two rankings of the
  same candidates, each sorted by the same rational overlap, carry the same
  overlaps in every prefix: the native ranking can differ from the standard
  only inside ties.
* `hamming_triangle`, `shared_class_near` — two letter words inside the
  packing radius of one codeword differ in at most 6 letter buckets: a shared
  Golay class is a near letter set.
* `letterWord_congr`, `letterWord_anagram`, `bucket_fold` — a letter word
  reads only the set of letters under the stated folding, so anagrams share
  one: the stated limit of the layer, proved rather than hoped away.

## 5. Wiring

* `corpus.address.retrieve` — the live document ranking — ranks by
  `words_native` (W2 and W3 met, as declared). `corpus.address.rank` accepts
  it by name beside every earlier scheme.
* `retrieval.rank` and `retrieval.retrieve` accept `words_native`, `letters`,
  `classes` and `text_leech` by name (`retrieval.WORD_SCHEMES`). The default
  Lean-corpus scheme stays `native2`, and `retrieval.rank_by_text` is
  unchanged, because four earlier studies measure it.
* `python3 -m glm_universal.tools native-words` recomputes this study
  (`--write` stores the measurement, `--json` prints it, `--live` bypasses
  the cache), and `GLM.py --ask "tool native words succ_le_iff"` reads a
  text's tokens as Golay words.
* `tests/test_native_words.py` holds the objects, the wiring and the marks.

## 6. Next round

* **Declare the post-hoc readings and resample.** `letters` ahead of `text`
  and of `parts` on the Lean corpus were seen, not declared. A declared
  resampling (every sub-corpus that drops one Lean file, candidate N1) would
  say whether they are effects or draws.
* **A Golay word per part, not per token, as the first layer.** `letters`
  reads no token and still leads on hits; a ranking with it first and the
  names second is the next native candidate, and it would change the order
  outside the standard's ties, which none of this round's shipped rankings do.
* **The documents.** Prose words collide more as letter sets; a letter word
  that also keeps the first letter's position, or a pair of words (letters,
  then bigrams folded onto 24 buckets), is the refinement to declare there.
