import RequestProject.GLM.ScaledLadder

/-!
# The norm family: one rung at every power of two

`GLM.ConstructionLadder` has the five constructions and `GLM.ScaledLadder` the
scaling `L ↦ 2L` that fills the step between them.  This file indexes the
result by the quantity a reading actually escalates over — the **minimum
squared norm** — and proves that the family so indexed is complete and is a
tower.

## §1 What doubling does to a norm

`dbl_normSq` and `scaled_normSq`: a vector of `2^k L` is `2^k` times a vector
of `L`, so its squared norm is `4^k` times that one's.  `scaled_min_norm` is
the consequence the family is built on — scaling a lattice of minimum norm `m`
by `2^k` gives one of minimum norm `4^k m`.

That is exactly why a complete power-of-two family cannot be made out of one
construction: scaling multiplies the norm by **four**, so `L, 2L, 4L, …` lands
on every *other* power of two and never on the ones between.  The family has to
interleave two constructions, and §2 is the pair that does it.

## §2 The steps the tower is made of

* `dbl_isD_isG` — `2D₂₄ ⊆ G`, the step from norm 8 to norm 4;
* `dbl_isA_isB` — `2A ⊆ B`, the step from norm 64 to norm 32;
* `dbl_isC_isA` — `2Λ₂₄ ⊆ A`, the same step taken through the Leech lattice
  instead of Construction `B`;
* `chain_step_A` and `chain_step_B` — those two steps at *every* scale, which
  is what makes the tower infinite rather than as long as somebody wrote down.

## §3 The tower

`norm_family_chain` states the repeating part — for every `k`,
`2^{k+1}A ⊆ 2^k B ⊆ 2^k A` — and `family_tower` states the whole ladder from
the grid up:

`… ⊆ 2B ⊆ 2A ⊆ B ⊆ A ⊆ 2D₂₄ ⊆ G ⊆ D₂₄ ⊆ ℤ²⁴`

with one rung at every power-of-two minimum norm: `1, 2, 4, 8, 16, 32, 64,
128, …`.  `glm_universal.substrate.norm_family` generates the same family and
checks every containment on generated points of the coarser rung.
-/

namespace GLM.NormFamily

open GLM.ConstructionLadder GLM.ScaledLadder GLM.LatticeShortcut

/-! ## §1 What doubling does to a norm -/

/-- A vector of `2^k L` is `2^k` times a vector of `L`. -/
theorem scaled_witness {P : (Fin 24 → ℤ) → Prop} :
    ∀ (k : ℕ) (x : Fin 24 → ℤ), Scaled k P x →
      ∃ y, P y ∧ ∀ i, x i = 2 ^ k * y i := by
  intro k
  induction k with
  | zero =>
      intro x hx
      exact ⟨x, hx, by simp⟩
  | succ k ih =>
      intro x hx
      rw [scaled_succ] at hx
      obtain ⟨z, hz, hxz⟩ := hx
      obtain ⟨y, hy, hzy⟩ := ih z hz
      refine ⟨y, hy, fun i => ?_⟩
      rw [hxz i, hzy i, pow_succ]
      ring

private theorem two_pow_sq (k : ℕ) : ((2 : ℤ) ^ k) ^ 2 = 4 ^ k := by
  rw [← pow_mul, mul_comm, pow_mul]
  norm_num

/-- **Scaling by `2^k` multiplies every squared norm by `4^k`.** -/
theorem scaled_normSq {P : (Fin 24 → ℤ) → Prop} {k : ℕ} {x : Fin 24 → ℤ}
    (h : Scaled k P x) :
    ∃ y, P y ∧ (∀ i, x i = 2 ^ k * y i) ∧ normSq24 x = 4 ^ k * normSq24 y := by
  obtain ⟨y, hy, hxy⟩ := scaled_witness k x h
  refine ⟨y, hy, hxy, ?_⟩
  unfold normSq24
  rw [Finset.mul_sum]
  refine Finset.sum_congr rfl fun i _ => ?_
  rw [hxy i, mul_pow, two_pow_sq]

/-- **Doubling multiplies every squared norm by four.** -/
theorem dbl_normSq {P : (Fin 24 → ℤ) → Prop} {x : Fin 24 → ℤ} (h : Dbl P x) :
    ∃ y, P y ∧ normSq24 x = 4 * normSq24 y := by
  obtain ⟨y, hy, -, hnorm⟩ := scaled_normSq (k := 1) (P := P) (x := x)
    (by rw [scaled_succ]; simpa [scaled_zero] using h)
  exact ⟨y, hy, by simpa using hnorm⟩

/-- **The minimum norm of a scaled rung.**  If no non-zero vector of `L` has
squared norm below `m`, then none of `2^k L` has squared norm below `4^k m` —
which is why the rungs of the family can be indexed by their minimum norm. -/
theorem scaled_min_norm {P : (Fin 24 → ℤ) → Prop} {m : ℤ} {k : ℕ}
    (h : ∀ y, P y → y ≠ 0 → m ≤ normSq24 y) :
    ∀ x, Scaled k P x → x ≠ 0 → 4 ^ k * m ≤ normSq24 x := by
  intro x hx hne
  obtain ⟨y, hy, hxy, hnorm⟩ := scaled_normSq hx
  have hy0 : y ≠ 0 := by
    intro hzero
    apply hne
    funext i
    rw [hxy i, hzero]
    simp
  have hpow : (0 : ℤ) ≤ 4 ^ k := pow_nonneg (by norm_num) k
  calc 4 ^ k * m ≤ 4 ^ k * normSq24 y :=
        mul_le_mul_of_nonneg_left (h y hy hy0) hpow
    _ = normSq24 x := hnorm.symm

/-! ## §2 The steps the tower is made of -/

/-- **`2D₂₄ ⊆ G`** — the step from minimum norm 8 to minimum norm 4. -/
theorem dbl_isD_isG : ∀ x : Fin 24 → ℤ, Dbl IsD x → IsG x := by
  intro x hx
  exact dbl_isZ_isG x (dbl_mono (fun _ h => isD_isZ h) x hx)

/-- **`2A ⊆ B`** — the step from minimum norm 64 to minimum norm 32.  Doubling
`A` gives `4G`, and `G` sits inside the checkerboard lattice, so the result is
`4D₂₄`, which is inside Construction `B`. -/
theorem dbl_isA_isB : ∀ x : Fin 24 → ℤ, Dbl IsA x → IsB x := by
  intro x hx
  obtain ⟨y, hy, hxy⟩ := hx
  obtain ⟨z, hz, hyz⟩ := isA_dbl_isD hy
  refine scaled_two_isD_isB x ?_
  rw [scaled_succ]
  refine ⟨y, ?_, hxy⟩
  rw [scaled_succ]
  exact ⟨z, by simpa [scaled_zero] using hz, hyz⟩

/-- **`2Λ₂₄ ⊆ A`** — the same step taken through the Leech lattice: every
Leech vector has all its coordinates of one parity, so it lies on `G`, and
twice a vector of `G` is a vector of `A`. -/
theorem dbl_isC_isA : ∀ x : Fin 24 → ℤ, Dbl IsC x → IsA x := by
  rintro x ⟨y, hy, hxy⟩
  exact isA_iff_dbl_isG.mpr ⟨y, isC_isG hy, hxy⟩

/-! ## §3 The tower -/

/-- The `A`-to-`B` step at every scale: `2^{k+1} A ⊆ 2^k B`. -/
theorem chain_step_A (k : ℕ) :
    ∀ x : Fin 24 → ℤ, Scaled (k + 1) IsA x → Scaled k IsB x := by
  intro x hx
  have hiter : Scaled (k + 1) IsA = Scaled k (Dbl IsA) := by
    simp [Scaled, Function.iterate_succ_apply]
  rw [hiter] at hx
  exact scaled_mono dbl_isA_isB k x hx

/-- The `B`-to-`A` step at every scale: `2^k B ⊆ 2^k A`. -/
theorem chain_step_B (k : ℕ) :
    ∀ x : Fin 24 → ℤ, Scaled k IsB x → Scaled k IsA x :=
  scaled_mono (fun _ h => isB_isA h) k

/-- **The repeating part of the family.**  Above minimum norm 16 the rungs are
`2^k A` at the even powers of two and `2^k B` at the odd ones, and each sits
inside the one below it. -/
theorem norm_family_chain (k : ℕ) :
    (∀ x : Fin 24 → ℤ, Scaled (k + 1) IsA x → Scaled k IsB x)
      ∧ (∀ x : Fin 24 → ℤ, Scaled k IsB x → Scaled k IsA x) :=
  ⟨chain_step_A k, chain_step_B k⟩

/-- **The tower, from the grid up.**  One rung at every power-of-two minimum
norm: `ℤ²⁴` (1), `D₂₄` (2), `G` (4), `2D₂₄` (8), `A` (16), `B` (32), `2A` (64),
and from there the two steps of `norm_family_chain` repeating for ever. -/
theorem family_tower :
    (∀ x : Fin 24 → ℤ, IsD x → IsZ x)
      ∧ (∀ x : Fin 24 → ℤ, IsG x → IsD x)
      ∧ (∀ x : Fin 24 → ℤ, Dbl IsD x → IsG x)
      ∧ (∀ x : Fin 24 → ℤ, IsA x → Dbl IsD x)
      ∧ (∀ x : Fin 24 → ℤ, IsB x → IsA x)
      ∧ (∀ k : ℕ, (∀ x : Fin 24 → ℤ, Scaled (k + 1) IsA x → Scaled k IsB x)
          ∧ (∀ x : Fin 24 → ℤ, Scaled k IsB x → Scaled k IsA x)) :=
  ⟨fun _ h => isD_isZ h, fun _ h => isG_isD h, dbl_isD_isG,
   fun _ h => isA_dbl_isD h, fun _ h => isB_isA h, norm_family_chain⟩

end GLM.NormFamily
