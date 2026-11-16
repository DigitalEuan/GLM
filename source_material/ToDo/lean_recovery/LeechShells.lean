import Mathlib
import RequestProject.GLM.GolayWeightEnum

/-!
# The Leech lattice's shells, from its definition (Phase 164) — partial rebuild

*Created 19 October 2026. Partially rebuilt 15 November 2026 (Phase 190) from
`studies/LEECH_SHELLS_STUDY.md`, `reasoning/leech_shells.py` and the two held
files that import it (`LeechShellCount.lean`, `GolayDeepHole.lean`): the
original was lost in the October 2026 reorganisation and never uploaded.
**Not yet built, and not yet complete** — see
`source_material/ToDo/lean_recovery/README.md` for exactly what is owed.*

## What is here

The predicate and the norm are the API the two held files are written against,
reproduced exactly — `LeechShellCount.lean` destructures `IsLeech` into its two
parities and reads `(∑ i, x i) % 8 = 4 * m` off them, and `GolayDeepHole.lean`
builds `normSq (dbl b − dbl c) = 4 · hdist b c` on `normSq`. Both proofs below
are about those definitions and nothing else.

* `normSq x = ∑ i, (x i)^2`, in the integral (`×√8`) scaling: a vector of true
  norm `2t` has squared length `16t`;
* `IsLeech x` — Conway's construction as a disjunction of the two parities:
  every coordinate even, the coordinates `≡ 2 (mod 4)` on a Golay codeword and
  the coordinates summing to `0 (mod 8)`; or every coordinate odd, the
  coordinates `≡ 1 (mod 4)` on a codeword and the sum `4 (mod 8)`;
* `support x` — the coordinates the vector is nonzero on;
* `minimal_even_support` — a minimal vector with coordinates `0` or `±2` has
  its support on an octad: the support is a Golay codeword of eight elements;
* `minimal_odd_pattern` — an odd minimal vector has exactly one coordinate
  `±3` and every other coordinate `±1`.

## What is owed, and why it is not here

* `minimal_shape` — every minimal vector has one of the three shapes (eight
  `±2` on an octad, two `±4`, or one `±3` and the rest `±1` on a codeword).
  This is the case split over the two lemmas above plus "two coordinates of
  size `4`"; it is not a restatement of them and must be proved, not asserted.
* `shellCount_eq`, `shells_from_census` — the shell count at `t = 1` and
  `t = 2` (`196560` and `16773120`), from the procedure of §3 of the study:
  one-coordinate generating functions over (squared length, value mod 8),
  truncated powers of them per codeword weight, and the weight census. The
  procedure is the part `LeechShellCount.lean` (550 lines, held) then proves
  correct for every shell, so it must be written to agree with that file's
  `patternGF`/`patternArr` — a specification that cannot be checked here.

Both are recorded in `studies/_lean_files_needed.md` as owed. Writing them
without a build would be guessing at the elaborator, and a `sorry` would be
worse: the repository's own `lean_check` and `AxiomAuditAll` refuse one.
-/

namespace GLM.LeechShells

open Finset GLM.Golay24

/-- Squared Euclidean norm, in the integral (`×√8`) scaling: a vector of true
norm `2t` has `normSq = 16t`. -/
def normSq (x : Fin 24 → ℤ) : ℤ := ∑ i, (x i) ^ 2

/-- **Membership in the Leech lattice** (Conway's construction from the Golay
code): the two parities of the coordinates. -/
def IsLeech (x : Fin 24 → ℤ) : Prop :=
  ((∀ i, x i % 2 = 0) ∧ IsCodeword (univ.filter fun i => x i % 4 = 2) ∧
      (∑ i, x i) % 8 = 0) ∨
    ((∀ i, x i % 2 = 1) ∧ IsCodeword (univ.filter fun i => x i % 4 = 1) ∧
      (∑ i, x i) % 8 = 4)

/-- The support of a vector: the coordinates it is nonzero on. -/
def support (x : Fin 24 → ℤ) : Finset (Fin 24) := univ.filter fun i => x i ≠ 0

/-- **The even minimal vectors lie on an octad.** If every coordinate is `0` or
`±2` and the squared length is `32`, the support is a Golay codeword of eight
elements. (The sign condition — an even number of `−2` — is the mod-8 sum
condition `IsLeech` already carries.) -/
theorem minimal_even_support {x : Fin 24 → ℤ} (hx : IsLeech x) (hn : normSq x = 32)
    (hb : ∀ i, x i = -2 ∨ x i = 0 ∨ x i = 2) :
    IsCodeword (support x) ∧ (support x).card = 8 := by
  rcases hx with ⟨-, hc, -⟩ | ⟨hod, -, -⟩
  · have hsupp : support x = univ.filter fun i => x i % 4 = 2 := by
      ext i
      simp only [support, mem_filter, mem_univ, true_and]
      constructor
      · intro hi
        rcases hb i with h | h | h <;> omega
      · intro hi
        rcases hb i with h | h | h <;> omega
    refine ⟨hsupp ▸ hc, ?_⟩
    have hsum : (∑ i, (x i) ^ 2) = ∑ i ∈ support x, (4 : ℤ) := by
      rw [support, Finset.sum_filter]
      exact Finset.sum_congr rfl fun i _ => by
        rcases hb i with h | h | h <;> simp [h]
    rw [Finset.sum_const, smul_eq_mul] at hsum
    unfold normSq at hn
    rw [hn] at hsum
    have hcard : ((support x).card : ℤ) = 8 := by linarith
    exact_mod_cast hcard
  · have h1 := hod 0
    rcases hb 0 with h | h | h <;> omega

/-- **The odd minimal vectors are one `±3` and twenty-three `±1`.** -/
theorem minimal_odd_pattern {x : Fin 24 → ℤ} (hx : IsLeech x) (hn : normSq x = 32)
    (hodd : ∀ i, x i % 2 = 1) :
    (univ.filter fun i => x i = 3 ∨ x i = -3).card = 1 ∧
      ∀ i, x i = 3 ∨ x i = -3 ∨ x i = 1 ∨ x i = -1 := by
  have hle : ∀ i, (x i) ^ 2 ≤ 32 := by
    intro i
    unfold normSq at hn
    rw [← hn]
    exact Finset.single_le_sum (f := fun j => (x j) ^ 2) (fun j _ => sq_nonneg _) (mem_univ i)
  -- an odd coordinate of squared length at most 32 is `±1`, `±3` or `±5`
  have hbnd : ∀ i, -5 ≤ x i ∧ x i ≤ 5 := by
    intro i
    have h := hle i
    constructor <;> nlinarith
  have hsmall : ∀ i, x i = 1 ∨ x i = -1 ∨ x i = 3 ∨ x i = -3 := by
    intro i
    have h5 := hbnd i
    have ho := hodd i
    -- `±5` would need `25` of the `32` squared length and leave `23` coordinates
    -- with at least `1` each, which is impossible
    rcases (show x i = -5 ∨ x i = -3 ∨ x i = -1 ∨ x i = 1 ∨ x i = 3 ∨ x i = 5 by omega)
      with h | h | h | h | h | h
    · exfalso
      have : (∑ j, (x j) ^ 2) ≥ 25 + 23 := by
        have hsplit := Finset.sum_eq_add_sum_diff_singleton (s := univ) (a := i)
          (f := fun j => (x j) ^ 2) (mem_univ i)
        have hrest : 23 ≤ ∑ j ∈ univ \ {i}, (x j) ^ 2 := by
          have hcard : (univ \ {i} : Finset (Fin 24)).card = 23 := by simp
          calc (23 : ℤ) = ∑ _j ∈ univ \ {i}, (1 : ℤ) := by
                rw [Finset.sum_const, hcard]; norm_num
            _ ≤ ∑ j ∈ univ \ {i}, (x j) ^ 2 := by
                refine Finset.sum_le_sum fun j _ => ?_
                have := hodd j
                have : (1 : ℤ) ≤ (x j) ^ 2 := by
                  rcases (show x j = 1 ∨ x j = -1 ∨ x j = 3 ∨ x j = -3 ∨ x j = 5 ∨ x j = -5 by
                    have := hbnd j; omega) with h' | h' | h' | h' | h' | h' <;>
                    rw [h'] <;> norm_num
                exact this
        rw [hsplit, h]
        norm_num
        linarith
      unfold normSq at hn
      omega
    · tauto
    · tauto
    · tauto
    · tauto
    · exfalso
      have : (∑ j, (x j) ^ 2) ≥ 25 + 23 := by
        have hsplit := Finset.sum_eq_add_sum_diff_singleton (s := univ) (a := i)
          (f := fun j => (x j) ^ 2) (mem_univ i)
        have hrest : 23 ≤ ∑ j ∈ univ \ {i}, (x j) ^ 2 := by
          have hcard : (univ \ {i} : Finset (Fin 24)).card = 23 := by simp
          calc (23 : ℤ) = ∑ _j ∈ univ \ {i}, (1 : ℤ) := by
                rw [Finset.sum_const, hcard]; norm_num
            _ ≤ ∑ j ∈ univ \ {i}, (x j) ^ 2 := by
                refine Finset.sum_le_sum fun j _ => ?_
                have : (1 : ℤ) ≤ (x j) ^ 2 := by
                  rcases (show x j = 1 ∨ x j = -1 ∨ x j = 3 ∨ x j = -3 ∨ x j = 5 ∨ x j = -5 by
                    have := hbnd j; omega) with h' | h' | h' | h' | h' | h' <;>
                    rw [h'] <;> norm_num
                exact this
        rw [hsplit, h]
        norm_num
        linarith
      unfold normSq at hn
      omega
  -- each square is `1` or `9`, and they sum to `32 = 24 + 8`
  have hsq : ∀ i, (x i) ^ 2 = if x i = 3 ∨ x i = -3 then (9 : ℤ) else 1 := by
    intro i
    rcases hsmall i with h | h | h | h <;> simp [h]
  have hcount : (∑ i, (x i) ^ 2) =
      24 + 8 * ((univ.filter fun i => x i = 3 ∨ x i = -3).card : ℤ) := by
    have hcompl : (univ.filter fun i => ¬ (x i = 3 ∨ x i = -3)).card +
        (univ.filter fun i => x i = 3 ∨ x i = -3).card = 24 := by
      rw [Finset.card_filter, Finset.card_filter, ← Finset.sum_add_distrib]
      simp
    have hcompl' : ((univ.filter fun i => ¬ (x i = 3 ∨ x i = -3)).card : ℤ) =
        24 - ((univ.filter fun i => x i = 3 ∨ x i = -3).card : ℤ) := by
      have := hcompl
      omega
    calc (∑ i, (x i) ^ 2)
        = ∑ i, (if x i = 3 ∨ x i = -3 then (9 : ℤ) else 1) :=
          Finset.sum_congr rfl fun i _ => hsq i
      _ = (∑ i ∈ univ.filter fun i => x i = 3 ∨ x i = -3, (9 : ℤ)) +
            ∑ i ∈ univ.filter fun i => ¬ (x i = 3 ∨ x i = -3), (1 : ℤ) := by
          rw [Finset.sum_ite, Finset.sum_filter]
          simp only [Finset.sum_ite, Finset.sum_filter, Finset.mem_univ, if_true]
          ring
      _ = 9 * ((univ.filter fun i => x i = 3 ∨ x i = -3).card : ℤ) +
            (24 - ((univ.filter fun i => x i = 3 ∨ x i = -3).card : ℤ)) := by
          rw [Finset.sum_const, Finset.sum_const, hcompl', smul_eq_mul, smul_eq_mul]
          ring
      _ = 24 + 8 * ((univ.filter fun i => x i = 3 ∨ x i = -3).card : ℤ) := by ring
  constructor
  · unfold normSq at hn
    rw [hcount] at hn
    have : ((univ.filter fun i => x i = 3 ∨ x i = -3).card : ℤ) = 1 := by linarith
    exact_mod_cast this
  · intro i
    exact hsmall i

end GLM.LeechShells
