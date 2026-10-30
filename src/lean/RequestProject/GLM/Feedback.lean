/-
# Error feedback through a rational matrix, and the symmetry it must respect

`DeltaSigma.lean` and `Cascade.lean` chase a scalar.  The to-do list asks for
the next structure: a modulator on *many* coordinates at once whose past
quantisation error is fed back through a rational matrix `A`, with `A` chosen
to commute with a symmetry of the carrier.  This file builds that loop and
proves three things about it.

**It is a genuine loop.**  `efErr_abs_le_half` — whatever `A` is, the
instantaneous quantisation error never leaves `[-1/2, 1/2]`, coordinate by
coordinate; the nonlinearity is bounded even when the linear part is not.

**Only one feedback matrix tracks the input.**  `efSum_eq` is the exact
accounting identity

```
∑_{k<N} (u k − y k)  =  (∑_{k<N} e k) − (∑_{k<N} s k),        s (k+1) = A e k,
```

and at `A = 1` the second sum is the first one shifted, so everything cancels
but a single bounded term: `efAverage_error_le_identity` gives
`|average of the bits − running mean of the input| ≤ 1/(2N)`, in every
coordinate and for every input.  That is the vector form of the `1/N` law, and
it is *sharper* than the scalar accumulator's, because the error that survives
is one quantisation step rather than one accumulator state.

Contracting the feedback destroys it, and not by a little:
`halfFeedback_dead_zone` runs the same loop with `A = 1/2` on the constant
input `1/4` and shows the quantiser **never fires** — `y k = 0` for every `k`,
the running average error is exactly `1/4` for ever, and the loop is dead
rather than slow.  A feedback matrix is not a free parameter: it has to fix the
direction the input lives in.

**The symmetry is exact.**  `efOut_equivariant` — if a permutation `σ` of the
coordinates leaves `A` invariant (`A (σ i) (σ j) = A i j`), then permuting the
input permutes the output, tick for tick.  Noise shaping through a
symmetry-commuting matrix therefore commutes with that symmetry exactly, with
no averaging and no limit: the whole trajectory is equivariant.  This is what
makes a feedback matrix built out of a group action safe to put inside a
carrier the same group acts on.
-/
import Mathlib

namespace GLM.Feedback

open Finset

/-! ## 1.  The quantiser -/

/-- Nearest integer, ties resolved upward. -/
def quant (x : ℚ) : ℤ := ⌊x + 1 / 2⌋

theorem quant_sub_lt (x : ℚ) : x - (quant x : ℚ) < 1 / 2 := by
  have h : (x + 1 / 2) - 1 < (⌊x + 1 / 2⌋ : ℚ) := by
    have := Int.sub_one_lt_floor (x + 1 / 2)
    linarith
  simp only [quant]
  linarith

theorem neg_half_le_quant_sub (x : ℚ) : -(1 / 2) ≤ x - (quant x : ℚ) := by
  have h : (⌊x + 1 / 2⌋ : ℚ) ≤ x + 1 / 2 := Int.floor_le _
  simp only [quant]
  linarith

theorem quant_err_abs_le (x : ℚ) : |x - (quant x : ℚ)| ≤ 1 / 2 := by
  rw [abs_le]
  exact ⟨neg_half_le_quant_sub x, le_of_lt (quant_sub_lt x)⟩

theorem quant_eq_zero {x : ℚ} (h0 : -(1 / 2) ≤ x) (h1 : x < 1 / 2) :
    quant x = 0 := by
  simp only [quant]
  rw [Int.floor_eq_zero_iff, Set.mem_Ico]
  constructor <;> linarith

/-! ## 2.  The loop -/

variable {n : ℕ}

/-- The feedback state: `s 0 = 0` and `s (k+1) = A · e k`, where `e k` is the
quantisation error committed at tick `k`. -/
def efState (A : Fin n → Fin n → ℚ) (u : ℕ → Fin n → ℚ) : ℕ → Fin n → ℚ
  | 0 => fun _ => 0
  | k + 1 => fun i =>
      ∑ j, A i j *
        ((u k j + efState A u k j) - (quant (u k j + efState A u k j) : ℚ))

/-- The value presented to the quantiser at tick `k`. -/
def efIn (A : Fin n → Fin n → ℚ) (u : ℕ → Fin n → ℚ) (k : ℕ) (i : Fin n) : ℚ :=
  u k i + efState A u k i

/-- The emitted integer, as a rational. -/
def efOut (A : Fin n → Fin n → ℚ) (u : ℕ → Fin n → ℚ) (k : ℕ) (i : Fin n) : ℚ :=
  (quant (efIn A u k i) : ℚ)

/-- The instantaneous quantisation error. -/
def efErr (A : Fin n → Fin n → ℚ) (u : ℕ → Fin n → ℚ) (k : ℕ) (i : Fin n) : ℚ :=
  efIn A u k i - efOut A u k i

theorem efState_succ (A : Fin n → Fin n → ℚ) (u : ℕ → Fin n → ℚ)
    (k : ℕ) (i : Fin n) :
    efState A u (k + 1) i = ∑ j, A i j * efErr A u k j := by
  simp [efState, efErr, efIn, efOut]

theorem efErr_abs_le_half (A : Fin n → Fin n → ℚ) (u : ℕ → Fin n → ℚ)
    (k : ℕ) (i : Fin n) : |efErr A u k i| ≤ 1 / 2 :=
  quant_err_abs_le _

/-- The one-tick accounting identity: input minus output is the error made now
less the error fed forward from before. -/
theorem efStep_eq (A : Fin n → Fin n → ℚ) (u : ℕ → Fin n → ℚ)
    (k : ℕ) (i : Fin n) :
    u k i - efOut A u k i = efErr A u k i - efState A u k i := by
  simp only [efErr, efIn]
  ring

/-- Summed over a window: what the bits miss is the error still held minus the
error already fed back. -/
theorem efSum_eq (A : Fin n → Fin n → ℚ) (u : ℕ → Fin n → ℚ)
    (N : ℕ) (i : Fin n) :
    ∑ k ∈ range N, (u k i - efOut A u k i)
      = (∑ k ∈ range N, efErr A u k i) - ∑ k ∈ range N, efState A u k i := by
  rw [← Finset.sum_sub_distrib]
  exact Finset.sum_congr rfl fun k _ => efStep_eq A u k i

/-! ## 3.  The identity feedback, and the `1/(2N)` law -/

/-- The identity matrix over `Fin n`. -/
def idMat (n : ℕ) : Fin n → Fin n → ℚ := fun i j => if i = j then 1 else 0

theorem efState_id_succ (u : ℕ → Fin n → ℚ) (k : ℕ) (i : Fin n) :
    efState (idMat n) u (k + 1) i = efErr (idMat n) u k i := by
  rw [efState_succ]
  simp [idMat]

/-- With identity feedback the window sum telescopes to a single error term. -/
theorem efSum_id (u : ℕ → Fin n → ℚ) (N : ℕ) (i : Fin n) :
    ∑ k ∈ range (N + 1), (u k i - efOut (idMat n) u k i)
      = efErr (idMat n) u N i := by
  induction N with
  | zero =>
      simp [efState, efErr, efIn, efOut]
  | succ N ih =>
      rw [Finset.sum_range_succ, ih, efStep_eq, efState_id_succ]
      ring

/-- **The vector `1/(2N)` law.**  Whatever the input does, the average of the
emitted integers is within `1/(2N)` of the input's running mean, in every
coordinate. -/
theorem efAverage_error_le_identity (u : ℕ → Fin n → ℚ) (N : ℕ) (hN : 0 < N)
    (i : Fin n) :
    |(∑ k ∈ range N, u k i) / N - (∑ k ∈ range N, efOut (idMat n) u k i) / N|
      ≤ 1 / (2 * N) := by
  obtain ⟨M, rfl⟩ : ∃ M, N = M + 1 := ⟨N - 1, by omega⟩
  have hpos : (0 : ℚ) < ((M : ℚ) + 1) := by positivity
  have hsum := efSum_id u M i
  have hdiv :
      (∑ k ∈ range (M + 1), u k i) / ((M : ℚ) + 1)
        - (∑ k ∈ range (M + 1), efOut (idMat n) u k i) / ((M : ℚ) + 1)
        = efErr (idMat n) u M i / ((M : ℚ) + 1) := by
    rw [div_sub_div_same, ← Finset.sum_sub_distrib, hsum]
  push_cast
  rw [hdiv, abs_div, abs_of_pos hpos]
  have h := efErr_abs_le_half (idMat n) u M i
  have hstep : |efErr (idMat n) u M i| / ((M : ℚ) + 1)
      ≤ (1 / 2) / ((M : ℚ) + 1) := by gcongr
  have hrw : (1 : ℚ) / 2 / ((M : ℚ) + 1) = 1 / (2 * ((M : ℚ) + 1)) := by
    field_simp
  linarith [hstep, hrw.le, hrw.ge]

/-! ## 4.  A contracting feedback is not slow, it is dead -/

theorem half_pow_le (k : ℕ) : ((1 : ℚ) / 2) ^ (k + 2) ≤ 1 / 4 := by
  have h : ((1 : ℚ) / 2) ^ (k + 2) = (1 / 2) ^ k * (1 / 4) := by ring
  have hk : ((1 : ℚ) / 2) ^ k ≤ 1 := pow_le_one₀ (by norm_num) (by norm_num)
  rw [h]; linarith

theorem half_pow_pos (k : ℕ) : (0 : ℚ) < (1 / 2) ^ (k + 2) := by positivity

/-- Halved feedback in one coordinate. -/
def halfMat : Fin 1 → Fin 1 → ℚ := fun _ _ => 1 / 2

/-- The constant input `1/4` in one coordinate. -/
def quarterIn : ℕ → Fin 1 → ℚ := fun _ _ => 1 / 4

theorem halfFeedback_state (k : ℕ) (i : Fin 1) :
    efState halfMat quarterIn k i = 1 / 4 - (1 / 2) ^ (k + 2) := by
  induction k with
  | zero => norm_num [efState]
  | succ k ih =>
      have hin : efIn halfMat quarterIn k i = 1 / 2 - (1 / 2) ^ (k + 2) := by
        simp only [efIn, quarterIn, ih]; ring
      have hquant : quant (1 / 2 - (1 / 2) ^ (k + 2) : ℚ) = 0 :=
        quant_eq_zero (by linarith [half_pow_le k, half_pow_pos k])
          (by linarith [half_pow_pos k])
      have herr : ∀ j : Fin 1, efErr halfMat quarterIn k j
          = 1 / 2 - (1 / 2) ^ (k + 2) := by
        intro j
        have hj : j = i := Subsingleton.elim _ _
        subst hj
        simp only [efErr, efOut, hin, hquant]
        norm_num
      rw [efState_succ]
      simp only [halfMat, herr]
      rw [Finset.sum_const, Finset.card_univ, Fintype.card_fin]
      ring

/-- **The dead zone.**  With halved feedback the quantiser never fires on the
constant input `1/4`: every emitted value is `0`. -/
theorem halfFeedback_out_zero (k : ℕ) (i : Fin 1) :
    efOut halfMat quarterIn k i = 0 := by
  have hin : efIn halfMat quarterIn k i = 1 / 2 - (1 / 2) ^ (k + 2) := by
    simp only [efIn, quarterIn, halfFeedback_state k i]; ring
  have hquant : quant (1 / 2 - (1 / 2) ^ (k + 2) : ℚ) = 0 :=
    quant_eq_zero (by linarith [half_pow_le k, half_pow_pos k])
      (by linarith [half_pow_pos k])
  rw [efOut, hin, hquant]
  norm_num

/-- So the average error never decreases: it is exactly the input, for ever.
Contrast `efAverage_error_le_identity`, which is `1/(2N)`. -/
theorem halfFeedback_dead_zone (N : ℕ) (hN : 0 < N) (i : Fin 1) :
    (∑ k ∈ range N, quarterIn k i) / N
      - (∑ k ∈ range N, efOut halfMat quarterIn k i) / N = 1 / 4 := by
  have h0 : ∑ k ∈ range N, efOut halfMat quarterIn k i = 0 := by
    simp [halfFeedback_out_zero]
  have h1 : ∑ k ∈ range N, quarterIn k i = (N : ℚ) * (1 / 4) := by
    simp [quarterIn]
  rw [h0, h1]
  have hN' : (N : ℚ) ≠ 0 := Nat.cast_ne_zero.mpr (by omega)
  field_simp
  ring

/-! ## 5.  A symmetry-commuting feedback matrix gives an equivariant loop -/

/-- Permuting the coordinates of an input. -/
def permIn (σ : Equiv.Perm (Fin n)) (u : ℕ → Fin n → ℚ) : ℕ → Fin n → ℚ :=
  fun k i => u k (σ i)

theorem efState_equivariant (A : Fin n → Fin n → ℚ) (σ : Equiv.Perm (Fin n))
    (hA : ∀ i j, A (σ i) (σ j) = A i j) (u : ℕ → Fin n → ℚ) :
    ∀ (k : ℕ) (i : Fin n),
      efState A (permIn σ u) k i = efState A u k (σ i) := by
  intro k
  induction k with
  | zero => intro i; simp [efState]
  | succ k ih =>
      intro i
      simp only [efState]
      rw [← Equiv.sum_comp σ (fun j => A (σ i) j *
        ((u k j + efState A u k j) - (quant (u k j + efState A u k j) : ℚ)))]
      refine Finset.sum_congr rfl fun j _ => ?_
      simp only [permIn]
      rw [ih j, hA i j]

/-- **Equivariance.**  A feedback matrix invariant under `σ` gives a loop that
commutes with `σ`: permuting the input permutes the output at every tick, with
no error term and no limit. -/
theorem efOut_equivariant (A : Fin n → Fin n → ℚ) (σ : Equiv.Perm (Fin n))
    (hA : ∀ i j, A (σ i) (σ j) = A i j) (u : ℕ → Fin n → ℚ)
    (k : ℕ) (i : Fin n) :
    efOut A (permIn σ u) k i = efOut A u k (σ i) := by
  simp [efOut, efIn, permIn, efState_equivariant A σ hA u k i]

theorem efErr_equivariant (A : Fin n → Fin n → ℚ) (σ : Equiv.Perm (Fin n))
    (hA : ∀ i j, A (σ i) (σ j) = A i j) (u : ℕ → Fin n → ℚ)
    (k : ℕ) (i : Fin n) :
    efErr A (permIn σ u) k i = efErr A u k (σ i) := by
  simp [efErr, efIn, permIn, efOut, efState_equivariant A σ hA u k i]

/-- The identity feedback is invariant under *every* permutation, so the
`1/(2N)` loop of §3 is equivariant under the whole symmetric group — and hence
under any subgroup a carrier's symmetry supplies. -/
theorem idMat_perm_invariant (σ : Equiv.Perm (Fin n)) (i j : Fin n) :
    idMat n (σ i) (σ j) = idMat n i j := by
  simp [idMat, σ.injective.eq_iff]

end GLM.Feedback
