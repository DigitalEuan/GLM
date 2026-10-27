module

public import RequestProject.GLM.Rule30.Prizes

/-!
# Round 23: the power-series ladder

Write `A(z) = ∑ a(n) zⁿ` over `GF(2)` for the centre column `a = centerCol`.  Classical
characterisations of "simple" sequences give equivalent forms of `Problem1` and stronger,
sufficient targets.  This file proves the implications for **every** Boolean sequence; the
finite certificates for the centre column are in `PowerSeriesLadderData.lean`.

## The ladder

  eventually periodic  =  rational `A(z)` (linear recurrence)  ⊂  2-automatic  ⊂  all sequences

* **2-kernel / automaticity.** `TwoKernel a` is the set of decimations `n ↦ a(2ᵏ n + r)`,
  `r < 2ᵏ`; `IsTwoAutomatic a` says it is finite (Eilenberg's characterisation of 2-automatic
  sequences, taken here as the definition).
  - `isTwoAutomatic_of_eventuallyPeriodic` — eventually periodic sequences are 2-automatic.
  - `problem1_of_centreNotTwoAutomatic` — so `CentreNotTwoAutomatic → Problem1`.
  - `not_isTwoAutomatic_of_kernelPath` — the kernel criterion: infinitely many pairwise distinct
    kernel members (one per depth) make the kernel infinite.
* **Linear complexity (power-series form).** `lcProfile a m` is the least `L` such that some
  linear recurrence of order `L` over `GF(2)` generates `a(0), …, a(m-1)` (the quantity computed
  by Berlekamp–Massey; here it is a specification, not an algorithm).
  - `eventuallyPeriodic_iff_lcBounded` — `a` is eventually periodic iff its linear-complexity
    profile is bounded; hence **`problem1_iff_lcUnbounded`**.
  - `noSmallPeriodicity_of_lcProfile` — the certificate interface: `N ≤ lcProfile a m` rules out
    every eventual period with `τ + p < N`.
* **Hankel determinants.** `hankel a N` is the `N × N` matrix `(a(i+j))` over `ZMod 2`.
  - `hankel_det_eq_zero_of_periodic` — an eventual period with `τ + p < N` kills `det (hankel a N)`
    (two equal columns).
  - `problem1_of_hankel_infinitely_often` — infinitely many non-zero Hankel determinants prove
    `Problem1`.  (The converse, Kronecker's theorem, is proved in `HankelKronecker.lean`.)
* **Factor complexity (Morse–Hedlund).** `complexity a n` is the number of distinct length-`n`
  blocks of the whole infinite sequence.
  - **`eventuallyPeriodic_iff_complexity_le`** — `a` is eventually periodic iff `complexity a n ≤ n`
    for some `n` (Morse–Hedlund, one-sided form); hence **`problem1_iff_complexity`**:
    `Problem1 ↔ ∀ n, n + 1 ≤ complexity centerCol n`.

### Correction to the Round 21 draft

The draft stated the complexity form with blocks counted inside the finite prefix of length
`2²²`.  That statement is not equivalent to `Problem1`: a prefix of length `M` contains at most
`M - n + 1` blocks of length `n`, which is `< n + 1` once `n > M/2`, so the draft's right-hand side is
false and the draft "iff" would assert `¬ Problem1`.  The equivalence holds for the blocks of the
infinite sequence, as stated here; a finite prefix only gives *lower* bounds on `complexity`.
-/

@[expose] public section

namespace GLM.Rule30

open Finset

/-! ## A finite-state lemma -/

/-- A sequence in a finite set whose next value is determined by the current one is eventually
periodic. -/
theorem eventually_periodic_of_next_determined {σ : Type*} [Finite σ] (s : ℕ → σ)
    (hs : ∀ i j, s i = s j → s (i + 1) = s (j + 1)) :
    ∃ p > 0, ∃ N, ∀ n ≥ N, s (n + p) = s n := by
  obtain ⟨i, j, hne, hij⟩ := Finite.exists_ne_map_eq_of_infinite s
  have key : ∀ i j, s i = s j → ∀ k, s (i + k) = s (j + k) := by
    intro i j h k
    induction k with
    | zero => simpa using h
    | succ k ih => exact hs _ _ ih
  rcases Nat.lt_or_gt_of_ne hne with h | h
  · refine ⟨j - i, by omega, i, fun n hn => ?_⟩
    have := key i j hij (n - i)
    rw [show i + (n - i) = n by omega, show j + (n - i) = n + (j - i) by omega] at this
    exact this.symm
  · refine ⟨i - j, by omega, j, fun n hn => ?_⟩
    have := key j i hij.symm (n - j)
    rw [show j + (n - j) = n by omega, show i + (n - j) = n + (i - j) by omega] at this
    exact this.symm

/-- Sequences with eventual period `p > 0` from time `N` form a finite set. -/
theorem finite_eventuallyPeriodic_from {p : ℕ} (hp : 0 < p) (N : ℕ) :
    {g : ℕ → Bool | ∀ n ≥ N, g (n + p) = g n}.Finite := by
  apply Set.Finite.of_finite_image (f := fun g (i : Fin (N + p)) => g i) (Set.toFinite _)
  intro g hg g' hg' heq
  have hfun : ∀ i < N + p, g i = g' i := fun i hi => congrFun heq ⟨i, hi⟩
  funext n
  induction n using Nat.strong_induction_on with
  | _ n ih =>
    by_cases hn : n < N + p
    · exact hfun n hn
    · have h1 := hg (n - p) (by omega)
      have h2 := hg' (n - p) (by omega)
      rw [show n - p + p = n by omega] at h1 h2
      rw [h1, h2]
      exact ih _ (by omega)

/-! ## The 2-kernel -/

/-- The 2-kernel of a sequence: all decimations `n ↦ a(2ᵏ n + r)` with `r < 2ᵏ`. -/
def TwoKernel (a : ℕ → Bool) : Set (ℕ → Bool) :=
  { f | ∃ k r, r < 2 ^ k ∧ f = fun n => a (2 ^ k * n + r) }

/-- `a` is 2-automatic: its 2-kernel is finite (Eilenberg's characterisation, used as the
definition). -/
def IsTwoAutomatic (a : ℕ → Bool) : Prop := (TwoKernel a).Finite

/-- **Eventually periodic sequences are 2-automatic.** Every kernel member has the same eventual
period `p` from the same time `N`, and such sequences are determined by their first `N + p`
values. -/
theorem isTwoAutomatic_of_eventuallyPeriodic {a : ℕ → Bool} (h : EventuallyPeriodic a) :
    IsTwoAutomatic a := by
  obtain ⟨p, hp, N, h⟩ := h
  refine (finite_eventuallyPeriodic_from hp N).subset ?_
  rintro f ⟨k, r, hr, rfl⟩ n hn
  show a (2 ^ k * (n + p) + r) = a (2 ^ k * n + r)
  have := periodic_mul h (2 ^ k) (2 ^ k * n + r) (by nlinarith [Nat.one_le_two_pow (n := k)])
  rw [← this]; congr 1; ring

/-- **The automaticity rung**: the centre column is not 2-automatic (open). -/
def CentreNotTwoAutomatic : Prop := ¬ IsTwoAutomatic centerCol

/-- `CentreNotTwoAutomatic` implies `Problem1`. -/
theorem problem1_of_centreNotTwoAutomatic (h : CentreNotTwoAutomatic) : Problem1 :=
  fun hp => h (isTwoAutomatic_of_eventuallyPeriodic hp)

/-- A choice of one kernel member per depth, pairwise distinct. -/
def KernelPath (a : ℕ → Bool) : Prop :=
  ∃ r : ℕ → ℕ, (∀ k, r k < 2 ^ k) ∧
    ∀ k₁ k₂, k₁ ≠ k₂ → (fun n => a (2 ^ k₁ * n + r k₁)) ≠ (fun n => a (2 ^ k₂ * n + r k₂))

/-- **The kernel criterion.** A kernel path makes the 2-kernel infinite. -/
theorem not_isTwoAutomatic_of_kernelPath {a : ℕ → Bool} (h : KernelPath a) :
    ¬ IsTwoAutomatic a := by
  obtain ⟨r, hr, hd⟩ := h
  refine Set.infinite_of_injective_forall_mem (f := fun k n => a (2 ^ k * n + r k)) ?_ ?_
  · intro k₁ k₂ he; by_contra hne; exact hd k₁ k₂ hne he
  · intro k; exact ⟨k, r k, hr k, rfl⟩

/-- **Kernel lower bounds.** If the decimations indexed by a finite set `S` of pairs `(k, r)` with
`r < 2ᵏ` are pairwise distinct, the 2-kernel has at least `|S|` elements. -/
theorem card_le_encard_twoKernel {a : ℕ → Bool} (S : Finset (ℕ × ℕ))
    (hS : ∀ x ∈ S, x.2 < 2 ^ x.1)
    (hinj : ∀ x ∈ S, ∀ y ∈ S, x ≠ y → ∃ n, a (2 ^ x.1 * n + x.2) ≠ a (2 ^ y.1 * n + y.2)) :
    (S.card : ℕ∞) ≤ (TwoKernel a).encard := by
  let f : ℕ × ℕ → ℕ → Bool := fun x n => a (2 ^ x.1 * n + x.2)
  have hf : Set.InjOn f (S : Set (ℕ × ℕ)) := by
    intro x hx y hy hxy
    by_contra hne
    obtain ⟨n, hn⟩ := hinj x hx y hy hne
    exact hn (congrFun hxy n)
  rw [← Set.encard_coe_eq_coe_finsetCard, ← hf.encard_image]
  refine Set.encard_le_encard ?_
  rintro _ ⟨x, hx, rfl⟩
  exact ⟨x.1, x.2, hS x hx, rfl⟩

/-! ## Linear recurrences and the linear-complexity profile -/

/-- A Boolean as an element of `GF(2)`. -/
def b2 (b : Bool) : ZMod 2 := if b then 1 else 0

theorem b2_inj {x y : Bool} (h : b2 x = b2 y) : x = y := by
  cases x <;> cases y <;> simp_all [b2]

/-- The value predicted at time `n` by the recurrence of order `L` with coefficients `c`:
`∑_{i < L} c i · a(n - 1 - i)` over `GF(2)`. -/
def recVal (a : ℕ → Bool) (L : ℕ) (c : ℕ → Bool) (n : ℕ) : ZMod 2 :=
  ∑ i ∈ range L, b2 (c i && a (n - 1 - i))

/-- The recurrence `(L, c)` generates `a(0), …, a(m-1)`: it predicts `a n` for `L ≤ n < m`. -/
def Fits (a : ℕ → Bool) (L : ℕ) (c : ℕ → Bool) (m : ℕ) : Prop :=
  ∀ n, L ≤ n → n < m → b2 (a n) = recVal a L c n

/-- **Linear-complexity profile** `L_a(m)`: the least order of a linear recurrence over `GF(2)`
generating the first `m` terms. -/
noncomputable def lcProfile (a : ℕ → Bool) (m : ℕ) : ℕ :=
  sInf { L | ∃ c : ℕ → Bool, Fits a L c m }

theorem lcProfile_le (a : ℕ → Bool) (m : ℕ) : lcProfile a m ≤ m :=
  Nat.sInf_le ⟨fun _ => false, fun n h1 h2 => by omega⟩

theorem lcProfile_spec (a : ℕ → Bool) (m : ℕ) : ∃ c, Fits a (lcProfile a m) c m :=
  Nat.sInf_mem (s := { L | ∃ c : ℕ → Bool, Fits a L c m })
    ⟨m, fun _ => false, fun n h1 h2 => by omega⟩

theorem lcProfile_le_of_fits {a : ℕ → Bool} {L m : ℕ} {c : ℕ → Bool} (h : Fits a L c m) :
    lcProfile a m ≤ L :=
  Nat.sInf_le ⟨c, h⟩

/-- The profile is bounded. -/
def LCBounded (a : ℕ → Bool) : Prop := ∃ B, ∀ m, lcProfile a m ≤ B

/-- The profile is unbounded (the power-series form of `Problem1`). -/
def LCUnbounded (a : ℕ → Bool) : Prop := ∀ B, ∃ m, B < lcProfile a m

/-- An eventual period `p` from time `τ` gives the recurrence `a n = a (n - p)` of order `τ + p`. -/
theorem fits_of_periodic {a : ℕ → Bool} {p τ : ℕ} (hp : 0 < p)
    (h : ∀ n ≥ τ, a (n + p) = a n) (m : ℕ) :
    Fits a (τ + p) (fun i => decide (i = p - 1)) m := by
  intro n hn _
  unfold recVal
  rw [Finset.sum_eq_single (p - 1)]
  · have := h (n - p) (by omega)
    rw [show n - p + p = n by omega] at this
    simp only [decide_true, Bool.true_and]
    rw [this, show n - 1 - (p - 1) = n - p by omega]
  · intro b _ hb; simp [hb, b2]
  · intro h'; simp at h'; omega

/-- A recurrence of order `L` that holds for all `n ≥ L` forces eventual periodicity. -/
theorem eventuallyPeriodic_of_fits_all {a : ℕ → Bool} {L : ℕ} {c : ℕ → Bool}
    (h : ∀ m, Fits a L c m) : EventuallyPeriodic a := by
  let s : ℕ → Fin (L + 1) → Bool := fun n i => a (n + i)
  have hs : ∀ i j, s i = s j → s (i + 1) = s (j + 1) := by
    intro i j hij
    have e : ∀ k ≤ L, a (i + k) = a (j + k) := fun k hk => congrFun hij ⟨k, by omega⟩
    funext ⟨k, hk⟩
    simp only [s]
    by_cases hkL : k < L
    · have := e (k + 1) (by omega)
      rw [show i + 1 + k = i + (k + 1) by ring, show j + 1 + k = j + (k + 1) by ring]; exact this
    · have hk' : k = L := by omega
      subst hk'
      apply b2_inj
      rw [h (i + 1 + k + 1) (i + 1 + k) (by omega) (by omega),
        h (j + 1 + k + 1) (j + 1 + k) (by omega) (by omega)]
      unfold recVal
      refine Finset.sum_congr rfl fun t ht => ?_
      simp only [Finset.mem_range] at ht
      have := e (k - t) (by omega)
      rw [show i + 1 + k - 1 - t = i + (k - t) by omega,
        show j + 1 + k - 1 - t = j + (k - t) by omega, this]
  obtain ⟨p, hp, N, hN⟩ := eventually_periodic_of_next_determined s hs
  exact ⟨p, hp, N, fun n hn => by simpa [s] using congrFun (hN n hn) 0⟩

theorem recVal_congr (a : ℕ → Bool) {L : ℕ} {c c' : ℕ → Bool} (h : ∀ i < L, c i = c' i)
    (n : ℕ) : recVal a L c n = recVal a L c' n :=
  Finset.sum_congr rfl fun i hi => by rw [h i (Finset.mem_range.1 hi)]

/-- Padding a recurrence with zero coefficients keeps it valid. -/
theorem fits_pad {a : ℕ → Bool} {L B m : ℕ} {c : ℕ → Bool} (h : Fits a L c m) (hLB : L ≤ B) :
    Fits a B (fun i => decide (i < L) && c i) m := by
  intro n hn hm
  rw [h n (by omega) hm]
  unfold recVal
  refine (Finset.sum_congr rfl fun i hi => ?_).trans
    (Finset.sum_subset (Finset.range_subset_range.2 hLB) ?_)
  · simp [Finset.mem_range.1 hi]
  · intro i hi hi'
    simp only [Finset.mem_range, not_lt] at hi hi'
    simp [b2, show ¬ i < L by omega]

/-- Compactness: if the profile is bounded, one recurrence fits every prefix. -/
theorem exists_fits_all_of_lcBounded {a : ℕ → Bool} (h : LCBounded a) :
    ∃ L c, ∀ m, Fits a L c m := by
  obtain ⟨B, hB⟩ := h
  let ext : (Fin B → Bool) → ℕ → Bool := fun f i => if hi : i < B then f ⟨i, hi⟩ else false
  by_contra hcon
  push_neg at hcon
  have hm : ∀ f : Fin B → Bool, ∃ m, ¬ Fits a B (ext f) m := fun f => hcon B (ext f)
  choose mf hmf using hm
  let M := Finset.univ.sup mf
  obtain ⟨c, hc⟩ := lcProfile_spec a M
  have hc' := fits_pad hc (hB M)
  let f : Fin B → Bool := fun i => decide (i.1 < lcProfile a M) && c i
  apply hmf f
  intro n hn hnm
  have hle : mf f ≤ M := Finset.le_sup (Finset.mem_univ f)
  rw [hc' n hn (by omega)]
  exact recVal_congr a (fun i hi => by simp [ext, f, hi]) n

/-- **Eventually periodic ⇔ bounded linear complexity.** -/
theorem eventuallyPeriodic_iff_lcBounded (a : ℕ → Bool) :
    EventuallyPeriodic a ↔ LCBounded a := by
  constructor
  · rintro ⟨p, hp, N, h⟩
    exact ⟨N + p, fun m => lcProfile_le_of_fits (fits_of_periodic hp h m)⟩
  · intro h
    obtain ⟨L, c, hc⟩ := exists_fits_all_of_lcBounded h
    exact eventuallyPeriodic_of_fits_all hc

/-- **`Problem1` in power-series form**: the linear-complexity profile of the centre column is
unbounded, i.e. `A(z)` is not a rational function over `GF(2)`. -/
theorem problem1_iff_lcUnbounded : Problem1 ↔ LCUnbounded centerCol := by
  rw [Problem1, eventuallyPeriodic_iff_lcBounded]
  simp only [LCBounded, LCUnbounded, not_exists, not_forall, not_le]

/-- **Certificate interface.** A linear-complexity lower bound `N ≤ L_a(m)` rules out every
eventual period `p` starting at `τ` with `τ + p < N`. -/
theorem noSmallPeriodicity_of_lcProfile {a : ℕ → Bool} {N m : ℕ} (h : N ≤ lcProfile a m) :
    ∀ τ p, 0 < p → τ + p < N → ¬ ∀ n ≥ τ, a (n + p) = a n := by
  intro τ p hp hlt hper
  have := lcProfile_le_of_fits (fits_of_periodic hp hper m)
  omega

/-! ## Hankel determinants -/

/-- The `N × N` Hankel matrix `(a(i + j))` over `GF(2)`. -/
def hankel (a : ℕ → Bool) (N : ℕ) : Matrix (Fin N) (Fin N) (ZMod 2) :=
  fun i j => b2 (a (i + j))

/-- An eventual period with `τ + p < N` makes columns `τ` and `τ + p` of the Hankel matrix equal. -/
theorem hankel_det_eq_zero_of_periodic {a : ℕ → Bool} {p τ N : ℕ} (hp : 0 < p)
    (h : ∀ n ≥ τ, a (n + p) = a n) (hN : τ + p < N) : (hankel a N).det = 0 := by
  refine Matrix.det_zero_of_column_eq (i := ⟨τ, by omega⟩) (j := ⟨τ + p, hN⟩) ?_ ?_
  · simp [Fin.ext_iff]; omega
  · intro k
    simp only [hankel]
    rw [show (k : ℕ) + (τ + p) = (k + τ) + p by ring, h _ (by omega)]

theorem b2_and (x y : Bool) : b2 (x && y) = b2 x * b2 y := by
  cases x <;> cases y <;> simp [b2]

/-- A recurrence of order `L < N` generating the first `2N - 1` terms makes column `L` of the
Hankel matrix a combination of the earlier columns, so the determinant vanishes. -/
theorem hankel_det_eq_zero_of_fits {a : ℕ → Bool} {L N m : ℕ} {c : ℕ → Bool}
    (h : Fits a L c m) (hL : L < N) (hm : 2 * N ≤ m + 1) : (hankel a N).det = 0 := by
  rw [← Matrix.exists_mulVec_eq_zero_iff]
  let w : ℕ → ZMod 2 := fun j => if j = L then 1 else if j < L then b2 (c (L - 1 - j)) else 0
  refine ⟨fun j => w j, fun hv => by simpa [w] using congrFun hv ⟨L, hL⟩, ?_⟩
  funext i
  simp only [Matrix.mulVec, dotProduct, hankel, Pi.zero_apply]
  rw [Fin.sum_univ_eq_sum_range (fun j => b2 (a (i + j)) * w j) N]
  have hsplit : ∑ j ∈ range N, b2 (a (i + j)) * w j =
      ∑ j ∈ range (L + 1), b2 (a (i + j)) * w j := by
    symm
    apply Finset.sum_subset (Finset.range_subset_range.2 (by omega))
    intro j hj hj'
    simp only [Finset.mem_range] at hj hj'
    simp [w, show j ≠ L by omega, show ¬ j < L by omega]
  rw [hsplit, Finset.sum_range_succ]
  have hlow : ∑ j ∈ range L, b2 (a (i + j)) * w j = recVal a L c (i + L) := by
    unfold recVal
    rw [← Finset.sum_range_reflect]
    refine Finset.sum_congr rfl fun k hk => ?_
    simp only [Finset.mem_range] at hk
    simp only [w, show L - 1 - k ≠ L by omega, show L - 1 - k < L by omega, if_false, if_true,
      b2_and]
    rw [show L - 1 - (L - 1 - k) = k by omega, show i + L - 1 - k = i + (L - 1 - k) by omega]
    ring
  rw [hlow, ← h (i + L) (by omega) (by omega)]
  simp only [w, if_true, mul_one]
  rw [← two_mul]
  exact mul_eq_zero_of_left (by decide) _

/-- **Hankel certificate for linear complexity.** A non-zero `N × N` Hankel determinant forces
linear complexity at least `N` on every prefix of length `m ≥ 2N - 1`: no linear recurrence of
order `< N` (equivalently, no rational function with denominator of degree `< N`) generates those
terms. -/
theorem le_lcProfile_of_hankel_det {a : ℕ → Bool} {N : ℕ} (h : (hankel a N).det ≠ 0)
    {m : ℕ} (hm : 2 * N ≤ m + 1) : N ≤ lcProfile a m := by
  by_contra hlt
  obtain ⟨c, hc⟩ := lcProfile_spec a m
  exact h (hankel_det_eq_zero_of_fits hc (by omega) hm)

/-- **Hankel form of the sufficient direction.** Infinitely many non-zero Hankel determinants
prove `Problem1`. -/
theorem problem1_of_hankel_infinitely_often
    (h : ∀ N, ∃ M ≥ N, (hankel centerCol M).det ≠ 0) : Problem1 := by
  rintro ⟨p, hp, τ, hper⟩
  obtain ⟨M, hM, hdet⟩ := h (τ + p + 1)
  exact hdet (hankel_det_eq_zero_of_periodic hp hper (by omega))

/-! ### A checkable certificate for `det (hankel a N) ≠ 0`

The prefix `a(0), …, a(2N-2)` is packed into one natural number `P`; row `j` of the Hankel matrix
is `(P >>> j) mod 2^N`.  An (unverified) Gauss–Jordan elimination `gf2Inverse` proposes an inverse;
`hankelInvCheck` verifies `B · H = I` row by row with bitwise xor, and
`hankel_det_ne_zero_of_check` proves that a successful check forces `det H ≠ 0`.  Only the checker
is trusted, not the elimination. -/

/-- Pack a list of bits into a natural number (bit `n` is the `n`-th entry). -/
def packBits (l : List Bool) : ℕ := l.reverse.foldl (fun acc b => Nat.bit b acc) 0

theorem testBit_packBits (l : List Bool) (n : ℕ) : (packBits l).testBit n = l.getD n false := by
  rw [packBits, List.foldl_reverse]
  induction l generalizing n with
  | nil => simp
  | cons b l ih =>
    cases n with
    | zero => simp
    | succ n => simp [Nat.testBit_bit_succ, ih]

/-- Row `j` of the Hankel matrix of the bits of `P`, as a bitmask. -/
def hankelRow (P N j : ℕ) : ℕ := (P >>> j) % 2 ^ N

theorem testBit_hankelRow (P N j l : ℕ) (hl : l < N) :
    (hankelRow P N j).testBit l = P.testBit (j + l) := by
  rw [hankelRow, Nat.testBit_mod_two_pow, Nat.testBit_shiftRight]; simp [hl]

/-- Gauss–Jordan elimination over `GF(2)` on bitmask rows, returning the proposed inverse rows.
(Unverified: its output is checked by `hankelInvCheck`.) -/
def gf2Inverse (N : ℕ) (row : ℕ → ℕ) : Array ℕ := Id.run do
  let mut A : Array ℕ := (Array.range N).map row
  let mut B : Array ℕ := (Array.range N).map fun i => 2 ^ i
  for c in [0:N] do
    let mut piv := N
    for r in [c:N] do
      if piv == N && (A.getD r 0).testBit c then piv := r
    if piv < N then
      let ar := A.getD piv 0
      let br := B.getD piv 0
      A := (A.set! piv (A.getD c 0)).set! c ar
      B := (B.set! piv (B.getD c 0)).set! c br
      for r in [0:N] do
        if r != c && (A.getD r 0).testBit c then
          A := A.set! r (A.getD r 0 ^^^ ar)
          B := B.set! r (B.getD r 0 ^^^ br)
  return B

/-- The xor of the rows `R j` selected by the bits of `b`. -/
def xorCombo (b : ℕ) (R : ℕ → ℕ) (N : ℕ) : ℕ :=
  (List.range N).foldl (fun acc j => if b.testBit j then acc ^^^ R j else acc) 0

theorem b2_xor (x y : Bool) : b2 (xor x y) = b2 x + b2 y := by
  cases x <;> cases y <;> simp [b2]; decide

theorem b2_testBit_xorCombo (b : ℕ) (R : ℕ → ℕ) (N l : ℕ) :
    b2 ((xorCombo b R N).testBit l) =
      ∑ j ∈ range N, b2 (b.testBit j) * b2 ((R j).testBit l) := by
  unfold xorCombo
  induction N with
  | zero => simp [b2]
  | succ N ih =>
    rw [List.range_succ, List.foldl_append, List.foldl_cons, List.foldl_nil,
      Finset.sum_range_succ, ← ih]
    split_ifs with h
    · rw [Nat.testBit_xor, b2_xor, h]; simp [b2]
    · simp [h, b2]

/-- The checker: the proposed inverse times the Hankel matrix is the identity. -/
def hankelInvCheck (P N : ℕ) : Bool :=
  let R := (Array.range N).map (hankelRow P N)
  let B := gf2Inverse N (fun j => R.getD j 0)
  (List.range N).all fun k => xorCombo (B.getD k 0) (fun j => R.getD j 0) N == 2 ^ k

/-- **Soundness of the Hankel certificate.** -/
theorem hankel_det_ne_zero_of_check {g : ℕ → Bool} {P N : ℕ} (hc : hankelInvCheck P N = true)
    (hP : ∀ n, n + 1 < 2 * N → P.testBit n = g n) : (hankel g N).det ≠ 0 := by
  have hR0 : ∀ j < N, ((Array.range N).map (hankelRow P N)).getD j 0 = hankelRow P N j := by
    intro j hj
    simp [Array.getD_eq_getD_getElem?, hj]
  simp only [hankelInvCheck, List.all_eq_true, List.mem_range, beq_iff_eq] at hc
  generalize (Array.range N).map (hankelRow P N) = R at hc hR0
  generalize gf2Inverse N (fun j => R.getD j 0) = B at hc
  let M : Matrix (Fin N) (Fin N) (ZMod 2) := fun k j => b2 ((B.getD k 0).testBit j)
  have hMH : M * hankel g N = 1 := by
    ext k l
    simp only [Matrix.mul_apply, M, hankel]
    rw [Fin.sum_univ_eq_sum_range (fun j => b2 ((B.getD k 0).testBit j) * b2 (g (j + l))) N]
    have : ∑ j ∈ range N, b2 ((B.getD k 0).testBit j) * b2 (g (j + l)) =
        ∑ j ∈ range N, b2 ((B.getD k 0).testBit j) * b2 ((R.getD j 0).testBit l) := by
      refine Finset.sum_congr rfl fun j hj => ?_
      rw [Finset.mem_range] at hj
      rw [hR0 j hj, testBit_hankelRow P N j l l.2, hP _ (by omega)]
    rw [this, ← b2_testBit_xorCombo, hc k k.2, Nat.testBit_two_pow, Matrix.one_apply]
    by_cases h : k = l
    · subst h; simp [b2]
    · have : (k : ℕ) ≠ l := fun h' => h (Fin.ext h')
      simp [b2, h, this]
  intro hdet
  have := congrArg Matrix.det hMH
  rw [Matrix.det_mul, hdet, mul_zero, Matrix.det_one] at this
  exact zero_ne_one this

/-! ## Factor complexity (Morse–Hedlund) -/

/-- The block of length `n` starting at position `i`. -/
def factorAt (a : ℕ → Bool) (n i : ℕ) : Fin n → Bool := fun j => a (i + j)

/-- The set of length-`n` blocks of the infinite sequence `a`. -/
def factors (a : ℕ → Bool) (n : ℕ) : Set (Fin n → Bool) := Set.range (factorAt a n)

/-- **Factor complexity** `p_a(n)`: the number of distinct length-`n` blocks of `a`. -/
noncomputable def complexity (a : ℕ → Bool) (n : ℕ) : ℕ := (factors a n).ncard

theorem complexity_zero (a : ℕ → Bool) : complexity a 0 = 1 := by
  rw [complexity, Set.ncard_eq_one]
  refine ⟨factorAt a 0 0, Set.eq_singleton_iff_unique_mem.2 ⟨⟨0, rfl⟩, fun w _ => ?_⟩⟩
  funext j; exact j.elim0

/-- Dropping the last letter of a block. -/
def restrictFactor {n : ℕ} (w : Fin (n + 1) → Bool) : Fin n → Bool := fun j => w (Fin.castSucc j)

theorem factors_eq_image (a : ℕ → Bool) (n : ℕ) :
    factors a n = restrictFactor '' factors a (n + 1) := by
  ext w
  constructor
  · rintro ⟨i, rfl⟩; exact ⟨factorAt a (n + 1) i, ⟨i, rfl⟩, rfl⟩
  · rintro ⟨_, ⟨i, rfl⟩, rfl⟩; exact ⟨i, rfl⟩

theorem complexity_le_two_pow (a : ℕ → Bool) (n : ℕ) : complexity a n ≤ 2 ^ n := by
  refine (Set.ncard_le_ncard (Set.subset_univ _) Set.finite_univ).trans ?_
  simp [Set.ncard_univ]

theorem complexity_mono (a : ℕ → Bool) (n : ℕ) : complexity a n ≤ complexity a (n + 1) := by
  rw [complexity, complexity, factors_eq_image]
  exact Set.ncard_image_le (Set.toFinite _)

/-- If every word of length `n` occurs, every shorter word occurs too. -/
theorem factors_univ_of_le {a : ℕ → Bool} {m n : ℕ} (hmn : m ≤ n)
    (h : ∀ w : Fin n → Bool, w ∈ factors a n) : ∀ w : Fin m → Bool, w ∈ factors a m := by
  intro w
  obtain ⟨i, hi⟩ := h fun j => if hj : (j : ℕ) < m then w ⟨j, hj⟩ else false
  refine ⟨i, funext fun j => ?_⟩
  have := congrFun hi ⟨j, by omega⟩
  simpa [factorAt] using this

/-- All `2ⁿ` words occur: `p_a(n) = 2ⁿ`. -/
theorem complexity_eq_two_pow {a : ℕ → Bool} {n : ℕ} (h : ∀ w : Fin n → Bool, w ∈ factors a n) :
    complexity a n = 2 ^ n := by
  rw [complexity, show factors a n = Set.univ from Set.eq_univ_of_forall h, Set.ncard_univ]
  simp

/-- An eventual period `p` from time `N` bounds the complexity by `N + p`. -/
theorem complexity_le_of_periodic {a : ℕ → Bool} {p N : ℕ} (hp : 0 < p)
    (h : ∀ n ≥ N, a (n + p) = a n) (n : ℕ) : complexity a n ≤ N + p := by
  have key : ∀ i, ∃ i' < N + p, factorAt a n i = factorAt a n i' := by
    intro i
    induction i using Nat.strong_induction_on with
    | _ i ih =>
      by_cases hi : i < N + p
      · exact ⟨i, hi, rfl⟩
      · obtain ⟨i', hi', he⟩ := ih (i - p) (by omega)
        refine ⟨i', hi', ?_⟩
        rw [← he]; funext j
        simp only [factorAt]
        rw [← h (i - p + j) (by omega)]; congr 1; omega
  have hsub : factors a n ⊆ ((Finset.range (N + p)).image (factorAt a n) : Set _) := by
    rintro _ ⟨i, rfl⟩
    obtain ⟨i', hi', he⟩ := key i
    simp only [Finset.coe_image, Finset.coe_range, Set.mem_image, Set.mem_Iio]
    exact ⟨i', hi', he.symm⟩
  refine (Set.ncard_le_ncard hsub (Finset.finite_toSet _)).trans ?_
  rw [Set.ncard_coe_finset]
  exact (Finset.card_image_le).trans (by simp)

/-- If `p_a(m + 1) = p_a(m)`, each block of length `m` has a unique extension, so `a` is eventually
periodic. -/
theorem eventuallyPeriodic_of_complexity_eq {a : ℕ → Bool} {m : ℕ}
    (h : complexity a (m + 1) = complexity a m) : EventuallyPeriodic a := by
  have hinj : Set.InjOn restrictFactor (factors a (m + 1)) :=
    Set.injOn_of_ncard_image_eq (by rw [← factors_eq_image]; exact h.symm) (Set.toFinite _)
  let s : ℕ → Fin (m + 1) → Bool := factorAt a (m + 1)
  have hs : ∀ i j, s i = s j → s (i + 1) = s (j + 1) := by
    intro i j hij
    apply hinj ⟨i + 1, rfl⟩ ⟨j + 1, rfl⟩
    funext k
    have := congrFun hij k.succ
    simp only [s, factorAt, restrictFactor, Fin.val_castSucc, Fin.val_succ] at this ⊢
    rw [show i + 1 + k = i + (k + 1) by ring, show j + 1 + k = j + (k + 1) by ring]
    exact this
  obtain ⟨p, hp, N, hN⟩ := eventually_periodic_of_next_determined s hs
  exact ⟨p, hp, N, fun n hn => by simpa [s, factorAt] using congrFun (hN n hn) 0⟩

/-- **Morse–Hedlund.** `a` is eventually periodic iff `p_a(n) ≤ n` for some `n`. -/
theorem eventuallyPeriodic_iff_complexity_le (a : ℕ → Bool) :
    EventuallyPeriodic a ↔ ∃ n, complexity a n ≤ n := by
  constructor
  · rintro ⟨p, hp, N, h⟩
    exact ⟨N + p, complexity_le_of_periodic hp h _⟩
  · rintro ⟨n, hn⟩
    by_contra hne
    have hstrict : ∀ m, complexity a m < complexity a (m + 1) := fun m =>
      lt_of_le_of_ne (complexity_mono a m) fun he =>
        hne (eventuallyPeriodic_of_complexity_eq he.symm)
    have : ∀ m, m + 1 ≤ complexity a m := by
      intro m
      induction m with
      | zero => rw [complexity_zero]
      | succ m ih => have := hstrict m; omega
    have := this n; omega

/-- **`Problem1` in complexity form**: every length `n` has at least `n + 1` distinct blocks in the
centre column. -/
theorem problem1_iff_complexity : Problem1 ↔ ∀ n, n + 1 ≤ complexity centerCol n := by
  rw [Problem1, eventuallyPeriodic_iff_complexity_le]
  simp only [not_exists, not_le, Nat.succ_le_iff]

/-! ### The draft's finite-prefix complexity form -/

/-- The number of distinct length-`n` blocks inside the prefix `a(0), …, a(m-1)`. -/
def prefixComplexity (a : ℕ → Bool) (n m : ℕ) : ℕ :=
  ((Finset.range (m + 1 - n)).image (factorAt a n)).card

/-- A prefix only gives lower bounds for the complexity. -/
theorem prefixComplexity_le_complexity (a : ℕ → Bool) (n m : ℕ) :
    prefixComplexity a n m ≤ complexity a n := by
  rw [prefixComplexity, complexity, ← Set.ncard_coe_finset]
  refine Set.ncard_le_ncard ?_ (Set.toFinite _)
  intro w hw
  simp only [Finset.coe_image, Set.mem_image] at hw
  obtain ⟨i, -, rfl⟩ := hw
  exact ⟨i, rfl⟩

/-- **Audit of the Round 21 draft.** The draft stated `Problem1 ↔ ∀ n, n + 1 ≤ p_M(n)` with the
blocks counted inside a fixed prefix of length `M` (`M = 2²²` in the draft).  For `n = M + 1` the
right-hand side fails, so the draft statement is equivalent to `¬ Problem1`: asserting it would
assert that the centre column *is* eventually periodic. -/
theorem draftComplexityForm_iff (M : ℕ) :
    (Problem1 ↔ ∀ n, n + 1 ≤ prefixComplexity centerCol n M) ↔ ¬ Problem1 := by
  have hfalse : ¬ ∀ n, n + 1 ≤ prefixComplexity centerCol n M := by
    intro h
    have := h (M + 1)
    simp [prefixComplexity] at this
  constructor
  · intro h hp; exact hfalse (h.1 hp)
  · intro h; exact ⟨fun hp => absurd hp h, fun h' => absurd h' hfalse⟩

/-- The full Hankel form of `Problem1`. The `←` direction is
`problem1_of_hankel_infinitely_often`; the `→` direction (Kronecker's converse) is proved in
Round 24, so the whole statement is the theorem `problem1IffHankelInfinitelyOften`
(`HankelKronecker.lean`). -/
def Problem1IffHankelInfinitelyOften : Prop :=
  Problem1 ↔ ∀ N, ∃ M ≥ N, (hankel centerCol M).det ≠ 0

end GLM.Rule30
