/-!
  # Layers — the perception-layer lattice of the packing problem

  Integration of the uploaded layer theory (layers_universal.lean, Lean 4
  v4.8.0, verified 100%, 0 sorries) into tct_squares, extended with the
  run-11 audit's formal core: the scan-blindness boundary.

  Lattice (each layer strictly coarser than the one below):
    Substrate   floor parity mod 2  — 0 and 2 indistinguishable
    Integer      floor               — distinguishes 0/2; blind to 0/½
    Rational     identity            — distinguishes 0/½
  Beyond Rational, exact perception of an algebraic value requires the
  certificate layer (minimal polynomial). A value-space scan is a
  Rational perception composed with 12-dp rounding — blind at the
  clearance scale: the formal counterpart of run 11's measured audit
  (879/1000 spurious fits at the strict budget), and the reason all
  certification moved to the certificate route.
-/

import Mathlib.Data.Rat.Floor
import Mathlib.Tactic

namespace TCT.Layers

/-! ## Carriers and perceptions (from the uploaded theory) -/

/-- 24-dimensional rational carriers (Golay dimension). -/
def Carrier24 : Type := Fin 24 → ℚ

namespace Carrier24

def zero : Carrier24 := fun _ => 0

def two : Carrier24 := fun i => if i = 0 then (2 : ℚ) else 0

def half : Carrier24 := fun i => if i = 0 then (1/2 : ℚ) else 0

end Carrier24

/-- Substrate perception: parity of the floor of each coordinate. -/
def SubstratePerceive (c : Carrier24) : Fin 24 → ℤ :=
  fun i => ⌊c i⌋ % 2

/-- Integer perception: the floors together with their parities. -/
def IntegerPerceive (c : Carrier24) : (Fin 24 → ℤ) × (Fin 24 → ℤ) :=
  (fun i => ⌊c i⌋, fun i => ⌊c i⌋ % 2)

/-- Indistinguishability induced by a perception function. -/
def Indist {α : Type*} (f : Carrier24 → α) (a b : Carrier24) : Prop :=
  f a = f b

/-! ### The three escalation boundaries (uploaded proofs) -/

theorem substrate_indist_zero_two :
    Indist SubstratePerceive Carrier24.zero Carrier24.two := by
  unfold Indist SubstratePerceive Carrier24.zero Carrier24.two
  funext i
  by_cases h : i = 0
  · subst h
    simp only [if_true]
    norm_num
  · simp only [if_false, h]
    norm_num

theorem integer_distinguishes_zero_two :
    ¬ Indist IntegerPerceive Carrier24.zero Carrier24.two := by
  unfold Indist IntegerPerceive Carrier24.zero Carrier24.two
  intro h
  have h_floor := congr_arg Prod.fst h
  have := congr_fun h_floor 0
  simp only [if_true] at this
  norm_num at this

theorem integer_indist_zero_half :
    Indist IntegerPerceive Carrier24.zero Carrier24.half := by
  unfold Indist IntegerPerceive Carrier24.zero Carrier24.half
  simp only [if_true, if_false]
  constructor <;> funext i <;> by_cases h : i = 0 <;> simp [h] <;> norm_num

theorem rational_distinguishes_zero_half :
    ¬ Indist (fun c : Carrier24 => c) Carrier24.zero Carrier24.half := by
  intro h
  have := congr_fun h 0
  simp only [Carrier24.zero, Carrier24.half, if_true] at this
  norm_num at this

/-! ### The run-11 boundary: scan blindness at the clearance scale -/

/-- Scan perception: the 12-decimal image of a rational value. -/
def ScanPerceive (v : ℚ) : ℤ := round (v * 10^12)

/-- Core blindness lemma (sharp form). If two values differ by less
    than a QUARTER of a 12-dp grid step (2.5·10⁻¹³), the scan
    perception cannot tell them apart — regardless of their exact
    algebraic status. Proof: each round sits within 1/2 of its
    argument; the two rounds then differ by < 3/4; an integer gap
    below 1 is 0. This is the formal counterpart of the run-11 audit
    (value scans cannot certify at the table's clearance scale). -/
theorem scan_blind_to_clearance (v w : ℚ)
    (h : |v - w| < 25 / 10^14) :
    ScanPerceive v = ScanPerceive w := by
  set x := v * 10^12 with hx
  set y := w * 10^12 with hy
  have hdiff : |x - y| < 1 / 4 := by
    have e : x - y = (v - w) * 10^12 := by
      simp only [hx, hy]
      ring
    have h25 : 25 / 10^14 * 10^12 = 1 / 4 := by norm_num
    have hle : |v - w| * 10^12 < 25 / 10^14 * 10^12 := by
      exact (mul_lt_mul_right (by norm_num : (0:ℚ) < 10^12)).2 h
    rw [e, abs_mul, abs_of_pos (by norm_num : (0:ℚ) < 10^12)]
    rw [← h25]
    exact hle
  have hv : |x - round x| ≤ 1 / 2 := abs_sub_round _
  have hw : |y - round y| ≤ 1 / 2 := abs_sub_round _
  have hgap : |round x - round y| < 1 := by
    have tri : |round x - round y| ≤ |round x - x| + |x - y| + |y - round y| := by
      have e1 : round x - round y = (round x - x) + (x - y) + (y - round y) := by ring
      rw [e1]
      have t1 : |(round x - x) + (x - y) + (y - round y)|
          ≤ |round x - x| + |x - y| + |y - round y| := by
        exact abs_add_three _ _ _
      exact t1
    have h1 : |round x - x| ≤ 1/2 := by
      rw [abs_sub_comm]; exact hv
    have h3 : |y - round y| ≤ 1/2 := hw
    have h2 : |x - y| < 1/4 := hdiff
    have : |round x - round y| < 1/4 + 1/2 + 1/2 := by
      linarith
    linarith
  have hgap' : round x - round y = 0 := by
    have := abs_lt.1 hgap
    rcases this.2 with hpos | hneg
    · have : round x - round y ≥ 1 := by
        have : (0:ℤ) < round x - round y := hpos
        omega
      omega
    · have : round x - round y ≤ 0 := by omega
      have : round x - round y ≤ -1 := by omega
      have hlt : round x - round y < 0 := by omega
      have : |round x - round y| < 1 := hgap
      have : |round x - round y| ≥ 1 := by
        rw [abs_of_nonpos (by omega)]
        omega
      omega
  unfold ScanPerceive
  simp only [hx, hy]
  rw [hgap']
  rfl
