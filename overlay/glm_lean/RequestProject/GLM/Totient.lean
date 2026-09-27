/-
# The totient sub-cycle count of an N-gon

This file is **retrieved material**: `GMHGL/spatial_totient_kinetics.py` of the
supplied archive (`source_material/GLM-main.zip`) states, as its "Totient
Sub-Cycle Theorem", that the number of proper closed loops obtained by walking
the vertices of a regular `N`-gon in constant strides is

```
  C(N) = ⌊N/2⌋ − φ(N)/2 .
```

The script verifies it by traversal for `3 ≤ N ≤ 999`. Here it is proved, for
every `N ≥ 3` at once, and the geometric reading is made precise rather than
described:

* `stride_orbit_card` — striding by `k` from a vertex of the `N`-gon returns to
  the start after `N / gcd(N,k)` steps, so the walk closes early — a *proper*
  sub-cycle — exactly when `k` shares a factor with `N`
  (`stride_proper_iff_not_coprime`);
* `card_coprime_lower_half` — the totatives below `N/2` are exactly half of
  them: `#{k ∈ [1, ⌊N/2⌋] : gcd(k,N) = 1} = φ(N)/2`, the pairing being
  `k ↦ N − k`;
* `subCycles_eq` — hence `C(N) = ⌊N/2⌋ − φ(N)/2`, which is the claim;
* `subCycles_eq_zero_iff_prime` — and the corollary the archive's "geometric
  primality" is really making: a walk on an `N`-gon has *no* proper sub-cycle
  exactly when `N` is prime.

The last statement is the honest form of the script's claim that the geometry
"derives primality": it does, but the derivation is Euler's totient, not a new
primality test — the count is as expensive as knowing the factorisation.
-/
import Mathlib

namespace GLM.Totient

open Finset

/-! ## 1. Striding around the polygon -/

/-- Striding by `k` around an `N`-gon returns to the start after `N / gcd(N,k)`
steps: the orbit of the stride is a sub-polygon on that many vertices. -/
theorem stride_orbit_card (n k : ℕ) (hn : n ≠ 0) :
    addOrderOf ((k : ZMod n)) = n / n.gcd k :=
  ZMod.addOrderOf_coe k hn

/-- The walk closes *early* — that is, it traces a proper sub-cycle rather than
the whole polygon — exactly when the stride shares a factor with `N`. -/
theorem stride_proper_iff_not_coprime (n k : ℕ) (hn : n ≠ 0) :
    addOrderOf ((k : ZMod n)) < n ↔ ¬ Nat.Coprime n k := by
  rw [stride_orbit_card n k hn]
  constructor
  · intro h hcop
    rw [Nat.Coprime] at hcop
    rw [hcop, Nat.div_one] at h
    exact lt_irrefl n h
  · intro h
    have hg : n.gcd k ≠ 0 := fun h0 => hn (Nat.eq_zero_of_gcd_eq_zero_left h0)
    have h1 : n.gcd k ≠ 1 := h
    have h2 : 2 ≤ n.gcd k := by omega
    calc n / n.gcd k ≤ n / 2 := Nat.div_le_div_left h2 (by norm_num)
      _ < n := Nat.div_lt_self (Nat.pos_of_ne_zero hn) (by norm_num)

/-! ## 2. Half the totatives lie below `N/2` -/

/-- The totatives of `n`, as strides in `[1, n]`. -/
def totatives (n : ℕ) : Finset ℕ := (Icc 1 n).filter (fun k => Nat.Coprime n k)

theorem card_totatives (n : ℕ) : (totatives n).card = n.totient := by
  have h : Icc 1 n = Ico 1 (1 + n) := by
    ext k; simp; omega
  rw [totatives, h]
  exact Nat.filter_coprime_Ico_eq_totient n 1

/-- The totatives at most `n/2`. -/
def lowerTotatives (n : ℕ) : Finset ℕ := (Icc 1 (n / 2)).filter (fun k => Nat.Coprime n k)

/-- The totatives above `n/2`. -/
def upperTotatives (n : ℕ) : Finset ℕ :=
  (Icc (n / 2 + 1) n).filter (fun k => Nat.Coprime n k)

theorem totatives_split (n : ℕ) :
    (totatives n).card = (lowerTotatives n).card + (upperTotatives n).card := by
  classical
  have hsplit : Icc 1 n = Icc 1 (n / 2) ∪ Icc (n / 2 + 1) n := by
    ext k
    simp only [mem_union, mem_Icc]
    constructor
    · rintro ⟨h1, h2⟩
      by_cases h : k ≤ n / 2
      · exact Or.inl ⟨h1, h⟩
      · exact Or.inr ⟨by omega, h2⟩
    · rintro (⟨h1, h2⟩ | ⟨h1, h2⟩)
      · exact ⟨h1, le_trans h2 (Nat.div_le_self n 2)⟩
      · exact ⟨le_trans (by omega) h1, h2⟩
  have hdisj : Disjoint (Icc 1 (n / 2)) (Icc (n / 2 + 1) n) := by
    rw [Finset.disjoint_left]
    intro a ha hb
    rw [mem_Icc] at ha hb
    omega
  rw [totatives, lowerTotatives, upperTotatives, hsplit, Finset.filter_union,
    Finset.card_union_of_disjoint (Finset.disjoint_filter_filter hdisj)]

/-- The reflection `k ↦ n − k` matches the totatives below `n/2` with those
above it. -/
theorem card_upper_eq_lower {n : ℕ} (hn : 3 ≤ n) :
    (upperTotatives n).card = (lowerTotatives n).card := by
  classical
  apply Finset.card_nbij' (i := fun k => n - k) (j := fun k => n - k)
  · intro k hk
    simp only [upperTotatives, coe_filter, Set.mem_setOf_eq, mem_Icc] at hk
    obtain ⟨⟨h1, h2⟩, hcop⟩ := hk
    have hkn : k ≠ n := by
      intro h
      subst h
      have : Nat.gcd k k = k := Nat.gcd_self k
      rw [Nat.Coprime, this] at hcop
      omega
    simp only [lowerTotatives, coe_filter, Set.mem_setOf_eq, mem_Icc]
    refine ⟨⟨by omega, by omega⟩, ?_⟩
    have hgcd : Nat.gcd n (n - k) = Nat.gcd n k := Nat.gcd_self_sub_right (by omega)
    rw [Nat.Coprime, hgcd]
    exact hcop
  · intro k hk
    simp only [lowerTotatives, coe_filter, Set.mem_setOf_eq, mem_Icc] at hk
    obtain ⟨⟨h1, h2⟩, hcop⟩ := hk
    have hhalf : n / 2 < n := Nat.div_lt_self (by omega) (by norm_num)
    have hne : 2 * k ≠ n := by
      intro h
      have hk2 : Nat.gcd n k = k := Nat.gcd_eq_right ⟨2, by omega⟩
      rw [Nat.Coprime, hk2] at hcop
      omega
    simp only [upperTotatives, coe_filter, Set.mem_setOf_eq, mem_Icc]
    refine ⟨⟨by omega, by omega⟩, ?_⟩
    have hgcd : Nat.gcd n (n - k) = Nat.gcd n k := Nat.gcd_self_sub_right (by omega)
    rw [Nat.Coprime, hgcd]
    exact hcop
  · intro k hk
    simp only [upperTotatives, coe_filter, Set.mem_setOf_eq, mem_Icc] at hk
    show n - (n - k) = k
    omega
  · intro k hk
    simp only [lowerTotatives, coe_filter, Set.mem_setOf_eq, mem_Icc] at hk
    have hhalf : n / 2 < n := Nat.div_lt_self (by omega) (by norm_num)
    show n - (n - k) = k
    omega

/-- **Half the totatives lie below `n/2`.** -/
theorem card_coprime_lower_half {n : ℕ} (hn : 3 ≤ n) :
    (lowerTotatives n).card = n.totient / 2 := by
  have h := totatives_split n
  rw [card_totatives, card_upper_eq_lower hn] at h
  omega

/-! ## 3. The sub-cycle count -/

/-- The number of proper closed sub-cycles of the `n`-gon: the strides
`1 ≤ k ≤ n/2` whose walk closes before visiting every vertex. -/
def subCycles (n : ℕ) : ℕ := ((Icc 1 (n / 2)).filter (fun k => ¬ Nat.Coprime n k)).card

/-- **The totient sub-cycle theorem.** `C(N) = ⌊N/2⌋ − φ(N)/2`. -/
theorem subCycles_eq {n : ℕ} (hn : 3 ≤ n) : subCycles n = n / 2 - n.totient / 2 := by
  classical
  have hcard : (lowerTotatives n).card + subCycles n = (Icc 1 (n / 2)).card := by
    rw [lowerTotatives, subCycles]
    exact Finset.card_filter_add_card_filter_not _
  have hIcc : (Icc 1 (n / 2)).card = n / 2 := by
    rw [Nat.card_Icc]
    omega
  rw [hIcc, card_coprime_lower_half hn] at hcard
  omega

/-- The strides counted are exactly the ones whose walk closes early. -/
theorem mem_subCycles_iff {n k : ℕ} (hn : 3 ≤ n) :
    (k ∈ (Icc 1 (n / 2)).filter (fun k => ¬ Nat.Coprime n k)) ↔
      (1 ≤ k ∧ k ≤ n / 2 ∧ addOrderOf ((k : ZMod n)) < n) := by
  rw [Finset.mem_filter, Finset.mem_Icc,
    stride_proper_iff_not_coprime n k (by omega)]
  tauto

/-- **Geometric primality, honestly stated.** The `n`-gon has no proper
sub-cycle exactly when `n` is prime. -/
theorem subCycles_eq_zero_iff_prime {n : ℕ} (hn : 3 ≤ n) :
    subCycles n = 0 ↔ n.Prime := by
  constructor
  · intro h
    have hlow : (lowerTotatives n).card = n / 2 := by
      have hcard : (lowerTotatives n).card + subCycles n = (Icc 1 (n / 2)).card := by
        rw [lowerTotatives, subCycles]
        exact Finset.card_filter_add_card_filter_not _
      have hIcc : (Icc 1 (n / 2)).card = n / 2 := by rw [Nat.card_Icc]; omega
      omega
    have htot : n.totient / 2 = n / 2 := by rw [← card_coprime_lower_half hn, hlow]
    have htot' : n.totient = n - 1 := by
      have h1 : n.totient < n := Nat.totient_lt n (by omega)
      have h2 : Even n.totient := Nat.totient_even (by omega)
      rcases Nat.even_or_odd n with hpar | hpar
      · obtain ⟨m, hm⟩ := hpar
        have hn2 : ¬ Nat.Coprime n (n / 2) := by
          have : n / 2 = m := by omega
          rw [this, Nat.Coprime]
          have : Nat.gcd n m = m := Nat.gcd_eq_right ⟨2, by omega⟩
          rw [this]
          omega
        have hmem : (n / 2) ∈ (Icc 1 (n / 2)).filter (fun k => ¬ Nat.Coprime n k) := by
          rw [Finset.mem_filter, Finset.mem_Icc]
          exact ⟨⟨by omega, le_rfl⟩, hn2⟩
        rw [subCycles] at h
        rw [Finset.card_eq_zero] at h
        rw [h] at hmem
        exact absurd hmem (by simp)
      · obtain ⟨m, hm⟩ := hpar
        omega
    exact (Nat.totient_eq_iff_prime (by omega)).1 htot'
  · intro hp
    rw [subCycles]
    rw [Finset.card_eq_zero, Finset.filter_eq_empty_iff]
    intro k hk
    rw [Finset.mem_Icc] at hk
    simp only [not_not]
    refine (Nat.Prime.coprime_iff_not_dvd hp).2 ?_
    intro hdvd
    have hle : n ≤ k := Nat.le_of_dvd (by omega) hdvd
    have hhalf : n / 2 < n := Nat.div_lt_self (by omega) (by norm_num)
    omega

end GLM.Totient
