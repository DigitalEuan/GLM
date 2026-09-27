/-
# Past 24: the 32- and 48-dimensional constructions, and their addresses

The spatial layer of this development stops at the Leech lattice: 24
coordinates, minimum 4, kissing number 196,560.  The next even unimodular
*extremal* lattice lives in 32 dimensions, and the one after that in 48, and
this file proves the two facts a machine actually needs about them — how short
their vectors can be, and how a point is addressed at several resolutions at
once.

Nothing here mentions a particular code.  Both sections are stated for an
arbitrary code with the weight properties the construction uses, so the Python
side is free to supply Reed–Muller, Golay, quadratic-residue or Pless codes and
inherit the theorem.

## 32 dimensions: Construction D, and the three-level address

A Barnes–Wall vector is `x = 4a + 2b + c` with `c` a codeword of the *outer*
code `C₂` (all weights divisible by 16), `b` a codeword of the *inner* code `C₁`
(all weights divisible by 4, minimum weight 4), and `a` an arbitrary integer
vector.  In 32 coordinates `C₂ = RM(1,5)` and `C₁ = RM(3,5)`, and dividing the
whole lattice by 2 makes it even unimodular with minimum 4 — extremal.

* `norm_ge_of_ne_zero` — **the minimum.**  Every nonzero vector has
  `∑ xᵢ² ≥ 16`, i.e. norm 4 after the scaling.  The proof is a three-way case
  split on which resolution the vector is first visible at, and each case is
  forced by a different property of the codes: a coordinate carrying a `c`-bit
  is odd, a coordinate carrying a `b`-bit is `≡ 2 (mod 4)`, and a coordinate
  carrying only an `a`-bit is divisible by 4.
* `norm_dvd_eight` — **evenness.**  `8 ∣ ∑ xᵢ²`, which is what makes the scaled
  lattice even.  This is where the *duality* of the two codes does the work:
  the term that survives mod 8 is `4·|b ∧ c|`, and `|b ∧ c|` is even exactly
  because `C₂ ⊆ C₁^⊥`.
* `mk_injective` — **the address is unique.**  A point determines its three
  levels `(c, b, a)` and nothing else does; `mk_emod_two` and `mk_emod_four`
  say the two coarse levels are read off by reducing mod 2 and mod 4.  That is
  the multi-resolution addressing the construction buys: a coarse address in
  `C₂`, a middle address in `C₁`, a fine address in `ℤ³²`, each a quotient of
  the one below.

## 48 dimensions: why the even part of a ternary construction reaches 6

Over `ℤ⁴⁸` with a self-dual ternary code of minimum weight 15, Construction A
gives a unimodular lattice of minimum 3 — odd, and therefore not the thing one
wants.  Its **even sublattice** is the interesting object, and
`even_norm_ge_eighteen` proves what it is worth: every nonzero vector of it has
`∑ xᵢ² ≥ 18`, that is, norm 6 after the scaling by `1/3`.  Six is the extremal
minimum in 48 dimensions.

The argument is again a case split by resolution, and again each case is closed
by a different property: off the code the weight bound gives `∑ xᵢ² ≥ 15`, and
on the code every coordinate is a multiple of 3 so `∑ xᵢ² ` is a multiple of 9.
Evenness then rules out the two odd values `15` and `9` that would otherwise be
in the way.
-/
import Mathlib

namespace GLM.HigherLattices

open Finset

/-! ## 1.  Construction D in 32 dimensions -/

namespace BarnesWall

variable {n : ℕ}

/-- A `0/1` vector, which is how a binary codeword enters an integer lattice. -/
def IsBinary (c : Fin n → ℤ) : Prop := ∀ i, c i = 0 ∨ c i = 1

/-- The Hamming weight of a `0/1` vector. -/
def wt (c : Fin n → ℤ) : ℕ := #{i | c i = 1}

/-- The size of the overlap of two `0/1` vectors — their inner product over
`F₂` is its parity. -/
def meetWt (b c : Fin n → ℤ) : ℕ := #{i | b i = 1 ∧ c i = 1}

/-- The Construction-D vector `4a + 2b + c`. -/
def mk (a b c : Fin n → ℤ) : Fin n → ℤ := fun i => 4 * a i + 2 * b i + c i

/-- The squared length in the unscaled model; the lattice norm is this over 4. -/
def nrm (x : Fin n → ℤ) : ℤ := ∑ i, (x i) ^ 2

/-- A `0/1` vector sums to its weight. -/
theorem sum_binary {c : Fin n → ℤ} (hc : IsBinary c) : ∑ i, c i = (wt c : ℤ) := by
  classical
  rw [wt, Finset.card_filter]
  push_cast
  exact Finset.sum_congr rfl fun i _ => by rcases hc i with h | h <;> simp [h]

/-- Two `0/1` vectors have coordinatewise product summing to their overlap. -/
theorem sum_meet {b c : Fin n → ℤ} (hb : IsBinary b) (hc : IsBinary c) :
    ∑ i, b i * c i = (meetWt b c : ℤ) := by
  classical
  rw [meetWt, Finset.card_filter]
  push_cast
  exact Finset.sum_congr rfl fun i _ => by
    rcases hb i with h | h <;> rcases hc i with h2 | h2 <;> simp [h, h2]

/-- The coarse address is read off by reducing mod 2. -/
theorem mk_emod_two {a b c : Fin n → ℤ} (hc : IsBinary c) (i : Fin n) :
    (mk a b c i) % 2 = c i := by
  rcases hc i with h | h <;> simp only [mk, h] <;> omega

/-- The middle address is read off by reducing mod 4, once the coarse one is
subtracted. -/
theorem mk_emod_four {a b c : Fin n → ℤ} (hb : IsBinary b) (i : Fin n) :
    (mk a b c i - c i) % 4 = 2 * b i := by
  rcases hb i with h | h <;> simp only [mk, h] <;> omega

/-- **The address is unique**: a lattice point determines its three levels. -/
theorem mk_injective {a b c a' b' c' : Fin n → ℤ}
    (hb : IsBinary b) (hc : IsBinary c) (hb' : IsBinary b') (hc' : IsBinary c')
    (h : mk a b c = mk a' b' c') : a = a' ∧ b = b' ∧ c = c' := by
  have key : ∀ i, a i = a' i ∧ b i = b' i ∧ c i = c' i := by
    intro i
    have h' := congrFun h i
    simp only [mk] at h'
    rcases hb i with h1 | h1 <;> rcases hc i with h2 | h2 <;>
      rcases hb' i with h3 | h3 <;> rcases hc' i with h4 | h4 <;>
      rw [h1, h2, h3, h4] at h' ⊢ <;> omega
  exact ⟨funext fun i => (key i).1, funext fun i => (key i).2.1,
    funext fun i => (key i).2.2⟩

/-- A set of coordinates on which every square is at least `k` forces that much
squared length. -/
theorem card_mul_le_nrm (s : Finset (Fin n)) (x : Fin n → ℤ) (k : ℤ)
    (h : ∀ i ∈ s, k ≤ (x i) ^ 2) : (s.card : ℤ) * k ≤ nrm x := by
  calc (s.card : ℤ) * k = ∑ _i ∈ s, k := by simp [mul_comm]
    _ ≤ ∑ i ∈ s, (x i) ^ 2 := Finset.sum_le_sum h
    _ ≤ ∑ i, (x i) ^ 2 := by
        refine Finset.sum_le_sum_of_subset_of_nonneg (Finset.subset_univ s) ?_
        intro i _ _
        positivity

/-- **The minimum.**  With an outer code of minimum weight 16 and an inner code
of minimum weight 4, every nonzero Construction-D vector has squared length at
least 16 — minimum 4 after the scaling.  Three cases, one per resolution: a
coordinate carrying a `c`-bit is odd, a coordinate carrying a `b`-bit is
`≡ 2 (mod 4)`, and a coordinate carrying only an `a`-bit is divisible by 4. -/
theorem norm_ge_of_ne_zero {a b c : Fin n → ℤ}
    (hcw : c ≠ 0 → 16 ≤ wt c) (hbw : b ≠ 0 → 4 ≤ wt b)
    (hx : mk a b c ≠ 0) : 16 ≤ nrm (mk a b c) := by
  classical
  by_cases hc0 : c = 0
  · by_cases hb0 : b = 0
    · have ha : a ≠ 0 := by
        intro h
        apply hx
        funext i
        simp [mk, h, hb0, hc0]
      obtain ⟨i, hi⟩ := Function.ne_iff.mp ha
      have h1 : (16 : ℤ) ≤ (mk a b c i) ^ 2 := by
        have hmk : mk a b c i = 4 * a i := by simp [mk, hb0, hc0]
        rw [hmk]
        have : (1 : ℤ) ≤ (a i) ^ 2 := by
          rcases lt_or_gt_of_ne (show a i ≠ 0 by simpa using hi) with h | h <;> nlinarith
        nlinarith
      have h2 := card_mul_le_nrm {i} (mk a b c) 16 (by
        intro j hj
        simp only [Finset.mem_singleton] at hj
        subst hj
        exact h1)
      simpa using h2
    · have hwt : (wt b : ℤ) = ((({i | b i = 1} : Finset (Fin n)).card : ℤ)) := rfl
      have hset : ∀ i ∈ ({i | b i = 1} : Finset (Fin n)), (4 : ℤ) ≤ (mk a b c i) ^ 2 := by
        intro i hi
        simp only [Finset.mem_filter, Finset.mem_univ, true_and] at hi
        have hci : c i = 0 := by rw [hc0]; rfl
        have hmk : mk a b c i = 4 * a i + 2 := by simp [mk, hi, hci]
        rw [hmk]
        rcases le_or_gt (a i) (-1) with h | h
        · nlinarith
        · have h0 : 0 ≤ a i := by omega
          nlinarith
      have hcard := card_mul_le_nrm ({i | b i = 1} : Finset (Fin n)) (mk a b c) 4 hset
      have h4 : (4 : ℤ) ≤ (wt b : ℤ) := by exact_mod_cast hbw hb0
      calc (16:ℤ) ≤ (wt b : ℤ) * 4 := by linarith
        _ = ((({i | b i = 1} : Finset (Fin n)).card : ℤ)) * 4 := by rw [hwt]
        _ ≤ nrm (mk a b c) := hcard
  · have hwt : (wt c : ℤ) = ((({i | c i = 1} : Finset (Fin n)).card : ℤ)) := rfl
    have hset : ∀ i ∈ ({i | c i = 1} : Finset (Fin n)), (1 : ℤ) ≤ (mk a b c i) ^ 2 := by
      intro i hi
      simp only [Finset.mem_filter, Finset.mem_univ, true_and] at hi
      have hne : mk a b c i ≠ 0 := by
        simp only [mk, hi]
        omega
      rcases lt_or_gt_of_ne hne with h | h <;> nlinarith
    have hcard := card_mul_le_nrm ({i | c i = 1} : Finset (Fin n)) (mk a b c) 1 hset
    have h16 : (16 : ℤ) ≤ (wt c : ℤ) := by exact_mod_cast hcw hc0
    calc (16:ℤ) ≤ (wt c : ℤ) := h16
      _ = ((({i | c i = 1} : Finset (Fin n)).card : ℤ)) * 1 := by rw [hwt]; ring
      _ ≤ nrm (mk a b c) := hcard

/-- **Evenness.**  Weights divisible by 16 in the outer code, by 4 in the inner
code, and an even overlap between the two — which is exactly `C₂ ⊆ C₁^⊥` — make
every squared length divisible by 8, so the scaled lattice is even. -/
theorem norm_dvd_eight {a b c : Fin n → ℤ}
    (hb : IsBinary b) (hc : IsBinary c)
    (hcw : 16 ∣ wt c) (hbw : 4 ∣ wt b) (hbc : Even (meetWt b c)) :
    (8 : ℤ) ∣ nrm (mk a b c) := by
  classical
  have expand : nrm (mk a b c)
      = 8 * (∑ i, (2 * (a i) ^ 2 + 2 * a i * b i + a i * c i))
        + 4 * (∑ i, b i) + 4 * (∑ i, b i * c i) + (∑ i, c i) := by
    simp only [nrm, mk, Finset.mul_sum, ← Finset.sum_add_distrib]
    refine Finset.sum_congr rfl fun i _ => ?_
    rcases hb i with h1 | h1 <;> rcases hc i with h2 | h2 <;> rw [h1, h2] <;> ring
  rw [expand, sum_binary hc, sum_meet hb hc, sum_binary hb]
  obtain ⟨k, hk⟩ := hcw
  obtain ⟨l, hl⟩ := hbw
  obtain ⟨m, hm⟩ := hbc
  rw [hk, hl, hm]
  push_cast
  ring_nf
  omega

end BarnesWall

/-! ## 2.  The even part of a ternary construction in 48 dimensions -/

namespace Ternary

variable {n : ℕ}

/-- The coordinates at which a vector is not divisible by 3: the support of its
image in the ternary code. -/
def support3 (x : Fin n → ℤ) : Finset (Fin n) := {i | ¬ (3 : ℤ) ∣ x i}

/-- The squared length in the unscaled model; the lattice norm is this over 3. -/
def nrm (x : Fin n → ℤ) : ℤ := ∑ i, (x i) ^ 2

/-- Off the code, the weight bound is a length bound: each coordinate of the
support contributes at least 1. -/
theorem norm_ge_card_support (x : Fin n → ℤ) :
    ((support3 x).card : ℤ) ≤ nrm x := by
  classical
  calc ((support3 x).card : ℤ) = ∑ _i ∈ support3 x, (1:ℤ) := by simp
    _ ≤ ∑ i ∈ support3 x, (x i) ^ 2 := by
        refine Finset.sum_le_sum ?_
        intro i hi
        simp only [support3, Finset.mem_filter, Finset.mem_univ, true_and] at hi
        have hne : x i ≠ 0 := by rintro h; exact hi (by simp [h])
        rcases lt_or_gt_of_ne hne with h | h <;> nlinarith
    _ ≤ nrm x := by
        refine Finset.sum_le_sum_of_subset_of_nonneg (Finset.subset_univ _) ?_
        intro i _ _; positivity

/-- On the code — every coordinate divisible by 3 — the squared length is
divisible by 9. -/
theorem norm_dvd_nine {x : Fin n → ℤ} (h : support3 x = ∅) :
    (9 : ℤ) ∣ nrm x := by
  classical
  refine Finset.dvd_sum ?_
  intro i _
  have h3 : (3:ℤ) ∣ x i := by
    by_contra hcon
    have hmem : i ∈ support3 x := by simp [support3, hcon]
    rw [h] at hmem; simp at hmem
  obtain ⟨y, hy⟩ := h3
  exact ⟨y ^ 2, by rw [hy]; ring⟩

/-- **The even sublattice reaches the extremal minimum.**  With a ternary code
of minimum weight 15, every nonzero vector whose lattice norm `∑xᵢ²/3` is an
even integer has `∑ xᵢ² ≥ 18` — norm 6, which is extremal in 48 dimensions. -/
theorem even_norm_ge_eighteen {x : Fin n → ℤ}
    (hcode : support3 x ≠ ∅ → 15 ≤ (support3 x).card)
    (hx : x ≠ 0) (heven : (6 : ℤ) ∣ nrm x) : 18 ≤ nrm x := by
  classical
  obtain ⟨i, hi⟩ := Function.ne_iff.mp hx
  have hpos : 1 ≤ nrm x := by
    have h1 : (1:ℤ) ≤ (x i) ^ 2 := by
      rcases lt_or_gt_of_ne (show x i ≠ 0 by simpa using hi) with h | h <;> nlinarith
    calc (1:ℤ) ≤ (x i)^2 := h1
      _ ≤ nrm x := by
          refine Finset.single_le_sum (f := fun j => (x j)^2) ?_ (Finset.mem_univ i)
          intro j _; positivity
  by_cases hs : support3 x = ∅
  · obtain ⟨k, hk⟩ := norm_dvd_nine hs
    obtain ⟨l, hl⟩ := heven
    omega
  · have h15 : (15:ℤ) ≤ ((support3 x).card : ℤ) := by exact_mod_cast hcode hs
    have hge := norm_ge_card_support x
    obtain ⟨l, hl⟩ := heven
    omega

end Ternary

end GLM.HigherLattices
