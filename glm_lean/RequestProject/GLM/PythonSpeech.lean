module

public import Mathlib

/-!
# Python speech: the facts behind the dialect's substrate operations

The formal half of `studies/PYTHON_SPEECH_STUDY.md`. The Python modules
`glm_universal/reasoning/python_substrate.py` and `python_speech.py` let the
GLM evaluate a small Python dialect on the substrate. This file proves that
the substrate operations they run mean what the payloads say they mean.

* **The sub-register programs.** A lane is the triple `(a, b, t)`, with a
  constant rail `1` available as a control. The programs `andP`, `xorP`,
  `orP`, `notP`, `copyP` are built from Toffoli gates and `andnotP` from one
  Fredkin gate. Started with `t = false`, each leaves its Boolean function on
  the result line (`andP_spec`, `xorP_spec`, `orP_spec`, `notP_spec`,
  `copyP_spec`, `andnotP_spec`). Each is undone by running its gates in
  reverse (`andP_inv` … `andnotP_inv`), so each is a bijection of the eight
  lane states (`andP_bijective` … `andnotP_bijective`): nothing is erased.
* **The register tower.** Bitwise operations on natural numbers act window
  by window: the low `k` bits and the high part of `a ⊕ b`, `a ∧ b`,
  `a ∨ b` are the operations on the low bits and on the high parts
  (`xor_mod_two_pow`, `xor_div_two_pow` and the `and`/`or` versions). With
  `k = 24` this is why a word wider than 24 bits can be processed one
  24-bit carrier at a time.
* **Dyadic moves.** `n <<< k = n * 2 ^ k` and, over `ℤ`, `m >>> k = m / 2 ^ k`
  with `/` the floor division by a positive number (`shiftLeft_eq_mul`,
  `int_shiftRight_eq_floor_div`), which is Python's `>>` on negative numbers.
* **Slices.** For a positive step, position `i` is read exactly when
  `start + i * step < stop`, where the count is CPython's
  `(stop - start + step - 1) / step` (`mem_slice_iff`), so the index map
  `i ↦ start + i * step` never leaves `[start, stop)` (`slice_index_lt`).
* **Golay branching.** For any code of minimum distance `8` (the Golay code
  is one: `GLM.Golay24.golay_min_distance_eight`), a subject within `3` of a
  declared case codeword is within `4` of no other codeword
  (`branch_unique`), a subject at distance exactly `4` from a declared case
  is at distance at least `4` from every codeword, so the tie is genuine
  (`deep_hole_no_nearer`), and the classifier's three verdicts are exhaustive
  and exclusive (`classify_trichotomy`). The six-fold tie itself is
  `GLM.Golay24.ties_card_eq_six`, and the fact that no word is `5` or more
  from the *whole* code is `GLM.Golay24.covering_radius_le_four`: the
  `UNCORRECTABLE` verdict exists only relative to the declared cases.
-/

@[expose] public section

namespace GLM.PythonSpeech

/-! ## 1. The gates and the sub-register programs -/

/-- CCNOT on a three-bit register: toggle the target when both controls are set. -/
def toffoli : Bool × Bool × Bool → Bool × Bool × Bool
  | (c1, c2, t) => (c1, c2, xor t (c1 && c2))

/-- CSWAP on a three-bit register: swap the last two bits when the control is set. -/
def fredkin : Bool × Bool × Bool → Bool × Bool × Bool
  | (c, x, y) => if c then (c, y, x) else (c, x, y)

theorem toffoli_involutive : Function.Involutive toffoli := by
  intro x; revert x; decide

theorem fredkin_involutive : Function.Involutive fredkin := by
  intro x; revert x; decide

/-- A lane: operand bit `a`, operand bit `b`, target line `t`. -/
abbrev Lane := Bool × Bool × Bool

/-- Toffoli with controls `a`, `b` and target `t`. -/
def tofAB : Lane → Lane
  | (a, b, t) => toffoli (a, b, t)

/-- Toffoli with the rail and `a` as controls, target `t` (a CNOT). -/
def tofRA : Lane → Lane
  | (a, b, t) => let r := toffoli (true, a, t); (r.2.1, b, r.2.2)

/-- Toffoli with the rail and `b` as controls, target `t`. -/
def tofRB : Lane → Lane
  | (a, b, t) => let r := toffoli (true, b, t); (a, r.2.1, r.2.2)

/-- Toffoli with the rail as both controls, target `t` (a NOT). -/
def tofRR : Lane → Lane
  | (a, b, t) => let r := toffoli (true, true, t); (a, b, r.2.2)

/-- Fredkin with control `b`, swapping `a` and `t`. -/
def fredB : Lane → Lane
  | (a, b, t) => let r := fredkin (b, a, t); (r.2.1, r.1, r.2.2)

/-- `AND`: one Toffoli. -/
def andP : Lane → Lane := tofAB
/-- `XOR`: two rail-controlled Toffolis. -/
def xorP : Lane → Lane := tofRB ∘ tofRA
/-- `OR`: `ab ⊕ a ⊕ b`. -/
def orP : Lane → Lane := tofRB ∘ tofRA ∘ tofAB
/-- `NOT`: `1 ⊕ a`. -/
def notP : Lane → Lane := tofRA ∘ tofRR
/-- `COPY`: `t := a` (fan-out into a zeroed line). -/
def copyP : Lane → Lane := tofRA
/-- `AND NOT`, in place on line `a`, by one Fredkin gate. -/
def andnotP : Lane → Lane := fredB

/-- The inverse programs: the same gates in reverse order. -/
def xorInv : Lane → Lane := tofRA ∘ tofRB
def orInv : Lane → Lane := tofAB ∘ tofRA ∘ tofRB
def notInv : Lane → Lane := tofRR ∘ tofRA

theorem andP_spec (a b : Bool) : andP (a, b, false) = (a, b, a && b) := by
  cases a <;> cases b <;> rfl

theorem xorP_spec (a b : Bool) : xorP (a, b, false) = (a, b, xor a b) := by
  cases a <;> cases b <;> rfl

theorem orP_spec (a b : Bool) : orP (a, b, false) = (a, b, a || b) := by
  cases a <;> cases b <;> rfl

theorem notP_spec (a b : Bool) : notP (a, b, false) = (a, b, !a) := by
  cases a <;> cases b <;> rfl

theorem copyP_spec (a b : Bool) : copyP (a, b, false) = (a, b, a) := by
  cases a <;> cases b <;> rfl

/-- The Fredkin program leaves `a ∧ ¬b` on line `a` and keeps `a ∧ b` on
line `t`, so the bit it moves is stored, not erased. -/
theorem andnotP_spec (a b : Bool) :
    andnotP (a, b, false) = (a && !b, b, a && b) := by
  cases a <;> cases b <;> rfl

theorem andP_inv : ∀ x, andP (andP x) = x := by decide
theorem xorP_inv : ∀ x, xorInv (xorP x) = x := by decide
theorem orP_inv : ∀ x, orInv (orP x) = x := by decide
theorem notP_inv : ∀ x, notInv (notP x) = x := by decide
theorem copyP_inv : ∀ x, copyP (copyP x) = x := by decide
theorem andnotP_inv : ∀ x, andnotP (andnotP x) = x := by decide

theorem andP_bijective : Function.Bijective andP :=
  Function.Involutive.bijective andP_inv

theorem xorP_bijective : Function.Bijective xorP := by
  refine ⟨Function.LeftInverse.injective xorP_inv, ?_⟩
  intro y; exact ⟨xorInv y, by revert y; decide⟩

theorem orP_bijective : Function.Bijective orP := by
  refine ⟨Function.LeftInverse.injective orP_inv, ?_⟩
  intro y; exact ⟨orInv y, by revert y; decide⟩

theorem notP_bijective : Function.Bijective notP := by
  refine ⟨Function.LeftInverse.injective notP_inv, ?_⟩
  intro y; exact ⟨notInv y, by revert y; decide⟩

theorem copyP_bijective : Function.Bijective copyP :=
  Function.Involutive.bijective copyP_inv

theorem andnotP_bijective : Function.Bijective andnotP :=
  Function.Involutive.bijective andnotP_inv

/-! ## 2. The register tower: bitwise operations act window by window -/

theorem xor_mod_two_pow (a b k : ℕ) :
    (a ^^^ b) % 2 ^ k = (a % 2 ^ k) ^^^ (b % 2 ^ k) := by
  apply Nat.eq_of_testBit_eq; intro i
  simp only [Nat.testBit_mod_two_pow, Nat.testBit_xor]
  by_cases h : i < k <;> simp [h]

theorem xor_div_two_pow (a b k : ℕ) :
    (a ^^^ b) / 2 ^ k = (a / 2 ^ k) ^^^ (b / 2 ^ k) := by
  apply Nat.eq_of_testBit_eq; intro i
  simp only [Nat.testBit_div_two_pow, Nat.testBit_xor]

theorem and_mod_two_pow (a b k : ℕ) :
    (a &&& b) % 2 ^ k = (a % 2 ^ k) &&& (b % 2 ^ k) := by
  apply Nat.eq_of_testBit_eq; intro i
  simp only [Nat.testBit_mod_two_pow, Nat.testBit_and]
  by_cases h : i < k <;> simp [h]

theorem and_div_two_pow (a b k : ℕ) :
    (a &&& b) / 2 ^ k = (a / 2 ^ k) &&& (b / 2 ^ k) := by
  apply Nat.eq_of_testBit_eq; intro i
  simp only [Nat.testBit_div_two_pow, Nat.testBit_and]

theorem or_mod_two_pow (a b k : ℕ) :
    (a ||| b) % 2 ^ k = (a % 2 ^ k) ||| (b % 2 ^ k) := by
  apply Nat.eq_of_testBit_eq; intro i
  simp only [Nat.testBit_mod_two_pow, Nat.testBit_or]
  by_cases h : i < k <;> simp [h]

theorem or_div_two_pow (a b k : ℕ) :
    (a ||| b) / 2 ^ k = (a / 2 ^ k) ||| (b / 2 ^ k) := by
  apply Nat.eq_of_testBit_eq; intro i
  simp only [Nat.testBit_div_two_pow, Nat.testBit_or]

/-! ## 3. Dyadic moves -/

theorem shiftLeft_eq_mul (n k : ℕ) : n <<< k = n * 2 ^ k := Nat.shiftLeft_eq n k

/-- Python's `>>` on a (possibly negative) integer is floor division by `2 ^ k`:
over `ℤ`, `/` by a positive divisor rounds towards `-∞`. -/
theorem int_shiftRight_eq_floor_div (m : ℤ) (k : ℕ) :
    m >>> k = ⌊(m : ℚ) / 2 ^ k⌋ := by
  rw [Int.shiftRight_eq_div_pow]
  have h : ((2 : ℚ) ^ k) = ((2 ^ k : ℕ) : ℚ) := by push_cast; ring
  rw [h]
  exact (Rat.floor_intCast_div_natCast m (2 ^ k)).symm

/-! ## 4. Slices -/

/-- CPython's element count of `s[start:stop:step]` for `0 < step`, after
clamping. -/
def sliceCount (start stop step : ℕ) : ℕ := (stop - start + step - 1) / step

/-- Position `i` of the slice is read exactly when its source index lies
before `stop`. -/
theorem mem_slice_iff {start stop step : ℕ} (h : 0 < step) (i : ℕ) :
    i < sliceCount start stop step ↔ start + i * step < stop := by
  unfold sliceCount
  rw [← Nat.add_one_le_iff, Nat.le_div_iff_mul_le h]
  constructor <;> intro hi
  · have : i * step + step ≤ stop - start + step - 1 := by nlinarith
    omega
  · have : i * step + step ≤ stop - start + step - 1 := by omega
    nlinarith

/-- The index map `i ↦ start + i * step` stays inside the window. -/
theorem slice_index_lt {start stop step len : ℕ} (h : 0 < step)
    (hstop : stop ≤ len) {i : ℕ} (hi : i < sliceCount start stop step) :
    start + i * step < len :=
  lt_of_lt_of_le ((mem_slice_iff h i).1 hi) hstop

/-! ## 5. Golay branching, for any code of minimum distance 8 -/

/-- A 24-bit word as a set of coordinates. -/
abbrev Word := Finset (Fin 24)

/-- Hamming distance. -/
def hdist (a b : Word) : ℕ := (symmDiff a b).card

theorem hdist_comm (a b : Word) : hdist a b = hdist b a := by
  unfold hdist; rw [symmDiff_comm]

theorem hdist_triangle (a b c : Word) : hdist a c ≤ hdist a b + hdist b c := by
  unfold hdist
  calc (symmDiff a c).card ≤ (symmDiff a b ∪ symmDiff b c).card :=
        Finset.card_le_card (symmDiff_triangle a b c)
    _ ≤ _ := Finset.card_union_le _ _

/-- A code of minimum distance at least 8. -/
def MinDistEight (C : Set Word) : Prop :=
  ∀ c ∈ C, ∀ c' ∈ C, c ≠ c' → 8 ≤ hdist c c'

/-- **Branching is unambiguous.** Within `3` of one codeword, a subject is
within `4` of no other. -/
theorem branch_unique {C : Set Word} (hC : MinDistEight C) {v c c' : Word}
    (hc : c ∈ C) (hc' : c' ∈ C) (h : hdist v c ≤ 3) (h' : hdist v c' ≤ 4) :
    c = c' := by
  by_contra hne
  have h8 := hC c hc c' hc' hne
  have := hdist_triangle c v c'
  rw [hdist_comm c v] at this
  omega

/-- **The deep hole is a genuine tie.** At distance exactly `4` from a
codeword, no codeword is nearer than `4`. -/
theorem deep_hole_no_nearer {C : Set Word} (hC : MinDistEight C) {v c : Word}
    (hc : c ∈ C) (h : hdist v c = 4) : ∀ c' ∈ C, 4 ≤ hdist v c' := by
  intro c' hc'
  by_contra hlt
  push_neg at hlt
  have := branch_unique (v := v) hC hc' hc (by omega) (by omega)
  subst this; omega

/-- **Exhaustive and exclusive.** For declared cases `S` inside a code of
minimum distance 8, exactly one holds: a unique declared case within `3`;
none within `3` but one at exactly `4`; or every declared case at `5` or
more. -/
theorem classify_trichotomy {C : Set Word} (hC : MinDistEight C) (S : Finset Word)
    (hS : ∀ c ∈ S, c ∈ C) (v : Word) :
    ((∃ c ∈ S, hdist v c ≤ 3 ∧ ∀ c' ∈ S, hdist v c' ≤ 4 → c' = c) ∧
        ¬ (∃ c ∈ S, hdist v c = 4) ∧ ¬ (∀ c ∈ S, 5 ≤ hdist v c)) ∨
      ((∀ c ∈ S, 4 ≤ hdist v c) ∧ (∃ c ∈ S, hdist v c = 4)) ∨
      (∀ c ∈ S, 5 ≤ hdist v c) := by
  by_cases h3 : ∃ c ∈ S, hdist v c ≤ 3
  · obtain ⟨c, hcS, hc3⟩ := h3
    left
    refine ⟨⟨c, hcS, hc3, fun c' hc'S hc'4 =>
      (branch_unique hC (hS c hcS) (hS c' hc'S) hc3 hc'4).symm⟩, ?_, ?_⟩
    · rintro ⟨c', hc'S, hc'4⟩
      have := branch_unique hC (hS c hcS) (hS c' hc'S) hc3 (by omega)
      subst this; omega
    · intro hall; have := hall c hcS; omega
  · push_neg at h3
    right
    by_cases h4 : ∃ c ∈ S, hdist v c = 4
    · left; exact ⟨fun c hc => by have := h3 c hc; omega, h4⟩
    · right
      push_neg at h4
      intro c hc
      have := h3 c hc; have := h4 c hc; omega

end GLM.PythonSpeech
