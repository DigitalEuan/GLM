module

public import RequestProject.GLM.Rule30.PowerSeriesLadder

/-!
# Round 24: Kronecker's converse — the Hankel form of Problem 1 is exact

Round 23 proved one direction of the Hankel form of Problem 1: infinitely many non-zero Hankel
determinants `det (hankel centerCol N)` (over `GF(2)`) imply `Problem1`
(`problem1_of_hankel_infinitely_often`).  The converse was left open (To Do item 11).  It is
proved here, for every Boolean sequence.

* **`eventuallyPeriodic_of_hankel_det_eventually_zero`** : if `det H_r ≠ 0` and `det H_N = 0` for
  every `N > r`, then `a` obeys a linear recurrence of order `r` for ever, hence is eventually
  periodic.
* **`hankel_infinitely_often_iff`** : `a` is not eventually periodic iff `det H_N ≠ 0` for
  infinitely many `N`.
* **`problem1IffHankelInfinitelyOften`** : the Round 23 statement `Problem1IffHankelInfinitelyOften`
  is now a theorem.  So Problem 1 has (at least) four proved equivalent forms: unbounded linear
  complexity, block complexity `≥ n + 1`, escape from all finite-state predictors, and infinitely
  many non-singular Hankel matrices.

## The argument

Let `r` be such that `H_r` is invertible.  Solve `H_r c = (a(r), …, a(2r-1))` and let
`e(n) = a(n + r) + ∑_{j<r} c_j a(n + j)` be the error of the recurrence; `e(n) = 0` for `n < r`.
If `e` is not identically zero, let `s` be its first non-zero index.  Multiply `H_{s+1}` on the
right by the unitriangular matrix `U` that turns column `r + t` into `col (r + t) + ∑ c_j col (t + j)`:
the columns `r + t` of `H_{s+1} U` are `(e(i + t))_i`.  A kernel vector `w` of `H_{s+1} U` then
vanishes on its first `r` entries (rows `i < r` see only `H_r`, because `e(i + t) = 0` there) and
on the remaining entries (row `s - t` sees `e(s) = 1` exactly once, from the top down).  So
`det H_{s+1} ≠ 0` with `s + 1 > r`.
-/

@[expose] public section

namespace GLM.Rule30

open Finset

/-- The error of the recurrence of order `r` with coefficients `c` at time `n`, over `GF(2)`. -/
def recErr (a : ℕ → Bool) (r : ℕ) (c : ℕ → ZMod 2) (n : ℕ) : ZMod 2 :=
  b2 (a (n + r)) + ∑ j ∈ range r, c j * b2 (a (n + j))

/-- A non-singular Hankel matrix has trivial kernel, in `ℕ`-indexed form. -/
theorem hankel_kernel_trivial {a : ℕ → Bool} {r : ℕ} (hr : (hankel a r).det ≠ 0)
    {W : ℕ → ZMod 2} (hW : ∀ i < r, ∑ j ∈ range r, b2 (a (i + j)) * W j = 0) :
    ∀ j < r, W j = 0 := by
  have hv : (hankel a r).mulVec (fun j : Fin r => W j) = 0 := by
    funext i
    simp only [Matrix.mulVec, dotProduct, hankel, Pi.zero_apply]
    rw [Fin.sum_univ_eq_sum_range (fun j => b2 (a (i + j)) * W j) r]
    exact hW i i.2
  have := Matrix.eq_zero_of_mulVec_eq_zero hr hv
  intro j hj
  simpa using congrFun this ⟨j, hj⟩

/-- A non-singular Hankel matrix solves the next-term system. -/
theorem hankel_solve {a : ℕ → Bool} {r : ℕ} (hr : (hankel a r).det ≠ 0) :
    ∃ c : ℕ → ZMod 2, ∀ i < r, recErr a r c i = 0 := by
  set H := hankel a r
  let y : Fin r → ZMod 2 := fun i => b2 (a (i + r))
  let cv := H⁻¹.mulVec y
  have hcv : H.mulVec cv = y := by
    simp only [cv, Matrix.mulVec_mulVec]
    rw [Matrix.mul_nonsing_inv _ (Ne.isUnit hr), Matrix.one_mulVec]
  refine ⟨fun j => if h : j < r then cv ⟨j, h⟩ else 0, fun i hi => ?_⟩
  have hi' := congrFun hcv ⟨i, hi⟩
  simp only [Matrix.mulVec, dotProduct, H, hankel, y] at hi'
  have h2 : ∑ j ∈ range r, (if h : j < r then cv ⟨j, h⟩ else 0) * b2 (a (i + j)) =
      b2 (a (i + r)) := by
    rw [← Fin.sum_univ_eq_sum_range (fun j => (if h : j < r then cv ⟨j, h⟩ else 0) *
      b2 (a (i + j))) r, ← hi']
    refine Finset.sum_congr rfl fun j _ => ?_
    simp [mul_comm]
  unfold recErr
  rw [h2]
  generalize b2 (a (i + r)) = z
  revert z; decide

/-- The unitriangular column operation `col (r + t) ↦ col (r + t) + ∑_{l<r} c_l col (t + l)`. -/
def recU (r N : ℕ) (c : ℕ → ZMod 2) : Matrix (Fin N) (Fin N) (ZMod 2) := fun k j =>
  if k = j then 1
  else if r ≤ (j : ℕ) ∧ (j : ℕ) - r ≤ k ∧ (k : ℕ) < j then c (k - (j - r)) else 0

theorem det_recU (r N : ℕ) (c : ℕ → ZMod 2) : (recU r N c).det = 1 := by
  rw [Matrix.det_of_upperTriangular]
  · simp [recU]
  · intro i j hij
    have h1 : i ≠ j := fun h => by subst h; exact lt_irrefl _ hij
    have h2 : ¬ ((i : ℕ) < j) := by
      have := Fin.lt_def.mp hij; simp only [id] at this; omega
    simp [recU, h1, h2]

theorem hankel_mul_recU_apply (a : ℕ → Bool) (r N : ℕ) (c : ℕ → ZMod 2) (i j : Fin N) :
    (hankel a N * recU r N c) i j =
      if (j : ℕ) < r then b2 (a (i + j)) else recErr a r c (i + j - r) := by
  rw [Matrix.mul_apply]
  simp only [hankel, recU]
  set g : ℕ → ZMod 2 := fun k => b2 (a (i + k)) * (if k = (j : ℕ) then 1
    else if r ≤ (j : ℕ) ∧ (j : ℕ) - r ≤ k ∧ k < j then c (k - (j - r)) else 0) with hg
  rw [show (∑ x : Fin N, b2 (a (i + x)) * (if x = j then 1
      else if r ≤ (j : ℕ) ∧ (j : ℕ) - r ≤ x ∧ (x : ℕ) < j then c (x - (j - r)) else 0)) =
      ∑ k ∈ range N, g k by
    rw [← Fin.sum_univ_eq_sum_range]
    refine Finset.sum_congr rfl fun x _ => ?_
    simp [hg, Fin.ext_iff]]
  set J : ℕ := (j : ℕ) with hJdef
  have hJ : J < N := j.2
  have hsplit : ∀ k, g k = (if k = J then b2 (a (i + k)) else 0) +
      (if r ≤ J ∧ J - r ≤ k ∧ k < J then b2 (a (i + k)) * c (k - (J - r)) else 0) := by
    intro k
    simp only [hg]
    by_cases h1 : k = J
    · subst h1; simp
    · simp [h1, mul_ite]
  rw [Finset.sum_congr rfl (fun k _ => hsplit k), Finset.sum_add_distrib,
    Finset.sum_ite_eq' (range N) J, if_pos (Finset.mem_range.2 hJ)]
  split_ifs with hJr
  · rw [Finset.sum_eq_zero (fun k _ => if_neg (by omega))]; ring
  · have hfil : (range N).filter (fun k => r ≤ J ∧ J - r ≤ k ∧ k < J) = Ico (J - r) J := by
      ext k
      simp only [Finset.mem_filter, Finset.mem_range, Finset.mem_Ico]
      omega
    rw [← Finset.sum_filter, hfil, Finset.sum_Ico_eq_sum_range, show J - (J - r) = r by omega]
    unfold recErr
    rw [show (i : ℕ) + J - r + r = i + J by omega]
    congr 1
    refine Finset.sum_congr rfl fun l _ => ?_
    rw [show J - r + l - (J - r) = l by omega, show (i : ℕ) + (J - r + l) = i + J - r + l by omega]
    ring

/-- The key step: if the recurrence fitted to `H_r` first fails at `s`, then `det H_{s+1} ≠ 0`. -/
theorem hankel_det_ne_zero_at_first_error {a : ℕ → Bool} {r s : ℕ} {c : ℕ → ZMod 2}
    (hr : (hankel a r).det ≠ 0) (hrs : r ≤ s) (hs : recErr a r c s ≠ 0)
    (hbelow : ∀ n < s, recErr a r c n = 0) : (hankel a (s + 1)).det ≠ 0 := by
  set N := s + 1 with hN
  have hdet : (hankel a N).det = (hankel a N * recU r N c).det := by
    rw [Matrix.det_mul, det_recU, mul_one]
  rw [hdet]
  intro h0
  obtain ⟨v, hv0, hv⟩ := Matrix.exists_mulVec_eq_zero_iff.mpr h0
  let W : ℕ → ZMod 2 := fun n => if h : n < N then v ⟨n, h⟩ else 0
  -- the row equations in `ℕ`-indexed form
  have hrow : ∀ i < N, ∑ j ∈ range r, b2 (a (i + j)) * W j +
      ∑ t ∈ range (N - r), recErr a r c (i + t) * W (r + t) = 0 := by
    intro i hi
    have := congrFun hv ⟨i, hi⟩
    simp only [Matrix.mulVec, dotProduct, hankel_mul_recU_apply, Pi.zero_apply] at this
    rw [← this]
    have e1 : (∑ x : Fin N, (if (x : ℕ) < r then b2 (a (i + x)) else recErr a r c (i + x - r)) *
        v x) = ∑ j ∈ range N, (if j < r then b2 (a (i + j)) else recErr a r c (i + j - r)) *
        W j := by
      rw [← Fin.sum_univ_eq_sum_range]
      refine Finset.sum_congr rfl fun x _ => ?_
      simp [W]
    have e2 : ∀ F : ℕ → ZMod 2, ∑ j ∈ range N, F j =
        ∑ j ∈ range r, F j + ∑ t ∈ range (N - r), F (r + t) := fun F => by
      rw [← Finset.sum_range_add, Nat.add_sub_cancel' (by omega)]
    rw [e1, e2]
    congr 1
    · refine Finset.sum_congr rfl fun j hj => ?_
      simp only [Finset.mem_range] at hj
      simp [hj]
    · refine Finset.sum_congr rfl fun t _ => ?_
      rw [if_neg (by omega), show (i : ℕ) + (r + t) - r = i + t by omega]
  -- the first `r` entries vanish
  have hlow : ∀ j < r, W j = 0 := by
    refine hankel_kernel_trivial hr fun i hi => ?_
    have h := hrow i (by omega)
    rw [Finset.sum_eq_zero (s := range (N - r)) (f := fun t => recErr a r c (i + t) * W (r + t))
      (fun t ht => by
        simp only [Finset.mem_range] at ht
        show recErr a r c (i + t) * W (r + t) = 0
        rw [hbelow (i + t) (by omega), zero_mul]), add_zero] at h
    exact h
  -- the remaining entries vanish, from the top down
  have hhigh : ∀ m t, t + m = N - r - 1 → W (r + t) = 0 := by
    intro m
    induction m using Nat.strong_induction_on with
    | _ m ih =>
      intro t ht
      have h := hrow (s - t) (by omega)
      rw [Finset.sum_eq_zero (s := range r) (f := fun j => b2 (a (s - t + j)) * W j)
        (fun j hj => by
          simp only [Finset.mem_range] at hj
          show b2 (a (s - t + j)) * W j = 0
          rw [hlow j hj, mul_zero]), zero_add,
        Finset.sum_eq_single t] at h
      · rw [show s - t + t = s by omega] at h
        exact (mul_eq_zero.mp h).resolve_left hs
      · intro t' ht' hne
        simp only [Finset.mem_range] at ht'
        rcases Nat.lt_or_gt_of_ne hne with hlt | hgt
        · rw [hbelow _ (by omega), zero_mul]
        · rw [ih (N - r - 1 - t') (by omega) t' (by omega), mul_zero]
      · intro h'; simp only [Finset.mem_range] at h'; omega
  apply hv0
  funext x
  have hx : W x = 0 := by
    rcases Nat.lt_or_ge (x : ℕ) r with h | h
    · exact hlow x h
    · have := hhigh (N - r - 1 - (x - r)) (x - r) (by omega)
      rwa [show r + (x - r) = x by omega] at this
  simpa [W] using hx

/-- A recurrence that never fails forces eventual periodicity. -/
theorem eventuallyPeriodic_of_recErr_zero {a : ℕ → Bool} {r : ℕ} {c : ℕ → ZMod 2}
    (h : ∀ n, recErr a r c n = 0) : EventuallyPeriodic a := by
  have hb : ∀ (z : ZMod 2) (x : Bool), b2 (decide (z = 1) && x) = z * b2 x := by
    intro z x; fin_cases z <;> cases x <;> rfl
  apply eventuallyPeriodic_of_fits_all (L := r) (c := fun i => decide (c (r - 1 - i) = 1))
  intro m n hn _
  have h := h (n - r)
  unfold recErr at h
  rw [show n - r + r = n by omega] at h
  unfold recVal
  simp only [hb]
  rw [← Finset.sum_range_reflect (fun i => c (r - 1 - i) * b2 (a (n - 1 - i))) r]
  have : ∑ j ∈ range r, c (r - 1 - (r - 1 - j)) * b2 (a (n - 1 - (r - 1 - j))) =
      ∑ j ∈ range r, c j * b2 (a (n - r + j)) :=
    Finset.sum_congr rfl fun j hj => by
      simp only [Finset.mem_range] at hj
      rw [show r - 1 - (r - 1 - j) = j by omega, show n - 1 - (r - 1 - j) = n - r + j by omega]
  rw [this]
  generalize b2 (a n) = x at h ⊢
  generalize ∑ j ∈ range r, c j * b2 (a (n - r + j)) = S at h ⊢
  revert x S; decide

/-- **Kronecker's converse.** If `det H_r ≠ 0` and every larger Hankel determinant vanishes,
then `a` is eventually periodic. -/
theorem eventuallyPeriodic_of_hankel_det_eventually_zero {a : ℕ → Bool} {r : ℕ}
    (hr : (hankel a r).det ≠ 0) (hzero : ∀ N > r, (hankel a N).det = 0) :
    EventuallyPeriodic a := by
  obtain ⟨c, hc⟩ := hankel_solve hr
  by_cases hall : ∀ n, recErr a r c n = 0
  · exact eventuallyPeriodic_of_recErr_zero hall
  · push_neg at hall
    let s := Nat.find hall
    have hs : recErr a r c s ≠ 0 := Nat.find_spec hall
    have hbelow : ∀ n < s, recErr a r c n = 0 := fun n hn => by
      have := Nat.find_min hall hn
      simpa using this
    have hrs : r ≤ s := by
      by_contra h
      exact hs (hc s (by omega))
    exact (hankel_det_ne_zero_at_first_error hr hrs hs hbelow (hzero (s + 1) (by omega))).elim

/-- **The Hankel form of eventual periodicity.** A Boolean sequence is not eventually periodic
iff infinitely many of its Hankel determinants over `GF(2)` are non-zero. -/
theorem hankel_infinitely_often_iff (a : ℕ → Bool) :
    (∀ N, ∃ M ≥ N, (hankel a M).det ≠ 0) ↔ ¬ EventuallyPeriodic a := by
  constructor
  · rintro h ⟨p, hp, τ, hper⟩
    obtain ⟨M, hM, hdet⟩ := h (τ + p + 1)
    exact hdet (hankel_det_eq_zero_of_periodic hp hper (by omega))
  · intro hnp N
    by_contra hcon
    push_neg at hcon
    -- the non-zero determinants all have index `< N`; take the largest
    have h0 : (hankel a 0).det ≠ 0 := by simp
    let r := Nat.findGreatest (fun M => (hankel a M).det ≠ 0) N
    have hr : (hankel a r).det ≠ 0 := Nat.findGreatest_spec (P := fun M => (hankel a M).det ≠ 0)
      (Nat.zero_le N) h0
    have hrN : r ≤ N := Nat.findGreatest_le N
    refine hnp (eventuallyPeriodic_of_hankel_det_eventually_zero hr fun M hM => ?_)
    rcases Nat.lt_or_ge M N with h | h
    · by_contra hne
      have := Nat.le_findGreatest (P := fun M => (hankel a M).det ≠ 0) h.le hne
      omega
    · exact hcon M h

/-- **To Do item 11, done: the Hankel form of Problem 1 is exact.** -/
theorem problem1IffHankelInfinitelyOften : Problem1IffHankelInfinitelyOften := by
  unfold Problem1IffHankelInfinitelyOften Problem1
  exact (hankel_infinitely_often_iff centerCol).symm

end GLM.Rule30
