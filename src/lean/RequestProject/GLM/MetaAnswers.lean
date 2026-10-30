module

public import Mathlib

/-!
# The mathematics behind the meta answers (Phase 117, track M)

`studies/META_QUESTIONS_STUDY.md` answers the eighteen outside questions
about the GLM's own engineering from the project's own documents.  Most of
those answers quote a study and cite a theorem already in this development
(`GLM.GolayBoundary`, `GLM.Steiner`, `GLM.IntegerDecision`,
`GLM.ConnectedMachine`).  Five of the questions ask for a mathematical fact
that no earlier file proved; this file proves them, so that the answer the
machine gives rests on a theorem rather than on prose.

* **Distance bounds without square roots** (outside question 100):
  `euclid_le_iff` and `euclid_lt_iff` — for rational points `x`, `y` and a
  rational bound `r ≥ 0`, the Euclidean distance `√(Σ (xᵢ - yᵢ)²)` is at most
  (below) `r` exactly when the rational number `Σ (xᵢ - yᵢ)²` is at most
  (below) `r²`; `euclid_le_euclid_iff` compares two distances the same way.
* **Threshold crossings of `v = √(2gh)`** (outside question 91):
  `torricelli_crossing` — for a critical speed `v ≥ 0`, `v < √(2gh)` exactly
  when `v² < 2gh`, an inequality between rationals when `g`, `h` and `v` are.
* **Rotations with rational entries** (outside question 102): for a rational
  skew-symmetric matrix `A`, `1 - A` is invertible
  (`isUnit_det_one_sub_of_skew`) and the Cayley transform
  `(1 + A)(1 - A)⁻¹` is orthogonal (`cayley_orthogonal`) with determinant 1
  (`cayley_det`): a rotation whose entries are rational.
* **Lattice automorphisms are rational** (outside question 98):
  `lattice_map_rational` — a real matrix that sends a rational basis to
  integer combinations of itself has rational entries.  The automorphisms of
  the Leech lattice are of this kind, since the lattice has a rational basis.
* **Inverse certificates** (outside questions 97 and 110):
  `inverse_of_certificate` — a matrix `B` with `A * B = 1` *is* `A⁻¹`, so a
  claimed inverse is checked by one exact multiplication; `certificate_example`
  checks a 3 × 3 rational inverse that way.
-/

@[expose] public section

namespace GLM.MetaAnswers

open Matrix

/-! ## Distances compared by their squares -/

/-- The squared Euclidean distance between two rational points: a rational
number, so it can be compared exactly. -/
def sqDist {n : ℕ} (x y : Fin n → ℚ) : ℚ := ∑ i, (x i - y i) ^ 2

theorem sqDist_nonneg {n : ℕ} (x y : Fin n → ℚ) : 0 ≤ sqDist x y :=
  Finset.sum_nonneg fun _ _ => sq_nonneg _

/-- A distance bound is the bound on the squared distance: no square root is
taken. -/
theorem euclid_le_iff {n : ℕ} (x y : Fin n → ℚ) {r : ℚ} (hr : 0 ≤ r) :
    Real.sqrt (sqDist x y : ℝ) ≤ r ↔ sqDist x y ≤ r ^ 2 := by
  rw [Real.sqrt_le_left (by exact_mod_cast hr)]
  exact_mod_cast Iff.rfl

/-- The strict form of `euclid_le_iff`. -/
theorem euclid_lt_iff {n : ℕ} (x y : Fin n → ℚ) {r : ℚ} (hr : 0 ≤ r) :
    Real.sqrt (sqDist x y : ℝ) < r ↔ sqDist x y < r ^ 2 := by
  constructor
  · intro h
    have h0 : (0 : ℝ) ≤ Real.sqrt (sqDist x y : ℝ) := Real.sqrt_nonneg _
    have hpos : (0 : ℝ) < r := lt_of_le_of_lt h0 h
    have := (Real.sqrt_lt' hpos).1 h
    exact_mod_cast this
  · intro h
    have hr' : (0 : ℝ) ≤ r := by exact_mod_cast hr
    rcases hr'.lt_or_eq with hpos | hzero
    · exact (Real.sqrt_lt' hpos).2 (by exact_mod_cast h)
    · exfalso
      have : (r : ℚ) = 0 := by exact_mod_cast hzero.symm
      rw [this] at h
      have := sqDist_nonneg x y
      nlinarith

/-- Two distances compare as their squares do. -/
theorem euclid_le_euclid_iff {n : ℕ} (x y u v : Fin n → ℚ) :
    Real.sqrt (sqDist x y : ℝ) ≤ Real.sqrt (sqDist u v : ℝ) ↔
      sqDist x y ≤ sqDist u v := by
  rw [Real.sqrt_le_sqrt_iff (by exact_mod_cast sqDist_nonneg u v)]
  exact_mod_cast Iff.rfl

/-! ## Torricelli's speed against a threshold -/

/-- `v < √(2gh)` is the rational inequality `v² < 2gh`, for `v ≥ 0`. -/
theorem torricelli_crossing {g h v : ℚ} (hv : 0 ≤ v) :
    (v : ℝ) < Real.sqrt (2 * g * h) ↔ v ^ 2 < 2 * g * h := by
  rw [Real.lt_sqrt (by exact_mod_cast hv)]
  exact_mod_cast Iff.rfl

/-! ## Rational rotations: the Cayley transform -/

variable {ι : Type*} [Fintype ι] [DecidableEq ι]

omit [DecidableEq ι] in
/-- For a skew-symmetric rational matrix, `v ⬝ (A v) = 0`. -/
theorem dot_mulVec_self_of_skew {A : Matrix ι ι ℚ} (hA : Aᵀ = -A) (v : ι → ℚ) :
    v ⬝ᵥ (A *ᵥ v) = 0 := by
  have h1 : v ⬝ᵥ (A *ᵥ v) = (Aᵀ *ᵥ v) ⬝ᵥ v := by
    rw [dotProduct_mulVec, ← vecMul_transpose, transpose_transpose]
  rw [hA, neg_mulVec, neg_dotProduct, dotProduct_comm] at h1
  have h2 : (A *ᵥ v) ⬝ᵥ v = 0 := by linarith
  rw [dotProduct_comm]
  exact h2

/-- `1 - A` is invertible when `A` is a rational skew-symmetric matrix. -/
theorem isUnit_det_one_sub_of_skew {A : Matrix ι ι ℚ} (hA : Aᵀ = -A) :
    IsUnit (1 - A).det := by
  rw [isUnit_iff_ne_zero]
  intro hdet
  obtain ⟨v, hv, hAv⟩ := (exists_mulVec_eq_zero_iff).2 hdet
  have hfix : v = A *ᵥ v := by
    rw [sub_mulVec, one_mulVec, sub_eq_zero] at hAv
    exact hAv
  have h0 : v ⬝ᵥ v = 0 := by
    conv_lhs => rw [show v ⬝ᵥ v = v ⬝ᵥ (A *ᵥ v) from by rw [← hfix]]
    exact dot_mulVec_self_of_skew hA v
  exact hv (dotProduct_self_eq_zero.1 h0)

/-- `1 + A` is invertible too (apply the above to `-A`). -/
theorem isUnit_det_one_add_of_skew {A : Matrix ι ι ℚ} (hA : Aᵀ = -A) :
    IsUnit (1 + A).det := by
  have h := isUnit_det_one_sub_of_skew (A := -A) (by rw [transpose_neg, hA])
  simpa [sub_neg_eq_add] using h

/-- The Cayley transform of `A`. -/
noncomputable def cayley (A : Matrix ι ι ℚ) : Matrix ι ι ℚ := (1 + A) * (1 - A)⁻¹

/-- The Cayley transform of a rational skew-symmetric matrix is orthogonal. -/
theorem cayley_orthogonal {A : Matrix ι ι ℚ} (hA : Aᵀ = -A) :
    (cayley A)ᵀ * cayley A = 1 := by
  have hs := isUnit_det_one_sub_of_skew hA
  have ha := isUnit_det_one_add_of_skew hA
  have hT : (cayley A)ᵀ = (1 + A)⁻¹ * (1 - A) := by
    unfold cayley
    rw [transpose_mul, transpose_nonsing_inv, transpose_sub, transpose_add,
      transpose_one, hA, sub_neg_eq_add, ← sub_eq_add_neg]
  have hcomm : (1 - A) * (1 + A) = (1 + A) * (1 - A) := by
    simp only [sub_mul, mul_add, add_mul, mul_sub, one_mul, mul_one]
    abel
  rw [hT]
  unfold cayley
  calc (1 + A)⁻¹ * (1 - A) * ((1 + A) * (1 - A)⁻¹)
      = (1 + A)⁻¹ * ((1 - A) * (1 + A)) * (1 - A)⁻¹ := by
        simp only [Matrix.mul_assoc]
    _ = (1 + A)⁻¹ * (1 + A) * ((1 - A) * (1 - A)⁻¹) := by
        rw [hcomm]; simp only [Matrix.mul_assoc]
    _ = 1 := by
        rw [nonsing_inv_mul _ ha, mul_nonsing_inv _ hs, Matrix.one_mul]

/-- The Cayley transform of a rational skew-symmetric matrix has determinant
1: it is a rotation, not a reflection. -/
theorem cayley_det {A : Matrix ι ι ℚ} (hA : Aᵀ = -A) : (cayley A).det = 1 := by
  have hs := isUnit_det_one_sub_of_skew hA
  have hdet : (1 + A).det = (1 - A).det := by
    rw [← det_transpose (1 + A), transpose_add, transpose_one, hA,
      ← sub_eq_add_neg]
  unfold cayley
  rw [det_mul, det_nonsing_inv, hdet, Ring.inverse_eq_inv',
    mul_inv_cancel₀ (isUnit_iff_ne_zero.1 hs)]

/-! ## Lattice automorphisms are rational -/

/-- A real matrix `g` that sends the columns of a rational basis `B` to integer
combinations of them (`g B = B M`, `M` an integer matrix) has rational entries:
it is `B M B⁻¹`, mapped into the reals. -/
theorem lattice_map_rational {g : Matrix ι ι ℝ} {B : Matrix ι ι ℚ}
    {M : Matrix ι ι ℤ} (hB : IsUnit B.det)
    (h : g * B.map (Rat.cast : ℚ → ℝ) =
      (B * M.map (Int.cast : ℤ → ℚ)).map (Rat.cast : ℚ → ℝ)) :
    g = (B * M.map (Int.cast : ℤ → ℚ) * B⁻¹).map (Rat.cast : ℚ → ℝ) := by
  set f : ℚ →+* ℝ := Rat.castHom ℝ
  have hBR : IsUnit (B.map f).det := by
    have hm : (B.map f).det = f B.det := (RingHom.map_det f B).symm
    rw [hm]
    exact hB.map f
  have key : (B * M.map (Int.cast : ℤ → ℚ) * B⁻¹).map f * B.map f =
      (B * M.map (Int.cast : ℤ → ℚ)).map f := by
    rw [← Matrix.map_mul, Matrix.mul_assoc, nonsing_inv_mul _ hB, Matrix.mul_one]
  have h' : g * B.map f = (B * M.map (Int.cast : ℤ → ℚ)).map f := h
  have hcancel : g = (B * M.map (Int.cast : ℤ → ℚ) * B⁻¹).map f := by
    calc g = g * B.map f * (B.map f)⁻¹ := by
            rw [Matrix.mul_assoc, mul_nonsing_inv _ hBR, Matrix.mul_one]
      _ = (B * M.map (Int.cast : ℤ → ℚ) * B⁻¹).map f * B.map f * (B.map f)⁻¹ := by
            rw [h', key]
      _ = (B * M.map (Int.cast : ℤ → ℚ) * B⁻¹).map f := by
            rw [Matrix.mul_assoc, mul_nonsing_inv _ hBR, Matrix.mul_one]
  exact hcancel

/-! ## Inverse certificates -/

/-- A claimed inverse is checked by one exact multiplication. -/
theorem inverse_of_certificate {A B : Matrix ι ι ℚ} (h : A * B = 1) : A⁻¹ = B :=
  inv_eq_right_inv h

/-- The template on a 3 × 3 rational matrix: the certificate `A * B = 1` is
checked by exact arithmetic, and the theorem turns it into `A⁻¹ = B`. -/
theorem certificate_example :
    (!![2, 1, 0; 1, 2, 1; 0, 1, 2] : Matrix (Fin 3) (Fin 3) ℚ)⁻¹ =
      !![3/4, -1/2, 1/4; -1/2, 1, -1/2; 1/4, -1/2, 3/4] := by
  apply inverse_of_certificate
  rw [Matrix.mul_fin_three]
  ext i j
  fin_cases i <;> fin_cases j <;> norm_num

end GLM.MetaAnswers
