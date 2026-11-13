import RequestProject.Decoder

/-!
# The substrate's `snap_to_codeword`, and why "even quantisation" was never evidence

The engine shipped in `ubp_unified_v5.py` corrects error patterns of Hamming
weight `≤ 3` and otherwise returns its input unchanged:

```python
def snap_to_codeword(v):        # GolayCodeEngine
    s = syndrome(v)
    if s == 0: return v
    if s in table_of_leaders_of_weight_le_3: return v ^ leader[s]
    return v                    # <- not a codeword
```

`legacySnap` below is that function.  The published directory reports
"`d² ∈ 2ℤ`, 100 %" as an empirical *lattice* law of the deep-integer walks.
It is neither empirical nor about the walks:

* the Golay code is doubly even, so Hamming-weight parity is constant on every
  coset (`pop_parity_of_coset`);
* the cosets the legacy engine fails on are exactly those whose leader has
  weight `4`, which is even;
* hence **every** output of `legacySnap` has even weight
  (`legacySnap_even_weight`), and therefore **every** jump norm between two
  such states is even (`legacy_even_quantisation`) — for any encoder, any
  integers, primes or not.

With the complete decoder of `RequestProject.Decoder` the true law is the
strictly stronger `4 ∣ d²` (`RequestProject.Leech.golay_step_quantized`),
and `legacy_d2_not_div_four` exhibits a legacy transition with `d² = 2`, which
is impossible between genuine codewords.
-/

namespace LatticeShortcut

/-! ### Weight parity -/

/-- Hamming weight parity is additive under `XOR`. -/
theorem pop_xor_parity (a b : ℕ) : pop (a ^^^ b) % 2 = (pop a + pop b) % 2 := by
  have h := pop_xor_add a b
  omega

/-- Weight parity is constant on the cosets of the Golay code (the code is
doubly even). -/
theorem pop_parity_of_coset {c : ℕ} (hc : IsGolay c) (v : ℕ) :
    pop (v ^^^ c) % 2 = pop v % 2 := by
  have h4 : 4 ∣ pop c := golay_weight_div_four hc
  have h := pop_xor_parity v c
  omega

/-! ### The substrate's engine -/

/-- The substrate's `snap_to_codeword`: correct the error only when the coset
leader has weight `≤ 3`, otherwise return the input unchanged. -/
def legacySnap (v : ℕ) : ℕ :=
  if pop (leader (syn v)) ≤ 3 then v ^^^ leader (syn v) else v

/-- When it does correct, the legacy engine agrees with the complete decoder. -/
theorem legacySnap_eq_decode {v : ℕ} (h : pop (leader (syn v)) ≤ 3) :
    legacySnap v = decode v := by
  simp [legacySnap, decode, h]

/-- Every state produced by the legacy engine has **even Hamming weight** —
whether or not it is a codeword. -/
theorem legacySnap_even_weight {v : ℕ} (hv : v < 2 ^ 24) :
    pop (legacySnap v) % 2 = 0 := by
  have hgolay : IsGolay (decode v) := decode_isGolay hv
  have hdist : pop (v ^^^ decode v) ≤ 4 := decode_dist_le_four v hv
  have hlead : v ^^^ decode v = leader (syn v) := by
    simp [decode]
  have h4 : 4 ∣ pop (decode v) := golay_weight_div_four hgolay
  by_cases h : pop (leader (syn v)) ≤ 3
  · -- the corrected word is a codeword, hence has weight divisible by 4
    rw [legacySnap_eq_decode h]
    omega
  · -- otherwise the coset leader has weight exactly 4, so `v` itself is even
    have hv4 : pop (leader (syn v)) = 4 := by rw [← hlead] at h ⊢; omega
    have hpar : pop (v ^^^ decode v) % 2 = (pop v + pop (decode v)) % 2 :=
      pop_xor_parity v (decode v)
    have : legacySnap v = v := by simp [legacySnap, h]
    rw [this]
    rw [hlead] at hpar
    omega

/-- **The "100 % even quantisation" of the published directory.**  Any two
states produced by the substrate's snap are at even Hamming distance, so every
jump norm `d² = ‖Δv‖²` is even.  No hypothesis on the integers, the encoder or
primality is used: it is a parity property of Golay cosets. -/
theorem legacy_even_quantisation {a b : ℕ} (ha : a < 2 ^ 24) (hb : b < 2 ^ 24) :
    pop (legacySnap a ^^^ legacySnap b) % 2 = 0 := by
  have h := pop_xor_parity (legacySnap a) (legacySnap b)
  have ha' := legacySnap_even_weight ha
  have hb' := legacySnap_even_weight hb
  omega

/-- The legacy engine really does leave non-codewords behind: `15` is at
distance `4` from the code, so `legacySnap 15 = 15 ∉ Golay`. -/
theorem legacySnap_not_codeword : legacySnap 15 = 15 ∧ ¬ IsGolay 15 := by
  refine ⟨?_, substrate_snap_fails.1⟩
  have h : ¬ pop (leader (syn 15)) ≤ 3 := by decide +kernel
  simp [legacySnap, h]

/-- Even quantisation is strictly weaker than the corrected law `4 ∣ d²`:
here is a legacy transition whose jump norm is `2`, a value impossible between
two genuine Golay codewords. -/
theorem legacy_d2_not_div_four :
    pop (legacySnap 15 ^^^ legacySnap 23) = 2 := by decide +kernel

end LatticeShortcut
