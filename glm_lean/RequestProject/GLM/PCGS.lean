import Mathlib

/-!
# Proof-carrying generative substrate: the claims the wider-landscape script makes

`source_material/pcgs_wider_landscape_v4.txt` pushes "generate, don't store" past
the Golay/Leech pair the substrate already generates
(`GLM.ZeroStorage`, `GLM.ZeroStorageV5`) and onto a wider list of systems: a
Reed-Muller code generated from its evaluation basis, a number-theoretic
transform generated from a primitive root, a cost algebra that replaces "CPU
cycles and RAM bytes" with algebraic operation counts and information bits, and
a physical layer that turns those two axes into energies.

Everything the script *asserts* about those systems is tested there.  This file
proves the part that is mathematics rather than engineering.

## §1 The cost algebra is a commutative monoid, and the totals are additive

`Cost` is the script's `CostVector`: six operation counters and one information
counter.  Sequential composition is addition and `k`-fold repetition is
`Cost.scale`, so the claims that make the ledger usable are
`Cost.add_comm`, `Cost.add_assoc`, `Cost.algebraicTotal_add`,
`Cost.algebraicTotal_scale` and `Cost.scale_add` — a report may be assembled
in any order and in any grouping and still name the same cost.

## §2 The information axis is the tight description bound

`bitsFor n` is the script's `InformationComplexity.of_set`, written as
`Nat.size (n-1)`.  `bitsFor_spec` says `n ≤ 2 ^ bitsFor n` (the bound is
achievable) and `bitsFor_min` says nothing smaller works, so `bitsFor` is the
exact number of bits needed to name one element of an `n`-element image —
`bitsFor_two_pow` and `bitsFor_pow` are the two cases the script quotes.

## §3 Reed-Muller RM(1,m): the weight is forced, so the distance needs no table

A codeword of RM(1,m) is an affine functional `x ↦ c + ⟪a, x⟫` on `(Fin m → ZMod 2)`.
`rmWeight_of_ne_zero` shows that whenever `a ≠ 0` exactly half the points are
hit — `2 ^ (m-1)`, by an involution that flips one coordinate on which `a` is
supported — and `rmWeight_of_zero` handles the two constant words.
`rm_min_distance` then reads off the minimum distance `2 ^ (m-1)` of the script's
generated code without enumerating its `2 ^ (m+1)` codewords.

## §4 The transform inverts: orthogonality of a primitive root

`ntt` and `intt` are the transform pair the script generates from `(p, g)`.
`sum_geom_of_pow_eq_one` is the orthogonality relation — a root of unity other
than `1` sums to zero over a full period — and `ntt_intt` proves the round trip,
which is the semantic specification the script tests on examples.

## §5 The physical layer: erasure, reversibility, and a lower bound that stays one

`bitsErased` is `max 0 (in - out)`; `bitsErased_reversible` is Bennett's
observation that a reversible step erases nothing, and `landauerEnergy_mono`
plus `landauerEnergy_le_of_le_log_two` are the reason the script may replace
`ln 2` by a rational lower bound and still report a *lower* bound on the
dissipated energy.  `ln2Fast_le_log_two` is the bound the module now uses --
every partial sum of `Σ 1/(k 2^k)` at once -- and `ln2Lower_100_le_log_two`
checks the slower constant the source script used.

## §6 Caching is a decision, not a slogan

`breakeven_iff` is the exact statement of when materialising wins: with
generation dearer than lookup by `d` per query, a stored table pays for itself
exactly once the query count reaches `⌈store / d⌉` (`breakevenQueries_spec`).
-/

namespace GLM.PCGS

/-! ## §1 The cost algebra -/

/-- The script's `CostVector`: an exact algebraic-operation count together with
the information content of the answer, replacing "CPU cycles and RAM bytes". -/
structure Cost where
  mul : ℕ := 0
  add : ℕ := 0
  sub : ℕ := 0
  xor : ℕ := 0
  modinv : ℕ := 0
  cmp : ℕ := 0
  infoBits : ℕ := 0
  deriving DecidableEq, Repr

namespace Cost

/-- Sequential composition of two measured stages. -/
def plus (c d : Cost) : Cost :=
  { mul := c.mul + d.mul, add := c.add + d.add, sub := c.sub + d.sub,
    xor := c.xor + d.xor, modinv := c.modinv + d.modinv, cmp := c.cmp + d.cmp,
    infoBits := c.infoBits + d.infoBits }

/-- `k`-fold repetition of a measured stage. -/
def scale (c : Cost) (k : ℕ) : Cost :=
  { mul := c.mul * k, add := c.add * k, sub := c.sub * k, xor := c.xor * k,
    modinv := c.modinv * k, cmp := c.cmp * k, infoBits := c.infoBits * k }

/-- The all-zero ledger: the cost of doing nothing. -/
def zero : Cost := {}

/-- The algebraic axis collapsed to one number: every primitive operation counts
once (a modular inverse is one logical operation, not its expansion). -/
def algebraicTotal (c : Cost) : ℕ :=
  c.mul + c.add + c.sub + c.xor + c.modinv + c.cmp

theorem plus_comm (c d : Cost) : c.plus d = d.plus c := by
  simp only [plus, Cost.mk.injEq]
  omega

theorem plus_assoc (c d e : Cost) : (c.plus d).plus e = c.plus (d.plus e) := by
  simp only [plus, Cost.mk.injEq]
  omega

theorem zero_plus (c : Cost) : zero.plus c = c := by
  cases c; simp [plus, zero]

theorem plus_zero (c : Cost) : c.plus zero = c := by
  cases c; simp [plus, zero]

theorem algebraicTotal_plus (c d : Cost) :
    (c.plus d).algebraicTotal = c.algebraicTotal + d.algebraicTotal := by
  simp only [plus, algebraicTotal]
  omega

theorem algebraicTotal_scale (c : Cost) (k : ℕ) :
    (c.scale k).algebraicTotal = c.algebraicTotal * k := by
  simp only [scale, algebraicTotal]
  ring

theorem infoBits_plus (c d : Cost) :
    (c.plus d).infoBits = c.infoBits + d.infoBits := rfl

theorem scale_succ (c : Cost) (k : ℕ) : c.scale (k + 1) = (c.scale k).plus c := by
  simp [scale, plus, Nat.mul_succ]

theorem scale_one (c : Cost) : c.scale 1 = c := by
  cases c; simp [scale]

theorem scale_zero (c : Cost) : c.scale 0 = zero := by
  simp [scale, zero]

end Cost

/-! ## §2 The information axis -/

/-- The script's `InformationComplexity.of_set`: the number of bits needed to
name one element of a set of `n` elements, `⌈log₂ n⌉`. -/
def bitsFor (n : ℕ) : ℕ := Nat.size (n - 1)

theorem bitsFor_spec (n : ℕ) : n ≤ 2 ^ bitsFor n := by
  rcases Nat.eq_zero_or_pos n with h | h
  · subst h; simp [bitsFor]
  · have hs : n - 1 < 2 ^ Nat.size (n - 1) := Nat.lt_size_self (n - 1)
    have hb : bitsFor n = Nat.size (n - 1) := rfl
    rw [hb]
    omega

theorem bitsFor_min {n b : ℕ} (h : n ≤ 2 ^ b) : bitsFor n ≤ b := by
  have hpos : 0 < 2 ^ b := Nat.two_pow_pos b
  have hlt : n - 1 < 2 ^ b := by omega
  exact Nat.size_le.mpr hlt

theorem bitsFor_le_iff (n b : ℕ) : bitsFor n ≤ b ↔ n ≤ 2 ^ b :=
  ⟨fun h => le_trans (bitsFor_spec n) (Nat.pow_le_pow_right (by norm_num) h),
   fun h => bitsFor_min h⟩

theorem bitsFor_two_pow (k : ℕ) : bitsFor (2 ^ k) = k := by
  have h1 : bitsFor (2 ^ k) ≤ k := bitsFor_min le_rfl
  by_contra hne
  have h2 : bitsFor (2 ^ k) < k := lt_of_le_of_ne h1 (fun h => hne h)
  have h3 : (2 : ℕ) ^ k ≤ 2 ^ bitsFor (2 ^ k) := bitsFor_spec _
  have : (2 : ℕ) ^ bitsFor (2 ^ k) < 2 ^ k := Nat.pow_lt_pow_right (by norm_num) h2
  omega

/-- The description bound of an `n`-symbol word over an alphabet of size `q`. -/
theorem bitsFor_pow (q n : ℕ) : bitsFor (q ^ n) ≤ n * bitsFor q := by
  refine bitsFor_min ?_
  calc q ^ n ≤ (2 ^ bitsFor q) ^ n := Nat.pow_le_pow_left (bitsFor_spec q) n
    _ = 2 ^ (bitsFor q * n) := by rw [← pow_mul]
    _ = 2 ^ (n * bitsFor q) := by rw [Nat.mul_comm]

/-! ## §3 Reed-Muller RM(1,m) -/

section ReedMuller

variable {m : ℕ}

theorem zmod2_cases (v : ZMod 2) : v = 0 ∨ v = 1 := by revert v; decide

theorem zmod2_sub_eq_one_iff (u v : ZMod 2) : u - v = 1 ↔ u ≠ v := by revert u v; decide

/-- The value at `x` of the RM(1,m) codeword with linear part `a` and constant
part `c`: the affine functional `x ↦ c + ⟪a, x⟫` over `𝔽₂`. -/
def rmValue (a : Fin m → ZMod 2) (c : ZMod 2) (x : Fin m → ZMod 2) : ZMod 2 :=
  c + ∑ i, a i * x i

/-- The Hamming weight of that codeword: how many evaluation points it is `1` at. -/
noncomputable def rmWeight (a : Fin m → ZMod 2) (c : ZMod 2) : ℕ :=
  (Finset.univ.filter fun x : Fin m → ZMod 2 => rmValue a c x = 1).card

/-- Flipping coordinate `i₀` of an evaluation point. -/
def flipAt (i₀ : Fin m) (x : Fin m → ZMod 2) : Fin m → ZMod 2 :=
  Function.update x i₀ (x i₀ + 1)

theorem flipAt_flipAt (i₀ : Fin m) (x : Fin m → ZMod 2) :
    flipAt i₀ (flipAt i₀ x) = x := by
  funext j
  by_cases h : j = i₀
  · subst h
    simp only [flipAt, Function.update_self]
    have h2 : (1 : ZMod 2) + 1 = 0 := by decide
    rw [add_assoc, h2, add_zero]
  · simp [flipAt, Function.update_of_ne h]

theorem rmValue_flipAt {a : Fin m → ZMod 2} {c : ZMod 2} {i₀ : Fin m}
    (ha : a i₀ = 1) (x : Fin m → ZMod 2) :
    rmValue a c (flipAt i₀ x) = rmValue a c x + 1 := by
  have hsplit : ∀ f : Fin m → ZMod 2,
      ∑ i, a i * f i = a i₀ * f i₀ + ∑ i ∈ Finset.univ.erase i₀, a i * f i := by
    intro f
    rw [← Finset.add_sum_erase _ _ (Finset.mem_univ i₀)]
  have h2 : ∀ i ∈ Finset.univ.erase i₀, a i * (flipAt i₀ x) i = a i * x i := by
    intro i hi
    have hne : i ≠ i₀ := (Finset.mem_erase.mp hi).1
    simp [flipAt, Function.update_of_ne hne]
  have hsum : ∑ i, a i * (flipAt i₀ x) i = (∑ i, a i * x i) + 1 := by
    rw [hsplit (flipAt i₀ x), hsplit x, Finset.sum_congr rfl h2]
    have h1 : (flipAt i₀ x) i₀ = x i₀ + 1 := by simp [flipAt]
    rw [h1, ha]
    ring
  simp only [rmValue, hsum]
  ring

/-- **Half the points.**  A Reed-Muller RM(1,m) codeword with nonzero linear part
has weight exactly `2 ^ (m - 1)`: the coordinate flip on a support point of `a`
is an involution exchanging the points where the codeword is `1` with those
where it is `0`, and the two sets cover `𝔽₂^m`. -/
theorem rmWeight_of_ne_zero {a : Fin m → ZMod 2} (ha : a ≠ 0) (c : ZMod 2) :
    rmWeight a c = 2 ^ (m - 1) := by
  obtain ⟨i₀, hi₀⟩ : ∃ i, a i ≠ 0 := by
    by_contra h
    push_neg at h
    exact ha (funext fun i => h i)
  have ha1 : a i₀ = 1 := (zmod2_cases (a i₀)).resolve_left hi₀
  classical
  set S := Finset.univ.filter fun x : Fin m → ZMod 2 => rmValue a c x = 1 with hS
  set T := Finset.univ.filter fun x : Fin m → ZMod 2 => ¬ rmValue a c x = 1 with hT
  have hcard : S.card = T.card := by
    refine Finset.card_bij' (fun x _ => flipAt i₀ x) (fun x _ => flipAt i₀ x)
      ?_ ?_ ?_ ?_
    · intro x hx
      simp only [hS, Finset.mem_filter, Finset.mem_univ, true_and] at hx
      simp only [hT, Finset.mem_filter, Finset.mem_univ, true_and]
      rw [rmValue_flipAt ha1, hx]
      decide
    · intro x hx
      simp only [hT, Finset.mem_filter, Finset.mem_univ, true_and] at hx
      simp only [hS, Finset.mem_filter, Finset.mem_univ, true_and]
      rw [rmValue_flipAt ha1, (zmod2_cases (rmValue a c x)).resolve_right hx]
      decide
    · intro x _; exact flipAt_flipAt i₀ x
    · intro x _; exact flipAt_flipAt i₀ x
  have htotal : S.card + T.card = 2 ^ m := by
    rw [hS, hT, Finset.card_filter_add_card_filter_not]
    simp [ZMod.card]
  have hm : 1 ≤ m := by
    rcases Nat.eq_zero_or_pos m with h | h
    · subst h; exact absurd (Subsingleton.elim a 0) ha
    · exact h
  have hpow : 2 ^ m = 2 ^ (m - 1) * 2 := by
    conv_lhs => rw [show m = (m - 1) + 1 by omega]
    ring
  have hw : rmWeight a c = S.card := rfl
  omega

/-- The two constant codewords: the zero word has weight `0`, the all-ones word
has weight `2 ^ m`. -/
theorem rmWeight_of_zero (c : ZMod 2) :
    rmWeight (0 : Fin m → ZMod 2) c = if c = 1 then 2 ^ m else 0 := by
  classical
  by_cases hc : c = 1
  · subst hc
    rw [if_pos rfl]
    have hfilter : rmWeight (0 : Fin m → ZMod 2) 1
        = (Finset.univ.filter fun _ : Fin m → ZMod 2 => True).card := by
      unfold rmWeight
      congr 1
      apply Finset.filter_congr
      intro x _
      simp [rmValue]
    rw [hfilter]
    simp [ZMod.card]
  · rw [if_neg hc]
    have hfilter : rmWeight (0 : Fin m → ZMod 2) c
        = (Finset.univ.filter fun _ : Fin m → ZMod 2 => False).card := by
      unfold rmWeight
      congr 1
      apply Finset.filter_congr
      intro x _
      simp [rmValue, hc]
    rw [hfilter]
    simp

theorem rmValue_sub (a b : Fin m → ZMod 2) (c d : ZMod 2) (x : Fin m → ZMod 2) :
    rmValue (a - b) (c - d) x = rmValue a c x - rmValue b d x := by
  simp only [rmValue, Pi.sub_apply, sub_mul, Finset.sum_sub_distrib]
  ring

/-- **The minimum distance of RM(1,m) is `2 ^ (m-1)`,** proved from the
generator rather than read off a stored codeword table: two distinct codewords
differ in at least `2 ^ (m-1)` places. -/
theorem rm_min_distance (hm : 1 ≤ m) {a b : Fin m → ZMod 2} {c d : ZMod 2}
    (hne : (a, c) ≠ (b, d)) :
    2 ^ (m - 1) ≤
      (Finset.univ.filter fun x : Fin m → ZMod 2 => rmValue a c x ≠ rmValue b d x).card := by
  classical
  have hset : (Finset.univ.filter fun x : Fin m → ZMod 2 => rmValue a c x ≠ rmValue b d x)
      = (Finset.univ.filter fun x : Fin m → ZMod 2 => rmValue (a - b) (c - d) x = 1) := by
    apply Finset.filter_congr
    intro x _
    rw [rmValue_sub, zmod2_sub_eq_one_iff]
  rw [hset]
  by_cases hab : a = b
  · subst hab
    have hcd : c ≠ d := fun h => hne (by rw [h])
    have hsub : c - d = 1 := (zmod2_sub_eq_one_iff c d).mpr hcd
    have hw : (Finset.univ.filter fun x : Fin m → ZMod 2 =>
        rmValue (a - a) (c - d) x = 1).card = 2 ^ m := by
      have hz : rmWeight (a - a) (c - d) = 2 ^ m := by
        rw [sub_self, rmWeight_of_zero, if_pos hsub]
      exact hz
    rw [hw]
    exact Nat.pow_le_pow_right (by norm_num) (by omega)
  · have hne0 : a - b ≠ 0 := sub_ne_zero.mpr hab
    have hz : rmWeight (a - b) (c - d) = 2 ^ (m - 1) := rmWeight_of_ne_zero hne0 _
    exact le_of_eq hz.symm

end ReedMuller

/-! ## §4 The transform inverts -/

section Transform

variable {K : Type*} [Field K]

/-- Orthogonality: over a full period, a root of unity other than `1` sums to
zero.  This is the only fact the transform pair needs. -/
theorem sum_geom_of_pow_eq_one {x : K} {n : ℕ} (hx : x ^ n = 1) (hne : x ≠ 1) :
    ∑ i ∈ Finset.range n, x ^ i = 0 := by
  have h := geom_sum_mul x n
  rw [hx, sub_self] at h
  exact (mul_eq_zero.mp h).resolve_right (sub_ne_zero.mpr hne)

/-- The orthogonality relation in the form the transform uses it: the inner
product of the `j`-th forward column with the `k`-th inverse row is `n` on the
diagonal and `0` off it. -/
theorem root_orthogonality {n : ℕ} {w : K} (hw : IsPrimitiveRoot w n) (hwne : w ≠ 0)
    (j k : Fin n) :
    (∑ i : Fin n, w ^ (i.val * j.val) * (w⁻¹) ^ (k.val * i.val))
      = if j = k then (n : K) else 0 := by
  set x : K := w ^ j.val * (w⁻¹) ^ k.val with hx
  have hterm : ∀ i : Fin n,
      w ^ (i.val * j.val) * (w⁻¹) ^ (k.val * i.val) = x ^ i.val := by
    intro i
    rw [hx, mul_pow, ← pow_mul, ← pow_mul, Nat.mul_comm j.val i.val,
      Nat.mul_comm k.val i.val]
  have hsum : (∑ i : Fin n, w ^ (i.val * j.val) * (w⁻¹) ^ (k.val * i.val))
      = ∑ i ∈ Finset.range n, x ^ i := by
    rw [Finset.sum_congr rfl (fun i _ => hterm i)]
    exact Fin.sum_univ_eq_sum_range (fun i => x ^ i) n
  have hxn : x ^ n = 1 := by
    rw [hx, mul_pow, ← pow_mul, ← pow_mul, Nat.mul_comm j.val n,
      Nat.mul_comm k.val n, pow_mul, pow_mul, hw.pow_eq_one, inv_pow,
      hw.pow_eq_one]
    simp
  by_cases hjk : j = k
  · subst hjk
    have hx1 : x = 1 := by
      rw [hx, inv_pow]
      field_simp
    rw [hsum, hx1]
    simp
  · have hxne : x ≠ 1 := by
      intro h1
      apply hjk
      have hpow : w ^ j.val = w ^ k.val := by
        rw [hx, inv_pow] at h1
        field_simp at h1
        exact h1
      exact Fin.ext (hw.pow_inj j.isLt k.isLt hpow)
    rw [hsum, sum_geom_of_pow_eq_one hxn hxne]
    simp [hjk]

/-- The forward number-theoretic transform generated from a root `w`. -/
def ntt {n : ℕ} (w : K) (a : Fin n → K) : Fin n → K :=
  fun i => ∑ j, a j * w ^ (i.val * j.val)

/-- Its inverse, generated from `w⁻¹` and `n⁻¹` — no stored twiddle table. -/
def intt {n : ℕ} (w : K) (A : Fin n → K) : Fin n → K :=
  fun k => (n : K)⁻¹ * ∑ i, A i * (w⁻¹) ^ (k.val * i.val)

/-- **The round trip.**  For a primitive `n`-th root of unity `w` in a field
whose characteristic does not divide `n`, the generated inverse transform undoes
the generated forward transform — so the transform pair may be generated from
`(p, g)` and never stored. -/
theorem ntt_intt {n : ℕ} {w : K} (hw : IsPrimitiveRoot w n) (hn : (n : K) ≠ 0)
    (a : Fin n → K) : intt w (ntt w a) = a := by
  have hn0 : 0 < n := by
    rcases Nat.eq_zero_or_pos n with h | h
    · exact absurd (by rw [h]; simp) hn
    · exact h
  have hwne : w ≠ 0 := by
    intro h
    have hp := hw.pow_eq_one
    rw [h, zero_pow (by omega)] at hp
    exact zero_ne_one hp
  funext k
  show (n : K)⁻¹ * ∑ i : Fin n,
      (∑ j, a j * w ^ (i.val * j.val)) * (w⁻¹) ^ (k.val * i.val) = a k
  have hswap : ∑ i : Fin n, (∑ j, a j * w ^ (i.val * j.val)) * (w⁻¹) ^ (k.val * i.val)
      = ∑ j : Fin n, a j * (∑ i : Fin n, w ^ (i.val * j.val) * (w⁻¹) ^ (k.val * i.val)) := by
    simp only [Finset.sum_mul, Finset.mul_sum]
    rw [Finset.sum_comm]
    exact Finset.sum_congr rfl fun j _ => Finset.sum_congr rfl fun i _ => by ring
  rw [hswap]
  simp only [root_orthogonality hw hwne]
  rw [Finset.sum_congr rfl (fun j (_ : j ∈ Finset.univ) =>
    (by split <;> simp_all : a j * (if j = k then (n : K) else 0)
      = if j = k then a k * (n : K) else 0))]
  rw [Finset.sum_ite_eq' Finset.univ k (fun _ => a k * (n : K))]
  simp only [Finset.mem_univ, if_true]
  field_simp

end Transform

/-! ## §5 The physical layer -/

/-- Bits erased by a step taking `inBits` to `outBits`. -/
def bitsErased (inBits outBits : ℕ) : ℕ := inBits - outBits

/-- Bennett: a step that does not lose information erases nothing, so its
Landauer cost is exactly zero. -/
theorem bitsErased_reversible {inBits outBits : ℕ} (h : inBits ≤ outBits) :
    bitsErased inBits outBits = 0 := Nat.sub_eq_zero_of_le h

theorem bitsErased_mono {i₁ i₂ o : ℕ} (h : i₁ ≤ i₂) :
    bitsErased i₁ o ≤ bitsErased i₂ o := Nat.sub_le_sub_right h o

/-- A NAND-style step: two bits in, one out, one bit erased. -/
theorem bitsErased_nand : bitsErased 2 1 = 1 := rfl

/-- Landauer's floor for erasing `bits` bits at temperature `T` with Boltzmann
constant `k`, using a stand-in `L` for `ln 2`. -/
noncomputable def landauerEnergy (k T L : ℝ) (bits : ℕ) : ℝ := (bits : ℝ) * k * T * L

theorem landauerEnergy_mono {k T L : ℝ} (hk : 0 ≤ k) (hT : 0 ≤ T) (hL : 0 ≤ L)
    {b₁ b₂ : ℕ} (h : b₁ ≤ b₂) :
    landauerEnergy k T L b₁ ≤ landauerEnergy k T L b₂ := by
  unfold landauerEnergy
  have hb : (b₁ : ℝ) ≤ (b₂ : ℝ) := Nat.cast_le.mpr h
  have h1 : (b₁ : ℝ) * k ≤ (b₂ : ℝ) * k := mul_le_mul_of_nonneg_right hb hk
  have h2 : (b₁ : ℝ) * k * T ≤ (b₂ : ℝ) * k * T := mul_le_mul_of_nonneg_right h1 hT
  exact mul_le_mul_of_nonneg_right h2 hL

/-- **A rational lower bound for `ln 2` keeps the Landauer figure a lower
bound.**  This is what licences the script's exact-`Fraction` arithmetic: the
reported energy never overstates the thermodynamic floor. -/
theorem landauerEnergy_le_of_le_log_two {k T L : ℝ} (hk : 0 ≤ k) (hT : 0 ≤ T)
    (hL : L ≤ Real.log 2) (bits : ℕ) :
    landauerEnergy k T L bits ≤ landauerEnergy k T (Real.log 2) bits := by
  unfold landauerEnergy
  have hbk : 0 ≤ (bits : ℝ) * k := mul_nonneg (Nat.cast_nonneg bits) hk
  exact mul_le_mul_of_nonneg_left hL (mul_nonneg hbk hT)

/-- The script's `ln2_lower_bound`: the alternating harmonic partial sum. -/
def ln2Lower (terms : ℕ) : ℚ :=
  ∑ k ∈ Finset.range terms, (if k % 2 = 0 then (1 : ℚ) / (k + 1) else -(1 : ℚ) / (k + 1))

theorem ln2Lower_two : ln2Lower 2 = 1 / 2 := by
  norm_num [ln2Lower, Finset.sum_range_succ]

/-- The faster lower bound the module prefers: `ln 2 = Σ 1/(k 2^k)` has only
positive terms, so *every* partial sum is a lower bound -- and at thirty terms
it is nine decimal places, where the alternating sum at a hundred terms is two. -/
def ln2Fast (terms : ℕ) : ℚ :=
  ∑ k ∈ Finset.range terms, (1 : ℚ) / ((k + 1) * 2 ^ (k + 1))

/-- **Every** partial sum of `Σ 1/(k 2^k)` is below `ln 2` -- proved for all
lengths at once, where the alternating constant has to be checked one length at
a time. -/
theorem ln2Fast_le_log_two (n : ℕ) : (ln2Fast n : ℝ) ≤ Real.log 2 := by
  have hx : |(1 / 2 : ℝ)| < 1 := by rw [abs_of_pos] <;> norm_num
  have hs := Real.hasSum_pow_div_log_of_abs_lt_one hx
  have hlog : -Real.log (1 - 1 / 2 : ℝ) = Real.log 2 := by
    rw [show (1 - 1 / 2 : ℝ) = (2 : ℝ)⁻¹ by norm_num, Real.log_inv, neg_neg]
  rw [hlog] at hs
  have hle := sum_le_hasSum (Finset.range n) (fun i _ => by positivity) hs
  refine le_trans (le_of_eq ?_) hle
  push_cast [ln2Fast]
  refine Finset.sum_congr rfl fun k _ => ?_
  rw [div_pow, one_pow]
  field_simp

set_option maxRecDepth 8000 in
/-- The constant the source script actually uses is a genuine lower bound for
`ln 2` too, so every Landauer figure it reports stays below the true floor. -/
theorem ln2Lower_100_le_log_two : (ln2Lower 100 : ℝ) ≤ Real.log 2 := by
  have h : ln2Lower 100 < (6931471803 : ℚ) / 10 ^ 10 := by
    norm_num [ln2Lower, Finset.sum_range_succ]
  have hcast : ((ln2Lower 100 : ℚ) : ℝ) < (((6931471803 : ℚ) / 10 ^ 10 : ℚ) : ℝ) := by
    exact_mod_cast h
  have hlog := Real.log_two_gt_d9
  push_cast at hcast
  norm_num at hcast hlog ⊢
  linarith

/-! ## §6 Caching is a decision -/

/-- Generating beats a stored table at `q` queries exactly when the saved
per-query difference has not yet paid for the table. -/
theorem breakeven_iff (store gen look q : ℕ) (h : look ≤ gen) :
    store + look * q ≤ gen * q ↔ store ≤ (gen - look) * q := by
  have hsub : (gen - look) * q = gen * q - look * q := by rw [Nat.sub_mul]
  have hle : look * q ≤ gen * q := Nat.mul_le_mul_right q h
  omega

/-- The number of queries at which materialising starts to pay. -/
def breakevenQueries (store gen look : ℕ) : ℕ :=
  (store + (gen - look) - 1) / (gen - look)

theorem breakevenQueries_spec {store gen look : ℕ} (h : look < gen) (q : ℕ) :
    breakevenQueries store gen look ≤ q ↔ store + look * q ≤ gen * q := by
  have hd : 0 < gen - look := by omega
  rw [breakeven_iff store gen look q (le_of_lt h)]
  unfold breakevenQueries
  set d := gen - look with hdef
  set P := d * q with hP
  rw [Nat.div_le_iff_le_mul_add_pred hd, ← hP]
  omega

end GLM.PCGS
