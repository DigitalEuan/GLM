import Mathlib
import RequestProject.WideWorld
import RequestProject.Zipf

/-!
# Does a wider world give a Zipf tail?  Measured: yes, mostly

Report 3 §5.2 recorded that the generated corpus has **no tail, hence no
Zipf**, and §6 proposed the remedy:

> Widen the world (more things, more properties, ranges rather than four
> temperature steps) and re-measure the Zipf fit; that is the single change
> most likely to move the frequency curve.

`WideWorld.lean` supplies the wider world — twenty-four things, six properties,
three relations, a six-point temperature scale.  This file does the
re-measurement and reports the outcome.

## The two generators

* `neutralCorpus` — for each of 64 worlds and each of the 24 things, say the
  six property facts about it and three comparisons with its neighbours.
  Nothing is selected for: this is the wide world's version of the old
  generator.  13824 clauses, 79112 word tokens, 39 word types.
* `newsCorpus` — the same, but a fact is uttered **only when it is news**: only
  if it holds in fewer than half of the local configurations, so a hearer would
  not have guessed it.  Rarity is measured on the readings, not stipulated.
  5632 clauses, 35328 tokens, 38 types.

## The result

Take the Zipf prediction from the top count, `c₁ / r`, and call a rank a
*fit* when the observed count is within a factor of two of it either way.

* The narrow corpus of report 3 fits at **8 of its 17 ranks** (47%)
  (`narrow_band_count`).
* The wide corpus fits at **37 of its 39 ranks** (95%)
  (`zipf_band_counts`) — and the news-only corpus at 35 of 38 (92%).

So widening the world *did* move the frequency curve, and by a lot: the report's
guess was right.  What it did not do is make the head Zipfian.  The wide head
still sits **above** `c₁/r` at ranks 2 and 3 and then falls **below** it from
rank 4 on (`wide_head_crosses_zipf`) — the corpus overshoots the law at the top
and undershoots it in the shoulder, and only the long flat tail of 24
thing-names, each at 768 tokens, lands inside the band.

The honest reading: a wider world buys a tail, which is most of the Zipf fit by
rank count, but the *head* of a Zipf curve is made by unequal airtime between
words, and this generator still gives every thing exactly the same airtime.
Selecting for news changes which properties dominate the head — `heavier` and
`warm` rise, `not` collapses from rank 3 to rank 10 — without producing the
`1/r` shape either.
-/

namespace WideZipf

open WideWorld

set_option maxRecDepth 10000

/-! ## 1. The worlds -/

/-- A deterministic spread of 64 worlds over the twenty-four things. -/
def wideWorlds : List (World 24) :=
  (List.range 64).map fun k => fun e =>
    (⟨(7 * k + 5 * e.val + e.val * e.val) % 6, Nat.mod_lt _ (by norm_num)⟩,
     ⟨(3 * k + e.val) % 3, Nat.mod_lt _ (by norm_num)⟩)

/-- The neighbour of a thing, for comparisons. -/
def nb (e : Fin 24) (k : Nat) : Fin 24 := ⟨(e.val + k) % 24, Nat.mod_lt _ (by norm_num)⟩

/-- The clauses the generator considers about one thing. -/
def clausesAbout (e : Fin 24) : List (Atom 24) :=
  [.frozen e, .warm e, .hot e, .boiling e, .heavy e, .massive e,
   .hotter e (nb e 1), .heavier e (nb e 2), .sameTemp e (nb e 3)]

/-- Say a fact with the polarity that makes it true. -/
def sayTrue (a : Atom 24) (w : World 24) : Lit 24 := (a, evalAtom a w)

/-! ## 2. Two generators -/

/-- Everything, whether or not it is news. -/
def neutralPara (w : World 24) : List String :=
  (ents 24).flatMap fun e => (clausesAbout e).map fun a => render (sayTrue a w)

/-- How many of the local configurations of the mentioned things make a literal
true — the measured commonness of a fact. -/
def commonness (l : Lit 24) : Nat :=
  ((tuples (scope [l.1]).length).filter fun ls => evalLit l (assign (scope [l.1]) ls)).length

/-- News: true here, and true in fewer than half of the configurations. -/
def isNews (l : Lit 24) : Bool :=
  decide (2 * commonness l < (tuples (scope [l.1]).length).length)

/-- Only the news. -/
def newsPara (w : World 24) : List String :=
  (ents 24).flatMap fun e =>
    ((clausesAbout e).map fun a => sayTrue a w).filterMap fun l =>
      if isNews l then some (render l) else none

def neutralCorpus : List String := wideWorlds.flatMap neutralPara
def newsCorpus : List String := wideWorlds.flatMap newsPara

/-! ## 3. Counting -/

/-- Split a sentence into word tokens. -/
def tokens (s : String) : List String :=
  s.splitOn " " |>.filter fun t => t ≠ ""

def corpusToks (c : List String) : List String := c.flatMap tokens

/-- The word types of a corpus. -/
def types (c : List String) : List String := (corpusToks c).dedup

/-- The counts, largest first. -/
def ranked (c : List String) : List (String × Nat) :=
  let toks := corpusToks c
  let ts := toks.dedup
  let cs := ts.map fun t => (t, toks.count t)
  cs.mergeSort fun a b => b.2 ≤ a.2

/-- The count at a rank (1-based). -/
def freqAt (c : List String) (r : Nat) : Nat := ((ranked c).getD (r - 1) ("", 0)).2

/-! ## 4. The measurement -/

/-- **The wide corpora, measured.** -/
theorem corpus_sizes :
    neutralCorpus.length = 13824 ∧ (corpusToks neutralCorpus).length = 79112 ∧
    (types neutralCorpus).length = 39 ∧
    newsCorpus.length = 5632 ∧ (corpusToks newsCorpus).length = 35328 ∧
    (types newsCorpus).length = 38 := by
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_⟩ <;> native_decide

/-- **The head of the neutral corpus**, ranks 1–8. -/
theorem neutral_head :
    (List.range' 1 8).map (freqAt neutralCorpus) =
      [19968, 13824, 6920, 3072, 1536, 1536, 1536, 1536] := by native_decide

/-- **The head of the news-only corpus**, ranks 1–8.  Selecting for news
reshapes it: the comparison words and the rarer properties move up, and `not`
falls out of the head altogether. -/
theorem news_head :
    (List.range' 1 8).map (freqAt newsCorpus) =
      [10240, 5632, 1536, 1536, 1536, 1536, 1024, 528] := by native_decide

/-- **The flat tail.**  Every one of the 24 thing-names occurs 768 times, and
those are the last 24 ranks. -/
theorem tail_is_the_names :
    ((List.range' 16 24).map (freqAt neutralCorpus)).all (fun c => c = 768) = true ∧
    (types neutralCorpus).length = 39 := by
  constructor <;> native_decide

/-! ## 5. Against Zipf -/

/-- A rank *fits* Zipf when the observed count is within a factor of two of the
prediction `c₁ / r`, in either direction — stated with integer arithmetic so it
is decidable exactly. -/
def inBand (c : List String) (r : Nat) : Bool :=
  decide (freqAt c 1 ≤ 2 * r * freqAt c r) && decide (r * freqAt c r ≤ 2 * freqAt c 1)

def bandCount (c : List String) (n : Nat) : Nat :=
  ((List.range' 1 n).filter (inBand c)).length

/-- The narrow corpus of report 3, ranked, for comparison. -/
def narrowFreqAt (r : Nat) : Nat := (Zipf.counts.getD (r - 1) ("", 0)).2

def narrowInBand (r : Nat) : Bool :=
  decide (narrowFreqAt 1 ≤ 2 * r * narrowFreqAt r) && decide (r * narrowFreqAt r ≤ 2 * narrowFreqAt 1)

/-- **The narrow corpus fits Zipf at 8 of its 17 ranks.** -/
theorem narrow_band_count :
    ((List.range' 1 17).filter narrowInBand).length = 8 ∧ Zipf.counts.length = 17 := by
  constructor <;> native_decide

/-- **The wide corpus fits at 37 of its 39 ranks, the news corpus at 35 of 38.**
This is the re-measurement report 3 asked for: widening the world moves the fit
from 47% of ranks to 95%. -/
theorem zipf_band_counts :
    bandCount neutralCorpus 39 = 37 ∧ bandCount newsCorpus 38 = 35 := by
  constructor <;> native_decide

/-- **But the head is not Zipfian.**  Ranks 2 and 3 sit above the prediction
`c₁/r`, and ranks 4 to 8 sit below it: the curve crosses the law instead of
following it. -/
theorem wide_head_crosses_zipf :
    ((List.range' 2 2).all fun r =>
      decide (freqAt neutralCorpus 1 < r * freqAt neutralCorpus r)) = true ∧
    ((List.range' 4 5).all fun r =>
      decide (r * freqAt neutralCorpus r < freqAt neutralCorpus 1)) = true := by
  constructor <;> native_decide

/-- The ranked heads, for inspection. -/
def demoRanked : List (String × Nat) := (ranked neutralCorpus).take 12
def demoRankedNews : List (String × Nat) := (ranked newsCorpus).take 12

#eval demoRanked
#eval demoRankedNews

end WideZipf
