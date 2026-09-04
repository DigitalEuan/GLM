/-
# A coordinate permutation is an isometry, so it may be wrapped around a decoder

The project keeps two coordinate frames for the same `[24, 12, 8]` code: a
legacy one and the canonical one.  The bridge between them is a *permutation of
coordinates*, and the package treats that as the only sanctioned map — a general
linear isomorphism between the two codes also exists, but it scrambles Hamming
distance and therefore cannot be composed with a nearest-codeword decoder.

This file proves the property that makes the distinction:

* `hdist_permute` — a coordinate permutation preserves Hamming distance;
* `weight_permute` — hence Hamming weight;
* `nearest_permute` — hence nearest-codeword decoding commutes with it: if `c`
  is a nearest codeword of `v` in a code `C`, then `σ • c` is a nearest codeword
  of `σ • v` in the permuted code `σ • C`;
* `decoding_commutes` — the same statement read backwards: decoding a legacy
  word by permuting it into the canonical frame, decoding there and permuting
  the answer back is *exactly* nearest-codeword decoding in the legacy frame.

Nothing here is special to 24 coordinates or to the Golay code.
-/
import Mathlib
import RequestProject.GLM.GolayBoundary

namespace GLM.Golay

open Finset

variable {n : ℕ}

/-- Relabel the coordinates of a bit pattern by a permutation. -/
def permute (σ : Equiv.Perm (Fin n)) (v : Fin n → Bool) : Fin n → Bool :=
  fun i => v (σ i)

/-- The image of a code under a coordinate permutation. -/
def permuteSet (σ : Equiv.Perm (Fin n)) (C : Set (Fin n → Bool)) :
    Set (Fin n → Bool) := (permute σ) '' C

@[simp] theorem permute_apply (σ : Equiv.Perm (Fin n)) (v : Fin n → Bool)
    (i : Fin n) : permute σ v i = v (σ i) := rfl

/-- Permuting by `σ` and then by `σ⁻¹` is the identity. -/
@[simp] theorem permute_symm_permute (σ : Equiv.Perm (Fin n))
    (v : Fin n → Bool) : permute σ.symm (permute σ v) = v := by
  funext i; simp

@[simp] theorem permute_permute_symm (σ : Equiv.Perm (Fin n))
    (v : Fin n → Bool) : permute σ (permute σ.symm v) = v := by
  funext i; simp

/-! ## The isometry -/

theorem diffSet_permute (σ : Equiv.Perm (Fin n)) (a b : Fin n → Bool) :
    diffSet (permute σ a) (permute σ b)
      = (diffSet a b).image σ.symm := by
  ext i
  simp only [diffSet, permute_apply, Finset.mem_filter, Finset.mem_univ,
    true_and, Finset.mem_image]
  constructor
  · intro h
    exact ⟨σ i, by simpa [diffSet] using h, by simp⟩
  · rintro ⟨j, hj, rfl⟩
    simpa [diffSet] using hj

/-- **A coordinate permutation preserves Hamming distance.** -/
theorem hdist_permute (σ : Equiv.Perm (Fin n)) (a b : Fin n → Bool) :
    hdist (permute σ a) (permute σ b) = hdist a b := by
  unfold hdist
  rw [diffSet_permute, Finset.card_image_of_injective _ σ.symm.injective]

/-- **Hence it preserves Hamming weight**, the distance to the zero pattern. -/
theorem weight_permute (σ : Equiv.Perm (Fin n)) (v : Fin n → Bool) :
    hdist (permute σ v) (permute σ (fun _ => false))
      = hdist v (fun _ => false) :=
  hdist_permute σ v _

/-! ## Nearest-codeword decoding commutes with it -/

/-- `c` is a nearest codeword of `v` in `C`. -/
def IsNearest (C : Set (Fin n → Bool)) (v c : Fin n → Bool) : Prop :=
  c ∈ C ∧ ∀ d ∈ C, hdist v c ≤ hdist v d

/-- **Decoding commutes with a coordinate permutation.**  This is the property a
general linear isomorphism of the two codes does *not* have, and the reason the
package migrates by permutation only. -/
theorem nearest_permute (σ : Equiv.Perm (Fin n)) {C : Set (Fin n → Bool)}
    {v c : Fin n → Bool} (h : IsNearest C v c) :
    IsNearest (permuteSet σ C) (permute σ v) (permute σ c) := by
  refine ⟨⟨c, h.1, rfl⟩, ?_⟩
  rintro d ⟨e, he, rfl⟩
  rw [hdist_permute, hdist_permute]
  exact h.2 e he

/-- The converse: a nearest codeword found in the permuted frame comes back to a
nearest codeword in the original one.  Together with `nearest_permute` this says
that routing a legacy word through the canonical frame is not an approximation
of legacy decoding — it *is* legacy decoding. -/
theorem decoding_commutes (σ : Equiv.Perm (Fin n)) {C : Set (Fin n → Bool)}
    {v c : Fin n → Bool}
    (h : IsNearest (permuteSet σ C) (permute σ v) (permute σ c)) :
    IsNearest C v c := by
  obtain ⟨⟨e, he, hec⟩, hmin⟩ := h
  have hc : c ∈ C := by
    have : e = c := by
      have := congrArg (permute σ.symm) hec
      simpa using this
    exact this ▸ he
  refine ⟨hc, fun d hd => ?_⟩
  have := hmin (permute σ d) ⟨d, hd, rfl⟩
  rwa [hdist_permute, hdist_permute] at this

/-- The two readings agree, so nearest-codeword decoding in the legacy frame and
in the canonical frame are the same operation. -/
theorem nearest_permute_iff (σ : Equiv.Perm (Fin n)) {C : Set (Fin n → Bool)}
    {v c : Fin n → Bool} :
    IsNearest C v c ↔
      IsNearest (permuteSet σ C) (permute σ v) (permute σ c) :=
  ⟨nearest_permute σ, decoding_commutes σ⟩

/-- A permutation of the coordinates carries a minimum-distance-`8` code to a
minimum-distance-`8` code, so every bound proved in `GolayBoundary` transports
across the migration. -/
theorem min_distance_permute (σ : Equiv.Perm (Fin n))
    {C : Set (Fin n → Bool)}
    (hmin : ∀ c ∈ C, ∀ c' ∈ C, c ≠ c' → 8 ≤ hdist c c') :
    ∀ c ∈ permuteSet σ C, ∀ c' ∈ permuteSet σ C, c ≠ c' → 8 ≤ hdist c c' := by
  rintro _ ⟨a, ha, rfl⟩ _ ⟨b, hb, rfl⟩ hne
  rw [hdist_permute]
  refine hmin a ha b hb ?_
  rintro rfl
  exact hne rfl

end GLM.Golay
