module

public import RequestProject.GLM.Rule30.LeftWhiteLift

/-!
# Round 13: the lifted statement is the same as a run bound (compactness)

`leftWhiteAperiodic_of_runBound` shows that a run bound implies the lifted statement
`LeftWhiteAperiodic p`.  Here is the converse:

* `runBound_of_leftWhiteAperiodic` — if no column of any left-white row is eventually
  `p`-periodic, then there is a run bound `B` for period `p`.
* `leftWhiteAperiodic_iff_runBound` — the two are equivalent.

So, in the language of the propose-and-check loop (`refutation_horizon_of_runBound`): the lifted
statement holds for period `p` exactly when **every** proposal "period `p` from time `N`" is
refuted within a horizon that depends only on `N`.

The proof is a compactness argument (König's lemma): if a column at distance `d` could stay
`p`-periodic for arbitrarily long, a limit of the witnessing rows would be a left-white row whose
column stays `p`-periodic for ever.
-/

@[expose] public section

namespace GLM.Rule30

open Filter Topology

/-- The left-white row with edge `0` whose cells right of the edge are given by `y`. -/
def rowOf (y : ℕ → Bool) : Config := fun j => if j < 0 then false else y j.toNat

theorem rowOf_white (y : ℕ → Bool) : ∀ j, j < 0 → rowOf y j = false := by
  intro j hj; simp [rowOf, hj]

/-- The column at distance `d` up to time `L` only depends on the first `d + L + 1` cells. -/
theorem evolve_rowOf_congr (y z : ℕ → Bool) (d L : ℕ) (h : ∀ k ≤ d + L, y k = z k) (t : ℕ)
    (ht : t ≤ L) : evolve (rowOf y) t d = evolve (rowOf z) t d := by
  apply evolve_congr
  intro j _ h2
  unfold rowOf
  split_ifs with hj
  · rfl
  · exact h _ (by omega)

/-- **Compactness:** if no left-white row has an eventually `p`-periodic column, then a column at
distance `d` from the edge can only be `p`-periodic on boundedly long windows. -/
theorem exists_run_limit {p : ℕ} (h : LeftWhiteAperiodic p) (d : ℕ) :
    ∃ L0 : ℕ, ∀ (x : Config) (ℓ : ℤ), (∀ j, j < ℓ → x j = false) → x ℓ = true →
      ¬ ∀ t, t + p ≤ L0 → evolve x (t + p) (ℓ + d) = evolve x t (ℓ + d) := by
  by_contra hne
  push_neg at hne
  choose x ℓ hw hb hrun using hne
  -- normalise every witness to edge `0`
  set y : ℕ → ℕ → Bool := fun L k => x L (ℓ L + k) with hy
  have hshift : ∀ L t, evolve (rowOf (y L)) t d = evolve (x L) t (ℓ L + d) := by
    intro L t
    have : rowOf (y L) = fun j => x L (j + ℓ L) := by
      funext j
      unfold rowOf
      split_ifs with hj
      · exact (hw L _ (by omega)).symm
      · simp only [hy]; congr 1; omega
    rw [this, evolve_shift, add_comm]
  -- a convergent subsequence
  obtain ⟨z, -, φ, hφ, hlim⟩ :=
    (isCompact_univ (X := ℕ → Bool)).tendsto_subseq (x := fun n => y n) (fun _ => trivial)
  have hev : ∀ K : ℕ, ∀ᶠ n in atTop, ∀ k ≤ K, y (φ n) k = z k := by
    intro K
    have hcoord : ∀ k, ∀ᶠ n in atTop, y (φ n) k = z k := by
      intro k
      have := (continuous_apply k).continuousAt.tendsto.comp hlim
      rw [nhds_discrete, tendsto_pure] at this
      exact this
    have := (Filter.eventually_all_finset (Finset.range (K + 1))).mpr fun k _ => hcoord k
    exact this.mono fun n hn k hk => hn k (Finset.mem_range.mpr (by omega))
  -- the limit row has a column that is `p`-periodic for ever
  apply h (rowOf z) ⟨0, rowOf_white z, ?_⟩ d 0
  · intro t _
    obtain ⟨n, hn⟩ := ((hev (d + t + p)).and (eventually_ge_atTop (t + p))).exists
    have hφn : t + p ≤ φ n := le_trans hn.2 (hφ.id_le n)
    have e1 := evolve_rowOf_congr z (y (φ n)) d (t + p) (fun k hk => (hn.1 k (by omega)).symm)
      (t + p) le_rfl
    have e2 := evolve_rowOf_congr z (y (φ n)) d (t + p) (fun k hk => (hn.1 k (by omega)).symm)
      t (by omega)
    rw [e1, e2, hshift, hshift]
    exact hrun (φ n) t hφn
  · obtain ⟨n, hn⟩ := (hev 0).exists
    have := hn 0 le_rfl
    simp only [hy] at this
    simpa [rowOf, ← this] using hb (φ n)

/-- **The lifted statement gives a run bound.** -/
theorem runBound_of_leftWhiteAperiodic {p : ℕ} (h : LeftWhiteAperiodic p) :
    ∃ B : ℕ → ℕ, RunBound p B := by
  choose L0 hL0 using exists_run_limit h
  refine ⟨L0, fun x ℓ hw hb d L hrun => ?_⟩
  by_contra hL
  exact hL0 d x ℓ hw hb fun t ht => hrun t (by omega)

/-- **Equivalence:** the lifted statement for period `p` holds if and only if period `p` has a run
bound, i.e. iff the propose-and-check loop has a horizon for every proposal of period `p`. -/
theorem leftWhiteAperiodic_iff_runBound (p : ℕ) :
    LeftWhiteAperiodic p ↔ ∃ B : ℕ → ℕ, RunBound p B :=
  ⟨runBound_of_leftWhiteAperiodic, fun ⟨_, hB⟩ => leftWhiteAperiodic_of_runBound hB⟩

/-- The lifted statement for every period. -/
def LeftWhiteAperiodicAll : Prop := ∀ p, 0 < p → LeftWhiteAperiodic p

/-- A run bound for every period. -/
def RunBoundsAll : Prop := ∀ p, 0 < p → ∃ B : ℕ → ℕ, RunBound p B

theorem leftWhiteAperiodicAll_iff_runBoundsAll : LeftWhiteAperiodicAll ↔ RunBoundsAll :=
  forall_congr' fun p => imp_congr_right fun _ => leftWhiteAperiodic_iff_runBound p

/-- **The lift implies Problem 1** (packaged form of `problem1_of_leftWhiteAperiodic`). -/
theorem problem1_of_leftWhiteAperiodicAll (h : LeftWhiteAperiodicAll) : Problem1 :=
  problem1_of_leftWhiteAperiodic h

/-- **Run bounds for every period imply Problem 1.** -/
theorem problem1_of_runBoundsAll (h : RunBoundsAll) : Problem1 :=
  problem1_of_leftWhiteAperiodic (leftWhiteAperiodicAll_iff_runBoundsAll.mpr h)

end GLM.Rule30
