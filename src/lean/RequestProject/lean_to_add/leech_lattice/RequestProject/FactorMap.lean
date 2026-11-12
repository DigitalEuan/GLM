import RequestProject.Shortcut
import RequestProject.Substrate

/-!
# The factor encoder actually used by the generator, and reproduction of the
# published "Deep Interfacial Sequence"

`generate_shortcut_directory_standalone.py` does **not** use the documented
bit-shift channels for every integer.  A prime `n` is mapped through
`x = n & 0xFF`, `y = (n >>> 8) & 0xFF`, `z = (n >>> 16) & 0xFF`, but a composite
is mapped through its factorisation:

```
x = p₁^e₁,   y = p₂^e₂,   z = ∏_{i ≥ 3} pᵢ^eᵢ      (each taken mod 256)
```

`interfacialFactorStates` lists the resulting 24-bit words for
`1000033 … 1000050`, written so that the channel values are visible as the
prime powers they are; `interfacial_factorisations` certifies that those really
are the factorisations (each integer is the stated product of powers of
increasing primes).

With that table, the published jump norms are reproduced exactly
(`legacyD2_interfacial_reproduces_directory`), and the corrected pipeline is
evaluated on the same walk (`snapD2_interfacial_factor`).  This is what makes
the point of the audit precise: the tabulated norms `8,10,12,14` for
*consecutive* integers are real output of the generator, but they measure the
distance between the factorisations of `n` and `n+1`, not a lattice property of
adjacent integers.
-/

namespace LatticeShortcut

set_option maxRecDepth 8000
set_option maxHeartbeats 2000000

/-- A 24-bit state assembled from three (unreduced) channel values. -/
def encCh (x y z : ℕ) : ℕ :=
  rev8 (gray8 (x % 256)) + 256 * rev8 (gray8 (y % 256)) + 65536 * rev8 (gray8 (z % 256))

/-- The documented bit-shift map is the special case of three byte channels. -/
theorem grayBytes_eq_encCh (n : ℕ) :
    grayBytes n = encCh (n % 256) (n / 256 % 256) (n / 65536 % 256) := by
  simp [grayBytes, encCh]

/-- The states of `1000033 … 1000050` under the generator's encoder. -/
def interfacialFactorStates : List ℕ :=
  [encCh 97 66 15,
   encCh (2) (7) (61 * 1171),
   encCh (3 ^ 2) (5) (71 * 313),
   encCh (2 ^ 2) (29) (37 * 233),
   encCh 101 66 15,
   encCh (2) (3) (13 * 12821),
   encCh 103 66 15,
   encCh (2 ^ 3) (5) (23 * 1087),
   encCh (3) (7 ^ 2) (6803),
   encCh (2) (17) (67 * 439),
   encCh (11) (229) (397),
   encCh (2 ^ 2) (3 ^ 2) (27779),
   encCh (5) (200009) (1),
   encCh (2) (19) (26317),
   encCh (3) (333349) (1),
   encCh (2 ^ 4) (7) (8929),
   encCh (353) (2833) (1),
   encCh (2) (3) (5 ^ 2 * 59 * 113)]

/-- The channel values above are the genuine prime factorisations. -/
theorem interfacial_factorisations :
    (Nat.Prime 1000033) ∧
      (1000034 = 2 * 7 * 61 * 1171 ∧ Nat.Prime 2 ∧ Nat.Prime 7 ∧ Nat.Prime 61 ∧ Nat.Prime 1171 ∧ (2 : ℕ) < 7 ∧ (7 : ℕ) < 61 ∧ (61 : ℕ) < 1171) ∧
      (1000035 = 3 ^ 2 * 5 * 71 * 313 ∧ Nat.Prime 3 ∧ Nat.Prime 5 ∧ Nat.Prime 71 ∧ Nat.Prime 313 ∧ (3 : ℕ) < 5 ∧ (5 : ℕ) < 71 ∧ (71 : ℕ) < 313) ∧
      (1000036 = 2 ^ 2 * 29 * 37 * 233 ∧ Nat.Prime 2 ∧ Nat.Prime 29 ∧ Nat.Prime 37 ∧ Nat.Prime 233 ∧ (2 : ℕ) < 29 ∧ (29 : ℕ) < 37 ∧ (37 : ℕ) < 233) ∧
      (Nat.Prime 1000037) ∧
      (1000038 = 2 * 3 * 13 * 12821 ∧ Nat.Prime 2 ∧ Nat.Prime 3 ∧ Nat.Prime 13 ∧ Nat.Prime 12821 ∧ (2 : ℕ) < 3 ∧ (3 : ℕ) < 13 ∧ (13 : ℕ) < 12821) ∧
      (Nat.Prime 1000039) ∧
      (1000040 = 2 ^ 3 * 5 * 23 * 1087 ∧ Nat.Prime 2 ∧ Nat.Prime 5 ∧ Nat.Prime 23 ∧ Nat.Prime 1087 ∧ (2 : ℕ) < 5 ∧ (5 : ℕ) < 23 ∧ (23 : ℕ) < 1087) ∧
      (1000041 = 3 * 7 ^ 2 * 6803 ∧ Nat.Prime 3 ∧ Nat.Prime 7 ∧ Nat.Prime 6803 ∧ (3 : ℕ) < 7 ∧ (7 : ℕ) < 6803) ∧
      (1000042 = 2 * 17 * 67 * 439 ∧ Nat.Prime 2 ∧ Nat.Prime 17 ∧ Nat.Prime 67 ∧ Nat.Prime 439 ∧ (2 : ℕ) < 17 ∧ (17 : ℕ) < 67 ∧ (67 : ℕ) < 439) ∧
      (1000043 = 11 * 229 * 397 ∧ Nat.Prime 11 ∧ Nat.Prime 229 ∧ Nat.Prime 397 ∧ (11 : ℕ) < 229 ∧ (229 : ℕ) < 397) ∧
      (1000044 = 2 ^ 2 * 3 ^ 2 * 27779 ∧ Nat.Prime 2 ∧ Nat.Prime 3 ∧ Nat.Prime 27779 ∧ (2 : ℕ) < 3 ∧ (3 : ℕ) < 27779) ∧
      (1000045 = 5 * 200009 ∧ Nat.Prime 5 ∧ Nat.Prime 200009 ∧ (5 : ℕ) < 200009) ∧
      (1000046 = 2 * 19 * 26317 ∧ Nat.Prime 2 ∧ Nat.Prime 19 ∧ Nat.Prime 26317 ∧ (2 : ℕ) < 19 ∧ (19 : ℕ) < 26317) ∧
      (1000047 = 3 * 333349 ∧ Nat.Prime 3 ∧ Nat.Prime 333349 ∧ (3 : ℕ) < 333349) ∧
      (1000048 = 2 ^ 4 * 7 * 8929 ∧ Nat.Prime 2 ∧ Nat.Prime 7 ∧ Nat.Prime 8929 ∧ (2 : ℕ) < 7 ∧ (7 : ℕ) < 8929) ∧
      (1000049 = 353 * 2833 ∧ Nat.Prime 353 ∧ Nat.Prime 2833 ∧ (353 : ℕ) < 2833) ∧
      (1000050 = 2 * 3 * 5 ^ 2 * 59 * 113 ∧ Nat.Prime 2 ∧ Nat.Prime 3 ∧ Nat.Prime 5 ∧ Nat.Prime 59 ∧ Nat.Prime 113 ∧ (2 : ℕ) < 3 ∧ (3 : ℕ) < 5 ∧ (5 : ℕ) < 59 ∧ (59 : ℕ) < 113) := by
  norm_num

/-- **Reproduction of the published catalogue.**  With the substrate's
weight-`≤ 3` corrector, the jump norms of the "Deep Interfacial Sequence" are
exactly the ones tabulated in `lattice_shortcut_directory_standalone.json`. -/
theorem legacyD2_interfacial_reproduces_directory :
    List.zipWith (fun a b => pop (legacySnap a ^^^ legacySnap b))
      interfacialFactorStates interfacialFactorStates.tail
      = [10, 8, 12, 10, 8, 10, 12, 14, 10, 12, 8, 8, 10, 10, 12, 12, 14] := by decide +kernel

/-- Every one of those norms is even — an instance of `legacy_even_quantisation`,
not of any property of the integers `1000033 … 1000050`. -/
theorem legacyD2_interfacial_even :
    ∀ d ∈ List.zipWith (fun a b => pop (legacySnap a ^^^ legacySnap b))
      interfacialFactorStates interfacialFactorStates.tail, d % 2 = 0 := by
  rw [legacyD2_interfacial_reproduces_directory]; decide

/-- **The corrected pipeline on the same walk**: with complete decoding every
state is a codeword and every jump norm is a multiple of `4`. -/
theorem snapD2_interfacial_factor :
    List.zipWith (fun a b => pop (decode a ^^^ decode b))
      interfacialFactorStates interfacialFactorStates.tail
      = [16, 8, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 8, 8, 12, 12, 12] := by decide +kernel

theorem snapD2_interfacial_factor_quantized :
    ∀ d ∈ List.zipWith (fun a b => pop (decode a ^^^ decode b))
      interfacialFactorStates interfacialFactorStates.tail, 4 ∣ d := by
  rw [snapD2_interfacial_factor]; decide

end LatticeShortcut
