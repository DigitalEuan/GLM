module

public import Mathlib

/-!
# Native parity: what a refined native ranking can and cannot gain

`studies/NATIVE_PARITY_STUDY.md` (Phase 70) keeps the GLM's native methods
where a standard method ties or narrowly beats them, and refines them.  The
computational half is `overlay/glm_universal/reasoning/native_parity.py`.  This
file is the half that is a theorem, and it says exactly where a refinement of a
ranking can gain and where it cannot.

## 1.  A refinement only reorders inside ties

`sortedBy_map_primary_eq`: two lists that are permutations of one another and
are both sorted by the same integer cost list the *same sequence of costs*,
whatever else they were sorted by.  `take_map_primary_eq` is the retrieval
reading: the top `k` of any two such rankings have the same costs, so they can
differ only in *which* candidates fill a tie of the cost at the boundary.
`sorted_primary_of_sorted_lex` says a ranking by a lexicographic key (the
native ranking's read-back distance, then Leech distance, then name) is sorted
by its first component, so the theorem applies to it.

## 2.  The read-back is exact

`readbackCoord` is the integer rounding the running system uses — divide by
the scale, round half away from zero, sign-magnitude — and
`readbackCoord_eq` proves it returns the feature coordinate whenever the
quantiser moved the scaled coordinate by at most `ρ` and `2ρ < s`.  With the
Leech lattice's covering radius `ρ = 4` in the integer model and `s = 9`, every
address reads back to its feature vector (`readback_eq`), which is what makes
the read-back distance a native reading of the address rather than a second
copy of the features.

## 3.  The residue carries nothing about the query

`residue_congr`: the quantisation residue `Q(s·f) − s·f` is a function of `f`.
So breaking a tie of the read-back distance by the raw Leech distance orders
the tied candidates by something no more informative about the query than the
alphabet — round one's measured wash — and a tie-break that is to gain must
read another book.

## 4.  Where the raw Leech distance can and cannot disagree

`order_agrees_of_gap`: if `z` is farther from `x` than `y` is by more than
`4ρ`, the addresses keep that order.  The raw address ranking can therefore
only depart from the feature ranking on comparisons within `4ρ` of a tie;
scaled by `s`, that is a feature gap of `4ρ/s`.
-/

@[expose] public section

namespace GLM.NativeParity

/-! ## 1.  A refinement only reorders inside ties -/

section Ties

variable {α : Type*}

/-- **Two rankings by the same cost list the same costs.**  If `l₁` and `l₂`
hold the same candidates and each is sorted by the integer cost `c` — however
each broke its ties — then they list the same sequence of costs. -/
theorem sortedBy_map_primary_eq (c : α → ℤ) {l₁ l₂ : List α}
    (hperm : l₁.Perm l₂)
    (h₁ : l₁.Pairwise (fun a b => c a ≤ c b))
    (h₂ : l₂.Pairwise (fun a b => c a ≤ c b)) :
    l₁.map c = l₂.map c :=
  List.Perm.eq_of_pairwise (le := (· ≤ ·)) (fun _ _ _ _ h1 h2 => le_antisymm h1 h2)
    (List.pairwise_map.mpr h₁) (List.pairwise_map.mpr h₂) (hperm.map c)

/-- **The top `k` of two such rankings have the same costs.**  A native
tie-break and a standard one can disagree only on which candidates fill a tie
of the cost; they never disagree on how far away the `k`-th candidate is. -/
theorem take_map_primary_eq (c : α → ℤ) {l₁ l₂ : List α} (k : ℕ)
    (hperm : l₁.Perm l₂)
    (h₁ : l₁.Pairwise (fun a b => c a ≤ c b))
    (h₂ : l₂.Pairwise (fun a b => c a ≤ c b)) :
    (l₁.take k).map c = (l₂.take k).map c := by
  rw [List.map_take, List.map_take, sortedBy_map_primary_eq c hperm h₁ h₂]

/-- **A lexicographic ranking is sorted by its first key.**  Any order `R`
that never puts a costlier candidate first — the native key (read-back
distance, Leech distance, name) is one — sorts by the cost. -/
theorem sorted_primary_of_sorted_lex (c : α → ℤ) {R : α → α → Prop}
    (hR : ∀ a b, R a b → c a ≤ c b) {l : List α} (h : l.Pairwise R) :
    l.Pairwise (fun a b => c a ≤ c b) :=
  h.imp (hR _ _)

/-- The native key compared lexicographically never puts a costlier read-back
first. -/
theorem lex_fst_le {a b : ℤ × ℤ} (h : toLex a ≤ toLex b) : a.1 ≤ b.1 := by
  rcases (Prod.Lex.le_iff).mp h with h' | ⟨h', _⟩
  · exact le_of_lt h'
  · exact le_of_eq h'

end Ties

/-! ## 2.  The read-back is exact -/

/-- One coordinate read back from an address at scale `s`: the magnitude
divided by `s` and rounded half away from zero, then signed — exactly
`lean_address.describe_address` and `controller.readback_of`. -/
def readbackCoord (s p : ℤ) : ℤ :=
  if p < 0 then -((2 * (-p) + s) / (2 * s)) else (2 * p + s) / (2 * s)

/-- The read-back of a whole address. -/
def readback {n : ℕ} (s : ℤ) (p : Fin n → ℤ) : Fin n → ℤ :=
  fun i => readbackCoord s (p i)

/-- Rounding a magnitude: if `|q − s·m| ≤ ρ` and `2ρ < s`, then
`(2q + s) / (2s) = m`.  No sign condition is needed. -/
theorem round_magnitude {s ρ q m : ℤ} (hs : 2 * ρ < s)
    (h : |q - s * m| ≤ ρ) : (2 * q + s) / (2 * s) = m := by
  have h' := abs_le.mp h
  have hspos : 0 < 2 * s := by omega
  rw [Int.ediv_eq_iff_of_pos hspos]
  constructor <;> nlinarith [h'.1, h'.2]

/-- **The read-back is exact.**  If the quantiser moved the scaled coordinate
`s·f` by at most `ρ`, and `2ρ < s`, the read-back is `f`. -/
theorem readbackCoord_eq {s ρ p f : ℤ} (hs : 2 * ρ < s)
    (h : |p - s * f| ≤ ρ) : readbackCoord s p = f := by
  unfold readbackCoord
  split_ifs with hp
  · have h2 : |(-p) - s * (-f)| ≤ ρ := by
      rw [show (-p) - s * (-f) = -(p - s * f) by ring, abs_neg]; exact h
    rw [round_magnitude hs h2]; ring
  · exact round_magnitude hs h

/-- **Every address reads back to its features.**  With the Leech covering
radius `ρ = 4` and the shipped scale `s = 9`, as in the running system. -/
theorem readback_eq {n : ℕ} {s ρ : ℤ} (hs : 2 * ρ < s)
    (p f : Fin n → ℤ) (h : ∀ i, |p i - s * f i| ≤ ρ) :
    readback s p = f :=
  funext fun i => readbackCoord_eq hs (h i)

/-- The shipped instance: covering radius 4, scale 9. -/
theorem readback_eq_leech {n : ℕ} (p f : Fin n → ℤ)
    (h : ∀ i, |p i - 9 * f i| ≤ 4) : readback 9 p = f :=
  readback_eq (ρ := 4) (by norm_num) p f h

/-! ## 3.  The residue carries nothing about the query -/

/-- **The residue is a function of the features.**  Equal feature vectors
have equal quantisation residues, so the raw Leech distance, used as a
tie-break inside a tie of the read-back distance, reads nothing the features
did not already fix. -/
theorem residue_congr {X : Type*} [AddCommGroup X] (quantise scale : X → X)
    {f g : X} (h : f = g) :
    quantise (scale f) - scale f = quantise (scale g) - scale g := by
  subst h; rfl

/-! ## 4.  Where the raw Leech distance can and cannot disagree -/

/-- **A comparison with a gap of more than `4ρ` survives quantisation.**  If
`z` is farther from `x` than `y` is, by more than `4ρ`, the address of `z` is
farther from the address of `x` than the address of `y` is. -/
theorem order_agrees_of_gap {X : Type*} [MetricSpace X] {ρ : ℝ}
    (q : X → X) (close : ∀ w, dist w (q w) ≤ ρ) {x y z : X}
    (h : dist x y + 4 * ρ < dist x z) :
    dist (q x) (q y) < dist (q x) (q z) := by
  have hx := close x
  have hy := close y
  have hz := close z
  have up : dist (q x) (q y) ≤ dist x y + 2 * ρ := by
    calc dist (q x) (q y) ≤ dist (q x) x + dist x (q y) := dist_triangle _ _ _
      _ ≤ dist (q x) x + (dist x y + dist y (q y)) := by
          gcongr; exact dist_triangle _ _ _
      _ ≤ ρ + (dist x y + ρ) := by rw [dist_comm (q x) x]; gcongr
      _ = dist x y + 2 * ρ := by ring
  have tri : dist x z ≤ dist x (q x) + dist (q x) (q z) + dist (q z) z := by
    calc dist x z ≤ dist x (q z) + dist (q z) z := dist_triangle _ _ _
      _ ≤ dist x (q x) + dist (q x) (q z) + dist (q z) z := by
          gcongr; exact dist_triangle _ _ _
  rw [dist_comm (q z) z] at tri
  linarith

/-! ## 5.  Worked instances, by computation -/

/-- A coordinate `9·3 + 4` reads back to `3`; `9·(−2) − 4` to `−2`; `3` to `0`. -/
theorem readback_examples :
    readbackCoord 9 31 = 3 ∧ readbackCoord 9 (-22) = -2 ∧ readbackCoord 9 3 = 0 := by
  decide

end GLM.NativeParity
