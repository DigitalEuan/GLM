/-
# Every Leech shell, counted and proved (Phase 180)

*Created 22 October 2026.*

The formal half of `studies/LEECH_SHELL_COUNT_STUDY.md`. Phase 164
(`LeechShells.lean`) defined the Leech lattice (`IsLeech`, Conway's
construction from the Golay code, coordinates scaled by `√8`) and ran a
counting procedure: for each codeword weight, the one-coordinate generating
functions in (squared value, value mod 8) raised to the weight and the
co-weight, the coefficient at `(16t, 4m)` read off, weighted by the census
`1, 759, 2576, 759, 1`. That the procedure counts lattice vectors was argued
(the count on a codeword depends only on its weight), not proved. Phase 165
(`LeechKissing.lean`) proved the count for the minimal shell only, by an
explicit bijection. This file proves the procedure correct for **every** `t`.

* `GF` — generating functions with exponents in `ℕ × ZMod 8`, as Mathlib's
  `AddMonoidAlgebra`; `gfOne r B` is the class `r (mod 4)` in `[-B, B]`.
* `coeff_prod` — the product of the per-coordinate generating functions
  counts vectors: its coefficient at `p` is the number of vectors whose
  coordinates lie in their classes with exponent sum `p`.
* `prod_pattern` — the product over a pattern `c` depends only on `|c|`:
  `gfOne a ^ |c| * gfOne b ^ (24 − |c|)`. This is the study's argument.
* `card_shellSet`, `card_fib`, `sum_codewords`, `shell_card_gf` — the shell of
  squared length `16t` splits over the parity `m` and the codeword the
  residues sit on, and sums by weight against the census.
* `oneArr`, `mulArr`, `powArr`, `patternArr`, `shellArr` — the procedure on
  arrays (index `8n + s`, truncated at `16t`); `Rep` says an array holds a
  generating function's coefficients; `rep_one`, `mul_coeff`, `rep_mul`,
  `rep_pow`, `patternArr_eq`.
* `shellArr_correct` — **for every `t`, the number of lattice vectors of
  squared length `16t` is the procedure's count.** `shellFast_correct` — the
  same with the powers shared (the form evaluated below).
* `shellCount_correct` — the Phase 164 procedure itself agrees on `t ≤ 4`, so
  its counts are the lattice's.
* `leech_shell_sizes` — the first eight shells as theorems about the
  definition: `1, 0, 196560, 16773120, 398034000, 4629381120, 34417656000,
  187489935360`.

The proof of correctness uses no computation beyond the Golay census of
`GolayWeightEnum.lean`; the shell sizes are `native_decide` evaluations of a
procedure proved correct.
-/
import Mathlib
import RequestProject.GLM.LeechShells

namespace GLM.LeechShellCount

open Finset GLM.Golay24 GLM.LeechShells

/-! ## 1. Generating functions in (squared length, sum mod 8) -/

/-- Generating functions with exponents (squared length, coordinate sum mod 8). -/
abbrev GF := AddMonoidAlgebra ℕ (ℕ × ZMod 8)

/-- The integers of the residue class `r (mod 4)` in `[-B, B]`. -/
def cls (r : ℤ) (B : ℕ) : Finset ℤ := (Icc (-(B : ℤ)) B).filter fun v => v % 4 = r

/-- The exponent of one coordinate value. -/
def expo (v : ℤ) : ℕ × ZMod 8 := (v.natAbs ^ 2, (v : ZMod 8))

/-- The one-coordinate generating function of the class `r (mod 4)`. -/
noncomputable def gfOne (r : ℤ) (B : ℕ) : GF :=
  ∑ v ∈ cls r B, AddMonoidAlgebra.single (expo v) 1

/-- The vectors whose coordinate `i` lies in the class `ρ i`, bounded by `B`. -/
def vecSet (ρ : Fin 24 → ℤ) (B : ℕ) : Finset (Fin 24 → ℤ) :=
  Fintype.piFinset fun i => cls (ρ i) B

/-- The exponent of a vector. -/
def vexpo (y : Fin 24 → ℤ) : ℕ × ZMod 8 := ∑ i, expo (y i)

theorem coeff_prod (ρ : Fin 24 → ℤ) (B : ℕ) (p : ℕ × ZMod 8) :
    (∏ i, gfOne (ρ i) B) p = #((vecSet ρ B).filter fun y => vexpo y = p) := by
  classical
  unfold gfOne
  rw [Finset.prod_univ_sum]
  simp_rw [AddMonoidAlgebra.prod_single, prod_const_one]
  rw [Finsupp.finset_sum_apply, card_filter]
  apply sum_congr rfl
  intro y _
  rw [AddMonoidAlgebra.single_apply]
  rfl

theorem prod_pattern (c : Finset (Fin 24)) (a b : ℤ) (B : ℕ) :
    ∏ i, gfOne (if i ∈ c then a else b) B = gfOne a B ^ c.card * gfOne b B ^ (24 - c.card) := by
  classical
  rw [show (∏ i, gfOne (if i ∈ c then a else b) B) =
      ∏ i, (if i ∈ c then gfOne a B else gfOne b B) from
    prod_congr rfl fun i _ => by split_ifs <;> rfl]
  rw [prod_ite, prod_const, prod_const]
  congr 2
  · simp
  · rw [filter_not, card_sdiff_of_subset (filter_subset _ _)]; simp

/-! ## 2. The Leech shell split over the codewords -/

/-- The residue pattern of parity `m` on the codeword `c`. -/
def pat (m : ℕ) (c : Finset (Fin 24)) : Fin 24 → ℤ :=
  fun i => if m = 0 then (if i ∈ c then 2 else 0) else (if i ∈ c then 1 else 3)

/-- The lattice vectors of squared length `16t`, as a finite set. -/
noncomputable def shellSet (t : ℕ) : Finset (Fin 24 → ℤ) := by
  classical
  exact (Fintype.piFinset fun _ => Icc (-((16 * t : ℕ) : ℤ)) (16 * t)).filter
    fun x => IsLeech x ∧ normSq x = 16 * t

theorem bound_of_normSq {x : Fin 24 → ℤ} {t : ℕ} (hn : normSq x = 16 * t) (i : Fin 24) :
    -((16 * t : ℕ) : ℤ) ≤ x i ∧ x i ≤ ((16 * t : ℕ) : ℤ) := by
  have h : x i ^ 2 ≤ 16 * t := by
    rw [← hn, normSq]
    exact single_le_sum (f := fun j => x j ^ 2) (fun j _ => sq_nonneg _) (mem_univ i)
  push_cast
  constructor <;> nlinarith

theorem shellSet_eq (t : ℕ) :
    {x : Fin 24 → ℤ | IsLeech x ∧ normSq x = 16 * t} = ↑(shellSet t) := by
  classical
  ext x
  simp only [Set.mem_setOf_eq, shellSet, coe_filter, Fintype.mem_piFinset, mem_Icc]
  constructor
  · rintro ⟨hL, hn⟩
    refine ⟨fun i => ?_, hL, hn⟩
    exact bound_of_normSq hn i
  · exact fun h => h.2

/-- The vectors of parity `m` on the codeword `c` with squared length `16t`. -/
noncomputable def fib (m t : ℕ) (c : Finset (Fin 24)) : Finset (Fin 24 → ℤ) :=
  (vecSet (pat m c) (16 * t)).filter fun y => vexpo y = (16 * t, ((4 * m : ℕ) : ZMod 8))

theorem vexpo_eq (x : Fin 24 → ℤ) (t : ℕ) (s : ZMod 8) :
    vexpo x = (16 * t, s) ↔ normSq x = 16 * t ∧ ((∑ i, x i : ℤ) : ZMod 8) = s := by
  have hcast : ((∑ i, (x i).natAbs ^ 2 : ℕ) : ℤ) = normSq x := by
    push_cast [normSq]; simp [sq_abs]
  simp only [vexpo, expo, Prod.ext_iff, Prod.fst_sum, Prod.snd_sum, Int.cast_sum]
  constructor
  · rintro ⟨h1, h2⟩; exact ⟨by rw [← hcast, h1]; push_cast; ring, h2⟩
  · rintro ⟨h1, h2⟩; refine ⟨?_, h2⟩
    have : ((∑ i, (x i).natAbs ^ 2 : ℕ) : ℤ) = ((16 * t : ℕ) : ℤ) := by
      rw [hcast, h1]; push_cast; ring
    exact_mod_cast this

theorem cast_sum_iff (S : ℤ) (m : ℕ) (hm : m < 2) :
    (S : ZMod 8) = ((4 * m : ℕ) : ZMod 8) ↔ S % 8 = 4 * m := by
  have : ((4 * m : ℕ) : ZMod 8) = ((4 * m : ℤ) : ZMod 8) := by push_cast; rfl
  rw [this, ZMod.intCast_eq_intCast_iff']
  interval_cases m <;> simp

theorem isLeech_iff (x : Fin 24 → ℤ) :
    IsLeech x ↔ ∃ m < 2, ∃ c ∈ codewords, (∀ i, x i % 4 = pat m c i) ∧
      ((∑ i, x i : ℤ) : ZMod 8) = ((4 * m : ℕ) : ZMod 8) := by
  constructor
  · rintro (⟨hev, hc, hs⟩ | ⟨hod, hc, hs⟩)
    · refine ⟨0, by norm_num, _, mem_codewords.2 hc, fun i => ?_, (cast_sum_iff _ 0 (by norm_num)).2 hs⟩
      have := hev i
      by_cases h : x i % 4 = 2 <;> simp [pat, h]
      omega
    · refine ⟨1, by norm_num, _, mem_codewords.2 hc, fun i => ?_, (cast_sum_iff _ 1 (by norm_num)).2 hs⟩
      have := hod i
      by_cases h : x i % 4 = 1 <;> simp [pat, h]
      omega
  · rintro ⟨m, hm, c, hc, hp, hs⟩
    rw [cast_sum_iff _ m hm] at hs
    have hc' := mem_codewords.1 hc
    interval_cases m
    · left
      have hkey : (univ.filter fun i => x i % 4 = 2) = c := by
        ext i; have := hp i; by_cases h : i ∈ c <;> simp [pat, h] at this ⊢ <;> omega
      refine ⟨fun i => ?_, hkey ▸ hc', by simpa using hs⟩
      have := hp i; by_cases h : i ∈ c <;> simp [pat, h] at this <;> omega
    · right
      have hkey : (univ.filter fun i => x i % 4 = 1) = c := by
        ext i; have := hp i; by_cases h : i ∈ c <;> simp [pat, h] at this ⊢ <;> omega
      refine ⟨fun i => ?_, hkey ▸ hc', by simpa using hs⟩
      have := hp i; by_cases h : i ∈ c <;> simp [pat, h] at this <;> omega

theorem pat_inj {m m' : ℕ} (hm : m < 2) (hm' : m' < 2) {c c' : Finset (Fin 24)}
    (h : ∀ i, pat m c i = pat m' c' i) : m = m' ∧ c = c' := by
  have h0 := h 0
  have hmm : m = m' := by
    clear h
    interval_cases m <;> interval_cases m' <;> simp only [pat] at h0 <;> split_ifs at h0 <;>
      first | rfl | omega | contradiction
  subst hmm
  refine ⟨rfl, ?_⟩
  ext i
  have := h i
  interval_cases m <;> by_cases hi : i ∈ c <;> by_cases hi' : i ∈ c' <;> simp [pat, hi, hi'] at this ⊢

theorem mem_fib {m t : ℕ} {c : Finset (Fin 24)} {x : Fin 24 → ℤ} :
    x ∈ fib m t c ↔ (∀ i, -((16 * t : ℕ) : ℤ) ≤ x i ∧ x i ≤ ((16 * t : ℕ) : ℤ)) ∧
      (∀ i, x i % 4 = pat m c i) ∧ normSq x = 16 * t ∧
        ((∑ i, x i : ℤ) : ZMod 8) = ((4 * m : ℕ) : ZMod 8) := by
  simp only [fib, vecSet, cls, mem_filter, Fintype.mem_piFinset, mem_Icc, vexpo_eq]
  constructor
  · rintro ⟨h1, h2, h3⟩; exact ⟨fun i => (h1 i).1, fun i => (h1 i).2, h2, h3⟩
  · rintro ⟨h1, h2, h3, h4⟩; exact ⟨fun i => ⟨h1 i, h2 i⟩, h3, h4⟩

theorem card_shellSet (t : ℕ) :
    #(shellSet t) = ∑ c ∈ codewords, (#(fib 0 t c) + #(fib 1 t c)) := by
  classical
  have hset : shellSet t = (range 2 ×ˢ codewords).biUnion (fun p => fib p.1 t p.2) := by
    ext x
    simp only [shellSet, mem_filter, Fintype.mem_piFinset, mem_Icc, mem_biUnion, mem_product,
      mem_range, Prod.exists, mem_fib, isLeech_iff]
    constructor
    · rintro ⟨hb, ⟨m, hm, c, hc, hp, hs⟩, hn⟩
      exact ⟨m, c, ⟨hm, hc⟩, hb, hp, hn, hs⟩
    · rintro ⟨m, c, ⟨hm, hc⟩, hb, hp, hn, hs⟩
      exact ⟨hb, ⟨m, hm, c, hc, hp, hs⟩, hn⟩
  rw [hset, card_biUnion, sum_product, sum_range_succ, sum_range_succ, sum_range_zero,
    zero_add, ← sum_add_distrib]
  rintro ⟨m, c⟩ hp ⟨m', c'⟩ hp' hne
  simp only [coe_product, Set.mem_prod, coe_range, Set.mem_Iio, mem_coe] at hp hp'
  simp only [Function.onFun]
  rw [Finset.disjoint_left]
  intro x hx hx'
  rw [mem_fib] at hx hx'
  obtain ⟨h1, h2⟩ := pat_inj hp.1 hp'.1 (fun i => (hx.2.1 i).symm.trans (hx'.2.1 i))
  exact hne (by simp [h1, h2])

/-- The number of vectors of squared length `16t` and parity `m` on one
codeword of weight `w`, as a coefficient of a generating function. -/
noncomputable def patternGF (m w t : ℕ) : ℕ :=
  ((if m = 0 then gfOne 2 (16 * t) else gfOne 1 (16 * t)) ^ w *
    (if m = 0 then gfOne 0 (16 * t) else gfOne 3 (16 * t)) ^ (24 - w))
    (16 * t, ((4 * m : ℕ) : ZMod 8))

theorem card_fib (m t : ℕ) (c : Finset (Fin 24)) : #(fib m t c) = patternGF m c.card t := by
  rw [fib, ← coeff_prod, patternGF]
  by_cases hm : m = 0
  · have : pat m c = fun i => if i ∈ c then 2 else 0 := by funext i; simp [pat, hm]
    rw [this, prod_pattern]; simp [hm]
  · have : pat m c = fun i => if i ∈ c then 1 else 3 := by funext i; simp [pat, hm]
    rw [this, prod_pattern]; simp [hm]

theorem sum_by_weight (s : Finset (Finset (Fin 24)))
    (hs : ∀ c ∈ s, c.card = 0 ∨ c.card = 8 ∨ c.card = 12 ∨ c.card = 16 ∨ c.card = 24)
    (F cen : ℕ → ℕ) (hcen : ∀ w, cen w = #(s.filter fun c => wt c = w)) :
    ∑ c ∈ s, F c.card = ([0, 8, 12, 16, 24].map fun w => cen w * F w).sum := by
  rw [← sum_fiberwise_of_maps_to (s := s) (t := {0, 8, 12, 16, 24}) (g := wt)
    (fun c hc => by
      rcases hs c hc with h | h | h | h | h <;> simp [wt, h])]
  have : ∀ w, ∑ c ∈ s with wt c = w, F c.card = cen w * F w := by
    intro w
    rw [sum_congr rfl (g := fun _ => F w) (fun c hc => by
      rw [mem_filter] at hc; rw [← hc.2]; rfl), sum_const, smul_eq_mul, hcen]
  simp only [this]
  simp only [List.map_cons, List.map_nil, List.sum_cons, List.sum_nil, add_zero]
  rw [sum_insert (by decide), sum_insert (by decide), sum_insert (by decide),
    sum_insert (by decide), sum_singleton]

theorem sum_codewords (F : ℕ → ℕ) :
    ∑ c ∈ codewords, F c.card = ([0, 8, 12, 16, 24].map fun w => census w * F w).sum :=
  sum_by_weight codewords (fun _ hc => golay_weight_mem (mem_codewords.1 hc)) F census
    (fun _ => rfl)

/-- **Every shell, counted from the census by generating functions.** -/
theorem shell_card_gf (t : ℕ) :
    {x : Fin 24 → ℤ | IsLeech x ∧ normSq x = 16 * t}.ncard =
      ([0, 8, 12, 16, 24].map fun w => census w * (patternGF 0 w t + patternGF 1 w t)).sum := by
  rw [shellSet_eq, Set.ncard_coe_finset, card_shellSet]
  simp only [card_fib]
  exact sum_codewords (fun w => patternGF 0 w t + patternGF 1 w t)

/-! ## 3. The procedure: truncated generating functions as arrays -/

/-- The one-coordinate generating function as an array, index `8n + s`. -/
def oneArr (r : ℤ) (lim : ℕ) : Array ℕ :=
  Array.ofFn (n := (lim + 1) * 8) fun k =>
    #((Icc (-(lim : ℤ)) lim).filter fun v =>
      v % 4 = r ∧ v.natAbs ^ 2 = k.1 / 8 ∧ (v : ZMod 8) = ((k.1 % 8 : ℕ) : ZMod 8))

/-- A sum over `range n` is the sum of the mapped list (the form the
procedure evaluates quickly). -/
theorem sum_range_list (n : ℕ) (f : ℕ → ℕ) :
    ∑ a ∈ range n, f a = ((List.range n).map f).sum := by
  rw [Finset.sum_eq_multiset_sum, Finset.range_val, Multiset.range, Multiset.map_coe,
    Multiset.sum_coe]

/-- The product, truncated at squared length `lim`: entry `8n + s` is
`∑_{a ≤ n} ∑_{u < 8} p[8a + u] · q[8(n − a) + (s − u) mod 8]`. -/
def mulArr (lim : ℕ) (p q : Array ℕ) : Array ℕ :=
  Array.ofFn (n := (lim + 1) * 8) fun k =>
    ((List.range (k.1 / 8 + 1)).map fun a => ((List.range 8).map fun u =>
      p[8 * a + u]! * q[8 * (k.1 / 8 - a) + (k.1 % 8 + 8 - u) % 8]!).sum).sum

/-- The `k`-th power, truncated. -/
def powArr (lim : ℕ) (p : Array ℕ) : ℕ → Array ℕ
  | 0 => Array.ofFn (n := (lim + 1) * 8) fun k => if k.1 = 0 then 1 else 0
  | k + 1 => mulArr lim (powArr lim p k) p

/-- The procedure's count on one codeword of weight `w`. -/
def patternArr (m w t : ℕ) : ℕ :=
  let lim := 16 * t
  let (on, off) : ℤ × ℤ := if m = 0 then (2, 0) else (1, 3)
  (mulArr lim (powArr lim (oneArr on lim) w) (powArr lim (oneArr off lim) (24 - w)))[8 * lim + (4 * m) % 8]!

/-- The procedure's shell count from the census. -/
def shellArr (t : ℕ) : ℕ :=
  ([0, 8, 12, 16, 24].map fun w => censusTable w * (patternArr 0 w t + patternArr 1 w t)).sum

/-- An array represents a generating function up to squared length `lim`. -/
def Rep (lim : ℕ) (A : Array ℕ) (P : GF) : Prop :=
  ∀ n ≤ lim, ∀ u < 8, A[8 * n + u]! = P (n, (u : ZMod 8))

theorem ofFn_getElem! {N : ℕ} (f : Fin N → ℕ) {k : ℕ} (hk : k < N) :
    (Array.ofFn f)[k]! = f ⟨k, hk⟩ := by
  simp [getElem!_pos, hk]

theorem idx_lt {lim n u : ℕ} (hn : n ≤ lim) (hu : u < 8) : 8 * n + u < (lim + 1) * 8 := by
  nlinarith

theorem rep_one (r : ℤ) (lim : ℕ) : Rep lim (oneArr r lim) (gfOne r lim) := by
  classical
  intro n hn u hu
  rw [oneArr, ofFn_getElem! _ (idx_lt hn hu), gfOne, Finsupp.finset_sum_apply]
  simp only [AddMonoidAlgebra.single_apply, sum_boole, Nat.cast_id, cls, filter_filter]
  have h1 : (8 * n + u) / 8 = n := by omega
  have h2 : (8 * n + u) % 8 = u := by omega
  simp only [h1, h2]
  congr 1
  apply filter_congr
  intro v _
  simp [expo, Prod.ext_iff, eq_comm]

theorem mul_coeff (P Q : GF) (n : ℕ) (s : ZMod 8) :
    (P * Q) (n, s) = ∑ a ∈ range (n + 1), ∑ u ∈ range 8, P (a, (u : ZMod 8)) * Q (n - a, s - u) := by
  classical
  let f : ℕ × ℕ → (ℕ × ZMod 8) × (ℕ × ZMod 8) :=
    fun au => ((au.1, (au.2 : ZMod 8)), (n - au.1, s - au.2))
  have hinj : Set.InjOn f ↑(range (n + 1) ×ˢ range 8) := by
    rintro ⟨a, u⟩ hau ⟨a', u'⟩ hau' h
    simp only [coe_product, Set.mem_prod, mem_coe, mem_range] at hau hau'
    simp only [f, Prod.mk.injEq] at h
    obtain ⟨⟨h1, h2⟩, -⟩ := h
    subst h1
    have := congrArg ZMod.val h2
    rw [ZMod.val_natCast, ZMod.val_natCast, Nat.mod_eq_of_lt hau.2, Nat.mod_eq_of_lt hau'.2] at this
    rw [this]
  rw [AddMonoidAlgebra.mul_apply_antidiagonal P Q (n, s) ((range (n + 1) ×ˢ range 8).image f)]
  · rw [sum_image hinj, sum_product]
  · rintro ⟨⟨a, x⟩, ⟨b, y⟩⟩
    simp only [mem_image, mem_product, mem_range, Prod.exists, Prod.mk_add_mk, Prod.mk.injEq, f]
    constructor
    · rintro ⟨a', u, ⟨ha, hu⟩, ⟨rfl, rfl⟩, rfl, rfl⟩
      exact ⟨by omega, by ring⟩
    · rintro ⟨h1, h2⟩
      refine ⟨a, x.val, ⟨by omega, ZMod.val_lt x⟩, ⟨rfl, ZMod.natCast_zmod_val x⟩, by omega, ?_⟩
      rw [ZMod.natCast_zmod_val, ← h2]; ring

theorem rep_mul {lim : ℕ} {A B : Array ℕ} {P Q : GF} (hA : Rep lim A P) (hB : Rep lim B Q) :
    Rep lim (mulArr lim A B) (P * Q) := by
  intro n hn u hu
  rw [mulArr, ofFn_getElem! _ (idx_lt hn hu), mul_coeff]
  simp only [← sum_range_list]
  have h1 : (8 * n + u) / 8 = n := by omega
  have h2 : (8 * n + u) % 8 = u := by omega
  simp only [h1, h2]
  apply sum_congr rfl
  intro a ha
  apply sum_congr rfl
  intro u' hu'
  rw [mem_range] at ha hu'
  rw [hA a (by omega) u' hu', hB (n - a) (by omega) _ (Nat.mod_lt _ (by norm_num))]
  congr 2
  rw [ZMod.natCast_mod, Nat.cast_sub (by omega), Nat.cast_add]
  have : ((8 : ℕ) : ZMod 8) = 0 := by decide
  rw [this, add_zero]

theorem rep_pow {lim : ℕ} {A : Array ℕ} {P : GF} (hA : Rep lim A P) (k : ℕ) :
    Rep lim (powArr lim A k) (P ^ k) := by
  induction k with
  | zero =>
    intro n hn u hu
    rw [powArr, ofFn_getElem! _ (idx_lt hn hu), pow_zero, AddMonoidAlgebra.one_def,
      AddMonoidAlgebra.single_apply]
    by_cases h : n = 0 ∧ u = 0
    · obtain ⟨rfl, rfl⟩ := h; simp only [if_true]; rfl
    · have h' : ¬ ((0 : ℕ × ZMod 8) = (n, (u : ZMod 8))) := by
        intro he
        simp only [Prod.ext_iff, Prod.fst_zero, Prod.snd_zero] at he
        apply h
        refine ⟨he.1.symm, ?_⟩
        have := congrArg ZMod.val he.2
        rw [ZMod.val_zero, ZMod.val_natCast, Nat.mod_eq_of_lt hu] at this
        exact this.symm
      rw [if_neg h', if_neg (show ¬ (8 * n + u = 0) by omega)]
  | succ k ih =>
    rw [powArr, pow_succ]
    exact rep_mul ih hA

theorem patternArr_eq (m w t : ℕ) (hm : m ≤ 1) : patternArr m w t = patternGF m w t := by
  have key : ∀ a b : ℤ, ∀ s < 8,
      (mulArr (16 * t) (powArr (16 * t) (oneArr a (16 * t)) w)
        (powArr (16 * t) (oneArr b (16 * t)) (24 - w)))[8 * (16 * t) + s]! =
      (gfOne a (16 * t) ^ w * gfOne b (16 * t) ^ (24 - w)) (16 * t, (s : ZMod 8)) :=
    fun a b s hs => rep_mul (rep_pow (rep_one a _) w) (rep_pow (rep_one b _) _) _ le_rfl s hs
  interval_cases m
  · simpa [patternArr, patternGF] using key 2 0 0 (by norm_num)
  · simpa [patternArr, patternGF] using key 1 3 4 (by norm_num)

/-- **The procedure counts the Leech lattice, for every shell.** -/
theorem shellArr_correct (t : ℕ) :
    {x : Fin 24 → ℤ | IsLeech x ∧ normSq x = 16 * t}.ncard = shellArr t := by
  rw [shell_card_gf, shellArr]
  obtain ⟨h0, h8, h12, h16, h24⟩ := census_values
  simp [patternArr_eq, censusTable, h0, h8, h12, h16, h24]

/-! ## 4. The same procedure with shared powers, and the shells' sizes

`shellArr` recomputes every power for every weight. `shellFast` forms the
powers `8, 12, 16, 24` of each of the four one-coordinate functions once, by
squaring (`powTab`), and reads only the one coefficient it needs (`coeffAt`).
It is proved correct for every shell the same way, through `Rep`. -/

/-- The unit array: the generating function `1`. -/
def unitArr (lim : ℕ) : Array ℕ := Array.ofFn (n := (lim + 1) * 8) fun k => if k.1 = 0 then 1 else 0

/-- The powers `8, 12, 16, 24`, by squaring. -/
def powTab (lim : ℕ) (A : Array ℕ) : Array ℕ × Array ℕ × Array ℕ × Array ℕ :=
  let a2 := mulArr lim A A
  let a4 := mulArr lim a2 a2
  let a8 := mulArr lim a4 a4
  let a16 := mulArr lim a8 a8
  (a8, mulArr lim a8 a4, a16, mulArr lim a16 a8)

/-- The power of weight `w` from the table (`1` for `w = 0`). -/
def pick (lim : ℕ) (T : Array ℕ × Array ℕ × Array ℕ × Array ℕ) (w : ℕ) : Array ℕ :=
  if w = 8 then T.1 else if w = 12 then T.2.1 else if w = 16 then T.2.2.1
    else if w = 24 then T.2.2.2 else unitArr lim

/-- One coefficient `(n, s)` of the product of two arrays. -/
def coeffAt (p q : Array ℕ) (n s : ℕ) : ℕ :=
  ((List.range (n + 1)).map fun a => ((List.range 8).map fun u =>
      p[8 * a + u]! * q[8 * (n - a) + (s + 8 - u) % 8]!).sum).sum

/-- The shell count with shared powers. -/
def shellFast (t : ℕ) : ℕ :=
  let lim := 16 * t
  let T2 := powTab lim (oneArr 2 lim)
  let T0 := powTab lim (oneArr 0 lim)
  let T1 := powTab lim (oneArr 1 lim)
  let T3 := powTab lim (oneArr 3 lim)
  ([0, 8, 12, 16, 24].map fun w => censusTable w *
    (coeffAt (pick lim T2 w) (pick lim T0 (24 - w)) lim 0 +
      coeffAt (pick lim T1 w) (pick lim T3 (24 - w)) lim 4)).sum

theorem rep_unit (lim : ℕ) : Rep lim (unitArr lim) 1 := by
  have h := rep_pow (rep_one 0 lim) 0
  rw [pow_zero] at h
  exact h

theorem rep_powTab {lim : ℕ} {A : Array ℕ} {P : GF} (hA : Rep lim A P) {w : ℕ}
    (hw : w = 0 ∨ w = 8 ∨ w = 12 ∨ w = 16 ∨ w = 24) :
    Rep lim (pick lim (powTab lim A) w) (P ^ w) := by
  have h2 := rep_mul hA hA
  have h4 := rep_mul h2 h2
  have h8 := rep_mul h4 h4
  have h12 := rep_mul h8 h4
  have h16 := rep_mul h8 h8
  have h24 := rep_mul h16 h8
  rcases hw with rfl | rfl | rfl | rfl | rfl
  · simpa [pick] using rep_unit lim
  · convert h8 using 1; ring
  · convert h12 using 1; ring
  · convert h16 using 1; ring
  · convert h24 using 1; ring

theorem coeffAt_rep {lim : ℕ} {A B : Array ℕ} {P Q : GF} (hA : Rep lim A P) (hB : Rep lim B Q)
    {s : ℕ} (hs : s < 8) : coeffAt A B lim s = (P * Q) (lim, (s : ZMod 8)) := by
  rw [coeffAt, mul_coeff]
  simp only [← sum_range_list]
  apply sum_congr rfl
  intro a ha
  apply sum_congr rfl
  intro u' hu'
  rw [mem_range] at ha hu'
  rw [hA a (by omega) u' hu', hB (lim - a) (by omega) _ (Nat.mod_lt _ (by norm_num))]
  congr 2
  rw [ZMod.natCast_mod, Nat.cast_sub (by omega), Nat.cast_add]
  have : ((8 : ℕ) : ZMod 8) = 0 := by decide
  rw [this, add_zero]

theorem shellFast_term (t w : ℕ) (hw : w = 0 ∨ w = 8 ∨ w = 12 ∨ w = 16 ∨ w = 24) :
    coeffAt (pick (16 * t) (powTab (16 * t) (oneArr 2 (16 * t))) w)
        (pick (16 * t) (powTab (16 * t) (oneArr 0 (16 * t))) (24 - w)) (16 * t) 0 +
      coeffAt (pick (16 * t) (powTab (16 * t) (oneArr 1 (16 * t))) w)
        (pick (16 * t) (powTab (16 * t) (oneArr 3 (16 * t))) (24 - w)) (16 * t) 4 =
    patternGF 0 w t + patternGF 1 w t := by
  have hw' : 24 - w = 0 ∨ 24 - w = 8 ∨ 24 - w = 12 ∨ 24 - w = 16 ∨ 24 - w = 24 := by omega
  rw [coeffAt_rep (rep_powTab (rep_one 2 _) hw) (rep_powTab (rep_one 0 _) hw') (by norm_num),
    coeffAt_rep (rep_powTab (rep_one 1 _) hw) (rep_powTab (rep_one 3 _) hw') (by norm_num)]
  simp [patternGF]

/-- **The procedure with shared powers counts the Leech lattice, for every
shell.** -/
theorem shellFast_correct (t : ℕ) :
    {x : Fin 24 → ℤ | IsLeech x ∧ normSq x = 16 * t}.ncard = shellFast t := by
  rw [shell_card_gf, shellFast]
  obtain ⟨h0, h8, h12, h16, h24⟩ := census_values
  simp only [List.map_cons, List.map_nil, List.sum_cons, List.sum_nil,
    shellFast_term t 0 (by norm_num), shellFast_term t 8 (by norm_num),
    shellFast_term t 12 (by norm_num), shellFast_term t 16 (by norm_num),
    shellFast_term t 24 (by norm_num), h0, h8, h12, h16, h24]
  simp [censusTable]

/-- The procedure of `LeechShells.lean` (Phase 164) gives the same counts on
the shells `t ≤ 4`, the range it was run on. -/
theorem shellFast_eq_shellCount : ∀ t < 5, shellFast t = shellCount t := by
  simp only [census_eq_table]
  native_decide

/-- **The Phase 164 procedure counts the Leech lattice** on every shell it was
run on (`t ≤ 4`). -/
theorem shellCount_correct {t : ℕ} (ht : t < 5) :
    {x : Fin 24 → ℤ | IsLeech x ∧ normSq x = 16 * t}.ncard = shellCount t := by
  rw [shellFast_correct, shellFast_eq_shellCount t ht]

/-- The procedure's values on the first eight shells. -/
theorem shellFast_values :
    shellFast 0 = 1 ∧ shellFast 1 = 0 ∧ shellFast 2 = 196560 ∧ shellFast 3 = 16773120 ∧
    shellFast 4 = 398034000 ∧ shellFast 5 = 4629381120 ∧ shellFast 6 = 34417656000 ∧
    shellFast 7 = 187489935360 := by
  native_decide

/-- **The sizes of the first eight shells of the Leech lattice**, as theorems
about the lattice's definition: true norms `0, 2, 4, …, 14`. -/
theorem leech_shell_sizes :
    {x : Fin 24 → ℤ | IsLeech x ∧ normSq x = 0}.ncard = 1 ∧
    {x : Fin 24 → ℤ | IsLeech x ∧ normSq x = 16}.ncard = 0 ∧
    {x : Fin 24 → ℤ | IsLeech x ∧ normSq x = 32}.ncard = 196560 ∧
    {x : Fin 24 → ℤ | IsLeech x ∧ normSq x = 48}.ncard = 16773120 ∧
    {x : Fin 24 → ℤ | IsLeech x ∧ normSq x = 64}.ncard = 398034000 ∧
    {x : Fin 24 → ℤ | IsLeech x ∧ normSq x = 80}.ncard = 4629381120 ∧
    {x : Fin 24 → ℤ | IsLeech x ∧ normSq x = 96}.ncard = 34417656000 ∧
    {x : Fin 24 → ℤ | IsLeech x ∧ normSq x = 112}.ncard = 187489935360 := by
  have h := fun t => shellFast_correct t
  obtain ⟨h0, h1, h2, h3, h4, h5, h6, h7⟩ := shellFast_values
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩
  · simpa [h0] using h 0
  · simpa [h1] using h 1
  · simpa [h2] using h 2
  · simpa [h3] using h 3
  · simpa [h4] using h 4
  · simpa [h5] using h 5
  · simpa [h6] using h 6
  · simpa [h7] using h 7

end GLM.LeechShellCount
