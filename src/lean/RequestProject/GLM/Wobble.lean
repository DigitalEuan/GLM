/-
# The wobble as the computation: a trajectory through the ambiguity is a
# faithful record of what was read

Concept 3 of the brief asks whether the *long-term frequency distribution* of a
wiggling carrier can be made to do geometric work that a static algorithm would
otherwise do by search.  This file answers it in the one place where the
geometry is completely pinned down: the six-fold tie at the Golay covering
radius.

Let the carrier, instead of snapping to one of the six equidistant codewords,
visit all six in a cycle — the deterministic "wiggle" through the weight-4
decision space.  Then:

* `sextet_cycle_avgVec` — its reading at every completed cycle is exactly the
  rational bundle of the tie, `(1 + 4·v)/6` coordinatewise;
* `sextet_cycle_determines` — and that reading determines the received word
  uniquely.

So the trajectory distribution is not a lossy summary of the ambiguity: it is a
complete encoding of the input, computed by the motion itself.  A snap, by
`single_candidate_card`, leaves 10,626 possibilities open; the wiggle leaves
one.
-/
import RequestProject.GLM.Superposition
import RequestProject.GLM.HullExpansion

namespace GLM.Golay24

open Finset Filter Topology
open GLM.Info GLM.Hull

/-- The real-valued bundle of the tie: the mean of the six candidates. -/
noncomputable def bundleR (v : Word) : Fin 24 → ℝ :=
  fun i => (∑ c ∈ candidates v, indR c i) / 6

theorem indR_eq_cast_indQ (c : Word) (i : Fin 24) : indR c i = ((indQ c i : ℚ) : ℝ) := by
  by_cases h : i ∈ c <;> simp [indR, indQ, h]

theorem bundleR_eq_cast (v : Word) (i : Fin 24) : bundleR v i = ((bundleQ v i : ℚ) : ℝ) := by
  unfold bundleR bundleQ
  push_cast
  rw [Finset.sum_congr rfl (fun c _ => indR_eq_cast_indQ c i)]

/-- The bundle, in real coordinates: `(1 + 4·vᵢ)/6`. -/
theorem bundleR_eq {v : Word} (h : CosetHasTetrad v) (i : Fin 24) :
    bundleR v i = (1 + 4 * indR v i) / 6 := by
  rw [bundleR_eq_cast, bundleQ_eq h, indR_eq_cast_indQ]
  push_cast
  ring

/-- **A cycle through the tie reads back the bundle.**  If the carrier visits
each of the six equidistant codewords once per cycle, its reading at every
completed cycle is exactly the rational bundle of the tie. -/
theorem sextet_cycle_avgVec {v : Word} (h : CosetHasTetrad v)
    (y : Fin 6 → Word) (hinj : Function.Injective y) (hmem : ∀ j, y j ∈ candidates v)
    {k : ℕ} (hk : 0 < k) :
    avgVec (fun m => indR (y ⟨m % 6, Nat.mod_lt _ (by norm_num)⟩)) (6 * k) = bundleR v := by
  have himg : Finset.image y univ = candidates v := by
    refine Finset.eq_of_subset_of_card_le ?_ ?_
    · intro c hc
      obtain ⟨j, _, rfl⟩ := Finset.mem_image.1 hc
      exact hmem j
    · rw [Finset.card_image_of_injective _ hinj, candidates_card h]
      simp
  rw [cycle_avgVec_eq (by norm_num) (fun j => indR (y j)) hk]
  funext i
  unfold bundleR
  congr 1
  rw [← himg, Finset.sum_image (fun a _ b _ hab => hinj hab)]

/-- **The wiggle is faithful.**  Two words at the covering radius whose sextet
cycles read the same are equal: the trajectory's distribution over the six
candidates determines the received word. -/
theorem sextet_cycle_determines {v v' : Word} (h : CosetHasTetrad v) (h' : CosetHasTetrad v')
    (heq : bundleR v = bundleR v') : v = v' := by
  refine bundleQ_injective h h' ?_
  funext i
  have := congrFun heq i
  rw [bundleR_eq_cast, bundleR_eq_cast] at this
  exact_mod_cast this

/-- The reading also converges, along the cycles, to the bundle. -/
theorem sextet_cycle_tendsto {v : Word} (h : CosetHasTetrad v)
    (y : Fin 6 → Word) (hinj : Function.Injective y) (hmem : ∀ j, y j ∈ candidates v) :
    Tendsto (fun k => avgVec (fun m => indR (y ⟨m % 6, Nat.mod_lt _ (by norm_num)⟩)) (6 * k))
      atTop (𝓝 (bundleR v)) := by
  rw [tendsto_congr' ?_]
  · exact tendsto_const_nhds
  · filter_upwards [eventually_gt_atTop 0] with k hk
    exact sextet_cycle_avgVec h y hinj hmem hk

end GLM.Golay24
