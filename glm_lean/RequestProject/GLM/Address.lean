/-
# Addressing: what a lattice address can and cannot mean

`overlay/glm_universal/reasoning/lean_address.py` gives every declaration of
this development a **deterministic Leech address**: the declaration is reduced
to twenty four integer counts, the counts are multiplied by a scale, and the
result is sent to its nearest point of the lattice.  This file proves the four
things that make that a defensible construction rather than a decoration, and
one thing that decides the scale.

## The abstract part: a quantiser is a resolution

A `Quantiser L ρ` is a map into `L` that moves nothing further than `ρ` and
never returns a point of `L` further away than the nearest one.  Everything
about addressing follows from just those three properties, with no mention of
which lattice is used:

* `Quantiser.fixed` — a point already in `L` is its own address.  This is what
  makes the *scale* matter, see below.
* `Quantiser.dist_le` — addresses of nearby things are nearby:
  `dist (Q x) (Q y) ≤ dist x y + 2ρ`.
* `Quantiser.ne_of_far` — and conversely, things further apart than `2ρ`
  cannot share an address.  So an address separates what the feature map
  separates by enough, and *only* that.
* `address_congr` — the one that answers "does the address mean the
  declaration?".  An address is `Q (scale • features d)`, so equal features
  force equal addresses: the address cannot carry a single distinction that
  the feature map has already thrown away.  Meaning lives in the feature map;
  the lattice only supplies somewhere to put it.  `Conflates` is the resulting
  equivalence relation — the boundary of this layer in the sense of
  `Layers.lean` — and `injective_features_of_injective_address` says an
  injective address forces an injective feature map, never the other way
  round.

## The integer part: the address *is* the feature vector

`readback_unique`: if two feature vectors are both within `ρ` of the same
address coordinatewise and the scale exceeds `2ρ`, they are equal.  So under
that condition the address determines the features exactly — the encoding is
lossless, and the "read the address back as a sentence" operation of the Python
module is well defined rather than a guess.

## Why the scale is 9 and not 8

`eightZ_mem_leech`: **`8ℤ²⁴ ⊆ Λ`.**  Every vector all of whose coordinates are
multiples of 8 is already in the Leech lattice — the parity condition holds
with `m = 0`, the mod-4 support is empty and the empty word is a Golay
codeword, and the coordinate sum is a multiple of 8.  Combined with
`Quantiser.fixed` this says that at scale 8 the decoder returns its input: the
"Leech address" of a declaration would be nothing but its feature vector
multiplied by 8, and the lattice would be doing no work at all.

`nineZ_not_mem_leech` shows the degeneracy is genuinely a property of 8: the
vector `(9, 0, …, 0)` is not in the lattice, because 9 is odd and 0 is even, so
no single parity `m` covers both coordinates.  At scale 9 the decoder has to
choose a point, and — by `readback_unique`, since `2 * 4 < 9` — it can do so
without losing anything.

The lattice used here is the standard mod-2/mod-4/mod-8 description, stated
against the concrete Golay code of `Golay/Code.lean` rather than an abstract
one, so `InLeech` is the same predicate the substrate's `leech_construct.py`
tests.
-/
import Mathlib
import RequestProject.GLM.Golay.Code

namespace GLM.Address

open Finset

/-! ## 1.  Quantisers in the abstract -/

/-- A nearest-point map onto a set `L`, with a covering bound `ρ`.

`mem` says an address is a legal address, `close` that addressing moves a point
by at most `ρ`, and `best` that no legal address is closer.  The Leech decoder
of `reasoning/analogy.py` is exactly this, with `L` the lattice and `ρ = 4` in
the integer model where the minimal squared norm is 32. -/
structure Quantiser (X : Type*) [MetricSpace X] (L : Set X) (rho : ℝ) where
  /-- The map itself. -/
  toFun : X → X
  /-- Every address is a point of `L`. -/
  mem : ∀ x, toFun x ∈ L
  /-- Addressing moves a point by at most the covering radius. -/
  close : ∀ x, dist x (toFun x) ≤ rho
  /-- No point of `L` is closer than the address. -/
  best : ∀ x, ∀ y ∈ L, dist x (toFun x) ≤ dist x y

namespace Quantiser

variable {X : Type*} [MetricSpace X] {L : Set X} {rho : ℝ}

/-- **A legal point is its own address.**  If the thing being addressed is
already in the lattice, the decoder returns it unchanged — so a scale that puts
every feature vector inside the lattice makes the decoder an identity map. -/
theorem fixed (Q : Quantiser X L rho) {x : X} (hx : x ∈ L) : Q.toFun x = x := by
  have h := Q.best x x hx
  rw [dist_self] at h
  have : dist x (Q.toFun x) = 0 := le_antisymm h dist_nonneg
  exact (dist_eq_zero.mp this).symm

/-- **Nearby things get nearby addresses.**  Addressing is 1-Lipschitz up to
twice the covering radius. -/
theorem dist_le (Q : Quantiser X L rho) (x y : X) :
    dist (Q.toFun x) (Q.toFun y) ≤ dist x y + 2 * rho := by
  have h1 : dist (Q.toFun x) x ≤ rho := by
    rw [dist_comm]; exact Q.close x
  have h2 : dist y (Q.toFun y) ≤ rho := Q.close y
  calc dist (Q.toFun x) (Q.toFun y)
      ≤ dist (Q.toFun x) x + dist x (Q.toFun y) := dist_triangle _ _ _
    _ ≤ dist (Q.toFun x) x + (dist x y + dist y (Q.toFun y)) := by
        gcongr; exact dist_triangle _ _ _
    _ ≤ rho + (dist x y + rho) := by gcongr
    _ = dist x y + 2 * rho := by ring

/-- **Two things far enough apart cannot share an address.**  The converse of
`dist_le`: an address can only conflate points closer than `2ρ`. -/
theorem ne_of_far (Q : Quantiser X L rho) {x y : X} (h : 2 * rho < dist x y) :
    Q.toFun x ≠ Q.toFun y := by
  intro heq
  have h1 : dist x (Q.toFun x) ≤ rho := Q.close x
  have h2 : dist y (Q.toFun y) ≤ rho := Q.close y
  have : dist x y ≤ 2 * rho := by
    calc dist x y ≤ dist x (Q.toFun x) + dist (Q.toFun x) y := dist_triangle _ _ _
      _ = dist x (Q.toFun x) + dist (Q.toFun y) y := by rw [heq]
      _ = dist x (Q.toFun x) + dist y (Q.toFun y) := by rw [dist_comm (Q.toFun y) y]
      _ ≤ rho + rho := by gcongr
      _ = 2 * rho := by ring
  exact absurd this (not_le.mpr h)

end Quantiser

/-! ## 2.  Addresses of declarations, and what they can mean -/

section Addressing

variable {D X : Type*} [MetricSpace X] {L : Set X} {rho : ℝ}

/-- The address of a subject: quantise its feature vector.  `feat` is whatever
the feature map is — for this development, the twenty four counts of
`FEATURE_NAMES` scaled by 9. -/
def address (Q : Quantiser X L rho) (feat : D → X) (d : D) : X :=
  Q.toFun (feat d)

/-- **The address cannot mean more than the features do.**  Equal features
force equal addresses, so every distinction visible in the address book is a
distinction the feature map already made.  This is the precise sense in which
"the address means the declaration" is false and "the address means the
features" is true. -/
theorem address_congr (Q : Quantiser X L rho) (feat : D → X) {a b : D}
    (h : feat a = feat b) : address Q feat a = address Q feat b := by
  unfold address; rw [h]

/-- Two subjects are conflated by the addressing when they share an address. -/
def Conflates (Q : Quantiser X L rho) (feat : D → X) (a b : D) : Prop :=
  address Q feat a = address Q feat b

theorem conflates_refl (Q : Quantiser X L rho) (feat : D → X) (a : D) :
    Conflates Q feat a a := rfl

theorem conflates_symm (Q : Quantiser X L rho) (feat : D → X) {a b : D}
    (h : Conflates Q feat a b) : Conflates Q feat b a := h.symm

theorem conflates_trans (Q : Quantiser X L rho) (feat : D → X) {a b c : D}
    (hab : Conflates Q feat a b) (hbc : Conflates Q feat b c) :
    Conflates Q feat a c := hab.trans hbc

/-- **An injective address forces an injective feature map.**  Never the other
way round: the feature map can separate two declarations that the quantiser
then places at the same point. -/
theorem injective_features_of_injective_address (Q : Quantiser X L rho)
    (feat : D → X) (h : Function.Injective (address Q feat)) :
    Function.Injective feat := by
  intro a b hab
  exact h (address_congr Q feat hab)

/-- Distinct addresses are a certificate of distinct subjects. -/
theorem ne_of_address_ne (Q : Quantiser X L rho) (feat : D → X) {a b : D}
    (h : address Q feat a ≠ address Q feat b) : a ≠ b := by
  intro hab; exact h (by rw [hab])

end Addressing

/-! ## 3.  Reading the address back: the integer statement -/

/-- **The address determines the feature vector.**  If two integer feature
vectors are each within `rho` of the same address in every coordinate, and the
scale is more than `2 * rho`, they are the same vector.  With `rho = 4` — the
covering radius of the Leech lattice in the integer model — any scale of 9 or
more makes the encoding lossless. -/
theorem readback_unique {n : ℕ} {scale rho : ℤ} (hrho : 0 ≤ rho)
    (hscale : 2 * rho < scale) (p f g : Fin n → ℤ)
    (hf : ∀ i, |p i - scale * f i| ≤ rho)
    (hg : ∀ i, |p i - scale * g i| ≤ rho) : f = g := by
  funext i
  have h1 := abs_le.mp (hf i)
  have h2 := abs_le.mp (hg i)
  have hspos : 0 < scale := by omega
  by_contra hne
  rcases lt_or_gt_of_ne hne with h | h
  · have step : scale * 1 ≤ scale * (g i - f i) :=
      mul_le_mul_of_nonneg_left (by omega) (le_of_lt hspos)
    have e : scale * (g i - f i) = scale * g i - scale * f i := by ring
    rw [mul_one, e] at step
    linarith [h1.1, h1.2, h2.1, h2.2]
  · have step : scale * 1 ≤ scale * (f i - g i) :=
      mul_le_mul_of_nonneg_left (by omega) (le_of_lt hspos)
    have e : scale * (f i - g i) = scale * f i - scale * g i := by ring
    rw [mul_one, e] at step
    linarith [h1.1, h1.2, h2.1, h2.2]

/-! ## 4.  The Leech lattice, and why the scale is not 8 -/

/-- Membership of the Leech lattice, in the standard mod-2 / mod-4 / mod-8
form: for one parity `m`, every coordinate is congruent to `m` mod 2, the
coordinates congruent to `m + 2` mod 4 form a Golay codeword, and the
coordinate sum is congruent to `4 * m` mod 8.  This is the predicate the
substrate's `leech_construct.py` sieve tests. -/
def leechSupport (x : Fin 24 → ℤ) (m : ℤ) : GLM.Golay24.Word :=
  Finset.univ.filter (fun i => (x i - m) % 4 ≠ 0)

def InLeech (x : Fin 24 → ℤ) : Prop :=
  ∃ m : ℤ,
    (∀ i, (x i - m) % 2 = 0) ∧
    GLM.Golay24.IsCodeword (leechSupport x m) ∧
    (∑ i, x i) % 8 = (4 * m) % 8

/-- **`8ℤ²⁴ ⊆ Λ`.**  Every vector whose coordinates are all multiples of 8 is
already a Leech point, so the nearest-point decoder returns it unchanged.  That
is why a scale which is a multiple of 8 makes the address a relabelled cube
rather than a lattice address. -/
theorem eightZ_mem_leech (y : Fin 24 → ℤ) : InLeech (fun i => 8 * y i) := by
  classical
  refine ⟨0, ?_, ?_, ?_⟩
  · intro i; simp; omega
  · have hempty : leechSupport (fun i => 8 * y i) 0 = (∅ : GLM.Golay24.Word) := by
      refine Finset.eq_empty_of_forall_notMem ?_
      intro i hi
      simp only [leechSupport, Finset.mem_filter, Finset.mem_univ,
        true_and] at hi
      exact hi (by omega)
    rw [hempty]
    exact GLM.Golay24.isCodeword_empty
  · have : (∑ i, 8 * y i) = 8 * ∑ i, y i := by rw [Finset.mul_sum]
    rw [this]
    simp [Int.mul_emod_right]

/-- The degeneracy is a property of 8, not of scaling.  `(9, 0, …, 0)` is not
a Leech point: 9 is odd and 0 is even, so no parity `m` covers both
coordinates. -/
theorem nineZ_not_mem_leech :
    ¬ InLeech (fun i : Fin 24 => if i = 0 then 9 else 0) := by
  rintro ⟨m, hpar, -, -⟩
  have h0 : ((9 : ℤ) - m) % 2 = 0 := by simpa using hpar 0
  have h1 : ((0 : ℤ) - m) % 2 = 0 := by simpa using hpar 1
  omega

end GLM.Address
