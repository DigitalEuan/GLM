/-
# The third view on demand, independent faults, and argument unpacking

Phase 97 (`studies/UNPACKING_RESCORE_STUDY.md`). Three groups of statements,
one for each part of the round.

* `inter_eq_of_resolved`, `on_demand_agrees`, `inside_radius_unique` —
  **the third view on demand changes no answer inside the fault model.** If
  the carrier is in every view's fork and two views leave only the carrier,
  a third view leaves only the carrier too; and inside the packing radius one
  view already leaves only the carrier, so the third view is never read.
* `open_seconds_card`, `open_seconds_card_frame`, `independent_never_separated`
  — **under independent faults the frame cannot help two views.** For a
  first error `e` of weight four, exactly 346 of the 10,626 second errors `f`
  leave an octad through `e ∪ f` (the five octads through `e` hold 70
  four-sets each, and any two share only `e`); the count is the same for
  every permutation applied to the second view, so no frame does better; and
  for every frame some pair stays open.
* `flatten_length`, `bind_isSome_iff`, `bind_rest`, `star_round_trip` —
  **argument unpacking, as the dialect runs it.** A call's arguments are its
  positional values with every `*xs` spliced in place; a definition with `k`
  positional parameters and a `*rest` accepts exactly the argument lists of
  length at least `k`, binding `rest` to what is past the first `k`; so
  `def f(*r)` called as `f(*xs)` binds `r` to `xs`.
-/
import RequestProject.GLM.SecondView

namespace GLM.OnDemandView

open Finset GLM.Golay24 GLM.SecondView

/-! ## 1. The third view on demand -/

/-- If the truth lies in every fork and two forks meet only in the truth, a
third fork does not change the intersection. -/
theorem inter_eq_of_resolved {α : Type*} [DecidableEq α] {A B C : Finset α} {t : α}
    (hC : t ∈ C) (h : A ∩ B = {t}) : A ∩ B ∩ C = A ∩ B := by
  rw [h]
  ext x
  simp only [mem_inter, mem_singleton]
  constructor
  · exact fun h => h.1
  · rintro rfl; exact ⟨rfl, hC⟩

/-- No octad contains a larger set of points than one that lies in no octad. -/
theorem through_eq_empty_mono {u v : Word} (huv : u ⊆ v) (h : through u = ∅) :
    through v = ∅ := by
  rw [eq_empty_iff_forall_notMem] at h ⊢
  intro o ho
  obtain ⟨ho8, hv⟩ := mem_through.1 ho
  exact h o (mem_through.2 ⟨ho8, huv.trans hv⟩)

/-- **On demand agrees with three views.** For a codeword `c` and errors `e`,
`f`, `g` of weight four read through three views: if the first two views
resolve the read (no octad through `e ∪ f`), the three views resolve it, to
the same codeword. -/
theorem on_demand_agrees {c e f g : Word} (hc : IsCodeword c) (he : e.card = 4)
    (hf : f.card = 4) (h : through (e ∪ f) = ∅) :
    ∀ c', IsCodeword c' → hdist c' (symmDiff c e) = 4 → hdist c' (symmDiff c f) = 4 →
      hdist c' (symmDiff c g) = 4 → c' = c := by
  intro c' hc' h1 h2 _
  exact (resolved_iff hc he hf).2 h c' hc' h1 h2

/-- **Inside the packing radius one view suffices.** For an error of weight
at most three, every codeword other than `c` is farther from the read
`c ∆ e` than `c` is. -/
theorem inside_radius_unique {c c' e : Word} (hc : IsCodeword c) (hc' : IsCodeword c')
    (he : e.card ≤ 3) (hne : c' ≠ c) : e.card < hdist c' (symmDiff c e) := by
  rw [hdist_read]
  set d := symmDiff c c'
  have hd : IsCodeword d := isCodeword_symmDiff hc hc'
  have hd0 : d ≠ ∅ := fun h0 => hne (symmDiff_eq_bot.1 h0).symm
  have h8 : 8 ≤ d.card := golay_min_weight hd hd0
  have hcard : (symmDiff d e).card = d.card + e.card - 2 * (d ∩ e).card :=
    card_symmDiff_eq d e
  have hle : (d ∩ e).card ≤ e.card := card_le_card inter_subset_right
  omega

/-! ## 2. Independent faults: the frame cannot help two views -/

/-- A four-set `f` leaves an octad through `e ∪ f` exactly when it lies in
one of the octads through `e`. -/
theorem through_union_nonempty_iff (e f : Word) :
    (through (e ∪ f)).Nonempty ↔ ∃ o ∈ through e, f ⊆ o := by
  constructor
  · rintro ⟨o, ho⟩
    obtain ⟨ho8, hsub⟩ := mem_through.1 ho
    exact ⟨o, mem_through.2 ⟨ho8, subset_union_left.trans hsub⟩,
      subset_union_right.trans hsub⟩
  · rintro ⟨o, ho, hf⟩
    obtain ⟨ho8, he⟩ := mem_through.1 ho
    exact ⟨o, mem_through.2 ⟨ho8, union_subset he hf⟩⟩

/-- Two distinct octads through a four-set `e` meet exactly in `e`. -/
theorem inter_eq_of_through {e o₁ o₂ : Word} (he : e.card = 4) (h₁ : o₁ ∈ through e)
    (h₂ : o₂ ∈ through e) (hne : o₁ ≠ o₂) : o₁ ∩ o₂ = e := by
  obtain ⟨h₁8, he₁⟩ := mem_through.1 h₁
  obtain ⟨h₂8, he₂⟩ := mem_through.1 h₂
  have hle := card_inter_le_four h₁8 h₂8 hne
  have hsub : e ⊆ o₁ ∩ o₂ := subset_inter he₁ he₂
  exact (eq_of_subset_of_card_le hsub (by omega)).symm

/-- The four-sets of the octads through `e`, `e` itself set aside. -/
def openSeconds (e : Word) : Finset Word :=
  (univ.powersetCard 4).filter fun f => (through (e ∪ f)).Nonempty

theorem openSeconds_eq (e : Word) :
    openSeconds e = (through e).biUnion fun o => o.powersetCard 4 := by
  ext f
  simp only [openSeconds, mem_filter, mem_powersetCard, mem_biUnion,
    through_union_nonempty_iff, subset_univ, true_and]
  constructor
  · rintro ⟨hf, o, ho, hfo⟩
    exact ⟨o, ho, hfo, hf⟩
  · rintro ⟨o, ho, hfo, hf⟩
    exact ⟨hf, o, ho, hfo⟩

/-- **Two views, independent faults.** For a first error `e` of weight four,
exactly 346 of the four-sets `f` leave an octad through `e ∪ f`. -/
theorem open_seconds_card {e : Word} (he : e.card = 4) : (openSeconds e).card = 346 := by
  have hmem : e ∈ openSeconds e := by
    rw [openSeconds_eq, mem_biUnion]
    obtain ⟨o, ho⟩ : (through e).Nonempty := by
      rw [← card_pos, card_octads_through_four he]; norm_num
    exact ⟨o, ho, mem_powersetCard.2 ⟨(mem_through.1 ho).2, he⟩⟩
  have herase : (openSeconds e).erase e =
      (through e).biUnion fun o => (o.powersetCard 4).erase e := by
    rw [openSeconds_eq]
    ext f
    simp only [mem_erase, mem_biUnion]
    constructor
    · rintro ⟨hne, o, ho, hf⟩; exact ⟨o, ho, hne, hf⟩
    · rintro ⟨o, ho, hne, hf⟩; exact ⟨hne, o, ho, hf⟩
  have hdisj : (↑(through e) : Set Word).PairwiseDisjoint
      fun o => (o.powersetCard 4).erase e := by
    intro o₁ h₁ o₂ h₂ hne
    rw [Function.onFun, disjoint_left]
    intro f hf1 hf2
    obtain ⟨hfe, hf1⟩ := mem_erase.1 hf1
    obtain ⟨_, hf2⟩ := mem_erase.1 hf2
    obtain ⟨hs1, hc⟩ := mem_powersetCard.1 hf1
    obtain ⟨hs2, _⟩ := mem_powersetCard.1 hf2
    have hint := inter_eq_of_through he (mem_coe.1 h₁) (mem_coe.1 h₂) hne
    have hsub : f ⊆ e := by
      have := subset_inter hs1 hs2
      rwa [hint] at this
    exact hfe (eq_of_subset_of_card_le hsub (by omega))
  have hpiece : ∀ o ∈ through e, ((o.powersetCard 4).erase e).card = 69 := by
    intro o ho
    obtain ⟨ho8, heo⟩ := mem_through.1 ho
    have hw : o.card = 8 := (mem_octads.1 ho8).2
    rw [card_erase_of_mem (mem_powersetCard.2 ⟨heo, he⟩), card_powersetCard, hw]
    rfl
  have hsum : ((openSeconds e).erase e).card = 345 := by
    rw [herase, card_biUnion hdisj, sum_congr rfl hpiece, sum_const,
      card_octads_through_four he]
    rfl
  have := card_erase_add_one hmem
  omega

/-- **The frame cannot help.** Whatever permutation `σ` the second view's
frame applies to its error, exactly 346 second errors leave the read open. -/
theorem open_seconds_card_frame (σ : Equiv.Perm (Fin 24)) {e : Word} (he : e.card = 4) :
    ((univ.powersetCard 4).filter fun f : Word =>
        (through (e ∪ f.map σ.toEmbedding)).Nonempty).card = 346 := by
  rw [← open_seconds_card he, openSeconds]
  apply card_bij (fun f _ => f.map σ.toEmbedding)
  · intro f hf
    simp only [mem_filter, mem_powersetCard, subset_univ, true_and] at hf ⊢
    exact ⟨by rw [card_map]; exact hf.1, hf.2⟩
  · intro f₁ _ f₂ _ h
    exact map_injective _ h
  · intro g hg
    simp only [mem_filter, mem_powersetCard, subset_univ, true_and] at hg
    refine ⟨g.map σ.symm.toEmbedding, ?_, ?_⟩
    · simp only [mem_filter, mem_powersetCard, subset_univ, true_and]
      have hback : (g.map σ.symm.toEmbedding).map σ.toEmbedding = g := by
        rw [map_map]
        ext x
        simp
      rw [hback, card_map]
      exact hg
    · rw [map_map]
      ext x
      simp

/-- **Some pair always stays open.** For every frame `σ` and every first
error `e`, the second error `σ⁻¹ e` is read back as `e`, and five octads pass
through `e`. -/
theorem independent_never_separated (σ : Equiv.Perm (Fin 24)) {e : Word} (he : e.card = 4) :
    ∃ f : Word, f.card = 4 ∧ (through (e ∪ f.map σ.toEmbedding)).card = 5 := by
  refine ⟨e.map σ.symm.toEmbedding, by rw [card_map]; exact he, ?_⟩
  have hback : (e.map σ.symm.toEmbedding).map σ.toEmbedding = e := by
    rw [map_map]
    ext x
    simp
  rw [hback, union_self]
  exact card_octads_through_four he

/-! ## 3. Argument unpacking -/

/-- One argument of a call: a positional value, or `*xs`. -/
inductive Arg (α : Type*) where
  | pos (a : α)
  | star (xs : List α)

/-- How many positional arguments one argument supplies. -/
def Arg.width {α : Type*} : Arg α → ℕ
  | .pos _ => 1
  | .star xs => xs.length

/-- The positional arguments of a call, every `*xs` spliced in place, left to
right (`Evaluator.call_args`). -/
def flatten {α : Type*} : List (Arg α) → List α
  | [] => []
  | .pos a :: rest => a :: flatten rest
  | .star xs :: rest => xs ++ flatten rest

theorem flatten_append {α : Type*} (as bs : List (Arg α)) :
    flatten (as ++ bs) = flatten as ++ flatten bs := by
  induction as with
  | nil => rfl
  | cons a as ih =>
    cases a <;> simp [flatten, ih]

/-- The number of positional arguments is the sum of the widths. -/
theorem flatten_length {α : Type*} (as : List (Arg α)) :
    (flatten as).length = (as.map Arg.width).sum := by
  induction as with
  | nil => rfl
  | cons a as ih =>
    cases a <;> simp [flatten, Arg.width, ih]; omega

/-- A call with only positional arguments is unchanged by flattening. -/
theorem flatten_pos {α : Type*} (xs : List α) : flatten (xs.map Arg.pos) = xs := by
  induction xs with
  | nil => rfl
  | cons x xs ih => simp [flatten, ih]

/-- Binding a call's arguments to a definition with `k` positional
parameters and, if `rest`, a `*rest` parameter (`Evaluator.call_function`):
the positional bindings and the tuple bound to `rest`, or `none` for
CPython's `TypeError`. -/
def bind {α : Type*} (k : ℕ) (rest : Bool) (args : List α) :
    Option (List α × List α) :=
  if rest then (if k ≤ args.length then some (args.take k, args.drop k) else none)
  else (if args.length = k then some (args, []) else none)

/-- **Which calls bind.** Without `*rest` exactly the argument lists of
length `k`; with it exactly those of length at least `k`. -/
theorem bind_isSome_iff {α : Type*} (k : ℕ) (rest : Bool) (args : List α) :
    (bind k rest args).isSome ↔ if rest then k ≤ args.length else args.length = k := by
  unfold bind
  cases rest <;> simp only [Bool.false_eq_true, ite_false, ite_true] <;> split <;> simp_all

/-- **What `*rest` holds.** With a `*rest` parameter, `rest` is bound to the
arguments past the first `k`, and the positional parameters to the first `k`;
together they are the whole argument list. -/
theorem bind_rest {α : Type*} {k : ℕ} {args ps rs : List α}
    (h : bind k true args = some (ps, rs)) :
    ps = args.take k ∧ rs = args.drop k ∧ ps ++ rs = args := by
  unfold bind at h
  simp only [ite_true] at h
  split at h
  · simp only [Option.some.injEq, Prod.mk.injEq] at h
    obtain ⟨rfl, rfl⟩ := h
    exact ⟨rfl, rfl, List.take_append_drop k args⟩
  · simp at h

/-- **The round trip.** `def f(*r)` called as `f(*xs)` binds `r` to `xs`. -/
theorem star_round_trip {α : Type*} (xs : List α) :
    bind 0 true (flatten [Arg.star xs]) = some ([], xs) := by
  simp [bind, flatten]

end GLM.OnDemandView
