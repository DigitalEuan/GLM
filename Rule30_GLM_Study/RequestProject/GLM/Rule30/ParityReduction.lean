module

public import RequestProject.GLM.Rule30.ANF

/-!
# Halving the parity-count problem: half of the cells are forced

Round 6, feedback #3 track A ("an exact reduction of the parity count").  All results proved.

`whiteDiagonalCount n` (`ANF.lean`) counts the rows `x` supported on `[2−n, n−1]` (that is
`2n − 2` free cells) whose space-time diagram is white along the diagonal `(k, n−1−k)`, `k < n`;
its parity is the coefficient of the top monomial (`anfCoeff_topMonomial_eq_count`).

**Observation (cone separation does half of the work).** The constraint at time `k` reads the
cells `[n−1−2k, n−1]` of the row, and by cone separation (`cone_separation_decomposition`) it is
`x_{n−1−2k} xor (something depending only on cells to the right) = 0`.  So, scanning the row from
right to left, every cell at an *even* distance `n−1−2k` from the right end is **forced**, and only
the `n − 1` cells at *odd* distance, `n−2, n−4, …, 2−n`, are free.  The last constraint (`k = n−1`)
would force the cell `1 − n`, which lies outside the window, so it becomes a genuine condition.

* `buildAux`, `build n f` : the row obtained by scanning right to left, taking free cells from `f`
  and forced cells from the constraints.
* `reducedPhi n f` : the value the scan forces at position `1 − n`.
* `build_constraints` : the built row always satisfies all `n` diagonal constraints.
* `build_of_valid` : every valid row is the built row of its own free cells.
* `whiteDiagonalCount_eq_reduced` : **`whiteDiagonalCount n = #{g < 2^(n−1) : reducedPhi n g = 0}`**,
  a count over `2^(n−1)` instead of `2^(2n−2)` rows.
* `topMonomialConjecture_iff_reduced` : the top-monomial conjecture ⟺ for every `n ≥ 2` the
  number of zeros of the `(n−1)`-variable Boolean function `reducedPhi n` is odd ⟺ (for `n ≥ 2`)
  its number of ones is odd, i.e. `reducedPhi n` has full algebraic degree `n − 1`.
-/

@[expose] public section

namespace GLM.Rule30

open Finset

/-- The position handled at step `m` of the right-to-left scan. -/
def scanPos (n m : ℕ) : ℤ := (n : ℤ) - 1 - m

/-- The right-to-left scan: after `m` steps the cells `n−1, …, n−m` are set.  At even steps
`m = 2k` the cell is forced to make the cell `(k, n−1−k)` white; at odd steps it is read from
`f (m / 2)`. -/
def buildAux (n : ℕ) (f : ℕ → Bool) : ℕ → Config
  | 0 => fun _ => false
  | m + 1 => Function.update (buildAux n f m) (scanPos n m)
      (if m % 2 = 0 then evolve (buildAux n f m) (m / 2) ((n : ℤ) - 1 - ((m / 2 : ℕ) : ℤ))
       else f (m / 2))

/-- The built row (positions `n−1` down to `1−n`). -/
def build (n : ℕ) (f : ℕ → Bool) : Config := buildAux n f (2 * n - 1)

/-- The reduced Boolean function: the value forced at the outside position `1 − n`. -/
def reducedPhi (n : ℕ) (f : ℕ → Bool) : Bool := build n f (1 - n)

variable {n : ℕ} {f : ℕ → Bool}

/-- After `m` steps only the cells `(n−1−m, n−1]` can be black. -/
theorem buildAux_support (m : ℕ) (q : ℤ) (hq : buildAux n f m q = true) :
    scanPos n m < q ∧ q ≤ (n : ℤ) - 1 := by
  induction m generalizing q with
  | zero => simp [buildAux] at hq
  | succ m ih =>
    simp only [scanPos] at ih ⊢
    by_cases hqm : q = scanPos n m
    · subst hqm; simp only [scanPos]; push_cast; omega
    · rw [buildAux, Function.update_of_ne hqm] at hq
      have := ih q hq; push_cast; omega

theorem buildAux_eq_false (m : ℕ) (q : ℤ) (hq : q ≤ scanPos n m ∨ (n : ℤ) - 1 < q) :
    buildAux n f m q = false := by
  by_contra h
  have := buildAux_support m q (by simpa using h)
  omega

/-- Cells already set are never changed. -/
theorem buildAux_stable {m m' : ℕ} (h : m ≤ m') (q : ℤ) (hq : scanPos n m < q) :
    buildAux n f m' q = buildAux n f m q := by
  induction m', h using Nat.le_induction with
  | base => rfl
  | succ m' hmm' ih =>
    rw [buildAux, Function.update_of_ne (by simp only [scanPos] at hq ⊢; omega), ih]

/-- The scan satisfies the constraint `k` as soon as it has passed the cell `n−1−2k`. -/
theorem buildAux_constraint (k m' : ℕ) (hm : 2 * k + 1 ≤ m') :
    evolve (buildAux n f m') k ((n : ℤ) - 1 - k) = false := by
  have hcongr : evolve (buildAux n f m') k ((n : ℤ) - 1 - k) =
      evolve (buildAux n f (2 * k + 1)) k ((n : ℤ) - 1 - k) :=
    evolve_congr _ _ _ _ (fun j hj _ => buildAux_stable hm j (by simp only [scanPos]; push_cast; omega))
  rw [hcongr, cone_separation_decomposition]
  have hpos : (n : ℤ) - 1 - k - k = scanPos n (2 * k) := by simp only [scanPos]; push_cast; ring
  have hk2 : (2 * k) / 2 = k := by omega
  rw [hpos]
  simp only [buildAux, Function.update_self, Function.update_idem, if_pos (show 2 * k % 2 = 0 by omega),
    hk2]
  have hfalse : Function.update (buildAux n f (2 * k)) (scanPos n (2 * k)) false =
      buildAux n f (2 * k) := by
    funext j
    by_cases hj : j = scanPos n (2 * k)
    · subst hj; rw [Function.update_self, buildAux_eq_false _ _ (Or.inl le_rfl)]
    · rw [Function.update_of_ne hj]
  rw [hfalse]
  simp

/-- **The built row satisfies all diagonal constraints.** -/
theorem build_constraints (k : ℕ) (hk : k < n) :
    evolve (build n f) k ((n : ℤ) - 1 - k) = false :=
  buildAux_constraint k _ (by omega)

/-- A valid row: white outside `[2−n, n−1]` and white along the diagonal. -/
def ValidRow (n : ℕ) (x : Config) : Prop :=
  (∀ q, x q = true → 2 - (n : ℤ) ≤ q ∧ q ≤ (n : ℤ) - 1) ∧
    ∀ k < n, evolve x k ((n : ℤ) - 1 - k) = false

/-- The scan reproduces a valid row from its free cells. -/
theorem buildAux_of_valid {x : Config} (hx : ValidRow n x)
    (hf : ∀ i, i + 1 < n → f i = x ((n : ℤ) - 2 - 2 * i)) (m : ℕ) (hm : m ≤ 2 * n - 1) (q : ℤ)
    (hq : scanPos n m < q) : buildAux n f m q = x q := by
  induction m generalizing q with
  | zero =>
    simp only [scanPos, CharP.cast_eq_zero, sub_zero] at hq
    simp only [buildAux]
    by_contra h
    have := hx.1 q (by simpa using (Ne.symm h))
    omega
  | succ m ih =>
    have ih' := ih (by omega)
    by_cases hqm : q = scanPos n m
    · subst hqm
      rw [buildAux, Function.update_self]
      split_ifs with hpar
      · -- forced cell
        set k := m / 2 with hk
        have hm2 : m = 2 * k := by omega
        have hkn : k < n := by omega
        have hc := hx.2 k hkn
        rw [cone_separation_decomposition] at hc
        have hpos : (n : ℤ) - 1 - k - k = scanPos n m := by
          simp only [scanPos]; rw [hm2]; push_cast; ring
        rw [hpos] at hc
        have hval : x (scanPos n m) =
            evolve (Function.update x (scanPos n m) false) k ((n : ℤ) - 1 - k) := by
          revert hc; cases x (scanPos n m) <;> cases evolve (Function.update x (scanPos n m) false) k
            ((n : ℤ) - 1 - k) <;> simp
        rw [hval]
        apply evolve_congr
        intro j hj1 hj2
        by_cases hj : j = scanPos n m
        · subst hj; rw [Function.update_self, buildAux_eq_false _ _ (Or.inl le_rfl)]
        · rw [Function.update_of_ne hj]
          exact ih' j (by rw [← hpos]; omega)
      · -- free cell
        have hi : m / 2 + 1 < n := by omega
        rw [hf _ hi]
        congr 1; simp only [scanPos]; push_cast; omega
    · rw [buildAux, Function.update_of_ne hqm]
      exact ih' q (by simp only [scanPos] at hq hqm ⊢; push_cast at hq; omega)

/-- **Every valid row is the built row of its free cells.** -/
theorem build_of_valid {x : Config} (hx : ValidRow n x)
    (hf : ∀ i, i + 1 < n → f i = x ((n : ℤ) - 2 - 2 * i)) : build n f = x := by
  funext q
  by_cases hq : scanPos n (2 * n - 1) < q
  · exact buildAux_of_valid hx hf _ le_rfl q hq
  · rw [build, buildAux_eq_false _ _ (Or.inl (not_lt.mp hq))]
    by_contra h
    have := hx.1 q (by simpa using (Ne.symm h))
    simp only [scanPos] at hq
    omega

/-- The built row carries its free cells. -/
theorem build_free (i : ℕ) (hi : i + 1 < n) : build n f ((n : ℤ) - 2 - 2 * i) = f i := by
  have hpos : (n : ℤ) - 2 - 2 * i = scanPos n (2 * i + 1) := by
    simp only [scanPos]; push_cast; ring
  have hlt : scanPos n (2 * i + 2) < (n : ℤ) - 2 - 2 * i := by
    simp only [scanPos]; push_cast; omega
  rw [build, buildAux_stable (m := 2 * i + 2) (by omega) _ hlt, hpos, buildAux,
    Function.update_self, if_neg (by omega)]
  congr 1; omega

/-- The built row is valid exactly when the forced outside value is white. -/
theorem validRow_build_iff (hn : 1 ≤ n) : ValidRow n (build n f) ↔ reducedPhi n f = false := by
  constructor
  · intro h
    by_contra hc
    have := h.1 (1 - n) (by simpa [reducedPhi] using hc)
    omega
  · intro h
    refine ⟨fun q hq => ?_, fun k hk => build_constraints k hk⟩
    have hs := buildAux_support _ q hq
    simp only [scanPos] at hs
    have hne : q ≠ 1 - n := by
      rintro rfl; simp [reducedPhi, hq] at h
    omega

/-- Any finite bit pattern is the bit pattern of some number below `2^L`. -/
theorem exists_mask (L : ℕ) (p : ℕ → Bool) : ∃ g < 2 ^ L, ∀ i < L, g.testBit i = p i := by
  induction L generalizing p with
  | zero => exact ⟨0, by simp, fun i hi => absurd hi (Nat.not_lt_zero _)⟩
  | succ L ih =>
    obtain ⟨g, hg, hbits⟩ := ih (fun i => p (i + 1))
    refine ⟨Nat.bit (p 0) g, ?_, fun i hi => ?_⟩
    · rw [Nat.bit_val, pow_succ]; cases p 0 <;> simp <;> omega
    · rcases i with _ | i
      · exact Nat.testBit_bit_zero _ _
      · rw [Nat.testBit_bit_succ]; exact hbits i (by omega)

/-- **The reduction.** `whiteDiagonalCount n` is the number of zeros of the `(n−1)`-variable
Boolean function `reducedPhi n`. -/
theorem whiteDiagonalCount_eq_reduced (hn : 1 ≤ n) :
    whiteDiagonalCount n =
      ((range (2 ^ (n - 1))).filter (fun g => reducedPhi n (fun i => g.testBit i) = false)).card := by
  -- the row of a valid `g`, as a subset of the window
  have hind : ∀ g : ℕ, reducedPhi n (fun i => g.testBit i) = false →
      ind ((Icc (2 - (n : ℤ)) (n - 1)).filter (fun q => build n (fun i => g.testBit i) q = true)) =
        build n (fun i => g.testBit i) := by
    intro g hg
    have hv := (validRow_build_iff hn).mpr hg
    funext q
    simp only [ind, mem_filter, mem_Icc]
    cases hb : build n (fun i => g.testBit i) q
    · simp
    · have := hv.1 q hb; simp [this]
  unfold whiteDiagonalCount
  symm
  apply Finset.card_bij
    (fun (g : ℕ) _ => (Icc (2 - (n : ℤ)) (n - 1)).filter (fun q => build n (fun i => g.testBit i) q = true))
  · intro g hg
    simp only [mem_filter, mem_range] at hg
    simp only [mem_filter, mem_powerset]
    refine ⟨filter_subset _ _, fun k hk => ?_⟩
    rw [hind g hg.2]
    exact build_constraints k hk
  · intro g₁ hg₁ g₂ hg₂ heq
    simp only [mem_filter, mem_range] at hg₁ hg₂
    have hb := congrArg ind heq
    rw [hind g₁ hg₁.2, hind g₂ hg₂.2] at hb
    apply Nat.eq_of_testBit_eq
    intro i
    by_cases hi : i + 1 < n
    · have h1 := build_free (f := fun i => g₁.testBit i) i hi
      have h2 := build_free (f := fun i => g₂.testBit i) i hi
      simp only at h1 h2
      rw [← h1, ← h2, hb]
    · rw [Nat.testBit_eq_false_of_lt (lt_of_lt_of_le hg₁.1 (Nat.pow_le_pow_right (by norm_num)
        (by omega))), Nat.testBit_eq_false_of_lt (lt_of_lt_of_le hg₂.1 (Nat.pow_le_pow_right
        (by norm_num) (by omega)))]
  · intro T hT
    simp only [mem_filter, mem_powerset] at hT
    have hv : ValidRow n (ind T) := by
      refine ⟨fun q hq => ?_, hT.2⟩
      have : q ∈ T := by simpa [ind] using hq
      exact mem_Icc.mp (hT.1 this)
    obtain ⟨g, hg, hbits⟩ := exists_mask (n - 1) (fun i => ind T ((n : ℤ) - 2 - 2 * i))
    have hbuild : build n (fun i => g.testBit i) = ind T :=
      build_of_valid hv (fun i hi => hbits i (by omega))
    have hphi : reducedPhi n (fun i => g.testBit i) = false := by
      rw [reducedPhi, hbuild]
      simp only [ind, decide_eq_false_iff_not]
      intro h; have := mem_Icc.mp (hT.1 h); omega
    refine ⟨g, by simp [hg, hphi], ?_⟩
    rw [hbuild]
    ext q
    simp only [mem_filter, ind, decide_eq_true_eq]
    constructor
    · exact fun h => h.2
    · exact fun h => ⟨hT.1 h, h⟩

/-- **The top-monomial conjecture in reduced form.** -/
theorem topMonomialConjecture_iff_reduced :
    TopMonomialConjecture ↔ ∀ n : ℕ, 2 ≤ n →
      Odd ((range (2 ^ (n - 1))).filter
        (fun g => reducedPhi n (fun i => g.testBit i) = false)).card := by
  rw [topMonomialConjecture_iff]
  refine forall_congr' (fun n => imp_congr_right (fun hn => ?_))
  rw [whiteDiagonalCount_eq_reduced (by omega)]

/-- For `n ≥ 2` the number of zeros and the number of ones of `reducedPhi n` have the same
parity (their sum `2^(n−1)` is even). -/
theorem reduced_zeros_odd_iff_ones_odd (hn : 2 ≤ n) :
    Odd ((range (2 ^ (n - 1))).filter (fun g => reducedPhi n (fun i => g.testBit i) = false)).card ↔
      Odd ((range (2 ^ (n - 1))).filter
        (fun g => reducedPhi n (fun i => g.testBit i) = true)).card := by
  have hsum := card_filter_add_card_filter_not (s := range (2 ^ (n - 1)))
    (fun g => reducedPhi n (fun i => g.testBit i) = false)
  simp only [Bool.not_eq_false, card_range] at hsum
  have heven : Even (2 ^ (n - 1)) := (Nat.even_pow' (by omega)).mpr even_two
  rw [← hsum] at heven
  have h2 := Nat.not_odd_iff_even.mpr heven
  rw [Nat.odd_add] at h2
  rw [← Nat.not_even_iff_odd (n := #({g ∈ range (2 ^ (n - 1)) |
    (reducedPhi n fun i => g.testBit i) = true}))]
  tauto

end GLM.Rule30
