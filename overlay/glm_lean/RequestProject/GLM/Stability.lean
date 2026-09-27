/-
# How far may an input move before its address does?

Every figure in this project is exact (directive D7), and every address is a
*nearest lattice point*: `overlay/glm_universal/reasoning/lean_address.py`
sends a declaration's 24 structural counts, scaled, to the Leech point nearest
them.  The question this file answers is the one that had never been asked of
that map — **how far may the input be moved before the address it decodes to
changes?** — and it answers it for an arbitrary set of candidate points, so
that the Leech lattice is one instance rather than the subject.

Three answers, of increasing sharpness.

* `isNearest_of_margin` — the triangle-inequality bound, in a bare metric
  space.  If every rival is at least `2r` further from `x` than the incumbent
  is, no move of size `r` can unseat the incumbent.
* `isNearest_of_separation` — the same bound expressed through the property a
  lattice actually publishes, its **minimum distance** `m`: a move of size `r`
  is safe as soon as `2·dist x p + 2·r ≤ m`.  For the Leech lattice in the
  `× √8` model of `substrate/leech2.py` that is `m² = 32`.
  `isNearest_of_sq_data` restates it in *squared* quantities alone —
  `64·D·E ≤ (m² − 4D − 4E)²` — because that is the form the Python can check
  in exact rational arithmetic, with no square root anywhere.
* `isNearest_perturbed_iff` — the sharp answer, in an inner product space.
  The distance from `x` to the bisector of `p` and a rival `q` is
  `competitorRadius x p q = (dist x q ^ 2 − dist x p ^ 2) / (2 · dist p q)`,
  and the exact stability radius of the address is the **minimum** of that
  over the rivals: every perturbation of norm at most `r` keeps the address
  **if and only if** `r` does not exceed any competitor radius.

The `only if` half is what stops the bound being a safe over-estimate:
`exists_perturbation_flip` *builds* the perturbation that changes the address,
of exactly the declared norm, by moving straight at the rival that is closest
to winning.  So the radius the Python reports is not merely sufficient — past
it there is a witness, and the witness is constructed rather than searched
for.

`competitorRadius_ge_of_separation` connects the two: a lattice's minimum
distance alone forces every competitor radius to be at least `m/2 − dist x p`,
which is why the certified lower bound and the measured radius are comparable
figures rather than two unrelated numbers.

Nothing here mentions 24 dimensions, the Leech lattice or the Golay code.  The
statements are about a set `S` in a metric or inner product space, so the
measurement in `overlay/glm_universal/reasoning/stability.py` supplies the
instance and inherits the theorem (directive D8).
-/
import Mathlib

namespace GLM.Stability

/-! ## 1.  Nearest points, and the triangle-inequality bound -/

section MetricForm

variable {X : Type*} [MetricSpace X]

/-- `IsNearest S x p` says that `p` is a point of `S` no further from `x` than
any other point of `S`.  This is what "the address of `x`" means: the decoder
returns some `p` with this property, and the question of stability is whether
the same `p` still has it after `x` moves. -/
def IsNearest (S : Set X) (x p : X) : Prop :=
  p ∈ S ∧ ∀ q ∈ S, dist x p ≤ dist x q

theorem IsNearest.mem {S : Set X} {x p : X} (h : IsNearest S x p) : p ∈ S := h.1

theorem IsNearest.le {S : Set X} {x p : X} (h : IsNearest S x p) {q : X}
    (hq : q ∈ S) : dist x p ≤ dist x q := h.2 q hq

/-- **The triangle-inequality bound.**  If every rival is at least `2r`
further from `x` than the incumbent `p`, then moving `x` by at most `r` leaves
`p` nearest.  Nothing but the triangle inequality is used, so this holds in any
metric space and for any set of candidates. -/
theorem isNearest_of_margin {S : Set X} {x y p : X} {r : ℝ}
    (hp : IsNearest S x p)
    (hmargin : ∀ q ∈ S, q ≠ p → dist x p + 2 * r ≤ dist x q)
    (hy : dist x y ≤ r) : IsNearest S y p := by
  refine ⟨hp.mem, fun q hq => ?_⟩
  by_cases hqp : q = p
  · subst hqp; exact le_rfl
  · have h1 : dist y p ≤ dist x y + dist x p := by
      have h := dist_triangle y x p
      rw [dist_comm y x] at h
      exact h
    have h2 : dist x q ≤ dist x y + dist y q := dist_triangle x y q
    have hm := hmargin q hq hqp
    have : dist x p + 2 * r ≤ dist x y + dist y q := hm.trans h2
    linarith
end MetricForm

/-! ## 2.  The bound a lattice publishes: its minimum distance -/

section Separation

variable {X : Type*} [MetricSpace X]

/-- **The separation form.**  A set whose distinct points are at least `m`
apart — a lattice with minimum distance `m` — keeps the address of `x` under
every move of size `r`, as soon as `2·dist x p + 2·r ≤ m`.  This is the bound
the Python calls *certified*: it needs only the incumbent's own distance and a
published property of the lattice, never a search over rivals. -/
theorem isNearest_of_separation {S : Set X} {x y p : X} {m r : ℝ}
    (hp : IsNearest S x p)
    (hsep : ∀ q ∈ S, ∀ q' ∈ S, q ≠ q' → m ≤ dist q q')
    (hbound : 2 * dist x p + 2 * r ≤ m)
    (hy : dist x y ≤ r) : IsNearest S y p := by
  refine isNearest_of_margin hp (fun q hq hqp => ?_) hy
  have hpq : m ≤ dist p q := hsep p hp.mem q hq (Ne.symm hqp)
  have h : dist p q ≤ dist p x + dist x q := dist_triangle p x q
  have hpx : dist p x = dist x p := dist_comm p x
  linarith

/-- The same bound with every quantity squared, which is the only form exact
rational arithmetic can check: `E` bounds the squared distance from `x` to its
address, `D` bounds the squared norm of the perturbation, `m` is the minimum
distance, and the single inequality `64·D·E ≤ (m² − 4D − 4E)²` (with the right
side's base nonnegative) is equivalent to `2√E + 2√D ≤ m`.  No square root is
taken anywhere. -/
theorem two_mul_add_two_mul_le_of_sq {a b m D E : ℝ}
    (ha : 0 ≤ a) (hb : 0 ≤ b) (hm : 0 ≤ m)
    (hA : a ^ 2 ≤ D) (hB : b ^ 2 ≤ E)
    (hpos : 0 ≤ m ^ 2 - 4 * D - 4 * E)
    (h : 64 * D * E ≤ (m ^ 2 - 4 * D - 4 * E) ^ 2) :
    2 * a + 2 * b ≤ m := by
  have hD : 0 ≤ D := le_trans (sq_nonneg a) hA
  have hE : 0 ≤ E := le_trans (sq_nonneg b) hB
  have hab : 0 ≤ 8 * (a * b) := by positivity
  have hsq : (8 * (a * b)) ^ 2 ≤ (m ^ 2 - 4 * D - 4 * E) ^ 2 := by
    have : (8 * (a * b)) ^ 2 = 64 * (a ^ 2) * (b ^ 2) := by ring
    rw [this]
    refine le_trans ?_ h
    have h1 : 64 * a ^ 2 * b ^ 2 ≤ 64 * D * b ^ 2 := by nlinarith [sq_nonneg b]
    nlinarith [sq_nonneg b, hB, hD]
  have hle : 8 * (a * b) ≤ m ^ 2 - 4 * D - 4 * E := by
    nlinarith [hsq, hab, hpos]
  have hfinal : (2 * a + 2 * b) ^ 2 ≤ m ^ 2 := by nlinarith
  nlinarith [sq_nonneg (2 * a + 2 * b - m), sq_nonneg (2 * a + 2 * b + m)]

/-- **The form the measurement checks.**  Everything is a squared quantity and
an exact rational comparison: if the squared distance from `x` to its address
is at most `E`, the squared norm of the perturbation at most `D`, the lattice's
squared minimum distance `m²`, and `64·D·E ≤ (m² − 4D − 4E)²` with
`4D + 4E ≤ m²`, then the address does not move. -/
theorem isNearest_of_sq_data {S : Set X} {x y p : X} {m D E : ℝ}
    (hp : IsNearest S x p)
    (hsep : ∀ q ∈ S, ∀ q' ∈ S, q ≠ q' → m ≤ dist q q')
    (hm : 0 ≤ m)
    (hE : dist x p ^ 2 ≤ E) (hD : dist x y ^ 2 ≤ D)
    (hpos : 0 ≤ m ^ 2 - 4 * D - 4 * E)
    (h : 64 * D * E ≤ (m ^ 2 - 4 * D - 4 * E) ^ 2) :
    IsNearest S y p := by
  have hbound : 2 * dist x p + 2 * dist x y ≤ m := by
    have := two_mul_add_two_mul_le_of_sq (a := dist x y) (b := dist x p)
      dist_nonneg dist_nonneg hm hD hE hpos h
    linarith
  exact isNearest_of_separation hp hsep hbound le_rfl

end Separation

/-! ## 3.  The sharp radius, in an inner product space -/

section InnerForm

variable {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]

/-- The distance from `x` to the bisecting hyperplane of its address `p` and a
rival `q`: the exact amount by which `x` may be moved *straight at* `q` before
`q` becomes the nearer of the two. -/
noncomputable def competitorRadius (x p q : E) : ℝ :=
  (dist x q ^ 2 - dist x p ^ 2) / (2 * dist p q)

/-- The identity every statement in this section rests on: shifting `x` by `δ`
changes the *difference* of the two squared distances by `2⟪δ, q − p⟫`, and by
nothing else — the `‖δ‖²` terms cancel. -/
theorem sq_dist_sub_sq_dist_add (x p q δ : E) :
    dist (x + δ) p ^ 2 - dist (x + δ) q ^ 2
      = (dist x p ^ 2 - dist x q ^ 2) + 2 * inner ℝ δ (q - p) := by
  have hp : dist (x + δ) p ^ 2
      = ‖x - p‖ ^ 2 + 2 * inner ℝ (x - p) δ + ‖δ‖ ^ 2 := by
    rw [dist_eq_norm, show x + δ - p = (x - p) + δ from by abel, norm_add_sq_real]
  have hq : dist (x + δ) q ^ 2
      = ‖x - q‖ ^ 2 + 2 * inner ℝ (x - q) δ + ‖δ‖ ^ 2 := by
    rw [dist_eq_norm, show x + δ - q = (x - q) + δ from by abel, norm_add_sq_real]
  have hsplit : inner ℝ (x - p) δ - inner ℝ (x - q) δ = inner ℝ δ (q - p) := by
    rw [← inner_sub_left, real_inner_comm]
    congr 1
    abel
  rw [hp, hq, dist_eq_norm, dist_eq_norm]
  linarith [hsplit]

/-- **The sufficient half of the sharp bound.**  If `r` does not exceed the
bisector distance to any rival, every perturbation of norm at most `r` leaves
the address where it was.  Cauchy–Schwarz is the only inequality used, so the
bound is attained exactly when the perturbation points straight at the rival —
which is what the next theorem builds. -/
theorem isNearest_perturbed_of_radius {S : Set E} {x p δ : E} {r : ℝ}
    (hp : p ∈ S)
    (hnear : ∀ q ∈ S, q ≠ p → 2 * r * dist p q ≤ dist x q ^ 2 - dist x p ^ 2)
    (hδ : ‖δ‖ ≤ r) : IsNearest S (x + δ) p := by
  refine ⟨hp, fun q hq => ?_⟩
  by_cases hqp : q = p
  · subst hqp; exact le_rfl
  · have hcs : inner ℝ δ (q - p) ≤ ‖δ‖ * ‖q - p‖ :=
      real_inner_le_norm δ (q - p)
    have hnorm : ‖q - p‖ = dist p q := by
      rw [dist_comm, dist_eq_norm]
    have hbound : 2 * inner ℝ δ (q - p) ≤ 2 * r * dist p q := by
      have h1 : ‖δ‖ * ‖q - p‖ ≤ r * dist p q := by
        rw [hnorm]
        exact mul_le_mul_of_nonneg_right hδ dist_nonneg
      linarith
    have hid := sq_dist_sub_sq_dist_add x p q δ
    have hmargin := hnear q hq hqp
    have hsq : dist (x + δ) p ^ 2 ≤ dist (x + δ) q ^ 2 := by
      have : dist (x + δ) p ^ 2 - dist (x + δ) q ^ 2 ≤ 0 := by
        rw [hid]; linarith
      linarith
    have h1 : (0:ℝ) ≤ dist (x + δ) p := dist_nonneg
    have h2 : (0:ℝ) ≤ dist (x + δ) q := dist_nonneg
    nlinarith

/-- **The necessary half.**  Past the bisector distance to a rival there is a
perturbation of *exactly* the declared norm that hands the address to that
rival, and it is constructed, not searched for: move straight at `q`. -/
theorem exists_perturbation_flip {x p q : E} (hqp : q ≠ p)
    (hle : dist x p ≤ dist x q) {s : ℝ} (hs : competitorRadius x p q < s) :
    ∃ δ : E, ‖δ‖ = s ∧ dist (x + δ) q < dist (x + δ) p := by
  have hd : (0:ℝ) < dist p q := dist_pos.mpr (Ne.symm hqp)
  have hnorm : ‖q - p‖ = dist p q := by rw [dist_comm, dist_eq_norm]
  have hnum : 0 ≤ dist x q ^ 2 - dist x p ^ 2 := by nlinarith [dist_nonneg (x := x) (y := p)]
  have hrad : 0 ≤ competitorRadius x p q := by
    apply div_nonneg hnum
    linarith
  have hspos : 0 < s := lt_of_le_of_lt hrad hs
  refine ⟨(s / dist p q) • (q - p), ?_, ?_⟩
  · rw [norm_smul, hnorm]
    rw [Real.norm_eq_abs, abs_of_nonneg (by positivity)]
    field_simp
  · set δ : E := (s / dist p q) • (q - p) with hδdef
    have hinner : inner ℝ δ (q - p) = s * dist p q := by
      rw [hδdef, real_inner_smul_left, real_inner_self_eq_norm_sq, hnorm]
      field_simp
    have hid := sq_dist_sub_sq_dist_add x p q δ
    have hgt : dist x q ^ 2 - dist x p ^ 2 < 2 * s * dist p q := by
      rw [competitorRadius] at hs
      rw [div_lt_iff₀ (by linarith)] at hs
      linarith
    have hpos : 0 < dist (x + δ) p ^ 2 - dist (x + δ) q ^ 2 := by
      rw [hid, hinner]; linarith
    have h1 : (0:ℝ) ≤ dist (x + δ) p := dist_nonneg
    have h2 : (0:ℝ) ≤ dist (x + δ) q := dist_nonneg
    nlinarith

/-- **The exact stability radius.**  Every perturbation of norm at most `r`
keeps the address *if and only if* `r` is at most every competitor radius.  So
the minimum bisector distance is not a conservative estimate of how far the
input may move: it is the answer. -/
theorem isNearest_perturbed_iff {S : Set E} {x p : E} {r : ℝ}
    (hp : IsNearest S x p) :
    (∀ δ : E, ‖δ‖ ≤ r → IsNearest S (x + δ) p)
      ↔ (∀ q ∈ S, q ≠ p → r ≤ competitorRadius x p q) := by
  constructor
  · intro hstable q hq hqp
    by_contra hlt
    push_neg at hlt
    obtain ⟨δ, hnorm, hflip⟩ :=
      exists_perturbation_flip hqp (hp.le hq) hlt
    have := (hstable δ (le_of_eq hnorm)).le hq
    exact absurd this (not_le.mpr hflip)
  · intro hmin δ hδ
    refine isNearest_perturbed_of_radius hp.mem (fun q hq hqp => ?_) hδ
    have hd : (0:ℝ) < dist p q := dist_pos.mpr (Ne.symm hqp)
    have := hmin q hq hqp
    rw [competitorRadius, le_div_iff₀ (by linarith)] at this
    linarith

omit [InnerProductSpace ℝ E] in
/-- The certified bound, in the sharp bound's own terms: a set whose distinct
points are at least `m` apart has every competitor radius at least
`m/2 − dist x p`.  This is why the lower bound the Python certifies from the
Leech lattice's minimum distance and the radius it measures against a searched
set of rivals are two estimates of one quantity. -/
theorem competitorRadius_ge_of_separation {x p q : E} (hqp : q ≠ p) {m : ℝ}
    (hsep : m ≤ dist p q) : m / 2 - dist x p ≤ competitorRadius x p q := by
  have hd : (0:ℝ) < dist p q := dist_pos.mpr (Ne.symm hqp)
  have h1 : dist p q - dist x p ≤ dist x q := by
    have h := dist_triangle p x q
    rw [dist_comm p x] at h
    linarith
  have h2 : dist x p - dist p q ≤ dist x q := by
    have h := dist_triangle x q p
    rw [dist_comm q p] at h
    linarith
  have h3 : (dist p q - dist x p) ^ 2 ≤ dist x q ^ 2 := by
    nlinarith [dist_nonneg (x := x) (y := q)]
  rw [competitorRadius, le_div_iff₀ (by linarith)]
  nlinarith [mul_le_mul_of_nonneg_right hsep (le_of_lt hd)]

omit [InnerProductSpace ℝ E] in
/-- **Why a bounded search can still be exact.**  Suppose the rivals in a
searched part `T` all keep a radius of at least `r`, and every rival outside
`T` is at least `L` away from the address.  Then, as soon as
`r ≤ L/2 − dist x p`, the unsearched rivals cannot beat the searched ones, and
`r` is a radius for the whole of `S`.

This is what makes the measurement in
`overlay/glm_universal/reasoning/stability.py` a certificate rather than an
estimate: it searches the 196,560 minimal-vector translates of the address,
and the next shell of the Leech lattice is at squared norm 48, so a searched
minimum below `√48/2 − dist x p` is the true minimum. -/
theorem le_competitorRadius_of_shell {S T : Set E} {x p : E} {r L : ℝ}
    (hsearched : ∀ q ∈ T, q ≠ p → r ≤ competitorRadius x p q)
    (hrest : ∀ q ∈ S, q ∉ T → q ≠ p → L ≤ dist p q)
    (hshell : r ≤ L / 2 - dist x p) :
    ∀ q ∈ S, q ≠ p → r ≤ competitorRadius x p q := by
  intro q hq hqp
  by_cases hT : q ∈ T
  · exact hsearched q hT hqp
  · exact hshell.trans (competitorRadius_ge_of_separation hqp (hrest q hq hT hqp))

end InnerForm

end GLM.Stability
