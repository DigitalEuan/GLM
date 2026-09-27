/-
# The LLVQ table: why the class minimum is a min-sum, and why the search may stop

`overlay/glm_universal/reasoning/llvq_table.py` replaces the Leech decoder's
4,096-codeword scan by a table.  Under the MOG alignment the Golay code splits
into **128 classes** — a hexacode word and a parity bit — of **32 codewords**
each, and inside a class the only freedom left is one *top bit* per column,
constrained so that the six top bits have the class's parity.  Two facts make
that split into an algorithm, and this file proves both of them.

## 1.  A class minimum is a six-term min-sum with one parity repair

Each column offers two patterns, of costs `a i` and `b i`, and the cost of a
choice `t : Fin n → Bool` is `cost a b t = ∑ i, if t i then b i else a i`.
Take the cheaper pattern in every column — `pick`, with ties going to the
first — and let `gap i = |a i − b i|`.  Then

* `isLeast_cost_of_parity_eq` — if `pick` already has the wanted parity, the
  class minimum is `∑ lo`, and `pick` attains it;
* `isLeast_cost_of_parity_ne` — if it does not, the class minimum is
  `∑ lo + gap i₀` for a column `i₀` of least gap, and flipping that one top
  bit attains it.

Both are stated as `IsLeast`, so each carries the two halves the decoder needs
at once: the value is attained, and nothing in the class beats it.  This is
exactly the six comparisons the Python `_class_minimum` makes, and nothing
weaker: `cost_eq` is the identity it relies on, that a choice costs the
cheapest choice plus the gaps of the columns where it differs.

## 2.  The class really does hold 32 words

`card_parity_class`: the choices of `n` top bits with a fixed parity number
`2 ^ (n − 1)`.  At `n = 6` that is the 32 the table claims, and with the 128
classes it is the whole code, `128 × 32 = 4096`.

## 3.  Expanding only the cheap classes still returns the true minimum

`isLeast_of_bounded_search` is the branch-and-bound step, stated for an
arbitrary finite set `S`, an expanded part `E`, a lower bound `f ≤ g` and an
incumbent `w`: if `w` is best in `E` and every unexpanded member already costs
at least `g w` under the *bound* `f`, then `w` is best in `S`.  In the decoder
`g` is the cost with the `±4` repair and `f` is the cost without it — the
repair is nonnegative, which is the whole of what `hfg` asks — so a class whose
minimum exceeds the incumbent can be skipped unopened.  That is why the
measured figure of a couple of classes per call is a *complete* search and not
a heuristic one.

Nothing here is about the Golay code specifically: the code enters only
through the two structural facts the Python side checks by computation (that
the 128 classes are the code, and that a class is a parity-constrained product
of column choices), and everything the algorithm then does is proved here.
-/
import Mathlib

namespace GLM.LLVQ

open Finset

/-! ## 0.  Two-element arithmetic, used for the parity bookkeeping -/

theorem zmod2_ne_succ : ∀ x : ZMod 2, x ≠ x + 1 := by decide

theorem zmod2_succ_succ : ∀ x : ZMod 2, x + 1 + 1 = x := by decide

theorem zmod2_cases : ∀ x p : ZMod 2, x = p ∨ x = p + 1 := by decide

/-! ## 1.  The columns, the greedy choice and the gaps -/

variable {n : ℕ}

/-- The parity of a choice of top bits. -/
def parZ (t : Fin n → Bool) : ZMod 2 := ∑ i, if t i then 1 else 0

variable (a b : Fin n → ℚ)

/-- The cheaper of a column's two patterns. -/
def lo (i : Fin n) : ℚ := min (a i) (b i)

/-- What a column's dearer pattern costs above its cheaper one. -/
def gap (i : Fin n) : ℚ := |a i - b i|

/-- The greedy choice: the cheaper top bit, ties going to `0`. -/
def pick (i : Fin n) : Bool := decide (b i < a i)

/-- The cost of a choice of top bits, column by column. -/
def cost (t : Fin n → Bool) : ℚ := ∑ i, if t i then b i else a i

theorem gap_nonneg (i : Fin n) : 0 ≤ gap a b i := abs_nonneg _

/-- A column costs its cheaper pattern, plus its gap when the choice differs
from the greedy one. -/
theorem cost_pointwise (t : Fin n → Bool) (i : Fin n) :
    (if t i then b i else a i)
      = lo a b i + (if t i = pick a b i then 0 else gap a b i) := by
  unfold lo gap pick
  rcases lt_trichotomy (b i) (a i) with h | h | h
  · have hmin : min (a i) (b i) = b i := min_eq_right h.le
    have habs : |a i - b i| = a i - b i := abs_of_pos (by linarith)
    cases ht : t i <;> simp [hmin, habs, h]
  · cases ht : t i <;> simp [h]
  · have hmin : min (a i) (b i) = a i := min_eq_left h.le
    have habs : |a i - b i| = b i - a i := by
      rw [abs_of_nonpos (by linarith)]; ring
    have hp : ¬ (b i < a i) := not_lt.mpr h.le
    cases ht : t i <;> simp [hmin, habs, hp]

/-- **The identity the class minimum rests on.**  A choice costs the greedy
choice plus the gaps of exactly the columns where the two differ. -/
theorem cost_eq (t : Fin n → Bool) :
    cost a b t = (∑ i, lo a b i)
      + ∑ i ∈ univ.filter (fun i => t i ≠ pick a b i), gap a b i := by
  have h1 : cost a b t
      = ∑ i, (lo a b i + (if t i = pick a b i then 0 else gap a b i)) :=
    Finset.sum_congr rfl (fun i _ => cost_pointwise a b t i)
  rw [h1, Finset.sum_add_distrib]
  congr 1
  rw [Finset.sum_filter]
  exact Finset.sum_congr rfl
    (fun i _ => by by_cases h : t i = pick a b i <;> simp [h])

/-- The parity of a choice is the greedy parity shifted by the number of
columns at which the two differ. -/
theorem parZ_eq_add_card_diff (t : Fin n → Bool) :
    parZ t = parZ (pick a b)
      + ((univ.filter (fun i => t i ≠ pick a b i)).card : ZMod 2) := by
  unfold parZ
  rw [Finset.card_filter]
  push_cast
  rw [← Finset.sum_add_distrib]
  refine Finset.sum_congr rfl (fun i _ => ?_)
  by_cases h : t i = pick a b i
  · cases ht : t i <;> simp <;> rw [← h, ht] <;> simp
  · cases ht : t i <;> cases hp : pick a b i <;>
      (simp [ht, hp] at h ⊢; try decide)

/-! ## 2.  The class minimum -/

/-- **The class minimum, greedy parity already right.**  The cheapest pattern
in every column is admissible, so the class minimum is the plain min-sum. -/
theorem isLeast_cost_of_parity_eq (p : ZMod 2) (hp : parZ (pick a b) = p) :
    IsLeast {c | ∃ t, parZ t = p ∧ cost a b t = c} (∑ i, lo a b i) := by
  constructor
  · refine ⟨pick a b, hp, ?_⟩
    rw [cost_eq]
    simp
  · rintro c ⟨t, _, rfl⟩
    rw [cost_eq]
    have h : 0 ≤ ∑ i ∈ univ.filter (fun i => t i ≠ pick a b i), gap a b i :=
      Finset.sum_nonneg (fun i _ => gap_nonneg a b i)
    linarith

/-- **The class minimum, greedy parity wrong.**  Exactly one column has to give
way, and the cheapest way to give it is the least gap: the minimum is
`∑ lo + gap i₀`, attained by flipping that column's top bit. -/
theorem isLeast_cost_of_parity_ne (p : ZMod 2) (hp : parZ (pick a b) ≠ p)
    (i₀ : Fin n) (hi₀ : ∀ i, gap a b i₀ ≤ gap a b i) :
    IsLeast {c | ∃ t, parZ t = p ∧ cost a b t = c}
      ((∑ i, lo a b i) + gap a b i₀) := by
  have hp' : p = parZ (pick a b) + 1 := by
    rcases zmod2_cases p (parZ (pick a b)) with h | h
    · exact absurd h.symm hp
    · exact h
  have hfilter : univ.filter
      (fun i => Function.update (pick a b) i₀ (!(pick a b i₀)) i
        ≠ pick a b i) = {i₀} := by
    ext j
    by_cases hj : j = i₀ <;> simp [hj, Function.update_apply]
  constructor
  · refine ⟨Function.update (pick a b) i₀ (!(pick a b i₀)), ?_, ?_⟩
    · rw [parZ_eq_add_card_diff, hfilter, hp']
      simp
    · rw [cost_eq, hfilter]
      simp
  · rintro c ⟨t, ht, rfl⟩
    rw [cost_eq]
    set D := univ.filter (fun i => t i ≠ pick a b i) with hD
    have hcard : ((D.card : ZMod 2)) = 1 := by
      have hpar := parZ_eq_add_card_diff a b t
      rw [ht, hp'] at hpar
      exact (add_right_injective _ hpar).symm
    have hne : D.Nonempty := by
      rcases Finset.eq_empty_or_nonempty D with h | h
      · rw [h] at hcard; simp at hcard
      · exact h
    obtain ⟨j, hj⟩ := hne
    have h1 : gap a b j ≤ ∑ i ∈ D, gap a b i :=
      Finset.single_le_sum (fun i _ => gap_nonneg a b i) hj
    have h2 := hi₀ j
    linarith

/-- The least gap the previous theorem asks for always exists. -/
theorem exists_least_gap (hn : 0 < n) :
    ∃ i₀ : Fin n, ∀ i, gap a b i₀ ≤ gap a b i := by
  have hne : (univ : Finset (Fin n)).Nonempty := by
    rw [Finset.univ_nonempty_iff]
    exact Fin.pos_iff_nonempty.mp hn
  obtain ⟨i₀, _, hmin⟩ := Finset.exists_min_image univ (gap a b) hne
  exact ⟨i₀, fun i => hmin i (Finset.mem_univ i)⟩

/-! ## 3.  A class holds `2 ^ (n - 1)` choices -/

/-- Flipping one top bit flips the parity. -/
theorem parZ_update (t : Fin n → Bool) (i : Fin n) :
    parZ (Function.update t i (!t i)) = parZ t + 1 := by
  unfold parZ
  rw [← Finset.add_sum_erase univ _ (Finset.mem_univ i),
      ← Finset.add_sum_erase univ (fun j => if t j then (1:ZMod 2) else 0)
        (Finset.mem_univ i)]
  have h1 : ∑ j ∈ univ.erase i,
        (if Function.update t i (!t i) j then (1:ZMod 2) else 0)
      = ∑ j ∈ univ.erase i, (if t j then (1:ZMod 2) else 0) :=
    Finset.sum_congr rfl (fun j hj => by
      have hne : j ≠ i := (Finset.mem_erase.mp hj).1
      simp [hne])
  have h2 : (1 : ZMod 2) + 1 = 0 := by decide
  rw [h1, Function.update_self]
  cases h : t i
  · simp; ring
  · simp
    rw [add_comm (1 : ZMod 2) _, add_assoc, h2, add_zero]

/-- **The class size.**  Half of the `2 ^ n` choices of top bit have each
parity; at `n = 6` that is the table's 32 codewords per class. -/
theorem card_parity_class (hn : 0 < n) (p : ZMod 2) :
    (univ.filter fun t : Fin n → Bool => parZ t = p).card = 2 ^ (n - 1) := by
  classical
  set i₀ : Fin n := ⟨0, hn⟩ with hi₀
  set A := univ.filter fun t : Fin n → Bool => parZ t = p with hA
  set B := univ.filter fun t : Fin n → Bool => parZ t = p + 1 with hB
  have hAB : A.card = B.card := by
    refine Finset.card_bij' (fun t _ => Function.update t i₀ (!t i₀))
      (fun t _ => Function.update t i₀ (!t i₀)) ?_ ?_ ?_ ?_
    · intro t ht
      simp only [hA, hB, Finset.mem_filter, Finset.mem_univ, true_and] at ht ⊢
      rw [parZ_update, ht]
    · intro t ht
      simp only [hA, hB, Finset.mem_filter, Finset.mem_univ, true_and] at ht ⊢
      rw [parZ_update, ht, zmod2_succ_succ]
    · intro t _
      funext j
      by_cases hj : j = i₀ <;> simp [hj, Function.update_apply]
    · intro t _
      funext j
      by_cases hj : j = i₀ <;> simp [hj, Function.update_apply]
  have hdisj : Disjoint A B := by
    rw [Finset.disjoint_left]
    intro t htA htB
    simp only [hA, hB, Finset.mem_filter] at htA htB
    exact zmod2_ne_succ p (htA.2 ▸ htB.2)
  have hunion : A ∪ B = univ := by
    ext t
    simp only [hA, hB, Finset.mem_union, Finset.mem_filter, Finset.mem_univ,
      true_and, iff_true]
    exact zmod2_cases (parZ t) p
  have hcard : A.card + B.card = 2 ^ n := by
    have hu := Finset.card_union_of_disjoint hdisj
    rw [hunion] at hu
    rw [← hu, Finset.card_univ]
    simp
  rw [hAB] at hcard
  have h2 : (2:ℕ) ^ n = 2 * 2 ^ (n - 1) := by
    cases n with
    | zero => omega
    | succ k => simp [pow_succ]; ring
  omega

/-! ## 4.  Why the search may stop early -/

section BoundedSearch

variable {α : Type*}

/-- **Branch and bound is exact.**  `f` is a lower bound for `g` — in the
decoder, the cost before the `±4` repair for the cost after it, the repair
being nonnegative.  If the incumbent `w` is best among the expanded part `E`,
and every unexpanded member of `S` already reaches `g w` under the *bound*,
then `w` is best in the whole of `S`: the classes never opened contained
nothing better. -/
theorem isLeast_of_bounded_search (S E : Finset α) (f g : α → ℚ)
    (hE : E ⊆ S) (hfg : ∀ x ∈ S, f x ≤ g x)
    (w : α) (hw : w ∈ E) (hbest : ∀ x ∈ E, g w ≤ g x)
    (hrest : ∀ x ∈ S, x ∉ E → g w ≤ f x) :
    IsLeast {c | ∃ x ∈ S, g x = c} (g w) := by
  refine ⟨⟨w, hE hw, rfl⟩, ?_⟩
  rintro c ⟨x, hx, rfl⟩
  by_cases hxE : x ∈ E
  · exact hbest x hxE
  · exact le_trans (hrest x hx hxE) (hfg x hx)

end BoundedSearch

end GLM.LLVQ
