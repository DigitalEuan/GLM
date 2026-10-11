import RequestProject.GLM.Shortcut.Leech

/-!
# Norm 256 and the hex colour (Phase 127)

The power-of-two family of rungs (`GLM.NormFamily`) had no rung at minimum
norm 256 that survived its retirement rule.  This file holds what Phase 127
proves about the two kinds of candidate it tried there.

## §1 A rotation by `√2` (generic)

Let `P` be a fixed-point-free involution of the coordinates and `e` a sign
vector that takes opposite values on the two coordinates of every pair
(`e i * e (P i) = -1`).  The signed permutation `rot x j = e (P j) * x (P j)`
satisfies

* `rot_rot` — `rot (rot x) = -x`, so `rot` is a square root of `-1`;
* `inner_rot_self` — `x` is orthogonal to `rot x`;
* `normSq_add_rot` — `‖x + rot x‖² = 2 ‖x‖²`, so `1 + rot` is `√2` times an
  isometry;
* `sub_rot_add_rot` — `(1 - rot)(1 + rot) = 2`, so `1 + rot` is inverted by
  `(1 - rot)/2`;
* `min_norm_doubles` — `(1 + rot) L` has twice the minimum norm of `L`;
* `nearest_transfer` — the nearest point of `(1 + rot) L` to `y` is `1 + rot`
  applied to the nearest point of `L` to `(y - rot y)/2`, which is how the
  candidate's quantiser is built from the Leech quantiser.

## §2 The concrete rotation of the Leech lattice

`hexP` (a fixed-point-free involution found by search) and the dodecad
`hexS = 466837` (a transversal of its twelve pairs) give a rotation `hexRot`
with

* `hexP_invol`, `hexP_ne`, `hexSign_pair` — the hypotheses of §1;
* `hexS_golay` and `golay_perm_closed` — the sign set is a codeword and `hexP`
  is an automorphism of the Golay code;
* `hexRot_isLeech` — `hexRot` maps the Leech lattice to itself;
* `rotLeech_min_norm` — every nonzero vector of the norm-256 candidate
  `(1 + hexRot)(2Λ₂₄)` has squared norm at least `256`.

## §3 The hex-digit reading

* `floor_bucket_nearest` — reading a coordinate by its hex bucket
  `⌊v / 16⌋` is the nearest-point map of the coset `16ℤ + 8`;
* `hex_counts` — `16² = 256` (one colour channel), `16³ = 4096` (the Golay
  code, and the short `#RGB` form) and `16⁶ = 2²⁴` (a hex colour, and the
  number of classes of `Λ₂₄ / 2Λ₂₄`).
-/

namespace GLM.HexRung

open GLM.LatticeShortcut

/-! ## §1 A rotation by `√2` -/

section Generic

variable {n : ℕ} {R : Type*} [CommRing R]

/-- The signed permutation `x ↦ (j ↦ e (P j) * x (P j))`. -/
def rot (P : Fin n → Fin n) (e : Fin n → R) (x : Fin n → R) : Fin n → R :=
  fun j => e (P j) * x (P j)

/-- Squared norm. -/
def nsq (x : Fin n → R) : R := ∑ i, x i ^ 2

/-- Inner product. -/
def dot (x y : Fin n → R) : R := ∑ i, x i * y i

variable {P : Fin n → Fin n} {e : Fin n → R}

theorem rot_add (x y : Fin n → R) : rot P e (x + y) = rot P e x + rot P e y := by
  funext j; simp [rot, mul_add]

theorem rot_sub (x y : Fin n → R) : rot P e (x - y) = rot P e x - rot P e y := by
  funext j; simp [rot, mul_sub]

theorem rot_smul (c : R) (x : Fin n → R) : rot P e (c • x) = c • rot P e x := by
  funext j; simp [rot]; ring

theorem rot_zero : rot P e (0 : Fin n → R) = 0 := by
  funext j; simp [rot]

/-- The partner of a coordinate carries the opposite sign. -/
theorem sign_partner (hsq : ∀ i, e i * e i = 1) (hpair : ∀ i, e i * e (P i) = -1)
    (i : Fin n) : e (P i) = - e i := by
  have h := hpair i
  calc e (P i) = (e i * e i) * e (P i) := by rw [hsq i, one_mul]
    _ = e i * (e i * e (P i)) := by ring
    _ = - e i := by rw [h]; ring

theorem rot_rot (hinv : ∀ i, P (P i) = i) (hpair : ∀ i, e i * e (P i) = -1)
    (x : Fin n → R) : rot P e (rot P e x) = -x := by
  funext j
  simp only [rot, Pi.neg_apply, hinv]
  have h := hpair (P j)
  rw [hinv] at h
  calc e (P j) * (e j * x j) = (e (P j) * e j) * x j := by ring
    _ = - x j := by rw [h]; ring

/-- Reindexing a sum by an involution. -/
theorem sum_comp_invol (hinv : ∀ i, P (P i) = i) (f : Fin n → R) :
    ∑ j, f (P j) = ∑ j, f j := by
  have hbij : Function.Bijective P :=
    Function.Involutive.bijective (f := P) hinv
  exact Fintype.sum_bijective P hbij _ _ (fun _ => rfl)

theorem inner_rot_self [NoZeroDivisors R] [CharZero R]
    (hinv : ∀ i, P (P i) = i) (hsq : ∀ i, e i * e i = 1)
    (hpair : ∀ i, e i * e (P i) = -1) (x : Fin n → R) :
    dot x (rot P e x) = 0 := by
  unfold dot rot
  have h1 : ∑ j, x j * (e (P j) * x (P j)) = ∑ j, x (P j) * (e j * x j) := by
    rw [← sum_comp_invol hinv (fun j => x j * (e (P j) * x (P j)))]
    simp [hinv]
  have h2 : ∑ j, x (P j) * (e j * x j) = - ∑ j, x j * (e (P j) * x (P j)) := by
    rw [← Finset.sum_neg_distrib]
    refine Finset.sum_congr rfl fun j _ => ?_
    rw [sign_partner hsq hpair j]; ring
  have h3 : (2 : R) * ∑ j, x j * (e (P j) * x (P j)) = 0 := by
    rw [two_mul]; nth_rewrite 2 [h1]; rw [h2]; ring
  rcases mul_eq_zero.mp h3 with h | h
  · exact absurd h two_ne_zero
  · exact h

theorem nsq_rot (hinv : ∀ i, P (P i) = i) (hsq : ∀ i, e i * e i = 1)
    (x : Fin n → R) : nsq (rot P e x) = nsq x := by
  unfold nsq rot
  have : ∀ j, (e (P j) * x (P j)) ^ 2 = x (P j) ^ 2 := fun j => by
    have := hsq (P j)
    calc (e (P j) * x (P j)) ^ 2 = (e (P j) * e (P j)) * x (P j) ^ 2 := by ring
      _ = x (P j) ^ 2 := by rw [this, one_mul]
  simp only [this]
  exact sum_comp_invol hinv (fun j => x j ^ 2)

theorem nsq_add (x y : Fin n → R) : nsq (x + y) = nsq x + 2 * dot x y + nsq y := by
  unfold nsq dot
  simp only [Pi.add_apply, Finset.mul_sum, ← Finset.sum_add_distrib]
  refine Finset.sum_congr rfl fun i _ => by ring

theorem normSq_add_rot [NoZeroDivisors R] [CharZero R]
    (hinv : ∀ i, P (P i) = i) (hsq : ∀ i, e i * e i = 1)
    (hpair : ∀ i, e i * e (P i) = -1) (x : Fin n → R) :
    nsq (x + rot P e x) = 2 * nsq x := by
  rw [nsq_add, inner_rot_self hinv hsq hpair, nsq_rot hinv hsq]; ring

theorem sub_rot_add_rot (hinv : ∀ i, P (P i) = i) (hpair : ∀ i, e i * e (P i) = -1)
    (x : Fin n → R) :
    (x + rot P e x) - rot P e (x + rot P e x) = (2 : R) • x := by
  rw [rot_add, rot_rot hinv hpair]
  funext j; simp; ring

end Generic

/-- `1 + rot` doubles the minimum norm of any set of integer vectors. -/
theorem min_norm_doubles {n : ℕ} {P : Fin n → Fin n} {e : Fin n → ℤ}
    (hinv : ∀ i, P (P i) = i) (hsq : ∀ i, e i * e i = 1)
    (hpair : ∀ i, e i * e (P i) = -1)
    {L : Set (Fin n → ℤ)} {m : ℤ} (hL : ∀ x ∈ L, x ≠ 0 → m ≤ nsq x)
    {x : Fin n → ℤ} (hx : x ∈ L) (hne : x + rot P e x ≠ 0) :
    2 * m ≤ nsq (x + rot P e x) := by
  have hx0 : x ≠ 0 := by
    rintro rfl; exact hne (by rw [rot_zero]; simp)
  rw [normSq_add_rot hinv hsq hpair]
  have := hL x hx hx0
  linarith

/-- Nearest points transfer through `1 + rot`: if `p` is a nearest point of `L`
to `(y - rot y)/2`, then `p + rot p` is a nearest point of `(1 + rot) L` to `y`. -/
theorem nearest_transfer {n : ℕ} {P : Fin n → Fin n} {e : Fin n → ℚ}
    (hinv : ∀ i, P (P i) = i) (hsq : ∀ i, e i * e i = 1)
    (hpair : ∀ i, e i * e (P i) = -1)
    {L : Set (Fin n → ℚ)} (y p : Fin n → ℚ)
    (hnear : ∀ q ∈ L, nsq ((2⁻¹ : ℚ) • (y - rot P e y) - p) ≤
      nsq ((2⁻¹ : ℚ) • (y - rot P e y) - q)) :
    ∀ q ∈ L, nsq (y - (p + rot P e p)) ≤ nsq (y - (q + rot P e q)) := by
  intro q hq
  set z := (2⁻¹ : ℚ) • (y - rot P e y) with hz
  have hy : z + rot P e z = y := by
    have h : y - rot P e y + rot P e (y - rot P e y) = (2 : ℚ) • y := by
      rw [rot_sub, rot_rot hinv hpair]; funext j; simp; ring
    rw [hz, rot_smul, ← smul_add, h, smul_smul]; norm_num
  have key : ∀ w, y - (w + rot P e w) = (z - w) + rot P e (z - w) := by
    intro w; rw [rot_sub]; nth_rewrite 1 [← hy]; abel
  rw [key p, key q, normSq_add_rot hinv hsq hpair, normSq_add_rot hinv hsq hpair]
  have := hnear q hq
  linarith


/-! ## §2 The concrete rotation of the Leech lattice -/

/-- A fixed-point-free involution of the 24 coordinates that is an automorphism
of the Golay code (found by a backtracking search over octads). -/
def hexP : Fin 24 → Fin 24 :=
  ![1, 0, 3, 2, 5, 4, 9, 20, 23, 6, 14, 13, 21, 11, 10, 16, 15, 19, 22, 17, 7, 12, 18, 8]

/-- The sign set: a dodecad meeting every pair of `hexP` once. -/
def hexS : ℕ := 466837

/-- The sign vector: `-1` on `hexS`, `+1` off it. -/
def hexSign (i : Fin 24) : ℤ := if Nat.testBit hexS i then -1 else 1

/-- The rotation of the Leech lattice. -/
def hexRot (x : Fin 24 → ℤ) : Fin 24 → ℤ := rot hexP hexSign x

theorem hexP_invol : ∀ i, hexP (hexP i) = i := by decide

theorem hexP_ne : ∀ i, hexP i ≠ i := by decide

theorem hexSign_sq : ∀ i, hexSign i * hexSign i = 1 := by decide

theorem hexSign_pair : ∀ i, hexSign i * hexSign (hexP i) = -1 := by decide

theorem hexS_golay : IsGolay hexS := ⟨4095 &&& 466837, by decide, by decide⟩

/-- Permute the coordinates of a 24-bit word by `hexP`. -/
def permMask (c : ℕ) : ℕ := maskOf fun j => Nat.testBit c (hexP j)

theorem hexS_pop : pop hexS = 12 := by decide

theorem testBit_maskOf (p : Fin 24 → Bool) (i : Fin 24) :
    Nat.testBit (maskOf p) i = p i := by
  rw [maskOf, Nat.testBit_ofBits_lt p i i.isLt]

theorem golay_zero : IsGolay 0 := ⟨0, by norm_num, by decide⟩

set_option maxRecDepth 100000 in
/-- Every Golay codeword, permuted by `hexP`, is again the codeword of its own
first twelve bits (checked over all 4096 messages). -/
theorem perm_cw_table : ∀ m < 4096, permMask (cw m) = cw (permMask (cw m) % 4096) := by
  decide +kernel

/-- `hexP` is an automorphism of the Golay code. -/
theorem golay_perm_closed {c : ℕ} (h : IsGolay c) : IsGolay (permMask c) := by
  obtain ⟨m, hm, rfl⟩ := h
  exact ⟨_, Nat.mod_lt _ (by norm_num), (perm_cw_table m hm).symm⟩

set_option maxRecDepth 100000 in
/-- `hexS` meets every codeword in an even number of coordinates. -/
theorem hexS_meet_even : ∀ m < 4096,
    (∑ i : Fin 24, if (Nat.testBit hexS i && Nat.testBit (cw m) i) = true
      then (1 : ℤ) else 0) % 2 = 0 := by
  decide +kernel

theorem hexS_card : (∑ i : Fin 24, if Nat.testBit hexS i = true then (1 : ℤ) else 0) = 12 := by
  decide

theorem sign_mul (i : Fin 24) (v : ℤ) :
    hexSign i * v = v - 2 * (if Nat.testBit hexS i = true then v else 0) := by
  unfold hexSign; split_ifs <;> ring

/-- `hexRot` maps the Leech lattice to itself. -/
theorem hexRot_isLeech {x : Fin 24 → ℤ} (hx : IsLeech x) : IsLeech (hexRot x) := by
  obtain ⟨m, hm, hpar, hgol, hsum⟩ := hx
  set c := maskOf fun i => decide ((4 : ℤ) ∣ x i - m) with hc
  have hcbit : ∀ i : Fin 24, Nat.testBit c i = decide ((4 : ℤ) ∣ x i - m) :=
    fun i => testBit_maskOf _ i
  refine ⟨m, hm, ?_, ?_, ?_⟩
  · intro j
    have hp := hpar (hexP j)
    simp only [hexRot, rot, hexSign]
    split_ifs
    · rcases hm with rfl | rfl <;> omega
    · simpa using hp
  · have key : (maskOf fun j => decide ((4 : ℤ) ∣ hexRot x j - m)) =
        permMask (c ^^^ (if m = 1 then hexS else 0)) := by
      unfold permMask
      congr 1
      funext j
      rw [Nat.testBit_xor, hcbit]
      have hp := hpar (hexP j)
      simp only [hexRot, rot, hexSign]
      rcases hm with rfl | rfl
      · by_cases h1 : Nat.testBit hexS (hexP j) = true
        · simp [h1]
        · simp [h1]
      · by_cases h1 : Nat.testBit hexS (hexP j) = true
        · simp only [h1, ↓reduceIte, Bool.xor_true, neg_mul, one_mul, ← decide_not]
          exact decide_eq_decide.mpr (by omega)
        · have h1' : Nat.testBit hexS (hexP j) = false := by simpa using h1
          simp only [h1', ↓reduceIte, Bool.xor_false]
          simp
    rw [key]
    apply golay_perm_closed
    apply golay_xor_closed hgol
    split_ifs
    · exact hexS_golay
    · exact golay_zero
  · obtain ⟨m', hm', hcw⟩ := hgol
    have heven := hexS_meet_even m' hm'
    rw [hcw] at heven
    simp only [hcbit] at heven
    have hrs : ∑ i, hexRot x i = ∑ i, hexSign i * x i :=
      sum_comp_invol hexP_invol (fun i => hexSign i * x i)
    have hsplit : ∑ i, hexSign i * x i =
        ∑ i, x i - 2 * ∑ i : Fin 24, (if Nat.testBit hexS i = true then x i else 0) := by
      simp only [sign_mul, Finset.sum_sub_distrib, Finset.mul_sum]
    set T := ∑ i : Fin 24, (if Nat.testBit hexS i = true then x i else 0) with hT
    set E := ∑ i : Fin 24, (if (Nat.testBit hexS i && decide ((4 : ℤ) ∣ x i - m)) = true
      then (1 : ℤ) else 0) with hE
    have hterm : (4 : ℤ) ∣ ∑ i : Fin 24,
        ((if Nat.testBit hexS i = true then x i else 0)
          - m * (if Nat.testBit hexS i = true then (1 : ℤ) else 0)
          - 2 * ((if Nat.testBit hexS i = true then (1 : ℤ) else 0)
            - (if (Nat.testBit hexS i && decide ((4 : ℤ) ∣ x i - m)) = true
                then (1 : ℤ) else 0))) := by
      apply Finset.dvd_sum
      intro i _
      have hp := hpar i
      by_cases hs : Nat.testBit hexS i = true
      · by_cases h4 : (4 : ℤ) ∣ x i - m
        · simp [hs, h4]
        · simp [hs, h4]; omega
      · simp [hs]
    have hval : ∑ i : Fin 24,
        ((if Nat.testBit hexS i = true then x i else 0)
          - m * (if Nat.testBit hexS i = true then (1 : ℤ) else 0)
          - 2 * ((if Nat.testBit hexS i = true then (1 : ℤ) else 0)
            - (if (Nat.testBit hexS i && decide ((4 : ℤ) ∣ x i - m)) = true
                then (1 : ℤ) else 0))) = T - m * 12 - 2 * (12 - E) := by
      simp only [Finset.sum_sub_distrib, ← Finset.mul_sum, hexS_card, hT, hE]
    rw [hval] at hterm
    rw [hrs, hsplit]
    rcases hm with rfl | rfl <;> omega

/-- The norm-256 candidate: every nonzero `(1 + hexRot) (2 y)` with `y` in the
Leech lattice has squared norm at least 256. -/
theorem rotLeech_min_norm {y : Fin 24 → ℤ} (hy : IsLeech y)
    (hne : (2 • y) + hexRot (2 • y) ≠ 0) :
    256 ≤ normSq24 ((2 • y) + hexRot (2 • y)) := by
  have hL : ∀ x ∈ {x : Fin 24 → ℤ | ∃ y, IsLeech y ∧ x = 2 • y}, x ≠ 0 → 128 ≤ nsq x := by
    rintro x ⟨z, hz, rfl⟩ hx
    have hz0 : z ≠ 0 := by rintro rfl; exact hx (by simp)
    have h32 := leech_min_norm hz hz0
    have : nsq (2 • z) = 4 * normSq24 z := by
      unfold nsq normSq24; rw [Finset.mul_sum]
      refine Finset.sum_congr rfl fun i _ => ?_
      simp only [Pi.smul_apply]; ring
    linarith
  have := min_norm_doubles hexP_invol hexSign_sq hexSign_pair hL ⟨y, hy, rfl⟩ hne
  simpa [nsq, normSq24, hexRot] using this

/-! ## §3 The hex-digit reading -/

/-- The hex bucket `⌊v/16⌋` of a coordinate is the nearest point of the coset
`16ℤ + 8`, ties going up. -/
theorem floor_bucket_nearest (v : ℚ) (k : ℤ) :
    |v - (16 * ⌊v / 16⌋ + 8)| ≤ |v - (16 * k + 8)| := by
  have h1 := Int.floor_le (v / 16)
  have h2 := Int.lt_floor_add_one (v / 16)
  set f := ⌊v / 16⌋
  have hl : |v - (16 * (f : ℚ) + 8)| ≤ 8 := by
    rw [abs_le]; constructor <;> linarith
  rcases lt_trichotomy k f with h | h | h
  · have : (k : ℚ) ≤ f - 1 := by exact_mod_cast Int.le_sub_one_of_lt h
    calc _ ≤ 8 := hl
      _ ≤ v - (16 * k + 8) := by linarith
      _ ≤ _ := le_abs_self _
  · rw [h]
  · have : (f : ℚ) + 1 ≤ k := by exact_mod_cast h
    calc _ ≤ 8 := hl
      _ ≤ -(v - (16 * k + 8)) := by linarith
      _ ≤ _ := neg_le_abs _

theorem hex_counts : 16 ^ 2 = 256 ∧ 16 ^ 3 = 4096 ∧ 16 ^ 6 = 2 ^ 24 := by
  decide

end GLM.HexRung
