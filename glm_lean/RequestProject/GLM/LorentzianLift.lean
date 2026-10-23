import Mathlib

/-!
# The Lorentzian lift of the ambiguous space (Phase 182)

*Created 22 October 2026.*

The formal half of `studies/LORENTZIAN_LIFT_STUDY.md`, which audits and
repairs the owner's `source_material/iter10_lorentzian.py`. That script lifts a
point `x` of `ℚⁿ` (`n = 24` for the Leech lattice) to the light cone of
`ℚⁿ⁺²` with the Lorentzian form `⟨a, b⟩ = a_x · b_x + a_t b_t − a_τ b_τ`:

  `L(x) = (x, (1 − |x|²)/2, (1 + |x|²)/2)`,

and proposes that every tie of the 24-dimensional picture is a reflection
hyperplane upstairs, and that the reflection resolves it. Everything here is
over `ℚ` and in the script's own coordinates.

What holds:

* `lift_null` — the lift is null, as the script says;
* `inner_lift_lift` — `⟨L x, L y⟩ = −|x − y|²/2`: the lift turns squared
  distance into a linear quantity;
* `weyl_null`, `inner_lift_weyl` — the vector `w = (0, −1, 1)` is null and
  `⟨L x, w⟩ = −1` for every `x`: this is the Weyl vector of the lift;
* `root_norm`, `inner_root_weyl`, `root_char` — the vectors `r` with
  `⟨r, r⟩ = 2` and `⟨r, w⟩ = −1` are exactly `r_λ = L λ − w`, one for every
  point `λ`: Conway's Leech roots are indexed by **lattice points**, not by
  deep holes;
* `inner_lift_root` — **the key identity** `⟨L x, r_λ⟩ = 1 − |x − λ|²/2`;
* `nearer_iff`, `tie_iff` — the nearest point is the root of largest inner
  product, and a tie between `λ` and `μ` is exactly membership of `L x` in the
  mirror of `s = r_λ − r_μ` (`root_sub_norm`: `⟨s, s⟩ = |λ − μ|²`);
* `hole_orth` — a point at squared distance `2` (the Leech covering radius) is
  orthogonal to the root of every vertex of its hole.

What fails, and why:

* `scriptW_eq`, `inner_lift_scriptW` — the script's `w = (0, 1, 1)` is
  `2 · L 0`, the lift of the origin, and `⟨L x, (0,1,1)⟩ = −|x|²` is not
  constant: it is not the Weyl vector of this lift;
* `inner_weyl_root` — `⟨w, r_λ⟩ = −1` for every `λ`, so the Weyl vector
  scores all candidates alike;
* `refl_fix_of_orth`, `refl_swap`, `tie_reflection` — the reflection in the
  tie's mirror fixes the tied point and swaps the two tied roots;
* `reflection_invariant_tie` — **no rule that is unchanged under reflections
  can break a tie**: any score `f` with `f (σ v) (σ r) = f v r` for every
  reflection `σ` gives the two tied roots the same score at a tied point.

So the lift *certifies* a tie exactly and names the hole, but a tie can only be
broken by information from outside the geometry: `context_break` is the
context rule the study measures (score by a second point `y`).
-/

namespace GLM.LorentzianLift

open Finset

variable {n : ℕ}

/-- The Euclidean dot product on `ℚⁿ`. -/
def dot (x y : Fin n → ℚ) : ℚ := ∑ i, x i * y i

/-- The squared Euclidean norm. -/
def nsq (x : Fin n → ℚ) : ℚ := dot x x

/-- A vector of `ℚⁿ⁺²` in the script's coordinates `(x, t, τ)`. -/
@[ext]
structure LVec (n : ℕ) where
  x : Fin n → ℚ
  t : ℚ
  τ : ℚ

/-- The Lorentzian form of signature `(n+1, 1)`: `x·x' + t t' − τ τ'`. -/
def inner (a b : LVec n) : ℚ := dot a.x b.x + a.t * b.t - a.τ * b.τ

instance : Add (LVec n) := ⟨fun a b => ⟨a.x + b.x, a.t + b.t, a.τ + b.τ⟩⟩
instance : Sub (LVec n) := ⟨fun a b => ⟨a.x - b.x, a.t - b.t, a.τ - b.τ⟩⟩
instance : SMul ℚ (LVec n) := ⟨fun c a => ⟨c • a.x, c * a.t, c * a.τ⟩⟩

@[simp] lemma add_x (a b : LVec n) : (a + b).x = a.x + b.x := rfl
@[simp] lemma add_t (a b : LVec n) : (a + b).t = a.t + b.t := rfl
@[simp] lemma add_τ (a b : LVec n) : (a + b).τ = a.τ + b.τ := rfl
@[simp] lemma sub_x (a b : LVec n) : (a - b).x = a.x - b.x := rfl
@[simp] lemma sub_t (a b : LVec n) : (a - b).t = a.t - b.t := rfl
@[simp] lemma sub_τ (a b : LVec n) : (a - b).τ = a.τ - b.τ := rfl
@[simp] lemma smul_x (c : ℚ) (a : LVec n) : (c • a).x = c • a.x := rfl
@[simp] lemma smul_t (c : ℚ) (a : LVec n) : (c • a).t = c * a.t := rfl
@[simp] lemma smul_τ (c : ℚ) (a : LVec n) : (c • a).τ = c * a.τ := rfl

/-! ## 1. Bilinearity -/

lemma dot_comm (x y : Fin n → ℚ) : dot x y = dot y x := by
  unfold dot; exact sum_congr rfl fun i _ => mul_comm _ _

lemma dot_sub_left (x y z : Fin n → ℚ) : dot (x - y) z = dot x z - dot y z := by
  unfold dot; rw [← sum_sub_distrib]; exact sum_congr rfl fun i _ => by simp [sub_mul]

lemma dot_sub_right (x y z : Fin n → ℚ) : dot x (y - z) = dot x y - dot x z := by
  rw [dot_comm, dot_sub_left, dot_comm y, dot_comm z]

lemma dot_smul_left (c : ℚ) (x y : Fin n → ℚ) : dot (c • x) y = c * dot x y := by
  unfold dot; rw [mul_sum]; exact sum_congr rfl fun i _ => by simp [mul_assoc]

lemma dot_smul_right (c : ℚ) (x y : Fin n → ℚ) : dot x (c • y) = c * dot x y := by
  rw [dot_comm, dot_smul_left, dot_comm]

lemma dot_zero_left (y : Fin n → ℚ) : dot 0 y = 0 := by simp [dot]

lemma inner_comm (a b : LVec n) : inner a b = inner b a := by
  unfold inner; rw [dot_comm]; ring

lemma inner_sub_left (a b c : LVec n) : inner (a - b) c = inner a c - inner b c := by
  unfold inner; simp only [sub_x, sub_t, sub_τ, dot_sub_left]; ring

lemma inner_sub_right (a b c : LVec n) : inner a (b - c) = inner a b - inner a c := by
  rw [inner_comm, inner_sub_left, inner_comm b, inner_comm c]

lemma inner_smul_left (k : ℚ) (a b : LVec n) : inner (k • a) b = k * inner a b := by
  unfold inner; simp only [smul_x, smul_t, smul_τ, dot_smul_left]; ring

lemma inner_smul_right (k : ℚ) (a b : LVec n) : inner a (k • b) = k * inner a b := by
  rw [inner_comm, inner_smul_left, inner_comm]

/-- `|x − y|² = |x|² − 2 x·y + |y|²`. -/
lemma nsq_sub (x y : Fin n → ℚ) : nsq (x - y) = nsq x - 2 * dot x y + nsq y := by
  unfold nsq; rw [dot_sub_left, dot_sub_right, dot_sub_right, dot_comm y x]; ring

/-! ## 2. The lift and the Weyl vector -/

/-- The script's lift `L(x) = (x, (1 − |x|²)/2, (1 + |x|²)/2)`. -/
def lift (x : Fin n → ℚ) : LVec n := ⟨x, (1 - nsq x) / 2, (1 + nsq x) / 2⟩

/-- **The lift is null**, as the script says. -/
theorem lift_null (x : Fin n → ℚ) : inner (lift x) (lift x) = 0 := by
  unfold inner lift nsq; simp only; ring

/-- **The lift linearises distance**: `⟨L x, L y⟩ = −|x − y|²/2`. -/
theorem inner_lift_lift (x y : Fin n → ℚ) :
    inner (lift x) (lift y) = -(nsq (x - y)) / 2 := by
  rw [nsq_sub]; unfold inner lift; simp only; unfold nsq; ring

/-- The Weyl vector of the lift: `w = (0, −1, 1)`. -/
def weyl : LVec n := ⟨0, -1, 1⟩

theorem weyl_null : inner (weyl : LVec n) weyl = 0 := by
  simp [inner, weyl, dot]

/-- **`⟨L x, w⟩ = −1` for every `x`**: every lifted point sits on the same
affine slice of the light cone. -/
theorem inner_lift_weyl (x : Fin n → ℚ) : inner (lift x) weyl = -1 := by
  simp only [inner, lift, weyl, dot, Pi.zero_apply, mul_zero, sum_const_zero]; ring

/-- The script's choice `w = (0, …, 0, 1, 1)`. -/
def scriptW : LVec n := ⟨0, 1, 1⟩

/-- **The script's `w` is the lift of the origin, doubled.** -/
theorem scriptW_eq : (scriptW : LVec n) = (2 : ℚ) • lift 0 := by
  ext i <;> simp [scriptW, lift, nsq, dot]

/-- With the script's `w`, `⟨L x, w⟩ = −|x|²`, which depends on `x`: the
script's `w` is null, but it is not the Weyl vector of the lift. -/
theorem inner_lift_scriptW (x : Fin n → ℚ) : inner (lift x) scriptW = -nsq x := by
  simp only [inner, lift, scriptW, dot, Pi.zero_apply, mul_zero, sum_const_zero]; ring

/-! ## 3. Roots are indexed by points -/

/-- The root of the point `λ`: `r_λ = L λ − w`. -/
def root (l : Fin n → ℚ) : LVec n := lift l - weyl

theorem root_norm (l : Fin n → ℚ) : inner (root l) (root l) = 2 := by
  unfold root
  rw [inner_sub_left, inner_sub_right, inner_sub_right, lift_null, weyl_null,
    inner_lift_weyl, inner_comm weyl, inner_lift_weyl]; ring

theorem inner_root_weyl (l : Fin n → ℚ) : inner (root l) weyl = -1 := by
  unfold root; rw [inner_sub_left, inner_lift_weyl, weyl_null]; ring

/-- **The Weyl vector scores every root alike**: it cannot break any tie. -/
theorem inner_weyl_root (l : Fin n → ℚ) : inner weyl (root l) = -1 := by
  rw [inner_comm, inner_root_weyl]

/-- **The roots of the lift are exactly the `r_λ`**: a vector of norm `2` with
`⟨r, w⟩ = −1` is the root of its own Euclidean part. In the lattice
`II_{25,1}` this is Conway's indexing of the Leech roots by the points of the
Leech lattice. -/
theorem root_char (r : LVec n) (h2 : inner r r = 2) (hw : inner r weyl = -1) :
    r = root r.x := by
  have hw' : r.t + r.τ = 1 := by
    simp only [inner, weyl, dot, Pi.zero_apply, mul_zero, sum_const_zero] at hw; linarith
  have h2' : dot r.x r.x + r.t * r.t - r.τ * r.τ = 2 := h2
  have hd : r.t - r.τ = 2 - nsq r.x := by
    have : (r.t - r.τ) * (r.t + r.τ) = 2 - dot r.x r.x := by linarith
    rw [hw', mul_one] at this; simpa [nsq] using this
  ext i
  · simp [root, lift, weyl]
  · simp only [root, lift, weyl, sub_t]; linarith
  · simp only [root, lift, weyl, sub_τ]; linarith

/-- **The key identity**: `⟨L x, r_λ⟩ = 1 − |x − λ|²/2`. -/
theorem inner_lift_root (x l : Fin n → ℚ) :
    inner (lift x) (root l) = 1 - nsq (x - l) / 2 := by
  unfold root; rw [inner_sub_right, inner_lift_lift, inner_lift_weyl]; ring

/-- **The nearer point has the larger root score.** -/
theorem nearer_iff (x l m : Fin n → ℚ) :
    nsq (x - l) < nsq (x - m) ↔ inner (lift x) (root m) < inner (lift x) (root l) := by
  rw [inner_lift_root, inner_lift_root]; constructor <;> intro h <;> linarith

/-- **A tie is a mirror**: `x` is equidistant from `λ` and `μ` exactly when
`L x` is orthogonal to `r_λ − r_μ`. -/
theorem tie_iff (x l m : Fin n → ℚ) :
    nsq (x - l) = nsq (x - m) ↔ inner (lift x) (root l - root m) = 0 := by
  rw [inner_sub_right, inner_lift_root, inner_lift_root]
  constructor <;> intro h <;> linarith

/-- `⟨r_λ, r_μ⟩ = 2 − |λ − μ|²/2`. -/
theorem inner_root_root (l m : Fin n → ℚ) :
    inner (root l) (root m) = 2 - nsq (l - m) / 2 := by
  have h := inner_lift_root l m
  unfold root at h ⊢
  rw [inner_sub_left, h, inner_comm weyl, inner_sub_left, inner_comm weyl,
    inner_lift_weyl, weyl_null]; ring

/-- The mirror of a tie has norm `|λ − μ|²`. -/
theorem root_sub_norm (l m : Fin n → ℚ) :
    inner (root l - root m) (root l - root m) = nsq (l - m) := by
  rw [inner_sub_left, inner_sub_right, inner_sub_right, root_norm, root_norm,
    inner_root_root, inner_comm (root m), inner_root_root]
  ring

/-- **A hole is orthogonal to its vertices**: a point at squared distance `2`
from `λ` (for the Leech lattice, the covering radius squared) is orthogonal to
the root `r_λ`. -/
theorem hole_orth (c l : Fin n → ℚ) (h : nsq (c - l) = 2) : inner (lift c) (root l) = 0 := by
  rw [inner_lift_root, h]; norm_num

/-! ## 4. Reflections cannot break a tie -/

/-- The Householder reflection `v ↦ v − 2⟨v, s⟩/⟨s, s⟩ · s`. -/
def refl (s v : LVec n) : LVec n := v - (2 * inner v s / inner s s) • s

/-- A reflection is an isometry. -/
theorem refl_inner (s u v : LVec n) (hs : inner s s ≠ 0) :
    inner (refl s u) (refl s v) = inner u v := by
  unfold refl
  rw [inner_sub_left, inner_sub_right, inner_sub_right, inner_smul_left, inner_smul_right,
    inner_smul_left, inner_smul_right, inner_comm s v]
  field_simp; ring

/-- **A reflection fixes its mirror pointwise.** -/
theorem refl_fix_of_orth (s v : LVec n) (h : inner v s = 0) : refl s v = v := by
  unfold refl; rw [h]; ext i <;> simp

/-- A reflection in `a − b` swaps two vectors of equal norm. -/
theorem refl_swap (a b : LVec n) (hab : inner a a = inner b b)
    (hs : inner (a - b) (a - b) ≠ 0) : refl (a - b) a = b := by
  have key : 2 * inner a (a - b) = inner (a - b) (a - b) := by
    simp only [inner_sub_left, inner_sub_right]; rw [inner_comm b a]; linarith
  unfold refl; rw [key, div_self hs]; ext i <;> simp

lemma nsq_pos_of_ne {l m : Fin n → ℚ} (h : l ≠ m) : nsq (l - m) ≠ 0 := by
  intro h0
  apply h
  have hz : ∀ i, (l - m) i * (l - m) i = 0 := by
    have hnn : ∀ i ∈ (univ : Finset (Fin n)), 0 ≤ (l - m) i * (l - m) i :=
      fun i _ => mul_self_nonneg _
    intro i
    exact (sum_eq_zero_iff_of_nonneg hnn).mp h0 i (mem_univ i)
  funext i
  have := hz i
  have : (l - m) i = 0 := mul_self_eq_zero.mp this
  simpa [sub_eq_zero] using this

/-- **The reflection of a tie fixes the tied point and swaps the candidates.**
For distinct `λ, μ` and `x` equidistant from both, the reflection in
`r_λ − r_μ` sends `L x` to itself and `r_λ` to `r_μ`: the move the script
proposes leaves the ambiguous point where it is. -/
theorem tie_reflection (x l m : Fin n → ℚ) (hlm : l ≠ m) (htie : nsq (x - l) = nsq (x - m)) :
    refl (root l - root m) (lift x) = lift x ∧ refl (root l - root m) (root l) = root m := by
  refine ⟨refl_fix_of_orth _ _ ((tie_iff x l m).mp htie), refl_swap _ _ ?_ ?_⟩
  · rw [root_norm, root_norm]
  · rw [root_sub_norm]; exact nsq_pos_of_ne hlm

/-- **No reflection-invariant rule breaks a tie.** If a score `f` is unchanged
when both of its arguments are reflected in the same (non-null) mirror, then at
a point equidistant from distinct `λ` and `μ` it scores `r_λ` and `r_μ` alike.
The Lorentzian form itself, and every function of Lorentzian inner products,
is such a score. -/
theorem reflection_invariant_tie {β : Type*} (f : LVec n → LVec n → β)
    (hf : ∀ s v r, inner s s ≠ 0 → f (refl s v) (refl s r) = f v r)
    (x l m : Fin n → ℚ) (hlm : l ≠ m) (htie : nsq (x - l) = nsq (x - m)) :
    f (lift x) (root l) = f (lift x) (root m) := by
  obtain ⟨h1, h2⟩ := tie_reflection x l m hlm htie
  have hs : inner (root l - root m) (root l - root m) ≠ 0 := by
    rw [root_sub_norm]; exact nsq_pos_of_ne hlm
  have := hf (root l - root m) (lift x) (root l) hs
  rw [h1, h2] at this; exact this.symm

/-- The Lorentzian score `⟨v, r⟩` is reflection invariant. -/
theorem inner_reflection_invariant (s v r : LVec n) (hs : inner s s ≠ 0) :
    inner (refl s v) (refl s r) = inner v r := refl_inner s v r hs

/-- **The context rule.** Scoring the candidates by a second point `y`, the
context, prefers the candidate nearer to `y`; it breaks a tie at `x` exactly
when `y` is not itself equidistant. This is information from outside the
geometry of `x`, which is what `reflection_invariant_tie` says a tie needs. -/
theorem context_break (y l m : Fin n → ℚ) :
    inner (lift y) (root m) < inner (lift y) (root l) ↔ nsq (y - l) < nsq (y - m) :=
  (nearer_iff y l m).symm

end GLM.LorentzianLift
