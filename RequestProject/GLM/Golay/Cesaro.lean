/-
# Cesàro convergence of the perturbation chain

`Golay/Dynamics.lean` settles the negative half of the self-organised-criticality
question and leaves exactly one thing open.  The perturb-only chain on cosets
is *periodic* — every parity-check column has odd parity, so `step^[n] μ` hops
between the two parity classes and can never converge (`iterate_dirac_ne_unif`).
The correct dynamical statement is therefore about the **time averages**:

  `cesaro μ N f = (1 / N) ∑_{n < N} (step^[n] μ) f  →  1 / 4096`.

This file proves it, with an explicit rate: for every probability law `μ`,
every syndrome `f` and every `N ≥ 1`,

  `|cesaro μ N f - 1/4096| ≤ 24 / N`   (`cesaro_converges`).

Everything is exact rational arithmetic; no limit of real numbers is taken and
no analysis is used in the proof.  The bound *is* the convergence statement,
and `cesaro_tendsto` reads it back as an ordinary `Tendsto` for anyone who
wants it in that form.

## The argument

The chain is a convolution on the group `Syn = (ZMod 2)^12`, so it is
diagonalised by that group's characters, and over `ZMod 2` the characters take
the values `±1` and therefore live in `ℚ`.  For a syndrome `s` put

  `chi s f = (-1)^⟨s, f⟩`,   `hat μ s = ∑_f chi s f * μ f`.

Then `hat` turns `step` into multiplication by the eigenvalue

  `lam s = (1/24) ∑_k chi s (col k)`,

and the whole proof is four facts about that number.

* `lam_zero`: `lam 0 = 1`, because `chi 0` is constantly `1`.  This is the
  eigenvalue of the stationary law and the reason the limit is `1/4096` and
  not `0`.
* `lam_le`: `lam s ≤ 11/12` for `s ≠ 0`.  Some column must fail to be
  orthogonal to `s`, since the columns span every syndrome
  (`exists_word_syn`); one `-1` among twenty-four terms is enough.  So
  `1 - lam s ≥ 1/12`: the chain is *irreducible*, quantitatively.
* `abs_lam_le_one`: `|lam s| ≤ 1`, an average of numbers of modulus one.  It
  is attained at the all-ones syndrome, where `lam s = -1` — that is exactly
  the periodicity `par_col` records, and it is why the Cesàro average and not
  the iterate is what converges.
* `abs_geom_sum_le`: `|∑_{n<N} lam s ^ n| = |(1 - lam s ^ N)/(1 - lam s)| ≤
  2 / (1/12) = 24`.  A bounded partial sum divided by `N` tends to zero, and
  the `24` in the headline bound is this `24`.

Fourier inversion (`inversion`) turns the `4095` non-trivial coefficients back
into a bound on `cesaro μ N f - 1/4096`, and `abs_hat_le_one` does the rest.

The argument is self-contained: the orthogonality relation it needs
(`sum_chi`) is proved here from the character property, not imported.
-/
import RequestProject.GLM.Golay.Dynamics

namespace GLM.Golay24

open Finset

/-! ## Arithmetic in `ZMod 2`, and reindexing a sum over syndromes -/

theorem zmod2_eq_one_of_ne_zero {x : ZMod 2} (h : x ≠ 0) : x = 1 := by
  revert h; revert x; decide

theorem syn_add_self (a b : Syn) : a + b + b = a := by
  funext i
  have h : ∀ x y : ZMod 2, x + y + y = x := by decide
  exact h (a i) (b i)

/-- Translating the index of a sum over the whole syndrome group changes
nothing. -/
theorem sum_shift (c : Syn) (F : Syn → ℚ) :
    ∑ f : Syn, F (f + c) = ∑ f : Syn, F f :=
  Fintype.sum_equiv (Equiv.addRight c) _ _ (fun _ => rfl)

/-! ## Characters of the syndrome group -/

/-- The `F₂` inner product of two syndromes. -/
def ip (s f : Syn) : ZMod 2 := ∑ i : Fin 12, s i * f i

/-- The character `chi s f = (-1)^⟨s, f⟩`, valued in `ℚ`.  Over `ZMod 2` the
characters are real — indeed rational — which is what lets the whole argument
stay inside exact arithmetic. -/
def chi (s f : Syn) : ℚ := if ip s f = 0 then 1 else -1

theorem ip_comm (s f : Syn) : ip s f = ip f s := by
  simp only [ip]
  exact Finset.sum_congr rfl (fun i _ => mul_comm _ _)

theorem ip_add_right (s f g : Syn) : ip s (f + g) = ip s f + ip s g := by
  simp only [ip, Pi.add_apply, mul_add]
  exact Finset.sum_add_distrib

theorem ip_zero_left (f : Syn) : ip 0 f = 0 := by simp [ip]

theorem chi_zero_left (f : Syn) : chi 0 f = 1 := by simp [chi, ip_zero_left]

theorem chi_zero_right (s : Syn) : chi s 0 = 1 := by simp [chi, ip]

/-- A character is multiplicative in its second argument. -/
theorem chi_add (s f g : Syn) : chi s (f + g) = chi s f * chi s g := by
  simp only [chi, ip_add_right]
  rcases eq_or_ne (ip s f) 0 with hf | hf <;>
    rcases eq_or_ne (ip s g) 0 with hg | hg
  · simp [hf, hg]
  · simp [hf, hg]
  · simp [hf, hg]
  · rw [zmod2_eq_one_of_ne_zero hf, zmod2_eq_one_of_ne_zero hg,
      show (1 : ZMod 2) + 1 = 0 from by decide]
    norm_num

theorem chi_eq_one_or (s f : Syn) : chi s f = 1 ∨ chi s f = -1 := by
  unfold chi; split <;> simp

theorem abs_chi (s f : Syn) : |chi s f| = 1 := by
  rcases chi_eq_one_or s f with h | h <;> simp [h]

theorem chi_le_one (s f : Syn) : chi s f ≤ 1 := by
  rcases chi_eq_one_or s f with h | h <;> simp [h]

/-- A nonzero syndrome is detected by some character. -/
theorem exists_ip_ne_zero {f : Syn} (hf : f ≠ 0) : ∃ s : Syn, ip s f = 1 := by
  obtain ⟨i, hi⟩ : ∃ i : Fin 12, f i ≠ 0 := by
    by_contra h
    push_neg at h
    exact hf (funext fun i => h i)
  exact ⟨fun j => if j = i then 1 else 0, by
    simp [ip, Finset.sum_ite_eq' Finset.univ i, zmod2_eq_one_of_ne_zero hi]⟩

/-- **Orthogonality.**  Summed over all `4096` characters, `chi s f` is `4096`
when `f = 0` and `0` otherwise. -/
theorem sum_chi (f : Syn) :
    ∑ s : Syn, chi s f = if f = 0 then (4096 : ℚ) else 0 := by
  classical
  by_cases hf : f = 0
  · subst hf
    simp [chi_zero_right, Finset.card_univ]
  · simp only [hf, if_false]
    obtain ⟨s₀, hs₀⟩ := exists_ip_ne_zero hf
    have hchi : ∀ s : Syn, chi (s + s₀) f = - chi s f := by
      intro s
      have hip : ip (s + s₀) f = ip s f + 1 := by
        rw [ip_comm, ip_add_right, ip_comm f s, ip_comm f s₀, hs₀]
      simp only [chi, hip]
      rcases eq_or_ne (ip s f) 0 with h | h
      · simp [h]
      · rw [zmod2_eq_one_of_ne_zero h, show (1 : ZMod 2) + 1 = 0 from by decide]
        norm_num
    have hbij : ∑ s : Syn, chi (s + s₀) f = ∑ s : Syn, chi s f :=
      sum_shift s₀ (fun s => chi s f)
    have hneg : ∑ s : Syn, chi s f = - ∑ s : Syn, chi s f := by
      calc ∑ s : Syn, chi s f = ∑ s : Syn, chi (s + s₀) f := hbij.symm
        _ = ∑ s : Syn, -chi s f := Finset.sum_congr rfl (fun s _ => hchi s)
        _ = - ∑ s : Syn, chi s f := by simp
    linarith

/-! ## The Fourier transform of a law -/

/-- The Fourier coefficient of a law at a character. -/
def hat (μ : Law) (s : Syn) : ℚ := ∑ f : Syn, chi s f * μ f

/-- **Fourier inversion.** -/
theorem inversion (μ : Law) (f : Syn) :
    (4096 : ℚ) * μ f = ∑ s : Syn, chi s f * hat μ s := by
  classical
  have hswap : ∑ s : Syn, chi s f * hat μ s
      = ∑ g : Syn, (∑ s : Syn, chi s (f + g)) * μ g := by
    simp only [hat, Finset.mul_sum, Finset.sum_mul]
    rw [Finset.sum_comm]
    refine Finset.sum_congr rfl (fun g _ => ?_)
    refine Finset.sum_congr rfl (fun s _ => ?_)
    rw [chi_add]; ring
  rw [hswap]
  have hpt : ∀ g : Syn, (∑ s : Syn, chi s (f + g)) * μ g
      = if g = f then 4096 * μ f else 0 := by
    intro g
    rw [sum_chi]
    by_cases hg : g = f
    · subst hg
      have hzero : g + g = (0 : Syn) := by
        funext i
        have h : ∀ x : ZMod 2, x + x = 0 := by decide
        exact h (g i)
      simp [hzero]
    · have hne : f + g ≠ 0 := by
        intro h
        refine hg (funext fun i => ?_)
        have hi : f i + g i = 0 := congrFun h i
        have h2 : ∀ x y : ZMod 2, x + y = 0 → y = x := by decide
        exact h2 _ _ hi
      simp [hne, hg]
  rw [Finset.sum_congr rfl (fun g _ => hpt g)]
  simp

theorem hat_zero_of_isProb {μ : Law} (hp : IsProb μ) : hat μ 0 = 1 := by
  simp [hat, chi_zero_left, hp.total]

/-- `|hat μ s| ≤ 1` for a probability law: an average of numbers of
modulus one. -/
theorem abs_hat_le_one {μ : Law} (hp : IsProb μ) (s : Syn) : |hat μ s| ≤ 1 := by
  calc |hat μ s| ≤ ∑ f : Syn, |chi s f * μ f| := Finset.abs_sum_le_sum_abs _ _
    _ = ∑ f : Syn, μ f := by
        refine Finset.sum_congr rfl (fun f _ => ?_)
        rw [abs_mul, abs_chi, one_mul, abs_of_nonneg (hp.nonneg f)]
    _ = 1 := hp.total

/-! ## The eigenvalues -/

/-- The eigenvalue of `step` at the character `chi s`. -/
def lam (s : Syn) : ℚ := (∑ k : Fin 24, chi s (col k)) / 24

theorem lam_zero : lam 0 = 1 := by
  simp [lam, chi_zero_left]

theorem abs_lam_le_one (s : Syn) : |lam s| ≤ 1 := by
  have h : |∑ k : Fin 24, chi s (col k)| ≤ 24 :=
    calc |∑ k : Fin 24, chi s (col k)| ≤ ∑ k : Fin 24, |chi s (col k)| :=
          Finset.abs_sum_le_sum_abs _ _
      _ = 24 := by simp [abs_chi]
  rw [lam, abs_div, abs_of_nonneg (by norm_num : (0:ℚ) ≤ 24)]
  rw [div_le_one (by norm_num)]
  exact h

/-- The inner product of a syndrome with the syndrome of a word is the sum of
its inner products with the columns the word selects. -/
theorem ip_syn (s : Syn) (u : Word) :
    ip s (syn u) = ∑ k ∈ u, ip s (col k) := by
  classical
  induction u using Finset.induction with
  | empty => simp [syn, ip]
  | insert k t hk ih =>
      have hstep : syn (insert k t) = col k + syn t := by
        simp [syn, Finset.sum_insert hk]
      rw [hstep, ip_add_right, ih, Finset.sum_insert hk]

/-- **Quantitative irreducibility.**  A nonzero syndrome is not orthogonal to
every column, because the columns span the whole syndrome group. -/
theorem exists_col_ip {s : Syn} (hs : s ≠ 0) :
    ∃ k : Fin 24, ip s (col k) = 1 := by
  classical
  obtain ⟨t, ht⟩ := exists_ip_ne_zero hs
  have hst : ip s t = 1 := by rw [ip_comm]; exact ht
  obtain ⟨u, -, hu⟩ := exists_word_syn t
  by_contra hno
  push_neg at hno
  have hzero : ∀ k : Fin 24, ip s (col k) = 0 := by
    intro k
    rcases eq_or_ne (ip s (col k)) 0 with h | h
    · exact h
    · exact absurd (zmod2_eq_one_of_ne_zero h) (hno k)
  have : ip s t = 0 := by
    rw [← hu, ip_syn]
    simp [hzero]
  rw [this] at hst
  exact absurd hst (by decide)

theorem lam_le {s : Syn} (hs : s ≠ 0) : lam s ≤ 11 / 12 := by
  classical
  obtain ⟨k₀, hk₀⟩ := exists_col_ip hs
  have hneg : chi s (col k₀) = -1 := by simp [chi, hk₀]
  have hsum : ∑ k : Fin 24, chi s (col k) ≤ 22 := by
    have hsplit : ∑ k : Fin 24, chi s (col k)
        = chi s (col k₀) + ∑ k ∈ univ.erase k₀, chi s (col k) :=
      (Finset.add_sum_erase _ _ (Finset.mem_univ k₀)).symm
    have hrest : ∑ k ∈ univ.erase k₀, chi s (col k) ≤ 23 :=
      calc ∑ k ∈ univ.erase k₀, chi s (col k)
          ≤ ∑ _k ∈ univ.erase k₀, (1 : ℚ) :=
            Finset.sum_le_sum (fun k _ => chi_le_one s (col k))
        _ = 23 := by
            simp [Finset.card_erase_of_mem, Finset.card_univ]
    rw [hsplit, hneg]
    linarith
  rw [lam, div_le_iff₀ (by norm_num : (0:ℚ) < 24)]
  linarith

theorem one_sub_lam_ge {s : Syn} (hs : s ≠ 0) : (1 : ℚ) / 12 ≤ 1 - lam s := by
  have := lam_le hs
  linarith

/-! ## `step` is diagonal in the character basis -/

theorem hat_step (μ : Law) (s : Syn) : hat (step μ) s = lam s * hat μ s := by
  classical
  have hshift : ∀ k : Fin 24,
      ∑ f : Syn, chi s f * μ (f + col k) = chi s (col k) * hat μ s := by
    intro k
    have hre := sum_shift (col k) (fun y : Syn => chi s (y + col k) * μ y)
    simp only [syn_add_self] at hre
    rw [hre, hat, Finset.mul_sum]
    exact Finset.sum_congr rfl (fun g _ => by rw [chi_add]; ring)
  have hnum : ∑ f : Syn, chi s f * ∑ k : Fin 24, μ (f + col k)
      = (∑ k : Fin 24, chi s (col k)) * hat μ s :=
    calc ∑ f : Syn, chi s f * ∑ k : Fin 24, μ (f + col k)
        = ∑ f : Syn, ∑ k : Fin 24, chi s f * μ (f + col k) :=
          Finset.sum_congr rfl (fun f _ => by rw [Finset.mul_sum])
      _ = ∑ k : Fin 24, ∑ f : Syn, chi s f * μ (f + col k) := Finset.sum_comm
      _ = ∑ k : Fin 24, chi s (col k) * hat μ s :=
          Finset.sum_congr rfl (fun k _ => hshift k)
      _ = (∑ k : Fin 24, chi s (col k)) * hat μ s := by rw [Finset.sum_mul]
  have hdiv : hat (step μ) s
      = (∑ f : Syn, chi s f * ∑ k : Fin 24, μ (f + col k)) / 24 := by
    rw [Finset.sum_div]
    simp only [hat, step, mul_div_assoc]
  rw [hdiv, hnum, lam, div_mul_eq_mul_div]

theorem hat_iterate (μ : Law) (s : Syn) (n : ℕ) :
    hat (step^[n] μ) s = lam s ^ n * hat μ s := by
  induction n with
  | zero => simp
  | succ n ih =>
      rw [Function.iterate_succ_apply', hat_step, ih]
      ring

/-! ## The Cesàro average -/

/-- The time average of the first `N` laws of the chain. -/
def cesaro (μ : Law) (N : ℕ) : Law :=
  fun f => (∑ n ∈ range N, (step^[n] μ) f) / N

theorem hat_cesaro (μ : Law) (s : Syn) (N : ℕ) :
    hat (cesaro μ N) s = ((∑ n ∈ range N, lam s ^ n) * hat μ s) / N := by
  classical
  have hnum : ∑ f : Syn, chi s f * ∑ n ∈ range N, (step^[n] μ) f
      = (∑ n ∈ range N, lam s ^ n) * hat μ s :=
    calc ∑ f : Syn, chi s f * ∑ n ∈ range N, (step^[n] μ) f
        = ∑ f : Syn, ∑ n ∈ range N, chi s f * (step^[n] μ) f :=
          Finset.sum_congr rfl (fun f _ => by rw [Finset.mul_sum])
      _ = ∑ n ∈ range N, ∑ f : Syn, chi s f * (step^[n] μ) f := Finset.sum_comm
      _ = ∑ n ∈ range N, lam s ^ n * hat μ s :=
          Finset.sum_congr rfl (fun n _ => hat_iterate μ s n)
      _ = (∑ n ∈ range N, lam s ^ n) * hat μ s := by rw [Finset.sum_mul]
  have hdiv : hat (cesaro μ N) s
      = (∑ f : Syn, chi s f * ∑ n ∈ range N, (step^[n] μ) f) / N := by
    rw [Finset.sum_div]
    simp only [hat, cesaro, mul_div_assoc]
  rw [hdiv, hnum]

/-- The partial sums of a geometric series whose ratio has modulus at most one
and is bounded above by `11/12` never exceed `24` in modulus, uniformly in
`N`.  This is the whole content of "the Cesàro average converges": the
numerator does not grow, so dividing by `N` sends it to zero. -/
theorem abs_geom_sum_le {r : ℚ} (h1 : |r| ≤ 1) (h2 : r ≤ 11 / 12) (N : ℕ) :
    |∑ n ∈ range N, r ^ n| ≤ 24 := by
  have hne : r ≠ 1 := by intro h; rw [h] at h2; norm_num at h2
  rw [geom_sum_eq hne]
  have hdenpos : (0 : ℚ) < 1 - r := by linarith
  have hpow : |r ^ N| ≤ 1 := by
    rw [abs_pow]
    exact pow_le_one₀ (abs_nonneg r) h1
  rw [abs_le] at hpow
  have hnum : |1 - r ^ N| ≤ 2 := by
    rw [abs_le]
    constructor <;> linarith [hpow.1, hpow.2]
  have hnum' : |r ^ N - 1| ≤ 2 := by rwa [abs_sub_comm]
  rw [abs_div, abs_sub_comm r 1, abs_of_pos hdenpos, div_le_iff₀ hdenpos]
  nlinarith

/-- **Cesàro convergence, with a rate.**  For every probability law, every
syndrome and every `N ≥ 1`, the time average of the perturbation chain is
within `24 / N` of the uniform law.  In particular the time averages converge
to uniform, which is the statement `Dynamics.lean` recorded as open: the
iterates themselves cannot converge, because the chain is periodic. -/
theorem cesaro_converges {μ : Law} (hp : IsProb μ) (f : Syn) {N : ℕ}
    (hN : 0 < N) : |cesaro μ N f - 1 / 4096| ≤ 24 / N := by
  classical
  have hNQ : (0 : ℚ) < (N : ℚ) := by exact_mod_cast hN
  -- the trivial character contributes exactly `1`, whatever `N` is
  have hlam0 : ∑ n ∈ range N, lam 0 ^ n = (N : ℚ) := by
    simp [lam_zero]
  have hhat0 : hat (cesaro μ N) 0 = 1 := by
    rw [hat_cesaro, hlam0, hat_zero_of_isProb hp, mul_one,
      div_self (ne_of_gt hNQ)]
  -- every other character contributes at most `24 / N` in modulus
  have hbound : ∀ s : Syn, s ≠ 0 → |hat (cesaro μ N) s| ≤ 24 / N := by
    intro s hs
    rw [hat_cesaro, abs_div, abs_of_pos hNQ]
    have hg := abs_geom_sum_le (abs_lam_le_one s) (lam_le hs) N
    have hh := abs_hat_le_one hp s
    have hnum : |(∑ n ∈ range N, lam s ^ n) * hat μ s| ≤ 24 := by
      rw [abs_mul]
      calc |∑ n ∈ range N, lam s ^ n| * |hat μ s|
          ≤ 24 * |hat μ s| := mul_le_mul_of_nonneg_right hg (abs_nonneg _)
        _ ≤ 24 * 1 := mul_le_mul_of_nonneg_left hh (by norm_num)
        _ = 24 := by ring
    exact (div_le_div_iff_of_pos_right hNQ).mpr hnum
  -- Fourier inversion, with the trivial character split off
  have hinv := inversion (cesaro μ N) f
  have hsplit : ∑ s : Syn, chi s f * hat (cesaro μ N) s
      = 1 + ∑ s ∈ univ.erase (0 : Syn), chi s f * hat (cesaro μ N) s := by
    rw [← Finset.add_sum_erase _ _ (Finset.mem_univ (0 : Syn))]
    congr 1
    rw [hhat0, mul_one, chi_zero_left]
  have htail : |∑ s ∈ univ.erase (0 : Syn), chi s f * hat (cesaro μ N) s|
      ≤ 4095 * (24 / N) :=
    calc |∑ s ∈ univ.erase (0 : Syn), chi s f * hat (cesaro μ N) s|
        ≤ ∑ s ∈ univ.erase (0 : Syn), |chi s f * hat (cesaro μ N) s| :=
          Finset.abs_sum_le_sum_abs _ _
      _ ≤ ∑ _s ∈ univ.erase (0 : Syn), (24 / (N : ℚ)) := by
          refine Finset.sum_le_sum (fun s hs => ?_)
          rw [abs_mul, abs_chi, one_mul]
          exact hbound s (Finset.ne_of_mem_erase hs)
      _ = 4095 * (24 / N) := by
          rw [Finset.sum_const, Finset.card_erase_of_mem (Finset.mem_univ _),
            Finset.card_univ]
          norm_num
  have hval : (4096 : ℚ) * (cesaro μ N f - 1 / 4096)
      = ∑ s ∈ univ.erase (0 : Syn), chi s f * hat (cesaro μ N) s := by
    rw [mul_sub, hinv, hsplit]; norm_num
  have habs : (4096 : ℚ) * |cesaro μ N f - 1 / 4096| ≤ 4095 * (24 / N) :=
    calc (4096 : ℚ) * |cesaro μ N f - 1 / 4096|
        = |(4096 : ℚ) * (cesaro μ N f - 1 / 4096)| := by
          rw [abs_mul, abs_of_nonneg (by norm_num : (0:ℚ) ≤ 4096)]
      _ = |∑ s ∈ univ.erase (0 : Syn), chi s f * hat (cesaro μ N) s| := by
          rw [hval]
      _ ≤ 4095 * (24 / N) := htail
  have h24 : (0 : ℚ) < 24 / N := by positivity
  linarith

/-- The same statement read as an ordinary limit of real numbers. -/
theorem cesaro_tendsto {μ : Law} (hp : IsProb μ) (f : Syn) :
    Filter.Tendsto (fun N : ℕ => ((cesaro μ N f : ℚ) : ℝ)) Filter.atTop
      (nhds ((1 : ℝ) / 4096)) := by
  rw [Metric.tendsto_atTop]
  intro ε hε
  obtain ⟨M, hM⟩ := exists_nat_gt (24 / ε)
  refine ⟨max M 1, fun N hN => ?_⟩
  have hN1 : 0 < N :=
    lt_of_lt_of_le Nat.zero_lt_one (le_trans (le_max_right M 1) hN)
  have hNR : (0 : ℝ) < (N : ℝ) := by exact_mod_cast hN1
  have hMN : (M : ℝ) ≤ (N : ℝ) := by
    exact_mod_cast le_trans (le_max_left M 1) hN
  have hlt : (24 : ℝ) / (N : ℝ) < ε := by
    have h1 : (24 : ℝ) / ε < (N : ℝ) := lt_of_lt_of_le hM hMN
    rw [div_lt_iff₀ hε] at h1
    rw [div_lt_iff₀ hNR]
    linarith
  have hb := cesaro_converges hp f hN1
  have hbR : |((cesaro μ N f : ℚ) : ℝ) - 1 / 4096| ≤ 24 / (N : ℝ) := by
    have hcast : ((|cesaro μ N f - 1 / 4096| : ℚ) : ℝ)
        ≤ ((24 / (N : ℚ) : ℚ) : ℝ) := by exact_mod_cast hb
    push_cast at hcast
    exact hcast
  rw [Real.dist_eq]
  exact lt_of_le_of_lt hbR hlt

end GLM.Golay24
