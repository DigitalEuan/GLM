module

public import Mathlib

/-!
# The rest of track P: what the Phase 107 readings rest on

`studies/DERIVATION_TWO_STUDY.md` (Phase 107) adds eight derivations and
eleven outside frames to the machine
(`overlay/glm_universal/reasoning/info_inequality.py`, `coding_theory.py`,
`maxent.py`, `spectral.py`, `fft_derivation.py`).  This file proves the
facts their readings rest on.
-/

@[expose] public section

namespace GLM.DerivationsTwo

universe u v

open Finset Real

/-! ## 1. Gibbs' inequality and mutual information -/

/-- One term of Gibbs' inequality: `p log (p/q) ≥ p - q`, with equality only at `p = q`. -/
private lemma gibbs_term {p q : ℝ} (hp : 0 ≤ p) (hq : 0 < q) :
    p - q ≤ p * Real.log (p / q) ∧ (p * Real.log (p / q) = p - q → p = q) := by
  rcases hp.eq_or_lt with h0 | hpos
  · subst h0; simp; exact ⟨hq.le, fun h => h.symm⟩
  · have hx : 0 < q / p := div_pos hq hpos
    have e : Real.log (p / q) = - Real.log (q / p) := by
      rw [← Real.log_inv, inv_div]
    have key : p * (q / p) = q := by field_simp
    refine ⟨?_, ?_⟩
    · have := Real.log_le_sub_one_of_pos hx
      rw [e]; nlinarith
    · intro heq
      by_contra hne
      have hne' : q / p ≠ 1 := by
        intro h1; apply hne; field_simp at h1; linarith
      have := Real.log_lt_sub_one_of_pos hx hne'
      rw [e] at heq; nlinarith

/-- **Gibbs' inequality**, with its equality case: for distributions `p`, `q`
on a finite set with `q > 0`, `D(p ‖ q) = ∑ p log (p/q) ≥ 0`, and `D = 0`
only when `p = q`. -/
theorem gibbs_inequality {ι : Type*} (s : Finset ι) (p q : ι → ℝ)
    (hp : ∀ i ∈ s, 0 ≤ p i) (hq : ∀ i ∈ s, 0 < q i)
    (hps : ∑ i ∈ s, p i = 1) (hqs : ∑ i ∈ s, q i = 1) :
    0 ≤ ∑ i ∈ s, p i * Real.log (p i / q i) ∧
      (∑ i ∈ s, p i * Real.log (p i / q i) = 0 → ∀ i ∈ s, p i = q i) := by
  have hdiff : ∑ i ∈ s, (p i - q i) = 0 := by rw [Finset.sum_sub_distrib, hps, hqs]; ring
  have hle : ∑ i ∈ s, (p i - q i) ≤ ∑ i ∈ s, p i * Real.log (p i / q i) :=
    Finset.sum_le_sum fun i hi => (gibbs_term (hp i hi) (hq i hi)).1
  refine ⟨by linarith, fun h0 i hi => ?_⟩
  have hz : ∑ j ∈ s, (p j * Real.log (p j / q j) - (p j - q j)) = 0 := by
    rw [Finset.sum_sub_distrib, h0, hdiff]; ring
  have := (Finset.sum_eq_zero_iff_of_nonneg fun j hj =>
    sub_nonneg.2 (gibbs_term (hp j hj) (hq j hj)).1).1 hz i hi
  exact (gibbs_term (hp i hi) (hq i hi)).2 (by linarith)

/-- **Mutual information is nonnegative**, and zero only for independence:
`I(X;Y) = ∑ P(x,y) log (P(x,y)/(P(x)P(y))) = D(P ‖ P_X P_Y)`. -/
theorem mutual_information_nonneg {α β : Type*} [Fintype α] [Fintype β]
    (P : α → β → ℝ) (hP : ∀ x y, 0 ≤ P x y) (hsum : ∑ x, ∑ y, P x y = 1)
    (hX : ∀ x, 0 < ∑ y, P x y) (hY : ∀ y, 0 < ∑ x, P x y) :
    0 ≤ ∑ x, ∑ y, P x y * Real.log (P x y / ((∑ y', P x y') * ∑ x', P x' y))
      ∧ (∑ x, ∑ y, P x y * Real.log (P x y / ((∑ y', P x y') * ∑ x', P x' y))
          = 0 → ∀ x y, P x y = (∑ y', P x y') * ∑ x', P x' y) := by
  have hprod : ∑ z : α × β, (∑ y', P z.1 y') * ∑ x', P x' z.2 = 1 := by
    have hsum' := hsum
    rw [Fintype.sum_prod_type]; simp_rw [← Finset.mul_sum, ← Finset.sum_mul]
    rw [Finset.sum_comm] at hsum'; rw [hsum', mul_one, Finset.sum_comm]; exact hsum'
  have g := gibbs_inequality (Finset.univ : Finset (α × β)) (fun z => P z.1 z.2)
    (fun z => (∑ y', P z.1 y') * ∑ x', P x' z.2) (fun z _ => hP _ _)
    (fun z _ => mul_pos (hX _) (hY _)) (by rw [Fintype.sum_prod_type]; exact hsum) hprod
  rw [Fintype.sum_prod_type] at g
  exact ⟨g.1, fun h x y => g.2 h (x, y) (Finset.mem_univ _)⟩

/-! ## 2. Shannon-type certificates -/

/-- A certificate is sound: if `c = ∑ λᵢ Eᵢ + ∑ μⱼ Gⱼ` with every `λᵢ ≥ 0`,
then every vector `h` meeting the elemental inequalities `Eᵢ · h ≥ 0` and
the givens `Gⱼ · h = 0` has `c · h ≥ 0`. -/
theorem shannon_certificate_sound {m k l : ℕ} (c : Fin m → ℝ)
    (E : Fin k → Fin m → ℝ) (G : Fin l → Fin m → ℝ) (lam : Fin k → ℝ)
    (mu : Fin l → ℝ) (hlam : ∀ i, 0 ≤ lam i)
    (hc : ∀ t, c t = ∑ i, lam i * E i t + ∑ j, mu j * G j t)
    (h : Fin m → ℝ) (hE : ∀ i, 0 ≤ ∑ t, E i t * h t)
    (hG : ∀ j, ∑ t, G j t * h t = 0) :
    0 ≤ ∑ t, c t * h t := by
  have : ∑ t, c t * h t = ∑ i, lam i * ∑ t, E i t * h t + ∑ j, mu j * ∑ t, G j t * h t := by
    simp_rw [hc, add_mul, Finset.sum_add_distrib, Finset.sum_mul, Finset.mul_sum]
    rw [Finset.sum_comm, Finset.sum_comm (s := Finset.univ) (t := Finset.univ)
      (f := fun x y => mu y * G y x * h x)]
    congr 1 <;> refine Finset.sum_congr rfl fun _ _ => Finset.sum_congr rfl fun _ _ => by ring
  rw [this]; simp [hG]
  exact Finset.sum_nonneg fun i _ => mul_nonneg (hlam i) (hE i)

/-- Conditional mutual information of a set function:
`I(A;B|C) = h(A ∪ C) + h(B ∪ C) - h(A ∪ B ∪ C) - h(C)`. -/
def cmi {ι : Type*} [DecidableEq ι] (h : Finset ι → ℝ) (A B C : Finset ι) : ℝ :=
  h (A ∪ C) + h (B ∪ C) - h (A ∪ B ∪ C) - h C

/-- **The data processing inequality** for any set function meeting the
Shannon inequalities: if `X → Y → Z` (`I(X;Z|Y) = 0`) then
`I(X;Y) ≥ I(X;Z)`; the certificate is `I(X;Y) - I(X;Z) = I(X;Y|Z) - I(X;Z|Y)`. -/
theorem data_processing {ι : Type*} [DecidableEq ι] (h : Finset ι → ℝ)
    (hshannon : ∀ A B C, 0 ≤ cmi h A B C) (x y z : ι)
    (hmarkov : cmi h {x} {z} {y} = 0) :
    cmi h {x} {z} ∅ ≤ cmi h {x} {y} ∅ := by
  have h1 := hshannon {x} {y} {z}
  have e : cmi h {x} {y} ∅ - cmi h {x} {z} ∅ = cmi h {x} {y} {z} - cmi h {x} {z} {y} := by
    simp only [cmi, Finset.union_empty]
    have a1 : ({x} ∪ {y} : Finset ι) ∪ {z} = ({x} ∪ {z}) ∪ {y} := by
      ext; simp; tauto
    have a2 : ({y} ∪ {z} : Finset ι) = {z} ∪ {y} := Finset.union_comm _ _
    rw [a1, a2]; ring
  linarith

/-! ## 3. Kraft-McMillan -/

/-- The `n`-th power of the Kraft sum is a sum over all `n`-sequences of codewords. -/
private lemma kraft_power {D m : ℕ} (w : Fin m → List (Fin D)) (n : ℕ) (r : ℝ) :
    (∑ i, r ^ (w i).length) ^ n = ∑ s : Fin n → Fin m, r ^ (∑ j, (w (s j)).length) := by
  rw [← Fin.prod_const, Fintype.prod_sum]
  refine Finset.sum_congr rfl fun s _ => ?_
  rw [Finset.prod_pow_eq_pow_sum]

/-- Unique decodability: at most `D^t` codeword sequences have total length `t`. -/
private lemma kraft_fiber_card {D m n : ℕ} (w : Fin m → List (Fin D))
    (hud : Function.Injective (fun s : List (Fin m) => (s.map w).flatten)) (t : ℕ) :
    (univ.filter (fun s : Fin n → Fin m => ∑ j, (w (s j)).length = t)).card ≤ D ^ t := by
  classical
  let S : Finset (List (Fin D)) := univ.image (fun v : List.Vector (Fin D) t => v.toList)
  have hS : S.card ≤ D ^ t := by
    calc S.card ≤ (univ : Finset (List.Vector (Fin D) t)).card := card_image_le
      _ = D ^ t := by simp [card_vector]
  refine le_trans (card_le_card_of_injOn (fun s => ((List.ofFn s).map w).flatten) ?_ ?_) hS
  · intro s hs
    simp only [coe_filter, mem_univ, true_and, Set.mem_setOf_eq] at hs
    simp only [S, coe_image, coe_univ, Set.image_univ, Set.mem_range]
    refine ⟨⟨((List.ofFn s).map w).flatten, ?_⟩, rfl⟩
    rw [List.length_flatten, ← hs, List.map_map, List.map_ofFn, List.sum_ofFn]; rfl
  · intro s _ s' _ h
    exact List.ofFn_injective (hud h)

/-- A number whose powers grow at most linearly is at most `1`. -/
private lemma le_one_of_pow_le_linear {K l : ℝ} (hl : 0 ≤ l)
    (hK : ∀ n : ℕ, K ^ n ≤ n * l + 1) : K ≤ 1 := by
  by_contra h
  push_neg at h
  have ht := tendsto_pow_const_div_const_pow_of_one_lt 1 h
  have hev := (ht.eventually (gt_mem_nhds (show (0:ℝ) < 1 / (l + 1) by positivity))).and
    (Filter.eventually_ge_atTop 1)
  obtain ⟨n, hn, hn1⟩ := hev.exists
  simp only [pow_one] at hn
  have hKn : 0 < K ^ n := by positivity
  rw [div_lt_div_iff₀ hKn (by positivity)] at hn
  have := hK n
  have hn1' : (1:ℝ) ≤ n := by exact_mod_cast hn1
  nlinarith

/-- **McMillan's theorem**: every uniquely decodable code over `D ≥ 2`
symbols -- concatenation of codeword sequences injective -- has Kraft sum
`∑ D^(-lᵢ) ≤ 1`. -/
theorem kraft_mcmillan {D m : ℕ} (hD : 2 ≤ D) (w : Fin m → List (Fin D))
    (hud : Function.Injective (fun s : List (Fin m) => (s.map w).flatten)) :
    ∑ i, ((D : ℝ)⁻¹) ^ (w i).length ≤ 1 := by
  classical
  have hDpos : (0:ℝ) < D := by exact_mod_cast (by omega : 0 < D)
  apply le_one_of_pow_le_linear (l := ((∑ i, (w i).length : ℕ) : ℝ)) (Nat.cast_nonneg _)
  intro n
  rw [kraft_power]
  let L : (Fin n → Fin m) → ℕ := fun s => ∑ j, (w (s j)).length
  have hmaps : ∀ s ∈ (univ : Finset (Fin n → Fin m)),
      L s ∈ range (n * (∑ i, (w i).length) + 1) := by
    intro s _
    simp only [mem_range, Nat.lt_succ_iff]
    calc ∑ j, (w (s j)).length ≤ ∑ _j : Fin n, ∑ i, (w i).length :=
          Finset.sum_le_sum fun j _ =>
            Finset.single_le_sum (f := fun i => (w i).length) (fun _ _ => Nat.zero_le _)
              (mem_univ (s j))
      _ = n * ∑ i, (w i).length := by simp
  change ∑ s, ((D : ℝ)⁻¹) ^ L s ≤ _
  rw [← Finset.sum_fiberwise_of_maps_to hmaps]
  have hfib : ∀ t ∈ range (n * (∑ i, (w i).length) + 1),
      ∑ s ∈ univ with L s = t, ((D : ℝ)⁻¹) ^ L s ≤ 1 := by
    intro t _
    have e : ∑ s ∈ univ with L s = t, ((D : ℝ)⁻¹) ^ L s
        = ((univ.filter (fun s => L s = t)).card : ℝ) * ((D : ℝ)⁻¹) ^ t := by
      rw [Finset.sum_congr rfl (g := fun _ => ((D : ℝ)⁻¹) ^ t)
          (fun s hs => by rw [(Finset.mem_filter.1 hs).2]), Finset.sum_const, nsmul_eq_mul]
    rw [e]
    have hc : ((univ.filter (fun s => L s = t)).card : ℝ) ≤ (D : ℝ) ^ t := by
      exact_mod_cast kraft_fiber_card w hud t
    calc _ ≤ (D : ℝ) ^ t * ((D : ℝ)⁻¹) ^ t := mul_le_mul_of_nonneg_right hc (by positivity)
      _ = 1 := by rw [← mul_pow, mul_inv_cancel₀ hDpos.ne', one_pow]
  refine (Finset.sum_le_sum hfib).trans ?_
  simp

/-! ## 4. The radix-2 split -/

/-- Decimation in frequency, even outputs: `X[2r]` is the half-length DFT of
`x[n] + x[n + M]`. -/
theorem dif_even {R : Type*} [CommRing R] (M : ℕ) (ω : R) (hω : ω ^ (2 * M) = 1)
    (x : ℕ → R) (r : ℕ) :
    ∑ n ∈ range (2 * M), x n * ω ^ (n * (2 * r)) =
      ∑ n ∈ range M, (x n + x (n + M)) * (ω ^ 2) ^ (n * r) := by
  rw [two_mul, Finset.sum_range_add, ← Finset.sum_add_distrib]
  refine Finset.sum_congr rfl fun n _ => ?_
  have : ω ^ ((M + n) * (2 * r)) = ω ^ (n * (2 * r)) := by
    rw [show (M + n) * (2 * r) = 2 * M * r + n * (2 * r) by ring, pow_add, pow_mul, hω, one_pow,
      one_mul]
  rw [this, add_comm M n, ← pow_mul]; ring_nf

/-- Decimation in frequency, odd outputs: `X[2r+1]` is the half-length DFT
of `(x[n] - x[n + M]) ω^n`. -/
theorem dif_odd {R : Type*} [CommRing R] (M : ℕ) (ω : R) (hω : ω ^ M = -1)
    (x : ℕ → R) (r : ℕ) :
    ∑ n ∈ range (2 * M), x n * ω ^ (n * (2 * r + 1)) =
      ∑ n ∈ range M, (x n - x (n + M)) * ω ^ n * (ω ^ 2) ^ (n * r) := by
  rw [two_mul, Finset.sum_range_add, ← Finset.sum_add_distrib]
  refine Finset.sum_congr rfl fun n _ => ?_
  have : ω ^ ((M + n) * (2 * r + 1)) = - ω ^ (n * (2 * r + 1)) := by
    rw [show (M + n) * (2 * r + 1) = M * (2 * r + 1) + n * (2 * r + 1) by ring, pow_add, pow_mul,
      hω, pow_succ, pow_mul, neg_one_sq, one_pow]; ring
  rw [this, add_comm M n, ← pow_mul]; ring_nf

/-! ## 5. The rate posterior -/

/-- The posterior `p^a (1-p)^b` (`a` flips, `b` clean bits) increases
strictly up to its mode `a/(a+b)`. -/
theorem posterior_increasing (a b : ℕ) (ha : 1 ≤ a) {p q : ℝ} (hp : 0 ≤ p)
    (hpq : p < q) (hq : q ≤ a / (a + b)) :
    p ^ a * (1 - p) ^ b < q ^ a * (1 - q) ^ b := by
  have hab : (0:ℝ) < a + b := by positivity
  have hmono : StrictMonoOn (fun x : ℝ => x ^ a * (1 - x) ^ b) (Set.Icc 0 (a / (a + b))) := by
    apply strictMonoOn_of_deriv_pos (convex_Icc _ _)
    · fun_prop
    · intro x hx
      rw [interior_Icc] at hx
      obtain ⟨hx0, hx1⟩ := hx
      have hmode : (a:ℝ) / (a + b) ≤ 1 := (div_le_one hab).2 (by simp)
      have h1x : 0 < 1 - x := by linarith
      have hlin : 0 < (a:ℝ) - (a + b) * x := by
        rw [lt_div_iff₀ hab] at hx1; linarith
      have hd : HasDerivAt (fun x : ℝ => x ^ a * (1 - x) ^ b)
          (a * x ^ (a - 1) * (1 - x) ^ b + x ^ a * (b * (1 - x) ^ (b - 1) * (-1))) x := by
        apply HasDerivAt.mul (hasDerivAt_pow a x)
        have := (hasDerivAt_pow b (1 - x)).comp x ((hasDerivAt_id x).const_sub 1)
        simpa using this
      rw [hd.deriv]
      rcases Nat.eq_zero_or_pos b with hb | hb
      · subst hb; simp; positivity
      · obtain ⟨a', rfl⟩ : ∃ a', a = a' + 1 := ⟨a - 1, by omega⟩
        obtain ⟨b', rfl⟩ : ∃ b', b = b' + 1 := ⟨b - 1, by omega⟩
        simp only [Nat.add_sub_cancel, pow_succ]
        have : 0 < x ^ a' * (1 - x) ^ b' := by positivity
        push_cast at hlin ⊢
        nlinarith [mul_pos this hlin, mul_pos (mul_pos this hlin) hx0,
          mul_pos (mul_pos this hlin) h1x]
  exact hmono ⟨hp, hpq.le.trans hq⟩ ⟨hp.trans hpq.le, hq⟩ hpq

/-! ## 6. Rate distortion of a binary source -/

/-- The backward test channel of the binary source: with
`q = (p - D)/(1 - 2D)`, `q` is a probability, the reconstruction `Xh ~
Bernoulli(q)` sent through a BSC(`D`) gives `P(X = 1) = p`, and the
distortion is `D`; and the step of the lower bound -- the binary entropy is
increasing on `[0, 1/2]` -- holds. -/
theorem rd_test_channel {p D : ℝ} (hD0 : 0 ≤ D) (hDp : D ≤ p) (hp : p ≤ 1 / 2)
    (hD : D < 1 / 2) :
    0 ≤ (p - D) / (1 - 2 * D) ∧ (p - D) / (1 - 2 * D) ≤ 1 ∧
      (p - D) / (1 - 2 * D) * (1 - D) + (1 - (p - D) / (1 - 2 * D)) * D = p ∧
      (∀ d, 0 ≤ d → d ≤ D → Real.binEntropy d ≤ Real.binEntropy D) := by
  have h12 : 0 < 1 - 2 * D := by linarith
  refine ⟨div_nonneg (by linarith) h12.le, (div_le_one h12).2 (by linarith), ?_, ?_⟩
  · have key := div_mul_cancel₀ (p - D) h12.ne'
    linear_combination key
  · intro d hd0 hdD
    exact Real.binEntropy_strictMonoOn.monotoneOn ⟨hd0, by linarith⟩ ⟨hD0, by linarith⟩ hdD

/-! ## 7. Transmission through a delta barrier -/

/-- The matching conditions at a delta barrier and their solution: with
`t = 2ik/(2ik - g)` and `r = t - 1`, continuity and the derivative jump
hold, `|t|² = 1/(1 + g²/(4k²))`, `|r|² + |t|² = 1`, and with
`k² = 2mE/ħ²`, `g = 2mα/ħ²` this is `1/(1 + mα²/(2ħ²E))`. -/
theorem delta_transmission (k g : ℝ) (hk : k ≠ 0) :
    let t : ℂ := 2 * k * Complex.I / (2 * k * Complex.I - g)
    let r : ℂ := t - 1
    (1 + r = t) ∧
      (Complex.I * k * t - Complex.I * k * (1 - r) = g * t) ∧
      Complex.normSq t = 1 / (1 + g ^ 2 / (4 * k ^ 2)) ∧
      Complex.normSq r + Complex.normSq t = 1 := by
  intro t r
  have hden : (2 * k * Complex.I - g) ≠ 0 := by
    intro h
    have := congrArg Complex.im h
    simp at this; exact hk this
  have hns : Complex.normSq (2 * k * Complex.I - g) = 4 * k ^ 2 + g ^ 2 := by
    simp [Complex.normSq_apply]; ring
  have hnum : Complex.normSq (2 * k * Complex.I) = 4 * k ^ 2 := by
    simp [Complex.normSq_apply]; ring
  have hk2 : (0:ℝ) < k ^ 2 := by positivity
  refine ⟨by simp [r], ?_, ?_, ?_⟩
  · have key := div_mul_cancel₀ (2 * k * Complex.I) hden
    simp only [r, t]
    linear_combination key
  · simp only [t]; rw [Complex.normSq_div, hns, hnum]; field_simp
  · have hr : r = g / (2 * k * Complex.I - g) := by
      simp only [r, t]; field_simp; ring
    rw [hr]; simp only [t]; rw [Complex.normSq_div, Complex.normSq_div, hns, hnum,
      Complex.normSq_ofReal]
    have : (0:ℝ) < 4 * k ^ 2 + g ^ 2 := by positivity
    field_simp; ring

/-- The energy form of the delta-barrier transmission coefficient. -/
theorem delta_transmission_energy {m E hbar α k g : ℝ} (hm : 0 < m) (hE : 0 < E)
    (hh : 0 < hbar) (hk2 : k ^ 2 = 2 * m * E / hbar ^ 2)
    (hg : g = 2 * m * α / hbar ^ 2) :
    1 / (1 + g ^ 2 / (4 * k ^ 2)) = 1 / (1 + m * α ^ 2 / (2 * hbar ^ 2 * E)) := by
  congr 2
  rw [hk2, hg]; field_simp; ring

/-! ## 8. Eigenfunctions -/

/-- **The particle on a ring**: `ψ_m(φ) = exp(i m φ)/√(2π)` has second
derivative `-m² ψ_m` (so `-(ħ²/2I) ψ'' = (m²ħ²/2I) ψ`), is `2π`-periodic for
integer `m`, and is normalised on `[0, 2π]`. -/
theorem ring_eigenfunction (m : ℤ) :
    let ψ : ℝ → ℂ := fun φ => Complex.exp (Complex.I * m * φ) / Real.sqrt (2 * π)
    (∀ φ : ℝ, HasDerivAt ψ (Complex.I * m * ψ φ) φ) ∧
      (∀ φ : ℝ, HasDerivAt (fun φ => Complex.I * m * ψ φ) (-(m : ℂ) ^ 2 * ψ φ) φ) ∧
      (∀ φ : ℝ, ψ (φ + 2 * π) = ψ φ) ∧
      ∫ φ in (0 : ℝ)..(2 * π), Complex.normSq (ψ φ) = 1 := by
  intro ψ
  have hd : ∀ φ : ℝ, HasDerivAt ψ (Complex.I * m * ψ φ) φ := by
    intro φ
    have h1 : HasDerivAt (fun φ : ℝ => Complex.I * m * (φ : ℂ)) (Complex.I * m * 1) φ :=
      (hasDerivAt_id φ).ofReal_comp.const_mul _
    have h2 := (h1.cexp).div_const ((Real.sqrt (2 * π) : ℝ) : ℂ)
    convert h2 using 1
    simp only [ψ]; ring
  have hns : ∀ φ : ℝ, Complex.normSq (ψ φ) = 1 / (2 * π) := by
    intro φ
    simp only [ψ]
    rw [Complex.normSq_div, Complex.normSq_ofReal]
    have : Complex.I * m * φ = ((m * φ : ℝ) : ℂ) * Complex.I := by push_cast; ring
    rw [this, Complex.normSq_eq_norm_sq, Complex.norm_exp_ofReal_mul_I]
    rw [Real.mul_self_sqrt (by positivity)]; simp
  refine ⟨hd, fun φ => ?_, fun φ => ?_, ?_⟩
  · convert (hd φ).const_mul (Complex.I * m) using 1
    rw [mul_assoc, ← mul_assoc Complex.I, ← mul_assoc]
    ring_nf; rw [Complex.I_sq]; ring
  · simp only [ψ]
    congr 1
    have : Complex.I * m * ((φ + 2 * π : ℝ) : ℂ) =
        Complex.I * m * φ + (m : ℂ) * (2 * π * Complex.I) := by
      push_cast; ring
    rw [this, Complex.exp_add, Complex.exp_int_mul_two_pi_mul_I, mul_one]
  · simp_rw [hns]
    simp
    field_simp

/-- **Dirichlet eigenfunctions**: `y(x) = √(2/L) sin(nπx/L)` solves
`y'' + (nπ/L)² y = 0`, vanishes at `0` and `L`, and is normalised. -/
theorem dirichlet_eigenfunction (n : ℕ) (hn : 1 ≤ n) {L : ℝ} (hL : 0 < L) :
    let y : ℝ → ℝ := fun x => Real.sqrt (2 / L) * Real.sin (n * π * x / L)
    (∀ x, HasDerivAt (deriv y) (-(n * π / L) ^ 2 * y x) x) ∧ y 0 = 0 ∧ y L = 0 ∧
      ∫ x in (0 : ℝ)..L, y x ^ 2 = 1 := by
  intro y
  set c : ℝ := n * π / L with hc
  have hy : ∀ x, y x = Real.sqrt (2 / L) * Real.sin (c * x) := by
    intro x; simp only [y, c]; ring_nf
  have hdy : ∀ x, HasDerivAt y (Real.sqrt (2 / L) * (Real.cos (c * x) * c)) x := by
    intro x
    have : y = fun x => Real.sqrt (2 / L) * Real.sin (c * x) := funext hy
    rw [this]
    exact (((hasDerivAt_id x).const_mul c).sin.const_mul _).congr_deriv (by simp)
  have hder : deriv y = fun x => Real.sqrt (2 / L) * (Real.cos (c * x) * c) :=
    funext fun x => (hdy x).deriv
  have hcpos : 0 < c := by
    have : (0:ℝ) < n := by exact_mod_cast hn
    positivity
  have hcL : c * L = n * π := by simp only [c]; field_simp
  refine ⟨fun x => ?_, ?_, ?_, ?_⟩
  · rw [hder, hy]
    have := ((((hasDerivAt_id x).const_mul c).cos.mul_const c).const_mul (Real.sqrt (2 / L)))
    convert this using 1; simp; ring
  · simp [y]
  · rw [hy, hcL, Real.sin_nat_mul_pi]; simp
  · simp_rw [hy, mul_pow, Real.sq_sqrt (by positivity : (0:ℝ) ≤ 2 / L)]
    rw [intervalIntegral.integral_const_mul,
      intervalIntegral.integral_comp_mul_left (fun x => Real.sin x ^ 2) hcpos.ne',
      integral_sin_sq]
    rw [mul_zero, hcL, Real.sin_nat_mul_pi]
    simp
    field_simp
    simp only [c]; field_simp

/-! ## 9. The diagonal argument -/

/-- **Lawvere's fixed point theorem**: if `e : A → (A → B)` is onto, every
`f : B → B` has a fixed point. -/
theorem lawvere_fixed_point {A B : Type*} (e : A → A → B)
    (he : Function.Surjective e) (f : B → B) : ∃ b, f b = b := by
  obtain ⟨a, ha⟩ := he fun a => f (e a a)
  exact ⟨e a a, by conv_rhs => rw [ha]⟩

/-- **Tarski's undefinability theorem**, in general form: in any
interpretation with substitution of codes `sub`, negation of formulas, and
the diagonal property (every formula `φ` has a sentence `d` with
`d ↔ φ(#d)`), no formula `τ` defines truth (`τ(#s) ↔ s` for all `s`). -/
theorem tarski_undefinability {Sent Form : Type*} (True' : Sent → Prop)
    (sub : Form → Sent → Sent) (neg : Form → Form)
    (hneg : ∀ φ s, True' (sub (neg φ) s) ↔ ¬ True' (sub φ s))
    (hdiag : ∀ φ, ∃ d, True' d ↔ True' (sub φ d)) :
    ¬ ∃ τ : Form, ∀ s, True' (sub τ s) ↔ True' s := by
  rintro ⟨τ, hτ⟩
  obtain ⟨d, hd⟩ := hdiag (neg τ)
  rw [hneg, hτ] at hd
  tauto

/-! ## 10. Compactness -/

open FirstOrder FirstOrder.Language Cardinal in
/-- **A theory with arbitrarily large finite models has an infinite model**
(from the compactness theorem,
`FirstOrder.Language.Theory.isSatisfiable_iff_isFinitelySatisfiable`). -/
theorem infinite_model_of_large_finite_models {L : FirstOrder.Language.{u, v}}
    (T : L.Theory)
    (h : ∀ n : ℕ, ∃ M : Theory.ModelType.{u, v, max u v} T, Finite M ∧ n ≤ Nat.card M) :
    ∃ M : Theory.ModelType.{u, v, max u v} T, Infinite M := by
  let S : ℕ → L.Theory := fun N => T ∪ Sentence.cardGe L '' {n | n ≤ N}
  have hdir : Directed (· ⊆ ·) S := by
    apply Monotone.directed_le
    intro a b hab
    exact Set.union_subset_union_right _ (Set.image_mono fun n (hn : n ≤ a) => le_trans hn hab)
  have hS : ∀ N, (S N).IsSatisfiable := by
    intro N
    obtain ⟨M, hfin, hcard⟩ := h N
    have hM : M ⊨ S N := by
      rw [Theory.model_union_iff]
      refine ⟨M.is_model, ?_⟩
      rw [Theory.model_iff]
      rintro _ ⟨n, hn, rfl⟩
      rw [Sentence.realize_cardGe]
      have : (Nat.card M : Cardinal) = #M := Nat.cast_card
      rw [← this]; exact_mod_cast le_trans hn hcard
    exact ⟨hM.bundled⟩
  have hU : (⋃ N, S N) = T ∪ L.infiniteTheory := by
    ext φ
    simp only [S, Set.mem_iUnion, Set.mem_union, Set.mem_image, Set.mem_setOf_eq,
      Language.infiniteTheory, Set.mem_range]
    constructor
    · rintro ⟨N, h | ⟨n, -, rfl⟩⟩
      · exact Or.inl h
      · exact Or.inr ⟨n, rfl⟩
    · rintro (h | ⟨n, rfl⟩)
      · exact ⟨0, Or.inl h⟩
      · exact ⟨n, Or.inr ⟨n, le_rfl, rfl⟩⟩
  have hsat : (T ∪ L.infiniteTheory).IsSatisfiable := by
    rw [← hU]; exact (Theory.isSatisfiable_directed_union_iff hdir).2 hS
  obtain ⟨M⟩ := hsat
  have hT : M ⊨ T := M.is_model.mono Set.subset_union_left
  have hI : M ⊨ L.infiniteTheory := M.is_model.mono Set.subset_union_right
  exact ⟨hT.bundled, (L.model_infiniteTheory_iff).1 hI⟩

end GLM.DerivationsTwo
