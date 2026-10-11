import Mathlib
import RequestProject.GLM.DeepHoleEscalation

/-!
# The share-carrying rungs: what bounds the share part's seed shift (Phase 121)

`studies/SHARE_SEPARATION_STUDY.md` takes lattice item 6 for the two rungs of
the deep-hole ladder whose profile carries the **arrival shares**.  The share
part of a profile is a *sorted* vector: the share of each vertex the ensemble
reached, in descending order, padded with zeros.  Sorting is what lets two
holes with different vertex sets be compared at all.  This file proves the two
facts the study measures against.

## 1.  Sorting is non-expansive in L1

`l1_le_perm` (the swap argument): if `f` and `g` are both antitone (or both
monotone, `l1_le_perm_of_monotone`), pairing them index by index is the
cheapest pairing — no permutation of `g` comes closer to `f` in L1.

`l1_rearranged_le` and `l1_sort_le` turn this into the statement the study
uses: the L1 distance between the sorted rearrangements of two vectors is at
most their L1 distance as given.  For the **same** deep hole under two
ensemble seeds, the vertices are the same lattice points, so the two share
vectors can be compared vertex by vertex; `share_shift_le_matched` says the
seed shift of the sorted share profile — the share part of the ladder's `W` —
is at most that vertex-matched shift, the L1 distance between two empirical
distributions on one finite set.

## 2.  The per-hole criterion

`nearest_correct_local` is `GLM.DeepHoleLadder.nearest_correct` with the worst
spread replaced by the hole's own: a carrier within `w` of its reference is
named correctly whenever that reference is more than `2w` from every other.
`resolves_local` says the global criterion `Resolves` gives the local one at
every reference, so the per-hole certificate is never weaker.
-/

namespace GLM.ShareSeparation

open Finset GLM.DeepHoleLadder

/-! ## 1.  Sorting is non-expansive in L1 -/

/-- The L1 distance between two rational vectors of one length. -/
def l1 {n : ℕ} (x y : Fin n → ℚ) : ℚ := ∑ i, |x i - y i|

/-- The four-point inequality behind the swap argument: pairing the larger
with the larger and the smaller with the smaller is never worse. -/
theorem four_point {a b c d : ℚ} (hab : b ≤ a) (hcd : d ≤ c) :
    |a - c| + |b - d| ≤ |a - d| + |b - c| := by
  rcases abs_cases (a - c) with ⟨h1, _⟩ | ⟨h1, _⟩ <;>
  rcases abs_cases (b - d) with ⟨h2, _⟩ | ⟨h2, _⟩ <;>
  rcases abs_cases (a - d) with ⟨h3, _⟩ | ⟨h3, _⟩ <;>
  rcases abs_cases (b - c) with ⟨h4, _⟩ | ⟨h4, _⟩ <;>
  linarith

/-- **The swap argument.**  Two antitone vectors are closest in L1 when paired
index by index: no permutation of the second does better. -/
theorem l1_le_perm {n : ℕ} {f g : Fin n → ℚ} (hf : Antitone f) (hg : Antitone g)
    (σ : Equiv.Perm (Fin n)) :
    ∑ i, |f i - g i| ≤ ∑ i, |f i - g (σ i)| := by
  induction h : σ.support.card using Nat.strong_induction_on generalizing σ with
  | _ k ih =>
  by_cases hs : σ.support.Nonempty
  · set x := σ.support.min' hs with hxdef
    have hxmem : x ∈ σ.support := Finset.min'_mem _ _
    have hx : σ x ≠ x := Equiv.Perm.mem_support.mp hxmem
    have hmin : ∀ y ∈ σ.support, x ≤ y := fun y hy => Finset.min'_le _ _ hy
    set j := σ.symm x with hjdef
    have hσj : σ j = x := by simp [hjdef]
    have hjx : j ≠ x := by
      intro hj; apply hx; rw [← hj, hσj, hj]
    have hjmem : j ∈ σ.support := by
      rw [Equiv.Perm.mem_support, hσj]; exact fun h => hjx h.symm
    have hσxmem : σ x ∈ σ.support := Equiv.Perm.apply_mem_support.mpr hxmem
    set τ := Equiv.swap x (σ x) * σ with hτdef
    have hcard : τ.support.card < σ.support.card :=
      Equiv.Perm.card_support_swap_mul hx
    have ih' := ih τ.support.card (h ▸ hcard) τ rfl
    have hτx : τ x = x := by
      simp only [hτdef, Equiv.Perm.mul_apply, Equiv.swap_apply_right]
    have hτj : τ j = σ x := by
      simp only [hτdef, Equiv.Perm.mul_apply, hσj, Equiv.swap_apply_left]
    have hτo : ∀ i, i ≠ x → i ≠ j → τ i = σ i := by
      intro i hix hij
      simp only [hτdef, Equiv.Perm.mul_apply]
      apply Equiv.swap_apply_of_ne_of_ne
      · intro hc; apply hij; rw [hjdef, ← hc]; simp
      · intro hc; exact hix (σ.injective hc)
    have hxj : x ≤ j := hmin j hjmem
    have hxσ : x ≤ σ x := hmin (σ x) hσxmem
    have key : ∑ i, |f i - g (τ i)| ≤ ∑ i, |f i - g (σ i)| := by
      rw [← sub_nonneg, ← Finset.sum_sub_distrib]
      rw [Fintype.sum_eq_add x j hjx.symm]
      · rw [hτx, hτj]
        have := four_point (a := f x) (b := f j) (c := g x) (d := g (σ x))
          (hf hxj) (hg hxσ)
        rw [hσj]
        linarith
      · intro i ⟨hix, hij⟩
        rw [hτo i hix hij]; ring
    linarith
  · have hσ : σ = 1 := by
      rw [Finset.not_nonempty_iff_eq_empty] at hs
      exact Equiv.Perm.support_eq_empty_iff.mp hs
    subst hσ; simp

/-- The same for two monotone vectors. -/
theorem l1_le_perm_of_monotone {n : ℕ} {f g : Fin n → ℚ} (hf : Monotone f)
    (hg : Monotone g) (σ : Equiv.Perm (Fin n)) :
    ∑ i, |f i - g i| ≤ ∑ i, |f i - g (σ i)| := by
  have h := l1_le_perm (f := fun i => -f i) (g := fun i => -g i)
    (fun a b hab => neg_le_neg (hf hab)) (fun a b hab => neg_le_neg (hg hab)) σ
  have e : ∀ u v : ℚ, |-u - -v| = |u - v| := fun u v => by
    rw [show -u - -v = -(u - v) by ring, abs_neg]
  simpa only [e] using h

/-- **Sorting is non-expansive in L1.**  If `x ∘ p` and `y ∘ q` are the two
vectors rearranged into the same order (both antitone), their L1 distance is
at most the distance between `x` and `y` as given. -/
theorem l1_rearranged_le {n : ℕ} (x y : Fin n → ℚ) (p q : Equiv.Perm (Fin n))
    (hp : Antitone (x ∘ p)) (hq : Antitone (y ∘ q)) :
    l1 (x ∘ p) (y ∘ q) ≤ l1 x y := by
  unfold l1
  have h := l1_le_perm hp hq (q.symm * p)
  have e : ∑ i, |x i - y i| = ∑ i, |(x ∘ p) i - (y ∘ q) ((q.symm * p) i)| := by
    rw [← Equiv.sum_comp p (fun i => |x i - y i|)]
    simp
  rw [e]; exact h

/-- The same for the ascending order. -/
theorem l1_rearranged_le_of_monotone {n : ℕ} (x y : Fin n → ℚ)
    (p q : Equiv.Perm (Fin n)) (hp : Monotone (x ∘ p)) (hq : Monotone (y ∘ q)) :
    l1 (x ∘ p) (y ∘ q) ≤ l1 x y := by
  unfold l1
  have h := l1_le_perm_of_monotone hp hq (q.symm * p)
  have e : ∑ i, |x i - y i| = ∑ i, |(x ∘ p) i - (y ∘ q) ((q.symm * p) i)| := by
    rw [← Equiv.sum_comp p (fun i => |x i - y i|)]
    simp
  rw [e]; exact h

/-- Sorting with Mathlib's `Tuple.sort` never increases an L1 distance. -/
theorem l1_sort_le {n : ℕ} (x y : Fin n → ℚ) :
    l1 (x ∘ Tuple.sort x) (y ∘ Tuple.sort y) ≤ l1 x y :=
  l1_rearranged_le_of_monotone x y _ _ (Tuple.monotone_sort x) (Tuple.monotone_sort y)

/-- **The share part's seed shift is bounded by the vertex-matched shift.**
Index the vertices one deep hole's two ensembles reached by `Fin n` (padding
with zero shares, as the ladder pads to 48); `s` and `t` are the two seeds'
shares and `p`, `q` the orders that sort them descending.  The distance the
ladder's share part measures between the two seeds is at most the L1 distance
between the two share vectors vertex by vertex. -/
theorem share_shift_le_matched {n : ℕ} (s t : Fin n → ℚ) (p q : Equiv.Perm (Fin n))
    (hp : Antitone (s ∘ p)) (hq : Antitone (t ∘ q)) :
    l1 (s ∘ p) (t ∘ q) ≤ ∑ i, |s i - t i| :=
  l1_rearranged_le s t p q hp hq

/-- A sorted profile does not depend on which order the vertices were listed
in: two descending rearrangements of the same vector are at L1 distance `0`. -/
theorem l1_rearranged_self {n : ℕ} (x : Fin n → ℚ) (p q : Equiv.Perm (Fin n))
    (hp : Antitone (x ∘ p)) (hq : Antitone (x ∘ q)) :
    l1 (x ∘ p) (x ∘ q) = 0 := by
  apply le_antisymm
  · have := l1_rearranged_le x x p q hp hq
    simpa [l1] using this
  · exact Finset.sum_nonneg (fun i _ => abs_nonneg _)

/-! ## 2.  The per-hole criterion -/

variable {C : Type*} {L : Type*}

/-- **The per-hole criterion.**  A carrier within `w` of its own reference is
strictly nearer to it than to any other reference, provided that reference is
more than `2w` from every reference with another label.  The spread is the
hole's own, not the worst hole's. -/
theorem nearest_correct_local {R : Reading C} {refs : List (L × C)} {w : ℚ}
    {t : L} {p x : C} (hx : R.dist x p ≤ w)
    (hsep : ∀ e ∈ refs, e.1 ≠ t → 2 * w < R.dist p e.2) :
    ∀ e ∈ refs, e.1 ≠ t → R.dist x p < R.dist x e.2 := by
  intro e he hne
  have h1 := hsep e he hne
  have htri : R.dist p e.2 ≤ R.dist p x + R.dist x e.2 := R.dist_triangle p x e.2
  have hpx : R.dist p x = R.dist x p := R.dist_comm p x
  linarith

/-- The global criterion gives the per-hole one at every reference, so the
per-hole certificate is never weaker. -/
theorem resolves_local {R : Reading C} {refs : List (L × C)} {w : ℚ}
    (hres : Resolves R refs w) {t : L} {p : C} (hmem : (t, p) ∈ refs) :
    ∀ e ∈ refs, e.1 ≠ t → 2 * w < R.dist p e.2 := by
  intro e he hne
  have := hres e he (t, p) hmem hne
  rwa [R.dist_comm] at this

/-- The per-hole criterion can certify a hole the global one cannot: a table
of three references on the line where the global criterion fails at the worst
spread and the per-hole one still holds for the far reference. -/
theorem local_can_certify_when_global_fails :
    let R := Reading.ofMap (fun z : ℚ => z)
    let refs : List (Fin 3 × ℚ) := [(0, 0), (1, 1), (2, 10)]
    ¬ Resolves R refs 1 ∧ ∀ e ∈ refs, e.1 ≠ 2 → 2 * 1 < R.dist 10 e.2 := by
  simp only
  refine ⟨?_, ?_⟩
  · intro h
    have := h (0, 0) (by simp) (1, 1) (by simp) (by decide)
    norm_num at this
  · intro e he hne
    simp only [List.mem_cons, List.not_mem_nil, or_false] at he
    rcases he with rfl | rfl | rfl
    · norm_num
    · norm_num
    · exact absurd rfl hne

end GLM.ShareSeparation
