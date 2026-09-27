/-
# The corpus held the way the data is: a tiered read, and a certified shortlist

`Address.lean` proves what an address is, and `Retrieval.lean` proves what an
index built out of addresses can promise.  This file is the same discipline
applied to the project's **prose**: the machinery is
`overlay/glm_universal/corpus/`, the measurements are
`studies/CORPUS_ADDRESS_STUDY.md`, and the part that is a theorem rather than a
measurement is here.

## 1.  A tiered document, and why a truncated read is safe

A document is modelled as a *chain of claim sets*: `tier 0` is the paragraph a
reader stops at, and each finer tier adds detail.  The single structural
assumption is `mono` — a finer tier contains every claim of a coarser one — and
everything below is a consequence of it.

* `Tiered.le_mono`, `Tiered.zero_subset`: reading further never *retracts*.  A
  claim seen at tier 0 is still there at tier 5; descending buys resolution and
  can only add.
* `Tiered.coarse_read_sound`: if every claim of the document is true, then
  every claim a tier-0 reader took away is true.  This is the delta-sigma
  contract stated for prose — *a truncated read is coarse, never wrong* — and
  it is exactly what `glm_universal.corpus.checks.tier_report` enforces on the
  real documents by requiring each tier-0 verdict to be quoted from, or
  contained in the vocabulary of, the body below it.
* `Tiered.missed_disjoint`, `Tiered.read_union`: what a reader at tier `k`
  missed is disjoint from what they read, and reading to tier `k'` is reading
  to `k` together with the difference.  Truncation loses claims; it never
  changes one.

## 2.  Archive by rule

`archived` is a predicate on documents, and `stateNow` is its complement, so
the two halves of a corpus partition it: `state_archive_partition` and
`card_state_add_card_archive`.  The corresponding rule in the code decides
membership from the *path*, which is what makes the partition checkable rather
than a matter of judgement.

## 3.  A generated document is a function of its inputs

`generated_congr`: if two corpora agree, anything rendered from them agrees.
That is the whole content of "generate, don't store" — the artefact carries no
information the inputs do not — and it is why the digest of the inputs is a
licence to reuse the artefact (`Derived`, `fresh_iff`).

## 4.  Absence, certified

`absent_of_shortlist_empty` composes `Retrieval.complete_shortlist` with
`Retrieval.filterRadius_eq_nil_certifies_absence`: if the address ball of
radius `r + 2ρ` around a question is empty, then **no** section of the corpus
has features within `r` of it.  An empty answer from the corpus index is a
proof that there is nothing to find within the radius, not a failure to look —
which is the property that makes it safe not to read the rest of a large
corpus.

Everything here is proved outright, with no holes, and depends only on
Lean's standard axioms.
-/
import Mathlib
import RequestProject.GLM.Address
import RequestProject.GLM.Retrieval

namespace GLM.Corpus

open Finset

/-! ## 1.  A tiered document -/

/-- A document read at increasing resolution: `tier k` is what a reader who
stops at tier `k` takes away, and finer tiers only add. -/
structure Tiered (C : Type*) where
  /-- The claims visible at each tier. -/
  tier : ℕ → Set C
  /-- A finer tier contains every claim of the tier before it. -/
  mono : ∀ k, tier k ⊆ tier (k + 1)

namespace Tiered

variable {C : Type*} (D : Tiered C)

/-- Reading further never retracts: the tiers are a chain. -/
theorem le_mono {k k' : ℕ} (h : k ≤ k') : D.tier k ⊆ D.tier k' := by
  induction k' with
  | zero => simpa using (Nat.le_zero.mp h) ▸ subset_rfl
  | succ n ih =>
      rcases Nat.lt_or_ge k (n + 1) with hlt | hge
      · exact (ih (Nat.lt_succ_iff.mp hlt)).trans (D.mono n)
      · have : k = n + 1 := le_antisymm h hge
        exact this ▸ subset_rfl

/-- The coarse read is contained in every finer read. -/
theorem zero_subset (k : ℕ) : D.tier 0 ⊆ D.tier k :=
  D.le_mono (Nat.zero_le k)

/-- **A truncated read is coarse, never wrong.**  If every claim the document
makes at resolution `k` is true, then everything a tier-0 reader took away is
true as well.  Nothing at a finer tier can contradict the summary, because the
summary's claims *are* claims of the finer tier. -/
theorem coarse_read_sound {holds : C → Prop} (k : ℕ)
    (h : ∀ c ∈ D.tier k, holds c) : ∀ c ∈ D.tier 0, holds c :=
  fun c hc => h c (D.zero_subset k hc)

/-- What a reader who stopped at tier `k` missed. -/
def missed (k k' : ℕ) : Set C := D.tier k' \ D.tier k

/-- What was missed is disjoint from what was read: truncation omits claims, it
never alters one. -/
theorem missed_disjoint (k k' : ℕ) : Disjoint (D.tier k) (D.missed k k') :=
  Set.disjoint_sdiff_right

/-- Reading to `k'` is reading to `k` and then the difference. -/
theorem read_union {k k' : ℕ} (h : k ≤ k') :
    D.tier k ∪ D.missed k k' = D.tier k' := by
  have hsub : D.tier k ⊆ D.tier k' := D.le_mono h
  simpa [missed, Set.union_diff_self] using Set.union_eq_self_of_subset_left hsub

/-- A document that never grows is its own summary: the coarse read is the
whole of it. -/
theorem stationary_of_eq (h : ∀ k, D.tier k = D.tier 0) (k : ℕ) :
    D.tier k = D.tier 0 := h k

end Tiered

/-! ## 2.  Archive by rule -/

section Archive

variable {Doc : Type*} (archived : Doc → Prop) [DecidablePred archived]

/-- The documents that describe the state now: exactly those not archived. -/
def stateNow (d : Doc) : Prop := ¬ archived d

/-- The rule partitions the corpus: every document is state or archive, and
none is both. -/
theorem state_archive_partition (d : Doc) :
    (stateNow archived d ∧ ¬ archived d) ∨ (¬ stateNow archived d ∧ archived d) := by
  by_cases h : archived d
  · exact Or.inr ⟨by simpa [stateNow] using h, h⟩
  · exact Or.inl ⟨by simpa [stateNow] using h, h⟩

/-- A session that loads only the current state loads exactly the complement of
the archive, so the two counts add to the size of the corpus. -/
theorem card_state_add_card_archive (s : Finset Doc) :
    (s.filter (fun d => ¬ archived d)).card + (s.filter archived).card = s.card := by
  classical
  rw [add_comm]
  simpa using Finset.card_filter_add_card_filter_not (s := s) (p := archived)

end Archive

/-! ## 3.  A generated artefact is a function of its inputs -/

section Generated

variable {In Out : Type*}

/-- **Generate, don't store.**  Anything rendered from the corpus carries no
information the corpus does not: equal inputs render equal outputs.  This is
why a generated document cannot drift from what it summarises — there is
nothing in it that was not computed from them. -/
theorem generated_congr (render : In → Out) {a b : In} (h : a = b) :
    render a = render b := congrArg render h

/-- A derived artefact kept beside the digest of the inputs it came from. -/
structure Derived (In Out : Type*) where
  /-- The stored output. -/
  value : Out
  /-- The inputs recorded when it was computed. -/
  source : In

/-- The artefact may be reused exactly when the inputs have not moved. -/
def fresh (d : Derived In Out) (now : In) : Prop := d.source = now

/-- **Unchanged input plus recorded digest is a licence to reuse.**  If the
artefact is fresh then it equals what a recomputation would produce; if it is
stale, nothing is claimed — which is why the code reports `stale` rather than
answering. -/
theorem value_eq_of_fresh (render : In → Out) (now : In)
    (d : Derived In Out) (hval : d.value = render d.source)
    (hfresh : fresh d now) : d.value = render now := by
  rw [hval, hfresh]

end Generated

/-! ## 4.  An empty shortlist is a proof of absence -/

section Shortlist

variable {V : Type*} [MetricSpace V] {L : Set V} {rho : ℝ}
variable {I : Type*}

/-- **Nothing within the radius, certified.**  Take a question `q`, address it,
and keep every section whose address lies within `r + 2ρ`.  If that list is
empty then no section of the corpus has features within `r` of the question:
the corpus index either produces candidates or proves there are none.

This is `Retrieval.complete_shortlist` — every feature-close section is
address-close — read in the contrapositive, and it is what makes an unread
corpus safe: an empty answer is a bounded statement about the whole of it, not
a failure to look. -/
theorem absent_of_shortlist_empty (Q : GLM.Address.Quantiser V L rho)
    (q : V) (units : List (GLM.Retrieval.Entry I V)) {r : ℝ}
    (h : units.filter
          (fun e => decide (dist (Q.toFun q) (Q.toFun e.point) ≤ r + 2 * rho))
        = []) :
    ∀ e ∈ units, ¬ dist q e.point ≤ r := by
  intro e he hclose
  have haddr : dist (Q.toFun q) (Q.toFun e.point) ≤ r + 2 * rho :=
    GLM.Retrieval.address_dist_le Q q e.point hclose
  have hmem : e ∈ units.filter
      (fun e => decide (dist (Q.toFun q) (Q.toFun e.point) ≤ r + 2 * rho)) :=
    List.mem_filter.mpr ⟨he, by simpa using haddr⟩
  rw [h] at hmem
  exact absurd hmem List.not_mem_nil

/-- The positive half, for the record: a feature-close section is always in the
shortlist, so the shortlist is a superset of the true neighbourhood and
discarding everything outside it discards nothing. -/
theorem mem_shortlist_of_close (Q : GLM.Address.Quantiser V L rho)
    (q : V) (units : List (GLM.Retrieval.Entry I V)) {r : ℝ}
    {e : GLM.Retrieval.Entry I V} (he : e ∈ units) (hclose : dist q e.point ≤ r) :
    e ∈ units.filter
      (fun e => decide (dist (Q.toFun q) (Q.toFun e.point) ≤ r + 2 * rho)) :=
  List.mem_filter.mpr
    ⟨he, by simpa using GLM.Retrieval.address_dist_le Q q e.point hclose⟩

end Shortlist

/-! ## 5.  A worked document -/

/-- Three tiers over the natural numbers: the verdict, the claims, the detail. -/
def demoDocument : Tiered ℕ where
  tier k := {c | c < k + 1}
  mono k := by
    intro c hc
    simp only [Set.mem_setOf_eq] at hc ⊢
    omega

theorem demo_zero_subset_two : demoDocument.tier 0 ⊆ demoDocument.tier 2 :=
  demoDocument.zero_subset 2

theorem demo_missed :
    demoDocument.missed 0 2 = {c | c < 3 ∧ ¬ c < 1} := by
  ext c
  simp only [Tiered.missed, demoDocument, Set.mem_diff, Set.mem_setOf_eq]

end GLM.Corpus
