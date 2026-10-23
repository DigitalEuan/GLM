import Mathlib

/-!
# Exact rational Lorentz boosts, and what separates a frame change from a unit change (Phase 177)

*Created 21 October 2026.*

The formal half of `studies/FRAME_OPERATOR_STUDY.md`, taken from the owner's document
`source_material/Lorentz boosts.pdf`. That document proposes reading a Lorentz boost as a "move"
of a puzzle whose invariant core is the rest mass, with `c` as the calibration dial, and closes with
a proposal to run two studies: an *exact transformation integrity* study (the boost done in exact
rational arithmetic, checked for invariance, inverse, composition and branch) and an *operator
inference* study (the boost learned from examples). Its Lean sketch was not compiled; this file is
the compiled version, in one spatial dimension and natural units.

**Exact parametrisation.** For rational `u` with `u² ≠ 1` put
`a(u) = (1+u²)/(1−u²)` and `b(u) = 2u/(1−u²)`; then `a² − b² = 1` (`ca_sq_sub_sb_sq`), so the boost
`B(u)` has rational entries and no hyperbolic function is ever evaluated.

* `boost_inv` — `E² − p²` is preserved;
* `boost_zero`, `boost_neg_boost` — `B(0)` is the identity and `B(−u)` undoes `B(u)`;
* `boost_boost`, `compose_abs_lt_one` — `B(u) B(v) = B((u+v)/(1+uv))`, and the composed parameter
  stays in `(−1, 1)`: composing boosts never leaves the family;
* `boost_future` — a future-pointing timelike state stays future-pointing timelike;
* `rational_boost_param` — **every** boost with rational entries (`a² − b² = 1`, `a > 0`) is
  `B(u)` for a rational `u = b/(a+1)`. The document's reviewer called the family "dense, not every
  real boost", which is right for real boosts; for rational ones the family is all of them.
* `int_boost_trivial` — an *integer* matrix of this shape is the identity or its negative: an
  integer lattice with the form `E² − p²` carries no non-trivial boost, so the exact substrate for
  boosts is `ℚ`, with growing denominators, not a lattice.

**The light-cone layer.** In the coordinates `E + p` and `E − p` a boost is diagonal: it divides
one by the Doppler factor `k(u) = (1+u)/(1−u)` and multiplies the other by it (`boost_plus`,
`boost_minus`), the invariant is their product (`inv_eq_plus_mul_minus`), and composing boosts
multiplies Doppler factors (`doppler_compose`). This is the layer in which the operator is read off
as a ratio.

**Frame change against unit change.** A change of units multiplies every component by one scale
`s` (`scale`); it commutes with every boost (`scale_boost_comm`) and multiplies the invariant by `s²`
(`scale_inv`), where a boost leaves it alone.

* `null_confound` — on a light-like state a boost *is* a change of units: `B(u)(e, e)` is
  `(e, e)` rescaled by `1/k(u)`. No light-like observation can tell a change of frame from a change
  of calibration (`null_confound_example`: `B(1/2)` and the rescaling by `1/3` agree on `(1, 1)`).
* `null_confound_opposite`, `null_rays_separate` — on the opposite light ray `(e, −e)` the same boost
  is the *reciprocal* rescaling, by `k(u)`; so light from both directions does separate a frame
  change from a unit change, and only light along one ray cannot.
* `timelike_separates` — on a state with `E² − p² ≠ 0`, a rescaled boost is determined: if
  `s B(u) q = s' B(u') q` with positive scales then `s = s'` and `u = u'`. One massive observation
  fixes both the frame and the calibration; `boost_determined` is the special case `s = s' = 1`.

**Rotations are told apart by their invariant.** The rational rotation `R(t)` preserves
`E² + p²` (`rot_euclid`); a non-trivial boost does not (`boost_not_euclid`), and a non-trivial
rotation does not preserve `E² − p²` (`rot_not_inv`). Which quadratic form survives is therefore a
classifier for the operator family, and the GLM's frame tool reads it first.

What is *not* claimed: nothing here derives `c`, and nothing maps the Euclidean Leech lattice onto
Lorentzian spacetime; `int_boost_trivial` is the reason the second is not attempted on an integer
carrier.
-/

namespace GLM.RationalBoost

/-- An energy–momentum state in one spatial dimension, natural units (`c = 1`). -/
@[ext] structure State where
  E : ℚ
  p : ℚ

/-- The Lorentz invariant `E² − p²` (the squared rest mass). -/
def inv (q : State) : ℚ := q.E ^ 2 - q.p ^ 2

/-- The Euclidean form `E² + p²`, preserved by rotations and not by boosts. -/
def euclid (q : State) : ℚ := q.E ^ 2 + q.p ^ 2

/-- `a(u) = (1+u²)/(1−u²)`, the rational `cosh`. -/
def ca (u : ℚ) : ℚ := (1 + u ^ 2) / (1 - u ^ 2)

/-- `b(u) = 2u/(1−u²)`, the rational `sinh`. -/
def sb (u : ℚ) : ℚ := 2 * u / (1 - u ^ 2)

/-- The boost `B(u)`: `E' = aE − bp`, `p' = −bE + ap`. -/
def boost (u : ℚ) (q : State) : State :=
  ⟨ca u * q.E - sb u * q.p, -(sb u) * q.E + ca u * q.p⟩

/-- The composed parameter `(u+v)/(1+uv)`. -/
def compose (u v : ℚ) : ℚ := (u + v) / (1 + u * v)

/-- The velocity ratio `β = 2u/(1+u²)`. -/
def beta (u : ℚ) : ℚ := 2 * u / (1 + u ^ 2)

/-- The light-cone coordinate `E + p`. -/
def plus (q : State) : ℚ := q.E + q.p

/-- The light-cone coordinate `E − p`. -/
def minus (q : State) : ℚ := q.E - q.p

/-- The Doppler factor `k(u) = (1+u)/(1−u)`. -/
def doppler (u : ℚ) : ℚ := (1 + u) / (1 - u)

/-- A change of units: every component rescaled by `s`. -/
def scale (s : ℚ) (q : State) : State := ⟨s * q.E, s * q.p⟩

/-- Future-pointing timelike: `|p| < E`. -/
def Future (q : State) : Prop := |q.p| < q.E

lemma one_sub_sq_ne {u : ℚ} (hu : |u| < 1) : 1 - u ^ 2 ≠ 0 := by
  have : u ^ 2 < 1 := by
    have := abs_lt.mp hu
    nlinarith
  linarith

lemma one_sub_sq_pos {u : ℚ} (hu : |u| < 1) : 0 < 1 - u ^ 2 := by
  have := abs_lt.mp hu
  nlinarith

/-- The defining identity of the parametrisation. -/
theorem ca_sq_sub_sb_sq (u : ℚ) (hu : u ^ 2 ≠ 1) : ca u ^ 2 - sb u ^ 2 = 1 := by
  have h : (1 - u ^ 2) ≠ 0 := sub_ne_zero.mpr (Ne.symm hu)
  unfold ca sb
  field_simp
  ring

/-- **A boost preserves `E² − p²`.** -/
theorem boost_inv (u : ℚ) (hu : u ^ 2 ≠ 1) (q : State) : inv (boost u q) = inv q := by
  have h := ca_sq_sub_sb_sq u hu
  unfold inv boost
  simp only
  linear_combination (q.E ^ 2 - q.p ^ 2) * h

/-- `B(0)` is the identity. -/
theorem boost_zero (q : State) : boost 0 q = q := by
  ext <;> simp [boost, ca, sb]

/-- `B(−u)` undoes `B(u)`. -/
theorem boost_neg_boost (u : ℚ) (hu : u ^ 2 ≠ 1) (q : State) :
    boost (-u) (boost u q) = q := by
  have h := ca_sq_sub_sb_sq u hu
  have hca : ca (-u) = ca u := by simp [ca]
  have hsb : sb (-u) = -sb u := by simp [sb]; ring
  ext
  · simp only [boost, hca, hsb]; linear_combination q.E * h
  · simp only [boost, hca, hsb]; linear_combination q.p * h

/-- Composing two parameters in `(−1, 1)` stays in `(−1, 1)`. -/
theorem compose_abs_lt_one {u v : ℚ} (hu : |u| < 1) (hv : |v| < 1) : |compose u v| < 1 := by
  obtain ⟨hu1, hu2⟩ := abs_lt.mp hu
  obtain ⟨hv1, hv2⟩ := abs_lt.mp hv
  have hden : 0 < 1 + u * v := by nlinarith
  unfold compose
  rw [abs_lt, lt_div_iff₀ hden, div_lt_iff₀ hden]
  constructor <;> nlinarith

lemma one_add_mul_pos {u v : ℚ} (hu : |u| < 1) (hv : |v| < 1) : 0 < 1 + u * v := by
  obtain ⟨hu1, hu2⟩ := abs_lt.mp hu
  obtain ⟨hv1, hv2⟩ := abs_lt.mp hv
  nlinarith

lemma ca_compose {u v : ℚ} (hu : |u| < 1) (hv : |v| < 1) :
    ca (compose u v) = ca u * ca v + sb u * sb v := by
  have h1 := one_sub_sq_ne hu
  have h2 := one_sub_sq_ne hv
  have h3 := (one_add_mul_pos hu hv).ne'
  have h4 := one_sub_sq_ne (compose_abs_lt_one hu hv)
  have key : 1 - compose u v ^ 2 = (1 - u ^ 2) * (1 - v ^ 2) / (1 + u * v) ^ 2 := by
    unfold compose; field_simp; ring
  unfold ca sb
  rw [key]
  unfold compose
  field_simp
  ring

lemma sb_compose {u v : ℚ} (hu : |u| < 1) (hv : |v| < 1) :
    sb (compose u v) = sb u * ca v + ca u * sb v := by
  have h1 := one_sub_sq_ne hu
  have h2 := one_sub_sq_ne hv
  have h3 := (one_add_mul_pos hu hv).ne'
  have key : 1 - compose u v ^ 2 = (1 - u ^ 2) * (1 - v ^ 2) / (1 + u * v) ^ 2 := by
    unfold compose; field_simp; ring
  unfold ca sb
  rw [key]
  unfold compose
  field_simp
  ring

/-- **Composition law.** `B(u) B(v) = B((u+v)/(1+uv))`. -/
theorem boost_boost {u v : ℚ} (hu : |u| < 1) (hv : |v| < 1) (q : State) :
    boost u (boost v q) = boost (compose u v) q := by
  ext
  · simp only [boost, ca_compose hu hv, sb_compose hu hv]; ring
  · simp only [boost, ca_compose hu hv, sb_compose hu hv]; ring

/-- The velocity ratio of `B(u)` is `b/a = 2u/(1+u²)`. -/
theorem sb_div_ca (u : ℚ) (hu : u ^ 2 ≠ 1) : sb u / ca u = beta u := by
  have h : (1 - u ^ 2) ≠ 0 := sub_ne_zero.mpr (Ne.symm hu)
  have h' : (1 + u ^ 2) ≠ 0 := by positivity
  unfold sb ca beta
  field_simp

/-- The velocity ratio is below the speed of light. -/
theorem abs_beta_lt_one {u : ℚ} (hu : |u| < 1) : |beta u| < 1 := by
  obtain ⟨h1, h2⟩ := abs_lt.mp hu
  have hden : 0 < 1 + u ^ 2 := by positivity
  unfold beta
  rw [abs_lt, lt_div_iff₀ hden, div_lt_iff₀ hden]
  constructor <;> nlinarith [sq_nonneg (u + 1), sq_nonneg (u - 1)]

/-! ## The light-cone layer -/

lemma doppler_pos {u : ℚ} (hu : |u| < 1) : 0 < doppler u := by
  obtain ⟨h1, h2⟩ := abs_lt.mp hu
  unfold doppler
  apply div_pos <;> linarith

/-- The invariant is the product of the light-cone coordinates. -/
theorem inv_eq_plus_mul_minus (q : State) : inv q = plus q * minus q := by
  unfold inv plus minus; ring

/-- A boost divides `E + p` by the Doppler factor. -/
theorem boost_plus {u : ℚ} (hu : |u| < 1) (q : State) :
    plus (boost u q) = plus q / doppler u := by
  obtain ⟨h1, h2⟩ := abs_lt.mp hu
  have a : (1 - u) ≠ 0 := by linarith
  have b : (1 + u) ≠ 0 := by linarith
  have c : (1 - u ^ 2) ≠ 0 := one_sub_sq_ne hu
  unfold plus boost doppler ca sb
  simp only
  field_simp
  ring

/-- A boost multiplies `E − p` by the Doppler factor. -/
theorem boost_minus {u : ℚ} (hu : |u| < 1) (q : State) :
    minus (boost u q) = doppler u * minus q := by
  obtain ⟨h1, h2⟩ := abs_lt.mp hu
  have a : (1 - u) ≠ 0 := by linarith
  have b : (1 + u) ≠ 0 := by linarith
  have c : (1 - u ^ 2) ≠ 0 := one_sub_sq_ne hu
  unfold minus boost doppler ca sb
  simp only
  field_simp
  ring

/-- Composing boosts multiplies Doppler factors. -/
theorem doppler_compose {u v : ℚ} (hu : |u| < 1) (hv : |v| < 1) :
    doppler (compose u v) = doppler u * doppler v := by
  obtain ⟨h1, h2⟩ := abs_lt.mp hu
  obtain ⟨h3, h4⟩ := abs_lt.mp hv
  have hd := (one_add_mul_pos hu hv).ne'
  have a : (1 - u) ≠ 0 := by linarith
  have b : (1 - v) ≠ 0 := by linarith
  have c : (1 - u) * (1 - v) ≠ 0 := mul_ne_zero a b
  have e : 1 + u * v - (u + v) ≠ 0 := by
    have : 1 + u * v - (u + v) = (1 - u) * (1 - v) := by ring
    rw [this]; exact c
  have k1 : 1 + (u + v) / (1 + u * v) = (1 + u) * (1 + v) / (1 + u * v) := by
    field_simp; ring
  have k2 : 1 - (u + v) / (1 + u * v) = (1 - u) * (1 - v) / (1 + u * v) := by
    field_simp; ring
  unfold doppler compose
  rw [k1, k2]
  field_simp

lemma future_iff (q : State) : Future q ↔ 0 < plus q ∧ 0 < minus q := by
  unfold Future plus minus
  rw [abs_lt]
  constructor
  · rintro ⟨h1, h2⟩; constructor <;> linarith
  · rintro ⟨h1, h2⟩; constructor <;> linarith

/-- **The physical branch is kept.** A future-pointing timelike state stays one under any boost. -/
theorem boost_future {u : ℚ} (hu : |u| < 1) {q : State} (h : Future q) : Future (boost u q) := by
  rw [future_iff] at h ⊢
  have hk := doppler_pos hu
  rw [boost_plus hu, boost_minus hu]
  exact ⟨div_pos h.1 hk, mul_pos hk h.2⟩

/-! ## Every rational boost is in the family; no integer one is -/

/-- **Every boost with rational entries is `B(u)` for a rational `u`**, namely `u = b/(a+1)`. -/
theorem rational_boost_param (a b : ℚ) (h : a ^ 2 - b ^ 2 = 1) (ha : 0 < a) :
    ∃ u : ℚ, |u| < 1 ∧ ca u = a ∧ sb u = b := by
  have ha1 : 0 < a + 1 := by linarith
  have hb : b ^ 2 < (a + 1) ^ 2 := by nlinarith
  have hu : |b / (a + 1)| < 1 := by
    rw [abs_div, abs_of_pos ha1, div_lt_one ha1]
    exact abs_lt_of_sq_lt_sq' hb ha1.le |> fun h => abs_lt.mpr h
  refine ⟨b / (a + 1), hu, ?_, ?_⟩
  · have hne := one_sub_sq_ne hu
    have key : 1 - (b / (a + 1)) ^ 2 = 2 / (a + 1) := by
      field_simp
      nlinarith
    unfold ca
    rw [key]
    field_simp
    nlinarith
  · have hne := one_sub_sq_ne hu
    have key : 1 - (b / (a + 1)) ^ 2 = 2 / (a + 1) := by
      field_simp
      nlinarith
    unfold sb
    rw [key]
    field_simp

/-- **An integer lattice carries no non-trivial boost**: `a² − b² = 1` over `ℤ` forces `b = 0`. -/
theorem int_boost_trivial (a b : ℤ) (h : a ^ 2 - b ^ 2 = 1) : b = 0 := by
  have h' : (a - b) * (a + b) = 1 := by linear_combination h
  rcases Int.eq_one_or_neg_one_of_mul_eq_one' h' with ⟨h1, h2⟩ | ⟨h1, h2⟩ <;> omega

/-! ## Frame change against unit change -/

/-- A change of units multiplies the invariant by `s²`. -/
theorem scale_inv (s : ℚ) (q : State) : inv (scale s q) = s ^ 2 * inv q := by
  unfold inv scale; ring

/-- A change of units commutes with every boost. -/
theorem scale_boost_comm (s u : ℚ) (q : State) : scale s (boost u q) = boost u (scale s q) := by
  ext <;> simp [scale, boost] <;> ring

/-- **On a light-like state a boost is a change of units**: `B(u)(e, e) = (e, e) / k(u)`. -/
theorem null_confound {u : ℚ} (hu : |u| < 1) (e : ℚ) :
    boost u ⟨e, e⟩ = scale (1 / doppler u) ⟨e, e⟩ := by
  obtain ⟨h1, h2⟩ := abs_lt.mp hu
  have a : (1 - u) ≠ 0 := by linarith
  have b : (1 + u) ≠ 0 := by linarith
  have c : (1 - u ^ 2) ≠ 0 := one_sub_sq_ne hu
  ext <;> simp only [boost, scale, doppler, ca, sb] <;> field_simp <;> ring

/-- The worked instance: `B(1/2)` and the rescaling by `1/3` agree on `(1, 1)`, though one changes
the frame and the other the calibration. -/
theorem null_confound_example : boost (1 / 2) ⟨1, 1⟩ = scale (1 / 3) ⟨1, 1⟩ := by
  ext <;> norm_num [boost, scale, ca, sb]

/-- On the opposite light ray a boost is the reciprocal change of units:
`B(u)(e, −e) = k(u) · (e, −e)`. -/
theorem null_confound_opposite {u : ℚ} (hu : |u| < 1) (e : ℚ) :
    boost u ⟨e, -e⟩ = scale (doppler u) ⟨e, -e⟩ := by
  obtain ⟨h1, h2⟩ := abs_lt.mp hu
  have a : (1 - u) ≠ 0 := by linarith
  have b : (1 + u) ≠ 0 := by linarith
  have c : (1 - u ^ 2) ≠ 0 := one_sub_sq_ne hu
  ext <;> simp only [boost, scale, doppler, ca, sb] <;> field_simp <;> ring

/-- **Light from both directions separates frame from units.** A change of units that agrees with
a boost on both light rays is the identity boost: a frame change scales the two rays reciprocally,
a unit change equally. -/
theorem null_rays_separate {u s : ℚ} (hu : |u| < 1)
    (h₁ : boost u ⟨1, 1⟩ = scale s ⟨1, 1⟩) (h₂ : boost u ⟨1, -1⟩ = scale s ⟨1, -1⟩) :
    u = 0 := by
  rw [null_confound hu] at h₁
  rw [null_confound_opposite hu] at h₂
  have e1 := congrArg State.E h₁
  have e2 := congrArg State.E h₂
  simp only [scale, mul_one] at e1 e2
  have hk := doppler_pos hu
  obtain ⟨hl, hr⟩ := abs_lt.mp hu
  have hk1 : doppler u = 1 := by
    have : doppler u * doppler u = 1 := by
      rw [← e2] at e1; field_simp at e1; linarith
    nlinarith
  unfold doppler at hk1
  have : (1 - u) ≠ 0 := by linarith
  field_simp at hk1
  linarith

/-- Reading `u` back from the boost entries: `b/(a+1) = u`. -/
lemma sb_div_ca_add_one {u : ℚ} (hu : |u| < 1) : sb u / (ca u + 1) = u := by
  have c := one_sub_sq_ne hu
  have hpos := one_sub_sq_pos hu
  have : ca u + 1 = 2 / (1 - u ^ 2) := by
    unfold ca; field_simp; ring
  rw [this]
  unfold sb
  field_simp

/-- **One massive observation fixes frame and calibration together.** If two rescaled boosts agree
on a state with `E² − p² ≠ 0`, their scales and their parameters are equal. -/
theorem timelike_separates {q : State} (hq : inv q ≠ 0) {s s' u u' : ℚ} (hs : 0 < s)
    (hs' : 0 < s') (hu : |u| < 1) (hu' : |u'| < 1)
    (h : scale s (boost u q) = scale s' (boost u' q)) : s = s' ∧ u = u' := by
  have hE := congrArg State.E h
  have hp := congrArg State.p h
  simp only [scale, boost] at hE hp
  set A := s * ca u - s' * ca u'
  set B := s * sb u - s' * sb u'
  have hinv : q.E ^ 2 - q.p ^ 2 ≠ 0 := hq
  have hA : A * (q.E ^ 2 - q.p ^ 2) = 0 := by
    simp only [A]; linear_combination q.E * hE - q.p * hp
  have hB : B * (q.E ^ 2 - q.p ^ 2) = 0 := by
    simp only [B]; linear_combination q.p * hE - q.E * hp
  have hA0 : s * ca u = s' * ca u' := by
    have := (mul_eq_zero.mp hA).resolve_right hinv; simp only [A] at this; linarith
  have hB0 : s * sb u = s' * sb u' := by
    have := (mul_eq_zero.mp hB).resolve_right hinv; simp only [B] at this; linarith
  have i1 := ca_sq_sub_sb_sq u (by have := one_sub_sq_ne hu; intro h; apply this; linarith)
  have i2 := ca_sq_sub_sb_sq u' (by have := one_sub_sq_ne hu'; intro h; apply this; linarith)
  have hsq : s ^ 2 = s' ^ 2 := by
    have e1 : s ^ 2 = (s * ca u) ^ 2 - (s * sb u) ^ 2 := by linear_combination (-s ^ 2) * i1
    have e2 : s' ^ 2 = (s' * ca u') ^ 2 - (s' * sb u') ^ 2 := by
      linear_combination (-s' ^ 2) * i2
    rw [e1, e2, hA0, hB0]
  have hss : s = s' := by
    have := (sq_eq_sq₀ hs.le hs'.le).mp hsq; exact this
  refine ⟨hss, ?_⟩
  subst hss
  have hca : ca u = ca u' := mul_left_cancel₀ hs.ne' hA0
  have hsb : sb u = sb u' := mul_left_cancel₀ hs.ne' hB0
  rw [← sb_div_ca_add_one hu, ← sb_div_ca_add_one hu', hca, hsb]

/-- One non-null observation determines the boost. -/
theorem boost_determined {q : State} (hq : inv q ≠ 0) {u u' : ℚ} (hu : |u| < 1)
    (hu' : |u'| < 1) (h : boost u q = boost u' q) : u = u' := by
  have h' : scale 1 (boost u q) = scale 1 (boost u' q) := by rw [h]
  exact (timelike_separates hq one_pos one_pos hu hu' h').2

/-! ## Rotations, and the invariant as a classifier -/

/-- The rational rotation `R(t)`, `cos = (1−t²)/(1+t²)`, `sin = 2t/(1+t²)`. -/
def rot (t : ℚ) (q : State) : State :=
  ⟨(1 - t ^ 2) / (1 + t ^ 2) * q.E - 2 * t / (1 + t ^ 2) * q.p,
   2 * t / (1 + t ^ 2) * q.E + (1 - t ^ 2) / (1 + t ^ 2) * q.p⟩

/-- A rotation preserves `E² + p²`. -/
theorem rot_euclid (t : ℚ) (q : State) : euclid (rot t q) = euclid q := by
  have h : (1 + t ^ 2) ≠ 0 := by positivity
  unfold euclid rot
  simp only
  field_simp
  ring

/-- A non-trivial boost does not preserve `E² + p²`. -/
theorem boost_not_euclid {u : ℚ} (hu : |u| < 1) (hu0 : u ≠ 0) :
    euclid (boost u ⟨1, 0⟩) ≠ euclid ⟨1, 0⟩ := by
  have i := ca_sq_sub_sb_sq u (by have := one_sub_sq_ne hu; intro h; apply this; linarith)
  have hb : sb u ≠ 0 := by
    unfold sb
    exact div_ne_zero (mul_ne_zero two_ne_zero hu0) (one_sub_sq_ne hu)
  unfold euclid boost
  simp only [mul_one, mul_zero, sub_zero, add_zero]
  intro h
  have : sb u ^ 2 = 0 := by nlinarith
  exact hb (pow_eq_zero_iff (n := 2) (by norm_num) |>.mp this)

/-- A non-trivial rotation does not preserve `E² − p²`. -/
theorem rot_not_inv {t : ℚ} (ht : t ≠ 0) : inv (rot t ⟨1, 0⟩) ≠ inv ⟨1, 0⟩ := by
  have h : (1 + t ^ 2) ≠ 0 := by positivity
  have hpos : 0 < 1 + t ^ 2 := by positivity
  unfold inv rot
  simp only [mul_one, mul_zero, sub_zero, add_zero]
  intro heq
  rw [div_pow, div_pow, ← sub_div, div_eq_iff (pow_ne_zero 2 h)] at heq
  have ht2 : 0 < t ^ 2 := by positivity
  nlinarith [sq_nonneg t]

end GLM.RationalBoost
