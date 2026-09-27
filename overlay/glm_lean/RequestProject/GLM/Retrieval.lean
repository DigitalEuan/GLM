/-
# Retrieval by address: what an index built on the lattice can promise

`Address.lean` proves what an address *is* — a quantised feature vector, which
means whatever the feature map means and no more.  This file proves what an
*index* built out of those addresses can promise when it is asked a question:
`overlay/glm_universal/reasoning/retrieval.py` takes a query, addresses it with
the same feature map, and returns the nearest declarations of the development.
The measured half of that — whether the neighbours it returns are relatives,
and whether it beats a name search, a digest control, a reshuffle and chance —
is `studies/ADDRESS_RETRIEVAL_STUDY.md`.  The half that is a theorem is here,
and it is the half that says the answer is *the* answer rather than *an*
answer.

## 1.  The ranking is total, and nothing is decided silently

A candidate is ranked by `(cost, name)`: address distance first, and the name
as the tie-break.  `Prec` is that order.  It is total (`prec_total`) and
transitive (`prec_trans`), so a sort by it is defined; and on a corpus whose
names are distinct it is antisymmetric, which is what makes
`ranked_eq_of_perm` true — **the ranking does not depend on the order the
corpus was read in**.  Two runs over the same declarations in different file
order return the same list, in the same order, with no coin flipped.  That is
the retrieval counterpart of the decoder's `no silent tie-break` discipline:
ties are broken by a stated rule on the name, not by whichever candidate the
loop happened to see first.

## 2.  Taking more is taking more

`topk_prefix`: the top `k` is a prefix of the top `k'` whenever `k ≤ k'`, so
enlarging the window can only add candidates, never reorder or drop one, and
`hit_mono` — if a relative was found at `k` it is still found at `k'` — is a
corollary rather than an experiment.  `mem_topk` says every returned candidate
is a member of the corpus: the index cannot invent a declaration.

## 3.  A radius search is complete, and an empty answer is a proof

`mem_filterRadius_of_le` and `filterRadius_eq_nil_certifies_absence` are the
two halves of the shortlist guarantee.  If the filter at radius `r` comes back
empty, that is not a failure to look: it is a certificate that no entry of the
corpus lies within `r`.  This is the refusal boundary of the address layer —
the index either produces candidates or proves there are none.

## 4.  Feature-close implies address-close, so the shortlist is a superset

`address_dist_le` (a restatement of `GLM.Address.Quantiser.dist_le` in the
retrieval vocabulary) and `complete_shortlist`: everything whose *features* are
within `r` of the query's features has an *address* within `r + 2ρ` of the
query's address, so the radius-`(r + 2ρ)` shortlist contains every entry the
feature map considers close.  Searching the index therefore never misses a
candidate that searching the features would have found — the lattice is a
sound filter, not an approximation of one.  With `ρ = 4`, the covering radius
in the integer model of `Address.lean`, the widening is a constant 8 and does
not grow with the corpus.

## 5.  The index sees the features and nothing else

`retrieve_congr`: two queries with equal features receive the same answer.
Combined with `GLM.Address.address_congr` this fixes the honest reading of the
whole layer — a retrieval result is a fact about the feature map, carried by
the lattice, and the lattice adds no distinction of its own.  The study
measures exactly that: address ranking and raw-feature ranking find a relative
in the same number of cases, and the lattice's contribution is the exactness
and the shortlist bound above, not extra semantics.

Everything here is computable: `sqDist`, `ranked`, `topk` and `filterRadius`
run, and §6 evaluates them on a small corpus by `decide`.
-/
import Mathlib
import RequestProject.GLM.Address

namespace GLM.Retrieval

open Finset

/-! ## 1.  Corpus entries and the ranking order -/

/-- One addressed candidate: a name drawn from a linearly ordered type (the
fully qualified Lean name, in the running system) and the point it addresses
to. -/
structure Entry (I : Type*) (X : Type*) where
  /-- The candidate's name; the tie-break key. -/
  name : I
  /-- The candidate's address. -/
  point : X
  deriving DecidableEq

variable {I : Type*} {X : Type*}

/-- Squared Euclidean distance between integer points — the cost the running
index actually minimises.  Integer in, integer out: no float anywhere. -/
def sqDist {n : ℕ} (x y : Fin n → ℤ) : ℤ := ∑ i, (x i - y i) ^ 2

theorem sqDist_self {n : ℕ} (x : Fin n → ℤ) : sqDist x x = 0 := by
  simp [sqDist]

theorem sqDist_comm {n : ℕ} (x y : Fin n → ℤ) : sqDist x y = sqDist y x :=
  Finset.sum_congr rfl fun _ _ => by ring

theorem sqDist_nonneg {n : ℕ} (x y : Fin n → ℤ) : 0 ≤ sqDist x y :=
  Finset.sum_nonneg fun _ _ => sq_nonneg _

/-- The ranking order: cheaper first, and among equal costs the smaller name.
The tie-break is part of the definition, so no comparison is ever left to the
order in which the corpus was enumerated. -/
def Prec [LinearOrder I] (c : Entry I X → ℤ) (a b : Entry I X) : Prop :=
  c a < c b ∨ (c a = c b ∧ a.name ≤ b.name)

instance instDecidablePrec [LinearOrder I] (c : Entry I X → ℤ) :
    DecidableRel (Prec (X := X) c) := by
  intro a b
  unfold Prec
  infer_instance

theorem prec_refl [LinearOrder I] (c : Entry I X → ℤ) (a : Entry I X) :
    Prec c a a := Or.inr ⟨rfl, le_refl _⟩

theorem prec_total [LinearOrder I] (c : Entry I X → ℤ) (a b : Entry I X) :
    Prec c a b ∨ Prec c b a := by
  unfold Prec
  rcases lt_trichotomy (c a) (c b) with h | h | h
  · exact Or.inl (Or.inl h)
  · rcases le_total a.name b.name with hn | hn
    · exact Or.inl (Or.inr ⟨h, hn⟩)
    · exact Or.inr (Or.inr ⟨h.symm, hn⟩)
  · exact Or.inr (Or.inl h)

theorem prec_trans [LinearOrder I] (c : Entry I X → ℤ) {a b d : Entry I X}
    (hab : Prec c a b) (hbd : Prec c b d) : Prec c a d := by
  unfold Prec at *
  rcases hab with h1 | ⟨h1, hn1⟩ <;> rcases hbd with h2 | ⟨h2, hn2⟩
  · exact Or.inl (h1.trans h2)
  · exact Or.inl (h2 ▸ h1)
  · exact Or.inl (h1 ▸ h2)
  · exact Or.inr ⟨h1.trans h2, hn1.trans hn2⟩

instance instTotalPrec [LinearOrder I] (c : Entry I X → ℤ) :
    Std.Total (Prec (X := X) c) := ⟨prec_total c⟩

instance instTransPrec [LinearOrder I] (c : Entry I X → ℤ) :
    IsTrans (Entry I X) (Prec (X := X) c) := ⟨fun _ _ _ => prec_trans c⟩

/-! ## 2.  The index -/

/-- The whole corpus, ranked against a query cost. -/
def ranked [LinearOrder I] (c : Entry I X → ℤ) (es : List (Entry I X)) :
    List (Entry I X) :=
  List.insertionSort (Prec c) es

/-- The `k` nearest candidates: what `retrieve` returns. -/
def topk [LinearOrder I] (c : Entry I X → ℤ) (k : ℕ) (es : List (Entry I X)) :
    List (Entry I X) :=
  (ranked c es).take k

/-- The shortlist at a radius: every candidate within `r` of the query. -/
def filterRadius [LinearOrder I] (c : Entry I X → ℤ) (r : ℤ)
    (es : List (Entry I X)) : List (Entry I X) :=
  es.filter (fun e => decide (c e ≤ r))

theorem ranked_perm [LinearOrder I] (c : Entry I X → ℤ) (es : List (Entry I X)) :
    (ranked c es).Perm es := List.perm_insertionSort _ _

theorem ranked_pairwise [LinearOrder I] (c : Entry I X → ℤ)
    (es : List (Entry I X)) : List.Pairwise (Prec c) (ranked c es) :=
  List.pairwise_insertionSort _ _

theorem length_ranked [LinearOrder I] (c : Entry I X → ℤ)
    (es : List (Entry I X)) : (ranked c es).length = es.length :=
  (ranked_perm c es).length_eq

/-- **The index cannot invent a declaration.**  Everything it returns is a
member of the corpus it was built from. -/
theorem mem_topk [LinearOrder I] (c : Entry I X → ℤ) (k : ℕ)
    {es : List (Entry I X)} {e : Entry I X} (h : e ∈ topk c k es) : e ∈ es :=
  (ranked_perm c es).mem_iff.mp (List.mem_of_mem_take h)

theorem length_topk_le [LinearOrder I] (c : Entry I X → ℤ) (k : ℕ)
    (es : List (Entry I X)) : (topk c k es).length ≤ k :=
  List.length_take_le _ _

/-- **Taking more is taking more.**  The top `k` is a prefix of the top `k'`
for `k ≤ k'`: widening the window adds candidates at the end and never
reorders or drops one. -/
theorem topk_prefix [LinearOrder I] (c : Entry I X → ℤ) {k k' : ℕ} (h : k ≤ k')
    (es : List (Entry I X)) : (topk c k es) <+: (topk c k' es) :=
  List.take_prefix_take_left h

/-- **A hit at `k` is a hit at any larger `k`.**  The monotonicity the study's
hit-rate table relies on, as a theorem rather than an observation. -/
theorem hit_mono [LinearOrder I] (c : Entry I X → ℤ) {k k' : ℕ} (h : k ≤ k')
    {es : List (Entry I X)} {e : Entry I X} (he : e ∈ topk c k es) :
    e ∈ topk c k' es :=
  (topk_prefix c h es).subset he

/-! ## 3.  Determinism: the answer does not depend on the reading order -/

theorem prec_antisymm_of_nodup [LinearOrder I] (c : Entry I X → ℤ)
    {es : List (Entry I X)} (hnd : (es.map Entry.name).Nodup)
    {a b : Entry I X} (ha : a ∈ es) (hb : b ∈ es)
    (hab : Prec c a b) (hba : Prec c b a) : a = b := by
  have hname : a.name = b.name := by
    unfold Prec at hab hba
    rcases hab with h1 | ⟨h1, hn1⟩ <;> rcases hba with h2 | ⟨h2, hn2⟩
    · exact absurd h1 (by omega)
    · exact absurd h1 (by omega)
    · exact absurd h2 (by omega)
    · exact le_antisymm hn1 hn2
  exact List.inj_on_of_nodup_map hnd ha hb hname

/-- **The ranking is independent of the order the corpus was read in.**  Two
enumerations of the same declarations — a different `rglob` order, a file
renamed, the address book rewritten — produce the same ranked list, provided
the names are distinct.  This is what makes a retrieval result reproducible
rather than merely deterministic within one process. -/
theorem ranked_eq_of_perm [LinearOrder I] (c : Entry I X → ℤ)
    {es fs : List (Entry I X)} (hperm : es.Perm fs)
    (hnd : (es.map Entry.name).Nodup) :
    ranked c es = ranked c fs := by
  have hmem : ∀ x, x ∈ ranked c es ↔ x ∈ es := fun x => (ranked_perm c es).mem_iff
  have hmem' : ∀ x, x ∈ ranked c fs ↔ x ∈ es := by
    intro x
    rw [(ranked_perm c fs).mem_iff]
    exact hperm.mem_iff.symm
  refine List.Perm.eq_of_pairwise (le := Prec c) ?_ (ranked_pairwise c es)
    (ranked_pairwise c fs) ?_
  · intro a b ha hb hab hba
    exact prec_antisymm_of_nodup c hnd ((hmem a).mp ha) ((hmem' b).mp hb) hab hba
  · exact ((ranked_perm c es).trans hperm).trans (ranked_perm c fs).symm

/-- **The top `k` is independent of the reading order too.** -/
theorem topk_eq_of_perm [LinearOrder I] (c : Entry I X → ℤ) (k : ℕ)
    {es fs : List (Entry I X)} (hperm : es.Perm fs)
    (hnd : (es.map Entry.name).Nodup) :
    topk c k es = topk c k fs := by
  unfold topk
  rw [ranked_eq_of_perm c hperm hnd]

/-! ## 4.  The radius shortlist, and what an empty one proves -/

theorem mem_filterRadius_of_le [LinearOrder I] (c : Entry I X → ℤ) {r : ℤ}
    {es : List (Entry I X)} {e : Entry I X} (he : e ∈ es) (hle : c e ≤ r) :
    e ∈ filterRadius c r es := by
  unfold filterRadius
  exact List.mem_filter.mpr ⟨he, by simpa using hle⟩

theorem le_of_mem_filterRadius [LinearOrder I] (c : Entry I X → ℤ) {r : ℤ}
    {es : List (Entry I X)} {e : Entry I X} (he : e ∈ filterRadius c r es) :
    e ∈ es ∧ c e ≤ r := by
  unfold filterRadius at he
  have := List.mem_filter.mp he
  exact ⟨this.1, by simpa using this.2⟩

/-- **An empty shortlist is a proof of absence, not a failure to look.**  If
the radius-`r` filter returns nothing then no entry of the corpus is within
`r`.  This is the refusal boundary of the address layer: the index either
produces candidates or certifies that there are none. -/
theorem filterRadius_eq_nil_certifies_absence [LinearOrder I]
    (c : Entry I X → ℤ) {r : ℤ} {es : List (Entry I X)}
    (h : filterRadius c r es = []) : ∀ e ∈ es, r < c e := by
  intro e he
  by_contra hcon
  have : e ∈ filterRadius c r es := mem_filterRadius_of_le c he (not_lt.mp hcon)
  rw [h] at this
  exact absurd this (List.not_mem_nil)

/-! ## 5.  Feature-close implies address-close -/

section Metric

variable {V : Type*} [MetricSpace V] {L : Set V} {rho : ℝ}

/-- Addressing a query and a candidate moves them apart by at most `2ρ`: a
restatement of `GLM.Address.Quantiser.dist_le` in the retrieval vocabulary. -/
theorem address_dist_le (Q : GLM.Address.Quantiser V L rho) (x y : V) {r : ℝ}
    (h : dist x y ≤ r) : dist (Q.toFun x) (Q.toFun y) ≤ r + 2 * rho :=
  le_trans (Q.dist_le x y) (by linarith)

/-- **The shortlist is a superset, so the index never misses.**  Every
candidate whose features are within `r` of the query's features has an address
within `r + 2ρ` of the query's address, so a radius-`(r + 2ρ)` search over the
addresses returns everything a radius-`r` search over the features would have
returned.  The widening is the constant `2ρ` — with `ρ = 4`, the covering
radius of the integer model, a constant `8`, independent of the corpus. -/
theorem complete_shortlist {D : Type*} (Q : GLM.Address.Quantiser V L rho)
    (feat : D → V) (query : D) {r : ℝ} (cand : D)
    (h : dist (feat query) (feat cand) ≤ r) :
    dist (GLM.Address.address Q feat query) (GLM.Address.address Q feat cand)
      ≤ r + 2 * rho :=
  address_dist_le Q _ _ h

/-- **The index sees the features and nothing else.**  Two queries with equal
features are answered identically — there is no distinction the lattice can
make that the feature map has not already made. -/
theorem retrieve_congr {D : Type*} (Q : GLM.Address.Quantiser V L rho)
    (feat : D → V) {a b : D} (h : feat a = feat b) :
    GLM.Address.address Q feat a = GLM.Address.address Q feat b :=
  GLM.Address.address_congr Q feat h

end Metric

/-! ## 6.  A worked corpus, evaluated -/

/-- A three-coordinate toy corpus, in the same shape as the running one: a
name and an integer address. -/
def demoCorpus : List (Entry ℕ (Fin 3 → ℤ)) :=
  [⟨1, ![0, 0, 0]⟩, ⟨2, ![3, 0, 0]⟩, ⟨3, ![0, 4, 0]⟩, ⟨4, ![1, 1, 1]⟩,
   ⟨5, ![3, 0, 0]⟩]

/-- The cost of a candidate against the query `(1, 0, 0)`. -/
def demoCost (e : Entry ℕ (Fin 3 → ℤ)) : ℤ := sqDist ![1, 0, 0] e.point

theorem demo_topk_three :
    (topk demoCost 3 demoCorpus).map Entry.name = [1, 4, 2] := by decide

/-- The tie between entries 2 and 5 — identical addresses — is broken by the
name, in the stated direction, rather than by the corpus order. -/
theorem demo_ranked_breaks_the_tie_by_name :
    (ranked demoCost demoCorpus).map Entry.name = [1, 4, 2, 5, 3] := by decide

/-- Reading the same corpus in a different order returns the same ranking. -/
theorem demo_ranked_independent_of_reading_order :
    (ranked demoCost demoCorpus.reverse).map Entry.name = [1, 4, 2, 5, 3] := by
  decide

/-- A radius that excludes everything certifies that the corpus is empty at
that radius; a radius that includes some returns exactly those. -/
theorem demo_filter_empty_at_radius_zero :
    filterRadius demoCost 0 demoCorpus = [] := by decide

theorem demo_filter_at_radius_four :
    (filterRadius demoCost 4 demoCorpus).map Entry.name = [1, 2, 4, 5] := by
  decide

end GLM.Retrieval
