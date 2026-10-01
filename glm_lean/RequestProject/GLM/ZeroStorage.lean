import RequestProject.GLM.Shortcut.Leech
import RequestProject.GLM.Tower

/-!
# Generated, not stored — what the zero-storage substrate really produces

`glm_zero_storage_substrate_v3.txt` proposes replacing the substrate's stored
tables by generators: the Leech lattice is to be re-derived from a
"Construction A → B → C" sieve at the moment of the snap, and a real number is
to be held as the dyadic tower `π_n(q) = ⌊q · 2ⁿ⌋` rather than as digits.  This
file checks both proposals against the definitions already formalised here
(`GLM.LatticeShortcut.IsLeech`, `GLM.Info.dyadicLayer`).

## The sieve (§1)

The proposed sieve keeps a 24-tuple `x` when

* every coordinate has the same residue **mod 4** — `∃ m, ∀ i, 4 ∣ x i - m`; and
* `∑ x ≡ 4m (mod 8)`.

That is `V3Sieve` below.  The results are:

* `v3Sieve_sound` — everything the sieve keeps really is a Leech point, so the
  sieve never invents lattice points;
* `v3Sieve_iff` — but it keeps *exactly* the Leech points whose mod-4 Golay
  word is trivial: `V3Sieve x ↔ IsLeech x ∧ UniformMod4 x`.  The Golay
  condition of the real construction is not "all coordinates agree mod 4"; it
  is "the coordinates that disagree form a **codeword**", and the sieve has
  replaced a 4096-word condition by its two trivial cases;
* `v3Sieve_zero`, `v3Sieve_add`, `v3Sieve_neg` — the survivors do form a
  lattice, a genuine sublattice of `Λ₂₄`; the sieve is a well-defined object,
  just not the one advertised;
* `octadVec_isLeech`, `octadVec_not_v3Sieve`, `octadVec_normSq` — an explicit
  minimal vector (`2` on the octad `{0,1,2,3,4,17,21,23}`, norm² `32`) that the
  sieve throws away.  Of the 196 560 minimal vectors the sieve keeps 1152; the
  count is measured in `glm_universal.substrate.generative`;
* `fallbackVec_not_isLeech` — the snap's last-resort branch ("round each
  coordinate to the nearest even integer") returns points outside `Λ₂₄`:
  `(2,2,0²²)` is the witness.  Rounding to even is *not* a Leech snap.

## The tower (§2)

`dyadic_surrogate_error` is the read-out bound that makes "the process is the
number" usable: level `n` pins `q` to a half-open window of width `2⁻ⁿ`, so a
generator plus a level replaces stored digits.  `dyadic_exact_iff_den_pow_two`
says exactly when the tower terminates (iff the denominator is a power of two),
and `dyadic_value_not_strictMono` refutes the script's claim that the tower is
*strictly* increasing: at `q = 1/3` levels `0` and `1` return the same value.
What is strictly increasing is the resolution, not the reading —
`GLM.Info.dyadic_boundary_nonempty` is the true form of that claim.
-/

namespace GLM.ZeroStorage

open GLM.LatticeShortcut

/-! ## §1 The Construction A → B → C sieve -/

/-- The sieve's mod-4 test: every coordinate has the same residue mod 4. -/
def UniformMod4 (x : Fin 24 → ℤ) : Prop := ∃ m : ℤ, ∀ i, (4 : ℤ) ∣ (x i - m)

/-- The membership test of the zero-storage script, transcribed: a uniform
residue `m` mod 4, and the coordinate sum congruent to `4m` mod 8.  (The
script's separate "odd glue" branch subtracts `g = (-3, 1²³)` and repeats the
two tests; on a uniform vector that branch succeeds exactly when these two do,
which is why it does not appear here.) -/
def V3Sieve (x : Fin 24 → ℤ) : Prop :=
  ∃ m : ℤ, (∀ i, (4 : ℤ) ∣ (x i - m)) ∧ (8 : ℤ) ∣ ((∑ i : Fin 24, x i) - 4 * m)

theorem maskOf_const_true : maskOf (fun _ => true) = 2 ^ 24 - 1 := by decide

theorem maskOf_const_false : maskOf (fun _ => false) = 0 := by decide

/-- The zero word is a Golay codeword. -/
theorem golay_zero : IsGolay 0 := ⟨0, by norm_num, by decide⟩

/-- **The sieve is sound**: every vector it keeps is a Leech point. -/
theorem v3Sieve_sound {x : Fin 24 → ℤ} (h : V3Sieve x) : IsLeech x := by
  obtain ⟨m, hu, hs⟩ := h
  refine ⟨m % 2, ?_, ?_, ?_, ?_⟩
  · omega
  · intro i
    have := hu i
    omega
  · by_cases h4 : (4 : ℤ) ∣ (m - m % 2)
    · have hall : (fun i => decide ((4 : ℤ) ∣ (x i - m % 2))) = fun _ => true := by
        funext i
        have h1 := hu i
        simp only [decide_eq_true_eq]
        omega
      rw [hall, maskOf_const_true]
      exact golay_allOnes
    · have hnone : (fun i => decide ((4 : ℤ) ∣ (x i - m % 2))) = fun _ => false := by
        funext i
        have h1 := hu i
        simp only [decide_eq_false_iff_not]
        omega
      rw [hnone, maskOf_const_false]
      exact golay_zero
  · omega

/-- Conversely, a Leech point with a uniform mod-4 residue passes the sieve. -/
theorem v3Sieve_of_isLeech {x : Fin 24 → ℤ} (h : IsLeech x) (hu : UniformMod4 x) :
    V3Sieve x := by
  obtain ⟨m, hm⟩ := hu
  obtain ⟨m₀, hm₀, hpar, -, hsum⟩ := h
  refine ⟨m, hm, ?_⟩
  have h0 := hm ⟨0, by norm_num⟩
  have hp0 := hpar ⟨0, by norm_num⟩
  -- `m` and `m₀` agree mod 2, hence `4m ≡ 4m₀ (mod 8)`.
  have hmm : (2 : ℤ) ∣ (m - m₀) := by omega
  omega

/-- **What the sieve actually generates**: the Leech points whose mod-4 Golay
word is trivial.  The real Construction C admits any of the 4096 codewords; the
sieve admits only the empty word and the all-ones word. -/
theorem v3Sieve_iff {x : Fin 24 → ℤ} : V3Sieve x ↔ IsLeech x ∧ UniformMod4 x := by
  constructor
  · intro h
    exact ⟨v3Sieve_sound h, by obtain ⟨m, hu, -⟩ := h; exact ⟨m, hu⟩⟩
  · rintro ⟨h, hu⟩
    exact v3Sieve_of_isLeech h hu

/-! ### The survivors form a sublattice -/

theorem v3Sieve_zero : V3Sieve (fun _ => 0) := by
  refine ⟨0, fun i => by norm_num, ?_⟩
  simp

theorem v3Sieve_add {x y : Fin 24 → ℤ} (hx : V3Sieve x) (hy : V3Sieve y) :
    V3Sieve (fun i => x i + y i) := by
  obtain ⟨a, hax, has⟩ := hx
  obtain ⟨b, hby, hbs⟩ := hy
  refine ⟨a + b, ?_, ?_⟩
  · intro i
    have h1 := hax i
    have h2 := hby i
    show (4 : ℤ) ∣ (x i + y i - (a + b))
    omega
  · have : (∑ i : Fin 24, (x i + y i)) = (∑ i : Fin 24, x i) + ∑ i : Fin 24, y i :=
      Finset.sum_add_distrib
    rw [this]
    omega

theorem v3Sieve_neg {x : Fin 24 → ℤ} (hx : V3Sieve x) : V3Sieve (fun i => -x i) := by
  obtain ⟨a, hax, has⟩ := hx
  refine ⟨-a, ?_, ?_⟩
  · intro i
    have h1 := hax i
    show (4 : ℤ) ∣ (-x i - -a)
    omega
  · have : (∑ i : Fin 24, -x i) = -∑ i : Fin 24, x i := by
      simp
    rw [this]
    omega

/-! ### A minimal vector the sieve loses -/

/-- The octad `{0,1,2,3,4,17,21,23}` — the Golay codeword `cw 31`. -/
def octad : ℕ := 10616863

theorem octad_isGolay : IsGolay octad := ⟨31, by norm_num, by decide⟩

/-- Twice the indicator of an octad: a minimal vector of `Λ₂₄`. -/
def octadVec : Fin 24 → ℤ := fun i => if bit octad (i : ℕ) = 1 then 2 else 0

theorem octadVec_isLeech : IsLeech octadVec := by
  refine ⟨0, Or.inl rfl, by decide, ?_, by decide⟩
  have : (maskOf fun i => decide ((4 : ℤ) ∣ (octadVec i - 0))) = 6160352 := by decide
  rw [this]
  exact ⟨4064, by norm_num, by decide⟩

theorem octadVec_normSq : normSq24 octadVec = 32 := by decide

/-- The sieve rejects it: coordinate `0` is `2 (mod 4)` and coordinate `5` is
`0 (mod 4)`, so no uniform residue exists. -/
theorem octadVec_not_v3Sieve : ¬ V3Sieve octadVec := by
  rintro ⟨m, hu, -⟩
  have h0 := hu ⟨0, by norm_num⟩
  have h5 := hu ⟨5, by norm_num⟩
  have e0 : octadVec ⟨0, by norm_num⟩ = 2 := by decide
  have e5 : octadVec ⟨5, by norm_num⟩ = 0 := by decide
  rw [e0] at h0
  rw [e5] at h5
  omega

/-- So the sieve is *strictly* weaker than Leech membership. -/
theorem v3Sieve_ne_isLeech : ¬ (∀ x : Fin 24 → ℤ, IsLeech x → V3Sieve x) :=
  fun h => octadVec_not_v3Sieve (h octadVec octadVec_isLeech)

/-! ### The snap's last-resort branch is unsound -/

/-- `(2, 2, 0²²)` — what "round every coordinate to the nearest even integer"
returns for a target near `(2, 2, 0²²)`. -/
def fallbackVec : Fin 24 → ℤ := fun i => if (i : ℕ) < 2 then 2 else 0

/-- Rounding to even is not a Leech snap: this vector is not in `Λ₂₄`.  Its
mod-4 word has weight `22`, and the Golay code has no word of weight `22`. -/
theorem fallbackVec_not_isLeech : ¬ IsLeech fallbackVec := by
  rintro ⟨m, hm, hpar, hgol, -⟩
  rcases hm with rfl | rfl
  · have : (maskOf fun i => decide ((4 : ℤ) ∣ (fallbackVec i - 0))) = 16777212 := by decide
    rw [this] at hgol
    have hw := golay_weight_mem hgol
    have : pop 16777212 = 22 := by decide
    omega
  · have h0 := hpar ⟨0, by norm_num⟩
    have e0 : fallbackVec ⟨0, by norm_num⟩ = 2 := by decide
    rw [e0] at h0
    omega

/-! ### §1b The repaired sieve: what the refined script actually computes

The refined substrate script (`studies/scripts/glm_zero_storage_substrate_v4.py`,
`is_leech`) replaces the uniform mod-4 test by the Golay test, and it does so
*deterministically*: it reads the parity off coordinate `0` rather than
searching for one, then checks three congruences in a single pass.
`RefinedSieve` is that test, transcribed, and `refinedSieve_iff_isLeech` says
it decides exactly `Λ₂₄` — so the script needs no stored shell, and no search
over the two parities either. -/

/-- The membership test of the refined script: `m = x₀ mod 2`, every
coordinate congruent to `m` mod 2, the coordinates congruent to `m` mod 4
forming a Golay codeword, and `∑ x ≡ 4m (mod 8)`. -/
def RefinedSieve (x : Fin 24 → ℤ) : Prop :=
  (∀ i, (2 : ℤ) ∣ (x i - x 0 % 2)) ∧
    IsGolay (maskOf fun i => decide ((4 : ℤ) ∣ (x i - x 0 % 2))) ∧
    (8 : ℤ) ∣ ((∑ i : Fin 24, x i) - 4 * (x 0 % 2))

/-- **The repaired sieve is exactly Leech membership.**  The existential over
the parity in `IsLeech` is redundant: coordinate `0` determines it, so the
refined script's single pass decides `Λ₂₄` with no search and no table. -/
theorem refinedSieve_iff_isLeech {x : Fin 24 → ℤ} : RefinedSieve x ↔ IsLeech x := by
  constructor
  · rintro ⟨hpar, hgol, hsum⟩
    exact ⟨x 0 % 2, by omega, hpar, hgol, hsum⟩
  · rintro ⟨m, hm, hpar, hgol, hsum⟩
    have h0 := hpar 0
    have hmeq : m = x 0 % 2 := by rcases hm with rfl | rfl <;> omega
    subst hmeq
    exact ⟨hpar, hgol, hsum⟩

/-! ## §2 The dyadic tower as a read-out -/

open GLM.Info

/-- **The read-out bound.**  Level `n` of the tower pins `q` to a half-open
window of width `2⁻ⁿ`: the generator plus the level replaces stored digits. -/
theorem dyadic_surrogate_error (q : ℚ) (n : ℕ) :
    0 ≤ q - (⌊q * 2 ^ n⌋ : ℚ) / 2 ^ n ∧ q - (⌊q * 2 ^ n⌋ : ℚ) / 2 ^ n < 1 / (2 : ℚ) ^ n := by
  have h2 : (0 : ℚ) < 2 ^ n := by positivity
  have hle : (⌊q * 2 ^ n⌋ : ℚ) ≤ q * 2 ^ n := Int.floor_le _
  have hlt : q * 2 ^ n < (⌊q * 2 ^ n⌋ : ℚ) + 1 := Int.lt_floor_add_one _
  constructor
  · rw [sub_nonneg, div_le_iff₀ h2]
    linarith
  · rw [sub_lt_iff_lt_add, ← add_div, lt_div_iff₀ h2]
    linarith

/-- **The tower terminates exactly on the dyadic rationals.**  For every other
rational the ladder is genuinely infinite — which is the script's claim, made
precise. -/
theorem dyadic_exact_iff_den_pow_two (q : ℚ) :
    (∃ n : ℕ, ((⌊q * 2 ^ n⌋ : ℚ)) / 2 ^ n = q) ↔ ∃ k : ℕ, q.den = 2 ^ k := by
  constructor
  · rintro ⟨n, hn⟩
    have hq : q = Rat.divInt (⌊q * 2 ^ n⌋) ((2 : ℤ) ^ n) := by
      rw [Rat.divInt_eq_div]
      push_cast
      exact hn.symm
    have hdvd : ((q.den : ℤ)) ∣ (2 : ℤ) ^ n := by
      conv_lhs => rw [hq]
      exact Rat.den_dvd _ _
    have hdvd' : q.den ∣ 2 ^ n := Int.ofNat_dvd.mp (by exact_mod_cast hdvd)
    obtain ⟨k, -, hk⟩ := (Nat.dvd_prime_pow Nat.prime_two).1 hdvd'
    exact ⟨k, hk⟩
  · rintro ⟨k, hk⟩
    refine ⟨k, ?_⟩
    have hden : ((q.den : ℚ)) = 2 ^ k := by rw [hk]; push_cast; ring
    have hnum : q * 2 ^ k = (q.num : ℚ) := by rw [← hden, Rat.mul_den_eq_num]
    rw [hnum, Int.floor_intCast, ← hden, Rat.num_div_den]

/-- **The reading is not strictly increasing.**  At `q = 1/3` the level-0 and
level-1 readings agree, so the script's "strictly increasing ladder" is a
statement about resolutions, not about values. -/
theorem dyadic_value_not_strictMono :
    ⌊(1 / 3 : ℚ) * 2 ^ (0 : ℕ)⌋ = ⌊(1 / 3 : ℚ) * 2 ^ (1 : ℕ)⌋ := by
  norm_num

/-- What *is* monotone: on nonnegative carriers the reading never goes down. -/
theorem dyadic_value_mono {q : ℚ} (hq : 0 ≤ q) (n : ℕ) :
    ⌊q * 2 ^ n⌋ ≤ ⌊q * 2 ^ (n + 1)⌋ := by
  apply Int.floor_le_floor
  have h2 : (0 : ℚ) < 2 ^ n := by positivity
  have hstep : (2 : ℚ) ^ (n + 1) = 2 ^ n * 2 := by ring
  rw [hstep]
  nlinarith

end GLM.ZeroStorage
