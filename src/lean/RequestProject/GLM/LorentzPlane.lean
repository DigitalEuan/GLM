import Mathlib

/-!
# The Lorentz plane: boosts, rotations and the Thomas–Wigner split (Phase 178, part B)

*Created 22 October 2026. Rebuilt 15 November 2026 (Phase 190) from
`studies/COLOUR_INDUCTION_STUDY.md` part B, `reasoning/frame_plane.py` and the
two held files that import it (`LorentzImproper.lean`, `LorentzUnits.lean`):
the original was lost in the October 2026 reorganisation and never uploaded.*

The formal half of `tool frame` in 1+2 dimensions. Everything is over `ℚ` —
no floating point anywhere — and a state is a vector `(E, px, py)` whose
Minkowski square is `E² − px² − py²`.

* `eta`, `IsLorentz`, `minkowski` — the form, the Lorentz condition
  `Aᵀ η A = η`, and the squared Minkowski norm;
* `boostXOf`, `boostYOf`, `rot` — the three families the tool answers with:
  a boost along `x`, a boost along `y`, and a rotation of the spatial plane.
  A boost is parametrised by `a = cosh u`, `b = sinh u` with `a² − b² = 1`,
  so nothing in its proof divides; `boostX u` / `boostY u` read the rational
  rapidity `u` through `ca`/`sb`;
* `boostX_lorentz`, `boostY_lorentz`, `rot_lorentz`, `lorentz_mul` — each
  family preserves the form, and a product of Lorentz maps is one;
* `minkowski_preserved` — a Lorentz map keeps `E² − px² − py²` on every
  state, which is what the tool checks an answer against;
* `boostTo_symm`, `boostTo_rest`, `boostTo_lorentz` — the pure boost to a
  state `g` on the unit hyperboloid (`minkowski g = 1`): symmetric, it sends
  rest to `g`, and it is a Lorentz map;
* `thomas_eq`, `thomas_lorentz`, `thomas_not_symm`, `thomas_wigner`,
  `thomas_rotation_ne_one` — **the Thomas–Wigner example**:
  `boostX(1/2) · boostY(1/2)` is exactly the pure boost to
  `(25/9, −20/9, −4/3)` times the rotation `(15/17, −8/17)`, it is a Lorentz
  map, it is not itself a boost (it is not symmetric), and its Wigner
  rotation is not the identity. Two boosts compose to a boost times a
  rotation, and the rotation is what `tool frame` reports.
-/

namespace GLM.LorentzPlane

open Matrix

/-- The Minkowski form of 1+2 dimensions, in the `(E, px, py)` order. -/
def eta : Matrix (Fin 3) (Fin 3) ℚ := !![1, 0, 0; 0, -1, 0; 0, 0, -1]

/-- A Lorentz map: it keeps the Minkowski form, `Aᵀ η A = η`. -/
def IsLorentz (A : Matrix (Fin 3) (Fin 3) ℚ) : Prop := Aᵀ * eta * A = eta

/-- The squared Minkowski norm of a state. -/
def minkowski (v : Fin 3 → ℚ) : ℚ := v 0 ^ 2 - v 1 ^ 2 - v 2 ^ 2

/-- The rest state. -/
def rest : Fin 3 → ℚ := ![1, 0, 0]

/-- The squared Minkowski norm is the form applied to the state. -/
theorem minkowski_eta (v : Fin 3 → ℚ) : minkowski v = v ⬝ᵥ (eta *ᵥ v) := by
  simp [minkowski, eta, Matrix.mulVec, dotProduct, Fin.sum_univ_three]
  ring

/-! ## 1. The boost families, parametrised without division -/

/-- A boost along `x` with `a = cosh u`, `b = sinh u`. -/
def boostXOf (a b : ℚ) : Matrix (Fin 3) (Fin 3) ℚ :=
  !![a, -b, 0; -b, a, 0; 0, 0, 1]

/-- A boost along `y` with `a = cosh u`, `b = sinh u`. -/
def boostYOf (a b : ℚ) : Matrix (Fin 3) (Fin 3) ℚ :=
  !![a, 0, -b; 0, 1, 0; -b, 0, a]

/-- `cosh` of a rational rapidity, `(1 + u²)/(1 − u²)`. -/
def ca (u : ℚ) : ℚ := (1 + u ^ 2) / (1 - u ^ 2)

/-- `sinh` of a rational rapidity, `2u/(1 − u²)`. -/
def sb (u : ℚ) : ℚ := 2 * u / (1 - u ^ 2)

/-- A boost along `x`, read off the rapidity `u`. -/
def boostX (u : ℚ) : Matrix (Fin 3) (Fin 3) ℚ := boostXOf (ca u) (sb u)

/-- A boost along `y`, read off the rapidity `u`. -/
def boostY (u : ℚ) : Matrix (Fin 3) (Fin 3) ℚ := boostYOf (ca u) (sb u)

/-- A rotation of the spatial plane. -/
def rot (c s : ℚ) : Matrix (Fin 3) (Fin 3) ℚ := !![1, 0, 0; 0, c, -s; 0, s, c]

theorem boostXOf_lorentz {a b : ℚ} (h : a ^ 2 - b ^ 2 = 1) : IsLorentz (boostXOf a b) := by
  unfold IsLorentz boostXOf eta
  ext i j
  fin_cases i <;> fin_cases j <;>
    simp [Matrix.mul_apply, Fin.sum_univ_three] <;>
    ring_nf <;> linarith [h]

theorem boostYOf_lorentz {a b : ℚ} (h : a ^ 2 - b ^ 2 = 1) : IsLorentz (boostYOf a b) := by
  unfold IsLorentz boostYOf eta
  ext i j
  fin_cases i <;> fin_cases j <;>
    simp [Matrix.mul_apply, Fin.sum_univ_three] <;>
    ring_nf <;> linarith [h]

/-- `ca u ^ 2 − sb u ^ 2 = 1`: the rational rapidity sits on the hyperbola. -/
theorem ca_sq_sub_sb_sq (u : ℚ) (h : 1 - u ^ 2 ≠ 0) : ca u ^ 2 - sb u ^ 2 = 1 := by
  unfold ca sb
  field_simp
  ring

/-- **A boost along `x` is a Lorentz map.** -/
theorem boostX_lorentz (u : ℚ) (h : 1 - u ^ 2 ≠ 0) : IsLorentz (boostX u) :=
  boostXOf_lorentz (ca_sq_sub_sb_sq u h)

/-- **A boost along `y` is a Lorentz map.** -/
theorem boostY_lorentz (u : ℚ) (h : 1 - u ^ 2 ≠ 0) : IsLorentz (boostY u) :=
  boostYOf_lorentz (ca_sq_sub_sb_sq u h)

/-- **A rotation of the spatial plane is a Lorentz map.** -/
theorem rot_lorentz (c s : ℚ) (h : c ^ 2 + s ^ 2 = 1) : IsLorentz (rot c s) := by
  unfold IsLorentz rot eta
  ext i j
  fin_cases i <;> fin_cases j <;>
    simp [Matrix.mul_apply, Fin.sum_univ_three] <;>
    ring_nf <;> linarith [h]

/-- **A product of Lorentz maps is a Lorentz map.** -/
theorem lorentz_mul {A B : Matrix (Fin 3) (Fin 3) ℚ} (hA : IsLorentz A) (hB : IsLorentz B) :
    IsLorentz (A * B) := by
  unfold IsLorentz at *
  rw [Matrix.transpose_mul]
  calc Bᵀ * Aᵀ * eta * (A * B)
      = Bᵀ * (Aᵀ * eta * A) * B := by simp only [Matrix.mul_assoc]
    _ = Bᵀ * eta * B := by rw [hA]
    _ = eta := hB

/-- **A Lorentz map preserves the squared Minkowski norm of every state.** -/
theorem minkowski_preserved {A : Matrix (Fin 3) (Fin 3) ℚ} (hA : IsLorentz A)
    (v : Fin 3 → ℚ) : minkowski (A *ᵥ v) = minkowski v := by
  have h00 := congrFun (congrFun hA 0) 0
  have h01 := congrFun (congrFun hA 0) 1
  have h02 := congrFun (congrFun hA 0) 2
  have h11 := congrFun (congrFun hA 1) 1
  have h12 := congrFun (congrFun hA 1) 2
  have h22 := congrFun (congrFun hA 2) 2
  simp [eta, Matrix.mul_apply, Matrix.transpose_apply, Fin.sum_univ_three] at h00 h01 h02 h11 h12 h22
  simp only [minkowski, Matrix.mulVec, dotProduct, Fin.sum_univ_three]
  linear_combination
    v 0 ^ 2 * h00 + 2 * v 0 * v 1 * h01 + 2 * v 0 * v 2 * h02 +
    v 1 ^ 2 * h11 + 2 * v 1 * v 2 * h12 + v 2 ^ 2 * h22

/-! ## 2. The pure boost to a state on the hyperboloid -/

/-- The pure boost taking the rest state to `g`, for `minkowski g = 1`. -/
def boostTo (g : Fin 3 → ℚ) : Matrix (Fin 3) (Fin 3) ℚ :=
  !![g 0, g 1, g 2;
     g 1, 1 + g 1 ^ 2 / (1 + g 0), g 1 * g 2 / (1 + g 0);
     g 2, g 1 * g 2 / (1 + g 0), 1 + g 2 ^ 2 / (1 + g 0)]

/-- A pure boost is symmetric: it is its own transpose. -/
theorem boostTo_symm (g : Fin 3 → ℚ) : (boostTo g)ᵀ = boostTo g := by
  unfold boostTo
  ext i j
  fin_cases i <;> fin_cases j <;> simp [Matrix.transpose_apply]

/-- A pure boost sends rest to its target. -/
theorem boostTo_rest (g : Fin 3 → ℚ) : boostTo g *ᵥ rest = g := by
  unfold boostTo rest
  ext i
  fin_cases i <;> simp [Matrix.mulVec, dotProduct, Fin.sum_univ_three]

/-- **The pure boost to a state on the hyperboloid is a Lorentz map.** -/
theorem boostTo_lorentz {g : Fin 3 → ℚ} (hm : minkowski g = 1) (hd : 1 + g 0 ≠ 0) :
    IsLorentz (boostTo g) := by
  have hg0 : g 0 ^ 2 = 1 + g 1 ^ 2 + g 2 ^ 2 := by
    have : g 0 ^ 2 - g 1 ^ 2 - g 2 ^ 2 = 1 := hm
    linarith
  unfold IsLorentz boostTo eta
  ext i j
  fin_cases i <;> fin_cases j <;>
    simp [Matrix.mul_apply, Fin.sum_univ_three, Matrix.transpose_apply] <;>
    field_simp <;>
    ring_nf <;>
    simp only [hg0] <;>
    ring

/-! ## 3. The Thomas–Wigner example -/

/-- Two boosts along different axes, `boostX(1/2) · boostY(1/2)`. -/
def thomas : Matrix (Fin 3) (Fin 3) ℚ := boostX (1 / 2) * boostY (1 / 2)

/-- The pure boost the Thomas–Wigner split names, `(25/9, −20/9, −4/3)`. -/
def thomasBoost : Fin 3 → ℚ := ![25 / 9, -20 / 9, -4 / 3]

/-- The Wigner rotation of the Thomas–Wigner split, `(15/17, −8/17)`. -/
def thomasCos : ℚ := 15 / 17

/-- The sine of the Wigner rotation. -/
def thomasSin : ℚ := -8 / 17

/-- **The Thomas–Wigner identity**: the two boosts are the pure boost to
`(25/9, −20/9, −4/3)` times the rotation `(15/17, −8/17)`, exactly. -/
theorem thomas_eq : thomas = boostTo thomasBoost * rot thomasCos thomasSin := by
  unfold thomas boostX boostY boostXOf boostYOf boostTo rot thomasBoost thomasCos thomasSin
    ca sb
  ext i j
  fin_cases i <;> fin_cases j <;>
    simp [Matrix.mul_apply, Fin.sum_univ_three] <;>
    norm_num

/-- The target of the pure boost is the Thomas map applied to rest. -/
theorem thomas_apply_rest : thomas *ᵥ rest = thomasBoost := by
  rw [thomas_eq]
  ext i
  fin_cases i <;>
    simp [Matrix.mulVec, Matrix.mul_apply, dotProduct, Fin.sum_univ_three,
      rest, boostTo, rot, thomasBoost, thomasCos, thomasSin]

/-- **A product of two boosts is a Lorentz map.** -/
theorem thomas_lorentz : IsLorentz thomas :=
  lorentz_mul (boostX_lorentz (1 / 2) (by norm_num))
    (boostY_lorentz (1 / 2) (by norm_num))

/-- **The Thomas–Wigner split**: a Lorentz map is a pure boost times a
rotation, and for the two boosts the rotation is `(15/17, −8/17)`. -/
theorem thomas_wigner :
    ∃ (b : Matrix (Fin 3) (Fin 3) ℚ) (c s : ℚ), bᵀ = b ∧ c ^ 2 + s ^ 2 = 1 ∧
      thomas = b * rot c s ∧ b = boostTo (thomas *ᵥ rest) ∧ c = 15 / 17 ∧ s = -8 / 17 := by
  refine ⟨boostTo thomasBoost, thomasCos, thomasSin, boostTo_symm _, ?_, thomas_eq, ?_, rfl, rfl⟩
  · unfold thomasCos thomasSin; norm_num
  · rw [thomas_apply_rest]

/-- **A product of two boosts is not itself a boost**: it is not symmetric. -/
theorem thomas_not_symm : thomasᵀ ≠ thomas := by
  intro h
  have h01 := congrFun (congrFun h 0) 1
  have h10 := congrFun (congrFun h 1) 0
  unfold thomas boostX boostY boostXOf boostYOf ca sb at h01 h10
  simp [Matrix.transpose_apply, Matrix.mul_apply, Fin.sum_univ_three] at h01 h10
  norm_num at h01

/-- **The Wigner rotation of the two boosts is not the identity.** -/
theorem thomas_rotation_ne_one :
    rot thomasCos thomasSin ≠ (1 : Matrix (Fin 3) (Fin 3) ℚ) := by
  intro h
  have h12 := congrFun (congrFun h 1) 2
  unfold thomasCos thomasSin rot at h12
  simp at h12

end GLM.LorentzPlane
