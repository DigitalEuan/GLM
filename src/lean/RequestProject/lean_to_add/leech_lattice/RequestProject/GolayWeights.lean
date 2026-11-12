import RequestProject.Golay

/-!
# Exhaustive verification of the Golay weight enumerator

All 4096 codewords produced by the substrate's generator matrix are enumerated
by the kernel and their Hamming weights computed.  This establishes that the
code really is the extended binary Golay code `[24,12,8]`:

* `LatticeShortcut.golay_weight_distribution` — weight enumerator
  `1 + 759 x⁸ + 2576 x¹² + 759 x¹⁶ + x²⁴`;
* `LatticeShortcut.golay_weight_div_four` — the code is doubly even;
* `LatticeShortcut.golay_min_dist` — minimum distance `8`;
* `LatticeShortcut.isGolay_iff` — codeword recognition is an `O(1)` test.
-/

namespace LatticeShortcut

set_option maxRecDepth 10000
set_option maxHeartbeats 2000000

/-- Exhaustive check of the weight enumerator of the code:
`1 + 759 x⁸ + 2576 x¹² + 759 x¹⁶ + x²⁴`. -/
theorem golay_weight_distribution :
    (List.range 4096).countP (fun m => pop (cw m) == 0) = 1 ∧
    (List.range 4096).countP (fun m => pop (cw m) == 8) = 759 ∧
    (List.range 4096).countP (fun m => pop (cw m) == 12) = 2576 ∧
    (List.range 4096).countP (fun m => pop (cw m) == 16) = 759 ∧
    (List.range 4096).countP (fun m => pop (cw m) == 24) = 1 := by
  refine ⟨by decide +kernel, by decide +kernel, by decide +kernel, by decide +kernel,
    by decide +kernel⟩

theorem cw_weight_check :
    ((List.range 4096).all fun m =>
      decide (pop (cw m) = 0 ∨ pop (cw m) = 8 ∨ pop (cw m) = 12 ∨ pop (cw m) = 16 ∨
        pop (cw m) = 24)) = true := by decide +kernel

/-- Every codeword has weight `0, 8, 12, 16` or `24`. -/
theorem cw_weight_mem (m : ℕ) (h : m < 4096) :
    pop (cw m) = 0 ∨ pop (cw m) = 8 ∨ pop (cw m) = 12 ∨ pop (cw m) = 16 ∨
      pop (cw m) = 24 := by
  have h2 := List.all_eq_true.1 cw_weight_check m (List.mem_range.mpr h)
  simpa using h2

theorem golay_weight_mem {c : ℕ} (hc : IsGolay c) :
    pop c = 0 ∨ pop c = 8 ∨ pop c = 12 ∨ pop c = 16 ∨ pop c = 24 := by
  obtain ⟨m, hm, rfl⟩ := hc; exact cw_weight_mem m hm

/-- The code is doubly even. -/
theorem golay_weight_div_four {c : ℕ} (hc : IsGolay c) : 4 ∣ pop c := by
  rcases golay_weight_mem hc with h | h | h | h | h <;> rw [h] <;> decide

/-- Systematic encoding: the information bits of `cw m` are `m` itself. -/
theorem cw_mod_check : ((List.range 4096).all fun m => cw m % 4096 == m) = true := by
  decide +kernel

theorem cw_mod (m : ℕ) (h : m < 4096) : cw m % 4096 = m := by
  have h2 := List.all_eq_true.1 cw_mod_check m (List.mem_range.mpr h)
  simpa using h2

/-- Recognising codewords is a constant-time test: a 24-bit word is a codeword
iff re-encoding its information part reproduces it. -/
theorem isGolay_iff (c : ℕ) : IsGolay c ↔ cw (c % 4096) = c := by
  constructor
  · rintro ⟨m, hm, rfl⟩
    rw [cw_mod m hm]
  · intro h
    exact ⟨c % 4096, Nat.mod_lt _ (by norm_num), h⟩

/-- **Minimum distance 8.** -/
theorem golay_min_dist {a b : ℕ} (ha : IsGolay a) (hb : IsGolay b) (hab : a ≠ b) :
    8 ≤ pop (a ^^^ b) := by
  have hx : IsGolay (a ^^^ b) := golay_xor_closed ha hb
  have hne : a ^^^ b ≠ 0 := fun h => hab (Nat.xor_eq_zero_iff.1 h)
  have hpop : pop (a ^^^ b) ≠ 0 := fun h => hne ((pop_eq_zero_iff _ (golay_lt hx)).1 h)
  rcases golay_weight_mem hx with h | h | h | h | h <;> omega

/-- Intersections of codewords are even. -/
theorem golay_inter_even {a b : ℕ} (ha : IsGolay a) (hb : IsGolay b) :
    pop (a &&& b) % 2 = 0 := by
  have h4a := golay_weight_div_four ha
  have h4b := golay_weight_div_four hb
  have h4x := golay_weight_div_four (golay_xor_closed ha hb)
  have hie := pop_xor_add a b
  omega

/-- Difference sets of two codewords have even size: `|a \ b|` is even.
This is what makes doubled Golay differences land in the Leech lattice. -/
theorem golay_sdiff_even {a b : ℕ} (ha : IsGolay a) (hb : IsGolay b) :
    (pop a - pop (a &&& b)) % 2 = 0 := by
  have h4a := golay_weight_div_four ha
  have hi := golay_inter_even ha hb
  have hle := pop_and_le a b
  omega

end LatticeShortcut
