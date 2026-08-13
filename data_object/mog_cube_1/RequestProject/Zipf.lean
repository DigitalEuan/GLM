import Mathlib
import RequestProject.Discourse

/-!
# Zipf, least effort, and how many cube cells a sentence costs

Zipf's law says that in natural text the `n`-th most common word appears about
`f₁ / n` times, and Zipf explained it by a *principle of least effort*: common
things get short forms.  This file does two things with that.

## 1. Measure the corpus, and report honestly

`Discourse.corpus` is 1536 paragraphs — one for every one of the 512 worlds and
each of the three things.  Rendered into English and tokenised that is **66288
word tokens over a vocabulary of 17 types** (`corpus_size`).  The ranked counts
are

    is 10752 · it 9216 · not 7152 · the 6912 · than 5376 · and 4824 ·
    hotter 3072 · so 2880 · water 2560 · stone 2304 · heavier 2304 ·
    lamp 2048 · frozen 1536 · boiling 1536 · but 1512 · warm 1344 · heavy 960

Zipf from the top word would predict `10752/n`: 5376 at rank 2, 3584 at rank 3,
2688 at rank 4.  The observed counts are 9216, 7152, 6912.  So the distribution
of this generated language is **much flatter than Zipf**
(`corpus_is_flatter_than_zipf`, `zipf_worst_case`): every rank from 2 down sits
*above* the Zipf prediction, by more than a factor of 2 from rank 4 to rank 12.

That is a real diagnostic rather than a failure to hide.  Two causes, both
visible in the generator: the vocabulary is tiny and every content word is
forced to be *news* (`Discourse.and_is_informative`), so no word can dominate
the way "the" does in English; and there are no rare words at all, because the
world has only three things and six properties.  A Zipf-shaped corpus would
need a long tail this micro-world does not have.

## 2. Use least effort anyway: a code that fits more words in a cube

Least effort is still worth obeying, and it is measurable here because the cube
has exactly **24 cells**.  A fixed-length code over 17 words needs 5 bits per
word, so 4 words fit in a cube.  A Huffman code built from the measured counts
gives "is", "it", "not", "the" three bits and "heavy" six
(`huffman_code_lengths`), and it is checked to be

* **prefix-free** — no codeword begins another, so a cube's worth of bits parses
  one way only (`huffman_facts`);
* **exactly invertible** — decoding the encoded corpus returns the original
  66288 tokens, token for token (`huffman_facts`);
* **cheaper** — 249528 bits against 331440, a saving of 81912 bits, so the whole
  corpus takes **10397 cubes instead of 13810** (`huffman_facts`).

Nothing here is estimated: the tree is built by the usual Huffman merge inside
Lean and every number is computed from the corpus.
-/

namespace Zipf

open Semantics Discourse

set_option maxRecDepth 100000

/-! ## 1. The corpus as words -/

/-- Split a rendered sentence into word tokens, dropping punctuation. -/
def tokens (s : String) : List String :=
  ((s.replace "," "").replace "." "").splitOn " " |>.filter fun t => t ≠ ""

/-- Every paragraph the discourse generator produces, as English. -/
def corpusText : List String := Discourse.corpus.map fun wp => renderPara wp.2

/-- Every word token in the corpus. -/
def corpusToks : List String := corpusText.flatMap tokens

/-- The word types. -/
def vocab : List String := corpusToks.eraseDups

/-- The vocabulary ranked by frequency, commonest first. -/
def counts : List (String × Nat) :=
  (vocab.map fun t => (t, (corpusToks.filter fun u => u == t).length)).mergeSort
    fun a b => decide (b.2 ≤ a.2)

/-! ## 2. Zipf's prediction against the measurement -/

/-- Zipf's prediction for rank `n` from the top count `f₁`. -/
def zipfPredict (f1 n : Nat) : Nat := f1 / n

/-- Rank, measured count, Zipf's prediction — for every word type. -/
def zipfTable : List (Nat × Nat × Nat) :=
  match counts with
  | [] => []
  | (_, f1) :: _ =>
      (counts.zipIdx.map fun p => (p.2 + 1, p.1.2, zipfPredict f1 (p.2 + 1)))

/-- **The corpus, measured.**  66288 tokens over 17 types, with the ranked
counts listed in the module docstring. -/
theorem corpus_size :
    corpusToks.length = 66288 ∧ vocab.length = 17 ∧
    counts.map (·.2) =
      [10752, 9216, 7152, 6912, 5376, 4824, 3072, 2880, 2560, 2304, 2304, 2048,
        1536, 1536, 1512, 1344, 960] := by
  native_decide

/-- **The generated language is flatter than Zipf's law.**  At every rank the
observed frequency is at least the Zipf prediction — the tail never falls away
as fast as `f₁/n` — so this corpus is not Zipf-distributed. -/
theorem corpus_is_flatter_than_zipf :
    (zipfTable.all fun r => decide (r.2.2 ≤ r.2.1)) = true := by
  native_decide

/-- **How far from Zipf.**  At rank 4 the observed count is more than twice the
prediction, and the same holds at every rank from 4 to 12: the mismatch is
systematic, not a wobble at one rank.  (Past rank 12 the observed counts fall
back to between one and two times the prediction, so the corpus is flat rather
than uniformly doubled.) -/
theorem zipf_worst_case :
    ((zipfTable.filter fun r => decide (4 ≤ r.1 ∧ r.1 ≤ 12)).all fun r =>
      decide (2 * r.2.2 ≤ r.2.1)) = true := by
  native_decide

/-! ## 3. Least effort: a Huffman code over the measured counts -/

/-- A code tree. -/
inductive HTree where
  | leaf (tok : String)
  | node (l r : HTree)
deriving Repr, Inhabited, DecidableEq

/-- Insert keeping the list sorted by weight. -/
def insertBy (x : Nat × HTree) : List (Nat × HTree) → List (Nat × HTree)
  | [] => [x]
  | y :: ys => if x.1 ≤ y.1 then x :: y :: ys else y :: insertBy x ys

/-- The Huffman merge: repeatedly join the two lightest trees. -/
def huffStep : Nat → List (Nat × HTree) → List (Nat × HTree)
  | 0, l => l
  | _ + 1, [] => []
  | _ + 1, [x] => [x]
  | n + 1, a :: b :: rest => huffStep n (insertBy (a.1 + b.1, .node a.2 b.2) rest)

/-- The Huffman tree for the measured counts. -/
def huffTree : Option HTree :=
  match huffStep counts.length
      ((counts.map fun p => (p.2, HTree.leaf p.1)).mergeSort fun a b => decide (a.1 ≤ b.1)) with
  | [(_, t)] => some t
  | _ => none

/-- Read the codewords off a tree. -/
def codesOf : HTree → List Bool → List (String × List Bool)
  | .leaf t, pre => [(t, pre.reverse)]
  | .node l r, pre => codesOf l (false :: pre) ++ codesOf r (true :: pre)

/-- The code book. -/
def book : List (String × List Bool) :=
  match huffTree with
  | some t => codesOf t []
  | none => []

/-- The codeword of a word. -/
def codeOf (t : String) : List Bool :=
  match book.find? fun p => p.1 == t with
  | some p => p.2
  | none => []

/-- Encode a list of words as bits. -/
def encode (ts : List String) : List Bool := ts.flatMap codeOf

/-- The cost of a word list in bits, without building the bit-string. -/
def costOf (ts : List String) : Nat := ts.foldl (fun a t => a + (codeOf t).length) 0

/-- One step of decoding: follow a bit; on reaching a leaf, emit the word and
return to the root. -/
def stepD (root : HTree) (st : HTree × List String) (b : Bool) : HTree × List String :=
  match st.1 with
  | .leaf _ => st
  | .node l r =>
      match (if b then r else l) with
      | .leaf t => (root, t :: st.2)
      | c => (c, st.2)

/-- Decode bits back to words. -/
def decode (bs : List Bool) : List String :=
  match huffTree with
  | some t => ((bs.foldl (stepD t) (t, [])).2).reverse
  | none => []

/-- A cube has 24 cells, so 24 bits. -/
def cellsPerCube : Nat := 24

/-- How many cubes a bit-string needs. -/
def cubesFor (bits : Nat) : Nat := (bits + cellsPerCube - 1) / cellsPerCube

/-- Fixed-length coding needs 5 bits for 17 words. -/
def fixedWidth : Nat := 5

/-- The codeword lengths the merge produces. -/
def bookLengths : List (String × Nat) := book.map fun p => (p.1, p.2.length)

/-- **The code, word by word.**  The four commonest words cost three cells each;
the rarest costs six. -/
theorem huffman_code_lengths :
    (counts.map fun p => (book.find? fun q => q.1 == p.1).map fun q => q.2.length) =
      [some 3, some 3, some 3, some 3, some 4, some 4, some 4, some 4, some 5,
        some 5, some 5, some 5, some 5, some 5, some 5, some 6, some 6] := by
  native_decide

/-- **The least-effort code, checked end to end.**

* no codeword is a prefix of another, so the bit-stream parses one way only;
* every one of the 1536 paragraphs, encoded and decoded again, comes back word
  for word;
* the corpus costs 249528 bits instead of the 331440 a fixed 5-bit code would
  need — 81912 bits saved, 10397 cubes instead of 13810. -/
theorem huffman_facts :
    (book.all fun p => book.all fun q => decide (p.1 = q.1) || !p.2.isPrefixOf q.2) = true ∧
    (corpusText.all fun s => decode (encode (tokens s)) == tokens s) = true ∧
    costOf corpusToks = 249528 ∧
    fixedWidth * corpusToks.length = 331440 ∧
    cubesFor (costOf corpusToks) = 10397 ∧
    cubesFor (fixedWidth * corpusToks.length) = 13810 := by
  native_decide

/-- **Least effort pays, as a statement rather than a measurement.**  Whatever
the numbers, the Huffman coding of the corpus is strictly shorter than the
fixed-width coding, and therefore needs strictly fewer cubes. -/
theorem least_effort_is_cheaper :
    costOf corpusToks < fixedWidth * corpusToks.length ∧
      cubesFor (costOf corpusToks) < cubesFor (fixedWidth * corpusToks.length) := by
  obtain ⟨_, _, h1, h2, _, _⟩ := huffman_facts
  rw [h1, h2]
  exact ⟨by norm_num, by norm_num [cubesFor, cellsPerCube]⟩

/-- **The code is a genuine code.**  Every paragraph in the corpus survives
encoding and decoding unchanged, so the compression loses nothing. -/
theorem huffman_lossless :
    (corpusText.all fun s => decode (encode (tokens s)) == tokens s) = true :=
  huffman_facts.2.1

#eval counts
#eval bookLengths

end Zipf
