module

public import Mathlib

/-!
# Substrate-native cognition, round two: the certificates behind the new frames

The formal half of round two (Phase 63) of
`studies/SUBSTRATE_NATIVE_COGNITION_STUDY.md` (its §6 and §7). Round two
wires three new readings into the typed planner and refines three concepts
that the first round had found close to useful but not quite there. Each
answer the new readings give carries a certificate, and this file proves
that each kind of certificate means what the answer says.

* **Y1, intervals.** Two closed intervals overlap exactly when some value
  lies in both (`closed_overlap_iff`). That makes the planner's **yes** and
  **no** to *is X consistent with Y* sound in both directions.
* **Y2, rational recognition.** Two distinct fractions `p/q` and `r/s` differ
  by at least `1/(q s)` (`farey_rival_bound`). So an interval narrower than
  that holds at most one of them (`farey_unique_in_interval`), and the
  window of a delta-sigma stream pins its input to `[S/n, (S+1)/n)`
  (`stream_window_sound`).
* **Y3, dimensional derivation.** An exponent vector reached with
  independent columns is the only one (`monomial_unique`, with
  `ker_trivial_of_rank` turning the rank the code checks into its hypothesis). A covector that
  kills every column and not the target rules out every exponent vector
  (`monomial_impossible`). A non-zero kernel vector gives a whole line of
  solutions (`monomial_undetermined`).
* **Y4, vacuum seeking inside a coset.** For 0/1 words the coherence TAX is
  `HW · (Y + 1/8)` (`tax_binary`). Any strictly increasing function of the
  weight has the same minimisers over a coset as the Hamming distance
  (`coset_argmin_iff_nearest`), so constrained vacuum seeking *is*
  nearest-codeword decoding.
* **Y6 (C2), streams.** The delta-sigma output as a `Stream'`: its first `N`
  bits sum to `⌊N t⌋` (`dsStream_sum`), every bit is 0 or 1 when
  `0 ≤ t < 1` (`dsStream_bit`), and a rational input `p/q` gives a stream
  with period `q` (`dsStream_drop_period`). `GLM.Info.dsBit_eq_floor_diff`
  (in `Sturmian.lean`) proves that the shipped loop emits exactly this
  stream.
* **Y7 (C1), the stack as a Galois connection.** One layer refines another
  exactly when its kernel is finer. Refinement is the same thing as
  factorisation (`refines_iff_factors`). The cumulative layer's kernel is
  the meet of the two kernels (`ker_pair_eq_inf`), so it is the coarsest
  layer refining both (`ker_le_pair_iff`). Image and preimage of partitions
  along a layer map form a Galois connection (`map_comap_gc`).
-/

@[expose] public section

namespace GLM.SubstrateCognition

/-! ## Y1 — interval consistency -/

/-- Two closed intervals meet exactly when some value lies in both: the
planner's *yes* names such a value's existence, and its *no* rules out every
value. -/
theorem closed_overlap_iff {a b c d : ℚ} (hab : a ≤ b) (hcd : c ≤ d) :
    (a ≤ d ∧ c ≤ b) ↔ ∃ x, (a ≤ x ∧ x ≤ b) ∧ (c ≤ x ∧ x ≤ d) := by
  constructor
  · rintro ⟨h1, h2⟩
    exact ⟨max a c, ⟨le_max_left _ _, max_le hab h2⟩,
      ⟨le_max_right _ _, max_le h1 hcd⟩⟩
  · rintro ⟨x, ⟨h1, h2⟩, h3, h4⟩
    exact ⟨h1.trans h4, h3.trans h2⟩

/-! ## Y2 — rational recognition -/

/-- **The Farey bound.** Two distinct fractions `p/q` and `r/s` with positive
denominators differ by at least `1/(q s)`. -/
theorem farey_rival_bound (p r : ℤ) {q s : ℤ} (hq : 0 < q) (hs : 0 < s)
    (hne : (p : ℚ) / q ≠ (r : ℚ) / s) :
    1 / ((q : ℚ) * s) ≤ |(p : ℚ) / q - (r : ℚ) / s| := by
  have hq' : (0 : ℚ) < q := by exact_mod_cast hq
  have hs' : (0 : ℚ) < s := by exact_mod_cast hs
  have hkey : (p : ℚ) / q - (r : ℚ) / s = ((p * s - r * q : ℤ) : ℚ) / (q * s) := by
    push_cast
    field_simp
  have hnum : p * s - r * q ≠ 0 := by
    intro h
    apply hne
    have : (p : ℚ) * s = r * q := by exact_mod_cast sub_eq_zero.mp h
    field_simp
    linarith
  have hone : (1 : ℚ) ≤ |((p * s - r * q : ℤ) : ℚ)| := by
    have : (1 : ℤ) ≤ |p * s - r * q| := Int.one_le_abs hnum
    exact_mod_cast this
  rw [hkey, abs_div, abs_of_pos (mul_pos hq' hs')]
  exact div_le_div_of_nonneg_right hone (mul_pos hq' hs').le

/-- **At most one simple fraction in a narrow interval.** If two fractions
lie in an interval narrower than `1/(q s)`, they are the same fraction. This
is the uniqueness half of every recognition certificate. -/
theorem farey_unique_in_interval (p r : ℤ) {q s : ℤ} (hq : 0 < q) (hs : 0 < s)
    {lo hi : ℚ} (h1 : lo ≤ (p : ℚ) / q) (h2 : (p : ℚ) / q ≤ hi)
    (h3 : lo ≤ (r : ℚ) / s) (h4 : (r : ℚ) / s ≤ hi)
    (hw : hi - lo < 1 / ((q : ℚ) * s)) :
    (p : ℚ) / q = (r : ℚ) / s := by
  by_contra hne
  have hb := farey_rival_bound p r hq hs hne
  have : |(p : ℚ) / q - (r : ℚ) / s| ≤ hi - lo := by
    rw [abs_le]
    constructor <;> linarith
  linarith

/-- A fraction whose denominator is at most `Q`, in an interval narrower than
`1/Q²`, is the only such fraction there. -/
theorem farey_unique_bounded (p r : ℤ) {q s Q : ℤ} (hq : 0 < q) (hs : 0 < s)
    (hqQ : q ≤ Q) (hsQ : s ≤ Q) {lo hi : ℚ} (h1 : lo ≤ (p : ℚ) / q)
    (h2 : (p : ℚ) / q ≤ hi) (h3 : lo ≤ (r : ℚ) / s) (h4 : (r : ℚ) / s ≤ hi)
    (hw : hi - lo < 1 / ((Q : ℚ) * Q)) :
    (p : ℚ) / q = (r : ℚ) / s := by
  apply farey_unique_in_interval p r hq hs h1 h2 h3 h4
  have hq' : (0 : ℚ) < q := by exact_mod_cast hq
  have hs' : (0 : ℚ) < s := by exact_mod_cast hs
  have hqQ' : (q : ℚ) ≤ Q := by exact_mod_cast hqQ
  have hsQ' : (s : ℚ) ≤ Q := by exact_mod_cast hsQ
  have : 1 / ((Q : ℚ) * Q) ≤ 1 / ((q : ℚ) * s) :=
    one_div_le_one_div_of_le (mul_pos hq' hs') (mul_le_mul hqQ' hsQ' hs'.le (hq'.le.trans hqQ'))
  linarith

/-- **What a window says.** After `n` ticks the ones-count is `⌊n t⌋`
(`GLM.Info.dsOnes_eq_floor`), so the input lies in `[S/n, (S+1)/n)`. -/
theorem stream_window_sound (t : ℝ) {n : ℕ} (hn : 0 < n) :
    (⌊(n : ℝ) * t⌋ : ℝ) / n ≤ t ∧ t < ((⌊(n : ℝ) * t⌋ : ℝ) + 1) / n := by
  have hn' : (0 : ℝ) < n := by exact_mod_cast hn
  constructor
  · rw [div_le_iff₀ hn']
    have := Int.floor_le ((n : ℝ) * t)
    linarith
  · rw [lt_div_iff₀ hn']
    have := Int.lt_floor_add_one ((n : ℝ) * t)
    linarith

/-! ## Y3 — dimensional derivation -/

section Monomial

variable {m n : Type*} [Fintype n]

/-- **Unique.** With independent columns (a trivial kernel), two exponent
vectors that both reproduce the target are equal. -/
theorem monomial_unique (M : Matrix m n ℚ) (t : m → ℚ) {x y : n → ℚ}
    (hker : ∀ z, M.mulVec z = 0 → z = 0) (hx : M.mulVec x = t)
    (hy : M.mulVec y = t) : x = y := by
  have : M.mulVec (x - y) = 0 := by
    rw [Matrix.mulVec_sub, hx, hy, sub_self]
  exact sub_eq_zero.mp (hker _ this)

/-- **What the code checks is what the theorem needs.** The planner checks
that the columns have full rank; full column rank is a trivial kernel, the
hypothesis of `monomial_unique`. -/
theorem ker_trivial_of_rank [Fintype m] [DecidableEq n] (M : Matrix m n ℚ)
    (hr : M.rank = Fintype.card n) : ∀ z, M.mulVec z = 0 → z = 0 := by
  intro z hz
  have h := LinearMap.finrank_range_add_finrank_ker M.mulVecLin
  rw [← Matrix.rank, hr, Module.finrank_fintype_fun_eq_card] at h
  have hk : Module.finrank ℚ (LinearMap.ker M.mulVecLin) = 0 := by omega
  have := Submodule.finrank_eq_zero.mp hk
  have hz' : z ∈ LinearMap.ker M.mulVecLin := by simpa using hz
  rw [this] at hz'
  simpa using hz'

/-- **Impossible.** A covector that kills every column but not the target
rules out every exponent vector: this is the certificate behind a *no
product of powers* answer. -/
theorem monomial_impossible [Fintype m] (M : Matrix m n ℚ) (t : m → ℚ) (y : m → ℚ)
    (hy : Matrix.vecMul y M = 0) (ht : y ⬝ᵥ t ≠ 0) :
    ∀ x : n → ℚ, M.mulVec x ≠ t := by
  intro x hx
  apply ht
  rw [← hx, Matrix.dotProduct_mulVec, hy, zero_dotProduct]

/-- **Undetermined.** A non-zero kernel vector gives a line of solutions,
pairwise distinct: the dimensionless group is free, so the planner refuses. -/
theorem monomial_undetermined (M : Matrix m n ℚ) (t : m → ℚ) {x z : n → ℚ}
    (hx : M.mulVec x = t) (hz : M.mulVec z = 0) (hz0 : z ≠ 0) :
    (∀ c : ℚ, M.mulVec (x + c • z) = t) ∧
      Function.Injective (fun c : ℚ => x + c • z) := by
  refine ⟨fun c => ?_, fun c d h => ?_⟩
  · rw [Matrix.mulVec_add, Matrix.mulVec_smul, hz, smul_zero, add_zero, hx]
  · have h' : c • z = d • z := add_left_cancel h
    have : (c - d) • z = 0 := by rw [sub_smul, h', sub_self]
    rcases smul_eq_zero.mp this with h0 | h0
    · exact sub_eq_zero.mp h0
    · exact absurd h0 hz0

end Monomial

/-! ## Y4 — vacuum seeking inside a coset -/

/-- For a word whose entries are all 0 or 1, the coherence TAX
`HW · Y + ‖v‖² / 8` is `HW · (Y + 1/8)`. -/
theorem tax_binary {n : ℕ} (Y : ℚ) (v : Fin n → ℚ) (hv : ∀ i, v i = 0 ∨ v i = 1) :
    ((Finset.univ.filter fun i => v i ≠ 0).card : ℚ) * Y + (∑ i, v i ^ 2) / 8
      = ((Finset.univ.filter fun i => v i ≠ 0).card : ℚ) * (Y + 1 / 8) := by
  have hsq : ∑ i, v i ^ 2 = ((Finset.univ.filter fun i => v i ≠ 0).card : ℚ) := by
    rw [Finset.card_filter, Nat.cast_sum]
    refine Finset.sum_congr rfl fun i _ => ?_
    rcases hv i with h | h <;> simp [h]
  rw [hsq]
  ring

/-- **Constrained vacuum seeking is nearest-codeword decoding.** For any
strictly increasing `f` of the Hamming weight (the coherence TAX of a 0/1
word is one, by `tax_binary`), a codeword minimises `f (weight (r + c))`
over a code exactly when it is nearest to `r`. -/
theorem coset_argmin_iff_nearest {n : ℕ} (C : Set (Fin n → ZMod 2))
    (f : ℕ → ℚ) (hf : StrictMono f) (r c : Fin n → ZMod 2) :
    (∀ c' ∈ C, f (hammingNorm (r + c)) ≤ f (hammingNorm (r + c'))) ↔
      (∀ c' ∈ C, hammingDist r c ≤ hammingDist r c') := by
  have key : ∀ a b : Fin n → ZMod 2, hammingDist a b = hammingNorm (a + b) := by
    intro a b
    rw [hammingDist_eq_hammingNorm]
    congr 1
    funext i
    simp only [Pi.sub_apply, Pi.add_apply]
    exact ZModModule.sub_eq_add (a i) (b i)
  simp only [key, hf.le_iff_le]

/-! ## Y6 (C2) — the delta-sigma output as a stream -/

/-- The delta-sigma output of input `t`, as a `Stream'`: the bit at tick `n`
is `⌊(n+1) t⌋ - ⌊n t⌋` (`GLM.Info.dsBit_eq_floor_diff`). -/
noncomputable def dsStream (t : ℝ) : Stream' ℤ :=
  fun n => ⌊((n : ℝ) + 1) * t⌋ - ⌊(n : ℝ) * t⌋

/-- The first `N` bits of the stream sum to exactly `⌊N t⌋`. -/
theorem dsStream_sum (t : ℝ) (N : ℕ) :
    ∑ i ∈ Finset.range N, dsStream t i = ⌊(N : ℝ) * t⌋ := by
  induction N with
  | zero => simp
  | succ k ih =>
      rw [Finset.sum_range_succ, ih]
      simp only [dsStream]
      push_cast
      ring

/-- For `0 ≤ t < 1` every bit of the stream is 0 or 1. -/
theorem dsStream_bit {t : ℝ} (ht0 : 0 ≤ t) (ht1 : t < 1) (n : ℕ) :
    dsStream t n = 0 ∨ dsStream t n = 1 := by
  simp only [dsStream]
  have h1 : ⌊(n : ℝ) * t⌋ ≤ ⌊((n : ℝ) + 1) * t⌋ :=
    Int.floor_mono (by nlinarith)
  have h2 : ⌊((n : ℝ) + 1) * t⌋ ≤ ⌊(n : ℝ) * t⌋ + 1 := by
    rw [← Int.floor_add_one]
    exact Int.floor_mono (by nlinarith)
  omega

/-- **A rational input gives a periodic stream.** For `t = p/q` the stream
dropped by `q` ticks is the stream itself. -/
theorem dsStream_drop_period (p : ℤ) {q : ℕ} (hq : 0 < q) :
    Stream'.drop q (dsStream ((p : ℝ) / q)) = dsStream ((p : ℝ) / q) := by
  funext n
  have hq' : (q : ℝ) ≠ 0 := by exact_mod_cast hq.ne'
  have shift : ∀ k : ℕ, ((((k + q : ℕ) : ℝ)) * ((p : ℝ) / q))
      = (k : ℝ) * ((p : ℝ) / q) + (p : ℤ) := by
    intro k
    push_cast
    field_simp
  simp only [Stream'.drop, Stream'.get, dsStream]
  have e1 : (((n + q : ℕ) : ℝ) + 1) = (((n + 1 + q : ℕ) : ℝ)) := by push_cast; ring
  have e2 : ((n : ℝ) + 1) = ((n + 1 : ℕ) : ℝ) := by push_cast; ring
  rw [e1, shift (n + 1), shift n, Int.floor_add_intCast, Int.floor_add_intCast, e2]
  ring

/-! ## Y7 (C1) — the stack as a Galois connection -/

section Layers

variable {C V W : Type*}

/-- **Refinement is factorisation.** One layer map `f` refines another `g`
(what `f` conflates, `g` conflates too) exactly when `g` factors through
`f`. -/
theorem refines_iff_factors [Nonempty W] (f : C → V) (g : C → W) :
    Setoid.ker f ≤ Setoid.ker g ↔ ∃ h : V → W, g = h ∘ f := by
  classical
  constructor
  · intro hle
    refine ⟨fun v => if hv : ∃ c, f c = v then g hv.choose else Classical.arbitrary W, ?_⟩
    funext c
    have hv : ∃ c', f c' = f c := ⟨c, rfl⟩
    simp only [Function.comp_apply, dif_pos hv]
    exact (hle hv.choose_spec).symm
  · rintro ⟨h, rfl⟩ a b hab
    simp only [Setoid.ker, Function.onFun, Function.comp_apply] at hab ⊢
    exact congrArg h hab

/-- **The cumulative layer is the meet.** The kernel of the paired layer
`c ↦ (f c, g c)` is the meet of the two kernels. -/
theorem ker_pair_eq_inf (f : C → V) (g : C → W) :
    Setoid.ker (fun c => (f c, g c)) = Setoid.ker f ⊓ Setoid.ker g := by
  ext a b
  simp only [Setoid.ker, Function.onFun, Setoid.inf_def, Prod.mk.injEq]
  rfl

/-- **Coarsest refining both.** A layer refines the cumulative layer exactly
when it refines each of its two parts (`glmIntegerLayer_least` is one
direction of this, on the shipped carriers). -/
theorem ker_le_pair_iff {U : Type*} (k : C → U) (f : C → V) (g : C → W) :
    Setoid.ker k ≤ Setoid.ker (fun c => (f c, g c)) ↔
      Setoid.ker k ≤ Setoid.ker f ∧ Setoid.ker k ≤ Setoid.ker g := by
  rw [ker_pair_eq_inf, le_inf_iff]

/-- **Image ⊣ preimage.** Along a layer map `f`, pushing a partition forward
and pulling one back form a Galois connection between the partition
lattices. -/
theorem map_comap_gc (f : C → V) :
    GaloisConnection (fun r : Setoid C => Setoid.map r f)
      (fun s : Setoid V => Setoid.comap f s) := by
  intro r s
  constructor
  · intro h a b hab
    exact h (Relation.EqvGen.rel _ _ ⟨a, b, hab, rfl, rfl⟩)
  · intro h x y hxy
    induction hxy with
    | rel x y hr =>
        obtain ⟨a, b, hab, rfl, rfl⟩ := hr
        exact h hab
    | refl x => exact s.refl' x
    | symm x y _ ih => exact s.symm' ih
    | trans x y z _ _ ih1 ih2 => exact s.trans' ih1 ih2

end Layers

end GLM.SubstrateCognition
